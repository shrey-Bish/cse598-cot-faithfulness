"""The final deck (docs/presentation/final/Group10_final.pptx, Nov 25): built by tools/deck/build_deck.py.

- Every "k of n", interval and decimal on a slide is in docs/presentation/pack/02_NUMBERS.md, FINDINGS or (the demo's
  finder counts) TALK_MAP.
- No internal codes on the slides (the notes may carry them).
- Every picture, video and video placeholder has alt text.
- Nothing the deck adds sits in the template's reserved strip (below 4.78 in) on the main slides (those before the
  "Backup" divider: 11 in version 3, Nov 26).
- The main slides' notes carry their times, which add up to 6:00; every slide has notes.
- The tracked deck holds no video and no still of one (they show recorded model text) and stays under 5 MB; the local
  deck with the clips (gitignored) embeds three videos (A, B, C) and stays under 50 MB.
- Version 3 (Nov 26): counts written "k/n" (row labels, chart categories) are checked as "k of n"; every percent on a
  main slide is in 02_NUMBERS or FINDINGS; slide 3's effort band matches its sources (method.json, the ledger).
"""
import re
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FINAL = ROOT / "docs" / "presentation" / "final"
DECK = FINAL / "Group10_final.pptx"
LOCAL = FINAL / "local" / "Group10_final_with_video.pptx"
pytestmark = pytest.mark.skipif(not DECK.exists(), reason="the deck isn't built yet")

KN = re.compile(r"(\d{1,3}(?:,\d{3})+|\d+) of (\d{1,3}(?:,\d{3})+|\d+)")
_B = r"[+\-]?\d+(?:\.\d+)?%?"
IV = re.compile(r"\[\s*" + _B + r"\s*,\s*" + _B + r"\s*\]")
DEC = re.compile(r"[+\-]?\d+\.\d+")
SLASH = re.compile(r"(?<![\d.])(\d{1,3}(?:,\d{3})+|\d+)/(\d{1,3}(?:,\d{3})+|\d+)(?![\d.])")
PCT = re.compile(r"(?<![\d.\[,])\d{1,3}%")
CODES = re.compile(r"\b(?:F\d{1,2}|FB\d|FC\d|A\d{2}|B\d{1,2}(?:R\d)?|C\d{1,2}|E2|L[346]|T\d{1,2}|Gate \d)\b")


def norm(s):
    return re.sub(r"\s+", " ", s.replace("−", "-").replace("–", "-").replace(" ", " ").replace("**", ""))


def deck(path=DECK):
    from pptx import Presentation
    return Presentation(str(path))


def slide_text(slide):
    out = []
    for sh in slide.shapes:
        if sh.has_text_frame:
            out.append(sh.text_frame.text)
        if getattr(sh, "has_table", False) and sh.has_table:
            out += [c.text for row in sh.table.rows for c in row.cells]
        if getattr(sh, "has_chart", False) and sh.has_chart:
            out += [str(c) for c in sh.chart.plots[0].categories]
    return norm(" ".join(out))


def main_slides(d=None):
    """The slides before the "Backup" divider."""
    slides = list((d or deck()).slides)
    i = next(i for i, s in enumerate(slides) if s.shapes.title is not None and s.shapes.title.text.startswith("Backup"))
    return slides[:i]


ALLOWED = norm("\n".join((ROOT / p).read_text() for p in (
    "docs/presentation/pack/02_NUMBERS.md", "docs/FINDINGS.md", "docs/trackB/FINDINGS_B.md", "docs/trackC/FINDINGS_C.md",
    "docs/presentation/TALK_MAP.md")))


def test_every_number_on_a_slide_is_in_the_numbers_file_findings_or_talk_map():
    bad = []
    for i, s in enumerate(deck().slides, 1):
        t = slide_text(s)
        # the illustrative question's own numbers (ours, the demo's illustration: g = 9.8, options 14.7 m and 19.6 m)
        toks = [m.group(0) for m in KN.finditer(t)] + IV.findall(t) + [d for d in DEC.findall(t) if d not in ("9.8", "14.7", "19.6")]
        toks += [f"{m.group(1)} of {m.group(2)}" for m in SLASH.finditer(t)]
        bad += [(i, x) for x in toks if x not in ALLOWED]
    assert not bad, bad


def test_every_percent_on_a_main_slide_is_in_the_numbers_file_or_findings():
    """Version 3 writes rates as percents (42% -> 12%): each is in 02_NUMBERS (its k of n, rounded: N150, N151) or
    FINDINGS. Interval bounds are checked as intervals above."""
    bad = [(i, p) for i, s in enumerate(main_slides(), 1) for p in PCT.findall(slide_text(s)) if p not in ALLOWED]
    assert not bad, bad


def test_no_internal_codes_on_the_slides():
    bad = [(i, m.group(0)) for i, s in enumerate(deck().slides, 1) for m in CODES.finditer(slide_text(s))]
    assert not bad, bad


def test_every_picture_and_video_has_alt_text():
    bad = []
    for i, s in enumerate(deck().slides, 1):
        for sh in s.shapes:
            el = sh._element
            pic = el.tag.endswith("}pic")
            placeholder = sh.name == "deck video placeholder"
            if pic or placeholder:
                cnv = el.xpath(".//p:cNvPr")[0]
                if not (cnv.get("descr") or "").strip():
                    bad.append((i, sh.name))
    assert not bad, bad


def test_nothing_the_deck_adds_sits_in_the_reserved_strip():
    bad = []
    for i, s in enumerate(main_slides(), 1):
        for sh in s.shapes:
            # slide 5's video runs full height under the title (Ritik, Nov 25); inside the frame its captions and zoom
            # targets stay above the strip (captions end at y 880 of 1080 px, 0.92 + 4.22 x 880/1080 = 4.36 in)
            if sh.name in ("deck video", "deck video placeholder"):
                continue
            if sh.name.startswith("deck") and (sh.top + sh.height) / 914400 > 4.80:
                bad.append((i, sh.name, round((sh.top + sh.height) / 914400, 2)))
    assert not bad, bad


def test_the_notes_time_the_main_slides_to_six_minutes():
    slides = list(deck().slides)
    total = 0
    for s in main_slides():
        m = re.search(r"Time: (\d+):(\d\d)", s.notes_slide.notes_text_frame.text)
        assert m, s.notes_slide.notes_text_frame.text[:80]
        total += int(m.group(1)) * 60 + int(m.group(2))
    assert 300 <= total <= 360          # Ritik's simple deck (Nov 26): 5:30 in the notes, 30 s of slack
    assert all(s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip() for s in slides)


def test_the_tracked_deck_holds_no_video_and_stays_small():
    names = zipfile.ZipFile(DECK).namelist()
    assert not [n for n in names if re.search(r"\.(mp4|mov|m4v|webm)$", n, re.I)]
    stills = list((FINAL / "video").glob("**/*.png"))
    if stills:
        import hashlib
        h = {hashlib.sha256(p.read_bytes()).hexdigest() for p in stills}
        z = zipfile.ZipFile(DECK)
        media = [n for n in names if n.startswith("ppt/media/")]
        assert not [n for n in media if hashlib.sha256(z.read(n)).hexdigest() in h]
    assert DECK.stat().st_size < 5_000_000
    assert (FINAL / "Group10_final.pdf").exists()


@pytest.mark.skipif(not LOCAL.exists(), reason="the local deck with the clips is gitignored")
def test_the_local_deck_embeds_every_clip():
    z = zipfile.ZipFile(LOCAL)
    clips = [n for n in z.namelist() if n.endswith(".mp4")]
    assert len(clips) == 4                  # D (slide 6), C (backup 16), B and A (Nov 26, the simple deck)
    current = list((FINAL / "video").glob("clip_*.mp4"))
    if current:                             # each embedded clip is the current build of one of them, not a stale copy
        import hashlib
        h = {hashlib.sha256(p.read_bytes()).hexdigest() for p in current}
        assert all(hashlib.sha256(z.read(n)).hexdigest() in h for n in clips)
    assert LOCAL.stat().st_size < 50_000_000
    a, b = deck(), deck(LOCAL)
    assert len(a.slides) == len(b.slides)
    assert [s.shapes.title.text if s.shapes.title else "" for s in a.slides] == \
           [s.shapes.title.text if s.shapes.title else "" for s in b.slides]


GUIDE = FINAL / "PREP_GUIDE.md"


@pytest.mark.skipif(not GUIDE.exists(), reason="the prep guide isn't written yet")
def test_every_number_in_the_prep_guide_is_in_the_numbers_file_findings_or_talk_map():
    """The 6-minute prep guide (Phase C, Nov 25): every k of n, interval and decimal traces like the slides'."""
    t = norm(GUIDE.read_text())
    toks = [m.group(0) for m in KN.finditer(t)] + IV.findall(t) + [d for d in DEC.findall(t) if d not in ("9.8", "14.7", "19.6")]
    bad = [x for x in toks if x not in ALLOWED]
    assert not bad, bad
    assert (FINAL / "PREP_GUIDE.pdf").exists()


def test_the_effort_band_matches_its_sources():
    """The "What we built" slide's band (version 3, Nov 26; a backup in the simple deck): GPU-hours and GPU jobs from Sol's sacct (method.json), the hand-labelled rows
    and the models (method.json), the pre-registered rows of the ledger, the freeze's date (the git tag)."""
    import json
    import subprocess
    t = slide_text(next(s for s in deck().slides if s.shapes.title is not None and s.shapes.title.text == "What we built"))
    m = json.loads((ROOT / "cot-disclosure/tools/demo_template/method.json").read_text())
    g = m["running"]["gpu_total"]["v"]
    assert f"{round(g['gpu_hours'])} GPU-hours" in t and f"({g['gpu_jobs']} GPU jobs)" in t, t
    assert f"{m['counts']['hand_labels']['v']} answers labelled by hand" in t
    assert f"({m['counts']['models']['v']} with the reviewers)" in t
    ledger = (ROOT / "docs/paper/supplement/PREREGISTRATIONS.md").read_text()
    frozen = [l for l in ledger.splitlines() if "| pre-registered |" in l and "post-freeze addendum" not in l]
    assert f"{len(frozen)} rules written before the data" in t        # the frozen results' rules (C27, Nov 26, is after)
    tag = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%cd", "--date=format:%b %-d",
                          "results-freeze-2026-11-18"], capture_output=True, text=True).stdout.strip()
    assert tag == "Nov 18" and "Nov 18 results frozen" in t


@pytest.mark.parametrize("which", ["tracked", "local"])
def test_every_timing_node_names_a_shape_on_its_slide(which):
    """Nov 26: a replaced video left <p:timing> naming a deleted shape (spid 4 on slides 6 and 16), so PowerPoint
    offered a repair. Every spid in a slide's timing must be the id of a shape on that slide."""
    path = DECK if which == "tracked" else LOCAL
    if not path.exists():
        pytest.skip("the local deck is gitignored")
    bad = []
    for i, s in enumerate(deck(path).slides, 1):
        ids = {e.get("id") for e in s._element.xpath(".//p:cNvPr")}
        spids = {e.get("spid") for e in s._element.xpath(".//p:timing//*[@spid]")}
        if spids - ids:
            bad.append((i, sorted(spids - ids)))
    assert not bad, bad
