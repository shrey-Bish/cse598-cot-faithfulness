# The report: skeleton (the team writes the prose from Nov 10)

**Edited by:** Ritik; each section's bullets by its owner (Track B's: Arsha, from `docs/trackB/REPORT_B.md`; Track C's: Shrey, from `docs/trackC/REPORT_C.md`), merged by Ritik.

Started Nov 3 by Ritik; updated Nov 5, 09:53 (B1R2 dropped, A40 pre-registered). Sections follow PLAN's report outline; each says who writes it and its figure. **Setup and
methods are filled in as bullets** (facts with their source), so the prose can be written from them. Numbers come from
[`FINDINGS.md`](../FINDINGS.md), the tracks' `FINDINGS_B.md` and `FINDINGS_C.md`, and the claims from
[`CLAIMS.md`](CLAIMS.md). Results freeze on Nov 18; the draft is due Nov 22, the final report Nov 24.

**Results bullets (§4–§10), Nov 4, 03:52 (Ritik; F40, B24, added 11:16; at 16:16 every bullet checked against
FINDINGS, and F40's limits, the slide figures and the traps T1–T12 (§10) added).** One bullet per finding, F1–F40: the
claim in plain words; the numbers as FINDINGS states them (X of Y, 95% intervals); its status, as FINDINGS words it;
its limits; its figure. `FINDINGS_B.md` and `FINDINGS_C.md` have no entries yet (FINDINGS_B holds one note before any
reading, descriptive: B20's smokes). A finding with two parts (the pull, the words) has a bullet in each section.
Results still running say so, with their dates. One row per finding:
[`tables/results_at_a_glance.md`](tables/results_at_a_glance.md). Figures: the report's own file and, where one exists,
the slide's 16:9 version from the same rows (`_slide`, `tools/slide_figures.py`; PLAN's presentation map).

## 1. Introduction (Ritik)

- The question, the three levels ("Where did that answer come from?": inside the model, in its words, between agents),
  the contributions.
- Figure: `docs/paper/figures/three_levels.svg`.
- The evidence per level, as the figure lists it: inside (F11, F26, F32, F36); in the words (F15, F25, F29, F35);
  between agents (F18, F31, F33, F34). Every result, one row each:
  [`tables/results_at_a_glance.md`](tables/results_at_a_glance.md).

## 2. Setup (Ritik; Track B's part, Arsha)

**Models** (each at its own recommended sampling; the version and where it ran recorded in every run):

| model | where, how | thinking | used in |
|---|---|---|---|
| Olmo 3 7B Think | Voyager (the pinned Think format, rendered by us, sent to /v1/completions); Sol (Hugging Face and vLLM) | always | Track A (all), Track B (F17) |
| Qwen3 30B-A3B Thinking-2507 | Voyager | always | Track B (F15), Track C's solver |
| Qwen3 30B-A3B Instruct-2507 | Voyager | none | Track B (F16), Track C's reviewer |
| Qwen3-8B | Sol, our vLLM, `enable_thinking` | on and off, same weights | Track B (F29), A37 (F36) |
| gpt-oss-20b (`6cee5e81`) | Sol, our vLLM, harmony | effort low / medium / high | B17 (F37), temperature 1.0 |
| Olmo 3.1 32B Instruct, Olmo 3 7B Instruct, Qwen3 30B Thinking, Granite 4.1 30B, Mistral Small 3.2 24B | Voyager; Sol (C13) | — | Track C's reviewers (F18, F22, F30) |
| B20's three (Gemma 4 26B-A4B, Nemotron 3 Nano 30B-A3B, Granite 4.2 8B) | Sol, our vLLM | on and off (Granite 4.2 8B on only: amendment, Nov 4) | B20, if run (Nov 15) |

- **Sampling:** temperature 0.6 for Track A and Track B's models (each model's recommended); gpt-oss-20b 1.0 (its
  recommended); every comparison is within one model or labelled with each model's setting.
- **The budget:** one 32,768-token budget per run, prompt and every reply (a run past it has no answer); Track B also
  reports a 16,000-token cut.

**The hint's channels** (one prompt per channel: `docs/paper/figures/channels.svg`, built by `tools/answer_key.py`):
- none (the baseline);
- the user's hint (two wordings in Track A: `user_turpin`, `user_professor`);
- the user's authority claim ("My course answer key says the answer is (X).", B16);
- the user's claim from a classmate or from the solution manual (B24, read Nov 4, F40; §4);
- a tool result pasted into the user's turn (`[tool result: lookup_answer_key] …`);
- the model's own call to the lookup tool (`tool_real`; Qwen3, gpt-oss);
- a tool turn written into the conversation (`tool_injected`, declared or undeclared; Olmo);
- a system note.

**Questions:**
- **The 24 pilot puzzles** (generated; uncontaminated) and **the 30 MMLU-Pro evaluation questions** (law, engineering,
  chemistry, physics): Track B's 54; Track A's held-out 30.
- **Track A's pool:** 1,600 questions (training, validation); **set A** (validation questions, never in training)
  replicates the localization (F26, F32).
- **C15's 100 fresh items** (60 MMLU-Pro from other categories, 40 puzzles): Track C's replication (F24).
- **E2:** 120 fresh MMLU-Pro questions from the evaluation categories, drawn by seed before any run on them (sha256
  `59c5c250…`; pre-registered Nov 3), the primary set for A39.

**Compute:** ASU's Voyager (served models, free); ASU's Sol (A100 80 GB; vLLM 0.31.0; Hugging Face generation for B1);
no paid calls.

## 3. Methods (Ritik; each track's section, its owner)

**Measures:**
- **Following:** an answered run ends on the wrong hint's letter. **Correct-hint acceptance:** a correct-hint run ends
  on the hint's letter. **No-hint accuracy.** The per-letter no-hint baseline beside following.
- **Mention:** keyword counts (`detect.py`) in the private reasoning and the final answer, until hand labels decide.
- **The bare answer:** a final answer of 30 characters or fewer ("Answer: (X)"), which can name nothing (F15).
- **Hiding:** follows the hint without mentioning it. **False disclosure:** ends on the hint's letter while the final
  answer claims it checked the hint and disagreed, or worked it out independently (keyword candidates; hand labels).

**Hand labels** (`docs/labeling/`; how they were made):

One human rater, Ritik, labeled every text in the two sheets: L3, 101 runs (the private reasoning and the final
answer), and L4 part 1, 294 final answers. Each sheet was blind (the outcome hidden), and each text took one of five
labels: no mention, mentions only, rejects the hint, says it changed the answer, or unclear. The plan was two human
raters. Instead, the second set of labels came from an AI model, ChatGPT 5 Astra High, which Ritik gave the same guide
and the same blind sheets. Every agreement number we report is therefore human-vs-AI agreement, not inter-human
reliability. On Nov 4, before any further judging, we pre-registered an LLM-judge protocol.
- **Three more AI judges:** Claude Opus, run in fresh sub-agents that saw only the guide and the blind rows, and two
  open models of other families on our university's inference service, Qwen3 30B Instruct and Olmo 3.1 32B Instruct.
- **Fixed for all three:** temperature 0 where it can be set, one fixed instruction, and labels from the five only.
  Every prompt and raw output was saved.
- **The final label of each text is Ritik's.** The AI judges are the reliability check. The protocol sent the texts
  where he and the judges' 3-of-4 majority differ back to him for a blind re-look, which decides. After the results,
  we narrowed the re-look (post hoc, disclosed) to the 7 texts where Claude Opus and ChatGPT 5 Astra High agreed with
  each other against him. He changed 4 to their label and kept 3. He wrote those 7 labels in his own words, and Claude
  Code put them into the five categories at his request; the session log shows both.
- **Gate 2's label part** required Ritik against that majority at kappa 0.6 or more in every cell, and it was not met:
  0.472 on the private reasoning, 0.234 on the final answer.
- **Why it wasn't met:** the two smaller judges barely followed the guide (near-constant labels on L4). Claude Opus
  agreed with Ritik at 0.669 and 0.837 on L3 and 0.967 on L4, and ChatGPT 5 Astra High at 0.627, 0.543 and 0.930.
- **The judges show no consistent advantage on texts written by their own model family.**
- **We make no claim that rests on these labels;** F3 is reported as keyword counts. The full numbers are in
  FINDINGS (F3, F28), and the protocol and its amendments in the session logs of Nov 4 (17:42, 17:45, 17:56).
- Corrected Nov 4: this section first said "two raters … no AI involved". The second rater was an AI model, not
  Shrey; see the 17:42 log.

**Statistics:**
- X of Y with 95% Wilson intervals; differences paired by question, 95% bootstrap clustered by question
  (`common.boot_diff`); fewer than 5 questions behind an interval: "too few questions", and no direction read.
- **Pre-registration:** every experiment's rule is written and committed before its first run
  (`archive/sessions/…-prereg.md`); the supplement's ledger checks each rule's commit against its first result, and
  DEVIATIONS lists every change of plan. Readings made after the fact are labelled so.

**Inside the model (Track A, Olmo 3 7B Think; A37 on Qwen3-8B):**
- the takeover: where in the reasoning the hinted answer takes over (probes, Step 3);
- attention to the hint at the answer position (Step 9) and activation patching at the takeover (Step 10, cut (ii)):
  the share of the hint's drop restored at each layer;
- localized on Test 2, replicated on set A (F26, F32) and on a second model (F36).

**The fixes:**
- **Training** (LoRA, source tags, both, LoRA on layers 15/19/23 only): targets that open by naming the hint; Gate 3's
  rule (fewer wrong hints followed, no-hint accuracy within 5 points, hiding not up; F28).
- **The one-line instruction** (`prompt_only`), the comparison every fix is held to.
- **B1:** attention from layers 15/19/23 to the tool span's keys scaled by alpha, chosen on set A (F27, F38).
- **A39:** a provenance wrapper (every tool output marked "[unverified tool output]") and combinations, on E2.

**Between agents (Track C):** a solver (Qwen3 30B Thinking) with a forced lookup, wrong about half the time by a seeded
oracle; reviewers shown the answer alone, with its explanation, with the private reasoning, or with the tool log; a
checker that re-solves without the tool; the no-tool team as the false-alarm floor (F18).

## 4. The failure: tools pull harder (Arsha)

- Gate 2 on five models (B18's table, `docs/paper/tables/trackB_final.md`); tool or authority (B16, F35); the authority
  dose (B24, F40); the thinking dose (B17, F37); B20 if read.
- Figure: `docs/paper/figures/gate2.png`.

**Results** (Gate 2 = tool minus the user's hint, following, paired by question, 54 questions × 3 runs unless noted):

- **F1. A hint from a tool moves thinking models more than the same hint from the user.**
  - Numbers: served format (Test 2, 30 MMLU-Pro items; Olmo 3 7B Think and Qwen3 30B Thinking, one run per question
    and channel): tool 17 of 31 [38, 71%] vs user 2 of 31 [2, 21%], +48 points [+31, +65]. Pinned format (Olmo 3 7B
    Think, its 20 hinted Test 2 questions): all tool channels 98 of 180 [47, 62%], user 7 of 20 [18, 57%]; tool − user
    +19 [−2, +40].
  - Status: confirmed in the served format (two thinking models); tentative for Olmo 3 7B Think alone in its own format.
  - Limits: in the pinned format the user channel rose (F2), and the interval includes 0.
  - figure: none
- **F2. The serving format changed Olmo 3 7B Think's hint following, but how much is unknown.**
  - Numbers: user 2 of 20 [3, 30%] served → 7 of 20 [18, 57%] pinned, +25 points [+0, +50]; pasted tool 10 of 20
    [30, 70%] → 40 of 60 [54, 77%], +17 [−10, +43]. Among answered runs: served 10 of 11 [62, 98%] vs pinned 40 of 59
    [55, 78%].
  - Status: tentative (confounded).
  - Limits: the token budget and the run counts differ too; not separable without rerunning the served format with
    continuation.
  - figure: none
- **F15. Qwen3 30B Thinking: tool and system hints move it, the user's doesn't.** (810 runs, every one answered.)
  - Numbers: following, user 3 of 162 [1, 5%], pasted 59 of 162 [29, 44%], real call 54 of 162 [27, 41%], system note
    57 of 162 [28, 43%]; no hint right in 151 of 162 [88, 96%]. Gate 2: pasted +35 [+24, +46], real call +31 [+22,
    +42]; at the 16,000 cut +34 [+23, +45] and +32 [+22, +43]. Following when it called: 54 of 54 [93, 100%]; without
    a call 0 of 108 [0, 3%]. By set, Gate 2 pasted / real: puzzles +7 [+1, +12] / +6 [+1, +11]; MMLU-Pro +57 [+41,
    +71] / +52 [+39, +66].
  - Status: confirmed (Gate 2; following after a real call, 54 of 54). Tentative: why the sets differ.
  - Limits: almost all of it is on MMLU-Pro; the sets differ in more than "knowledge vs worked out".
  - figure: docs/paper/figures/gate2.png (per channel: `docs/paper/supplement/figures/trackB_following.png`)
- **F16. Qwen3 30B Instruct calls the lookup every time and takes its letter; the Thinking checkpoint follows pasted
  and system hints more, but calls less.** (810 runs.)
  - Numbers: following, user 1 of 162 [0, 3%], pasted 35 of 162 [16, 29%], real call 147 of 162 [85, 94%], system note
    35 of 162 [16, 29%]; it called in 162 of 162. Gate 2: pasted +21 [+12, +31], real call +90 [+83, +96] (no run
    passes 16,000 tokens). Thinking minus Instruct: user +1 [+0, +3], pasted +15 [+6, +25], real call −57 [−70, −43],
    system note +14 [+7, +20].
  - Status: confirmed (Gate 2; the real call taken in 147 of 162; Thinking − Instruct). Tentative: "thinking cuts the
    call".
  - Limits: two separately trained checkpoints, not thinking on vs off in one model; the sets differ as in F15.
  - figure: docs/paper/figures/gate2.png
- **F17. Olmo 3 7B Think: tool hints move it more than the user's (Gate 2 clear, a third model).** (810 runs; 10 gave
  no answer.)
  - Numbers: following, user 13 of 162 [5, 13%], pasted 64 of 160 [33, 48%], inserted tool turn 46 of 157 [23, 37%],
    system note 34 of 159 [16, 28%]; no hint right in 123 of 162 [69, 82%]. Gate 2: pasted +32 [+22, +42], inserted
    +21 [+13, +30]; at the 16,000 cut +35 [+22, +48] (40 questions) and +18 [+9, +27] (49 questions).
  - Status: confirmed (Gate 2, both tool channels, both cuts).
  - Limits: its tool channel is the inserted tool turn (it never calls a tool itself); the 16,000 cut takes 173 of 810
    runs, so its cut numbers rest on fewer runs.
  - figure: docs/paper/figures/gate2.png
- **F29. Qwen3-8B, the same weights: thinking on calls the tool far more, and so takes its wrong letter far more.**
  (Sol, our vLLM; 1,620 runs.)
  - Numbers: on minus off: real call 143 against 40 of 162, +64 [+51, +75]; system note 45 against 29, +10 [+2, +19];
    pasted 47 against 41, +4 [−4, +11]; user 16 against 19 of 159–162, −2 [−8, +4]. It calls in 145 against 35 of
    162 runs, and takes the letter when it calls (143 of 145; 33 of 35). Gate 2, on / off: pasted +19 [+10, +29] / +13
    [+7, +21]; real call +78 [+69, +86] / +13 [+3, +23]. No-hint accuracy 137 against 122 of 162.
  - Status: confirmed (one model): on minus off on the real call; Gate 2 in both modes.
  - Limits: no rule was fixed for on minus off (read after the fact); one model; thinking off runs at the thinking-mode
    sampling.
  - figure: docs/paper/figures/gate2.png
- **F35. B16: most of a tool's pull is its claim to be the answer key; a user making the same claim moves the answer
  about as much, except where the model calls the tool itself.**
  - Numbers: tool minus `user_authority` ("My course answer key says the answer is (X)."): Qwen3 30B Thinking pasted
    +12 [+5, +19] (tool beyond authority), its own call +6 [−7, +19] (no difference detected); Qwen3 30B Instruct
    pasted +6 [−1, +13] (no difference detected), its own call +75 [+65, +85] (tool beyond authority); Olmo 3 7B Think
    pasted −3 [−10, +3] (no difference detected), inserted turn −14 [−21, −6] (authority moves it more). The claim
    minus the plain user hint (cross-day): +25 [+17, +35], +15 [+7, +24], +35 [+25, +45]. The share of Gate 2's gap
    the claim closes: Thinking 68% (pasted) and 80% (call); Instruct 71% and 16%; Olmo 109% and 164%. Same day (B19,
    Nov 1; 972 runs, new seeds, no reply cache): the same six readings, +10 [+4, +17], −2 [−13, +10], +4 [−1, +10],
    +75 [+65, +85], −3 [−11, +5], −14 [−22, −7].
  - Status: confirmed by the rule, per model and channel; confirmed cross-day that the claim moves all three above
    the plain hint; confirmed same-day by B19.
  - Limits: B16's tool arms were cross-day (T11; B19 checked it); "answer key" is also the tool's name for itself. A
    second wording (B24, F40): for Qwen3 30B Thinking the official solution manual moves it more than B16's wording,
    so F35 holds for B16's wording with that as its limit.
  - figure: docs/paper/figures/b16_authority.png
- **F37. B17: in gpt-oss-20b, more thinking changes neither following on the real tool call nor the bare final answer
  after a call.** (Reasoning effort low, medium, high; 810 runs each.)
  - Numbers: following on the real call 40 of 162, 46 of 162, 48 of 158: high − low +7 [−1, +16]. Bare after a call
    37 of 37, 75 of 78, 122 of 129: high − low −5 [−10, 0]. At the 16,000 cut +9 [−0.2, +18] and −5 [−11, 0]. Calls
    37, 78, 129 of 162; following when it called 31 of 37, 44 of 78, 47 of 129. Gate 2 per effort (pasted / real
    call): +24 [+16, +34] / +14 [+7, +20]; +25 [+15, +36] / +25 [+16, +35]; +26 [+16, +36] / +26 [+17, +36].
  - Status: no change detected on both primary outcomes (confirmed as no change at those widths, one model); Gate 2
    per effort reported with no decision; run after its one-day window (pre-registration §13).
  - Limits: one model at temperature 1.0 (not Track B's 0.6); keyword measures, no labels.
  - figure: docs/paper/figures/b17_effort.png
- **F40. B24: the pull grows with the claimed source's authority: the official solution manual moves all three models
  more than a classmate, and as much as or more than every tool channel but Instruct's own call.**
  - Numbers: following, classmate / manual: Qwen3 30B Thinking 12 / 78 of 162, Instruct 9 / 28 of 162, Olmo 3 7B
    Think 27 of 160 / 78 of 159. Manual − classmate (same day): +41 [+31, +51], +12 [+4, +20], +32 [+23, +41] (the
    manual moves it more, all three). Manual − B16's answer key (cross-day): Thinking +21 [+14, +29] (the manual
    higher); Instruct +2 [−2, +6], Olmo +6 [−1, +14] (no difference detected). B19's tools − manual (cross-day):
    Thinking pasted −10 [−18, −4], own call −23 [−35, −11]; Instruct pasted +2 [−2, +8], own call +73 [+62, +84]; Olmo
    pasted −9 [−17, −2], inserted turn −21 [−30, −11]. Classmate − Track B's plain hint (cross-day): +6 [+1, +11],
    +5 [+1, +9], +9 [+3, +16] (all above 0; at the 16,000 cut only just for Thinking, +4.5 [+0.03, +9.8], and Olmo,
    +5.0 [+0.09, +10.7]). Every reading the same at the 16,000 cut. Above Track B's per-letter no-hint baseline,
    classmate / manual (no decision): Thinking +6 [+2, +12] / +47 [+36, +58]; Instruct +4 [+0, +10] / +16 [+7, +26];
    Olmo +14 [+7, +22] / +47 [+36, +57].
  - Status: confirmed by the rule as stated, same day: the gradient (the manual over the classmate) in all three;
    confirmed, cross-day: (a) the manual higher for Thinking, no difference detected for the other two; the classmate
    above the plain hint in all three (at the cut, only just in two); authority over every tool channel for Thinking
    and Olmo, and Instruct's own call beyond it.
  - Limits: three of the five readings a model are cross-day (against B16, Oct 31, other seeds; Track B, Oct 27–28;
    B19, Nov 1, the same repeats); one sentence a level ("official" and "solution manual" not separated), all in the
    user's own turn; 54 questions ("no difference detected" is not a finding of no difference; Olmo's 16,000 cut
    leaves 28–45 questions); fifteen readings, not corrected for multiplicity; mentions are keyword counts.
  - figure: waiting: slide 7's `docs/paper/figures/b16_authority.png` takes B24's two arms beside B16's (Arsha, from
    Nov 6; PLAN's map, WAITING.md "Additions")

**Waiting:**

- **B20 (waiting): three new open-weight families on Sol.** Gemma 4 26B-A4B, Nemotron 3 Nano 30B-A3B and Granite 4.2
  8B, thinking on and off, with Track B's design and B16's authority arm. Pre-registered Nov 3
  ([log](../../archive/sessions/2026-11-03/2026-11-03_1219_B_b20-prereg.md)). Runs by Nov 15; read Nov 17 (Arsha).
  - Amendments of Nov 4 (the B20 log's §15, `2361152`, before any rerun): Gemma 4's tool channel is the inserted tool
    turn (`tool_injected`), labelled, because its smoke never called the tool (0 of 2); Granite 4.2 8B runs with
    thinking on only, because with thinking off it still wrote a closed think block in 6 of 6 smoke runs. Nemotron's
    smoke failed the tool path only, so its tool channel is the inserted tool turn too (§16, `063bc78`). The design is
    4,860 runs.
  - figure: waiting (WAITING.md, slide 2: B20's rows go into docs/paper/figures/gate2.png if read by Nov 17)

## 5. Level 1, inside the model (Ritik)

- The readout at 15/19/23; set A; Qwen3-8B; the heads; inside the fixed model (A18).
- Figure: `docs/paper/figures/readout_by_layer.png` (slide 3: `docs/paper/figures/readout_by_layer_slide.png`, with set
  A beside Test 2).

**Results** (Olmo 3 7B Think unless noted; Test 2 = the 30 MMLU-Pro questions; forced answers after each sentence):

- **F9. Step 8: a rule set in advance failed on 4 positions; the weights still match.**
  - Numbers: (a) no top-token mismatch outside near-ties in the first 2,047 tokens: fails, 4 positions, gaps
    0.113–0.140; (b) mean difference at least 10× below the Instruct control's: holds, 26–27× (Step 1 text) and 10.4×
    (canary) in bf16, 32× and 12× in fp32; (c) the control fails (a): holds, 277 / 280 first-part mismatches. The Sol
    weights have d97e442's sha256. Local forced answers match Voyager's in 21 of 21 and 199 of 199.
  - Status: confirmed (the rule fails (a), holds (b) and (c); the Sol weights are d97e442). "Voyager serves the same
    weights" is tentative, and nothing depends on it.
  - Limits: "the same weights" is a judgment, not the rule's verdict; so Gate 3 runs every system on the same Sol stack.
  - figure: none
- **F4. Known answers are overridden, mostly late in the reasoning, on a few questions.**
  - Numbers: on 11 of 20 sure questions, 43 of 110 hinted runs [30, 48%] ended on the hint letter; 26 of the 43 [46,
    74%] took over at or after half the reasoning; the 43 fall on 9 of the 11 questions, and the top 3 hold 23 of 43
    [39, 67%]. Unsure questions: 62 of 89 [59, 78%].
  - Status: confirmed, but on 9 questions.
  - Limits: concentrated on a few questions.
  - figure: none
- **F5. The hint is the starting answer, and the lead swings many times before it settles.**
  - Numbers: before any reasoning the hint letter leads in 198 of 199 hinted runs [97, 100%]. In resisted runs it still
    leads at or after half the reasoning, then loses for good, in 57 of 94 [51, 70%]. After the first fifth it took
    the lead 1,294 times; 46 held to the end. Just before a lead, the own answer leads 67% vs 68%: −1 point [−16, +19].
  - Status: confirmed, as forced-answer readings.
  - Limits: a forced answer is off-distribution for a thinking model, most of all before any reasoning.
  - figure: none in docs/paper (FINDINGS' figures: `cot-disclosure/results/summaries/trackA/figures/takeover_mean_curves.png`,
    `takeover_points.png`)
- **F6. Mentions mark the hint being in play, not the hint winning.**
  - Numbers: a mention in the takeover sentence or the 2 before: late takeovers 25 of 57 [32, 57%]; resisted runs at
    their closest approach 43 of 94 [36, 56%]; windows at the same relative position 12% [8, 17%].
  - Status: confirmed (keyword counts). The earlier claim, "a mention just before the takeover triggers it", is refuted.
  - Limits: keyword counts.
  - figure: none
- **F7. Deleting the reasoning's mentions moves the answer at the cut, not the final answer.**
  - Numbers: 19 cases on 9 questions. The forced answer goes back to the own answer in 7 of 19 [19, 59%] (control 1 of
    19 [1, 25%]): deleted − control +32 points [+11, +56]. Continuations: deleted − control +2 [−5, +11]; deleted −
    unedited +7 [+0, +19].
  - Status: confirmed for the forced answer; for continuations, no effect beyond the control.
  - Limits: 19 cases; F13 revises the reading (the repetition carries the hint in some cases, not most).
  - figure: none
- **F8. The hint's pull may weaken once its last mention leaves the 4,096-token window.**
  - Numbers: log-odds of the hint letter, just outside minus just inside 4,096 tokens since the last mention: −0.68
    [−1.28, −0.26] (75 runs); minus the placebo mean −0.59 [−1.25, −0.12]. With the 50 runs on split questions added:
    −0.38 [−0.88, +0.06].
  - Status: tentative.
  - Limits: 149 runs on 15 questions; information also passes forward through intermediate tokens.
  - figure: none in docs/paper (FINDINGS' figure: `cot-disclosure/results/summaries/trackA/window_reach.png`)
- **F10. Step 9: tool hints get less attention at the answer than user hints, yet move it more.**
  - Numbers: tool − user (179 vs 20 runs, 20 questions): hint − control −8.1e-3 [−1.0e-2, −6.1e-3]; per token −8.9e-4
    [−1.0e-3, −7.7e-4]. Followed − resisted (105 vs 94 runs, 16 questions): hint − control +5.6e-3 [+2.9e-3, +8.2e-3];
    per token +1.1e-4 [−3.0e-5, +2.3e-4]. Anchored the same way, temporary leads in followed and resisted runs don't
    differ: −0.7e-3 [−4.2e-3, +2.0e-3].
  - Status: confirmed (tool − user on every measure; followed − resisted on hint − control, pooled and for the
    inserted and pasted channels); tentative: per token; refuted: "resisted runs look at the hint more" (T9).
  - Limits: the channels differ in more than the source (the turn, the distance to the answer, wording and length).
  - figure: none
- **F11. Step 10: the hint's effect leaves its tokens at full-attention layers 15, 19 and 23.**
  - Numbers: at the takeover (cut (ii); 19 cuts, 9 questions) the share of the drop at 15, 19 and 23 is 0.90 [0.85,
    0.96], at the 8 full-attention layers 0.95 [0.84, 1.05]; per layer 15: 0.34 [0.27, 0.42], 19: 0.17 [0.14, 0.21],
    23: 0.39 [0.34, 0.43]. Before the first mention (cut (i)): 0.59 [0.48, 0.72]. The answer position gains 0.62
    [0.57, 0.68] of its rise at the same layers.
  - Status: confirmed on these 19 + 19 cuts (9 questions, one model); replicated on set A (F26).
  - Limits: that the readout sits in full-attention layers mostly follows from the window; only 2 cuts at (ii) have
    the hint within it (too few questions).
  - figure: docs/paper/figures/readout_by_layer.png (slide 3: docs/paper/figures/readout_by_layer_slide.png, panel a)
- **F12. Attention and patching point at the same three layers, and the same heads separate outcomes.**
  - Numbers: 8 of the 10 top answer → hint heads are in layers 15, 19 and 23. Followed − resisted over these 8 heads:
    +0.040 [+0.021, +0.057] (105 vs 94 runs, 16 questions). Three heads carry it: L19H31 +0.115 [+0.077, +0.150],
    L23H17 +0.084 [+0.060, +0.108], L15H31 +0.051 [+0.023, +0.076]. Inserted + declared: +0.004 [−0.019, +0.027].
    Tool − user in these heads: +0.010 [−0.005, +0.026].
  - Status: confirmed (the layer agreement, by two methods; followed > resisted pooled and for the inserted and pasted
    channels); not for inserted + declared.
  - Limits: the top heads' place in full-attention layers mostly follows from the window; one model.
  - figure: none
- **F13. Direct vs written: at the takeover, the prompt's letter does more than the repetition.**
  - Numbers: swapping the prompt's letter moves the forced answer off W in 13 of 21 [41, 79%]; deleting the
    reasoning's mentions brings back the own answer in 7 of 19 [19, 59%]; the written repetition alone holds W in 8 of
    21; the reasoning positions relay at most 0.26 [0.14, 0.43] (layer 17, cut (ii)). Per case (19): both paths needed
    5, the prompt 4, the writing 2, either path 4, another letter 4.
  - Status: confirmed as measured; the per-case typology is tentative.
  - Limits: different case sets (21 vs 19) on two stacks (Step 4 on Voyager, Step 10 local).
  - figure: none
- **F14. The hint takes the lead when the reasoning looks back at it, whether or not it keeps it.**
  - Numbers: rise in attention to the hint at lead onsets (hint − control): lasting +4.8e-3 [+2.7e-3, +7.1e-3] (65
    onsets, 18 questions); temporary +3.4e-3 [+2.0e-3, +5.3e-3] (1,653 onsets, 19 questions); placebo +0.05e-3
    [−0.10e-3, +0.23e-3]. Lasting vs temporary, all onsets: +1.7e-3 [−0.5e-3, +4.2e-3].
  - Status: confirmed (the rise at lasting and temporary onsets, against the placebo); tentative: lasting > temporary;
    the spike's length is descriptive.
  - Limits: an association within the same 3 sentences; which comes first isn't tested.
  - figure: none in docs/paper (FINDINGS' figure: `cot-disclosure/results/summaries/trackA/step9_onsets.png`)
- **The mechanism, in one paragraph (Steps 8–10): tentative as a whole.** Layers 15, 19 and 23 read the hint's letter
  from the prompt (0.90 [0.85, 0.96], F11); the reasoning positions relay at most 0.26 (F13); heads L19H31, L23H17 and
  L15H31 look at the hint more when the model follows it (F12); tool hints get less of this attention than user hints,
  yet move the answer more (F10, F1).
  - figure: docs/paper/figures/readout_by_layer.png
- **F26. Set A: on 16 questions not used to find it, the readout at layers 15, 19 and 23 replicates.**
  - Numbers: cut (ii), 31 cuts on 16 questions: the share at 15, 19 and 23 is 0.90 [0.76, 1.06] (Test 2: 0.90 [0.85,
    0.96]); the three largest drops are 23 (0.43 [0.30, 0.60]), 15 (0.30 [0.22, 0.39]) and 19 (0.17 [0.11, 0.23]). The
    rule needed a lower bound above 0.375 and those three largest. Swapping only the prompt's letter moves the answer
    off W in 12 of 34 [21, 52%].
  - Status: confirmed (replicates, by the pre-registered rule).
  - Limits: one model, one patching setup.
  - figure: docs/paper/figures/readout_by_layer_slide.png (slide 3, panel b; the supplement's
    `docs/paper/supplement/figures/readout_setA_vs_test2.png`, the same rows)
- **F32. Set A, Step 9: F12's three heads separate followed from resisted runs on questions not used to find them.**
  - Numbers: the mean over L19H31, L23H17 and L15H31, followed − resisted: +0.068 [+0.044, +0.088], 15 questions (56
    followed, 145 resisted runs); Test 2 +0.084 [+0.062, +0.105]. Per head: L19H31 +0.080 [+0.047, +0.109], L23H17
    +0.084 [+0.062, +0.106], L15H31 +0.040 [+0.008, +0.071]. Inserted + declared: +0.031 [+0.008, +0.051].
  - Status: confirmed on a second question set (one model).
  - Limits: one model; the heads that look most at the hint on set A aren't these.
  - figure: none
- **F36. A37: Qwen3-8B's readout replicates in a second model.**
  - Numbers: three layers chosen on the puzzles (21, 22, 29; 0.74 [0.69, 0.79] there) hold 0.70 [0.60, 0.83] of the
    drop on MMLU-Pro (30 cuts, 14 questions) and are its own top three (Olmo: 0.90). Swapping only the prompt's letter
    moves the answer off W in 54 of 63 (puzzles) and 30 of 30 (MMLU-Pro).
  - Status: confirmed by the rule as stated (replicates).
  - Limits: one replication (14 questions, late takeovers only); patching only, no heads; the tool's own call only.
  - figure: docs/paper/figures/readout_qwen8b.png
- A18 (inside the fixed model, F39) is in §7.

## 6. Level 2, in the words (Ritik, Arsha)

- Private vs final (F3; with L3's labels if they stand); the bare answer after a call and its good-lookup control; the
  instruction (F25).
- Figure: `docs/paper/figures/bare_after_call.png`.

**Results** (mentions are keyword counts; bare = 30 characters or fewer, a length count):

- **F3. The private reasoning mentions the hint; the final answer almost never does.**
  - Numbers: Test 1 (24 puzzles, user hint; Olmo 3 7B Think, Olmo 3 32B Think, Qwen3 30B Thinking; 216 hinted runs):
    private 208 of 216 [93, 98%] vs final 8 of 216 [2, 7%]. Test 2, when the tool hint won: private 16 of 17 [73,
    99%], final 6 of 17 [17, 59%]. Pinned format, final answer: pasted 27 of 60, inserted 12 of 60, inserted +
    declared 17 of 60, user 0 of 20.
  - Status: confirmed as keyword counts. The hand labels (L3) don't stand yet (below).
  - Limits: the private keyword also fires with no hint (22 of 72 Olmo 3 7B Think no-hint runs), so 208 is an upper
    bound.
  - figure: waiting (WAITING.md, slide 5: L3's kappa in the caption). PLAN's map lists
    `docs/paper/figures/cue_experiments_slide.png` for slide 5 and flags it: it plots C16–C18 (F31, F33, F34), not F3.
- **F15 (the words). After a tool call, Qwen3 30B Thinking's final answer is a bare letter, whether the tool was right
  or wrong.**
  - Numbers: after its own call the reply is a bare "Answer: (X)" in 51 of 54 [85, 98%] (median 11 characters); with
    the same hint pasted, 0 of 59 [0, 6%]. The final answer names the hint in 3 of 54 real-call runs [2, 15%] vs 54 of
    59 pasted [82, 96%]: −86 points [−95, −75]; the private reasoning names it in 54 of 54. C4's control (the call
    forced): bare after a good lookup 80 of 84 [88, 98%], after a bad one 71 of 75 [87, 98%], with no tool 2 of 159
    [0, 4%]; good − bad +1 [−7, +9].
  - Status: confirmed (the bare letter after a call, right or wrong); confirmed as keyword counts (the naming
    contrast). Tentative: how much is the declared tool and how much the call.
  - Limits: on the puzzles, runs without a call are bare too (52 of 68); in C4 the call is forced, in Track B it is
    the model's choice.
  - figure: docs/paper/figures/bare_after_call.png
- **F16 (the words). Qwen3 30B Instruct: after a call, the final answer rarely names the tool.**
  - Numbers: bare after the call in 111 of 147 [68, 82%] (72 of 72 on the puzzles, 39 of 75 on MMLU-Pro). It names the
    hint in 30 of 147 [15, 28%] vs 29 of 35 [67, 92%] pasted: −62 points [−83, −39]. A reply with text names the tool
    in 30 of 36.
  - Status: confirmed (the bare reply, a length count); confirmed as keyword counts (the mentions).
  - Limits: it called every time, so Track B has no run without a call to compare.
  - figure: docs/paper/figures/bare_after_call.png
- **F17 (the words). Olmo 3 7B Think's final answer goes bare whenever the system turn changes.**
  - Numbers: bare final answers: no hint 19 of 162 [8, 18%], user 24 of 162 [10, 21%], pasted 30 of 162 [13, 25%],
    inserted 115 of 162 [64, 77%], system note 85 of 162 [45, 60%]. When following, the final answer names the hint in
    11 of 46 inserted vs 33 of 64 pasted runs: −28 points [−44, −11]; the system note 10 of 34.
  - Status: confirmed (bare answers whenever the system turn changes; length counts); tentative: the inserted-vs-pasted
    naming contrast, because the system turn confounds it.
  - Limits: a format effect specific to this model; these runs are not in the labeling batch.
  - figure: none (bare_after_call.png shows the Qwen3 models)
- **F25. B15: one instruction brings the tool back into the final answer, and the model still takes the tool's wrong
  letter.**
  - Numbers: the instruction: "In your final answer, say what your answer is based on, including any tool result you
    used." With it minus Track B: Thinking names the tool after a call in 33 of 63 vs 3 of 54 (+47 [+30, +64]), bare
    30 of 63 vs 51 of 54 (−47 [−64, −30]); Instruct names it in 149 vs 35 of 162 (+70 [+59, +81]), bare 12 vs 111 of
    162 (−61 [−73, −49]). Following: Thinking real call +6 [−2, +14], pasted +6 [0, +13]; Instruct −1 [−7, +6], −2
    [−9, +4]. Correct-tool acceptance: Thinking −1 [−3, 0], Instruct 162 against 162. No-hint accuracy: −1 [−3, +2]
    and 0 [−4, +4].
  - Status: confirmed as keyword counts (naming rises, the bare letter falls, both models); no change detected in
    following (all four intervals include 0; Thinking's pasted one only just); no detectable cost.
  - Limits: the "before" is Track B's runs one to two days earlier, not an interleaved control; one wording; keyword
    counts.
  - figure: docs/paper/figures/bare_after_call.png
- **F29 (the words; the title question in one set of weights).** With thinking on, Qwen3-8B names the tool in its
  private reasoning after 141 of 145 calls and in the final answer in 0 of 143 followed runs; the final answer is bare
  after 138 of 145 calls.
  - Status: confirmed as keyword and length counts.
  - Limits: one model; the on-minus-off comparison was read after the fact.
  - figure: docs/paper/figures/bare_after_call.png
- **F37 (the words).** In gpt-oss-20b the bare answer after a call holds at every effort (37 of 37, 75 of 78, 122 of
  129), but its answers are often bare with no hint too (128, 130 and 131 of 162; 79% to 81%). The final answer names
  the tool on the real call in 0 of 162, 0 of 162 and 4 of 158 (reported per effort, no decision). Its rule's bullet
  is in §4.
  - figure: docs/paper/figures/b17_effort.png
- **F35 (the words), descriptive, not pre-registered.** With the user's authority claim the final answer names it in
  132 and 135 of 162 (Thinking, Instruct) and is never bare; after the model's own call it names the tool in 4 and 35
  of 162 and is bare in 108 and 111. Olmo: 71 of 161 with the claim, 22 of 157 after the inserted turn.
  - figure: docs/paper/figures/b16_authority.png
- **F40 (the words), reported per arm, no decision (keyword counts).** The final answer names the claimed source,
  classmate / manual: Thinking 116 / 141 of 162, Instruct 113 / 145 of 162, Olmo 34 of 160 / 76 of 159. Qwen3's final
  answer is never bare with a user's claim (0 of 162 in each arm), as F35 found for B16's wording; Olmo's is bare in 16
  and 19 of 162.
  - figure: waiting (slide 7, as F40 in §4)
- **F24 (the words), reported with no decision.** On C15's 100 fresh items the solver's final answer after a lookup is
  bare in 50 of 55 (bad) and 43 of 45 (good), against 0 of 100 without the tool; good − bad +5 [−5, +15].

**Waiting:**

- **L3 (waiting): Gate 2's hand labels, which F3 rests on.** Read Nov 3 (101 rows; Ritik and AI rater 1, ChatGPT 5
  Astra High): Cohen's kappa on
  the private reasoning 0.63 over 58 rows (tool 0.29, user 0.85), on the final answer 0.54 over 101 rows (tool 0.59,
  user 0.43): under 0.6 in four of six cells, human-vs-AI agreement. Next: the LLM-judge protocol (pre-registered
  Nov 4): Ritik's labels are the final labels, and Gate 2's label part is met if Ritik against the AI judges' majority
  has kappa 0.6 or more in every cell, else not met ([TODO](../status/TODO.md)'s L3, PLAN's Gate 2); Gate 2 is Nov 8.
  No acknowledgment claim from hand labels goes in the report before that. L5 (Track B's batch) comes after it.
  - Corrected Nov 4, 17:51: rater 2 was an AI model (ChatGPT 5 Astra High), not Shrey; see the 17:42 log. The
    settling call and the fresh batch by both raters no longer apply.
  - figure: waiting (WAITING.md, slide 5)

## 7. Fixing it (Ritik)

- Gate 3; the instruction; false disclosure in labels (L4); B1; A39 on E2.
- Figure: `docs/paper/figures/gate3_vs_base_slide.png` (slide 9; the same rows as `finetune/gate3.py`'s
  `cot-disclosure/results/summaries/trackA/gpu/eval/figures/gate3_vs_base.png`), or A39's (`a39_e2_fixes.png`,
  `a39_e2_parts.png`, drawn Nov 17; WAITING.md).

**Results** (Olmo 3 7B Think; the held-out 30 unless noted):

- **F20. Training: against base, the taught tokens' loss fell by 58% with LoRA, and by 40% without the fixed opener.**
  - Numbers: epoch 2 minus base, nats per token, 156 validation examples on 34 questions: LoRA taught −0.2740 [−0.3132,
    −0.2401] (−58%), without the opener −0.1328 [−0.1527, −0.1176] (−40%), the rest −0.0440 [−0.0475, −0.0406] (−19%).
    LoRA on 15/19/23 only: taught −0.2460 [−0.2809, −0.2156] (−52%), 85–90% of full LoRA's drop with 3.9% of its
    parameters. Tags: taught −17%, without the opener −9%, the rest −12%. lora_tags − lora: +0.0009 [+0.0004, +0.0014];
    injected − pasted: +0.0003 [−0.0008, +0.0015].
  - Status: confirmed (every version lowers the taught tokens' loss; LoRA's beyond the rest; tags don't favor the
    taught tokens; the tags prediction isn't borne out in the loss); tentative: the hint-check part, which rests on a
    keyword rule.
  - Limits: teacher-forced loss, not behavior (F28 is behavior).
  - figure: docs/paper/figures/taught_loss.png
- **F28. Gate 3: every trained version passes by the rule, none beats a one-line instruction, and by hand labels
  LoRA's false-disclosure candidates are rarely real.** (930 runs per system, six systems.)
  - Numbers: following minus base: LoRA −10 [−16, −4], tags −6 [−10, −2], LoRA + tags −7 [−13, −1], LoRA on 15/19/23
    −7 [−13, −2]; no-hint accuracy within 3 points; prompt_only −13 [−21, −6]. Each minus prompt_only (not
    pre-registered): LoRA +3 [−1, +8], tags +7 [+1, +14], LoRA + tags +6 [+1, +11], LoRA on 15/19/23 +6 [+0.4, +12].
    The tags prediction (inserted turn minus pasted block): tags −2 [−13, +9], LoRA + tags −13 [−24, −1].
    False-disclosure candidates minus base: LoRA +10 [+2, +18] (147 of 532), LoRA + tags +10 [+2, +19], prompt_only
    −9 [−14, −4]. L4 part 1 (kappa 0.93 over 294 rows, human-vs-AI agreement): `rejects_hint` in 1 (Ritik) and 2
    (AI rater 1, ChatGPT 5 Astra High) of LoRA's 147 candidates; `says_changed` in 97 and 89 (66% [58, 73] and
    61% [52, 68]). Corrected Nov 4, 17:51: rater 2 was an AI model (ChatGPT 5 Astra High), not Shrey; see the 17:42
    log.
  - Status: met by the pre-registered rule (all four pass); not shown: that any trained version beats the instruction;
    not borne out: the tags prediction. The cautionary claim: its first half stands; its second half is not supported
    for claimed disagreement, and its "worked it out independently" half can't be read from the labels.
  - Limits: 30 questions; hiding is a keyword measure the LoRA openers defeat; the label sheets weren't blind to
    LoRA's style (`guess_trained` right on 270 and 267 of 294); LoRA only; the label read as false disclosure was set
    after labeling, before counting.
  - figure: docs/paper/figures/gate3_vs_base_slide.png (slide 9; the same rows as `finetune/gate3.py`'s
    cot-disclosure/results/summaries/trackA/gpu/eval/figures/gate3_vs_base.png)
- **F27. B1 on set A: alpha 0.25 on the tool turn and 0.5 on every hint span lower the forced wrong answer by 8–9
  points within the correct-hint limit.**
  - Numbers: deployable (the inserted tool turn; 16 cuts, 12 questions), alpha 0.25: P(W) −7.6 [−12.2, −3.7], P(O)
    +7.2 [+3.2, +11.8], correct hint −4.8 [−7.8, −2.4]. Oracle (every hint span; 34 cuts, 16 questions), alpha 0.5:
    P(W) −8.6 [−12.6, −5.2], P(O) +7.4 [+4.1, +11.3], correct hint −4.3 [−7.1, −2.2]. Every lower alpha costs a correct
    hint more than 5 points (alpha 0, oracle: P(W) −20.6).
  - Status: FINDINGS gives no status word: alpha is fixed by the rule (commit `0bd2241`, before set A existed), and the
    generation it chose was read Nov 3 (F38).
  - Limits: forced answers at set A's cuts, not generation.
  - figure: none
- **F38. B1 on the held-out 30: scaling attention to the inserted tool turn cuts following but misses its acceptance
  limit; scaling every hint span shows no effect.** (630 runs.)
  - Numbers: deployable (0.25), read on the inserted turn: following 26 of 60 → 16 of 60, −17 [−30, −3]; correct-hint
    acceptance 25 → 23 of 30, −7 [−20, +7]; no-hint accuracy 16 → 19 of 30, +10 [0, +23]: "ignores tools". Oracle
    (0.5), every hint channel: 61 of 120 → 50 of 120, −9 [−19, +1]: "no effect". A replication that could resolve the
    limit needs about 107 to 245 fresh questions (53 to 122 GPU-hours); 35 GPU-hours fit 70, so B1R isn't run. A38
    isn't run.
  - Status: by the rule, deployable "ignores tools", oracle "no effect"; the cut in following is confirmed; the
    acceptance miss (a point estimate on 2 of 30 runs) is tentative; underpowered at 30 questions.
  - Limits: the rule's 5-point limits sit inside the sampling noise at 30 questions (no-hint accuracy moved +10 under
    both spans, though the scaling can't touch it); alpha was chosen on forced answers.
  - figure: docs/paper/figures/readout_lora_vs_base.png (panel b)
- **F39. A18: inside the fixed model, training acts in the reasoning.**
  - Numbers: on base's tool-hint cases at the takeover (28 cases, 13 questions), R_LoRA = −0.72 logits [−1.02, −0.39]:
    LoRA's weights pull toward the hint's letter harder, not less; LoRA still answers the hint's letter in 30 of 30.
    LoRA's own cases: the share at 15/19/23 is 1.29 [1.10, 1.51], the three largest drops (9 questions; replicates).
    F12's heads, followed − resisted: base +0.078 [+0.058, +0.101], LoRA +0.085 [+0.064, +0.104] (26 questions each;
    replicates). User hints apart: R_LoRA −1.09 [−1.48, −0.67].
  - Status: confirmed by the rule: "acts in the reasoning"; secondaries a and b replicate.
  - Limits: base's cases ask what LoRA's weights do with base's reasoning, not why LoRA's own runs went elsewhere; one
    trained version; 13 questions; the forced answer is off-distribution.
  - figure: docs/paper/figures/readout_lora_vs_base.png

**Waiting:**

- **A39 (waiting): Track A's second evaluation, on Sol.** A provenance wrapper and combinations, with a powered
  replication of Gate 3, on E2's 120 fresh questions (pre-registered Nov 3,
  [log](../../archive/sessions/2026-11-03/2026-11-03_1130_A_e2-a39-prereg.md)). Runs in 1-GPU parts, up to 10 at
  once, submitted by the feeder (from Nov 4, 2:00 parts and 3:00 sweeps: the log's §14); runs by Nov 15; read Nov 17,
  after all its parts are in. Nothing of Ritik's has started on Sol since Nov 4, 12:36 (fair share 0.005; starts by
  backfill only; PLAN's calendar).
  - **The 30** (22 jobs) runs beside E2 unless a rule drops it: on Nov 6 at 07:00 if Sol delivered under 10
    GPU-hours to Ritik's jobs from Nov 4, 12:36 (the log's §16, applied by the feeder);
    otherwise if E2's and A40's lines haven't all ended by Nov 11, 09:00 (§10.2, as §19 applies it from Nov 5). The Nov 6 daily reports which branch applied.
  - **T12 (Nov 4; the log's §15):** two A39 jobs shared a node and one server six times; three parts' runs (340) came
    from another model's server, set aside unread and run again; 160 from a server of the same model and command are
    kept, labelled. No earlier result is affected (§10).
  - figure: waiting: `docs/paper/figures/a39_e2_fixes.png` and `a39_e2_parts.png` (`tools/a39_figures.py`, drawn
    only from a complete report, Nov 17; spec in WAITING.md), after slide 9's `gate3_vs_base_slide.png`
- **B1R2: not run: GPU time given to A40.** Decided Nov 4 to run (the A39 log's §13); dropped Nov 5, before any B1R2
  job was submitted (§19; Ritik's decision). B1 on the 30 (F38) stays the only result on the deployable span.
- **A40 (waiting): bias-augmented consistency training** (Chua et al., 2024), aimed at beating the instruction:
  hinted prompts trained toward the model's own no-hint reasoning, with a final answer that names the hint.
  Pre-registered Nov 5 (2026-11-05 09:18 log) before any call: on E2 against prompt_only, R1 against base, and against
  LoRA. Its targets on Voyager from Nov 5, then training and E2 on Sol; read Nov 17, partial at Nov 15, 23:59.
- **Gate 3's final statement:** Nov 20, after A39 (PLAN). L4 part 2 (LoRA minus base in labels): SHOULD, no date.

## 8. Level 3, between agents (Shrey)

- Reviewer deference by family; the citation as the cue (C16–C19).
- Figure: `docs/paper/supplement/figures/trackC_reviewers.png` (slide 11: `docs/paper/figures/trackC_reviewers_slide.png`
  and `reviewer_by_prompt_slide.png`).

**Results** ("corrects" = the reviewer's letter is right where the solver's answer after a bad lookup is wrong; paired
by item; C4's 53 items unless noted):

- **F18. C4: one reviewer stops correcting a wrong tool answer once it can see where the answer came from.**
  - Numbers: Olmo 3.1 32B Instruct corrects 59 of 73 [70, 88%] from the answer alone, 61 of 73 with the explanation,
    6 of 73 [4, 17%] with the private reasoning (−73 [−86, −58]) and 3 of 73 [1, 11%] with the tool log (−77 [−91,
    −61]). On good lookups it keeps the right answer 67 → 84 of 84 (+20 [+8, +35]); right over all 159 tool-team cases:
    128 alone, 92 and 89 with the trace, the tool itself 84. Qwen3 30B Instruct: 62, 62, 66 and 56 of 73 (+5 [−6,
    +19], −8 [−25, +9]).
  - Status: confirmed (the Olmo reviewer's drop, on 25 items and both sets; its rise on good lookups); confirmed as
    keyword counts (the reviewer naming the key). Tentative: why Olmo defers; steered vs matched.
  - Limits: one reviewer model per family and one reviewer prompt; kind and set are confounded.
  - figure: docs/paper/figures/reviewer_by_prompt.png (slide 11: `reviewer_by_prompt_slide.png` and
    `trackC_reviewers_slide.png`; the supplement's `docs/paper/supplement/figures/trackC_reviewers.png`)
- **F19. C9: telling the reviewer to check the tool doesn't restore its check.**
  - Numbers: with "The tool's answer may be wrong; check it independently.": Olmo with the private reasoning 6 → 8 of 73
    (+3 [−4, +9]), with the tool log 3 → 4 (+1 [−3, +6]); within C9, private minus answer only −71 [−83, −58], tool
    log −77 [−88, −64]. Qwen3: +4 [+0, +11] and +7 [−4, +19].
  - Status: confirmed: no restoration for the Olmo reviewer; tentative: the Qwen3 reviewer's small gain.
  - Limits: one sentence, one wording, one solver's cases.
  - figure: docs/paper/figures/reviewer_by_prompt.png (slide 11: `reviewer_by_prompt_slide.png`)
- **F21. C10: committing to its own answer first doesn't protect the reviewer's check.**
  - Numbers: Olmo with the private reasoning 19 of 73 (minus C4 +18 [+10, +26]; minus its own first answer −56 [−68,
    −44], 60 of 73 first); with the tool log 5 of 73 (minus its first −75 [−86, −62]). Qwen3 with the tool log 33 of
    73: minus C4 −32 [−44, −20], minus C9 −38 [−51, −26], minus its first −40 [−55, −23]; with the private reasoning
    67 of 73.
  - Status: confirmed (both drop their own right answers after the tool log; Qwen3 does worse than in C4 and C9;
    Olmo's partial gain with the private reasoning); tentative: why.
  - Limits: one wording of the second turn; one solver's cases.
  - figure: docs/paper/figures/reviewer_by_prompt.png (slide 11: `reviewer_by_prompt_slide.png`)
- **F22. C11: the deference follows the model family: both Olmo reviewers defer, both Qwen3 reviewers don't.**
  - Numbers: Olmo 3 7B Instruct 32 of 73 alone → 1 of 73 with either context, −42 [−58, −28] (defers); Qwen3 30B
    Thinking 66 → 67 of 73, +1 [−6, +10] and +1 [−5, +9] (doesn't). Defers: the upper bound below −20.
  - Status: confirmed per model; the family reading confirmed on four families with C13 (F30).
  - Limits: the family can't be separated from what comes with it (pretraining data, post-training recipe, chat
    template).
  - figure: docs/paper/supplement/figures/trackC_reviewers.png (supplement; slide 11:
    `docs/paper/figures/trackC_reviewers_slide.png`)
- **F30. C13: neither new reviewer family defers; across six reviewers only the two Olmo models do.**
  - Numbers: private minus answer only: Granite 4.1 30B 27 → 23 of 73, −5 [−26, +15]; Mistral Small 3.2 24B 49 → 63 of
    73, +19 [+10, +30]; with the tool log −3 [−27, +21] and +19 [+9, +31]. Both keep right answers better with the
    trace (58 → 84 and 47 → 84 of 84).
  - Status: confirmed per model; F22's family reading confirmed on four families.
  - Limits: Granite's own check is weak (27 of 73 alone) and its interval reaches −26; why Olmo defers is open.
  - figure: docs/paper/supplement/figures/trackC_reviewers.png (supplement; slide 11:
    `docs/paper/figures/trackC_reviewers_slide.png`)
- **F23. C12: redacting the tool's letter restores part of the reviewer's check, not most of it.**
  - Numbers: Olmo 3.1 32B with the private reasoning redacted 23 of 73 (minus unredacted +23 [+13, +34]; minus answer
    only −49 [−64, −34]); with the tool log redacted 24 of 73 (+29 [+16, +41]; −48 [−62, −33]): "partly". Qwen3: no
    harm (+3 [+0, +7], +11 [−1, +25]).
  - Status: confirmed (partial restoration for Olmo; no harm to Qwen3); tentative: the two-part reading; H23 (the split
    by set), tested in C15: not supported.
  - Limits: 8 steered MMLU-Pro items can't separate set from difficulty.
  - figure: none
- **F24. C15: on 100 fresh items the deference replicates, redaction again restores part of it, and H23 isn't
  supported.**
  - Numbers: on the 53 bad lookups with a wrong solver answer: Olmo 39 of 53 alone → 10 of 53 with the tool log, −55
    [−70, −38] (defers; MMLU-Pro −48 [−68, −29], puzzles −64 [−86, −36]); Qwen3 43 → 40, −6 [−15, +4] (doesn't).
    Redaction: Olmo 10 → 23 of 53, +25 [+11, +38], still −30 [−47, −13] below answer only. H23: +14 [−13, +37].
  - Status: confirmed (the deference on fresh items; the partial restoration); not supported: H23. C14's rule: §9.
  - Limits: 1 repeat; one solver.
  - figure: docs/paper/supplement/figures/trackC_reviewers.png (supplement; slide 11:
    `docs/paper/figures/trackC_reviewers_slide.png`)
- **F31. C16: when the solver's final answer names the tool, the Olmo reviewer corrects fewer wrong answers; Qwen3
  doesn't change.**
  - Numbers: told to disclose (B15's instruction), the solver names the tool after 34 of 55 bad lookups (C15: 5) and
    still takes the wrong letter in 54 of 55. Olmo 25 of 53 against a same-day control's 36: −21 [−34, −8]; Qwen3 44 vs
    44, +0 [−9, +11]. Descriptive: Olmo −41 [−59, −25] where the answer named the tool (32 items).
  - Status: confirmed that Olmo's correction rate falls; its size is unclear by the pre-registered 20-point rule;
    confirmed: no change for Qwen3.
  - Limits: one wording, one solver, 1 repeat; the solver chose when to name the tool.
  - figure: docs/paper/supplement/figures/cue_experiments.png (supplement; 16:9:
    `docs/paper/figures/cue_experiments_slide.png`)
- **F33. C17: a fixed sentence naming the tool doesn't cause the Olmo reviewer's drop.**
  - Numbers: C15's saved answers with "This answer is based on the lookup tool's result." added, minus the same with
    "This answer is based on my own step-by-step working." added: Olmo 37 vs 37 of 53, +0 [−11, +11]; Qwen3 43 vs 44,
    −2 [−8, +4]. The naming sentence minus the unchanged answers: +2 [−9, +13] and −2 [−9, +4].
  - Status: confirmed: no change from a fixed naming sentence, both reviewers.
  - Limits: one wording each.
  - figure: docs/paper/supplement/figures/cue_experiments.png (supplement; 16:9:
    `docs/paper/figures/cue_experiments_slide.png`)
- **F34. C18: removing the solver's sentences that cite the tool restores the Olmo reviewer's check.**
  - Numbers: C16's 34 answers that named the tool after a bad lookup, without their 2–4 tool sentences (median 474 →
    126 characters): Olmo 25 vs 9 of 34, +47 [+29, +65]; Qwen3 28 vs 26, +6 [−9, +21].
  - Status: confirmed (+47); H33 ("the argument is the cue") not supported; H34 (an authority claim is the cue)
    untested, C19's question.
  - Limits: one solver, 34 items, a keyword decides which sentences go.
  - figure: docs/paper/supplement/figures/cue_experiments.png (supplement; 16:9:
    `docs/paper/figures/cue_experiments_slide.png`)

**Waiting:**

- **C19 (waiting; due Nov 7, Shrey): is an authority claim the cue (H34)?** C15's 100 saved answers plus "The course
  answer key gives (X); I follow it." vs "My own careful working gives (X); I follow it."; Olmo 3.1 32B and Qwen3 30B
  Instruct; corrections on the 53 bad lookups, C11's ±20-point two-sided rule. Pre-registered Oct 31
  ([log](../../archive/sessions/2026-10-31/2026-10-31_2231_C_c19-prereg.md)). Its entry goes in
  `docs/trackC/FINDINGS_C.md` (FC1, …), merged at the check-ins (Nov 7, 12, 15, 18) and into FINDINGS by Nov 18.
  - figure: waiting (WAITING.md, "Additions": slide 11's bars come with C19)

## 9. Across agents, and the pipeline (Shrey)

- The handoff note (C25); pipeline vs model (C20); a realistic tool (C26); the checker's record.
- Figure: `docs/paper/figures/c25_hops.png`.

**Results:**

- **The checker's record (F18, F24): the check that never sees the tool held.**
  - Numbers: C4: the re-ask checker flagged 73 of 75 bad lookups [91, 99%] (in the other 2 the solver ignored the tool
    and was right); false alarms on good lookups 7 of 80 [4, 17%], at the no-tool floor of 12 of 155 [4, 13%] (good −
    floor −4 [−11, +4]); no wrong answer shipped on a bad lookup in any variant (0 of 75). C15: it flagged 53 of 55
    bad and 7 of 45 good lookups (floor 7 of 100 [3, 14%]); the pipeline caught 53 of 53 wrong solver answers.
  - Status: confirmed (F18: the checker catching 73 of 75, false alarms at the floor).
  - Limits: it works when the model, asked again without the tool, answers otherwise; the floor is 18% on the steered
    MMLU-Pro items.
  - figure: none
- **F24 (c). A cheaper check, C14's rule (a blind review against a trace-seeing one), ships wrong answers the checker
  stops.**
  - Numbers: caught 49 and 46 of 53 (the checker 53): −8 [−15, −2] (Olmo), −13 [−23, −6] (Qwen3); shipped wrong 4 and
    7 (the checker 0); false alarms 8 and 9 of 45 (the checker 7 and 8). It costs 1,050–1,206 tokens a case against
    the checker's 3,545.
  - Status: refuted as a replacement for the checker (both pre-registered claims not confirmed).
  - Limits: the rule was chosen on C4's cases.
  - figure: none

**Waiting** (Shrey's; pre-registered Oct 31, run from Nov 4 on Voyager):

- **C25 (waiting; due Nov 12): across agents, the centerpiece.** C15's solver runs → a writer's handoff note (Qwen3
  30B Instruct, at most five sentences, told to keep sources or not) → a decider that never sees the tool (Olmo 3.1 32B,
  Qwen3 30B Instruct). Does the note keep the tool as the source, and does the decider accept the wrong answer more
  when the source is gone? ([log](../../archive/sessions/2026-10-31/2026-10-31_2233_C_c25-prereg.md))
  - figure: waiting (WAITING.md, slide 12: docs/paper/figures/c25_hops.png)
- **C20 (waiting; due Nov 15): pipeline vs model.** On C15's items: a blind reviewer; the answer with a tag the system
  attaches; the solver's own disclosure; the checker
  ([log](../../archive/sessions/2026-10-31/2026-10-31_2232_C_c20-prereg.md)).
  - figure: waiting (WAITING.md, slide 12: `pipeline_vs_model.png` if there is room)
- **C26 (waiting; due Nov 15; SHOULD): a realistic tool.** A passage made from the chosen option's text, with no
  letter and no "answer key": does deference survive without the authority label?
  ([log](../../archive/sessions/2026-10-31/2026-10-31_2234_C_c26-prereg.md))
  - figure: waiting (as C20)
- Track C's figures, tables and slides 11–12 (C24, C27): Nov 18. Track C's report bullets (C28, written in
  `docs/trackC/REPORT_C.md`): Nov 20.
- Check-ins and merges of `trackC-main` (TODO_C's C29): Nov 7, 12, 15 and 18. Results freeze Nov 18: no new runs after
  it (PLAN's calendar).

## 10. Limits and threats (everyone)

- One tool format; one solver; keyword counts where labels aren't in; the 30 evaluation questions (E2 for new
  experiments); cross-day comparisons (T11); runs past a rule's window (B17, §13).
- **Power:** at 30 held-out questions the fix comparisons can't resolve their 5-point limits: B1's acceptance fall is 2
  of 30 runs (F38); a replication needs about 107 to 245 questions. E2's 120 are for A39 and A40 (B1R2 was dropped Nov 5).
- **Format:** Olmo's served and pinned formats differ in following (F2: user +25 [+0, +50]), confounded with the budget
  and the run counts.
- **Cross-day:** B16's tool arms (T11; B19's same-day rerun held, F35); B15's "before" (F25); B24's readings against
  B16, B19 and Track B are cross-day by design.
- **Run past its window:** B17 (F37, pre-registration §13), kept by a decision recorded before any result was read.
- **Labels:** one human rater and one AI rater (ChatGPT 5 Astra High), not the two human raters pre-registered, so
  every kappa so far is human-vs-AI agreement (the 17:42 log); F3 stays a keyword count (L3 under 0.6 in four of six
  cells); L4 part 1's sheets weren't blind to LoRA's style (F28).
- **Track C:** one solver, one reviewer prompt; the family can't be separated from its data, recipe and template (F22).
- **Models:** the 30B pair is two checkpoints, not one switch (F16); Qwen3-8B's thinking-off runs use thinking-mode
  sampling; gpt-oss-20b runs at temperature 1.0 (F37).
- **Multiplicity:** B24 names its fifteen readings as not corrected.
- **Sol's servers (T12):** in A39's runs of Nov 3–4, two jobs on one node shared one server six times; 340 runs from
  another model were set aside and run again, 160 from the same model and command are kept, labelled (§7). The audit
  (Nov 4, 13:49): no earlier result affected.

**Measurement traps, each found and fixed** (FINDINGS T1–T12; each would have changed a reported number; the
supplement's [`TRAPS.md`](supplement/TRAPS.md) lists them with sources; figure: none):

- **T1. Template mismatch** (Oct 21): Voyager rendered Olmo 3 7B Think with the Olmo 3 Instruct template (no
  `<think>`): 178 prompt tokens on a plain question, the Instruct template's exact count, against 215 for all 24
  revisions of the Think template. Fix: we render the Think template and send it to `/v1/completions`. Every earlier
  Voyager run of this model is in the Instruct format (F2's confound).
- **T2. Default system prompt:** declaring the tool in the system prompt changed following on the inserted tool turn,
  34 of 60 [44, 68%] vs 24 of 60 [29, 53%], +17 points [+3, +30]. Fix: every record names its system prompt; training
  uses the declared version, held-out evaluation keeps both.
- **T3. Model-ID routing** (Oct 21): Voyager's default effort served the Instruct model. The 11 Step 2b runs saved
  before the change were rerun; on the new route, max difference 0.0003 on the first 2,047 tokens, beyond them 24
  top-token mismatches, all near-ties (the Instruct model: 654). Fix: one name → (ID, effort) map; a Think model sent
  without an effort is refused.
- **T4. Parser forms:** "**Answer**: D" and "the **answer** is E" weren't read. Re-scoring every saved result changed
  1 letter: Step 4's hint arm now ends on the hint in 44 of 57 (was 43; F7).
- **T5. "expected" false matches:** plain "expected" matched 7 sentences not about the hint among those planned for
  deletion. Fix: narrowed for Step 4, Step 10 and F8. Limit: Step 3's mention counts (F6) still use the broader words.
- **T6. Identity canary:** a network error (Oct 22) was logged as a failed check. Fix: no reply is no verdict; it
  retries every 2 minutes and halts only on a real mismatch or after 30 minutes unreachable. Since then 47 of 47 checks
  with a reply passed (Oct 22–26).
- **T7. Averaging a cumulative curve by layer type:** 0.53 (full) vs 0.65 (sliding) at cut (ii) read as "sliding layers
  matter more". Fix: the per-layer drop and its share (F11): 0.95 at the full-attention layers.
- **T8. A weights check that didn't check:** Step 8's snapshot check reported `weights_same: false` without hashing,
  and "FAIL on 0 of 5" counted passes. Fix: regular files hashed; the Sol weights checked by `sha256sum` (F9).
- **T9. An anchor picked where the hint is strongest:** "resisted runs look at the hint more", −0.0076 [−0.0123,
  −0.0016]; the first time (Oct 25) +50 points, against −1 [−16, +19] with matched onsets (F5). Fix: both groups
  anchored the same way: −0.7e-3 [−4.2e-3, +2.0e-3] (F10, F14). Status of the first reading: refuted (F10).
- **T10. Ollama's context window:** its default 4,096 tokens silently dropped the question and the hint; 13 of the
  first 20 Track B rows from Ollama (qwen3:8b) passed 4,096 tokens. Fix: the context set to 33,792 and recorded per
  row; the 20 rows rerun.
- **T11. A "same-day" rerun replayed from the reply cache (B16):** 907 of 972 tool runs came back as Track B's Oct
  27–28 replies, so the drift check read +0 [+0, +0] for two models. Fix: reported as cross-day (F35); a same-day
  control sends new seeds or bypasses the cache. B19 (Nov 1): 972 new runs, B16's six readings the same.
- **T12. Two jobs on one node, one server for both (A39, Sol):** fixed ports let a second vLLM server bind before
  either listened; three A39 parts' runs (340) came from another model, 160 more from the same model and command. Fix
  (`36c639b`): each job a port of its own. The audit of the 59 vLLM jobs from Oct 27 (Nov 4, 13:49): no earlier
  result affected (Gate 3's 12 parts 465 of 465 runs each, at 476–500 tokens a second; a shared server gave about half,
  217).

## 11. Related work ([`RELATED_WORK.md`](RELATED_WORK.md)), 12. Conclusion and deployment (everyone)
