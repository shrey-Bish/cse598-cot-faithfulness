"""Track A, Step 12: generation for the evaluated systems, with the same continuation logic as every
other Track A run (finetune/continuation.py takes a complete_fn; this module makes them).

  server_complete(url, name)               a local vLLM server's /v1/completions (base, prompt-only,
                                           LoRA versions: the adapter is a served model name)
  server_complete(url, name, tagger)       the same, for a tag version: the prompt goes as
                                           prompt_embeds (each token's own embedding + its source tag)
                                           to a server whose embedding table has tag[model] folded in
                                           (fold_model), so every generated token is tagged "model"
  hf_complete(model, tokenizer, tagger)    the own decoding loop (the fallback if vLLM can't take
                                           prompt embeddings with LoRA): Hugging Face generate from
                                           inputs_embeds on the folded model, one sequence at a time
Each returns what client.complete returns: {content, finish, usage, error, ...}.

Source tags of a prompt: the rendered conversation's turns give the tags (source_tags.
source_ids_from_render); everything after the last "<|im_start|>assistant\\n<think>" is the model's
own text so far (a continuation) and is tagged "model". The two parts are tokenized apart, as at
training (finetune/train.py).

  python finetune/generate.py fold --model BASE --tags OUT/final/tags.pt --out FOLDED   # for vLLM
  python finetune/generate.py serve-cmd --model DIR [--lora name=PATH] [--prompt-embeds]  # the command
"""
import argparse
import base64
import io
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

from finetune import olmo_format  # noqa: E402

PORT = 8011
MAX_MODEL_LEN = olmo_format.CAP_TOTAL + 1024        # the 32,768 cap plus room for a tool round's prompt growth
GEN = olmo_format.GEN_PROMPT                        # "<|im_start|>assistant\n<think>"
EMBED_KEY = "model.embed_tokens.weight"


class Tagger:
    """Prompt embeddings with source tags: E[token] + tags[source]."""

    def __init__(self, tokenizer, embedding, tags):
        self.tokenizer, self.embedding, self.tags = tokenizer, embedding, tags      # tensors on the CPU

    @classmethod
    def load(cls, model_dir, tags_pt):
        import torch
        from transformers import AutoTokenizer
        return cls(AutoTokenizer.from_pretrained(model_dir), load_embedding(model_dir), torch.load(tags_pt, map_location="cpu"))

    def ids_and_sources(self, text):
        from finetune.source_tags import SOURCES, source_ids_from_render
        cut = text.rfind(GEN)
        if cut < 0:
            raise ValueError("a tagged prompt must contain the generation prompt")
        head, tail = text[:cut + len(GEN)], text[cut + len(GEN):]
        ids, src, _ = source_ids_from_render(self.tokenizer, head)
        t_ids = list(self.tokenizer(tail, add_special_tokens=False)["input_ids"]) if tail else []
        return ids + t_ids, src + [SOURCES["model"]] * len(t_ids)

    def embeds(self, text):
        import torch
        ids, src = self.ids_and_sources(text)
        e = self.embedding[torch.tensor(ids)].float() + self.tags[torch.tensor(src)].float()
        return e.to(self.embedding.dtype)


def load_embedding(model_dir):
    """The input embedding table from a model's safetensors shards (no model load)."""
    from safetensors import safe_open
    for shard in sorted(Path(model_dir).glob("*.safetensors")):
        with safe_open(str(shard), "pt") as f:
            if EMBED_KEY in f.keys():
                return f.get_tensor(EMBED_KEY)
    raise ValueError(f"{EMBED_KEY} not found in {model_dir}")


def encode_embeds(tensor):
    """vLLM's prompt_embeds field: a torch.save'd tensor, base64."""
    import torch
    buf = io.BytesIO()
    torch.save(tensor.contiguous(), buf)
    return base64.b64encode(buf.getvalue()).decode()


def fold_model(base_dir, tags_pt, out_dir):
    """A copy of the base model whose input embedding table is E + tag[model] (finetune/tags_vllm.py):
    only the shard holding the table is rewritten; every other file is linked. Olmo 3 7B's input and
    output embeddings are separate (tie_word_embeddings false), so the output layer is untouched."""
    import torch
    from safetensors import safe_open
    from safetensors.torch import save_file
    from finetune.source_tags import SOURCES
    base, out = Path(base_dir), Path(out_dir)
    cfg = json.loads((base / "config.json").read_text())
    if cfg.get("tie_word_embeddings"):
        raise ValueError("tied input and output embeddings: folding the model tag would change the output layer")
    tag = torch.load(tags_pt, map_location="cpu")[SOURCES["model"]]
    out.mkdir(parents=True, exist_ok=True)
    done = False
    for f in base.iterdir():
        dst = out / f.name
        if dst.exists() or dst.is_symlink():
            dst.unlink()
        if f.suffix == ".safetensors":
            with safe_open(str(f), "pt") as sf:
                if EMBED_KEY in sf.keys():
                    tensors = {k: sf.get_tensor(k) for k in sf.keys()}
                    meta = sf.metadata()
                    e = tensors[EMBED_KEY]
                    tensors[EMBED_KEY] = (e.float() + tag.float()).to(e.dtype)
                    save_file(tensors, str(dst), metadata=meta)
                    done = True
                    continue
        if f.is_dir():
            shutil.copytree(f, dst, symlinks=True)
        else:
            dst.symlink_to(f.resolve())
    if not done:
        raise ValueError(f"{EMBED_KEY} not found in {base}")
    (out / "folded_from.json").write_text(json.dumps({"base": str(base), "tags": str(tags_pt),
                                                      "tag_norm": float(tag.float().norm())}, indent=1) + "\n")
    return out


def serve_cmd(model_dir, port=PORT, lora=None, prompt_embeds=False, vllm="vllm", served_name="system"):
    """The vllm serve command for one evaluated system."""
    cmd = [vllm, "serve", str(model_dir), "--served-model-name", served_name, "--port", str(port),
           "--max-model-len", str(MAX_MODEL_LEN), "--dtype", "bfloat16", "--seed", "0", "--disable-log-requests"]
    if lora:
        cmd += ["--enable-lora", "--max-lora-rank", "16", "--lora-modules", *[f"{k}={v}" for k, v in lora.items()]]
    if prompt_embeds:
        cmd += ["--enable-prompt-embeds"]
    return cmd


def wait_ready(url, timeout=1800, proc=None):
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        if proc is not None and proc.poll() is not None:
            raise RuntimeError(f"the server exited with code {proc.returncode}")
        try:
            with urllib.request.urlopen(url.rstrip("/") + "/health", timeout=5) as r:
                if r.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(5)
    raise TimeoutError(f"no server at {url} after {timeout} s")


def server_complete(url, name, tagger=None, timeout=3600):
    """A complete_fn for continuation.continue_to_answer, against a local vLLM server."""
    endpoint = url.rstrip("/") + "/v1/completions"

    def complete(model, prompt, *, max_tokens, temperature=0.6, seed=None, backoff=None, extra=None):
        body = {"model": name, "max_tokens": max_tokens, "temperature": temperature, **(extra or {})}
        if seed is not None:
            body["seed"] = seed
        if tagger is None:
            body["prompt"] = prompt
        else:
            body["prompt_embeds"] = encode_embeds(tagger.embeds(prompt))
        start = time.monotonic()
        req = urllib.request.Request(endpoint, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                res = json.loads(r.read().decode())
        except urllib.error.HTTPError as err:
            return {"content": "", "finish": "error", "usage": {}, "error": f"HTTP {err.code}: {err.read()[:300]!r}",
                    "reasoning": "", "latency_s": round(time.monotonic() - start, 2)}
        except (urllib.error.URLError, OSError, TimeoutError) as err:
            return {"content": "", "finish": "error", "usage": {}, "error": f"connection: {err}", "reasoning": "",
                    "latency_s": round(time.monotonic() - start, 2)}
        choice = res["choices"][0]
        return {"content": choice.get("text") or "", "finish": choice.get("finish_reason"), "error": None,
                "usage": res.get("usage") or {}, "reasoning": "", "latency_s": round(time.monotonic() - start, 2),
                "served_model": name, "requested_model_id": name, "reasoning_effort": None}
    return complete


def hf_complete(model, tokenizer, tagger=None, device="cuda"):
    """The own decoding loop: one sequence at a time with Hugging Face generate. With a tagger, `model`
    must be the folded model (fold_model) and the prompt goes in as tagged embeddings."""
    import torch

    def complete(name, prompt, *, max_tokens, temperature=0.6, seed=None, backoff=None, extra=None):
        stops = (extra or {}).get("stop") or []
        start = time.monotonic()
        if seed is not None:
            torch.manual_seed(seed)
        kw = {"max_new_tokens": max_tokens, "do_sample": temperature > 0, "temperature": temperature or None,
              "pad_token_id": tokenizer.pad_token_id, "eos_token_id": tokenizer.eos_token_id}
        if stops:
            kw.update({"stop_strings": stops, "tokenizer": tokenizer})
        with torch.no_grad():
            if tagger is None:
                ids = tokenizer(prompt, add_special_tokens=False, return_tensors="pt")["input_ids"].to(device)
                out = model.generate(input_ids=ids, attention_mask=torch.ones_like(ids), **kw)[0, ids.shape[1]:]
                n_prompt = ids.shape[1]
            else:
                emb = tagger.embeds(prompt).to(device=device, dtype=model.dtype)[None]
                out = model.generate(inputs_embeds=emb, attention_mask=torch.ones(emb.shape[:2], dtype=torch.long, device=device),
                                     **kw)[0]
                n_prompt = emb.shape[1]
        toks = out.tolist()
        eos = toks and toks[-1] == tokenizer.eos_token_id
        text = tokenizer.decode(toks, skip_special_tokens=False)
        if eos:
            text = text[: -len(tokenizer.eos_token)] if text.endswith(tokenizer.eos_token) else text
        finish = "stop" if eos or any(text.endswith(s) for s in stops) else ("length" if len(toks) >= max_tokens else "stop")
        return {"content": text, "finish": finish, "error": None, "reasoning": "",
                "usage": {"prompt_tokens": n_prompt, "completion_tokens": len(toks)},
                "latency_s": round(time.monotonic() - start, 2), "served_model": name, "requested_model_id": name,
                "reasoning_effort": None}
    return complete


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fold")
    f.add_argument("--model", required=True)
    f.add_argument("--tags", required=True)
    f.add_argument("--out", required=True)
    s = sub.add_parser("serve-cmd")
    s.add_argument("--model", required=True)
    s.add_argument("--lora", action="append", default=[], help="name=PATH")
    s.add_argument("--prompt-embeds", action="store_true")
    s.add_argument("--port", type=int, default=PORT)
    a = ap.parse_args()
    if a.cmd == "fold":
        print(fold_model(a.model, a.tags, a.out))
    else:
        print(" ".join(serve_cmd(a.model, a.port, dict(x.split("=", 1) for x in a.lora) or None, a.prompt_embeds)))


if __name__ == "__main__":
    main()
