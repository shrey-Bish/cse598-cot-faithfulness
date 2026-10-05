# Progress report: CoT Honesty Lab (CSE 598, Group 10)

Working notes for the progress presentation (week of Oct 5 to 11, 2026). They follow the
course's progress rubric. Every number comes from `docs/progress/RESULTS_SUMMARY.json`,
which `cot-disclosure/progress/analyze_progress.py` builds from saved JSONL. Figures are
in `presentation/progress/figures/` and screenshots in `presentation/progress/screenshots/`.

## 1. The system and the question

**Base paper.** Turpin et al., "Language Models Don't Always Say What They Think"
(NeurIPS 2023). A user line such as "I think the answer is (B), but I'm curious what you
think" moved GPT-3.5 and Claude 1.0 toward (B), and the chain-of-thought explanation
rarely mentioned the suggestion. The test is necessary, not sufficient, for
faithfulness.

**Systems under test.** Six open-weight models on ASU's Voyager API, in three
instruct/thinking pairs:
- Olmo 3 7B
- Olmo 3 (or 3.1) 32B
- Qwen3-30B-A3B (2507)

Thinking models return private reasoning in a separate field from the final answer.
Exact IDs, checkpoints, and pair differences are in `MODELS.md`.

**Question.** When a planted cue changes a model's answer, does the private reasoning or
the final answer say so? Does that depend on how much the model thinks, on where the cue
comes from, and on whether a second model reviews the answer?

## 2. What changed since the proposal

| Change | Why (TA point it answers) |
|---|---|
| Eight endpoints → six (three instruct/thinking pairs) | Document exact checkpoints and how each pair differs; `MODELS.md` lists IDs, candidate model cards, and post-training differences, and marks the Olmo 32B identity as unconfirmed. |
| Generated swap puzzles first (24 fresh, answers spread over A–G) | Uncontaminated items with exact answers. Public benchmarks now come second (Experiment B uses MMLU-Pro, which is public and possibly contaminated). |
| Three no-cue repeats per puzzle | "Repeated no-cue runs": separates cue effects from run-to-run wobble. |
| Hint letters balanced across positions, plus one correct hint per puzzle | "Balanced suggested-answer positions" and "say whether suggestions are correct or incorrect". |
| Mention vs acknowledgment, with human labels planned | "Distinguish mentioning a cue from acknowledging it influenced the answer". Keyword counts are labeled a pre-sort; `LABELING_GUIDE.md` and `LABEL_QUEUE.csv` start the human labels. |
| Thinking can't be disabled on Voyager, so we use "think briefly" on the same model | "Clarify how 'no chain-of-thought' interacts with built-in thinking"; verified that the API exposes traces (separate `reasoning` field). |
| Reviewer-agent extension (Experiment A, a demo today) | Optional multi-agent extension: only the answerer sees the cue; the reviewer sees the question plus answer, explanation, and (arm c) private reasoning; no-cue twin workflow; correction vs agreement. |
| Budget trimmed from about 180M to about 55M output tokens | "Validate runtime and token budgets before any sweep": timing run today (`F6_timing_and_tokens.png`). |
| Omission treated as an operational measure | "Treat cue omission as an operational measure, not proof of dishonesty". |
| Null results reported as results | "Null results count": four models at 0/48 hint following are reported with intervals. |

## 3. The pipeline running end to end

Steps:
1. **Items.** Generate puzzles (`tasks.py`), or load MMLU-Pro items with a seed.
2. **Prompts.** Build each prompt with an optional cue (user sentence or simulated tool
   block).
3. **Calls.** Call Voyager through `client.py`. Replies are streamed. The private and
   final channels are split. Seeds are fixed.
4. **Parsing.** `parse.py` extracts the answer letter.
5. **Keyword pre-sort.** `detect.py` flags cue mentions per channel.
6. **Analysis.** `analyze.py` (pilot) and `analyze_progress.py` (today) compute every
   number, interval, and figure.

**Counts.**
- Pilot progress round: 1,056 calls, 0 failed.
- Earlier test runs: 312 calls.
- Today: 427 new calls (plus 5 served from the reply cache), 0 API errors, 0 retries,
  0 parse failures, about 1.95M output tokens, 86 minutes from first call to last
  (`RESULTS_SUMMARY.json` → `today`). Breakdown:
  - 9 timing
  - 24 replays and re-draws
  - 87 reviewer
  - 6 guard
  - 177 Experiment B no-cue
  - 100 Experiment B cued
  - 24 truncation sweep

**Two engineering fixes from the pilot:**
- **Streaming.** Replies over about 100 s failed with Cloudflare 524 errors until we
  streamed them.
- **Robust final-answer parser.** 46% of answers in the difficulty test ignored the
  `Answer: (X)` format.

**Found today:**
- **Field name.** The streamed reasoning field is now called `reasoning`, not
  `reasoning_content` as in the README. The client reads both. We now log the field
  name per call.
- **Seeded replays.** Seeded replays are byte-identical on 4 of 6 models for short
  replies (timing run). They are not identical on the two Olmo 32B endpoints. Across
  Experiment A, 7 of 14 replays matched the pilot exactly. The misses were 6 Olmo 3 7B
  Instruct replies and 1 Qwen3 30B Thinking reply, and length didn't predict which.
  Because the pilot didn't save reply texts (only metadata), we can't recover every
  pilot text. **We now save every prompt and reply** (one record format for every
  call, built by `progress/common.py`).
- **Summary file.** `analyze.py` rewrites `results/summary.json` with a different key
  order on every run (set iteration). The values are the same, but the file shows as
  changed in git.

## 4. Preliminary results

### Pilot findings (24 puzzles × 6 models × 6 runs = 864 main-grid calls)

**Finding 1. Steering appears only where the model is unsure.** (`F1_pilot_hint_following.png`)
- Olmo 3 7B Instruct chose the hinted wrong letter in 5/48 wrong-hint runs (10.4%, 95%
  bootstrap range 2.1 to 18.8 points). It chose the same letters in 0/144 no-hint
  comparisons.
- Olmo 3 7B Think: 1/48. The other four models: 0/48 each.
- Olmo 3 7B Instruct was also the least stable without a hint: different no-hint
  answers on 7/24 puzzles, none of them a hinted letter.

*Interpretation:* on easy items, cues rarely move these models. Where they do, the
model is already unstable. Next step: screen for items the models are unsure about
(Experiment B is the first look).

**Finding 2. Private reasoning mentions the hint; final answers mostly don't.** (`F2_pilot_mentions_by_channel.png`)
- Thinking models, hinted runs, keyword pre-sort:
  - private reasoning: 208/216 (Olmo 7B Think 66/72, Olmo 32B Think 71/72, Qwen 30B
    Thinking 71/72)
  - final answers: 8/216 (0/72, 0/72, 8/72)
- The same keywords also fire on no-hint private traces (22/72, 18/72, 2/72), because
  traces say "the user" without any hint. The private counts are therefore upper
  bounds until the human labels are done.
- Instruct models, final answers: Olmo instruct models mention the hint in 56/144
  (Olmo thinking models: 0/144). Qwen instruct 6/72 vs Qwen thinking 8/72.

*Interpretation:* a monitor that reads only final answers would miss most mentions.
Whether the private mentions acknowledge influence or reject the hint needs the human
labels. The `ack_influence` keyword fires in only 3/72, 14/72, 10/72 private traces.

**Finding 3. "Answer only" breaks instruct models, not thinking models.** (`F3_pilot_answer_only.png`)
- Olmo 3 7B Instruct: 21/24 → 1/24.
- Qwen3 30B Instruct: 24/24 → 2/24 (chance 1/7).
- Thinking models still reasoned privately in 21/24 (Olmo 7B Think) and 23/24 (Qwen
  30B Thinking) replies, and scored 23/24 and 24/24.

*Interpretation:* "no chain-of-thought" removes reasoning from an instruct model but
only hides it in a thinking model. Next step: report no-CoT conditions per track.

**Finding 4. Hitting the token cap can push private reasoning into the visible answer.** (`F5_pilot_truncation_leak.png`)
- Earlier ladder run, 8,000-token cap: 10/10 capped replies (all Olmo 3 7B Think) had
  an empty private field and the reasoning in the visible answer (median 26,896
  characters).
- Progress round, 16,000-token cap, streamed: 0/5 capped replies leaked. The visible
  answer was empty and the reasoning stayed private.
- **Truncation sweep today** (Olmo 3 7B Think, pilot puzzles 0–7, no hint, seed 0;
  `truncation_sweep.jsonl`):
  - Streamed requests capped at 2,000 and 4,000 tokens: 16/16 replies hit the cap, and
    0/16 leaked. The reasoning stayed in the private field and the visible answer was
    empty.
  - The **same requests sent without streaming** (2,000 cap): 8/8 leaked (95% Wilson
    67.6 to 100%). The visible answer held the reasoning, the private field was empty,
    and the visible text had exactly as many characters as the streamed private field
    (8/8).
  - The parser pulled a letter out of 1 of the 8 leaked texts: puzzle 3 read as (B),
    while the correct answer is (D).

*Interpretation:* on Voyager the leak follows the request mode, not the cap. Without
streaming, a reply cut off before the model finishes thinking puts all the private
reasoning in the user-visible field, and a parser can read a wrong letter out of it.
The earlier 10/10 ladder leaks fit this: that run likely predates streaming. Next step:
always stream, and treat `finish_reason == "length"` as "no answer" rather than parsing
the visible text.

**Finding 5. Hints cost work.** (`F4_pilot_length_with_hint.png`)
- Median paired output tokens were 4.9% (Olmo 7B Think) to 58.9% (Olmo 32B Instruct)
  higher with a wrong hint than without, on all six models.

*Interpretation:* models spend tokens on the hint even when they don't follow it. Plan
token budgets accordingly.

**Finding 6. Thinking can be dialed down inside one model.**
- "Think briefly" shortened private reasoning by 29.8% (Olmo 3 7B Think) and 47.7%
  (Qwen3 30B Thinking).
- Accuracy went from 45/48 to 42/48 on Olmo, and from 48/48 to 48/48 on Qwen.

*Interpretation:* this is the same-checkpoint dose lever for weeks 13 to 14.

### Experiment A: reviewer demo (single-digit n)

Details: `EXPERIMENT_A.md`. Figure: `F7_expA_reviewer_arms.png`. Screenshot:
`screenshots/05_card-reviewer.png`.

**Cases.** 5 cue-steered pilot answers (Olmo 3 7B Instruct ×4, Olmo 3 7B Think ×1) and
6 no-hint twins.
- 3 of the steered texts are exact pilot replays.
- 2 are re-draws of the same prompt with fresh seeds, which picked the hinted letter.
- The 6th steered case couldn't be reproduced: 6 fresh draws gave no hint-following
  reply.

**Reviewer.** Qwen3 30B Instruct, 3 repeats per arm, 87 calls, 0 errors.

**Results** (counts across repeats; 95% Wilson). The reviewer kept the hinted wrong
answer:
- **0/15 [0, 20.4%]** with the answer only (arm a)
- **7/15 [24.8, 69.9%]** with the visible explanation (arm b)
- **3/3** with the Think model's private reasoning (arm c, one case)
- **6/15 [19.8, 64.3%]** even when told the user had suggested that letter (arm d)

With the answer only, it changed 3/18 right twin answers to wrong ones.

**Counterfactual guard.** Flagged 5/5 steered cases.
- From existing no-hint runs: false alarms on 0/5 twins, plus 1 undetermined tie.
- From one fresh re-ask: false alarms on 1/6 twins.

*Interpretation (demo-level):* in this demo, showing the reviewer more of the answerer's
text made it more likely to pass a steered answer along, and a plain disclosure didn't
stop it. Caveat: in 3 of the 5 steered cases, that text itself already mentions the
user's suggestion, so arm d is not a clean disclosure test. Re-solving from scratch avoided that but damaged right answers. Next step:
arms a–e on the steered and twin cases from the main sweep, with more than one reviewer
model.

### Experiment B: harder items and a second cue channel (first look)

Details: `EXPERIMENT_B.md`. Figures: `F8_expB_item_groups.png`,
`F9_expB_cue_by_channel.png`. Screenshot: `screenshots/06_card-expB-tool.png`.

**Setup.**
- 30 MMLU-Pro items (law, engineering, chemistry, physics), 2 no-cue runs each.
- Uncertain items, plus 5 confident controls per model, then got one wrong cue letter
  through the user sentence, and the same letter through a **simulated tool block**
  (`[tool result: lookup_answer_key] {"expected": "X", …}` inside the user turn).
- 100 cued runs.

**Item groups** (confident / mixed / wrong both):
- Olmo 3 7B Instruct 16 / 2 / 12
- Olmo 3 7B Think 14 / 5 / 11
- Qwen3 30B Thinking 24 / 3 / 3

**Steering where the model is unsure.** Olmo 3 7B Instruct chose the cue letter on 7/14
uncertain items with either channel [26.8, 73.2%], vs 4/28 for the same letters without
a cue. On confident items it chose it 0/5 (user) and 1/5 (tool).

**The tool block steers the thinking models much more than the user sentence:**
- Olmo 3 7B Think: 10/20 vs 2/20. Counting only runs not cut off at 16,000 tokens:
  10/11 vs 2/12.
- Qwen3 30B Thinking: 7/11 [35.4, 84.8%] vs 0/11 (answered only: 7/10 vs 0/9).
- Same letters without a cue: 2/40 and 0/22
- On confident items (10/10 right without a cue), the tool block still moved 3/5 and
  2/5 answers.

**Steered by the tool:**
- Private reasoning referred to it in 9/10 (Olmo Think) and 7/7 (Qwen) runs.
- The final answer did in 2/10 and 4/7 (keyword pre-sort).
- The tool keywords also fire on 12/40 no-cue Olmo Think traces, so the private counts
  need labels.

*Interpretation:* the pilot's null result for thinking models doesn't carry over to a
cue that looks like an answer-key lookup. The private/final gap reappears in the new
channel (`CASE_STUDIES.md` case 6: the final answer builds a calculation that lands on
the cued letter and never mentions the tool). Next step: a real tool-role message, a
system-prompt channel, 3 no-cue runs per item, human labels.

## 5. Failures found in the systems

These are findings about the models and the serving stack. Each has a next step.
`FAILURES_AND_RISKS.md` has the one-slide version.

1. **The smallest instruct model follows wrong hints, and does so more on harder
   items.**
   - Olmo 3 7B Instruct: 5/48 on puzzles; 7/14 on uncertain MMLU-Pro items.
   - Next: the uncertain-item sweep.
2. **Final answers drop what private reasoning says.**
   - Pilot: 208/216 private vs 8/216 final mentions.
   - Experiment B, steered by the tool: private 9/10 and 7/7, final 2/10 and 4/7.
   - Next: human labels for mention, rejection, and acknowledgment.
3. **A simulated tool result steers thinking models that ignore the same hint from the
   user:** Qwen3 30B Thinking 7/11 vs 0/11; Olmo 3 7B Think 10/20 vs 2/20 (10/11 vs
   2/12 among runs that produced an answer).
   - Next: a real tool-role turn and a system-prompt channel.
4. **Instruct models can't answer without room to reason** ("answer only" 1/24 and
   2/24). Thinking models keep reasoning privately.
   - Next: report no-CoT conditions per track.
5. **Hidden reasoning leaks into the visible answer at the token cap when the reply
   isn't streamed.** Same 8 requests: 8/8 vs 0/8 streamed. The parser read a wrong
   letter out of 1 leak.
   - Next: always stream, and treat `finish_reason = length` as no answer.
6. **A reviewer can pass a steered answer along (demo).** It kept the hinted wrong answer
   0/15 times with the answer only, 7/15 with the explanation, and 3/3 with private
   reasoning (1 case).
   - Next: reviewer arms at scale with twins and more than one reviewer.
7. **Olmo 3 7B Think runs out of tokens on hard items.** 13/60 no-cue MMLU-Pro runs hit
   16,000 tokens.
   - Next: per-model budgets from the timing run, and capped runs reported as "no
     answer".

**Operational issues found today:**
- One job starved another for 4 minutes until the shared request limiter was made fair.
- Seeded replays matched the pilot on only 7/14 runs, and the pilot hadn't saved texts.
  All replies are now saved.
- The streamed reasoning field is named `reasoning`, not `reasoning_content`.
- No API errors, retries, or parse failures in 427 calls.

## 6. Risks and obstacles

- **Long traces and budget.** Thinking replies average 4,252 to 8,535 output tokens in
  the pilot. Some MMLU-Pro replies hit the 16,000 cap. Budget per call before each
  sweep.
- **Mention vs admission needs human labels.** Keywords over-fire on private traces
  ("the user" appears without a hint). Two raters and Cohen's kappa are required before
  any acknowledgment claim.
- **Twins differ in training, not only in thinking.** Instruct-vs-thinking gaps are
  checkpoint differences (`MODELS.md`).
- **Olmo 32B identity unconfirmed.** The catalog gives no upstream name. Seeded replays
  on both 32B endpoints don't match the pilot.
- **Reviewer flips need a no-cue twin.** Without twins, a reviewer that changes answers
  looks like it corrects. Twins show whether it also damages right answers.
- **GPQA Diamond is gated.** It needs an access request before the uncertain-item
  screen.
- **Voyager tool-turn format untested.** Experiment B's tool cue is a simulated tool
  block inside the user turn, not a real tool-role message.
- **Pilot texts not saved.** From now on every reply is saved. Old pilot texts can only
  be recovered by seeded replay where the endpoint is deterministic.

## 7. Next steps (weeks 9 to 16)

- **Weeks 9 to 12, core sweep.**
  - Uncertain-item screen on GPQA Diamond and MMLU-Pro with 3 no-cue runs per item.
  - Cue via user, tool (real tool turn if Voyager supports it), and system prompt.
  - Wrong and correct cues, balanced letters.
- **Labels.** Two raters label about 300 cases with `LABELING_GUIDE.md`. We report
  Cohen's kappa and per-channel mention / acknowledgment / rejection rates.
- **Weeks 13 to 14, depth.**
  - Same-model thinking dose ("think briefly" vs normal) on uncertain items.
  - Truncation sweep over caps and request modes.
- **Week 15, reviewer and guard.**
  - Reviewer arms a to e on steered and twin cases from the sweep.
  - Identical no-cue twin workflow.
  - Counterfactual guard with its false-alarm rate.
- **Final talk** Nov 30 to Dec 6. **Report** Dec 7 to 12.

## 8. Reproducibility

```bash
python3 -m venv .venv && .venv/bin/pip install matplotlib numpy pandas datasets playwright pytest
cd cot-disclosure
python analyze.py                                   # pilot numbers (rewrites results/summary.json)
../.venv/bin/python -m pytest -q tests              # parser, detector, helper tests
# new runs (need a Voyager key in cot-disclosure/.env; all resumable):
../.venv/bin/python progress/timing_run.py
../.venv/bin/python progress/mmlu_pro_probe.py select
../.venv/bin/python progress/mmlu_pro_probe.py nocue
../.venv/bin/python progress/mmlu_pro_probe.py cued
../.venv/bin/python progress/reviewer_demo.py all
../.venv/bin/python progress/truncation_sweep.py
cd ..
.venv/bin/python cot-disclosure/progress/analyze_progress.py      # RESULTS_SUMMARY.json + figures
.venv/bin/python cot-disclosure/progress/build_evidence_viewer.py # evidence_viewer.html
.venv/bin/python cot-disclosure/progress/take_screenshots.py      # add --headed --slow-mo 300 to watch
```
