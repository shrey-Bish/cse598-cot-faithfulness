"""Compose clip_c.mp4 (1920x1080, 30 fps, no audio) from record_c.py --frames' raw frames (video/raw_c/).

Same method as compose.py (eased crops of the 2x captures, gold/red boxes, burned-in captions at 44 px on the near-black band
with its bottom at y = 880, 0.3 s crossfades, never a dip to black, H.264 yuv420p -crf 20 faststart). Captions are the plan's
words (about the beats), not recorded text; the end card is composed here.
Usage: compose_c.py [--raw DIR] [--out DIR] [--crf 20]
"""
import argparse, json, pathlib, sys
from PIL import Image, ImageDraw
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import compose as C
from compose import Beat, GOLD, RED, union, grow, fit

_caption = C.caption
C.caption = lambda im, text, a: im if not text else _caption(im, text, a)   # the end card has no caption band


def cam(x, y, w): return (x, y, w, w * 9 / 16)


def end_card(path):
    S = C.S; W, H = C.W * S, C.H * S
    im = Image.new("RGB", (W, H), (20, 20, 20)); d = ImageDraw.Draw(im)
    f = lambda px: C.font(px * S)
    lines = [("Consistency training vs no fix", 64, (255, 255, 255), 250), ("Wrong hints followed: 42% → 12%", 76, GOLD, 400),
             ("Right tool hints taken: 92% → 76%", 76, GOLD, 540)]
    for text, px, col, y in lines: d.text((W / 2, y * S), text, font=f(px), fill=col, anchor="mm")
    d.text((W / 2, 690 * S), "Real recorded runs, found by pattern.", font=f(40), fill=(215, 215, 215), anchor="mm")
    im.save(path)


def clip_c(m, raw):
    words = json.loads((raw / "words.json").read_text())
    cut = lambda seq: seq[-1][0] + 0.07
    # ---- C1
    s1, f1 = m["C1_stream"], m["C1_finish"]; c1 = cut(s1)
    seq1 = [list(x) for x in s1] + [[c1 + t, f] for t, f in f1]
    B = m["C1_boxes"]; hint = grow(m["C1_hint_box"], 8); lines = m["C1_sentence"]["lines"]; sent = union(*lines)
    chk = union(B["ans"], (B["chk"][0], B["chk"][1], 340, B["chk"][3]))   # the answer box, the three labels and the pencilled yes/no marks to their right
    C1 = Beat("C1", 8.0, (seq1, "C1.png", 0.0),
              [(0.2, 0.8, cam(140, 246, 1000)), (c1 - 0.6, c1 + 0.1, fit(B["pad"], minw=1100)), (c1 + 0.9, c1 + 1.6, fit(sent, minw=1300)),
               (c1 + 3.3, c1 + 4.0, fit(chk, minw=1100))],
              [(0.9, hint, GOLD)] + [(c1 + 2.0, ln, GOLD, 4) for ln in lines] + [(c1 + 4.2, grow(chk, 4), RED)],
              [(0.3, 7.7, "No fix: it follows the tool’s wrong answer, and the answer doesn’t say so.")])
    # ---- C2
    s2, f2 = m["C2_stream"], m["C2_finish"]; c2 = cut(s2)
    seq2 = [list(x) for x in s2] + [[c2 + t, f] for t, f in f2]
    B2 = m["C2_boxes"]; ver = grow(B2["verdict"], 6); find = B2["find"]
    C2 = Beat("C2", 8.0, (seq2, "C2.png", 0.0),
              [(c2 + 1.3, c2 + 2.1, fit(ver, minw=1100)), (5.4, 6.2, fit(find, below=0.55, minw=1100))],
              [(c2 + 2.4, ver, RED), (6.4, grow(find, 4), GOLD)],
              [(0.3, 7.7, "Same question, same hint: consistency training held. It held on 26 of 112 questions.")])
    # ---- C3
    name = m["C3_name_lines"][0]; lab = m["C3_label_lines"][0]
    pathx = min(w[1] for w in words["C3end"] if w[0].startswith("results/") and abs(w[2] - lab[1]) < 6)   # the file path starts here: keep it out of frame
    labbox = (lab[0], lab[1], pathx - lab[0] - 10, lab[3])     # "Hand label: ... answered (G)." only
    camA = (180, 357, 1000, 562.5); bw = pathx - 190 - 10; camB = (190, 1080 - bw * 9 / 16, bw, bw * 9 / 16)
    sc = m["C3_scroll"]
    seq3 = [[0.0, "C3top.png"]] + [[2.8 + t, f] for t, f in sc]   # the scroll starts after the camera has narrowed (2.7)
    C3 = Beat("C3", 6.0, (seq3, "C3end.png", 0.0), [(0.1, 0.7, camA), (2.2, 2.7, camB)],
              [(0.9, grow(name, 5), GOLD), (4.7, grow(labbox, 5), GOLD)],
              [(0.3, 5.7, "Fine-tuned, another question: when it still follows, its answer says so (37 of 42 vs 18 of 42, hand-labelled).")])
    # ---- C4
    camL = (688, 418, 1110, 624.4)       # starts below the panel's first line (which holds an internal test code)
    seq4 = [[0.0, "C4apre.png"]] + [[0.8 + t, f] for t, f in m["C4a_anim"]]
    C4a = Beat("C4a", 5.2, (seq4, "C4a.png", 0.0), [(0.0, 0.05, camL)], [(2.8, (m["C4a_panel"][0][0] + 6, 421, m["C4a_panel"][0][2] - 12, 140), GOLD, 2)],
               [(0.3, 4.9, "Three layers carry the hint: together 90%.")])
    note = (190, 639, 650, 365.6)
    cap2 = "Training changed it in different places: fine-tuning in the reasoning; consistency training before the readout layers."
    C4b = Beat("C4b", 2.8, ([list(x) for x in m["C4b_anim"]], "C4b.png", 0.0), [(0.0, 0.5, note)], [(0.8, grow(m["C4b_note"][0], 4), GOLD)],
               [(-1.0, 3.8, cap2)])
    C4c = Beat("C4c", 2.8, ([list(x) for x in m["C4c_anim"]], "C4c.png", 0.0), [(0.0, 0.1, note)], [(0.6, grow(m["C4c_note"][0], 4), GOLD)],
               [(-1.0, 2.5, cap2)])
    # ---- C5
    C5 = Beat("C5", 5.0, "C5card.png", [(0.0, 0.1, C.PAGE)], [], [(0.0, 5.0, "")])
    return [C1, C2, C3, C4a, C4b, C4c, C5]


CODE_RE = r"\b(?:F\d{1,2}|FB\d|FC\d|A\d{2}|B\d{1,2}(?:R\d)?|C\d{1,2}|E2|L[346]|T\d{1,2}|Gate \d|Test \d)\b|results/|\.jsonl|\.json"


def sweep(beats, raw):
    """For every frame's camera box, the visible page words that intersect it (DOM boxes captured by record_c.py --frames),
    tested against the internal-code regex plus file paths. Prints hits per beat."""
    import re
    words = json.loads((raw / "words.json").read_text()); rx = re.compile(CODE_RE)
    states = {"C1": ["C1"], "C2": ["C2"], "C3": ["C3top", "C3end"], "C4a": ["C4apre", "C4a"], "C4b": ["C4b"], "C4c": ["C4c"], "C5": []}
    st = C.PAGE; hits = {}
    for b in beats:
        start = st; st = C.cam_end(b, st)
        for i in range(int(b.dur * C.FPS)):
            x, y, w, h = C.cam_at(b, i / C.FPS, start)
            t_ = i / C.FPS
            sts = ["C3top"] if b.name == "C3" and t_ < 2.8 else states[b.name]    # C3 shows the overlay unscrolled until the scroll starts (2.8)
            for sn in sts:
                inn = [wd for wd in words[sn] if wd[1] < x + w and wd[1] + wd[3] > x and wd[2] < y + h and wd[2] + wd[4] > y]
                lines = {}
                for wd in sorted(inn, key=lambda q: (round(q[2] / 6), q[1])): lines.setdefault(round(wd[2] / 6), []).append(wd[0])
                for ln in lines.values():
                    for mt in rx.finditer(" ".join(ln)): hits.setdefault((b.name, sn, mt.group(0)), round(i / C.FPS, 2))
    for b in beats: print(b.name, "hits:", [(k[1], k[2], t) for k, t in hits.items() if k[0] == b.name] or "none")
    return hits


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(C.ROOT / "docs/presentation/final/video/raw_c"))
    ap.add_argument("--out", default=str(C.ROOT / "docs/presentation/final/video"))
    ap.add_argument("--crf", type=int, default=20); ap.add_argument("--poster", default="C5"); ap.add_argument("--sweep", action="store_true")
    C.ARGS = ap.parse_args(); raw, out = pathlib.Path(C.ARGS.raw), pathlib.Path(C.ARGS.out)
    m = json.loads((raw / "manifest.json").read_text()); end_card(raw / "C5card.png")
    beats = clip_c(m, raw)
    if C.ARGS.sweep: sweep(beats, raw); sys.exit(0)
    t = 0.0
    for i, b in enumerate(beats):
        print(b.name, f"{t:.2f}-{t + b.dur:.2f}"); t += b.dur - (0.3 if i < len(beats) - 1 else 0) if False else 0
    print(C.build("c", beats, raw, out, C.ARGS.poster, True))
