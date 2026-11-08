## In plain words (Ritik's page, as of Nov 7, 20:45: A39 read; the trade-off explored, post hoc; L6 pre-registered, not run; the scorecard; B1R2 running; earlier 13:48: A40, A41 and A42 read; the counting bug fixed; earlier Nov 6, 23:22: A40's training verified, B20 complete, Track C merged; edited by hand in `docs/status/ONE_PAGE.md`)

**Done.**
- **44 findings** (F1–F44, in `docs/FINDINGS.md`). **Gate 3 is met** (F28). **B24 is read** (F40): a source's
  authority adds to its pull.
- **The fix, read on E2 today** (F41–F44; `docs/status/FIX_SO_FAR.md`):
  - **A40, consistency training,** follows the wrong hint in 12% of runs against the one-line instruction's 33%. But
    it takes the correct hint in 76% against 91%.
  - By its pre-registered rule that is **"fewer, but costs acceptance"**: it ignores hints, the right ones too. It is a
    trade, not a fix. It passes Gate 3's rule against base.
  - **A42, A40 with the note,** gets the same reading at a larger cost.
  - **A41:** inside the model, A40 is the first fix that changes how the hint is read off. Its weights act in layers
    0–14, before the readout, and remove more of the hint's pull than LoRA's.
  - **A39 (F44, read 20:33):** marking every tool output "unverified" has **no effect** alone on the tool turn. With
    the instruction, it follows fewer wrong hints there (18% against 32%) but takes fewer correct ones (76% against
    88%): "adds, costs acceptance". LoRA + note is "fewer than the instruction" by R2, which reads following only
    (25% against 33%), with acceptance 9 points lower beside it. Gate 3's rule passes again on E2, with power.
  - **So nothing beats the instruction without a cost to correct hints.** The scorecard against the original plan is
    FINDINGS' story item 7 (and the README).
  - **Exploratory (post hoc):** A40 gives more correct answers than the instruction only when under 36% [22, 50] of
    the tool's answers are right. When LoRA follows a wrong hint, its answer names it 91% of the time against the
    instruction's 50% (keyword). **L6,** a hand-label check of that, is pre-registered and not run: Ritik decides.
- **Gate 2:** a tool's hint pulls harder than the user's on all five models. The label part is **not met** (Ritik
  against the AI judges' majority: 0.472 and 0.234, under 0.6). The statement is ready to mark **Nov 8**.
- **The labels are final** (L3, Nov 4; rater 2 was an AI model, ChatGPT 5 Astra High, not Shrey).
- **Track C is done early:** C19, C25, C20 and C26 were run and read Nov 6 (FC1–FC4), merged Nov 6 at 23:17; C24's
  tables merged Nov 7.
- **B20 is complete** (Arsha's account, Nov 6, 21:11). By its rule she reads it now, in her own log.

**Running.**
- **Only B1R2 is left** (Sol read-only, 20:22): 31 of 40 parts ended, 4 pending (32–35), 5 to submit (36–40), then 4
  sweeps; 291 runs left. Sol gives no start time.
  - Parts 21 and 24 "FAILED, exit 1" at 2:25–2:26: the planned stop at Slurm's warning (6 and 7 runs left, for the
    sweeps), like part 06 on Nov 6.
  - Parts 14 and 20 left 3 runs "out of memory alone"; the sweeps retry them, and they may run out of memory again.

**On track?**

| item | state | why |
|---|---|---|
| Gate 2 (Nov 8) | on track | the statement is written: the gap is clear on 5 of 5 models; the label part is not met (0.472 and 0.234) |
| Gate 3's final statement (Nov 20) | on track | met Oct 31 (F28); A39's powered replication passes (F44) |
| A39 on E2 and the 30 | **read Nov 7 (F44)** | the wrapper alone "no effect"; wrapper + note "adds, costs acceptance"; LoRA + wrapper "adds to both"; LoRA + note "fewer than the instruction" (acceptance −9 beside it) |
| L6 (a label check) | pre-registered, not run | 168 rows, about 3½ hours of labeling; Ritik's yes or no; the sheet by about Nov 12 if yes |
| A40 | **read Nov 7 (F41)** | "fewer, but costs acceptance" against the instruction and LoRA; R1 passes |
| A41 | **read Nov 7 (F42)** | "stops the readout, before them"; "A40 removes more of the hint's pull than LoRA" |
| A42 | **read Nov 7 (F43)** | "fewer, but costs acceptance"; R3 "adds, costs acceptance"; R1 passes |
| B1R2 | on track | 31 of 40 parts ended at 20:22; 9 parts and 4 sweeps left, no start time from Sol; read when complete, partial at Nov 15 23:59 |
| B20 (Arsha reads now) | runs done | complete Nov 6 against its design; she reads it by its rule (§10), in her own log |
| Track C (Shrey) | done early | FC1–FC4 merged Nov 6; C24 (Track C's tables) merged Nov 7, and Shrey's figures and tables placed in `docs/paper/` |
| The labels | done | L3 final (Nov 4); L4 part 1 Nov 3; L4 part 2 (a SHOULD) is not labelled |
| The report and slides (Nov 18–24) | on track | REPORT has bullets for F1–F44 (and §7's labelled exploratory bullet) and Track C's FC1–FC4; §5, §6, §8 and §9 are final; the writing plan for Nov 18–24 is in PLAN ("The report's state") |

**Projected finishes** (Sol's own dates come from `squeue --start`, which gives none tonight).
- **B1R2:** the earlier projection (parts done by about Nov 8, 02:00–03:00) has slipped: at 20:22, 9 parts were still to
  start. Parts take 0:41–2:26 each, so the parts and the 4 sweeps need several more hours once they start.
- **Then Ritik's queue is empty.** No other pending work is planned for the account (L6, if run, needs no GPU).
- **`reserve=240:2`** was there to keep room for A40's training and E2. Those lines have ended, so it now only paces
  B1R2. Dropping it is a queue-file edit, which is Ritik's call (see below).

**Waiting on whom.**
- **Ritik:**
  - **L6:** yes or no (168 rows, about 3½ hours of labeling; the sheet by about Nov 12 if yes);
  - **Nov 8:** mark Gate 2 (PLAN's statement, this page, TODO's G2);
  - **Nov 8, once every B1R2 part has started:** pull on Sol, by the safety diff (today's counting fix touches
    `finetune/`, which B1R2's queued parts load);
  - **optional:** drop B1R2's `reserve=240:2` (a queue-file edit) so its last parts go in faster.
- **Shrey:** merged `origin/main` back and reinstalled the hooks (Nov 7, 09:15); C24 done and merged Nov 7. Next: merge
  `origin/main` back again; check-ins Nov 12, 15 and 18; Track C's report bullets are in REPORT already.
- **Arsha:** read B20 by its rule, in her own log on `trackB-main` and in FINDINGS_B; merge `origin/main` and rerun
  `--install`; the re-reads; B18's table, Nov 18; slides 2, 6, 7 and 8, Nov 20.

**The dates to Nov 24.**
- **Nov 7:** A40, A41, A42 and A39 read (F41–F44). **Nov 8:** Gate 2; B1R2's last parts, then its sweeps.
- **Nov 11:** the 30's rule, 09:00 (nothing left to drop). **Nov 12, 15, 18:** check-ins and merges.
- **Nov 15, 23:59:** runs end (B1R2 read partial if not complete). **By Nov 17:** B1R2 read; B20 by Arsha.
- **Nov 18:** the results freeze. **Nov 20:** Gate 3's final statement, Track B's and Track C's report bullets, the
  slides.
- **Nov 22:** the report draft. **Nov 23:** the rehearsal. **Nov 24:** the final presentation and report.

**Only Ritik or a teammate can do these.** Sending messages and bundles; approving any rule or amendment; any Sol
change on Ritik's account beyond reading and a safe pull (a queue-file edit included); every Sol command on Arsha's
account (hers, typed in her own login); Arsha's and Shrey's own track work.
