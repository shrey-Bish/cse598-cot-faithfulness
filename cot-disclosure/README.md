# cot-disclosure: the code map

Last updated: 2026-11-03. Everything that calls the models, saves the runs, computes the numbers and makes the
figures. What the project found is in [`../docs/FINDINGS.md`](../docs/FINDINGS.md), what comes next in
[`../docs/PLAN.md`](../docs/PLAN.md), and the exact command for each step in [`../docs/RUNBOOK.md`](../docs/RUNBOOK.md).
Folders and module names are fixed: tests, Sol job scripts, RUNBOOK lines and teammates' commands use these paths.

## Setup

```bash
python3 -m venv ../.venv && ../.venv/bin/pip install -r requirements.txt
cp .env.example .env                          # your own keys; gitignored, never printed
../.venv/bin/python -m pytest -q               # all tests: CPU only, no network
```

`.env` holds `RC_LLM_API_KEY` (ASU Voyager: https://voyager.rc.asu.edu → LLM Access → Create Key) and
`RC_LLM_BASE_URL` (default `https://openai.rc.asu.edu/v1`). The paid providers' keys (`OPENAI_API_KEY`,
`ANTHROPIC_API_KEY`, `XAI_API_KEY`) and their caps (`*_CAP_USD`, default $5 each) are unused: the project makes no
paid calls. Replies are cached in `cache/` (local, not in git), keyed by the exact request, so a rerun reuses them.
Produced data stays off GitHub: `results/trackA/`, `results/trackB/`, `results/trackC/`, `results/labels/` and
`finetune/data/` are gitignored; numbers-only summaries go in `results/summaries/` (`tools/export_summaries.py`).

## The map

Track: A = inside one model and the fix; B = more models and channels; C = agents; all = shared. Files marked
*historical* ran once and are kept as the evidence for the results named; nothing current depends on rerunning them.

| Folder | Track | What it holds | Main entry points |
|---|---|---|---|
| `./` (top level) | all | The Voyager client (streaming, cache, the identity canary and the other guards), the answer parser, the keyword pre-sort. *Historical, evidence for the progress round (Test 1; its figures F1–F9):* `tasks.py` (the puzzles), `experiments.py`, `analyze.py`, `run.py` (the Oct 1–2 ladder), `audit.py` | `client.py`, `parse.py`, `detect.py` |
| `progress/` | B, all | `common.py` (one record format, the 4-request limiter, run IDs, Wilson intervals) and `guard.py` (Ritik's power rules, restarts after sleep), used by every track. Track B's runner, report and its experiments B15, B16, B17; Sol's Track B (Qwen3-8B, gpt-oss-20b); the served-template check and canary references. *Historical, evidence for the progress round (Test 2, Experiment A; its figures F1–F9):* `mmlu_pro_probe.py` (Test 2), `reviewer_demo.py` (Experiment A), `truncation_sweep.py`, `timing_run.py`, `check_tool_support.py`, `rescore.py`, `analyze_progress.py` (every progress-round number → `docs/labeling/RESULTS_SUMMARY.json`, the label queue), and the presentation tools `build_evidence_viewer.py`, `take_screenshots.py`, `extract_slides.py`, `make_bundle.py` | `run_trackB.py`, `trackB_report.py`, `run_b15.py`, `run_b16.py`, `run_b17.py`, `sol_trackB.py`, `sol_b17.py`, `guard.py` |
| `providers/` | B | One interface over Voyager, our own vLLM or Hugging Face on Sol, Ollama, OpenAI, Anthropic and xAI (`base.py`); `config.py` reads `configs/models.yaml`; `budget.py` caps spend (unused: no paid calls) | `voyager.py`, `sol_vllm.py`, `sol_hf.py` |
| `agents/` | C | The pipeline: `solver.py` (a thinking model with the `lookup_answer_key` tool, or a retrieval tool), `reviewer.py`, `checker.py`, `run_team.py` (teams, reviewer models, handoff notes); one reading script per experiment, `c15.py`–`c20.py`, `c25.py`, `c26.py` (pre-registered readings, no calls); `fresh_items.py` (C15's items); `sol_c13.py` (reviewers on Sol). *Historical:* `disagreement.py` (C14, exploratory) | `run_team.py`, then `c19.py`, `c25.py`, `c20.py`, `c26.py` (TRACK_C §5a) |
| `finetune/` | A | The pinned Olmo format (`olmo_format.py`), continuation, the dataset (Steps 5–7), source tags, training, generation, evaluation (Steps 11–13), Gate 3's table, provenance-scaled attention (B1). *Historical, evidence for Steps 1–2b:* `voyager_capabilities.py`, `voyager_ids_check.py`, `template_revisions.py`, `show_spans.py`, `smoke_2b.py`, `base_format.py`; *for Steps 5–7:* `length_audit.py`, `make_pool.py`, `run_nohint.py`, `make_targets.py`, `run_steps67.py`, `check_examples.py`; *for the training plan:* `gpu_estimate.py`, `move_to_gz.py` | `build_dataset.py`, `train.py`, `generate.py`, `eval.py`, `gate3.py`, `provenance.py`, `setA.py` |
| `finetune/look/` | A | Looking inside: the takeover curve (Step 3), the deletion test (Step 4), attention to the hint (Step 9), activation patching (Step 10), the window check; the same on Qwen3-8B (`qwen8b_mech.py`) and on the trained model (`a18.py`); figures. *Historical, evidence for F4–F6 (Step 3):* `before_takeover.py`, `plot_takeover.py` | `takeover.py`, `patching.py`, `attn_to_hint.py`, `qwen8b_mech.py`, `a18.py`, `plot_figures.py` |
| `finetune/gpu/` | A (B, C on Sol) | The Sol kit: what every GPU job shares (`kit.py`), job plans, the evaluation job, B1's jobs, the checks (import, checkpoint, vLLM options); `sol/`: one `.sbatch` per job kind, `run.sh` (the dispatcher), `submit.sh` (the only way to submit; accounts and estimates checked). *Historical:* `smoke.py`, `step8_verdict.py`, `plan_training.py` (Steps 8–11) | `sol/submit.sh <kind>`, `provenance_job.py`, `plan_eval.py`, `eval_job.py` ([its README](finetune/gpu/README.md)) |
| `tools/` | all | The hint conditions and the tool (`answer_key.py`); labels (`label_kit.py`: queues, sheets, Cohen's kappa, the settling sheet, the fresh batch; `rater_packets.py`); the generated docs (`make_gantt.py`, `make_supplement.py`, `paper_figures.py`, `slide_figures.py`, `trackb_final.py`, `export_summaries.py`); repo checks (`check_links.py`, `prepush_check.py`, `path_check.py`: the path allowlist as a pre-commit hook); per-track data bundles (`make_handoff_bundle.py`). *Historical:* `untrack_produced.py` (the history rewrite decided Oct 26) | `make_gantt.py`, `make_supplement.py`, `paper_figures.py`, `label_kit.py`, `prepush_check.py` |
| `configs/` | all | `models.yaml` (provider facts, Voyager IDs), `trackB.yaml` (Track B's design), `canary/` (identity references), `prices.yaml`, `path_allowlist.txt` (each listed branch's paths: Track C's) | read by the code |
| `data/progress/` | all | `mmlupro_30.jsonl`: the 30 evaluation questions; `mmlupro_e2.jsonl`: E2, 120 fresh ones (Nov 3, `finetune/make_e2.py`, sha256 in its pre-registration). Nothing is ever chosen on them | read by the code |
| `results/` | all | `summaries/` is tracked and numbers-only; everything else is produced data (gitignored) | `tools/export_summaries.py --check` |
| `tests/` | all | CPU tests for every module above (no network, no calls) | `../.venv/bin/python -m pytest -q` |
| `ui/` | all | *Historical, the progress round's demo* (its figures F1–F9): six examples and the charts page from saved runs; its guide is [archive/progress-round/ui_demo_README.md](../archive/progress-round/ui_demo_README.md) | `python3 ui/app.py` (http://127.0.0.1:8765) |

Track A's design is in [`docs/tracks/TRACK_A.md`](../docs/tracks/TRACK_A.md), B1/B2's in
[`docs/tracks/TRACK_A_FIX.md`](../docs/tracks/TRACK_A_FIX.md), Track B's and Track C's handoffs in
[`docs/tracks/`](../docs/tracks/), and each track owner's own records in [`docs/trackB/`](../docs/trackB/START_HERE.md) and
[`docs/trackC/`](../docs/trackC/START_HERE.md).

## Voyager facts that matter for new code

- **Stream every request.** Replies over about 100 s fail with Cloudflare 524 otherwise,
  and a non-streamed reply cut off at the token limit puts the private reasoning in the
  visible answer.
- **A cut-off reply** (`finish_reason == "length"`) is no answer. Never parse a letter
  from it.
- **Private reasoning arrives in the `reasoning` field** (formerly `reasoning_content`).
  `client.py` reads both.
- **Model IDs changed on Oct 21: `reasoning_effort` now chooses the model.**
  - Each instruct/thinking pair is one family ID (`olmo3-7b`, `olmo3-32b`,
    `qwen3-30b-a3b`). `none` (the default!) gives the instruct checkpoint;
    `low`/`medium`/`high` give the thinking one.
  - These are still two separately trained models, not thinking switched on and off in
    one model. `enable_thinking` is still ignored. "Think very briefly" in the prompt still
    shortens the reasoning.
  - Keep using our six names (`olmo3-7b-think`, …). `client.py` maps them through
    `configs/models.yaml` (`voyager_ids`) on every request and never sends an old ID.
- **The client guards every Voyager run:**
  - a thinking model can't be sent with effort `none`
  - the first request checks `/v1/models` and stops if the family ID is gone, or no
    longer serves our model at that effort
  - an identity canary runs at the start and hourly: an echo call on a short reference
    text (`configs/canary/<name>.json`, under 2,048 tokens). The run stops unless the
    top tokens match and the max log-prob difference is under 0.01.
  - a canary that gets no reply is not a verdict: new requests pause, the canary is
    retried every 2 minutes, and the run resumes when it passes. It halts only on an
    identity mismatch, or after 30 minutes unreachable. A request that fails in transit
    also makes the canary due at once.
  - a request that never got a whole reply (no token for 10 minutes, a dropped
    connection, a stream cut short, a gateway 5xx) is `not_run` (retried later), never
    "no answer"
  - every record saves `requested_model_id`, `reasoning_effort` and `served_model`
- **Seeds repeat runs only partly** (not at all on the 32B endpoints), so save every
  prompt and reply. `progress/common.make_record` does.
- **Keep at most 4 requests in flight** (`progress/common.slot`).
- **Tool calls work in the OpenAI chat format** on Qwen3 30B and Olmo 3 7B Instruct.
  Olmo 3 7B Think doesn't make valid calls itself. A tool turn we insert (an assistant
  call + a `tool` message) does reach it (checked Oct 21).
- **`olmo3-7b-think` is served with the Olmo 3 Instruct chat template** (checked Oct 21).
  - The template has its own default system prompt and no `<think>` in the generation
    prompt.
  - Tool messages become an `environment` turn.
  - With `continue_final_message` the server drops a leading `<think>` from the assistant
    content.
  - Track A renders Olmo prompts itself (`finetune/olmo_format.py`) and uses
    `/v1/completions`.
- **`prompt_logprobs` is refused on streamed requests;** `echo: true` + `logprobs` gives
  prompt-token log-probabilities instead (Oct 21).

## Limits

- `detect.py` matches keywords only. Hand labels (`docs/labeling/LABELING_GUIDE.md`)
  decide what a reply actually says.
- The puzzles are generated (uncontaminated but narrow). MMLU-Pro is public and may be in
  the models' training data.
