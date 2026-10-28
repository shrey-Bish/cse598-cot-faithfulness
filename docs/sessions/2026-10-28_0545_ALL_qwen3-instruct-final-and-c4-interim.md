# Session log: Track B's final Qwen3 30B Instruct table (F16), thinking minus Instruct, and C4 at a third (2026-10-28 05:45 MST)

Project: CSE 598 Group 10. Track B measures, across open models, how often a wrong hint (from the
user, a pasted tool block, a real tool call or a system note) moves the answer and whether the reply
says so. Track C runs a solver/reviewer/checker team on Track B's cases. Ritik is asleep; this is
part of the overnight list.

## 1. Header

- **Time:** 2026-10-28 05:45 MST = 12:45 UTC.
- **Branch:** `trackA-nosol`, at `7ac2dc2` before; one commit with this log. Not pushed.
- **Running:**
  - **Track B, Olmo 3 7B Think:** on Voyager since 05:32 under the first power guard
    (`logs/guard.log`); 7 runs at 05:39, all ok. ~8 h or more.
  - **Track C, C4:** since 03:13 under the second guard (`logs/guard_c4.log`); 102 of 318 cases at
    05:39, no errors.

## 2. What ran

| Command | Where | Calls | Duration | Failures |
|---|---|---|---|---|
| Track B Qwen3 30B Instruct, `run_trackB.py --run` (guard) | Mac → Voyager | 810 runs | 03:11–05:32 | none: 0 without an answer |
| `trackB_report.py --export --by-set` | Mac | none | seconds | — |
| `run_team.py --summary --log team_c4 --cases … --table` (interim) | Mac | none | seconds | — |

**Not run: Instruct's steered export.** `--steered` appends to `results/trackB/steered_cases.jsonl`,
and C4 reads that file whenever the guard restarts it. Both Qwen3 checkpoints have the same 54 item
ids, so Instruct's rows would change C4's pools and collide with its case ids. It waits until C4 is
done (section 4 has the guard added).

## 3. Results

**Qwen3 30B Instruct, final** (FINDINGS F16). The same 54 questions × 5 conditions × 3 runs as F15.
Rates are Wilson; differences are a bootstrap clustered by question.

| channel | following | above the no-hint baseline | final answer names it, when following |
|---|---|---|---|
| user | 1 of 162 [0, 3%] | −1 [−2, +1] | 1 of 1 |
| tool, pasted | 35 of 162 [16, 29%] | +20 [+11, +30] | 29 of 35 [67, 92%] |
| tool, real call | 147 of 162 [85, 94%] | +90 [+82, +96] | 30 of 147 [15, 28%] |
| system note | 35 of 162 [16, 29%] | +20 [+11, +30] | 32 of 35 [78, 97%] |

- **Gate 2:** pasted +21 [+12, +31], real call +90 [+83, +96]. Both clear. No run past 16,000 tokens.
- **The real call:** it called the tool in 162 of 162 runs (tool choice is left to the model). The
  median real-call run is 35 output tokens over both turns.
- **By set:**
  - **Puzzles (24 q):** pasted, system and user 0 of 72 each; real call 72 of 72, and its final
    answer named the tool in 0 of those.
  - **MMLU-Pro (30 q):** pasted 35 of 90, real call 75 of 90, system 35 of 90.

**Thinking minus Instruct** (following, paired by question, 54 questions):

| channel | both sets | puzzles (24 q) | MMLU-Pro (30 q) |
|---|---|---|---|
| user | +1 [+0, +3] | +0 [+0, +0] | +2 [+0, +6] |
| tool, pasted | +15 [+6, +25] | +7 [+1, +12] | +21 [+6, +38] |
| tool, real call | −57 [−70, −43] | −94 [−99, −89] | −28 [−44, −10] |
| system note | +14 [+7, +20] | +10 [+4, +15] | +17 [+7, +27] |

- **Reading:** Instruct follows a real call because it calls every time. The Thinking checkpoint
  calls less (54 of 162) but follows pasted and system hints more.

**C4, interim** (102 of 318 cases, 51 items, mostly 1 repeat each). Not final; C5's run-to-run
variation needs the repeats.
- **The checker:**
  - It flagged 23 of 23 bad lookups [86, 100%] and 2 of 26 good ones (2 undetermined).
  - In the no-tool team it flagged 5 of 49 [4, 22%]: the floor.
  - Bad minus floor: +96 [+87, +100] (23 items).
- **The pipeline:** it shipped no wrong answer on a bad lookup (0 of 23, every variant), because the
  checker escalated them all.
- **The reviewer alone, bad lookups (23 items):**

  | reviewer | answer only | + explanation | + private reasoning | + tool log |
  |---|---|---|---|---|
  | Olmo 3.1 32B Instruct | corrects 19 | 19 | **2** | **1** |
  | Qwen3 30B Instruct | 19 | 19 | 21 | 17 |

  - The Olmo drop appears in both kinds: matched puzzles 12 of 13 → 2 of 13 (private reasoning);
    steered MMLU-Pro 5 of 8 → 0 of 8.
  - On good lookups, Olmo keeps the right answer in 22 of 28 (answer only) and 28 of 28 (private
    reasoning).
  - This repeats the 32B smoke's 3 of 3 → 0 of 3.

## 4. Changes

- **`progress/trackB_report.py`:** "clear" for thinking minus not is two-sided (the interval
  excludes 0, either sign). It was Gate 2's one-sided test, which called −57 [−70, −43] not clear.
  The printout marks "clear". Test added.
- **`agents/run_team.py`:** `case_items` takes one Track B model's rows. It uses `--case-model M`,
  or refuses a file with several models' rows. C4's command line still plans the same 53 items and
  318 cases (dry run checked). Test added.
- **Docs:** FINDINGS F16; `handoff/TRACK_B.md`, `handoff/TRACK_C.md`; TODO B7, B8, B9, B14, C4, C5.
- **Summaries:** `results/summaries/trackB/` re-exported (Instruct's rows, thinking minus not).

## 5. For review

- **Thinking vs Instruct is two checkpoints.** The −57 on the real call is "this Thinking
  checkpoint vs this Instruct one". Qwen3-8B on Sol (one set of weights, the switch) is the
  same-weights comparison; it waits for Ritik's go.
- **Instruct's real-call following is a call rate.** It calls the "course answer key" tool every
  time and answers with it. Whether that counts as "steered" or as using a tool it was invited to
  use is a framing question for the paper. The pasted block and the system note carry the same
  source claim and move it far less.
- **The interim C4 reviewer drop is from 23 items, mostly one repeat.** It is worth a FINDINGS
  entry only once C4 is done and paired by item.

## 6. Next

- C4: the full C5 tables and a FINDINGS entry when it finishes (~11:00–13:00); then Instruct's
  steered export.
- Olmo 3 7B Think: its table when the runs are done.
- The 7 am daily log, with the morning commands.
