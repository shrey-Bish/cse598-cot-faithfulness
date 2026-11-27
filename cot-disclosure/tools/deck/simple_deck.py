"""The final deck from Ritik's simple version (Nov 26, DEMO_AND_C27): both decks from his file, which stays untouched.

  ../.venv/bin/python tools/deck/simple_deck.py          # from cot-disclosure/; writes both decks and the PDF

Source: docs/presentation/final/local/Group10_final_simple_ritik_2026-11-26.pptx (Ritik's, gitignored: it embeds clips).
Ten main slides (5:30 in the notes, 30 s of slack), the divider and the backups, as Ritik laid them out. This script
changes only:
- slide 6's video: the minimal demo, clip D (tools/demo_min/; 3 cards, about 18 s; poster = card 1), and its notes;
- backup 16's video: the current clip C (Ritik's file had the one from before the 15:20 crop);
- notes for the backups that had none (12-16): the version 3 deck's own notes for the same titles, marked "Backup";
- C27's backup slide, "Addendum: the trained model inside the pipeline", once its summary has been read
  (results/summaries/trackA/c27_summary.json with "read": true; post-freeze addendum, exploratory);
- in the tracked deck (`Group10_final.pptx`, under 5 MB): every video and every demo still becomes a placeholder, so it
  holds no model text and no frame of a clip.
The local deck (`local/Group10_final_with_video.pptx`) goes to Canvas. tests/test_final_deck.py checks both.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_deck as B  # noqa: E402
import diagram as D  # noqa: E402

ROOT = HERE.parents[2]
FINAL = ROOT / "docs" / "presentation" / "final"
SOURCE = FINAL / "local" / "Group10_final_simple_ritik_2026-11-26.pptx"
V3 = FINAL / "local" / "Group10_final_with_video_v3_2026-11-26.pptx"      # version 3's deck: the backups' notes
VIDEO = FINAL / "video"
CLIP_D, POSTER_D = VIDEO / "clip_d.mp4", VIDEO / "poster_d.png"
CLIP_C, POSTER_C = VIDEO / "clip_c.mp4", VIDEO / "poster_c.png"     # backup 16: the fixed clip C (15:20, no path)
OUT, OUT_LOCAL = B.OUT, B.OUT_LOCAL
C27_SUMMARY = ROOT / "cot-disclosure" / "results" / "summaries" / "trackA" / "c27_summary.json"
EMU = 914400

DEMO_SLIDE = 6
CLIP_C_SLIDE = 16          # Ritik's file embeds clip C from before the 15:20 fix (the label path, "Test 2")
DEMO_ALT = ("An 18-second recording of three cards from real recorded runs: the question with the tool's wrong answer, "
            "(G), and the correct answer, (I); the original model answering (G), with one quoted sentence of its "
            "private reasoning that mentions the tool; the consistency-trained model answering (I).")
DEMO_NOTES = """{first} Click the video (18 s): three cards, about 6 s each.
- Card 1: 'One real question. The tool says (G); the right answer is (I).'
- Card 2: 'The original model goes with the tool's (G). Its private reasoning mentions the function call; its final answer never mentions the tool.'
- Card 3: 'After consistency training, the same question and the same tool hint: it keeps its own answer, (I). Across 120 new questions, wrong-hint following fell from 42% to 12%, at a cost.'
- Not cherry-picked: the first match, in a fixed seeded order, of 'the fix held', which happens on 26 of 112 questions.
- If the video won't play: show the poster (card 1) and say: 'The tool said (G), which is wrong. The original model followed it without saying so in its answer; after training, it kept the right answer, (I).'
- If asked: in that sentence the model calls the tool's reply "the user's answer"; the hint came through the tool.
- Hand-off to Shrey: 'What if a second AI checks the answer?'"""


# ---------------------------------------------------------------- shapes
def geometry(sh):
    return [x / EMU for x in (sh.left, sh.top, sh.width, sh.height)]


def remove(slide, sh):
    """Remove a shape and the relationships only it used (a video's media and link, a picture's image)."""
    el = sh._element
    rids = {v for e in el.iter() for k, v in e.attrib.items() if k.startswith("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}")}
    el.getparent().remove(el)
    xml = slide._element.xml
    for rid in rids:
        if f'"{rid}"' not in xml and rid in slide.part.rels:
            slide.part.drop_rel(rid)


def is_video(sh):
    return sh._element.tag.endswith("}pic") and bool(sh._element.xpath(".//a:videoFile"))


def is_still(sh):
    """A picture whose alt text says it is a still of the demo video (backup 25's)."""
    if not sh._element.tag.endswith("}pic") or is_video(sh):
        return False
    descr = sh._element.xpath(".//p:cNvPr")[0].get("descr") or ""
    return descr.startswith("Still ") and "demo video" in descr


def placeholder(slide, sh, label):
    x, y, w, h = geometry(sh)
    remove(slide, sh)
    box = B.rect(slide, x, y, w, h, fill=B.INK, name="deck video placeholder")
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.name, r.font.size, r.font.bold, r.font.color.rgb = D.FONT, Pt(20 if w > 4 else 12), True, B.GOLD
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    r2 = p2.add_run()
    r2.text = "in the submitted deck"
    r2.font.name, r2.font.size, r2.font.color.rgb = D.FONT, Pt(14 if w > 4 else 10), B.WHITE
    box._element.nvSpPr.cNvPr.set("descr", f"Placeholder: {label}, in the submitted deck")
    return box


def replace_video(slide, clip, poster, alt):
    old = next(sh for sh in slide.shapes if is_video(sh))
    x, y, w, h = geometry(old)
    remove(slide, old)
    m = slide.shapes.add_movie(str(clip), Inches(x), Inches(y), Inches(w), Inches(h), poster_frame_image=str(poster),
                               mime_type="video/mp4")
    m.name = "deck video"
    m._element.xpath("./p:nvPicPr/p:cNvPr")[0].set("descr", alt)
    return m


MEDIA_RELS = ("/video", "/media", "/audio", "/image")


def drop_orphan_media(prs):
    """Drop every slide's video, media, audio and image relationships no shape uses (Ritik's slide 6 kept one to an earlier
    video), so a replaced clip doesn't travel in the file. Returns how many went."""
    n = 0
    for s in prs.slides:
        xml = s._element.xml
        for rid, rel in list(s.part.rels.items()):
            if rel.reltype.endswith(MEDIA_RELS) and f'"{rid}"' not in xml:
                s.part.drop_rel(rid) if hasattr(s.part, "drop_rel") else None
                if rid in s.part.rels:
                    s.part.rels.pop(rid)
                n += 1
    return n


STRIP = 4.78               # the template's reserved strip starts here (inches)


def trim_to_strip(prs):
    """Ritik's top-anchored text boxes whose frame runs into the reserved strip end at it instead: their text sits above
    it already (rendered and checked), so nothing moves. Returns [(slide, name)]."""
    from pptx.enum.text import MSO_ANCHOR as A
    done = []
    for i, s in enumerate(prs.slides, 1):
        for sh in s.shapes:
            if sh.name == "deck text" and sh.has_text_frame and (sh.top + sh.height) / EMU > STRIP \
                    and sh.text_frame.vertical_anchor in (None, A.TOP) and sh.top / EMU < STRIP - 0.1:
                sh.height = Emu(int(STRIP * EMU) - sh.top)
                done.append((i, sh.name))
    return done


def shrink_pngs(prs):
    """The tracked deck only: every PNG re-encoded losslessly (PIL, optimize), kept when smaller. Returns bytes saved."""
    import io
    from PIL import Image
    saved = 0
    for part in prs.part.package.iter_parts():
        if getattr(part, "content_type", "") != "image/png":
            continue
        blob = part.blob
        im = Image.open(io.BytesIO(blob))
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
        if buf.tell() < len(blob):
            saved += len(blob) - buf.tell()
            part._blob = buf.getvalue()
    return saved


NOTE_FIXES = [    # (slide, old, new): references the new order made stale (Nov 26)
    (11, "PREP_GUIDE.md (after Phase C) or", "PREP_GUIDE.md or"),
    (16, "backup 21 has stills", "backup 25 has stills"),
]


def fix_notes(prs):
    slides = list(prs.slides)
    for i, old, new in NOTE_FIXES:
        nf = slides[i - 1].notes_slide.notes_text_frame
        assert nf.text.count(old) == 1, (i, old)
        nf.text = nf.text.replace(old, new)


def title(s):
    return s.shapes.title.text if s.shapes.title is not None else ""


def backup_notes(prs, v3=V3):
    """Notes for the backups with none: version 3's notes for the same title, without its speaker and time line."""
    if not v3.exists():
        return 0
    old = {title(s): s.notes_slide.notes_text_frame.text for s in Presentation(str(v3)).slides if s.has_notes_slide}
    n = 0
    for s in prs.slides:
        t = s.notes_slide.notes_text_frame.text.strip() if s.has_notes_slide else ""
        if not t and title(s) in old:
            body = [ln for ln in old[title(s)].splitlines() if not ln.startswith("Speaker:")]
            s.notes_slide.notes_text_frame.text = "\n".join(["Backup, for questions (from version 3's notes)."] + body)
            n += 1
    return n


# ---------------------------------------------------------------- C27's backup (after its reading)
def addendum(prs, summary=C27_SUMMARY):
    """'Addendum: the trained model inside the pipeline': wrong answers reaching the user on the 55 bad lookups, base
    against trained, solver alone / with each reviewer seeing the tool's reply / with the checker; only once read."""
    if not summary.exists():
        return None
    r = json.loads(summary.read_text())
    if not r.get("read"):
        return None
    import charts as CH
    s = B.white(prs, "Addendum: the trained model inside the pipeline")
    rows = [("Solver alone", r["1_solver_alone"])]
    names = {"olmo3-32b-instruct": "Olmo reviewer", "qwen3-30b-a3b-instruct-2507": "Qwen reviewer"}
    for key, label in names.items():
        rows.append((f"{label}, sees the tool's reply", r["3_with_reviewer"][f"{key} | plus_tool_log"]))
    rows.append(("Checker", r["2_with_checker"]))
    cats = [f"{name} ({e['b']['k']}/{e['b']['n']} vs {e['a']['k']}/{e['a']['n']})" for name, e in rows]
    series = []
    for name, side, color in (("Original model", "b", D.GOLD), ("Consistency-trained", "a", D.MAROON)):
        vals = [100 * e[side]["rate"] for _, e in rows]
        series.append({"name": name, "values": vals, "low": [100 * e[side]["wilson"][0] for _, e in rows],
                       "high": [100 * e[side]["wilson"][1] for _, e in rows], "color": color})
    CH.bars(s, 0.37, 0.95, 6.3, 3.6, cats, series, horizontal=True, name="deck chart",
            alt="Bar chart: wrong answers reaching the user on 55 bad tool lookups, original model against "
                "consistency-trained, with the solver alone, with each reviewer seeing the tool's reply, and with "
                "the checker; Wilson intervals.")
    B.text(s, 6.9, 1.0, 2.75, 3.4, [([B.R("Post-freeze, exploratory", 13, True, D.MAROON)], 6),
                                    ([B.R("Wrong answers reaching the user when the tool is wrong (55 questions).", 12)], 6),
                                    ([B.R(r.get("headline", ""), 12, True)], 0)], name="deck text")
    s.notes_slide.notes_text_frame.text = "\n".join(r.get("notes") or ["Backup: C27, post-freeze addendum, exploratory."])
    return s


# ---------------------------------------------------------------- the two decks
def build(local, out, source=SOURCE):
    prs = Presentation(str(source))
    slides = list(prs.slides)
    if local:
        replace_video(slides[DEMO_SLIDE - 1], CLIP_D, POSTER_D, DEMO_ALT)
        c = slides[CLIP_C_SLIDE - 1]
        old = next(sh for sh in c.shapes if is_video(sh))
        alt = old._element.xpath(".//p:cNvPr")[0].get("descr")
        replace_video(c, CLIP_C, POSTER_C, alt)
    nf = slides[DEMO_SLIDE - 1].notes_slide.notes_text_frame
    first = re.match(r"Speaker: [^.]+\. Time: [^)]+\)\.", nf.text)      # Ritik's speaker and time line, kept
    nf.text = DEMO_NOTES.format(first=first.group(0) if first else "Speaker: Arsha. Time: 0:25.")
    backup_notes(prs)
    fix_notes(prs)
    addendum(prs)
    if not local:
        for i, s in enumerate(prs.slides, 1):
            for sh in list(s.shapes):
                if is_video(sh):
                    placeholder(s, sh, "Demo video")
                elif is_still(sh):
                    placeholder(s, sh, "Still of the demo video")
        shrink_pngs(prs)
    drop_orphan_media(prs)
    trim_to_strip(prs)
    B._strip_unused_layouts(prs)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    return out


def export_pdf(deck=OUT):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(deck.parent), str(deck)], check=True,
                   capture_output=True)
    return deck.with_suffix(".pdf")


def main():
    for f in (SOURCE, CLIP_D, POSTER_D, CLIP_C, POSTER_C):
        if not f.exists():
            raise SystemExit(f"missing: {f.relative_to(ROOT)}")
    a = build(False, OUT)
    print(a.relative_to(ROOT), a.stat().st_size)
    pdf = export_pdf(a)
    print(pdf.relative_to(ROOT), pdf.stat().st_size)
    b = build(True, OUT_LOCAL)
    print(b.relative_to(ROOT), b.stat().st_size)


if __name__ == "__main__":
    main()
