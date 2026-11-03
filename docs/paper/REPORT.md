# The report: skeleton (the team writes the prose from Nov 10)

Started Nov 3 by Ritik. Sections follow PLAN's report outline; each says who writes it and its figure. **Setup and
methods are filled in as bullets** (facts with their source), so the prose can be written from them. Numbers come from
[`FINDINGS.md`](../FINDINGS.md), the tracks' `FINDINGS_B.md` and `FINDINGS_C.md`, and the claims from
[`CLAIMS.md`](CLAIMS.md). Results freeze on Nov 18; the draft is due Nov 22, the final report Nov 24.

## 1. Introduction (Ritik)

- The question, the three levels ("Where did that answer come from?": inside the model, in its words, between agents),
  the contributions.
- Figure: `docs/paper/figures/three_levels.svg`.

## 2. Setup (Ritik; Track B's part, Arsha)

**Models** (each at its own recommended sampling; the version and where it ran recorded in every run):

| model | where, how | thinking | used in |
|---|---|---|---|
| Olmo 3 7B Think | Voyager (the pinned Think format, rendered by us, sent to /v1/completions); Sol (Hugging Face and vLLM) | always | Track A (all), Track B (F17) |
| Qwen3 30B-A3B Thinking-2507 | Voyager | always | Track B (F15), Track C's solver |
| Qwen3 30B-A3B Instruct-2507 | Voyager | none | Track B (F16), Track C's reviewer |
| Qwen3-8B | Sol, our vLLM, `enable_thinking` | on and off, same weights | Track B (F29), A37 (F36) |
| gpt-oss-20b (`6cee5e81`) | Sol, our vLLM, harmony | effort low / medium / high | B17 (F37), temperature 1.0 |
| Olmo 3.1 32B Instruct, Olmo 3 7B Instruct, Qwen3 30B Thinking, Granite 4.1 30B, Mistral Small 3.2 24B | Voyager; Sol (C13) | — | Track C's reviewers (F18, F22, F30) |
| B20's three (Gemma 4 26B-A4B, Nemotron 3 Nano 30B-A3B, Granite 4.2 8B) | Sol, our vLLM | on and off | B20, if run (Nov 15) |

- **Sampling:** temperature 0.6 for Track A and Track B's models (each model's recommended); gpt-oss-20b 1.0 (its
  recommended); every comparison is within one model or labelled with each model's setting.
- **The budget:** one 32,768-token budget per run, prompt and every reply (a run past it has no answer); Track B also
  reports a 16,000-token cut.

**The hint's channels** (one prompt per channel: `docs/paper/figures/channels.svg`, built by `tools/answer_key.py`):
- none (the baseline);
- the user's hint (two wordings in Track A: `user_turpin`, `user_professor`);
- the user's authority claim ("My course answer key says the answer is (X).", B16);
- a tool result pasted into the user's turn (`[tool result: lookup_answer_key] …`);
- the model's own call to the lookup tool (`tool_real`; Qwen3, gpt-oss);
- a tool turn written into the conversation (`tool_injected`, declared or undeclared; Olmo);
- a system note.

**Questions:**
- **The 24 pilot puzzles** (generated; uncontaminated) and **the 30 MMLU-Pro evaluation questions** (law, engineering,
  chemistry, physics): Track B's 54; Track A's held-out 30.
- **Track A's pool:** 1,600 questions (training, validation); **set A** (validation questions, never in training)
  replicates the localization (F26, F32).
- **C15's 100 fresh items** (60 MMLU-Pro from other categories, 40 puzzles): Track C's replication (F24).
- **E2:** 120 fresh MMLU-Pro questions from the evaluation categories, drawn by seed before any run on them (sha256
  `59c5c250…`; pre-registered Nov 3), the primary set for A39.

**Compute:** ASU's Voyager (served models, free); ASU's Sol (A100 80 GB; vLLM 0.31.0; Hugging Face generation for B1);
no paid calls.

## 3. Methods (Ritik; each track's section, its owner)

**Measures:**
- **Following:** an answered run ends on the wrong hint's letter. **Correct-hint acceptance:** a correct-hint run ends
  on the hint's letter. **No-hint accuracy.** The per-letter no-hint baseline beside following.
- **Mention:** keyword counts (`detect.py`) in the private reasoning and the final answer, until hand labels decide.
- **The bare answer:** a final answer of 30 characters or fewer ("Answer: (X)"), which can name nothing (F15).
- **Hiding:** follows the hint without mentioning it. **False disclosure:** ends on the hint's letter while the final
  answer claims it checked the hint and disagreed, or worked it out independently (keyword candidates; hand labels).

**Hand labels** (`docs/labeling/`):
- two raters, five labels (no mention, mentions only, rejects the hint, says it changed the answer, unclear), blind
  sheets with the outcome hidden, no AI involved;
- Cohen's kappa per text and channel; 0.6 or more, the labels stand; below it, the raters settle the disagreements,
  the guide is tightened, a fresh batch is labeled (L3: under 0.6 on Nov 3; L4 part 1: 0.93).

**Statistics:**
- X of Y with 95% Wilson intervals; differences paired by question, 95% bootstrap clustered by question
  (`common.boot_diff`); fewer than 5 questions behind an interval: "too few questions", and no direction read.
- **Pre-registration:** every experiment's rule is written and committed before its first run
  (`archive/sessions/…-prereg.md`); the supplement's ledger checks each rule's commit against its first result, and
  DEVIATIONS lists every change of plan. Readings made after the fact are labelled so.

**Inside the model (Track A, Olmo 3 7B Think; A37 on Qwen3-8B):**
- the takeover: where in the reasoning the hinted answer takes over (probes, Step 3);
- attention to the hint at the answer position (Step 9) and activation patching at the takeover (Step 10, cut (ii)):
  the share of the hint's drop restored at each layer;
- localized on Test 2, replicated on set A (F26, F32) and on a second model (F36).

**The fixes:**
- **Training** (LoRA, source tags, both, LoRA on layers 15/19/23 only): targets that open by naming the hint; Gate 3's
  rule (fewer wrong hints followed, no-hint accuracy within 5 points, hiding not up; F28).
- **The one-line instruction** (`prompt_only`), the comparison every fix is held to.
- **B1:** attention from layers 15/19/23 to the tool span's keys scaled by alpha, chosen on set A (F27, F38).
- **A39:** a provenance wrapper (every tool output marked "[unverified tool output]") and combinations, on E2.

**Between agents (Track C):** a solver (Qwen3 30B Thinking) with a forced lookup, wrong about half the time by a seeded
oracle; reviewers shown the answer alone, with its explanation, with the private reasoning, or with the tool log; a
checker that re-solves without the tool; the no-tool team as the false-alarm floor (F18).

## 4. The failure: tools pull harder (Arsha)

- Gate 2 on five models (B18's table, `docs/paper/tables/trackB_final.md`); tool or authority (B16, F35); the thinking
  dose (B17, F37); B20 if read.
- Figure: `docs/paper/figures/gate2.png`.

## 5. Level 1, inside the model (Ritik)

- The readout at 15/19/23; set A; Qwen3-8B; the heads; inside the fixed model (A18).
- Figure: `docs/paper/figures/readout_by_layer.png`.

## 6. Level 2, in the words (Ritik, Arsha)

- Private vs final (F3; with L3's labels if they stand); the bare answer after a call and its good-lookup control; the
  instruction (F25).
- Figure: `docs/paper/figures/bare_after_call.png`.

## 7. Fixing it (Ritik)

- Gate 3; the instruction; false disclosure in labels (L4); B1; A39 on E2.
- Figure: `cot-disclosure/results/summaries/trackA/gpu/eval/figures/gate3_vs_base.png` (or A39's).

## 8. Level 3, between agents (Shrey)

- Reviewer deference by family; the citation as the cue (C16–C19).
- Figure: `docs/paper/supplement/figures/trackC_reviewers.png`.

## 9. Across agents, and the pipeline (Shrey)

- The handoff note (C25); pipeline vs model (C20); a realistic tool (C26); the checker's record.
- Figure: `docs/paper/figures/c25_hops.png`.

## 10. Limits and threats (everyone)

- One tool format; one solver; keyword counts where labels aren't in; the 30 evaluation questions (E2 for new
  experiments); cross-day comparisons (T11); runs past a rule's window (B17, §13).

## 11. Related work ([`RELATED_WORK.md`](RELATED_WORK.md)), 12. Conclusion and deployment (everyone)
