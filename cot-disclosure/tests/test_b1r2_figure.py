"""B1R2's figure beside B1's (tools/b1r2_figure.py): the deployable span minus alpha = 1 on following, correct-hint
acceptance and no-hint accuracy, B1 on the 30 and B1R2 on E2 side by side, drawn from two reports in
finetune/gpu/provenance_job.report's format. Synthetic reports into a temporary folder: never into docs/paper/figures/.
Every plotted number in the CSV is b1_verdict's (B1's rule, unchanged); a B1R2 report short of its 600 runs a system is
refused (the A39 log's section 13.8 reads a partial B1R2 on its complete questions only). CPU only, no network."""
import csv
import struct
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))
sys.path.insert(0, str(CODE / "tools"))

pytest.importorskip("matplotlib")

from finetune.gpu import provenance_job as pj  # noqa: E402

import b1r2_figure as bf  # noqa: E402

KEYS = {"following": "wrong_hint_following | tool_injected", "acceptance": "correct_hint_acceptance | tool_injected",
        "accuracy": "no_hint_accuracy | all"}


def cell(k, n, q, diff=None, lo=None, hi=None):
    c = {"k": k, "n": n, "text": f"{k} of {n}", "wilson": [0.1, 0.9], "questions": q}
    if diff is not None:
        c["minus_alpha1"] = {"diff": diff, "interval": [lo, hi], "questions": q}
    return c


def report(q, runs, alpha1, dep):
    """A report in provenance_job.report's shape: alpha1 and dep map each measure to (k, n) and dep's also to
    (diff, low, high)."""
    def system(alpha, cells, minus):
        e = {"span": "deployable", "alpha": alpha, "runs": runs, "no_answer": 1}
        for m, key in KEYS.items():
            e[key] = cell(*cells[m][:2], q, *(cells[m][2:] if minus else ()))
        return e
    return {"engine": "v2", "base": "prov-a1-v2",
            "systems": {"prov-a1-v2": system(1.0, alpha1, False),
                        "prov-deployable-a0.25-v2": system(0.25, dep, True)},
            "bootstrap": "paired by question (clustered), 20,000 resamples, seed 0", "set_aside": {}}


B1 = report(30, 210, {"following": (26, 60), "acceptance": (25, 30), "accuracy": (16, 30)},
            {"following": (16, 60, -1 / 6, -0.30, -1 / 30), "acceptance": (23, 30, -1 / 15, -0.20, 1 / 15),
             "accuracy": (19, 30, 0.10, 0.0, 7 / 30)})
B1R2 = report(120, 600, {"following": (82, 240), "acceptance": (211, 240), "accuracy": (78, 120)},
              {"following": (49, 240, -0.1375, -0.20, -0.075), "acceptance": (197, 240, -0.0583, -0.108, -0.0125),
               "accuracy": (79, 120, 0.0083, -0.067, 0.083)})


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def test_the_rows_are_b1_verdict_s_numbers_for_each_study():
    rows = bf.rows(B1, B1R2)
    assert [(r["study"], r["measure"]) for r in rows] == [(s, m) for s in ("B1", "B1R2") for m in bf.MEASURES]
    for study, res in (("B1", B1), ("B1R2", B1R2)):
        v = pj.b1_verdict(res, "deployable", "tool_injected")
        dep, base = res["systems"][v["system"]], res["systems"][res["base"]]
        for m, d in (("following", v["following"]), ("acceptance", v["acceptance"]), ("accuracy", v["accuracy"])):
            r = next(x for x in rows if x["study"] == study and x["measure"] == m)
            assert (r["value"], r["low"], r["high"]) == (d["diff"], *d["interval"])
            assert (r["k"], r["n"]) == (dep[KEYS[m]]["k"], dep[KEYS[m]]["n"])
            assert (r["compared_k"], r["compared_n"]) == (base[KEYS[m]]["k"], base[KEYS[m]]["n"])
            assert r["questions"] == d["questions"] and r["reading"] == v["reading"] == "ignores tools"
            assert r["limit"] == ("" if m == "following" else pj.MARGIN)       # the 5-point limits, acceptance and accuracy
            assert r["alpha"] == 0.25 and r["channel"] == ("no hint" if m == "accuracy" else "inserted tool turn")


def test_the_headline_gives_each_study_s_reading_in_the_rule_s_words():
    head, sub = bf.words(bf.rows(B1, B1R2))
    assert head.count('"ignores tools"') == 2
    assert "the held-out 30 (primary)" in head and "E2" in head and "a labelled replication" in head
    assert "−16.7 [−30.0, −3.3]" in sub and "−13.8 [−20.0, −7.5]" in sub     # following on each, in points
    assert "−6.7" in sub and "−5.8" in sub and "5-point limit" in sub         # acceptance against the limit, points


def test_another_reading_changes_the_words():
    worse = report(120, 600, {"following": (82, 240), "acceptance": (211, 240), "accuracy": (78, 120)},
                   {"following": (90, 240, 0.03, -0.02, 0.08), "acceptance": (210, 240, -0.004, -0.03, 0.02),
                    "accuracy": (78, 120, 0.0, -0.05, 0.05)})
    head, _ = bf.words(bf.rows(B1, worse))
    assert '"ignores tools"' in head and '"no effect"' in head


def test_the_figure_draws_png_svg_and_csv_into_the_folder_given(tmp_path):
    a, b = tmp_path / "b1.json", tmp_path / "b1r2.json"
    import json
    a.write_text(json.dumps(B1))
    b.write_text(json.dumps(B1R2))
    paths = bf.main(["--b1", str(a), "--b1r2", str(b), "--out", str(tmp_path / "fig")])
    assert [p.name for p in paths] == [f"b1r2_vs_b1.{x}" for x in ("png", "svg", "csv")]
    assert all(p.parent == tmp_path / "fig" and p.stat().st_size > 0 for p in paths)
    assert png_size(tmp_path / "fig" / "b1r2_vs_b1.png") == (2000, 1125)
    table = list(csv.DictReader(open(tmp_path / "fig" / "b1r2_vs_b1.csv")))
    want = bf.rows(B1, B1R2)
    assert len(table) == len(want) == 6
    for got, w in zip(table, want):
        assert float(got["value"]) == pytest.approx(w["value"]) and float(got["low"]) == pytest.approx(w["low"])
        assert float(got["high"]) == pytest.approx(w["high"]) and int(got["k"]) == w["k"] and got["reading"] == w["reading"]
    assert not any(len(v) > 80 for r in table for v in r.values())                     # numbers and labels only


def test_an_incomplete_b1r2_is_refused(tmp_path):
    import json
    short = report(120, 599, {"following": (82, 240), "acceptance": (211, 240), "accuracy": (78, 120)},
                   {"following": (49, 239, -0.1375, -0.20, -0.075), "acceptance": (197, 240, -0.0583, -0.108, -0.0125),
                    "accuracy": (79, 120, 0.0083, -0.067, 0.083)})
    a, b = tmp_path / "b1.json", tmp_path / "b1r2.json"
    a.write_text(json.dumps(B1))
    b.write_text(json.dumps(short))
    with pytest.raises(SystemExit, match="600"):
        bf.main(["--b1", str(a), "--b1r2", str(b), "--out", str(tmp_path / "fig")])
    assert not (tmp_path / "fig").exists()


def test_the_defaults_are_the_tracked_reports_and_the_paper_s_figures():
    sums = CODE / "results" / "summaries" / "trackA" / "gpu"
    assert bf.B1_REPORT == sums / "provenance_gen" / "provenance_gen_report.json"
    assert bf.B1R2_REPORT == sums / "b1r2" / "provenance_gen_report.json"
    assert bf.OUT == CODE.parent / "docs" / "paper" / "figures"


def test_the_export_keeps_b1r2_s_report():
    import export_summaries as es
    assert es.KEEP_PATH["gpu/b1r2/provenance_gen_report.json"] == "trackA/gpu/b1r2/provenance_gen_report.json"
