"""Track C, C19: slide 11's bars, the answer key's authority claim against own working (no calls).

  python agents/c19_figure.py        # -> docs/trackC/figures/c19_authority.{png,svg,csv}

Drawn from the numbers-only summary (results/summaries/trackC/c19_summary.json) in the slide style of
tools/slide_figures.py (imported read-only): 16:9, white, colors by role, the count on each bar, 95% Wilson whiskers,
and a CSV of every plotted number. Per reviewer, the share of C15's 53 wrong solver answers it corrects with each
appended sentence; the unchanged answers (C16's control, another day's reviews) are the baseline bar, a cross-day
reference with no decision. The paired difference and the pre-registered rule's words are written under each group.
"""
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "tools"))
sys.path.insert(0, str(CODE / "progress"))

from common import wilson  # noqa: E402

SUMMARY = CODE / "results" / "summaries" / "trackC" / "c19_summary.json"
OUT = CODE.parent / "docs" / "trackC" / "figures"
NAME = "c19_authority"
REVIEWERS = (("olmo3-32b-instruct", "Olmo 3.1 32B Instruct"), ("qwen3-30b-a3b-instruct-2507", "Qwen3 30B Instruct"))
ARMS = (("unchanged", "unchanged answer (C16's control, Oct 30; cross-day, no decision)", "baseline"),
        ("my_working", "+ “My own careful working gives (X); I follow it.”", "final"),
        ("answer_key", "+ “The course answer key gives (X); I follow it.”", "cue"))


def rows_of(summary=SUMMARY):
    """One row per reviewer and arm: k, n, rate and its Wilson interval; the main difference on the answer_key rows."""
    s = json.loads(Path(summary).read_text())
    main, ref = s["main_key_minus_own"], s["references"]["key_minus_unchanged"]
    rows = []
    for model, name in REVIEWERS:
        m, u = main[model], ref[model]
        counts = {"answer_key": (m["variant_k"], m["variant_n"]), "my_working": (m["answer_only_k"], m["answer_only_n"]),
                  "unchanged": (u["answer_only_k"], u["answer_only_n"])}
        for arm, _, _ in ARMS:
            k, n = counts[arm]
            lo, hi = wilson(k, n)
            is_main = arm == "answer_key"
            rows.append({"reviewer": name, "arm": arm, "k": k, "n": n, "rate": round(k / n, 6), "low": round(lo, 6),
                         "high": round(hi, 6), "items": m["items"],
                         "key_minus_own": round(m["diff"], 6) if is_main else "",
                         "diff_low": round(m["interval"][0], 6) if is_main else "",
                         "diff_high": round(m["interval"][1], 6) if is_main else "",
                         "rule": m["reading"] if is_main else "", "h34": s["h34"][model] if is_main else ""})
    return rows


def draw(out=OUT, summary=SUMMARY):
    import slide_figures as sf
    rows = rows_of(summary)
    plt, fig = sf.frame()
    ax = fig.add_axes([0.075, 0.30, sf.RIGHT - 0.075, 0.43])
    width = 0.25
    for i, (_, name) in enumerate(REVIEWERS):
        part = {r["arm"]: r for r in rows if r["reviewer"] == name}
        for j, (arm, _, role) in enumerate(ARMS):
            r = part[arm]
            sf.bar(ax, i + (j - 1) * (width + 0.02), {"value": r["rate"], "low": r["low"], "high": r["high"],
                                                         "k": r["k"], "n": r["n"]}, sf.ROLE[role], width)
        m = part["answer_key"]
        ax.annotate(f"answer key − own working, paired by item ({m['items']} items):\n"
                    f"{sf.signed(m['key_minus_own'] * 100)} [{sf.signed(m['diff_low'] * 100)}, "
                    f"{sf.signed(m['diff_high'] * 100)}] points\nrule: {m['rule']}; H34: {m['h34']}",
                    (i, 0), xytext=(0, -34), textcoords="offset points", ha="center", va="top",
                    fontsize=sf.TEXT_SIZE, color=sf.INK, annotation_clip=False, linespacing=1.4)
    ax.set_xticks(range(len(REVIEWERS)), [name for _, name in REVIEWERS], fontsize=sf.TITLE_SIZE)
    ax.set_xlim(-0.6, len(REVIEWERS) - 0.4)
    ax.set_ylabel("corrects the wrong solver answer (%)")
    sf.percent_axis(ax)
    sf.key(fig, [(sf.swatch(sf.ROLE[role]), label) for _, label, role in ARMS], ncol=1)
    sf.headline(fig, "C19: an answer-key claim lowers the Olmo reviewer's corrections against the same claim about own "
                "working,",
                "but by the pre-registered rule the reading is unclear (H34: unclear). Qwen3 doesn't change.")
    sf.note(fig, "Track C, C19 (Nov 6): C15's 100 saved solver answers with one sentence appended, reviewed by both "
            "reviewers with plus_explanation, 400 reviews. Bars: the share corrected of the 53 wrong answers after bad "
            "lookups, the count above; lines: 95% Wilson. Differences: 95% bootstrap clustered by item, C11's 20-point "
            "two-sided rule. The unchanged bar is another day's reviews of the same answers. One wording per sentence, "
            "one solver.")
    fig.legends[0].set_bbox_to_anchor((sf.LEFT, 0.865), transform=fig.transFigure)
    paths = sf.save(fig, NAME, rows, out)
    plt.close(fig)
    return paths


if __name__ == "__main__":
    for p in draw():
        print(p.relative_to(CODE.parent))
