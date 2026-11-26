"""Storyboard stills for clip C (Phase A: stills and a manifest only; Playwright, 1920x1080, light theme).

Needs the pad served:  cd cot-disclosure && ../.venv/bin/python -u tools/demo_template/serve.py --no-open --port 8797
Writes docs/presentation/final/storyboard/video_beats/clipC/ (gitignored: the stills show recorded model text):
  C*.png, contact.png, manifest.json (question ids, counts, boxes in CSS px; no model text).
Usage: record_c.py [--base http://127.0.0.1:8797/demo.html] [--out DIR] [--scale 2]
This file holds no model text: the question is chosen by the page's own finder (Show me, "the fix held",
Consistency-trained selected, first match in the page's seeded order); the hand-labelled run by a fixed rule (see RULE_C3).
"""
import argparse, asyncio, json, pathlib, re, sys
from playwright.async_api import async_playwright

sys.path.insert(0, str(pathlib.Path(__file__).parent))
ROOT = pathlib.Path(__file__).resolve().parents[3]
SRC = (ROOT / "cot-disclosure/tools/demo_video/record.py").read_text()
SENT_JS = re.search(r'SENT_JS = """(.*?)"""', SRC, re.S).group(1).replace("\\\\", "\\")
SELS = {"hint": ".padhint", "pad": ".padpad", "mark": ".padpad mark", "ans": ".padans", "chk": ".padchk",
        "find": ".padfind", "count": ".padcount", "verdict": ".padverdict", "host": ".padhost"}
BOXES_JS = re.search(r'BOXES_JS = """(.*?)"""', SRC, re.S).group(1)
RULE_C3 = ("Bench test 4 (The fixes), Fine-tuned selected, key L: the first hand-labelled run in the page's own order "
           "(L6's key-file row order); advance with L only if its label is not 'says_changed' or 'mentions_only'.")
# the first sentence of the hand-labelled answer that mentions the tool or the hint (a heuristic, checked by eye)
NAME_JS = """() => { const el = document.querySelector('.bover .bobody'); if (!el) return null;
  const node = el.firstChild; if (!node || node.nodeType !== 3) return null; const t = node.nodeValue;
  const cut = t.indexOf('\\n\\n\\u2014 Hand label'); const body = cut > 0 ? t.slice(0, cut) : t;
  const re = /[^.?!\\n]*(tool|study guide|lookup|hint|reply|suggest)[^.?!\\n]*[.?!]?/i; const m = re.exec(body); if (!m) return null;
  const r = document.createRange(); r.setStart(node, m.index); r.setEnd(node, m.index + m[0].length);
  return {lines: [...r.getClientRects()].filter(q => q.width > 2).map(q => [q.left, q.top, q.width, q.height]), chars: m[0].length}; }"""
BOX_OF = """(s) => { const e = [...document.querySelectorAll(s)].filter(e => e.getBoundingClientRect().width > 0)[0];
  if (!e) return null; const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }"""


SCROLL_JS = """async (to) => { const els = [document.querySelector('.bover .bobody'), document.querySelector('.bover')];
  const el = els.find(e => e && e.scrollHeight > e.clientHeight + 4); if (!el) return {scrolled: false};
  el.scrollTo({top: to ? el.scrollHeight : 0, behavior: 'smooth'});
  await new Promise(r => setTimeout(r, 1700)); return {scrolled: true, top: el.scrollTop, max: el.scrollHeight - el.clientHeight}; }"""
LABEL_JS = """() => { const el = document.querySelector('.bover .bobody'); const node = el && el.firstChild; if (!node) return null;
  const i = node.nodeValue.indexOf('\\u2014 Hand label'); if (i < 0) return null;
  const r = document.createRange(); r.setStart(node, i); r.setEnd(node, node.nodeValue.length);
  return [...r.getClientRects()].filter(q => q.width > 2).map(q => [q.left, q.top, q.width, q.height]); }"""
PANELS_JS = """() => [...document.querySelectorAll('.panel')].filter(e => e.getBoundingClientRect().width > 0).map(e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height, e.innerText]; })"""


async def frames_main(a):
    import time
    out = ROOT / "docs/presentation/final/video/raw_c"; out.mkdir(parents=True, exist_ok=True)
    man = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=2, color_scheme="light")
        pg = await ctx.new_page()

        async def fresh(url):
            await pg.goto(url); await pg.wait_for_timeout(2500)
            await pg.evaluate("document.documentElement.dataset.theme='light'")

        async def still(name):
            await pg.screenshot(path=str(out / f"{name}.png")); return f"{name}.png"

        async def frames(name, seconds):
            t0 = time.perf_counter(); fr = []; i = 0
            while time.perf_counter() - t0 < seconds:
                t = time.perf_counter() - t0; f = f"{name}_{i:03d}.jpg"
                await pg.screenshot(path=str(out / f), type="jpeg", quality=93); fr.append([round(t, 3), f]); i += 1
            return fr

        async def pset(js): await pg.evaluate(f"PAD_API.set({js})")

        await fresh(a.base + "#pad")
        await pg.wait_for_function("typeof PS!=='undefined' && PS.state==='ok'")
        # the finder's pick (same call as the stills): its question, text and order
        await pset('{ds:"fresh120", src:"call", wd:"inserted_study_guide", w:"wrong", ver:"a40", find:"fixed"}')
        await pg.wait_for_timeout(500)
        q = await pg.evaluate("PS.q"); man["question"] = q; man["find_text_c2"] = (await pg.evaluate("document.querySelector('.padfind').innerText")).split("\n")[0]
        man["first_in_order"] = await pg.evaluate("(PAD_API.matches('fixed').order || [])[0] && (PAD_API.matches('fixed').order[0].id || PAD_API.matches('fixed').order[0].q || PAD_API.matches('fixed').order[0])")
        # ---- C1: No fix alone
        await pset('{ds:"fresh120", q:"%s", src:"call", wd:"inserted_study_guide", w:"wrong", ver:"base"}' % q)
        await pg.wait_for_timeout(300)
        await pg.evaluate("pFindOff(); pRender()"); await pg.wait_for_timeout(200)
        man["C1_hint_box"] = await pg.evaluate(BOX_OF, ".padhint")
        await pg.evaluate("pReplay()")
        man["C1_stream"] = await frames("C1s", 2.2)
        await pg.evaluate("pFinish()")
        man["C1_finish"] = await frames("C1f", 3.0)
        await pg.wait_for_timeout(1200)
        man["C1_still"] = await still("C1")
        man["C1_sentence"] = await pg.evaluate(SENT_JS)
        man["C1_boxes"] = await pg.evaluate(BOXES_JS, SELS)
        # ---- C2: split with Show me set to "the fix held"
        await pset('{ds:"fresh120", src:"call", wd:"inserted_study_guide", w:"wrong", ver:"a40", find:"fixed"}')
        man["C2_stream"] = await frames("C2s", 1.2)
        await pg.evaluate("pFinish()")
        man["C2_finish"] = await frames("C2f", 2.4)
        await pg.wait_for_timeout(1000)
        man["C2_still"] = await still("C2")
        man["C2_boxes"] = await pg.evaluate(BOXES_JS, SELS)
        man["C2_find_text_shown"] = (await pg.evaluate("document.querySelector('.padfind').innerText")).split("\n")[0]
        man["C2_q_shown"] = await pg.evaluate("PS.q")
        # ---- C3: bench test 4, Fine-tuned, key L
        await fresh(a.base)
        await pg.keyboard.press("3"); await pg.wait_for_timeout(700)
        await pg.keyboard.press("Shift+4"); await pg.wait_for_timeout(900)
        await pg.keyboard.press("l"); await pg.wait_for_timeout(1000)
        man["C3_title"] = await pg.evaluate("(document.querySelector('.bover .bohead b')||{}).innerText")
        man["C3_still_top"] = await still("C3top")
        man["C3_name_lines"] = (await pg.evaluate(NAME_JS) or {}).get("lines")
        man["C3_overlay_box"] = await pg.evaluate(BOX_OF, ".bover")
        sc = asyncio.create_task(pg.evaluate(SCROLL_JS, True))
        man["C3_scroll"] = await frames("C3s", 1.8)
        man["C3_scroll_info"] = await sc
        await pg.wait_for_timeout(300)
        man["C3_still_end"] = await still("C3end")
        man["C3_label_lines"] = await pg.evaluate(LABEL_JS)
        await pg.keyboard.press("Escape")
        # ---- C4: the map
        await fresh(a.base)
        await pg.keyboard.press("2"); await pg.wait_for_timeout(1200)
        await pg.locator(".mstep", has_text="The layers").first.click(); await pg.wait_for_timeout(2500)
        man["C4a_pre"] = await still("C4apre")
        await pg.locator(".crow .opt", has_text="The three together").first.click()
        man["C4a_anim"] = await frames("C4aa", 3.2)
        await pg.wait_for_timeout(600)
        man["C4a_still"] = await still("C4a")
        pan = await pg.evaluate(PANELS_JS); man["C4a_panel"] = [x[:4] for x in pan if "together" in x[4]]
        man["C4a_together_text"] = next((x[4].replace("\n", " ") for x in pan if "together" in x[4]), None)
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(800)
        await pg.locator(".mstep", has_text="Changes").first.click()
        man["C4b_anim"] = await frames("C4ba", 2.4)
        await pg.wait_for_timeout(600)
        man["C4b_still"] = await still("C4b")
        pan = await pg.evaluate(PANELS_JS); man["C4b_note"] = [x[:4] for x in pan if "What we read" in x[4]]
        await pg.locator(".crow .opt", has_text="Consistency-trained").first.click()
        man["C4c_anim"] = await frames("C4ca", 2.4)
        await pg.wait_for_timeout(600)
        man["C4c_still"] = await still("C4c")
        pan = await pg.evaluate(PANELS_JS); man["C4c_note"] = [x[:4] for x in pan if "What we read" in x[4]]
        await b.close()
    (out / "manifest.json").write_text(json.dumps(man, indent=1))
    print({k: (v if not isinstance(v, list) or len(v) < 6 else f"[{len(v)} items]") for k, v in man.items() if k not in ("C1_boxes", "C2_boxes", "C1_sentence")})


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8797/demo.html")
    ap.add_argument("--out", default=str(ROOT / "docs/presentation/final/storyboard/video_beats/clipC"))
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--frames", action="store_true", help="capture clip C's raw frames (video/raw_c/) instead of the storyboard stills")
    a = ap.parse_args()
    if a.frames:
        await frames_main(a); return
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    man = {"stills": [], "rule_C3": RULE_C3}

    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=a.scale, color_scheme="light")
        pg = await ctx.new_page()
        await pg.goto(a.base + "#pad")
        await pg.wait_for_function("typeof PS!=='undefined' && PS.state==='ok'")
        await pg.evaluate("document.documentElement.dataset.theme='light'")

        async def still(name, beat, target, box, caption, extra=None):
            await pg.screenshot(path=str(out / f"{name}.png"))
            e = {"id": name, "file": str((out / f"{name}.png").relative_to(ROOT)), "beat": beat, "target": target,
                 "box_css_px": box, "caption": caption}
            if extra: e.update(extra)
            man["stills"].append(e)

        async def pset(js): await pg.evaluate(f"PAD_API.set({js})")
        async def boxes(): return await pg.evaluate(BOXES_JS, SELS)

        # ---- C1/C2: the finder's pick
        await pset('{ds:"fresh120", src:"call", wd:"inserted_study_guide", w:"wrong", ver:"a40", find:"fixed"}')
        await pg.wait_for_timeout(500)
        man["C_question"] = await pg.evaluate("PS.q")
        man["C_find_text"] = await pg.evaluate("document.querySelector('.padfind').innerText")
        man["C_pattern_key"] = await pg.evaluate("PS.find")
        man["C_match_index"] = await pg.evaluate("PS.fi")
        # the first match in the seeded order, and whether the 11784 question is it
        man["C_first_matches"] = await pg.evaluate("(PAD_API.matches(PS.find).order || []).slice(0, 3).map(m => typeof m === 'string' ? m : (m.id || m.q || JSON.stringify(Object.keys(m))))")
        # C1: No fix alone, same question
        await pset('{ds:"fresh120", q:"%s", src:"call", wd:"inserted_study_guide", w:"wrong", ver:"base"}' % man["C_question"])
        await pg.wait_for_timeout(300)
        await pg.evaluate("pFindOff(); pRender()"); await pg.wait_for_timeout(200)   # base has no "fix held" pattern: drop the finder's empty panel
        await pg.evaluate("pReplay()"); await pg.wait_for_timeout(1300)
        await still("C1a_hint_lands", "C1", "the hint slip (.padhint)", await pg.evaluate(BOX_OF, ".padhint"),
                    "Tool call's wrong reply lands.", {"all_boxes": await boxes()})
        await pg.evaluate("pFinish()"); await pg.wait_for_timeout(1800)
        sent = await pg.evaluate(SENT_JS)
        bx = await boxes()
        man["C_marks_in_no_fix_reasoning"] = await pg.evaluate("document.querySelectorAll('.padpad mark').length")
        await still("C1b_reasoning_sentence", "C1", "the sentence holding the first highlighted mark (lines) in the reasoning pad (.padpad)",
                    bx.get("pad"), "No fix: its reasoning cites the tool.", {"sentence_lines_css_px": sent and sent["lines"], "sentence_chars": sent and sent["chars"], "all_boxes": bx})
        await still("C1c_final_answer", "C1", "the final answer box (.padans) with its three check lines (.padchk)",
                    bx.get("ans"), "No fix: the answer is the wrong letter, and doesn't say so.", {"checks_box": bx.get("chk"), "all_boxes": bx})
        # C2: split with Consistency-trained
        await pset('{ds:"fresh120", q:"%s", src:"call", wd:"inserted_study_guide", w:"wrong", ver:"a40"}' % man["C_question"])
        await pg.wait_for_timeout(800); await pg.evaluate("pFinish()"); await pg.wait_for_timeout(3000)
        bx = await boxes()
        man["C2_verdict_text_length"] = await pg.evaluate("(document.querySelector('.padverdict')||{innerText:''}).innerText.length")
        await still("C2_split_verdict", "C2", "the red verdict line across the split (.padverdict) and the two panes (.padpad)", bx.get("verdict"),
                    "Same question, same hint: the fix held (%s)." % man["C_find_text"].split("\n")[0].split(" on ")[-1].rstrip(".").replace(" questions"," questions"),
                    {"all_boxes": bx, "count_box": bx.get("count"), "find_box": bx.get("find")})

        # ---- C3: the hand-labelled Fine-tuned run (bench test 4, key L)
        await pg.goto(a.base); await pg.wait_for_timeout(2500)
        await pg.evaluate("document.documentElement.dataset.theme='light'")
        await pg.keyboard.press("3"); await pg.wait_for_timeout(700)
        await pg.keyboard.press("Shift+4"); await pg.wait_for_timeout(900)
        for i in range(8):
            await pg.keyboard.press("l"); await pg.wait_for_timeout(700)
            head = await pg.evaluate("(document.querySelector('.bover .bohead b')||{}).innerText||''")
            lab = await pg.evaluate("(document.querySelector('.bover .bobody')||{innerText:''}).innerText.split('Hand label: ')[1]?.split('.')[0]||''")
            man.setdefault("C3_tried", []).append({"title": head, "label": lab})
            if lab in ("says_changed", "mentions_only"): break
        man["C3_label"] = lab
        man["C3_info"] = await pg.evaluate("(document.querySelector('.bover .bobody')||{innerText:''}).innerText.split('— Hand label: ')[1]||''")
        nm = await pg.evaluate(NAME_JS)
        ob = await pg.evaluate(BOX_OF, ".bover")
        await still("C3_lora_hand_label", "C3", "the hand-labelled final answer overlay (.bover); the sentence naming the hint (lines); the hand-label line at its foot",
                    ob, "Fine-tuned: when it still follows, its answer says so (37 of 42 vs 18 of 42).",
                    {"naming_sentence_lines_css_px": nm and nm["lines"], "overlay_title": man["C3_tried"][-1]["title"], "bobody_box": await pg.evaluate(BOX_OF, ".bover .bobody")})
        await pg.keyboard.press("Escape")

        # ---- C4: the map
        await pg.goto(a.base); await pg.wait_for_timeout(2500)
        await pg.evaluate("document.documentElement.dataset.theme='light'")
        await pg.keyboard.press("2"); await pg.wait_for_timeout(1200)
        await pg.locator(".mstep", has_text="The layers").first.click(); await pg.wait_for_timeout(2500)
        await pg.locator(".crow .opt", has_text="The three together").first.click(); await pg.wait_for_timeout(3500)
        panels = await pg.evaluate("[...document.querySelectorAll('.panel')].filter(e=>e.getBoundingClientRect().width>0).map(e=>{const r=e.getBoundingClientRect();return [r.left,r.top,r.width,r.height,e.innerText]})")
        side = [x for x in panels if "together" in x[4]]
        man["C4a_together_text"] = side[0][4].replace("\n", " ") if side else None
        man["C4a_total_numbers"] = re.findall(r"\d+%[^\]]*\]?", man["C4a_together_text"] or "")[:1]
        await still("C4a_layers_together", "C4", "the layer column with layers 15, 19, 23 lit (left of centre) and the 'together' side panel (right)",
                    side[0][:4] if side else None, "Three layers carry it: together 90% (page text: see manifest).",
                    {"panels_css_px": [x[:4] for x in panels], "readout_row_box": await pg.evaluate(BOX_OF, ".crow")})
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(800)
        await pg.locator(".mstep", has_text="Changes").first.click(); await pg.wait_for_timeout(3500)
        for k, nm_, fn in (("lora", "Fine-tuned (LoRA)", "C4b_training_lora"), ("a40", "Consistency-trained", "C4c_training_consistency")):
            if k == "a40":
                await pg.locator(".crow .opt", has_text="Consistency-trained").first.click(); await pg.wait_for_timeout(3500)
            panels = await pg.evaluate("[...document.querySelectorAll('.panel')].filter(e=>e.getBoundingClientRect().width>0).map(e=>{const r=e.getBoundingClientRect();return [r.left,r.top,r.width,r.height,e.innerText]})")
            note = [x for x in panels if "What we read" in x[4]]
            man[fn + "_note_first_line"] = note[0][4].split("\n")[1] if note else None
            await still(fn, "C4", "the layer column with its three brackets (before, readout, after), the five bars with their values, and the 'What we read' note (left)",
                        note[0][:4] if note else None,
                        "Fine-tuned: the change sits in the reasoning." if k == "lora" else "Consistency-trained: the change sits before the readout.",
                        {"panels_css_px": [x[:4] for x in panels]})
        await b.close()

    man["C5"] = "end card, composed (no capture): '42% -> 12%' and '92% -> 76%' from FINDINGS."
    (out / "manifest.json").write_text(json.dumps(man, indent=1))

    from PIL import Image, ImageDraw, ImageFont
    names = [s["id"] for s in man["stills"]]
    tw, th = 640, 360
    cols = 3; rows = (len(names) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + 30)), "white"); d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 22)
    for i, n in enumerate(names):
        im = Image.open(out / f"{n}.png").convert("RGB").resize((tw, th))
        x, y = (i % cols) * tw, (i // cols) * (th + 30)
        sheet.paste(im, (x, y + 30)); d.text((x + 6, y + 3), n, fill="black", font=f)
    sheet.save(out / "contact.png")
    print(json.dumps({k: v for k, v in man.items() if k != "stills"}, indent=1)[:3000])

asyncio.run(main())
