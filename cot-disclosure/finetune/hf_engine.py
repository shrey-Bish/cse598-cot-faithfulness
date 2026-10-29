"""Tracks A and B on Sol: Hugging Face generation for many runs at once, with a key/value cache (no vLLM).

make(model, tok, ...) returns a complete_fn (finetune/continuation.py's interface) that many threads call
at once, one call per round of a run:
  continuous  transformers' continuous batching (a paged key/value cache; a request joins the batch as
              soon as another one leaves). The default, after a self-check on the GPU: its greedy tokens
              on two short prompts against plain generate's.
  static      the fallback when the self-check fails or errors: requests that arrive together go
              through one generate with a key/value cache (finetune/gpu/provenance_job.Batched).
The engine object says which one ran (.kind); every record of the job carries it.

Sampling: the caller's temperature (0.6 in every planned run). top_p, top_k, min_p and
repetition_penalty only if the snapshot's generation_config.json sets them, which is what the planned
vLLM server would have applied; Hugging Face's own default top_k=50 is never used. A reply ends at the
tokenizer's end-of-text, generation_config.json's end ids, or <|im_end|>. Stop strings (the inserted tool
turn's "</function_calls>") end a reply as vLLM's stop does: the text up to and including the string, and
the request is cancelled there. Special tokens are left out of the text, as vLLM does. Per-run seeds can't
be kept inside a batch: one generator per job, seeded from the job, so runs are samples, not replays.

Tag versions (tags, lora_tags): TagTable widens the input embedding table to one block of rows per source,
row(token, source) = E[token] + tag[source] (SourceTaggedLM.embed's sum, in the model's dtype), the model's
own block first, so generated tokens get tag[model]. A prompt's tokens are moved to their source's block:
the input vectors SourceTaggedLM gave in training, as plain token ids, so both engines take them.
"""
import json
import threading
import time
from contextlib import contextmanager
from pathlib import Path

EXTRA_END = ("<|im_end|>",)
FROM_GENERATION_CONFIG = ("top_p", "top_k", "min_p", "repetition_penalty")
STOP_WINDOW = 24                  # tokens decoded around each new token when looking for a stop string
CHECK_TOKENS = 16                 # the self-check: greedy tokens per prompt
CHECK_AGREE = 8                   # ... that must match plain generate's from the first (bf16 noise after that)
CHECK_PROMPTS = ("<|im_start|>user\nWhat is 17 + 25? Answer with the number.<|im_end|>\n<|im_start|>assistant\n",
                 "<|im_start|>user\nName the largest planet in the solar system.<|im_end|>\n<|im_start|>assistant\n"
                 "The largest planet is")
GiB = 1024 ** 3


# ---------------------------------------------------------------- sampling and loading
def sampling(model_dir, tok, temperature=0.6):
    """{"temperature", "eos_ids", and any of FROM_GENERATION_CONFIG the snapshot's generation_config.json sets}."""
    gc = {}
    p = Path(model_dir) / "generation_config.json"
    if p.exists():
        gc = json.loads(p.read_text())
    eos = set()
    for v in (gc.get("eos_token_id"), tok.eos_token_id):
        eos |= set(v if isinstance(v, list) else [] if v is None else [v])
    for s in EXTRA_END:
        i = tok.convert_tokens_to_ids(s)
        if isinstance(i, int) and i != tok.unk_token_id and i >= 0:
            eos.add(i)
    out = {"temperature": temperature, "eos_ids": sorted(eos)}
    out.update({k: gc[k] for k in FROM_GENERATION_CONFIG if gc.get(k) is not None})
    return out


def load(model_dir, device="cuda", adapter=None):
    """(model, tokenizer): bf16 (fp32 on the CPU), sdpa attention, eval mode; a LoRA adapter merged in memory."""
    from finetune.gpu import kit
    import torch
    dev = torch.device(device) if isinstance(device, str) and device != "auto" else kit.pick_device(device)
    model = kit.load_model(model_dir, "bf16" if dev.type != "cpu" else "fp32", dev)
    if adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, str(adapter)).merge_and_unload().eval()
    return model, kit.load_tokenizer(model_dir)


# ---------------------------------------------------------------- tags as token ids
class TagTable:
    """Source tags as plain token ids (module docstring): install() widens the input embedding table, ids()
    gives a rendered prompt's ids moved to their sources' blocks."""
    ORDER = ("model", "system", "user", "tool")

    def __init__(self, tok, vocab_rows):
        from finetune.generate import Tagger
        from finetune.source_tags import SOURCES
        self.tagger = Tagger(tok, None, None)                     # ids_and_sources needs only the tokenizer
        self.rows = vocab_rows
        self.block = {SOURCES[s]: k for k, s in enumerate(self.ORDER)}

    @classmethod
    def install(cls, model, tok, tags):
        """Replace the model's input embeddings by len(ORDER) blocks of E + tag[source]; returns the table."""
        import torch
        from finetune.source_tags import SOURCES
        emb = model.get_input_embeddings()
        w = emb.weight.data
        tags = torch.as_tensor(tags).to(device=w.device)
        blocks = [w + tags[SOURCES[s]].to(w.dtype) for s in cls.ORDER]
        wide = torch.nn.Embedding(w.shape[0] * len(blocks), w.shape[1], device=w.device, dtype=w.dtype)
        wide.weight.data = torch.cat(blocks)
        wide.weight.requires_grad_(False)
        model.set_input_embeddings(wide)
        return cls(tok, w.shape[0])

    def ids(self, prompt):
        ids, src = self.tagger.ids_and_sources(prompt)
        return [t + self.rows * self.block[s] for t, s in zip(ids, src)]


# ---------------------------------------------------------------- shared pieces
def reply(tok, sample, toks, n_prompt, max_tokens, stops, name, start, kind, stopped=False):
    """The complete_fn reply for generated token ids (vLLM's fields); a stop string cuts the text after it."""
    text = tok.decode(toks, skip_special_tokens=True)
    if stops:
        hits = [(text.find(s), s) for s in stops if s in text]
        if hits:
            i, s = min(hits)
            text, stopped = text[:i + len(s)], True
    ended = bool(toks) and toks[-1] in sample["eos_ids"]
    finish = "stop" if stopped or ended or len(toks) < max_tokens else "length"
    return {"content": text, "finish": finish, "error": None, "reasoning": "",
            "usage": {"prompt_tokens": n_prompt, "completion_tokens": len(toks)},
            "latency_s": round(time.monotonic() - start, 2), "served_model": name, "requested_model_id": name,
            "reasoning_effort": None, "engine": kind}


def failed(name, err, kind):
    return {"content": "", "finish": "error", "error": f"{kind} engine: {err}", "reasoning": "", "usage": {},
            "latency_s": 0.0, "served_model": name, "requested_model_id": name, "reasoning_effort": None, "engine": kind}


def stop_index(tok, toks, stops, start):
    """The number of tokens up to the first one whose text completes a stop string (looking from token
    `start` on), or None."""
    for k in range(max(start, 1), len(toks) + 1):
        window = tok.decode(toks[max(0, k - STOP_WINDOW):k], skip_special_tokens=True)
        if any(s in window for s in stops):
            return k
    return None


def kv_bytes_per_request(config, tokens, dtype_bytes=2):
    """Key/value bytes one request of `tokens` tokens holds: full-attention layers keep every token, sliding
    layers at most their window."""
    heads = getattr(config, "num_key_value_heads", None) or config.num_attention_heads
    dim = getattr(config, "head_dim", None) or config.hidden_size // config.num_attention_heads
    types = getattr(config, "layer_types", None) or ["full_attention"] * config.num_hidden_layers
    window = getattr(config, "sliding_window", None) or tokens
    per_layer = 2 * heads * dim * dtype_bytes
    return sum(per_layer * (min(tokens, window) if t == "sliding_attention" else tokens) for t in types)


def workers_for(model, free_bytes, expected_tokens=12000, share=0.8, lo=4, hi=48):
    """Concurrent runs to keep in flight: the cache share of free memory over one request's key/value bytes
    at the expected length (requests start short; the scheduler evicts and recomputes if they all grow)."""
    per = kv_bytes_per_request(model.config, expected_tokens)
    return max(lo, min(hi, int(share * free_bytes // per)))


# ---------------------------------------------------------------- continuous batching
class Continuous:
    """complete_fn over transformers' ContinuousBatchingManager: one router thread hands each result to the
    caller waiting on it; requests with stop strings stream, and are cancelled at the stop."""
    kind = "continuous"

    def __init__(self, model, tok, sample, *, seed=0, encode=None, workers=8, log=print, cb_config=None):
        from transformers import GenerationConfig
        from transformers.generation.configuration_utils import ContinuousBatchingConfig
        self.tok, self.sample, self.workers, self.log = tok, sample, workers, log
        self.encode = encode or (lambda p: tok(p, add_special_tokens=False)["input_ids"])
        extra = {k: sample[k] for k in FROM_GENERATION_CONFIG if k in sample}
        gc = GenerationConfig(do_sample=sample["temperature"] > 0, temperature=sample["temperature"] or None,
                              top_k=extra.pop("top_k", 0), top_p=extra.pop("top_p", 1.0), max_new_tokens=32768,
                              eos_token_id=sample["eos_ids"], pad_token_id=tok.pad_token_id, **extra)
        self.manager = model.init_continuous_batching(generation_config=gc,
                                                      continuous_batching_config=ContinuousBatchingConfig(seed=seed, **(cb_config or {})))
        self.manager.start()
        self.lock, self.waiting, self.broken, self.closed = threading.Lock(), {}, None, False
        self.router = threading.Thread(target=self._route, daemon=True)
        self.router.start()

    def __call__(self, name, prompt, *, max_tokens, temperature=None, seed=None, backoff=None, extra=None):
        if temperature is not None and abs(temperature - self.sample["temperature"]) > 1e-9:
            raise ValueError(f"this engine samples at temperature {self.sample['temperature']}, not {temperature}")
        if self.broken:
            return failed(name, self.broken, self.kind)
        stops = list((extra or {}).get("stop") or ())
        ids = self.encode(prompt)
        r = {"done": threading.Event(), "stops": stops, "n": len(ids), "max": max_tokens, "name": name,
             "start": time.monotonic(), "checked": 0}
        with self.lock:
            rid = self.manager.add_request(ids, max_new_tokens=max_tokens, streaming=bool(stops))
            if rid is None:
                return failed(name, "the generation loop takes no new requests", self.kind)
            self.waiting[rid] = r
        r["done"].wait()
        return r["result"]

    def _deliver(self, rid, result):
        with self.lock:
            r = self.waiting.pop(rid, None)
        if r is not None:
            r["result"] = result
            r["done"].set()

    def _fail_all(self, err, broken=True):
        if broken:
            self.broken = str(err)
        with self.lock:
            rs, self.waiting = list(self.waiting.values()), {}
        for r in rs:
            r["result"] = failed(r["name"], err, self.kind)
            r["done"].set()

    def _route(self):
        while not self.closed:
            try:
                out = self.manager.get_result(timeout=0.5)
            except Exception as err:                              # noqa: BLE001 - the loop must not die silently
                self.log(f"continuous batching: reading results failed: {err!r}")
                self._fail_all(err)
                return
            if out is None:
                status = getattr(self.manager, "background_thread_status", None)
                fatal = getattr(status, "fatal_error", None)
                if fatal is not None or not self.manager.is_running():
                    if not self.closed:
                        self.log(f"continuous batching stopped: {fatal!r}")
                        self._fail_all(fatal or "the generation loop stopped")
                    return
                continue
            with self.lock:
                r = self.waiting.get(out.request_id)
            if r is None:
                continue
            if getattr(out, "error", None):
                self._deliver(out.request_id, failed(r["name"], out.error, self.kind))
                continue
            toks = list(out.generated_tokens)
            if r["stops"]:
                k = stop_index(self.tok, toks, r["stops"], r["checked"] + 1)
                r["checked"] = len(toks)
                if k is not None:
                    if not out.is_finished():
                        self.manager.cancel_request(out.request_id)
                    self._deliver(out.request_id, reply(self.tok, self.sample, toks[:k], r["n"], r["max"], r["stops"],
                                                        r["name"], r["start"], self.kind, stopped=True))
                    continue
            if out.is_finished():
                self._deliver(out.request_id, reply(self.tok, self.sample, toks, r["n"], r["max"], r["stops"], r["name"],
                                                    r["start"], self.kind))

    def close(self):
        self.closed = True
        try:
            self.manager.stop(block=True, timeout=30)
        finally:
            self._fail_all("the engine was closed", broken=False)       # closing is not breaking


# ---------------------------------------------------------------- static batches (the fallback)
class _NoHook:
    """provenance_job.Batched's hook interface, doing nothing (no provenance bias)."""

    def set_alpha(self, alpha):
        return self

    @contextmanager
    def marked(self, mark):
        yield self


def static(model, tok, sample, *, encode=None, workers=8, max_batch=8, token_budget=110000):
    from finetune.gpu.provenance_job import Batched
    eng = Batched(model, tok, _NoHook(), "deployable", max_batch=max_batch, token_budget=token_budget, sample=sample,
                  encode=encode)
    eng.kind, eng.workers, eng.broken = "static", workers, None
    return eng


# ---------------------------------------------------------------- the self-check and make()
def first_divergence(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def self_check(model, tok, sample, log=print):
    """(passed, details): continuous batching's greedy tokens against plain generate's on CHECK_PROMPTS."""
    import torch
    from transformers import GenerationConfig
    dev = next(model.parameters()).device
    prompts = [tok(p, add_special_tokens=False)["input_ids"] for p in CHECK_PROMPTS]
    ref = []
    with torch.no_grad():
        for ids in prompts:
            x = torch.tensor([ids], device=dev)
            ref.append(model.generate(input_ids=x, attention_mask=torch.ones_like(x), max_new_tokens=CHECK_TOKENS,
                                      do_sample=False, eos_token_id=sample["eos_ids"],
                                      pad_token_id=tok.pad_token_id)[0, len(ids):].tolist())
    gc = GenerationConfig(max_new_tokens=CHECK_TOKENS, do_sample=False, eos_token_id=sample["eos_ids"],
                          pad_token_id=tok.pad_token_id)
    start = time.monotonic()
    res = model.generate_batch(prompts, generation_config=gc, warmup=False)
    got = [list(o.generated_tokens) for o in sorted(res.values(), key=lambda o: int(o.request_id.split("_")[-1]))]
    agree = [first_divergence(a, b) for a, b in zip(got, ref)]
    need = [min(CHECK_AGREE, len(r)) for r in ref]
    ok = len(got) == len(ref) and all(a >= n for a, n in zip(agree, need))
    details = {"agree_from_first": agree, "needed": need, "tokens": CHECK_TOKENS, "seconds": round(time.monotonic() - start, 1)}
    log(f"continuous batching self-check: {'passed' if ok else 'FAILED'} {details}")
    return ok, details


def make(model, tok, sample, *, seed=0, encode=None, workers=None, log=print, check=True, engine="auto", cb_config=None):
    """The engine for a job: continuous batching if its self-check passes (engine 'auto'), else static
    batches; engine='continuous' or 'static' forces one. .workers: concurrent runs to keep in flight."""
    import torch
    from finetune.gpu import kit
    dev = next(model.parameters()).device
    attn = model.config._attn_implementation          # continuous batching switches it to paged|...; static needs it back
    if workers is None:
        free = kit.free_bytes(dev) if dev.type == "cuda" else 8 * GiB
        workers = workers_for(model, free)
    reason = engine
    if engine == "auto":
        try:
            ok, details = self_check(model, tok, sample, log) if check else (True, None)
            reason = "self-check passed" if ok else f"self-check failed: {details}"
            engine = "continuous" if ok else "static"
        except Exception as err:                                  # noqa: BLE001 - any failure means the fallback
            log(f"continuous batching self-check raised {err!r}: static batches instead")
            reason, engine = f"self-check raised {type(err).__name__}: {err}", "static"
            if dev.type == "cuda":
                torch.cuda.empty_cache()
    if engine == "continuous":
        try:
            eng = Continuous(model, tok, sample, seed=seed, encode=encode, workers=workers, log=log, cb_config=cb_config)
        except Exception as err:                                  # noqa: BLE001
            log(f"continuous batching failed to start ({err!r}): static batches instead")
            reason, engine = f"start raised {type(err).__name__}: {err}", "static"
    if engine == "static":
        if model.config._attn_implementation != attn:                 # a failed start can leave paged attention set
            model.set_attn_implementation(attn)
        torch.manual_seed(seed)
        eng = static(model, tok, sample, encode=encode, workers=min(workers, 16))
    eng.why = reason
    log(f"engine: {eng.kind} ({reason}); {eng.workers} runs in flight; sampling {sample}")
    return eng
