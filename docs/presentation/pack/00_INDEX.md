# The presentation pack (Nov 24)

Everything needed to build the slides, write the report and prepare for the presentation, in one place. **Gathering
and explaining only:** no new analysis, no frozen number changed (results frozen: tag `results-freeze-2026-11-18` on
`7e1fdc0`), no report prose and no speaker scripts. Every number carries its finding id and its source; plain names
come first, internal codes in parentheses; exploratory results are marked. The whole pack in one file, for a phone:
[`PACK.pdf`](PACK.pdf).

## Read in this order

| order | file | what it is | when you need it |
|---|---|---|---|
| 1 | [01_STORY.md](01_STORY.md) | the question, the answer ("mixed"), the five findings with their evidence, what's new and what isn't, the limits, and a "don't say" list of every overstatement we've corrected | first: the spine of the talk and the report |
| 2 | [05_SLIDE_OUTLINE.md](05_SLIDE_OUTLINE.md) | a 12-minute deck, slide by slide (point, figure, numbers, demo keys, time, a blank speaker column), six backups, what to cut | building the slides |
| 3 | [04_FIGURES.md](04_FIGURES.md) | every figure: path, what it shows, a plain caption, its data source, its slide and report section; [`figures/`](figures/) holds the slide-ready ones at 1920 px | placing figures |
| 4 | [08_PREP_GUIDE.md](08_PREP_GUIDE.md) | a study guide: 13 concepts (plain words, an analogy, how we used it, its number, a check-yourself question), the demo's four moves, fallbacks, a rehearsal plan | preparing to present |
| 5 | [09_QA_BANK.md](09_QA_BANK.md) | 28 likely questions with the facts and findings to answer from, the hard ones marked | the Q&A drill |
| 6 | [02_NUMBERS.md](02_NUMBERS.md) | every number a slide or the report might use: claim, numbers, interval, finding, source file, status (131 rows), checked against its source | checking any number |
| 7 | [03_METHODS.md](03_METHODS.md) | how exactly we did it: question sets, hint wordings, the 12 models, compute, Olmo's architecture, patching step by step, both fine-tuning methods, the other fixes, the review pipeline, statistics, pre-registration, labels, judges, the freeze | methods slides and §3 of the report |
| 8 | [06_REPORT_OUTLINE.md](06_REPORT_OUTLINE.md) | the report section by section: the facts, figures and tables each needs, with a suggested length | writing the report |
| 9 | [07_RELATED_WORK.md](07_RELATED_WORK.md) | each paper: full reference, what it found, how ours relates (agrees, extends, differs) | related work, novelty questions |
| 10 | [10_TEAM_AND_PROCESS.md](10_TEAM_AND_PROCESS.md) | who did what (git history, tracks), the timeline of key dates, the AI-use facts | writing CONTRIBUTIONS.md and AI_USE.md |
| 11 | [11_REQUIREMENTS.md](11_REQUIREMENTS.md) | course requirements found in the repo: none (page limit, format, rubric, deadlines): check Canvas | before submitting |

## Also here

- [`figures/`](figures/): the slide-ready figures, PNG, 1920 px wide, rendered from the tracked SVGs.
- `demo_shots/`: screenshots of the demo's four moves, as a fallback. **Local only** (gitignored): they show recorded
  model text, which never goes to GitHub. Not in PACK.pdf.
- [`PACK.pdf`](PACK.pdf): files 00–11 in order, with the slide figures; phone-sized pages.

## How the numbers are checked

`cot-disclosure/tests/test_presentation_pack.py`:
- Each row of 02_NUMBERS is checked three ways: its "k of n" and intervals are in its finding's section of FINDINGS (or
  FINDINGS' summary at the top), as frozen; its source file exists; in a JSON source, each "k of n" is a k and n in one
  record and each interval bound is a number in the file (within rounding).
- Every "k of n" and interval anywhere in the pack is in 02_NUMBERS, FINDINGS or (the demo's finder counts) TALK_MAP.
- The links resolve; the figures are 1920 px wide; PACK.pdf is there.

**Where a number and its source differ** (stated in the test, so nothing new can slip in):
- **F42's interval:** "s(0–14) 1.89 [1.39, 4.82]". The source `a41_readout.json` holds 4.8148 for the upper bound,
  which is 4.81: FINDINGS' 4.82 is one off in the last place. It is kept as frozen, and 02_NUMBERS notes it.
- **Recounted rather than read from one record:**
  - J-opus agreeing on 82 of 84 rows (`l6_report.json`: agreement × rows);
  - the keyword agreeing with the labels on 83 of 84 (42 + 41);
  - B20's "5 of 10" readings (counted from `b20_report.json`).
- **Counted from per-run rows** (no summary holds them; checked against FINDINGS only):
  - Qwen3 30B Instruct's bare answers, 111 of 147 (F16);
  - F1's pinned-format interval [−2, +40];
  - F13's 7 of 19.
- **Recorded only in FINDINGS' own tables** (hand labels whose sheets stay local): L4's 97 of 147 and 1 to 2 of 147
  (F28), and Track C's spot check, 15 of 20 (FC2). For these the source is FINDINGS.
- Three rows of the Nov 4 glance table are in FINDINGS' own words in 02_NUMBERS: F4 ("26 of the 43"), FC2
  ("0 [0, 0]"), FC4 ("[−29, 0]"). The numbers are the same.
