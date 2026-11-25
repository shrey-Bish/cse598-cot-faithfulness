# Session log: the deck's fixes and Phase C (the prep guide) (2026-11-25 10:56 MST)

**By:** Ritik. Branch `trackA-nosol`, from `898cb9c` (main, `trackA-nosol`, `origin/main` and `origin/trackA-nosol`
level). The day's third session. The time in the name is the session's first clock reading (the prompt arrived a few
minutes before it). The daily: [DAILY_2026-11-25](DAILY_2026-11-25.md). The previous session: Nov 25,
[10:13](2026-11-25_1013_ALL_deck-build.md). The results are frozen: the tag `results-freeze-2026-11-18` on `7e1fdc0`.
Two helpers: clip A's fixes; the prep guide. They did not commit.

## 0. Input

A pasted review of both decks, with a prompt, acted on as Ritik's: "Phase B fixes, then Phase C."
1. **Slide 5:** the video at about 75% of the width and the full height under the title, with the two counts in a
   narrow column.
2. **Slide 6:** each recommendation is its headline plus one deciding number, at 14 pt or more; the intervals move to
   the notes.
3. **Slide 4:** "Did thinking make it more honest? Mixed." as one bold line, with short clauses; the numbers move to
   the notes; larger strip labels.
4. **Slide 3:** one line with the three levels, the fixes re-tested on 120 fresh questions, and 352 GPU-hours.
5. **Clip A:** box the whole sentence around the tool mention and hold it longer; replace the dip to black near 7 s
   with a crossfade; rebuild the poster.

Then re-render, re-test, rebuild both decks, push, and write Phase C (the prep guide).

## 1. What was done (10:56–11:01)

**The slides** (`tools/deck/build_deck.py`, mine):
- **Slide 3:** the diagram is shorter ("Reasoning names it?"), and under it one line: "Three levels: behavior across
  12 models; inside the model, by swapping layers' activations; downstream, solver → reviewer → checker. The fixes were
  re-tested on 120 fresh questions with wrong and right hints. 352 GPU-hours on ASU's Sol."
- **Slide 4:** "Did thinking make it more honest? Mixed." in 17 pt bold, then one clause each for Qwen3 8B, gpt-oss
  and Nemotron. The numbers (+64 [+51, +75]; +7 [−1, +16] and −5 [−10, 0]; −14 [−19, −9]) are in the notes. The strip's
  model names are 11.5 pt, with the axes moved so none is clipped.
- **Slide 5:** the video (or the placeholder) is 7.5 × 4.22 in under the title. The column beside it holds 28 of 114
  and 85 of 233 [31, 43%]. The safe-zone test excepts the video: its captions and targets end above the strip.
- **Slide 6:** each recommendation is a 15 pt headline and one 14 pt line. Recommendation 4 is "wrong hints followed
  12% vs 33%; right hints taken 76% vs 91%", plus its exploratory crossover. Every interval is in the notes.
- **The percentages are documented:** in 02_NUMBERS as N150 (84 of 694 (12%), 237 of 713 (33%), 347 of 459 (76%),
  431 of 476 (91%); F41). A test checks that each is its k of n rounded.

**Clip A** (helper 1; `tools/demo_video/`):
- The sentence that holds the first highlighted mention is found by punctuation, with no model words in any script,
  and boxed line by line (three lines, from its start: "Wait but …" to "… expected value.").
- That beat is held 1 s longer; 0.3 s crossfades replace the dips. Clip A is 48.5 s and 12.2 MB, clip B 27.4 s and
  5.0 MB.
- A luma scan found no dark frame (the lowest mean is 195 of 255). I looked at the sentence frame and at clip B's
  three beats.

**Phase C, the prep guide** (helper 2): `docs/presentation/final/PREP_GUIDE.md` (369 lines) and `PREP_GUIDE.pdf` (12
phone-sized pages).
- The run of show; the timing plan (about 130 words a minute, about 260 words a speaker, each section timed
  separately; a 6:00 deck usually runs 6:30–7:00 with hand-offs).
- The cut order:
  1. clip B (a backup already);
  2. slide 4's gpt-oss and Nemotron clause;
  3. slide 3's whys down to two;
  4. slide 6's crossover line;
  5. last, slide 7's "Applies to" column.
- 13 concepts; 30 questions, each with a direct answer, evidence, what's unknown and the backup slide; a rubric
  self-check; what to say if the video won't play; a rehearsal plan.
- Mine: Q7 now says why 38 of 114 and 85 of 233 share units (one run per question per wording on the 120).
- `tests/test_final_deck.py` checks every number in the guide like the slides'.

**After the freeze (Nov 25, 10:56): presentation work only.** No frozen number changed. The only new figures are
slide 6's four percentages: FINDINGS' k of n, rounded, and tested.

## 2. Waiting for Ritik

1. **Play both videos once in PowerPoint,** in Slide Show mode (`final/local/Group10_final_with_video.pptx`), on
   Windows too if possible.
2. **A timed rehearsal:** each speaker's two minutes separately; agree each person's cuts in advance (PREP_GUIDE §2).
3. Upload the local deck to Canvas by Nov 30. Then Phase D (the repo) for Dec 10.

## 3. Checks and push

- `tests/test_final_deck.py` (8, the prep guide's numbers now included), `test_deck_figures.py`,
  `test_presentation_pack.py` (with N150's rounding), hygiene, links and the Gantt: 135 passed.
- `tools/check_links.py`: 0 broken links.
- Slides 3–6 re-rendered and looked at; the strip's labels at slide size; both decks rebuilt (the tracked one 4.57 MB,
  its PDF 3.46 MB; the local one 31 MB, both clips).
- Staged: no clip, still, local deck or template.
- STATUS and the Gantt; the pre-push check; the push: `git push origin trackA-nosol:main trackA-nosol:trackA-nosol`.
