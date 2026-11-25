"""Final slide figures (docs/presentation/final/figures/; tests/test_deck_figures.py checks them against 02_NUMBERS.md).

Every plotted number is read from a tracked numbers-only summary under results/summaries/ (no calls, no gitignored
data). `plotted()` returns every (figure, label, k, n, interval, source file, key path) row, so a test can compare
them with docs/presentation/pack/02_NUMBERS.md. Intervals are 95% Wilson computed from k of n (checked against the
summaries' own stored Wilson bounds where they exist), except the trade-off's crossing interval, which is stored.

  python tools/deck/figures.py [--out DIR]      # -> DIR/fig_*.png (PNG at 2x the drawn size, 300 dpi; SVG too)

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
OUT = REPO / "docs" / "presentation" / "final" / "figures"
DPI = 600  # PNG: 2x the drawn size at 300 dpi

MAROON, GOLD, INK, GRID, MUTED = "#8C1D40", "#FFC627", "#191919", "#E8E8E8", "#6B6B6B"
FS = 14  # label size, pt, at the figure's drawn size (backups); the slide-4 strip uses 10 pt at 4.4 x 2.0 in

_have = {f.name for f in font_manager.fontManager.ttflist}
plt.rcParams.update({
    "font.family": "Arial" if "Arial" in _have else "DejaVu Sans", "font.size": FS, "text.color": INK,
    "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "axes.edgecolor": INK,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "axes.spines.top": False, "axes.spines.right": False, "svg.fonttype": "none"})

ROWS = []   # every plotted number
LABELS = []  # every number drawn as text: (figure, text, tokens that must be in 02)


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



def ivs(lo, hi):
    """The interval as 02_NUMBERS writes it."""
    return f"[{round(lo * 100)}, {round(hi * 100)}%]"


def row_(fig, label, kn, row, source, keypath, stored=None):
    k, n = kn
    return rec(fig, label, k, n, source, keypath, row, stored) and ROWS[-1].update(row=row) or ROWS[-1]


def lab(fig, text, *tokens):
    """Record a number drawn as text; tokens are the exact 02 strings that carry it."""
    LABELS.append({"figure": fig, "text": text, "tokens": list(tokens)})
    return text


def savefig(fig, out, name):
    fig.savefig(out / f"{name}.png", dpi=DPI)
    fig.savefig(out / f"{name}.svg")
    plt.close(fig)
    print("wrote", out / f"{name}.png")


TRACKB = "trackB/trackB_report.json"
B20 = "trackB/b20_report.json"
V = "voyager | {} | thinking=None"
# (short name, long name, own call?, source, path to the channels, tool key, 02 row)
MODELS = [
    ("Qwen3 30B Instruct", "Qwen3 30B Instruct", True, TRACKB, ["budget_32768", V.format("qwen3-30b-a3b-instruct-2507"), "channels"], "tool_real", "N140"),
    ("Qwen3 30B Thinking", "Qwen3 30B Thinking", True, TRACKB, ["budget_32768", V.format("qwen3-30b-a3b-thinking-2507"), "channels"], "tool_real", "N141"),
    ("Olmo 3 7B Think", "Olmo 3 7B Think", False, TRACKB, ["budget_32768", V.format("olmo3-7b-think"), "channels"], "tool_injected", "N142"),
    ("Qwen3 8B", "Qwen3-8B, thinking on", True, TRACKB, ["budget_32768", "sol_vllm | qwen3-8b | thinking=True", "channels"], "tool_real", "N143"),
    ("Gemma 4", "Gemma 4, thinking on", False, B20, ["gemma-4-26b-a4b-it", "settings", "on", "budget_32768", "secondary", "channels"], "tool_injected", "N144"),
    ("Nemotron 3 Nano", "Nemotron 3 Nano, thinking on", False, B20, ["nemotron-3-nano-30b-a3b", "settings", "on", "budget_32768", "secondary", "channels"], "tool_injected", "N145"),
    ("Granite 4.2", "Granite 4.2 8B, thinking on", True, B20, ["granite-4.2-8b", "settings", "on", "budget_32768", "secondary", "channels"], "tool_real", "N146"),
]


# the full backup figure adds the three thinking-off settings (02 rows N147-N149)
MODELS_OFF = [
    ("Qwen3 8B, off", "Qwen3-8B, thinking off", True, TRACKB, ["budget_32768", "sol_vllm | qwen3-8b | thinking=False", "channels"], "tool_real", "N147"),
    ("Gemma 4, off", "Gemma 4, thinking off", False, B20, ["gemma-4-26b-a4b-it", "settings", "off", "budget_32768", "secondary", "channels"], "tool_injected", "N148"),
    ("Nemotron 3 Nano, off", "Nemotron 3 Nano, thinking off", False, B20, ["nemotron-3-nano-30b-a3b", "settings", "off", "budget_32768", "secondary", "channels"], "tool_injected", "N149"),
]


def models_data(fig, models=None):
    out = []
    for short, long_, own, src, path, tk, rid in (models or MODELS):
        ch = get(J(src), path)
        kp = "/".join(path)
        u = prop(fig, f"{long_}: user", ch, ["user", "following"], src, f"{kp}/user/following", rid)
        ROWS[-1]["row"] = rid
        t = prop(fig, f"{long_}: tool", ch, [tk, "following"], src, f"{kp}/{tk}/following", rid)
        ROWS[-1]["row"] = rid
        ku, kt = ROWS[-2], ROWS[-1]
        out.append({"short": short, "long": long_, "own": own, "user": u, "tool": t,
                    "ukn": (ku["k"], ku["n"]), "tkn": (kt["k"], kt["n"])})
    return out


def dots(ax, data, y_of, ms, lw_i, lw_l, kn_fs, ukn_x, tkn_x, kn_sep=False):
    for r in data:
        y = y_of(r)
        (pu, ulo, uhi), (pt, tlo, thi) = r["user"], r["tool"]
        ax.plot([pu * 100, pt * 100], [y, y], color=GRID, lw=lw_l, zorder=1)
        ax.plot([ulo * 100, uhi * 100], [y, y], color=GOLD, lw=lw_i, solid_capstyle="butt", zorder=2)
        ax.plot([tlo * 100, thi * 100], [y, y], color=MAROON, lw=lw_i, solid_capstyle="butt", zorder=2)
        ax.scatter([pu * 100], [y], s=ms, color=GOLD, edgecolor=INK, linewidth=0.8, zorder=4, clip_on=False)
        mk = "o" if r["own"] else "D"
        ax.scatter([pt * 100], [y], s=ms if r["own"] else ms * 0.75, marker=mk, color=MAROON, edgecolor=MAROON,
                   zorder=4, clip_on=False)


# ---------------------------------------------------------------- figure 1: slide 4's strip, one row per model
def fig_across_models(out):
    fig_id = "across_models"
    data = models_data(fig_id)
    data.sort(key=lambda r: -r["tool"][0])
    n = len(data)
    fig = plt.figure(figsize=(4.4, 2.0))
    ax = fig.add_axes([1.62 / 4.4, 0.27 / 2.0, 1.40 / 4.4, 1.43 / 2.0])   # room for 11.5 pt model names
    dots(ax, data, lambda r: n - 1 - data.index(r), 24, 2.2, 1.0, 10, 0, 0)
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xticks([0, 50, 100])
    ax.set_xticklabels(["0%", "50%", "100%"], fontsize=10)
    ax.set_yticks(range(n))
    ax.set_yticklabels([r["short"] for r in data][::-1], fontsize=11.5)
    ax.xaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0, pad=3)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    tr = ax.get_yaxis_transform()
    for r in data:
        y = n - 1 - data.index(r)
        ax.text(1.05, y, lab(fig_id, f"{r['ukn'][0]}/{r['ukn'][1]}", f"{r['ukn'][0]} of {r['ukn'][1]}"),
                va="center", ha="left", fontsize=10, color=INK, transform=tr)
        ax.text(1.42, y, lab(fig_id, f"{r['tkn'][0]}/{r['tkn'][1]}", f"{r['tkn'][0]} of {r['tkn'][1]}"),
                va="center", ha="left", fontsize=10, color=MAROON, fontweight="bold", transform=tr)
    ax.scatter([], [], s=24, color=GOLD, edgecolor=INK, linewidth=0.8, label="user")
    ax.scatter([], [], s=24, color=MAROON, label="tool")
    ax.legend(loc="lower left", bbox_to_anchor=(-0.05, 1.0), ncol=2, frameon=False, fontsize=10,
              handletextpad=0.2, columnspacing=1.0, borderaxespad=0.1)
    savefig(fig, out, "fig_across_models")


# ---------------------------------------------------------------- figure 2: the 02 rows, backup
def fig_tool_vs_user_full(out):
    fig_id = "tool_vs_user_full"
    data = models_data(fig_id, MODELS + MODELS_OFF)
    data.sort(key=lambda r: -r["tool"][0])
    n = len(data)
    fig = plt.figure(figsize=(8.2, 5.0))
    ax = fig.add_axes([0.37, 0.31, 0.28, 0.60])
    dots(ax, data, lambda r: n - 1 - data.index(r), 110, 3, 1.2, FS, 0, 0)
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xticks([0, 50, 100])
    ax.set_xticklabels(["0%", "50%", "100%"])
    ax.set_yticks(range(n))
    ax.set_yticklabels([r["long"] for r in data][::-1])
    ax.set_xlabel("Runs that followed the wrong letter")
    ax.xaxis.grid(True, color=GRID, lw=1)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.spines["left"].set_visible(False)
    tr = ax.get_yaxis_transform()
    for r in data:
        y = n - 1 - data.index(r)
        ax.text(1.05, y, lab(fig_id, f"{r['ukn'][0]}/{r['ukn'][1]}", f"{r['ukn'][0]} of {r['ukn'][1]}"),
                va="center", ha="left", transform=tr)
        ax.text(1.50, y, lab(fig_id, f"{r['tkn'][0]}/{r['tkn'][1]}", f"{r['tkn'][0]} of {r['tkn'][1]}"),
                va="center", ha="left", color=MAROON, fontweight="bold", transform=tr)
    ax.text(1.05, n - 0.4, "User", ha="left", va="bottom", fontweight="bold", transform=tr)
    ax.text(1.50, n - 0.4, "Tool", ha="left", va="bottom", color=MAROON, fontweight="bold", transform=tr)
    ax.scatter([], [], s=110, color=GOLD, edgecolor=INK, label="user")
    ax.scatter([], [], s=110, color=MAROON, label="tool: the model's own call")
    ax.scatter([], [], s=80, marker="D", color=MAROON, label="tool: inserted tool turn")
    fig.legend(loc="lower left", bbox_to_anchor=(0.02, 0.07), ncol=3, frameon=False, handletextpad=0.3,
               columnspacing=1.2, fontsize=12)
    fig.text(0.02, 0.02, "gpt-oss-20b: tested, reported without a decision; not shown.", fontsize=12, color=MUTED)
    savefig(fig, out, "fig_tool_vs_user_full")


# ---------------------------------------------------------------- figure 3: reasoning vs answer
def fig_reasoning_vs_answer(out):
    fig_id = "reasoning_vs_answer"
    t = J(TRACKB)["budget_32768"]
    q8 = t["sol_vllm | qwen3-8b | thinking=True"]["channels"]["tool_real"]
    q30 = t["voyager | qwen3-30b-a3b-thinking-2507 | thinking=None"]["channels"]["tool_real"]
    q8p = "budget_32768/sol_vllm | qwen3-8b | thinking=True/channels/tool_real"
    q30p = "budget_32768/voyager | qwen3-30b-a3b-thinking-2507 | thinking=None/channels/tool_real"
    g = J(B20)["gemma-4-26b-a4b-it"]["settings"]["off"]["budget_32768"]["secondary"]["channels"]["tool_injected"]
    gp = "gemma-4-26b-a4b-it/settings/off/budget_32768/secondary/channels/tool_injected/mention_final"

    def p(label, e, key, src, kp, rid):
        v = prop(fig_id, label, e, [key], src, f"{kp}/{key}", rid)
        ROWS[-1]["row"] = rid
        return v, (ROWS[-1]["k"], ROWS[-1]["n"])
    rows = [
        {"name": "Qwen3-8B, thinking on",
         "priv": p("Qwen3-8B on: reasoning names the tool", q8, "mention_private_when_called", TRACKB, q8p, "N134"),
         "final": p("Qwen3-8B on: answer names the tool", q8, "mention_final_when_followed", TRACKB, q8p, "N135")},
        {"name": "Qwen3 30B Thinking",
         "priv": p("Qwen3 30B Thinking: reasoning names the tool", q30, "mention_private_when_called", TRACKB, q30p, "N133"),
         "final": p("Qwen3 30B Thinking: answer names the tool", q30, "mention_final_when_followed", TRACKB, q30p, "N133")},
        {"name": "Gemma 4, thinking off", "priv": None,
         "final": p("Gemma 4 off: answer names the tool", g, "mention_final", B20, gp.rsplit("/", 1)[0], "N136")}]
    n = len(rows)
    fig = plt.figure(figsize=(8.2, 4.8))
    ax = fig.add_axes([0.27, 0.34, 0.45, 0.63])
    bh = 0.34
    ticks = []
    for i, r in enumerate(rows):
        yc = (n - 1 - i) * 1.25
        ticks.append(yc)
        for key, col in (("priv", MAROON), ("final", GOLD)):
            y = yc + 0.2 if key == "priv" else yc - 0.2
            v = r[key]
            if v is None:
                ax.text(2, y + 0.2, "no private reasoning\n(thinking off)", va="center", ha="left", color=MUTED, style="italic")
                continue
            (pp, lo, hi), (k, nn) = v
            ax.barh(y, pp * 100, height=bh, color=col, edgecolor=INK if col == GOLD else col, linewidth=0.8, zorder=2)
            ax.plot([lo * 100, hi * 100], [y, y], color=INK, lw=1.6, zorder=3)
            for cap in (lo, hi):
                ax.plot([cap * 100] * 2, [y - 0.07, y + 0.07], color=INK, lw=1.6, zorder=3)
            ax.text(105, y, lab(fig_id, f"{k} of {nn}", f"{k} of {nn}"), va="center", ha="left",
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
    ax.bar(0, 0, color=MAROON, label="private reasoning")
    ax.bar(0, 0, color=GOLD, edgecolor=INK, label="final answer")
    fig.legend(loc="lower left", bbox_to_anchor=(0.02, 0.095), ncol=2, frameon=False, handlelength=1.2,
               columnspacing=1.2)
    fig.text(0.02, 0.015, "Reasoning: of the runs that called the tool.  Answer: of the runs that followed it\n"
             "(Gemma 4: all answered runs).", fontsize=11, color=MUTED, va="bottom")
    savefig(fig, out, "fig_reasoning_vs_answer")


# ---------------------------------------------------------------- figure 4: trade-off (exploratory)
def fig_tradeoff(out):
    fig_id = "tradeoff"
    src = "trackA/gpu/a39/tradeoff_e2.json"
    c = J(src)["crossings"]["answered"]["a40"]
    kp = "crossings/answered/a40"
    pts = {}
    for side, name in (("a", "Consistency training"), ("b", "One-line instruction")):
        s = c[side]
        w = rec(fig_id, f"{name}: correct when the tool is wrong (left end, unlabelled)", *s["a_W_kn"], src, f"{kp}/{side}/a_W_kn", "none")
        ROWS[-1]["row"] = None
        r_ = rec(fig_id, f"{name}: correct when the tool is right (right end)", *s["a_C_kn"], src, f"{kp}/{side}/a_C_kn", "N69")
        ROWS[-1]["row"] = "N69"
        for e in ROWS[-2:]:
            e["low"] = e["high"] = None  # no interval is drawn on these points
        pts[name] = {"W": w, "C": r_, "Ckn": tuple(s["a_C_kn"])}
    pstar = c["p_star"]
    lo, hi = c["interval"]
    ROWS.append({"figure": fig_id, "label": "crossover share", "k": None, "n": None, "low": lo, "high": hi,
                 "source": src, "key_path": f"{kp}/p_star", "finding": "N81", "row": "N81", "value": pstar})
    fig = plt.figure(figsize=(7.2, 4.5))
    ax = fig.add_axes([0.12, 0.15, 0.62, 0.66])
    spec = {"Consistency training": MAROON, "One-line instruction": INK}
    for name, col in spec.items():
        w, c_ = pts[name]["W"], pts[name]["C"]
        ax.plot([0, 100], [w[0] * 100, c_[0] * 100], color=col, lw=3, zorder=3)
        ax.scatter([0, 100], [w[0] * 100, c_[0] * 100], s=60, color=col, zorder=4, clip_on=False)
        k, nn = pts[name]["Ckn"]
        ax.text(103, c_[0] * 100, lab(fig_id, f"{k} of {nn}", f"{k} of {nn}"), color=col, ha="left", va="center",
                clip_on=False)
    wc, cc = pts["Consistency training"]["W"][0], pts["Consistency training"]["C"][0]
    yc = (wc + pstar * (cc - wc)) * 100
    ax.axvspan(lo * 100, hi * 100, color=GRID, zorder=0)
    ax.plot([pstar * 100], [yc], marker="o", ms=11, mfc="white", mec=INK, mew=2, zorder=5)
    ax.annotate(lab(fig_id, "tool right about 36% of the time [22%, 50%]", "0.36", "[0.22, 0.50]").replace(" of the time ", " of the time\n"),
                xy=(pstar * 100, yc), xytext=(45, 46), ha="left", va="center", fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.4, shrinkA=2, shrinkB=7))
    ax.text(10, 94, "One-line instruction", color=INK, fontweight="bold", ha="left", va="center")
    ax.text(40, 74, "Consistency training", color=MAROON, fontweight="bold", ha="left", va="center")
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
    fig.text(0.12, 0.955, "Exploratory (post hoc)", ha="left", va="center", fontweight="bold", color=INK,
             bbox=dict(boxstyle="round,pad=0.25", fc=GOLD, ec="none"))
    sub = lab(fig_id, "Wrong hints followed: 84 of 694 vs 237 of 713", "84 of 694", "237 of 713")
    fig.text(0.12, 0.865, sub, ha="left", va="center", fontsize=12, color=MUTED)
    savefig(fig, out, "fig_tradeoff")


# ---------------------------------------------------------------- figure 5: the checker
def fig_checker(out):
    fig_id = "checker"
    c15 = "trackC/c15_summary.json"
    base = "c_frozen_rule/olmo3-32b-instruct/plus_tool_log"
    d = get(J(c15), base.split("/"))
    st = prop(fig_id, "Checker: wrong tool answers stopped", d, ["bad_lookups", "checker_pipeline_caught"], c15, f"{base}/bad_lookups/checker_pipeline_caught", "N137")
    ROWS[-1]["row"] = "N137"
    fa = prop(fig_id, "Checker: false alarms on good lookups", d, ["good_lookups", "checker_pipeline_false_alarms"], c15, f"{base}/good_lookups/checker_pipeline_false_alarms", "N138")
    ROWS[-1]["row"] = "N138"
    kst, kfa = (ROWS[-2]["k"], ROWS[-2]["n"]), (ROWS[-1]["k"], ROWS[-1]["n"])
    c4 = "trackC/team_c4_summary.json"
    r = J(c4)["by_team_model_variant"]
    rb = "by_team_model_variant/tool | olmo3-32b-instruct | {}/reviewer_alone/corrects_wrong_solver"
    rev = []
    for var, name in (("answer_only", "Reviewer, answer only"), ("plus_tool_log", "Reviewer + tool's log")):
        e = r[f"tool | olmo3-32b-instruct | {var}"]["reviewer_alone"]["corrects_wrong_solver"]
        ROWS.append({"figure": fig_id, "label": f"{name}: corrected", "k": e["k"], "n": e["n"], "low": None, "high": None,
                     "source": c4, "key_path": rb.format(var), "finding": "N48", "row": "N48"})
        rev.append((name, e["k"] / e["n"], (e["k"], e["n"])))
    fig = plt.figure(figsize=(8.0, 3.9))
    a1 = fig.add_axes([0.28, 0.20, 0.46 * 0.62, 0.66])
    a2 = fig.add_axes([0.80, 0.20, 0.12, 0.66])
    items = [("Independent checker", st, MAROON, kst)] + [(nm, (p, None, None), GOLD, kn) for nm, p, kn in rev]
    for i, (name, (p, lo, hi), col, kn) in enumerate(items):
        y = 2 - i
        a1.barh(y, p * 100, height=0.5, color=col, edgecolor=INK if col == GOLD else col, linewidth=0.8, zorder=2)
        if lo is not None:
            a1.plot([lo * 100, hi * 100], [y, y], color=INK, lw=1.6, zorder=3)
            for cap in (lo, hi):
                a1.plot([cap * 100] * 2, [y - 0.1, y + 0.1], color=INK, lw=1.6, zorder=3)
        a1.text(106, y, lab(fig_id, f"{kn[0]} of {kn[1]}", f"{kn[0]} of {kn[1]}"), va="center", ha="left",
                fontweight="bold", color=MAROON if col == MAROON else INK, clip_on=False)
    a1.set_yticks([2, 1, 0])
    a1.set_yticklabels([x[0] for x in items])
    a1.set_xlim(0, 100)
    a1.set_ylim(-0.6, 2.7)
    a1.set_xticks([0, 50, 100])
    a1.set_xticklabels(["0%", "50%", "100%"])
    a1.set_title("Wrong tool answers stopped", loc="left", fontsize=FS, fontweight="bold")
    p, lo, hi = fa
    a2.bar(0, p * 100, width=0.5, color=MAROON, zorder=2)
    a2.plot([0, 0], [lo * 100, hi * 100], color=INK, lw=1.6, zorder=3)
    for cap in (lo, hi):
        a2.plot([-0.1, 0.1], [cap * 100] * 2, color=INK, lw=1.6, zorder=3)
    a2.text(0, hi * 100 + 4, lab(fig_id, f"{kfa[0]} of {kfa[1]}", f"{kfa[0]} of {kfa[1]}"), ha="center", va="bottom",
            fontweight="bold", color=MAROON)
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
        a.spines["left"].set_visible(False)
    a1.xaxis.grid(True, color=GRID, lw=1)
    a2.yaxis.grid(True, color=GRID, lw=1)
    fig.text(0.02, 0.025, "checker: 100 fresh items; reviewer: the first test's 73 cases", fontsize=12, color=MUTED)
    savefig(fig, out, "fig_checker")


FIGS = {"fig_across_models": fig_across_models, "fig_tool_vs_user_full": fig_tool_vs_user_full,
        "fig_reasoning_vs_answer": fig_reasoning_vs_answer, "fig_tradeoff": fig_tradeoff, "fig_checker": fig_checker}


def _build(out):
    ROWS.clear()
    LABELS.clear()
    for fn in FIGS.values():
        fn(out)


def plotted():
    """Every plotted number: dicts with figure, label, k, n, low, high (None when not drawn), row (02 id)."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _build(Path(d))
    return list(ROWS)


def labels():
    """Every number drawn as text: dicts with figure, text, tokens (exact 02 strings that carry it).
    Axis tick labels (0%, 50%, 100%, ...) are scale marks, not data, and are not listed."""
    plotted()
    return list(LABELS)


def main(out=OUT):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    _build(out)
    for r in ROWS:
        print(r["figure"], "|", r["label"], "|", r["k"], r["n"], r["row"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    main(ap.parse_args().out)
