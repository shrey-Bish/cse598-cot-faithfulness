"""The final deck's figures: every plotted and every drawn number is in docs/presentation/pack/02_NUMBERS.md."""
import re
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
REPO = CODE.parent
sys.path.insert(0, str(CODE / "tools" / "deck"))
import figures  # noqa: E402

NUMBERS = (REPO / "docs" / "presentation" / "pack" / "02_NUMBERS.md").read_text().replace("−", "-")
FIGDIR = REPO / "docs" / "presentation" / "final" / "figures"
NAMES = ["fig_across_models", "fig_tool_vs_user_full", "fig_reasoning_vs_answer", "fig_tradeoff", "fig_checker"]


def table():
    rows = {}
    for line in NUMBERS.splitlines():
        if line.startswith("| N"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows[cells[0]] = cells
    return rows


ROWS = table()
PLOTTED = figures.plotted()
LABELS = figures.labels()


def test_table_parsed():
    assert len(ROWS) >= 149 and "N149" in ROWS


@pytest.mark.parametrize("r", PLOTTED, ids=lambda r: f"{r['figure']}:{r['label'][:40]}")
def test_plotted_in_02(r):
    if r["row"] is None:
        # the trade-off's two left-end points: drawn, never labelled, not a 02 row
        assert r["figure"] == "tradeoff" and "unlabelled" in r["label"]
        return
    cells = ROWS[r["row"]]
    text = " ".join(cells[1:4])
    if r["k"] is not None:
        assert f"{r['k']} of {r['n']}" in text, (r["label"], r["row"])
    if r["low"] is not None and r["k"] is not None:
        assert figures.ivs(r["low"], r["high"]) in text, (r["label"], figures.ivs(r["low"], r["high"]), r["row"])
    if r["k"] is None:  # the crossover
        assert f"{r['value']:.2f} [{r['low']:.2f}, {r['high']:.2f}]" in text


def test_drawn_numbers_in_02():
    assert LABELS
    for L in LABELS:
        for tok in L["tokens"]:
            assert tok in NUMBERS, (L["figure"], tok)
        for num in re.findall(r"\d+(?:\.\d+)?", L["text"]):
            assert re.search(rf"(?<![\d.]){re.escape(num)}(?![\d.])", NUMBERS), (L["figure"], L["text"], num)


def test_every_labelled_row_is_a_token():
    # each across-models row uses exactly 02 rows N140-N146
    ids = {r["row"] for r in PLOTTED if r["figure"] == "across_models"}
    assert ids == {f"N{i}" for i in range(140, 147)}


def test_tradeoff_labels_leave_out_the_left_ends():
    txt = " ".join(L["text"] for L in LABELS if L["figure"] == "tradeoff")
    assert "285" not in txt and "251" not in txt
    assert "347 of 459" in txt and "431 of 476" in txt and "36%" in txt


def test_files_exist_and_are_fresh():
    src = (CODE / "tools" / "deck" / "figures.py").stat().st_mtime
    for n in NAMES:
        for ext in ("png", "svg"):
            f = FIGDIR / f"{n}.{ext}"
            assert f.exists(), f
            assert f.stat().st_mtime >= src, f"{f} older than figures.py: rerun tools/deck/figures.py"
