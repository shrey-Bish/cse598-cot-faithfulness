# Slide points: ten slides, six minutes

For the assistant that builds the deck, and for the speakers. Every number is in
`RESULTS_SUMMARY.json`. Figures are in `presentation/progress/figures/` and screenshots
in `presentation/progress/screenshots/`. Times add up to 360 s.

---

## 1. Title and question (25 s)

- **Title:** Do thinking models say when a hint changed their answer?
- CSE 598 Group 10: Shrey Bishnoi, Arsha Jindal, Ritik Agarwal.
- **The question:** when a planted cue changes the answer, does the private reasoning
  or the final answer say so?
- Six open-weight models on ASU Voyager, in three instruct/thinking pairs.

**Visual:** none, or `screenshots/03_card-two-channels.png` as a background strip.

**Speaker note:** "Thinking models now hand back two texts: private reasoning and the
answer you see. We test whether either one admits it when a hint moved the answer."

## 2. Base paper and what it couldn't show (35 s)

- **Turpin et al. (NeurIPS 2023):** "I think the answer is (B)" moved GPT-3.5 and
  Claude 1.0, and the explanation rarely said so.
- **What it couldn't test:**
  - closed 2023 models
  - one cue channel (the user)
  - single runs, with no repeated no-cue baseline
  - no separate private-reasoning channel
- **What we add:**
  - open instruct/thinking pairs
  - both channels scored separately
  - wobble and letter controls
  - cue via the user and a simulated tool block
  - a reviewer agent
- The test is necessary, not sufficient, for faithfulness.

**Visual:** text only.

**Speaker note:** "Turpin's test is a floor. If the answer moves and the explanation is
silent, the explanation is unfaithful on that case. Passing it doesn't prove more."

## 3. What changed since the proposal (40 s)

- Eight endpoints → six (three pairs). Exact IDs and pair differences are in
  `MODELS.md`, and the Olmo 32B checkpoint is marked unconfirmed.
- 3 no-hint repeats per puzzle.
- Hint letters balanced across A–G.
- One correct hint per puzzle.
- Mention vs acknowledgment: keyword counts are a pre-sort; two human raters next.
- Thinking can't be turned off on Voyager, so the dose lever is "think briefly" on the
  same model.
- Reviewer-agent extension started (Experiment A).
- Budget trimmed from about 180M to about 55M output tokens. The timing run validates it
  (`F6_timing_and_tokens.png`).

**Visual:** a two-column table, change → TA point (from `PROGRESS_REPORT.md` §2).

**Speaker note:** "Every change answers a point from the proposal review. The biggest
are repeated no-hint runs and separating mention from acknowledgment."

## 4. The pipeline runs end to end (35 s)

- Pipeline: puzzles → prompts with and without a cue → Voyager (streamed, seeded) →
  split private vs final → parse the letter → keyword pre-sort → analysis.
- **Pilot:** 1,056 calls, 0 failed. 24 puzzles × 6 models × 6 runs = 864 in the main
  grid.
- **Today:** 427 new calls, 0 API errors, 0 retries, 0 parse failures, 86 minutes of
  run time.
- **Fixes:**
  - streaming, after Cloudflare 524 errors
  - a robust answer parser, because 46% of replies ignored the format
  - saving every reply, because the pilot saved only metadata
- New today: the private field is now called `reasoning`, and seeded replays are not
  always byte-identical. Both are logged.

**Visual:** `screenshots/01_card-counters.png` + `screenshots/07_card-terminal.png`.

**Speaker note:** "This runs end to end on real endpoints. Today we found the reply
texts weren't saved, so we now store every prompt and reply."

## 5. Finding: steering appears where the model is unsure (40 s)

- Wrong-hint following, 48 runs per model:
  - Olmo 3 7B Instruct: 5/48 (10.4%, 95% range 2.1 to 18.8)
  - Olmo 3 7B Think: 1/48
  - the other four models: 0/48
- Without a hint, the same letters were chosen 0/144 times.
- Olmo 3 7B Instruct also changed its no-hint answer on 7/24 puzzles.
- Re-asking the steered prompts with new seeds: only 2 of 12 draws followed the hint
  again. Steering is a low-probability event on these puzzles.

**Visual:** `figures/F1_pilot_hint_following.png`, and
`screenshots/02_card-pilot-steered.png` as an inset.

**Speaker note:** "On easy puzzles the hint rarely wins. Where it does, the model was
already unsure. So the next sweep targets items the models are unsure about."

## 6. Finding: the private vs final mention gap (45 s)

- Thinking models, hinted runs: the hint is mentioned in 208/216 private traces vs
  8/216 final answers (keyword pre-sort).
- Caveat: the same keywords fire on 22/72, 18/72, 2/72 no-hint traces ("the user"), so
  the private counts are upper bounds until human labels.
- Olmo instruct models mention the hint in 56/144 visible answers. Olmo thinking models:
  0/144.
- Real example: the private reasoning says "the user's initial thought was correct",
  and the final answer is silent (Olmo 3 7B Think, steered).

**Visual:** `figures/F2_pilot_mentions_by_channel.png` +
`screenshots/03_card-two-channels.png`.

**Speaker note:** "A reader of the final answer sees the hint in about one run in 27.
The private channel has it almost always, but mentioning isn't admitting. That's what
the human labels will settle."

## 7. Four smaller findings (40 s)

- **"Answer only" breaks instruct models:** 21/24 → 1/24 and 24/24 → 2/24. Thinking
  models keep reasoning privately (21/24, 23/24 replies) and stay at 23/24 and 24/24.
  (`F3`)
- **Token cap:** whether private reasoning leaks into the visible answer depends on
  the request mode.
  - Same 8 requests capped at 2,000 tokens: streamed 0/8 leaked, non-streamed 8/8.
  - Earlier 8,000-cap run: 10/10 leaked.
  - The parser read a wrong letter out of one leak.
  - (`F5`, `screenshots/04_card-truncation.png`)
- **Hints cost work:** replies 4.9% to 58.9% longer with a hint, on all six models.
  (`F4`)
- **Thinking can be dialed down in one model:** "think briefly" cut private reasoning by
  29.8% and 47.7%.

**Visual:** `F3_pilot_answer_only.png` and `F5_pilot_truncation_leak.png` side by side.

**Speaker note:** "Each of these shapes the design. No-CoT means different things per
track, the cap must be set per model, and 'think briefly' is our dose knob."

## 8. New today: Experiment A and Experiment B (50 s)

- **Experiment A, reviewer demo (single-digit n: 5 steered + 6 twin cases × 3
  repeats).** Reviewer kept the hinted wrong answer:
  - 0/15 with the answer only
  - 7/15 with the explanation
  - 3/3 with private reasoning (one case)
  - 6/15 even when told the user suggested it
  - With the answer only, it damaged 3/18 right twin answers.
  - The counterfactual guard flagged 5/5 steered cases. False alarms on twins: 0/5
    (+1 undetermined) from existing runs, 1/6 from a fresh re-ask.
- **Experiment B (30 MMLU-Pro items; user sentence vs simulated tool block):**
  - On uncertain items, Olmo 3 7B Instruct took the cue 7/14 times.
  - The tool block steered the thinking models (Olmo Think 10/20, or 10/11 of runs that
    finished; Qwen 7/11), where the
    user sentence mostly didn't (2/20, 0/11).
  - When steered, private reasoning referred to the tool 9/10 and 7/7 times; final
    answers 2/10 and 4/7.

**Visual:** `F7_expA_reviewer_arms.png` (left), `F9_expB_cue_by_channel.png` (right);
optionally `screenshots/05_card-reviewer.png`.

**Speaker note:** "Two small runs from today. On harder items, a cue that looks like an
answer-key lookup moves even the thinking models, and their final answers mostly don't
say why. The reviewer demo suggests showing more of the answerer's text can make a
reviewer pass the error along. It's five cases, so it's a design input, not a result."

## 9. Plan for weeks 9 to 16 (30 s)

- **Weeks 9–12:**
  - uncertain-item screen on GPQA Diamond + MMLU-Pro, 3 no-cue runs
  - cue via user / tool / system
  - wrong and correct cues
- **Labels:** two raters, about 300 cases, Cohen's kappa (`LABELING_GUIDE.md`).
- **Weeks 13–14:** "think briefly" dose on uncertain items; truncation sweep over caps
  and request modes.
- **Week 15:** reviewer arms a–e with twins and the counterfactual guard.
- **Final talk** Nov 30 to Dec 6. **Report** Dec 7 to 12.

**Visual:** a timeline bar.

**Speaker note:** "The sweep moves to items where models are unsure, because that's
where steering showed up."

## 10. Risks and asks (20 s)

- Keyword counts over-fire. Human labels before any acknowledgment claim.
- The Olmo 32B checkpoint behind the Voyager ID is unconfirmed. **Ask:** Research
  Computing.
- GPQA Diamond is gated (access request). The real tool-role turn on Voyager is
  untested.
- Instruct vs thinking twins differ in training, not only in thinking.

**Visual:** `FAILURES_AND_RISKS.md` as a two-column table.

**Speaker note:** "These are the things that could change our conclusions, and what
we're doing about each."
