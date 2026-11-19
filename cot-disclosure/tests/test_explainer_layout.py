"""The Hint Explainer's layout and wording rules (presentation only; no number changes):
c3 one legend line instead of per-card badges; c4 a count with fewer than 5 runs behind it is never shown as "k of n";
c6 one controls row at 1920x1080, sentence case, stage text at least 16px, the final-answer footer matches the run;
c9 one chart per article section. Playwright; skips cleanly when it or Chromium is missing. No network."""
import json
import re
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "tools"))
sys.path.insert(0, str(CODE / "progress"))

import build_demo as bd  # noqa: E402

SUM = CODE / "results" / "summaries"
MIN_RUNS = 5                                                             # FINDINGS: fewer than 5 behind a number: none reported
KN = re.compile(r"\b(\d+) of (\d+)\b")
FEW = "too few runs to say"

try:
    from playwright.sync_api import sync_playwright
except Exception:                                                        # noqa: BLE001
    sync_playwright = None


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    d = tmp_path_factory.mktemp("layout")
    out = d / "docs" / "index.html"
    bd.build(summaries=SUM, findings=bd.FINDINGS, out=out, examples=d / "none.json", local_out=d / "l.html")
    return out


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


def open_page(browser, path, w=1920, h=1080):
    ctx = browser.new_context(viewport={"width": w, "height": h}, reduced_motion="reduce")
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(Path(path).resolve().as_uri())
    page.wait_for_selector("body[data-ready='1']")
    return ctx, page, errs


def everything(page):
    """All the text a reader can get: the page's text and every hover text on it."""
    tips = page.evaluate("Array.from(document.querySelectorAll('[data-tip]')).map(e => e.getAttribute('data-tip'))")
    return page.inner_text("body") + "\n" + "\n".join(tips)


def few(text):
    return [m.group(0) for m in KN.finditer(text) if int(m.group(2)) < MIN_RUNS]


def sources(page):
    return page.eval_on_selector_all("#sources button", "bs => bs.map(b => [b.dataset.src, b.getAttribute('aria-disabled')])")


def settings(page):
    return page.eval_on_selector_all("#setting button", "bs => bs.map(b => b.dataset.v)")


def panels(page, texts):
    for stage in (1, 2, 3, 4):
        page.click(f".stage[data-stage='{stage}'] .stage-head")
        page.wait_for_selector("#expand.open")
        texts.append(everything(page))
        page.keyboard.press("Escape")
    page.click("#to-tradeoff") if page.is_visible("#to-tradeoff") else None
    texts.append(everything(page))
    page.keyboard.press("Escape")


# ---------------------------------------------------------------- c4
def test_no_count_with_fewer_than_five_runs_is_shown_as_k_of_n(browser, built):
    ctx, page, errs = open_page(browser, built)
    texts, seen_few = [], False
    n_models = page.eval_on_selector_all("#model option", "o => o.length")
    for mi in range(n_models):
        page.select_option("#model", index=mi)
        for sv in (settings(page) or [None]):
            if sv is not None:
                page.click(f"#setting button[data-v='{sv}']")
            for src, off in sources(page):
                if off:
                    continue
                page.click(f"#sources button[data-src='{src}']")
                page.click("#run")
                texts.append(everything(page))
                page.click("#run20")
                texts.append(everything(page))
        panels(page, texts)
    # the Olmo fresh questions with every fix, with the review team on
    page.select_option("#model", label="Olmo 3 7B Think")
    page.click(".sw") if not page.is_checked("#review") else None
    for fx in page.eval_on_selector_all("#fix option", "o => o.map(x => x.value)"):
        page.select_option("#fix", value=fx)
        for src, off in sources(page):
            if off:
                continue
            page.click(f"#sources button[data-src='{src}']")
            page.click("#run")
            texts.append(everything(page))
    panels(page, texts)
    for t in texts:
        bad = few(t)
        assert not bad, bad
        seen_few = seen_few or FEW in t
    assert seen_few, "the few-runs words never appeared: the test is not reaching the small counts"
    assert not errs, errs
    ctx.close()


def test_the_known_small_counts_read_too_few_runs_to_say(browser, built):
    data = json.loads(re.search(r'id="demo-data">(.*?)</script>', built.read_text(), re.S).group(1))
    rows = data["x"]["settings"]
    small = [(i, r) for i, r in enumerate(rows) if r["sources"]["user"].get("names") and r["sources"]["user"]["names"]["n"] < MIN_RUNS]
    assert small, "no setting has a small count any more: update the test"
    ctx, page, _ = open_page(browser, built)
    for i, r in small:
        page.select_option("#model", label=r["model"])
        sets = settings(page)
        if len(sets) > 1 and not (r["model"].startswith("Olmo")):
            page.click(f"#setting button[data-v='{i}']")
        page.click("#sources button[data-src='user']")
        txt = page.inner_text("#b4")
        assert FEW in txt, (r["model"], r["setting"])
        assert not few(txt)
    ctx.close()


def test_a_chart_mark_with_few_runs_is_replaced_by_the_words(browser, built, tmp_path):
    """Today no charted count is small, so this makes three of them small in a copy of the page (a test double, not
    a result): the checker's catches, a reviewer's cell and a model's follow rate."""
    html = built.read_text()
    m = re.search(r'(id="demo-data">)(.*?)(</script>)', html, re.S)
    data = json.loads(m.group(2))
    data["s4"]["checker"]["caught"].update(n=3, k=2)
    data["s4"]["reviewers"][0]["answer_only"].update(n=2, k=1)
    data["x"]["settings"][0]["sources"]["user"]["f"].update(n=4, k=1)
    small = tmp_path / "small.html"
    small.write_text(html[:m.start(2)] + bd.script_json(data) + html[m.end(2):])
    ctx, page, errs = open_page(browser, small)
    art = page.inner_text("#article")
    assert FEW in art and not few(art), few(art)
    # the checker chart's row holds the words and no bar, no interval, no mark
    rows = page.evaluate("""Array.from(document.querySelectorAll('#a-checker .chart g')).map(g => [g.textContent, g.querySelectorAll('rect').length, g.querySelectorAll('line').length])""")
    assert any(FEW in t and rect == 0 and ln == 0 for t, rect, ln in rows), rows
    page.click(".stage[data-stage='1'] .stage-head")
    page.wait_for_selector("#expand.open")
    assert FEW in page.inner_text("#expand-body") and not few(everything(page))
    page.keyboard.press("Escape")
    page.select_option("#model", index=0)
    page.click("#sources button[data-src='user']")
    assert FEW in page.inner_text("#b4") and FEW in page.inner_text("#b1")   # the bar and the stage-1 line
    assert page.locator("#b4 .ob.hint .fill").inner_text().strip() == ""
    assert not few(everything(page))
    assert not errs, errs
    ctx.close()


# ---------------------------------------------------------------- c3
def test_one_legend_line_and_no_badges_in_the_cards(browser, built):
    ctx, page, _ = open_page(browser, built)
    page.select_option("#model", label="Olmo 3 7B Think")
    page.click("#run")
    assert page.locator("#stages .tag").count() == 0
    assert page.locator("#stages .ill").count() == 0
    leg = page.inner_text("#legend").lower()
    for w in ("solid", "measured", "dashed", "drawn to explain", "italic", "illustrative"):
        assert w in leg, w
    assert page.is_visible("#simnote") and "Simulated at our measured rates" in page.inner_text("#simnote")
    box = page.eval_on_selector("#legend", "e => e.getBoundingClientRect().height")
    assert box < 60, box                                                 # one line at 1920 wide
    ctx.close()


# ---------------------------------------------------------------- c6
def test_controls_are_one_row_at_1920_and_sentence_case(browser, built):
    ctx, page, _ = open_page(browser, built)
    for label in ("Qwen3 30B Instruct", "Olmo 3 7B Think"):
        page.select_option("#model", label=label)
        ys = page.evaluate("""['#model', '#setting', '#sources', '#fix', '#review', '#run', '#run20'].map(s => {
            const r = document.querySelector(s).getBoundingClientRect(); return r.top + r.height / 2; })""")
        assert max(ys) - min(ys) < 24, (label, ys)
        assert page.evaluate("document.querySelector('.controls').getBoundingClientRect().height") < 120
    upper = page.evaluate("""Array.from(document.querySelectorAll('body *')).filter(e => getComputedStyle(e).textTransform === 'uppercase').map(e => e.className || e.tagName)""")
    assert not upper, upper
    page.click("#to-tradeoff")
    assert not page.evaluate("""Array.from(document.querySelectorAll('body *')).filter(e => getComputedStyle(e).textTransform === 'uppercase').length""")
    shout = [w for w in re.findall(r"\b[A-Z]{4,}(?: [A-Z()]{3,})+\b", page.inner_text("body"))]
    assert not shout, shout
    ctx.close()


def test_stage_text_is_at_least_16px_at_1920(browser, built):
    ctx, page, _ = open_page(browser, built)
    page.select_option("#model", label="Olmo 3 7B Think")
    page.click("#run")
    small = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('#stages .stage-body *, #stages .stage-head .title').forEach(e => {
          if (e.closest('.idtag')) return;
          const own = Array.from(e.childNodes).filter(n => n.nodeType === 3 && n.nodeValue.trim()).length;
          if (!own) return;
          let fs = parseFloat(getComputedStyle(e).fontSize);
          const svg = e.ownerSVGElement;
          if (svg) { const vb = svg.viewBox.baseVal; fs *= svg.getBoundingClientRect().width / vb.width; }
          if (fs < 15.95 && !e.classList.contains('td')) out.push([e.className.baseVal === undefined ? e.className : 'svg', e.textContent.trim().slice(0, 30), Math.round(fs * 10) / 10]);
        });
        return out; }""")
    assert not small, small
    ctx.close()


def test_the_footer_the_letter_and_the_tally_describe_the_same_run(browser, built):
    ctx, page, _ = open_page(browser, built)
    page.select_option("#model", label="Olmo 3 7B Think")
    page.click("#run20")
    assert page.locator("#tally .td").count() == 20
    assert page.inner_text("#verdict").startswith("The last of the runs")
    followed = "followed the hint" in page.inner_text("#verdict") and "did not" not in page.inner_text("#verdict")
    assert (page.inner_text("#letter") == "C") == followed
    assert "20" in page.inner_text("#tallyline")
    # the thread and the stage text describe that same last run
    assert page.locator("#priv-text").inner_text().strip() != "Press Run: illustrative reasoning streams in here."
    # a changed control clears the old run everywhere
    page.select_option("#fix", value="prompt_only")
    assert page.inner_text("#letter") == "?"
    assert page.locator("#tally .td").count() == 0
    assert "of 20" not in page.inner_text("#tallyline")
    assert page.inner_text("#verdict").startswith("Press Run")
    page.click("#run")
    assert page.locator("#tally .td").count() == 1
    assert "1 of 1" not in page.inner_text("#tallyline")                 # a single run is not a rate
    followed = "Followed" in page.inner_text("#verdict")
    assert (page.inner_text("#letter") == "C") == followed
    # the source and the setting clear it too
    page.click("#sources button[data-src='pasted']")
    assert page.inner_text("#letter") == "?" and page.locator("#tally .td").count() == 0
    page.click("#run")
    page.click(".sw")
    assert page.inner_text("#letter") == "?" and page.locator("#tally .td").count() == 0
    ctx.close()


# ---------------------------------------------------------------- c9
def test_each_article_section_has_exactly_one_chart(browser, built):
    ctx, page, _ = open_page(browser, built)
    rows = page.evaluate("""Array.from(document.querySelectorAll('#article section.art')).map(s => ({
        id: s.id, charts: s.querySelectorAll('.chart').length,
        figures: Array.from(s.querySelectorAll('.chart')).map(c => c.querySelectorAll(':scope > svg').length),
        inputs: s.querySelectorAll('input').length }))""")
    for r in rows:
        assert r["charts"] <= 1, r
        assert all(f == 1 for f in r["figures"]), r                       # one figure, not a pair stacked
        assert r["inputs"] == 0, r
    assert sum(r["charts"] for r in rows) >= 10
    ctx.close()
