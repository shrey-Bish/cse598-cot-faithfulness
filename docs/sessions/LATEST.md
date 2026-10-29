# Session log: Hugging Face generation for Sol's batch 3 and Qwen3-8B (2026-10-29 08:10 MST)

Project: CSE 598 Group 10. Track A trains Olmo 3 7B Think on Sol to stop hiding hint-following and
evaluates the versions (batch 3); Track B adds Qwen3-8B on Sol. On the night of Oct 28–29 both vLLM
jobs failed to start. This log covers what replaced vLLM, why each job would have failed, the cost,
and the morning's Sol commands (in the Oct 29 daily).

## 1. Header

- **Time:** Oct 29, 01:00–02:05, then 07:36–08:10 MST. **Track:** A and B. **By:** Ritik.
- **Branch:** `trackA-nosol`. Three earlier commits and this one are local; the repo is public, and
  the push waits for Ritik's "push".
- **Input:** Ritik's Sol message (night of Oct 28): requests 1–4 below.
- **Tests:** 476 pass.
- **In flight:** Voyager, under the guard since 07:58: set A (140 of 204 runs at 08:00), then C11,
  then C12. Nothing on Sol.

## 2. What happened on Sol

- **vllm_check 66878660** failed after 24:26, and **trackb_qwen3-8b 66879362** after 13:39. Both
  ended with "RuntimeError: Engine core initialization failed. See root cause above".
- **The traceback:** `_initialize_kv_caches` → `compile_or_warm_up_model` → `gpu_worker.py:876`
  `warmup_kernels(` → torch's `decorate_context`. The copied lines stop there, so the root-cause line
  is not known.
  - `vllm_base.log` line 4 (`--disable-log-requests`) is from Oct 27. The log is appended to across
    jobs.
  - The weights had loaded in both jobs. Olmo runs through vLLM's Transformers backend, and Qwen3-8B
    natively, so the cause is more likely the node or the environment than either model.
- **The 8 eval parts were removed.** Nothing is queued.

## 3. Request 1: the root cause

- **Not found.** The daily's command 1 prints both tracebacks from `warmup_kernels` to the end.
- **The next failure names its cause itself:** `generate.log_tail` now reads only this start's part
  of a server log (each start writes a `=== server start` line). It lists the start's error lines
  first, without EngineCore prefixes and generic lines ("See root cause above"), then the last 30
  lines.
- **Test:** `test_a_server_log_names_this_starts_root_cause`.

## 4. Request 2: Hugging Face generation for batch 3

**`finetune/hf_engine.py`** (new; 10 CPU tests on a tiny Olmo 3 with the real tokenizer):
- **Load:** the base snapshot in bf16, the adapter merged in memory.
- **Tag versions:** `TagTable` widens the input embedding table to 4 blocks (model, system, user,
  tool); row = embedding + tag. Prompt ids are shifted by the block, so tags work as plain token ids.
  The logits equal training's `SourceTaggedLM.embed` inputs on CPU (atol 1e-5).
- **Engines:**
  - transformers 5.18's continuous batching (the same version on Sol) after a GPU self-check: its
    greedy tokens against plain `generate` on 2 prompts, at least 8 of 16 alike from the first;
  - else static batches (B1's `Batched`).
- **Sampling, as vLLM's would have been:**
  - temperature 0.6; top_p, top_k, min_p and repetition_penalty only if the snapshot's
    `generation_config.json` sets them, never Hugging Face's default top_k = 50;
  - Olmo 3 7B Think's at d97e442 sets top_p 0.95, checked against the pinned blob hash
    (d456a34e) on Oct 29;
  - end ids: the tokenizer's, the config's and `<|im_end|>`; special tokens skipped in the text;
  - stop strings as vLLM's (text up to and including the stop).
- **Seeds:** per-run seeds can't be kept inside a batch. The job's generator is seeded from system,
  part and job id.

**`eval_job.py --engine hf`** (now the default; `--engine vllm` is still available):
- `kit.check_inputs` always runs; the vLLM preflight only for vLLM.
- Each record and the `eval_jobs.jsonl` row name the engine, why it was chosen, runs in flight and
  the sampling.

**Concurrent writers:** two jobs appending to one file on Sol's shared /scratch is unsafe. Each part
now writes `eval_<system>_p<k>of<n>.jsonl.gz` and `…_runs.jsonl`. Resume and the report read every
file of a system; B1's report groups by system across part files.

**Four fixes; each would have broken or stalled a job:**

| Problem | Effect on Sol | Fix and test |
|---|---|---|
| A static batch that raised anything but out-of-memory killed the worker thread | every waiting run hangs until the time limit (seen on CPU: the test hung) | each run of a failed batch gets an error reply (retried later); three failing batches in a row break the engine and end the job. `test_a_static_batch_that_raises_…` |
| Continuous batching switches the model to paged attention; a start that failed partway left it there | the static fallback fails on every batch ("paged\|sdpa was called without a paged attention cache") | `make` restores the attention before the fallback. `test_a_failed_start_leaves_the_static_fallback_its_own_attention` (fails without the fix) |
| `step8`, `step9`, `step10` and `smoke` job scripts didn't pass their arguments | set A's Step 9/10 would have run on Test 2's inputs, silently | `"$@"` added; a test checks every job script |
| Parts were every N-th question | parts 0.7–5.4 h apart: 17 parts per system | parts are every N-th run (`eval.jobs`): 10 equal parts of ~6 h |

**`plan_eval.py`:**
- `--engine hf` is the default; it needs no vLLM check, and the tag versions run on it.
- **Step 2b's lengths as a range:** 92 of 350 runs stopped at Voyager's 16,000-token cap and were
  never continued. They count as recorded (low), as the 94 continued runs' mean, 23,547 (mid), and as
  the 32,768 cap less the prompt (high).
- **Parts:** the fewest N whose every part's high end × 1.3 fits 8 h. Each part gets its own
  estimate.
- **Made again at any time:**
  - it leaves out saved runs (every part file);
  - it leaves out parts already queued (sacct's SubmitLine); a system with queued parts keeps their N;
  - it uses the rate measured by finished jobs on the same engine.
- 8 tests.

**The rate: an estimate, not measured.**
- Paged SDPA gathers each run's keys and values into a new tensor, then copies it again
  (`.contiguous()`) before attention: about 5 passes a step.
- A run holds ~3.0 GB of keys and values at Olmo's 10,522-token average context per generated
  token: 8 full layers × 16 KiB a token, plus 24 sliding layers × 16 KiB × 4,096.
- 16 in flight move ~254 GB a step with the weights: ~160 ms at ~1.6 TB/s, ~100 tokens/s. More in
  flight doesn't help (ceiling ~110).
- The prior is **70–120 tokens/s**.

| | low | mid | high |
|---|---|---|---|
| tokens per system (M) | 11.7 | 13.4 | 15.0 |
| GPU h per system | 27.1 | 38.4 | 59.8 |
| GPU h, six systems | 163 | 230 | 359 |

At two jobs at once that is 3.5–7.5 days. vLLM was planned at 500–1,500 tokens/s (15–50 GPU h for
six systems). B1's generation (P2) uses the same static path; its 11–23 GPU h (PROVENANCE.md) is
from an 80–160 tokens/s guess and is likely low.

## 5. Request 3: Qwen3-8B the same way

- **`providers/sol_hf.py`** (new) and `sol_trackB.py --engine hf` (the default). It renders the
  snapshot's chat template as vLLM's chat endpoint hands messages to it:
  - tool-call arguments as a mapping;
  - `enable_thinking` only when the request sets it.
- **It parses the reply as the server's parsers did:**
  - `--reasoning-parser qwen3`: `<think>` split out;
  - `--tool-call-parser hermes`: `<tool_call>` blocks, only when tools were declared.
- **A reply cut inside its reasoning** is all private reasoning (finish "length", no answer).
- **The provider name stays `sol_vllm`,** so run ids, records, flags and the report are unchanged.
  Each record names its engine.
- **Tests:** 8, with the Qwen3-8B tokenizer from the local cache. The template rendering equals
  `apply_chat_template` with vLLM's message form; a whole Track B run goes through a fake engine.
- **Size:**
  - 1,620 runs, ~6.7M tokens (Voyager's Qwen3 30B lengths: ~6,200 a run thinking, ~2,000 not).
  - Qwen3's 4 query heads per key head add a copy (`repeat_kv`), so ~120–190 tokens/s: **10–15
    GPU h**, two 8-hour jobs.
  - The first estimate in the job's docstring (5 h) was too low.

## 6. Request 4: the morning commands

They are in [DAILY_2026-10-29.md](DAILY_2026-10-29.md), ahead of the set-A jobs:
- 0, pull;
- 1, vLLM's root cause;
- 2, base 1/10 to 7/10 and Qwen3-8B (two jobs), with the tenth slot left for set A;
- 3, copy-backs;
- 4, set A's Step 10, Step 9 and B1 forced, with `--out $A`, once set A is done.

## 7. Files and tests

- **New:** `finetune/hf_engine.py`, `providers/sol_hf.py`, `tests/test_hf_engine.py`,
  `tests/test_trackB_sol_hf.py`.
- **Changed:**
  - `finetune/eval.py` (every-N-th-run parts, per-part files);
  - `finetune/generate.py` (log_tail);
  - `finetune/gpu/eval_job.py`, `finetune/gpu/provenance_job.py` (static engine, report by system),
    `finetune/gpu/plan_eval.py`;
  - `progress/sol_trackB.py`, `progress/run_trackB.py` (engine field), `providers/sol_vllm.py`;
  - job scripts `step8`, `step9`, `step10`, `smoke`, `trackb_qwen8b`; `run.sh` comment;
  - tests for eval, provenance, the GPU kit, generate, Track B and the planner.
- **Docs:** GPU README (the Hugging Face section, table rows), PLAN (the night, E1–E6, B-Q8, the
  schedule, a risk), TODO (A16, A29, A33, A34, B4), the Track B handoff, the daily.
- **Tests:** the full suite, 476 pass (08:08).

## 8. For review

1. **The speed is an estimate from memory traffic.** Base 1/10's log prints the measured rate every
   25 runs. If it is near 100 tokens/s, batch 3 needs most of the remaining Sol time.
2. **The scope may need a choice** (fewer runs per question, or fewer systems) if vLLM's cause isn't
   a small fix. That is Ritik's call.
3. **The GPU self-check's threshold** (8 of 16 greedy tokens alike) is a judgment. bf16 kernels can
   diverge early and still be correct; a failure only means the static fallback.
4. **Parts by run, not by question:** a part now holds runs of many questions. Analysis merges
   every part, so nothing downstream changes.

## 9. Next

- Ritik: "push" (the pre-push check passes), then the daily's commands 0–2, and command 1's output
  to me.
- Mac: set A finishing on Voyager, then its Sol lines (command 4); C11 and C12 after it under the
  guard.
