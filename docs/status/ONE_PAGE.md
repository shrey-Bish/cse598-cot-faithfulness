## In plain words (Ritik's page, as of Nov 8, 15:14: Gate 2 marked; Arsha's B20 merged, FB1; L6's sheet built; B1R2's 40 parts ended; the conclusion made specific; earlier Nov 7, 20:45: A39 read; the trade-off explored, post hoc; the scorecard; edited by hand in `docs/status/ONE_PAGE.md`)

**Done.**
- **44 findings** (F1–F44, in `docs/FINDINGS.md`) and Track B's **FB1** (B20, in `docs/trackB/FINDINGS_B.md`, merged
  Nov 8). **Gate 2 is marked** (below). **Gate 3 is met** (F28). **B24 is read** (F40): a source's authority adds to
  its pull.
- **Gate 2, marked Nov 8: met (the gap), not met (the labels).** A tool's hint pulls harder than the user's on all
  five Track B models and on B20's three new families (10 of 10 readings, FB1). The label part is not met (Ritik
  against the AI judges' majority: 0.472 and 0.234, under 0.6), with its descriptive sentence (PLAN).
- **B20, read by Arsha (Nov 7, FB1; merged Nov 8, `5f767e4`):** tools beat users in Gemma 4, Nemotron 3 Nano and
  Granite 4.2. Whether the tool's form adds to its claim depends on the family and the channel (beyond it in 5 of 10
  readings). A call makes the answer barer after Granite's own call and Nemotron's inserted turn with thinking off;
  Nemotron's bare answer falls with thinking. Labelled: the inserted tool turn, Granite thinking on only, temperature
  1.0.
- **The fix, read on E2** (F41–F44; `docs/status/FIX_SO_FAR.md`):
  - **A40, consistency training,** follows the wrong hint in 12% of runs against the one-line instruction's 33%. But
    it takes the correct hint in 76% against 91%: **"fewer, but costs acceptance"**, a trade, not a fix. **A42,** A40
    with the note, the same at a larger cost. **A41:** A40's weights act in layers 0–14, before the readout.
  - **A39 (F44):** marking every tool output "unverified" has **no effect** alone on the tool turn. With the
    instruction, it follows fewer wrong hints there (18% against 32%) but takes fewer correct ones (76% against 88%):
    "adds, costs acceptance". LoRA + note is "fewer than the instruction" by R2 (25% against 33%; −8 [−12, −4]) at an
    acceptance cost of −9 [−13, −5]. Gate 3's rule passes again on E2, with power.
  - **So nothing beats the instruction without a cost to correct hints,** and the fix belongs at the system level:
    provenance labels alone don't help (the wrapper alone, "no effect"); independent verification does (Track C's
    checker stopped all 53 wrong tool answers on fresh items, F24). The scorecard is FINDINGS' story item 7 (and the
    README).
  - **Exploratory (post hoc):** A40 gives more correct answers than the instruction only when under 36% [22, 50] of
    the tool's answers are right. When LoRA follows a wrong hint, its answer names it 91% of the time against the
    instruction's 50% (keyword).
- **L6** (a hand-label check of that, LoRA against the instruction): Ritik's yes Nov 8, reduced to 84 rows (amendment
  `615452b`); the builder `a457b3c`; **the sheet is built**: `cot-disclosure/results/labels/L6/sheet_L6.csv`.
- **The labels are final** (L3, Nov 4; rater 2 was an AI model, ChatGPT 5 Astra High, not Shrey).
- **Track C is done early:** C19, C25, C20 and C26 read Nov 6 (FC1–FC4); C24's tables merged Nov 7.

**Running.**
- **Only B1R2 is left** (Sol read-only, Nov 8 14:55): all 40 parts ended by 06:35 (parts 06, 21, 24 and 37 at the
  planned stop at Slurm's warning; their runs left go to the sweeps). Sweep 2 done, sweep 3 not needed; **sweeps 1 and
  4 pending** (11 and 9 runs left when submitted), reason `Priority`, no start time from Sol.
  - Parts 14 and 20 left 3 runs "out of memory alone"; the sweeps retry them, and they may run out of memory again.
- **`reserve=240:2` was not dropped:** every B1R2 line had gone in by 06:35, and `reserve=` only gates the feeder's
  submissions, so the edit would change nothing.

**On track?**

| item | state | why |
|---|---|---|
| Gate 2 (Nov 8) | **marked Nov 8** | met (the gap: 5 of 5 Track B models and B20's three families); not met (the labels: 0.472 and 0.234) |
| Gate 3's final statement (Nov 20) | on track | met Oct 31 (F28); A39's powered replication passes (F44) |
| A39 on E2 and the 30 | **read Nov 7 (F44)** | the wrapper alone "no effect"; wrapper + note "adds, costs acceptance"; LoRA + wrapper "adds to both"; LoRA + note "fewer than the instruction" (−8 [−12, −4]) at an acceptance cost of −9 [−13, −5] |
| L6 (a label check) | **sheet built Nov 8** | 84 rows, LoRA against the instruction; Ritik labels it (about 1¾ hours), then J-opus, then its §5 rule |
| A40, A41, A42 | **read Nov 7 (F41–F43)** | A40 and A42 "fewer, but costs acceptance"; A41 "stops the readout, before them" |
| B1R2 | on track | 40 of 40 parts ended Nov 8; sweeps 1 and 4 pending, no start time from Sol; read when complete, partial at Nov 15 23:59 |
| B20 (Arsha) | **read Nov 7 (FB1), merged Nov 8** | R1 clear in 10 of 10; R2 split by family and channel; in the story, README and REPORT §2–§4 and §6 |
| Track C (Shrey) | done early | FC1–FC4 merged Nov 6; C24 merged Nov 7 |
| The labels | done | L3 final (Nov 4); L4 part 1 Nov 3; L4 part 2 (a SHOULD) is not labelled; L6 in progress |
| The report and slides (Nov 18–24) | on track | REPORT has bullets for F1–F44, FB1 and FC1–FC4, §7's labelled exploratory bullet and §12's conclusion bullets; the writing plan is in PLAN |

**Projected finishes** (Sol's dates come from `squeue --start`, which gives none today).
- **B1R2:** two sweeps of at most 2:30 each, once Sol starts them; then it is read when complete (by Nov 17).
- **Then Ritik's queue is empty.** L6 needs no GPU.

**Waiting on whom.**
- **Ritik:**
  - **L6:** label `cot-disclosure/results/labels/L6/sheet_L6.csv` (84 rows, about 1¾ hours; the `label_final`,
    `guess_trained` and `note` columns). Open only that file: `texts_L6.jsonl` and `key_L6.csv` beside it name the
    systems. Then J-opus runs (2 batches of 42), then the reading;
  - **once sweeps 1 and 4 have started:** the Sol pull, by the safety diff (Nov 7's counting fix touches
    `finetune/`, which the sweeps load).
- **Arsha:** merge `origin/main` back into `trackB-main` (the B20 merge, `5f767e4`) and rerun `--install`; B18's table
  with B20's rows, Nov 18; slides 2, 6, 7 and 8, Nov 20.
- **Shrey:** merge `origin/main` back; check-ins Nov 12, 15 and 18.

**The dates to Nov 24.**
- **Nov 8:** Gate 2 marked; B20 merged; L6's sheet built. **Nov 11:** the 30's rule, 09:00 (nothing left to drop).
- **Nov 12, 15, 18:** check-ins and merges. **Nov 15, 23:59:** runs end (B1R2 read partial if not complete).
- **By Nov 17:** B1R2 read. **Nov 18:** the results freeze. **Nov 20:** Gate 3's final statement, Track B's and
  Track C's report bullets, the slides.
- **Nov 22:** the report draft. **Nov 23:** the rehearsal. **Nov 24:** the final presentation and report.

**Only Ritik or a teammate can do these.** Sending messages and bundles; approving any rule or amendment; labeling L6;
any Sol change on Ritik's account beyond reading and a safe pull; every Sol command on Arsha's account; Arsha's and
Shrey's own track work.
