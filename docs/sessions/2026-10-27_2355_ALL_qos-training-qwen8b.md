# Session log: the class QoS only, training ready (batch 2), Qwen3-8B moves to Sol, Track B resumed (2026-10-27 23:55 MST)

Project: CSE 598 Group 10, "Do thinking modes make chain-of-thought more honest?" Track A fine-tunes
Olmo 3 7B Think on Sol so it says when a hint changes its answer; Track B measures hint following
across open models; Track C runs a solver/reviewer/checker team. This session acts on Ritik's
messages of 23:30: the setup jobs were refused for their QoS, Track B's Voyager runs resume, Ollama
is replaced by Qwen3-8B on Sol, and training is to start now.

## 1. Header

- **Time:** 2026-10-27 23:55 MST = Oct 28 06:55 UTC.
- **Branch:** `trackA-nosol` at `8125f48` before; one commit after (§5) and this log. Nothing pushed
  since `cbbd936`. **Tests:** 381 pass (CPU only, no network).
- **Running:** Track B on the Mac (§2). On Sol, from Ritik: `setup_vllm.sh` by hand in a CPU salloc;
  vllm_check 66757260 queued.

## 2. What ran

| Command | Where | Calls | Duration | Failures |
|---|---|---|---|---|
| `progress/guard.py`, Voyager only: Qwen3 30B Thinking, then Instruct, then Olmo 3 7B Think (each starts when the one before is done) | Mac (AC, 100%) → Voyager | 663 + 805 + 805 jobs; 4 in flight | started 23:36; ~3.7 h + ~1 h + ~8 h | none so far (20 of 663 at 23:44) |
| `finetune/check_examples.py` (checks (a) and (e)) | Mac | 0 | 13 s | none |
| vLLM 0.31.0's own parser on the 9 server commands (scratch environment from its source release) | Mac, CPU | 0 | minutes | none: all 9 accepted; `qwen3` reasoning and `hermes` tool parsers exist |

Nothing local runs beside the Voyager runs for this project. One process from another project was
running on the Mac at 23:34 (`exp_oneshot_breakages.py` under `caffeinate`); not ours, not touched.

## 3. Results

**(a) Held out stays held out:** 0 of 1,040 training and 0 of 156 validation examples is one of the
30 held-out MMLU-Pro questions, by id or by question text; 0 carries a held-out hint wording (every
wording id and channel is a training one; no held-out wording's own text, the system note or the
`fetch_reference_solution` tool name appears in any prompt or tool list).

**(e) Length:** 0 examples over 32,768 tokens, encoded exactly as training encodes them: the
longest is 31,625 in training and 23,878 in validation. 0 have no reply tokens; the assembly also
dropped 0. Total 7,992,302 training tokens per epoch, 1,301,780 validation.

**Training batch 2 is ready**, but its limits wait for the refit. S1's `timing.jsonl` is on Sol, and
the Mac can't reach Sol: ssh asks for a password. `finetune/gpu/plan_training.py` refits S1 and
prints each version's hours as a range and the four `submit.sh` lines with their limits:
- **The fit:** seconds = c1 × tokens + c2 × tokens², both ≥ 0. A straight line through long and
  short examples gives the negative fixed part S1 printed.
- **The sum:** over the real lengths, 2 epochs, plus a validation pass each epoch at 0.25–0.5 of a
  training step's time.
- **The range:** a bootstrap over the timed examples.
- **The limits:** each is the high end × 1.3, at most 8 h.
- **Where it runs:** on a login node, no GPU.

**The QoS fix:** `setup_vllm`, `setup_env` and `smoke` now ask for `-p public -q class`. smoke had
`-q debug`, which the account doesn't have either. `submit.sh` refuses a partition or QoS that
`accounts.conf` doesn't list for the account, with the reason, before sbatch. "limits not checked"
is gone, and `-q` or `-p` on the command line is refused. A job without a GPU still takes one of the
class QoS's 2 job slots.

**Qwen3-8B on Sol** (replaces the Ollama grid; written now, since the earlier message about it isn't
in this session's history):
- **The job:** one GPU job starts vLLM on `Qwen/Qwen3-8B` (revision `b968826d`) from envs/olmo-vllm
  and runs Track B's runner against it. Thinking on/off goes through `enable_thinking` in each
  request. 48 requests are in flight, and the order is core-first: 540 core runs, then the rest of
  the 1,620.
- **The server's options:** `--reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser
  hermes --max-model-len 33792`. They are checked like Track A's servers.
- **What comes back:** records with text stay on Sol. The numbers-only `sol_vllm_runs.jsonl` and
  `sol_vllm_flags.jsonl` come back, and `trackB_report.py` reads the flags.
- **Estimate: 0.5–1.5 GPU hours** (limit 2:00):
  - Output: ~5,000 tokens a thinking run and ~800 without (Track B's Qwen3 runs so far), about 4.7M
    output tokens in all.
  - Speed: 1,000–3,000 tokens/s across 48 sequences on one A100, plus about 5 minutes to start.
  - Not measured yet.

## 4. Files

- **New:**
  - `finetune/check_examples.py`; its numbers-only outputs `results/summaries/trackA/data/examples_check.json`
    and `examples_lengths.json`.
  - `finetune/gpu/plan_training.py`.
  - `providers/sol_vllm.py`, `progress/sol_trackB.py`, `finetune/gpu/sol/trackb_qwen8b.sbatch`.
  - Tests: `test_check_examples.py`, `test_trackA_plan.py`, `test_trackB_sol.py`.
- **Changed:**
  - `submit.sh` (QoS and partition from `accounts.conf`; `trackb_qwen8b` may wait for `setup_vllm`).
  - `setup_env.sbatch`, `setup_vllm.sbatch`, `smoke.sbatch`; `run.sh` (step `trackb_qwen8b`).
  - `vllm_options.py` (9 commands); `eval_job.Server` (takes a command).
  - `run_trackB.py` (per-provider concurrency, a pinned tokenizer revision); `trackB_report.py`
    (reads `*_flags.jsonl`); `configs/trackB.yaml` (Ollama out, Qwen3-8B on Sol in).
  - `guard.py` (a job can wait for another).
  - Docs: PLAN, TODO, RUNBOOK, OVERVIEW, the GPU README, `handoff/TRACK_B.md`.

## 5. Problems and fixes

- **`setup_vllm` was refused** ("Invalid qos specification"): it asked for `-p lightwork -q public`,
  and submit.sh only printed "limits not checked". Fixed as in §3; 5 new tests.
- **The tests block the network, localhost included** (conftest). The Sol adapter's tests use a fake
  `urlopen`, as the other tests do.
- **build_dataset's own leak check, which gave the manifest's "0 held-out wordings seen in training",
  splits each template at `{`.** For several held-out wordings the longest piece then still contains
  `letter}` or `qid}`, which never appears in filled text, so that check couldn't fire for them. The
  new check splits at the slots and confirms 0. build_dataset itself is unchanged (the data is
  built).

## 6. For review

- **45 targets contain "I think the answer is (":** 40 in training, 5 in validation. It is in the
  model's own reasoning, not in any prompt. It is also how the held-out Turpin wording begins ("I
  think the answer is (X) but I'm curious what you think."), whose second half appears nowhere.
  Training doesn't show the model that wording, but the model's phrase overlaps it.
- **The refit's validation share (0.25–0.5) is an assumption:** a forward pass against forward,
  recomputation and backward. The S1 log doesn't measure it.
- **Qwen3-8B on Sol (vLLM, bf16) is not the same serving as Ollama's qwen3:8b,** which is quantized.
  The 2 Ollama runs at the right context stay apart in the report (by provider) and aren't pooled.
- **vllm_check 66757260 was queued without a dependency.** If it starts before your `setup_vllm.sh`
  has saved the option list, it refuses within seconds (the preflight). It also competes with
  training for the 2 slots.

## 7. Decisions needed from me

1. The Qwen3-8B job on Sol: "go" (`submit.sh trackb_qwen8b --estimate 1.5`, 120 GPU-minutes), and
   the snapshot download in your CPU session first.
2. Batch 2's limits: `plan_training.py` prints them from S1. Submit as printed, or tell me if a
   version's range looks wrong.

## 8. Open work (top 10 of docs/TODO.md)

| # | Item | Status |
|---|---|---|
| A13 | S1 timing (66749357), S2 vLLM check (66757260) | S1 done on Sol (refit on Sol); S2 queued |
| A15 | Batch 2: lora + tags, then lora_tags, lora_attn3 | ready: (a) and (e) pass; lines from `plan_training.py` |
| B7 | Voyager runs, one model after another | running (Qwen3 Thinking 20 of 663 at 23:44) |
| B4 | Qwen3-8B on Sol | code done; waits for "go" |
| C (decision 5) | Track C's second reviewer becomes Olmo 3 32B Instruct | not started |
| ALL | `trackB-main`, `trackC-main` | after the push; next |
| A16 | Evaluate (E1–E5) | after S2 and training |
| L3 | Labels | kit ready |
| H2–H4 | Handoff docs final by Nov 3 | drafts exist |

## 9. Next

**Ritik (Mac, then Sol):**
```bash
git push origin main trackA-nosol         # optional
git ls-files | rsync -av --files-from=- ./ ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/
# Sol, from /scratch/ragarw68/cse598-cot-faithfulness
source cot-disclosure/finetune/gpu/sol/env.sh
"$TRACKA_PY" cot-disclosure/finetune/gpu/plan_training.py /scratch/ragarw68/trackA/timing/timing.jsonl
# -> the table and four submit.sh lines: run the first two, put their job ids into the last two
```
**Arsha and Shrey:** watch the Voyager runs; decision 5's code; the branches; the handoff docs.
