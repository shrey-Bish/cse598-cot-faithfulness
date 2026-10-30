# Candidate claims: evidence, status, objection, what settles it

Bullets for the team; numbers as in [`docs/FINDINGS.md`](../FINDINGS.md) (Oct 29; updated 23:15 with C11–C14, Oct
30 01:10 with C15, 04:00 with B15, 09:30 with set A, B1's alpha, Gate 3 interim, Qwen3-8B and C13). Status words as in
FINDINGS: *confirmed* (measured as stated, the interval excludes no effect), *tentative* (direction
there, interval includes 0 or a confound remains), *waiting* (the run is going or planned).
`[TONIGHT: ...]` marks a number tonight's runs fill in.

## Thread 1: where the hint is read, and a repair that acts there

**1.1 A hint from a tool moves thinking models more than the same hint from the user.**
- **Evidence:**
  - F1 (served format, 2 models: +48 [+31, +65]).
  - Gate 2 in Track B, 54 questions × 3 runs, tool − user, pasted / real call or injected:
    - Qwen3 30B Thinking +35 [+24, +46] / +31 [+22, +42] (F15);
    - Qwen3 30B Instruct +21 [+12, +31] / +90 [+83, +96] (F16);
    - Olmo 3 7B Think +32 [+22, +42] / +21 [+13, +30] (F17);
    - Qwen3-8B, the same weights, thinking on +19 [+10, +29] / +78 [+69, +86], off +13 [+7, +21] / +13 [+3, +23]
      (F29).
- **Status:** *confirmed* (four models; thinking on and off in one of them). *Tentative* for Olmo alone in its pinned format (F1:
  +19 [−2, +40], one user run per question).
- **Strongest objection:** the channels differ in more than the source: wording, position, and
  the pasted block sits inside the user turn.
- **Settles it:** the real tool call (F15, F16) and the inserted tool turn (F17) use the same JSON
  as the pasted block. A wording-matched user channel ("my notes say (B)") would close the rest.

**1.2 The private reasoning mentions the hint; the final answer almost never does.**
- **Evidence:**
  - F3: Test 1 private 208 of 216 vs final 8 of 216.
  - F15: after a tool call the final answer is a bare letter, whether the lookup was right or
    wrong (C4: 80 of 84 vs 71 of 75; no tool 2 of 159).
- **Status:** *confirmed* as keyword and length counts. Hand labels *waiting* (L3, 101 rows; L5,
  171 rows with a 20-row keyword check).
- **Strongest objection:** a keyword is not an acknowledgment, and "the user asks…" fires with no
  hint (22 of 72).
- **Settles it:** two raters, Cohen's kappa per channel; the keyword check (rows 152–171).

**1.3 The hinted answer takes over late, on a few questions, and the lead swings.**
- **Evidence:** F4 (43 of 110 followed on sure questions; 26 of 43 late; on 9 of 11 questions), F5,
  F14.
- **Status:** *confirmed* as forced-answer readings, but concentrated (top 3 questions hold 23 of
  43).
- **Strongest objection:** forced answers off-distribution; few questions.
- **Settles it:** more questions with late takeovers. Set A (tonight) adds the 34 validation
  questions: set A (Oct 29, Voyager) followed 30 of 100 pasted and 26 of 101 inserted runs, with 39 late takeovers
  on 16 sure questions (above the minimum of 5). Step 10 on them is done (F26); Step 9 is back, unread.

**1.4 Three full-attention layers (15, 19, 23) read the hint's letter straight from the prompt.**
- **Evidence:**
  - F11: 0.90 [0.85, 0.96] of the drop at the takeover; per layer 0.34, 0.17, 0.39.
  - F12: the top answer→hint heads sit in the same layers; L19H31, L23H17 and L15H31 separate
    followed from resisted.
  - F13: removing the prompt's letter moves the answer off W in 13 of 21 cuts; deleting the
    reasoning's mentions brings back the own answer in 7 of 19.
- **Status:** *confirmed* on two question sets, one model: Test 2 (19 cuts, 9 questions) and set A (31 cuts, 16
  questions not used to find it; F26). The mechanism as a whole is *tentative*.
- **Strongest objection (the one that blocks a repair paper):** the layers and heads were found on
  the same 30 MMLU-Pro questions we evaluate on, so a fix designed from them is circular. Also one
  model and one patching setup.
- **Settles it:** set A, the 34 validation questions (in neither training nor the held-out 30).
  Pre-registered: does the share of the hint-row drop at cut (ii) replicate at 15, 19 and 23?
  **Answered (F26): replicates.** 0.90 [0.76, 1.06] at 15, 19 and 23 on 16 questions (lower bound above 0.375), and
  23, 15, 19 are the three largest drops (0.43, 0.30, 0.17). The circularity objection is answered.
  Step 9 too (F32, pre-registered): F12's three heads separate followed from resisted runs on set A, +0.068 [+0.044,
  +0.088] (Test 2 +0.084).

**1.5 Training learns the taught text; most of LoRA's gain is reachable from the three layers alone.**
- **Evidence:** F20.
  - LoRA's taught tokens −58% [−67, −51] against base; without the fixed opener −40% [−46, −36];
    the rest −19%.
  - LoRA on the attention of layers 15/19/23 only (1.6 M parameters, 3.9% of full LoRA's) reaches
    85–90% of that drop.
- **Status:** *confirmed* as teacher-forced loss on held-out questions. **Behavior, interim (F28): Gate 3 is met
  by LoRA** (following −10 [−16, −4], no-hint accuracy −2 points, hiding −24). LoRA on 15/19/23 is still running.
- **Strongest objection:** loss is not behavior. Half the taught drop is a memorized opener. Now also, from Gate 3
  (F28):
  - LoRA passes by the pre-registered rule, *and* it doesn't beat an independent one-line instruction in the prompt
    (prompt_only −13; LoRA minus it +3 [−1, +8]);
  - *and* its false-disclosure candidates rise (+10 [+2, +18]) while the instruction's fall (−9 [−14, −4]).
- **Candidate cautionary claim (waiting on hand labels):** fine-tuning for disclosure reduced hint-following no more
  than an instruction, and may have taught the model to claim checks it didn't do. The labels of LoRA's
  false-disclosure candidates go first in the queue.
- **Settles it:** the label sample (false disclosure; what the trained answer says); LoRA on 15/19/23 and the tag
  versions (Gate 3, all six systems).

**1.6 Input-embedding provenance tags don't help.**
- **Evidence:** F20.
  - tags alone −9% on the taught tokens without the opener, less than the −12% on the rest;
  - lora_tags − lora +0.0009 [+0.0004, +0.0014] nats;
  - injected − pasted +0.0003 [−0.0008, +0.0015].
- **Status:** *confirmed* in loss. Behavior *waiting* (Gate 3).
- **Strongest objection:** loss can't show whether tags change how tool text is treated.
- **Settles it:** Gate 3's behavior test per channel.

**1.7 (B1) Downweighting attention to tool-span keys in those layers cuts wrong-tool-hint following
without making the model ignore correct tools.**
- **Evidence:** alpha chosen on set A by the rule fixed before set A existed (F27). Deployable (tool turn) 0.25:
  forced P(W) −7.6 [−12.2, −3.7], correct hint −4.8. Oracle 0.5: −8.6 [−12.6, −5.2], correct hint −4.3. Lower alphas
  cost a correct hint more than 5 points.
- **Status:** alpha fixed; behavior *waiting* (provenance_gen, 4 parts, submitted Oct 30).
- **Strongest objection:** it may just make the model ignore tools. Its layers and alpha could be
  tuned on the evaluation questions.
- **Settles it:**
  - alpha chosen on set A (forced answer at the takeover cuts);
  - then generation on the held-out 30: wrong-hint following vs correct-hint acceptance (the
    trade-off curve) and no-hint accuracy, at the chosen alpha and at alpha = 1 (same code path);
  - deployable (tool-role span) and oracle (pasted span) reported apart.
- `[SOL: following at alpha* (0.25 deployable, 0.5 oracle) vs 1 = ___; correct-hint acceptance = ___]`

**1.8 (B2) A learned per-head provenance bias in those layers beats input-embedding tags.**
- **Status:** *waiting* (code tonight, training after Gate 3's schedule allows).
- **Settles it:** same data and settings as lora_attn3, alone and together; loss by part (S7's
  method), then behavior.

## Thread 2: automation bias in LLM reviewers

**2.1 Deference to the solver's tool trace is family-specific: Olmo reviewers defer (2 of 6 reviewers, 4
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
    interval is wide (−5 [−26, +15]: it reaches −26, past the −20 line; "doesn't defer" because it includes 0), and
    its own check is weak (27 of 73 alone), so its test has less room.
  - C15 (F24, done): on 100 fresh items Olmo 3.1 32B defers again (39 → 10 of 53, −55 [−70, −38]) and Qwen3 30B
    Instruct doesn't (−6 [−15, +4]): *confirmed* on fresh items.

**2.2 It becomes as good as the tool, no longer a second opinion.**
- **Evidence:** F18. Right in 128 of 159 from the answer, 92 and 89 with the trace; the tool
  itself 84 of 159. Good lookups 67 → 84 of 84 (+20 [+8, +35]).
- **Status:** *confirmed* (Olmo).
- **Objection:** on a mix with more good lookups, deferring would look like a gain.
- **Settles it:** report both sides at the observed bad-lookup rate (here 75 of 159) and say what
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
- **Evidence:** C14 (exploratory: chosen on C4's cases as reviewed in C4 and C9–C12). Against the checker's
  pipeline with the same reviewer: catches 56–73 of 73 against 73; with Qwen3 reviewers about the same false
  alarms (+1 [−6, +8]) at ~30–45% of the checker's tokens; with Olmo reviewers 12–21 points more false alarms.
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
- **F17:** Gate 2 clear for a third model and family. The system-turn confound for bare answers
  is *tentative*.
