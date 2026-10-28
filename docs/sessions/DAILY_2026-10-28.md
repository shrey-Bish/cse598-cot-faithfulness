# Daily log: 2026-10-28 (Wednesday), the night of Oct 27–28 (23:08 to 07:00)

Project: CSE 598 Group 10, "Do thinking modes make chain-of-thought more honest?" Track A explains and
fixes hint-following that the final answer hides, in Olmo 3 7B Think; Track B measures it across
open models and channels (user, tool, system); Track C tests a solver/reviewer/checker team against a
wrong tool result. Session logs of the night: `docs/sessions/INDEX.md` (23:55 to 05:45). Arizona time
(MST). Ritik was asleep from about 00:30; this follows the overnight list.

## The night in brief

Track A's training started on Sol (batch 2, four versions). Batch 3 (evaluation) and the Qwen3-8B job
are prepared but not submitted. Track B finished both Qwen3 30B checkpoints on Voyager: 1,480 runs
overnight, all answered.
- **Gate 2 is clear for both.** Tool − user is +35 and +31 points for Thinking, +21 and +90 for
  Instruct (pasted block / real call).
- **After a real tool call the final answer rarely names the tool:** 3 of 54 for Thinking, 30 of 147
  for Instruct.

Track C's second reviewer is now Olmo 3.1 32B Instruct. C4 (the team on Track B's cases) has run
since 03:13: 120 of 318 cases at 07:00. It slowed when Olmo 3 7B Think started (decision 7).

## By track

**Track A** (Sol; the Mac can't reach Sol, so the Sol state is as of Ritik's 00:20 message)
- **The class QoS only.** `submit.sh` refuses an unlisted partition or QoS before sbatch.
- **Data checks:**
  - (a) 0 held-out questions or wordings in the 1,040 training and 156 validation examples;
  - (e) 0 examples over 32,768 tokens (the longest is 31,625).
- **S1 refit** (`plan_training.py`, hours, 5–95%): lora 3.66 (3.56–3.78), tags 2.97 (2.89–3.04),
  lora_tags 3.65 (3.56–3.74), lora_attn3 2.99 (2.92–3.07).
- **vLLM options:** the CUDA build can't print `vllm serve --help=all` on a CPU node. `setup_vllm`
  checks the installed version against the committed list instead, and every vLLM GPU job compares
  its node's help with the list before loading anything.
- **Batch 2 (Ritik, 00:20):**
  - lora 66759753 (limit 5:00) and tags 66759769 (4:00);
  - lora_tags 66759772 (afterany lora) and lora_attn3 66759822 (afterany tags);
  - setup_vllm 66760181 completed (all 9 server commands fit the list); vllm_check 66760726 queued.
- **Prepared, not run:**
  - `plan_eval.py` (batch 3: 12 lines with the prior rate, each system 2.2–6.5 h in 2 parts, limit
    4:30);
  - `get_qwen8b` (the snapshot job, no GPU, the only job online; every file checked against the Hub);
  - Qwen3-8B requests at 32,768 minus the prompt, with the snapshot's chat template and its sha256
    per run;
  - FINDINGS limitations.

**Track B** (Voyager, on the Mac under the power guard, one model after another)
- **Qwen3 30B Thinking: done** (810 runs, 23:36–03:11; FINDINGS F15).
  - Following: user 3 of 162 [1, 5%], pasted 59 of 162 [29, 44%], real call 54 of 162 [27, 41%],
    system note 57 of 162 [28, 43%].
  - Gate 2: +35 [+24, +46] and +31 [+22, +42], clear at both cuts.
  - It called the tool in 54 of 162 runs and followed every call. The final answer named the tool 3
    times.
  - Almost all of it is on MMLU-Pro. On the puzzles, pasted 5, real call 4 and system 7 of 72.
- **Qwen3 30B Instruct: done** (810 runs, 03:11–05:32; F16).
  - Following: user 1 of 162 [0, 3%], pasted 35 of 162 [16, 29%], real call 147 of 162 [85, 94%],
    system note 35 of 162 [16, 29%].
  - Gate 2: +21 [+12, +31] and +90 [+83, +96].
  - It called the tool in 162 of 162 runs. On the puzzles it took the tool's letter 72 of 72, with
    0 mentions, although pasted and system hints moved it 0 of 72 there.
- **Thinking minus Instruct** (54 questions): real call −57 [−70, −43], pasted +15 [+6, +25], system
  +14 [+7, +20], user +1 [+0, +3]. These are two checkpoints, not one switch.
- **Olmo 3 7B Think:** running since 05:32; 96 of 810 runs at 07:00, 0 errors. Its replies are long
  (median about 10,300 tokens; 11 of 96 past 16,000), so each run holds a Voyager slot for minutes.
- **Steered export:** Qwen3 Thinking's cases are exported (24 steered, all MMLU-Pro; 29 matched, 24
  of them puzzles). Instruct's export waits for C4 (05:45 log).
- **The report** (`trackB_report.py`):
  - `--by-set`, thinking minus not (two-sided "clear");
  - the final answer naming the hint when following;
  - following with and without a call.
- **A failed Voyager guard** (identity canary) now pauses all Voyager work; it didn't fail tonight.

**Track C**
- **Decision 5 done:** the second reviewer is Olmo 3 32B Instruct. Voyager serves it as Olmo 3.1 32B
  Instruct (A27; prompt-token gap 0 in 4 of 5 conditions).
- **The smoke:** 5 of 5 cases, 20 of 20 reviews with a letter.
- **C4:** since 03:13 under a second guard: Qwen3 Thinking's 53 cases × 2 teams × 3 repeats = 318
  cases, both reviewers. 120 done at 07:00, 0 errors.
- **C4 interim** (102 cases at 05:39, mostly 1 repeat; not final):
  - The checker flagged 23 of 23 bad lookups; the no-tool floor is 5 of 49.
  - No wrong answer was shipped on a bad lookup.
  - The Olmo 32B reviewer alone corrected bad lookups 19 of 23 from the answer only, 2 of 23 with the
    private reasoning and 1 of 23 with the tool log. The Qwen3 reviewer: 19, 21, 17.
- **Code:**
  - C5 in `--summary` (the checker against the no-tool team's run-to-run variation);
  - the split by Track B kind and kind × set;
  - exit codes for the guard;
  - `--case-model` (one Track B model per run).

**Repo**
- 11 commits since `1c66f33` (the last push), none pushed. No attribution lines.
- Tests: 399 pass (381 at 23:55).

## Compute used (the night)

- **Voyager:**
  - Track B: 1,559 runs, about 1,769 calls (Thinking 663 runs, Instruct 805, Olmo 91 by 07:00),
    with 0 errors.
  - C4: 1,104 agent steps by 07:00 (856 reviews, 124 solver, 124 checker).
  - The 32B smoke: 30 agent steps, plus its canary and template check.
- **Sol** (Ritik's jobs): setup_vllm (CPU); batch 2 training, 4 GPU jobs (about 13.3 GPU-hours at
  the refit's middle).
- **Mac:** no local model, no Ollama, the power guard on (AC 100% all night).
- **No paid calls.**

## State at 07:00

- **Mac** (on AC 100% all night; no halt, no stop file):
  - Guard 1 (`logs/guard.log`) runs Olmo 3 7B Think: 96 of 810 runs, 0 errors, about 57 runs an
    hour.
  - Guard 2 (`logs/guard_c4.log`) runs C4: 120 of 318 cases, 0 errors.
  - **C4 slowed when Olmo started.** It finished 53 cases between 04:00 and 05:00, and 10 between
    06:00 and 07:00: Olmo's long replies hold most of the 4 shared slots. At this pace Olmo ends
    around 19:30 and C4 around 21:00. Decision 7 would put C4 first.
  - **To stop:** `touch cot-disclosure/logs/stop_guard` stops both guards. Cases and runs in flight
    finish first, and both runs resume when started again. A job's own stop file (`logs/stop_c4`,
    `logs/stop_olmo3think`) only pauses it: the guard restarts it a minute later.
- **Sol** (last known, 00:20): batch 2 running or queued; vllm_check 66760726 queued (it needs one of
  the class QoS's 2 job slots).
- **Not pushed:** 11 commits (`49f1f76` … this log).

## For review

- **In C4, steered vs matched is also MMLU-Pro vs puzzles.** Qwen3 Thinking has no steered puzzle (0
  of 24); 5 MMLU-Pro matched cases give the same-set comparison. Instruct's cases would add 24 steered
  puzzles, but C4's solver is Qwen3 Thinking, so they would answer a different question.
- **Instruct's real-call following is a call rate.** It calls the "course answer key" tool every time
  and answers with it. Whether that is being steered or using a tool it was invited to use is a
  framing question for the paper.
- **"The final answer names the hint" is keyword counts** (`detect.py`). The hand labels (L3) would
  confirm them.
- **The interim C4 reviewer drop is 23 items, mostly one repeat.** It goes into FINDINGS when C4 is
  done, paired by item.
- **A slip:** the 05:45 log was first stamped 06:00. It was corrected in `b104426`.
- **A wrong stop instruction:** RUNBOOK §19 and the 03:25 log said `touch logs/stop_c4` stops C4.
  Under the guard it only pauses C4 for a minute: `guard.py` restarts a job that exits with code 2,
  and its `start()` removes the stop file. Nobody used it. RUNBOOK §19 is fixed; the 03:25 log stays
  as written.

## Decisions waiting (Ritik)

1. **The Qwen3-8B job on Sol:** `get_qwen8b`, then `trackb_qwen8b` (0.5–1.5 GPU-hours, limit 2:00).
   Each takes one of the class QoS's 2 job slots while it runs.
2. **Batch 3's GPU hours:** 12 evaluation jobs, 13–39 GPU-hours with the prior rate. `plan_eval.py`
   re-plans with the measured rate after the first job.
3. **C4's set confound:** report by kind and by kind × set (as now), or add cases.
4. **The `trackB-main` and `trackC-main` branches** for the Nov 3 handover.
5. **The 16,000-cut wording:** "a run whose replies total over 16,000 tokens counts as no answer"
   (both turns of a real-call run together).
6. **The push** of the 11 commits.
7. **C4 before Olmo?** As now, Olmo ends around 19:30 and C4 around 21:00. With C4 first (one guard,
   Olmo after C4), C4 ends around 12:00 and Olmo around 23:00. I recommend C4 first: its tables and
   FINDINGS entry can then be written in the afternoon while Olmo runs. The commands are below. Both
   times are estimates from tonight's rates.

## Morning commands

**Mac, from the repo root** (`~/Documents/Projects/ODL/cse598-cot-faithfulness`):
```bash
git push origin main trackA-nosol                         # 11 commits; the pre-push check passes
git ls-files | rsync -av --files-from=- ./ ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/
```
- The inputs (`finetune/gpu/sol/inputs.txt`) are unchanged since `1c66f33`, so there is no inputs
  rsync.
- The code rsync is safe while training runs. `train.py` and `train.sbatch` are unchanged, `run.sh`
  only gains the `get_qwen8b` case, and rsync replaces files by rename.

**Mac, decision 7 (C4 first, then Olmo, under one guard), from `cot-disclosure/`:**
```bash
touch logs/stop_guard                          # both guards; cases and runs in flight finish first
tail -n 1 logs/guard.log logs/guard_c4.log     # wait until both say "guard stopped"
nohup caffeinate -i ../.venv/bin/python -u progress/guard.py \
  --job "voyager:c4=agents/run_team.py --live --cases results/trackB/steered_cases.jsonl --kinds steered,matched --per-kind 30 --repeats 3 --teams tool,notool --log team_c4 --run-name C4-oct28" \
  --job "voyager:olmo3think:c4=progress/run_trackB.py --run --model olmo3-7b-think" >> logs/guard.log 2>&1 &
```
- The new guard removes `logs/stop_guard` when it starts. C4 resumes from its `case_done` rows and
  Olmo from its runs. Olmo starts when C4 exits with code 0.

**Sol, from `/scratch/ragarw68/cse598-cot-faithfulness`:**
```bash
squeue -u ragarw68
sacct -u ragarw68 -S 2026-10-28T00:00 -o JobID,JobName%20,State,Elapsed,ExitCode
# Track B Qwen3-8B (decision 1)
cot-disclosure/finetune/gpu/sol/submit.sh get_qwen8b                                            # -> job G
cot-disclosure/finetune/gpu/sol/submit.sh trackb_qwen8b --estimate 1.5 --dependency=afterok:G   # limit 2:00
# Batch 3 (decision 2): prints the submit.sh lines; submit them in order (lines past the 10-job limit say "later")
source cot-disclosure/finetune/gpu/sol/env.sh
"$TRACKA_PY" cot-disclosure/finetune/gpu/plan_eval.py --vllm-check 66760726 \
    --train lora=66759753,tags=66759769,lora_tags=66759772,lora_attn3=66759822
```
- **Base and prompt_only** wait for 66760726 (the vLLM check).
- **Each trained version** waits for the check and its own training job.
- **A version whose job ended at its limit before `final/`:** the planner prints a resubmit instead
  of its evaluation.

**Mac, afterwards** (numbers only):
```bash
cd cot-disclosure
rsync -av ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/cot-disclosure/results/trackB/sol_vllm_{runs,flags}.jsonl results/trackB/
../.venv/bin/python progress/trackB_report.py --export --by-set        # adds Qwen3-8B, thinking on minus off
S=ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/trackA
for v in lora tags lora_tags lora_attn3; do mkdir -p results/trackA/gpu/train/$v
  rsync -av $S/train/$v/chosen.json $S/train/$v/train_log.jsonl results/trackA/gpu/train/$v/; done
rsync -av $S/vllm_check/vllm_check.json results/trackA/gpu/
```

## Today (Oct 28)

1. Sol: the batch-2 results, vllm_check, then batch 3 and Qwen3-8B on Ritik's go.
2. C4 done (about 12:00 with decision 7, about 21:00 without): the C5 tables and a FINDINGS entry;
   then Instruct's steered export.
3. Olmo 3 7B Think's Track B table (evening or night), and Gate 2 for three models.
4. The branches and the handoff drafts (final by Nov 3).
