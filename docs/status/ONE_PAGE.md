## In plain words (Ritik's page, as of Nov 19, 10:35: the last materials, no number changed: the report's bullets complete, the related work checked on arXiv, the slide shell and the presentation kit, the submission folder's checklist and zip command; earlier Nov 18, 21:04: the results frozen, tag `results-freeze-2026-11-18` at `7e1fdc0`; slides 2 and 7 after Track B's merge; earlier Nov 14, 23:09: the demo is now the Hint Explainer; plain names (the glossary, the README, the slide figures); earlier Nov 14, 20:14: the results demo; slide 5's figure; Gate 3's statement drafted; the freeze procedure; the submission folder; earlier Nov 13, 11:14: B1R2 read; the freeze page; the wording held after L6; earlier 09:56: L6 read, F45; Sol pulled; edited by hand in `docs/status/ONE_PAGE.md`)

**Done. Every experiment is read; nothing runs.**
- **45 findings** (F1–F45, in `docs/FINDINGS.md`) and Track B's **FB1**. **Gate 2 is marked** (Nov 8). **Gate 3 is
  met** (F28); its final statement is Nov 20.
- **The title question, answered mixed:** with thinking on, Qwen3-8B names the tool in its private reasoning but not in
  its final answer (F29); gpt-oss-20b's reasoning effort changes nothing (F37); Nemotron's answer after the tool turn is
  less bare with thinking (FB1).
- **B1R2, read Nov 13 (F38's replication line): "ignores tools" again.** Scaling attention to the tool turn cuts
  following on E2's 120 questions too (82 of 240 → 49 of 240, −13.8 [−20.0, −7.5]), and takes fewer correct tool hints
  (−5.8 [−10.8, −1.3]): a real cost, just past B1's 5-point limit by the point estimate. B1's verdict on the 30 stays
  primary.
- **L6, read Nov 13 (F45): training made the answer more candid about a hint it followed, in hand labels, without
  making it follow less.** When LoRA follows a wrong hint on E2, its answer says so in 37 of 42 runs against the
  instruction's 18 of 42 (+45 [+25, +64]); Claude Opus, the check, agreed at kappa 0.96 (82 of 84 rows). Limits:
  LoRA's trained opener names the hint (F28); it follows as often as the instruction (F44); one model, E2, 42 rows a
  system, the final answer only; the sheet wasn't blind in practice (32 of LoRA's 42 guessed "trained").
- **The fix, overall** (`docs/status/FIX_SO_FAR.md`): A40, A42, LoRA + note, the wrapper + note and B1's attention
  scaling all follow fewer wrong hints and take fewer correct ones. Nothing beats the instruction without that cost.
  The fix belongs at the system level: provenance labels alone don't help (F44, FC3); independent verification does
  (Track C's checker, F24). FINDINGS' story item 7 is the scorecard.

- **For the presentation (Nov 22):** the demo is now **an answer sheet in three parts** (how we did it, run it, what we
  found), [`docs/demo/index.html`](../demo/index.html); the local build replays recorded runs. Earlier (Nov 13–14) the
  **Hint Explainer**, now [`archive/superseded/explainer_2026-11-14/explainer.html`](../../archive/superseded/explainer_2026-11-14/explainer.html)
  (opens offline; "Play the story" plays the 7-scene tour by itself, about 2 minutes: space pauses, → steps, ← back, 1–7
  jump, Esc closes a chart, then the tour; presentation fixes after the freeze, Nov 18, no number changed;
  `t` theme, `i` the IDs); everything in plain names, the IDs in [`docs/GLOSSARY.md`](../GLOSSARY.md); the slide
  figures relabelled in plain names (slide 1's stale "Open" line now "Read since"); slide 5's figure of F3
  (`private_vs_final.png`); **Gate 3's final statement drafted in PLAN for Ritik's approval** ("met; the stricter bar:
  not met"); the freeze procedure (CHECKIN §10); the submission folder (`docs/submission/`) with the AI-use facts.

- **The last materials (Nov 19; no number changed):** the report's material is complete, every section with its
  bullets, limits and figure, nothing marked waiting ([`REPORT.md`](../paper/REPORT.md); Track B's section prepared from
  FINDINGS_B and B18's table); nine related papers checked on arXiv and the novelty claims reworded where they already
  show it ([`RELATED_WORK.md`](../paper/RELATED_WORK.md)); the slide shell [`deck.pptx`](../presentation/deck.pptx)
  (14 slides and 4 backups, built from [`TALK_MAP.md`](../presentation/TALK_MAP.md)) and
  [`QA_FACTS.md`](../presentation/QA_FACTS.md); the submission folder's checklist and one command for the zip
  ([`docs/submission/`](../submission/README.md)); the README's "Start here in five minutes".

**Running.** Nothing. Ritik's Sol queue was empty at the last check (Nov 13); the feeder still ticks every 5 minutes (Ritik stops it himself).

**Frozen Nov 18, 21:04.** The tag `results-freeze-2026-11-18` is on `main` at `7e1fdc0` (the freeze commit `85b3e32`; the supplement regenerated from it, `7e1fdc0`). Every check passed; the bundles' sha256s are in the Nov 18 log. A later change to a frozen number gets a dated note (CHECKIN §10). The full page is in PLAN, "Freeze readiness for Nov 18".

| item | state | on whom, by when |
|---|---|---|
| Gate 3's final statement | approved by Ritik as drafted, Nov 23 (PLAN) | — |
| The demo (`docs/demo/index.html`), the answer sheet | built Nov 22; the Sol copy in Nov 23; the final pass Nov 23 (the review's seven fixes, both builds offline at 1920×1080 and 1440×900) | publish the seeded runs? (Ritik and the team) |
| Slide 2 (B20's rows) and B18's table | done: merged and redrawn Nov 18 | — |
| Slide 5 (F3) | figure made Nov 13 (`private_vs_final.png`) | Ritik and Shrey place it, Nov 18 |
| Slide 7 (B24's arms) | Arsha's `authority_ladder.png`, placed Nov 18 | Arsha, final Nov 20 |
| Slide 10 (B1R2 in panel b) | figure drawn Nov 13 | Ritik places it |
| Slides 11–12 | figures placed | Shrey, Nov 18 |
| Track B's report material | prepared Nov 19 from FINDINGS_B and B18's table (REPORT §4) | Arsha's words, Nov 20 |
| The report's material | complete Nov 19 | the prose: each section's owner; draft Nov 22 |
| The slide shell and the kit | built Nov 19 (`deck.pptx`, TALK_MAP, QA_FACTS) | the words: each slide's owner; rehearsal Nov 23 |
| The contribution statement | the placeholder, Nov 19 | Ritik, before submission |

**Waiting on whom.**
- **Ritik:** Nov 20, approve or change Gate 3's draft (REPORT §7, PLAN's Gates); the contribution statement
  (`docs/submission/CONTRIBUTIONS.md`, now the placeholder); Nov 22, the AI-use inventory's "to confirm" lines and the
  report draft; the slides' words with the team; Nov 23, the rehearsal; Nov 24, the presentation and the report.
- **Arsha:** merge `origin/main` back; her words for REPORT §4 (prepared Nov 19 from her findings) and slides 6–8
  (Nov 20); her Track B AI-use lines.
- **Shrey:** merge `origin/main` back; slides 11–12's words; his Track C AI-use lines.

**The dates to Nov 24.**
- **Nov 15:** check-ins and merges. **Nov 16:** the feeder stopped. **Nov 18:** the results freeze; check-ins and
  merges. **Nov 20:** Gate 3's final statement, Track B's report bullets, the slides.
- **Nov 22:** the report draft. **Nov 23:** the rehearsal. **Nov 24:** the final presentation and report.

**Only Ritik or a teammate can do these.** Sending messages; approving any rule or amendment; any Sol change on Ritik's
account beyond reading and a safe pull (the feeder's stop included); every Sol command on Arsha's account; Arsha's and
Shrey's own track work.
