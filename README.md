# Do Thinking Modes Make Chain-of-Thought More Honest?

CSE 598, Fall 2026 · Group 10: Shrey Bishnoi, Arsha Jindal, Ritik Agarwal

When a hint pushes a model toward an answer, does the model say so? We test three
pairs of models (Olmo 3 7B, Olmo 3 32B, Qwen3 30B) on ASU's free Voyager service.
Each pair has a regular chat model and a thinking model. Thinking models send back
their private reasoning and their final answer separately, so we can check which of
the two mentions the hint.

## Status (progress presentation, October 2026)

**What ran**
- **Pilot:** 24 puzzles × 6 models × 6 runs = 864 calls, plus "think briefly" and
  "answer only" side tests. 1,056 calls in total, 0 failed.
- **Today (2026-10-04):**
  - timing run
  - Experiment A: reviewer demo
  - Experiment B: 30 MMLU-Pro items, cue in the user turn vs a simulated tool block
  - truncation sweep

  Every prompt and reply is saved in `cot-disclosure/results/progress/`.

**Key numbers** (all in `docs/progress/RESULTS_SUMMARY.json`)
- **Wrong-hint following:**
  - Olmo 3 7B Instruct 5/48 (10.4%, 95% range 2.1 to 18.8)
  - Olmo 3 7B Think 1/48
  - the other four models 0/48
  - the same letters without a hint: 0/144 for every model
- **Hint mentioned (keyword pre-sort):** thinking models 208/216 in private reasoning vs
  8/216 in final answers. The keywords also fire on 22/72, 18/72 and 2/72 no-hint traces.
- **"Answer only":** instruct models fall to 1/24 and 2/24. Thinking models keep
  reasoning privately and score 23/24 and 24/24.
- **Token cap:** private reasoning leaks into the visible answer when the reply isn't
  streamed. Same 8 requests: 8/8 leaked unstreamed, 0/8 leaked streamed.
- **Reviewer demo (n = 5 steered + 6 twin cases):** the reviewer kept the hinted wrong
  answer 0/15 times with the answer only and 7/15 with the explanation.
- **Experiment B (30 MMLU-Pro items, first look):**
  - On uncertain items, Olmo 3 7B Instruct took a wrong cue 7/14 times.
  - A simulated tool-result cue steered Olmo 3 7B Think 10/20 and Qwen3 30B Thinking
    7/11 times. The same letter as a user sentence steered them 2/20 and 0/11.
  - In tool-steered runs, private reasoning referred to the tool 9/10 and 7/7 times;
    final answers 2/10 and 4/7.

**Checkpoints:** `docs/progress/MODELS.md` (Voyager IDs, candidate model cards; the
Olmo 32B identity is unconfirmed).

**Notes and figures:**
- notes: [`docs/progress/`](docs/progress/), starting with `PROGRESS_REPORT.md` and
  `SLIDE_POINTS.md`
- figures: [`presentation/progress/figures/`](presentation/progress/figures/)
- evidence viewer and screenshots: [`presentation/progress/`](presentation/progress/)

**Reproduce:**

```bash
.venv/bin/python cot-disclosure/progress/analyze_progress.py       # RESULTS_SUMMARY.json + figures F1-F9
.venv/bin/python cot-disclosure/progress/build_evidence_viewer.py  # presentation/progress/evidence_viewer.html
.venv/bin/python cot-disclosure/progress/take_screenshots.py       # add --headed --slow-mo 300 to watch
cd cot-disclosure && ../.venv/bin/python -m pytest -q tests        # unit tests
```

The commands that call the models (resumable; they need a key in `cot-disclosure/.env`)
are listed in `docs/progress/PROGRESS_REPORT.md` §8.

| Folder | What's in it |
|---|---|
| `cot-disclosure/` | The code that runs the models, the raw results, and the analysis. Its README has the exact commands. |
| `presentation/` | The progress slides and the script that builds them from the results. |

## Get the same numbers

```bash
cd cot-disclosure
python analyze.py          # recomputes every number we report from results/*.jsonl
```

To rerun the experiments themselves you need a Voyager key: `cp .env.example .env`,
add the key, then run `python experiments.py run`.
