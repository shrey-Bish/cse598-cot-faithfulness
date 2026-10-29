# Outlines (bullets; the team writes the prose)

Evidence by F-number ([`docs/FINDINGS.md`](../FINDINGS.md)), claims by number
([`CLAIMS.md`](CLAIMS.md)). **Missing** marks what a reviewer would ask for and we don't have yet.

## Thread 1: "Where tool hints are read, and a repair that acts there"

1. **Introduction**
   - Thinking models follow wrong hints from tools more than from users (1.1), and hide it in the
     final answer (1.2).
   - We locate the readout (1.4) and repair it where it lives (1.7, 1.8). Input-embedding
     provenance tags don't help (1.6).
   - Contributions: the tool-vs-user gap in 3 models; a layer-level localization replicated on
     separate questions; a training-free, deployable fix with its trade-off; a trained per-head
     bias.
2. **Setup**
   - Models: Olmo 3 7B Think (pinned Think format, rendered by us); Track B's Qwen3 30B Thinking and
     Instruct.
   - Channels: user, pasted tool block, inserted tool turn (declared), real tool call; system note.
   - Questions: 24 puzzles and 30 MMLU-Pro (evaluation); the training pool's 34 validation questions
     (set A, localization only).
   - Statistics: X of Y with Wilson intervals; differences with a bootstrap clustered by question;
     at least 5 questions per group.
3. **Behavior** (F1, F2, F3, F15–F17)
   - Gate 2 table: 3 models × channels.
   - Private vs final mention; bare final answers after a tool call.
   - **Missing:** hand labels (L3, L5).
4. **When the hint takes over** (F4, F5, F14; early answering)
   - Takeover curves; late takeovers on few questions; the lead swings.
   - **Missing:** more questions (set A adds some).
5. **Where it is read** (F10, F11, F12, F13)
   - Attention at the answer (Step 9) and activation patching (Step 10) agree on layers 15/19/23.
   - Three heads separate followed from resisted. The direct path does more than the written
     repetition.
   - **Missing:** replication on set A (tonight's runs + Sol tomorrow). This is what makes section
     6 non-circular.
6. **Repair**
   - Training (F20): LoRA learns the taught text. LoRA on the three layers reaches 85–90% of it.
     Tags don't help.
   - B1: inference-time downweighting of tool-span keys in the three layers.
     - Alpha chosen on set A.
     - Evaluated on the held-out 30: wrong-hint following vs correct-hint acceptance vs no-hint
       accuracy.
     - Deployable vs oracle spans.
   - B2: a learned per-head bias.
   - **Missing:** all behavioral numbers (batch 3; B1 Sol jobs; B2 training).
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
   - Agent pipelines add a reviewer model as oversight. We show a reviewer shown the solver's tool
     trace stops checking and defers to the tool (2.1, 2.2).
   - Two prompt fixes fail (2.3). We isolate the cue (2.4). The only check that worked never saw
     the tool (2.5).
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
   - C11: more reviewer models (family, size, thinking).
   - C12: redacted letter vs redacted reasoning.
   - **Missing:** tonight's numbers.
6. **What works**
   - The blind re-ask checker (73 of 75; false alarms at the floor).
   - Its limit: items the model can't answer alone.
7. **Related work:** automation bias (Skitka; Parasuraman & Manzey; Goddard); LLM-as-judge;
   sycophancy; knowledge conflicts (Xie; ClashEval).
8. **Limitations**
   - One solver and one oracle design.
   - Answer-key wording of the tool ("study guide v2").
   - Reviewer temperature 0.6 and Voyager seeds not deterministic.
   - Kind and set confounded.

## Figures available now (`docs/paper/figures/`, from the tracked summaries; `tools/paper_figures.py`)

- `reviewer_by_prompt`: thread 2, sections 3–4.
- `readout_by_layer`: thread 1, section 5 (F11).
- `taught_loss`: thread 1, section 6 (F20).
- Each has a CSV with every plotted number.
