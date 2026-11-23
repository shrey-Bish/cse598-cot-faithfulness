# How to reproduce

This page says what you can rerun, and on what. The exact command for every step is in
[`docs/RUNBOOK.md`](docs/RUNBOOK.md); the code map is [`cot-disclosure/README.md`](cot-disclosure/README.md); what
each result means is in [`docs/FINDINGS.md`](docs/FINDINGS.md). Results are frozen at the git tag
`results-freeze-2026-11-18`; check it out to get exactly the code and numbers behind the report.

## Two levels

1. **On a laptop, from the tracked summaries.** Recompute the numbers' tables, redraw the figures, rebuild the
   supplement and the demo, and run the tests. No key, no network, no GPU. This is what a reader should do.
2. **From the runs.** Collecting the model runs again needs API access to ASU's Voyager, and, for Track A and part of
   Track B, A100 GPUs on Sol. Teammates and graders do not need this, and the runs are not in the repo (see the end).

## 1. Environment

- **Python 3.9 or newer.** We used 3.14. The model client, parser and demo app use only the standard library; the
  packages below are for the analysis, the tests and the tooling.
- **A virtual environment at the repo root, called `.venv`.** All commands below use `.venv/bin/python`.

```bash
python3 -m venv .venv
.venv/bin/pip install -r cot-disclosure/requirements.txt
```

`requirements.txt` lists pytest, PyYAML, matplotlib, numpy, datasets, python-pptx and playwright (for screenshots; then
`playwright install chromium`), and torch, transformers and peft for Track A. The tests that need torch skip without it.

## 2. Keys

Only level 2 needs a key, and only to call the models.
- Make your own `cot-disclosure/.env` (it is gitignored, so it can never be committed): copy
  `cot-disclosure/.env.example` and fill it in yourself.
- The one that matters is the Voyager key: ASU Voyager (the university's model API), then LLM Access, then Create Key.
  It goes in as `RC_LLM_API_KEY`. The paid providers' lines in `.env.example` are unused; the project made no paid
  calls.
- Never print or share the file. Replies are cached locally in `cot-disclosure/cache/`.

## 3. The order of commands

**On a laptop.** Run these from `cot-disclosure/`, in this order.

```bash
cd cot-disclosure

# 1. The tests: CPU only, no network, no calls
../.venv/bin/python -m pytest -q

# 2. The repo's own checks: every link resolves, the summaries hold numbers only
../.venv/bin/python tools/check_links.py
../.venv/bin/python tools/export_summaries.py --check

# 3. The figures, from results/summaries/
../.venv/bin/python tools/paper_figures.py        # readout_by_layer, reviewer_by_prompt, taught_loss
../.venv/bin/python tools/slide_figures.py        # the slides' figures

# 4. The supplement (checked in a scratch folder; docs/ is untouched)
../.venv/bin/python tools/make_supplement.py --check

# 5. The demo: rebuilds docs/demo/index.html
../.venv/bin/python tools/demo_template/build.py
```

The demo's build writes the same tracked page. If `cot-disclosure/results/demo/bench_runs.json` exists (made by
`tools/demo_template/runs.py` from the local runs), it also writes `results/demo/demo.html`, the version that replays
recorded runs. That file is gitignored.

**From the runs (level 2).** In the order the project took (RUNBOOK sections in brackets):
1. The progress round (Test 1, Test 2, Experiment A): `progress/analyze_progress.py` recomputes it from the saved
   runs (§1).
2. Track B, models and sources, on Voyager: `progress/run_trackB.py` and the experiment scripts `run_b15.py` to
   `run_b24.py` (§18).
3. Track C, review teams: `agents/run_team.py`, then the reading scripts `c15.py` to `c26.py` (§19).
4. Track A, inside Olmo 3 7B Think and the fixes: the dataset and training (§7, §8, §14), looking inside (§4, §6,
   §12, §13).
5. Labels: §15. Summaries out: `tools/export_summaries.py` (§16).

Each finding in FINDINGS names the script that recomputes it.

## 4. What needs a GPU, and what doesn't

| Step | Needs | Where |
|---|---|---|
| Tests, links check, summaries check | nothing | laptop |
| Figures, tables, supplement, the demo's build | the tracked `results/summaries/` | laptop |
| Reading results by their pre-registered rules | saved runs (local) | laptop |
| Track B on the three Voyager models; Track C on Voyager reviewers | a Voyager key | laptop |
| Training (LoRA, tags, consistency training), activation patching, attention scaling, Qwen3-8B, gpt-oss-20b, the open-model families, reviewers on Sol | A100 GPUs | Sol |

Sol is ASU's supercomputer. Its jobs run under a course account and need the ASU VPN to reach the login node. The
Sol kit is in `cot-disclosure/finetune/gpu/` (its [README](cot-disclosure/finetune/gpu/README.md)); RUNBOOK §9, §10 and
§14 give the setup and the commands, and `docs/tracks/SOL_SETUP.md` is for a second user. Code and data go to
`/scratch/$USER/cse598-cot-faithfulness`.

## 5. Why the produced data are not in the repo

- **Size.** The runs, checkpoints and caches are large; a push is refused over 50 MB a file.
- **The rule.** Tracked files hold numbers, ids and paths, never model text. The repo is public, and model replies
  and questions are not ours to publish. So `cot-disclosure/results/track*/`, `results/labels/`, `results/handoff/`,
  `results/demo/`, `finetune/data/`, `cache/` and `logs/` are gitignored, and a pre-push hook refuses them.
- **What is tracked instead:** `cot-disclosure/results/summaries/`, numbers only (`tools/export_summaries.py` refuses
  a file with text over 200 characters), plus the progress round's runs as its evidence.
- **Checking a copy.** The team passes the produced data around as three bundles. Their sha256 sums are in
  [`docs/submission/BUNDLES.sha256`](docs/submission/BUNDLES.sha256).
