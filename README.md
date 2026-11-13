# Do Thinking Modes Make Chain-of-Thought More Honest?

CSE 598, Fall 2026 · Group 10: Shrey Bishnoi, Arsha Jindal, Ritik Agarwal. Last updated: 2026-11-13. **Edited by:** Ritik.

We slip a wrong hint into a multiple-choice question, from the user or from a tool, and ask two things: does the hint
change the model's answer, and does the model say so? Thinking models return their private reasoning and their final
answer separately, so we can check which of the two admits the hint. Three tracks:
- **Track A** looks inside one open thinking model, Olmo 3 7B Think, to find where the hint takes over, and tries
  fixes.
- **Track B** tests more models and channels.
- **Track C** asks what a wrong tool answer does to a team of agents: a solver, a reviewer and a checker.

## The theme and the story in five lines

**"Where did that answer come from?"** A tool's influence loses its source at three levels: inside the model (line
3), in the model's words (line 2) and between agents (line 4). [`docs/PLAN.md`](docs/PLAN.md) places every remaining
experiment on that map. Results freeze on Nov 18; the final presentation and report are on Nov 24. Details, numbers
and status for each line are in [`docs/FINDINGS.md`](docs/FINDINGS.md) ("The story so far").

1. **Tools sway models more than users, mostly through their claim to be the answer key.** The same wrong hint moves
   the answer more from a tool than from the user, in all five Track B models (Gate 2, marked Nov 8); a user who claims the answer
   key's authority moves it about as much, except where the model calls the tool itself every time (B16, F35;
   confirmed same-day, B19). The pull grows with the claimed source's authority: the official solution manual moves
   all three Voyager models more than a classmate, and for Qwen3 30B Thinking more than "answer key" (B24, F40).
   In three more open-weight families on Sol (B20, FB1: Gemma 4, Nemotron 3 Nano, Granite 4.2), tools beat users in
   all 10 readings; whether the tool's form adds to the claim it carries depends on the family and the channel (beyond
   the claim in 5 of 10 readings, the claim moves it more in 1, no difference detected in 4). Labelled: the inserted
   tool turn for Gemma and Nemotron, Granite thinking on only, temperature 1.0.
2. **After a tool call, the final answer stops explaining.** It becomes a bare letter while the private reasoning
   names the tool. Disclosure can be prompted, but it doesn't reduce deference to the tool (B15). More thinking
   doesn't change it: in gpt-oss-20b, raising the reasoning effort from low to high changes neither the bare answer
   after a call nor how often the model follows the tool (no change detected on either; B17, F37, run after its
   one-day window). In B20 (FB1), a call makes the answer barer after Granite's own call and after Nemotron's inserted
   turn with thinking off; with thinking on, Nemotron's bare answer after the inserted turn falls (−14 [−19, −9]):
   thinking writes more of the source down.
3. **Inside Olmo 3 7B Think, layers 15, 19 and 23 read the hint straight from the prompt.** They hold 0.90 of the
   drop at the takeover, and the result replicates on questions not used to find them, by two methods (F26, F32).
   It isn't forced by Olmo's sliding windows: in Qwen3-8B, whose layers all see the whole prompt, three layers chosen
   on one question set hold 0.70 of the drop on another (A37, F36).
4. **Downstream, a reviewer shown the tool's trace defers to it, but only in one model family** (Olmo, 2 of 6
   reviewers). A checker that never sees the tool held every time. The deferring reviewer follows the solver's
   citation of the tool's letter as authority (C16–C18).
5. **The fix, so far:** all four fine-tuned versions pass Gate 3 by its rule, but none beats a one-line
   instruction on following, and the source tags don't act where the tool's tokens are. By hand labels, LoRA's
   keyword false-disclosure candidates are rarely real: most say the hint shaped the answer (L4 part 1, F28).
   Inference-time attention scaling (B1, F38) makes a real cut in following on the inserted tool turn that misses
   its pre-registered acceptance limit ("ignores tools"), underpowered at 30 questions; the 70-question replication
   the budget allowed (B1R) couldn't settle it, so neither it nor A38 is run. Inside the trained model (A18, F39), training
   acts in the reasoning, not on the readout: given base's own reasoning, LoRA's weights pull toward the hint's letter
   harder, not less, and when LoRA follows it is through the same three layers (in plain words:
   [`docs/status/FIX_SO_FAR.md`](docs/status/FIX_SO_FAR.md)). On E2, 120 fresh questions, A39 (F44) finds that marking
   every tool output "unverified" has no effect alone; with the one-line instruction it follows fewer wrong hints on the
   tool turn but takes fewer correct ones, and LoRA with the instruction follows fewer than the instruction alone (R2,
   −8 [−12, −4]) at an acceptance cost of −9 [−13, −5]. Also on E2, A40 trains on the model's own reasoning written without the
   hint (bias-augmented consistency training): it follows far fewer wrong hints than the one-line instruction but takes
   fewer correct ones, "fewer, but costs acceptance" by its rule (F41; with the note, A42, the same, F43). Inside the
   model it is the first fix that acts on the readout, before layers 15, 19 and 23 (A41, F42). B1's replication on E2
   (B1R2) was revived on Nov 6; all 40 parts ended Nov 8, and its last two sweeps wait in Sol's queue.

**Scorecard against the original plan (Nov 7, updated Nov 8 and 13; numbers as read in [`docs/FINDINGS.md`](docs/FINDINGS.md), story item 7).**
- **The failure: tools pull harder than users in every model tested** (Gate 2, marked Nov 8): all five Track B models
  and B20's three new families, 10 of 10 readings (FB1). The label part of Gate 2 is not met (F3).
- **Honesty when following improved with training, in hand labels** (L6, F45, Nov 13): when LoRA follows a wrong hint
  on E2, its answer says so in 37 of 42 hand-labelled runs against the instruction's 18 of 42 (+45 [+25, +64] points,
  "discloses more than the instruction, in labels"; Ritik against the AI check, kappa 0.96). The keyword count agrees
  (exploratory). On the 30, hand labels back it too (L4, F28).
- **Resisting wrong hints improved with A40, but as a trade:** 84 of 694 wrong hints followed against the
  instruction's 237 of 713, and 347 of 459 correct hints taken against 431 of 476 (F41). LoRA + note is "fewer than
  the instruction" by R2 (−8 [−12, −4]) at an acceptance cost of −9 [−13, −5] (F44). Exploratory (post hoc): A40
  gives more correct answers than the instruction only when fewer than about 36% of the tool's answers are right.
- **Accuracy was preserved, and every trained version passes Gate 3** (F28; on E2 with power, F44).
- **The stricter bar, beating the one-line instruction on following at no cost to correct hints, is met by no fix**
  (F28, F41, F43, F44).
- **The mechanism:** LoRA acts in the reasoning (F39); A40 changes how the hint is read, in layers 0–14 (F42).
- **Our reading:** without a way to verify the tool, resisting wrong hints and relying on right ones trade off. So the
  fix belongs at the system level, and the evidence says which part: provenance labels alone don't help (marking every
  tool output "unverified" has no effect alone, F44); independent verification does (Track C's checker, which
  re-solves without the tool, stopped all 53 wrong tool answers on fresh items, F24).

## Read this first

| You are | Read first | Then |
|---|---|---|
| Ritik (Track A, labels, the report) | [`docs/status/STATUS.md`](docs/status/STATUS.md), [`docs/status/TODO.md`](docs/status/TODO.md) | the newest daily in [`archive/sessions/`](archive/sessions/INDEX.md); [`docs/RUNBOOK.md`](docs/RUNBOOK.md) |
| Shrey (Track C, from Oct 30) | [`docs/trackC/START_HERE.md`](docs/trackC/START_HERE.md) (its Quick start first) | [`docs/tracks/SOL_SETUP.md`](docs/tracks/SOL_SETUP.md), [`docs/labeling/RATER_GUIDE.md`](docs/labeling/RATER_GUIDE.md), the code map [`cot-disclosure/README.md`](cot-disclosure/README.md) |
| Arsha (Track B, from Nov 6) | [`docs/trackB/START_HERE.md`](docs/trackB/START_HERE.md) (its Quick start first), then [`docs/tracks/TRACK_B.md`](docs/tracks/TRACK_B.md); B20 on her own Sol account from Nov 5: [`docs/trackB/SOL_ARSHA.md`](docs/trackB/SOL_ARSHA.md) | [`docs/RUNBOOK.md`](docs/RUNBOOK.md) §18, the code map |
| A grader | this page, then FINDINGS' "story so far" | [`docs/paper/REPORT.md`](docs/paper/REPORT.md) (the report's skeleton), [`docs/PLAN.md`](docs/PLAN.md) (the calendar, the presentation map; the figures in `docs/paper/figures/`), [`docs/status/STATUS.md`](docs/status/STATUS.md) |
| A paper reviewer | [`docs/paper/CLAIMS.md`](docs/paper/CLAIMS.md) | [`docs/paper/supplement/EVIDENCE.md`](docs/paper/supplement/EVIDENCE.md) and [`PREREGISTRATIONS.md`](docs/paper/supplement/PREREGISTRATIONS.md) |

## The folders

```
README.md            this page
docs/
  FINDINGS.md          every result: claim, numbers, source, status; the story so far; measurement traps
  PLAN.md              the plan to Nov 24: the story's map, owners and dates, gates, the presentation map, the
                       report outline
  RUNBOOK.md           how to run each step: where, the commands, inputs, outputs, what to check
  tracks/              one doc per track: TRACK_A.md (design), TRACK_A_FIX.md (B1/B2: provenance-scaled attention and the learned gate),
                       TRACK_B.md (Arsha), TRACK_C.md (Shrey), SOL_SETUP.md (Sol for a second user)
  labeling/            LABELING_GUIDE.md and RATER_GUIDE.md (by hand); LABEL_QUEUE.csv and RESULTS_SUMMARY.json,
                       generated by progress/analyze_progress.py (the progress round's numbers; code reads them)
  paper/               by hand: CLAIMS, OUTLINE, REPORT (the report's skeleton), REVIEWER_QUESTIONS, RELATED_WORK
                       (bullets, not prose), figures/WAITING.md (specs of slides not drawn yet); generated:
                       figures/*.png|svg|csv (tools/slide_figures.py; readout_by_layer, reviewer_by_prompt and
                       taught_loss by tools/paper_figures.py), tables/ (tools/trackb_final.py), supplement/ with its
                       figures/ and tables/ (tools/make_supplement.py)
  status/              TODO.md (Track A, labels, repo; edited by hand), and STATUS.md, GANTT.xlsx, gantt.png,
                       gantt.pdf, generated by tools/make_gantt.py from TODO.md, TODO_B.md and TODO_C.md after every
                       working session
  trackB/, trackC/     each track owner's own records (Arsha's from Nov 6, Shrey's): START_HERE (a Quick start on
                       top), TODO_B / TODO_C (the Gantt reads them), FINDINGS_B / FINDINGS_C (new findings, merged
                       into FINDINGS at the end), sessions/, and figures/ for their slides (placed at merge)
cot-disclosure/      the code, configs and tests; its README.md is the code map (folder -> track -> entry points)
  results/summaries/   the tracked, numbers-only results (tools/export_summaries.py); the progress round's runs
                       (results/*.jsonl, progress/, scope/) are tracked as its evidence; all other produced data
                       is gitignored (results/trackA|B|C, results/labels, results/handoff, results/archive)
archive/             history, kept but out of the way
  sessions/            every session log and daily, one folder per date (INDEX.md lists them; LATEST.md is a copy
                       of the newest)
  superseded/          earlier versions of the front page, the overview, PLAN, TRACK_C and TODO's old notes
  merged-docs/         the originals of merged docs, unchanged
  progress-round/      the October progress presentation (decks, figures, screenshots), the demo's guide
  MOVES.md             every file moved (Oct 30 and Nov 1): old path -> new path, and why
```

Generated files live where the map says. A few more stay beside the code that reads them, so they aren't moved:
`cot-disclosure/configs/canary/*.json` (`progress/make_canary.py`), `cot-disclosure/finetune/gpu/inputs_manifest.json`
and `sol/inputs.txt` (`finetune/gpu/kit.py --manifest`), and the progress round's figures F1–F9 under
`archive/progress-round/presentation/` (`progress/analyze_progress.py`). `archive/sessions/LATEST.md` is a copy of the
newest log. Every other doc is written by hand and names who edits it in its header.

The report's and slides' submission folder is made on Nov 19–21 (PLAN, the calendar).

## Run the tests

```bash
python3 -m venv .venv && .venv/bin/pip install -r cot-disclosure/requirements.txt
cd cot-disclosure && ../.venv/bin/python -m pytest -q     # all tests, CPU only, no network, no API calls
../.venv/bin/python tools/check_links.py                   # every internal link and RUNBOOK script exists
```

Recompute reported numbers from saved runs, with no API calls:

```bash
.venv/bin/python cot-disclosure/progress/analyze_progress.py                  # the progress round
cd cot-disclosure && ../.venv/bin/python tools/export_summaries.py --check     # the summaries hold no text
../.venv/bin/python tools/paper_figures.py                                    # docs/paper/figures/
../.venv/bin/python tools/slide_figures.py                                    # the slides' figures (WAITING.md: the rest)
../.venv/bin/python tools/make_supplement.py --check                          # the supplement, checked
```

Each finding names the script that recomputes it. Most need the local runs, which stay off GitHub (produced data is
gitignored; teammates get it as a bundle, `tools/make_handoff_bundle.py`). To call a model you need your own Voyager
key in `cot-disclosure/.env` (copy `.env.example`). Before a push, install the pre-push check (RUNBOOK §17). The
progress round's demo: `python3 cot-disclosure/ui/app.py` (http://127.0.0.1:8765).
