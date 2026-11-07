## In plain words (Ritik's page, as of Nov 7, 13:48: A40, A41 and A42 read; A39 complete; B1R2 running; the counting bug fixed; earlier Nov 6, 23:22: A40's training verified, B20 complete, Track C merged; edited by hand in `docs/status/ONE_PAGE.md`)

**Done.**
- **43 findings** (F1–F43, in `docs/FINDINGS.md`). **Gate 3 is met** (F28). **B24 is read** (F40): a source's
  authority adds to its pull.
- **The fix, read on E2 today** (F41–F43; `docs/status/FIX_SO_FAR.md`):
  - **A40, consistency training,** follows the wrong hint in 12% of runs against the one-line instruction's 33%. But
    it takes the correct hint in 76% against 91%.
  - By its pre-registered rule that is **"fewer, but costs acceptance"**: it ignores hints, the right ones too. It is a
    trade, not a fix. It passes Gate 3's rule against base.
  - **A42, A40 with the note,** gets the same reading at a larger cost.
  - **A41:** inside the model, A40 is the first fix that changes how the hint is read off. Its weights act in layers
    0–14, before the readout, and remove more of the hint's pull than LoRA's.
  - **So no fix beats the instruction by its rule yet.** A39 (the wrapper and the combinations) is next.
- **Gate 2:** a tool's hint pulls harder than the user's on all five models. The label part is **not met** (Ritik
  against the AI judges' majority: 0.472 and 0.234, under 0.6). The statement is ready to mark **Nov 8**.
- **The labels are final** (L3, Nov 4; rater 2 was an AI model, ChatGPT 5 Astra High, not Shrey).
- **Track C is done early:** C19, C25, C20 and C26 were run and read Nov 6 (FC1–FC4), merged Nov 6 at 23:17; C24's
  tables merged Nov 7.
- **B20 is complete** (Arsha's account, Nov 6, 21:11). By its rule she reads it now, in her own log.

**Running.**
- **Ritik's account ran A40's E2, A41 and A42 overnight; all ended ok** (helper A, Sol read-only, 13:18):
  - A40's 16 parts ended at 01:50, A41's swap at 01:20 and its Step 10 at 07:25, A42's 16 parts at 07:51;
  - the two sweeps weren't needed;
  - every part served its own requests on its own port;
  - nothing failed: `a41-step10`'s exit 2 was its planned stop at the limit, and its again-line finished.
- **Only B1R2 is left:** 19 of 40 parts done, 3 running, 4 pending, 13 to submit, then 4 sweeps. 556 of 1,200 runs are
  left.
  - Two parts (14 and 20) left 3 runs "out of memory alone"; the sweeps retry them.
- **A39 is complete,** on E2 and the 30. Sol's "54 runs left" was a counting bug: the code took a part's older
  `not_run` over a sweep's `ok`. The readers were never affected. Fixed today, with tests (the A39 log's §22).

**On track?**

| item | state | why |
|---|---|---|
| Gate 2 (Nov 8) | on track | the statement is written: the gap is clear on 5 of 5 models; the label part is not met (0.472 and 0.234) |
| Gate 3's final statement (Nov 20) | on track | met Oct 31 (F28); waits on A39 (complete; read by Nov 17) |
| A39 on E2 and the 30 | complete, to read | every run has an ok record (counted Nov 7); its rule reads it once complete; Ritik picks the day, by Nov 17 |
| A40 | **read Nov 7 (F41)** | "fewer, but costs acceptance" against the instruction and LoRA; R1 passes |
| A41 | **read Nov 7 (F42)** | "stops the readout, before them"; "A40 removes more of the hint's pull than LoRA" |
| A42 | **read Nov 7 (F43)** | "fewer, but costs acceptance"; R3 "adds, costs acceptance"; R1 passes |
| B1R2 | on track | 19 of 40 parts done at 13:18; parts project to end about Nov 8, 02:00–03:00, then 4 sweeps (under an hour each); read when complete, partial at Nov 15 23:59 |
| B20 (Arsha reads now) | runs done | complete Nov 6 against its design; she reads it by its rule (§10), in her own log |
| Track C (Shrey) | done early | FC1–FC4 merged Nov 6; C24 (Track C's tables) merged Nov 7, and Shrey's figures and tables placed in `docs/paper/` |
| The labels | done | L3 final (Nov 4); L4 part 1 Nov 3; L4 part 2 (a SHOULD) is not labelled |
| The report and slides (Nov 18–24) | on track | REPORT has bullets for F1–F43 and Track C's FC1–FC4; §5, §6, §8 and §9 are final; the writing plan for Nov 18–24 is in PLAN ("The report's state") |

**Projected finishes** (projections from today's pace; Sol's own dates come from `squeue --start`).
- **B1R2's parts:** about 1.5 an hour today (median part 86 minutes, at most about 4 at once under `reserve=240:2`), so
  the 40 end about Nov 8, 02:00–03:00. They could end by about 21:00 tonight if nothing waits. Then 4 sweeps.
- **Then Ritik's queue is empty** (about Nov 8 morning). No other pending work is planned for the account.
- **`reserve=240:2`** was there to keep room for A40's training and E2. Those lines have ended, so it now only paces
  B1R2. Dropping it is a queue-file edit, which is Ritik's call (see below).

**Waiting on whom.**
- **Ritik:**
  - **any day, by Nov 17:** read A39 (complete). Its reader and figures are ready (CHECKIN §3);
  - **Nov 8:** mark Gate 2 (PLAN's statement, this page, TODO's G2);
  - **Nov 8, once every B1R2 part has started:** pull on Sol, by the safety diff (today's counting fix touches
    `finetune/`, which B1R2's queued parts load);
  - **optional:** drop B1R2's `reserve=240:2` (a queue-file edit) so its last parts go in faster.
- **Shrey:** merged `origin/main` back and reinstalled the hooks (Nov 7, 09:15); C24 done and merged Nov 7. Next: merge
  `origin/main` back again; check-ins Nov 12, 15 and 18; Track C's report bullets are in REPORT already.
- **Arsha:** read B20 by its rule, in her own log on `trackB-main` and in FINDINGS_B; merge `origin/main` and rerun
  `--install`; the re-reads; B18's table, Nov 18; slides 2, 6, 7 and 8, Nov 20.

**The dates to Nov 24.**
- **Nov 7:** A40, A41 and A42 read (F41–F43). **Nov 8:** Gate 2; B1R2's parts end, then its sweeps.
- **Nov 11:** the 30's rule, 09:00 (nothing left to drop). **Nov 12, 15, 18:** check-ins and merges.
- **Nov 15, 23:59:** runs end (B1R2 read partial if not complete). **By Nov 17:** A39 and B1R2 read; B20 by Arsha.
- **Nov 18:** the results freeze. **Nov 20:** Gate 3's final statement, Track B's and Track C's report bullets, the
  slides.
- **Nov 22:** the report draft. **Nov 23:** the rehearsal. **Nov 24:** the final presentation and report.

**Only Ritik or a teammate can do these.** Sending messages and bundles; approving any rule or amendment; any Sol
change on Ritik's account beyond reading and a safe pull (a queue-file edit included); every Sol command on Arsha's
account (hers, typed in her own login); Arsha's and Shrey's own track work.
