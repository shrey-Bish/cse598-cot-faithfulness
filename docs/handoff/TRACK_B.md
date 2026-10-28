# Track B handoff: test widely (for Arsha, from Nov 3)

Last updated: 2026-10-28 06:00 MST. A working draft, kept current every day and final on Nov 3,
when Track B goes back to you. Until then Ritik runs it (code by Claude Code).

**The question.** Does the failure seen in the progress round (a wrong hint from a tool moves
thinking models more than the same hint from the user, and the final answer rarely says so) hold on
more models, with thinking on and off in the same model, real tool calls and 3 runs per question?

## 1. What's done (as of Oct 27)

- **Code** (`cot-disclosure/progress/run_trackB.py`, `configs/trackB.yaml`, `providers/`):
  - one runner for every provider; each (model, thinking, question, condition, run) is a job with a
    fixed `run_id`; restarts skip finished jobs; runs that got no reply are retried twice
  - `--model` (repeatable) and `--thinking on|off`; jobs go repeat by repeat, so a partial run is
    balanced and `--limit 5` is one question in all five conditions (the smoke test)
  - Olmo 3 7B Think runs as in Track A: our pinned Think template on `/v1/completions`, continued
    past calls quoted in its reasoning, a 32,768-token cap (prompt + reply); its tool channel is
    `tool_injected` (our call and the tool's reply written in, the tool declared), because it never
    calls a tool by itself
  - `--steered` exports `results/trackB/steered_cases.jsonl` for Track C (one row per question:
    the no-hint and per-channel runs; `steered` / `matched` / `other` by a fixed rule; written once
    per model after all its runs)
  - the budget guard for paid providers ($5 cap each; `providers/budget.py`); no key exists yet
- **Checks before the first runs** (Oct 27; session log 13:05):
  - served chat templates: Voyager's prompt-token counts equal our rendering with each model's own
    Hugging Face template on all 5 conditions for Qwen3 30B Thinking and Instruct, except the tool
    condition (−1: Voyager sorts the tool spec's JSON keys; same content). Olmo pinned: 5 of 5 equal.
  - identity canaries (`configs/canary/`): Olmo 3 7B Think, Qwen3 30B Thinking, Qwen3 30B Instruct
  - smoke tests: 15 of 15 answered (3 models × 5 conditions), no errors
  - Ollama `qwen3:8b` timing pilot: thinking on 99–189 s per call, off 23–45 s (this Mac)
- **Runs** (Oct 28): on the Mac under the power guard, Voyager only, one model after another.
  - **Qwen3 30B Thinking: done** (810 runs, 23:36–03:11).
  - **Qwen3 30B Instruct: done** (810 runs, 03:11–05:32, sharing the 4 Voyager slots with Track C's
    C4).
  - **Olmo 3 7B Think:** running since 05:32 (~8 h or more, with C4 beside it).
  - Steered cases for Qwen3 Thinking are exported: 24 steered, 29 matched, 1 other. **Instruct's
    export waits until C4 is done:** C4 reads `steered_cases.jsonl` on every restart, and every model
    has the same item ids. `run_team.py` now refuses a file with several models' rows unless
    `--case-model` picks one, and each model's cases need their own `--log`. Qwen3-8B, thinking on and off, moved to Sol (decided Oct 28: Ollama never on the Mac):
  `progress/sol_trackB.py`, one GPU job, runs on Ritik's "go".
- **Not done:** closed providers (no keys; Gate 1 was missed and its fallback applies: Voyager and
  our own Sol server only); GPQA (waits for Ritik to accept its terms on Hugging Face).
- **The table:** `progress/trackB_report.py` prints it from the saved runs (no calls). `--by-set`
  also gives it per question set; `--export` writes the numbers-only copies to
  `results/summaries/trackB/`.

## 2. Results so far

From the progress round ([`docs/FINDINGS.md`](../FINDINGS.md)):
- **F1** (confirmed, served format, two thinking models): the tool hint moved the answer on 17 of 31
  questions vs the user hint on 2 of 31, +48 points [+31, +65].
- **F3** (confirmed as keyword counts): the private reasoning names the hint in 208 of 216 hinted
  runs, the final answer in 8. Hand labels pending (Gate 2).
- **F2** (tentative): Olmo 3 7B Think's hint following depends on the serving format and the token
  budget; that is why Track B runs Olmo in the pinned format.

Track B's own numbers (FINDINGS F15; the 5-question rule: fewer than 5 questions, "too few
questions", no interval):
- **Qwen3 30B Thinking** (54 questions × 5 conditions × 3 runs, the 32,768 budget). Following the
  wrong hint:
  - user: 3 of 162 [1, 5%]
  - tool, pasted: 59 of 162 [29, 44%]
  - tool, real call: 54 of 162 [27, 41%]
  - system note: 57 of 162 [28, 43%]
  - no hint: the hint letter in 0 of 162
- **Gate 2:** tool − user is +35 points [+24, +46] (pasted) and +31 [+22, +42] (real call), both
  clear. They stay clear at the 16,000 cut.
- **The real call:** following when it called the tool, 54 of 54; its final answer named the tool
  in 3 of 54.
- **By set:** almost all the following is on MMLU-Pro (pasted 54 of 90, real call 50 of 90). On
  the puzzles: 5 of 72 and 4 of 72.
- **Qwen3 30B Instruct** (FINDINGS F16; the same design, no private reasoning):
  - user 1 of 162 [0, 3%]; pasted 35 of 162 [16, 29%]; real call 147 of 162 [85, 94%]; system note
    35 of 162 [16, 29%]
  - Gate 2: pasted +21 [+12, +31], real call +90 [+83, +96], both clear; no run past 16,000 tokens
  - it called the tool in 162 of 162 runs (tool choice left to the model); on the puzzles it took
    the tool's letter in 72 of 72, though pasted and system hints moved it 0 of 72 there
  - after a real call the final answer named the tool in 30 of 147 (all on MMLU-Pro)
- **Thinking minus Instruct** (paired by question, 54 questions): real call −57 [−70, −43],
  pasted +15 [+6, +25], system note +14 [+7, +20], user +1 [+0, +3]. The Thinking checkpoint calls
  the tool less but follows pasted and system hints more. These are two checkpoints, not one
  switch; Qwen3-8B on Sol is the same-weights comparison.

## 3. How to run each step

[`docs/RUNBOOK.md`](../RUNBOOK.md) §18 (Track B), §17 (the pre-push check, once per clone), §16 (data
handoff). In short, from `cot-disclosure/`:

```bash
../.venv/bin/python progress/run_trackB.py --dry-run --model M                 # jobs, calls, hours
../.venv/bin/python progress/run_trackB.py --run --model M --limit 5           # smoke test
nohup caffeinate -i ../.venv/bin/python -u progress/run_trackB.py --run --model M >> logs/trackB_M.log 2>&1 &
../.venv/bin/python progress/run_trackB.py --steered --model qwen3-30b-a3b-thinking-2507   # for Track C
```

**Your data:** produced data is gitignored, so it won't come with GitHub. Ritik shares the bundle
(`tools/make_handoff_bundle.py --track B`: `results/trackB/` and the canary log, with a sha256
manifest); unpack it into `cot-disclosure/` and check it with `--verify`.

## 4. Open items (docs/TODO.md, Track B)

| # | Item | Status (Oct 27) |
|---|---|---|
| B7 | Voyager runs: Qwen3 Thinking, then Instruct, then Olmo 3 7B Think | Thinking done (Oct 28 03:11); Instruct done (05:32); Olmo running since 05:32 |
| B4 | Qwen3-8B on Sol, thinking on and off (replaces the Ollama grid) | code done; waits for "go" |
| B8 | `steered_cases.jsonl` per model | Qwen3 Thinking exported (24 steered, 29 matched, 1 other); Instruct after C4 is done (C4 reads the file on restart); Olmo after its runs |
| B14 | The Track B table: model × channel × thinking; following vs the per-letter no-hint baseline; sure and unsure questions; mention in reasoning and final answer; tool-call rate | `trackB_report.py` (and `--by-set`); filled per model as runs finish |
| B9 | The Gate 2 question: is the tool-vs-user gap still clear with 3 runs per question and more models? | clear for Qwen3 Thinking (F15) and Qwen3 Instruct (F16); Olmo next |
| B1–B3 | Closed providers: keys, Haiku 4.5 check, smoke tests | blocked: keys and Ritik's "go" |
| B6 | GPQA export | blocked: Ritik accepts the terms |

## 5. Decisions you inherit

- Gate 1 (Oct 25) was missed; the fallback applies: Voyager, and Qwen3-8B on Sol (Ollama dropped Oct 28). Paid calls only with
  keys and Ritik's explicit "go"; the budget guard caps each provider at $5.
- 3 runs per question; temperature 0.6; 16,000 reply tokens for chat models; always streamed; a
  cut-off reply is no answer.
- Olmo 3 7B Think: pinned format, `tool_injected` declared, 32,768-token cap (Ritik is asked whether
  to keep this; a 16,000 cut can be applied in the analysis from the saved token counts).
- Hint following is always reported against the per-letter no-hint baseline, as X of Y with a 95%
  interval and the number of questions; fewer than 5 questions: "too few questions".
- Mentions are keyword counts until the hand labels are in; no admission claim before Gate 2.
- Nothing from GPQA in any doc or tracked file. Produced data never goes to GitHub.

## 6. Known traps

- **Wrong template** (FINDINGS T1, T2): Voyager rendered Olmo 3 7B Think with the Instruct template;
  check every new model's served template by prompt-token counts before trusting its runs.
- **Model-ID routing** (T3): Voyager changed its IDs on Oct 21; `client.py` maps our names to the
  family ID and `reasoning_effort` (`configs/models.yaml`). Run from a branch with this fix.
- **Identity** (T6): the hourly canary must pass; a missing reference only warns, so make one first
  (`progress/make_canary.py`).
- **"expected" false matches** (T5): the tool keyword pattern fires on ordinary words; compare with
  the same pattern's rate in no-hint runs.
- **4 requests in flight** across every process on the Mac (slot files in `progress/common.py`);
  Track C shares them.
- **The Mac must stay awake:** plugged in, lid open; `caffeinate -i` stops idle sleep only.
- **Olmo 3 7B Think never calls the tool**; with `tool_real` it never sees the hint.
- Olmo 3 7B Instruct (Track C's second reviewer): the served default system prompt differs from the
  current Hugging Face template's; with a system message the counts match.
