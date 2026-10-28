# Session log: Track C's 32B reviewer ready (smoke 5 of 5), Sol's morning work prepared (2026-10-28 00:32 MST)

Project: CSE 598 Group 10. Track A fine-tunes Olmo 3 7B Think on Sol (batch 2 training is running);
Track B measures hint following across open models (Voyager runs on the Mac tonight); Track C runs a
solver/reviewer/checker team on Voyager. Ritik is asleep until morning; this is the first log of the
overnight list (his message of 00:20).

## 1. Header

- **Time:** 2026-10-28 00:32 MST = 07:32 UTC.
- **Branch:** `trackA-nosol` at `1c66f33` before; one commit with this log. Not pushed since
  `cbbd936`. **Tests:** 391 pass.
- **Running:**
  - Track B, Qwen3 30B Thinking on Voyager under the power guard (AC, 100%): 155 of 663 runs since
    23:36. Qwen3 30B Instruct starts when it's done, then Olmo 3 7B Think.
  - Sol (from Ritik): lora 66759753 and tags 66759769 training; lora_tags 66759772 and lora_attn3
    66759822 after them; vllm_check 66760726 queued (setup_vllm 66760181 completed in 44 s).

## 2. What ran

| Command | Where | Calls | Duration | Failures |
|---|---|---|---|---|
| `client.list_models()` (Olmo entries) | Mac → Voyager | 1 | seconds | none |
| `voyager_template_check.py --model olmo3-32b-instruct --canary-specs` then `make_canary.py` | Mac → Voyager | 1 echo call | seconds | none |
| `voyager_template_check.py --model olmo3-32b-instruct` | Mac → Voyager | 5 + the canary | 1 min | none |
| `agents/run_team.py --live --n 5 --log team_smoke_olmo32b --reviewer-model voyager:olmo3-32b-instruct` | Mac → Voyager, beside Track B (shared 4 slots) | 35 | 00:20–00:27 | none: 5 of 5 cases complete |

## 3. Results

**A27, which Olmo 32B Voyager serves:** the instruct route (`olmo3-32b`, effort none) is Olmo 3.1
32B Instruct.
- `/v1/models` lists only the family `olmo3-32b`, and Hugging Face has no public Olmo 3 32B
  Instruct besides `allenai/Olmo-3.1-32B-Instruct` (revision `ac0587e4`).
- Voyager's prompt-token counts match that template exactly in 4 of 5 conditions, and −1 with the
  tool spec (none 349, user 365, pasted 382, system 318). The template carries 3.1's own default
  system prompt ("…date cutoff is December 2024…"), and the counts include it.
- Canary reference stored (`configs/canary/olmo3-32b-instruct.json`, 349 prompt tokens).

**The 32B reviewer's smoke** (the 5 C1 puzzles, tool team, 1 repeat; counts only, since 5 items can't
give a rate):
- **No-letter replies:** every one of 20 reviews gave a letter (C1's Olmo 3 7B Instruct: 6 of 20
  had none).
- **The checker:** flagged 3 of 3 bad lookups and 0 of 2 good ones.
- **The reviewer alone** corrected the solver's wrong answer:
  - with the answer only: 3 of 3
  - with the explanation: 3 of 3
  - with the private reasoning: 0 of 3
  - with the tool log: 0 of 3

  This is the Experiment A pattern again: what the reviewer reads about the lookup pulls it toward
  the wrong letter.
- **False alarm:** it kept the right answer in 7 of 8; the one change, with the explanation, shipped
  as a false alarm.
- **Shipped wrong:** 0 of 5 in three variants; 1 of 5 with the explanation (that false alarm).

**Sol, prepared for the morning (no runs):**
- **Batch 3 (evaluation): `finetune/gpu/plan_eval.py`.**
  - **Order:** base and prompt_only first (afterok vllm_check); each trained version afterok its
    training job and the check.
  - **Hours:** Step 2b's measured reply lengths per question × 930 runs, divided by a decoding rate.
  - **The rate:** a prior of 500–1,500 tokens/s until an evaluation job measures it. `eval_job` now
    writes its `eval_jobs.jsonl` row at the time-limit warning too.
  - **Parts:** a system over 8 h × 1/1.3 is split by question.
  - **What it reads on Sol:** the queue (dependencies still queued; room under the 10-job submit
    limit), `sacct` (how a finished dependency ended), `train/<version>/final/` and
    `vllm_check.json`.
  - **Today, with the prior:** each system is 2.2–6.5 h, in 2 parts with a 4:30 limit.
- **The Qwen3-8B download: a job without a GPU, `get_qwen8b`, the only job online.**
  - It downloads the pinned snapshot (`b968826d`) unless it is cached.
  - It checks every file's sha256 against the Hub's and records them, with the chat template's
    sha256, in `$TRACKA_OUT/trackb_qwen8b/snapshot.json`.
  - The GPU job checks that record offline. `trackb_qwen8b` may depend on `get_qwen8b` in
    submit.sh.
- **Qwen3-8B requests:**
  - **The budget:** no 16,000 default; every request carries 32,768 minus the prompt and the replies
    so far. A test checks it for thinking on and off: the request's max_tokens is over 16,000.
  - **Sampling:** temperature 0.6, top_p 0.95 and top_k 20 with thinking on and off.
  - **The chat template:** the server gets the snapshot's template as a file (`--chat-template`),
    and its sha256 is saved with every run (`chat_template_sha256`, in the records and the `_runs`
    rows).
  - **FINDINGS:** a new "Limitations" section notes that Qwen recommends 0.7 / 0.8 for non-thinking
    mode.
- **PLAN:** the refit hours and the batch-2 job ids and limits.

## 4. Files

- Code:
  - `agents/run_team.py`: the 32B default reviewer and `--log`.
  - `progress/voyager_template_check.py`: the 32B repo.
  - `finetune/gpu/plan_eval.py` (new).
  - `finetune/gpu/eval_job.py`: the `eval_jobs` row at the time-limit warning.
  - `progress/sol_trackB.py`: download, the snapshot record, the template.
  - `providers/sol_vllm.py`, `progress/run_trackB.py`: `chat_template_sha256`.
  - `finetune/gpu/sol/get_qwen8b.sbatch` (new), `run.sh`, `submit.sh`, `finetune/gpu/vllm_options.py`.
- Config: `configs/canary/olmo3-32b-instruct.json`.
- Tests: `test_trackA_plan_eval.py` (new), `test_trackB_sol.py`, `test_trackA_gpu_kit.py`.
- Summaries (numbers only): `results/summaries/trackC/team_smoke_olmo32b_summary.json`,
  `trackB/template_check.jsonl`, `voyager_canary.jsonl`.
- Docs: PLAN, FINDINGS (limitations), TODO (A16, A27, C3, C4), RUNBOOK, the GPU README,
  `handoff/TRACK_C.md` (C1 and the smoke).

## 5. For review

- **The decoding-rate prior (500–1,500 tokens/s) is not measured.** Once the first evaluation job
  ends, `plan_eval.py` uses the measured rate ±20% and re-plans.
- **A trained version can show COMPLETED while its training is unfinished.** That happens when a
  job is cut at its limit after saving a resume checkpoint. The planner then asks for a resubmit,
  checking `final/`, instead of planning that version's evaluation.
- **The smoke's private-reasoning and tool-log pattern (0 of 3 corrections) is 3 items.** C4 tests
  it.

## 6. Next

C4 waits for Qwen3 Thinking's Track B runs (about 03:45) and the steered export. Meanwhile: the Track
B table on the data so far, FINDINGS, and the logs. The 7 am daily log will carry the morning
commands.
