# 18. Evaluation audit (Nov 26)

An audit of the project's evaluation against a standard checklist, written for the handbook dossier
(`~/Downloads/HANDBOOK_DOSSIER.md`, Part B).

- **Status:** **done**, **partly** or **missing**, from the repo as it stands at `a90b216` (the results frozen at the tag
  `results-freeze-2026-11-18`; C27 a post-freeze addendum).
- **Evidence:** a file, a finding or a 02_NUMBERS row, as cited; paths are from the repo root.
- No number is new here.

## The checklist

| item | status | evidence | why it matters |
|---|---|---|---|
| A research question and hypotheses stated before the data | done | `docs/PLAN.md`; the supplement's ledger `docs/paper/supplement/PREREGISTRATIONS.md` (43 rows; each rule with the commit that fixed it and the one that first reported a result) | a claim tested against a rule written first can't be fitted to the data |
| Datasets documented (source, size, splits, contamination, overlaps) | done | `cot-disclosure/data/progress/mmlupro_30.jsonl`, `mmlupro_e2.jsonl` (E2: 30 each of chemistry, engineering, law, physics; `finetune/make_e2.py`); `agents/fresh_items.py` (C15: none in the pool or the 30, by id and text); `finetune/c27.py --items` (C27: none of Track A's 1,750 questions); dossier file 04 | a model that has seen a question, or a set chosen after looking, inflates or biases every rate |
| Baselines | done | no hint (`eval.py` A39_NOHINT); the user's guess against the tool (F16, N132); no fix and the one-line instruction for every fix (F41, the fix table on backup 30); the no-tool team (C5's floor, `agents/run_team.py`); the reviewer seeing the answer only (F18) | a rate means little without the comparison it moves against; the instruction is the cheap fix every trained one must beat |
| Metrics defined in code | done | `finetune/eval.py` (system_report, followed, flags), `finetune/a39.py` MEASURES, `detect.py` (the keyword lists), `agents/run_team.py` (outcome: shipped, caught, false alarm, undetermined); dossier file 07 | a metric defined only in prose drifts between experiments |
| Metrics validated against hand labels | partly | keyword mention against labels: L3 under kappa 0.6 in four of six cells, so F3 stays a keyword count; L4 part 1 kappa 0.93 (human against an AI rater); the judges (J-opus 0.967 on L4) (FINDINGS F3, F28, F45; lines 115, 195, 304) | keyword "hiding" is defeated by the trained models' openers (F28, F41); only the labels can say what an answer discloses |
| Uncertainty | done | Wilson intervals on rates; differences with a 95% paired bootstrap clustered by question (by item in Track C), 20,000 resamples, seed 0 (`progress/common.py` boot_diff, wilson); under 5 questions "too few questions" (MIN_QUESTIONS) | runs on one question aren't independent; clustering keeps the intervals honest |
| Multiple comparisons | partly | named but not corrected: B20's 27 readings and B24's fifteen "not corrected for multiplicity" (`docs/paper/REPORT.md` lines 188, 206; FINDINGS line 2411) | with many readings some intervals exclude 0 by chance |
| Pre-registration | done | 31 rules pre-registered for the frozen results and C27's after the freeze (PREREGISTRATIONS.md); each with its fixing commit before its first result ("yes" in the order column) | it separates tests from explorations; the exploratory ones are labelled (e.g. the trade-off, `2026-11-07_2020_A_tradeoff-exploratory.md`) |
| Deviations recorded | done | `docs/paper/supplement/DEVIATIONS.md` (curated and dated, each checked against its source); TRAPS T1–T12 (`docs/paper/supplement/TRAPS.md`) | a change of plan that isn't written down can't be weighed |
| Held-out evaluation for every fix | done | every trained version on the 30 held-out questions with held-out wordings (Gate 3) and on E2's 120 fresh questions (A39, A40, A42); C27 on C15's 100 | a fix tested on its training questions shows memory, not a fix |
| Contamination, training against test | done | E2 and the 30 disjoint from the training pool (`finetune/make_e2.py`, `build_dataset.heldout_overlap`); C15 and C27 items checked by id and text; held-out wordings never in training (`build_dataset.WORDINGS`) | the same question or wording in training and test would show a fix that isn't there |
| Ablations | done | five trained versions (LoRA, tags, LoRA + tags, LoRA on layers 15/19/23, consistency training), the instruction and label alone and combined (F28, F41–F44); channels (user, pasted, inserted declared and undeclared, system); per-layer patching over 32 layers (F11); the reviewer's views and redaction (C9–C13, C17–C20) | each part's own effect, not just the whole system's |
| Replication | done | layers on 16 new questions 0.90 [0.76, 1.06] and in Qwen3 8B 0.70 [0.60, 0.83] (F11, F36); F18 on C15's fresh items (F24); B19's same-day rerun of B16 (F35); Gate 3's reading again on E2 with power (A39, F41) | a result seen once on one set may be that set's |
| Error analysis and examples | partly | hand-label categories (L4, L6; now tabulated, Part C 2, `docs/handbook/PART_C.md`); the demo's recorded runs (clips A–D); dossier file 17; resisted answers never labelled | the rates say how often; the categories and examples say how |
| Cost and efficiency | done | 352.47 GPU-hours over 271 GPU jobs (`cot-disclosure/tools/demo_template/method.json`); C27 about 2.0 GPU-hours (the 17:45 log); tokens per case in Track C (`agents/run_team.py` tokens); the checker's cost, one more model call (slide 9) | a fix that works at ten times the cost isn't the same fix |
| Reproducibility | done | `REPRODUCE.md`; seeds (seed = the run's repeat; the bootstrap's seed 0; sheet seeds such as L6-20261107); model revisions pinned (`finetune/gpu/olmo3_7b_think_d97e442.json`, `agents/sol_c13.py`); every deck number traced to a JSON key in `docs/presentation/pack/02_NUMBERS.md` and tested (`tests/test_presentation_pack.py`, `tests/test_final_deck.py`); summaries exported numbers-only (`tools/export_summaries.py`) | a number nobody can recompute can't be checked |
| Limitations | done | `docs/paper/REPORT.md` §10 (power, format, cross-day, labels, Track C, models, multiplicity, Sol's servers; the limits with sources) | the reader needs to know where the claims stop |

## What's missing

| missing | from saved data (Part C) or new runs |
|---|---|
| Seed variance: one training run per version (REPORT §10, "one model, one training run a version") | new runs (train each version with more seeds) |
| A second trained model: only Olmo 3 7B Think was trained | new runs |
| A second benchmark: MMLU-Pro and the puzzles only; GPQA was planned and not used (dossier file 04) | new runs |
| Free-form tasks: multiple choice only | new runs and a new scoring method |
| Closed models: open-weight models only, up to about 30B parameters | new runs (paid APIs) |
| The checker's hard case: a checker re-solving with a model that can't solve the question alone (C27: 5 of 55 got through with the 7B checker; C15's checker 53 of 53) | partly from saved data (split C15's and C27's items by whether the no-tool model solves them); fully, new runs on hard items (C21, not run) |
| Two human raters: one human and one AI rater, not the two pre-registered (REPORT §10) | new labelling, no runs |
| Resisted answers never hand-labelled (Part C 2) | new labelling of saved runs, no runs |
| Blind labelling: L4 part 1's and L6's rater could tell the trained style (F28, F45) | new labelling with the openers hidden |
| No multiplicity correction on B20's and B24's readings | from saved data (e.g. Holm on the stored intervals' bootstraps), not done here |
| Per-subject results on the 120 fresh questions | done from saved data (Part C 3; descriptive) |
| A failure taxonomy from the labels (planned in Week 15) | done from saved data (Part C 2; descriptive) |
| Power: the 30-question comparisons can't resolve 5-point limits (REPORT §10; F38) | new runs (E2's 120 were the answer for later fixes) |
