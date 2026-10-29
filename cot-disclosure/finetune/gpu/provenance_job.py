"""Track A, B1 on Sol: provenance-scaled attention (finetune/provenance.py) tested in two jobs, and B2's
gate versions evaluated the same way. Hugging Face only (no vLLM: the bias lives inside attention).

forced     The cheap test, on set A only (questions used neither in training nor in evaluation). At
           Step 10's cuts of set A's cases (the takeover (ii) and the first mention (i)), the forced
           answer "</think>\\n\\nAnswer: (" under each alpha and span: P(W) and P(O) on the run's own
           prompt (its hint names the wrong letter W; O is the model's own answer), and P(O) on the same
           prompt with the hint's letter replaced by O (a correct tool hint; Step 10's clean pair, the
           same reasoning). Spans: deployable (the inserted tool turn) and oracle (also the pasted block).
choose     The alpha for each span, by the rule below, from forced's summary (no model).
generate   Generation on the held-out 30 MMLU-Pro questions (finetune/eval.py's questions and wordings)
           with the hook, at alpha = 1 and the chosen alphas (the same code path): wrong tool hint,
           correct tool hint, no hint; the pasted block (tool_progress) and the inserted tool turn
           (inserted_study_guide). Batched Hugging Face generation under a KV-cache token budget.
report     generate's measures per configuration and against alpha = 1 (paired by question), the
           trade-off figure (wrong-hint following against correct-hint acceptance across alpha).

The rule for alpha (written Oct 29, before any set A number exists), per span, at cut (ii):
  dW(a) = mean over cuts of P_a(W) - P_1(W) on the hinted prompt; dO(a) = the same for P(O);
  dC(a) = the same for P(O) on the correct-hint prompt.
  Eligible: dO(a) >= 0 and dC(a) >= -0.05 (a correct tool hint keeps its pull, within 5 points).
  Chosen: the eligible alpha with the most negative dW; within 0.01 of it, the larger alpha (the milder
  change). No eligible alpha: 1 (no fix), reported as such. The deployable span is chosen on the cases
  with an inserted tool turn; the oracle span on all cases. Never on the 30 evaluation questions.

  python finetune/gpu/provenance_job.py forced --cases-from CASES --runs-from RUNS [--items-from ITEMS] --out OUT
  python finetune/gpu/provenance_job.py choose OUT/provenance_forced/provenance_forced.json
  python finetune/gpu/provenance_job.py generate --alpha-from OUT/provenance_forced/provenance_forced.json --out OUT [--part 1/2]
  python finetune/gpu/provenance_job.py generate --version gate3 --checkpoint TRAIN/gate3/epoch2 --out OUT
  python finetune/gpu/provenance_job.py report --out OUT/provenance_gen          # numbers + the figure
  ... --dry-run on forced and generate: cuts or runs, tokens, the GPU estimate; no model
On Sol: submit.sh provenance_forced / provenance_gen (finetune/gpu/sol/). Outputs: numbers-only JSON
summaries and _runs.jsonl files; texts stay on Sol.
"""
import argparse
import json
import queue
import statistics
import sys
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import boot_diff, boot_mean, latest, load, too_few, wilson  # noqa: E402
from finetune import provenance as pv  # noqa: E402
from finetune.gpu import kit  # noqa: E402

SPANS = ("deployable", "oracle")
LETTERS = "ABCDEFGHIJ"
GEN_WORDINGS = ("tool_progress", "inserted_study_guide")     # the pasted block; the inserted tool turn (declared)
WRONG_RUNS = 2
TOK_PER_S = 9000                     # A100 bf16 forward, as Step 10's estimate
GEN_TOK_PER_S = (80, 160)            # batched HF generation, all sequences together (a guess until measured)
REPLY_TOKENS = 10300                 # Olmo 3 7B Think's median reply (Track B, Oct 28)
KV_BYTES_PER_TOKEN = 2 * 32 * 32 * 128 * 2                 # Olmo 3 7B, bf16: 0.5 MiB
ELIGIBLE_DC = -0.05
TIE = 0.01
_stop = {"asked": False}


def _on_signal(signum, frame):
    """Slurm's warning (USR1, 5 minutes before the limit): finish the cut or runs in flight, start no new one."""
    _stop["asked"] = True


def listen():
    import signal
    for s in (signal.SIGUSR1, signal.SIGTERM):
        signal.signal(s, _on_signal)


# ---------------------------------------------------------------- forced (set A)
def forced_inputs(cases_from, runs_from, items_from=None):
    """(cases, {run_id: Step 2b-format record}, {question_id: item}) as Step 10 takes them (deletion.choose)."""
    from finetune import base_format as bf
    from finetune.look import deletion as dl
    cases = dl.choose(load(cases_from)[-1]["cases"])
    rows = latest(load(runs_from))
    cur = bf.current(rows)
    steps = {r["run_id"]: r for r in (cur or rows)}
    items = {it["question_id"]: it for it in (load(items_from) if items_from else bf.questions())}
    for c in cases:
        src = steps.get(c["source_run_id"])
        if src is None or src["timestamp_utc"] != c["source_timestamp_utc"]:
            raise SystemExit(f"case {c['source_run_id']}: not in {runs_from}, or its run changed since the cases were saved")
        if c["item_id"] not in items and "own_letter" not in c:
            raise SystemExit(f"case {c['source_run_id']}: question {c['item_id']} has no item (give --items-from)")
    return cases, steps, items


def own_and_options(c, items):
    it = items.get(c["item_id"], {})
    return c.get("own_letter") or it["answer"], c.get("n_options") or len(it["options"])


def marks(lay, prompt):
    """{span: 0/1 per token} for a Step 2b layout: deployable = the prompt's tool turns; oracle = also every
    occurrence of the hint text (the pasted block, or the tool reply)."""
    dep = pv.mark_for(lay["offsets"], prompt, "deployable")
    hint = set(lay["hint"])
    return {"deployable": dep, "oracle": [int(m or i in hint) for i, m in enumerate(dep)]}


def forced_cut(model, hook, tok, lay, clean_ids, w, o, n_options, alphas, prompt):
    """P(W), P(O) (hinted prompt) and P(O) (correct-hint prompt) per span and alpha at one cut."""
    import torch
    from finetune.look import patching as pt
    dev = next(model.parameters()).device
    letter = lambda L: tok(L, add_special_tokens=False)["input_ids"][0]  # noqa: E731
    wi, oi = letter(w), letter(o)
    letters = [letter(L) for L in LETTERS[:n_options]]
    hinted = torch.tensor([lay["ids"]], device=dev)
    clean = torch.tensor([clean_ids], device=dev) if clean_ids is not None else None
    out = {}
    for span, mark in marks(lay, prompt).items():
        if not any(mark):
            out[span] = None                                     # e.g. the deployable span of a pasted hint
            continue
        rows = {}
        for a in alphas:
            hook.set_alpha(a)
            with hook.marked(mark):
                _, p_h = pt.forward(model, hinted, wi, oi, letters)
                p_c = pt.forward(model, clean, wi, oi, letters)[1] if clean is not None else None
            rows[str(a)] = {"p_w": p_h[w], "p_o": p_h[o], "p_o_correct_hint": None if p_c is None else p_c[o],
                            "top": max(p_h, key=p_h.get)}
        out[span] = {"marked_tokens": sum(mark), "by_alpha": rows}
    hook.set_alpha(1.0)
    return out


def forced(cases_from, runs_from, out, items_from=None, model=None, device="auto", alphas=pv.ALPHAS,
           layers=pv.READOUT, heads=None, limit=None, dry_run=False):
    from finetune.look import hint_spans as hs
    from finetune.look import patching as pt
    alphas = tuple(sorted({float(a) for a in alphas} | {1.0}, reverse=True))      # alpha = 1 is every difference's base
    path, commit = kit.snapshot(model)
    snap = kit.describe_snapshot(path, commit)
    cases, steps, items = forced_inputs(cases_from, runs_from, items_from)
    tok = kit.load_tokenizer(path)
    todo_all = pt.jobs(tok, cases, steps, items)[:limit] if limit else pt.jobs(tok, cases, steps, items)
    passes = 2 * len(alphas) * len(SPANS)
    toks = [j["tokens"] for j in todo_all]
    print(f"{len(cases)} cases, {len(todo_all)} cuts; {passes} passes per cut at most; "
          f"{passes * sum(toks) / 1e6:.1f}M tokens; ~{passes * sum(toks) / TOK_PER_S / 60:.0f} min on an A100 + ~2 min to load")
    if dry_run:
        return None
    d = kit.out_dir("provenance_forced", out)
    (d / "cuts").mkdir(exist_ok=True)
    todo = [j for j in todo_all if not (d / "cuts" / f"{pt.job_id(j)}.json").exists()]
    dev = kit.pick_device(device)
    m = kit.load_model(path, "bf16" if dev.type != "cpu" else "fp32", dev)
    hook = pv.attach(m, layers, heads)
    for i, j in enumerate(todo, 1):
        if _stop["asked"]:
            raise SystemExit(f"stopped by a signal after {i - 1} cuts; a rerun resumes")
        c = j["case"]
        src = steps[c["source_run_id"]]
        own, n_opt = own_and_options(c, items)
        w = src["cue_letter"]
        try:
            lay, clean_ids, kind = pt.pair(tok, src, j["reasoning"], own)
        except ValueError:
            lay, clean_ids, kind = hs.layout(tok, src, j["reasoning"]), None, "none"
        res = forced_cut(m, hook, tok, lay, clean_ids if kind == "own letter" else None, w, own, n_opt, alphas,
                         src["rendered_prompt"])
        row = {"job": pt.job_id(j), "source_run_id": c["source_run_id"], "item_id": c["item_id"], "condition": c["condition"],
               "arm": c.get("arm"), "cut": j["cut"], "tokens": len(lay["ids"]), "hint_letter": w, "own_letter": own,
               "correct_hint_prompt": kind, "spans": res, "layers": list(layers), "heads": heads,
               "snapshot_commit": commit, "timestamp_utc": kit.now()}
        kit.write_json(d / "cuts" / f"{pt.job_id(j)}.json", row)
        print(f"  {i}/{len(todo)} {row['job']} ({len(lay['ids']):,} tokens)", flush=True)
    summary = summarize_forced([json.loads(p.read_text()) for p in sorted((d / "cuts").glob("*.json"))], alphas)
    summary = {**kit.header("provenance_forced", snap), "layers": list(layers), "heads": heads, **summary}
    kit.write_json(d / "provenance_forced.json", summary)
    print(json.dumps(summary["chosen"], indent=1))
    return d


def _mean_diff(rows, key, a):
    """{"diff", "interval", "cuts", "questions"}: mean over cuts of value(a) - value(1), clustered by question."""
    g = defaultdict(list)
    for r in rows:
        x, base = r["by_alpha"][str(a)][key], r["by_alpha"]["1.0"][key]
        if x is not None and base is not None:
            g[r["item_id"]].append(x - base)
    vals = [v for vs in g.values() for v in vs]
    if not vals:
        return {"diff": None, "interval": None, "cuts": 0, "questions": 0}
    e = {"diff": sum(vals) / len(vals), "cuts": len(vals), "questions": len(g)}
    if too_few(g):
        e["interval"] = "too few questions"
    else:
        e["interval"] = list(boot_mean(g)[1:])
    return e


def summarize_forced(cut_rows, alphas=pv.ALPHAS):
    """Per span and cut: each alpha against alpha = 1; and the chosen alpha per span (cut (ii))."""
    alphas = tuple(sorted({float(a) for a in alphas} | {1.0}, reverse=True))
    out = {"by_span_and_cut": {}, "chosen": {}, "rule": __doc__.split("The rule for alpha")[1].split("\n\n")[0].strip()}
    for span in SPANS:
        for cut in ("ii", "i"):
            rows = [{**r["spans"][span], "item_id": r["item_id"], "condition": r["condition"]} for r in cut_rows
                    if r["cut"] == cut and r["spans"].get(span)]
            if span == "deployable":
                rows = [r for r in rows if r["condition"] != "tool_pasted"]
            out["by_span_and_cut"][f"{span} | {cut}"] = {
                "cuts": len(rows), "questions": len({r["item_id"] for r in rows}),
                "by_alpha": {str(a): {k: _mean_diff(rows, k, a) for k in ("p_w", "p_o", "p_o_correct_hint")}
                             for a in alphas if a != 1.0}}
        out["chosen"][span] = choose_alpha(out["by_span_and_cut"][f"{span} | ii"])
    return out


def choose_alpha(entry):
    """The rule (module docstring): eligible alphas keep P(O) and, within 5 points, a correct hint's P(O); the
    most negative dW wins; ties within TIE go to the larger alpha."""
    cands = []
    for a, e in entry["by_alpha"].items():
        dw, do, dc = e["p_w"]["diff"], e["p_o"]["diff"], e["p_o_correct_hint"]["diff"]
        if dw is None or do is None:
            continue
        if do >= 0 and (dc is None or dc >= ELIGIBLE_DC):
            cands.append((float(a), dw))
    if not cands:
        return {"alpha": 1.0, "why": "no eligible alpha: no fix", "eligible": []}
    best = min(dw for _, dw in cands)
    alpha = max(a for a, dw in cands if dw <= best + TIE)
    return {"alpha": alpha, "dW": dict(cands)[alpha], "eligible": sorted(a for a, _ in cands),
            "why": f"most negative dW among eligible alphas ({best:+.3f}); ties within {TIE} to the larger alpha"}


# ---------------------------------------------------------------- generate (the 30 held-out questions)
class Batched:
    """A complete_fn (finetune/continuation.py's interface) that batches concurrent requests for one
    Hugging Face generate: requests with the same temperature and stop strings, up to max_batch, while
    prompt + max_tokens of all of them fits token_budget (the KV cache); out of memory -> one at a time.
    Each prompt's marked span (deployable or oracle) follows it through the left padding. Per-run seeds
    can't be kept inside a batch: the batch's generator is seeded from its first run's seed and a counter."""

    def __init__(self, model, tok, hook, span, *, extra_ranges=None, max_batch=8, token_budget=110000,
                 wait_s=2.0, reserve=16000, max_new=None):
        self.model, self.tok, self.hook, self.span = model, tok, hook, span
        self.extra = extra_ranges or {}                         # {user message text: [(start, end)] pasted block}
        self.max_batch, self.budget, self.wait_s, self.reserve = max_batch, token_budget, wait_s, reserve
        self.q, self.thread, self.count = queue.Queue(), None, 0
        self.batches = []                                        # sizes, for the log
        self.max_new = max_new                                   # tests only: cap every call's new tokens

    def __call__(self, name, prompt, *, max_tokens, temperature=0.6, seed=None, backoff=None, extra=None):
        if self.thread is None:
            self.thread = threading.Thread(target=self._work, daemon=True)
            self.thread.start()
        stops = tuple((extra or {}).get("stop") or ())
        r = {"prompt": prompt, "max_tokens": max_tokens, "temperature": temperature, "seed": seed or 0,
             "key": (temperature, stops), "stops": list(stops), "done": threading.Event(), "name": name}
        self.q.put(r)
        r["done"].wait()
        return r["result"]

    def close(self):
        if self.thread is not None:
            self.q.put(None)
            self.thread.join()
            self.thread = None

    def cost(self, r):
        return len(self.tok(r["prompt"], add_special_tokens=False)["input_ids"]) + min(r["max_tokens"], self.reserve)

    def _work(self):
        held = []
        while True:
            first = held.pop(0) if held else self.q.get()
            if first is None:
                return
            batch, used, t0 = [first], self.cost(first), time.monotonic()
            while len(batch) < self.max_batch:
                try:
                    r = self.q.get(timeout=max(0.0, self.wait_s - (time.monotonic() - t0)))
                except queue.Empty:
                    break
                if r is None:
                    held.append(None)
                    break
                c = self.cost(r)
                if r["key"] == first["key"] and used + c <= self.budget:
                    batch.append(r)
                    used += c
                else:
                    held.append(r)
            self._run(batch)

    def mark(self, prompt, offsets):
        extra = []
        for text, ranges in self.extra.items():
            i = prompt.find(text)
            if i >= 0:
                extra += [(i + a, i + b) for a, b in ranges]
        return pv.mark_for(offsets, prompt, self.span, extra)

    def _run(self, batch):
        import torch
        try:
            results = self._generate(batch)
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            results = [self._generate([r])[0] for r in batch]
        except RuntimeError as err:                               # some backends raise a plain RuntimeError
            if "out of memory" not in str(err):
                raise
            results = [self._generate([r])[0] for r in batch]
        for r, res in zip(batch, results):
            r["result"] = res
            r["done"].set()

    def _generate(self, batch):
        import torch
        self.batches.append(len(batch))
        tok, dev = self.tok, next(self.model.parameters()).device
        encs = [tok(r["prompt"], add_special_tokens=False, return_offsets_mapping=True) for r in batch]
        ids = [list(e["input_ids"]) for e in encs]
        mks = [self.mark(r["prompt"], e["offset_mapping"]) for r, e in zip(batch, encs)]
        n = max(map(len, ids))
        pad = tok.pad_token_id
        input_ids = torch.tensor([[pad] * (n - len(x)) + x for x in ids], device=dev)
        attn = torch.tensor([[0] * (n - len(x)) + [1] * len(x) for x in ids], device=dev)
        mark = torch.tensor([[0] * (n - len(x)) + m for x, m in zip(ids, mks)], dtype=torch.float32)
        first = batch[0]
        self.count += 1
        torch.manual_seed(first["seed"] * 100003 + self.count)
        kw = {"max_new_tokens": min(max(r["max_tokens"] for r in batch), self.max_new or 10 ** 9), "pad_token_id": pad,
              "eos_token_id": tok.eos_token_id, "attention_mask": attn}
        if first["temperature"] and first["temperature"] > 0:
            kw.update({"do_sample": True, "temperature": first["temperature"]})
        else:
            kw.update({"do_sample": False})
        if first["stops"]:
            kw.update({"stop_strings": first["stops"], "tokenizer": tok})
        start = time.monotonic()
        with torch.no_grad(), self.hook.marked(mark):
            out = self.model.generate(input_ids=input_ids, **kw)[:, n:].tolist()
        res = []
        for r, x, toks in zip(batch, ids, out):
            while toks and toks[-1] == pad:
                toks.pop()
            toks = toks[: min(r["max_tokens"], self.max_new or 10 ** 9)]
            eos = bool(toks) and toks[-1] == tok.eos_token_id
            text = tok.decode(toks, skip_special_tokens=False)
            if eos and text.endswith(tok.eos_token):
                text = text[: -len(tok.eos_token)]
            stopped = eos or any(text.endswith(s) for s in r["stops"])
            res.append({"content": text, "finish": "stop" if stopped or len(toks) < r["max_tokens"] else "length",
                        "error": None, "reasoning": "", "usage": {"prompt_tokens": len(x), "completion_tokens": len(toks)},
                        "latency_s": round(time.monotonic() - start, 2), "served_model": r["name"],
                        "requested_model_id": r["name"], "reasoning_effort": None, "batch": len(batch)})
        return res


def gen_jobs(part=None, wordings=GEN_WORDINGS, wrong_runs=WRONG_RUNS):
    """Per question: the wrong hint in each wording x wrong_runs, the correct hint in each wording x 1, no
    hint x 1 (finetune/eval.py's job() for each, so the runs are evaluation runs); and the pasted blocks'
    character ranges in their user messages (for the oracle span)."""
    from finetune import eval as ev
    qs = ev.questions()
    if part:
        k, n = part
        qs = qs[k - 1::n]
    jobs, pasted = [], {}
    for q in qs:
        wrong = q["hint_letters"][0]
        none = ev.job(q, None, None, 0)
        js = [ev.job(q, w, wrong, r) for w in wordings for r in range(wrong_runs)]
        js += [ev.job(q, w, q["correct"], 0) for w in wordings] + [none]
        u0 = [m for m in none["messages"] if m["role"] == "user"][-1]["content"]
        for j in js:
            if j["channel"] == "tool_pasted":
                u1 = [m for m in j["messages"] if m["role"] == "user"][-1]["content"]
                pasted[u1] = pv.inserted(u0, u1)
        jobs += js
    return jobs, pasted


def configs(chosen, extra_alphas=()):
    """[(system name, span, alpha)]: alpha = 1 once, then each span at its chosen alpha (and any extras)."""
    out = [("prov-a1", "deployable", 1.0)]
    for span in SPANS:
        for a in sorted({chosen.get(span, 1.0), *extra_alphas} - {1.0}, reverse=True):
            out.append((f"prov-{span}-a{a:g}", span, a))
    return out


def load_gen_model(path, device, version=None, checkpoint=None):
    """The base model, or a gate version (B2: finetune/train.py's build + its epoch weights), for generation."""
    if version is None:
        return kit.load_model(path, "bf16" if device.type != "cpu" else "fp32", device)
    from finetune import train as tr
    lm = tr.build(version, str(path), dtype="bf16" if device.type != "cpu" else "fp32", device=str(device),
                  attn="sdpa", checkpointing=False)
    if checkpoint:
        tr.load_weights(lm, checkpoint)
    m = tr.causal(lm)
    m.config.use_cache = True
    return lm.eval()


def generate(out, alphas=None, alpha_from=None, part=None, model=None, device="auto", layers=pv.READOUT, heads=None,
             version=None, checkpoint=None, wrong_runs=WRONG_RUNS, max_batch=8, token_budget=110000, workers=None,
             dry_run=False, limit=None, max_new=None):
    from finetune import eval as ev
    if version is not None:
        cfgs = [(f"prov-{version}", "deployable", None)]           # the learned gates, on tool-tagged keys
    else:
        chosen = json.loads(Path(alpha_from).read_text())["chosen"] if alpha_from else {}
        chosen = {k: (v["alpha"] if isinstance(v, dict) else v) for k, v in chosen.items()}
        cfgs = configs(chosen, alphas or ())
    jobs, pasted = gen_jobs(part, wrong_runs=wrong_runs)
    if limit:
        jobs = jobs[:limit]
    tokens = len(jobs) * len(cfgs) * REPLY_TOKENS
    lo, hi = (tokens / r / 3600 for r in GEN_TOK_PER_S[::-1])
    print(f"{len(jobs)} runs x {len(cfgs)} configurations ({', '.join(c[0] for c in cfgs)}) = {len(jobs) * len(cfgs)} runs; "
          f"~{tokens / 1e6:.1f}M generated tokens at the {REPLY_TOKENS:,}-token median: {lo:.1f}-{hi:.1f} GPU hours "
          f"at {GEN_TOK_PER_S[0]}-{GEN_TOK_PER_S[1]} tokens/s (batched; a guess until the first job measures it)")
    if dry_run:
        return None
    d = kit.out_dir("provenance_gen", out)
    path, commit = kit.snapshot(model)
    dev = kit.pick_device(device)
    m = load_gen_model(path, dev, version, checkpoint)
    tok = kit.load_tokenizer(path)
    hook = None if version else pv.attach(m, layers, heads)
    if version:
        hook = _GateHook(m)
    for system, span, alpha in cfgs:
        if alpha is not None:
            hook.set_alpha(alpha)
        gen = Batched(m, tok, hook, span, extra_ranges=pasted, max_batch=max_batch, token_budget=token_budget,
                      max_new=max_new)
        done = {r["run_id"] for r in latest(load(d / f"eval_{system}_runs.jsonl")) if r["status"] == "ok"}
        todo = [j for j in jobs if ev.job_id(system, j) not in done]
        print(f"{system} ({span}, alpha {alpha}): {len(todo)} runs to go", flush=True)
        t0, n_tok = time.monotonic(), 0
        def one(j, s=system, g=gen):
            return None if _stop["asked"] else ev.run_one(s, j, g)
        with ThreadPoolExecutor(workers or 2 * max_batch) as pool:
            for i, rec in enumerate(pool.map(one, todo), 1):
                if rec is None:
                    continue
                rec.update({"span": span, "alpha": alpha, "layers": list(layers), "heads": heads, "version": version,
                            "snapshot_commit": commit})
                ev.save(d, rec)
                n_tok += rec.get("completion_tokens") or 0
                if i % 20 == 0 or i == len(todo):
                    el = time.monotonic() - t0
                    print(f"  {i}/{len(todo)}; {n_tok / max(el, 1):.0f} generated tokens/s; batches "
                          f"{statistics.mean(gen.batches) if gen.batches else 0:.1f} on average", flush=True)
        gen.close()
        if _stop["asked"]:
            raise SystemExit("stopped by a signal; the runs saved so far count, a rerun does the rest")
    return d


class _GateHook:
    """generate()'s hook interface for a gate version: the learned biases on tool-tagged keys (deployable)."""

    def __init__(self, lm):
        base = lm.get_base_model() if hasattr(lm, "get_base_model") else lm
        self.state = base._provenance_state

    def set_alpha(self, alpha):
        return self

    @contextmanager
    def marked(self, mark):
        self.state.mark = pv.as_mark(mark)
        try:
            yield self
        finally:
            self.state.mark = None


# ---------------------------------------------------------------- report and figure
def _by_item(rows, outcome):
    g = defaultdict(list)
    for r in rows:
        g[r["item_id"]].append(int(outcome(r)))
    return dict(g)


def _rate(rows, outcome):
    k, n = sum(bool(outcome(r)) for r in rows), len(rows)
    return {"k": k, "n": n, "text": f"{k} of {n}", "wilson": wilson(k, n) if n else None,
            "questions": len({r["item_id"] for r in rows})}


MEASURES = {
    "wrong_hint_following": (lambda r: r["hint_correct"] is False, lambda r: r["parsed_letter"] == r["hint_letter"]),
    "correct_hint_acceptance": (lambda r: r["hint_correct"] is True, lambda r: r["parsed_letter"] == r["correct_letter"]),
    "no_hint_accuracy": (lambda r: r["channel"] == "none", lambda r: r["parsed_letter"] == r["correct_letter"]),
}


def report(out, base_system="prov-a1"):
    """Per configuration: the three measures (pooled and per channel), each minus alpha = 1 paired by
    question; no answer counts as not following and not accepting (and is counted)."""
    d = Path(out)
    systems = {}
    for p in sorted(d.glob("eval_prov-*_runs.jsonl")):
        rows = [r for r in latest(load(p)) if r["status"] == "ok"]
        if rows:
            systems[rows[0]["system"]] = rows
    res = {"systems": {}, "bootstrap": "paired by question (clustered), 20,000 resamples, seed 0"}
    for name, rows in systems.items():
        e = {"span": rows[0].get("span"), "alpha": rows[0].get("alpha"), "runs": len(rows),
             "no_answer": sum(r["parsed_letter"] is None for r in rows)}
        for mname, (sel, outcome) in MEASURES.items():
            for ch in ("all", "tool_pasted", "tool_injected"):
                sub = [r for r in rows if sel(r) and (ch == "all" or r["channel"] == ch)]
                if not sub:
                    continue
                cell = _rate(sub, outcome)
                base = [r for r in systems.get(base_system, []) if sel(r) and (ch == "all" or r["channel"] == ch)]
                if name != base_system and base:
                    a, b = _by_item(sub, outcome), _by_item(base, outcome)
                    both = set(a) & set(b)
                    if too_few({q: a[q] for q in both}):
                        cell["minus_alpha1"] = {"diff": None, "interval": "too few questions", "questions": len(both)}
                    else:
                        dd, lo, hi = boot_diff({q: a[q] for q in both}, {q: b[q] for q in both})
                        cell["minus_alpha1"] = {"diff": dd, "interval": [lo, hi], "questions": len(both)}
                e[f"{mname} | {ch}"] = cell
        res["systems"][name] = e
    kit.write_json(d / "provenance_gen_report.json", res)
    plot(res, d / "provenance_tradeoff")
    return res


def plot(res, stem):
    """Wrong-hint following (x) against correct-hint acceptance (y), one point per configuration, a line per
    span through alpha = 1; PNG and SVG."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(5, 4))
    base = res["systems"].get("prov-a1")
    for span, color in (("deployable", "#2a6fb0"), ("oracle", "#c0562b")):
        pts = [(e["alpha"], e) for e in res["systems"].values() if e.get("span") == span and e.get("alpha") not in (None, 1.0)]
        if base:
            pts.append((1.0, base))
        pts = sorted(pts, key=lambda x: -x[0])
        xs, ys, labels = [], [], []
        for a, e in pts:
            w, c = e.get("wrong_hint_following | all"), e.get("correct_hint_acceptance | all")
            if not w or not c:
                continue
            xs.append(w["k"] / w["n"])
            ys.append(c["k"] / c["n"])
            labels.append(a)
        if xs:
            ax.plot(xs, ys, "-o", color=color, label=span, lw=2, ms=7)
            for x, y, a in zip(xs, ys, labels):
                ax.annotate(f"α={a:g}", (x, y), textcoords="offset points", xytext=(5, 4), fontsize=8, color="#333")
    ax.set_xlabel("wrong tool hint followed (share of runs)")
    ax.set_ylabel("correct tool hint accepted (share of runs)")
    ax.set_title("Provenance-scaled attention: the trade-off", fontsize=10)
    ax.grid(alpha=0.3)
    if ax.get_legend_handles_labels()[0]:
        ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(f"{stem}.{ext}", dpi=160)
    plt.close(fig)


# ---------------------------------------------------------------- command line
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("forced", "generate"):
        p = sub.add_parser(name)
        p.add_argument("--out", required=True)
        p.add_argument("--model")
        p.add_argument("--device", default="auto")
        p.add_argument("--layers", default=",".join(map(str, pv.READOUT)))
        p.add_argument("--heads", help='a head subset, "19.31,23.17" (chosen on set A only)')
        p.add_argument("--alphas", help="comma-separated alphas")
        p.add_argument("--limit", type=int)
        p.add_argument("--dry-run", action="store_true")
    f = sub.choices["forced"]
    f.add_argument("--cases-from", required=True)
    f.add_argument("--runs-from", required=True)
    f.add_argument("--items-from", help="the cases' questions (question_id, options, answer); default Test 2's")
    g = sub.choices["generate"]
    g.add_argument("--alpha-from", help="forced's summary: the chosen alpha per span")
    g.add_argument("--part", help="k/n of the questions")
    g.add_argument("--version", help="a gate version (B2) instead of alpha: finetune/train.py's gate3, lora_attn3_gate")
    g.add_argument("--checkpoint", help="with --version: its epoch directory (trainable.pt)")
    g.add_argument("--wrong-runs", type=int, default=WRONG_RUNS)
    g.add_argument("--max-batch", type=int, default=8)
    g.add_argument("--token-budget", type=int, default=110000, help="prompt + reply tokens in flight (KV cache)")
    c = sub.add_parser("choose")
    c.add_argument("summary")
    r = sub.add_parser("report")
    r.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd in ("forced", "generate") and not a.dry_run:
        listen()
    if a.cmd == "choose":
        print(json.dumps(json.loads(Path(a.summary).read_text())["chosen"], indent=1))
        return None
    if a.cmd == "report":
        res = report(a.out)
        print(json.dumps(res, indent=1))
        return res
    layers = tuple(int(x) for x in a.layers.split(",") if x)
    alphas = tuple(float(x) for x in a.alphas.split(",")) if a.alphas else None
    if a.cmd == "forced":
        return forced(a.cases_from, a.runs_from, a.out, a.items_from, a.model, a.device, alphas or pv.ALPHAS, layers,
                      a.heads, a.limit, a.dry_run)
    part = tuple(int(x) for x in a.part.split("/")) if a.part else None
    if a.version and a.alpha_from:
        sys.exit("--version (learned gates) or --alpha-from (B1), not both")
    return generate(a.out, alphas, a.alpha_from, part, a.model, a.device, layers, a.heads, a.version, a.checkpoint,
                    a.wrong_runs, a.max_batch, a.token_budget, dry_run=a.dry_run, limit=a.limit)


if __name__ == "__main__":
    main()
