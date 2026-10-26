# Findings (CSE 598, Group 10)

One entry per finding: the claim in one sentence, the numbers, where they come from, and a
status. Started 2026-10-26. Design and plans: [`OVERVIEW.md`](OVERVIEW.md), [`PLAN.md`](PLAN.md).

- **Numbers.** Rates are "X of Y [95% Wilson interval]". Differences are percentage points with
  a 95% bootstrap clustered by question. Mentions are keyword counts (`detect.py`) until the hand
  labels exist.
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
  comparison and by F5's matched onsets.

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
- **Reading.** At the cut, the reasoning's repetition carries the hint. Given room to go on, the
  model goes back to the hint in the prompt, and mostly names it again.
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
  intermediate tokens. Steps 9 and 10 test the layers directly.

## F9. Inside the weights (Sol): the checkpoint, attention to the hint, activation patching

- **Step 8,** checkpoint check, under the rule fixed Oct 26 (PLAN, Track A): *waiting*.
  `finetune/gpu/step8_verdict.py` → `results/summaries/trackA/step8_verdict.json`.
- **Step 9,** attention to the hint, by layer and head; followed vs resisted, tool vs user,
  pasted vs inserted: *waiting*.
- **Step 10,** activation patching on F4's 21 cases, with restoration in the 8 full-attention vs
  24 sliding-window layers: *waiting*.

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

**Also:**
- Cut-off replies leak when not streamed (the reasoning landed in the answer in 8 of 8).
- A tool call quoted inside the reasoning tripped the tool-call stop (7 runs, continued).
- Streams that closed without a finish reason were taken as complete (3 runs, rerun).

---

## Figure plan: the 6 figures that tell the story

| # | Story beat | Figure | Status |
|---|---|---|---|
| 1 | The failure: tool hints move the answer more than user hints | Test 2 by channel, served (`presentation/progress/figures/F9_expB_cue_by_channel.png`) next to Step 2b per channel, pinned (F1, F2) | served panel **exists**; pinned panel **pending** |
| 2 | It's hidden: the reasoning names the hint, the final answer doesn't | `presentation/progress/figures/F2_pilot_mentions_by_channel.png` (F3) | **exists** |
| 3 | Where it takes over: the hint starts ahead, swings, and wins late on known answers | `results/summaries/trackA/figures/takeover_mean_curves.png` and `takeover_points.png` (F4–F6) | **exists** |
| 4 | Is the repetition causal? Deletion vs control vs unedited: the answer at the cut, continuations, re-mentions | new, from `deletion_runs.jsonl` + `deletion_remention.jsonl` (F7) | **pending** (no calls needed) |
| 5 | Inside the model: attention to the hint by layer (followed vs resisted), and restoration by layer (hint / reasoning / answer positions, full vs sliding layers) | Step 9 maps + `step10_restoration.png` (F9) | **pending** (Sol, running) |
| 6 | The window: the hint's pull vs distance to its last mention | `results/summaries/trackA/window_reach.png` (F8) | **exists** (tentative finding) |

After Phase 6, a seventh figure goes in: the Gate 3 comparison (hint following, accuracy and the
hiding check for base, prompt-only and the three trained versions).
