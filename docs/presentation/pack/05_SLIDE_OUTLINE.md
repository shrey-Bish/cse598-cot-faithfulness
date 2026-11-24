# 05. Slide outline (12 minutes)

A 12-minute deck, slide by slide: the point (one sentence), the figure, the numbers to show, any demo moment (keys),
the time, and a blank speaker column for the team. Numbers are FINDINGS' (each a row of [02_NUMBERS](02_NUMBERS.md));
figures are in [`pack/figures/`](figures/) at 1920 px (see [04_FIGURES](04_FIGURES.md)). Slide ids S1–S13 and B1–B6
are the ones 04_FIGURES uses.

**How it relates to the existing deck.** [`TALK_MAP.md`](../TALK_MAP.md) and `deck.pptx` (built from it by
`cot-disclosure/tools/make_deck.py`) have 14 slides in an earlier order with no setup, demo, novelty or team slide.
This outline reuses their points and figures in the requested order: title, question, setup, the five findings, the
demo, novelty, limits, next steps, team. Rebuilding `deck.pptx` from it means editing TALK_MAP's table; nothing here
changes the deck.

**On screen, numbers stay few:** one or two per finding slide; the rest is for answering questions (09_QA_BANK).

| # | Slide | The point (one sentence) | Figure | Numbers to show | Demo moment (keys) | Time | Speaker |
|---|---|---|---|---|---|---|---|
| S1 | Do thinking modes make chain-of-thought more honest? | The question, the team, the date. | — | — | — | 0:15 | |
| S2 | Where did that answer come from? | A wrong hint can steer an answer inside the model, in the words it writes and in whoever reads it next; our answer to the title question is mixed. | `three_levels.png` | thinking on: the tool named in the private reasoning after 141 of 145 calls, in the final answer of 0 of 143 followed runs (Qwen3-8B, F29) | — | 0:45 | |
| S3 | Setup | Multiple-choice questions with a wrong (or right) hint from the user or a tool; 12 models (8 answering, 4 reviewers); following = the hint's letter in the answer; three levels measured. | `channels.png` (the hint's seven ways in; in `figures/`) | the 54 test questions × 3 runs; the 30 held-out (930 runs a system); the 120 fresh (03_METHODS) | — | 0:50 | |
| S4 | 1. A tool's hint pulls harder than the user's | The same wrong hint moves the answer more from a tool, in every model we tested; much of a pasted block's pull is its claim to be the answer key. | `gate2.png` (second: `authority_ladder.png`) | tool − user, pasted block: +35 [+24, +46] (Qwen3 30B Thinking), +32 [+22, +42] (Olmo 3 7B Think); all 10 readings in three more families (FB1); the answer-key claim closes 68% and 71% of the gap (F35) | — | 1:05 | |
| S5 | 2. The reasoning names the tool; the answer doesn't | The private reasoning names the hint, the final answer almost never; after a tool call the answer is a bare letter, right tool or wrong. | `private_vs_final.png` (second: `bare_after_call.png`) | 208 of 216 against 8 of 216 (keyword counts, F3); bare 80 of 84 (right lookup), 71 of 75 (wrong), 2 of 159 (no tool) (F15) | — | 1:05 | |
| S6 | 3. Inside the model: three layers | In Olmo 3 7B Think, layers 15, 19 and 23 read the hint's letter from the prompt and carry most of its effect; Qwen3-8B replicates with its own three layers. | `readout_by_layer_slide.png` (second: `readout_qwen8b.png`) | 0.90 [0.85, 0.96] (F11); 0.90 [0.76, 1.06] on 16 new questions (F26); Qwen3-8B 21, 22, 29: 0.70 [0.60, 0.83] (F36) | — | 1:00 | |
| S7 | 4. Reviewers defer; the checker holds | An Olmo reviewer stops correcting a wrong tool answer once it sees the trace; only Olmo's two of six reviewers do; a checker that never sees the tool stops every wrong answer. | `trackC_reviewers_slide.png` (second: `pipeline_vs_model.png`) | 59 of 73 alone → 6 and 3 of 73 (F18); all 53 wrong stopped, false alarms 7 of 45 (F24) | — | 1:00 | |
| S8 | 5. Every fix is a trade | No fix beats a one-line instruction without a cost to right hints; consistency training follows far fewer wrong hints but takes fewer right ones; fine-tuning made the answer more candid. | `a40_e2_fixes.png` (second: `gate3_vs_base_slide.png`; `tradeoff_e2.png` is exploratory, say so) | 84 of 694 against 237 of 713, and 347 of 459 against 431 of 476 (F41); 37 of 42 against 18 of 42 (F45) | — | 1:15 | |
| S9 | The demo: four moves on the scratch pad | The pattern on screen with its frequency: the problem, the fix, its cost, and the review team. | live: the local build (pack/demo_shots/ if it fails) | the finder's counts as TALK_MAP gives them: 38 of 114; 26 of 112; 16 of 118 | see the moves below | 2:00 | |
| S10 | What's new and what isn't | Others showed unnamed hints, tool cues said less, authority effects and consistency training; ours are the private/final split after the own call, the readout layers in two models, the review team, and the cost of every fix. | — (two columns of text) | — | — | 0:45 | |
| S11 | Limits | One model for the fixes, one tool format, multiple choice, keyword counts where labels didn't stand, small sets. | — | — | — | 0:40 | |
| S12 | Next steps | Verify the tool independently; treat each fix as a trade; the dial's cost on 120 questions is open. | — | all 53 stopped (F24); −13.8 [−20.0, −7.5] with acceptance −5.8 [−10.8, −1.3] (F38) | — | 0:30 | |
| S13 | Team | Who did what (10_TEAM_AND_PROCESS); questions. | — | — | — | 0:15 | |

**Total: 11:25 on the slides + 0:35 of slack = 12:00.** (0:15 + 0:45 + 0:50 + 1:05 + 1:05 + 1:00 + 1:00 + 1:15 + 2:00
+ 0:45 + 0:40 + 0:30 + 0:15.)

## The demo, S9 (TALK_MAP's "Show me", Nov 23–24)

Setup before the talk: from `cot-disclosure/`, `../.venv/bin/python tools/demo_template/serve.py` (opens
`http://127.0.0.1:8765/demo.html#pad`); full screen; **T** sets the theme. Keys on the pad: **F** the next question
found, **N** the next run, **Enter** replays, **Esc** finishes a run; **1–4** switch parts.

| move | do | point at | time | fallback shot |
|---|---|---|---|---|
| 1. The problem | as it opens: Show me on "No fix took the wrong hint", the 120, a tool call's reply | the finder line (38 of 114 questions), the slip, the red-pen checks (took it: yes) | 0:30 | `demo_shots/move1_problem.png` |
| 2. The fix | click Consistency-trained; on the first question it took the hint too (the red line says so), so then Show me → "the fix held" | the verdict line across the split; 26 of 112 | 0:40 | `move2a_fix_split.png`, `move2b_fix_held.png` |
| 3. The cost | Show me → "the cost" (the hint turns right) | a right hint refused; 16 of 118 | 0:25 | `move3_cost.png` |
| 4. Downstream | Dataset → the review team's items → "Send to the review team" | solver → reviewer → checker → you | 0:25 | `move4_review.png` |

The screenshots are local only (gitignored: they show model text). If the server fails, the double-clicked
`cot-disclosure/results/demo/demo.html` has the drawn questions; the public `docs/demo/index.html` has the frozen results.

## Backup slides

| # | Slide | For the question | Figure | Facts (see 09_QA_BANK) |
|---|---|---|---|---|
| B1 | Why one model for the fixes | "Do the fixes generalize?" | `gate3_vs_base_slide.png` | every fix on Olmo 3 7B Think (F28, F41–F44, F38); the failure holds in eight models (F15–F17, F29, F37, FB1); the readout in two (F36) |
| B2 | The 42 hand-labelled rows | "Is 42 rows enough?" | — (a table) | 37 of 42 against 18 of 42, +45 [+25, +64]; kappa 0.96; J-opus 82 of 84; the sheet not blind in practice (F45) |
| B3 | Multiple choice and the question sets | "Why multiple choice? Which questions?" | — (a table) | the 54 (24 puzzles + 30 MMLU-Pro), the 30 held-out, the 120 fresh, set A's 16, C4's 53 and C15's 100 items (03_METHODS) |
| B4 | Related work, side by side | "How is this different?" | — (07_RELATED_WORK's table) | agrees / extends / differs per paper |
| B5 | Are the demo's examples cherry-picked? | "Did you pick the good ones?" | `demo_shots/move1_problem.png` | the finder counts every question and orders matches by a seed, never by outcome; 38 of 114 against the frozen 85 of 233 (TALK_MAP) |
| B6 | Statistics and the second model | "How sure are you?" | `readout_qwen8b.png` | Wilson intervals; paired bootstrap clustered by question; "too few questions" under 5; Qwen3-8B 0.70 [0.60, 0.83] (F36) |

## If short on time (cut in this order)

1. S9's move 3 (keep the cost as one sentence on S8).
2. S6's second figure and Qwen3-8B number (keep 0.90).
3. S3 to 0:30 (one sentence and the model count).
4. S10 to 0:30 (two lines: not new / ours).
