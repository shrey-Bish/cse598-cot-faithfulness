# Session log: the handbook dossier, the evaluation audit and Part C (2026-11-26 20:39 MST)

**By:** Ritik. Branch `trackA-nosol`, from `a90b216` (main, `trackA-nosol`, `origin/main` and `origin/trackA-nosol`
level). The time in the name is the prompt's first `date`. The daily: [DAILY_2026-11-26](DAILY_2026-11-26.md). The
previous log: [1745](2026-11-26_1745_ALL_demo-min-simple-deck.md). The results are frozen: the tag
`results-freeze-2026-11-18` on `7e1fdc0`. Two helpers wrote the dossier's files (01–17, 19, 20). They did not commit.

## 0. Input

A pasted note and `~/Downloads/HANDBOOK_DOSSIER.md` (20:38, read in full), acted on as Ritik's.
- **Part A:** a dossier of files 00–20 in `results/handbook_dossier/` (gitignored, zipped).
- **Part B:** an evaluation audit, also in `docs/handbook/`.
- **Part C:** three descriptive analyses from saved data (post-freeze, no new runs), two backup slides.
- **Slide 7's notes:** one line on C27.

The brief is dated Nov 27 and asks for "(Nov 27)" labels. It is Nov 26, so the labels say Nov 26.

**Dated note (Nov 26, 20:39): documentation and presentation work after the freeze. No frozen number, figure or verdict
changed. Part C's analyses are descriptive and change no verdict.**

## 1. Part B: the evaluation audit (mine)

`docs/handbook/18_EVALUATION_AUDIT.md` (also in the dossier):
- **The checklist:** each item done, partly or missing, with its evidence and why it matters.
  - Partly: validation against hand labels (L3 under 0.6 in four of six cells; human against AI), multiple comparisons
    (named, not corrected), error analysis (resisted answers unlabelled).
  - Done: the rest.
- **What's missing:** seed variance; a second trained model; a second benchmark; free-form tasks; closed models; the
  checker's hard case; two human raters; resisted answers unlabelled; blind labelling; multiplicity; power. Each is
  marked saved-data or new runs.

## 2. Part C: three descriptive analyses (mine; `cot-disclosure/tools/handbook_part_c.py`)

**Descriptive, post-freeze (Nov 26).** Counts from saved, frozen records, with Wilson intervals. Output:
`results/summaries/handbook/part_c.json` (numbers only) and `docs/handbook/PART_C.md`. Test:
`tests/test_handbook_part_c.py`, which checks every Wilson and the frozen totals, checks the glance against 02, and
recomputes from the gitignored records where they exist.
1. **The evaluation at a glance:** eight rows (data, measure, compared with, systems, headline), each a row of 02_NUMBERS.
   No new number. Backup 32, "Datasets, metrics and baselines".
2. **The hand labels' categories** (Ritik's final labels; every labelled row followed its hint, and no sheet holds a
   resisted answer):
   - L6 (a seeded sample, 42 per system):
     - instruction: no mention 23 of 42, mentions only 5, says it changed 13, rejects 1;
     - fine-tuning: 5, 9, 28 and 0.
     - Says it changed plus mentions only = 37 and 18, F45's.
   - L4 part 1: the fine-tuned keyword candidates say it changed in 97 of 147 (F28's). The matched no-fix and
     instruction runs are mostly no mention (62 of 74; 57 of 73).
   - Backup 33, "How the answers fail, by category" (L6).
3. **By subject on the 120 fresh questions** (30 each), pooled as A39 pools. The totals reproduce 297 of 703, 84 of 694,
   439 of 476, 347 of 459, 237 of 713 and 248 of 705.
   - Law leads wrong-hint following for every system: no fix 107 of 180 (59%), consistency training 55 of 175 (31%).
   - Consistency training's cost on right tool hints is largest in law: 71 of 112 (63%). The other subjects are 71–85%.
- **02_NUMBERS N176–N217** (descriptive): the L6 categories and the by-subject cells, each checked exactly against the
  summary.

## 3. The decks and slide 7

- **Source:** Ritik's 18:55 deck (`tools/deck/simple_deck.py`).
- **New backups:** 32 and 33 after C27's backup 31. The main slides are untouched.
- **Slide 7's notes** gain the line Ritik gave, before the hand-off.
- **Builds:** the tracked copy with placeholders and its PDF (33 pages), and the local deck. Backup 32 was rendered and
  fixed: its last row ran into the footnote.

## 4. Part A: the dossier (two helpers; checked and indexed by me)

- **Where:** `cot-disclosure/results/handbook_dossier/` (gitignored), 32 files, 1.8 MB.
- **The zip:** `cot-disclosure/results/handbook_dossier_2026-11-26.zip` (593 KB, gitignored).
- **Each file:**
  - opens with what it covers and its sources;
  - is under 150 KB (the big ones split: 01a, 02a, 03a–b, 08a–c, 09a–d, 10a–b);
  - is listed with its size in `00_INDEX.md`.
- **Model text:** only `17_EXAMPLES.md` quotes it (9 runs, each picked first in the order sha256("dossier-20261126" + id)).
  The verbatim progress and plan copies have quoted model text replaced by omission markers.
- **Privacy:** no email, Sol username or key in any file (grepped; the Sol username appears as `<sol-user>`).
- **My corrections to the helpers' files:**
  - file 15's last full test run is the Nov 26 one (1,485 passed, 1 skipped), not Nov 23's;
  - file 04 points to Part C for the per-subject results.
- **File 20, approaches considered but not done** (19 entries in the file), each with its date and reason:
  - B2 gated attention (Oct 31, scope; about 2.75 GPU-hours a version);
  - the larger dial replication B1R (Nov 3, underpowered; 53–122 GPU-hours for ±5 points; B1R2 on E2 instead);
  - A38, the dial with the note (Nov 3, as pre-registered);
  - closed models B21–B23 (Nov 3, cost);
  - GPQA (B6, access never obtained);
  - C21, hard items (Oct 31, scope; about 600 calls);
  - C22, another solver (stretch; about 2,000 calls);
  - C23, reviewer wordings (Oct 31, scope; about 1,500 reviews);
  - A21 (Oct 31, scope and timing; reopened as C27 on Nov 26);
  - L4 part 2 and L5;
  - L3's settling call (Nov 4, the AI rater);
  - Ollama (Oct 28);
  - the guide note in targets (Oct 25);
  - C14 (refuted on fresh items).
- **Not in the repo:**
  - the proposal's text, hypotheses, thresholds and staff feedback (01 reconstructs what the progress documents say about
    it);
  - the progress talk's date and feedback;
  - the puzzles' independent-solver and hand-trace checks;
  - a recorded reason for GPQA beyond the access;
  - some Voyager settings and revisions;
  - per-epoch training-loss curves;
  - the Gate 3 and E2 run texts (on Sol) and C26's texts;
  - cost estimates for seed variance, a second trained model, a second benchmark or closed models.
- **Two names for C27:** `docs/trackC/TODO_C.md` line 36 already used "C27" for Track C's slides 11–12 (done Nov 7)
  before the post-freeze addendum took the code on Nov 26.
  - Renaming would touch the addendum's committed pre-registration, code, summary and 02 rows, so it isn't renamed.
  - `00_INDEX.md` and this log say which is which.
- **Source conflicts the helpers noticed** (not fixed, reported):
  - TODO line 18 says Arsha and Shrey have no commits after Oct 4, while git has commits from both on Nov 6–15;
  - LABELING_GUIDE gives 295 runs for the L5 batch, while TODO gives 171 rows.

## 5. Checks and push

- 53 deck, pack, Part C, C27 and hygiene tests passed. `tools/check_links.py`: 0 broken links.
  `export_summaries.py --check`: numbers only.
- Pushed with Parts B and C at 20:46; the records at 20:59.
