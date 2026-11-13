"""B1R2 beside B1 (F38): the deployable span (alpha 0.25 on the inserted tool turn, chosen on set A) minus alpha = 1, by
B1's rule unchanged (finetune/gpu/provenance_job.b1_verdict), on the held-out 30 (B1, the primary result) and on E2's 120
questions (B1R2, a labelled replication; the A39 log's sections 5, 13 and 21), side by side, in tools/slide_figures.py's
style: 16:9, white, colors by role, a CSV of every plotted number, PNG 2000 x 1125 and SVG.

  b1r2_vs_b1   per study, three rows: wrong-hint following and correct-hint acceptance on the inserted tool turn, and
               no-hint accuracy; each the deployable span minus alpha = 1, paired by question (dots, in points), with
               the report's 95% bootstrap clustered by question (lines), alpha = 1's and the span's X of Y under it, and
               the rule's 5-point limits shaded (acceptance falls by no more than 5, accuracy moves by no more than 5:
               the rule reads the point estimates). The headline gives each study's reading in the rule's words.

Both reports are provenance_job.py report's (numbers only): B1's tracked one, and B1R2's once exported. A B1R2 report short
of its 600 runs a system is refused: a partial B1R2 is read on its complete questions only (section 13.8), which this
report doesn't do.

  python tools/b1r2_figure.py           # -> docs/paper/figures/b1r2_vs_b1.png, .svg and .csv
  python tools/b1r2_figure.py --b1 B1_REPORT --b1r2 B1R2_REPORT --out SOMEWHERE
"""
import argparse
import json
import sys
import textwrap
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "tools"))
sys.path.insert(0, str(CODE / "progress"))

from finetune.gpu import provenance_job as pj  # noqa: E402
from paper_figures import GRID, INK, MUTED  # noqa: E402
from slide_figures import CLUSTERED, OUT, ROLE, SIZE, WHITE, save, style  # noqa: E402

GPU_SUM = CODE / "results" / "summaries" / "trackA" / "gpu"
B1_REPORT = GPU_SUM / "provenance_gen" / "provenance_gen_report.json"
B1R2_REPORT = GPU_SUM / "b1r2" / "provenance_gen_report.json"
B1R2_RUNS = 600                    # a system: E2's 120 questions x (2 wrong, 2 correct, 1 no hint), the inserted tool turn
NAME = "b1r2_vs_b1"
STUDIES = (("B1", "the held-out 30", "(a) B1 on the held-out 30 (primary, F38)"),
           ("B1R2", "E2", "(b) B1R2 on E2's 120 questions (a labelled replication)"))
MEASURES = {"following": ("wrong_hint_following | tool_injected", "follows the wrong hint", "inserted tool turn",
                          ROLE["damage"], "o"),
            "acceptance": ("correct_hint_acceptance | tool_injected", "takes the correct hint", "inserted tool turn",
                           ROLE["correct"], "D"),
            "accuracy": ("no_hint_accuracy | all", "no-hint accuracy", "no hint", ROLE["baseline"], "s")}
LIMITS = {"acceptance": (-pj.MARGIN, None), "accuracy": (-pj.MARGIN, pj.MARGIN)}    # B1's rule, on the point estimates
PAIRED = CLUSTERED + ", paired"


# ---------------------------------------------------------------- the rows (every plotted number)
def rows(b1, b1r2):
    """Per study and measure: b1_verdict's difference and interval (the deployable span on the inserted tool turn), the
    span's and alpha = 1's X of Y, the questions, the rule's limit (acceptance and accuracy) and the study's reading."""
    out = []
    for (study, qset, _), res in zip(STUDIES, (b1, b1r2)):
        v = pj.b1_verdict(res, "deployable", "tool_injected")
        dep, base = res["systems"][v["system"]], res["systems"][res["base"]]
        for m, (key, _, channel, _, _) in MEASURES.items():
            d = v[m]
            out.append({"study": study, "set": qset, "measure": m, "channel": channel, "alpha": v["alpha"],
                        "value": d["diff"], "low": d["interval"][0], "high": d["interval"][1],
                        "questions": d["questions"], "interval": PAIRED, "k": dep[key]["k"], "n": dep[key]["n"],
                        "compared_k": base[key]["k"], "compared_n": base[key]["n"],
                        "limit": pj.MARGIN if m in LIMITS else "", "reading": v["reading"]})
    return out


def complete(res):
    """B1R2's runs: each system's count against the design's 600 ({system: runs} of those short)."""
    return {s: e["runs"] for s, e in res["systems"].items() if e["runs"] != B1R2_RUNS}


# ---------------------------------------------------------------- words
def pts(v):
    """A difference in points, one decimal, a true minus: −5.8, +0.8, 0.0."""
    return "0.0" if abs(v) < 0.0005 else f"{v * 100:+.1f}".replace("-", "−")


def ci(r):
    return f"{pts(r['value'])} [{pts(r['low'])}, {pts(r['high'])}]"


def words(rs):
    """(headline, sentence): each study's reading in the rule's words, then following on each and acceptance against
    the rule's 5-point limit."""
    get = {(r["study"], r["measure"]): r for r in rs}
    reading = {s: get[(s, "following")]["reading"] for s, _, _ in STUDIES}
    head = (f'B1\'s rule: the held-out 30 (primary) "{reading["B1"]}"; E2\'s 120 questions (B1R2, a labelled '
            f'replication) "{reading["B1R2"]}"')
    acc = [get[(s, "acceptance")]["value"] for s, _, _ in STUDIES]
    side = ["past" if a < -pj.MARGIN else "within" for a in acc]
    limit = (f"both {side[0]} the rule's 5-point limit" if side[0] == side[1] else
             f"{side[0]} and {side[1]} the rule's 5-point limit")
    sub = (f"The deployable span (alpha 0.25, the inserted tool turn) minus alpha = 1, paired by question. Wrong hints "
           f"followed: {ci(get[('B1', 'following')])} points on the 30, {ci(get[('B1R2', 'following')])} on E2. "
           f"Correct hints taken: {pts(acc[0])} and {pts(acc[1])} points, {limit} (point estimates).")
    return head, sub


# ---------------------------------------------------------------- drawing
def xlim(rs):
    """One x range for both panels, in points: the intervals with room for the value labels on the right."""
    vals = [round(x * 100, 6) for r in rs for x in (r["low"], r["high"])]      # -30.000000000000004 is -30
    return min(-10, (min(vals) // 10) * 10 - 5), max(10, -(-max(vals) // 10) * 10 + 25)


def panel(ax, rs, lim, title):
    from matplotlib import patheffects
    from matplotlib.patches import Rectangle
    halo = [patheffects.withStroke(linewidth=3, foreground=WHITE)]      # no reference line cuts through a label
    ys = {m: len(MEASURES) - 1 - i for i, m in enumerate(MEASURES)}
    ax.set_xlim(*lim)
    ax.set_ylim(-0.6, len(MEASURES) - 0.35)
    for m, (lo, hi) in LIMITS.items():                     # the rule's limits: shaded, edges dashed
        left, right = lo * 100, (hi * 100 if hi is not None else lim[1])
        ax.add_patch(Rectangle((left, ys[m] - 0.4), right - left, 0.8, facecolor=GRID, edgecolor="none", alpha=0.75,
                               zorder=0))
        for edge in (lo, hi):
            if edge is not None:
                ax.plot([edge * 100] * 2, [ys[m] - 0.4, ys[m] + 0.4], color=MUTED, linewidth=1.0, linestyle="--",
                        zorder=1)
    ax.axvline(0, color=MUTED, linewidth=1.0, zorder=1)
    for r in rs:
        _, _, _, color, marker = MEASURES[r["measure"]]
        y, v, lo, hi = ys[r["measure"]], r["value"] * 100, r["low"] * 100, r["high"] * 100
        ax.plot([lo, hi], [y, y], color=color, linewidth=2.4, solid_capstyle="butt", zorder=2)
        ax.plot(v, y, marker, color=color, markersize=10 if marker == "o" else 8.5, markeredgecolor=WHITE,
                markeredgewidth=1.5, zorder=3)
        ax.annotate(ci(r), (hi, y), xytext=(7, 0), textcoords="offset points", va="center", fontsize=11, color=INK,
                    zorder=4, path_effects=halo)
        ax.annotate(f"α = 1 → {r['alpha']:g}: {r['compared_k']} of {r['compared_n']} → {r['k']} of {r['n']}", (lo, y),
                    xytext=(0, -13), textcoords="offset points", va="top", ha="left", fontsize=10, color=MUTED,
                    zorder=4, path_effects=halo)
    for y in range(len(MEASURES) - 1):
        ax.axhline(y + 0.5, color=GRID, linewidth=0.8, zorder=0)
    ax.set_xticks([t for t in range(-200, 201, 10) if lim[0] <= t <= lim[1]])
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", color=GRID)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("deployable span minus alpha = 1 (points)")
    ax.set_title(f'{title}\nB1\'s rule: "{rs[0]["reading"]}"', loc="left", color=INK, fontsize=13, linespacing=1.4)
    return ys


def draw(b1, b1r2, out):
    plt = style()
    rs = rows(b1, b1r2)
    fig = plt.figure(figsize=SIZE)
    lim = xlim(rs)
    axes = [fig.add_axes([0.19, 0.3, 0.375, 0.42]), fig.add_axes([0.61, 0.3, 0.375, 0.42])]
    for ax, (study, _, title) in zip(axes, STUDIES):
        ys = panel(ax, [r for r in rs if r["study"] == study], lim, title)
    from matplotlib.transforms import blended_transform_factory
    t = blended_transform_factory(fig.transFigure, axes[0].transData)
    for m, (_, name, channel, _, _) in MEASURES.items():
        axes[0].text(0.015, ys[m] + 0.06, name, transform=t, fontsize=12, color=INK, va="bottom", clip_on=False)
        axes[0].text(0.015, ys[m] - 0.04, channel, transform=t, fontsize=10, color=MUTED, va="top", clip_on=False)
    head, sub = words(rs)
    head = textwrap.fill(head, 125)
    fig.text(0.015, 0.955, head, fontsize=15, color=INK, va="top", linespacing=1.25)
    fig.text(0.015, 0.905 - 0.033 * head.count("\n"), textwrap.fill(sub, 150), fontsize=12, color=INK, va="top",
             linespacing=1.3)
    handles = [plt.Line2D([], [], color=MEASURES[m][3], marker=MEASURES[m][4], linewidth=2.4, markersize=8,
                          markeredgecolor=WHITE) for m in MEASURES]
    from matplotlib.patches import Patch
    handles.append(Patch(facecolor=GRID, edgecolor=MUTED, linestyle="--"))
    names = [MEASURES[m][1] for m in MEASURES] + ["the rule's 5-point limit (read on the point estimate)"]
    fig.legend(handles, names, loc="lower left", bbox_to_anchor=(0.01, 0.165), ncol=len(handles), frameon=False,
               fontsize=11)
    fig.text(0.015, 0.012, textwrap.fill(
        "B1's rule (the Oct 30 17:15 log, section 2; provenance_job.b1_verdict, unchanged): works, following's interval "
        "below 0 with acceptance falling by no more than 5 points and no-hint accuracy moving by no more than 5; ignores "
        "tools, following falls and acceptance falls more than 5; costs accuracy, acceptance holds and accuracy moves more "
        "than 5; no effect, following's interval includes 0; worse, above 0. Olmo 3 7B Think, attention from layers 15, "
        "19 and 23 to the inserted tool turn scaled by 0.25 (chosen on set A), the fixed engine (-v2). B1: 30 questions, "
        "each 2 wrong-hint and 1 correct-hint runs on the inserted turn and 1 no-hint run. B1R2: E2's 120, each 2, 2 and "
        "1 (the A39 log's sections 5 and 13). Dots: the span minus alpha = 1, paired by question; lines: 95% bootstrap clustered by "
        "question (20,000 resamples, seed 0); no answer counts as not following and not taking.", 172),
        fontsize=10, color=MUTED, linespacing=1.35)
    paths = save(fig, NAME, rs, out)
    plt.close(fig)
    return paths


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--b1", default=str(B1_REPORT), help="B1's report on the 30 (provenance_job.py report)")
    ap.add_argument("--b1r2", default=str(B1R2_REPORT), help="B1R2's report on E2 (provenance_job.py report)")
    ap.add_argument("--out", default=str(OUT), help="where the PNG, SVG and CSV go (default docs/paper/figures/)")
    a = ap.parse_args(argv)
    b1, b1r2 = (json.loads(Path(p).read_text()) for p in (a.b1, a.b1r2))
    short = complete(b1r2)
    if short:
        raise SystemExit(f"B1R2 is not complete ({a.b1r2}: runs {short}, against {B1R2_RUNS} a system); a partial B1R2 "
                         "is read on its complete questions only (the A39 log's section 13.8)")
    paths = draw(b1, b1r2, a.out)
    for p in paths:
        print(p)
    return paths


if __name__ == "__main__":
    main()
