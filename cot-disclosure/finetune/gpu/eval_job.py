"""Track A on Sol: one evaluation job (Step 13, jobs E1-E6) or the vLLM tag check (Step 12, job S2).

A job prepares the system's model, starts a vLLM server on it (its own environment,
$TRACKA_VLLM = /scratch/ragarw68/envs/olmo-vllm/bin/vllm, since vLLM pins its own torch), runs
finetune/eval.py's runs against it, and stops it. Models (under $TRACKA_OUT/models/, made once):
  base, prompt_only   the cached Olmo 3 7B Think snapshot
  lora, lora_attn3    the base with the chosen epoch's LoRA merged in (merge_and_unload)
  tags                the base with tag[model] folded into the input embedding table (generate.fold_model)
  lora_tags           LoRA merged, then the tag folded
Tag versions get tagged prompt embeddings (--enable-prompt-embeds). Merging first means no system
needs vLLM's prompt embeddings together with LoRA.

  python finetune/gpu/eval_job.py --system base --part 1/2 --out /scratch/ragarw68/trackA/eval
  python finetune/gpu/eval_job.py --check --out /scratch/ragarw68/trackA/vllm_check     # S2

The check (S2): a synthetic tag table and LoRA adapter (seeded), the served versions against the
Hugging Face reference on 3 held-out prompts, greedy, 48 tokens: base served vs HF base (the bf16
noise floor), merged LoRA + folded tag + tagged prompt embeddings served vs SourceTaggedLM(LoRA) in HF.
It passes when the tagged version agrees with its reference as far as the plain base does
(vllm_check.json, numbers only). The plain base server runs first, before the synthetic LoRA merge
and the shard writing, so a server that can't start fails the job in minutes.

Every job first checks its server commands against the installed vLLM's option list, which
setup_vllm.sh saved on the CPU (finetune/gpu/vllm_options.py): an option the version doesn't take
stops the job before any GPU work.
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from finetune import generate as gen  # noqa: E402
from finetune.gpu import kit  # noqa: E402

TAGGED = ("tags", "lora_tags")
LORA = ("lora", "lora_attn3", "lora_tags")
CHECK_TOKENS = 48


def out_root():
    return Path(os.environ.get("TRACKA_OUT", "/scratch/ragarw68/trackA"))


def merge_lora(base_dir, adapter_dir, out_dir):
    """The base with a LoRA adapter merged in, saved in bf16 (with the base's tokenizer files)."""
    import shutil

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM
    out = Path(out_dir)
    if (out / "config.json").exists():
        return out
    model = AutoModelForCausalLM.from_pretrained(base_dir, dtype=torch.bfloat16)
    model = PeftModel.from_pretrained(model, str(adapter_dir)).merge_and_unload()
    tmp = out.with_name(out.name + ".tmp")
    model.save_pretrained(tmp)
    for f in Path(base_dir).iterdir():
        if f.is_file() and (f.name.startswith("tokenizer") or f.name in ("special_tokens_map.json", "chat_template.jinja",
                                                                          "generation_config.json")):
            shutil.copy(f, tmp / f.name)
    tmp.rename(out)
    return out


def prepare(system, base_dir, train_root, models_root):
    """(model directory to serve, tags.pt or None) for one system."""
    if system in ("base", "prompt_only"):
        return Path(base_dir), None
    final = Path(train_root) / system / "final"
    if not (final / "chosen.json").exists():
        raise FileNotFoundError(f"{final}/chosen.json: train and export {system} first (finetune/train.py --export)")
    model = Path(base_dir)
    if system in LORA:
        model = merge_lora(model, final / "adapter", Path(models_root) / f"{system}_merged")
    tags = final / "tags.pt" if system in TAGGED else None
    if tags:
        model = gen.fold_model(model, tags, Path(models_root) / f"{system}_folded")
    return model, tags


_SERVERS = []


def _stop_now(*_):
    """Slurm's warning before the time limit: stop the server and exit; every finished run is already
    saved, and the next job resumes the rest."""
    for s in _SERVERS:
        if s.proc.poll() is None:
            s.proc.terminate()
    os._exit(0)


class Server:
    """vllm serve as a child process; stopped on exit (and on SIGUSR1 from Slurm, _stop_now)."""

    def __init__(self, model_dir, prompt_embeds, port=gen.PORT, log=None, lora=None):
        self.cmd = self.command(model_dir, prompt_embeds, port, lora)
        self.url, self.log = f"http://localhost:{port}", log

    @staticmethod
    def command(model_dir, prompt_embeds, port=gen.PORT, lora=None):
        return gen.serve_cmd(model_dir, port, lora=lora, prompt_embeds=prompt_embeds,
                             vllm=os.environ.get("TRACKA_VLLM", "vllm"))

    def __enter__(self):
        out = open(self.log, "a") if self.log else subprocess.DEVNULL
        print(f"{kit.now()} starting: {' '.join(self.cmd)}", flush=True)
        self.proc = subprocess.Popen(self.cmd, stdout=out, stderr=subprocess.STDOUT)
        _SERVERS.append(self)
        try:
            gen.wait_ready(self.url, proc=self.proc, log=self.log)
        except BaseException:
            self.__exit__()
            raise
        print(f"{kit.now()} server ready", flush=True)
        return self

    def __exit__(self, *exc):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(60)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        return False


def server_commands():
    """Every vllm serve command a job starts (label -> argv): each evaluated system's and the check's two."""
    from finetune.eval import SYSTEMS
    cmds = {f"eval {s}": Server.command(f"MODEL_{s}", prompt_embeds=s in TAGGED) for s in SYSTEMS}
    cmds["vllm_check plain"] = Server.command("BASE", prompt_embeds=False)
    cmds["vllm_check tagged"] = Server.command("FOLDED", prompt_embeds=True)
    return cmds


def preflight():
    """Before any GPU work: every server command uses only options the installed vLLM lists (setup_vllm.sh
    saved its list, from `vllm serve --help=all`, in $TRACKA_OUT)."""
    from finetune.gpu import vllm_options
    saved = out_root() / "vllm_serve_options.txt"
    if not saved.exists():
        sys.exit(f"no vLLM option list at {saved}: run setup_vllm first (submit.sh setup_vllm), which saves it")
    version, opts = vllm_options.load(saved)
    bad = vllm_options.problems(server_commands(), opts)
    if bad:
        sys.exit(f"refusing: vLLM {version} ({saved}) doesn't list these server options:\n  " + "\n  ".join(bad))
    print(f"{kit.now()} server options: all in vLLM {version}'s list", flush=True)


def evaluate(system, part, out, workers):
    from finetune import eval as ev
    base = kit.snapshot()[0]
    model, tags = prepare(system, base, out_root() / "train", out_root() / "models")
    tagger = gen.Tagger.load(base, tags) if tags else None
    Path(out).mkdir(parents=True, exist_ok=True)
    started = kit.now()
    with Server(model, prompt_embeds=tags is not None, log=Path(out) / f"vllm_{system}.log") as srv:
        ev.run(system, gen.server_complete(srv.url, "system", tagger), out, part, workers)
    with open(Path(out) / "eval_jobs.jsonl", "a") as f:       # which job ran what, in which environments
        f.write(json.dumps({"system": system, "part": part, "model_dir": str(model), "tags": str(tags) if tags else None,
                            "started_utc": started, "ended_utc": kit.now(), "slurm": kit.slurm(),
                            "environments": kit.environments(server=True)}) + "\n")


# ---------------------------------------------------------------- S2: the vLLM tag check
def synthetic_parts(base_dir, root, seed=0):
    """A seeded tag table (each row ~ the embedding rows' scale) and LoRA adapter (B not zero), for the check."""
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM
    root = Path(root)
    tags_pt, adapter = root / "tags.pt", root / "adapter"
    if tags_pt.exists() and (adapter / "adapter_config.json").exists():
        return tags_pt, adapter
    g = torch.Generator().manual_seed(seed)
    emb = gen.load_embedding(base_dir)
    torch.save(torch.randn(4, emb.shape[1], generator=g) * emb.float().std() * 0.5, tags_pt)
    model = AutoModelForCausalLM.from_pretrained(base_dir, dtype=torch.bfloat16)
    from finetune.train import ALPHA, DROPOUT, LORA_ALL, RANK
    lm = get_peft_model(model, LoraConfig(r=RANK, lora_alpha=ALPHA, lora_dropout=DROPOUT, target_modules=LORA_ALL,
                                          task_type="CAUSAL_LM"))
    with torch.no_grad():
        for n, p in lm.named_parameters():
            if "lora_B" in n:
                p.copy_(torch.randn(p.shape, generator=g) * 0.01)
    lm.save_pretrained(adapter)
    return tags_pt, adapter


def check_prompts():
    from finetune import eval as ev
    from finetune import olmo_format
    js = ev.jobs()
    picks = [next(j for j in js if j["channel"] == c and j["hint_correct"] is False) for c in ("user", "tool_pasted", "tool_injected")]
    return [olmo_format.render(j["messages"], tools=j["tools"]) for j in picks]


def hf_greedy(model_dir, prompts, adapter=None, tags_pt=None, device="cuda"):
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from finetune import tags_vllm
    from finetune.source_tags import SourceTaggedLM
    tok = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=torch.bfloat16).to(device).eval()
    if adapter:
        model = PeftModel.from_pretrained(model, str(adapter)).merge_and_unload()
    out = []
    if tags_pt:
        lm = SourceTaggedLM(model)
        lm.tags.weight.data.copy_(torch.load(tags_pt).to(lm.tags.weight.dtype))
        lm.to(device)
        t = gen.Tagger(tok, gen.load_embedding(model_dir), torch.load(tags_pt))
        for p in prompts:
            ids, src = t.ids_and_sources(p)
            out.append(tags_vllm.tagged_greedy(lm, torch.tensor([ids], device=device), torch.tensor([src], device=device),
                                               CHECK_TOKENS)[0].tolist())
    else:
        for p in prompts:
            ids = tok(p, add_special_tokens=False, return_tensors="pt")["input_ids"].to(device)
            with torch.no_grad():
                out.append(model.generate(input_ids=ids, max_new_tokens=CHECK_TOKENS, do_sample=False)[0, ids.shape[1]:].tolist())
    del model
    torch.cuda.empty_cache()
    return out


def served_tokens(url, prompts, tagger=None):
    """Greedy tokens from the server, as token ids (logprobs give the ids' strings; re-tokenized here)."""
    complete = gen.server_complete(url, "system", tagger)
    return [complete("system", p, max_tokens=CHECK_TOKENS, temperature=0.0, seed=0)["content"] for p in prompts]


def agreement(a, b):
    """Tokens equal from the start (the first divergence)."""
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def check(out):
    from transformers import AutoTokenizer
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    base = kit.snapshot()[0]
    prompts = check_prompts()
    with Server(base, prompt_embeds=False, log=out / "vllm_base.log") as srv:   # first: a server that can't start
        got_plain = served_tokens(srv.url, prompts)                               # fails in minutes, before any merge
    tok = AutoTokenizer.from_pretrained(base)
    tags_pt, adapter = synthetic_parts(base, out)
    tagged_dir = gen.fold_model(merge_lora(base, adapter, out / "merged"), tags_pt, out / "folded")
    ref_plain = hf_greedy(base, prompts)
    ref_tagged = hf_greedy(base, prompts, adapter=adapter, tags_pt=tags_pt)
    tagger = gen.Tagger(tok, gen.load_embedding(base), __import__("torch").load(tags_pt))
    with Server(tagged_dir, prompt_embeds=True, log=out / "vllm_tagged.log") as srv:
        got_tagged = served_tokens(srv.url, prompts, tagger)
    ids = lambda texts: [tok(t, add_special_tokens=False)["input_ids"] for t in texts]  # noqa: E731
    plain = [agreement(a, b) for a, b in zip(ids(got_plain), ref_plain)]
    tagged = [agreement(a, b) for a, b in zip(ids(got_tagged), ref_tagged)]
    res = {"tokens": CHECK_TOKENS, "prompts": len(prompts), "plain_agreement": plain, "tagged_agreement": tagged,
           "tagged_differs_from_plain_output": [a != b for a, b in zip(got_tagged, got_plain)],
           "pass": sum(tagged) >= sum(plain) - CHECK_TOKENS // 4 and min(tagged) > 0,
           "rule": "the tagged version agrees with its HF reference about as far as the plain base does "
                   "(summed agreement within a quarter of the tokens) and on every prompt from the first token",
           "slurm": kit.slurm(), "environments": kit.environments(server=True)}
    (out / "vllm_check.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--system")
    ap.add_argument("--part")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=48)
    ap.add_argument("--check", action="store_true", help="S2: the vLLM tag check")
    a = ap.parse_args()
    signal.signal(signal.SIGUSR1, _stop_now)
    if os.environ.get("SLURM_JOB_ID"):                       # on Sol: the Mac's bytes (kit manifest), and
        kit.check_inputs("eval")                             # the server options before any GPU work
        preflight()
    if a.check:
        check(a.out)
        return
    part = tuple(int(x) for x in a.part.split("/")) if a.part else None
    evaluate(a.system, part, a.out, a.workers)


if __name__ == "__main__":
    main()
