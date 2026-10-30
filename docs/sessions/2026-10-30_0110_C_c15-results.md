# Session log: C15 done; the pre-registered readings (2026-10-30 01:10 MST)

Project: CSE 598 Group 10, Track C. C15 replicates C4's team on 100 fresh items. It was pre-registered in the Oct 29
23:00 log before any call, and is read here by that log's rules. FINDINGS F24 has the full entry.

## 1. Header

- **Time:**
  - the solver and checker, Oct 29 22:48–23:57 (200 of 200 cases);
  - the reviews, Oct 29 23:57 – Oct 30 00:45 (100 of 100 cases, 600 calls), beside B15.
- **Errors:** 0. **By:** Ritik. **Branch:** `trackA-nosol`, local commits.
- **Power:** on the charger until about 23:50, then on battery (97% → 88% at 00:45); the guard didn't pause.

## 2. The three pre-registered readings

**(a) Does F18 replicate? Yes.** plus_tool_log minus answer_only on correcting a wrong answer after a bad lookup
(53 items), by C11's rule:
- **Olmo 3.1 32B Instruct:** 39 → 10 of 53, **−55 [−70, −38]**: defers. It defers on both sets: MMLU-Pro −48
  [−68, −29], puzzles −64 [−86, −36].
- **Qwen3 30B Instruct:** 43 → 40 of 53, −6 [−15, +4]: doesn't defer.

**(b) H23 is not supported.** For the Olmo reviewer, redaction's restoration where its own answer_only review
corrects (0.28, 39 items) minus where it doesn't (0.14, 14 items) is **+14 [−13, +37]**. That is H23's direction,
but the interval includes 0. Qwen3, with no reading drawn: +15 [−2, +39].

**(c) C14's rule, frozen: neither claim is confirmed.** Against the checker's pipeline with the same reviewer:
- **(c1) Olmo:** false alarms 8 against 7 of 45, **+2 [−9, +13]**: not confirmed (C14 had +12).
- **(c2) Qwen3:** caught 46 against 53 of 53, **−13 [−23, −6]**, and false alarms +2 [−11, +16]. Not confirmed:
  the lower bound is below −10, and the upper bound is above +10.
- **The rule ships wrong answers** (4 with Olmo, 7 with Qwen3, of 53) where both reviews agree on the wrong letter.
  The checker's pipeline ships none: it caught 53 of 53 with both reviewers.

## 3. Also reported (no decision)

- **Redaction, as in C12:** Olmo 10 → 23 of 53 (+25 [+11, +38]), still −30 [−47, −13] below answer only. The
  restoration is on both sets: MMLU-Pro 6 → 14 of 31, puzzles 4 → 9 of 22. Qwen3: +2 [−8, +11].
- **Good lookups:** with the tool log, Olmo keeps the right answer in 45 of 45 (alone: 37; +18 [+7, +29]), and
  Qwen3 in 43 of 45 (36; +16 [+7, +27]).
- **The checker:** it flagged 53 of 55 bad lookups and 7 of 45 good ones. The no-tool floor was 7 of 100 [3, 14%],
  so good − floor is +4 [−7, +16].
- **The solver's final answer after a lookup** (F15 on fresh items): bare in 50 of 55 (bad) and 43 of 45 (good),
  against 0 of 100 with no tool. Good − bad is +5 [−5, +15].
- **Tokens per case:** the rule's added answer_only review takes 1,050–1,206; the checker's re-ask 3,545.

## 4. What changes

- **FINDINGS F24 added.**
- **Story step 4:** the deference and the partial restoration replicate on fresh items.
- **F23's H23:** "tested in C15: not supported".
- **CLAIMS:**
  - 2.1 is now *confirmed* on fresh items for the Olmo reviewer;
  - 2.4's split by set is dropped;
  - 2.6 (a cheaper check) is refuted as a replacement for the checker.
- **For deployment:** F18's point is stronger. The check that never sees the tool held on every wrong answer, in C4
  and here.
- **Process:** C14's favourable reading for Qwen3 came from the cases that chose the rule, and it didn't survive
  fresh items. That is the reason C15 was pre-registered.

## 5. Source

- `cot-disclosure/results/summaries/trackC/c15_summary.json`, `team_c15_summary.json`, `team_c15_solve_summary.json`.
- Recomputed with `python agents/c15.py` (no calls).

## 6. Next

- **B15:** running; its readings and log when it ends.
- **The 07:00 daily.**
