# The final deck, version 3: storyboard (Phase A, Nov 26)

**By:** Ritik (with Claude Code; two helpers: the number check and clip C's stills). Brief: `~/Downloads/DECK_V3.md`
(not in the repo; its rules are DECK_BRIEF's, plus "lead with what we built"). Presentation work after the freeze: no
frozen number changed. Phase A only: the titles, draft renders of slides 3, 4, 5, 6 and 8, and clip C's beats with
stills. Phase B (the build and clip C) waits for Ritik.

**The local deck is Ritik's Nov 26 version** (`final/local/Group10_final_with_video.pptx`, gitignored; sha256 starts
`412922c9892f019f`, the same as `~/Downloads/`). Ours from Nov 25 is kept beside it as
`Group10_final_with_video_v2_2026-11-25.pptx`. Ritik's version has native charts with Wilson error bars (tool vs user,
reasoning vs answer, the trade-off, the review team), ten main slides and twelve backups. The drafts below use its
style: native, editable charts (`tools/deck/charts.py`), maroon for the tool or the trained model, gold for the user or
the baseline, near-black for the checker, Arial, labels 11 pt or more, an interval on every bar, the count beside
each label.

## 1. The eleven slides (6:00)

| # | Title (draft) | Time | Clock | Speaker (brief's) |
|---|---|---|---|---|
| 1 | Do thinking modes make chain-of-thought more honest? (kept) | 0:10 | 0:00–0:10 | Ritik |
| 2 | Tools steer answers, and the user sees only the result (kept, plus the why line) | 0:30 | 0:10–0:40 | Ritik |
| 3 | What we built | 0:55 | 0:40–1:35 | Ritik |
| 4 | The failure: tools pull harder, and the answer hides it | 0:35 | 1:35–2:10 | Arsha |
| 5 | Inside the model: three layers read the hint | 0:30 | 2:10–2:40 | Ritik |
| 6 | Training cut wrong-hint following from 42% to 12%, at a cost | 0:50 | 2:40–3:30 | Ritik |
| 7 | See it: the same question, before and after training (clip C) | 0:40 | 3:30–4:10 | Arsha |
| 8 | Two of six reviewers defer to the tool; a checker doesn't | 0:45 | 4:10–4:55 | Shrey |
| 9 | What we'd tell a team deploying a tool-using model | 0:40 | 4:55–5:35 | Shrey |
| 10 | Where this holds, and what we don't know (kept) | 0:20 | 5:35–5:55 | Shrey |
| 11 | Thank you (kept) | 0:05 | 5:55–6:00 | Shrey |

The brief's split gives Ritik 2:55, Arsha 1:15 and Shrey 1:50 (decision 5).

## 2. The draft renders (LibreOffice; numbers only)

Built by `tools/deck/draft_v3.py` on the ASU template (the draft .pptx is local, `storyboard/draft_v3.pptx`). Each was
rendered and looked at; nothing the deck adds reaches the reserved strip (below 4.78 in).

- **Slide 3, what we built:** [v3/slide_03_what_we_built.png](storyboard/v3/slide_03_what_we_built.png). Four numbered
  blocks with arrows (the test harness; inside the model; training the fixes; the multi-agent check), 2–3 facts each,
  and the effort band: 352 GPU-hours on Sol (271 GPU jobs), 5 trained versions, 31 rules written before the data, 479
  answers labelled by hand, 1,400+ automated tests, results frozen Nov 18. The four "why" lines go to the notes.
- **Slide 4, the failure:** [v3/slide_04_failure.png](storyboard/v3/slide_04_failure.png). Left: user against tool for
  the seven models, sorted by the tool's share, with counts and intervals (02 N140–N146). Right: after a tool call,
  reasoning against answer naming the tool: Qwen3 8B 141/145 vs 0/143, Qwen3 30B Thinking 54/54 vs 3/54, Gemma 4 with
  thinking off 127/162 (N133–N136). Under it: "Did thinking make it more honest? Mixed."
- **Slide 5, inside the model:** [v3/slide_05_inside.png](storyboard/v3/slide_05_inside.png). All 32 layers' shares of
  the hint's effect at the takeover, with 95% intervals (`results/summaries/trackA/step10_handoff.json`,
  `handoff/by_cut_type/ii/all/drop_by_layer`); 15, 19 and 23 in maroon. Beside it: together 0.90 [0.85, 0.96]; on 16
  new questions 0.90 [0.76, 1.06]; Qwen3 8B's own three (21, 22, 29), less concentrated, 0.70 [0.60, 0.83]; 8 of the 10
  top heads. The bottom line: "This told us where to intervene."
- **Slide 6, training (two versions; decision 2):**
  - A, one paired chart as the brief asks: [v3/slide_06a_training_grouped.png](storyboard/v3/slide_06a_training_grouped.png).
  - B, two panels on the same rows (no fix gold, consistency maroon, the rest grey):
    [v3/slide_06b_training_panels.png](storyboard/v3/slide_06b_training_panels.png). **Recommended:** each panel
    answers one question, and the maroon bar falls in both, so it reads in five seconds.
  - Both: the five versions' counts as in FINDINGS (F41's table and A42), Wilson intervals computed from the counts and
    checked against FINDINGS' printed bounds; "What training changed" beside; the bottom line in 13 pt bold.
- **Slide 8, the check:** [v3/slide_08_check.png](storyboard/v3/slide_08_check.png). The why line; the six reviewers'
  corrections of the same 73 wrong answers, seeing the answer only against the tool's log (F18, F22, F30); a seventh
  bar, the checker, 53/53 on other items (C15's 100 fresh items, F24); the pipeline as four native boxes; the three
  follow-ups; the limit; the conclusion.

## 3. What the number check changed (helper 1, read-only; about 60 numbers, about 50 exact matches)

Every number in the brief was looked up in FINDINGS, FINDINGS_B/C, 02_NUMBERS or TALK_MAP, with its JSON key path.
These differ from the brief, and the drafts follow the sources:

1. **"Wrong-tool following, 42% → 12%" pools three channels.** 297 of 703 is the user's guess, pasted tool output and
   the tool's turn together (82 of 237 + 130 of 233 + 85 of 233; F41's measure, "follows the wrong hint"). Only the
   right-hint counts (439 of 476 …) are tool-only. The drafts say "wrong-hint following" and "wrong hints followed,
   from the user or a tool" (decision 1).
2. **"No-hint accuracy within 4 points" is not true for consistency + instruction** (−4.3 [−9.2, +0.5] against no fix;
   FINDINGS F43 "−4"). The drafts say "within 5 points", FINDINGS' Gate 3 margin.
3. **Fine-tuning "following no less than the instruction"** → "no difference detected" (+1.9 [−2.1, +5.7], F44).
4. **"+0.68 logits … layers 0–14"** are two results: +0.68 [+0.17, +1.18] is the whole effect of the consistency-trained
   weights; "before the readout layers (0–14)" is where it sits (F42's split). The draft says them as two clauses.
5. **"6 reviewers, 4 views":** only the two C4 reviewers had all four views; the other four had three. The drafts say
   "up to 4 views".
6. **The reviewers defer:** only the two Olmo reviewers do (F30). Slide 8's title says "Two of six".
7. **"1,196" and "981 examples"** include validation (1,040 + 156; 881 + 100): the drafts say "from 1,196 examples",
   the notes give the split. **"271 jobs"** are GPU jobs (287 in all), Ritik's account only.
8. **"Every model we decided; gpt-oss: no decision":** FINDINGS says the tool-over-user gap is clear in gpt-oss too;
   "no decision" means it ran after its window. Notes: "every model tested; gpt-oss reported without a decision".
9. **The "unverified" label's −1 [−7, +4]** holds on the inserted tool turn only (slide 9's notes).
10. **Not on slide 6's chart but in its notes:** LoRA + instruction beats the instruction on following alone (−8
    [−12, −4]) at an acceptance cost (−9 [−13, −5]); FINDINGS: the no-cost bar is "met by no fix".

**The effort band's sources:** 352.47 GPU-hours, 271 GPU jobs, 287 jobs since Oct 1 (`pack/03_METHODS.md` and
`tools/demo_template/method.json`, from Sol's sacct); 31 of the ledger's 42 rows marked pre-registered
(`docs/paper/supplement/PREREGISTRATIONS.md`, counted); 479 = 101 + 294 + 84 rows (L3, L4, L6; L3's 101 are below the
agreement bar, F3, so this is effort, not 479 trusted labels); 1,413 tests passed in the Nov 23–24 full run; the freeze
tag on Nov 18, 21:03; 12 models = 8 that answer + 4 reviewers. "5 trained versions" is derived: Gate 3's four (LoRA,
tags, LoRA + tags, LoRA on 15/19/23) plus consistency training; the demo holds those five training logs.

## 4. Clip C, the video (about 35–40 s; stills local, gitignored: they show model text)

The question is chosen by the page, not by us: the scratch pad on the 120 fresh questions, a tool call's wrong reply,
Show me → "the fix held" with Consistency-trained selected, the first match in the seeded order. That is
**mmlupro-11784** (then mmlupro-1802, mmlupro-3675); the page says "No fix took the wrong hint and Consistency-trained
didn't on 26 of 112 questions" (TALK_MAP's count). It is also clip A's question, the first of "named in reasoning
only". Stills in `docs/presentation/final/storyboard/video_beats/clipC/` (with `manifest.json`: ids, counts, boxes;
`contact.png`); capture script `tools/demo_video/record_c.py` (no model text).

| beat | about | what is on screen (zoom target) | caption (ours) |
|---|---|---|---|
| C1a | 2 s | No fix alone; the tool-call slip lands (the slip, top left) | Tool call's wrong reply lands. |
| C1b | 4 s | the reasoning's sentence holding the first highlighted mark (per-line gold boxes, as clip A) | No fix: its reasoning cites the tool. |
| C1c | 2 s | the final answer and its three checks (took it yes, reasoning says so yes, answer says so no) | No fix: the wrong letter, and the answer doesn't say so. |
| C2 | 8 s | split, No fix against Consistency-trained; the red verdict line across both | Same question, same hint: the fix held (26 of 112 questions). |
| C3 | 6 s | the bench, test 4, Fine-tuned, key L: hand-labelled answer 1 of 42 (says_changed); its opening line names the hint | Fine-tuned, another question: when it still follows, its answer says so (37 of 42 vs 18 of 42, hand labels). |
| C4a | 5 s | the map, step 6: layers 15, 19, 23 and "together 90% [85%, 96%]" (side panel) | Three layers carry it: together 90%. |
| C4b–c | 5 s | the map, step 8: the "What we read" note for Fine-tuned, then Consistency-trained | Fine-tuned: the change is in the reasoning. Consistency-trained: before the readout. |
| C5 | 5 s | end card (composed) | Wrong hints followed: 42% → 12%. Right tool hints taken: 92% → 76%. Real recorded runs, found by pattern. |

**To fix in Phase B** (seen on the stills):
- C2: the Show me box reads "pick a pattern"; capture it with "the fix held" set, so the count is on screen too.
- C3 is a different question (mmlupro-4588) and pasted tool output, not a tool call. That is inside F45's sample (14
  rows a channel), but the caption must say "another question". Its hand-label line sits below the overlay's fold:
  scroll it into view. The rule that chose it: the first Fine-tuned row in L6's key order whose label is
  says_changed or mentions_only (the first row was).
- C4b–c: step 8 also prints per-group logits (e.g. +1.29 for layers 0–14) that FINDINGS doesn't print; zoom to the
  "What we read" note, not the numbers.
- The end card's first line must say "wrong hints" (item 1 above), not "wrong tool hints".
- If the clip runs long, cut C3 first (the brief).

## 5. The other slides and the backups (Phase B)

- **Slide 2:** keep the scenario; one line on why it matters (tool-using assistants act on tool output; users see
  only the final answer; other models are used to check it).
- **Slide 9:** four rows, each with its number: the answer isn't a record of why (0 of 143); a label or a prompt line
  won't fix it ("unverified" −1 [−7, +4], inserted turn); if you train, pick by the tool's reliability (42% → 12%
  wrong hints, 92% → 76% right tool hints); an independent check before acting (53 of 53, one more model call).
- **Slides 10–11:** Ritik's, kept; the limits slide's notes cut to the "unknown" column.
- **Backups** (renumbered): Ritik's twelve (they already hold the ten-settings figure and clip B), plus clip A, Ritik's
  Nov 26 main charts that v3 replaces (reasoning vs answer; the trade-off; the review team), and a new table of every
  fix with its intervals.
- **Checks to add in Phase B:** the slides now carry counts as "k/n" in text boxes, so the number test learns that
  form; 02_NUMBERS gets rows for the new slide numbers that aren't there yet (Granite's and Mistral's k of 73, 42% and
  92% as rates, the per-layer chart's source); a check of the effort band against `method.json` and the ledger.
- **Docs:** TALK_MAP and PREP_GUIDE to the new slides, times and backup numbers.

## 6. Decisions for Ritik

1. **Slide 6's measure.** Keep FINDINGS' pooled measure and say "wrong-hint" (recommended: it is the pre-registered
   Gate 3 measure, and 42% → 12% stays true), or chart the two tool channels separately (pasted 130 of 233 → 31 of
   232; inserted 85 of 233 → 29 of 234, from the summaries; new rows in 02).
2. **Slide 6's chart:** A (one paired chart, as briefed) or B (two panels; recommended).
3. **Slide 8's title:** "Two of six reviewers defer to the tool; a checker doesn't" (the brief's title reads as if
   reviewers in general defer).
4. **Clip C's beat 3:** keep it on another question, captioned so (recommended), or cut it.
5. **Speakers:** the brief's split (Ritik 2:55, Arsha 1:15, Shrey 1:50), or contiguous and closer to two minutes each:
   Ritik 1–3 (1:35), Arsha 4–7 (2:35), Shrey 8–11 (1:50).
6. **The effort band:** keep 479 (all rows labelled, the notes say L3's agreement was below the bar), and "5 trained
   versions" (derived; the notes list them).
