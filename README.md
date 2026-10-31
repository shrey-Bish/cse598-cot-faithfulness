# Do Thinking Modes Make Chain-of-Thought More Honest?

CSE 598, Fall 2026 · Group 10: Shrey Bishnoi, Arsha Jindal, Ritik Agarwal. Last updated: 2026-10-31.

We slip a wrong hint into a multiple-choice question, from the user or from a tool, and ask two things: does the hint
change the model's answer, and does the model say so? Thinking models return their private reasoning and their final
answer separately, so we can check which of the two admits the hint. Three tracks:
- **Track A** looks inside one open thinking model, Olmo 3 7B Think, to find where the hint takes over, and tries
  fixes.
- **Track B** tests more models and channels.
- **Track C** asks what a wrong tool answer does to a team of agents: a solver, a reviewer and a checker.

## The story so far, in five lines

Details, numbers and status for each line are in [`docs/FINDINGS.md`](docs/FINDINGS.md) ("The story so far").

1. **Tools sway models more than users.** The same wrong hint moves the answer more from a tool than from the user,
   in all four models tested (Gate 2).
2. **After a tool call, the final answer stops explaining.** It becomes a bare letter while the private reasoning
   names the tool. Disclosure can be prompted, but it doesn't reduce deference to the tool (B15).
3. **Inside Olmo 3 7B Think, layers 15, 19 and 23 read the hint straight from the prompt.** They hold 0.90 of the
   drop at the takeover, and the result replicates on questions not used to find them, by two methods (F26, F32).
4. **Downstream, a reviewer shown the tool's trace defers to it, but only in one model family** (Olmo, 2 of 6
   reviewers). A checker that never sees the tool held every time. The deferring reviewer follows the solver's
   citation of the tool's letter as authority (C16–C18).
5. **The fix, so far:** all four fine-tuned versions pass Gate 3 by its rule, but none beats a one-line
   instruction on following, the source tags don't act where the tool's tokens are, and the LoRA versions'
   false-disclosure candidates rise (hand labels pending; F28). Inference-time attention scaling (B1) and a second
   model's mechanism (Qwen3-8B) are under way.

## Where to start

| You are | Read first | Then |
|---|---|---|
| Ritik (Track A, labels, the report) | [`docs/STATUS.md`](docs/STATUS.md), [`docs/TODO.md`](docs/TODO.md) | the newest daily in [`archive/sessions/`](archive/sessions/INDEX.md); [`docs/RUNBOOK.md`](docs/RUNBOOK.md) |
| Shrey (Track C, from Oct 30) | [`docs/handoff/TRACK_C.md`](docs/handoff/TRACK_C.md) | [`docs/handoff/SOL_SETUP.md`](docs/handoff/SOL_SETUP.md), [`cot-disclosure/README.md`](cot-disclosure/README.md) |
| Arsha (Track B, from Nov 3) | [`docs/handoff/TRACK_B.md`](docs/handoff/TRACK_B.md) | [`docs/RUNBOOK.md`](docs/RUNBOOK.md) §18 |
| A grader | this page, then FINDINGS' "story so far" | [`docs/STATUS.md`](docs/STATUS.md), [`docs/PLAN.md`](docs/PLAN.md) |
| A paper reviewer | [`docs/paper/CLAIMS.md`](docs/paper/CLAIMS.md) | [`docs/paper/supplement/EVIDENCE.md`](docs/paper/supplement/EVIDENCE.md) and [`PREREGISTRATIONS.md`](docs/paper/supplement/PREREGISTRATIONS.md) |

## The folders

```
README.md            this page
cot-disclosure/      all code, configs and tests: README.md is the code guide
  finetune/gpu/        the Sol GPU kit: README.md
  results/summaries/   the tracked, numbers-only results (produced data stays in gitignored results/trackA|B|C)
docs/                the living docs
  FINDINGS.md          every finding: claim, numbers, source, status; the story so far; measurement traps
  PLAN.md TODO.md      what's left: timeline, gates, Sol job plan, risks; every task with owner and status
  RUNBOOK.md           how to run each step: where, the commands, inputs, outputs, what to check
  STATUS.md GANTT.xlsx gantt.png gantt.pdf
                       progress, generated from the repo (tools/make_gantt.py): what's done, what's next, by
                       whom, by when; gantt.pdf has a page per track
  TRACK_A.md           Track A's design: pipeline, data, training, tags, evaluation
  TRACK_A_PROVENANCE.md   B1/B2: provenance-scaled attention and the learned gate
  MOVES.md             every file moved on Oct 30: old path -> new path, and why
  handoff/             TRACK_B.md (Arsha), TRACK_C.md (Shrey), SOL_SETUP.md (Sol for a second user)
  paper/               working material for two possible papers (bullets, not prose):
                         CLAIMS.md            each candidate claim: evidence (F-numbers), status, the strongest
                                              objection, what would settle it
                         OUTLINE.md           an outline per thread (1: localization and a targeted repair;
                                              2: automation bias in LLM reviewers), the evidence each section
                                              needs and what's missing
                         REVIEWER_QUESTIONS.md   questions we can't answer yet, and which runs answer which
                         RELATED_WORK.md      verified references only, with how we differ
                         figures/             reviewer_by_prompt, readout_by_layer, taught_loss (PNG, SVG and a CSV
                                              of every plotted number; tools/paper_figures.py)
                         supplement/          EVIDENCE, PREREGISTRATIONS, DEVIATIONS, TRAPS, tables, figures,
                                              APPENDIX_OUTLINE (tools/make_supplement.py)
  progress/            the labeling guides (LABELING_GUIDE.md, RATER_GUIDE.md) and two files code reads:
                         LABEL_QUEUE.csv, RESULTS_SUMMARY.json (the progress round's numbers)
archive/             history, kept but out of the way
  sessions/            every session log and daily, one folder per date (INDEX.md lists them; LATEST.md is the newest)
  progress-round/      the October progress presentation (decks, figures, screenshots), the demo's guide, its console logs
  superseded/          the Oct 27 overview and the Oct 27 front page
  merged-docs/         the originals of merged docs, unchanged
```

The paper figures are remade from the tracked summaries with
`cd cot-disclosure && ../.venv/bin/python tools/paper_figures.py`, and the supplement with
`../.venv/bin/python tools/make_supplement.py`.

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r cot-disclosure/requirements.txt
cp cot-disclosure/.env.example cot-disclosure/.env       # your own Voyager key: RC_LLM_API_KEY, RC_LLM_BASE_URL
cd cot-disclosure && ../.venv/bin/python -m pytest -q     # the tests, no network
cd .. && python3 cot-disclosure/ui/app.py                 # the progress round's demo at http://127.0.0.1:8765
```

Recompute reported numbers from saved runs, with no API calls:

```bash
.venv/bin/python cot-disclosure/progress/analyze_progress.py                  # the progress round
cd cot-disclosure && ../.venv/bin/python tools/export_summaries.py --check     # the summaries hold no text
```

Each finding names the script that recomputes it. Most need the local runs, which stay off GitHub (produced data is
gitignored; teammates get it as a bundle). Before a push, install the pre-push check (RUNBOOK §17).
