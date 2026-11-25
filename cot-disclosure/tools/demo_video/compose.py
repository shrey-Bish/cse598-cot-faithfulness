"""Compose clip_a.mp4 / clip_b.mp4 (1920x1080, 30 fps, no audio) from record.py's raw frames.

Eased crops of the 2x screenshots, gold/red boxes, burned-in captions, 0.3 s dips between beats, ffmpeg encode.
Usage: compose.py [--raw DIR] [--out DIR] [--only a|b] [--crf 20]
Captions are the plan's own words (about the beats), not recorded text.
"""
import argparse, functools, json, pathlib, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[3]
W, H, FPS, S = 1920, 1080, 30, 2          # output size, fps, screenshot scale
PAGE = (0, 0, 1920, 1080)
GOLD, RED, DARK = (255, 198, 39), (200, 16, 46), (25, 25, 25)
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
BAND_BOTTOM = 880                         # captions stay above y = 900
CAP_PX = 44


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def fit(box, below=0.30, pad=1.28, minw=760):
    """a 16:9 rect (CSS px) holding box in its upper part (the caption band sits in the lower ~30%)"""
    x, y, w, h = box
    cw = max(w * pad, (h / (1 - below)) * 16 / 9 * 1.12, minw)
    cw = min(cw, PAGE[2]); ch = cw * 9 / 16
    cx = x + w / 2
    rx = min(max(cx - cw / 2, 0), PAGE[2] - cw)
    ry = min(max(y - ch * 0.08, 0), PAGE[3] - ch)
    return (rx, ry, cw, ch)


def union(*bs):
    x0 = min(b[0] for b in bs); y0 = min(b[1] for b in bs)
    x1 = max(b[0] + b[2] for b in bs); y1 = max(b[1] + b[3] for b in bs)
    return (x0, y0, x1 - x0, y1 - y0)


def grow(b, m):
    return (b[0] - m, b[1] - m, b[2] + 2 * m, b[3] + 2 * m)


@functools.lru_cache(maxsize=12)
def load(p): return Image.open(p).convert("RGB")


@functools.lru_cache(maxsize=8)
def font(sz): return ImageFont.truetype(FONT, sz)


def wrap(text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if f.getlength(t) <= maxw: cur = t
        else: lines.append(cur); cur = w
    return lines + [cur]


def caption(im, text, a):
    if a <= 0: return im
    f = font(CAP_PX); lines = wrap(text, f, 1560)
    lh = int(CAP_PX * 1.25); tw = max(f.getlength(l) for l in lines)
    bw, bh = int(tw + 80), int(lh * len(lines) + 40)
    x0 = (W - bw) // 2; y0 = BAND_BOTTOM - bh
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), 22, fill=DARK + (int(204 * a),))
    for i, l in enumerate(lines):
        d.text((W / 2, y0 + 20 + i * lh + lh / 2), l, font=f, fill=(255, 255, 255, int(255 * a)), anchor="mm")
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")


class Beat:
    def __init__(self, name, dur, src, cams, boxes=(), caps=(), poster=None):
        self.name, self.dur, self.src, self.cams, self.boxes, self.caps = name, dur, src, cams, boxes, caps

    def image_at(self, t, raw):
        seq, still, t0 = self.src if not isinstance(self.src, str) else (None, self.src, 0)
        if seq is None: return load(str(raw / still))
        tt = t - t0
        if tt >= seq[-1][0] + 0.09: return load(str(raw / still))      # past the capture: the settled still
        pick = seq[0][1]
        for ft, f in seq:
            if ft <= tt: pick = f
        return load(str(raw / pick))


def cam_at(beat, t, start):
    r = start
    for (t0, t1, to) in beat.cams:
        if t >= t1: r = to
        elif t > t0:
            k = ease((t - t0) / (t1 - t0)); a = r
            return tuple(a[i] + (to[i] - a[i]) * k for i in range(4))
        else: break
    return r


def cam_end(beat, start):
    return beat.cams[-1][2] if beat.cams else start


def render(beat, t, start, raw, with_caps=True, with_boxes=True):
    im = beat.image_at(t, raw); x, y, w, h = cam_at(beat, t, start)
    out = im.resize((W, H), Image.BICUBIC, box=(x * S, y * S, (x + w) * S, (y + h) * S))
    if with_boxes:
        d = ImageDraw.Draw(out)
        for (t0, bx, col) in beat.boxes:
            if t >= t0:
                k = ease((t - t0) / 0.25); bx = grow(bx, 5)
                sx, sy = W / w, H / h
                r = ((bx[0] - x) * sx, (bx[1] - y) * sy, (bx[0] + bx[2] - x) * sx, (bx[1] + bx[3] - y) * sy)
                d.rounded_rectangle(r, 8, outline=col, width=max(1, int(6 * k)))
    if with_caps:
        for (c0, c1, text) in beat.caps:
            a = min((t - c0) / 0.2, (c1 - t) / 0.2, 1)
            out = caption(out, text, a)
    return out


def build(name, beats, raw, out, posters, only_stills):
    fr = out / f"_frames_{name}"; shutil.rmtree(fr, ignore_errors=True); fr.mkdir(parents=True)
    n = 0; start = PAGE; DIP = 0.15; keep = {}
    for b in beats:
        frames = int(round(b.dur * FPS))
        for i in range(frames):
            t = i / FPS; im = render(b, t, start, raw)
            d = min(t / DIP, (b.dur - t) / DIP, 1.0)       # 0.15 s down + 0.15 s up = a 0.3 s dip
            if d < 1: im = Image.blend(Image.new("RGB", (W, H), DARK), im, max(d, 0))
            im.save(fr / f"{n:05d}.png"); n += 1
        # stills: the beat's last settled frame (captioned), plus a bare one for the poster
        lt = min(b.dur - 1 / FPS, max(c[1] for c in b.caps) - 0.3)   # inside the last caption, fully faded in
        keep[b.name] = (render(b, lt, start, raw), render(b, lt, start, raw, with_caps=False))
        start = cam_end(b, start)
    mp4 = out / f"clip_{name}.mp4"
    subprocess.run(["/opt/homebrew/bin/ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(fr / "%05d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(ARGS.crf), "-preset", "slow",
                    "-movflags", "+faststart", str(mp4)], check=True)
    (out / "stills").mkdir(exist_ok=True)
    for k, (cap, bare) in keep.items():
        (bare if k == "A6" else cap).save(out / "stills" / f"{k}.png")
    cap, bare = keep[posters]
    cap.save(out / f"poster_{name}.png")
    shutil.rmtree(fr)
    return mp4


def clip_a(m, raw):
    A1, A2, A4 = m["A1"]["boxes"], m["A2"]["boxes"], m["A4"]["boxes"]
    hint = grow(A1["hint"], 8); mark = grow(A2["mark"], 6); pad = A2["pad"]; ans = A2["ans"]
    chk = union(A4["ans"], A4["chk"]); find, count = A2["find"], A2["count"]
    stream = m["A2_stream"]; fin = m["A2_finish"]; pen = m["A4_pen"]
    seq = [[t, f] for t, f in stream] + [[stream[-1][0] + 0.07 + t, f] for t, f in fin]
    cut = stream[-1][0] + 0.07   # when pFinish() was called
    return [
        Beat("A1", 7.0, m["A1"]["img"], [(0.3, 1.0, fit(hint, minw=900))], [(1.2, hint, GOLD)],
             [(0.3, 6.7, "A real recorded run. The tool’s answer key says (G); the right answer is (I).")]),
        Beat("A2", 11.0, (seq, "A2.png", 0.0), [(0.0, 0.7, fit(pad, minw=1100)), (cut + 0.4, cut + 1.2, fit(mark, minw=1000))],
             [(cut + 1.5, mark, GOLD)], [(0.3, 10.7, "In its private reasoning, the model cites the tool.")]),
        Beat("A3", 7.0, "A2.png", [(0.0, 0.8, fit(ans, minw=1000))], [(0.9, grow(ans, 4), GOLD)],
             [(0.3, 6.7, "The answer the user sees: (G). No word about the tool.")]),
        Beat("A4", 8.0, (pen, "A4.png", 0.0), [(0.0, 0.7, fit(chk, minw=1100))], [(1.4, grow(chk, 4), RED)],
             [(0.3, 7.7, "Took the wrong hint: yes. Reasoning says so: yes. Answer says so: no.")]),
        Beat("A5", 10.0, "A4.png", [(0.0, 0.8, fit(find, minw=1000)), (5.0, 5.8, fit(count, below=0.55, minw=1100))],
             [(0.9, grow(find, 4), GOLD), (5.2, grow(count, 4), GOLD)],
             [(0.3, 4.9, "Found by pattern: 28 of 114 questions look like this."), (5.1, 9.7, "No fix took this wrong hint in 85 of 233 runs.")]),
        Beat("A6", 6.0, "A4.png", [(0.0, 0.8, PAGE)], [],
             [(0.3, 5.7, "A real recorded run, found by pattern; the count is every question.")]),
    ]


def clip_b(m, raw):
    B1, B2, B3 = m["B1"]["boxes"], m["B2"]["boxes"], m["B3"]["boxes"]
    s1 = m["B1_stream"]; f1 = m["B1_finish"]; cut1 = s1[-1][0] + 0.07
    seq1 = [[t, f] for t, f in s1] + [[cut1 + t, f] for t, f in f1]
    v1 = grow(B1["verdict"], 6); v2 = grow(B2["verdict"], 6)
    f2 = m["B2_finish"]; host = B3["host"]; anim = m["B3_anim"]
    hx, hy, hw, hh = host
    left = (hx - 20, hy - 10, 640, 360); right = (hx + hw - 640 + 20, hy - 10, 640, 360)
    left = fit((hx, hy + 120, hw * 0.55, 330), minw=800); right = fit((hx + hw * 0.45, hy + 120, hw * 0.55, 330), minw=800)
    return [
        Beat("B1", 9.0, (seq1, "B1.png", 0.0), [(cut1 + 1.0, cut1 + 1.8, fit(v1, minw=1100))], [(cut1 + 2.0, v1, RED)],
             [(0.3, 8.7, "The same question, consistency-trained: it resists the wrong answer.")]),
        Beat("B2", 8.0, ([[t, f] for t, f in f2], "B2.png", 0.0), [(1.2, 2.0, fit(v2, minw=1100))], [(2.2, v2, RED)],
             [(0.3, 7.7, "The cost: it also refuses right answers (16 of 118 questions).")]),
        Beat("B3", 11.0, (anim, "B3.png", 0.0), [(0.0, 0.7, left), (3.0, 3.8, right), (7.0, 7.9, fit(host, below=0.3, minw=1300))], [],
             [(0.3, 10.7, "Downstream, the reviewer defers to the tool’s log. A checker that never sees the tool flags it.")]),
    ]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(ROOT / "docs/presentation/final/video/raw"))
    ap.add_argument("--out", default=str(ROOT / "docs/presentation/final/video"))
    ap.add_argument("--only", choices=["a", "b"]); ap.add_argument("--crf", type=int, default=20)
    ARGS = ap.parse_args(); raw, out = pathlib.Path(ARGS.raw), pathlib.Path(ARGS.out)
    m = json.loads((raw / "manifest.json").read_text())
    if ARGS.only in (None, "a"): print(build("a", clip_a(m, raw), raw, out, "A6", True))
    if ARGS.only in (None, "b"): print(build("b", clip_b(m, raw), raw, out, "B3", True))
