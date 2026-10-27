# Do Thinking Modes Make Chain-of-Thought More Honest?

CSE 598, Fall 2026 · Group 10: Shrey Bishnoi, Arsha Jindal, Ritik Agarwal.
Last updated: 2026-10-27.

We slip a wrong hint into a multiple-choice question, from the user or from a tool. Does the hint
change the model's answer, and does the model admit it? Thinking models return their private
reasoning and their final answer separately, so we can check which of the two mentions the hint.
Then we look inside one open thinking model (Olmo 3 7B Think) to see where the hint takes over and
which layers carry it, and we try a fix: fine-tuning with **source tags** that mark every token
with where it came from.

## What we found so far

Each line is one entry in [`docs/FINDINGS.md`](docs/FINDINGS.md), with its source and status.
Mentions are keyword counts until the hand labels are done.

**Confirmed**
- **Thinking models trust tools** ([F1](docs/FINDINGS.md)): they followed a tool-looking hint's
  wrong option on 17 of 31 questions, the same hint from the user on 2 of 31 (+48 points [+31, +65];
  two models, Voyager's served format).
- **They keep it private** ([F3](docs/FINDINGS.md)): the private reasoning names the hint in 208 of
  216 hinted runs, the final answer in 8.
- **Known answers are overridden late, on a few questions** ([F4](docs/FINDINGS.md)): on questions
  Olmo 3 7B Think gets right without a hint, it still ends on the hint in 43 of 110 hinted runs
  [30, 48%], 26 of them late in the reasoning; 9 questions.
- **The hint is the starting answer** ([F5](docs/FINDINGS.md)): forced to answer before any
  reasoning, it gives the hint letter in 198 of 199 hinted runs; the lead then swings many times.
- **Mentions mark the hint in play, not the hint winning** ([F6](docs/FINDINGS.md)): a mention comes
  just before 25 of 57 late takeovers and just before 43 of 94 resisted runs' closest approaches.
- **Deleting the reasoning's mentions moves the answer only at the cut** ([F7](docs/FINDINGS.md)):
  7 of 19 back to the own answer vs 1 of 19 for a length-matched control (+32 points [+11, +56]);
  given room to continue, the model returns to the hint.
- **The Sol weights are the checkpoint we meant** ([F9](docs/FINDINGS.md)): sha256 equal to
  d97e442; a rule set in advance for matching Voyager failed narrowly on 4 positions, so every
  evaluated system runs on Sol.
- **Tool hints get less attention at the answer than user hints, yet move it more**
  ([F10](docs/FINDINGS.md)): tool − user −8.1e-3 [−1.0e-2, −6.1e-3] (full-attention layers, hint
  minus control).
- **Three layers read the hint from the prompt** ([F11](docs/FINDINGS.md)): layers 15, 19 and 23
  hold 0.90 [0.85, 0.96] of the drop in hint-token restoration at the takeover (activation
  patching; 19 cuts, 9 questions).
- **The same heads separate followed from resisted runs** ([F12](docs/FINDINGS.md)): +0.040 [+0.021,
  +0.057] over the 8 top heads in those layers, carried by L19H31, L23H17 and L15H31.
- **At the takeover, the prompt's letter does more than the reasoning's repetition**
  ([F13](docs/FINDINGS.md)): swapping the prompt's letter moves the answer off the hint in 13 of
  21 cases; deleting the mentions, back to the own answer in 7 of 19.
- **The hint takes the lead when the reasoning looks back at it** ([F14](docs/FINDINGS.md)):
  attention to the hint rises at lead onsets, lasting +4.8e-3 [+2.7e-3, +7.1e-3] and temporary
  +3.4e-3 [+2.0e-3, +5.3e-3], against about 0 elsewhere.

**Tentative**
- Olmo 3 7B Think alone, in its own format: tool − user +19 points [−2, +40] ([F1](docs/FINDINGS.md)).
- The serving format changed its hint following, by an amount we can't separate from the token
  budget ([F2](docs/FINDINGS.md)).
- The hint's pull may weaken once its last mention leaves the 4,096-token window: −0.68 [−1.28,
  −0.26] in log-odds ([F8](docs/FINDINGS.md)).
- The mechanism as a whole (FINDINGS, mechanism paragraph): the extra trust in tools lies in what
  layers 15, 19 and 23 read at the hint, not in how much they attend to it.

**Next:** Steps 6–7 (training data) finish Oct 27; train LoRA, tag and combined versions on ASU Sol
(week 11); evaluate all systems on held-out questions (weeks 12–13); Gate 3 on Nov 22.

## Where things are

| Doc | What's in it |
|---|---|
| [`docs/OVERVIEW.md`](docs/OVERVIEW.md) | Everything done so far: experiments, Track A Steps 1–10, models and Voyager facts, Sol setup, traps, code map |
| [`docs/FINDINGS.md`](docs/FINDINGS.md) | Every finding: claim, numbers, source, status; measurement traps; figure plan |
| [`docs/PLAN.md`](docs/PLAN.md) | What's left: timeline, gates, the Sol job plan, budget, risks |
| [`docs/TODO.md`](docs/TODO.md) | Every open item: status, blocker, owner, calls needed, time |
| [`docs/RUNBOOK.md`](docs/RUNBOOK.md) | How to run each step: where, the exact commands, inputs, outputs, time, what to check |
| [`docs/sessions/`](docs/sessions/INDEX.md) | Session logs, one per run or stop ([latest](docs/sessions/LATEST.md)) |
| [`docs/progress/LABELING_GUIDE.md`](docs/progress/LABELING_GUIDE.md) | How to hand-label replies (with `LABEL_QUEUE.csv`) |
| [`cot-disclosure/README.md`](cot-disclosure/README.md) | Code setup, commands, what each file does |
| [`cot-disclosure/finetune/README.md`](cot-disclosure/finetune/README.md) | Track A pipeline, data and training |
| [`cot-disclosure/finetune/gpu/README.md`](cot-disclosure/finetune/gpu/README.md) | The Sol GPU kit |

| Folder | Contents |
|---|---|
| `cot-disclosure/` | All code, configs and tests. Produced data lives in gitignored `results/trackA/`, `results/trackB/`, `results/trackC/` and `finetune/data/`; numbers-only summaries in `results/summaries/` |
| `docs/` | The docs above, plus `progress/RESULTS_SUMMARY.json` (the progress round's numbers) |
| `presentation/` | The progress deck (v3 was presented), figures, evidence viewer, screenshots |

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r cot-disclosure/requirements.txt
cp cot-disclosure/.env.example cot-disclosure/.env       # add your Voyager key
cd cot-disclosure && ../.venv/bin/python -m pytest -q     # 283 tests, no network
cd .. && python3 cot-disclosure/ui/app.py                 # demo at http://127.0.0.1:8765
```

Recompute reported numbers from saved runs (no API calls):

```bash
.venv/bin/python cot-disclosure/progress/analyze_progress.py     # the progress round
cd cot-disclosure && ../.venv/bin/python tools/export_summaries.py --check   # Track A summaries hold no text
```

Each Track A finding names the script that recomputes it (most need the local runs, which stay off
GitHub). Before a push, install the pre-push check (RUNBOOK, repo hygiene).
