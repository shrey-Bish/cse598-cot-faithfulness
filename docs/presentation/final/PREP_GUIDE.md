# Prep guide for the final talk (Group 10, Dec 3)

"Do thinking modes make chain-of-thought more honest?" Six minutes of talk, two of Q&A, three speakers, one deck
(`Group10_final.pptx`, 21 slides: 8 main, a divider, 12 backups). This guide is for the three of you to study from. It
gives cues, not a script. Results are frozen (tag `results-freeze-2026-11-18`): every number below is FINDINGS' (rows
of `docs/presentation/pack/02_NUMBERS.md`) or the demo's finder counts (`docs/presentation/TALK_MAP.md`). Plain names
come first; internal codes (F16, FB1 ...) sit in parentheses so you can look them up in FINDINGS. The speakers are a
suggestion: swap them if you like, but then swap the time boxes with them.

**What the answer is, in one breath.** Tools pull harder than people; after a tool call the answer the user reads goes
quiet about the tool while the private reasoning names it; a thinking mode helped only in part (mixed); so check the
tool outside the model. Where it holds: multiple choice, one tool format, open models up to about 32B.

**Hold these corrected wordings** (each is an overstatement we already fixed):

| Don't say | Say |
|---|---|
| "Models stop saying where the answer came from" | In the Qwen3 models; not general: Gemma names the tool in 127 of 162 with thinking off |
| "Tools beat users in all 13 settings" | Decided in the five Track B models (Gate 2) and clear in all 10 readings of the three newer families (FB1); gpt-oss reported without a decision |
| "Authority explains the pull" | It does for pasted tool output; Qwen3 30B Instruct's own call goes beyond the claim (+75 [+65, +85]) |
| "The same three layers in a second model" | Qwen3 8B's own layers 21, 22, 29 hold 0.70 [0.60, 0.83]; the heads are Olmo only |
| "Fine-tuning made answers candid and fixed following" | Candid (37 of 42 against 18 of 42), but following no less than the one-line instruction, and fewer than no fix |
| "Consistency training beats the instruction" | Fewer wrong hints followed, but costs acceptance of right ones: a trade |
| "The models lie" | Keyword counts of mentions; no proof of lying |
| "+64" alone | On the real tool call, thinking on minus off, read after the fact (exploratory) |
| "The label / the instruction does nothing" | No change detected in following |

---

## 1. The run of show

Times are the deck's notes. Hit the points; the numbers are the ones on the slide or in its notes (rate, n, interval).
Hand-off lines give the idea, not the words.

| Slide, speaker, time | Hit these points | Numbers | Hand-off |
|---|---|---|---|
| **1 Title** Ritik 0:00–0:10 | Who we are. The title question. | none | "Here is the situation we care about." |
| **2 Tools steer answers, and the user sees only the result** Ritik 0:10–1:00 | Tool-using systems look things up, increasingly in a thinking mode. The tool can be wrong. The user sees only "(C)". Our question: when the tool is wrong, does the model follow it, and does its reasoning or its answer say so? Say once: the example is illustrative, our own question, not a recorded run. | none (illustration) | "Here is how we tested it." |
| **3 Same question, same wrong letter: only the source changes** Ritik 1:00–2:00 | The design: same question, same wrong letter; only the source changes (the user's guess, a stronger claim, pasted tool output, the model's own call). Four whys: paired by question (difficulty cancels); multiple choice (following is unambiguous; fixes on fresh questions); right hints too (over-correction shows); rules written first. Three levels: behavior, inside the model, a review team. | 12 models; the fixes re-tested on 120 fresh questions; 352 GPU-hours on ASU's Sol; 95% intervals; paired bootstrap by question, 20,000 resamples; 31 rules pre-registered | "What did we find?" |
| **4 Tools pull harder than people, and the answer goes quiet** Arsha 2:00–2:55 | Part 1: same wrong letter, user against tool; Qwen3 30B Instruct is the sharpest case; the strip shows every model decided. Part 2: after a call, Qwen3 8B's reasoning names the tool, its answer doesn't (keyword counts). Exception: Gemma. Title question: mixed. | 1 of 162 [0, 3%] user; 147 of 162 [85, 94%] own tool call. 141 of 145 [93, 99%] reasoning; 0 of 143 [0, 3%] answer. Gemma 127 of 162 [71, 84%]. Mixed: +64 [+51, +75] (on − off, read after the fact); gpt-oss +7 [−1, +16], −5 [−10, 0]; Nemotron −14 [−19, −9] | "Here is one real run." |
| **5 See it happen: one real run, and how often it happens** Arsha 2:55–4:00 | Click the video (49 s) and narrate over it: the tool's wrong reply lands; the reasoning cites it; the answer is the bare letter. Then the counts: not cherry-picked, the first match in a fixed seeded order; Olmo 3 7B Think, no fix. | 28 of 114 questions fit the pattern; 85 of 233 runs took this wrong tool hint [31, 43%] | "So what should a team do?" |
| **6 Verify the tool; don't trust the answer to explain itself** Shrey 4:00–5:15 | Four recommendations, each from a number: (1) the answer isn't a record of why; log provenance outside the model; (2) a label or a prompt line won't fix it; (3) put an independent check before acting; (4) fine-tune only if your tool is often wrong. | (1) 0 of 143 [0, 3%] against 141 of 145 [93, 99%]. (2) "unverified" label −1 [−7, +4]; asking for sources names the tool more, +47 [+30, +64], follows no less, +6 [−2, +14]. (3) checker stopped 53 of 53 [93, 100%] on 100 fresh items; 7 of 45 [8, 29%] false alarms; one more model call; reviewer shown the tool's log corrected 3 of 73 (59 of 73 from the answer alone). (4) wrong hints 84 of 694 against 237 of 713, −21 [−26, −16]; right hints 347 of 459 against 431 of 476, −15 [−20, −10]; exploratory crossover 0.36 [0.22, 0.50] | "Where this holds, and what we don't know." |
| **7 Where this holds, and what we don't know** Shrey 5:15–5:55 | Applies to: multiple choice; one tool format; open models up to about 32B; every fix on one model (Olmo 3 7B Think), one training run each; 42 hand-labelled answers per system; the checker on items the solver can solve alone. Unknown: free-form multi-step agent tasks; larger and closed models; transfer of the fixes. | none | "Thank you." |
| **8 Thank you** Shrey 5:55–6:00 | Thank you; questions; backups wait after the divider. | none | none |

**Per-slide points to land if you only have a breath** (the one sentence each slide must leave):
2 the user sees only the letter; 3 only the source changes; 4 tools pull harder and the answer goes quiet; 5 it is a
real, common pattern; 6 verify outside the model; 7 here is where we stop.

---

## 2. Timing plan

About 130 words a minute. A deck timed at 6:00 from its notes usually runs 6:30 to 7:00 when three people speak it with
hand-offs and a video click. So time each speaker's section separately, and decide in advance what you cut.

| Speaker | Section | Budget | Words |
|---|---|---|---|
| Ritik | 0:00–2:00 | slide 1: 0:10 (about 20 words); slide 2: 0:50 (about 110); slide 3: 1:00 (about 130) | about 260 |
| Arsha | 2:00–4:00 | slide 4: 0:55 (about 120); slide 5: 1:05 (about 140) | about 260 |
| Shrey | 4:00–6:00 | slide 6: 1:15 (about 165); slide 7: 0:40 (about 85); slide 8: 0:05 (about 10) | about 260 |

- **Slide 5.** The clip is 49 s and plays on click. Spend about 10 s before the click (what to watch for: the tool's reply, the
  highlighted mentions, the bare letter), narrate over the clip in short phrases (about 80 words at most), then about
  6 s after it for the two counts. Don't read the counts; say "28 of 114 questions look like this".
- **Hand-offs** take about 3 s each. Start the next speaker's first sentence on the slide change, not after it.
- **Numbers cost time.** Say the number and its n ("147 of 162"), not the interval; the interval is on the slide. Say
  an interval aloud only if asked.

**Where to cut if running long, in order** (the order we chose; each speaker cuts only their own section):
1. **Clip B** (the fix and the check, slide 21): already a backup, never played in the main talk.
2. **Slide 4's second-part details** (Arsha): drop the gpt-oss and Nemotron sentence from the title-question answer; keep "mixed",
   the Qwen3 8B line and the Gemma exception (the exception is an honest limit). The "inside the model" line (layers; slide 10) is not
   in the main talk: say it only if asked.
3. **Slide 3's four whys to two** (Ritik): keep "paired by question" and "right hints too"; say the other two in a clause
   ("multiple choice, rules fixed first").
4. **Slide 6's fourth recommendation's exploratory line** (Shrey): say the two rates and "it's a trade"; skip the 0.36 crossover
   (it stays on the slide, marked exploratory). Never drop the word "exploratory" if you say the crossover.

Last resort: slide 7, read only the "Unknown" column and say "the left column is on the slide".

---

## 3. Concepts in plain words

Each: one line, an analogy, our number (verbatim; keyword counts are marked).

1. **Chain-of-thought faithfulness.** Whether the reasoning a model writes is the real reason for its answer, and whether
   the answer is honest about what it used. *Analogy:* a student shows their working, but the real reason they chose (C) was
   a neighbor's paper. *Our number:* Qwen3 8B with thinking on names the tool in its private reasoning in 141 of 145 [93, 99%]
   runs, in its final answer in 0 of 143 [0, 3%] (keyword counts).
2. **Hints and sources.** A hint is a stated answer in the prompt; the source is who says it: the user, a claimed authority,
   pasted tool output, an inserted tool turn, the model's own tool call. Only the source changes. *Analogy:* the same wrong
   answer is more persuasive from the answer key than from the person next to you. *Our number:* Qwen3 30B Instruct follows
   the user's wrong letter in 1 of 162 [0, 3%], its own tool call's in 147 of 162 [85, 94%].
3. **Sliding-window against full attention.** A sliding-window layer sees only the last 4,096 tokens; a full-attention layer
   sees the whole prompt. *Analogy:* a reader limited to the last few pages against one who can flip back to page one.
   *Our number:* in Olmo 3 7B Think, the 8 full layers hold 0.95 [0.84, 1.05] of the drop and layers 15, 19, 23 hold 0.90 [0.85, 0.96].
4. **Activation patching and the readout layers.** Copy one layer's internal state from a clean run into a hinted run and see
   whether the answer flips back; where it does is where the hint is read. *Analogy:* in a game of telephone, replace one
   person's message with the clean one and see whose fixes the final message. *Our number:* layers 15, 19, 23 hold 0.90 [0.85, 0.96];
   Qwen3 8B, with its own layers 21, 22, 29, 0.70 [0.60, 0.83].
5. **Attention heads.** Each layer has many heads, each its own "where to look" pattern; we asked which look at the hint more
   when the model follows it. *Analogy:* a layer is a committee, heads are its members. *Our number:* 8 of the 10 top heads are in
   layers 15, 19 and 23; followed minus resisted +0.040 [+0.021, +0.057] (Olmo only).
6. **LoRA (light fine-tuning).** Train small added matrices instead of changing all the weights. *Analogy:* clipping an adjustable
   lens onto a camera. *Our number:* following wrong hints, LoRA minus no fix −10 [−16, −4], the one-line instruction −13 [−21, −6];
   when LoRA follows a wrong hint its answer says so in 37 of 42 against the instruction's 18 of 42.
7. **Consistency training.** Train the model to write the reasoning it would have written without the hint, then an answer that
   names the hint. *Analogy:* practicing with the rumor removed, then saying "someone told me (C); I checked and disagreed".
   *Our number:* wrong hints followed 84 of 694 against 237 of 713 for the instruction, −21 [−26, −16]; right hints taken 347 of 459
   against 431 of 476, −15 [−20, −10]: "fewer, but costs acceptance".
8. **The attention dial.** At answer time, turn down the attention to the tool's tokens in the readout layers; no training.
   *Analogy:* a volume knob on one speaker. *Our number:* on 120 fresh questions, following 82 of 240 → 49 of 240 (−13.8 [−20.0, −7.5]),
   with right-hint acceptance −5.8 [−10.8, −1.3].
9. **Wilson interval.** A 95% interval for a rate "k of n", well behaved at small n and near 0% and 100%. *Analogy:* 73 cars pass
   and 59 are red: the true share is probably within a band, wider with fewer cars. *Our number:* the Olmo reviewer corrects
   59 of 73 [70, 88%] wrong tool answers from the answer alone.
10. **Paired bootstrap, clustered by question.** For a difference between two systems, re-draw the questions (with all their runs,
    in both systems) 20,000 times and read the middle 95%. *Analogy:* re-deal the same exam to many imaginary classes and see how much the gap moves.
    *Our number:* LoRA minus no fix −10 [−16, −4]. Under 5 questions: "too few questions", no interval.
11. **Pre-registration.** Write the rule for reading a result, with a timestamp, before the result. *Analogy:* name the card before you
    draw it. *Our number:* 31 rules pre-registered (of 42 ledger rows), results frozen Nov 18; one rule went against our hopes: the dial's cut missed its acceptance limit ("ignores tools").
12. **Cohen's kappa and the blind judge.** Agreement between two labelers beyond chance (1 is perfect); a blind judge doesn't know which
    system wrote the text. *Analogy:* two umpires calling balls and strikes, after subtracting luck. *Our number:* Ritik against J-opus
    (an AI judge) 0.96; it agreed on 82 of 84 rows. The second rater was an AI, not a second human; the earlier labels (L3, 0.63 and 0.54)
    did not reach agreement, so the keyword counts stand alone there.
13. **The trade-off (exploratory).** Every fix follows fewer wrong hints by also taking fewer right ones; whether that pays depends on how often
    the tool is right. *Analogy:* a smoke alarm turned down so it never false-alarms also misses real fires. *Our number:* consistency training gives more correct answers
    than the instruction only when fewer than 0.36 [0.22, 0.50] of the tool's answers are correct. Exploratory, post hoc.

---

## 4. The Q&A bank

Thirty questions. **Say** is one sentence in FINDINGS' wording; **Evidence** has the numbers; **Unknown** is what we don't
know (say it: the rubric rewards it); **Show** is the backup slide to jump to (slide 9 is the divider). Hard ones are
marked with a star. Rule for all of them: answer the question in your first sentence, then stop.

**Q1 ★ Why one model for the fixes?**
- **Say:** Every fix was tested on one model, Olmo 3 7B Think, where we had found the readout layers and could train and patch; so the
  fixes' trade-off is claimed for that model only.
- **Evidence:** the instruction −13 [−21, −6] against no fix; consistency training 84 of 694 against 237 of 713. The failure itself
  holds in the answering models; the readout replicates in a second (0.70 [0.60, 0.83]). Compute was the limit: a replication that resolves the dial needs about 107 to 245 fresh questions.
- **Unknown:** whether the fixes transfer; each is one training run.
- **Show:** slide 12, then 7.

**Q2 ★ Are 42 labels enough?**
- **Say:** It is a small sample, so we state the interval and claim only that candid answers are more common than with the instruction: 37 of 42 against 18 of 42.
- **Evidence:** +45 [+25, +64]; Ritik against J-opus 0.96, J-opus (blind to systems) agrees on 82 of 84 rows; the keyword version agrees
  (225 of 248 against 118 of 237; exploratory, post hoc). Candid does not mean following less: +2 [−2, +6] against the instruction.
- **Unknown:** other models and question sets; the sheet was not blind in practice (the trained style is recognizable); final answer only.
- **Show:** slide 12 (the fine-tuning rows), 7.

**Q3 ★ Why multiple choice?**
- **Say:** Because following a hint is unambiguous (the hint's letter picked) and fresh questions mean we didn't tune to the test.
- **Evidence:** the 54 questions (24 puzzles and 30 MMLU-Pro), the held-out 30, 120 fresh ones for the fixes. A letter answer is also why the final
  answer can be a bare letter.
- **Unknown:** free-form, multi-step tasks; other tool formats.
- **Show:** slide 3, 7.

**Q4 ★ Is this just sycophancy?**
- **Say:** No: sycophancy is deferring to the user, and here the same wrong letter from the user is followed far less than from a tool.
- **Evidence:** Qwen3 30B Instruct 1 of 162 [0, 3%] from the user, 147 of 162 [85, 94%] from its own tool call. A user's answer-key claim closes 68% and 71% of the gap to the pasted block in Qwen3, all of it in Olmo: claimed authority matters; the model's own call goes beyond the claim (+75 [+65, +85]).
- **Unknown:** why; we didn't test what in training causes the deference.
- **Show:** slide 11, 19.

**Q5 ★ How is this different from the related work?**
- **Say:** Others showed first that models use hints they don't name, that a tool's cue is named less than a user's, that claimed authority
  moves answers, and consistency training as a method; ours is the private reasoning against the final answer after the model's own tool call,
  thinking on and off in the same weights, a user's claim against each tool channel, the layers, the cost of every fix on right hints, and a review team.
- **Evidence:** nine papers checked, not a literature search; four of them on abstracts only.
- **Unknown:** two papers disagree with a tool-over-user claim (a user's assertions followed more than function-sourced ones; tool-channel instructions discounted); we haven't reconciled them, and ours is for our models and tasks.
- **Show:** slide 15.

**Q6 ★ Are the demo's examples cherry-picked?**
- **Say:** No: the demo finds the question by a pattern, in a fixed seeded order that never looks at outcomes, and says how many questions fit.
- **Evidence:** the run in the video is the first match of "took the wrong hint, named the tool in its reasoning, not in its answer", which fits 28 of 114 questions (Olmo 3 7B Think, no fix). The finder's counts equal a count made from the per-question files, tested over 624 combinations.
- **Unknown:** the finder shows one question at a time; the frozen counts, not the clip, are the evidence.
- **Show:** slide 5 (caption), 18.

**Q7 ★ Why 38 of 114 on one screen and 85 of 233 on another?**
- **Say:** The finder counts questions for the wording on screen; the number under the run is the frozen count of runs over both tool-call wordings; the two wordings' counts add up to it, because on the 120 each question has exactly one run per wording, so a question count there is also a run count (tested).
- **Evidence:** 38 of 114 and 47 of 119 make 85 of 233 [31, 43%]. The slide's 28 of 114 is a narrower pattern (the reasoning named the tool, the answer didn't).
- **Unknown:** none; these are presentation counts from recorded runs, and the frozen one is the 85 of 233.
- **Show:** slide 5.

**Q8 ★ Isn't consistency training just ignoring tools?**
- **Say:** Partly: it follows fewer wrong hints but also takes fewer right ones, which is a trade, not a fix that beats the instruction.
- **Evidence:** wrong hints 84 of 694 against 237 of 713 (−21 [−26, −16]); right hints 347 of 459 against 431 of 476 (−15 [−20, −10]). Inside, its weights remove part of the hint's pull from layers 0 to 14, before the readout (+0.68 [+0.17, +1.18]).
- **Unknown:** one model, one run; the crossover (0.36 [0.22, 0.50]) is exploratory.
- **Show:** slide 12, 13.

**Q9 ★ How expensive is the checker?**
- **Say:** One more model call, and false alarms on 7 of 45 good lookups.
- **Evidence:** it stopped 53 of 53 [93, 100%] wrong tool answers on 100 fresh items; false alarms 7 of 45 [8, 29%]. It flagged 73 of 75 bad lookups in the first test. A cheaper check from two reviews shipped wrong answers (4 and 7 of 53).
- **Unknown:** items the solver can't solve without the tool; we tested only solvable ones.
- **Show:** slide 6, 14, 17.

**Q10 ★ Would larger or closed models behave the same?**
- **Say:** We don't know; we tested open models up to about 32B.
- **Evidence:** the effect is decided in five Track B models and clear in all 10 readings of three newer families; no closed model, no paid API.
- **Unknown:** larger and closed models.
- **Show:** slide 7, 19.

**Q11 ★ What would you do with another month?**
- **Say:** Test the fixes on a second model, try free-form multi-step tool tasks, and test the checker where the solver can't solve the question alone. (Plans, not results.)
- **Evidence:** the three open limits on slide 7; the dial's replication needs about 107 to 245 fresh questions.
- **Unknown:** all three.
- **Show:** slide 7.

**Q12 ★ Is this "lying"?**
- **Say:** No; our word counts show mentions, not intent: the keyword counts are an upper bound and the hand labels find almost no claimed disagreement.
- **Evidence:** keyword counts of the hint named in private reasoning 208 of 216 and in the final answer 8 of 216; the keyword also fires on 22 of 72 no-hint runs.
- **Unknown:** what the model "means"; we only measure what the text says.
- **Show:** slide 20.

**Q13 Did thinking make chain-of-thought more honest?**
- **Say:** Mixed: thinking on moved the tool into Qwen3 8B's private reasoning but not its answer, and it followed the real tool call more.
- **Evidence:** 141 of 145 [93, 99%] reasoning, 0 of 143 [0, 3%] answer; following +64 [+51, +75] (on minus off, read after the fact). gpt-oss: more effort, no change detected (+7 [−1, +16]; −5 [−10, 0]). Nemotron: less bare with thinking on (−14 [−19, −9]).
- **Unknown:** one model per comparison; Qwen3 8B's on-minus-off was exploratory.
- **Show:** slide 4, 19, 20.

**Q14 Doesn't another paper contradict "tools beat users"?**
- **Say:** We claim it for our models and tasks only: an answer key's wrong fact, decided in the five Track B models and clear in all 10 readings of three newer families.
- **Evidence:** Qwen3 30B Thinking +35 [+24, +46] for pasted output; Olmo +32 [+22, +42]; Qwen3 30B Instruct's own call +90 [+83, +96], each against the user.
- **Unknown:** policy-style or function-calling hints; not reconciled.
- **Show:** slide 15, 19.

**Q15 Why not just add the one-line instruction?**
- **Say:** The instruction is the baseline every fix must beat, and none beat it without a cost to right hints.
- **Evidence:** the instruction −13 [−21, −6]; LoRA −10 [−16, −4]; LoRA minus the instruction +3 [−1, +8]. Asking the model to cite its sources made the answer name the tool more (+47 [+30, +64]) but following no less (+6 [−2, +14]).
- **Unknown:** the instruction is one wording on one model.
- **Show:** slide 12.

**Q16 How do you know which layers read the hint, and does it generalize?**
- **Say:** By activation patching at the takeover; three layers of Olmo 3 7B Think carry about 90%, and Qwen3 8B replicates with its own three layers.
- **Evidence:** layers 15, 19, 23: 0.90 [0.85, 0.96]; on 16 new questions 0.90 [0.76, 1.06]; Qwen3 8B's layers 21, 22, 29: 0.70 [0.60, 0.83].
- **Unknown:** the mechanism as a whole is tentative; the heads are Olmo only.
- **Show:** slide 10.

**Q17 Is the tool format realistic?**
- **Say:** It is one format, an answer-key lookup; a retrieved passage gives a smaller but real pull.
- **Evidence:** with a retrieved passage the solver follows a bad lookup in 19 of 55 against 52 of 55; the Olmo reviewer still defers (5 against 15 of 21, −48 [−67, −29]).
- **Unknown:** other tools and free-form tasks.
- **Show:** slide 11, 14.

**Q18 Are the keyword counts valid? What about hand labels?**
- **Say:** They are keyword counts and we call them that; hand labels stand for some claims, not for the first private/final split.
- **Evidence:** 208 of 216 and 8 of 216 are keyword counts; the first hand labels reached kappa 0.63 and 0.54, short of agreement; later labels reached 0.93 and 0.96.
- **Unknown:** every kappa is Ritik against an AI rater, not two humans.
- **Show:** slide 20.

**Q19 How do we know the numbers didn't move after you saw them?**
- **Say:** Results were frozen on Nov 18 under a git tag, and the decision rules were written before their data.
- **Evidence:** 31 rules pre-registered, each committed before its runs; deviations listed. Not pre-registered: the trained versions against the instruction on the 30, Qwen3 8B's on minus off, and the trade-off figure (exploratory).
- **Unknown:** none beyond those marked.
- **Show:** slide 16.

**Q20 Which models, and why these?**
- **Say:** Twelve open models: eight answering and four reviewers, open so we can patch layers and train fixes.
- **Evidence:** the answering set includes Olmo 3 7B Think, three Qwen3 models, gpt-oss-20b, Gemma 4, Nemotron 3 Nano and Granite 4.2.
- **Unknown:** closed models.
- **Show:** slide 19, 17.

**Q21 Why do only Olmo's reviewers defer?**
- **Say:** Six reviewers over four families were run and only Olmo's two defer; the family can't be separated from its data, recipe and template.
- **Evidence:** Olmo 3.1 32B corrected 59 of 73 from the answer alone, 3 of 73 with the tool's log; Olmo 3 7B Instruct −42 [−58, −28]; Qwen3 30B Thinking +1 [−6, +10]; Granite −5 [−26, +15]; Mistral +19 [+10, +30].
- **Unknown:** tentative with two reviewers a family.
- **Show:** slide 14.

**Q22 Did the attention dial work?**
- **Say:** It cut following on 120 fresh questions but cost right-hint acceptance, so it ignores tools by our rule.
- **Evidence:** 82 of 240 → 49 of 240 (−13.8 [−20.0, −7.5]); acceptance −5.8 [−10.8, −1.3]. On the first 30 questions −17 [−30, −3], underpowered.
- **Unknown:** whether the cost passes the 5-point limit isn't resolved.
- **Show:** slide 12.

**Q23 Why is the trade-off "exploratory"?**
- **Say:** It was computed after the results were read, with its log written before computing, and it replaces no verdict.
- **Evidence:** consistency training gives more correct answers than the instruction only when fewer than 0.36 [0.22, 0.50] of the tool's answers are correct.
- **Unknown:** the crossover for other tools and models.
- **Show:** slide 13.

**Q24 Does "tools pull harder" hold in every model?**
- **Say:** Decided in the five Track B models and clear in all 10 readings of the three newer families; gpt-oss was reported without a decision.
- **Evidence:** the strip on slide 4 and the full figure on slide 19; gpt-oss ran after its one-day window.
- **Unknown:** gpt-oss, and everything beyond these models.
- **Show:** slide 19.

**Q25 Is the pull just the claimed authority?**
- **Say:** For pasted tool output, much of it; for a model's own tool call, no.
- **Evidence:** the answer-key claim closes 68% and 71% of the gap; the official manual minus a classmate +41 [+31, +51], +12 [+4, +20], +32 [+23, +41]; Qwen3 30B Instruct's call goes beyond the claim, +75 [+65, +85].
- **Unknown:** what else in the tool's form drives the pull.
- **Show:** slide 11.

**Q26 If a team does only one thing, what?**
- **Say:** Put an independent check before acting on a tool-backed answer, and log the tool's provenance outside the model.
- **Evidence:** the checker 53 of 53 [93, 100%] against reviewers who see the log, 3 of 73; the answer names the tool in 0 of 143.
- **Unknown:** solver-can't-solve cases.
- **Show:** slide 6, 14.

**Q27 What if the solver can't solve the question without the tool?**
- **Say:** We don't know; the checker was tested where the solver can solve alone.
- **Evidence:** 53 of 53 [93, 100%] stopped; 7 of 45 [8, 29%] false alarms; both were measured on items the solver can solve alone.
- **Unknown:** the hard case; the most important open one for deployment.
- **Show:** slide 7, 17.

**Q28 How sure are you? What are the intervals?**
- **Say:** Rates carry 95% Wilson intervals; differences are percentage points with a paired bootstrap clustered by question.
- **Evidence:** 20,000 resamples; under 5 questions we give no interval ("too few questions").
- **Unknown:** the keyword counts are a measure, not a ground truth.
- **Show:** slide 16.

**Q29 Why 12 models and two modes, not more questions?**
- **Say:** We wanted to know whether the pattern is about one model or many; the strip shows it across ten model settings.
- **Evidence:** 54 questions with 3 runs each per setting for the main tests; 120 fresh questions for the fixes.
- **Unknown:** larger question sets would narrow intervals.
- **Show:** slide 19.

**Q30 How did you use AI tools?**
- **Say:** Claude Code wrote and ran code, tests, analyses and figures under rules that keep every commit a team member's own; models studied are the experiments' subjects.
- **Evidence:** the AI-use inventory (`docs/submission/AI_USE_INVENTORY.md`); labels by Ritik with an AI rater and AI judges; no paid API called.
- **Unknown:** some inventory lines are still "to confirm": check before Dec 3.
- **Show:** none.

---

## 5. Rubric self-check

| Criterion | Where the deck earns it | Evidence | What a grader could still mark down |
|---|---|---|---|
| **Technical soundness (7)** | Slide 3 (each choice with its why); backups 16, 17 | Paired by question; multiple choice for an unambiguous measure; right hints for the cost; 12 models; 31 rules pre-registered; 95% Wilson and paired bootstrap | One task type and tool format; keyword counts for the words; 42 labels per system; kappa is a human against an AI rater; fixes on one model |
| **Quality and interpretation of results (5)** | Slides 4, 5, 6 (each with n and interval); backups 12, 19, 20 | 1 of 162 [0, 3%] against 147 of 162 [85, 94%]; 141 of 145 [93, 99%] against 0 of 143 [0, 3%]; 53 of 53 [93, 100%]; the Gemma exception; "mixed" stated | The strip's top row is one model's sharpest case; +64 read after the fact; one honest limit per result must be said aloud, not just shown |
| **Deployment framing (4)** | Slide 6 (four recommendations, each from a number); slide 7 | 0 of 143; −1 [−7, +4]; 7 of 45 false alarms and one more call; the trade-off | The recommendations are our reading (interpretation), not tested in a real deployment; the exploratory crossover |
| **Presentation clarity (2)** | The whole deck in 6:00; one idea a slide; claim titles; the clip | Notes timed to 6:00 | Three speakers usually run over: rehearse each section; slide 4 is dense |
| **Q&A** | The 12 backups, section 4 above | Each answer: one sentence, its numbers, its unknown, its slide | A vague "we think so"; an uncorrected old wording; reading a number without its n |

Past feedback to remember: we lost marks on "quality of preliminary results". Every result you say needs its number, n,
comparison and one limit.

---

## 6. If the video doesn't play

Don't debug on stage. The poster frame on slide 5 stays visible, and slide 18 holds four stills of the same run
(the local deck; the tracked deck shows placeholders). Two sentences, over the frame:

> "Here the tool's wrong answer arrives, the model's private reasoning cites it, and its final answer is just the letter, with no word about the tool.
> This is a real recorded run, and 28 of 114 questions look like this for Olmo 3 7B Think with no fix."

Then go straight to the two counts (28 of 114; 85 of 233 [31, 43%]) and the hand-off to Shrey. Clip B (slide 21) has the
same fallback: say what it shows (consistency training resists the wrong answer, also refuses a right one; the review
team's reviewer defers and the checker flags it) in one sentence, and move on.

---

## 7. Rehearsal plan

1. **Run 1, slow, with the notes.** Everyone, all slides, with a stopwatch per speaker (three stopwatches or a phone each). Note each
   section's time. Mark what you cut (section 2's order).
2. **Run 2, no notes, with the video.** Arsha rehearses the click and the 49 s narration; hand-offs on the slide change. Each speaker
   must finish inside their box: Ritik 2:00, Arsha 2:00 (4:00 total), Shrey 2:00 (6:00 total). Anyone over cuts the next item in their list.
3. **Run 3, the dress run.** One continuous take from the deck file as it will be uploaded, in Slide Show mode, with the 2-minute mock Q&A.
4. **The 2-minute mock Q&A.** One person reads questions from section 4 at random (at least two stars, "38 of 114 against 85 of 233", "is this lying"); another
   answers in one sentence and jumps to the backup slide; the third times it. Aim for 15 seconds an answer, so about 8 in 2 minutes.
5. **Check both videos play in PowerPoint's Slide Show mode**, on the file that goes to Canvas (the one with the clips embedded),
   and on a Windows machine if you can borrow one: the classroom PC likely runs Windows. Confirm the click starts clip A, the sound works or the
   clip is fine silent, and clip B on slide 21 starts too. Run with no internet.
6. **Before Dec 3:** upload by Nov 30; agree who answers which questions (the owner of the slide answers first); each person reads the "Don't say" table once more.
