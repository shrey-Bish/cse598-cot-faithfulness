# Session log: the repository reorganization, PROPOSED (not applied) (2026-10-30 21:41 MST)

Project: CSE 598 Group 10, all tracks. Ritik asked for an organized, properly structured repo with nothing lost, in
two steps: propose, then apply after his "go". This is step 1. **Nothing has moved yet**, and this log is not
committed. **By:** Ritik.

Rules:
- move with `git mv`, never delete;
- every move goes in `docs/MOVES.md`;
- merge only real duplicates, with the originals kept in `archive/merged-docs/`;
- no code, tests, configs, sbatch files or anything a Sol job reads moves;
- produced data is untouched;
- numbers-only summaries that code reads stay.

## a. The tree now (582 tracked files)

```
/ (2 files: README.md, .gitignore)
cot-disclosure/                  385  the code (agents 13, configs 8, data 1, finetune 89, progress 19, providers 13,
                                      results 141 [summaries 118, progress-round 23], tests 66, tools 10, ui 13, root 12)
docs/                            129  FINDINGS, OVERVIEW, PLAN, RUNBOOK, TODO (5); handoff 3; paper 60 [figures 9,
                                      supplement 46, 5 docs]; progress 7; sessions 54
presentation/                     66  the Oct progress deck: 3 .pptx, the build script, figures, screenshots
```

**Every README and top-level doc:**

| file | lines | what it is for |
|---|---|---|
| `README.md` | 106 | the project's front page: the question, findings so far, where things are, quick start |
| `cot-disclosure/README.md` | 171 | the code: setup, commands, a file map, Voyager facts, limits |
| `cot-disclosure/finetune/README.md` | 143 | Track A's design: the pipeline, data, training, tags, evaluation |
| `cot-disclosure/finetune/PROVENANCE.md` | 172 | B1/B2's method (provenance-scaled attention, the gate) |
| `cot-disclosure/finetune/gpu/README.md` | 633 | the Sol kit: access, environments, jobs, QoS, every Sol line |
| `cot-disclosure/ui/README.md` | 132 | the progress round's wrong-hint demo |
| `docs/paper/README.md` | 14 | an index of the paper pack |
| `docs/OVERVIEW.md` | 294 | "everything done so far", an Oct 27 snapshot |
| `docs/FINDINGS.md` | 1,876 | every finding with numbers, sources and status; the story so far; the traps |
| `docs/PLAN.md` | 531 | weeks 11–16: timeline, gates, per-track plans, Sol job plan, risks |
| `docs/TODO.md` | 185 | every open and done task, by track |
| `docs/RUNBOOK.md` | 483 | how to run every step |
| `docs/handoff/TRACK_B.md`, `TRACK_C.md`, `SOL_SETUP.md` | 241, 186, 150 | handoffs to Arsha and Shrey; Sol for a second user |
| `docs/paper/CLAIMS.md`, `OUTLINE.md`, `REVIEWER_QUESTIONS.md`, `RELATED_WORK.md` | 215, 118, 114, 206 | the paper pack |
| `docs/progress/LABELING_GUIDE.md`, `RATER_GUIDE.md` | 139, 102 | hand labels |
| `docs/progress/STATUS.md` (+ `GANTT.xlsx`, `gantt.png`) | 60 | generated status |
| `docs/sessions/*` | 54 files | session logs, dailies, INDEX, LATEST |

**Overlaps (docs that say the same things):**
- **Status and the story are in four places:** the root README's "What we found so far", FINDINGS' "story so far",
  OVERVIEW §1–3 (as of Oct 27), and STATUS.md.
- **OVERVIEW.md is an Oct 27 snapshot, now superseded:**
  - its traps (§9) are FINDINGS' T1–T10;
  - its code map (§10) is the code README's "Files";
  - its status (§2) is PLAN, TODO and STATUS.
  - Its terms (§4), models and Voyager (§5) and progress round (§6) are partly in the code README and FINDINGS. It
    is kept whole in the archive, not merged.
- **How to run is in three places:** RUNBOOK (by step), the code README's "Commands", Track A's README (pipeline
  commands). The audiences differ (operator, new coder, Track A design), so no merge.
- **`docs/paper/README.md`** (14 lines) is a list of the paper files: the same as the folder map the new root README
  will have.
- **`docs/sessions/LATEST.md`** is a copy of the newest log, by design. It stays beside INDEX as the "start here" of
  the history.

## b. The proposed tree

```
/  README.md (rewritten: the front door), .gitignore (+ !/archive/)
cot-disclosure/          the code, UNCHANGED in layout. README.md = the code guide (one README);
                         finetune/gpu/README.md = the Sol kit (one README). No other README under it.
docs/                    the living docs, in one place:
  FINDINGS.md PLAN.md TODO.md RUNBOOK.md STATUS.md GANTT.xlsx gantt.png MOVES.md
  TRACK_A.md             (was cot-disclosure/finetune/README.md: Track A's design)
  TRACK_A_PROVENANCE.md  (was cot-disclosure/finetune/PROVENANCE.md: B1/B2's method)
  handoff/               TRACK_B.md TRACK_C.md SOL_SETUP.md: the handoffs, in one place
  paper/                 CLAIMS OUTLINE REVIEWER_QUESTIONS RELATED_WORK figures/ supplement/: the paper, in one place
  progress/              LABELING_GUIDE.md RATER_GUIDE.md LABEL_QUEUE.csv RESULTS_SUMMARY.json
                         (stays by name: label_kit.py, the UI and the progress-round scripts read these two files)
archive/                 history, out of the way but kept:
  sessions/              INDEX.md LATEST.md 2026-10-27/ 2026-10-28/ 2026-10-29/ 2026-10-30/ (logs + dailies by date)
  progress-round/        presentation/ (the Oct deck and its assets), ui_demo_README.md, results/ (3 console logs)
  superseded/            OVERVIEW_2026-10-27.md
  merged-docs/           paper_README.md (the original of the one merged doc)
```

**Why each folder:**
- **The root README** is the one front door. It says:
  - what the project is;
  - the five-line story of the findings;
  - a folder map;
  - where to start for Ritik (STATUS, TODO), Shrey (handoff/TRACK_C.md), Arsha (handoff/TRACK_B.md), a grader
    (README, FINDINGS' story, STATUS), and a paper reviewer (paper/CLAIMS, paper/supplement/EVIDENCE and
    PREREGISTRATIONS).
- **`cot-disclosure/`** keeps every code folder where it is: Sol's queued jobs read the clone's paths.
- **`docs/`** holds only what is current; `docs/progress/` keeps its name because code reads two files in it.
- **`archive/`** holds everything historical, kept and linked from the root README in one line.
- **The progress round's tracked results** that code reads (`results/*.jsonl`, `results/progress/`,
  `results/scope/`, `results/summary.json`) stay put. The three console logs nothing reads move to the archive.

## c. The move table (131 files) and the one merge

**The merge:** `docs/paper/README.md` → its list goes into the root README's folder map. The original is kept
unchanged at `archive/merged-docs/paper_README.md`. Nothing in it is dropped: every file it lists is in the new map.

| # | old path | new path | why |
|---|---|---|---|
| 1 | `docs/sessions/2026-10-27_1010_catch-up.md` | `archive/sessions/2026-10-27/2026-10-27_1010_catch-up.md` | history: session logs and dailies, by date |
| 2 | `docs/sessions/2026-10-27_1305_B_smoke-and-pilots.md` | `archive/sessions/2026-10-27/2026-10-27_1305_B_smoke-and-pilots.md` | history: session logs and dailies, by date |
| 3 | `docs/sessions/2026-10-27_1355_A_steps67-final.md` | `archive/sessions/2026-10-27/2026-10-27_1355_A_steps67-final.md` | history: session logs and dailies, by date |
| 4 | `docs/sessions/2026-10-27_1400_ALL_paused-for-class.md` | `archive/sessions/2026-10-27/2026-10-27_1400_ALL_paused-for-class.md` | history: session logs and dailies, by date |
| 5 | `docs/sessions/2026-10-27_1400_ALL_rewrite-and-merge.md` | `archive/sessions/2026-10-27/2026-10-27_1400_ALL_rewrite-and-merge.md` | history: session logs and dailies, by date |
| 6 | `docs/sessions/2026-10-27_1505_C_C1-five-items.md` | `archive/sessions/2026-10-27/2026-10-27_1505_C_C1-five-items.md` | history: session logs and dailies, by date |
| 7 | `docs/sessions/2026-10-27_2308_ALL_sol-fixes-and-status.md` | `archive/sessions/2026-10-27/2026-10-27_2308_ALL_sol-fixes-and-status.md` | history: session logs and dailies, by date |
| 8 | `docs/sessions/2026-10-27_2355_ALL_qos-training-qwen8b.md` | `archive/sessions/2026-10-27/2026-10-27_2355_ALL_qos-training-qwen8b.md` | history: session logs and dailies, by date |
| 9 | `docs/sessions/2026-10-28_0002_A_vllm-options-on-gpu.md` | `archive/sessions/2026-10-28/2026-10-28_0002_A_vllm-options-on-gpu.md` | history: session logs and dailies, by date |
| 10 | `docs/sessions/2026-10-28_0032_ALL_32b-reviewer-and-sol-prep.md` | `archive/sessions/2026-10-28/2026-10-28_0032_ALL_32b-reviewer-and-sol-prep.md` | history: session logs and dailies, by date |
| 11 | `docs/sessions/2026-10-28_0045_B_interim-table-and-halt-guard.md` | `archive/sessions/2026-10-28/2026-10-28_0045_B_interim-table-and-halt-guard.md` | history: session logs and dailies, by date |
| 12 | `docs/sessions/2026-10-28_0325_B_qwen3-thinking-final-and-c4-start.md` | `archive/sessions/2026-10-28/2026-10-28_0325_B_qwen3-thinking-final-and-c4-start.md` | history: session logs and dailies, by date |
| 13 | `docs/sessions/2026-10-28_0545_ALL_qwen3-instruct-final-and-c4-interim.md` | `archive/sessions/2026-10-28/2026-10-28_0545_ALL_qwen3-instruct-final-and-c4-interim.md` | history: session logs and dailies, by date |
| 14 | `docs/sessions/2026-10-28_1220_ALL_sol-fixes-decisions-and-the-bare-letter.md` | `archive/sessions/2026-10-28/2026-10-28_1220_ALL_sol-fixes-decisions-and-the-bare-letter.md` | history: session logs and dailies, by date |
| 15 | `docs/sessions/2026-10-28_1823_ALL_c4-olmo-done-and-the-bare-letter-control.md` | `archive/sessions/2026-10-28/2026-10-28_1823_ALL_c4-olmo-done-and-the-bare-letter-control.md` | history: session logs and dailies, by date |
| 16 | `docs/sessions/2026-10-28_2144_ALL_vllm-rule-keyword-check-and-c9-dry-run.md` | `archive/sessions/2026-10-28/2026-10-28_2144_ALL_vllm-rule-keyword-check-and-c9-dry-run.md` | history: session logs and dailies, by date |
| 17 | `docs/sessions/2026-10-28_2242_ALL_training-against-base-and-c9.md` | `archive/sessions/2026-10-28/2026-10-28_2242_ALL_training-against-base-and-c9.md` | history: session logs and dailies, by date |
| 18 | `docs/sessions/2026-10-28_2303_ALL_tags-check-and-c10-dry-run.md` | `archive/sessions/2026-10-28/2026-10-28_2303_ALL_tags-check-and-c10-dry-run.md` | history: session logs and dailies, by date |
| 19 | `docs/sessions/2026-10-28_2319_C_c10-commit-first.md` | `archive/sessions/2026-10-28/2026-10-28_2319_C_c10-commit-first.md` | history: session logs and dailies, by date |
| 20 | `docs/sessions/2026-10-29_0020_ALL_night-dry-runs-setA-c11-c12.md` | `archive/sessions/2026-10-29/2026-10-29_0020_ALL_night-dry-runs-setA-c11-c12.md` | history: session logs and dailies, by date |
| 21 | `docs/sessions/2026-10-29_0810_ALL_hf-generation-for-sol.md` | `archive/sessions/2026-10-29/2026-10-29_0810_ALL_hf-generation-for-sol.md` | history: session logs and dailies, by date |
| 22 | `docs/sessions/2026-10-29_1055_ALL_setA-c11-c12-done.md` | `archive/sessions/2026-10-29/2026-10-29_1055_ALL_setA-c11-c12-done.md` | history: session logs and dailies, by date |
| 23 | `docs/sessions/2026-10-29_1645_ALL_sol-fixes-and-c13-prereg.md` | `archive/sessions/2026-10-29/2026-10-29_1645_ALL_sol-fixes-and-c13-prereg.md` | history: session logs and dailies, by date |
| 24 | `docs/sessions/2026-10-29_2300_ALL_c14-c15-b15-prereg.md` | `archive/sessions/2026-10-29/2026-10-29_2300_ALL_c14-c15-b15-prereg.md` | history: session logs and dailies, by date |
| 25 | `docs/sessions/2026-10-29_2330_ALL_gate3-raters-handoffs.md` | `archive/sessions/2026-10-29/2026-10-29_2330_ALL_gate3-raters-handoffs.md` | history: session logs and dailies, by date |
| 26 | `docs/sessions/2026-10-30_0110_C_c15-results.md` | `archive/sessions/2026-10-30/2026-10-30_0110_C_c15-results.md` | history: session logs and dailies, by date |
| 27 | `docs/sessions/2026-10-30_0400_B_b15-results.md` | `archive/sessions/2026-10-30/2026-10-30_0400_B_b15-results.md` | history: session logs and dailies, by date |
| 28 | `docs/sessions/2026-10-30_0845_ALL_sol-morning-and-decisions.md` | `archive/sessions/2026-10-30/2026-10-30_0845_ALL_sol-morning-and-decisions.md` | history: session logs and dailies, by date |
| 29 | `docs/sessions/2026-10-30_0850_C_c16-prereg.md` | `archive/sessions/2026-10-30/2026-10-30_0850_C_c16-prereg.md` | history: session logs and dailies, by date |
| 30 | `docs/sessions/2026-10-30_0900_A_setA-step10-replicates.md` | `archive/sessions/2026-10-30/2026-10-30_0900_A_setA-step10-replicates.md` | history: session logs and dailies, by date |
| 31 | `docs/sessions/2026-10-30_0905_A_b1-alpha-chosen.md` | `archive/sessions/2026-10-30/2026-10-30_0905_A_b1-alpha-chosen.md` | history: session logs and dailies, by date |
| 32 | `docs/sessions/2026-10-30_0910_A_gate3-interim.md` | `archive/sessions/2026-10-30/2026-10-30_0910_A_gate3-interim.md` | history: session logs and dailies, by date |
| 33 | `docs/sessions/2026-10-30_0915_B_qwen3-8b-thinking-on-off.md` | `archive/sessions/2026-10-30/2026-10-30_0915_B_qwen3-8b-thinking-on-off.md` | history: session logs and dailies, by date |
| 34 | `docs/sessions/2026-10-30_0920_C_c13-granite-mistral.md` | `archive/sessions/2026-10-30/2026-10-30_0920_C_c13-granite-mistral.md` | history: session logs and dailies, by date |
| 35 | `docs/sessions/2026-10-30_1010_A_setA-step9-prereg.md` | `archive/sessions/2026-10-30/2026-10-30_1010_A_setA-step9-prereg.md` | history: session logs and dailies, by date |
| 36 | `docs/sessions/2026-10-30_1025_C_c17-prereg.md` | `archive/sessions/2026-10-30/2026-10-30_1025_C_c17-prereg.md` | history: session logs and dailies, by date |
| 37 | `docs/sessions/2026-10-30_1030_C_c16-results.md` | `archive/sessions/2026-10-30/2026-10-30_1030_C_c16-results.md` | history: session logs and dailies, by date |
| 38 | `docs/sessions/2026-10-30_1035_A_setA-step9-replicates.md` | `archive/sessions/2026-10-30/2026-10-30_1035_A_setA-step9-replicates.md` | history: session logs and dailies, by date |
| 39 | `docs/sessions/2026-10-30_1045_A_l4-label-sheets.md` | `archive/sessions/2026-10-30/2026-10-30_1045_A_l4-label-sheets.md` | history: session logs and dailies, by date |
| 40 | `docs/sessions/2026-10-30_1100_C_c17-results.md` | `archive/sessions/2026-10-30/2026-10-30_1100_C_c17-results.md` | history: session logs and dailies, by date |
| 41 | `docs/sessions/2026-10-30_1145_A_qwen8b-mech-prereg.md` | `archive/sessions/2026-10-30/2026-10-30_1145_A_qwen8b-mech-prereg.md` | history: session logs and dailies, by date |
| 42 | `docs/sessions/2026-10-30_1700_C_c18-prereg.md` | `archive/sessions/2026-10-30/2026-10-30_1700_C_c18-prereg.md` | history: session logs and dailies, by date |
| 43 | `docs/sessions/2026-10-30_1715_A_b1-generation-rule.md` | `archive/sessions/2026-10-30/2026-10-30_1715_A_b1-generation-rule.md` | history: session logs and dailies, by date |
| 44 | `docs/sessions/2026-10-30_1720_C_c18-results.md` | `archive/sessions/2026-10-30/2026-10-30_1720_C_c18-results.md` | history: session logs and dailies, by date |
| 45 | `docs/sessions/2026-10-30_1725_ALL_gantt.md` | `archive/sessions/2026-10-30/2026-10-30_1725_ALL_gantt.md` | history: session logs and dailies, by date |
| 46 | `docs/sessions/2026-10-30_1740_ALL_cleanup.md` | `archive/sessions/2026-10-30/2026-10-30_1740_ALL_cleanup.md` | history: session logs and dailies, by date |
| 47 | `docs/sessions/2026-10-30_1800_ALL_supplement.md` | `archive/sessions/2026-10-30/2026-10-30_1800_ALL_supplement.md` | history: session logs and dailies, by date |
| 48 | `docs/sessions/2026-10-30_1805_C_handoff-to-shrey.md` | `archive/sessions/2026-10-30/2026-10-30_1805_C_handoff-to-shrey.md` | history: session logs and dailies, by date |
| 49 | `docs/sessions/DAILY_2026-10-27.md` | `archive/sessions/2026-10-27/DAILY_2026-10-27.md` | history: session logs and dailies, by date |
| 50 | `docs/sessions/DAILY_2026-10-28.md` | `archive/sessions/2026-10-28/DAILY_2026-10-28.md` | history: session logs and dailies, by date |
| 51 | `docs/sessions/DAILY_2026-10-29.md` | `archive/sessions/2026-10-29/DAILY_2026-10-29.md` | history: session logs and dailies, by date |
| 52 | `docs/sessions/DAILY_2026-10-30.md` | `archive/sessions/2026-10-30/DAILY_2026-10-30.md` | history: session logs and dailies, by date |
| 53 | `docs/sessions/INDEX.md` | `archive/sessions/INDEX.md` | history: session logs and dailies, by date |
| 54 | `docs/sessions/LATEST.md` | `archive/sessions/LATEST.md` | history: session logs and dailies, by date |
| 55 | `presentation/CSE598_Group10_progress_Presentation_v2.pptx` | `archive/progress-round/presentation/CSE598_Group10_progress_Presentation_v2.pptx` | history: the Oct progress presentation and its assets |
| 56 | `presentation/CSE598_Group10_progress_Presentation_v3.pptx` | `archive/progress-round/presentation/CSE598_Group10_progress_Presentation_v3.pptx` | history: the Oct progress presentation and its assets |
| 57 | `presentation/CSE598_progress_presentation.pptx` | `archive/progress-round/presentation/CSE598_progress_presentation.pptx` | history: the Oct progress presentation and its assets |
| 58 | `presentation/build_deck.js` | `archive/progress-round/presentation/build_deck.js` | history: the Oct progress presentation and its assets |
| 59 | `presentation/package-lock.json` | `archive/progress-round/presentation/package-lock.json` | history: the Oct progress presentation and its assets |
| 60 | `presentation/package.json` | `archive/progress-round/presentation/package.json` | history: the Oct progress presentation and its assets |
| 61 | `presentation/progress/evidence_viewer.html` | `archive/progress-round/presentation/progress/evidence_viewer.html` | history: the Oct progress presentation and its assets |
| 62 | `presentation/progress/figures/F1_pilot_hint_following.png` | `archive/progress-round/presentation/progress/figures/F1_pilot_hint_following.png` | history: the Oct progress presentation and its assets |
| 63 | `presentation/progress/figures/F1_pilot_hint_following.svg` | `archive/progress-round/presentation/progress/figures/F1_pilot_hint_following.svg` | history: the Oct progress presentation and its assets |
| 64 | `presentation/progress/figures/F2_pilot_mentions_by_channel.png` | `archive/progress-round/presentation/progress/figures/F2_pilot_mentions_by_channel.png` | history: the Oct progress presentation and its assets |
| 65 | `presentation/progress/figures/F2_pilot_mentions_by_channel.svg` | `archive/progress-round/presentation/progress/figures/F2_pilot_mentions_by_channel.svg` | history: the Oct progress presentation and its assets |
| 66 | `presentation/progress/figures/F3_pilot_answer_only.png` | `archive/progress-round/presentation/progress/figures/F3_pilot_answer_only.png` | history: the Oct progress presentation and its assets |
| 67 | `presentation/progress/figures/F3_pilot_answer_only.svg` | `archive/progress-round/presentation/progress/figures/F3_pilot_answer_only.svg` | history: the Oct progress presentation and its assets |
| 68 | `presentation/progress/figures/F4_pilot_length_with_hint.png` | `archive/progress-round/presentation/progress/figures/F4_pilot_length_with_hint.png` | history: the Oct progress presentation and its assets |
| 69 | `presentation/progress/figures/F4_pilot_length_with_hint.svg` | `archive/progress-round/presentation/progress/figures/F4_pilot_length_with_hint.svg` | history: the Oct progress presentation and its assets |
| 70 | `presentation/progress/figures/F5_pilot_truncation_leak.png` | `archive/progress-round/presentation/progress/figures/F5_pilot_truncation_leak.png` | history: the Oct progress presentation and its assets |
| 71 | `presentation/progress/figures/F5_pilot_truncation_leak.svg` | `archive/progress-round/presentation/progress/figures/F5_pilot_truncation_leak.svg` | history: the Oct progress presentation and its assets |
| 72 | `presentation/progress/figures/F6_timing_and_tokens.png` | `archive/progress-round/presentation/progress/figures/F6_timing_and_tokens.png` | history: the Oct progress presentation and its assets |
| 73 | `presentation/progress/figures/F6_timing_and_tokens.svg` | `archive/progress-round/presentation/progress/figures/F6_timing_and_tokens.svg` | history: the Oct progress presentation and its assets |
| 74 | `presentation/progress/figures/F7_expA_reviewer_arms.png` | `archive/progress-round/presentation/progress/figures/F7_expA_reviewer_arms.png` | history: the Oct progress presentation and its assets |
| 75 | `presentation/progress/figures/F7_expA_reviewer_arms.svg` | `archive/progress-round/presentation/progress/figures/F7_expA_reviewer_arms.svg` | history: the Oct progress presentation and its assets |
| 76 | `presentation/progress/figures/F8_expB_item_groups.png` | `archive/progress-round/presentation/progress/figures/F8_expB_item_groups.png` | history: the Oct progress presentation and its assets |
| 77 | `presentation/progress/figures/F8_expB_item_groups.svg` | `archive/progress-round/presentation/progress/figures/F8_expB_item_groups.svg` | history: the Oct progress presentation and its assets |
| 78 | `presentation/progress/figures/F9_expB_cue_by_channel.png` | `archive/progress-round/presentation/progress/figures/F9_expB_cue_by_channel.png` | history: the Oct progress presentation and its assets |
| 79 | `presentation/progress/figures/F9_expB_cue_by_channel.svg` | `archive/progress-round/presentation/progress/figures/F9_expB_cue_by_channel.svg` | history: the Oct progress presentation and its assets |
| 80 | `presentation/progress/screenshots/01_card-counters.png` | `archive/progress-round/presentation/progress/screenshots/01_card-counters.png` | history: the Oct progress presentation and its assets |
| 81 | `presentation/progress/screenshots/02_card-pilot-steered.png` | `archive/progress-round/presentation/progress/screenshots/02_card-pilot-steered.png` | history: the Oct progress presentation and its assets |
| 82 | `presentation/progress/screenshots/03_card-two-channels.png` | `archive/progress-round/presentation/progress/screenshots/03_card-two-channels.png` | history: the Oct progress presentation and its assets |
| 83 | `presentation/progress/screenshots/04_card-truncation.png` | `archive/progress-round/presentation/progress/screenshots/04_card-truncation.png` | history: the Oct progress presentation and its assets |
| 84 | `presentation/progress/screenshots/05_card-reviewer.png` | `archive/progress-round/presentation/progress/screenshots/05_card-reviewer.png` | history: the Oct progress presentation and its assets |
| 85 | `presentation/progress/screenshots/06_card-expB-tool.png` | `archive/progress-round/presentation/progress/screenshots/06_card-expB-tool.png` | history: the Oct progress presentation and its assets |
| 86 | `presentation/progress/screenshots/07_card-terminal.png` | `archive/progress-round/presentation/progress/screenshots/07_card-terminal.png` | history: the Oct progress presentation and its assets |
| 87 | `presentation/progress/screenshots/fig_F1_pilot_hint_following.png` | `archive/progress-round/presentation/progress/screenshots/fig_F1_pilot_hint_following.png` | history: the Oct progress presentation and its assets |
| 88 | `presentation/progress/screenshots/fig_F2_pilot_mentions_by_channel.png` | `archive/progress-round/presentation/progress/screenshots/fig_F2_pilot_mentions_by_channel.png` | history: the Oct progress presentation and its assets |
| 89 | `presentation/progress/screenshots/fig_F3_pilot_answer_only.png` | `archive/progress-round/presentation/progress/screenshots/fig_F3_pilot_answer_only.png` | history: the Oct progress presentation and its assets |
| 90 | `presentation/progress/screenshots/fig_F4_pilot_length_with_hint.png` | `archive/progress-round/presentation/progress/screenshots/fig_F4_pilot_length_with_hint.png` | history: the Oct progress presentation and its assets |
| 91 | `presentation/progress/screenshots/fig_F5_pilot_truncation_leak.png` | `archive/progress-round/presentation/progress/screenshots/fig_F5_pilot_truncation_leak.png` | history: the Oct progress presentation and its assets |
| 92 | `presentation/progress/screenshots/fig_F6_timing_and_tokens.png` | `archive/progress-round/presentation/progress/screenshots/fig_F6_timing_and_tokens.png` | history: the Oct progress presentation and its assets |
| 93 | `presentation/progress/screenshots/fig_F7_expA_reviewer_arms.png` | `archive/progress-round/presentation/progress/screenshots/fig_F7_expA_reviewer_arms.png` | history: the Oct progress presentation and its assets |
| 94 | `presentation/progress/screenshots/fig_F8_expB_item_groups.png` | `archive/progress-round/presentation/progress/screenshots/fig_F8_expB_item_groups.png` | history: the Oct progress presentation and its assets |
| 95 | `presentation/progress/screenshots/fig_F9_expB_cue_by_channel.png` | `archive/progress-round/presentation/progress/screenshots/fig_F9_expB_cue_by_channel.png` | history: the Oct progress presentation and its assets |
| 96 | `presentation/progress/screenshots/full_page.png` | `archive/progress-round/presentation/progress/screenshots/full_page.png` | history: the Oct progress presentation and its assets |
| 97 | `presentation/progress/ui_screenshots/1_question_and_hint.png` | `archive/progress-round/presentation/progress/ui_screenshots/1_question_and_hint.png` | history: the Oct progress presentation and its assets |
| 98 | `presentation/progress/ui_screenshots/1_question_and_hint_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/1_question_and_hint_1280x720.png` | history: the Oct progress presentation and its assets |
| 99 | `presentation/progress/ui_screenshots/2_fell_for_it.png` | `archive/progress-round/presentation/progress/ui_screenshots/2_fell_for_it.png` | history: the Oct progress presentation and its assets |
| 100 | `presentation/progress/ui_screenshots/2_fell_for_it_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/2_fell_for_it_1280x720.png` | history: the Oct progress presentation and its assets |
| 101 | `presentation/progress/ui_screenshots/3_kept_right_answer.png` | `archive/progress-round/presentation/progress/ui_screenshots/3_kept_right_answer.png` | history: the Oct progress presentation and its assets |
| 102 | `presentation/progress/ui_screenshots/3_kept_right_answer_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/3_kept_right_answer_1280x720.png` | history: the Oct progress presentation and its assets |
| 103 | `presentation/progress/ui_screenshots/4_numbers.png` | `archive/progress-round/presentation/progress/ui_screenshots/4_numbers.png` | history: the Oct progress presentation and its assets |
| 104 | `presentation/progress/ui_screenshots/4_numbers_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/4_numbers_1280x720.png` | history: the Oct progress presentation and its assets |
| 105 | `presentation/progress/ui_screenshots/5_live.png` | `archive/progress-round/presentation/progress/ui_screenshots/5_live.png` | history: the Oct progress presentation and its assets |
| 106 | `presentation/progress/ui_screenshots/5_live_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/5_live_1280x720.png` | history: the Oct progress presentation and its assets |
| 107 | `presentation/progress/ui_screenshots/charts.png` | `archive/progress-round/presentation/progress/ui_screenshots/charts.png` | history: the Oct progress presentation and its assets |
| 108 | `presentation/progress/ui_screenshots/charts_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/charts_1280x720.png` | history: the Oct progress presentation and its assets |
| 109 | `presentation/progress/ui_screenshots/demo_1_eng-qwen.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_1_eng-qwen.png` | history: the Oct progress presentation and its assets |
| 110 | `presentation/progress/ui_screenshots/demo_1_eng-qwen_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_1_eng-qwen_1280x720.png` | history: the Oct progress presentation and its assets |
| 111 | `presentation/progress/ui_screenshots/demo_2_eng-olmo.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_2_eng-olmo.png` | history: the Oct progress presentation and its assets |
| 112 | `presentation/progress/ui_screenshots/demo_2_eng-olmo_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_2_eng-olmo_1280x720.png` | history: the Oct progress presentation and its assets |
| 113 | `presentation/progress/ui_screenshots/demo_3_law-olmo.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_3_law-olmo.png` | history: the Oct progress presentation and its assets |
| 114 | `presentation/progress/ui_screenshots/demo_3_law-olmo_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_3_law-olmo_1280x720.png` | history: the Oct progress presentation and its assets |
| 115 | `presentation/progress/ui_screenshots/demo_4_law-qwen.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_4_law-qwen.png` | history: the Oct progress presentation and its assets |
| 116 | `presentation/progress/ui_screenshots/demo_4_law-qwen_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_4_law-qwen_1280x720.png` | history: the Oct progress presentation and its assets |
| 117 | `presentation/progress/ui_screenshots/demo_5_puzzle3.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_5_puzzle3.png` | history: the Oct progress presentation and its assets |
| 118 | `presentation/progress/ui_screenshots/demo_5_puzzle3_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_5_puzzle3_1280x720.png` | history: the Oct progress presentation and its assets |
| 119 | `presentation/progress/ui_screenshots/demo_6_puzzle21.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_6_puzzle21.png` | history: the Oct progress presentation and its assets |
| 120 | `presentation/progress/ui_screenshots/demo_6_puzzle21_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_6_puzzle21_1280x720.png` | history: the Oct progress presentation and its assets |
| 121 | `docs/OVERVIEW.md` | `archive/superseded/OVERVIEW_2026-10-27.md` | superseded: an Oct 27 snapshot; its status, findings, traps and code map now live in FINDINGS, PLAN, STATUS and cot-disclosure/README |
| 122 | `docs/paper/README.md` | `archive/merged-docs/paper_README.md` | merged into the root README's map (a 14-line index of the paper pack) |
| 123 | `cot-disclosure/ui/README.md` | `archive/progress-round/ui_demo_README.md` | the progress round's demo guide; the ui/ code stays, cot-disclosure/README points to it |
| 124 | `cot-disclosure/finetune/README.md` | `docs/TRACK_A.md` | Track A's design doc, with the other living docs; not a folder front door |
| 125 | `cot-disclosure/finetune/PROVENANCE.md` | `docs/TRACK_A_PROVENANCE.md` | B1/B2's method doc, beside Track A's |
| 126 | `docs/progress/STATUS.md` | `docs/STATUS.md` | living status, beside FINDINGS, PLAN and TODO (make_gantt.py writes it) |
| 127 | `docs/progress/GANTT.xlsx` | `docs/GANTT.xlsx` | living status (make_gantt.py writes it) |
| 128 | `docs/progress/gantt.png` | `docs/gantt.png` | living status (make_gantt.py writes it) |
| 129 | `cot-disclosure/results/pilot_stdout.txt` | `archive/progress-round/results/pilot_stdout.txt` | progress-round console log; no code reads it |
| 130 | `cot-disclosure/results/pilot_stdout_v2.txt` | `archive/progress-round/results/pilot_stdout_v2.txt` | progress-round console log; no code reads it |
| 131 | `cot-disclosure/results/progress_log.txt` | `archive/progress-round/results/progress_log.txt` | progress-round console log; no code reads it |


## d. What has to change because of it

**Doc links** (found by `tools/check_links.py` after the moves):
- the root README (4 links);
- `cot-disclosure/README.md` (3);
- the Sol kit README (1, to PROVENANCE);
- FINDINGS (5: OVERVIEW, session logs);
- PLAN (1), RUNBOOK (3), TODO (4);
- INDEX.md's rows (now into date folders);
- links inside the moved logs;
- the handoffs (log names).
- The supplement (`EVIDENCE`, `PREREGISTRATIONS`, `DEVIATIONS`, `TRAPS`) is regenerated, not hand-edited.

**Tools (code under `cot-disclosure/tools/`; none is used by Sol):**
- `make_supplement.py`: the sessions path (`docs/sessions` → `archive/sessions`, read recursively), its link
  prefixes, `presentation/` in its path check, and the curated DEVIATIONS sources.
- `make_gantt.py`:
  - the sessions path (recursive);
  - the dailies' glob;
  - `docs/OVERVIEW.md` → `archive/superseded/OVERVIEW_2026-10-27.md`;
  - its output folder `docs/progress` → `docs/`.
- `check_links.py`: none (RUNBOOK stays at `docs/RUNBOOK.md`).
- `make_handoff_bundle.py`: none (it bundles produced data only).
- `export_summaries.py`: none.

**Progress-round scripts (not Sol)** that write into `presentation/`: `analyze_progress.py`,
`build_evidence_viewer.py`, `extract_slides.py`, `make_bundle.py`, `take_screenshots.py`. They point at
`archive/progress-round/presentation/`.

**Root `.gitignore`:** `!/archive/` added; `!/presentation/` and the `presentation/…` patterns repointed.

**Text-only mentions in code docstrings** (no logic, no path read at run time):
- `agents/c15.py`–`c18.py`, `progress/run_b15.py`: their pre-registration logs' new paths.
- `finetune/__init__.py`, `finetune/source_tags.py`: "finetune/README.md" → "docs/TRACK_A.md".
- `finetune/gpu/checkpoint_check.py`: an output string naming `docs/OVERVIEW.md §5`.

The last three are files Sol's jobs import. Only comment and docstring text changes, and Ritik isn't pulling until
the queue is done, so they are listed rather than left stale.

**RUNBOOK** (§20, session logs) and **the handoffs** (log names, the Track A doc's path) are updated.

**Sol:** a `git pull` changes no code path the queued jobs use.
- The jobs (provenance_gen, eval tags/lora_tags/lora_attn3, later qwen8b) read `cot-disclosure/finetune/**`,
  `providers/`, `progress/sol_trackB.py`, `agents/sol_c13.py`, `configs/`, `data/`, and the gitignored
  `results/trackA|B`.
- No moved file is in those paths, except two docs inside `finetune/` (README.md, PROVENANCE.md) that no code opens.

## e. Before and after (tracked files)

| | before | after |
|---|---|---|
| root (files + folders) | 2 files, 3 folders (cot-disclosure, docs, presentation) | 2 files, 3 folders (cot-disclosure, docs, archive) |
| `docs/` | 129 (5 at its root; sessions 54, paper 60, progress 7, handoff 3) | 76 (10 at its root; paper 59, progress 4, handoff 3) |
| `cot-disclosure/` | 385 (6 READMEs and docs inside) | 379 (2 READMEs: the code, the Sol kit) |
| `archive/` | — | 126 |
| total | 582 | 583 (+ `docs/MOVES.md`; nothing removed) |

## Also asked (Ritik, 21:40)

**Track C, cleaned further before it goes to Shrey** (nothing has been sent yet):
- **TRACK_C.md** becomes a short front page:
  - the question and the answer in five lines;
  - one results table (C4 → C18);
  - the deployment reading;
  - the first day;
  - his plan.
- **Reference material** goes in a closing reference part: setup details, inherited decisions, traps, the bundle's
  contents.
- **Out:** the development history (Experiment A, C1 and smoke counts, per-date code changes). It stays in FINDINGS
  and the archived logs.
- **One map of the files he needs:** `agents/`, the summaries, `SOL_SETUP.md`, the bundle.
- **The root README** points him there. The handoff note is rewritten after the moves, with the new paths and no
  "paths moved" caveat, since he hasn't seen the old ones.

**The Gantt, more detailed about what's done and what's left:**
- **The Gantt sheet at task level:** one row and bar per task (not per phase), with its status, dates, owner and a
  short label.
- **A "Done" sheet:** every completed task with its date, owner, what it delivered (the finding and its key number)
  and its evidence (F-number, session log, commit).
- **A "To do" sheet:** every open task with its next concrete action, owner, due date, estimate, dependency and
  blocker, sorted by due date. What each gate needs (Gate 2, Nov 8; Gate 3, Nov 22; the report) as its own rows.
- **STATUS.md:**
  - per track, "done since Oct 27" (dated bullets with numbers), "next" (ordered), and "blocked on";
  - a per-owner list.
- **gantt.png** becomes an overview page plus one page per track with task-level bars.
- **TODO's stale statuses** are fixed first (e.g. A13 says S2 is pending, A34 says it passed), so the sheet reads
  right.
