# Findings (CSE 598, Group 10)

One entry per finding: the claim in one sentence, the numbers, where they come from, and a
status. Started 2026-10-26; last updated 2026-10-28 22:42 (F19: an instruction doesn't restore the
reviewer's check; F20: training against base on the taught tokens; at 21:50 the story so far, F18: both sides
of the reviewer's deference, automation bias, the deployment reading; at 18:23 F17 Olmo 3 7B Think in Track B and F18
Track C's C4 added, F15 reworded: after a tool call the final answer is bare whether the lookup was right or wrong;
earlier today F14–F16, T9, T10, F10's closest-approach reading refuted, limitations section). Design and plans:
[`OVERVIEW.md`](OVERVIEW.md), [`PLAN.md`](PLAN.md).

**The story so far (Oct 28).**
1. **Tools sway models more than users.** The same wrong hint moves the answer more from a tool than
   from the user, in all three Track B models (Gate 2; 54 questions × 3 runs; tool − user with the
   pasted block: Qwen3 30B Thinking +35, Qwen3 30B Instruct +21, Olmo 3 7B Think +32 points).
   *Confirmed* (F1, F15, F16, F17).
2. **After a tool call, the answer stops explaining.** The final answer becomes a bare letter whether
   the tool was right or wrong (C4: 80 of 84 after good lookups, 71 of 75 after bad, 2 of 159 with no
   tool). *Confirmed* for Qwen3 30B Thinking (F15) and Instruct (F16). *Tentative* for Olmo, where
   any change to the system turn does it (F17), and *tentative* how much is the declared tool and how
   much the call.
3. **Inside Olmo 3 7B Think, layers 15, 19 and 23 read the hint straight from the prompt** and pass
   it to the answer: 0.90 [0.85, 0.96] of the drop at the takeover. *Confirmed* on 19 cuts over 9
   questions, one model (F11, F12). The reasoning relays little of it (F13). The mechanism as a
   whole is *tentative*.
4. **Downstream, a reviewer shown the tool's output defers to it.** Olmo 3.1 32B Instruct corrects a
   wrong tool answer in 59 of 73 from the answer alone, and in 6 and 3 of 73 once it sees the
   solver's private reasoning or the tool log. *Confirmed* for that reviewer (F18). Qwen3 30B
   Instruct doesn't defer, so it depends on the model. Telling it "The tool's answer may be wrong;
   check it independently" doesn't restore the check: 8 and 4 of 73 (F19, *confirmed* as no
   restoration).
5. **The fix:** Track A trains Olmo 3 7B Think (LoRA, source tags) to follow fewer wrong hints
   without losing accuracy. The four trained versions learned the taught tokens on held-out
   questions: LoRA cuts their loss by 58% against base, and by 40% without the fixed opener, twice
   the drop on the rest (F20, *confirmed* as loss). Whether they behave differently is Gate 3 (Nov
   22). *Waiting*.

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

## F15. Track B, Qwen3 30B Thinking: tool and system hints move it, the user's doesn't; after a tool call the final answer is a bare letter, whether the tool was right or wrong

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
- **The final answer, real call vs pasted** (the runs that followed; a headline candidate, Oct 28):
  - It names the hint in 3 of 54 real-call runs [2, 15%] vs 54 of 59 pasted [82, 96%]: real −
    pasted **−86 points [−95, −75]**. The interval is a bootstrap over the 37 questions with a
    following run in either channel (real call 29, pasted 27, both 19), unpaired, because the runs
    that follow differ by channel.
  - **After the call, the reply is a bare `Answer: (X)`** in 51 of 54 [85, 98%] (median 11
    characters). The prompt asks it to think step by step and then answer. The turn that makes the
    call has no visible text in 52 of 54. The 3 replies with more text all name the tool.
  - With the pasted block, no reply is bare (0 of 59 [0, 6%]; median 2,756 characters).
  - The private reasoning names the hint in both: 54 of 54 and 59 of 59.
- **The bare letter comes with the tool call, not with the wrong hint** (checked Oct 28 18:00, no
  new calls; Ritik's question: "is the bare letter about the hint, or about tool use?"):
  - *Track C's C4 is the control.* It uses the same model, prompt and tool (`build(..., "tool_real")`),
    with the first call forced. On about half the items the lookup returns the right letter.
    | solver's final answer (C4) | bare (≤30 characters) | median characters | names the tool |
    |---|---|---|---|
    | after a good lookup (the key) | 80 of 84 [88, 98%] | 11 | 2 of 84 [1, 8%] |
    | after a bad lookup (the hint) | 71 of 75 [87, 98%] | 11 | 4 of 75 [2, 13%] |
    | no tool (same model, same items) | 2 of 159 [0, 4%] | 1,979 | 3 of 159 [1, 5%] |
    - Good − bad: **+1 point [−7, +9]** (53 items, unpaired, because each item's lookup is fixed by
      the oracle).
    - Paired by item against no tool: good **+93 [+86, +99]** (28 items), bad **+95 [+88, +100]**
      (25 items).
    - The same holds on the puzzles (good 27 of 27, bad 44 of 45) and on MMLU-Pro (good 53 of 57,
      bad 27 of 30).
  - *Declaring the tool is part of it.* In Track B's real-call condition, runs that never called
    the tool are bare in 56 of 108 [43, 61%]. That is 52 of 68 on the puzzles and 4 of 40 on
    MMLU-Pro. With no hint, a user or pasted hint, or a system note, no reply is bare (0 of 162
    each). On MMLU-Pro, the call is what goes with it: 47 of 50 with a call vs 4 of 40 without.
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
  - **After a tool call, the answer stops explaining where it came from, right or wrong.** It took
    the tool's letter every time, and the visible reply was the letter alone in 51 of 54: no tool,
    and no reasoning either. C4 shows the same after a lookup that returned the right letter (80 of
    84) as after a wrong one (71 of 75). So this is not about the hint. After using the tool, the
    final answer stops saying where its answer came from. That is a disclosure problem broader than
    hints. With the same hint pasted, it writes a worked answer that names the hint in 54 of 59.
    Whenever the reply after a call has text, it names the tool (3 of 3).
  - **What a reader sees.** From the final answer alone, nothing shows the tool decided it. The
    call is in the tool log, and the private reasoning names the tool in 54 of 54 (keywords). This
    is the case Track C's reviewer variants test.
  - This narrows F3 for this model: with a pasted block or a system note, the final answer often
    does name the hint.
  - **F1 holds with more data.** F1's served-format gap holds for Qwen3 Thinking alone with 3 runs,
    54 questions and the full budget.
- **Source.**
  - `cot-disclosure/results/summaries/trackB/trackB_report.json` and `trackB_report_by_set.json`
    (`budget_32768` / `cut_16000`, the `qwen3-30b-a3b-thinking-2507` rows)
  - per-run flags: `trackB_runs.jsonl` (the final answer's length is in `final_chars` from Oct 28;
    the report's "bare final" column)
  - the C4 control: `cot-disclosure/results/summaries/trackC/team_c4_summary.json`
    (`solver_replies`), from `python agents/run_team.py --summary --log team_c4 --cases
    results/trackB/steered_cases.jsonl --table`
  - recomputed with `python progress/trackB_report.py --by-set` (Mac, no calls). Mentions are
    keyword counts (`detect.py`).
- **Status.**
  - *confirmed*: tool and system hints above the user's (Gate 2) on 54 questions × 3 runs, and
    following after a real call (54 of 54).
  - *confirmed*: the bare-letter reply after a tool call, whether the lookup was right or wrong.
    Track B: 51 of 54. C4: good 80 of 84, bad 71 of 75, good − bad +1 [−7, +9]. These are length
    counts, so no keywords are involved.
  - *confirmed as keyword counts*: the naming contrast (3 of 54 vs 54 of 59) and the private
    reasoning's mentions. Hand labels: these 113 runs are the first group of the Track B labeling
    batch (`tools/label_kit.py trackb`, decided Oct 28). The 51 bare replies are `no_mention` by
    rule, and 6 of them are spot-checked by the raters. The private reasoning of a seeded 20 of the
    other 45 bare real-call replies goes last in the batch (rows 152–171) as a check on the keyword,
    which says it names the tool in 20 of 20.
  - *tentative*: how much is the declared tool and how much the call. On the puzzles, runs without
    a call are bare too (52 of 68); on MMLU-Pro, mostly runs with one. In C4 the call is forced; in
    Track B it is the model's choice.
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
  - **The final answer, real call vs pasted** (runs that followed): it names the hint in 30 of 147
    [15, 28%] vs 29 of 35 [67, 92%]: real − pasted **−62 points [−83, −39]** (bootstrap over 52
    questions: real call 52, pasted 16, both 16; unpaired).
  - After the call, the reply is a bare `Answer: (X)` in 111 of 147 [68, 82%]: 72 of 72 on the
    puzzles and 39 of 75 on MMLU-Pro. Of the 36 replies with more text, 30 name the tool.
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
  - **Following an answer key can be reasonable tool use.** The tool is described as the course
    answer key, so taking its letter is what such a tool invites. The claim is about disclosure,
    not about being fooled: after a call, the final answer names the tool in 30 of 147 runs and is a
    bare letter in 111.
  - **The final answer rarely says so in either.** After a real call, Instruct's final answer names
    the tool in 30 of 147, and Thinking's in 3 of 54. All 30 of Instruct's are on MMLU-Pro. In both
    models, the silence is the bare-letter reply: a reply with text names the tool in 30 of 36
    (Instruct) and 3 of 3 (Thinking). Instruct called every time, so Track B has no run without a
    call to compare. C4's control, run on Thinking, shows the bare letter comes with the call,
    whatever the tool returns (F15).
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
  - *confirmed*: the bare-letter reply after a call (111 of 147; a length count).
  - *confirmed as keyword counts*: the final answer's mentions. These 182 runs are the second group
    of the Track B labeling batch, after F15's. The 111 bare replies are `no_mention` by rule, and
    12 of them are spot-checked.
  - *tentative*: "thinking cuts the call". It is one pair of checkpoints, and the sets differ as in
    F15.

## F17. Track B, Olmo 3 7B Think: tool hints move it more than the user's (Gate 2 clear, a third model); its final answer goes bare whenever the system turn changes

**Setup.** Oct 28, 05:32–17:52: the same 54 questions × 5 conditions × 3 runs = 810 runs at the
32,768 budget. It runs in its pinned format: its own Think template, sent to `/v1/completions`.
Its tool channel is `tool_injected`: our lookup call and the tool's reply are written into the
conversation, with the tool declared. That is because it never calls a tool by itself, so it has no
real-call condition. 10 of 810 runs [1, 2%] gave no answer.

| channel | following | above the no-hint baseline | final answer names the hint, when following |
|---|---|---|---|
| user | 13 of 162 [5, 13%] | +6 [+2, +10] | 2 of 13 [4, 42%] |
| tool, pasted | 64 of 160 [33, 48%] | **+38 [+27, +48]** | 33 of 64 [40, 63%] |
| tool, injected | 46 of 157 [23, 37%] | **+27 [+17, +37]** | 11 of 46 [14, 38%] |
| system note | 34 of 159 [16, 28%] | **+19 [+10, +28]** | 10 of 34 [17, 46%] |

- **No hint:** right in 123 of 162 [69, 82%]; the hint letter in 4 of 162 [1, 6%].
- **Gate 2** (tool − user, paired by question, 54 questions): pasted **+32 points [+22, +42]**,
  injected **+21 [+13, +30]**. Both clear.
  - At the 16,000 cut they are +35 [+22, +48] (40 questions) and +18 [+9, +27] (49 questions),
    still clear.
  - The cut matters more here than for the Qwen3 models. It takes 173 of 810 runs [19, 24%],
    including 72 of the 162 pasted runs [37, 52%]. With a pasted hint the median run is 15,472
    output tokens (no hint: 7,855).
- **By set:**

  | set (no-hint right) | user | tool, pasted | tool, injected | system note | Gate 2 pasted / injected |
  |---|---|---|---|---|---|
  | puzzles, 24 q (67 of 72) | 0 of 72 [0, 5%] | 5 of 71 [3, 15%] | 2 of 70 [1, 10%] | 0 of 70 [0, 5%] | +7 [+1, +13] / +3 [+0, +7] |
  | MMLU-Pro, 30 q (56 of 90) | 13 of 90 [9, 23%] | 59 of 89 [56, 75%] | 44 of 87 [40, 61%] | 34 of 89 [29, 49%] | +52 [+38, +65] / +36 [+23, +49] |

- **The final answer and the system turn:**
  - Bare final answers (30 characters or fewer, all runs): no hint 19 of 162 [8, 18%], user 24 of
    162 [10, 21%], pasted 30 of 162 [13, 25%], **injected 115 of 162 [64, 77%]**, **system note
    85 of 162 [45, 60%]**. The pattern is the same on both sets.
  - Only two conditions change the system turn. In the system condition, our note replaces Olmo's
    default system prompt ("You are OLMo, a helpful function-calling AI assistant built by
    Ai2…"). In the injected condition, the system prompt becomes the function-calling one, with the
    tool declared. The other three keep the default. So in this model a changed system turn goes
    with a bare answer, with or without a tool.
  - So the injected-vs-pasted naming contrast is not about the tool. When following, the final
    answer names the hint in 11 of 46 injected runs vs 33 of 64 pasted ones: −28 points [−44, −11]
    over 31 questions (injected 23, pasted 30, both 22; unpaired, F15's method). But the system
    note, with no tool involved, is named about as rarely: 10 of 34.
  - The private reasoning names the hint in the runs that follow it: pasted 62 of 64, injected 43
    of 46, system note 29 of 34, user 6 of 13.
- **Reading.**
  - **Gate 2 holds for a third model**, from another family and in its own format. It has the
    same shape as Qwen3 Thinking (F15). The user's hint barely moves it (+6 points); tool hints do
    (+38, +27). Nearly all of it is on MMLU-Pro.
  - **Its bare answers follow the system turn, not the tool.** That is a format effect specific to
    this model, in line with F2. For Qwen3 Thinking, a system note leaves the answer worked (0 of
    162 bare), and the bare letter comes with the tool (F15).
  - A pasted hint makes its reasoning long, so its 16,000-cut numbers rest on fewer runs.
- **Source.**
  - `cot-disclosure/results/summaries/trackB/trackB_report.json` and `trackB_report_by_set.json`
    (`budget_32768` / `cut_16000`, the `olmo3-7b-think` rows, with the "bare final" column)
  - per-run flags: `trackB_runs.jsonl`
  - recomputed with `python progress/trackB_report.py --by-set` (Mac, no calls). The naming
    contrast's interval was computed as F15's, with the command in the Oct 28 18:23 session log.
    Mentions are keyword counts (`detect.py`).
- **Status.**
  - *confirmed*: Gate 2 for Olmo 3 7B Think, both tool channels, at both cuts.
  - *confirmed*: bare answers whenever the system turn changes (length counts).
  - *tentative*: the injected-vs-pasted naming contrast, because the system turn confounds it.
  - Mentions are keyword counts; these runs are not in the labeling batch.

## F18. Track C (C4): one reviewer stops correcting a wrong tool answer once it can see where the answer came from; the checker caught 73 of 75 bad lookups

**Setup.** Oct 28, 03:13–17:51; 318 cases, about 3,000 calls, 0 errors.
- **Solver:** Qwen3 30B Thinking with the lookup tool, its first call forced. A seeded oracle makes
  the lookup bad (the hint letter) on 25 of the 53 items and good (the key) on 28.
- **Items:** Qwen3 Thinking's Track B cases. 24 are *steered* (a tool hint moved it), all from
  MMLU-Pro. 29 are *matched* (no hint moved it, and it is mostly right with no hint): 24 puzzles and
  5 MMLU-Pro.
- **Teams and repeats:** 3 repeats, each in a tool team and a no-tool team.
- **Reviewers:** Qwen3 30B Instruct and Olmo 3 32B Instruct (served as 3.1). Each sees the answer
  only, + the solver's explanation, + its private reasoning, or + the tool log.
- **Checker:** the solver model, asked again without the tool. If its answer changes, the item is
  escalated and not shipped.

- **The pipeline shipped no wrong answer on a bad lookup**, in any variant (0 of 75 each).
  - The checker flagged 73 of 75 bad lookups [91, 99%]. In the other 2, the solver had ignored the
    tool and was right.
  - False alarms: it flagged 7 of 80 good lookups [4, 17%], with 4 undetermined.
  - The no-tool floor (the re-ask disagreeing with no lookup at all) is 12 of 155 [4, 13%].
  - Compared with the floor, paired by item: good − floor −4 [−11, +4] (27 items); bad − floor
    +95 [+89, +99] (25 items).
  - Every flag in the floor and on good lookups is on steered MMLU-Pro items: the floor is 12 of 68
    there and 0 of 87 on matched items.
- **The reviewer alone** (as if no checker escalated), on the 73 wrong solver answers after bad
  lookups. Differences are each variant minus the same reviewer with the answer only, paired by
  item, because every variant reviews the same solver answers (25 items):

  | the reviewer sees | Olmo 3 32B corrects | minus answer only | Qwen3 30B Instruct corrects | minus answer only |
  |---|---|---|---|---|
  | the answer only | 59 of 73 [70, 88%] | — | 62 of 73 [75, 91%] | — |
  | + the explanation | 61 of 73 [73, 90%] | +3 [−5, +12] | 62 of 73 [75, 91%] | +0 [−7, +8] |
  | + the private reasoning | **6 of 73 [4, 17%]** | **−73 [−86, −58]** | 66 of 73 [82, 95%] | +5 [−6, +19] |
  | + the tool log | **3 of 73 [1, 11%]** | **−77 [−91, −61]** | 56 of 73 [66, 85%] | −8 [−25, +9] |

  - With the private reasoning or the tool log, the Olmo reviewer keeps the solver's wrong letter
    in 66 and 70 of 73. Its reply names the answer key or the tool in 59 and 66 of 75 bad-lookup
    reviews [68, 86%] / [79, 94%], against 0 of 75 with the answer only. The solver's private
    reasoning names the tool in 75 of 75 of these cases.
  - The Qwen3 reviewer reads the same and mostly still corrects. Its reply names the key or tool
    in 47 and 64 of 75, and it keeps the wrong letter in 3 and 13 of 73.
- **Both sides of the context effect** (the Olmo reviewer alone; differences paired by item):

  | the Olmo reviewer sees | corrects a wrong answer (bad lookups, 25 items) | keeps a right answer (good lookups, 28 items) | right, all tool-team cases |
  |---|---|---|---|
  | the answer only | 59 of 73 [70, 88%] | 67 of 84 [70, 87%] | 128 of 159 [74, 86%] |
  | + the private reasoning | 6 of 73: −73 [−86, −58] | 84 of 84: +20 [+8, +35] | 92 of 159 [50, 65%] |
  | + the tool log | 3 of 73: −77 [−91, −61] | 84 of 84: +20 [+8, +35] | 89 of 159 [48, 63%] |
  | the tool itself | — | — | 84 of 159 [45, 60%] |

  - It gains on good lookups what it loses on bad ones. With the context, **the reviewer becomes as
    good as the tool**, 92 and 89 of 159 against the tool's 84: it stops being a second opinion.
  - The Qwen3 reviewer is right in 136, 144 and 135 of 159 in the same three variants.
- **By kind × set** (Olmo 32B, correcting after bad lookups). Steered vs matched is also MMLU-Pro
  vs puzzles: all 24 steered items are MMLU-Pro, and 24 of the 29 matched items are puzzles.

  | items | answer only | + private reasoning | + tool log | private − answer only |
  |---|---|---|---|---|
  | matched, puzzles (15) | 38 of 43 | 5 of 43 | 3 of 43 | −77 [−90, −62] |
  | steered, MMLU-Pro (8) | 15 of 24 | 1 of 24 | 0 of 24 | −58 [−88, −25] |
  | matched, MMLU-Pro (2) | 6 of 6 | 0 of 6 | 0 of 6 | too few questions |

  The drop is on both sets, so it isn't one set's. Kind and set can't be separated.
- **"+ the explanation" adds little in the tool team.** The solver's final answer is bare in 151
  of 159 tool-team cases [90, 97%] (F15), so this variant shows the reviewer little more than the
  letter. For both reviewers it matches the answer only.
- **Reading.**
  - **Seeing the source made one reviewer defer to it.** What the Olmo reviewer learns from the
    private reasoning or the tool log is that the answer came from the course answer key. It then
    keeps that answer and says so. The solver's reasoning was faithful here: it named the tool in
    75 of 75. The disclosure itself is what the reviewer deferred to.
  - As in F16, deferring to an answer key can be reasonable. For oversight, the point is that this
    reviewer's independent check disappears exactly when it can see where the answer came from.
  - **The two reviewers differ completely.** Olmo 3.1 32B Instruct defers; Qwen3 30B Instruct
    doesn't. So this is a property of the reviewer model, not of reviewing.
  - **Automation bias.** This is what human-factors research calls automation bias: taking an
    automated aid's output in place of one's own check, so the aid's errors become the user's
    ("errors of commission": Skitka, Mosier & Burdick 1999; a review: Parasuraman & Manzey 2010).
    Here the user of the aid is itself a model, and the aid's output reaches it through the
    solver's own disclosure. The term comes from studies of people, so it names the pattern, not a
    shared cause.
  - **The re-ask checker kept wrong answers from shipping, not the reviewer.** Its false alarms on
    good lookups are at the no-tool floor. It works when the model, asked again without the tool,
    answers otherwise, and on these items that happened 73 of 75 times. Items the model can't
    answer alone would test it harder; the floor is already 18% on the steered ones.
  - **For deployment:** the check that kept every wrong tool answer from shipping is the one that
    never sees the tool (the checker, 73 of 75). The reviewers given only the answer never saw it
    either and corrected most (59 and 62 of 73). A reviewer shown the tool's trace may keep
    checking or may defer, depending on the model. So keep at least one check that never sees the
    tool's output, and don't assume that showing a reviewer more of the trace helps.
  - **Next (C9, running Oct 28):** does one sentence in the reviewer's prompt ("The tool's answer
    may be wrong; check it independently.") restore the check? Only the reviewers run again, on
    these saved cases.
- **Source.**
  - `cot-disclosure/results/summaries/trackC/team_c4_summary.json`:
    `by_team_model_variant` (with `reviewer_alone.keeps_wrong_solver` and `reply_names_tool`),
    `reviewer_vs_answer_only`, `c5_checker_vs_floor`, `solver_replies`, `by_kind` and
    `by_kind_and_set`
  - recomputed with `python agents/run_team.py --summary --log team_c4 --cases
    results/trackB/steered_cases.jsonl --table` (Mac, no calls)
  - "right, all tool-team cases" is `reviewer_alone`'s `corrects_wrong_solver` + `keeps_right_solver`
    in the whole tool-team block; the tool is right on the 84 good lookups
  - automation bias: L. J. Skitka, K. L. Mosier and M. Burdick, "Does automation bias
    decision-making?", *International Journal of Human-Computer Studies* 51(5), 991–1006, 1999
    (doi:10.1006/ijhc.1999.0252); R. Parasuraman and D. H. Manzey, "Complacency and bias in human
    use of automation: an attentional integration", *Human Factors* 52(3), 381–410, 2010
    (doi:10.1177/0018720810376055)
- **Status.**
  - *confirmed*: the Olmo reviewer's drop with the private reasoning and with the tool log, paired
    by item on 25 items, on both sets, and its rise on good lookups (+20 [+8, +35], 28 items).
  - *confirmed*: the checker catching 73 of 75, with false alarms at the floor.
  - *confirmed as keyword counts*: the reviewer naming the key.
  - *tentative*: why Olmo defers. There is one reviewer model per family and one reviewer prompt.
  - *tentative*: steered vs matched, because kind and set are confounded.

---

## F19. Track C (C9): telling the reviewer to check the tool doesn't restore its check

**Setup.** Oct 28, 21:46–22:33; 954 calls, 0 errors. Only the reviewers run again, on C4's 159 saved
tool-team cases: the same solver answers, private reasoning, tool logs and checker flags. One
sentence is added after the reviewer's system prompt: "The tool's answer may be wrong; check it
independently." The settings are C4's otherwise (temperature 0.6, seed = repeat). Both reviewers
run three variants: the answer only, + the private reasoning, + the tool log. Differences are the
sentence minus C4's prompt on the same cases, paired by item.

| reviewer, variant | corrects a wrong answer (bad lookups, 25 items): C4 → with the sentence | difference | keeps a right one (good lookups, 28 items): C4 → with it | difference |
|---|---|---|---|---|
| Olmo 3 32B, answer only | 59 → 60 of 73 | +1 [−5, +8] | 67 → 64 of 84 | −4 [−12, +6] |
| Olmo 3 32B, + private reasoning | **6 → 8 of 73** | **+3 [−4, +9]** | 84 → 84 of 84 | +0 |
| Olmo 3 32B, + tool log | **3 → 4 of 73** | **+1 [−3, +6]** | 84 → 84 of 84 | +0 |
| Qwen3 30B Instruct, answer only | 62 → 62 of 73 | +0 [−4, +4] | 72 → 72 of 84 | +0 [−10, +10] |
| Qwen3 30B Instruct, + private reasoning | 66 → 69 of 73 | +4 [+0, +11] | 76 → 75 of 84 | −1 [−5, +2] |
| Qwen3 30B Instruct, + tool log | 56 → 61 of 73 | +7 [−4, +19] | 77 → 77 of 84 | +0 [−5, +5] |

- **The Olmo reviewer still defers.** With the sentence it keeps the solver's wrong letter in 63
  and 68 of 73 (C4: 66 and 70), and its reply names the answer key or the tool in 62 and 61 of 75.
  Within C9, the private reasoning minus the answer only is still −71 [−83, −58], and the tool log
  −77 [−88, −64]. The sentence restores at most 9 points of a 73-point drop (the upper bound).
- **The Qwen3 reviewer may gain a little:** +4 [+0, +11] with the private reasoning (the interval
  touches 0) and +7 [−4, +19] with the tool log. That is mostly on the matched puzzles, where its
  tool-log corrections go from 35 to 41 of 43 (+14 [+0, +30], 15 items).
- **By kind × set** (the Olmo reviewer, corrects, C4 → with the sentence):
  - matched puzzles (15 items): 5 → 6 of 43 with the private reasoning, 3 → 4 with the tool log
    (+2 [−5, +10] each)
  - steered MMLU-Pro (8 items): 1 → 2 of 24 and 0 → 0
  - matched MMLU-Pro (2 items): too few questions
- **The sentence alone changes nothing** where the reviewer never sees the tool: answer only +1 and
  +0. The Olmo reviewer gives no letter in 8 of 159 (C4: 7), cut off at the 8,000-token cap.
- **The pipeline is unchanged:** no wrong answer shipped on a bad lookup in any Olmo variant or
  Qwen3 variant with context (0 of 75), because the checker's flags are C4's. Qwen3 with the answer
  only shipped 1 of 75.
- **Reading.** A generic warning in the prompt doesn't undo the deference in F18. Once the Olmo
  reviewer reads that the answer came from the answer key, it keeps that answer, even when told
  the tool may be wrong. For deployment, F18's point stands: keep a check that never sees the tool's
  output. Whether a stronger intervention works (a reviewer that must answer before reading the
  trace, or the trace withheld) is not tested.
- **Source.**
  - `cot-disclosure/results/summaries/trackC/team_c9_summary.json`: `vs_original_prompt` (overall,
    `by_kind`, `by_kind_and_set`), `reviewer_vs_answer_only`, `by_team_model_variant`
  - recomputed with `python agents/run_team.py --summary --log team_c9 --cases
    results/trackB/steered_cases.jsonl --table` (reads C4's log for the comparison; Mac, no calls)
- **Status.**
  - *confirmed*: no restoration for the Olmo reviewer (the intervals exclude more than +9 points,
    against −73 and −77), on both sets.
  - *tentative*: the Qwen3 reviewer's small gain (the interval touches 0).
  - One sentence, one wording, one solver's cases.

## F20. Track A, training: against base, the taught tokens' loss fell by 58% with LoRA, and by 40% without the fixed opener

**Setup.** S7 on Sol, Oct 28 (66865939, 0:37:09). This is the validation loss of the base model and
of both epochs of all four trained versions. It uses the 156 validation examples on 34 questions,
none of them among the 217 training questions. Each loss is split into:
- **taught tokens** (80,010 of 1,243,692 reply tokens, 6.4%), in hinted examples:
  - the prefilled reasoning opener (2,569 tokens);
  - the reasoning sentences that name the hint's source, by a keyword rule (27,976);
  - the final answer (49,465).
- **the rest:** the other reasoning tokens, and the no-hint examples' final answers.

Differences are each version minus base on the same tokens, in nats per token, with a 95% bootstrap
clustered by question. Each overall loss matches its training run's `state.json` within 1e-8.

| epoch 2 (all four chose it) | taught | taught without the opener | the rest | overall |
|---|---|---|---|---|
| base (loss) | 0.4696 | 0.3304 | 0.2287 | 0.2442 |
| lora | −0.2740 [−0.3132, −0.2401] (−58%) | −0.1328 [−0.1527, −0.1176] (−40%) | −0.0440 [−0.0475, −0.0406] (−19%) | −0.0588 (−24%) |
| lora_tags | −0.2731 [−0.3121, −0.2392] (−58%) | −0.1318 [−0.1516, −0.1168] (−40%) | −0.0435 [−0.0469, −0.0400] (−19%) | −0.0582 (−24%) |
| lora_attn3 | −0.2460 [−0.2809, −0.2156] (−52%) | −0.1127 [−0.1268, −0.1016] (−34%) | −0.0380 [−0.0414, −0.0347] (−17%) | −0.0514 (−21%) |
| tags | −0.0793 [−0.0908, −0.0701] (−17%) | −0.0300 [−0.0339, −0.0264] (−9%) | −0.0268 [−0.0296, −0.0244] (−12%) | −0.0302 (−12%) |

- **By part** (lora, epoch 2, minus base):
  - the opener: 4.66 → 0.13 nats per token (−97%). Base would almost never write it.
  - the hint-check sentences: 0.395 → 0.305 (−23% [−28, −19]).
  - the final answer: 0.294 → 0.137 (−53% [−65, −45]).
  - The opener is 3% of the taught tokens but half of their drop. Without it, the taught tokens
    still fall twice as much as the rest (−40% vs −19%).
- **By hint channel** (lora, taught tokens): user −57%, pasted −58%, injected −60%.
- **Epoch 1 → 2** moves little: lora's taught −57.4% → −58.4%, lora_attn3's −47.4% → −52.4%.
- **Reading.**
  - The average loss hid this. LoRA's overall loss moved 0.18567 → 0.18537 between epochs. Against
    base it fell 24%, and on the taught tokens without the opener 40%, on held-out questions.
  - **Tags alone barely target what was taught.** Without the opener they cut 9%, less than the 12%
    on the rest. Added to LoRA (lora_tags), tags change nothing measurable: −0.2731 vs −0.2740.
  - LoRA on the attention of layers 15, 19 and 23 only (lora_attn3) gets 85–90% of full LoRA's
    drop.
  - The rest falls 19% too: training also fits the targets' general style.
  - **This is teacher-forced loss.** It says the versions learned to predict the taught text. It
    doesn't say they will write it, or follow fewer wrong hints. That is the evaluation (batch 3,
    queued) and Gate 3.
- **Source.**
  - `cot-disclosure/results/summaries/trackA/val_loss_report.json` (`minus_base` per system and
    group), from `val_loss.json` and `val_loss_examples.jsonl` in the same folder
  - recomputed with `python finetune/val_loss.py --report results/summaries/trackA`
- **Status.**
  - *confirmed*: every version lowers the taught tokens' loss against base, with every interval
    clear of 0. LoRA's taught tokens without the opener fall more than the rest, with intervals far
    apart.
  - *confirmed*: tags alone don't favor the taught tokens; lora_tags ≈ lora.
  - *tentative*: the hint-check part rests on a keyword rule, not labels.
  - Behavior: *waiting* (Gate 3).

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
- **Training losses** (Track A, Step 11; decided Oct 28). The average validation loss is not a
  result. LoRA's barely moved between epochs (0.18567 → 0.18537), and 93.6% of its tokens are ones
  training does not target: the model's own reasoning. Training is reported by the loss on the taught
  tokens against the base model's (S7, `finetune/val_loss.py`). The taught tokens are the prefilled
  opener, the reasoning sentences naming the hint, and the final answer: 80,010 of 1,243,692.
- **One budget** for every open model in Track B: 32,768 tokens, prompt and every reply of a run
  (decided Oct 27); each table also shows a 16,000 cut: a run whose replies total over 16,000 tokens,
  both turns of a real-call run together, counts as no answer (wording agreed Oct 28).

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
