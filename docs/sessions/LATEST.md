# Session log: catch-up on the whole project (2026-10-27 10:10 MST)

Project: CSE 598 Group 10, "Do thinking modes make chain-of-thought more honest?" A wrong hint
(from the user or from a tool) is added to multiple-choice questions; we measure whether the answer
follows it and whether the model says so. Track A (Ritik) explains and fixes it in Olmo 3 7B Think;
Track B (Arsha) tests more models and providers; Track C (Shrey) tests a solver-reviewer-checker
agent team. Models run on ASU Voyager (an API) and ASU Sol (GPUs).

## 1. Header

- **Time:** 2026-10-27 10:10 MST (Arizona) = 17:10 UTC. Week 11 of 16.
- **Branch:** `trackA-nosol` (local only; never pushed beyond `main`'s commit).
- **Commits:** before this session's work `f96f917`; after `2a8fc1c` (3 commits: `07999f7` Step 9
  matched onsets, `39f8534` Sol Python path, `2a8fc1c` docs). This log is committed on top.
- **Tests:** 283 of 283 pass (CPU only, no network).
- **Steps 6–7 run** (Voyager, pid 12290, running 1 day 21.5 h): 473 questions run, 227 kept of the
  240 target; second-to-last batch at 70 of 120 no-hint runs. Expected finish 2–4 PM MST today, if
  the Mac stays plugged in with the lid open (it slept 11:35 PM–8:28 AM and lost ~9 h).

## 2. What ran

| Command | Where | Calls / GPU | Duration | Failures |
|---|---|---|---|---|
| `finetune/look/attn_to_hint.py --followup` (matched onsets; Ritik's run) | Sol job, CPU only | 0 GPU min | ~1 min | none |
| `attn_to_hint.py --followup --from-reduced results/trackA/gpu/step9_reduced.npz` | Mac | 0 | ~20 s | none |
| Ad hoc checks: share of onsets with a positive rise; placebo (then added to the code) | Mac | 0 | seconds | none |
| `tools/export_summaries.py` | Mac | 0 | seconds | none |
| `pytest -q` (3 times) | Mac | 0 | ~1:45 each | 0 failures |
| `run_steps67.py` state, read only (nothing appended to its report file) | Mac | 0 | seconds | none |
| `untrack_produced.py` (dry run) | Mac | 0 | seconds | nothing changed |
| Steps 6–7 driver (started Oct 25, untouched) | Mac → Voyager | ~1,420 no-hint runs + ~1,270 target samples so far | ongoing | 2 "Voyager unreachable" pauses (both resumed; likely the Mac asleep) |

No Voyager or Sol run was started in this session.

## 3. Results

**Step 9 matched lead onsets (new finding F14, confirmed).** Attention from each reasoning sentence
to the hint (8 full-attention layers, hint minus a same-length control span), around every sentence
after the first fifth where the hint letter becomes the leading forced answer; rise = mean of the
onset sentence and the 2 before, minus the same run's sentences 6–15 before; per run, then a
bootstrap clustered by question.

| Anchor | Onsets (runs, questions) | Rise above 0 | Rise, 95% interval |
|---|---|---|---|
| lasting (the takeover) | 65 (65, 18) | 55 of 65 | +4.8e-3 [+2.7e-3, +7.1e-3] |
| temporary (lost again) | 1,653 (123, 19) | 1,056 of 1,653 | +3.4e-3 [+2.0e-3, +5.3e-3] |
| placebo: other sentences after the first fifth, not within 2 of an onset | 93,005 sentences (199, 20) | — | +0.05e-3 [−0.10e-3, +0.23e-3] |

- Onset minus placebo: lasting +4.7e-3 [+2.7e-3, +7.0e-3] (18 questions); temporary +3.4e-3
  [+2.0e-3, +5.3e-3] (19). Expected: a rise at both if look-backs mark the hint "in play" (F6).
  Matches.
- Lasting − temporary: +1.7e-3 [−0.5e-3, +4.2e-3] (17 questions in both); isolated onsets +1.3e-3
  [−1.5e-3, +3.9e-3] (15). Both include 0: no difference shown.
- Within followed runs: +2.2e-3 [+0.2e-3, +4.5e-3], but isolated +2.2e-3 [−0.3e-3, +4.4e-3]; per
  token both exclude 0 (+8.8e-5 [+1.7e-5, +17.4e-5]; +9.5e-5 [+1.1e-5, +18.2e-5]). Tentative.
- After the onset (descriptive): the takeover's spike stays above its earlier level ~5 sentences
  (+10.3e-3 at 0, +4.8e-3 at +2, back by +6); temporary leads drop back within 2.
- The Mac rerun reproduces Sol's numbers (max relative difference 8e-15) and adds the placebo.

**Refuted:** F10's closest-approach reading ("resisted runs look at the hint more"): matched
temporary leads, followed − resisted −0.7e-3 [−4.2e-3, +2.0e-3] (16 questions). Recorded as trap T9,
the second anchor-selection artifact (the first, Oct 24 analysis 2(a): +50 points built in; matched
−1 point [−16, +19]).

**The Steps 6–7 checkpoint report at 100 kept** (written by the driver Oct 26 10:42 MST; never sent
before, because that session ran out):
- Keep rate 117 of 250 [41, 53%] (pilot 5 of 10).
- A prefill target within 4 samples, wrong / correct hint: user 112 of 117 [90, 98%] / 60 of 61;
  pasted tool 110 of 117 [88, 97%] / 59 of 59; inserted tool 102 of 117 [80, 92%] / 62 of 62. No
  rate off by more than half from the pilot.
- Target length, median (prompt + target tokens): easy puzzles 5,401; hard puzzles 11,342; MMLU-Pro
  4,678; all 7,352; held-out replies 11,988.
- Final-answer stance: "neither" 27 of 533 (5%), under the 10% line, so it will be dropped at
  assembly.
- At 216 kept (Oct 27 09:15): 979 examples, "neither" 49 of 979 (5%); targets within 4 samples:
  wrong hint 208 of 215 (user), 205 of 215 (pasted), 196 of 214 (inserted).

**Audit results (TODO.md):** Gate 1 (Oct 25) not met per the repo: Voyager is the only provider
called, no closed-provider keys, agents on 2 items, `results/trackB/` empty, no Track B/C commits
after Oct 4 (none ever by Arsha). Sol scripts called a bare `python`: now fixed.

**FINDINGS status changes:** F14 added (confirmed; lasting > temporary tentative). F10's
closest-approach part refuted. T9 added. No other number changed.

## 4. Files

| Path | Size | Tracked? | Change |
|---|---|---|---|
| `docs/FINDINGS.md` | 36.7 KB | tracked | F14, T9, F10 retraction, figure plan #5, header date |
| `docs/TODO.md` | 12.7 KB | tracked | new: every open item |
| `docs/RUNBOOK.md` | 20.6 KB | tracked | new: one page per step |
| `docs/PLAN.md`, `docs/OVERVIEW.md` | 19.8, 20.6 KB | tracked | rewritten |
| `README.md`, `cot-disclosure/README.md` | 6.7, 9.8 KB | tracked | refreshed |
| `cot-disclosure/finetune/README.md`, `finetune/gpu/README.md` | 10.4, 25.6 KB | tracked | refreshed |
| `cot-disclosure/finetune/look/attn_to_hint.py` | 57.4 KB | tracked | placebo, rise-above-0 counts |
| `cot-disclosure/finetune/gpu/sol/env.sh`, `run.sh`, `setup_env.sh` | 1.5, 1.1, 1.6 KB | tracked | Python by full path |
| `cot-disclosure/tests/test_trackA_attn.py`, `test_trackA_gpu_kit.py` | 12.1, 11.6 KB | tracked | 2 new tests |
| `cot-disclosure/results/summaries/trackA/step9_followup.json` | 124 KB | tracked | numbers only, with placebo |
| `…/summaries/trackA/step9_onsets.png` / `.svg`, `step9_aligned.png` / `.svg` | 133, 87, 202, 105 KB | tracked | onsets new; aligned re-rendered |
| `cot-disclosure/results/summaries/voyager_canary.jsonl` | 18 KB | tracked | refreshed export |
| `cot-disclosure/results/trackA/gpu/step9_*` | 2.6 MB npz + summaries | gitignored | copied back from Sol by Ritik; the Mac rerun overwrote `step9_followup.json` and the figures (Sol originals kept in the session scratchpad) |
| `docs/sessions/` | this log, `LATEST.md`, `INDEX.md` | tracked | new |

Copied from Sol (by Ritik, Oct 27 ~08:50 MST): `step9_followup.json`, `step9_aligned.*`,
`step9_onsets.*`, `step9_reduced.npz`. Nothing copied to Sol.

## 5. Problems and fixes

- **"Every onset is a look-back" is too strong:** 55 of 65 lasting and 1,056 of 1,653 temporary
  onsets have a positive rise. Recorded as an average, with those counts.
- **Placebo added** so "the rise is onset-specific" rests on a tracked number, not only the shape of
  the curve.
- **Sol scripts used a bare `python`** after `source activate` (`run.sh`, `setup_env.sh`). Fixed:
  `"$TRACKA_PY"`, with a test that refuses any bare `python` / `python3` in a Sol script.
- **The checkpoint report was never delivered** (Oct 26 session ended a minute after it was
  written). Now in this log and TODO.
- **Owners:** Track B is Arsha's and Track C is Shrey's in every doc; the audit agent's brief briefly
  had them swapped (my error), corrected.
- **Docs were stale since Oct 20** (OVERVIEW, PLAN, README, "61 tests", "Sol unconfirmed"): rewritten.

## 6. For review

- **Few questions:** F4, F7, F11 and F13 rest on 9 questions (19–21 cases). F14's isolated-onset
  comparisons use 15–16 questions. The within-reach Step 9 runs (6 questions) are not read.
- **Design that may build in the result (F14):** a lead onset is detected from a forced answer after
  a sentence; a sentence that names the hint letter raises both that forced answer and attention to
  the hint. So "looks back at the hint" may be partly the mention itself. Which comes first isn't
  tested; recorded as an association.
- **F14 lasting vs temporary within followed runs:** temporary leads there all come before the
  takeover, so position in the run differs too.
- **The 960 GPU-minute reading** (two jobs at once ≤ 8 h each) is my reading of the class QoS; not
  checked on Sol (Next, command 2).
- **Deviations from instructions:** you asked to "confirm" the Sol Python path; it wasn't true, so I
  fixed it (code + test) rather than only reporting. The placebo and the rise-above-0 counts are
  additions you didn't ask for. The Mac rerun overwrote Sol's copy of `step9_followup.json` in the
  gitignored folder (identical numbers plus the placebo; original kept).
- **Unsure:** Track B/C call and hour estimates (Haiku and Ollama speeds are assumptions); Gate 1 is
  judged from the repo only (teammates may have unpushed work); the Phase 6 labeling size (200 + up
  to 50) is a proposal.

## 7. Decisions needed from me

1. **Assemble right when Steps 6–7 end?** (a) yes, run `--assemble` (no calls), report the counts,
   then stop; (b) wait for your go first. **Recommend (a).**
2. **History rewrite scope** (`untrack_produced.py --run`, after the run ends): it rewrites the 53
   unpushed commits, untracks `results/trackA/` (61 paths), `finetune/data/` (5) and
   `results/voyager_canary.jsonl`, and moves local `main` and `voyager-ids-oct21` to the rewritten
   commits; files on disk don't move. Track C's `results/scope/` is out of scope (already on GitHub).
   (a) approve as is; (b) change the scope. **Recommend (a).**
3. **The 10 label rows with no text:** (a) regenerate with 10 Voyager calls (the model route changed
   Oct 21 and seeds don't reproduce, so these are new runs of the same prompts); (b) replace them
   with 10 random saved hinted runs that neither mention nor follow the hint (no calls); (c) drop
   them and label 91. **Recommend (b):** it keeps the queue's calibration purpose with no calls.
4. **Optional fourth version** (LoRA on layers 15/19/23 attention, +6–16 GPU h): (a) decide after
   the timing run; (b) yes now; (c) no. **Recommend (a).**
5. **Training settings:** (a) one setting (rank 16, learning rate 2e-4); (b) the rank × learning-rate
   grid (3–6× the training hours). **Recommend (a)**, grid only if the timing run leaves room.
6. **Tracks B and C:** no owner activity in the repo since Oct 4. (a) I write their no-call code
   fixes now (B5 `tool_injected` wiring, C2 no-tool team, C3 reviewer flag, C6 append-only log in a
   gitignored folder, a model flag, an input-file option) and they run on Voyager from Oct 28 with
   your go; (b) leave them to Arsha and Shrey. **Recommend (a)**, after checking with them.
7. **F14 wording:** recorded as "on average; 55 of 65 and 1,056 of 1,653 onsets" rather than "every
   onset". (a) keep; (b) reword. **Recommend (a).**

## 8. Open work (top 10 of docs/TODO.md)

| # | Item | Status |
|---|---|---|
| A1 | Steps 6–7 to 240 kept | in progress: 227 kept, finish 2–4 PM MST |
| A4 | Assemble train / validation, counts, stop | not started (waits on A1) |
| A6 | History rewrite, then push (A7) | not started (waits on A1 + approval) |
| A8 | Step 11 `train.py` + CPU tests | not started |
| A9 | Step 12 tagged generation (own loop + vLLM) | partial |
| A10 | Step 13 `eval.py` | not started |
| A11 | Sol job scripts for Steps 11–13 | not started |
| L2 | Labeling kit (blank sheets, kappa script) | not started |
| L3 | Hand labels, two raters, by Gate 2 (Nov 8) | not started |
| B1/C1 | Track B keys and smoke tests; Track C on 5 items | blocked / not done |

## 9. Next

**You run (nothing is required now):**
1. Mac: keep it plugged in with the lid open until the Steps 6–7 run ends.
2. Sol (any login node; read only): `sacctmgr -P show qos class` and paste the line, to confirm the
   2-job / 960 GPU-minute limits behind the job plan.

**After your reply, I will:** act on decisions 1–7; when Steps 6–7 finish, export the final
summaries, run `--assemble` if decision 1 is (a), and write a log with the final counts and stop for
your go. With your go I'll start the Steps 11–13 code and the labeling kit (no calls) in that order.
