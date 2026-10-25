"""Track A, step 3: figures from results/trackA/takeover.jsonl (no calls).

  python finetune/look/plot_takeover.py --dry-run     # which figures, from how many runs
  python finetune/look/plot_takeover.py               # -> results/trackA/figures/takeover_*.png and .svg

  takeover_curves_<channel>_<outcome>_<page>.png  one panel per run: the hint letter's and the
        model's own answer's probability after each sentence, the takeover point, and the
        sentences that mention the hint (keyword count)
  takeover_points.png      each followed run's takeover point, as a share of its reasoning; filled
                           when a mention came in the takeover sentence or the 2 before
  takeover_mean_curves.png the hint letter's mean probability through the reasoning (20 bins),
                           followed vs resisted vs no hint, per channel
A probability outside the top 10 is drawn at the 10th probability (its upper bound).
"""
import argparse
import math
import statistics
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import load  # noqa: E402
from finetune.look import takeover as tk  # noqa: E402

FIGS = CODE / "results" / "trackA" / "figures"
C = {"private": "#2F6FD6", "final": "#E2622A", "cue": "#C02F79", "base": "#8893A6",
     "correct": "#14826A", "damage": "#9C6C06", "ink": "#1F2430", "muted": "#5B6474", "grid": "#E6E8EE"}
KIND_COLOR = {"followed": C["cue"], "resisted": C["private"], "no hint": C["base"]}
plt.rcParams.update({
    "font.size": 12, "axes.titlesize": 12, "axes.labelsize": 12, "xtick.labelsize": 10, "ytick.labelsize": 10,
    "legend.fontsize": 11, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": C["muted"],
    "axes.labelcolor": C["ink"], "xtick.color": C["ink"], "ytick.color": C["ink"], "text.color": C["ink"],
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "svg.hashsalt": "trackA-takeover", "font.family": "DejaVu Sans",
})
PER_PAGE = 24
BINS = 20
SCRIPT = "finetune/look/plot_takeover.py"


def series(r, key):
    """A probability series with letters outside the top 10 drawn at the 10th probability."""
    return [p if p is not None else (c["floor"] or 0.0) for p, c in zip(r[key], r["curve"])]


def xs(r):
    """Each probe's position as a share of the reasoning (dense or adaptive probes)."""
    n = max(1, r["n_sentences"])
    return [p["k"] / n for p in r["curve"]]


def finish(fig, path, title, n_runs):
    fig.suptitle(title, fontsize=15, x=0.02, ha="left", y=0.985)
    fig.text(0.02, 0.008, f"Olmo 3 7B Think on Voyager, Step 2b runs ({n_runs} probed). Mentions are keyword counts "
             f"(detect.py). A letter outside the top 10 is drawn at the 10th probability. Source: "
             f"results/trackA/takeover.jsonl · script: {SCRIPT}", fontsize=8, color=C["muted"], ha="left")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".png"), dpi=160, metadata={"Software": None})
    fig.savefig(path.with_suffix(".svg"), metadata={"Date": None, "Creator": None})
    plt.close(fig)
    return path.with_suffix(".png")


def curve_pages(rows):
    """{(channel label, outcome): runs}, in report order."""
    pages = {}
    for cond, arm, label in tk.GROUPS + [("none", None, "no hint")]:
        for kind in ("followed", "resisted", "no hint"):
            rs = [r for r in rows if r["condition"] == cond and r.get("arm") == arm and r["kind"] == kind]
            if rs:
                pages[(label, kind)] = sorted(rs, key=lambda r: (r["item_id"], r["repeat"]))
    return pages


def slug(label, kind, page):
    return "takeover_curves_" + "_".join(s.replace(",", "").replace("+ ", "").replace(" ", "-")
                                         for s in (label, kind)) + f"_{page + 1}"


def plot_curves(rows, figs=FIGS):
    out = []
    for (label, kind), rs in curve_pages(rows).items():
        for page in range(math.ceil(len(rs) / PER_PAGE)):
            chunk = rs[page * PER_PAGE:(page + 1) * PER_PAGE]
            ncols = 6
            nrows = max(1, math.ceil(len(chunk) / ncols))
            fig, axes = plt.subplots(nrows, ncols, figsize=(16, 9), sharex=True, sharey=True, squeeze=False)
            for ax, r in zip(axes.flat, chunk):
                x = xs(r)
                ax.plot(x, series(r, "hint_prob"), color=C["cue"], lw=2, label=f"hint letter")
                if r.get("own_letter"):
                    ax.plot(x, series(r, "own_prob"), color=C["correct"], lw=2, label="own no-hint answer")
                for i, m in enumerate(r.get("mentions") or []):
                    if m:
                        ax.plot([(i + 1) / max(1, r["n_sentences"])] * 2, [-0.08, -0.02], color=C["cue"], lw=1,
                                clip_on=False)
                if r.get("takeover_k") is not None:
                    ax.axvline(r["takeover_frac"], color=C["ink"], lw=1, ls="--")
                ax.set_title(f"Q{r['item_id']} run {r['repeat']} · {r['n_sentences']} sentences\n"
                             f"hint {r['hint_letter']} · own {r['own_letter'] or '—'} · final {r['final_letter']}",
                             fontsize=8, loc="left")
                ax.set_ylim(-0.1, 1.02)
                ax.set_yticks([0, 0.5, 1])
                ax.grid(axis="y", color=C["grid"], lw=0.8)
            for ax in list(axes.flat)[len(chunk):]:
                ax.axis("off")
            for ax in axes[-1]:
                ax.set_xlabel("share of the reasoning", fontsize=9)
            handles = [plt.Line2D([], [], color=C["cue"], lw=2), plt.Line2D([], [], color=C["correct"], lw=2),
                       plt.Line2D([], [], color=C["ink"], lw=1, ls="--"),
                       plt.Line2D([], [], color=C["cue"], lw=1, marker="|", ls="none", markersize=8)]
            fig.legend(handles, ["hint letter", "own no-hint answer", "takeover point", "sentence mentions the hint"],
                       loc="upper left", ncol=4, frameon=False, bbox_to_anchor=(0.015, 0.955))
            fig.subplots_adjust(top=0.85, bottom=0.08, left=0.04, right=0.99, hspace=0.75, wspace=0.12)
            pages = math.ceil(len(rs) / PER_PAGE)
            out.append(finish(fig, figs / slug(label, kind, page),
                              f"Answer probability after each sentence: {label} hint, {kind} runs"
                              + (f" ({page + 1} of {pages})" if pages > 1 else ""), len(rows)))
    return out


def plot_points(rows, figs=FIGS):
    groups = [(label, [r for r in rows if r["condition"] == c and r.get("arm") == a and r["kind"] == "followed"
                       and r.get("takeover_k") is not None]) for c, a, label in tk.GROUPS]
    groups = [(label, rs) for label, rs in groups if rs]
    if not groups:
        return []
    fig, ax = plt.subplots(figsize=(16, 9))
    for y, (label, rs) in enumerate(reversed(groups)):
        for j, r in enumerate(sorted(rs, key=lambda r: r["takeover_frac"])):
            jitter = ((j % 5) - 2) * 0.06
            filled = bool(r.get("mention_within_2_before"))
            ax.plot(r["takeover_frac"], y + jitter, "o", markersize=9, color=C["cue"],
                    markerfacecolor=C["cue"] if filled else "white", markeredgewidth=1.6)
        m = statistics.median(r["takeover_frac"] for r in rs)
        ax.plot([m, m], [y - 0.3, y + 0.3], color=C["ink"], lw=2)
        with_mention = sum(bool(r.get("mention_within_2_before")) for r in rs if r["takeover_k"] >= 1)
        ax.text(1.02, y, f"{len(rs)} runs · median {m:.2f} · mention just before: {with_mention} of "
                f"{sum(r['takeover_k'] >= 1 for r in rs)}", va="center", fontsize=11, color=C["ink"])
    ax.set_yticks(range(len(groups)))
    ax.set_yticklabels([label for label, _ in reversed(groups)])
    ax.set_xlim(-0.03, 1.0)
    ax.set_xlabel("takeover point: share of the reasoning before the hint letter leads for good (0 = before any "
                  "reasoning)")
    ax.grid(axis="x", color=C["grid"], lw=0.8)
    ax.tick_params(axis="y", length=0)
    handles = [plt.Line2D([], [], marker="o", color=C["cue"], ls="none", markersize=9),
               plt.Line2D([], [], marker="o", color=C["cue"], markerfacecolor="white", ls="none", markersize=9),
               plt.Line2D([], [], color=C["ink"], lw=2)]
    ax.legend(handles, ["mention in the takeover sentence or the 2 before", "no mention just before", "median"],
              loc="upper left", bbox_to_anchor=(0, 1.08), ncol=3, frameon=False)
    fig.subplots_adjust(top=0.86, bottom=0.1, left=0.16, right=0.72)
    return [finish(fig, figs / "takeover_points", "Where the hint takes over, in followed runs", len(rows))]


def binned(rs):
    """Mean hint-letter probability per tenth (BINS) of the reasoning, over runs."""
    sums, counts = [0.0] * BINS, [0] * BINS
    for r in rs:
        for x, p in zip(xs(r), series(r, "hint_prob")):
            b = min(BINS - 1, int(x * BINS))
            sums[b] += p
            counts[b] += 1
    return [s / c if c else float("nan") for s, c in zip(sums, counts)]


def plot_means(rows, figs=FIGS):
    panels = [(c, a, label) for c, a, label in tk.GROUPS if any(r["condition"] == c and r.get("arm") == a for r in rows)]
    if not panels:
        return []
    nohint = [r for r in rows if r["kind"] == "no hint"]
    fig, axes = plt.subplots(1, len(panels), figsize=(16, 9), sharey=True, squeeze=False)
    mid = [(b + 0.5) / BINS for b in range(BINS)]
    for ax, (c, a, label) in zip(axes[0], panels):
        for kind in ("followed", "resisted"):
            rs = [r for r in rows if r["condition"] == c and r.get("arm") == a and r["kind"] == kind]
            if rs:
                ax.plot(mid, binned(rs), color=KIND_COLOR[kind], lw=2, label=f"{kind} ({len(rs)})")
        if nohint:
            ax.plot(mid, binned(nohint), color=KIND_COLOR["no hint"], lw=2, label=f"no hint ({len(nohint)})")
        ax.set_title(label, loc="left")
        ax.set_xlim(0, 1)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1], ["0", "0.25", "0.5", "0.75", "1"])
        ax.set_ylim(0, 1)
        ax.set_xlabel("share of the reasoning")
        ax.grid(axis="y", color=C["grid"], lw=0.8)
        ax.legend(loc="center right", frameon=False)
    axes[0][0].set_ylabel("mean probability of the hint letter")
    fig.subplots_adjust(top=0.86, bottom=0.1, left=0.06, right=0.98, wspace=0.14)
    return [finish(fig, figs / "takeover_mean_curves",
                   "The hint letter's probability through the reasoning, by outcome", len(rows))]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    rows = tk.current_probes(load(tk.OUT))
    pages = curve_pages(rows)
    n_curve = sum(math.ceil(len(rs) / PER_PAGE) for rs in pages.values())
    print(f"{len(rows)} probed runs -> {n_curve} pages of curves, takeover_points, takeover_mean_curves "
          f"in {FIGS.relative_to(CODE)}")
    if a.dry_run:
        return
    for path in plot_curves(rows) + plot_points(rows) + plot_means(rows):
        print(f"  {path.relative_to(CODE)}")


if __name__ == "__main__":
    main()
