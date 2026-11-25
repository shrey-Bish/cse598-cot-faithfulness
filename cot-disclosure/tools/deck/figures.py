"""Slide-specific figures for the final presentation (storyboard drafts; Phase B adds a test against 02_NUMBERS.md).

Every plotted number is read from a tracked numbers-only summary under results/summaries/ (no calls, no gitignored
data). `plotted()` returns every (figure, label, k, n, interval, source file, key path) row, so a test can compare
them with docs/presentation/pack/02_NUMBERS.md. Intervals are 95% Wilson computed from k of n (checked against the
summaries' own stored Wilson bounds where they exist), except the trade-off's crossing interval, which is stored.

  python tools/deck/figures.py [--out DIR]      # -> DIR/fig_*.png (300 dpi at the size shown on a 10 x 5.625 in slide)

Style (DECK_BRIEF section 4): maroon = the tool (or private reasoning), gold = the user (or the final answer),
near-black text, Arial, labels at least 14 pt as drawn at the figure's stated size, plain names only.
"""
import argparse
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

CODE = Path(__file__).resolve().parents[2]            # cot-disclosure/
REPO = CODE.parent
SUM = CODE / "results" / "summaries"
OUT = REPO / "docs" / "presentation" / "final" / "storyboard"

MAROON, GOLD, INK, GRID, MUTED = "#8C1D40", "#FFC627", "#191919", "#E8E8E8", "#6B6B6B"
FS = 14  # minimum label size, pt, at the figure's drawn size

_have = {f.name for f in font_manager.fontManager.ttflist}
plt.rcParams.update({
    "font.family": "Arial" if "Arial" in _have else "DejaVu Sans", "font.size": FS, "text.color": INK,
    "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "axes.edgecolor": INK,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "axes.spines.top": False, "axes.spines.right": False, "svg.fonttype": "none"})

ROWS = []   # every plotted number


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def J(path):
    return json.loads((SUM / path).read_text())


def rec(fig, label, k, n, source, keypath, finding, stored=None):
    """Record one plotted proportion; check the computed Wilson interval against the summary's own, if any."""
    lo, hi = wilson(k, n)
    if stored:
        assert abs(lo - stored[0]) < 1e-6 and abs(hi - stored[1]) < 1e-6, (label, (lo, hi), stored)
    ROWS.append({"figure": fig, "label": label, "k": k, "n": n, "low": lo, "high": hi, "source": source,
                 "key_path": keypath, "finding": finding})
    return k / n, lo, hi


def get(d, path):
    for p in path:
        d = d[p]
    return d


def prop(fig, label, d, path, source, keypath, finding):
    e = get(d, path)
    return rec(fig, label, e["k"], e["n"], source, keypath, finding, e.get("wilson"))


# ---------------------------------------------------------------- figure 1: tool vs user
TRACKB = "trackB/trackB_report.json"
B20 = "trackB/b20_report.json"
# (plain name, tool channel label, kind, source, path to the setting's channels, tool channel key, finding)
F1_MODELS = [
    ("Qwen3 30B Thinking", "own call", "call", TRACKB, ["budget_32768", "voyager | qwen3-30b-a3b-thinking-2507 | thinking=None", "channels"], "tool_real", "F15"),
    ("Qwen3 30B Instruct", "own call", "call", TRACKB, ["budget_32768", "voyager | qwen3-30b-a3b-instruct-2507 | thinking=None", "channels"], "tool_real", "F16"),
    ("Olmo 3 7B Think", "inserted tool turn", "inserted", TRACKB, ["budget_32768", "voyager | olmo3-7b-think | thinking=None", "channels"], "tool_injected", "F17"),
    ("Qwen3-8B, thinking on", "own call", "call", TRACKB, ["budget_32768", "sol_vllm | qwen3-8b | thinking=True", "channels"], "tool_real", "F29"),
    ("Qwen3-8B, thinking off", "own call", "call", TRACKB, ["budget_32768", "sol_vllm | qwen3-8b | thinking=False", "channels"], "tool_real", "F29"),
    ("Gemma 4, thinking on", "inserted tool turn", "inserted", B20, ["gemma-4-26b-a4b-it", "settings", "on", "budget_32768", "secondary", "channels"], "tool_injected", "FB1"),
    ("Gemma 4, thinking off", "inserted tool turn", "inserted", B20, ["gemma-4-26b-a4b-it", "settings", "off", "budget_32768", "secondary", "channels"], "tool_injected", "FB1"),
    ("Nemotron 3, thinking on", "inserted tool turn", "inserted", B20, ["nemotron-3-nano-30b-a3b", "settings", "on", "budget_32768", "secondary", "channels"], "tool_injected", "FB1"),
    ("Nemotron 3, thinking off", "inserted tool turn", "inserted", B20, ["nemotron-3-nano-30b-a3b", "settings", "off", "budget_32768", "secondary", "channels"], "tool_injected", "FB1"),
    ("Granite 4.2", "own call", "call", B20, ["granite-4.2-8b", "settings", "on", "budget_32768", "secondary", "channels"], "tool_real", "FB1"),
]


def fig1_data():
    out = []
    for name, chan, kind, src, path, tool_key, fid in F1_MODELS:
        ch = get(J(src), path)
        kp = "/".join(path)
        u = prop("tool_vs_user", f"{name}: user", ch, ["user", "following"], src, f"{kp}/user/following", fid)
        t = prop("tool_vs_user", f"{name}: tool ({chan})", ch, [tool_key, "following"], src,
                 f"{kp}/{tool_key}/following", fid)
        ku, kt = ROWS[-2], ROWS[-1]
        out.append({"name": name, "kind": kind, "user": u, "tool": t,
                    "user_kn": (ku["k"], ku["n"]), "tool_kn": (kt["k"], kt["n"])})
    out.sort(key=lambda r: r["tool"][0])
    inst = [r for r in out if r["name"] == "Qwen3 30B Instruct"][0]
    out.remove(inst)
    return [inst] + out          # the annotated pair sits on the bottom row; the rest ascend by tool rate


def fig_tool_vs_user(path):
    data = fig1_data()
    n = len(data)
    fig, ax = plt.subplots(figsize=(8.2, 5.0), dpi=300)
    for i, r in enumerate(data):
        y = i
        (pu, ulo, uhi), (pt, tlo, thi) = r["user"], r["tool"]
        ax.plot([pu * 100, pt * 100], [y, y], color=INK, lw=1.2, zorder=1)
        ax.plot([ulo * 100, uhi * 100], [y, y], color=INK, lw=3, solid_capstyle="butt", alpha=0.45, zorder=2)
        ax.plot([tlo * 100, thi * 100], [y, y], color=MAROON, lw=3, solid_capstyle="butt", alpha=0.45, zorder=2)
        ax.scatter([pu * 100], [y], s=110, color=GOLD, edgecolor=INK, linewidth=1.2, zorder=4)
        mk = "o" if r["kind"] == "call" else "D"
        ax.scatter([pt * 100], [y], s=110 if mk == "o" else 80, marker=mk, color=MAROON, edgecolor=MAROON, zorder=4, clip_on=False)
        ax.text(1.05, y, f"{r['user_kn'][0]}/{r['user_kn'][1]}", va="center", ha="left", color=INK, transform=ax.get_yaxis_transform())
        ax.text(1.45, y, f"{r['tool_kn'][0]}/{r['tool_kn'][1]}", va="center", ha="left", color=MAROON, fontweight="bold", transform=ax.get_yaxis_transform())
    ax.set_yticks(range(n))
    ax.set_yticklabels([r["name"] for r in data])
    ax.set_ylim(-0.6, n - 0.2)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 50, 100])
    ax.set_xticklabels(["0%", "50%", "100%"])
    ax.set_xlabel("Runs that followed the wrong letter")
    ax.xaxis.grid(True, color=GRID, lw=1)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.spines["left"].set_visible(False)
    ax.text(1.05, n - 0.35, "User", ha="left", va="bottom", fontweight="bold", transform=ax.get_yaxis_transform())
    ax.text(1.45, n - 0.35, "Tool", ha="left", va="bottom", color=MAROON, fontweight="bold", transform=ax.get_yaxis_transform())
    # the one annotation: Instruct
    iy = 0
    ax.annotate("Instruct:\nuser 1 of 162\ntool 147 of 162",
                xy=(91, iy + 0.25), xytext=(50, 2.1), ha="left", va="center", fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.4, shrinkA=2, shrinkB=8))
    # legend (drawn by hand: marker meaning)
    ax.scatter([], [], s=110, color=GOLD, edgecolor=INK, label="user gives the letter")
    ax.scatter([], [], s=110, color=MAROON, label="tool: the model's own call")
    ax.scatter([], [], s=80, marker="D", color=MAROON, label="tool: inserted tool turn")
    fig.legend(loc="lower left", bbox_to_anchor=(0.02, -0.005), ncol=1, frameon=False, handletextpad=0.3,
               labelspacing=0.15)
    fig.subplots_adjust(left=0.27, right=0.66, top=0.93, bottom=0.30)
    fig.savefig(path)
    plt.close(fig)


# ---------------------------------------------------------------- figure 2: reasoning vs answer
def fig2_data():
    t = J(TRACKB)["budget_32768"]
    b = J(B20)
    q8 = t["sol_vllm | qwen3-8b | thinking=True"]["channels"]["tool_real"]
    q30 = t["voyager | qwen3-30b-a3b-thinking-2507 | thinking=None"]["channels"]["tool_real"]
    q8p = "budget_32768/sol_vllm | qwen3-8b | thinking=True/channels/tool_real"
    q30p = "budget_32768/voyager | qwen3-30b-a3b-thinking-2507 | thinking=None/channels/tool_real"
    fig = "reasoning_vs_answer"
    rows = [
        {"name": "Qwen3-8B, thinking on", "sub": "after its own call",
         "priv": prop(fig, "Qwen3-8B on: reasoning names tool (when called)", q8, ["mention_private_when_called"], TRACKB, f"{q8p}/mention_private_when_called", "F29"),
         "final": prop(fig, "Qwen3-8B on: final answer names tool (when followed)", q8, ["mention_final_when_followed"], TRACKB, f"{q8p}/mention_final_when_followed", "F29")},
        {"name": "Qwen3 30B Thinking", "sub": "after its own call",
         "priv": prop(fig, "Qwen3 30B Thinking: reasoning names tool (when called)", q30, ["mention_private_when_called"], TRACKB, f"{q30p}/mention_private_when_called", "F15"),
         "final": prop(fig, "Qwen3 30B Thinking: final answer names tool (when followed)", q30, ["mention_final_when_followed"], TRACKB, f"{q30p}/mention_final_when_followed", "F15")},
    ]
    g_on = b["gemma-4-26b-a4b-it"]["settings"]["on"]["budget_32768"]["secondary"]["channels"]["tool_injected"]
    g_off = b["gemma-4-26b-a4b-it"]["settings"]["off"]["budget_32768"]["secondary"]["channels"]["tool_injected"]
    gp = "gemma-4-26b-a4b-it/settings/{}/budget_32768/secondary/channels/tool_injected"
    rows.append({"name": "Gemma 4, thinking on", "sub": "inserted tool turn",
                 "priv": prop(fig, "Gemma on: reasoning names tool", g_on, ["mention_private"], B20, gp.format("on") + "/mention_private", "FB1"),
                 "final": prop(fig, "Gemma on: final answer names tool", g_on, ["mention_final"], B20, gp.format("on") + "/mention_final", "FB1")})
    rows.append({"name": "Gemma 4, thinking off", "sub": "inserted tool turn", "priv": None,
                 "final": prop(fig, "Gemma off: final answer names tool", g_off, ["mention_final"], B20, gp.format("off") + "/mention_final", "FB1")})
    return rows


def fig_reasoning_vs_answer(path):
    rows = fig2_data()
    n = len(rows)
    fig, ax = plt.subplots(figsize=(8.0, 4.4), dpi=300)
    bh = 0.34
    ticks = []
    for i, r in enumerate(rows):
        yc = (n - 1 - i) * 1.25
        ticks.append(yc)
        for j, (key, col, lab) in enumerate((("priv", MAROON, "private reasoning"), ("final", GOLD, "final answer"))):
            y = yc + 0.2 if key == "priv" else yc - 0.2
            v = r[key]
            kn = [x for x in ROWS if False]
            if v is None:
                ax.text(2, y, "no private reasoning (thinking off)", va="center", ha="left", color=MUTED, style="italic")
                continue
            p, lo, hi = v
            ax.barh(y, p * 100, height=bh, color=col, edgecolor=INK if col == GOLD else col, linewidth=0.8, zorder=2)
            ax.plot([lo * 100, hi * 100], [y, y], color=INK, lw=1.6, zorder=3)
            for cap in (lo, hi):
                ax.plot([cap * 100] * 2, [y - 0.07, y + 0.07], color=INK, lw=1.6, zorder=3)
    # n labels, aligned in a column right of the axis
    order = []
    for r in rows:
        order += [r["priv"], r["final"]]
    labs = [x for x in ROWS if x["figure"] == "reasoning_vs_answer"]
    li = 0
    for i, r in enumerate(rows):
        yc = (n - 1 - i) * 1.25
        for key, dy in (("priv", 0.2), ("final", -0.2)):
            if r[key] is None:
                continue
            e = labs[li]
            li += 1
            ax.text(106, yc + dy, f"{e['k']} of {e['n']}", va="center", ha="left",
                    color=MAROON if key == "priv" else INK, fontweight="bold")
    ax.set_yticks(ticks)
    ax.set_yticklabels([r["name"] for r in rows])
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.75, (n - 1) * 1.25 + 0.75)
    ax.set_xticks([0, 50, 100])
    ax.set_xticklabels(["0%", "50%", "100%"])
    ax.set_xlabel("Runs that name the tool as the source")
    ax.xaxis.grid(True, color=GRID, lw=1)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.spines["left"].set_visible(False)
    ax.annotate("never, in 143 runs", xy=(1, (n - 1) * 1.25 - 0.2), xytext=(16, (n - 1) * 1.25 - 0.2),
                va="center", ha="left", fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.4, shrinkA=2, shrinkB=2))
    ax.bar(0, 0, color=MAROON, label="private reasoning")
    ax.bar(0, 0, color=GOLD, edgecolor=INK, label="final answer")
    fig.legend(loc="lower left", bbox_to_anchor=(0.02, -0.005), ncol=2, frameon=False, handlelength=1.2,
               columnspacing=1.2)
    fig.subplots_adjust(left=0.30, right=0.78, top=0.97, bottom=0.25)
    fig.savefig(path)
    plt.close(fig)


# ---------------------------------------------------------------- figure 3: trade-off (exploratory)
def fig3_data():
    src = "trackA/gpu/a39/tradeoff_e2.json"
    d = J(src)
    fig = "tradeoff"
    c = d["crossings"]["answered"]["a40"]
    kp = "crossings/answered/a40"
    pts = {}
    for sys_, side, name in (("a40", "a", "Consistency training"), ("a40", "b", "One-line instruction")):
        s = c[side]
        wk, wn = s["a_W_kn"]
        ck, cn = s["a_C_kn"]
        pts[name] = {"W": rec(fig, f"{name}: correct when the tool is wrong (p = 0)", wk, wn, src, f"{kp}/{side}/a_W_kn", "F41/story 7"),
                     "C": rec(fig, f"{name}: correct when the tool is right (p = 1)", ck, cn, src, f"{kp}/{side}/a_C_kn", "F41/story 7"),
                     "W_kn": (wk, wn), "C_kn": (ck, cn)}
    cross = {"p": c["p_star"], "interval": c["interval"]}
    ROWS.append({"figure": fig, "label": "crossover p* (consistency training = instruction)", "k": None, "n": None,
                 "low": c["interval"][0], "high": c["interval"][1], "source": src, "key_path": f"{kp}/p_star, {kp}/interval",
                 "finding": "story 7 (REPORT s7)", "value": c["p_star"]})
    return pts, cross


def fig_tradeoff(path):
    pts, cross = fig3_data()
    fig, ax = plt.subplots(figsize=(6.6, 4.3), dpi=300)
    spec = {"Consistency training": (MAROON, "o"), "One-line instruction": (INK, "s")}
    for name, (col, mk) in spec.items():
        w, c_ = pts[name]["W"], pts[name]["C"]
        ax.plot([0, 100], [w[0] * 100, c_[0] * 100], color=col, lw=3, zorder=3)
        for x, v in ((0, w), (100, c_)):
            ax.plot([x, x], [v[1] * 100, v[2] * 100], color=col, lw=1.6, zorder=3)
            ax.scatter([x], [v[0] * 100], s=60, color=col, marker=mk, zorder=4, clip_on=False)
    # crossover and its interval, on the x axis
    p = cross["p"]
    lo, hi = cross["interval"]
    yc = pts["Consistency training"]["W"][0] * 100 + p * (pts["Consistency training"]["C"][0] - pts["Consistency training"]["W"][0]) * 100
    ax.axvspan(lo * 100, hi * 100, color=GRID, zorder=0)
    ax.plot([p * 100], [yc], marker="o", ms=11, mfc="white", mec=INK, mew=2, zorder=5)
    ax.annotate("Crossover: tool right\nabout 36% of the time\n[22%, 50%]", xy=(p * 100, yc), xytext=(50, 47),
                ha="left", va="center", fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.4, shrinkA=2, shrinkB=7))
    # direct labels
    ax.text(30, 94, "One-line instruction", color=INK, fontweight="bold", ha="left", va="center")
    ax.text(52, 63, "Consistency training", color=MAROON, fontweight="bold", ha="left", va="center")
    # n at the ends
    for name, col in (("Consistency training", MAROON), ("One-line instruction", INK)):
        w, c_ = pts[name]["W_kn"], pts[name]["C_kn"]
        wy = pts[name]["W"][0] * 100
        cy = pts[name]["C"][0] * 100
        ax.text(3, wy + (9 if name.startswith("Cons") else -3.6), f"{w[0]} of {w[1]}", color=col, ha="left", va="center")
        ax.text(103, cy, f"{c_[0]} of {c_[1]}", color=col, ha="left", va="center", clip_on=False)
    ax.set_xlim(0, 100)
    ax.set_ylim(40, 100)
    ax.set_xticks([0, 50, 100])
    ax.set_xticklabels(["never", "half", "always"])
    ax.get_xticklabels()[0].set_ha("left")
    ax.get_xticklabels()[2].set_ha("right")
    ax.set_yticks([40, 60, 80, 100])
    ax.set_yticklabels(["40%", "60%", "80%", "100%"])
    ax.set_xlabel("How often the tool's answer is right")
    ax.set_ylabel("Correct final answers")
    ax.yaxis.grid(True, color=GRID, lw=1)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.text(0.0, 1.03, "Exploratory (post hoc)", transform=ax.transAxes, ha="left", va="bottom", fontweight="bold",
            color=INK, bbox=dict(boxstyle="round,pad=0.25", fc=GOLD, ec="none"))
    fig.subplots_adjust(left=0.15, right=0.80, top=0.90, bottom=0.16)
    fig.savefig(path)
    plt.close(fig)


# ---------------------------------------------------------------- figure 4: the checker
def fig4_data():
    c15 = "trackC/team_c15_summary.json"
    c4 = "trackC/team_c4_summary.json"
    fig = "checker"
    v = J(c15)["by_kind"]["fresh"]["by_team_model_variant"]["tool | olmo3-32b-instruct | plus_tool_log"]
    base = "by_kind/fresh/by_team_model_variant/tool | olmo3-32b-instruct | plus_tool_log"
    stopped = prop(fig, "Checker: wrong tool answers stopped", v, ["caught"], c15, f"{base}/caught", "F24")
    fa = prop(fig, "Checker: false alarms on good lookups", v, ["good_lookups", "false_alarms"], c15, f"{base}/good_lookups/false_alarms", "F24")
    r = J(c4)["by_team_model_variant"]
    rb = "by_team_model_variant/tool | olmo3-32b-instruct | {}/reviewer_alone/corrects_wrong_solver"
    alone = prop(fig, "Reviewer, answer only: corrected", r["tool | olmo3-32b-instruct | answer_only"], ["reviewer_alone", "corrects_wrong_solver"], c4, rb.format("answer_only"), "F18")
    log = prop(fig, "Reviewer shown the tool's log: corrected", r["tool | olmo3-32b-instruct | plus_tool_log"], ["reviewer_alone", "corrects_wrong_solver"], c4, rb.format("plus_tool_log"), "F18")
    return stopped, fa, alone, log


def fig_checker(path):
    stopped, fa, alone, log = fig4_data()
    labs = [x for x in ROWS if x["figure"] == "checker"]
    kn = lambda i: f"{labs[i]['k']} of {labs[i]['n']}"
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.0, 3.6), dpi=300, gridspec_kw={"width_ratios": [2.0, 1]})
    items = [("Independent checker", stopped, MAROON, kn(0)),
             ("Reviewer, answer only", alone, GOLD, kn(2)),
             ("Reviewer + tool's log", log, GOLD, kn(3))]
    for i, (name, (p, lo, hi), col, t) in enumerate(items):
        y = 2 - i
        a1.barh(y, p * 100, height=0.5, color=col, edgecolor=INK if col == GOLD else col, linewidth=0.8, zorder=2)
        a1.plot([lo * 100, hi * 100], [y, y], color=INK, lw=1.6, zorder=3)
        for cap in (lo, hi):
            a1.plot([cap * 100] * 2, [y - 0.1, y + 0.1], color=INK, lw=1.6, zorder=3)
        a1.text(106, y, t, va="center", ha="left", fontweight="bold", color=MAROON if col == MAROON else INK)
    a1.set_yticks([2, 1, 0])
    a1.set_yticklabels([x[0] for x in items])
    a1.set_xlim(0, 100)
    a1.set_ylim(-0.6, 2.9)
    a1.set_xticks([0, 50, 100])
    a1.set_xticklabels(["0%", "50%", "100%"])
    a1.set_title("Wrong tool answers stopped", loc="left", fontsize=FS, fontweight="bold")
    p, lo, hi = fa
    a2.bar(0, p * 100, width=0.5, color=MAROON, zorder=2)
    a2.plot([0, 0], [lo * 100, hi * 100], color=INK, lw=1.6, zorder=3)
    for cap in (lo, hi):
        a2.plot([-0.1, 0.1], [cap * 100] * 2, color=INK, lw=1.6, zorder=3)
    a2.text(0, hi * 100 + 4, kn(1), ha="center", va="bottom", fontweight="bold", color=MAROON)
    a2.set_xlim(-0.6, 0.6)
    a2.set_ylim(0, 60)
    a2.set_xticks([0])
    a2.set_xticklabels(["Checker"])
    a2.set_yticks([0, 25, 50])
    a2.set_yticklabels(["0%", "25%", "50%"])
    a2.set_title("False alarms", loc="left", fontsize=FS, fontweight="bold")
    for a in (a1, a2):
        a.tick_params(length=0)
        a.set_axisbelow(True)
    a1.xaxis.grid(True, color=GRID, lw=1)
    a2.yaxis.grid(True, color=GRID, lw=1)
    a1.spines["left"].set_visible(False)
    a2.spines["left"].set_visible(False)
    fig.subplots_adjust(left=0.30, right=0.98, top=0.88, bottom=0.12, wspace=0.95)
    fig.savefig(path)
    plt.close(fig)


FIGS = {"fig_tool_vs_user": fig_tool_vs_user, "fig_reasoning_vs_answer": fig_reasoning_vs_answer,
        "fig_tradeoff": fig_tradeoff, "fig_checker": fig_checker}


def plotted():
    """Every plotted number, as rows (builds the figures' data without drawing)."""
    ROWS.clear()
    fig1_data()
    fig2_data()
    fig3_data()
    fig4_data()
    return list(ROWS)


def main(out=OUT):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    ROWS.clear()
    for name, fn in FIGS.items():
        fn(out / f"{name}.png")
        print("wrote", out / f"{name}.png")
    for r in ROWS:
        print(r["figure"], "|", r["label"], "|", r["k"], r["n"], round(r["low"], 4), round(r["high"], 4))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    main(ap.parse_args().out)
