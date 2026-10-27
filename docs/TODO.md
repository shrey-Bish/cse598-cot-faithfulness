# Open work, every track

Last updated: 2026-10-27 10:00 MST (week 11). Rebuilt from the session transcripts (Oct 4–27),
[`PLAN.md`](PLAN.md), [`FINDINGS.md`](FINDINGS.md), [`OVERVIEW.md`](OVERVIEW.md), the commit log
and every local and remote branch. How to run each step: [`RUNBOOK.md`](RUNBOOK.md).

- **Status:** done / in progress / not started / blocked.
- **Needs:** Voyager (ASU's API), Sol (GPU jobs), paid (closed-model API), or no calls.
- **Times** are working time for code and docs, and GPU or Voyager time for runs.
- **Owners:** Track B is Arsha's and Track C is Shrey's (PLAN, scope docs). The repo has no commits
  by Arsha and none by Shrey after Oct 4, so their local work can't be seen from here.

## The table

| # | Item | Track | From | Status | Blocked by | Owner | Needs | Time |
|---|---|---|---|---|---|---|---|---|
| A1 | Steps 6–7 to 240 kept questions (`run_steps67.py --kept 240 --checkpoint 100`) | A | Oct 25 "go" | in progress: 225 kept of 469 run (09:55 MST Oct 27) | — | Claude Code (pid 12290) | Voyager | done about 2–4 PM MST Oct 27 |
| A2 | The checkpoint report at 100 kept | A | Oct 25 | done: written Oct 26 10:42 MST, sent to Ritik Oct 27 (session log) | — | Claude Code | no calls | — |
| A3 | Final Steps 6–7 counts, then stop for "go" | A | Oct 27 | not started | A1 | Claude Code | no calls | 30 min |
| A4 | Assemble train / validation (`--assemble`): 10% no-hint, "neither" dropped if under 10%, counts | A | Oct 25, Oct 27 | not started (code exists) | A1, then "go" | Claude Code | no calls | 15 min |
| A5 | Export the final Steps 6–7 summaries | repo | Oct 26 | not started | A1 | Claude Code | no calls | 10 min |
| A6 | Untrack Track A data, rewrite this branch's history (`untrack_produced.py --run`); files stay on disk | repo | Oct 26 | not started (dry run clean) | A1; your approval and 4 scope choices (decision 2 in the log) | Ritik approves, Claude Code runs | no calls | 15 min |
| A7 | Push `trackA-nosol` and local `main` (it has the Oct 21 Voyager ID fix `280bd12`) | repo | Oct 26 | not started | A6, "go" | Ritik | no calls | 10 min |
| A8 | Step 11 `train.py`: LoRA only, tags only, both; 32,768 tokens, chunked loss, gradient checkpointing, checkpoint/resume; CPU tests | A | Oct 21, Oct 25 | not started | — | Claude Code | no calls | 4–6 h |
| A9 | Step 12 generation: tagged decoding loop, and the vLLM path (`tags_vllm.py`, equal on a tiny model on CPU) | A | Oct 21, Oct 25 | partial | — | Claude Code | no calls | 3–5 h |
| A10 | Step 13 `eval.py`: hint following, no-hint accuracy, mention, hiding check, false-disclosure check; X of Y, clustered bootstrap | A | Oct 21, Oct 25 | not started | — | Claude Code | no calls | 3–4 h |
| A11 | Sol job scripts for Steps 11–13 in the kit: account guard, resume, at most 8 h each when two run at once (16 h alone); CPU tests | A | Oct 25–26 | not started | A8–A10 | Claude Code | no calls | 2 h |
| A12 | First Sol job: the 20-step training timing run | A | Oct 27 | not started | A8, A11, "go" | Ritik submits | Sol | 30 min GPU |
| A13 | Step 12 check on Sol: do tags work in vLLM (prompt embeddings + LoRA on Olmo 3)? Fallback: own loop | A | Oct 25 | not started | A9, A11 | Ritik submits | Sol | ≤1 h GPU |
| A14 | Gate 3 job plan: every job in order, 2 at a time, hours, dates | A | Oct 26–27 | done (PLAN, Track A) | — | Claude Code | no calls | — |
| A15 | Train the 3 versions | A | PLAN | not started | A4, A12 | Ritik submits | Sol | 6–9 GPU h |
| A16 | Evaluate base, prompt-only and the 3 versions on Sol, finished by Nov 20 | A | Oct 26 | not started | A13, A15 | Ritik submits | Sol | 25–70 GPU h |
| A17 | Step 13 analysis: 4 measures, hiding check, false-disclosure check, measure 4 on hand-label categories, "tags help more on the inserted tool turn than the pasted block" | A | Oct 25, Oct 27 | not started | A16, L4 | Claude Code | no calls | 1 day |
| A18 | Look-inside rerun on the best version: Step 10 drops at 15/19/23; heads L19H31, L23H17, L15H31: drop, or stay while the answer stops following | A | Oct 26–27 | not started (code takes `--model`) | A16 | Ritik submits | Sol | 4–10 GPU h |
| A19 | Optional fourth version: LoRA on the attention of layers 15, 19, 23 only | A | Oct 26 | decision pending | your decision (log, decision 4) | Ritik | Sol | 6–16 GPU h |
| A20 | Training settings: one setting, or the rank × learning-rate grid in the finetune README | A | finetune README | decision pending | A12's timing | Ritik | Sol | grid: ×3–6 training hours |
| A21 | Hand the best version to Tracks B and C (week 15) | A | Oct 21 brief | not started | A16 | Ritik | Sol | — |
| A22 | Figure #1: the pinned panel (Step 2b per channel) | docs | Oct 26 | not started | — | Claude Code | no calls | 30 min |
| A23 | Figure #4: deletion vs control vs unedited | docs | Oct 26 | not started | — | Claude Code | no calls | 45 min |
| A24 | Sol scripts call `/scratch/ragarw68/envs/olmo/bin/python` by full path | A | Oct 27 | done (`39f8534`, with a test) | — | Claude Code | no calls | — |
| A25 | Record Step 9's matched onsets | A | Oct 27 | done (`07999f7`: F14, T9) | — | Claude Code | no calls | — |
| A26 | Olmo 3 32B identity (3 vs 3.1) on Voyager | all | Oct 4 | open | — | Ritik | no calls | 15 min |
| D1 | README, OVERVIEW, PLAN, FINDINGS, RUNBOOK, finetune and GPU READMEs brought up to date | docs | Oct 27 | done | — | Claude Code | no calls | — |
| D2 | Session logs after every run and every stop (`docs/sessions/`) | docs | Oct 27 | in progress (first log written) | — | Claude Code | no calls | 15 min each |
| L1 | The 10 label-queue rows with no text: regenerate (small Voyager job) or replace | labels | PLAN | not started | A1 (Voyager); decision 3 in the log | Claude Code | Voyager (10 calls) or no calls | 30 min |
| L2 | Labeling kit: two blank rater sheets from `LABEL_QUEUE.csv` (keyword columns hidden), the guide, a kappa-per-channel script that lists disagreements | labels | Oct 27 | not started | — | Claude Code | no calls | 1–2 h |
| L3 | Label the queue, two raters; Cohen's kappa per channel; under 0.6, tighten the guide and label a fresh batch | labels | PLAN (Gate 2, Nov 8) | not started | L2 | two raters | none | 3–4 h per rater |
| L4 | Phase 6 labeling sample: 200 evaluation replies + every false-disclosure candidate (PLAN, hand labels) | labels | Oct 25, Oct 27 | planned, size proposed | A16 | two raters | none | 6–8 h per rater |
| B1 | Closed-provider keys: a real OpenAI key (the current one is the Voyager key), Anthropic, xAI | B | Oct 5 | blocked | keys | Arsha | — | — |
| B2 | Is Claude Haiku 4.5 still served? Swap in its replacement if not (needs an adapter change for Haiku 5.5) | B | PLAN | not started | B1 | Arsha | no calls | 15 min |
| B3 | Closed-model smoke tests (`run_trackB.py --run --only-provider X --limit 1`) | B | Gate 1 | not started | B1 | Arsha | paid (under $0.20) | 15 min |
| B4 | Ollama `qwen3:8b`, thinking on and off, real tool calls | B | PLAN weeks 9–10 | not started (Ollama installed, model not pulled) | — | Arsha | local | 30 min + runs |
| B5 | Olmo 3 Think's `tool_injected` channel in Track B (`trackB.yaml` + `run_one` → `run_injected`); with `tool_real` it never sees the hint | B | Oct 21 | not started (exists in `tools/answer_key.py`) | — | Arsha (or Claude Code) | no calls | 1–2 h |
| B6 | GPQA Diamond access and export to `data/gpqa_diamond.jsonl`; the gitignore and hook exist only on `trackA-nosol` | B | PLAN | not started | gated access; A7 for the gitignore on `main` | Arsha | none | 1 h |
| B7 | Track B main runs, 3 per question | B | PLAN weeks 11–12 | not started (0 result rows) | B1–B5 | Arsha | Voyager + paid | ~15 h Voyager (below) |
| B8 | `steered_cases.jsonl` for Track C (no code writes it; format not defined) | B | PLAN | not started | B7 | Arsha | no calls | 1 h |
| B9 | Gate 2 (Nov 8): is the tool-vs-user gap still clear with 3 runs per question and more models? | B | PLAN | not started | B7 | Arsha | no calls | — |
| C1 | Live team on 5 items (`run_team.py --live --n 5`) | C | Gate 1 | not done: 2 items (Oct 4) | — | Shrey | Voyager (35 calls) | 15 min |
| C2 | No-tool baseline team (the solver always gets the tool today) | C | PLAN | not started | — | Shrey | no calls | 1–2 h |
| C3 | Second reviewer model (hard-coded today) | C | PLAN | not started | — | Shrey | no calls | 1 h |
| C4 | Run on Track B's steered cases (`live` takes pilot puzzles only) | C | PLAN | not started | B8 | Shrey | Voyager (~3,400 calls) | ~3–13 h |
| C5 | Analysis: shipped / caught / false alarms per reviewer variant, with intervals, and cost | C | PLAN | not started | C4 | Shrey | no calls | 3 h |
| C6 | `run_team.py` deletes its own log and writes to tracked `results/scope/`: make it append-only, write to gitignored `results/trackC/` | C, repo | Oct 22, Oct 26 replies | not fixed (left to its owner) | owner | Shrey | no calls | 30 min |
| G1 | Gate 1 (Oct 25): not met as far as the repo shows; the plan's fallback applies (PLAN, gates) | all | PLAN | missed | B1, C1 | everyone | — | — |
| R1 | GitHub `main` still has the old Voyager IDs: runs from GitHub fail the Oct 21 routing | repo | Oct 21 | open | A7 | Ritik | no calls | — |
| R2 | The pre-push hook is installed only on this Mac; each teammate installs it (RUNBOOK, repo hygiene) | repo | Oct 26 | open | — | each teammate | no calls | 2 min |

## Notes

**A2, the checkpoint report at 100 kept** (written Oct 26 10:42 MST, after 250 questions; not sent
at the time because the session ran out):
- **Keep rate:** 117 of 250 [41, 53%], pilot 5 of 10. Kept by set: MMLU-Pro 68 of 149, hard puzzles
  46 of 96, easy puzzles 3 of 5.
- **Step 7, a prefill target within 4 samples:**

  | channel | wrong hint | correct hint |
  |---|---|---|
  | user | 112 of 117 [90, 98%] | 60 of 61 [91, 100%] |
  | tool, pasted | 110 of 117 [88, 97%] | 59 of 59 [94, 100%] |
  | tool, inserted (declared) | 102 of 117 [80, 92%] | 62 of 62 [94, 100%] |

  Failed samples: wrong letter 192, hit the token cap 18, reasoning refers to instructions 14,
  called the tool again 6. No rate was off by more than half from the pilot, so the run went on.
- **Target length** (prompt + target, tokens; median / 90th percentile / max): easy puzzles 5,401 /
  7,356 / 9,611 (18 examples); hard puzzles 11,342 / 16,869 / 26,748 (204); MMLU-Pro 4,678 / 10,409 /
  18,523 (311); all 7,352 / 14,094 / 26,748 (533). Held-out Step 2b replies: 11,988 / 24,856 / 34,706.
- **Stance after the final-answer opener** (keyword count): wrong hint: disagrees 331, agrees after
  checking 13, neither 7; correct hint: agrees after checking 148, disagrees 14, neither 20.
  "Neither" 27 of 533 (5%).

**A1 now** (09:55 MST Oct 27): 469 questions run, 225 kept (48%); 979 examples for the 216 kept by
the last finished batch, 49 of them "neither" (5%). Two more batches of 40 are almost certainly
needed (each keeps 16–21). The overnight slowdown was the Mac asleep on battery (11:35 PM–8:28 AM).

**Proposed order for Tracks B and C once Voyager is free** (Track A then needs Voyager only for L1):

| # | Step | Calls | Time |
|---|---|---|---|
| 0 | Code, no calls: B5, C2, C3, C6, a model flag for `run_trackB.py`, an input-file option for `run_team.py` | 0 | 1 day |
| 1 | If an Anthropic key exists: smoke test, then the Haiku grid (180 jobs + ~60 tool rounds, guard at $5) | 4, then ~240 | 5 min, then 1–2 h |
| 2 | Ollama: pull `qwen3:8b`, check thinking on and off, `--limit 1`; then a cut grid (MMLU-Pro × none / user / tool_real × on / off) | 1–5, then ~240 | 30 min, then local hours |
| 3 | C1: live team on 5 items (copy `team_live.jsonl` first: the run rewrites it) | 35 | 15 min |
| 4 | Track B Voyager smoke, `--limit 5` | 5 | 5 min |
| 5 | Track B, Qwen3 30B Thinking first (Track C's solver): 54 questions × 5 conditions × 3 runs + tool rounds | ~972 | ~5.4 h (972 × 80 s / 4) |
| 6 | Track B, Qwen3 30B Instruct | ~972 | ~1.4 h |
| 7 | Track B, Olmo 3 7B Think with `tool_injected` | ~810 | ~7.9 h (810 × 140 s / 4) |
| 8 | Export `steered_cases.jsonl`; Track C on N steered + N matched no-hint cases, 3 repeats, tool and no-tool teams | ~114 × N (N = 30: ~3,400) | ~3.3 h at 4 in flight; ~13 h one at a time, as written |

Without GPQA: about 6,200 Voyager calls, 18–28 hours. GPQA on Voyager, cut to Qwen3 Thinking ×
none / user / tool_real × 1 run: ~792 calls, ~4.4 h. Times for Haiku and Ollama are assumptions
(no timing data in the repo). The 4-in-flight limit is shared by every process on this Mac.
