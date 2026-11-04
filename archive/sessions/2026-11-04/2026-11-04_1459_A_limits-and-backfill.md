# Session log: would shorter limits start more often? The backfill evidence (2026-11-04 14:59 MST)

**By:** Ritik. Ritik asked at 14:59. Sol at `f8b61af`; the feeder ticking (last 14:56), the queue full (9 jobs and the
feeder, all pending, Priority); nothing has run since 12:36. On Sol only read-only commands ran: `sacct`, `sprio`,
`squeue --start`, `scontrol show config/partition/node`, `sacctmgr show qos`, and reading the jobs' Slurm logs. All
counting went through pipes; nothing was written on Sol. No queue edit, no commit to code, no pull needed.

## 0. What Ritik asked

- Our class QoS gets no priority boost, so our jobs start almost only by backfill, and backfill favours short limits.
  `1af93fc` raised the remaining parts to 2:00 and the sweeps to 3:00.
- Weigh it with evidence from Sol: would 1:00–1:30 start more often, now that each run is saved as it finishes?
- Recommend keep or change, with the cost (start-up per job). If change: queue edits for the lines not yet submitted
  only, in their own commit, and say before any pull is needed.

## 1. The evidence

**Every GPU job of ours since Nov 1 was started by backfill** (sacct's `Flags`: `SchedBackfill`, 51 of 51).

**The waits, by limit** (sacct: submit to start):

| limit | jobs | when submitted | wait |
|---|---|---|---|
| 1:00 | 378041, 389340 | Nov 3 day | 0.1, 0.7 h |
| 1:00, 1:30 | 334085, 334084 | Nov 2 13:57 | 1.1, 0.8 h, while others of the same submission, with the same limits, waited 10.9 h (below) |
| 1:00 | 355632, 355747, 334114/5 | Nov 2 | 6.9–10.9 h, starting in the same minute (Nov 3 00:50–00:51) as the 1:30 and 2:30 jobs below |
| 1:30 / 2:30 | 334111–334113 | Nov 2 13:57 | 10.9–11.6 h, the same wave |
| 2:00 / 2:30 | 378051–378053 | Nov 3 08:50 | 0.2–0.3 h |
| 3:00 | the 9 quarters | Nov 3 21:02–21:24 | 1.8–4.4 h |
| 1:30 | the 16 sixteenths, 4 B20 jobs | Nov 4 00:23–10:25 | 0.1–4.8 h (the sixteenths 1.8–4.8) |
| 5:30, 8:00 | B1's generation, B17's main job | Nov 1–2 | 8.2–19.3 h; the 8:00 started 5 hours after the 1:00 jobs submitted with it |

- From 1:00 to 3:00 the jobs started in waves, together, whatever their limit. Only the very long limits (5:30, 8:00)
  clearly waited longer.

**The scheduler** (`scontrol show config`):
- backfill tests every job: `bf_max_job_test=150000`, and 25 per association against our 9;
- `bf_window` is 30 days, at a 5-minute resolution;
- `bf_max_time=120` with `bf_continue`. That would explain why our jobs' estimates come and go (21:30, 23:40, N/A,
  06:25, N/A).

**The priority** (`sprio`, `sacctmgr`):
- Neither QoS adds any: `public` and `class` are both 0.
- The pending jobs on top are almost all fair share (weight 100 M): 89 M, 82 M and 80 M for the first three.
- Ours is 0.83 M: fair share 0.0057 and 4.5 hours of waiting. Age adds at most 10 M after 7 days.
- So 212–218 of the 226–232 pending GPU jobs rank above ours, from 25 users.

**Right now** (between 14:59 and 15:02): every A100 in the public partition is allocated, except two drained nodes (sg008, sg044). No
gap is open, at any limit.

**The jobs ahead** (218):
- 80 wait on a dependency and 10 on a node or array limit. About 128 could start.
- They ask for 1 GPU (188), 4 (23) or 2 (5).
- Their limits: 9 at 2 hours or less, 68 at 4 or less, 85 at 12 or less, 8 at a day or less, 48 over a day.

**The gaps to come.** 22 nodes are held for 36 pending multi-GPU jobs, with planned starts. On those nodes, 49 GPUs
free up before the node's held start, between 16:43 today and Nov 5 13:04. A job shorter than the gap can use it:

| our limit | gaps that fit |
|---|---|
| 1:00 | 43 |
| 1:30 | 41 |
| 2:00 | 41 |
| 3:00 | 40 |

- The median gap is 12 hours.
- Backfill offers each gap in priority order, and most jobs ahead of ours (4–12 hours) fit a 12-hour gap.
- So what holds us back is our place in the order, not our limit. Shortening from 2:00 to 1:30 gains no gap; to
  1:00, 2 of 49, and the 9 jobs ahead at 2 hours or less compete for those.

**Start-up, per job** (start to "server ready" in 18 A39 jobs' Slurm logs): median 10.6 minutes, range 1.9–25.4.

## 2. Recommendation: keep `1af93fc` (2:00 parts, 3:00 sweeps)

- **What a shorter limit would gain:** almost nothing now (0 of 49 gaps at 1:30, 2 at 1:00, in one snapshot), and
  nothing in the history, where 1:00 and 3:00 jobs started in the same waves.
- **What it would cost:**
  - At 1:00 the warning comes at 55 minutes. After a median 10.6-minute start that leaves about 44 minutes to
    generate, while a sixteenth alone needs 40–69 minutes in all. So many parts would stop short.
  - Each stop loses the runs in flight (up to 48, at the long tail of a pass), and its leftovers need a sweep job with
    its own 2–25-minute start. Saving each run as it finishes keeps only the finished ones.
  - At 1:30 most sixteenths fit, but with no gap gained over 2:00 and less margin.
- **No queue edit, no commit to the queue file, no pull needed.**
- **When to look again:** if most jobs ahead of ours had short limits, or the gaps became short. The Nov 5 digest's
  waits will show it; the commands are in §1.

## 3. A correction

At 13:49 I put our low priority down to the QoS: a "priority factor" of 0 for ours against 200 M for `public`'s.
`sacctmgr` shows both QoS at 0, and `sprio` shows the gap is fair share. Corrected, with the time, in:
- the 13:49 log's §4;
- DAILY_2026-11-04 §6;
- DAILY_2026-11-05's carry-over;
- PLAN's calendar, TODO's A39 row and INDEX's 13:49 row.

The 13:49 commit message (`e3f010e`, pushed) keeps the old wording.

## 4. Docs

DAILY_2026-11-04 §7; DAILY_2026-11-05's carry-over; INDEX; LATEST; TODO's A39 row (the limits kept by this evidence);
STATUS and the Gantt; the supplement.

## 5. Checks and push

On the final tree (`df2f119`):
- **The full suite:** 912 passed, 1 skipped (CPU, no network).
- **Links:** 0 broken.
- **`export_summaries --check`:** numbers only.
- **The supplement** (regenerated, `df2f119`; `--check` passes): 36 rows, none unverified, no log outside the ledger.
  CLAIMS unchanged.
- **The Gantt's dry run:** passes.
- **The bundles:** Track B 51 files, Track C 43.
- **The pre-push check:** clean.
- **Nothing missing:** all 748 files tracked at `origin/main` (`67dbe36`) are still here.
- **No file a Sol job loads changed,** so no pull is needed.

## 6. Judgment calls, with their cost if wrong

1. **One snapshot of the gaps.** Jobs end early and new ones arrive, so the gaps move. The history (waves for every
   limit from 1:00 to 3:00) agrees with it.
   - Cost if wrong: a few starts a day missed, if short gaps turn out to be common. The Nov 5 digest's waits would
     show it.
2. **Gaps counted only on nodes held for multi-GPU jobs.** Gaps also open when a job ends early on any node, but those
   too go first to the higher-priority jobs that fit.
3. **No change to the A39 log.** Nothing changed: §14's limits stand, now with this evidence.
