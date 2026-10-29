# Session log: Sol fixes, set A's lines, C13 pre-registered (2026-10-29 16:45 MST)

Project: CSE 598 Group 10. Track A evaluates its trained versions of Olmo 3 7B Think on Sol (batch 3)
and runs set A's look-inside jobs; Track B runs Qwen3-8B on Sol; Track C tests a solver/reviewer/checker
team against a wrong tool result. This log answers Ritik's nine items of 15:10: the push, the olmo
environment, the vLLM check, per-part server logs, set A's and Qwen3-8B's lines, C13 (pre-registered
here, before it runs), F23's wording, and the Sol commands in order.

## 1. Header

- **Time:** Oct 29, 15:13–16:45. **Tracks:** A, B, C. **By:** Ritik.
- **Branch:** `trackA-nosol`.
  - Pushed at 15:36: `ef6afd8` (set A, C11, C12) and `7931b79` (the vLLM fix); main and `trackA-nosol`
    = `7931b79`.
  - Local, waiting for Ritik's "push": `28d68a4` (the import race and the import check), `ad7ce06`
    (per-part server logs; per-job model directories), the C13 commit, and this log's.
- **Tests:** 509 pass (CPU, no network).
- **Sol at 15:10 (Ritik):**
  - base 1/2 66932942 and 2/2 66932944: running on vLLM.
  - prompt_only 66932945/46: queued.
  - lora 66932947/48: held by Ritik.
  - vllm_check 66920320 and trackb_qwen3-8b 66934413: failed.
- **Nothing was submitted from this session.**

## 2. Item 1: the vLLM fix committed, then pushed with ef6afd8

- **`7931b79`:** the parallel session's four files, unchanged.
  - The server starts with `VLLM_USE_FLASHINFER_SAMPLER=0`. FlashInfer's sampler needed nvcc in
    vLLM's warm-up, which was the root cause of 66878660 and 66879362.
  - The check's HF reference frees its model.
  - `Server` takes Track B's own command.
  - Qwen3-8B's tokenizer loads at its pinned revision.
  - 479 tests passed before the commit.
- **Usual rules, all checked:**
  - Author and committer are Ritik; no co-author or tool lines in the messages; no added line names a
    tool.
  - main → `trackA-nosol` is a fast-forward; `prepush_check.py` found nothing produced, GPQA or over
    50 MB.
  - Pushed: `git push origin main trackA-nosol` (c8d0586..7931b79).

## 3. Item 2: the olmo environment is fine; the failure was a thread race in the runner

**Answer: envs/olmo is not broken, and nothing leaks into the runner from envs/olmo-vllm.**
66934413 failed on a Python 3.11 import race in Track B's runner.

- **Not broken:**
  - Your login-node test imports transformers 5.18.0 and AutoTokenizer.
  - The two base parts and the check's driver (66928369: `"prefix": "/scratch/ragarw68/envs/olmo"`,
    transformers 5.18.0, peft 0.21.2) run on it.
  - The traceback's transformers is envs/olmo's own.
- **No leak:**
  - The runner starts with envs/olmo's Python (`sys.executable`). Its environment is `os.environ`
    plus `TRACKB_VLLM_URL` and `TRACKB_CHAT_TEMPLATE_SHA256`.
  - The only PYTHONPATH change in the code, the faulthandler `sitecustomize`, goes to the
    `vllm serve --help=all` child alone, as a copy of the environment (`vllm_options.run_help`).
  - The vLLM server gets its own copy too.
  - `/etc/python` on PYTHONPATH is Sol's own.
- **The cause:**
  - The runner's 48 threads (`sol_in_flight`) all reached `prompt_tokens`'
    `from transformers import AutoTokenizer` at once, in a fresh process (the vLLM path runs the
    runner as a subprocess).
  - transformers replaces itself in `sys.modules` with a lazy module at the end of its `__init__`.
  - On Python 3.11, a thread that waits on another thread's first import of it gets back the
    original module object, which has no AutoTokenizer. The error is the exact message:
    `cannot import name 'AutoTokenizer' from 'transformers' (.../transformers/__init__.py)`.
- **Reproduced on the Mac**, with Sol's versions (transformers 5.18.0, tokenizers 0.23.2,
  huggingface_hub 1.33.0) and threads arriving 1–10 ms apart:

  | Python | without the lock | with the lock |
  |---|---|---|
  | 3.11 (Sol's) | 47 of 48 threads fail | 0 of 48 |
  | 3.14 (the test suite's) | 0 of 48 | – |

  - That is why no test saw it.
  - In 66932943 the same race was there. The first thread's OSError (the unpinned tokenizer) surfaced
    first, so it never showed.
- **Fix (`28d68a4`):**
  - `run_trackB.prompt_tokens` loads and counts under a lock: one thread imports and loads, and the
    others wait.
  - A test fails without the lock: 16 threads made 16 loads; with it, 1.
- **The startup import check** (`finetune/gpu/import_check.py`), run first by `sol/run.sh` in every
  job:
  - torch, transformers with AutoTokenizer, tokenizers and peft, each from the job's own environment.
  - vllm with vLLM's Python, in vLLM jobs only: vllm_check, c13, and eval or trackb_qwen8b with
    `--engine vllm`.
  - A package, or a sys.path entry, from another environment fails the check.
  - It names the `sitecustomize` loaded and prints the versions.
  - A failure stops the job before its step.
- **Installs:** only `setup_env.sh` installs into envs/olmo (and `setup_vllm.sh` into olmo-vllm); no
  job or script does (grep of the code).
- **Set A's Step 9, Step 10 and B1 forced: yes, they can run safely now.**
  - They are Hugging Face jobs in envs/olmo, the environment and code path of Oct 26–27's Steps 8–10.
  - None of them imports transformers in threads: Steps 9 and 10 have none, and B1 forced has none.
    Only B1's generation mode uses threads, after loading in the main thread.
  - The import check comes with the pull. They don't depend on it.

## 4. Item 3: vllm_check, stage by stage

- **66920320 failed at the tag path's server start.** It got past the plain server and the HF
  comparison.
  - The root cause is your grep's line 39: `Free memory on device cuda:0 (64.74/79.28 GiB) on
    startup is less than desired GPU memory utilization (0.92, 72.94 GiB)`.
  - The driver holds no model before the comparison, so the 14.5 GiB was its model: SourceTaggedLM
    kept the bf16 weights in PyTorch's cache past `del model`.
  - It was not a LoRA or tag incompatibility.
  - Fixed in `7931b79` (freed before `empty_cache`).
- **66928369** (resubmitted at 10:45 with the fix; the log you tailed) passed every stage:
  - the plain server against HF base: 48, 11, 48 tokens agree (bf16 noise);
  - the merged synthetic LoRA plus the folded tag, served with tagged prompt embeddings, against
    `SourceTaggedLM(LoRA)`: 48, 48, 48;
  - `pass: true`.
- **LoRA works on vLLM.**
  - lora and lora_attn3 are served as merged checkpoints (no `--enable-lora`).
  - The merge, `merge_lora`, is the step 66928369 verified inside the tagged version: a synthetic
    adapter on every LoRA target, B not zero.
  - Serving a plain checkpoint is the verified plain path.
- **Release 66932947/48 after the pull (step 1 below), not before.**
  - Both parts merge into `models/lora_merged` when they start. Before `ad7ce06` they shared one
    `lora_merged.tmp`, and two parts starting together could write the same shard files.
  - Now each job builds in its own `models/lora_merged.tmp-<job id>` and renames it into place. The
    second job keeps the first one's.
  - `fold_model` (tags, lora_tags) wrote straight into the served directory. It now builds the same
    way, and keeps a folded model of the same base and tags (sha256) as it is.
- **The tag path is verified,** so tags, lora_tags and lora_attn3 run on vLLM. No version needs HF
  generation.
  - B1 and B2 (provenance) are Hugging Face only, and their comparison is alpha = 1 on the same code
    path (`provenance_job.py` always adds alpha = 1).
  - All six systems are compared on one stack.
- **Watch:** the tag versions send every prompt as embeddings, 4,096 bf16 values a token. A
  20,000-token second round is ~160 MB a request. Check the first tag part's tokens/s.

## 5. Item 4: one server log per eval part (`ad7ce06`)

- `eval/vllm_<system>_p<k>of<n>.log`, named like the part's record files. A whole-system job keeps
  `vllm_<system>.log`.
- The running base parts still write the shared `vllm_base.log`. Parts that start after the pull use
  their own.

## 6. Items 5 and 6: the lines

In section 9, in order:
- set A: Step 10 first, then Step 9 and B1 forced;
- Qwen3-8B: resubmit after the pull, on vLLM, `--estimate 3` (limit 4:00, resumable).

## 7. Item 7: C13, a third and fourth reviewer family (pre-registered here, before it runs)

**Models** (checked on the Hub on Oct 29: license, gating, revision, architecture; vLLM 0.31.0's
supported-models list):

| Served name | Repository @ revision | Family | Size | License, gating |
|---|---|---|---|---|
| granite-4.1-30b | ibm-granite/granite-4.1-30b @ 4fae6278 | IBM Granite | 28.9B dense (GraniteForCausalLM) | Apache 2.0, not gated |
| mistral-small-3.2-24b | mistralai/Mistral-Small-3.2-24B-Instruct-2506 @ 95a6d26c | Mistral | 24.0B dense (Mistral3) | Apache 2.0, not gated |

- **Why these two:**
  - Both are non-thinking instruct models of 24–30B, like C4's pair (Olmo 3.1 32B Instruct defers;
    Qwen3 30B Instruct doesn't).
  - So size and thinking are held near C4's, and only the family changes.
- **Left out:**
  - Gemma 3 and Llama: gated.
  - Gemma 4 31B: Apache 2.0 and not gated, but it reasons and leaves an empty thought block. It is the
    reserve.
  - GLM-4-32B: its 32,768-token limit leaves too little room for the cache.
  - Phi-4: 16k context.
  - Yi-1.5-34B: too large for one A100 at 32k.
  - gpt-oss-20b and Nemotron 3 Nano: reasoning models.
- **Fit on one A100 80GB:**
  - Granite: 53.8 GiB of weights, ~15 GiB of cache at 0.92, so ~60k tokens.
  - Mistral: ~55 GB per its card.
  - `--max-model-len 32768` for both.
- **Mistral** runs in its own format, as its card serves it: `--tokenizer-mode mistral
  --config-format mistral --load-format mistral`, consolidated weights only, and no images
  (`--limit-mm-per-prompt '{"image":0}'`). Every option is in the committed 0.31.0 list.

**Design:**
- Reviewer only, on C4's 159 saved tool-team cases (53 items; 75 bad and 84 good lookups):
  `run_team.py --rereview team_c4 --no-check-tool --bad-first`.
- Variants: answer_only, plus_private, plus_tool_log.
- C4's prompt; C11's settings: temperature 0.6, seed = repeat, 16,000-token cap.
- Each model gets its own log, `team_c13_granite` and `team_c13_mistral`, so each resumes on its own.
- Requests carry what C4's Voyager calls carried and nothing else (messages, max_tokens, temperature,
  seed). Other sampling settings are each model's `generation_config.json` defaults, saved with the
  download.
- Mistral's card suggests temperature 0.15. It stays at 0.6, so the comparison with C4 and C11 holds.

**Question 1: does the plus_private drop appear?** Per model:
- **Main comparison:** plus_private minus answer_only, on correcting a wrong answer after a bad
  lookup (25 items, 73 reviews). Paired by item, 95% bootstrap clustered by item. The same for
  plus_tool_log, secondary.
- **Rule** (C11's):
  - **defers:** the upper bound is below −20 points;
  - **doesn't defer:** the interval includes 0 or lies above −20;
  - **unclear:** otherwise.

**Question 2: does family still predict it?** Six reviewers, four families. So far: both Olmo defer,
both Qwen don't. Fixed now:
- **Olmo-specific:** neither new model defers. Deference is seen in one family of four, and family
  still predicts it.
- **Not one family's trait:** at least one new model defers. Family still sorts the two families seen
  twice, but it doesn't predict whether a new family defers.
- **Unclear results** count for neither reading and are reported as unclear.
- **Limits:**
  - One model per new family, so agreement within the new families can't be tested.
  - One solver's cases (C4's).
  - 25 items for the main comparison, as in C11 (−42 and +1 there).

**Also reported, no decision:**
- keeping a right answer on good lookups (28 items), each variant minus answer_only;
- no-letter counts;
- by kind × set (descriptive; H23 needs the redacted variants and isn't tested here).

**Dry run (Mac, no calls):**

```
$ ../.venv/bin/python agents/run_team.py --rereview team_c4 --no-check-tool --bad-first --reviewer-model sol_chat:granite-4.1-30b --reviewer-max-tokens 16000 --cases results/trackB/steered_cases.jsonl --log team_c13_granite --workers 16 --dry-run
159 saved tool-team cases of team_c4 (53 items; 75 bad and 84 good lookups), 159 to run: ~477 calls (1 reviewer models x 3 variants: answer_only, plus_private, plus_tool_log); no solver or checker calls. C4's reviewer prompt, unchanged; bad lookups first (75 cases)
$ (the same for sol_chat:mistral-small-3.2-24b, --log team_c13_mistral): ~477 calls
$ ../.venv/bin/python agents/sol_c13.py --dry-run
per model: 477 reviews, ~1.29M tokens (~0.24M generated; C11's Olmo 3 7B Instruct on the same cases), 0.18-0.37 h at 2,000-4,000 prompt and 300-600 generated tokens/s (assumed). Job: the option check (5-15 min), 2 server starts (5-15 min each) and the reviews: 0.6-1.5 A100 hours
```

**GPU estimate:**
- 0.6–1.5 A100 hours: `--estimate 1.5`, a 2:00 limit, 120 GPU-minutes.
- The rates are assumptions; the job's log measures them.
- The download (`get_c13`, no GPU) is about 106 GB into `/scratch/ragarw68/hf`: Granite 57.7 GB,
  Mistral 48.0 GB.

**Code (the C13 commit):**
- `agents/sol_c13.py`: the download job, the GPU job and the dry run.
- `providers/sol_chat.py`.
- `run_team.py --workers`: 16 against the job's own server; Voyager keeps 4.
- `run.sh` steps `c13` and `get_c13`; `c13.sbatch` and `get_c13.sbatch`.
- `submit.sh`: C13 may wait only for get_c13, Step 10, Step 9 and B1 forced.
- The vLLM option check covers C13's two server commands.
- 9 new CPU tests.

## 8. Item 8: F23's split by set is a hypothesis

- In FINDINGS F23, "the restoration is all on the matched puzzles" is now a description of these
  cases.
- **Hypothesis H23, to test:** on puzzles the reviewer can re-solve once the letter is hidden; on hard
  items the solver's reasoning persuades it.
  - Set and difficulty go together here. The reviewer alone corrects 38 of 43 puzzle cases and 15 of
    24 steered MMLU-Pro ones, and 8 steered items can't separate the two.
  - **Test:** split by the reviewer's own answer-only success on cases not used here, not by set.
- TODO's C12 row says the same.

## 9. The Sol commands, in order

```bash
# 0. Mac: the four local commits go up on Ritik's "push" (git push origin main trackA-nosol, after the
#    pre-push and metadata checks).

# 1. Sol, the clone: the fixes. The checkout holds the parallel session's rsync copies (Oct 29 10:44 and
#    12:42): modified tracked files, and three files new in ef6afd8 (the C11/C12 summaries, the 10:55 log)
#    that a plain pull would refuse to overwrite. All of them are in the commits; the stash keeps them anyway.
cd /scratch/ragarw68/cse598-cot-faithfulness
git status --short                                  # expect only those rsync copies
git stash push --include-untracked -m "rsync copies, Oct 29" && git pull --ff-only && git log -1 --oneline
source cot-disclosure/finetune/gpu/sol/env.sh
"$TRACKA_PY" cot-disclosure/finetune/gpu/import_check.py --vllm "$TRACKA_VLLM_PY"   # both environments' versions
# (the running base parts loaded their code at start; the pull doesn't touch them)

# 2. Mac, from cot-disclosure/: set A's inputs (skip if they're already on Sol)
rsync -av results/trackA/setA/{runs.jsonl.gz,items.jsonl,takeover_runs.jsonl,cases.jsonl} \
      ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/trackA/setA/

# 3. Sol: set A, Step 10 first (then move it up), Step 9, B1 forced
A=/scratch/ragarw68/trackA/setA
S=cot-disclosure/finetune/gpu/sol/submit.sh
$S step10 --estimate 2 -- --runs-from $A/runs.jsonl.gz --cases-from $A/cases.jsonl --items-from $A/items.jsonl --out $A
scontrol top <the step10 job>
$S step9 --estimate 0.75 -- --runs-from $A/runs.jsonl.gz --items-from $A/items.jsonl --step3-from $A/takeover_runs.jsonl --out $A
$S provenance_forced --estimate 0.5 -- --cases-from $A/cases.jsonl --runs-from $A/runs.jsonl.gz --items-from $A/items.jsonl

# 4. Sol: Qwen3-8B again on vLLM (the race fixed; resumable, limit 4:00)
$S trackb_qwen8b --estimate 3 -- --engine vllm

# 5. Sol: lora 1/2 and 2/2 (LoRA on vLLM verified; each part now merges in its own directory)
ls -d /scratch/ragarw68/trackA/models/* 2>/dev/null   # a leftover *.tmp* is a killed job's: delete it when no job runs
scontrol release 66932947 66932948

# The queue holds 10 jobs and runs 2. Steps 3-4 bring it to 10 (base x2, prompt_only x2, lora x2, set A x3,
# Qwen3-8B); submit each line below when a job has ended.

# 6. C13: inputs (Mac, from cot-disclosure/), the snapshots (no GPU), then the job after set A
rsync -av results/trackC/team_c4.jsonl \
      ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/cot-disclosure/results/trackC/
rsync -av results/trackB/steered_cases.jsonl \
      ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/cot-disclosure/results/trackB/
$S get_c13                                          # limit 3:00; check its .out says both match the Hub
$S c13 --estimate 1.5 --dependency=afterany:<step10>:<step9>:<provenance_forced>

# 7. The rest of batch 3 on vLLM (tags, lora_tags, lora_attn3): the planner prints their lines, leaving out
#    what is saved or queued
"$TRACKA_PY" cot-disclosure/finetune/gpu/plan_eval.py --engine vllm --vllm-check 66928369 \
    --train lora=66759753,tags=66759769,lora_tags=66862721,lora_attn3=66862726

# 8. Back to the Mac (cot-disclosure/), as jobs end; each rsync is one Duo push
S2=ragarw68@login.sol.rc.asu.edu
rsync -av $S2:/scratch/ragarw68/trackA/setA/step10/step10_patching.json results/trackA/setA/
../.venv/bin/python finetune/look/patching.py --handoff results/trackA/setA/step10_patching.json \
    --handoff-out results/trackA/setA/step10_handoff.json
rsync -av $S2:/scratch/ragarw68/trackA/setA/step9/ results/trackA/setA/step9/
rsync -av $S2:/scratch/ragarw68/trackA/provenance_forced/provenance_forced.json results/trackA/setA/
rsync -av "$S2:/scratch/ragarw68/trackA/eval/eval_*_runs.jsonl" "$S2:/scratch/ragarw68/trackA/eval/eval_jobs.jsonl" results/trackA/gpu/eval/
rsync -av $S2:/scratch/ragarw68/cse598-cot-faithfulness/cot-disclosure/results/trackB/sol_vllm_{runs,flags}.jsonl results/trackB/
rsync -av "$S2:/scratch/ragarw68/cse598-cot-faithfulness/cot-disclosure/results/trackC/team_c13_*.jsonl" results/trackC/
```

## 10. For review

1. **C13's pair:**
   - IBM Granite 4.1 30B and Mistral Small 3.2 24B are the closest ungated, non-thinking 24–30B
     instruct models from two new families.
   - Gemma 4 31B is the reserve if you'd rather have Google; it would need its thinking off and the
     empty thought block stripped.
2. **Mistral runs at temperature 0.6, not its card's 0.15,** so it matches C4 and C11.
3. **The queue limit (10 jobs) sets the order after step 4.** C13 and the six tag and lora_attn3 parts
   go in as jobs end.
4. **The race was found by reproducing it, not from Sol's full traceback.** The SSH socket had
   expired. Your one line matches the reproduced message exactly. The import check will show any
   other cause on the first job.

## 11. Next

- **Ritik:** "push"; then section 9's steps 1–5 on Sol, and 6–7 as the queue frees.
- **Mac:**
  - set A's answer against its rule once `step10_patching.json` is back;
  - C13's summary and its readings once both logs are back;
  - the Qwen3-8B rows into Track B's table;
  - batch 3's report as parts finish.
