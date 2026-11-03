# Session log: the Sol re-plan on the course account, and A18 read (2026-11-03 15:14 MST)

By: Ritik. Ritik's message of about 14:50, eight items.

## What Ritik reported and asked

**What Ritik found on Sol:**
- Sol is busy, not closed. There is no reservation. `sinfo -s` showed `public` 164 allocated, 0 idle, 166 total;
  `htc` 208/1/212; `general` 97/2/100.
- `--test-only`'s "Nov 14" starts are worst cases and no use for planning. The real 1-GPU bench, job 389340
  (`a39_1gpu`, `base e2 2/2 --limit 96`), shows START_TIME 2026-11-03T16:12 in `squeue --start`. **From now on, time
  estimates come from `squeue --start` on real jobs.**
- B20's three downloads (388229, 388230, 388273) are running and took both running-job slots: the class QoS counts
  jobs without a GPU too. Ritik cancelled a duplicate Nemotron download (388274).
- The H100s aren't available. **The course account only; no other account.**
- A18 was copied back to the Mac. Its cut counts are 30, 22, 30, 22, 18 and 12, as planned.

**The re-plan, for the earliest finish:**
1. A39 on E2 as 1-GPU parts sized to start early (limits of about 2–4 h), in priority order: base, prompt_only,
   LoRA, LoRA + note first, then the wrapper systems. The first wave's lines now, up to the 10-submission limit
   (389340 counts as one), and the rest as waves.
2. A `--test-only` line for whether the class QoS can use `htc` (4 h limit) as well as `public`; if it can, an option
   in `submit.sh`, used where it helps.
3. `a39.sbatch` asks for one node; `submit.sh` doesn't count jobs without a GPU as GPU-minutes; downloads don't block
   GPU work (when to submit them).
4. A39 on the 30: dropped unless it fits after E2 and B20 by Nov 12; say which.
5. B20: the smokes after A39's first wave, smallest model first; what the parser `grep` means for each model
   (Granite's plugin especially).
6. B1R2: decided Nov 8 from what the course account can still fit by Nov 15; if it can't, F38 records "not run: no
   GPU time by Nov 15".
7. A18 read by its rule, in plain words; what it changes in the story and README; slide 10.
8. PLAN's calendar; the standing rules.

## 1. What was done, in order

1. **The A39 amendment came first** (the 11:30 log's §10, committed `9fc52d6` at 14:59, before the bench started):
   - **job shapes:** E2 on 1-GPU parts, the core systems 4 parts each (limit 3:00) and the wrapper systems 2 each
     (2:30), round-robin with the core first; the bench is 1-GPU only;
   - **the 30:** kept, from compute only, and dropped if E2 and B20 aren't done by Nov 11 09:00;
   - **B1R2:** decided Nov 8 09:00, from GPU-hours delivered against needed.
   - No rule, system, design or run changes.
2. **The Sol kit (item 3; tests first, 6 failing, then all passing):**
   - `a39.sbatch` asks for one node (`-N 1`). One vLLM server over 4 GPUs needs them on one node, and `-G 4` alone lets
     Slurm spread them. The kit's account test now requires `-N 1` of any job with more than one GPU.
   - In `submit.sh`'s QoS check:
     - **A job without a GPU counts 0.** Before, it counted as 1 GPU.
     - **A job that asks for GPUs per job** (`-G`, as every script here does) may show `N/A` in squeue's `%b`. Its
       GPUs now come from `scontrol show job`'s `ReqTRES` (`gres/gpu=N`), so a 4-GPU job counts 4.
     - **The 960 GPU-minutes count running jobs only,** as Slurm counts them. Pending jobs are listed, not added. Adding
       them would have printed a false "over the limit" warning for every wave of 1-GPU parts.
     - The "both slots are taken" line says how many are held by jobs without a GPU.
   - **One download at a time:** a `get_*` job while another download is running or pending is refused, unless it
     waits for it (`--dependency=afterany:N`). The refusal prints that line. Downloads may now wait for each other.
   - **`--htc`** (item 2):
     - the job may start on `public` or `htc` (`-p public,htc`);
     - only with a limit of 4 h or less, and an htc row in `accounts.conf`;
     - `sbatch --test-only` must accept the same request first, or nothing is submitted (it prints the test's
       answer).
   - **`accounts.conf`** lists the htc row (4 h). Whether the class QoS may use it is unconfirmed until Ritik's check;
     `--htc` re-checks it on every submission.
   - **Tests** (`tests/test_trackA_gpu_kit.py`):
     - 4 new: GPUs from ReqTRES; one download at a time; `--htc` with `--test-only`; and pending jobs not added, which
       replaces the old test that counted them;
     - 2 changed: the account rows; `-N 1`.
3. **A18 read by its rule:** the reading has its own log (15:09). See §5.
4. **B20's operational note** (its log's §13, 15:13, before any B20 run):
   - the order of the smokes, and the runs' limit (estimate 3 h, limit 4:00);
   - the downloads;
   - its §12 ruling 4 is stale: Gemma is served with its snapshot's own template (§4, the code).
5. **The docs:** PLAN (Sol order, A18, map, calendar, Gate 3, slide 10), RUNBOOK §0, TODO (A18, A39, B1R2, R3, D14),
   TODO_B (B20), FINDINGS (F39, the story), README, TRACK_A, OUTLINE, WAITING.

## 2. A39 on E2: the lines (item 1)

**The parts:**
- **Core systems:** 4 parts each (`k/4`), 360 runs and about 2.1 GPU-hours a part plus the server's start. `--estimate
  2.3` gives a 3:00 limit.
- **Wrapper systems:** 2 parts each (`k/2`), 240 runs and about 1.4 GPU-hours. `--estimate 1.6` gives a 2:30 limit.
- **All A39 parts, about 46 GPU-hours.** Throughput is 500 tokens/s per A100 at 48 in flight (batch 3); the bench
  replaces this.
- **Runs resume by run id across part files.** A part that runs out of time is submitted again with the same line and
  does only what's left. The bench's 96 runs are in base's parts 2/4 and 4/4 (48 each), which skip them. So base's
  1/4 and 3/4 go first, sharing no run with the bench.

**The rule for submitting:**
- At most 10 jobs may be submitted (running and pending, downloads included). Now: 389340 and the three downloads, so
  6 more fit; lines 7–9 go in as the downloads end. After that, **when a job ends, submit the next line.**
- `submit.sh` refuses an 11th job and says so.
- After each wave: `squeue --start -u $USER` for the times.

```bash
cd /scratch/ragarw68/cse598-cot-faithfulness && git pull --ff-only
S=cot-disclosure/finetune/gpu/sol/submit.sh
H=--htc     # only if the htc check (§3) printed "to start at"; otherwise:  H=

# Wave 1, now (lines 1-6; lines 7-9 as the downloads end): the core systems, round-robin
$S a39_1gpu $H --estimate 2.3 -- base e2 1/4            # 1
$S a39_1gpu $H --estimate 2.3 -- prompt_only e2 1/4     # 2
$S a39_1gpu $H --estimate 2.3 -- lora e2 1/4            # 3
$S a39_1gpu $H --estimate 2.3 -- lora_note e2 1/4       # 4
$S a39_1gpu $H --estimate 2.3 -- base e2 3/4            # 5
$S a39_1gpu $H --estimate 2.3 -- prompt_only e2 2/4     # 6
$S a39_1gpu $H --estimate 2.3 -- lora e2 2/4            # 7
$S a39_1gpu $H --estimate 2.3 -- lora_note e2 2/4       # 8
$S a39_1gpu $H --estimate 2.3 -- base e2 2/4            # 9  (skips the bench's 48)

# Wave 2, one line per job that ends: B20's three smokes (item 5), then the core systems' last parts
$S b20 $H --model granite-4.2-8b -- --smoke             # 10 (estimate 1 h, limit 1:30)
$S b20 $H --model gemma-4-26b-a4b-it -- --smoke         # 11
$S b20 $H --model nemotron-3-nano-30b-a3b -- --smoke    # 12
$S a39_1gpu $H --estimate 2.3 -- prompt_only e2 3/4     # 13
$S a39_1gpu $H --estimate 2.3 -- lora e2 3/4            # 14
$S a39_1gpu $H --estimate 2.3 -- lora_note e2 3/4       # 15
$S a39_1gpu $H --estimate 2.3 -- base e2 4/4            # 16 (skips the bench's 48)
$S a39_1gpu $H --estimate 2.3 -- prompt_only e2 4/4     # 17
$S a39_1gpu $H --estimate 2.3 -- lora e2 4/4            # 18
$S a39_1gpu $H --estimate 2.3 -- lora_note e2 4/4       # 19

# Wave 3: the wrapper systems (4 runs a question each), then B20's runs, each after its clean smoke
$S a39_1gpu $H --estimate 1.6 -- wrap e2 1/2            # 20
$S a39_1gpu $H --estimate 1.6 -- wrap_note e2 1/2       # 21
$S a39_1gpu $H --estimate 1.6 -- lora_wrap e2 1/2       # 22
$S a39_1gpu $H --estimate 1.6 -- wrap e2 2/2            # 23
$S a39_1gpu $H --estimate 1.6 -- wrap_note e2 2/2       # 24
$S a39_1gpu $H --estimate 1.6 -- lora_wrap e2 2/2       # 25
$S b20 $H --model granite-4.2-8b --estimate 3 --dependency=afterok:<line 10's job>            # 26 (limit 4:00)
$S b20 $H --model gemma-4-26b-a4b-it --estimate 3 --dependency=afterok:<line 11's job>        # 27
$S b20 $H --model nemotron-3-nano-30b-a3b --estimate 3 --dependency=afterok:<line 12's job>   # 28

# Wave 4: A39 on the 30 (item 4), one 1-GPU job a system
$S a39_1gpu $H --estimate 2.5 -- base mmlupro_30        # 29 (limit 3:30)
$S a39_1gpu $H --estimate 2.5 -- prompt_only mmlupro_30
$S a39_1gpu $H --estimate 2.5 -- lora mmlupro_30
$S a39_1gpu $H --estimate 2.5 -- lora_note mmlupro_30
$S a39_1gpu $H --estimate 1 -- wrap mmlupro_30          # limit 1:30
$S a39_1gpu $H --estimate 1 -- wrap_note mmlupro_30
$S a39_1gpu $H --estimate 1 -- lora_wrap mmlupro_30     # 35
```

**Details for some lines:**
- **A smoke whose job has ended** can't be named in `--dependency`. Submit that model's runs without it, but only
  after reading its `smoke_check.json` (clean = exit 0).
- **A B20 run job that leaves runs:** its line again, with `--dependency=afterany:<that job>`.
- **A job stopped at its limit** (Slurm's warning, then "stopped by a signal"): the same line again.
- **What the bench gives:** its console log's `generated tokens/s` and the job's elapsed time (`sacct -j 389340 -o
  Elapsed`). If a part's real time comes out well under 2.1 hours, nothing changes: the limits only cap. If it is over
  2.3 hours, parts stop at their limit and resume when submitted again.

## 3. htc (item 2)

The check, on the login node; nothing is submitted:

```bash
scontrol show partition htc | grep -oE '(AllowQos|AllowAccounts|DenyQos|MaxTime|TotalNodes)=[^ ]*'
sbatch --test-only -A class_cse59888883fall2026 -p htc -q class -G a100:1 -c 8 --mem=96G -t 3:00:00 --wrap true
```

- **`sbatch: Job N to start at ... in partition htc`:** the class QoS may use htc. Set `H=--htc` in the lines above.
  - `submit.sh --htc` sends `-p public,htc`, so each job starts on whichever partition has a gap first.
  - It runs the same `--test-only` before every such submission.
  - Every line above fits htc's 4 hours (3:00, 2:30, 1:30, 4:00 and 3:30 limits).
- **An error** ("Invalid qos specification", "not permitted to use this partition", or `AllowQos` not listing
  `class`): leave `H=` empty. Tell me, and I'll take the htc row out of `accounts.conf`.

## 4. The 30, B20, downloads, B1R2 (items 3–6)

**Downloads (item 3).**
- **None is left to submit:** all three of B20's are running.
- **A job without a GPU still takes one of the two running slots** (Ritik's finding). So a download is best submitted
  when one GPU job is running and the next GPU job's `squeue --start` is over an hour away, so that it uses a slot that
  would sit idle.
- **Never two at once:** `submit.sh` refuses a second unless it waits for the first.
- **A check:** with MaxJobsPU 2 (`accounts.conf`, confirmed Oct 27), three downloads can't all be running at once.
  `squeue -u $USER -t R` shows whether one is pending. If three really run, the QoS's limit changed. Then
  `sacctmgr -P show qos class format=MaxJobsPU,MaxSubmitPU,MaxTRESRunMinsPU` shows the new value, and the plan can use
  more slots.

**The 30 (item 4): kept.** The rule is the A39 log's §10, from compute only:
- E2 needs about 46 GPU-hours, B20 5–16 and the 30 about 12.
- The two slots give at most 48 GPU-hours a day. From now to Nov 12 is 8.3 days, so the 30 misses Nov 12 only if the
  slots deliver under about 9 GPU-hours a day.
- It is wave 4, after E2 and B20. It is dropped, and recorded "not run: no GPU time by Nov 12", if E2's and B20's jobs
  haven't all finished by Nov 11 09:00.

**B20 (item 5).**
- **The smokes** are wave 2's first three lines, smallest first: Granite (17.6 GB), Gemma (51.6), Nemotron (63.2).
- **The parser grep** (the B20 log's line 0) searches vLLM's `reasoning/` folder for the three reasoning parsers' names:
  - **`gemma4`, Gemma's parser:** a hit means our vLLM 0.31.0 ships it. No hit means `--reasoning-parser gemma4`
    doesn't exist, and Gemma's server won't start. Its smoke would stop before any run, and nothing counts. The way on
    would be an amendment (another parser, or drop Gemma). Its tool-call parser `gemma4` lives elsewhere and is already
    in the committed option list.
  - **`nemotron_v3`, Nemotron's parser:** the same meaning. Its tool parser `qwen3_coder` is in the option list. Its
    model code comes from the pinned snapshot (`--trust-remote-code`).
  - **`granite_thinking_parser`, Granite's parser:** **no hit is expected and fine.**
    - The parser isn't part of vLLM 0.31.0 (released Oct 5). Granite 4.2's card says native support is coming.
    - It ships as `granite_thinking_parser.py` in Granite's own snapshot. Our server loads it with
      `--reasoning-parser-plugin SNAPSHOT/granite_thinking_parser.py`, the card's own command.
    - A hit would mean vLLM has it natively too. Then the plugin registers the same name from IBM's file, which is
      harmless.
    - What decides Granite is three things:
      1. **The file is in the download.** Check with
         `ls /scratch/ragarw68/hf/hub/models--ibm-granite--granite-4.2-8b/snapshots/a7042144*/granite_thinking_parser.py`
         after 388229 ends; the download also lists it in its `snapshot.json`.
      2. **vLLM accepts `--reasoning-parser-plugin`.** It's in the committed option list, and the smoke's first step
         checks it on the node.
      3. **The plugin's code imports against 0.31.0's parser interface.** Only the server's start shows this. If it
         fails, the Granite smoke stops before any run and the fix is an amendment. Its reasoning split is then
         checked by the smoke itself.
- **B20's runs:** `--estimate 3` (limit 4:00) a model, and again if runs are left. The dry run is 0.9–4.4 GPU-hours a
  model.

**B1R2 (item 6): decided Nov 8 at 09:00** by the A39 log's §10, from compute only:
- **needed:** A39's, B20's and the 30's remaining runs at their dry run's GPU-hours, plus B1R2's 60 GPU-hours × 1.1;
- **left:** the GPU-hours delivered Nov 4–7 per day, times the days to Nov 15 23:59;
- B1R2 runs if needed ≤ left. Otherwise F38 gets **"not run: no GPU time by Nov 15"**.
- The delivered GPU-hours, on Sol (`-T` cuts each job to the window):

```bash
sacct -u ragarw68 -X -T -S 2026-11-04T00:00 -E 2026-11-08T00:00 -P -n -o ElapsedRaw,AllocTRES \
  | awk -F'|' '{ g = 0; if (match($2, /gres\/gpu=[0-9]+/)) g = substr($2, RSTART + 9, RLENGTH - 9); s += $1 * g }
               END { printf "%.1f GPU-hours delivered, %.1f a day\n", s / 3600, s / 3600 / 4 }'
```

## 5. A18 (item 7)

**The reading** is in its own log, `2026-11-03_1509_A_a18-reading.md`, as A18's pre-registration asked.
- **Primary: "acts in the reasoning."**
  - Given base's own reasoning, LoRA's weights don't reduce the hint's direct pull on the answer: R_LoRA −0.72 logits
    [−1.02, −0.39], over 28 cases and 13 questions. They add to it, by about a quarter.
  - Under LoRA's weights, the forced answer at base's cut is still the hint's letter in 30 of 30.
- **Secondary a (set A's rule): replicates.** When LoRA does follow, the drop runs through 15, 19 and 23.
- **Secondary b (F32's rule): replicates** in both systems. F12's heads still separate followed from resisted runs.
- **In plain words:** training didn't cut the readout or discount the tool's letter after it. What changed is the
  reasoning LoRA writes before the answer.
- **What it changes:**
  - **The story:** the fix acts through the text, not on the readout. This fits F28, where no trained version beats a
    one-line instruction.
  - **The docs:** F39; FINDINGS' story item 5 and README's item 5; PLAN (map, story, Gate 3 and slide 10); TRACK_A;
    OUTLINE.
- **Slide 10:** `docs/paper/figures/readout_lora_vs_base.png`.
  - (a) R for LoRA, beside each layer swap's R, marked "reported, not read". The extra pull comes with LoRA's layers
    24–31.
  - (b) B1's two spans.
  - The figure departs from WAITING's spec on one point, said in WAITING: the rule's shares are undefined when R_LoRA
    is below 0, so the swaps show R instead.

## 6. Judgment calls

1. **The GPU-minute check counts running jobs only.** Ritik asked only that jobs without a GPU count 0, but adding
   pending jobs made every wave of 1-GPU parts print a false "over the limit" warning. Slurm counts a job only once it
   runs.
   - Cost if wrong: none for submission (it was only ever a warning); a wave could start later than the message says.
2. **The 4-GPU kind stays** (`a39`, now `-N 1`), unused in this plan.
   - Cost: none.
3. **`--htc` asks for `public,htc` in one job,** with `sbatch --test-only` before each submission. The htc row went
   into `accounts.conf` before Ritik's check, safe because `--htc` is opt-in and re-checked every time.
   - Cost if htc isn't allowed: a refused `--htc` line, and the row comes out.
4. **Base's parts 1/4 and 3/4 go first,** so no part runs the bench's runs twice.
   - Cost: none.
5. **Round-robin over the core systems,** so a cut-short E2 leaves each core system the same share of every question.
   - Cost: none; every part covers every question.
6. **All three B20 smokes go at the head of wave 2,** smallest first, before the core systems' last 7 parts.
   - Why: a smoke failing late is the costliest surprise.
   - Cost: about 3 GPU-hours before the core finishes.
7. **B20's runs at `--estimate 3`** (limit 4:00), not the default 6 (8:00).
   - Why: to fit htc and the gaps.
   - Cost: a second job for a model whose runs take over about 3.5 hours.
8. **The 30 is kept** by a break-even rate, not a guessed one. Ritik asked that times come from `squeue --start`.
   - Cost if wrong: it is dropped on Nov 11 by the rule.
9. **A18's swaps are shown as R, not the rule's shares,** which are undefined here. They are marked "reported, not
   read", in the reading's log, F39 and the slide.
   - Cost: none; nothing is read from them.
10. **The B20 log's stale ruling 4 is noted in its §13,** not edited, because the log is a committed
    pre-registration.
    - Cost: none.

## 7. What waits for Ritik

- On Sol:
  - `git pull --ff-only`;
  - the htc check (§3);
  - wave 1, lines 1–6 now and 7–9 as the downloads end;
  - then one line per finished job, in order;
  - `squeue --start -u $USER` after each wave.
- **Granite's plugin file:** after 388229 ends, the `ls` in §4.
- **Tell me:**
  - the htc check's answer;
  - the bench's throughput and elapsed time (`sacct -j 389340 -o Elapsed,State`, and the console log's last
    `generated tokens/s` line);
  - any smoke that isn't clean.
- **Nov 8, 09:00:** the `sacct` line in §4, for B1R2's decision.
- **Nov 11, 09:00:** whether E2 and B20 are done (the 30's rule).
- **Still open from the morning:** the L3 settling call with Shrey; Shrey's message and bundle; Arsha's bundle on Nov
  6.

## 8. Checks

- The Sol-kit tests (`test_trackA_gpu_kit.py`, B20's, the second user's, A18's, the provenance jobs', Qwen3-8B's,
  A39's): 221 passed, 1 skipped.
- The slide tests: 9 passed. The full suite and the pre-push check: see the commit.
