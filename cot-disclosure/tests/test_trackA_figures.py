"""Figures #1 (pinned panel) and #4 (finetune/look/plot_figures.py) count from the tracked summaries
exactly what FINDINGS F1 and F7 report."""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from finetune.look import plot_figures as pf  # noqa: E402


def test_figure1_counts_are_F1s():
    rows, base = pf.pinned_counts()
    assert [(k, n) for _, k, n in rows] == [(7, 20), (40, 60), (24, 60), (34, 60)] and base == (2, 40)


def test_figure4_counts_are_F7s():
    d = pf.deletion_counts()
    assert (d["hint"]["forced_own"], d["hint"]["forced_n"], d["control"]["forced_own"]) == (7, 19, 1)
    assert [d[a]["cont_own"] for a in ("hint", "control", "unedited")] == [5, 4, 1]
    assert [d[a]["cont_hint"] for a in ("hint", "control", "unedited")] == [44, 51, 53]
    assert [(d[a]["rementions"], d[a]["hint_ending"]) for a in ("hint", "control", "unedited")] == [(34, 44), (46, 51), (46, 53)]
