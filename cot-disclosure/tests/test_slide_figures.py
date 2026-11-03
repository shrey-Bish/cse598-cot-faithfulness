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
    for f in (sf.fig_bare, sf.fig_levels, sf.fig_b16, sf.fig_channels, sf.fig_qwen8b, sf.fig_b17, sf.fig_gate2):
        paths = f(out=tmp_path)
        assert [p.suffix for p in paths] == [".png", ".svg", ".csv"] and all(p.stat().st_size > 0 for p in paths)
        w, h = png_size(paths[0])
        assert abs(w / h - 16 / 9) < 0.01
        table = list(csv.DictReader(open(paths[2])))
        assert table and not any(len(v) > 80 for row in table for v in row.values())          # numbers and labels only


def test_the_waiting_spec_names_every_waiting_slide():
    text = (CODE.parent / "docs" / "paper" / "figures" / "WAITING.md").read_text()
    for name in ("readout_lora_vs_base", "c25_hops"):
        assert f"`docs/paper/figures/{name}.png`" in text
        assert not (CODE.parent / "docs" / "paper" / "figures" / f"{name}.png").exists()   # a spec, not a chart


def test_b16_rows_are_the_pre_registered_readings():
    """Slide 7 (F35, Nov 1): each tool arm minus user_authority, paired by question, with the rule's reading; and the
    following per arm, the plain user hint marked cross-day."""
    rows = sf.b16_rows()
    a = by([r for r in rows if r["panel"] == "a"], "model", "arm")
    assert len(a) == 6
    r = a[("Qwen3 30B Instruct", "its own call")]
    assert (r["k"], r["n"], r["compared_k"], r["compared_n"]) == (147, 162, 25, 162)
    assert round(r["value"] * 100) == 75 and r["reading"] == "tool beyond authority"
    assert a[("Olmo 3 7B Think", "inserted tool turn")]["reading"] == "authority moves it more"
    assert a[("Qwen3 30B Thinking", "pasted block")]["reading"] == "tool beyond authority"
    assert sum(r["reading"] == "no difference detected" for r in a.values()) == 3
    for r in a.values():
        assert r["low"] <= r["value"] <= r["high"] and r["interval"].startswith("95% bootstrap")
    b = by([r for r in rows if r["panel"] == "b"], "model", "arm")
    assert (b[("Olmo 3 7B Think", "plain user hint")]["k"], b[("Olmo 3 7B Think", "user_authority")]["k"]) == (13, 69)
    assert b[("Qwen3 30B Thinking", "plain user hint")]["measure"].endswith("(Oct 27–28)")


def test_channel_turns_come_from_the_prompt_builder():
    """The report's setup figure (channels, Nov 1): one prompt per channel, built by tools/answer_key.build, the hint
    in exactly one turn (none for the no-hint baseline), and who writes each turn."""
    from tools import answer_key as ak
    turns = sf.channel_turns()
    assert [c for c, _, _ in sf.CHANNELS] == ["none", "user", "user_authority", "system", "tool_pasted", "tool_real",
                                              "tool_injected"]
    hint = {c: [t for t in ts if t["hint"]] for c, ts in turns.items()}
    assert hint["none"] == [] and all(len(v) == 1 for c, v in hint.items() if c != "none")
    where = {c: v[0]["role"] for c, v in hint.items() if v}
    assert where == {"user": "user", "user_authority": "user", "system": "system", "tool_pasted": "user",
                     "tool_real": "tool", "tool_injected": "tool"}
    assert hint["user_authority"][0]["text"] == ak.AUTHORITY_CUE.format(letter="B")
    assert hint["system"][0]["text"] == ak.SYSTEM_HINT.format(letter="B")
    assert hint["tool_real"][0]["text"] == hint["tool_injected"][0]["text"] == ak.tool_reply("q1", "B")
    real = [t["writer"] for t in turns["tool_real"]]
    injected = [t["writer"] for t in turns["tool_injected"]]
    assert "the model" in real and "the model" not in injected      # the call: the model's own, or written in by us
    rows = sf.channel_rows()
    assert all(len(str(v)) <= 80 for r in rows for v in r.values())  # labels only, no prompt text in the CSV


def test_qwen8b_rows_are_a37s_readout():
    """Slide 4 (A37, F36, Nov 1): the drop by layer at the takeover in each half, the layers chosen on the puzzles
    marked, and the share at them on MMLU-Pro beside Olmo's at 15, 19 and 23; every number from the tracked summaries."""
    r = json.loads((SUM / "trackA" / "qwen8b_mech" / "qwen8b_readout.json").read_text())
    rows = sf.qwen8b_rows()
    b = [x for x in rows if x["panel"] == "b"]
    means = {"puzzles": r["localization"]["drop_by_layer_mean"],
             "MMLU-Pro": r["replication"]["descriptive"]["drop_by_layer_mean"]}
    for half, m in means.items():
        mine = sorted((x for x in b if x["half"] == half), key=lambda x: x["layer"])
        assert [x["layer"] for x in mine] == list(range(36))
        assert all(abs(x["value"] - v) < 1e-12 for x, v in zip(mine, m))
        assert [x["layer"] for x in mine if x["chosen"] == "yes"] == [21, 22, 29]
        assert all(x["low"] <= x["value"] <= x["high"] and x["interval"].startswith("95% bootstrap") for x in mine)
    puzzles = {x["layer"]: x for x in b if x["half"] == "puzzles"}
    for layer, e in r["localization"]["drop_at_layer"].items():               # the rule's own intervals (Sol's
        x = puzzles[int(layer)]                                                # float rounding aside)
        assert abs(x["low"] - e["low"]) < 1e-12 and abs(x["high"] - e["high"]) < 1e-12
    a = by([x for x in rows if x["panel"] == "a"], "what")
    q, share = a[("Qwen3-8B, MMLU-Pro (the test)",)], r["replication"]["share_at_layers"]
    assert (q["value"], q["low"], q["high"], q["questions"]) == (share["mean"], share["low"], share["high"], 14)
    assert q["reading"] == "replicates"
    assert [round(a[(k,)]["value"], 2) for k in ("Olmo 3 7B Think, Test 2 (F11)", "Olmo 3 7B Think, set A (F26)")] \
        == [0.90, 0.90]


def test_b17_rows_are_the_pre_registered_readings():
    """Slide 8 (B17, F37, Nov 3): per effort, following on the real call and the call rate (a) and the bare final
    answer after a call (b), each X of Y with its clustered interval; (c) the contrasts, high minus low with the rule's
    reading, the other two with no decision; every number from the tracked summary."""
    rows = sf.b17_rows()
    a = by([r for r in rows if r["panel"] == "a"], "measure", "arm")
    assert [(a[("following on the real call", e)]["k"], a[("following on the real call", e)]["n"])
            for e in ("low", "medium", "high")] == [(40, 162), (46, 162), (48, 158)]
    assert [a[("calls the tool", e)]["k"] for e in ("low", "medium", "high")] == [37, 78, 129]
    b = by([r for r in rows if r["panel"] == "b"], "arm")
    assert [(b[(e,)]["k"], b[(e,)]["n"]) for e in ("low", "medium", "high")] == [(37, 37), (75, 78), (122, 129)]
    for r in [*a.values(), *b.values()]:
        assert r["low"] <= r["value"] <= r["high"] and r["interval"] == sf.CLUSTERED
    c = by([r for r in rows if r["panel"] == "c"], "measure", "arm")
    hl = c[("following on the real call", "high - low")]
    assert round(hl["value"] * 100) == 7 and hl["reading"] == "no change detected"
    assert c[("bare final answer after a call", "high - low")]["reading"] == "no change detected"
    assert c[("bare final answer after a call", "medium - low")]["reading"] == "no decision"
    assert len(c) == 6
