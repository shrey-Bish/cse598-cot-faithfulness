# Plan: Oct 31 – Nov 24 (CSE 598, Group 10)

Last updated: 2026-11-06 11:30 MST (E2's and the 30's lines all ended; the nov6 rule said no cut; A40's data and its gated lines; A41 and A42 after A40's training; earlier, Nov 5 13:42: the pull done; A40's targets about 11 h; Arsha's setup Nov 6; 09:54: two Sol accounts from Nov 5: B20 on Arsha's own, the Sol order, B1R2 dropped for A40 and A40's row, the calendar's rows from Nov 5, slide 10 and the Sol risk; earlier, Nov 4 22:52: the calendar's Nov 5–7 row: that night's Sol state, the projections from ONE_PAGE, B20's stop fixed (T13); 21:31: Ritik's re-look of the 7 cells recorded: 4 changed, 3 kept, Gate 2's verdict unchanged; earlier, 18:22: Gate 2's statement with the descriptive sentence; 17:51: the second rater corrected: an AI model, ChatGPT 5 Astra High, not Shrey; L3, L4 and Gate 2 under the LLM-judge protocol; earlier, 16:38: Gate 2's statement; the presentation map and the submission checklist; the 30's Nov 6 and Nov 11 rules applied by the feeder, the A39 log's §16 and §17; earlier: B24 read: F40; B20's second amendment, §16; A39's parts at 2:00, its log's §14; earlier Nov 4: B20 amended after its first smokes, §15 of its log; the feeder's digest and health check; earlier Nov 4: Sol's real limit, the re-plan at 1:30 a job, B1R2 decided).
**Edited by:** Ritik. History: `git log -- docs/PLAN.md`; the Oct 31 version and the per-track design notes that
were below the gates, word for word, in [`archive/superseded/PLAN_2026-10-31.md`](../archive/superseded/PLAN_2026-10-31.md). Where things are:
- progress: [`STATUS.md`](status/STATUS.md);
- each result, with its numbers and source: [`FINDINGS.md`](FINDINGS.md);
- every open item, with owner and due date: [`TODO.md`](status/TODO.md) (Track A, labels, repo), Track B's
  [`TODO_B.md`](trackB/TODO_B.md) and Track C's [`TODO_C.md`](trackC/TODO_C.md);
- how to run each step: [`RUNBOOK.md`](RUNBOOK.md).

**Who runs what.**
- **Track A:** Ritik, to the end.
- **Track C:** Shrey's since Oct 30; the final handoff was Nov 3 (`docs/trackC/START_HERE.md`, its Quick start). Its
  experiments below are prepared (code, CPU tests, a pre-registration log and a dry run each), and Shrey runs them on
  Voyager from Nov 4. Check-ins, and merges of `trackC-main` into `main`: Nov 7, 12, 15 and 18 (RUNBOOK §16).
- **Track B:** Arsha's from Nov 6 (`docs/trackB/START_HERE.md`; the bundle rebuilt and sent Nov 6 morning, with
  Ritik's last push to `trackB-main`; after that the branch is hers). B20 runs on her own Sol account from Nov 5
  (`docs/trackB/SOL_ARSHA.md`). Check-ins Nov 6, 12, 15 and 18; merges of `trackB-main` on the last three. B16 ran Oct 31–Nov 1 and is read (F35); B17 ran Nov 3 and is read (F37; run
  after its one-day window, pre-registration §13). B24, the authority dose, ran on Voyager Nov 4 (Ritik's Mac;
  pre-registered 03:37) and is read (F40): the pull grows from a classmate to the official solution manual.
- **Sol:** the course account only (no other account; the H100s aren't available). **From Nov 5, two Sol accounts,
  one queue file each** (Ritik's decision h; the B20 log's §19 and the A39 log's §19), so no line is ever submitted
  from both, and no credentials are shared (Ritik, Nov 3; re-planned Nov 4 00:48 for Sol's real limit; Nov 5 for two
  accounts):
  - **Ritik's** (`finetune/gpu/sol/queue_2026-11-04.txt`, `owner: ragarw68`), in this order:
    1. the 1-GPU bench (389340): **done Nov 3**, about 400 tokens/s per A100 (not 500), so E2 is 53.2 GPU-hours;
    2. A39 on E2 in 1-GPU parts: the 9 parts queued Nov 3 (7 running from that evening); then the core systems' 28
       sixteenths, the wrapper systems' 15 fifths, and a sweep per system (the A39 log's §12). From Nov 4, the parts
       not submitted by 10:15 run at 2:00 and the sweeps at 3:00: a sixteenth took 1:24:54 of its 1:30 (§14). By Nov 5
       morning every part had gone in, and by Nov 6 10:56 every E2 line had ended (status only; the A39 log's §20);
    3. A40 (its own pre-registration, Nov 5, the 09:18 log): its lines after E2's, the first gated by the feeder's
       check of its data on Sol (its §11, Nov 6). Its data: 883 examples (its §17);
    4. A39 on the 30 (29 lines): all ended by Nov 6 10:56, having gone in as places freed while A40's lines weren't
       ready. The Nov 6 07:00 rule said no cut (60.6 GPU-hours), and the Nov 11 rule has nothing left to drop (§20);
    5. A41 (A40's weights in A18's swap and Step 10) and A42 (A40 with the note, on E2), pre-registered Nov 6 (the
       11:21 and 11:22 logs), after A40's training, so the account doesn't sit idle.
  - **Arsha's** (`queue_b20_2026-11-05.txt`, `owner: not ragarw68`; her setup `docs/trackB/SOL_ARSHA.md`): B20's runs
    left on her own feeder, Granite's 8 and Gemma's 12 lines of 3:00, one chain a model, question by question (the
    B20 log's §19). B20's smokes and first runs (Nov 4, the B20 log's §14–§18) ran on Ritik's account, and Nemotron's
    runs are all done; the saved files are copied to her scratch first.
  - **B1R2:** dropped Nov 5 (decision f), revived Nov 6 (the A39 log's §21): last in Ritik's queue with `reserve=240:2`,
    filling only room A40's, A41's and A42's lines can't use; partial at Nov 15 23:59 as §13.8 says.

  **What binds** is the class QoS's 960 running GPU-minutes (each running job's time left × GPUs) and the 10 submitted
  jobs, each user's own, not two running jobs: 7 ran at once on Nov 3. So jobs are 1:30 (10 at once hold 900); A39's
  parts at 2:00 from Nov 4 (8 fresh ones hold 960); B20's at 3:00 from Nov 5. **The feeder**
  (`tools/sol_feeder.py`, from Nov 4) submits them from its user's queue file as places free, day and night (RUNBOOK
  §0); it refuses a queue whose owner line isn't its user's. Time estimates come from `squeue --start` on real jobs,
  not `--test-only`.
- **Pre-registration:** before any run, as always.

**The fix, honestly (Nov 3).** LoRA cuts wrong-hint following by 10 points against base (−10 [−16, −4]) and passes Gate 3 by its rule, as do the other three trained versions. But no trained version beats the one-line instruction in the prompt (prompt_only −13 [−21, −6]; LoRA minus it +3 [−1, +8]). The source tags aren't tool-specific: they help no more on the inserted tool turn than on the pasted block (F28). B1's attention scaling cut following on the inserted turn by 17 points (−17 [−30, −3]) but missed its pre-registered acceptance limit (F38). By hand labels, LoRA's keyword false-disclosure candidates are rarely real (L4 part 1, F28). The main limit is power: 30 questions can't resolve the 5–10 point differences these comparisons turn on (B1's acceptance interval is ±13 points; Gate 3's following differences ±6 to ±7). So the fix round's next step is a bigger, fresh evaluation set fixed before any new result (E2, about 120 questions) and A39 on it (Part 4 of the Nov 3 plan). The verdicts already read on the 30 stay as they are.

## The story: "Where did that answer come from?"

**A tool's influence loses its source at three levels.**

1. **Inside the model: the readout layers read the tool's letter directly.**
   - Known:
     - In Olmo 3 7B Think, three full-attention layers, 15, 19 and 23, carry 0.90 [0.85, 0.96] of the drop in
       hint-token restoration at the takeover (F11).
     - Replicated on separate questions: 0.90 [0.76, 1.06] (set A, F26).
     - Heads L19H31, L23H17 and L15H31 look at the hint more when the model follows it (F12; set A, F32).
     - In Qwen3-8B, whose 36 layers all see the whole prompt, three layers chosen on the puzzles (21, 22, 29) hold
       0.70 [0.60, 0.83] of the drop on MMLU-Pro and are its own top three (A37, F36: replicates).
     - Scaling the tool's attention at inference (B1, F38): a real cut in following on the inserted turn that misses
       its acceptance limit; underpowered at 30 questions; A38 dropped.
     - Training acts in the reasoning, not on the readout (A18, F39): given base's own reasoning, LoRA's weights pull
       toward the hint's letter harder, not less; LoRA's own following runs through the same three layers.
   - Open: does a provenance wrapper or a combination beat the one-line instruction on 120 fresh questions (A39, E2)?
2. **In the model's words: after a tool call, the answer stops naming its source.**
   - Known:
     - The private reasoning names the hint in 208 of 216 runs, the final answer in 8 (F3, keyword counts).
     - After a real call, Qwen3 30B Thinking's final answer is a bare `Answer: (X)` in 51 of 54, whether the lookup
       was wrong or right (F15, with C4's control).
     - With the same weights and thinking on, Qwen3-8B's is bare in 138 of 145 (F29).
     - One instruction brings the source back and doesn't reduce the deference (F25).
     - Training cuts following, but none of the four trained versions beats a one-line instruction (F28); the LoRA
       versions' false-disclosure candidates rise by keyword, but by hand labels LoRA's are rarely real (L4 part 1).
     - More thinking changes neither following nor the bare answer after a call (gpt-oss-20b, B17, F37).
     - Most of a tool's pull is its claim to be the answer key: a user making the same claim moves the answer about
       as much, except Qwen3 30B Instruct's own call (+75) and Qwen3 30B Thinking's pasted block (+12); and that
       claim, from the user, is named in the final answer, unlike a tool call (B16, F35; confirmed same-day, B19).
   - Open:
     - Do the hand labels hold (L3: Ritik against AI rater 1, ChatGPT 5 Astra High, kappa under 0.6 on Nov 3; now
       the LLM-judge protocol, pre-registered Nov 4)?
     - Do open models from new families behave the same (B20)?
3. **Between agents: downstream agents can't tell a tool's claim from a colleague's conclusion.**
   - Known:
     - A reviewer that sees the solver's trace stops correcting wrong answers: Olmo 3.1 32B, 59 of 73 → 6 (F18).
     - It replicates on 100 fresh items (F24), in one model family of four (F22, F30).
     - When the solver cites the answer key, the deferring reviewer gets worse (F31). Removing the citing sentences
       restores the check (F34).
     - The checker that never sees the tool caught every wrong answer (C4, C15).
   - Open:
     - Is the authority claim the cue (C19)?
     - Does a handoff note keep the source, and does a decider that never sees the tool accept the wrong answer more
       when the source is gone (C25)?
     - Does a tag the pipeline attaches beat the model's own disclosure (C20)?
     - Does deference survive a realistic tool with no authority label (C26)?

## Every experiment on the map

MUST unless marked. Each new experiment has code with CPU tests, a pre-registration session log (question,
comparison, rule, what counts as each outcome, cost) and a dry run before it runs.

| level | # | question | owner | due | state (Nov 3) |
|---|---|---|---|---|---|
| 1 inside | A37 | Qwen3-8B, Steps 3 and 10: the readout on a second model; verdict by its rule | Ritik | Nov 3 | **done Nov 1** (F36): replicates; layers 21, 22, 29 (chosen on the puzzles) hold 0.70 [0.60, 0.83] on MMLU-Pro |
| 1 inside | A30 | B1, provenance-scaled attention: the bench gate, the plan, the verdict by its rule | Ritik | Nov 4 | **done Nov 3** (F38): deployable "ignores tools" (following on the inserted turn −17 [−30, −3], acceptance −7 points), oracle "no effect" (−9 [−19, +1]) |
| 1 inside | A18 | Inside the fixed model: Steps 9 and 10 on LoRA's evaluation runs. Does training stop the readout at 15/19/23, or act after it? Tool-hint cases only in the primary, user hints apart (amended Nov 1) | Ritik | Nov 10 | **done Nov 3** (F39): "acts in the reasoning" (R_LoRA −0.72 [−1.02, −0.39]); secondaries a and b replicate; slide 10 |
| 1 inside | A38 | STRETCH, only if B1 "works": prompt_only's note + B1 deployable, against each alone, same HF stack | Ritik | Nov 14 | **dropped Nov 3, as pre-registered:** B1's deployable span reads "ignores tools" (F38) |
| control | B16 | Tool or authority? The answer key's authority in the user's hint, against the tool channels | Ritik; Arsha, from Nov 6 | Nov 3 | **done Nov 1** (F35): tool beyond authority for Qwen3 Instruct's call (+75) and Thinking's pasted block (+12), authority moves Olmo more than its inserted turn (−14), no difference in the other three; cross-day (T11) |
| 2 words | B17 | Thinking dose: gpt-oss-20b on Sol at reasoning effort low, medium, high | Ritik submits; Arsha, from Nov 6 | Nov 12 | **done Nov 3** (F37): no change detected on both (following on the real call +7 [−1, +16]; bare after a call −5 [−10, 0]); run after its one-day window, kept by Ritik's decision before any result was read (§13) |
| 2 words | L3 | Gate 2's hand labels (F3 rests on them): kappa per channel | Ritik (rater 2 was AI rater 1, ChatGPT 5 Astra High) | Nov 7 | **both sheets in Nov 3; kappa under 0.6 in four of six cells** (private 0.63, tool 0.29, user 0.85; final 0.54, tool 0.59, user 0.43), human-vs-AI agreement. Next: the LLM-judge protocol (pre-registered Nov 4, the 17:45 log): Ritik's labels final, the AI judges the reliability check; no acknowledgment claim from labels until then. Corrected Nov 4, 17:51: rater 2 was an AI model (ChatGPT 5 Astra High), not Shrey; see the 17:42 log; the settling call and the fresh batch no longer apply |
| 2 words | L4 part 1 | Does training teach the model to claim checks it doesn't do? | Ritik (rater 2 was AI rater 1, ChatGPT 5 Astra High) | Nov 14 | **read Nov 3** (F28; kappa 0.93, human-vs-AI agreement): 1 to 2 of LoRA's 147 candidates claim a rejection they didn't act on; most say the hint shaped the answer; the raters could tell LoRA's style. Corrected Nov 4, 17:51: rater 2 was an AI model (ChatGPT 5 Astra High), not Shrey; see the 17:42 log; the reading stays, as human + AI agreement |
| 2 words | B18 | The final Track B table and one figure | Ritik; Arsha, from Nov 6 | Nov 18 | started Nov 3 (`tools/trackb_final.py`; slide 2) |
| 2 words | B20 | Open models from new families on Sol (Gemma 4 26B-A4B, Nemotron 3 Nano 30B-A3B, Granite 4.2 8B), thinking on and off | Arsha submits, on her own Sol account from Nov 5 (Ritik's until then); Arsha reads | runs Nov 15, read Nov 17 | pre-registered Nov 3; smokes Nov 4: none clean, **amended (§15, §16): Gemma and Nemotron the inserted tool turn, Granite thinking on only** (4,860 runs); runs from Nov 4 evening; Granite's and Gemma's first jobs stopped by a shared stop file (T13, fixed Nov 4, confirmed Nov 5); Nemotron's runs all done. **Amended Nov 5 (§19):** Granite's 849 and Gemma's 1,784 runs left on her account, 3:00 lines (Granite 8, Gemma 12), question by question; read partial at Nov 15 23:59 ("partial: N of 54 questions") if not complete |
| 2 words | B24 | The authority dose: does a second wording hold, and does the pull grow from a classmate to the solution manual? | Ritik runs; Arsha reads from Nov 6 if not before | read when done (by Nov 9) | **done Nov 4 (F40):** 972 runs on Voyager 03:38–11:12; the manual over the classmate in all three; Thinking's manual over B16's wording |
| 1 fix | E2 | A second, larger held-out set: 120 fresh MMLU-Pro questions from the evaluation categories | Ritik | Nov 3 | **done Nov 3** (sha256 `59c5c250…`) |
| 1 fix | A39 | Fix round 2 on E2: the wrapper, combinations, a powered replication of Gate 3 | Ritik | runs Nov 15, read Nov 17 | pre-registered and coded Nov 3; the bench done (400 tokens/s); 9 parts queued Nov 3 (7 running that evening); then 1:30 parts (§12); from Nov 4, 2:00 parts and 3:00 sweeps (§14) |
| 1 fix | B1R2 | B1's deployable span on E2 (a labelled replication) | Ritik | — | **dropped Nov 5 (compute): "not run: GPU time given to A40"** (Ritik's decision f, before any B1R2 run; the A39 log's §19; F38); its 44 lines left the queue. Was: decided Nov 4, it runs (A39 log §13) |
| 1 fix | A40 | Bias-augmented consistency training (Chua et al. 2024): LoRA at `lora`'s settings on the model's own reasoning written without the hint, read on E2 against prompt_only, against base by Gate 3's rule, and against LoRA | Ritik | runs Nov 15, read Nov 17 | pre-registered Nov 5 (log 09:18), before any Voyager call; its targets on Voyager (Ritik's Mac, Nov 5–6); then about 20–25 GPU-hours on Ritik's account, after E2's lines; read partial at Nov 15 23:59 if not complete (its §10) |
| 3 agents | C19 | Is an authority claim the cue (H34)? | Shrey | Nov 7 | prepared |
| 3 agents | C25 | Across agents (the centerpiece): solver with tool → a writer's handoff note → a decider that never sees the tool | Shrey | Nov 12 | prepared |
| 3 agents | C20 | Pipeline vs model: a blind reviewer; a tag the system attaches; the solver's own disclosure; the checker | Shrey | Nov 15 | prepared |
| 3 agents | C26 | SHOULD: a realistic tool, a retrieval passage from the wrong option's text, with no letter and no "answer key" | Shrey | Nov 15 | prepared |
| 3 agents | C22 | STRETCH: a second solver | Shrey | — | not prepared |
| 3 agents | C24, C27, C28 | Track C's figures and tables, and slides 11–12 (Nov 18); Track C's report section, as bullets (Nov 20) | Shrey | Nov 18, Nov 20 | planned |
| labels | L4 part 2, L5 | SHOULD | two raters | — | built |
| dropped | B2 (A31), C21, C23 | dropped (scope, Oct 31) | — | — | — |

## The calendar

| when | Track A (Ritik) | Track B | Track C | labels, repo, report |
|---|---|---|---|---|
| Oct 31–Nov 3 | A37 done (Nov 1); B1 read (Nov 3); A38 dropped; E2 and A39 pre-registered | B16, B19 done; B17 done (Nov 3) | C19, C25, C20, C26 prepared and dry-run; Shrey's workspace (Nov 3) | L3 and L4 part 1 in (Nov 3) |
| Nov 3 | A18 read (F39); the bench done; 9 A39 parts queued | B20's downloads done | **final handoff** (START_HERE's Quick start) | the label deadlines set: Nov 7 |
| Nov 4 | the 9 queued parts end (7 started Nov 3 evening; the last 2 as GPU-minutes free); then, as places free, B20's smokes and runs, E2's 28 sixteenths and the 15 fifths, 1:30 each, up to 10 at once (the Nov 4 log; the feeder from 03:20); one port for every job found and fixed, 340 runs from another model's server set aside (the A39 log's §15) | B20's first smokes: Granite and Gemma amended (§15), Nemotron (§16); **B24 on Voyager** (03:38–11:12), **read (F40)** | setup (Nov 4); C19 | L3: the second rater found to be an AI model (17:42); the settling call and the fresh batch dropped; the LLM-judge protocol pre-registered (17:45) |
| Nov 5–7 | **Nov 5: two Sol accounts** (Ritik's runs A39 and A40; B20 to Arsha's) and **B1R2 dropped** for A40 (the A39 log's §19); Ritik's pull (done about 12:40). E2's last parts and its 7 sweeps (at most about 28 GPU-hours at Nov 5 08:43; about 40 of its parts ran overnight Nov 4–5); **A40** pre-registered (log 09:18), its targets made on Voyager on Ritik's Mac (from 09:50, about 11 h: done about 21:00), then checked, assembled and copied to Sol (about Nov 6), its lines after E2's; A39 on the 30 (29 lines) as places free. **Nov 6 07:00: the feeder's nov6** (should say "no cut": the 08:57 log's §2). Projected (ONE_PAGE, Nov 5): Ritik's account's about 100 GPU-hours end about Nov 7–8 at Nov 3–4's pace, about Nov 13 at a third of it | **Nov 5: B20 moves to Arsha's own Sol account** (the B20 log's §19): she runs `docs/trackB/SOL_ARSHA.md` herself (Nov 6); then Granite's 8 and Gemma's 12 lines of 3:00 (849 and 1,784 runs left; Nemotron done; T13 confirmed). **Handoff to Arsha, Nov 6** (the bundle, with Ritik's last push to `trackB-main`); B24 re-read from the bundle (read Nov 4) | **C19; check-in and merge (Nov 7)** | **L3 done (Nov 4: the LLM judges by the protocol, Ritik's re-look of 7 cells; rows 67 and 290 kept as recorded, Nov 5)** |
| Nov 8–12 | A40's training and E2 parts (from Nov 6), then A41 and A42 (pre-registered Nov 6); the 30's lines all ended Nov 6 and the Nov 6 07:00 rule said no cut, so the Nov 11 rule has nothing left to drop (the A39 log's §20) | B20's chains on Arsha's account; **check-in and merge (Nov 12)** | **C25; check-in and merge (Nov 12)** | **Gate 2 (Nov 8)** |
| Nov 13–18 | runs end Nov 15 (A39 on E2 and A40 read partial at 23:59 if not complete); A39 and A40 read Nov 17 | B20's runs end Nov 15 (read partial at 23:59 if not complete); B20 read (Nov 17); B18's table and figure (Nov 18); **check-ins Nov 15, 18** | **C20, C26 (Nov 15); C24 and slides 11–12 (Nov 18); check-ins Nov 15, 18** | the report from Nov 10 |
| Nov 18 | results freeze: all evaluation done by Nov 18, no new runs after it | | | |
| Nov 19–24 | Gate 3's final statement (Nov 20) | slides 2, 6, 7, 8 final; the report's Track B bullets (Nov 20) | the report's Track C bullets (Nov 20) | the report draft (Nov 22); rehearsal (Nov 23); final presentation and report (Nov 24) |

## Gates

- **Gate 1 (Oct 25): missed** (recorded Oct 27; TODO, G1). It needed real tool calls on 2+ providers (Voyager only so
  far), closed-model smoke tests (no keys) and the agents on 5 items (2 so far). The fallback written for this
  applies: **Track B narrows to the providers that work (Voyager, and Qwen3-8B on Sol in place of Ollama since Oct
  28), and Track C runs on Voyager only.** Paid calls wait for keys and Ritik's "go".
- **Gate 2 (Nov 8).** Is the tool-vs-user gap still clear with 3 runs per question and more models (Track B)?
  Answered: clear for all five models (B9; gpt-oss-20b at every effort, F37). And are the hand labels in, with Cohen's
  kappa per channel? L3: both sheets in Nov 3 (Ritik and AI rater 1, ChatGPT 5 Astra High), kappa under 0.6 in four
  of six cells. Read under the LLM-judge protocol (pre-registered Nov 4) on Nov 4: **the label part is not met**
  (F3).
  - **The statement, as of Nov 4, 18:00 (its label part read Nov 4 by the protocol).**
    - **Corrected Nov 4, 17:51:** rater 2 was an AI model (ChatGPT 5 Astra High), not Shrey; see the
      [17:42 log](../archive/sessions/2026-11-04/2026-11-04_1742_ALL_label-correction.md). The two-rater route
      (settle, tighten the guide, a fresh batch) no longer applies, and there is no settling call.
    - **The tool-vs-user gap is answered:** clear for all five models (B9; F15–F17, F29; gpt-oss-20b at every effort,
      F37).
    - **The hand labels aren't passed yet.** On the original independent sheets (L3, read Nov 3; they stay the record),
      Cohen's kappa, Ritik against AI rater 1 (human-vs-AI agreement, not inter-human), is under 0.6 in four of six
      cells:
      - the private reasoning: 0.627 overall, 0.288 on tool runs, 0.850 on user runs;
      - the final answer: 0.543, 0.589 and 0.425.
    - The "final" sheets of Nov 4 were made by the same AI model and carry Ritik's labels on the 25 disagreement
      cells. They are not used for kappa.
    - **Gate 2's label part is now read under the LLM-judge protocol** (pre-registered Nov 4,
      [the 17:45 log](../archive/sessions/2026-11-04/2026-11-04_1745_ALL_llm-judge-prereg.md)):
      - the final labels are Ritik's;
      - the AI judges are the reliability check;
      - the label part is **met** if Ritik against the AI judges' majority has kappa 0.6 or more in every cell;
        otherwise it is **"not met"**, stated plainly.
    - **Filled in Nov 4, 18:00** (read by the protocol at 17:56,
      [the results](../archive/sessions/2026-11-04/2026-11-04_1756_ALL_llm-judge-results.md); the rule didn't wait for
      Nov 8, since nothing left changes the number):
      - Ritik against the AI judges' majority, kappa: private 0.472 / 0.353 / 0.576 and final 0.234 / 0.223 / 0.201
        (all / tool / user);
      - every cell at 0.6 or more: **not met**;
      - so F3 stays a keyword count, and no acknowledgment claim rests on hand labels.
      - **Descriptive, not a gate claim** (added 18:22): the two capable judges agreed with the human labels (J-opus 0.669 and 0.837 on L3, 0.967 on L4; AI1 0.627, 0.543 and 0.930), while the 3-of-4 majority included two judges that did not follow the guide (near-constant labels on L4).
    - **Gate 2's statement:**
      - the tool-vs-user gap is clear on every model;
      - the label part is **not met** by the pre-registered rule.
      - The re-look is now 7 cells, where J-opus and AI1 agree against Ritik (the protocol's §11, post hoc). It
        doesn't change the verdict.
      - Done Nov 4, 21:31 ([log](../archive/sessions/2026-11-04/2026-11-04_2124_ALL_relook-recorded.md)): 4 changed
        to the judges' label, 3 kept; no reading changes.
    - L4 part 1 (Gate 3's labels, kappa 0.930, human-vs-AI agreement) is not part of Gate 2. If the gap isn't clear, the headline becomes the private-vs-final gap, the mechanism (Track A) and the agent
  results.
- **Gate 3 (Nov 20), its final statement.** Does a trained version follow fewer wrong hints on held-out questions
  without losing accuracy? Success:
  - the 95% bootstrap difference against the base model, clustered by question, excludes 0;
  - no-hint accuracy stays within 5 points;
  - the hiding check doesn't rise.

  Otherwise a negative result with the analysis. All systems run on the same Sol stack (F9).
  - **Met on Oct 31** (F28): all four trained versions pass.
  - The final statement is Nov 20 (it was due Nov 22). L4 part 1 was read Nov 3 (F28: LoRA's candidates rarely real);
    A18 was read Nov 3 (F39: training acts in the reasoning); the statement waits on A39's powered replication on E2
    (Nov 17).

## Final presentation map (about 12 slides)

The team writes the prose and the speaker notes. Every made slide's figure is in one style (Nov 4): 16:9, white, colors
by role, made by `tools/slide_figures.py` from the numbers-only summaries into `docs/paper/figures/` (PNG 2000 x 1125,
SVG, and a CSV of every plotted number). A `_slide` file is the 16:9 version of a figure made elsewhere, from the same
rows (the report and the supplement keep their own). "Waiting" marks a result not in yet: its spec is in
[`docs/paper/figures/WAITING.md`](paper/figures/WAITING.md), and nothing is drawn from it until it arrives.

**Nov 4, 16:20:** 10 slides made (1–4, 6–11), 2 waiting (5: L3; 12: C25, C20, C26), slide 13 written Nov 21–22.
Five made slides still wait on a later result (2: B20; 7: B24's two arms; 9: A39, in figures of its own; 10: B1R2;
11: C19). **Nov 5:** slide 10 no longer waited: B1R2 was dropped (F38). **Nov 6:** B1R2 revived (the A39 log's §21), so
slide 10's panel (b) gains B1R2 if it finishes, else stays B1 on the 30. Every made figure was regenerated by its script at 16:14 (`tools/slide_figures.py`,
`tools/paper_figures.py`): PNGs and CSVs byte-identical, so no number changed. The report's own three
(`readout_by_layer`, `reviewer_by_prompt`, `taught_loss`, from `tools/paper_figures.py`) keep the report's palette, not
this style; `taught_loss` (F20) has no 16:9 version.

| # | slide | figure (in `docs/paper/figures/`) | status | waits on | owner |
|---|---|---|---|---|---|
| 1 | **Where did that answer come from?** The question and the three levels | `three_levels.png` (a diagram, no data) | made Nov 1 | — | Ritik |
| 2 | **Tools pull harder than users.** Gate 2 on five models (F15–F17, F29, F37) | `gate2.png` (B18's rows) | made Nov 3 | B20, added if read (read Nov 17); final by Nov 20 | Arsha |
| 3 | **Level 1: three layers read the tool's letter.** F11, replicated on set A (F26); the heads (F12, F32) | `readout_by_layer_slide.png` (the report's `readout_by_layer` and the supplement's `readout_setA_vs_test2`) | made Nov 4 | — | Ritik |
| 4 | **Level 1 on a second model.** Qwen3-8B (A37; F36: replicates) | `readout_qwen8b.png` | made Nov 1 | — | Ritik |
| 5 | **Level 2: the private reasoning names it, the final answer doesn't** (F3, with L3's kappa) | listed: `cue_experiments_slide.png` (the supplement's `cue_experiments`); it shows C16–C18 (F31, F33, F34), not F3 | waiting | L3's labels under the LLM-judge protocol (kappa under 0.6 on Nov 3, Ritik against an AI rater; pre-registered Nov 4; Gate 2 Nov 8); F3 stays a keyword count until then | Ritik and Shrey |
| 6 | **Level 2: after a tool call, the answer goes bare.** F15, C4's control, F29; one instruction brings the source back without reducing deference (F25) | `bare_after_call.png` | made Nov 1 | — | Arsha |
| 7 | **Tool or authority?** (B16, F35; the authority dose, B24, F40) | `b16_authority.png` | made Nov 1 | B24's two arms beside B16's (B24 read Nov 4, F40; spec in WAITING.md's additions); Arsha, from Nov 6; final by Nov 20 | Ritik, then Arsha |
| 8 | **Thinking dose** (B17, F37; labelled §13) | `b17_effort.png` | made Nov 3 | — | Arsha |
| 9 | **The fix: training cuts following, but none beats one line** (F28, Gate 3; false disclosure from L4 part 1, read Nov 3) | `gate3_vs_base_slide.png` (`finetune/gate3.py`'s `gate3_vs_base`, the same rows) | made Nov 4 | A39, the powered replication on E2 (runs by Nov 15, read Nov 17; its own figures `a39_e2_fixes.png` and `a39_e2_parts.png`, spec in WAITING.md); Gate 3's final statement Nov 20 | Ritik |
| 10 | **Inside the fixed model: training acts in the reasoning** (A18, F39). And B1 at inference (A30, F38) | `readout_lora_vs_base.png` | made Nov 3 | — (Nov 5: B1R2, B1's labelled replication on E2, is not run: GPU time given to A40; F38) | Ritik |
| 11 | **Level 3: reviewers defer to the trace, and the citation is the cue.** F18, F22, F24, F30, F31, F33, F34, C19 | `trackC_reviewers_slide.png` and `reviewer_by_prompt_slide.png` (the supplement's `trackC_reviewers`, the report's `reviewer_by_prompt`) | made Nov 4 | C19, added when in (Nov 7) | Shrey |
| 12 | **Across agents, and what holds.** The handoff note loses the source (C25); pipeline vs model (C20); a realistic tool (C26); the checker | `c25_hops.png` (spec in `WAITING.md`; Shrey draws it under `docs/trackC/figures/`, Ritik places it at merge) | waiting | C25 (Nov 12), C20 and C26 (Nov 15); slides 11–12 Nov 18 | Shrey |
| 13 | **What to do about it, and the limits** | none | Nov 21–22 | — | everyone |

## Report outline (sections, one figure each)

Bullets only; the team writes the prose. [`docs/paper/OUTLINE.md`](paper/OUTLINE.md) has the threads' detailed
outlines and [`docs/paper/CLAIMS.md`](paper/CLAIMS.md) the claims.

1. **Introduction:** the question, the three levels, the contributions.
   - Figure: `three_levels.svg`.
2. **Setup:**
   - the models (Olmo 3 7B Think, Qwen3 30B Thinking and Instruct, Qwen3-8B, gpt-oss-20b in B17);
   - the five channels and the authority hint;
   - the questions;
   - the statistics: X of Y; a bootstrap clustered by question; at least 5 questions.
   - Figure: one prompt per channel, `docs/paper/figures/channels.svg` (made Nov 1, `tools/slide_figures.py`, from
     `tools/answer_key.py` itself).
3. **The failure:** tools pull harder (Gate 2); tool or authority (B16); thinking dose (B17).
   - Figure: `docs/paper/figures/gate2.png`, final.
4. **Level 1, inside the model:** the readout at 15/19/23; set A; Qwen3-8B; the heads.
   - Figure: `readout_by_layer.png`.
5. **Level 2, in the words:**
   - private vs final, with L3's kappa;
   - the bare answer after a call, and the good-lookup control;
   - the instruction (F25).
   - Figure: `bare_after_call.png`.
6. **Fixing it:**
   - the four trained versions and the one-line instruction (Gate 3);
   - false disclosure (L4);
   - inside the fixed model (A18);
   - B1 at inference (A30; A38 dropped); A39 on E2.
   - Figure: `gate3_vs_base.png`.
7. **Level 3, between agents:** reviewer deference by family; the citation as the cue (C16–C19).
   - Figure: `trackC_reviewers.png`.
8. **Across agents, and the pipeline:**
   - the handoff note (C25);
   - pipeline vs model (C20);
   - a realistic tool (C26);
   - the checker's record.
   - Figure: `c25_hops.png`.
9. **Limits and threats:** one tool format; one solver; keyword counts where the labels aren't in; the 30 evaluation
   questions; cross-day comparisons. Figure: none.
10. **Related work:** [`RELATED_WORK.md`](paper/RELATED_WORK.md). Figure: none.
11. **Conclusion and deployment:** the check that never sees the tool held; disclosure needs the source, not the
    authority. Figure: none.

**The supplement** is made by `tools/make_supplement.py`: pre-registrations, deviations, evidence and traps.

## Submission checklist, Nov 19–24

Added Nov 4, 16:20. What the course submission needs, who makes each and by when; everything reads only the results
frozen on Nov 18. The course's exact requirements (formats, length and time limits, where and how to submit, the form
of the contribution statement and of the AI-use disclosure) are not in the repo: each row says "confirm against the
course page". "Proposed" marks an owner or date set nowhere else in the repo, for Ritik to confirm.

| file | what | who | by when |
|---|---|---|---|
| the report: [`docs/paper/REPORT.md`](paper/REPORT.md) → the final report file | the prose from REPORT's bullets (numbers only from FINDINGS and CLAIMS), one figure a section (the outline above); each section by the owner its heading names (Ritik §1, §2, §3, §5, §7; Arsha §4, and §6 with Ritik, from `docs/trackB/REPORT_B.md`; Shrey §8, §9, from `docs/trackC/REPORT_C.md`; everyone §10–12); format and length: confirm against the course page | everyone; Ritik merges | Track B's and Track C's bullets Nov 20; the draft Nov 22; final Nov 24 |
| the supplement (`docs/paper/supplement/`) | regenerated from the frozen results by `tools/make_supplement.py` (TODO D6); whether it goes in as an appendix: confirm against the course page | Ritik | Nov 20 (D6) |
| the slides | the 13 slides of the presentation map above, figures from `docs/paper/figures/`, each slide by its owner (Ritik 1, 3, 4, 9, 10; Arsha 2, 6, 7, 8; Ritik and Shrey 5; Shrey 11, 12; everyone 13); the speaker notes by the team; one deck (proposed: Ritik assembles it); format and time limit: confirm against the course page | each slide's owner; the deck Ritik (proposed) | 11–12 Nov 18; 2 by Nov 20, 6–8 in Nov 19–24 (the calendar); 9 after Gate 3's final statement (Nov 20); 13 Nov 21–22; rehearsal Nov 23; presented Nov 24 |
| the code link | https://github.com/shrey-Bish/cse598-cot-faithfulness (`git remote get-url origin`): `main` with `trackB-main` and `trackC-main` merged at the Nov 18 check-in; the README's test and recompute commands; produced data local (gitignored), the numbers-only summaries tracked (Deliverables, 5); the graders' access: confirm against the course page | Ritik (the merges and the push) | the last merge Nov 18; in the submission folder Nov 21 |
| a contribution statement | who did what, by track and date, from "Who runs what" (top of this file) and each track's TODO: Track A Ritik; Track B Ritik to Nov 6, Arsha from Nov 6; Track C Shrey from Oct 30; the hand labels Ritik (L3, L4; the second sheets by an AI model, ChatGPT 5 Astra High, and the LLM judges, as the 17:42 and 17:45 logs record them; corrected Nov 4, 17:51: not Shrey); the report's sections and the slides by owner (above); form: confirm against the course page | each member their own lines; Ritik merges (proposed) | with the draft, Nov 22 (proposed) |
| an AI-use disclosure | which AI tools each member used, for what (code, analysis, writing), and what was checked by hand; how the hand labels were made: Ritik's by hand, the second sheets by ChatGPT 5 Astra High (run by Ritik with the guide and the blind sheets), and the LLM judges by their protocol (the 17:42 and 17:45 logs; corrected Nov 4, 17:51); Ritik's 7 re-look labels written in his own words and put into the five categories by Claude Code at his request (the 21:24 log); form and policy: confirm against the course page | each member for their own work; Ritik merges (proposed) | with the draft, Nov 22 (proposed) |
| the submission folder (TODO D13) | the report and slide files, the code link, the statement and the disclosure in one place | Ritik | Nov 21 (D13); submitted Nov 24 |

---

## Per-track design

The design notes that were here (Track A's Steps 11–13 and Sol job plan, Track B's and Track C's run notes, the hand
labels' plan, as of Oct 31) are kept word for word in
[`archive/superseded/PLAN_2026-10-31.md`](../archive/superseded/PLAN_2026-10-31.md). Current design: [`tracks/TRACK_A.md`](tracks/TRACK_A.md),
[`trackB/START_HERE.md`](trackB/START_HERE.md) and [`tracks/TRACK_B.md`](tracks/TRACK_B.md), [`trackC/START_HERE.md`](trackC/START_HERE.md), each
experiment's pre-registration log, and [`RUNBOOK.md`](RUNBOOK.md).

## Budget

**No paid calls:** the closed models were dropped for cost on Nov 3 (B21–B23); Voyager, Ollama and Sol are free.
**Spent: $0** (no `results/spend_log.jsonl`). The guard and prices below are kept for the record, unused.

- **The guard** (`providers/budget.py`): caps in `cot-disclosure/.env` (`OPENAI_CAP_USD`,
  `ANTHROPIC_CAP_USD`, `XAI_CAP_USD`, default 5). Before each paid call it assumes the worst case
  (prompt + `max_tokens`) and refuses a call that could pass the cap; after it, the priced usage is
  appended to `results/spend_log.jsonl`. `python -m providers.budget --status` (from
  `cot-disclosure/`); `progress/run_trackB.py --dry-run` before any sweep.
- **Keys** go in `cot-disclosure/.env` and are never printed. The adapters refuse a key equal to the
  Voyager key; the current `OPENAI_API_KEY` *is* the Voyager key.
- **Data rule:** only public benchmark questions go to outside providers.
- **Prices** (USD per 1M tokens, checked Oct 4, `configs/prices.yaml`): gpt-6-luna 0.10 / 0.50;
  claude-haiku-4-5 1.00 / 5.00; grok-4.3 1.25 / 2.50. The flagship models only fit spot checks.

## Deliverables

1. **Track B table:** hint following and admission per model × hint channel × thinking on/off,
   with 95% intervals and n.
2. **Hand labels** with Cohen's kappa per channel.
3. **Track C:** wrong answers shipped, catches, false alarms and cost per reviewer variant.
4. **Track A:** the look-inside analysis (FINDINGS F4–F14); the trained adapters and tags; the
   behavior-based evaluation; the mechanism check on the best version.
5. **Code and configs** on GitHub; produced data stays local (gitignored) with numbers-only
   summaries tracked. Final presentation and report on Nov 24 (rehearsal Nov 23; the Oct 31 program).

## Risks (Nov 4)

| risk | what we do |
|---|---|
| Sol is busy at times (`public` full on Nov 3 afternoon; htc isn't open to the class QoS) | 1:30 parts (2:00 from Nov 4, the A39 log's §14), up to 10 at once under the 960 GPU-minute cap, kept full day and night by the feeder (so no longer night shapes); times from `squeue --start`; the 30 is dropped on Nov 11 by its rule if time runs short. **Nov 5:** two accounts, each with its own 10 places and 960 GPU-minutes (B20 on Arsha's, with 3:00 lines); B1R2 dropped (GPU time given to A40); A39 on E2, A40 and B20 are read partial if not done by Nov 15 23:59 (the A39 log's §18, A40's §10, the B20 log's §19) |
| L3's labels don't reach 0.6 (Ritik against the AI judges' majority, the LLM-judge protocol) | Gate 2's label part is "not met", stated plainly; F3 stays a keyword count and no acknowledgment claim from labels goes in the report (corrected Nov 4, 17:51: the settle-tighten-fresh-batch route was for two human raters) |
| A model in B20 doesn't serve cleanly on vLLM 0.31.0 | its smoke stops it before any run; the fallback is the inserted tool turn, or the model is dropped by an amendment. **Nov 4:** both used (§15): Gemma's fallback; Granite's thinking-off setting dropped, since its off mode still thinks |
| A teammate's change touches shared code, or Ritik's touches theirs | the path allowlist, both ways (`tools/path_check.py` as pre-commit and pre-merge-commit hooks); Ritik reviews each merge on the check-in days |
