# Session log: C16: the Olmo reviewer corrects less when the final answer names the tool; unclear by the rule (2026-10-30 10:30 MST)

Project: CSE 598 Group 10, Track C. C16 asks whether a solver's final answer that names the tool (B15's
instruction) changes how often a reviewer corrects a wrong one. Pre-registered in the 08:50 log before any call.
Ritik agreed the ruling (plus_explanation, the same-day control as the main comparison) at 10:00. FINDINGS F31.
**By:** Ritik.

## 1. What ran

- **Voyager, under the power guard, on the charger, 0 errors:**
  - the solve phase 08:50–09:29 (100 cases);
  - the same-day control 08:50–09:13 (200 reviews of C15's solver answers);
  - C16's reviews 09:29–09:33 (200).
- **Solver:** Qwen3 30B Thinking, C15's 100 fresh items, C4's oracle (55 bad, 45 good lookups), the solver's turn
  ending with B15's instruction.
- **Reviewers:** Olmo 3.1 32B Instruct and Qwen3 30B Instruct, C4's prompt, `plus_explanation`: the question, the
  proposed letter and the solver's final answer.
- **Read:** `python agents/c16.py` (no calls).

## 2. The solver did what B15 found

On C16's solve against C15's, paired by item:
- **Its final answer names the tool:**
  - after bad lookups 34 of 55 (C15: 5), +53 [+36, +67];
  - after good ones 32 of 45 (C15: 1), +69 [+56, +82].
- **Bare:** 21 of 55 (C15: 50) and 11 of 45 (C15: 43).
- **It takes the tool's wrong letter** in 54 of 55 (C15: 52), +4 [0, +9]. It is right on all 45 good lookups in
  both.

So the reviewer now sees a final answer that says where the letter came from, in about 6 of 10 cases, and the
letter is still the tool's.

## 3. The pre-registered reading

**Items:** bad lookups with the solver wrong in both solves (53 items). **Measure:** the review corrects (its letter
is right). **Comparison:** C16 minus the control, paired by item, with a 95% bootstrap clustered by item. **Rule:**
two-sided with C11's 20-point margin.

| reviewer | C16 (final answer names the tool, 34 of 55) | control (C15's solver) | minus | reading |
|---|---|---|---|---|
| Olmo 3.1 32B | 25 of 53 | 36 of 53 | **−21 [−34, −8]** | **unclear** |
| Qwen3 30B Instruct | 44 of 53 | 44 of 53 | +0 [−9, +11] | **no change** |

- **Olmo: unclear.** The interval excludes 0, so the drop is detected. Its upper bound (−8) isn't below −20, and
  its lower bound (−34) is past −20, so it is neither "fewer corrections" (by 20 points or more) nor "a smaller
  drop". Plainly: Olmo corrects fewer wrong answers when the answer names the tool, by between 8 and 34 points.
- **Qwen3: no change.**
- **Against C15's answer_only, as Ritik named it:**
  - Olmo 25 against 39 of 53, −26 [−42, −11], unclear;
  - Qwen3 44 against 43, +2 [−4, +9], no change.

## 4. Side effect (no decision)

Keeping a right answer on good lookups (45 items), C16 minus the control:
- Olmo 43 against 40 of 45, +7 [0, +16];
- Qwen3 40 against 35 of 45, +11 [0, +22].

Against C15's answer_only: +13 [0, +27] and +9 [0, +20]. Naming a right tool helps the reviewer keep the right
answer a little, less than the tool log did in C15 (+18 and +16).

## 5. Checked after the reading (descriptive, not pre-registered)

The solver named the tool on some bad-lookup items and not others. Split by that, C16 minus the control:
- **Olmo, where the final answer named the tool** (32 items): 8 against 21, −41 [−59, −25].
- **Olmo, where it didn't** (21 items): 17 against 15, +10 [0, +24].
- **Qwen3:** +0 in both (24 against 24, 20 against 20).

The drop sits where the tool is named. But the solver chose when to name it, so the two groups can differ in more
than the naming (for example, how hard the item is). This split is a pointer, not a result.

## 6. Reading

- **For the Olmo reviewer, the disclosure B15 can prompt makes its check worse, not better.** It corrects 21
  points fewer wrong answers when the solver's answer says it came from a lookup. The rule calls the size
  "unclear" (between 8 and 34 points). The descriptive split puts the effect where the tool is actually named.
- **Qwen3 30B Instruct, the reviewer that didn't defer to the tool log** (F18, F24), doesn't change.
- **With B15 (F25), the chain reads:**
  - the solver can be prompted to say it used the tool;
  - it still takes the tool's wrong letter;
  - and a reviewer from the deferring family then defers more.
- **Disclosure without independence doesn't protect the pipeline.** The check that never sees the tool held in
  C4, C13 and C15.
- **Limits:**
  - one wording;
  - one solver;
  - 1 repeat;
  - keyword counts for naming;
  - the control reviews Oct 29's solver answers, the same day's reviewers.

## 7. What changes

- **FINDINGS F31.** Story step 4: C16.
- **CLAIMS:** 2.1 (the deferring family defers to a named source too) and B15's headline.
- **REVIEWER_QUESTIONS:** thread 1, question 10.
- **TODO C16:** done. **PLAN; TRACK_C.**
- **Exported:** `c16_summary.json`, `team_c16_summary.json`, `team_c16_control_summary.json`,
  `team_c16_solve_summary.json`.

## 8. Source

`cot-disclosure/results/summaries/trackC/c16_summary.json` (`main`, `vs_c15_answer_only`, `side_effect_keeps*`,
`solver`). Recomputed with `python agents/c16.py`.
