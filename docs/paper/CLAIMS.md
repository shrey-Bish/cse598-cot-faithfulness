# Candidate claims: evidence, status, objection, what settles it

Bullets for the team; numbers as in [`docs/FINDINGS.md`](../FINDINGS.md). Last updated 2026-11-13 09:55 (claim 1.5: L6 read, F45; earlier 2026-11-08 15:10 (B20, FB1, in claim 1.1 and Gate 2's gap marked; claim 1.5: LoRA + note's acceptance cost in the same sentence, L6 reduced and its sheet built; earlier 2026-11-07 20:39: A39 read, F44: claims 1.5 and 1.6; L6 pre-registered, not run; earlier 13:53: A40, A41 and A42 read: claim 1.5; B1R2 running: claim 1.7; earlier 2026-11-05 09:52: B1R2 not run: GPU time given to A40; 2026-11-04 17:50: the second
rater corrected: an AI model, ChatGPT 5 Astra High, not Shrey; earlier: B17, B1, the hand labels, A18, B1R2 decided; **edited by:** Ritik; history: `git log -- docs/paper/CLAIMS.md`). Status words as in FINDINGS: *confirmed* (measured as stated,
the interval excludes no effect), *tentative* (direction there, interval includes 0 or a confound remains), *waiting*
(the run is going or planned), *not supported*, *dropped*.

## Thread 1: where the hint is read, and a repair that acts there

**1.1 A hint from a tool moves thinking models more than the same hint from the user.**
- **Evidence:**
  - F1 (served format, 2 models: +48 [+31, +65]).
  - Gate 2 in Track B, 54 questions × 3 runs, tool − user, pasted / real call or injected:
    - Qwen3 30B Thinking +35 [+24, +46] / +31 [+22, +42] (F15);
    - Qwen3 30B Instruct +21 [+12, +31] / +90 [+83, +96] (F16);
    - Olmo 3 7B Think +32 [+22, +42] / +21 [+13, +30] (F17);
    - Qwen3-8B, the same weights, thinking on +19 [+10, +29] / +78 [+69, +86], off +13 [+7, +21] / +13 [+3, +23]
      (F29);
    - gpt-oss-20b, the same weights at reasoning effort low / medium / high, pasted +24 [+16, +34], +25 [+15, +36],
      +26 [+16, +36]; real call +14 [+7, +20], +25 [+16, +35], +26 [+17, +36] (B17, F37; reported with no decision;
      temperature 1.0; run after its one-day window, pre-registration §13).
  - **B20 (FB1, read Nov 7 by Arsha), three more open-weight families on Sol,** tool − user, pasted / the tool channel
    (the inserted turn for Gemma and Nemotron, Granite's own call), clear in all 10 readings: Gemma 4 26B-A4B on +39 /
    +24, off +73 / +33; Nemotron 3 Nano 30B-A3B on +51 / +75, off +35 / +61; Granite 4.2 8B on +18 / +91 (temperature
    1.0; Granite thinking on only). R2, minus the authority claim: tool beyond it in 5 of 10, the claim more in 1 (2 at
    the 16,000 cut), no difference detected in 4.
  - **B16 (F35, Nov 1), the user with the tool's authority** ("My course answer key says the answer is (X)."), tool
    minus that, pasted / the tool's channel: Qwen3 30B Thinking +12 [+5, +19] / +6 [−7, +19]; Instruct +6 [−1, +13] /
    **+75 [+65, +85]**; Olmo 3 7B Think −3 [−10, +3] / **−14 [−21, −6]** (authority moves it more). The share of
    Gate 2's gap the claim closes: the pasted block 68% and 71% (Qwen3), 109% (Olmo); the tool's channel 80%
    (Thinking), 164% (Olmo), 16% (Instruct's own call).
- **Status:** *confirmed* as worded, against the plain user hint (five models; thinking on and off in one of them,
  three reasoning efforts in another; and B20's three families, FB1). **Gate 2's gap part marked met Nov 8.**
  *Tentative* for Olmo alone in its pinned format (F1: +19 [−2, +40], one user run per question). **Restated by B16:**
  most of the gap is the source's claimed authority, not the channel; the channel adds to it only for Qwen3 30B
  Instruct's own call and Qwen3 30B Thinking's pasted block.
- **Strongest objection:** B16 is cross-day (T11: its tool arms were Track B's replies, replayed from the cache; the
  canary held) and one wording, and "answer key" is also the tool's name for itself.
- **Settles it:** B19, the same comparison made the same day (new seeds), and a second authority wording.
  **Same day, answered (B19, Nov 1, F35):** new seeds and no reply cache, the same six readings: Thinking +10 [+4,
  +17] / −2 [−13, +10]; Instruct +4 [−1, +10] / **+75 [+65, +85]**; Olmo −3 [−11, +5] / **−14 [−22, −7]**.
  **A second wording, answered (B24, Nov 4, F40):** "The official solution manual says the answer is (X)." moves all
  three more than "A classmate of mine says…" (+41 [+31, +51], +12 [+4, +20], +32 [+23, +41]; same day): the pull
  grows with the claimed source's authority. Against B16's wording (cross-day): Qwen3 30B Thinking +21 [+14, +29], the
  manual higher, so the claim holds for B16's wording with that as its limit; Instruct and Olmo no difference detected.
  With the manual's wording the user's claim pulls as hard as every tool channel, or harder, except Instruct's own
  call (+73 [+62, +84] beyond it).

**1.2 The private reasoning mentions the hint; the final answer almost never does.**
- **Evidence:**
  - F3: Test 1 private 208 of 216 vs final 8 of 216.
  - F15: after a tool call the final answer is a bare letter, whether the lookup was right or
    wrong (C4: 80 of 84 vs 71 of 75; no tool 2 of 159).
- **Status:** *confirmed* as keyword and length counts. **Hand labels (L3, Nov 3; Ritik and AI rater 1, ChatGPT 5
  Astra High): kappa below 0.6 in four of six cells** (private 0.63, tool 0.29, user 0.85; final 0.54, tool 0.59,
  user 0.43; F3), human-vs-AI agreement. They don't stand yet. L3 is now read under the LLM-judge protocol
  (pre-registered Nov 4): Ritik's labels are the final labels, several AI judges the reliability check; no
  acknowledgment claim from hand labels goes in the report before that. L5 (171 rows) waits.
  - Corrected Nov 4, 17:50: rater 2 was an AI model (ChatGPT 5 Astra High), not Shrey; see the 17:42 log. The
    two-rater route (settle the disagreements, tighten the guide, a fresh batch) no longer applies.
- **Strongest objection:** a keyword is not an acknowledgment, and "the user asks…" fires with no
  hint (22 of 72).
- **Settles it:** Ritik's labels against the AI judges' majority, Cohen's kappa per channel (the LLM-judge protocol);
  the keyword check (rows 152–171).

**1.3 The hinted answer takes over late, on a few questions, and the lead swings.**
- **Evidence:** F4 (43 of 110 followed on sure questions; 26 of 43 late; on 9 of 11 questions), F5,
  F14.
- **Status:** *confirmed* as forced-answer readings, but concentrated (top 3 questions hold 23 of
  43).
- **Strongest objection:** forced answers off-distribution; few questions.
- **Settles it:** more questions with late takeovers. Set A (Oct 29) adds the 34 validation
  questions: set A (Oct 29, Voyager) followed 30 of 100 pasted and 26 of 101 inserted runs, with 39 late takeovers
  on 16 sure questions (above the minimum of 5). Step 10 on them is done (F26); Step 9 is read (F32: the heads replicate).

**1.4 Three full-attention layers (15, 19, 23) read the hint's letter straight from the prompt.**
- **Evidence:**
  - F11: 0.90 [0.85, 0.96] of the drop at the takeover; per layer 0.34, 0.17, 0.39.
  - F12: the top answer→hint heads sit in the same layers; L19H31, L23H17 and L15H31 separate
    followed from resisted.
  - F13: removing the prompt's letter moves the answer off W in 13 of 21 cuts; deleting the
    reasoning's mentions brings back the own answer in 7 of 19.
- **Status:** *confirmed* on two question sets, one model: Test 2 (19 cuts, 9 questions) and set A (31 cuts, 16
  questions not used to find it; F26). In a second model, at its own layers: Qwen3-8B (F36, below). The mechanism as
  a whole is *tentative*.
- **Strongest objection (the one that blocks a repair paper):** the layers and heads were found on
  the same 30 MMLU-Pro questions we evaluate on, so a fix designed from them is circular. Also one
  model and one patching setup.
- **Settles it:** set A, the 34 validation questions (in neither training nor the held-out 30).
  Pre-registered: does the share of the hint-row drop at cut (ii) replicate at 15, 19 and 23?
  **Answered (F26): replicates.** 0.90 [0.76, 1.06] at 15, 19 and 23 on 16 questions (lower bound above 0.375), and
  23, 15, 19 are the three largest drops (0.43, 0.30, 0.17). The circularity objection is answered.
  Step 9 too (F32, pre-registered): F12's three heads separate followed from resisted runs on set A, +0.068 [+0.044,
  +0.088] (Test 2 +0.084).
  **"One model" (A37, F36, pre-registered Oct 30): replicates in Qwen3-8B,** whose 36 layers all see the whole
  prompt. The three layers chosen on the puzzles, 21, 22 and 29, hold 0.70 [0.60, 0.83] of the drop on MMLU-Pro (30
  cuts, 14 questions) and are its own top three; 0.74 on the puzzles. Less concentrated than Olmo's 0.90 (four layers
  hold 80%), the tool's own call only, and patching only (no heads). So the readout isn't an artifact of Olmo's
  sliding windows; the layers differ by model.

**1.5 Training learns the taught text; most of LoRA's gain is reachable from the three layers alone.**
- **Evidence:** F20.
  - LoRA's taught tokens −0.2740 nats [−0.3132, −0.2401] against base (−58%); without the fixed opener −0.1328
    [−0.1527, −0.1176] (−40%); the rest −19%.
  - LoRA on the attention of layers 15/19/23 only (1.6 M parameters, 3.9% of full LoRA's) reaches
    85–90% of that drop.
- **Status:** *confirmed* as teacher-forced loss on held-out questions. **Behavior, final (F28, Oct 31): Gate 3 is
  met, and all four trained versions pass** (following − base: LoRA −10 [−16, −4], tags −6 [−10, −2], LoRA + tags
  −7 [−13, −1], LoRA on 15/19/23 −7 [−13, −2]; no-hint accuracy within 3 points).
- **Strongest objection:** loss is not behavior. Half the taught drop is a memorized opener. Now also, from Gate 3
  (F28):
  - every version passes by the pre-registered rule, *and* none beats an independent one-line instruction in the
    prompt (prompt_only −13; each minus it, not pre-registered: LoRA +3 [−1, +8], tags +7 [+1, +14], LoRA + tags
    +6 [+1, +11], LoRA on 15/19/23 +6 [+0.4, +12]);
  - *and* the LoRA versions' false-disclosure candidates rise (LoRA +10 [+2, +18], LoRA + tags +10 [+2, +19]) while
    the instruction's fall (−9 [−14, −4]);
  - *and* the tags prediction (more help on the inserted tool turn) isn't borne out for either tag version.
- **Candidate cautionary claim, read with hand labels (L4 part 1, Nov 3; Ritik and AI rater 1, ChatGPT 5 Astra High;
  kappa 0.93, human-vs-AI agreement; F28):** fine-tuning for
  disclosure reduced hint-following no more than an instruction (stands), and may have taught the model to claim
  checks it didn't do: **not supported** for claimed disagreement. 1 and 2 of LoRA's 147 candidates are
  `rejects_hint` (the answer says the hint is wrong, yet ends on it); 97 and 89 say the hint shaped the answer. The
  "worked independently" half has no label; the raters could tell LoRA's style (`guess_trained` right on 270 and
  267 of 294). The reading was set after labeling, before counting (the L4 log, §6).
  - Corrected Nov 4, 17:50: rater 2 was an AI model (ChatGPT 5 Astra High), not Shrey; see the 17:42 log. The
    reading stays as read, as human + AI agreement.
- **Inside the fixed model (A18, F39, Nov 3): "acts in the reasoning".** On base's own reasoning, LoRA's weights pull
  toward the hint's letter harder, not less (R_LoRA −0.72 [−1.02, −0.39]; 28 cases, 13 questions; the hint's letter in
  30 of 30); its own following runs through the same readout, and F12's heads still separate outcomes (both
  secondaries replicate). So the fix acts through what the model writes, not on the readout.
- **Consistency training on E2 (A40, F41; A42, F43; read Nov 7 by rules fixed Nov 5 and 6):** a different kind of
  target, the model's own reasoning written without the hint. It follows far fewer wrong hints than the instruction
  (84 of 694 against 237 of 713; −21 [−26, −16]) but takes fewer correct ones (−15 [−20, −10]): **"fewer, but costs
  acceptance"**, against the instruction and against LoRA; R1 against base passes. With the note (A42): the same
  reading (−24 following, −20 acceptance); R3 "adds, costs acceptance". **So A40 doesn't beat the instruction by its
  rule;** the one that follows fewest does it by ignoring hints.
- **Inside the model (A41, F42, Nov 7): "stops the readout, before them".** On base's own reasoning A40's weights
  remove part of the hint's pull (+0.68 logits [+0.17, +1.18]), from layers 0–14, and more than LoRA (+1.40 [+0.73, +2.09]).
  The kind of target changes how the weights read the hint, unlike LoRA's.
- **The powered replication on E2 (A39, F44, read Nov 7 by the rules of Nov 3):** Gate 3's rule passes again for the
  instruction (−9 [−14, −4]) and LoRA (−7 [−11, −3]), and LoRA matches the instruction (R2 +2 [−2, +6], "no difference
  detected"), now with power. **LoRA + note is "fewer than the instruction"** (R2, following only: −8 [−12, −4]) at an
  acceptance cost of −9 [−13, −5]; A39's log called that reading in advance "the first fix that beats one line", and R3
  reads it "adds, costs acceptance". So no fix beats the instruction without a cost to correct hints.
- **Settles it:** L4 part 2 (LoRA minus base in labels). **Answered on E2 (L6, F45, Nov 13):** in hand labels, when
  LoRA follows a wrong hint its answer says so in 37 of 42 runs against the instruction's 18 of 42 (+45.2 [+25.4,
  +64.2], "discloses more than the instruction, in labels"; Ritik against J-opus kappa 0.961), and none of LoRA's
  claims to reject the hint it ends on (0 of 42). In plain words: training made the answer more candid about a hint it followed, in hand labels, without making it follow less. Limits: LoRA's trained opener names the
  hint (F28); one model, E2 only, 42 rows a system, the final answer only; the sheet not blind in practice, with J-opus
  (blind to systems) agreeing on 82 of 84 rows.

**1.6 Input-embedding provenance tags don't help.**
- **Evidence:** F20.
  - tags alone −9% on the taught tokens without the opener, less than the −12% on the rest;
  - lora_tags − lora +0.0009 [+0.0004, +0.0014] nats;
  - injected − pasted +0.0003 [−0.0008, +0.0015].
- **Status:** *confirmed* in loss. Behavior (F28): tags pass Gate 3 (−6 [−10, −2]) but help no more on the inserted
  turn than the pasted block (−2 [−13, +9]): not tool-specific.
- **A source mark in the prompt doesn't help alone either (A39, F44, read Nov 7 by the rules of Nov 3):** prefixing every
  tool output "[unverified tool output] " reads **"no effect"** on the inserted tool turn (R4: following −1 [−7, +4]).
  With the one-line instruction it "adds, costs acceptance" (following −14 [−20, −9], acceptance −12 [−18, −6] against
  the instruction alone); with LoRA it "adds to both" (−8 [−14, −2] against LoRA).
- **Strongest objection:** loss can't show whether tags change how tool text is treated.
- **Settles it:** Gate 3's behavior test per channel.

**1.7 (B1) Downweighting attention to tool-span keys in those layers cuts wrong-tool-hint following
without making the model ignore correct tools.**
- **Evidence:** alpha chosen on set A by the rule fixed before set A existed (F27). Deployable (tool turn) 0.25:
  forced P(W) −7.6 [−12.2, −3.7], correct hint −4.8. Oracle 0.5: −8.6 [−12.6, −5.2], correct hint −4.3. Lower alphas
  cost a correct hint more than 5 points.
- **Generation on the held-out 30 (F38, Nov 3),** each span minus alpha = 1, paired by question:
  - deployable (0.25), on the inserted tool turn: following 26 of 60 → 16 of 60, −17 [−30, −3]; correct-hint acceptance
    25 → 23 of 30 (−7 points); no-hint accuracy 16 → 19 of 30 (+10): **ignores tools** by the rule;
  - oracle (0.5), on every hint channel: following 61 of 120 → 50 of 120, −9 [−19, +1]: **no effect**.
- **Status:** *not supported as worded* by its rule (deployable "ignores tools", oracle "no effect"): a real cut in
  following on the inserted turn that misses its pre-registered acceptance limit; underpowered at 30 questions.
  *Tentative* on the cost: it is 2 of 30 runs, and no-hint accuracy, which the scaling can't touch, moved +10 by
  sampling alone. **A replication (B1R) isn't run:** 35 GPU-hours fit 70 fresh questions, an acceptance half-width
  of 6 to 9 points; ±5 needs about 107 to 245 questions (53 to 122 GPU-hours; F38). A38 isn't run. **B1R2, a
  labelled replication on E2 (120 questions; read Nov 13 by B1's rule, F38): "ignores tools" again.** Following
  82 of 240 → 49 of 240, −13.8 [−20.0, −7.5] (the cut replicates); correct-hint acceptance 211 → 197 of 240, −5.8 [−10.8,
  −1.3] (a real cost, past the 5-point limit by the point estimate, 2 runs; the interval includes −5); no-hint
  accuracy +0.8 [−6.7, +8.3]. B1's verdict on the 30 stays primary.
- **Strongest objection:** it may just make the model ignore tools. Its layers and alpha could be
  tuned on the evaluation questions.
- **Settles it:**
  - alpha chosen on set A (forced answer at the takeover cuts);
  - then generation on the held-out 30: wrong-hint following vs correct-hint acceptance (the
    trade-off curve) and no-hint accuracy, at the chosen alpha and at alpha = 1 (same code path);
  - deployable (tool-role span) and oracle (pasted span) reported apart.

**1.8 (B2) A learned per-head provenance bias in those layers beats input-embedding tags.**
- **Status:** *dropped* (scope, Oct 31; A31): code and CPU tests exist, never trained.
- **Settles it:** same data and settings as lora_attn3, alone and together; loss by part (S7's
  method), then behavior.

## Thread 2: automation bias in LLM reviewers

**2.1 Deference to the solver's tool trace is family-specific: Olmo reviewers defer (two of six reviewers, four
families); prompt fixes don't help the deferring family (2.3); the blind checker holds for all (2.5).**
- **Evidence:** F18 (C4, 53 items, 318 cases).
  - Olmo 3.1 32B Instruct corrects 59 of 73 wrong answers from the answer alone, 6 with the
    private reasoning (−73 [−86, −58]) and 3 with the tool log (−77 [−91, −61]). It keeps the
    wrong letter 66 and 70 of 73 and names the answer key.
  - On both sets.
- **Status:** *confirmed* for two reviewers of one family: Olmo 3.1 32B (F18) and Olmo 3 7B Instruct (C11, F22:
  32 → 1 of 73, −42 [−58, −28]). Qwen3 30B Instruct and Qwen3 30B Thinking don't (+1 [−6, +10]), nor do Granite 4.1
  30B (−5 [−26, +15]) and Mistral Small 3.2 24B (+19 [+10, +30]) (C13, F30). Over six reviewers and four families it
  follows the family: *confirmed*. The claim is "some reviewer families defer", not "reviewers defer".
- **Strongest objection:** one family of two, one solver's cases. It could be prompt-specific. Deferring to an
  answer key can be reasonable.
- **Settles it:**
  - C16 (F31): Olmo 3.1 32B corrects 25 against 36 of 53 when the solver, told to disclose, writes answers that
    name the lookup (−21 [−34, −8]); Qwen3 unchanged. C17 (F33): a fixed sentence naming the tool, added to bare
    answers, changes nothing (+0 [−11, +11] against own working). C18 (F34): removing the solver's own tool-citing
    sentences restores the check (25 against 9 of 34, +47 [+29, +65]). The deferring family follows the solver's
    citation of the tool's letter as authority, not a source label and not the remaining argument.
  - C13 (F30, done): neither Granite nor Mistral defers; the pre-registered reading is "Olmo-specific". Granite's
    interval is wide (−5 [−26, +15]: it reaches −26, past C11's −20 line (F22); "doesn't defer" because it includes 0), and
    its own check is weak (27 of 73 alone), so its test has less room.
  - C15 (F24, done): on 100 fresh items Olmo 3.1 32B defers again (39 → 10 of 53, −55 [−70, −38]) and Qwen3 30B
    Instruct doesn't (−6 [−15, +4]): *confirmed* on fresh items.

**2.2 It becomes as good as the tool, no longer a second opinion.**
- **Evidence:** F18. Right in 128 of 159 from the answer, 92 and 89 with the trace; the tool
  itself 84 of 159. Good lookups 67 → 84 of 84 (+20 [+8, +35]).
- **Status:** *confirmed* (Olmo).
- **Objection:** on a mix with more good lookups, deferring would look like a gain.
- **Settles it:** report both sides at the observed bad-lookup rate (here 75 bad and 84 good lookups) and say what
  a lower rate would show.

**2.3 Prompt fixes don't restore the deferring family's check.**
- **Evidence:**
  - F19: a warning ("The tool's answer may be wrong; check it independently") gives 6 → 8 and
    3 → 4 of 73 (+3 [−4, +9], +1 [−3, +6]).
  - F21: committing to its own answer first: Olmo drops its own right answers (60 → 19 and 5);
    Qwen3 with the tool log gets worse (56 → 33 of 73, −32 [−44, −20]).
- **Status:** *confirmed* (one wording each).
- **Objection:** other wordings or stronger fixes might work.
- **Settles it:** a pre-registered set of wordings, or a structural fix (the trace withheld; the
  reviewer answers blind first and only reports disagreement).

**2.4 What the reviewer defers to: the tool's letter, or the reasoning around it.**
- **Evidence:** C12 (F23). With every statement of the tool's letter redacted, the Olmo 3.1 32B reviewer corrects
  23 and 24 of 73 (unredacted 6 and 3: +23 [+13, +34], +29 [+16, +41]; answer only 59: −49, −48). No harm to Qwen3.
- **Status:** *confirmed* as partial: the letter is part of the cue, the source (knowing it came from a key) the
  rest. The split by set (the gain on puzzles) is **H23**, a hypothesis.
- **C15 (F24):** on fresh items redaction restores part of Olmo's check again (10 → 23 of 53, +25 [+11, +38]), on
  MMLU-Pro as well as puzzles; H23 (where the reviewer can re-solve) is not supported (+14 [−13, +37]). The split by
  set is dropped from the claim.

**2.5 The check that never sees the tool works.**
- **Evidence:** F18. The re-ask checker flagged 73 of 75 bad lookups. False alarms on good lookups
  (7 of 80) are at the no-tool floor (12 of 155; −4 [−11, +4]). No wrong answer shipped in any
  variant.
- **Status:** *confirmed*.
- **Strongest objection:** it works only when the model can answer alone. The floor is already
  18% on steered MMLU-Pro.
- **Settles it:** items the model can't answer without the tool, and the cost in escalations.

**2.6 A cheaper check: escalate when a blind review and a trace-seeing review disagree.**
- **Evidence:** C14 (exploratory, no F entry: log 2026-10-29 23:00, `results/summaries/trackC/c14_disagreement.json`;
  chosen on C4's cases as reviewed in C4 and C9–C12). Against the checker's
  pipeline with the same reviewer: catches 56–73 of 73 against 73; with Qwen3 reviewers about the same false
  alarms (+1 [−6, +8]) at ~30–45% of the checker's tokens (Qwen3 30B Instruct 30–31%, Olmo 39–43%; Qwen3 30B
  Thinking's reviews cost 76%); with Olmo reviewers 12–21 points more false alarms.
- **Status:** *refuted* as a replacement for the checker (C15, F24): on fresh items neither pre-registered claim
  held, and it shipped 4 (Olmo) and 7 (Qwen3) wrong answers of 53 where the checker's pipeline shipped none. Keep as a
  cautionary result: chosen on C4's cases, it failed on fresh ones.

## Supporting (Track B)

- **F15:** after a tool call the final answer is a bare letter, right or wrong (the C4 control). It
  is *confirmed* for Qwen3 Thinking. How much is the declared tool and how much the call is
  *tentative*.
- **F16:** Instruct calls the tool every time and takes its letter (147 of 162); Thinking − Instruct
  on the real call −57 [−70, −43].
- **B15 (F25, pre-registered):** one instruction ("say what your answer is based on, including any tool result you
  used") brings the tool back into the final answer. After a call, Thinking names it in 33 of 63 against 3 of 54
  (+47 [+30, +64]) and Instruct in 149 against 35 of 162 (+70 [+59, +81]); the bare letter falls (−47, −61).
  *Confirmed as keyword counts*: F15 is a default, not a limit. Following doesn't change (all four intervals include
  0), nor do correct-tool acceptance or no-hint accuracy: the answer now says it took the tool's wrong letter, and
  still takes it.
  - **Objection:** keyword counts, and the instruction adds a little noise: with no hint the final matches the tool
    keyword in 4 and 17 of 162 (Track B: 2 and 8), some of them echoing the instruction. That is far below the rise
    after a call; hand labels would settle it.
  - **Objection:** the "before" is not an interleaved control. It is Track B's runs from one to two days earlier
    (same route, canary passed); only the right-letter arm without the instruction ran beside B15.
- **Headline:** disclosure can be prompted, but it doesn't reduce deference to the tool. Downstream (C16, F31), a
  final answer that names the tool makes the Olmo reviewer correct fewer wrong answers (−21 [−34, −8]; unclear by
  the 20-point rule) and leaves Qwen3 unchanged. A fixed naming sentence alone doesn't (C17, F33); removing the
  solver's tool-citing sentences restores the check (C18, F34, +47): the disclosure carries the authority claim.
- **F29 (Qwen3-8B, thinking on and off, the same weights):** thinking on calls the tool in 145 of 162 runs against
  35, and so follows the real call's wrong letter far more (+64 [+51, +75]); the pasted block and the user hint
  don't move (+4, −2). After a call with thinking on the final answer is bare (138 of 145) and names the tool in 0
  of 143 followed runs. *Confirmed* (one model).
- **F37 (B17, gpt-oss-20b at reasoning effort low, medium and high, the same weights; pre-registered):** more
  thinking changes neither following on the real call (high − low +7 [−1, +16]) nor the bare final answer after a
  call (−5 [−10, 0]; 37 of 37 bare at low): no change detected on both. It calls the tool in 129 against 37 of 162
  runs, but follows less once it has called (descriptive). Unlike Qwen3-8B (F29), more calls don't bring more
  deference here. Run after its one-day window (pre-registration §13).
- **F17:** Gate 2 clear for a third model and family. The system-turn confound for bare answers
  is *tentative*.
