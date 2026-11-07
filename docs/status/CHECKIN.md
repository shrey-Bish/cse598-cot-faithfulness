# The daily check-in

**Edited by:** Ritik. Written 2026-11-04 16:19 MST; the labels corrected 17:54 (the standing rule, Nov 7, Nov 8); the daily rule 22:33; the push to two branches 22:34; Nov 5, 09:40: two Sol accounts (B20 on Arsha's), B1R2 dropped, §1 step 4 and §9.
History: `git log -- docs/status/CHECKIN.md`.

One routine, once a day, in this order: §1 to §7. §8 is the merge, on the merge days. §9 is what each day from Nov 5 to
Nov 24 brings. Run it after 07:00, when the feeder's daily digest is out.

Mac commands run from the repo root, `~/Documents/Projects/ODL/cse598-cot-faithfulness`, unless a line says
`cd cot-disclosure`. Sol commands run from Sol's clone, `/scratch/ragarw68/cse598-cot-faithfulness`. The steps
themselves are in [`RUNBOOK.md`](../RUNBOOK.md): §0 (the feeder), §16 (merges, the Sol safety list, data handoff), §17
(the pre-push check), §20 (session logs).

## The standing rules

- **Commits as Ritik** (`Ritik <his Gmail>`), with no attribution lines of any kind: no co-author
  trailer, no "generated with" line, no bot address.
- **Pre-register before any run.** A run's rule is committed in its session log before its first job; an amendment is
  committed before the runs it changes.
- **Nothing is chosen on any evaluation question** (E2, the 30, B20's questions). No outcome of A39, B1R2 or B20 is
  read before its rule says so. Status counts only.
- **LLM judges only under the LLM-judge protocol (pre-registered Nov 4), for labels only, always disclosed.** Ritik's
  labels are the final labels; the AI judges are their reliability check.
  - Corrected Nov 4, 17:54: this rule was "No automated judging of labels". Rater 2 was an AI model (ChatGPT 5 Astra
    High), not Shrey; see the
    [17:42 log](../../archive/sessions/2026-11-04/2026-11-04_1742_ALL_label-correction.md) and the protocol's
    [17:45 log](../../archive/sessions/2026-11-04/2026-11-04_1745_ALL_llm-judge-prereg.md).
- **Produced data never goes on GitHub.** Runs, replies and records stay in gitignored folders. Only numbers-only
  summaries under `cot-disclosure/results/summaries/` are tracked. Nothing from GPQA in any tracked file.
- **No paid calls.** Voyager and Sol only.
- **Times from the clock.** Run `date "+%H:%M"` immediately before writing any time (logs, headers, amendments, commit
  messages), and write exactly what it prints. Sol's dates come from `squeue --start`, never `--test-only`.
- **Teammates' paths.** Track C's paths are Shrey's (from Nov 3); Track B's are Arsha's from Nov 6
  (`cot-disclosure/configs/path_allowlist.txt`). On Ritik's branches they change only by merging the owner's branch
  (§8). A change the owner agreed to: `PATH_CHECK_ALLOW=trackB-main git commit ...` (or `trackC-main`); the commit
  message says so. After Nov 6, no commit of Ritik's touches Track B's paths except that way.
- **Results are read by their owners:** B20 by Arsha (from Nov 6); C19, C25, C20 and C26 by Shrey. Ritik reads A39
  and B1R2.

## The Sol access rule (Ritik's, in force)

- **Allowed:** read-only commands: `squeue`, `sacct`, `sshare`, `sprio`, `scrontab -l`, the feeder's `--status`,
  `--dry-run` and `--runs-left`, `git log`, `git status`, `git fetch`, `git diff`, and reading logs and status counts.
  Counts go through pipes, never temporary files.
- **`git pull --ff-only`** only after the safety diff (§1, step 4) prints nothing and the clone is clean.
- **Ask Ritik first** before submitting, cancelling, moving, renaming or deleting anything on Sol. That includes the
  feeder's `--adopt`, `--skip` and `--reset`, its stop file, and `scrontab`.
- **The feeder submits every job.** Nothing is submitted by hand.
- **If Sol needs a Duo approval,** skip every Sol step (§1, the copy-back in §2, any Sol part of §3 and §4) and say so
  in the report.

## 0. Open the day

```bash
cd ~/Documents/Projects/ODL/cse598-cot-faithfulness
date "+%Y-%m-%d %H:%M"                         # today's date and the log's time
git checkout trackA-nosol && git status --short # must print nothing (or only your own work in progress)
git fetch origin
git log --oneline -1 origin/main; git log --oneline origin/main..origin/trackC-main; git log --oneline origin/main..origin/trackB-main
```
- Name the log: `archive/sessions/<date>/<date>_<HHMM>_ALL_checkin.md` (a track's own work: `_A_`, `_B_` or `_C_`).
- Read the day's row in §9 and the carry-over: the previous day's "For <today>" section, the last in its daily
  (`archive/sessions/<previous date>/DAILY_<previous date>.md`).

## 1. Sol: status and the feeder's digest (read-only)

1. **Is Sol open without Duo?**
   ```bash
   ssh -O check login.sol.rc.asu.edu      # "Master running": go on. Anything else: Sol needs Duo; skip every Sol step
   ```
2. **The state** (one SSH call; read-only):
   ```bash
   ssh login.sol.rc.asu.edu 'bash -s' <<'EOF'
   cd /scratch/ragarw68/cse598-cot-faithfulness
   P=/scratch/ragarw68/envs/olmo/bin/python; F=cot-disclosure/tools/sol_feeder.py
   date "+%Y-%m-%d %H:%M"; git log --oneline -1; git status --short
   $P $F --status | head -16                         # last tick (not "late"), decision nov6, line counts, alerts
   cat /scratch/$USER/trackA/feeder/digest.txt       # today's digest: finished, failed, GPU-hours, gaps, rough finishes
   squeue -u $USER -o "%.10i %.28j %.2t %.10M %.10l %R"
   squeue --start -u $USER | head -15                # start estimates: the only source for dates
   scrontab -l | grep -v '^#'; squeue -u $USER -n trackA-feeder -h
   tail -5 /scratch/$USER/trackA/feeder.log
   EOF
   ```
   - **Check:** the last tick is under 30 minutes old; no new alert; the digest is today's. A failure in the digest
     or the alerts goes in the report, with its job id and exit. Exit 138 "done ... all its runs saved" is not a
     failure (RUNBOOK §0).
   - **The feeder late again and again** (the scron job stuck at `Priority`): RUNBOOK §0's switch to the nohup loop.
     That changes Sol: needs Ritik.
3. **Each A39 part that ran since yesterday served its own requests** (RUNBOOK §0):
   ```bash
   ssh login.sol.rc.asu.edu 'for f in $(ls -t /scratch/$USER/trackA/a39/vllm_*.log | head -6); do echo "$f $(grep -c "POST /v1/completions" $f) $(grep -o -- "--port [0-9]*" $f | tail -1)"; done'
   ```
   Each count is above 0 and each port is `2xxxx`. Otherwise stop and report it.
4. **The pull, only if safe.** Is anything a queued job loads changed? (RUNBOOK §16's list; `finetune/a39.py` and the
   queue file are loaded by no job.)
   ```bash
   ssh login.sol.rc.asu.edu 'bash -s' <<'EOF'
   cd /scratch/ragarw68/cse598-cot-faithfulness && git fetch -q origin && git log --oneline -1 @{u}
   git diff --stat HEAD..@{u} -- cot-disclosure/finetune cot-disclosure/progress/common.py cot-disclosure/progress/sol_trackB.py \
     cot-disclosure/progress/sol_b17.py cot-disclosure/progress/sol_b20.py cot-disclosure/progress/run_b20.py \
     cot-disclosure/progress/run_trackB.py \
     cot-disclosure/agents/__init__.py cot-disclosure/agents/sol_c13.py cot-disclosure/client.py cot-disclosure/parse.py \
     cot-disclosure/detect.py cot-disclosure/experiments.py cot-disclosure/tasks.py cot-disclosure/tools/answer_key.py \
     cot-disclosure/providers cot-disclosure/configs cot-disclosure/data \
     ':!cot-disclosure/finetune/a39.py' ':!cot-disclosure/finetune/gpu/sol/queue_2026-11-04.txt'
   EOF
   ```
   - **Prints nothing, and step 2's `git status --short` printed nothing:** pull.
     ```bash
     ssh login.sol.rc.asu.edu 'cd /scratch/ragarw68/cse598-cot-faithfulness && git pull --ff-only && git log --oneline -1'
     ```
   - **Prints anything:** don't pull. Report the files: needs Ritik (a changed file waits until the queued jobs that
     load it have started).
   - **From Nov 5, no job of Ritik's loads B20's files** (`progress/sol_b20.py`, `run_b20.py`, `run_trackB.py`): his
     queue has no B20 line. A change to them alone doesn't stop his pull. They stay on the list for Arsha's clone, where
     B20's jobs load them (her `SOL_ARSHA.md`, step 2).
   - Pull at the end of the day too, after §6's push, by the same rule, so Sol has the day's commits.

## 2. Copy back finished numbers

Numbers-only files only. The records with text (`*.jsonl.gz`) stay on Sol.
```bash
H=ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68
# B20: each model's flags, run rows, checks and canary (Arsha reads them; they go in her bundle)
rsync -av --exclude '*.jsonl.gz' $H/cse598-cot-faithfulness/cot-disclosure/results/trackB/b20/ cot-disclosure/results/trackB/b20/
```
A39 and B1R2 only once §3 says complete (or at their read date):
```bash
cd cot-disclosure && mkdir -p results/trackA/gpu/a39 results/trackA/gpu/b1r2
rsync -av --include='eval_*_a39_*_runs.jsonl' --exclude='*' $H/trackA/a39/ results/trackA/gpu/a39/
rsync -av --include='eval_prov-*_runs.jsonl' --exclude='*' $H/trackA/b1r2/ results/trackA/gpu/b1r2/
../.venv/bin/python tools/export_summaries.py --dry-run && ../.venv/bin/python tools/export_summaries.py
cd ..
```
- `export_summaries.py` refuses a file with question or reply text. From Nov 6 anything it writes under
  `results/summaries/trackB/` is Arsha's path: leave it uncommitted and tell her.
- Nothing new finished: say so in the report.

## 3. Read every experiment whose rule says it is complete

Each in its own session log (`<date>_<HHMM>_A_<name>-reading.md`), by its pre-registered rule only, with its F entry.
Nothing is read before its rule says so. The checks below run on Sol, from the clone, with `P` and `F` set as in §1.

| experiment | complete when (read-only check, on Sol) | read by | rule |
|---|---|---|---|
| **A39 on E2** (primary) | **complete (counted Nov 7, the A39 log's §22).** Count on the Mac after §2's copy-back: `finetune/a39.py --report` says "complete". Sol's `--runs-left` overcounts until Sol pulls the Nov 7 fix (a part's older `not_run` hid a sweep's `ok`) | Ritik, **by Nov 17** | the A39 log, §4 and §9 |
| **A39 on the 30** (beside it) | the same with `mmlupro_30`, unless dropped (Nov 6 or Nov 11) | Ritik, with E2 | §10.2, §16, §17 |
| **B1R2** | `for k in 1 2 3 4; do $P $F --runs-left b1r2:$k/4; done` all 0 (after Sol pulls the Nov 7 fix; before it, confirm on the Mac with the report's own counts); **or Nov 15 23:59**, whatever is done | Ritik, **when complete, by Nov 17** | the A39 log, §13 and §22 |
| **A40, A41, A42** | **read Nov 7** (F41–F43; the 13:29 and 13:31 logs), each once complete by its own rule | Ritik | their logs |
| **B20** | the feeder shows every line of a model done or not needed (`$P $F --status \| grep '^b20-'`) | **Arsha, by Nov 17** | the B20 log, §6, §8 and §10 |
| **C19, C25, C20, C26** | Shrey's own logs, merged in §8 | Shrey | his pre-registrations |

The logs: [A39](../../archive/sessions/2026-11-03/2026-11-03_1130_A_e2-a39-prereg.md),
[B20](../../archive/sessions/2026-11-03/2026-11-03_1219_B_b20-prereg.md).

- **A39** (from `cot-disclosure/`, after §2's copy-back):
  ```bash
  ../.venv/bin/python finetune/a39.py --report --qset e2            # must say complete; "INCOMPLETE": stop, read nothing
  ../.venv/bin/python finetune/a39.py --report --qset mmlupro_30    # only if the 30 ran
  ../.venv/bin/python tools/export_summaries.py
  ../.venv/bin/python tools/a39_figures.py
  ```
  R1–R4 as written; the no-answer labels of §9. **If E2 is not complete by Nov 15 23:59,** it is read partial by the
  A39 log's §18 (Nov 4): on the questions with every run of all seven systems, labelled "partial: N of 120
  questions".
- **B1R2:** `../.venv/bin/python finetune/gpu/provenance_job.py report --out results/trackA/gpu/b1r2`, then B1's
  rule (`b1_verdict`), paired by question (RUNBOOK §14). Not done by Nov 15 23:59: read on the questions with every
  run of both configurations, labelled "partial: N of 120 questions". None complete: F38 records "not run: no GPU
  time by Nov 15".
- **B20:** Ritik copies back (§2) and tells Arsha when a model is complete. Ritik doesn't read it.

## 4. Apply what is due today

The day's row in §9 says which of these applies.

- **Nov 6, the Nov 6 rule's record** (the A39 log's §16; the feeder decides at its first tick at or after 07:00):
  ```bash
  ssh login.sol.rc.asu.edu 'grep "decision nov6" /scratch/$USER/trackA/feeder.log; cd /scratch/ragarw68/cse598-cot-faithfulness && /scratch/ragarw68/envs/olmo/bin/python cot-disclosure/tools/sol_feeder.py --status | grep "decision nov6"'
  ```
  - The Nov 6 daily records the branch and the number, in the feeder's words.
  - **Cut** (under 10 GPU-hours): A39 on the 30 is recorded "not run: dropped on Nov 6 by §16 (under 10 GPU-hours
    from Nov 4 12:36 to Nov 6 07:00)"; B1R2's lines wait for E2's sweeps and B20's lines. TODO's A39 and B1R2 rows,
    PLAN's calendar and RUNBOOK §0 say so. Cut 3 (B1R2 on fewer parts) is Ritik's: needs Ritik.
  - **No cut:** record it. The 30's Nov 11 rule and B1R2's Nov 15 partial read stand.
  - **"not made yet"** after 07:00 (a failed `sacct` waits a tick): record that, and check again later.
  - Sol needs Duo: the digest mail in Ritik's inbox has it: needs Ritik.
- **Nov 6, Arsha's bundle** (built from Ritik's first message that day; after §2's B20 copy-back):
  ```bash
  cd cot-disclosure
  python3 tools/make_handoff_bundle.py --track B --dry-run      # files and MB; Sol's records with text left out
  python3 tools/make_handoff_bundle.py --track B                # results/handoff/trackB_20261106.tar.gz and its manifest
  python3 tools/make_handoff_bundle.py --verify results/handoff/trackB_20261106.tar.gz   # "bundle matches its manifest"
  cd ..
  ```
  - Then a fresh-clone check of `trackB-main`, as Arsha would run it (`docs/trackB/START_HERE.md` §1).
  - Needs Ritik: upload the bundle to ASU storage and send her note.
  - The handoff's push is the last to `trackB-main` (§6).
- **Nov 7, 12, 15 and 18: merges** (§8). Track C on all four; Track B on Nov 12, 15 and 18.
- **Nov 11, 09:00: the 30's rule** (the A39 log's §10.2). The feeder applies it itself (§17, decision `nov11`).
  - At its first tick at or after 09:00 it checks every E2 and B20 line.
    - Not all finished: the 30's lines still to submit are dropped ("not run: no GPU time by Nov 12").
    - All finished: the 30 runs.
  - Record the branch, as for Nov 6, in the day's log, TODO and PLAN:
    ```bash
    ssh login.sol.rc.asu.edu 'grep "decision nov11" /scratch/ragarw68/trackA/feeder.log'
    ```
    If the 30 was dropped on Nov 6, record "no effect".
- **Nov 15, 23:59:** runs end. B1R2 is read partial if not done (§3). A39 on E2 has no partial rule (§3).
  - Needs Ritik on Nov 16: stop the feeder now or at the freeze.
- **Nov 18: the results freeze.** No new runs after it, on Sol or Voyager.
  - Needs Ritik: stop the feeder (`touch /scratch/$USER/trackA/feeder.stop`, `scrontab -r`) and decide on any pending
    job (`scancel`).
  - Record what didn't run, and why, in FINDINGS, PLAN and TODO.

## 5. Update the docs

- **The session log** (RUNBOOK §20): header (times from `date`, branch, commits, tests, runs in flight), what ran,
  results, files, problems, decisions needed, next commands. Numbers and paths only; under 250 lines.
- **INDEX:** a row in `archive/sessions/INDEX.md`, as the rows above it: the date and time, the log's name linked as
  `<date>/<log>.md`, and what it did.
- **LATEST:** a copy of the newest log, its relative links rewritten for the folder above:
  ```bash
  L=archive/sessions/<date>/<log>.md
  .venv/bin/python - "$L" > archive/sessions/LATEST.md <<'EOF'
  import re, sys, pathlib
  src = pathlib.Path(sys.argv[1]); d = src.parent.name
  def fix(m):
      t = m.group(1)
      if re.match(r"(https?:|mailto:|#|/)", t):
          return m.group(0)
      return "](" + (t[3:] if t.startswith("../") else d + "/" + t) + ")"
  sys.stdout.write(re.sub(r"\]\(([^)\s]+)\)", fix, src.read_text()))
  EOF
  ```
- **The daily:** a section in `DAILY_<date>.md` for this check-in. The first session on a date creates that date's
  daily (`archive/sessions/<date>/DAILY_<date>.md`); the day's last prompt closes it. Carry-over goes in the previous
  day's daily, in its last section, `## For <next date>` (what runs, what waits, the next dates). No file is dated
  ahead of the clock.
- **TODO** (`docs/status/TODO.md`): done items marked done, with the date and the evidence. A dropped item keeps its
  reason. `TODO_B` and `TODO_C` are the owners' and come in by merge.
- **FINDINGS** (`docs/FINDINGS.md`): an F entry for each reading in §3, with its numbers, source and status; the
  merged FB and FC entries; the header's "last updated".
- **The story:** FINDINGS' "The story so far" and the README's "The theme and the story in five lines", when a reading
  or a dropped experiment changes them. PLAN's story, map and calendar only when a date or the map moves.
- **README:** its "Last updated", and the story's five lines.
- **REPORT** (`docs/paper/REPORT.md`): a bullet for each new F entry, as the others: numbers, F number, status,
  limits and a `figure:` line.
- **The plain-words page** (`docs/status/ONE_PAGE.md`, on top of STATUS), if it exists: current.
- **STATUS and the Gantt:**
  ```bash
  .venv/bin/python cot-disclosure/tools/make_gantt.py --dry-run && .venv/bin/python cot-disclosure/tools/make_gantt.py
  ```
  It writes `docs/status/STATUS.md`, `GANTT.xlsx`, `gantt.png` and `gantt.pdf`.

## 6. The checks, then the push

In this order. Each must pass before the next.
```bash
cd cot-disclosure
../.venv/bin/python -m pytest -q                          # every test passes (916 passed, 1 skipped on Nov 4); no network
../.venv/bin/python tools/check_links.py                  # 0 broken links, 0 missing RUNBOOK scripts
../.venv/bin/python tools/make_supplement.py              # regenerates docs/paper/supplement/
../.venv/bin/python tools/make_supplement.py --check      # passes: no row unverified, no log outside the ledger
../.venv/bin/python tools/export_summaries.py --check     # numbers only
../.venv/bin/python tools/make_gantt.py --dry-run         # passes (then without --dry-run, as in §5)
python3 tools/make_handoff_bundle.py --track B --dry-run  # files and MB
python3 tools/make_handoff_bundle.py --track C --dry-run  # 43 files, 31.3 MB until Track C's data changes
cd ..
```
**Commit** the day's work (never `git add -A`; nothing under `results/` but `results/summaries/`):
```bash
git add <the files changed>
git commit -m "<what> (Ritik, $(date '+%b %-d, %H:%M')): <details>"
git log -1 --format='%an <%ae>%n%b'                       # Ritik <his Gmail>; no attribution line
```
**Before the push:**
```bash
python3 cot-disclosure/tools/prepush_check.py --rev HEAD  # nothing produced, GPQA or over 50 MB
git fetch origin
git ls-tree -r --name-only origin/main | while IFS= read -r f; do [ -e "$f" ] || echo "missing: $f"; done
#   nothing missing: prints nothing (a file moved on purpose is in archive/MOVES.md)
```
**The push:**

| when | the line |
|---|---|
| from Nov 4, 22:34 (Ritik: "teammates' branches are theirs") | `git push origin trackA-nosol:main trackA-nosol:trackA-nosol` |
| before that (history) | `HEAD:trackA-nosol HEAD:main HEAD:trackB-main`, and `HEAD:trackC-main` until Nov 4 15:57 |

- RUNBOOK §16: from Nov 3 `trackC-main` is Shrey's, and `trackB-main` is Arsha's (from Nov 4, 22:34, Ritik pushes
  there no more, a day before her handoff; the handoff's own push to `trackB-main` on Nov 6 is the last, with her bundle: Ritik's decision d, Nov 5). Until Nov 4 15:57 the practice still pushed all four branches; `trackC-main` is level with `main` at
  `0570d69`.
- A teammate's branch is pushed to only while `git log --oneline origin/main..origin/<branch>` prints nothing. Never
  force.
- The pre-push hook checks every push.
- Then the pull on Sol, by §1 step 4's rule.

## 7. The report: at most 10 lines

```
Check-in <date> <HH:MM> (log: archive/sessions/<date>/<log>.md)
1. Sol: <last tick; running/pending; GPU-hours in the last 24 h; failures> (or: skipped, Sol needs Duo)
2. Copied back: <what> (or: nothing new)
3. Read: <experiment -> F number> (or: nothing complete)
4. Due today: <what was applied, and its result>
5. Docs: <files>
6. Checks: <N passed, M skipped; 0 broken links; supplement, export, Gantt, bundles, pre-push, nothing missing>; pushed <sha> to <branches>
7. Needs Ritik: <item> (by <date>)
8. Needs Ritik: <item> (by <date>)
9. Next: <date: what is due>
```

## 8. Merging a teammate's branch (Nov 7, 12, 15, 18)

RUNBOOK §16, step by step. Track C (Shrey) on all four days; Track B (Arsha) on Nov 12, 15 and 18. Set the two
variables, then paste the rest.
```bash
B=trackC-main; WHO=Shrey                  # or: B=trackB-main; WHO=Arsha
cd ~/Documents/Projects/ODL/cse598-cot-faithfulness
git checkout trackA-nosol && git status --short                 # must print nothing
git fetch origin
git log --oneline origin/main..origin/$B                        # their commits; nothing printed: nothing to merge, stop
python3 cot-disclosure/tools/path_check.py --range origin/main..origin/$B --branch $B   # must print nothing
git diff --stat origin/main...origin/$B                         # only their paths
git diff --stat origin/main...origin/$B -- docs/trackC/sessions docs/trackB/sessions docs/trackC/FINDINGS_C.md docs/trackB/FINDINGS_B.md
#   read the session logs and FC/FB entries it adds
D=$(date "+%b %-d, %H:%M")
git merge --no-ff origin/$B -m "Merge $B ($WHO, $D): <what came>"
cd cot-disclosure
../.venv/bin/python -m pytest -q                                # all pass, their new tests too
../.venv/bin/python tools/export_summaries.py --check           # numbers only
../.venv/bin/python tools/check_links.py                        # 0 broken
cd ..
.venv/bin/python cot-disclosure/tools/make_gantt.py             # their TODO rows feed STATUS and the Gantt
git add docs/status/STATUS.md docs/status/GANTT.xlsx docs/status/gantt.png docs/status/gantt.pdf
git commit -m "STATUS and the Gantt after the $B merge (Ritik, $(date '+%b %-d, %H:%M'))"
python3 cot-disclosure/tools/prepush_check.py --rev HEAD        # nothing produced, GPQA or over 50 MB
git ls-tree -r --name-only origin/main | while IFS= read -r f; do [ -e "$f" ] || echo "missing: $f"; done   # prints nothing
git push origin trackA-nosol:main trackA-nosol:trackA-nosol
```
- **The hook** passes the merge only if their files come in unchanged. If theirs conflict with Ritik's, take theirs
  and ask them. If the hook refuses a clean merge: `git merge --abort`, then
  `git merge --no-ff --no-commit origin/$B` and `git commit -m "..."`.
- **Sol:** a Track B merge that changes `progress/run_b20.py` (Arsha's, and loaded by B20's jobs) makes §1 step 4
  print it. No pull until B20's queued jobs have started: needs Ritik.
- **Then place their figures** (a commit of Ritik's):
  ```bash
  F=docs/${B%-main}/figures; ls $F 2>/dev/null                  # nothing printed: no figures yet; skip the rest
  mkdir -p docs/paper/figures && cp -v $F/* docs/paper/figures/
  git add docs/paper/figures && git commit -m "$WHO's figures placed (Ritik, $(date '+%b %-d, %H:%M')): <files>"
  git push origin trackA-nosol:main trackA-nosol:trackA-nosol
  ```
- **Then tell them to merge back:** "Merged `<branch>` into `main` (`<sha>`). Please run
  `git fetch origin && git merge origin/main` on your branch, then push it." The hook passes `main`'s files only
  unchanged.
- **Then §5:** their FC/FB entries into FINDINGS, the story, REPORT.

## 9. What is due, Nov 5 to Nov 24

From PLAN's calendar, the TODOs and the logs. "Needs Ritik" goes in the report.

| day | due | the check-in does |
|---|---|---|
| Thu Nov 5 | **B20 moves to Arsha's own Sol account** (the B20 log's §19): Ritik's pull (no B20 line left in his queue); Arsha runs `docs/trackB/SOL_ARSHA.md` herself. A40 pre-registered; its Voyager targets start | §1–§7; push as §6's first row. Needs Ritik: the pull; send Arsha her block |
| Fri Nov 6 | **07:00, the feeder's decision nov6** (the A39 log's §16). **Arsha's handoff:** her bundle `trackB_20261106`, her setup and check-in; Track B is hers from today | record decision nov6 in the Nov 6 daily (§4); build and verify her bundle (§4). Needs Ritik: send the bundle and her note. The handoff's push is the last to `trackB-main` (decision d, Nov 5). **A40:** once its Voyager targets are done (about 9 h from Nov 5 09:50; `logs/guard_a40.log`), `make_bct.py --check-shards`, `--report`, `--assemble`, and the manifest committed with an operational note in A40's log (§11); needs Ritik: the rsync to Sol and `--check-data`, then A40's lines go in his queue after E2's |
| Sat Nov 7 | **Track C check-in and merge** (C19 due). (Corrected Nov 4, 17:54: no L3 settling call or fresh batch; Shrey does no labeling) | §8 for `trackC-main`. Needs Ritik: L3's state for Gate 2 |
| Sun Nov 8 | **Gate 2** (G2): the tool-vs-user gap (answered) and the labels' kappa per channel (Ritik against the AI judges' majority, the LLM-judge protocol) | needs Ritik: Gate 2's statement from L3 |
| Mon Nov 9 | Arsha re-reads B24 from the bundle | — |
| Tue Nov 10 | the report from Nov 10 (PLAN) | — |
| Wed Nov 11 | **09:00, the 30's rule** (the A39 log's §10.2), applied by the feeder (§17): from Nov 5 it checks E2's and A40's lines (§19), unless the 30 was dropped Nov 6 | record its branch (§4) |
| Thu Nov 12 | **check-ins and merges:** Track B (Arsha), Track C (C25, Shrey) | §8 twice |
| Fri Nov 13 | — | §1–§7 |
| Sat Nov 14 | — | §1–§7; if A39 on E2 won't be complete by Nov 15, its §18 partial read applies (§3) |
| Sun Nov 15 | **runs end**; B20's runs by today (Arsha's account); C20 and C26 (Shrey); **check-ins and merges** B and C; **23:59: the partial cut-offs** of A39 on E2 (§18), A40 and B20 (the B20 log's §19) | §8 twice; §3's completeness checks |
| Mon Nov 16 | — (B1R2, revived Nov 6, runs by Nov 15 and is read with the rest) | §3; needs Ritik: stop the feeder now or at the freeze |
| Tue Nov 17 | **A39 read by now** (complete since Nov 7's count; E2 and the 30); **B1R2 read** (complete, or partial at Nov 15 23:59); B20 read by Arsha (complete Nov 6). A40, A41 and A42 were read Nov 7 (F41–F43) | §2 copy-back, §3 |
| Wed Nov 18 | **the results freeze**: no new runs. **Check-ins and merges** B and C; C24 and slides 11–12 (Shrey); B18's table and figure (Arsha) | §8 twice; §4's freeze (needs Ritik: the feeder's stop, any `scancel`) |
| Thu Nov 19 | — | §1–§7 |
| Fri Nov 20 | **Gate 3's final statement** (G3, A17, D6: final verdicts, figures, supplement, STATUS); Arsha's slides 2, 6, 7, 8 final and Track B's report bullets; Track C's bullets (`docs/trackC/REPORT_C.md`) | needs Ritik: Gate 3's statement; a merge to bring in Nov 20's bullets and slides (no merge day is set after Nov 18) |
| Sat Nov 21 | the submission folder (D13) | — |
| Sun Nov 22 | **the report draft** (D7, everyone) | — |
| Mon Nov 23 | **rehearsal** (D8) | — |
| Tue Nov 24 | **final presentation and report** (D9) | — |
