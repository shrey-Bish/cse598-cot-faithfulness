"""The final deck's version 3 main slides (DECK_V3, Nov 26): slides 3-9 on the ASU template, with native (editable)
charts from tools/deck/charts.py, and the full fix table (a backup). build_deck.py calls these; run alone, this file
renders the Phase A drafts (slides 3, 4, 5, 6 in two versions, and 8):

    python tools/deck/slides_v3.py     # -> docs/presentation/final/storyboard/draft_v3.pptx (gitignored) and
                                       #    docs/presentation/final/storyboard/v3/slide_*.png (numbers only)

Every plotted number is read from a tracked summary or is a FINDINGS k of n (the Wilson interval computed from it and
checked against FINDINGS' printed bounds); the storyboard (STORYBOARD_V3.md) lists each with its source.
"""
import subprocess
import sys
from pathlib import Path

from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_deck as B  # noqa: E402
import charts as CH  # noqa: E402
import diagram as D  # noqa: E402
import figures as F  # noqa: E402

R, text, rect, notes = B.R, B.text, B.rect, B.notes
MAROON, GOLD, INK, WHITE, GREY, MUTED = CH.MAROON, CH.GOLD, CH.INK, B.WHITE, CH.GREY, CH.MUTED
SB = B.FINAL / "storyboard"
OUT = SB / "draft_v3.pptx"
PNG = SB / "v3"


def pct(k, n):
    lo, hi = F.wilson(k, n)
    return 100 * k / n, 100 * lo, 100 * hi


def check_iv(k, n, lo, hi):
    """FINDINGS prints Wilson bounds as whole percents: the computed bounds must round to them."""
    a, b = F.wilson(k, n)
    assert (round(100 * a), round(100 * b)) == (lo, hi), (k, n, a, b, lo, hi)


def badge(s, x, y, label, fill=MAROON, size=0.34):
    o = rect(s, x, y, size, size, fill=fill, shape=MSO_SHAPE.OVAL, name="deck badge")
    tf = o.text_frame
    for side in ("left", "right", "top", "bottom"):
        setattr(tf, f"margin_{side}", Inches(0))
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    r = p.add_run()
    r.text = label
    r.font.name, r.font.size, r.font.bold, r.font.color.rgb = D.FONT, Pt(13), True, WHITE if fill != GOLD else INK
    return o


def arrow_right(s, x, y, w=0.22):
    a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(0.26))
    a.name = "deck arrow"
    D._no_effect(a)
    a.fill.solid()
    a.fill.fore_color.rgb = INK
    a.line.fill.background()
    return a


# ---------------------------------------------------------------- slide 3: what we built
EFFORT = [  # (number, label); sources in STORYBOARD_V3 section 3
    ("352", "GPU-hours on Sol\n(271 GPU jobs)"),
    ("5", "trained\nversions"),
    ("31", "rules written\nbefore the data"),
    ("479", "answers\nlabelled by hand"),
    ("1,400+", "automated\ntests"),
    ("Nov 18", "results frozen,\nthen reported"),
]


def slide3(prs, effort=EFFORT):
    s = B.white(prs, "What we built")
    blocks = [
        ("The test harness", ["Same question, same wrong letter; only the source changes (the user, a stronger claim, "
                              "pasted tool output, its own tool call).",
                              "8 open models (12 with the reviewers), thinking on and off; on Sol and Voyager."]),
        ("Inside the model", ["Activation patching: swap one layer's activations between a hinted and an unhinted run, "
                              "across all 32 layers of Olmo 3 7B Think.",
                              "Then the same test in a second model."]),
        ("Training the fixes", ["Fine-tuning (LoRA), from 1,196 examples.",
                                "Consistency training, from 981 examples of the model's own hint-free reasoning.",
                                "Tested on 120 fresh questions, 12 runs each."]),
        ("The multi-agent check", ["Solver with the tool → reviewer (6 models, up to 4 views of the solver's work) → "
                                   "checker that re-solves without the tool."]),
    ]
    x0, y0, gapw, h = 0.37, 0.93, 0.26, 2.66
    w = (9.26 - 3 * gapw) / 4
    for i, (head, facts) in enumerate(blocks):
        x = x0 + i * (w + gapw)
        rect(s, x, y0, w, h, fill=RGB_LIGHT, name=f"deck block {i + 1}")
        badge(s, x + 0.1, y0 + 0.14, str(i + 1))
        text(s, x + 0.52, y0 + 0.06, w - 0.58, 0.56, [([R(head, 16, True, MAROON)], 0)], anchor=MSO_ANCHOR.MIDDLE,
             name="deck block head")
        text(s, x + 0.12, y0 + 0.7, w - 0.22, h - 0.74, [([R(f, 11)], 3) for f in facts], name="deck block text")
        if i < 3:
            arrow_right(s, x + w + 0.02, y0 + h / 2 - 0.13)
    # the effort band
    yb, hb = 3.68, 1.0
    rect(s, 0.37, yb, 9.26, hb, fill=INK, name="deck effort band")
    cw = 9.26 / len(effort)
    for i, (num, lab) in enumerate(effort):
        text(s, 0.37 + i * cw, yb + 0.06, cw, 0.46, [([R(num, 24, True, GOLD)], 0)], align=PP_ALIGN.CENTER,
             name="deck effort number")
        text(s, 0.37 + i * cw + 0.05, yb + 0.52, cw - 0.1, 0.44, [([R(ln, 12, False, WHITE)], 0) for ln in lab.split("\n")],
             align=PP_ALIGN.CENTER, name="deck effort label")
    notes(s, "Speaker: Ritik. Time: 0:55 (0:40-1:35).\n"
             "- Four things we built, left to right: the test harness (only the source of the same wrong letter changes); "
             "inside the model (activation patching, Olmo 3 7B Think, then Qwen3 8B); training the fixes (LoRA, "
             "consistency training; tested on the 120 fresh questions); the multi-agent check (solver, reviewer, checker).\n"
             "- Why: paired by question, so difficulty cancels; multiple choice, so following is unambiguous; right hints "
             "too, so over-correction shows; rules written before the data.\n"
             "- The band: 352.47 GPU-hours, 271 GPU jobs on Sol since Oct 1 (Ritik's account; Arsha's B20 runs not in "
             "it); 5 trained versions (LoRA, tags, LoRA + tags, LoRA on layers 15/19/23, consistency); 31 of the "
             "ledger's 42 rows pre-registered; 479 rows labelled by hand (101 + 294 + 84; the first sheet's agreement "
             "was below the bar, F3); 1,413 tests in the last full run; frozen Nov 18. 1,196 examples = 1,040 to train "
             "+ 156 to validate; 981 = 881 + 100. 12 models = 8 that answer + 4 reviewers.\n"
             "- Hand-off to Arsha: 'First, the failure itself.'")
    return s


RGB_LIGHT = B.GRAY


# ---------------------------------------------------------------- slide 4: the failure, across models
def slide4(prs):
    s = B.white(prs, "The failure: tools pull harder, and the answer hides it")
    data = sorted(F.models_data("v3_s4"), key=lambda d: -d["tool"][0])
    cats = [f"{d['short']} ({'own call' if d['own'] else 'inserted turn'})\n"
            f"{d['ukn'][0]}/{d['ukn'][1]} vs {d['tkn'][0]}/{d['tkn'][1]}" for d in data]
    ser = []
    for key, name, col in (("user", "from the user's guess", GOLD), ("tool", "from a tool", MAROON)):
        ser.append({"name": name, "color": col, "values": [100 * d[key][0] for d in data],
                    "low": [100 * d[key][1] for d in data], "high": [100 * d[key][2] for d in data]})
    text(s, 0.37, 0.92, 5.3, 0.3, [([R("Runs that took the wrong letter", 12, True)], 0)], name="deck chart head")
    CH.bars(s, 0.30, 1.14, 5.45, 3.62, cats, ser, horizontal=True, gap=35, overlap=-5, fs=11, legend_pos="bottom",
            name="chart tool vs user",
            alt="Bar chart: for seven models, the share of runs that took a wrong letter when it came from the user's "
                "guess against from a tool; the tool's bar is higher in every row. Counts under each model name; "
                "95% Wilson intervals.")
    # right: who names the tool after a call
    t = F.J(F.TRACKB)["budget_32768"]
    q8 = t["sol_vllm | qwen3-8b | thinking=True"]["channels"]["tool_real"]
    q30 = t["voyager | qwen3-30b-a3b-thinking-2507 | thinking=None"]["channels"]["tool_real"]
    g = F.J(F.B20)["gemma-4-26b-a4b-it"]["settings"]["off"]["budget_32768"]["secondary"]["channels"]["tool_injected"]
    kn = lambda e: (e["k"], e["n"])  # noqa: E731
    rows = [("Qwen3 8B", kn(q8["mention_private_when_called"]), kn(q8["mention_final_when_followed"])),
            ("Qwen3 30B Thinking", kn(q30["mention_private_when_called"]), kn(q30["mention_final_when_followed"])),
            ("Gemma 4, thinking off", None, kn(g["mention_final"]))]
    cats2 = [f"{nm}\n{p[0]}/{p[1]} vs {a[0]}/{a[1]}" if p else f"{nm}\nno reasoning; {a[0]}/{a[1]}" for nm, p, a in rows]
    ser2 = []
    for j, (name, col) in enumerate((("reasoning names the tool", MAROON), ("final answer names it", GOLD))):
        vals, lo, hi = [], [], []
        for nm, p, a in rows:
            e = (p, a)[j]
            if e is None:
                vals.append(None), lo.append(None), hi.append(None)
                continue
            v, l_, h_ = pct(*e)
            vals.append(v), lo.append(l_), hi.append(h_)
        ser2.append({"name": name, "color": col, "values": vals, "low": lo, "high": hi})
    text(s, 5.95, 0.92, 3.7, 0.3, [([R("After a tool call: who names the tool", 12, True)], 0)], name="deck chart head")
    CH.bars(s, 5.88, 1.14, 3.78, 2.72, cats2, ser2, horizontal=True, gap=60, overlap=-5, fs=11, major=50,
            legend_pos="bottom", name="chart reasoning vs answer",
            alt="Bar chart: after a tool call, the share of runs whose private reasoning names the tool against "
                "whose final answer does, for Qwen3 8B, Qwen3 30B Thinking and Gemma 4 with thinking off (no "
                "reasoning; its answer names the tool most of the time). 95% Wilson intervals.")
    text(s, 5.95, 3.98, 3.68, 0.75, [([R("Did thinking make it more honest? Mixed.", 17, True, MAROON)], 0)],
         name="deck bottom line")
    notes(s, "Speaker: Arsha. Time: 0:35 (1:35-2:10).\n"
             "- Left (F16, FB1): the same wrong letter from the user or a tool; the tool's bar is higher in every row "
             "(Qwen3 30B Instruct 1 of 162 vs 147 of 162). Every model tested; gpt-oss reported without a decision, run after its window (F37).\n"
             "- Right (F29, F15, FB1): reasoning 141 of 145 vs answer 0 of 143 (Qwen3 8B); 54 of 54 vs 3 of 54; Gemma 4 "
             "off 127 of 162, the exception.\n"
             "- Mixed: Qwen3 8B +64 [+51, +75]; gpt-oss +7 [-1, +16]; Nemotron -14 [-19, -9].\n"
             "- Hand-off: 'So where in the model does the tool's letter take over?'")
    return s


# ---------------------------------------------------------------- slide 6: training
FIXES = [  # (name, wrong followed k/n + printed bounds, right taken k/n + printed bounds); FINDINGS F41 table, A42
    ("No fix", (297, 703, 39, 46), (439, 476, 89, 94)),
    ("One-line instruction", (237, 713, 30, 37), (431, 476, 88, 93)),
    ("Fine-tuned (LoRA)", (248, 705, 32, 39), (421, 477, 85, 91)),
    ("Consistency-trained", (84, 694, 10, 15), (347, 459, 71, 79)),
    ("Consistency + instruction", (64, 706, 7, 11), (334, 472, 67, 75)),
]


def fixes_series(color_of):
    for _, w, r in FIXES:
        check_iv(*w), check_iv(*r)
    out = []
    for j, name in enumerate(("wrong hints followed (lower is better)", "right tool hints taken (higher is better)")):
        vals, lo, hi, pcs = [], [], [], []
        for i, f in enumerate(FIXES):
            v, a, b = pct(*f[1 + j][:2])
            vals.append(v), lo.append(a), hi.append(b), pcs.append(color_of(i, j))
        out.append({"name": name, "values": vals, "low": lo, "high": hi, "point_colors": pcs})
    return out


def training_side(s, x, y, w):
    text(s, x, y, w, 2.9, [
        ([R("What training changed", 13, True, MAROON)], 6),
        ([R("Fine-tuned: ", 12, True), R("when it still follows, its answer says so in 37 of 42, against the "
                                          "instruction's 18 of 42 (+45 points [+25, +64]); it follows about as often "
                                          "(no difference detected).", 12)], 6),
        ([R("Inside: ", 12, True), R("fine-tuning changes the reasoning it writes, not the pull; consistency training "
                                      "removes part of the pull (+0.68 logits [+0.17, +1.18]), before the readout "
                                      "layers (0–14).", 12)], 6),
        ([R("No-hint accuracy stayed within 5 points for every version.", 11, False, MUTED)], 0)], name="deck side")


def training_notes(s):
    notes(s, "Speaker: Arsha. Time: 0:50 (2:40-3:30).\n"
             "- Against no fix (F43, R1 Gate 3's rule): consistency training -30 [-35, -26] wrong hints followed; right "
             "hints taken 439 of 476 -> 347 of 459 (-17 [-22, -12]).\n"
             "- Against the instruction (F43): -21 [-26, -16] following, -15 [-20, -10] acceptance: 'fewer, but costs "
             "acceptance'. LoRA against no fix on the 30: -10 [-16, -4].\n"
             "- Candour (F45): 37 of 42 vs 18 of 42. Inside (F42): +0.68 logits [+0.17, +1.18], layers 0-14.\n"
             "- Exploratory crossover about 0.36 [0.22, 0.50] (tradeoff_e2).\n"
             "- Wrong hints pool the user, pasted and inserted channels (F41's measure); right hints are the two tool "
             "channels. Not on the chart: LoRA + instruction beats the instruction on following alone (-8 [-12, -4]) "
             "at an acceptance cost (-9 [-13, -5]): 'met by no fix' (F43).\n"
             "- Hand-off: 'Here is what that looks like on one question.'")


BOTTOM6 = ("No fix beat the one-line instruction without refusing more right answers; how often your tool is right "
           "decides which to use (exploratory: about 36%).")


def legend_key(s, x, y, color, label, size=11, w=3.0):
    rect(s, x, y + 0.04, 0.16, 0.16, fill=color, name="deck legend key")
    text(s, x + 0.22, y, w, 0.24, [([R(label, size)], 0)], name="deck legend")


PLOT = (0.01, 0.02, 0.97, 0.86)  # the inner plot area, as fractions of the chart frame


def slide6a(prs):
    """As the brief asks: one paired chart, two bars per version; names and counts as text beside the rows."""
    s = B.white(prs, "Training cut wrong-hint following from 42% to 12%, at a cost")
    ser = fixes_series(lambda i, j: None)
    ser[0]["color"], ser[1]["color"] = MAROON, GOLD
    legend_key(s, 0.37, 0.93, MAROON, "wrong hints followed, from the user or a tool (lower is better)", w=5.5)
    legend_key(s, 0.37, 1.19, GOLD, "right tool hints taken (higher is better)", w=5.5)
    cy, ch_ = 1.46, 2.68
    CH.bars(s, 2.55, cy, 3.9, ch_, [f[0] for f in FIXES], ser, horizontal=True, gap=30, overlap=-5, fs=11,
            legend=False, plot=PLOT, cat_labels=False, name="chart training",
            alt="Bar chart: five versions of Olmo 3 7B Think on 120 fresh questions; for each, the share of wrong "
                "hints followed and of right tool hints taken, with counts beside each name and 95% Wilson intervals. "
                "Consistency training follows far fewer wrong hints and takes fewer right ones.")
    for i, (yc, (nm, w, r)) in enumerate(zip(CH.rows_y(cy, ch_, PLOT, 5), FIXES)):
        col = MAROON if i == 3 else INK
        text(s, 0.30, yc - 0.24, 2.17, 0.5, [([R(nm, 12, True, col)], 0), ([R(f"{w[0]}/{w[1]} · {r[0]}/{r[1]}", 11)], 0)],
             align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE, name="deck row label")
    y3 = CH.rows_y(cy, ch_, PLOT, 5)[3]
    text(s, 3.3, y3 - 0.24, 3.1, 0.22, [([R("−30 points [−35, −26] vs no fix", 11, True, MAROON)], 0)],
         name="deck callout")
    text(s, 5.68, y3 + 0.02, 0.85, 0.22, [([R("92% → 76%", 11, True, MAROON)], 0)], name="deck callout")
    training_side(s, 6.65, 0.95, 2.98)
    text(s, 0.37, 4.18, 9.26, 0.55, [([R(BOTTOM6, 13, True, INK)], 0)], name="deck bottom line")
    training_notes(s)
    return s


def slide6b(prs):
    """Alternative: two panels on the same rows; no fix gold, consistency maroon, the rest grey."""
    s = B.white(prs, "Training cut wrong-hint following from 42% to 12%, at a cost")
    col = lambda i, j: GOLD if i == 0 else MAROON if i == 3 else GREY  # noqa: E731
    ser = fixes_series(col)
    cy, ch_ = 1.56, 2.58
    ys = CH.rows_y(cy, ch_, PLOT, 5)
    panels = [(2.62, 1.80, "Wrong hints followed", "user or tool; lower is better", "42% → 12%", 1),
              (4.98, 1.55, "Right tool hints taken", "higher is better", "92% → 76%: the cost", 2)]
    for j, (x, w, h1, h2, h3, k) in enumerate(panels):
        text(s, x - 0.62, 0.9, w + 0.75, 0.66, [([R(h1, 12, True)], 0), ([R(h2, 11, False, MUTED)], 0),
                                                ([R(h3, 11, True, MAROON)], 0)], name="deck chart head")
        CH.bars(s, x, cy, w, ch_, [f[0] for f in FIXES], [dict(ser[j], color=GREY)], horizontal=True, gap=35, fs=11,
                legend=False, major=50, plot=PLOT, cat_labels=False,
                name=f"chart training {'wrong' if j == 0 else 'right'}",
                alt=("Bar chart: share of wrong hints (from the user or a tool) followed by five versions of Olmo 3 7B Think on 120 fresh "
                     "questions, with counts and 95% Wilson intervals; consistency training is lowest." if j == 0 else
                     "Bar chart: share of right tool hints taken by the same five versions, with counts and 95% "
                     "Wilson intervals; consistency training takes fewer."))
        for yc, f in zip(ys, FIXES):
            text(s, x - 0.66, yc - 0.12, 0.6, 0.24, [([R(f"{f[k][0]}/{f[k][1]}", 11)], 0)], align=PP_ALIGN.RIGHT,
                 anchor=MSO_ANCHOR.MIDDLE, name="deck row count")
    text(s, 3.0, ys[3] - 0.12, 1.4, 0.24, [([R("−30 [−35, −26]", 11, True, MAROON)], 0)], anchor=MSO_ANCHOR.MIDDLE,
         name="deck callout")
    for i, (yc, f) in enumerate(zip(ys, FIXES)):
        text(s, 0.30, yc - 0.22, 1.62, 0.44, [([R(f[0], 12, True, MAROON if i == 3 else INK)], 0)],
             align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE, name="deck row label")
    training_side(s, 6.75, 0.95, 2.88)
    text(s, 0.37, 4.18, 9.26, 0.55, [([R(BOTTOM6, 13, True, INK)], 0)], name="deck bottom line")
    training_notes(s)
    return s



# ---------------------------------------------------------------- slide 5: inside the model
def slide5(prs):
    s = B.white(prs, "Inside the model: three layers read the hint")
    h = F.J("trackA/step10_handoff.json")["handoff"]["by_cut_type"]["ii"]["all"]
    layers = h["drop_by_layer"]
    tot = h["drop_share_readout"]
    assert (round(tot["mean"], 2), round(tot["low"], 2), round(tot["high"], 2)) == (0.90, 0.85, 0.96)
    hot = (15, 19, 23)
    ser = [{"name": "share of the hint's effect", "color": GREY, "values": [e["mean"] for e in layers],
            "low": [e["low"] for e in layers], "high": [e["high"] for e in layers],
            "point_colors": [MAROON if i in hot else None for i in range(32)]}]
    plot = (0.09, 0.03, 0.89, 0.80)
    x, y, w, hh = 0.30, 1.0, 6.1, 3.15
    text(s, 0.37, 0.92, 6.0, 0.3, [([R("Each layer's share of the hint's effect, where the reasoning turns to the hint",
                                       12, True)], 0)], name="deck chart head")
    CH.bars(s, x, y + 0.2, w, hh, [str(i) for i in range(32)], ser, vmin=-0.1, vmax=0.45, major=0.1,
            number_format="0.0", gap=35, fs=11, legend=False, plot=plot, cat_labels=False, name="chart layers",
            alt="Column chart: for each of Olmo 3 7B Think's 32 layers, its share of the hint's effect at the point "
                "the reasoning turns to the hint, with 95% intervals; layers 15, 19 and 23 (maroon) carry almost all "
                "of it, the other 29 (grey) are near zero.")
    xs = CH.cols_x(x, w, plot, 32)
    ybase = y + 0.2 + (plot[1] + plot[3]) * hh + 0.02
    for i in (0, 15, 19, 23, 31):
        col = MAROON if i in hot else MUTED
        text(s, xs[i] - 0.3, ybase, 0.6, 0.22, [([R(str(i), 11, i in hot, col)], 0)], align=PP_ALIGN.CENTER,
             name="deck layer label")
    text(s, xs[0] - 0.15, ybase + 0.22, 6.0, 0.22, [([R("layer (Olmo 3 7B Think, 32 layers)", 11, False, MUTED)], 0)],
         name="deck axis label")
    text(s, 6.6, 0.95, 3.03, 3.2, [
        ([R("Together: 0.90 [0.85, 0.96]", 14, True, MAROON)], 2),
        ([R("of the effect, in layers 15, 19 and 23", 11)], 8),
        ([R("Held on 16 new questions: ", 12, True), R("0.90 [0.76, 1.06]", 12)], 6),
        ([R("A second model, Qwen3 8B: ", 12, True), R("its own three layers (21, 22, 29), less concentrated: "
                                                        "0.70 [0.60, 0.83]", 12)], 6),
        ([R("8 of the 10 top attention heads ", 12, True), R("sit in those three layers (Olmo).", 12)], 0)],
        name="deck side")
    text(s, 0.37, 4.3, 9.26, 0.42, [([R("This told us where to intervene: ", 13, True, MAROON),
                                      R("the attention dial targets these layers; one fine-tuned version trains only "
                                        "them.", 13)], 0)], name="deck bottom line")
    notes(s, "Speaker: Arsha. Time: 0:30 (2:10-2:40).\n"
             "- Activation patching (F11): copy one layer's output from the run without the hint into the hinted run, "
             "at the hint's tokens; each bar is that layer's share of the drop. 9 questions, 19 cut points.\n"
             "- 15, 19, 23 together 0.90 [0.85, 0.96]; on 16 new questions 0.90 [0.76, 1.06] (F26). Qwen3 8B (F36): "
             "replicates at its own 21, 22, 29, less concentrated, 0.70 [0.60, 0.83]; layers chosen on puzzles, "
             "patching only.\n"
             "- Heads (F12): 8 of the 10 top heads. The dial (F27, F38); LoRA on 15/19/23 (F28).\n"
             "- Hand-off: 'So we trained fixes.'")
    return s


# ---------------------------------------------------------------- slide 8: the multi-agent check
REVIEWERS = [  # (name, summary file, reviewer id, FINDINGS row)
    ("Olmo 3.1 32B", "trackC/team_c4_summary.json", "olmo3-32b-instruct", "F18"),
    ("Olmo 3 7B", "trackC/team_c11_summary.json", "olmo3-7b-instruct", "F22"),
    ("Qwen3 30B Instruct", "trackC/team_c4_summary.json", "qwen3-30b-a3b-instruct-2507", "F18"),
    ("Qwen3 30B Thinking", "trackC/team_c11_summary.json", "qwen3-30b-a3b-thinking-2507", "F22"),
    ("Granite 4.1 30B", "trackC/team_c13_granite_summary.json", "granite-4.1-30b", "F30"),
    ("Mistral Small 3.2", "trackC/team_c13_mistral_summary.json", "mistral-small-3.2-24b", "F30"),
]


def reviewer_rows():
    out = []
    for name, src, rid, fid in REVIEWERS:
        d = F.J(src)["by_team_model_variant"]
        row = {"name": name}
        for v in ("answer_only", "plus_tool_log"):
            e = d[f"tool | {rid} | {v}"]["reviewer_alone"]["corrects_wrong_solver"]
            lo, hi = F.wilson(e["k"], e["n"])
            assert abs(lo - e["wilson"][0]) < 1e-6 and abs(hi - e["wilson"][1]) < 1e-6
            row[v] = (e["k"], e["n"])
        out.append(row)
    return out


def slide8(prs):
    s = B.white(prs, "Two of six reviewers defer to the tool; a checker doesn't")
    text(s, 0.37, 0.92, 9.26, 0.26, [([R("Why we built it: ", 12, True), R("deployed systems have one model review "
                                     "another. Does the reviewer catch a tool's wrong answer?", 12)], 0)],
         name="deck why")
    rows = reviewer_rows()
    c = F.J("trackC/c15_summary.json")["c_frozen_rule"]["olmo3-32b-instruct"]["plus_tool_log"]
    ck = c["bad_lookups"]["checker_pipeline_caught"]
    lo, hi = F.wilson(ck["k"], ck["n"])
    assert abs(lo - ck["wilson"][0]) < 1e-6 and abs(hi - ck["wilson"][1]) < 1e-6
    cv = pct(ck["k"], ck["n"])
    legend_key(s, 2.45, 1.24, GOLD, "sees the answer only", w=1.9)
    legend_key(s, 4.2, 1.24, MAROON, "sees the tool's log", w=1.9)
    ser = []
    for j_, (v, nm, col) in enumerate((("answer_only", "sees the answer only", GOLD),
                                       ("plus_tool_log", "sees the tool's log", MAROON))):
        vals, lo_, hi_ = [], [], []
        for r in rows:
            a, b, c_ = pct(*r[v])
            vals.append(a), lo_.append(b), hi_.append(c_)
        # the 7th row: the checker (its own items), drawn in the first slot in near-black
        vals.append(cv[0] if j_ == 0 else None), lo_.append(cv[1] if j_ == 0 else None)
        hi_.append(cv[2] if j_ == 0 else None)
        ser.append({"name": nm, "color": col, "values": vals, "low": lo_, "high": hi_,
                    "point_colors": [None] * 6 + [INK if j_ == 0 else None]})
    plot = (0.01, 0.01, 0.97, 0.88)
    x, y, w, h = 2.40, 1.52, 3.45, 2.85
    CH.bars(s, x, y, w, h, [r["name"] for r in rows] + ["Checker"], ser, horizontal=True, gap=30, overlap=-5, fs=11,
            legend=False, plot=plot, cat_labels=False, major=50, name="chart review team",
            alt="Bar chart: for six reviewer models, the share of 73 wrong tool answers each corrected when it saw "
                "the answer only against when it also saw the tool's log, with 95% Wilson intervals; the two Olmo "
                "reviewers drop to almost none, the other four don't. A last bar: a checker that re-solves without "
                "the tool stopped all 53 wrong tool answers on 100 other, fresh items.")
    ys = CH.rows_y(y, h, plot, 7)
    for yc, r in zip(ys, rows):
        (a, n), (b, _) = r["answer_only"], r["plus_tool_log"]
        text(s, 0.30, yc - 0.21, 2.05, 0.42, [([R(r["name"], 12, True, MAROON if "Olmo" in r["name"] else INK)], 0),
                                              ([R(f"{a}/{n} → {b}/{n}", 11)], 0)],
             align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE, name="deck row label")
    text(s, 0.30, ys[6] - 0.21, 2.05, 0.42, [([R("Checker, no tool", 12, True)], 0),
                                             ([R(f"stopped {ck['k']}/{ck['n']}, other items", 11)], 0)],
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE, name="deck row label")
    # the pipeline and the follow-ups
    xs, yp = 6.1, 1.24
    steps = [("Solver", "with the tool", MAROON), ("Reviewer", "reads its work", GOLD), ("Checker", "re-solves, no tool", INK),
             ("User", "gets the answer", B.GRAY)]
    bw, gw = 0.78, 0.1
    for i, (t1, t2, col) in enumerate(steps):
        bx = xs + i * (bw + gw)
        rect(s, bx, yp, bw, 0.62, fill=col, name="deck pipeline step")
        fg = INK if col in (GOLD, B.GRAY) else WHITE
        text(s, bx + 0.03, yp + 0.05, bw - 0.06, 0.55, [([R(t1, 11, True, fg)], 0), ([R(t2, 9, False, fg)], 0)],
             align=PP_ALIGN.CENTER, name="deck pipeline text")
    text(s, xs, 2.0, 3.53, 2.3, [
        ([R("What else we tried (Olmo reviewer)", 12, True, MAROON)], 4),
        ([R("Removed the solver's tool-citing sentences: ", 11, True), R("corrections came back, 25 vs 9 of 34 "
                                                                        "(+47 [+29, +65]).", 11)], 4),
        ([R("A handoff note between agents: ", 11, True), R("it named the tool as the source in 35 of 55; the "
                                                           "solver's own answer, in 5 of 55.", 11)], 4),
        ([R("A retrieved passage instead of an answer key: ", 11, True), R("still deferred, 5 vs 15 of 21.", 11)], 4),
        ([R("Only the two Olmo reviewers defer; the checker was tested where the solver can solve the question "
            "alone (7 of 45 false alarms).", 10, False, MUTED)], 0)], name="deck side")
    text(s, 0.37, 4.44, 9.26, 0.3, [([R("Reading more of the solver's work doesn't help when it cites the tool: check "
                                       "without the tool.", 13, True, MAROON)], 0)], name="deck bottom line")
    notes(s, "Speaker: Shrey. Time: 0:45 (4:10-4:55).\n"
             "- Why: one model reviewing another is common. Same 73 wrong solver answers for all six reviewers.\n"
             "- Olmo 3.1 32B 59 of 73 -> 3 of 73 with the tool's log (F18); only the two Olmo reviewers defer (F22, F30).\n"
             "- Checker (F24): 53 of 53 [93, 100%] on C15's 100 fresh items, a different set; 7 of 45 false alarms "
             "[8, 29%]; one more model call.\n"
             "- Follow-ups: F34 +47 [+29, +65]; FC2 5 of 55 -> 35 of 55; FC4 5 vs 15 of 21 (-48 [-67, -29]).\n"
             "- Hand-off: 'So what should a team do?'")
    return s



# ---------------------------------------------------------------- slide 7: clip C
def slide7(prs, with_video):
    s = B.white(prs, "See it: the same question, before and after training")
    B.video_slot(s, 0.37, 0.92, 7.5, 4.22, B.VIDEO / "clip_c.mp4", B.VIDEO / "poster_c.png",
                 "Demo video: on the same question and the same wrong tool answer, Olmo 3 7B Think with no fix follows "
                 "it and doesn't say so, the consistency-trained version doesn't follow it; a fine-tuned answer names "
                 "the hint; the three layers and where training changed them. Real recorded runs.",
                 with_video, "Clip C: no fix against consistency training, the fine-tuned answer, the layers")
    text(s, 8.02, 0.92, 1.61, 3.8, [
        ([R("Real recorded runs", 12, True, MAROON)], 6),
        ([R("26 of 112", 20, True, INK, True)], 2),
        ([R("questions where no fix took the wrong hint and consistency training didn't", 11)], 10),
        ([R("37 of 42", 20, True, INK, True)], 2),
        ([R("fine-tuned answers that followed said so; the instruction's 18 of 42 (hand labels)", 11)], 10),
        ([R("Found by pattern, first in a fixed seeded order; the count is every question.", 10, False, MUTED)], 0)],
         name="deck video caption")
    notes(s, "Speaker: Arsha. Time: 0:40 (3:30-4:10). Click the video to play (36 s); narrate over it. Beats: no fix "
             "0-8 s; the split 8-16 s; fine-tuned, another question 15-21 s; the layers 21-31 s; the end card 31-36 s.\n"
             "- No fix follows the tool's wrong answer; its reasoning cites it; the answer doesn't say so.\n"
             "- The same question with consistency training: it didn't follow. Not cherry-picked: the first match in a "
             "fixed seeded order of 'the fix held', 26 of 112 questions (TALK_MAP).\n"
             "- Fine-tuned, another question: its answer names the hint (F45: 37 of 42 vs 18 of 42, hand labels).\n"
             "- The map: layers 15, 19, 23 together 0.90 (F11); where training changed it (F39, F42).\n"
             "- If the video won't play: the poster and these beats; backup 21 has stills.\n"
             "- Hand-off to Shrey: 'And what if a second model checks the first?'")
    return s


# ---------------------------------------------------------------- slide 9: what we'd tell a team
def slide9(prs):
    s = B.white(prs, "What we'd tell a team deploying a tool-using model")
    recs = [("Don't read the final answer as a record of why",
             "Log provenance outside the model: Qwen3 8B's answer named the tool in 0 of 143 runs."),
            ("A label or a prompt line won't fix it",
             "An \"unverified\" label on the tool's turn: −1 [−7, +4] points, no effect."),
            ("If you train, pick by how often your tool is right",
             "Consistency training: wrong hints followed 42% → 12%; right tool hints taken 92% → 76%."),
            ("Put an independent check before acting",
             "Re-solving without the tool stopped 53 of 53 wrong answers, for one more model call.")]
    y = 0.95
    for i, (h, body) in enumerate(recs):
        badge(s, 0.37, y + 0.06, str(i + 1), size=0.42)
        text(s, 0.98, y, 8.65, 0.66, [([R(h, 18, True)], 1), ([R(body, 14)], 0)], name="deck rec")
        y += 0.74
    # where each safeguard sits, native
    steps = [("Tool", "can be wrong", B.GRAY, INK), ("Model", "2, 3: a prompt line, training", B.GRAY, INK),
             ("Log provenance", "1: outside the model", MAROON, WHITE),
             ("Checker", "4: re-solves without the tool", MAROON, WHITE), ("User", "acts on the answer", INK, WHITE)]
    gap, yd, hd = 0.3, 4.03, 0.64
    bw = (9.26 - 4 * gap) / 5
    for k, (t1, t2, fill, fg) in enumerate(steps):
        bx = 0.37 + k * (bw + gap)
        rect(s, bx, yd, bw, hd, fill=fill, name="deck safeguard step")
        text(s, bx + 0.05, yd + 0.05, bw - 0.1, hd - 0.1, [([R(t1, 12, True, fg)], 0), ([R(t2, 11, False, fg)], 0)],
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, name="deck safeguard text")
        if k < 4:
            arrow_right(s, bx + bw + 0.04, yd + hd / 2 - 0.13)
    notes(s, "Speaker: Shrey. Time: 0:40 (4:55-5:35).\n"
             "- 1 (F29): 0 of 143 [0, 3%] vs 141 of 145 [93, 99%], keyword counts; not universal, Gemma 4 127 of 162 (FB1).\n"
             "- 2 (F44): the 'unverified' label alone, -1 [-7, +4] on the inserted tool turn; asking for sources names the "
             "tool more (+47 [+30, +64]), follows no less (+6 [-2, +14]) (F25).\n"
             "- 3 (F41): pooled wrong hints 297 of 703 -> 84 of 694; right tool hints 439 of 476 -> 347 of 459; against "
             "the instruction -21 [-26, -16] and -15 [-20, -10]; exploratory crossover 0.36 [0.22, 0.50].\n"
             "- 4 (F24): 53 of 53 [93, 100%] on 100 fresh items; 7 of 45 false alarms [8, 29%]; tested where the solver "
             "can solve the question alone.\n"
             "- The strip: where each sits. 1 is a log kept outside the model; 2 and 3 act on the model; 4 is a second "
             "call that never sees the tool.\n"
             "- Hand-off: 'Where this holds, and what we don't know.'")
    return s


# ---------------------------------------------------------------- backup: every fix with its intervals
FIX_TABLE = [  # FINDINGS F41's table and F43's (A42; LoRA + note): k of n [Wilson]
    ("No fix", "297 of 703 [39, 46%]", "439 of 476 [89, 94%]", "156 of 236 [60, 72%]", "—"),
    ("One-line instruction", "237 of 713 [30, 37%]", "431 of 476 [88, 93%]", "154 of 235 [59, 71%]", "the bar to beat"),
    ("Fine-tuned (LoRA)", "248 of 705 [32, 39%]", "421 of 477 [85, 91%]", "155 of 235 [60, 72%]", "no difference detected"),
    ("LoRA + instruction", "179 of 710 [22, 29%]", "384 of 470 [78, 85%]", "151 of 236 [58, 70%]", "fewer, at an acceptance cost"),
    ("Consistency-trained", "84 of 694 [10, 15%]", "347 of 459 [71, 79%]", "146 of 229 [57, 70%]", "fewer, but costs acceptance"),
    ("Consistency + instruction", "64 of 706 [7, 11%]", "334 of 472 [67, 75%]", "147 of 238 [55, 68%]", "fewer, but costs acceptance"),
]


def fix_table(prs):
    s = B.white(prs, "Every fix on the 120 fresh questions, with its intervals")
    rows = [("Olmo 3 7B Think", "Wrong hints followed (user or tool)", "Right tool hints taken", "No-hint accuracy",
             "Against the instruction")] + FIX_TABLE
    tbl = s.shapes.add_table(len(rows), 5, Inches(0.37), Inches(0.98), Inches(9.26), Inches(2.9)).table
    for j, wd in enumerate((1.95, 1.95, 1.8, 1.7, 1.86)):
        tbl.columns[j].width = Inches(wd)
    for i, r_ in enumerate(rows):
        for j, v in enumerate(r_):
            cell = tbl.cell(i, j)
            cell.text = v
            pr = cell.text_frame.paragraphs[0].runs[0]
            pr.font.size, pr.font.name, pr.font.bold = Pt(11), D.FONT, i == 0 or j == 0
            pr.font.color.rgb = WHITE if i == 0 else (MAROON if r_[0] == "Consistency-trained" and j == 0 else INK)
            cell.fill.solid()
            cell.fill.fore_color.rgb = MAROON if i == 0 else (B.GRAY if i % 2 else WHITE)
    text(s, 0.37, 4.42, 9.26, 0.5, [([R("Against no fix, consistency training: −30 [−35, −26] wrong hints, −17 [−22, −12] "
                                         "right tool hints. Against the instruction: −21 [−26, −16] and −15 [−20, −10]. "
                                         "Beating the instruction at no cost to right hints: met by no fix.", 11, False, MUTED)], 0)],
         name="deck table note")
    notes(s, "Backup (F41, F43, F44). Rates with 95% Wilson intervals; differences in points, paired by question, 95% "
             "bootstrap clustered by question. The last column is the pre-registered rule's reading against the instruction.")
    return s


# ---------------------------------------------------------------- render
def render(pptx, out_dir, names):
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(pptx.parent), str(pptx)],
                   check=True, capture_output=True)
    pdf = pptx.with_suffix(".pdf")
    for i, nm in enumerate(names, 1):
        subprocess.run(["pdftoppm", "-png", "-singlefile", "-scale-to", "1920", "-f", str(i), "-l", str(i), str(pdf),
                        str(out_dir / nm)], check=True)
    pdf.unlink()


SLIDES = [("slide_03_what_we_built", slide3), ("slide_04_failure", slide4), ("slide_05_inside", slide5),
          ("slide_06a_training_grouped", slide6a), ("slide_06b_training_panels", slide6b), ("slide_08_check", slide8)]


def main():
    prs = D.open_template_copy(B.TEMPLATE)
    for _, fn in SLIDES:
        fn(prs)
    B._strip_unused_layouts(prs)
    prs.save(OUT)
    render(OUT, PNG, [n for n, _ in SLIDES])
    print("wrote", OUT, "and", [str(PNG / f"{n}.png") for n, _ in SLIDES])


if __name__ == "__main__":
    main()
