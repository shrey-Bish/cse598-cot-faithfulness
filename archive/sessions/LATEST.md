# Session log: the last materials: related work, the report's material, the slide shell, the presentation kit, the submission folder (2026-11-19 10:18 MST)

**By:** Ritik. Branch `trackA-nosol`, from `7e7f340` (main, `trackA-nosol` and `origin/main` level). The day's first
session; the daily: [DAILY_2026-11-19](2026-11-19/DAILY_2026-11-19.md). The previous session: Nov 18,
[20:44](2026-11-18/2026-11-18_2044_ALL_freeze.md). The results are frozen: the tag `results-freeze-2026-11-18` on
`7e1fdc0`.

## 0. Input

A pasted prompt, acted on as Ritik's: the last working session, to finish every remaining piece of material without
waiting for Arsha or Shrey. Its decisions:
- **Teammates' missing pieces** are prepared from the tracked, frozen numbers in Ritik's paths (`docs/paper/`,
  `docs/presentation/`, `docs/submission/`), each said to come from its track; their paths (`docs/trackB/`,
  `docs/trackC/`) aren't edited.
- **The team's words stay theirs:** materials only (figures, tables, bullets with exact numbers, a slide shell, facts
  for questions); no report prose, no slide paragraphs, no speaker notes or scripts. Contributions: a placeholder
  ("Contributions: to be completed before submission"); Ritik writes it.
- **a.** RELATED_WORK: nine references added, each checked on arXiv, with what it found and how our result relates;
  CLAIMS and REPORT: every novelty claim checked against them and reworded where they already show it. What stays
  ours: the authority ladder (dose-response); the readout layers with a second-family replication; where training acts
  inside the model (fine-tuning vs consistency training); the nine-fix trade-off; the review-team results.
- **b.** REPORT complete: every section with bullets, exact numbers, plain names (codes in parentheses), limits, its
  figure or table; Track B's section from FINDINGS_B and B18's table ("prepared from Track B's findings"); Track C's
  from Shrey's bullets as they are; nothing left "waiting".
- **c.** Gate 3's draft statement from PLAN printed word for word in the handoff.
- **d.** Every slide in PLAN's map with a current figure (a missing one made from frozen numbers, house style, plain
  names); then `docs/presentation/deck.pptx`: a title slide, one slide per TALK_MAP entry (its figure and a short plain
  title), a final "Limits and next steps" slide with the limits as short lines from FINDINGS. No paragraphs, no notes.
- **e.** `docs/presentation/TALK_MAP.md` (about 12 minutes, slide by slide: the point, the figure, the explainer scene,
  a time budget; a blank speaker column) and `QA_FACTS.md` (likely questions with the facts and findings to point to;
  no scripted answers).
- **f.** The submission folder: a checklist of every file with its state (ready / to write by us), the contribution
  placeholder, the AI-use inventory's "to confirm" lines listed, and one command that assembles the submission zip
  (report, slides, figures, the explainer, the code link, the bundles' sha256s) once our parts are written.
- **g.** The README: a "Start here in five minutes" opening; the rest as is.
- **h.** Sol and the feeder: no action.
- **Limits:** at most 2 helpers (helpers don't commit); the full suite once, at the end; push `trackA-nosol` and
  `main` only.

## 1. Plan (10:18, before any helper starts)

State at the start: `git fetch` (10:18) shows no commit on `trackB-main` or `trackC-main` that `main` lacks, so there
is nothing to merge. Track B's report bullets (`docs/trackB/REPORT_B.md`) don't exist; Track C's
(`docs/trackC/REPORT_C.md`) were merged into REPORT §8–§9 on Nov 6. Every slide in PLAN's map but 13 has a figure in
`docs/paper/figures/`; slides 6 and 8's (`bare_after_call.png`, `b17_effort.png`) were made Nov 1 and Nov 3 by
`tools/slide_figures.py` and are there. `docs/presentation/` doesn't exist yet. python-pptx 1.0.2 is in `.venv`.

1. **Helper A (a and b):** RELATED_WORK's nine references, each looked up on arXiv (the abstract page: its title,
   authors and date against the prompt's), an entry only where they match; the novelty claims in CLAIMS and REPORT
   checked against them; REPORT completed section by section from FINDINGS, FINDINGS_B, FINDINGS_C, B18's table and
   `REPORT_C.md`; nothing marked waiting.
2. **Helper B (d and e):** the slide map's figures checked (each exists, plain names, the house style); a missing one
   made only from frozen, tracked numbers; TALK_MAP and QA_FACTS; the deck built by a script, `tools/make_deck.py`
   (tests first), from TALK_MAP's table, so the deck and the map can't drift.
3. **Me (c, f, g), while they run:** the submission folder (its checklist, `CONTRIBUTIONS.md`'s placeholder, the
   "to confirm" lines, the bundles' sha256s as a tracked file, and `tools/make_submission.py`, tests first, which
   refuses to build the zip while a part the team writes is missing); the README's opening.
4. **Then I review both helpers' work against FINDINGS, every number against the frozen tag** (`git show
   results-freeze-2026-11-18:<file>`); fix what I find; the logs, TODO and the Gantt; the full suite once; commit; the
   supplement after the commit if CLAIMS changed; push.

**Rulings (10:18):**
- **"Nothing left waiting" and Gate 3:** Gate 3's final statement is Ritik's to approve (Nov 20). REPORT §7 carries
  PLAN's draft word for word, marked "draft, for Ritik's approval by Nov 20": a decision of Ritik's, not a result
  waiting. Cost if wrong: one heading to change on Nov 20.
- **A reference that doesn't check out isn't cited:** an arXiv number whose page shows another title (or none) goes
  under RELATED_WORK's "Not verified" with what the page showed, and no claim is reworded against it. Cost if wrong:
  a real paper left out until someone finds its right number.
- **Slides 6 and 8 have figures** (made by Track A's script from Track B's tracked rows), so nothing new is drawn for
  them unless the check finds one stale; Arsha's words for those slides stay hers.
- **The deck is built, not hand-made:** `tools/make_deck.py` reads TALK_MAP's table, so a figure or title changed in
  the map changes the deck the same way. Cost if wrong: none beyond the script.
- **The supplement:** `tools/make_supplement.py` checks every number in CLAIMS against FINDINGS (its EVIDENCE.md). If
  CLAIMS changes today, the supplement is regenerated after the work's commit, from a clean tree, and that change gets
  a dated note here (it changes no number; the tag keeps the frozen supplement).
- **The full suite once, at the end;** the helpers run their own tests.

## 2. What the helpers did (10:19–10:28)

- **Helper A (a, b):** `docs/paper/RELATED_WORK.md`, `CLAIMS.md`, `REPORT.md` only.
  - **The nine references:** all nine ids match their arXiv pages (title, authors, v1 date); FACE-Eval found by search
    (arXiv 2608.29464, Gema et al., which introduces it); BCT is arXiv 2403.05518. Four titles given were short forms of
    the arXiv titles (Assertion-Conditioned Compliance, Trust Asymmetry: "Same Payload, Different Channel: ...", When
    Tools Hurt, Unspoken Hints). Each entry: "Did:" from its abstract, "Relates:" agrees / extends / differs with our
    entries. Chen et al.'s three future-work directions kept (tool use; training by SFT or RL; probing activations).
  - **Novelty:** no "first" wording existed; "Prior work" bullets added to CLAIMS 1.1, 1.2, 1.4, 1.5, 1.7, 2.2 and
    B15, and to REPORT §1's new contribution bullets, §4–§7, §11 and §12. Not claimed as ours any more: unnamed hint use
    (Chen; Unspoken Hints; Walden and Wanner), a tool cue said less than a user's (FACE-Eval), a source over a user and
    a dose in authority (Authority Bias), consistency training as a method (BCT), tool evidence overturning right
    answers (When Tools Hurt). What stays ours, as worded: the user's own claim set against the tool channels in one
    model and day (the ladder, F35, F40); the readout layers and heads and their replication in a second family (F11,
    F26, F32, F36); where training acts, fine-tuning in the reasoning (F39) and consistency training before the readout
    (F42); the measured set of fixes and their trade-off (post hoc); the review team (F18–F34, FC1–FC4).
  - **REPORT:** every section with bullets, plain names, limits and its figure or table; §4 "prepared from Track B's
    findings, FINDINGS_B and B18's table, Nov 19; Arsha's words to come"; §8–§9 left as Shrey's bullets (REPORT_C.md
    unchanged since Nov 6), with a table line and a limits line; §7's "Waiting:" became "Read, and not run" (reasons
    from PLAN's freeze page) and Gate 3's draft, word for word, "for Ritik's approval by Nov 20".
- **Helper B (d, e):** `docs/presentation/` (TALK_MAP, QA_FACTS, `deck.pptx`), `tools/make_deck.py` and its test.
  - Every slide in the map has its figure (2000x1125 PNG with SVG and CSV; `test_slide_figures.py` 18 passed); none
    made or redrawn; slides 6 and 8's are there. TALK_MAP: 14 rows (title, 13 slides), 12:00. QA_FACTS: 12 questions.
  - The deck: tests first (RED on the missing module, then 13 passed); 3.6 MB; rendered and looked at.

## 3. My review (10:28–10:35): every number against the tag, every paper against its own text

- **Numbers:** a script compares every number added today (`git diff`) in REPORT, CLAIMS, RELATED_WORK, TALK_MAP,
  QA_FACTS and the README with the frozen sources (`git show results-freeze-2026-11-18:` FINDINGS, FINDINGS_B,
  FINDINGS_C, PLAN, REPORT_C, the tables, the frozen REPORT/CLAIMS/RELATED_WORK). Missing: none, but RELATED_WORK's
  arXiv ids, A-CC's two percentages (checked in its text) and three numbers written with "-" for "−" (fixed). CLAIMS
  by the supplement's own check: 244 numbers, the same 10 known mismatches, 12 source problems.
- **The papers, a second pass** (arXiv's API for titles, authors and dates; a text search of five papers' full HTML):
  - **Corrected:** FACE-Eval already varies reasoning effort (on GPT-OSS) and tests a source-attribution prompt, so
    RELATED_WORK and REPORT §11 no longer list them as our extensions (ours differs in measure: F37, F25); what stays
    ours there: thinking on and off in the same weights (F29) and whether the final answer names the source (their
    answer judge labels only the side taken). CLAIMS' B15 line said FACE-Eval measures "verbalization, not following":
    it measures both; reworded.
  - **Corrected:** Syed and Yasaei's patching recovers the channel an instruction arrives by; it doesn't separate source
    deference from user agreement (that is Kumar and Chopra's). CLAIMS 1.4 and REPORT §1, §5.
  - **Made exact:** Kumar and Chopra's untested cost now quotes the paper ("does not test whether the models still
    benefit from correct source information after the intervention"); BCT's quotes "we always bias towards incorrect
    answers"; BCT has 7 authors, not 8; "1 and 2 of 147" was "1 to 2" in F28; "is the arbitration problem" became "a
    form of" (CLAIMS 1.5); "address" became "speak to" (REPORT §11, Chen's directions).
  - **Confirmed in the text:** Chen's three directions, verbatim; A-CC's 36.3% (confident user assertions) and 27.8%
    (function-sourced); Authority Bias's four wordings and Qwen3.5 with thinking off; FACE-Eval's models include Olmo 3
    Think and GPT-OSS. Walden and Wanner, Unspoken Hints, Zhao et al. and Syed and Yasaei rest on their abstracts.
- **TALK_MAP:** slide 5's kappas were the human-vs-AI-rater ones (0.63, 0.54), not the Gate 2 rule's (judges'
  majority 0.472, 0.234): corrected; slide 8 "0 of 143" made "0 of 143 followed runs name it"; slide 10 "+0.68" given
  its unit, logits. **QA_FACTS:** one bullet run into another (item 3) split; item 2's keyword counts labelled; item 5
  (related work) filled with the checked facts, the disagreements (A-CC, Syed and Yasaei) and its limits.
- **The deck, looked at slide by slide** (LibreOffice to PDF to PNG): slides 9–12 put two figures side by side, each too
  small to read. Tests first (3 failed), then one figure a slide: the row's first on the slide, the second on a backup
  slide after "Limits and next steps" ("(backup)" in its title); 13 passed; all 18 slides looked at again, readable.

**Rulings (10:35):**
- **The two-figure slides:** the map's first figure stays on the slide; the second goes to a full-size backup slide.
  Cost if wrong: the team moves a backup slide up (TALK_MAP's header says how).
- **"What stays ours":** Ritik's list named "the authority ladder (dose-response)"; Authority Bias (Kumar and Chopra)
  already reports compliance rising with the note's authority, so the dose-response isn't claimed as ours: what stays
  is the user's own claim set against the tool channels in one model and day (F35, F40). "The nine-fix trade-off" is
  worded "the measured set of fixes" (no entry counts nine). Cost if wrong: two phrases for Ritik to restore.
- **README's opening:** five findings in plain words from the story's five lines and FINDINGS, every number checked;
  finding 5 says "the solver's trace" (F18's table: the private reasoning beside the answer), not "the tool's".

## 4. Changed after the freeze (dated notes, CHECKIN §10)

- Changed after the freeze (Nov 19, 10:35): CLAIMS' and REPORT's positioning, from claims stated without prior work
  to "Prior work" bullets that say where nine checked papers already show a result, because Ritik asked for honest
  positioning against them. No number, figure or verdict changed; CLAIMS keeps its 244 numbers and 10 known mismatches.
- Changed after the freeze (Nov 19, 10:35): REPORT's "waiting" marks, from "Waiting:" (B1R2, Gate 3) to "Read, and not
  run" with PLAN's draft of Gate 3's statement word for word, because every result was read by Nov 13; the statement
  stays Ritik's to approve (Nov 20).
- No figure changed: the deck uses the frozen figures' files byte for byte (its tests compare hashes).

## 5. The checks (CHECKIN §6)

- **The full suite, once:** 1,238 passed, 1 skipped (10:37–10:48; 24 new today: `test_make_submission.py` 11,
  `test_make_deck.py` 13).
- **Links:** 0 broken, 0 missing RUNBOOK scripts. **Export:** numbers only. **The Gantt:** regenerated (144 rows).
- **The supplement's check:** 42 rows, none unverified, no log outside the ledger; CLAIMS 244 numbers, 10 mismatches
  (the known ones), 12 source problems. CLAIMS changed, so the supplement is regenerated after this commit, from a clean
  tree (the ruling in §1), and committed next.
- **The bundles:** dry runs B 51 files, 73.8 MB; C 43 files, 31.3 MB. `make_submission.py --verify-bundles`: the three
  Nov 18 bundles on this Mac match `BUNDLES.sha256`. `make_submission.py --check`: 4 pieces ready, 4 to write by us
  (the report, the slides, the contributions, the AI-use disclosure).
- **Gate 3's block in REPORT §7** equals PLAN's draft word for word (compared by script).

## 6. For Ritik

- **Gate 3's final statement:** approve or change PLAN's draft (Nov 20); REPORT §7 carries it word for word.
- **To write by us:** the report's prose (draft Nov 22), the slides' words (the shell's titles are drafts too), the
  contribution statement (the placeholder), `AI_USE.md` from the inventory and its five "to confirm" lines (Nov 22),
  the rehearsal (Nov 23), the presentation and the report (Nov 24); then `make_submission.py` builds the zip.
- **Two wordings to check:** "the authority ladder (dose-response)" isn't claimed as ours (Authority Bias reports a dose
  in authority); "the nine-fix trade-off" is worded "the measured set of fixes" (§3's rulings).
- Sol's read-only check and the feeder: Ritik's own, no action here.
