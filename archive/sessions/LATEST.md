# Session log: the Sol feeder (2026-11-04 01:24 MST)

By: Ritik. Ritik's message of about 01:20, seven items, with Sol's output.

**The ask:** 118 lines by hand won't work, because places free up while Ritik sleeps or is in class, and the
dependency placeholders are easy to get wrong. So a feeder on Sol keeps the queue full from a tracked queue file.

**What Sol showed:**
- 9 jobs before the Gemma smoke, which was submitted as 457471. That makes 10: 8 running (689 GPU-minutes left) and
  2 pending (270 requested).
- The Nemotron smoke and the three B20 run lines were refused ("more than 10 jobs").
- Ritik also got a warning from Sol about an idle GPU on a job, which might be cancelled.

**The safety rule for Sol, kept:** nothing a queued or running job loads changes. The feeder, its queue file and
`submit.sh` run on the login node; no job loads them.

## Plans for the structural changes (written before each)

- **The queue file** (`finetune/gpu/sol/queue_2026-11-04.txt`, tracked): one job a line, `LABEL | OPTIONS | submit.sh
  arguments`, in §4's order of the 00:26 log.
  - Dependencies refer to earlier lines by label (`afterok=@b20-gemma-smoke`) or to a job id.
  - Jobs already submitted by hand are lines with `job=N`, so later lines can depend on them.
- **The feeder** (`tools/sol_feeder.py`, standard library only, Python 3.6 or later, on the login node).
  - One tick: the stop file; the jobs' states (sacct); then the lines in order.
  - A line goes in through `submit.sh` when its dependencies have ended as required, a place is free and its
    GPU-minutes fit.
  - Each line's job id is recorded in a state file before the next line is looked at. Its `--comment=feeder:LABEL`
    lets a restart recover a submission it didn't record.
  - **The dependencies are the feeder's, not Slurm's.** A line is submitted after its dependencies end. So no pending
    job holds one of the 10 places while it waits, and none waits forever behind a failed job
    (`DependencyNeverSatisfied`).
  - **The references are still replaced by real job ids:** in the checks and in the log.
- **`submit.sh`:**
  - `--check` (every check, then "nothing submitted"), so the feeder uses the same limits as a person;
  - `--mail-type=FAIL` to `$TRACKA_MAIL` (default `$USER@asu.edu`; `none` turns it off). It goes on the sbatch command
    line, not in the job scripts, so every job gets it, no tracked file holds an address, and no `.sbatch` file
    changes.
- **No folder moves; nothing deleted.**

## 1. The queue file (item 1)

`cot-disclosure/finetune/gpu/sol/queue_2026-11-04.txt`, 153 lines, generated from the 00:26 log's §4 order so it
can't drift (`test_the_queue_file_follows_the_plan` checks the order, the parts and every sweep's references):
- 11 lines already submitted (`job=`): the 9 A39 parts and the two smokes (456999, 457471). Later lines wait on them by
  label.
- **B20 first:**
  - Nemotron's smoke;
  - each model's runs after its own clean smoke (`afterok=@b20-<model>-smoke`);
  - then up to 5 more jobs a model (`again=`). Each runs only if the one before stopped at its limit with runs left
    (B20's exit 2), and is "not needed" once a job finishes its runs (exit 0).
- **E2:**
  - the 28 sixteenths in §4's order;
  - the 15 fifths;
  - a sweep per system (core and wrapper), after every part of that system (`afterany`), and only if runs are left
    (`left=`, counted by `finetune/eval.py`'s own resume rule). So a sweep never starts a GPU for nothing.
- **The 30:** 16 quarters, 6 halves and 7 sweeps. Its Nov 11 rule stays Ritik's check, since E2 and B20 are projected
  done days before.
- **B1R2 last:**
  - 40 parts, then 4 sweeps;
  - each `needs=27a2a39`, the commit with `--b1r2`: a line waits until Sol's clone has it.

## 2. The feeder (item 2)

`cot-disclosure/tools/sol_feeder.py`: standard library only, Python 3.6 or later. On Sol, run it with
`/scratch/$USER/envs/olmo/bin/python`, which also runs the "runs left" counts.

**One tick:**
1. The stop file ends it.
2. Every job it knows gets its state from sacct (squeue while sacct doesn't know it yet).
   - A job that ends other than COMPLETED with exit 0 is an alert, once.
   - A B20 stop at its limit isn't, when a line runs it again.
3. The lines, in order. A ready line goes in through `submit.sh` when `submit.sh --check` leaves it a place in the 10
   and its GPU-minutes fit what the running and pending jobs leave of the 960.
   - The first ready line that doesn't fit ends the tick, so the order holds.
   - A line waiting on a dependency doesn't block the ones after it.

**Never a line twice:**
- A line is marked "submitting" in the state file before `submit.sh` runs, and gets its job id right after.
- Each job carries `--comment=feeder:LABEL`. A restart finds a submission it didn't record by that comment.
- If no job carries it, the line is held as "unknown" and you're told. It is never resubmitted.

**Dependencies are the feeder's, not Slurm's.** References become job ids (in the checks, the log and `--status`), but
a line is submitted only after its dependencies have ended. So:
- no pending job holds one of the 10 places waiting;
- none waits forever behind a failed job (Slurm's `DependencyNeverSatisfied`);
- and no `--dependency` names a job that already ended, which `submit.sh` refuses.

**Failures:**
- A failed `afterok` dependency skips the line, logs it and mails you.
- A transient failure doesn't skip anything: squeue down, a command timed out or missing. The tick ends and the next
  tries again.
- `submit.sh` failing 3 times on one line holds that line and mails you.
- It never resubmits a job that ended. `--reset LABEL` is yours.

**Where things are:**
- the log: `/scratch/$USER/trackA/feeder.log`;
- the state: `/scratch/$USER/trackA/feeder/state.json`, under a lock, so two feeders never tick at once;
- the stop file: `/scratch/$USER/trackA/feeder.stop`.

**Modes:**
- `--once` (scrontab) and `--loop` (every 5 minutes; the stop file is checked every 10 s);
- `--dry-run` (changes nothing; tried on the Mac without Slurm: it waits instead of failing) and `--status`;
- `--adopt`, `--skip`, `--reset`.

**Alerts:**
- the log, the state file's last 100 (shown by `--status`);
- one mail a tick to `$TRACKA_MAIL` or `$USER@asu.edu`, through the node's `mail`, `mailx` or `sendmail` if it has one.

## 3. Where it runs (item 3)

- **The check:** `scontrol show config | grep -iE 'ScronParameters|MailProg|MailDomain'` and `scrontab -l`.
  scrontab works if ScronParameters shows `enable` and `scrontab -l` doesn't say it's disabled.
- **scrontab (Ritik's first choice):** a tick every 5 minutes as a small CPU job (1 core, 10 minutes).
  - It survives logouts and login-node restarts.
  - Its cost: between ticks it waits in the queue as one of your 10 places, so 9 are left for work. The feeder counts
    it like any job.
- **Otherwise:** `nohup ... --loop` on a login node. It uses almost no CPU.
  - It dies if that node restarts. `--status` shows the last tick's time and host.
- The exact lines are in §7.

## 4. Failure mail (item 4)

- `submit.sh` now puts `--mail-type=FAIL --mail-user=$USER@asu.edu` on every sbatch line. `TRACKA_MAIL` picks another
  address, and `none` turns it off.
- It is on the command line, not in the `.sbatch` files: every job gets it, no tracked file holds an address, and none
  of the job scripts the queued jobs came from changes.
- Whether Sol delivers it: `scontrol show config | grep -i MailProg` (set means yes).
- Note: a B20 job stopped at its limit exits 2, so Slurm mails "FAILED" for it too. The feeder treats it as planned
  and runs the model's next line.

## 5. The order, and the night shapes (item 5)

- **The order is the 00:26 log's §4:**
  1. B20's smokes and runs;
  2. E2's sixteenths, then the fifths, then the sweeps;
  3. the 30;
  4. B1R2 last, behind its commit check.
- **The night shapes aren't used.** They were there only because nobody refilled the places at night: 10 places × 1:30
  is about 10 GPU-hours, then idle.
  - The feeder refills them every 5 minutes, day and night. So 1:30 jobs stay best around the clock: 10 at once, and
    longer ones would fit fewer under the 960.
  - If the feeder stops, `--status` shows it, and the longer shapes (A39 log §12.5, §13.5) are still there by hand.

## 6. Tests (item 6), the idle-GPU warning

**Tests:** `tests/test_sol_feeder.py`, 21, all failing first (the module didn't exist), plus 1 in the kit's tests for
`submit.sh --check` and the mail options (failing first on the old `submit.sh`). They cover:
- the order;
- references becoming job ids, with no `--dependency` on the sbatch line;
- no second submission after a restart, including a crash between sbatch and the record;
- a failed dependency skipping its line, with one mail;
- the 10 places;
- the GPU-minutes holding the order;
- B20's `again=`;
- `needs=` and `left=`;
- an uncounted queue ending the tick;
- the stop file;
- `--dry-run` writing nothing;
- `--adopt`, `--skip` and `--reset`;
- bad queue lines;
- `$USER` in the queue's arguments, expanded by the feeder, so the kit names no Sol user (the
  second-user test caught a literal one on the first full run);
- the real queue file against the plan;
- the runs-left count against `eval.py`'s resume;
- one tick through the real `submit.sh` with fake Slurm commands.

**The idle-GPU warning** (Ritik saw one; its text isn't here).
- Every job here leaves its GPU idle at its start: the vLLM option check (`vllm serve --help=all`, up to 15 minutes in
  B20's), and loading the weights.
- If Sol cancels a job for it, sacct shows CANCELLED. The feeder then mails you and doesn't resubmit:
  - an A39 part's leftovers go to its system's sweep;
  - a B20 model's next line is skipped until `--reset`.
- The warning's job id and threshold would show which start is too long. Nothing in the job code changes while jobs
  are queued.

## 7. The Sol lines: pull, dry-run, start (item 7)

**The pull is safe for the queued and running jobs.** This session changed only things no job loads:
- `submit.sh`, run on the login node;
- the feeder and its queue file (new);
- tests and docs.

What the 00:26 log's §5 says of the pull still holds.

```bash
cd /scratch/ragarw68/cse598-cot-faithfulness
git rev-parse --short HEAD                          # d4ae9ab or ef815ba (or 14105b7)
git fetch -q origin
git diff --stat HEAD..@{u} -- cot-disclosure/finetune/gpu/sol/run.sh cot-disclosure/finetune/gpu/sol/env.sh \
  cot-disclosure/finetune/gpu/sol/guard.sh cot-disclosure/finetune/eval.py cot-disclosure/finetune/gpu/eval_job.py \
  cot-disclosure/finetune/gpu/vllm_options.py cot-disclosure/progress/sol_b20.py cot-disclosure/progress/run_b20.py
                                                    # must print nothing
git pull --ff-only

P=/scratch/ragarw68/envs/olmo/bin/python; F=cot-disclosure/tools/sol_feeder.py
$P $F --dry-run                                     # what a tick would submit now (the queue is full: nothing yet)
$P $F --status | head -20                           # 153 lines; 11 known jobs
scontrol show config | grep -iE 'ScronParameters|MailProg|MailDomain'
scrontab -l; command -v mail mailx sendmail
```

**Start: scrontab** (if ScronParameters says `enable`):
```bash
cat > /scratch/ragarw68/trackA/feeder.scron <<'SCRON'
#SCRON -A class_cse59888883fall2026 -p public -q class -t 0:10:00 -c 1 --mem=2G -J trackA-feeder
#SCRON -o /scratch/ragarw68/trackA/slurm/feeder-%j.out
*/5 * * * * cd /scratch/ragarw68/cse598-cot-faithfulness && /scratch/ragarw68/envs/olmo/bin/python cot-disclosure/tools/sol_feeder.py --once
SCRON
scrontab /scratch/ragarw68/trackA/feeder.scron      # replaces your scrontab (scrontab -l first if you have one)
scrontab -l; squeue -u $USER -n trackA-feeder       # status: the entry, and its job waiting for its next run
```
**Stop it:** `touch /scratch/ragarw68/trackA/feeder.stop`; to remove it, `scrontab -r`.

**Start: otherwise, on a login node:**
```bash
rm -f /scratch/ragarw68/trackA/feeder.stop
nohup $P $F --loop >> /scratch/ragarw68/trackA/feeder.out 2>&1 &
echo "feeder pid $! on $(hostname)"
```
**Stop it:** `touch /scratch/ragarw68/trackA/feeder.stop`. It ends within 10 seconds.

**Status, either way:**
- `$P $F --status | head -20`;
- `tail -20 /scratch/ragarw68/trackA/feeder.log`.

The first tick reads the 11 known jobs' states. If one has already ended badly (say a smoke), you get its mail at
once.

## 8. Checks

- **The suite:** 852 passed, 1 skipped. The first full run had 1 failure: the queue file named a Sol user, which the
  second-user test refuses. It now says `$USER`, which the feeder expands; a new test covers that.
- **Links:** 0 broken.
- **Summaries:** numbers-only.
- **Bundles:** both dry runs: B 33 files, 62.5 MB; C 43 files, 31.3 MB.
- **Nothing missing:** all 713 files tracked at `ef815ba` are still at their path.
- **The frozen files:** none of last night's 49 changed since `ef815ba`.
- **The Gantt:** regenerated; R5 done.
- **Commits:** Ritik's, with no attribution. The pre-push check runs at the push.
