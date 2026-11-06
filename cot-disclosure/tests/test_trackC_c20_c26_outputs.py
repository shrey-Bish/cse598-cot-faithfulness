"""C20 and C26's hand-back: the shared figure's rows (agents/c20_c26_figure.py) from made-up numbers-only summaries.
CPU only, no network."""
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from agents import c20_c26_figure as fig  # noqa: E402
from common import wilson  # noqa: E402

OLMO, QWEN = (m for m, _ in fig.REVIEWERS)


def cnt(k, n):
    return {"k": k, "n": n, "wilson": list(wilson(k, n))}


def pair(k_var, k_ref, n=53, reading="no change", **more):
    return {"items": n, "variant_k": k_var, "variant_n": n, "answer_only_k": k_ref, "answer_only_n": n,
            "diff": (k_var - k_ref) / n, "interval": [-0.1, 0.2], "reading": reading, **more}


def summaries(tmp):
    c20 = {"pipelines": {"d_checker": {"caught": cnt(53, 53)}}, "readings": {}}
    for m, (a, b, c) in ((OLMO, (39, 43, 26)), (QWEN, (43, 46, 46))):
        c20["pipelines"][f"a_blind | {m}"] = {"caught": cnt(a, 53)}
        c20["pipelines"][f"b_tag | {m}"] = {"caught": cnt(b, 53)}
        c20["pipelines"][f"c_disclosure | {m}"] = {"caught": cnt(c, 55)}
        c20["readings"][m] = {"1_tag_minus_blind_catches": pair(b, a),
                              "4_tag_minus_disclosure_catches": pair(b, c, reading="more catches")}
    c26 = {"reading": "Olmo: defers",
           "reviewers": {OLMO: {"R2_plus_tool_log_minus_answer_only": {**pair(12, 40), "rule": "defers"}},
                         QWEN: {"R2_plus_tool_log_minus_answer_only": {**pair(41, 44), "rule": "doesn't defer"}}}}
    c15 = {"a_replication": {OLMO: {**pair(10, 39), "rule": "defers"}, QWEN: {**pair(40, 43), "rule": "doesn't defer"}}}
    paths = []
    for name, s in (("c20", c20), ("c26", c26), ("c15", c15)):
        p = tmp / f"{name}_summary.json"
        p.write_text(json.dumps(s))
        paths.append(p)
    return paths


def test_the_figure_rows_are_the_summaries_counts_with_wilson_intervals(tmp_path):
    rows = fig.rows_of(*summaries(tmp_path))
    assert len(rows) == 2 * 3 + 1 + 2 * 4
    olmo = fig.REVIEWERS[0][1]
    c20 = {r["arm"]: r for r in rows if r["panel"] == "c20" and r["group"] == olmo}
    assert [(c20[a]["k"], c20[a]["n"]) for a in ("a_blind", "b_tag", "c_disclosure")] == [(39, 53), (43, 53), (26, 55)]
    lo, hi = wilson(43, 53)
    assert (c20["b_tag"]["low"], c20["b_tag"]["high"]) == (round(lo, 6), round(hi, 6))
    assert c20["b_tag"]["diff"] == round((43 - 39) / 53, 6) and c20["b_tag"]["rule"] == "no change"
    assert c20["b_tag"]["diff2"] == round((43 - 26) / 53, 6) and c20["b_tag"]["rule2"] == "more catches"
    assert c20["a_blind"]["diff"] == "" and c20["a_blind"]["rule"] == ""
    chk = next(r for r in rows if r["arm"] == "d_checker")
    assert (chk["k"], chk["n"], chk["group"]) == (53, 53, "checker")
    c26 = {r["arm"]: r for r in rows if r["panel"] == "c26" and r["group"] == olmo}
    assert [(c26[a]["k"], c26[a]["n"]) for a in ("c15_answer_only", "c15_plus_tool_log", "c26_answer_only",
                                                 "c26_plus_tool_log")] == [(39, 53), (10, 53), (40, 53), (12, 53)]
    assert c26["c26_plus_tool_log"]["diff"] == round((12 - 40) / 53, 6) and c26["c26_plus_tool_log"]["rule"] == "defers"
    assert c26["c26_answer_only"]["rule"] == ""


def test_the_figure_draws_from_made_up_summaries(tmp_path):
    c20, c26, c15 = summaries(tmp_path)
    paths = fig.draw(tmp_path / "figs", c20, c26, c15)
    assert [p.name for p in paths] == ["pipeline_vs_model.png", "pipeline_vs_model.svg", "pipeline_vs_model.csv"]
    assert all(p.exists() for p in paths)
