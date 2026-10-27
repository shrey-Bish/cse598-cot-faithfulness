# Open work, every track

Last updated: 2026-10-27 12:30 MST (week 11). Rebuilt from the session transcripts (Oct 4–27),
[`PLAN.md`](PLAN.md), [`FINDINGS.md`](FINDINGS.md), [`OVERVIEW.md`](OVERVIEW.md), the commit log
and every local and remote branch; updated with Ritik's decisions and the Oct 27–Nov 3 plan. How
to run each step: [`RUNBOOK.md`](RUNBOOK.md).

- **Status:** done / in progress / not started / blocked.
- **Needs:** Voyager (ASU's API), Ollama (local), Sol (GPU jobs), paid (closed-model API), or no
  calls. Paid calls and Sol jobs always wait for Ritik's "go"; GPQA waits until Ritik has
  accepted its terms on Hugging Face.
- **Times** are working time for code and docs, and GPU or Voyager time for runs.
- **Owners:** until Nov 3 Ritik owns all three tracks (code work by Claude Code). On Nov 3 Track
  B goes back to Arsha and Track C to Shrey; "→ Arsha" / "→ Shrey" marks the owner from then.
  The repo has no commits by Arsha and none by Shrey after Oct 4, so their local work can't be
  seen from here.

## Track A

| # | Item | From | Status | Blocked by | Owner | Needs | Time |
|---|---|---|---|---|---|---|---|
| A1 | Steps 6–7 to 240 kept questions (`run_steps67.py --kept 240 --checkpoint 100`) | Oct 25 "go" | in progress: 237 kept after 490 questions (12:00 MST Oct 27); last chunk of 40 running | — | Claude Code (pid 12290) | Voyager | done about 2–4 PM MST Oct 27 |
| A2 | The checkpoint report at 100 kept | Oct 25 | done: written Oct 26 10:42 MST, sent Oct 27 (notes below) | — | Claude Code | no calls | — |
| A3 | Final Steps 6–7 counts and the final-count log | Oct 27 | not started | A1 | Claude Code | no calls | 30 min |
| A4 | Assemble train / validation (`--assemble`): 10% no-hint, "neither" dropped if under 10%, counts | Oct 25; "go" Oct 27 | not started (code exists; runs as soon as A1 ends) | A1 | Claude Code | no calls | 15 min |
| A5 | Export the final Steps 6–7 summaries | Oct 26 | not started | A1 | Claude Code | no calls | 10 min |
| A6 | History rewrite (`untrack_produced.py --run`), approved Oct 27 with conditions: `git bundle` backup and a sha256 list of every file under `results/`, `finetune/data/`, `configs/` first; keep tracked `configs/canary/*.json`, `results/summaries/`, `docs/sessions/` and every numbers-only summary; rewrite only commits unique to `trackA-nosol` (a plan for `main` first if it carries produced files); after: tests pass, sha256 list identical, pre-push check passes on both branches | Oct 26, Oct 27 | not started (dry run clean) | A1 | Claude Code | no calls | 30 min |
| A7 | Merge `trackA-nosol` into local `main` (shared code, docs, no produced data); tests; push commands for Ritik | Oct 27 | not started | A6 | Claude Code; Ritik pushes | no calls | 30 min |
| A8 | Step 11 `train.py`: LoRA only, tags only, both; 32,768 tokens, chunked loss, gradient checkpointing, checkpoint after each epoch and resume; validation loss per epoch; CPU tests | Oct 21, Oct 25 | not started | — | Claude Code | no calls | 4–6 h |
| A9 | Step 12 generation: tagged decoding loop, and the vLLM path (`tags_vllm.py`, equal on a tiny model on CPU) | Oct 21, Oct 25 | partial | — | Claude Code | no calls | 3–5 h |
| A10 | Step 13 `eval.py`: hint following, no-hint accuracy, mention, hiding check, false-disclosure check; X of Y, clustered bootstrap | Oct 21, Oct 25 | not started | — | Claude Code | no calls | 3–4 h |
| A11 | Sol job scripts for Steps 11–13 in the kit: account guard, checkpoint/resume; CPU tests | Oct 25–26 | not started | A8–A10 | Claude Code | no calls | 2 h |
| A12 | Sol kit QoS checks (Oct 27): one config file of accounts, partitions, QoS and limits (only listed accounts allowed; today the course account); each job's limit = estimate × 1.3 rounded up to 30 min; `submit.sh` refuses a job over 960 GPU-minutes, adds the remaining GPU-minutes of running and pending jobs (`squeue`), warns over 960 and says when the second slot frees; QoS fields in the GPU README | Oct 27 | not started (fields recorded in PLAN) | — | Claude Code | no calls | 2 h |
| A13 | First Sol jobs: S1 the 20-step timing run, S2 the vLLM tag check (prompt embeddings + LoRA on Olmo 3; fallback own loop) | Oct 25, Oct 27 | not started | A8, A9, A11, A12, "go" | Ritik submits | Sol | ≤2.5 h GPU |
| A14 | Gate 3 job plan: every job in order, 2 at a time, limits, dates | Oct 26–27 | done (PLAN; updated Oct 27 with the QoS and the accelerated dates) | — | Claude Code | no calls | — |
| A15 | Train the 3 versions (S3–S5): rank 16, LoRA 2e-4, tag table 1e-3, 2 epochs; checkpoint per epoch, chosen by validation loss only (decided Oct 27) | PLAN | not started | A4, A13 | Ritik submits | Sol | 6–9 GPU h |
| A16 | Evaluate base, prompt-only and the 3 versions on Sol (E1–E5), from Oct 30 | Oct 26 | not started | A13, A15 | Ritik submits | Sol | 25–70 GPU h |
| A17 | Step 13 analysis: 4 measures, hiding check, false-disclosure check, measure 4 on hand-label categories, "tags help more on the inserted tool turn than the pasted block" | Oct 25, Oct 27 | not started | A16, L4 | Claude Code | no calls | 1 day |
| A18 | Look-inside rerun on the best version (L1): Step 10 drops at 15/19/23; heads L19H31, L23H17, L15H31: drop, or stay while the answer stops following | Oct 26–27 | not started (code takes `--model`) | A16 | Ritik submits | Sol | 4–10 GPU h |
| A19 | Fourth version (S6, E6): LoRA on the attention of layers 15, 19, 23 only; included, scheduled last, dropped if E1–E5 aren't done by Nov 9 | Oct 26, Oct 27 | decided; not started | A16 | Ritik submits | Sol | 6–16 GPU h |
| A20 | Training settings | finetune README | done: one setting, decided Oct 27 (A15) | — | Ritik | — | — |
| A21 | Hand the best version to Tracks B and C (week 15) | Oct 21 brief | not started | A16 | Ritik | Sol | — |
| A22 | Figure #1: the pinned panel (Step 2b per channel) | Oct 26 | not started | — | Claude Code | no calls | 30 min |
| A23 | Figure #4: deletion vs control vs unedited | Oct 26 | not started | — | Claude Code | no calls | 45 min |
| A24 | Sol scripts call `/scratch/ragarw68/envs/olmo/bin/python` by full path | Oct 27 | done (`39f8534`, with a test) | — | Claude Code | no calls | — |
| A25 | Record Step 9's matched onsets | Oct 27 | done (`07999f7`: F14, T9) | — | Claude Code | no calls | — |
| A26 | Copy Sol's original `step9_followup.json` to `results/trackA/gpu/original/step9_followup_sol.json` (gitignored) | Oct 27 | done (sha256 `6282a790…`, same as the scratchpad copy) | — | Claude Code | no calls | — |
| A27 | Olmo 3 32B identity (3 vs 3.1) on Voyager | Oct 4 | open | — | Ritik | no calls | 15 min |

## Track B (Ritik until Nov 3, then Arsha)

| # | Item | From | Status | Blocked by | Owner | Needs | Time |
|---|---|---|---|---|---|---|---|
| B5 | Olmo 3 7B Think in Track B through the pinned Think format on `/v1/completions` (`olmo_format.py`), with the declared `tool_injected` channel in place of `tool_real` | Oct 21, Oct 27 | not started (exists in `tools/answer_key.py` and Track A) | — | Claude Code → Arsha | no calls | 1–2 h |
| B12 | A model flag for `run_trackB.py` | Oct 27 | not started | — | Claude Code → Arsha | no calls | 30 min |
| B8 | `steered_cases.jsonl`: define the format (no code writes it today), then export from B7 | PLAN, Oct 27 | not started | format: —; export: B7 | Claude Code → Arsha | no calls | 1 h |
| B10 | Served chat template per Voyager model (prompt-token count against a local rendering, as for Olmo on Oct 21), recorded | Oct 27 | not started | — | Claude Code → Arsha | Voyager (a few calls) | 30 min |
| B11 | Identity-canary references for every Voyager model Tracks B and C use, before their first batch | Oct 27 | not started | — | Claude Code → Arsha | Voyager (a few calls) | 30 min |
| B13 | Per model: smoke test (`--limit 5`) and the dry run (calls, hours) in a session log; then the run starts | Oct 27 | not started | B5, B10–B12 | Claude Code → Arsha | Voyager | 15 min each |
| B7 | Voyager runs, 3 per question, the 24 puzzles and the 30 MMLU-Pro items, all conditions: Qwen3 30B Thinking, then Qwen3 30B Instruct, then Olmo 3 7B Think | PLAN, Oct 27 | not started (0 result rows) | B13 | Claude Code → Arsha | Voyager | ~15 h (notes) |
| B4 | Ollama `qwen3:8b`, thinking on and off, real tool calls: a 5-call timing pilot, then the grid it allows | PLAN, Oct 27 | not started (Ollama installed, model not pulled) | — | Claude Code → Arsha | Ollama | 30 min + runs |
| B14 | Track B table: model × channel × thinking (on/off where it exists); hint following against the per-letter no-hint baseline; sure and unsure questions; mention in the private reasoning and the final answer (keywords); tool-call rate | Oct 27 | not started | B7, B4 | Claude Code → Arsha | no calls | 3 h |
| B9 | The Gate 2 question: is the tool-vs-user gap still clear with 3 runs per question and more models? Answered as soon as the data allows | PLAN, Oct 27 | not started | B14 | Claude Code → Arsha | no calls | — |
| B1 | Closed-provider keys: a real OpenAI key (the current one is the Voyager key), Anthropic, xAI | Oct 5 | blocked | keys | Ritik → Arsha | — | — |
| B2 | Is Claude Haiku 4.5 still served? Swap in its replacement if not (Haiku 5.5 needs an adapter change) | PLAN | not started | B1 | Claude Code → Arsha | no calls | 15 min |
| B3 | Closed-model smoke tests (`run_trackB.py --run --only-provider X --limit 1`) | Gate 1 | blocked | B1, "go" (paid) | Ritik → Arsha | paid (under $0.20) | 15 min |
| B6 | GPQA Diamond: export to `data/gpqa_diamond.jsonl` (gitignored); nothing from it in any doc or tracked file | PLAN | blocked | Ritik accepts its terms on Hugging Face and says so | Claude Code → Arsha | none | 1 h |

## Track C (Ritik until Nov 3, then Shrey)

| # | Item | From | Status | Blocked by | Owner | Needs | Time |
|---|---|---|---|---|---|---|---|
| C6 | `run_team.py`: append-only, writing to gitignored `results/trackC/` (today it deletes its own log and writes to tracked `results/scope/`) | Oct 22, Oct 26, Oct 27 | not started | — | Claude Code → Shrey | no calls | 30 min |
| C2 | No-tool team (the solver always gets the tool today) | PLAN | not started | — | Claude Code → Shrey | no calls | 1–2 h |
| C3 | Second reviewer model (hard-coded today) | PLAN | not started | — | Claude Code → Shrey | no calls | 1 h |
| C7 | Input-file option for `run_team.py` (`live` takes pilot puzzles only) | Oct 27 | not started | — | Claude Code → Shrey | no calls | 1 h |
| C1 | Live team on 5 items (`run_team.py --live --n 5`) | Gate 1 | not done: 2 items (Oct 4) | C6; room on Voyager | Claude Code → Shrey | Voyager (35 calls) | 15 min |
| C4 | The team on Track B's steered cases (Qwen3 Thinking's first), 3 repeats, tool and no-tool teams | PLAN, Oct 27 | not started | B8, C2, C3, C7 | Claude Code → Shrey | Voyager (~3,400 calls) | ~3–13 h |
| C5 | Track C table per reviewer variant: shipped, caught, false alarms, undetermined; bad and good lookups apart; the checker's disagreement against the no-tool team's run-to-run variation; tokens | PLAN, Oct 27 | not started | C4 | Claude Code → Shrey | no calls | 3 h |

## Labels

| # | Item | From | Status | Blocked by | Owner | Needs | Time |
|---|---|---|---|---|---|---|---|
| L1 | Replace the 10 label-queue rows with no text: no calls, the original rule (random hinted pilot runs with saved text, seed recorded), marked as replacements in the queue and in the guide | PLAN; decided Oct 27 | not started | — | Claude Code | no calls | 30 min |
| L2 | Labeling kit: two blank rater sheets from `LABEL_QUEUE.csv` (keyword columns hidden), the guide, a kappa-per-channel script that lists disagreements (no labels filled by Claude Code) | Oct 27 | not started | — | Claude Code | no calls | 1–2 h |
| L3 | Label the queue, two raters; Cohen's kappa per channel; under 0.6, tighten the guide and label a fresh batch | PLAN (Gate 2, Nov 8) | not started | L1, L2 | two raters | none | 3–4 h per rater |
| L4 | Phase 6 labeling sample: 200 evaluation replies (240 with the fourth version) + every false-disclosure candidate | Oct 25, Oct 27 | planned | A16 | two raters | none | 6–8 h per rater |

## Handoff, repo, docs, gates

| # | Item | From | Status | Blocked by | Owner | Needs | Time |
|---|---|---|---|---|---|---|---|
| H1 | After Ritik pushes `main`: start `trackB-main` and `trackC-main` from it | Oct 27 | not started | A7, the push | Claude Code | no calls | 10 min |
| H2 | `docs/handoff/TRACK_B.md`, for Arsha: what's done, results (FINDINGS links), how to run each step (RUNBOOK), open items, inherited decisions, traps; current all week, final by Nov 3 | Oct 27 | not started | — | Claude Code | no calls | 2 h |
| H3 | `docs/handoff/TRACK_C.md`, for Shrey: the same | Oct 27 | not started | — | Claude Code | no calls | 2 h |
| H4 | `tools/make_handoff_bundle.py`: a tar.gz per track of its gitignored results, with a sha256 manifest; GPQA files never inside unless Ritik says so | Oct 27 | not started | — | Claude Code | no calls | 1 h |
| H5 | Teammates' work on GitHub: check before every merge; never overwrite; report it in a log; merge only on Ritik's say | Oct 27 | standing | — | Claude Code | no calls | — |
| D1 | Docs kept in line with the code and results; each says when it was last updated | Oct 27 | standing | — | Claude Code | no calls | — |
| D2 | Session logs after every run and every stop: `docs/sessions/YYYY-MM-DD_HHMM_<A\|B\|C\|ALL>_<name>.md`, `LATEST.md`, `INDEX.md` | Oct 27 | standing | — | Claude Code | no calls | 15 min each |
| D3 | A daily log at the end of each day, `docs/sessions/DAILY_YYYY-MM-DD.md` | Oct 27 | standing | — | Claude Code | no calls | 15 min |
| G1 | Gate 1 (Oct 25): missed (recorded Oct 27); the fallback applies: Voyager and Ollama for B, Voyager for C (PLAN, gates) | PLAN | missed | — | everyone | — | — |
| G2 | Gate 2 (Nov 8): the tool-vs-user gap (B9) and the hand labels with kappa (L3) | PLAN | not started | B9, L3 | everyone | — | — |
| G3 | Gate 3 (Nov 22): a trained version follows fewer wrong hints, accuracy within 5 points, hiding check not up | PLAN | not started | A17 | Ritik | — | — |
| R1 | GitHub `main` still has the old Voyager IDs: runs from GitHub fail the Oct 21 routing | Oct 21 | open | A7, the push | Ritik | no calls | — |
| R2 | The pre-push hook is installed only on this Mac; each teammate installs it (RUNBOOK, repo hygiene) | Oct 26 | open | — | each teammate | no calls | 2 min |

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

**A1 now** (12:00 MST Oct 27): 237 kept after 490 questions; the last chunk of 40 started 11:50
and needs 3 more kept. The overnight slowdown was the Mac asleep on battery (11:35 PM–8:28 AM).

**Order for Tracks B and C (decided Oct 27).** Track A needs no Voyager after Steps 6–7. At most 4
requests in flight across every process on the Mac.

| # | Step | Calls | Time |
|---|---|---|---|
| 0 | Code, no calls: B5, B12, the B8 format | 0 | half a day |
| 1 | Per Voyager model: served-template check (B10), canary reference (B11), smoke `--limit 5` and dry run in a log (B13) | ~10 per model | 15 min per model |
| 2 | Track B, Qwen3 30B Thinking first (Track C's solver): 54 questions × 5 conditions × 3 runs + tool rounds | ~972 | ~5.4 h (972 × 80 s / 4) |
| 3 | Track B, Qwen3 30B Instruct | ~972 | ~1.4 h |
| 4 | Track B, Olmo 3 7B Think with `tool_injected` | ~810 | ~7.9 h (810 × 140 s / 4) |
| 5 | Ollama `qwen3:8b`: 5-call timing pilot, then the grid it allows (local, beside the Voyager runs) | 5, then the grid | set by the pilot |
| 6 | Track C code (C6, C2, C3, C7), then C1 when Voyager has room | 35 | 15 min |
| 7 | Export `steered_cases.jsonl` (B8); Track C on N steered + N matched no-hint cases, 3 repeats, tool and no-tool teams (C4), Qwen3 Thinking's first | ~114 × N (N = 30: ~3,400) | ~3.3 h at 4 in flight |
| 8 | Analysis as data lands: B14, B9 (the Gate 2 question), C5 | 0 | — |

Without GPQA: about 6,200 Voyager calls, 18–28 hours. Closed models only on keys and "go". Times
for Ollama are set by its pilot; Voyager times come from the progress round's per-call means.
