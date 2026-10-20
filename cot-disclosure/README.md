# cot-disclosure: the code

Everything that calls the models, saves the runs, computes the numbers and runs the
demo. What the project found so far is in [`../docs/OVERVIEW.md`](../docs/OVERVIEW.md);
what comes next is in [`../docs/PLAN.md`](../docs/PLAN.md).

## Setup

**Python.** The model client, parser, experiments and demo app use only the standard
library (Python 3.9+, macOS or Linux: `progress/common.py` uses `fcntl`). The analysis,
tests and Track A need a few packages:

```bash
python3 -m venv ../.venv && ../.venv/bin/pip install -r requirements.txt
../.venv/bin/playwright install chromium     # only for the screenshot tools
```

**Keys** go in `cot-disclosure/.env`, which is gitignored and never printed:

```bash
cp .env.example .env
```

| Variable | What it's for |
|---|---|
| `RC_LLM_API_KEY` | ASU Voyager (https://voyager.rc.asu.edu → LLM Access → Create Key) |
| `RC_LLM_BASE_URL` | Defaults to `https://openai.rc.asu.edu/v1` |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `XAI_API_KEY` | Track B closed models. Must be real provider keys: the adapters refuse a key equal to the Voyager key. |
| `OPENAI_CAP_USD`, `ANTHROPIC_CAP_USD`, `XAI_CAP_USD` | Spending caps; default $5 each |

Only public benchmark questions go to outside providers.

## Commands

Run from the repo root unless noted. Everything that calls a model is resumable and
appends to `results/`. Nothing overwrites a saved run.

**Recompute numbers (no API calls):**

```bash
.venv/bin/python cot-disclosure/progress/analyze_progress.py      # docs/progress/RESULTS_SUMMARY.json, figures F1-F9, LABEL_QUEUE.csv
cd cot-disclosure && ../.venv/bin/python -m pytest -q tests        # 61 tests, no network
```

**The demo app:**

```bash
python3 cot-disclosure/ui/app.py                                   # http://127.0.0.1:8765; see ui/README.md
```

**The tracks:**

```bash
.venv/bin/python cot-disclosure/progress/run_trackB.py --dry-run   # Track B: calls and cost per provider
.venv/bin/python cot-disclosure/progress/run_trackB.py --run --only-provider voyager --limit 1
.venv/bin/python cot-disclosure/agents/run_team.py --replay        # Track C on saved data, no calls
.venv/bin/python cot-disclosure/agents/run_team.py --live --n 5    # Track C live on Voyager
.venv/bin/python cot-disclosure/finetune/build_dataset.py          # Track A train / held-out records
cd cot-disclosure && ../.venv/bin/python -m providers.budget --status   # spend so far, per provider
```

**The progress-round experiments** (already run; rerunning needs a Voyager key):

```bash
cd cot-disclosure
python experiments.py run --workers 20        # Test 1: 24 puzzles x 6 models (1,056 calls)
python analyze.py                             # Test 1 numbers -> results/summary.json
../.venv/bin/python progress/timing_run.py
../.venv/bin/python progress/mmlu_pro_probe.py select      # Test 2: pick 30 MMLU-Pro items
../.venv/bin/python progress/mmlu_pro_probe.py nocue       # Test 2: no-hint runs
../.venv/bin/python progress/mmlu_pro_probe.py cued        # Test 2: user and tool hints
../.venv/bin/python progress/reviewer_demo.py all          # Experiment A
../.venv/bin/python progress/truncation_sweep.py
../.venv/bin/python progress/check_tool_support.py         # real tool calls on Voyager
```

Replies are cached in `cache/` (local, not in git), keyed by the exact request, so a
rerun with the same seed reuses them. Delete `cache/` for fresh calls.

## Files

| Path | What it does |
|---|---|
| `client.py` | Calls Voyager: streaming, splits private reasoning from the final answer, caches replies, retries transport errors, passes tool calls; `chat_live` streams piece by piece to the UI |
| `tasks.py` | Generates puzzles with one right answer (ball swaps, race order) |
| `parse.py` | Finds the answer letter (A–J): `Answer: (X)`, `\boxed{X}`, "the answer is X", bold, trailing `(X)`; `parse_final` for the reviewer's `FINAL: X` |
| `detect.py` | Keyword pre-sort: `cue` (user hint), `cue_tool` (tool hint), uncertainty, self-correction, acknowledgment |
| `audit.py` | Shows each keyword match in its sentence, to check the keywords by eye |
| `experiments.py`, `analyze.py` | Test 1 grid and prompts (`build_prompt` rebuilds any pilot prompt exactly); its numbers |
| `run.py` | The Oct 1–2 difficulty ladder and first pilot |
| `progress/common.py` | One record format for every call, the fair 4-request limiter (`slot`), run IDs, Wilson intervals |
| `progress/mmlu_pro_probe.py` | Test 2 (Experiment B) |
| `progress/reviewer_demo.py` | Experiment A (reviewer arms and guard) |
| `progress/truncation_sweep.py`, `timing_run.py` | Cut-off leak test; timing and catalog check |
| `progress/analyze_progress.py` | Every reported number → `docs/progress/RESULTS_SUMMARY.json`, figures, label queue |
| `progress/check_tool_support.py` | Real tool calls on Voyager |
| `progress/run_trackB.py` | Track B runner with dry run and budget guard (`configs/trackB.yaml`) |
| `progress/build_evidence_viewer.py`, `take_screenshots.py`, `extract_slides.py`, `make_bundle.py` | Presentation tooling |
| `providers/` | One interface over Voyager, Ollama, OpenAI, Anthropic, xAI (`base.py`); `budget.py` caps and logs spend |
| `tools/answer_key.py` | Hint conditions (`none`, `user`, `tool_pasted`, `tool_real`, `system`) and the `lookup_answer_key` tool |
| `agents/` | Track C: `solver.py`, `reviewer.py`, `checker.py`, `run_team.py` |
| `finetune/` | Track A: `build_dataset.py`, `source_tags.py` ([README](finetune/README.md)) |
| `configs/` | `models.yaml` (provider facts), `prices.yaml`, `trackB.yaml` |
| `ui/` | The demo app ([README](ui/README.md)) |
| `data/progress/mmlupro_30.jsonl` | The 30 Test 2 questions |
| `results/` | Every saved run (map in `docs/OVERVIEW.md` §8) |

## Voyager facts that matter for new code

- **Stream every request.** Replies over about 100 s fail with Cloudflare 524 otherwise,
  and a non-streamed reply cut off at the token limit puts the private reasoning in the
  visible answer.
- **A cut-off reply** (`finish_reason == "length"`) is no answer. Never parse a letter
  from it.
- **Private reasoning arrives in the `reasoning` field** (formerly `reasoning_content`).
  `client.py` reads both.
- **Thinking can't be switched off** (`enable_thinking: false` is ignored), and
  `reasoning_effort` does nothing. "Think very briefly" in the prompt does shorten it.
- **Seeds repeat runs only partly** (not at all on the 32B endpoints), so save every
  prompt and reply. `progress/common.make_record` does.
- **Keep at most 4 requests in flight** (`progress/common.slot`).
- **Tool calls work in the OpenAI chat format** on Qwen3 30B and Olmo 3 7B Instruct.
  Olmo 3 7B Think doesn't make valid calls.

## Limits

- `detect.py` matches keywords only. Hand labels (`docs/progress/LABELING_GUIDE.md`)
  decide what a reply actually says.
- The puzzles are generated (uncontaminated but narrow). MMLU-Pro is public and may be in
  the models' training data.
