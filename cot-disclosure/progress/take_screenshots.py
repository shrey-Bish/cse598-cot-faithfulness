"""Screenshot the evidence viewer cards and frame each figure at 16:9.

  python cot-disclosure/progress/take_screenshots.py                     # headless
  python cot-disclosure/progress/take_screenshots.py --headed --slow-mo 300   # watch the browser

Writes presentation/progress/screenshots/NN_<card-id>.png, full_page.png, and
fig_<name>.png. Needs: pip install playwright && python -m playwright install chromium
"""
import argparse
import base64
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

PRES = Path(__file__).resolve().parents[2] / "presentation" / "progress"
VIEWER = PRES / "evidence_viewer.html"
SHOTS = PRES / "screenshots"
FIGS = PRES / "figures"

FRAME = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;background:#fff}
.frame{width:1600px;height:900px;display:flex;align-items:center;justify-content:center;background:#fff}
img{max-width:1520px;max-height:855px}
</style></head><body><div class="frame"><img src="data:image/png;base64,%s"></div></body></html>"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--headed", action="store_true", help="show the browser window")
    p.add_argument("--slow-mo", type=int, default=0, metavar="MS", help="slow every browser action by MS")
    p.add_argument("--out", default=str(SHOTS), help="output folder")
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed, slow_mo=args.slow_mo)
        page = browser.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=2)
        page.goto(VIEWER.resolve().as_uri())
        page.wait_for_load_state("load")
        cards = page.locator(".card")
        for i in range(cards.count()):
            el = cards.nth(i)
            cid = el.get_attribute("id")
            el.scroll_into_view_if_needed()
            el.screenshot(path=str(out / f"{i + 1:02d}_{cid}.png"))
            print(f"saved {i + 1:02d}_{cid}.png")
        page.screenshot(path=str(out / "full_page.png"), full_page=True)
        print("saved full_page.png")
        with tempfile.TemporaryDirectory() as tmp:
            for fig in sorted(FIGS.glob("*.png")):
                wrapper = Path(tmp) / f"{fig.stem}.html"
                wrapper.write_text(FRAME % base64.b64encode(fig.read_bytes()).decode())
                page.goto(wrapper.as_uri())
                page.wait_for_load_state("load")
                page.locator(".frame").screenshot(path=str(out / f"fig_{fig.stem}.png"))
                print(f"saved fig_{fig.stem}.png")
        browser.close()


if __name__ == "__main__":
    main()
