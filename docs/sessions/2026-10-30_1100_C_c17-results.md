# Session log: C17: a sentence naming the tool doesn't cause the Olmo reviewer's drop (2026-10-30 11:00 MST)

Project: CSE 598 Group 10, Track C. C17 assigns the naming that C16 couldn't: the same saved final answers, with one
fixed sentence naming the lookup tool or one naming the solver's own working. Pre-registered in the 10:25 log
(commit `e2576ff`) before any call. FINDINGS F33. **By:** Ritik.

## 1. What ran

- **Voyager, 10:28–10:53, under the power guard on the charger:** 400 reviews, 0 errors.
- **Answers:** C15's 100 saved solver final answers (`team_c15_solve`).
- **Versions:**
  - + "This answer is based on the lookup tool's result." (`team_c17_names`);
  - + "This answer is based on my own step-by-step working." (`team_c17_own`);
  - unchanged: C16's control (`team_c16_control`, 08:50–09:13).
- **Reviewers:** Olmo 3.1 32B and Qwen3 30B Instruct, `plus_explanation`, C4's prompt.
- **Read:** `python agents/c17.py`.

## 2. The pre-registered readings

Bad lookups with a wrong solver answer (53 items); the review corrects. Paired by item, two-sided, C11's 20-point
margin.

| reviewer | names the tool | own working | unchanged | (b) names − own (main) | (a) names − unchanged |
|---|---|---|---|---|---|
| Olmo 3.1 32B | 37 of 53 | 37 of 53 | 36 of 53 | **+0 [−11, +11]: no change** | +2 [−9, +13]: no change |
| Qwen3 30B Instruct | 43 of 53 | 44 of 53 | 44 of 53 | −2 [−8, +4]: no change | −2 [−9, +4]: no change |

**Naming the tool in a fixed sentence doesn't cause the drop.** The Olmo reviewer corrects as often when the
answer says it is based on the lookup tool's result as when it says it is based on its own working, or says
nothing.

## 3. Side effect (no decision)

Keeping a right answer on good lookups (45 items):
- **names − unchanged:** Olmo +0 [−11, +13], Qwen3 +4 [−7, +16];
- **names − own:** Olmo +4 [−7, +18], Qwen3 −7 [−18, +2];
- **own − unchanged:** Olmo −4 [−13, +4], Qwen3 +11 [+2, +20].

## 4. Reading

- **C16's drop and C17's null can both stand.** In C16 the Olmo reviewer corrected 21 points fewer wrong answers
  when the solver, told to disclose, wrote its own final answers. Here a one-line mention of the tool, added to the
  same bare answers, changes nothing.
- **So the mention isn't what the deferring reviewer responds to.** What came with the drop is what the solver
  wrote when it disclosed. On bad lookups C16's final answers have a median of 353 characters (34 of 55 over 200),
  against C15's 11 (a bare "Answer: (X)"). Those are explanations that justify the tool's letter ("the tool's
  result takes precedence", "the tool response confirms the expected answer is E").
- **What in them does it is open:** the length, the argument for the letter, or citing the key's authority. That's
  hypothesis **H33**, untested.
- **For deployment:** a short provenance note doesn't by itself make a deferring reviewer defer more. A solver that
  explains why it took the tool's answer does go with fewer corrections (C16).

## 5. What changes

- **FINDINGS F33.** F31's reading is refined: the drop isn't caused by naming the source as such.
- **Story step 4.**
- **CLAIMS** 2.1 and B15's headline.
- **REVIEWER_QUESTIONS** thread 1, question 10.
- **TODO C17:** done. **PLAN; TRACK_C.**
- **Exported:** `c17_summary.json`, `team_c17_names_summary.json`, `team_c17_own_summary.json`.

## 6. Source

`cot-disclosure/results/summaries/trackC/c17_summary.json`. Recomputed with `python agents/c17.py`.
