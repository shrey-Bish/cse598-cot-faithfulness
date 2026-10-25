"""Track A: Sol GPU hours (one A100-class GPU) for Steps 8-13, from the measured lengths. No calls.

  python finetune/gpu_estimate.py --dry-run                 # the inputs
  python finetune/gpu_estimate.py --examples 1200           # the table

Assumptions (replace them with Step 11's 20-step timing run and a Step 12 decoding timing):
  - training: 3 versions (LoRA only, tags only, LoRA + tags), at most 2 epochs, every token
    capped at 32,768 per example (longer ones dropped), bf16, gradient checkpointing, loss in
    chunks. Every version runs a full backward pass through the frozen base (tags only too):
    6 x parameters per token plus attention (4 x its forward). Speed = model FLOPs utilisation
    (30-45%) x 312 TFLOP/s. Example lengths: the Step 7 pilot's targets (prompt + reply).
  - evaluation (Phase 6), per system and question: 3 runs for wrong hints on the user (2
    held-out wordings), pasted (1) and declared inserted (3) channels; 1 run for correct hints
    on those 6 wordings and for the undeclared inserted and system channels (wrong and correct);
    3 no-hint runs. Replies as long as Step 2b's on these questions, capped at 32,768 tokens with
    the prompt. Base and prompt-only run in full on Voyager, 10% of them again on Sol as a
    cross-check; the three trained versions run in full on Sol.
  - decoding speed on one A100 80GB, Olmo 3 7B at 10-30k tokens of context: vLLM 250-700
    tokens/s in all (Olmo 3 runs through vLLM's Transformers backend); the tag versions' own loop
    150-400 tokens/s, or vLLM if Sol confirms prompt embeddings + LoRA (finetune/tags_vllm.py).
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
CAP = 32768
EPOCHS, VERSIONS = 2, 3
QUESTIONS = 30
PER_QUESTION = {"wrong hints, 3 runs (user x2, pasted, declared inserted x3)": 6 * 3,
                "correct hints, 1 run (the same 6 wordings)": 6,
                "undeclared inserted, 1 run (wrong, correct)": 2, "system note, 1 run (wrong, correct)": 2,
                "no hint, 3 runs": 3}
VLLM_TOK_S = (250, 700)
LOOP_TOK_S = (150, 400)
VOYAGER_TOK_S = 4 * 50              # 4 in flight x Step 2b's ~50 tokens/s per stream
LOOK_INSIDE = {"Step 8, checkpoint check (5 forward passes)": (0.1, 0.3),
               "Step 9, attention to the hint (~100 saved runs, one forward pass each, hooks)": (1, 3),
               "Step 10, patching (26 cases x 32 layers, forward passes)": (2, 5),
               "Step 13, look inside again on the best version (Steps 3, 9, 10)": (4, 10)}


def shape():
    c = json.loads(CONFIG.read_text()) if CONFIG else {"hidden_size": 4096, "num_hidden_layers": 32,
                                                        "sliding_window": 4096, "layer_types": ["full_attention"] * 32}
    kinds = c.get("layer_types") or ["full_attention"] * c["num_hidden_layers"]
    return (c["hidden_size"], sum(k == "full_attention" for k in kinds), sum(k != "full_attention" for k in kinds),
            c.get("sliding_window") or 4096)


def train_lengths():
    """Prompt + target tokens of the Step 7 pilot's examples (prefill if it has run), and Step 6's
    kept no-hint runs (the no-hint examples)."""
    for name in ("targets_prefill.jsonl.gz", "targets.jsonl.gz"):
        ex = list({e["record_id"]: e for e in load(CODE / "results" / "trackA" / name)}.values())
        if ex:
            return [e["tokens"] for e in ex if not e["dropped_for_length"]], name
    return [], None


def eval_replies():
    """Step 2b's replies on the held-out questions, capped at 32,768 tokens with the prompt."""
    from finetune import base_format as bf
    rows = [r for r in bf.current(load(bf.OUT)) if r["status"] == "ok"]
    return [min(r["usage"]["completion_tokens"], CAP - r["usage"]["prompt_tokens"]) for r in rows]


def flops_per_token(length):
    d, n_full, n_swa, window = shape()
    attn_fwd = 4 * d * (n_full * length / 2 + n_swa * min(length / 2, window))
    return 6 * PARAMS + 4 * attn_fwd


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--examples", type=int, default=1200)
    a = ap.parse_args()
    lengths, source = train_lengths()
    replies = eval_replies()
    gens = QUESTIONS * sum(PER_QUESTION.values())
    print(f"inputs: training examples from {source}: {len(lengths)} pilot targets, prompt + reply mean "
          f"{statistics.mean(lengths):,.0f} (median {statistics.median(lengths):,.0f}); evaluation replies (Step 2b, "
          f"capped at {CAP:,} with the prompt): mean {statistics.mean(replies):,.0f}; {gens} generations per system "
          f"({PER_QUESTION}); model shape {shape()}")
    if a.dry_run:
        return
    per_example = statistics.mean(flops_per_token(x) * x for x in lengths)
    train = [VERSIONS * EPOCHS * a.examples * per_example / (m * PEAK) / 3600 for m in MFU[::-1]]
    tokens = gens * statistics.mean(replies)
    lora = [tokens / t / 3600 for t in VLLM_TOK_S[::-1]]
    tags_loop = [2 * tokens / t / 3600 for t in LOOP_TOK_S[::-1]]
    tags_vllm = [2 * tokens / t / 3600 for t in VLLM_TOK_S[::-1]]
    cross = [0.2 * tokens / t / 3600 for t in VLLM_TOK_S[::-1]]
    look = [sum(v[0] for v in LOOK_INSIDE.values()), sum(v[1] for v in LOOK_INSIDE.values())]
    print(f"\n| job | Sol GPU hours (one A100) |")
    print("|---|---|")
    print(f"| Step 11, training: {a.examples:,} examples x {EPOCHS} epochs x {VERSIONS} versions | "
          f"{train[0]:.0f}-{train[1]:.0f} (1 epoch: {train[0] / 2:.0f}-{train[1] / 2:.0f}) |")
    print(f"| Step 13, evaluation, LoRA only (vLLM), {gens} generations, {tokens / 1e6:.1f}M tokens | "
          f"{lora[0]:.0f}-{lora[1]:.0f} |")
    print(f"| Step 13, evaluation, the two tag versions: own loop / vLLM with prompt embeddings | "
          f"{tags_loop[0]:.0f}-{tags_loop[1]:.0f} / {tags_vllm[0]:.0f}-{tags_vllm[1]:.0f} |")
    print(f"| Step 13, 10% cross-check of base and prompt-only | {cross[0]:.1f}-{cross[1]:.1f} |")
    for name, (lo, hi) in LOOK_INSIDE.items():
        print(f"| {name} | {lo:g}-{hi:g} |")
    for label, tags in (("tag versions in their own loop", tags_loop), ("tag versions in vLLM", tags_vllm)):
        lo = train[0] + lora[0] + tags[0] + cross[0] + look[0]
        hi = train[1] + lora[1] + tags[1] + cross[1] + look[1]
        print(f"Total, {label}: {lo:.0f}-{hi:.0f} Sol GPU hours")
    print(f"Voyager (not Sol): base and prompt-only in full, {2 * tokens / VOYAGER_TOK_S / 3600:.0f} hours at 4 in flight.")


if __name__ == "__main__":
    main()
