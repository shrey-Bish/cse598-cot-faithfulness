"""Track A figures #1 (pinned panel) and #4 of the figure plan (docs/FINDINGS.md), from the tracked
numbers-only summaries (no calls, no gitignored data):

  fig1_pinned_by_channel   Step 2b: Olmo 3 7B Think in the pinned Think format picks the hint letter,
                           per channel (F1, F2), beside the no-hint rate of the same letters; the panel
                           that goes next to the progress round's served panel (F9_expB_cue_by_channel)
  fig4_deletion            Step 4: deleting the reasoning's mentions vs a length-matched control vs the
                           unedited reasoning: the forced answer at the cut, the continuations, and
                           re-mentions after the cut (F7)

  python finetune/look/plot_figures.py      # -> results/summaries/trackA/figures/fig1_*.png/.svg, fig4_*

Style and colors are the progress deck's (progress/analyze_progress.py). Figure 4's arms: deleted blue,
unedited orange (the pair passes the colorblind checks), the control in the deck's neutral grey, and
every bar is labeled "X of Y", so no arm is told apart by color alone.
"""
import json
import sys
from collections import Counter
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import latest, wilson  # noqa: E402

SUM = CODE / "results" / "summaries" / "trackA"
FIGS = SUM / "figures"
C = {"private": "#2F6FD6", "final": "#E2622A", "cue": "#C02F79", "base": "#8893A6", "ink": "#1F2430",
     "muted": "#5B6474"}
ARM_COLOR = {"hint": C["private"], "control": C["base"], "unedited": C["final"]}
ARM_LABEL = {"hint": "mentions deleted", "control": "length-matched control", "unedited": "unedited"}


def style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.size": 14, "axes.titlesize": 16, "axes.labelsize": 13, "xtick.labelsize": 12, "ytick.labelsize": 13,
        "legend.fontsize": 12, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": C["muted"],
        "axes.labelcolor": C["ink"], "xtick.color": C["ink"], "ytick.color": C["ink"], "text.color": C["ink"],
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
        "svg.hashsalt": "trackA-figures", "font.family": "DejaVu Sans"})
    return plt


def finish(plt, fig, name, title, sources, **adjust):
    fig.suptitle(title, fontsize=17, x=0.02, ha="left", y=0.975)
    fig.text(0.02, 0.015, f"Source (in cot-disclosure/): {', '.join(sources)}  ·  script: finetune/look/plot_figures.py",
             fontsize=9, color=C["muted"], ha="left")
    fig.subplots_adjust(**adjust)
    FIGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGS / f"{name}.png", dpi=200, metadata={"Software": None})
    fig.savefig(FIGS / f"{name}.svg", metadata={"Date": None, "Creator": None})
    plt.close(fig)
    return FIGS / f"{name}.png"


def load(path):
    return [json.loads(line) for line in open(path)]


# ---------------------------------------------------------------- figure 1, pinned panel
def pinned_counts(rows=None):
    """[(label, k, n)] per channel (the current route's runs, as base_format.py --report counts them),
    and the no-hint runs that end on their question's hint letter."""
    from finetune import base_format as bf
    cur = bf.current(rows if rows is not None else load(SUM / "base_format_runs.jsonl"))
    out = []
    for label, cond, arm in (("user", "user", None), ("tool, pasted block", "tool_pasted", None),
                             ("tool, inserted turn", "tool_injected", None),
                             ("tool, inserted + declared", "tool_injected", "declared_functions")):
        rs = [r for r in cur if r["condition"] == cond and r["arm"] == arm]
        out.append((label, sum(r["parsed_letter"] == r["cue_letter"] for r in rs), len(rs)))
    hint = {r["item_id"]: r["cue_letter"] for r in cur if r["condition"] != "none"}
    nh = [r for r in cur if r["condition"] == "none"]
    return out, (sum(r["parsed_letter"] == hint.get(r["item_id"]) for r in nh), len(nh))


def fig1():
    import numpy as np
    plt = style()
    rows, (bk, bn) = pinned_counts()
    labels = [r[0] for r in rows] + ["no hint (the same letter)"]
    ks, ns = [r[1] for r in rows] + [bk], [r[2] for r in rows] + [bn]
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    y = np.arange(len(labels))[::-1]
    vals = [100 * k / n for k, n in zip(ks, ns)]
    cols = [C["cue"]] * len(rows) + [C["base"]]
    ax.barh(y, vals, height=0.56, color=cols)
    for yy, k, n, v in zip(y, ks, ns, vals):
        lo, hi = wilson(k, n)
        ax.errorbar(v, yy, xerr=[[v - 100 * lo], [100 * hi - v]], fmt="none", ecolor=C["ink"], elinewidth=1.2, capsize=3)
        ax.text(100 * hi + 1.5, yy, f"{k} of {n}", va="center", fontsize=12)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 105)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("% of runs ending on the hint letter (95% Wilson)")
    ax.tick_params(axis="y", length=0)
    return finish(plt, fig, "fig1_pinned_by_channel",
                  "Pinned format (Step 2b): Olmo 3 7B Think picks the hint letter\n"
                  "20 hinted Test 2 questions; user 1 run, each tool channel 3 runs per question",
                  ["results/summaries/trackA/base_format_runs.jsonl"], top=0.80, bottom=0.17, left=0.31, right=0.97)


# ---------------------------------------------------------------- figure 4, deletion
def deletion_counts(runs=None, remention=None):
    """{arm: {forced_own, forced_n, cont_own, cont_hint, cont_n, rementions, hint_ending}} from Step 4's
    summaries (the latest call per run_id)."""
    runs = latest(runs if runs is not None else load(SUM / "deletion_runs.jsonl"))
    rem = remention if remention is not None else load(SUM / "deletion_remention.jsonl")
    out = {}
    for arm in ("hint", "control", "unedited"):
        f = [r for r in runs if r["deletion_arm"] == arm and r["call"] == "forced" and r["status"] == "ok"]
        c = [r for r in runs if r["deletion_arm"] == arm and r["call"] == "continuation" and r["status"] == "ok"]
        oc = Counter(r["outcome"] for r in c)
        m = [r for r in rem if r["arm"] == arm]
        out[arm] = {"forced_own": sum(r["outcome"] == "own" for r in f), "forced_n": len(f), "cont_own": oc["own"],
                    "cont_hint": oc["hint"], "cont_n": len(c), "rementions": sum(r["mentions"] for r in m),
                    "hint_ending": len(m)}
    return out


def fig4():
    import numpy as np
    plt = style()
    d = deletion_counts()
    panels = [("Forced answer at the cut:\nback to the own answer", "forced_own", "forced_n", ("hint", "control")),
              ("Continuations:\nend on the own answer", "cont_own", "cont_n", ("hint", "control", "unedited")),
              ("Continuations:\nend on the hint letter", "cont_hint", "cont_n", ("hint", "control", "unedited")),
              ("Of those, the reasoning\nnames the hint again", "rementions", "hint_ending", ("hint", "control", "unedited"))]
    fig, axes = plt.subplots(1, 4, figsize=(12.8, 5.4), sharey=False)
    for ax, (title, k_key, n_key, arms) in zip(axes, panels):
        x = np.arange(len(arms))
        for xx, arm in zip(x, arms):
            k, n = d[arm][k_key], d[arm][n_key]
            v = 100 * k / n if n else 0
            lo, hi = wilson(k, n) if n else (0, 0)
            ax.bar(xx, v, width=0.62, color=ARM_COLOR[arm], label=ARM_LABEL[arm])
            ax.errorbar(xx, v, yerr=[[v - 100 * lo], [100 * hi - v]], fmt="none", ecolor=C["ink"], elinewidth=1.2, capsize=3)
            ax.text(xx, 100 * hi + 2, f"{k} of {n}", ha="center", va="bottom", fontsize=11)
        if "unedited" not in arms:
            ax.text(len(arms) - 0.4, 50, "unedited:\nthe hint letter\nby definition", ha="left", va="center",
                    fontsize=10, color=C["muted"])
            ax.set_xlim(-0.6, len(arms) + 0.9)
        ax.set_xticks([])
        ax.set_ylim(0, 112)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.set_title(title, fontsize=12, loc="left")
    axes[0].set_ylabel("% (95% Wilson)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=ARM_COLOR[a]) for a in ("hint", "control", "unedited")]
    fig.legend(handles, [ARM_LABEL[a] for a in ("hint", "control", "unedited")], loc="lower center", ncol=3,
               frameon=False, bbox_to_anchor=(0.5, 0.05))
    n_cases = d["hint"]["forced_n"]
    return finish(plt, fig, "fig4_deletion",
                  f"Step 4: deleting the reasoning's hint mentions moves the answer at the cut, not the final answer\n"
                  f"{n_cases} late takeovers on sure questions (9 questions), cut at the takeover; 3 continuations per case",
                  ["results/summaries/trackA/deletion_runs.jsonl", "deletion_remention.jsonl"],
                  top=0.76, bottom=0.2, left=0.06, right=0.99, wspace=0.28)


def main():
    for f in (fig1, fig4):
        print(f().relative_to(CODE))


if __name__ == "__main__":
    main()
