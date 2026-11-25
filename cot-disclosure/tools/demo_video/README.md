# Demo video clips (final deck, slides 5 and 6)

Rebuilds the two clips from the local scratch pad. Outputs go to `docs/presentation/final/video/` (gitignored: the
frames show recorded model text; nothing from them belongs in a tracked file).

| clip | length | beats (element and position, no quoted text) |
|---|---|---|
| A (slide 5) | about 49 s | A1 zoom to the hint slip (top left); A2 the reasoning pane streams in real time for 3 s, then finish: zoom to its first highlighted mark, gold box; A3 zoom to the answer box (below the pane); A4 the three red-pen checks, red box; A5 the finder line (left column), then the count line under the run; A6 whole pad, hold = poster |
| B (backup) | about 28 s | B1 split view, zoom to the verdict line across the top; B2 the "cost" pattern, zoom to the verdict line; B3 review dataset, click "Send to the review team", pan across the flow left to right = poster |

The question and pattern come from the page's own finder (`PAD_API.set(... find: "cited")`), not by hand.

## Rebuild

```sh
# 1. serve the pad (127.0.0.1 only); keep running
cd cot-disclosure && ../.venv/bin/python -u tools/demo_template/serve.py --no-open --port 8797 &

# 2. capture (Playwright, 1920x1080 at scale 2, light theme) into docs/presentation/final/video/raw/
cd .. && .venv/bin/python cot-disclosure/tools/demo_video/record.py

# 3. compose (about 3 minutes): clip_a.mp4, clip_b.mp4, poster_a.png, poster_b.png, stills/
.venv/bin/python cot-disclosure/tools/demo_video/compose.py            # --only a|b, --crf 20

# 4. stop the server
kill %1
```

Encode: `ffmpeg -framerate 30 -i frames/%05d.png -c:v libx264 -pix_fmt yuv420p -crf 20 -preset slow -movflags +faststart`
(compose.py runs it). Captions are 44 px Arial on a near-black band whose bottom edge is at y = 880 (above the
template's safe-zone strip); 0.3 s dips between beats; no audio. Raise `--crf` if a clip passes about 15 MB.
Check: `ffprobe`, then look at a contact sheet of frames.
