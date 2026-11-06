"""C19's hand-back: the numbers-only export (agents/trackc_summaries.py) and the figure's rows (agents/c19_figure.py).
CPU only, no network."""
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from agents import c19_figure, trackc_summaries  # noqa: E402
from common import wilson  # noqa: E402


def cell(k_var, k_ref, n=53, reading="no change"):
    return {"items": n, "variant_k": k_var, "variant_n": n, "answer_only_k": k_ref, "answer_only_n": n,
            "diff": (k_var - k_ref) / n, "interval": [-0.2, 0.1], "reading": reading}


def summary(path):
    olmo, qwen = (m for m, _ in c19_figure.REVIEWERS)
    path.write_text(json.dumps({
        "main_key_minus_own": {olmo: cell(24, 31, reading="unclear"), qwen: cell(47, 48)},
        "h34": {olmo: "unclear", qwen: "not supported"},
        "references": {"key_minus_unchanged": {olmo: cell(24, 36), qwen: cell(47, 44)}}}))
    return path


def test_the_export_copies_a_numbers_only_file_and_refuses_text(tmp_path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    src.mkdir()
    (src / "ok.json").write_text(json.dumps({"k": 24, "n": 53, "reading": "unclear"}))
    (src / "text.json").write_text(json.dumps({"reply": "x" * 500}))
    assert trackc_summaries.export("ok.json", src, dst, starts=set()) == []
    assert (dst / "ok.json").read_text() == (src / "ok.json").read_text()
    assert trackc_summaries.export("text.json", src, dst, starts=set())
    assert not (dst / "text.json").exists()


def test_the_figure_rows_are_the_summarys_counts_with_wilson_intervals(tmp_path):
    rows = c19_figure.rows_of(summary(tmp_path / "c19_summary.json"))
    assert len(rows) == 6
    at = {(r["reviewer"], r["arm"]): r for r in rows}
    olmo = c19_figure.REVIEWERS[0][1]
    assert [(at[(olmo, a)]["k"], at[(olmo, a)]["n"]) for a in ("unchanged", "my_working", "answer_key")] == \
        [(36, 53), (31, 53), (24, 53)]
    key = at[(olmo, "answer_key")]
    lo, hi = wilson(24, 53)
    assert (key["low"], key["high"]) == (round(lo, 6), round(hi, 6))
    assert key["key_minus_own"] == round((24 - 31) / 53, 6) and key["rule"] == "unclear" and key["h34"] == "unclear"
    assert at[(olmo, "my_working")]["rule"] == ""          # the difference is written once, on the answer_key row
