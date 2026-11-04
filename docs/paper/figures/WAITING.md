# Slide figures waiting on a result: the specs

**Edited by:** Ritik (Shrey's slide 12 spec is Shrey's to follow, not to edit).

Written Nov 1 for the final presentation map in [`docs/PLAN.md`](../../PLAN.md); updated Nov 3 (slides 4, 7, 8, 2 and 10
are made; slide 12 is drawn by Shrey). Nothing here is drawn from fake or partial numbers. Ritik's slides are added to
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

- **Figures:** `docs/paper/figures/a39_e2_fixes.png` and `docs/paper/figures/a39_e2_parts.png` (.svg, .csv), drawn by
  `cot-disclosure/tools/a39_figures.py` (written Nov 4, 04:05) in `bare_after_call`'s style. The 30, reported beside
  E2, gives `a39_mmlupro_30_fixes` and `a39_mmlupro_30_parts` for the supplement.
- **Drawn only after all A39 parts are in (Nov 17).** The tool refuses a report whose `complete` is false (its
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
- **Tested only on synthetic reports**, written to a temporary folder (`tests/test_a39_figures.py`). Nothing is drawn
  into this folder before Nov 17.
- **Owner and date:** Ritik. The runs end Nov 15; A39 is read and drawn Nov 17.

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
- **Owner and date:** Shrey; C25 due Nov 12, C20 and C26 Nov 15.

## Additions to figures that exist (no new file)

- **Slide 2:** made Nov 3 as `docs/paper/figures/gate2.png` (B18's rows, with B17's efforts); B20 if read by Nov 17.
  Owner: Arsha, from Nov 6.
- **Slide 5** (`docs/paper/supplement/figures/cue_experiments.png`): L3's kappa in the caption once the labels are
  settled (kappa under 0.6 on Nov 3). Owners: Ritik and Shrey.
- **Slide 9** (`cot-disclosure/results/summaries/trackA/gpu/eval/figures/gate3_vs_base.png`): false disclosure from
  L4 part 1's hand labels (read Nov 3, F28). The final statement is Nov 20. Owner: Ritik.
- **Slide 11** (`docs/paper/supplement/figures/trackC_reviewers.png`): C19's answer-key-versus-own-working bars,
  due Nov 7. Owner: Shrey.
