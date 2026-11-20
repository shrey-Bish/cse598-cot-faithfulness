# Session log: the demo's three concepts, phase 1: plans and six mockups, then stop (2026-11-19 22:49 MST)

**By:** Ritik. Branch `trackA-nosol`, from `15601fb` (main, `trackA-nosol`, `origin/main` and `origin/trackA-nosol`
level). The day's third session; the daily: [DAILY_2026-11-19](DAILY_2026-11-19.md). The previous session: Nov 19,
[15:14](2026-11-19_1514_ALL_final-check.md). The results are frozen: the tag `results-freeze-2026-11-18` on
`7e1fdc0`. Presentation work after the freeze: no number, figure or verdict changes.

## 0. Input

A pasted prompt, acted on as Ritik's: a new demo for the 12-minute presentation and the repo, instantly
understandable, interactive, animated and visually distinctive, not templated. Two earlier versions were rejected as
generic (panels, pill chips and badges; a bold headline beside a dot chart on navy with pink and green). Ten beats,
presenter-paced; every number from DATA (compact() of the frozen summaries). The Transformer Explainer is a reference
for its interaction only. **Phase 1:** three concepts (the exam paper, the transit map, the evidence board, or better),
each with a design plan, a check against the generic defaults, and two mockups (beats 2 and 7) at 1920×1080 in
`docs/demo/concepts/` (local, not committed); then stop for Ritik's pick. At most 2 helpers. (The paste ends partway
into phase 2; phase 2 waits for the pick.)

## 1. Plan (22:54)

- `docs/demo/concepts/` gitignored (root `.gitignore`); in it: `make_data.py` writes `data.js` from the tag's page
  (checks the current page's DATA equals the tag's: it does); `render.py` screenshots each mockup at 1920×1080 with
  Playwright; `PLANS.md` holds the three plans.
- Line colors validated with the dataviz palette check (the transit map's teal, ochre and violet pass; red left out of
  the line set after a deutan clash with ochre, kept for buffer stops with a symbol and label).
- Helper 1: concept B (the line map), mockups of beats 2 and 7. Helper 2: concept C (the case board), the same. Me:
  concept A (the answer sheet), then review all six screenshots against the plans, the defaults and the numbers.
  Helpers don't commit and write only in `docs/demo/concepts/`.

## 2. What was made (22:56–23:07)

All in `docs/demo/concepts/` (gitignored; nothing there is committed): `PLANS.md` (the three plans, the check against
the generic defaults, and what changed in each build), the six mockups as HTML and PNG at 1920×1080
(`A_beat2`, `A_beat7`, `B_beat2`, `B_beat7`, `C_beat2`, `C_beat7`), `overview.png` (the six on one sheet), and the
scripts (`make_data.py`, `render.py`, `overview.py`, `C_build.py`).

| concept | the world | signature animation | built by |
|---|---|---|---|
| A. The answer sheet | an optical answer sheet in dropout green; one bubble a run, filled in pencil; the hint a sticky note or a stapled tool slip; red-pen tallies; the checker a second grader's violet stamp | the pencil fill, run by run, then the red pen circles the tally | me |
| B. The line map | a schematic transit map; each hint source a line, the layers stations, a dropped source a buffer stop; the statement a station name board | trains split at the answer junction; a dropped line retracts to its buffer stop | helper 1, my review |
| C. The case board | a steel case board; each source an exhibit in an evidence bag with a chain-of-custody form; yellow evidence markers as the progress | threads pulled taut from exhibit to answer | helper 2, my review |

**My review's corrections (each re-rendered and looked at again):**
- B: the statement in a near-black box with bold white sans (it echoed the rejected version 2), made a station name
  board on the paper; beat 7's statement said "a reviewer corrects 3 of 73" without naming the Olmo reviewer (only
  the two Olmo reviewers defer), now the brief's statement plus "Only the two Olmo reviewers defer; the other four
  keep checking."; beat 2's pasted-output line removed (beat 3's); the 100 read from DATA; "0 of 53" in ink.
- C: in beat 2, 161 dark threads to "its own answer" made the person's hint look strongest; now only runs that ended
  on (C) are taut (1 from the user, 147 from the tool) and the rest hang faint; beat 7's statement generalized to
  "the reviewer", now the brief's plus the same note; the case number shrunk (it read as a hero); the handwriting's
  "1" read as "I", font changed; its sources moved into the concepts folder.
- A (mine): the model row ran off the screen, the red loops touched their captions, the checker's speckled stamps and
  caption wrap were unreadable; fixed.

**Checked on all six (by 23:07):** every number read from `data.js` in the page (three are n − k: 161 of 162,
15 of 162, 70 of 73); no internal code in the visible text (a scan of the rendered text for F, FB, FC, A, B, C, L, R codes, E2,
Gate, Track, judge and channel names: none); no script error; no page text under 20 px. The illustrative question is
ours and marked as such.

**After the freeze (Nov 19, 23:07):** presentation work only. No number, figure or verdict changed; the explainer
page and its DATA are unchanged (`make_data.py` checks the page's DATA equals the tag's: equal). The only tracked
change is `.gitignore`'s line for `docs/demo/concepts/`.

## 3. Stopped here, for Ritik's pick

Phase 1 ends here, as the prompt asks: Ritik picks A, B or C, or a mix. The pasted prompt ended partway into phase 2
("each beat with ONE purposeful animation that shows the finding,"); the rest of phase 2 comes with the pick.

## 4. Checks and push

`tests/test_repo_hygiene.py` and `tests/test_check_links.py`; `tools/check_links.py`; `tools/make_supplement.py
--check`; `tools/export_summaries.py --check`; STATUS and the Gantt; the pre-push check; nothing on `origin/main`
missing here. Results in the commit message. The push: `git push origin trackA-nosol:main trackA-nosol:trackA-nosol`.
