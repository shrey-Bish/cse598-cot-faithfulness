# 06. Report outline

Section by section, in the order a reader meets them: the facts, figures and tables each section needs, drawn from
[`docs/paper/REPORT.md`](../../paper/REPORT.md)'s bullets (§1–§12, each with its owner), with a suggested length.
Outline only: the prose is the team's. Numbers are FINDINGS' (rows of [02_NUMBERS](02_NUMBERS.md)); figures are in
[04_FIGURES](04_FIGURES.md); methods facts in [03_METHODS](03_METHODS.md).

**Length.** No page limit, format or rubric is in the repo ([11_REQUIREMENTS](11_REQUIREMENTS.md)); check Canvas. The
lengths below assume a body of about 5,000 words (about 8 pages in a two-column conference format, figures included).
Rescale by the same shares if the limit differs.

| section | REPORT.md source | share | words (of ~5,000) |
|---|---|---|---|
| Abstract | §1, §12 | — | 150–200 |
| 1. Introduction | §1 | 12% | ~600 |
| 2. Related work | §11, RELATED_WORK.md | 10% | ~500 |
| 3. Setup and methods | §2, §3 | 18% | ~900 |
| 4. Results | §4–§9 | 40% | ~2,000 |
| 5. Discussion | §12, FINDINGS' story item 7 | 8% | ~400 |
| 6. Limits | §10 | 7% | ~350 |
| 7. Conclusion | §12 | 5% | ~250 |
| AI use | `docs/submission/AI_USE_INVENTORY.md` | appendix | as needed |
| Contributions | [10_TEAM_AND_PROCESS](10_TEAM_AND_PROCESS.md) | appendix | as needed |

## Abstract (150–200 words)

- The question; the three levels; the answer: **mixed** (FINDINGS' story, item 5).
- One number per level, at most: tool − user +35 [+24, +46] (F15); 208 of 216 against 8 of 216 (keyword counts,
  F3); 0.90 [0.85, 0.96] (F11); 59 of 73 → 3 of 73 (F18); the fix trade: 84 of 694 against 237 of 713, at 347 of 459
  against 431 of 476 (F41).
- The one result that works: the checker that never sees the tool, all 53 wrong answers stopped (F24).
- Scope in one phrase: small models, mostly one or two per result.

## 1. Introduction (REPORT §1; Ritik)

- The question and "Where did that answer come from?": inside the model, in its words, between agents. Figure:
  `three_levels.png` (the project's map).
- The contributions, each with its prior work said beside it (REPORT §1's Nov 19 bullets): the tool-vs-user test
  (F15–F17, F29, F37, FB1); the authority ladder (F35, F40); the readout layers (F11, F26, F32, F36); the words (F3,
  F15, F25, F29); where training acts (F39, F42); the trade-off in the fixes (F41, F43, F44, F38); the review team (F18,
  F24, F30, F34).
- The answer to the title question, mixed, in two sentences (F29, F37, FB1).

## 2. Related work (REPORT §11; everyone)

- Four groups: CoT faithfulness under hints; deference to a claimed source or a tool; fixes (consistency training,
  attention steering, provenance defenses); reviewers and automation bias. One line per paper, with agrees / extends /
  differs ([07_RELATED_WORK](07_RELATED_WORK.md)).
- Say what is not ours before what is (01_STORY, "What's new and what isn't").
- The two disagreements to state: A-CC (users followed more than function outputs) and Syed and Yasaei (tool
  instructions discounted); neither reconciled.

## 3. Setup and methods (REPORT §2, §3; each track's part by its owner)

- **Setup table:** 12 models (8 answering, 4 reviewers), where each ran, thinking settings (03_METHODS).
- **Question sets:** the 54 test questions (24 puzzles, 30 MMLU-Pro) × 3 runs; the 30 held-out (930 runs a system);
  the 120 fresh (seed, categories, exclusion checks); set A's 16; C4's 53 items; C15's 100 (03_METHODS).
- **Hints:** sources and wordings (user, professor, pasted tool block, inserted tool turn, the model's own call, system
  note; classmate, answer key, solution manual). Figure: `channels.png` (report only).
- **Measures:** following = the hint's letter in the answer; acceptance = a right hint taken; mentions = keyword counts
  (`detect.py`); bare answer; hand labels (L3, L4, L6) and LLM judges; the review pipeline (solver, reviewer, checker).
- **Inside the model:** activation patching at the takeover (one-token swap, logit difference), attention heads;
  Olmo 3 7B Think's sliding-window and full-attention layers.
- **Fixes:** the one-line instruction; LoRA (four versions) and consistency training with their configs and data counts;
  source tags; the "unverified" wrapper and notes; the attention dial (B1).
- **Statistics:** Wilson 95% intervals; differences in points with a 95% bootstrap clustered by question (by item in
  Track C); "too few questions" under 5; pre-registered rules (31, PREREGISTRATIONS.md), deviations listed; the freeze.

## 4. Results (REPORT §4–§9; 40% of the body)

One subsection per level, each finding as a claim, its numbers and status, its limits and its figure (REPORT's bullets
already have this shape; [`results_at_a_glance.md`](../../paper/tables/results_at_a_glance.md) is the one-row-a-finding
table).

| subsection | REPORT § | findings | figures | table |
|---|---|---|---|---|
| 4.1 The failure: tools pull harder | §4 (Arsha) | F1, F15–F17, F29, F35, F37, F40, FB1 | `gate2.png`, `authority_ladder.png`, `b16_authority.png` | Track B's final table (`docs/paper/tables/trackB_final.md`) |
| 4.2 Level 1, inside the model | §5 (Ritik) | F11, F12, F26, F32, F36 (F4–F10, F13, F14 as supporting) | `readout_by_layer.png`, `readout_qwen8b.png` | — |
| 4.3 Level 2, in the words | §6 (Ritik, Arsha) | F3, F15, F16, F17, F25, F29, F37, FB1 | `private_vs_final.png`, `bare_after_call.png`, `b17_effort.png` | — |
| 4.4 Fixing it | §7 (Ritik) | F20, F28, F38, F39, F41–F45 | `gate3_vs_base_slide.png`, `a40_e2_fixes.png`, `a39_e2_fixes.png`, `readout_lora_vs_base.png`, `b1r2_vs_b1.png`, `taught_loss.png`; `tradeoff_e2.png` (exploratory) | L6's labels (F45) as a table |
| 4.5 Level 3, between agents | §8 (Shrey) | F18, F19, F21–F24, F30, F31, F33, F34, FC1 | `reviewer_by_prompt.png`, `trackC_reviewers.png` (supplement), `cue_experiments.png`, `c19_authority.png` | `trackC_experiments.md` |
| 4.6 Across agents, and the pipeline | §9 (Shrey) | FC2, FC3, FC4, F24's checker | `c25_hops.png`, `pipeline_vs_model.png` | `trackC_pipelines.md` |

## 5. Discussion (REPORT §12, FINDINGS' story item 7; ~400 words)

- Label it interpretation ("our reading"): without a way to verify the tool, resisting wrong hints and relying on right
  ones trade off; every fix moves along that trade (F41, F43, F44, F38).
- So the fix belongs at the system level: provenance labels alone don't help (F44, FC3); independent verification does
  (F24).
- The exploratory trade-off figure (0.36 [0.22, 0.50]; `tradeoff_e2.png`): marked post hoc, replacing no verdict.
- What the title question's "mixed" means: thinking doesn't reliably make the final answer say where it came from.

## 6. Limits (REPORT §10; everyone; ~350 words)

- Small models, one or two per result; every fix on Olmo 3 7B Think; MMLU-Pro's evaluation categories and puzzles;
  multiple choice; one tool format; one solver and one reviewer prompt in Track C.
- Keyword counts where labels didn't stand (F3); every kappa one human against an AI rater; L4's and L6's sheets not
  blind in practice.
- Underpowered: the attention dial on the 30 (F38). After the fact: Qwen3-8B on/off (F29). Out of window: gpt-oss-20b
  (F37). Temperature 1.0 in the newer families (FB1).
- The measurement traps found and fixed (T1–T13; `docs/paper/supplement/TRAPS.md`).

## 7. Conclusion (REPORT §12; ~250 words)

- The failure holds across families (Gate 2, FB1); the words hide the source (F3, F15); three layers read it (F11,
  F36); reviewers of one family defer and a blind checker holds (F18, F24, F30); every fix is a trade (F41).
- **Wording to fix from REPORT §12:** its L6 bullet says training made the answer more candid "without making it follow
  less". Per the Nov 23 correction, say instead: more candid than the instruction (37 of 42 against 18 of 42; F45),
  following no less than the instruction (F44) and fewer than no fix (LoRA −10 [−16, −4], F28).

## AI use (appendix)

- From `docs/submission/AI_USE_INVENTORY.md` (summarized in [10_TEAM_AND_PROCESS](10_TEAM_AND_PROCESS.md)): what each
  AI tool did, by track; the AI rater (ChatGPT 5 Astra High) as rater 2 for labels; the LLM judges (Nov 4 protocol).
- Open: the inventory's "to confirm" lines (Arsha's and Shrey's own use) and its update for Nov 20–24.

## Contributions (appendix)

- Who did what, from the git history and the tracks: [10_TEAM_AND_PROCESS](10_TEAM_AND_PROCESS.md) (facts only;
  `docs/submission/CONTRIBUTIONS.md` is the team's to write).
