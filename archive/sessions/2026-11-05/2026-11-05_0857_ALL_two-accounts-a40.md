# Session log: B20 to Arsha's account, B20's job size, B1R2 dropped, A40 (the fix), Arsha's Sol setup (2026-11-05 08:57 MST)

**By:** Ritik. Branch `trackA-nosol`, from `307367f`. Plan written at 08:57, before any helper started.

## 0. Inputs

- **Ritik's email:** job 510702 (`trackB-b20`, `b20-nemotron-r2-1`, the old code) ended FAILED at Nov 4 23:41:34.
- **His read-only Sol outputs** (pasted at about 08:43; the feeder's last tick 08:40:38):
  - **510702's server started at 2026-11-05T05:18:23Z** (22:18:23 MST), before Gemma's runner ended at 05:23:59Z.
  - `sacct`: 510702 FAILED, exit 2:0, end 23:41:34. No `trackB-b20` job in `squeue`.
  - **Granite's two files:** 129 runs and 129 records, read without an error.
  - **Runs left** (`run_b20.py --dry-run`): Granite 849, Gemma 1,784, **Nemotron 0**.
  - The feeder's log: `b20-nemotron-r2-8` to `r2-12` "not needed" at 00:30:44 (the runs before them were done).
  - `--status`: 220 lines: 5 failed, 10 not needed, 76 ok, 8 pending, 40 skipped, 1 timeout, 80 to submit.
    Decisions nov6 and nov11 not made yet.
  - `sshare`, the course account: his FairShare **0.001884** (NormUsage 0.001042 of the account's 0.001245). Most
    users listed have no usage and 0.868.
  - `/scratch/ragarw68`, its `envs` and `hf`: `drwxr-x---`, group `class_cse598fall2026`.
- **His decisions** (in this prompt):
  - a. Keep all three B20 models.
  - b. B20's job size, an operational amendment, committed before these lines run:
    - 3:00 limits for every B20 line not yet submitted;
    - enough lines per model to finish its runs left at its measured rate;
    - each model's remaining runs ordered question by question.
  - c. B20's partial-read rule, as A39's §18, committed now before any B20 result is read.
  - d. Arsha: one last push to `trackB-main` on Nov 6, with her bundle; after that it's hers.
  - e. Re-look rows 67 and 290: kept as recorded.
  - f. B1R2 dropped (an amendment for compute, before any B1R2 run). It is reported "not run: GPU time given to A40",
    and its feeder lines are dropped.
  - g. A40: a new fine-tune aimed at beating the instruction. It goes in his feeder's order after A39's E2 core
    parts.
  - h. From Nov 5, Arsha runs B20 on her own Sol account, typing every command herself in her own login. No
    credentials are shared.
    - His account runs A39 and A40. Hers runs all of B20, on her own feeder.
    - No line is ever submitted from both accounts.
  - i. Voyager at the weekend runs on teammates' own machines with their own keys. Shrey does Track C only. Arsha may
    run a shard of A40's target generation; shards are merged and checked on Ritik's Mac.
- **Sol needs Duo this morning** (08:57: no open connection). So every Sol step is skipped. This session works from
  his outputs, and every Sol command goes to the handoff.

## 1. The plan

Helpers don't commit. I check each one's work against the rules, then commit in small commits.

| helper | task | the files it alone owns | waits for |
|---|---|---|---|
| **A: B20 and the queues** | <ul><li>Confirm the cause from Ritik's outputs, and that Granite's saved files are intact.</li><li>Write b and c as the B20 log's §19, and f as the A39 log's §19, with what B20's move does to the feeder's nov11 rule.</li><li>Order B20's remaining runs question by question.</li><li>Split the queue by account:<ul><li>B20's lines leave Ritik's queue file for a new B20-only file for Arsha's feeder, with 3:00 lines, enough per model, and consistent chains;</li><li>B1R2's lines are dropped;</li><li>the feeder refuses a queue that belongs to the other account.</li></ul></li><li>Tests, failing first.</li></ul> | `progress/run_b20.py`, `progress/sol_b20.py`, `tools/sol_feeder.py`, both queue files, `tests/test_sol_feeder.py`, `tests/test_trackB_b20.py`, the two logs' new §19 | nothing |
| **B: A39's outlook** | From the feeder's numbers: E2's outlook by Nov 15 (B20 now off Ritik's account), and the Nov 6 rule's likely branch. | (none: §2 of this log) | nothing. **Done by me:** it is a few lines from the counts above. |
| **D1: the fix so far** | One page in plain words, for Ritik: what each trained version did (LoRA, tags, LoRA + tags, LoRA on layers 15/19/23) on following, acceptance, accuracy and hiding, against base and against prompt_only; why they matched the instruction instead of beating it (A18, F39); and what A39 will settle. | `docs/status/FIX_SO_FAR.md` (new) | nothing |
| **D2: A40** | <ul><li>Read Chua et al. (2024), bias-augmented consistency training, first.</li><li>Design A40 on Track A's training pool, with Olmo 3 7B Think's own no-hint reasoning and answer as targets, generated on Voyager.</li><li>Draft its pre-registration (its rule on E2, every outcome named).</li><li>Code, CPU tests, the Voyager dry run with the shard split, and the Sol dry run.</li><li>Its queue lines, in its report (I place them).</li></ul> | new files only: A40's code and tests, and the pre-registration log `2026-11-05_<time>_A_a40-prereg.md` | nothing to start. Its queue lines wait for A. |
| **E: Arsha's Sol setup** | <ul><li>`docs/trackB/SOL_ARSHA.md`: a numbered block she runs herself, each step with its expected output.</li><li>Whether her fair share is likely better than Ritik's, from his `sshare`.</li></ul> | `docs/trackB/SOL_ARSHA.md` (new) | A's file names and owner check (given in its brief) |
| **C: docs** | ONE_PAGE, PLAN's calendar, the README's story lines 1 and 5, TRACK_B, Track B's START_HERE, TODO_B and FINDINGS_B, current with a to i. | those files | A, D and E |
| **me** | <ul><li>This log, today's daily, INDEX, LATEST, TODO, STATUS and the Gantt.</li><li>The commits, in the order below.</li><li>Starting Ritik's shard of A40's Voyager generation.</li><li>The stale-file scan, the checks and the push.</li></ul> | everything else | the helpers |

**The commit order** (what must wait for what):
1. This plan and today's daily.
2. The amendments: the B20 log's §19 (b, c) and the A39 log's §19 (f, and what B20's move does to nov11). They come
   before any queue change.
3. A40's pre-registration, before anything is generated and before its lines enter the queue.
4. A's code, the queue split and the tests.
5. A40's code and tests, then its queue lines.
6. Then I start Ritik's shard of the Voyager generation under the power guard (pre-approved once 3 is committed).
7. Then `SOL_ARSHA.md`, the docs, and the logs.

**The rules:**
- The push goes to `trackA-nosol` and `main` only. `trackB-main` waits for Nov 6 (d).
- No Sol change; Sol needs Duo.
- Track B paths are committed with `PATH_CHECK_ALLOW=trackB-main` (Ritik's decisions h and b make them his to change
  today), and the message says so.
