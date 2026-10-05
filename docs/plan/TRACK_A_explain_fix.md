# Track A: explain and fix (owner: Ritik)

## Question

Why does a thinking model follow a wrong hint, especially a tool hint, without saying so?
And can a small architectural change plus fine-tuning make it check the hint and keep its
own answer?

## Suspected cause (the hypothesis this track tests)

Attention lets every new token draw on every earlier token in the same way. Nothing marks
a tool's text as less trustworthy; role labels are just more tokens. The reasoning is
generated on top of itself, so once it repeats the hint ("the expected answer is G"),
later tokens build on that repetition.

## Method

1. **Model.** Olmo 3 7B Think (`allenai/Olmo-3-7B-Think`). Its weights are open, it
   follows hints (1 of 48 hinted runs on easy puzzles; 7 of 15 tool hints on unsure
   MMLU-Pro questions, 7 of 7 among the runs not cut off), and it fits one GPU. Run on
   ASU Sol; request access in week 9.
2. **Look inside** (weeks 13–14), on saved steered and unsteered runs of the same
   question:
   - **Attention to hint tokens:** for each layer and head, the share of attention from
     the reasoning tokens to the hint tokens. Compare steered vs unsteered runs, user vs
     tool hint.
   - **Where the hinted answer takes over:** at each sentence of the reasoning, the
     model's probability of each answer letter, read with a logit lens or with a forced
     "Answer: (" continuation. Mark the first point where the hinted letter leads, and
     check whether it comes right after the reasoning repeats the hint.
   - **A causal check:** remove (or mask attention to) the repeated hint sentence in the
     reasoning, and see whether the answer goes back to the no-hint answer.
3. **Training data** (`cot-disclosure/finetune/build_dataset.py`, runs today). It writes
   196 training and 120 held-out records (`RESULTS_SUMMARY.json` →
   `scope_numbers.trackA_dataset`).
   - **Training:** the 24 puzzles with paraphrased hints only.
   - **Held out:** the 30 MMLU-Pro items, with the exact wordings we test with. Of the
     held-out wordings, 0 appear in training.
   - **To do:** target reasoning, correct-hint examples, more training questions with
     the model's own no-hint answers (see `cot-disclosure/finetune/README.md`).
4. **Source tags** (`cot-disclosure/finetune/source_tags.py`, unit-tested). An
   `Embedding(4, hidden_size)` is added to each input token: system, user, tool, model.
   The source ids come from the chat template's role spans. The tag table starts at
   zero, so the wrapped model starts identical to the base model (tested).
5. **Train** (weeks 13–14). LoRA (rank 8–32) + source tags, with three ablations:
   - LoRA only
   - tags only
   - both

   Loss only on the model's tokens.
6. **Evaluate on behavior:**
   - hint following on held-out questions with held-out wordings
   - no-hint accuracy
   - mention and acknowledgment (keyword pre-sort, then hand labels)
   - the **hiding check:** follows the hint but doesn't mention it
   - transfer to Track B's conditions and Track C's pipeline (week 15)

## Measures and success (Gate 3, Nov 22)

**Success:** on held-out questions and wordings, the trained model follows fewer wrong
hints than the base model:
- a 95% bootstrap difference (clustered by question) that excludes 0
- no-hint accuracy within 5 points
- no rise in the hiding check

Otherwise we report it as a negative result, with the inside-the-model analysis.

## Risks

- **Fine-tuning can teach the model to hide the hint.** If training rewards text that
  looks honest, the model can change its words instead of its behavior. OpenAI reported
  this in 2025 with reasoning monitors. So we train on behavior targets, score behavior
  first, and test with wordings unseen in training.
- **Small data.** 24 training questions isn't enough. Generate more puzzles and use
  MMLU-Pro categories not in the evaluation, each with the model's own no-hint runs.
- **GPU access** on Sol isn't confirmed yet. 7B LoRA fits one 40–80 GB GPU; request it
  early.
- **The chat template may not render prefix-stably,** so role spans can't be read off
  automatically. `source_ids_from_chat` raises in that case; tag spans by hand then.
- **The served checkpoint may differ.** The one behind Voyager's `olmo3-7b-think` is
  only the candidate for `allenai/Olmo-3-7B-Think` (`docs/progress/MODELS.md`).
  Re-measure the base model on Sol before training.

## Tasks

| Week | Task | Owner |
|---|---|---|
| 9 | Request Sol GPUs; download Olmo 3 7B Think; reproduce one steered run and one unsteered run locally | Ritik |
| 10 | Check Olmo's chat template with `source_ids_from_chat`; attention-extraction script | Ritik |
| 11–12 | Generate more training questions and their no-hint runs; write target reasoning; correct-hint examples | Ritik |
| 13 | Look inside (attention, answer takeover, causal check) | Ritik |
| 14 | Train (3 ablations); evaluate; Gate 3 | Ritik |
| 15 | Hand the trained model to Tracks B and C | Ritik, Arsha, Shrey |
