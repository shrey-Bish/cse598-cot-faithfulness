"""A40's and A42's figure (tools/a40_figures.py), drawn from small planted reports with the real keys of finetune/a40.py's
and finetune/a42.py's reports, into a temporary folder: never from a real file and never into docs/paper/figures/. The
figure writes PNG (2000 x 1125), SVG and its CSV; every plotted difference in the CSV is the report's, with its reading;
A42's vs_a40 (no decision) is not drawn; an incomplete report is refused unless --draft. CPU only, no network."""
import copy
import csv
import json
import struct
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "tools"))

pytest.importorskip("matplotlib")

import a40_figures as af  # noqa: E402

FIGURE = "a40_e2_fixes"
SYSTEMS_A40 = ("base", "prompt_only", "lora", "a40")
SYSTEMS_A42 = ("base", "prompt_only", "a40", "a40_note")


def d(v, lo, hi, q=120, imbalance=False):
    """One difference as a39.minus writes it (fractions)."""
    return {"diff": v, "interval": [lo, hi], "questions": q,
            "no_answer": {"a": {"k": 9 if imbalance else 3, "n": 100}, "b": {"k": 1, "n": 100},
                          "gap": 0.08 if imbalance else 0.02, "imbalance": imbalance}}


def system(i):
    """A system's own X of Y (a39.summary's keys), distinct per system."""
    x = lambda k, n: {"k": k, "n": n, "rate": k / n, "wilson": [0, 1], "questions": 16, "clustered": [0, 1]}  # noqa
    return {"runs": 192, "shared": 0, "no_answer": 2, "accuracy": x(20 + i, 32),
            "following": {"pooled": x(40 + i, 95)}, "acceptance": {"pooled": x(50 + i, 64)}}


def against(base, reading, imbalance=False):
    """a40.against's keys: four pooled differences, the reading, the accuracy label and the channels beside them."""
    return {"following": d(base, base - 0.05, base + 0.05), "acceptance": d(base / 2, base / 2 - 0.04, base / 2 + 0.04,
                                                                            imbalance=imbalance),
            "accuracy": d(-0.011, -0.05, 0.03, q=15), "hiding": d(-0.1, -0.15, -0.05), "reading": reading,
            "accuracy_label": None, "no_answer_imbalance": ["acceptance"] if imbalance else [],
            "by_channel": {"user": {"following": d(base, -0.3, -0.1), "acceptance": {"diff": None, "interval":
                                    "too few questions", "questions": 0}}}}


def r1(base, verdict="passes", failed=()):
    return {"following_vs_base": d(base, base - 0.05, base + 0.05), "nohint_accuracy_vs_base": d(-0.027, -0.07, 0.02),
            "hiding_vs_base": d(-0.2, -0.25, -0.15), "acceptance_vs_base": d(base / 2, base / 2 - 0.05, base / 2 + 0.05),
            "gate3": {}, "verdict": verdict, "failed": list(failed), "criteria": {}, "no_answer_imbalance": []}


def head(systems):
    return {"generated_utc": "2026-11-07T00:00:00+00:00", "qset": "e2", "complete": True,
            "completeness": {s: {"expected": 192, "ok": 192, "missing": 0} for s in systems},
            "bootstrap": "paired by question (clustered)", "measures": "A39's", "label": "complete: 16 questions",
            "questions": 16, "systems": {s: system(i) for i, s in enumerate(systems)}}


@pytest.fixture
def reports(tmp_path):
    """A complete planted A40 report and A42 report (one no-answer imbalance: A40 minus LoRA's acceptance; A42's R1
    fails, with its reason; A42's vs_a40 carries a planted reading that must not be drawn)."""
    a40 = {**head(SYSTEMS_A40), "primary": against(-0.21, "fewer, but costs acceptance"),
           "r1": r1(-0.30), "vs_lora": against(-0.23, "fewer, but costs acceptance", imbalance=True),
           "false_disclosure_vs_prompt_only": {"diff": -0.05, "interval": [-0.09, -0.01], "questions": 16}}
    minus = lambda b: {m: against(b, "")[m] for m in ("following", "acceptance", "accuracy")}  # noqa: E731
    a42 = {**head(SYSTEMS_A42), "primary": against(-0.24, "fewer, but costs acceptance"),
           "r3": {"against": ["a40", "prompt_only"], "channel": "pooled", "minus a40": minus(-0.03),
                  "minus prompt_only": minus(-0.24), "reading": "adds, costs acceptance", "no_answer_imbalance": []},
           "r1": r1(-0.33, "fails", ["no-hint accuracy within 5 points"]),
           "vs_a40": {**against(-0.777, "PLANTED no-decision reading"), "reading": "PLANTED no-decision reading"},
           "false_disclosure_vs_prompt_only": {"diff": -0.08, "interval": [-0.12, -0.04], "questions": 16}}
    paths = tmp_path / "a40_e2.json", tmp_path / "a42_e2.json"
    for p, r in zip(paths, (a40, a42)):
        p.write_text(json.dumps(r))
    return paths


def png_size(path):
    with open(path, "rb") as f:
        return struct.unpack(">II", f.read(24)[16:24])


def rows(path):
    return list(csv.DictReader(open(path)))


def num(x):
    return None if x == "" else float(x)


def draw(reports, out, *extra):
    return af.main(["--a40", str(reports[0]), "--a42", str(reports[1]), "--out", str(out), *extra])


def test_the_figure_draws_from_the_reports_into_the_folder_given(reports, tmp_path):
    paths = draw(reports, tmp_path / "fig")
    assert [p.name for p in paths] == [f"{FIGURE}.{x}" for x in ("png", "svg", "csv")]
    assert all(p.parent == tmp_path / "fig" and p.stat().st_size > 0 for p in paths)
    assert png_size(tmp_path / "fig" / f"{FIGURE}.png") == (2000, 1125)
    table = rows(tmp_path / "fig" / f"{FIGURE}.csv")
    assert table and not any(len(v) > 80 for r in table for v in r.values())          # numbers and labels only
    assert af.OUT == CODE.parent / "docs" / "paper" / "figures"                       # the defaults, not used here
    assert af.A40 == CODE / "results" / "summaries" / "trackA" / "gpu" / "a39" / "a40_e2.json"
    assert af.A42 == CODE / "results" / "summaries" / "trackA" / "gpu" / "a39" / "a42_e2.json"


def test_the_csv_has_one_row_per_plotted_difference_with_the_reports_numbers(reports, tmp_path):
    a40, a42 = (json.loads(p.read_text()) for p in reports)
    draw(reports, tmp_path)
    table = rows(tmp_path / f"{FIGURE}.csv")
    comparisons = [("a40", "primary", "prompt_only"), ("a40", "vs_lora", "lora"), ("a40", "r1", "base"),
                   ("a40_note", "primary", "prompt_only"), ("a40_note", "r3", "a40"), ("a40_note", "r3", "prompt_only"),
                   ("a40_note", "r1", "base")]
    assert [(r["system"], r["panel"], r["against"]) for r in table][::3] == comparisons
    assert [r["measure"] for r in table] == ["following", "acceptance", "accuracy"] * len(comparisons)
    r1_keys = {"following": "following_vs_base", "acceptance": "acceptance_vs_base", "accuracy": "nohint_accuracy_vs_base"}
    for r in table:
        res = a40 if r["system"] == "a40" else a42
        block = res[r["panel"]]
        e = block[f"minus {r['against']}"] if r["panel"] == "r3" else block
        got = e[r1_keys[r["measure"]] if r["panel"] == "r1" else r["measure"]]
        assert (num(r["value"]), num(r["low"]), num(r["high"])) == (got["diff"], *got["interval"])
        assert int(r["questions"]) == got["questions"]
        assert r["channel"] == ("no hint" if r["measure"] == "accuracy" else "pooled")
        own = res["systems"][r["system"]]
        other = res["systems"][r["against"]]
        pick = lambda s: s["accuracy"] if r["measure"] == "accuracy" else s[r["measure"]]["pooled"]  # noqa: E731
        assert (int(r["k"]), int(r["n"]), int(r["compared_k"]), int(r["compared_n"])) == (
            pick(own)["k"], pick(own)["n"], pick(other)["k"], pick(other)["n"])
        na = got["no_answer"]
        assert (int(r["no_answer_k"]), int(r["compared_no_answer_k"])) == (na["a"]["k"], na["b"]["k"])
        assert (r["no_answer_imbalance"] == "yes") == na["imbalance"]
    imbalanced = [r for r in table if r["no_answer_imbalance"] == "yes"]
    assert [(r["panel"], r["measure"]) for r in imbalanced] == [("vs_lora", "acceptance")]
    assert "†" in (tmp_path / f"{FIGURE}.svg").read_text()


def test_the_reading_strings_are_in_the_csv(reports, tmp_path):
    draw(reports, tmp_path)
    reading = {(r["system"], r["panel"]): r["reading"] for r in rows(tmp_path / f"{FIGURE}.csv")}
    assert reading == {("a40", "primary"): "fewer, but costs acceptance",
                       ("a40", "vs_lora"): "fewer, but costs acceptance",
                       ("a40", "r1"): "passes",
                       ("a40_note", "primary"): "fewer, but costs acceptance",
                       ("a40_note", "r3"): "adds, costs acceptance",
                       ("a40_note", "r1"): "fails (no-hint accuracy within 5 points)"}
    svg = (tmp_path / f"{FIGURE}.svg").read_text()
    assert all(x in svg for x in ("fewer, but costs acceptance", "adds, costs acceptance", "passes", "fails"))


def test_a42s_vs_a40_no_decision_is_not_drawn_as_a_reading(reports, tmp_path):
    draw(reports, tmp_path)
    table = rows(tmp_path / f"{FIGURE}.csv")
    assert "vs_a40" not in {r["panel"] for r in table}
    assert not any("PLANTED" in v for r in table for v in r.values())
    assert -0.777 not in {num(r["value"]) for r in table}
    assert "PLANTED" not in (tmp_path / f"{FIGURE}.svg").read_text()


@pytest.mark.parametrize("which, name", [(0, "A40"), (1, "A42")])
def test_an_incomplete_report_is_refused_unless_a_draft(reports, tmp_path, which, name):
    res = json.loads(reports[which].read_text())
    res["complete"] = False
    first = next(iter(res["completeness"]))
    res["completeness"][first]["missing"] = 9
    reports[which].write_text(json.dumps(res))
    with pytest.raises(SystemExit, match=f"not every {name} part is in"):
        draw(reports, tmp_path / "fig")
    assert not (tmp_path / "fig").exists()
    paths = draw(reports, tmp_path / "fig", "--draft")
    assert all(p.exists() for p in paths)
    assert "DRAFT" in (tmp_path / "fig" / f"{FIGURE}.svg").read_text()


def test_a_complete_pair_is_not_stamped(reports, tmp_path):
    draw(reports, tmp_path, "--draft")
    assert "DRAFT" not in (tmp_path / f"{FIGURE}.svg").read_text()


def test_without_a42_only_a40s_rows_are_drawn(reports, tmp_path):
    paths = af.main(["--a40", str(reports[0]), "--a42", str(tmp_path / "none.json"), "--out", str(tmp_path / "fig")])
    table = rows(paths[2])
    assert len(table) == 3 * 3 and {r["system"] for r in table} == {"a40"}
    assert [r["panel"] for r in table][::3] == ["primary", "vs_lora", "r1"]


def test_a_report_with_no_reading_is_written_not_drawn(reports, tmp_path):
    """A report with no reading (a40.py's "not run" or "partial" with none): its rows say why, and nothing is drawn."""
    res = json.loads(reports[0].read_text())
    for k in ("primary", "vs_lora", "r1"):
        del res[k]
    res.update(complete=False, label="not run: no GPU time by Nov 15")
    reports[0].write_text(json.dumps(res))
    table = rows(draw(reports, tmp_path, "--draft")[2])
    mine = [r for r in table if r["system"] == "a40"]
    assert len(mine) == 9 and all(r["value"] == r["low"] == r["high"] == "" for r in mine)
    assert {r["interval"] for r in mine} == {"missing runs"}
    assert {r["reading"] for r in mine} == {"not run: no GPU time by Nov 15"}
