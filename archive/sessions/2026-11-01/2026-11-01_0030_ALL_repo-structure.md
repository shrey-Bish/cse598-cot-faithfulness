# Session log: the repo's structure (Nov 1, 00:10–00:30 MST, then after B16)

By: Ritik (asked Oct 31 at night, before anything new runs and before Arsha or Shrey receive anything, so their
paths never change again). Work done overnight while Ritik was away; every judgment call is listed in §6 for the
morning.

## 1. The limits

- **B16 was running on this Mac** (pid 11863 under the guard 11859, since Oct 31 22:25). Nothing it imports or
  writes was moved, changed or deleted, and nothing was run that writes there, until it ended. Its static import
  graph (from `progress/run_b16.py`, `progress/guard.py` and the provider it loads by name, `providers/voyager.py`):
  `client.py`, `detect.py`, `experiments.py`, `parse.py`, `tasks.py`, `finetune/__init__.py`, `base_format.py`,
  `continuation.py`, `olmo_format.py`, `progress/common.py`, `guard.py`, `run_b16.py`, `run_trackB.py`,
  `trackB_report.py`, `voyager_template_check.py`, `providers/__init__.py`, `base.py`, `budget.py`, `ollama.py`,
  `responses_api.py`, `voyager.py`, `tools/answer_key.py`; it reads `configs/` (models, prices, Track B, canaries)
  and writes `results/trackB/b16_*`, `cache/` and `logs/`. To be safe, nothing in `progress/`, `providers/` or
  `configs/` changed while it ran, imported or not.
- **Sol's queued jobs** (the B1 bench 122956, Qwen3-8B's Steps 3 and 10, 123022 and 123025) run whatever Sol pulls
  next. Their graph (`finetune/gpu/provenance_job.py`, `finetune/look/qwen8b_mech.py`) adds `build_dataset.py`,
  `eval.py`, `generate.py`, `hf_engine.py`, `make_targets.py`, `provenance.py`, `run_nohint.py`, `source_tags.py`,
  `train.py`, `finetune/gpu/kit.py`, `finetune/look/` (`before_takeover`, `deletion`, `hint_spans`, `patching`,
  `qwen8b_mech`, `takeover`), `providers/sol_hf.py`, and `run.sh`, `env.sh`, `guard.sh`, `accounts.conf`, `submit.sh`
  and the three `.sbatch` files. None of these 53 files changed tonight (checked against the list before each
  commit).
- **No code folder or Python module moved.** Code is cleaned by removing dead files and explaining the rest.

## 2. The moves (commit `d48660e`, content unchanged)

15 files, each a `git mv` (the table, with the reason for each, is in [`archive/MOVES.md`](../../MOVES.md)):
the track docs to `docs/tracks/` (`TRACK_A_PROVENANCE.md` renamed `TRACK_A_FIX.md`, as asked), the labeling material
to `docs/labeling/`, TODO, STATUS and the Gantt files to `docs/status/`, `docs/MOVES.md` to `archive/`. `docs/handoff/`
and `docs/progress/` are gone (empty).

**Links and paths (the next commit).** A script rewrote every relative markdown link to a moved file and every link
inside one, from the move table (63 links in 16 files, archived logs and superseded copies included: only their link
targets changed). Path mentions by hand in FINDINGS, PLAN, RUNBOOK, TODO, REVIEWER_QUESTIONS, the track docs, the GPU
kit's README; in code: `tools/make_gantt.py` (TODO from `docs/status/`, a fallback to `docs/TODO.md` for an older
tree; the generated files into `docs/status/`; a commit to `docs/tracks/TRACK_B.md` or `TRACK_C.md` counts for its
track; 3 new or changed tests, run failing first: 16 of 49 failed, then all 49 passed; with the fallback test, 50), `tools/make_supplement.py` (the track
docs), `tools/label_kit.py`, `ui/app.py`, `ui/static/charts.js` and `tests/test_ui.py` (the label queue and the
results summary).

**Left at the old path** (TODO D12): `finetune/__init__.py`'s and `finetune/source_tags.py`'s docstrings (they name
`docs/TRACK_A.md`) and `progress/common.py`'s `DOCS` (`docs/progress`), because B16 and Sol's queued jobs import
them. `docs/labeling/RESULTS_SUMMARY.json` still records `"file": "docs/progress/LABEL_QUEUE.csv"`: it is generated
(`progress/analyze_progress.py`), so it was not edited by hand; the next run of the script writes the new path.

## 3. The front door and the code map

- `README.md`: one page. The theme and the story in five lines; "read this first" for Ritik, Shrey, Arsha, a grader
  and a paper reviewer; the folder map; how to run the tests; the submission folder's date.
- `cot-disclosure/README.md`: the code map. One table: folder → track → what it holds → main entry points, with the
  older scripts marked *historical* and the result each is evidence for (the progress round's Test 1 and 2 and
  Experiment A, its figures F1–F9; Track A's Steps 1–2b, 5–7 and 8–11; F4–F6 for Step 3's extra analyses; C14). The
  Voyager facts and the limits are kept; the long command list (now in RUNBOOK) and the key table are shortened.
- `docs/PLAN.md`: no submission folder yet; it's made on Nov 19–21 (TODO D13).

## 4. Dead code: the checks, and why nothing was removed

The four checks, for every tracked file under `cot-disclosure/` outside `results/` and `tests/` (a static import
graph that also resolves the `sys.path` folders the code adds; `git grep` for the file name in the tests, `sbatch`
files, `run.sh`, RUNBOOK, the two handoffs and the 20 pre-registration logs in the supplement's ledger; and in
FINDINGS, `results/summaries/` and the supplement). 35 files pass all four. None is dead:

| files | why it stays |
|---|---|
| `configs/canary/*.json` (4), `providers/xai.py` | loaded by name at run time (`client.py`'s identity canary, `configs/canary/<model>.json`; `providers/__init__.py` imports `providers.<name>` for each provider in `models.yaml`) |
| `configs/prices.yaml`, `finetune/gpu/inputs_manifest.json` | read by `providers/budget.py` and `finetune/gpu/kit.py` |
| `finetune/gpu/sol/get_qwen8b.sbatch`, `setup_env.sbatch`, `step8.sbatch`, `timing.sbatch`, `vllm_check.sbatch` | job definitions `submit.sh <kind>` runs by kind (RUNBOOK names the kind, not the file); `run.sh` dispatches each; SOL_SETUP uses `setup_env` |
| `ui/static/*` (11) | served by `ui/app.py` (`test_ui` runs it) |
| `finetune/gpu_estimate.py` | PLAN's Sol hours estimate comes from it (Track A, the training plan) |
| `finetune/show_spans.py`, `finetune/smoke_2b.py`, `finetune/template_revisions.py`, `finetune/move_to_gz.py` | Steps 2–2b and the Oct 25 size rule; listed in TRACK_A.md; `template_revisions.json` is read by `voyager_template_check.py` and `export_summaries.py`; all still import cleanly (checked) |
| `progress/check_tool_support.py`, `timing_run.py`, `truncation_sweep.py`, `build_evidence_viewer.py`, `extract_slides.py`, `make_bundle.py`, `take_screenshots.py`, `ui/screenshots.py` | the progress round's evidence and presentation tools (its figures F1–F9; `results/scope/voyager_tool_support.jsonl` is cited in `configs/models.yaml`); marked historical in the code map |

**Removed: none.** The rule allows a removal only when all four checks hold, and asks for judgment on top; every file
that passes them is either loaded by name or is the record of how a reported result was made.

## 5. Untracked clutter

(Filled in after B16: §5 of the overnight log below.)

## 6. Judgment calls (for the morning)

1. **`cot-disclosure/cache/` is not a cache to delete.** It is the API reply cache (841 MB) that makes reruns free and
   B16 writes there; "delete caches" was read as Python's and the test tools' caches only.
2. **The docs' `RESULTS_SUMMARY.json` went to `docs/labeling/`, as asked,** though it is the progress round's
   numbers rather than labeling material: code reads it beside the label queue, and moving it twice later would cost
   more than the name.
3. **`TRACK_A_PROVENANCE.md` → `TRACK_A_FIX.md`**, as asked; its first line still says what it holds (B1/B2).
4. **Nothing in `progress/`, `providers/` or `configs/` changed while B16 ran,** even files outside its import graph
   (the instruction listed the folders). The progress-round scripts' new paths and B17's amendment waited for B16 to
   end.
5. **One test wrote to `logs/` while B16 ran.** `tests/test_ui.py`, run on its own at 00:17 after its path changed,
   appended one line (`[ui] rerun ... cached=False`, a fake reply; no call) to the shared session log
   `logs/progress_20261004T201106Z.log`, which B16 also writes. B16's own lines and records are unaffected. From
   then on, the full suite ran in a separate worktree until B16 ended.
