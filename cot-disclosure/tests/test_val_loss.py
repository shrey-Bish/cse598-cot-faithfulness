"""Track A: the validation loss by part (finetune/val_loss.py) on a tiny random Olmo 3 with the real tokenizer
and template: each reply token in exactly one part, the opener / check sentences / final answer where they
belong, base vs each version's epochs, and the overall loss equal to train.validation_loss. CPU only."""
import gzip
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "tests"))

torch = pytest.importorskip("torch")
pytest.importorskip("peft")

from _tiny_olmo import tiny_model_dir  # noqa: E402
from finetune import train as tr  # noqa: E402
from finetune import val_loss as vl  # noqa: E402
from finetune.make_targets import REASONING_OPENERS  # noqa: E402
from tools.answer_key import TOOL_SPEC, build  # noqa: E402

OPENER_TOOL, OPENER_USER = REASONING_OPENERS["tool"][2], REASONING_OPENERS["user"][0]
CHECK = "The pasted tool result says (B), but my own working gives (A), so I keep (A)."


def example(i, cond, method, raw, wording=None):
    msgs, _ = build(f"Question {i}?\n(A) one\n(B) two", f"q{i}", cond, None if cond == "none" else "B")
    side = "user" if cond == "user" else "tool"
    return {"record_id": f"q{i}|{cond}|{method}", "messages": msgs, "tools": [TOOL_SPEC] if cond == "tool_injected" else None,
            "hint_channel": cond, "hint_wording": wording, "hint_letter": None if cond == "none" else "B",
            "target_answer": "A", "target_method": method, "target_raw": raw,
            "openers": {"reasoning": [side, 2 if side == "tool" else 0], "final": [side, 0]} if method == "prefill" else None}


EXAMPLES = [
    example(0, "tool_injected", "prefill", OPENER_TOOL + " One and one make two. The tool says (B), which I check now. "
            "So it is A.</think>\n\nThe tool suggested (B). My working gives (A). Answer: (A)"),
    example(1, "user", "prefill", OPENER_USER + " Counting gives A. My friend picked (B), so I compare. It is A.</think>"
            "\n\nYou suggested (B). Answer: (A)", wording="user_p1"),
    example(2, "tool_pasted", "inserted_sentence", "I add the numbers. It is A.\n\n" + CHECK + "\n</think>\n\nThe pasted "
            "tool result says (B); I checked it against my own working and did not use it.\n\nAnswer: (A)"),
    example(3, "none", "nohint_run", "I add the numbers. It is A.</think>\n\nAnswer: (A)")]


@pytest.fixture(scope="module")
def tiny(tmp_path_factory):
    d = tiny_model_dir(tmp_path_factory.mktemp("m"))
    from transformers import AutoTokenizer
    return d, AutoTokenizer.from_pretrained(d)


def text_of(tok, e, part):
    return tok.decode([t for t, p in zip(e["ids"][-e["n_target"]:], e["parts"]) if p == part])


def test_each_reply_token_has_one_part_where_it_belongs(tiny):
    _, tok = tiny
    enc = [vl.encode(tok, x) for x in EXAMPLES]
    for e, x in zip(enc, EXAMPLES):
        plain = tr.encode(tok, x)
        assert e["ids"] == plain["ids"] and e["labels"] == plain["labels"]          # training's tokens and labels
        assert len(e["parts"]) == e["n_target"] == sum(y != -100 for y in e["labels"])
        assert text_of(tok, e, "final").endswith("Answer: (A)<|endoftext|>") and "think>" in text_of(tok, e, "final")
        assert "Answer" not in text_of(tok, e, "rest") + text_of(tok, e, "hint_check")
    tool, user, inserted, nohint = enc
    assert text_of(tok, tool, "opener") == OPENER_TOOL and text_of(tok, user, "opener") == OPENER_USER
    assert text_of(tok, tool, "hint_check").strip() == "The tool says (B), which I check now."
    assert "One and one make two." in text_of(tok, tool, "rest") and "The tool" not in text_of(tok, tool, "rest")
    assert text_of(tok, user, "hint_check").strip() == "My friend picked (B), so I compare."      # the wording's word
    assert text_of(tok, inserted, "hint_check").strip() == CHECK and "opener" not in inserted["parts"]
    assert set(nohint["parts"]) == {"rest", "final"}
    counts = vl.part_counts(enc)
    n = {p: sum(e["parts"].count(p) for e in enc) for p in vl.PARTS}
    assert counts["taught"] == n["opener"] + n["hint_check"] + sum(e["parts"].count("final") for e in enc[:3])
    assert counts["final_no_hint"] == nohint["parts"].count("final") and counts["overall"] == sum(n.values())
    assert counts["taught"] + counts["not_taught"] == counts["overall"] == counts["hinted"] + counts["no_hint"]


def test_an_opener_that_is_not_there_is_refused(tiny):
    _, tok = tiny
    bad = {**EXAMPLES[0], "target_raw": "Something else.</think>\n\nAnswer: (A)"}
    with pytest.raises(ValueError, match="does not start with its opener"):
        vl.encode(tok, bad)


def write_validation(path):
    with gzip.open(path, "wt") as f:
        for x in EXAMPLES:
            f.write(json.dumps(x) + "\n")
    return path


def test_base_and_each_epoch_against_train_validation_loss(tiny, tmp_path, capsys):
    d, tok = tiny
    val = write_validation(tmp_path / "validation.jsonl.gz")
    data = tr.usable(tr.encode(tok, x) for x in EXAMPLES)
    lm = tr.build("lora", d, dtype="fp32", device="cpu", attn="eager", checkpointing=False)   # LoRA B = 0: the base model
    same, _ = tr.validation_loss(lm, data, "cpu")
    tr.save_state(lm, tmp_path / "train" / "lora" / "epoch1", {"epoch": 1, "validation_loss": same})
    with torch.no_grad():
        for n, p in tr.trainable(lm).items():
            if "lora_B" in n:
                p.add_(0.05)
    moved, _ = tr.validation_loss(lm, data, "cpu")
    tr.save_state(lm, tmp_path / "train" / "lora" / "epoch2", {"epoch": 2, "validation_loss": moved})
    out = tmp_path / "out"
    res = vl.run(["lora"], tmp_path / "train", out, model=str(d), validation=val, device="cpu", dtype="fp32", attn="eager")
    s = res["systems"]
    assert list(s) == ["base", "lora/epoch1", "lora/epoch2"]
    assert abs(s["base"]["groups"]["overall"]["loss"] - same) < 1e-5                # base = LoRA with B = 0
    for g in vl.GROUPS:
        if s["base"]["groups"][g]["tokens"]:
            assert abs(res["minus_base"]["lora/epoch1"][g]) < 1e-5
    assert abs(s["lora/epoch1"]["overall_minus_state"]) < 1e-5 and abs(s["lora/epoch2"]["overall_minus_state"]) < 1e-5
    assert abs(res["minus_base"]["lora/epoch2"]["overall"]) > 1e-4                   # the epoch's weights were loaded
    assert s["base"]["groups"]["taught"]["tokens"] == res["part_tokens"]["taught"] > 0
    saved = json.loads((out / "val_loss.json").read_text())
    assert saved["minus_base"] == res["minus_base"] and saved["examples"] == 4
    rows = [json.loads(x) for x in (out / "val_loss_examples.jsonl").read_text().splitlines()]
    assert len(rows) == 12 and {r["system"] for r in rows} == set(s)
    assert not any(isinstance(v, str) and len(v) > 200 for r in rows for v in r.values())        # numbers and ids only
    capsys.readouterr()
    vl.run(["lora"], tmp_path / "train", out, model=str(d), validation=val, device="cpu", dtype="fp32", attn="eager")
    assert capsys.readouterr().out.count("done before; skipped") == 3
    assert len((out / "val_loss_examples.jsonl").read_text().splitlines()) == 12       # nothing doubled
    with pytest.raises(SystemExit, match="no checkpoint in"):
        vl.run(["tags"], tmp_path / "train", out, model=str(d), validation=val, device="cpu")
    rep = vl.report(out, out=tmp_path / "report.json")["minus_base"]                    # back on the Mac
    assert set(rep) == {"lora/epoch1", "lora/epoch2"}
    for g in ("taught", "not_taught", "overall"):                                   # the same points as val_loss.json
        assert abs(rep["lora/epoch2"][g]["minus_base"] - res["minus_base"]["lora/epoch2"][g]) < 1e-9
    e = rep["lora/epoch2"]["taught"]
    assert e["items"] == len({x["record_id"].split("|")[0] for x in EXAMPLES if x["hint_channel"] != "none"})
    if e["items"] > 1:
        assert e["interval"][0] <= e["minus_base"] <= e["interval"][1]
    assert abs(rep["lora/epoch1"]["overall"]["minus_base"]) < 1e-5
    tn = rep["lora/epoch2"]["taught_no_opener"]
    hc, fh = rep["lora/epoch2"]["hint_check"], rep["lora/epoch2"]["final_hinted"]
    assert tn["tokens"] == hc["tokens"] + fh["tokens"]
    assert abs(tn["minus_base"] * tn["tokens"] - hc["minus_base"] * hc["tokens"] - fh["minus_base"] * fh["tokens"]) < 1e-9
    assert json.loads((tmp_path / "report.json").read_text())["bootstrap"].startswith("paired, clustered by question")


def test_dry_run_counts_parts_without_a_model(tiny, tmp_path, capsys):
    d, _ = tiny
    counts, (lo, hi) = vl.dry_run(write_validation(tmp_path / "v.jsonl.gz"), str(d), ["lora", "tags"])
    assert counts["overall"] > counts["taught"] > 0 and 0 < lo <= hi
    assert "5 systems (base + lora, tags x 2 epochs), 3 models built" in capsys.readouterr().out
    assert vl.predicted_minutes(5, 3, vl.VAL_TOKENS) == [25.5, 45.0]


def test_the_contrast_per_channel_and_injected_minus_pasted():
    """lora_tags minus lora per channel, and injected minus pasted of that, in the same resamples."""
    b = {f"q{i}": {"taught | tool_injected": [10, 5.0], "taught | tool_pasted": [10, 4.0], "taught | user": [10, 3.0],
                   "taught": [30, 12.0], "taught_no_opener": [20, 8.0]} for i in range(6)}
    a = {q: {g: [n, s - (1.0 if g in ("taught | tool_injected", "taught") else 0.0)] for g, (n, s) in v.items()}
         for q, v in b.items()}
    res = vl.contrast(a, b, n=200)
    assert abs(res["taught | tool_injected"]["diff"] + 0.1) < 1e-12 and res["taught | tool_pasted"]["diff"] == 0.0
    assert abs(res["injected minus pasted"]["diff"] + 0.1) < 1e-12 and res["injected minus pasted"]["items"] == 6
    assert res["injected minus pasted"]["interval"][0] <= -0.1 <= res["injected minus pasted"]["interval"][1]
    assert abs(res["taught | tool_injected"]["b_loss"] - 0.5) < 1e-12 and res["injected minus pasted"]["b_loss"] is None

