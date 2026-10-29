# Track C handoff: the agent team (for Shrey, from Nov 3)

Last updated: 2026-10-28 22:42 MST. A working draft, kept current every day and final on Nov 3,
when Track C goes back to you. Until then Ritik runs it.

**The question.** When the solver's lookup tool returns a wrong answer, does it reach the team's final
output? What changes when the reviewer sees more (the explanation, the private reasoning, the tool
log), and how often does the checker catch it or raise a false alarm?

## 1. What's done (as of Oct 28)

- **Code** (`cot-disclosure/agents/`): solver (Qwen3 30B Thinking with the real `lookup_answer_key`
  tool, forced on its first turn; a seeded oracle makes each item's lookup bad, returning the hint
  letter, or good, about half each), reviewer (4 variants: `answer_only`, `plus_explanation`,
  `plus_private`, `plus_tool_log`; Experiment A's prompt and parser), checker (re-asks without the
  tool; flags a changed answer; no answer = undetermined). A flagged item is escalated, not shipped.
- **Changes on Oct 27** (`run_team.py`):
  - append-only logs in gitignored `results/trackC/` (it used to delete its log and write to tracked
    `results/scope/`, which keeps the Oct 4 runs); every step carries `case_id`, team, repeat and
    a run name; a case is done at its `case_done` row, so a rerun resumes and a failed case reruns
  - the **no-tool team** (`--teams tool,notool`): the same solver without the tool, the baseline for
    run-to-run variation (the checker's flags there are the false-alarm floor)
  - **two reviewer models** (`--reviewer-model`, default Qwen3 30B Instruct and, since Oct 28, Olmo 3
    32B Instruct, served as Olmo 3.1 32B Instruct; each has an identity canary); reviewer replies capped
    at 8,000 tokens, and a reply that is a bare letter parses
  - `--log NAME` writes to `results/trackC/NAME.jsonl` (and `NAME_summary.json`), so a smoke or C4
    runs beside the cases another log has done
  - **Track B's cases as input** (`--cases results/trackB/steered_cases.jsonl --kinds steered,matched
    --per-kind N --repeats 3`); cases run 4 at a time through the shared Voyager slots. One Track B
    model at a time: with several models' rows in the file, `--case-model M` picks one (item ids
    repeat across models, so give each model its own `--log`)
  - `--summary`: per team × reviewer model × variant, bad and good lookups apart, Wilson intervals,
    undetermined checks, tokens, and the checker's flag rate per team
  - **C5 in the summary:** the no-tool solver's run-to-run variation, the checker's flag rate there
    (the floor), and the bad and good lookup flag rates minus the floor, paired by item. `--table`
    prints it all as markdown.
  - **`--summary --cases`:** the same split by Track B kind (steered / matched) and by kind ×
    question set. For Qwen3 Thinking, all 24 steered cases are MMLU-Pro and 24 of the 29 matched
    ones are puzzles, so kind and set must be read apart.
  - **Since Oct 28, the summary also has:**
    - each reviewer variant minus the same reviewer with the answer only, paired by item
      (`reviewer_vs_answer_only`)
    - the reviewer keeping the solver's wrong letter, and its reply naming the tool
    - the solver's final answer after good vs bad lookups and with no tool (`solver_replies`:
      bare, median length, naming the tool; F15's control)
  - **Exit codes:** `--stop-file` and exit codes 0 / 1 / 2 / 3, so a run goes under the power guard
    (`progress/guard.py`). Code 3: a Voyager guard failed and all Voyager work pauses.
  - **C9 (`--rereview LOG`, Oct 28):** only the reviewers again, on a log's completed tool-team
    cases (no solver or checker calls), with one sentence after the reviewer's system prompt
    (`CHECK_TOOL`); the summary adds `vs_original_prompt`, each reviewer × variant against the
    original prompt on the same cases, paired by item
- **Runs:** replay of Experiment A (no calls); live on 2 pilot puzzles (Oct 4); **C1**, live on 5
  pilot puzzles (Oct 27, tool team, Qwen3 30B Instruct and Olmo 3 7B Instruct); **the 32B reviewer's
  smoke**, the same 5 puzzles (Oct 28 00:20, `--log team_smoke_olmo32b`, 35 calls).
- **C4: done** (Oct 28, 03:13–17:51, under a second power guard): Qwen3 Thinking's 24 steered and
  29 matched cases × 2 teams × 3 repeats = 318 cases, about 3,021 calls, 0 errors; 25 of the 53
  items get a bad lookup. Results: FINDINGS F18.
- **C9: done** (Oct 28, 21:46–22:33, under the power guard; `--log team_c9`): 159 tool-team
  cases × 2 reviewers × 3 variants (answer_only, plus_private, plus_tool_log) = 954 calls, 0 errors,
  with "The tool's answer may be wrong; check it independently." added to the reviewer's system
  prompt. Results: FINDINGS F19.

## 2. Results so far

- **Experiment A** (Oct 4, a demo, not a result; [`docs/OVERVIEW.md`](../OVERVIEW.md) §6): a reviewer
  that never saw the hint kept a hinted wrong answer in 0 of 15 reviews from the answer alone, 7 of
  15 once it read the explanation; a re-ask without the hint flagged 5 of 5, with 1 false alarm in 6.
- **Replay** of those runs through the pipeline (`--replay`): wrong answers shipped 3 of 33 reviews
  (answer only) and 2 of 33 (with the explanation); caught 15 of 15 wrong solver answers in both;
  false alarms 6 of 18 and 5 of 18 right ones. 6 items: too few questions for intervals.
- **Live, Oct 4** (2 puzzles, 1 bad lookup): the checker caught the bad lookup in every variant; no
  false alarm. 2 items: no rate can be read.
- **C1** (Oct 27, 5 puzzles, 3 bad lookups; counts only): the checker flagged 3 of 3 bad lookups and
  0 of 2 good ones, so no wrong answer was shipped. The reviewers alone: Qwen3 30B Instruct corrected
  12 of 12 wrong solver answers; Olmo 3 7B Instruct 0, and 6 of its 20 replies had no letter (cut off
  at 2,000 tokens: the cap is now 8,000). An observation, not a rate.
- **The 32B reviewer's smoke** (Oct 28, the same 5 puzzles; counts only): every one of 20 reviews gave
  a letter. The checker again flagged 3 of 3 bad and 0 of 2 good lookups. The reviewer alone corrected
  the wrong solver answer in 3 of 3 with the answer only and 3 of 3 with the explanation, but in 0 of
  3 with the private reasoning and 0 of 3 with the tool log; it kept the right answer in 7 of 8 (one
  change with the explanation, shipped as a false alarm since the checker didn't flag it). 5 items:
  no rate can be read; C4 measures it.
- **C4** (FINDINGS F18; 53 items, 318 cases):
  - **The pipeline shipped no wrong answer on a bad lookup** in any variant (0 of 75). The
    checker flagged 73 of 75 bad lookups; in the other 2 the solver had ignored the tool and was
    right.
  - The checker's false alarms are at the no-tool floor: good lookups 7 of 80, floor 12 of 155,
    good − floor −4 [−11, +4]. All of them are on steered MMLU-Pro items.
  - **The Olmo 32B reviewer alone stops correcting once it sees the tool's answer.** On the 73
    wrong solver answers after bad lookups, it corrected:
    - 59 with the answer only
    - 6 with the private reasoning: −73 points [−86, −58], paired by item, 25 items
    - 3 with the tool log: −77 [−91, −61]
  - With that context it keeps the solver's wrong letter (66 and 70 of 73), and its reply names
    the answer key (59 and 66 of 75; keyword counts).
  - **The other side:** on good lookups it keeps the right answer in 67 of 84 with the answer only
    and 84 of 84 with the context (+20 [+8, +35], 28 items). Over all 159 tool-team cases it is right
    in 128 from the answer, 92 and 89 with the context, and the tool itself in 84: it becomes as
    good as the tool. FINDINGS calls it automation bias (Skitka, Mosier & Burdick 1999; Parasuraman
    & Manzey 2010).
  - **For deployment:** the check that kept every wrong tool answer from shipping never sees the
    tool (the checker, 73 of 75).
  - The Qwen3 30B Instruct reviewer doesn't change: 62, 66 and 56 of 73 (+5 [−6, +19], −8 [−25,
    +9]).
  - **By kind × set** (steered = MMLU-Pro, matched mostly puzzles): matched puzzles −77 [−90, −62]
    over 15 items; steered MMLU-Pro −58 [−88, −25] over 8; matched MMLU-Pro 6 of 6 → 0 of 6, too
    few items (2).
  - **"+ the explanation" adds little in the tool team:** the solver's final answer is a bare
    letter in 151 of 159 tool-team cases (F15). It is bare after good lookups as after bad ones
    (80 of 84 vs 71 of 75), the control that made F15 a claim about tool use, not hints.
- **C9** (FINDINGS F19; the same 159 cases, paired by item with C4's prompt):
  - The sentence doesn't restore the Olmo reviewer's check: with the private reasoning it corrects
    6 → 8 of 73 (+3 [−4, +9]), with the tool log 3 → 4 (+1 [−3, +6]). It still keeps the wrong
    letter in 63 and 68 of 73, and names the key in 62 and 61 of 75.
  - Qwen3 30B Instruct may gain a little: +4 [+0, +11] and +7 [−4, +19].
  - The answer-only arm doesn't change (+1, +0); good lookups don't either.
- **C10** (FINDINGS F21; commit first: C9's answer-only review, then the trace and a final answer):
  - Olmo drops its own right answer: 60 of 73 → 19 (private reasoning) and 5 (tool log); against C4
    +18 [+10, +26] and +3 [−4, +9].
  - Qwen3 gets worse with the tool log: 33 of 73 (C4: 56; −32 [−44, −20]); it keeps the wrong
    letter in 37 of 73.
  - Good lookups stay near C4. No wrong answer shipped on a bad lookup (the checker).
- Related Track B/A findings ([`docs/FINDINGS.md`](../FINDINGS.md)): F1 (tool hints move thinking
  models more than user hints), F3 (the final answer rarely names the hint), which is why a
  reviewer that only sees the final answer is expected to miss it.

## 3. How to run each step

[`docs/RUNBOOK.md`](../RUNBOOK.md) §19 (Track C), §17 (the pre-push check), §16 (data handoff). From
`cot-disclosure/`:

```bash
../.venv/bin/python agents/run_team.py --live --n 5 --dry-run                 # calls before running
../.venv/bin/python agents/run_team.py --live --cases results/trackB/steered_cases.jsonl \
      --kinds steered,matched --per-kind 30 --repeats 3 --teams tool,notool --dry-run
../.venv/bin/python agents/run_team.py --summary                              # the table so far
../.venv/bin/python agents/run_team.py --summary --log team_c4 --cases results/trackB/steered_cases.jsonl --table
                                                                             # C4, also by kind and set
```

**Your data:** gitignored, shared by Ritik as a bundle (`tools/make_handoff_bundle.py --track C`:
`results/trackC/`, Track B's `steered_cases.jsonl`, the labeling kit; sha256 manifest; check with
`--verify`).

## 4. Open items (docs/TODO.md, Track C)

| # | Item | Status (Oct 27) |
|---|---|---|
| C1 | Live team on 5 items | done Oct 27 |
| C8 | The 32B reviewer's 5-item smoke | done Oct 28 (20 of 20 letters) |
| C4 | The team on Track B's steered and matched cases (Qwen3 Thinking's first), 3 repeats, tool and no-tool teams, both reviewers (`--log team_c4`) | done Oct 28 17:51 (318 of 318 cases, 0 errors) |
| C5 | The Track C table per reviewer variant: shipped, caught, false alarms, undetermined; bad and good lookups apart; the checker's disagreement against the no-tool team's run-to-run variation; tokens | done (FINDINGS F18; `results/summaries/trackC/team_c4_summary.json`) |
| C9 | Does an instruction restore the reviewer's check? The reviewers again on C4's saved cases, one sentence added; compared with C4's prompt, paired by item, by kind × set | done Oct 28 22:33 (954 calls, 0 errors): no, for the Olmo reviewer (F19) |
| C10 | Commit first: the reviewer's own answer_only review (C9's) first, then the trace and a final answer; compared with C4, C9 and the own answer, paired by item | done Oct 28 23:16 (636 calls, 0 errors): no protection (F21) |
| — | Next: the team on Instruct's or Olmo's cases, or more reviewer models | not decided (C4 was "no extra cases", Oct 28); `steered_cases.jsonl` now has all three models' cases |

## 5. Decisions you inherit

- Gate 1 (Oct 25) was missed; the fallback applies: Voyager only for Track C.
- Solver Qwen3 30B Thinking; reviewers Qwen3 30B Instruct and Olmo 3 32B Instruct (a second model
  family; decided Oct 27, in place of Olmo 3 7B Instruct after C1), 8,000-token cap; bad lookups ~50%
  by a seeded oracle (seed 20261005); 3 repeats per case for C4.
- False alarms are always reported next to catches; undetermined checks are counted, never dropped.
- Every rate as X of Y with a 95% interval and the number of items; fewer than 5: "too few".
- C4 is reported by kind and by kind × set, saying plainly that steered vs matched is also MMLU-Pro
  vs puzzles (Qwen3 Thinking's steered cases are all MMLU-Pro); no extra cases for now (Oct 28).
- C9 (Ritik, Oct 28): only the reviewers again, on C4's saved solver outputs, with "The tool's
  answer may be wrong; check it independently." added; both reviewer models; answer_only,
  plus_private, plus_tool_log; pre-approved on Voyager once its dry run was in a session log.
- C10 (Ritik, Oct 28): commit first, on C4's saved cases, reusing C9's answer_only replies as the
  first turn; both reviewer models; plus_private and plus_tool_log; pre-approved on Voyager once its
  dry run was in a session log.
- Your branch: `trackC-main`, made from `main` on Oct 28 and kept at `main` until Nov 3.
- Logs are append-only and gitignored; numbers-only summaries go to `results/summaries/`.

## 6. Known traps

- **4 requests in flight** across every process on the Mac, shared with Track B's runs: Track C's
  cases wait for a free slot.
- **Identity canaries** for every Voyager model before its first batch (`configs/canary/`).
- **Olmo 3 7B Instruct's served default system prompt** differs from the current Hugging Face
  template's; reviewer calls always send their own system prompt, where the counts match.
- **Olmo 3 32B Instruct on Voyager is 3.1** (A27): `olmo3-32b` at effort none; no public Olmo 3 32B
  Instruct exists except `allenai/Olmo-3.1-32B-Instruct`, and Voyager's prompt-token counts match its
  template (with its own default system prompt) in 4 of 5 conditions, 1 token off with the tool spec.
- **Qwen3 30B Thinking sometimes skips the tool** when it isn't forced; the solver forces the first
  call (`tool_choice`), so every tool-team case delivers its lookup.
- **`steered_cases.jsonl` has three models' rows** since Oct 28 18:00, with the same item ids.
  Any new run on it needs `--case-model` and its own `--log`. C4's summary still reads it
  correctly, because cases are matched by `model|item` id.
- **The Mac must stay awake** (plugged in, lid open) during live runs.
