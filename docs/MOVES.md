# Moves: every file moved on Oct 30, 2026, and why

The repository was reorganized on Oct 30, 2026 (By: Ritik; session log
[`2026-10-30_2230_ALL_reorg-applied.md`](../archive/sessions/2026-10-30/2026-10-30_2230_ALL_reorg-applied.md); the proposal:
[`2026-10-30_2141_ALL_reorg-proposal.md`](../archive/sessions/2026-10-30/2026-10-30_2141_ALL_reorg-proposal.md)).
**Rules:**
- every move was a `git mv`, so `git log --follow <new path>` shows a file's whole history; nothing was deleted;
- no code, test, config or sbatch file moved, nor anything a Sol job reads;
- produced data was untouched;
- numbers-only summaries that code reads stayed where they were.

## Merged

- **`docs/paper/README.md`** (a 14-line index of the paper pack) was merged into the root `README.md`'s folder
  map, which lists every file it listed, with the same descriptions, the figures and the command that makes them.
  The original is kept unchanged at `archive/merged-docs/paper_README.md`. **Dropped as duplicates:** none; every
  line of it is in the root README.

## Rewritten in place, with the earlier version kept

- **`README.md`** became the front door: what the project is, the story in five lines, where to start, the folders.
  The Oct 27 version is kept at `archive/superseded/README_2026-10-27.md`, word for word; only its link targets
  were changed, so they resolve from the new folder. Its findings list (F1–F14) is
  in `docs/FINDINGS.md`; its Oct 27 plan is in `docs/PLAN.md`.
- **`docs/handoff/TRACK_C.md`** was shortened to a front page and a reference part, before Shrey received it. The
  longer version is kept at `archive/superseded/TRACK_C_2026-10-30_long.md`, word for word; only its link targets
  were changed, so they resolve from the new folder. Its story is in
  `docs/FINDINGS.md`, F18–F34.

## Moved (131 files)

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
| 55 | `presentation/CSE598_Group10_progress_Presentation_v2.pptx` | `archive/progress-round/presentation/CSE598_Group10_progress_Presentation_v2.pptx` | history: the October progress presentation and its assets |
| 56 | `presentation/CSE598_Group10_progress_Presentation_v3.pptx` | `archive/progress-round/presentation/CSE598_Group10_progress_Presentation_v3.pptx` | history: the October progress presentation and its assets |
| 57 | `presentation/CSE598_progress_presentation.pptx` | `archive/progress-round/presentation/CSE598_progress_presentation.pptx` | history: the October progress presentation and its assets |
| 58 | `presentation/build_deck.js` | `archive/progress-round/presentation/build_deck.js` | history: the October progress presentation and its assets |
| 59 | `presentation/package-lock.json` | `archive/progress-round/presentation/package-lock.json` | history: the October progress presentation and its assets |
| 60 | `presentation/package.json` | `archive/progress-round/presentation/package.json` | history: the October progress presentation and its assets |
| 61 | `presentation/progress/evidence_viewer.html` | `archive/progress-round/presentation/progress/evidence_viewer.html` | history: the October progress presentation and its assets |
| 62 | `presentation/progress/figures/F1_pilot_hint_following.png` | `archive/progress-round/presentation/progress/figures/F1_pilot_hint_following.png` | history: the October progress presentation and its assets |
| 63 | `presentation/progress/figures/F1_pilot_hint_following.svg` | `archive/progress-round/presentation/progress/figures/F1_pilot_hint_following.svg` | history: the October progress presentation and its assets |
| 64 | `presentation/progress/figures/F2_pilot_mentions_by_channel.png` | `archive/progress-round/presentation/progress/figures/F2_pilot_mentions_by_channel.png` | history: the October progress presentation and its assets |
| 65 | `presentation/progress/figures/F2_pilot_mentions_by_channel.svg` | `archive/progress-round/presentation/progress/figures/F2_pilot_mentions_by_channel.svg` | history: the October progress presentation and its assets |
| 66 | `presentation/progress/figures/F3_pilot_answer_only.png` | `archive/progress-round/presentation/progress/figures/F3_pilot_answer_only.png` | history: the October progress presentation and its assets |
| 67 | `presentation/progress/figures/F3_pilot_answer_only.svg` | `archive/progress-round/presentation/progress/figures/F3_pilot_answer_only.svg` | history: the October progress presentation and its assets |
| 68 | `presentation/progress/figures/F4_pilot_length_with_hint.png` | `archive/progress-round/presentation/progress/figures/F4_pilot_length_with_hint.png` | history: the October progress presentation and its assets |
| 69 | `presentation/progress/figures/F4_pilot_length_with_hint.svg` | `archive/progress-round/presentation/progress/figures/F4_pilot_length_with_hint.svg` | history: the October progress presentation and its assets |
| 70 | `presentation/progress/figures/F5_pilot_truncation_leak.png` | `archive/progress-round/presentation/progress/figures/F5_pilot_truncation_leak.png` | history: the October progress presentation and its assets |
| 71 | `presentation/progress/figures/F5_pilot_truncation_leak.svg` | `archive/progress-round/presentation/progress/figures/F5_pilot_truncation_leak.svg` | history: the October progress presentation and its assets |
| 72 | `presentation/progress/figures/F6_timing_and_tokens.png` | `archive/progress-round/presentation/progress/figures/F6_timing_and_tokens.png` | history: the October progress presentation and its assets |
| 73 | `presentation/progress/figures/F6_timing_and_tokens.svg` | `archive/progress-round/presentation/progress/figures/F6_timing_and_tokens.svg` | history: the October progress presentation and its assets |
| 74 | `presentation/progress/figures/F7_expA_reviewer_arms.png` | `archive/progress-round/presentation/progress/figures/F7_expA_reviewer_arms.png` | history: the October progress presentation and its assets |
| 75 | `presentation/progress/figures/F7_expA_reviewer_arms.svg` | `archive/progress-round/presentation/progress/figures/F7_expA_reviewer_arms.svg` | history: the October progress presentation and its assets |
| 76 | `presentation/progress/figures/F8_expB_item_groups.png` | `archive/progress-round/presentation/progress/figures/F8_expB_item_groups.png` | history: the October progress presentation and its assets |
| 77 | `presentation/progress/figures/F8_expB_item_groups.svg` | `archive/progress-round/presentation/progress/figures/F8_expB_item_groups.svg` | history: the October progress presentation and its assets |
| 78 | `presentation/progress/figures/F9_expB_cue_by_channel.png` | `archive/progress-round/presentation/progress/figures/F9_expB_cue_by_channel.png` | history: the October progress presentation and its assets |
| 79 | `presentation/progress/figures/F9_expB_cue_by_channel.svg` | `archive/progress-round/presentation/progress/figures/F9_expB_cue_by_channel.svg` | history: the October progress presentation and its assets |
| 80 | `presentation/progress/screenshots/01_card-counters.png` | `archive/progress-round/presentation/progress/screenshots/01_card-counters.png` | history: the October progress presentation and its assets |
| 81 | `presentation/progress/screenshots/02_card-pilot-steered.png` | `archive/progress-round/presentation/progress/screenshots/02_card-pilot-steered.png` | history: the October progress presentation and its assets |
| 82 | `presentation/progress/screenshots/03_card-two-channels.png` | `archive/progress-round/presentation/progress/screenshots/03_card-two-channels.png` | history: the October progress presentation and its assets |
| 83 | `presentation/progress/screenshots/04_card-truncation.png` | `archive/progress-round/presentation/progress/screenshots/04_card-truncation.png` | history: the October progress presentation and its assets |
| 84 | `presentation/progress/screenshots/05_card-reviewer.png` | `archive/progress-round/presentation/progress/screenshots/05_card-reviewer.png` | history: the October progress presentation and its assets |
| 85 | `presentation/progress/screenshots/06_card-expB-tool.png` | `archive/progress-round/presentation/progress/screenshots/06_card-expB-tool.png` | history: the October progress presentation and its assets |
| 86 | `presentation/progress/screenshots/07_card-terminal.png` | `archive/progress-round/presentation/progress/screenshots/07_card-terminal.png` | history: the October progress presentation and its assets |
| 87 | `presentation/progress/screenshots/fig_F1_pilot_hint_following.png` | `archive/progress-round/presentation/progress/screenshots/fig_F1_pilot_hint_following.png` | history: the October progress presentation and its assets |
| 88 | `presentation/progress/screenshots/fig_F2_pilot_mentions_by_channel.png` | `archive/progress-round/presentation/progress/screenshots/fig_F2_pilot_mentions_by_channel.png` | history: the October progress presentation and its assets |
| 89 | `presentation/progress/screenshots/fig_F3_pilot_answer_only.png` | `archive/progress-round/presentation/progress/screenshots/fig_F3_pilot_answer_only.png` | history: the October progress presentation and its assets |
| 90 | `presentation/progress/screenshots/fig_F4_pilot_length_with_hint.png` | `archive/progress-round/presentation/progress/screenshots/fig_F4_pilot_length_with_hint.png` | history: the October progress presentation and its assets |
| 91 | `presentation/progress/screenshots/fig_F5_pilot_truncation_leak.png` | `archive/progress-round/presentation/progress/screenshots/fig_F5_pilot_truncation_leak.png` | history: the October progress presentation and its assets |
| 92 | `presentation/progress/screenshots/fig_F6_timing_and_tokens.png` | `archive/progress-round/presentation/progress/screenshots/fig_F6_timing_and_tokens.png` | history: the October progress presentation and its assets |
| 93 | `presentation/progress/screenshots/fig_F7_expA_reviewer_arms.png` | `archive/progress-round/presentation/progress/screenshots/fig_F7_expA_reviewer_arms.png` | history: the October progress presentation and its assets |
| 94 | `presentation/progress/screenshots/fig_F8_expB_item_groups.png` | `archive/progress-round/presentation/progress/screenshots/fig_F8_expB_item_groups.png` | history: the October progress presentation and its assets |
| 95 | `presentation/progress/screenshots/fig_F9_expB_cue_by_channel.png` | `archive/progress-round/presentation/progress/screenshots/fig_F9_expB_cue_by_channel.png` | history: the October progress presentation and its assets |
| 96 | `presentation/progress/screenshots/full_page.png` | `archive/progress-round/presentation/progress/screenshots/full_page.png` | history: the October progress presentation and its assets |
| 97 | `presentation/progress/ui_screenshots/1_question_and_hint.png` | `archive/progress-round/presentation/progress/ui_screenshots/1_question_and_hint.png` | history: the October progress presentation and its assets |
| 98 | `presentation/progress/ui_screenshots/1_question_and_hint_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/1_question_and_hint_1280x720.png` | history: the October progress presentation and its assets |
| 99 | `presentation/progress/ui_screenshots/2_fell_for_it.png` | `archive/progress-round/presentation/progress/ui_screenshots/2_fell_for_it.png` | history: the October progress presentation and its assets |
| 100 | `presentation/progress/ui_screenshots/2_fell_for_it_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/2_fell_for_it_1280x720.png` | history: the October progress presentation and its assets |
| 101 | `presentation/progress/ui_screenshots/3_kept_right_answer.png` | `archive/progress-round/presentation/progress/ui_screenshots/3_kept_right_answer.png` | history: the October progress presentation and its assets |
| 102 | `presentation/progress/ui_screenshots/3_kept_right_answer_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/3_kept_right_answer_1280x720.png` | history: the October progress presentation and its assets |
| 103 | `presentation/progress/ui_screenshots/4_numbers.png` | `archive/progress-round/presentation/progress/ui_screenshots/4_numbers.png` | history: the October progress presentation and its assets |
| 104 | `presentation/progress/ui_screenshots/4_numbers_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/4_numbers_1280x720.png` | history: the October progress presentation and its assets |
| 105 | `presentation/progress/ui_screenshots/5_live.png` | `archive/progress-round/presentation/progress/ui_screenshots/5_live.png` | history: the October progress presentation and its assets |
| 106 | `presentation/progress/ui_screenshots/5_live_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/5_live_1280x720.png` | history: the October progress presentation and its assets |
| 107 | `presentation/progress/ui_screenshots/charts.png` | `archive/progress-round/presentation/progress/ui_screenshots/charts.png` | history: the October progress presentation and its assets |
| 108 | `presentation/progress/ui_screenshots/charts_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/charts_1280x720.png` | history: the October progress presentation and its assets |
| 109 | `presentation/progress/ui_screenshots/demo_1_eng-qwen.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_1_eng-qwen.png` | history: the October progress presentation and its assets |
| 110 | `presentation/progress/ui_screenshots/demo_1_eng-qwen_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_1_eng-qwen_1280x720.png` | history: the October progress presentation and its assets |
| 111 | `presentation/progress/ui_screenshots/demo_2_eng-olmo.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_2_eng-olmo.png` | history: the October progress presentation and its assets |
| 112 | `presentation/progress/ui_screenshots/demo_2_eng-olmo_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_2_eng-olmo_1280x720.png` | history: the October progress presentation and its assets |
| 113 | `presentation/progress/ui_screenshots/demo_3_law-olmo.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_3_law-olmo.png` | history: the October progress presentation and its assets |
| 114 | `presentation/progress/ui_screenshots/demo_3_law-olmo_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_3_law-olmo_1280x720.png` | history: the October progress presentation and its assets |
| 115 | `presentation/progress/ui_screenshots/demo_4_law-qwen.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_4_law-qwen.png` | history: the October progress presentation and its assets |
| 116 | `presentation/progress/ui_screenshots/demo_4_law-qwen_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_4_law-qwen_1280x720.png` | history: the October progress presentation and its assets |
| 117 | `presentation/progress/ui_screenshots/demo_5_puzzle3.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_5_puzzle3.png` | history: the October progress presentation and its assets |
| 118 | `presentation/progress/ui_screenshots/demo_5_puzzle3_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_5_puzzle3_1280x720.png` | history: the October progress presentation and its assets |
| 119 | `presentation/progress/ui_screenshots/demo_6_puzzle21.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_6_puzzle21.png` | history: the October progress presentation and its assets |
| 120 | `presentation/progress/ui_screenshots/demo_6_puzzle21_1280x720.png` | `archive/progress-round/presentation/progress/ui_screenshots/demo_6_puzzle21_1280x720.png` | history: the October progress presentation and its assets |
| 121 | `docs/OVERVIEW.md` | `archive/superseded/OVERVIEW_2026-10-27.md` | superseded: the Oct 27 snapshot; its status, findings, traps and code map now live in FINDINGS, PLAN, STATUS and cot-disclosure/README.md |
| 122 | `docs/paper/README.md` | `archive/merged-docs/paper_README.md` | merged into the root README's folder map (a 14-line index of the paper pack); the original kept unchanged |
| 123 | `cot-disclosure/ui/README.md` | `archive/progress-round/ui_demo_README.md` | the progress round's demo guide; the ui/ code stays and cot-disclosure/README.md points here |
| 124 | `cot-disclosure/finetune/README.md` | `docs/TRACK_A.md` | Track A's design doc, with the other living docs (only the code and the Sol kit keep a README) |
| 125 | `cot-disclosure/finetune/PROVENANCE.md` | `docs/TRACK_A_PROVENANCE.md` | B1/B2's method doc, beside Track A's |
| 126 | `docs/progress/STATUS.md` | `docs/STATUS.md` | living status, beside FINDINGS, PLAN and TODO (tools/make_gantt.py writes it) |
| 127 | `docs/progress/GANTT.xlsx` | `docs/GANTT.xlsx` | living status (tools/make_gantt.py writes it) |
| 128 | `docs/progress/gantt.png` | `docs/gantt.png` | living status (tools/make_gantt.py writes it) |
| 129 | `cot-disclosure/results/pilot_stdout.txt` | `archive/progress-round/results/pilot_stdout.txt` | a progress-round console log no code reads |
| 130 | `cot-disclosure/results/pilot_stdout_v2.txt` | `archive/progress-round/results/pilot_stdout_v2.txt` | a progress-round console log no code reads |
| 131 | `cot-disclosure/results/progress_log.txt` | `archive/progress-round/results/progress_log.txt` | a progress-round console log no code reads |
