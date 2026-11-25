"""Capture the demo pad for the two clips (Playwright, 1920x1080 at device scale 2, light theme).

Needs the pad served:  cd cot-disclosure && ../.venv/bin/python -u tools/demo_template/serve.py --no-open --port 8797
Writes docs/presentation/final/video/raw/ (gitignored: the frames show recorded model text):
  <name>.png / <name>_NNN.jpg frames and manifest.json (frame times, element boxes in CSS px).
Usage: record.py [--url http://127.0.0.1:8797/demo.html#pad] [--out DIR]
"""
import argparse, asyncio, json, pathlib, time
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parents[3]
SELS = {"hint": ".padhint", "pad": ".padpad", "mark": ".padpad mark", "ans": ".padans", "chk": ".padchk",
        "find": ".padfind", "count": ".padcount", "verdict": ".padverdict", "host": ".padhost"}
BOXES_JS = """(sels) => { const o = {}; for (const [k, s] of Object.entries(sels)) {
  const all = [...document.querySelectorAll(s)].filter(e => e.getBoundingClientRect().width > 0);
  if (!all.length) continue;
  const rs = all.map(e => e.getBoundingClientRect());
  if (k === 'chk' || k === 'verdict') { const x0 = Math.min(...rs.map(r => r.left)), y0 = Math.min(...rs.map(r => r.top)),
     x1 = Math.max(...rs.map(r => r.right)), y1 = Math.max(...rs.map(r => r.bottom)); o[k] = [x0, y0, x1 - x0, y1 - y0]; }
  else { const r = rs[0]; o[k] = [r.left, r.top, r.width, r.height]; } } return o; }"""


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8797/demo.html#pad")
    ap.add_argument("--out", default=str(ROOT / "docs/presentation/final/video/raw"))
    a = ap.parse_args()
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    man = {}

    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=2, color_scheme="light")
        pg = await ctx.new_page()
        await pg.goto(a.url)
        await pg.wait_for_function("typeof PS!=='undefined' && PS.state==='ok'")
        await pg.evaluate("document.documentElement.dataset.theme='light'")

        async def boxes(): return await pg.evaluate(BOXES_JS, SELS)

        async def still(name):
            await pg.screenshot(path=str(out / f"{name}.png"))
            return {"img": f"{name}.png", "boxes": await boxes()}

        async def frames(name, seconds):
            """real-time capture; each frame stamped with seconds since this call began"""
            t0 = time.perf_counter(); fr = []; i = 0
            while time.perf_counter() - t0 < seconds:
                t = time.perf_counter() - t0
                f = f"{name}_{i:03d}.jpg"
                await pg.screenshot(path=str(out / f), type="jpeg", quality=93)
                fr.append([round(t, 3), f]); i += 1
            return fr

        async def pset(js):
            await pg.evaluate(f"PAD_API.set({js})")

        # ---- clip A
        await pset('{ds:"fresh120", src:"call", wd:"inserted_study_guide", w:"wrong", ver:"base", find:"cited"}')
        await pg.wait_for_timeout(250)
        man["A_q"] = await pg.evaluate("PS.q")
        man["A1"] = await still("A1")
        await pg.evaluate("pReplay()")
        man["A2_stream"] = await frames("A2s", 3.0)
        await pg.evaluate("pFinish()")
        man["A2_finish"] = await frames("A2f", 1.4)
        await pg.wait_for_timeout(600)
        man["A2"] = await still("A2")
        await pg.evaluate("pReplay()"); await pg.wait_for_timeout(150)
        await pg.evaluate("pFinish()")
        man["A4_pen"] = await frames("A4p", 1.3)
        await pg.wait_for_timeout(500)
        man["A4"] = await still("A4")
        man["A_find_text"] = await pg.evaluate("document.querySelector('.padfind').innerText")
        man["A_count_text"] = await pg.evaluate("document.querySelector('.padcount').innerText")
        # ---- clip B
        await pset('{ds:"fresh120", q:"mmlupro-11784", src:"call", wd:"inserted_study_guide", w:"wrong", ver:"a40"}')
        man["B1_stream"] = await frames("B1s", 1.5)
        await pg.evaluate("pFinish()")
        man["B1_finish"] = await frames("B1f", 1.6)
        await pg.wait_for_timeout(600)
        man["B1"] = await still("B1")
        await pset('{ds:"fresh120", ver:"a40", find:"cost"}')
        await pg.wait_for_timeout(400)
        await pg.evaluate("pFinish()")
        man["B2_finish"] = await frames("B2f", 1.8)
        await pg.wait_for_timeout(1200)
        man["B2"] = await still("B2")
        man["B2_q"] = await pg.evaluate("PS.q")
        man["B2_find_text"] = await pg.evaluate("document.querySelector('.padfind') && document.querySelector('.padfind').innerText")
        await pset('{ds:"review"}')
        await pg.wait_for_timeout(500)
        man["B3_pre"] = await still("B3pre")
        await pg.get_by_role("button", name="Send to the review team").first.click()
        man["B3_anim"] = await frames("B3a", 4.2)
        await pg.wait_for_timeout(800)
        man["B3"] = await still("B3")
        await b.close()
    (out / "manifest.json").write_text(json.dumps(man, indent=1))
    print("question", man["A_q"], "| find:", man["A_find_text"][:120].replace("\n", " "), "| count:", man["A_count_text"])
    print("B2 question", man["B2_q"], "| find:", (man["B2_find_text"] or "")[:120].replace("\n", " "))
    for k in ("A2", "A4", "B1", "B2", "B3"):
        print(k, sorted(man[k]["boxes"]))
    for k in ("A2_stream", "A2_finish", "A4_pen", "B1_stream", "B1_finish", "B2_finish", "B3_anim"):
        print(k, len(man[k]), "frames")

asyncio.run(main())
