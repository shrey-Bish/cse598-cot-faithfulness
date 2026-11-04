# Session log: Track C's final handoff, the Sol re-plan with the bench's numbers, Arsha's workspace, the clean-up (2026-11-03 22:16 MST)

By: Ritik. Ritik's message of about 22:16, four parts and 13 items.

**The safety rule for Sol, kept throughout:** A39's 9 queued jobs start from Nov 4 19:25 and load code from Sol's clone
when they start. Nothing they load was changed.

**The files they load,** found by importing the job's modules (`finetune/gpu/eval_job.py`, `finetune/eval.py` and their
lazy imports, and `vllm_options.job_commands`, which every vLLM job's preflight calls):
- `finetune/` (eval, generate, continuation, olmo_format, hf_engine, make_targets, provenance, build_dataset,
  source_tags, tags_vllm, train, run_nohint, base_format, gpu/);
- `progress/common.py`, `progress/mmlu_pro_probe.py`, `progress/sol_trackB.py`, `progress/sol_b17.py`;
- `agents/__init__.py`, `agents/sol_c13.py`;
- `client.py`, `parse.py`, `detect.py`, `experiments.py`, `tasks.py`, `tools/answer_key.py`, `providers/`;
- the Sol kit's `run.sh`, `env.sh`, `guard.sh` and `accounts.conf`;
- B20's `sol_b20.py` and `run_b20.py`.

**Against Sol's commit (`14105b7`):** the only one of these that differs is `accounts.conf`, whose htc row comes out.
The job's guard reads only its account names, and they are the same (`class_cse59888883fall2026`). `submit.sh` isn't
loaded by a job.

## Plans for the structural changes (written before each)

- **The path guard both ways:**
  - one allowlist file (`configs/path_allowlist.txt`), two directions:
    - forward: a listed branch touches only its paths;
    - reverse: other branches change a listed branch's paths only by merging that branch, unchanged.
  - "!" exclusions keep the files Sol's jobs import with Ritik.
  - Installed as the pre-commit and pre-merge-commit hooks, because a clean merge runs only the latter.
  - No code folder moves.
- **Track B's list:** her docs, results, tests, runners, report and table; not the Sol job code.
- **The clean-up:** docs and tests only. The superseded bundles and a stray diff move to `results/archive/`
  (gitignored); nothing is deleted except the pytest cache.

## Part 1. Sol

**1. The bench (389340).**
- **The numbers:** COMPLETED in 0:54:49 (limit 1:00). vLLM's log averages 393–401 tokens/s, with about 20 requests
  running and the KV cache 98–99% full, so more requests in flight won't help. 36 runs were saved.
- **A39 at 400 tokens/s:** E2 is **53.2 GPU-hours** of generation (was 42.6 at 500); the 30 is 13.3.
  - A core quarter-part is 3.85 M tokens: 2.67 hours, plus about 10 minutes of start, plus the last long runs. That
    is against about 2.9 hours before Slurm's stop warning.
  - So **the 9 queued parts (3:00) will mostly stop just short.** Each core system's leftovers then run in one sweep
    job (the system with no part) after its 4 parts end.
  - The parts not yet submitted get longer limits: the core systems' 3:30 (`--estimate 2.6`) and the wrapper systems'
    halves 3:00 (`--estimate 2.1`). These are the A39 log's §11, committed at 22:30, before any production part
    starts.
- **The bench's runs count once.** Run ids carry no part. Resume reads every part file of a system, so base's 2/4 and
  4/4 skip the bench's finished runs. The readings keep the last record per run. Pinned by
  `test_the_bench_s_runs_count_once_beside_the_production_parts`.

**2. The calendar to Nov 15**, from `squeue --start`, in PLAN's calendar:
- **The 9 queued parts:** 19:25 Nov 4; 00:55 and 01:20 Nov 5; then 11:30–12:40.
  - The scheduler's forecast ignores the two-job limit. With two slots and each job taken to its 3:00, the last ends
    about Nov 5 21:00.
- **Wave 2** (below) from about Nov 5 evening.
- **E2 and B20 done:** projected Nov 7–8.
- **The 30:** after them; dropped if E2 and B20 aren't done by Nov 11 09:00.
- **B1R2:** decided Nov 8 09:00 by its rule (R4).
- **Runs end** Nov 15; A39 and B20 are read Nov 17; the freeze is Nov 18.

**Wave 2, in order** (one free place now: 9 queued, the downloads are done). Submit the next line as a place frees. No
`--htc`.

```bash
S=cot-disclosure/finetune/gpu/sol/submit.sh
# B20's smokes, smallest first (estimate 1 h, limit 1:30; Granite's plugin is in its snapshot)
$S b20 --model granite-4.2-8b -- --smoke                 # 1 (can go now: the 10th place)
$S b20 --model gemma-4-26b-a4b-it -- --smoke             # 2
$S b20 --model nemotron-3-nano-30b-a3b -- --smoke        # 3
# the rest of the core systems, round-robin (limit 3:30)
$S a39_1gpu --estimate 2.6 -- prompt_only e2 3/4         # 4
$S a39_1gpu --estimate 2.6 -- lora e2 3/4                # 5
$S a39_1gpu --estimate 2.6 -- lora_note e2 3/4           # 6
$S a39_1gpu --estimate 2.6 -- base e2 4/4                # 7 (skips the bench's finished runs)
$S a39_1gpu --estimate 2.6 -- prompt_only e2 4/4         # 8
$S a39_1gpu --estimate 2.6 -- lora e2 4/4                # 9
$S a39_1gpu --estimate 2.6 -- lora_note e2 4/4           # 10
# the wrapper systems, halves (limit 3:00)
$S a39_1gpu --estimate 2.1 -- wrap e2 1/2                # 11
$S a39_1gpu --estimate 2.1 -- wrap_note e2 1/2           # 12
$S a39_1gpu --estimate 2.1 -- lora_wrap e2 1/2           # 13
$S a39_1gpu --estimate 2.1 -- wrap e2 2/2                # 14
$S a39_1gpu --estimate 2.1 -- wrap_note e2 2/2           # 15
$S a39_1gpu --estimate 2.1 -- lora_wrap e2 2/2           # 16
# B20's runs, each after its clean smoke (limit 4:00; the same line again with afterany if runs are left)
$S b20 --model granite-4.2-8b --estimate 3 --dependency=afterok:<job of line 1>               # 17
$S b20 --model gemma-4-26b-a4b-it --estimate 3 --dependency=afterok:<job of line 2>           # 18
$S b20 --model nemotron-3-nano-30b-a3b --estimate 3 --dependency=afterok:<job of line 3>      # 19
# a sweep per core system, after its 4 parts end (the system with no part: only what's left; limit 1:30)
$S a39_1gpu --estimate 1 --dependency=afterany:426582:428297:428332:<line 7> -- base e2            # 20
$S a39_1gpu --estimate 1 --dependency=afterany:428294:428298:<line 4>:<line 8> -- prompt_only e2   # 21
$S a39_1gpu --estimate 1 --dependency=afterany:428295:428299:<line 5>:<line 9> -- lora e2          # 22
$S a39_1gpu --estimate 1 --dependency=afterany:428296:428330:<line 6>:<line 10> -- lora_note e2    # 23
```

- **A smoke or part that has already ended** can't be named in `--dependency`: drop it from the list. Only running or
  pending jobs pass `submit.sh`'s check.
- **A wrapper half that stops short** gets the same line again.
- **Wave 3** is A39 on the 30, 7 jobs, only by §10's rule:
  - `$S a39_1gpu --estimate 2.6 -- <core system> mmlupro_30` (limit 3:30);
  - `$S a39_1gpu --estimate 1 -- <wrapper system> mmlupro_30` (1:30).

**3. htc is closed to the class QoS** (AllowQos=public,debug; `--test-only` rerouted the job to public). The removal:
- `accounts.conf` lists no htc row;
- `submit.sh` refuses `--htc` before sbatch, and its `--test-only` code is gone;
- RUNBOOK §0, SOL_SETUP, the TODO rows, PLAN's risks and the A39 log's §11 say so;
- tested by `test_htc_is_refused_and_not_listed` and `test_only_listed_accounts` (one row), both failing first.

## Part 2. Track C's final handoff

**4. A fresh-clone check of `trackC-main`,** as Shrey would run it: after this session's commit, see Checks.
- **The bundle is still current:** all 43 files of `trackC_20261103` match their manifest's sha256, and there are no
  new Track C files. It isn't rebuilt.

**5. The run guard on any machine** (`progress/guard.py`, which no Sol job imports):
- **Off macOS** (no `pmset`), it skips the battery and sleep checks, says so once at the start, and treats every job as
  on the charger.
- **On a Mac,** it reads `pmset` as before.
- **The same everywhere:** the stop files, the Voyager halt (code 3), AFTER and the 4-in-flight slots.
- **Native Windows Python isn't supported:** `progress/common.py`, which A39 imports, uses POSIX locks. So WSL.
- **Tests:** 3 new (Linux skips, macOS reads, and off macOS the stop file and the halt still work), failing first.
- START_HERE §5 and the Quick start say this.

**6–7. START_HERE**:
- **A one-page Quick start on top:**
  - what Track C is, and what's done;
  - his five next steps with dates (setup Nov 4; labels by Nov 7; C19 Nov 7; C25 Nov 12; C20 and C26 Nov 15);
  - then C24 and slides 11–12 by Nov 18, and the report bullets (`docs/trackC/REPORT_C.md`) by Nov 20;
  - check-ins Nov 7, 12, 15 and 18; where to ask.
- **Below it:**
  - the hooks by `--install`;
  - the two Sol exclusions;
  - the guard off macOS;
  - the merges on the check-in days;
  - the calendar rewritten.
- **TODO_C:**
  - C24 due Nov 18;
  - new rows: C27 (slides 11–12, Nov 18), C28 (the report bullets, Nov 20), C29 (the check-ins and merges);
  - an "Edited by" line.

**8. Merging both ways:**
- **`tools/path_check.py`:**
  - "!" exclusions;
  - the reverse rule: on Ritik's branches, a path a teammate's branch owns changes only by a merge from that branch,
    taken unchanged (MERGE_HEAD, or the GITHEAD_<sha> variable git sets during a clean merge's pre-merge-commit hook);
  - `PATH_CHECK_ALLOW=<owner>` for an agreed change, which passes with a warning;
  - `--install`, which writes both hooks and leaves someone else's hook alone.
- **Tests:** 6 new (exclusions; the reverse refusal; a merge from the owner, an edit during it, and a merge from
  another branch; the override; the hooks run by real `git commit` and `git merge`; the real list), failing first.
  13 in all.
- **The real list:**
  - **Track C:** `agents/` except `__init__.py` and `sol_c13.py`;
  - **Track B:** its docs, results, tests, `run_trackB.py`, `run_b15`–`run_b20.py`, `trackB_report.py`,
    `trackb_final.py` and its table.
  - Neither may touch the Sol job code or shared modules (tested against the frozen list).
- **RUNBOOK §16:** the merge steps for Ritik (the checks, `--no-ff` merge, tests, export check, Gantt, push; placing
  their figures; them merging back; the files Sol jobs load).
- **The hooks** are installed in Ritik's clone after this session's commit (Checks).

**9. His labeling duty, separate from Track C:**
- the L3 settling call on `results/labels/L3_settle.csv` (23 rows, 25 disagreements), then the 72-row fresh batch;
- both by Nov 7, for Gate 2 on Nov 8;
- in his Quick start, TODO's L3 row and RATER_GUIDE.

**10. The message for Ritik to send Shrey** (with `trackC_20261103.tar.gz` through ASU storage):

> Hi Shrey, here's the final Track C handoff. Your branch is `trackC-main`. Start with the Quick start at the top of
> `docs/trackC/START_HERE.md`; it's one page, and the detail is below it. The data bundle `trackC_20261103.tar.gz` is
> in our ASU folder: unpack it into `cot-disclosure/` and run `--verify` (§4). Install the hooks once:
> `python3 cot-disclosure/tools/path_check.py --install`, plus the pre-push line in §4. Your first two tasks: (1) setup,
> the tests and the three no-call reproductions by Wed Nov 4; (2) C19 by Sat Nov 7. Separately, the labels: our L3
> settling call (`L3_settle.csv`, 25 disagreements; when suits you?) and then the 72-row fresh batch, both by Nov 7
> for Gate 2. Check-ins: Nov 7, 12, 15 and 18, when I merge `trackC-main` into `main`. The guard now works on Linux
> and WSL as well as a Mac.

## Part 3. Arsha (11)

- **`docs/trackB/START_HERE.md`** is written, in Track C's shape:
  - a one-page Quick start;
  - setup (Nov 6), and her paths with the hooks both ways;
  - the plan to the freeze: B18's table and figure by Nov 18, B20's reading by Nov 17, slides 2, 6, 7 and 8 by
    Nov 20, the report bullets by Nov 20;
  - check-ins Nov 6, 12, 15 and 18 (merges on the last three);
  - B20's reading, the slides, the rules, the hand-back, a brief, contacts.
- **TRACK_B.md** points to it.
- **Her allowlist** is in the file, and the hooks are the same tool.
- **Her bundle** is rebuilt on Nov 6 morning, with a fresh-clone check: that is the first message that day.

## Part 4. The clean-up (12): every fix

- **Stale statements** (found by a read-only audit, each checked against the file before it was changed):
  1. FINDINGS: the Track C list (F18, F19, F21–F24, F30, F31, F33, F34: F20 and F32 are Track A's); A39 and B1R2 as
     "Next" in story item 5; "keyword counts until the hand labels exist" → where the labels stand; the header.
  2. FINDINGS_C: the same Track C list.
  3. README: B1R's wording (the 70-question replication couldn't settle it); B1R2 decided Nov 8.
  4. CLAIMS: A18 in claim 1.5; "settles it" → L4 part 2 and A39 on E2; B1R2 conditional in 1.7; the header.
  5. OUTLINE: results through F39; L3's state; the cautionary claim as read; the slide figures listed.
  6. REVIEWER_QUESTIONS: B1's blanks filled from F38 (questions 3–4); B2 dropped (6); L4 part 1's reading (7);
     Qwen3-8B and five models (8); L3's state (9).
  7. WAITING: slide 10's owner line ("made Nov 3").
  8. PLAN:
     - the header;
     - Track C's final handoff and check-ins; Track B's check-ins;
     - the Sol order with the bench's numbers;
     - the map (A39, B20, C24/C27/C28);
     - the calendar (Nov 3 to Nov 24, from `squeue --start`);
     - the budget (no paid calls; closed models dropped);
     - the risks (Sol busy, htc closed; the guard both ways).
  9. RUNBOOK:
     - §0 (the bench, the queued parts, htc refused, pulling on Sol while jobs are queued);
     - §14's A18 line (read, F39);
     - §16 (the push, the guard both ways, the merge steps, the files Sol jobs load).
  10. SOL_SETUP: the date; htc refused.
  11. TODO:
      - A39 (the bench done; 9 parts queued; ~58 GPU-hours; blocked by nothing);
      - R3 (htc checked; the bench done);
      - G3 (A18 read);
      - H3 (the final handoff Nov 3);
      - L3 (both by Nov 7);
      - D14 and R4 as before.
  12. TODO_B: B18 and B20 reworded so the Gantt doesn't read "Gate 2" or "from Nov 6" as their due dates (B18 Nov 18,
      B20 Nov 15 now); B20 blocked by A39's first wave.
  13. TODO_C: as in Part 2.
  14. TRACK_B: points to START_HERE; F37 in the reading list; B20's status.
  15. RATER_GUIDE: the L3 deadlines (Nov 7).
  16. `cot-disclosure/README.md`:
      - B19, B20 and their entry points;
      - `a39.py`, `make_e2.py`;
      - the path check both ways and the two teams' lists;
      - `results/` (the progress round's tracked runs).
  17. `finetune/gpu/README.md`: a pointer to the job kinds and rules since Oct 31.
- **The README's map and "Read this first":**
  - the Quick starts;
  - REPORT for a grader;
  - what's generated, by which script;
  - trackB/ and trackC/ with figures/;
  - `results/` (tracked evidence, the archive);
  - LATEST as a copy;
  - superseded's contents;
  - the generated files that stay beside their code (canaries, the Sol inputs manifest, the progress round's figures).
- **"Edited by" headers:**
  - added: RUNBOOK, RELATED_WORK, REPORT, WAITING, RATER_GUIDE, LABELING_GUIDE, the code map, the sessions INDEX, TODO,
    TRACK_C, and the PLAN, FINDINGS, CLAIMS, OUTLINE, REVIEWER_QUESTIONS, SOL_SETUP, TRACK_B and gpu README headers;
  - already there: TODO_B, TODO_C, FINDINGS_B/C, TRACK_A, TRACK_A_FIX.
- **AI tools named:** two tests named a product to forbid it in generated files. They now check the generic markers
  instead (co-author trailers, "generated with", bot e-mail addresses).
  - Kept, as study subjects or provider code: the closed-model names (dropped B22, the providers, prices) and the cited
    paper's "Claude 1.0".
  - Commit history is unchanged.
- **Leftovers:**
  - `results/sol_tree_vs_a752db5.diff` moved to `results/archive/`;
  - the superseded bundles `trackC_20261030` and `trackB_20261101` moved from `results/handoff/` to
    `results/archive/handoff/` (all gitignored);
  - `.pytest_cache` removed (a cache).
  - There are no worktrees besides the main one, and no temporary files in the tree.

## Judgment calls (each with its cost if wrong)

1. **Sweeps per system instead of a resume per part.** One job finishes a system's leftovers after its parts end.
   - Cost: none for the runs (resume by run id); one wait instead of four.
2. **Longer limits only for the parts not yet submitted.** The queued 9 keep their 3:00 and their queue position.
   - Cost: their leftovers wait for the sweep.
3. **`agents/__init__.py`, `agents/sol_c13.py` and the Sol job code are excluded from the teammates' lists,** because
   every vLLM job imports them.
   - Cost: Shrey asks Ritik for a change to C13's code, which is done.
4. **Arsha gets `run_b20.py`, which B20's Sol jobs import,** with a rule in her START_HERE (only its report functions
   until Nov 15) and a merge-time check.
   - Cost: a merge Ritik must check before pulling on Sol.
5. **`PATH_CHECK_ALLOW`, a documented override** for a change the owner agreed to (this handoff, Arsha's files until
   Nov 6).
   - Cost: none; `--no-verify` exists anyway, and this one warns.
6. **The pre-merge-commit hook detects the merged commit from git's GITHEAD_<sha> variable.**
   - Cost if a git version lacks it: the hook refuses a clean merge, and `git merge --no-commit` then `git commit`
     (MERGE_HEAD) passes.
7. **Arsha's slides 2, 6, 7 and 8:** she draws a changed design under `docs/trackB/figures/` and Ritik places it; the
   numbers-only reruns stay with `tools/slide_figures.py`.
8. **The audit's note on Shrey's calendar** (labels by Nov 6 and Nov 8) was overridden by Ritik's Nov 7.

## What waits for Ritik

- Send Shrey the message (§10) and the bundle.
- On Sol:
  - Optional: a pull is safe (the check is at the top of this log).
  - Wave 2 as places free; the Granite smoke can go now.
  - `squeue --start -u $USER` after each wave.
- Nov 6 morning: Arsha's bundle and her note.
- Nov 7: the L3 call with Shrey; the first check-in and merge.
- Nov 8 09:00: R4's `sacct` line (B1R2).
- Nov 11 09:00: the 30's rule.

## Checks

- **Tests:** 823 passed, 1 skipped (the full suite, CPU only).
  - New or changed, each failing first: path check 13, guard 9, the GPU kit (htc refused, one account row), A39's
    bench-counted-once.
  - The two tests that named a product now check generic markers.
- **`check_links`:** 0 broken links, 0 missing RUNBOOK scripts.
- **The Gantt:** `make_gantt.py --dry-run` ok, then regenerated. Due dates: A39 Nov 15, B1R2 Nov 15, B18 Nov 18, B20
  Nov 15, C27 Nov 18, R4 Nov 8.
- **The bundles' dry runs:** Track C has 43 files, 31.3 MB (unchanged); Track B has 33 files, 62.5 MB (rebuilt Nov 6).
- **`export_summaries.py --check`:** all numbers-only.
- **Nothing missing** (a scratch script; every file tracked at `14105b7` still tracked, and every file deleted since
  Oct 30 found through MOVES.md's chains): 709 of 709 at their path; 146 of 146 moved; 0 missing.
- **The Sol-safety diff:** among the 49 files the queued jobs load, only `accounts.conf` differs from `14105b7` (its
  htc row out); the account list is the same.
- The supplement check, the pre-push check, the fresh-clone check and the hooks' install: in the commit messages
  that follow and the final message.
