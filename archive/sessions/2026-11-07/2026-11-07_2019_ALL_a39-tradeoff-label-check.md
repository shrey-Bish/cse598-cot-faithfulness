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
  - **e. Arsha's B20 reading** (added by Ritik at 20:31, during this session): when she says `trackB-main` is pushed,
    merge it into `main` by the merge steps (path check, her identity only, no AI lines, Track B's tests on the
    merge). Then update Ritik's docs from her FB1 entry, copying no number FB1 doesn't give: FINDINGS' story line 1 and
    the README (tools beat users in all three new families, 10 of 10 readings; the claim against the tool's form
    depends on family and channel); line 2 (the bare answer after a call in Granite and Nemotron, and Nemotron's drop
    with thinking); REPORT §2–§4's bullets; the scorecard (d). If she hasn't pushed by the end of this session, the
    merge waits for the next one.
    - **At 20:31:** `origin/trackB-main` has nothing new (still `10f7920`, Nov 6 10:08). Checked again before the push.

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

## 2. B1R2 on Sol (me, read-only, 20:22–20:24; status counts only, nothing of B1R2 read)

- **The two "FAILED, exit 1" jobs are the planned stop at the warning,** as Ritik thought.
  - 680258 is `b1r2-21of40` (2:25:48) and 683313 is `b1r2-24of40` (2:26:06), each against a limit of 2:30.
  - Slurm's warning comes 5 minutes before the limit (`--signal=B:USR1@300`). `provenance_job.py` finishes the round
    in flight, then ends with "stopped by a signal; the runs saved so far count, a rerun does the rest". That message
    is a `SystemExit`, so the exit code is 1.
  - The feeder alerted each (6 and 7 of its runs left), as it did for `b1r2-06of40` on Nov 6 (5 left). The sweeps
    take those runs. No fix is needed.
- **The parts:** 31 of 40 have ended (28 COMPLETED, 3 stopped at the warning: 06, 21 and 24).
  - Four are pending, all on Priority: 32–35 (702635, 703028, 704784 and 705727). `squeue --start` gives no time.
  - Five are still to submit (36–40). Each waits only for room (`reserve=240:2`).
  - Ritik's 686233, 695986 and 702072 have since COMPLETED (parts 27, 28 and 31; ended 18:57–19:29).
- **The sweeps** (each after its 10 parts, `left=b1r2:k/4`): 66, 66, 60 and 99 runs left, 291 in all.
  - 270 of those are parts 32–40, not yet run (9 × 30).
  - The other 21 are leftovers: the three warning stops (06: 5, 21: 6, 24: 7), and parts 14 (1) and 20 (2). Those
    three are the "out of memory alone" runs at alpha 0.25 (the 13:15 log's §2), which the sweeps retry and which may
    run out of memory again.
- **Projected finish:** none from Sol (`squeue --start` gives N/A for all four pending parts). Parts take 0:41–2:26
  each. The last parts and the four sweeps need several more hours of starts.
- **The Sol clone:** still at `81ab922`, clean. **The pull still waits:** parts 36–40 haven't started, and they load
  `finetune/` (the 13:15 log's §8).
- **The feeder:** last tick 20:20; "200 lines: 4 failed, 12 not needed, 171 ok, 4 pending, 9 to submit". The 4
  failed are the three warning stops and `a41-step10`'s planned exit 2.

## 3. L6 pre-registered, not run (c; [its log](2026-11-07_2025_A_l6-prereg.md), `838bc86`)

- **The name:** asked for as L5, which is Track B's labeling batch, so it is **L6**.
- **The question:** when a system follows the wrong hint, does its final answer really say the hint shaped it? It
  tests the keyword result: LoRA names the hint in 225 of 248 followed runs (91%), base in 132 of 297 (44%),
  prompt_only in 118 of 237 (50%), A40 in 60 of 84 (71%).
- **The sheet:** 14 followed runs per system and channel from base, prompt_only, lora and a40, one per question, drawn
  by seed `L6-20261107`; **168 rows**, shuffled, with the system, run id, question and keywords hidden. Every stratum
  has 20 or more distinct questions (pool: base 297, prompt_only 237, lora 248, a40 84 runs).
- **The labels:** L4's guide and five labels, the final answer only. Ritik's labels are final; J-opus is the
  reliability check (the Nov 4 protocol's batch files), run after Ritik's sheet is saved; no re-look.
- **The rule:** per system, the share labelled `says_changed` or `mentions_only`. LoRA − prompt_only and A40 −
  prompt_only by a bootstrap clustered by question: "discloses more / less than the instruction, in labels" or "no
  difference detected in labels". Each outcome's meaning is said in advance.
- **For Ritik's yes or no:** 168 rows, **about 3½ hours of labeling** (L4's 1¼ minutes a row); J-opus under an hour;
  the sheet is built on Sol from the texts (no GPU). To land before the Nov 18 freeze, the sheet should reach Ritik by
  about Nov 12.

## 4. A39 read (a; helper A; [its log](2026-11-07_2033_A_a39-results.md), F44)

- **When:** complete, and its rule reads it once complete (§18 gives only a partial read at Nov 15 23:59).
- **Checked by me:** the log's verbatim block matches the reader's JSON exactly (`a39.text` on `a39_e2.json`, 40 of 40
  lines). Both reports are complete (E2: 1,440 a core system, 480 own runs a wrapper system; the 30: 360 and 120).
  There are no text keys and no no-answer imbalance.
- **The wrapper, first:**
  - **alone (R4): "no effect"** on the inserted tool turn (following −1 [−7, +4], acceptance −0.5 [−5, +4]); the
    pasted block's check is exactly 0;
  - **with the instruction (R3): "adds, costs acceptance".** Against the instruction alone it follows −14 [−20, −9]
    and takes −12 [−18, −6] on the tool turn: 42 of 232 against 77 of 237, and 179 of 235 against 210 of 238;
  - **with LoRA (R3): "adds to both"** (−8 [−14, −2] against LoRA, −14 [−20, −8] against the wrapper; acceptance
    within 5 points).
- **The rest:**
  - **R2: LoRA + note is "fewer than the instruction"** (−8 [−12, −4]), which the pre-registration called "the first
    fix that beats one line". R2 reads following only; acceptance −9 [−13, −5] sits beside it, and R3 reads the same
    system "adds, costs acceptance";
  - LoRA "no difference detected" (+2 [−2, +6]); base "more";
  - **R1 (Gate 3's rule): passes for the instruction (−9 [−14, −4]) and LoRA (−7 [−11, −3])**, the powered
    replication (F28 stays); it passes for every system but the wrapper (diluted by design).
- **The 30, beside it:** R4 "works" (−18 [−34, −1]); both wrapper combinations "no better than the better one alone";
  LoRA + note "fewer than the instruction" (−11 [−18, −4]).
- **Figures** (`tools/a39_figures.py`, headlines with the readings' words; 4 new tests seen failing first; its file 8
  passed): `a39_e2_fixes`, `a39_e2_parts` and the 30's two. I looked at both E2 PNGs: clean.
- **My edits after helper A:** FINDINGS' story sentence on A40 now says "doesn't beat the instruction by its rule"
  (A39's R2 reads LoRA + note "fewer"); A39's log's limits note L6. The supplement's A39 row has its verdict and checks;
  the export's comment says F44.

## 5. The trade-off, explored (b; post hoc; helper B; [its log](2026-11-07_2020_A_tradeoff-exploratory.md) §5)

- **Written and committed before computing** (`3c3aa62`); §1–§4 unchanged since (80 lines added below them, none
  removed).
- **Checked by me:** I recomputed A40's and LoRA's crossings and four systems' disclosure counts in a separate script.
  They match: A40 dW +8.4, dC −14.9, p* 0.361; LoRA dW −2.4, dC −2.3, no crossing; 132/297, 118/237, 225/248, 60/84.
- **The numbers (exploratory, post hoc):**
  - every E2 system that follows fewer wrong hints than the instruction also takes fewer correct ones, pooled and on
    the tool turn (point estimates);
  - **A40 gives more correct answers than the instruction only when fewer than 0.361 [0.220, 0.499] of the tool's
    answers are correct** (no answer counted wrong: 0.288 [0.149, 0.417]);
  - **LoRA is behind the instruction at every p,** by about 2 points, every pointwise interval including 0;
  - **disclosure when following (keyword):** LoRA 225 of 248, A40 60 of 84, the instruction 118 of 237, base 132 of
    297; LoRA − the instruction +40.9 [+30.2, +51.4], A40 +21.6 [+6.9, +35.5]. A40's depends on the channel: user 5
    of 24, inserted 29 of 29.
- **Tests:** `tests/test_tradeoff.py`, 24 seen failing (no module) then passing. The export then refused
  `tradeoff_e2.json`: its bootstrap description was one 406-character string, and the limit is 200. A test was added
  first (RED), then the description was split into four strings; 25 passed. The rerun gives the same numbers.
- **Recorded:** REPORT §7's labelled exploratory bullet and `tradeoff_e2.png`; WAITING; the supplement's row (kind
  "exploratory"); PLAN's row; the export.

## 6. The scorecard (d)

FINDINGS' story item 7 and the README, every number as already read, the exploratory ones labelled:
- honesty when following improved with training (keyword; backed on the 30 by L4; L6 pending);
- resisting wrong hints improved by A40, as a trade (A40's crossing at 0.36, exploratory);
- accuracy preserved, and Gate 3 passed by every trained version (on E2 with power);
- the stricter bar (beating the instruction on following at no cost) met by no fix;
- the mechanism (LoRA in the reasoning, F39; A40 in layers 0–14, F42);
- our reading: without verification, the two trade off, so the fix belongs at the system level (Track C, F24).
- **Not in it yet:** Arsha's FB1 (decision e), which waits for her push.

## 7. Stale lines fixed

- FINDINGS (F44 and story item 6 by helper A; item 7 and the A40 sentence by me), REPORT §7 and its header, CLAIMS
  1.5 and 1.6, FIX_SO_FAR, `results_at_a_glance` (F44's row), PLAN (A39, B1R2, the trade-off and L6 rows; the
  calendar; Gate 3's statement; the report's state; slide 9 and the slide history), TODO (A39, B1R2, L6), ONE_PAGE,
  CHECKIN §3, WAITING, the README.
- **A slip, corrected:** I first wrote REPORT's header time as 20:52, ahead of the clock (20:43). It was set to the
  clock at once.

## 8. Needs Ritik, and Sol

- **L6:** yes or no (168 rows, about 3½ hours of labeling; if yes, the sheet should reach Ritik by about Nov 12).
- **Nov 8:** mark Gate 2 (PLAN's statement, ONE_PAGE, TODO's G2).
- **Once every B1R2 part has started** (36–40 are still to submit): the Sol pull, by the 13:15 log's §8 block.
- **Optional:** drop B1R2's `reserve=240:2` (a queue-file edit), so parts 36–40 and the sweeps go in faster.
- **Arsha:** when she says `trackB-main` is pushed, the merge (decision e) in the next session.
- **No Sol block tonight:** nothing on Sol needs a command now. The clone is clean at `81ab922`, and the pull waits for
  parts 36–40 to start.
