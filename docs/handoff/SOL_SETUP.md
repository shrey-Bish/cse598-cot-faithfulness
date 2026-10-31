# Sol setup for a second user (Shrey, Track C)

Last updated: 2026-10-30 17:20 MST. How to run the Sol kit (`cot-disclosure/finetune/gpu/sol/`) under your own
Sol user and course account: C13-style jobs (reviewers served by our own vLLM) and the rest. The kit's rules and
every job are in `cot-disclosure/finetune/gpu/README.md`; this page is what a second user does differently.

## What the kit does for you

- **Paths from `$USER`.** `sol/env.sh` puts everything under `/scratch/$USER`: `envs/olmo` (Python 3.11, the
  drivers), `envs/olmo-vllm` (vLLM's own environment), `hf` (`HF_HOME`), `trackA` (`TRACKA_OUT`, every job's
  output). The clone is `/scratch/$USER/cse598-cot-faithfulness`. Slurm's logs go to
  `/scratch/$USER/trackA/slurm/<job name>-<job id>.out` (`%u` in every job script).
- **Your own accounts file.** `sol/accounts.d/$USER.conf` lists the accounts you may submit under; when it
  exists it replaces `accounts.conf` (Ritik's) for you. Without it the kit falls back to `accounts.conf`, whose
  course account sbatch refuses if you aren't in it. Never edit `accounts.conf`.
- **Always `submit.sh`, never `sbatch` directly.** It passes your account with `-A`, checks the QoS limits
  against your own queue, and refuses anything else. Inside a job, `run.sh` stops under an account your file
  doesn't list, or outside a Slurm job.

## Before you start

- **Duo.** Every `ssh` and every `rsync` to `login.sol.rc.asu.edu` is one Duo push (ASU VPN on when off campus).
  Optional, so one push covers a working session, in `~/.ssh/config` on the Mac:
  `Host login.sol.rc.asu.edu` with `ControlMaster auto`, `ControlPath ~/.ssh/cm-%r@%h:%p`, `ControlPersist 4h`.
- **Space.** C13's two snapshots are about 106 GB (Granite 4.1 30B 57.7, Mistral Small 3.2 24B 48.0), the two
  environments roughly 15–20 GB more. Check your scratch quota and free space before `get_c13`.
- **On the Mac:** `export SOL_USER=<your Sol user>` in your shell profile. The rsync lines here and in the GPU
  README use it; on Sol, `$USER` is already that name.

## Setup, once

**1. Your course account** (login node):

```bash
sacctmgr show assoc user=$USER format=Account,Partition,QOS
sacctmgr -P show qos class format=Name,MaxTRES,MaxWall,MaxJobsPU,MaxSubmitPU,MaxTRESRunMinsPU
```

Take the CSE 598 course account (`class_cse598…`), never a lab account (`grp_…`).

**2. The clone:**

```bash
git clone -b trackC-main https://github.com/shrey-Bish/cse598-cot-faithfulness.git /scratch/$USER/cse598-cot-faithfulness
cd /scratch/$USER/cse598-cot-faithfulness
grep -q TRACKA_SCRATCH cot-disclosure/finetune/gpu/sol/env.sh && echo "per-user kit: ok"
```

No "ok": the branch doesn't have the per-user kit yet (Oct 30); it needs merging into `trackC-main`, then `git pull`.

**3. Your accounts file** (in the clone; it holds no secret and can be committed on `trackC-main`):

```bash
mkdir -p cot-disclosure/finetune/gpu/sol/accounts.d
echo "<your course account>  public  class  960  2  10  24  4" > cot-disclosure/finetune/gpu/sol/accounts.d/$USER.conf
```

The columns are `accounts.conf`'s: account, partition, QoS, then that QoS's limits: GPU-minutes
(MaxTRESRunMinsPU), running jobs (MaxJobsPU), queued jobs (MaxSubmitPU), MaxWall in hours, GPUs per job. Use the
numbers `sacctmgr` printed; the ones above are the class QoS's (checked Oct 30). If your partition or QoS isn't
the job scripts' `-p public -q class`, `submit.sh` passes yours instead.

**4. The environments and the import check** (a CPU allocation under your account; while open it takes one of
your 2 job slots):

```bash
salloc -A <your course account> -p public -q class -c 4 --mem=16G -t 1:30:00
cd /scratch/$USER/cse598-cot-faithfulness
module load mamba/latest
mamba create -y -p /scratch/$USER/envs/olmo python=3.11     # env.sh never creates it
bash cot-disclosure/finetune/gpu/sol/setup_env.sh             # torch 2.14.1 + requirements-sol.txt (5-15 min)
bash cot-disclosure/finetune/gpu/sol/setup_vllm.sh            # envs/olmo-vllm with vLLM 0.31.0 (10-20 min)
source cot-disclosure/finetune/gpu/sol/env.sh && cd cot-disclosure && \
    "$TRACKA_PY" finetune/gpu/import_check.py --vllm "$TRACKA_VLLM_PY"     # one line of versions; vLLM's first import can take ~10 min
exit
```

Or, after the `mamba create`: `submit.sh setup_env`, then `submit.sh setup_vllm` (jobs without a GPU). Every job
also runs the import check first and stops in seconds if an environment is broken.

**5. C13's snapshots** (no GPU; with `get_qwen8b` the only jobs that use the network; not gated, no token):

```bash
cot-disclosure/finetune/gpu/sol/submit.sh get_c13      # limit 3:00, into /scratch/$USER/hf
```

Its `.out` (`/scratch/$USER/trackA/slurm/trackC-get-c13-<job>.out`) must say both snapshots match the Hub; the
records are `/scratch/$USER/trackA/c13/snapshot_<model>.json`.

## A C13-style run

**Inputs by rsync** (Mac, from your clone's `cot-disclosure/`, where the Track C bundle put them; they hold text,
so never GitHub):

```bash
rsync -av results/trackC/team_c4.jsonl \
      $SOL_USER@login.sol.rc.asu.edu:/scratch/$SOL_USER/cse598-cot-faithfulness/cot-disclosure/results/trackC/
rsync -av results/trackB/steered_cases.jsonl \
      $SOL_USER@login.sol.rc.asu.edu:/scratch/$SOL_USER/cse598-cot-faithfulness/cot-disclosure/results/trackB/
```

**The job** (Sol, from the clone; one A100, both reviewers one after the other, resumable):

```bash
cot-disclosure/finetune/gpu/sol/submit.sh c13 --estimate 1.5      # limit 2:00 (Oct 29's run took 48 min)
squeue -u $USER
```

Its logs are written in the clone, `results/trackC/team_c13_granite.jsonl` and `team_c13_mistral.jsonl`; the
servers' in `/scratch/$USER/trackA/c13/vllm_<model>.log`. A job that runs out of time resumes in the next one:
submit the same line again.

**Copy-back** (Mac, from `cot-disclosure/`). The Track C bundle already has C13's logs from Oct 29 under those
names, so copy a new run back under its own name:

```bash
S=$SOL_USER@login.sol.rc.asu.edu:/scratch/$SOL_USER/cse598-cot-faithfulness/cot-disclosure/results/trackC
rsync -av $S/team_c13_granite.jsonl results/trackC/team_c13_granite_$(date +%m%d).jsonl
rsync -av $S/team_c13_mistral.jsonl results/trackC/team_c13_mistral_$(date +%m%d).jsonl
../.venv/bin/python agents/run_team.py --summary --log team_c13_granite_$(date +%m%d) \
      --cases results/trackB/steered_cases.jsonl --table
```

The other jobs work the same way under your user; their lines and outputs are in the GPU README
(`/scratch/$USER/trackA/<step>/`; on the Mac, `$SOL_USER` in place of a user name).

## Limits (the class QoS, per user; `sacctmgr`, Oct 30)

| Field | Value |
|---|---|
| MaxTRES (per job) | cpu=32, gres/gpu=4, mem=320G |
| MaxWall | 24 h |
| MaxJobsPU (running) | 2 (an open `salloc` counts) |
| MaxSubmitPU (running + pending) | 10 |
| MaxTRESRunMinsPU | gres/gpu=960: each running job's remaining time × GPUs; one 1-GPU job up to 16 h |
| Flags | DenyOnLimit: a job whose own request is over the limit is rejected at submission |

`submit.sh` sets each limit to the estimate × 1.3, refuses a job over your row's GPU-minutes or MaxWall, and
counts your running and pending jobs (`squeue -u $USER`) before it submits.

## Known traps

- **Fixed vLLM ports** (8011 Olmo evaluation, 8012 Track B, 8013 C13). Two vLLM jobs on one GPU node, yours and
  Ritik's, would share a port: the second server can't start, or its runner reaches the other job's server.
  If a c13 job fails at the server start, or its reviews fail on the model name, look for another vLLM job on
  that node (`squeue -o "%i %u %j %N"`) and resubmit with `--exclude=<node>` (submit.sh passes it to sbatch).
- **`.out` files** stay in `/scratch/$USER/trackA/slurm/` even if you set `TRACKA_SCRATCH` (an `#SBATCH` line
  reads no variable).
- **`TRACKA_SUBMIT_ACCOUNT`** must name an account in your own file; anything else is refused.
- **No keys on Sol.** Nothing here needs one: both C13 models are public and the reviewers run on your own GPU.
