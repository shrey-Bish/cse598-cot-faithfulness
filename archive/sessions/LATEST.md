# Session log: the v3 deck's three small fixes (2026-11-26 15:20 MST)

**By:** Ritik. Branch `trackA-nosol`, from `358dc12` (main, `trackA-nosol`, `origin/main` and `origin/trackA-nosol`
level). The day's third session. The daily: [DAILY_2026-11-26](2026-11-26/DAILY_2026-11-26.md). The previous session: Nov 26,
[14:24](2026-11-26/2026-11-26_1424_ALL_deck-v3-build.md). The results are frozen: the tag `results-freeze-2026-11-18` on
`7e1fdc0`. One helper (clip C's). It did not commit.

## 0. Input

A pasted review of the v3 deck, acted on as Ritik's. The deck now leads with what we built. Three small fixes:
1. Slide 9: fill it. Headlines at 18 pt and lines at 14 pt, or a small native diagram of where each safeguard sits.
2. Clip C: crop the path `results/labels/…` (beat 3) and "Test 2" (the layers beat) out of frame; rebuild the clip
   and its poster; re-run the clip checks.
3. Slide 3: the four block names at 16 pt, if they fit.

Then rebuild both decks, run the deck tests, push, and report in at most 4 lines.

## 1. What was done (15:20–15:29)

**Dated note (Nov 26, 15:20): presentation work after the freeze. No number changed.**

- **Slide 9** (`tools/deck/slides_v3.py`): both options.
  - Each recommendation is an 18 pt headline and one 14 pt line.
  - Under them, a native strip shows where each safeguard sits: tool → model (2, 3: a prompt line, training) → log
    provenance (1) → checker, re-solving without the tool (4) → user.
  - Row 1's line is shorter ("…named the tool in 0 of 143 runs"); 141 of 145 stays in the notes.
- **Slide 3:** the block names are 16 pt, on two lines. The blocks are 0.16 in taller and the effort band 0.12 in
  shorter. "on ASU's Sol" became "on Sol".
- **Clip C** (helper; `tools/demo_video/record_c.py`, `compose_c.py`):
  - C3's zoom and gold box end before the file path; the overlay scrolls only after the camera has narrowed.
  - C4a's zoom starts below the panel's first line, which carries "Test 2", and cuts straight to its crop.
  - A new sweep (`compose_c.py --sweep`): for every frame of every beat, the page's words inside the camera box are
    tested against the deck's code pattern, plus file paths. No hits in any beat. On the full pages, the same sweep
    finds `L6`, the path and "Test 2", so the test works.
  - The clip: 36.0 s, 9.5 MB. The lowest mean luma is 37.1, the end card. I looked at frames from C3 and C4a myself.

## 2. Checks and push

- Both decks rebuilt: tracked 4.42 MB (with its PDF); local 40.4 MB, three clips.
- The deck, figures, pack, hygiene, links, make_deck, Gantt and submission tests: 161 passed. `check_links.py`: 0
  broken links. The full suite last ran at 14:31 (1,485 passed, 1 skipped); since then only the slide layout and the
  clip scripts changed, and those are covered by the tests above.
- STATUS and the Gantt; the push: `git push origin trackA-nosol:main trackA-nosol:trackA-nosol`.

## 3. Waiting for Ritik

The playback check in PowerPoint (slide 7, backups 24–25); a timed rehearsal per speaker; the Canvas upload by Nov 30.
