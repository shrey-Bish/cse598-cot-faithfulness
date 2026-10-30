# Session log: set A's Step 9: F12's three heads separate followed from resisted runs again (2026-10-30 10:35 MST)

Project: CSE 598 Group 10, Track A. Read by the rule pre-registered in the 10:10 log (commit `e4e1b1f`) before the
per-run file was on the Mac. FINDINGS F32. **By:** Ritik.

## 1. What ran

- **Sol (Ritik, ~10:10):** `attn_to_hint.py --followup --out /scratch/ragarw68/trackA/setA` on the login node. It
  wrote `step9_reduced.npz`, 201 runs, 3.3 MB, sha256 `825fae1e…`. As expected, the takeover-aligned part skipped
  all 201 runs ("not in Step 3's rows"), and isn't read.
- **Mac:** `python finetune/look/attn_to_hint.py --fixed-heads results/trackA/setA/step9_reduced.npz`, which writes
  `step9_fixed_heads.json`.

## 2. The pre-registered reading

**Rule:** at the answer position, the mean over F12's three heads (L19H31, L23H17, L15H31) of the hint's mass minus
the control span's; followed minus resisted, all channels, paired by question, with a 95% bootstrap clustered by
question. Replicates if the interval lies above 0.

**Result: replicates.** **+0.068 [+0.044, +0.088]**, over 15 questions with both outcomes (56 followed and 145
resisted runs; means 0.120 against 0.051). Test 2: +0.084 [+0.062, +0.105].

## 3. Also reported (no decision)

| | set A | Test 2 (reference) |
|---|---|---|
| hint mass alone (not minus control) | +0.066 [+0.040, +0.089] | +0.084 [+0.062, +0.104] |
| L19H31 | +0.080 [+0.047, +0.109] | +0.115 [+0.077, +0.150] |
| L23H17 | +0.084 [+0.062, +0.106] | +0.086 [+0.062, +0.111] |
| L15H31 | +0.040 [+0.008, +0.071] | +0.051 [+0.023, +0.076] |
| pasted block | +0.087 [+0.070, +0.106] (8 questions) | +0.097 [+0.059, +0.139] |
| inserted + declared | **+0.031 [+0.008, +0.052]** (9 questions) | +0.028 [−0.002, +0.058] |

- **Every head is above 0 on its own.** The order is a little different: L23H17 and L19H31 are about equal here.
- **Inserted + declared:** the interval lies above 0 on set A. On Test 2 it included 0, so F12's "not for inserted
  + declared" is now mixed. The two point estimates are nearly the same (+0.031, +0.028).
- **These three are not set A's top heads by attention mass.** The follow-up's own ranking puts L23H20, L7H3, L27H5,
  L19H2 and L15H1 first, and L15H31 is 10th by hint minus control. The heads that look most at the hint aren't the
  ones that separate the outcomes; F12's heads were fixed in advance and do separate them. Re-ranking on set A
  would have chosen other heads, which is why the rule fixed them.

## 4. Reading

- On 15 questions not used to find them, the three heads F12 named attend more to the hint when the model follows
  it.
- With Step 10 on set A (F26: 0.90 of the drop at 15, 19 and 23), both methods replicate on separate questions:
  where the hint is read, and which heads separate the outcomes.
- One model; attention isn't causation, and Step 10 is the causal half.

## 5. What changes

- **FINDINGS F32.** Story step 3 (both Step 9 and Step 10 replicate). F12's status gets a set A line.
- **CLAIMS 1.4.** **REVIEWER_QUESTIONS** thread 1, question 1. **TODO A32.**
- **Exported:** `results/summaries/trackA/setA/step9_fixed_heads.json`.

## 6. Source

`cot-disclosure/results/summaries/trackA/setA/step9_fixed_heads.json` (numbers only); the reference is Test 2's
`results/trackA/gpu/step9_reduced.npz` with the same function.
