# Findings (CSE 598, Group 10)

One entry per finding: the claim in one sentence, the numbers, where they come from, and a
status. Started 2026-10-26; last updated 2026-10-28 (F14, F15, F16, T9 and T10 added; F10's closest-approach
reading refuted; limitations section). Design and plans: [`OVERVIEW.md`](OVERVIEW.md), [`PLAN.md`](PLAN.md).

- **Numbers.** Rates are "X of Y [95% Wilson interval]". Differences are percentage points with
  a 95% bootstrap clustered by question. Mentions are keyword counts (`detect.py`) until the hand
  labels exist.
- **Too few questions** (decided Oct 26). A clustered interval resting on fewer than 5 questions
  degenerates (it can have zero width), so none is reported: the point is followed by "too few
  questions", and no direction is read from it. Group sizes are given in questions as well as
  runs.
- **Sources.** Every source is a tracked file: a numbers-only summary in
  `cot-disclosure/results/summaries/` (no question or reply text), or a progress-round file on
  main. The full runs stay local (gitignored); the command given recomputes the numbers from them.
- **Status.**
  - *confirmed*: measured as stated, and the interval excludes no effect
  - *tentative*: the direction is there, but the interval includes 0, or a confound remains
  - *refuted*: an earlier claim the data contradicts
  - *waiting*: the run is going

Models are on ASU Voyager unless noted. "Served format" is Voyager's chat endpoint; for Olmo 3 7B
Think that meant the Olmo 3 *Instruct* template. "Pinned format" is Olmo 3 7B Think's own Think
template, rendered by us (Track A, from Oct 21).

---

## F1. A hint from a tool moves thinking models more than the same hint from the user

- **Served format** (Test 2: 30 MMLU-Pro items; Olmo 3 7B Think and Qwen3 30B Thinking, one run
  per question and channel):
  - tool 17 of 31 [38, 71%] vs user 2 of 31 [2, 21%]: **+48 points [+31, +65]**
  - among runs not cut off at 16,000 tokens: 17 of 21 [60, 92%] vs 2 of 21 [3, 29%]
- **Pinned format** (Step 2b: Olmo 3 7B Think only, its 20 hinted Test 2 questions):

  | channel | picked the hint letter |
  |---|---|
  | user (1 run per question) | 7 of 20 [18, 57%] |
  | tool, pasted (3 per question) | 40 of 60 [54, 77%] |
  | tool, inserted turn (3) | 24 of 60 [29, 53%] |
  | tool, inserted + declared (3) | 34 of 60 [44, 68%] |

  - all tool channels: 98 of 180 [47, 62%]; tool − user **+19 points [−2, +40]**
  - the same letter with no hint: 2 of 40 [1, 17%]
- **Source.**
  - `docs/progress/RESULTS_SUMMARY.json` (`expB.cells`) and
    `cot-disclosure/results/progress/expB_cued.jsonl` (on main)
  - `cot-disclosure/results/summaries/trackA/base_format_runs.jsonl`, via
    `python finetune/base_format.py --report`
- **Status.** *confirmed* in the served format (two thinking models). *tentative* for Olmo 3 7B
  Think alone in its own format: the user channel rose (F2), and the interval includes 0.

## F2. The serving format changed Olmo 3 7B Think's hint following, but how much is unknown

The pinned runs followed more hints than the served runs. Two differences besides the format
confound the comparison: the token budget and the run counts.

- **User:** 2 of 20 [3, 30%] served → 7 of 20 [18, 57%] pinned, **+25 points [+0, +50]**. One run
  per question in both.
- **Pasted tool:** 10 of 20 [30, 70%] served (1 per question) → 40 of 60 [54, 77%] pinned (3 per
  question), **+17 points [−10, +43]**.
- **The budget confound reverses the order.**
  - Served: a reply cut off at 16,000 tokens was no answer, which was 9 of the 20 pasted runs.
  - Pinned: cut-off runs were continued up to the 65,536-token context; 1 of 60 was still cut off.
  - Among answered runs: served 10 of 11 [62, 98%] vs pinned 40 of 59 [55, 78%].
- **Fixed between the two:** the same checkpoint behind both (Oct 21 echo check, T3) and the same
  per-letter no-hint baseline, 2 of 40 in both.
- **Source.** `cot-disclosure/results/summaries/trackA/base_format_runs.jsonl` (the "Test 2,
  served format" column of `base_format.py --report`); `docs/progress/RESULTS_SUMMARY.json`.
- **Status.** *tentative* (confounded). Not separable without rerunning the served format with
  continuation.

## F3. The private reasoning mentions the hint; the final answer almost never does

- **Test 1** (24 puzzles, user hint; Olmo 3 7B Think, Olmo 3 32B Think, Qwen3 30B Thinking; 216
  hinted runs, served format):
  - private 208 of 216 [93, 98%] vs final 8 of 216 [2, 7%]
  - both 8; private only 200; final only 0; neither 8
- **Test 2, when the tool hint won** (17 runs): the private reasoning named the tool in 16 of 17
  [73, 99%], the final answer in 6 of 17 [17, 59%].
- **Pinned format** (Step 2b, final answer, Olmo 3 7B Think): pasted 27 of 60 [33, 58%], inserted
  12 of 60 [12, 32%], inserted + declared 17 of 60 [19, 41%], user 0 of 20 [0, 16%].
- **Caveat.** The private keyword also fires with no hint (22 of 72 Olmo 3 7B Think no-hint runs:
  "the user asks…"), so 208 is an upper bound.
- **Source.** `docs/progress/RESULTS_SUMMARY.json` (`pilot.mentions.<model>.private_mentions_hinted`
  and `final_mentions_hinted`); `docs/OVERVIEW.md` §6; `base_format.py --report`.
- **Status.** *confirmed* as keyword counts. Hand labels (two raters, Cohen's kappa) *waiting*.

## F4. Known answers are overridden, mostly late in the reasoning, on a few questions

- **"Sure" questions:** both Step 2b no-hint runs answered and correct; 11 of 20.
- **Followed on sure questions:** **43 of 110 hinted runs [30, 48%]** ended on the hint letter.
- **When:** 26 of the 43 [46, 74%] took over at or after half the reasoning ("late"); 9 led from
  before any reasoning; 8 took over in between.
- **Concentrated:** the 43 fall on 9 of the 11 questions (per question: 8, 8, 7, 5, 5, 4, 3, 2, 1,
  0, 0), and the top 3 questions hold 23 of 43 [39, 67%].
- **Unsure questions,** for contrast: 62 of 89 [59, 78%].
- **Source.** `cot-disclosure/results/summaries/trackA/takeover_runs.jsonl` and
  `before_takeover.jsonl` (`concentration`); `python finetune/look/takeover.py --report`.
- **Status.** *confirmed*, but on 9 questions. The 26 late runs (at most 3 per question: 21) are
  the cases for Steps 4 and 10.

## F5. The hint is the starting answer, and the lead swings many times before it settles

Early answering (Lanham et al. 2023): after each sentence, close the reasoning and force
"Answer: (". A forced answer is off-distribution for a thinking model, most of all before any
reasoning.

- **Before any reasoning** (k = 0):
  - the hint letter leads in **198 of 199 hinted runs [97, 100%]**
  - the correct letter leads in 0 of 199 [0, 2%]
  - with no hint, the correct letter leads in 5 of 20 [11, 47%]
- **Resisted runs:** the hint letter still leads at or after half the reasoning, then loses for
  good, in 57 of 94 [51, 70%].
- **Swings:** after the first fifth of the reasoning, the hint letter took the lead 1,294 times.
  46 of those leads held to the end (the takeovers that begin after the first fifth); 1,248 were
  lost again.
- **Just before a lead begins,** the own answer leads about equally often whether the lead holds
  or not: 67% vs 68%, **−1 point [−16, +19]**.
- **Source.** `cot-disclosure/results/summaries/trackA/takeover_per_run.jsonl` (k = 0 letters,
  types), `before_takeover.jsonl` (`onsets_all`); figures `takeover_mean_curves.png`,
  `takeover_points.png`.
- **Status.** *confirmed*, as forced-answer readings.

## F6. Mentions mark the hint being in play, not the hint winning

- **The comparison:** a hint mention in the takeover sentence or the 2 before it.
  - late takeovers: **25 of 57 [32, 57%]**
  - resisted runs at their closest approach (where the hint letter peaks, after the first fifth):
    **43 of 94 [36, 56%]**
  - windows in the same runs at the same relative position: 12% [8, 17%]
- **Reading.** Mentions cluster where the hint is strongest, whether or not it then wins.
- **Source.** `cot-disclosure/results/summaries/trackA/takeover_per_run.jsonl`
  (`mention_within_2_before_takeover`, `closest_approach_mention`); `takeover.py --report`.
- **Status.** *confirmed* (keyword counts). The earlier claim, "a mention just before the
  takeover triggers it," was based on a 7% any-window baseline and is *refuted* by this
  comparison and by F5's matched onsets. F14 is the attention-level counterpart.

## F7. Deleting the reasoning's mentions moves the answer at the cut, not the final answer

**Design.** 19 cases (late takeovers on sure questions, at most 3 per question, 9 questions), cut
at the takeover point. The hint stays in the prompt.

| | mentions deleted | length-matched control | unedited |
|---|---|---|---|
| forced answer at the cut goes back to the own answer | 7 of 19 [19, 59%] | 1 of 19 [1, 25%] | the hint letter, by definition |
| continuations end on the own answer (3 per case) | 5 of 57 [4, 19%] | 4 of 57 [3, 17%] | 1 of 57 [0, 9%] |
| continuations end on the hint letter | 44 of 57 | 51 of 57 | 53 of 57 |
| …and mention the hint again after the cut | 34 of 44 [63, 87%] | 46 of 51 [79, 96%] | 46 of 53 [75, 93%] |

- **Differences.**
  - forced answer, deleted − control: **+32 points [+11, +56]**
  - continuations, deleted − control: +2 [−5, +11]
  - continuations, deleted − unedited: +7 [+0, +19]
- **Reading.** At the cut, the reasoning's repetition carries the hint in 7 of 19 cases (F13: the
  prompt's letter, read directly, does more). Given room to go on, the model goes back to the hint
  in the prompt, and mostly names it again.
- **Source.** `cot-disclosure/results/summaries/trackA/deletion_runs.jsonl` and
  `deletion_remention.jsonl`; `python finetune/look/deletion.py --report`.
- **Status.** *confirmed* for the forced answer. For continuations, no effect beyond the control.

## F8. The hint's pull may weaken once its last mention leaves the 4,096-token window

24 of Olmo 3 7B's 32 layers attend only to the last 4,096 tokens. The test compares Step 3 probes
within runs: the log-odds of the hint letter vs the own answer, just outside minus just inside a
distance cutoff (bands of 512 tokens).

| distance | at 4,096 | 4,096 minus the placebo mean | placebos 2,048 / 3,072 / 5,120 / 6,144 |
|---|---|---|---|
| since the last mention | **−0.68 [−1.28, −0.26]** (75 runs) | **−0.59 [−1.25, −0.12]** | +0.09 / −0.26 / −0.05 / −0.15 |
| since the prompt's hint | −0.52 [−0.85, −0.22] (133 runs) | −0.44 [−0.77, −0.12] | −0.05 / −0.32 / −0.00 / +0.04 |

- **By outcome** (since the last mention, at 4,096): mostly resisted runs, −1.15 [−2.24, −0.42];
  followed −0.28 [−0.72, +0.21].
- **Robustness.** Unchanged without the probes where a letter was outside the top 10.
- **Sensitivity.** Adding the 50 runs on questions whose no-hint runs split (own answer = the key)
  weakens it: −0.38 [−0.88, +0.06], contrast −0.34 [−0.85, +0.07].
- **Source.** `cot-disclosure/results/summaries/trackA/window_reach.json` (+ `.png`);
  `python finetune/look/window_reach.py`.
- **Status.** *tentative*. 149 runs on 15 questions, and information also passes forward through
  intermediate tokens. Step 10 (F11) shows the full-attention layers read the prompt's hint at any
  distance, so a window effect would concern the reasoning's mentions, not the prompt's hint.

## F9. Step 8: a rule set in advance failed on 4 positions; the weights still match

**Step 8 asks whether Voyager serves the checkpoint we load on Sol.** It compares a local
forward pass with Voyager's echo log-probs on the Step 1 text (5,185 tokens, echoed 4 ways)
and the canary (530 tokens). The Instruct checkpoint is the negative control. The rule was fixed
on Oct 26, before the result (PLAN, Track A).

| condition | result |
|---|---|
| (a) no top-token mismatch outside near-ties (top two within 0.1) in the first 2,047 tokens, bf16 and fp32 | **fails**: 4 positions, gaps 0.113–0.140 |
| (b) mean difference at least 10× below the Instruct control's | holds: 26–27× (Step 1 text), 10.4× (canary, narrow) in bf16; 32× and 12× in fp32 |
| (c) the control clearly fails (a) | holds: 277 / 280 first-part mismatches, at least 17 / 16 outside near-ties |

- **The 4 positions.**
  - Step 1 text, position 1,130: 1 of its 19 (bf16) and 15 (fp32) first-part mismatches. The
    two tokens tie locally (gap 0.000 bf16, 0.011 fp32); Voyager's gap is 0.124.
  - Canary: 3 of 8 (bf16) and 2 of 9 (fp32), local gaps 0.113–0.140.
  - Every other first-part mismatch is a near-tie.
  - Beyond 2,047 tokens (the Step 1 text), there are 30–48 mismatches, all near-ties. The control
    has 332–337 outside near-ties there.
- **Supporting evidence, not pass/fail.** The fp32 first-part maximum is 0.27 on the Step 1 text
  and 0.59 on the canary, against the old 0.01 limit.
- **By the rule:** Voyager isn't serving this checkpoint. The rule is not changed after the fact.
- **The weights on Sol are d97e442's.** All three `.safetensors` files have the sha256 of
  `olmo3_7b_think_d97e442.json` (`sha256sum` on Sol, Oct 26).
- **Why we still conclude Voyager serves the same weights.** This is a judgment, not the rule's
  verdict. The failures look like different serving arithmetic (Voyager's kernels against
  Hugging Face sdpa):
  - The local fp32 pass is as far from Voyager as the bf16 pass (mean 0.0100 vs 0.0118).
  - The Instruct checkpoint is 27× further away.
  - All 4 gaps are within 0.04 of the line.
  - Local forced answers match Voyager's results: 21 of 21 at Step 10's takeover cuts (Step 3's
    letter) and 199 of 199 at the end of the reasoning (Step 9: the run's final letter).
- **Consequence.** Gate 3 runs every system on the same Sol stack, base and prompt-only included.
  Voyager's base numbers stay as the Steps 2b–4 results and a cross-check (PLAN, Track A).
- **Source.** `cot-disclosure/results/summaries/trackA/step8_verdict.json`, via `python
  finetune/gpu/step8_verdict.py --sha256sum results/trackA/gpu/weights_sha256.txt`.
- **Status.** *confirmed*: the rule fails (a) and holds (b) and (c), and the Sol weights are
  d97e442. "Voyager serves the same weights" is *tentative*, and nothing depends on it.

## F10. Step 9: tool hints get less attention at the answer than user hints, yet move it more

One forward pass per hinted Step 2b run (199 runs, 20 questions). Measured: the attention mass
from the answer position ("(" of "Answer: (") to the hint, per layer and head. Reported here on the
8 full-attention layers, the only ones that reach the hint in 174 of 199 runs. Two measures:
- **hint − control:** the hint's mass minus that of a question-stem span of the same length
- **per token:** the hint's mass divided by its length

**Tool − user** (179 vs 20 runs, 20 questions in both):

| measure | tool − user |
|---|---|
| hint − control | **−8.1e-3 [−1.0e-2, −6.1e-3]** |
| per token | −8.9e-4 [−1.0e-3, −7.7e-4] |
| the letter | −2.0e-3 [−3.2e-3, −6.7e-4] |

- **The two orders don't match.**
  - Attention (hint − control, channel means): user 0.023 > pasted 0.022 > inserted 0.013 >
    inserted + declared 0.011. Per token gives the same order.
  - Hint following (Step 2b): pasted 40 of 60 > inserted + declared 34 of 60 > inserted 24 of
    60 > user 7 of 20.
  - Caveat: the channels differ in more than the source. The hint sits in a user turn or a tool
    turn, at a different distance from the answer, and with different wording and length.
- **Followed − resisted** (105 vs 94 runs, 16 questions in both):
  - hint − control **+5.6e-3 [+2.9e-3, +8.2e-3]**
  - the letter +1.8e-3 [+4.8e-4, +3.1e-3]
  - per token +1.1e-4 [−3.0e-5, +2.3e-4]
  - by channel (hint − control):
    - inserted +4.9e-3 [+1.4e-3, +8.1e-3] (9 questions)
    - pasted +6.1e-3 [+2.4e-3, +9.8e-3] (9)
    - inserted + declared +9.7e-4 [−1.8e-3, +3.6e-3] (10): no difference
    - user: no question has both outcomes
- **The top heads sit in full-attention layers. That mostly follows from the window and is not a
  finding.** All 10 top heads, ranked by hint mass or by hint − control, are in full-attention
  layers, 8 of them in layers 15, 19 and 23 (F12).
- **Where the sliding layers can reach the hint** (25 runs on 6 questions), 7 of the 10 top heads
  are in sliding layers. This matches Step 10's cut (i) split (F11). These runs have too few
  questions per group for any comparison: no direction is read from them.
- **Attention from the reasoning around the takeover: the first reading is *refuted* (T9).**
  - The first reading aligned followed runs on the takeover and resisted runs on their closest
    approach. Attention to the hint rose more at the closest approach (+0.012 against +0.005,
    difference −0.0076 [−0.0123, −0.0016]), read as "resisted runs look at the hint more".
  - The closest approach is picked where the hint is strongest. Anchored the same way in both
    (every lead onset after the first fifth), temporary leads in followed and resisted runs
    don't differ: **−0.7e-3 [−4.2e-3, +2.0e-3]** (16 questions in both). The difference came from
    how the anchor was picked. What the matched version does show is F14.
- **Source.** `cot-disclosure/results/summaries/trackA/step9_followup.json` (`run_sets`,
  `top_heads`, `aligned`, `onsets_matched`) and `step9_attention.json`.
- **Status.**
  - *confirmed*: tool − user on every measure, and followed − resisted on hint − control,
    pooled and for the inserted and pasted channels
  - *tentative*: per token
  - *refuted*: "resisted runs look at the hint more" (closest-approach anchor, T9)

## F11. Step 10: the hint's effect leaves its tokens at full-attention layers 15, 19 and 23

**Setup.** F4's 21 cases, all tool hints, cut (i) before the first hint mention (19 cases) and
cut (ii) at the takeover (21). The clean prompt is the same prompt with the hint letter W
replaced by the own answer O: same length, one token different.
- **The patch:** copy the clean run's output of one layer into the hinted run, at the hint's
  tokens, the reasoning, or the answer position.
- **Restoration:** 1 = the clean answer's logit difference. 19 of 19 cuts at (i) and 19 of 21 at
  (ii) are usable; 2 have a gap under 0.5. Sanity checks pass on 40 of 40.

**Restoring at the hint's tokens stays near 1 up to layer 14.** Patching there still gives the
clean answer, so the information hasn't left those tokens yet. It then falls in steps.

- **The drop at a layer** is restoration before it minus after it: what that layer reads out of
  the hint's tokens. The drops add up to 1.

  | cut | cuts (questions) | share of the drop at the 8 full-attention layers | share at 15, 19, 23 |
  |---|---|---|---|
  | (ii) all | 19 (9) | 0.95 [0.84, 1.05] | **0.90 [0.85, 0.96]** |
  | (ii) hint beyond the window | 17 (9) | 1.00 [0.92, 1.07] | 0.92 [0.88, 0.97] |
  | (ii) hint within the window | 2 (2) | too few questions | too few questions |
  | (i) all | 19 (9) | 0.68 [0.55, 0.84] | 0.59 [0.48, 0.72] |
  | (i) hint beyond the window | 9 (6) | 0.93 [0.85, 0.99] | **0.81 [0.71, 0.89]** |
  | (i) hint within the window | 10 (5) | 0.46 [0.38, 0.50] | **0.39 [0.33, 0.43]** |

- **Per layer at cut (ii):** 15: 0.34 [0.27, 0.42], 19: 0.17 [0.14, 0.21], 23: 0.39 [0.34, 0.43].
  Every other layer drops less than 0.05.
- **The answer position gains it at the same layers:** 0.62 [0.57, 0.68] of its rise is at 15,
  19 and 23 at cut (ii), and 0.45 [0.32, 0.59] at cut (i). The rest comes at the last layers.
- **Reading.**
  - That the readout sits in full-attention layers mostly follows from the window. When the
    hint letter is within 4,096 tokens of the answer (10 cuts at (i)), the sliding layers take
    over half of it.
  - What the window doesn't explain is which of the 8 full layers do it: the middle three, 15,
    19 and 23. Layers 3, 7, 11, 27 and 31 read almost nothing.
  - The readout is direct: by layer 23 the answer position holds 0.80 of the effect (cut (ii)).
- **Source.** `cot-disclosure/results/summaries/trackA/step10_handoff.json` and
  `step10_patching.json`; figure `figures/step10_handoff.png`; `python finetune/look/patching.py
  --handoff results/trackA/gpu/step10_patching.json`.
- **Status.** *confirmed* on these 19 + 19 cuts (9 questions, one model). At cut (ii) only 2 cuts
  (2 questions) have the hint within the window: too few to read.

## F12. Attention and patching point at the same three layers, and the same heads separate outcomes

- **Attention (Step 9):** 8 of the 10 top answer → hint heads are in layers 15, 19 and 23: L15H31,
  L15H1, L15H19, L15H0, L19H31, L19H2, L23H20 and L23H17. They were picked on all runs pooled, not
  by outcome.
- **Patching (Step 10):** layers 15, 19 and 23 are where the hint's effect leaves its tokens
  (F11).
- **Followed − resisted, the mean over these 8 heads** (105 vs 94 runs, 16 questions in both):
  **+0.040 [+0.021, +0.057]** (hint mass; hint − control gives the same). Three heads carry it:

  | head | followed − resisted |
  |---|---|
  | L19H31 | **+0.115 [+0.077, +0.150]** |
  | L23H17 | **+0.084 [+0.060, +0.108]** |
  | L15H31 | **+0.051 [+0.023, +0.076]** |
  | the other five (L23H20, L15H1, L15H19, L19H2, L15H0) | each interval includes 0 |

- **By channel** (mean over the 8):
  - inserted +0.049 [+0.016, +0.080]
  - pasted +0.044 [+0.015, +0.073]
  - inserted + declared +0.004 [−0.019, +0.027]: no difference, as in F10
- **Tool − user in these heads:** +0.010 [−0.005, +0.026], which includes 0.
- **Source.** `step9_followup.json` (`readout_heads_followed_vs_resisted`) and `step9_attention.json`
  (`top_heads`); `step10_handoff.json`.
- **Status.** *confirmed*: the layer agreement (two independent methods), and followed > resisted in
  these heads pooled over channels and for the inserted and pasted channels. Not for inserted +
  declared.

## Mechanism, in one paragraph (Steps 8–10, tentative as a whole)

Three full-attention layers, 15, 19 and 23, read the hint's letter straight from the prompt and pass
it to the answer: they hold 0.90 [0.85, 0.96] of the drop in hint-token restoration at the takeover
(F11). The reasoning positions relay at most 0.26 of it (F13). Within those layers, heads L19H31,
L23H17 and L15H31 look at the hint more when the model follows it (F12). But tool hints don't get
more of this attention than user hints; they get less (F10), while moving the answer more (F1). So
the extra trust in tools lies in what is read at the hint, not in how much it is attended to.
In the reasoning, the hint letter takes the lead at sentences that look back at the hint, whether
or not the lead lasts (F14).

**Link to the fix.** Source tags add a learned vector to every token marking where it came from (at
the hint's tokens: a tool). They change what these heads read there, not where they look. After training, the look-inside
rerun on the best version (Step 13) checks both possibilities:
- (a) attention in L19H31, L23H17 and L15H31 drops, or
- (b) it stays while the answer stops following: the model still looks, but discounts what it
  reads.

The check is Step 9's readout-head comparison and Step 10's drops at 15, 19 and 23 (PLAN, Track A,
mechanism check).

## F13. Direct vs written: at the takeover, the prompt's letter does more than the repetition

At cut (ii) the hint can reach the answer in two ways:
- **Direct path:** the prompt's hint letter, read at the answer through layers 15, 19 and 23.
- **Written path:** the reasoning's own repetition of the hint.

Two experiments each take one path away. They use different case sets (21 vs 19: Step 4 has
nothing to delete in the 2 cases with no mention before the takeover) and different stacks
(Step 4 on Voyager, Step 10 local; F9).

| | what is removed | what stays | forced answer |
|---|---|---|---|
| Step 10, clean run | the prompt's W (the hint now names O) | the reasoning names W | **off W in 13 of 21 [41, 79%]** (10 to O, 3 to another letter); W in 8 |
| Step 4, deletion | the reasoning's mentions | the prompt's W | **back to the own answer in 7 of 19 [19, 59%]** (8 W, 4 another letter) |

- **Per case** (the 19 in both):

  | reading | what happens | cases |
  |---|---|---|
  | both paths needed | either removal moves the answer | 5 |
  | the prompt carries it | only the swap moves it | 4 |
  | the writing carries it | only the deletion moves it | 2 |
  | either path suffices | neither moves it | 4 |
  | another letter | Step 4 ends on a third letter | 4 |

  Different cases respond to the two manipulations; no single path carries the hint everywhere.
- **The written repetition alone holds W in 8 of 21,** even against a prompt whose hint now names
  O.
- **The reasoning positions' activations** restore up to 0.26 [0.14, 0.43] at layer 17 at cut
  (ii), and 0.08 [0.01, 0.17] at cut (i).
  - The reasoning text is the same in the clean and hinted runs, so this is the relay of the
    prompt's letter through those positions: they read it at layer 15 and pass it on.
  - It does not measure the effect of the written repetition.
- **Reading.** Restoration comes mostly through the hint's tokens, read directly by
  full-attention layers (F11). The relay through the reasoning positions is at most 0.26. This
  weakens the idea that "the reasoning carries the hint": at the takeover, the prompt's letter
  read directly does more. The repetition is decisive in a minority of cases (2 of 19 alone; 5
  more where both are needed).
- **Revises F7's reading.** F7 said "at the cut, the reasoning's repetition carries the hint." It
  does in some cases, not in most.
- **Source.** `step10_handoff.json` (`paths_at_cut_ii`: per case, totals, cross table);
  `deletion_runs.jsonl`.
- **Status.** *confirmed* as measured. The per-case typology is *tentative*: 19 cases, two
  stacks.

## F14. The hint takes the lead when the reasoning looks back at it, whether or not it keeps it

**Setup.** Step 9's attention from each reasoning sentence to the hint (the 8 full-attention
layers, hint − control), around every point after the first fifth where the hint letter becomes
the leading forced answer (Step 3's dense curves: 199 runs, 20 questions).
- **Rise:** the mean over the onset sentence and the 2 before, minus the same run's sentences 6–15
  before. Averaged per run, then clustered by question.
- **Onsets:** lasting (the takeover: the hint keeps the lead to the end) or temporary (lost
  again). F5's counts (46 and 1,248) also required the run's own no-hint answer; this doesn't.
- **Placebo:** every other sentence after the first fifth, not within 2 of an onset, in the same
  runs.

| anchor | onsets (runs, questions) | rise above 0 | rise, hint − control |
|---|---|---|---|
| lasting (the takeover) | 65 (65, 18) | 55 of 65 | **+4.8e-3 [+2.7e-3, +7.1e-3]** |
| temporary | 1,653 (123, 19) | 1,056 of 1,653 | **+3.4e-3 [+2.0e-3, +5.3e-3]** |
| placebo | 93,005 sentences (199, 20) | — | +0.05e-3 [−0.10e-3, +0.23e-3] |

- **Against the placebo:** lasting +4.7e-3 [+2.7e-3, +7.0e-3] (18 questions in both); temporary
  +3.4e-3 [+2.0e-3, +5.3e-3] (19). Per token gives the same.
- **Reading.** The hint gains the lead when the reasoning looks back at it, whether or not it
  keeps it. This is the attention-level counterpart of F6: looking back marks the hint being in
  play, not the hint winning.
  - It is an average, not every onset: 55 of 65 lasting and 1,056 of 1,653 temporary onsets have
    a positive rise.
  - It is an association within the same 3 sentences; which comes first isn't tested.
- **Lasting vs temporary at the onset: no difference shown.**
  - All onsets: +1.7e-3 [−0.5e-3, +4.2e-3] (17 questions in both). Isolated onsets (no other
    onset in the 15 sentences before; 44 vs 605): +1.3e-3 [−1.5e-3, +3.9e-3]. Both include 0.
  - Within followed runs only (the takeover vs the same runs' earlier temporary leads): +2.2e-3
    [+0.2e-3, +4.5e-3], but the isolated version includes 0 (+2.2e-3 [−0.3e-3, +4.4e-3]). Per token
    it excludes 0 in both: +8.8e-5 [+1.7e-5, +17.4e-5] and +9.5e-5 [+1.1e-5, +18.2e-5].
  - In followed runs every temporary lead comes before the takeover, so this comparison also
    differs in position in the run.
- **After the onset (descriptive only).** The takeover's spike stays above the level before it for
  about 5 sentences: +10.3e-3 at the onset, +4.8e-3 two sentences later (interval excludes 0), back
  at the earlier level by the sixth. Temporary leads drop back within 2: +4.3e-3 at the onset,
  +2.1e-3 one sentence later (interval includes 0), −0.1e-3 two later. After a lasting takeover
  the reasoning goes on to use the hint by definition, so this can't explain the outcome.
- **Source.** `cot-disclosure/results/summaries/trackA/step9_followup.json` (`onsets_matched`:
  `groups`, `comparisons`, `placebo`, `curves`); figure `step9_onsets.png`; onsets from
  `hint_onsets.jsonl` (Step 3). `python finetune/look/attn_to_hint.py --followup --from-reduced
  results/trackA/gpu/step9_reduced.npz` (Mac, no GPU) reproduces Sol's numbers to 1e-14 and adds
  the placebo.
- **Status.** *confirmed*: the rise at lasting and at temporary onsets, against the placebo.
  *tentative*: lasting > temporary (followed runs only, not robust to isolated onsets). The
  spike's length: descriptive.

## F15. Track B, Qwen3 30B Thinking: tool and system hints move it, the user's doesn't; after a real tool call the final answer hides the tool

**Setup.** Track B (Oct 27–28, Voyager, served format): 54 questions (24 pilot puzzles, 30
MMLU-Pro) × 5 conditions × 3 runs = 810 runs at the 32,768-token budget, every one with an answer.
Each hint names the same wrong letter.
- **user:** the hint is in the question.
- **tool, pasted:** a tool block is pasted into the user turn.
- **tool, real call:** the model has a lookup tool, and the hint comes back only if it calls it.
- **system note:** the hint is in the system prompt.

| channel | following | above the no-hint baseline | final answer names the hint, when following |
|---|---|---|---|
| user | 3 of 162 [1, 5%] | +1 [−1, +2] | 0 of 3 |
| tool, pasted | 59 of 162 [29, 44%] | **+35 [+25, +46]** | 54 of 59 [82, 96%] |
| tool, real call | 54 of 162 [27, 41%] | **+32 [+23, +42]** | **3 of 54 [2, 15%]** |
| system note | 57 of 162 [28, 43%] | **+34 [+25, +44]** | 50 of 57 [77, 94%] |

- **No hint:** right in 151 of 162 [88, 96%]; the hint letter in 0 of 162 [0, 2%].
- **Gate 2** (tool − user, paired by question, 54 questions): pasted **+35 points [+24, +46]**,
  real call **+31 [+22, +42]**. Both clear.
  - At the 16,000 cut: +34 [+23, +45] and +32 [+22, +43].
  - 23 of 810 runs [2, 4%] go past 16,000 tokens. All are on MMLU-Pro, and none are real-call runs.
- **The real call:**
  - The model called the tool in 54 of 162 runs [27, 41%], on 29 questions.
  - Following when it called: 54 of 54 [93, 100%]. Without a call: 0 of 108 [0, 3%]. So this
    channel's following is its call rate.
  - When it called, the private reasoning named the tool in 54 of 54 and the final answer in 3 of 54.
- **Final answers name pasted and system hints.** With a pasted block or a system note, the final
  answer names the hint in most runs that follow it (table). The user's hint is named in 31 of 162
  final answers, all in runs that didn't follow it.
- **The two sets differ:**

  | set (no-hint right) | user | tool, pasted | tool, real call (calls) | system note | Gate 2 pasted / real |
  |---|---|---|---|---|---|
  | puzzles, 24 q (72 of 72) | 0 of 72 [0, 5%] | 5 of 72 [3, 15%] | 4 of 72 [2, 13%] (4) | 7 of 72 [5, 19%] | +7 [+1, +12] / +6 [+1, +11] |
  | MMLU-Pro, 30 q (79 of 90) | 3 of 90 [1, 9%] | 54 of 90 [50, 70%] | 50 of 90 [45, 65%] (50) | 50 of 90 [45, 65%] | +57 [+41, +71] / +52 [+39, +66] |

  - Sureness doesn't explain the gap. On MMLU-Pro questions it gets right in every no-hint run
    (23 questions), it still follows the pasted block in 34 of 69 [38, 61%], the real call in 39 of
    69 [45, 68%] and the system note in 31 of 69 [34, 57%]. On the puzzles, every question is
    sure.
- **Sure vs unsure, both sets** (47 sure questions; the 7 unsure are all MMLU-Pro):
  - pasted: 39 of 141 [21, 36%] vs 20 of 21 [77, 99%]
  - real call: 43 of 141 [23, 39%] vs 11 of 21 [32, 72%]
  - system note: 38 of 141 [20, 35%] vs 19 of 21 [71, 97%]
  - user: 2 of 141 [0, 5%] vs 1 of 21 [1, 23%]
- **Length** (median reply tokens): no hint 3,763; user 4,545; pasted 8,794; system note 9,015;
  real call 2,470 (3,969 with a call, 2,249 without).
- **Reading.**
  - **Source matters.** This model ignores the user's hint (+1 point above baseline), although its
    private reasoning names that hint in 158 of 162 runs. A tool or a system note moves it by about
    a third of all runs.
  - **The set matters.** Almost all of that happens on MMLU-Pro: knowledge questions, where it
    also calls the lookup tool. On the puzzles, which it works out (72 of 72 right with no hint), it
    rarely calls the tool and rarely follows.
  - **The real call is the hidden case.** After a real call, it took the tool's letter every time
    and its final answer cited the tool 3 times in 54. A pasted block or a system note is cited
    instead. This narrows F3 for this model: for these two channels, the final answer often does
    name the hint.
  - **F1 holds with more data.** F1's served-format gap holds for Qwen3 Thinking alone with 3 runs,
    54 questions and the full budget.
- **Source.**
  - `cot-disclosure/results/summaries/trackB/trackB_report.json` and `trackB_report_by_set.json`
    (`budget_32768` / `cut_16000`, the `qwen3-30b-a3b-thinking-2507` rows)
  - per-run flags: `trackB_runs.jsonl`
  - recomputed with `python progress/trackB_report.py --by-set` (Mac, no calls). Mentions are
    keyword counts (`detect.py`).
- **Status.**
  - *confirmed*: tool and system hints above the user's (Gate 2) on 54 questions × 3 runs, and
    following after a real call (54 of 54).
  - *confirmed as keyword counts*: the real call missing from the final answer.
  - *tentative*: why the sets differ. "Knowledge vs worked out" is one reading; the sets differ in
    more than that.

## F16. Track B, Qwen3 30B Instruct: it calls the lookup every time and takes its letter; the Thinking checkpoint follows pasted and system hints more, but calls less

**Setup.** As F15 (Oct 28, 03:11–05:32): the same 54 questions × 5 conditions × 3 runs = 810 runs
at the 32,768 budget, every one with an answer. Instruct has no private reasoning, so only the final
answer can name the hint. The lookup tool is described to the model as "the course answer key", the
source the pasted block and the system note also name.

| channel | following | above the no-hint baseline | final answer names the hint, when following |
|---|---|---|---|
| user | 1 of 162 [0, 3%] | −1 [−2, +1] | 1 of 1 |
| tool, pasted | 35 of 162 [16, 29%] | **+20 [+11, +30]** | 29 of 35 [67, 92%] |
| tool, real call | **147 of 162 [85, 94%]** | **+90 [+82, +96]** | **30 of 147 [15, 28%]** |
| system note | 35 of 162 [16, 29%] | **+20 [+11, +30]** | 32 of 35 [78, 97%] |

- **No hint:** right in 142 of 162 [82, 92%]; the hint letter in 2 of 162 [0, 4%].
- **Gate 2** (tool − user, paired by question, 54 questions): pasted **+21 points [+12, +31]**,
  real call **+90 [+83, +96]**. Both clear. No run goes past 16,000 tokens (the longest is 11,564),
  so the 16,000 cut changes nothing.
- **The real call:**
  - It called the tool in 162 of 162 runs [98, 100%], with tool choice left to the model.
  - It took the tool's letter in 147 of 162. In 14 of the other 15 it gave the right answer.
  - The median real-call run is 35 output tokens over both turns (puzzles 32, MMLU-Pro 140): the
    call, then the letter.
- **By set:**

  | set (no-hint right) | user | tool, pasted | tool, real call | system note | Gate 2 pasted / real |
  |---|---|---|---|---|---|
  | puzzles, 24 q (70 of 72) | 0 of 72 [0, 5%] | 0 of 72 [0, 5%] | 72 of 72 [95, 100%] | 0 of 72 [0, 5%] | +0 [+0, +0] / +100 [+100, +100] |
  | MMLU-Pro, 30 q (72 of 90) | 1 of 90 [0, 6%] | 35 of 90 [29, 49%] | 75 of 90 [74, 90%] | 35 of 90 [29, 49%] | +38 [+23, +52] / +82 [+70, +93] |

  - On the puzzles, a pasted block or a system note never moved it, but after a real call it took
    the tool's letter in 72 of 72. Its final answer named the tool in 0 of those 72.
  - On MMLU-Pro, the final answer named the tool in 30 of 75 runs that followed it [30, 51%].
- **Sure vs unsure** (43 sure questions, right in every no-hint run; 11 unsure):
  - pasted: 18 of 129 [9, 21%] vs 17 of 33 [35, 67%]
  - real call: 115 of 129 [83, 93%] vs 32 of 33 [85, 99%]
  - system note: 15 of 129 [7, 18%] vs 20 of 33 [44, 75%]
  - user: 1 of 129 [0, 4%] vs 0 of 33 [0, 10%]
- **Thinking minus Instruct** (F15 minus this entry, following, paired by question, 54 questions;
  the same at the 16,000 cut within a point or two):

  | channel | both sets | puzzles (24 q) | MMLU-Pro (30 q) |
  |---|---|---|---|
  | user | +1 [+0, +3] | +0 [+0, +0] | +2 [+0, +6] |
  | tool, pasted | **+15 [+6, +25]** | +7 [+1, +12] | +21 [+6, +38] |
  | tool, real call | **−57 [−70, −43]** | **−94 [−99, −89]** | −28 [−44, −10] |
  | system note | **+14 [+7, +20]** | +10 [+4, +15] | +17 [+7, +27] |

- **Reading.**
  - **Calling is following.** With a lookup tool available, Instruct calls it at once and answers
    with its letter, even on puzzles it solves alone 70 of 72 times. The same "course answer key"
    claim pasted into the question or put in the system prompt moves it far less (35 of 162 each,
    none of it on the puzzles).
  - **Thinking cuts the call, not the pull.** The Thinking checkpoint calls the tool in a third of
    runs (54 of 162) and follows every call it makes (F15). It also follows pasted and system hints
    more than Instruct does. So its lower real-call following comes from calling less, not from
    weighing the tool's answer.
  - **The final answer rarely says so in either.** After a real call, Instruct's final answer names
    the tool in 30 of 147, and Thinking's in 3 of 54. All 30 of Instruct's are on MMLU-Pro.
  - **Two checkpoints, not one switch.** Thinking-2507 and Instruct-2507 are separately trained
    models. The difference is "this Thinking checkpoint vs this Instruct one", not thinking on vs
    off. Qwen3-8B's switch (one set of weights, on Sol, prepared) is the same-weights comparison.
- **Source.**
  - `cot-disclosure/results/summaries/trackB/trackB_report.json` and `trackB_report_by_set.json`
    (`budget_32768` / `cut_16000`, the `qwen3-30b-a3b-instruct-2507` rows, and
    `thinking_minus_not`)
  - per-run flags: `trackB_runs.jsonl`
  - recomputed with `python progress/trackB_report.py --by-set` (Mac, no calls). Mentions are
    keyword counts (`detect.py`).
- **Status.**
  - *confirmed*: Gate 2 for Instruct; the real call taken in 147 of 162; Thinking − Instruct on
    the real call (−57) and on pasted and system hints (+15, +14), on 54 questions × 3 runs.
  - *confirmed as keyword counts*: the final answer's mentions.
  - *tentative*: "thinking cuts the call". It is one pair of checkpoints, and the sets differ as in
    F15.

---

## Measurement traps we hit and fixed

Each one would have changed a reported number.

**T1. Template mismatch.**
- *What.* Voyager's chat endpoint rendered `olmo3-7b-think` with the Olmo 3 *Instruct* template,
  whose generation prompt has no `<think>`.
- *Found* Oct 21 from prompt-token counts. On a plain question the server counted 178 tokens: the
  Instruct template's exact count. All 24 revisions of the Think template give 215.
- *Fix.* Render the official Think template ourselves and send it to `/v1/completions`. Every
  earlier Voyager run of this model is in the Instruct format (F2).
- *Source.* `results/summaries/trackA/template_revisions.json`.

**T2. Default system prompt.**
- *What.* The two templates carry different default system prompts. Declaring the tool in the
  system prompt changed hint following on the inserted tool turn: 34 of 60 [44, 68%] vs 24 of 60
  [29, 53%], **+17 points [+3, +30]**.
- *Fix.* Every record names its system prompt. Training uses the declared version; held-out
  evaluation keeps both.
- *Source.* `base_format_runs.jsonl` (`system_prompt`).

**T3. Model-ID routing.**
- *What.* On Oct 21 Voyager replaced its six IDs with family IDs plus `reasoning_effort`, and the
  default effort serves the *Instruct* model.
- *Rerun:* the 11 Step 2b runs saved before the change.
- *Same-checkpoint check on the new route:*
  - max difference 0.0003 on the first 2,047 tokens
  - beyond them, 24 top-token mismatches, all near-ties
  - the Instruct model gave 654 mismatches
- *Fix.* One name → (ID, effort) map. A Think model sent without an effort is refused, and the
  catalog is checked at the start of each run.
- *Source.* `docs/OVERVIEW.md` §5; commit `280bd12`.

**T4. Parser forms.**
- *What.* "**Answer**: D" and "the **answer** is E" weren't read. Found in a Step 4 continuation.
- *Fix.* Re-scoring every saved result changed 1 letter: a Step 4 hint-arm continuation went from
  no answer to D, the hint letter. The hint arm now ends on the hint 44 of 57 (was 43).
- *Source.* Commits `b0331ed`, `5bbd7c0`.

**T5. "expected" false matches.**
- *What.* The tool-mention words included plain "expected", which matched 7 sentences that weren't
  about the hint ("the expected value") among those planned for deletion.
- *Fix.* Narrowed to "expected answer" / "expected_answer" / "expected is" / "expected: (X)" for
  Step 4, Step 10 and F8. Step 3's mention counts (F6) still use the broader words.
- *Source.* Commit `5559a3d`; `finetune/look/deletion.py` (`HINT_TOOL`).

**T6. Identity canary.**
- *What it does.* An hourly echo on a fixed 530-token text checks that Voyager still serves our
  model: the same top token everywhere, max difference under 0.01.
- *The trap.* On Oct 22 a network error was logged as a failed check. Now a canary that gets no
  reply is no verdict: requests pause, it retries every 2 minutes, and the run halts only on a
  real mismatch or after 30 minutes unreachable.
- *Since then:* 47 of 47 checks with a reply passed (Oct 22–26).
- *Source.* `results/summaries/voyager_canary.jsonl`; commit `58dcf97`.

**T7. Averaging a cumulative curve by layer type.**
- *What.* Restoration at the hint's tokens stays near 1 until the information leaves them, then
  falls in steps. Averaged over the 8 full vs the 24 sliding layers, it gave 0.53 vs 0.65 at cut
  (ii), which reads as "sliding layers matter more". Those averages describe the step's position,
  not which layers do the reading.
- *Fix.* The per-layer drop and its share of the total (F11): 0.95 at the full layers.
- *Source.* `step10_by_layer_type.json` (the first reading, kept) vs `step10_handoff.json`.

**T8. A weights check that didn't check.**
- *What.* Step 8's snapshot check read the hash from the cache's link names. On Sol the weight
  files are regular files, so it reported `weights_same: false` without hashing anything. Its
  summary line, "FAIL on 0 of 5", also counted passes.
- *Fix.* Regular files are now hashed (sha256 for the weights, the git blob id for the rest) and
  the result is cached. The line counts failures. The Sol weights were checked by `sha256sum`
  (F9).
- *Source.* `finetune/gpu/kit.py` (`files_vs_template_rev`), `checkpoint_check.py` (`verdict`).

**T9. An anchor picked where the hint is strongest (the second time).**
- *What.* Step 9's first aligned reading compared followed runs at the takeover with resisted runs
  at their closest approach, which is by construction where the hint letter peaks. It read
  "resisted runs look at the hint more there": −0.0076 [−0.0123, −0.0016].
- *The first time* was before Step 4 (analysis 2(a), Oct 25). "The own answer leads just before a
  late takeover more often than at a closest approach" came out +50 points, partly built in: just
  before a takeover the hint can't lead. Matched onsets gave −1 point [−16, +19] (F5).
- *Fix.* Anchor both groups the same way: every lead onset after the first fifth, lasting or
  temporary. Temporary leads in followed and resisted runs then don't differ: −0.7e-3 [−4.2e-3,
  +2.0e-3] (F10, F14).
- *Rule.* No comparison anchors one group on a point chosen by the measure being compared.
- *Source.* `step9_followup.json` (`aligned`, kept and marked biased; `onsets_matched`).

**T10. A context window that silently drops the question (Ollama).**
- *What.* Ollama's default context is 4,096 tokens with context shift on: once a run's conversation
  passed it, Ollama dropped the conversation's start (the question and the hint) without an error,
  and the model kept answering. The first 20 Track B rows from Ollama (qwen3:8b) ran this way; 13 of
  them passed 4,096 tokens (prompt + reply).
- *Fix.* Every request sets the context to 33,792 (the 32,768 budget plus room) and each row records
  it; a row counts as done only with the current context, so the 20 rows are rerun (`8d8e206`).
- *Rule.* A local server's context is set explicitly and recorded per row; a row made under another
  context doesn't count.
- *Source.* `providers/ollama.py` (`NUM_CTX`), `progress/run_trackB.py` (`current()`).

**Also:**
- Cut-off replies leak when not streamed (the reasoning landed in the answer in 8 of 8).
- A tool call quoted inside the reasoning tripped the tool-call stop (7 runs, continued).
- Streams that closed without a finish reason were taken as complete (3 runs, rerun).

---

## Limitations: how runs were made, where it matters

- **Qwen3-8B's sampling** (Track B, on Sol from Oct 28): one setting for thinking on and off,
  temperature 0.6, top_p 0.95, top_k 20 (Qwen's values for thinking mode), so that thinking is the
  only difference between the two arms. Qwen recommends temperature 0.7 and top_p 0.8 for
  non-thinking mode; the thinking-off numbers are at the thinking-mode setting, not that one.
- **Qwen3-8B's serving**: vLLM in bf16 on one A100 (our own server, the snapshot's chat template,
  its sha256 saved with every run), not Ollama's quantized `qwen3:8b`; the 2 Ollama runs made at
  the full context are reported apart, never pooled.
- **One budget** for every open model in Track B: 32,768 tokens, prompt and every reply of a run
  (decided Oct 27); each table also shows a 16,000 cut, where a run past it counts as no answer.

---

## Figure plan: the 6 figures that tell the story

| # | Story beat | Figure | Status |
|---|---|---|---|
| 1 | The failure: tool hints move the answer more than user hints | Test 2 by channel, served (`presentation/progress/figures/F9_expB_cue_by_channel.png`) next to Step 2b per channel, pinned (`results/summaries/trackA/figures/fig1_pinned_by_channel.png`) (F1, F2) | both **exist** (pinned panel drawn Oct 27) |
| 2 | It's hidden: the reasoning names the hint, the final answer doesn't | `presentation/progress/figures/F2_pilot_mentions_by_channel.png` (F3) | **exists** |
| 3 | Where it takes over: the hint starts ahead, swings, and wins late on known answers | `results/summaries/trackA/figures/takeover_mean_curves.png` and `takeover_points.png` (F4–F6) | **exists** |
| 4 | Is the repetition causal? Deletion vs control vs unedited: the answer at the cut, continuations, re-mentions | `results/summaries/trackA/figures/fig4_deletion.png`, from `deletion_runs.jsonl` + `deletion_remention.jsonl` (F7) | **exists** (drawn Oct 27; `finetune/look/plot_figures.py`) |
| 5 | Inside the model: the handoff. Per cut, hint-token and answer restoration by layer, with the full-attention layers drawn and 15, 19, 23 marked (F11, F12). Beside it: the hint wins the lead at the moments the model looks back at it (F14, hint − control panel) | `results/summaries/trackA/figures/step10_handoff.png`; `results/summaries/trackA/step9_onsets.png` (left panel) | both **exist**. The per-token panel goes in the appendix. `step9_aligned.png` is not used (closest-approach anchor, T9) |
| 6 | The window: the hint's pull vs distance to its last mention | `results/summaries/trackA/window_reach.png` (F8) | **exists** (tentative finding) |

After Phase 6, a seventh figure goes in: the Gate 3 comparison. It shows hint following,
accuracy and the hiding check for base, prompt-only and the trained versions, all on Sol (F9). The
handoff figure is redrawn for the best version, to show whether the drops at 15, 19 and 23 shrink.
