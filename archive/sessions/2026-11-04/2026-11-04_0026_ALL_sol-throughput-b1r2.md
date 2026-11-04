# Session log: Sol's real limit (960 running GPU-minutes, not 2 jobs), the re-plan for throughput, B1R2 decided early (2026-11-04 00:26 MST)

By: Ritik. Ritik's message of about 00:20, five items, with `squeue` from Sol (Nov 3, late evening).

**What Ritik saw on Sol:** 7 of Ritik's jobs RUNNING at once, not 2. `submit.sh` printed "running 7 (913 GPU-minutes left),
pending 2 ... total 1003 of 960" and "both slots are taken". The two pending A39 parts (428330, 428332) show
`(MaxGRESRunMinsPerUser)`. So what binds is the 960 running GPU-minutes, not MaxJobsPU 2. B20's Granite smoke is
submitted: 456999 (Priority).

**The safety rule for Sol, kept throughout:** the two pending A39 parts and the pending smoke load code from Sol's
clone when they start. Nothing they load changes (the list in §5).

## Plans for the structural changes (written before each)

- **`submit.sh`'s message:** the "both slots are taken" line goes. In its place, one line names what limits a job: the
  GPU-minutes free now (960 minus the running jobs' time left × GPUs) and the places left in the 10 submitted. The
  download rule stays (one download at a time), reworded without slots. `accounts.conf`'s `max_jobs` column becomes 10
  (what binds is the 10 submitted), with its comment; the column stays, so a second user's file keeps its format.
  Tests first.
- **B1R2's code:** one option on B1's generation job (`provenance_job.py generate --b1r2`): E2's questions, the
  inserted tool turn only, 2 wrong + 2 correct + 1 no-hint run a question, alpha = 1 and the deployable span only,
  written to its own folder (`$TRACKA_OUT/b1r2`), so it can't mix with B1's runs on the 30. Every existing path keeps
  its defaults. No A39 or B20 job imports this module (they run vLLM: `run.sh` gives A39 `--engine vllm`), and a test
  pins that. Tests first.
- **Job shapes:** written in the A39 log (§12, operational) and the B20 log (§14, operational) before any of the new
  shapes is submitted. B1R2's decision and job lines are the A39 log's §13, an amendment, committed before any B1R2
  run.
- **No folder moves; nothing deleted.**

## 1. What binds on Sol (item 1)

- **The evidence (Ritik's `squeue`, Nov 3 late evening):**
  - 7 one-GPU A39 parts were RUNNING at once (426582, 428294 at 1:15; 428295–428297 at 1:05; 428298 and 428299 just
    started);
  - 428330 and 428332 were pending on `MaxGRESRunMinsPerUser`;
  - B20's Granite smoke 456999 was pending on `Priority`.
- **So the class QoS's MaxJobsPU 2 doesn't bind.** It is still in the Oct 27 listing; a re-check with `sacctmgr` would
  say whether it changed.
- **What binds is two things:**
  - the 960 running GPU-minutes: each running job's time left × its GPUs, so the full limit for a job just started;
  - the 10 submitted jobs (running and pending).
- **Fixed everywhere it was stated:**
  - `accounts.conf`: the comment, and `max_jobs` 2 → 10, which is what binds. The column stays, so a second user's
    file keeps its format. `guard.sh` reads only the account names, which are unchanged.
  - `submit.sh`: its header; the message (below); the download refusal, reworded without slots (still one download
    at a time).
  - `SOL_SETUP` (the setup line, the limits table, the CPU allocation's place), RUNBOOK §0 and the `submit.sh` note,
    PLAN (the Sol order, the risks), the GPU README (the QoS table and checks), `plan_eval.py`'s docstring.
  - Old session logs keep what they said then.
- **`submit.sh`'s message now,** on Ritik's queue (the test's numbers; Ritik's own run showed 913 minutes a little
  earlier):
  ```
  QoS check: this job 1:30:00 x 1 GPU = 90 GPU-minutes; running 7 (901 GPU-minutes left), pending 2 (360 requested, counted once they run); total 991 of 960
  limits: 59 of 960 GPU-minutes free now (this job needs 90); 0 of 10 places left after this one (7 running, 2 pending)
  WARNING: over the 960 GPU-minute limit by 31: the job waits about 5 min, until the running jobs have used that much of their time (or longer: a pending job that fits may start first)
  ```
- **Tests,** all failing first:
  - new: `test_seven_running_jobs_the_limit_is_gpu_minutes_and_places_not_two_slots`;
  - changed: `test_running_jobs_count_their_gpus_and_pending_ones_are_listed`,
    `test_a_second_download_waits_for_the_first` and `test_only_listed_accounts`.

## 2. The re-plan for throughput (item 2)

**The arithmetic.**
- A job holds its whole limit in GPU-minutes when it starts, and the hold falls as it runs. So:
  - at a 1:30 limit, 10 one-GPU jobs fit at once (900 of 960);
  - at 3:00, only 5 fit fresh, and about 7–8 once their ages are spread out (tonight's 7).
- A job's size here is generation at the bench's 400 tokens/s, plus about 10 minutes of start (imports, the vLLM
  start) and about 10 minutes for its last runs, when fewer are in flight.
- A 1:30 job stops at 1:25 (Slurm's warning), so it fits about an hour of generation.

**The units** (each checked on the job lists; `--estimate 1` gives 1:30):

| work | unit | runs | generation (GPU-h) | jobs | limit |
|---|---|---|---|---|---|
| E2, core systems: the 7 quarters not submitted (prompt_only, LoRA, LoRA + note 3/4 and 4/4; base 4/4) | sixteenths: quarter k/4 = sixteenths k, k+4, k+8, k+12, exactly | 90 | 0.64–0.69 | 28 | 1:30 |
| E2, wrapper systems | fifths (`k/5`; each mixes wrong- and correct-hint runs) | 96 | 0.70 | 15 | 1:30 |
| E2, leftovers of the 3:00 parts and any unit cut short | a sweep per system (no part) after all its parts end | what's left | — | 4+ | 1:30 |
| B20's smokes | as before | 12 | — | 2 more | 1:30 |
| B20's runs | one job a model at a time, resumed (`--estimate 1.1`); again while runs are left | ~1 h of runs a job | 0.9–4.4 a model | 3–15 | 1:30 |
| the 30, core systems | quarters (`k/4`) | 90 | 0.64–0.69 | 16 | 1:30 |
| the 30, wrapper systems | halves (`k/2`) | 60 | 0.44 | 6 | 1:30 |
| B1R2 | 3 questions (`--part k/40`) | 30 | 1.3–1.7 + 0.15 load | 40 + 4 sweeps | 2:30 |

- **Why sixteenths and fifths.**
  - Twelfths would each hold one wording of every question. The wrong-hint ones run long (1.02 GPU-hours, about 81
    minutes with the start), close to the 1:25 stop.
  - Sixteenths and fifths mix kinds, so every unit is about the same size, well inside 1:30.
  - The sixteenths nest exactly in the quarters already named, so no run is done twice. Resume reads every part file
    of a system.
- **B1R2's units.**
  - B1's engine batches up to 8 rows at a time, one configuration at a time.
  - 3 questions give 15 runs a configuration, two near-full batches. 2 questions would leave a batch of 2 that costs
    nearly a full batch's time, so a 1:30 limit isn't safe.
  - So 2:30, 6 at once.
- **The 9 queued parts stay as they are.** The 2 pending ones each hold one place, as their sixteenths would; cancelling
  and resplitting gains little.
- **Nights.**
  - With the queue full, places, not GPU-minutes, cap what runs unattended: 10 places × 1:30 is about 10 GPU-hours
    of work.
  - Before a night away, fill places with the longer shapes, which cover the same runs:
    - a core quarter's own line (`k/4`, `--estimate 2.6`, 3:30) for its four sixteenths, if none has been submitted;
    - B1R2's `k/20` (`--estimate 3`, 4:00) for parts k and k+20 of 40;
    - B20's runs at `--estimate 3` (4:00).
- **Written before any of these shapes ran:** the A39 log's §12 and the B20 log's §14 (operational), and §13 for
  B1R2, committed `21e0386` at 00:49.

## 3. B1R2 (item 3): it clearly fits, so it's decided now

- **Needed** to Nov 15 23:59, in GPU-hours of job time with starts: about 181 (the A39 log's §13.2). That is:
  - A39's E2, about 70;
  - B20, at most 24;
  - the 30, about 21;
  - B1R2, 66 (its rule's 60 × 1.1).
- **What that asks of Sol:** 0.63 of one A100 around the clock (15 GPU-hours a day). The 7 jobs running at once
  deliver that in about 2 hours, and the cap allows 10 at once.
- **The amendment** (the A39 log's §13, `21e0386`, before any B1R2 run; nothing of E2 read):
  - the decision moves from Nov 8 09:00 to now: **it runs**;
  - the design is §5's, unchanged;
  - B1R2 runs last;
  - it is read partial ("partial: N of 120 questions") if it isn't done by Nov 15 23:59.
- **The code:** `provenance_job.py generate --b1r2`.
  - **The runs:** E2's 120 questions, the inserted tool turn, 2 wrong + 2 correct + 1 no-hint run a question.
  - **The configurations:** `prov-a1-v2` and `prov-deployable-a0.25-v2` only.
  - **The engine:** B1's engine and settings unchanged.
  - **Where:** `$TRACKA_OUT/b1r2/`, so its runs never mix with B1's on the 30.
  - **What it refuses:** `--note`, `--version`, `--alphas`, and a summary whose deployable alpha is 1.
  - **Every default path is unchanged:** B1's 210 jobs on the 30 are identical, and a test says so.
- **Tests** (`tests/test_b1r2.py`, 6; 5 failing first):
  - the jobs;
  - B1's defaults unchanged;
  - the configurations;
  - generation into its own folder on the tiny model;
  - the CLI's dry run;
  - and that no vLLM job imports `provenance_job` or `hf_engine`. That one passed from the start, since it pins
    today's behavior: run.sh gives A39 `--engine vllm`, so only the Hugging Face path reaches B1's module.
- **The dry run,** with B1's own `provenance_forced.json` (deployable alpha 0.25):
  - all of E2: 600 runs × 2 configurations = 1,200 runs, about 12.4 M tokens, 52.8–68.7 GPU-hours;
  - one part (`1/40`): 15 × 2 = 30 runs, 1.3–1.7.
- **Its lines:** RUNBOOK §14, the GPU README's job table, and `provenance_gen.sbatch`'s comment. They need a pull on
  Sol first (§5).

## 4. The calendar to Nov 15, and the next lines (item 4)

**Projected,** from a simple schedule of the work above under the 960 cap and the 10 places:
- Ritik submits whenever places free, between 08:00 and midnight, every 30–60 minutes.
- Times are from Ritik's `squeue` at about 00:20.
- These are projections, not start times: after each wave, `squeue --start -u $USER` gives the real ones.

| GPUs Sol gives at once | 9 queued parts end | E2 core | wrappers | B20 | the 30 | B1R2 |
|---|---|---|---|---|---|---|
| 10 (Nov 3 night) | Nov 4 ~04:00 | Nov 4 midday | Nov 4 afternoon | Nov 4 evening | Nov 4 evening | Nov 5 morning |
| at most 5 | Nov 4 ~05:00 | Nov 4 afternoon | Nov 4 evening | Nov 4 evening | Nov 4 late | Nov 5 evening |
| at most 3 | Nov 4 ~06:00 | Nov 4 evening | Nov 4 late | Nov 5 early | Nov 5 afternoon | Nov 6 afternoon |

**In PLAN's calendar,** with a day's margin for Sol's busy spells (on Nov 3 afternoon nothing started for hours):
- **Nov 4:** the 9 parts end. As places free: B20, E2's 28 sixteenths and 15 fifths.
- **Nov 5–7:** the sweeps; E2 and B20 done (projected Nov 5–6); the 30; B1R2 (projected done Nov 6–8).
- **Nov 8–12:** room for reruns. The 30's rule on Nov 11 09:00 has no effect if E2 and B20 are done.
- **The rest is unchanged:**
  - runs end Nov 15;
  - A39, B20 and B1R2 are read Nov 17 (earlier is possible, not planned);
  - the freeze is Nov 18.

**The next lines, in order, as places free** (the queue is full now: 7 running, 2 A39 parts pending, the smoke
pending). From the Sol clone, `S=cot-disclosure/finetune/gpu/sol/submit.sh`. No `--htc`. Submit one line per free place.
Keep each job id: sweeps and B20's runs name them.

```bash
# B20 (its log, §13-§14): the other two smokes, then each model's runs after its clean smoke
$S b20 --model gemma-4-26b-a4b-it -- --smoke                                     # 1
$S b20 --model nemotron-3-nano-30b-a3b -- --smoke                                # 2
$S b20 --model granite-4.2-8b --estimate 1.1 --dependency=afterok:456999          # 3
$S b20 --model gemma-4-26b-a4b-it --estimate 1.1 --dependency=afterok:<job 1>     # 4
$S b20 --model nemotron-3-nano-30b-a3b --estimate 1.1 --dependency=afterok:<job 2> # 5
#   then each model's same line again (no --dependency, or afterany on its last job) while its log says runs are left
# E2, the core systems' sixteenths, round-robin (the A39 log's section 12; all --estimate 1, limit 1:30)
$S a39_1gpu --estimate 1 -- prompt_only e2 3/16                                  # 6
$S a39_1gpu --estimate 1 -- lora e2 3/16                                         # 7
$S a39_1gpu --estimate 1 -- lora_note e2 3/16                                    # 8
$S a39_1gpu --estimate 1 -- base e2 4/16                                         # 9
$S a39_1gpu --estimate 1 -- prompt_only e2 4/16                                  # 10
$S a39_1gpu --estimate 1 -- lora e2 4/16                                         # 11
$S a39_1gpu --estimate 1 -- lora_note e2 4/16                                    # 12
$S a39_1gpu --estimate 1 -- prompt_only e2 7/16                                  # 13
$S a39_1gpu --estimate 1 -- lora e2 7/16                                         # 14
$S a39_1gpu --estimate 1 -- lora_note e2 7/16                                    # 15
$S a39_1gpu --estimate 1 -- base e2 8/16                                         # 16
$S a39_1gpu --estimate 1 -- prompt_only e2 8/16                                  # 17
$S a39_1gpu --estimate 1 -- lora e2 8/16                                         # 18
$S a39_1gpu --estimate 1 -- lora_note e2 8/16                                    # 19
$S a39_1gpu --estimate 1 -- prompt_only e2 11/16                                 # 20
$S a39_1gpu --estimate 1 -- lora e2 11/16                                        # 21
$S a39_1gpu --estimate 1 -- lora_note e2 11/16                                   # 22
$S a39_1gpu --estimate 1 -- base e2 12/16                                        # 23
$S a39_1gpu --estimate 1 -- prompt_only e2 12/16                                 # 24
$S a39_1gpu --estimate 1 -- lora e2 12/16                                        # 25
$S a39_1gpu --estimate 1 -- lora_note e2 12/16                                   # 26
$S a39_1gpu --estimate 1 -- prompt_only e2 15/16                                 # 27
$S a39_1gpu --estimate 1 -- lora e2 15/16                                        # 28
$S a39_1gpu --estimate 1 -- lora_note e2 15/16                                   # 29
$S a39_1gpu --estimate 1 -- base e2 16/16                                        # 30
$S a39_1gpu --estimate 1 -- prompt_only e2 16/16                                 # 31
$S a39_1gpu --estimate 1 -- lora e2 16/16                                        # 32
$S a39_1gpu --estimate 1 -- lora_note e2 16/16                                   # 33
# E2, the wrapper systems' fifths, round-robin
$S a39_1gpu --estimate 1 -- wrap e2 1/5                                          # 34
$S a39_1gpu --estimate 1 -- wrap_note e2 1/5                                     # 35
$S a39_1gpu --estimate 1 -- lora_wrap e2 1/5                                     # 36
$S a39_1gpu --estimate 1 -- wrap e2 2/5                                          # 37
$S a39_1gpu --estimate 1 -- wrap_note e2 2/5                                     # 38
$S a39_1gpu --estimate 1 -- lora_wrap e2 2/5                                     # 39
$S a39_1gpu --estimate 1 -- wrap e2 3/5                                          # 40
$S a39_1gpu --estimate 1 -- wrap_note e2 3/5                                     # 41
$S a39_1gpu --estimate 1 -- lora_wrap e2 3/5                                     # 42
$S a39_1gpu --estimate 1 -- wrap e2 4/5                                          # 43
$S a39_1gpu --estimate 1 -- wrap_note e2 4/5                                     # 44
$S a39_1gpu --estimate 1 -- lora_wrap e2 4/5                                     # 45
$S a39_1gpu --estimate 1 -- wrap e2 5/5                                          # 46
$S a39_1gpu --estimate 1 -- wrap_note e2 5/5                                     # 47
$S a39_1gpu --estimate 1 -- lora_wrap e2 5/5                                     # 48
# a sweep per core system, once none of its parts is running or pending (only what's left; again if runs are left)
$S a39_1gpu --estimate 1 -- base e2              # 49: after 426582, 428297, 428332 and lines 9, 16, 23, 30
$S a39_1gpu --estimate 1 -- prompt_only e2       # 50: after 428294, 428298 and lines 6, 10, 13, 17, 20, 24, 27, 31
$S a39_1gpu --estimate 1 -- lora e2              # 51: after 428295, 428299 and lines 7, 11, 14, 18, 21, 25, 28, 32
$S a39_1gpu --estimate 1 -- lora_note e2         # 52: after 428296, 428330 and lines 8, 12, 15, 19, 22, 26, 29, 33
#   a wrapper system's sweep (-- wrap e2, ...) only if one of its fifths stopped short
# the 30 (the A39 log's section 10.2: unless E2 and B20 miss Nov 11 09:00), round-robin
#   53-68: for k in 1 2 3 4, for s in base prompt_only lora lora_note:  $S a39_1gpu --estimate 1 -- $s mmlupro_30 $k/4
#   69-74: for k in 1 2, for s in wrap wrap_note lora_wrap:            $S a39_1gpu --estimate 1 -- $s mmlupro_30 $k/2
# B1R2 (the A39 log's section 13), last; after a pull on Sol (the --b1r2 option is new)
#   75-114: for k in 1 .. 40:
#   $S provenance_gen --estimate 1.6 -- --alpha-from /scratch/$USER/trackA/provenance_forced/provenance_forced.json --b1r2 --part $k/40
#   115-118: after all 40 end, the same line with --part 1/4 .. 4/4 (only what's left)
```

- **A dependency on a job that has already ended can't be named:** drop it. `submit.sh` accepts only running or
  pending jobs.
- **If you fill places before a night away,** use the night shapes (§2): for example
  `$S a39_1gpu --estimate 2.6 -- prompt_only e2 3/4` in place of lines 6, 13, 20 and 27, if none of them has been
  submitted.
- **When places free:** 426582 and 428294 end within about 1:45 of the pasted `squeue`; 428295–428297 within 1:55;
  428298 and 428299 within about 2:55. The 2 pending parts start as GPU-minutes free up.

## 5. Is a pull on Sol safe now? Yes

Changed since the last push (`d4ae9ab`), outside tests and docs:
- `accounts.conf`: comments, and the `max_jobs` column 2 → 10.
  - A job's account check (`guard.sh`) reads only the first column of lines that aren't comments, the account
    names. They are unchanged.
  - `submit.sh` reads the rest.
- `submit.sh`: run by Ritik on the login node; no job loads it.
- `provenance_job.py`: the `--b1r2` option, whose defaults leave every existing path as it was.
  - It is one of the two files on last night's list of 49 that change (`accounts.conf` is the other). It was on the
    list only because `hf_engine.py` imports it lazily, for the Hugging Face engine's fallback.
  - This module is reached only through the Hugging Face engine: `eval_job.py --engine hf`, and B1's own jobs.
  - A39's jobs run `--engine vllm` (`run.sh`), and B20's job serves vLLM.
  - `test_no_vllm_job_imports_b1s_generation_module` imports every module those jobs load, and the lazy imports on
    their path. Neither `provenance_job` nor `hf_engine` gets loaded.
  - The jobs' import check (`import_check.py`) imports only torch, transformers, tokenizers, peft and vllm.
- `provenance_gen.sbatch`: a comment. No B1 job is queued, and Slurm keeps a copy of each script as submitted.
- `plan_eval.py`: a docstring. No job imports it.
- `make_supplement.py`: Mac only.

So nothing the 2 pending A39 parts (428330, 428332), the pending smoke (456999) or the running parts load has changed.
- **Before pulling:** `git rev-parse --short HEAD` on Sol (`d4ae9ab` or `14105b7`), then
  `git diff --stat HEAD..origin/main -- cot-disclosure/finetune/gpu/sol/run.sh cot-disclosure/finetune/gpu/sol/env.sh cot-disclosure/finetune/gpu/sol/guard.sh cot-disclosure/finetune/eval.py cot-disclosure/finetune/gpu/eval_job.py cot-disclosure/finetune/gpu/vllm_options.py cot-disclosure/progress/sol_b20.py cot-disclosure/progress/run_b20.py`
  should print nothing.
- **Wave 2's A39 and B20 lines need no pull.** `eval.py` already takes any `k/n`, and `submit.sh`'s new message is
  only text. B1R2's lines need one, for `--b1r2`.

## 6. Judgment calls (each with its cost if wrong)

1. **`max_jobs` is 10, not removed.** Seven ran at once and the pending ones waited on GPU-minutes. A cap between 7 and
   10 can't be ruled out until `sacctmgr` is re-read.
   - Cost: if one exists, a job waits with no message saying why. `squeue`'s reason would show it.
2. **Sixteenths and fifths, not twelfths and quarters.** Every unit mixes kinds and fits 1:30 with room.
   - Cost: more job starts, about 10 minutes each. 43 E2 jobs instead of about 33 is under 2 GPU-hours more.
3. **The 9 queued parts kept,** with a sweep per system after them.
   - Cost: if the 3:00 parts stop short, their in-flight runs (up to about 36 a part) are redone in the sweeps.
     About 1 GPU-hour a part at worst.
4. **B20's runs at 1:30** (B20 log §14), not 3:00 or 4:00.
   - Cost: its start (up to about 20 minutes) recurs in each job, so B20 takes more jobs. It keeps 10 jobs fitting
     under the cap, and nights use 4:00.
5. **B1R2 at 3 questions a part (2:30), not 2 (1:30).** B1's engine runs one configuration at a time in batches of up
   to 8, so a 2-question part (10 runs) wastes most of its second batch.
   - Cost: only 6 B1R2 jobs fit at once (900 of 960), not 10. B1R2 is last, and nothing waits on it before Nov 17.
6. **B1R2 decided now** (the A39 log's §13). It needs 0.63 of an A100 around the clock, and the cap allows 10.
   - Cost: if Sol stays full for days, B1R2 is read partial, as pre-registered. It runs last, so it can't delay A39,
     B20 or the 30.
7. **The calendar is a projection,** from a simple schedule under the cap. The real starts come from
   `squeue --start` after each wave. PLAN keeps a day's margin and the read dates (Nov 17) as they were.
   - Cost: none for the rules; only the plan's dates.

## 7. What waits for Ritik

- Submit the lines in §4 as places free: lines 1–5 first (B20), then E2's.
  - Before a night away, use the night shapes.
  - Run `squeue --start -u $USER` after each wave.
- **Optional:** `sacctmgr -P show qos class format=Name,MaxJobsPU,MaxSubmitPU,MaxTRESRunMinsPU`, to see whether
  MaxJobsPU changed. The plan doesn't depend on it.
- **For B1R2:** a `git pull` on Sol (safe: §5), then its lines last.
- Nov 6 morning: Arsha's bundle (`trackB_20261106`), with a fresh-clone check.
- By Nov 7: the L3 call with Shrey, then the first check-in and merge.
- Nov 11 09:00: the 30's rule. It has no effect if E2 and B20 are done.

## 8. Checks

- **Tests:** `submit.sh`'s 4 failing first, then passing; B1R2's 6 (5 failing first); B1's, A38's, A39's and the kit's
  tests unchanged and passing. The full suite: 830 passed, 1 skipped (823 last night, plus 6 for B1R2 and 1 for `submit.sh`).
- **Links:** `check_links`: 0 broken, 0 missing RUNBOOK scripts.
- **Summaries:** `export_summaries --check`: all numbers-only.
- **Bundles:** both dry runs: B 33 files, 62.5 MB; C 43 files, 31.3 MB.
- **Nothing missing:** all 710 files tracked at `d4ae9ab` are still at their path; nothing was deleted.
- **The Gantt:** `make_gantt.py --dry-run` ok, then regenerated. Due dates: A39, B1R2 and B20 Nov 15; R4 done
  (Nov 4).
- **Commits:** `21e0386` (the amendments, 00:49, alone and first), then this session's work, then the supplement.
  All are Ritik's, with no attribution. The pre-push check runs at the push.
