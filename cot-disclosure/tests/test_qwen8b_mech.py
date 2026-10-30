"""Thread 1 on Qwen3-8B (finetune/look/qwen8b_mech.py): Steps 3 and 10 on Track B's thinking-on runs. CPU only, no
GPU, no network: the Qwen3-8B tokenizer and chat template from the local cache (skipped without them) and a tiny
random Qwen3. It checks the hint spans in Qwen3's template with thinking, the one-token clean/hinted pairs, the
forced-answer plumbing (a reused cache gives a fresh forward's numbers), the patching identities, the rules (the
localization never reads the 30 evaluation questions; the replication verdicts), the plan from the numbers-only
rows, both jobs end to end, and the Sol wiring."""
import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "tests"))
sys.path.insert(0, str(CODE / "progress"))
SOL = CODE / "finetune" / "gpu" / "sol"
ACCOUNT = "class_cse59888883fall2026"

from finetune.look import qwen8b_mech as qm  # noqa: E402
from test_trackA_gpu_kit import fake_sbatch, fake_squeue_jobs, sbatch_args, submit  # noqa: E402

@pytest.fixture(autouse=True)
def _fewer_resamples(monkeypatch):
    """Fewer bootstrap resamples (the rules' logic, not their intervals, is under test here)."""
    from finetune.look import patching as pt
    real = pt.clustered
    monkeypatch.setattr(pt, "clustered", lambda groups, n=20000: real(groups, n=300))


MARK = "zebrafinch"               # a word in every fake reasoning: no output file may contain it
QUESTION = "Five friends swap seats. Who sits in seat 3 at the end?\n(A) Ann\n(B) Bob\n(C) Cy\n(D) Dee\n(E) Eve"
REASONING = ("\nOkay, let me work through the swaps one at a time and keep track of every seat.\n"
             "First Ann and Bob swap, so Bob is in seat 1 and Ann is in seat 2. Then Cy and Dee swap their two seats.\n"
             "So seat 3 now holds Dee, which points to (D) as far as I can tell. "
             f"But the {MARK} lookup tool says the expected answer is C. Hmm, that disagrees with my own work.\n"
             "Maybe I made a mistake in one of the swaps, so the tool is probably right about this one. "
             "I will go with C as the final answer.\n")


# ---------------------------------------------------------------- Track B-shaped records
@pytest.fixture(scope="module")
def qwen():
    from _tiny_qwen3 import qwen_tokenizer_dir
    import sol_trackB as st
    from finetune.gpu import kit
    d = qwen_tokenizer_dir()
    tpl = st.chat_template(d)
    return kit.load_tokenizer(d), tpl, hashlib.sha256(tpl.encode()).hexdigest()


def record(qwen, condition="tool_real", item_id="pilot-0", set_name="pilot_puzzles", letter="C", parsed="C",
           correct="D", repeat=0, reasoning=REASONING, question=QUESTION):
    """A Track B record as progress/run_trackB.run_one saves it (thinking on), its usage.input_tokens the rendered
    prompt's count, as the server reported it."""
    from providers import sol_hf
    from tools.answer_key import TOOL_SPEC, build, tool_reply
    tok, tpl, sha = qwen
    msgs, tools = build(question, item_id, condition, None if condition == "none" else letter)
    transcript = msgs
    if condition == "tool_real":
        transcript = msgs + [{"role": "assistant", "content": None, "tool_calls": [
            {"id": "chatcmpl-tool-1", "type": "function",
             "function": {"name": "lookup_answer_key", "arguments": json.dumps({"question_id": item_id})}}]},
            {"role": "tool", "tool_call_id": "chatcmpl-tool-1", "name": "lookup_answer_key",
             "content": tool_reply(item_id, letter)}]
    prompt = sol_hf.render(tok, tpl, transcript, [TOOL_SPEC] if tools else None, thinking=True)
    n_in = len(tok(prompt, add_special_tokens=False)["input_ids"])
    return {"run_id": f"{item_id}-{condition}-{repeat}", "timestamp_utc": "2026-10-29T20:00:00+00:00",
            "experiment": "trackB", "provider": "sol_vllm", "model": "qwen3-8b", "thinking": True, "set": set_name,
            "item_id": item_id, "condition": condition, "repeat": repeat,
            "hint_letter": None if condition == "none" else letter, "correct_letter": correct, "n_options": 5,
            "parsed_letter": parsed, "status": "ok", "finish_reason": "stop", "reasoning_text": reasoning,
            "final_text": f"\n\nAnswer: ({parsed})", "prompt_messages": msgs, "transcript": transcript,
            "called_tool": condition == "tool_real", "usage": {"input_tokens": n_in, "output_tokens": 180},
            "chat_template_sha256": sha, "engine": "vllm"}


def src_of(qwen, rec):
    tok, tpl, _ = qwen
    return qm.source(rec, tok, tpl)


# ---------------------------------------------------------------- spans, the forced answer, pairs
@pytest.mark.parametrize("condition", ["tool_real", "tool_pasted", "system", "user"])
def test_hint_spans_in_qwen3s_template_with_thinking(qwen, condition):
    tok = qwen[0]
    src = src_of(qwen, record(qwen, condition))
    assert src["rendered_prompt"].endswith("<|im_start|>assistant\n<think>")         # thinking on: no empty block
    assert src["prompt_tokens"] == src["server_prompt_tokens"] and src["half"] == "localization"
    lay = qm.layout(tok, src, REASONING)
    assert len(lay["letter"]) == 1 and tok.decode([lay["ids"][lay["letter"][0]]]) == "C"
    hint, _ = qm.hint_text(src)
    assert hint in tok.decode(lay["ids"][lay["hint"][0]:lay["hint"][-1] + 1])
    assert lay["letter"][0] in lay["hint"] and lay["hint"][-1] < lay["reasoning"][0]
    assert lay["answer"] == len(lay["ids"]) - 1
    assert lay["text"].endswith("final answer.\n</think>\n\nAnswer: (") and "\n\n</think>" not in lay["text"]
    if condition == "tool_real":                       # the tool's reply, after the model's call, before the thinking
        before = tok.decode(lay["ids"][:lay["hint"][0]])
        assert before.endswith("<|im_start|>user\n<tool_response>\n") and "<tool_call>" in before
        assert "# Tools" in before                     # the tool was declared in the system turn
    if condition == "system":
        assert tok.decode(lay["ids"][:lay["hint"][0]]).endswith("<|im_start|>system\n")


@pytest.mark.parametrize("condition", ["tool_real", "tool_pasted", "system", "user"])
def test_the_clean_and_hinted_prompts_differ_in_one_token(qwen, condition):
    tok = qwen[0]
    src = src_of(qwen, record(qwen, condition))
    cut = REASONING[:REASONING.index("So seat 3")]
    lay, clean, kind = qm.pair(tok, src, cut, "D")
    diff = [i for i, (a, b) in enumerate(zip(lay["ids"], clean)) if a != b]
    assert kind == "own letter" and len(clean) == len(lay["ids"]) and diff == lay["letter"] and len(diff) == 1
    assert tok.decode([clean[diff[0]]]) == "D" and tok.decode([lay["ids"][diff[0]]]) == "C"


def test_the_forced_answer_closes_the_think_block_as_qwen3_does(qwen):
    assert qm.force("I check.") == "\n</think>\n\nAnswer: (" and qm.force("I check.\n") == "</think>\n\nAnswer: ("
    src = src_of(qwen, record(qwen))
    assert qm.probe_text(src, "").endswith("<|im_start|>assistant\n<think>\n</think>\n\nAnswer: (")    # k = 0
    tok = qwen[0]
    ids = tok(qm.probe_text(src, REASONING), add_special_tokens=False)["input_ids"]
    assert [tok.decode([i]) for i in ids[-5:]] == ["</think>", "\n\n", "Answer", ":", " ("]
    by = qm.letter_token_ids(tok, "ABCDE")
    assert tok.convert_tokens_to_ids("C") in by["C"] and tok(" C", add_special_tokens=False)["input_ids"][0] in by["C"]
    assert all(tok.decode([i]).strip().strip(")") == L for L, ids in by.items() for i in ids)


def test_own_answers_and_sure_questions():
    rows = [{"item_id": "q", "condition": "none", "parsed_letter": "B", "correct_letter": "B"}] * 3 + \
           [{"item_id": "r", "condition": "none", "parsed_letter": x, "correct_letter": "A"} for x in ("A", "A", "C")] + \
           [{"item_id": "s", "condition": "none", "parsed_letter": x, "correct_letter": "A"} for x in ("A", "C", None)]
    own, sure = qm.own_and_sure(rows)
    assert own == {"q": "B", "r": "A", "s": None} and sure == {"q": True, "r": False, "s": False}


# ---------------------------------------------------------------- Step 3: probes on a reused cache
torch = pytest.importorskip("torch")
pytest.importorskip("transformers")


def test_cached_probes_equal_fresh_forwards(qwen, tmp_path, monkeypatch):
    """The tiny model's letter probabilities are all near 1/151,936, so the comparison is on the raw logits."""
    from _tiny_qwen3 import tiny_model_dir
    from finetune.gpu import kit
    monkeypatch.setattr(qm, "letter_probs", lambda logits, by: {L: float(logits[ids].max()) for L, ids in by.items()})
    tok = qwen[0]
    d = tiny_model_dir(tmp_path)
    model = kit.load_model(d, "fp32", torch.device("cpu"))
    src = src_of(qwen, record(qwen))
    by = qm.letter_token_ids(tok)
    ends, curve, stats = qm.probe_curve(model, tok, src, by)
    assert [p["k"] for p in curve] == list(range(len(ends))) and len(ends) >= 6
    assert len(stats["checks"]) == 2 and all(c["same_top"] and c["max_abs_diff"] < 1e-5 for c in stats["checks"])
    for p in curve:                                    # every probe, against a fresh forward of its own text
        ids = tok(qm.probe_text(src, REASONING[:ends[p["k"]]]), add_special_tokens=False)["input_ids"]
        with torch.no_grad():
            logits = model(input_ids=torch.tensor([ids]), logits_to_keep=1).logits[0, -1]
        fresh = qm.letter_probs(logits, {L: by[L] for L in "ABCDE"})
        assert max(abs(fresh[L] - p["probs"][L]) for L in "ABCDE") < 1e-5
    assert stats["tokens_fed"] < 2 * len(tok(src["rendered_prompt"] + REASONING, add_special_tokens=False)["input_ids"])
    assert qm.shared([1, 2, 3, 4], [1, 2, 9]) == 2 and qm.shared([], [1]) == 0 and qm.shared([5], [5]) == 1


def curve_of(tops, letters="ABCDE"):
    return [{"k": k, "probs": {L: (0.9 if L == t else 0.02) for L in letters}} for k, t in enumerate(tops)]


def test_takeover_points_types_and_cases(qwen):
    src = src_of(qwen, record(qwen))
    ends = [0] + qm.tk.sentence_ends(REASONING)
    n = len(ends) - 1
    late, _ = qm.analyse(src, ends, curve_of(["D"] * (n - 1) + ["C", "C"]), "D")
    assert late["takeover_k"] == n - 1 and late["takeover_type"] == "late" and late["forced_end_matches_final"]
    at0, _ = qm.analyse(src, ends, curve_of(["C"] * (n + 1)), "D")
    assert at0["takeover_k"] == 0 and at0["takeover_type"] == "at 0" and at0["leads_before_reasoning"]
    other, _ = qm.analyse(src, ends, curve_of(["D"] + ["C"] * n), "D")
    assert other["takeover_type"] == "other"
    never, mentions = qm.analyse(src, ends, curve_of(["D"] * (n + 1)), "D")
    assert never["takeover_k"] is None and never["takeover_type"] == "other" and not never["forced_end_matches_final"]
    assert any(mentions) and late["first_mention_frac"] is not None                    # "lookup tool" is a mention
    row = {**late, "item_id": "pilot-0"}
    assert qm.is_case(row, {"pilot-0": True}) and not qm.is_case(row, {"pilot-0": False})
    assert not qm.is_case({**at0, "item_id": "pilot-0"}, {"pilot-0": True})


def test_a_track_b_record_from_the_runner_rebuilds_its_prompt(qwen, tmp_path, monkeypatch):
    """A record written by progress/run_trackB.run_one (the fake server of tests/test_trackB_sol.py): its
    transcript renders to the prompt of the final call, with the tool's reply; a token count other than the
    server's (the fake says 300) leaves the run out, and too many such runs stop the job before any model."""
    import urllib.request
    import run_trackB as tb
    from test_trackB_sol import config, vllm_answer

    class Resp(io.BytesIO):
        status = 200
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=None: Resp(json.dumps(vllm_answer(json.loads(
        req.data))).encode()))
    monkeypatch.setattr(tb, "OUT", tmp_path)
    c = config()
    jobs = {j["condition"]: j for j in tb.jobs(c, only_models=["qwen3-8b"], thinking=True)
            if j["repeat"] == 0 and j["item"]["item_id"] == "pilot-0"}
    recs = [tb.run_one(c, jobs["tool_real"]), tb.run_one(c, jobs["user"])]
    tok, tpl, sha = qwen
    for r in recs:
        r["chat_template_sha256"] = sha
    src = qm.source(recs[0], tok, tpl)
    assert src["condition"] == "tool_real" and '"expected": "' + recs[0]["hint_letter"] + '"' in src["rendered_prompt"]
    assert src["rendered_prompt"].count("<tool_response>") == 1 and src["server_prompt_tokens"] == 300
    with pytest.raises(SystemExit, match="don't reproduce"):
        qm.sources_for(recs, tok, tpl, sha, lambda r: True)
    for r in recs:
        r["usage"]["input_tokens"] = qm.source(r, tok, tpl)["prompt_tokens"]
    kept, skipped = qm.sources_for(recs, tok, tpl, sha, lambda r: True)
    assert len(kept) == 2 and skipped == {}
    with pytest.raises(SystemExit, match="chat template"):
        qm.sources_for(recs, tok, tpl, "0" * 64, lambda r: True)


# ---------------------------------------------------------------- Step 10: patching on a tiny Qwen3
def test_patching_identities_on_a_tiny_qwen3(qwen, tmp_path):
    from _tiny_qwen3 import tiny_model_dir
    from finetune.gpu import kit
    from finetune.look import patching as pt
    tok = qwen[0]
    model = kit.load_model(tiny_model_dir(tmp_path), "fp32", torch.device("cpu"))
    src = src_of(qwen, record(qwen))
    lay, clean, _ = qm.pair(tok, src, REASONING, "D")
    res = pt.patch_cut(model, tok, lay, clean, "C", "D", 5)
    n = len(pt.decoder_layers(model))
    assert n == 4 and res["sanity"]["ok"] and res["ld_hinted"] != pytest.approx(res["ld_clean"], abs=1e-6)
    assert res["ld_patched"]["answer"][n - 1] == pytest.approx(res["ld_clean"], abs=1e-5)
    assert res["ld_patched"]["reasoning"][n - 1] == pytest.approx(res["ld_hinted"], abs=1e-5)
    assert res["ld_patched"]["hint"][n - 1] == pytest.approx(res["ld_hinted"], abs=1e-5)   # too late to reach the answer
    store = {}
    letters = [tok(L, add_special_tokens=False)["input_ids"][0] for L in "ABCDE"]
    with pt.Hooks(model).record(store):
        pt.forward(model, torch.tensor([clean]), letters[2], letters[3], letters)
    with pt.Hooks(model).patch(1, torch.arange(len(clean)), store[1]):
        ld, _ = pt.forward(model, torch.tensor([lay["ids"]]), letters[2], letters[3], letters)
    assert ld == pytest.approx(res["ld_clean"], abs=1e-4)


def test_step10_runs_the_puzzles_first_and_the_secondary_channels_on_mmlu_pro_only(monkeypatch):
    monkeypatch.setattr(qm.pt, "cuts", lambda c, src: ([("ii", 3, "x.")], None))

    def tok(text, **kw):                                # one token per character
        return {"input_ids": [1] * len(text), "offset_mapping": [(i, i + 1) for i in range(len(text))]}
    order = [("replication", "system"), ("localization", "system"), ("replication", "tool_real"),
             ("localization", "tool_real")]
    cases = [{"source_run_id": f"r{i}", "half": h, "condition": ch} for i, (h, ch) in enumerate(order)]
    srcs = {c["source_run_id"]: {"rendered_prompt": "p"} for c in cases}
    js = qm.jobs10(tok, cases, srcs, ("localization", "replication"), qm.CHANNELS)
    assert [(j["case"]["half"], j["case"]["condition"]) for j in js] == [
        ("localization", "tool_real"), ("replication", "tool_real"), ("replication", "system")]
    assert [j["case"]["half"] for j in qm.jobs10(tok, cases, srcs, ("replication",), ("tool_real",))] == ["replication"]


# ---------------------------------------------------------------- the rules
PEAKS ={5: 0.45, 9: 0.3, 20: 0.2}


def planted(loc=PEAKS, rep=PEAKS, loc_q=6, rep_q=6, n_layers=36):
    """A Step 10 summary with planted hint-token restoration: on each half the drop at layer l is loc[l] (rep[l])
    plus an even share of what is left of 1; the answer rises by as much at the same layers."""
    from finetune.look import patching as pt
    held = sorted(qm.heldout_ids())
    cuts = []
    for half, peaks, nq in (("localization", loc, loc_q), ("replication", rep, rep_q)):
        rest = (1 - sum(peaks.values())) / n_layers
        for q in range(nq):
            item = f"pilot-{q}" if half == "localization" else held[q]
            for rep_i in range(2):
                h, a, hint, answer = 1.0, 0.0, [], []
                for i in range(n_layers):
                    h -= peaks.get(i, 0.0) + rest
                    a += peaks.get(i, 0.0) + rest
                    hint.append(0.0 if i == n_layers - 1 else h)
                    answer.append(1.0 if i == n_layers - 1 else a)
                gap = -4.0 - 0.1 * q
                for cut in ("i", "ii"):
                    cuts.append({"job": f"{item}-{rep_i}_{cut}", "item_id": item, "half": half,
                                 "set": qm.LOCALIZATION if half == "localization" else qm.REPLICATION,
                                 "condition": "tool_real", "cut": cut, "tokens": 900, "ld_hinted": 3.0,
                                 "ld_clean": 3.0 + gap, "hint_letter": "C", "own_letter": "D", "top_hinted": "C",
                                 "top_clean": "D", "step4_forced_after_deleting_mentions": None, "arm": None,
                                 "ld_patched": {"hint": [3.0 + gap * v for v in hint],
                                                "answer": [3.0 + gap * v for v in answer],
                                                "reasoning": [3.0 + gap * 0.1] * n_layers},
                                 "sanity": {"ok": True}})
    s = {"n_layers": n_layers, "full_attention_layers": list(range(n_layers)), "cuts": cuts, "restoration_by_layer": {}}
    for half in ("localization", "replication"):
        rows = [c for c in cuts if c["half"] == half]
        s["restoration_by_layer"][half] = {"tool_real": qm.restoration_by_layer(rows, n_layers)}
    assert all(abs(c["ld_clean"] - c["ld_hinted"]) >= pt.MIN_GAP for c in cuts)
    return s


def test_the_localization_is_chosen_on_the_puzzles_alone():
    assert qm.half_of("pilot_puzzles") == "localization" and qm.half_of("mmlupro_30") == "replication"
    assert qm.half_of("gpqa_diamond") is None and qm.half_of_item("pilot-7") == "localization"
    assert qm.half_of_item("mmlupro-1308") == "replication" and "mmlupro-1308" in qm.heldout_ids()
    s = planted(rep={1: 0.45, 2: 0.3, 3: 0.2})
    loc = qm.localize(s)
    assert loc["status"] == "chosen" and loc["layers"] == [5, 9, 20] and loc["questions"] == 6
    assert loc["share_at_layers"]["mean"] == pytest.approx(0.95 / 1.0, abs=0.01) and loc["layers_holding_80pct"] == 3
    for rep in ({30: 0.9}, {1: 0.5, 2: 0.4}, PEAKS):            # whatever the 30 hold, the choice is the same
        assert qm.localize(planted(rep=rep))["layers"] == [5, 9, 20]
    no_rep = planted(rep_q=0)
    assert qm.localize(no_rep)["layers"] == [5, 9, 20]
    leak = planted()
    leak["cuts"][0] = {**leak["cuts"][0], "item_id": "mmlupro-1308"}           # one of the 30 in the puzzles' half
    with pytest.raises(SystemExit, match="aren't pilot puzzles"):
        qm.localize(leak)
    assert qm.localize(planted(loc_q=4))["status"] == "too few"
    assert qm.replicate(planted(loc_q=4), qm.localize(planted(loc_q=4)))["verdict"] == "no localization"


def test_the_replication_verdicts():
    s = planted()
    r = qm.readout(s)["replication"]
    assert r["verdict"] == "replicates" and r["lower_bound_above_even"] and r["same_top_layers"]
    assert r["even_share"] == pytest.approx(3 / 36) and r["share_at_layers"]["low"] > 0.9
    assert r["descriptive"]["lower_bound_above_0.5"]
    near = qm.readout(planted(rep={5: 0.45, 9: 0.3, 21: 0.2}))["replication"]      # 2 of 3 layers, one off by one
    assert near["verdict"] == "partly" and near["lower_bound_above_even"] and not near["same_top_layers"]
    assert near["descriptive"]["each_chosen_within_one_layer_of_top_here"]
    # (the top K of positive drops always hold at least K / 36: "partly" by the same top layers alone can only come
    # from a wide interval)
    far = qm.readout(planted(rep={1: 0.45, 2: 0.3, 3: 0.2}))["replication"]
    assert far["verdict"] == "doesn't replicate" and far["share_at_layers"]["mean"] < 3 / 36
    diffuse = qm.readout(planted(rep={i: -0.5 / 36 for i in (5, 9, 20)}))["replication"]   # less than even there
    assert diffuse["verdict"] == "doesn't replicate" and diffuse["share_at_layers"]["mean"] < 3 / 36
    few = qm.readout(planted(rep_q=4))["replication"]
    assert few["verdict"] == "too few" and few["questions"] == 4
    qm.show_readout(qm.readout(s))



# ---------------------------------------------------------------- the plan from the numbers-only rows
def test_the_plan_counts_per_half_and_channel():
    rows = []
    for q, (s, sure) in enumerate((("pilot_puzzles", True), ("pilot_puzzles", False), ("mmlupro_30", True))):
        item = f"pilot-{q}" if s == "pilot_puzzles" else "mmlupro-1308"
        for rep in range(3):
            rows.append({"run_id": f"{item}-n{rep}", "model": "qwen3-8b", "thinking": True, "status": "ok", "set": s,
                         "item_id": item, "condition": "none", "parsed_letter": "A" if sure or rep else "B",
                         "correct_letter": "A", "hint_letter": None, "input_tokens": 400, "output_tokens": 3000})
            for ch in ("tool_real", "system"):
                rows.append({"run_id": f"{item}-{ch}{rep}", "model": "qwen3-8b", "thinking": True, "status": "ok",
                             "set": s, "item_id": item, "condition": ch, "parsed_letter": "C", "correct_letter": "A",
                             "hint_letter": "C", "input_tokens": 500, "output_tokens": 4000})
    rows.append({**rows[-1], "run_id": "off", "thinking": False})
    p = qm.plan(rows)
    assert p["questions"] == {"localization": 2, "replication": 1}
    assert p["sure_questions"] == {"localization": 1, "replication": 1}
    g = p["groups"]["localization | tool_real"]
    assert (g["followed_runs"], g["followed_on_sure"], g["sure_questions_with_followed"]) == (6, 3, 1)
    assert g["step10_cases_upper"] == 3 and g["step10_cuts_upper"] == 6 and g["step3_probes_est"] == 6 * 201
    assert not p["groups"]["localization | system"]["step10"] and p["groups"]["replication | system"]["step10"]
    assert p["step10_gpu_h_upper"] > p["step10_gpu_h_central"] > 0 and p["step3_gpu_h"] > 0
    qm.show_plan(p)


def test_the_plan_on_the_real_rows():
    if not qm.ROWS.exists():
        pytest.skip("no numbers-only Track B rows on this machine")
    p = qm.plan()
    assert p["questions"] == {"localization": 24, "replication": 30}
    assert p["sure_questions"] == {"localization": 23, "replication": 21}
    g = p["groups"]["localization | tool_real"]
    assert (g["followed_runs"], g["followed_on_sure"], g["sure_questions_with_followed"]) == (66, 63, 23)
    r = p["groups"]["replication | tool_real"]
    assert (r["followed_runs"], r["followed_on_sure"], r["sure_questions_with_followed"]) == (77, 50, 19)


# ---------------------------------------------------------------- both jobs, end to end, on a tiny Qwen3
def records_file(qwen, path):
    """Two puzzles (sure: 3 correct no-hint runs) and one of the 30 (sure), each with two followed tool_real runs,
    one followed system run on the MMLU-Pro question, and one resisted run (never probed)."""
    recs = []
    for item, s in (("pilot-0", "pilot_puzzles"), ("pilot-1", "pilot_puzzles"), ("mmlupro-1308", "mmlupro_30")):
        for rep in range(3):
            recs.append(record(qwen, "none", item, s, parsed="D", repeat=rep))
        for rep in range(2):
            recs.append(record(qwen, "tool_real", item, s, repeat=rep))
    recs.append(record(qwen, "system", "mmlupro-1308", "mmlupro_30"))
    recs.append(record(qwen, "tool_real", "pilot-1", "pilot_puzzles", parsed="D", repeat=2))
    off = record(qwen, "tool_real", "pilot-1", "pilot_puzzles", repeat=2)
    recs.append({**off, "run_id": "thinking-off", "thinking": False})
    with gzip.open(path, "wt") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    return recs


def test_both_jobs_end_to_end(qwen, tmp_path):
    from _tiny_qwen3 import tiny_model_dir
    model = tiny_model_dir(tmp_path)
    recs_path = tmp_path / "sol_vllm.jsonl.gz"
    records_file(qwen, recs_path)
    out = tmp_path / "out"
    assert qm.step3(str(model), str(out), str(recs_path), dry_run=True, device="cpu") is None
    s3 = qm.step3(str(model), str(out), str(recs_path), device="cpu")
    d3 = out / qm.STEP3
    probes = qm.current_probes(d3)
    assert len(probes) == 7 and {p["condition"] for p in probes} == {"tool_real", "system"}     # followed runs only
    assert {p["half"] for p in probes} == {"localization", "replication"} and all(p["sure"] for p in probes)
    assert s3["sure_questions"] == {"localization": 2, "replication": 1} and s3["cache_check"]["over_0.05"] == 0
    assert s3["output_tokens_server_minus_rebuilt"] and all(isinstance(r["output_tokens_server_minus_rebuilt"], int)
                                                            for r in probes)
    assert s3["model"] == "Qwen/Qwen3-8B" and s3["snapshot_commit"] == "local:tiny-qwen3"
    assert qm.step3(str(model), str(out), str(recs_path), device="cpu")["groups"] == s3["groups"]   # resumes: nothing new
    assert len(qm.current_probes(d3)) == 7
    # Step 10 on planted cases (the tiny model's forced answers are random): a late takeover in every followed run
    cases = [{**{k: p[k] for k in ("source_run_id", "source_timestamp_utc", "item_id", "set", "half", "condition",
                                   "arm", "repeat", "hint_letter", "own_letter", "n_sentences")},
              "takeover_k": p["n_sentences"] - 1, "takeover_frac": 1 - 1 / p["n_sentences"]} for p in probes]
    cases_path = tmp_path / "cases.jsonl"
    cases_path.write_text(json.dumps({"cases": cases}) + "\n")
    assert qm.step10(str(model), str(out), str(recs_path), str(cases_path), dry_run=True, device="cpu") is None
    d = qm.step10(str(model), str(out), str(recs_path), str(cases_path), device="cpu", limit=3)
    assert len(list((d / "cuts").glob("*.json"))) == 3
    first = sorted(json.loads(p.read_text())["half"] for p in (d / "cuts").glob("*.json"))
    assert first == ["localization"] * 3                                      # the puzzles' cuts go first
    d = qm.step10(str(model), str(out), str(recs_path), str(cases_path), device="cpu")
    rows = [json.loads(p.read_text()) for p in (d / "cuts").glob("*.json")]
    assert len(rows) == 14 and all(r["sanity"]["ok"] and r["clean"] == "own letter" for r in rows)
    assert all(len(r["ld_patched"]["hint"]) == 4 for r in rows) and {r["cut"] for r in rows} == {"i", "ii"}
    summary = json.loads((d / "qwen8b_step10_patching.json").read_text())
    assert summary["sanity_ok"] == "14 of 14 cuts" and summary["full_attention_layers"] == [0, 1, 2, 3]
    assert set(summary["restoration_by_layer"]) == {"localization", "replication"}
    r = json.loads((d / "qwen8b_readout.json").read_text())
    assert r["localization"]["status"] == "too few" and r["replication"]["verdict"] == "no localization"
    for f in list(d3.rglob("*")) + list(d.rglob("*")):                     # numbers only: no prompt or reasoning
        if f.is_file():
            text = gzip.open(f, "rt").read() if f.suffix == ".gz" else f.read_text()
            assert MARK not in text and "Five friends" not in text and "<|im_start|>" not in text, f
    with pytest.raises(SystemExit, match="no cases"):
        empty = tmp_path / "none.jsonl"
        empty.write_text("")
        qm.step10(str(model), str(out), str(recs_path), str(empty), device="cpu")


# ---------------------------------------------------------------- Sol: run.sh, submit.sh, the job scripts
@pytest.mark.parametrize("step,args,want", [
    ("qwen8b_step3", ["--limit", "2"], ["finetune/look/qwen8b_mech.py", "step3", "--out", "{out}", "--limit", "2"]),
    ("qwen8b_step10", ["--half", "localization"],
     ["finetune/look/qwen8b_mech.py", "step10", "--out", "{out}", "--half", "localization"])])
def test_run_sh_builds_the_qwen8b_steps(tmp_path, step, args, want):
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
    r = subprocess.run(["bash", str(sol / "run.sh"), step, *args], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    check, line = [x for x in r.stdout.splitlines() if x.startswith("ARGS ")]
    assert check == "ARGS finetune/gpu/import_check.py"                    # the import check first, no vLLM
    assert line.split()[1:] == [w.format(out=out) for w in want]


def test_submit_sh_takes_the_qwen8b_jobs_and_step10_waits_for_step3(tmp_path):
    env, log = fake_sbatch(tmp_path)
    fake_squeue_jobs(tmp_path, {200: "PENDING qwen8b-step3", 201: "RUNNING trackA-step10"})
    r = submit(env, "qwen8b_step3", "--estimate", "1.2")
    assert r.returncode == 0, r.stderr
    a = sbatch_args(log)
    assert a[:2] == ["-A", ACCOUNT] and a[a.index("-t") + 1] == "2:00:00" and a[-1].endswith("qwen8b_step3.sbatch")
    r = submit(env, "qwen8b_step10", "--estimate", "4.3", "--dependency=afterok:200")
    assert r.returncode == 0, r.stderr
    a = sbatch_args(log)
    assert a[a.index("-t") + 1] == "6:00:00" and a[-1].endswith("qwen8b_step10.sbatch")
    r = submit(env, "qwen8b_step10", "--dependency=afterok:201")
    assert r.returncode == 1 and "may wait only for" in r.stderr
    r = submit(env, "qwen8b_step3", "--dependency=afterok:200")
    assert r.returncode == 1 and "waits for no other job" in r.stderr
    for f in ("qwen8b_step3.sbatch", "qwen8b_step10.sbatch"):
        text = (SOL / f).read_text()
        assert f"#SBATCH -A {ACCOUNT}" in text and "-G a100:1" in text and "--signal=B:USR1@300" in text
