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
                         ("gpt-oss-20b", "effort high")}
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


def test_write_makes_the_table_and_its_csv(tmp_path):
    md, path = tf.write(out=tmp_path)
    table = list(csv.DictReader(open(path)))
    assert len(table) == 8 and md.read_text().count("\n| ") >= 9


def test_slide_2_draws_gate2_per_model(tmp_path):
    import slide_figures as sf
    paths = sf.fig_gate2(out=tmp_path)
    assert [p.suffix for p in paths] == [".png", ".svg", ".csv"]
    table = list(csv.DictReader(open(paths[2])))
    assert len(table) == 16                                    # 8 model settings x 2 tool channels
    assert all(float(r["low"]) <= float(r["value"]) <= float(r["high"]) for r in table)
