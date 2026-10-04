# Run log: progress-presentation run, 2026-10-04

The session log lives at `cot-disclosure/logs/progress_20261004T201106Z.log`. It is
gitignored; a sanitized copy goes into the bundle. All times are UTC (MST = UTC − 7).

## Code map (Phase 0)

What the new scripts reuse from the repo, unchanged or extended:

| Repo piece | What it does | How the progress scripts use it |
|---|---|---|
| `client.chat()` | Streams the reply from Voyager, splits private reasoning (`reasoning_content` / `reasoning` delta) from the visible answer (`content`), caches each reply on disk keyed by the request, retries transport errors | Every new call goes through it. **Extended**: optional `backoff=[2,4,8]` and `on_retry` callback so retries are logged, and the result now includes `retries`, `latency_s`, `reasoning_field`, `cached`. An optional `stream=False` path has its own cache key; existing cache keys are unchanged. Added `list_models()`. |
| `parse.parse_answer()` | Priority rules: `Answer: (X)`, `\boxed{X}`, "answer is X", bold, lone trailing `(X)` | **Extended** from A–I to A–J. `n_options` still limits valid letters, so seven-option puzzles parse exactly as before. Added `parse_final()` for the reviewer's `FINAL: X` line, which falls back to `parse_answer` and labels the rule `fallback:...`. |
| `detect.detect()` | Keyword pre-sort: `cue`, `uncertainty`, `self_correction`, `ack_influence` | Reused for every mention count. **Extended** with a `cue_tool` pattern (lookup, answer key, study guide, expected, tool) for the simulated tool block. |
| `experiments.py` | Pilot grid: `ITEMS` (24 balanced puzzles), `CUE` (Turpin wording), `STEPS` (answer instruction), balanced wrong cues, seeds | **Refactored** one function: `build_prompt(idx, kind, seed, instruction)` returns the exact pilot user message, so pilot calls can be replayed byte for byte. `run_job` calls it; behaviour is unchanged. |
| `analyze.py` | Pilot numbers → `results/summary.json` | Reused through `main_summary`, `brief_summary`, `nocot_summary`, `history_summary`, imported from `analyze_progress.py`. |

**Pilot result line** (`results/progress.jsonl`, 1,056 lines): `exp` (main / brief /
nocot), `model`, `thinking`, `item` (0–23), `cue_kind` (none / wrong / correct), `seed`,
`cue`, `correct`, `answer`, `parse_rule`, `is_correct`, `followed_cue`, `finish`, `error`,
`trace_chars`, `answer_chars`, `out_tokens`, `trace{cue, uncertainty, self_correction,
ack_influence}`, `said{...}`. **The texts themselves are not stored.** The reply cache
(`cache/`) wasn't kept in the repo and was empty on this machine. Any pilot text we need
(Experiment A, case studies, evidence viewer) is recovered by a seeded replay, and each
replay is checked against the stored lengths, answer and token count.

New files follow the record schema in the brief (section 6). New helper:
`cot-disclosure/progress/common.py` holds logging, the 4-slot limiter, run IDs, the
record builder and Wilson intervals.

## Chronological log

| Time (UTC) | Command / step | Purpose | Calls | Failures / retries | Notes |
|---|---|---|---|---|---|
| 19:55 | read README, code, results | recon | 0 | – | `cache/` absent; `.env` ignored via `cot-disclosure/.gitignore` (`git check-ignore` → `.env`) |
| 20:00 | `python3 -m venv .venv`; `pip install matplotlib numpy pandas datasets playwright pytest`; `playwright install chromium` | environment | 0 | – | The repo has no requirements file (stdlib only); nothing pinned was upgraded. Python 3.14.7. |
| 20:02 | `git checkout -b progress-oct2026` | branch | 0 | – | The working tree already had two uncommitted user changes (`.gitignore` adds `*.md`; `cot-disclosure/.env.example` deleted). Both were left alone and never staged. |
| 20:05 | `python3 analyze.py` (in `cot-disclosure/`) | reproduce pilot | 0 | – | Output matches the slide numbers; differences listed below. `analyze.py` rewrites `results/summary.json` with a different key order (set iteration) and float repr, but the same values. That file was restored with `git checkout` so existing results stay untouched. |
| 20:08 | `pytest cot-disclosure/tests` | parser A–J, `cue_tool` keywords, helpers | 0 | – | Tests written first; watched them fail, then pass. |
| 20:11:06 | `progress/mmlu_pro_probe.py select` | 30 MMLU-Pro items | 0 | – | `mmlupro_30.jsonl` sha256 `0abd5efb…f65c0`, dataset revision `b189ec76…71f97be`. 8 law, 8 engineering, 7 chemistry, 7 physics. Cue letters 2–4 per letter. |
| 20:11:34–20:13:35 | `progress/timing_run.py` | catalog + timing | 9 (+1 `/models`) | 0 / 0 | 55 catalog IDs, 6/6 study models present. Projected Experiment B: 32 min no-cue + 22 min cued at 4 in flight (< 100 min, so all 30 items kept). |
| 20:13:58 | `nohup progress/mmlu_pro_probe.py nocue &` | Experiment B no-cue screen | 180 planned | see below | resumable by run_id |
| 20:14:10 | `nohup progress/reviewer_demo.py all &` | Experiment A: replay → guard → review | ~114 planned | see below | shares the 4 request slots with Experiment B |

## Pilot verification: brief vs `analyze.py`

`analyze.py` is the reference. These are the differences from the numbers in the brief:

1. **Olmo 3 7B Think wrong-hint following, upper end of the 95% range.** The exact value
   is 0.0625 (6.25 points). `analyze.py` prints 6.2. The brief says 6.3. This is rounding
   only.
2. **"Answer only: thinking models stayed 88% to 96% accurate"** mixes up two numbers.
   87.5% (21/24) and 95.8% (23/24) are the shares of answer-only replies that still
   produced a private trace (Olmo 7B Think and Qwen 30B Thinking). Accuracy under answer
   only was 23/24 (95.8%) and 24/24 (100%). Corrected wording: "thinking models kept
   reasoning privately in 21/24 and 23/24 answer-only replies and stayed 96% and 100%
   accurate."
3. **Typical output tokens, Qwen 30B Thinking.** The median is 3,996.5. `analyze.py`
   prints 3,996; the brief says 3,997. Olmo 7B Instruct: 2,020.5 (brief 2,021, printed
   2,020). Rounding only.
4. **"10 of 10 replies that hit the token limit spilled private reasoning."** True for the
   **earlier ladder run** (8,000-token cap, `results/ladder.jsonl`, all from Olmo 3 7B
   Think, median 26,896 characters in the visible field). In the progress-round main grid
   at the 16,000-token cap, 5 replies were cut off (all Olmo 3 7B Think). In **0 of 5**,
   the reasoning landed in the visible field: it stayed in the private field (median
   54,408 characters) and the visible answer was empty. So the leak isn't a fixed property
   of hitting the cap. A likely difference is that the ladder ran before the client
   switched to streaming. Phase 3c tests this.
5. **Keyword baseline not shown on the slides.** The `cue` keyword fires on private
   reasoning in no-hint runs too, because traces say "the user" without any hint:
   - Olmo 7B Think 22/72
   - Olmo 32B Think 18/72
   - Qwen 30B Thinking 2/72

   The private-mention counts with a hint (66/72, 71/72, 71/72) have to be read against
   that baseline. It is a keyword pre-sort, not acknowledgment.

Everything else matches:
- 1,056 calls, 0 failed; 312 earlier calls (120 ladder + 192 early pilot)
- 864 main-grid calls
- wrong-hint following 5/48 (10.4%, 95% range 2.1 to 18.8) and 1/48; 0/48 for the other
  four models
- 0/144 same-letter choices without a hint, for every model
- Olmo 7B Instruct changed its no-hint answer on 7/24 puzzles, none to a hinted letter
- 208/216 private and 8/216 final mentions
- Olmo instruct 56/144 vs Olmo thinking 0/144 final mentions; Qwen 6/72 vs 8/72
- 4.9% to 58.9% longer with a hint
- answer only: 21/24 → 1/24 and 24/24 → 2/24
- think briefly: 29.8% and 47.7% shorter reasoning

## Deviations from the brief (with reasons)

- **`docs/` location and git.** `docs/progress/` is at the repo root, as in the output
  map. The root `.gitignore` whitelists only `README.md`, `cot-disclosure/` and
  `presentation/`, and the user's uncommitted `*.md` line ignores all Markdown. Instead of
  editing `.gitignore` (which would also stage the user's change), the progress docs are
  added with `git add -f`.
- **Extra result files.** `results/progress/pilot_replay.jsonl` holds the seeded replays
  of the pilot texts Experiment A needs. `results/progress/expA_guard.jsonl` holds the
  counterfactual re-asks. `results/progress/expB_plan.json` holds the per-model item
  classification and cue plan.
- **Answer instruction for MMLU-Pro.** The pilot instruction ("…give your final answer in
  the format 'Answer: (X)'.") doesn't list letters, so it is reused verbatim. Only the
  parser's valid letters change to A–J.
- **Guard re-ask seed.** A re-ask with the hint removed and the pilot's own seed would
  repeat the pilot's no-hint run exactly (same payload). So the fresh re-ask uses seed 3,
  the next unused seed.
- **Retry policy.** `BACKOFF = [2, 4, 8]`, at most 3 retries (4 tries in all), only on
  HTTP 408/429/5xx/524 and connection or timeout errors. Every retry is logged with its
  run_id.
- **Four in flight across processes.** A lock-file semaphore (`logs/.slots/slot0..3`) is
  shared by every script, so Experiments A and B running together never exceed 4 open
  requests.
