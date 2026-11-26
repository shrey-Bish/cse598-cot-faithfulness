"""The final deck (Nov 25; version 3 Nov 26, DECK_V3): docs/presentation/final/Group10_final.pptx from a copy of the
ASU 2026 template. Version 3 leads with what we built: 11 main slides in 6:00 (slides 3-9 from tools/deck/slides_v3.py,
with native charts from tools/deck/charts.py), a divider and 14 backups.

  ../.venv/bin/python tools/deck/build_deck.py            # from cot-disclosure/; writes both decks

Two decks, one source:
- `Group10_final.pptx` (tracked, under 5 MB): the video slides show a placeholder, no model text, no stills.
- `local/Group10_final_with_video.pptx` (gitignored): the demo clips embedded with their poster frames, and the stills;
  this one goes to Canvas.
Plain names on the slides, no internal codes (the notes may carry them). Every number on a slide is in
docs/presentation/pack/02_NUMBERS.md or FINDINGS (tests/test_final_deck.py). The figures come from tools/deck/figures.py,
the design diagram from tools/deck/diagram.py. Clips: A and B (backups), C (slide 7). Nothing in the template's reserved strip (below 4.78 in).
"""
import copy
import io
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import diagram as D  # noqa: E402

ROOT = HERE.parents[2]
FINAL = ROOT / "docs" / "presentation" / "final"
TEMPLATE = FINAL / "templates" / "__2026_Official_ASU_presentation_template___READ-ONLY__Make_a_copy_to_use_.pptx"
FIGS = FINAL / "figures"
PACKFIG = ROOT / "docs" / "presentation" / "pack" / "figures"
VIDEO = FINAL / "video"
OUT = FINAL / "Group10_final.pptx"
OUT_LOCAL = FINAL / "local" / "Group10_final_with_video.pptx"
REPO = "github.com/shrey-Bish/cse598-cot-faithfulness"

MAROON, GOLD, INK, WHITE, GRAY, MID = D.MAROON, D.GOLD, D.INK, D.WHITE, D.GRAY, D.MID
SAFE = 4.75                                   # keep content above the template's reserved strip (4.78 in)
LAYOUT = {"title": "CUSTOM_23_1_1_1_1_1_1_2_1_2", "white": "CUSTOM_40", "two": "CUSTOM_22_1_1_1_1_1_1_3",
          "thanks": "CUSTOM_23_1_1_1_1_2_1_1_1_2", "divider": "CUSTOM_19_1_2_1"}


# ---------------------------------------------------------------- text
def _highlight(run, color="FFC627"):
    rpr = run._r.get_or_add_rPr()
    h = etree.SubElement(rpr, qn("a:highlight"))
    c = etree.SubElement(h, qn("a:srgbClr"))
    c.set("val", color)


def text(slide, x, y, w, h, paras, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, name="deck text"):
    """paras: [(runs, space_after_pt)], runs: [(text, size, bold, color, highlight)]; a plain str is one run."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for side in ("left", "right", "top", "bottom"):
        setattr(tf, f"margin_{side}", Inches(0))
    for i, (runs, after) in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(after)
        for t, size, bold, color, hl in runs:
            r = p.add_run()
            r.text = t
            r.font.name, r.font.size, r.font.bold = D.FONT, Pt(size), bold
            r.font.color.rgb = color
            if hl:
                _highlight(r)
    return tb


def R(t, size=14, bold=False, color=INK, hl=False):
    return (t, size, bold, color, hl)


def big_number(slide, x, y, w, number, label, interval, name="deck number"):
    """The template's key-number style: the number bold on the gold highlight, a bold label, the interval below."""
    return text(slide, x, y, w, 1.05, [([R(number, 30, True, INK, True)], 2), ([R(label, 13, True)], 0),
                                      ([R(interval, 12, False, MID)], 0)], name=name)


def rect(slide, x, y, w, h, fill=GRAY, line=None, shape=MSO_SHAPE.RECTANGLE, name="deck shape"):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.name = name
    D._no_effect(s)
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1.5)
    return s


def picture(slide, path, x, y, w=None, h=None, alt="", name="deck figure"):
    p = slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w) if w else None, Inches(h) if h else None)
    p.name = name
    p._element.nvPicPr.cNvPr.set("descr", alt)
    return p


def notes(slide, cues):
    slide.notes_slide.notes_text_frame.text = cues


# ---------------------------------------------------------------- slides
def slide(prs, kind):
    layout = next(l for l in prs.slide_layouts if l.name == LAYOUT[kind])
    return prs.slides.add_slide(layout)


def ph(s, idx):
    return next(p for p in s.placeholders if p.placeholder_format.idx == idx)


def fill_ph(s, idx, runs_paras, size=None):
    p = ph(s, idx)
    tf = p.text_frame
    tf.text = ""
    for i, runs in enumerate(runs_paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        for t in ([runs] if isinstance(runs, str) else runs):
            r = para.add_run()
            r.text = t
            if size:
                r.font.size = Pt(size)
    return p


def white(prs, title, size=22):
    return D.slide_with_title(prs, title, size)


def video_slot(s, x, y, w, h, clip, poster, alt, with_video, label):
    """The local deck embeds the clip (poster frame, plays on click); the tracked deck shows a placeholder."""
    if with_video and clip.exists() and poster.exists():
        m = s.shapes.add_movie(str(clip), Inches(x), Inches(y), Inches(w), Inches(h), poster_frame_image=str(poster),
                               mime_type="video/mp4")
        m.name = "deck video"
        m._element.xpath("./p:nvPicPr/p:cNvPr")[0].set("descr", alt)
        return m
    box = rect(s, x, y, w, h, fill=INK, name="deck video placeholder")
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "Demo video in the submitted deck"
    r.font.name, r.font.size, r.font.bold, r.font.color.rgb = D.FONT, Pt(24), True, GOLD
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    r2 = p2.add_run()
    r2.text = label
    r2.font.name, r2.font.size, r2.font.color.rgb = D.FONT, Pt(14), WHITE
    box._element.nvSpPr.cNvPr.set("descr", "Placeholder: " + label)
    return box


def build(with_video, out):
    import slides_v3 as V  # noqa: E402 (imports this module's helpers; loaded here to avoid a cycle)
    prs = D.open_template_copy(TEMPLATE)

    # 1. Title (0:10)
    s = slide(prs, "title")
    t = ph(s, 0)
    t.text_frame.text = "Do thinking modes make\vchain-of-thought more honest?"
    for r in t.text_frame.paragraphs[0].runs:
        r.font.size = Pt(36)
    sub = fill_ph(s, 2, ["When a tool is wrong, does the model follow it, and does it tell you?"], 14)
    sub.width = Inches(8.6)
    e = ph(s, 1)._element
    e.getparent().remove(e)
    text(s, 5.48, 3.9, 4.15, 0.8, [([R("CSE 598, Group 10", 12, True)], 0), ([R("Ritik Agarwal, Arsha Jindal, Shrey Bishnoi", 12)], 0),
                                   ([R("December 3, 2026", 12)], 0)], name="deck presenters")
    notes(s, "Speaker: Ritik. Time: 0:10 (0:00-0:10).\n- Who we are; the title question.\n- Hand-off: 'Here is the situation we care about.'")

    # 2. The question and why it matters (0:30)
    s = white(prs, "Tools steer answers, and the user sees only the result")
    text(s, 0.37, 0.98, 6.0, 0.3, [([R("Illustrative example (our own question)", 12, True, INK, True)], 0)])
    q = rect(s, 0.37, 1.35, 3.1, 2.3, fill=WHITE, line=MAROON, shape=MSO_SHAPE.ROUNDED_RECTANGLE, name="deck question")
    text(s, 0.5, 1.45, 2.85, 2.1, [([R("The question", 13, True, MAROON)], 4),
                                   ([R("A ball is dropped from rest. How far does it fall in 2 s? (g = 9.8 m/s²)", 13)], 6),
                                   ([R("(C) 14.7 m   (D) 19.6 m   …", 13)], 0)])
    t = rect(s, 3.75, 1.35, 2.5, 2.3, fill=GRAY, shape=MSO_SHAPE.ROUNDED_RECTANGLE, name="deck tool")
    text(s, 3.88, 1.45, 2.25, 2.1, [([R("The tool (a lookup)", 13, True, MAROON)], 4),
                                    ([R("\"The answer key says (C).\"", 15, True)], 6),
                                    ([R("Wrong: the right answer is (D).", 13)], 0)])
    a = rect(s, 6.53, 1.35, 3.1, 2.3, fill=INK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, name="deck answer")
    text(s, 6.66, 1.45, 2.85, 2.1, [([R("What the user sees", 13, True, GOLD)], 4),
                                    ([R("(C)", 40, True, WHITE)], 4),
                                    ([R("No word about the tool.", 13, False, WHITE)], 0)])
    D.arrow(s, q, t, 3, 1)
    D.arrow(s, t, a, 3, 1)
    text(s, 0.37, 3.85, 9.26, 0.85, [([R("Why it matters: ", 14, True, MAROON),
                                       R("tool-using assistants act on tool output, the user sees only the final answer, "
                                         "and other models are more and more used to check it.", 14)], 4),
                                     ([R("When the tool is wrong, does the model follow it, and does it tell you?", 15, True)], 0)],
         name="deck why")
    notes(s, "Speaker: Ritik. Time: 0:30 (0:10-0:40).\n- Tool-using systems act on answers like this; the tool can be wrong.\n"
             "- What does the model do, and what does the user see: only '(C)'.\n- Our question: does a thinking mode make the reasoning more honest about the source?\n"
             "- The example is illustrative (our own question), not a recorded run.\n- Hand-off: 'Here is what we built to answer it.'")

    # 3-9. Version 3 (DECK_V3, Nov 26): what we built, the failure, inside the model, training, clip C, the check,
    # what we'd tell a team (tools/deck/slides_v3.py)
    V.slide3(prs)
    V.slide4(prs)
    V.slide5(prs)
    V.slide6b(prs)
    V.slide7(prs, with_video)
    V.slide8(prs)
    V.slide9(prs)

    # 10. Where this holds (0:20)
    s = slide(prs, "two")
    fill_ph(s, 0, ["Where this holds, and what we don't know"], 22)
    for idx in (1, 2, 3):
        e = ph(s, idx)._element
        e.getparent().remove(e)
    cols = [("Applies to", MAROON, ["Multiple-choice questions", "One tool format: an answer-key lookup",
                                    "Open models up to about 32B parameters",
                                    "Every fix tested on one model (Olmo 3 7B Think), one training run each",
                                    "Candid answers: 42 hand-labelled answers per system",
                                    "The checker: on items the solver can solve without the tool"]),
            ("Unknown", INK, ["Free-form, multi-step agent tasks", "Larger and closed models",
                              "Whether the fixes transfer to other models",
                              "The checker where the solver can't solve the question alone"])]
    for i, (h, col, items) in enumerate(cols):
        x = 0.37 + i * 4.75
        dot = rect(s, x, 1.05, 0.34, 0.34, fill=col, shape=MSO_SHAPE.OVAL, name="deck column mark")
        dot.text_frame.text = "✓" if i == 0 else "?"
        p = dot.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.runs[0].font.size, p.runs[0].font.bold, p.runs[0].font.color.rgb = Pt(13), True, WHITE
        text(s, x + 0.48, 1.06, 4.0, 0.35, [([R(h, 18, True, col)], 0)])
        text(s, x, 1.55, 4.45, 3.15, [([R("•  " + it, 15)], 8) for it in items], name="deck limits")
    notes(s, "Speaker: Shrey. Time: 0:20 (5:35-5:55).\n- Unknown: free-form, multi-step agent tasks; larger and closed "
             "models; whether the fixes transfer to other models; the checker where the solver can't solve the question "
             "alone.\n- Hand-off: 'Thank you.'")

    # 11. Thank you (0:05)
    s = slide(prs, "thanks")
    tpl = Presentation(TEMPLATE)
    photo = next((sh for sh in tpl.slides[17].shapes if getattr(sh, "is_placeholder", False) and sh.placeholder_format.idx == 2), None)
    pic_ph = ph(s, 2)
    if photo is not None:
        pic = pic_ph.insert_picture(io.BytesIO(photo.image.blob))
        pic._element.nvPicPr.cNvPr.set("descr", "Decorative photo from the ASU template: aloe flowers.")
    else:
        pic_ph._element.getparent().remove(pic_ph._element)
    fill_ph(s, 0, ["Thank you"], 30)
    fill_ph(s, 1, ["Questions?", "Ritik Agarwal, Arsha Jindal, Shrey Bishnoi", REPO], 16)
    notes(s, "Speaker: Shrey. Time: 0:05 (5:55-6:00).\n- Thank you; questions. Backup slides follow the divider.")

    # ---------------------------------------------------------------- backups
    s = slide(prs, "divider")
    fill_ph(s, 0, ["Backup: for questions"], 40)
    fill_ph(s, 1, ["Not presented: each slide answers a likely question"], 14)
    notes(s, "Backup slides: not presented. See docs/presentation/final/PREP_GUIDE.md (after Phase C) or pack/09_QA_BANK.md.")

    s = white(prs, "Inside the model, three layers carry most of the hint's effect")
    picture(s, PACKFIG / "readout_by_layer_slide.png", 0.37, 1.0, w=6.4,
            alt="Bar chart of the hint's effect by layer in Olmo 3 7B Think: layers 15, 19 and 23 carry most of it, on the first questions and on 16 new ones.")
    text(s, 6.95, 1.0, 2.68, 3.7, [([R("0.90", 28, True, INK, True)], 2), ([R("of the hint's effect at the takeover, layers 15, 19, 23 [0.85, 0.96] (Olmo 3 7B Think)", 12)], 8),
                                   ([R("0.90", 22, True, INK, True)], 2), ([R("on 16 new questions [0.76, 1.06]", 12)], 8),
                                   ([R("0.70", 22, True, INK, True)], 2), ([R("Qwen3 8B, with its own layers 21, 22, 29 [0.60, 0.83]", 12)], 0)])
    notes(s, "Backup (F11, F26, F36). Activation patching at the takeover; Qwen3-8B replicates with its own three layers, less concentrated.")

    s = white(prs, "The stronger the claimed authority, the harder the pull")
    picture(s, PACKFIG / "authority_ladder.png", 0.37, 1.0, w=6.4,
            alt="Chart of how far a wrong hint moves the answer as the claimed source grows in authority, from a user's guess to the official solution manual, beside the tool channels.")
    text(s, 6.95, 1.0, 2.68, 3.7, [([R("For pasted tool output, the claim explains much of the pull: ", 12),
                                     R("a user's \"my course answer key\" closes 68% and 71% of the gap (Qwen3), all of it (Olmo).", 12, True)], 8),
                                   ([R("The official manual minus a classmate: +41 [+31, +51], +12 [+4, +20], +32 [+23, +41] points.", 12)], 8),
                                   ([R("Not for a model's own tool call: Qwen3 30B Instruct's goes beyond the claim, +75 [+65, +85].", 12)], 0)])
    notes(s, "Backup (F35, F40). Authority explains the pull for pasted output, not the model's own call.")

    s = white(prs, "Every fix trades wrong hints resisted for right hints refused")
    rows = [("Fix (one model: Olmo 3 7B Think)", "Wrong hints taken", "Right hints taken", "Reading"),
            ("One-line instruction", "−13 [−21, −6] vs no fix", "—", "the baseline to beat"),
            ("Fine-tuning", "−10 [−16, −4] vs no fix; +3 [−1, +8] vs the instruction", "—", "passes; doesn't beat the instruction"),
            ("Consistency training", "84 of 694 vs 237 of 713", "347 of 459 vs 431 of 476", "fewer, but costs acceptance"),
            ("…with the instruction", "64 of 706", "−20 [−26, −14] vs the instruction", "fewer, costs more"),
            ("\"Unverified\" label alone", "−1 [−7, +4]", "—", "no effect"),
            ("Label with the instruction", "−14 [−20, −9]", "−12 [−18, −6]", "adds, costs acceptance"),
            ("Attention dial (120 questions)", "82 of 240 → 49 of 240", "−5.8 [−10.8, −1.3]", "cut replicates, real cost")]
    tbl = s.shapes.add_table(len(rows), 4, Inches(0.37), Inches(1.0), Inches(9.26), Inches(3.6)).table
    widths = (2.4, 2.95, 2.11, 1.8)
    for j, wd in enumerate(widths):
        tbl.columns[j].width = Inches(wd)
    for i, r_ in enumerate(rows):
        for j, v in enumerate(r_):
            cell = tbl.cell(i, j)
            cell.text = v
            pr = cell.text_frame.paragraphs[0].runs[0]
            pr.font.size, pr.font.name, pr.font.bold = Pt(11), D.FONT, i == 0
            pr.font.color.rgb = WHITE if i == 0 else INK
            cell.fill.solid()
            cell.fill.fore_color.rgb = MAROON if i == 0 else (GRAY if i % 2 else WHITE)
    notes(s, "Backup (F28, F41, F43, F44, F38). Differences in points with 95% intervals; following and acceptance against the instruction unless noted.")

    s = white(prs, "Exploratory: the better fix depends on the tool")
    picture(s, FIGS / "fig_tradeoff.png", 0.37, 1.0, h=3.65,
            alt="Exploratory line chart: correct answers against how often the tool is right, for consistency training and the one-line instruction; they cross when the tool is right about 36% of the time.")
    text(s, 6.6, 1.0, 3.03, 3.7, [([R("Exploratory (post hoc)", 13, True, INK, True)], 6),
                                  ([R("Consistency training gives more correct answers than the instruction only if the tool is right less than 0.36 [0.22, 0.50] of the time.", 12)], 6),
                                  ([R("Right hints taken: 347 of 459 against 431 of 476.", 12)], 0)])
    notes(s, "Backup (story item 7; REPORT section 7). Exploratory, post hoc: replaces no verdict.")

    s = white(prs, "Only Olmo's reviewers defer to the tool")
    picture(s, PACKFIG / "trackC_reviewers_slide.png", 0.37, 1.0, w=6.4,
            alt="Chart of six reviewers in four model families: how often each corrects a wrong tool answer from the answer alone and when shown the tool's log; only the two Olmo reviewers drop.")
    text(s, 6.95, 1.0, 2.68, 3.7, [([R("Six reviewers, four families: only Olmo's two defer.", 12, True)], 8),
                                   ([R("Olmo 3.1 32B corrected 59 of 73 from the answer alone, 3 of 73 with the tool's log.", 12)], 8),
                                   ([R("The checker never sees the tool: 53 of 53 stopped on 100 fresh items.", 12)], 0)])
    notes(s, "Backup (F18, F22, F30, F24).")

    s = white(prs, "What's new, and what others showed first")
    for i, (h, col, items) in enumerate([
            ("Shown first by others", INK, ["Models use hints they don't name (Turpin et al.; Chen et al.)",
                                            "A tool's cue is named less than a user's (FACE-Eval, Gema et al.)",
                                            "Claimed authority moves answers (Kumar and Chopra)",
                                            "Consistency training as a method (Chua et al.)"]),
            ("Ours", MAROON, ["Private reasoning against the final answer, after the model's own tool call",
                              "A user's claim against each tool channel, same model, same day",
                              "The layers that read the hint, in two model families",
                              "Every fix's cost on right hints; a review team where a blind checker holds"])]):
        x = 0.37 + i * 4.75
        mark = rect(s, x, 1.05, 0.34, 0.34, fill=col, shape=MSO_SHAPE.OVAL, name="deck column mark")
        text(s, x + 0.48, 1.06, 4.0, 0.35, [([R(h, 17, True, col)], 0)])
        text(s, x, 1.55, 4.45, 3.15, [([R("•  " + it, 14)], 8) for it in items], name="deck novelty")
        del mark
    notes(s, "Backup (pack 07_RELATED_WORK; RELATED_WORK.md). Disagreements: A-CC and Syed and Yasaei, not reconciled.")

    s = white(prs, "Every decision rule was written down before its data")
    steps = [("Oct 20–27", "5 rules fixed in the plan or code before their results"),
             ("Oct 29–Nov 7", "31 rules pre-registered, each committed before its runs"),
             ("Nov 18", "results frozen (a git tag); since then, presentation work only")]
    prev = None
    for i, (d, t) in enumerate(steps):
        x = 0.37 + i * 3.15
        bx = rect(s, x, 1.15, 2.85, 1.55, fill=MAROON if i == 1 else GRAY, shape=MSO_SHAPE.ROUNDED_RECTANGLE, name="deck step")
        text(s, x + 0.15, 1.25, 2.55, 1.4, [([R(d, 16, True, GOLD if i == 1 else MAROON)], 4),
                                            ([R(t, 13, False, WHITE if i == 1 else INK)], 0)])
        if prev is not None:
            D.arrow(s, prev, bx, 3, 1)
        prev = bx
    text(s, 0.37, 3.0, 9.26, 1.7, [([R("Statistics: ", 14, True), R("rates with 95% Wilson intervals; differences in percentage points with a 95% "
                                     "paired bootstrap clustered by question (20,000 resamples); under 5 questions, no interval (\"too few questions\").", 14)], 8),
                                   ([R("Also on record: 2 exploratory analyses and 1 comparison read after the fact, each marked as such.", 13, False, MID)], 0)])
    notes(s, "Backup (docs/paper/supplement/PREREGISTRATIONS.md: 42 ledger rows; DEVIATIONS.md; the freeze tag results-freeze-2026-11-18).")

    s = white(prs, "The full evaluation: one spine, three branches off the model")
    D.draw_full(s)
    notes(s, "Backup: the full design (03_METHODS). Review team: the first test on 53 items, then 100 fresh items.")

    s = white(prs, "The demo, in stills")
    stills = [VIDEO / "stills" / f"{b}.png" for b in ("A1", "A2", "A3", "A6")]
    if with_video and all(p.exists() for p in stills):
        for i, p in enumerate(stills):
            picture(s, p, 0.37 + (i % 2) * 4.7, 1.0 + (i // 2) * 1.9, w=3.2,
                    alt=f"Still {i + 1} of the demo video: a real recorded run on the scratch pad.")
    else:
        video_slot(s, 0.37, 1.0, 6.3, 3.55, Path("-"), Path("-"), "", False, "Stills of the demo, in case a video won't play")
    notes(s, "Backup: the demo's key frames (local deck only).")

    s = white(prs, "Across ten model settings, tools pull harder")
    picture(s, FIGS / "fig_tool_vs_user_full.png", 0.37, 1.0, h=3.7,
            alt="Dot plot for ten model settings: following a wrong letter from the user against from a tool, with 95% intervals.")
    notes(s, "Backup (F15-F17, F29, FB1). gpt-oss-20b reported without a decision (F37), not shown.")

    s = white(prs, "After a tool call, the reasoning names it; the answer rarely does")
    picture(s, FIGS / "fig_reasoning_vs_answer.png", 0.37, 1.0, h=3.7,
            alt="Paired bars: the share of runs whose private reasoning names the tool against whose final answer does, for Qwen3 8B thinking on and Qwen3 30B Thinking, with Gemma 4 thinking off as the exception.")
    notes(s, "Backup (F29, F15, FB1). Denominators: reasoning, runs that called; answer, runs that followed (Gemma: all answered runs).")

    s = white(prs, "The fix and the check, on video")
    video_slot(s, 0.37, 1.0, 6.3, 3.55, VIDEO / "clip_b.mp4", VIDEO / "poster_b.png",
               "Demo video: consistency training resists the wrong answer on the same question; it also refuses a right one; the review team: the reviewer defers, the checker flags it.",
               with_video, "Consistency training, its cost, and the review team")
    notes(s, "Backup: clip B (about 28 s).")

    # backup: clip A, the base model only (the old slide 5)
    s = white(prs, "See it happen: one real run, and how often it happens")
    video_slot(s, 0.37, 0.92, 7.5, 4.22, VIDEO / "clip_a.mp4", VIDEO / "poster_a.png",
               "Demo video: a real recorded run of Olmo 3 7B Think with a tool's wrong answer: its private reasoning cites the tool, its final answer is the bare letter.",
               with_video, "A real recorded run: the tool's wrong answer, the reasoning citing it, the bare answer")
    text(s, 8.02, 0.92, 1.61, 3.8, [
        ([R("A real recorded run", 12, True, MAROON)], 6),
        ([R("28 of 114", 20, True, INK, True)], 2),
        ([R("questions look like this: took the wrong hint, named the tool in its reasoning, not its answer", 11)], 10),
        ([R("85 of 233", 20, True, INK, True)], 2),
        ([R("runs took this wrong tool hint [31, 43%]", 11)], 10),
        ([R("Olmo 3 7B Think, no fix. Found by pattern; the count is every question.", 10, False, MID)], 0)], name="deck video caption")
    notes(s, "Backup: clip A (about 49 s), the base model only. The question is the first match, in a fixed seeded "
             "order, of 'named in reasoning only': 28 of 114 questions (TALK_MAP, Show me); 85 of 233 runs took this wrong "
             "tool hint (F41's inserted channel).")

    V.fix_table(prs)

    if not with_video:
        _strip_unused_layouts(prs)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(out)
    return out


def _strip_unused_layouts(prs):
    """Drop the layouts no slide uses (and with them their pictures), so the tracked deck stays small."""
    used = {s.slide_layout.name for s in prs.slides}
    for layout in list(prs.slide_layouts):
        if layout.name not in used:
            prs.slide_layouts.remove(layout)


def export_architecture(out_dir=ROOT / "docs" / "figures"):
    """The full design diagram on its own slide, as docs/figures/architecture.svg and .png (for the README and the
    report), rendered by LibreOffice from native shapes."""
    import shutil
    import subprocess
    import tempfile
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(10), Inches(5.625)
    s = prs.slides.add_slide(prs.slide_layouts[6])
    text(s, 0.37, 0.3, 9.26, 0.5, [([R("The evaluation: one spine, three branches off the model", 22, True)], 0)])
    D.draw_full(s, y=1.0)
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "architecture.pptx"
        prs.save(src)
        for fmt in ("svg", "pdf"):
            subprocess.run(["soffice", "--headless", "--convert-to", fmt, "--outdir", td, str(src)], check=True, capture_output=True)
        shutil.copy(Path(td) / "architecture.svg", out_dir / "architecture.svg")
        subprocess.run(["pdftoppm", "-png", "-r", "192", "-singlefile", str(Path(td) / "architecture.pdf"), str(out_dir / "architecture")], check=True)
    return out_dir / "architecture.svg", out_dir / "architecture.png"


def export_pdf(deck=OUT):
    """The tracked deck as a PDF beside it (LibreOffice), for reading and for the slide check."""
    import subprocess
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(deck.parent), str(deck)], check=True, capture_output=True)
    return deck.with_suffix(".pdf")


def main():
    a = build(False, OUT)
    print(a, a.stat().st_size)
    pdf = export_pdf(a)
    print(pdf, pdf.stat().st_size)
    b = build(True, OUT_LOCAL)
    print(b, b.stat().st_size)
    for f in export_architecture():
        print(f, f.stat().st_size)


if __name__ == "__main__":
    main()
