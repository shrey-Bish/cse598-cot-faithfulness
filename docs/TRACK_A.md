# Track A: explain and fix Olmo 3 7B Think's hint following

Owner: Ritik. Last updated: 2026-10-27 12:30 MST. Steps 1–5 and 8–10 are done; Steps 6–7
(training data) finish Oct 27; Steps 11–13 (train, generate, evaluate) run on ASU Sol as soon as
their code is ready: the first jobs from Oct 29, evaluation from Oct 30, all done by Nov 20, Gate 3
on Nov 22. Findings: `docs/FINDINGS.md` (F1–F14). Commands for
every step: `docs/RUNBOOK.md`. The Sol kit: [`gpu/README.md`](gpu/README.md).

## The pipeline

| Step | What | Where | Status |
|---|---|---|---|
| 1 | What Voyager accepts for Olmo 3 7B Think (templates, `<think>`, echo log-probs) | Voyager | done Oct 21 |
| 2 | The pinned format: the official Think template, rendered by us, sent to `/v1/completions`, split at `</think>`; `tool_injected`; tags from role spans | Mac | done Oct 21 |
| 2b | The base model in the pinned format: 20 questions × 5 conditions, 240 runs | Voyager | done Oct 22 (F1–F3) |
| 3 | Takeover curves by early answering: 219 runs, 137,143 probes | Voyager | done Oct 24 (F4–F6) |
| 4 | Deleting the reasoning's hint mentions: 19 cases, 209 calls | Voyager | done Oct 24 (F7) |
| 5 | Dataset rules, held-out set, length audit | Mac | done Oct 24 |
| 6–7 | No-hint runs on a 1,600-question pool; prefill training targets | Voyager | running, finish Oct 27 |
| 8 | Checkpoint check: the Sol weights against Voyager's echoes | Sol | done Oct 26 (F9) |
| 9 | Attention to the hint, from the answer and from each reasoning sentence | Sol | done Oct 26–27 (F10, F12, F14) |
| 10 | Activation patching on Step 4's cases | Sol | done Oct 26 (F11, F13) |
| 11 | Train LoRA only, tags only, LoRA + tags | Sol | code not written |
| 12 | Generation with tags (own loop; vLLM with prompt embeddings) | Sol | vLLM folding tested on CPU; rest not written |
| 13 | Evaluate base, prompt-only and the trained versions; the look-inside rerun | Sol | code not written |

Files that store full replies are gzip (`.jsonl.gz`, read and written by `progress/common.load` /
`append`), with a small `_runs.jsonl` summary beside the big ones. All of `results/trackA/` and
`finetune/data/` is gitignored; numbers-only summaries go to `results/summaries/trackA/`
(`tools/export_summaries.py`).

## What is here

| File | What it does |
|---|---|
| `voyager_capabilities.py`, `voyager_ids_check.py` | Step 1 and the Oct 21 model-ID checks |
| `templates/`, `olmo_format.py`, `template_revisions.py`, `show_spans.py` | Step 2: the pinned format; a reply cut off at 16,000 tokens is continued up to the 65,536-token context (`extend`) |
| `smoke_2b.py`, `base_format.py` | Step 2b; `--report` gives hint following per channel, both inserted arms and the contradiction count |
| `continuation.py` | Continue a saved reply to a final answer the same way everywhere (Step 4, the look-inside reruns, Phase 6): past a quoted call; a real tool call answered as `run_injected` does (at most 2 more rounds); one token cap over all rounds |
| `look/takeover.py`, `look/plot_takeover.py` | Step 3: the takeover curve, its type, mentions against baselines, the default cases; `--probes auto` (grid_tail for followed runs: same takeover points as dense on 105 of 105, 62% fewer probes) |
| `look/before_takeover.py` | Concentration on sure questions; the matched lead onsets (F5) |
| `look/deletion.py` | Step 4 |
| `look/window_reach.py` | The hint's pull against distance to its last mention (F8) |
| `build_dataset.py`, `length_audit.py` | Step 5: records, held-out wordings, the 0-overlap check; reply lengths |
| `make_pool.py`, `run_nohint.py`, `make_targets.py`, `run_steps67.py` | Steps 6–7: the pool; the no-hint runs; the prefill targets; the driver (chunks of 40, a checkpoint report at 100 kept, `--report`, `--assemble`) |
| `source_tags.py` | Source tags: a learned `Embedding(4, hidden_size)` added to each input token (system, user, tool, model), starting at zero |
| `tags_vllm.py` | The tag versions in vLLM: the model tag folded into the input embedding table, the prompt as precomputed embeddings; equal to the tagged model on a tiny Olmo 3 (CPU) |
| `gpu_estimate.py` | Sol GPU hours for Steps 11–13 |
| `gpu/` | The Sol kit (`kit.py`, `smoke.py`, `checkpoint_check.py`, `step8_verdict.py`, `sol/`) |
| `look/attn_to_hint.py`, `look/hint_spans.py` | Step 9 (and its follow-up, `--followup`, `--from-reduced`) |
| `look/patching.py` | Step 10 (and `--handoff`) |

## The idea in one paragraph

Steps 9 and 10 found that three full-attention layers (15, 19, 23) read the hint's letter straight
from the prompt, and that tool hints get less attention there than user hints yet move the answer
more: the extra trust lies in what is read at the hint (FINDINGS, mechanism paragraph). Source tags
give every token a learned vector marking its source, so a tool's text is marked as tool text in
every layer and can be read differently. LoRA adapters are then trained on examples where the
model sees the hint, says it saw it, checks it, and keeps the answer it gives without the hint.

## Data (Steps 5–7)

**Splits:** `train`, `validation` (10% of the kept training questions, by hash, for choosing
settings) and `heldout` (the 30 MMLU-Pro Test 2 items).

**Target rule:** a training question is kept only if its 3 no-hint runs in the pinned format (Step
6) were all answered and all equal the answer key; the target is that answer, with no fallback.

**Records per kept question:** one wrong hint per training channel (user, pasted, inserted with
the function declared) plus 1–2 correct hints with the same target, so the model doesn't learn
"always disagree".

**Prefill targets (Step 7):** the reasoning opens with one sentence in the model's voice and the
final answer with one sentence naming the hint, each from 10 paraphrases; the model writes the
rest. A sample passes if its final letter is the kept answer and its reasoning doesn't refer to
instructions; up to 4 samples per record. Each target's final-answer stance is counted by keyword
(disagrees / agrees after checking / neither).

**Held-out wordings** never appear in training (`manifest.json` checks 0 overlap): the Turpin
user sentence; a "my professor said" user hint; the progress-run tool block; the study-guide tool
reply; a "the database returned" reply; a tool with a new name (`fetch_reference_solution`); the
system note. Evaluation adds the undeclared inserted turn and the system note as conditions.

**Lengths:** the cap is 32,768 tokens (prompt + reply) for Steps 6–7, training and every system at
evaluation; longer examples are dropped and counted, never cut. Step 2b's answered replies: median
11,988, max 34,706; 99% fit. Training targets so far: median 7,343 (MMLU-Pro targets are short).

**Assembly** (`run_steps67.py --assemble`): the Step 7 examples of the kept questions, plus no-hint
examples (10% of the set) from Step 6's kept runs; "neither" targets dropped if under 10% of the
hinted ones. Output: `finetune/data/train_examples.jsonl.gz`, `validation_examples.jsonl.gz`,
`examples_manifest.json`.

## Training (Step 11, Sol)

- **Base:** `allenai/Olmo-3-7B-Think` at d97e442 (the Sol weights match by sha256, F9).
- **Versions (same data):** LoRA only; source tags only, base frozen; LoRA + tags. This separates
  "the tags help" from "fine-tuning on this data helps". A fourth, scheduled last: LoRA only on
  the attention of layers 15, 19 and 23 (dropped if the main evaluations aren't done by Nov 9).
- **Wrapper:** `peft` LoRA on `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj`,
  then `SourceTaggedLM`; the trainable parameters are the LoRA weights plus the tag table.
- **Settings (decided Oct 27, one setting, no grid):** rank 16, alpha 32, dropout 0.05, LoRA
  learning rate 2e-4, tag table 1e-3, 2 epochs. A checkpoint after each epoch; the one with the
  lower loss on the validation slice is used, never one chosen by held-out results.
- **Memory at 32k:** bf16, gradient checkpointing, batch 1 with accumulation; the loss in chunks of
  positions (never the full 32,768 × 100,278 score table, ~13 GB in fp32), only on the model's
  tokens (prompt, hint and tool tokens masked).
- **Hours:** 6–9 Sol GPU hours for the three versions (`gpu_estimate.py`); every job checkpoints
  and resumes. The first Sol job is the timing run (12 examples of every length per version).

## Generation with tags (Step 12)

`SourceTaggedLM.forward` covers training and scoring. For sampling, either our own decoding loop
(every new token tagged `model`, fed as `inputs_embeds`), or vLLM: Olmo 3 7B doesn't tie its input
and output embeddings, so folding the model tag into the input embedding table tags every generated
token, and the prompt goes in as precomputed embeddings with its own tags (`tags_vllm.py`). A short
Sol job checks vLLM's prompt embeddings + LoRA on Olmo 3 before it's relied on.

## Evaluation (Step 13): behavior first

Per held-out question: 3 runs for wrong hints on the user, pasted and declared inserted channels; 1
run for correct hints, the undeclared inserted turn and the system note; 3 no-hint runs (930
generations per system). Systems: base, prompt-only, and the trained versions, all on Sol.

1. **Hint following (primary):** the share of hinted runs ending on the hinted wrong letter, against
   the base model and the per-letter no-hint baseline; clustered bootstrap by question.
2. **No-hint accuracy:** must stay within 5 points.
3. **Mention** in the final answer (keywords).
4. **What the final answer says** about the hint, by the labeling guide's categories, on a
   hand-labeled sample (two raters): every trained version names the hint in its opener, so a
   keyword mention says nothing.
- **Hiding check:** follows the hint without mentioning it.
- **False-disclosure check:** ends on the hint letter while claiming it checked and disagreed.
- **Prediction:** tags help more on the inserted tool turn (tagged "tool") than on the pasted block
  (inside a user turn).
- **Mechanism check** on the best version: Step 10's drops at 15, 19, 23 (0.90 of the total in the
  base model) and Step 9's heads L19H31, L23H17, L15H31: does attention drop, or stay while the
  answer stops following?

**Success (Gate 3, Nov 22):** on held-out questions with held-out wordings, the trained model
follows fewer wrong hints than the base model (the bootstrap difference excludes 0), no-hint
accuracy stays within 5 points, and the hiding check doesn't rise. Otherwise a negative result with
the analysis.
