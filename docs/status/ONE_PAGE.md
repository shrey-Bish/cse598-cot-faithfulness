## In plain words (Ritik's page, as of Nov 13, 09:56: L6 read, F45; B1R2's runs complete; Sol pulled; earlier Nov 8, 15:14: Gate 2 marked; Arsha's B20 merged; the conclusion made specific; edited by hand in `docs/status/ONE_PAGE.md`)

**Done.**
- **45 findings** (F1–F45, in `docs/FINDINGS.md`) and Track B's **FB1** (B20, merged Nov 8). **Gate 2 is marked**
  (Nov 8). **Gate 3 is met** (F28). **B24 is read** (F40): a source's authority adds to its pull.
- **L6, read Nov 13 (F45): in hand labels, LoRA's answer is more honest about a wrong hint it followed.** When LoRA
  follows a wrong hint on E2, its final answer says so in 37 of 42 runs, against the instruction's 18 of 42 (+45
  [+25, +64] points): "discloses more than the instruction, in labels". Ritik's labels are final; Claude Opus, the
  check, agreed at kappa 0.96. No LoRA answer claims to reject the hint it ends on. Ritik guessed "trained" on 32 of
  LoRA's 42 rows, so the sheet wasn't blind in practice.
- **Gate 2, marked Nov 8: met (the gap), not met (the labels).** A tool's hint pulls harder than the user's on all
  five Track B models and on B20's three new families (10 of 10 readings, FB1). The label part is not met (0.472 and
  0.234, under 0.6).
- **B20, read by Arsha (Nov 7, FB1; merged Nov 8).** Tools beat users in Gemma 4, Nemotron 3 Nano and Granite 4.2;
  whether the tool's form adds to its claim depends on the family and the channel.
- **The fix, read on E2** (F41–F45; `docs/status/FIX_SO_FAR.md`):
  - **A40** follows the wrong hint in 12% of runs against the instruction's 33%, but takes the correct hint in 76%
    against 91%: "fewer, but costs acceptance", a trade. **A42** the same at a larger cost. **A41:** A40 acts in
    layers 0–14.
  - **A39 (F44):** marking tool output "unverified" has **no effect** alone; with the instruction it "adds, costs
    acceptance". LoRA + note is "fewer than the instruction" by R2 (−8 [−12, −4]) at an acceptance cost of −9 [−13,
    −5].
  - **LoRA follows as often as the instruction (F44), but says so more when it does (F45).**
  - **So nothing beats the instruction without a cost to correct hints,** and the fix belongs at the system level:
    provenance labels alone don't help; independent verification does (Track C's checker, F24). FINDINGS' story item
    7 is the scorecard.
- **The labels:** L3 final (Nov 4); L4 part 1 (Nov 3); **L6 read (Nov 13)**. L4 part 2 (a SHOULD) is not labelled.
- **Track C is done early:** FC1–FC4 (Nov 6); C24's tables merged Nov 7.

**Running.**
- **Nothing.** B1R2's runs are complete: its 40 parts ended Nov 8 and its last sweeps Nov 9 (05:07, 05:29). Sol was
  pulled Nov 13 (`97c0628`), and its fixed count gives 0 runs left. The feeder still ticks every 5 minutes, with an
  empty queue.
- **The Nov 11 rule** (applied by the feeder at 09:00:46): "the 30 runs". The 30's lines had all ended Nov 6: no
  effect.

**On track?**

| item | state | why |
|---|---|---|
| Gate 2 (Nov 8) | **marked Nov 8** | met (the gap: 5 of 5 Track B models and B20's three families); not met (the labels) |
| Gate 3's final statement (Nov 20) | on track | met Oct 31 (F28); A39's powered replication passes (F44) |
| L6 (a label check) | **read Nov 13 (F45)** | "discloses more than the instruction, in labels": 37 of 42 against 18 of 42; kappa 0.961 with J-opus |
| B1R2 | **runs complete Nov 9** | Ritik reads it by its rule (B1's, paired by question), by Nov 17 |
| A39, A40, A41, A42 | **read Nov 7 (F41–F44)** | A40 and A42 trade acceptance; the wrapper alone no effect; LoRA + note R2 at an acceptance cost |
| B20 (Arsha) | **read Nov 7 (FB1), merged Nov 8** | R1 clear in 10 of 10; R2 split by family and channel |
| Track C (Shrey) | done early | FC1–FC4 merged Nov 6; C24 merged Nov 7 |
| The report and slides (Nov 18–24) | on track | REPORT has bullets for F1–F45, FB1 and FC1–FC4, and §12's conclusion bullets; the writing plan is in PLAN |

**Waiting on whom.**
- **Ritik:**
  - **B1R2:** read it by its rule, by Nov 17 (copy back its numbers-only files, `provenance_job.py report`, B1's rule;
    RUNBOOK §14). Its runs are complete.
  - **Nov 16 or Nov 18:** stop the feeder (`touch /scratch/$USER/trackA/feeder.stop`, `scrontab -r`); nothing is
    left in the queue.
- **Arsha:** merge `origin/main` back into `trackB-main` (Ritik sent the message) and push; B18's table with B20's
  rows, Nov 18; slides 2, 6, 7 and 8, Nov 20.
- **Shrey:** merge `origin/main` back; check-ins Nov 15 and 18.

**The dates to Nov 24.**
- **Nov 13:** L6 read (F45); Sol pulled; B1R2 complete. **Nov 15:** check-ins and merges; 23:59, runs end (nothing
  is running).
- **By Nov 17:** B1R2 read. **Nov 18:** the results freeze; check-ins and merges. **Nov 20:** Gate 3's final
  statement, Track B's and Track C's report bullets, the slides.
- **Nov 22:** the report draft. **Nov 23:** the rehearsal. **Nov 24:** the final presentation and report.
- **Missed:** the Nov 12 check-ins and merges (no session ran Nov 9–12; nothing new was on either teammate's branch
  on Nov 13).

**Only Ritik or a teammate can do these.** Sending messages and bundles; approving any rule or amendment; any Sol
change on Ritik's account beyond reading and a safe pull (the feeder's stop included); every Sol command on Arsha's
account; Arsha's and Shrey's own track work.
