"""Screenshots of the demo at 1920 x 1080 (development and review; Playwright in the repo's .venv).

  .venv/bin/python cot-disclosure/tools/demo_template/shots.py PAGE OUTDIR part:index[:theme][:js] ...

part is map, bench or found; index the page within the part; theme light (default) or dark; js an optional snippet
run after the page is shown (e.g. a bench action), then the screenshot waits for the choreography (4.5 s; 0 with
INSTANT). Fonts are awaited. Console errors are printed and make the exit code 1.
"""
import hashlib
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright


def main(argv):
    page_path, out, specs = Path(argv[0]).resolve(), Path(argv[1]), argv[2:]
    out.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for spec in specs:
            part, idx, *rest = spec.split(":", 3)
            theme = rest[0] if rest and rest[0] in ("light", "dark") else "light"
            js = rest[1] if len(rest) > 1 else (rest[0] if rest and rest[0] not in ("light", "dark") else "")
            vw, vh = (int(x) for x in os.environ.get("DEMO_VIEWPORT", "1920x1080").split("x"))
            ctx = b.new_context(viewport={"width": vw, "height": vh}, color_scheme=theme)
            pg = ctx.new_page()
            pg.on("console", lambda m, s=spec: m.type == "error" and errors.append(f"{s}: {m.text}"))
            pg.on("pageerror", lambda e, s=spec: errors.append(f"{s}: {e}"))
            pg.goto(page_path.as_uri() + "#" + part)
            pg.evaluate("document.fonts.ready")
            pg.evaluate(f"go('{part}', {int(idx)})")
            if js:
                pg.evaluate(js)
            pg.wait_for_timeout(4500)
            name = f"{part}_{int(idx):02d}_{theme}" + ("_" + hashlib.sha1(js.encode()).hexdigest()[:6] if js else "") + ".png"
            pg.screenshot(path=str(out / name))
            print(out / name)
            ctx.close()
        b.close()
    for e in errors:
        print("ERROR", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
