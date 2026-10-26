# Track A GPU kit: ASU Sol

The look-inside steps that need the weights (Steps 8–10), and the Sol plumbing every later GPU
step (11–13) reuses. Everything runs from the repo's `cot-disclosure/` folder in the project
environment `/scratch/ragarw68/envs/olmo` (Python 3.11). Never use the system `python3` (3.6.8).

| Item | Script | Reads | Output on Sol | One A100 80GB |
|---|---|---|---|---|
| 1. environment + smoke | `sol/setup_env.sh`, `smoke.py` | the cached model | `/scratch/ragarw68/trackA/smoke/smoke.json` | setup 5–15 min (downloads); smoke 2–5 min |
| 2. Step 8: checkpoint check | `checkpoint_check.py` | Step 1, Oct 21 and canary echoes | `/scratch/ragarw68/trackA/step8/step8_checkpoint.json` | 5–10 min |

## Rules every script follows

- **Account.** Every job runs under `class_cse59888883fall2026` (the CSE 598 section), never the
  lab's `grp_hdavulcu`. `sol/submit.sh` always passes `-A class_cse59888883fall2026` itself and
  refuses a job script that names another account, or any account option you add. Inside a job,
  `sol/run.sh` checks `$SLURM_JOB_ACCOUNT` and stops under any other account, and also stops
  outside a Slurm job (login nodes). Don't call `sbatch` directly.
- **Where.** `-p public -q class -G a100:1` (class QoS: at most 24 h, 4 GPUs, 32 cores, 320 GB
  per job; 2 running and 10 queued jobs, and 960 GPU running minutes in all). Your open session
  counts against the 960, so while it's open, run in the session. Batch jobs ask for at most
  16 h and resume from their own checkpoints. Quick script tests: `-q debug` (15 min). Setup
  without a GPU: `-p lightwork -q public`.
- **Model.** `allenai/Olmo-3-7B-Think` from `HF_HOME=/scratch/ragarw68/hf`, offline
  (`HF_HUB_OFFLINE=1`). Every output records the snapshot's commit hash and whether it is
  `d97e442`, the revision our template came from. If it isn't, the kit says whether its files,
  and at least its weights, equal d97e442's. It checks this offline: the cache names each file by
  its hash, and `olmo3_7b_think_d97e442.json` lists d97e442's hashes. On Oct 26, `main` was
  d97e442, and the weights were the same in 24 of the repo's 25 revisions (all but the first).
- **Outputs.** `$TRACKA_OUT/<step>/` = `/scratch/ragarw68/trackA/<step>/`, plus a console log
  there. Only the small summary file of each step comes back to the Mac
  (`cot-disclosure/results/trackA/gpu/`, committed).
- **No API keys on Sol.** Anything compared with Voyager uses values already saved on the Mac
  (the result files below).

## 0. Code and data onto Sol

### Code

Checked on the Mac, Oct 26:

| Check | Result |
|---|---|
| repo private? | **No.** `shrey-Bish/cse598-cot-faithfulness` is **public** (`gh repo view`). Don't push Track A to it until the owner makes it private. |
| a tracked file over 50 MB? | No. Largest: `results/trackA/takeover_probes.jsonl.gz`, 15.7 MB (`tests/test_repo_size.py` passes) |
| a GPQA file tracked? | No. No tracked file name contains "gpqa", and no `.gz` result contains a GPQA record; 7 code, config and doc files mention it by name only |

**Today, without GitHub: a git bundle** (the committed branch only; the Steps 6–7 files the Mac
is still writing stay out). On the Mac:

```bash
cd ~/Documents/Projects/ODL/cse598-cot-faithfulness
git bundle create ~/trackA.bundle trackA-nosol
scp ~/trackA.bundle ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/
```

On Sol, the first time:

```bash
git clone -b trackA-nosol /scratch/ragarw68/trackA.bundle /scratch/ragarw68/cse598-cot-faithfulness
```

After each update: make a new bundle, `scp` it the same way, then on Sol
`cd /scratch/ragarw68/cse598-cot-faithfulness && git pull /scratch/ragarw68/trackA.bundle trackA-nosol`.

**Once the repo is private:** `git push origin trackA-nosol` on the Mac, then on Sol
`git clone -b trackA-nosol https://github.com/shrey-Bish/cse598-cot-faithfulness.git /scratch/ragarw68/cse598-cot-faithfulness`
(a private clone needs a GitHub token or SSH key on Sol).

The commands below assume the clone is at `/scratch/ragarw68/cse598-cot-faithfulness`; `cd` there first.

### Data

Steps 8–10 read these result files. They are committed, so the clone (or bundle) already carries
them. `finetune/gpu/inputs_manifest.json` holds their sizes and sha256, and every step checks them
before it runs (`python finetune/gpu/kit.py --check-inputs` checks all of them).

| File (under `cot-disclosure/`) | Size | Used by |
|---|---|---|
| `results/trackA/voyager_capabilities.jsonl.gz` | 0.10 MB | Step 8: Step 1's echo log-probs (old route) |
| `results/trackA/voyager_ids_check.jsonl.gz` | 0.30 MB | Step 8: the Oct 21 echoes (low / medium / high; default = Instruct, the negative control) |
| `configs/canary/olmo3-7b-think.json` | 0.07 MB | Step 8: the canary text and its reference log-probs |
| `results/trackA/base_format.jsonl.gz` | 7.25 MB | Steps 9, 10: the Step 2b runs (prompts, reasoning) |
| `results/trackA/takeover_runs.jsonl` | 0.15 MB | Step 9: Step 3's outcome and takeover point per run |
| `results/trackA/takeover_cases.jsonl` | 0.01 MB | Step 10: Step 3's default cases |
| `results/trackA/deletion_runs.jsonl` | 0.15 MB | Step 10: Step 4's results, for the cut (ii) cross-check |
| `results/progress/expB_cued.jsonl` | 2.70 MB | Steps 9, 10: which questions and hint letters Step 2b used |
| `data/progress/mmlupro_30.jsonl` | 0.03 MB | Steps 9, 10: the questions and answer keys |

If a check fails (or you clone without the results), copy them from the Mac:

```bash
cd ~/Documents/Projects/ODL/cse598-cot-faithfulness/cot-disclosure
rsync -av --relative \
  results/trackA/voyager_capabilities.jsonl.gz results/trackA/voyager_ids_check.jsonl.gz \
  configs/canary/olmo3-7b-think.json results/trackA/base_format.jsonl.gz \
  results/trackA/takeover_runs.jsonl results/trackA/takeover_cases.jsonl \
  results/trackA/deletion_runs.jsonl results/progress/expB_cued.jsonl data/progress/mmlupro_30.jsonl \
  ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/cot-disclosure/
```

### Results back

Summary files only, from the Mac (each step below names its file):

```bash
cd ~/Documents/Projects/ODL/cse598-cot-faithfulness/cot-disclosure
mkdir -p results/trackA/gpu
scp ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/trackA/smoke/smoke.json results/trackA/gpu/
```

## 1. Environment and smoke test

Installs pinned torch 2.14.1 (the CUDA 13.0 build; the driver reports CUDA 13.4 and runs any build
up to it), transformers, accelerate, peft and the repo's requirements into the existing
environment (`requirements-sol.txt`; no vLLM until Steps 12–13). Then loads the model in bf16 on
the GPU, generates 32 tokens (greedy) in our pinned Think format, and prints the GPU name, library
versions, the snapshot hash (and whether it matches d97e442), whether the snapshot's own chat
template renders our prompt exactly, and the config fields the later steps need (layers, heads,
key/value heads, hidden size, max positions, sliding-window settings, tie_word_embeddings).

**In your session** (from the clone):

```bash
cd /scratch/ragarw68/cse598-cot-faithfulness
bash cot-disclosure/finetune/gpu/sol/setup_env.sh        # 5-15 min, once
cot-disclosure/finetune/gpu/sol/run.sh smoke              # 2-5 min
```

**Batch:** `cot-disclosure/finetune/gpu/sol/submit.sh setup_env` (lightwork, no GPU), then
`cot-disclosure/finetune/gpu/sol/submit.sh smoke` (debug QoS, 15 min). Log:
`/scratch/ragarw68/trackA/slurm/trackA-smoke-<job>.out`.

**CPU test (Mac):** `python -m pytest tests/test_trackA_gpu_kit.py` (a tiny random Olmo 3 with the
real tokenizer; the offline snapshot check; the account guards), and
`python finetune/gpu/smoke.py --dry-run` (the real config; the memory check refuses the Mac:
the model needs ~15.6 GiB).

**Look for:** `snapshot d97e442… matches d97e442`, `renders our prompt exactly`, the A100 and
CUDA 13.0 in the versions, and a sensible start of reasoning in `generated:`.

**Back to the Mac:** `/scratch/ragarw68/trackA/smoke/smoke.json` (a few KB).

## 2. Step 8: checkpoint check

Is Voyager's `olmo3-7b-think` the checkpoint we load? A local forward pass over the saved texts
whose per-token log-probabilities Voyager returned by echo, compared token by token with the
two-part rule (`docs/PLAN.md`, Track A):

- **Strict on the first 2,047 tokens:** the same top token at every position, and max absolute
  log-prob difference under 0.01.
- **Beyond that** (Voyager seems to process long prompts in 2,048-token chunks): the mean, median
  and max difference, and top-token mismatches counted only where they are not near-ties. A
  near-tie means the two tokens are within 0.1 probability of each other: under the local model,
  and under Voyager too when its saved top tokens include both. A mismatch outside a near-tie fails.

| Reference | Tokens | Saved |
|---|---|---|
| `step1_old_route` | 5,185 | Step 1 call 8, `olmo3-7b-think` before the Oct 21 ID change |
| `oct21_low`, `oct21_medium`, `oct21_high` | 5,185 each | the same text through `olmo3-7b` at each effort |
| `canary` | 530 | the identity canary's reference (all of it falls in the strict part) |
| `oct21_default` (negative control) | 5,185 | the same text at the default effort = the **Instruct** checkpoint; it must fail |

The rule is applied to the bf16 pass, the dtype every GPU step uses. An fp32 pass with the same
weights (loaded once in fp32, then cast to bf16, which is exact) is reported beside it, to tell
numerics from a different checkpoint. For scale: Voyager against itself (old vs new route) was
max 0.0003 in the strict part, mean 0.006 / max 0.19 beyond, with 24 mismatches, all near-ties.
The Instruct model against Think gave 654 mismatches, mean 0.32 and max 20.7.

**In your session:** `cot-disclosure/finetune/gpu/sol/run.sh step8` (5–10 min, peak ~32 GiB).
**Batch:** `cot-disclosure/finetune/gpu/sol/submit.sh step8` (class QoS, 30 min).
**CPU test (Mac):** `python -m pytest tests/test_trackA_checkpoint.py`. This covers the rule on
synthetic log-probs (a strict-part difference, near-ties, a mismatch outside one, Voyager-side
gaps), echo alignment, and an end-to-end run on a tiny random Olmo 3 whose own log-probs stand in
for Voyager's. `python finetune/gpu/checkpoint_check.py --dry-run` checks the references and
alignment (all 5 Think references align token for token; the control has 5 positions tokenized
differently, so it is compared on the rest).

**Look for:** the table, then `verdict: PASS (bf16)`. If it fails, the strict part's `worst` and
`mismatches` and the beyond part's `outside_examples` in the JSON show where. Per-position
differences are in `step8_positions.npz`.

**Back to the Mac:** `/scratch/ragarw68/trackA/step8/step8_checkpoint.json` (tens of KB).
