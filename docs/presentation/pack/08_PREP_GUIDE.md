# 08. Prep guide for Ritik (presenting today, Nov 24)

Presentation pack, file 8. A study guide, not a script. For each concept: (a) what it is, (b) an everyday analogy,
(c) how we used it, (d) its number in our results (verbatim, with finding ID and source file), (e) one check-yourself
question with its answer. Then the demo's four moves, the fallbacks, and a rehearsal plan.

Results are frozen (tag `results-freeze-2026-11-18`, commit `7e1fdc0`). Every result number below is copied from
`docs/FINDINGS.md` (or FB1 in `docs/trackB/FINDINGS_B.md`, FC in `docs/trackC/FINDINGS_C.md`). The detailed method
facts, each with its file, are in `03_METHODS.md` of this pack. Internal codes are in parentheses; the mapping is
`docs/GLOSSARY.md`.

**The corrected story to hold in your head** (README "The five findings"; `archive/sessions/2026-11-23/2026-11-23_0910_ALL_front-door.md`,
"Ritik's five-line story against FINDINGS"):
- "Much of the pull is authority" holds for pasted tool blocks (F35). It is not general: Gemma names the tool in
  127 of 162 with thinking off (FB1).
- Qwen3-8B replicates the readout with its OWN layers 21, 22, 29 at 0.70 [0.60, 0.83] (F36), not the same three
  as Olmo's.
- Fine-tuning made answers more candid (L6, F45: 37 of 42 against 18 of 42) while following wrong hints no less than the
  instruction, and fewer than no fix (LoRA −10 [−16, −4] against base, F28).

---

## Part A. The concepts, in order

### 1. Chain-of-thought faithfulness

- **(a) What it is.** Whether the reasoning a model writes before its answer is the real reason for the answer, and
  whether the answer is honest about what it used. Our version: when a hint changes the answer, does the model say so?
- **(b) Analogy.** A student shows their working on an exam, but the real reason they chose (C) was that the
  person next to them wrote (C). Faithful working would say so.
- **(c) How we used it.** We put a wrong hint in the prompt, from different sources, and checked (by keyword counts and by
  hand labels) whether the private reasoning and the final answer mention it.
- **(d) The number.** Private reasoning names the hint in 208 of 216 [93, 98%] hinted runs, the final answer in 8 of 216 [2, 7%] (F3, `docs/labeling/RESULTS_SUMMARY.json`). Keyword counts, an upper bound on the private side. The hand
  labels did not pass Gate 2's label rule, so F3 stays a keyword count.
- **(e) Check yourself.** *Why do we say "keyword counts" out loud on that slide?* Because Ritik's labels against the AI
  judges' majority had kappa under 0.6 (private 0.472, final 0.234; F3), so no claim rests on hand labels there.

### 2. Hints, and why sources matter

- **(a) What it is.** A hint is a stated answer in the prompt (the same wrong letter every time); the source is who
  or what says it: the user, a claimed authority, a pasted tool block, an inserted tool turn, the model's own tool
  call. Only the source changes between conditions.
- **(b) Analogy.** The same wrong answer is more persuasive from the textbook's answer key than from the person
  sitting next to you.
- **(c) How we used it.** Track B's 54 test questions with three runs each, across many models; then the authority
  ladder (classmate, answer key, official manual).
- **(d) The numbers.**
  - Tool minus user, pasted block, in points: Qwen3 30B Thinking +35, Qwen3 30B Instruct +21, Olmo 3 7B Think +32 (story
    item 1; F15, F16, F17).
  - Authority: "My course answer key says…" closes 68% and 71% of the gap with the pasted block in Qwen3 and all of it
    in Olmo (F35, `docs/FINDINGS.md`, item 1). Manual moves all three models more than a classmate: +41, +12, +32 points (F40).
  - Not general: Gemma names the tool in the final answer in 127 of 162 with thinking off (FB1); "the tool's form
    adds to the claim" depends on family and channel: beyond the claim in 5 of 10 readings (FB1).
- **(e) Check yourself.** *Is "the tool's pull is authority" a general result?* No. It holds for the pasted block (F35,
  stated for B16's wording; F40 gives its limit); beyond the claim in 5 of 10 readings, the claim does the work in 1,
  no difference detected in 4 (FB1).

### 3. Sliding-window versus full attention

- **(a) What it is.** In a transformer each layer decides which earlier words to look at. A *sliding-window* layer sees
  only the last 4,096 tokens; a *full-attention* layer sees the whole prompt. Olmo 3 7B Think has 24 of 32 layers
  sliding and 8 full (layers 3, 7, 11, 15, 19, 23, 27, 31; F8; `cot-disclosure/finetune/gpu/kit.py`).
- **(b) Analogy.** Reading a long report with a window that shows only the last few pages (sliding), versus a few
  readers who can flip back to page one (full).
- **(c) How we used it.** To ask whether the readout layers (below) are forced by the architecture. Qwen3-8B, with all
  36 layers full attention, is the control (F36).
- **(d) The number.** In Olmo, the 8 full layers hold 0.95 [0.84, 1.05] of the drop and layers 15, 19, 23 hold 0.90
  [0.85, 0.96] (F11, `cot-disclosure/results/summaries/trackA/step10_handoff.json`). In Qwen3-8B, 3 of 36 layers
  is the even share 0.083 (F36).
- **(e) Check yourself.** *The window explains part of the readout; what does it not explain?* Which of the 8 full
  layers do it (15, 19, 23); layers 3, 7, 11, 27 and 31 read almost nothing (F11).

### 4. Activation patching and the readout layers

- **(a) What it is.** Copy the internal activations of one layer from a run on a clean prompt into a run on the hinted
  prompt, one layer at a time, and watch whether the answer flips back. Where it flips is where the hint is read out
  of its tokens. The "drop at a layer" is how much restoration is lost passing it; drops sum to 1.
- **(b) Analogy.** A dimmer-switch audit: with a bad rumour in a game of telephone, replace one person's message with
  the clean version; the person whose replacement fixes the final message is where the rumour is read.
- **(c) How we used it.** On followed runs with a late takeover, on sure questions; a clean twin with the hint letter
  replaced by the own answer; measure logit(wrong) minus logit(own) at the answer position (03_METHODS.md section 6).
- **(d) The numbers.**
  - Olmo, layers 15, 19, 23: 0.90 [0.85, 0.96] of the drop at the takeover (F11).
  - On 16 questions not used to find it: 0.90 [0.76, 1.06] (set A, F26).
  - Qwen3-8B, its own layers 21, 22, 29: 0.70 [0.60, 0.83] on MMLU-Pro; pre-registered: replicates; less concentrated
    than Olmo's 0.90 (F36).
- **(e) Check yourself.** *Is Qwen3-8B's readout "the same three layers"?* No. Its own layers are 21, 22, 29, chosen on
  the puzzles and then its own top three on MMLU-Pro (F36).

### 5. Attention heads

- **(a) What it is.** Inside each layer there are 32 attention heads (Olmo; `method.json`, `arch`), each a separate
  "where to look" pattern. We asked which heads look at the hint more when the model follows it.
- **(b) Analogy.** A layer is a committee; heads are its members. Three members glance at the hint more on the days the
  committee goes along with it.
- **(c) How we used it.** Step 9: attention from the answer position to the hint; top heads picked on all runs pooled, not
  by outcome; then fixed in advance and tested on new questions (F32).
- **(d) The numbers.** 8 of the 10 top heads are in layers 15, 19 and 23. Followed minus resisted, mean over 8 heads:
  +0.040 [+0.021, +0.057]; L19H31 +0.115 [+0.077, +0.150]; replicated on set A: +0.068 [+0.044, +0.088] (F12, F32).
  Tool hints get less of this attention than user hints, yet move the answer more (F10).
- **(e) Check yourself.** *Do tool hints get more attention at those heads?* No, less (F10); tool minus user in those
  heads is +0.010 [−0.005, +0.026], which includes 0 (F12). So the extra trust is in what is read, not how much is looked at.

### 6. LoRA

- **(a) What it is.** Low-rank adaptation: instead of changing all the weights, train small added matrices on the
  projections. Cheap, and the base model is untouched. Ours: rank 16, alpha 32 (`cot-disclosure/finetune/train.py`).
- **(b) Analogy.** Clipping a small adjustable lens onto a camera instead of rebuilding the camera.
- **(c) How we used it.** Fine-tuned Olmo 3 7B Think on its own replies that note the hint's source and decide for
  itself, on training wordings different from the evaluation ones. Four trained versions (LoRA, source tags only,
  LoRA + tags, LoRA on layers 15, 19, 23) all passed Gate 3's rule (F28).
- **(d) The numbers.**
  - Following wrong hints: base 249 of 530 [37, 57%], LoRA 197 of 532 [27, 48%]; LoRA minus base −10 [−16, −4]; the
    one-line instruction −13 [−21, −6] (F28, `cot-disclosure/finetune/gate3.py` output).
  - Loss: taught tokens fall 58% against base, 40% without the fixed opener (F20).
  - Candid answers: when LoRA follows a wrong hint, its answer says so in 37 of 42 runs against the instruction's 18 of 42 (+45 [+25, +64]; Ritik against J-opus kappa 0.96; F45).
  - Inside: given base's own reasoning, LoRA's weights pull toward the hint harder (−0.72 logits [−1.02, −0.39]
    removed; F39). Training acts in the reasoning.
- **(e) Check yourself.** *Did fine-tuning beat the one-line instruction on following?* No: the instruction −13 [−21, −6]; each version minus it, LoRA +3 [−1, +8] (F28). What it did do: more candid answers (F45).

### 7. Consistency training (A40)

- **(a) What it is.** Bias-augmented consistency training (Chua et al., 2024, adapted): train the model so that,
  given the hinted prompt, it writes the reasoning it would have written *without* the hint, then a final answer that
  names the hint and whether it agreed.
- **(b) Analogy.** Practising by always being asked the question with the rumour removed, then being told to say
  "someone told me (C), I checked and disagreed".
- **(c) How we used it.** Same LoRA settings as above, so A40 and LoRA differ only in the target. 979 records, 981 examples
  (`cot-disclosure/finetune/data/a40/manifest.json`; F41). Tested on E2 (120 fresh questions).
- **(d) The numbers.** Wrong hint followed in 84 of 694 runs against the instruction's 237 of 713 (−21 [−26, −16]), but
  correct hint taken in 347 of 459 against 431 of 476 (−15 [−20, −10]): "fewer, but costs acceptance" (F41). With the note
  (A42): 64 of 706, acceptance −20 [−26, −14] (F43). Inside: it acts on the readout from layers 0 to 14 (+0.68
  logits [+0.17, +1.18], F42).
- **(e) Check yourself.** *Why is it "a trade, not a fix"?* It follows fewer wrong hints by ignoring hints, correct
  ones too: 84 of 694 followed but 347 of 459 correct taken, against 237 of 713 and 431 of 476 (F41).

### 8. The attention dial (B1, B1R2)

- **(a) What it is.** At answer time, scale down the attention from layers 15, 19, 23 to the hint's tokens by a factor
  alpha. No training. Deployable version: the inserted tool turn, alpha 0.25 (chosen on set A's forced answers, F27, F38).
- **(b) Analogy.** A volume knob on one speaker: turn down the voice of the "tool" and see whether the model still
  listens to it.
- **(c) How we used it.** B1 on the 30 held-out questions, then a labelled replication on 120 fresh questions (B1R2).
- **(d) The numbers.** B1: −17 [−30, −3] on the inserted tool turn; misses its pre-registered acceptance limit ("ignores tools")
  and is underpowered at 30 questions; scaling every hint span shows no effect (−9 [−19, +1]) (F38). B1R2: following
  82 of 240 → 49 of 240 (−13.8 [−20.0, −7.5]), so the cut replicates; correct-hint acceptance 211 → 197 of 240
  ([−10.8, −1.3]), now a real cost (F38).
- **(e) Check yourself.** *What does "ignores tools" mean here?* Following falls, but correct-hint acceptance drops by
  more than 5 points; so the fix turns the tool down, including when it is right (F38).

### 9. Wilson intervals

- **(a) What it is.** A 95% interval for a rate "k of n", better behaved than the textbook one at small n or near 0% and 100%.
  FINDINGS writes it as "X of Y [lower, upper%]".
- **(b) Analogy.** Watching 73 cars pass and 59 are red: the true share of red cars on that road is probably within
  a band, wider with fewer cars.
- **(c) How we used it.** Every rate in FINDINGS.
- **(d) The number.** The Olmo reviewer corrects 59 of 73 [70, 88%] wrong tool answers from the answer alone (F18).
- **(e) Check yourself.** *Does "[70, 88%]" mean the rate in new runs will be between 70% and 88%?* Not exactly: it is
  a 95% interval for the underlying rate from these runs.

### 10. The paired bootstrap, clustered by question

- **(a) What it is.** For a difference between two systems: resample *questions* (with all their runs, in both systems),
  recompute the difference many times (20,000, seed 0) and read off the middle 95%. Paired because both systems saw the
  same questions; clustered because runs on one question are not independent.
- **(b) Analogy.** Re-dealing the same exam to a thousand imaginary classes, and seeing how much the score gap moves.
- **(c) How we used it.** Every difference in points, e.g. "LoRA −10 [−16, −4]". Rule: under 5 questions behind an
  interval, "too few questions", no interval and no direction read (FINDINGS line 197).
- **(d) The number.** LoRA minus base −10 [−16, −4] (F28); the dial's cut −13.8 [−20.0, −7.5] (F38).
- **(e) Check yourself.** *Why cluster by question?* Runs on the same question share the question's difficulty; treating
  930 runs as independent would give intervals too narrow.

### 11. Pre-registration

- **(a) What it is.** Writing the rule for reading a result (what counts as "works", "replicates", "ignores tools"),
  with its commit timestamp, before looking at the result.
- **(b) Analogy.** Naming the card you will draw before you draw it.
- **(c) How we used it.** Each experiment has a session log with its rule, committed before results; the ledger of 42
  rules (31 marked pre-registered) is in `docs/paper/supplement/PREREGISTRATIONS.md`. Deviations are listed in
  `DEVIATIONS.md`.
- **(d) A number.** F36 was "pre-registered: replicates" (0.70 [0.60, 0.83]); B1's rule gave "ignores tools" on the 30 (F38);
  A40 "doesn't beat the instruction by its rule" (F41).
- **(e) Check yourself.** *Name a result where the pre-registered rule went against our hopes.* B1: the dial cut following
  but missed its acceptance limit ("ignores tools"); and A40's rule read "fewer, but costs acceptance" (F38, F41).

### 12. Cohen's kappa and the blind judge

- **(a) What it is.** Agreement between two labellers beyond what chance gives: 1 is perfect, 0 is chance. A blind judge
  sees the text without knowing which system wrote it.
- **(b) Analogy.** Two umpires calling balls and strikes: how often they agree after subtracting luck.
- **(c) How we used it.** Ritik's hand labels are the labels; AI judges check them (Nov 4 protocol). The second
  rater was an AI (ChatGPT 5 Astra High), not a second human (corrected Nov 4).
- **(d) The numbers.** L4 part 1: kappa 0.93 (F28). L3: private 0.63, final 0.54 over the labelled rows; against the AI judges'
  majority private 0.472 and final 0.234 (F3), so Gate 2's label part: not met. L6: Ritik against J-opus kappa 0.96
  (F45); the J-opus agreed on 82 of 84 rows.
- **(e) Check yourself.** *Why is L6's "37 of 42 against 18 of 42" credible, and what are its limits?* Ritik's labels agree
  with a blind AI judge (0.96); limits: LoRA's trained opener names the hint, one model, E2 only, 42 rows a system,
  final answer only, and the sheet was not blind in practice (the style is recognisable) (F45).

### 13. The trade-off, and why it is exploratory

- **(a) What it is.** Every fix we trained, prompted or applied at inference follows fewer wrong hints by also taking
  fewer correct ones. Whether that is worth it depends on how often the tool is right.
- **(b) Analogy.** A smoke alarm turned down so it never false-alarms also misses real fires.
- **(c) How we used it.** The fixes on E2; a curve of correct answers against the share of tool answers that are right.
- **(d) The number.** From FINDINGS story item 7 (scorecard): "A40 gives more correct answers than the instruction only
  when fewer than 0.36 [0.22, 0.50] of the tool's answers are correct." *Exploratory (post hoc).* Not pre-registered;
  figure `tradeoff_e2.png` (not in the deck, in `docs/paper/figures/`).
- **(e) Check yourself.** *Why do we call it exploratory?* The threshold was computed after the results were read; no rule
  for it was fixed in advance (FINDINGS item 7).
  *Our reading (interpretation):* without a way to verify the tool, resisting wrong hints and relying on right ones
  trade off; independent verification does not (checker stopped all 53 wrong answers, false alarms on 7 of 45 good
  lookups; F24).

---

## Part B. The demo's four moves

Source: `docs/presentation/TALK_MAP.md`, section "Show me, the case finder (Nov 23–24)". **Every finder number below
(38 of 114, 32 of the 38, 26 of 112, 10, 16 of 118, 47 of 119, 85 of 233) is a presentation count from recorded runs,
not a FINDINGS number. Source for all of them: TALK_MAP, Show me.** Where each count is read from: each run's own outcome
fields; the finder counts questions; the number under a run is the frozen count of runs.

Setup: the local build `cot-disclosure/results/demo/demo.html`, key **1** (the scratch pad; map 2, bench 3, sheets 4).
The pad opens on Show me → "No fix took the wrong hint", for the 120 and a tool call's reply (a study guide).

| Move | What to press / point at | The number on screen (TALK_MAP, Show me) |
|---|---|---|
| 1. The problem (as it opens) | Point at the **finder line**: it says how many questions this happens on. Point at the **slip** (the tool's reply with the hint's letter), then the private reasoning streaming with the **highlighted mentions** of the hint (found by the analysis's own keyword matcher). Point at the three **red-pen checks** under the answer: "took the hint?", "reasoning says so?", "answer says so?". On the first question (mmlupro-1817) No fix took the hint and neither its reasoning nor its answer names the study guide | The finder line: 38 of 114 questions with an answer. Common case: 32 of the 38 hid it in the answer ("took it, hid it") |
| 2. The fix | Click **Consistency-trained**. Point at the **red verdict line** across the split: on mmlupro-1817 it took the hint too. Then Show me → "the fix held" (**F** or next cycles the questions) | No fix took it and Consistency-trained didn't, on 26 of 112 questions (both took it on 10) |
| 3. The cost | Show me → "the cost" (the hint turns right): point at the pane where Consistency-trained **refused a right hint** that No fix accepted | Consistency-trained refused a right hint that No fix accepted, on 16 of 118 |
| 4. Downstream | **Dataset** → the review team's items, then **Send to the review team**; point at the solver, reviewer, checker flow and the verdict | Not a finder number. Frozen numbers behind it: F18, F24 (59 of 73 corrected from the answer alone, 6 of 73 and 3 of 73 with the reasoning or the tool log) |

**The count under each run.** Each pane shows its version's frozen count (from the frozen data, every count with its
path), e.g. the run's version row (13 versions; untested ones greyed). If asked why 38 of 114 differs from "85 of 233"
under the run: the finder counts *questions* for the wording on screen; the number under the run is the frozen count of
*runs* over both tool-call wordings; the two wordings' finder counts add up to it (38 of 114 and 47 of 119) (TALK_MAP,
Show me).

**Keys:** on the pad **F** next question Show me found, **N** next run, **Enter** replay, **Esc** finish the run; anywhere
**1** pad, **2** map, **3** bench, **4** sheets, **← →** step, **T** theme, **R** replay the page (TALK_MAP, "Keys").
Do not use L (hand-labelled answers) in the talk; keep it for Q&A about candour (sheet 9).

---

## Part C. Fallbacks if something fails

TALK_MAP's rule for every failure: **press R once; if the page is not right within 5 seconds, say the row's point from
whatever is on screen and switch to the named slide. Never debug on stage.**

- **The local server** (the pad's full recorded runs load from it; it serves on this machine only). From
  `cot-disclosure/`: `../.venv/bin/python tools/demo_template/serve.py` (TALK_MAP writes the same as
  `python3 cot-disclosure/tools/demo_template/serve.py`; `docs/demo/README.md` gives the `../.venv/bin/python` form).
- **Double-clicked local build** (no server): the drawn questions only (TALK_MAP, "The scratch pad"; `docs/demo/README.md`).
  The first drawn question of each test is the first shown; **N** gives the next (`cot-disclosure/tools/demo_template/draw.json`).
- **If a run's text says "outcome only: this run's text is on Sol":** the Sol copy is missing from the build; the frozen
  panel and red marks still work; go on (TALK_MAP, "Setup"). (The commit log says the full Sol copy is in the local
  build, so this should not appear.)
- **The tracked offline page** `docs/demo/index.html`: the map, the bench's frozen results and the sheets; it has no
  Enter, N, M, C and no pad (parts keyed 1 to 3, `docs/demo/README.md`).
- **Live mode** (your own question on Qwen3-8B; never counted) needs `ollama serve` running on this Mac
  (`cot-disclosure/tools/demo_template/live.py`; Ollama endpoint `http://localhost:11434/api/chat` in
  `cot-disclosure/configs/models.yaml`). If it is not running, skip live mode.
- **TALK_MAP's fallback slides:** each moment names a slide to switch to (e.g. slide 9 `gate3_vs_base_slide.png` and
  `a40_e2_fixes.png` for the fixes; slide 10 `readout_lora_vs_base.png` and `b1r2_vs_b1.png`; slide 11
  `trackC_reviewers_slide.png`). Deck: `docs/presentation/deck.pptx`. Recorded screens for Q&A only:
  `cot-disclosure/results/demo/screens_answer_sheet/`.
- **Screenshots** of the demo are being made by another helper in `docs/presentation/pack/demo_shots/`: check what is
  there before relying on it.
- **If the whole demo fails:** keep talking from slide 1 on, same order and times (TALK_MAP).
- **Before the talk:** run each live moment once with the same keys; check the clock and the theme (**T** once).

---

## Part D. Rehearsal plan (facts and structure, not a script)

**The structure** ([05_SLIDE_OUTLINE](05_SLIDE_OUTLINE.md)): 13 slides in 12:00 (11:25 on the slides, 0:35 of slack),
plus six backups (B1–B6). The existing `deck.pptx` follows TALK_MAP's earlier 14-slide order; 05 reuses its points
and figures in the requested order.

| Slide | Time |
|---|---|
| S1 Title | 0:15 |
| S2 Where did that answer come from? | 0:45 |
| S3 Setup | 0:50 |
| S4 1. A tool's hint pulls harder | 1:05 |
| S5 2. The reasoning names the tool; the answer doesn't | 1:05 |
| S6 3. Inside the model: three layers | 1:00 |
| S7 4. Reviewers defer; the checker holds | 1:00 |
| S8 5. Every fix is a trade | 1:15 |
| S9 The demo: four moves | 2:00 |
| S10 What's new and what isn't | 0:45 |
| S11 Limits | 0:40 |
| S12 Next steps | 0:30 |
| S13 Team | 0:15 |

**Suggested run-throughs.**
1. *Run 1, untimed, with the demo:* every key press and every fallback switch, once (TALK_MAP "Before the talk").
2. *Run 2, timed, slides only* (deck, no demo): find where you run over; compare with the table above.
3. *Run 3, timed with the demo:* the demo's four moves in about 2 minutes; if Show me takes longer, shorten move 4.
4. *Run 4, a failure drill:* kill the server on purpose; switch to the slide fallback in under 5 seconds; then go on.
5. *Run 5, Q&A drill:* answer the "check yourself" questions above aloud; `docs/presentation/QA_FACTS.md` has the corrected facts.
6. *Last pass:* the numbers you will say aloud, each with its finding ID (the deck's evidence footer column in TALK_MAP).

**What to cut first if short on time** (05_SLIDE_OUTLINE's order; your call):
1. The demo's move 3 (say the cost in one sentence on S8).
2. S6's second figure and the Qwen3-8B number (keep 0.90 [0.85, 0.96], F11).
3. S3 to 0:30 (one sentence and the model count).
4. S10 to 0:30 (two lines: not new / ours).
5. In the demo: stop after move 2; say moves 3 and 4 from the slide.
Do not cut: the corrected authority caveat (F35 not general, FB1), the trade-off caveat (exploratory, post hoc), or
the limits slide.

**Facts to keep ready for questions.**
- Pre-registration, with the freeze: Nov 18, tag `results-freeze-2026-11-18` on `7e1fdc0`.
- Labels: one human and one AI rater, not two humans (L3, L4; Nov 4 correction).
- Compute: 352.47 GPU-hours, 271 GPU jobs on Ritik's Sol account since Oct 1
  (`cot-disclosure/results/demo/sol/sacct.json`, via `method.json`).
- The 12 models, 8 answering and 4 reviewers (`method.json`, `models`).
