"""Screenshot the playground's six examples (saved runs only, no live calls) and every
walkthrough scene (after its animation), at 1920x1080 and 1280x720.

  python cot-disclosure/ui/app.py &          # the demo must be running
  python cot-disclosure/ui/screenshots.py    # -> presentation/progress/ui_screenshots/
"""
import json
import urllib.request
import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[2] / "presentation" / "progress" / "ui_screenshots"
NAMES = ["1_question_and_hint", "2_fell_for_it", "3_kept_right_answer", "4_numbers", "5_live"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8765")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        examples = json.load(urllib.request.urlopen(a.url + "/api/examples"))["examples"]
        for w, h in ((1920, 1080), (1280, 720)):
            suffix = "" if w == 1920 else "_1280x720"
            page = browser.new_page(viewport={"width": w, "height": h})
            page.goto(a.url)
            page.wait_for_selector("#col-with .rchip")
            for i, ex in enumerate(examples, 1):
                page.select_option("#example", ex["id"])
                page.wait_for_timeout(1200)          # saved runs and the featured reply load
                page.screenshot(path=str(out / f"playground_{i}_{ex['id']}{suffix}.png"))
                overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
                print(f"{w}x{h} playground {ex['id']}: saved{' (HORIZONTAL OVERFLOW)' if overflow else ''}")
            page.close()
            page = browser.new_page(viewport={"width": w, "height": h})
            page.goto(a.url + "/walkthrough.html")
            page.wait_for_selector(".scene.active")
            for i, name in enumerate(NAMES):
                page.wait_for_timeout(6500)          # let the scene's animation finish
                page.screenshot(path=str(out / f"{name}{suffix}.png"))
                overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
                print(f"{w}x{h} {name}: saved{' (HORIZONTAL OVERFLOW)' if overflow else ''}")
                page.keyboard.press("ArrowRight")
            page.close()
        browser.close()


if __name__ == "__main__":
    main()
