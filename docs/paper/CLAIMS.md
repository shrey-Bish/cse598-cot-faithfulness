# Candidate claims: evidence, status, objection, what settles it

Bullets for the team; numbers as in [`docs/FINDINGS.md`](../FINDINGS.md) (Oct 29; updated 23:15 with C11–C15 and
B15). Status words as in
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
    - Olmo 3 7B Think +32 [+22, +42] / +21 [+13, +30] (F17).
- **Status:** *confirmed* (three models). *Tentative* for Olmo alone in its pinned format (F1:
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
  on 16 sure questions (above the minimum of 5); Steps 9 and 10 on them are queued on Sol.

**1.4 Three full-attention layers (15, 19, 23) read the hint's letter straight from the prompt.**
- **Evidence:**
  - F11: 0.90 [0.85, 0.96] of the drop at the takeover; per layer 0.34, 0.17, 0.39.
  - F12: the top answer→hint heads sit in the same layers; L19H31, L23H17 and L15H31 separate
    followed from resisted.
  - F13: removing the prompt's letter moves the answer off W in 13 of 21 cuts; deleting the
    reasoning's mentions brings back the own answer in 7 of 19.
- **Status:** *confirmed* on 19 cuts, 9 questions, one model. The mechanism as a whole is
  *tentative*.
- **Strongest objection (the one that blocks a repair paper):** the layers and heads were found on
  the same 30 MMLU-Pro questions we evaluate on, so a fix designed from them is circular. Also one
  model and one patching setup.
- **Settles it:** set A, the 34 validation questions (in neither training nor the held-out 30).
  Pre-registered: does the share of the hint-row drop at cut (ii) replicate at 15, 19 and 23?
  `[TONIGHT/SOL: share at 15/19/23 on set A = ___ (questions ___)]`

**1.5 Training learns the taught text; most of LoRA's gain is reachable from the three layers alone.**
- **Evidence:** F20.
  - LoRA's taught tokens −58% [−67, −51] against base; without the fixed opener −40% [−46, −36];
    the rest −19%.
  - LoRA on the attention of layers 15/19/23 only (1.6 M parameters, 3.9% of full LoRA's) reaches
    85–90% of that drop.
- **Status:** *confirmed* as teacher-forced loss on held-out questions. Behavior *waiting* (batch 3,
  Gate 3).
- **Strongest objection:** loss is not behavior. Half the taught drop is a memorized opener.
- **Settles it:** batch 3: hint following, no-hint accuracy and disclosure per version (Gate 3).

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
- **Evidence:** none yet. Code tonight; Sol tomorrow.
- **Status:** *waiting*.
- **Strongest objection:** it may just make the model ignore tools. Its layers and alpha could be
  tuned on the evaluation questions.
- **Settles it:**
  - alpha chosen on set A (forced answer at the takeover cuts);
  - then generation on the held-out 30: wrong-hint following vs correct-hint acceptance (the
    trade-off curve) and no-hint accuracy, at the chosen alpha and at alpha = 1 (same code path);
  - deployable (tool-role span) and oracle (pasted span) reported apart.
- `[SOL: following at alpha* vs 1 = ___; correct-hint acceptance = ___]`

**1.8 (B2) A learned per-head provenance bias in those layers beats input-embedding tags.**
- **Status:** *waiting* (code tonight, training after Gate 3's schedule allows).
- **Settles it:** same data and settings as lora_attn3, alone and together; loss by part (S7's
  method), then behavior.

## Thread 2: automation bias in LLM reviewers

**2.1 A reviewer shown the solver's tool trace defers to the tool.**
- **Evidence:** F18 (C4, 53 items, 318 cases).
  - Olmo 3.1 32B Instruct corrects 59 of 73 wrong answers from the answer alone, 6 with the
    private reasoning (−73 [−86, −58]) and 3 with the tool log (−77 [−91, −61]). It keeps the
    wrong letter 66 and 70 of 73 and names the answer key.
  - On both sets.
- **Status:** *confirmed* for two reviewers of one family: Olmo 3.1 32B (F18) and Olmo 3 7B Instruct (C11, F22:
  32 → 1 of 73, −42 [−58, −28]). Qwen3 30B Instruct and Qwen3 30B Thinking don't (+1 [−6, +10]). In four reviewers
  it follows the family, not size or thinking: *tentative*.
- **Strongest objection:** one family of two, one solver's cases. It could be prompt-specific. Deferring to an
  answer key can be reasonable.
- **Settles it:**
  - C13 (Sol, queued): IBM Granite 4.1 30B and Mistral Small 3.2 24B. Does family still predict it?
    `[Granite ___; Mistral ___]`
  - C15 (F24, done): on 100 fresh items Olmo 3.1 32B defers again (39 → 10 of 53, −55 [−70, −38]) and Qwen3 30B
    Instruct doesn't (−6 [−15, +4]): *confirmed* on fresh items.

**2.2 It becomes as good as the tool, no longer a second opinion.**
- **Evidence:** F18. Right in 128 of 159 from the answer, 92 and 89 with the trace; the tool
  itself 84 of 159. Good lookups 67 → 84 of 84 (+20 [+8, +35]).
- **Status:** *confirmed* (Olmo).
- **Objection:** on a mix with more good lookups, deferring would look like a gain.
- **Settles it:** report both sides at the observed bad-lookup rate (here 75 of 159) and say what
  a lower rate would show.

**2.3 Prompt fixes don't restore the check.**
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
- **B15 (running, pre-registered):** can one instruction ("say what your answer is based on, including any tool
  result you used") bring the tool back into the final answer? Thinking names it after 3 of 54 calls today; the
  bare letter is 51 of 54. *Waiting.* If it works, F15 is a default, not a limit; if not, it is harder to fix than a
  prompt.
- **F17:** Gate 2 clear for a third model and family. The system-turn confound for bare answers
  is *tentative*.
