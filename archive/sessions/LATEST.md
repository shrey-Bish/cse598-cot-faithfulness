# Session log: the results demo, slide 5's figure, Gate 3's draft, the freeze and the submission prepared (2026-11-13 13:36 MST)

**By:** Ritik. Branch `trackA-nosol`, from `1dfd6b8`. The day's third session (the first two:
[09:37](2026-11-13/2026-11-13_0937_A_l6-judge-reading.md), [11:00](2026-11-13/2026-11-13_1100_A_b1r2-freeze-wording.md); the daily
[DAILY_2026-11-13](2026-11-13/DAILY_2026-11-13.md)). Interrupted Nov 13 (a network error, then a usage limit) and continued
Nov 14 from 20:08 (§8; the daily [DAILY_2026-11-14](2026-11-14/DAILY_2026-11-14.md)).

## 0. Input

A pasted prompt ("Prompt 1: the demo and the remaining work, run once"; a second, daily prompt was pasted with it, for
later days). Decisions in it, as Ritik's:
- **a. A final results demo:** one self-contained HTML file, no network, built by `tools/build_demo.py` into
  `docs/demo/index.html` (tracked, numbers only) from the tracked numbers-only summaries and FINDINGS; the build fails if
  a number it needs is missing. Sections 0–6 following the story; every chart with its F-number, X of Y, 95%
  intervals and the reading's words; exploratory items marked. Example outputs only from a local, gitignored
  `results/demo/examples.json`, drawn by a fixed seed from labelled rows (L6, L4). Tests: every number equals its
  summary; no network request; no text field in the tracked HTML.
- **b.** Slide 5's figure (F3), from tracked numbers, in the house style.
- **c.** Gate 3's final statement (due Nov 20): a draft in PLAN for Ritik's approval.
- **d.** The freeze (Nov 18), prepared: a written procedure in CHECKIN; §9's Nov 18 row pointing to it.
- **e.** The submission (Nov 19–24), prepared: the folder's structure; a factual AI-use inventory (facts only).
- **Limits:** at most 2 helpers (they don't commit); the full suite once, at the end.

## 1. Plan (13:36, before any helper starts)

1. **Me, first:** `cot-disclosure/results/demo/` made a produced-data folder (gitignored; the pre-push check refuses
   it), test first, so no example text can reach GitHub.
2. **Helper A:** the demo: `tools/build_demo.py`, its tests, `docs/demo/index.html`, then
   `tools/demo_examples.py` (writes the gitignored examples file). No commit.
3. **Helper B:** slide 5's figure of F3 (`docs/paper/figures/`), from tracked numbers, with its test. No commit.
4. **Me:** c (Gate 3's draft in PLAN), d (the freeze procedure in CHECKIN, §9's Nov 18 row), e (the submission folder's
   structure and the AI-use inventory); then the demo checked by eye at presentation size, light and dark, section by
   section, and anything cluttered fixed.
5. **Then:** the README links the demo; the docs, logs, TODO and the Gantt; the checks; the full suite once; the push.

## 2. The demo's examples kept off GitHub, test first

- `cot-disclosure/results/demo/` is now a produced-data folder: in `cot-disclosure/.gitignore`, and in
  `tools/prepush_check.py`'s list (`PRODUCED`), so a push carrying `results/demo/examples.json` is refused.
  `tests/test_repo_hygiene.py` gained that path first and failed; then 11 passed.
- **Ruling (mine):** the build writes two pages. `docs/demo/index.html` (tracked) never holds example text; when
  `results/demo/examples.json` exists, it also writes `results/demo/index.html` (gitignored), the same page with
  the examples panel. The prompt asks both that the build read the local examples "if present" and that no text reach
  the tracked HTML; two outputs satisfy both. If wrong: one panel to move.

## 3. Gate 3's final statement, a draft (13:40), for Ritik's approval

In PLAN's Gates, under Gate 3, marked "Draft ... for Ritik's approval. Not marked". Every number as read in F28, F38,
F41, F43, F44 and F45; nothing computed.
- **The gate: met.** All four trained versions on the 30 (F28); on E2, the powered replication for LoRA (−7
  [−11, −3]) and the instruction (−9 [−14, −4]), and LoRA + note, A40 and A40 + note by the same rule.
- **The stricter bar (beating the instruction on following at no cost to correct hints): not met by any fix,** each
  stated with its numbers (LoRA matches; A40, A40 + note and LoRA + note trade acceptance; the wrapper alone no
  effect; B1 and B1R2 "ignores tools").
- **Beside it, not part of the gate:** L6's line with its limits (F45); F39 and F42 inside the model. Limits: one
  model, one training run a version, keyword hiding, the 30's comparisons with the instruction not pre-registered.
- The line before it ("nothing it waits on is left but B1R2's replication") now says B1R2 was read Nov 13.

## 4. The freeze procedure (14:12): CHECKIN §10

- **What "frozen" means:** no new runs on any account; the F/FB/FC entries, summaries, figures and the demo final;
  any later change with a dated note (`Changed after the freeze (<date>, <time>): ...`) in its F-entry and the day's
  log; what didn't run keeps its reason.
- **The day, in order:** nothing runs (three accounts; the feeder's stop is Ritik's, Nov 16); the merges (§8); the
  supplement and the demo rebuilt; §6 in full; final bundles A, B and C with `--verify` and each bundle's sha256 in
  the log (A was 1,744 MB at Nov 13's dry run; the labels in no bundle); the annotated tag
  `results-freeze-2026-11-18` on `main` after the push, under Ritik's identity (**a tag push is new: Ritik's go
  that day**); the freeze log.
- Checked: the pre-push hook peels a pushed tag to its commit (`git rev-list <sha> --not --remotes`), so a tag on a
  commit already on `main` passes. The only earlier tag, `progress-oct-2026`, is a lightweight one.
- §9's Nov 18 row points to §10; §4's freeze bullet too; the header.
- **A slip, fixed:** I typed 13:44 into §10's first line before running `date`; it printed 14:12, and the line says
  14:12.

## 5. The submission prepared (14:13)

- [`docs/submission/README.md`](../../docs/submission/README.md): what goes in (report, supplement, slides, the demo,
  the code link at the freeze tag, the contribution statement, the AI-use disclosure), where, who, by when, the state
  on Nov 13, and the folder at Nov 24. The statement and the disclosure are not created: the team writes them.
- [`docs/submission/AI_USE_INVENTORY.md`](../../docs/submission/AI_USE_INVENTORY.md): facts only, each with where the
  repo records it: Claude Code (code, tests, analyses, docs; its sub-agents; the 7 re-look labels mapped to categories
  at Ritik's request, Nov 4 21:24; the no-attribution rules, Nov 5–6); Claude in chat for planning; ChatGPT 5 Astra
  High as AI rater 1 (L3, L4 part 1, Nov 3; corrected Nov 4 17:51); the LLM judges (Nov 4: J-opus, J-qwen, J-olmo,
  AI1; Nov 13: J-opus on L6); the models studied, kept apart as subjects; what the repo records as done by hand. Lines
  the repo doesn't record are marked *to confirm* by the member they name (when Claude Code use began; which prompts
  came from Claude in chat; Arsha's and Shrey's own use).
- PLAN's submission checklist: a row for the demo; the folder's row and the disclosure's row link both files.

## 6. Slide 5's figure of F3 (helper B; placed in the docs at 14:43)

- `docs/paper/figures/private_vs_final.{png,svg,csv}` (`tools/slide_figures.py`, `fig_private_final`; 16:9, the house
  style). Panel (a), Test 1 per model and all three: private reasoning 66, 71 and 71 of 72 (208 of 216), final answer
  0, 0 and 8 of 72 (8 of 216), the private keyword with no hint beside it (22, 18 and 2 of 72). Panel (b), Test 2 where
  the tool's hint won: private 16 of 17, final 6 of 17. Wilson 95% whiskers; F3 in the title and the note.
- Every number from `docs/labeling/RESULTS_SUMMARY.json` (key in the CSV's `source` column). From F3's text only:
  "Nov 4", "0.6" and "all six cells" in the note (L3's verdict). Left out: the pinned-format final-answer rates (no
  tracked numbers file holds them; `base_format.py --report` reads gitignored runs).
- `tests/test_slide_figures.py`: 3 new tests (written first), 16 passed. No existing figure changed.
- Checked by eye (the PNG): no overlap. The docs that said "no figure for F3" now point to it: PLAN (the freeze page,
  the slide map, §6's row, REPORT's waiting list), REPORT §6 (F3 and L3), WAITING.md, ONE_PAGE, FINDINGS F3 (a
  "Figure" line), `results_at_a_glance` (.md, .csv), TODO D14.

## 7. The demo (helper A)

- **Files:** `tools/build_demo.py`; `tools/demo_page/` (template.html, demo.css, demo.js, examples.html, inlined at
  build time); `tools/demo_examples.py`; `tests/test_build_demo.py` (13) and `tests/test_demo_examples.py` (4),
  each seen failing first. Built: `docs/demo/index.html` (about 337 KB, tracked) and, gitignored,
  `results/demo/examples.json` (9 examples) and `results/demo/index.html`.
- **Every number** sits in one data block with its summary path and key (or, for the per-layer swaps, the loader
  `slide_figures.a18_rows` and its row); the test recomputes each (over 300). A missing summary, key or quoted FINDINGS
  sentence stops the build (exit 1). No request but `file:`; the only URL in the page is the SVG namespace.
- **Screens:** 0 the question, the tracks and the models; 1 tools against users (13 model and setting rows, F40's
  authority dose with B16, FB1's R2); 2 the bare answer (F15, F16, F29, C4, F25) and the title question "answered
  mixed", stamped "not a yes" (F29, F37, FB1); 3 inside the model (F11, F26, F32, F36; F39 and F42's swaps); 4 between
  agents (the diagram; six reviewers and C15; the checker 53 of 53, 7 of 45, floor 7 of 100; C16–C18; F44's wrapper and
  FC3's tag, no effect); 5 the fixes on E2 (the trade-off scatter and the Acc(p) slider, both stamped exploratory, post
  hoc; the keyword bars with L6's hand-label points and L6's line with its four limits; B1R2 beside B1); 6 story item
  7 as written, how we worked, AI use, limits.
- **The examples draw** (seed `cse598-demo-examples-2026-11-13`): L3, Ritik's sheet (3 rows: the only labelled sheet
  with private text), L6 (2 LoRA, 2 instruction), L4 part 1 (2 LoRA); each marked "illustrative, drawn by seed".
  Read-only on every source (hashes checked in the test).
- **The helper's rulings:** L3's private excerpts for the side-by-side (L6 and L4 hold the final answer only); C17's
  part (a) left out of the cue chart (C16, C17 (b), C18 kept); B1's 5-point limit as 0.05 in the page's script
  (`provenance_job.MARGIN`); the 82 of 84 computed from `l6_report.json` (agreement 0.976 × 84).

## 8. Interrupted twice; resumed Nov 14

- **Nov 13, found at 14:39:** both helpers stopped on a network error (the API server unreachable). Helper B's figure was
  on disk; helper A had written nothing yet. Both resumed with their context.
- **Later on Nov 13** (after helper A's 15:03 build): a usage limit stopped helper A while it re-took its screenshots.
- **Nov 14, 20:08:** Ritik: "continue, and resume the agents". Helper A resumed and finished (helper B had finished on
  Nov 13).

## 9. The demo checked by eye (Nov 14, 20:09–20:14)

- All seven screens at 1920×1080, light and dark (Playwright, Chrome): no request but `file:`, no console error, no
  screen scrolls. The numbers on screen checked against FINDINGS (Gate 2's tool − user column, FB1's 10 R2 readings
  (5 beyond, 1 authority more, 4 no difference), F15, F25, F29, F37, FB1's −14, F11's layers, F39 and F42's swaps, the
  checker's tiles, C16–C18, the E2 trade-off, the A40 crossing 0.36 [0.22, 0.50], L6's 37/42 and 18/42, B1 and B1R2).
- B1's and B1R2's shaded limits checked at 2× zoom: acceptance [−5, …], no-hint accuracy [−5, +5], as the rule reads.
- **One fix:** the Acc(p) chart listed each system's value at the slider's p beside the lines' right ends (p = 1); it
  now says "at p = 0.50:" above them (`demo.js`). Rebuilt; the keys work (→ moves on, `t` switches the theme);
  33 tests passed (the demo's 17, the slide figures' 16).
- **Left as they are:** some empty space on screen 0 and under screen 2's left chart; small type in the captions and
  source lines (the headings, labels and values are large); s6's limit "(F38)" is FINDINGS' own wording (F40's limits).

## 10. The docs

- **README:** "The results demo" (open `docs/demo/index.html`; the keys; how to rebuild; examples local only); the
  grader's row names it.
- **TODO:** D15 (the demo) done; D14 (slide 5); G3 (the draft); D5 (the procedure); D13 (the folder); the header.
- **PLAN:** the header; the freeze page (Gate 3 drafted; slide 5 made; Ritik's dates). **ONE_PAGE:** the header, the
  presentation line, the freeze table (Gate 3's draft, the demo), Ritik's dates. **FINDINGS:** the header; F3's figure.

## 11. Needs Ritik

- **By Nov 20:** approve or change Gate 3's draft (PLAN, Gates). **Nov 16:** stop the feeder. **Nov 18:** the freeze by
  CHECKIN §10; the tag `results-freeze-2026-11-18` waits on your go that day. **By Nov 22:** the AI-use inventory's
  *to confirm* lines (when Claude Code use began; which prompts came from Claude in chat); Arsha and Shrey add theirs.
- **Before Nov 24:** open the demo on the presenting laptop with Wi-Fi off; the local page with examples is
  `cot-disclosure/results/demo/index.html` (on this Mac only).

## 12. The checks (Nov 14, 20:15–20:27)

- **The full suite once** (20:15–20:26): **1,166 passed, 1 skipped** (1,146 on Nov 13 + 20 new: the demo's 17, slide
  5's 3). No leftover pytest of ours before it.
- Links: 0 broken, 0 missing RUNBOOK scripts. The export: numbers only. The Gantt: `--dry-run` passes; STATUS and the
  Gantt regenerated. Bundles (dry run): B 51 files, 73.8 MB; C 43 files, 31.3 MB.
- No example text in the tracked page: of 53 snippets sampled from `examples.json`, 0 in `docs/demo/index.html`, 25
  in the local page.
- **The supplement:** 42 rows, none unverified, no log outside the ledger; CLAIMS 10 mismatches as before. Source
  problems 13 before the commit: the new one is F3's figure, "on disk, not tracked", which the commit clears; so the
  supplement is regenerated after it, in its own commit (as on Nov 13).
