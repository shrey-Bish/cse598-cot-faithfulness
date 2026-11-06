# B20 on your own Sol account (Arsha)

Last updated: 2026-11-06 11:10 (step 4: owner-only `trees/*.json` in the HF cache, and the fix; earlier 09:18, the handoff: your Sol clone on `trackB-main` from the start, step 2; Ritik's own Sol
check before steps 4 and 6; you never commit in the Sol clone). Earlier: 2026-11-05 09:20 (B20 moves to your
account). **Edited by:** Ritik until his last push to `trackB-main` on Nov 6, then Arsha.

**What this is.** From Nov 5, B20 runs on your own Sol account, with commands you type yourself in your own login. No
password, key or login is shared, and nobody uses anyone else's. Ritik's account runs A39 and A40. Yours runs all of
B20's remaining runs (Granite 849, Gemma 1,784; Nemotron's are done) on a feeder of your own, which reads the B20-only
queue `cot-disclosure/finetune/gpu/sol/queue_b20_2026-11-05.txt`: one chain of 3:00 jobs a model (8 Granite lines, 12
Gemma lines), so one job a model at a time. Ritik's queue no longer has B20 lines, so no line is ever submitted from
both accounts. B20's runs end by Nov 15 and are read by Nov 17. The kit is
`cot-disclosure/finetune/gpu/sol/`; [SOL_SETUP.md](../tracks/SOL_SETUP.md) is the general page for a second user, and
this page is what B20 needs.

**Your fair share** (from Ritik's `sshare` of the course account, Nov 5, 08:43):
- Sol orders pending jobs partly by each user's FairShare factor (0 to 1). In the course account everyone has the same
  shares, so your factor falls with your own recent GPU use (which decays over time). The numbers appear to fit Slurm's
  classic formula, 2^(−usage/shares), with about 53 users of equal shares (inferred from one paste; `scontrol show
  config | grep -i PriorityFlags` would say).
- Ritik's is 0.0019, the lowest listed: his use is 84% of the account's. Users with no use have 0.87; those with a
  little, 0.58 to 0.75.
- Your line wasn't in his paste. Unless you have run a lot on Sol lately, yours is near 0.87, far above his. It falls
  as B20 uses GPU time, and stays above his while your use stays below his. Step 1 shows it.
- It is one part of a job's priority, not a start time: `squeue --start -u $USER` gives estimates. The certain gain is
  your own limits: 960 running GPU-minutes and 10 places, so B20 no longer waits behind A39 and A40.

**What you use of Ritik's, read-only:** his two Python environments and B20's two model snapshots, through links in
your own scratch (step 4). Every file a B20 job writes goes to your own scratch, your home or the node's `/tmp`. Ritik
leaves those four folders unchanged (no install, no rebuild, no `chmod`) until B20's last job ends.

**On your machine:** `export SOL_USER=<your Sol user>`. Every `ssh` or `rsync` to Sol is one Duo push (the ASU VPN when
off campus).

## Setup, once (Sol, in your own login)

**1. Log in; check your account, your group and your fair share.**
```bash
ssh $SOL_USER@login.sol.rc.asu.edu                       # on your machine
sacctmgr -nP show assoc user=$USER format=Account,Partition,QOS
id -Gn | tr ' ' '\n' | grep -x class_cse598fall2026
sshare -U -A class_cse59888883fall2026 -o Account,User,RawShares,NormUsage,EffectvUsage,FairShare
```
- **Expected:**
  - a line that starts `class_cse59888883fall2026` and ends `class` (if others are listed, use only this one, never a
    `grp_…`);
  - `class_cse598fall2026`;
  - one row of yours, with FairShare well above Ritik's 0.0019.
- **Either name missing:** stop and tell Ritik. Steps 4 and 6 read his files through that group.

**2. Your clone, on your branch** (`trackB-main`: since Ritik's last push on Nov 6 it is the same commit as `main`):
```bash
git clone -b trackB-main https://github.com/shrey-Bish/cse598-cot-faithfulness.git /scratch/$USER/cse598-cot-faithfulness
cd /scratch/$USER/cse598-cot-faithfulness
git rev-parse HEAD origin/trackB-main             # two lines, the same commit
grep -q TRACKA_SCRATCH cot-disclosure/finetune/gpu/sol/env.sh && echo "per-user kit: ok"
ls cot-disclosure/finetune/gpu/sol/queue_b20_2026-11-05.txt
```
- **Expected:** two lines, the same commit, the one Ritik's message names (or a later one of yours); `per-user kit:
  ok`; and the queue file.
- **The two commits differ, or not the one Ritik named:** stop and tell Ritik. A queued job reads its code from this
  clone when it starts.
- **A clone you made before Nov 6, on `main`:** switch it, once, while no B20 job of yours is pending or running:
  ```bash
  cd /scratch/$USER/cse598-cot-faithfulness && git fetch origin
  git rev-parse HEAD origin/trackB-main        # two lines, the same commit (else: git pull --ff-only first)
  git checkout trackB-main                     # "... set up to track 'origin/trackB-main'"
  ```
- **This clone only runs jobs: you never commit in it.** Your commits come from your machine's clone (START_HERE
  §10), and reach this one only by a pull. No `git config user.*`, no hooks and no edits are needed here; the one
  file you add, step 3's accounts file, stays uncommitted.
- **Every later `git pull` here:** first run [CHECKIN.md](../status/CHECKIN.md) §1 step 4's `git diff --stat HEAD..@{u}`
  in this clone. Pull only if it prints nothing, or while no B20 job is pending or running.

**3. Your accounts file** (no secret in it; leave it uncommitted, `git status` shows it):
```bash
mkdir -p cot-disclosure/finetune/gpu/sol/accounts.d
echo "class_cse59888883fall2026  public  class  960  10  10  24  4" > cot-disclosure/finetune/gpu/sol/accounts.d/$USER.conf
cot-disclosure/finetune/gpu/sol/submit.sh b20 --model granite-4.2-8b --estimate 2.3 --check
```
- **Expected** (with no jobs of yours queued):
  - `QoS check: this job 3:00:00 x 1 GPU = 180 GPU-minutes; running 0 …`;
  - `limits: 960 of 960 GPU-minutes free now (this job needs 180); 9 of 10 places left …`;
  - `check only: nothing submitted`.
- **`refusing: account … is not listed`:** the file's name or its first word is wrong.

**4. The environments: Ritik's, read-only, through links.** Ritik checks first, in his own login, that these folders
and B20's saved runs (step 6) are open to the course group; his message says when that's done.

Can you read them?
```bash
R=/scratch/ragarw68
find -H $R/envs/olmo $R/envs/olmo-vllm $R/hf/hub/models--ibm-granite--granite-4.2-8b $R/hf/hub/models--google--gemma-4-26B-A4B-it \
     ! -type l \( ! -readable -o -type d ! -executable -o -type f -perm -u+x ! -executable \) -print 2>&1 | head -5
$R/envs/olmo/bin/python -c 'import sys, importlib.metadata as m; print(sys.version.split()[0], "torch", m.version("torch"), "transformers", m.version("transformers"))'
$R/envs/olmo-vllm/bin/python -c 'import importlib.metadata as m; print("vllm", m.version("vllm"), "torch", m.version("torch"))'
```
- **Expected:** `find` prints nothing (it takes a minute or two). Then `3.11.… torch 2.14.1… transformers 5.18.0` and
  `vllm 0.31.0 torch 2.13.0`.
- **`find` prints paths or `Permission denied`:** send Ritik the lines. He makes them group-readable in his own login;
  then run it again. Or build your own (the fallback below).
- **Known case (Nov 6, 11:10):** the Hugging Face cache can keep its `trees/<sha>.json` files owner-only
  (`-rw-------`), though the snapshot itself is open. Ritik's two were
  `models--google--gemma-4-26B-A4B-it/trees/4d7ae4984b7db7de8f8457170b3f1a419ee76d52.json` and
  `models--ibm-granite--granite-4.2-8b/trees/a7042144125ce5ae64f89610e8289647fc000b9a.json`. He ran `chmod g+r` on
  both on Nov 6, so they now read `-rw-r----- … class_cse598fall2026`.
  - **If such a file shows up again:** only its owner can fix it, with `chmod g+r <file>` in their own login. Send
    Ritik the path.

The links (the `ls -d` must say "No such file or directory" twice; if either folder exists, stop and tell Ritik):
```bash
ls -d /scratch/$USER/envs /scratch/$USER/hf
mkdir -p /scratch/$USER/envs /scratch/$USER/hf/hub
ln -s $R/envs/olmo $R/envs/olmo-vllm /scratch/$USER/envs/
ln -s $R/hf/hub/models--ibm-granite--granite-4.2-8b $R/hf/hub/models--google--gemma-4-26B-A4B-it /scratch/$USER/hf/hub/
cd /scratch/$USER/cse598-cot-faithfulness
(source cot-disclosure/finetune/gpu/sol/env.sh && echo "$TRACKA_PY $TRACKA_VLLM $HF_HOME $TRACKA_OUT")
```
- **Expected:** `/scratch/<you>/envs/olmo/bin/python /scratch/<you>/envs/olmo-vllm/bin/vllm /scratch/<you>/hf
  /scratch/<you>/trackA`, and no `wrong Python` line.
- **Why links, and not `TRACKA_SCRATCH=/scratch/ragarw68`:**
  - `env.sh` takes the environments, `HF_HOME` and every output folder from `TRACKA_SCRATCH`. Pointing it at Ritik's
    scratch would send a job's writes where you can't write.
  - With the links, `TRACKA_SCRATCH` stays yours. A job reads Ritik's environments and snapshots through the links,
    and writes everything in your own places:
    - outputs and logs in `/scratch/$USER/trackA`;
    - results and stop files in your clone;
    - Hugging Face's own files in `/scratch/$USER/hf`;
    - the caches of vLLM, Triton and FlashInfer in your home.
  - No file of the kit changes. And it is the exact environment B20's runs so far came from.
- **Fallback: your own environments** (if you can't read Ritik's):
  - Run [SOL_SETUP.md](../tracks/SOL_SETUP.md) step 4 as written: `mamba create`, `setup_env.sh`, `setup_vllm.sh`, the
    import check. It takes about 30–45 minutes, plus the wait for the allocation. Make no links.
  - Step 5 then downloads instead of checking: 17.6 and 51.6 GB, about 70 GB of your scratch. About 1–3 hours in all.
  - Packages that nothing pins may then differ from Ritik's. The canary flags any job whose completions differ from
    the model's first job (in the report, never a stop).

**5. The model snapshots: checked, not downloaded.** No GPU, limit 2:00 each, and each holds one of your 10 places.
The second waits for the first:
```bash
cd /scratch/$USER/cse598-cot-faithfulness
J=$(cot-disclosure/finetune/gpu/sol/submit.sh get_b20 --model granite-4.2-8b | tail -1 | awk '{print $4}'); echo "Granite's check: job $J"
cot-disclosure/finetune/gpu/sol/submit.sh get_b20 --model gemma-4-26b-a4b-it --dependency=afterany:$J
```
If the first prints no job id, `submit.sh` printed why, and the second refuses (`no job id in --dependency`).
Once both have left `squeue -u $USER`:
```bash
grep -h "match the Hub" /scratch/$USER/trackA/slurm/trackB-get-b20-*.out
ls /scratch/$USER/trackA/b20/*/snapshot.json
```
- **Expected:**
  - two lines: `ibm-granite/granite-4.2-8b@a7042144: already cached at /scratch/<you>/hf/hub/models--ibm-granite--…;
    N files (17.6 GB) match the Hub; …`, and Gemma's (`google/gemma-4-26B-A4B-it@4d7ae498`, 51.6 GB);
  - two `snapshot.json` files.
- Each job reads every file through the link and checks it against the Hub. It then writes your own record, which
  every B20 job checks before it serves.
- **`downloaded` instead of `already cached`:** the link wasn't found, so the job fetched its own copy. That is fine,
  but check step 4.
- **No line, or `Permission denied` in the `.out`:** send Ritik its last lines.

**6. B20's saved runs, from Ritik's clone to yours.** Copy only while no B20 job is pending or running on either
account. Ritik confirms his side (his Sol check, the same message as step 4's): no `trackB-b20` job, and no B20 line
in his feeder's queue. Then:
```bash
squeue -h -u $USER -n trackB-b20                         # prints nothing (your feeder isn't started yet)
FROM=/scratch/ragarw68/cse598-cot-faithfulness/cot-disclosure/results/trackB/b20
TO=/scratch/$USER/cse598-cot-faithfulness/cot-disclosure/results/trackB/b20
mkdir -p $TO && rsync -a $FROM/ $TO/ && ls $TO
cd /scratch/$USER/cse598-cot-faithfulness/cot-disclosure; P=/scratch/$USER/envs/olmo/bin/python
for d in $FROM $TO; do $P -c 'import sys; sys.path.insert(0, "progress"); from common import load; [print(m, len(load(f"{sys.argv[1]}/{m}/b20_sol_vllm_runs.jsonl")), len(load(f"{sys.argv[1]}/{m}/b20_sol_vllm.jsonl.gz"))) for m in sys.argv[2:]]' $d granite-4.2-8b gemma-4-26b-a4b-it nemotron-3-nano-30b-a3b; done
for m in granite-4.2-8b gemma-4-26b-a4b-it nemotron-3-nano-30b-a3b; do $P progress/run_b20.py --dry-run --model $m | head -1; done
```
- **Expected:**
  - `ls`: the three model folders;
  - the counts: the same three lines twice, Ritik's then yours (Granite `129 129` on Nov 5 at 08:43);
  - the dry run: `B20: 849 jobs to run …`, `B20: 1,784 jobs to run …`, `B20: 0 jobs to run …`.
- **What is copied:**
  - every file the runner resumes from: `b20_sol_vllm_runs.jsonl` says which runs are done, and new records are added
    to `b20_sol_vllm.jsonl.gz`;
  - each model's `canary.jsonl` (each later job is compared with the model's first), `template_check.json`,
    `smoke_check.json` and `b20_flags.jsonl`.
- **`Permission denied`:** Ritik makes that folder group-readable in his own login; then copy again.
- **Other counts or other runs left:** stop, don't start the feeder, and tell Ritik.
- After the copy, Ritik's B20 folder is never written again: his account runs no B20.

**7. Your feeder: check it before it starts.**
```bash
cd /scratch/$USER/cse598-cot-faithfulness
P=/scratch/$USER/envs/olmo/bin/python; F=cot-disclosure/tools/sol_feeder.py; Q=cot-disclosure/finetune/gpu/sol/queue_b20_2026-11-05.txt
$P $F --queue $Q --status | head -8
$P $F --queue $Q --dry-run
```
- **Expected `--status`:**
  - `last tick: never on - (pid -); stop file /scratch/<you>/trackA/feeder.stop: absent`;
  - `20 lines: 20 to submit`;
  - `b20-granite-r3-1` and `b20-gemma-r3-1` `to submit (needs <commit>: on Sol)`, every other line
    `to submit (again:@<the line before>)`.
- **Expected `--dry-run`:**
  - two lines, `[dry run] would submit b20-granite-r3-1 (no dependency): submit.sh b20 --model granite-4.2-8b …
    --comment=feeder:b20-granite-r3-1`, and the same for `b20-gemma-r3-1`;
  - nothing skipped and no `ALERT`. The other lines wait, each for the job before it, so the dry run doesn't list
    them.
- **`not on Sol yet`:** your clone lacks that commit. Run `git pull --ff-only` (step 2's rule).
- **The owner check:** the B20 queue's first line, `owner: not ragarw68`, lets any account's feeder but Ritik's use
  it; his queue says `owner: ragarw68`. Without `--queue` (his queue is the default), the feeder stops at once with
  `sol_feeder: refusing …/queue_2026-11-04.txt: its owner line says "owner: ragarw68", and you are <you>: run your own
  account's queue file (--queue)`, and changes nothing. Always pass `--queue $Q`.
- **No `--reset` needed:** your feeder's state (`/scratch/$USER/trackA/feeder/state.json`) doesn't exist yet. So no
  line has a job or a skip, and the `-r3-` labels are new. The resets in Ritik's notes were for his own state's `-r2-`
  lines.

**8. Start it under scrontab** (only after step 5's two jobs matched the Hub and step 6's numbers matched):
```bash
scrontab -l                                              # anything besides comments: add the 3 lines below to it instead
mkdir -p /scratch/$USER/trackA/slurm
cat > /scratch/$USER/trackA/feeder.scron <<SCRON
#SCRON -A class_cse59888883fall2026 -p public -q class -t 0:10:00 -c 1 --mem=2G -J trackA-feeder
#SCRON -o /scratch/$USER/trackA/slurm/feeder-%j.out
*/5 * * * * cd /scratch/$USER/cse598-cot-faithfulness && /scratch/$USER/envs/olmo/bin/python cot-disclosure/tools/sol_feeder.py --once --queue cot-disclosure/finetune/gpu/sol/queue_b20_2026-11-05.txt
SCRON
scrontab /scratch/$USER/trackA/feeder.scron
scrontab -l; squeue -u $USER -n trackA-feeder
```
- **Expected:**
  - the entry, with your user in its paths;
  - the feeder's job pending (it waits between ticks and holds one of your 10 places);
  - within 10 minutes, `$P $F --queue $Q --status | head -8` shows a last tick under 5 minutes old and job ids on
    the first Granite and Gemma lines, and `squeue -u $USER` shows two `trackB-b20` jobs.
- **Mail:** all to `$USER@asu.edu`.
  - Each job mails you if it fails (`submit.sh`).
  - The feeder mails its alerts and, at the first tick after 07:00, a daily digest (also in
    `/scratch/$USER/trackA/feeder/digest.txt`).
  - For another address, put `TRACKA_MAIL=<address> ` before `/scratch/$USER/envs/…` in the entry (both use it).
- **Day to day:**
  - `$P $F --queue $Q --status | head -20`, the digest, and `squeue --start -u $USER` (start estimates, the only
    source for dates).
  - Submit nothing by hand while it runs. A line that ended badly goes in again only with
    `$P $F --queue $Q --reset LABEL`, once you know why it ended.
- **Stop:** `touch /scratch/$USER/trackA/feeder.stop` (`rm` it to start again). To remove the entry: `scrontab -r`.
  If `--status` says `late` again and again, use RUNBOOK §0's nohup loop, with `--queue $Q`.

**9. Reading B20: the copy-back.** On your machine, from your clone's `cot-disclosure/`. Numbers only: the records with
text (`*.jsonl.gz`) stay on Sol.
```bash
rsync -av --exclude '*.jsonl.gz' $SOL_USER@login.sol.rc.asu.edu:/scratch/$SOL_USER/cse598-cot-faithfulness/cot-disclosure/results/trackB/b20/ results/trackB/b20/
../.venv/bin/python progress/run_b20.py --dry-run | head -1     # runs left: a status count, any time
../.venv/bin/python progress/run_b20.py --report               # the readings: only when B20's rule allows
```
- **`--report`** reads each model's `b20_flags.jsonl` and `canary.jsonl`. It prints R1 to R3b per model and setting,
  and writes `results/trackB/b20/b20_report.json`.
- **When:** B20's log says when it may be read (§19, the partial-read rule). Until then, copy and count only.
- **Ritik's copy, only if you choose to grant it.** He can copy your numbers with his own login if your folders let
  the course group in:
  ```bash
  D=/scratch/$USER/cse598-cot-faithfulness/cot-disclosure/results
  ls -ld /scratch/$USER $D/trackB/b20                 # the group column must read class_cse598fall2026
  chmod g+x /scratch/$USER /scratch/$USER/cse598-cot-faithfulness /scratch/$USER/cse598-cot-faithfulness/cot-disclosure $D $D/trackB
  chmod -R g+rX $D/trackB/b20 && chmod g-r $D/trackB/b20/*/b20_sol_vllm.jsonl.gz
  ```
  - If the group column reads another group, run `chgrp class_cse598fall2026` on the same folders first
    (`chgrp -R` for `b20`).
  - The second `chmod` keeps the records with text closed. Then Ritik, from his own clone's `cot-disclosure/` on his
    Mac:
    ```bash
    rsync -av --exclude '*.jsonl.gz' login.sol.rc.asu.edu:/scratch/<your Sol user>/cse598-cot-faithfulness/cot-disclosure/results/trackB/b20/ results/trackB/b20/
    ```
  - The group is the whole class (about 53 students), so every member can then read those files. And `g+x` on
    `/scratch/$USER` also opens to them anything below it that is already group-readable (`ls -l` shows which). To
    undo: `chmod g-x /scratch/$USER` and `chmod -R g-rwx $D/trackB/b20`.
  - Not granting it is fine: B20 is yours to read, and Ritik needs only the numbers you report.
