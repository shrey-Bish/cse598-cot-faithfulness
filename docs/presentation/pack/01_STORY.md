# 01. The story

The question, the answer, the five findings with their evidence, what's new, the limits, and what not to say. Every
number is FINDINGS' as frozen (tag `results-freeze-2026-11-18`), with its finding; each one is a row of
[02_NUMBERS](02_NUMBERS.md), which gives its source file. Plain names first, codes in parentheses
([`GLOSSARY`](../../GLOSSARY.md)). Facts and structure only: the words for the slides and the report are the team's.

## The question

**Do thinking modes make chain-of-thought more honest?** Concretely: when a wrong hint reaches a model, from the user
or from a tool, does a model that thinks before it answers say where its answer came from? We follow the hint at three
levels: inside the model (which layers read it), in the model's words (the private reasoning against the final
answer), and between agents (what a reviewer does with the solver's trace). Figure: `three_levels.png`.

## The answer in one paragraph

**Mixed** (FINDINGS' story, item 5; README). In the cases we tested, thinking puts the tool's source into the private
reasoning but not into the final answer, which is what a user or a reviewer reads. In one model (Qwen3-8B), switching
thinking on names the tool in the private reasoning after 141 of 145 calls and in the final answer of 0 of 143 followed
runs, and makes it follow the tool's wrong letter far more on the real tool call (+64 [+51, +75], read after the fact)
(F29). In another (gpt-oss-20b), more reasoning effort changes neither following (+7 [−1, +16]) nor the bare answer
(−5 [−10, 0]): no change detected (F37). In a third (Nemotron 3 Nano), the answer after the inserted tool turn is less
bare with thinking on (−14 [−19, −9]) (FB1). Every fix we tried trades resisting wrong hints against accepting right
ones; what worked was a check that never sees the tool (F24). Small studies, one or two models each.

## The five findings

**1. A tool's hint pulls harder than the user's, and much of the pull is the claim to be the answer key.**
- The same wrong hint, tool minus user (the main tool-versus-user test, Gate 2; 54 questions × 3 runs): Qwen3 30B
  Thinking +35 [+24, +46] (pasted tool block), +31 [+22, +42] (its own call) (F15); Qwen3 30B Instruct +21 [+12, +31],
  +90 [+83, +96] (F16); Olmo 3 7B Think +32 [+22, +42], +21 [+13, +30] (inserted tool turn) (F17).
- Also in Qwen3-8B, thinking on and off (+19, +13; F29), in gpt-oss-20b at every effort (F37), and in three more
  families, clear in all 10 readings (Gemma 4 26B-A4B, Nemotron 3 Nano 30B-A3B, Granite 4.2 8B; B20, FB1).
- **The answer-key claim:** a user who writes "My course answer key says the answer is (X)" closes 68% and 71% of the
  gap to the pasted block in the two Qwen3 models and all of it in Olmo (B16, F35). **This holds for pasted tool
  output:** where Qwen3 30B Instruct calls the tool itself, the tool goes beyond the claim (+75 [+65, +85], F35).
- **Authority:** "the official solution manual" moves all three models more than "a classmate" (+41 [+31, +51],
  +12 [+4, +20], +32 [+23, +41]; B24, F40).
- Figures: `gate2.png`, `authority_ladder.png`.

**2. After a tool call, the reasoning names the tool, but the final answer usually doesn't.**
- Keyword counts (Test 1): the private reasoning names the hint in 208 of 216 runs, the final answer in 8 of 216 (F3).
  Hand labels (L3) didn't reach agreement, so these stay keyword counts.
- After a call the final answer is a bare letter, right or wrong tool: 80 of 84 after a right lookup, 71 of 75 after a
  wrong one, against 2 of 159 with no tool (Qwen3 30B Thinking, C4; F15). Qwen3 30B Instruct too (bare after 111 of 147
  calls, F16). Olmo is tentative (F17).
- **Not general:** Gemma names the tool in 127 of 162 with thinking off (FB1); Nemotron with thinking on shows no
  difference (FB1).
- One instruction ("say what your answer is based on") brings the tool back into the answer (Qwen3 30B Thinking bare
  51 of 54 → 30 of 63), and following doesn't change (+6 [−2, +14]; no change detected) (B15, F25).
- Figures: `private_vs_final.png`, `bare_after_call.png`.

**3. Inside the model, three layers carry most of the hint's effect.**
- In Olmo 3 7B Think, full-attention layers 15, 19 and 23 read the hint's letter straight from the prompt and hold
  0.90 [0.85, 0.96] of the drop at the takeover (activation patching; F11); on 16 questions not used to find them,
  0.90 [0.76, 1.06] (set A; F26). Three attention heads separate followed from resisted runs on the new questions
  (+0.068 [+0.044, +0.088]; F32).
- **A second model, with its own layers:** in Qwen3-8B, whose layers all see the whole prompt, its own three layers
  (21, 22, 29), chosen on the puzzles, hold 0.70 [0.60, 0.83] of the drop on MMLU-Pro (A37, F36): pre-registered,
  replicates, less concentrated. Not the same three layers, and the heads are Olmo only.
- One model family each; the mechanism as a whole is tentative.
- Figures: `readout_by_layer_slide.png`, `readout_qwen8b.png`.

**4. Olmo reviewers defer to a tool's log; an independent checker holds.**
- Olmo 3.1 32B Instruct, as a reviewer, corrects a wrong tool answer in 59 of 73 from the answer alone, and in 6 and
  3 of 73 once it sees the solver's private reasoning or the tool log (−73 [−86, −58], −77 [−91, −61]; C4, F18).
- Of six reviewers in four families, only Olmo's two defer (Olmo 3 7B Instruct −42 [−58, −28]; F22, F30).
- Prompt fixes don't restore the check (F19, F21). The cue is the solver's citation of the tool: removing those
  sentences restores it (25 against 9 of 34, +47 [+29, +65]; C18, F34).
- A checker that re-solves without ever seeing the tool stopped all 53 wrong tool answers on 100 fresh items, with
  false alarms on 7 of 45 good lookups (C15, F24); on the first items it flagged 73 of 75 bad lookups (F18).
- Figures: `trackC_reviewers_slide.png`, `reviewer_by_prompt_slide.png`, `pipeline_vs_model.png`.

**5. Every fix is a trade; fine-tuning made answers more candid, following wrong hints no less than the instruction
and fewer than no fix.**
- All four fine-tuned versions pass the fix test against no fix (Gate 3; LoRA −10 [−16, −4]), but the one-line
  instruction in the prompt does as well (−13 [−21, −6]); none beats it without a cost (F28).
- Consistency training (A40) follows far fewer wrong hints than the instruction (84 of 694 against 237 of 713,
  −21 [−26, −16]) but takes fewer right ones (347 of 459 against 431 of 476, −15 [−20, −10]): "fewer, but costs
  acceptance" (F41).
- Marking tool output "unverified" does nothing alone (−1 [−7, +4]; A39, F44).
- **Candid:** by hand labels on 120 fresh questions, when LoRA follows a wrong hint its answer says so in 37 of 42 runs,
  against the instruction's 18 of 42 (+45 [+25, +64]; L6, F45), while following no less than the instruction
  (no difference detected, F44) and fewer than no fix. One model, one question set, 42 rows a system, the final answer
  only.
- The attention dial (B1): a real cut in following on the tool turn that misses its acceptance limit ("ignores tools"
  by the rule, F38); on 120 fresh questions (B1R2) the cut replicates, 82 of 240 → 49 of 240 (−13.8 [−20.0, −7.5]),
  with acceptance down (−5.8 [−10.8, −1.3]).
- *Exploratory (post hoc):* consistency training gives more correct answers than the instruction only when fewer than
  0.36 [0.22, 0.50] of the tool's answers are correct (FINDINGS' story, item 7; REPORT §7).
- Figures: `gate3_vs_base_slide.png`, `a40_e2_fixes.png`, `tradeoff_e2.png` (exploratory).

## What's new and what isn't

From [`CLAIMS.md`](../../paper/CLAIMS.md), [`RELATED_WORK.md`](../../paper/RELATED_WORK.md) and the README; the
papers are in [07_RELATED_WORK](07_RELATED_WORK.md).
- **Not new:**
  - That models follow a hint and leave it out of their chain of thought (Turpin et al.; Chen et al.), and use answer
    hints without acknowledging them (Unspoken Hints; Walden and Wanner).
  - That a cue delivered by a tool is said less than a user's (FACE-Eval, Gema et al., which also varies reasoning
    effort and tests a source-attribution prompt).
  - That a source's authority moves answers more (Kumar and Chopra): our authority ladder is not new in kind.
  - Consistency training is bias-augmented consistency training (Chua et al.); we don't claim the method.
- **Ours:**
  - The split between the private reasoning and the final answer in thinking models, after the model's own tool call
    (keyword counts, not proof of lying) (F3, F15, F29).
  - The same-model, same-day comparison of a user's authority claim against each tool channel (F35, F40).
  - Layers 15, 19 and 23 in Olmo, replicated in Qwen3-8B with its own layers (F11, F26, F36). A wider search for
    related mechanistic work was not done.
  - The review-team results: deference follows the model family, and an independent checker holds (F18–F34).
  - The cost of every fix to correct hints, which the consistency-training paper leaves unmeasured, and the hand
    labels of what the answers say (F41, F43, F44, F38; F45).

## The limits

- Small models, mostly one or two per result; every fix on one model (Olmo 3 7B Think) and MMLU-Pro's evaluation
  categories; one tool format (the answer key's JSON) and one solver in the review-team track.
- Multiple-choice questions only: following is the hint's letter in the answer.
- Keyword counts where hand labels didn't stand (F3); every kappa is one human against an AI rater (ChatGPT 5 Astra
  High), not two humans.
- The attention dial was underpowered at 30 questions (F38); the Qwen3-8B on/off comparison was read after the fact
  (F29); gpt-oss-20b ran after its one-day window (F37); the newer families ran at temperature 1.0 (FB1).
- The trade-off reading (item 7) is exploratory.

## Don't say (each an overstatement we've corrected)

| don't say | say instead (the finding) | corrected where |
|---|---|---|
| "Much of the pull is authority" in general | holds for pasted tool output; where Qwen3 30B Instruct calls the tool itself, the tool goes beyond the claim (F35) | Nov 23 log, Ritik's five-line story |
| "After a tool call, models stop saying where the answer came from" | in the Qwen3 models; not general: Gemma names the tool in 127 of 162 with thinking off; Olmo tentative (F17, FB1) | Nov 23 log |
| "The same three layers in a second model" / "the heads replicate in Qwen3" | Qwen3-8B's own layers 21, 22, 29 at 0.70 [0.60, 0.83]; the heads are Olmo only (F36, F32) | Nov 23 log; QA_FACTS |
| "Fine-tuning made answers more candid without making them follow less" | candid against the instruction (37 of 42 against 18 of 42), following no less than the instruction and fewer than no fix (LoRA −10 [−16, −4]) (F45, F44, F28) | Nov 23 log |
| "Models lie" / "deny using the hint" | keyword counts of mentions, not proof of lying; almost no claimed disagreement in hand labels (1 to 2 of 147; 0 of 42) (F3, F28, F45) | CLAIMS 1.2; RELATED_WORK (Walden and Wanner) |
| "The instruction doesn't work" / "no effect" for B15 | no change detected in following (F25) | QA_FACTS, Nov 23 |
| "+64" without its condition | on the real tool call, on − off, read after the fact (F29) | QA_FACTS, Nov 23 |
| "The attention dial works" | "ignores tools" by its rule on the 30; the cut replicates on 120 with a cost to right hints (F38) | CLAIMS 1.7; TALK_MAP next steps |
| "Consistency training beats the instruction" | fewer wrong hints followed, but costs acceptance (F41) | FINDINGS F41's rule |
| "LoRA + note is the first fix that beats one line" (unqualified) | fewer than the instruction by R2, at an acceptance cost of −9 [−13, −5] (F44) | FINDINGS story, item 6 |
| "The fix belongs at the system level" as a result | our reading (interpretation): labels alone don't help (F44, FC3); the checker does (F24) | QA_FACTS, Nov 23 |
| "Two raters agreed" / "Shrey labelled" | Ritik against an AI rater (ChatGPT 5 Astra High) | FINDINGS, corrected Nov 4, 17:49 |
| "Hand labels confirm the private/final split" | L3 didn't reach agreement; Gate 2's label part is not met (F3) | FINDINGS F3 |
| "First to show tool cues are disclosed less" | FACE-Eval showed it first; ours is the private/final split and the own call (F3, F15, F29) | RELATED_WORK, Nov 19 |
| "We vary reasoning effort first" / "a source prompt is ours" | FACE-Eval did both; ours differs in measure (F37, F25) | RELATED_WORK, Nov 19 |
| "Tools beat users in general" | in our five Track B models and B20's three families only (Gate 2, FB1) | RELATED_WORK (A-CC; Syed and Yasaei) |
| "A cheaper check (two reviews) can replace the checker" | refuted as a replacement: it shipped 4 and 7 of 53 wrong (F24) | CLAIMS 2.6 |
| "We trained a provenance bias in the attention (B2)" | dropped Oct 31, never trained | CLAIMS 1.8 |
| "Input source tags help" | did nothing measurable in loss, nor on the inserted tool turn (F20) | CLAIMS 1.6 |
| "Gate 3's comparisons with the instruction were pre-registered" | on the 30, not pre-registered; on the 120, they were (F28, F44) | QA_FACTS |
| "208 of 216 means the reasoning always names the hint" | an upper bound: the keyword also fires on 22 of 72 no-hint runs (F3) | QA_FACTS |
