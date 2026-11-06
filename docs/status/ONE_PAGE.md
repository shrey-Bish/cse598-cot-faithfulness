## In plain words (Ritik's page, as of Nov 6, 09:56: Arsha's handoff; earlier Nov 5, 23:51, 22:00, 13:40; Sol as of Ritik's block 1 at about 12:41 and his feeder log at 13:36; edited by hand in `docs/status/ONE_PAGE.md`)

**Done.**
- 40 findings (F1–F40, in `docs/FINDINGS.md`). **Gate 3 is met** (F28): trained versions follow fewer wrong hints,
  though none beats a one-line instruction. **B24 is read** (F40): a source's authority adds to its pull.
- **The fix so far, in plain words** (`docs/status/FIX_SO_FAR.md`, Nov 5): every trained version follows fewer wrong
  hints than base and passes Gate 3, but none beats one line of instruction; training changed the reasoning LoRA
  writes, not how it reads the hint (F39).
- **Gate 2:** a tool's hint pulls harder than the user's on all five models. The label part is **not met**: Ritik
  against the AI judges' majority is 0.472 and 0.234, under 0.6. It is stated plainly on Nov 8.
- **The labels are final** (L3, Nov 4 21:31). Ritik's blind re-look of 7 cells changed 4 and kept 3, and nothing read
  changes. The two notes Ritik was to check (rows 67 and 290) are kept as recorded (Ritik, Nov 5). Rater 2 was an AI
  model (ChatGPT 5 Astra High), not Shrey (corrected Nov 4, 17:54).
- **Track C** went to Shrey on Nov 3. **The shared-port fault on Sol is fixed,** and every earlier result was checked clean (T12).
- **B20's stop fault is confirmed and fixed** (T13; Nov 5, from Ritik's Sol outputs): Nemotron's job started its
  server at 22:18, before Gemma's runner looked again, so its start removed the one shared stop file. Granite's saved
  files are whole, and **Nemotron's runs are all done.**

**Running.**
- **Two Sol accounts from Nov 5** (Ritik's decision h; RUNBOOK §0). Ritik's runs A39 and A40 from his queue file.
  Arsha's runs all of B20 from hers, on her own feeder, with commands she types in her own login. No line is ever
  submitted from both, and no credentials are shared.
- **A39 on E2 (Ritik's account):** at about 08:43 the feeder's 220 lines were 76 ok, 8 pending, 80 to submit, 40
  skipped, 10 not needed, 5 failed and 1 timed out. Every one of E2's 80 parts has a job or is settled, and the 8
  pending are E2's; its 7 sweeps come next. Sol ran about 40 of E2's parts overnight. At most about 28 GPU-hours of E2
  are left (the 08:57 log's §2). **Ritik pulled at about 12:40** (`92ee692`): his queue is 116 lines, E2's 87 and
  the 30's 29, with a place marked for A40's. At 12:36: 75 ok, 5 pending, 2 running, 34 to submit (E2's last 5
  sweeps and the 30's 29). E2's sweeps go in as GPU-minutes free (`e2-lora-sweep` by 13:20).
- **B20 (Arsha's account, from her setup on Nov 6):** no B20 job is queued. Granite has 849 runs left and Gemma
  1,784, on 3:00 lines (Granite 8, Gemma 12), one chain a model, question by question (the B20 log's §19). Her setup:
  `docs/trackB/SOL_ARSHA.md`.
- **A40, a new fine-tune** (Ritik's decision g; pre-registered today, the 09:18 log): LoRA trained on the model's own
  reasoning written without the hint (bias-augmented consistency training), read on E2. Its Voyager targets started
  at 09:50 on Ritik's Mac. At 13:38, shard 1 had 377 of its 486 records finished: 332 examples and 45 dropped
  (the final answer passed in none of 4 samples; correct-hint records drop more, 17% against 9%). **Paused 16:46–21:58**
  while the Mac slept on battery (Voyager unreachable); resumed by itself. Both shards now end about 04:30–05:00 Nov 6,
  if the Mac stays plugged in with the lid open.

**On track?**

| item | state | why |
|---|---|---|
| Gate 2 (Nov 8) | on track | the statement is written: the gap is clear on 5 of 5 models; the label part is not met (0.472 and 0.234) |
| Gate 3's final statement (Nov 20) | on track | met Oct 31 (F28); waits on A39 on E2 (read Nov 17, partial by its §18 if not complete) |
| A39 on E2 (read Nov 17) | on track | at most about 28 GPU-h left (8 parts pending, then 7 sweeps): under a day at Nov 3–4's pace (38.8 a day), about 3.6 days at a fifth of it (the 08:57 log's §2); B20 no longer shares Ritik's places |
| A39 on the 30 | at risk | the first to give way: at Nov 11 09:00 the feeder drops its lines not yet submitted unless every E2 and A40 line on Ritik's account has ended (the A39 log's §19, confirmed by Ritik, Nov 5; B20 no longer counts). Its lines go in as places free while A40's aren't ready |
| A40 (read Nov 17) | on track | pre-registered Nov 5 (the 09:18 log). Its Voyager targets run on Ritik's Mac from 09:50 (paused 16:46–21:58 while the Mac slept; done Nov 6, 05:03; 12% of records dropped so far, by its rules); then about 20–25 GPU-h on Ritik's account from about Nov 6, after E2's lines (training 3.2, E2 16–21); read partial at Nov 15 23:59 if not complete (its §10) |
| B1R2 | dropped (Nov 5) | "not run: GPU time given to A40" (Ritik's decision f, before any B1R2 run; the A39 log's §19, F38); its 44 lines left the queue |
| B20 (Arsha reads Nov 17) | on track | the cause is fixed and confirmed (T13), and the job size amended (the B20 log's §19): 3:00 lines, twice the jobs the measured pace needs (Granite 8 for about 4, Gemma 12 for about 6). It runs on Arsha's own account, whose fair share is likely far above Ritik's 0.0019. Bound by Gemma's ~6 jobs and the waits between them; it starts after her setup (Nov 6); read partial at Nov 15 23:59 if not complete |
| Track C (Shrey: C19 Nov 7; C20, C26 Nov 15) | at risk | the handoff refreshed Nov 5, 23:13 (START_HERE §0 and §9–§11; `trackC_20261105.zip`; commits as Shrey only, enforced three ways); the message goes with the zip's ASU Drive link; none of Shrey's work shows here yet (last commit Oct 4); C19 is about 25 min of Voyager |
| The labels | done | L3 final with the re-look (Nov 4 21:31; rows 67 and 290 kept as recorded, Nov 5); L4 part 1 Nov 3; L4 part 2 (a SHOULD) is not labelled |
| Arsha's handoff (Nov 6) | on track | built Nov 6, 09:54 (START_HERE §0, §1, §9–§11; SOL_ARSHA from `trackB-main`; `trackB_20261106.zip`, 51 files, verified; commits as Arsha only); `trackB-main` pushed for the last time (decision d), so the branch is hers. Ritik sends the zip's link and the note (the 09:10 log's §5); his own Sol block (its §4) comes before her steps 4–8 |
| The report and slides (Nov 20–24) | on track | REPORT has the bullets for F1–F40; 10 slides made (1–4, 6–11), 2 waiting (5, the labels; 12, Shrey's, Nov 18); A39 and B20 go in after Nov 17 |

**Projected finishes** (projections, rough: from the feeder's counts at about 08:43 and the logs' GPU-hour estimates;
Sol's own dates come from `squeue --start`). Two accounts now, each with its own 10 places and 960 GPU-minutes.

| Ritik's account, in the queue's order | GPU-h left | starts |
|---|---|---|
| A39 on E2: 8 parts pending, then 7 sweeps | at most about 28 | now |
| A40: training (three 2:00 jobs, about 3.2), then E2 (16 parts and a sweep, about 16–21) | about 20–25 | once its data is on Sol, about Nov 6 |
| A39 on the 30 (29 lines) | about 49 (the feeder's estimates) | as places free while A40's lines aren't ready |
| **all three** | **about 100** | |

- **Ritik's account fits with room (projection).** About 100 GPU-hours is about 2.6 days of Sol at Nov 3–4's pace
  (38.8 a day): everything ends around Nov 7–8. At a third of that pace it is about 8 days, about Nov 13, still before
  Nov 15.
- **A40's way to Sol (projection):** its Voyager targets, both shards in one guard on Ritik's Mac (shard 2 after shard
  1), about 9 h, done tonight or early Nov 6. Then, on the Mac, the merge check, assembly and the manifest commit;
  Ritik copies the data to Sol and pulls; its lines go in after E2's and before the 30's.

| Arsha's account (B20) | runs left | lines of 3:00 | jobs needed (the B20 log's §19) |
|---|---|---|---|
| Granite | 849 | 8 | about 4 |
| Gemma | 1,784 | 12 | about 6 |
| Nemotron | 0: done | none | — |

- **B20 is bound by Gemma's chain, not by GPU-hours (projection).** One job a model at a time, Granite's and Gemma's
  side by side (360 of her 960 GPU-minutes). Gemma's ~6 jobs of 3:00, plus the waits between them, set B20's finish.
  The first start comes after her setup (Nov 6). Her fair share is likely far above Ritik's 0.0019
  (`docs/trackB/SOL_ARSHA.md`), so her waits should be shorter than his have been; her `squeue --start` will say.
- **What gives way first if Sol slows:** the 30 (its lines not yet submitted at Nov 11 09:00), then A40 read partial,
  then B20 read partial, each at Nov 15 23:59 ("partial: N of 120 questions" for A40; "partial: N of 54 questions"
  for each B20 model).
- **The Nov 6 07:00 rule should say "no cut"** (the 08:57 log's §2): it needs 10 GPU-hours from Nov 4 12:36, and the
  41 jobs that ended ok since 22:26 give that even at 15 minutes each. The feeder decides.

**Waiting on whom.**
- **Ritik:**
  - done Nov 5: the pull (no key file in his scratch; his queue without B20's and B1R2's lines; no B20 job of his);
    Arsha has her Sol block and starts Nov 6;
  - A40: its Voyager targets started at 09:50 (both shards on his Mac, unless he hands shard 2 to Arsha); then the
    merge check, assembly and the manifest commit; copy the data to Sol and pull; then its queue lines;
  - Nov 6: upload `trackB_20261106.zip` to ASU Drive and send Arsha the note with its link (the 09:10 log's §5);
    run his Sol block (its §4: the nov6 decision, no B20 of his, the group can read what her steps 4 and 6 need),
    then tell her steps 4–8 can go ahead;
  - upload `trackC_20261105.zip` to ASU Drive and send Shrey the refreshed handoff message with its link (the Nov 5 23:13 log's §5; it replaces the 17:42 one);
- **Shrey:** C19 by Nov 7; C20 and C26 by Nov 15; slides 11–12 by Nov 18. Check-ins on Nov 7, 12, 15 and 18.
- **Arsha:** her Sol setup (`docs/trackB/SOL_ARSHA.md`, Nov 6), then B20 on her own feeder, read Nov 17;
  optionally shard 2 of A40's Voyager targets, on her own machine with her own key, only if Ritik hands it to her.
  From Nov 6: the re-reads (Nov 7 and 9); B18's table, Nov 18; slides 2, 6, 7 and 8, Nov 20.

**The dates to Nov 24.**
- **Nov 5:** two Sol accounts: Ritik's pull (done); A40 pre-registered, its Voyager targets started at
  09:50 (about 9 h). **Nov 6:** the feeder's 07:00 rule; Arsha's bundle and the last push to `trackB-main`; A40's data to Sol
  (about), then its lines.
- **Nov 7:** Shrey's merge (C19). **Nov 8:** Gate 2. **Nov 11:** the 30's rule, 09:00 (E2's and A40's lines).
  **Nov 12, 15, 18:** merges.
- **Nov 15, 23:59:** runs end (A39 on E2, A40 and B20 read partial if not complete). **Nov 17:** A39, A40 and B20
  read.
- **Nov 18:** the results freeze. **Nov 20:** Gate 3's final statement, the report bullets and the slides.
- **Nov 22:** the report draft. **Nov 23:** the rehearsal. **Nov 24:** the final presentation and report.

**Only Ritik or a teammate can do these.** Sending the messages and bundles; approving any rule or amendment; any Sol
change on Ritik's account beyond reading and a safe pull; every Sol command on Arsha's account (hers, typed in her own
login); Arsha's and Shrey's own track work.
