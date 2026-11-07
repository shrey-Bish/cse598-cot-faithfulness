"""Track C, C25: slide 12's figure, the three hops and the decider (no calls).

  python agents/c25_figure.py        # -> docs/trackC/figures/c25_hops.{png,svg,csv}

Drawn from the numbers-only summary (results/summaries/trackC/c25_summary.json) in the slide style of
tools/slide_figures.py (imported read-only), to WAITING.md's spec: 16:9, white, colors by role, the count on each bar,
95% Wilson whiskers, a CSV of every plotted number. Left: x = hop (the solver's final answer, the plain note, the keep
note), y = the share of bad-lookup cases naming the tool, with a 50% line. Right: per decider, the share accepting the
solver's wrong letter for the plain, keep and keep_stripped notes, with the paired differences (M1: keep_stripped
minus keep; M2: plain minus keep) and the pre-registered rule's words under each group.
"""
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "tools"))
sys.path.insert(0, str(CODE / "progress"))

from common import wilson  # noqa: E402

SUMMARY = CODE / "results" / "summaries" / "trackC" / "c25_summary.json"
OUT = CODE.parent / "docs" / "trackC" / "figures"
NAME = "c25_hops"
DECIDERS = (("olmo3-32b-instruct", "Olmo 3.1 32B Instruct"), ("qwen3-30b-a3b-instruct-2507", "Qwen3 30B Instruct"))
# WAITING.md: the private reasoning's color on the solver's hop, the final answer's on the notes, the damage color on
# the decider's bars (the keep note's hatch marks the one told to say where the answer comes from).
HOPS = (("hop1_solver", "the solver's final answer (hop 1)", "private", None),
        ("hop2_plain", "the writer's handoff note (hop 2)", "final", None),
        ("hop2_keep", "the keep note (hop 2, told to say where the answer comes from)", "final", "//"))
NOTES = (("plain", "plain", None), ("keep", "keep", "//"), ("keep_stripped", "keep,\nstripped", "xx"))


def _row(panel, group, arm, k, n, **more):
    lo, hi = wilson(k, n)
    return {"panel": panel, "group": group, "arm": arm, "k": k, "n": n, "rate": round(k / n, 6), "low": round(lo, 6),
            "high": round(hi, 6), **more}


def rows_of(summary=SUMMARY):
    """One row per bar. Left: the three hops on bad lookups (the source reading on the hop-2 rows). Right: per decider
    and note version, acceptances of the wrong letter on the 53 (M1 and M2, the rule and the verdict on the keep_stripped
    and plain rows)."""
    s = json.loads(Path(summary).read_text())
    rows = []
    src = s["source_bad_lookups"]
    for hop, _, _, _ in HOPS:
        e = src[hop]
        rows.append(_row("source", "bad lookups", hop, e["k"], e["n"], diff="", diff_low="", diff_high="",
                         rule=e.get("reading", ""), verdict=""))
    for model, name in DECIDERS:
        d = s["deciders"][model]
        m1, m2 = d["M1_stripped_minus_keep"], d["M2_plain_minus_keep"]
        counts = {"plain": (m2["variant_k"], m2["variant_n"]), "keep": (m1["answer_only_k"], m1["answer_only_n"]),
                  "keep_stripped": (m1["variant_k"], m1["variant_n"])}
        for note, _, _ in NOTES:
            k, n = counts[note]
            m = m1 if note == "keep_stripped" else m2 if note == "plain" else None
            rows.append(_row("decider", name, note, k, n,
                             diff=round(m["diff"], 6) if m else "", diff_low=round(m["interval"][0], 6) if m else "",
                             diff_high=round(m["interval"][1], 6) if m else "", rule=m["reading"] if m else "",
                             verdict=m1["source_gone"] if note == "keep_stripped" else ""))
    return rows


def draw(out=OUT, summary=SUMMARY):
    import slide_figures as sf
    rows = rows_of(summary)
    plt, fig = sf.frame()
    width = 0.25
    # left: the source at each hop
    ax = fig.add_axes([0.06, 0.30, 0.30, 0.43])
    src = {r["arm"]: r for r in rows if r["panel"] == "source"}
    for j, (hop, _, role, hatch) in enumerate(HOPS):
        r = src[hop]
        sf.bar(ax, j, {"value": r["rate"], "low": r["low"], "high": r["high"], "k": r["k"], "n": r["n"]},
               sf.ROLE[role], 0.6, hatch=hatch)
        if r["rule"]:
            ax.annotate(r["rule"], (j, 0), xytext=(0, -34), textcoords="offset points", ha="center", va="top",
                        fontsize=sf.TEXT_SIZE, color=sf.INK, annotation_clip=False)
    ax.axhline(50, color=sf.INK, linewidth=1, linestyle=(0, (4, 3)))
    ax.set_xticks(range(3), ["solver", "plain note", "keep note"], fontsize=sf.TITLE_SIZE)
    ax.set_xlim(-0.6, 2.6)
    ax.set_ylabel("names the tool (% of 55 bad lookups)")
    ax.set_title("Where the source goes, hop by hop", fontsize=sf.TITLE_SIZE, loc="left")
    sf.percent_axis(ax)
    # right: the decider, never shown the tool
    ax = fig.add_axes([0.44, 0.30, sf.RIGHT - 0.44, 0.43])
    ticks, labels = [], []
    for i, (_, name) in enumerate(DECIDERS):
        part = {r["arm"]: r for r in rows if r["panel"] == "decider" and r["group"] == name}
        for j, (note, label, hatch) in enumerate(NOTES):
            r = part[note]
            x = i + (j - 1) * (width + 0.02)
            sf.bar(ax, x, {"value": r["rate"], "low": r["low"], "high": r["high"], "k": r["k"], "n": r["n"]},
                   sf.ROLE["damage"], width, hatch=hatch)
            ticks.append(x)
            labels.append(label)
        ax.annotate(name, (i, 0), xytext=(0, -38), textcoords="offset points", ha="center", va="top",
                    fontsize=sf.TITLE_SIZE, color=sf.INK, annotation_clip=False)
        m1, m2 = part["keep_stripped"], part["plain"]
        ax.annotate(f"stripped − keep: {sf.signed(m1['diff'] * 100)} [{sf.signed(m1['diff_low'] * 100)}, "
                    f"{sf.signed(m1['diff_high'] * 100)}], {m1['rule']}\n"
                    f"plain − keep: {sf.signed(m2['diff'] * 100)} [{sf.signed(m2['diff_low'] * 100)}, "
                    f"{sf.signed(m2['diff_high'] * 100)}], {m2['rule']}",
                    (i, 0), xytext=(0, -60), textcoords="offset points", ha="center", va="top",
                    fontsize=sf.LABEL_SIZE, color=sf.INK, annotation_clip=False, linespacing=1.4)
    ax.set_xticks(ticks, labels, fontsize=sf.LABEL_SIZE)
    ax.set_xlim(-0.6, len(DECIDERS) - 0.4)
    ax.set_ylabel("accepts the wrong letter (% of 53)")
    ax.set_title("The decider, which never sees the tool", fontsize=sf.TITLE_SIZE, loc="left")
    sf.percent_axis(ax)
    sf.key(fig, [(sf.swatch(sf.ROLE[role], hatch), label) for _, label, role, hatch in HOPS]
           + [(sf.swatch(sf.ROLE["damage"]), "the decider accepts the solver's wrong letter")], ncol=2)
    sf.headline(fig, "C25: the writer restores the source (plain 35 of 55, keep 55 of 55). Stripped, the Olmo "
                "decider accepts the wrong",
                "answer 9 of 53 against 16 of 53, −13 [−23, −6]: unclear by the pre-registered rule. Qwen3: 0 of 53 "
                "either way.")
    sf.note(fig, "Track C, C25 (Nov 6): C15's 100 saved solver answers (55 bad lookups), a Qwen3 30B Instruct writer "
            "(one note per answer, plain or told to keep the source), then both deciders with C4's reviewer prompt "
            "(plus_explanation), the note in place of the final answer; 800 calls. Bars: X of Y above; lines: 95% "
            "Wilson. Left: the share naming the tool (keyword), 50% line = the kept/lost rule. Right: the share whose "
            "letter is the solver's wrong letter; under each group M1 (stripped − keep, the main comparison) and M2 "
            "(plain − keep), paired by item, 95% bootstrap, C11's 20-point two-sided rule. One writer, one wording per "
            "variant.")
    fig.legends[0].set_bbox_to_anchor((sf.LEFT, 0.865), transform=fig.transFigure)
    paths = sf.save(fig, NAME, rows, out)
    plt.close(fig)
    return paths


if __name__ == "__main__":
    for p in draw():
        print(p.relative_to(CODE.parent))
