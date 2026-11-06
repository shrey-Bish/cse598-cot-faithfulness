"""A41 (Nov 6; finetune/look/a18.py with A40's weights): A18's swap and Step 10 on base's own tool-hint cases with
A40's trained weights in LoRA's place. A18's own files and readings stay as they were (its swap keeps swap/, its
readout keeps a18_readout.json); A41's go beside them (swap_a40/, step10_a40_on_base/, a41_readout.json). The
pre-registered readings on planted numbers, the comparison with LoRA paired by case, the tiny-model run, the
command line and the queue lines. No GPU, no network."""
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))
sys.path.insert(0, str(CODE / "tests"))

from finetune.look import a18  # noqa: E402
from test_a18 import eval_records, lora_like, write_eval  # noqa: E402


@pytest.fixture(autouse=True)
def _fewer_resamples(monkeypatch):
    import common
    real = common.boot_mean
    monkeypatch.setattr(a18, "boot_mean", lambda g, n=20000, seed=0: real(g, n=400, seed=seed))
    real_ratio = a18.ratio_boot
    monkeypatch.setattr(a18, "ratio_boot", lambda num, den, n=20000, seed=0: real_ratio(num, den, n=400, seed=seed))


def row(q, te_base, te_trained, trained="a40", job=None, condition="tool_pasted", **hybrids):
    te = {"base": te_base, trained: te_trained, **{f"base+{trained}_{k}": v for k, v in hybrids.items()}}
    heads = {s: {"L19H31": {"hint": h, "letter": 0.0, "control": 0.01}} for s, h in (("base", 0.3), (trained, 0.1))}
    return {"job": job or f"{q}_ii", "item_id": q, "hint_letter": "G", "condition": condition, "te": te,
            "top_hinted": {"base": "G", trained: "F"}, "heads": heads}


def test_a40_takes_loras_place_and_a18s_folders_stay():
    assert a18.TRAINED == ("lora", "a40")
    assert a18.swap_dir("OUT", "lora") == Path("OUT") / "a18" / "swap"                 # A18's, unchanged
    assert a18.swap_dir("OUT", "a40") == Path("OUT") / "a18" / "swap_a40"
    assert a18.step10_name("base", "a40") == "step10_a40_on_base"


@pytest.mark.parametrize("hybrids,want,where", [
    ({"before": 4.0, "readout": 1.2, "through": 1.1, "after": 3.9}, "stops the readout", "at the readout layers"),
    ({"before": 4.0, "readout": 4.0, "through": 3.9, "after": 1.2}, "acts after the readout", None)])
def test_the_primary_reads_a40_in_loras_place(hybrids, want, where):
    rows = [row(f"q{i}", 4.0 + 0.1 * (i % 3), 1.0 + 0.1 * (i % 2), **{k: v + 0.05 * (i % 2) for k, v in hybrids.items()})
            for i in range(8)]
    res = a18.primary(rows, trained="a40")
    assert res["reading"] == want and res.get("where") == where, res
    assert res["a40_still_answers_W"] == "0 of 8" and res["reduction_a40"]["low"] > 0
    assert "reduction_lora" not in res


def test_no_reduction_reads_acts_in_the_reasoning_for_a40_too():
    rows = [row(f"q{i}", 4.0, 4.0 + (0.2 if i % 2 else -0.2), before=4, readout=4, through=4, after=4) for i in range(8)]
    assert a18.primary(rows, trained="a40")["reading"].startswith("acts in the reasoning")
    rows = [row(f"q{i}", 4.0, 1.0, before=4, readout=4, through=1, after=4) for i in range(4)]
    assert a18.primary(rows, trained="a40")["reading"] == "too few"
    h = a18.heads_same_tokens([row(f"q{i}", 4, 1) for i in range(6)], trained="a40")
    assert h["words"] == "A40's heads look at the hint less"


def test_a40_against_lora_is_paired_by_case_and_each_r_keeps_its_own_base():
    lora = [row(f"q{i}", 4.0, 5.0, trained="lora", job=f"c{i}") for i in range(8)]             # R_LoRA = -1
    a40 = [row(f"q{i}", 4.0 + 0.01 * (i % 2), 2.0, job=f"c{i}") for i in range(8)]            # R_A40 = about +2
    res = a18.against_lora(a40, lora)
    assert res["reading"] == "A40 removes more of the hint's pull than LoRA", res
    assert res["difference"]["mean"] == pytest.approx(3.005, abs=0.01) and res["questions"] == 8
    assert res["cases_matched"] == 8 and res["unmatched"] == 0
    assert res["base_effect_drift_max"] == pytest.approx(0.01)
    flipped = [row(f"q{i}", 4.0, 6.0, job=f"c{i}") for i in range(8)]                          # R_A40 = -2
    assert a18.against_lora(flipped, lora)["reading"] == "A40 removes less than LoRA"
    same = [row(f"q{i}", 4.0, 5.0 + (0.3 if i % 2 else -0.3), job=f"c{i}") for i in range(8)]
    assert a18.against_lora(same, lora)["reading"] == "no difference detected"
    few = a18.against_lora(a40[:4], lora)
    assert few["reading"] == "too few" and few["unmatched"] == 0
    small = [row(f"q{i}", 0.3, 0.1, job=f"c{i}") for i in range(8)]                            # base's effect < 0.5
    assert a18.against_lora(small, lora)["reading"] == "too few"
    extra = a40 + [row("q99", 4.0, 2.0, job="c99")]                                            # no LoRA row for it
    assert a18.against_lora(extra, lora)["unmatched"] == 1


def test_a41_readout_reads_its_own_folders_and_leaves_a18s_readout_alone(tmp_path):
    lora_tool = [row(f"q{i}", 4.0, 5.0 + 0.1 * (i % 2), trained="lora", job=f"c{i}", before=3.9, readout=4.0,
                     through=4.0, after=4.9) for i in range(8)]                         # as A18's own rows: every swap
    a40_tool = [row(f"q{i}", 4.0, 2.0 + 0.1 * (i % 2), job=f"c{i}", before=4.0, readout=1.2, through=1.1, after=3.9)
                for i in range(8)]
    a40_user = [row(f"q{i}", 4.0, 3.5 + 0.1 * (i % 2), job=f"u{i}", condition="user", before=4.0, readout=4.0,
                    through=3.9, after=1.2) for i in range(8)]
    for name, rows in (("swap", lora_tool), ("swap_a40", a40_tool + a40_user)):
        (tmp_path / name).mkdir()
        (tmp_path / name / "swap_rows.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    res = a18.a41_readout(tmp_path)
    assert res["primary"]["reading"] == "stops the readout" and res["primary"]["cases"] == 8
    assert res["against LoRA"]["reading"] == "A40 removes more of the hint's pull than LoRA"
    assert set(res["layer R (reported, no decision)"]) == set(a18.SWAPS)
    assert res["heads_same_tokens"]["words"] == "A40's heads look at the hint less"
    sec = res[a18.SECONDARY]
    assert sec["swap"]["cases"] == 8 and sec["swap"]["reading"] == "acts after the readout"
    assert json.loads((tmp_path / "a41_readout.json").read_text())["primary"]["reading"] == "stops the readout"
    a18_res = a18.readout(tmp_path)                                                           # A18's: LoRA's rows only
    assert a18_res["primary"]["cases"] == 8 and "against LoRA" not in a18_res
    assert not any("a40" in k for k in a18_res)


def test_swap_and_step10_take_a40s_weights_on_tiny_models(tmp_path, monkeypatch):
    pytest.importorskip("torch")
    from _tiny_olmo import tiny_model_dir
    from finetune.gpu import kit
    base = tiny_model_dir(tmp_path, window=16, kv_heads=2)
    a40 = lora_like(tmp_path / "a40", base) if (tmp_path / "a40").mkdir() is None else None
    monkeypatch.setattr(a18, "model_dir", lambda system, out: base if system == "base" else
                        a40 if system == "a40" else pytest.fail(f"only base and a40 here, not {system}"))
    monkeypatch.setattr(a18, "tokenizer_dir", lambda: base)
    monkeypatch.setattr(kit, "full_attention_layers", lambda model=None: [3])
    out = tmp_path / "out"
    write_eval(out / "eval", "base", eval_records("base", n_questions=1))
    a18.step3("base", out, device="cpu", limit=2)
    probes = [json.loads(x) for x in (out / "a18" / "step3_base" / "probes.jsonl").read_text().splitlines()]
    planted = [{**{k: p[k] for k in ("source_run_id", "source_timestamp_utc", "item_id", "condition", "arm", "repeat",
                                     "hint_letter", "n_sentences")}, "takeover_k": p["n_sentences"], "takeover_frac": 1.0,
                "mention_just_before": True} for p in probes]
    with open(out / "a18" / "step3_base" / "cases.jsonl", "a") as f:
        f.write(json.dumps({"rule": "planted for the test", "cases": planted}) + "\n")
    # Slurm's warning with work left: exit 2, which the feeder reads as a stop at the limit (its again= line runs)
    monkeypatch.setitem(a18._stop, "asked", True)
    for step in (lambda: a18.swap(out, device="cpu", readout=(1, 2), heads=((1, 0), (2, 1), (3, 1)), trained="a40"),
                 lambda: a18.step10("base", "a40", out, device="cpu")):
        with pytest.raises(SystemExit) as stop:
            step()
        assert stop.value.code == 2
    assert not (out / "a18" / "swap_a40" / "swap_rows.jsonl").exists()
    monkeypatch.setitem(a18._stop, "asked", False)
    sw = a18.swap(out, device="cpu", readout=(1, 2), heads=((1, 0), (2, 1), (3, 1)), trained="a40")
    assert sw == out / "a18" / "swap_a40" and not (out / "a18" / "swap").exists()
    srows = [json.loads(x) for x in (sw / "swap_rows.jsonl").read_text().splitlines()]
    assert len(srows) == 2 and all(r["trained"] == "a40" for r in srows)
    for r in srows:
        assert set(r["te"]) == {"base", "a40"} | {f"base+a40_{s}" for s in a18.SWAPS}
        assert set(r["top_hinted"]) >= {"base", "a40"} and set(r["heads"]) == {"base", "a40"}
    assert "primary (tool hints)" in json.loads((sw / "swap_primary.json").read_text())
    d = a18.step10("base", "a40", out, device="cpu")
    assert d == out / "a18" / "step10_a40_on_base"
    rows = [json.loads(p.read_text()) for p in (d / "cuts").glob("*.json")]
    assert len(rows) == 2 and all(r["weights"] == "a40" and r["cases_of"] == "base" for r in rows)
    assert (d / "step10_handoff.json").exists()


def test_the_command_line_takes_a40_for_the_swap_and_step10_only(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(a18, "swap", lambda *a, **k: seen.append(("swap", k.get("trained"))))
    monkeypatch.setattr(a18, "step10", lambda *a, **k: seen.append(("step10", a[:2])))
    monkeypatch.setattr(a18, "a41_readout", lambda d: seen.append(("a41", d)) or {})
    a18.main(["swap", "--out", str(tmp_path), "--trained", "a40", "--dry-run"])
    a18.main(["swap", "--out", str(tmp_path), "--dry-run"])
    a18.main(["step10", "--cases", "base", "--weights", "a40", "--out", str(tmp_path), "--dry-run"])
    a18.main(["a41", str(tmp_path)])
    assert seen == [("swap", "a40"), ("swap", "lora"), ("step10", ("base", "a40")), ("a41", str(tmp_path))]
    for bad in (["step10", "--cases", "a40", "--weights", "a40", "--out", "x"], ["step3", "--system", "a40", "--out", "x"],
                ["swap", "--out", "x", "--trained", "tags"]):
        with pytest.raises(SystemExit):
            a18.main(bad)


A41_LINES = """\
owner: ragarw68
a40-train-3                | -                                        | train --estimate 1.5 -- a40
a41-swap                   | afterok=@a40-train-3                     | a18 --estimate 0.8 -- swap --trained a40
a41-step10                 | afterok=@a40-train-3                     | a18 --estimate 2.3 -- step10 --cases base --weights a40
a41-step10-again           | again=@a41-step10                        | a18 --estimate 2.3 -- step10 --cases base --weights a40
"""


def test_a41s_queue_lines_parse_with_their_limits():
    sys.path.insert(0, str(CODE / "tools"))
    import sol_feeder as sf
    lines = {l.label: l for l in sf.parse_queue(A41_LINES)}
    assert [sf.limit_hours(lines[k].argv) for k in ("a41-swap", "a41-step10", "a41-step10-again")] == [1.5, 3.0, 3.0]
    assert lines["a41-swap"].argv == ["a18", "--estimate", "0.8", "--", "swap", "--trained", "a40"]
    assert lines["a41-step10-again"].opts == {"again": "@a41-step10"}
