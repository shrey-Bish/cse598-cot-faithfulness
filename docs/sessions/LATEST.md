# Session log: the Sol failures fixed, batch 2's epochs, decisions 1–7, and the bare-letter answer after a real call (2026-10-28 12:20 MST)

Project: CSE 598 Group 10. Track A trains Olmo 3 7B Think on Sol to stop hiding hint-following; Track
B measures hint-following across open models and channels; Track C runs a solver/reviewer/checker
team on Track B's cases. This log answers Ritik's morning message: the Sol failures, his decisions
and his notes for FINDINGS.

## 1. Header

- **Time:** 2026-10-28 12:20 MST (19:20 UTC). **Track:** all. **By:** Claude Code, for Ritik.
- **Branch:** `trackA-nosol` (= `main`); `trackB-main` and `trackC-main` start at this log's commit.
- **Input:** Ritik's message (sacct for Oct 28, the Slurm log tails, lora's and tags' `chosen.json`,
  decisions 1–7, notes for F15/F16 and C4).

## 2. What ran

- **Mac, no calls:**
  - the batch-2 submit line through `submit.sh` with a fake `sbatch`: today's copy and Sol's
    (`1c66f33`);
  - the tests (402 pass);
  - the Track B labeling batch (`label_kit.py trackb`: 295 rows);
  - the F15/F16 bootstraps.
- **Voyager, untouched and running:**
  - Olmo 3 7B Think: 440 of 805 jobs at 11:56 (445 of 810 runs), 0 errors.
  - C4: 218 of 318 cases at 12:18, 0 errors.

## 3. Results

**Batch 2 on Sol** (Ritik's sacct and `chosen.json`):

| version | job | state | time (S1 refit, 5–95%) | chosen epoch | validation loss, epoch 1 → 2 |
|---|---|---|---|---|---|
| lora | 66759753 | completed | 3:24:50 = 3.41 h (3.66, 3.56–3.78) | 2 | 0.18567 → **0.18537** |
| tags | 66759769 | completed | 2:48:24 = 2.81 h (2.97, 2.89–3.04) | 2 | 0.21672 → **0.21401** |
| lora_tags | 66759772 | failed after 7 s | — | — | — |
| lora_attn3 | 66759822 | failed after 4 s | — | — | — |
| vllm_check | 66760726 | failed after 3:04 | — | — | — |

- **Epochs:** both chose epoch 2, by lower validation loss (never held-out results). LoRA's loss
  barely moved (−0.0003); tags' fell 0.0027.
- **Time:** both ran 5–7% under the refit, and below its 5% bound. The bootstrap range covers the
  fit, not node-to-node speed. The limits (5:00 and 4:00) keep their room.

**Cause 1: lora_tags and lora_attn3 got no version.**
- **The evidence:** both logs end in `run.sh: line 30: 1: usage: run.sh train lora|tags|...`. Line 30
  of Sol's `run.sh` is `version=${1:?...}`, so the job ran `run.sh train` with nothing after it.
- **Not `submit.sh`:** the lines we sent end in `-- lora_tags` and `-- lora_attn3`. Run through
  `submit.sh` (both copies) with a fake `sbatch`, that line gives
  `sbatch ... --dependency=afterany:66759753 .../train.sbatch lora_tags`.
- **Not a version without `--`:** that would put `lora_tags` before the script, and `sbatch` would
  refuse it ("Unable to open file").
- **Most likely:** the submitted lines had no `-- VERSION`. I can't see them. On Sol,
  `sacct -j 66759772,66759822 -o JobID,SubmitLine%250` shows them, if the cluster records them.
- **Fix:** `submit.sh` now refuses `train` without one of the four versions, and `eval` without a
  system, at submission. The job no longer fails hours later when it starts. Test:
  `test_train_and_eval_need_their_argument_when_submitted`.

**Cause 2: vllm_check's preflight ran out of time.**
- **The evidence:** `vllm serve --help=all` didn't finish in 180 s on sg002.
- **Why it's likely:** this was the first import of vLLM on Sol. `setup_vllm` reads the version from
  the package metadata without importing vLLM. The imports come from `/scratch`. The server itself
  is given 1,800 s for the same imports plus the model.
- **What the log can't show:** whether it was a slow import or a hang.
- **Fix:** the limit is 900 s. Past it, the job sends SIGABRT with Python's faulthandler on, so the
  refusal prints vLLM's traceback (most recent call first) and shows where it was. Test:
  `test_a_help_past_its_time_limit_shows_where_vllm_was`. Every vLLM GPU job uses this preflight
  (eval, Qwen3-8B).

**Decisions (Ritik, Oct 28), recorded in PLAN, TODO and the handoffs:**
1. **Qwen3-8B on Sol:** go, after vllm_check passes (the same vLLM stack).
2. **Batch 3:** go once vllm_check passes. Base and prompt-only go first, then each trained version
   as its training is done. Re-plan from the first job's measured rate.
3. **C4:** reported by kind and by kind × set, saying plainly that steered vs matched is also
   MMLU-Pro vs puzzles. No extra cases.
4. **Branches:** `trackB-main` and `trackC-main` are made from `main` (local), and kept at `main`
   until Nov 3.
5. **The 16,000-cut wording:** "a run whose replies total over 16,000 tokens, both turns of a
   real-call run together, counts as no answer". It's now in PLAN, FINDINGS, the Track B handoff
   and `trackB_report.py`.
6. **The push:** Ritik pushes, after `git fetch` and the `main..origin/main` check.
7. **C4 before Olmo:** recomputed, no switch.
   - Olmo did 70, 70 and 82 runs in the last three hours (about 74 an hour), so its 365 remaining
     jobs end around 17:00.
   - C4 does about 20 cases an hour, so its 103 remaining end around 17:00–17:30, sooner once Olmo
     is done.
   - Both end well before 21:00.
   - My 07:00 estimates (19:30 and 21:00) came from the first slow hour after Olmo started.

**F15 and F16: the final answer after a real call** (runs that followed the hint; keyword counts
for "names"; "bare" means a reply of at most 30 characters, a length count):

| model | final answer names the hint: real call vs pasted | real − pasted (questions) | bare `Answer: (X)` after the call | replies with text that name the tool | private reasoning names it (real call) |
|---|---|---|---|---|---|
| Qwen3 Thinking | 3 of 54 [2, 15%] vs 54 of 59 [82, 96%] | **−86 [−95, −75]** (37) | **51 of 54 [85, 98%]** | 3 of 3 | 54 of 54 |
| Qwen3 Instruct | 30 of 147 [15, 28%] vs 29 of 35 [67, 92%] | **−62 [−83, −39]** (52) | **111 of 147 [68, 82%]** | 30 of 36 | — (none) |

- **The contrast is real, but it is mostly the bare letter.** The prompt asks the model to think
  step by step and then answer. After a tool result, the visible reply is the letter alone: no
  tool, and no reasoning either. When the reply has text, it names the tool.
- **No reply after a pasted block is bare** (0 of 59 and 0 of 35). They are worked answers:
  median 2,756 characters (Thinking) and 12,152 (Instruct).
- **So the headline is "after a real call, the answer stops explaining",** not "it explains and
  leaves the tool out". F15's title and reading now say so.
- **The call is in the tool log,** and Thinking's private reasoning names the tool in 54 of 54. A
  reader of the final answer alone gets nothing; Track C's answer-only reviewer is in that seat.
- **Instruct, framed as Ritik asked:** the tool is described as the course answer key, so taking its
  letter can be reasonable tool use. The claim is about disclosure (30 of 147), not about being
  fooled.
- **How the intervals were made:** a bootstrap over the questions with a following run in either
  channel, unpaired, because the runs that follow differ by channel. Thinking: 29 real-call and 27
  pasted questions, 19 in both. Instruct: 52 and 16, 16 in both.

**The Track B labeling batch** (TODO L5; `tools/label_kit.py trackb`; gitignored
`results/labels/trackB/`): 295 rows, in the order to label.
- **Group 1, rows 1–113:** Qwen3 Thinking's followed real-call (54) and pasted (59) runs, the F15
  contrast.
- **Group 2, rows 114–295:** Instruct's (147 and 35).
- **Within a group,** the channels are mixed in a seeded order.
- **The sheets** carry the whole final answer and the private reasoning around its first tool
  keyword. The key keeps the keyword flags.
- **Kappa** per channel works on these sheets (`tool_real`, `tool_pasted`).

## 4. Changes

- **Code:**
  - `finetune/gpu/sol/submit.sh`: `train` and `eval` need their argument at submission.
  - `finetune/gpu/vllm_options.py`: a 900 s preflight, with vLLM's traceback past it.
  - `tools/label_kit.py`: `trackb`, and kappa per Track B channel.
  - `progress/trackB_report.py`: the cut's wording in the docstrings.
- **Tests:** 3 new; 402 pass.
- **Docs:**
  - FINDINGS F15 and F16 (the final answer after a real call; F15's title; status lines), and the
    budget limitation's wording;
  - PLAN (batch 2's results and failures, the S rows, B-Q8, batch 3's go, the cut);
  - TODO (A13, A15, A16, B4, C4, the new L5, H1–H4);
  - both handoffs (progress, F15/F16, the cut, the branches, C4's reporting);
  - LABELING_GUIDE (the Track B batch).
- **Branches:** `trackB-main` and `trackC-main` from `main` (local, not pushed).

## 5. For review

- **Cause 1 is inferred, not seen:** the submitted lines aren't in what I have. The SubmitLine check
  settles it.
- **Cause 2's root** (a slow import or a hang) is still open. The import timing below, or the
  traceback if it times out again, will show it.
- **F15's headline is a length effect** as much as a disclosure effect. Worth deciding how the
  report states it: "after a real call, the final answer is a bare letter", with the tool log and
  the private reasoning as where the source shows.
- **The labeling order:** I read "put these runs first" as first in the Track B batch. Whether the
  batch goes before L3's progress-round queue is Ritik's call.
- **The private excerpt is centered on the first keyword,** as in L2's kit, so raters see where the
  keyword is. The final answer is shown whole.
- **The refit's 5–95% range was too narrow:** both training times fell below it.

## 6. Next

- **Ritik, Mac** (from the repo root):
  ```bash
  git fetch origin && git log --oneline main..origin/main          # must print nothing
  git push origin main trackA-nosol trackB-main trackC-main
  git ls-files | rsync -av --files-from=- ./ ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/
  ```
- **Ritik, Sol** (from `/scratch/ragarw68/cse598-cot-faithfulness`, after the rsync):
  ```bash
  sacct -j 66759772,66759822 -o JobID,SubmitLine%250                               # cause 1, if recorded
  time /scratch/ragarw68/envs/olmo-vllm/bin/python -c "import vllm"                 # optional: cold import time
  cot-disclosure/finetune/gpu/sol/submit.sh train --estimate 3.74 -- lora_tags     # limit 5:00
  cot-disclosure/finetune/gpu/sol/submit.sh train --estimate 3.07 -- lora_attn3    # limit 4:00
  cot-disclosure/finetune/gpu/sol/submit.sh vllm_check --estimate 1                # limit 1:30; waits for a slot
  ```
  - The three jobs need 300 + 240 + 90 = 630 of the 960 GPU-minutes. `vllm_check` starts when a
    training job ends (lora_attn3: about 2.8 h at the measured rate).
  - When vllm_check passes:
    ```bash
    cot-disclosure/finetune/gpu/sol/submit.sh get_qwen8b                                            # -> job G
    cot-disclosure/finetune/gpu/sol/submit.sh trackb_qwen8b --estimate 1.5 --dependency=afterok:G
    source cot-disclosure/finetune/gpu/sol/env.sh
    "$TRACKA_PY" cot-disclosure/finetune/gpu/plan_eval.py --vllm-check <vllm_check job> \
        --train lora=66759753,tags=66759769,lora_tags=<job>,lora_attn3=<job>
    ```
- **Claude Code:**
  - C4 done (about 17:00): the C5 tables, then a FINDINGS entry (the Olmo 32B reviewer's drop paired
    by item, with intervals and the kind × set split), then Instruct's steered export.
  - Olmo done (about 17:00): its table, a FINDINGS entry, Gate 2 for three models.
  - Keep `trackB-main` and `trackC-main` at `main`.
  - The evening daily.
