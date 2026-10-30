# Questions a reviewer would ask that we can't answer yet

Each question: why it matters, and which runs answer it. Updated Oct 29 23:15: C11 and C12 are in (F22, F23);
added C13 (Sol), C14 (exploratory), C15 (fresh items, running) and B15 (a disclosure instruction, running).
The runs of Oct 28–29:
- **A:** set A localization replication (Voyager runs and probes tonight; Steps 9/10 on Sol).
- **B1:** provenance-scaled attention (code tonight, Sol jobs).
- **B2:** a learned per-head provenance bias (code tonight, training later).
- **C11:** more reviewer models.
- **C12:** the redacted cue.
- **C13:** a third and fourth reviewer family (Granite, Mistral) on Sol, after set A.
- **C14:** two reviews that disagree, as a cheaper check (exploratory, saved data).
- **C15:** 100 fresh items: F18, H23 and C14's rule, pre-registered.
- **B15:** one instruction asking the final answer to say what it is based on.
- **Gate 3:** batch 3's table and figures in one command (`finetune/gate3.py`) when its files are back.

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
   - Keyword counts until the hand labels (L3, L5). Not answered yet; the raters' one-page guide is ready
     (`docs/progress/RATER_GUIDE.md`).
10. **Couldn't you just ask the model to say where its answer came from?** (F15: after a tool call the final answer
    is a bare letter.)
    - **Answered by B15:** one added instruction; does naming the tool after a call rise (Thinking: 3 of 54 before),
      does the bare letter fall, and at what cost to correct-tool acceptance and no-hint accuracy?
    - `[Thinking: names the tool after a call ___ of ___ (before 3 of 54); bare ___; Instruct: ___ (before 35 of 162)]`

## Thread 2: automation bias in reviewers

1. **Is the deference one model's quirk?**
   - **Partly answered by C11 (F22):** Olmo 3 7B Instruct defers too (−42 [−58, −28]); Qwen3 30B Thinking doesn't
     (+1 [−6, +10]). In four reviewers it follows the family, not size or thinking (*tentative*: two per family).
   - **C13** adds two families on Sol (Granite, Mistral): does family still predict it?
     `[Granite ___; Mistral ___]`
2. **What does the reviewer defer to: the visible letter or the reasoning?**
   - **Answered in part by C12 (F23):** with the tool's letter redacted, Olmo corrects 23 and 24 of 73 (C4: 6 and 3;
     answer only 59). The letter is part of the cue, not most of it.
   - By set, the gain was on the matched puzzles: **hypothesis H23** (re-solvable items), tested in **C15** on fresh
     items, split by the reviewer's own answer_only result. `[restoration where it re-solves ___, where it doesn't ___]`
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
   - C15's fresh items include hard puzzles and MMLU-Pro outside the evaluation categories: its floor there is
     reported. Items the solver gets wrong without the tool are still the open test.
   - **Is there a cheaper check?** C14 (exploratory): escalating when the answer_only and trace-seeing reviews
     disagree never beat the checker's pipeline on catches; with a non-deferring reviewer it matched it at about a
     third of the tokens, with a deferring one it added false alarms. **C15 (c)** tests that on fresh items.
6. **Does any of it hold on new items?**
   - **Answered by C15 (a):** F18's comparison on 100 fresh items, C11's rule. `[Olmo ___; Qwen3 ___]`
7. **One solver, one tool format?**
   - Yes (Qwen3 30B Thinking; the answer key's JSON).
   - Not answered tonight. Next: Track B's other models as solvers (steered cases exist for all
     three).
