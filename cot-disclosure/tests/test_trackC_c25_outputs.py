"""C25's hand-back: the figure's rows (agents/c25_figure.py) from a made-up numbers-only summary. CPU only, no network."""
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from agents import c25_figure  # noqa: E402
from common import wilson  # noqa: E402


def cell(k_var, k_ref, n=53, reading="no change", **more):
    return {"items": n, "variant_k": k_var, "variant_n": n, "answer_only_k": k_ref, "answer_only_n": n,
            "diff": (k_var - k_ref) / n, "interval": [-0.2, 0.1], "reading": reading, **more}


def summary(path):
    olmo, qwen = (m for m, _ in c25_figure.DECIDERS)
    path.write_text(json.dumps({
        "source_bad_lookups": {"hop1_solver": {"k": 5, "n": 55}, "hop2_plain": {"k": 35, "n": 55, "reading": "kept"},
                               "hop2_keep": {"k": 55, "n": 55, "reading": "kept"}},
        "deciders": {olmo: {"M1_stripped_minus_keep": cell(9, 16, reading="unclear", source_gone="unclear"),
                            "M2_plain_minus_keep": cell(13, 16)},
                     qwen: {"M1_stripped_minus_keep": cell(0, 0, source_gone="no change"),
                            "M2_plain_minus_keep": cell(1, 0)}}}))
    return path


def test_the_figure_rows_are_the_summarys_counts_with_wilson_intervals(tmp_path):
    rows = c25_figure.rows_of(summary(tmp_path / "c25_summary.json"))
    assert len(rows) == 3 + 2 * 3
    src = {r["arm"]: r for r in rows if r["panel"] == "source"}
    assert [(src[h]["k"], src[h]["n"]) for h in ("hop1_solver", "hop2_plain", "hop2_keep")] == [(5, 55), (35, 55), (55, 55)]
    assert src["hop1_solver"]["rule"] == "" and src["hop2_plain"]["rule"] == "kept"
    lo, hi = wilson(35, 55)
    assert (src["hop2_plain"]["low"], src["hop2_plain"]["high"]) == (round(lo, 6), round(hi, 6))
    olmo = c25_figure.DECIDERS[0][1]
    at = {r["arm"]: r for r in rows if r["panel"] == "decider" and r["group"] == olmo}
    assert [(at[a]["k"], at[a]["n"]) for a in ("plain", "keep", "keep_stripped")] == [(13, 53), (16, 53), (9, 53)]
    assert at["keep_stripped"]["diff"] == round((9 - 16) / 53, 6) and at["keep_stripped"]["rule"] == "unclear"
    assert at["keep_stripped"]["verdict"] == "unclear"
    assert at["plain"]["diff"] == round((13 - 16) / 53, 6) and at["plain"]["verdict"] == ""
    assert at["keep"]["diff"] == "" and at["keep"]["rule"] == ""       # the differences are written on the compared rows
