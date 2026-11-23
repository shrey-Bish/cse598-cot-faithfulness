# tools/

Scripts that make or check things around the experiments. Run from `cot-disclosure/`.

| Group | Scripts |
|---|---|
| Figures and tables | `paper_figures.py`, `slide_figures.py`, `trackb_final.py`, `a39_figures.py`, `a40_figures.py`, `b1r2_figure.py`, `tradeoff.py` |
| Generated docs | `make_supplement.py`, `make_glossary.py`, `make_gantt.py`, `make_deck.py`, `make_submission.py` |
| The demo | `demo_template/` (the current demo's source and build), `build_demo.py` and `explainer/` (the earlier Hint Explainer) |
| Summaries and bundles | `export_summaries.py` (numbers-only results), `make_handoff_bundle.py` |
| Labels | `label_kit.py`, `rater_packets.py`, `llm_judge.py`, `l6_sheet.py`, `l6_read.py` |
| Repo checks | `check_links.py`, `prepush_check.py`, `path_check.py` (the git hooks) |
| Other | `answer_key.py` (the hint conditions and the tool), `sol_feeder.py` (keeps Sol's queue full) |

Open `check_links.py` or `paper_figures.py` first. Each script's top comment says what it reads and writes. Most
generated files say "do not edit by hand" in their header; rerun the script instead.
