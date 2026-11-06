## In plain words (Ritik's page, as of Nov 6, 14:48: A40 training queued; B1R2 revived; emails hashed; C25 done; A40's data and lines; A41 and A42; only the team commits; earlier 09:56, Arsha's handoff; Sol as of Ritik's Nov 6 morning block, his feeder at 10:56; edited by hand in `docs/status/ONE_PAGE.md`)

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
- **Ritik's account: every line has ended** (10:56 Nov 6, the feeder: 116 lines, 106 ok, 10 not needed; status only,
  nothing read). A39 on E2 (87 lines) and on the 30 (29 lines) are done running; both are read Nov 17. The Nov 6
  07:00 rule said no cut (60.6 GPU-hours), so nov11 has nothing left to drop (the A39 log's §20). **The account has
  sat idle since**, until Ritik's pull and rsync: **`a40-train-1` went in at 14:15:59** (job 622511, its data check
  passing), pending on priority. **B1R2 is revived** (Nov 6, the A39 log's §21): its 44 lines last, each with
  `reserve=240:2`, so they fill only room A40's, A41's and A42's lines can't use.
- **B20 (Arsha's account, from her setup on Nov 6):** no B20 job is queued. Granite has 849 runs left and Gemma
  1,784, on 3:00 lines (Granite 8, Gemma 12), one chain a model, question by question (the B20 log's §19). Her setup:
  `docs/trackB/SOL_ARSHA.md`.
- **A40, a new fine-tune** (Ritik's decision g; pre-registered Nov 5, the 09:18 log): LoRA trained on the model's own
  reasoning written without the hint (bias-augmented consistency training), read on E2. **Its data is done** (Nov 6
  05:03, after a pause while the Mac slept): 979 of 979 records, 883 examples (96 dropped by its rules), correct to
  wrong 0.47, 981 training examples (its §17). Its 20 lines go in with Ritik's pull; the feeder submits `a40-train-1`
  only once its check of the data on Sol passes (its §11, Nov 6).
- **A41 and A42, pre-registered Nov 6** (the 11:21 and 11:22 logs), so Ritik's account doesn't sit idle: A41 puts
  A40's weights in A18's swap and Step 10 (does consistency training change the readout at 15, 19 and 23?); A42 is
  A40 with the one-line note on E2. Both after A40's training.

**On track?**

| item | state | why |
|---|---|---|
| Gate 2 (Nov 8) | on track | the statement is written: the gap is clear on 5 of 5 models; the label part is not met (0.472 and 0.234) |
| Gate 3's final statement (Nov 20) | on track | met Oct 31 (F28); waits on A39 on E2 (read Nov 17, partial by its §18 if not complete) |
| A39 on E2 (read Nov 17) | runs done | every E2 line ended by Nov 6 10:56 (status only; the A39 log's §20) |
| A39 on the 30 (read Nov 17) | runs done | all 29 lines ended by Nov 6 10:56, having gone in as places freed; the Nov 6 07:00 rule said no cut, and nov11 has nothing left to drop (§20) |
| A40 (read Nov 17) | on track | data done Nov 6 (883 examples); `a40-train-1` in at 14:15 (job 622511, pending), its data check passed; about 20–25 GPU-h (training 3.2, E2 16–21); read partial at Nov 15 23:59 if not complete (its §10) |
| A41 (read when done) | on track | pre-registered Nov 6; ~4 GPU-h after A40's training; its code and tests in (`8952e24`) |
| A42 (read Nov 17) | on track | pre-registered Nov 6; 16–21 GPU-h after A40's training; partial at Nov 15 23:59 if not complete |
| B1R2 (read Nov 17) | on track | revived Nov 6 (the A39 log's §21, before any B1R2 run): 44 lines last in Ritik's queue, `reserve=240:2` (about 4 parts at a time beside A40's training); about 66 GPU-h; partial at Nov 15 23:59 by §13.8 |
| B20 (Arsha reads Nov 17) | on track | the cause is fixed and confirmed (T13), and the job size amended (the B20 log's §19): 3:00 lines, twice the jobs the measured pace needs (Granite 8 for about 4, Gemma 12 for about 6). It runs on Arsha's own account, whose fair share is likely far above Ritik's 0.0019. Bound by Gemma's ~6 jobs and the waits between them; it starts after her setup (Nov 6); read partial at Nov 15 23:59 if not complete |
| Track C (Shrey: C20, C26 Nov 15) | on track | on `trackC-main`, as Shrey with no AI line: setup (09:42), C19 (10:31) and C25, due Nov 12 (14:20), each run and read; path check clean, no merge conflict; Ritik merges Nov 7 (the 14:35 log's §3) |
| The labels | done | L3 final with the re-look (Nov 4 21:31; rows 67 and 290 kept as recorded, Nov 5); L4 part 1 Nov 3; L4 part 2 (a SHOULD) is not labelled |
| Arsha's handoff (Nov 6) | on track | built Nov 6, 09:54 (START_HERE §0, §1, §9–§11; SOL_ARSHA from `trackB-main`; `trackB_20261106.zip`, 51 files, verified; commits as Arsha only); `trackB-main` pushed for the last time (decision d), so the branch is hers. Ritik sends the zip's link and the note (the 09:10 log's §5); his own Sol block (its §4) comes before her steps 4–8 |
| The report and slides (Nov 20–24) | on track | REPORT has the bullets for F1–F40; 10 slides made (1–4, 6–11), 2 waiting (5, the labels; 12, Shrey's, Nov 18); A39 and B20 go in after Nov 17 |

**Projected finishes** (projections, rough: from the logs' GPU-hour estimates and the 11:07 log's helper D; Sol's
own dates come from `squeue --start`). Two accounts, each with its own 10 places and 960 GPU-minutes.

| Ritik's account, in the queue's order | GPU-h left | starts |
|---|---|---|
| A39 on E2 and on the 30 | 0: every line ended (Nov 6 10:56) | — |
| A40: training (three 2:00 jobs in a chain, about 3.3), then E2 (16 parts and a sweep, about 16–21) | about 20–25 | at the first tick after Ritik's pull and rsync (its data check) |
| A41: A18's swap and Step 10 with A40's weights | about 4 | after A40's training, beside E2's second wave |
| A42: A40 with the note on E2 (16 parts and a sweep) | about 16–21 | after A40's training |
| B1R2: B1's span on E2 (40 parts and 4 sweeps; revived Nov 6) | about 66 | now, about 4 parts at a time, in room the lines above can't use (`reserve=240:2`) |

- **When his queue runs dry (projection, the 11:07 log):** A40's lines alone, about 8–18 hours after the pull; A41 adds
  no time; A42 adds about 2.5–6 hours. B1R2 adds about 66 GPU-h at 4–5 parts at a time, so the queue now lasts to
  about Nov 8–10, if Sol's waits are like this week's.
- **During A40's training B1R2 fills the places the chain leaves idle** (revived Nov 6). The cost, said in its §21:
  part of A40's first E2 wave may wait up to one B1R2 part (2:30).

| Arsha's account (B20) | runs left | lines of 3:00 | jobs needed (the B20 log's §19) |
|---|---|---|---|
| Granite | 849 | 8 | about 4 |
| Gemma | 1,784 | 12 | about 6 |
| Nemotron | 0: done | none | — |

- **B20 is bound by Gemma's chain, not by GPU-hours (projection).** One job a model at a time, Granite's and Gemma's
  side by side (360 of her 960 GPU-minutes). Gemma's ~6 jobs of 3:00, plus the waits between them, set B20's finish.
  The first start comes after her setup (Nov 6). Her fair share is likely far above Ritik's 0.0019
  (`docs/trackB/SOL_ARSHA.md`), so her waits should be shorter than his have been; her `squeue --start` will say.
- **What gives way first if Sol slows:** A42 and A40 read partial, then B20 read partial, each at Nov 15 23:59
  ("partial: N of 120 questions" for A40 and A42; "partial: N of 54 questions" for each B20 model).
- **The Nov 6 07:00 rule said "no cut"** (60.6 GPU-hours from Nov 4 12:36; the A39 log's §20).

**Waiting on whom.**
- **Ritik:**
  - **now: his Sol block** (the 14:35 log): the safety diff, the pull (B1R2's lines and the reserve), the feeder's
    `--dry-run` showing B1R2's first parts last; and close B20's three text records (`chmod g-r`), since Arsha's copy
    matched (14:31);
  - **Nov 7:** merge Shrey's `trackC-main` (setup, C19, C25), with the steps in the 14:35 log's §3;
  - done Nov 6: both handoffs and both notes sent; his Sol block for A40 (`a40-train-1` in); B1R2 revived; the team
    emails stored as hashes (Arsha's two included).
- **Shrey:** C19 and C25 done on `trackC-main` (Nov 6; merged Nov 7); C20 and C26 by Nov 15; slides 11–12 by Nov 18. Check-ins on Nov 7, 12, 15 and 18.
- **Arsha:** her Sol setup: steps 1–6 done (Nov 6; her copy matched), steps 7–8 (her feeder, scrontab) next; then B20
  on her own feeder, read Nov 17. Before her first commit, merge `origin/main`, rerun `--install`, commit with her Gmail.
  From Nov 6: the re-reads (Nov 7 and 9); B18's table, Nov 18; slides 2, 6, 7 and 8, Nov 20.

**The dates to Nov 24.**
- **Nov 5:** two Sol accounts: Ritik's pull (done); A40 pre-registered, its Voyager targets started at
  09:50. **Nov 6:** the 07:00 rule said no cut; every E2 and 30 line ended (10:56); A40's data done; both handoffs
  sent and the last push to `trackB-main`; A40's lines, then A41's and A42's, in with Ritik's pull.
- **Nov 7:** Shrey's merge (setup, C19, C25). **Nov 8:** Gate 2.
  **Nov 11:** the 30's rule, 09:00 (nothing left to drop).
  **Nov 12, 15, 18:** merges.
- **Nov 15, 23:59:** runs end (A40, A42, B1R2 and B20 read partial if not complete). **Nov 17:** A39, A40, A42, B1R2
  and B20 read (A41 when done).
- **Nov 18:** the results freeze. **Nov 20:** Gate 3's final statement, the report bullets and the slides.
- **Nov 22:** the report draft. **Nov 23:** the rehearsal. **Nov 24:** the final presentation and report.

**Only Ritik or a teammate can do these.** Sending the messages and bundles; approving any rule or amendment; any Sol
change on Ritik's account beyond reading and a safe pull; every Sol command on Arsha's account (hers, typed in her own
login); Arsha's and Shrey's own track work.
