# Questions a reviewer would ask that we can't answer yet

Each question: why it matters, and which runs answer it. **Edited by:** Ritik. Updated Nov 3: B1 (F38) on questions 3
and 4, L4 part 1 (F28) on 7, A37 (F36) on 8, L3 on 9. Nov 1: B16 (F35) on question 3. Oct 31 16:40: Gate 3 final (F28). Oct 30 09:30: set A (F26), B1's alpha (F27), Gate 3
interim (F28), Qwen3-8B (F29) and C13 (F30) are in; C16 running. Oct 30 04:00: C15 (F24) and B15 (F25);
Oct 29 23:15: C11 and C12 (F22, F23); added C13 (Sol), C14 (exploratory).
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
   - **Answered (F26): no, and it replicates.** On set A, 16 questions not used to find the layers: 0.90 [0.76, 1.06]
     at 15, 19 and 23 (31 cuts); evaluation set 0.90 [0.85, 0.96]. Pre-registered rule: replicates.
   - The heads too (F32): L19H31, L23H17 and L15H31, fixed in advance, separate followed from resisted runs on set A
     (+0.068 [+0.044, +0.088]).
2. **Is the readout specific to these three layers, or do all full-attention layers do it?**
   - F11 says the other five full layers read almost nothing on the evaluation set.
   - **Answered by A (F26):** on set A the 8 full layers hold 0.92 [0.83, 1.03] and 15/19/23 hold 0.90, so the
     other five hold about 0.02; the next largest drop is layer 31's 0.07 [0.04, 0.10].
   - **And where every layer is full attention (A37, F36):** in Qwen3-8B, 3 of 36 layers (21, 22, 29), chosen on
     the puzzles, hold 0.70 [0.60, 0.83] on MMLU-Pro (even share 0.083) and are its top three there; four hold 80%.
     So a few layers do it without Olmo's sliding windows, not all of them.
3. **Does a fix that downweights the tool span just make the model ignore tools?**
   - **Answered by B1:** the trade-off curve, wrong-hint following against correct-hint acceptance,
     and no-hint accuracy at the chosen alpha and at alpha = 1.
   - **Read Nov 3 (F38):** deployable span on the inserted turn: following 26 → 16 of 60 (−17 [−30, −3]); acceptance
     25 → 23 of 30 (−7 points); no-hint accuracy 16 → 19 of 30 (+10, sampling): "ignores tools" by the rule.
4. **Can a real system apply it?**
   - The deployable version acts only on tool-role spans (the inserted tool turn), which the
     framework knows. The oracle also marks a pasted block.
   - **Answered by B1** (F38), reported apart: deployable "ignores tools" (−17 [−30, −3]); oracle "no effect" (−9
     [−19, +1]).
5. **Was alpha tuned on the test set?**
   - No, by design. Alpha is chosen on set A's forced answers before any generation on the
     held-out 30.
   - **Answered (F27):** alpha* = 0.25 on the tool turn (deployable), 0.5 on every hint span (oracle), chosen on set
     A's forced answers by the rule committed before set A existed.
6. **Why should a per-head bias beat input-embedding tags?**
   - The tags did nothing measurable in loss (F20). B2 puts the provenance signal where the hint is
     read.
   - Not answered: B2 was dropped for scope (Oct 31).
7. **Does training change behavior, not just loss?**
   - **Answered in part (F28, final):** all four trained versions follow fewer wrong hints with no-hint accuracy
     within 3 points (Gate 3 met by the rule; LoRA −10 [−16, −4]). But an independent one-line instruction in the
     prompt does as well or better (each version minus prompt_only +3 to +7, not pre-registered), and the LoRA
     versions' false-disclosure candidates rise (+10 [+2, +18], +10 [+2, +19]) while the instruction's fall (−9). Read with hand labels (L4 part 1, F28): the claimed-disagreement half of the cautionary claim is not
     supported (1 to 2 of LoRA's 147 candidates).
8. **One model?**
   - **Answered in part:** the readout replicates in Qwen3-8B (A37, F36); Gate 2 holds for 5 models (F15–F17, F29,
     F37). B20 adds three new families (read Nov 17).
9. **Are the mention counts real acknowledgments?**
   - Keyword counts until the hand labels stand. L3 came back Nov 3 with kappa under 0.6, so by the plan: the
     settling call, a tightened guide and a fresh batch (by Nov 7; `docs/labeling/RATER_GUIDE.md`).
10. **Couldn't you just ask the model to say where its answer came from?** (F15: after a tool call the final answer
    is a bare letter.)
    - **Answered by B15 (F25): yes, for disclosure; no, for following.** After a call, Thinking names the tool in 33
      of 63 (before 3 of 54; +47 [+30, +64]) and is bare in 30 of 63 (before 51 of 54); Instruct names it in 149 of
      162 (before 35; +70 [+59, +81]) and is bare in 12 (before 111).
    - Following doesn't change (Thinking +6 [−2, +14], Instruct −1 [−7, +6] on the real call), and neither do
      correct-tool acceptance or no-hint accuracy. The answer says it took the tool's wrong letter, and takes it.
    - Still open: does a final answer that names the tool help a reviewer catch it, or give it more to defer to?
      **C16 (F31): it doesn't help.** Olmo 3.1 32B corrects 25 against 36 of 53 when the answer names the tool
      (−21 [−34, −8], unclear by the 20-point rule); Qwen3 30B Instruct 44 against 44.
      **C17 (F33):** a fixed sentence naming the tool doesn't cause it (+0 [−11, +11] against a sentence naming the
      solver's own working). **C18 (F34):** removing the solver's tool-citing sentences restores it (+47 [+29, +65]):
      the reviewer follows the citation of the tool's letter as authority, not the label or the argument.
    - B15's "before" is Track B's runs from one to two days earlier, not an interleaved control; C16's control runs
      the same day.

## Thread 2: automation bias in reviewers

1. **Is the deference one model's quirk?**
   - **Partly answered by C11 (F22):** Olmo 3 7B Instruct defers too (−42 [−58, −28]); Qwen3 30B Thinking doesn't
     (+1 [−6, +10]). In four reviewers it follows the family, not size or thinking (*tentative*: two per family).
   - **C13 (F30):** Granite 4.1 30B −5 [−26, +15], Mistral Small 3.2 24B +19 [+10, +30]: neither defers. Over six
     reviewers and four families, only the two Olmo models do. It is a family's trait, not a general one.
2. **What does the reviewer defer to: the visible letter or the reasoning?**
   - **Answered in part by C12 (F23):** with the tool's letter redacted, Olmo corrects 23 and 24 of 73 (C4: 6 and 3;
     answer only 59). The letter is part of the cue, not most of it.
   - By set, the gain was on the matched puzzles: **hypothesis H23** (re-solvable items), tested in **C15** on fresh
     items, split by the reviewer's own answer_only result. **C15 (F24):** restoration 0.28 where it re-solves, 0.14
     where it doesn't, +14 [−13, +37]: not supported; on fresh items redaction restores on MMLU-Pro too (+25 overall).
3. **Is the deference just reasonable trust in an answer key?**
   - Partly. On good lookups it helps (67 → 84 of 84).
   - Our point is that the independent check disappears: "as good as the tool" (F18: 92 and 89 of
     159 vs the tool's 84).
   - The paper should show both sides at other bad-lookup rates (a reweighting, no new calls).
   - **For the solver, mostly yes (B16, F35, Nov 1):** a user who claims the answer key's authority moves the answer
     about as much as the tool's pasted block (Qwen3 +6 and +12 beyond the claim; Olmo −3), and more than Olmo's
     inserted tool turn (−14). Only Qwen3 30B Instruct's own call goes far beyond it (+75). Cross-day (T11).
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
     third of the tokens, with a deferring one it added false alarms. **C15 (c), F24: no.** On fresh items it shipped
     4 and 7 wrong answers of 53 where the checker shipped none.
6. **Does any of it hold on new items?**
   - **Answered by C15 (a), F24: yes.** Olmo −55 [−70, −38] (defers), Qwen3 −6 [−15, +4] (doesn't).
7. **One solver, one tool format?**
   - Yes (Qwen3 30B Thinking; the answer key's JSON).
   - Not answered tonight. Next: Track B's other models as solvers (steered cases exist for all
     three).
