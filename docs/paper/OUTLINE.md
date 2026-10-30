# Outlines (bullets; the team writes the prose)

Evidence by F-number ([`docs/FINDINGS.md`](../FINDINGS.md)), claims by number
([`CLAIMS.md`](CLAIMS.md)). **Missing** marks what a reviewer would ask for and we don't have yet.

## Thread 1: "Where tool hints are read, and a repair that acts there"

1. **Introduction**
   - Thinking models follow wrong hints from tools more than from users (1.1), and hide it in the
     final answer (1.2).
   - We locate the readout (1.4) and repair it where it lives (1.7, 1.8). Input-embedding
     provenance tags don't help (1.6).
   - Contributions: the tool-vs-user gap in 4 models (thinking on and off in one of them); a layer-level
     localization replicated on separate questions (set A, F26); a training-free, deployable fix with its
     trade-off; a trained per-head bias; and a cautionary result on fine-tuning for disclosure (F28, waiting
     on labels).
2. **Setup**
   - Models: Olmo 3 7B Think (pinned Think format, rendered by us); Track B's Qwen3 30B Thinking and
     Instruct.
   - Channels: user, pasted tool block, inserted tool turn (declared), real tool call; system note.
   - Questions: 24 puzzles and 30 MMLU-Pro (evaluation); the training pool's 34 validation questions
     (set A, localization only).
   - Statistics: X of Y with Wilson intervals; differences with a bootstrap clustered by question;
     at least 5 questions per group.
3. **Behavior** (F1, F2, F3, F15–F17, F25, F29)
   - Gate 2 table: 4 models × channels; Qwen3-8B with thinking on and off.
   - Private vs final mention; bare final answers after a tool call.
   - The title question in the same weights (F29): thinking puts the tool in the private reasoning
     (141 of 145) and not the final answer (0 of 143), and raises the call rate.
   - Disclosure can be prompted, but it doesn't reduce deference (B15, F25).
   - **Missing:** hand labels (L3, L5).
4. **When the hint takes over** (F4, F5, F14; early answering)
   - Takeover curves; late takeovers on few questions; the lead swings.
   - **Missing:** more questions (set A adds some).
5. **Where it is read** (F10, F11, F12, F13)
   - Attention at the answer (Step 9) and activation patching (Step 10) agree on layers 15/19/23.
   - Three heads separate followed from resisted. The direct path does more than the written
     repetition.
   - **Set A replicates (F26):** 0.90 [0.76, 1.06] at 15/19/23 on 16 questions not used to find them;
     the same three layers are the largest drops. This makes section 6 non-circular.
   - **Missing:** set A's Step 9 (F12's three heads, pre-registered Oct 30).
6. **Repair**
   - Training (F20): LoRA learns the taught text. LoRA on the three layers reaches 85–90% of it.
     Tags don't help.
   - B1: inference-time downweighting of tool-span keys in the three layers.
     - Alpha chosen on set A.
     - Evaluated on the held-out 30: wrong-hint following vs correct-hint acceptance vs no-hint
       accuracy.
     - Deployable vs oracle spans.
   - B2: a learned per-head bias.
   - **Gate 3, interim (F28):** LoRA passes by the rule, and doesn't beat a one-line instruction (+3
     [−1, +8]), and its false-disclosure candidates rise (+10 [+2, +18]) while the instruction's fall.
     Candidate cautionary claim: fine-tuning for disclosure reduced hint-following no more than an
     instruction, and may have taught the model to claim checks it didn't do.
   - B1's alpha from set A (F27): 0.25 deployable, 0.5 oracle.
   - **Missing:** the false-disclosure labels; three trained versions; B1's generation; B2 training.
7. **Related work** ([`RELATED_WORK.md`](RELATED_WORK.md)): CoT faithfulness; patching; ITI and PASTA;
   instruction hierarchy, ISE, StruQ and SecAlign; knowledge conflicts.
8. **Limitations**
   - One model for the mechanism.
   - Forced answers off-distribution.
   - Keyword counts until labels.
   - The serving-format confound (F2).
   - Teacher-forced loss.

## Thread 2: "Automation bias in LLM reviewers"

1. **Introduction**
   - Agent pipelines add a reviewer model as oversight. Deference to the solver's tool trace is
     family-specific: the Olmo reviewers stop checking and defer to the tool, 2 of 6 reviewers over 4
     families (2.1, 2.2).
   - Prompt fixes don't help the deferring family (2.3). We isolate the cue (2.4). The blind checker
     holds for all six reviewers (2.5).
2. **Setup** (F18's design)
   - Solver Qwen3 30B Thinking with a forced lookup. A seeded oracle makes about half the lookups
     wrong.
   - Reviewer variants: answer only / + explanation / + private reasoning / + tool log.
   - Checker: re-ask without the tool. No-tool team = false-alarm floor.
   - 53 Track B items (steered and matched), 3 repeats.
   - Kind and set confounded; reported by kind × set.
3. **Deference** (F18)
   - Correct-rate by variant and reviewer, both lookup types: the two sides.
   - The reviewer names the answer key. "As good as the tool."
   - Figure: `figures/reviewer_by_prompt` (C4 bars).
4. **Fixes that fail** (F19, F21)
   - The warning sentence; commit first (own answer kept as the first turn).
   - Figure: C9 and C10 bars.
5. **Generality and the cue**
   - C11 and C13: six reviewers, four families (F22, F30). Only Olmo's two defer; Granite's interval is
     wide (to −26).
   - C15: the deference replicates on 100 fresh items (F24).
   - C12 and C15: redacting the tool's letter restores part of the check (F23, F24).
   - C16 (F31): a final answer that names the tool makes the Olmo reviewer correct fewer wrong answers
     (−21 [−34, −8]); Qwen3 unchanged. Disclosure without independence doesn't help.
   - C17 (F33): a fixed sentence naming the tool doesn't do it (+0 [−11, +11] against own working); the drop
     went with the solver's explanations. C18 (F34): removing the solver's tool-citing sentences restores the
     check (+47): the reviewer follows the citation of the tool's letter as authority.
6. **What works**
   - The blind re-ask checker (73 of 75; false alarms at the floor), with every reviewer (C13) and on
     fresh items (53 of 53, C15).
   - A cheaper check from two disagreeing reviews fails on fresh items (C14 → C15, 2.6).
   - Its limit: items the model can't answer alone.
7. **Related work:** automation bias (Skitka; Parasuraman & Manzey; Goddard); LLM-as-judge;
   sycophancy; knowledge conflicts (Xie; ClashEval).
8. **Limitations**
   - One solver and one oracle design.
   - Answer-key wording of the tool ("study guide v2").
   - Reviewer temperature 0.6 and Voyager seeds not deterministic.
   - Kind and set confounded.
   - Two reviewers in the deferring family; Granite's own check is weak, so its "doesn't defer" has less
     room.

## Figures available now (`docs/paper/figures/`, from the tracked summaries; `tools/paper_figures.py`)

- `reviewer_by_prompt`: thread 2, sections 3–4.
- `readout_by_layer`: thread 1, section 5 (F11).
- `taught_loss`: thread 1, section 6 (F20).
- Each has a CSV with every plotted number.
