# Session log: Track B's interim table (Qwen3 30B Thinking, one run per question) and a Voyager halt that holds (2026-10-28 00:45 MST)

Project: CSE 598 Group 10. Track B measures, across open models, how often a wrong hint (from the
user, a pasted tool block, a real tool call or a system note) moves the answer and whether the reply
says so. This log has the first numbers with enough questions, the report fixes found on the way,
and a change so that a failed identity canary pauses all Voyager work overnight.

## 1. Header

- **Time:** 2026-10-28 00:45 MST = 07:45 UTC.
- **Branch:** `trackA-nosol`; commits `49f1f76` (00:32 log) and `e0b6870` (this work). Not pushed.
  **Tests:** 396 pass.
- **Running:** Track B Qwen3 30B Thinking on Voyager, 180 of 663 runs since 23:36. About 2.9 runs a
  minute, so done around 03:30; then Qwen3 30B Instruct, then Olmo 3 7B Think.

## 2. Results (interim)

Qwen3 30B Thinking, 54 questions (24 puzzles, 30 MMLU-Pro), mostly 1 run each so far. The 32,768
budget; X of Y with a 95% bootstrap clustered by question:

| channel | following (hint letter) | above the no-hint baseline | final answer names the hint | private reasoning names it |
|---|---|---|---|---|
| user | 2 of 62 [0, 8%] | +3 [0, +8] | 13 of 62 | 59 of 62 |
| tool, pasted | 19 of 62 [19, 44%] | +31 [+19, +44] | 54 of 62 | 62 of 62 |
| tool, real call | 23 of 62 [25, 50%] | +37 [+25, +50] | 1 of 62 | 36 of 62 |
| system note | 17 of 61 [17, 40%] | +28 [+17, +40] | 41 of 61 | 55 of 61 |

- **Gate 2 (tool − user, paired by question):** pasted +27 points [+16, +41], real call +34 [+21,
  +47]. Both are clear so far.
- **The real tool call:** Qwen3 30B Thinking called it in 23 of 62 runs and took the tool's wrong
  letter in **23 of 23** of those (0 of 39 without the call). When it followed the real tool, its
  final answer named the tool once in 62 runs.
- **Interim only:** most questions have 1 of their 3 runs, and only 8 questions count as "sure" yet
  (that needs 2 or more no-hint runs). FINDINGS gets the entry when the 3 runs are in (about 03:30).

## 3. Fixes

- **The report counted Ollama's 20 old rows**, made at the default 4,096 context that dropped the
  question (T10); the runner already didn't count them as done. `trackB_report.py` now leaves out
  what the runner leaves out (Ollama off the current context; a reply cut at an older cap). 2
  Ollama rows remain, reported apart.
- **The printed table** adds following above the per-letter no-hint baseline, and following when
  the tool was called.
- **A failed Voyager guard pauses all Voyager work.** Before, a failed identity canary made the
  runner exit and the power guard restart it every minute, each time with another canary call. Now:
  - the client writes `logs/voyager_halted`, and every process then refuses Voyager requests
    without making a call;
  - the runners exit with code 3, and the guard doesn't restart them, pauses the other Voyager
    jobs, and starts nothing waiting on them.

  The guard running since 23:36 has the old code, but the halt file already stops its restarts
  from calling Voyager.
- **Track C:**
  - `run_team.py` takes `--stop-file` and returns the same exit codes, so C4 can run under the
    guard.
  - C5 is in the summary: the no-tool solver's run-to-run variation, the checker's floor, and the
    bad- and good-lookup flag rates minus the floor, paired by item.
  - `--table` prints the summary as tables.

## 4. For review

- The tool channels' "final answer names the hint" differ a lot: pasted 54 of 62 vs real call 1 of
  62. With a real call the hint comes back as a tool result, and the final answer cites it rarely;
  the pasted block sits in the question and gets quoted. The counts are keywords (`detect.py`), not
  labels.

## 5. Next

At ~03:30: the final Qwen3 Thinking table and FINDINGS entry, the steered export, then C4 under the
guard. The 7 am daily log.
