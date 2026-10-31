# Session log: Qwen3-8B, thinking on and off in the same weights (2026-10-30 09:15 MST)

Project: CSE 598 Group 10, Track B. B4 runs Qwen3-8B (`Qwen/Qwen3-8B` @ `b968826d`) on our own vLLM server on Sol,
with thinking on and off through `enable_thinking`. It is the only model in Track B where thinking is switched with
the weights held fixed. Track B's 54 questions, every channel, 3 runs, 1,620 runs. FINDINGS F29. **By:** Ritik.

## 1. What ran

- Sol 66954217, 2:00:45, exit 0, all 1,620 runs. The numbers-only `sol_vllm_runs.jsonl` and `sol_vllm_flags.jsonl`
  came back by rsync.
- Read on the Mac: `python progress/trackB_report.py --export --by-set`.

## 2. What was fixed in advance, and how it is read

- PLAN (Track B) fixed the table, per model × channel × thinking on/off: following against the per-letter no-hint
  baseline, admission in the final answer and the reasoning, the tool-call rate. Gate 2's rule (tool minus user,
  interval above 0) applies to each mode.
- No decision rule was written for thinking on minus off. Here it is read plainly: "differs" if its paired 95%
  interval (clustered by question) excludes 0, "no difference detected" otherwise. That reading is mine, made
  after the fact, and labelled so.

## 3. Results (one budget of 32,768 tokens)

| channel | thinking off: following | thinking on: following | on minus off |
|---|---|---|---|
| user | 19 of 159 [6, 19%] | 16 of 162 [4, 18%] | −2 [−8, +4]: no difference detected |
| pasted tool block | 41 of 162 [15, 36%] | 47 of 162 [18, 41%] | +4 [−4, +11]: no difference detected |
| real tool call | 40 of 162 [15, 35%] | **143 of 162 [81, 94%]** | **+64 [+51, +75]: differs** |
| system note | 29 of 162 [10, 27%] | 45 of 161 [17, 39%] | +10 [+2, +19]: differs |

- **Gate 2 is clear in both modes.**
  - Off: pasted − user +13 [+7, +21]; real − user +13 [+3, +23].
  - On: pasted − user +19 [+10, +29]; real − user +78 [+69, +86].
- **The real call's difference is the call rate.** Thinking on calls the tool in 145 of 162 runs, off in 35 of 162.
  When it calls, it takes the letter either way: on 143 of 145, off 33 of 35.
- **After a call, F15's pattern:**
  - With thinking on, the final answer is bare in 138 of 145 calls. When following, it names the tool in 0 of 143.
    The private reasoning names it in 141 of 145.
  - With thinking off, it is bare in 12 of 35 calls, and names the tool in 13 of 40 followed runs.
- **No-hint accuracy:** on 137 of 162 [75, 93%], off 122 of 162 [67, 83%]. Sure questions: 44 and 29 of 54.
- **With Track B's 16,000-token cut** (decided Oct 28), thinking on loses 43 runs to "no answer", most on MMLU-Pro.
  On minus off is the same: real call +63 [+50, +75], system note +9 [+1, +19], pasted +3, user −4.

## 4. Reading

- **In the same weights, turning thinking on makes Qwen3-8B call the lookup far more often, and so take its wrong
  letter far more often.** The pasted block and the user hint don't move.
- The Qwen3 30B twins went the other way: Thinking minus Instruct on the real call was −57, because the Instruct
  model calls every time. "Thinking" is not one thing across checkpoints. For calling a tool, what decides
  following is the call.
- After the call, thinking on gives the F15 picture in a third model: the reasoning names the tool, and the final
  answer is a bare letter.
- **Limits:**
  - One model.
  - Keyword counts until the hand labels.
  - The table also carries a 2-run `ollama | qwen3:8b` row from the Oct 27 timing pilot. It isn't part of B4 and
    should be left out of the paper's table.

## 5. What changes

- **FINDINGS F29.**
- **CLAIMS:** Track B's supporting claims; 1.1 and 1.2 gain a fourth model.
- **TODO:** B4 done.
- **TRACK_B handoff:** Qwen3-8B's results.
- **The Track B summaries** re-exported.

## 6. Source

`results/summaries/trackB/trackB_report.json`, `trackB_report_by_set.json`, `trackB_runs.jsonl` (numbers only).
