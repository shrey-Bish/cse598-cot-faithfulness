"""docs/GLOSSARY.md is written from tools/explainer/names.json by tools/make_glossary.py: every plain name and every ID
appears in it, and the committed file equals a fresh generation."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cot-disclosure" / "tools"))

import make_glossary  # noqa: E402

NAMES = ROOT / "cot-disclosure" / "tools" / "explainer" / "names.json"
GLOSSARY = ROOT / "docs" / "GLOSSARY.md"


def _entries():
    data = json.loads(NAMES.read_text())
    return [n for g in data["groups"] for n in g["names"]]


def test_every_plain_name_and_id_appears():
    text = GLOSSARY.read_text()
    for e in _entries():
        assert e["plain"] in text, e["plain"]
        for i in e["ids"]:
            assert i in text, (e["plain"], i)


def test_every_group_heading_appears():
    text = GLOSSARY.read_text()
    for g in json.loads(NAMES.read_text())["groups"]:
        assert "## " + g["group"] in text


def test_committed_file_equals_fresh_generation():
    assert GLOSSARY.read_text() == make_glossary.render(NAMES)


def test_generation_is_byte_stable():
    assert make_glossary.render(NAMES) == make_glossary.render(NAMES)
