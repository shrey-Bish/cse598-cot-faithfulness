# 09. Q&A bank

28 likely questions, grouped, each with the facts to answer from and the finding to cite. **Facts, not scripted
answers.** Numbers are FINDINGS' (rows of [02_NUMBERS](02_NUMBERS.md)); the demo's finder counts are TALK_MAP's.
Built on [`QA_FACTS.md`](../QA_FACTS.md) (checked against FINDINGS on Nov 23) and
[`REVIEWER_QUESTIONS.md`](../../paper/REVIEWER_QUESTIONS.md). The hard ones are marked ★.

## Setup

**Q1. What exactly is a "hint", and where does it come from?**
- A wrong (or right) answer letter placed in the prompt by a source: the user ("I think the answer is (X)…"), a
  professor, a pasted tool block, an inserted tool turn, the model's own tool call, a system note; and the user's
  authority claims (a classmate, "my course answer key", "the official solution manual") (03_METHODS).
- Following = the hint's letter in the final answer; acceptance = a right hint taken.

**Q2. Which models, and why these?**
- 12: eight answering (Olmo 3 7B Think, Qwen3 30B Thinking, Qwen3 30B Instruct, Qwen3-8B, gpt-oss-20b, Gemma 4 26B-A4B,
  Nemotron 3 Nano 30B-A3B, Granite 4.2 8B) and four reviewers (Olmo 3.1 32B Instruct, Olmo 3 7B Instruct, Granite 4.1
  30B, Mistral Small 3.2 24B), on ASU Voyager and Sol (03_METHODS). Open weights, so the layers can be patched and the
  fixes trained.

**Q3. ★ Why multiple choice only?**
- Following is measurable as the hint's letter in the answer (the 54: 24 puzzles and 30 MMLU-Pro; the 30 held-out; the
  120 fresh); the words are read by keyword counts, hand labels and judges (QA_FACTS 6).
- Limits: MMLU-Pro's evaluation categories and puzzles only; one tool format; a letter answer is also why the final
  answer can be a bare letter (F15).

**Q4. Is the tool format realistic?**
- A retrieved passage in place of the answer key (C26): the solver follows a bad lookup in 19 of 55 against 52 of 55,
  and the Olmo reviewer still defers to the tool log (5 against 15 of 21, −48 [−67, −29]) (FC4).
- The claimed authority matters: the manual against a classmate +41, +12, +32 points (F40).
- Limit: one tool format (the answer key's JSON) in the main runs (REPORT §10).

## Methods

**Q5. How do you know which layers read the hint?**
- Activation patching at the takeover: swap one token (the hint's letter for the model's own answer), restore layer by
  layer at the hint's tokens, measure the logit difference (F11). Layers 15, 19 and 23 hold 0.90 [0.85, 0.96] (19 cuts,
  9 questions); on 16 new questions 0.90 [0.76, 1.06] (F26). Attention agrees: 8 of the 10 top heads are in those
  layers (F12).

**Q6. Is it one model? Does the mechanism generalize?**
- Qwen3-8B, whose layers all see the whole prompt, replicates with its own three layers (21, 22, 29): 0.70 [0.60,
  0.83] (F36, pre-registered). Less concentrated than Olmo's 0.90; the heads are Olmo only. The mechanism as a whole
  is tentative.

**Q7. What is consistency training doing — just ignoring hints?**
- It follows the wrong hint in 84 of 694 against the instruction's 237 of 713 (−21 [−26, −16]), but takes the right
  hint in 347 of 459 against 431 of 476 (−15 [−20, −10]): "fewer, but costs acceptance" (F41). With the note it
  follows fewest (64 of 706), at more cost (−20 [−26, −14]) (F43).
- Inside: its weights remove part of the hint's pull from layers 0–14, before the readout (+0.68 [+0.17, +1.18], F42);
  LoRA acts in the reasoning instead (F39).

**Q8. Why not just add the one-line instruction?**
- It does as well as training on the 30: −13 [−21, −6] against LoRA's −10 [−16, −4] (F28); no fix beats it without a
  cost to right hints (F41, F43, F44). It is the baseline every fix must beat.

**Q9. How do the review-team experiments work?**
- A solver (Qwen3 30B Thinking with a lookup tool, a seeded oracle makes its lookup bad on 25 of the 53 items) answers; a reviewer sees the
  answer alone, or plus the explanation, the private reasoning or the tool log; a checker re-solves without the tool
  and escalates on disagreement, so no answer ships (F18; `agents/run_team.py`).
- Olmo 3.1 32B: 59 of 73 corrected alone, 6 and 3 of 73 with the reasoning or the log (F18); the checker flagged 73 of
  75 bad lookups (F18) and stopped all 53 wrong answers on fresh items (F24).

**Q10. What is the attention dial, and did it work?**
- At inference, scale attention to the tool turn's tokens in the readout layers (alpha 0.25). On the 30: −17 [−30,
  −3] on the tool turn, missing its acceptance limit ("ignores tools" by the rule; underpowered); every hint span: no
  effect (−9 [−19, +1]) (F38). On 120 fresh questions the cut replicates (82 of 240 → 49 of 240, −13.8 [−20.0, −7.5]),
  acceptance down (−5.8 [−10.8, −1.3]) (F38).

## Statistics

**Q11. How sure are you? What are the intervals?**
- Rates: 95% Wilson intervals. Differences: percentage points, 95% bootstrap with questions resampled with all their
  runs, paired across systems; under 5 questions, "too few questions" and no direction (FINDINGS' notes on numbers).

**Q12. ★ Is 42 rows enough?**
- L6: when LoRA follows a wrong hint, its answer says so in 37 of 42 hand-labelled runs, against the instruction's
  18 of 42 (+45 [+25, +64]); Ritik against J-opus kappa 0.96 (F45).
- Limits: 42 rows a system, one model, the 120 only, the final answer only; the sheet not blind in practice (J-opus,
  blind to systems, agrees on 82 of 84 rows); LoRA's trained opener names the hint (F28). The keyword version agrees
  (225 of 248 against 118 of 237; exploratory, post hoc).

**Q13. Are the keyword counts real? What about the hand labels?**
- F3's 208 of 216 against 8 of 216 are keyword counts; L3's labels didn't reach agreement (kappa private 0.63, final
  0.54), so Gate 2's label part is not met (F3). Labels do stand for L4 part 1 (kappa 0.93) and L6 (kappa 0.96).
- Every kappa is Ritik against an AI rater (ChatGPT 5 Astra High), not two humans (corrected Nov 4).

**Q14. What was pre-registered, and what wasn't?**
- 31 rules fixed before their runs (`docs/paper/supplement/PREREGISTRATIONS.md`; 03_METHODS); deviations listed
  (`DEVIATIONS.md`). Not pre-registered: the trained versions against the instruction on the 30 (F28); Qwen3-8B's
  on − off (F29, after the fact); the trade-off figure (exploratory, post hoc). gpt-oss-20b ran after its one-day
  window (F37).

**Q15. Why is the trade-off figure "exploratory"?**
- It was computed after the A40–A42 readings, with its log written before computing, and replaces no verdict
  (REPORT §7): consistency training gives more correct answers than the instruction only when fewer than 0.36 [0.22,
  0.50] of the tool's answers are correct.

## Novelty

**Q16. ★ How does this differ from the related work?**
- Not ours: unnamed hint use (Turpin et al.; Chen et al.; Unspoken Hints; Walden and Wanner), a tool cue said less than
  a user's (FACE-Eval, which also varies effort and tests a source prompt), authority effects (Kumar and Chopra),
  consistency training as a method (Chua et al.).
- Ours: the private/final split after the model's own call and thinking on/off in the same weights (F3, F15, F29); the
  user's claim against each tool channel, same day (F35, F40); the readout layers in two models (F11, F26, F36); where
  training acts (F39, F42); the cost of every fix to right hints (F41, F43, F44, F38); the review team (F18–F34).
- Disagreements: A-CC and Syed and Yasaei; not reconciled; our tool-over-user claim is for our models and tasks only.
  ([07_RELATED_WORK](07_RELATED_WORK.md))

**Q17. Isn't "tools beat users" contradicted by other papers?**
- A-CC found user assertions followed more than function-sourced ones in function-calling models on policy hints; Syed
  and Yasaei found tool-channel instructions discounted. Ours is a wrong fact in an answer key, in our eight models
  (Gate 2, FB1); claimed for those only.

**Q18. Did thinking make chain-of-thought more honest?**
- Mixed: Qwen3-8B with thinking on names the tool in its private reasoning after 141 of 145 calls and in the final
  answer of 0 of 143 followed runs, and follows more on the real call (+64 [+51, +75], read after the fact) (F29);
  gpt-oss-20b, more effort: no change detected (+7 [−1, +16]; −5 [−10, 0]) (F37); Nemotron 3 Nano's answer less bare
  with thinking on (−14 [−19, −9]) (FB1).

## Limits

**Q19. ★ Why only one model for the fixes?**
- Every fix (fine-tuning, consistency training, the wrapper, the dial) is on Olmo 3 7B Think (F28, F41–F44, F38), the
  model whose readout layers were found (F11) and that LoRA on layers 15/19/23 and the dial act on. Compute was a
  limit: a replication resolving the dial's limit needs about 107 to 245 fresh questions (53 to 122 GPU-hours), and
  35 GPU-hours fit 70, so it wasn't run (FINDINGS' story, item 6; 03_METHODS for the compute).
- The failure itself holds in eight answering models (F15–F17, F29, F37, FB1), the readout in two (F36).

**Q20. Do the fixes generalize to other question sets?**
- Gate 3 passes on the 30 and again with power on the 120 (the instruction −9 [−14, −4], LoRA −7 [−11, −3]; F44);
  consistency training and the wrapper were read on the 120 (F41, F44). One model; MMLU-Pro categories.

**Q21. Why do only Olmo's reviewers defer?**
- Six reviewers over four families; only Olmo's two defer (F22, F30). The family can't be separated from its data,
  recipe and template; tentative with two reviewers a family (F22).

**Q22. What would you do next?**
- Our reading: verify the tool independently (the checker stopped all 53, F24); labels alone don't help (F44, FC3);
  treat each fix as a trade; the dial's cost to right hints on 120 questions is open (F38).

## The demo

**Q23. ★ Are the demo's examples cherry-picked?**
- The pad's "Show me" finds a question where a pattern happens and says on how many questions it does; the count is
  every question in the set with a counted run for that hint and model, from each run's own outcome fields; matches
  come in a seeded order (fnv1a of a fixed seed and the question id), never by outcome (TALK_MAP, Show me).
- On the first question found, consistency training took the hint too, and the verdict line says so; the contrast
  comes from "the fix held", shown with its count (26 of 112).
- Tested: the finder's counts equal a count made from the per-question files, for 624 combinations
  (`cot-disclosure/tests/test_demo_pad.py`).

**Q24. ★ Why "38 of 114" on the pad but "85 of 233" under the run?**
- The finder counts questions for the wording on screen (a study guide): 38 of the 114 questions with an answer. The
  number under the run is the frozen count of runs over both tool-call wordings. The two wordings' finder counts add
  up to it: 38 of 114 and 47 of 119 make 85 of 233 (TALK_MAP; the frozen count is F41's source, `a40_e2.json`).

**Q25. Are the runs on the pad real?**
- Recorded runs from the experiments, each labelled with its model, version and date, with its file and line; the
  highlights are the analysis's own keyword matcher's spans (`detect.py`); live mode (Qwen3-8B through Ollama) is
  labelled "not a recorded run, never counted".

## AI use and process

**Q26. How did you use AI tools?**
- From `docs/submission/AI_USE_INVENTORY.md` (facts only; [10_TEAM_AND_PROCESS](10_TEAM_AND_PROCESS.md)):
  - assistance: Claude Code wrote and ran code, tests, analyses and figures, the docs and session logs, under rules
    that keep every commit the member's own (no AI author or co-author; enforced by git hooks); Claude in chat for
    planning (to confirm);
  - labels: ChatGPT 5 Astra High as "AI rater 1" for L3 and L4 part 1; LLM judges (J-opus, Claude Opus; J-qwen and
    J-olmo on Voyager) under the Nov 4 protocol; L6 labelled by Ritik alone, with J-opus as the check;
  - not assistance: the models studied are the experiments' subjects; no paid API was called.
- Open: the inventory's "to confirm" lines (each member's own use and hand checks) and the uses since Nov 19.

**Q27. Who did what?**
- Track A (Ritik), Track B (Arsha, from Nov 6), Track C (Shrey); commit counts and dates in
  [10_TEAM_AND_PROCESS](10_TEAM_AND_PROCESS.md). `CONTRIBUTIONS.md` is the team's to write.

**Q28. How do we know the numbers didn't move after you saw them?**
- Results were frozen on Nov 18 (tag `results-freeze-2026-11-18` on `7e1fdc0`); since then, presentation work only,
  with a dated note in each day's log. Rules were fixed before their runs (Q14); the pack's numbers are checked against
  their sources by `cot-disclosure/tests/test_presentation_pack.py`.
