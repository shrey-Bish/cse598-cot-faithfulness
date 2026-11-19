## In plain words (Ritik's page, as of Nov 18, 21:04: the results frozen, tag `results-freeze-2026-11-18` at `7e1fdc0`; slides 2 and 7 after Track B's merge; earlier Nov 14, 23:09: the demo is now the Hint Explainer; plain names (the glossary, the README, the slide figures); earlier Nov 14, 20:14: the results demo; slide 5's figure; Gate 3's statement drafted; the freeze procedure; the submission folder; earlier Nov 13, 11:14: B1R2 read; the freeze page; the wording held after L6; earlier 09:56: L6 read, F45; Sol pulled; edited by hand in `docs/status/ONE_PAGE.md`)

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

- **For the presentation (Nov 13–14):** the demo is now the **Hint Explainer**, [`docs/demo/index.html`](../demo/index.html)
  (opens offline; "Play the story" plays the 7-scene tour by itself, about 2 minutes: space pauses, → steps, ← back, 1–7
  jump, Esc closes a chart, then the tour; presentation fixes after the freeze, Nov 18, no number changed;
  `t` theme, `i` the IDs); everything in plain names, the IDs in [`docs/GLOSSARY.md`](../GLOSSARY.md); the slide
  figures relabelled in plain names (slide 1's stale "Open" line now "Read since"); slide 5's figure of F3
  (`private_vs_final.png`); **Gate 3's final statement drafted in PLAN for Ritik's approval** ("met; the stricter bar:
  not met"); the freeze procedure (CHECKIN §10); the submission folder (`docs/submission/`) with the AI-use facts.

**Running.** Nothing. Ritik's Sol queue was empty at the last check (Nov 13); the feeder still ticks every 5 minutes (Ritik stops it himself).

**Frozen Nov 18, 21:04.** The tag `results-freeze-2026-11-18` is on `main` at `7e1fdc0` (the freeze commit `85b3e32`; the supplement regenerated from it, `7e1fdc0`). Every check passed; the bundles' sha256s are in the Nov 18 log. A later change to a frozen number gets a dated note (CHECKIN §10). The full page is in PLAN, "Freeze readiness for Nov 18".

| item | state | on whom, by when |
|---|---|---|
| Gate 3's final statement | drafted Nov 13 in PLAN; waits on Ritik's approval | Ritik, Nov 20 |
| The demo (`docs/demo/index.html`), the Hint Explainer | built and checked Nov 14 | rebuilt at the freeze (CHECKIN §10) |
| Slide 2 (B20's rows) and B18's table | done: merged and redrawn Nov 18 | — |
| Slide 5 (F3) | figure made Nov 13 (`private_vs_final.png`) | Ritik and Shrey place it, Nov 18 |
| Slide 7 (B24's arms) | Arsha's `authority_ladder.png`, placed Nov 18 | Arsha, final Nov 20 |
| Slide 10 (B1R2 in panel b) | figure drawn Nov 13 | Ritik places it |
| Slides 11–12 | figures placed | Shrey, Nov 18 |
| Track B's report bullets | not started | Arsha, Nov 20 |
| The report's prose | bullets in | each section's owner, Nov 18–21; draft Nov 22 |

**Waiting on whom.**
- **Ritik:** Nov 15, the check-ins and merges; Nov 16, stop the feeder (`touch /scratch/ragarw68/trackA/feeder.stop;
  scrontab -r`); Nov 18, the freeze by CHECKIN §10 (its tag needs Ritik's go) and slide 5 placed with Shrey; Nov 20,
  approve or change Gate 3's draft; Nov 22, confirm the AI-use inventory's "to confirm" lines.
- **Arsha:** merge `origin/main` back and push; B18's table with B20's rows and slides 2 and 7 (Nov 18); slides 6–8 and
  `docs/trackB/REPORT_B.md`'s bullets (Nov 20).
- **Shrey:** merge `origin/main` back; slides 11–12 (Nov 18).

**The dates to Nov 24.**
- **Nov 15:** check-ins and merges. **Nov 16:** the feeder stopped. **Nov 18:** the results freeze; check-ins and
  merges. **Nov 20:** Gate 3's final statement, Track B's report bullets, the slides.
- **Nov 22:** the report draft. **Nov 23:** the rehearsal. **Nov 24:** the final presentation and report.

**Only Ritik or a teammate can do these.** Sending messages; approving any rule or amendment; any Sol change on Ritik's
account beyond reading and a safe pull (the feeder's stop included); every Sol command on Arsha's account; Arsha's and
Shrey's own track work.
