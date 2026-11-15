"""The slide figures (tools/slide_figures.py): every plotted number comes from the tracked summaries, each figure
writes PNG, SVG and its CSV at 16:9, and a slide still waiting on a result has a spec, not a chart. No calls."""
import csv
import json
import re
import struct
import sys
from pathlib import Path

import pytest

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
    for f in (sf.fig_bare, sf.fig_levels, sf.fig_b16, sf.fig_channels, sf.fig_qwen8b, sf.fig_b17, sf.fig_gate2, sf.fig_a18):
        paths = f(out=tmp_path)
        assert [p.suffix for p in paths] == [".png", ".svg", ".csv"] and all(p.stat().st_size > 0 for p in paths)
        w, h = png_size(paths[0])
        assert abs(w / h - 16 / 9) < 0.01
        table = list(csv.DictReader(open(paths[2])))
        assert table and not any(len(v) > 80 for row in table for v in row.values())          # numbers and labels only


def test_the_waiting_spec_names_every_waiting_slide():
    """Slide 12's c25_hops was a spec until Shrey drew it (Nov 6, docs/trackC/figures/); Nov 7 it was placed in
    docs/paper/figures/ with his other two (CHECKIN section 8). WAITING still names each, and each placed copy is there
    with its CSV."""
    figures = CODE.parent / "docs" / "paper" / "figures"
    text = (figures / "WAITING.md").read_text()
    assert "`docs/paper/figures/c25_hops.png`" in text
    for name in ("c25_hops", "c19_authority", "pipeline_vs_model"):
        assert name in text
        assert (figures / f"{name}.png").exists() and (figures / f"{name}.csv").exists()


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


def test_a18_rows_are_the_pre_registered_readings():
    """Slide 10 (A18, F39, Nov 3): (a) on base's tool-hint cases, R = TE_base - TE_X for LoRA (the primary, "acts in
    the reasoning") and the four layer swaps (reported, not read: the rule's shares are undefined when R_lora < 0),
    each with its 95% bootstrap clustered by question; (b) B1's spans minus alpha = 1 with F38's readings."""
    rows = sf.a18_rows()
    a = by([r for r in rows if r["panel"] == "a"], "arm")
    lora = a[("LoRA, every layer",)]
    readout = json.loads((SUM / "trackA" / "gpu" / "a18" / "a18_readout.json").read_text())["primary"]
    assert (lora["value"], lora["low"], lora["high"]) == pytest.approx(
        (readout["reduction_lora"]["mean"], readout["reduction_lora"]["low"], readout["reduction_lora"]["high"]))
    assert round(lora["value"], 2) == -0.72 and lora["high"] < 0 and lora["reading"].startswith("acts in the reasoning")
    assert lora["n"] == 28 and "13 questions" in lora["interval"]
    swaps = [a[(s,)] for s in ("base + LoRA's 0-14", "base + LoRA's 15, 19, 23", "base + LoRA's 0-23",
                               "base + LoRA's 24-31")]
    assert [round(r["value"], 2) for r in swaps] == [0.07, -0.01, 0.01, -0.9]
    assert all(r["reading"] == "reported, not read" and r["low"] <= r["value"] <= r["high"] for r in swaps)
    b = by([r for r in rows if r["panel"] == "b"], "arm")
    dep, ora = b[("deployable (0.25), inserted turn",)], b[("oracle (0.5), every hint channel",)]
    assert (dep["k"], dep["n"], dep["compared_k"], dep["compared_n"]) == (16, 60, 26, 60) and dep["reading"] == "ignores tools"
    assert round(dep["value"] * 100) == -17 and round(ora["value"] * 100) == -9 and ora["reading"] == "no effect"


def test_a41_puts_a40s_bars_beside_loras_and_without_it_the_rows_are_as_before(tmp_path):
    """Slide 10 with A41 (the A41 log's section 6: "slide 10 beside LoRA's bars"): A40's R and its four swaps on the same
    tool-hint cases, computed as LoRA's are, match a41_readout.json (the primary's reduction_a40; the layer R, reported
    with no decision), with the primary's reading and where; A40 minus LoRA per case and its reading come from the
    readout. Without a41_readout.json the rows, and the figure's CSV, are A18's and B1's alone."""
    a41 = json.loads((SUM / "trackA" / "gpu" / "a18" / "a41_readout.json").read_text())
    p, layer, vs = a41["primary"], a41["layer R (reported, no decision)"], a41["against LoRA"]
    rows = sf.a18_rows()
    mine = by([r for r in rows if "A40" in r["arm"]], "arm")
    a40 = mine[("A40, every layer",)]
    assert (a40["value"], a40["low"], a40["high"]) == pytest.approx(
        (p["reduction_a40"]["mean"], p["reduction_a40"]["low"], p["reduction_a40"]["high"]))
    assert a40["n"] == p["usable"] == 28 and f"{p['questions']} questions" in a40["interval"]
    assert a40["reading"] == "stops the readout, before them"
    for name, arm in (("before", "base + A40's 0-14"), ("readout", "base + A40's 15, 19, 23"),
                      ("through", "base + A40's 0-23"), ("after", "base + A40's 24-31")):
        r = mine[(arm,)]
        assert (r["value"], r["low"], r["high"]) == pytest.approx((layer[name]["mean"], layer[name]["low"],
                                                                   layer[name]["high"]))
        assert r["reading"] == "reported, no decision"
    d = mine[("A40 minus LoRA, per case",)]
    assert (d["value"], d["low"], d["high"]) == (vs["difference"]["mean"], vs["difference"]["low"],
                                                 vs["difference"]["high"])
    assert d["reading"] == "A40 removes more of the hint's pull than LoRA" and d["n"] == vs["usable"]
    assert len(mine) == 6 and all(r["panel"] == "a" for r in mine.values())
    without = sf.a18_rows(a41=tmp_path / "none.json")
    assert without == [r for r in rows if "A40" not in r["arm"]]
    assert [r["arm"] for r in without] == [arm for _, arm in sf.SWAPS_A18] + [arm for _, _, arm in sf.B1_SPANS]
    table = list(csv.DictReader(open(sf.fig_a18(out=tmp_path / "with")[2])))
    got = {r["arm"]: r for r in table if "A40" in r["arm"]}
    assert set(got) == {r["arm"] for r in mine.values()}
    for arm, r in got.items():
        x = mine[(arm,)]
        assert (float(r["value"]), float(r["low"]), float(r["high"])) == pytest.approx((x["value"], x["low"], x["high"]))
        assert r["reading"] == x["reading"]
    before = list(csv.DictReader(open(sf.fig_a18(out=tmp_path / "without", a41=tmp_path / "none.json")[2])))
    assert before == [r for r in table if "A40" not in r["arm"]] and len(before) == 7



# ---------------------------------------------------------------- one style for every finished slide (Nov 4)
SLIDE_NAMES = {"three_levels", "gate2", "readout_by_layer_slide", "readout_qwen8b", "bare_after_call", "b16_authority",
               "b17_effort", "gate3_vs_base_slide", "readout_lora_vs_base", "reviewer_by_prompt_slide",
               "trackC_reviewers_slide", "cue_experiments_slide", "channels", "private_vs_final"}


def test_every_slide_figure_is_2000_by_1125_with_its_csv(tmp_path):
    """Every figure a finished slide uses (and the report's channels) comes out of slide_figures at 2000 x 1125 pixels,
    with its SVG and a CSV of every plotted number; main() makes each one."""
    made = {}
    for f in sf.SLIDE_FIGURES:
        paths = f(out=tmp_path)
        assert [p.suffix for p in paths] == [".png", ".svg", ".csv"] and all(p.stat().st_size > 0 for p in paths)
        assert png_size(paths[0]) == (2000, 1125), paths[0].name
        table = list(csv.DictReader(open(paths[2])))
        assert table and not any(len(str(v)) > 80 for row in table for v in row.values())
        made[paths[0].stem] = f
    assert set(made) == SLIDE_NAMES


def drawn(monkeypatch, f, tmp_path):
    """The figure f draws, caught as it is saved."""
    figs = []
    real = sf.save

    def keep(fig, name, rows, out):
        figs.append(fig)
        return real(fig, name, rows, out)
    monkeypatch.setattr(sf, "save", keep)
    f(out=tmp_path)
    return figs[0]


def test_one_style_text_in_ink_headline_key_and_note_in_place(monkeypatch, tmp_path):
    """Ritik's brief: text in ink, never a series color; the headline at the same place and size in every figure;
    a key (when there is one) is the figure's, one place under the headline, never inside a panel; the note at the
    foot; panel titles left, one size."""
    from matplotlib.colors import to_hex
    from matplotlib.text import Text
    ink = {to_hex(sf.INK), to_hex(sf.MUTED)}
    for f in sf.SLIDE_FIGURES:
        fig = drawn(monkeypatch, f, tmp_path)
        texts = [t for t in fig.findobj(Text) if t.get_text().strip() and t.get_visible()]
        bad = {(t.get_text()[:30], to_hex(t.get_color())) for t in texts if to_hex(t.get_color()) not in ink}
        assert not bad, (f.__name__, bad)
        head = [t for t in fig.texts if t.get_position() == (sf.LEFT, sf.HEAD[0])]
        assert len(head) == 1 and head[0].get_fontsize() == sf.HEAD_SIZE, f.__name__
        assert all(ax.get_legend() is None for ax in fig.axes), f.__name__
        for lg in fig.legends:
            box = lg.get_bbox_to_anchor().transformed(fig.transFigure.inverted())
            assert (round(box.x0, 3), round(box.y1, 3)) == (sf.LEFT, sf.KEY_TOP), f.__name__
        notes = [t for t in fig.texts if t.get_position() == (sf.LEFT, sf.NOTE_Y)]
        assert len(notes) <= 1 and all(t.get_fontsize() == sf.NOTE_SIZE for t in notes), f.__name__
        for ax in fig.axes:
            t = ax.title if ax.title.get_text() else ax._left_title
            if t.get_text():
                assert t is ax._left_title and t.get_fontsize() == sf.TITLE_SIZE, (f.__name__, t.get_text())


def csv_rows(path):
    return [r for r in csv.reader(open(path)) if r and not r[0].startswith("# ")]


def test_slide_versions_keep_their_sources_numbers(tmp_path):
    """The slide versions of figures made elsewhere plot the same rows: the report's readout_by_layer and
    reviewer_by_prompt (tools/paper_figures.py), the supplement's readout_setA_vs_test2, trackC_reviewers and
    cue_experiments (tools/make_supplement.py, imported read-only) and Gate 3's gate3_vs_base (finetune/gate3.py)."""
    import paper_figures as pf
    import make_supplement as ms
    from finetune import gate3
    src, mine = tmp_path / "src", tmp_path / "mine"
    rows = sf.layers_slide_rows()
    a = [{k: r[k] for k in ("layer", "kind", "share", "low", "high", "questions", "cuts")} for r in rows if r["panel"] == "a"]
    assert a == pf.layer_rows()
    setA = csv_rows(ms.fig_readout(src, SUM)[2])
    b = [[str(r[k]) for k in setA[0]] for r in rows if r["panel"] == "b"]
    assert [setA[0]] + b == setA
    assert csv_rows(sf.fig_reviewer_slide(out=mine)[2]) == csv_rows(pf.fig_reviewer(out=src)[2])
    assert csv_rows(sf.fig_reviewers_slide(out=mine)[2]) == csv_rows(ms.fig_reviewers(src, ms.reviewer_rows(SUM))[2])
    assert csv_rows(sf.fig_cues_slide(out=mine)[2]) == csv_rows(ms.fig_cues(src, ms.cue_rows(SUM)[0])[2])
    tracked = SUM / "trackA" / "gpu" / "eval" / "figures" / "gate3_vs_base.csv"
    assert csv_rows(sf.fig_gate3_slide(out=mine)[2]) == csv_rows(tracked)
    rep = json.loads((SUM / "trackA" / "gpu" / "eval" / "eval_report.json").read_text())
    assert sf.gate3_slide_rows() == gate3.vs_base_rows(rep)


# ---------------------------------------------------------------- slide 5 (F3, Nov 13)
SUMMARY = CODE.parent / "docs" / "labeling" / "RESULTS_SUMMARY.json"
MODELS_TEST2 = ("olmo3-7b-think", "qwen3-30b-a3b-thinking-2507")


def test_private_final_rows_are_f3s_keyword_counts():
    """Slide 5 (F3): in Test 1's hinted runs, per thinking model, the private reasoning and the final answer naming the
    user's hint (detect.py's keyword), and the private keyword with no hint; the totals, the overlap and Test 2's runs
    where the tool hint won. Every k and n is RESULTS_SUMMARY.json's; the per-model counts sum to F3's totals; the
    intervals are progress/common.py's Wilson and round to F3's."""
    from common import wilson
    s = json.loads(SUMMARY.read_text())
    men = s["pilot"]["mentions"]
    rows = sf.private_final_rows()
    a = by([r for r in rows if r["panel"] == "a" and r["shown"] == "bar"], "model", "text", "runs")
    for key, name in sf.MODELS_F3:
        for field, text, runs, _ in sf.TEXTS_F3:
            r, e = a[(name, text, runs)], men[key][field]
            assert (r["k"], r["n"]) == (e["num"], e["den"]) and r["source"] == f"pilot.mentions.{key}.{field}"
    models = [name for _, name in sf.MODELS_F3]
    assert [a[(m, "private reasoning", "hinted")]["k"] for m in models] == [66, 71, 71]
    assert [a[(m, "final answer", "hinted")]["k"] for m in models] == [0, 0, 8]
    assert all(a[(m, t, "hinted")]["n"] == 72 for m in models for t in ("private reasoning", "final answer"))
    for key, _ in sf.MODELS_F3:                       # the final total sums the runs with private reasoning: the same
        assert men[key]["final_mentions_hinted"] == {**men[key]["final_mentions_hinted_with_trace"],
                                                     "function": men[key]["final_mentions_hinted"]["function"]}
    seven = a[("Olmo 3 7B Think", "private reasoning", "no hint")]
    assert (seven["k"], seven["n"]) == (22, 72)                                     # F3's caveat: an upper bound
    total = {t: a[(sf.ALL_F3, t, "hinted")] for t in ("private reasoning", "final answer")}
    assert [(r["k"], r["n"]) for r in total.values()] == [(208, 216), (8, 216)]     # F3, Test 1
    for t, field in (("private reasoning", "private_mentions_all_thinking"),
                     ("final answer", "final_mentions_all_thinking")):
        assert (total[t]["k"], total[t]["n"]) == (s["pilot"][field]["num"], s["pilot"][field]["den"])
        assert total[t]["source"] == f"pilot.{field}"
        assert sum(a[(m, t, "hinted")]["k"] for m in models) == total[t]["k"]
        assert sum(a[(m, t, "hinted")]["n"] for m in models) == total[t]["n"]
    assert (sf.ALL_F3, "private reasoning", "no hint") not in a                   # no total the summary doesn't give
    over = by([r for r in rows if r["measure"] == "overlap"], "text")
    assert [(over[(t,)]["k"], over[(t,)]["n"]) for t in ("both", "private only", "final only", "neither")] == \
        [(8, 216), (200, 216), (0, 216), (8, 216)]                                   # F3: both 8; 200; 0; 8
    assert over[("both",)]["k"] + over[("private only",)]["k"] == total["private reasoning"]["k"]
    assert over[("both",)]["k"] + over[("final only",)]["k"] == total["final answer"]["k"]
    b = by([r for r in rows if r["panel"] == "b"], "text", "measure")
    t2 = s["scope_numbers"]["test2_thinking_combined"]
    assert t2["models"] == list(MODELS_TEST2)
    for text, field in (("private reasoning", "followed_and_private_mention"),
                        ("final answer", "followed_and_final_mention")):
        r = b[(text, "names the tool")]
        cells = [s["expB"]["cells"][f"{m}|cue_tool|all"][field] for m in MODELS_TEST2]
        assert (r["k"], r["n"]) == (sum(c["num"] for c in cells), sum(c["den"] for c in cells))
    assert [(b[(t, "names the tool")]["k"], b[(t, "names the tool")]["n"]) for t in ("private reasoning", "final answer")] \
        == [(16, 17), (6, 17)]                                                        # F3, Test 2
    won = b[("", "the tool hint won")]
    assert (won["k"], won["n"]) == (t2["tool_hint_followed"]["num"], t2["tool_hint_followed"]["den"]) == (17, 31)
    for r in rows:
        assert r["value"] == r["k"] / r["n"] and r["interval"] == sf.WILSON
        assert (r["low"], r["high"]) == tuple(wilson(r["k"], r["n"]))
    rounded = [[round(x * 100) for x in (r["low"], r["high"])] for r in
               (total["private reasoning"], total["final answer"], b[("private reasoning", "names the tool")],
                b[("final answer", "names the tool")])]
    assert rounded == [[93, 98], [2, 7], [73, 99], [17, 59]]                          # F3's intervals


def strings(o, key=""):
    if isinstance(o, dict):
        return [x for k, v in o.items() for x in strings(v, k)]
    if isinstance(o, list):
        return [x for v in o for x in strings(v, key)]
    return [(key, o)] if isinstance(o, str) else []


def test_f3s_source_holds_numbers_not_model_text():
    """The parts of RESULTS_SUMMARY.json the figure reads hold numbers, ids, paths and our own short notes: no reply
    text (the model ids, the source paths, the function names, the notes and the run ids are every string there)."""
    s = json.loads(SUMMARY.read_text())
    parts = [s["pilot"]["mentions"], s["pilot"]["private_mentions_all_thinking"], s["pilot"]["final_mentions_all_thinking"],
             s["scope_numbers"]["pilot_mention_overlap"], s["scope_numbers"]["test2_thinking_combined"],
             [s["expB"]["cells"][f"{m}|cue_tool|all"] for m in MODELS_TEST2]]
    found = strings(parts)
    ids = {"models", "model", "channel", "group", "ci_method"}
    assert found and {k for k, _ in found} <= ids | {"source", "function", "note", "run_ids"}
    assert all(len(v) <= 120 and "\n" not in v for _, v in found)
    assert all(re.fullmatch(r"[a-z0-9_.\-]+", v) for k, v in found if k in ids)
    assert all(re.fullmatch(r"cot-disclosure/[A-Za-z0-9_/.\-]+\.jsonl", v) for k, v in found if k == "source")
    assert all(len(v) == 16 and int(v, 16) >= 0 for k, v in found if k == "run_ids")


def test_private_final_figure_plots_only_its_csv(monkeypatch, tmp_path):
    """The figure's bars are the CSV's "bar" rows, every "X of Y" it prints is a CSV row, the CSV is the rows (numbers
    and short labels only), and the note says what the counts are and why no claim rests on L3's labels."""
    fig = drawn(monkeypatch, sf.fig_private_final, tmp_path)
    rows = sf.private_final_rows()
    table = list(csv.DictReader(open(tmp_path / "private_vs_final.csv")))
    assert table == [{k: str(v) for k, v in r.items()} for r in rows]
    assert png_size(tmp_path / "private_vs_final.png") == (2000, 1125)
    assert (tmp_path / "private_vs_final.svg").stat().st_size > 0
    numeric = ("k", "n", "value", "low", "high")
    for r in table:
        for k, v in r.items():
            if k in numeric:
                float(v)
            else:
                assert len(v) <= 80 and "\n" not in v, (k, v)
        assert re.fullmatch(r"[a-z0-9_.\-]+", r["source"]), r["source"]
    heights = sorted(b.get_height() for ax in fig.axes for c in ax.containers for b in c)
    assert heights == pytest.approx(sorted(r["value"] * 100 for r in rows if r["shown"] == "bar"))
    words = " ".join(t.get_text() for t in fig.findobj(lambda o: hasattr(o, "get_text"))).replace("\n", " ")
    printed = {(int(k), int(n)) for k, n in re.findall(r"(\d+) of (\d+)", words)}
    assert printed and printed <= {(r["k"], r["n"]) for r in rows}
    assert {(r["k"], r["n"]) for r in rows if r["shown"] == "bar"} <= printed
    for must in ("F3", "detect.py", "not hand labels", "L3", "Nov 4", "LLM-judge", "Gate 2", "not met", "0.6",
                 "all six cells", "upper bound", "22 of 72"):
        assert must in words, must
