# Session log: the Nov 3 big session: corrections, Track C as its own workspace, B20, E2 and A39, the clean-up (Nov 3, 11:05– MST)

By: Ritik. Ritik's message of about 11:05, five parts and 19 items, worked in order. This log is written as the work
goes. Each structural change has its plan here before it is made, as Ritik asked.

## Part 1. Corrections and quick items (committed as `6ea9016`)

1. **Arsha's handoff is Nov 6, not Nov 3.** The 10:00 "sent" is corrected in TODO H2, TRACK_B (title, §0, §1),
   PLAN, README, the TODO owner column (12 rows: "Arsha, from Nov 6") and the note in the Nov 1 daily. Her bundle is
   rebuilt on Nov 6 morning.
   - **Started for her (TRACK_B §1a): B18's table and slide 2.**
     - `tools/trackb_final.py` writes `docs/paper/tables/trackB_final.md` and `.csv` from the tracked summaries. It
       has 8 model settings: following per channel, Gate 2 with clustered intervals, B16's authority arm, and B17's
       efforts labelled §13.
     - Slide 2 is `docs/paper/figures/gate2.png`, drawn from the same rows (`fig_gate2`).
     - 5 new tests. I wrote them before the code but ran them only after, so I didn't watch them fail.
   - TRACK_B §1a says what is done and what she takes over: checking, B20's rows, three decisions, the text.
2. **A18:** all four jobs COMPLETED on Sol, but their outputs aren't on the Mac. The user-hint folders still hold 15,
   16 and 8 cuts, and there is no `step9_lora`. Left there; the copy-back lines are in §10.
3. **L3, prepared for the settling call; nothing judged:**
   - **(a) The settling sheet:** `results/labels/L3_settle.csv` (`label_kit.py settle`, gitignored). It holds the 23
     rows with the 25 disagreements: both raters' labels and notes side by side, `to_settle`, an empty third column
     pair (`settled_label_private`, `settled_label_final`) and an empty `guide_rule_that_decided_it`.
   - **(b) The fresh batch:** `results/labels/fresh/` (`label_kit.py fresh`, gitignored), 72 rows.
     - **Source:** L3's own sources (Test 2, the pilot) have only 25 hinted runs left outside the queue, too few to
       balance. So the draw comes from Track B's Oct 27–28 Voyager runs of L3's three model types: Olmo 3 7B Think,
       Qwen3 30B Thinking and Qwen3 30B Instruct.
     - **The draw:** seeded (`L3-fresh-20261103`), 12 per model and channel (user; tool = pasted, own call or
       inserted turn).
     - **Exclusions:** runs in no sheet (982 run ids excluded: L5's batch, bare or not, and L3's and L4's keys), with
       a final answer over 30 characters (L5's bare rule, Oct 28).
     - **Size:** 48 private and 72 final cells, about 85 minutes per rater at L3's pace.
     - No label or keyword was looked at in choosing it.
   - 2 tests, failing first, then 9 of 9.
4. **D12 done:** `finetune/__init__.py` and `finetune/source_tags.py` name `docs/tracks/TRACK_A.md`;
   `progress/common.py`'s `DOCS` is `docs/labeling`, which nothing reads; archive/MOVES.md is updated.

## Part 2. Track C as Shrey's own workspace: the plan, written before the changes

**Who owns what, by path.** Shrey works only on `trackC-main`, and only in these paths:
- `cot-disclosure/agents/`;
- `cot-disclosure/tests/test_trackC_*`;
- `docs/trackC/` (new);
- `docs/tracks/TRACK_C.md`;
- `cot-disclosure/results/trackC/` and `cot-disclosure/results/summaries/trackC/`.

Everything else is read-only for him. If he needs a change elsewhere, he writes a new module under `agents/` or
asks Ritik. `tests/test_agents_dataset.py` doesn't match `test_trackC_*`, so it is read-only for him too, as the
allowlist reads.

**The plan:**
1. **The allowlist: `cot-disclosure/configs/path_allowlist.txt`** (tracked; `configs/` is read-only for him, so he
   can't widen his own list). One line per rule, `<branch> <path>`: a path ending in `/` is a folder, anything else
   a glob. Only branches listed there are checked.
2. **The check: `cot-disclosure/tools/path_check.py`** (standard library only, so a plain `python3` runs it as a
   hook):
   - **As a pre-commit hook** (he installs it once, like the pre-push check): on a listed branch it refuses a commit
     whose staged files (added, changed, deleted or renamed, both names of a rename) fall outside the allowlist.
   - **During a merge** (`MERGE_HEAD` present): a file outside the list passes only if it is exactly the version from
     the branch being merged in. So he can merge `main` into `trackC-main` and take its files unchanged, but can't
     edit them in the merge.
   - **`--range A..B`, for review:** every path changed between the merge base and the tip, as Ritik checks before
     merging his branch into `main`.
   - **Tests** (`tests/test_path_check.py`) on throwaway git repos:
     - an allowed commit passes and a refused one is refused;
     - a merge that takes main's files unchanged passes, and one that edits them is refused;
     - other branches aren't checked;
     - `--range` reports the paths outside the list.
3. **His records, so no file is edited by both of us:** `docs/trackC/`
   - `START_HERE.md`;
   - `TODO_C.md`: Track C's rows moved from `docs/status/TODO.md`, history kept. TODO.md keeps a one-line pointer.
   - `FINDINGS_C.md`: new Track C findings, numbered FC1, FC2, … so they never collide with FINDINGS' F-numbers.
     F18–F34 stay in FINDINGS.md, which links to it, and Ritik merges at the end.
   - `sessions/INDEX.md`: his session logs go in `sessions/<date>/`.
4. **`tools/make_gantt.py` reads every TODO:** `docs/status/TODO.md`, `docs/trackB/TODO_B.md` and
   `docs/trackC/TODO_C.md`. Each table's track still comes from its heading. This needs a test, failing first.
5. **The same layout for Track B** (`docs/trackB/`), for Arsha on Nov 6:
   - START_HERE (pointing to TRACK_B.md until Nov 6);
   - TODO_B with Track B's rows moved;
   - FINDINGS_B (FB1, …);
   - sessions/INDEX.
   - Ritik keeps them current until Nov 6. No path allowlist for `trackB-main` yet, because Ritik didn't ask for
     one; the same file takes it when wanted.
6. **What doesn't move:** no code folder or module. TRACK_C.md stays as the track's design record and links to
   START_HERE.

**Done as planned** (commit `f603110`):
- **The allowlist and its check.** `path_check.py` has 7 tests on throwaway repos, all failing first:
  - an allowed commit passes and a shared file is refused;
  - a deletion or rename of a shared file is refused;
  - a wider list staged in the same commit doesn't help;
  - other branches aren't checked;
  - a merge may take main's files unchanged but not edit them;
  - `--range` reports outside paths.
- **The TODOs.** 25 Track C rows went to `docs/trackC/TODO_C.md` and 19 Track B rows to `docs/trackB/TODO_B.md`,
  verbatim; TODO.md keeps a pointer for each.
  - `make_gantt.todo_paths` reads all three. Its test failed first; 51 of 51 pass.
  - The Gantt counts Track B and Track C as before.
- **The records.** `FINDINGS_C.md` (FC1, …) and `FINDINGS_B.md` (FB1, …) exist; FINDINGS.md links to both. Each track
  has `sessions/INDEX.md`. Track B's START_HERE points to TRACK_B until Nov 6.
- **START_HERE.md (Track C)** was drafted from TRACK_C, FINDINGS and the four pre-registration logs, then checked
  (§2a below).
- **Shrey's bundle:** `results/handoff/trackC_20261103.tar.gz` (gitignored):
  - 43 files, 31.3 MB raw, 5.1 MB packed;
  - all of `results/trackC/` (C15's items, every team log and summary) plus Track B's `steered_cases.jsonl`;
  - verified against its manifest; no GPQA.
  - C19, C20, C25 and C26 read only these. Drawing new fresh items would need the training pool, which no prepared
    run does.

## Part 4, so far: E2 and A39 (their pre-registration is the 11:30 log, commit `61db5af`, before any run on E2)

The full record is in [`2026-11-03_1130_A_e2-a39-prereg.md`](2026-11-03_1130_A_e2-a39-prereg.md).
- **Item 12:** PLAN's honest verdict (one paragraph, "The fix, honestly").
- **Item 13, E2:** 120 questions, 30 per evaluation category, seed `e2-20261103`, sha256 `59c5c250…`.
  - Its size comes from Gate 3's own runs (`make_e2.py --power`), not the GPU cap: at 120, following is ±3.8 to
    ±4.9 and acceptance ±3.7 to ±3.9.
  - Checked by id and text: none of the 30, the pool, set A, Track B's 54 or C15's items.
- **Item 14, A39:** 7 systems, a lean design of 12 runs a question, and shared runs where the wrapper's prompt is
  identical (60 a question, 9,000 with the 30 beside), with rules R1–R4.
  - **Added: LoRA + wrapper,** because it is cheap (4 runs a question) and asks whether marking adds to training.
  - The implementation is under way.
- **Item 15, B1R2:** written as conditional: it runs only if the Sol plan leaves about 60 GPU-hours by Nov 15 after
  A39 and B20.

### §2a. START_HERE, checked; the handoff verified as Shrey would run it (items 7–8)

**START_HERE.md** (866 lines; drafted from TRACK_C, FINDINGS and the four pre-registrations, then reviewed):
- the setup, hand-back and brief sections were read line by line; the bundle line was corrected to Nov 3's contents;
- the brief names no product; every number in its results section is copied from FINDINGS;
- **its additions, kept and listed here for Ritik:**
  - a smoke step before each run, with its own log, read by no rule;
  - one-line meanings for C25's four spot-check labels, from the guide's rules;
  - figures written to `docs/trackC/figures/` and placed by Ritik at merge;
  - halt handling: an unreachable Voyager resumes; a canary failure or a changed model stops and goes to Ritik;
  - the assistant asks Shrey before any command that calls Voyager.

**TRACK_C.md fixed where it contradicted the decisions:**
- a header says START_HERE holds;
- the bundle is now Nov 3's;
- FC entries, logs, summaries and figures go where START_HERE says.

**RUNBOOK §0:** C19, C25, C20 and C26 now run without a further go from Ritik, since they are pre-registered and
their choices were confirmed Nov 1.

**The fresh clone** (`git clone` of this repo at `5f38123` as `trackC-main`, the commit pushed today):
1. The allowlist, `path_check.py` and `docs/trackC/` are all present.
2. **The bundle:** unpacked with `--exclude MANIFEST.json`. `--verify` printed "bundle matches its manifest"; 42 files
   are in `results/trackC/`; C15's items hash begins `10dd00e3e8f5bc0e`.
3. **Tests:** Track C's 8 files and the allowlist's give **54 passed**. The full suite in the clone is in §11.
   - The clone reused the project's virtual environment; a fresh `pip install` wasn't repeated.
4. **The hooks:**
   - a commit of a session log under `docs/trackC/sessions/` **went through**;
   - a commit touching `cot-disclosure/client.py` was **refused** (exit 1, naming the file);
   - `--range` over the branch is clean.
5. **F18, F24 and F34 reproduced with no calls:**
   - F18: Olmo 32B with the private reasoning corrects 6 of 73;
   - F24: −55 [−70, −38], "defers"; H23 +14 [−13, +37], "not supported";
   - F34: +47 [+29, +65], "more corrections";
   - each summary is byte-identical to the tracked copy in `results/summaries/trackC/`.
6. **One thing to tell Shrey:** the run guard (`progress/guard.py`) uses macOS's `pmset` and `caffeinate`. If his
   machine isn't a Mac, the guard won't start, and he should say so before C19.

### §2b. The message for Ritik to send Shrey (item 9)

> Hi Shrey, Track C is set up for you to run on your own from today.
> - **Branch:** `trackC-main`. Start with `docs/trackC/START_HERE.md`; it has everything, and where TRACK_C.md differs,
>   START_HERE holds.
> - **Your paths** on that branch: `agents/`, `tests/test_trackC_*`, `docs/trackC/`, `docs/tracks/TRACK_C.md`,
>   `results/trackC/` and `results/summaries/trackC/`. Install the two git hooks in START_HERE §4; the first refuses a
>   commit outside those paths, the second keeps data off GitHub.
> - **Data:** `trackC_20261103.tar.gz` (5 MB) is in our ASU storage folder. Unpack it into `cot-disclosure/` and run
>   `--verify` (START_HERE §4, step 6).
> - **First two tasks:** (1) setup, the tests and the three no-call reproductions of F18, F24 and F34, which should
>   match exactly; (2) C19 by its pre-registration, due Nov 7.
> - **To hand back:** push to `trackC-main` and tell me; I review and merge into main.
> - **One check first:** the run guard uses macOS tools. If you're not on a Mac, tell me before C19.

## Part 5, item 18: the sloppiness audit and its fixes (docs only, plus one constant)

**How the audit was done:** a read-only audit of 18 docs against the facts of Nov 3 found 81 problems: 41 stale or
wrong statements, 20 out-of-date TODO rows, 10 numbers that disagree and 10 long or duplicated passages. They were
fixed as below. Line numbers are as of `5f38123`.

**Stale or wrong statements:**
- **PLAN:**
  - the header is one line, and the history is in git;
  - the Sol order;
  - the open questions: B1, B17 and L4 moved to "known";
  - the map, dated Nov 3, now has rows for A18 (done on Sol), B18 (started), B20, E2, A39 and B1R2;
  - a new calendar to Nov 18;
  - Gate 2: five models, and L3's kappa;
  - Gate 3: L4 read; it waits on A18 and A39;
  - slides 2, 5, 8 and 12;
  - the report outline's B1 line;
  - "confirmed same-day (B19)";
  - the 458 lines of Oct 31 per-track design notes replaced by a pointer (they are word for word in
    `archive/superseded/PLAN_2026-10-31.md`);
  - the risks rewritten for Nov 3.
  - 695 → 274 lines.
- **FINDINGS:**
  - the header is one line (a 27-line changelog before);
  - story line 1: "all five Track B models";
  - story line 4: the family reading, now confirmed over four families (F30), so the stale "tentative" line was
    deleted;
  - F3's status;
  - F20's two "waiting (Gate 3)" lines;
  - F26's "Step 9 isn't read" (it is F32);
  - F27's generation line;
  - the Oct 27 figure plan replaced by a pointer;
  - "*waiting*" defined as in CLAIMS ("going or planned").
- **CLAIMS:**
  - the header;
  - the obsolete `[TONIGHT]` line deleted;
  - set A "tonight" → Oct 29, and Step 9 read;
  - 1.6's behavior (F28);
  - 1.8, B2: dropped.
- **README:**
  - line 5: A18 done on Sol, A39 and B1R2;
  - the read-first table sends Shrey and Arsha to their START_HERE;
  - the folder map has `trackB/`, `trackC/`, `paper/REPORT.md` and `paper/tables/`.
- **TODO.md:**
  - the header is one line;
  - one status vocabulary, shared with TODO_B and TODO_C;
  - current cells for A17, A18, A30, A36, L3, L4, L5, G2, G3, H1, H2 and D14 (each points to the logs for history);
  - "Blocked by" cleared on A17, A18 and L4;
  - L4's and L5's owner: "Ritik and Shrey";
  - H2's item: "final by Nov 6";
  - the old Notes section moved word for word to `archive/superseded/TODO_notes_2026-11-03.md`.
- **TODO_B:**
  - the closed-provider rows are renamed B21–B23 (they were B1–B3, which clashed with the attention scaling) and
    marked dropped for cost (Part 3);
  - B9, B17 and B18 are current, and B20 is added;
  - done rows' owner: "Ritik", never a later owner for past work;
  - B4's time column.
- **TRACK_B:**
  - the header;
  - the bundle line, sized on Nov 6;
  - B16/B19 due Nov 7;
  - five models;
  - §5 links TODO_B, dated Nov 3, with B18 and B20;
  - B16 "confirmed same-day";
  - the closed providers dropped.
- **TRACK_A:** the header (steps 1–13 done; Gate 3 met Oct 31; A18 and A39 open), steps 6–7 and 11–13 done, the
  fourth version's line, and Gate 3's date.
- **TRACK_A_FIX:** B2 dropped; B1R and B1R2; LR_GATE approved Oct 29; B1's GPU hours as run (34.3 for 630).
- **RUNBOOK:**
  - the header;
  - TODO pointers;
  - §0's Sol order (Nov 3);
  - the test count;
  - §14's status;
  - §15's labels (both sheets in; settle; the fresh batch);
  - §17's pre-commit hook lines;
  - §18's status;
  - B17 and A38 marked done and dropped;
  - §19's Track C status;
  - §20: whose logs go where.
- **RATER_GUIDE:**
  - raters "Ritik and Shrey";
  - L3 and L4 part 1 returned;
  - rows for L3's settling and its fresh batch;
  - the kappa rule's wording aligned with PLAN's "per channel" (written Oct 27). This changes no verdict: L3's final
    answer fails overall too, and L4 passes everywhere.
- **WAITING.md:** the preamble (slides 2, 4, 7, 8 made; Shrey's figures go under `docs/trackC/figures/`), slide 8's
  owner, B1 read, slide 2 → `gate2.png`, slides 5 and 9.
- **SOL_SETUP:** the per-user kit is on `trackC-main`; his accounts file stays uncommitted (it is outside the
  allowlist); C13's run dates (Oct 29–30, 66954278).
- **OUTLINE:**
  - a dated header pointing to REPORT.md;
  - contributions with 5 models and F36, F38 and L4;
  - the setup's models;
  - Gate 2 table;
  - set A's Step 9 (F32);
  - B2 removed;
  - "missing" now A18 and A39;
  - the mechanism in two models.
- **The code map (`cot-disclosure/README.md`):** `path_check.py`, `slide_figures.py`, `trackb_final.py`,
  `path_allowlist.txt`, E2's file, and the tracks' own folders.
- **`tools/make_gantt.py`:** Track B's takeover date Nov 3 → Nov 6, the source of STATUS's "Arsha from Nov 3". The
  Gantt tests' fixtures and expectations moved to Nov 6; 51 of 51 pass.

**Numbers that disagreed:**

| # | what | fix |
|---|---|---|
| N1 | the family reading | confirmed, F30 |
| N2 | TRACK_B's bundle size | sized on Nov 6 |
| N3 | trackB-main | kept at main until Nov 6 |
| N4 | the test count | 745 on Nov 3 |
| N5 | B1's GPU hours | as run |
| N6 | Gate 3's date | Nov 20 |
| N7 | the kappa wording | above |
| N8 | B4's engine and hours | vLLM, 2:01 |
| N9 | C13's dates | Oct 29–30 |
| N10 | the training-target median | left: the two numbers are different snapshots, each labelled where it appears |

**Not done, on purpose:**
- **L7:** TODO_C's C19–C26 cells repeat TRACK_C §5. That is Shrey's file now; he may trim it.
- **L8:** F28's "earlier readings, interim" (66 lines) stays. The supplement's DEVIATIONS check reads strings in F28,
  and moving them risks unverifying rows.
- **L9:** the repeated phrases ("§13", "underpowered") stay where each is a label the rule asks for. They were cut in
  TODO's cells.
- **The ID clash between E2 (the set) and PLAN's old batch-3 job "E2":** the job ID left with the removed PLAN
  sections. `eval_job.py`'s docstring still says "jobs E1-E6", and the A39 change is editing that file now.

**After the fixes:**
- `check_links`: 0 broken.
- The supplement: 34 ledger rows (A39 and B1R2 added), none unverified, no log outside it; DEVIATIONS 0 unverified;
  CLAIMS the same 3 old mismatches.
- `make_gantt --dry-run` parses everything.
