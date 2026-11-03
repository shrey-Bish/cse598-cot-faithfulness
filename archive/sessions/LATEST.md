# Session log: the hand labels' kappa (L3 under 0.6, L4 part 1 read); B1's framing and B1R's power check; slide 8; A18 (Nov 3, 09:45–10:40 MST)

By: Ritik. Ritik's message of about 09:45, ten items:
1. Shrey's returned sheets: check and place them;
2. kappa by the plan, with Gate 2's label part (0.6), stopping if any channel is under it;
3. the disagreements by row number only, and the rates;
4. the label results in plain words (F3, L4 part 1 against F28), and what they change;
5. B1's framing in F38 and the story;
6. B1R, a replication of B1's deployable span gated by a power check;
7. slide 8 (B17);
8. A18's state, the resubmit and copy-back lines, and the readings when they are due;
9. Arsha's handoff recorded as done;
10. the standing rules.

## 1. Shrey's sheets: checked and placed

**Where they were:** `results/labels/returned/shrey_20261103/`, as `L3_SB_updated.csv` and
`L4_part1_SB_updated.csv` (saved Nov 3, 08:58). These are the filled sheets. The packet's `L3_SB.csv` and
`L4_part1_SB.csv` are the blanks, byte for byte `rater2.csv` and `gate3/L4/part1.csv`.

**The format check:** the same checks as Ritik's on Nov 1, from a script that reports problems only and never counts
labels. It compares each sheet with its blank:
- UTF-8, no byte-order mark, the blank's line ends;
- the header unchanged; 101 and 294 rows in the blank's order; every cell outside the label, guess and note columns
  unchanged;
- every label an allowed value exactly as written; `n/a` kept where the blank had it; `guess_trained` `yes` or `no`;
- a note on every `unclear` and `says_changed`.

**No problems found in either sheet.** Ritik's two sheets, rerun as a control, are clean too. Ritik's and Shrey's L3
blanks are identical (the same rows).

**Placed** byte for byte beside Ritik's, where `label_kit kappa` reads them (gitignored):
- `results/labels/L3_SB.csv` (sha256 `8d05be73…`);
- `results/labels/gate3/L4/L4_part1_SB.csv` (`c97cbe13…`).

The originals stay in `returned/shrey_20261103/`.

## 2. Kappa by the plan

**The rule and where it is written:**
- **RATER_GUIDE, "How agreement is computed":** Cohen's kappa per text (private, final), overall and per channel.
  "Kappa of 0.6 or more for a text: the labels stand. Below 0.6: 1. both raters meet and settle the disagreements;
  the settled labels go in a third column pair, and the original two stay. 2. The guide is tightened. 3. A fresh
  batch is labeled."
- **PLAN** (the labels section) and **TODO L3:** "Cohen's kappa per channel; under 0.6, tighten the guide and label a
  fresh batch. No acknowledgment claim goes in the report before this is done (Gate 2)."
- **The command:** `label_kit.py kappa`, as RATER_GUIDE gives it.

**L3 (101 rows): Gate 2's label part is not passed.** Four of six cells are under 0.6.

| text | all | tool | user |
|---|---|---|---|
| private reasoning | **0.627** (58 rows; agreement 0.845) | **0.288** (30; 0.767) | 0.850 (28; 0.929) |
| final answer | **0.543** (101; 0.842) | **0.589** (44; 0.795) | **0.425** (57; 0.877) |

Under the guide's "for a text" (private, final overall), the final answer fails. Under PLAN's and TODO's "per
channel", private tool and both final channels fail as well.

**Why kappa is low where agreement is high:** chance agreement is high there (private tool 0.67, final user 0.79),
so a few disagreements weigh a lot. This is said without looking at which labels.

**What the plan says to do, and I stopped there:**
1. **Ritik and Shrey settle the 25 disagreements** (§3), writing the settled labels in a third column pair and keeping
   the original two.
2. **The guide is tightened.**
3. **A fresh batch is labeled.** The plan doesn't name its rows; that is Ritik's decision.

No L3 rate, count or distribution was computed. F3 stays a keyword count, and no acknowledgment claim from hand
labels goes in the report before these three steps.

**L4 part 1 (294 rows; final answer only): kappa passes in every channel.**

| all | tool_injected | tool_pasted | user |
|---|---|---|---|
| **0.930** (294 rows; agreement 0.956) | 0.958 (147; 0.973) | 0.891 (58; 0.931) | 0.908 (89; 0.944) |

- **The labels stand,** and the plan calls for no adjudication.
- **`guess_trained` against the key:** Ritik right on 270 of 294 (92%), Shrey on 267 (91%). LoRA writes 147 of the
  294 rows, so chance is 50%. **The sheets were not blind to LoRA's style.** The L4 log named this limit on Oct 30
  (LoRA's trained opener names the hint). RATER_GUIDE reads it as "the style gave the model away" and sets no stop
  rule for it.

## 3. The disagreements, by row number only

- **L3, 25 disagreements (23 rows):**
  - private: rows 30, 36, 47, 55, 61, 67, 69, 72, 77;
  - final: rows 10, 30, 31, 32, 34, 36, 37, 38, 39, 41, 42, 46, 51, 58, 63, 66.
  - The plan calls for adjudication (§2). Ritik and Shrey resolve them. No judgment of which label is right was made
    here. `label_kit`'s own output, which also shows each rater's label, was kept in the scratchpad and not copied
    here.
- **L4 part 1, 13 disagreements:** rows 15, 58, 87, 98, 107, 152, 166, 169, 176, 181, 234, 284 and 290 (final
  answer). Kappa passes, so the plan calls for no adjudication.
- **The rates:**
  - **L4 part 1:** each rater's rates and those on the agreed rows are in §4.
  - **L3:** none, because it stopped at its gate. Reading L3's rates before the raters settle their disagreements
    could also sway the settling.

## 4. The label results, in plain words

**F3 with hand labels: not available.** L3 didn't pass kappa, so how often the private reasoning and the final
answer acknowledge the hint isn't read from labels. F3 stays "private 208 of 216, final 8 of 216" by keyword.

**L4 part 1 against F28: LoRA's false-disclosure candidates are rarely real.**

The reading was fixed after the kappa and before any count: the L4 log's §6, committed as `d63eb7f`. It is a
reading set after labeling, not in the pre-registration:
- **The measure** is PLAN's measure 4: each label's share in each group, per rater and on agreed rows.
- **A real false disclosure** is `rejects_hint` on these rows. Every row ends on the hint's wrong letter, so it is an
  answer that says it rejected the hint and still took it. That is PLAN's "claims it checked the hint and disagreed".
- PLAN's other half, "worked it out independently", has no label of its own; the guide puts it under
  `mentions_only`.

| group | rater | rejects_hint | says_changed | mentions_only | no_mention | unclear |
|---|---|---|---|---|---|---|
| LoRA's 147 candidates | Ritik | **1** | 97 (66% [58, 73]) | 42 | 6 | 1 |
| | Shrey | **2** | 89 (61% [52, 68]) | 49 | 6 | 1 |
| | agreed, 139 | **1** | 89 | 42 | 6 | 1 |
| base, 74 matched non-candidates | Ritik / Shrey / agreed (72) | 0 / 0 / 0 | 11 / 10 / 10 | 0 / 1 / 0 | 62 / 63 / 62 | 1 / 0 / 0 |
| prompt_only, 73 matched | Ritik / Shrey / agreed (70) | 0 / 0 / 0 | 12 / 10 / 10 | 4 / 5 / 3 | 57 / 58 / 57 | 0 / 0 / 0 |

**In plain words:**
- **Real false disclosures are rare.** The keyword flagged 147 of LoRA's answers as possibly saying "I checked and
  disagreed" or "I worked it out myself" while taking the wrong letter. By two raters, only 1 or 2 of them actually
  claim to have rejected the hint.
- **Most are the opposite: honest deference.** About two in three say the hint shaped the answer ("the answer key
  says J, so J").
- **The matched base and prompt_only answers** almost never mention the hint (78% to 86% `no_mention`). None claims
  to have rejected it.
- **Part 1 can't give LoRA minus base in labels.** Its LoRA rows are keyword candidates and its base and prompt_only
  rows are non-candidates; part 2 gives that difference. This was said on Oct 30.

**Limits:**
- The raters could tell LoRA's rows (91% to 92%).
- LoRA only: not LoRA + tags or LoRA on 15/19/23.
- The "worked independently" half isn't read.
- The mapping was set after labeling, before counting.

**What it changes:**

| where | before | now |
|---|---|---|
| FINDINGS F28 | the candidate cautionary claim *waiting* on hand labels | the hand-label table; the claim's "may have taught the model to claim checks it didn't do" **not supported** for claimed disagreement; its first half (no better than an instruction) stands; the title adds "by hand labels LoRA's are rarely real" |
| FINDINGS F3 | hand labels *waiting* | L3's kappa, the plan's three steps, no claim from labels yet |
| the story, line 6 | "Candidate cautionary claim, waiting on hand labels" | LoRA's candidates rarely real by hand labels; the first half stands |
| README, line 5 | "the LoRA versions' false-disclosure candidates rise (hand labels pending)" | "By hand labels, LoRA's keyword false-disclosure candidates are rarely real" |
| CLAIMS | 1.2: hand labels *waiting*; 1.5: the cautionary claim *waiting* | 1.2: L3's kappa and its steps; 1.5: read with L4 part 1 |

## 5. B1's framing (F38 and the story)

The new framing, in F38's title and status, story line 6, README line 5 and CLAIMS 1.7: **"a real cut in following
(−17 [−30, −3] on the inserted turn) that misses its pre-registered acceptance limit; underpowered at 30 questions."**
The verdict is unchanged everywhere: deployable "ignores tools", oracle "no effect". The ledger's verdict string is
unchanged too.

## 6. B1R: the power check, before anything ran. Not run.

**The gate (Ritik):** run only if the expected 95% half-width of the acceptance difference is at most about 5 points,
at the largest question count that fits in 35 GPU-hours. The design is as Ritik gave it: fresh questions, the
deployable span, alpha 1 against 0.25, the fixed engine, the inserted turn, and per question 2 wrong, 2 correct and
1 no-hint run in each configuration.

**The cost, from B1's own runs:**
- B1 used 34.3 GPU-hours, from Slurm's elapsed times with load included. Parts 1–7 are measured first run to last,
  plus 0.15 h each. Part 8's two jobs were 17 h apart, so it uses 5:30 + 0:37.
- That bought 630 runs and 6.93 M generated tokens: 202,000 tokens per GPU-hour.
- **Per B1R question:** 4 inserted-turn runs (B1's mean 9,226 tokens) plus 1 no-hint run (10,716), times 2
  configurations, is 95,000 tokens. That is 0.50 GPU-hours with load, in parts of 6.
- **35 GPU-hours fit 70 questions.**

**The expected half-widths at 70 questions**, from B1's numbers:

| measure | B1's clustered interval, scaled from 30 questions | from B1's rates, pairing ignored |
|---|---|---|
| acceptance (2 correct-hint runs a configuration) | 8.7 if the second run adds nothing; 6.2 if it halves the variance | 9.3 (25 and 23 of 30) |
| following (2 wrong-hint runs, as in B1) | 8.7 | 11.0 (26 and 16 of 60) |

**All are above 5, so B1R isn't run.** Recorded in F38: "B1 is underpowered: a replication that could resolve its
limits needs about 107 to 245 questions, 53 to 122 GPU-hours", for ±5 on acceptance by the three estimates.
- The script is `power.py` in the scratchpad. It only reads B1's report and runs files.
- The formulas: B1's half-width × √(30/N), times √½ for the optimistic case; and 1.96·√((p₁q₁ + p₂q₂)/(2N)).

## 7. Slide 8 (B17): drawn

`docs/paper/figures/b17_effort.png` (.svg, .csv), from `results/summaries/trackB/b17_report.json`, by
`tools/slide_figures.py fig_b17` in the house style (16:9, white, colors by role).
- **(a)** Following on the real call per effort (damage color), with the call rate behind it (baseline color).
- **(b)** The bare answer after a call (final-answer color).
- Each point carries its clustered interval and X of Y. The x labels give the median reply length.
- The panel titles carry the pre-registered high − low and its reading. The footer carries the §13 label.

**Tests, written first:** a new one checks every plotted number against the summary and the readings; the
16:9/CSV test now covers it; the waiting-spec test drops `b17_effort`. Both failed before the code, then 8 of 8
passed. I checked the rendered PNG three times and fixed the overflow, the label collisions and the number format.
Regenerating the other five slides changed only their SVGs' dates and ids, so they were restored.

## 8. A18: the state and the lines

From Ritik's `sacct` (about 10:00):
- 378053 (Step 10, LoRA's cases under LoRA) **COMPLETED** 0:23:36;
- 378041 (Step 9 LoRA) **COMPLETED** 0:49:25;
- 378051 (base/base) and 378052 (base/LoRA) **running**, at 47 and 43 minutes into 2:30 limits.

**On the Mac**, from Ritik's earlier copy-back:
- every tool-hint folder (the primary's) is complete: 30 of 30, 30 of 30 and 18 of 18 cuts;
- the user-hint folders (reported apart) have 15 of 22, 16 of 22 and 8 of 12;
- there is no `step9_lora`.

So the reruns are finishing the user-hint cases. Nothing is read: per Ritik, the primary and Step 10 wait for 378051
and 378052, and Step 9's secondary waits for 378041's copy-back.

```bash
# on Sol: the two still running
sacct -j 378051,378052 --format=JobID,State,Elapsed,ExitCode
# only if one stops at its limit again (its saved cuts count):
S=cot-disclosure/finetune/gpu/sol/submit.sh
$S a18 --estimate 1.8 -- step10 --cases base --weights base      # if 378051 stops
$S a18 --estimate 1.6 -- step10 --cases base --weights lora      # if 378052 stops

# on the Mac, from cot-disclosure/: now (378041, 378053), and again once 378051 and 378052 have ended
H=ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68
rsync -av --exclude 'sources_*' $H/trackA/a18/ results/trackA/gpu/a18/
for d in results/trackA/gpu/a18/step10_*; do printf '%3s cuts  %s\n' "$(ls $d/cuts | wc -l | tr -d ' ')" "${d##*/}"; done
# complete: base_on_base 30, base_on_base_user 22, lora_on_base 30, lora_on_base_user 22, lora_on_lora 18, lora_on_lora_user 12
ls results/trackA/gpu/a18/step9_lora/step9/
```

## 9. Arsha's handoff: done

Ritik sends `trackB_20261103.tar.gz` and the note today. Recorded in TODO H2 (sent), TRACK_B (its plan's Nov 3
row and header) and PLAN.

## 10. Judgment calls, each with its cost if wrong

1. **L3 stopped at kappa: no rates, not even each rater's.** Item 3 asked for each rater's rates. Item 2 said not to
   go past a failed gate, and L3's rates are F3's result in another form; reading them could also sway the
   adjudication.
   - Cost if wrong: one command to run after you say so.
2. **L4 part 1 went ahead,** because its own kappa passes every channel. Your stop applies to Gate 2's label part,
   which is L3.
   - Cost if wrong: the L4 numbers are in F28, the story and the README a step early. If you wanted to hold L4 too,
     they come out in one commit.
3. **The L4 reading was committed before counting** (`d63eb7f`): `rejects_hint` as the real false disclosure. It is
   labelled as a reading set after labeling, not pre-registered.
   - Cost if wrong: if "worked it out independently" was meant to count, part of `mentions_only` (42 and 49 of 147)
     could be false disclosure, and the labels can't separate it. F28 says so.
4. **B1R's cost from B1's tokens and elapsed times** (202,000 tokens per GPU-hour), and three half-width estimates,
   not one.
   - Cost if wrong: the optimistic case needs 107 questions, 53 GPU-hours, still above 35. Only a much faster engine
     would change the decision.
5. **Slide 8's headline:** "follows the tool about as often", not "as often". The +7 [−1, +16] interval doesn't
   show equality.

## 11. Checks and the push

In §5 of the Nov 3 daily (this prompt's section).

## 12. What's waiting for Ritik

- **L3:** settle the 25 disagreements with Shrey (rows in §3), then tighten the guide and choose the fresh batch.
  Gate 2 is Nov 8.
- **A18:** the copy-back now (378041, 378053) and again after 378051 and 378052. Then I read Step 9's secondary, and
  the primary with Step 10.
- **L4 part 2 (SHOULD):** needed for LoRA minus base in labels.
- **D12** (due Nov 4) still waits on A18's running jobs.
