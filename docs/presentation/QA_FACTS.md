# Likely questions: the facts to point to

**What it is.** For Q&A after the Nov 24 talk: each likely question with the facts and findings to point to (numbers
with their codes), the limits that apply, and where to look. **No scripted answers**: the team decides what to say.
Results are frozen (tag `results-freeze-2026-11-18`); every number is as [`FINDINGS.md`](../FINDINGS.md) (F),
[`FINDINGS_B.md`](../trackB/FINDINGS_B.md) (FB1) and [`FINDINGS_C.md`](../trackC/FINDINGS_C.md) (FC1–FC4) read it, or
as the Gate 3 draft in [`PLAN.md`](../PLAN.md). Figures are in [`docs/paper/figures/`](../paper/figures/); "scene" is a
tour scene of the [Hint Explainer](../demo/explainer.html) (`docs/demo/explainer.html`). Slide numbers are
[`TALK_MAP.md`](TALK_MAP.md)'s. Related questions come from [`REVIEWER_QUESTIONS.md`](../paper/REVIEWER_QUESTIONS.md).

## 1. Why not just add the one-line instruction?

- **Facts**
  - On the held-out 30, the one-line instruction cuts following by −13 [−21, −6] (`prompt_only`); LoRA −10 [−16, −4];
    each trained version minus the instruction: LoRA +3 [−1, +8], tags +7 [+1, +14], LoRA + tags +6 [+1, +11], LoRA on
    layers 15/19/23 +6 [+0.4, +12] (F28).
  - On E2's 120 fresh questions the instruction −9 [−14, −4]; LoRA against it: no difference detected, +2 [−2, +6] (F44).
  - The instruction is the baseline the training fixes must beat: no fix beats it without a cost to correct hints
    (F41, F43, F44). Consistency training: 84 of 694 wrong hints followed against 237 of 713, but 347 of 459 correct
    hints taken against 431 of 476 (F41).
  - A different instruction (say what your answer is based on) brings the tool into the answer (Thinking bare 51 of 54 to
    30 of 63) and the model still takes the wrong letter as often (+6 [−2, +14]) (F25).
- **Limits.** The comparisons with the instruction on the 30 were not pre-registered (on E2 they were, F44); one model.
- **Where.** Slide 9; `gate3_vs_base_slide.png`, `a40_e2_fixes.png`; scene 7 (Fixes).

## 2. Is 42 rows enough?

- **Facts.** L6 (F45): when LoRA follows a wrong hint on E2, its final answer says so in 37 of 42 hand-labelled runs
  against the instruction's 18 of 42, +45 [+25, +64]; none claims to reject the hint it ends on. Ritik against J-opus
  kappa 0.96; the keyword agreed with the labels on 83 of 84 rows. By keyword on all followed runs: 225 of 248 against
  118 of 237 (exploratory, post hoc).
- **Limits.** 42 rows a system, one model, E2 only, the final answer only; the sheet was not blind in practice (J-opus,
  blind to systems, agrees on 82 of 84 rows); LoRA's trained opener names the hint (F28); it did not make LoRA follow
  less (F44). The interval is the one stated; nothing more is claimed from it.
- **Where.** FINDINGS F45; the story's item 6 and its scorecard (item 7).

## 3. Why only Olmo's reviewers?

- **Facts**
  - Not only Olmo's: six reviewers over four families were run; only Olmo's two defer (F22: Olmo 3 7B Instruct −42
    [−58, −28], Qwen3 30B Thinking +1 [−6, +10]; F30: Granite 4.1 30B −5 [−26, +15], Mistral Small 3.2 24B +19 [+10,
    +30]). Olmo 3.1 32B: corrects 59 of 73 from the answer alone, 6 and 3 of 73 with the reasoning or the tool log (F18).
  - Run on Olmo's reviewer: C19 (FC1, −13 points, unclear), the writer-to-decider handoff C25 (FC2: 9 of 53 against 16
    of 53, −13 [−23, −6], unclear), C20's blind reviewer (FC3: +8 [−2, +19]), C26 (FC4: 5 against 15 of 21, −48
    [−67, −29]).
  - On 100 fresh items it replicates (Olmo −55 [−70, −38]; Qwen3 −6 [−15, +4]) (F24).
- **Limits.** The deference follows the family, which can't be separated from its data, recipe and template (F22);
  tentative with two reviewers a family; Track C used one solver and one reviewer prompt (REPORT §10).
- **Where.** Slides 11 and 12; `trackC_reviewers_slide.png`, `reviewer_by_prompt_slide.png`, `c19_authority.png`,
  `c25_hops.png`, `pipeline_vs_model.png`; scene 6 (Review team).

## 4. Is consistency training just ignoring hints?

- **Facts**
  - A40 follows the wrong hint in 84 of 694 runs against the instruction's 237 of 713 (−21 [−26, −16]), but takes the
    correct hint in 347 of 459 against 431 of 476 (−15 [−20, −10]): "fewer, but costs acceptance" by the rule fixed Nov 5
    (F41). Where it follows fewer wrong hints it also takes fewer right ones: a trade, not a fix beating the instruction.
  - It passes Gate 3's rule against base (−30 [−35, −26]) (Gate 3 draft, F41); with the note added it follows fewest (64
    of 706) and costs more acceptance (−20 [−26, −14]) (F43).
  - Where it acts (F42): on base's own reasoning A40's weights remove part of the hint's pull (+0.68 logits [+0.17,
    +1.18]), from layers 0–14, before the readout layers (F42); LoRA's acts in the reasoning instead (F39).
  - Exploratory, post hoc: A40 gives more correct answers than the instruction only when fewer than 0.36 [0.22, 0.50] of
    the tool's answers are correct (the story's item 7; `tradeoff_e2.png`).
- **Limits.** One model; E2; A40's disclosure line is keyword-only (60 of 84, exploratory).
- **Where.** Slides 9 and 10; `a40_e2_fixes.png`, `readout_lora_vs_base.png`; scene 7 (Fixes).

## 5. How does this differ from the related work?

- **Facts** (each paper checked on arXiv Nov 19; the entries, with what each found, in
  [`RELATED_WORK.md`](../paper/RELATED_WORK.md); REPORT §11 has one line each):
  - **Already shown by others, so not claimed as ours:** hint use that goes unnamed in the reasoning (Chen et al. 2025;
    Unspoken Hints, Marioriyad et al. 2025; Walden and Wanner 2026, where models also deny using hints); a cue from a
    tool said less than the same cue from the user, across 15 open models including Olmo 3 Think and gpt-oss, with
    reasoning effort and a source-attribution prompt tested (FACE-Eval, Gema et al. 2026); a verified-source note moving
    answers more than a user's opinion, more so the more authoritative it sounds, separable inside the model (Authority
    Bias, Kumar and Chopra 2026); consistency training as a method (BCT, Chua et al. 2024); tool evidence overturning
    right answers (When Tools Hurt, Zhao et al. 2025).
  - **Where ours differs or adds:** the private reasoning against the final answer (F3, F15: FACE-Eval judges the
    reasoning, and the final answer only for the side it takes); thinking on and off in the same weights (F29); the
    model's own tool call (F15, F16); the readout layers and heads, replicated in a second family (F11, F26, F32, F36);
    where training acts, fine-tuning in the reasoning (F39) and consistency training before the readout (F42); the cost
    to correct hints for every fix (F41, F43, F44, F38), which BCT's evaluation and Authority Bias's direction removal
    don't test; the review team (F18–F34, FC1–FC4).
  - **Disagreements to know:** Assertion-Conditioned Compliance (Waqas et al. 2025) found user assertions followed more
    than function-sourced ones (36.3% against 27.8%) in function-calling models on policy hints; Syed and Yasaei (2026)
    found instructions in tool metadata discounted against the user's. Neither is reconciled with our tool-over-user
    result (Gate 2), which is claimed for our models and tasks only.
- **Limits.** Nine papers checked, not a search of the literature; four of them (Walden and Wanner, Unspoken Hints,
  Zhao et al., Syed and Yasaei) on their abstracts only.
- **Where.** `docs/paper/RELATED_WORK.md`; REPORT §1 (each contribution's prior work) and §11.

## 6. Why multiple choice?

- **Facts.** Following a hint is measurable as the hint's letter picked in the answer (puzzles: 24; MMLU-Pro: 30 held-out
  questions, E2's 120 fresh ones for the later experiments); the keyword, hand-label and judge checks read the words.
- **Limits.** MMLU-Pro's evaluation categories and puzzles only; one tool format (the answer key's JSON, REPORT §10); a
  letter answer is also why the final answer can be a bare letter (F15).
- **Where.** REPORT §2 and §10; `channels.png` (the five channels); scene 1–2.

## 7. What next?

- **Facts (the conclusion's bullets, REPORT §12; FINDINGS' scorecard).** The fix belongs at the system level: provenance
  labels alone don't help (A39 −1 [−7, +4], F44; FC3); independent verification does (the checker stopped all 53 wrong
  tool answers on fresh items, false alarms on 7 of 45 good lookups, F24). A powered replication of B1 needs about 107 to
  245 fresh questions (53 to 122 GPU-hours) (F38). Open: items the solver gets wrong without the tool (the checker's
  hard case).
- **Limits.** The checker was tested on fresh items of one tool format; Track C's solver is one model.
- **Where.** Slide 13; REPORT §10 and §12; PLAN's Gate 3 draft.

## 8. Did thinking make chain-of-thought more honest?

- **Facts.** Answered mixed (the story's item 5). Qwen3-8B with thinking on names the tool in its private reasoning after
  141 of 145 calls and in the final answer in 0 of 143 followed runs, and follows the wrong letter far more (+64 [+51,
  +75]) (F29). gpt-oss-20b, effort low to high: following +7 [−1, +16], bare answer −5 [−10, 0], no change detected (F37).
  Nemotron 3 Nano's answer after the inserted turn is less bare with thinking on (−14 [−19, −9]) (FB1). Private reasoning
  names the hint in 208 of 216 runs, the final answer 8 of 216 (F3).
- **Limits.** One model per comparison; Qwen3-8B's on-minus-off was read after the fact (no rule fixed for it); F37 ran
  past its one-day window; the keyword also fires with no hint (22 of 72 no-hint runs, so 208 is an upper bound, F3).
- **Where.** Slides 5, 6, 8; `private_vs_final.png`, `b17_effort.png`; scene 5 (The quiet answer).

## 9. Are the keyword counts real? What about the hand labels?

- **Facts.** F3's mentions are keyword counts. Hand labels (L3, 101 rows, Ritik and an AI rater): kappa private 0.63 (58
  rows), final 0.54 (101 rows). Read by the Nov 4 judge protocol, Ritik against the judges' majority is under 0.6 in all six
  cells (private 0.472, final 0.234): **Gate 2's label part is not met**. Hand labels do stand for L4 part 1 (kappa 0.93;
  1 to 2 of LoRA's 147 candidates claim to reject the hint, 97 of 147 say it shaped the answer, F28) and L6 (F45).
- **Limits.** One human and one AI rater (ChatGPT 5 Astra High), so every kappa is human-vs-AI agreement; L4's sheets were
  not blind to LoRA's style.
- **Where.** FINDINGS F3, F28, F45; REPORT §10; slide 5's figure note.

## 10. Is it one model? Do the fixes generalize?

- **Facts.** Gate 2 holds in five Track B models (F15–F17, F29, F37) and three more families, clear in all 10 readings
  (FB1). The readout replicates in Qwen3-8B (layers 21, 22, 29: 0.70 [0.60, 0.83], F36). Reviewer deference is Olmo's
  family only (F22, F30). The fixes (Gate 3, A39, A40, A42, B1) are Olmo 3 7B Think only.
- **Limits.** One model for every fix (Gate 3 draft's limits); the readout is *tentative* as a whole (the story's item 3).
- **Where.** Slides 2, 4, 9; `gate2.png`, `readout_qwen8b.png`.

## 11. Is the tool format realistic?

- **Facts.** C26 (FC4), a retrieved passage in place of the answer key: the solver follows a bad lookup in 19 of 55
  (against 52 of 55), still 35 points above the no-tool floor; the Olmo reviewer still defers to the tool log (5 against 15
  of 21, −48 [−67, −29]): deference survives without the authority label. B24 (F40): the claimed source's authority
  moves the answer (manual against classmate +41, +12, +32 points).
- **Limits.** One tool format (the answer key's JSON) in the main runs; B20's tool channel is the inserted turn for
  Gemma and Nemotron, Granite's own call (FB1).
- **Where.** Slide 7 and 12; `authority_ladder.png`, `pipeline_vs_model.png`; scene 3 (Authority).

## 12. Does the model just trust a tool, or an authority claim?

- **Facts.** "My course answer key says (X)" from a user closes 68% and 71% of the gap to the pasted block in Qwen3 and
  all of it in Olmo (F35); the tool goes beyond the claim where Qwen3 30B Instruct calls it itself (+75 [+65, +85]) (F35);
  "the official solution manual" pulls as hard as or harder than every tool channel except Instruct's own call (F40);
  in B20, the tool's form adds to the claim in 5 of 10 readings, the claim moves it more in 1, no difference detected in 4
  (FB1).
- **Limits.** B16's tool arms are cross-day (B19's same-day rerun held, F35); B24's fifteen readings are not corrected
  for multiplicity; "no difference detected" is not no difference.
- **Where.** Slide 7; `authority_ladder.png`; scene 3 (Authority).
