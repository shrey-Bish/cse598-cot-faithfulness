"""The Hint Explainer (tools/build_demo.py, tools/explainer/): one self-contained HTML page built from the tracked
numbers-only summaries. Every number in its data block names its source and equals it; every number a caption or the
article shows comes from that block; no internal code is visible outside the IDs toggle; the page makes no network
request; no example text reaches the tracked page; a missing number stops the build. No calls, no network.
The Playwright tests skip cleanly when Playwright or its browser is missing."""
import json
import math
from html.parser import HTMLParser
import re
import shutil
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "tools"))
sys.path.insert(0, str(CODE / "progress"))

import build_demo as bd  # noqa: E402

SUM = CODE / "results" / "summaries"
EXPL = CODE / "tools" / "explainer"
SENTINELS = ("SENTINEL-FINAL-7f3a", "SENTINEL-PRIVATE-91bc", "SENTINEL-NOTE-c4d2")
SYNTH = {"seed": "test-seed", "illustrative": "illustrative, drawn by seed", "missing": [],
         "examples": [{"section": "s5", "source": "L6", "row": 1, "run_id": "r1", "system": "lora", "channel": "pasted",
                       "label": "says_changed", "hint_letter": "B", "illustrative": "illustrative, drawn by seed",
                       "final_answer": SENTINELS[0] + " (B)", "private": SENTINELS[1], "note": SENTINELS[2]}]}
TEXTY = re.compile(r"final_answer|private|text|note", re.IGNORECASE)
# the internal codes no visible text may show outside the IDs toggle (model names like 30B-A3B must not trip it)
CODES = re.compile(r"\b(?:[ABCDEFGHLR]\d{1,2}[a-z]?(?:R\d)?|F[BC]\d|J-(?:opus|qwen|olmo)|Gate \d|Step \d+|set A|prompt_only"
                   r"|tool_injected|tool_pasted|tool_real|Track [ABC])\b")


_COLLECTED = []


def collected():
    """collect() takes seconds: once per test run."""
    if not _COLLECTED:
        _COLLECTED.append(bd.collect())
    return _COLLECTED[0]


def data_block(page, ident="demo-data"):
    m = re.search(r'<script type="application/json" id="%s">(.*?)</script>' % ident, page, re.S)
    assert m, f"no {ident} block"
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
    return tracked.read_text(), local.read_text(), tracked, local


# ---------------------------------------------------------------- (a) every number equals its summary
def test_every_number_in_the_data_block_equals_its_source():
    cache, rows_cache, checked = {}, {}, 0
    for path, o in walk(collected()):
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


def test_no_number_in_collect_lacks_a_source():
    data = collected()
    for path, o in walk(data):
        if isinstance(o, (int, float)) and not isinstance(o, bool):
            parent = data
            for k in path[:-1]:
                parent = parent[k]
            inside_key = isinstance(parent, list) and len(path) >= 2 and path[-2] == "key"
            where = isinstance(parent, list) and len(path) >= 3 and path[-3] == "where"
            assert inside_key or (path[-1] == "v" and sourced(parent)) or where, f"a bare number at {path}"


def test_the_pages_data_is_compact_collect(built):
    assert data_block(built[0]) == bd.compact(collected())
    assert data_block(built[0]) == data_block(built[1])


def test_the_anchor_numbers_are_the_findings(built):
    """A few numbers FINDINGS quotes, read back from the page's own data (so the right keys were taken)."""
    d = data_block(built[0])
    l6 = d["s5"]["l6"]
    assert (l6["lora"]["k"], l6["lora"]["n"], l6["instruction"]["k"], l6["instruction"]["n"]) == (37, 42, 18, 42)
    f = {r["study"]: r for r in d["s5"]["b1r2"]}["B1R2"]["following"]
    assert (f["base_k"], f["k"], f["n"]) == (82, 49, 240)
    x = d["s5"]["crossings"]["a40"]
    assert (round(x["p"], 2), round(x["lo"], 2), round(x["hi"], 2)) == (0.36, 0.22, 0.50)
    t = d["s2"]["title"]
    assert (t["f29"]["private"]["k"], t["f29"]["private"]["n"], t["f29"]["final"]["k"], t["f29"]["final"]["n"]) \
        == (141, 145, 0, 143)
    assert round(d["s3"]["share"][0]["m"], 2) == 0.90 and d["s3"]["readout"] == [15, 19, 23]
    r0 = d["s4"]["reviewers"][0]
    assert (r0["answer_only"]["k"], r0["plus_tool_log"]["k"], r0["plus_tool_log"]["n"]) == (59, 3, 73)
    assert (d["s4"]["checker"]["caught"]["k"], d["s4"]["checker"]["caught"]["n"]) == (53, 53)
    assert (d["s4"]["checker"]["false_alarms"]["k"], d["s4"]["checker"]["false_alarms"]["n"]) == (7, 45)
    st = d["x"]["settings"]
    assert len(st) == 13 and len({r["model"] for r in st}) == 8
    assert (st[1]["sources"]["user"]["f"]["k"], st[1]["sources"]["call"]["f"]["k"], st[1]["sources"]["call"]["f"]["n"]) \
        == (1, 147, 162)
    dose = d["s1"]["dose"][2]
    assert (dose["manual"]["k"], dose["manual"]["n"], dose["pasted"]["k"], dose["pasted"]["n"]) == (78, 159, 63, 158)
    assert d["x"]["fresh_questions"] == 120 and d["x"]["test_questions"] == 54
    assert d["s3"]["qwen"]["n_layers"] == 36 and d["s3"]["qwen"]["at"] == [21, 22, 29]


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


def test_the_page_is_small_and_reads_nothing_from_the_old_demo(built):
    assert len(built[0].encode()) < 700_000
    assert "demo_page" not in (CODE / "tools" / "build_demo.py").read_text()
    assert not (bd.PAGE / "demo.js").exists() and bd.PAGE.name == "explainer"


# ---------------------------------------------------------------- (c) no text field leaks into the tracked page
def test_example_text_reaches_only_the_local_page(built):
    tracked, local = built[:2]
    for s in SENTINELS[:2]:
        assert s not in tracked
        assert s in local
    assert 'id="demo-examples"' not in tracked and 'id="demo-examples"' in local


def test_the_tracked_page_holds_no_text_field(built):
    tracked = built[0]
    for path, o in walk(data_block(tracked)):
        if path and isinstance(path[-1], str) and TEXTY.search(path[-1]):
            assert not isinstance(o, str), path
    blocks = " ".join(re.findall(r'<script type="application/json"[^>]*>(.*?)</script>', tracked, re.S))
    assert blocks and not re.search(r'"[^"<>]*(?:final_answer|private|text|note)[^"<>]*"\s*:\s*"', blocks, re.IGNORECASE)


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
    assert e.value.code == 1
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


def test_the_build_fails_when_the_new_numbers_are_missing(summaries_copy, tmp_path):
    p = summaries_copy / "trackA" / "qwen8b_mech" / "qwen8b_readout.json"
    d = json.loads(p.read_text())
    del d["localization"]["n_layers"]
    p.write_text(json.dumps(d))
    with pytest.raises(bd.MissingNumber) as e:
        bd.build(summaries=summaries_copy, findings=bd.FINDINGS, out=tmp_path / "x.html",
                 examples=tmp_path / "none.json", local_out=tmp_path / "y.html")
    assert "n_layers" in str(e.value)


@pytest.mark.parametrize("sentence", bd.WORDING)
def test_the_build_fails_when_findings_lose_a_quoted_sentence(sentence, tmp_path):
    f = tmp_path / "FINDINGS.md"
    f.write_text(bd.normal(bd.FINDINGS.read_text()).replace(bd.normal(sentence), "x"))
    with pytest.raises(bd.MissingNumber) as e:
        bd.build(summaries=SUM, findings=f, out=tmp_path / "x.html", examples=tmp_path / "none.json",
                 local_out=tmp_path / "y.html")
    assert "no longer has the wording" in str(e.value)


def test_the_build_fails_when_a_template_is_missing(tmp_path, monkeypatch):
    d = tmp_path / "explainer"
    shutil.copytree(EXPL, d)
    (d / "tour.json").unlink()
    monkeypatch.setattr(bd, "PAGE", d)
    with pytest.raises((bd.MissingNumber, FileNotFoundError)):
        bd.build(summaries=SUM, findings=bd.FINDINGS, out=tmp_path / "x.html", examples=tmp_path / "none.json",
                 local_out=tmp_path / "y.html")


# ---------------------------------------------------------------- (e) every number shown comes from DATA
PH = re.compile(r"\{([^{}:]+)(?::(\w+))?\}")


def resolve(data, path):
    o = data
    for tok in re.findall(r"[^.\[\]]+", path):
        o = len(o) if tok == "length" else o[int(tok)] if isinstance(o, list) else o[tok]
    return o


def fmt(v, f):
    if f == "2":
        return f"{v:.2f}"
    if f == "pct":
        return f"{math.floor(v * 100 + 0.5)}%"
    if f == "minus1":
        return str(v - 1)
    if f == "pts":
        return f"{v * 100:+.0f}"
    assert f is None, f
    return str(v)


def fill(data, tpl):
    return PH.sub(lambda m: fmt(resolve(data, m.group(1)), m.group(2)), tpl)


def test_tour_captions_hold_no_digit_outside_placeholders_and_every_placeholder_resolves(built):
    tour, data = data_block(built[0], "demo-tour"), data_block(built[0])
    assert len(tour) == 7
    for i, sc in enumerate(tour):
        assert not re.search(r"\d", PH.sub("", sc["caption"])), (i, sc["caption"])
        for m in PH.finditer(sc["caption"]):
            resolve(data, m.group(1))
        assert PH.search(sc["caption"]), "a caption without a number from DATA"
        assert isinstance(resolve(data, "x.settings")[sc["row"]], dict)


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        self.skip += tag in ("script", "style")
        self.out += [v for k, v in attrs if k in ("aria-label", "title", "data-tip") and v]

    def handle_endtag(self, tag):
        self.skip -= tag in ("script", "style")

    def handle_data(self, d):
        if not self.skip:
            self.out.append(d)


def visible_literals():
    """The page's own strings that could show a number: the template's text and attributes, and the script's literals."""
    p = _Text()
    p.feed((EXPL / "template.html").read_text())
    js = (EXPL / "explainer.js").read_text()
    lits = re.findall(r'"((?:[^"\\\n]|\\.)*)"|\'((?:[^\'\\\n]|\\.)*)\'|`((?:[^`\\]|\\.)*)`', js)
    return p.out, [a or b or c for a, b, c in lits]


# a digit in a visible string is allowed only when it is one of these (a UI constant, not a result), each with its reason
ALLOW = {"Run 20 times": "UI constant: the batch size of the tally (also its dots)",
         "1 to 7": "the key hint for the tour's scenes",
         "1-7": "the key hint for the tour's scenes",
         "(1 - p)": "the slider's formula: the complement of p, not a result",
         "95%": "the interval level, a method constant stated once, not a result"}


def test_no_hard_coded_result_number_in_visible_strings(built):
    data = data_block(built[0])
    names = sorted({r["model"] for r in data["x"]["settings"]} | {r["name"] for r in data["s4"]["reviewers"]}
                   | {"Qwen3-8B", "Qwen3", "Olmo 3", "Gemma 4", "Nemotron 3", "Granite 4.2", "gpt-oss-20b"}, key=len, reverse=True)
    text, lits = visible_literals()
    bad = []
    for s in text + lits:
        t = re.sub(r"<[^>]*>", " ", PH.sub("", s))
        if t.lstrip().startswith(("#", ".")):
            continue                                                     # a selector, not text
        for n in names:
            t = t.replace(n, " ")
        for a in ALLOW:
            t = t.replace(a, " ")
        t = re.sub(r"\\u[0-9a-fA-F]{4}|&#?\w+;|#[0-9a-fA-F]{3,8}\b|\b\d+(?:px|rem|em|ms|s|vh|vw|%)\b", " ", t)
        # only strings that read as text (a letter run, a space and a digit)
        if len(re.findall(r"[A-Za-z]{3,}", t)) >= 2 and re.search(r"\d", t) and " " in t.strip():
            bad.append(t.strip()[:100])
    assert not bad, "\n".join(bad)


def test_the_quoted_findings_sentences_are_on_the_page_and_nothing_overclaims(built):
    text = bd.normal(re.sub(r"<[^>]+>", " ", built[0]))
    for w in bd.WORDING:
        assert bd.normal(w) in text, w
        assert not CODES.search(w), w                                    # quoted sentences carry no internal code
    for banned in ("honesty solved", "makes cot honest", "thinking makes it honest", "a yes for training"):
        assert banned not in text


def test_tour_json_and_names_are_in_the_page(built):
    assert data_block(built[0], "demo-names")["groups"]
    assert [sc["row"] for sc in data_block(built[0], "demo-tour")]


# ---------------------------------------------------------------- (f) Playwright: the page as it runs
try:
    from playwright.sync_api import sync_playwright
except Exception:                                                        # noqa: BLE001
    sync_playwright = None


@pytest.fixture(scope="module")
def browser():
    if sync_playwright is None:
        pytest.skip("Playwright is not installed")
    pw = sync_playwright().start()
    try:
        b = pw.chromium.launch()
    except Exception as e:                                               # noqa: BLE001
        pw.stop()
        pytest.skip(f"no Chromium: {e}")
    yield b
    b.close()
    pw.stop()


def open_page(browser, path, w=1920, h=1080, reduced=True):
    ctx = browser.new_context(viewport={"width": w, "height": h},
                              reduced_motion="reduce" if reduced else "no-preference")
    page = ctx.new_page()
    log = {"requests": [], "errors": []}
    page.on("request", lambda r: log["requests"].append(r.url))
    page.on("console", lambda m: log["errors"].append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: log["errors"].append(str(e)))
    page.goto(Path(path).resolve().as_uri())
    page.wait_for_selector("body[data-ready='1']")
    return ctx, page, log


def test_no_request_but_the_file_and_no_console_error(browser, built):
    ctx, page, log = open_page(browser, built[2])
    page.click("#run")
    page.click("#play")
    for i in "1234567":
        page.keyboard.press(i)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    assert all(u.startswith("file://") or u.startswith("data:") for u in log["requests"]), log["requests"]
    assert not log["errors"], log["errors"]
    ctx.close()


def test_each_scene_shows_its_caption_from_data_and_the_tour_goes_back(browser, built):
    data, tour = data_block(built[0]), data_block(built[0], "demo-tour")
    ctx, page, log = open_page(browser, built[2])
    page.click("#play")
    for i, sc in enumerate(tour):
        page.keyboard.press(str(i + 1))
        page.wait_for_function("n => document.querySelector('#tour').dataset.scene == n", arg=str(i + 1))
        assert page.inner_text("#tour-caption").strip() == fill(data, sc["caption"]), i
        assert page.evaluate("document.querySelector('#model').selectedIndex >= 0")
    page.keyboard.press("ArrowLeft")
    assert page.get_attribute("#tour", "data-scene") == "6"
    page.keyboard.press("ArrowRight")
    page.keyboard.press(" ")
    assert page.get_attribute("#tour", "data-scene") == "7"                # the last scene stays the last
    page.keyboard.press("Escape")                                           # the first closes the open stage
    assert page.get_attribute("body", "data-tour") == "1"
    page.keyboard.press("Escape")                                           # the second leaves the story
    assert page.get_attribute("body", "data-tour") in (None, "0")
    assert not log["errors"], log["errors"]
    ctx.close()


def test_a_scene_sets_the_controls(browser, built):
    data, tour = data_block(built[0]), data_block(built[0], "demo-tour")
    ctx, page, _ = open_page(browser, built[2])
    page.click("#play")
    page.keyboard.press("2")
    row = data["x"]["settings"][tour[1]["row"]]
    assert page.eval_on_selector("#model", "e => e.selectedOptions[0].textContent") == row["model"]
    assert page.get_attribute("#sources [aria-pressed='true']", "data-src") == tour[1]["source"]
    ctx.close()


def test_no_internal_code_is_visible_outside_the_ids_toggle_in_any_scene_or_stage(browser, built):
    tour = data_block(built[0], "demo-tour")
    ctx, page, _ = open_page(browser, built[2])
    texts = []
    page.click("#run20")
    texts.append(page.inner_text("body"))
    for i in range(len(tour)):
        page.click("#play") if page.get_attribute("body", "data-tour") != "1" else None
        page.keyboard.press(str(i + 1))
        page.wait_for_timeout(50)
        texts.append(page.inner_text("body"))
    page.keyboard.press("Escape")
    for stage in range(1, 6):
        page.click(".sw") if stage == 5 and not page.is_checked("#review") else None
        page.click(f".stage[data-stage='{stage}'] .stage-head")
        page.wait_for_selector("#expand.open")
        texts.append(page.inner_text("body"))
        page.keyboard.press("Escape")
    page.select_option("#model", index=2)
    page.select_option("#fix", index=2) if page.is_enabled("#fix") else None
    texts.append(page.inner_text("body"))
    for t in texts:
        found = CODES.findall(t)
        assert not found, found
    assert not CODES.search(page.inner_text("body"))
    # the toggle reveals them: the glossary and the small tags
    page.click("#ids-toggle")
    shown = page.inner_text("body")
    assert "Gate 2" in shown and "GLOSSARY.md" in page.inner_html("body")
    assert CODES.search(shown)
    page.click("#ids-toggle")
    assert not CODES.search(page.inner_text("body"))
    ctx.close()


def test_choosing_a_fix_on_the_test_questions_switches_to_the_fresh_ones_with_a_note(browser, built):
    ctx, page, _ = open_page(browser, built[2])
    page.select_option("#model", label="Olmo 3 7B Think")
    assert page.is_enabled("#setting button[data-v='test']")
    page.click("#setting button[data-v='test']")
    assert page.is_enabled("#fix")                                            # enabled on both Olmo settings
    page.select_option("#fix", index=2) if page.is_enabled("#fix") else None
    texts.append(page.inner_text("body"))
    for t in texts:
        found = CODES.findall(t)
        assert not found, found
    assert not CODES.search(page.inner_text("body"))
    # the toggle reveals them: the glossary and the small tags
    page.click("#ids-toggle")
    shown = page.inner_text("body")
    assert "Gate 2" in shown and "GLOSSARY.md" in page.inner_html("body")
    assert CODES.search(shown)
    page.click("#ids-toggle")
    assert not CODES.search(page.inner_text("body"))
    ctx.close()


def test_choosing_a_fix_on_the_test_questions_switches_to_the_fresh_ones_with_a_note(browser, built):
    ctx, page, _ = open_page(browser, built[2])
    page.select_option("#model", label="Olmo 3 7B Think")
    assert page.is_enabled("#setting button[data-v='test']")
    page.click("#setting button[data-v='test']")
    assert page.is_disabled("#fix") or page.eval_on_selector("#fix", "e => e.value") == "none"
    page.evaluate("document.querySelector('#fix').disabled = false")        # a click lands on a note, not a dead control
    page.select_option("#fix", index=2)
    assert page.get_attribute("#setting [aria-pressed='true']", "data-v") == "fresh"
    assert page.is_visible("#fixnote") and page.inner_text("#fixnote").strip()
    page.select_option("#model", label="Qwen3-8B")
    assert page.is_disabled("#fix")
    ctx.close()


def test_runs_are_seeded_and_never_forced(browser, built):
    ctx, page, _ = open_page(browser, built[2])
    page.select_option("#model", index=1)
    page.click("#run20")
    a = page.inner_text("#tally")
    ctx.close()
    ctx, page, _ = open_page(browser, built[2])
    page.select_option("#model", index=1)
    page.click("#run20")
    assert page.inner_text("#tally") == a                                   # the same seed, the same dots
    ctx.close()


def test_the_local_page_shows_a_real_run_and_the_tracked_page_has_no_such_control(browser, built):
    ctx, page, _ = open_page(browser, built[3])
    page.click("#real-run")
    out = page.inner_text("#real-run-out")
    assert SENTINELS[0] in out and "a real run, drawn by seed" in out
    assert not CODES.search(page.inner_text("body"))
    ctx.close()
    ctx, page, _ = open_page(browser, built[2])
    assert page.query_selector("#real-run") is None
    assert SENTINELS[0] not in page.content()
    ctx.close()


def test_the_page_fits_the_screens_and_respects_the_themes(browser, built):
    for w, h in ((1920, 1080), (1440, 900), (1366, 768), (390, 844)):
        ctx, page, _ = open_page(browser, built[2], w, h)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"), (w, h)
        ctx.close()
    ctx, page, _ = open_page(browser, built[2])
    page.keyboard.press("t")
    assert page.get_attribute("html", "data-theme") in ("dark", "light")
    ctx.close()
