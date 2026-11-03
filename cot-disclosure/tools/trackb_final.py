"""B18, the final Track B table (started by Ritik on Nov 3; Arsha's from Nov 6): Gate 2 on every model and setting,
B16's authority arm beside it, and B17's three efforts, each row labelled with its own settings. Every number comes
from the tracked numbers-only summaries in results/summaries/trackB/ (no calls, no gitignored data).

  python tools/trackb_final.py     # -> docs/paper/tables/trackB_final.md and .csv

Columns: following per channel (X of Y, the model's answered runs at the 32,768 budget), Gate 2 (each tool channel
minus the user's hint, paired by question, 95% bootstrap clustered by question, "clear" if above 0), and, for the three
Voyager models, B16's user_authority arm and each tool arm's reading against it (F35; B19 confirmed it same-day).
B20's models join here when they are read (Nov 17).
"""
import csv
import json
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
SUM = CODE / "results" / "summaries" / "trackB"
OUT = CODE.parent / "docs" / "paper" / "tables"
# (report key, model, setting, temperature, served, B16 key, finding)
TRACKB = (("voyager | qwen3-30b-a3b-thinking-2507 | thinking=None", "Qwen3 30B Thinking", "thinking always", "0.6",
           "Voyager", "qwen3-30b-a3b-thinking-2507", "F15, F35"),
          ("voyager | qwen3-30b-a3b-instruct-2507 | thinking=None", "Qwen3 30B Instruct", "no thinking", "0.6",
           "Voyager", "qwen3-30b-a3b-instruct-2507", "F16, F35"),
          ("voyager | olmo3-7b-think | thinking=None", "Olmo 3 7B Think", "thinking always", "0.6",
           "Voyager, pinned format", "olmo3-7b-think", "F17, F35"),
          ("sol_vllm | qwen3-8b | thinking=True", "Qwen3-8B", "thinking on", "0.6", "Sol, our vLLM", None, "F29"),
          ("sol_vllm | qwen3-8b | thinking=False", "Qwen3-8B", "thinking off", "0.6", "Sol, our vLLM", None, "F29"))
TOOL = ("tool_real", "tool_injected")                       # the model's own call, or Olmo's inserted turn
TOOL_NAME = {"tool_real": "its own call", "tool_injected": "inserted tool turn"}


def _rates(channels):
    out = {}
    for c, name in (("user", "user"), ("tool_pasted", "pasted"), ("system", "system")):
        f = channels.get(c, {}).get("following")
        out[f"{name}_k"], out[f"{name}_n"] = (f["k"], f["n"]) if f else (None, None)
    tc = next(c for c in TOOL if c in channels)
    f = channels[tc]["following"]
    out.update({"tool_channel": TOOL_NAME[tc], "tool_k": f["k"], "tool_n": f["n"]})
    return out, tc


def _gate2(g, tc):
    out = {}
    for c, name in (("tool_pasted", "pasted"), (tc, "tool")):
        e = g.get(c) or {}
        lo, hi = e.get("interval") or (None, None)
        out.update({f"gate2_{name}": e.get("diff"), f"gate2_{name}_low": lo, f"gate2_{name}_high": hi,
                    f"gate2_{name}_clear": e.get("clear")})
    return out


def rows(summaries=SUM):
    """One row per model and setting."""
    rep = json.loads((Path(summaries) / "trackB_report.json").read_text())["budget_32768"]
    b16 = json.loads((Path(summaries) / "b16_report.json").read_text())
    b17 = json.loads((Path(summaries) / "b17_report.json").read_text())
    out = []
    for key, model, setting, temp, served, b16key, finding in TRACKB:
        m = rep[key]
        rates, tc = _rates(m["channels"])
        r = {"model": model, "setting": setting, "temperature": temp, "served": served, "finding": finding,
             **rates, **_gate2(m["gate2_tool_minus_user"], tc), "authority_k": None, "authority_n": None,
             "authority_reading_pasted": "", "authority_reading_tool": "", "note": ""}
        if b16key:
            a = b16[b16key]
            f = a["arms"]["user_authority"]["following"]
            r.update({"authority_k": f["k"], "authority_n": f["n"],
                      "authority_reading_pasted": a["primary"]["tool_pasted"]["reading"],
                      "authority_reading_tool": a["primary"][tc]["reading"],
                      "note": "B16's tool arms cross-day (T11); B19 gave the same readings same-day"})
        out.append(r)
    for e in ("low", "medium", "high"):
        p = b17["per_effort"][e]
        rates, tc = _rates(p["channels"])
        out.append({"model": "gpt-oss-20b", "setting": f"effort {e}", "temperature": "1.0",
                    "served": "Sol, our vLLM (harmony)", "finding": "F37", **rates,
                    **_gate2(p["gate2_tool_minus_user"], tc), "authority_k": None, "authority_n": None,
                    "authority_reading_pasted": "", "authority_reading_tool": "",
                    "note": "B17: its recommended temperature; run after its one-day window (pre-registration §13)"})
    return out


def _pts(v):
    return "—" if v is None else ("0" if abs(v) < 0.005 else f"{v * 100:+.0f}".replace("-", "−"))


def _iv(r, name):
    if r[f"gate2_{name}"] is None:
        return "—"
    return f"{_pts(r[f'gate2_{name}'])} [{_pts(r[f'gate2_{name}_low'])}, {_pts(r[f'gate2_{name}_high'])}]"


def _xy(r, name):
    return "—" if r[f"{name}_k"] is None else f"{r[f'{name}_k']} of {r[f'{name}_n']}"


def write(out=OUT, summaries=SUM):
    rs = rows(summaries)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "trackB_final.csv"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rs[0]))
        w.writeheader()
        w.writerows(rs)
    head = ("| model | setting | temp. | user | pasted | tool (channel) | system | Gate 2: pasted − user | "
            "Gate 2: tool − user | user's authority claim (B16) | tool vs authority (pasted; tool) | source |")
    lines = ["# Track B, the final table (B18; started Nov 3, Arsha's from Nov 6)", "",
             "Generated by `cot-disclosure/tools/trackb_final.py` from `results/summaries/trackB/`; do not edit by "
             "hand. Following = answered runs ending on the wrong hint's letter, X of Y (54 questions × 3 runs, the "
             "32,768-token budget). Gate 2: paired by question, 95% bootstrap clustered by question.", "", head,
             "|" + "---|" * 12]
    for r in rs:
        auth = _xy(r, "authority") if r["authority_k"] is not None else "—"
        reading = (f"{r['authority_reading_pasted']}; {r['authority_reading_tool']}" if r["authority_k"] is not None
                   else "—")
        lines.append(f"| {r['model']} | {r['setting']} | {r['temperature']} | {_xy(r, 'user')} | {_xy(r, 'pasted')} | "
                     f"{_xy(r, 'tool')} ({r['tool_channel']}) | {_xy(r, 'system')} | {_iv(r, 'pasted')} | "
                     f"{_iv(r, 'tool')} | {auth} | {reading} | {r['finding']} |")
    notes = {}
    for r in rs:
        if r["note"]:
            notes.setdefault(r["note"], []).append(r["model"])
    lines += ["", "Notes: " + "; ".join(f"{', '.join(dict.fromkeys(m))}: {n}" for n, m in notes.items()) + "."]
    md = out / "trackB_final.md"
    md.write_text("\n".join(lines) + "\n")
    return md, path


if __name__ == "__main__":
    for p in write():
        print(p.relative_to(CODE.parent))
