# Runbook: how to run every step

Last updated: 2026-10-27. One page per step: what it does, where it runs, the commands in order,
inputs and outputs, how long it takes, and what to check. Written so anyone in the group can run a
step without asking. Results and their status are in [`FINDINGS.md`](FINDINGS.md); open work in
[`TODO.md`](TODO.md).

**Conventions.** Mac commands run from `cot-disclosure/` with the repo's virtual environment, written
`../.venv/bin/python`. Sol commands run from the clone's root, `/scratch/ragarw68/cse598-cot-faithfulness`.
"Voyager" means ASU's model API, called from the Mac. "Sol" means a GPU job on ASU Sol.

---

## 0. Read this first

**Rules that apply to every step.**
- **Dry run first.** Every script that calls a model has `--dry-run` (calls, time, nothing sent).
  Any run over 50 calls, and any Sol job, needs Ritik's "go".
- **At most 4 Voyager requests in flight** per machine, shared by every process
  (`progress/common.slot`). Long runs resume where they stopped.
- **Keep the Mac awake** during Voyager runs: plugged in, lid open. On battery with the lid closed
  it sleeps and the run stalls (Oct 27 lost 9 hours).
- **Data never goes to GitHub.** Runs, replies, probes, caches and Sol outputs live in gitignored
  folders (`results/trackA/`, `results/trackB/`, `results/trackC/`, `finetune/data/`). Only
  numbers-only summaries in `results/summaries/` are tracked. Nothing from GPQA goes into any tracked
  file or doc. Saved results are never edited; new runs are appended.
- **Keys** live in `cot-disclosure/.env` (gitignored) and are never printed. No keys on Sol.
- **Sol:** every job under `class_cse59888883fall2026` (never `grp_hdavulcu`), submitted through
  `sol/submit.sh`; Python is always `/scratch/ragarw68/envs/olmo/bin/python`, never the system
  `python3`.
- **Reporting:** rates as "X of Y [95% Wilson]"; differences as bootstraps clustered by question;
  under 5 questions, "too few questions" and no interval.

**Setup (Mac, once).**
```bash
cd ~/Documents/Projects/ODL/cse598-cot-faithfulness
python3 -m venv .venv && .venv/bin/pip install -r cot-disclosure/requirements.txt
cp cot-disclosure/.env.example cot-disclosure/.env        # add RC_LLM_API_KEY (Voyager)
cd cot-disclosure && ../.venv/bin/python -m pytest -q      # 283 tests, no network, ~2 min
```
**Check:** every test passes. Then install the pre-push check (page 17).

---

## 1. The progress round: recompute its numbers

- **What:** every progress-round number (Test 1, Test 2, Experiment A) from the saved runs.
- **Where:** Mac, no calls. **Status:** done; rerun after any parser change.
- **Commands** (repo root): `.venv/bin/python cot-disclosure/progress/analyze_progress.py`
- **In → out:** `results/progress*.jsonl` → `docs/progress/RESULTS_SUMMARY.json`, figures F1–F9,
  `docs/progress/LABEL_QUEUE.csv`.
- **Time:** under a minute. **Check:** `git diff docs/progress/` shows no number changes unless you
  meant one.

## 2. Track A, Step 1 and the Voyager ID checks

- **What:** what Voyager's endpoints accept for Olmo 3 7B Think (templates, `<think>`, echo
  log-probs); after Oct 21, that the new model IDs route to the same checkpoint.
- **Where:** Mac → Voyager (8 and 7 calls). **Status:** done Oct 21; rerun only if Voyager changes.
- **Commands:**
  ```bash
  ../.venv/bin/python finetune/voyager_capabilities.py --dry-run
  ../.venv/bin/python finetune/voyager_capabilities.py
  ../.venv/bin/python finetune/voyager_ids_check.py --dry-run
  ../.venv/bin/python finetune/voyager_ids_check.py
  ```
- **Out:** `results/trackA/voyager_capabilities.jsonl.gz`, `voyager_ids_check.jsonl.gz`.
- **Time:** a few minutes. **Check:** the summary lines: the served template, and on the ID check
  max difference ≤ 0.01 on the first 2,047 tokens with mismatches only at near-ties.
- **Automatic from then on:** every Voyager run checks the catalog and runs the identity canary at
  the start and hourly (`client.py`; log in `results/voyager_canary.jsonl`).

## 3. Track A, Step 2b: the base model in the pinned format

- **What:** Olmo 3 7B Think on the 20 hinted Test 2 questions, in its own Think format: no hint × 2,
  user × 1, pasted × 3, inserted × 3, inserted + declared × 3 (240 runs).
- **Where:** Mac → Voyager. **Status:** done Oct 22 (240 of 240).
- **Commands:**
  ```bash
  ../.venv/bin/python finetune/base_format.py --dry-run
  ../.venv/bin/python finetune/base_format.py            # resumable
  ../.venv/bin/python finetune/base_format.py --extend   # continue replies cut off at 16,000 tokens
  ../.venv/bin/python finetune/base_format.py --report
  ```
- **In → out:** `data/progress/mmlupro_30.jsonl`, `results/progress/expB_cued.jsonl` →
  `results/trackA/base_format.jsonl.gz` (+ `base_format_runs.jsonl`).
- **Time:** 68–156 min at 4 in flight, plus continuations. **Check:** `--report`: 240 ok; hint
  following per channel; cut-off runs continued; no `not_run` left.

## 4. Track A, Step 3: takeover curves (early answering)

- **What:** after each sentence of each Step 2b run, close the reasoning, force `Answer: (` and read
  the letters' probabilities; the takeover point and type; the default cases for Steps 4 and 10.
- **Where:** Mac → Voyager, one probe per request. **Status:** done Oct 24 (219 runs, 137,143 probes).
- **Commands:**
  ```bash
  ../.venv/bin/python finetune/look/takeover.py --dry-run
  ../.venv/bin/python finetune/look/takeover.py --pilot          # the shortest followed run only
  ../.venv/bin/python finetune/look/takeover.py --workers 2      # all runs, resumable
  ../.venv/bin/python finetune/look/takeover.py --report
  ../.venv/bin/python finetune/look/takeover.py --cases          # default cases for Steps 4 and 10
  ../.venv/bin/python finetune/look/plot_takeover.py
  ```
  For a trained version on Sol, `--batch N` sends lists to a local vLLM server.
- **Out:** `results/trackA/takeover_probes.jsonl.gz`, `takeover_runs.jsonl`, `takeover_cases.jsonl`,
  `results/trackA/figures/takeover_*.png`.
- **Time:** ~0.5 s per probe; `--probes auto` (grid_tail for followed runs) cuts probes by 62%.
  **Check:** `--report`: every run probed, no gaps; the k = 0 table; the 26 default cases.

## 5. Track A, analyses with no calls (before Step 4, the window)

- **What:** concentration on sure questions and the matched lead onsets (`before_takeover.py`); the
  sliding-window analysis (`window_reach.py`).
- **Where:** Mac, no calls. **Status:** done (F5, F8).
- **Commands:**
  ```bash
  ../.venv/bin/python finetune/look/before_takeover.py --dry-run
  ../.venv/bin/python finetune/look/before_takeover.py
  ../.venv/bin/python finetune/look/window_reach.py
  ```
- **Out:** `results/trackA/before_takeover.jsonl`; `results/summaries/trackA/window_reach.json` + figure.
- **Time:** about a minute each. **Check:** groups under 5 questions print "too few questions".

## 6. Track A, Step 4: the deletion test

- **What:** on the late takeovers on sure questions (19 cases), cut at the takeover, delete the
  reasoning's hint mentions (or as many length-matched sentences), then one forced answer and 3
  continuations per arm; an unedited arm.
- **Where:** Mac → Voyager (209 calls). **Status:** done Oct 24 (F7).
- **Commands:**
  ```bash
  ../.venv/bin/python finetune/look/deletion.py --dry-run
  ../.venv/bin/python finetune/look/deletion.py
  ../.venv/bin/python finetune/look/deletion.py --report
  ```
- **Out:** `results/trackA/deletion_calls.jsonl.gz`, `deletion_runs.jsonl`.
- **Time:** ~25 min typical, up to ~7.5 h if every continuation runs to its cap.
  **Check:** `--report`: hint vs control vs unedited, per question and pooled.

## 7. Track A, Step 5: the dataset rules and the length audit

- **What:** train / validation / held-out records (target rule, correct-hint records, channels,
  held-out wordings with a 0-overlap check); reply lengths by source.
- **Where:** Mac, no calls. **Status:** done; `train` fills from Steps 6–7.
- **Commands:**
  ```bash
  ../.venv/bin/python finetune/build_dataset.py --dry-run
  ../.venv/bin/python finetune/build_dataset.py
  ../.venv/bin/python finetune/length_audit.py
  ```
- **Out:** `finetune/data/{train,validation,heldout}.jsonl`, `manifest.json`;
  `results/trackA/length_audit.jsonl`. **Check:** `manifest.json` reports 0 held-out wordings in
  training.

## 8. Track A, Steps 6–7: training data

- **What:** Step 6: 3 no-hint runs per pool question in the pinned format; a question is kept if all
  3 are answered and correct. Step 7: for each kept question, one wrong hint per channel plus 1–2
  correct hints; a prefill target per record (one opening sentence each for the reasoning and the
  final answer, from 10 paraphrases; the model writes the rest; up to 4 samples; pass = ends on the
  kept answer and doesn't refer to instructions).
- **Where:** Mac → Voyager. **Status:** running since Oct 25 (pid 12290), target 240 kept.
- **Commands:**
  ```bash
  ../.venv/bin/python finetune/make_pool.py --help      # the pool: done Oct 25 (1,600 questions, with --hard)
  ../.venv/bin/python finetune/run_steps67.py --dry-run --kept 240
  nohup ../.venv/bin/python -u finetune/run_steps67.py --kept 240 --checkpoint 100 \
      >> logs/trackA_steps67.log 2>&1 &                                           # resumable
  ../.venv/bin/python finetune/run_steps67.py --report      # the state so far (appends a report row)
  ../.venv/bin/python finetune/run_steps67.py --assemble    # after it ends, with "go": the training set
  ```
- **In → out:** `finetune/data/pool.jsonl` → `results/trackA/nohint_train.jsonl.gz`,
  `target_samples_prefill.jsonl.gz`, `targets_prefill.jsonl.gz` (+ `_runs.jsonl`),
  `results/trackA/steps67_report.jsonl`; `--assemble` → `finetune/data/train_examples.jsonl.gz`,
  `validation_examples.jsonl.gz`, `examples_manifest.json`.
- **Time:** batches of 40 questions, ~2.5 h each while the Mac is awake (~142 s per no-hint run,
  ~139 s per target sample, 4 in flight). **Check:** `tail logs/trackA_steps67.log`; at 100 kept it
  writes a checkpoint report and stops (exit 3) if a rate is off by more than half from the pilot's;
  `--assemble` prints the counts and says whether "neither" targets were dropped (under 10%).

## 9. Sol: access, code, data, results

- **What:** get code and inputs onto Sol, and the summaries back. **Where:** Mac ↔ Sol (ASU VPN on).
- **Code** (tracked files only; until this branch is pushed):
  ```bash
  cd ~/Documents/Projects/ODL/cse598-cot-faithfulness
  git ls-files | rsync -av --files-from=- ./ ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/
  ```
- **Inputs** (gitignored run files the GPU steps read; each step checks their sha256):
  ```bash
  cd cot-disclosure
  rsync -av --files-from=finetune/gpu/sol/inputs.txt ./ \
      ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/cot-disclosure/
  ```
- **Results back** (summaries only, into gitignored `results/trackA/gpu/`): the exact `rsync` lines
  per step are in `finetune/gpu/README.md` ("Results back"). Then
  `../.venv/bin/python tools/export_summaries.py` copies the numbers-only ones into
  `results/summaries/trackA/`.
- **Check** (on Sol): `cd /scratch/ragarw68/cse598-cot-faithfulness/cot-disclosure &&
  /scratch/ragarw68/envs/olmo/bin/python finetune/gpu/kit.py --check-inputs` lists every input as
  matching.

## 10. Sol: environment and smoke test

- **What:** install pinned packages into `/scratch/ragarw68/envs/olmo`; load the model, generate 32
  tokens in the pinned format, check the snapshot is d97e442.
- **Where:** Sol. **Status:** done Oct 26.
- **Commands:** in an interactive GPU session under the course account:
  ```bash
  cd /scratch/ragarw68/cse598-cot-faithfulness
  bash cot-disclosure/finetune/gpu/sol/setup_env.sh        # 5-15 min, once
  cot-disclosure/finetune/gpu/sol/run.sh smoke              # 2-5 min
  ```
  or as batch jobs: `cot-disclosure/finetune/gpu/sol/submit.sh setup_env`, then `… submit.sh smoke`.
- **Out:** `/scratch/ragarw68/trackA/smoke/smoke.json`. **Check:** "matches d97e442", "renders our
  prompt exactly", an A100 and CUDA 13.0, a sensible start of reasoning.

## 11. Track A, Step 8: the checkpoint check

- **What:** a local bf16 and fp32 forward pass over the texts Voyager echoed, against the rule fixed
  on Oct 26; the Instruct checkpoint as the negative control.
- **Where:** Sol (5–10 min), then the Mac. **Status:** done Oct 26 (F9).
- **Commands:**
  ```bash
  cot-disclosure/finetune/gpu/sol/run.sh step8                       # Sol, or submit.sh step8
  ../.venv/bin/python finetune/gpu/step8_verdict.py --sha256sum results/trackA/gpu/weights_sha256.txt   # Mac
  ```
- **Out:** `step8_checkpoint.json` (stays gitignored: it holds token strings);
  `results/summaries/trackA/step8_verdict.json`. **Check:** the decision line and the list of
  positions outside near-ties; the rule is never changed after the result.

## 12. Track A, Step 9: attention to the hint

- **What:** one forward pass per hinted Step 2b run (199); attention mass from the answer position
  and from each reasoning sentence to the hint, its letter and a same-length control span, per layer
  and head. The follow-up re-reads the saved runs (full layers, hint − control, readout heads,
  matched lead onsets with a placebo).
- **Where:** Sol (~15–40 min GPU; the follow-up ~1 min CPU), then the Mac. **Status:** done Oct
  26–27 (F10, F12, F14).
- **Commands:**
  ```bash
  cot-disclosure/finetune/gpu/sol/run.sh step9 --limit 3     # Sol: quick check, ~3 min
  cot-disclosure/finetune/gpu/sol/run.sh step9               # Sol: the rest, then the report
  cot-disclosure/finetune/gpu/sol/run.sh step9 --followup    # Sol: the follow-up, CPU only
  ../.venv/bin/python finetune/look/attn_to_hint.py --followup --from-reduced results/trackA/gpu/step9_reduced.npz   # Mac, no GPU
  ```
- **Out:** `step9_attention.json`, `step9_followup.json`, `step9_aligned.png`, `step9_onsets.png`,
  `step9_reduced.npz`. **Check:** 199 runs, no skipped onsets; groups show their questions; the
  placebo's rise is near 0.

## 13. Track A, Step 10: activation patching

- **What:** on Step 4's 21 cases, cut (i) before the first hint mention and (ii) at the takeover;
  copy one layer's clean output (prompt with the own letter) into the hinted run at the hint, the
  reasoning or the answer position; restoration by layer.
- **Where:** Sol (1–2 h), then the Mac. **Status:** done Oct 26 (F11, F13).
- **Commands:**
  ```bash
  cot-disclosure/finetune/gpu/sol/run.sh step10 --limit 3    # Sol: quick check
  cot-disclosure/finetune/gpu/sol/run.sh step10              # Sol: the rest, then the report
  ../.venv/bin/python finetune/look/patching.py --handoff results/trackA/gpu/step10_patching.json   # Mac
  ```
- **Out:** `step10_patching.json`; `results/summaries/trackA/step10_handoff.json`, the handoff
  figure. **Check:** sanity ok on every cut; cuts with a gap under 0.5 are left out and counted.

## 14. Track A, Steps 11–13: train, generate, evaluate (code not written yet)

- **Status:** not runnable yet (TODO A8–A13). The order, GPU hours and dates are in PLAN (Track A,
  the Gate 3 job plan): S1 timing run and S2 vLLM tag check, then training (S3–S5), then evaluation
  (E1–E5, two jobs at a time, at most 8 h each), then the look-inside rerun (L1).
- **How they will run:** like Steps 8–10: `sol/submit.sh <job>` under the course account, outputs in
  `/scratch/ragarw68/trackA/<step>/`, checkpoints so each job resumes, summaries back by rsync. This
  page gets the exact commands when the code lands.
- **The look-inside rerun** already works on a trained version: Steps 9 and 10 take `--model DIR`,
  `--runs-from` and (Step 10) `--cases-from`, with their own `--out`.

## 15. Labels

- **What:** two raters label what the text says about the hint, for the private reasoning and the
  final answer: no mention / mentions only / rejects the hint / says the hint changed the answer /
  unclear ([`progress/LABELING_GUIDE.md`](progress/LABELING_GUIDE.md)).
- **Where:** anywhere, no calls. **Status:** not started; the kit is TODO L2.
- **Until the kit exists:** each rater copies `docs/progress/LABEL_QUEUE.csv`, hides the
  `keyword_private` and `keyword_final` columns, and fills only their own two columns
  (`rater1_private`, `rater1_final` or `rater2_…`), independently. Skip the 10 rows whose
  `text_status` is "not saved". Then Cohen's kappa per channel; under 0.6, meet, tighten the guide,
  and label a fresh batch.
- **Time:** about 2 minutes per row per rater (91 rows with text: 3–4 hours). **Check:** every row
  has exactly one label per channel from the guide's five.

## 16. Repo hygiene: summaries, history, push

- **Export summaries** (after any run): `../.venv/bin/python tools/export_summaries.py --dry-run`,
  then without `--dry-run`. It refuses a file with question or reply text. `--check` re-checks
  what's tracked.
- **History rewrite** (once, after Steps 6–7, with Ritik's approval): untracks the Track A data on
  the unpushed branches; files on disk don't move.
  ```bash
  python3 tools/untrack_produced.py          # dry run: commits, paths, refs, checks
  python3 tools/untrack_produced.py --run
  ```
- **Push** (with "go"): `git push origin trackA-nosol`; the hook checks it first.

## 17. The pre-push check (each person, once per clone)

```bash
cd ~/path/to/cse598-cot-faithfulness
printf '#!/bin/sh\nexec python3 "$(git rev-parse --show-toplevel)/cot-disclosure/tools/prepush_check.py" "$@"\n' > .git/hooks/pre-push
chmod +x .git/hooks/pre-push
python3 cot-disclosure/tools/prepush_check.py --rev HEAD     # what a push would be checked for
```
It refuses a push that adds anything under a produced-data folder, any file with "gpqa" in its name
(code and docs excepted), or a file over 50 MB.

## 18. Track B: test widely

- **What:** hint following and admission across providers, models, thinking on/off and channels
  (`configs/trackB.yaml`). **Where:** Mac → Voyager, Ollama (local), OpenAI, Anthropic, xAI.
  **Status:** code done; only the Voyager tool check has run (TODO B1–B9). Run it from a branch that
  has the Oct 21 Voyager ID fix (this one, or `main` after the push).
- **Commands** (repo root):
  ```bash
  .venv/bin/python cot-disclosure/progress/run_trackB.py --dry-run                     # calls and cost per provider
  .venv/bin/python cot-disclosure/progress/run_trackB.py --run --only-provider voyager --limit 5
  .venv/bin/python cot-disclosure/progress/run_trackB.py --run --only-provider anthropic --limit 1   # needs a key
  ollama serve & ollama pull qwen3:8b                                                    # before the ollama provider
  cd cot-disclosure && ../.venv/bin/python -m providers.budget --status                  # spend so far
  ```
- **Out:** `results/trackB/` (gitignored); spend in `results/spend_log.jsonl`.
- **Time:** see TODO (notes): about 5.4 h for Qwen3 30B Thinking, 1.4 h for Qwen3 30B Instruct,
  7.9 h for Olmo 3 7B Think on Voyager at 4 in flight. **Check:** the smoke run's rows parse to a
  letter; the budget status stays under each $5 cap; Olmo 3 7B Think must use `tool_injected`
  (TODO B5), since with `tool_real` it never calls the tool.

## 19. Track C: the agent team

- **What:** solver (with the lookup tool) → reviewer → checker; wrong answers shipped, catches,
  false alarms. **Where:** Mac → Voyager. **Status:** replay done; live on 2 items (TODO C1–C6).
- **Commands** (repo root):
  ```bash
  .venv/bin/python cot-disclosure/agents/run_team.py --replay          # saved data, no calls
  cp cot-disclosure/results/scope/team_live.jsonl ~/team_live_backup.jsonl     # it rewrites its log
  .venv/bin/python cot-disclosure/agents/run_team.py --live --n 5      # 35 calls, ~15 min
  ```
- **Out:** `results/scope/team_<mode>.jsonl` and `_summary.json` (tracked today; TODO C6 moves it to
  gitignored `results/trackC/`). **Check:** 5 items, each with solver, reviewer variants and the
  checker's verdict.

## 20. Session logs

- **What:** after every run (a Voyager batch, a Sol job, an analysis that changes a reported number)
  and at every stop, Claude Code writes `docs/sessions/YYYY-MM-DD_HHMM_<name>.md` (Arizona time),
  copies it to `docs/sessions/LATEST.md` and adds a line to `docs/sessions/INDEX.md`.
- **Content:** header (times, branch, commits, tests, the Steps 6–7 run), what ran, results,
  files, problems, points for review, decisions needed, open work, next commands. Numbers and paths
  only; under 250 lines; tracked in git.
