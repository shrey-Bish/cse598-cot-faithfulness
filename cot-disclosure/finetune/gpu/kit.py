"""Track A GPU kit: what every GPU script shares (Steps 8-10 on ASU Sol; small jobs anywhere).

- Outputs: --out BASE, else $TRACKA_OUT (finetune/gpu/sol/env.sh sets /scratch/ragarw68/trackA);
  each step writes to BASE/<step>/. A small summary file per step is copied back to the Mac and
  committed in results/trackA/gpu/.
- The model: allenai/Olmo-3-7B-Think from the local Hugging Face cache, never downloaded at run
  time. Every output records the snapshot's commit hash and whether its files equal d97e442, the
  revision our pinned template came from. olmo3_7b_think_d97e442.json holds the hash of every
  file at d97e442; the cache names each file's blob by that same hash, so the check needs no
  network and no re-hashing. (The weights are the same in 24 of the repo's 25 revisions.)
- A memory check that refuses to start when the device can't hold the job.
- The inputs each step reads, with their sha256 (inputs_manifest.json), checked before a run.

  python finetune/gpu/kit.py --manifest        # on the Mac: write inputs_manifest.json (+ sol/inputs.txt for rsync)
  python finetune/gpu/kit.py --check-inputs    # on Sol: are the inputs the same bytes as on the Mac?
"""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

MODEL_ID = "allenai/Olmo-3-7B-Think"
TEMPLATE_REV = "d97e442d7cc678210054dbcc9b440894d62c89a4"      # finetune/templates/olmo3_think_tools.jinja's Think part
REV_FILES = Path(__file__).with_name("olmo3_7b_think_d97e442.json")
INPUTS = Path(__file__).with_name("inputs_manifest.json")
INPUTS_LIST = Path(__file__).parent / "sol" / "inputs.txt"     # the same paths, one per line, for rsync --files-from
SUMMARIES = CODE / "results" / "trackA" / "gpu"                # the copied-back summaries, committed
GiB = 2 ** 30
DTYPES = {"bf16": "bfloat16", "fp16": "float16", "fp32": "float32"}
NEEDED = {                                                     # result files each step reads (relative to cot-disclosure/)
    "step8": ["results/trackA/voyager_capabilities.jsonl.gz", "results/trackA/voyager_ids_check.jsonl.gz",
              "configs/canary/olmo3-7b-think.json"],
    "step9": ["results/trackA/base_format.jsonl.gz", "results/trackA/takeover_runs.jsonl",
              "results/progress/expB_cued.jsonl", "data/progress/mmlupro_30.jsonl"],
    "step10": ["results/trackA/base_format.jsonl.gz", "results/trackA/takeover_cases.jsonl",
               "results/trackA/deletion_runs.jsonl", "results/progress/expB_cued.jsonl",
               "data/progress/mmlupro_30.jsonl"],
}


# ---------------------------------------------------------------- outputs
def out_dir(step, out=None):
    """BASE/<step>, created. BASE is --out, else $TRACKA_OUT."""
    base = out or os.environ.get("TRACKA_OUT")
    if not base:
        raise SystemExit("no output directory: pass --out DIR or set TRACKA_OUT (finetune/gpu/sol/env.sh sets it)")
    d = Path(base) / step
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_json(path, obj):
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, default=str) + "\n")
    tmp.replace(path)                                          # never a half-written file after a time limit
    return path


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- the model
def snapshot(model=None):
    """(local model directory, its commit hash). model=None: Olmo 3 7B Think from the Hugging Face
    cache (the snapshot "main" points to; no network). A plain directory (a test's tiny model)
    has no commit: "local:<name>"."""
    if model and Path(model).is_dir():
        p = Path(model).resolve()
        return p, (p.name if p.parent.name == "snapshots" else f"local:{p.name}")
    from huggingface_hub import snapshot_download
    p = Path(snapshot_download(model or MODEL_ID, local_files_only=True))
    return p, p.name


def files_vs_template_rev(path):
    """Each file of the local snapshot against d97e442's: the cache keeps a file as a link to
    blobs/<hash>, the hash olmo3_7b_think_d97e442.json lists. same = every listed file present
    and equal; weights_same = the .safetensors files alone."""
    ref = json.loads(REV_FILES.read_text())
    differ, missing, unknown = [], [], []
    for name, h in ref["files"].items():
        f = Path(path) / name
        if not f.exists():
            missing.append(name)
            continue
        target = Path(os.path.realpath(f))
        if target.parent.name != "blobs":
            unknown.append(name)                               # not a cache link: would need hashing
        elif target.name != h:
            differ.append(name)
    weights = [n for n in ref["files"] if n.endswith(".safetensors")]
    bad = set(differ) | set(missing) | set(unknown)
    return {"same": not bad, "weights_same": not (set(weights) & bad), "differ": differ, "missing": missing,
            "not_a_cache_link": unknown, "checked": len(ref["files"]), "reference_revision": ref["revision"],
            "revisions_with_the_same_weights": len(ref["revisions_with_these_weights"])}


def describe_snapshot(path, commit):
    rev = files_vs_template_rev(path)
    return {"model": MODEL_ID, "snapshot_dir": str(path), "snapshot_commit": commit,
            "snapshot_is_d97e442": commit == TEMPLATE_REV, "files_vs_d97e442": rev}


def snapshot_line(s):
    """One line for the console: the hash, and whether it (or at least its weights) is d97e442's."""
    r = s["files_vs_d97e442"]
    if s["snapshot_is_d97e442"]:
        verdict = "matches d97e442 (the template's revision)"
    else:
        verdict = (f"is NOT d97e442; its files {'all equal' if r['same'] else 'differ from'} d97e442's"
                   + ("" if r["same"] else f" (weights {'equal' if r['weights_same'] else 'DIFFER'}; differ: "
                      f"{r['differ']}, missing: {r['missing']}, unverified: {r['not_a_cache_link']})"))
    return f"snapshot {s['snapshot_commit']} {verdict}"


def config_fields(cfg):
    """The config fields the look-inside steps depend on."""
    kinds = list(getattr(cfg, "layer_types", None) or ["full_attention"] * cfg.num_hidden_layers)
    return {"num_hidden_layers": cfg.num_hidden_layers, "num_attention_heads": cfg.num_attention_heads,
            "num_key_value_heads": getattr(cfg, "num_key_value_heads", cfg.num_attention_heads),
            "head_dim": getattr(cfg, "head_dim", None) or cfg.hidden_size // cfg.num_attention_heads,
            "hidden_size": cfg.hidden_size, "intermediate_size": getattr(cfg, "intermediate_size", None),
            "vocab_size": cfg.vocab_size, "max_position_embeddings": cfg.max_position_embeddings,
            "sliding_window": getattr(cfg, "sliding_window", None),
            "layer_types": {k: kinds.count(k) for k in sorted(set(kinds))},
            "full_attention_layers": [i for i, k in enumerate(kinds) if k == "full_attention"],
            "rope": getattr(cfg, "rope_parameters", None) or getattr(cfg, "rope_scaling", None),
            "rope_theta": getattr(cfg, "rope_theta", None),
            "tie_word_embeddings": getattr(cfg, "tie_word_embeddings", None),
            "dtype": str(getattr(cfg, "dtype", None) or getattr(cfg, "torch_dtype", None))}


def n_params(path):
    """Parameters of a decoder-only model from its config (for a memory estimate without the weights)."""
    c = json.loads((Path(path) / "config.json").read_text())
    d, inter, layers, v = c["hidden_size"], c["intermediate_size"], c["num_hidden_layers"], c["vocab_size"]
    hd = c.get("head_dim") or d // c["num_attention_heads"]
    attn = d * hd * (2 * c["num_attention_heads"] + 2 * c.get("num_key_value_heads", c["num_attention_heads"]))
    return v * d * (1 if c.get("tie_word_embeddings") else 2) + layers * (attn + 3 * d * inter)


def weight_bytes(path):
    """Bytes of the stored weights (bf16 for Olmo 3), from the safetensors index or the files; from
    the config (2 bytes per parameter) when the weights aren't in this cache (the Mac)."""
    index = Path(path) / "model.safetensors.index.json"
    if index.exists():
        total = json.loads(index.read_text()).get("metadata", {}).get("total_size")
        if total:
            return int(total)
    return sum(f.stat().st_size for f in Path(path).glob("*.safetensors")) or 2 * n_params(path)


def model_bytes(path, dtype):
    """Weights in memory at `dtype` (stored as bf16: fp32 doubles them)."""
    return weight_bytes(path) * (2 if dtype == "fp32" else 1)


def torch_dtype(name):
    import torch
    return getattr(torch, DTYPES[name])


def pick_device(name="auto"):
    import torch
    if name != "auto":
        return torch.device(name)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def free_bytes(device):
    """Memory the job may still use on this device."""
    import torch
    if device.type == "cuda":
        return torch.cuda.mem_get_info(device)[0]
    if device.type == "mps":
        return torch.mps.recommended_max_memory() - torch.mps.driver_allocated_memory()
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_AVPHYS_PAGES")
    except (ValueError, OSError, AttributeError):              # macOS: no free-page count; use half the RAM
        out = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True)
        return int(out.stdout.strip() or 0) // 2


def check_memory(device, need, what):
    """Refuse to start (SystemExit) unless the device has `need` bytes free. Returns (need, free)."""
    have = free_bytes(device)
    if need > have:
        raise SystemExit(f"refusing to start: {what} needs about {need / GiB:.1f} GiB on {device}, "
                         f"{have / GiB:.1f} GiB is free. Run it on the GPU (finetune/gpu/README.md).")
    return need, have


def load_model(path, dtype="bf16", device="cuda", attn="sdpa"):
    """The model from a local directory (offline), in eval mode, on one device."""
    from transformers import AutoModelForCausalLM
    model = AutoModelForCausalLM.from_pretrained(path, dtype=torch_dtype(dtype), attn_implementation=attn,
                                                 device_map={"": str(device)}, local_files_only=True)
    return model.eval()


def load_tokenizer(path):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(path, local_files_only=True)


# ---------------------------------------------------------------- what every output records
def versions():
    import importlib
    out = {"python": platform.python_version()}
    for m in ("torch", "transformers", "tokenizers", "huggingface_hub", "accelerate", "peft", "safetensors", "numpy"):
        try:
            out[m] = importlib.import_module(m).__version__
        except Exception as err:                               # noqa: BLE001  (a missing package is a finding)
            out[m] = f"missing ({type(err).__name__})"
    try:
        import torch
        out["torch_cuda_build"] = torch.version.cuda
    except Exception:                                          # noqa: BLE001
        pass
    return out


def gpu_info():
    import torch
    if not torch.cuda.is_available():
        return None
    p = torch.cuda.get_device_properties(0)
    info = {"name": p.name, "memory_gib": round(p.total_memory / GiB, 1), "capability": f"{p.major}.{p.minor}",
            "count": torch.cuda.device_count(), "bf16": torch.cuda.is_bf16_supported()}
    try:                                                       # the driver and the CUDA version it reports
        smi = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=20).stdout
        for key, field in (("Driver Version:", "driver"), ("CUDA Version:", "driver_cuda")):
            if key in smi:
                info[field] = smi.split(key, 1)[1].split()[0]
    except (OSError, subprocess.SubprocessError):
        pass
    return info


def code_commit():
    try:
        rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=CODE, capture_output=True, text=True, timeout=10)
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "finetune"], cwd=CODE, capture_output=True,
                               text=True, timeout=10)
        return {"commit": rev.stdout.strip() or None, "finetune_dirty": bool(dirty.stdout.strip())}
    except (OSError, subprocess.SubprocessError):
        return None


def slurm():
    keys = ("SLURM_JOB_ID", "SLURM_JOB_ACCOUNT", "SLURM_JOB_PARTITION", "SLURM_JOB_QOS", "SLURMD_NODENAME")
    return {k: os.environ[k] for k in keys if k in os.environ} or None


def header(step, snap):
    """The fields every output of a GPU step starts with."""
    return {"step": step, "timestamp_utc": now(), **snap, "versions": versions(), "gpu": gpu_info(),
            "code": code_commit(), "slurm": slurm(), "host": platform.node()}


class Timer:
    def __init__(self):
        self.t = time.monotonic()

    def __call__(self):
        return round(time.monotonic() - self.t, 2)


# ---------------------------------------------------------------- inputs
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_manifest():
    """inputs_manifest.json from the files on the Mac (refuses a tracked file with uncommitted changes;
    produced data is gitignored from Oct 26, so most inputs go to Sol by rsync, not git)."""
    out = {}
    for step, files in NEEDED.items():
        dirty = subprocess.run(["git", "status", "--porcelain", "--", *files], cwd=CODE, capture_output=True,
                               text=True).stdout.strip()
        if dirty:
            raise SystemExit(f"uncommitted changes in inputs of {step}:\n{dirty}")
        out[step] = [{"path": f, "bytes": (CODE / f).stat().st_size, "sha256": sha256(CODE / f)} for f in files]
    write_json(INPUTS, out)
    INPUTS_LIST.write_text("".join(f"{f}\n" for f in sorted({r["path"] for rows in out.values() for r in rows})))
    for step, rows in out.items():
        print(f"{step}: " + ", ".join(f"{r['path']} ({r['bytes'] / 2 ** 20:.2f} MB)" for r in rows))
    print(f"wrote {INPUTS.relative_to(CODE)}")


def check_inputs(step):
    """SystemExit unless every input of `step` is present with the manifest's sha256."""
    bad = []
    for r in json.loads(INPUTS.read_text())[step]:
        p = CODE / r["path"]
        if not p.exists():
            bad.append(f"missing {r['path']}")
        elif p.stat().st_size != r["bytes"] or sha256(p) != r["sha256"]:
            bad.append(f"different bytes: {r['path']}")
    if bad:
        raise SystemExit(f"{step} inputs are not the Mac's (finetune/gpu/inputs_manifest.json): " + "; ".join(bad)
                         + ". Copy them as finetune/gpu/README.md says.")
    return [r["path"] for r in json.loads(INPUTS.read_text())[step]]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", action="store_true", help="write inputs_manifest.json (Mac)")
    ap.add_argument("--check-inputs", action="store_true", help="check every step's inputs (Sol)")
    ap.add_argument("--dry-run", action="store_true", help="list each step's inputs; check nothing")
    a = ap.parse_args()
    if a.manifest:
        return write_manifest()
    if a.check_inputs:
        for step in NEEDED:
            check_inputs(step)
            print(f"{step}: inputs match the manifest")
        return
    for step, files in NEEDED.items():
        print(f"{step}: {', '.join(files)}")


if __name__ == "__main__":
    main()
