## In plain words (Ritik's page, as of Nov 4, 22:38; Sol as of Ritik's 22:26 paste; edited by hand in `docs/status/ONE_PAGE.md`)

**Done.**
- 40 findings (F1–F40, in `docs/FINDINGS.md`). **Gate 3 is met** (F28): trained versions follow fewer wrong hints,
  though none beats a one-line instruction. **B24 is read** (F40): a source's authority adds to its pull.
- **Gate 2:** a tool's hint pulls harder than the user's on all five models. The label part is **not met**: Ritik
  against the AI judges' majority is 0.472 and 0.234, under 0.6. It is stated plainly on Nov 8.
- **The labels are final** (L3, Nov 4 21:31). Ritik's blind re-look of 7 cells changed 4 and kept 3, and nothing read
  changes. Rater 2 was an AI model (ChatGPT 5 Astra High), not Shrey (corrected Nov 4, 17:54).
- **Track C** went to Shrey on Nov 3. **The shared-port fault on Sol is fixed,** and every earlier result was checked clean (T12).

**Running.**
- **Sol runs our jobs again** (nothing ran from 12:36 to at least 13:56; by tonight the second smokes had run). At
  22:26, 8 were running (7 of E2's sixteenths and Nemotron's first B20 link) and 1 was pending. The feeder's 220
  lines: 35 ok, 8 running, 1 pending, 131 to submit, 40 skipped, 4 failed, 1 timed out.
- **B20 stopped tonight for Granite and Gemma.** Granite's first link timed out at its 1:30 (about 100 of 954 runs
  done; 34 minutes of it was start-up). Gemma's failed after 52 minutes. The feeder then skipped both chains (22 links).
  A fix is being made, and restoring the chains needs Ritik on Sol.

**On track?**

| item | state | why |
|---|---|---|
| Gate 2 (Nov 8) | on track | the statement is written: the gap is clear on 5 of 5 models; the label part is not met (0.472 and 0.234) |
| Gate 3's final statement (Nov 20) | on track | met Oct 31 (F28); waits on A39 on E2 (read Nov 17, partial by its §18 if not complete) |
| A39 on E2 (read Nov 17) | on track | 70 GPU-h of parts left (+ up to 16 of sweeps), 7 running; makes Nov 15 at under a third of Nov 3–4's pace |
| A39 on the 30 | at risk | Nov 11 09:00 drops it unless every E2 and B20 line has ended; at half Nov 3–4's pace they end only Nov 10–11 |
| B1R2 (runs end Nov 15) | on track | last in the queue (64 GPU-h + up to 6): Nov 10–11 at Nov 3–4's pace; under about half that pace, it is read partial |
| B20 (Arsha reads Nov 17) | at risk | Granite's and Gemma's chains were skipped tonight; restoring them needs the fix and Ritik on Sol |
| Track C (Shrey: C19 Nov 7; C20, C26 Nov 15) | at risk | none of Shrey's work shows here (his last commit was Oct 4); his handoff message is still unsent; C19 is about 25 min of Voyager |
| The labels | done | L3 final with the re-look (Nov 4 21:31); L4 part 1 Nov 3; L4 part 2 (a SHOULD) is not labelled |
| Arsha's handoff (Nov 6) | on track | the bundle is built and verified, and her note is ready; one command refreshes the bundle; Ritik sends it |
| The report and slides (Nov 20–24) | on track | REPORT has the bullets for F1–F40; 10 slides made (1–4, 6–11), 2 waiting (5, the labels; 12, Shrey's, Nov 18); A39 and B20 go in after Nov 17 |

**Projected finishes** (rough, from the feeder's estimates and tonight's 8 running; Sol's own dates come from
`squeue --start`). About 205 GPU-hours are left (245 if every sweep runs). The feeder runs them in the queue's order:

| in the queue's order | GPU-h left | at tonight's 8, around the clock | at Nov 3–4's pace (38.8 a day) | at half that pace |
|---|---|---|---|---|
| A39 on E2, with B20 beside it | 108–125 | Nov 5 midday (B20 itself: below) | Nov 7–8 | Nov 10–11, at the 30's rule |
| then A39 on the 30 | 33–49 | Nov 5 evening | Nov 8–9 | dropped Nov 11, if E2 and B20 aren't done |
| then B1R2 | 64–70 | Nov 6, early | Nov 10–11 | Nov 15–17: misses Nov 15 23:59, read partial |

- **To make Nov 15 23:59,** everything needs about 19–22 GPU-hours a day (0.8–0.9 of a GPU around the clock). That is
  about half Nov 3–4's pace. Sol gave nothing from 12:36 to 20:45 today.
- **B20 is bound by its chains, not by GPU-hours.** Each model runs one 1:30 link at a time, up to 12. If the chains
  are restored by Nov 5 noon, Gemma's 12 links end Nov 6 06:00 if each link starts at once. Every hour a link waits
  adds about 12 hours. Nemotron's first link ends by about 23:45 tonight.
- **The Nov 6 07:00 rule should say "no cut":** at least 4 GPU-hours since Nov 4 12:36 by 22:26, and the 8 running add
  about 8 an hour.

**Waiting on whom.**
- **Ritik:**
  - send Shrey the Track C handoff message (ready, with no labels: the 17:42 log's §5);
  - on Sol, once the B20 fix is in: pull it and restore Granite's and Gemma's chains (the commands come with the fix);
  - check two of the re-look's notes (row 67 says "user might be wrong" but is labelled "mentions"; row 290's note is
    a copy of row 176's);
  - on Nov 6, send Arsha her bundle and note (ready; one command refreshes the bundle).
- **Shrey:** C19 by Nov 7; C20 and C26 by Nov 15; slides 11–12 by Nov 18. Check-ins on Nov 7, 12, 15 and 18.
- **Arsha, from Nov 6:** the re-reads (Nov 7 and 9); B20, read Nov 17; B18's table, Nov 18; slides 2, 6, 7 and 8, Nov 20.

**The dates to Nov 24.**
- **Nov 5:** B20's chains restored (Ritik, on Sol). **Nov 6:** the feeder's 07:00 rule; Arsha's bundle.
- **Nov 7:** Shrey's merge (C19). **Nov 8:** Gate 2. **Nov 11:** the 30's rule, 09:00. **Nov 12, 15, 18:** merges.
- **Nov 15, 23:59:** runs end (E2 and B1R2 read partial if not complete). **Nov 17:** A39 and B20 read.
- **Nov 18:** the results freeze. **Nov 20:** Gate 3's final statement, the report bullets and the slides.
- **Nov 22:** the report draft. **Nov 23:** the rehearsal. **Nov 24:** the final presentation and report.

**Only Ritik or a teammate can do these.** Sending the messages and bundles; approving any rule or amendment; any Sol
change beyond reading and a safe pull (restoring B20's chains included); Arsha's and Shrey's own track work.
