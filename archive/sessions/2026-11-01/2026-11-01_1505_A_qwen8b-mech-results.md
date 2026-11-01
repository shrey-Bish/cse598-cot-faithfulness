# Session log: A37 read by its rule: Qwen3-8B's readout replicates (Nov 1, 15:00–15:30 MST)

By: Ritik. Ritik's message of about 15:00: the six Qwen3-8B files are in `results/trackB/qwen8b_mech/`; read A37 by
its pre-registered rule, recomputing the verdict from `qwen8b_step10_patching.json` first, in its own session log.
The rule: [the Oct 30 11:45 log](../2026-10-30/2026-10-30_1145_A_qwen8b-mech-prereg.md), §4–5, with Ritik's choices
fixed in `fd1a679` (Oct 30, about 17:10) before anything was submitted.

## 1. The result: replicates

**The rule:**
- **Localization:** the 3 layers with the largest mean drop in hint-token restoration on the 24 pilot puzzles
  (`tool_real`, cut (ii), the takeover).
- **Replicates on MMLU-Pro** if two things hold:
  - the share of the drop at those layers has a 95% lower bound above 0.5 (bootstrap clustered by question);
  - each layer is within one layer of one of MMLU-Pro's 3 largest drops.
- **Partly:** one of the two. **Doesn't replicate:** neither. **Too few:** under 5 questions.

| half | channel | cuts at (ii) (questions) | layers | share of the drop at 21, 22, 29 | 3 largest drops there | reading |
|---|---|---|---|---|---|---|
| puzzles (localization) | `tool_real` | 63 (23) | **21, 22, 29** chosen | 0.74 [0.69, 0.79] | 21, 22, 29 | chosen |
| MMLU-Pro (replication) | `tool_real` | 30 (14) | the puzzles' | **0.70 [0.60, 0.83]** | **21, 22, 29** | **replicates** |

- **Both conditions hold:**
  - the lower bound, 0.60, is above 0.5;
  - each chosen layer is one of MMLU-Pro's own top 3 (within one layer by the rule; here exactly the same three).
- **Against Olmo 3 7B Think's readout** at 15, 19 and 23: 0.90 [0.85, 0.96] on Test 2 (F11), 0.90 [0.76, 1.06] on
  set A (F26). Qwen3-8B's three layers hold less, about 0.70–0.74.

## 2. Descriptive (pre-registered as never in the verdict)

- **The drop by layer at cut (ii)** (each half's mean drops sum to 1):

| layer | 21 | 22 | 29 | 26 | 24 | next |
|---|---|---|---|---|---|---|
| puzzles | **0.30** [0.27, 0.34] | **0.21** [0.18, 0.24] | **0.23** [0.21, 0.25] | 0.19 | 0.12 | 32: 0.07 |
| MMLU-Pro | **0.17** | **0.20** | **0.33** | 0.15 | 0.15 | 34: 0.09 |

  - Four layers hold 80% of the drop in each half (the three plus 26).
  - Some layers give some back (25: −0.10 and −0.14).
- **Above the even share** (3 of 36 layers, 0.083): yes, by far.
- **Cut (i), before the first mention, MMLU-Pro:** 0.37 [0.31, 0.43] at 21, 22, 29.
- **The answer position's rise at the same layers:** 0.45 [0.42, 0.48] (puzzles), 0.43 [0.40, 0.46] (MMLU-Pro).
  Olmo: 0.62 (Test 2), 0.57 (set A).
- **Swapping only the prompt's letter at cut (ii)** (the reasoning still names W) moves the answer off W:
  - **puzzles:** 54 of 63 [75, 92%], all to O;
  - **MMLU-Pro:** 30 of 30 [89, 100%], all to O;
  - **Olmo:** 13 of 21 (Test 2) and 12 of 34 (set A).
  - So in Qwen3-8B the prompt's letter, not the reasoning's repetition of it, carries the answer at the takeover in
    almost every case.
- **The secondary channels** (MMLU-Pro, the same numbers, no verdict drawn):

| channel | cuts (questions) | share at 21, 22, 29 | 3 largest drops there | the rule's words, if applied |
|---|---|---|---|---|
| `tool_pasted` (the block in the user's message) | 15 (8) | 0.60 [0.48, 0.73] | 21, 24, 29 | partly |
| `system` (the hint in the system prompt) | 12 (8) | 0.17 [0.08, 0.28] | 13, 24, 29 | doesn't replicate |
| `user` | 3 (3) | — | — | too few |

  The system-prompt hint leaves its tokens elsewhere (layer 13 holds 0.40). With 8 questions this is a pointer,
  not a finding.

## 3. Step 3: the cases (`qwen8b_step3.json`)

| half, channel | followed runs probed | on sure questions | takeover on sure questions | cases (questions) |
|---|---|---|---|---|
| puzzles, `tool_real` | 66 | 63 | all 63 late | **63 (23)** |
| MMLU-Pro, `tool_real` | 77 | 50 | 30 late, 15 at k = 0, 5 other | **30 (14)** |
| MMLU-Pro, `tool_pasted` | 46 | 22 | 15 late, 4 at 0, 3 other | 15 (8) |
| MMLU-Pro, `system` | 44 | 19 | 12 late, 3 at 0, 4 other | 12 (8) |
| MMLU-Pro, `user` | 16 | 3 | 3 late | 3 (3) |

(Puzzles, pasted and system: 1 run each, followed; outside the rule.)

- **"Sure":** all 3 no-hint runs answered and correct (23 of 24 puzzles, 21 of 30 MMLU-Pro).
- **"At k = 0":** the forced answer is already W before the first sentence. Those runs aren't cases.
- **Not needed:** the fallback for under 5 usable puzzle questions (fresh puzzles).

## 4. Checks

- **Recomputed on the Mac** from the summary alone (`qwen8b_mech.py readout
  results/trackB/qwen8b_mech/qwen8b_step10_patching.json`):
  - the same verdicts, layers and counts;
  - every number equal to Sol's `qwen8b_readout.json` within 2.2e-16 (floating-point rounding).
- **The code the rule names:**
  - **Commit:** both jobs ran at `4222ff6` with a clean `finetune/`, and `4222ff6` contains the rule's commit
    `fd1a679`.
  - **Unchanged since:** `qwen8b_mech.py`, `patching.py`, `takeover.py` and `gpu/kit.py` are the same from
    `4222ff6` to now.
  - **The same in both jobs:** the snapshot `b968826d` (pinned), the chat template's sha256 `a55ee1b1…` and the
    records' sha256 `21b3e772…`.
- **Step 3** (job 123022, sg033, ended Oct 31 19:17 MST):
  - every rebuilt prompt matched the server's token count (none left out);
  - the rebuilt reasoning matched the server's output tokens in 250 runs, off by one in 1;
  - the forced answer at the end equals the run's final answer: 66/66, 77/77, 45/46, 44/44, 16/16;
  - cached against fresh probes: 502 of 502 had the same top letter (largest probability difference 0.12, 12 over
    0.05, bf16).
- **Step 10** (job 123025, sg037, ended Nov 1 04:18 MST):
  - 243 of 243 cuts pass the patching sanity checks;
  - none was left out by the 0.5 logit-difference gap (set A left out 3 of 34, Test 2 2 of 21).
- **Nothing chosen on the 30:** the localization code refuses any question that isn't a pilot puzzle, and it ran.
  MMLU-Pro (Track A's 30 evaluation questions) was read only by this rule.

## 5. What it says, and its limits

- **The readout isn't forced by Olmo's sliding windows.** Every one of Qwen3-8B's 36 layers sees the whole prompt.
  Still, three layers chosen on the puzzles hold most of the drop at the takeover on questions not used to choose
  them, and they're the new questions' own top three. The story's line 3 now rests on two models.
- **Less concentrated than in Olmo:** 0.70 against 0.90, and a fourth layer (26) adds 0.15–0.19 in both halves.
- **The tool's own call only.** The verdict reads `tool_real`. The pasted block shows the same layers more weakly,
  and the system-prompt hint shows other layers (descriptive, 8 questions each).
- **One replication, 14 questions, 30 cuts.** Late takeovers only: on MMLU-Pro, 15 of the 50 followed runs on sure
  questions already favor W at k = 0 and aren't tested.
- **Patching only.** No Step 9 (attention heads) on Qwen3-8B, so nothing here speaks to F12's heads.
- **The rule's own caveat:** chosen on puzzles, tested on MMLU-Pro, so a replication is the stronger evidence. It
  stands.

## 6. What changed

- **FINDINGS:**
  - **F36,** the result above.
  - **The story's line 3:** two models.
  - **The header.**
- **The level-1 claim and its reviewer question:**
  - **README's line 3:** the level-1 claim now names two models.
  - **CLAIMS 1.4:** its "one model" objection is answered.
  - **REVIEWER_QUESTIONS, thread 1 question 2:** answered for the second model.
- **Plans and status:**
  - **PLAN:** level 1's known and open, the map row, slide 4.
  - **TODO A37:** done.
  - **The supplement's ledger:** A37's verdict, regenerated.
- **Summaries and the slide:**
  - **The summaries:** `export_summaries.py` copies the three numbers-only summaries (readout, Step 10, Step 3) to
    `results/summaries/trackA/qwen8b_mech/`.
  - **Slide 4:** drawn to its spec in `WAITING.md` (`docs/paper/figures/readout_qwen8b.png`, .svg, .csv).

## 7. The rest of Ritik's message

- **Shrey's packet:** Ritik left out `hint_labeler.html` and `check_sheet.py` (Ritik's own aids). The packet stays as
  built at 12:27, with nothing rebuilt; the files are unchanged since. TODO L3 and the Nov 2 daily say so.
- **A18 "tool-only":** confirmed as §8's amendment (the tool-hint cases decide; the user-hint cases are reported
  apart). The Nov 2 daily's lines stand.
- **B19:** read when it finishes, then the second push (this commit goes with it).
- **Not committed here:** `voyager_canary.jsonl`'s export picked up B19's 15 canary rows, so the tracked file was
  restored. It's exported with B19's reading.
