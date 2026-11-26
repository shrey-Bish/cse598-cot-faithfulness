# Session log: the final deck, version 3, Phase A (the storyboard) (2026-11-26 13:33 MST)

**By:** Ritik. Branch `trackA-nosol`, from `c1e7734` (main, `trackA-nosol`, `origin/main` and `origin/trackA-nosol`
level). The day's first session. The daily: [DAILY_2026-11-26](2026-11-26/DAILY_2026-11-26.md). The previous session: Nov 25,
[10:56](2026-11-25/2026-11-25_1056_ALL_deck-fixes-prep.md). The results are frozen: the tag
`results-freeze-2026-11-18` on `7e1fdc0`. Two helpers: the number check (read-only); clip C's stills. They did not
commit.

## 0. Input

A pasted note, acted on as Ritik's. The current deck tells a measurement study. Version 3 leads with what we built
(inside the model, trained fixes, the multi-agent check), gives the cross-model testing one slide, and adds a video of
training and the layers.
- **The brief:** `~/Downloads/DECK_V3.md`, read in full. Its rules are DECK_BRIEF's, plus "lead with what we built".
- **The deck:** Ritik's latest, `~/Downloads/Group10_final_with_video.pptx`, becomes the local deck first.
- **Scope:** Phase A only: the storyboard, draft renders of slides 3–6 and 8, and clip C's stills. Then stop.
- **Rules:** presentation work after the freeze; no number changes; a dated note in today's log; at most 2 helpers.

## 1. What was done (13:33–13:50)

**Dated note (Nov 26, 13:33): presentation work after the freeze. No frozen number, figure or verdict changed.** The
drafts plot numbers read from tracked summaries or FINDINGS' own k of n. Where the brief's wording didn't match its
source, the drafts follow the source, and the storyboard lists each case.

**The local deck:**
- Ritik's Nov 26 deck is now `docs/presentation/final/local/Group10_final_with_video.pptx`. It is gitignored; its
  sha256 starts `412922c9892f019f`, the same as the copy in Downloads.
- Ours from Nov 25 stays beside it as `Group10_final_with_video_v2_2026-11-25.pptx`.
- What Ritik changed: native charts with Wilson error bars (tool vs user, reasoning vs answer, the trade-off, the
  review team), ten main slides and twelve backups. Their style is kept.

**The drafts** (`cot-disclosure/tools/deck/`, mine):
- **`charts.py`:** native bar charts with custom error bars from absolute bounds, and per-bar colours.
  - A fixed plot area, so rows and columns sit where the slide expects; names and counts are drawn as text beside
    the rows, because LibreOffice drops crowded category labels.
  - Helpers that give each row's or column's position.
- **`draft_v3.py`:** slides 3, 4, 5, 6 (two versions) and 8 on the ASU template. Every count is read from a
  summary; each Wilson interval is computed and checked against the stored or printed bounds.
  - The .pptx is local (`storyboard/draft_v3.pptx`).
  - Renders: `docs/presentation/final/storyboard/v3/` (numbers only).
  - Every render was looked at; fixes were made for crowded labels, a title wrapping into the next line, a block
    overflowing, and one bottom line reaching the reserved strip.

**The number check** (helper 1, read-only): about 60 numbers, about 50 exact matches. Six items differ from the
brief, and the drafts follow the sources:
- the 42% → 12% pools the user's guess with both tool channels (82 + 130 + 85 = 297 of 703; checked in `a40_e2.json`);
- "within 4 points" fails for consistency + instruction (−4.3);
- "no less than the instruction" should be "no difference detected";
- +0.68 and "layers 0–14" are two results;
- only two reviewers had all four views;
- only the two Olmo reviewers defer.

The effort band's sources were found and checked here: `method.json` 352.47 GPU-hours, 271 GPU jobs, 479 labels and
12 models; the ledger, 31 pre-registered; the tag dated Nov 18, 21:03.

**Clip C** (helper 2; `tools/demo_video/record_c.py`, no model text):
- **The question,** chosen by the page: Show me → "the fix held" with Consistency-trained selected, first in the
  seeded order. That is mmlupro-11784, and the page shows 26 of 112.
- **The stills:** 8, plus a contact sheet and a manifest, in `storyboard/video_beats/clipC/` (gitignored).
- **C3** is a hand-labelled Fine-tuned run on another question (mmlupro-4588, pasted tool output; in F45's sample).

**The storyboard:** `docs/presentation/final/STORYBOARD_V3.md`:
- the 11 titles in 6:00;
- the renders;
- what the check changed;
- the effort band's sources;
- clip C's beats with zoom targets and captions;
- what Phase B must fix on the stills;
- six decisions.

## 2. Waiting for Ritik (STORYBOARD_V3 §6)

1. Slide 6's measure: "wrong-hint" (pooled, recommended) or the two tool channels charted separately.
2. Slide 6's chart: A (as briefed) or B (two panels, recommended).
3. Slide 8's title: "Two of six reviewers defer to the tool; a checker doesn't".
4. Clip C's beat 3: keep it on another question, captioned so, or cut it.
5. The speakers: the brief's split (2:55, 1:15, 1:50) or contiguous (1:35, 2:35, 1:50).
6. The effort band: keep 479 and 5 as worded.

Then Phase B: the deck from Ritik's local version, clip C, the checks, and TALK_MAP and PREP_GUIDE.

## 3. Checks and push

- Tests (the deck, figures, pack, hygiene, links, Gantt, make_deck, submission): 158 passed, **1 failed, expected**.
  - The failure is `test_the_local_deck_embeds_both_clips`: the local deck is now Ritik's (23 slides), and the
    tracked deck is still ours from Nov 25 (21 slides).
  - The test is unchanged. Phase B rebuilds both decks from the local version, and it passes again then.
  - It runs only where the gitignored local deck exists.
- `make_supplement.py --check` and `export_summaries.py --check`: pass.
- `tools/check_links.py`: 0 broken links.
- Privacy: no email, Sol username, key or model text in tracked files. The stills, the draft .pptx and both local
  decks are gitignored.
- STATUS and the Gantt; the pre-push check; the push: `git push origin trackA-nosol:main trackA-nosol:trackA-nosol`.
