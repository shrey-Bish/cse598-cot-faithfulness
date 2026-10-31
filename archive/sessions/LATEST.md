# Session log: Gate 3 final on all six systems; B1's first-engine runs counted (2026-10-31 16:40 MST)

Project: CSE 598 Group 10, Track A. **By:** Ritik. No calls and no GPU. This ran on the Mac, on the runs files Ritik
copied back from Sol.

## 1. Pushed (Ritik's OK on the 12:40 log)

`4222ff6` is on `trackA-nosol`, `main`, `trackB-main` and `trackC-main` (`c6f4d31..4222ff6` on all four).
- Checks:
  - the full test suite on `4222ff6`: 649 passed;
  - the pre-push check passed, by hand and again as the hook;
  - author and committer are Ritik, with no attribution lines;
  - the three other branches were ancestors of `4222ff6`.
- Sol updates once, straight to `4222ff6`. Beyond `c6f4d31` it changes no `.sh`, `.sbatch` or `.conf` file, so the
  11:50 review still holds. The lines are the 11:50 log's §g with `4222ff6` as the expected commit.

## 2. What Ritik reported (Sol, `sacct` since 06:00)

| job | what | state | elapsed |
|---|---|---|---|
| 66989506, 66989507 | provenance_gen 3/4, 4/4 | TIMEOUT | 6:00:11, 6:00:28 |
| 66989534 | eval lora_tags 2/2 | COMPLETED | 3:09:12 |
| 66989537, 66989539 | eval lora_attn3 1/2, 2/2 | COMPLETED | 3:17:06, 3:13:45 |
| 122956 | provenance_bench | PENDING | — |
| 123022 | qwen8b_step3 | PENDING | — |

Copied to the Mac: every `eval_*_runs.jsonl`, and the first engine's `eval_prov-*_runs.jsonl`.

## 3. What ran

```bash
cd cot-disclosure
../.venv/bin/python finetune/gate3.py --out results/trackA/gpu/eval
../.venv/bin/python tools/export_summaries.py && ../.venv/bin/python tools/export_summaries.py --check   # numbers-only
```

`results/trackA/gpu/eval/`: 12 part files of 465 runs each, so 930 runs for each of the six systems.

## 4. Gate 3, final (`gate3_table.md`)

| system | following (wrong hints) | − base | no-hint accuracy | − base | hiding − base | false disclosure − base | inserted − pasted (base − system) | Gate 3 |
|---|---|---|---|---|---|---|---|---|
| base | 249 of 530 [37, 57%] | — | 58 of 90 | — | — | — | — | |
| prompt only | 179 of 532 [22, 46%] | −13 [−21, −6] | 56 of 89 | −2 | −8 [−12, −4] | −9 [−14, −4] | −15 [−26, −4] | (not trained) |
| LoRA | 197 of 532 [27, 48%] | −10 [−16, −4] | 56 of 89 | −2 | −24 [−32, −17] | +10 [+2, +18] | −8 [−16, +1] | passes |
| tags | 215 of 524 [30, 52%] | −6 [−10, −2] | 60 of 89 | +3 | −6 [−10, −3] | +0 [−4, +4] | −2 [−13, +9] | passes |
| LoRA + tags | 211 of 532 [28, 52%] | −7 [−13, −1] | 59 of 90 | +1 | −25 [−33, −17] | +10 [+2, +19] | −13 [−24, −1] | passes |
| LoRA, layers 15/19/23 | 212 of 534 [29, 51%] | −7 [−13, −2] | 56 of 89 | −2 | −19 [−25, −13] | +5 [−1, +12] | −7 [−18, +4] | passes |

The rule was fixed before any result (PLAN; `eval.report()` since Oct 25; `finetune/gate3.py`). A trained version
passes when three things hold:
- its following minus base has a 95% interval (clustered by question) below 0;
- its no-hint accuracy is within 5 points of base;
- its hiding minus base has an interval reaching 0 or below.

Gate 3 is met if at least one version passes.

## 5. The reading, by the rule

1. **Gate 3 is met: all four trained versions pass all three criteria.**
2. **LoRA + tags changed from the interim reading.** At 11:40, on 810 runs, it failed on following (−3 [−9, +3]).
   On all 930 runs it passes (−7 [−13, −1]). The rule and how it is read are unchanged; the 11:40 reading was
   labelled interim.
3. **The prediction set in advance, for each tag version.** PLAN predicted that tags help more on the inserted tool
   turn (the only channel whose tokens are tagged "tool") than on the pasted block. The statistic is (base − system)
   on the inserted turn minus the same on the pasted block, bootstrapped over questions; it is positive if the
   prediction is borne out.
   - tags: −2 [−13, +9], **not borne out**;
   - LoRA + tags: −13 [−24, −1], **not borne out**, with the interval on the other side: following fell more on the
     pasted block.

   | channel (wrong hints) | base | tags | − base (points) | LoRA + tags | − base (points) |
   |---|---|---|---|---|---|
   | user | 79 of 177 | 63 of 175 | −9 | 73 of 177 | −3 |
   | pasted block | 59 of 88 | 54 of 89 | −6 | 43 of 89 | −19 |
   | inserted turn (declared) | 111 of 265 | 98 of 260 | −4 | 95 of 266 | −6 |
   | inserted turn (undeclared) | 10 of 30 | 10 of 30 | 0 | 10 of 30 | 0 |
   | system | 11 of 30 | 10 of 30 | −3 | 12 of 29 | +5 |

   *Not pre-registered:* the pasted block falls more than the inserted turn for every version, tagged or not:
   - prompt only −15 [−26, −4] (pasted 36 of 90, −27 points);
   - LoRA −8 [−16, +1] (pasted 43 of 89, −19);
   - LoRA on 15/19/23 −7 [−18, +4] (pasted 45 of 87, −15).

   So the reversed sign isn't something the tags do.
4. **No trained version beats the one-line instruction on following.** Each minus prompt_only, paired by question,
   `eval.diff`; *not pre-registered*:

   | version | minus prompt_only |
   |---|---|
   | LoRA | +3 [−1, +8] |
   | tags | +7 [+1, +14] |
   | LoRA + tags | +6 [+1, +11] (interim at 11:40: +10 [+4, +16]) |
   | LoRA on 15/19/23 | +6 [+0.4, +12] |

   Three of the four follow more wrong hints than the instruction; LoRA matches it.
5. **False disclosure** (keyword candidates; the hand labels decide):
   - it rises for LoRA (147 of 532, +10 [+2, +18]) and LoRA + tags (150 of 532, +10 [+2, +19]);
   - LoRA on 15/19/23 has 126 of 534 (+5 [−1, +12]);
   - it doesn't rise for tags (95 of 524, +0 [−4, +4]);
   - it falls for the instruction (50 of 532, −9 [−14, −4]).
6. **Hiding** is a keyword measure. The LoRA versions' trained opener names the hint (by broad keyword: LoRA 456 of
   532, LoRA + tags 469, LoRA on 15/19/23 390; base 146), so for them the hand labels decide. For tags, which has no
   opener (167 of 524), the keyword measure holds.
7. **Correct-hint acceptance:** base 206 of 238, prompt only 206 of 239, LoRA 208 of 239, tags 199 of 237, LoRA +
   tags 207 of 237, LoRA on 15/19/23 204 of 236.
8. **No answer:** base 12, prompt only 10, LoRA 14, tags 20, LoRA + tags 12, LoRA on 15/19/23 12, each of 930.

## 6. B1: the first engine's runs, counted (run IDs and status only; nothing read)

Parts 3/4 and 4/4 ended in TIMEOUT at 6:00, so the first engine's runs are now final:

| configuration | p1 | p2 | p3 | p4 | runs | use (rule log §4) |
|---|---|---|---|---|---|---|
| `prov-a1` | 56 | 23 | 49 | 49 | **177** | the robustness check's old side |
| `prov-deployable-a0.25` | 2 | — | 12 | 3 | **17** | set aside, counts only |
| `prov-oracle-a0.5` | — | — | — | — | 0 | — |

- Every record has status `ok` and none has an `engine_tag`.
- These counts are appended to B1's rule log as §5 (`archive/sessions/2026-10-30/2026-10-30_1715_A_b1-generation-rule.md`).
- `report` takes all 177 alpha = 1 runs.

## 7. Corrections

- **"The 174 alpha = 1 runs."** This phrase was in Ritik's 12:40 decision text and in my 12:40 reply, TODO A30 and
  the supplement's DEVIATIONS line. The budget check's 174 runs were 172 at alpha = 1 and 2 deployable. The budget
  check's own numbers (41 of 174 past 16,000; no answer 1 of 174) were stated as runs and stand.
  - The alpha = 1 count is now 177.
  - TODO and DEVIATIONS are fixed.
  - The rule log's §5 says so.
- **The 11:40 log's channel table:** the system row said −1, which is the change in count. In points it is −3
  (11 → 10 of 30). It is fixed in that log, with a note. FINDINGS never carried that row.

## 8. What changed

- **FINDINGS F28:**
  - a new title, and the final block first (table, prediction per tag version, each minus prompt_only, false
    disclosure, hiding, acceptance, status);
  - the earlier interim blocks kept as written, under "Earlier readings, interim";
  - story item 6 and the header updated.
- **README:** story line 5.
- **PLAN:** E3–E6 and an Oct 31 line.
- **Paper docs:** CLAIMS 1.5, OUTLINE (Gate 3; "three trained versions" dropped from Missing), REVIEWER_QUESTIONS 7.
- **TODO:** A16 and A19 done; A30 (the counts), A36, G3 (done: met, final); L4 (the open question below).
- **`tools/make_supplement.py`:**
  - the Gate 3 table is called interim only when a system is missing or has fewer than 930 runs;
  - its note now covers each version minus prompt_only;
  - the tags-prediction, Gate 3 and false-disclosure entries are updated, and read this log.
- **Regenerated:** `results/summaries/trackA/gpu/eval/*`, the supplement, STATUS, the Gantt.

## 9. Open for Ritik

- **L4's sheets** (fixed Oct 30) hold LoRA's, base's and prompt_only's false-disclosure candidates. They don't hold
  LoRA + tags' 150 or LoRA on 15/19/23's 126. The cautionary claim now has two LoRA versions whose candidates rise.
  Whether to label LoRA + tags' candidates too, as a third sheet, is your call.
- **Qwen3-8B Step 10** isn't in the `sacct` list. The 11:50 log's step 4 submits it after Step 3:
  `$S qwen8b_step10 --estimate 4.3 --dependency=afterok:123022`.
- **B1:** waiting on the bench (122956), then `plan` (the gate inside it).

## 10. Checks and commit

- **Tests:** the full suite, 650 passed. One test is new: the Gate 3 table is called interim only while a system is
  missing or short. It fails on the committed code.
- **The tools:**
  - `check_links`: 0 broken links;
  - `make_supplement --check`: numbers-only; 23 pre-registrations, none unverified; the same 3 mismatches and 12
    source problems as before;
  - `export_summaries --check`: numbers-only.
- **Commit:** as Ritik. **Not pushed:** pushing waits for Ritik's OK.
