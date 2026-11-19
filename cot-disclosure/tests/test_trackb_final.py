"""B18's final Track B table (tools/trackb_final.py), slide 2 (tools/slide_figures.py fig_gate2) and slide 7
(trackb_final.fig_slide7): every number from the tracked summaries, each model labelled with its own settings. No
calls."""
import csv
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "tools"))

import trackb_final as tf  # noqa: E402

SUM = CODE / "results" / "summaries" / "trackB"


def by(rows, *keys):
    return {tuple(r[k] for k in keys): r for r in rows}


def test_rows_cover_every_model_and_setting():
    rows = by(tf.rows(), "model", "setting")
    assert set(rows) == {("Qwen3 30B Thinking", "thinking always"), ("Qwen3 30B Instruct", "no thinking"),
                         ("Olmo 3 7B Think", "thinking always"), ("Qwen3-8B", "thinking on"),
                         ("Qwen3-8B", "thinking off"), ("gpt-oss-20b", "effort low"), ("gpt-oss-20b", "effort medium"),
                         ("gpt-oss-20b", "effort high"), ("Gemma 4 26B-A4B", "thinking on"),
                         ("Gemma 4 26B-A4B", "thinking off"), ("Nemotron 3 Nano 30B-A3B", "thinking on"),
                         ("Nemotron 3 Nano 30B-A3B", "thinking off"), ("Granite 4.2 8B", "thinking on only")}
    assert rows[("gpt-oss-20b", "effort high")]["temperature"] == "1.0"
    assert rows[("Qwen3-8B", "thinking on")]["temperature"] == "0.6"
    assert "§13" in rows[("gpt-oss-20b", "effort low")]["note"]


def test_gate2_numbers_are_the_reports():
    rows = by(tf.rows(), "model", "setting")
    rep = json.loads((SUM / "trackB_report.json").read_text())["budget_32768"]
    g = rep["voyager | qwen3-30b-a3b-thinking-2507 | thinking=None"]["gate2_tool_minus_user"]["tool_pasted"]
    r = rows[("Qwen3 30B Thinking", "thinking always")]
    assert (r["gate2_pasted"], r["gate2_pasted_low"], r["gate2_pasted_high"]) == (g["diff"], *g["interval"])
    assert (r["user_k"], r["user_n"]) == (3, 162)
    o = rows[("Olmo 3 7B Think", "thinking always")]
    assert o["tool_channel"] == "inserted tool turn" and o["tool_k"] is not None
    b17 = json.loads((SUM / "b17_report.json").read_text())["per_effort"]["high"]
    h = rows[("gpt-oss-20b", "effort high")]
    assert h["gate2_tool"] == b17["gate2_tool_minus_user"]["tool_real"]["diff"]
    assert (h["tool_k"], h["tool_n"]) == (48, 158)


def test_b16_authority_on_the_three_voyager_models_only():
    rows = by(tf.rows(), "model", "setting")
    th = rows[("Qwen3 30B Thinking", "thinking always")]
    assert th["authority_k"] is not None and th["authority_reading_pasted"] == "tool beyond authority"
    assert rows[("Qwen3 30B Instruct", "no thinking")]["authority_reading_tool"] == "tool beyond authority"
    assert rows[("Olmo 3 7B Think", "thinking always")]["authority_reading_tool"] == "authority moves it more"
    assert rows[("Qwen3-8B", "thinking on")]["authority_k"] is None


def test_b20_rows_are_fb1s_readings_with_its_labels():
    """B20 (FB1, Nov 7): Gate 2 is R1's numbers, the authority readings R2's against B20's own arm, and every row
    carries B20's labels (temperature 1.0; the fallback; Granite thinking on only)."""
    rows = by(tf.rows(), "model", "setting")
    b20 = json.loads((SUM / "b20_report.json").read_text())
    for key, model in tf.B20:
        for s, d in b20[key]["settings"].items():
            b = d["budget_32768"]
            r = rows[(model, f"thinking {s}" + (" only" if key == "granite-4.2-8b" else ""))]
            tc = b20[key]["tool_channel"]
            assert r["temperature"] == "1.0" and r["finding"] == "FB1" and r["note"] == tf.B20_NOTE[tc]
            for name, c in (("pasted", "tool_pasted"), ("tool", tc)):
                assert (r[f"gate2_{name}"], r[f"gate2_{name}_low"], r[f"gate2_{name}_high"]) == \
                    (b["R1_gate2"][c]["diff"], *b["R1_gate2"][c]["interval"])
                assert r[f"gate2_{name}_clear"] is (b["R1_gate2"][c]["reading"] == "clear")
            assert (r["authority_reading_pasted"], r["authority_reading_tool"]) == \
                (b["R2_tool_or_authority"]["tool_pasted"]["reading"], b["R2_tool_or_authority"][tc]["reading"])
            assert (r["authority_k"], r["authority_n"]) == (b["R2_tool_or_authority"][tc]["b"]["k"],
                                                            b["R2_tool_or_authority"][tc]["b"]["n"])
    assert rows[("Gemma 4 26B-A4B", "thinking on")]["tool_channel"] == "inserted tool turn, the fallback"
    assert rows[("Granite 4.2 8B", "thinking on only")]["tool_channel"] == "its own call"
    g = rows[("Granite 4.2 8B", "thinking on only")]                     # FB1's table: +91 [+85, +96], 156 of 162
    assert (round(g["gate2_tool"] * 100), g["tool_k"], g["tool_n"]) == (91, 156, 162)
    assert rows[("Gemma 4 26B-A4B", "thinking off")]["authority_reading_tool"] == "authority moves it more"
    assert all(r["gate2_pasted_clear"] and r["gate2_tool_clear"] for r in tf.b20_rows())   # Gate 2: 10 of 10


def test_the_16000_cut_changes_one_reading_and_the_table_says_so(tmp_path):
    """Nov 14 (Arsha): the cut as one note, not a column. Of every reading in the table, only Gemma's tool vs authority
    with thinking on reads otherwise at the cut (FB1's dagger)."""
    assert tf.cut_changes() == [("Gemma 4 26B-A4B", "thinking on", "tool vs authority (inserted tool turn, the fallback)",
                                 "no difference detected", "authority moves it more")]
    md, _ = tf.write(out=tmp_path)
    assert ("except Gemma 4 26B-A4B, thinking on: tool vs authority (inserted tool turn, the fallback) reads authority "
            "moves it more (no difference detected at the budget).") in md.read_text()


def test_write_makes_the_table_and_its_csv(tmp_path):
    md, path = tf.write(out=tmp_path)
    table = list(csv.DictReader(open(path)))
    assert len(table) == 13 and md.read_text().count("\n| ") >= 14


def test_slide_2_draws_gate2_per_model(tmp_path):
    import slide_figures as sf
    paths = sf.fig_gate2(out=tmp_path)
    assert [p.suffix for p in paths] == [".png", ".svg", ".csv"]
    table = list(csv.DictReader(open(paths[2])))
    assert len(table) == 26                                    # 13 model settings x 2 tool channels
    assert all(float(r["low"]) <= float(r["value"]) <= float(r["high"]) for r in table)


# ---------------------------------------------------------------- slide 7 (Arsha, Nov 15)
FIG7 = CODE.parent / "docs" / "trackB" / "figures"
# F35's table and secondary, F40's table: following per source the user cites, X of Y
SOURCES_7 = {"Qwen3 30B Thinking": {"user": (3, 162), "user_classmate": (12, 162), "user_authority": (44, 162),
                                    "user_manual": (78, 162)},
             "Qwen3 30B Instruct": {"user": (1, 162), "user_classmate": (9, 162), "user_authority": (25, 162),
                                    "user_manual": (28, 162)},
             "Olmo 3 7B Think": {"user": (13, 162), "user_classmate": (27, 160), "user_authority": (69, 161),
                                 "user_manual": (78, 159)}}
# (model, arm): (points, reading), from F35's table and F40's (b), (a) and (c)
READINGS_7 = {
    ("Qwen3 30B Thinking", "tool_pasted - user_authority"): (12, "tool beyond authority"),
    ("Qwen3 30B Thinking", "tool_real - user_authority"): (6, "no difference detected"),
    ("Qwen3 30B Instruct", "tool_pasted - user_authority"): (6, "no difference detected"),
    ("Qwen3 30B Instruct", "tool_real - user_authority"): (75, "tool beyond authority"),
    ("Olmo 3 7B Think", "tool_pasted - user_authority"): (-3, "no difference detected"),
    ("Olmo 3 7B Think", "tool_injected - user_authority"): (-14, "authority moves it more"),
    ("Qwen3 30B Thinking", "user_manual - user_classmate"): (41, "the manual moves it more"),
    ("Qwen3 30B Instruct", "user_manual - user_classmate"): (12, "the manual moves it more"),
    ("Olmo 3 7B Think", "user_manual - user_classmate"): (32, "the manual moves it more"),
    ("Qwen3 30B Thinking", "user_classmate - user"): (6, "a classmate's claim moves it more"),
    ("Qwen3 30B Instruct", "user_classmate - user"): (5, "a classmate's claim moves it more"),
    ("Olmo 3 7B Think", "user_classmate - user"): (9, "a classmate's claim moves it more"),
    ("Qwen3 30B Thinking", "user_manual - user_authority"): (21, "the manual higher"),
    ("Qwen3 30B Instruct", "user_manual - user_authority"): (2, "no difference detected"),
    ("Olmo 3 7B Think", "user_manual - user_authority"): (6, "no difference detected"),
    ("Qwen3 30B Thinking", "tool_pasted - user_manual"): (-10, "authority moves it more"),
    ("Qwen3 30B Thinking", "tool_real - user_manual"): (-23, "authority moves it more"),
    ("Qwen3 30B Instruct", "tool_pasted - user_manual"): (2, "no difference detected"),
    ("Qwen3 30B Instruct", "tool_real - user_manual"): (73, "tool beyond authority"),
    ("Olmo 3 7B Think", "tool_pasted - user_manual"): (-9, "authority moves it more"),
    ("Olmo 3 7B Think", "tool_injected - user_manual"): (-21, "authority moves it more")}


def test_slide7_numbers_are_f35s_and_f40s():
    """Every bar is F35's or F40's X of Y; every difference and reading F35's table or F40's (b), (a) and (c)."""
    rows = tf.slide7_rows()
    bars = {(r["model"], r["arm"]): (r["k"], r["n"]) for r in rows if r["shown"] == "bar"}
    assert bars == {(m, arm): kn for m, arms in SOURCES_7.items() for arm, kn in arms.items()}
    diffs = {(r["model"], r["arm"]): (round(r["value"] * 100), r["reading"]) for r in rows
             if r["finding"] in ("F35", "F40") and r["shown"] != "bar"}
    assert diffs == READINGS_7
    for r in rows:
        assert r["low"] <= r["value"] <= r["high"], (r["model"], r["arm"])
    b16 = json.loads((SUM / "b16_report.json").read_text())
    b24 = json.loads((SUM / "b24_report.json").read_text())
    for key, _m in tf.MODELS_7:      # B24's report carries B16's answer-key arm and Track B's guess unchanged
        f, b = b16[key]["arms"]["user_authority"]["following"], b24[key]["a_wording"]["b"]
        assert (f["k"], f["n"]) == (b["k"], b["n"])
        g, h = b16[key]["secondary"]["authority_minus_user"]["b"], b24[key]["b_classmate_minus_user"]["b"]
        assert (g["k"], g["n"]) == (h["k"], h["n"])


def test_slide7_note_gives_the_cross_day_readings_the_cut_and_b20s_count():
    rows = tf.slide7_rows()
    assert tf.slide7_cut_changes() == []                    # F35 and F40: every reading the same at the cut
    fb1 = [r for r in rows if r["finding"] == "FB1"]
    assert len(fb1) == 10 and [r["reading"] for r in fb1].count("tool beyond authority") == 5
    note = tf.slide7_note(rows)
    for must in ("+6, +5, +9 (a classmate's claim moves it more, all three)",
                 "+21, +2, +6 (Qwen3 30B Thinking: the manual higher; the others: no difference detected)",
                 "Every reading here is the same at the 16,000-token cut",
                 "the tool beyond my answer key in 5 of 10 readings, authority moves it more in 1",
                 "temperature 1.0", "Oct 27-28", "Nov 1"):
        assert must in note, must


def test_slide7_draws_x_of_y_plain_names_and_its_csv(monkeypatch, tmp_path):
    """The slide shows every bar's and tool arm's X of Y and no internal code (slide_figures' Nov 14 rule); the CSV
    keeps the ids, the F-numbers and the sources; PNG 2000 x 1125."""
    import re
    import struct

    import slide_figures as sf
    from matplotlib.text import Text
    from test_slide_figures import CODES
    figs = []
    real = sf.save
    monkeypatch.setattr(sf, "save", lambda fig, name, rows, out: figs.append(fig) or real(fig, name, rows, out))
    png, svg, path = tf.fig_slide7(out=tmp_path)
    words = " ".join(t.get_text() for t in figs[0].findobj(Text) if t.get_visible()).replace("\n", " ")
    assert not CODES.findall(words), sorted(set(CODES.findall(words)))
    table = list(csv.DictReader(open(path)))
    pairs = lambda rs, k, n: {(int(r[k]), int(r[n])) for r in rs if r[k] != ""}            # noqa: E731
    shown = [r for r in table if r["shown"] in ("bar", "dot")]
    printed = {(int(k), int(n)) for k, n in re.findall(r"(\d+) of (\d+)", words)}
    assert pairs(table, "k", "n") & printed >= {(int(r["k"]), int(r["n"])) for r in shown}
    assert printed - pairs(table, "k", "n") - pairs(table, "compared_k", "compared_n") == {(5, 10)}  # B20's count
    for must in ("Oct 27–28", "Oct 31", "Nov 4", "my answer key", "the official manual", "tool beyond authority",
                 "authority moves it more", "no difference detected", "+41"):
        assert must in words, must
    assert {r["finding"] for r in table} == {"F35", "F40", "F35, F40", "FB1"}
    assert all(r["source"].split()[0] in ("b16_report.json", "b24_report.json", "b20_report.json") for r in table)
    assert struct.unpack(">II", png.read_bytes()[16:24]) == (2000, 1125)
    assert svg.exists()


def test_slide7_committed_csv_is_the_code_s():
    """docs/trackB/figures/authority_ladder.csv is what fig_slide7 writes now (regenerate with --slide7)."""
    import io
    buf = io.StringIO()
    rows = tf.slide7_rows()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\r\n")
    w.writeheader()
    w.writerows(rows)
    assert (FIG7 / "authority_ladder.csv").read_text(newline="") == buf.getvalue()
