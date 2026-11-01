"""The slide figures (tools/slide_figures.py): every plotted number comes from the tracked summaries, each figure
writes PNG, SVG and its CSV at 16:9, and a slide still waiting on a result has a spec, not a chart. No calls."""
import csv
import json
import struct
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "tools"))

import slide_figures as sf  # noqa: E402

SUM = CODE / "results" / "summaries"


def by(rows, *keys):
    return {tuple(r[k] for k in keys): r for r in rows}


def test_bare_rows_match_track_b_and_c4():
    rows = sf.bare_rows()
    a = by([r for r in rows if r["panel"] == "a"], "model", "arm")
    after, pasted = sf.ARMS_B
    assert (a[("Qwen3 30B Thinking", after)]["k"], a[("Qwen3 30B Thinking", after)]["n"]) == (51, 54)       # F15
    assert (a[("Qwen3 30B Instruct", after)]["k"], a[("Qwen3 30B Instruct", after)]["n"]) == (111, 162)     # F25
    assert (a[("Qwen3-8B, thinking on", after)]["k"], a[("Qwen3-8B, thinking on", after)]["n"]) == (138, 145)  # F29
    assert (a[("Qwen3 30B Thinking", pasted)]["k"], a[("Qwen3-8B, thinking on", pasted)]["k"]) == (0, 40)
    rep = json.loads((SUM / "trackB" / "trackB_report.json").read_text())["budget_32768"]
    for key, name in sf.MODELS_B:                                     # every bar against the JSON, clustered
        e = rep[key]["channels"]["tool_real"]["bare_final_when_called"]
        r = a[(name, after)]
        assert (r["low"], r["high"]) == tuple(e["clustered"]) and r["interval"].startswith("95% bootstrap")
    b = {r["arm"]: r for r in rows if r["panel"] == "b"}
    assert [(b[x]["k"], b[x]["n"]) for x in sf.ARMS_C4_LABELS] == [(80, 84), (71, 75), (2, 159)]          # F15, C4
    assert all(r["interval"] == "95% Wilson" for r in b.values())


def test_instruction_rows_match_b15():
    rows = [r for r in sf.bare_rows() if r["panel"] == "c"]
    at = by(rows, "model", "measure")
    names, follows = sf.MEASURES_B15[0][1], sf.MEASURES_B15[1][1]
    t, i = "Qwen3 30B Thinking", "Qwen3 30B Instruct"
    assert round(at[(t, names)]["value"] * 100) == 47 and at[(t, names)]["reading"] == "rises"              # F25
    assert round(at[(i, names)]["value"] * 100) == 70
    assert (at[(t, names)]["compared_k"], at[(t, names)]["compared_n"], at[(t, names)]["k"], at[(t, names)]["n"]) \
        == (3, 54, 33, 63)
    assert at[(t, follows)]["reading"] == at[(i, follows)]["reading"] == "no change detected"
    for r in rows:
        assert r["low"] <= r["value"] <= r["high"]


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def test_each_figure_writes_png_svg_and_its_table_at_16_9(tmp_path):
    for f in (sf.fig_bare, sf.fig_levels):
        paths = f(out=tmp_path)
        assert [p.suffix for p in paths] == [".png", ".svg", ".csv"] and all(p.stat().st_size > 0 for p in paths)
        w, h = png_size(paths[0])
        assert abs(w / h - 16 / 9) < 0.01
        table = list(csv.DictReader(open(paths[2])))
        assert table and not any(len(v) > 80 for row in table for v in row.values())          # numbers and labels only


def test_the_waiting_spec_names_every_waiting_slide():
    text = (CODE.parent / "docs" / "paper" / "figures" / "WAITING.md").read_text()
    for name in ("readout_qwen8b", "b16_authority", "b17_effort", "readout_lora_vs_base", "c25_hops"):
        assert f"`docs/paper/figures/{name}.png`" in text
        assert not (CODE.parent / "docs" / "paper" / "figures" / f"{name}.png").exists()   # a spec, not a chart
