# Session log: C13: neither new reviewer family defers; the family reading holds (2026-10-30 09:20 MST)

Project: CSE 598 Group 10, Track C. C13 adds a third and a fourth reviewer family on Sol: IBM Granite 4.1 30B and
Mistral Small 3.2 24B Instruct. Both are non-thinking instruct models of 24–30B, like C4's pair. Pre-registered in
the Oct 29 16:45 log (section 7). FINDINGS F30. **By:** Ritik.

## 1. What ran

- Sol: get_c13 66954063 (the snapshots, 19:53) and C13 66954278 (47:33), both exit 0.
- Each model was served by the job's own vLLM. They reviewed C4's 159 saved tool-team cases (53 items: 75 bad and
  84 good lookups):
  - variants answer_only, plus_private and plus_tool_log;
  - C4's prompt; C11's settings (temperature 0.6, seed = repeat, 16,000-token cap);
  - 477 reviews per model.
- The logs came back by rsync. Read on the Mac:
  `python agents/run_team.py --summary --log team_c13_<model> --cases results/trackB/steered_cases.jsonl --table`.

## 2. The pre-registered readings

**Question 1: does the plus_private drop appear?** Per model, plus_private minus answer_only on correcting a wrong
answer after a bad lookup (25 items, 73 reviews), paired by item, by C11's rule: defers if the upper bound is
below −20 points; doesn't defer if the interval includes 0 or lies above −20; unclear otherwise.

| reviewer | answer only | + private reasoning | minus answer only | rule | + tool log (secondary) |
|---|---|---|---|---|---|
| Granite 4.1 30B | 27 of 73 [27, 48%] | 23 of 73 | −5 [−26, +15] | **doesn't defer** | 25 of 73, −3 [−27, +21] |
| Mistral Small 3.2 24B | 49 of 73 [56, 77%] | 63 of 73 | **+19 [+10, +30]** | **doesn't defer** | 63 of 73, +19 [+9, +31] |

**Question 2: does family still predict it?** The pre-registered readings:
- **Olmo-specific:** neither new model defers. Deference is seen in one family of four, and family still predicts
  it.
- **Not one family's trait:** at least one new model defers.

**Result: Olmo-specific.** Neither Granite nor Mistral defers. Across six reviewers and four families, the two Olmo
models defer (F18, F22) and the two Qwen3, the Granite and the Mistral reviewers don't.

## 3. Also reported (no decision)

- **Granite's own check is weak.** Alone it corrects 27 of 73 wrong answers and keeps only 58 of 84 right ones. So
  there is less to lose. Its interval reaches −26: by the rule it doesn't defer, but a drop of
  that size isn't ruled out.
- **Mistral gains from the trace.** With the solver's private reasoning or the tool log, it corrects more (49 → 63),
  not fewer.
- **Both keep right answers better with the trace:**
  - Granite 58 → 84 of 84 (+31 [+17, +46]);
  - Mistral 47 → 84 of 84 (+44 [+29, +60]).
- **By set** (bad-lookup items: 15 matched puzzles, 8 steered MMLU-Pro, 2 other):
  - Granite: +5 [−18, +27] on the puzzles, −25 [−62, +17] on the steered MMLU-Pro;
  - Mistral: +12 [+5, +20] and +33 [+12, +58].
- **The pipeline:** with either reviewer, in every variant, the checker's pipeline catches 73 of 73 wrong answers,
  as in C4.

## 4. Reading

- Deference to the solver's trace is not a general property of instruct reviewers. Six reviewers over four
  families show it in one family, Olmo, at two sizes.
- Size and thinking were held near C4's pair, so the family is the best single predictor so far. Why Olmo defers
  is open.
- The deployment point from F18 stands: the check that never sees the tool (the checker) is the one that holds
  across reviewers.

## 5. What changes

- **FINDINGS F30.** F22's family reading: *confirmed* on six reviewers, four families.
- **Story step 4.**
- **CLAIMS** 2.1, 2.3.
- **REVIEWER_QUESTIONS** thread 2, question 1, filled in.
- **TODO C13:** done.
- **TRACK_C handoff.**
- **Exported:** `team_c13_granite_summary.json`, `team_c13_mistral_summary.json`.

## 6. Source

`results/summaries/trackC/team_c13_granite_summary.json`, `team_c13_mistral_summary.json` (numbers only).
