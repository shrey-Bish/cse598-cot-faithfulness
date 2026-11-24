# 04. Figures: every figure, where it comes from, where it goes

Facts only, for the presentation pack. Gathered Nov 24 from the frozen results (tag `results-freeze-2026-11-18` on `7e1fdc0`); no figure was redrawn and no number was changed. Every result number below is copied word for word from [`docs/FINDINGS.md`](../../FINDINGS.md) (through [`results_at_a_glance.md`](../../paper/tables/results_at_a_glance.md), whose rows are FINDINGS' own words), with its finding ID. A figure with no number here has its numbers in its own CSV.

## How to read this page

- **Count.** `docs/paper/figures/` holds 29 PNGs (not 31), each with a `.svg` and a `.csv` beside it (the SVG is the 16:9, 960 x 540 point drawing; the PNG is 2000 x 1125). `docs/paper/supplement/figures/` holds 7 PNGs with the same trio. `docs/paper/figures/WAITING.md` is the specs page (it holds no image: the specs of the slide figures, with the dates each was made; check it before calling any figure final). Four more figures sit in Track B's and Track C's own folders (`docs/trackB/figures/authority_ladder.*`, `docs/trackC/figures/c19_authority.*`, `c25_hops.*`, `pipeline_vs_model.*`); they are the same files as the ones in `docs/paper/figures/` (placed at the merge).
- **Slides.** The slide column uses the planned list: S1 Title; S2 The question; S3 Setup; S4 Finding 1 (tools pull harder, and authority); S5 Finding 2 (private reasoning vs final answer; bare after a call); S6 Finding 3 (inside the model); S7 Finding 4 (reviewers defer, the checker holds); S8 Finding 5 (every fix is a trade); S9 The demo; S10 What's new and what isn't; S11 Limits; S12 Next steps; S13 Team. Backups: B1 why one model for the fixes; B2 the 42 hand-labelled rows; B3 multiple-choice only and the question sets; B4 related work; B5 are the demo's examples cherry-picked; B6 statistics and the second-model mechanism.
- **Report sections.** 1 Introduction, 2 Setup, 3 Methods, 4 The failure: tools pull harder, 5 Level 1 inside the model, 6 Level 2 in the words, 7 Fixing it, 8 Level 3 between agents, 9 Across agents and the pipeline, 10 Limits, 11 Related work, 12 Conclusion. The section is the one whose bullets cite the figure in [`docs/paper/REPORT.md`](../../paper/REPORT.md).
- **Slide-ready** means a 1920 px copy is in `docs/presentation/pack/figures/` (PNG, rendered from the SVG so the text is crisp; same file name as the source PNG; 16:9, 1920 x 1080; each under 400 KB). **Report/supplement only** means no copy was made.
- Interval convention in the figures (WAITING.md, FINDINGS): 95% bootstraps clustered by question (by item in Track C); X of Y on the bars.

## A. The 14 slide-ready figures

| # | figure (path under `docs/paper/figures/`) | what it shows, in one sentence | plain caption | data source | finding | slide | report section |
|---|---|---|---|---|---|---|---|
| 1 | `three_levels.png` | A diagram (no data) of where a wrong hint can show up: inside the model, in the model's words, between agents. | "Where did that answer come from? Three levels, three kinds of evidence." | `three_levels.csv` (level, where, evidence IDs); a diagram, no summary file | F11, F26, F32, F36 (level 1); F15, F25, F29, F35 (level 2); read since: F39, F42, F37 | S3 (S2 can reuse it) | 1 Introduction (REPORT line 23), 2 Setup |
| 2 | `gate2.png` | For each model, how far a hint in each channel (pasted tool output, the real call, the system turn) moves the answer above the user's hint. | "A hint from a tool moves thinking models more than the same hint from the user, in five models and three newer families." | `gate2.csv`; `cot-disclosure/results/summaries/trackB/trackB_report.json`, `trackB_report_by_set.json` (F15, F16, F17, F29); `b17_report.json` (F37); FB1 in `docs/trackB/FINDINGS_B.md` (Source bullet there) | F15, F16, F17, F29, F37, FB1 | S4 | 4 The failure (REPORT lines 244, 272, 282, 291, 301, 368) |
| 3 | `authority_ladder.png` | The hint's pull grows with the authority it claims (user's guess, classmate, answer key, official manual), and the tool is set against the same claim from the user. | "Most of a tool's pull is the authority it claims; the pull grows with the authority claimed." | `authority_ladder.csv` (its `source` column names `b16_report.json` and `b24_report.json` rows); `cot-disclosure/results/summaries/trackB/b16_report.json`, `b19_report.json`, `b24_report.json` | F35, F40 | S4 (second half) | 4 The failure (REPORT lines 348, 602); 6 |
| 4 | `cue_experiments_slide.png` | How much each change to what the reviewer sees (the solver naming the tool, a fixed sentence, removing the citing sentences) moves the Olmo and Qwen3 reviewers' corrections. | "The cue is the solver's citation of the tool, not the argument." | `cue_experiments_slide.csv` (beside it) and `docs/paper/supplement/figures/cue_experiments.csv`; `trackC/c16_summary.json`, `c17_summary.json`, `c18_summary.json` (F31, F33, F34 Source bullets) | F31, F33, F34 | S7 (second figure, or backup B6) | 8 Level 3 (REPORT lines 960, 968, 976) |
| 5 | `private_vs_final.png` | The private reasoning names the hint nearly every time; the final answer almost never does (Test 1 per model, and Test 2). | "The reasoning says it; the answer doesn't." | `private_vs_final.csv` (its `source` column: `pilot.mentions.<model>...` in `docs/labeling/RESULTS_SUMMARY.json`); `base_format_runs.jsonl` (F3 Source bullet) | F3 | S5 | 6 Level 2 (REPORT line 541) |
| 6 | `bare_after_call.png` | After the model makes its own tool call, its final answer is a bare letter that does not name the tool; one instruction brings the tool's name back but not a lower following rate. | "After a tool call, the answer goes bare." | `bare_after_call.csv`; `trackB_report.json`, `trackB_report_by_set.json`, `trackB_runs.jsonl` (F15, F16, F29); `b15_report.json` (F25); `team_c4_summary.json` for the C4 control (F15) | F15, F16, F25, F29 | S5 (second half) | 6 Level 2 (REPORT lines 513, 554, 561, 582, 588) |
| 7 | `readout_by_layer_slide.png` | Which layers carry the hint's effect at the takeover: panel a is the first test (9 questions), panel b the same readout on 16 new questions. | "The hint's effect is read at three full-attention layers: 15, 19 and 23." | `readout_by_layer_slide.csv`; `trackA/step10_handoff.json`, `step10_patching.json` (F11); `trackA/setA/step10_handoff.json`, `step10_patching.json` (F26) | F11, F12, F26, F32 | S6 | 5 Level 1 (REPORT lines 373, 453, 491) |
| 8 | `readout_qwen8b.png` | The same readout in a second model (Qwen3-8B): three layers chosen on the puzzles hold most of the drop on MMLU-Pro, and they are its own top three. | "It replicates in a second model, in its own layers." | `readout_qwen8b.csv`; `trackA/qwen8b_mech/qwen8b_readout.json`, `qwen8b_step10_patching.json` (F36 Source bullet) | F36 | S6 (second half; or backup B6) | 5 Level 1 (REPORT line 506) |
| 9 | `reviewer_by_prompt_slide.png` | How often the reviewer (Olmo 3.1 32B, Qwen3 30B Instruct) keeps correcting a wrong tool answer when it sees only the answer, the private reasoning, the tool log, an instruction to check the tool, or its own first answer. | "A reviewer that sees where the answer came from stops correcting it." | `reviewer_by_prompt_slide.csv`; `trackC/team_c4_summary.json` and the C9, C10 summaries (F18, F19, F21 Source bullets) | F18, F19, F21 | S7 | 8 Level 3 (REPORT lines 901, 909, 918) |
| 10 | `trackC_reviewers_slide.png` | The same check across six reviewers, on C4's cases and on 100 fresh items: only the two Olmo models defer. | "Deference follows the model family, not the size." | `trackC_reviewers_slide.csv`; `trackC/team_c11_summary.json`, `c15_summary.json`, `team_c13_granite_summary.json`, `team_c13_mistral_summary.json` (F22, F24, F30) | F22, F23, F24, F30 | S7 | 8 Level 3 (REPORT lines 883, 925, 933, 950) |
| 11 | `pipeline_vs_model.png` | Pipeline fixes against the checker: a tag naming the tool's letter (C20) and a retrieved passage in place of the answer key (C26). | "The checker that never sees the tool is the check that holds." | `pipeline_vs_model.csv` (also `docs/trackC/figures/pipeline_vs_model.csv`); `trackC/c20_summary.json`, `c26_summary.json` (FC3, FC4; `docs/trackC/FINDINGS_C.md`) | FC3, FC4 (and F24 for the checker) | S7 (the "checker holds" half) | 9 Across agents (REPORT lines 1064, 1080) |
| 12 | `tradeoff_e2.png` | Wrong hints followed against correct hints taken, for nine systems on E2 (a: pooled channels; b: the inserted tool turn only). **Exploratory (post hoc), labelled so on the figure.** | "Every fix is a trade: fewer wrong hints followed, but fewer right ones taken." | `tradeoff_e2.csv` (its first line names `tools/tradeoff.py`, `tradeoff_e2.json` and the Nov 7 20:20 log); no FINDINGS entry of its own | none of its own (exploratory; sits beside F41, F43, F44; REPORT §7 says it "replaces and qualifies no verdict") | S8 | 7 Fixing it (REPORT line 834) |
| 13 | `a40_e2_fixes.png` | On E2, consistency training (A40) and A40 with the one-line note against the one-line instruction and LoRA: following and correct-hint acceptance. | "Consistency training follows far fewer wrong hints, and takes fewer correct ones." | `a40_e2_fixes.csv`; `trackA/gpu/a39/a40_e2.json`, `a42_e2.json` (F41, F43 Source bullets) | F41, F43 | S8 | 7 Fixing it (REPORT lines 748, 768) |
| 14 | `gate3_vs_base_slide.png` | Each trained version against base on the held-out 30: wrong-hint following and no-hint accuracy. | "Every trained version passes; none beats a one-line instruction." | `gate3_vs_base_slide.csv`; `trackA/gpu/eval/gate3.json`, `gate3_table.md`, `eval_report.json` (F28 Source bullet); same rows as `cot-disclosure/results/summaries/trackA/gpu/eval/figures/gate3_vs_base.png` | F28 | S8 | 7 Fixing it (REPORT lines 641, 695) |

### Key numbers on the slide-ready figures (verbatim from FINDINGS, through results_at_a_glance.md)

- `gate2.png`, F15: Gate 2 pasted +35 [+24, +46], real call +31 [+22, +42]. F16: Gate 2 +21 [+12, +31], +90 [+83, +96]. F17: Gate 2 pasted +32 [+22, +42], inserted +21 [+13, +30]. F29: real call on − off +64 [+51, +75]; calls 145 vs 35 of 162. FB1: R1 clear in all 10 readings.
- `authority_ladder.png`, F40: manual − classmate +41 [+31, +51], +12 [+4, +20], +32 [+23, +41]. F35: tool − authority: Instruct's call +75 [+65, +85], Thinking pasted +12 [+5, +19], Olmo inserted −14 [−21, −6], three no difference.
- `private_vs_final.png`, F3: Test 1: private 208 of 216 vs final 8 of 216.
- `bare_after_call.png`, F15: bare after a call 51 of 54. F29: bare 138 of 145; names the tool in 0 of 143. F25: names the tool after a call: Thinking +47 [+30, +64], Instruct +70 [+59, +81].
- `readout_by_layer_slide.png`, F11: share at 15, 19, 23 at the takeover 0.90 [0.85, 0.96] (19 cuts, 9 questions). F26: 0.90 [0.76, 1.06] at 15, 19, 23 (31 cuts).
- `readout_qwen8b.png`, F36: layers 21, 22, 29 hold 0.70 [0.60, 0.83] on MMLU-Pro (14 questions).
- `reviewer_by_prompt_slide.png`, F18: Olmo 3.1 32B: 59 of 73 alone → 6 (−73 [−86, −58]) and 3 (−77 [−91, −61]); checker 73 of 75.
- `trackC_reviewers_slide.png`, F22: Olmo 3 7B Instruct 32 → 1 of 73, −42 [−58, −28]; Qwen3 30B Thinking +1 [−6, +10].
- `cue_experiments_slide.png`, F34: Olmo 25 vs 9 of 34, +47 [+29, +65].
- `pipeline_vs_model.png`, FC3: tag − checker, catches Olmo −19 [−30, −9]. FC4: follows: 19 of 55 vs 52 of 55, −60 [−73, −45].
- `a40_e2_fixes.png`, F41: A40 84 of 694 vs the instruction 237 of 713, following −21 [−26, −16]; acceptance 347 of 459 vs 431 of 476, −15 [−20, −10].
- `gate3_vs_base_slide.png`, F28: following − base: LoRA −10 [−16, −4], tags −6 [−10, −2], LoRA + tags −7 [−13, −1], LoRA 15/19/23 −7 [−13, −2]; prompt_only −13 [−21, −6].
- `tradeoff_e2.png`: no FINDINGS number (exploratory).

Notes on choices:
- `three_levels` is the only figure with no plotted data; its CSV lists the evidence IDs per level.
- `authority_ladder.png` replaced `b16_authority.png` on the slide (PLAN's map, slide 7); `b16_authority.png` stays as REPORT §4's F35 figure.
- `cue_experiments_slide.png` is not on the old deck's main slides (it is in the supplement and REPORT §8); it is included because FINDINGS (F31, F33, F34) and REPORT §8 cite it as the 16:9 version. Use it as a second figure on S7 or a backup.
- `tradeoff_e2.png` is slide-ready as a picture but exploratory: say "exploratory, post hoc" aloud and keep its label.
- All 14 were rendered 1920 px wide from the SVGs (Playwright, Chromium), pixel width checked with PIL: every file is 1920 x 1080.

## B. Report/supplement only (15 PNGs in `docs/paper/figures/`)

| figure | shows | data source | finding | slide (if any) | report section |
|---|---|---|---|---|---|
| `a39_e2_fixes.png` | A39 on E2 (120 fresh questions), panel a: each fix against base, following and acceptance | `a39_e2_fixes.csv`; `trackA/gpu/a39/a39_e2.json` (F44 Source) | F44 | backup (B1 or S8 detail) | 7 (REPORT line 802) |
| `a39_e2_parts.png` | A39 panel b: LoRA + note, wrapper parts, the combinations | `a39_e2_parts.csv`; `a39_e2.json` | F44 | backup | 7 (line 802) |
| `a39_mmlupro_30_fixes.png` | The same as `a39_e2_fixes` on the held-out 30 | `a39_mmlupro_30_fixes.csv`; `a39_mmlupro_30.json` | F44 | none | 7 (line 802) |
| `a39_mmlupro_30_parts.png` | The same as `a39_e2_parts` on the held-out 30 | `a39_mmlupro_30_parts.csv`; `a39_mmlupro_30.json` | F44 | none | 7 (line 802) |
| `b16_authority.png` | B16: the tool against the user making the same answer-key claim | `b16_authority.csv`; `trackB/b16_report.json` (F35 Source) | F35 | none (replaced by `authority_ladder` on S4) | 4 (line 317), 6 (line 597) |
| `b17_effort.png` | B17: gpt-oss-20b, low against high thinking effort: following on the real call, calls, bare answer | `b17_effort.csv`; `trackB/b17_report.json` (F37 Source) | F37 | none in the planned list (old deck slide 9; usable as a backup) | 4 (line 327), 6 (line 593) |
| `b1r2_vs_b1.png` | B1 (held-out 30) and B1R2 (E2) side by side: the attention cut and its acceptance cost | `b1r2_vs_b1.csv`; `trackA/gpu/provenance_gen/provenance_gen_report.json`, `gpu/b1r2/provenance_gen_report.json` (F38 Source) | F38 | backup B1 / B6 (old deck backup slide 16) | 7 (line 725) |
| `c19_authority.png` | C19: an answer-key claim against the same claim about the solver's own working, per reviewer | `c19_authority.csv` (also in `docs/trackC/figures/`); `trackC/c19_summary.json` (FC1 Source) | FC1 | none | 8 (line 993) |
| `c25_hops.png` | C25: whether the tool stays named as the source at each hop (solver, plain note, keep note) and what the decider accepts | `c25_hops.csv` (also in `docs/trackC/figures/`); `trackC/c25_summary.json` (FC2 Source) | FC2 | none (old deck slide 13) | 9 (lines 998, 1045) |
| `channels.png` | The hint's channels: one prompt per channel (what each message contains) | `channels.csv`; built by `tools/answer_key.py` | none (a method diagram) | none (S3 optional) | 2 (lines 102, 131) |
| `readout_by_layer.png` | F11's share of the drop at every layer, full-attention layers marked | `readout_by_layer.csv`; `trackA/step10_handoff.json` (F11 Source) | F11 | S6 uses the `_slide` version | 5 (lines 373, 453, 483) |
| `readout_lora_vs_base.png` | Inside the fixed models: LoRA's (panel a) and A40's weights on the readout, on base's own reasoning | `readout_lora_vs_base.csv`; `trackA/gpu/a18/a18_readout.json`, `a41_readout.json` (F39, F42 Source) | F39, F42 (REPORT line 725 also cites its panel b under F38) | none planned (old deck slide 11) | 7 (lines 725, 735, 759) |
| `reviewer_by_prompt.png` | The report version of `reviewer_by_prompt_slide` | `reviewer_by_prompt.csv` | F18, F19, F21 | S7 uses the `_slide` version | 8 (lines 901 to 918) |
| `taught_loss.png` | Training: the taught tokens' loss against base, per trained version | `taught_loss.csv`; `trackA/val_loss_report.json` (F20 Source) | F20 | none | 7 (line 677) |
| `tradeoff_acc_p.png` | Expected accuracy as the share of correct tool answers p changes, exploratory (post hoc) | `tradeoff_acc_p.csv`; `tradeoff_e2.json` | none of its own (exploratory) | none | 7 (lines 829, 834; supplement) |

## C. The supplement's figures (`docs/paper/supplement/figures/`, 7 PNGs: report/supplement only)

Generated by `tools/make_supplement.py` on Nov 19 from the same rows as the paper versions (each CSV starts with that comment line).

| figure | shows | same rows as | finding | report section |
|---|---|---|---|---|
| `cue_experiments.png` | C16, C17 and C18: the cue experiments, per reviewer | `docs/paper/figures/cue_experiments_slide.png` | F31, F33, F34 | 8 (lines 960, 968, 976) |
| `readout_by_layer.png` | F11's readout by layer | `docs/paper/figures/readout_by_layer.png` | F11 | 5 |
| `readout_setA_vs_test2.png` | Set A against the first test, the share at 15, 19, 23 | `readout_by_layer_slide.png` panel b | F26 | 5 (line 492) |
| `reviewer_by_prompt.png` | The reviewer by prompt | `docs/paper/figures/reviewer_by_prompt.png` | F18, F19, F21 | 8 |
| `taught_loss.png` | Taught-token loss per trained version | `docs/paper/figures/taught_loss.png` | F20 | 7 |
| `trackB_following.png` | Following per model and per channel (the per-channel view of Gate 2) | `gate2.png` rows | F15, F16, F17, F29 | 4 (line 272) |
| `trackC_reviewers.png` | Six reviewers' corrections on C4's cases and fresh items | `trackC_reviewers_slide.png` | F18 to F24, F30 | 8 (lines 883 to 950) |

## D. The deck, `docs/presentation/deck.pptx`

Opened with python-pptx (`.venv/bin/python`, installed). It is the Nov 19 shell (built by `cot-disclosure/tools/make_deck.py` from [`TALK_MAP.md`](../TALK_MAP.md)): 18 slides, 14 in the talk and 4 backups, one picture each. It follows the older 13-content-slide map, not the S1 to S13 list above, so the columns say where each slide goes in the planned list.

| deck slide | title (first line) | picture | planned slide |
|---|---|---|---|
| 1 | Do thinking modes make chain-of-thought more honest? (CSE 598 Group 10) | none | S1 |
| 2 | Where did that answer come from? | `three_levels` | S2, S3 |
| 3 | Tools pull harder than users | `gate2` | S4 |
| 4 | Level 1: three layers read the tool's letter | `readout_by_layer_slide` | S6 |
| 5 | Level 1 on a second model | `readout_qwen8b` | S6 / B6 |
| 6 | Level 2: the reasoning names it, the answer doesn't | `private_vs_final` | S5 |
| 7 | Level 2: after a tool call, the answer goes bare | `bare_after_call` | S5 |
| 8 | Tool or authority? | `authority_ladder` | S4 |
| 9 | Does more thinking help? | `b17_effort` | (not in the planned list; backup) |
| 10 | The fix: fewer wrong hints, none beats one line | `gate3_vs_base_slide` | S8 |
| 11 | Inside the fixed model | `readout_lora_vs_base` | (not in the planned list; B1/B6) |
| 12 | Level 3: reviewers defer to the trace | `trackC_reviewers_slide` | S7 |
| 13 | Across agents, and what holds | `c25_hops` | S7 |
| 14 | Limits and next steps | none | S11, S12 |
| 15 (backup) | The fix: fewer wrong hints, none beats one line | `a40_e2_fixes` | S8 |
| 16 (backup) | Inside the fixed model | `b1r2_vs_b1` | B1 / B6 |
| 17 (backup) | Level 3: reviewers defer to the trace | `reviewer_by_prompt_slide` | S7 |
| 18 (backup) | Across agents, and what holds | `pipeline_vs_model` | S7 |

Finding IDs the deck's slide tags carry (from the slide subtitles): 2: F29, F37, FB1 (story); 3: F15, F16, F17, F29, F37, FB1; 4: F11, F12, F26, F32; 5: F36; 6: F3, F29; 7: F15, F25, F29; 8: F35, F40; 9: F37, F29; 10: F28, F41, F43, F44; 11: F38, F39, F42; 12: F18, F22, F30, F34, FC1; 13: F24, FC2, FC3, FC4.

Differences from the planned list that Ritik may want to settle: the deck has no demo slide (S9), no "what's new" slide (S10), no team slide (S13), and no separate S2 question slide; it has the two-model readout and the thinking-dose slide as main slides; `cue_experiments_slide`, `tradeoff_e2` and `c25_hops` placement differ. `c25_hops.png` (FC2) is on the deck but not in the expected slide-ready set; it is a main slide there (slide 13).

## E. Slide-ready copies

`docs/presentation/pack/figures/`: three_levels, gate2, authority_ladder, cue_experiments_slide, private_vs_final, bare_after_call, readout_by_layer_slide, readout_qwen8b, reviewer_by_prompt_slide, trackC_reviewers_slide, pipeline_vs_model, tradeoff_e2, a40_e2_fixes, gate3_vs_base_slide (all `.png`, 1920 x 1080). Added after (Nov 24, for S3, setup): `channels` (1920 x 1080), from `channels.svg`: a method diagram of the hint's seven ways in (our prompt templates, no model text). Not copied, though on the deck: `c25_hops`, `b17_effort`, `readout_lora_vs_base`, `b1r2_vs_b1` (their SVGs are in `docs/paper/figures/` if a backup slide needs them at 1920 px).
