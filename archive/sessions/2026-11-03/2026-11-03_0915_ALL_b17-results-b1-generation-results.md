# Session log: B17's deviation, then B17 and B1 read by their rules; A18 queued; Arsha's bundle (Nov 3, 08:57–09:40 MST)

By: Ritik. Ritik's message of about 08:55 gave Sol's results for Nov 2–3 and six items:
1. record B17's deviation first (its pre-registration and DEVIATIONS), committed before any B17 result is read;
2. B17: the smoke check, then the main run by its rule, in plain words;
3. B1: all 630 `-v2` runs by its rule, with the old-vs-new engine check; A38's lines if it reads "works", else A38
   dropped as pre-registered;
4. A18: the primary (Step 10 and the swap) once the three Step 10 reruns are back, Step 9's secondary once 378041
   is; the copy-back lines;
5. what each verdict changes in the story and the README;
6. the standing rules: session log, TODO, STATUS and the Gantt, the daily, then the push with the usual checks.

Also due this morning (TODO H2): Arsha's bundle, rebuilt and verified, and the file named.

**Sol, as Ritik reported it:**
- **B1:** all parts done. Part 9 (334078) COMPLETED 3:21, part 10 (334081) 4:52, part 8's last run (355747) 0:37;
  parts 1–7 earlier. Ritik held 334078 so B17's smoke started first. All `-v2` files are on the Mac.
- **A18:**
  - COMPLETED: Step 3 base (334084) and LoRA (334085), the swap (334114), Step 9 base (334115).
  - The three Step 10 jobs stopped cleanly at their limits: base/base 15 of 22 cuts (334111), base/LoRA 16 of 22
    (334112), LoRA/LoRA 8 of 12 (334113).
  - Resubmitted at estimates 1.8, 1.6 and 1.3 (378051, 378052, 378053), and Step 9 LoRA (378041). All four pending
    (Priority).
- **B17:**
  - The smoke 355632 was submitted Nov 2 17:56:16, started Nov 3 00:50:17 and ended 01:24:53 (34:36), COMPLETED.
  - The main job 355650 COMPLETED, 1:57.
- **The paste's "smoke check output" section was empty.** I ran the check myself after the deviation commit (§3).

## 1. B17's deviation, recorded first

**Ritik's decision, made before anyone read a B17 result: keep B17.**
- **The facts:**
  - the clock started with the first smoke (Nov 1, about 15:57);
  - the fixed smoke was submitted Nov 2 17:56, about 2 h after the one-day mark;
  - it waited in Sol's queue and ran Nov 3 from 00:50 to 01:24.
- **The reasons (Ritik's):**
  - the rule was a time-box against a broken setup, not a rule about results;
  - the fix (§12) corrected the validity check, not the runs;
  - no B17 outcome was seen before the decision.

**What I wrote:**
- **Pre-registration §13** (`archive/sessions/2026-10-31/2026-10-31_2237_B_b17-prereg.md`): the facts, the decision,
  the reasons, what had been seen when it was written, what changes, and the cost if wrong.
- **A DEVIATIONS row** in `make_supplement.py`'s curated list, checked against §13's wording.
- **TODO's B17 row, STATUS and the Gantt.**

**Committed before any result was opened:**
- `dc0d445` at 09:00;
- the supplement regenerated from the clean tree, `4570b09` at 09:01: DEVIATIONS shows the row, checked "yes";
  32 ledger rows, none unverified; no reported number changed.

**What had been seen before the commit:**
- Slurm's states and times, from Ritik's message.
- The rerun's `template_check.json`, which the editor showed me as changed on disk: `ok`, 12 of 15 identical,
  `system` whitespace only at each effort, as §12 expected. It is the served-template check, made before any run,
  not an outcome.
- No run file and no `smoke_check.json` had been opened. §13 says so.

**Added by me in §13, within Ritik's decision:**
- The smoke must still be clean by §4's and §11's five checks; if it isn't, B17 is dropped as before.
- Every B17 number is labelled "run after its one-day window (pre-registration §13)".

## 2. B17: the smoke check

`progress/run_b17.py --smoke-check` exits 0, and its output equals the `smoke_check.json` Sol wrote. **Clean on all
five checks:**
- all 15 ran, status ok;
- 15 of 15 answered;
- 0 unparsed, 0 cut off;
- the tool path ran: 1 of the 3 tool_real runs called the tool and answered;
- the output grows with effort: median output tokens 494 (low), 1,453 (medium) and 7,071 (high).

**The main run:** 2,430 runs, all ok. The runs file has 2,431 lines because one high-effort tool_real run failed
once (`not_run`) and succeeded on its retry. The flags file has 2,430, one per run.

## 3. B17: the main run by its rule, in plain words

**The rule** (§5): high minus low effort, paired by question, 95% bootstrap clustered by question, on two outcomes:
1. following on the real tool call (tool_real runs that answered, called or not);
2. the bare final answer after a call (30 characters or fewer, among tool_real runs that called and answered).

Each reads "rises" (the interval above 0), "falls" (below 0) or "no change detected" (it includes 0).

**The result: no change detected on both.**

| | low | medium | high | high − low |
|---|---|---|---|---|
| following on the real call | 40 of 162 | 46 of 162 | 48 of 158 | +7 [−0.6, +15.6] |
| bare final answer after a call | 37 of 37 | 75 of 78 | 122 of 129 | −4.7 [−10.3, 0.0] |

- **At the 16,000 cut:** +8.5 [−0.15, +17.5] and −5.3 [−11.3, 0.0]. Both readings are the same.
- **Secondary** (medium − low, high − medium): no change detected on all four.

**In plain words:**
- **More thinking doesn't change either outcome.** Giving gpt-oss-20b more thinking took its median reply from about
  400 to 6,700 tokens. That didn't change how often it ends on the tool's wrong letter. Nor did it change whether its
  final answer after a call is a bare letter.
- **How far that holds:**
  - Following: a rise of more than 16 points, or a fall of more than 1, is ruled out.
  - The bare answer: it was already 37 of 37 at low effort, so only a fall could have shown. A fall of more than 10
    points is ruled out.
- **Following's lower bound is close to 0** (−0.6, and −0.15 at the 16,000 cut). A small rise isn't excluded; the
  rule reads "no change detected".

**Beside it, no decision:**
- **More calls, not more following.** At high effort the model calls the tool in 129 of 162 runs, against 37 at low.
  The share ending on the wrong letter barely moves, because it follows less once it has called (31 of 37 at low,
  47 of 129 at high). The called runs are different questions at each effort, so that comparison isn't like for like.
- **Unlike Qwen3-8B,** where thinking on raised the calls and the following with them (F29).
- **Gate 2 is clear at every effort:** pasted − user +24 to +26; the real call − user +14, +25, +26.
- **The bare letter after a call** holds at every effort (95% to 100%). gpt-oss's answers are often bare with no hint
  too (79% to 81%).
- **No-hint accuracy rises with effort:** 111 of 160, 137 of 161, 140 of 153.
- **No answer at the 32,768 budget:** 4, 2 and 37 runs.

Written as **F37**. Source: `results/summaries/trackB/b17_report.json` and `b17_smoke_check.json`, both newly
exported.

## 4. B1: all 630 runs by its rule, in plain words

**The counts:** 30 files (10 parts × 3 configurations), 21 runs each, all `"status": "ok"`. No answer in 2, 9 and 6
runs (alpha = 1, deployable, oracle).

**The rule** (Oct 30 17:15 log, §2), as encoded in `b1_verdict` on Oct 31 before any result. I ran the function on
the report rather than reading the thresholds by hand. Each span minus alpha = 1, paired by question:
- **works:** following's interval is below 0, *and* correct-hint acceptance falls ≤ 5 points, *and* no-hint
  accuracy moves ≤ 5 points;
- **ignores tools:** following falls, but acceptance falls by more than 5;
- **costs accuracy:** following falls and acceptance holds, but accuracy moves more than 5;
- **no effect:** following's interval includes 0;
- **worse:** following's interval lies above 0.

The deployable span is read on the inserted tool turn; the oracle span on every hint channel.

| span | following | acceptance | no-hint accuracy | reading |
|---|---|---|---|---|
| deployable (0.25), the inserted turn | 26 → 16 of 60, **−16.7 [−30.0, −3.3]** | 25 → 23 of 30, −6.7 | 16 → 19 of 30, +10.0 | **ignores tools** |
| oracle (0.5), every hint channel | 61 → 50 of 120, **−9.2 [−19.2, +0.8]** | 54 → 50 of 60, −6.7 | +10.0 | **no effect** |

**In plain words:**
- **The deployable span's effect on following is real.** Scaling down layers 15, 19 and 23's attention to the inserted
  tool turn cuts how often the model takes that turn's wrong letter: from 43% to 27% of runs, and the interval
  excludes 0.
- **But it fails the rule on correct hints.** It also took a correct tool hint less often: 23 of 30 against 25, a fall
  of 7 points where the rule allowed 5. So the rule says "ignores tools".
- **Scaling every hint span shows no effect.** It cut following by 9 points, but the interval reaches +1.

**The rule's 5-point limits are inside the noise here:**
- The deciding acceptance fall is 2 runs of 30, and its interval (−20 to +7) includes 0.
- No-hint accuracy moved +10 under both spans, yet a no-hint prompt has no tool turn and no pasted block. The scaling
  marks no key there (`provenance.mark_for`: the tool turns, plus the pasted block for the oracle).
- So the +10 is sampling between jobs:
  - alpha = 1 and the deployable span give the same letter in 18 of 30 no-hint runs;
  - the two spans' no-hint runs are separate samples (the same length and letter in 1 of 30), and both are 19 of 30.
- By the rule's point estimates, the readings stand; F38 states this limit.

**A38 is dropped as pre-registered.** It runs only if the deployable span reads "works", and that is robust to how
acceptance is read:
- "works" also needs no-hint accuracy within 5 points, and it moved +10;
- the pooled acceptance (54 → 51 of 60, −5.0) would turn "ignores tools" into "costs accuracy", not "works".

**The engine check** (robustness, not the rule; first engine minus fixed, at alpha = 1, paired by question):
- following −2.9 [−10.8, +4.8] (26 questions);
- acceptance +2.0 [0.0, +6.0] (25);
- no-hint accuracy +12.0 [−4.0, +28.0] (25).

No difference was detected on any, as expected, though the no-hint interval is wide. The first engine's 17
deployable runs are set aside (counts only).

**Per channel, no decision:**
- the deployable span on the pasted block, which it doesn't touch: +5 [−10, +18];
- the oracle span on the inserted turn −15 [−28, −2], and on the pasted block −3 [−18, +13].

**Not in the report:** B1 beside prompt_only and LoRA (cross-stack, pre-registered with no decision). This is open,
and minor.

Written as **F38**. Source: `results/summaries/trackA/gpu/provenance_gen/provenance_gen_report.json`, newly exported.

## 5. A18: nothing read yet; the copy-back lines

Ritik's order: the primary (the swap) and Step 10 once all three Step 10 reruns are back; Step 9's secondary once
378041 is. The swap and Step 3 are complete on Sol, and Ritik's earlier copy-back brought their consoles and folders
to the Mac. I haven't opened any of them, and `a18.py readout` hasn't run.

```bash
# on Sol: wait until all four have ended
sacct -j 378041,378051,378052,378053 --format=JobID,State,ExitCode,Elapsed

# on the Mac, from cot-disclosure/ (numbers only; the sources stay on Sol); the same line again after 378041
H=ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68
rsync -av --exclude 'sources_*' $H/trackA/a18/ results/trackA/gpu/a18/
# every Step 10 folder complete: its cut count against the "N cuts at (ii)" line its job printed
for d in results/trackA/gpu/a18/step10_*; do printf '%3s cuts  %s\n' "$(ls $d/cuts | wc -l | tr -d ' ')" "${d##*/}"; done
grep -h "cuts at (ii)" results/trackA/gpu/a18/console_*.log | sort -u
ls results/trackA/gpu/a18/step9_*/step9/                    # step9_base and, after 378041, step9_lora
```

**Then the reading:** `../.venv/bin/python finetune/look/a18.py readout results/trackA/gpu/a18`, in its own log.
- The rule is §4 of the 22:44 log, as amended in §8: tool-hint cases only.
- `readout` reads whatever files exist, so it waits until the counts above are complete.
- **If a Step 10 job stops again** at its limit, its saved cuts count; resubmit the same line.

## 6. What each verdict changes in the story and the README

| verdict | the story (FINDINGS) | the README |
|---|---|---|
| **B17, no change detected (F37)** | Line 5 (the title question) gains a pre-registered second model: more thinking changes neither, with "more calls, not more following" as descriptive. Line 2 gains gpt-oss's bare letter at every effort, with its high no-hint baseline. Line 1: Gate 2 clear in a fifth model (reported, no decision). Each is labelled "run after its one-day window". | Line 2: "More thinking doesn't change it", B17. Line 1: "all five models tested". |
| **B1, "ignores tools" and "no effect" (F38)** | Line 6 (the fix): B1 doesn't pass its rule; the deployable span cuts following but costs correct tools beyond the limit; the oracle shows no effect; A38 isn't run; the limits sit inside the noise. | Line 5: B1's reading and A38 not run; "under way" now names A18 only. |
| **A38 dropped** | in line 6 | in line 5 |
| **A18 (not read)** | unchanged | "the trained model's mechanism (A18) is under way" |

Also updated:
- **CLAIMS:**
  - 1.1: gpt-oss's Gate 2 at three efforts; "five models".
  - 1.7: B1's generation; *not supported as worded*; *tentative* on the cost. The `[SOL: ___]` placeholder is
    removed.
  - The Track B supporting section: F37.
- **F27's status:** now points to F38.
- **TRACK_B:** B17 done, its plan row, the model table and the status table.
- **TRACK_A_FIX:** B1's result.
- **PLAN:** the Track B line; A30, A38 and B17's rows; slides 8 and 10.
- **WAITING.md:** slide 8 can be drawn, labelled §13; B1's exported source.
- **The supplement's ledger:**
  - B1's verdict, now matched to F38's title (its old pattern, `B1.*generation`, matched no heading);
  - B17's verdict, with §13's commit as a fixing commit;
  - A38: not run, as pre-registered.

## 7. Arsha's bundle (TODO H2, due this morning)

- **The file:** `cot-disclosure/results/handoff/trackB_20261103.tar.gz`
  - 33 files, 62.5 MB raw, 49.8 MB packed;
  - its manifest is beside it;
  - `--verify`: "bundle matches its manifest";
  - no GPQA.
- **Holds:** Track B's runs and reports; B15, B16 and B19 (runs, the text `.gz` and reports); B17's runs, flags,
  report, smoke check and both template checks; A37's Qwen3-8B files (`qwen8b_mech/`); the canary.
- **The note** (the Nov 1 daily) now has:
  - the bundle line (`trackB_20261103.tar.gz`, 50 MB);
  - Gate 2 on all five models;
  - a B17 line: it ran after its one-day window, Ritik kept it before anyone read a result, and it changed neither
    reading; her part is to re-read B16, B19 and B17, then B18.

## 8. Judgment calls, each with its cost if wrong

1. **The B1 rule as encoded.** I read the deployable span's acceptance on the inserted turn (−6.7), as the 17:15 log
   says, not pooled (−5.0).
   - Cost if wrong: none for A38. The pooled reading gives "costs accuracy", which isn't "works" either.
2. **The oracle span read pooled over every hint channel** (`b1_verdict`'s "all").
   - Cost if wrong: if each channel were read alone, the inserted turn reads "ignores tools" and the pasted block
     "no effect". Neither is "works".
3. **The no-hint +10 named as sampling** in F38 and CLAIMS 1.7, from the code and two record comparisons. The
   readings still follow the rule's point estimates.
   - Cost if wrong: a reader may take it as excusing the verdict. F38 states the verdict first.
4. **Two files kept out of the summaries:**
   - **B1's trade-off figure:** it pools both channels (so the deployable point isn't the pre-registered reading)
     and starts its y-axis at 0.83;
   - **B17's `template_check.json`:** it holds question text.

   Only numbers-only reports were exported. Cost if wrong: a figure to redraw later.
5. **Gate 2 for gpt-oss** goes in story line 1 and README line 1 ("all five models"), though B17 reports it with no
   decision.
   - Cost if wrong: a claim stronger than its design. F37 and the story say "reported with no decision". Each
     effort's interval is well above 0.
6. **A18 left unread** until all three Step 10 reruns are back, as Ritik asked, though the swap is complete.
   - Cost: none.

## 9. Checks and the push

In §4 of the Nov 3 daily: the suite (733 passed), links (0 broken), the supplement (32 rows, none unverified;
regenerated after this commit), export numbers-only, the Gantt, the pre-push check and the commit metadata.

## 10. What's waiting for Ritik

- **Send Arsha** `cot-disclosure/results/handoff/trackB_20261103.tar.gz` with the note in
  `archive/sessions/2026-11-01/DAILY_2026-11-01.md` (§4's end).
- **A18:** when 378051, 378052 and 378053 end, run §5's copy-back and tell me; I read the primary and Step 10. The
  same line again after 378041, for Step 9's secondary.
- **D12** (the old doc paths in three files) still waits: the queued A18 jobs load `finetune/` and
  `progress/common.py`. It is due Nov 4.
- **Slide 8** (B17) can be drawn (D14; Arsha's slide, or mine if you say so).
