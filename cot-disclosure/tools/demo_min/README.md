# demo_min: the three-step demo page and its clip

A plain page (one column, Arial, near-black, maroon and gold) and an 18 s clip, for one slide. It shows the recorded runs of
`mmlupro-11784` (the pad's "Show me" pick; the pad's runs for the inserted study-guide tool turn with a wrong hint): the setup,
the original model's answer and one sentence of its private reasoning, the consistency-trained model's answer. Output is local
and gitignored (`docs/presentation/final/video/`); no model text is in any tracked file.

```sh
.venv/bin/python cot-disclosure/tools/demo_min/build.py     # -> docs/presentation/final/video/demo_min/index.html (+ facts.json)
.venv/bin/python cot-disclosure/tools/demo_min/record.py    # -> video/clip_d.mp4, video/poster_d.png
```

The stem's two missing spaces (a dataset typo) are restored for display; the check allows exactly that and nothing else (the reasoning quote stays strict).

Keys: right arrow or PageDown next step, left arrow or PageUp back. `build.py` reads `results/demo/pad/` (pad.py's output) and
`finetune/eval.py`'s job, and asserts: the hint is an inserted tool turn whose `expected` is the hinted letter, the key differs,
the original run followed the hint, the consistency-trained run (system `a40`) ends on the key, the original's final answer has
no `cue_tool` match, and the quoted sentence is found byte for byte in the run (`quote_in`). `record.py` asserts no overflow and
no codes, ids or paths in the visible text (`find_codes`), then writes the clip (recorded at 1200x675 CSS px, device scale 1.6, so 1920x1080; H.264 yuv420p, 30 fps, crf 20,
faststart, no audio; 5.9 s per step, 150 ms fades). Test: `.venv/bin/python -m pytest cot-disclosure/tests/test_demo_min.py`.
