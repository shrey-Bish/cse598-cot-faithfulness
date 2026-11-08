# Session log: A39 read; the trade-off, explored (post hoc); a label check of disclosure, pre-registered (2026-11-07 20:19 MST)

**By:** Ritik. Branch `trackA-nosol`, from `905ed4a`. The day's second session (the first was
[13:15](2026-11-07_1315_ALL_overnight-reads-report.md)).

## 0. Input

- **Ritik sends Shrey the C24 message** (merge `origin/main` back).
- **Ritik's sacct (latest), B1R2:** 680258 and 683313 FAILED, exit 1, after 2:25:48 and 2:26:06 (Ritik: "the
  planned stop at the warning, I believe"); 686233, 695986 and 702072 RUNNING; 702635 and 703028 PENDING; the rest
  COMPLETED.
- **Decisions:**
  - **a. Read A39 now** (complete; its rule reads it once complete), by its rules R1–R4 only, in its own log, with its
    F-entry, FINDINGS' story, REPORT §7 and `a39_figures`. The wrapper systems first: does marking tool output
    "unverified" beat the instruction, and at what acceptance cost?
  - **b. An exploratory trade-off analysis,** labelled post hoc wherever it appears, never replacing a
    pre-registered verdict, in its own log written before computing: the trade-off figure (every E2 system, wrong-hint
    following against correct-hint acceptance); expected accuracy under hints as a function of p, the share of tool
    answers that are correct, and where each pair of systems crosses (A40 against prompt_only first, then LoRA against
    prompt_only); "disclosure when following" by keyword, per system. REPORT then gets one labelled exploratory bullet
    and the figure.
  - **c. Pre-register (not run) a hand-label check of disclosure when following,** under the LLM-judge protocol (Ritik's
    labels final; J-opus the reliability check): E2 runs that followed the wrong hint, from base, prompt_only, lora and
    a40, about 40 a system, by a fixed seed, balanced over channels, blind and shuffled, L4's guide and labels; the rule
    fixed now; the sheet's size and the labeling time, for Ritik's yes or no.
  - **d. A "scorecard against the original plan" paragraph** in FINDINGS' story and the README, every number as already
    read, exploratory items labelled.

## 1. Plan (at most 2 helpers; helpers don't commit; the full suite once, at the end)

- **First, committed before anything below is computed:** this plan and the exploratory analysis's own log (b), which
  says exactly what is computed.
- **Helper A:** A39's reading (a): its reader (`finetune/a39.py --report`, E2 and the 30), the reading by R1–R4 only
  in its own log, the wrapper systems first; then `tools/a39_figures.py`. It drafts the F-entry and REPORT's bullets;
  I put them in FINDINGS and REPORT.
- **Helper B:** the exploratory analysis (b), exactly as its log says: the numbers and the figure, with tests.
- **Me:**
  - the label check's pre-registration (c). **Ruling:** it is named **L6**, since **L5** is already Track B's labeling
    batch (TODO's L5, PLAN, CLAIMS). Cost if wrong: a rename;
  - B1R2's status from Ritik's sacct (the two stops, the sweeps, the out-of-memory leftovers), Sol read-only;
  - the scorecard (d), after A39 is read, so it includes the wrapper;
  - then the stale scan, the records, the checks and the push (`trackA-nosol` and `main` only).
