"""A39's figures (tools/a39_figures.py), drawn from a synthetic report (tests/test_a39_synthetic.py through
finetune/a39.py --report) into a temporary folder: never from a real A39 file and never into docs/paper/figures/.
Each figure writes PNG (2000 x 1125), SVG and its CSV; every plotted number in the CSV is the report's; an incomplete
report is refused unless --draft. CPU only, no network."""
import csv
import json
import struct
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))
sys.path.insert(0, str(CODE / "tests"))
sys.path.insert(0, str(CODE / "tools"))

pytest.importorskip("transformers")
pytest.importorskip("matplotlib")

import common  # noqa: E402
from finetune import a39  # noqa: E402
from finetune import eval as ev  # noqa: E402
from test_a39_synthetic import PROFILE, build  # noqa: E402

import a39_figures as af  # noqa: E402

FIGURES = ("a39_e2_fixes", "a39_e2_parts")


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def cut(monkeypatch, qset, n):
    whole = ev.QSETS[qset]
    monkeypatch.setitem(ev.QSETS, qset, lambda: sorted(whole(), key=lambda q: q["item_id"])[:n])


@pytest.fixture
def synthetic(tmp_path, monkeypatch):
    """A complete synthetic A39 report on E2 (cut to 16 questions; the bootstraps at 400 resamples), with one no-answer
    imbalance (LoRA's runs cut at the cap far more often)."""
    monkeypatch.setattr(ev, "boot_diff", lambda a, b: common.boot_diff(a, b, n=400))
    monkeypatch.setattr(ev, "boot_mean", lambda g: common.boot_mean(g, n=400))
    cut(monkeypatch, "e2", 16)
    build(tmp_path / "runs", "e2", profile={"lora": {**PROFILE["lora"], "no_answer": 0.3}})
    a39.report(tmp_path / "runs", "e2")
    return tmp_path / "runs" / "a39_e2.json"


def rows(path):
    return list(csv.DictReader(open(path)))


def num(x):
    return None if x == "" else float(x)


def test_the_figures_draw_from_the_report_into_the_folder_given(synthetic, tmp_path):
    paths = af.main(["--report", str(synthetic), "--out", str(tmp_path / "fig")])
    assert [p.name for p in paths] == [f"{f}.{x}" for f in FIGURES for x in ("png", "svg", "csv")]
    for p in paths:
        assert p.parent == tmp_path / "fig" and p.stat().st_size > 0
    for f in FIGURES:
        assert png_size(tmp_path / "fig" / f"{f}.png") == (2000, 1125)
        table = rows(tmp_path / "fig" / f"{f}.csv")
        assert table and not any(len(v) > 80 for r in table for v in r.values())    # numbers and labels only
    assert af.OUT == CODE.parent / "docs" / "paper" / "figures"                       # the default, not used here
    assert af.REPORT == CODE / "results" / "summaries" / "trackA" / "gpu" / "a39" / "a39_e2.json"


def test_the_csvs_hold_the_report_s_numbers(synthetic, tmp_path):
    res = json.loads(synthetic.read_text())
    af.main(["--report", str(synthetic), "--out", str(tmp_path)])
    fixes, parts = rows(tmp_path / "a39_e2_fixes.csv"), rows(tmp_path / "a39_e2_parts.csv")
    key = {("base", "following"): "following_vs_base", ("base", "acceptance"): "acceptance_vs_base",
           ("prompt_only", "following"): "following", ("prompt_only", "acceptance"): "acceptance"}
    assert len(fixes) == 6 * 2 * 2                                              # R1 and R2: 6 systems, 2 measures
    for r in fixes:
        block = res["r1" if r["against"] == "base" else "r2"][r["system"]]
        d = block[key[(r["against"], r["measure"])]]
        assert (num(r["value"]), num(r["low"]), num(r["high"])) == (d["diff"], *d["interval"])
        assert int(r["questions"]) == d["questions"] and r["channel"] == "pooled"
        own = res["systems"][r["system"]][r["measure"]]["pooled"]
        other = res["systems"][r["against"]][r["measure"]]["pooled"]
        assert (int(r["k"]), int(r["n"]), int(r["compared_k"]), int(r["compared_n"])) == (
            own["k"], own["n"], other["k"], other["n"])
        na = d["no_answer"]
        assert (int(r["no_answer_k"]), int(r["no_answer_n"])) == (na["a"]["k"], na["a"]["n"])
        assert (r["no_answer_imbalance"] == "yes") == na["imbalance"]
        assert r["reading"] == (block["reading"] if r["against"] == "prompt_only" else block["verdict"]
                                + (f" ({'; '.join(block['failed'])})" if block.get("failed") else ""))
        assert (r["note"] == "diluted by design") == (r["system"] in ev.SHARED)
    assert any(r["no_answer_imbalance"] == "yes" for r in fixes if r["system"] == "lora")
    r3 = [r for r in parts if r["panel"] == "b"]
    assert len(r3) == 3 * 2 * 3                                                 # 3 combinations, 2 parts, 3 measures
    for r in r3:
        e = res["r3"][r["system"]]
        d = e[f"minus {r['against']}"][r["measure"]]
        assert (num(r["value"]), num(r["low"]), num(r["high"])) == (d["diff"], *d["interval"])
        assert r["reading"] == e["reading"] and r["channel"] == ("no hint" if r["measure"] == "accuracy" else e["channel"])
    r4 = {(r["measure"], r["channel"]): r for r in parts if r["panel"] == "c"}
    assert set(r4) == {("following", "inserted"), ("acceptance", "inserted"), ("accuracy", "no hint"),
                       ("following", "pasted")}
    for (m, ch), r in r4.items():
        d = res["r4"]["pasted_check"]["following_minus_base"] if ch == "pasted" else res["r4"][m]
        assert (num(r["value"]), num(r["low"]), num(r["high"])) == (d["diff"], *d["interval"])
        assert (r["system"], r["against"]) == ("wrap", "base")
    assert num(r4[("following", "pasted")]["value"]) == 0 and r4[("following", "pasted")]["reading"] == "exactly 0: True"
    assert r4[("following", "inserted")]["reading"] == res["r4"]["reading"]


def test_an_incomplete_report_is_refused_unless_a_draft(synthetic, tmp_path):
    res = json.loads(synthetic.read_text())
    res["complete"] = False
    res["completeness"]["lora"]["missing"] = 9
    bad = tmp_path / "a39_e2.json"
    bad.write_text(json.dumps(res))
    with pytest.raises(SystemExit, match="not every A39 part is in"):
        af.main(["--report", str(bad), "--out", str(tmp_path / "fig")])
    assert not (tmp_path / "fig").exists()
    paths = af.main(["--report", str(bad), "--out", str(tmp_path / "fig"), "--draft"])
    assert all(p.exists() for p in paths)
    assert "DRAFT" in (tmp_path / "fig" / "a39_e2_fixes.svg").read_text()


def test_too_few_questions_and_missing_runs_are_written_not_drawn(tmp_path, monkeypatch):
    monkeypatch.setattr(ev, "boot_diff", lambda a, b: common.boot_diff(a, b, n=400))
    monkeypatch.setattr(ev, "boot_mean", lambda g: common.boot_mean(g, n=400))
    cut(monkeypatch, "mmlupro_30", 4)
    build(tmp_path, "mmlupro_30", systems=tuple(s for s in ev.A39_SYSTEMS if s != "lora_wrap"))
    a39.report(tmp_path, "mmlupro_30")
    paths = af.main(["--report", str(tmp_path / "a39_mmlupro_30.json"), "--out", str(tmp_path / "fig"), "--draft"])
    assert [p.name for p in paths][::3] == ["a39_mmlupro_30_fixes.png", "a39_mmlupro_30_parts.png"]
    table = rows(tmp_path / "fig" / "a39_mmlupro_30_fixes.csv") + rows(tmp_path / "fig" / "a39_mmlupro_30_parts.csv")
    assert all(r["value"] == r["low"] == r["high"] == "" for r in table)
    assert {r["interval"] for r in table} <= {"too few questions", "missing runs"}
    assert {r["reading"] for r in table if r["system"] == "lora_wrap" and r["panel"] == "b"} == {"missing runs"}
    svg = (tmp_path / "fig" / "a39_mmlupro_30_parts.svg").read_text()
    assert "too few questions" in svg and "missing runs" in svg
