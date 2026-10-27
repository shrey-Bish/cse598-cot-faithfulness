"""Track A, Step 11: train the fix (on Sol, one A100 80GB; CPU tests on a tiny Olmo 3).

Versions, all on the same data (finetune/data/train_examples.jsonl.gz from run_steps67.py --assemble):
  lora         LoRA on every attention and MLP projection
  tags         source tags only (finetune/source_tags.py), the base model frozen
  lora_tags    LoRA + source tags
  lora_attn3   the fourth version, scheduled last: LoRA on the attention projections of layers 15, 19
               and 23 only (where Step 10 sees the hint's effect leave the hint tokens, F11)
Settings (decided Oct 27, one setting): rank 16, alpha 32, dropout 0.05; learning rate 2e-4 for LoRA,
1e-3 for the tag table; 2 epochs; batch 1 with ACCUM examples per optimizer step (each example's mean
loss weighs the same); WARMUP of the steps rising linearly, then a linear decay to 0. bf16 weights,
gradient checkpointing. The loss is only on the model's own tokens: the reply after the prompt's
"<think>", through the template's closing <|endoftext|> (system, user, hint and tool tokens, and the
tool call we write for the model, are masked); it is computed over chunks of CHUNK positions, never the
full positions x 100,278 table.

Checkpoints: out/latest/ every SAVE_EVERY optimizer steps and on SIGTERM / SIGUSR1 (at the next
optimizer step; a job can then resubmit and resume), and out/epoch<k>/ after each epoch with its loss on
the validation slice (validation_examples.jsonl.gz). chosen.json names the epoch with the lower
validation loss: never chosen by held-out results. The end of the last epoch (or --export) writes the chosen epoch as a PEFT adapter
(LoRA versions) and tags.pt (tag versions) under out/final/. Every step of the log is appended to
out/train_log.jsonl.

  python finetune/train.py --version lora --dry-run                      # examples, tokens, steps; no model
  python finetune/train.py --version lora --out OUT                      # train (resumes from OUT/latest)
  python finetune/train.py --version lora,tags,lora_tags --timing 20 --out OUT   # S1: 20 longest examples each
  python finetune/train.py --version lora --out OUT --export             # the chosen epoch -> OUT/final/
"""
import argparse
import gzip
import json
import math
import os
import random
import signal
import sys
import time
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from finetune import olmo_format  # noqa: E402

VERSIONS = ("lora", "tags", "lora_tags", "lora_attn3")
TRAIN = CODE / "finetune" / "data" / "train_examples.jsonl.gz"
VALIDATION = CODE / "finetune" / "data" / "validation_examples.jsonl.gz"
RANK, ALPHA, DROPOUT = 16, 32, 0.05
LR_LORA, LR_TAGS = 2e-4, 1e-3
EPOCHS = 2
ACCUM = 8
WARMUP = 0.03
MAX_LEN = olmo_format.CAP_TOTAL              # 32,768: prompt + reply; longer examples were dropped at assembly
CHUNK = 1024                                 # positions per piece of the loss
SAVE_EVERY = 25                              # optimizer steps between resume checkpoints
SEED = 0
LORA_ALL = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
LORA_ATTN = ["q_proj", "k_proj", "v_proj", "o_proj"]
ATTN3_LAYERS = [15, 19, 23]


# ---------------------------------------------------------------- data
def load_examples(path):
    with gzip.open(path, "rt") as f:
        return [json.loads(line) for line in f]


def texts(ex):
    """(prompt, full text): the pinned rendering of the example's conversation, and the same with the
    target reply as the final assistant turn (the template closes it with <|endoftext|>)."""
    prompt = olmo_format.render(ex["messages"], tools=ex.get("tools"))
    full = olmo_format.render(ex["messages"] + [{"role": "assistant", "content": olmo_format.THINK_OPEN + ex["target_raw"]}],
                              add_generation_prompt=False, tools=ex.get("tools"))
    if not full.startswith(prompt):
        raise ValueError(f"{ex['record_id']}: the rendered target does not extend the rendered prompt")
    return prompt, full


def encode(tokenizer, ex):
    """{ids, src, labels, n_target}: token ids, one source tag per token (source_tags), and labels that
    are -100 everywhere but the reply. The prompt and the reply are tokenized apart, as at generation
    (the prompt alone, then the reply's tokens after it): "<think>" is not a special token, so
    tokenizing them together can merge its ">" with the reply's first word."""
    from finetune.source_tags import SOURCES, source_ids_from_render
    prompt, full = texts(ex)
    p_ids, p_src, _ = source_ids_from_render(tokenizer, prompt)
    r_ids = list(tokenizer(full[len(prompt):], add_special_tokens=False)["input_ids"])
    return {"record_id": ex["record_id"], "ids": p_ids + r_ids, "src": p_src + [SOURCES["model"]] * len(r_ids),
            "labels": [-100] * len(p_ids) + r_ids, "n_target": len(r_ids)}


def usable(encoded):
    """Examples within MAX_LEN that have reply tokens to learn from (others are counted and left out)."""
    keep, dropped = [], 0
    for e in encoded:
        if len(e["ids"]) <= MAX_LEN and e["n_target"] > 0:
            keep.append(e)
        else:
            dropped += 1
    if dropped:
        print(f"left out {dropped} examples (over {MAX_LEN} tokens or no reply tokens)")
    return keep


def order(n, epoch, seed=SEED):
    """The example order of one epoch (fixed by the seed, so a resumed run continues the same order)."""
    idx = list(range(n))
    random.Random(f"{seed}:{epoch}").shuffle(idx)
    return idx


def schedule(total_steps, warmup=WARMUP):
    w = max(1, round(total_steps * warmup))
    return lambda step: (step + 1) / w if step < w else max(0.0, (total_steps - step) / max(1, total_steps - w))


# ---------------------------------------------------------------- model
def build(version, model_path, dtype="bf16", device="cuda", attn="sdpa", checkpointing=True):
    """The model to train, with only the version's parameters trainable."""
    import torch
    from transformers import AutoModelForCausalLM
    from finetune.source_tags import SourceTaggedLM
    if version not in VERSIONS:
        raise ValueError(f"unknown version {version!r}; one of {VERSIONS}")
    torch_dtype = {"bf16": torch.bfloat16, "fp32": torch.float32}[dtype]
    model = AutoModelForCausalLM.from_pretrained(model_path, dtype=torch_dtype, attn_implementation=attn).to(device)
    model.config.use_cache = False
    if checkpointing:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    for p in model.parameters():
        p.requires_grad_(False)
    if version in ("lora", "lora_tags", "lora_attn3"):
        from peft import LoraConfig, get_peft_model
        attn3 = version == "lora_attn3"
        cfg = LoraConfig(r=RANK, lora_alpha=ALPHA, lora_dropout=DROPOUT, task_type="CAUSAL_LM",
                         target_modules=LORA_ATTN if attn3 else LORA_ALL,
                         layers_to_transform=ATTN3_LAYERS if attn3 else None)
        model = get_peft_model(model, cfg)
    if version in ("tags", "lora_tags"):
        model = SourceTaggedLM(model, freeze_base=False)          # the base is already frozen; LoRA stays trainable
        model.tags.to(device=device, dtype=torch.float32)
    return model


def causal(lm):
    """The underlying causal LM (LoRA layers, if any, are inside it)."""
    from finetune.source_tags import SourceTaggedLM
    m = lm.model if isinstance(lm, SourceTaggedLM) else lm
    return m.get_base_model() if hasattr(m, "get_base_model") else m


def trainable(lm):
    return {n: p for n, p in lm.named_parameters() if p.requires_grad}


def optimizer(lm):
    import torch
    params = trainable(lm)
    groups = [{"params": [p for n, p in params.items() if not n.startswith("tags.")], "lr": LR_LORA},
              {"params": [p for n, p in params.items() if n.startswith("tags.")], "lr": LR_TAGS}]
    return torch.optim.AdamW([g for g in groups if g["params"]], weight_decay=0.0)


def example_loss(lm, ex, device, chunk=CHUNK):
    """(mean loss over the reply's tokens, number of those tokens) for one encoded example."""
    import torch
    import torch.nn.functional as F
    from torch.utils.checkpoint import checkpoint
    from finetune.source_tags import SourceTaggedLM
    ids = torch.tensor([ex["ids"]], device=device)
    model = causal(lm)
    if isinstance(lm, SourceTaggedLM):
        embeds = lm.embed(ids, torch.tensor([ex["src"]], device=device))
    else:
        embeds = model.get_input_embeddings()(ids)
    h = model.get_decoder()(inputs_embeds=embeds, use_cache=False).last_hidden_state[0, :-1]
    target = torch.tensor(ex["labels"][1:], device=device)        # position t predicts token t + 1
    pos = (target != -100).nonzero().squeeze(-1)
    head = model.get_output_embeddings()

    def piece(hp, yp):
        return F.cross_entropy(head(hp).float(), yp, reduction="sum")
    total = h.new_zeros((), dtype=torch.float32)
    for k in range(0, len(pos), chunk):
        p = pos[k:k + chunk]
        total = total + (checkpoint(piece, h[p], target[p], use_reentrant=False) if torch.is_grad_enabled()
                         else piece(h[p], target[p]))
    return total / max(1, len(pos)), len(pos)


def validation_loss(lm, examples, device):
    """Token-weighted mean loss over the validation slice."""
    import torch
    lm.eval()
    total, tokens = 0.0, 0
    with torch.no_grad():
        for ex in examples:
            loss, n = example_loss(lm, ex, device)
            total += loss.item() * n
            tokens += n
    lm.train()
    return total / max(1, tokens), tokens


# ---------------------------------------------------------------- checkpoints
def save_state(lm, path, extra, opt=None, sched=None):
    """Trainable weights (+ optimizer and schedule) and the position, written to a temporary directory
    first and then moved into place, so a job killed while saving leaves the last good checkpoint."""
    import shutil

    import torch
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    torch.save({n: p.detach().cpu() for n, p in trainable(lm).items()}, tmp / "trainable.pt")
    if opt is not None:
        torch.save({"optimizer": opt.state_dict(), "schedule": sched.state_dict(),
                    "torch_rng": torch.get_rng_state(),
                    "cuda_rng": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None},
                   tmp / "optimizer.pt")
    (tmp / "state.json").write_text(json.dumps(extra, indent=1) + "\n")
    old = path.with_name(path.name + ".old")
    shutil.rmtree(old, ignore_errors=True)
    if path.exists():
        path.rename(old)
    tmp.rename(path)
    shutil.rmtree(old, ignore_errors=True)


def load_weights(lm, path):
    import torch
    saved = torch.load(Path(path) / "trainable.pt", map_location="cpu")
    params = trainable(lm)
    if set(saved) != set(params):
        raise ValueError(f"checkpoint {path} holds other parameters than this version trains")
    for n, p in params.items():
        p.data.copy_(saved[n].to(p.device, p.dtype))


def resume(lm, out, opt, sched):
    """The position to continue from ({epoch, index, step}), or the start."""
    import torch
    latest = Path(out) / "latest"
    if not (latest / "state.json").exists():
        return {"epoch": 0, "index": 0, "step": 0}
    load_weights(lm, latest)
    st = torch.load(latest / "optimizer.pt", map_location="cpu", weights_only=False)
    opt.load_state_dict(st["optimizer"])
    sched.load_state_dict(st["schedule"])
    torch.set_rng_state(st["torch_rng"])
    if st.get("cuda_rng") is not None and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(st["cuda_rng"])
    return json.loads((latest / "state.json").read_text())


def choose(out):
    """The saved epoch with the lower validation loss (validation slice only)."""
    eps = sorted(Path(out).glob("epoch*/state.json"))
    rows = [json.loads(p.read_text()) for p in eps]
    rows = [r for r in rows if r.get("validation_loss") is not None]
    if not rows:
        return None
    best = min(rows, key=lambda r: (r["validation_loss"], r["epoch"]))
    chosen = {"epoch": best["epoch"], "validation_loss": best["validation_loss"],
              "by_epoch": {r["epoch"]: r["validation_loss"] for r in rows},
              "rule": "lower loss on the validation slice; never held-out results"}
    (Path(out) / "chosen.json").write_text(json.dumps(chosen, indent=1) + "\n")
    return chosen


# ---------------------------------------------------------------- training
_stop = {"asked": False}


def _on_signal(signum, frame):
    _stop["asked"] = True


def log_row(out, row):
    with open(Path(out) / "train_log.jsonl", "a") as f:
        f.write(json.dumps(row) + "\n")


def train(lm, train_set, val_set, out, device, epochs=EPOCHS, accum=ACCUM, max_steps=None, meta=None):
    """Train to the end (or max_steps optimizer steps, or a signal); returns the final position."""
    import torch
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    steps_per_epoch = math.ceil(len(train_set) / accum)
    total = steps_per_epoch * epochs
    opt = optimizer(lm)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, schedule(total))
    pos = resume(lm, out, opt, sched)
    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGUSR1, _on_signal)
    lm.train()
    group_losses, group_tokens, t0 = [], 0, time.monotonic()
    while pos["epoch"] < epochs:
        idx = order(len(train_set), pos["epoch"])
        while pos["index"] < len(idx):
            ex = train_set[idx[pos["index"]]]
            group_size = min(accum, len(idx) - (pos["index"] - len(group_losses)))   # the last group may be short
            loss, n = example_loss(lm, ex, device)
            (loss / group_size).backward()
            group_losses.append(loss.item())
            group_tokens += n
            pos["index"] += 1
            if len(group_losses) == accum or pos["index"] == len(idx):
                opt.step()
                sched.step()
                opt.zero_grad(set_to_none=True)
                pos["step"] += 1
                log_row(out, {"step": pos["step"], "epoch": pos["epoch"] + 1, "loss": sum(group_losses) / len(group_losses),
                              "examples": len(group_losses), "tokens": group_tokens, "lr": sched.get_last_lr(),
                              "seconds": round(time.monotonic() - t0, 2),
                              "max_memory_gb": round(torch.cuda.max_memory_allocated() / 2 ** 30, 2) if torch.cuda.is_available() else None})
                group_losses, group_tokens, t0 = [], 0, time.monotonic()
                if pos["index"] == len(idx):
                    break
                if pos["step"] % SAVE_EVERY == 0 or _stop["asked"] or (max_steps and pos["step"] >= max_steps):
                    save_state(lm, out / "latest", {**pos, **(meta or {})}, opt, sched)
                if _stop["asked"] or (max_steps and pos["step"] >= max_steps):
                    return pos
        epoch = pos["epoch"] + 1
        vloss, vtok = validation_loss(lm, val_set, device) if val_set else (None, 0)
        save_state(lm, out / f"epoch{epoch}", {"epoch": epoch, "validation_loss": vloss, "validation_tokens": vtok,
                                               "step": pos["step"], **(meta or {})})
        log_row(out, {"epoch_done": epoch, "validation_loss": vloss, "validation_tokens": vtok, "step": pos["step"]})
        pos = {"epoch": epoch, "index": 0, "step": pos["step"]}
        save_state(lm, out / "latest", {**pos, **(meta or {})}, opt, sched)
        choose(out)
    return pos


def timing(version, model_path, train_set, n, device, out):
    """S1: forward + backward + optimizer step on the n longest examples; seconds against tokens, the
    peak memory, and the training time this predicts for the whole set (both epochs + validation)."""
    import torch
    lm = build(version, model_path, device=device)
    opt = optimizer(lm)
    longest = sorted(train_set, key=lambda e: -len(e["ids"]))[:n]
    rows = []
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    lm.train()
    for ex in longest:
        t = time.monotonic()
        loss, _ = example_loss(lm, ex, device)
        loss.backward()
        opt.step()
        opt.zero_grad(set_to_none=True)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        rows.append({"tokens": len(ex["ids"]), "seconds": round(time.monotonic() - t, 3)})
    xs, ys = [r["tokens"] for r in rows[1:]] or [1], [r["seconds"] for r in rows[1:]] or [0]   # the first warms up
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    var = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / var if var else my / mx
    a = my - b * mx
    per_epoch = sum(a + b * len(e["ids"]) for e in train_set)
    res = {"version": version, "examples": rows, "seconds_per_token": b, "seconds_fixed": a,
           "peak_memory_gb": round(torch.cuda.max_memory_allocated() / 2 ** 30, 2) if torch.cuda.is_available() else None,
           "predicted_hours_2_epochs": round(2 * per_epoch / 3600, 2),
           "trainable_parameters": sum(p.numel() for p in trainable(lm).values())}
    Path(out).mkdir(parents=True, exist_ok=True)
    with open(Path(out) / "timing.jsonl", "a") as f:
        f.write(json.dumps(res) + "\n")
    del lm, opt
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return res


def export(version, model_path, out, device):
    """The chosen epoch as a PEFT adapter (LoRA versions) and tags.pt (tag versions), under out/final/."""
    import torch
    from finetune.source_tags import SourceTaggedLM
    chosen = choose(out)
    if chosen is None:
        sys.exit("no epoch with a validation loss yet")
    lm = build(version, model_path, device=device, checkpointing=False)
    load_weights(lm, Path(out) / f"epoch{chosen['epoch']}")
    final = Path(out) / "final"
    final.mkdir(parents=True, exist_ok=True)
    inner = lm.model if isinstance(lm, SourceTaggedLM) else lm
    if hasattr(inner, "save_pretrained") and hasattr(inner, "peft_config"):
        inner.save_pretrained(final / "adapter")
    if isinstance(lm, SourceTaggedLM):
        torch.save(lm.tags.weight.detach().cpu(), final / "tags.pt")
    (final / "chosen.json").write_text(json.dumps({**chosen, "version": version}, indent=1) + "\n")
    return final


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", required=True, help=f"one of {VERSIONS} (comma-separated with --timing)")
    ap.add_argument("--out", help="output directory (one per version)")
    ap.add_argument("--model", help="model directory (default: the cached allenai/Olmo-3-7B-Think snapshot)")
    ap.add_argument("--train", default=str(TRAIN))
    ap.add_argument("--validation", default=str(VALIDATION))
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timing", type=int, metavar="N", help="S1: time the N longest examples per version")
    ap.add_argument("--max-steps", type=int, help="stop (with a resume checkpoint) after this many optimizer steps")
    ap.add_argument("--export", action="store_true")
    a = ap.parse_args()
    versions = a.version.split(",")
    for v in versions:
        if v not in VERSIONS:
            sys.exit(f"unknown version {v!r}; one of {VERSIONS}")
    if os.environ.get("SLURM_JOB_ID") and a.train == str(TRAIN):         # on Sol: the Mac's bytes (kit manifest)
        from finetune.gpu import kit
        kit.check_inputs("train")
    raw_train, raw_val = load_examples(a.train), load_examples(a.validation)
    steps = math.ceil(len(raw_train) / ACCUM) * EPOCHS
    print(f"{len(raw_train)} training and {len(raw_val)} validation examples; {EPOCHS} epochs of "
          f"{math.ceil(len(raw_train) / ACCUM)} optimizer steps ({ACCUM} examples each): {steps} steps; "
          f"rank {RANK}, LoRA {LR_LORA}, tags {LR_TAGS}")
    if a.dry_run:
        return
    if not a.out:
        sys.exit("--out is required")
    model_path = a.model
    if model_path is None:
        from finetune.gpu import kit
        model_path = str(kit.snapshot()[0])
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_path)
    train_set = usable(encode(tok, x) for x in raw_train)
    val_set = usable(encode(tok, x) for x in raw_val)
    if a.timing:
        for v in versions:
            res = timing(v, model_path, train_set, a.timing, a.device, a.out)
            print(json.dumps({k: res[k] for k in res if k != "examples"}))
        return
    if len(versions) != 1:
        sys.exit("train or export one version at a time")
    if a.export:
        print(export(versions[0], model_path, a.out, a.device))
        return
    lm = build(versions[0], model_path, device=a.device)
    meta = {"version": versions[0], "model": model_path, "train": a.train, "train_examples": len(train_set)}
    pos = train(lm, train_set, val_set, a.out, a.device, max_steps=a.max_steps, meta=meta)
    print(json.dumps({"stopped_at": pos, "chosen": choose(a.out)}))
    if pos["epoch"] >= EPOCHS:                       # done: the chosen epoch, ready for evaluation (out/final/)
        import torch
        del lm
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print(export(versions[0], model_path, a.out, a.device))


if __name__ == "__main__":
    main()
