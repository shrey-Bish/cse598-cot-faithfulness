"""A39's figures (Track A's fix round 2: E2, the primary, and the 30 beside it), from the report finetune/a39.py writes
(OUT/a39_<qset>.json, numbers only), in tools/slide_figures.py's style: 16:9, white, colors by role, X of Y beside each
comparison, a CSV of every plotted number, PNG 2000 x 1125 and SVG.

  a39_<qset>_fixes  (a) following (wrong-hint runs ending on the hint's letter) and correct-hint acceptance, pooled
                    over the channels, per system: minus base (R1, Gate 3's rule; its verdict under each row) and minus
                    prompt_only, the one-line instruction (R2; its reading under each row)
  a39_<qset>_parts  (b) each combination minus each of its parts alone (R3, A38's reading): LoRA + note pooled over the
                    channels, the wrapper combinations on the inserted tool turn; following, acceptance and no-hint
                    accuracy. (c) The wrapper alone, wrap minus base on the inserted tool turn (R4, B1's reading), and
                    the check: the pasted block's following difference, exactly 0 (its runs are shared)

Dots: a system minus its comparison, paired by question; lines: the report's 95% bootstrap clustered by question.
Following is in the damage color (a circle), acceptance in the correct color (a diamond), no-hint accuracy and the check
in the comparison gray (a square). A wrapper system's R1 and R2 markers are hollow (diluted by design: most of its
pooled runs are its partner's; the amendment's 9.2); a difference whose two sides' no-answer shares are more than 5
points apart carries a dagger (9.1). "too few questions" and "missing runs" are written where a dot would be.

Drawn only after every A39 part is in (the report's "complete"; A39 was read Nov 7, once complete, by its rules): an
incomplete report is refused unless --draft, which stamps every figure as a draft. The headlines say only what the
readings say (written once A39 was read): the fixes figure, R2's "fewer than the instruction" systems, a wrapper system
marked diluted by design, with the acceptance difference beside each, then R1's verdicts; the parts figure, what marking
does alone (R4) and added to the note and to LoRA (R3), with those differences on the inserted tool turn.

  python tools/a39_figures.py --report results/summaries/trackA/gpu/a39/a39_e2.json      # -> docs/paper/figures/
  python tools/a39_figures.py --report OUT/a39_e2.json --out SOMEWHERE [--draft]
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

from paper_figures import GRID, INK, MUTED  # noqa: E402
from slide_figures import CLUSTERED, OUT, ROLE, SIZE, WHITE, save, style  # noqa: E402

REPORT = CODE / "results" / "summaries" / "trackA" / "gpu" / "a39" / "a39_e2.json"
SYSTEMS = ("base", "prompt_only", "lora", "lora_note", "wrap", "wrap_note", "lora_wrap")        # eval.A39_SYSTEMS
SHARED = {"wrap": "base", "wrap_note": "prompt_only", "lora_wrap": "lora"}                     # eval.SHARED
NAMES = {"base": "base", "prompt_only": "the instruction", "lora": "LoRA", "lora_note": "LoRA + note",
         "wrap": "wrapper", "wrap_note": "wrapper + note", "lora_wrap": "LoRA + wrapper"}
SETS = {"e2": "E2", "mmlupro_30": "the 30"}
MEASURES = {"following": ("follows the wrong hint", ROLE["damage"], "o"),
            "acceptance": ("takes the correct hint", ROLE["correct"], "D"),
            "accuracy": ("no-hint accuracy", ROLE["baseline"], "s")}
FEW, MISSING = "too few questions", "missing runs"
PAIRED = CLUSTERED + ", paired"
DAGGER = "†"
SHORT = {"fewer wrong hints followed": "following", "no-hint accuracy within 5 points": "accuracy",
         "hiding doesn't rise": "hiding"}


# ---------------------------------------------------------------- the rows (every plotted number)
def rate(res, system, measure, channel):
    """A system's own X of Y on a measure (a39.summary): following and acceptance per channel or pooled, accuracy on the
    no-hint runs."""
    e = res["systems"].get(system, {})
    got = e.get("accuracy") if measure == "accuracy" else e.get(measure, {}).get(channel)
    return got or {}


def row(res, panel, system, against, channel, measure, d, reading="", note=""):
    """One plotted difference: value, low, high (fractions, the report's), its questions, both sides' X of Y and
    no-answer counts. d None: the reading's runs are missing."""
    d = d or {"diff": None, "interval": MISSING, "questions": 0}
    drawn = d["diff"] is not None
    na = d.get("no_answer") or {"a": {}, "b": {}, "imbalance": False}
    rch = "pooled" if channel == "no hint" else channel
    own, other = rate(res, system, measure, rch), rate(res, against, measure, rch)
    return {"panel": panel, "system": system, "against": against, "channel": channel, "measure": measure,
            "value": d["diff"] if drawn else "", "low": d["interval"][0] if drawn else "",
            "high": d["interval"][1] if drawn else "", "questions": d["questions"],
            "interval": PAIRED if drawn else d["interval"], "k": own.get("k", ""), "n": own.get("n", ""),
            "compared_k": other.get("k", ""), "compared_n": other.get("n", ""),
            "no_answer_k": na["a"].get("k", ""), "no_answer_n": na["a"].get("n", ""),
            "compared_no_answer_k": na["b"].get("k", ""), "compared_no_answer_n": na["b"].get("n", ""),
            "no_answer_imbalance": "yes" if na["imbalance"] else "", "reading": reading, "note": note}


def verdict(e):
    return e["verdict"] + (f" ({'; '.join(e['failed'])})" if e.get("failed") else "")


def fixes_rows(res):
    """(a) R1 and R2, following and acceptance pooled: minus base (the verdict) and minus prompt_only (the reading)."""
    out = []
    for against, block, keys, read in (("base", "r1", ("following_vs_base", "acceptance_vs_base"), verdict),
                                       ("prompt_only", "r2", ("following", "acceptance"), lambda e: e["reading"])):
        for s in SYSTEMS:
            e = res[block].get(s)
            if e:
                out += [row(res, "a", s, against, "pooled", m, e[k], read(e), "diluted by design" if "note" in e else "")
                        for m, k in zip(("following", "acceptance"), keys)]
    return out


def parts_rows(res):
    """(b) R3: each combination minus each part, three measures, its reading; (c) R4: wrap minus base on the inserted
    turn, three measures, B1's reading, and the pasted block's check."""
    out = []
    for combo, e in res["r3"].items():
        for p in e["against"]:
            for m in MEASURES:
                out.append(row(res, "b", combo, p, "no hint" if m == "accuracy" else e["channel"], m,
                               e.get(f"minus {p}", {}).get(m), e["reading"]))
    r = res["r4"]
    for m in MEASURES:
        out.append(row(res, "c", "wrap", "base", "no hint" if m == "accuracy" else "inserted", m, r.get(m), r["reading"],
                       "shared runs: exactly 0 by design" if m == "accuracy" else ""))
    check = r.get("pasted_check", {})
    out.append(row(res, "c", "wrap", "base", "pasted", "following", check.get("following_minus_base"),
                   f"exactly 0: {check['exactly_zero']}" if check else MISSING, "the check: shared runs"))
    return out


# ---------------------------------------------------------------- drawing
def points(v):
    return "0" if abs(v) < 0.005 else f"{v * 100:+.0f}".replace("-", "−")


def dot(ax, y, r, hollow=False):
    """One difference at row y: its interval and dot (hollow: diluted by design), the dagger for a no-answer imbalance;
    "too few questions" or "missing runs" written where the dot would be."""
    _, color, marker = MEASURES[r["measure"]]
    if r["value"] == "":
        ax.text(0, y, r["interval"], ha="center", va="center", fontsize=9.5, color=MUTED, style="italic",
                bbox={"boxstyle": "square,pad=0.1", "facecolor": WHITE, "edgecolor": "none"}, zorder=4)
        return
    v, lo, hi = r["value"] * 100, r["low"] * 100, r["high"] * 100
    ax.plot([lo, hi], [y, y], color=color, linewidth=2.2, solid_capstyle="butt", zorder=2)
    ax.plot(v, y, marker, color=color, markersize=9 if marker == "o" else 8, zorder=3,
            markerfacecolor=WHITE if hollow else color, markeredgecolor=color if hollow else WHITE,
            markeredgewidth=1.8 if hollow else 1.2)
    ax.annotate(points(r["value"]) + (f" {DAGGER}" if r["no_answer_imbalance"] else ""), (hi, y), xytext=(5, 0),
                textcoords="offset points", va="center", fontsize=9.5, color=INK, zorder=4,
                bbox={"boxstyle": "square,pad=0.05", "facecolor": WHITE, "edgecolor": "none"})


def row_of_dots(ax, y, rs, offsets, hollow=False):
    """A row's differences, one dot each at y + its offset; when none can be drawn, the reason once, at y."""
    if all(rs[m]["value"] == "" for m, _ in offsets):
        dot(ax, y, rs[offsets[0][0]])
        return
    for m, dy in offsets:
        dot(ax, y + dy, rs[m], hollow)


def frame(ax, rows, ylim, max_ticks=None):
    """A difference axis: a zero line, recessive grid, x in points from the rows' intervals (at least -10 to +10); ticks
    every 10 points, or every 20 when more than max_ticks would crowd a narrow panel."""
    vals = [x * 100 for r in rows if r["value"] != "" for x in (r["low"], r["high"])] or [0]
    lo, hi = min(-10, (min(vals) // 10) * 10 - 5), max(10, -(-max(vals) // 10) * 10 + 10)
    ax.set_xlim(lo, hi)
    ax.set_ylim(*ylim)
    ax.axvline(0, color=MUTED, linewidth=1.0, zorder=1)
    ticks = [t for t in range(-200, 201, 10) if lo <= t <= hi]
    ax.set_xticks(ticks if not max_ticks or len(ticks) <= max_ticks else [t for t in ticks if t % 20 == 0])
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", color=GRID)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("difference (points)")


def label(fig, ax, x, y, title, sub="", bold=False):
    """A row label in figure x, data y: the name in ink, its X of Y under it in muted ink."""
    from matplotlib.transforms import blended_transform_factory
    t = blended_transform_factory(fig.transFigure, ax.transData)
    ax.text(x, y + 0.08, title, transform=t, fontsize=11.5, color=INK, va="bottom", weight="bold" if bold else "normal",
            clip_on=False)
    if sub:
        ax.text(x, y - 0.02, sub, transform=t, fontsize=9.5, color=MUTED, va="top", clip_on=False)


def xofy(r):
    return f"{r['k']} of {r['n']}" if r["n"] != "" else "no runs"


def legend(fig, plt, x, y, measures, extra=True):
    handles = [plt.Line2D([], [], color=MEASURES[m][1], marker=MEASURES[m][2], linewidth=2.2, markersize=8,
                          markeredgecolor=WHITE) for m in measures]
    names = [MEASURES[m][0] for m in measures]
    if extra:
        handles.append(plt.Line2D([], [], color=MUTED, marker="o", linewidth=0, markersize=8, markerfacecolor=WHITE,
                                  markeredgewidth=1.8))
        names.append("a wrapper system: diluted by design")
    fig.legend(handles, names, loc="lower left", bbox_to_anchor=(x, y), ncol=len(handles), frameon=False, fontsize=11)


def words(fig, headline, sub, foot):
    """The headline (ink, wrapped), what the readings say (ink, wrapped, under it) and the method line at the foot
    (muted, wrapped)."""
    head = textwrap.fill(headline, 120)
    fig.text(0.015, 0.955, head, fontsize=15, color=INK, va="top", linespacing=1.25)
    fig.text(0.015, 0.905 - 0.033 * head.count("\n"), textwrap.fill(sub, 140), fontsize=12.5, color=INK, va="top",
             linespacing=1.3)
    fig.text(0.015, 0.012, textwrap.fill(foot, 168), fontsize=10, color=MUTED, linespacing=1.35)


def ci(d):
    """A difference in points with its interval, "−14 [−20, −9]"; "too few questions" or "missing runs" if not
    drawn."""
    if not d:
        return MISSING
    if d.get("diff") is None:
        return FEW
    return f"{points(d['diff'])} [{points(d['interval'][0])}, {points(d['interval'][1])}]"


def named(systems):
    """Systems by name, a wrapper system marked: its pooled R1 and R2 are diluted by design (the amendment's 9.2)."""
    return ", ".join(NAMES[s] + (" (diluted by design)" if s in SHARED else "") for s in systems)


def fixes_words(res):
    """(headline, sentence) of the fixes figure, the readings' words only: R2's "fewer than the instruction" systems,
    the acceptance difference beside each (R2 reads following only), then R1's verdicts."""
    name, n = SETS.get(res["qset"], res["qset"]), res["questions"]
    fewer = [s for s in SYSTEMS if res["r2"].get(s, {}).get("reading") == "fewer than the instruction"]
    passed = [s for s in SYSTEMS if res["r1"].get(s, {}).get("verdict") == "passes"]
    failed = [s for s in SYSTEMS if s in res["r1"] and res["r1"][s].get("verdict") != "passes"]
    head = (f"A39 on {name} ({n} questions): fewer wrong hints followed than the one-line instruction (R2): "
            f"{named(fewer) or 'none'}.")
    beside = "; ".join(f"{NAMES[s]} {ci(res['r2'][s]['acceptance'])}" for s in fewer)
    sub = ((f"Correct-hint acceptance minus the instruction, beside it (not read by R2): {beside}. " if fewer else "")
           + f"Gate 3's rule against base (R1) passes: {named(passed) or 'none'}"
           + (f"; fails: {named(failed)}" if failed else "")
           + ". A wrapper system's informative readings are R3 and R4, on the inserted tool turn (the parts figure).")
    return head, sub


def parts_words(res):
    """(headline, sentence) of the parts figure, the readings' words only: what marking does alone (R4) and added to
    the note and to LoRA (R3), with those differences on the inserted tool turn; LoRA + note's R3 beside."""
    name, r3, r4 = SETS.get(res["qset"], res["qset"]), res["r3"], res["r4"]
    reading = lambda s: r3.get(s, {}).get("reading", MISSING)  # noqa: E731
    pair = lambda d: f"follows {ci(d.get('following'))}, takes {ci(d.get('acceptance'))}"  # noqa: E731
    head = (f'A39 on {name}: the wrapper alone, "{r4["reading"]}" (R4); wrapper + note, "{reading("wrap_note")}", and '
            f'LoRA + wrapper, "{reading("lora_wrap")}" (R3).')
    sub = (f"On the inserted tool turn: wrapper − base {pair(r4)}; wrapper + note − the instruction "
           f"{pair(r3.get('wrap_note', {}).get('minus prompt_only') or {})}; LoRA + wrapper − LoRA "
           f"{pair(r3.get('lora_wrap', {}).get('minus lora') or {})}. "
           f'LoRA + note, pooled (R3): "{reading("lora_note")}".')
    return head, sub


def stamp(fig, res, draft):
    if draft and not res.get("complete"):
        fig.text(0.985, 0.975, "DRAFT: not every A39 part is in", ha="right", va="top", fontsize=13, color=ROLE["cue"],
                 weight="bold")


def fig_fixes(res, out, draft=False):
    plt = style()
    rows = fixes_rows(res)
    name = SETS.get(res["qset"], res["qset"])
    fig = plt.figure(figsize=SIZE)
    axes = {"base": fig.add_axes([0.215, 0.24, 0.355, 0.5]), "prompt_only": fig.add_axes([0.625, 0.24, 0.355, 0.5])}
    ys = {s: len(SYSTEMS) - 1 - i for i, s in enumerate(SYSTEMS)}
    for against, ax in axes.items():
        mine = [r for r in rows if r["against"] == against]
        frame(ax, rows, (-0.75, len(SYSTEMS) - 0.35))
        for s in SYSTEMS:
            rs = {r["measure"]: r for r in mine if r["system"] == s}
            y = ys[s]
            if s == against:
                ax.text(0, y, "the comparison", ha="center", va="center", fontsize=9.5, color=MUTED, style="italic")
                continue
            if not rs:
                ax.text(0, y, MISSING, ha="center", va="center", fontsize=9.5, color=MUTED, style="italic")
                continue
            row_of_dots(ax, y, rs, (("following", 0.24), ("acceptance", -0.04)), hollow=s in SHARED)
            ax.text(ax.get_xlim()[0], y - 0.35, rs["following"]["reading"], fontsize=9.5, color=MUTED, va="center",
                    ha="left", style="italic")
        for y in range(len(SYSTEMS) - 1):
            ax.axhline(y + 0.5, color=GRID, linewidth=0.8, zorder=0)
    titles = {"base": "(a) Minus base: R1, Gate 3's rule (its verdict under each)",
              "prompt_only": "Minus the one-line instruction: R2 (its reading)"}
    for against, ax in axes.items():
        ax.set_title(titles[against], loc="left", color=INK, fontsize=13)
    for s in SYSTEMS:
        f, a = rate(res, s, "following", "pooled"), rate(res, s, "acceptance", "pooled")
        sub = f"follows {f.get('k', '-')} of {f.get('n', '-')}, takes {a.get('k', '-')} of {a.get('n', '-')}"
        label(fig, axes["base"], 0.015, ys[s], NAMES[s] + (f" ({s})" if s != NAMES[s] else ""), sub)
    legend(fig, plt, 0.01, 0.112, ("following", "acceptance"))
    words(fig, *fixes_words(res),
          f"A39, pre-registered Nov 3 (the A39 log's sections 4 and 9): {name}, 12 runs a question a system (a wrapper "
          "system runs its 4 inserted-turn runs and shares the rest with its partner). Dots: the system minus the "
          "comparison, paired by question, answered runs only; lines: 95% bootstrap clustered by question (20,000 "
          f"resamples, seed 0). Under each name: its own X of Y, pooled over the channels. {DAGGER} the two sides' "
          "no-answer shares differ by more than 5 points (counts in the CSV).")
    stamp(fig, res, draft)
    paths = save(fig, f"a39_{res['qset']}_fixes", rows, out)
    plt.close(fig)
    return paths


def fig_parts(res, out, draft=False):
    plt = style()
    rows = parts_rows(res)
    fig = plt.figure(figsize=SIZE)
    ax_b, ax_c = fig.add_axes([0.215, 0.24, 0.36, 0.5]), fig.add_axes([0.78, 0.24, 0.205, 0.5])
    b = [r for r in rows if r["panel"] == "b"]
    combos = list(dict.fromkeys(r["system"] for r in b))
    y, ys = 0.0, {}
    for combo in reversed(combos):
        for p in reversed(list(dict.fromkeys(r["against"] for r in b if r["system"] == combo))):
            ys[(combo, p)] = y
            y += 1
        y += 0.75
    frame(ax_b, b, (-0.6, y - 0.55))
    for (combo, p), yy in ys.items():
        mine = {r["measure"]: r for r in b if r["system"] == combo and r["against"] == p}
        row_of_dots(ax_b, yy, mine, (("following", 0.24), ("acceptance", 0.0), ("accuracy", -0.24)))
        f = mine["following"]
        label(fig, ax_b, 0.015, yy, f"minus {NAMES[p]}", f"{f['channel']}: follows {xofy(f)} vs {f['compared_k']} "
              f"of {f['compared_n']}" if f["n"] != "" else f"{f['channel']}: no runs")
    for combo in combos[:-1]:                                      # a line under each but the last
        ax_b.axhline(min(yy for (c, _), yy in ys.items() if c == combo) - 0.55, color=GRID, linewidth=0.8, zorder=0)
    for combo in combos:                                 # the name in the label column, its reading in the panel
        top = max(yy for (c, _), yy in ys.items() if c == combo)
        reading = next(r["reading"] for r in b if r["system"] == combo)
        label(fig, ax_b, 0.015, top + 0.62, f"{NAMES[combo]} (R3):", bold=True)
        ax_b.text(ax_b.get_xlim()[0], top + 0.70, f" {reading}", fontsize=11.5, color=INK, va="bottom", ha="left",
                  weight="bold", style="italic", zorder=4,
                  bbox={"boxstyle": "square,pad=0.05", "facecolor": WHITE, "edgecolor": "none"})
    ax_b.set_title("(b) Each combination minus each part alone: R3 (A38's reading)", loc="left", color=INK, fontsize=13)
    c = [r for r in rows if r["panel"] == "c"]
    order = [("following", "inserted"), ("acceptance", "inserted"), ("accuracy", "no hint"), ("following", "pasted")]
    names = {("following", "inserted"): "follows, inserted turn", ("acceptance", "inserted"): "takes, inserted turn",
             ("accuracy", "no hint"): "no-hint accuracy (shared)", ("following", "pasted"): "check: pasted block"}
    frame(ax_c, c, (-0.6, len(order) - 0.4), max_ticks=6)
    for i, key in enumerate(order):
        r = next(x for x in c if (x["measure"], x["channel"]) == key)
        yy = len(order) - 1 - i
        dot(ax_c, yy, r, hollow=key[1] == "pasted")
        label(fig, ax_c, 0.625, yy, names[key], f"{xofy(r)} vs {r['compared_k']} of {r['compared_n']}"
              if r["n"] != "" else "no runs")
    reading = c[0]["reading"]
    ax_c.set_title(f"(c) The wrapper alone: R4\nwrap − base: {reading}", loc="left", color=INK, fontsize=13)
    legend(fig, plt, 0.01, 0.112, tuple(MEASURES), extra=False)
    words(fig, *parts_words(res),
          "R3 (A38's five readings, 5-point margins on acceptance and accuracy): LoRA + note pooled over the wrong-hint "
          "channels; the wrapper combinations on the inserted tool turn, the one channel the wrapper changes. R4: B1's "
          "five readings. Dots: minus the part (or base), paired by question, answered runs only; lines: 95% bootstrap "
          "clustered by question. No-hint accuracy: the no-hint runs, which a wrapper system shares with its partner. "
          f"The check (hollow): exactly 0. {DAGGER} the two sides' no-answer shares differ by more than 5 points.")
    stamp(fig, res, draft)
    paths = save(fig, f"a39_{res['qset']}_parts", rows, out)
    plt.close(fig)
    return paths


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", default=str(REPORT), help="finetune/a39.py's a39_<qset>.json (numbers only)")
    ap.add_argument("--out", default=str(OUT), help="where the PNG, SVG and CSV go (default docs/paper/figures/)")
    ap.add_argument("--draft", action="store_true", help="draw an incomplete report, stamped as a draft")
    a = ap.parse_args(argv)
    res = json.loads(Path(a.report).read_text())
    if not res.get("complete") and not a.draft:
        missing = {s: e["missing"] for s, e in res.get("completeness", {}).items() if e["missing"]}
        raise SystemExit(f"not every A39 part is in ({a.report}: runs missing {missing or 'unknown'}); the figures are "
                         "drawn once they are, or with --draft")
    paths = fig_fixes(res, a.out, a.draft) + fig_parts(res, a.out, a.draft)
    for p in paths:
        print(p)
    return paths


if __name__ == "__main__":
    main()
