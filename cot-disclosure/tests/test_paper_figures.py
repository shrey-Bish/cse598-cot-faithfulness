"""The paper figures (tools/paper_figures.py): every plotted number comes from the tracked summaries, and
each figure writes PNG, SVG and its CSV. No calls."""
import csv
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "tools"))

import paper_figures as pf  # noqa: E402

SUM = CODE / "results" / "summaries"


def test_reviewer_rows_match_the_c4_c9_c10_summaries():
    rows = pf.reviewer_rows()
    at = {(r["reviewer"], r["variant"], r["run"]): r for r in rows}
    olmo, qwen = (name for _, name in pf.REVIEWERS)
    c4, c9, c10 = (run for _, run in pf.RUNS)
    assert (at[(olmo, "answer only", c4)]["k"], at[(olmo, "+ private reasoning", c4)]["k"],
            at[(olmo, "+ tool log", c4)]["k"]) == (59, 6, 3)                                       # F18
    assert (at[(olmo, "+ private reasoning", c9)]["k"], at[(olmo, "+ tool log", c9)]["k"]) == (8, 4)  # F19
    assert (at[(olmo, "+ private reasoning", c10)]["k"], at[(qwen, "+ tool log", c10)]["k"]) == (19, 33)  # F21
    assert (olmo, "answer only", c10) not in at                         # C10's first turn is C9's answer only
    assert {r["n"] for r in rows} == {73} and len(rows) == 2 * 3 + 2 * 3 + 2 * 2
    for log, run in pf.RUNS:                                             # against the JSON, every bar
        res = json.loads((SUM / "trackC" / f"{log}_summary.json").read_text())["by_team_model_variant"]
        for model, name in pf.REVIEWERS:
            for v, vname in pf.VARIANTS:
                key = f"tool | {model} | {v}"
                if key in res:
                    c = res[key]["bad_lookups"]["reviewer_alone"]["corrects_wrong_solver"]
                    r = at[(name, vname, run)]
                    assert (r["k"], r["n"]) == (c["k"], c["n"]) and abs(r["low"] - c["wilson"][0]) < 1e-12


def test_layer_rows_match_step10():
    rows = pf.layer_rows()
    h = json.loads((SUM / "trackA" / "step10_handoff.json").read_text())["handoff"]
    assert len(rows) == 32 and [r["layer"] for r in rows if r["kind"] == "full attention"] == h["full_attention_layers"]
    by = {r["layer"]: r["share"] for r in rows}
    assert (round(by[15], 2), round(by[19], 2), round(by[23], 2)) == (0.34, 0.17, 0.39)       # F11
    assert abs(by[15] + by[19] + by[23] - h["by_cut_type"]["ii"]["all"]["drop_share_readout"]["mean"]) < 0.02
    assert rows[0]["cuts"] == 19 and rows[0]["questions"] == 9


def test_loss_rows_match_val_loss_report():
    rows = pf.loss_rows()
    at = {(r["version"], r["group"]): r for r in rows}
    assert round(at[("LoRA", "taught tokens")]["relative"] * 100) == -58                       # F20
    assert round(at[("LoRA", "taught, without the opener")]["relative"] * 100) == -40
    assert round(at[("tags", "taught, without the opener")]["relative"] * 100) == -9
    assert round(at[("LoRA, layers 15/19/23", "taught tokens")]["relative"] * 100) == -52
    for r in rows:
        assert r["low"] <= r["relative"] <= r["high"] and r["items"] == 34


def test_each_figure_writes_png_svg_and_its_table(tmp_path):
    for f in (pf.fig_reviewer, pf.fig_layers, pf.fig_loss):
        paths = f(out=tmp_path)
        assert [p.suffix for p in paths] == [".png", ".svg", ".csv"] and all(p.stat().st_size > 0 for p in paths)
        table = list(csv.DictReader(open(paths[2])))
        assert table and not any(len(v) > 80 for row in table for v in row.values())          # numbers and labels only
