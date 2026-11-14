"""B18's final Track B table (tools/trackb_final.py) and slide 2 (tools/slide_figures.py fig_gate2): every number
from the tracked summaries, each model labelled with its own settings. No calls."""
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
