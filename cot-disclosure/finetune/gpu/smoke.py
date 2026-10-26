"""Sol kit, item 1: does this environment load Olmo 3 7B Think and generate in our format?

Loads allenai/Olmo-3-7B-Think from the local Hugging Face cache in bf16 on the GPU and generates
32 tokens (greedy) from a short question in the pinned Think format (finetune/olmo_format.py:
the prompt ends "<|im_start|>assistant\\n<think>"). Prints the GPU, the library versions, the
snapshot's commit hash (and whether it, or at least its weights, is d97e442, the revision our
template came from), whether the snapshot's own chat template renders the same prompt as ours,
and the config fields the look-inside steps depend on.

  python finetune/gpu/smoke.py --versions      # library versions, torch's CUDA build, the GPU; no model
  python finetune/gpu/smoke.py --dry-run       # snapshot, config fields, memory check; no model loaded
  python finetune/gpu/smoke.py                 # load + generate -> $TRACKA_OUT/smoke/smoke.json
On Sol, run it through finetune/gpu/sol/run.sh smoke (environment and account checks first).
"""
import argparse
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))

from experiments import STEPS  # noqa: E402
from finetune import olmo_format  # noqa: E402
from finetune.gpu import kit  # noqa: E402

QUESTION = "What is 17 + 25?\n(A) 32\n(B) 42\n(C) 52\n(D) 41"
MESSAGES = [{"role": "user", "content": QUESTION + "\n\n" + STEPS}]
NEW_TOKENS = 32
HEADROOM = 2 * kit.GiB                       # activations and the CUDA context for a short prompt


def show_versions():
    v, g = kit.versions(), kit.gpu_info()
    print("versions: " + ", ".join(f"{k} {x}" for k, x in v.items()))
    print(f"GPU: {g}" if g else "GPU: none visible (fine for setup; smoke.py needs one)")
    return v, g


def run(model=None, device="auto", dtype="bf16", new_tokens=NEW_TOKENS, out=None, dry_run=False):
    from transformers import AutoConfig
    path, commit = kit.snapshot(model)
    snap = kit.describe_snapshot(path, commit)
    cfg = kit.config_fields(AutoConfig.from_pretrained(path, local_files_only=True))
    dev = kit.pick_device(device)
    need = kit.model_bytes(path, dtype) + HEADROOM
    print(kit.snapshot_line(snap))
    print("config: " + json.dumps(cfg))
    tok = kit.load_tokenizer(path)
    ours = olmo_format.render(MESSAGES)
    theirs = tok.apply_chat_template(MESSAGES, tokenize=False, add_generation_prompt=True)
    print(f"the snapshot's chat template renders our prompt {'exactly' if theirs == ours else 'DIFFERENTLY'}")
    if dry_run:
        need, have = kit.check_memory(dev, need, f"Olmo 3 7B Think in {dtype}")
        print(f"memory: needs ~{need / kit.GiB:.1f} GiB, {have / kit.GiB:.1f} GiB free on {dev}: ok")
        return None
    kit.check_memory(dev, need, f"Olmo 3 7B Think in {dtype}")
    import torch
    t = kit.Timer()
    m = kit.load_model(path, dtype, dev)
    load_s = t()
    ids = tok(ours, add_special_tokens=False, return_tensors="pt")["input_ids"].to(dev)
    t = kit.Timer()
    with torch.no_grad():
        gen = m.generate(ids, attention_mask=torch.ones_like(ids), max_new_tokens=new_tokens, do_sample=False)
    gen_s = t()
    new = gen[0, ids.shape[1]:]
    text = tok.decode(new, skip_special_tokens=False)
    res = {**kit.header("smoke", snap), "config": cfg, "dtype": dtype, "device": str(dev),
           "template_renders_same": theirs == ours, "pinned_template_sha256": olmo_format.PINNED_SHA256,
           "prompt": ours, "prompt_tokens": ids.shape[1], "generated_tokens": int(new.shape[0]), "generated": text,
           "greedy": True, "load_s": load_s, "generate_s": gen_s,
           "tokens_per_s": round(int(new.shape[0]) / gen_s, 1) if gen_s else None,
           "peak_gib": round(torch.cuda.max_memory_allocated() / kit.GiB, 2) if dev.type == "cuda" else None}
    path_out = kit.write_json(kit.out_dir("smoke", out) / "smoke.json", res)
    print(f"GPU: {res['gpu']}")
    print("versions: " + ", ".join(f"{k} {x}" for k, x in res["versions"].items()))
    print(f"loaded in {load_s:.0f} s; {res['prompt_tokens']} prompt tokens; {res['generated_tokens']} new tokens in "
          f"{gen_s:.1f} s; peak {res['peak_gib']} GiB")
    print(f"generated: {text!r}")
    print(f"saved {path_out}")
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--versions", action="store_true", help="print versions and the GPU, then stop")
    ap.add_argument("--dry-run", action="store_true", help="snapshot, config and memory check; load nothing")
    ap.add_argument("--model", help="a local model directory instead of the cached Olmo 3 7B Think (tests)")
    ap.add_argument("--device", default="auto", help="auto (cuda, else mps, else cpu), or a torch device")
    ap.add_argument("--dtype", default="bf16", choices=sorted(kit.DTYPES))
    ap.add_argument("--new-tokens", type=int, default=NEW_TOKENS)
    ap.add_argument("--out", help="output base directory (default $TRACKA_OUT)")
    a = ap.parse_args(argv)
    if a.versions:
        return show_versions()
    return run(a.model, a.device, a.dtype, a.new_tokens, a.out, a.dry_run)


if __name__ == "__main__":
    main()
