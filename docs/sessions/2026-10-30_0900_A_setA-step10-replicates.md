# Session log: set A's Step 10: the readout at layers 15, 19 and 23 replicates (2026-10-30 09:00 MST)

Project: CSE 598 Group 10, Track A. Set A asks whether the readout F11 found on Test 2's 30 questions holds on 34
questions not used to find it (the training data's validation questions). The rule was fixed in the Oct 29 00:20
log, before set A's runs existed. FINDINGS F26. **By:** Ritik.

## 1. What ran

- **Step 10** on set A's 34 cases, on Sol: 66953953, 1:49:46, exit 0. It made 66 cuts over 16 questions: 34 at
  the takeover (ii) and 32 before the first mention (i).
- **Read on the Mac (no model):**
  ```bash
  ../.venv/bin/python finetune/look/patching.py --handoff results/trackA/setA/step10_patching.json \
      --handoff-out results/trackA/setA/step10_handoff.json --runs-from results/trackA/setA/runs.jsonl.gz \
      --cases-from results/trackA/setA/cases.jsonl --items-from results/trackA/setA/items.jsonl
  ```
- **Fixed first:** `--runs-from`, `--cases-from` and `--items-from` now reach the distance split, which used to read
  Test 2's cases. The display no longer fails on cases without Step 4. Both are tested.

## 2. The pre-registered reading

**Rule** (Oct 29 00:20 log, section A), at cut (ii), share of the hint-row restoration drop at layers 15, 19 and
23, 95% bootstrap clustered by question:
- **replicates:** the lower bound is above 0.375 (3 of the 8 full-attention layers' even share), *and* 15, 19 and 23
  are the three layers with the largest drops;
- **partly:** one of the two;
- **doesn't replicate:** neither.

**Result: replicates.**
- **Share at 15, 19, 23:** **0.90 [0.76, 1.06]** on 31 cuts over 16 questions. The lower bound 0.76 is above 0.375.
  Test 2: 0.90 [0.85, 0.96] on 19 cuts over 9 questions.
- **The three largest drops** are 23 (0.43 [0.30, 0.60]), 15 (0.30 [0.22, 0.39]) and 19 (0.17 [0.11, 0.23]). Next:
  31 (0.07 [0.04, 0.10]), 22 (0.03). Test 2: 23 0.39, 15 0.34, 19 0.17.
- **Three of the 34 cut-(ii) cases are left out** because the clean and hinted runs' logit differences are less
  than 0.5 apart: the same filter as Test 2 (2 of 21 there).

## 3. Also reported (no decision)

| cut | cuts (questions) | share at the 8 full-attention layers | share at 15, 19, 23 | Test 2, share at 15, 19, 23 |
|---|---|---|---|---|
| (ii) all | 31 (16) | 0.92 [0.83, 1.03] | **0.90 [0.76, 1.06]** | 0.90 [0.85, 0.96] |
| (ii) hint beyond the window | 22 (13) | 1.03 [0.95, 1.12] | 1.01 [0.87, 1.19] | 0.92 [0.88, 0.97] |
| (ii) hint within the window | 9 (6) | 0.68 [0.53, 0.81] | 0.62 [0.43, 0.76] | too few questions (2) |
| (i) all | 32 (15) | 0.57 [0.47, 0.68] | 0.51 [0.42, 0.63] | 0.59 [0.48, 0.72] |

- **The answer position gains it at the same layers:** 0.57 [0.46, 0.70] of its rise is at 15, 19 and 23 at cut
  (ii). Test 2: 0.62 [0.57, 0.68].
- **Within the window** (the hint letter within 4,096 tokens of the answer), the sliding layers take part of it, as
  F11 said. On set A that can be read at cut (ii) for the first time (6 questions): 0.62 at 15, 19 and 23.
- **Direct path (F13's swap):** swapping only the prompt's letter (W → O; the reasoning still names W) moves the
  answer off W in 12 of 34 [21, 52%], all to O. Test 2: 13 of 21 [41, 79%]. Set A has no Step 4 deletion runs, so
  F13's comparison with deletion can't be made here.
- **Step 9 on set A** is back too (201 runs; `results/trackA/setA/step9_attention.json`). It isn't read here: no
  rule was fixed for it. Reading it needs one first, for example whether F12's three heads (L19H31, L23H17, L15H31)
  separate followed from resisted runs on set A.

## 4. What changes

- **FINDINGS F26 added.** Story step 3: the readout replicates on 16 questions not used to find it.
- **F11's status:** confirmed on two question sets, one model.
- **REVIEWER_QUESTIONS** thread 1, questions 1 and 2, filled in.
- **CLAIMS** 1.x, set A.
- **TODO:** set A done.

## 5. Source

`results/summaries/trackA/setA/step10_handoff.json` and `step10_patching.json` (numbers only), the figure
`step10_handoff.png`.
