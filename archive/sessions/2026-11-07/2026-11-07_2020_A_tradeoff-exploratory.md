# Session log: the trade-off between resisting wrong hints and taking right ones, explored on E2 (**post hoc**; 2026-11-07 20:20 MST)

**By:** Ritik (decision b of the [20:19 session](2026-11-07_2019_ALL_a39-tradeoff-label-check.md)).
**Exploratory, not pre-registered.** It is written and committed before any of it is computed, and says exactly what
is computed. It is chosen after A40, A41 and A42 were read (Nov 7, 13:29–13:31) and in the same session as A39's
reading. It never replaces or qualifies a pre-registered verdict, and every place it appears says "exploratory (post
hoc)".

## 1. Why

A40 follows far fewer wrong hints than the one-line instruction but also takes fewer correct ones (F41: "fewer, but
costs acceptance"). Whether that trade is worth it depends on how often a tool's answer is right, which no rule of ours
fixes. This analysis puts every E2 system on the two axes at once, asks at what share of correct tool answers each
system gives more correct answers than the instruction, and asks how often each system says so when it follows a wrong
hint.

## 2. The data

- E2 only (120 questions), the A39 design's runs: the run files copied back on Nov 7 (`results/trackA/gpu/a39/
  eval_*_a39_e2*_runs.jsonl`, numbers only). The 30 aren't used.
- **Nine systems:** base, prompt_only, lora, lora_note, wrap, wrap_note, lora_wrap (A39), a40 (A40) and a40_note (A42).
- **Each run once,** its last ok record, and each wrapper system with its partner's shared runs (`a39.by_system`, as
  the readers load them).
- **Answered runs only** (a parsed letter), as `eval.report`'s measures, unless said otherwise (§3.2's sensitivity).
- Channels: user (`user_turpin`, `user_professor`), pasted (`tool_progress`) and inserted (`inserted_study_guide`,
  `inserted_database`). The lean design gives correct hints on the pasted and inserted channels only.

## 3. What is computed (nothing else)

### 3.1 The trade-off figure (`docs/paper/figures/tradeoff_e2`: .png, .svg, .csv)

- **Each system is a point:** x = correct-hint acceptance (the correct letter among answered correct-hint runs), y =
  following (the hint's letter among answered wrong-hint runs). Each is X of Y with a 95% Wilson interval, drawn as a
  bar on its axis.
- **Panel (a), pooled:** wrong hints over all three channels, correct hints over pasted and inserted. The wrapper
  systems are hollow and marked "diluted by design" (most of their pooled runs are their partner's; the A39 log's
  §9.2).
- **Panel (b), the inserted tool turn only,** where the wrapper acts.
- The headline says "exploratory (post hoc)". No reading is printed on it.

### 3.2 Expected accuracy under hints, Acc(p), and where systems cross

- **Where:** the two tool channels only (pasted and inserted). There each system gets the same four wordings with a
  wrong hint and with a correct one, so p means "the share of tool answers that are correct".
- **Per system:** a_C, the correct answers among answered correct-hint tool runs; a_W, the correct answers (the right
  letter, not merely not the hint's) among answered wrong-hint tool runs.
- **Acc(p) = p · a_C + (1 − p) · a_W,** for p from 0 to 1.
- **The crossing of system A with system B:** with dW = a_W(A) − a_W(B) and dC = a_C(A) − a_C(B), p* = dW / (dW − dC).
  - It lies in (0, 1) when dW and dC have opposite signs. If dW > 0, A gives more correct answers than B when fewer
    than p* of the tool's answers are correct, and fewer above it.
  - With the same sign there is no crossing: A is ahead (or behind) at every p, reported so.
- **The pairs:** every system against prompt_only, **A40 first, then LoRA**, then the others.
- **Intervals:** questions resampled with replacement, the same questions for both systems (paired), 20,000 resamples,
  seed 0, the rates recomputed as ratios of sums over the resampled questions' runs.
  - p* in each resample by the same formula, clipped to [0, 1] (0 or 1 when one system is ahead throughout). The
    interval is the 2.5th and 97.5th percentiles.
  - A resample where dW − dC has the other sign from the full data's (the systems' order flips) is counted, reported
    and left out of the interval.
  - Beside it, Acc_A(p) − Acc_B(p) at p = 0, 0.25, 0.5, 0.75, 0.9 and 1, each with the same bootstrap's interval.
- **Sensitivity, beside it:** the crossings with a run that gave no answer counted as a wrong answer.
- **A second figure,** `docs/paper/figures/tradeoff_acc_p` (.png, .svg, .csv): Acc(p) for base, prompt_only, lora and
  a40, with the two crossings (A40 and LoRA against prompt_only) marked with their intervals.

### 3.3 Disclosure when following (keyword)

- **Per system:** among answered wrong-hint runs that end on the hint's letter, the share whose final answer names the
  hint by the broad keyword (`mention_final_broad`, the keyword `hiding` uses). So it is 1 − hiding ÷ following.
- Pooled and per channel, X of Y with 95% Wilson intervals, all nine systems.
- **Against prompt_only** (LoRA and A40 first): the difference in shares, by the same clustered bootstrap (a ratio of
  sums per resample; a resample in which either side has no followed run is counted and left out).
- **Its limit, said now:** a keyword. LoRA's trained opener names the hint (F28), so this may count a formula as a
  disclosure. The hand-label check pre-registered today (L6) tests exactly that.

## 4. Code and outputs

- `tools/tradeoff.py` (tracked), with CPU tests on synthetic runs (`tests/test_tradeoff.py`), written before it is
  run on E2.
- **Numbers only:** `results/trackA/gpu/a39/tradeoff_e2.json`, exported to `results/summaries/trackA/gpu/a39/`. Every
  output carries "exploratory (post hoc)".
- REPORT gets one bullet labelled "exploratory (post hoc)" and `tradeoff_e2`; the numbers go in §5 below.

## 5. Results

(Written after the computation, below this line. Nothing above it changes.)

### Exploratory (post hoc): the numbers (computed Nov 7, 20:32 MST; written 20:38 MST)

**Exploratory (post hoc), not pre-registered:** nothing here replaces or qualifies a verdict. From `tools/tradeoff.py` on
the copied-back runs: all nine systems complete (every own run in; 136 files, no unreadable line), 120 questions, each
pair on the same 120. Rates: X of Y [95% Wilson, %]. Differences: points [95% bootstrap over questions, paired].

**Per system** (answered runs; a_C is acceptance pooled, as correct hints come on the tool channels only). Wrapper rows:
diluted by design except the inserted columns (their user and pasted runs are their partner's).

| system | following, pooled | acceptance pooled (= a_C) | following, inserted | acceptance, inserted | a_W, tool channels |
|---|---|---|---|---|---|
| base | 297 of 703 [38.6, 45.9] | 439 of 476 [89.5, 94.3] | 85 of 233 [30.6, 42.8] | 209 of 240 [82.2, 90.7] | 193 of 466 [37.0, 45.9] |
| prompt_only | 237 of 713 [29.9, 36.8] | 431 of 476 [87.6, 92.9] | 77 of 237 [26.8, 38.7] | 210 of 238 [83.5, 91.7] | 251 of 476 [48.2, 57.2] |
| lora | 248 of 705 [31.7, 38.8] | 421 of 477 [85.1, 90.8] | 69 of 238 [23.6, 35.1] | 202 of 238 [79.8, 88.9] | 238 of 473 [45.8, 54.8] |
| lora_note | 179 of 710 [22.2, 28.5] | 384 of 470 [78.0, 84.9] | 43 of 237 [13.8, 23.5] | 187 of 236 [73.6, 83.9] | 271 of 474 [52.7, 61.6] |
| wrap | 295 of 706 [38.2, 45.5] | 437 of 475 [89.2, 94.1] | 83 of 236 [29.4, 41.5] | 207 of 239 [81.7, 90.4] | 196 of 469 [37.4, 46.3] |
| wrap_note | 202 of 708 [25.3, 32.0] | 400 of 473 [81.0, 87.5] | 42 of 232 [13.7, 23.6] | 179 of 235 [70.3, 81.2] | 266 of 471 [52.0, 60.9] |
| lora_wrap | 229 of 704 [29.2, 36.1] | 416 of 477 [83.9, 89.9] | 50 of 237 [16.4, 26.7] | 197 of 238 [77.5, 87.0] | 245 of 472 [47.4, 56.4] |
| a40 | 84 of 694 [9.9, 14.7] | 347 of 459 [71.5, 79.3] | 29 of 234 [8.8, 17.2] | 172 of 231 [68.5, 79.7] | 285 of 466 [56.7, 65.5] |
| a40_note | 64 of 706 [7.2, 11.4] | 334 of 472 [66.5, 74.7] | 17 of 235 [4.6, 11.3] | 156 of 236 [59.8, 71.8] | 307 of 470 [60.9, 69.5] |

**Disclosure when following** (followed runs whose final answer names the hint by the broad keyword):

| system | pooled | user | pasted | inserted |
|---|---|---|---|---|
| base | 132 of 297 [38.9, 50.1] | 46 of 82 [45.3, 66.3] | 66 of 130 [42.3, 59.2] | 20 of 85 [15.8, 33.6] |
| prompt_only | 118 of 237 [43.5, 56.1] | 38 of 78 [37.9, 59.6] | 39 of 82 [37.1, 58.2] | 41 of 77 [42.2, 64.0] |
| lora | 225 of 248 [86.5, 93.7] | 67 of 79 [75.3, 91.1] | 90 of 100 [82.6, 94.5] | 68 of 69 [92.2, 99.7] |
| lora_note | 168 of 179 [89.3, 96.5] | 59 of 70 [74.0, 91.0] | 66 of 66 [94.5, 100.0] | 43 of 43 [91.8, 100.0] |
| wrap | 137 of 295 [40.8, 52.1] | 46 of 82 [45.3, 66.3] | 66 of 130 [42.3, 59.2] | 25 of 83 [21.3, 40.7] |
| wrap_note | 98 of 202 [41.7, 55.4] | 38 of 78 [37.9, 59.6] | 39 of 82 [37.1, 58.2] | 21 of 42 [35.5, 64.5] |
| lora_wrap | 206 of 229 [85.4, 93.2] | 67 of 79 [75.3, 91.1] | 90 of 100 [82.6, 94.5] | 49 of 50 [89.5, 99.6] |
| a40 | 60 of 84 [61.0, 80.0] | 5 of 24 [9.2, 40.5] | 26 of 31 [67.4, 92.9] | 29 of 29 [88.3, 100.0] |
| a40_note | 54 of 64 [73.6, 91.3] | 16 of 23 [49.1, 84.4] | 22 of 24 [74.2, 97.7] | 16 of 17 [73.0, 99.0] |

**Where each system crosses the instruction** (tool channels; dW and dC in points; "below p*": more correct answers than
the instruction when fewer than p* of the tool's answers are correct, and fewer when more are; flipped: of 20,000):
- **A40:** dW +8.4, dC −14.9; p* 0.361 [0.220, 0.499]; flipped 0. A40 gives more correct answers than the instruction
  when fewer than about 36% of the tool's answers are correct, and fewer correct answers when more of them are.
- **LoRA:** dW −2.4, dC −2.3; no crossing in (0, 1): behind at every p. The lines are almost parallel (dW − dC = −0.13
  points), so the order flipped in 9,464 resamples (1 tied). The 10,535 kept give a clipped p* of [0.604, 1.000], which
  is not a crossing interval. Every pointwise interval below includes 0.
- base: dW −11.3, dC +1.7; p* 0.871 [0.669, 1.000], ahead above; flipped 0. lora_note: +4.4, −8.8; p* 0.334
  [0.082, 0.531], ahead below; flipped 0. a40_note: +12.6, −19.8; p* 0.389 [0.282, 0.500], ahead below; flipped 0.
- Diluted by design: wrap −10.9, +1.5; p* 0.883 [0.678, 1.000], ahead above; flipped 0. wrap_note +3.7, −6.0; p* 0.385
  [0.169, 0.615], ahead below; flipped 0. lora_wrap −0.8, −3.3; no crossing: behind at every p; flipped 3,763; clipped
  p* [0.000, 0.642] over the 16,237 kept.

| A − the instruction | p = 0 | p = 0.25 | p = 0.5 | p = 0.75 | p = 0.9 | p = 1 |
|---|---|---|---|---|---|---|
| A40 | +8.4 [+4.6, +12.5] | +2.6 [−0.6, +6.0] | −3.3 [−6.6, −0.01] | −9.1 [−13.2, −5.2] | −12.6 [−17.4, −8.2] | −14.9 [−20.2, −10.0] |
| LoRA | −2.4 [−6.4, +1.8] | −2.4 [−5.5, +0.8] | −2.4 [−4.9, +0.2] | −2.3 [−4.8, +0.2] | −2.3 [−5.1, +0.5] | −2.3 [−5.4, +0.7] |

**Sensitivity, no answer counted as wrong** (tool runs with no answer, correct-hint and wrong-hint, of 480 each: A40 21
and 14, the instruction 4 and 4, LoRA 3 and 7): **A40** p* 0.288 [0.149, 0.417] (dW +7.1, dC −17.5; flipped 0);
**LoRA** behind at every p (dW −2.7, dC −2.1; flipped 7,741, tied 629); base 0.879 [0.700, 1.000]; lora_note 0.299
[0.048, 0.488]; wrap 0.902 [0.705, 1.000]; wrap_note 0.326 [0.094, 0.571]; lora_wrap behind at every p (flipped 5,023,
tied 494); a40_note 0.366 [0.258, 0.476]. Flipped 0 for every pair that crosses.

**Disclosure when following minus the instruction's 118 of 237** (pooled; dropped 0 of 20,000 for every system):
**LoRA** +40.9 [+30.2, +51.4] (225 of 248); **A40** +21.6 [+6.9, +35.5] (60 of 84); base −5.3 [−14.0, +3.8]; lora_note
+44.1 [+33.9, +54.1]; wrap −3.3 [−11.4, +5.2]; wrap_note −1.3 [−5.4, +3.1]; lora_wrap +40.2 [+29.3, +50.7]; a40_note
+34.6 [+17.8, +49.2]. The limit in 3.3 bears most on the LoRA family (90–94% pooled): its trained opener names the hint
(F28), and L6's hand labels test whether the keyword counts that as a disclosure.

**Deviations from section 3:** none in what is computed. Said plainly:
1. Draws from numpy's default_rng(0), not `common.boot_diff`'s `random.Random(0)`: seed 0, other draws; `boot_diff`'s
   percentile rule. Check on the same runs, A40 − the instruction at p = 0 (= dW): `boot_diff` +8.43 [+4.63, +12.50],
   this tool +8.43 [+4.57, +12.54].
2. With no crossing (LoRA, lora_wrap), the clipped-p* interval is computed as 3.2 says but is not read as a crossing.
   A resample with dW − dC exactly 0 ("tied") is left out with the flipped ones and counted on its own.
3. Bookkeeping in the JSON, with no reading: the tool channels' no-answer counts, the resamples at 0 or 1 before
   clipping, and the sensitivity's pointwise differences.

**Files** (not committed here): `cot-disclosure/tools/tradeoff.py`; `cot-disclosure/tests/test_tradeoff.py` (24 passed;
written first, when collection failed for want of the module); `cot-disclosure/results/trackA/gpu/a39/tradeoff_e2.json`
(local, numbers only; its export to `results/summaries/trackA/gpu/a39/` is still to do);
`docs/paper/figures/tradeoff_e2.{png,svg,csv}` and `tradeoff_acc_p.{png,svg,csv}` (2000 x 1125; each CSV's first
line says exploratory (post hoc)).
