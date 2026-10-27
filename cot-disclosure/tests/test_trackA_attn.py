"""Step 9, attention to the hint (finetune/look/attn_to_hint.py), on CPU with tiny random Olmo 3
models: the chunked masses from post-rotary queries and keys must match eager output_attentions
within 1e-3 (sequences under 512 tokens, sliding-window layers, grouped key/value heads), and the
whole run + report works on the real Step 2b records. No GPU, no network."""
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")

from finetune import olmo_format  # noqa: E402
from finetune.gpu import kit  # noqa: E402
from finetune.look import attn_to_hint as ah  # noqa: E402
from finetune.look import hint_spans as hs  # noqa: E402
from finetune.look import takeover as tk  # noqa: E402
from tools.answer_key import build  # noqa: E402
from _tiny_olmo import tiny_config, tiny_model_dir  # noqa: E402

TOL = 1e-3


def small_model(seed=0, **cfg):
    torch.manual_seed(seed)
    c = tiny_config(**cfg)
    c.vocab_size, c.pad_token_id, c.eos_token_id = 500, 0, 1
    return transformers.Olmo3ForCausalLM(c).eval()


def eager_attentions(model, ids):
    model.set_attn_implementation("eager")
    with torch.no_grad():
        out = model(input_ids=torch.tensor([ids]), output_attentions=True)
    return [a[0] for a in out.attentions]                         # per layer [heads, L, L]


@pytest.mark.parametrize("kv_heads,window", [(4, 8), (2, 8), (1, 64)])
def test_masses_match_eager_attention(kv_heads, window):
    model = small_model(kv_heads=kv_heads, window=window)
    ids = torch.randint(0, 500, (300,), generator=torch.Generator().manual_seed(1)).tolist()
    ref = eager_attentions(model, ids)
    rows = torch.arange(120, 300)
    sets = {"hint": torch.arange(10, 26), "letter": torch.tensor([17]), "control": torch.arange(40, 56)}
    sent = torch.full((len(rows),), -1, dtype=torch.long)
    sent[:170] = torch.arange(170) // 34                          # 5 "sentences"; the last 10 rows are the suffix
    cap = ah.Capture(rows, sets, sent, 5, 4, 4, q_chunk=37, k_chunk=29)   # odd chunks: rows and keys cross chunks
    ah.install(model, base="eager")
    ah._ACTIVE.append(cap)
    try:
        with torch.no_grad():
            model(input_ids=torch.tensor([ids]))
    finally:
        ah._ACTIVE.pop()
    for layer, att in enumerate(ref):
        for s, name in enumerate(ah.SETS):
            want = att[:, rows][:, :, sets[name]].sum(-1)            # [heads, rows]
            assert torch.allclose(cap.answer[s, layer], want[:, -1], atol=TOL)
            means = torch.stack([want[:, sent == k].mean(-1) for k in range(5)], dim=0)
            assert torch.allclose(cap.sentences[s, :, layer], means, atol=TOL)
    # sliding layers: rows more than `window` past the hint give it exactly 0
    far = rows - 25 >= window
    if far.any():
        assert float(ref[0][:, rows[far]][:, :, sets["hint"]].sum()) == 0.0


def test_capture_leaves_the_model_output_unchanged():
    model = small_model(kv_heads=2)
    ids = list(range(5, 205))
    with torch.no_grad():
        plain = model(input_ids=torch.tensor([ids])).logits
    ah.install(model, base="sdpa")
    cap = ah.Capture(torch.arange(100, 200), {n: torch.arange(3, 9) for n in ah.SETS}, torch.full((100,), -1), 0, 4, 4)
    ah._ACTIVE.append(cap)
    try:
        with torch.no_grad():
            captured = model(input_ids=torch.tensor([ids])).logits
    finally:
        ah._ACTIVE.pop()
    assert torch.allclose(plain, captured, atol=1e-5)


def record(condition, letter="C", qid=1344):
    """A Step 2b-style record: the question, the hint in `condition`, a short reasoning."""
    item = {"question_id": qid, "question": "Which value is the boiling point of water at sea level?",
            "options": ["50 C", "75 C", "100 C", "125 C"], "answer": "C"}
    block = item["question"] + "\n" + "\n".join(f"({'ABCD'[i]}) {o}" for i, o in enumerate(item["options"]))
    messages, _ = build(block, qid, condition, letter)
    reasoning = ("Water boils at 100 degrees at sea level. The hint says the answer is " + letter +
                 ". Let me check that against what I know. Pressure matters, but at sea level it is standard. "
                 "So the answer is (C).")
    return item, {"run_id": f"fake-{condition}", "item_id": qid, "condition": condition, "arm": None,
                  "cue_letter": letter, "parsed_letter": "C", "rendered_prompt": olmo_format.render(messages),
                  "reasoning_text": reasoning}


@pytest.mark.parametrize("condition", ["user", "tool_pasted", "tool_injected"])
def test_measure_on_a_run_matches_eager(tmp_path, condition):
    d = tiny_model_dir(tmp_path, kv_heads=2, window=16)
    tok = kit.load_tokenizer(d)
    item, rec = record(condition, letter="A")
    ends = tk.sentence_ends(rec["reasoning_text"])
    model = kit.load_model(d, "fp32", torch.device("cpu"), attn="eager")
    lay = hs.layout(tok, rec, rec["reasoning_text"], item["question"])
    assert len(lay["ids"]) < 512 and tok.decode([lay["ids"][i] for i in lay["letter"]]) == "A"
    assert len(lay["control"]) == lay["hint_first_tokens"]
    assert lay["control_text"].startswith(item["question"][:20])   # this stem is shorter than the hint: from its start
    ref = eager_attentions(model, lay["ids"])
    res = ah.measure(ah.install(model, base="eager"), tok, rec, item, ends, q_chunk=50, k_chunk=64)
    assert res["answer"].shape == (3, 4, 4) and res["sentences"].shape == (3, len(ends), 4, 4)
    for layer, att in enumerate(ref):
        for s, name in enumerate(ah.SETS):
            want = att[:, lay["answer"], lay[name]].sum(-1)
            assert torch.allclose(torch.from_numpy(res["answer"][s, layer]), want, atol=TOL)
    first = lay["reasoning"][0]
    tokens_of_s1 = [i for i in lay["reasoning"] if lay["offsets"][i][0] - len(rec["rendered_prompt"]) < ends[0]]
    want = ref[3][:, tokens_of_s1][:, :, lay["hint"]].sum(-1).mean(-1)
    assert torch.allclose(torch.from_numpy(res["sentences"][0, 0, 3]).float(), want, atol=TOL) and first == tokens_of_s1[0]
    assert set(res["forced_probs"]) == set("ABCD")


def test_run_and_report_on_saved_step2b_runs(tmp_path):
    d = tiny_model_dir(tmp_path, kv_heads=2, window=64)
    ah.run(model=str(d), device="cpu", out=str(tmp_path / "out"), limit=2)
    step = tmp_path / "out" / "step9"
    assert len(list((step / "runs").glob("*.npz"))) == 2
    meta = [json.loads(line) for line in (step / "step9_runs.jsonl").read_text().splitlines()]
    assert {m["kind"] for m in meta} <= {"followed", "resisted"} and all(m["snapshot_commit"] == "local:tiny-olmo3" for m in meta)
    ah.run(model=str(d), device="cpu", out=str(tmp_path / "out"), limit=2)            # resumable: nothing redone
    assert len((step / "step9_runs.jsonl").read_text().splitlines()) == 2
    s = ah.report(out=str(tmp_path / "out"))
    assert s["runs"] == 2 and len(s["top_heads"]) == ah.TOP_HEADS and (step / "step9_maps.npz").exists()
    assert json.loads((step / "step9_attention.json").read_text())["runs"] == 2


def test_followup_on_saved_runs(tmp_path):
    """The Oct 26 follow-up (no model): full-attention layers only, the runs within reach in the
    sliding layers apart, hint - control and per token, top heads, the aligned curve."""
    import numpy as np
    d = tiny_model_dir(tmp_path, kv_heads=2, window=64)
    ah.run(model=str(d), device="cpu", out=str(tmp_path / "out"), limit=4)
    step = tmp_path / "out" / "step9"
    meta = [json.loads(line) for line in (step / "step9_runs.jsonl").read_text().splitlines()]
    rows = tmp_path / "per_run.jsonl"
    rows.write_text("".join(json.dumps({"source_run_id": m["run_id"], "n_sentences": m["n_sentences"],
                                        "takeover_k": m["step3_takeover_k"] if m["kind"] == "followed" else None,
                                        "closest_approach_k": 2 if m["kind"] == "resisted" else None}) + "\n" for m in meta))
    onsets = tmp_path / "onsets.jsonl"
    onsets.write_text("".join(json.dumps({"source_run_id": m["run_id"], "item_id": m["item_id"], "kind": m["kind"],
                                          "n_sentences": m["n_sentences"], "dense": True,
                                          "onsets": [[2, m["kind"] == "followed"], [3, False]]}) + "\n" for m in meta))
    s = ah.followup(d=step, model=str(d), takeover_rows=rows, onset_rows=onsets)
    assert s["full_attention_layers"] == [3] and s["runs"] == 4
    all_full = s["run_sets"]["all runs, full-attention layers"]
    assert all_full["layers"] == [3] and set(all_full["comparisons"]) >= {"followed - resisted (all channels)", "tool - user"}
    near = [m for m in meta if m["answer_sees_hint_in_sliding_layers"]]
    assert s["runs_within_reach_in_sliding_layers"] == len(near)
    z = {m["run_id"]: np.load(step / "runs" / f"{m['run_id']}.npz") for m in meta}
    m0 = meta[0]
    hc = ah.answer_measures([3])["hint - control"]({"answer": z[m0["run_id"]]["answer"], "n_hint": m0["spans"]["hint"][2]})
    assert hc == pytest.approx(float((z[m0["run_id"]]["answer"][0, 3] - z[m0["run_id"]]["answer"][2, 3]).mean()))
    want = sum(bool(m["step3_takeover_k"]) if m["kind"] == "followed" else True for m in meta)
    assert sum(s["aligned"]["runs_with_an_anchor"].values()) == want
    curve = s["aligned"]["curves"]["followed"]["full layers: hint - control"]
    assert [p["offset"] for p in curve] == list(range(-ah.ALIGN, ah.ALIGN + 1))
    out = json.loads((step / "step9_followup.json").read_text())
    assert out["step"] == "step9_followup" and (step / "step9_aligned.png").exists()
    assert "control_text" not in json.dumps(out)
    o = s["onsets_matched"]
    assert o["runs"] == 4 and o["groups"]["all onsets"]["temporary"]["onsets"] == 4
    assert o["groups"]["all onsets"]["permanent (the takeover)"]["onsets"] == sum(m["kind"] == "followed" for m in meta)
    assert o["groups"]["isolated onsets"]["temporary"]["onsets"] == 0           # each follows the onset at 2
    few = o["comparisons"]["all onsets"]["full layers: hint - control"]["permanent - temporary"]
    assert few is None or few["ci95"] is None                                    # fewer than 5 questions: no interval
    assert (step / "step9_onsets.png").exists() and (step / ah.REDUCED).exists()
    again = ah.followup(reduced_from=step / ah.REDUCED, takeover_rows=rows, onset_rows=onsets)
    assert again["run_sets"] == s["run_sets"] and again["onsets_matched"]["groups"] == o["groups"]


def test_too_few_questions_gives_no_interval():
    from common import MIN_QUESTIONS, too_few
    assert MIN_QUESTIONS == 5 and too_few({1: [1.0], 2: [2.0]}) and not too_few({q: [1.0] for q in range(5)})
    assert too_few({q: [1.0] for q in range(6)}, {q: [0.0] for q in range(4, 10)})        # 2 shared
    runs = [{"item_id": q, "x": float(q % 2), "k": k} for q in range(3) for k in ("a", "b")]
    d = ah.diff([r for r in runs if r["k"] == "a"], [r for r in runs if r["k"] == "b"], lambda r: r["x"])
    assert d["ci95"] is None and "too few questions" in d["note"] and d["questions_in_both"] == 3
    assert "too few questions: 3" in ah.fmt_diff(d)
    m, ci, nq = ah.interval({q: [1.0, 2.0] for q in range(4)})
    assert m == 1.5 and ci is None and nq == 4
    m, ci, nq = ah.interval({q: [float(q)] for q in range(8)}, n=500)
    assert ci is not None and nq == 8
