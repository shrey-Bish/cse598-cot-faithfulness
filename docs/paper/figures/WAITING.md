# Slide figures waiting on a result: the specs

**Edited by:** Ritik (Shrey's slide 12 spec is Shrey's to follow, not to edit).

Written Nov 1 for the final presentation map in [`docs/PLAN.md`](../../PLAN.md); updated Nov 3 (slides 4, 7, 8, 2 and 10
are made; slide 12 is drawn by Shrey) and Nov 4 (A39's spec, 04:05; slides 3, 9 and 11 made as `_slide` versions,
04:09; at 16:19 the additions below brought in line with the map: B24 on slide 7, B1R2 on slide 10, the `_slide`
files); Nov 5, 09:53: B1R2 dropped, so slide 10 waits on nothing); Nov 7, 20:36: A39's figures drawn (A39 read, F44). Nothing here is drawn from fake or partial numbers. Ritik's slides are added to
`cot-disclosure/tools/slide_figures.py` in the style of `bare_after_call` (16:9, white, colors by role, X of Y on the
bars, a CSV of every plotted number), from a numbers-only summary under `cot-disclosure/results/summaries/`. **Shrey's
(slides 11–12) are drawn by a script under `cot-disclosure/agents/` into `docs/trackC/figures/` (shared code is read-only
on `trackC-main`); Ritik places them at merge.**

Colors by role: final answer #E2622A, private reasoning #2F6FD6, the cue #C02F79, baseline or comparison #8893A6,
correct #14826A, damage (following a wrong letter) #9C6C06. Intervals: 95% bootstraps clustered by question
(or by item in Track C), as each experiment's rule computes them.

## Slide 4: Level 1 on a second model (A37, Qwen3-8B)

Made Nov 1 from `results/summaries/trackA/qwen8b_mech/` (the readout and Step 10's summary) and Olmo's
`step10_handoff.json` (Test 2, set A): `docs/paper/figures/readout_qwen8b.png` (F36). It's drawn to the spec, except
that the Sol files were copied back to `results/trackB/qwen8b_mech/`, not `results/trackA/qwen8b_step10/`.

## Slide 7: Tool or authority? (B16)

Made Nov 1 from `results/summaries/trackB/b16_report.json`: `docs/paper/figures/b16_authority.png` (F35).

## Slide 8: Thinking dose (B17)

- **Made Nov 3** from `results/summaries/trackB/b17_report.json`: `docs/paper/figures/b17_effort.png` (F37), to the spec
  below, labelled "run after its one-day window (pre-registration section 13)".
- **Shows:** one set of weights (gpt-oss-20b) at reasoning effort low, medium and high.
- **Source:** `cot-disclosure/results/trackB/b17/b17_report.json` (`progress/run_b17.py --report`, from the flags
  copied back from Sol), exported to `results/summaries/trackB/b17_report.json`.
- **Axes and encodings:** two panels, x = effort (low, medium, high) in both.
  - Left: following on the real tool call (damage color), with the call rate as a lighter baseline series.
  - Right: the bare final answer after a call (final-answer color).
  - Each point with its interval and X of Y. The high minus low differences are written in the panel titles.
- **Comparison (pre-registered Oct 31 22:37):** high minus low, paired by question, on two measures, each read as
  "rises with effort", "falls" or "no change detected":
  1. following on tool_real;
  2. the bare final answer after a call.
  - Medium minus low and high minus medium go in the CSV, with no decision.
- **Owner and date:** made Nov 3 by Ritik (F37); Arsha's from Nov 6.

## Slide 10: Inside the fixed model (A18, with B1)

- **Made Nov 3** from `results/summaries/trackA/gpu/a18/` (`a18_readout.json`, `swap_rows.jsonl`) and B1's report:
  `docs/paper/figures/readout_lora_vs_base.png` (F39, F38). Two departures from the spec below, both because R_lora
  came out below 0: the middle panel's shares s(S) are undefined (their denominator is negative in every resample), so
  panel (a) shows each swap's R beside R_lora, marked "reported, not read"; and the Sol files were copied back to
  `results/trackA/gpu/a18/`, not `results/trackA/a18/`.
- **The spec, as written Nov 1:**
- **Figure:** `docs/paper/figures/readout_lora_vs_base.png` (.svg, .csv).
- **Shows:** does LoRA's training stop the readout at layers 15, 19 and 23, or act after it? Beside it, B1 at
  inference time.
- **Source:**
  - A18: Sol `$TRACKA_OUT/a18/a18_readout.json` (`finetune/look/a18.py readout`), copied back to
    `cot-disclosure/results/trackA/a18/`; numbers only.
  - B1: `$TRACKA_OUT/provenance_gen/provenance_gen_report.json` (`provenance_job.py report`; the reading is
    `b1_verdict`). **Read Nov 3 (F38)**; exported to
    `results/summaries/trackA/gpu/provenance_gen/provenance_gen_report.json`.
  - Both exported under `results/summaries/trackA/`.
- **Axes and encodings:**
  - Left: R_lora, what LoRA's weights remove of base's direct effect of the hint, as a dot and interval, with a zero
    line.
  - Middle: the share s(S) for the four swaps (before 0–14, the readout 15/19/23, through 0–23, after 24–31), as
    bars with intervals and a 0.5 line. The readout swap is in the cue color; the others are baseline.
  - Right: B1's deployable span, following on the inserted tool turn minus alpha = 1, a dot and interval in the
    damage color.
- **Comparison (A18's log, Oct 31 22:44; its case set as amended Nov 1, before anything ran):**
  - R_lora's interval above 0, else "acts in the reasoning".
  - Then "stops the readout" if s(0–23)'s lower bound ≥ 0.5 and s(24–31)'s upper bound < 0.5, and within it "at the
    readout layers", "before them" or "spread over 0–23".
  - "Acts after the readout" if the reverse holds; else "either half suffices" or "unclear".
  - B1's rule (Oct 30 17:15): "works", "ignores tools", "costs accuracy", "no effect" or "worse".
- **Owner and date:** Ritik; made Nov 3 (A18 read, F39; B1 read, F38).

## A39: the fix round on E2 (after slide 9; the report's section 6)

- **Made Nov 7** (A39 read by its rules, F44): `docs/paper/figures/a39_e2_fixes.png` and `a39_e2_parts.png`, and the
  30's `a39_mmlupro_30_fixes.png` and `a39_mmlupro_30_parts.png` (.svg, .csv), from the complete reports
  `results/trackA/gpu/a39/a39_e2.json` and `a39_mmlupro_30.json` (`tools/export_summaries.py` copies them to the
  tool's default path). Three departures from the spec below, made after the reading (tests seen failing first):
  - **The headlines carry the readings' words** (the spec left the slide's sentence until A39 was read). The fixes
    figure: R2's "fewer than the instruction" systems, a wrapper system marked "diluted by design", with the acceptance
    difference beside each, then R1's verdicts. The parts figure: the wrapper alone (R4) and wrapper + note and LoRA +
    wrapper (R3), with those differences on the inserted tool turn.
  - **Panel (b)'s readings are written inside the panel,** beside each combination's name, so the longer ones ("no
    better than the better one alone", on the 30) don't run across the plot.
  - **Panel (c)'s ticks are every 20 points** when every 10 would crowd it (the 30's range, −45 to +20).
- **The spec, as written Nov 4:**
- **Figures:** `docs/paper/figures/a39_e2_fixes.png` and `docs/paper/figures/a39_e2_parts.png` (.svg, .csv), drawn by
  `cot-disclosure/tools/a39_figures.py` (written Nov 4, 04:05) in `bare_after_call`'s style. The 30, reported beside
  E2, gives `a39_mmlupro_30_fixes` and `a39_mmlupro_30_parts` for the supplement.
- **Drawn only after all A39 parts are in** (they were on Nov 7, 13:28). The tool refuses a report whose `complete` is false (its
  `completeness` lists the runs missing per system). `--draft` stamps "DRAFT"; a draft never goes on a slide.
- **Source:** `finetune/a39.py --report --qset e2` writes `a39_e2.json` (numbers only) from the run files copied back
  from Sol's `$TRACKA_OUT/a39/` (`eval_*_a39_e2*_runs.jsonl`). It is exported to
  `results/summaries/trackA/gpu/a39/a39_e2.json`, the tool's default `--report`.
- **(a) `a39_e2_fixes`:** one row per system (base, prompt_only, LoRA, LoRA + note, wrapper, wrapper + note, LoRA +
  wrapper), pooled over the channels.
  - Left, R1 (system minus base): `r1.<system>.following_vs_base` and `.acceptance_vs_base` (acceptance is beside,
    not read). Under each row: `verdict` and `failed`.
  - Right, R2 (system minus prompt_only): `r2.<system>.following` and `.acceptance`. Under each row: `reading`.
  - Row labels: the system's own X of Y, `systems.<system>.following.pooled` and `.acceptance.pooled`.
- **(b) `a39_e2_parts`, left:** R3, each combination minus each part alone. The keys are
  `r3.<combination>["minus <part>"]`'s `following`, `acceptance` and `accuracy`, with its `reading` (A38's) and
  `channel`.
  - LoRA + note is pooled; the wrapper combinations are on the inserted tool turn.
  - Row labels: `systems.<system>.following.<channel>`, X of Y against the part's.
- **(c) `a39_e2_parts`, right:** R4, wrap minus base on the inserted tool turn: `r4.following`, `r4.acceptance` and
  `r4.accuracy`, with `r4.reading` (B1's).
  - The check: `r4.pasted_check.following_minus_base`, which must be exactly 0 (`exactly_zero`).
- **Encodings and labels:**
  - Dots are the paired difference; lines are the report's 95% bootstrap clustered by question. The x axis is
    "difference (points)", with a zero line.
  - Following, "follows the wrong hint": damage #9C6C06, a circle. Acceptance, "takes the correct hint": correct
    #14826A, a diamond. No-hint accuracy and the check: comparison #8893A6, a square (the check hollow).
  - A wrapper system's R1 and R2 markers are hollow, "diluted by design" (`note`; the amendment's 9.2).
  - A dagger marks a difference whose sides' no-answer shares are more than 5 points apart
    (`no_answer.imbalance`; 9.1). The counts are in the CSV.
  - "too few questions" and "missing runs" are written where a dot would be.
  - The headline lines come from the readings only. The slide's own sentence is written once A39 is read.
- **The comparison:** R1–R4 as pre-registered Nov 3, with the amendment (the A39 log's section 9), both before any
  run; `finetune/a39.py`'s docstring.
- **Tested on synthetic reports**, written to a temporary folder (`tests/test_a39_figures.py`); drawn into this folder
  only from the complete reports, Nov 7.
- **Owner and date:** Ritik. Read and drawn Nov 7 (F44), once complete (its rule; PLAN's Nov 17 was a deadline).

## The trade-off on E2, exploratory (post hoc) (REPORT §7's labelled bullet; the supplement)

- **Made Nov 7:** `docs/paper/figures/tradeoff_e2.png` (.svg, .csv) and `tradeoff_acc_p.png` (.svg, .csv), drawn by
  `cot-disclosure/tools/tradeoff.py --figures` from its numbers-only `tradeoff_e2.json` (exported to
  `results/summaries/trackA/gpu/a39/`).
- **Exploratory (post hoc), not pre-registered:** the analysis is the
  [Nov 7 20:20 log](../../archive/sessions/2026-11-07/2026-11-07_2020_A_tradeoff-exploratory.md), written and committed
  before computing. Each figure's headline and each CSV's first line say so. It replaces no verdict.
- **`tradeoff_e2`:** every E2 system as a point, wrong-hint following against correct-hint acceptance, Wilson bars on
  both axes; (a) pooled, the wrapper systems hollow (diluted by design); (b) the inserted tool turn.
- **`tradeoff_acc_p`:** Acc(p) for base, the instruction, LoRA and A40; A40's crossing with the instruction (p* 0.36
  [0.22, 0.50]); LoRA doesn't cross (behind at every p).

## Slide 12: Across agents, and what holds (C25; C20, C26)

- **Figure:** `docs/paper/figures/c25_hops.png` (.svg, .csv).
- **Shows:** the source at each hop, from the solver to the writer's handoff note to a decider that never sees the
  tool, and whether the decider accepts the wrong answer more when the source is gone.
- **Source:** `cot-disclosure/results/trackC/c25_summary.json` (`agents/c25.py`), exported to
  `results/summaries/trackC/c25_summary.json`. The 20-row spot check is read with `agents/c25.py --spot-check-read`
  (Shrey labels it).
  - C20 and C26 add `c20_summary.json` and `c26_summary.json`, as a second figure if there is room
    (`pipeline_vs_model.png`).
- **Axes and encodings:**
  - Left: x = hop (solver, plain note, keep note), y = the share of bad-lookup cases naming the tool, X of Y with
    Wilson intervals. The private reasoning's color goes on the solver's hop; the final answer's on the notes. A 50%
    line marks the "kept" and "lost" thresholds.
  - Right: per decider (Olmo 3.1 32B, Qwen3 30B Instruct), the share accepting the wrong letter for the plain, keep
    and keep_stripped notes, in the damage color, with the paired differences as text.
- **Comparison (C25's log, Oct 31 22:33):**
  - Per note variant: "kept" (the lower bound is above 50%), "lost" (the upper bound is below 50%) or "mixed".
  - The decider: paired by item, clustered by item, with C11's 20-point margin (`c16.two_sided`).
- **Owner and date:** Shrey. C25, C20 and C26 read Nov 6 (FC2–FC4, merged Nov 6), their figures made as
  `docs/trackC/figures/c25_hops.png` and `pipeline_vs_model.png`; placed in `docs/paper/figures/` Nov 7 (C24's tables
  too, in `docs/paper/tables/`). Ritik puts them on the slide.

## Additions to figures that exist (no new file)

- **Slide 2:** made Nov 3 as `docs/paper/figures/gate2.png` (B18's rows, with B17's efforts); B20 if read by Nov 17.
  Owner: Arsha, from Nov 6.
- **Slide 5** (PLAN lists `docs/paper/figures/cue_experiments_slide.png`, the supplement's `cue_experiments`; it plots
  C16–C18, not F3): L3's kappa in the caption once the labels are read under the LLM-judge protocol (kappa under 0.6
  on Nov 3, Ritik against an AI rater; Gate 2 Nov 8). Owners: Ritik and Shrey. Corrected Nov 4, 17:55: rater 2 was an
  AI model (ChatGPT 5 Astra High), not Shrey; see the 17:42 log; no settling call or fresh batch.
- **Slide 7** (`docs/paper/figures/b16_authority.png`): B24's two arms (the classmate, the official solution manual)
  beside B16's, from `results/summaries/trackB/b24_report.json` (read Nov 4, F40), with B24's readings (the gradient
  same day; the rest cross-day, labelled). Owner: Arsha, from Nov 6.
- **Slide 9** (`docs/paper/figures/gate3_vs_base_slide.png`, made Nov 4 from `finetune/gate3.py`'s rows): false
  disclosure from L4 part 1's hand labels (read Nov 3, F28); A39's powered replication on E2 (read Nov 7, F44) is in its
  own figures (above). The final statement is Nov 20. Owner: Ritik.
- **Slide 10** (`docs/paper/figures/readout_lora_vs_base.png`): **A41's bars added Nov 7** (A40's weights beside LoRA's,
  from `a41_readout.json`; F42). B1R2, revived Nov 6 (the A39 log's §21), is running: panel (b) gains it once read
  (complete, or partial at Nov 15 23:59), else stays B1 on the 30, as made. Owner: Ritik.
- **A40 and A42** (`docs/paper/figures/a40_e2_fixes.png`, made Nov 7 by `tools/a40_figures.py` from their reports;
  F41, F43): for §7 and, if there is room, slide 9 beside Gate 3. Owner: Ritik.
- **Slide 11** (`docs/paper/figures/trackC_reviewers_slide.png` and `reviewer_by_prompt_slide.png`, made Nov 4; the
  supplement's `trackC_reviewers`): C19's answer-key-versus-own-working bars: read Nov 6 (FC1), made by Shrey as
  `docs/trackC/figures/c19_authority.png`; placed in `docs/paper/figures/` Nov 7. Owner: Shrey (the figure), Ritik (the
  slide).
