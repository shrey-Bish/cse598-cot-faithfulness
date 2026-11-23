# docs/demo/

[`index.html`](index.html) is the demo: one offline file, with its fonts embedded and no network calls. Download it and
open it in any browser. Nothing plays by itself.

Three parts:
- **How we did it:** a map of 11 steps, each with its real numbers.
- **Run it:** a test bench of 6 tests, each with its frozen result.
- **What we found:** 10 result sheets.

Keys: **1**, **2**, **3** switch parts, **←** **→** step, **T** changes the theme.

The file is generated, so do not edit it by hand. Its source is `cot-disclosure/tools/demo_template/` and the command is
`cd cot-disclosure && ../.venv/bin/python tools/demo_template/build.py`. Every number comes from the frozen summaries.

A local build with recorded runs, `cot-disclosure/results/demo/demo.html`, is produced data and is not in the repo.
It opens on the scratch pad (Nov 23): one recorded run of a question streams its private reasoning with the hint's
mentions highlighted, and a fix can be compared with no fix on the same question and hint. Its runs are built by
`tools/demo_template/pad.py` into `results/demo/pad/` and served on this machine only by
`../.venv/bin/python tools/demo_template/serve.py` (from `cot-disclosure/`); opened by double-click, it has the drawn
questions only.
The earlier Hint Explainer is in `archive/superseded/explainer_2026-11-14/`.
