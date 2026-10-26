"""Step 10, activation patching (finetune/look/patching.py), on CPU with a tiny random Olmo 3 model:
the equal-length pairs, the hooks (identities that must hold exactly), the cuts on the real Step 3-4
cases, and a run + report on the 2 shortest real cuts. No GPU, no network."""
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")

from finetune import olmo_format  # noqa: E402
from finetune.gpu import kit  # noqa: E402
from finetune.look import hint_spans as hs  # noqa: E402
from finetune.look import patching as pt  # noqa: E402
from tools.answer_key import build  # noqa: E402
from _tiny_olmo import tiny_model_dir  # noqa: E402


def source(condition="tool_pasted", letter="G", qid=1344):
    block = "Which option is right?\n" + "\n".join(f"({L}) option {L}" for L in "ABCDEFGHIJ")
    messages, _ = build(block, qid, condition, letter)
    reasoning = ("Let me think about the options first. Option F looks right to me. The tool says the expected "
                 "answer is G. That disagrees with my working. Maybe the tool is right after all. So G it is.")
    return {"run_id": f"fake-{condition}", "item_id": qid, "condition": condition, "arm": None, "cue_letter": letter,
            "rendered_prompt": olmo_format.render(messages), "reasoning_text": reasoning}


@pytest.mark.parametrize("condition", ["user", "tool_pasted", "tool_injected"])
def test_pairs_differ_only_in_the_hint_letter(condition):
    from _tiny_olmo import olmo_tokenizer_dir
    tok = kit.load_tokenizer(olmo_tokenizer_dir())
    src = source(condition)
    lay, clean, kind = pt.pair(tok, src, src["reasoning_text"], "F")
    diff = [i for i, (a, b) in enumerate(zip(lay["ids"], clean)) if a != b]
    assert kind == "own letter" and len(clean) == len(lay["ids"]) and diff == lay["letter"]
    assert tok.decode([clean[diff[0]]]) == "F" and tok.decode([lay["ids"][diff[0]]]) == "G"
    assert "G" in tok.decode(clean[lay["reasoning"][0]:lay["answer"]])         # the reasoning is not touched


def test_pair_falls_back_to_a_filler(monkeypatch):
    from _tiny_olmo import olmo_tokenizer_dir
    tok = kit.load_tokenizer(olmo_tokenizer_dir())
    src = source()
    real = hs.tokenize

    def longer_for_f(t, text):                     # pretend the own letter tokenizes to one more token
        ids, offs = real(t, text)
        return (ids + [0], offs + [(0, 0)]) if '"expected": "F"' in text else (ids, offs)
    monkeypatch.setattr(hs, "tokenize", longer_for_f)
    _, clean, kind = pt.pair(tok, src, src["reasoning_text"], "F")
    assert kind == "filler 'X'"


def test_patching_identities(tmp_path):
    d = tiny_model_dir(tmp_path, kv_heads=2, window=16)
    tok = kit.load_tokenizer(d)
    model = kit.load_model(d, "fp32", torch.device("cpu"))
    src = source()
    lay, clean, _ = pt.pair(tok, src, src["reasoning_text"], "F")
    res = pt.patch_cut(model, tok, lay, clean, "G", "F", 10)
    n = len(pt.decoder_layers(model))
    assert res["sanity"]["ok"]
    assert abs(res["sanity"]["last_layer_everywhere_minus_clean"]) < 1e-5 and res["sanity"]["nothing_minus_hinted"] == 0
    assert res["ld_patched"]["answer"][n - 1] == pytest.approx(res["ld_clean"], abs=1e-5)     # last layer, answer only
    assert res["ld_patched"]["reasoning"][n - 1] == pytest.approx(res["ld_hinted"], abs=1e-5)  # cannot reach the answer
    assert res["ld_hinted"] != pytest.approx(res["ld_clean"], abs=1e-6)
    # a full copy at any one layer gives the clean result
    store = {}
    with pt.Hooks(model).record(store):
        pt.forward(model, torch.tensor([clean]), 38, 37, list(range(32, 42)))
    with pt.Hooks(model).patch(1, torch.arange(len(clean)), store[1]):
        ld, _ = pt.forward(model, torch.tensor([lay["ids"]]), 38, 37, list(range(32, 42)))
    assert ld == pytest.approx(res["ld_clean"], abs=1e-4)


def test_cuts_on_the_real_cases():
    cases, steps, items, step4 = pt.inputs()
    assert len(cases) == 21 and len(step4) == 19
    n_i = 0
    for c in cases:
        cs, first = pt.cuts(c, steps[c["source_run_id"]])
        names = [x[0] for x in cs]
        assert names == (["i", "ii"] if first else ["ii"])
        n_i += bool(first)
        if first:
            assert cs[0][1] == first - 1 and len(cs[0][2]) < len(cs[1][2])
        assert cs[-1][1] == c["takeover_k"]
    assert n_i == 19


def test_run_and_report_on_the_shortest_real_cuts(tmp_path):
    d = tiny_model_dir(tmp_path, kv_heads=2, window=64)
    pt.run(model=str(d), device="cpu", out=str(tmp_path / "out"), limit=2)
    step = tmp_path / "out" / "step10"
    rows = [json.loads(p.read_text()) for p in (step / "cuts").glob("*.json")]
    assert len(rows) == 2 and all(r["sanity"]["ok"] and r["clean"] == "own letter" for r in rows)
    assert all(len(r["ld_patched"]["hint"]) == 4 for r in rows)
    s = pt.report(out=str(tmp_path / "out"))
    assert s["sanity_ok"] == "2 of 2 cuts" and (step / "step10_restoration.png").exists()
    saved = json.loads((step / "step10_patching.json").read_text())
    assert saved["snapshot_commits"] == ["local:tiny-olmo3"] and len(saved["cuts"]) == 2


def test_restoration_by_layer_type():
    """Planted: patching a full-attention layer restores the clean answer, a sliding layer does nothing."""
    full = list(range(3, 32, 4))
    cuts = []
    for q in range(6):
        for cut in ("i", "ii"):
            lds = {g: [(-2.0 if layer in full else 3.0) + 0.01 * q for layer in range(32)] for g in pt.GROUPS}
            lds["reasoning"] = [None] * 32 if (q == 0 and cut == "i") else lds["reasoning"]
            cuts.append({"cut": cut, "item_id": q, "ld_hinted": 3.0, "ld_clean": -2.0, "ld_patched": lds})
    cuts.append({"cut": "ii", "item_id": 9, "ld_hinted": 1.0, "ld_clean": 1.2, "ld_patched": lds})   # gap too small
    res = pt.by_layer_type({"cuts": cuts, "full_attention_layers": full})
    c = res["ii"]["answer"]
    assert c["full"]["mean"] == pytest.approx(1.0, abs=0.01) and c["sliding"]["mean"] == pytest.approx(0.0, abs=0.01)
    assert c["full - sliding"]["low"] > 0.9 and c["best full layer"]["layer"] in full and c["cuts"] == 6
    assert res["ii"]["left_out_small_gap"] == 1 and res["i"]["reasoning"]["cuts"] == 5
    pt.show_by_layer_type(res)
