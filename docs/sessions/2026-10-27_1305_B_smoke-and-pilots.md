# Session log: Track B smoke tests and pilots; Track A Steps 11–13 code (2026-10-27 13:05 MST)

Project: CSE 598 Group 10, "Do thinking modes make chain-of-thought more honest?" A wrong hint
(from the user or from a tool) is added to multiple-choice questions; we measure whether the answer
follows it and whether the model says so. Track A explains and fixes it in Olmo 3 7B Think; Track B
tests more models; Track C tests a solver-reviewer-checker agent team. Models run on ASU Voyager (an
API), Ollama (local) and ASU Sol (GPUs). Until Nov 3 Ritik runs all three tracks (code by Claude
Code); then Track B goes to Arsha and Track C to Shrey.

## 1. Header

- **Time:** 2026-10-27 13:05 MST (Arizona) = 20:05 UTC. Week 11 of 16.
- **Branch:** `trackA-nosol` (unpushed past `origin/main`'s commit `15e0047`).
- **Commits:** before `1db1fa0`; after `9256acc`, 11 commits: `5aa2742` plan for Oct 27–Nov 3 (PLAN,
  TODO, docs); `e3e5134` scoped, backed-up history rewrite and summary exporter; `fb9b5c1`, `d2210cf`,
  `2c818cf` Track B runner; `d5641d1` Qwen3 canaries and template check; `f52a5ef` Step 11
  `train.py`; `f2a9c4f` Step 12 `generate.py`; `f85f100` Step 13 `eval.py`; `1608665` Sol QoS
  checks; `9256acc` Sol jobs for Steps 11–13. This log is committed on top. Nothing pushed.
- **Tests:** 326 of 326 pass (CPU only, no network; 283 at the start of the day).
- **Steps 6–7 run** (Voyager, pid 12290, untouched): 237 kept after 490 questions; the last chunk of
  40 is at 110 of 120 no-hint runs (13:01), then Step 7 targets for that chunk's kept questions.
  Expected end about 2:30–3:30 PM MST.

## 2. What ran

| Command | Where | Calls | Duration | Failures |
|---|---|---|---|---|
| `progress/make_canary.py` for `qwen3-30b-a3b-thinking-2507` and `-instruct-2507` | Mac → Voyager | 2 echo calls + 2 catalog checks | 1 min | none |
| `progress/voyager_template_check.py` (3 models × 5 conditions, max_tokens 1) | Mac → Voyager | 15 + 5 preflight canaries | 10 min | Qwen3 local counts wrong (a bug, §5) |
| the same, Qwen3 models only, after the fix | Mac → Voyager | 10 | 5 min | none |
| `run_trackB.py --run --model M --limit 5`, M = Qwen3 Thinking, Qwen3 Instruct, Olmo 3 7B Think | Mac → Voyager | 15 jobs, 16 calls | 12:38–12:59 | none, no retries |
| `ollama pull qwen3:8b` | Mac | download ~5 GB | ~10 min | none |
| Ollama timing pilot: `--model qwen3:8b --thinking on --limit 3`, then `off --limit 2` | Mac (local) | 5 | 12:41–12:50 | none |
| **Ollama full grid** `run_trackB.py --run --model qwen3:8b` (under `caffeinate -i`) | Mac (local) | 1,615 jobs, ~1,939 calls | started 12:51; est. ~51 h | running (6 rows at 13:01) |
| `pytest -q` (several times) | Mac | 0 | ~2 min each | 0 at the end |

All Voyager calls held one of the 4 request slots shared with the Steps 6–7 run (preflight and
canary calls too, from today). No Sol job, no paid call, no GPQA.

## 3. Results

**Smoke tests (1 question each: they test the plumbing; no rate can be read from them).**

| Model | Conditions run | Answered | Seconds per call | Served as |
|---|---|---|---|---|
| Qwen3 30B Thinking | none, user, pasted, tool_real, system | 5 of 5 | 25–103 | qwen3-30b-a3b-thinking-2507 |
| Qwen3 30B Instruct | the same | 5 of 5 | 0.2–18 | qwen3-30b-a3b-instruct-2507 |
| Olmo 3 7B Think (pinned format) | none, user, pasted, tool_injected (declared), system | 5 of 5 | 184–737 (slots shared) | olmo3-7b-think |

Qwen3 Thinking did not call the tool in its one tool_real run; Qwen3 Instruct called it and ended on
the hint letter.

**Served chat templates** (server prompt tokens against our rendering with the model's own Hugging
Face template; Olmo against our pinned rendering on /v1/completions):

| Model | none | user | pasted | tool | system |
|---|---|---|---|---|---|
| Qwen3 30B Thinking (template @144afc2) | 293 = 293 | 309 = 309 | 326 = 326 | 476 vs 477 | 320 = 320 |
| Qwen3 30B Instruct (template @0d7cf23) | 291 = 291 | 307 = 307 | 324 = 324 | 474 vs 475 | 318 = 318 |
| Olmo 3 7B Think (pinned) | 358 = 358 | 374 = 374 | 391 = 391 | 535 = 535 (injected) | 336 = 336 |

The −1 on Qwen3's tool condition disappears when the tool spec's JSON keys are sorted (474 = 474):
Voyager (vLLM) serializes the tool declaration with sorted keys. Same template, same content.

**Identity canaries:** new references for Qwen3 Thinking (293 prompt tokens) and Instruct (291), each
the no-hint pilot-0 prompt in the model's own template; both passed on the next call; Olmo's passed
twice (529 positions, max diff 0.0).

**Ollama pilot** (qwen3:8b on this Mac, one at a time, while other runs shared the machine): thinking
on 99, 189, 182 s (2,308–4,153 output tokens); off 45, 23 s (524–1,023 tokens). The full grid:
~42 h on + ~9 h off, done about Oct 29 evening; on and off are interleaved by repeat, so a partial
run stays balanced.

**Dry runs for the Voyager runs (start after the history rewrite):**

| Model | Jobs | Calls | Hours at 4 in flight |
|---|---|---|---|
| Qwen3 30B Thinking (first: Track C's solver) | 810 | 972 | 4.3 |
| Qwen3 30B Instruct | 810 | 972 | 1.0 (the per-call time is a guess) |
| Olmo 3 7B Think | 810 | 810 | 8.2 |

54 questions (24 puzzles, 30 MMLU-Pro) × 5 conditions × 3 runs per model; GPQA not exported (waits
for Ritik). FINDINGS: no entry changed status.

## 4. Files

Tracked (code, configs, docs; sizes in bytes):
- Track B: `cot-disclosure/progress/run_trackB.py` (20,182), `progress/voyager_template_check.py`
  (7,296), `progress/make_canary.py`, `providers/ollama.py`, `configs/trackB.yaml`,
  `configs/canary/qwen3-30b-a3b-thinking-2507.json` (39,480), `configs/canary/qwen3-30b-a3b-instruct-2507.json`
  (38,951), `tests/test_trackB.py`.
- Track A: `finetune/train.py` (21,253), `finetune/generate.py` (12,117), `finetune/eval.py`
  (21,714), `finetune/gpu/eval_job.py` (11,320), `finetune/continuation.py` (render hook);
  `finetune/gpu/sol/`: `accounts.conf`, `guard.sh`, `submit.sh`, `run.sh`, `env.sh`,
  `timing.sbatch`, `vllm_check.sbatch`, `train.sbatch`, `eval.sbatch`, `setup_vllm.sh`,
  `setup_vllm.sbatch`; tests `test_trackA_train.py`, `test_trackA_generate.py`, `test_trackA_eval.py`,
  `test_trackA_gpu_kit.py`.
- Repo: `tools/untrack_produced.py`, `tools/export_summaries.py`, `tests/test_repo_hygiene.py`.
- Docs: `docs/PLAN.md`, `docs/TODO.md`, `docs/OVERVIEW.md`, `README.md`, `cot-disclosure/finetune/README.md`,
  `cot-disclosure/finetune/gpu/README.md`, this log, `LATEST.md`, `INDEX.md`.

Gitignored (produced data):
- `results/trackB/voyager.jsonl.gz` (105,456), `voyager_runs.jsonl` (10,181), `ollama.jsonl.gz`
  (19,389 and growing), `ollama_runs.jsonl` (3,778), `template_check.jsonl` (10,756).
- `results/trackA/gpu/original/step9_followup_sol.json` (121,764; Sol's original, sha256 `6282a790…`).
- `results/voyager_canary.jsonl` (21,578; still tracked until the rewrite, then untracked).

Nothing copied to or from Sol.

## 5. Problems and fixes

- **Template check counted 2 tokens** for Qwen3: under transformers 5, `apply_chat_template(...,
  tokenize=True)` returns an encoding object and `len()` counted its 2 keys. Fixed; the 10 Qwen3
  calls rerun; the wrong rows stay in the append-only log (the latest rows per model are the right ones).
- **The tool condition's −1** on Qwen3 traced to vLLM's sorted JSON keys (§3); recorded in the code.
- **Training labels:** `<think>` is not a special token, so tokenizing prompt + reply together merged
  it with the reply's first word. `train.py` now tokenizes the prompt and the reply apart, as at
  generation.
- **Ollama timeout:** the adapter waited 600 s; a 16,000-token local reply can take longer. Now 3,600 s.
- **Preflight and canary calls** ran outside the 4 request slots; they now hold one.
- **Local `main` carries one produced file:** commit `280bd12` adds one numbers-only row to
  `results/voyager_canary.jsonl`; the pre-push check flags it on `main` and on `trackA-nosol`. The plan
  for `main` is decision 1 below; until then the rewrite is scoped to the 53 commits unique to
  `trackA-nosol` (`untrack_produced.py --not-in main`; dry run clean).
- **A test needs gitignored inputs:** `test_inputs_manifest_matches_the_committed_files` checks the
  bytes of produced files that a fresh clone doesn't have. Not changed yet; noted for the handoff
  docs.

## 6. For review

- Smoke tests are 1 question per model: no claim rests on them.
- **Olmo's token cap in Track B differs from Qwen3's:** 32,768 for prompt + reply over all rounds
  (Track A's rule) vs 16,000 reply tokens for the chat models. Records keep completion tokens, so the
  analysis can also apply a common 16,000 cut. Decision 2.
- Qwen3 Thinking skipped the tool in its one tool_real run. If that rate is low, tool_real delivers
  few hints for that model; the tool-call rate is reported next to every tool_real number.
- Per-call times: Qwen3 Instruct's (15 s) comes from 1 progress-round call; Ollama's from 5 calls on
  a shared Mac. Hours are estimates.
- The Ollama grid started right after its pilot; its dry run is first recorded here (the "dry run in
  a log first" rule was written for Voyager models).
- **Untested on Sol:** the `squeue` fields `submit.sh` parses, vLLM 0.31.0 (its prompt_embeds format,
  Olmo 3 support), and the separate vLLM environment. S2 is the check. If `squeue` prints GPUs in
  another form, `submit.sh` counts 1 GPU per job (all our jobs use 1).
- **My choices, not in the brief:** accumulation 8, warmup 3% then linear decay, loss chunks of 1,024
  positions, a resume checkpoint every 25 optimizer steps (`train.py`). LoRA is merged into the base
  before serving for every LoRA version (PLAN said merged for LoRA only; now also for LoRA + tags), so
  no system needs vLLM's prompt embeddings together with LoRA.
- The fourth version's layers 15, 19, 23 are 0-based layer indices (full-attention layers at 3, 7,
  …, 31), the same numbering as Steps 9–10.
- Phase 6 sample: 40 per system over 6 strata (3 channels × followed / resisted) gives quotas
  7, 7, 7, 7, 6, 6.

## 7. Decisions needed from me

1. **Plan for local `main`** (2 unpushed commits; `280bd12` adds 1 numbers-only canary row). (a)
   Rewrite those 2 commits too: `821c583` comes out identical, `280bd12` loses only the row; `main`
   and `voyager-ids-oct21` move; nothing on GitHub changes; the pre-push check then passes on both
   branches. (b) Leave `main` alone and allow that one row through the pre-push check. **Recommend
   (a).** Until you answer, only `trackA-nosol`'s 53 unique commits are rewritten; (a) later is one
   more run of the same tool.
2. **Olmo's cap in Track B:** (a) 32,768 total, as in Track A, with a 16,000 cut also reported; (b)
   16,000 reply tokens, like the chat models. **Recommend (a).**
3. **Ollama grid:** running in full (~51 h, done ~Oct 29 evening). (a) Keep; (b) cut to MMLU-Pro
   only (~half). **Recommend (a).**
4. **First Sol jobs** once the data is assembled and rsynced: `setup_vllm` (no GPU), then S1 timing
   (`--estimate 0.5`, limit 1:00) and S2 vLLM check (`--estimate 1`, limit 1:30), together 150
   GPU-minutes. Needs your "go".

## 8. Open work (top 10 of docs/TODO.md)

| # | Item | Status |
|---|---|---|
| A1 | Steps 6–7 to 240 kept | in progress: 237 kept, last chunk |
| A4 | Assemble train / validation, final counts | runs when A1 ends (decided) |
| A6 | History rewrite with backup and sha256 list | ready (`--not-in main`); waits on A1 |
| A7 | Merge into local `main`; push commands | after A6 |
| B7 | Track B Voyager runs (Qwen3 Thinking, Instruct, Olmo) | smoke passed; start after A6 |
| B4 | Ollama qwen3:8b grid | running |
| A13 | S1 timing + S2 vLLM check on Sol | code done; needs data, setup_vllm, "go" |
| C6, C2, C3, C7 | Track C code: append-only log, no-tool team, second reviewer, input file | not started (next) |
| L1, L2 | 10 replacement label rows; labeling kit | not started |
| H2–H4 | Handoff docs and data bundles | not started |

## 9. Next

**Ritik:** nothing to run now. Answer decisions 1–4 when convenient.

**Claude Code, after this log:** Track C code (C6, C2, C3, C7). When Steps 6–7 end:
1. Assemble, export the summaries, write the final-count log.
2. Pause the Ollama grid; back up (`git bundle` to `~/backup-before-rewrite.bundle`, sha256 list
   beside it); rewrite (`untrack_produced.py --not-in main --run --backup ~/backup-before-rewrite.bundle`,
   or without `--not-in` if decision 1 is (a)); tests; restart the grid.
3. Start the Qwen3 30B Thinking Voyager run in the background; merge into local `main`; give the
   push commands.
