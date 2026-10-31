# Provenance-scaled attention: a fix where the mechanism lives (B1, B2)

Track A, Oct 29. By: Ritik. Code: `finetune/provenance.py` (the mechanism), `finetune/gpu/provenance_job.py`
(the Sol jobs), the gate versions in `finetune/train.py`. Tests: `tests/test_provenance.py`,
`tests/test_provenance_jobs.py` (CPU, a tiny random Olmo 3 with the real tokenizer).

## Why here

Steps 9 and 10 found where Olmo 3 7B Think reads a hint. In three full-attention layers, 15, 19 and
23, the hint's letter is read straight from the prompt and passed to the answer: 0.90 [0.85, 0.96] of
the drop in hint-token restoration at the takeover (FINDINGS F11, F12).

LoRA on just those layers' attention gets 85–90% of full LoRA's loss drop on the taught tokens (F20).
Source tags on the input embedding did nothing measurable (F20's tags check).

So both fixes act on the attention from any position to the hint's tokens, in those layers.

**The circularity to keep out:** layers 15, 19 and 23 were found on the 30 MMLU-Pro questions we
evaluate on. Every choice (alpha, the head subset) is therefore made on set A, the 34 validation
questions used in neither training nor evaluation, never on the 30.

## The mechanism (`finetune/provenance.py`)

In each chosen layer, the attention logit from every query to a key j in the marked span gets a
bias b_h added, per head h:

- **B1, at inference.** b_h = log(alpha) for the chosen heads and 0 for the others, with alpha in
  {1, 0.5, 0.25, 0.1, 0}.
  - Adding log(alpha) to a key's logit is the same as multiplying its attention weight by alpha
    and renormalizing.
  - alpha = 1 is the model itself; alpha = 0 masks the span (b = −10⁴).
  - Heads: all heads of layers 15, 19 and 23 (the default), or a subset such as `"19.31,23.17,15.31"`,
    ranked on set A only.
- **B2, trained.** b_h is a learned scalar per head in layers 15, 19 and 23, zero-initialized, for
  keys tagged *tool* by the source tags (`finetune/source_tags.py`: every environment turn).
  - The model starts as the base model.
  - The source signal moves from the input embedding (the tag versions) into the layers that read
    the hint.
- **Spans.**
  - *deployable*: the tool-role tokens, i.e. every environment turn, the inserted tool turn
    included. A serving system can find these from the conversation's roles.
  - *oracle*: the deployable span plus the pasted tool block inside the user turn. A system can't
    find that in general, so it is reported separately.
  - In the forced-answer job, the pasted block is the hint text's occurrences (`hint_spans`). In
    generation, it is the characters the hinted user message adds to the no-hint one (a diff,
    checked on the 30 questions: it is exactly the `[tool result: lookup_answer_key] …` block).
- **Implementation.**
  - No query × key mask is built, so 32k-token contexts stay on sdpa's efficient kernels.
  - Queries get one extra dimension equal to 1, and keys get b_h · marked(j) / scaling. Both are
    zero-padded to a multiple of 8, values with zeros, and the extra output dimensions are dropped.
  - This runs after the KV-cache update, so cached prompt keys keep their marks and generated
    tokens are never marked.
  - The wrapper replaces transformers' "sdpa" and "eager" functions; every module without an
    attached provenance goes to the original unchanged.
- **Tests:**
  - alpha = 1 gives exactly the base logits;
  - alpha = 0 on every layer equals masking those keys with an attention mask;
  - only the listed layers' hidden states change;
  - a head subset rescales only those heads' eager attention weights (alpha × the weight,
    renormalized);
  - cached generation matches a full forward with the bias;
  - batched, left-padded generation equals one prompt at a time.

## B1's two jobs (`finetune/gpu/provenance_job.py`)

**1. forced, on set A.** This is the cheap test. It runs at Step 10's cuts of set A's cases (Step 10's
format, chosen with Step 10's rule, `deletion.choose`):
- the cuts: the takeover (ii) and before the first mention (i);
- the forced answer `</think>\n\nAnswer: (` under each alpha and span;
- what it records:
  - P(W) and P(O) on the run's own prompt (W = the hint letter, O = the model's own answer);
  - P(O) on the same prompt with the hint's letter replaced by O. That is a correct tool hint
    (Step 10's clean pair, with the same reasoning, so it is a proxy).

Output: one JSON per cut (it resumes) and `provenance_forced.json`, with the difference from alpha = 1
per span, cut and alpha, clustered by question, and the chosen alpha per span.

**The rule for alpha** (written Oct 29, before any set A number exists), per span, at cut (ii):
- dW(a) = the mean over cuts of P_a(W) − P_1(W) on the hinted prompt; dO(a) is the same for P(O),
  and dC(a) the same for P(O) on the correct-hint prompt.
- **Eligible:** dO(a) ≥ 0 and dC(a) ≥ −0.05, so a correct tool hint keeps its pull to within 5
  points.
- **Chosen:** the eligible alpha with the most negative dW. Any alpha within 0.01 of that gives way to
  the larger alpha, the milder change.
- **No eligible alpha:** the choice is 1 (no fix), and that is reported.
- The deployable span is chosen on the cases with an inserted tool turn, the oracle span on all
  cases. Never on the 30 evaluation questions.

**2. generate, on the held-out 30 MMLU-Pro questions.** It uses `finetune/eval.py`'s questions,
wordings and run logic (`run_one`, continuation, parsing).
- **Per question (7 runs):**
  - the wrong tool hint as the pasted block (`tool_progress`) and as the inserted, declared tool turn
    (`inserted_study_guide`), 2 runs each;
  - the correct hint in each, 1 run;
  - no hint, 1 run.
- **Configurations:** alpha = 1 (the same code path, so the hook isn't a confound), then each span at
  its chosen alpha (`--alpha-from` forced's summary). `--alphas` adds more points for the trade-off
  curve.
- **Batching:** Hugging Face generation, batched under a KV-cache token budget (0.5 MiB per token for
  Olmo 3 7B in bf16); out of memory, it falls back to one sequence at a time.
- **Seeds:** per-run seeds can't be kept inside a batch; the batch's generator is seeded from its
  first run.
- **Output:** `eval_<config>_runs.jsonl` (numbers and keyword flags) and the texts beside them,
  which stay on Sol.
- **`report`** gives, per configuration (X of Y, Wilson intervals, each minus alpha = 1 paired by
  question, pooled and per channel):
  - wrong-hint following;
  - correct-hint acceptance;
  - no-hint accuracy.
  It also draws the trade-off figure (`provenance_tradeoff.png` and `.svg`): wrong-hint following
  against correct-hint acceptance.

A fix that just makes the model ignore tools isn't a fix, so both sides are always reported.

## B2's versions (`finetune/train.py`)

- **The versions:** `gate3` (gates only, the base model frozen) and `lora_attn3_gate` (lora_attn3 and
  the gates). They use the same data and settings.
- **One new setting:** the gates' learning rate, `LR_GATE` = 1e-2. A scalar moves at most about lr per
  Adam step, so 2e-4 would leave it near 0 after 260 steps. This is a decision for Ritik.
- **Checkpoints:** the epoch checkpoints hold the gates. `final/gate.pt` and `final/gate.json` hold
  the learned bias per layer and head.
- **Validation loss:** `val_loss.py` takes the gate versions and marks the tool keys.
- **Evaluation:** vLLM can't apply the bias, so `eval_job.py` (batch 3) doesn't take them. They are
  evaluated with `provenance_job.py generate --version <v> --checkpoint train/<v>/epoch<chosen>`, on
  the same runs as B1. `submit.sh eval` refuses them.

## Sol lines and estimates

The estimates are from the dry runs:
- the forced pass at Step 10's size: 40 cuts, 8.1M tokens at 9,000 tokens/s;
- generation: 210 runs per configuration at the 10,300-token median reply, with 80–160 generated
  tokens/s batched, which is a guess until the first job measures it;
- training: lora_attn3's measured 2:44:43.

```bash
# 1. forced on set A (after set A's cases and runs are on Sol; ~15-30 min)
cot-disclosure/finetune/gpu/sol/submit.sh provenance_forced --estimate 0.5 -- \
    --cases-from <set A cases.jsonl> --runs-from <set A runs.jsonl.gz> --items-from <set A items.jsonl>
# 2. generation: alpha = 1 and the chosen alpha per span; 630 runs, 11-23 GPU h, in 4 parts of 2.8-5.6 h
for k in 1 2 3 4; do
  cot-disclosure/finetune/gpu/sol/submit.sh provenance_gen --estimate 4.5 --dependency=afterok:<forced job> -- \
      --alpha-from /scratch/ragarw68/trackA/provenance_forced/provenance_forced.json --part $k/4
done
# 3. B2: train the gate versions (about lora_attn3's 2.75 h each), their validation loss, then generation
cot-disclosure/finetune/gpu/sol/submit.sh train --estimate 3.07 -- gate3
cot-disclosure/finetune/gpu/sol/submit.sh train --estimate 3.07 -- lora_attn3_gate
cot-disclosure/finetune/gpu/sol/submit.sh val_loss --estimate 0.5 --dependency=afterany:<gate3>:<lora_attn3_gate> -- gate3 lora_attn3_gate
cot-disclosure/finetune/gpu/sol/submit.sh provenance_gen --estimate 4.5 --dependency=afterok:<gate3> -- \
    --version gate3 --checkpoint /scratch/ragarw68/trackA/train/gate3/epoch<chosen> --part 1/2     # and 2/2
# Mac, numbers only (the texts stay on Sol), then the report and the figure
rsync -av ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/trackA/provenance_forced/provenance_forced.json results/trackA/gpu/
rsync -av "ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/trackA/provenance_gen/eval_prov-*_runs.jsonl" results/trackA/gpu/provenance_gen/
../.venv/bin/python finetune/gpu/provenance_job.py report --out results/trackA/gpu/provenance_gen
```

**What it costs:**
- One trade-off point (one alpha, one span, 210 runs) is 3.8–7.5 GPU hours.
- The full sweep, 4 alphas × 2 spans plus alpha = 1, would be 34–68 GPU hours. So the curve across
  alpha comes from `forced` on set A (cheap), and generation runs at alpha = 1 and the chosen alphas.
- Measure the rate on the first part before submitting the rest.

## Limits

- **The correct-hint arm in `forced`** reuses the hinted run's reasoning, which mentions W. It is a
  proxy; generation's correct-hint runs are the real test.
- **The deployable span can't reach a pasted block.** For pasted hints only the oracle acts; that is
  the point of reporting both.
- **No per-run seeds in batched generation,** so reruns differ in sampling. Paired comparisons are by
  question, not by run.
- **A head subset needs one key head per query head.** Olmo 3 7B has that (32 and 32); a uniform bias
  works with grouped keys too.
