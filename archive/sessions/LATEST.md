# Session log: B1's generation engine diagnosed and fixed; Sol's update reviewed (2026-10-31 11:50 MST)

Project: CSE 598 Group 10, Track A (B1) and the Sol kit. **By:** Ritik. No calls and no GPU from the Mac. Nothing
was started on Sol; the lines below are for Ritik.

## a. What Ritik reported (Sol, ~10:40)

- **provenance_gen:**
  - 1/4 66989478 and 2/4 66989491 TIMEOUT at 6:00;
  - 3/4 66989506 and 4/4 66989507 running, until their limit at ~12:15–12:25.
- **Eval:**
  - tags 1/2 and 2/2, and lora_tags 1/2: COMPLETED;
  - lora_tags 2/2 66989534 and lora_attn3 1/2 66989537: running;
  - lora_attn3 2/2 66989539: pending.
- **Four jobs ran at once,** although `sacctmgr` says MaxJobsPU 2. Noted; not a problem.
- **B1's runs files so far:**
  - alpha 1: p1 56 of 56, p2 23 of 56, p3 49 of 49, p4 44 of 49;
  - deployable 0.25: p1 2 of 56;
  - oracle: 0.
  That is 174 of 630 runs, and none is read. B1's rule (log 2026-10-30 17:15) waits until every configuration is
  complete.
- **The Slurm logs:** many "memory allocation failed with OOM" lines; 22–31 generated tokens/s; batches of 2.0–2.8.

## b. Diagnosis

### Where the time went: the batches (reconstructed from the runs files)

Runs ending in the same second came from one `generate` call. The batches run one after another (one worker
thread), so a batch's duration is the gap between consecutive end times.

| part | runs | batches | runs per batch | tokens/s (saved runs' tokens over the part's time) |
|---|---|---|---|---|
| 1/4 | 56 | 28 | 2.0 | 30.5 |
| 2/4 | 23 | 13 | 1.8 | 20.9 |
| 3/4 | 49 | 24 | 2.0 | 35.3 |
| 4/4 (so far) | 44 | 27 | 1.6 | 31.5 |

**Every part's first batch had 6 runs. After that, batches fell to 1–2.** In part 3, the oldest request rides along
in each batch (its `seconds` counts from 13:15:47, the job's start), and only 4, then 3, then 2 fresh requests join:

```
13:53:14  6 runs   (all waiting since the start)
14:05:15  5 runs   (1 from the start + 4 fresh)
14:13:01  4 runs   (1 + 3)
14:38:46  3 runs   (1 + 2)   ... then 2, 2, 1, 1
```

### Cause 1: the scheduler (`Batched._work`, as at a752db5)

```python
first = held.pop(0) if held else self.q.get()
...                                   # then only *fresh* queue arrivals join, within 2 s:
if r["key"] == first["key"] and used + c <= self.budget: batch.append(r)
else: held.append(r)
```

A request set aside once (`held`) could only lead a later batch; it never joined one. The key is (temperature,
stop strings). Runs with the inserted tool turn have a stop string (`</function_calls>`); the others don't. So
about 3 of every 7 arrivals were set aside behind the other kind. Each batch took 1 request out of `held` and put
more in. `held` came to hold most of the 16 runs in flight, and batches came down to "the oldest held one +
whatever had just arrived".

### Cause 2: static batches wait for their longest reply

`generate` ends a batch when its last row ends. Replies here run from ~1K to 32K tokens (finished runs: mean 10,587,
median 8,921, longest 32,127). The finished rows keep producing padding until then, at the batch's step cost. The
batches of 6: 31, 27, 67 and 49 tokens/s, depending on how long their longest reply was.

### The "OOM" lines: allocator retries, not failures

- **No batch failed.** An out-of-memory exception would have sent a batch back one run at a time. The batches
  counter would then show extra entries, and it doesn't: part 3, 49 runs over 24 `generate` calls, is the
  logged "batches 2.0 on average".
- **The lines are PyTorch's caching allocator:** an allocation failed, it freed its cached blocks, and it retried
  (`CUDACachingAllocator.cpp:3934`).
- **The failed size grows smoothly within a phase:** 92 MB → 860 MB over 06:19–06:52 in part 3; 904 MB → 1.33 GB
  over 10:28–10:44, both in each phase's first, 6-row batch. 1.33 GB is one full-attention layer's keys for
  6 rows × ~27K tokens (× 8 KiB a token). `DynamicCache` grows each full layer by `torch.cat` at every step, so
  each step allocates a slightly larger block than the one it frees. The cache fragments until the allocator
  must empty itself.
- **They happen in the big first batch** because the old budget allowed 6 rows, counting each at prompt +
  16,000 tokens, and replies ran to 25–32K.

### The hypotheses Ritik listed, checked against the code (transformers 5.18.0, torch 2.14.1: the Mac's `.venv` has Sol's versions)

| hypothesis | finding |
|---|---|
| full-length KV kept for the 24 sliding layers | **no.** `generate` builds `DynamicCache(config=…)` (`generation/utils.py`: `dynamic_cache_kwargs = {"config": …}`), which makes `DynamicSlidingWindowLayer` for the sliding layers: 4,095 tokens each. The observed sizes rule it out too: at 0.5 MiB a token, 6 × 27K tokens would be 81 GB of cache. |
| DynamicCache growing by concatenation, fragmenting | **yes** (above): the source of the allocator retries, and a full copy of each full layer's cache per step (part of the per-token cost below) |
| the padded head dimension pushing sdpa onto the math kernel | **not a memory risk.** 128 + 8 = 136 is a multiple of 8, so the efficient kernels accept it. A decode step has one query, so the scores are rows × 32 × 1 × context: megabytes, even on the math kernel. Prefill is the prompt only (≤ ~1K tokens; one of 6.5K). The augmented layers do copy their keys and values each step (3 of the 8 full layers). |
| the batch budget (0.5 MiB/token) | **wrong both ways.** 0.5 MiB/token assumed all 32 layers at full length; the true cost is 128 KiB a token (8 full layers) + 1.5 GiB a row (24 sliding layers at 4,095). And `reserve=16000` counted each reply as at most 16,000 tokens, when they run to 32,768. |

### The cost of one decode step, fitted to the 88 old batches (R² 0.86)

**ms per step = 35.7 + rows × (2.54 + 0.000500 × context)**
- 35.7 ms: the fixed part (weights, Python);
- 2.54 ms a row: the sliding windows;
- 0.5 µs a row per token of context: the full layers' keys and values, read and copied.

### What each change buys (simulated with that cost, 456 runs drawn from the finished runs' lengths)

| batches | finished rows leave | tokens/s | 456 runs, GPU-h (lengths × 1, × 1.15) |
|---|---|---|---|
| 6, all rows to the end (the scheduler fixed only) | no | 36 | 37, 45 |
| 8, all rows to the end | no | 37 | 36, 44 |
| **8** | **every 512 tokens** | **62** | **21.5, 25.5** |
| 12 | every 512 | 74 | 18, 21.5 (doesn't fit at full length) |
| 16 | every 512 | 82 | 16, 19 (doesn't fit) |

Fixing the scheduler alone barely helps (36–37 against 21–35): static batches still wait for their longest reply.
Letting finished rows leave is what doubles it. 8 rows is the most that fits if every row reaches 32,768 tokens
(8 × 5.6 GiB = 45 GiB of cache, beside 13.6 GiB of weights and the per-step copies).

## c. The fix (`finetune/gpu/provenance_job.py`, `Batched`; `run.sh`)

1. **The scheduler:** one first-come list. A batch is the oldest pending request plus each later one with its
   key, while the batch fits. Held requests now batch together. Tested: the case that gave 4, 1, 1, … gives 4, 4,
   2, 2.
2. **The budget at full length** (`--kv-gib 48`, the default for `generate`): a batch's key/value cache if every
   row reached its `max_tokens`, padded to the longest prompt (`hf_engine.kv_bytes_per_request`, sliding layers
   at their window). Tested on the real config: 8 rows of 1,000 + 31,768 tokens fit, 9 don't. No mid-batch
   out-of-memory by construction.
3. **Finished rows leave** (`--shrink-every 512`): `generate` runs 512 tokens at a time, continuing from the
   batch's own `DynamicCache`. The rows that ended (an end id, a stop string, their cap) leave it
   (`cache.batch_select_indices`). Every step is still `generate`'s one-token decode with the same cache class,
   the same hook and the same sampling. Tested on CPU: greedy, left-padded, oracle span at alpha 0.1, rows
   leaving at 3, 5 and 7 tokens give exactly one whole-batch `generate`'s tokens.
4. **`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`** for `provenance_gen` and `provenance_bench` only
   (`run.sh`; tested). The cache's growth no longer fragments the allocator. vLLM jobs are untouched.
5. **The time limit:** at Slurm's warning, a batch ends after its current round (512 tokens, under a minute) and
   the job exits. The runs it cut short aren't saved, and the next job redoes them; before, a running batch was
   killed at the limit. Tested.

**Not used, and why:**
- **A static (preallocated) cache:** it attends over the whole preallocated buffer and changes the cache class,
  a different code path from the 174 runs done.
- **Length-sorted batches:** a reply's length isn't known before it runs, and the prompts are all ~300–1,000 tokens.
- **A lower budget:** fewer rows, slower.
- **Re-prefilled continuous batching:** it changes the decode path.

**Ruling (Ritik's to accept): "the same code path".** alpha = 1 and the chosen alphas stay on one code path:
- every remaining run (alpha 1's 36 and the chosen alphas' 420) goes through the new engine;
- every step of every run, old or new, is `generate`'s one-token decode with `DynamicCache`, the hook and the
  same sampling;
- what changed is which rows share a batch over time, which always varied (1–6 rows).

The 174 runs done stay. *The stricter alternative:* rerun all 210 alpha = 1 runs on the new engine, +174 runs,
about +10 GPU-h.

**Tests added:**
- 6 in `tests/test_provenance.py` and `tests/test_provenance_jobs.py`: rows leave with the same tokens; a stop ends
  the batch after its round; held requests batch together; the budget, padded; 8 full-length rows fit 48 GiB on
  the real config; bench and plan on a tiny model;
- run.sh's step and allocator setting, and submit.sh's new kind and dependency.

The provenance, engine and kit tests: 128 passed. The full suite is in §h.

## d. The benchmark job (`provenance_bench`, limit 1:00)

```bash
cot-disclosure/finetune/gpu/sol/submit.sh provenance_bench -- --items-from /scratch/ragarw68/trackA/setA/items.jsonl \
    --alpha-from /scratch/ragarw68/trackA/provenance_forced/provenance_forced.json
```

It runs on **set A's questions, never the 30**, and reads no answer:
1. **Decode grid:** ms per step and peak memory for 1, 4 and 8 rows at 8,192 and 30,000 tokens of context (a real
   set A prompt with its marked tool turn, repeated; prefilled in chunks), at alpha 1 and 0.25. The fit
   a + rows × (c + d × context) comes from these cells.
2. **Before and after:** 16 set A runs (B1's own job types), capped at 1,024 tokens. The **before** is a752db5's
   `Batched`, loaded from git; the **after** is the new one. Each runs at alpha 1 and 0.25 and reports tokens/s,
   mean batch size, peak memory and allocator retries. The cap shortens runs, so these numbers show the batching
   (sizes), not the full-length gain.
3. **Projection:** the new and the old engine at full length, simulated with the grid's cost and the finished
   runs' lengths, for the runs left, in GPU-h.

**Its line** is the last console line, also in `/scratch/ragarw68/trackA/provenance_bench/bench.json` ("line"). It
starts with `B1 bench, 16 set A runs capped at 1024 tokens:`. Send it to me before the resubmits.

## e. The re-plan

`provenance_job.py plan` reads the runs files and the bench's projected rate, and prints the fewest parts by
question whose largest estimate fits 4.5 h. submit.sh's limit is the estimate × 1.3, so each part gets 6:00. A part
skips every run already finished, so the parts resume.

On the Mac's copies, at the projected 60 tokens/s, with the finished runs' mean reply × 1.15 (the runs cut short
were the long ones):
- 456 runs left;
- 7 parts, of 56–77 runs and 3.3–4.5 h each;
- **26.8 GPU-h** (21.5–25.5 by the simulation's range).

The plan run on Sol after 3/4 and 4/4 end, with the bench's measured rate, gives the lines to submit.

## f. Sol's update: the review

**The earlier "safe to pull" (log 2026-10-30 22:30 §f) compared the wrong starting point.** It compared `50076f2`
with `a752db5`. Sol's clone is at `427f39e` with rsync copies on top. Ritik's
`results/sol_tree_vs_a752db5.diff` compares Sol's actual files with a752db5:
- 39 files, all under `cot-disclosure/finetune/`;
- `-` lines are what a pull brings; `+` lines are what Sol has now.

**The Sol kit, for user ragarw68** (`$USER` = `id -un` = ragarw68, no `accounts.d/ragarw68.conf`,
`TRACKA_SCRATCH` unset):

| file | change | for ragarw68 |
|---|---|---|
| `env.sh` | paths from `TRACKA_SCRATCH=${TRACKA_SCRATCH:-/scratch/${USER:-$(id -un)}}` instead of `/scratch/ragarw68` | the same: `envs/olmo`, `envs/olmo-vllm`, `HF_HOME=/scratch/ragarw68/hf`, `TRACKA_OUT=/scratch/ragarw68/trackA` |
| `guard.sh` | `accounts.d/$USER.conf` if it exists, else `accounts.conf`; messages name the file | the same: no `accounts.d/` exists, so accounts.conf; the same account check |
| `accounts.conf` | comment lines only | the same row: `class_cse59888883fall2026 public class 960 2 10 24 4` |
| `submit.sh` | accepts accounts.conf's account as the scripts' `-A`; overrides partition and QoS only for another user's account; `mkdir` of `/scratch/${USER:-$(id -un)}/trackA/slurm` | the same: the default account is the scripts' `-A`, its partition and QoS are listed, and nothing is overridden |
| `run.sh` | a comment (`/scratch/$USER/...`) | the same |
| every `.sbatch` | `-o /scratch/%u/trackA/slurm/%x-%j.out` instead of `/scratch/ragarw68/...` | the same: `%u` is ragarw68 |
| `qwen8b_step3.sbatch`, `qwen8b_step10.sbatch` | not on Sol | arrive with the pull (Sol's `run.sh` already names the steps) |

**Code:**
- `eval_job.py` and `plan_eval.py`: `out_root()` falls back to `/scratch/{getpass.getuser()}/trackA` (the same),
  and docstrings.
- `kit.py`, `plan_training.py`, `source_tags.py`, `__init__.py`, `checkpoint_check.py`: docstrings or a message.
- `eval.py`: only `label_sheets` (the `guess_trained` column and rows running on from part 1 into part 2). **Sol
  doesn't have it yet,** so L4's sheets need the update.
- `gate3.py`, `look/qwen8b_mech.py`: not on Sol; they arrive with the pull.
- `finetune/README.md`, `finetune/PROVENANCE.md`: moved to `docs/` on Oct 30. No code opens them.

**Since a752db5** (this session's commit): `provenance_job.py` (B1's engine, bench, plan), `run.sh` (the
`provenance_bench` step, the allocator setting for B1's two kinds), `submit.sh` (provenance_gen may wait for
provenance_bench), and the new `provenance_bench.sbatch`. The eval path is untouched.

**The pending job 66989539** (eval lora_attn3 2/2, vLLM):
- Slurm stored its batch script at submission, but `run.sh`, `env.sh`, `guard.sh` and the Python code are read
  from the clone when it starts.
- After the pull, each resolves to the same paths and account, and its code path (eval_job.py with
  `--engine vllm`, eval.py's runs, hf_engine) is unchanged. **Safe.**

**The running jobs:**
- **Python:** has its modules in memory.
- **bash:** git replaces a changed file by unlinking it and writing a new one, and the stash and checkout do the
  same. A running `run.sh` keeps reading its old copy.
- **Inputs:** everything the jobs read in the clone is gitignored (`results/trackA|B|C/`, `finetune/data/`,
  `logs/`; checked with `git check-ignore`), so `git stash -u` doesn't touch it.
- **Safe.**

**B1's resubmits** need the update: they run the new engine and the bench.

**Decision: update now** (once this session's commit is on GitHub):
- every job still to start needs it: L4's guess column, Qwen3-8B's script and job files, B1's engine and bench;
- nothing queued or running changes behavior.

From then on, Sol updates by `git pull --ff-only` only, no rsync of code.

## g. The Sol lines, in one order

```bash
# ---- 1. Sol login node: the update (after Ritik pushes this session's commit)
cd /scratch/ragarw68/cse598-cot-faithfulness
git branch --show-current                     # expect trackA-nosol
git log -1 --format=%h                        # expect 427f39e
git status --porcelain --untracked-files=all | grep '^??' | head -40   # untracked files the stash will set aside (results/ is gitignored, untouched)
git fetch origin
git diff --stat origin/trackA-nosol -- . ':(exclude)cot-disclosure/finetune' | tail -15   # outside finetune/: expect agents/, progress/, tools/, tests/, docs; no .sh/.sbatch/.conf
git stash push --include-untracked -m "Sol's rsync copies before the Oct 31 pull"
git pull --ff-only origin trackA-nosol
git log -1 --format='%h %s' | cut -c1-90      # expect the hash Ritik pushed
git status --short | head                     # expect nothing
git stash list | head -3                      # keep it until the queue has run clean; then: git stash drop

# ---- 2. L4's sheets (login node, no GPU; the texts are on Sol), then to the Mac
source cot-disclosure/finetune/gpu/sol/env.sh
"$TRACKA_PY" cot-disclosure/finetune/eval.py --label-sheets --dry-run --out /scratch/ragarw68/trackA/eval   # expect 294 and 292
"$TRACKA_PY" cot-disclosure/finetune/eval.py --label-sheets --out /scratch/ragarw68/trackA/eval
head -1 /scratch/ragarw68/trackA/eval/label_L4/part1.csv  # expect ...,label_final,guess_trained,note
#   Mac, from cot-disclosure/:  rsync -av ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/trackA/eval/label_L4/ results/labels/gate3/L4/

# ---- 3. B1's speed check (1:00; starts when a GPU frees, e.g. when 3/4 and 4/4 end ~12:20)
S=cot-disclosure/finetune/gpu/sol/submit.sh
F=/scratch/ragarw68/trackA/provenance_forced/provenance_forced.json
$S provenance_bench -- --items-from /scratch/ragarw68/trackA/setA/items.jsonl --alpha-from $F

# ---- 4. Qwen3-8B, its rule fixed Oct 30 (fd1a679): Step 3, then Step 10 after it
(cd cot-disclosure && "$TRACKA_PY" finetune/look/qwen8b_mech.py step3 --dry-run)
$S qwen8b_step3 --estimate 1.2                                            # limit 2:00
$S qwen8b_step10 --estimate 4.3 --dependency=afterok:<the qwen8b_step3 job id>   # limit 6:00

# ---- 5. After the bench ends and 3/4, 4/4 have stopped: the plan, then its lines as places free (MaxSubmitPU 10)
tail -1 /scratch/ragarw68/trackA/provenance_bench/console_*.log      # the bench's line: send it to Ritik's session
"$TRACKA_PY" cot-disclosure/finetune/gpu/provenance_job.py plan --out /scratch/ragarw68/trackA --alpha-from $F
#   then each printed line, e.g.  $S provenance_gen --estimate 4.4 -- --alpha-from $F --part 1/7
```

**The queue:**
- **Now:** 5 jobs (3/4, 4/4, lora_tags 2/2, lora_attn3 1/2 running; lora_attn3 2/2 pending).
- **Steps 3–4:** add 3 (the bench, Qwen Step 3, Qwen Step 10), making 8 of 10.
- **When 3/4 and 4/4 end:** 6. The plan's 7 B1 parts go in as places free.
- **The GPU limit** (960 GPU-minutes of remaining time across running jobs) allows about two 6-hour jobs at once.
  At 2 at a time: ~27 GPU-h of B1 + ~5.5 of Qwen3-8B, about 17 hours of wall clock.

## h. Checks and commit

- **The full test suite:** 648 passed, 0 failed. A first full run had 2 failures: make_supplement crashed on LoRA on 15/19/23's "too few questions" intervals. That is fixed and tested; the test fails on the old code.
- **The tools:** `tools/check_links.py`, `tools/make_supplement.py --check`, `tools/make_gantt.py`.
- **Commit:** as Ritik. **Not pushed:** pushing waits for Ritik's OK, and Sol's update needs that push.
- **Mac-only file:** `results/sol_tree_vs_a752db5.diff` stays untracked.
