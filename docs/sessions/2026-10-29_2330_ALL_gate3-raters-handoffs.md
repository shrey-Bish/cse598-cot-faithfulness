# Session log: Gate 3 in one command, B2's bias log, the rater guide, the handoffs (2026-10-29 23:30 MST)

Project: CSE 598 Group 10. This covers Ritik's items 4–6 of 22:20 (no calls, no Sol), done while C15 runs on
Voyager. The decisions, C14 and the pre-registrations of C15 and B15 are in the 23:00 log.

## 1. Header

- **Time:** Oct 29, 23:00–23:30. **Tracks:** A, B, C. **By:** Ritik.
- **Branch:** `trackA-nosol`, local commits only.
- **Tests:** 524 pass (CPU, no network).
- **Calls:** none. C15's solver phase is running beside this work (section 5).

## 2. Track A, ready for the morning

**Gate 3 in one command** (`finetune/gate3.py --out results/trackA/gpu/eval`): runs eval.py's report, then writes:
- `gate3.json`, each trained version's verdict:
  - passes, fails (naming the criterion), waiting, or too few questions;
  - Gate 3 is "met" if one version passes, "not met (negative result)" once all four have failed, else waiting;
- `gate3_table.md`, the table: following, no-hint accuracy, hiding and false disclosure, each against base; the
  inserted-vs-pasted prediction; the verdict;
- `figures/gate3_following` and `figures/gate3_vs_base` (PNG, SVG, CSV): wrong-hint following per system and
  channel, and each system minus base with the ±5-point band on accuracy.

**The rule is the one PLAN states and eval.report() has applied since Oct 25**, unchanged:
- following minus base has a clustered 95% interval below 0;
- no-hint accuracy is within 5 points (the point difference);
- hiding minus base has an interval that reaches 0 or below.

**Tested** on synthetic files of the real shape (eval.jobs()'s 930 runs per system in two part files). In the
test:
- a version that follows less with the same accuracy passes;
- one that also loses accuracy fails on that criterion;
- a missing system waits;
- with no base, everything waits;
- all four failing is a negative result.

I looked at both figures from a synthetic run: no label collisions.

**B1's alpha rule is fixed in advance.** It is in `provenance_job.py` and `choose_alpha`, from commit `0bd2241`
(Oct 29 00:31): before set A's runs existed and before the forced job was queued (23:00 log, section 8).

**B2's bias log** (Ritik approved LR_GATE 1e-2):
- `train.py` writes every learned bias at every optimizer step (`train_log.jsonl`, "gates").
- After each epoch it checks them against Adam's applied bound (`gate_drift`). The export writes
  `final/gate_drift.json` for the chosen epoch.
- **Ruling:** the bound is the learning rates actually applied, summed: 1.31 over 260 steps with the warmup and
  linear decay. Ritik's lr × steps (2.6) is logged beside it. No bias can reach 2.6, so a check at 2.6 could never
  fire.
- A bias within 10% of the bound is reported with a rerun at 3e-2 proposed, and the run is left as it is.
- Tested on the tiny model.

## 3. Labels: the one-page rater guide

`docs/progress/RATER_GUIDE.md`, linked from LABELING_GUIDE.md. It gives:
- **the order:** L3's 101 rows, then L5's 171;
- **time per row:** L3 3–4 h; L5 group 1 ~2 h, group 2 ~1.5 h, group 3 ~30 min;
- **the five labels and their rules;**
- **what not to do:** no talking before both sheets are in, and no AI tools: the labels must be human, and the
  text stays in the sheet;
- **sending sheets back:** CSV, a file-name pattern, sent to Ritik directly, never through GitHub;
- **how kappa is computed:** p_o, p_e, kappa per text and channel; under 0.6, settle, tighten the guide, and
  label a fresh batch.

No labeling was done here.

## 4. Handoffs and the paper pack

- **`docs/handoff/TRACK_C.md`** (for Shrey, Nov 3) has:
  - the code since Oct 28 (`--first-from`, `--no-check-tool`, `--bad-first`, the redacted variants, `sol_c13.py`,
    `disagreement.py`, `fresh_items.py`, `--solve-only`, `c15.py`);
  - C11 and C12's results, C14, C15's design;
  - the commands, the open items, the decisions (C11's rule, C13's models and temperature, H23 on fresh cases,
    C14's frozen rule) and three new traps.
- **`docs/handoff/TRACK_B.md`** (for Arsha, Nov 3) has:
  - Qwen3-8B back on vLLM (FlashInfer's sampler, the pinned tokenizer, the import race), queued as 66954217, and
    how its numbers-only files come back;
  - B15's design and commands;
  - the rater guide;
  - two traps: Sol's clone origin, and B15's older "before" runs.
- **Data bundles:** `make_handoff_bundle.py` takes the whole `results/trackB/` and `results/trackC/` folders, so
  C15 and B15 are included once they end. A bundle is never overwritten, so both are built after the runs finish
  (dry runs now: B 10 files, 22.6 MB; C 29 files, 22.3 MB).
- **`docs/paper/CLAIMS.md`:**
  - 2.1 now rests on two Olmo reviewers (C11), with C13 and C15 as what settles it;
  - 2.4 is filled in from C12 (partial; H23 to test);
  - new 2.6: C14's cheaper check, waiting on C15;
  - B15 under the Track B supporting claims;
  - set A's Voyager numbers under 1.3.
- **`docs/paper/REVIEWER_QUESTIONS.md`:**
  - C11 and C12 answer thread 2's first two questions in part;
  - new: "Couldn't you just ask the model to say where its answer came from?" (B15) and "Does any of it hold on
    new items?" (C15);
  - C14 is under the checker's question.

## 5. Running now

- **The guard** (started 22:48):
  - C15's solver phase: 23 of 200 cases at 22:56, 0 errors.
  - Then, together on the 4 slots: C15's reviews (600 calls) and B15 (1,620 runs).
- **To stop:** `touch cot-disclosure/logs/stop_guard`.

## 6. Next

- C15's readings (`agents/c15.py`) and B15's (`progress/run_b15.py --report`), each with its own session log.
- The bundles once both end.
- The 07:00 daily with the morning Sol lines.
