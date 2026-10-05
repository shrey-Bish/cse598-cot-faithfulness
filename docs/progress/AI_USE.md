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
- Experiment B (MMLU-Pro with a user or simulated-tool hint)
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

## Scope update (2026-10-04, branch `scope-update`)

The same AI coding agent, again from a written brief the student supplied:

**Docs.**
- Updated the docs to the new scope:
  - a scope section in `PROGRESS_REPORT.md`
  - new risks in `FAILURES_AND_RISKS.md`
  - new plain-language entries in `CONCEPTS.md`
  - "hint" instead of "cue" throughout
  - `SLIDE_POINTS.md` regenerated from the v2 deck
- Wrote `docs/plan/` (project plan, three track pages, budget).

**Numbers.** Computed two new sets of numbers from saved results:
- the private/final mention overlap in Test 1
- Test 2's combined thinking-model counts

**Provider research.** Read each provider's current documentation and pricing on
2026-10-04 (through a research sub-agent) and recorded the facts, with sources, in
`cot-disclosure/configs/models.yaml` and `prices.yaml`.

**Code.** Wrote:
- the provider adapters and the budget guard
- the answer-key tool with real tool calls
- the Track B runner
- the Track C agents
- the Track A dataset builder and source tags
- tests (42 pass)

**Model calls.** Made only free Voyager calls:
- the tool-support check: about a dozen calls, first tried in a scratch script, then saved by `check_tool_support.py`, which reused the cached replies
- 14 calls for the 2-question live team run

No paid API was called: there are no OpenAI, Anthropic or xAI keys yet.

**Not done by the AI:** human labeling, the Track B sweep, and model training. The team
reviews and owns the plan, the code and the report.

