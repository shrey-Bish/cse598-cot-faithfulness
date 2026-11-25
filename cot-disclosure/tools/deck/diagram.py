"""The evaluation's architecture diagram as native PowerPoint shapes and connectors.

Two versions of one diagram, both drawn with python-pptx (editable shapes, not an image):
  draw_simple(slide, ...)  slide 3: six boxes, big text, reads in five seconds
  draw_full(slide, ...)    backup B7: the same spine plus three branches off "The model"

Phase A usage (a draft on a copy of the official template):
  python cot-disclosure/tools/deck/diagram.py TEMPLATE.pptx OUT.pptx
Phase B: import draw_simple / draw_full and call them on slides of the real deck.

Every number drawn here comes from docs/presentation/pack/03_METHODS.md, 02_NUMBERS.md
or cot-disclosure/tools/demo_template/method.json (listed in storyboard/TEMPLATE_MAP.md,
"diagram facts"). Plain names only. Nothing may sit in the template's bottom safe-zone strip
(y > SAFE_BOTTOM inches on a 5.625 in slide).
"""
import sys
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

MAROON = RGBColor(0x8C, 0x1D, 0x40)
GOLD = RGBColor(0xFF, 0xC6, 0x27)
INK = RGBColor(0x19, 0x19, 0x19)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GRAY = RGBColor(0xE8, 0xE8, 0xE8)
MID = RGBColor(0x74, 0x74, 0x74)
FONT = "Arial"
SAFE_BOTTOM = 4.78  # template slide 6: the reserved strip is y 4.78 to 5.625 in
LAYOUT_NAME = "CUSTOM_40"  # the white "Slide title" layout (template slide 12)


def _fmt_run(run, size, bold, color):
    f = run.font
    f.name, f.size, f.bold = FONT, Pt(size), bold
    f.color.rgb = color


def _text(tf, paras, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, inset=0.06):
    """paras: list of (text, size, bold, color)."""
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(inset)
    tf.margin_top = tf.margin_bottom = Inches(0.04)
    for i, (t, size, bold, color) in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(2)
        _fmt_run(p.add_run(), size, bold, color)
        p.runs[0].text = t


def _no_effect(shp):
    """Drop the theme's shadow (effectRef) so shapes render flat in PowerPoint and LibreOffice."""
    for e in shp._element.iter(qn("a:effectRef")):
        e.set("idx", "0")


def box(slide, x, y, w, h, paras, fill=MAROON, line=None, name="box",
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, rounded=True):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
                                 Inches(x), Inches(y), Inches(w), Inches(h))
    if rounded:
        shp.adjustments[0] = 0.07
    shp.name = name
    shp.shadow.inherit = False
    _no_effect(shp)
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(2)
    _text(shp.text_frame, paras, align=align, anchor=anchor)
    return shp


def arrow(slide, a, b, sa, sb, kind=MSO_CONNECTOR.STRAIGHT, color=INK, width=2.25, name="arrow"):
    """A native connector glued to shape a (site sa) and shape b (site sb), arrowhead at b.
    Rectangle sites: 0 top, 1 left, 2 bottom, 3 right."""
    c = slide.shapes.add_connector(kind, 0, 0, 0, 0)
    c.begin_connect(a, sa)
    c.end_connect(b, sb)
    c.name = name
    _no_effect(c)
    c.line.color.rgb = color
    c.line.width = Pt(width)
    ln = c.line._get_or_add_ln()
    tail = etree.SubElement(ln, qn("a:tailEnd"))
    tail.set("type", "triangle")
    tail.set("w", "med")
    tail.set("len", "med")
    return c


def _chain(slide, shapes, **kw):
    for a, b in zip(shapes, shapes[1:]):
        arrow(slide, a, b, 3, 1, **kw)


# ---------------------------------------------------------------- SIMPLE (slide 3)
def draw_simple(slide, x=0.37, y=1.4, w=9.26, h=2.6):
    """Six boxes, left to right. Body text 14 pt, heads 16 pt (at 10 x 5.625 in)."""
    n, gap = 6, 0.3
    bw = (w - gap * (n - 1)) / n
    spec = [
        ("Questions", ["Multiple choice", "Fixed, seeded sets"], MAROON),
        ("The hint", ["Same wrong letter", "Source swapped", "Wrong or right"], GOLD),
        ("The model", ["12 open models", "Thinking on or off"], MAROON),
        ("What it wrote", ["Private reasoning", "Final answer"], MAROON),
        ("Three measures", ["Took the wrong hint?", "Reasoning names the source?", "Answer names it?"], MAROON),
        ("Statistics", ["95% intervals", "Paired by question", "Rules written first"], MAROON),
    ]
    shapes = []
    for i, (head, lines, fill) in enumerate(spec):
        fg = INK if fill == GOLD else WHITE
        paras = [(head, 16, True, fg)] + [(t, 14, False, fg) for t in lines]
        shapes.append(box(slide, x + i * (bw + gap), y, bw, h, paras, fill=fill,
                          name=f"simple {i + 1} {head}", anchor=MSO_ANCHOR.TOP))
    _chain(slide, shapes, name="simple arrow")
    return shapes


# ---------------------------------------------------------------- FULL (backup B7)
def draw_full(slide, x=0.37, y=1.1, w=9.26):
    n, gap = 6, 0.19
    bw = (w - gap * (n - 1)) / n
    bh = 1.5
    spec = [
        ("Questions", "54 test questions, 3 runs each; 30 held-out; 120 fresh", MAROON),
        ("The hint", "user's guess, stronger claim, pasted tool output, own tool call; wrong or right", GOLD),
        ("The model", "12 open models (8 answer, 4 review); thinking on or off; 352 GPU-hours on Sol", MAROON),
        ("What it wrote", "private reasoning, then the final answer", MAROON),
        ("Three measures", "took the wrong hint? reasoning names the source? answer names it?", MAROON),
        ("Statistics", "95% intervals; paired bootstrap by question, 20,000 resamples; rules written before the data", MAROON),
    ]
    spine = []
    for i, (head, small, fill) in enumerate(spec):
        fg = INK if fill == GOLD else WHITE
        paras = [(head, 14, True, fg), (small, 10, False, fg)]
        spine.append(box(slide, x + i * (bw + gap), y, bw, bh, paras, fill=fill,
                         name=f"full spine {i + 1} {head}", anchor=MSO_ANCHOR.TOP))
    _chain(slide, spine, name="spine arrow")
    model = spine[2]

    cw, cgap, cy, ch = 2.95, (w - 3 * 2.95) / 2, 3.0, 1.68
    cards = []
    heads = [
        ("Inside the model", "Olmo 3 7B Think, 32 layers: three layers carry 0.90 [0.85, 0.96] of the hint's effect"),
        ("The fixes", "tested on the 30 held-out and the 120 fresh questions, with wrong and right hints"),
        ("The review team", "tested on 100 fresh items"),
    ]
    for i, (head, note) in enumerate(heads):
        cx = x + i * (cw + cgap)
        card = box(slide, cx, cy, cw, ch,
                   [(head, 14, True, MAROON), (note, 10, False, INK)],
                   fill=WHITE, line=MAROON, name=f"branch {head}", anchor=MSO_ANCHOR.TOP)
        cards.append((card, cx))
        arrow(slide, model, card, 2, 0, kind=MSO_CONNECTOR.ELBOW, name=f"branch arrow {head}")

    # mini flows inside the cards (lower part of each card)
    my, mh = cy + 0.78, 0.78

    def mini(i, labels, widths):
        cx = cards[i][1]
        total = sum(widths) + 0.18 * (len(widths) - 1)
        cur = cx + (cw - total) / 2
        out = []
        for lab, mw in zip(labels, widths):
            out.append(box(slide, cur, my, mw, mh, [(lab, 10, False, INK)], fill=GRAY,
                           name=f"mini {lab[:20]}", rounded=False))
            cur += mw + 0.18
        _chain(slide, out, width=1.5, name="mini arrow")

    mini(0, ["Activation patching", "The readout layers"], [1.25, 1.25])
    mini(1, ["Instruction, \"unverified\" label, fine-tuning, consistency training, attention dial",
             "Re-tested on fresh questions"], [1.55, 1.0])
    mini(2, ["Solver", "Reviewer", "Checker"], [0.72, 0.72, 0.72])
    return spine, cards


# ---------------------------------------------------------------- deck scaffolding
def open_template_copy(template_path):
    """Open the template (a COPY: the original is never written), drop every slide, keep the masters."""
    prs = Presentation(template_path)
    lst = prs.slides._sldIdLst
    for sld in list(lst):
        prs.part.drop_rel(sld.get(qn("r:id")))
        lst.remove(sld)
    return prs


def slide_with_title(prs, title, size=22):
    layout = next(l for l in prs.slide_layouts if l.name == LAYOUT_NAME)
    s = prs.slides.add_slide(layout)
    for ph in list(s.placeholders):
        if ph.placeholder_format.type is not None and ph.placeholder_format.idx == 0:
            ph.text_frame.text = title
            for r in ph.text_frame.paragraphs[0].runs:
                r.font.size = Pt(size)  # keeps the layout's bold, gold highlight, Arial
            ph.left, ph.top, ph.width, ph.height = Inches(0.37), Inches(0.35), Inches(9.26), Inches(0.75)
        else:
            ph._element.getparent().remove(ph._element)  # the empty body placeholder
    return s


def build(template_path, out_path):
    prs = open_template_copy(template_path)
    s1 = slide_with_title(prs, "Same question, same wrong letter: only the source changes", 24)
    draw_simple(s1)
    cap = s1.shapes.add_textbox(Inches(0.37), Inches(4.2), Inches(9.26), Inches(0.3))
    cap.name = "simple caption"
    _text(cap.text_frame, [("Everything else is held fixed, so a difference is the source's effect.", 14, False, INK)],
          align=PP_ALIGN.LEFT, inset=0)
    s2 = slide_with_title(prs, "The full evaluation: one spine, three branches off the model", 22)
    draw_full(s2)
    prs.save(out_path)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
