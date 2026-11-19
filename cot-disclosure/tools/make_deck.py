"""Build docs/presentation/deck.pptx (a slide shell) from docs/presentation/TALK_MAP.md.

One slide a table row: row 0 is the title slide, the last row the "Limits and next steps" slide (its lines are the
two bullet lists under the table). A content slide is the row's short title, its first figure fitted below at full
size, and a footer with the slide number and the evidence codes. A row's other figures each get a backup slide (the
same title with "(backup)", the figure at full size) after the limits slide: two figures side by side were too small
to read (Nov 19). No speaker notes, no paragraphs, no animation: the team writes
the words. Core properties are fixed so the file does not carry the build time.

    ../.venv/bin/python tools/make_deck.py [out.pptx]
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
TALK_MAP = ROOT / "docs" / "presentation" / "TALK_MAP.md"
FIG = ROOT / "docs" / "paper" / "figures"
DEFAULT_OUT = ROOT / "docs" / "presentation" / "deck.pptx"

PROJECT_TITLE = "Do thinking modes make chain-of-thought more honest?"
AUTHOR = "CSE 598 Group 10"
FIXED_TIME = datetime(2026, 11, 18, 21, 4)  # the results freeze
NAMES = "Shrey Bishnoi, Arsha Jindal, Ritik Agarwal"
FONT = "Calibri"
INK = RGBColor(0x1F, 0x29, 0x33)
MUTED = RGBColor(0x6B, 0x72, 0x80)
PRIVATE = RGBColor(0x2F, 0x6F, 0xD6)
SW, SH = Inches(13.333), Inches(7.5)


def parse_talk_map(path: Path = TALK_MAP) -> dict:
    text = path.read_text(encoding="utf-8")
    rows, header = [], None
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells[0] == "#":
            header = [c.lower() for c in cells]
            continue
        if header is None or not cells[0].isdigit():
            continue
        d = dict(zip(header, cells))
        rows.append({
            "num": int(d["#"]),
            "title": d["slide title"],
            "figures": re.findall(r"`([^`]+)`", d["figure(s)"]),
            "evidence": d["evidence (footer)"],
            "time": d["time"],
        })
    lines, cur = {"Limits": [], "Next steps": []}, None
    in_lines = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_lines = line.startswith("## Limits and next steps lines")
            cur = None
        elif in_lines:
            m = re.fullmatch(r"\*\*(Limits|Next steps)\*\*", line.strip())
            if m:
                cur = m.group(1)
            elif cur and line.startswith("- "):
                lines[cur].append(line[2:].strip())
    return {"rows": rows, "lines": lines}


def _text(slide, name, x, y, w, h, text, size, bold=False, color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(x, y, w, h)
    box.name = name
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.name, r.font.size, r.font.bold, r.font.color.rgb = FONT, Pt(size), bold, color
    return box


def _bullets(slide, name, x, y, w, h, items, size):
    box = slide.shapes.add_textbox(x, y, w, h)
    box.name = name
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(10)
        pPr = p._p.get_or_add_pPr()
        pPr.set("marL", "285750")
        pPr.set("indent", "-285750")
        bu = pPr.makeelement("{http://schemas.openxmlformats.org/drawingml/2006/main}buChar", {"char": "–"})
        pPr.append(bu)
        r = p.add_run()
        r.text = item
        r.font.name, r.font.size, r.font.color.rgb = FONT, Pt(size), INK
    return box


def _fit(slide, path: Path, x, y, w, h):
    pic = slide.shapes.add_picture(str(path), x, y)
    iw, ih = pic.image.size
    scale = min(w / iw, h / ih)
    pic.width, pic.height = int(iw * scale), int(ih * scale)
    pic.left = int(x + (w - pic.width) / 2)
    pic.top = int(y + (h - pic.height) / 2)
    pic.name = f"Figure {path.stem}"
    return pic


def _footer(slide, n, evidence):
    _text(slide, "Footer", Inches(0.6), Inches(7.0), Inches(10.5), Inches(0.3),
          f"{n}" + (f"   ·   {evidence}" if evidence else ""), 11, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)


def build(out: Path = DEFAULT_OUT, talk_map: Path = TALK_MAP) -> Path:
    tm = parse_talk_map(talk_map)
    rows, lines = tm["rows"], tm["lines"]
    prs = Presentation()
    prs.slide_width, prs.slide_height = SW, SH
    blank = prs.slide_layouts[6]
    for r in rows:
        s = prs.slides.add_slide(blank)
        if r["num"] == 0:
            _text(s, "Title", Inches(0.9), Inches(2.1), Inches(11.5), Inches(1.6), r["title"], 44, True, INK,
                  anchor=MSO_ANCHOR.BOTTOM)
            _text(s, "Course", Inches(0.9), Inches(4.0), Inches(11.5), Inches(0.5), "CSE 598 · Group 10", 24, False, PRIVATE)
            _text(s, "Team", Inches(0.9), Inches(4.6), Inches(11.5), Inches(0.5), NAMES, 22)
            _text(s, "Date", Inches(0.9), Inches(5.2), Inches(11.5), Inches(0.5), "Nov 24, 2026", 22, color=MUTED)
            continue
        _text(s, "Title", Inches(0.6), Inches(0.4), Inches(12.1), Inches(0.8), r["title"], 32, True, INK,
              anchor=MSO_ANCHOR.MIDDLE)
        if r["figures"]:
            # one figure a slide, full size: a row's first figure here, any other on a backup slide after the limits
            _fit(s, FIG / r["figures"][0], Inches(0.6), Inches(1.35), Inches(12.13), Inches(5.55))
        else:
            _text(s, "Limits header", Inches(0.6), Inches(1.6), Inches(5.9), Inches(0.5), "Limits", 26, True, PRIVATE)
            _bullets(s, "Limits lines", Inches(0.6), Inches(2.3), Inches(5.9), Inches(4.4), lines["Limits"], 20)
            _text(s, "Next steps header", Inches(6.9), Inches(1.6), Inches(5.9), Inches(0.5), "Next steps", 26, True,
                  PRIVATE)
            _bullets(s, "Next steps lines", Inches(6.9), Inches(2.3), Inches(5.9), Inches(4.4), lines["Next steps"], 20)
        _footer(s, r["num"], r["evidence"])
    for r in rows:
        for f in r["figures"][1:]:
            s = prs.slides.add_slide(blank)
            _text(s, "Title", Inches(0.6), Inches(0.4), Inches(12.1), Inches(0.8), r["title"] + " (backup)", 32, True,
                  INK, anchor=MSO_ANCHOR.MIDDLE)
            _fit(s, FIG / f, Inches(0.6), Inches(1.35), Inches(12.13), Inches(5.55))
            _footer(s, f"{r['num']}, backup", r["evidence"])
    cp = prs.core_properties
    cp.author = cp.last_modified_by = AUTHOR
    cp.title = PROJECT_TITLE
    cp.created = cp.modified = FIXED_TIME
    cp.subject = cp.keywords = cp.comments = cp.category = ""
    cp.revision = 1
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    print(build(dest), dest.stat().st_size // 1024, "KB")
