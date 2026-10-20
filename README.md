# Do Thinking Modes Make Chain-of-Thought More Honest?

CSE 598, Fall 2026 · Group 10: Shrey Bishnoi, Arsha Jindal, Ritik Agarwal

We slip a wrong hint into a multiple-choice question. Does the hint change the model's
answer, and does the model admit it? Thinking models return their private reasoning and
their final answer separately, so we can check which of the two mentions the hint.

## What we found so far (progress round, Oct 2026)

- **A wrong hint changes the answer when the model is unsure.** Olmo 3 7B Instruct
  followed 5 of 48 hints on easy puzzles, and 7 of 19 on harder exam questions.
- **Thinking models trust tools.** They picked a tool-looking hint's wrong option on
  **17 of 31** questions, the same hint from the user on **2 of 31**.
- **They keep it private.** In 216 hinted puzzle runs, the private reasoning mentioned
  the hint in **208**, the final answer in **8**.
- **A reviewer can pass a steered answer along.** It accepted 0 of 15 from the answer
  alone, but 7 of 15 once it read the explanation.

These are keyword counts until the hand labels are done.

## Where things are

| Doc | What's in it |
|---|---|
| [`docs/OVERVIEW.md`](docs/OVERVIEW.md) | **Everything done so far:** experiments, results, models, failures found, the code and data map, known gaps |
| [`docs/PLAN.md`](docs/PLAN.md) | **What's next:** Tracks A, B, C, timeline, gates, budget, risks |
| [`docs/progress/LABELING_GUIDE.md`](docs/progress/LABELING_GUIDE.md) | How to hand-label replies (with `LABEL_QUEUE.csv`) |
| [`cot-disclosure/README.md`](cot-disclosure/README.md) | Setup, commands, what each file does |
| [`cot-disclosure/ui/README.md`](cot-disclosure/ui/README.md) | The demo app |
| [`cot-disclosure/finetune/README.md`](cot-disclosure/finetune/README.md) | Track A data and training details |

| Folder | Contents |
|---|---|
| `cot-disclosure/` | All code, configs, raw results (`results/`) and tests |
| `docs/` | The docs above, plus `progress/RESULTS_SUMMARY.json` (every reported number) and `LABEL_QUEUE.csv` |
| `presentation/` | The progress deck (v3 is the one presented), figures, evidence viewer, screenshots |

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r cot-disclosure/requirements.txt
cp cot-disclosure/.env.example cot-disclosure/.env      # add your Voyager key
cd cot-disclosure && ../.venv/bin/python -m pytest -q tests   # 61 tests, no network
cd .. && python3 cot-disclosure/ui/app.py                 # demo at http://127.0.0.1:8765
```

Recompute every reported number from the saved runs (no API calls):

```bash
.venv/bin/python cot-disclosure/progress/analyze_progress.py
```
