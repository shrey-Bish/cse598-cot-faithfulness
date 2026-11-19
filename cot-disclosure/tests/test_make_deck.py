"""The slide-shell deck is built from docs/presentation/TALK_MAP.md, so the two can't drift."""
import hashlib
import re
import sys
from datetime import datetime
from pathlib import Path

import pytest
from pptx import Presentation
from pptx.util import Emu, Inches

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cot-disclosure" / "tools"))
import make_deck  # noqa: E402

FIG = ROOT / "docs" / "paper" / "figures"
CODE = re.compile(r"\b[A-Z]{1,2}\d+[A-Z]?\d*\b")


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("deck") / "deck.pptx"
    make_deck.build(out)
    return Presentation(str(out))


@pytest.fixture(scope="module")
def rows():
    return make_deck.parse_talk_map()["rows"]


@pytest.fixture(scope="module")
def lines():
    return make_deck.parse_talk_map()["lines"]


def pic_hashes(slide):
    return [hashlib.sha256(s.image.blob).hexdigest() for s in slide.shapes if s.shape_type == 13]


def title_of(slide):
    return next(s for s in slide.shapes if s.name == "Title").text_frame.text


def extras(rows):
    """(row, figure) for every figure after a row's first: each gets a full-size backup slide after the limits slide."""
    return [(r, f) for r in rows for f in r["figures"][1:]]


def limits_slide(built):
    return next(s for s in built.slides if title_of(s) == "Limits and next steps")


def test_slide_count_one_per_row_then_one_backup_per_extra_figure(built, rows):
    # row 0 is the title slide, the last row the limits slide; then the backups
    assert len(rows) == 14
    assert len(built.slides) == len(rows) + len(extras(rows))
    assert rows[0]["num"] == 0 and rows[-1]["title"] == "Limits and next steps"
    assert title_of(built.slides[len(rows) - 1]) == "Limits and next steps"


def test_slide_size_16x9(built):
    assert built.slide_width == Inches(13.333) or abs(built.slide_width - Inches(13.333)) < 2000
    assert built.slide_height == Inches(7.5)


def test_every_named_figure_exists(rows):
    for r in rows:
        for f in r["figures"]:
            assert (FIG / f).is_file(), f


def sha(f):
    return hashlib.sha256((FIG / f).read_bytes()).hexdigest()


def test_titles_and_pictures_match_the_map(built, rows):
    slides = list(built.slides)
    for slide, r in zip(slides, rows):
        assert title_of(slide) == r["title"]
        assert pic_hashes(slide) == [sha(f) for f in r["figures"][:1]], r["title"]
    for slide, (r, f) in zip(slides[len(rows):], extras(rows)):
        assert title_of(slide) == r["title"] + " (backup)"
        assert pic_hashes(slide) == [sha(f)], f


def test_every_named_figure_is_in_the_deck_once_and_full_size(built, rows):
    named = [sha(f) for r in rows for f in r["figures"]]
    shown = [h for s in built.slides for h in pic_hashes(s)]
    assert sorted(named) == sorted(shown)
    assert len(extras(rows)) >= 3
    for s in built.slides:
        for pic in (x for x in s.shapes if x.shape_type == 13):
            assert pic.width >= Inches(11) or pic.height >= Inches(5.4), (title_of(s), pic.width, pic.height)


def test_no_internal_code_in_titles(built):
    for s in built.slides:
        assert not CODE.search(title_of(s)), title_of(s)


def test_codes_are_in_the_footer(built, rows):
    for s, r in zip(built.slides, rows):
        if r["evidence"]:
            foot = next(x for x in s.shapes if x.name == "Footer").text_frame.text
            assert r["evidence"] in foot


def test_no_speaker_notes(built):
    for s in built.slides:
        assert not s.has_notes_slide or not s.notes_slide.notes_text_frame.text.strip()


def test_no_animation(built):
    for s in built.slides:
        assert "<p:timing" not in s._element.xml and "<p:transition" not in s._element.xml


def test_limits_slide_is_short_lines(built, lines):
    assert 3 <= len(lines["Limits"]) <= 5 and 3 <= len(lines["Next steps"]) <= 5
    last = limits_slide(built)
    for shp in last.shapes:
        if shp.has_text_frame:
            text = shp.text_frame.text
            for p in shp.text_frame.paragraphs:
                assert len(p.text) <= 90, p.text
            assert len(re.findall(r"[.!?](\s|$)", text)) <= 2 or shp.name in ("Footer",)
    body = " ".join(s.text_frame.text for s in last.shapes if s.has_text_frame)
    for l in lines["Limits"] + lines["Next steps"]:
        assert l in body


def test_core_properties_fixed_and_neutral(built):
    cp = built.core_properties
    assert cp.author == "CSE 598 Group 10" and cp.last_modified_by == "CSE 598 Group 10"
    assert cp.title == "Do thinking modes make chain-of-thought more honest?"
    assert cp.created == datetime(2026, 11, 18, 21, 4) and cp.modified == datetime(2026, 11, 18, 21, 4)
    for v in (cp.author, cp.last_modified_by, cp.title, cp.comments or ""):
        assert not re.search(r"python-pptx|claude|anthropic", v, re.I)


def test_title_slide_text(built):
    txt = " | ".join(s.text_frame.text for s in built.slides[0].shapes if s.has_text_frame)
    for want in ("CSE 598", "Group 10", "Shrey Bishnoi", "Arsha Jindal", "Ritik Agarwal", "Nov 24, 2026"):
        assert want in txt


def test_deterministic(tmp_path):
    a, b = tmp_path / "a.pptx", tmp_path / "b.pptx"
    make_deck.build(a)
    make_deck.build(b)
    def sig(p):
        pr = Presentation(str(p))
        return [(title_of(s), pic_hashes(s)) for s in pr.slides]
    assert sig(a) == sig(b)
