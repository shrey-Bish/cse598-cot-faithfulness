## In plain words: Track A's fix so far (as of Nov 7, 13:44; by Ritik; earlier Nov 5, 09:08)

**The verdict.** Every trained version follows fewer wrong hints than base and passes Gate 3. **None beats one line of
instruction in the prompt by its pre-registered rule.**
- **LoRA matched the instruction** (the 30, F28). Its training changed the reasoning LoRA writes, not how it reads the
  hint (F39).
- **Consistency training (A40) trades instead** (E2's 120 fresh questions, F41, read Nov 7). It follows the wrong hint
  in 12% of runs against the instruction's 33%, but takes the correct hint in 76% against 91%. The rule's reading is
  **"fewer, but costs acceptance"**: it ignores hints, the right ones too.
- **Adding the note (A42, F43)** follows fewest of all (9%), at a larger cost (71% of correct hints taken). Same
  reading.
- **Inside the model, A40 is the first fix that changes how the hint is read off** (A41, F42). In layers 0–14, before
  the readout, it removes part of the hint's pull, where LoRA's weights added to it.

Olmo 3 7B Think, the held-out 30 MMLU-Pro questions, 930 runs per system (F28, final Oct 31). Sources:
[FINDINGS](../FINDINGS.md); Gate 3's [table](../../cot-disclosure/results/summaries/trackA/gpu/eval/gate3_table.md)
and [report](../../cot-disclosure/results/summaries/trackA/gpu/eval/eval_report.json) (the percentages).

**1. What each version did** (counts; differences in points, 95% intervals clustered by question)

| system (what is trained) | wrong hints followed | − base | − prompt_only | correct hints accepted | no-hint accuracy (− base) | hiding, keyword (− base) | Gate 3 |
|---|---|---|---|---|---|---|---|
| base | 249 of 530 (47%) | — | — | 206 of 238 | 58 of 90 | 150 of 530 | |
| prompt_only (one line, no training) | 179 of 532 (34%) | −13 [−21, −6] | — | 206 of 239 | 56 of 89 (−2) | 109 of 532 (−8 [−12, −4]) | not trained |
| LoRA (all 32 layers) | 197 of 532 (37%) | −10 [−16, −4] | **+3 [−1, +8]** | 208 of 239 | 56 of 89 (−2) | 21 of 532 (−24 [−32, −17])* | passes |
| tags (a learned source-tag table; base frozen) | 215 of 524 (41%) | −6 [−10, −2] | **+7 [+1, +14]** | 199 of 237 | 60 of 89 (+3) | 116 of 524 (−6 [−10, −3]) | passes |
| LoRA + tags | 211 of 532 (40%) | −7 [−13, −1] | **+6 [+1, +11]** | 207 of 237 | 59 of 90 (+1) | 20 of 532 (−25 [−33, −17])* | passes |
| LoRA on layers 15/19/23 only | 212 of 534 (40%) | −7 [−13, −2] | **+6 [+0.4, +12]** | 204 of 236 | 56 of 89 (−2) | 50 of 534 (−19 [−25, −13])* | passes |

- **Following.** All four cut wrong-hint following against base, by 6 to 10 points; the one line cut 13. Against it,
  paired by question (*not pre-registered*), LoRA matches it and the other three follow more wrong hints.
- **Correct hints and accuracy.** Acceptance stays near base's (84–87% against 87%); accuracy moves 3 points or less.
  **Not computed** (in neither F28 nor the summaries): intervals for acceptance, or for accuracy and hiding − prompt_only.
- **Hiding** (followed a wrong hint, final answer doesn't name it; keyword) holds for tags. \*Not for the LoRA versions:
  their trained final-answer opener names the hint ("The tool suggested (B).") in 390 to 469 of about 532 wrong-hint
  runs (base 146), so −19 to −25 mostly counts the opener. Hand labels decide, and none gives a LoRA − base yet.
- **False disclosure.** Keyword candidates rose for LoRA and LoRA + tags (+10 each). By hand labels LoRA's are rarely
  real: 1 (Ritik) and 2 (AI rater 1) of 147 reject the hint yet end on it; most (97, 89) say it shaped the answer.
- **Tags aren't tool-specific:** the predicted extra help on the inserted tool turn isn't borne out (tags −2 [−13, +9];
  LoRA + tags −13 [−24, −1], the wrong side).

**1b. Consistency training on E2** (A40 and A42; 120 questions, 1,440 runs a system; F41, F43; read Nov 7 by the
rules fixed Nov 5 and 6; [A40's reading](../../archive/sessions/2026-11-07/2026-11-07_1329_A_a40-reading.md),
[A42's](../../archive/sessions/2026-11-07/2026-11-07_1331_A_a42-reading.md))

| system | wrong hints followed | − the instruction | correct hints accepted | − the instruction | no-hint accuracy | reading |
|---|---|---|---|---|---|---|
| base | 297 of 703 (42%) | | 439 of 476 (92%) | | 156 of 236 (66%) | |
| the instruction (prompt_only) | 237 of 713 (33%) | — | 431 of 476 (91%) | — | 154 of 235 (66%) | |
| LoRA | 248 of 705 (35%) | | 421 of 477 (88%) | | 155 of 235 (66%) | A39's, not read yet |
| **A40** (consistency training) | **84 of 694 (12%)** | **−21 [−26, −16]** | **347 of 459 (76%)** | **−15 [−20, −10]** | 146 of 229 (64%) | **fewer, but costs acceptance**; R1 passes |
| **A40 + note** (A42) | **64 of 706 (9%)** | **−24 [−30, −19]** | **334 of 472 (71%)** | **−20 [−26, −14]** | 147 of 238 (62%) | **fewer, but costs acceptance**; R3 adds, costs acceptance; R1 passes |

- **The trade is the risk A40's log named in advance** (its §4 and §9): trained only on questions it could solve, it
  learned to set hints aside, so it sets aside correct ones too.
- **Against LoRA,** A40 follows 23 points fewer and accepts 13 fewer: the same trade.
- **Hiding** isn't used: A40's trained final answer names the hint, so a keyword count says little without hand labels.

**2. Why they matched the instruction instead of beating it**

*What was shown.*
- **The targets** ([make_targets.py](../../cot-disclosure/finetune/make_targets.py)'s docstring): context distillation,
  Olmo's own reply to the hinted prompt with no instruction anywhere, after a reasoning opener we prefilled in its voice
  ("The tool's answer could be wrong, so I'll work this out myself first and then compare.") and a final-answer opener
  stating the hint. A target was kept only if it ended on the question's no-hint answer.
- **What training learned** (F20; teacher-forced loss, LoRA at epoch 2 against base). The taught tokens fell 58%. The
  opener, 3% of them, fell 97% and is half that drop; without it, 40%. Hint-check sentences fell 23%, the final answer
  53%, everything else 19%. LoRA on 15/19/23 (3.9% of LoRA's parameters) got 85–90% of LoRA's drop.
- **Where training acts** (A18, F39). On base's own reasoning, LoRA's weights pull toward the hint's letter harder, not
  less (−0.72 logits [−1.02, −0.39]; 28 cases, 13 questions). LoRA's own following still runs through the readout at
  15/19/23 (share 1.29 [1.10, 1.51]). The rule's reading: "acts in the reasoning".
- **Where consistency training acts** (A41, F42). On the same cases, A40's weights remove part of the hint's pull
  (+0.68 logits [+0.17, +1.18]), more than LoRA (+1.40 [+0.73, +2.09]), from layers 0–14, before the readout layers.
  The rule's reading: "stops the readout, before them". So the kind of target changed how the weights read the hint,
  and it bought fewer wrong hints followed at the price of correct ones (F41).
- **Cutting the readout instead** (B1; F27, F38). On set A, every stronger attention cut lowered the forced wrong answer
  more but cost correct hints over 5 points. On the 30, the tool-turn span cut following there by 17 points (−17 [−30, −3]), but
  acceptance fell 7 points (25 → 23 of 30) against a 5-point limit: "ignores tools", underpowered.

*Our reading (interpretation; how strongly the sources support it, in brackets).*
- **The targets mostly taught the model what to say about the hint, not to stop it pulling** [moderate]. The opener is
  half of what was learned; on base's reasoning LoRA's weights pull harder; LoRA names the hint in 456 of 532 wrong-hint
  answers yet follows 197, and most labelled candidates say the hint shaped a wrong answer. Against it: LoRA follows 10
  points less than base, so its reasoning helps some. Untested directly: one version, 13 questions, teacher-forced loss.
- **The openers carry the instruction's message** [plausible, untested]. The
  [note](../../cot-disclosure/finetune/prompts/guide_note.txt) says the hint "may be wrong", "check it against your own
  working", "say what the tool or the user suggested"; the openers say much the same. The note wasn't used to make the
  targets (F28, corrected Oct 30). If training mostly installed that message, matching the instruction is expected.
- **The readout carries the hint's letter, not whether it is right** [weak]. Cutting it costs correct hints too (F27,
  F38); training's cut kept acceptance near base's (no interval). B1 is underpowered at 30 questions.
- **Power** [shown]. On the 30, following differences are ±6 to ±7 points (A39 log §1): too wide to tell apart.

**3. What A39 will settle** ([its log](../../archive/sessions/2026-11-03/2026-11-03_1130_A_e2-a39-prereg.md) §1–4, §18)
- **E2:** 120 fresh MMLU-Pro questions (30 each of law, engineering, chemistry, physics; not the 30, Track A's pool or
  C15's). Planned 95% half-widths: following ±4.6, ±4.9, ±3.8 (LoRA − base, prompt_only − base, LoRA − prompt_only).
- **Seven systems:** base, prompt_only, LoRA, LoRA + note, a wrapper (every tool message prefixed "[unverified tool
  output] "), wrapper + note, LoRA + wrapper. 12 runs a question each; 7,200 on E2 after shared runs.
- **The rules,** paired by question: **R1**, Gate 3's rule against base (for prompt_only and LoRA a powered
  replication; F28 stays); **R2**, each against prompt_only: "fewer than the instruction", "more" or "no difference
  detected"; **R3**, each combination against its parts; **R4**, the wrapper against base on the tool turn, by B1's rule.
- **What each outcome means** (said Nov 3): "fewer than the instruction" is the first fix that beats one line; a
  combination "adds to both": they stack; the wrapper "works": marking the source does what training didn't; all "no
  difference detected" at ±5: the instruction is as good as these fixes get, now with the power to say so.
- **When:** complete (every run of all seven systems has an ok record, Nov 7, 13:28); its rule reads it once complete,
  so it is read when Ritik chooses, by Nov 17 ([PLAN](../PLAN.md)). The partial rule (§18, Nov 15 23:59) isn't
  needed.

**4. Next.**
- **A39** (the wrapper and the combinations, with a powered replication of Gate 3) is complete on E2 and the 30.
  Its rule reads it once complete, by Nov 17 (Ritik). Its base, prompt_only and lora rows are already printed above as
  A40's comparisons; its own rules R1–R4 aren't read yet.
- **B1R2** (B1's span on E2) is running: 19 of 40 parts done at 13:18 Nov 7. Read when complete, or partial at
  Nov 15 23:59.
