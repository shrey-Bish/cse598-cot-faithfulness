"""The template's DATA from the frozen data (Nov 22): the explainer's compact(collect()) (tools/build_demo.py, sections
s1..s6 and x, every number traced to its summary) mapped to the template's keys, floats rounded to 4 places.

  hint   <- s1.gate2   (finding -> ids, channel -> toolForm, d_pasted -> dPasted, d_tool -> dTool)
  dose   <- s1.dose    (tool_channel -> toolForm, answer_key -> key; the comparisons under r)
  newfam <- s1.r2
  quiet  <- s2
  layers <- s3         (layers -> effect; qwen left out)
  agents <- s4
  fixes  <- s5

tests/test_demo_template.py checks that template_data() reproduces data.json exactly, so data.json is never edited by
hand and the page's numbers are the frozen ones.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE = HERE.parents[1]
for p in (CODE, CODE / "tools", CODE / "progress"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

HINT = {"finding": "ids", "channel": "toolForm", "d_pasted": "dPasted", "d_tool": "dTool"}
DOSE = {"tool_channel": "toolForm", "answer_key": "key"}
DOSE_R = ("manual_minus_classmate", "manual_minus_key", "pasted_minus_manual", "call_minus_manual")


def r4(o):
    if isinstance(o, bool) or o is None:
        return o
    if isinstance(o, float):
        return round(o, 4)
    if isinstance(o, dict):
        return {k: r4(v) for k, v in o.items()}
    if isinstance(o, list):
        return [r4(v) for v in o]
    return o


def _rename(row, names):
    return {names.get(k, k): v for k, v in row.items()}


def _dose(row):
    out = {DOSE.get(k, k): v for k, v in row.items() if k not in DOSE_R}
    r = {k: row[k] for k in DOSE_R if k in row}
    if r:
        out["r"] = r
    return out


def from_frozen(d):
    """d: compact(collect()) of the frozen summaries."""
    s3 = {("effect" if k == "layers" else k): v for k, v in d["s3"].items() if k != "qwen"}
    return r4({
        "hint": [_rename(row, HINT) for row in d["s1"]["gate2"]],
        "dose": [_dose(row) for row in d["s1"]["dose"]],
        "newfam": d["s1"]["r2"],
        "quiet": d["s2"],
        "layers": s3,
        "agents": d["s4"],
        "fixes": d["s5"],
    })


def template_data(summaries=None):
    import build_demo as bd
    return from_frozen(bd.compact(bd.collect(summaries or bd.SUM)))


if __name__ == "__main__":
    print(json.dumps(template_data(), indent=1)[:400])
