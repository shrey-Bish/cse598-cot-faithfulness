"""The results demo (tools/build_demo.py): one self-contained HTML page built from the tracked numbers-only summaries.
Every number in its data block names its source and equals it; the page makes no network request; no example text
reaches the tracked page; a missing number stops the build. No calls, no network."""
import json
import math
import re
import shutil
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "tools"))

import build_demo as bd  # noqa: E402

SUM = CODE / "results" / "summaries"
SENTINELS = ("SENTINEL-FINAL-7f3a", "SENTINEL-PRIVATE-91bc", "SENTINEL-NOTE-c4d2")
SYNTH = {"seed": "test-seed", "illustrative": "illustrative, drawn by seed", "missing": [],
         "examples": [{"section": "s5", "source": "L6", "row": 1, "run_id": "r1", "system": "lora", "channel": "pasted",
                       "label": "says_changed", "hint_letter": "B", "illustrative": "illustrative, drawn by seed",
                       "final_answer": SENTINELS[0] + " (B)", "private": SENTINELS[1], "note": SENTINELS[2]}]}
TEXTY = re.compile(r"final_answer|private|text|note", re.IGNORECASE)


def data_block(page):
    m = re.search(r'<script type="application/json" id="demo-data">(.*?)</script>', page, re.S)
    assert m, "no data block"
    return json.loads(m.group(1))


def walk(o, path=()):
    yield path, o
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, path + (k,))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, path + (i,))


def sourced(o):
    return isinstance(o, dict) and "v" in o and "src" in o


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    d = tmp_path_factory.mktemp("demo")
    ex = d / "examples.json"
    ex.write_text(json.dumps(SYNTH))
    tracked, local = d / "docs" / "index.html", d / "local" / "index.html"
    bd.build(summaries=SUM, findings=bd.FINDINGS, out=tracked, examples=ex, local_out=local)
    return tracked.read_text(), local.read_text()


# ---------------------------------------------------------------- (a) every number equals its summary
def test_every_number_in_the_data_block_equals_its_source(built):
    data = data_block(built[0])
    cache, rows_cache, checked = {}, {}, 0
    for path, o in walk(data):
        if not sourced(o):
            continue
        assert isinstance(o["v"], (int, float)) and not isinstance(o["v"], bool), path
        if "key" in o:
            src = CODE / o["src"]
            assert o["src"].startswith("results/summaries/") and src.exists(), (path, o["src"])
            x = cache.setdefault(src, json.loads(src.read_text()))
            for k in o["key"]:
                x = x[k]
            assert x == o["v"] or math.isclose(x, o["v"], rel_tol=1e-12, abs_tol=1e-15), (path, o, x)
        else:
            assert o["fn"] in bd.FNS, (path, o["fn"])
            rows = rows_cache.setdefault(o["fn"], bd.FNS[o["fn"]](SUM))
            hits = [r for r in rows if all(r.get(k) == v for k, v in o["where"].items())]
            assert len(hits) == 1, (path, o["where"], len(hits))
            assert math.isclose(hits[0][o["field"]], o["v"], rel_tol=1e-12, abs_tol=1e-15), (path, o)
        checked += 1
    assert checked > 300, checked                       # the page's numbers, not a handful


def test_no_number_in_the_data_block_lacks_a_source(built):
    data = data_block(built[0])
    for path, o in walk(data):
        if isinstance(o, (int, float)) and not isinstance(o, bool):
            assert len(path) >= 2, path
            parent = data
            for k in path[:-1]:
                parent = parent[k]
            inside_key = isinstance(parent, list) and len(path) >= 2 and path[-2] == "key"
            assert inside_key or (path[-1] == "v" and sourced(parent)), f"a bare number at {path}"


def test_the_anchor_numbers_are_the_findings(built):
    """A few numbers FINDINGS quotes, read back from the page's own data (so the right keys were taken)."""
    d = data_block(built[0])
    v = lambda o: o["v"]  # noqa: E731
    l6 = d["s5"]["l6"]
    assert (v(l6["lora"]["k"]), v(l6["lora"]["n"]), v(l6["instruction"]["k"]), v(l6["instruction"]["n"])) == (37, 42, 18, 42)
    assert round(v(l6["agreement"]) * v(l6["rows"])) == 82 and v(l6["rows"]) == 84                  # J-opus, F45
    b = {r["study"]: r for r in d["s5"]["b1r2"]}
    f = b["B1R2"]["following"]
    assert (v(f["base_k"]), v(f["k"]), v(f["n"])) == (82, 49, 240)
    assert round(v(f["d"]) * 100, 1) == -13.8 and round(v(f["lo"]) * 100, 1) == -20.0
    x = d["s5"]["crossings"]["a40"]
    assert (round(v(x["p"]), 2), round(v(x["lo"]), 2), round(v(x["hi"]), 2)) == (0.36, 0.22, 0.50)
    t = d["s2"]["title"]
    assert (v(t["f29"]["private"]["k"]), v(t["f29"]["private"]["n"]), v(t["f29"]["final"]["k"]),
            v(t["f29"]["final"]["n"])) == (141, 145, 0, 143)
    assert round(v(t["fb1"]["d"]) * 100) == -14
    rows = {(r["model"], r["setting"]): r for r in d["s1"]["gate2"]}
    assert len(rows) == 13                                                  # all eight models, every setting
    assert round(v(rows[("Qwen3 30B Thinking", "thinking always")]["d_pasted"]["d"]) * 100) == 35


# ---------------------------------------------------------------- (b) no network request
NET = (r"""(?:src|href|action|poster|data)\s*=\s*["']?\s*(?:https?:)?//""", r"""url\(\s*["']?\s*(?:https?:)?//""",
       r"@import", r"\bfetch\s*\(", r"XMLHttpRequest", r"\bimport\s*\(", r"<iframe", r"<object", r"<embed",
       r"""<link[^>]*rel\s*=\s*["']?stylesheet""", r"WebSocket", r"EventSource", r"sendBeacon", r"<script[^>]*\ssrc=")


@pytest.mark.parametrize("which", [0, 1])
def test_the_page_makes_no_network_request(built, which):
    page = built[which]
    for rx in NET:
        assert not re.search(rx, page, re.IGNORECASE), rx
    for m in re.finditer(r"""https?://[^\s"'<>)]*""", page):
        assert m.group(0) == "http://www.w3.org/2000/svg", m.group(0)       # the SVG namespace, never fetched


# ---------------------------------------------------------------- (c) no text field leaks into the tracked page
def test_example_text_reaches_only_the_local_page(built):
    tracked, local = built
    for s in SENTINELS[:2]:
        assert s not in tracked
        assert s in local
    assert 'id="demo-examples"' not in tracked and 'id="examples"' not in tracked
    assert 'id="demo-examples"' in local


def test_the_tracked_page_holds_no_text_field(built):
    tracked = built[0]
    for path, o in walk(data_block(tracked)):
        if path and isinstance(path[-1], str) and TEXTY.search(path[-1]):
            assert not isinstance(o, str), path
    assert not re.search(r'"[^"<>]*(?:final_answer|private|text|note)[^"<>]*"\s*:\s*"', tracked, re.IGNORECASE)


def test_without_examples_both_pages_are_the_same_page(tmp_path):
    out, local = tmp_path / "index.html", tmp_path / "local" / "index.html"
    bd.build(summaries=SUM, findings=bd.FINDINGS, out=out, examples=tmp_path / "none.json", local_out=local)
    assert out.exists() and not local.exists()


def test_the_build_is_byte_stable(built, tmp_path):
    out = tmp_path / "again.html"
    bd.build(summaries=SUM, findings=bd.FINDINGS, out=out, examples=tmp_path / "none.json", local_out=tmp_path / "x.html")
    assert out.read_text() == built[0]


# ---------------------------------------------------------------- (d) a missing number stops the build
@pytest.fixture
def summaries_copy(tmp_path):
    dst = tmp_path / "summaries"
    shutil.copytree(SUM, dst, ignore=shutil.ignore_patterns("*.png", "*.svg"))
    return dst


def test_the_build_fails_when_a_summary_is_missing(summaries_copy, tmp_path, capsys):
    (summaries_copy / "trackB" / "b20_report.json").unlink()
    with pytest.raises(SystemExit) as e:
        bd.main(["--summaries", str(summaries_copy), "--out", str(tmp_path / "x.html"),
                 "--examples", str(tmp_path / "none.json"), "--local-out", str(tmp_path / "y.html")])
    assert e.value.code not in (0, None)
    assert "b20_report.json" in capsys.readouterr().err
    assert not (tmp_path / "x.html").exists()


def test_the_build_fails_when_a_key_is_missing(summaries_copy, tmp_path):
    p = summaries_copy / "trackA" / "labels" / "l6_report.json"
    d = json.loads(p.read_text())
    del d["discloses"]["lora"]["k"]
    p.write_text(json.dumps(d))
    with pytest.raises(bd.MissingNumber) as e:
        bd.build(summaries=summaries_copy, findings=bd.FINDINGS, out=tmp_path / "x.html",
                 examples=tmp_path / "none.json", local_out=tmp_path / "y.html")
    assert "l6_report.json" in str(e.value) and "discloses" in str(e.value)


def test_the_build_fails_when_findings_lose_a_wording(tmp_path):
    f = tmp_path / "FINDINGS.md"
    f.write_text(bd.FINDINGS.read_text().replace("B1's verdict on the 30 stays primary", "B1's verdict"))
    with pytest.raises(bd.MissingNumber) as e:
        bd.build(summaries=SUM, findings=f, out=tmp_path / "x.html", examples=tmp_path / "none.json",
                 local_out=tmp_path / "y.html")
    assert "stays primary" in str(e.value)


# ---------------------------------------------------------------- the presentation's own rules
def test_sections_keys_and_labels(built):
    page = built[0]
    for i in range(7):
        assert f'id="s{i}"' in page
    for key in ("ArrowRight", "ArrowLeft", "PageDown", "PageUp", "Home", "End", "hashchange", "prefers-color-scheme",
                "prefers-reduced-motion", '"t"', '"i"'):
        assert key in page, key
    assert page.count("EXPLORATORY (POST HOC)") >= 3                        # the scatter, Acc(p), the keyword bars
    text = re.sub(r"\s+", " ", page)
    assert "Training made the answer more candid about a hint it followed, in hand labels, without making it follow less." in text
    assert ("So the title question is answered mixed: with thinking on, Qwen3-8B names the tool in its private reasoning "
            "but not in its final answer (F29); in gpt-oss-20b, more reasoning effort changes nothing (F37); in Nemotron "
            "3 Nano, the answer after the inserted tool turn is less bare with thinking on (FB1).") in text
    assert "B1's verdict on the 30 stays primary" in text
    for banned in ("honesty solved", "a yes for training"):
        assert banned not in text.lower()
