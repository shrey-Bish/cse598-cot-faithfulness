# Track C handoff: the agent team (for Shrey, from Nov 3)

Last updated: 2026-10-27 14:20 MST. A working draft, kept current every day and final on Nov 3,
when Track C goes back to you. Until then Ritik runs it (code by Claude Code).

**The question.** When the solver's lookup tool returns a wrong answer, does it reach the team's final
output? What changes when the reviewer sees more (the explanation, the private reasoning, the tool
log), and how often does the checker catch it or raise a false alarm?

## 1. What's done (as of Oct 27)

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
  - **two reviewer models** (`--reviewer-model`, default Qwen3 30B Instruct and Olmo 3 7B Instruct;
    each has an identity canary)
  - **Track B's cases as input** (`--cases results/trackB/steered_cases.jsonl --kinds steered,matched
    --per-kind N --repeats 3`); cases run 4 at a time through the shared Voyager slots
  - `--summary`: per team × reviewer model × variant, bad and good lookups apart, Wilson intervals,
    undetermined checks, tokens, and the checker's flag rate per team
- **Runs:** replay of Experiment A (no calls); live on 2 pilot puzzles (Oct 4); **C1, live on 5
  pilot puzzles, started Oct 27 13:52** (tool team, 2 reviewer models, ~55 calls).

## 2. Results so far

- **Experiment A** (Oct 4, a demo, not a result; [`docs/OVERVIEW.md`](../OVERVIEW.md) §6): a reviewer
  that never saw the hint kept a hinted wrong answer in 0 of 15 reviews from the answer alone, 7 of
  15 once it read the explanation; a re-ask without the hint flagged 5 of 5, with 1 false alarm in 6.
- **Replay** of those runs through the pipeline (`--replay`): wrong answers shipped 3 of 33 reviews
  (answer only) and 2 of 33 (with the explanation); caught 15 of 15 wrong solver answers in both;
  false alarms 6 of 18 and 5 of 18 right ones. 6 items: too few questions for intervals.
- **Live, Oct 4** (2 puzzles, 1 bad lookup): the checker caught the bad lookup in every variant; no
  false alarm. 2 items: no rate can be read.
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
```

**Your data:** gitignored, shared by Ritik as a bundle (`tools/make_handoff_bundle.py --track C`:
`results/trackC/`, Track B's `steered_cases.jsonl`, the labeling kit; sha256 manifest; check with
`--verify`).

## 4. Open items (docs/TODO.md, Track C)

| # | Item | Status (Oct 27) |
|---|---|---|
| C1 | Live team on 5 items | running |
| C4 | The team on Track B's steered and matched cases (Qwen3 Thinking's first), 3 repeats, tool and no-tool teams | after Track B exports Qwen3 Thinking's cases |
| C5 | The Track C table per reviewer variant: shipped, caught, false alarms, undetermined; bad and good lookups apart; the checker's disagreement against the no-tool team's run-to-run variation; tokens | as data lands |

## 5. Decisions you inherit

- Gate 1 (Oct 25) was missed; the fallback applies: Voyager only for Track C.
- Solver Qwen3 30B Thinking; reviewers Qwen3 30B Instruct and Olmo 3 7B Instruct (a second model
  family); bad lookups ~50% by a seeded oracle (seed 20261005); 3 repeats per case for C4.
- False alarms are always reported next to catches; undetermined checks are counted, never dropped.
- Every rate as X of Y with a 95% interval and the number of items; fewer than 5: "too few".
- Logs are append-only and gitignored; numbers-only summaries go to `results/summaries/`.

## 6. Known traps

- **4 requests in flight** across every process on the Mac, shared with Track B's runs: Track C's
  cases wait for a free slot.
- **Identity canaries** for every Voyager model before its first batch (`configs/canary/`).
- **Olmo 3 7B Instruct's served default system prompt** differs from the current Hugging Face
  template's; reviewer calls always send their own system prompt, where the counts match.
- **Qwen3 30B Thinking sometimes skips the tool** when it isn't forced; the solver forces the first
  call (`tool_choice`), so every tool-team case delivers its lookup.
- **The Mac must stay awake** (plugged in, lid open) during live runs.
