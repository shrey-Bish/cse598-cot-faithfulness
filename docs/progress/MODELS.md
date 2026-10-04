# Models: exact endpoints, checkpoints, and how each pair differs

Working notes for Group 10. These numbers come from `docs/progress/RESULTS_SUMMARY.json`
(sections `pilot.output_tokens` and `timing`). The catalog check ran on 2026-10-04.

## What the Voyager catalog says

`GET /models` lists 55 IDs (saved in `cot-disclosure/results/progress/model_catalog.json`).
All six study models are there. For these six, the catalog gives only:
`owned_by: obleth`, `quantization: bf16`, `mode: chat`, and tags (`general`, `fast`,
`reasoning`, `math`). It has **no** upstream repository name, revision, or `variant_of`
field for them. So the upstream checkpoint for each ID below is a **candidate**, inferred
from the ID. The serving metadata doesn't confirm it.

## One row per model

| Voyager ID | Family | Size | Track | Candidate upstream model card | Reasoning field (streamed) | Pilot median output tokens, no hint | Pilot mean output tokens, all 144 main-grid runs | Timing run: tokens / latency (pilot puzzle 0) |
|---|---|---|---|---|---|---|---|---|
| `olmo3-7b-instruct` | Olmo 3 | 7B | instruct | allenai/Olmo-3-7B-Instruct | none | 2,020.5 | 2,619 | 1,065 / 9.2 s |
| `olmo3-7b-think` | Olmo 3 | 7B | thinking | allenai/Olmo-3-7B-Think | `reasoning` | 8,025.5 | 8,535 | 7,261 / 68.3 s |
| `olmo3-32b-instruct` | Olmo 3 or 3.1 (**unconfirmed**) | 32B | instruct | allenai/Olmo-3.1-32B-Instruct (the only 32B Instruct card on our candidate list) | none | 1,669 | 2,244 | 1,005 / 33.1 s |
| `olmo3-32b-think` | Olmo 3 or 3.1 (**unconfirmed**) | 32B | thinking | allenai/Olmo-3-32B-Think or allenai/Olmo-3.1-32B-Think | `reasoning` | 5,725 | 6,209 | 3,844 / 121.5 s |
| `qwen3-30b-a3b-instruct-2507` | Qwen3 | 30.5B total, 3.3B active | instruct (never thinks) | Qwen/Qwen3-30B-A3B-Instruct-2507 | none | 891 | 995 | 951 / 10.2 s |
| `qwen3-30b-a3b-thinking-2507` | Qwen3 | 30.5B total, 3.3B active | thinking (always thinks) | Qwen/Qwen3-30B-A3B-Thinking-2507 | `reasoning` | 3,996.5 | 4,252 | 3,951 / 40.0 s |

On MMLU-Pro (timing run, one item, no cue): `olmo3-7b-instruct` 707 tokens in 5.9 s,
`olmo3-7b-think` 7,959 tokens in 75.6 s, `qwen3-30b-a3b-thinking-2507` 4,724 tokens in 47.8 s.

**Usage fields.** The streamed `usage` block reports `completion_tokens`. It does not
report a separate reasoning-token count (`completion_tokens_details` is absent), so output
tokens here include private reasoning.

**Reasoning field name.** In the streamed deltas, thinking models now send private
reasoning in a field named `reasoning`. The repo README (checked 2026-10-01 and 02) says
`reasoning_content`. `client.py` reads both, so nothing broke. We now log the field name
on every call.

**Seeded replays.** We repeated the pilot's first no-hint call (puzzle 0, seed 0) on all
six models. Four replies came back byte-identical in length and answer: Olmo 3 7B Instruct
and Think, and Qwen3 Instruct and Thinking. The two Olmo 32B endpoints gave different
replies (32B Instruct 1,005 tokens vs 1,305 in the pilot; 32B Think 3,844 vs 4,683).
Either the 32B serving setup isn't deterministic under a seed, or the checkpoint behind the
ID changed between the pilot and today. We can't tell which from the API. This is one more
reason to keep the 32B identity marked unconfirmed.

## Architecture (from the upstream model cards; not checked against the served weights)

| | Olmo 3 7B | Olmo 3 / 3.1 32B | Qwen3-30B-A3B (2507) |
|---|---|---|---|
| Type | dense transformer | dense transformer | mixture of experts |
| Layers | 32 | 64 | 48 |
| Attention | multi-head | grouped-query, 40 query / 8 KV heads | grouped-query, 32 query / 4 KV heads |
| Sliding-window attention | in 3 of every 4 layers | in 3 of every 4 layers | no |
| Experts | none | none | 128, 8 active per token |
| Parameters | 7B | 32B | 30.5B total, 3.3B active |
| Context | 65K | 65K | 262K |

## Sampling settings we actually used

Same for every answerer call in the pilot and in Experiment B:
- temperature 0.6
- `max_tokens` 16,000
- seed = repeat index (0, 1, 2 for no-hint repeats; 0 or 1 for hinted runs)
- streamed (`stream: true`, `stream_options.include_usage: true`)
- no system prompt, one user turn
- top_p, top_k and other sampling settings left at server defaults
- `reasoning_effort` not sent. Per the README, Voyager accepts it but it has no effect.

Experiment A reviewer (`qwen3-30b-a3b-instruct-2507`): temperature 0.6, `max_tokens`
2,000, seeds 0, 1, 2 for its three repeats, plus a fixed system prompt (see
`EXPERIMENT_A.md`).

## How each pair differs (matched size does not isolate thinking)

Each pair shares a size and a base model, but the two members are separately post-trained
checkpoints. A difference between them could come from thinking, or from anything else
that differs in post-training: data, preference tuning, RL. Our instruct-vs-thinking
comparisons describe **checkpoints**, not the effect of thinking alone.

- **Olmo 3 7B Instruct vs Think.** Same Olmo 3 7B base. Two separate post-training tracks,
  each running SFT, then DPO, then RL (RLVR), with different data in each track. Think is
  trained to write a long private trace. Instruct is trained for direct chat replies.
- **Olmo 3 32B Instruct vs Think.** Same Olmo 3 32B base. Olmo 3.1 32B Think continued
  the Olmo 3 32B Think RL run for longer. Olmo 3.1 32B Instruct applies the 7B Instruct
  recipe at 32B. Which of these the Voyager IDs serve is **unconfirmed** (see above).
- **Qwen3-30B-A3B Instruct-2507 vs Thinking-2507.** The original Qwen3 checkpoints had
  one switchable hybrid model. The 2507 update split it into two separately post-trained
  checkpoints: one always thinks, one never thinks.

To vary the **amount** of thinking without changing weights, we use the "think briefly"
prompt on the same thinking checkpoint (pilot: private reasoning 29.8% shorter on Olmo 3
7B Think and 47.7% shorter on Qwen3 30B Thinking, median characters over 48 paired runs
each).

## How "no chain-of-thought" interacts with built-in thinking

On Voyager, thinking can't be switched off. The README records that
`enable_thinking: false` was ignored on all 7 thinking models tried. So an "answer only,
no explanation" prompt doesn't remove reasoning from a thinking model. It only moves the
question to whether the model still reasons privately. Pilot "answer only" test (24
puzzles, seed 0, vs the same model's step-by-step no-hint run):

| Model | Still produced a private trace | Accuracy, answer only | Accuracy, step by step |
|---|---|---|---|
| Olmo 3 7B Think | 21/24 | 23/24 | 22/24 |
| Qwen3 30B Thinking | 23/24 | 24/24 | 24/24 |
| Olmo 3 7B Instruct | 0/24 (has no private channel) | 1/24 | 21/24 |
| Qwen3 30B Instruct | 0/24 | 2/24 | 24/24 |

Chance is 1/7 on these seven-option puzzles. "No chain-of-thought" therefore means two
different things:
- For an instruct model, it really removes the reasoning, and accuracy falls to about
  chance.
- For a thinking model, it only removes the visible explanation. The private reasoning
  continues and accuracy holds.

Any "no-CoT" condition in the final study has to be read per track.
