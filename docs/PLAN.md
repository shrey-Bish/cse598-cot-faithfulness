# Plan: Oct 31 – Nov 24 (CSE 598, Group 10)

Last updated: 2026-11-03 12:30 MST (the Nov 3 session: the fix's honest verdict; E2 and A39; Track B's handoff on
Nov 6; the doc audit). History: `git log -- docs/PLAN.md`; the Oct 31 version and the per-track design notes that
were below the gates, word for word, in [`archive/superseded/PLAN_2026-10-31.md`](../archive/superseded/PLAN_2026-10-31.md). Where things are:
- progress: [`STATUS.md`](status/STATUS.md);
- each result, with its numbers and source: [`FINDINGS.md`](FINDINGS.md);
- every open item, with owner and due date: [`TODO.md`](status/TODO.md) (Track A, labels, repo), Track B's
  [`TODO_B.md`](trackB/TODO_B.md) and Track C's [`TODO_C.md`](trackC/TODO_C.md);
- how to run each step: [`RUNBOOK.md`](RUNBOOK.md).

**Who runs what.**
- **Track A:** Ritik, to the end.
- **Track C:** Shrey's since Oct 30. Its experiments below are prepared now (code, CPU tests, a pre-registration log
  and a dry run each), and Shrey runs them on Voyager from about Nov 4.
- **Track B:** Arsha's from Nov 6 (Ritik, Nov 3: moved from Nov 3; the bundle rebuilt and sent Nov 6). B16 ran Oct 31–Nov 1 and is read (F35); B17 ran Nov 3 and is read (F37; run
  after its one-day window, pre-registration §13).
- **Sol:** Ritik submits every job, in this order to the freeze (Ritik, Nov 3): A18's copy-back and reading; the bench
  (R3); A39 on E2 (runs by Nov 15); B20; B1R2 only if about 60 GPU-hours remain by Nov 15 (RUNBOOK §0).
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
   - Open: does training stop that readout, or act after it (A18: its Sol jobs are done, not read)? Does a provenance
     wrapper or a combination beat the one-line instruction on 120 fresh questions (A39, E2)?
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
     - Do two raters agree on what the texts say (L3: kappa under 0.6 on Nov 3; settling, then a fresh batch)?
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
| 1 inside | A18 | Inside the fixed model: Steps 9 and 10 on LoRA's evaluation runs. Does training stop the readout at 15/19/23, or act after it? Tool-hint cases only in the primary, user hints apart (amended Nov 1) | Ritik | Nov 10 | **all Sol jobs COMPLETED Nov 3**; not read |
| 1 inside | A38 | STRETCH, only if B1 "works": prompt_only's note + B1 deployable, against each alone, same HF stack | Ritik | Nov 14 | **dropped Nov 3, as pre-registered:** B1's deployable span reads "ignores tools" (F38) |
| control | B16 | Tool or authority? The answer key's authority in the user's hint, against the tool channels | Ritik; Arsha, from Nov 6 | Nov 3 | **done Nov 1** (F35): tool beyond authority for Qwen3 Instruct's call (+75) and Thinking's pasted block (+12), authority moves Olmo more than its inserted turn (−14), no difference in the other three; cross-day (T11) |
| 2 words | B17 | Thinking dose: gpt-oss-20b on Sol at reasoning effort low, medium, high | Ritik submits; Arsha, from Nov 6 | Nov 12 | **done Nov 3** (F37): no change detected on both (following on the real call +7 [−1, +16]; bare after a call −5 [−10, 0]); run after its one-day window, kept by Ritik's decision before any result was read (§13) |
| 2 words | L3 | Gate 2's hand labels (F3 rests on them): kappa per channel | Ritik and Shrey | Nov 6 | **both sheets in Nov 3; kappa under 0.6 in four of six cells** (private 0.63, tool 0.29, user 0.85; final 0.54, tool 0.59, user 0.43): by the plan, settle the 25 disagreements, tighten the guide, label a fresh batch; no acknowledgment claim from labels until then |
| 2 words | L4 part 1 | Does training teach the model to claim checks it doesn't do? | Ritik and Shrey | Nov 14 | **read Nov 3** (F28; kappa 0.93): 1 to 2 of LoRA's 147 candidates claim a rejection they didn't act on; most say the hint shaped the answer; the raters could tell LoRA's style |
| 2 words | B18 | The final Track B table and one figure | Ritik; Arsha, from Nov 6 | Nov 18 | started Nov 3 (`tools/trackb_final.py`; slide 2) |
| 2 words | B20 | Open models from new families on Sol (Gemma 4 26B-A4B, Nemotron 3 Nano 30B-A3B, Granite 4.2 8B), thinking on and off | Ritik submits; Arsha, from Nov 6 | runs Nov 15, read Nov 17 | being prepared Nov 3 |
| 1 fix | E2 | A second, larger held-out set: 120 fresh MMLU-Pro questions from the evaluation categories | Ritik | Nov 3 | **done Nov 3** (sha256 `59c5c250…`) |
| 1 fix | A39 | Fix round 2 on E2: the wrapper, combinations, a powered replication of Gate 3 | Ritik | runs Nov 15, read Nov 17 | pre-registered Nov 3 |
| 1 fix | B1R2 | B1's deployable span on E2 (a labelled replication) | Ritik | Nov 15 | conditional on Sol time |
| 3 agents | C19 | Is an authority claim the cue (H34)? | Shrey | Nov 7 | prepared |
| 3 agents | C25 | Across agents (the centerpiece): solver with tool → a writer's handoff note → a decider that never sees the tool | Shrey | Nov 12 | prepared |
| 3 agents | C20 | Pipeline vs model: a blind reviewer; a tag the system attaches; the solver's own disclosure; the checker | Shrey | Nov 15 | prepared |
| 3 agents | C26 | SHOULD: a realistic tool, a retrieval passage from the wrong option's text, with no letter and no "answer key" | Shrey | Nov 15 | prepared |
| 3 agents | C22 | STRETCH: a second solver | Shrey | — | not prepared |
| 3 agents | C24 | Track C's figures and tables | Shrey | Nov 19 | — |
| labels | L4 part 2, L5 | SHOULD | two raters | — | built |
| dropped | B2 (A31), C21, C23 | dropped (scope, Oct 31) | — | — | — |

## The calendar

| when | Track A (Ritik) | Track B | Track C | labels, repo, report |
|---|---|---|---|---|
| Oct 31–Nov 3 | A37 done (Nov 1); B1 read (Nov 3); A38 dropped; E2 and A39 pre-registered | B16, B19 done; B17 done (Nov 3) | C19, C25, C20, C26 prepared and dry-run; Shrey's workspace (Nov 3) | L3 and L4 part 1 in (Nov 3) |
| Nov 4–7 | A18's copy-back and reading; the Sol bench; A39 on Sol | **Handoff to Arsha, Nov 6**; B20's downloads and smokes | C19 (Nov 7) | L3: settle, tighten, the fresh batch (before Nov 8) |
| Nov 8–12 | A18's verdict (Nov 10); A39 runs | B20 runs | C25 (Nov 12) | **Gate 2 (Nov 8)** |
| Nov 13–18 | A39 runs by Nov 15, read Nov 17; B1R2 only if it fits | B20 read (Nov 17); B18's table and figure (Nov 18) | C20 and C26 (Nov 15) | the report from Nov 10 |
| Nov 18 | results freeze: all evaluation done by Nov 18, no new runs after it | | | |

## Gates

- **Gate 1 (Oct 25): missed** (recorded Oct 27; TODO, G1). It needed real tool calls on 2+ providers (Voyager only so
  far), closed-model smoke tests (no keys) and the agents on 5 items (2 so far). The fallback written for this
  applies: **Track B narrows to the providers that work (Voyager, and Qwen3-8B on Sol in place of Ollama since Oct
  28), and Track C runs on Voyager only.** Paid calls wait for keys and Ritik's "go".
- **Gate 2 (Nov 8).** Is the tool-vs-user gap still clear with 3 runs per question and more models (Track B)?
  Answered: clear for all five models (B9; gpt-oss-20b at every effort, F37). And are the hand labels in, with Cohen's
  kappa per channel? L3: both sheets in Nov 3, kappa under 0.6 in four of six cells, so the label part isn't passed yet
  (settle, tighten the guide, a fresh batch; F3). If the gap isn't clear, the headline becomes the private-vs-final gap, the mechanism (Track A) and the agent
  results.
- **Gate 3 (Nov 20), its final statement.** Does a trained version follow fewer wrong hints on held-out questions
  without losing accuracy? Success:
  - the 95% bootstrap difference against the base model, clustered by question, excludes 0;
  - no-hint accuracy stays within 5 points;
  - the hiding check doesn't rise.

  Otherwise a negative result with the analysis. All systems run on the same Sol stack (F9).
  - **Met on Oct 31** (F28): all four trained versions pass.
  - The final statement is Nov 20 (it was due Nov 22). L4 part 1 was read Nov 3 (F28: LoRA's candidates rarely real);
    the statement waits on A18 (Nov 10) and A39's powered replication on E2 (Nov 17).

## Final presentation map (about 12 slides)

Bullets only; the team writes the prose and the speaker notes. Figure paths are from the repo root. The slide figures
are made by `tools/slide_figures.py` from the numbers-only summaries (16:9, PNG, SVG and a CSV of every plotted
number). "Waiting" marks a figure whose result isn't in yet: its spec (source file, axes, the pre-registered
comparison, owner, date) is in [`docs/paper/figures/WAITING.md`](paper/figures/WAITING.md), and no chart is drawn
until the result arrives.

1. **Where did that answer come from?** The question and the three levels.
   - Figure: `docs/paper/figures/three_levels.png` and `.svg` (a diagram, no data; `tools/slide_figures.py`).
   - Status: made Nov 1. Owner: Ritik.
2. **Tools pull harder than users.** Gate 2 on five models (F15–F17, F29, F37).
   - Figure: `docs/paper/figures/gate2.png` (made Nov 3 from B18's rows, `tools/trackb_final.py`).
   - Status: made Nov 3; Arsha finishes it (B20 if read) by Nov 20. Owner: Arsha.
3. **Level 1: three layers read the tool's letter.** F11, replicated on set A (F26); the heads (F12, F32).
   - Figure: `docs/paper/figures/readout_by_layer.png` and `docs/paper/supplement/figures/readout_setA_vs_test2.png`.
   - Status: done. Owner: Ritik.
4. **Level 1 on a second model.** Qwen3-8B (A37).
   - Figure: `docs/paper/figures/readout_qwen8b.png`.
   - Status: done Nov 1 (F36: replicates). Owner: Ritik.
5. **Level 2: the private reasoning names it, the final answer doesn't** (F3, with L3's kappa).
   - Figure: `docs/paper/supplement/figures/cue_experiments.png`.
   - Status: the caption waits on L3's settled labels (kappa under 0.6 on Nov 3). Owner: Ritik and Shrey.
6. **Level 2: after a tool call, the answer goes bare.** F15, C4's control, F29; one instruction brings the source
   back without reducing deference (F25).
   - Figure: `docs/paper/figures/bare_after_call.png` (`tools/slide_figures.py`: Track B's bare answers after a call,
     C4's right-or-wrong control, B15's instruction).
   - Status: made Nov 1. Owner: Arsha.
7. **Tool or authority?** (B16, F35)
   - Figure: `docs/paper/figures/b16_authority.png` (`tools/slide_figures.py`: each tool arm minus the user's
     authority claim, and following per arm).
   - Status: made Nov 1. Owner: Ritik, then Arsha.
8. **Thinking dose** (B17, F37).
   - Figure: `docs/paper/figures/b17_effort.png` (made Nov 3; labelled §13).
   - Status: made Nov 3 (`docs/paper/figures/b17_effort.png`, F37; labelled §13). Owner: Arsha.
9. **The fix: training cuts following, but none beats one line** (F28, Gate 3).
   - Figure: `cot-disclosure/results/summaries/trackA/gpu/eval/figures/gate3_vs_base.png`.
   - Status: done; false disclosure from L4 part 1 read Nov 3 (F28: LoRA's candidates rarely real); the final statement
     Nov 20. Owner: Ritik.
10. **Inside the fixed model.** Does training stop the readout or act after it (A18)? And B1 (A30).
    - Figure: `docs/paper/figures/readout_lora_vs_base.png` (waiting; spec in `WAITING.md`).
    - Status: waiting on A18 (due Nov 10); B1 read Nov 3 (F38: "ignores tools" and "no effect"). Owner: Ritik.
11. **Level 3: reviewers defer to the trace, and the citation is the cue.** F18, F22, F24, F30, F31, F33, F34, C19.
    - Figure: `docs/paper/supplement/figures/trackC_reviewers.png` and `docs/paper/figures/reviewer_by_prompt.png`.
    - Status: done; C19 due Nov 7. Owner: Shrey.
12. **Across agents, and what holds.** The handoff note loses the source (C25); pipeline vs model (C20); a
    realistic tool (C26); the checker.
    - Figure: `c25_hops.png` (spec in `WAITING.md`): Shrey draws it under `docs/trackC/figures/`; Ritik places it at
      merge.
    - Status: waiting on C25 (Nov 12), C20 and C26 (Nov 15). Owner: Shrey.
13. **What to do about it, and the limits.**
    - Figure: none.
    - Status: Nov 21–22. Owner: everyone.

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

---

## Per-track design

The design notes that were here (Track A's Steps 11–13 and Sol job plan, Track B's and Track C's run notes, the hand
labels' plan, as of Oct 31) are kept word for word in
[`archive/superseded/PLAN_2026-10-31.md`](../archive/superseded/PLAN_2026-10-31.md). Current design: [`tracks/TRACK_A.md`](tracks/TRACK_A.md),
[`trackB/START_HERE.md`](trackB/START_HERE.md) and [`tracks/TRACK_B.md`](tracks/TRACK_B.md), [`trackC/START_HERE.md`](trackC/START_HERE.md), each
experiment's pre-registration log, and [`RUNBOOK.md`](RUNBOOK.md).

## Budget

**About $15 in total:** $5 each for OpenAI, Anthropic and xAI. Voyager, Ollama and Sol are free.
**Spent so far: $0** (no `results/spend_log.jsonl`).

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

## Risks (Nov 3)

| risk | what we do |
|---|---|
| Sol's queue is slow for 4-GPU jobs | the bench (R3) measures it first; 1-GPU jobs are the fallback; B1R2 gives way first |
| L3's labels don't reach 0.6 again | the plan's steps (settle, tighten, a fresh batch); F3 stays a keyword count and no acknowledgment claim from labels goes in the report |
| A model in B20 doesn't serve cleanly on vLLM 0.31.0 | its smoke stops it before any run; the fallback is the inserted tool turn, or the model is dropped by an amendment |
| A teammate's change touches shared code | Track C's path allowlist refuses it; Ritik reviews each merge |
