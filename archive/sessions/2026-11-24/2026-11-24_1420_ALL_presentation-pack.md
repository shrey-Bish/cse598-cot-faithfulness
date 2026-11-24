# Session log: the presentation pack (2026-11-24 14:20 MST)

**By:** Ritik. Branch `trackA-nosol`, from `7f53c2f` (main, `trackA-nosol`, `origin/main` and `origin/trackA-nosol`
level). The day's first session log; the morning finished the Nov 23 15:55 session (Show me, pushed at 08:48). The
daily: [DAILY_2026-11-24](DAILY_2026-11-24.md). The previous session: Nov 23,
[15:55](../2026-11-23/2026-11-23_1555_ALL_case-finder.md). The results are frozen: the tag
`results-freeze-2026-11-18` on `7e1fdc0`. Two helpers: methods and the study guide; figures, team and requirements.
They did not commit.

## 0. Input

A pasted prompt, acted on as Ritik's: "THE PRESENTATION PACK: gather everything I need to build the slides, write the
report and prepare for the presentation, in one place."
- **Scope:** gathering and explaining only. No new analysis, no frozen number changes, and no report prose or speaker
  scripts (outlines, facts and explanations only). A dated note goes in today's log; at most 2 helpers.
- **The files:** `docs/presentation/pack/` 00–11:
  - index, story, numbers, methods, figures (slide copies at 1920 px, demo screenshots);
  - slide outline, report outline, related work, prep guide, Q&A bank, team and process, requirements;
  - `PACK.pdf`.
- **The rules:**
  - Every number with "k of n" (and its interval), its finding and its source.
  - Plain names first; exploratory marked.
  - FINDINGS' wording, with the corrected story of the Nov 23 log.
- **Checks:** every number against its source (a test), and the links. Push both branches.

## 1. What was done (14:20–15:47)

**The pack** (`docs/presentation/pack/`, 12 files, 1,990 lines):

| file | by | what |
|---|---|---|
| 00_INDEX | me | the order to read; how the numbers are checked; where a number and its source differ |
| 01_STORY | me | the question; the answer ("mixed"); the five findings with evidence; what's new; limits; a "don't say" table (21 rows) |
| 02_NUMBERS | me | 131 rows: 81 slide numbers in six groups, then every finding at a glance; claim, numbers, interval, finding, source, status |
| 03_METHODS | helper 1 | question sets, hint wordings, the 12 models, compute, Olmo's architecture, patching, both fine-tuning methods, the other fixes, the review pipeline, statistics, pre-registration, labels, judges, the freeze |
| 04_FIGURES | helper 2 | every figure (29 in `docs/paper/figures/`, 7 in the supplement, the deck's 18 slides): what it shows, caption, data source, slide, report section |
| 05_SLIDE_OUTLINE | me | 13 slides in 12:00 (S1–S13), the demo's four moves with keys and fallback shots, 6 backups (B1–B6), what to cut |
| 06_REPORT_OUTLINE | me | abstract to contributions: facts, figures, tables, suggested lengths |
| 07_RELATED_WORK | me | 33 papers in a table and as entries, condensed from RELATED_WORK, with nothing added |
| 08_PREP_GUIDE | helper 1 | 13 concepts (plain words, analogy, how we used it, number, check-yourself); the four moves; fallbacks; rehearsal |
| 09_QA_BANK | me | 28 questions in 7 groups, the hard ones marked |
| 10_TEAM_AND_PROCESS | helper 2 | the tracks, report owners, commit counts, the timeline, labels, AI-use facts |
| 11_REQUIREMENTS | helper 2 | none in the repo: check Canvas |

**Figures and screenshots:**
- `figures/`: 15 PNGs at 1920 × 1080, rendered from the tracked SVGs. These are helper 2's 14 plus `channels.png`
  (mine, for S3).
- `demo_shots/`: 6 screenshots of the four moves. They are gitignored: they show recorded model text.

**PACK.pdf:** files 00–11 then the slide figures; 92 phone-sized pages, 1.9 MB. The figures are recompressed for the
PDF, and the demo shots are left out.

**The number check** (`cot-disclosure/tests/test_presentation_pack.py`, new, 7 tests):
- Each 02 row is checked three ways:
  - its "k of n" and intervals are in its finding's section of FINDINGS (or the summary at the top);
  - its source exists;
  - in a JSON source, each "k of n" is a k and n in one record, and each interval bound is in the file within
    rounding.
- Every "k of n" and interval anywhere in the pack is in 02, FINDINGS or (the finder's counts) TALK_MAP.
- The links resolve; the figures are 1920 wide; the PDF is there and under 5 MB.

**What the check found** (all now stated in the test and in 00_INDEX):
- **One number differs from its source:** F42's "s(0–14) 1.89 [1.39, 4.82]". `a41_readout.json` holds 4.8148, which
  is 4.81: one off in the last place. FINDINGS is frozen, so the number is kept as written and noted in 02.
- **Recounted from their sources:**
  - L6's 82 of 84 (agreement × rows) and 83 of 84 (42 + 41);
  - B20's "5 of 10" readings.
- **Per-run, against FINDINGS only:** F16's 111 of 147; F1's [−2, +40]; F13's 7 of 19.
- **Only in FINDINGS' own tables** (hand labels; the sheets are local): L4's 97 of 147 and 1 to 2 of 147; FC2's spot
  check, 15 of 20.
- **Three glance rows reworded to FINDINGS' own words,** same numbers: F4 ("26 of the 43"), FC2 ("0 [0, 0]"), FC4
  ("[−29, 0]").
- **Sources added after the first pass:** F28 (gate3_table.md, eval_report.json, FINDINGS' L4 table); F32
  (step9_followup.json); F34 (team_c18_unchanged_summary.json); F45 (tradeoff_e2.json).

**Corrected on the way** (my review of the helpers' files):
- 08's rehearsal timed TALK_MAP's older 14 slides; it now follows 05's S1–S13.
- 09's AI-use answer now follows the inventory's own lines.
- 09's "why one model" answer now cites the compute fact in FINDINGS' story (item 6), not an unsourced reason.

**Not found in the repo** (said in the files):
- The course's requirements (page limit, format, rubric, deadlines);
- the reviewer models' temperature;
- LoRA's per-channel data split;
- Gate 3's pass rule restated in full;
- Arsha's and Shrey's own AI use (the inventory's "to confirm" lines);
- the AI uses since Nov 19.

**After the freeze (Nov 24, 14:20): presentation and docs work only.** No number, figure or verdict changed. The pack
copies FINDINGS' numbers with their sources, and reports the one that differs from its source rather than changing
it.

## 2. Waiting for Ritik

1. **Check Canvas** for the requirements (11_REQUIREMENTS lists what to look for).
2. Build the slides from 05; write the report from 06; CONTRIBUTIONS.md from 10; AI_USE.md from the inventory.
3. Decide on the existing deck: rebuild it from TALK_MAP (its order) or follow 05 (new order).
4. The demo screenshots are in `docs/presentation/pack/demo_shots/` (local only).
5. As before: Prompt 2 (the final check, the zip, the tag); publish the seeded runs? a LICENSE? the username in the
   logs?

## 3. Checks and push

- `tests/test_presentation_pack.py`: 7 passed; with the repo's hygiene, link, Gantt and submission tests, 83 passed.
  The full suite was not rerun: no code changed but the new test (it ran last on Nov 24 at 08:47, 1,413 passed).
- `tools/check_links.py`: 0 broken links. `make_supplement.py --check` and `export_summaries.py --check`: pass.
- Privacy: no email, Sol username, key or model text in the tracked pack; `demo_shots/` ignored.
- STATUS and the Gantt; the pre-push check; the push: `git push origin trackA-nosol:main trackA-nosol:trackA-nosol`.
