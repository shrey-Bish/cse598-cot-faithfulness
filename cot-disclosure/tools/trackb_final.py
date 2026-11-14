"""B18, the final Track B table (started by Ritik on Nov 3; Arsha's from Nov 6): Gate 2 on every model and setting,
B16's authority arm beside it, and B17's three efforts, each row labelled with its own settings. Every number comes
from the tracked numbers-only summaries in results/summaries/trackB/ (no calls, no gitignored data).

  python tools/trackb_final.py     # -> docs/paper/tables/trackB_final.md and .csv

Columns: following per channel (X of Y, the model's answered runs at the 32,768 budget), Gate 2 (each tool channel
minus the user's hint, paired by question, 95% bootstrap clustered by question, "clear" if above 0), and, for the three
Voyager models, B16's user_authority arm and each tool arm's reading against it (F35; B19 confirmed it same-day).
B20's three families (FB1, read Nov 7 by its rule; Arsha, Nov 14) follow, each with B20's labels: temperature 1.0
(each model's recommended), the inserted tool turn as the pre-registered fallback (Gemma, Nemotron), Granite thinking on
only. Their authority arm is B20's own, run with the rest of B20, and their Gate 2 is B20's R1 (the same numbers).
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
# B20 (FB1): (summary key, model), then its labels by tool channel (B20's log §15, §16; FINDINGS_B FB1)
B20 = (("gemma-4-26b-a4b-it", "Gemma 4 26B-A4B"), ("nemotron-3-nano-30b-a3b", "Nemotron 3 Nano 30B-A3B"),
       ("granite-4.2-8b", "Granite 4.2 8B"))
B20_CHANNEL = {"tool_real": "its own call", "tool_injected": "inserted tool turn, the fallback"}
B20_NOTE = {"tool_injected": "B20: temperature 1.0, each model's recommended; the inserted tool turn is the "
                             "pre-registered fallback (B20's log §15, §16); the authority arm is B20's own, same day",
            "tool_real": "B20: temperature 1.0, its recommended; thinking on only: its off mode still wrote a think "
                         "block (6 of 6 smoke runs, B20's log §15); the authority arm is B20's own, same day"}


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
    out += b20_rows(summaries)
    return out


def b20_rows(summaries=SUM):
    """B20's rows (FB1): one per family and thinking setting, at the 32,768 budget, from b20_report.json's
    secondaries (Gate 2 there is R1's numbers) and R2's readings against B20's own authority arm."""
    b20 = json.loads((Path(summaries) / "b20_report.json").read_text())
    out = []
    for key, model in B20:
        m = b20[key]
        for s, d in m["settings"].items():
            b = d["budget_32768"]
            sec = b["secondary"]
            rates, tc = _rates(sec["channels"])
            only = len(m["settings"]) == 1
            f = sec["user_authority"]["following"]
            out.append({"model": model, "setting": f"thinking {s}" + (" only" if only else ""),
                        "temperature": f"{m['temperature']:.1f}", "served": "Sol, our vLLM", "finding": "FB1",
                        **rates, "tool_channel": B20_CHANNEL[tc], **_gate2(sec["gate2_tool_minus_user"], tc),
                        "authority_k": f["k"], "authority_n": f["n"],
                        "authority_reading_pasted": b["R2_tool_or_authority"]["tool_pasted"]["reading"],
                        "authority_reading_tool": b["R2_tool_or_authority"][tc]["reading"], "note": B20_NOTE[tc]})
    return out


def cut_changes(summaries=SUM):
    """Every reading in the table that reads otherwise at the 16,000-token cut, as (model, setting, reading, at the
    budget, at the cut): Gate 2 (clear or not) for every row, tool vs authority for B16's and B20's rows. Decided Nov 14
    (Arsha): the table stays at the 32,768 budget with one note naming these, not a column per reading."""
    S = Path(summaries)
    rep = json.loads((S / "trackB_report.json").read_text())
    b16 = json.loads((S / "b16_report.json").read_text())
    b17 = json.loads((S / "b17_report.json").read_text())
    b20 = json.loads((S / "b20_report.json").read_text())
    clear = lambda e: "clear" if (e or {}).get("clear") else "not clear"                     # noqa: E731
    name = lambda c, names: "pasted" if c == "tool_pasted" else names.get(c, c)               # noqa: E731
    out = []

    def gate2(model, setting, at, cut, names):
        out.extend((model, setting, f"Gate 2 ({name(c, names)})", clear(at[c]), clear(cut.get(c)))
                   for c in at if clear(at[c]) != clear(cut.get(c)))

    for key, model, setting, _t, _s, b16key, _f in TRACKB:
        gate2(model, setting, rep["budget_32768"][key]["gate2_tool_minus_user"],
              rep["cut_16000"].get(key, {}).get("gate2_tool_minus_user", {}), TOOL_NAME)
        if b16key:
            v = b16[b16key]
            out.extend((model, setting, f"tool vs authority ({name(c, TOOL_NAME)})", p["reading"],
                        v["primary_16k"][c]["reading"]) for c, p in v["primary"].items()
                       if v["primary_16k"][c]["reading"] != p["reading"])
    for e in ("low", "medium", "high"):
        gate2("gpt-oss-20b", f"effort {e}", b17["per_effort"][e]["gate2_tool_minus_user"],
              b17["per_effort_cut_16000"][e]["gate2_tool_minus_user"], TOOL_NAME)
    for key, model in B20:
        m = b20[key]
        for s, d in m["settings"].items():
            setting = f"thinking {s}" + (" only" if len(m["settings"]) == 1 else "")
            for r, what in (("R1_gate2", "Gate 2"), ("R2_tool_or_authority", "tool vs authority")):
                out.extend((model, setting, f"{what} ({name(c, B20_CHANNEL)})", x["reading"],
                            d["cut_16000"][r][c]["reading"]) for c, x in d["budget_32768"][r].items()
                           if d["cut_16000"][r][c]["reading"] != x["reading"])
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
            "Gate 2: tool − user | user's authority claim (B16; B20 its own) | tool vs authority (pasted; tool) | "
            "source |")
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
    changed = cut_changes(summaries)
    lines += ["", "At the 16,000-token cut (each report gives it beside every reading): every reading in this table "
              "is the same" + (", except " + "; ".join(f"{m}, {s}: {what} reads {cut} ({at} at the budget)"
                                                     for m, s, what, at, cut in changed) if changed else "") + "."]
    md = out / "trackB_final.md"
    md.write_text("\n".join(lines) + "\n")
    return md, path


if __name__ == "__main__":
    for p in write():
        print(p.relative_to(CODE.parent))
