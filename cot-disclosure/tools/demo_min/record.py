"""Record the minimal demo page as clip_d.mp4 (about 18 s) and poster_d.png (step 1). Local output only.

  .venv/bin/python cot-disclosure/tools/demo_min/build.py     # first: writes the page
  .venv/bin/python cot-disclosure/tools/demo_min/record.py

Playwright, 1200x675 CSS px at device scale 1.6 (output 1920x1080, light theme); the steps are reached with the right-arrow key; each step's settled screenshot is held
5.9 s and joined by a 150 ms (5-frame) linear fade; H.264 yuv420p, 30 fps, crf 20, faststart, no audio (as compose.py).
Also runs the visible-text sweep (no codes, ids or paths) and the luma check; exits non-zero if either fails.
"""
import asyncio, pathlib, re, shutil, subprocess, sys, tempfile
from PIL import Image, ImageStat
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as B

VID = B.ROOT / "docs/presentation/final/video"
PAGE = VID / "demo_min/index.html"
FPS, HOLD, FADE = 30, int(5.9 * 30), 5


async def shots(tmp):
    texts, files = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await (await b.new_context(viewport={"width": 1200, "height": 675}, device_scale_factor=1.6, color_scheme="light")).new_page()
        await pg.goto(PAGE.as_uri())
        await pg.wait_for_timeout(400)
        for n in range(3):
            if n:
                await pg.keyboard.press("ArrowRight")
                await pg.wait_for_timeout(500)
            f = tmp / f"s{n + 1}.png"
            await pg.screenshot(path=str(f)); files.append(f)
            assert Image.open(f).size == (1920, 1080)
            texts.append(await pg.evaluate("document.querySelector('.step.on').innerText + '\\n' + document.querySelector('footer').innerText"))
            ov = await pg.evaluate("(() => { const s = document.querySelector('.step.on'), f = document.querySelector('footer').getBoundingClientRect();"
                                   " return [s.scrollHeight > s.clientHeight, [...s.children].some(c => c.getBoundingClientRect().bottom > f.top - 8), document.documentElement.scrollWidth > innerWidth]; })()")
            print(f"step {n + 1}: overflow={ov[0]} clashes_footer={ov[1]} h_scroll={ov[2]}")
            assert not any(ov)
        await b.close()
    return files, texts


def main():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="demo_min_"))
    files, texts = asyncio.run(shots(tmp))
    for n, t in enumerate(texts, 1):
        assert not B.find_codes(t), (n, B.find_codes(t))
    print("sweep: no codes, ids or paths in the visible text of any step")
    ims = [Image.open(f).convert("RGB") for f in files]
    fr = tmp / "fr"; fr.mkdir(); k = 0; lumas = []
    def put(im):
        nonlocal k
        k += 1; im.save(fr / f"{k:05d}.png"); lumas.append(ImageStat.Stat(im.convert("L")).mean[0])
    for i, im in enumerate(ims):
        for _ in range(HOLD): put(im)
        if i + 1 < len(ims):
            for j in range(1, FADE + 1): put(Image.blend(im, ims[i + 1], j / (FADE + 1)))
    mp4 = VID / "clip_d.mp4"
    subprocess.run(["/opt/homebrew/bin/ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(fr / "%05d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "slow", "-movflags", "+faststart", str(mp4)], check=True)
    ims[0].save(VID / "poster_d.png")
    print(f"frames {k} ({k / FPS:.2f} s); lowest mean luma of the frames {min(lumas):.1f}; wrote {mp4}, poster_d.png")
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
