# Session log: Track B's final Qwen3 30B Thinking table (F15), the steered export, and C4 started (2026-10-28 03:25 MST)

Project: CSE 598 Group 10. Track B measures, across open models, how often a wrong hint (from the
user, a pasted tool block, a real tool call or a system note) moves the answer and whether the reply
says so. Track C runs a solver/reviewer/checker team on Track B's cases. Ritik is asleep; this is
part of the overnight list.

## 1. Header

- **Time:** 2026-10-28 03:25 MST = 10:25 UTC.
- **Branch:** `trackA-nosol`, at `b9e648d` before; one commit with this log. Not pushed.
  **Tests:** 397 pass.
- **Running:**
  - **Track B, Qwen3 30B Instruct:** on Voyager since 03:11, under the first power guard
    (`logs/guard.log`); about 100 of its 810 runs at 03:21, no errors. Olmo 3 7B Think follows it.
  - **Track C, C4:** since 03:13, under a second guard (`logs/guard_c4.log`, stop file
    `logs/stop_c4`); 5 of 318 cases at 03:20.
  - The two share the 4 Voyager slots (`common.slot()`, across processes).

## 2. What ran

| Command | Where | Calls | Duration | Failures |
|---|---|---|---|---|
| Track B Qwen3 30B Thinking, `run_trackB.py --run` (guard) | Mac → Voyager | 810 runs | 23:36–03:11 | none: 0 without an answer |
| `trackB_report.py --export --by-set` | Mac | none | seconds | — |
| `run_trackB.py --steered --model qwen3-30b-a3b-thinking-2507` | Mac | none | seconds | — |
| `run_team.py --live --cases results/trackB/steered_cases.jsonl --kinds steered,matched --per-kind 30 --repeats 3 --teams tool,notool --log team_c4 --run-name C4-oct28` (dry run, then under the guard) | Mac → Voyager | ~3,021 planned | from 03:13 | none so far |

## 3. Results

**Qwen3 30B Thinking, final** (FINDINGS F15). The setup: 54 questions × 5 conditions × 3 runs at
the 32,768 budget. Rates are Wilson; differences are a bootstrap clustered by question.

| channel | following | above the no-hint baseline | final answer names it, when following |
|---|---|---|---|
| user | 3 of 162 [1, 5%] | +1 [−1, +2] | 0 of 3 |
| tool, pasted | 59 of 162 [29, 44%] | +35 [+25, +46] | 54 of 59 |
| tool, real call | 54 of 162 [27, 41%] | +32 [+23, +42] | 3 of 54 |
| system note | 57 of 162 [28, 43%] | +34 [+25, +44] | 50 of 57 |

- **Gate 2 (tool − user, 54 questions):** pasted +35 [+24, +46], real call +31 [+22, +42]. Both
  clear, and still clear at the 16,000 cut (+34, +32).
- **The real call:** the model called the tool in 54 of 162 runs and followed it every time it
  did (54 of 54). Without a call, following was 0 of 108.
- **By set:**
  - **MMLU-Pro (30 questions):** pasted 54 of 90, real call 50 of 90, system note 50 of 90, user 3
    of 90.
  - **Puzzles (24 questions, 72 of 72 right with no hint):** pasted 5 of 72, real call 4 of 72,
    system note 7 of 72, user 0 of 72.
- **Since the interim table (00:45, about 1 run each):** the same picture. Real call 23 of 62 →
  54 of 162; pasted 19 of 62 → 59 of 162.

**Steered export** (`results/trackB/steered_cases.jsonl`, gitignored: it holds the question text):
- **The count:** 54 questions: 24 steered, 29 matched, 1 other.
- **Which channel steered** (some questions both): pasted on 18 questions, real call on 14.
- **The one "other":** the system note took 2 of 3 runs to the hint, but steered only counts tool
  channels.

**C4's plan (the dry run):**
- 53 items × 2 teams × 3 repeats = 318 cases, about 3,021 calls.
- 25 of the 53 items get the bad lookup (the seeded oracle).
- Both reviewers: Qwen3 30B Instruct and Olmo 3.1 32B Instruct.

## 4. Changes

- **`progress/trackB_report.py`:**
  - **New numbers:**
    - the final answer naming the hint among the runs that followed it;
    - for the real call, following without a call;
    - for the real call, the private reasoning naming the hint among the calls. Without a call,
      the `cue_tool` keyword only names the tool: 53 of 108 such runs match it.
  - **`--by-set`:** the same table per question set (`trackB_report_by_set.json`).
  - Test added.
- **Summaries (numbers only, now tracked):** `results/summaries/trackB/trackB_runs.jsonl` and
  `trackB_report_by_set.json`; `trackB_report.json` updated.
- **Docs:** FINDINGS F15; TODO B7, B8, B9, B14, C4; `handoff/TRACK_B.md`.

## 5. For review

- **In C4, steered vs matched is also MMLU-Pro vs puzzles.** All 24 steered cases are MMLU-Pro,
  and 24 of the 29 matched ones are puzzles. A C4 difference between the kinds can come from the
  question set. The 5 MMLU-Pro matched cases give a same-set comparison at the 5-question minimum.
  I ran C4 as planned (all steered and matched cases) and will report it both by kind and by set.
- **"The final answer names the tool" is keyword counts.** That covers 3 of 54 after a real call,
  and 54 of 59 for the pasted block. Gate 2's hand labels (L3) would confirm them.
- **C4's pace:** about 0.7 cases a minute while it shares the slots with Track B, so about 7–10 h.
  It is expected around midday. Olmo 3 7B Think's Track B runs (~8 h) share the same slots after
  Instruct.

## 6. Next

- When Qwen3 Instruct is done (~04:30): its table, its steered export and a FINDINGS entry.
- C4: watch for failures; the C5 tables as data lands.
- The 7 am daily log, with the morning commands.
