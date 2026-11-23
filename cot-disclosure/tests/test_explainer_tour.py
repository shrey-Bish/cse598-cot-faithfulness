"""The Hint Explainer's tour: autoplay, pause, Esc order, the thread, collapsed stages, hint chips (Playwright; skips without it).
Presentation only: no number is checked here beyond what DATA already holds."""
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "tools"))

try:
    from playwright.sync_api import sync_playwright
except Exception:                                                        # noqa: BLE001
    sync_playwright = None

PAGE = CODE.parent / "archive" / "superseded" / "explainer_2026-11-14" / "explainer.html"  # docs/demo/ until Nov 23


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


def open_page(browser, hash_="", reduced=True):
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080},
                              reduced_motion="reduce" if reduced else "no-preference")
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(PAGE.resolve().as_uri() + hash_)
    page.wait_for_selector("body[data-ready='1']")
    return ctx, page, errors


def scene(page):
    return page.get_attribute("#tour", "data-scene")


def test_escape_closes_the_open_panel_first_then_leaves_the_tour(browser):
    ctx, page, errors = open_page(browser, "#tourms=60000")
    page.click("#play")
    page.keyboard.press("1")
    page.click(".stage[data-stage='4'] .stage-head")
    page.wait_for_selector("#expand.open")
    page.keyboard.press("Escape")
    assert page.evaluate("!document.querySelector('#expand').classList.contains('open')")
    assert page.get_attribute("body", "data-tour") == "1"                 # the tour stays
    page.keyboard.press("Escape")
    assert page.get_attribute("body", "data-tour") in (None, "0")         # the second Esc leaves it
    assert not errors, errors
    ctx.close()


def test_autoplay_advances_by_itself_and_space_pauses(browser):
    ctx, page, errors = open_page(browser, "#tourms=1200", reduced=False)
    page.click("#play")
    assert scene(page) == "1" and page.get_attribute("#tour", "data-playing") == "1"
    page.wait_for_function("document.querySelector('#tour').dataset.scene == '2'", timeout=6000)
    page.keyboard.press(" ")
    assert page.get_attribute("#tour", "data-playing") == "0"
    held = scene(page)
    page.wait_for_timeout(2500)                                           # paused: longer than a scene
    assert scene(page) == held
    page.keyboard.press(" ")
    assert page.get_attribute("#tour", "data-playing") == "1"
    page.wait_for_function("n => document.querySelector('#tour').dataset.scene != n", arg=held, timeout=6000)
    page.keyboard.press("ArrowRight")                                     # Step and the arrows still work
    page.keyboard.press("ArrowLeft")
    assert not errors, errors
    ctx.close()


def test_the_step_button_and_the_default_scene_time(browser):
    ctx, page, _ = open_page(browser)
    page.click("#play")
    assert scene(page) == "1"
    page.click("#tour-next")
    assert scene(page) == "2"
    page.wait_for_timeout(600)
    assert scene(page) == "2"                                             # the default is about 15 s a scene
    ctx.close()


def test_every_scene_draws_one_thread_with_no_empty_stage(browser):
    ctx, page, errors = open_page(browser)
    page.click("#play")
    for i in "1234567":
        page.keyboard.press(i)
        page.wait_for_timeout(150)
        if i != "7":                                                      # scene 7 opens the trade-off panel instead of a run
            assert page.query_selector("#thread .th") is not None, i      # the thread is drawn (reduced motion: at once)
        for st in page.query_selector_all(".stage:visible"):
            body = st.query_selector(".stage-body")
            assert st.get_attribute("class").count("collapsed") or body.inner_text().strip(), i
        assert page.evaluate("[...document.querySelectorAll('.stage')].every(s => getComputedStyle(s).opacity === '1')")
    assert not errors, errors
    ctx.close()


def test_a_model_without_thinking_collapses_the_reasoning_stage(browser):
    ctx, page, _ = open_page(browser)
    page.select_option("#model", label="Qwen3 30B Instruct")
    cls = page.get_attribute(".stage[data-stage='3']", "class")
    assert "collapsed" in cls and "without thinking" in page.inner_text("#b3")
    page.select_option("#model", label="Olmo 3 7B Think")
    assert "collapsed" not in page.get_attribute(".stage[data-stage='3']", "class")
    ctx.close()


def test_hint_chips_say_what_the_model_saw(browser):
    ctx, page, _ = open_page(browser)
    page.select_option("#model", label="Olmo 3 7B Think")
    texts = {}
    for src in ("user", "pasted", "call"):
        page.click(f"#sources [data-src='{src}']")
        chip = page.query_selector("#b1 .chip")
        texts[src] = (chip.inner_text(), chip.get_attribute("data-tip"))
    assert "I think the answer is (C) but I'm curious what you think." in texts["user"][0]
    assert "Tool: the answer key says (C)." in texts["pasted"][0]
    assert "[tool result: lookup_answer_key]" in texts["pasted"][1] and '"expected": "C"' in texts["pasted"][1]
    assert "lookup_answer_key → (C)" in texts["call"][0]
    assert "inserted tool turn" in texts["call"][1]                       # Olmo gets an inserted tool turn
    ctx.close()
