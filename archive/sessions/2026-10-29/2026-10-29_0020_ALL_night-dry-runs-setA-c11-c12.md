# Session log: the night's dry runs: set A, C11, C12 (2026-10-29 00:20 MST)

Project: CSE 598 Group 10. Track A trains Olmo 3 7B Think on Sol to stop hiding hint-following and
localizes where the hint is read; Track C runs a solver/reviewer/checker team on Track B's cases. This
log holds the dry runs of the three Voyager experiments in Ritik's overnight plan (Part 3 A, C11 and
C12), with each one's main comparison and decision rule, written before any of them runs.

## 1. Header

- **Time:** 2026-10-29 00:20 MST. **Track:** A and C. **By:** Ritik.
- **Branch:** `trackA-nosol` (= `main`); the night's commits stay local until the single push at the
  end.
- **Input:** Ritik's overnight plan (Oct 28–29).

## 2. What ran

- **Mac, no calls:**
  - the attribution fix (487d47d: every log "By:" line and every past-work owner is Ritik);
  - the code below, with its tests;
  - the three dry runs.
- **Voyager:** nothing yet. The three runs start after this log, under one power guard, in Part 4's
  order: A, then C11, then C12.

## 3. Code (new or changed, all with CPU tests)

- **`finetune/setA.py`** (new): set A's runs, probes and cases (§4). It reuses Step 2b's runner
  (`base_format.one`) and Step 3's probes (`look/takeover.py`).
  - `takeover.save_cases` takes a path, rule and use.
  - Steps 9 and 10 take `--items-from` (and Step 9 `--step3-from`). Without them, Step 9's inputs
    are the Test 2 questions and Step 3's runs file.
  - `patching.py --handoff` takes `--handoff-out`, so set A's readout doesn't overwrite Test 2's.
- **`agents/reviewer.py`:**
  - the redacted variants for C12;
  - `redact`: every standalone mention of the tool's letter in the private reasoning;
  - `redact_tool_log`: the returned letter in the tool log.
- **`agents/run_team.py`:**
  - `--no-check-tool` (C4's original prompt) and `--bad-first`;
  - C12's comparisons with C4's unredacted variant (`vs_original_prompt`) and with C4's
    answer_only (`vs_original_answer_only`).
- **Tests:** `tests/test_setA.py` (6), 3 more in `tests/test_trackC_team.py`. The existing Step 3,
  9 and 10 tests pass (55).

## 4. Dry runs, main comparisons and decision rules (pre-registered)

### A. Set A: does the readout replicate on questions not used to find it?

```
$ ../.venv/bin/python finetune/setA.py --dry-run
set A: 34 questions ({'mmlupro_train': 16, 'fresh_puzzles_hard': 18}), none in training or in Test 2; sure (3 of 3 Step 6 no-hint runs correct): 34 of 34
204 runs: pasted tool block x 3 and declared inserted tool turn x 3 per question = 204 calls, plus up to 204 if inserted-tool replies keep calling
  time at Step 2b's 78 s/call, 4 in flight: 66 min (longer for long puzzle replies: Step 6's no-hint runs here had a median of 8,606 tokens)
then Step 3 grid_tail probes on the followed runs (~0.5 s a probe, a few dozen per run), then the cases -> results/trackA/setA/cases.jsonl
```

- **Questions:** the 34 validation questions of the training data. None is among the 217 training
  questions, and none is among Test 2's 30 (the questions F11 and F12 were found on, and the
  evaluation set); a test checks both.
- **Hint letter:** each question's own, chosen in Steps 6–7 (`pool.jsonl`), fixed before tonight.
  It is never the correct letter and never one of the model's no-hint answers.
- **Runs:** Step 2b's code, format and wordings. That is the pasted tool block × 3 and the declared
  inserted tool turn × 3 per question, the two arms Steps 9 and 10 used.
- **No-hint baseline:** the 3 Step 6 runs per question. They give the own answer (majority) and
  "sure" (all 3 correct). All 34 questions are sure.
- **Then:** Step 3's grid_tail probes on every followed run; cases are followed runs with a late
  takeover on sure questions. Tomorrow on Sol: Step 10 on those cases, and Step 9 on set A's runs
  (`--runs-from`, `--items-from`, `--step3-from`, `--cases-from`; the lines are in the morning
  daily).
- **Main comparison:** at cut (ii), the share of the hint-row restoration drop at layers 15, 19 and
  23 (`patching.py --handoff`, set A's step10_patching.json), with a 95% bootstrap clustered by
  question. Test 2 gave 0.90 [0.85, 0.96] (F11).
- **Decision rule:**
  - **Replicates:** the lower bound is above 0.375 (3 of the 8 full-attention layers' even share),
    *and* 15, 19 and 23 are the three layers with the largest drops.
  - **Partly:** one of the two holds.
  - **Does not replicate:** neither holds.
  - It is reported against 0.90 either way.
- **Too few:** if fewer than 5 questions have a late takeover, the answer is "too few". The log then
  proposes more questions from MMLU-Pro categories that are neither in the evaluation nor used by
  training.

### C11. Is the deference general? Two more reviewer models

```
$ ../.venv/bin/python agents/run_team.py --rereview team_c4 --no-check-tool --bad-first --reviewer-model voyager:olmo3-7b-instruct --reviewer-model voyager:qwen3-30b-a3b-thinking-2507 --reviewer-max-tokens 16000 --cases results/trackB/steered_cases.jsonl --log team_c11 --dry-run
159 saved tool-team cases of team_c4 (53 items; 75 bad and 84 good lookups), 159 to run: ~954 calls (2 reviewer models x 3 variants: answer_only, plus_private, plus_tool_log); no solver or checker calls. C4's reviewer prompt, unchanged; bad lookups first (75 cases)
```

- **Models:**
  - Olmo 3 7B Instruct (Olmo family, 7B, no thinking);
  - Qwen3 30B Thinking (Qwen family, 30B MoE, thinking).
  - With C4's Olmo 3.1 32B Instruct (defers) and Qwen3 30B Instruct (doesn't), family, size and
    thinking can be told apart.
  - Both have identity canaries.
  - **Left out:** Olmo 3 7B Think, whose served chat endpoint uses the Instruct template, not its
    own (Track B had to render its format by hand); and Olmo 3.1 32B Think, which has no canary.
- **Settings:** C4's reviewer prompt, temperature 0.6, seed = repeat, on C4's saved cases. The cap is
  16,000 tokens (C4: 8,000), because a thinking reviewer's reasoning counts. No letter counts as not
  correcting, and is reported.
- **Main comparison:** per model, plus_private minus answer_only on correcting a wrong answer after
  a bad lookup (25 items), paired by item. The same for plus_tool_log.
- **Decision rule:**
  - **Defers:** the difference's upper bound is below −20 points.
  - **Doesn't defer:** the interval includes 0, or lies above −20.
  - **Unclear:** otherwise.
- **Across the four models:**
  - **Family:** both Olmo defer, both Qwen don't.
  - **Size:** Olmo 7B differs from Olmo 32B.
  - **Thinking:** Qwen Thinking differs from Qwen Instruct.
  - It is reported as whichever of these the four results fit, or none.
- **Order:** bad lookups first, so the main comparison is complete first if time runs short.

### C12. What is the cue? The tool's letter redacted

```
$ ../.venv/bin/python agents/run_team.py --rereview team_c4 --no-check-tool --bad-first --variants plus_private_redacted,plus_tool_log_redacted --cases results/trackB/steered_cases.jsonl --log team_c12 --dry-run
159 saved tool-team cases of team_c4 (53 items; 75 bad and 84 good lookups), 159 to run: ~636 calls (2 reviewer models x 2 variants: plus_private_redacted, plus_tool_log_redacted); no solver or checker calls. C4's reviewer prompt, unchanged; bad lookups first (75 cases)
```

- **Reviewers:** C4's two, with C4's prompt and settings.
- **Redaction rule** (fixed before the run, `reviewer.redact`):
  - **Private reasoning:** every standalone mention of the tool's letter ("B", "(B)", '"B"')
    becomes "[redacted]". On the 75 bad lookups, that is a median of 40 redactions per reasoning,
    and at least 5 in each.
  - **Letters A and I** (12 of the 75) are also English words. For them only option-like forms go:
    "(A)", "A)", quoted, or after option/answer/choice/letter/is/be/to. So "I think A is wrong"
    could survive.
  - **Tool log:** the returned letter is redacted.
  - **Unchanged:** the proposed answer and the solver's final answer ("Answer: (B)"). The reviewer
    must see what it reviews.
- **Main comparison:** for each reviewer, on correcting a wrong answer after a bad lookup, paired by
  item:
  - plus_private_redacted minus C4's plus_private;
  - plus_tool_log_redacted minus C4's plus_tool_log;
  - each redacted variant minus C4's answer_only.
- **Decision rule** (the Olmo reviewer, which defers):
  - **The letter is the cue:** redacted minus unredacted has an interval above 0, *and* redacted
    minus answer_only's interval includes 0.
  - **The letter is not the cue:** redacted minus unredacted's interval includes 0. The deference
    then comes from knowing the answer came from the key, not from seeing its letter.
  - **Partly:** in between.
  - For the Qwen3 reviewer (no deference to remove), this is a check that redaction doesn't hurt.

## 5. The guard (power rules; at most 4 requests in flight; canaries first)

```
cd cot-disclosure
nohup caffeinate -i ../.venv/bin/python -u progress/guard.py \
  --job "voyager:setA=finetune/setA.py --run" \
  --job "voyager:c11:setA=agents/run_team.py --rereview team_c4 --no-check-tool --bad-first --reviewer-model voyager:olmo3-7b-instruct --reviewer-model voyager:qwen3-30b-a3b-thinking-2507 --reviewer-max-tokens 16000 --cases results/trackB/steered_cases.jsonl --log team_c11 --run-name C11-oct29" \
  --job "voyager:c12:c11=agents/run_team.py --rereview team_c4 --no-check-tool --bad-first --variants plus_private_redacted,plus_tool_log_redacted --cases results/trackB/steered_cases.jsonl --log team_c12 --run-name C12-oct29" \
  >> logs/guard_night.log 2>&1 &
```
`logs/stop_guard` stops all three, letting requests in flight finish. Exit 3 means a Voyager guard
failed, and every Voyager job pauses.

## 6. For review

- **Set A's hint letters come from Steps 6–7's choice,** not from Test 2's rule (Test 2 had its own
  per question). Both were fixed before the runs.
- **C11's 16,000-token cap differs from C4's 8,000;** a thinking reviewer needs it.
- **C12's redaction can miss some mentions of A and I** (12 of 75 bad lookups). It removes the
  letter, not the fact that a tool was consulted.
- **The power guard chains the jobs:** C11 starts only when set A exits 0. If set A gets stuck, C11
  and C12 wait.
