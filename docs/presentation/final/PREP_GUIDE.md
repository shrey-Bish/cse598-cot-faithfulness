# Prep guide for the final talk (Group 10, Dec 3)

"Do thinking modes make chain-of-thought more honest?" Six minutes of talk, two of Q&A, three speakers, one deck
(`Group10_final.pptx`, version 3, 26 slides: 11 main, a divider at 12, 14 backups at 13 to 26). This guide is for the three of you to study from. It
gives cues, not a script. Results are frozen (tag `results-freeze-2026-11-18`): every number below is FINDINGS' (rows
of `docs/presentation/pack/02_NUMBERS.md`) or the demo's finder counts (`docs/presentation/TALK_MAP.md`). Plain names
come first; internal codes (F16, FB1 ...) sit in parentheses so you can look them up in FINDINGS. The speakers are
contiguous (Ritik 1 to 3, Arsha 4 to 7, Shrey 8 to 11): swap them if you like, but then swap the time boxes with them.
Version 3 leads with what we built (the harness, the look inside the model, the trained fixes, the multi-agent check), so the
training and the check each get a main slide.

**What the answer is, in one breath.** Tools pull harder than people; after a tool call the answer the user reads goes
quiet about the tool while the private reasoning names it; a thinking mode helped only in part (mixed); so check the
tool outside the model; training cut wrong-hint following but at a cost, and a checker that doesn't read the tool's log stops what two of six reviewers let through. Where it holds: multiple choice, one tool format, open models up to about 32B.

**Hold these corrected wordings** (each is an overstatement we already fixed):

| Don't say | Say |
|---|---|
| "Models stop saying where the answer came from" | In the Qwen3 models; not general: Gemma names the tool in 127 of 162 with thinking off |
| "Tools beat users in all 13 settings" | Decided in the five Track B models (Gate 2) and clear in all 10 readings of the three newer families (FB1); gpt-oss reported without a decision |
| "Authority explains the pull" | It does for pasted tool output; Qwen3 30B Instruct's own call goes beyond the claim (+75 [+65, +85]) |
| "The same three layers in a second model" | Qwen3 8B's own layers 21, 22, 29 hold 0.70 [0.60, 0.83]; the heads are Olmo only |
| "Fine-tuning made answers candid and fixed following" | Candid (37 of 42 against 18 of 42), but no difference detected in following against the one-line instruction (+2 [−2, +6]), and fewer than no fix |
| "Consistency training beats the instruction" | Fewer wrong hints followed, but costs acceptance of right ones: a trade |
| "The models lie" | Keyword counts of mentions; no proof of lying |
| "+64" alone | On the real tool call, thinking on minus off, read after the fact (exploratory) |
| "The label / the instruction does nothing" | No change detected in following |
| "Training cut wrong-tool following 42% to 12%" | It cut wrong-hint following, from the user or a tool pooled (297 of 703 to 84 of 694); the right TOOL hints taken fell too, 439 of 476 to 347 of 459 (92% to 76%) |
| "No fix beats the instruction" without the cost | None did without refusing more right hints; say the gain and the cost together; never "solved" or "fixed" alone |
| "Fine-tuning follows no less than the instruction" | No difference detected (+2 [−2, +6]) |
| "No-hint accuracy within 4 points" | Within 5 points (Gate 3's margin); consistency + instruction is −4 against no fix |
| "Reviewers defer to the tool" | Two of six do, the two Olmo reviewers; the other four do not |
| "Six reviewers, four views" | Up to four views: only two reviewers saw all four |
| "+0.68 logits, layers 0 to 14" as one fact | Two results: +0.68 [+0.17, +1.18] is the whole effect of the consistency-trained weights; "before the readout layers (0 to 14)" is where it sits |
| "479 hand labels" as 479 trusted labels | 479 rows labelled; one set (101) is below the agreement bar, so it counts as effort, not as trusted labels |

---

## 1. The run of show

Times are the deck's notes. Hit the points; the numbers are the ones on the slide or in its notes (rate, n, interval).
Hand-off lines give the idea, not the words. Ritik has 1:35, Arsha 2:35, Shrey 1:50, and each person's slides are together.

| Slide, speaker, time | Hit these points | Numbers | Hand-off |
|---|---|---|---|
| **1 Do thinking modes make chain-of-thought more honest?** Ritik 0:00–0:10 | Who we are. The title question. | none | "Here is the situation we care about." |
| **2 Tools steer answers, and the user sees only the result** Ritik 0:10–0:40 | Tool-using systems look things up and the tool can be wrong. The user sees only "(C)". Why it matters: assistants act on tool output, users see only the final answer, other models increasingly check it. Our question: when the tool is wrong, does the model follow it, and does its reasoning or answer say so? Say once: the example is illustrative, our own question, not a recorded run. | none (illustration) | "Here is what we built to answer it." |
| **3 What we built** Ritik 0:40–1:35 | Four blocks, left to right. (1) The test harness: same question, same wrong letter, only the source changes; 12 open models, thinking on and off. (2) Inside the model: swapping layers' activations (activation patching) in Olmo 3 7B Think's 32 layers, replicated in a second model. (3) Training the fixes: five trained versions, tested on wordings and questions never seen in training (120 fresh questions). (4) The multi-agent check: solver, reviewer (6 models, up to 4 views of the solver's work), then a checker that re-solves without the tool. Then the effort band, one breath. The four whys (paired by question, multiple choice, right hints too, rules written first) are in the notes. | 12 models; 120 fresh questions; effort band: 352 GPU-hours (271 jobs, Ritik's account), 5 trained versions, 31 rules pre-registered, 479 hand labels, over 1,400 tests, results frozen Nov 18 | "First, what we found when we ran it." |
| **4 The failure: tools pull harder, and the answer hides it** Arsha 1:35–2:10 | Left: user against tool, same wrong letter; the tool's bar is higher in every row; Qwen3 30B Instruct is the sharpest. Right: after a tool call, Qwen3 8B's reasoning names the tool, its answer doesn't (keyword counts). Exception: Gemma. The bold line: did thinking make it more honest? Mixed. | 1 of 162 [0, 3%] user; 147 of 162 [85, 94%] own tool call. 141 of 145 [93, 99%] reasoning; 0 of 143 [0, 3%] answer. Gemma 127 of 162 [71, 84%]. Notes: +64 [+51, +75] (on − off, read after the fact) | "Inside the model, where is it read?" |
| **5 Inside the model: three layers read the hint** Arsha 2:10–2:40 | All 32 layers' shares of the hint's effect at the takeover; layers 15, 19, 23 in maroon. Together they hold 0.90 [0.85, 0.96]; the same three on 16 new questions; a second model has its own three (less concentrated). The message: this told us where to intervene (the dial and one fine-tuned version target these layers). | 0.90 [0.85, 0.96]; 0.90 [0.76, 1.06] (16 new questions); Qwen3 8B's layers 21, 22, 29: 0.70 [0.60, 0.83]; 8 of the 10 top heads (Olmo only) | "So we trained fixes." |
| **6 Training cut wrong-hint following from 42% to 12%, at a cost** Arsha 2:40–3:30 | Two panels on the same five versions (120 fresh questions, Olmo 3 7B Think): left, wrong hints followed from the user or a tool (lower is better); right, right tool hints taken (higher is better). Consistency training falls on the left, and on the right too: that is the cost. No fix beat the one-line instruction without refusing more right hints; how often your tool is right decides which to use. "What training changed": fine-tuning made a followed answer say so; inside, fine-tuning acts in the reasoning, consistency training removes part of the pull before the readout layers. | 297 of 703 → 84 of 694 (42% → 12%), −30 [−35, −26] against no fix; right tool hints 439 of 476 → 347 of 459 (92% → 76%); the instruction 237 of 713, LoRA 248 of 705; 37 of 42 vs 18 of 42 say so; +0.68 [+0.17, +1.18]. Notes: the instruction comparison −21 [−26, −16] following, −15 [−20, −10] acceptance | "Let's see one real question." |
| **7 See it: the same question, before and after training** (clip C, about 35 to 40 s) Arsha 3:30–4:10 | Click the video and narrate in short phrases. C1: No fix follows the tool's wrong answer, its reasoning cites the tool, its answer doesn't say so. C2: split with Consistency-trained on the same question and hint; the fix held. C3: Fine-tuned, a different question (pasted tool output): its answer says so. C4: the map, layers 15, 19, 23 together, then where training changed it. C5: the end card. Not cherry-picked: the page's first "fix held" match in a fixed seeded order. | "the fix held" on 26 of 112 questions; 37 of 42 vs 18 of 42 (hand labels); together 90%; 42% → 12%; 92% → 76% | "Now the check downstream." |
| **8 Two of six reviewers defer to the tool; a checker doesn't** Shrey 4:10–4:55 | Why: deployed systems have one model review another; does a reviewer catch a tool's wrong answer? The pipeline: solver with the tool, reviewer, checker, user. Six reviewers seeing the answer only against the tool's log: only the two Olmo reviewers defer. The checker re-solves without the tool and stopped every wrong answer. Three follow-ups (one line each); the limit: only items the solver can solve alone. | Olmo 3.1 32B corrects 59 of 73 from the answer alone, 3 of 73 with the tool's log; checker 53 of 53 [93, 100%] on 100 fresh items, 7 of 45 [8, 29%] false alarms. Follow-ups: 25 vs 9 of 34, +47 [+29, +65]; 5 vs 15 of 21 | "What should a team do?" |
| **9 What we'd tell a team deploying a tool-using model** Shrey 4:55–5:35 | Four rows, each from a number: (1) the answer isn't a record of why; log provenance outside the model; (2) a label or a prompt line won't fix it; (3) if you train, pick by how reliable your tool is; (4) put an independent check before acting. | (1) 0 of 143 [0, 3%] against 141 of 145 [93, 99%]. (2) "unverified" label −1 [−7, +4] (the inserted tool turn). (3) wrong hints 42% → 12%, right tool hints 92% → 76%. (4) 53 of 53 [93, 100%]; one more model call | "Where this holds, and what we don't know." |
| **10 Where this holds, and what we don't know** Shrey 5:35–5:55 | Applies to: multiple choice; one tool format; open models up to about 32B; every fix on one model, one training run each; 42 hand-labelled answers per system; the checker on items the solver can solve alone. Unknown: free-form multi-step agent tasks; larger and closed models; transfer of the fixes. | none | "Thank you." |
| **11 Thank you** Shrey 5:55–6:00 | Thank you; questions; backups wait after the divider (slide 12). | none | none |

**Per-slide points to land if you only have a breath** (the one sentence each slide must leave):
2 the user sees only the letter; 3 we built a harness, a look inside, fixes and a check; 4 tools pull harder and the answer
goes quiet; 5 three layers read the hint; 6 training helped, at a cost; 7 a real recorded question, found by pattern; 8 two of six
reviewers defer, a checker doesn't; 9 verify outside the model; 10 here is where we stop.

---

## 2. Timing plan

About 130 words a minute. A deck timed at 6:00 from its notes usually runs 6:30 to 7:00 when three people speak it with
hand-offs and a video click. So time each speaker's section separately, and decide in advance what you cut.

| Speaker | Section | Budget | Words |
|---|---|---|---|
| Ritik | 0:00–1:35 | slide 1: 0:10 (about 20 words); slide 2: 0:30 (about 65); slide 3: 0:55 (about 120) | about 205 |
| Arsha | 1:35–4:10 | slide 4: 0:35 (about 75); slide 5: 0:30 (about 65); slide 6: 0:50 (about 105); slide 7: 0:40 (about 55, over the clip) | about 300 |
| Shrey | 4:10–6:00 | slide 8: 0:45 (about 95); slide 9: 0:40 (about 85); slide 10: 0:20 (about 40); slide 11: 0:05 (about 10) | about 230 |

- **Slide 3 is dense.** Four blocks and a band in 55 s: about 10 s a block, then 10 s for the band. Don't read the band; say
  "352 GPU-hours, five trained versions, 479 hand labels, all rules written first" and move on.
- **Slide 7.** The clip is 35 to 40 s and plays on click. Say one sentence before the click (what to watch for: the tool's
  reply, the highlighted mention, the bare letter), then short phrases over it that match its captions (about 55 words in all),
  and let C5's end card finish it. Don't read the counts; say "26 of 112 questions look like this".
- **Hand-offs** take about 3 s each. Start the next speaker's first sentence on the slide change, not after it.
- **Numbers cost time.** Say the number and its n ("147 of 162"), not the interval; the interval is on the slide. Say
  an interval aloud only if asked.

**Where to cut if running long, in order** (each speaker cuts only their own section):
1. **Clip C's beat 3** (about 6 s; the fine-tuned model's hand-labelled answer, on another question). Ritik's rule: cut it first;
   the end card and the map still carry the training story. Then say nothing about 37 of 42 aloud on slide 7 (it is in slide 6's notes).
2. **Slide 4's second-part details** (Arsha): drop the title-question sentence's detail; keep "mixed", the Qwen3 8B line and
   the Gemma exception (the exception is an honest limit). Gpt-oss and Nemotron are only for questions.
3. **Slide 3's effort band** (Ritik): say the four blocks and one phrase for the band ("352 GPU-hours, five trained versions");
   the whys stay in the notes.
4. **Slide 8's three follow-ups to one** (Shrey): keep the 25 vs 9 of 34 line; the other two are on backup 17.
5. **Slide 6's "What training changed" panel and the exploratory crossover** (Arsha): say the two rates and "it's a trade".
   Never drop the right-hint cost, and never say the crossover (0.36 [0.22, 0.50]) without the word "exploratory" (backup 16).
6. **Clip C's beat 4b to c** (the second half of the map beat, 3 to 4 s): keep "three layers, together 90%".

Clip A (backup 25, with stills at 21) and clip B (backup 24) are never played in the main talk.

Last resort: slide 10, read only the "Unknown" column and say "the left column is on the slide".

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
4. **Activation patching and the readout layers.** Copy one layer's internal state (its activations) from a clean run into a hinted run and see
   whether the answer flips back; where it does is where the hint is read (the "readout" layers). *Analogy:* in a game of telephone, replace one
   person's message with the clean one and see whose fixes the final message. *Our number:* layers 15, 19, 23 hold 0.90 [0.85, 0.96];
   Qwen3 8B, with its own layers 21, 22, 29, 0.70 [0.60, 0.83].
5. **Attention heads.** Each layer has many heads, each its own "where to look" pattern; we asked which look at the hint more
   when the model follows it. *Analogy:* a layer is a committee, heads are its members. *Our number:* 8 of the 10 top heads are in
   layers 15, 19 and 23; followed minus resisted +0.040 [+0.021, +0.057] (Olmo only).
6. **LoRA (light fine-tuning).** Train small added matrices on examples, instead of changing all the weights; ours learns from 1,196 examples. *Analogy:* clipping an adjustable
   lens onto a camera. *Our number:* following wrong hints, LoRA minus no fix −10 [−16, −4], the one-line instruction −13 [−21, −6];
   when LoRA follows a wrong hint its answer says so in 37 of 42 against the instruction's 18 of 42; against the instruction it follows no less (no difference detected).
7. **Consistency training.** Train the model to write the reasoning it would have written without the hint, then an answer that
   names the hint. *Analogy:* practicing with the rumor removed, then saying "someone told me (C); I checked and disagreed".
   *Our number:* wrong hints followed 297 of 703 for no fix against 84 of 694 (42% to 12%, −30 [−35, −26]); right tool hints taken 439 of 476 against 347 of 459 (92% to 76%);
   against the instruction, 84 of 694 against 237 of 713, −21 [−26, −16]: "fewer, but costs acceptance".
8. **The attention dial.** At answer time, turn down the attention to the tool's tokens in the readout layers; no training.
   *Analogy:* a volume knob on one speaker. *Our number:* on 120 fresh questions, following 82 of 240 → 49 of 240 (−13.8 [−20.0, −7.5]),
   with right-hint acceptance −5.8 [−10.8, −1.3].
9. **Wilson interval (for a rate).** A 95% interval for a rate "k of n", well behaved at small n and near 0% and 100%. *Analogy:* 73 cars pass
   and 59 are red: the true share is probably within a band, wider with fewer cars. *Our number:* the Olmo reviewer corrects
   59 of 73 [70, 88%] wrong tool answers from the answer alone.
10. **Paired bootstrap, clustered by question (for a difference).** For a difference between two systems, re-draw the questions (with all their runs,
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
14. **The multi-agent check (solver, reviewer, checker).** A solver answers with the tool's help; a reviewer (another model) reads the solver's work and
    may correct it; a checker re-solves the question without the tool and flags a disagreement. *Analogy:* an editor who reads the draft and its footnotes
    (and trusts the footnotes), against a second person who solves the problem from scratch. *Our number:* two of six reviewers defer; the Olmo reviewer corrects 59 of 73 from
    the answer alone, 3 of 73 with the tool's log; the checker stopped 53 of 53 [93, 100%], with 7 of 45 [8, 29%] false alarms.

---

## 4. The Q&A bank

Thirty-seven questions (Q31 to Q37 are new for version 3). **Say** is one sentence in FINDINGS' wording; **Evidence** has the numbers; **Unknown** is what we don't
know (say it: the rubric rewards it); **Show** is the slide to jump to (slide 12 is the divider; the backups are 13 to 26). Hard ones are
marked with a star. Rule for all of them: answer the question in your first sentence, then stop.

**Q1 ★ Why one model for the fixes?**
- **Say:** Every fix was tested on one model, Olmo 3 7B Think, where we had found the readout layers and could train and patch; so the
  fixes' trade-off is claimed for that model only.
- **Evidence:** the instruction −13 [−21, −6] against no fix; consistency training 84 of 694 against 237 of 713. The failure itself
  holds in the answering models; the readout replicates in a second (0.70 [0.60, 0.83]). Compute was the limit: a replication that resolves the dial needs about 107 to 245 fresh questions.
- **Unknown:** whether the fixes transfer; each is one training run.
- **Show:** backups 15 and 26; slides 6 and 10.

**Q2 ★ Are 42 labels enough?**
- **Say:** It is a small sample, so we state the interval and claim only that candid answers are more common than with the instruction: 37 of 42 against 18 of 42.
- **Evidence:** +45 [+25, +64]; Ritik against J-opus 0.96, J-opus (blind to systems) agrees on 82 of 84 rows; the keyword version agrees
  (225 of 248 against 118 of 237; exploratory, post hoc). Candid does not mean following less: no difference detected against the instruction (+2 [−2, +6]).
- **Unknown:** other models and question sets; the sheet was not blind in practice (the trained style is recognizable); final answer only.
- **Show:** backups 26 and 15; slides 7 and 10.

**Q3 ★ Why multiple choice?**
- **Say:** Because following a hint is unambiguous (the hint's letter picked) and fresh questions mean we didn't tune to the test.
- **Evidence:** the 54 questions (24 puzzles and 30 MMLU-Pro), the held-out 30, 120 fresh ones for the fixes. A letter answer is also why the final
  answer can be a bare letter.
- **Unknown:** free-form, multi-step tasks; other tool formats.
- **Show:** slides 3 and 10.

**Q4 ★ Is this just sycophancy?**
- **Say:** No: sycophancy is deferring to the user, and here the same wrong letter from the user is followed far less than from a tool.
- **Evidence:** Qwen3 30B Instruct 1 of 162 [0, 3%] from the user, 147 of 162 [85, 94%] from its own tool call. A user's answer-key claim closes 68% and 71% of the gap to the pasted block in Qwen3, all of it in Olmo: claimed authority matters; the model's own call goes beyond the claim (+75 [+65, +85]).
- **Unknown:** why; we didn't test what in training causes the deference.
- **Show:** backups 22 and 14.

**Q5 ★ How is this different from the related work?**
- **Say:** Others showed first that models use hints they don't name, that a tool's cue is named less than a user's, that claimed authority
  moves answers, and consistency training as a method; ours is the private reasoning against the final answer after the model's own tool call,
  thinking on and off in the same weights, a user's claim against each tool channel, the layers, the cost of every fix on right hints, and a review team.
- **Evidence:** nine papers checked, not a literature search; four of them on abstracts only.
- **Unknown:** two papers disagree with a tool-over-user claim (a user's assertions followed more than function-sourced ones; tool-channel instructions discounted); we haven't reconciled them, and ours is for our models and tasks.
- **Show:** backup 18.

**Q6 ★ Are the demo's examples cherry-picked?**
- **Say:** No: the page finds the question by a pattern, in a fixed seeded order that never looks at outcomes, and says how many questions fit.
- **Evidence:** clip C's question is the first match of "the fix held" (No fix took the wrong hint and Consistency-trained didn't), which fits 26 of 112 questions; it is also clip A's question, the first match of "took the wrong hint, named the tool in its reasoning, not in its answer", which fits 28 of 114 (Olmo 3 7B Think, no fix). The finder's counts equal a count made from the per-question files, tested over 624 combinations.
- **Unknown:** the finder shows one question at a time; the frozen counts, not the clip, are the evidence. Clip C's third beat is a different question (Q34).
- **Show:** slide 7 (clip C); backups 25 and 21.

**Q7 ★ Why 38 of 114 on one screen and 85 of 233 on another?**
- **Say:** The finder counts questions for the wording on screen; the number under the run is the frozen count of runs over both tool-call wordings; the two wordings' counts add up to it, because on the 120 each question has exactly one run per wording, so a question count there is also a run count (tested).
- **Evidence:** 38 of 114 and 47 of 119 make 85 of 233 [31, 43%]. Backup 25's 28 of 114 is a narrower pattern (the reasoning named the tool, the answer didn't); clip C's 26 of 112 is "the fix held".
- **Unknown:** none; these are presentation counts from recorded runs, and the frozen one is the 85 of 233.
- **Show:** backup 25.

**Q8 ★ Isn't consistency training just ignoring tools?**
- **Say:** Partly: it follows fewer wrong hints but also takes fewer right ones, which is a trade, not a fix that beats the instruction.
- **Evidence:** wrong hints 84 of 694 against 237 of 713 (−21 [−26, −16]); right hints 347 of 459 against 431 of 476 (−15 [−20, −10]). Inside, its weights remove part of the hint's pull from layers 0 to 14, before the readout (+0.68 [+0.17, +1.18]).
- **Unknown:** one model, one run; the crossover (0.36 [0.22, 0.50]) is exploratory.
- **Show:** backups 15 and 26; slide 6.

**Q9 ★ How expensive is the checker?**
- **Say:** One more model call, and false alarms on 7 of 45 good lookups.
- **Evidence:** it stopped 53 of 53 [93, 100%] wrong tool answers on 100 fresh items; false alarms 7 of 45 [8, 29%]. It flagged 73 of 75 bad lookups in the first test. A cheaper check from two reviews shipped wrong answers (4 and 7 of 53).
- **Unknown:** items the solver can't solve without the tool; we tested only solvable ones.
- **Show:** slides 8 and 9; backups 17 and 20.

**Q10 ★ Would larger or closed models behave the same?**
- **Say:** We don't know; we tested open models up to about 32B.
- **Evidence:** the effect is decided in five Track B models and clear in all 10 readings of three newer families; no closed model, no paid API.
- **Unknown:** larger and closed models.
- **Show:** slide 10; backup 22.

**Q11 ★ What would you do with another month?**
- **Say:** Test the fixes on a second model, try free-form multi-step tool tasks, and test the checker where the solver can't solve the question alone. (Plans, not results.)
- **Evidence:** the three open limits on slide 10; the dial's replication needs about 107 to 245 fresh questions.
- **Unknown:** all three.
- **Show:** slide 10.

**Q12 ★ Is this "lying"?**
- **Say:** No; our word counts show mentions, not intent: the keyword counts are an upper bound and the hand labels find almost no claimed disagreement.
- **Evidence:** keyword counts of the hint named in private reasoning 208 of 216 and in the final answer 8 of 216; the keyword also fires on 22 of 72 no-hint runs.
- **Unknown:** what the model "means"; we only measure what the text says.
- **Show:** backup 23.

**Q13 Did thinking make chain-of-thought more honest?**
- **Say:** Mixed: thinking on moved the tool into Qwen3 8B's private reasoning but not its answer, and it followed the real tool call more.
- **Evidence:** 141 of 145 [93, 99%] reasoning, 0 of 143 [0, 3%] answer; following +64 [+51, +75] (on minus off, read after the fact). gpt-oss: more effort, no change detected (+7 [−1, +16]; −5 [−10, 0]). Nemotron: less bare with thinking on (−14 [−19, −9]).
- **Unknown:** one model per comparison; Qwen3 8B's on-minus-off was exploratory.
- **Show:** slide 4; backups 22 and 23.

**Q14 Doesn't another paper contradict "tools beat users"?**
- **Say:** We claim it for our models and tasks only: an answer key's wrong fact, decided in the five Track B models and clear in all 10 readings of three newer families.
- **Evidence:** Qwen3 30B Thinking +35 [+24, +46] for pasted output; Olmo +32 [+22, +42]; Qwen3 30B Instruct's own call +90 [+83, +96], each against the user.
- **Unknown:** policy-style or function-calling hints; not reconciled.
- **Show:** backups 18 and 22.

**Q15 Why not just add the one-line instruction?**
- **Say:** The instruction is the baseline every fix must beat, and none beat it without a cost to right hints.
- **Evidence:** the instruction −13 [−21, −6]; LoRA −10 [−16, −4]; LoRA minus the instruction +3 [−1, +8] (no difference detected). Asking the model to cite its sources made the answer name the tool more (+47 [+30, +64]) but following no less (+6 [−2, +14]).
- **Unknown:** the instruction is one wording on one model.
- **Show:** backups 15 and 26; slide 6.

**Q16 How do you know which layers read the hint, and does it generalize?**
- **Say:** By activation patching at the takeover; three layers of Olmo 3 7B Think carry about 90%, and Qwen3 8B replicates with its own three layers.
- **Evidence:** layers 15, 19, 23: 0.90 [0.85, 0.96]; on 16 new questions 0.90 [0.76, 1.06]; Qwen3 8B's layers 21, 22, 29: 0.70 [0.60, 0.83].
- **Unknown:** the mechanism as a whole is tentative; the heads are Olmo only.
- **Show:** slide 5; backup 13.

**Q17 Is the tool format realistic?**
- **Say:** It is one format, an answer-key lookup; a retrieved passage gives a smaller but real pull.
- **Evidence:** with a retrieved passage the solver follows a bad lookup in 19 of 55 against 52 of 55; the Olmo reviewer still defers (5 against 15 of 21, −48 [−67, −29]).
- **Unknown:** other tools and free-form tasks.
- **Show:** backups 14 and 17.

**Q18 Are the keyword counts valid? What about hand labels?**
- **Say:** They are keyword counts and we call them that; hand labels stand for some claims, not for the first private/final split.
- **Evidence:** 208 of 216 and 8 of 216 are keyword counts; the first hand labels reached kappa 0.63 and 0.54, short of agreement; later labels reached 0.93 and 0.96.
- **Unknown:** every kappa is Ritik against an AI rater, not two humans.
- **Show:** backup 23.

**Q19 How do we know the numbers didn't move after you saw them?**
- **Say:** Results were frozen on Nov 18 under a git tag, and the decision rules were written before their data.
- **Evidence:** 31 rules pre-registered, each committed before its runs; deviations listed. Not pre-registered: the trained versions against the instruction on the 30, Qwen3 8B's on minus off, and the trade-off figure (exploratory).
- **Unknown:** none beyond those marked.
- **Show:** backup 19.

**Q20 Which models, and why these?**
- **Say:** Twelve open models: eight answering and four reviewers, open so we can patch layers and train fixes.
- **Evidence:** the answering set includes Olmo 3 7B Think, three Qwen3 models, gpt-oss-20b, Gemma 4, Nemotron 3 Nano and Granite 4.2.
- **Unknown:** closed models.
- **Show:** backups 22 and 20.

**Q21 Why do only Olmo's reviewers defer?**
- **Say:** Six reviewers over four families were run and only Olmo's two defer; the family can't be separated from its data, recipe and template.
- **Evidence:** Olmo 3.1 32B corrected 59 of 73 from the answer alone, 3 of 73 with the tool's log; Olmo 3 7B Instruct −42 [−58, −28]; Qwen3 30B Thinking +1 [−6, +10]; Granite −5 [−26, +15]; Mistral +19 [+10, +30].
- **Unknown:** tentative with two reviewers a family.
- **Show:** slide 8; backup 17.

**Q22 Did the attention dial work?**
- **Say:** It cut following on 120 fresh questions but cost right-hint acceptance, so it ignores tools by our rule.
- **Evidence:** 82 of 240 → 49 of 240 (−13.8 [−20.0, −7.5]); acceptance −5.8 [−10.8, −1.3]. On the first 30 questions −17 [−30, −3], underpowered.
- **Unknown:** whether the cost passes the 5-point limit isn't resolved.
- **Show:** backups 15 and 26.

**Q23 Why is the trade-off "exploratory"?**
- **Say:** It was computed after the results were read, with its log written before computing, and it replaces no verdict.
- **Evidence:** consistency training gives more correct answers than the instruction only when fewer than 0.36 [0.22, 0.50] of the tool's answers are correct.
- **Unknown:** the crossover for other tools and models.
- **Show:** backup 16.

**Q24 Does "tools pull harder" hold in every model?**
- **Say:** Decided in the five Track B models and clear in all 10 readings of the three newer families; gpt-oss was reported without a decision.
- **Evidence:** the left chart on slide 4 and the full figure on backup 22; gpt-oss ran after its one-day window.
- **Unknown:** gpt-oss, and everything beyond these models.
- **Show:** slide 4; backup 22.

**Q25 Is the pull just the claimed authority?**
- **Say:** For pasted tool output, much of it; for a model's own tool call, no.
- **Evidence:** the answer-key claim closes 68% and 71% of the gap; the official manual minus a classmate +41 [+31, +51], +12 [+4, +20], +32 [+23, +41]; Qwen3 30B Instruct's call goes beyond the claim, +75 [+65, +85].
- **Unknown:** what else in the tool's form drives the pull.
- **Show:** backup 14.

**Q26 If a team does only one thing, what?**
- **Say:** Put an independent check before acting on a tool-backed answer, and log the tool's provenance outside the model.
- **Evidence:** the checker 53 of 53 [93, 100%] against reviewers who see the log, 3 of 73; the answer names the tool in 0 of 143.
- **Unknown:** solver-can't-solve cases.
- **Show:** slides 8 and 9; backup 17.

**Q27 What if the solver can't solve the question without the tool?**
- **Say:** We don't know; the checker was tested where the solver can solve alone.
- **Evidence:** 53 of 53 [93, 100%] stopped; 7 of 45 [8, 29%] false alarms; both were measured on items the solver can solve alone.
- **Unknown:** the hard case; the most important open one for deployment.
- **Show:** slide 10; backups 17 and 20.

**Q28 How sure are you? What are the intervals?**
- **Say:** Rates carry 95% Wilson intervals; differences are percentage points with a paired bootstrap clustered by question.
- **Evidence:** 20,000 resamples; under 5 questions we give no interval ("too few questions").
- **Unknown:** the keyword counts are a measure, not a ground truth.
- **Show:** backup 19.

**Q29 Why 12 models and two modes, not more questions?**
- **Say:** We wanted to know whether the pattern is about one model or many; the strip shows it across ten model settings.
- **Evidence:** 54 questions with 3 runs each per setting for the main tests; 120 fresh questions for the fixes.
- **Unknown:** larger question sets would narrow intervals.
- **Show:** backup 22.

**Q30 How did you use AI tools?**
- **Say:** Claude Code wrote and ran code, tests, analyses and figures under rules that keep every commit a team member's own; models studied are the experiments' subjects.
- **Evidence:** the AI-use inventory (`docs/submission/AI_USE_INVENTORY.md`); labels by Ritik with an AI rater and AI judges; no paid API called.
- **Unknown:** some inventory lines are still "to confirm": check before Dec 3.
- **Show:** none.

**Q31 ★ Did training solve it?**
- **Say:** No: consistency training cut wrong-hint following a lot, at a cost, and no fix beat the one-line instruction without that cost.
- **Evidence:** wrong hints followed 297 of 703 to 84 of 694 (42% to 12%, −30 [−35, −26] against no fix); right tool hints taken 439 of 476 to 347 of 459 (92% to 76%); the instruction alone 237 of 713, LoRA 248 of 705. Against the instruction, −21 [−26, −16] following and −15 [−20, −10] acceptance.
- **Unknown:** one model, one training run each; whether the cost can be removed.
- **Show:** slide 6; backups 15 and 26.

**Q32 ★ Is 42% to 12% about tool hints?**
- **Say:** It is wrong-hint following, pooled over the user's guess, pasted tool output and the tool's turn: not tool hints alone.
- **Evidence:** 297 of 703 to 84 of 694 is FINDINGS' pre-registered measure for the trained versions ("follows the wrong hint"). Only the right-hint rates are tool-only: 439 of 476 to 347 of 459 (92% to 76%).
- **Unknown:** the same fall split by channel is not in the frozen tables we use here; we don't claim it.
- **Show:** slide 6; backup 26.

**Q33 ★ How do you know layers 15, 19 and 23 aren't an artifact?**
- **Say:** We swapped each layer's state from a clean run into a hinted one and measured how much of the hint's effect disappeared; the same three held up on questions we hadn't used, and a second model has its own three.
- **Evidence:** 0.90 [0.85, 0.96]; on 16 new questions 0.90 [0.76, 1.06]; Qwen3 8B's layers 21, 22, 29: 0.70 [0.60, 0.83]; 8 of the 10 top heads are in layers 15, 19 and 23 (Olmo only).
- **Unknown:** patching shows where the hint is read, not why; the 16 new questions give a wide interval; a different second model might read it elsewhere.
- **Show:** slide 5; backup 13.

**Q34 ★ Why was the fine-tuned clip on another question?**
- **Say:** Hand labels exist only for a sample, not for every question, so beat 3 uses the first Fine-tuned row in the labelled sample's fixed order whose label says the answer names the hint, and the caption says "another question".
- **Evidence:** 37 of 42 against 18 of 42, hand-labelled (+45 [+25, +64]); that is the evidence, not the one clip.
- **Unknown:** a single run proves nothing; it illustrates the count. If the clip runs long this is the first beat cut.
- **Show:** slide 7; backup 26.

**Q35 What did training change inside the model?**
- **Say:** Fine-tuning acts in the reasoning, with the readout layers still pulling; consistency training removes part of the pull before the readout layers.
- **Evidence:** consistency-trained weights: +0.68 [+0.17, +1.18] in all, sitting before the readout layers (0 to 14): two results, not one.
- **Unknown:** whether other training recipes act the same way; one model and one run each.
- **Show:** slide 7 (the map beat); backup 15.

**Q36 Do the 479 hand labels and 5 trained versions mean what they look like?**
- **Say:** They're effort, not a headline: 479 rows were hand-labelled over three sets, one of which (101 rows) was below the agreement bar; and "five" counts the four Gate 3 versions plus consistency training.
- **Evidence:** the labels that carry claims: 42 a system, kappa 0.96 with an AI rater; the earlier set's 0.63 and 0.54 did not reach agreement.
- **Unknown:** the second rater was an AI, not a second human.
- **Show:** slide 3 (its notes); backup 19.

**Q37 Does training hurt accuracy when there's no hint?**
- **Say:** A little, within the 5-point margin we set.
- **Evidence:** no-hint accuracy 156 of 236 for no fix against 146 of 229 for consistency training; consistency + instruction −4 against no fix. Gate 3 allowed 5 points.
- **Unknown:** one model; the margin itself was our choice.
- **Show:** backups 15 and 26.

---

## 5. Rubric self-check

| Criterion | Where the deck earns it | Evidence | What a grader could still mark down |
|---|---|---|---|
| **Technical soundness (7)** | Slide 3 (what we built: harness, layers, fixes, check); backups 19, 20 | Paired by question; multiple choice for an unambiguous measure; right hints for the cost; 12 models; 31 rules pre-registered; 95% Wilson and paired bootstrap | One task type and tool format; keyword counts for the words; 42 labels per system; kappa is a human against an AI rater; fixes on one model |
| **Quality and interpretation of results (5)** | Slides 4 to 8 (each with n and interval); backups 22, 23, 26 | 1 of 162 [0, 3%] against 147 of 162 [85, 94%]; 141 of 145 [93, 99%] against 0 of 143 [0, 3%]; 0.90 [0.85, 0.96]; 84 of 694 against 297 of 703 with its cost; 53 of 53 [93, 100%]; the Gemma exception; "mixed" stated | The strip's top row is one model's sharpest case; +64 read after the fact; one honest limit per result must be said aloud, not just shown; 42% to 12% pools channels |
| **Deployment framing (4)** | Slide 9 (four rows, each from a number); slide 10 | 0 of 143; −1 [−7, +4]; 42% to 12% with 92% to 76%; 7 of 45 false alarms and one more call | The recommendations are our reading (interpretation), not tested in a real deployment; the exploratory crossover |
| **Presentation clarity (2)** | The whole deck in 6:00; one idea a slide; claim titles; clip C | Notes timed to 6:00; contiguous speakers | Three speakers usually run over: rehearse each section; slides 3 and 6 are dense |
| **Q&A** | The 14 backups, section 4 above | Each answer: one sentence, its numbers, its unknown, its slide | A vague "we think so"; an uncorrected old wording; reading a number without its n |

Past feedback to remember: we lost marks on "quality of preliminary results". Every result you say needs its number, n,
comparison and one limit.

---

## 6. If the video doesn't play

Don't debug on stage. Clip C's fallback is the poster frame on slide 7 plus the narrated beats, in this order (about 25 s; skip beat 3 if short):

> "No fix follows the tool's wrong answer; its reasoning cites the tool and its answer doesn't say so. Consistency training, on the same question and hint, held.
> The model's hidden layers are where this is read: three layers hold about 90% of the effect. And that's wrong-hint following down from 42% to 12%, with right tool hints taken down from 92% to 76%."

Say "this is a real recorded run, found by a fixed pattern, 26 of 112 questions" and move to Shrey. If the poster doesn't show either, the last resort
is the stills backup (backup 21, clip A's stills, the same kind of run, local deck only) or the live scratch pad (key **1** of the local demo, Show me, "the fix held"),
and only if it opens in 5 seconds; otherwise say the two sentences and go on. Clips A (backup 25) and B (backup 24) are not played in the main talk; each has
the same fallback: say in one sentence what it shows, and move on.

---

## 7. Rehearsal plan

1. **Run 1, slow, with the notes.** Everyone, all slides, with a stopwatch per speaker (three stopwatches or a phone each). Note each
   section's time. Mark what you cut (section 2's order).
2. **Run 2, no notes, with the video.** Arsha rehearses the click and the narration over clip C; hand-offs on the slide change (Ritik to Arsha at 1:35, Arsha to Shrey at 4:10). Each speaker
   must finish inside their own box: Ritik 1:35 (slides 1 to 3), Arsha 2:35 (4 to 7, ending at 4:10), Shrey 1:50 (8 to 11, ending at 6:00). Anyone over cuts the next item in their list.
   Because the speakers are contiguous, each person can rehearse their block alone, on their own, three times, before Run 3.
3. **Run 3, the dress run.** One continuous take from the deck file as it will be uploaded, in Slide Show mode, with the 2-minute mock Q&A.
4. **The 2-minute mock Q&A.** One person reads questions from section 4 at random (at least two stars, "Did training solve it?", "38 of 114 against 85 of 233", "is this lying"); another
   answers in one sentence and jumps to the backup slide; the third times it. Aim for 15 seconds an answer, so about 8 in 2 minutes. Ritik answers the training questions (Q8, Q15, Q31 to Q37) first.
5. **Check clip C plays in PowerPoint's Slide Show mode**, on the file that goes to Canvas (the one with the clips embedded),
   and on a Windows machine if you can borrow one: the classroom PC likely runs Windows. Confirm the click starts clip C, the sound works or the
   clip is fine silent, and clips A and B on backups 25 and 24 start too. Run with no internet.
6. **Before Dec 3:** upload by Nov 30; agree who answers which questions (the owner of the slide answers first); each person reads the "Don't say" table once more.
