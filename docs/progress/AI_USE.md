# AI use disclosure (progress round, October 2026)

This is for CSE 598 Group 10's progress submission.

An AI coding agent (Claude, run in Claude Code by Ritik Agarwal on 2026-10-04) did the
following from a written brief the student supplied.

**Wrote these scripts**, all in `cot-disclosure/progress/`:
- `common.py`
- `timing_run.py`
- `reviewer_demo.py`
- `mmlu_pro_probe.py`
- `truncation_sweep.py`
- `analyze_progress.py`
- `build_evidence_viewer.py`
- `take_screenshots.py`

It also wrote the unit tests in `cot-disclosure/tests/`.

**Made small extensions to existing repo code:**
- `client.py`: retry logging, latency, reasoning-field name, an optional non-streamed
  mode, and the model list
- `parse.py`: letters A to J, and the reviewer's `FINAL: X` line
- `detect.py`: tool-block keywords
- `experiments.py`: exposed the pilot prompt builder

**Ran the model calls** on ASU's Voyager service:
- the timing run
- Experiment A (the reviewer demo)
- Experiment B (MMLU-Pro with a user or simulated-tool cue)
- the truncation sweep

Every call's prompt, reply, and settings are saved in `cot-disclosure/results/progress/`.

**Generated outputs from the saved results only:**
- the figures in `presentation/progress/figures/`
- the evidence viewer and screenshots in `presentation/progress/`
- `docs/progress/RESULTS_SUMMARY.json`

**Drafted the working notes** in `docs/progress/` from `RESULTS_SUMMARY.json` and the
saved replies.

**What the AI did not do:** it did not build or edit the slide deck, and it did not
label any data. The human labels in `LABEL_QUEUE.csv` are still to be done by two team
members.

**Human responsibility:** the team reviews, checks, edits, and owns the final slides,
the talk, and the report. Every number in these notes can be regenerated from the saved
JSONL with `python cot-disclosure/progress/analyze_progress.py`. Any number the team
quotes should be checked against `RESULTS_SUMMARY.json` before it goes on a slide.
