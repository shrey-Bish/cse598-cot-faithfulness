# Runbook: how to run every step

**Edited by:** Ritik.

Last updated: 2026-11-04 (the Sol order and its real limit, §0; labels, §15; the pre-commit hook, §17; history: `git log -- docs/RUNBOOK.md`). One page per step: what it does, where it runs, the commands in order,
inputs and outputs, how long it takes, and what to check. Written so anyone in the group can run a
step without asking. Results and their status are in [`FINDINGS.md`](FINDINGS.md); open work in
[`TODO.md`](status/TODO.md), [`TODO_B.md`](trackB/TODO_B.md) and [`TODO_C.md`](trackC/TODO_C.md).

**Conventions.** Mac commands run from `cot-disclosure/` with the repo's virtual environment, written
`../.venv/bin/python`. Sol commands run from the clone's root, `/scratch/ragarw68/cse598-cot-faithfulness`.
"Voyager" means ASU's model API, called from the Mac. "Sol" means a GPU job on ASU Sol.

---

## 0. Read this first

**The Sol order to the results freeze (Ritik, Nov 3; re-planned Nov 4 00:48 for Sol's real limit).** The course account
only (no other account; the H100s aren't available). B1, A37, B17 and A18 are done (A18 read Nov 3, F39); A38 is
dropped. One queue, in this order:
1. the 1-GPU bench (389340): done Nov 3, about 400 tokens/s per A100 (KV-cache bound), so E2 is 53.2 GPU-hours;
2. B20's smokes (Granite's, 456999, submitted Nov 3), then each model's runs after its clean smoke (2026-11-03
   12:19, §13 and §14);
3. A39 on E2 in 1-GPU parts: the 9 parts queued Nov 3 (running from about 22:45), then the core systems' sixteenths,
   round-robin, the wrapper systems' fifths and a sweep per system (pre-registration 2026-11-03 11:30, §10–§12);
4. A39 on the 30 (quarters and halves), unless E2 and B20 miss Nov 11 09:00;
5. B1R2 last: decided Nov 4 by its rule's compute check, which it passed (the A39 log's §13): 40 parts of 3 questions.

Nothing new after Nov 18. **What binds** (Nov 4) is the class QoS's 960 running GPU-minutes (each running job's time
left × GPUs) and the 10 submitted jobs: 7 one-GPU jobs ran at once on Nov 3, so MaxJobsPU 2 doesn't bind. So most jobs
are 1:30 (10 at once hold 900).

**The feeder submits them** (Nov 4; `tools/sol_feeder.py`, the session log `2026-11-04_0124`). It runs on Sol and keeps
the 10 places full from the queue file `finetune/gpu/sol/queue_2026-11-04.txt`: the 00:26 log's lines, in its order,
dependencies by label. Every 5 minutes it reads the jobs' states (sacct), then submits the next lines through
`submit.sh` while places and GPU-minutes allow. It records each line's job id before the next, so a restart never
submits a line twice. It waits for dependencies itself, so no pending job holds a place, and it skips (and mails you) a
line whose `afterok` dependency failed. It never resubmits a job that ended. From the clone's root:
```bash
P=/scratch/$USER/envs/olmo/bin/python; F=cot-disclosure/tools/sol_feeder.py
$P $F --dry-run        # what a tick would submit now; changes nothing
$P $F --status         # last tick, counts, alerts, every line's job and state
nohup $P $F --loop >> /scratch/$USER/trackA/feeder.out 2>&1 &     # start (login node); or scrontab with --once
touch /scratch/$USER/trackA/feeder.stop                            # stop (rm it before starting again)
$P $F --adopt LABEL JOBID; $P $F --skip LABEL; $P $F --reset LABEL  # your own changes to a line
```
Its log is `/scratch/$USER/trackA/feeder.log`; its state `/scratch/$USER/trackA/feeder/state.json`. **Times** come from
`squeue --start -u $USER` on real jobs, not `sbatch --test-only`. **`submit.sh`** (Nov 3–4):
- it prints the two limits before each job: the GPU-minutes free now and the places left in the 10; `--check` does every
  check and submits nothing (the feeder asks it before each line);
- every job mails on failure (`--mail-type=FAIL`) to `$USER@asu.edu`, or `$TRACKA_MAIL` (`none`: off);
- **htc** isn't open to the class QoS (its AllowQos is public,debug), so `--htc` is refused;
- a second download is refused unless it waits for the first (`--dependency=afterany:N`): one at a time;
- only running jobs count toward the 960 GPU-minutes.

**Pulling on Sol while jobs are queued.** A queued job reads its code from Sol's clone when it starts. Before a
`git pull` there, check that no file a queued job loads has changed: §16's list of the files they load, then
`git diff --stat <Sol's HEAD>..origin/main -- <those files>` must print nothing.

**Rules that apply to every step.**
- **Dry run first.** Every script that calls a model has `--dry-run` (calls, time, nothing sent).
  Any run over 50 calls, and any Sol job, needs Ritik's "go". **From Nov 3, Track C:** C19, C25, C20 and C26 have it
  (pre-registered; their open choices confirmed Nov 1), so Shrey runs them without asking; a new Track C experiment needs
  its pre-registration committed on `trackC-main` first (docs/trackC/START_HERE.md).
- **At most 4 Voyager requests in flight** per machine, shared by every process
  (`progress/common.slot`). Long runs resume where they stopped.
- **Keep the Mac awake** during Voyager runs: plugged in, lid open. On battery with the lid closed
  it sleeps and the run stalls (Oct 27 lost 9 hours).
- **Data never goes to GitHub.** Runs, replies, probes, caches and Sol outputs live in gitignored
  folders (`results/trackA/`, `results/trackB/`, `results/trackC/`, `finetune/data/`). Only
  numbers-only summaries in `results/summaries/` are tracked. Nothing from GPQA goes into any tracked
  file or doc. Saved results are never edited; new runs are appended.
- **Keys** live in `cot-disclosure/.env` (gitignored) and are never printed. No keys on Sol.
- **Sol:** every job under `class_cse59888883fall2026` (never `grp_hdavulcu`), submitted through
  `sol/submit.sh`; Python is always `/scratch/ragarw68/envs/olmo/bin/python`, never the system
  `python3`.
- **Reporting:** rates as "X of Y [95% Wilson]"; differences as bootstraps clustered by question;
  under 5 questions, "too few questions" and no interval.

**Setup (Mac, once).**
```bash
cd ~/Documents/Projects/ODL/cse598-cot-faithfulness
python3 -m venv .venv && .venv/bin/pip install -r cot-disclosure/requirements.txt
cp cot-disclosure/.env.example cot-disclosure/.env        # add RC_LLM_API_KEY (Voyager)
cd cot-disclosure && ../.venv/bin/python -m pytest -q      # every test passes (823 on Nov 3), no network, ~7 min
```
**Check:** every test passes. Then install the pre-push check (page 17).

---

## 1. The progress round: recompute its numbers

- **What:** every progress-round number (Test 1, Test 2, Experiment A) from the saved runs.
- **Where:** Mac, no calls. **Status:** done; rerun after any parser change.
- **Commands** (repo root): `.venv/bin/python cot-disclosure/progress/analyze_progress.py`
- **In → out:** `results/progress*.jsonl` → `docs/labeling/RESULTS_SUMMARY.json`, figures F1–F9,
  `docs/labeling/LABEL_QUEUE.csv`.
- **Time:** under a minute. **Check:** `git diff docs/labeling/` shows no number changes unless you
  meant one.

## 2. Track A, Step 1 and the Voyager ID checks

- **What:** what Voyager's endpoints accept for Olmo 3 7B Think (templates, `<think>`, echo
  log-probs); after Oct 21, that the new model IDs route to the same checkpoint.
- **Where:** Mac → Voyager (8 and 7 calls). **Status:** done Oct 21; rerun only if Voyager changes.
- **Commands:**
  ```bash
  ../.venv/bin/python finetune/voyager_capabilities.py --dry-run
  ../.venv/bin/python finetune/voyager_capabilities.py
  ../.venv/bin/python finetune/voyager_ids_check.py --dry-run
  ../.venv/bin/python finetune/voyager_ids_check.py
  ```
- **Out:** `results/trackA/voyager_capabilities.jsonl.gz`, `voyager_ids_check.jsonl.gz`.
- **Time:** a few minutes. **Check:** the summary lines: the served template, and on the ID check
  max difference ≤ 0.01 on the first 2,047 tokens with mismatches only at near-ties.
- **Automatic from then on:** every Voyager run checks the catalog and runs the identity canary at
  the start and hourly (`client.py`; log in `results/voyager_canary.jsonl`).

## 3. Track A, Step 2b: the base model in the pinned format

- **What:** Olmo 3 7B Think on the 20 hinted Test 2 questions, in its own Think format: no hint × 2,
  user × 1, pasted × 3, inserted × 3, inserted + declared × 3 (240 runs).
- **Where:** Mac → Voyager. **Status:** done Oct 22 (240 of 240).
- **Commands:**
  ```bash
  ../.venv/bin/python finetune/base_format.py --dry-run
  ../.venv/bin/python finetune/base_format.py            # resumable
  ../.venv/bin/python finetune/base_format.py --extend   # continue replies cut off at 16,000 tokens
  ../.venv/bin/python finetune/base_format.py --report
  ```
- **In → out:** `data/progress/mmlupro_30.jsonl`, `results/progress/expB_cued.jsonl` →
  `results/trackA/base_format.jsonl.gz` (+ `base_format_runs.jsonl`).
- **Time:** 68–156 min at 4 in flight, plus continuations. **Check:** `--report`: 240 ok; hint
  following per channel; cut-off runs continued; no `not_run` left.

## 4. Track A, Step 3: takeover curves (early answering)

- **What:** after each sentence of each Step 2b run, close the reasoning, force `Answer: (` and read
  the letters' probabilities; the takeover point and type; the default cases for Steps 4 and 10.
- **Where:** Mac → Voyager, one probe per request. **Status:** done Oct 24 (219 runs, 137,143 probes).
- **Commands:**
  ```bash
  ../.venv/bin/python finetune/look/takeover.py --dry-run
  ../.venv/bin/python finetune/look/takeover.py --pilot          # the shortest followed run only
  ../.venv/bin/python finetune/look/takeover.py --workers 2      # all runs, resumable
  ../.venv/bin/python finetune/look/takeover.py --report
  ../.venv/bin/python finetune/look/takeover.py --cases          # default cases for Steps 4 and 10
  ../.venv/bin/python finetune/look/plot_takeover.py
  ```
  For a trained version on Sol, `--batch N` sends lists to a local vLLM server.
- **Out:** `results/trackA/takeover_probes.jsonl.gz`, `takeover_runs.jsonl`, `takeover_cases.jsonl`,
  `results/trackA/figures/takeover_*.png`.
- **Time:** ~0.5 s per probe; `--probes auto` (grid_tail for followed runs) cuts probes by 62%.
  **Check:** `--report`: every run probed, no gaps; the k = 0 table; the 26 default cases.

## 5. Track A, analyses with no calls (before Step 4, the window)

- **What:** concentration on sure questions and the matched lead onsets (`before_takeover.py`); the
  sliding-window analysis (`window_reach.py`).
- **Where:** Mac, no calls. **Status:** done (F5, F8).
- **Commands:**
  ```bash
  ../.venv/bin/python finetune/look/before_takeover.py --dry-run
  ../.venv/bin/python finetune/look/before_takeover.py
  ../.venv/bin/python finetune/look/window_reach.py
  ```
- **Out:** `results/trackA/before_takeover.jsonl`; `results/summaries/trackA/window_reach.json` + figure.
- **Time:** about a minute each. **Check:** groups under 5 questions print "too few questions".

## 6. Track A, Step 4: the deletion test

- **What:** on the late takeovers on sure questions (19 cases), cut at the takeover, delete the
  reasoning's hint mentions (or as many length-matched sentences), then one forced answer and 3
  continuations per arm; an unedited arm.
- **Where:** Mac → Voyager (209 calls). **Status:** done Oct 24 (F7).
- **Commands:**
  ```bash
  ../.venv/bin/python finetune/look/deletion.py --dry-run
  ../.venv/bin/python finetune/look/deletion.py
  ../.venv/bin/python finetune/look/deletion.py --report
  ```
- **Out:** `results/trackA/deletion_calls.jsonl.gz`, `deletion_runs.jsonl`.
- **Time:** ~25 min typical, up to ~7.5 h if every continuation runs to its cap.
  **Check:** `--report`: hint vs control vs unedited, per question and pooled.

## 7. Track A, Step 5: the dataset rules and the length audit

- **What:** train / validation / held-out records (target rule, correct-hint records, channels,
  held-out wordings with a 0-overlap check); reply lengths by source.
- **Where:** Mac, no calls. **Status:** done; `train` fills from Steps 6–7.
- **Commands:**
  ```bash
  ../.venv/bin/python finetune/build_dataset.py --dry-run
  ../.venv/bin/python finetune/build_dataset.py
  ../.venv/bin/python finetune/length_audit.py
  ```
- **Out:** `finetune/data/{train,validation,heldout}.jsonl`, `manifest.json`;
  `results/trackA/length_audit.jsonl`. **Check:** `manifest.json` reports 0 held-out wordings in
  training.

## 8. Track A, Steps 6–7: training data

- **What:** Step 6: 3 no-hint runs per pool question in the pinned format; a question is kept if all
  3 are answered and correct. Step 7: for each kept question, one wrong hint per channel plus 1–2
  correct hints; a prefill target per record (one opening sentence each for the reasoning and the
  final answer, from 10 paraphrases; the model writes the rest; up to 4 samples; pass = ends on the
  kept answer and doesn't refer to instructions).
- **Where:** Mac → Voyager. **Status:** done Oct 27 13:45 MST: 251 kept of 530; assembled 1,196
  examples (1,040 train, 156 validation).
- **Commands:**
  ```bash
  ../.venv/bin/python finetune/make_pool.py --help      # the pool: done Oct 25 (1,600 questions, with --hard)
  ../.venv/bin/python finetune/run_steps67.py --dry-run --kept 240
  nohup ../.venv/bin/python -u finetune/run_steps67.py --kept 240 --checkpoint 100 \
      >> logs/trackA_steps67.log 2>&1 &                                           # resumable
  ../.venv/bin/python finetune/run_steps67.py --report      # the state so far (appends a report row)
  ../.venv/bin/python finetune/run_steps67.py --assemble    # after it ends: the training set
  ```
- **In → out:** `finetune/data/pool.jsonl` → `results/trackA/nohint_train.jsonl.gz`,
  `target_samples_prefill.jsonl.gz`, `targets_prefill.jsonl.gz` (+ `_runs.jsonl`),
  `results/trackA/steps67_report.jsonl`; `--assemble` → `finetune/data/train_examples.jsonl.gz`,
  `validation_examples.jsonl.gz`, `examples_manifest.json`.
- **Time:** batches of 40 questions, ~2.5 h each while the Mac is awake (~142 s per no-hint run,
  ~139 s per target sample, 4 in flight). **Check:** `tail logs/trackA_steps67.log`; at 100 kept it
  writes a checkpoint report and stops (exit 3) if a rate is off by more than half from the pilot's;
  `--assemble` prints the counts and says whether "neither" targets were dropped (under 10%).

## 9. Sol: access, code, data, results

- **What:** get code and inputs onto Sol, and the summaries back. **Where:** Mac ↔ Sol (ASU VPN on).
- **Code** (tracked files only; until this branch is pushed):
  ```bash
  cd ~/Documents/Projects/ODL/cse598-cot-faithfulness
  git ls-files | rsync -av --files-from=- ./ ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/
  ```
- **Inputs** (gitignored run files the GPU steps read; each step checks their sha256):
  ```bash
  cd cot-disclosure
  rsync -av --files-from=finetune/gpu/sol/inputs.txt ./ \
      ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/cot-disclosure/
  ```
- **Results back** (summaries only, into gitignored `results/trackA/gpu/`): the exact `rsync` lines
  per step are in `finetune/gpu/README.md` ("Results back"). Then
  `../.venv/bin/python tools/export_summaries.py` copies the numbers-only ones into
  `results/summaries/trackA/`.
- **Check** (on Sol): `cd /scratch/ragarw68/cse598-cot-faithfulness/cot-disclosure &&
  /scratch/ragarw68/envs/olmo/bin/python finetune/gpu/kit.py --check-inputs` lists every input as
  matching.

## 10. Sol: environment and smoke test

- **What:** install pinned packages into `/scratch/ragarw68/envs/olmo`; load the model, generate 32
  tokens in the pinned format, check the snapshot is d97e442.
- **Where:** Sol. **Status:** done Oct 26.
- **Commands:** in an interactive GPU session under the course account:
  ```bash
  cd /scratch/ragarw68/cse598-cot-faithfulness
  bash cot-disclosure/finetune/gpu/sol/setup_env.sh        # 5-15 min, once
  cot-disclosure/finetune/gpu/sol/run.sh smoke              # 2-5 min
  ```
  or as batch jobs: `cot-disclosure/finetune/gpu/sol/submit.sh setup_env`, then `… submit.sh smoke`.
- **Out:** `/scratch/ragarw68/trackA/smoke/smoke.json`. **Check:** "matches d97e442", "renders our
  prompt exactly", an A100 and CUDA 13.0, a sensible start of reasoning.

## 11. Track A, Step 8: the checkpoint check

- **What:** a local bf16 and fp32 forward pass over the texts Voyager echoed, against the rule fixed
  on Oct 26; the Instruct checkpoint as the negative control.
- **Where:** Sol (5–10 min), then the Mac. **Status:** done Oct 26 (F9).
- **Commands:**
  ```bash
  cot-disclosure/finetune/gpu/sol/run.sh step8                       # Sol, or submit.sh step8
  ../.venv/bin/python finetune/gpu/step8_verdict.py --sha256sum results/trackA/gpu/weights_sha256.txt   # Mac
  ```
- **Out:** `step8_checkpoint.json` (stays gitignored: it holds token strings);
  `results/summaries/trackA/step8_verdict.json`. **Check:** the decision line and the list of
  positions outside near-ties; the rule is never changed after the result.

## 12. Track A, Step 9: attention to the hint

- **What:** one forward pass per hinted Step 2b run (199); attention mass from the answer position
  and from each reasoning sentence to the hint, its letter and a same-length control span, per layer
  and head. The follow-up re-reads the saved runs (full layers, hint − control, readout heads,
  matched lead onsets with a placebo).
- **Where:** Sol (~15–40 min GPU; the follow-up ~1 min CPU), then the Mac. **Status:** done Oct
  26–27 (F10, F12, F14).
- **Commands:**
  ```bash
  cot-disclosure/finetune/gpu/sol/run.sh step9 --limit 3     # Sol: quick check, ~3 min
  cot-disclosure/finetune/gpu/sol/run.sh step9               # Sol: the rest, then the report
  cot-disclosure/finetune/gpu/sol/run.sh step9 --followup    # Sol: the follow-up, CPU only
  ../.venv/bin/python finetune/look/attn_to_hint.py --followup --from-reduced results/trackA/gpu/step9_reduced.npz   # Mac, no GPU
  ```
- **Out:** `step9_attention.json`, `step9_followup.json`, `step9_aligned.png`, `step9_onsets.png`,
  `step9_reduced.npz`. **Check:** 199 runs, no skipped onsets; groups show their questions; the
  placebo's rise is near 0.

## 13. Track A, Step 10: activation patching

- **What:** on Step 4's 21 cases, cut (i) before the first hint mention and (ii) at the takeover;
  copy one layer's clean output (prompt with the own letter) into the hinted run at the hint, the
  reasoning or the answer position; restoration by layer.
- **Where:** Sol (1–2 h), then the Mac. **Status:** done Oct 26 (F11, F13).
- **Commands:**
  ```bash
  cot-disclosure/finetune/gpu/sol/run.sh step10 --limit 3    # Sol: quick check
  cot-disclosure/finetune/gpu/sol/run.sh step10              # Sol: the rest, then the report
  ../.venv/bin/python finetune/look/patching.py --handoff results/trackA/gpu/step10_patching.json   # Mac
  ```
- **Out:** `step10_patching.json`; `results/summaries/trackA/step10_handoff.json`, the handoff
  figure. **Check:** sanity ok on every cut; cuts with a gap under 0.5 are left out and counted.

## 14. Track A, Steps 11–13: train, generate, evaluate

- **What:** Step 11 trains LoRA only, tags only, LoRA + tags (and the fourth version, LoRA on the
  attention of layers 15/19/23, last) with the decided settings (`finetune/train.py`: rank 16, LoRA
  2e-4, tags 1e-3, 2 epochs, checkpoint per epoch, chosen by validation loss). Step 12 generates
  through a local vLLM server (`finetune/generate.py`; LoRA merged in, the model tag folded into the
  embeddings, tagged prompt embeddings). Step 13 evaluates 930 runs per system (`finetune/eval.py`)
  and reports the measures. The job order, hours and limits: PLAN (Track A, the Gate 3 job plan).
- **Where:** Sol, each job on Ritik's "go". **Status:** batch 2 trained Oct 28; batch 3 evaluated, Gate 3 final Oct 31
  (F28); A18 read Nov 3 (F39); A39 on E2 queued Nov 3 (its lines: the Nov 3 session logs, 15:14 and 22:16).
- **Commands** (first the inputs from the Mac, then on Sol from the clone's root):
  ```bash
  # Mac, repo root: the inputs (training examples included) to Sol
  rsync -av --files-from=cot-disclosure/finetune/gpu/sol/inputs.txt cot-disclosure/ \
        ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/cot-disclosure/
  # Sol
  cot-disclosure/finetune/gpu/sol/submit.sh setup_vllm                  # vLLM 0.31.0 in its own env (no GPU);
                                                                        # checks the version and server commands against the committed list (no --help: no GPU)
  cot-disclosure/finetune/gpu/sol/submit.sh timing --estimate 0.5       # S1: limit 1:00
  cot-disclosure/finetune/gpu/sol/submit.sh vllm_check --estimate 1 --dependency=afterok:<setup_vllm job>  # S2: limit 1:30
  "$TRACKA_PY" cot-disclosure/finetune/gpu/plan_training.py /scratch/ragarw68/trackA/timing/timing.jsonl
  # ^ S1's refit: hours per version (a range) and the batch-2 lines with their limits (high x 1.3, <= 8 h):
  #   train lora and tags at once; lora_tags --dependency=afterany:<lora job>; lora_attn3 afterany:<tags job>
  # each version exports its chosen epoch to train/<version>/final/ when its last epoch ends
  "$TRACKA_PY" cot-disclosure/finetune/gpu/plan_eval.py --vllm-check <S2 job> --train lora=<id>,tags=<id>,...
  # ^ batch 3: base and prompt_only after S2, each version after its training job; parts under 8 h;
  #   it reads the queue, finished jobs and train/<version>/final/ on Sol, and prints the submit.sh lines
  cot-disclosure/finetune/gpu/sol/submit.sh val_loss --estimate 1.25 --dependency=afterany:<training jobs> -- lora tags lora_tags lora_attn3
  # ^ S7 (Oct 28): the validation loss of base and of each version's two epochs, split into the taught
  #   tokens (the prefilled opener, the reasoning sentences naming the hint, the final answer) and the
  #   rest; Hugging Face only (no vLLM); all four versions (decided Oct 28): 45-80 GPU minutes, limit 2:00;
  #   refused at once if a version's checkpoint is missing; a rerun skips the systems done
  # Every vLLM job's first step (vllm_check, eval, trackb_qwen8b): `vllm serve --help=all` on the node. It stops
  #   only if an option or value a server command uses is missing or changed there; other differences are a
  #   WARNING line in the job's log, and the node's list is saved as trackA/vllm_serve_options_node.txt
  ```
  The parts' token counts, with no model (Mac or Sol): `../.venv/bin/python finetune/val_loss.py
  --dry-run` (Oct 28: 80,010 taught tokens of 1,243,692, 6.4%). S7 took 0:37:09 for all four
  versions (Oct 28). Back on the Mac (numbers only; `finetune/gpu/README.md`, "Results back"):
  ```bash
  cd cot-disclosure && mkdir -p results/trackA/gpu && S=ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/trackA
  rsync -av $S/val_loss/val_loss.json $S/val_loss/val_loss_examples.jsonl results/trackA/gpu/
  ../.venv/bin/python finetune/val_loss.py --report results/trackA/gpu    # each version minus base, clustered by question
  ../.venv/bin/python tools/export_summaries.py                           # -> results/summaries/trackA/
  ```
  `submit.sh` sets each limit to the estimate × 1.3 (rounded up to 30 min), refuses a job over 960
  GPU-minutes, and before submitting prints the GPU-minutes of your running and pending jobs, the
  GPU-minutes free now and the places left in the 10 (Nov 4). Evaluation report (any machine with the copied-back `_runs.jsonl` files):
  `../.venv/bin/python finetune/eval.py --report --out <dir>`; the Phase 6 rows: `--label-sample`.
- **In → out:** `finetune/data/{train,validation}_examples.jsonl.gz` → `/scratch/ragarw68/trackA/train/
  <version>/` (`latest/`, `epoch1/`, `epoch2/`, `chosen.json`, `final/`); `timing/timing.jsonl`;
  `vllm_check/vllm_check.json`; `eval/eval_<system>.jsonl.gz` + `_runs.jsonl`; `models/` (merged and
  folded copies); `val_loss/val_loss.json` + `val_loss_examples.jsonl` (numbers only: tokens and loss
  per part and system, each trained system minus base).
- **Time:** S1 ≤ 30 min, S2 ≤ 1 h, each version 2–3 h, each system's evaluation 5–14 h (1–3 jobs).
  **Check:** S1's `timing.jsonl` (peak memory under 80 GB, predicted hours); S2's `vllm_check.json`
  says `pass`; `train_log.jsonl` losses fall; `chosen.json` names an epoch; every evaluated system
  has 930 runs in its `_runs.jsonl`.
- **The look-inside rerun** works on a trained version: Steps 9 and 10 take `--model DIR`,
  `--runs-from` and (Step 10) `--cases-from`, with their own `--out`.

- **A18, inside the fixed model** (Oct 31; pre-registered in the 2026-10-31 22:44 log, amended Nov 1 before anything
  ran, its §8): Steps 3, 9 and 10 and a layer swap on batch 3's runs of base and LoRA, cases by Step 10's rule,
  chosen apart for tool hints (pasted and inserted: the primary, as F11 and F26) and user hints (reported apart).
  Expected cases: base 30–31 tool (14 questions) and 20–21 user; LoRA 17–18 tool (12 questions) and 16–17 user.
  8 jobs, 7.8 GPU h at most, after a push and a pull (`a18` is a new job kind). From the Sol clone,
  `S=cot-disclosure/finetune/gpu/sol/submit.sh`:
  ```bash
  $S a18 --estimate 1   -- step3 --system base                                   # job A
  $S a18 --estimate 0.6 -- step3 --system lora                                   # job B
  $S a18 --estimate 1.7 --dependency=afterok:A -- step10 --cases base --weights base
  $S a18 --estimate 1.7 --dependency=afterok:A -- step10 --cases base --weights lora
  $S a18 --estimate 1.1 --dependency=afterok:B -- step10 --cases lora --weights lora
  $S a18 --estimate 0.5 --dependency=afterok:A -- swap
  $S a18 --estimate 0.6 --dependency=afterok:A -- step9 --system base
  $S a18 --estimate 0.6 --dependency=afterok:B -- step9 --system lora
  ```
  The cases without any calls: `../.venv/bin/python finetune/look/a18.py plan` (Mac). The reading:
  `finetune/look/a18.py readout`.
- **Dropped Nov 3 (F38: B1 doesn't read "works").** **A38, the note + B1 (stretch)** (Oct 31; pre-registered in the 2026-10-31 22:45 log): only after B1's verdict reads
  "works". `plan --note` refuses otherwise and prints no lines.
  ```bash
  "$TRACKA_PY" cot-disclosure/finetune/gpu/provenance_job.py plan --out "$TRACKA_OUT" \
    --alpha-from "$TRACKA_OUT/provenance_forced/provenance_forced.json" --note     # ~4 provenance_gen ... --note lines
  ```
- **B1R2, B1's deployable span on E2** (a labelled replication; decided Nov 4 by its compute check, the A39 log's §13).
  - **What:** alpha 0.25 (set A's choice) against alpha = 1 on E2's 120 questions, the inserted tool turn only: 2
    wrong-hint, 2 correct-hint and 1 no-hint run a question in each configuration, 1,200 runs. B1's engine and
    settings (`-v2`), Hugging Face, one A100.
  - **Where:** Sol, after a pull (the `--b1r2` option is new on Nov 4), and last in the order (§0).
  - **The lines,** k = 1 to 40 in order, 3 questions each (about 1.4 GPU-hours with the load; limit 2:30):
    ```bash
    $S provenance_gen --estimate 1.6 -- --alpha-from /scratch/$USER/trackA/provenance_forced/provenance_forced.json --b1r2 --part k/40
    ```
    After all 40 end, the same line with `--part k/4` (k = 1 to 4) sweeps what's left. Before a night away, `--part
    k/20` at `--estimate 3` (4:00) may replace parts k and k+20 of 40, if neither has been submitted.
  - **Out:** `$TRACKA_OUT/b1r2/eval_prov-a1-v2_p<k>of40_runs.jsonl` and `eval_prov-deployable-a0.25-v2_...`
    (numbers only; texts in `.jsonl.gz` beside them, which stay on Sol). Never beside B1's runs.
  - **Check:** `"$TRACKA_PY" cot-disclosure/finetune/gpu/provenance_job.py generate --alpha-from ... --b1r2 --part
    1/40 --out "$TRACKA_OUT" --dry-run` prints "15 runs x 2 configurations".
  - **The reading** (Nov 16–17): `provenance_job.py report --out <copied-back b1r2 folder>`, then B1's rule
    (`b1_verdict`), paired by question. Not done by Nov 15 23:59: read on the questions with every run of both
    configurations, labelled "partial: N of 120 questions".

## 15. Labels

- **What:** two raters label what the text says about the hint, for the private reasoning and the
  final answer: no mention / mentions only / rejects the hint / says the hint changed the answer /
  unclear ([`labeling/LABELING_GUIDE.md`](labeling/LABELING_GUIDE.md)).
- **Where:** anywhere, no calls. **Status:** the kit is built (Oct 27); the rater packets for L3 and L4 part 1 are
  built (Oct 31; `tools/rater_packets.py`), their examples and practice answers reviewed and set by Ritik (Nov 1).
  Ritik's sheets (rater 1) are in, format checked (Nov 1): `results/labels/L3_RA.csv` and
  `results/labels/gate3/L4/L4_part1_RA.csv`. **Both sheets in Nov 3:** L3 kappa under 0.6 in four of six cells
  (settle the 25 disagreements on `results/labels/L3_settle.csv`, tighten the guide, label the fresh batch in
  `results/labels/fresh/`, 72 rows); L4 part 1 kappa 0.930 (read, F28).
- **Commands** (from `cot-disclosure/`):
  ```bash
  ../.venv/bin/python tools/label_kit.py build     # done Oct 27: results/labels/ (gitignored: model text)
  # each rater fills results/labels/rater1.csv or rater2.csv alone: label_private, label_final, note
  ../.venv/bin/python tools/label_kit.py kappa results/labels/rater1.csv results/labels/rater2.csv
  # then, after the queue (decided Oct 28), Track B's batch: 171 rows to label in results/labels/trackB/
  ../.venv/bin/python tools/label_kit.py trackb    # bare replies (<= 30 characters) no_mention by rule, 10% spot check;
                                                   # rows 152-171: private reasoning only, the keyword check (F15)
  ../.venv/bin/python tools/label_kit.py kappa results/labels/trackB/rater1.csv results/labels/trackB/rater2.csv
  # ^ also each rater's agreement with the bare-reply rule on the spot-check rows, and with the keyword on rows 152-171
  # rater packets (Oct 31): L3 and L4 part 1 as built, a README, the guide with examples, 10 practice rows; zipped
  ../.venv/bin/python tools/rater_packets.py build   # -> results/labels/packets/<rater>/ and rater_packet_<rater>.zip
  ../.venv/bin/python tools/rater_packets.py check results/labels/packets/shrey
  # returned sheets go next to their keys: L3_RA.csv, L3_SB.csv in results/labels/; L4_part1_*.csv in results/labels/gate3/L4/
  ../.venv/bin/python tools/label_kit.py kappa results/labels/L3_RA.csv results/labels/L3_SB.csv
  ../.venv/bin/python tools/label_kit.py kappa results/labels/gate3/L4/L4_part1_RA.csv results/labels/gate3/L4/L4_part1_SB.csv
  # ^ kappa per channel (user, tool_pasted, tool_injected) and each rater's guess against key_L4.csv
  ```
- **In → out:** `docs/labeling/LABEL_QUEUE.csv` + saved runs → `results/labels/` (101 rows: 91 + 10
  replacements; sheets, key). `kappa` prints Cohen's kappa per text (private, final), overall and by
  user / tool hint, and every disagreement by row. Under 0.6: meet, tighten the guide, label a fresh batch.
- **Time:** about 2 minutes per row per rater (101 rows: 3–4 hours). **Check:** every row has exactly
  one label per text from the guide's five ("n/a" where there is no private reasoning).

## 16. Repo hygiene: summaries, history, push

- **Export summaries** (after any run): `../.venv/bin/python tools/export_summaries.py --dry-run`,
  then without `--dry-run`. It refuses a file with question or reply text. `--check` re-checks
  what's tracked.
- **History rewrite** (done Oct 27 13:49 for `trackA-nosol`): untracks produced data in the unpushed
  commits; files on disk don't move. It refuses while a run is going, writes a verified `git bundle`
  of every ref and a sha256 list of every file under `results/`, `finetune/data/`, `configs/` first,
  and compares the list after. Pause every job that writes under those folders while it runs.
  ```bash
  python3 tools/untrack_produced.py --not-in main                        # dry run: commits, paths, refs
  python3 tools/untrack_produced.py --not-in main --run --backup ~/backup-before-rewrite.bundle
  ```
  (`--not-in main` leaves local `main`'s commits alone.)
- **Push** (Ritik): `git push origin trackA-nosol:main trackA-nosol:trackA-nosol`; the hook checks it first. From Nov 3
  `trackC-main` is Shrey's and from Nov 6 `trackB-main` is Arsha's: Ritik no longer pushes his branch to them.
- **The path guard, both ways** (Nov 3; `configs/path_allowlist.txt`, `tools/path_check.py`):
  - Install it in each clone, as the pre-commit and pre-merge-commit hooks:
    `python3 cot-disclosure/tools/path_check.py --install`.
  - On `trackC-main` (Shrey) and `trackB-main` (Arsha), a commit may touch only that track's paths.
  - On Ritik's branches, a track's paths change only through a merge of its branch, taken unchanged.
  - For a change the owner agreed to: `PATH_CHECK_ALLOW=trackC-main git commit ...`. It passes with a warning; say so
    in the commit.
- **Merging a teammate's branch** (Ritik, on the check-in days: Track C Nov 7, 12, 15, 18; Track B Nov 12, 15, 18):
  ```bash
  git fetch origin
  python3 cot-disclosure/tools/path_check.py --range origin/main..origin/trackC-main --branch trackC-main   # nothing outside
  git log --oneline origin/main..origin/trackC-main          # what came; read the session logs and FC entries it adds
  git diff --stat origin/main...origin/trackC-main           # only their paths
  git checkout trackA-nosol && git merge --no-ff origin/trackC-main -m "Merge trackC-main (Shrey, <date>): <what>"
  cd cot-disclosure && ../.venv/bin/python -m pytest -q && ../.venv/bin/python tools/export_summaries.py --check && cd ..
  ../.venv/bin/python cot-disclosure/tools/make_gantt.py     # their TODO rows feed STATUS and the Gantt
  git push origin trackA-nosol:main trackA-nosol:trackA-nosol
  ```
  - The hook passes the merge only if their files come in unchanged. If they conflict with Ritik's, take theirs and
    ask them.
  - **Then place their figures:** copy `docs/trackC/figures/*` (or `docs/trackB/figures/*`) into `docs/paper/figures/`
    in a commit of Ritik's.
  - **Then tell them to merge `origin/main` back:** `git fetch origin && git merge origin/main` on their branch. The
    hook passes `main`'s files only unchanged.
  - **Files Sol's queued jobs load** (A39 and B20; `tests/test_path_check.py`, FROZEN_FOR_SOL):
    - `finetune/` (eval.py, generate.py, continuation.py, olmo_format.py, hf_engine.py, gpu/);
    - `progress/common.py`, `progress/sol_trackB.py`, `progress/sol_b17.py`, `progress/sol_b20.py`,
      `progress/run_b20.py`;
    - `agents/__init__.py`, `agents/sol_c13.py`;
    - `client.py`, `parse.py`, `detect.py`, `experiments.py`, `tasks.py`, `tools/answer_key.py`, `providers/`,
      `configs/`, `data/`;
    - the Sol kit's `run.sh`, `env.sh`, `guard.sh` and `accounts.conf`.

    A merge that changes one of these waits for the queued jobs to start before Ritik pulls on Sol.
- **Data handoff:** `python3 tools/make_handoff_bundle.py --track B` (or A, C): a tar.gz of the track's
  gitignored results with a sha256 manifest, in `results/handoff/`; GPQA files never included unless
  Ritik says so. The receiver checks it: `--verify <file>.tar.gz`.

## 17. The pre-push check (each person, once per clone)

```bash
cd ~/path/to/cse598-cot-faithfulness
printf '#!/bin/sh\nexec python3 "$(git rev-parse --show-toplevel)/cot-disclosure/tools/prepush_check.py" "$@"\n' > .git/hooks/pre-push
chmod +x .git/hooks/pre-push
python3 cot-disclosure/tools/prepush_check.py --rev HEAD     # what a push would be checked for
```
It refuses a push that adds anything under a produced-data folder, any file with "gpqa" in its name
(code and docs excepted), or a file over 50 MB.

**The path allowlist (Track C's branch, from Nov 3).** On a branch listed in `cot-disclosure/configs/path_allowlist.txt`,
a commit may touch only that branch's paths. Install the check as the pre-commit hook, once per clone:
```bash
printf '#!/bin/sh\nexec python3 "$(git rev-parse --show-toplevel)/cot-disclosure/tools/path_check.py" "$@"\n' > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
python3 cot-disclosure/tools/path_check.py --range origin/main..origin/trackC-main --branch trackC-main   # review before a merge
```

## 18. Track B: test widely

- **What:** hint following and admission across models, thinking on/off and channels
  (`configs/trackB.yaml`): 54 questions (24 puzzles, 30 MMLU-Pro) × 5 conditions × 3 runs per model.
  Olmo 3 7B Think runs in the pinned Think format with the declared `tool_injected` channel, as in
  Track A. **Where:** Mac → Voyager; Qwen3-8B on Sol (a GPU job; Ollama never on the Mac, Oct 28);
  closed providers dropped for cost (Nov 3). **Status:** done Oct 28 (F15–F17); Qwen3-8B Oct 30 (F29); B16 Nov 1
  (F35); B17 Nov 3 (F37); B20 (open models on Sol) pre-registered Nov 3.
- **Before a model's first batch** (from `cot-disclosure/`): its served template and an identity
  canary, then a smoke test and the dry run in a session log.
  ```bash
  ../.venv/bin/python progress/voyager_template_check.py --model M     # 5 calls; gap 0 expected
  ../.venv/bin/python progress/voyager_template_check.py --model M --canary-specs /tmp/specs
  ../.venv/bin/python progress/make_canary.py --spec /tmp/specs/M.json  # configs/canary/M.json
  ../.venv/bin/python progress/run_trackB.py --run --model M --limit 5  # one question, every condition
  ../.venv/bin/python progress/run_trackB.py --dry-run --model M        # jobs, calls, hours
  ```
- **Runs** (resumable; repeat by repeat; at most 4 Voyager requests in flight across all processes):
  ```bash
  nohup caffeinate -i ../.venv/bin/python -u progress/guard.py \
    --job "voyager:qwen3think=progress/run_trackB.py --run --model qwen3-30b-a3b-thinking-2507" \
    --job "voyager:qwen3instruct:qwen3think=progress/run_trackB.py --run --model qwen3-30b-a3b-instruct-2507" \
    --job "voyager:olmo3think:qwen3instruct=progress/run_trackB.py --run --model olmo3-7b-think" >> logs/guard.log 2>&1 &
  touch logs/stop_guard                           # stop: requests in flight finish first
  ../.venv/bin/python progress/run_trackB.py --steered --model qwen3-30b-a3b-thinking-2507   # Track C's input
  ../.venv/bin/python -m providers.budget --status                    # paid spend (none yet)
  ```
- **Out:** `results/trackB/<provider>.jsonl.gz` (texts) and `<provider>_runs.jsonl` (numbers),
  `steered_cases.jsonl`, `template_check.jsonl` (all gitignored).
- **Time:** Qwen3 30B Thinking ~4.2 h, Qwen3 30B Instruct ~1 h, Olmo 3 7B Think ~8.2 h (4 in flight);
  Qwen3-8B on Sol 0.5–1.5 GPU hours (below). **Check:** `tail` the log (`not_run` and
  `api_error` counts); every row's `served_model` is the model asked for; the Mac stays awake.

- **Qwen3-8B on Sol** (decided Oct 28; replaces the Ollama grid): one GPU job runs our vLLM server
  (`Qwen/Qwen3-8B` at `b968826d`, envs/olmo-vllm) and the Track B runner against it, thinking on
  and off through `enable_thinking`, core cells first; resumable. Records with text stay on Sol;
  numbers-only flags come back.
  ```bash
  # Sol: the snapshot (a job without a GPU, the only one online; sha256 checked against the Hub)
  cot-disclosure/finetune/gpu/sol/submit.sh get_qwen8b                    # -> job G
  # Sol: the run (1 A100, offline; its first step checks the node's vLLM options)
  cot-disclosure/finetune/gpu/sol/submit.sh trackb_qwen8b --estimate 1.5 --dependency=afterok:G   # limit 2:00
  # Mac, numbers only, then the report
  rsync -av ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/cot-disclosure/results/trackB/sol_vllm_{runs,flags}.jsonl \
        cot-disclosure/results/trackB/
  ```

- **B16, tool or authority** (Oct 31; pre-registered in the 2026-10-31 22:20 log). The user's hint with the answer
  key's authority (`user_authority`) and the tool arms again, on the three Voyager models: 1,458 runs, ~8.4 h at 4
  in flight. Its own records (`b16_voyager.jsonl.gz`), never in Track B's table. **Done Nov 1 (F35).** The tool arms
  sent Track B's exact requests, so the reply cache returned Track B's replies for 907 of 972 (T11): to make a rerun
  the same day, change the seed or bypass the cache, and pre-register which.
  ```bash
  ../.venv/bin/python progress/run_b16.py --dry-run                 # jobs, calls, hours
  ../.venv/bin/python progress/run_b16.py --run --limit 9           # smoke: question 1, every arm and model
  nohup caffeinate -i ../.venv/bin/python -u progress/guard.py \
    --job "voyager:b16=progress/run_b16.py --run" >> logs/guard.log 2>&1 &
  ../.venv/bin/python progress/run_b16.py --report                  # once all 1,458 are done -> b16_report.json
  ```

- **B17, the thinking dose** (Oct 31; pre-registered in the 2026-10-31 22:37 log; **done Nov 3, F37; §13**): gpt-oss-20b at reasoning effort
  low, medium and high on our vLLM server in a Sol job; 2,430 runs, ~4–6 GPU h. Records stay on Sol, and the
  numbers-only flags come back. **At temperature 1.0** (gpt-oss's recommended setting; Track B's models stay at their
  0.6; amended Nov 1, before anything ran). **The smoke job exits 0 only if every check passes** (4: the template; 5:
  all ran, at least 12 of 15 answered, every finished run parsed, the tool path, the effort), so the runs wait on it
  with `afterok`; after a failed smoke the runs job stays pending (`DependencyNeverSatisfied`): `scancel` it.
  ```bash
  # Mac, no calls: the jobs and hours
  ../.venv/bin/python progress/run_b17.py --dry-run
  # Sol, after a pull: the snapshot (online), the smoke job (template check + 15 runs), then the runs
  cot-disclosure/finetune/gpu/sol/submit.sh get_gptoss                                              # -> job G
  cot-disclosure/finetune/gpu/sol/submit.sh b17 --estimate 0.75 --dependency=afterok:G -- --smoke    # -> job S
  cot-disclosure/finetune/gpu/sol/submit.sh b17 --estimate 6 --dependency=afterok:S                 # resumable
  # Mac: numbers only, then the checks
  S=ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/cot-disclosure/results/trackB
  rsync -av $S/b17/ cot-disclosure/results/trackB/b17/ && rsync -av $S/b17_sol_vllm_runs.jsonl cot-disclosure/results/trackB/
  ../.venv/bin/python progress/run_b17.py --smoke-check
  ../.venv/bin/python progress/run_b17.py --report        # when all 2,430 runs are back
  ```

## 19. Track C: the agent team

- **What:** solver (Qwen3 30B Thinking; the tool team gets the lookup tool, bad or good by a seeded
  oracle; the no-tool team doesn't) → reviewers (Qwen3 30B Instruct, Olmo 3 32B Instruct served as
  Olmo 3.1 32B Instruct since Oct 28; 4 variants)
  → checker (re-asks without the tool). Wrong answers shipped, catches, false alarms, per team ×
  reviewer model × variant, bad and good lookups apart. **Where:** Mac → Voyager.
  **Status:** code done Oct 27 (append-only, resumable); C1 (5 items) done Oct 27; the 32B
  reviewer's smoke done Oct 28 00:20; C4 done Oct 28 17:51 (318 cases); C9 (the reviewers again, with
  one sentence added) done Oct 28 22:33 (954 calls; FINDINGS F19); C4–C18 done (F18–F34); C19, C20, C25, C26 are
  Shrey's (`docs/trackC/START_HERE.md`).
- **Commands** (from `cot-disclosure/`):
  ```bash
  ../.venv/bin/python agents/run_team.py --replay                       # saved data, no calls
  ../.venv/bin/python agents/run_team.py --live --n 5 --dry-run         # 5 pilot items: ~55 calls
  ../.venv/bin/python agents/run_team.py --live --n 5 --run-name C1
  # C4, on Track B's cases (after run_trackB.py --steered for the solver model):
  ../.venv/bin/python agents/run_team.py --live --cases results/trackB/steered_cases.jsonl \
        --kinds steered,matched --per-kind 30 --repeats 3 --teams tool,notool --log team_c4 --dry-run
  # under the power guard (logs/stop_guard stops every guard, cases in flight first; logs/stop_c4
  # only pauses C4, the guard restarts it a minute later; exit 3 = a Voyager guard failed, all
  # Voyager work pauses). To run C4 before a Track B model, put both in one guard:
  # --job "voyager:c4=..." --job "voyager:olmo3think:c4=progress/run_trackB.py --run --model olmo3-7b-think"
  nohup caffeinate -i ../.venv/bin/python -u progress/guard.py \
    --job "voyager:c4=agents/run_team.py --live --cases results/trackB/steered_cases.jsonl --kinds steered,matched --per-kind 30 --repeats 3 --teams tool,notool --log team_c4 --run-name C4-oct28" >> logs/guard_c4.log 2>&1 &
  # one Track B model per run: with several models in steered_cases.jsonl, add --case-model M and a log of its own
  ../.venv/bin/python agents/run_team.py --summary                      # results/trackC/team_live_summary.json
  ../.venv/bin/python agents/run_team.py --summary --log team_c4 --cases results/trackB/steered_cases.jsonl --table
                                                                        # C4, also by Track B kind and kind x set
  # C9 (Oct 28): only the reviewers again, on C4's saved tool-team cases, with CHECK_TOOL after the system prompt
  ../.venv/bin/python agents/run_team.py --rereview team_c4 --cases results/trackB/steered_cases.jsonl --log team_c9 --dry-run
  nohup caffeinate -i ../.venv/bin/python -u progress/guard.py \
    --job "voyager:c9=agents/run_team.py --rereview team_c4 --cases results/trackB/steered_cases.jsonl --log team_c9 --run-name C9-oct28" >> logs/guard_c9.log 2>&1 &
  ../.venv/bin/python agents/run_team.py --summary --log team_c9 --cases results/trackB/steered_cases.jsonl --table
                                                                        # + vs_original_prompt: with the sentence minus C4's prompt, paired by item
  # C10 (Oct 28): commit first: C9's answer_only review is the first turn, then the trace and a final answer
  ../.venv/bin/python agents/run_team.py --rereview team_c4 --first-from team_c9 --cases results/trackB/steered_cases.jsonl --log team_c10 --dry-run
  nohup caffeinate -i ../.venv/bin/python -u progress/guard.py \
    --job "voyager:c10=agents/run_team.py --rereview team_c4 --first-from team_c9 --cases results/trackB/steered_cases.jsonl --log team_c10 --run-name C10-oct28" >> logs/guard_c10.log 2>&1 &
  ../.venv/bin/python agents/run_team.py --summary --log team_c10 --cases results/trackB/steered_cases.jsonl --table
                                                                        # + vs_first_log (minus C9) and final_vs_own_answer
  ```
- **Out:** `results/trackC/team_live.jsonl` (every agent step, appended; a case is done at its
  `case_done` row), `team_live_summary.json`, `team_replay.jsonl` (all gitignored; `results/scope/`
  keeps the Oct 4 runs). **Time:** about 11 calls per tool-team case and 9 per no-tool case with two
  reviewer models. **Check:** the dry run's call count; the summary's case counts; undetermined checks.

- **Prepared Oct 31 (the 20-day program), for Shrey from about Nov 4:** C19 (H34), C25 (across agents), C20
  (pipeline vs model), C26 (a retrieval tool, SHOULD). Each one's lines, in order, and its reading command are in
  [`tracks/TRACK_C.md`](tracks/TRACK_C.md) §5a, and its pre-registration in `archive/sessions/2026-10-31/` (22:31–22:34).
  Add `--dry-run` to any `run_team.py` line first.

## 20. Session logs

- **What:** after every run (a Voyager batch, a Sol job, an analysis that changes a reported number)
  and at every stop, Ritik writes (Track A and shared work; Track C's logs go in `docs/trackC/sessions/`, Shrey's;
  Track B's in `docs/trackB/sessions/`, Arsha's from Nov 6)
  `archive/sessions/YYYY-MM-DD/YYYY-MM-DD_HHMM_<A|B|C|ALL>_<name>.md` (Arizona
  time), copies it to `archive/sessions/LATEST.md` and adds a line to `archive/sessions/INDEX.md`; and at
  the end of each day `archive/sessions/YYYY-MM-DD/DAILY_YYYY-MM-DD.md` (per track: what ran, what's in flight, key
  numbers, decisions waiting, tomorrow's plan).
- **Content:** header (times, branch, commits, tests, runs in flight), what ran, results, files,
  problems, points for review, decisions needed, open work, next commands. Numbers and paths only;
  under 250 lines; tracked in git.
