# Questions a reviewer would ask that we can't answer yet

Each question: why it matters, and which of tonight's runs (Oct 28–29) or the next Sol jobs answer
it. Tonight's runs:
- **A:** set A localization replication (Voyager runs and probes tonight; Steps 9/10 on Sol).
- **B1:** provenance-scaled attention (code tonight, Sol jobs).
- **B2:** a learned per-head provenance bias (code tonight, training later).
- **C11:** more reviewer models.
- **C12:** the redacted cue.

`[___]` marks a number to fill in.

## Thread 1: localization and repair

1. **Were the layers and heads found on the questions you then evaluate the fix on?**
   - Yes, so far. F11 and F12 used the 30 MMLU-Pro evaluation questions.
   - **Answered by A:** the same readout measure on the 34 validation questions, used in neither
     training nor evaluation.
   - `[share of the hint-row drop at 15/19/23, cut (ii), set A = ___ (questions ___); evaluation set 0.90 [0.85, 0.96]]`
2. **Is the readout specific to these three layers, or do all full-attention layers do it?**
   - F11 says the other five full layers read almost nothing on the evaluation set.
   - **Answered by A** on separate questions. `[other full layers' share on set A = ___]`
3. **Does a fix that downweights the tool span just make the model ignore tools?**
   - **Answered by B1:** the trade-off curve, wrong-hint following against correct-hint acceptance,
     and no-hint accuracy at the chosen alpha and at alpha = 1.
   - `[following ___ → ___; acceptance ___ → ___; no-hint accuracy ___ → ___]`
4. **Can a real system apply it?**
   - The deployable version acts only on tool-role spans (the inserted tool turn), which the
     framework knows. The oracle also marks a pasted block.
   - **Answered by B1**, reported apart. `[deployable ___; oracle ___]`
5. **Was alpha tuned on the test set?**
   - No, by design. Alpha is chosen on set A's forced answers before any generation on the
     held-out 30.
   - **Answered by A + B1's first Sol job.** `[alpha* = ___]`
6. **Why should a per-head bias beat input-embedding tags?**
   - The tags did nothing measurable in loss (F20). B2 puts the provenance signal where the hint is
     read.
   - **Answered by B2's training** (loss by part as in S7, then behavior), not tonight.
7. **Does training change behavior, not just loss?**
   - **Answered by batch 3** (evaluation jobs queued on Sol; Gate 3), not tonight.
8. **One model?**
   - The mechanism is Olmo 3 7B Think only. Behavior (Gate 2) holds for 3 models.
   - Not answered tonight. Next: Steps 9/10 on a second open model.
9. **Are the mention counts real acknowledgments?**
   - Keyword counts until the hand labels (L3, L5). Not answered tonight.

## Thread 2: automation bias in reviewers

1. **Is the deference one model's quirk?**
   - It is one of two so far (F18).
   - **Answered by C11:** at least two more reviewer models varying family, size and thinking.
   - `[plus_private − answer_only on bad lookups, per model: ___]`
2. **What does the reviewer defer to: the visible letter or the reasoning?**
   - **Answered by C12:** the redacted tool log and redacted private reasoning.
   - `[Olmo: redacted plus_private ___ of 73 (C4: 6), redacted plus_tool_log ___ of 73 (C4: 3); Qwen3: ___]`
3. **Is the deference just reasonable trust in an answer key?**
   - Partly. On good lookups it helps (67 → 84 of 84).
   - Our point is that the independent check disappears: "as good as the tool" (F18: 92 and 89 of
     159 vs the tool's 84).
   - The paper should show both sides at other bad-lookup rates (a reweighting, no new calls).
4. **Would a better prompt fix it?**
   - Two failed: a warning (F19) and committing first (F21).
   - Not answered tonight: a pre-registered set of wordings, or a structural fix (the trace
     withheld).
5. **Does the checker work when the model can't answer without the tool?**
   - Not tested. Its false-alarm floor is already 18% on steered MMLU-Pro (F18).
   - Next: items the solver gets wrong without the tool.
6. **One solver, one tool format?**
   - Yes (Qwen3 30B Thinking; the answer key's JSON).
   - Not answered tonight. Next: Track B's other models as solvers (steered cases exist for all
     three).
