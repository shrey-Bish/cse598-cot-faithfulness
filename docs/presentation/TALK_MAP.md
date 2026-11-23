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
[Hint Explainer's](../../archive/superseded/explainer_2026-11-14/explainer.html) seven tour scenes (`tools/explainer/tour.json`): 1 User's guess, 2 Tool's answer,
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
- The attention dial replicated on 120 questions; its cost to right hints is open (F38)

## The live run: 12 minutes from the demo

**The live run replaces the Hint Explainer.** The table's "Explainer scene" column is kept as it was, but the talk is
given from the demo, not from those scenes (the explainer is archived). The deck is the backup: each moment below
says which slide to switch to if it fails. Added Nov 23, 09:16; the table, its times and its figures are unchanged.
This section is prose and lists only, so [`make_deck.py`](../../cot-disclosure/tools/make_deck.py), which reads
the rows of the table above and the two lists under "Limits and next steps lines", is not affected by it.

**Setup.** Open the local build `cot-disclosure/results/demo/demo.html` (it replays recorded runs; the public
[`docs/demo/index.html`](../demo/index.html) has the frozen results only, with no Enter, N, M or C), full screen, with
the deck open in a second window on slide 0. Press **T** once to pick the theme before the talk. The questions on the
bench are drawn by a stored seed (`draw.json`): the first question of each test is the first one shown, and **N**
gives the next. If a run's text says "outcome only: this run's text is on Sol", the Sol copy is missing from this
build; the frozen panel and the red marks still work, so go on.

**Keys.**
- Anywhere: **1** the map, **2** the test bench, **3** the result sheets; **← →** step; **Esc** returns the map home;
  **R** replays the page; **T** switches the theme.
- On the bench: **Shift+1 to Shift+6** choose a test; **Enter** runs; **N** the next question; **M** run 20 more; **C**
  compare; **P** the prompt; **L** a hand-labelled answer (test 4 only); **Esc** skips a run or closes a pane.
- The tests: 1 Tool vs person, 2 Authority, 3 Thinking on and off, 4 The fixes, 5 Review teams, 6 Inside the model.
- The map's 11 steps: 1 Questions, 2 The hint, 3 Models, 4 Running it, 5 Architecture, 6 Layers, 7 Fine-tuning, 8
  Training, inside, 9 Other fixes, 10 Review team, 11 Checking. Click a step on the map home or its mark in the strip.
- The ten sheets: 1 setup, 2 tool against person, 3 authority, 4 the quiet answer, 5 does thinking help, 6 inside the
  model, 7 review teams, 8 the trade-off, 9 candid answers, 10 what we learned. Each sheet has a "Run this test" and a
  "How we did this" button.

**Marks.** *Live run* = a recorded run replayed on the bench (Enter, N, M, C), the risky kind. *Live page* = flipping
pages of the map or the sheets: no run, so little to go wrong. **One rule for every failure: press R once; if the page
is not right within 5 seconds, say the row's point from whatever is on screen and switch to the named slide. Never
debug on stage.** Screens are described by what to press and point at, not by position, because map steps 1, 6 and 7,
the overview and sheet 8 are being reworded.

**The moments, in the table's order** (the time is the row's):

- **Slide 0, title (0:20): live page.** Press **1**: the map home. Say the question and the team; point at the six
  stops and the three pencil brackets (models and sources, inside the model and the fixes, downstream review). If it
  fails: slide 0.
- **Slide 1, where did that answer come from (1:00): live page.** Stay in part 1. **→** to step 2, the hint: point at
  the switch of source and the exact prompt, "only who says it changes". Then **Esc** to the map home and point at the
  three places to look (inside the model, what it wrote, the review team): these are the three levels. If it fails:
  slide 1 (`three_levels.png`).
- **Slide 2, tools pull harder than users (0:50): live run.** Press **2**, then **Shift+1** (Tool vs person). Pick
  Qwen3 30B Instruct (the default) with the tool call as the hint, **Enter**: point at the tool slip, then at the red
  mark on the hint's letter in the final answer. Press **C** to compare with the user's hint on the same
  question, then point at the two frozen counts: the same wrong letter, a lower pull from the user. If it fails: **3**, then **→** once to
  sheet 2 (the same comparison, no run); if that fails too, slide 2 (`gate2.png`).
- **Slide 3, Level 1: three layers read the tool's letter (0:50): live run.** **2**, **Shift+6** (Inside the model),
  **Enter**: for the drawn question, point at the layers lighting up one at a time and the total, then at the frozen
  panel's share for layers 15, 19 and 23 on the 16 new questions. If it fails: **3** and **→** to sheet 6 (the three
  layers and their total, no run); then slide 3 (`readout_by_layer_slide.png`).
- **Slide 4, Level 1 on a second model (0:30): live page.** On sheet 6, point at the note beside the total: Qwen3 8B
  has its own three layers, less concentrated. Or press **1** and open step 6 and choose its Qwen3 8B view. No run.
  If it fails: slide 4 (`readout_qwen8b.png`).
- **Slide 5, the reasoning names it, the answer doesn't (1:00): live run.** **2**, **Shift+3** (Thinking on and off),
  Qwen3 8B with thinking on, **Enter**: point at the scratch work naming the lookup tool, then at the final answer
  that doesn't, then the two marks. Point at the frozen panel's "named the tool in the scratch work" and "in the final
  answer" lines. Say once that these are keyword counts. If it fails: **3**, **→** three times to sheet 4 (the quiet
  answer); then slide 5 (`private_vs_final.png`).
- **Slide 6, after a tool call the answer goes bare (1:00): live run.** **2**, **Shift+1**, Qwen3 30B Thinking with
  the tool call: **Enter**, point at the final answer, a bare letter. **N** for a second question: the same.
  Optionally **P** to show the exact prompt, and **Esc** to close it. If it fails: sheet 4 (key **3**, **→**
  three times); then slide 6 (`bare_after_call.png`).
- **Slide 7, tool or authority (0:50): live run.** **2**, **Shift+2** (Authority), Qwen3 30B Instruct, the claim
  "the official manual", **Enter**; then **C** to compare with the plain user's guess. Point at the sticky note's
  wording: only the source changes. Then pick the pasted block and the tool call in the same row and point at the
  frozen counts rising along the ladder. If it fails: sheet 3 (key **3**, **→** twice); then slide 7
  (`authority_ladder.png`).
- **Slide 8, does more thinking help (0:50): live run.** **2**, **Shift+3**: gpt-oss 20B, effort low, **Enter**, then
  **C** (effort high): point at the frozen following counts, which barely move. Then Qwen3 8B, **C** between thinking
  off and on: the call count jumps. Say "mixed". If it fails: sheet 5 (key **3**, **→** four times); then slide 8
  (`b17_effort.png`).
- **Slide 9, the fix: none beats one line (1:10): live run.** **2**, **Shift+4** (The fixes). Choose Fine-tuned (or
  Consistency), the hint "tool turn, wrong", **Enter**; **C** to compare with the instruction; point at the frozen
  count of wrong hints followed. Then change the hint to "tool turn, right" and **Enter** again: point at what the fix
  now refuses. **M** for twenty more if there is time. If it fails: sheet 8 (key **3**, **→** seven times; being
  reworded, so point at the dots, not at positions); then slide 9 (`gate3_vs_base_slide.png`, `a40_e2_fixes.png`).
  Keep **L** (a hand-labelled answer, test 4) for Q&A about candour (sheet 9), not for the talk.
- **Slide 10, inside the fixed model (1:00): live page.** **1**, click step 8 (Training, inside): point at the two
  groups of layers swapped into the original, the reasoning for fine-tuning and the layers before the readout for
  consistency training. Then **→** to step 9 and turn the dial on the tool's turn: fewer wrong hints, at a cost to
  correct ones. If it fails: slide 10 (`readout_lora_vs_base.png`, `b1r2_vs_b1.png`).
- **Slide 11, reviewers defer to the trace (1:00): live run.** **2**, **Shift+5** (Review teams), the reviewer Olmo
  3.1 32B Instruct. Set "It sees" to the answer only and **Enter** (the solver is replayed, then the reviewer:
  "corrected it"); then set it to the tool log and **Enter** again ("let it through"). Point at the red words and the
  frozen count. Then pick Qwen3 30B Instruct and point at its frozen count: it holds. If it fails: sheet 7 (key **3**, **→** six times); then slide 11 (`trackC_reviewers_slide.png`,
  `reviewer_by_prompt_slide.png`).
- **Slide 12, across agents and what holds (0:50): live page.** Stay on test 5, choose "checker on" and **Enter**: point at the checker's
  "Flagged" stamp, then at the frozen count of wrong tool answers stopped. The handoff note and the unverified tag have no page in the demo: say them
  from the slide's numbers, or, if that is too much to hold in the head, switch to slide 12 (`c25_hops.png`,
  `pipeline_vs_model.png`) for this moment only and come back. If it fails: sheet 7's checker panel, then slide 12.
- **Slide 13, limits and next steps (0:50): live page.** **3**, then click the last mark in the strip of timing marks
  (sheet 10, what we learned). Read the limits and the next steps from the two lists above. If it fails: slide 13.

**If the whole demo fails** (blank page, wrong file): keep talking from slide 1 on, in the same order and with the same
times, and use the recorded screens in `cot-disclosure/results/demo/screens_answer_sheet/` only for questions.
**Before the talk:** run each live moment once with the same keys (the replay is the same each time except M's
sample), and check that the clock and the theme are as wanted.

## Not in the deck (more figures for questions, in `docs/paper/figures/`)

`a39_e2_fixes.png` and `a39_e2_parts.png` (A39, F44: the provenance wrapper and LoRA + note on E2), `c19_authority.png`
(C19, FC1), `b16_authority.png` (F35, before `authority_ladder.png`), `tradeoff_e2.png` (exploratory, post hoc).
