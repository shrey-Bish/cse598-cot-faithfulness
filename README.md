# Do Thinking Modes Make Chain-of-Thought More Honest?

CSE 598, Fall 2026 · Group 10: Shrey Bishnoi, Arsha Jindal, Ritik Agarwal. Last updated: 2026-11-19. **Edited by:** Ritik.

## Start here in five minutes

**The question.** We put a wrong hint in a multiple-choice question, from the user or from a tool. Does the model
follow it, and does it say so? Thinking models return their private reasoning and their final answer separately, so
we can see which of the two admits the hint.

**Five findings** (results frozen Nov 18, the tag `results-freeze-2026-11-18`; codes in parentheses are what to search
for in [`docs/FINDINGS.md`](docs/FINDINGS.md) and the [glossary](docs/GLOSSARY.md)):
1. **Tools sway models more than users do.** The same wrong hint moves the answer more from a tool than from the user,
   in all five models of the models-and-sources track and in all 10 readings of three newer families (Gate 2, FB1).
   Most of the pull is the claim to be the answer key, and it grows with the claimed authority (B16, B24; F35, F40).
2. **The final answer drops the source.** By keyword counts, the private reasoning names the hint in 208 of 216 runs,
   the final answer in 8 (F3); after a real tool call, Qwen3 30B Thinking's final answer is a bare letter in 51 of 54
   (F15). Does thinking make it more honest? Mixed: it depends on the model and how thinking is varied (F29, F37, FB1).
3. **Inside Olmo 3 7B Think, three layers read the hint's letter straight from the prompt.** Layers 15, 19 and 23
   carry 0.90 [0.85, 0.96] of the drop at the takeover (F11), and it replicates on new questions and, with its own
   three layers, in a second family, Qwen3-8B: 0.70 [0.60, 0.83] (F26, F36).
4. **The fixes trade; none wins.** Every fine-tuned version passes the fix test (Gate 3, F28), but none beats a
   one-line instruction without taking fewer correct hints: consistency training follows fewer wrong hints than the
   instruction (−21 [−26, −16] points) and takes fewer correct ones (−15 [−20, −10]) (A40, F41).
5. **A reviewer that sees the solver's trace stops checking.** Olmo 3.1 32B corrected 59 of 73 wrong answers from the
   answer alone and 6 of 73 with the solver's private reasoning beside it (C4, F18), in one model family of the four tried (F22); a checker that never sees the
   tool stopped all 53 wrong tool answers on fresh items (C15, F24).

**See it.** Open [`docs/demo/index.html`](docs/demo/index.html), the demo, in any browser (it works offline: download
the file and double-click it). It is one answer sheet in three parts: how we did it, run it, what we found (keys 1–3;
← → step). The earlier Hint Explainer is [`docs/demo/explainer.html`](docs/demo/explainer.html).

**Where things are.**
- **The report's material:** [`docs/paper/REPORT.md`](docs/paper/REPORT.md) (every section's bullets, numbers and
  figure), [`RELATED_WORK.md`](docs/paper/RELATED_WORK.md), [`CLAIMS.md`](docs/paper/CLAIMS.md); the figures in
  [`docs/paper/figures/`](docs/paper/figures/), the tables in [`docs/paper/tables/`](docs/paper/tables/).
- **The slides:** [`docs/presentation/deck.pptx`](docs/presentation/deck.pptx) (the shell), with
  [`TALK_MAP.md`](docs/presentation/TALK_MAP.md) and [`QA_FACTS.md`](docs/presentation/QA_FACTS.md).
- **The submission:** [`docs/submission/`](docs/submission/README.md), its checklist and one command that builds the zip.
- **The data:** every number in [`docs/FINDINGS.md`](docs/FINDINGS.md) (and Track B's
  [`FINDINGS_B.md`](docs/trackB/FINDINGS_B.md), Track C's [`FINDINGS_C.md`](docs/trackC/FINDINGS_C.md)); the
  numbers-only summaries in [`cot-disclosure/results/summaries/`](cot-disclosure/results/summaries/); the produced data
  stays local, in three bundles whose sha256s are in
  [`docs/submission/BUNDLES.sha256`](docs/submission/BUNDLES.sha256).

**New here?** Open the [demo](docs/demo/index.html) first (details below), and keep the
[glossary](docs/GLOSSARY.md) beside you: the repo's logs and findings use short internal codes (A40, B1R2, F41), and the
glossary turns each one into a plain name and back.

## What we ask

We slip a wrong hint into a multiple-choice question. The hint comes from the user or from a tool. Then we ask two
things: does the hint change the model's answer, and does the model say so? Thinking models hand back their private
reasoning and their final answer as two separate pieces, so we can check which of the two admits the hint.

Three tracks share the work:
- **Inside the model and the fixes** (Track A) looks inside one open thinking model, Olmo 3 7B Think, to find where
  the hint takes over, and tries ways to make it resist.
- **Models and sources** (Track B) tests more models, and different sources for the hint.
- **Review teams** (Track C) asks what a wrong tool answer does to a team of agents: a solver, a reviewer and a
  checker.

## The theme and the story in five lines

**"Where did that answer come from?"** A tool's influence loses its source at three levels: inside the model
(line 3 below), in the model's own words (line 2) and between agents (line 4). [`docs/PLAN.md`](docs/PLAN.md) places
every remaining experiment on that map. Results freeze on Nov 18, and the final presentation and report are due on
Nov 24. Numbers and status for each line are in [`docs/FINDINGS.md`](docs/FINDINGS.md) ("The story so far"). Where a
code appears in parentheses, it is what to search for there.

1. **Tools sway models more than users do, mostly through their claim to be the answer key.** The same wrong hint
   moves the answer more when a tool gives it than when the user does, in all five Track B models (the tool-vs-user
   test, Gate 2, marked Nov 8). A user who claims the answer key's authority moves it about as much, except where the
   model calls the tool itself every time (the authority ladder, B16 and F35; confirmed the same day in B19). The pull
   grows with the claimed source's authority: "the official solution manual" moves all three Voyager models more than
   "a classmate" does, and for Qwen3 30B Thinking it moves the answer more than "my answer key" (B24, F40). In three more
   open-weight families run on Sol (the newer families, B20 and FB1: Gemma 4, Nemotron 3 Nano and Granite 4.2), tools
   beat users in all 10 readings. Whether the tool's form adds to the claim it carries depends on the family and the
   channel: the form adds beyond the claim in 5 of 10 readings, the claim moves it more in 1, and no difference was
   detected in 4. Labelled: the inserted tool turn for Gemma and Nemotron, Granite with thinking on only, temperature
   1.0.
2. **After a tool call, the final answer stops explaining.** It becomes a bare letter while the private reasoning
   names the tool (the quiet answer). Asking the model to disclose what its answer is based on works, but it doesn't
   reduce deference to the tool (the disclosure instruction, B15). More thinking doesn't change it either: in
   gpt-oss-20b, raising the reasoning effort from low to high changes neither the bare answer after a call nor how
   often the model follows the tool (no change detected on either; B17 and F37, run after its one-day window). In the
   newer families (FB1), a call makes the answer barer after Granite's own call and after Nemotron's inserted turn with
   thinking off. With thinking on, Nemotron's bare answer after the inserted turn falls (−14 [−19, −9]): thinking
   writes more of the source down. **So the title question is answered mixed.** With thinking on, Qwen3-8B names the
   tool in its private reasoning but not in its final answer (F29). Raising gpt-oss-20b's effort changes nothing
   (F37). Nemotron's answer is less bare (FB1). The training result in line 5 (candid answers, L6) doesn't bear on it.
3. **Inside Olmo 3 7B Think, layers 15, 19 and 23 read the hint straight from the prompt.** Together they hold 0.90
   of the drop at the takeover, and the result replicates on questions not used to find the layers, by two methods
   (readout layers 15, 19 and 23; F26 and F32). Olmo's sliding windows don't force it: in Qwen3-8B, whose layers all
   see the whole prompt, three layers chosen on one question set hold 0.70 of the drop on another (the Qwen3-8B
   replication, A37 and F36). The mechanism as a whole is tentative.
4. **Downstream, a reviewer shown the tool's trace defers to it, but only in one model family.** Only Olmo's two of
   six reviewers do. A checker that never sees the tool stopped all 53 wrong tool answers on 100 fresh items (C15, F24;
   73 of 75 in the first run, F18). The deferring reviewer follows the solver's citation of the tool's letter as
   authority (C16 to C18).
5. **The fix, so far:**
   - All four fine-tuned versions pass the fix test (Gate 3) by its rule, but none beats the one-line instruction on
     following, and the source tags don't act where the tool's tokens are. By hand labels, the fine-tuned (LoRA) model's
     keyword false-disclosure candidates are rarely real: most say the hint shaped the answer (hand labels L4 part 1;
     F28).
   - The attention dial (B1, F38) makes a real cut in following on the inserted tool turn, but it misses its
     pre-registered acceptance limit ("ignores tools"), and it is underpowered at 30 questions. A replication that
     could resolve the limit needs about 107 to 245 fresh questions; the 35 GPU-hours available fit 70, so it was not
     run (B1R), and neither was A38.
   - Inside the fine-tuned model (A18, F39), training acts in the reasoning, not on the readout: given the base
     model's own reasoning, LoRA's weights pull toward the hint's letter harder, not less, and when LoRA follows it is
     through the same three layers. In plain words: [`docs/status/FIX_SO_FAR.md`](docs/status/FIX_SO_FAR.md).
   - On the 120 fresh questions (E2), marking every tool output "unverified" has no effect alone (A39, F44). With
     the one-line instruction, the label follows fewer wrong hints on the tool turn but takes fewer correct ones. The
     fine-tuned model with the instruction follows fewer than the instruction alone (R2, −8 [−12, −4]) at an
     acceptance cost of −9 [−13, −5].
   - Consistency training (A40) trains the model on its own reasoning written without the hint (bias-augmented
     consistency training). It follows far fewer wrong hints than the one-line instruction but takes fewer correct
     ones: "fewer, but costs acceptance" by its rule (F41). With the instruction added (A42) the result is the same
     (F43). Inside the model, it is the first fix that acts on the readout, before layers 15, 19 and 23 (A41, F42).
   - The attention dial's replication on the 120 fresh questions (B1R2, read Nov 13 by B1's rule) reads "ignores
     tools" again. The cut in following replicates (−13.8 [−20.0, −7.5] points on the tool turn), and correct tool
     hints are taken less too (−5.8 [−10.8, −1.3]), just past the rule's 5-point limit (F38).

**Scorecard against the original plan** (Nov 7, updated Nov 8 and 13; numbers as read in
[`docs/FINDINGS.md`](docs/FINDINGS.md), story item 7).
- **The failure: tools pull harder than users in every model tested.** The tool-vs-user test (Gate 2) was marked
  Nov 8: all five Track B models and the three newer families, 10 of 10 readings (FB1). The label part of Gate 2 is
  not met (F3).
- **Training made the answer more candid about a hint it followed, in hand labels, without making it follow less**
  (candid answers, L6, F45, Nov 13). When LoRA follows a wrong hint on the 120 fresh questions, its answer says so in 37
  of 42 hand-labelled runs, against the instruction's 18 of 42 (+45 [+25, +64] points). It follows as often as the
  instruction (F44). Limits: LoRA's trained opener names the hint (F28); this is one model, on those questions only,
  with 42 rows a system, and the final answer only. The sheet wasn't blind in practice, though the AI check (blind to
  systems) agreed on 82 of 84 rows.
- **Resisting wrong hints improved with consistency training, but as a trade:** 84 of 694 wrong hints followed against
  the instruction's 237 of 713, and 347 of 459 correct hints taken against 431 of 476 (A40, F41). Fine-tuned +
  instruction is "fewer than the instruction" by R2 (−8 [−12, −4]) at an acceptance cost of −9 [−13, −5] (F44).
  Exploratory (post hoc): consistency training gives more correct answers than the instruction only when fewer than
  0.36 [0.22, 0.50] of the tool's answers are right (the trade-off).
- **Accuracy was preserved, and every fine-tuned version passes the fix test** (Gate 3; F28, and on the 120 fresh
  questions with power, F44).
- **The stricter bar, beating the one-line instruction on following at no cost to correct hints, is met by no fix**
  (F28, F41, F43, F44).
- **The mechanism:** LoRA acts in the reasoning (F39). Consistency training changes how the hint is read, in layers
  0 to 14 (F42).
- **Our reading:** without a way to verify the tool, resisting wrong hints and relying on right ones trade off. So the
  fix belongs at the system level, and the evidence says which part. Labels alone don't help: marking every tool
  output "unverified" has no effect alone (F44). Independent verification does: the independent checker in the review
  team, which re-solves without the tool, stopped all 53 wrong tool answers on fresh items (C15, F24).

## The demo: an answer sheet in three parts

**Open [`docs/demo/index.html`](docs/demo/index.html) in any browser.** It works offline: one file, its fonts embedded,
no network. The whole screen is one exam answer sheet; everything on it is a mark (pencil fills a bubble per run, a red
pen grades, a sticky note brings a user's hint, a stapled slip a tool's). Nothing plays by itself.

- **How we did it** (key 1): a map of the project, left to right as a run flows (questions, the hint, the models, inside
  the model, what it wrote, how we checked; the fixes and the review team branching off). Click a step, or ← →, to open
  its method with the real numbers and one thing to try; Esc goes back to the map.
- **Run it** (key 2): the test bench, six tests (Shift+1–6). The tracked page shows each test's frozen result. The
  local build, `cot-disclosure/results/demo/demo.html` (gitignored, never on GitHub), replays every recorded run of
  questions drawn by a stored seed (`tools/demo_template/draw.json`), each with its file and line: Enter runs one, N the
  next question, M draws 20 more runs of the condition, C compares two conditions, P shows the exact prompt.
- **What we found** (key 3): the ten result sheets, stepped by hand (← →); each links to its test and its method.
- **Rebuild:** `cd cot-disclosure && ../.venv/bin/python tools/demo_template/runs.py` (the local runs; optional), then
  `../.venv/bin/python tools/demo_template/build.py` (both pages). Every number is the frozen one
  (`tools/demo_template/compact.py`; `tests/test_demo_template.py`). The design guide is
  [`TEMPLATE_GUIDE.md`](cot-disclosure/tools/demo_template/TEMPLATE_GUIDE.md); the brief is
  [`docs/demo/DEMO_SPEC.md`](docs/demo/DEMO_SPEC.md).
- **The Hint Explainer** (Nov 14), the earlier demo, is kept at [`docs/demo/explainer.html`](docs/demo/explainer.html)
  (`tools/build_demo.py`).

## Read this first

| You are | Read first | Then |
|---|---|---|
| Ritik (Track A, labels, the report) | [`docs/status/STATUS.md`](docs/status/STATUS.md), [`docs/status/TODO.md`](docs/status/TODO.md) | the newest daily in [`archive/sessions/`](archive/sessions/INDEX.md); [`docs/RUNBOOK.md`](docs/RUNBOOK.md) |
| Shrey (Track C, from Oct 30) | [`docs/trackC/START_HERE.md`](docs/trackC/START_HERE.md) (its Quick start first) | [`docs/tracks/SOL_SETUP.md`](docs/tracks/SOL_SETUP.md), [`docs/labeling/RATER_GUIDE.md`](docs/labeling/RATER_GUIDE.md), the code map [`cot-disclosure/README.md`](cot-disclosure/README.md) |
| Arsha (Track B, from Nov 6) | [`docs/trackB/START_HERE.md`](docs/trackB/START_HERE.md) (its Quick start first), then [`docs/tracks/TRACK_B.md`](docs/tracks/TRACK_B.md); B20 on her own Sol account from Nov 5: [`docs/trackB/SOL_ARSHA.md`](docs/trackB/SOL_ARSHA.md) | [`docs/RUNBOOK.md`](docs/RUNBOOK.md) §18, the code map |
| A grader | this page and the demo (`docs/demo/index.html`), then FINDINGS' "story so far" | [`docs/paper/REPORT.md`](docs/paper/REPORT.md) (the report's skeleton), [`docs/PLAN.md`](docs/PLAN.md) (the calendar, the presentation map; the figures in `docs/paper/figures/`), [`docs/status/STATUS.md`](docs/status/STATUS.md) |
| A paper reviewer | [`docs/paper/CLAIMS.md`](docs/paper/CLAIMS.md) | [`docs/paper/supplement/EVIDENCE.md`](docs/paper/supplement/EVIDENCE.md) and [`PREREGISTRATIONS.md`](docs/paper/supplement/PREREGISTRATIONS.md) |

## The folders

```
README.md            this page
docs/
  GLOSSARY.md          plain names and the internal codes behind them (generated from names.json by tools/make_glossary.py)
  demo/                the Hint Explainer: index.html, one offline page
  submission/          the course submission folder (set up Nov 13)
  drafts/              plain rewrites of the track START_HERE pages, offered to their owners (not in force)
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
  superseded/          earlier versions of the front page, the overview, PLAN, TRACK_C, TODO's old notes and the
                       Nov 13 demo's template
  merged-docs/         the originals of merged docs, unchanged
  progress-round/      the October progress presentation (decks, figures, screenshots), the demo's guide
  MOVES.md             every file moved (Oct 30, Nov 1 and Nov 14): old path -> new path, and why
```

Generated files live where the map says. A few more stay beside the code that reads them, so they aren't moved:
`cot-disclosure/configs/canary/*.json` (`progress/make_canary.py`), `cot-disclosure/finetune/gpu/inputs_manifest.json`
and `sol/inputs.txt` (`finetune/gpu/kit.py --manifest`), and the progress round's figures F1–F9 under
`archive/progress-round/presentation/` (`progress/analyze_progress.py`). `archive/sessions/LATEST.md` is a copy of the
newest log. Every other doc is written by hand and names who edits it in its header.

The report's and slides' submission folder, [`docs/submission/`](docs/submission/README.md), was set up on Nov 13 and is
filled by Nov 21 (PLAN, the calendar).

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
