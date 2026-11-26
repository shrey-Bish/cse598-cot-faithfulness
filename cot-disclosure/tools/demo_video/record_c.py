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


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8797/demo.html")
    ap.add_argument("--out", default=str(ROOT / "docs/presentation/final/storyboard/video_beats/clipC"))
    ap.add_argument("--scale", type=int, default=2)
    a = ap.parse_args()
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
