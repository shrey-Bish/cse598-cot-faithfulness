# Talk map: the final presentation (Nov 24, about 12 minutes)

**What it is.** One row a slide, in talk order: the slide's short title, its one-line point with the key number and its
code, the figure file(s), the Hint Explainer scene that fits (if any), the time, the owner. **Built for
[`cot-disclosure/tools/make_deck.py`](../../cot-disclosure/tools/make_deck.py)**, which reads the table below to build
`docs/presentation/deck.pptx`: change a title, a figure, or a row here and rebuild, so the deck and this map cannot
drift. Row 0 is the title slide; row 13 is the final "Limits and next steps" slide, whose lines are the two lists under
the table. A slide shows its row's first figure at full size; a row's second figure gets a backup slide of its own (the
same title with "(backup)") after the limits slide, since two side by side were too small to read (Nov 19): the deck has
14 slides in the talk and 4 backups (rows 9 to 12). To show a second figure in the talk, move its slide up. The deck has no speaker notes and no paragraphs: **the team writes the words and the notes**.

**Speaker column: blank for us to fill.** **Total time: 12:00** (title slide 0:20, thirteen content slides 11:40).
Reading aloud: a point's number is for the speaker to know, not for the slide to carry.

**Sources.** The plan's [final presentation map](../PLAN.md) (order, owners, figures); [`FINDINGS.md`](../FINDINGS.md)
(F-numbers), [`FINDINGS_B.md`](../trackB/FINDINGS_B.md) (FB1), [`FINDINGS_C.md`](../trackC/FINDINGS_C.md) (FC1–FC4);
the Gate 3 draft in the plan; REPORT §10 for the limits. Results are frozen (tag `results-freeze-2026-11-18`): every
number here is as FINDINGS reads it. Figures are in [`docs/paper/figures/`](../paper/figures/). Scenes are the
[Hint Explainer's](../demo/explainer.html) seven tour scenes (`tools/explainer/tour.json`): 1 User's guess, 2 Tool's answer,
3 Authority, 4 Inside the model, 5 The quiet answer, 6 Review team, 7 Fixes.

**The demo (Nov 22).** [`docs/demo/index.html`](../demo/index.html), an answer sheet in three parts, driven by the
presenter (no autoplay): key 1 the project map (← → through its 11 steps), key 2 the test bench (Shift+1–6 a test; the
local build `cot-disclosure/results/demo/demo.html` replays recorded runs: Enter, N, M, C, P), key 3 the ten result
sheets (← →), each with "Run this test" and "How we did this". The scene column above still names the Hint Explainer's
scenes; the matching result sheets: user's guess and tool's answer, item 2; authority, 3; the quiet answer, 4;
thinking, 5; inside the model, 6; review team, 7; fixes, 8 and 9.

| # | Slide title | The point | Figure(s) | Explainer scene | Time | Owner | Speaker | Evidence (footer) |
|---|---|---|---|---|---|---|---|---|
| 0 | Do thinking modes make chain-of-thought more honest? | The title slide: the question, the team, the date. | — | — | 0:20 | everyone | | |
| 1 | Where did that answer come from? | A wrong hint can steer an answer from inside the model, in the words it writes, and in whoever reads it next; the title question is answered mixed (story item 5). | `three_levels.png` | — | 1:00 | Ritik | | story, F29, F37, FB1 |
| 2 | Tools pull harder than users | The same wrong hint moves the answer more from a tool than from the user: tool minus user, pasted block, +35 (Qwen3 30B Thinking), +21 (Instruct), +32 (Olmo 3 7B Think) points; clear in all 10 readings in three more families (FB1). | `gate2.png` | 1 User's guess, 2 Tool's answer | 0:50 | Arsha | | F15, F16, F17, F29, F37, FB1 |
| 3 | Level 1: three layers read the tool's letter | In Olmo 3 7B Think, layers 15, 19 and 23 hold 0.90 [0.85, 0.96] of the drop at the takeover; on 16 new questions 0.90 [0.76, 1.06] (F26); three heads separate followed from resisted runs, +0.068 [+0.044, +0.088] (F32). | `readout_by_layer_slide.png` | 4 Inside the model | 0:50 | Ritik | | F11, F12, F26, F32 |
| 4 | Level 1 on a second model | In Qwen3-8B, three layers (21, 22, 29) chosen on the puzzles hold 0.70 [0.60, 0.83] of the drop on MMLU-Pro: replicates, less concentrated than Olmo's 0.90. | `readout_qwen8b.png` | — | 0:30 | Ritik | | F36 |
| 5 | Level 2: the reasoning names it, the answer doesn't | Private reasoning names the hint in 208 of 216 runs, the final answer in 8 of 216; keyword counts, since the hand labels didn't pass Gate 2's label rule (Ritik against the AI judges' majority: kappa private 0.472, final 0.234; under 0.6). | `private_vs_final.png` | 5 The quiet answer | 1:00 | Ritik and Shrey | | F3, F29 |
| 6 | Level 2: after a tool call, the answer goes bare | After a call the final answer is a bare letter, right or wrong tool: 80 of 84 after good lookups, 71 of 75 after bad, 2 of 159 with no tool (F15). One instruction brings the source back (Thinking bare 51 of 54 to 30 of 63) and the model still takes the wrong letter as often (F25). | `bare_after_call.png` | — | 1:00 | Arsha | | F15, F25, F29 |
| 7 | Tool or authority? | A user's "my course answer key says" closes 68% and 71% of the gap to the pasted block in Qwen3 and all of it in Olmo (F35); "the official solution manual" moves all three models more than "a classmate" (+41, +12, +32 points; F40). | `authority_ladder.png` | 3 Authority | 0:50 | Ritik, then Arsha | | F35, F40 |
| 8 | Does more thinking help? | In gpt-oss-20b, effort low to high changes neither following (+7 [−1, +16]) nor the bare answer (−5 [−10, 0]); in Qwen3-8B thinking on puts the tool in the reasoning (it names the tool after 141 of 145 calls) but not in the final answer (0 of 143 followed runs name it; F29). Mixed. | `b17_effort.png` | — | 0:50 | Arsha | | F37, F29 |
| 9 | The fix: fewer wrong hints, none beats one line | Gate 3 met: every trained version follows fewer wrong hints (LoRA −10 [−16, −4]), but the one-line instruction does as well (−13 [−21, −6]) (F28). Consistency training: 84 of 694 wrong hints followed against 237 of 713, but 347 of 459 correct taken against 431 of 476 (F41). | `gate3_vs_base_slide.png`, `a40_e2_fixes.png` | 7 Fixes | 1:10 | Ritik | | F28, F41, F43, F44 |
| 10 | Inside the fixed model | LoRA acts in the reasoning: on base's own reasoning its weights pull toward the hint harder, −0.72 logits [−1.02, −0.39] removed (F39); A40 acts before the readout, layers 0–14, +0.68 logits [+0.17, +1.18] (F42). At inference, scaling attention to the tool turn: 82 of 240 to 49 of 240 (−13.8 [−20.0, −7.5]), at a cost to correct hints (F38). | `readout_lora_vs_base.png`, `b1r2_vs_b1.png` | — | 1:00 | Ritik | | F38, F39, F42 |
| 11 | Level 3: reviewers defer to the trace | Olmo 3.1 32B corrects 59 of 73 wrong tool answers from the answer alone, 6 and 3 of 73 once it sees the solver's reasoning or the tool log (F18); only Olmo's two of six reviewers defer (F30); the solver's citation is the cue: 25 against 9 of 34 when removed (F34). | `trackC_reviewers_slide.png`, `reviewer_by_prompt_slide.png` | 6 Review team | 1:00 | Shrey | | F18, F22, F30, F34, FC1 |
| 12 | Across agents, and what holds | A handoff note puts the tool back as the source (plain note 35 of 55, keep note 55 of 55; FC2); an unverified tag gives the reviewer no change on catches (+8 [−2, +19]; FC3); the checker, which re-solves without the tool, stopped all 53 wrong answers (F24). | `c25_hops.png`, `pipeline_vs_model.png` | — | 0:50 | Shrey | | F24, FC2, FC3, FC4 |
| 13 | Limits and next steps | Limits of one model, one tool format and keyword counts, and what to do: verify the tool independently, treat each fix as a trade. | — | — | 0:50 | everyone | | F3, F24, F38, F41, F44 |

**Total: 12:00.**

## Limits and next steps lines

Drafts, each line from FINDINGS, REPORT §10 or the Gate 3 draft's limits (codes in the table's last row); the team
rewrites them. Short lines only.

**Limits**

- One model for the fixes: Olmo 3 7B Think, MMLU-Pro evaluation categories
- One tool format, one solver in Track C
- Keyword counts where the hand labels are not met (F3)
- Labels: one human and one AI rater, not two humans
- 30 held-out questions cannot resolve 5-point limits (F38)

**Next steps**

- Verify the tool independently: the checker stopped all 53 wrong answers (F24)
- Provenance labels alone do not help (F44, FC3)
- Every fix we tried trades wrong hints followed for correct ones (F41)
- A powered B1 replication needs about 107 to 245 fresh questions (F38)

## Not in the deck (more figures for questions, in `docs/paper/figures/`)

`a39_e2_fixes.png` and `a39_e2_parts.png` (A39, F44: the provenance wrapper and LoRA + note on E2), `c19_authority.png`
(C19, FC1), `b16_authority.png` (F35, before `authority_ladder.png`), `tradeoff_e2.png` (exploratory, post hoc).
