## In plain words (Ritik's page, as of Nov 4, 16:29; the labels corrected 17:54 and read 18:01; edited by hand in `docs/status/ONE_PAGE.md`)

**Done.**
- 40 findings (F1–F40, in `docs/FINDINGS.md`).
- **Gate 3 is met** (F28): trained versions follow fewer wrong hints, though none beats a one-line instruction.
- **Gate 2's first half is answered:** a tool's hint pulls harder than the user's on all five models.
- **B24 is read** (F40): a source's authority adds to its pull.
- **Track C** went to Shrey on Nov 3.
- **The shared-port fault on Sol is fixed,** and every earlier result was checked clean (T12).

**Running.**
- **On Sol:** A39 (the fix round on 120 fresh questions), B20 (three new model families), then B1R2. All are queued,
  but nothing has run since Nov 4 12:36, because our fair share is low. The first start is estimated tonight.
- **The feeder** submits every job by itself. The Nov 6 07:00 and Nov 11 09:00 rules apply themselves.

**Waiting on whom.**
- **The labels (Ritik):** one human rater, Ritik, plus four AI judges, under the LLM-judge protocol (pre-registered
  Nov 4).
  - **Read the same day: Gate 2's label part is not met.** Ritik against the judges' majority is 0.472 and 0.234.
  - Claude Opus agrees with Ritik closely (0.837 on L3's final answers, 0.967 on L4). The two smaller judges barely
    follow the guide.
  - Ritik's labels stand. No claim rests on them.
  - **Left:** Ritik's blind re-look of the cells where he and the majority differ (60 in L3, 140 in L4).
  - Corrected Nov 4, 17:54: rater 2 was an AI model (ChatGPT 5 Astra High), not Shrey; see the 17:42 log. There is
    no settling call, and Shrey does no labeling.
- **Ritik:**
  - send Shrey the Track C handoff message (ready, with no labels: the 17:42 log's §5);
  - the blind re-look (`results/labels/llm_judge/relook_L3.csv`, then `relook_L4_part1.csv`);
  - on Nov 6, send Arsha her bundle and note (ready; one command refreshes the bundle);
  - decide before Nov 15 whether A39 on E2 may be read partial (a draft rule is ready).
- **Shrey:** C19 by Nov 7. Check-ins on Nov 7, 12, 15 and 18.
- **Arsha, from Nov 6:**
  - the re-reads (Nov 7 and 9);
  - B20, read Nov 17;
  - B18's table, Nov 18;
  - slides 2, 6, 7 and 8, Nov 20.

**The dates to Nov 24.**
- **Nov 6:** Arsha's bundle; the 07:00 rule.
- **Nov 7:** Shrey's merge.
- **Nov 8:** Gate 2.
- **Nov 11:** the 30's rule, 09:00.
- **Nov 12, 15, 18:** merges.
- **Nov 15, 23:59:** runs end.
- **Nov 17:** A39 and B20 read.
- **Nov 18:** the results freeze.
- **Nov 20:** Gate 3's final statement, the report bullets and the slides.
- **Nov 22:** the report draft.
- **Nov 23:** the rehearsal.
- **Nov 24:** the final presentation and report.

**Only Ritik or a teammate can do these.** The labels (Ritik's; AI judges only under the LLM-judge protocol); sending
the messages and bundles; approving any rule or amendment; any Sol change beyond reading and a safe pull; Arsha's and Shrey's own track work.
