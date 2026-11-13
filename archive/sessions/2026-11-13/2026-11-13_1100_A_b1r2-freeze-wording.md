# Session log: B1R2 read; freeze readiness for Nov 18; the wording held after L6 (2026-11-13 11:00 MST)

**By:** Ritik. Branch `trackA-nosol`, from `01645c4`. The day's second session (the first:
[09:37](2026-11-13_0937_A_l6-judge-reading.md); the daily [DAILY_2026-11-13](DAILY_2026-11-13.md)).

## 0. Input

- **B1R2's runs are complete** (0 left; Sol at `97c0628`). Read it now.
- **Ritik stops the feeder on Nov 16** (`touch feeder.stop; scrontab -r`).
- **The wording, decided after L6, to hold everywhere:**
  - L6/F45: "training made the answer more candid about a hint it followed, in hand labels, without making it follow
    less." Not "honesty solved", not "a yes for training". Its limits beside it: LoRA's trained opener names the hint
    (F28); LoRA's following shows no difference from the instruction (F44); one model, E2 only, 42 rows a system, the
    final answer only; the sheet not blind in practice, with J-opus (blind to systems) agreeing on 82 of 84 rows.
  - The title question (do thinking modes make CoT more honest?) is answered **mixed**, and L6 doesn't bear on it:
    Qwen3-8B with thinking on moves the tool into the private reasoning but not the final answer (F29); gpt-oss-20b's
    reasoning effort changes nothing (F37); Nemotron's answer is less bare after the tool turn with thinking (FB1).
- **Limits:** at most 2 helpers; the full suite once, at the end.

## 1. Plan (11:00, before any B1R2 number is read)

1. **Me, first:** B1R2's numbers-only copy-back (CHECKIN §2: `eval_prov-*_runs.jsonl` from `/scratch/ragarw68/trackA/b1r2/`),
   read-only on Sol.
2. **Helper A:** B1R2's report and reading from the copied-back files, by §13.7 only: `provenance_job.py report --out
   results/trackA/gpu/b1r2`, then `b1_verdict` (the deployable span, the inserted tool turn; alpha 0.25 against
   alpha = 1; following, correct-hint acceptance, no-hint accuracy), paired by question, in its own log; F38's line
   "B1R2, a labelled replication on E2" (B1's verdict on the 30 stays primary); its figure beside B1's. No commit, no
   Sol.
3. **Me:** freeze readiness for Nov 18, one page in PLAN; the 7 CLAIMS mismatches classified (real error or the
   check's known limit), any real one fixed.
4. **Me:** B1R2 into FINDINGS' story item 6, the README's fix paragraph and REPORT §7; every scorecard line checked
   against its F-entry; §0's wording applied wherever L6, the honesty line or the title question appears, every
   sentence changed listed in §5.

## 2. B1R2's copy-back (11:00), read-only on Sol

- `rsync` of `eval_prov-*_runs.jsonl` from `/scratch/ragarw68/trackA/b1r2/` to `cot-disclosure/results/trackA/gpu/b1r2/`
  (gitignored): 83 files, 1,203 records (`prov-a1-v2`, alpha = 1, and `prov-deployable-a0.25-v2`). The records with
  text stayed on Sol.

## 3. The 7 CLAIMS mismatches, classified

- **Claim 2.6's 3** ("56–73 of 73", "+1 [−6, +8]", "30–45%"): C14 is exploratory with no F-entry, so its numbers live
  in its log and `results/summaries/trackC/c14_disagreement.json`, which the check reads only as "session log only":
  **the check's known limit.** Checked against the summary's 20 pairings: catches 56 to 73 of 73 against the checker's
  73 (right); Qwen3 30B Instruct's false alarms minus the checker's pipeline +1 [−6, +8] (C4, tool log: right); Olmo
  +12 to +21 (right). **One real imprecision, fixed:** "~30–45% of the checker's tokens" holds for Qwen3 30B Instruct
  (30–31%) and Olmo (39–43%) but not for Qwen3 30B Thinking (76%); the sentence now says so.
- **Claim 1.1's 4 B20 numbers** (+33, +61, +91, "5 of 10"): each is FB1's (Gemma off's tool channel +33, Nemotron off's
  +61, Granite's +91; R2 "tool beyond authority in 5 of 10"); the check reads only FINDINGS' F entries, not
  FINDINGS_B: **the check's known limit** (recorded Nov 8).

## 4. B1R2 read (helper A, 11:09): [its log](2026-11-13_1109_A_b1r2-results.md)

- **Complete:** 600 of 600 runs a configuration (each run's last ok record, §22), the run ids exactly `b1r2_jobs()`'s;
  1,203 records = 1,200 ok + 3 `not_run` that also have an ok record.
- **B1's rule, unchanged** (`b1_verdict`, the deployable span, the inserted tool turn; recomputed by me on the exported
  report: identical): following 82 of 240 → 49 of 240, **−13.8 [−20.0, −7.5]**; correct-hint acceptance 211 → 197 of
  240, **−5.8 [−10.8, −1.3]**; no-hint accuracy 78 → 79 of 120, +0.8 [−6.7, +8.3]: **"ignores tools"**, as B1 on the
  30.
- **What it means:** the cut in following replicates on 120 questions; the cost to correct hints is now real (its
  interval excludes 0) and past the 5-point limit by the point estimate (14 runs of 240, where 5 points is 12), though
  the interval includes −5. B1's verdict on the 30 stays primary.
- **Files (helper A):** F38's heading ("(B1R2)" in it, for the ledger), its B1R2 block and status line;
  `tools/b1r2_figure.py` with 7 tests (seen failing first) and `docs/paper/figures/b1r2_vs_b1.{png,svg,csv}` (looked at:
  no overlaps); `export_summaries.py`'s KEEP_PATH line and the exported numbers-only
  `results/summaries/trackA/gpu/b1r2/provenance_gen_report.json`.
- **Mine:** FINDINGS' story item 6 (B1R2 replaces "Next") and item 7 (the stricter bar; "trained, prompted or applied
  at inference"); the README's fix paragraph; REPORT §7 (F38's bullet; its waiting entry closed) and §12; CLAIMS 1.7;
  `results_at_a_glance` (F38's row); the supplement's B1R2 row (read, verified); PLAN, TODO, ONE_PAGE, CHECKIN,
  FIX_SO_FAR, WAITING (slide 10).

## 5. The wording held after L6: every sentence changed

- **The L6 line** ("training made the answer more candid about a hint it followed, in hand labels, without making it
  follow less"), with its limits beside it (LoRA's trained opener names the hint, F28; no difference in following,
  F44; one model, E2, 42 rows a system, the final answer only; not blind in practice, J-opus agreeing on 82 of 84):
  - FINDINGS: story item 6's L6 sentence; item 7's honesty line (was "improved with training, in hand labels"); F45's
    Reading (one sentence added) and Limits (the opener and the 82 of 84 added).
  - README: the scorecard's honesty bullet (was "Honesty when following improved with training, in hand labels").
  - REPORT: §6's F45 bullet (one sentence and its limits added); §7's F45 status (one sentence) and limits (the opener,
    the 82 of 84); §12, a new bullet.
  - ONE_PAGE: the L6 bullet (was "LoRA's answer is more honest about a wrong hint it followed").
  - FIX_SO_FAR: the L6 headline (was "what LoRA says when it follows is more honest than the instruction's").
  - CLAIMS 1.5: "Settles it" (one sentence and its limits added).
- **The title question, answered mixed** (F29, F37, FB1; L6 doesn't bear on it): FINDINGS' story item 5 (a closing
  sentence); F45's Reading; the README's story line 2 (a closing sentence); REPORT §1 (a new bullet) and §12 (a new
  bullet); ONE_PAGE (a new bullet).
- **Not changed:** F45's heading and §6's quoted meaning ("honesty when following improved with training", the
  pre-registered words, kept in quotes beside the plain line). REPORT has no abstract yet (it is a skeleton).
- **Also fixed:** §12's "Independent verification does" broken across lines (Nov 8); a time I typed by hand into the
  scorecard's heading ("11:15", ahead of the clock), set to the clock's 11:12 at once.

## 6. Freeze readiness: PLAN's new page, "Freeze readiness for Nov 18"

- Every experiment by state with its F-number; the 13 slides; what Arsha and Shrey owe; REPORT's "waiting" lines (all
  figures); the CLAIMS mismatches; Ritik's dates.
- **The slide map brought up to date:** slide 5 (no figure of F3 exists; L3 is read), 10 (`b1r2_vs_b1.png`), 11
  (C19's bars placed Nov 7) and 12 (made Nov 6, placed Nov 7) no longer say "waiting" on results that are in.
- **CLAIMS' mismatches, now 10: none a wrong number.** 6 are C14's in claim 2.6 (the 3 of §3, and the 3 token shares
  added by its fix, all in `c14_disagreement.json`); 4 are FB1's in claim 1.1. B1R2's "82 → 49 of 240" first showed as
  one more; written as F38 writes it ("82 of 240 → 49 of 240") in every file, it matches.

## 7. Needs Ritik

- **Nov 15:** check-ins and merges. **Nov 16:** stop the feeder. **Nov 18:** slide 5's figure of F3, with Shrey; the
  freeze. **Nov 20:** Gate 3's final statement.
- **No Sol block:** the clone is at `97c0628`, clean; nothing is queued.

## 8. Checks (11:26)

- **The full suite, once:** 1,146 passed, 1 skipped (9:50): the morning's 1,139 and `test_b1r2_figure.py`'s 7. (Another
  project's pytest was running beside it; left alone.)
- Links 0 broken; the supplement 42 rows, none unverified, no log outside the ledger (CLAIMS 10 mismatches, §6;
  source problems 12 once committed); export numbers-only; the Gantt; bundles B 51 files, 73.8 MB, and C 43 files,
  31.3 MB, as before. The pre-push and "nothing missing" checks before the push.
