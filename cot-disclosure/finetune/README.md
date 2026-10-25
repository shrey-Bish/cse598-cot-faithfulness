# Track A: teach Olmo 3 7B Think to check a wrong hint instead of following it

Owner: Ritik. Weeks 13–14 on ASU Sol GPUs. This folder holds the pieces that run today.
The training run itself is the plan below.

## What is here

Files that store full replies are gzip (`.jsonl.gz`, read and written by `progress/common.load`/`append`), with a small `_runs.jsonl` summary beside the big ones; no tracked file may exceed 50 MB (`tests/test_repo_size.py`).

| File | What it does | Runs today? |
|---|---|---|
| `build_dataset.py`, `length_audit.py` | Step 5: train / validation / held-out records (target rule, correct-hint records, channels, held-out wordings; see Data below) and the reply-length audit. | Yes. `data/heldout.jsonl` (240 records); `train`/`validation` fill once Step 6's no-hint runs exist. |
| `source_tags.py` | Source tags: a learned `Embedding(4, hidden_size)` added to each input token, marking its source (system, user, tool, model). Ids come from chat-template role spans. | Yes. Unit-tested on a tiny random model on CPU (`tests/test_source_tags.py`). |
| `voyager_capabilities.py`, `voyager_ids_check.py` | Step 1: what Voyager's endpoints accept (completions, echo log-probs, stops). The 2026-10-21 model-ID change checks. | Done. `results/trackA/voyager_capabilities.jsonl.gz` (+ `_summary.json`), `voyager_ids_check.jsonl.gz`. |
| `templates/`, `olmo_format.py`, `template_revisions.py`, `show_spans.py` | Step 2: the pinned format. The official Think template plus the Instruct template's tool turns. Rendered locally, sent to `/v1/completions`, split at `</think>` by us. A reply cut off at 16,000 tokens is continued up to the 65,536-token context (`extend`). | Yes. `tests/test_trackA_format.py`. |
| `smoke_2b.py`, `base_format.py` | Step 2b: the base model in the pinned format. 20 MMLU-Pro Test 2 questions × no hint, user, tool pasted, tool inserted, and tool inserted with the function declared. `--report` gives channels, both inserted arms and the contradiction keyword count. | Done: 240 of 240. Replies in `results/trackA/base_format.jsonl.gz`, one row per record in `base_format_runs.jsonl`. |
| `continuation.py` | Continue a saved reply from a given point to a final answer, the same way everywhere (Step 4, the look-inside reruns, Phase 6): past a call quoted in the reasoning; a tool call in the final answer is answered as `run_injected` answers it in Step 2b (at most 2 more rounds); one token cap over all rounds, and hitting it is no answer. | Yes (`tests/test_trackA_continuation.py`). Step 4 uses it from Oct 25; its Oct 25 run counted 6 repeat calls as no answer and was not rerun. |
| `look/takeover.py`, `look/plot_takeover.py` | Step 3: the takeover curve, by early answering (Lanham et al. 2023). After each sentence of a saved run, force `</think>\n\nAnswer: (` and read the option letters' probabilities (top 10). Gives the takeover point and its type (at 0 / late / other), whether a hint mention comes just before it (against two baselines), the sure/unsure split, and the default cases for Steps 4 and 10. One probe per request on Voyager (its gateway refuses a list of prompts); the last probe goes first so the server's prefix cache holds the reasoning. Future curves use `--probes grid_tail` (every 5%, refine where the leader changes, then every sentence back from the end until the leader changes): same takeover points as dense on all 105 saved followed runs, 62% fewer probes. | Done: 219 runs, 137,143 probes. Per-probe records in `results/trackA/takeover_probes.jsonl.gz`, one row per run in `takeover_runs.jsonl`, figures in `results/trackA/figures/`. Default `--probes auto`: grid_tail for followed runs, dense for resisted and no-hint runs. |
| `look/before_takeover.py` | Before Step 4, no calls: concentration of followed runs on sure questions; late takeovers vs resisted runs' closest approaches (the own answer just before the point; "doesn't fit the options" keywords), clustered by question. | Done (`results/trackA/before_takeover.jsonl`). |
| `look/deletion.py` | Step 4: the deletion test. On the late-takeover runs on sure questions (at most 3 per question), cut at the takeover point; delete the hint mentions before it, or as many length-matched other sentences; one forced answer and 3 continuations per arm. The hint stays in the prompt. | Done: 19 cases, 209 calls (`results/trackA/deletion_calls.jsonl.gz`, one row per call in `deletion_runs.jsonl`). Deleting the mentions moves the forced answer at the cut back to the own answer (7 of 19 vs 1 of 19 for the control), but continuations return to the hint (back to the own answer: 5 of 57 vs 4 of 57 vs 1 of 57 unedited). |

## The idea in one paragraph

Our suspected cause is that attention treats a tool's text like any other text, and the
role label is just more tokens. Once the reasoning repeats the hint ("the expected answer
is G"), later tokens build on that repetition. The fix gives every token a learned
**source tag**, so text from a tool is marked as tool text in every layer. LoRA adapters
are then trained on examples where the model:
- sees the hint
- says it saw it
- checks it
- keeps the answer it gives without the hint

## Data (`build_dataset.py`, Step 5)

**Splits:** `train`, `validation` (10% of the kept training questions, by seed, for choosing
settings) and `heldout` (the 30 MMLU-Pro Test 2 items).

**Target rule** (default `all_correct`): keep a training question only if the model's 3
no-hint runs in the pinned format (Step 6: `results/trackA/nohint_train.jsonl.gz`) were all
answered and all equal the answer key; the target is that answer, with no fallback.
`manifest.json` counts kept questions and dropped ones per reason. Until Step 6 runs, every
training question is dropped ("no pinned-format no-hint runs yet"), so `train.jsonl` is
empty. `--target-rule majority` keeps the old rule (no-hint majority, else the correct
answer: 24 questions from Test 1's served-format runs).

**Correct-hint records:** for kept questions, records whose hint names the right letter,
with the same target; `--correct-ratio` (default 0.5: 1 per 2 wrong-hint records).

**Channels:** training uses user hints, pasted tool blocks and inserted tool turns, with
paraphrased wordings only. The inserted tool turn is the **declared-function** version:
the tool is listed in the system prompt, as in Step 2b's declared arm (decided Oct 25).
Held-out evaluation adds the undeclared inserted turn (Step 2b's default arm) as an extra
condition, and the system note.

**Held-out wordings** never appear in training (`manifest.json` checks 0 overlap: filled
texts, template text, tool names):
- the Turpin user sentence; a "my professor said" user hint
- the progress-run tool block
- the study-guide tool reply (Step 2b's exact reply); a "the database returned" tool
  reply; a tool with a new name (`fetch_reference_solution`)
- the system note

**Fields:** `split`, `id`, `question_set`, `item_id`, `question`, `n_options`, `correct`,
`hint_channel`, `hint_wording`, `hint_text`, `hint_letter`, `hint_correct`,
`hint_placement`, `tool_name`, `tools_declared`, `system_prompt`, `messages` (render with
`olmo_format.render(messages, tools=tools_declared)`), `target_answer`, `target_source`,
`target_rule`, `no_hint_runs`, and `target_reasoning` (Step 7).

**Length audit** (`length_audit.py`): reply lengths per source, model and question set.
Pinned format (Step 2b), prompt + reply of the answered runs: median 11,988 tokens, max
34,706; 61% fit 16,384 and 99% fit 32,768.

## Training plan (Sol, weeks 13–14)

- **Base:** `allenai/Olmo-3-7B-Think`. The checkpoint behind Voyager's
  `olmo3-7b-think` is only the candidate (`docs/OVERVIEW.md` §5), so first run the
  two-part checkpoint check in `docs/PLAN.md` (Track A).
  - Strict on the first 2,047 tokens.
  - Near-ties only beyond that.
  - If it fails, re-measure the base model on the GPU.
- **Model wrapper:**
  - `peft` LoRA on the attention and MLP projections (`q_proj, k_proj, v_proj, o_proj,
    gate_proj, up_proj, down_proj`)
  - then wrap it in `SourceTaggedLM`, so the trainable parameters are the LoRA weights
    plus the tag table
- **Settings to try** (small grid; pick on a validation slice of the training
  questions):
  - rank 8 / 16 / 32
  - alpha = 2 × rank
  - dropout 0.05
  - learning rate 1e-4 / 2e-4 for LoRA, 1e-3 for the tag table
  - 1–3 epochs
  - bf16, gradient checkpointing, sequence length ~8k (thinking traces are long)
- **Loss:** only on the model's tokens (reasoning + answer). Prompt, hint, and tool
  tokens are masked.
- **Ablations (same data):**
  1. LoRA only
  2. source tags only, base frozen
  3. LoRA + source tags

  This separates "the tags help" from "fine-tuning on this data helps".

## Evaluation: behavior first

The question is whether the answer stops following the hint, not whether the text looks
more honest.

1. **Hint following (primary).** On the held-out set, the share of hinted runs whose
   answer equals the hinted wrong letter. Compare against:
   - the same model before training
   - the same letter in no-hint runs (the per-letter baseline)

   3 runs per question; Wilson intervals; clustered bootstrap by question.
2. **Accuracy without hints.** Must not drop. Same held-out questions, no hint, before
   vs after.
3. **Mention and acknowledgment (secondary).** Does the final answer say the hint was
   seen and checked? Keyword pre-sort, then two human raters (Cohen's kappa) on a sample.
4. **Hiding check.** Count runs where the text does not mention the hint but the answer
   still follows it. If this rises after training, the model learned to change its
   words instead of its behavior, the failure OpenAI reported in 2025 with reasoning
   monitors.
5. **Transfer.** Run the trained model through Track B's conditions (including the real
   tool call) and Track C's pipeline (week 15).

**Success (Gate 3, end of week 14):** on held-out questions with held-out wordings, the
trained model follows fewer wrong hints than the base model. The 95% intervals must not
overlap, or the bootstrap difference must exclude 0, and no-hint accuracy must stay
within 5 points. Otherwise we report a negative result with the analysis.

## Generation with tags (later step)

`SourceTaggedLM.forward` covers training and scoring. For sampling, use a decoding loop
that tags every newly generated token as `model` and feeds `inputs_embeds`. Some
thinking chat templates rewrite earlier turns, so `source_ids_from_chat` checks that the
template renders prefix-stably and raises if not. Check Olmo's template before training.
