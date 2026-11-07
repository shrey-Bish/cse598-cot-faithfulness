"""Track C, C20 and C26: slide 12's second figure, pipeline vs model (no calls).

  python agents/c20_c26_figure.py        # -> docs/trackC/figures/pipeline_vs_model.{png,svg,csv}

Drawn from the numbers-only summaries (results/summaries/trackC/c20_summary.json, c26_summary.json, and
c15_summary.json for C26's answer-key side) in the slide style of tools/slide_figures.py (imported read-only): 16:9,
white, colors by role, the count on each bar, 95% Wilson whiskers, a CSV of every plotted number.
Left (C20): per reviewer, the share of wrong solver answers caught by the blind reviewer, the reviewer with the
pipeline's provenance tag, and the reviewer of the solver's own disclosure; the checker's bar at the right. The two
pre-registered differences (tag − blind, tag − disclosure) and the rule's words under each group.
Right (C26): per reviewer, the share of wrong answers corrected with the answer only and with the tool log, for C15's
answer-key tool (solid) and C26's retrieval passage (hatched); the tool log − answer only difference and C11's rule
under each.
"""
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "tools"))
sys.path.insert(0, str(CODE / "progress"))

from common import wilson  # noqa: E402

SUM = CODE / "results" / "summaries" / "trackC"
C20, C26, C15 = SUM / "c20_summary.json", SUM / "c26_summary.json", SUM / "c15_summary.json"
OUT = CODE.parent / "docs" / "trackC" / "figures"
NAME = "pipeline_vs_model"
REVIEWERS = (("olmo3-32b-instruct", "Olmo 3.1 32B Instruct"), ("qwen3-30b-a3b-instruct-2507", "Qwen3 30B Instruct"))
PIPELINES = (("a_blind", "blind", "baseline", None), ("b_tag", "tag", "cue", None), ("c_disclosure", "disclosure", "final", None))
TOOLS = (("c15", "answer key (C15)", None), ("c26", "retrieved passage (C26)", "//"))
VARIANTS = (("answer_only", "answer only", "baseline"), ("plus_tool_log", "+ tool log", "cue"))


def _row(panel, group, arm, k, n, **more):
    lo, hi = wilson(k, n)
    return {"panel": panel, "group": group, "arm": arm, "k": k, "n": n, "rate": round(k / n, 6), "low": round(lo, 6),
            "high": round(hi, 6), "diff": "", "diff_low": "", "diff_high": "", "rule": "", **more}


def _d(e):
    return {"diff": round(e["diff"], 6), "diff_low": round(e["interval"][0], 6), "diff_high": round(e["interval"][1], 6)}


def rows_of(c20=C20, c26=C26, c15=C15):
    """One row per bar. C20: caught, per reviewer and pipeline (the differences on the tag row: tag − blind as
    diff/rule, tag − disclosure as diff2/rule2), plus the checker. C26: corrects a wrong answer, per reviewer, tool
    and variant (tool log − answer only on the plus_tool_log row)."""
    s20, s26, s15 = (json.loads(Path(p).read_text()) for p in (c20, c26, c15))
    rows = []
    for model, name in REVIEWERS:
        pipes, rd = s20["pipelines"], s20["readings"][model]
        for pipe, _, _, _ in PIPELINES:
            e = pipes[f"{pipe} | {model}"]["caught"]
            more = {}
            if pipe == "b_tag":
                m1, m4 = rd["1_tag_minus_blind_catches"], rd["4_tag_minus_disclosure_catches"]
                more = {**_d(m1), "rule": m1["reading"], "diff2": round(m4["diff"], 6),
                        "diff2_low": round(m4["interval"][0], 6), "diff2_high": round(m4["interval"][1], 6),
                        "rule2": m4["reading"]}
            rows.append(_row("c20", name, pipe, e["k"], e["n"], **more))
    e = s20["pipelines"]["d_checker"]["caught"]
    rows.append(_row("c20", "checker", "d_checker", e["k"], e["n"]))
    for model, name in REVIEWERS:
        a15, a26 = s15["a_replication"][model], s26["reviewers"][model]["R2_plus_tool_log_minus_answer_only"]
        for tool, e in (("c15", a15), ("c26", a26)):
            rows.append(_row("c26", name, f"{tool}_answer_only", e["answer_only_k"], e["answer_only_n"]))
            rows.append(_row("c26", name, f"{tool}_plus_tool_log", e["variant_k"], e["variant_n"], **_d(e),
                             rule=e["rule"]))
    return [{"diff2": "", "diff2_low": "", "diff2_high": "", "rule2": "", **r} for r in rows]


def _fmt(sf, d, lo, hi):
    return f"{sf.signed(d * 100)} [{sf.signed(lo * 100)}, {sf.signed(hi * 100)}]"


def _block(ax, sf, lines, y=-62):
    """Lines of text under a panel, left-aligned with its axis, below the tick labels and group names."""
    ax.annotate("\n".join(lines), (0, 0), xycoords="axes fraction", xytext=(0, y), textcoords="offset points",
                ha="left", va="top", fontsize=sf.LABEL_SIZE, color=sf.INK, annotation_clip=False, linespacing=1.45)


SHORT = {"Olmo 3.1 32B Instruct": "Olmo 3.1 32B", "Qwen3 30B Instruct": "Qwen3 30B Instruct"}


def draw(out=OUT, c20=C20, c26=C26, c15=C15):
    import slide_figures as sf
    rows = rows_of(c20, c26, c15)
    plt, fig = sf.frame()
    width, y0, h = 0.22, 0.365, 0.35
    # left: C20, the pipelines
    ax = fig.add_axes([0.06, y0, 0.42, h])
    block = []
    for i, (_, name) in enumerate(REVIEWERS):
        part = {r["arm"]: r for r in rows if r["panel"] == "c20" and r["group"] == name}
        for j, (pipe, _, role, hatch) in enumerate(PIPELINES):
            r = part[pipe]
            sf.bar(ax, i + (j - 1) * (width + 0.02), {"value": r["rate"], "low": r["low"], "high": r["high"],
                                                         "k": r["k"], "n": r["n"]}, sf.ROLE[role], width, hatch=hatch,
                   label=f"{r['k']} of {r['n']}" + ("\n" if j % 2 else ""))   # every second label a line higher
        t = part["b_tag"]
        block += [f"{SHORT[name]}, tag − blind: {_fmt(sf, t['diff'], t['diff_low'], t['diff_high'])}, {t['rule']}",
                  f"{SHORT[name]}, tag − disclosure: {_fmt(sf, t['diff2'], t['diff2_low'], t['diff2_high'])}, "
                  f"{t['rule2']}"]
    chk = next(r for r in rows if r["arm"] == "d_checker")
    sf.bar(ax, len(REVIEWERS), {"value": chk["rate"], "low": chk["low"], "high": chk["high"], "k": chk["k"],
                                "n": chk["n"]}, sf.ROLE["correct"], width)
    ax.set_xticks(range(len(REVIEWERS) + 1), [SHORT[n] for _, n in REVIEWERS] + ["the checker\n(no reviewer)"],
                  fontsize=sf.TEXT_SIZE)
    ax.set_xlim(-0.6, len(REVIEWERS) + 0.4)
    ax.set_ylabel("catches the wrong solver answer (% of 53)")
    ax.set_title("C20: can the pipeline carry the source?", fontsize=sf.TITLE_SIZE, loc="left")
    sf.percent_axis(ax)
    _block(ax, sf, block)
    # right: C26, deference without the authority label
    ax = fig.add_axes([0.56, y0, sf.RIGHT - 0.56, h])
    block = []
    for i, (model, name) in enumerate(REVIEWERS):
        part = {r["arm"]: r for r in rows if r["panel"] == "c26" and r["group"] == name}
        k = 0
        for tool, _, hatch in TOOLS:
            for variant, _, role in VARIANTS:
                r = part[f"{tool}_{variant}"]
                sf.bar(ax, i + (k - 1.5) * (width + 0.02), {"value": r["rate"], "low": r["low"], "high": r["high"],
                                                             "k": r["k"], "n": r["n"]}, sf.ROLE[role], width, hatch=hatch,
                       label=f"{r['k']} of {r['n']}" + ("\n" if k % 2 else ""))
                k += 1
        a, b = part["c15_plus_tool_log"], part["c26_plus_tool_log"]
        block += [f"{SHORT[name]}, answer key: {_fmt(sf, a['diff'], a['diff_low'], a['diff_high'])}, {a['rule']}",
                  f"{SHORT[name]}, passage: {_fmt(sf, b['diff'], b['diff_low'], b['diff_high'])}, {b['rule']}"]
    ax.set_xticks(range(len(REVIEWERS)), [SHORT[n] for _, n in REVIEWERS], fontsize=sf.TEXT_SIZE)
    ax.set_xlim(-0.7, len(REVIEWERS) - 0.3)
    ax.set_ylabel("corrects the wrong solver answer (%)")
    ax.set_title("C26: does deference survive without the authority label?", fontsize=sf.TITLE_SIZE, loc="left")
    sf.percent_axis(ax)
    _block(ax, sf, block)
    sf.key(fig, [(sf.swatch(sf.ROLE["baseline"]), "the reviewer sees the answer only (C20: blind)"),
                 (sf.swatch(sf.ROLE["cue"]), "+ the pipeline's tag (C20) or + the tool log (C26)"),
                 (sf.swatch(sf.ROLE["final"]), "the solver's own disclosure (C20; C16's solve)"),
                 (sf.swatch(sf.ROLE["correct"]), "the checker, which re-solves without the tool (C20)"),
                 (sf.swatch(sf.ROLE["cue"], "//"), "hatched: C26's retrieved passage; solid: C15's answer key")],
           ncol=2)
    o20 = next(r for r in rows if r["panel"] == "c20" and r["group"] == REVIEWERS[0][1] and r["arm"] == "b_tag")
    o26 = next(r for r in rows if r["panel"] == "c26" and r["group"] == REVIEWERS[0][1] and r["arm"] == "c26_plus_tool_log")
    sf.headline(fig, f"C20: the pipeline's tag: Olmo {sf.signed(o20['diff'] * 100)} points of catches over blind "
                f"({o20['rule']}), {sf.signed(o20['diff2'] * 100)} over the solver's own disclosure.",
                f"C26: a retrieved passage in place of the answer key: the Olmo reviewer's tool-log effect is "
                f"{_fmt(sf, o26['diff'], o26['diff_low'], o26['diff_high'])}, {o26['rule']}.")
    sf.note(fig, "Track C, C20 and C26 (Nov 6). Left: C15's 100 items; caught = the solver is wrong and the check "
            "stage corrects or escalates, of the 53 wrong answers (disclosure: C16's solve, 55); the tag is "
            "\"[letter from tool lookup_answer_key; unverified]\". Right: the same solver with search_passages "
            "returning the option's text (no letter, no \"answer key\"); corrects a wrong answer after a bad lookup: "
            "C26's 21 items (the solver followed the passage in 19 of 55) beside C15's 53. Bars: X of Y above; lines: "
            "95% Wilson. Differences paired by item, 95% "
            "bootstrap; C11's 20-point two-sided rule (C20) and C11's deference rule (C26).")
    fig.legends[0].set_bbox_to_anchor((sf.LEFT, 0.865), transform=fig.transFigure)
    paths = sf.save(fig, NAME, rows, out)
    plt.close(fig)
    return paths


if __name__ == "__main__":
    for p in draw():
        print(p.relative_to(CODE.parent))
