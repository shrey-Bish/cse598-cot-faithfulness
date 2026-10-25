"""Track A: GPU hours (A100 80GB) and cost for training and evaluation, from the measured lengths.
No calls; arithmetic on Step 2b's lengths and Olmo 3 7B's shape. Replace the assumptions with
Step 11's 20-step timing run and Step 12's decoding timing when they exist.

  python finetune/gpu_estimate.py --dry-run           # the inputs
  python finetune/gpu_estimate.py --examples 3000     # the table

Training: 3 versions (LoRA only, tags only, LoRA + tags), at most 2 epochs, max length 32,768
(longer examples dropped), bf16, gradient checkpointing, loss in chunks. Every version runs a
full backward pass through the frozen base (tags only too), so each costs about the same:
6 x parameters per token (forward, recomputed forward, backward to the activations) plus
attention (4 x the forward). Throughput = model FLOPs utilisation x 312 TFLOP/s.
Evaluation (Phase 6): the held-out set per system = 30 questions x (7 held-out wordings x wrong
and correct hint + no hint) x 3 runs. Base and prompt-only run in full on Voyager, with 10% of
their held-out set also on the GPU as a cross-check; the three trained versions run in full on
the GPU (LoRA only with vLLM, the tag versions with the Step 12 decoding loop).
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import load  # noqa: E402

CONFIG = next(Path.home().glob(".cache/huggingface/hub/models--allenai--Olmo-3-7B-Think/snapshots/*/config.json"), None)
PARAMS = 7.3e9
PEAK = 312e12                       # A100 bf16 dense
MFU = (0.30, 0.45)
MAX_LEN = 32768
EPOCHS, VERSIONS = 2, 3
EVAL_QUESTIONS, EVAL_WORDINGS, EVAL_RUNS = 30, 7, 3
VLLM_TOK_S = (300, 800)            # aggregate decode tokens/s, 7B at 10-30k context on one A100 80GB
LOOP_TOK_S = (150, 400)            # the tag versions' own decoding loop (batched, with a KV cache)
VOYAGER_TOK_S = 4 * 50              # 4 in flight x Step 2b's measured ~50-53 tokens/s per stream
PRICES = (1.2, 2.5, 4.5)            # $/h for an A100 80GB: marketplace, specialist cloud, hyperscaler on demand


def shape():
    c = json.loads(CONFIG.read_text()) if CONFIG else {"hidden_size": 4096, "num_hidden_layers": 32,
                                                        "sliding_window": 4096, "layer_types": ["full_attention"] * 32}
    kinds = c.get("layer_types") or ["full_attention"] * c["num_hidden_layers"]
    return c["hidden_size"], sum(k == "full_attention" for k in kinds), sum(k != "full_attention" for k in kinds), \
        c.get("sliding_window") or 4096


def lengths():
    """(prompt + reply of Step 2b's answered runs, reply of every run, reply capped at 16,000)."""
    from finetune import base_format as bf
    rows = [r for r in bf.current(load(bf.OUT)) if r["status"] == "ok"]
    answered = [r["usage"]["prompt_tokens"] + r["usage"]["completion_tokens"] for r in rows if r["finish_reason"] != "length"]
    replies = [r["usage"]["completion_tokens"] for r in rows]
    return answered, replies, [min(x, 16000) for x in replies]


def train_flops_per_token(length):
    d, n_full, n_swa, window = shape()
    ctx_full, ctx_swa = length / 2, min(length / 2, window)        # causal: on average half the sequence
    attn_fwd = 4 * d * (n_full * ctx_full + n_swa * ctx_swa)
    return 6 * PARAMS + 4 * attn_fwd


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--examples", type=int, default=3000)
    a = ap.parse_args()
    answered, replies, capped = lengths()
    kept = [x for x in answered if x <= MAX_LEN]
    print(f"inputs: Step 2b, {len(answered)} answered runs: prompt + reply median {statistics.median(answered):,.0f}, "
          f"mean {statistics.mean(kept):,.0f} for the {len(kept)} at or under {MAX_LEN:,} ({len(answered) - len(kept)} "
          f"dropped); reply per run mean {statistics.mean(replies):,.0f} (continued to the context) or "
          f"{statistics.mean(capped):,.0f} (capped at 16,000); model shape from {CONFIG.name if CONFIG else 'defaults'}: "
          f"{shape()}")
    if a.dry_run:
        return
    flops = sum(train_flops_per_token(x) * x for x in kept) / len(kept)          # per example
    per_epoch = a.examples * flops
    train_h = [VERSIONS * EPOCHS * per_epoch / (m * PEAK) / 3600 for m in MFU]
    gens = EVAL_QUESTIONS * (EVAL_WORDINGS * 2 + 1) * EVAL_RUNS
    rows = []
    for label, mean_reply in (("continued to the context", statistics.mean(replies)),
                              ("capped at 16,000 (the brief)", statistics.mean(capped))):
        tokens = gens * mean_reply
        lora = [tokens / t / 3600 for t in VLLM_TOK_S[::-1]]
        tags = [2 * tokens / t / 3600 for t in LOOP_TOK_S[::-1]]
        cross = [0.2 * tokens / t / 3600 for t in VLLM_TOK_S[::-1]]
        voy = 2 * tokens / VOYAGER_TOK_S / 3600
        rows.append((label, tokens, lora, tags, cross, voy))
    print(f"\nTraining, {a.examples:,} examples x {EPOCHS} epochs x {VERSIONS} versions: "
          f"{train_h[1]:.0f}-{train_h[0]:.0f} GPU-hours (model FLOPs utilisation {MFU[1]:.0%}-{MFU[0]:.0%}); "
          f"1 epoch: {train_h[1] / 2:.0f}-{train_h[0] / 2:.0f}")
    print(f"Evaluation: {gens:,} generations per system ({EVAL_QUESTIONS} questions x ({EVAL_WORDINGS} wordings x 2 + "
          f"no hint) x {EVAL_RUNS} runs)")
    print("| replies | GPU: LoRA only (vLLM) | GPU: tags only + LoRA + tags (own loop) | GPU: 10% cross-check of base and "
          "prompt-only | GPU total, eval | Voyager: base + prompt-only, full |")
    print("|---|---|---|---|---|---|")
    for label, tokens, lora, tags, cross, voy in rows:
        tot = [lora[i] + tags[i] + cross[i] for i in (0, 1)]
        print(f"| {label} ({tokens / 1e6:.1f}M tokens per system) | {lora[0]:.0f}-{lora[1]:.0f} h | {tags[0]:.0f}-{tags[1]:.0f} h "
              f"| {cross[0]:.1f}-{cross[1]:.1f} h | {tot[0]:.0f}-{tot[1]:.0f} h | {voy:.0f} h |")
    for label, tokens, lora, tags, cross, voy in rows:
        lo = train_h[1] + lora[0] + tags[0] + cross[0]
        hi = train_h[0] + lora[1] + tags[1] + cross[1]
        print(f"All GPU work, replies {label}: {lo:.0f}-{hi:.0f} A100-hours; cost "
              + ", ".join(f"${p}/h: ${lo * p:,.0f}-${hi * p:,.0f}" for p in PRICES))


if __name__ == "__main__":
    main()
