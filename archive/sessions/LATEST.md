# Session log: the final deck, Phase A (the storyboard) (2026-11-25 09:20 MST)

**By:** Ritik. Branch `trackA-nosol`, from `5b9956e` (main, `trackA-nosol`, `origin/main` and `origin/trackA-nosol`
level). The day's first session. The daily: [DAILY_2026-11-25](2026-11-25/DAILY_2026-11-25.md). The previous session: Nov 24,
[14:20](2026-11-24/2026-11-24_1420_ALL_presentation-pack.md). The results are frozen: the tag
`results-freeze-2026-11-18` on `7e1fdc0`. Two helpers: the template map and the design diagram; the figure drafts.
They did not commit.

## 0. Input

A pasted note with a prompt, acted on as Ritik's:
- "Read ~/Downloads/DECK_BRIEF.md in full: it's the brief for the final presentation".
- Copy the two ASU templates into `docs/presentation/final/templates/`.
- "Do PHASE A only (the storyboard, with draft renders of the figures, the diagram and the video beats), then stop
  and show me."
- Presentation work after the freeze: no number changes; a dated note in today's log; at most 2 helpers.

The note's deck shape: eight slides in 6:00, on the course's split (the question 1:00; how we tested 1:00; the
strongest finding with the video 2:00; four recommendations and the limits 2:00).

**The brief** (Canvas, Nov 24):
- one .pptx, uploaded by Mon Nov 30;
- the talk Thu Dec 3, Group 10 first: 6 minutes plus 2 of Q&A;
- the rubric: soundness 7, results 5, deployment 4, clarity 2;
- embedded demo videos and the ASU 2026 template;
- Phases A to D, stopping after A.

The files were in `~/Downloads/` under slightly different names (spaces and an em dash): the same files.

## 1. What was done (09:20–09:29)

- **The brief copied** to `docs/presentation/final/DECK_BRIEF.md` (as the brief asks).
- **The templates copied** to `templates/`, local only (gitignored): 11 MB and 6.8 MB, over the 5 MB limit, and the
  second is not ours to publish.
- **[`STORYBOARD.md`](../../docs/presentation/final/STORYBOARD.md)** (226 lines):
  - the eight slides with exact claim titles, times (6:00), speakers and rubric criteria;
  - the backups B1–B8;
  - each main-slide result with its n, interval, comparison, limit and source (the brief's checklist);
  - the figures, the diagram, the template use, the video storyboard;
  - seven decisions for Ritik.
- **Figure drafts** (helper 2; `cot-disclosure/tools/deck/figures.py`): tool vs user (10 model settings), reasoning vs
  answer, the trade-off (marked exploratory), the checker. The ASU palette, an n on every mark, 95% intervals equal to
  the summaries' stored Wilson bounds (asserted).
- **The design diagram** (helper 1; `cot-disclosure/tools/deck/diagram.py`): native PowerPoint shapes on a copy of the
  template, simple (slide 3) and full (B7), rendered by LibreOffice.
- **The template map** (`storyboard/TEMPLATE_MAP.md`): layouts, the safe-zone strip (the bottom 0.845 in), the
  theme's colors, the preheader style.
- **The video storyboard:**
  - Clip A, about 48 s, six beats.
  - Clip B, about 28 s, three beats.
  - Each beat has its state, zoom target and caption.
  - Draft stills with the zoom boxes and captions drawn in are local only (`storyboard/video_beats/`): they show
    model text.
- **The question, by pattern:**
  - On the 120 fresh questions with the tool call's reply, No fix took the wrong hint, its reasoning named the tool
    and its answer didn't, on 28 of 114 questions.
  - The first in the finder's seeded order is mmlupro-11784. It is also the first match of "No fix took it and
    consistency training didn't", so clip B shares it with no choosing.
  - The review team's first drawn item shows the reviewer deferring and the checker flagging.

**Numbers checked against FINDINGS:**
- The brief's: 1 of 162 [0, 3%] and 147 of 162 [85, 94%] (F16); 54 of 54 and 3 of 54 (F15); 53 of 53 (F24).
- Five slide intervals aren't printed in FINDINGS but are stored in the frozen summaries:
  - 141 of 145 [93, 99] and 0 of 143 [0, 3] (`trackB_report.json`);
  - 127 of 162 [71, 84] (`b20_report.json`);
  - 53 of 53 [93, 100] and 7 of 45 [8, 29] (`c15_summary.json`).
  - Phase B adds them to 02_NUMBERS with their paths.
- Not in FINDINGS verbatim (decision 4): Gemma's thinking-on reasoning bar, 138 of 145; the trade-off's end points.
- The clip's 28 of 114 is a presentation count from recorded runs (decision 1).

**After the freeze (Nov 25, 09:20): presentation work only.** No number, figure or verdict changed. The drafts plot
frozen summary numbers; the ones not printed in FINDINGS are listed above for Phase B to add with their sources.

## 2. Waiting for Ritik

1. Read `docs/presentation/final/STORYBOARD.md` and answer its §8 (seven decisions), then say "Phase B".
2. Settle the speakers with Arsha and Shrey.
3. As before: the report (Dec 10, NeurIPS format, 1–3 pages), CONTRIBUTIONS.md, AI_USE.md, Prompt 2.

## 3. Checks and push

- `tools/check_links.py`: 0 broken links. A privacy sweep of the new files: no email, username, key or model text.
- `.gitignore`: the templates, the video beats, `final/video/` and the draft .pptx, all local only.
- STATUS and the Gantt; the pre-push check; the push: `git push origin trackA-nosol:main trackA-nosol:trackA-nosol`.
