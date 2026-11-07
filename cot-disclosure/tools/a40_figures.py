"""A40's and A42's figure (Track A: A40's BCT training alone, and A40 + the note, on E2), from the reports finetune/a40.py
and finetune/a42.py write (OUT/a40_<qset>.json, OUT/a42_<qset>.json; numbers only), in tools/a39_figures.py's style:
16:9, white, colors by role, X of Y beside each comparison, a CSV of every plotted number, PNG 2000 x 1125 and SVG.

  a40_<qset>_fixes  each system minus each comparison it is read against, on following (wrong-hint runs ending on the
                    hint's letter), correct-hint acceptance (both pooled over the channels) and no-hint accuracy:
                    A40 minus the one-line instruction (prompt_only; the primary, A40's five readings), minus LoRA (the
                    same readings) and minus base (R1, Gate 3's rule); A40 + note (a40_note) minus the instruction
                    (A42's primary), minus A40 and minus the instruction (R3, A38's reading, written once) and minus
                    base (R1). The reading or verdict under each row.

Dots: the system minus its comparison, paired by question; lines: the report's 95% bootstrap clustered by question.
Following in the damage color (a circle), acceptance in the correct color (a diamond), no-hint accuracy in the comparison
gray (a square). A difference whose two sides' no-answer shares are more than 5 points apart carries a dagger. A42's
vs_a40 (a40_note minus A40 on A40's readings) is reported there with no decision, so it is not drawn: R3's row minus A40
is the reading against A40. Hiding, which R1 and the primary also read, is in the reports, not drawn.

Drawn only from complete reports (each report's "complete"): an incomplete one is refused unless --draft, which stamps
the figure as a draft. Without A42's report, A40's rows alone. The headline says only what the readings say.

  python tools/a40_figures.py                                    # -> docs/paper/figures/a40_e2_fixes.png, .svg, .csv
  python tools/a40_figures.py --a40 OUT/a40_e2.json --a42 OUT/a42_e2.json --out SOMEWHERE [--draft]
"""
import argparse
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "tools"))
sys.path.insert(0, str(CODE / "progress"))

from a39_figures import DAGGER, MEASURES, MISSING, frame, label, legend, rate, row, row_of_dots, verdict, words  # noqa: E402
from paper_figures import GRID, MUTED  # noqa: E402
from slide_figures import OUT, ROLE, SIZE, save, style  # noqa: E402

DIR = CODE / "results" / "summaries" / "trackA" / "gpu" / "a39"
A40, A42 = DIR / "a40_e2.json", DIR / "a42_e2.json"
NAMES = {"base": "base", "prompt_only": "the instruction", "lora": "LoRA", "a40": "A40", "a40_note": "A40 + note"}
SETS = {"e2": "E2"}
R1 = ("following_vs_base", "acceptance_vs_base", "nohint_accuracy_vs_base")     # a40.py's and a42.py's R1 keys
# each system's comparisons, top to bottom: (the report's block, the comparison, the row's name)
COMPARISONS = {"a40": (("primary", "prompt_only", "minus the instruction (primary)"),
                       ("vs_lora", "lora", "minus LoRA"),
                       ("r1", "base", "minus base (R1, Gate 3's rule)")),
               "a40_note": (("primary", "prompt_only", "minus the instruction (primary)"),
                            ("r3", "a40", "minus A40 (R3)"),
                            ("r3", "prompt_only", "minus the instruction (R3)"),
                            ("r1", "base", "minus base (R1, Gate 3's rule)"))}
WHAT = {"a40": "A40", "a40_note": "A42"}
# A40's five readings against the instruction (the A40 log's section 8), in plain words: (one system, two)
GLOSS = {"fewer, but costs acceptance": ("follows fewer wrong hints than the one-line instruction, but takes fewer "
                                         "correct hints", "follow fewer wrong hints than the one-line instruction, but "
                                         "take fewer correct hints"),
         "fewer, but hides more": ("follows fewer wrong hints than the one-line instruction, but hides more",
                                   "follow fewer wrong hints than the one-line instruction, but hide more"),
         "beats the instruction": ("follows fewer wrong hints than the one-line instruction, at no acceptance cost and "
                                   "no more hiding", "follow fewer wrong hints than the one-line instruction, at no "
                                   "acceptance cost and no more hiding"),
         "matches the instruction": ("against the one-line instruction: no difference detected in wrong hints followed",
                                     "against the one-line instruction: no difference detected in wrong hints "
                                     "followed"),
         "worse than the instruction": ("follows more wrong hints than the one-line instruction",
                                        "follow more wrong hints than the one-line instruction")}


# ---------------------------------------------------------------- the rows (every plotted number)
def reading(res, block):
    """A block's reading as the report says it (R1: the verdict and why; the accuracy label beside a reading); with no
    block, the report's label ("not run: ...", "partial: ...")."""
    e = res.get(block)
    if not e:
        return res.get("label") or MISSING
    if block == "r1":
        return verdict(e)
    return e["reading"] + (f" ({e['accuracy_label']})" if e.get("accuracy_label") else "")


def system_rows(res, system):
    """One row per plotted difference: each comparison of the system, following, acceptance and no-hint accuracy (a39's
    row: value, interval, questions, both sides' X of Y and no-answer counts, the reading)."""
    out = []
    for block, against, _ in COMPARISONS[system]:
        e = res.get(block) or {}
        if block == "r3":
            e = e.get(f"minus {against}") or {}
        keys = R1 if block == "r1" else tuple(MEASURES)
        for m, k in zip(MEASURES, keys):
            out.append(row(res, block, system, against, "no hint" if m == "accuracy" else "pooled", m, e.get(k),
                           reading(res, block)))
    return out


# ---------------------------------------------------------------- drawing
def headline(reports):
    """Plain words from the primaries' readings only; the readings themselves, verbatim, in the line under it."""
    names = [NAMES[s] for s, _ in reports]
    first = {reading(res, "primary") for _, res in reports}
    if len(first) == 1 and next(iter(first)) in GLOSS:
        return f"{' and '.join(names)} {GLOSS[next(iter(first))][len(names) > 1]}."
    return f"{' and '.join(names)} against the one-line instruction, LoRA and base."


def summary(reports):
    """Each reading as the report says it, quoted."""
    q = lambda s: f"“{s}”"  # noqa: E731
    got = dict(reports)
    parts = ["Against the instruction: " + ", ".join(f"{NAMES[s]} {q(reading(res, 'primary'))}" for s, res in reports)
             + "."]
    if "a40" in got:
        parts.append(f"Against LoRA: A40 {q(reading(got['a40'], 'vs_lora'))}.")
    if "a40_note" in got:
        parts.append(f"R3: A40 + note {q(reading(got['a40_note'], 'r3'))}.")
    parts.append("R1 against base: " + ", ".join(f"{NAMES[s]} {reading(res, 'r1')}" for s, res in reports) + ".")
    return " ".join(parts)


def layout(reports):
    """y of each comparison row (bottom up) and of each system's header, a row above its first comparison; the next
    system's rows start 1.2 above that header."""
    y, ys, heads = 0.0, {}, {}
    for s, _ in reversed(reports):
        for i in reversed(range(len(COMPARISONS[s]))):
            ys[(s, i)] = y
            y += 1
        heads[s] = y
        y += 1.2
    return ys, heads, max(heads.values()) + 0.55


def fig_fixes(reports, out, draft=False):
    """reports: [(system, report)], A40's first, then A40 + note's when it is in."""
    plt = style()
    rows = [r for s, res in reports for r in system_rows(res, s)]
    first = reports[0][1]
    name, n = SETS.get(first["qset"], first["qset"]), first["questions"]
    fig = plt.figure(figsize=SIZE)
    ax = fig.add_axes([0.255, 0.235, 0.73, 0.585])
    ys, heads, top = layout(reports)
    frame(ax, rows, (-0.75, top))
    left = ax.get_xlim()[0]
    for s, res in reports:
        mine = [r for r in rows if r["system"] == s]
        for i, (block, against, title) in enumerate(COMPARISONS[s]):
            rs = {r["measure"]: r for r in mine if (r["panel"], r["against"]) == (block, against)}
            y = ys[(s, i)]
            row_of_dots(ax, y, rs, (("following", 0.25), ("acceptance", 0.0), ("accuracy", -0.25)))
            f = rs["following"]
            label(fig, ax, 0.015, y, title, f"follows {f['k']} of {f['n']} vs {f['compared_k']} of {f['compared_n']}"
                  if f["n"] != "" else "no runs")
            last_r3 = block == "r3" and i + 1 < len(COMPARISONS[s]) and COMPARISONS[s][i + 1][0] != "r3"
            if block != "r3" or last_r3:
                text = f"R3 (A38's reading): {f['reading']}" if block == "r3" else f["reading"]
                ax.text(left + 0.5, y - 0.42, text, fontsize=9.5, color=MUTED, va="center", ha="left", style="italic")
        fol, acc = rate(res, s, "following", "pooled"), rate(res, s, "acceptance", "pooled")
        label(fig, ax, 0.015, heads[s], NAMES[s] + (f" ({s})" if s != NAMES[s] else ""),
              f"its own: follows {fol.get('k', '-')} of {fol.get('n', '-')}, takes {acc.get('k', '-')} of "
              f"{acc.get('n', '-')}", bold=True)
    for s, _ in reports[1:]:
        ax.axhline(heads[s] + 0.55, color=GRID, linewidth=0.8, zorder=0)
    legend(fig, plt, 0.01, 0.118, tuple(MEASURES), extra=False)
    words(fig, headline(reports), summary(reports),
          f"Pre-registered Nov 5 (A40: its log's sections 8-9) and Nov 6 (A42: its log's sections 3-4), on {name}: {n} "
          "questions, 12 runs a question a system; the comparisons are A39's own runs. Dots: the system minus the "
          "comparison, paired by question, answered runs only; lines: 95% bootstrap clustered by question (20,000 "
          "resamples, seed 0). Under each name: its own X of Y pooled over the channels; under each comparison: its "
          "following against the comparison's. Hiding (which R1 reads) is in the reports. "
          f"{DAGGER} the two sides' no-answer shares differ by more than 5 points (counts in the CSV).")
    if draft and not all(res.get("complete") for _, res in reports):
        fig.text(0.985, 0.975, "DRAFT: not every A40 or A42 part is in", ha="right", va="top", fontsize=13,
                 color=ROLE["cue"], weight="bold")
    paths = save(fig, f"a40_{first['qset']}_fixes", rows, out)
    plt.close(fig)
    return paths


def load(path, what, draft):
    res = json.loads(Path(path).read_text())
    if not res.get("complete") and not draft:
        missing = {s: e["missing"] for s, e in res.get("completeness", {}).items() if e.get("missing")}
        raise SystemExit(f"not every {what} part is in ({path}: {res.get('label')}; runs missing {missing or 'unknown'}); "
                         "the figure is drawn once they are, or with --draft")
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a40", default=str(A40), help="finetune/a40.py's a40_<qset>.json (numbers only)")
    ap.add_argument("--a42", default=str(A42), help="finetune/a42.py's a42_<qset>.json; if absent, A40's rows alone")
    ap.add_argument("--out", default=str(OUT), help="where the PNG, SVG and CSV go (default docs/paper/figures/)")
    ap.add_argument("--draft", action="store_true", help="draw an incomplete report, stamped as a draft")
    a = ap.parse_args(argv)
    if not Path(a.a40).exists():
        raise SystemExit(f"no A40 report at {a.a40}")
    reports = [("a40", load(a.a40, "A40", a.draft))]
    if Path(a.a42).exists():
        reports.append(("a40_note", load(a.a42, "A42", a.draft)))
    paths = fig_fixes(reports, a.out, a.draft)
    for p in paths:
        print(p)
    return paths


if __name__ == "__main__":
    main()
