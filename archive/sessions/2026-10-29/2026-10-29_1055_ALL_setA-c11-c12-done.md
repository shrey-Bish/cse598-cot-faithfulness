# Session log: set A on Voyager, C11 and C12 done (2026-10-29 10:55 MST)

Project: CSE 598 Group 10. Track A localized where Olmo 3 7B Think reads a wrong hint (layers 15, 19
and 23, found on Test 2's 30 questions); set A asks whether that replicates on 34 questions not used
to find it. Track C runs a solver/reviewer/checker team; C11 and C12 ask whether the reviewer's
deference to a tool is general and what its cue is. All three were pre-registered in the session log
of Oct 29 00:20; this log has their results.

## 1. Header

- **Time:** Oct 29, 07:58–10:47 (the guard's three Voyager jobs), analysis to 10:55. **Track:** A
  and C. **By:** Ritik.
- **Branch:** `trackA-nosol`; this log's commit is local until Ritik's "push".
- **Tests:** 478 pass (with the vLLM fix being made in a parallel session; its files are not in this
  commit).
- **In flight:** nothing on Voyager (the guard ended 10:47). Sol: batch 3 and Qwen3-8B (Ritik).

## 2. Set A (Voyager, 00:20–01:59 and 07:58–09:32)

- **Runs:** 204 of 204. The hint was followed in 30 of 100 answered pasted runs and 26 of 101
  answered inserted + declared runs (14 questions each).
- **Probes:** Step 3's grid_tail on all 56 followed runs. Takeover types: late 39, other 10, at 0 7.
- **Cases:** 39 late takeovers on 16 sure questions (20 pasted, 19 inserted; 10 MMLU-Pro, 6
  puzzles), against the pre-registered minimum of 5 questions. Test 2 had 26 on 9.
- **Sol's three jobs, from their dry runs (Mac):**

  | Job | Size | A100 time |
  |---|---|---|
  | Step 10 | 34 cases (at most 3 a question), 66 cuts (32 at (i), 34 at (ii)), 42.4M tokens, median 3,436 a cut | ~80 min |
  | Step 9 | 201 runs, 2.4M tokens | ~12 min |
  | B1 forced | 66 cuts, 8.5M tokens | ~18 min |

- **The lines** (rsync, then the three jobs with `--out $A`) are in the Oct 29 daily.
- **The pre-registered answer** waits for Step 10's `step10_patching.json`.

## 3. C11 (09:32–10:31; 954 reviews, 0 errors): FINDINGS F22

- **Corrects a wrong answer after a bad lookup** (25 items), each variant minus answer only:

  | Reviewer | Answer only | + private reasoning | + tool log | Verdict |
  |---|---|---|---|---|
  | Olmo 3 7B Instruct | 32 of 73 | 1 of 73: −42 [−58, −28] | 1 of 73: −42 [−58, −28] | **defers** |
  | Qwen3 30B Thinking | 66 of 73 | 67 of 73: +1 [−6, +10] | 67 of 73: +1 [−5, +9] | **doesn't defer** |

- **With C4's two:** Olmo 3.1 32B defers; Qwen3 30B Instruct doesn't. So **family** fits; size and
  thinking don't. The family reading is tentative: two models per family, one solver's cases.

## 4. C12 (10:31–10:46; 636 reviews, 0 errors): FINDINGS F23

- **Olmo 3.1 32B, the tool's letter redacted:** **partly**.
  - It corrects 23 and 24 of 73 (unredacted 6 and 3: +23 [+13, +34], +29 [+16, +41]).
  - Answer only gives 59 (−49 [−64, −34], −48 [−62, −33]).
  - All of the restoration is on matched puzzles (+33, +35; 15 items). On steered MMLU-Pro it is
    none (2 of 24; 8 items).
- **Qwen3 30B Instruct:** no harm (+3 [+0, +7], +11 [−1, +25]).

## 5. Files

- `docs/FINDINGS.md`: F22, F23, and the story so far (step 4).
- `docs/TODO.md`: A29, C11, C12.
- `tools/export_summaries.py`: C11's and C12's summaries.
- `results/summaries/trackC/team_c11_summary.json`, `team_c12_summary.json`: numbers only.
- `results/summaries/voyager_canary.jsonl`: today's canaries, all pass.
- The Oct 29 daily: set A's line with the dry-run sizes; Step 10's estimate is 2.

## 6. For review

1. **C11's family reading** rests on 2 models per family. A third family (e.g. another open
   reviewer on Voyager) would test it.
2. **C12's split by set:** redaction helps on puzzles, not on steered MMLU-Pro (8 items). The
   letters A and I don't explain it (3 of 21 steered cases).
3. **Set A's Step 10 decides the replication.** Its rule: the lower bound of the share at 15/19/23
   above 0.375, and those three the top drops.

## 7. Next

- **Ritik:** set A's rsync and Step 10 on Sol, then Step 9 and B1 forced as slots free. Step 10's
  `step10_patching.json` back to `results/trackA/setA/`.
- **Mac:** `patching.py --handoff results/trackA/setA/step10_patching.json --handoff-out
  results/trackA/setA/step10_handoff.json`, then the set A finding against its rule.
