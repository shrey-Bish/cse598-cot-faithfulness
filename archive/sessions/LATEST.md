# Session log: the overnight runs, what may be read now, the report's state (2026-11-07 13:15 MST)

**By:** Ritik. Branch `trackA-nosol`, from `81ab922`. The day's first session, so it opens Nov 7's daily (§0 carries
in Nov 6's "For Nov 7").

## 0. Input

- **Ritik's Sol, Nov 6 at 23:58:** the feeder said "200 lines: 1 failed, 10 not needed, 125 ok, 3 pending, 6 running,
  55 to submit".
- **This morning, sacct since Nov 6 12:00** (its last 25 lines):
  - `trackA-a39-1gpu` 659497, 660008, 660989, 660990, 661201, 664550, 668574 and 669744 COMPLETED (44–55 minutes
    each); none of that job type running or pending;
  - `trackA-a18` 667862 COMPLETED in 0:22:16 (A41's swap?);
  - `trackA-prov-gen` (B1R2): 675320, 675871, 676233, 676234, 676474, 676986, 677532, 678538 and 681191 COMPLETED;
    677995, 680258 and 682548 RUNNING; 683313, 684392 and 685235 PENDING;
  - no failure in the list; the feeder's job 460080 REQUEUED (normal).
- **Ritik sent both messages:** Arsha may read B20 now; Shrey's branch is merged, so he merges back and reinstalls.

## 1. Plan (at most 2 helpers; the full suite once, at the end)

- **Helper A, Sol (read-only; status counts only, no outcome):**
  - the night in full: A40's E2 (16 parts and its sweep), A41 (the swap and Step 10), A42's E2 (16 parts and its
    sweep), B1R2 (parts done and left, its 4 sweeps);
  - any failure or alert, each diagnosed with its fix (commands for Ritik, not run);
  - the projected finish of anything not done (`squeue --start` only);
  - the runs left of A39's seven systems on E2 and the 30, since A40's and A42's comparisons are A39's runs;
  - the Sol clone and the safety diff (no pull by the helper).
- **Me, reading:**
  - from each pre-registration, exactly when A40, A41, A42 and B1R2 may be read;
  - each that is complete and allowed now: the numbers-only copy-back, its reader, its reading by its rules only in its
    own log, with its F-entry, FINDINGS' story, REPORT's bullets and its figure. A40 first, then A41, then A42;
  - each that is complete but whose rule says wait: said plainly, with its date in PLAN's calendar.
- **Me, the report's state:** which REPORT sections are final and which wait (A40–A42, B1R2, B20 with Arsha, C24
  with Shrey), with dates; the team's writing plan for Nov 18–24 as a short table in PLAN (bullets and figures from
  Ritik's side; the team writes the prose).
- **Then:** the stale scan, the records, the full suite once, the push (`trackA-nosol` and `main` only).

## 2. The night on Sol (helper A, read-only, 13:18–13:25; status counts only)

- **The feeder:** last tick 13:15:56; "200 lines: 2 failed, 12 not needed, 162 ok, 4 pending, 3 running, 17 to
  submit". No new alert since `b1r2-06of40` (Nov 6 21:46, known). The digest: 49.2 GPU-hours in 24 h, no tick gaps.
- **A40: complete.** Its 16 E2 parts (643805 … 652218) all COMPLETED, exit 0, in 0:44–1:07 each; the last ended Nov 7
  01:50. The sweep wasn't needed; `--runs-left a39:a40:e2` = 0.
- **A41: complete.**
  - `a41-swap`: 652219, 0:24:43, ended 01:20.
  - `a41-step10`: 652471, exit 2 after 2:55:46. That is the planned stop at its limit, with 50 cuts saved.
  - `a41-step10-again`: 667862, 0:22:16, the last 2 cuts, ended 07:25. Ritik's note this morning read 667862 as the
    swap; it was this again-line.
- **A42: complete.** 16 parts (653898 … 669744), all exit 0, 0:44–0:55 each; the last ended 07:51. The sweep wasn't
  needed; runs left 0. The eight `trackA-a39-1gpu` jobs in Ritik's sacct were A42's parts 9–16.
- **Every A40 and A42 part served its own requests:** 90 or 91 each, on its own port.
- **B1R2: running.**
  - 19 of 40 parts done; 3 running (19, 21, 23); 4 pending (24–27); 13 to submit; the 4 sweeps wait.
  - 556 of 1,200 runs left (by sweep: 135, 126, 143, 152).
  - Parts 14 and 20 left 3 runs "not_run: static engine: out of memory alone" (alpha 0.25), which the sweeps retry.
    They may run out of memory again.
- **No new failure.** `a41-step10`'s exit 2 is by design (A41's §5).
- **The Sol clone:** at `81ab922`, clean; the safety diff printed nothing. No pull was needed.
- **The finding:** Sol's `--runs-left` said A39's E2 had 54 runs left. Every one has an ok record (§4).

## 3. When each may be read, from its pre-registration

| experiment | its rule | complete? | so |
|---|---|---|---|
| **A40** | §10: partial only if not complete by Nov 15 23:59; no earlier date | yes (1,440 of 1,440, and its comparisons') | **read now** (13:29) |
| **A41** | §6: "Read when both jobs have ended" | yes (07:25) | **read now** (13:31) |
| **A42** | §5: partial only if not complete by Nov 15 23:59; no earlier date | yes | **read now** (13:31) |
| **B1R2** | the A39 log's §13.7–§13.8: when its sweeps leave 0 runs, or partial at Nov 15 23:59 | no (19 of 40 parts) | **wait**: when complete (projected Nov 8), by Nov 17 |
| A39 (A40's comparisons) | its §18: partial only at Nov 15 23:59; no earlier date | yes (counted 13:28) | may be read; Ritik picks the day, by Nov 17 |

- PLAN's "read Nov 17" for A40 and A42 was the planned deadline, not a rule; B20's reading was settled the same way on
  Nov 6.
- PLAN's calendar now carries B1R2's and A39's dates.

**The readings** (each in its own log, by its rules only):
- **A40** ([13:29](2026-11-07/2026-11-07_1329_A_a40-reading.md)): **"fewer, but costs acceptance"** against the instruction
  (following −21 [−26, −16]; acceptance −15 [−20, −10]) and against LoRA; R1 passes. **It doesn't beat the
  instruction.**
- **A41** ([13:31](2026-11-07/2026-11-07_1331_A_a41-reading.md)): **"stops the readout", "before them"** (R_A40 +0.68 [+0.17,
  +1.18]; layers 0–14 carry 1.89 [1.39, 4.82] of it); **"A40 removes more of the hint's pull than LoRA"** (+1.40
  [+0.73, +2.09]).
- **A42** ([13:31](2026-11-07/2026-11-07_1331_A_a42-reading.md)): **"fewer, but costs acceptance"** (following −24 [−30, −19];
  acceptance −20 [−26, −14]); R3 **"adds, costs acceptance"**; R1 passes.
- **Recorded:**
  - F41–F43 and FINDINGS' story;
  - REPORT §7's bullets, in place of A40's waiting entry;
  - `results_at_a_glance`, FIX_SO_FAR and the supplement's rows;
  - the summaries exported.
- **Figures:** by helper B (§5).

## 4. The counting bug (`f42523e`)

- **The cause:**
  - `eval.runs_files` lists the whole-system file first, then the parts by name;
  - the resume, the feeder's `--runs-left`, `plan_eval` and B1R2's report took each run's last record of any status;
  - so an older `not_run` in a file listed later hid an `ok`.
- **What it did:**
  - E2's sweeps re-ran 33 runs that already had an ok record (base 26, lora 6, prompt_only 1);
  - Sol showed 54 runs left on a complete A39;
  - B1R2's report could have dropped finished runs once its sweeps of 4 (which sort before parts 5, 9, 21, … of 40)
    write.
- **The readers were never affected** (`a39.py`, `a40.py`, `a42.py`: any ok record counts, each run's last ok kept).
- **The fix, tests first:**
  - two tests, RED (90 runs left where 87 are; `ok_rows` missing), then GREEN;
  - `eval.done_ids` and `provenance_job.ok_rows`, and Gate 3's `rows_of` the same;
  - on B1's and Gate 3's saved runs, 0 of 824 and 0 of 5,580 runs change, so F38 and F28 stand;
  - the targeted suites: 321 passed.
- **Recorded:** the A39 log's §22 (operational, no rule changes).
- **Sol:** the pull waits until every B1R2 part has started, since `finetune/` is on the safety diff's list. Until
  then, at worst a sweep re-runs a run that is already done.

## 5. The figures (helper B; checked by eye before committing, `1898709`)

- **`docs/paper/figures/a40_e2_fixes.png`** (new, `tools/a40_figures.py`, 9 tests, RED then GREEN):
  - A40 against the instruction, LoRA and base; A40 + note against the instruction, A40 (R3) and base;
  - following, acceptance and no-hint accuracy, each reading under its row;
  - drawn only from the numbers-only reports; an incomplete report is refused unless `--draft`;
  - A42's `vs_a40` reading, which `a42.py` marks "(no decision)", isn't drawn.
- **Slide 10, `readout_lora_vs_base.png`:** A40's bars (A41) sit beside LoRA's, as A41's §6 said.
  - 1 test, RED then GREEN. Without A41's file the figure is byte-identical to before.
  - The headline: line 1 is F39's; line 2 is A41's reading. B1's readings stay in panel (b)'s title.
  - A small blemish, left: the "+0.02" label touches the 0–23 whisker.
- **Helper B's calls, accepted:**
  - A40 is drawn in the "private" blue, no new color (validator: worst CVD ΔE 10.2);
  - A40 − LoRA (+1.40) goes in the note and the CSV, not as a dot;
  - R3's "minus the instruction" row repeats A42's primary, with R3's reading once.

## 6. Shrey's C24, merged (`0c7a26f`), and Track C's files placed (`1a5002d`)

- **`trackC-main` at `50f041c`:** one commit by Shrey Bishnoi (author and committer).
  - No AI attribution line; the path check is clean; Track C paths only.
  - Shrey had merged `origin/main` back and reinstalled the hooks first (the 09:15 log).
- **C24:** `agents/trackc_tables.py` writes three tables into `docs/trackC/tables/`: `trackC_experiments` (71
  comparisons), `trackC_pipelines` (C20's four pipelines) and `at_a_glance_FC`. 4 new tests pass.
- **Placed, copied unchanged** (CHECKIN §8):
  - Shrey's three figures (`c19_authority`, `c25_hops`, `pipeline_vs_model`) into `docs/paper/figures/`;
  - the two tables into `docs/paper/tables/`;
  - FC1–FC4 into `results_at_a_glance` (md and CSV), verbatim from Shrey's generated rows.
- **Shrey's next step:** merge `origin/main` back again (the message in §8).

## 7. The report's state, and the writing plan (PLAN, "The report's state")

- **Final** (every number read): §5, §6 (L3 read Nov 4: not met), §8, §9. §7 is final for F20, F27, F28, F38, F39 and
  F41–F43.
- **Waiting:**
  - §1's contributions line on A39 (Ritik, by Nov 17);
  - §2–§4 on B20 (Arsha reads it now; Track B's bullets Nov 20; B18's table and slide 7's B24 arms Nov 18);
  - §7 on A39 and B1R2 (by Nov 17) and Gate 3's final statement (Nov 20);
  - §10–§12 on the freeze (Nov 18).
- **The writing plan, Nov 18–24:** a table in PLAN.
  - Each section's prose is by its owner, as REPORT's headings and the submission checklist already name them:
    - Ritik: §1–§3, §5, §7, and §6 with Arsha;
    - Arsha: §4;
    - Shrey: §8–§9;
    - everyone: §10–§12, merged by Ritik (proposed).
  - The prose is written from REPORT's bullets and figures.
  - Prose drafts by Nov 21 (proposed), the draft Nov 22, the rehearsal Nov 23, final Nov 24.
- **Stale lines fixed:**
  - REPORT §6's L3 entry (read Nov 4) and §7's waiting list;
  - CLAIMS 1.5 and 1.7, README's fix paragraph, F38's B1R2 note, TRACK_A_FIX, PLAN's L3 and B1R2 rows;
  - ONE_PAGE rewritten; CHECKIN's completeness checks.
  - Left: Track B's and Track C's START_HERE still say B1R2 was dropped (their owners' paths).

## 8. Messages, and Sol

**To Shrey:** "C24 is merged into `main` (`0c7a26f`). Your three figures and two tables are placed in `docs/paper/`,
and FC1–FC4 are in `results_at_a_glance` as you generated them. Please run `git fetch origin && git merge origin/main`
on `trackC-main`, then push it. Nothing else is due from Track C before the Nov 18 freeze; check-ins Nov 12, 15, 18."

**Arsha:** nothing new. B20's word was sent this morning.

**Sol: no block is needed today.** The clone is current (`81ab922`) and every job runs. Today's commits change
`finetune/eval.py` and `finetune/gpu/provenance_job.py`, which B1R2's parts load. So the safety diff will print them,
and the pull waits until every B1R2 part has started (projected Nov 8, early). **Nov 8's block** (after
`ssh -O check` says "Master running"):
```bash
ssh login.sol.rc.asu.edu 'bash -s' <<'EOS'
cd /scratch/ragarw68/cse598-cot-faithfulness; P=/scratch/ragarw68/envs/olmo/bin/python; F=cot-disclosure/tools/sol_feeder.py
$P $F --status | head -6                      # B1R2: no line "to submit" left among b1r2-01of40 … b1r2-40of40
squeue -u $USER -n trackA-prov-gen -h -t PD | wc -l   # 0: no B1R2 part waiting
git status --short && git fetch -q origin     # status prints nothing
git diff --stat HEAD..@{u} -- cot-disclosure/finetune cot-disclosure/progress/common.py   # lists eval.py, provenance_job.py, plan_eval.py: expected, now safe
git pull --ff-only && git log --oneline -1   # today's last commit
for k in 1 2 3 4; do $P $F --runs-left b1r2:$k/4; done   # now counted by the fix
EOS
```
Optional, Ritik's call: drop `reserve=240:2` from B1R2's lines (a queue-file edit). It now only paces B1R2.

## 9. Needs Ritik

- **Now:** send Shrey §8's message.
- **Any day, by Nov 17: read A39** (complete).
  - From `cot-disclosure/`: `a39.py --report --qset e2`, then `--qset mmlupro_30`, `export_summaries.py` and
    `a39_figures.py` (CHECKIN §3). The runs files are already copied back.
  - Its rules R1–R4 haven't been run.
- **Nov 8:** mark Gate 2 (PLAN's statement, ONE_PAGE, TODO's G2).
- **Nov 8, once every B1R2 part has started:** §8's Sol block (the pull).
- **Optional:** drop B1R2's `reserve=240:2`.
- **Nov 18 check-in:** confirm the writing plan's proposed dates (PLAN).
