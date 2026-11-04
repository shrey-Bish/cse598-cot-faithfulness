# Session log: a cut decided on Nov 6 at 07:00, from compute only (2026-11-04 15:38 MST)

**By:** Ritik. Ritik set the rule at 15:38. It is pre-registered as the A39 log's §16 (`ee14295`) and applied by the
feeder (`2095cfb`). Nothing of E2 read; no paid calls. On Sol: read-only commands, and the pull below after its
safety diff printed nothing, as the access rule allows.

## 0. What Ritik decided

At the Nov 6 07:00 digest, from compute only and about no result:
- **If Sol has delivered under 10 GPU-hours since Nov 4 12:36:**
  - cut 1: drop A39 on the old 30 early, amending §10.2;
  - cut 2: hold B1R2's parts until E2's sweeps and B20's last lines are submitted;
  - update the feeder's queue to match. Cut 3 (shrinking B1R2) stays Ritik's.
- **If 10 or more:** no cut; the existing rules stand.
- Write it into the A39 log as an amendment now, and say in the Nov 6 daily which branch applied and why.

## 1. The amendment: the A39 log's §16 (`ee14295`, committed before anything that applies it)

- **The measure:**
  - the GPU-hours of Ritik's jobs from Nov 4 12:36 to Nov 6 07:00, counted as the digest counts them (each job's
    time in the window × its GPUs, from `sacct`);
  - a job running at 07:00 counts up to 07:00, so the number doesn't depend on when the tick comes;
  - taken at the feeder's first tick at or after Nov 6 07:00, which is the digest's.
- **Under 10:**
  - **cut 1:** the 30's lines not yet submitted are dropped, recorded "not run: dropped on Nov 6 by §16". Any already
    submitted run to their end.
  - **cut 2:** B1R2's parts wait until every E2 sweep and every B20 line is submitted or settled (skipped, or not
    needed). §13's design and its partial read are unchanged.
- **10 or more:** no cut. §10.2 (Nov 11 09:00) and §13.8 (partial at Nov 15 23:59) stand.
- **"B20's last lines" read as every B20 line.** B20's chains end where a part finishes its runs, so their later
  lines settle as "not needed" rather than going in. Cut 2 waits for them to go in or settle.

## 2. How it applies itself (`2095cfb`)

- **`DECISIONS["nov6"]`** in `tools/sol_feeder.py`: the window, the time, the threshold and what each branch does.
- **Two queue options:**
  - `dropif=nov6` on the 30's 29 lines (22 parts, 7 sweeps);
  - `holdif=nov6` on B1R2's 44 lines (40 parts, 4 sweeps).
- **The decision is made once** and recorded with its number and branch in:
  - the feeder's log and state;
  - an alert mail;
  - that morning's digest ("decision nov6 …");
  - `--status`, which shows "not made yet" until then.
- **A failed `sacct` now raises.** The decision waits for the next tick, over the same window, so a failed query never
  reads as "no GPU-hours". The digest already catches such an error.
- **Tests (4 new, each failing first; 43 feeder tests pass):**
  - the cut branch: the 30 dropped, and B1R2 held with places free, then released right after the sweep in the same
    tick;
  - no cut at exactly 10;
  - a failed `sacct` waits a tick;
  - the queue's tags: exactly the 30's 29 and B1R2's 44.

## 3. On Sol

- **The safety diff printed nothing** (RUNBOOK §16's list, and the kit). Nothing was running and the clone was clean,
  so under the access rule I pulled: `28afc15..a6d60db`, before 15:53. It brought the feeder and the queue file, which
  no job loads, and docs.
- **`--status` now shows** "decision nov6 (the A39 log's section 16): not made yet; at the first tick at or after
  2026-11-06T07:00:00". The 30's and B1R2's lines are "to submit", as before.
- **`--dry-run`** reads the tagged queue. The feeder's first tick on the new code (15:56:18) ran cleanly: "the queue is
  full (10 places): b20-nemotron-smoke-r2 waits".

## 4. Docs

- The A39 log's §16.
- RUNBOOK §0: the decision and how to read it.
- PLAN's Nov 8–12 row.
- TODO's A39 row.
- The supplement's ledger: §16 under A39.
- DAILY_2026-11-04 §8; DAILY_2026-11-05's carry-over: Nov 6, 07:00, and what the Nov 6 daily records.
- INDEX; LATEST; STATUS and the Gantt.

## 5. Checks and push

On the final tree (`a6d60db`):
- **The full suite:** 916 passed, 1 skipped. The supplement's and the feeder's tests were re-run after the ledger's
  last edit: 73 passed.
- **Links:** 0 broken.
- **`export_summaries --check`:** numbers only.
- **The supplement's `--check`:** 36 rows, none unverified; CLAIMS unchanged.
- **The Gantt's dry run:** passes.
- **The bundles:** B 51 files, C 43.
- **The pre-push check:** clean.
- **Nothing missing:** 749 of 749.
- **Pushed** to the four branches; then the pull on Sol (§3).

## 6. Judgment calls, with their cost if wrong

1. **"B20's last lines" means every B20 line,** submitted or settled.
   - Cost if wrong: B1R2 waits a little longer for B20's chains to settle.
2. **"Since Nov 4 12:36" ends at Nov 6 07:00 exactly,** not at the tick, so the rule reads one fixed number.
   - Cost if wrong: none; a tick comes within 5 minutes.
3. **A 30's line already submitted at the decision runs on,** since dropping running work would waste it. Under 10
   GPU-hours none can have been: E2's 40-odd lines come first.
4. **The decision mails an alert** as well as being in the digest, so the branch reaches Ritik's inbox at 07:00
   either way.
