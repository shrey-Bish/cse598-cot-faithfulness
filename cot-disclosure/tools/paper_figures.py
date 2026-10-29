"""Paper figures for the two threads, from the tracked numbers-only summaries (no calls, no gitignored data):

  reviewer_by_prompt     thread 2 (FINDINGS F18, F19, F21): the reviewer alone corrects a wrong solver
                         answer after a bad lookup, per reviewer model and what it sees, under C4's prompt,
                         C9's (+ "The tool's answer may be wrong; check it independently.") and C10's
                         (commit first; no answer-only bar: its first turn is C9's answer-only review);
                         X of 73 with 95% Wilson intervals
  readout_by_layer       thread 1 (F11): the share of the drop in hint-token restoration at each of the
                         32 layers at cut (ii), mean and 95% bootstrap over questions; full-attention
                         layers apart from sliding ones
  taught_loss            thread 1 (F20): each trained version's validation loss minus base, relative to
                         base, on the taught tokens, the taught tokens without the opener, and the rest
                         (epoch 2, 95% bootstrap clustered by question)

  python tools/paper_figures.py          # -> docs/paper/figures/<name>.png, .svg and .csv

Each figure has a CSV beside it with every plotted number (the table view). Colors: the first three
slots of a validated categorical palette (blue, orange, aqua; colorblind-safe as a set); full-attention
layers blue, sliding layers a neutral grey.
"""
import csv
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "progress"))

from common import wilson  # noqa: E402

SUM = CODE / "results" / "summaries"
OUT = CODE.parent / "docs" / "paper" / "figures"
INK, MUTED, GRID, SURFACE, NEUTRAL = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb", "#a3a29c"
SERIES = ("#2a78d6", "#eb6834", "#1baf7a")
REVIEWERS = (("olmo3-32b-instruct", "Olmo 3.1 32B Instruct"), ("qwen3-30b-a3b-instruct-2507", "Qwen3 30B Instruct"))
VARIANTS = (("answer_only", "answer only"), ("plus_private", "+ private reasoning"), ("plus_tool_log", "+ tool log"))
RUNS = (("team_c4", "C4: original prompt"), ("team_c9", "C9: + check-the-tool sentence"),
        ("team_c10", "C10: own answer first"))
VERSIONS = (("lora", "LoRA"), ("lora_tags", "LoRA + tags"), ("lora_attn3", "LoRA, layers 15/19/23"), ("tags", "tags"))
GROUPS = (("taught", "taught tokens"), ("taught_no_opener", "taught, without the opener"), ("not_taught", "the rest"))


# ---------------------------------------------------------------- data
def reviewer_rows(summaries=SUM / "trackC"):
    """[{reviewer, variant, run, k, n, rate, low, high}] for the reviewer correcting after bad lookups."""
    rows = []
    for log, run in RUNS:
        res = json.loads((Path(summaries) / f"{log}_summary.json").read_text())["by_team_model_variant"]
        for model, name in REVIEWERS:
            for v, vname in VARIANTS:
                e = res.get(f"tool | {model} | {v}")
                if not e:
                    continue
                c = e["bad_lookups"]["reviewer_alone"]["corrects_wrong_solver"]
                lo, hi = wilson(c["k"], c["n"])
                rows.append({"reviewer": name, "variant": vname, "run": run, "k": c["k"], "n": c["n"],
                             "rate": c["k"] / c["n"], "low": lo, "high": hi})
    return rows


def layer_rows(path=SUM / "trackA" / "step10_handoff.json", cut="ii"):
    """[{layer, kind, share, low, high, questions, cuts}] at the cut, all cuts pooled."""
    h = json.loads(Path(path).read_text())["handoff"]
    full, a = set(h["full_attention_layers"]), h["by_cut_type"][cut]["all"]
    return [{"layer": i, "kind": "full attention" if i in full else "sliding window", "share": e["mean"],
             "low": e["low"], "high": e["high"], "questions": e["questions"], "cuts": a["cuts"]}
            for i, e in enumerate(a["drop_by_layer"])]


def loss_rows(path=SUM / "trackA" / "val_loss_report.json", epoch=2):
    """[{version, group, relative, low, high, base, tokens, items}]: minus base relative to base."""
    mb = json.loads(Path(path).read_text())["minus_base"]
    rows = []
    for v, vname in VERSIONS:
        for g, gname in GROUPS:
            e = mb[f"{v}/epoch{epoch}"][g]
            rows.append({"version": vname, "group": gname, "relative": e["relative"],
                         "low": e["interval"][0] / e["base"], "high": e["interval"][1] / e["base"],
                         "base": e["base"], "tokens": e["tokens"], "items": e["items"]})
    return rows


# ---------------------------------------------------------------- drawing
def style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
                         "font.size": 9, "axes.edgecolor": NEUTRAL, "axes.labelcolor": MUTED, "text.color": INK,
                         "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID,
                         "grid.linewidth": 0.6, "axes.axisbelow": True, "legend.frameon": False,
                         "svg.fonttype": "none"})
    return plt


def grouped(ax, cats, series, value, err, colors, width=0.26):
    """Grouped bars with error bars; a missing value is left out (no bar)."""
    for j, (s, color) in enumerate(zip(series, colors)):
        labeled = False
        for i, c in enumerate(cats):
            v = value(c, s)
            if v is None:
                continue
            x = i + (j - (len(series) - 1) / 2) * width
            ax.bar(x, v, width * 0.92, color=color, edgecolor=SURFACE, linewidth=1.2, label=None if labeled else s)
            labeled = True
            lo, hi = err(c, s)
            ax.plot([x, x], [lo, hi], color=MUTED, linewidth=1.0, solid_capstyle="butt")
    ax.set_xticks(range(len(cats)), cats)


def save(fig, name, rows, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(out / f"{name}.{ext}", dpi=200, bbox_inches="tight")
    with open(out / f"{name}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return [out / f"{name}.{ext}" for ext in ("png", "svg", "csv")]


def fig_reviewer(out=OUT, summaries=SUM / "trackC"):
    plt = style()
    rows = reviewer_rows(summaries)
    at = {(r["reviewer"], r["variant"], r["run"]): r for r in rows}
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
    cats, runs = [v for _, v in VARIANTS], [r for _, r in RUNS]
    for ax, (_, name) in zip(axes, REVIEWERS):
        grouped(ax, cats, runs, lambda c, s: (at[(name, c, s)]["rate"] * 100 if (name, c, s) in at else None),
                lambda c, s: (at[(name, c, s)]["low"] * 100, at[(name, c, s)]["high"] * 100), SERIES)
        ax.set_title(name, fontsize=9.5, color=INK, loc="left")
        ax.set_ylim(0, 100)
        ax.set_xticks(range(len(cats)), [c.replace("+ private ", "+ private\n") for c in cats])
    axes[0].set_ylabel("corrects the wrong solver answer (%)")
    axes[0].legend(loc="upper center", bbox_to_anchor=(1.05, -0.2), ncol=3, fontsize=8.5)
    fig.suptitle("The reviewer alone after a bad lookup: 73 wrong solver answers on 25 questions "
                 "(bars: the share corrected; lines: 95% Wilson)", fontsize=9, color=MUTED, x=0.01, ha="left")
    paths = save(fig, "reviewer_by_prompt", rows, out)
    plt.close(fig)
    return paths


def fig_layers(out=OUT, path=SUM / "trackA" / "step10_handoff.json"):
    plt = style()
    rows = layer_rows(path)
    fig, ax = plt.subplots(figsize=(9, 3.2))
    kinds = {"full attention": SERIES[0], "sliding window": NEUTRAL}
    for kind, color in kinds.items():
        sel = [r for r in rows if r["kind"] == kind]
        ax.bar([r["layer"] for r in sel], [r["share"] for r in sel], 0.8, color=color, edgecolor=SURFACE,
               linewidth=1.0, label=kind)
        for r in sel:
            ax.plot([r["layer"]] * 2, [r["low"], r["high"]], color=MUTED, linewidth=0.9)
    for r in rows:
        if r["layer"] in (15, 19, 23):
            ax.annotate(f"L{r['layer']}: {r['share']:.2f}", (r["layer"], r["high"]), xytext=(0, 3),
                        textcoords="offset points", ha="center", fontsize=8, color=INK)
    ax.axhline(0, color=NEUTRAL, linewidth=0.8)
    ax.set_xticks(range(0, 32, 2))
    ax.set_xlabel("layer")
    ax.set_ylabel("share of the drop at the hint's tokens")
    ax.legend(loc="upper left", fontsize=8.5)
    q, n = rows[0]["questions"], rows[0]["cuts"]
    ax.set_title(f"Where the hint's effect leaves its tokens, at the takeover (cut (ii); {n} cuts, {q} questions; "
                 "95% bootstrap over questions)", fontsize=9, color=MUTED, loc="left")
    paths = save(fig, "readout_by_layer", rows, out)
    plt.close(fig)
    return paths


def fig_loss(out=OUT, path=SUM / "trackA" / "val_loss_report.json"):
    plt = style()
    rows = loss_rows(path)
    at = {(r["version"], r["group"]): r for r in rows}
    fig, ax = plt.subplots(figsize=(8, 3.4))
    cats, groups = [v for _, v in VERSIONS], [g for _, g in GROUPS]
    grouped(ax, cats, groups, lambda c, s: at[(c, s)]["relative"] * 100,
            lambda c, s: (at[(c, s)]["low"] * 100, at[(c, s)]["high"] * 100), SERIES)
    ax.axhline(0, color=NEUTRAL, linewidth=0.8)
    ax.set_ylabel("validation loss minus base (% of base)")
    ax.legend(loc="lower right", fontsize=8.5)
    ax.set_title("Training against the untrained model, epoch 2 (156 held-out examples on 34 questions; "
                 "95% bootstrap clustered by question)", fontsize=9, color=MUTED, loc="left")
    paths = save(fig, "taught_loss", rows, out)
    plt.close(fig)
    return paths


def main():
    for f in (fig_reviewer, fig_layers, fig_loss):
        for p in f():
            print(p.relative_to(CODE.parent))


if __name__ == "__main__":
    main()
