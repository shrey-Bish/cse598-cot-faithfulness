# Session log: the full Sol copy in, Show me (the case finder) (2026-11-23 15:55 MST, finished Nov 24)

**By:** Ritik. Branch `trackA-nosol`, from `9bd64b5` (main, `trackA-nosol`, `origin/main` and `origin/trackA-nosol`
level). The day's third session, paused overnight after the first walk and finished on Nov 24 from 08:12. The daily:
[DAILY_2026-11-23](DAILY_2026-11-23.md). The previous session: Nov 23, [13:24](2026-11-23_1324_ALL_scratch-pad.md).
The results are frozen: the tag `results-freeze-2026-11-18` on `7e1fdc0`. Presentation work only, no helper.

## 0. Input

Two pastes, acted on as Ritik's:
- **The fetch's output.** Ritik ran the full Sol copy on his Mac (15:48), then `sol.py unpack_all`, `pad.py` and
  `build.py`.
- **A review of the pad, with the next prompt.** "The question it opens on is one where the model didn't take the
  hint." The prompt asked for four small additions, with nothing else changed (at most one helper):
  1. **The case finder.** A "Show me" control beside Question. It jumps to a question that fits a pattern, with how
     common the pattern is. Matches come in a seeded order, "next" cycles, and the label reads "found by pattern; the
     count is every question".
  2. **A verdict line** across the split, in red pen at 32 px or more, read from the outcome fields.
  3. **The scroll:** a finished run (or Esc) scrolls its pad to the first highlighted mention of the hint.
  4. **The landing:** the pad opens with the finder on "No fix took the wrong hint", for the 120 and a tool call's
     reply.

  Walk at 1920×1080 and 1440×900, both themes. Tests: counts equal the per-question outcome fields, and highlights are
  verbatim.

## 1. What was done (Nov 23 15:55 – Nov 24)

**The full Sol copy is in** (Ritik, Nov 23 15:48; read-only on Sol; gitignored):
- 25,627 runs, 190 MB compressed (the estimate was about 240 MB), complete against the plan.

  | group | runs | ids in this Mac's index |
  |---|---|---|
  | the fixes on the 120 | 10,223 | 10,080 |
  | the 30 | 7,380 | 7,380 |
  | the dial | 2,027 | 2,024 |
  | Qwen3-8B | 1,620 | 1,620 |
  | gpt-oss-20b | 2,431 | 2,430 |
  | Nemotron | 1,946 | (its whole file) |

  A group with more runs than ids holds a run listed twice. Texts match their index rows by run id and time.
- After `pad.py`, every run on the 54, the 30 and the 120 has its text (9,884, 7,800 and 11,280 runs). The review
  team's items have 2,275 texts of 2,450 runs.
- The test that the copy is complete now runs, and passes.

**Show me, the case finder** (`tools/demo_template/pad.js`, `pad.css`, `pad.py`; mine):
- **Where:** a fifth box in the top row, beside Question. The finder's line sits in the left column, between the hint
  and the question.
- **Patterns,** read from each run's own outcome fields:
  - No fix took the wrong hint; and hid it in the answer; and named it in the answer.
  - No fix took it and the selected version didn't.
  - Both took it.
  - The selected version refused a right hint that No fix accepted.

  For the dial, its control (the dial at 1) stands in for No fix, as in its split.
- **Counting:**
  - A question counts when one of its recorded runs fits (one on each side, for a pair). Where a question has more
    than one run, the line says so.
  - The count, "k of n questions", covers every question of the dataset with runs for this hint and model (and this
    version and its control, compared as the split compares them).
  - Matches come in a seeded order: fnv1a-32 of `cse598-demo-finder-2026-11-23` and the question id, never by outcome.
  - "next →" or **F** cycles the matches; each pane pins the first run that fits, and **N** still steps through the
    repeats.
  - On a double-click, only the embedded questions can be shown, and the line says "in this file".
- **The data:** the index carries each question's runs compactly (`finder_rows`: a key table per dataset, then
  [key, took, said so in the answer] per run), 0.76 MB. The page counts from these.
- **The verdict line:** across a split, red pen at 36 px, written when both runs finish. For example: "Same question,
  same wrong hint: No fix took it (G). Consistency-trained didn't (I)."
- **The scroll:** a finished pad scrolls to its first highlighted mention, a quarter of the way down.
- **The landing:** Show me on "No fix took the wrong hint", for the 120 and a tool call's reply (a study guide). It
  shows 38 of the 114 questions with an answer and opens on the first, mmlupro-1817.
- **The finder ends** when the question, the hint or the model is changed by hand. A version click keeps a pattern
  without a version (re-pinned) and ends one with a version.
- **Layout:** the top row is five boxes. In a split, the panes start below the verdict line, and each count under a
  run takes one line, with its condition and path on hover.

**One rule made consistent: a run with no answer.**
- Summed over the runs, every count's k matched the frozen one, but some n did not. The frozen counts treat a run with
  no answer differently by experiment:
  - Gate 3's, A39's and the 54's leave it out (n is the answered runs).
  - The dial's counts it as not taking the hint.
- The pad had marked every such run "took the hint? no". Those runs now carry no outcome ("–"), as their counts take
  them; the dial's are unchanged. `pad.py` says so, and the finder counts only runs with an outcome.
- **On the 54, a tool call's reply is one channel per model and setting**, as the frozen counts take it. Nemotron's
  file holds two own-call smoke runs (pilot-0, Nov 4) beside its 162 inserted turns per setting; they are in no count
  and are now left out, where the pad had merged them.
- Now every frozen count on the 54, the 30 and the 120 is exactly the sum of its runs' outcomes (a test). On the 120,
  where a question has one run per wording (a tool call's reply), the finder's k of n summed over the wordings is the
  frozen count beside the run: 38 of 114 and 47 of 119 make 85 of 233. Where it has two (pasted), the finder counts
  questions and the frozen count counts runs, so they differ (84 of 118 questions; 130 of 233 runs).

**What the finder shows** (the 120, a tool call's reply, a study guide):

| pattern | questions |
|---|---|
| No fix took the wrong hint | 38 of 114 |
| … and hid it in the answer | 32 of 114 |
| … and named it in the answer | 6 of 114 |
| No fix took it and Consistency-trained didn't | 26 of 112 |
| both took it | 10 of 112 |
| Consistency-trained refused a right hint that No fix accepted | 16 of 118 |

On the landing question, Consistency-trained took the hint too, and the verdict line says so. For the second move
(the fix), "the fix held" gives the contrast, with its count. The seeded order was not changed to land on a better
example.

**Docs:**
- TALK_MAP: the four moves on the pad, the answer to "38 of 114 against 85 of 233", and the pad's keys.
- `docs/demo/README.md`.
- TODO D19 and ONE_PAGE.

**After the freeze (Nov 23–24): presentation work only.** No frozen number, figure or verdict changed:
- Every count beside a run is DATA's.
- The finder's counts are sums of the runs' own outcomes, and agree with DATA's (tested).
- The only marks changed: a no-answer run's "took the hint?" from "no" to "–" (outside the dial), and Nemotron's two
  smoke runs leaving the 54's rows. Both follow the frozen counts' own rules.

## 2. Waiting for Ritik

1. **Rehearse the four moves** (TALK_MAP, "Show me"), from `cot-disclosure/`: `../.venv/bin/python
   tools/demo_template/serve.py`. Live mode needs `ollama serve`.
2. As before: the report's prose, the slides' words, `CONTRIBUTIONS.md`, `AI_USE.md`; Prompt 2 (the final check, the
   zip, the tag); publish the seeded runs? a LICENSE? the username in the logs?

## 3. Checks and push

**The walk** (Playwright, on the final page):
- The landing and 13 states: the move-2 split; the patterns "the fix held", "the cost" and "both" with
  Consistency-trained; "named" and "next"; the dial's split; the Show me menu; the 30 ("took", "the fix held" with
  3 layers); the 54 ("took", "named" with the user's hint); the review flow.
- At 1920×1080 and 1440×900, both themes, file:// with the network off and served on 127.0.0.1: **112 states**.
- 0 console errors, 0 requests but the file or the local server, 0 text cut by its box. In every state, the question
  shown is a match, every pinned run fits its pattern, and the verdict line names each shown run's answer.
- Screenshots in `cot-disclosure/results/demo/screens_finder/` (112, gitignored). Looked at: two contact sheets of nine
  (served 1920 light, served 1440 dark), the landing, the split and the menu.
- Found and fixed on the way:
  - The no-answer rule (above).
  - Nemotron's smoke runs (above).
  - A test that assumed one run per question for every source; it now checks the sum only where that holds.

**Tests:**
- `tests/test_demo_pad.py`: 11 passed.
  - New: every frozen count is the sum of its runs' outcomes (the 54, the 30, the 120).
  - New: the index's compact rows are each run's own outcome fields.
  - New: for 624 combinations of dataset, hint, wording, model, version and pattern, the page's k of n and its seeded
    order equal a count made here from the per-question files. On the 120, the tool call's sum is DATA's.
  - New, served: the landing; for 12 patterns × the first 3 matches, each fits and each pinned run fits; the verdict
    line is the shown runs' own fields; a finished pad shows its first highlighted mention.
  - Kept: the highlights are verbatim spans that agree with each run's flag. The full copy's completeness now runs
    (no longer skipped).
- `tests/test_demo_template.py`: passed (the tracked page has no pad; its bytes are unchanged, 446,186).
- The full suite once: **1,413 passed, 1 skipped** (17 min 35 s; on the final data; only a code comment changed after it).
- `tools/check_links.py`: 0 broken links. `make_supplement.py --check` and `export_summaries.py --check`: pass.
- STATUS and the Gantt; the pre-push check; the push: `git push origin trackA-nosol:main trackA-nosol:trackA-nosol`.
