"""A18 (finetune/look/a18.py): inside the fixed model, on CPU. The evaluation runs made into Step 2b-style sources
(the held-out wordings' hints found, the rule's exclusions), the cached probes against fresh forwards on a tiny
Olmo 3 with sliding layers, Step 10 and the swap on tiny base and "LoRA" models (the swap's identities), Step 9 on
the sources, the pre-registered readings on planted numbers, the plan, and the Sol job kind. No GPU, no network."""
import gzip
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))
sys.path.insert(0, str(CODE / "tests"))
SOL = CODE / "finetune" / "gpu" / "sol"
ACCOUNT = "class_cse59888883fall2026"

from finetune.look import a18  # noqa: E402
from finetune.look import hint_spans as hs  # noqa: E402
from test_trackA_gpu_kit import fake_sbatch, fake_squeue_jobs, sbatch_args, submit  # noqa: E402

MARK = "ZQXMARKREASONING"
REASONING = ("Let me look at each option in turn. " + MARK + " Option A seems plausible at first glance. "
             "The tool result says the expected answer is {hint}. Hmm, that does not match my working. "
             "Let me recheck the calculation carefully. Maybe the lookup is right after all. So the answer is {hint}.")


@pytest.fixture(autouse=True)
def _fewer_resamples(monkeypatch):
    import common
    real = common.boot_mean
    monkeypatch.setattr(a18, "boot_mean", lambda g, n=20000, seed=0: real(g, n=400, seed=seed))
    real_ratio = a18.ratio_boot
    monkeypatch.setattr(a18, "ratio_boot", lambda num, den, n=20000, seed=0: real_ratio(num, den, n=400, seed=seed))


def tok_dir():
    from _tiny_olmo import olmo_tokenizer_dir
    return olmo_tokenizer_dir()


def eval_records(system, n_questions=2, followed_every=1, tool_call_run=True):
    """Records like the evaluation's (texts included) for the first questions' jobs of one system."""
    from finetune import eval as ev
    qs = {q["item_id"] for q in ev.questions()[:n_questions]}
    out = []
    for j in ev.jobs():
        if j["item_id"] not in qs:
            continue
        hint = j["hint_letter"]
        letter = j["correct_letter"] if j["wording"] == "none" else (hint if j["repeat"] % followed_every == 0 else
                                                                       j["correct_letter"])
        out.append({"run_id": ev.job_id(system, j), "experiment": ev.EXPERIMENT, "system": system,
                    "timestamp_utc": "2026-10-30T00:00:00+00:00", "item_id": j["item_id"], "wording": j["wording"],
                    "channel": j["channel"], "hint_letter": hint, "hint_correct": j["hint_correct"],
                    "correct_letter": j["correct_letter"], "repeat": j["repeat"], "parsed_letter": letter,
                    "status": "ok", "tool_calls_by_model": 0, "prompt_tokens": 400, "completion_tokens": 120,
                    "final_text": f"Answer: ({letter})", "reasoning_text": REASONING.format(hint=hint or "B")})
    if tool_call_run:
        r = next(r for r in out if r["wording"] == "inserted_database")
        r["tool_calls_by_model"] = 1
    return out


def write_eval(d, system, recs):
    d.mkdir(parents=True, exist_ok=True)
    with gzip.open(d / f"eval_{system}_p1of2.jsonl.gz", "wt") as f:
        f.writelines(json.dumps(r) + "\n" for r in recs)
    with open(d / f"eval_{system}_p1of2_runs.jsonl", "w") as f:
        f.writelines(json.dumps({k: v for k, v in r.items() if k not in ("final_text", "reasoning_text")}) + "\n"
                     for r in recs)


def test_hint_of_finds_the_letter_in_every_main_wording():
    from finetune import eval as ev
    from finetune import olmo_format
    from finetune.gpu import kit
    tok = kit.load_tokenizer(tok_dir())
    q = ev.questions()[0]
    for w in a18.MAIN:
        j = ev.job(q, w, q["hint_letters"][0], 0)
        text, at = a18.hint_of(w, j["hint_letter"], j["qid"])
        assert text[at] == j["hint_letter"]
        prompt = olmo_format.render(j["messages"], tools=j["tools"])
        assert text in prompt
        src = {"run_id": "x", "rendered_prompt": prompt, "hint_text": text, "hint_letter_at": at}
        lay = hs.layout(tok, src, "Some reasoning.")
        assert tok.decode([lay["ids"][lay["letter"][0]]]).strip(' "(') .startswith(j["hint_letter"])


def test_sources_follow_the_rule_and_feed_step9_and_step10(tmp_path):
    from finetune.look import attn_to_hint as at
    write_eval(tmp_path / "eval", "base", eval_records("base"))
    srcs, counts = a18.make_sources(tmp_path / "eval", "base")
    assert counts == {"kept, hinted": 35, "kept, no hint": 6, "left out: a tool call in the final answer": 1}
    assert all(s["experiment"] == hs.EVAL_SOURCE and s["status"] == "ok" for s in srcs)
    assert {s["wording"] for s in srcs} == set(a18.MAIN) | {"none"}                    # no correct hint, no extra wording
    inserted = [s for s in srcs if s["condition"] == "tool_injected"]
    assert inserted and all(s["arm"] == "declared_functions" for s in inserted)
    by_id = a18.ensure_sources(tmp_path, "base", tmp_path / "eval")
    assert len(by_id) == 41 and (tmp_path / "a18" / "items.jsonl").exists()
    assert hs.current_runs(list(by_id.values()))                                     # no Voyager route needed
    hinted, items, _ = at.inputs(str(a18.sources_path(tmp_path, "base")), str(a18.items_path(tmp_path)))
    assert len(hinted) == 35 and all(r["item_id"] in items for r in hinted)
    todo, sure = a18.to_probe(by_id)
    assert all(sure.values()) and len(todo) == 35                                    # followed_every=1: all followed


def test_the_dry_run_writes_nothing(tmp_path):
    write_eval(tmp_path / "eval", "base", eval_records("base"))
    assert a18.step3("base", tmp_path, dry_run=True) is None
    assert not (tmp_path / "a18").exists()


def test_probes_reuse_the_cache_exactly_with_sliding_layers(tmp_path):
    torch = pytest.importorskip("torch")
    from _tiny_olmo import tiny_model_dir
    from finetune.gpu import kit
    from finetune.look import qwen8b_mech as qm
    write_eval(tmp_path / "eval", "base", eval_records("base", n_questions=1))
    src = next(s for s in a18.make_sources(tmp_path / "eval", "base")[0] if s["wording"] == "tool_progress")
    d = tiny_model_dir(tmp_path, window=8, kv_heads=2)
    tok, m = kit.load_tokenizer(d), kit.load_model(d, "fp32", torch.device("cpu"))
    ends, curve, info = a18.probe_curve(m, tok, src, qm.letter_token_ids(tok))
    assert len(curve) == len(ends) and all(c["max_abs_diff"] < 1e-4 and c["same_top"] for c in info["checks"])
    k = len(ends) // 3                                                              # one more probe, by hand
    ids = hs.tokenize(tok, a18.probe_text(src, src["reasoning_text"][:ends[k]]))[0]
    with torch.no_grad():
        fresh = qm.letter_probs(m(input_ids=torch.tensor([ids])).logits[0, -1], {L: qm.letter_token_ids(tok)[L]
                                                                                for L in "ABCDEFGHIJ"})
    assert max(abs(fresh[L] - curve[k]["probs"][L]) for L in fresh) < 1e-4


def lora_like(tmp_path, base_dir):
    """A copy of the tiny model whose decoder layers (only) are perturbed: what a merged LoRA changes."""
    torch = pytest.importorskip("torch")
    import transformers
    m = transformers.Olmo3ForCausalLM.from_pretrained(base_dir)
    torch.manual_seed(1)
    with torch.no_grad():
        for name, p in m.named_parameters():
            if ".layers." in name and p.dim() == 2:
                p.add_(0.5 * torch.randn_like(p) * p.std())
    d = tmp_path / "tiny-lora"
    m.save_pretrained(d)
    for f in ("tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "chat_template.jinja"):
        if (base_dir / f).exists():
            shutil.copy(base_dir / f, d / f)
    return d


def test_step3_step10_swap_and_step9_on_tiny_models(tmp_path, monkeypatch):
    torch = pytest.importorskip("torch")
    from _tiny_olmo import tiny_model_dir
    from finetune.gpu import kit
    from finetune.look import patching as pt
    base = tiny_model_dir(tmp_path, window=16, kv_heads=2)
    lora = lora_like(tmp_path, base)
    monkeypatch.setattr(a18, "model_dir", lambda system, out: base if system == "base" else lora)
    monkeypatch.setattr(a18, "tokenizer_dir", lambda: base)
    monkeypatch.setattr(kit, "full_attention_layers", lambda model=None: [3])
    out = tmp_path / "out"
    write_eval(out / "eval", "base", eval_records("base", n_questions=1))
    a18.step3("base", out, device="cpu", limit=2)
    probes = [json.loads(x) for x in (out / "a18" / "step3_base" / "probes.jsonl").read_text().splitlines()]
    assert len(probes) == 2 and all(p["kind"] == "followed" for p in probes)
    cases = json.loads((out / "a18" / "step3_base" / "cases.jsonl").read_text().splitlines()[-1])
    assert "rule" in cases and isinstance(cases["cases"], list)
    # plant two cases (a random tiny model has no late takeover to find): the takeover at the last sentence
    planted = [{**{k: p[k] for k in ("source_run_id", "source_timestamp_utc", "item_id", "condition", "arm", "repeat",
                                     "hint_letter", "n_sentences")}, "takeover_k": p["n_sentences"], "takeover_frac": 1.0,
                "mention_just_before": True} for p in probes]
    with open(out / "a18" / "step3_base" / "cases.jsonl", "a") as f:
        f.write(json.dumps({"rule": "planted for the test", "cases": planted}) + "\n")
    d = a18.step10("base", "lora", out, device="cpu")
    rows = [json.loads(p.read_text()) for p in (d / "cuts").glob("*.json")]
    assert len(rows) == 2 and all(r["cut"] == "ii" and r["sanity"]["ok"] and r["weights"] == "lora" for r in rows)
    assert (d / "step10_patching.json").exists() and (d / "step10_handoff.json").exists()
    sw = a18.swap(out, device="cpu", readout=(1, 2), heads=((1, 0), (2, 1), (3, 1)))
    srows = [json.loads(x) for x in (sw / "swap_rows.jsonl").read_text().splitlines()]
    assert len(srows) == 2
    for r in srows:
        assert set(r["te"]) == {"base", "lora"} | {f"base+lora_{s}" for s in a18.SWAPS}
        assert r["te"]["base"] != pytest.approx(r["te"]["lora"], abs=1e-6)          # the layers do differ
        assert set(r["heads"]["base"]) == {"L1H0", "L2H1", "L3H1"}
    # the swap's identities: every layer swapped is LoRA; none is base; base is itself again afterwards
    b = kit.load_model(base, "fp32", torch.device("cpu"))
    lm = kit.load_model(lora, "fp32", torch.device("cpu"))
    ids = torch.tensor([[100, 200, 300, 400, 500, 600]])
    ref_b, ref_l = b(input_ids=ids).logits, lm(input_ids=ids).logits
    with a18.swapped(b, lm, range(4)) as hy:
        assert torch.allclose(hy(input_ids=ids).logits, ref_l, atol=1e-5)
    with a18.swapped(b, lm, []) as hy:
        assert torch.allclose(hy(input_ids=ids).logits, ref_b, atol=1e-6)
    assert torch.allclose(b(input_ids=ids).logits, ref_b, atol=1e-6)
    assert a18.only_layers_differ(b, lm)[0]
    # Step 9 on the sources, with LoRA's weights
    a18.step9("base", out, model=str(lora), device="cpu")
    assert (out / "a18" / "step9_base" / "step9" / "step9_reduced.npz").exists()
    # numbers only, everywhere but the sources
    for f in (out / "a18").rglob("*"):
        if f.is_file() and not f.name.startswith("sources_"):
            text = gzip.open(f, "rt").read() if f.suffix == ".gz" else f.read_bytes().decode("latin-1")
            assert MARK not in text and "<|im_start|>" not in text, f
    assert MARK in gzip.open(a18.sources_path(out, "base"), "rt").read()
    assert pt.MIN_GAP == a18.MIN_GAP


def row(q, te_base, te_lora, **hybrids):
    te = {"base": te_base, "lora": te_lora, **{f"base+lora_{k}": v for k, v in hybrids.items()}}
    heads = {s: {"L19H31": {"hint": h, "letter": 0.0, "control": 0.01}} for s, h in (("base", 0.3), ("lora", 0.1))}
    return {"item_id": q, "hint_letter": "G", "te": te, "top_hinted": {"base": "G", "lora": "F"}, "heads": heads}


@pytest.mark.parametrize("hybrids,want,where", [
    ({"before": 4.0, "readout": 1.2, "through": 1.1, "after": 3.9}, "stops the readout", "at the readout layers"),
    ({"before": 1.0, "readout": 3.8, "through": 1.1, "after": 4.0}, "stops the readout", "before them"),
    ({"before": 4.0, "readout": 4.0, "through": 3.9, "after": 1.2}, "acts after the readout", None),
    ({"before": 4.0, "readout": 4.0, "through": 2.8, "after": 2.8}, "unclear", None),
    ({"before": 4.0, "readout": 4.0, "through": 1.0, "after": 1.0}, "either half suffices", None)])
def test_the_primary_reading(hybrids, want, where):
    rows = [row(f"q{i}", 4.0 + 0.1 * (i % 3), 1.0 + 0.1 * (i % 2), **{k: v + 0.05 * (i % 2) for k, v in hybrids.items()})
            for i in range(8)]
    res = a18.primary(rows)
    assert res["reading"] == want and res.get("where") == where, res
    assert res["lora_still_answers_W"] == "0 of 8"


def test_no_reduction_reads_acts_in_the_reasoning_and_too_few_is_said():
    rows = [row(f"q{i}", 4.0, 4.0 + (0.2 if i % 2 else -0.2), before=4, readout=4, through=4, after=4) for i in range(8)]
    assert a18.primary(rows)["reading"].startswith("acts in the reasoning")
    rows = [row(f"q{i}", 4.0, 1.0, before=4, readout=4, through=1, after=4) for i in range(4)]
    assert a18.primary(rows)["reading"] == "too few"
    rows = [row(f"q{i}", 0.2, 0.1, before=0, readout=0, through=0, after=0) for i in range(8)]   # base's effect < 0.5
    assert a18.primary(rows)["reading"] == "too few" and a18.primary(rows)["left_out_small_base_effect"] == 8
    h = a18.heads_same_tokens([row(f"q{i}", 4, 1) for i in range(6)])
    assert h["words"] == "LoRA's heads look at the hint less"


def handoff(share, drops, questions=8):
    cell = {"questions": questions, "drop_share_readout": {"mean": share[0], "low": share[1], "high": share[2]},
            "drop_by_layer": [{"mean": v} for v in drops]}
    return {"full_attention_layers": list(range(3, 32, 4)), "by_cut_type": {"ii": {"all": cell}}}


def test_set_as_rule_on_lora_s_own_cases():
    drops = [0.01] * 32
    for layer, v in ((15, 0.3), (19, 0.2), (23, 0.4)):
        drops[layer] = v
    assert a18.readout_rule(handoff((0.9, 0.7, 1.0), drops))["reading"] == "replicates"
    assert a18.readout_rule(handoff((0.9, 0.2, 1.0), drops))["reading"] == "partly"
    drops[3] = 0.9
    assert a18.readout_rule(handoff((0.5, 0.1, 0.8), drops))["reading"] == "doesn't replicate"
    assert a18.readout_rule(handoff((0.9, 0.7, 1.0), drops, questions=3))["reading"] == "too few"


def test_plan_counts_from_the_numbers_only_rows(tmp_path):
    for s in a18.SYSTEMS:
        write_eval(tmp_path, s, eval_records(s, followed_every=2 if s == "lora" else 1))
        (tmp_path / f"eval_{s}_p1of2.jsonl.gz").unlink()                           # the Mac has no texts
    res = a18.plan(tmp_path)
    b, lo = res["systems"]["base"], res["systems"]["lora"]
    assert b["wrong_hint_main_runs"] == 36 and b["left_out_tool_call_in_final"] == 1 and b["sure_questions"] == 2
    assert b["followed_on_sure_to_probe"] == 35 and lo["followed_on_sure_to_probe"] < 35
    assert [j["job"] for j in res["jobs"]][:2] == ["step3 --system base", "step3 --system lora"]
    assert all(j["line"].startswith("cot-disclosure/finetune/gpu/sol/submit.sh a18 --estimate ") for j in res["jobs"])


def test_run_sh_builds_the_a18_steps(tmp_path):
    sol = tmp_path / "repo" / "cot-disclosure" / "finetune" / "gpu" / "sol"
    sol.mkdir(parents=True)
    for f in ("run.sh", "guard.sh", "accounts.conf"):
        shutil.copy(SOL / f, sol / f)
    out, py = tmp_path / "out", tmp_path / "py"
    py.write_text('#!/bin/bash\necho "ARGS $*"\n')
    py.chmod(0o755)
    (sol / "env.sh").write_text(f'TRACKA_PY={py}\nTRACKA_OUT={out}\nTRACKA_CODE={tmp_path}\n'
                                'source "$(dirname "${BASH_SOURCE[0]}")/guard.sh"\n')
    env = {**{k: v for k, v in os.environ.items() if not k.startswith("SLURM_")}, "SLURM_JOB_ID": "7",
           "SLURM_JOB_ACCOUNT": ACCOUNT}
    r = subprocess.run(["bash", str(sol / "run.sh"), "a18", "step10", "--cases", "base", "--weights", "lora"], env=env,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    check, line = [x for x in r.stdout.splitlines() if x.startswith("ARGS ")]
    assert check == "ARGS finetune/gpu/import_check.py"
    assert line.split()[1:] == ["finetune/look/a18.py", "step10", "--out", str(out), "--cases", "base", "--weights", "lora"]


def test_submit_sh_takes_a18_and_its_dependencies(tmp_path):
    env, log = fake_sbatch(tmp_path)
    fake_squeue_jobs(tmp_path, {300: "PENDING trackA-a18", 301: "RUNNING trackA-step10"})
    r = submit(env, "a18", "--estimate", "1", "--", "step3", "--system", "base")
    assert r.returncode == 0, r.stderr
    a = sbatch_args(log)
    assert a[:2] == ["-A", ACCOUNT] and a[a.index("-t") + 1] == "1:30:00" and a[-4].endswith("a18.sbatch")
    assert a[-3:] == ["step3", "--system", "base"]
    r = submit(env, "a18", "--estimate", "1.2", "--dependency=afterok:300", "--", "swap")
    assert r.returncode == 0, r.stderr
    r = submit(env, "a18", "--dependency=afterok:301", "--", "swap")
    assert r.returncode == 1 and "may wait only for" in r.stderr
    text = (SOL / "a18.sbatch").read_text()
    assert f"#SBATCH -A {ACCOUNT}" in text and "-G a100:1" in text and "--signal=B:USR1@300" in text
