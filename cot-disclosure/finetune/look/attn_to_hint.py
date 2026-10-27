"""Track A, step 9: attention to the hint. How strongly do the answer and the reasoning attend to
the hint's words?

One forward pass per run, no gradients, over prompt + reasoning + "</think>\\n\\nAnswer: (", for every
hinted Step 2b run that ended with an answer (199: followed or resisted, user / pasted tool /
inserted tool / inserted tool with the function declared). No output_attentions on full sequences:
an attention implementation registered here receives each layer's queries and keys after the
rotary embedding, computes the masses below, and then runs the model's own attention (sdpa)
unchanged. Grouped key/value heads are expanded; in a sliding-window layer (24 of Olmo 3 7B's
32, window 4,096) a query sees only the last 4,096 keys (itself included), so a reasoning token
more than 4,096 tokens past the hint gives it exactly 0 there. In chunks of query rows (and of
keys), in fp32:
  mass on a span = exp(logsumexp(scores to the span's visible keys) - logsumexp(scores to every visible key))
Spans (finetune/look/hint_spans.py): the hint (its whole text), its letter, and a control span of
the question stem with as many tokens as the hint, so "a lot of attention" has a baseline.
Measured from:
  the answer position   the last token, "(" of "Answer: (": the presentation's "how strongly the
                        answer attends to the hint's words"; per layer and head
  each reasoning sentence  the mean over the sentence's tokens, per layer and head: a curve
Comparisons (bootstrap clustered by question): followed vs resisted; tool vs user; pasted vs
inserted tool. The top heads are chosen on all runs pooled (so they favour no group).

  python finetune/look/attn_to_hint.py --dry-run     # runs, tokens, memory, estimated GPU time; no model
  python finetune/look/attn_to_hint.py               # all runs -> $TRACKA_OUT/step9/ (resumable: one .npz per run)
  python finetune/look/attn_to_hint.py --limit 3     # a quick check on the 3 shortest runs
  python finetune/look/attn_to_hint.py --report      # step9_attention.json (copy back) + step9_maps.npz; no model
  python finetune/look/attn_to_hint.py --followup    # step9_followup.json (copy back) + step9_aligned.png; no model:
                                                     # full-attention layers only, the runs within the window apart,
                                                     # hint - control and per token, readout heads, aligned curve
On Sol: finetune/gpu/sol/run.sh step9 [args] (session) or finetune/gpu/sol/submit.sh step9 (batch).
--model and --runs-from let the same code run on a trained version and its own runs (Phase 6).
"""
import argparse
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import MIN_QUESTIONS, append, boot_diff, boot_mean, load, too_few  # noqa: E402
from finetune.gpu import kit  # noqa: E402
from finetune.look import hint_spans as hs  # noqa: E402

SETS = ("hint", "letter", "control")
CAPTURE = "trackA_capture"
Q_CHUNK, K_CHUNK = 512, 4096
TOP_HEADS = 10
BINS = 10
FORCE_LETTERS = "ABCDEFGHIJ"
HEADROOM = 6 * kit.GiB
TOK_PER_S = 9000          # A100 bf16 forward, for the estimate (7B, ~12k-token prompts)
FP32_FLOPS = 1.0e13       # effective fp32 matmul rate for the masses, for the estimate


# ---------------------------------------------------------------- the masses
def span_mass(q, k, rows, sets, scaling, window=None, q_chunk=Q_CHUNK, k_chunk=K_CHUNK):
    """Attention mass on each key set, per head, for the query rows `rows` (ascending positions).
    q: [heads, L, d] and k: [kv heads, L, d], after the rotary embedding; sets: {name: key positions}.
    Row i sees keys j <= i, and i - j < window in a sliding-window layer (as transformers masks
    them). Returns {name: [heads, len(rows)]} in fp32."""
    import torch
    heads = q.shape[0]
    if k.shape[0] != heads:                                           # grouped key/value heads
        k = k.repeat_interleave(heads // k.shape[0], dim=0)
    out = {n: torch.empty(heads, len(rows), device=q.device) for n in sets}
    for a in range(0, len(rows), q_chunk):
        r = rows[a:a + q_chunk]
        qc = q[:, r].float() * scaling
        top = int(r[-1]) + 1
        lo = 0 if window is None else max(0, int(r[0]) - window + 1)
        lse = torch.full((heads, len(r)), -math.inf, device=q.device)
        for b in range(lo, top, k_chunk):
            e = min(b + k_chunk, top)
            j = torch.arange(b, e, device=q.device)
            s = (qc @ k[:, b:e].float().transpose(1, 2)).masked_fill(~visible(r, j, window)[None], -math.inf)
            lse = torch.logaddexp(lse, torch.logsumexp(s, dim=-1))
        for n, ks in sets.items():
            s = (qc @ k[:, ks].float().transpose(1, 2)).masked_fill(~visible(r, ks, window)[None], -math.inf)
            out[n][:, a:a + len(r)] = torch.exp(torch.logsumexp(s, dim=-1) - lse)
    return out


def visible(rows, keys, window):
    ok = keys[None, :] <= rows[:, None]
    if window is not None:
        ok &= (rows[:, None] - keys[None, :]) < window
    return ok


class Capture:
    """Collects, per layer: the masses at the answer position [set, head] and the per-sentence
    means [set, sentence, head]."""

    def __init__(self, rows, sets, sentence, n_sentences, layers, heads, q_chunk=Q_CHUNK, k_chunk=K_CHUNK):
        import torch
        dev = rows.device
        self.rows, self.sets, self.q_chunk, self.k_chunk = rows, sets, q_chunk, k_chunk
        self.sentence = sentence                                          # per row: sentence index, or -1
        self.in_sentence = sentence >= 0
        self.count = torch.zeros(n_sentences, device=dev).index_add_(
            0, sentence[self.in_sentence], torch.ones(int(self.in_sentence.sum()), device=dev)).clamp_(min=1)
        self.answer = torch.zeros(len(SETS), layers, heads)
        self.sentences = torch.zeros(len(SETS), n_sentences, layers, heads)
        self.n = n_sentences

    def layer(self, idx, query, key, scaling, window):
        import torch
        m = span_mass(query[0], key[0], self.rows, self.sets, scaling, window, self.q_chunk, self.k_chunk)
        for s, name in enumerate(SETS):
            self.answer[s, idx] = m[name][:, -1].cpu()
            if self.n:
                sums = torch.zeros(m[name].shape[0], self.n, device=m[name].device).index_add_(
                    1, self.sentence[self.in_sentence], m[name][:, self.in_sentence])
                self.sentences[s, :, idx] = (sums / self.count).T.cpu()


_ACTIVE, _BASE = [], ["sdpa"]


def _attention(module, query, key, value, attention_mask, **kw):
    if _ACTIVE:
        _ACTIVE[-1].layer(module.layer_idx, query, key, kw["scaling"], kw.get("sliding_window"))
    from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS
    from transformers.models.olmo3.modeling_olmo3 import eager_attention_forward
    base = eager_attention_forward if _BASE[0] == "eager" else ALL_ATTENTION_FUNCTIONS[_BASE[0]]
    return base(module, query, key, value, attention_mask, **kw)


def install(model, base="sdpa"):
    """Route the model's attention through the capture (inactive until a Capture is pushed)."""
    from transformers import AttentionInterface
    from transformers.masking_utils import ALL_MASK_ATTENTION_FUNCTIONS, AttentionMaskInterface
    AttentionInterface.register(CAPTURE, _attention)
    AttentionMaskInterface.register(CAPTURE, ALL_MASK_ATTENTION_FUNCTIONS[base])
    _BASE[0] = base
    model.set_attn_implementation(CAPTURE)
    return model


# ---------------------------------------------------------------- one run
def measure(model, tok, rec, item, ends, q_chunk=Q_CHUNK, k_chunk=K_CHUNK):
    """The masses for one run (prompt + whole reasoning + the forced answer); item: its question."""
    import torch
    lay = hs.layout(tok, rec, rec["reasoning_text"], item["question"])
    dev = next(model.parameters()).device
    p0 = len(rec["rendered_prompt"])
    first = lay["reasoning"][0] if lay["reasoning"] else lay["answer"]
    rows = torch.arange(first, len(lay["ids"]), device=dev)
    sent = torch.full((len(rows),), -1, dtype=torch.long)
    if lay["reasoning"]:
        sent[torch.tensor(lay["reasoning"]) - first] = torch.tensor(
            hs.sentence_of_token(lay["offsets"], lay["reasoning"], p0, ends)).clamp(max=len(ends) - 1)
    sets = {n: torch.tensor(lay[n], device=dev) for n in SETS}
    cfg = model.config
    cap = Capture(rows, sets, sent.to(dev), len(ends), cfg.num_hidden_layers, cfg.num_attention_heads, q_chunk, k_chunk)
    _ACTIVE.append(cap)
    try:
        with torch.no_grad():
            logits = model(input_ids=torch.tensor([lay["ids"]], device=dev), logits_to_keep=1).logits[0, -1].float()
    finally:
        _ACTIVE.pop()
    n_opt = len(item["options"])
    letter_ids = [tok(L, add_special_tokens=False)["input_ids"][0] for L in FORCE_LETTERS[:n_opt]]
    probs = torch.softmax(logits, -1)[letter_ids].tolist()
    window = getattr(cfg, "sliding_window", None)
    return {"answer": cap.answer.numpy(), "sentences": cap.sentences.half().numpy(), "layout": lay,
            "prompt_tokens": sum(1 for a, _ in lay["offsets"] if a < p0),
            "forced_probs": dict(zip(FORCE_LETTERS, probs)), "forced_top": FORCE_LETTERS[max(range(n_opt), key=probs.__getitem__)],
            "answer_sees_hint_in_sliding_layers": window is None or lay["answer"] - lay["hint"][-1] < window}


# ---------------------------------------------------------------- inputs
def channel(rec):
    from finetune.look import takeover as tk
    return {(c, a): lbl for c, a, lbl in tk.GROUPS}[(rec["condition"], rec.get("arm"))]


def inputs(runs_from=None):
    """(hinted answered Step 2b runs, {question_id: item}, {run_id: Step 3 row})."""
    from finetune import base_format as bf
    from finetune.look import takeover as tk
    if runs_from is None:
        kit.check_inputs("step9")
    rows = bf.current(load(runs_from or bf.OUT))
    runs, _ = tk.runs_to_probe(rows)
    hinted = [r for r in runs if r["condition"] != "none"]
    step3 = {}
    for r in load(tk.RUNS_OUT):
        step3[r["source_run_id"]] = r
    return hinted, {it["question_id"]: it for it in bf.questions()}, step3


def run_meta(rec, res, step3, snap_commit, items):
    from finetune.look import takeover as tk
    lay, s3 = res["layout"], step3.get(rec["run_id"]) or {}
    it = items[rec["item_id"]]
    return {"run_id": rec["run_id"], "item_id": rec["item_id"], "condition": rec["condition"], "arm": rec.get("arm"),
            "channel": channel(rec), "kind": tk.kind(rec), "hint_letter": rec["cue_letter"],
            "final_letter": rec["parsed_letter"], "correct_letter": it["answer"], "tokens": len(lay["ids"]),
            "prompt_tokens": res["prompt_tokens"],
            "reasoning_tokens": len(lay["reasoning"]), "n_sentences": int(res["sentences"].shape[1]),
            "spans": {n: [lay[n][0], lay[n][-1] + 1, len(lay[n])] for n in SETS}, "control_text": lay["control_text"],
            "control_in_stem": lay["control_text"] in it["question"],
            "hint_occurrences": lay["hint_occurrences"],
            "answer_sees_hint_in_sliding_layers": res["answer_sees_hint_in_sliding_layers"],
            "forced_top": res["forced_top"], "forced_probs": res["forced_probs"],
            "step3_takeover_k": s3.get("takeover_k"), "step3_type": s3.get("takeover_type"),
            "snapshot_commit": snap_commit}


# ---------------------------------------------------------------- run
def tokens_of(tok, rec):
    return len(tok(rec["rendered_prompt"] + rec["reasoning_text"] + hs.FORCE, add_special_tokens=False)["input_ids"])


def estimate(lengths, layers=32, full=8, window=4096, d=4096):
    fwd = sum(lengths) / TOK_PER_S
    masses = sum(full * L * L / 2 * 2 * d + (layers - full) * L * min(L, window) * 2 * d for L in lengths) / FP32_FLOPS
    return fwd + masses


def run(model=None, device="auto", out=None, dry_run=False, limit=None, runs_from=None, q_chunk=Q_CHUNK,
        k_chunk=K_CHUNK, base="sdpa"):
    import numpy as np
    from finetune.look import takeover as tk
    path, commit = kit.snapshot(model)
    snap = kit.describe_snapshot(path, commit)
    print(kit.snapshot_line(snap))
    hinted, items, step3 = inputs(runs_from)
    tok = kit.load_tokenizer(path)
    lengths = {r["run_id"]: tokens_of(tok, r) for r in hinted}
    hinted.sort(key=lambda r: (lengths[r["run_id"]], r["run_id"]))
    if limit:
        hinted = hinted[:limit]
    L = [lengths[r["run_id"]] for r in hinted]
    print(f"{len(hinted)} runs: " + ", ".join(f"{g} {k}: {n}" for (g, k), n in
                                              sorted(Counter((channel(r), tk.kind(r)) for r in hinted).items())))
    print(f"tokens per run: median {statistics.median(L):,.0f}, max {max(L):,}, total {sum(L):,}")
    dev = kit.pick_device(device)
    from transformers import AutoConfig
    cfg = AutoConfig.from_pretrained(path, local_files_only=True)
    longest = max(L)
    act = longest * (cfg.intermediate_size * 2 * 3 + cfg.hidden_size * 2 * 6) + longest ** 2 \
        + 2 * longest * cfg.num_attention_heads * 128 * 4 + cfg.num_attention_heads * q_chunk * k_chunk * 4 * 3
    need = kit.model_bytes(path, "bf16") + act + HEADROOM
    est = estimate(L, cfg.num_hidden_layers, len(kit.config_fields(cfg)["full_attention_layers"]),
                   getattr(cfg, "sliding_window", None) or 10 ** 9, cfg.hidden_size)
    print(f"estimated A100 time: ~{est / 60:.0f} min of compute + ~2 min to load")
    if dry_run:
        n, have = kit.check_memory(dev, need, "Step 9")
        print(f"memory: needs ~{n / kit.GiB:.1f} GiB at {longest:,} tokens, {have / kit.GiB:.1f} GiB free on {dev}: ok")
        return None
    kit.check_memory(dev, need, "Step 9")
    d = kit.out_dir("step9", out)
    (d / "runs").mkdir(exist_ok=True)
    done = {p.stem for p in (d / "runs").glob("*.npz")}
    todo = [r for r in hinted if r["run_id"] not in done]
    print(f"{len(hinted) - len(todo)} runs already done; {len(todo)} to go")
    if not todo:
        return d
    model_ = install(kit.load_model(path, "bf16" if dev.type != "cpu" else "fp32", dev, attn=base), base)
    t, seen = kit.Timer(), 0
    for i, rec in enumerate(todo, 1):
        res = measure(model_, tok, rec, items[rec["item_id"]], tk.sentence_ends(rec["reasoning_text"]), q_chunk, k_chunk)
        meta = run_meta(rec, res, step3, commit, items)
        np.savez_compressed(d / "runs" / f"{rec['run_id']}.tmp.npz", answer=res["answer"], sentences=res["sentences"],
                            sentence_end_frac=np.asarray(tk.sentence_ends(rec["reasoning_text"])) / max(1, len(rec["reasoning_text"])),
                            snapshot_commit=np.asarray(commit))
        (d / "runs" / f"{rec['run_id']}.tmp.npz").replace(d / "runs" / f"{rec['run_id']}.npz")
        append(d / "step9_runs.jsonl", meta)
        seen += meta["tokens"]
        left = sum(lengths[r["run_id"]] for r in todo[i:])
        print(f"  {i}/{len(todo)} {rec['run_id']} {meta['channel']}, {meta['kind']}, {meta['tokens']:,} tokens: "
              f"answer -> hint {res['answer'][0].mean():.4f}, control {res['answer'][2].mean():.4f}; forced "
              f"{res['forced_top']} (final {rec['parsed_letter']}); {t() / 60:.1f} min, ~{t() / seen * left / 60:.0f} min left",
              flush=True)
    return d


# ---------------------------------------------------------------- report
def saved(d):
    import numpy as np
    meta = {}
    for m in load(d / "step9_runs.jsonl"):
        meta[m["run_id"]] = m
    out = []
    for rid, m in sorted(meta.items()):
        f = d / "runs" / f"{rid}.npz"
        if f.exists():
            z = np.load(f)
            out.append({**m, "answer": z["answer"], "sentences": z["sentences"].astype("float32"),
                        "sentence_end_frac": z["sentence_end_frac"]})
    return out


def group_by_q(rs, f):
    g = {}
    for r in rs:
        g.setdefault(r["item_id"], []).append(f(r))
    return g


def diff(a, b, f):
    """a - b, paired over the questions both groups have, with a 95% bootstrap clustered by question;
    no interval when fewer than MIN_QUESTIONS questions are shared ("too few questions")."""
    if not a or not b:
        return None
    return diff_groups(group_by_q(a, f), group_by_q(b, f))


def diff_groups(x, y):
    """diff() on values already grouped by question ({question: [values]})."""
    if not x or not y:
        return None
    shared = set(x) & set(y)
    flat = lambda g: [v for vs in g.values() for v in vs]  # noqa: E731
    out = {"n": [len(flat(x)), len(flat(y))], "questions": [len(x), len(y)], "questions_in_both": len(shared),
           "mean_a": statistics.mean(flat(x)), "mean_b": statistics.mean(flat(y))}
    if not shared:
        return {**out, "difference": None, "note": "no question in both groups"}
    if too_few(x, y):
        point = statistics.mean(v for q in shared for v in x[q]) - statistics.mean(v for q in shared for v in y[q])
        return {**out, "difference": point, "ci95": None, "note": f"too few questions ({len(shared)} in both)"}
    dd = boot_diff(x, y)
    return {**out, "difference": dd[0], "ci95": [dd[1], dd[2]]}


def interval(groups, n=20000):
    """(mean, [low, high] or None, questions): the mean of values grouped by question, with a 95%
    bootstrap clustered by question unless fewer than MIN_QUESTIONS questions."""
    if not groups:
        return None, None, 0
    if too_few(groups):
        return statistics.mean(v for vs in groups.values() for v in vs), None, len(groups)
    m = boot_mean(groups, n=n)
    return m[0], [m[1], m[2]], len(groups)


def fmt_diff(x, digits=".2e"):
    """'+d [low, high] (questions)', or the point with 'too few questions'."""
    if not x or x.get("difference") is None:
        return "—" if not x else f"— ({x.get('note')})"
    q = f"{x['questions_in_both']} questions"
    if x.get("ci95") is None:
        return f"{x['difference']:+{digits}} (too few questions: {x['questions_in_both']})"
    return f"{x['difference']:+{digits}} [{x['ci95'][0]:+{digits}}, {x['ci95'][1]:+{digits}}] ({q})"


def comparison_groups(rs):
    """{name: (runs a, runs b)} for every comparison (a - b)."""
    tool = [r for r in rs if r["condition"] != "user"]
    return {
        "followed - resisted (all channels)": ([r for r in rs if r["kind"] == "followed"], [r for r in rs if r["kind"] == "resisted"]),
        **{f"followed - resisted ({c})": ([r for r in rs if r["channel"] == c and r["kind"] == "followed"],
                                          [r for r in rs if r["channel"] == c and r["kind"] == "resisted"])
           for c in sorted({r["channel"] for r in rs})},
        "tool - user": (tool, [r for r in rs if r["condition"] == "user"]),
        "pasted - inserted (both inserted arms)": ([r for r in rs if r["condition"] == "tool_pasted"],
                                                   [r for r in rs if r["condition"] == "tool_injected"]),
        "inserted - inserted + declared": ([r for r in rs if r["condition"] == "tool_injected" and not r["arm"]],
                                           [r for r in rs if r["condition"] == "tool_injected" and r["arm"]]),
    }


def report(out=None, d=None):
    import numpy as np
    d = Path(d) if d else kit.out_dir("step9", out)
    rs = saved(d)
    if not rs:
        raise SystemExit(f"no saved runs in {d}")
    commits = sorted({r["snapshot_commit"] for r in rs})
    full = [i for i in range(rs[0]["answer"].shape[1]) if all(r["answer"][0, i].sum() > 0 for r in rs)] or None
    pooled = np.mean([r["answer"][0] for r in rs], axis=0)                       # [layer, head], hint mass
    top = np.dstack(np.unravel_index(np.argsort(-pooled, axis=None)[:TOP_HEADS], pooled.shape))[0]
    measures = {
        "hint, all heads": lambda r: float(r["answer"][0].mean()),
        "hint, top heads": lambda r: float(np.mean([r["answer"][0, l, h] for l, h in top])),
        "hint minus control, all heads": lambda r: float(r["answer"][0].mean() - r["answer"][2].mean()),
        "letter, all heads": lambda r: float(r["answer"][1].mean()),
        "hint per token, all heads": lambda r: float(r["answer"][0].mean() / r["spans"]["hint"][2]),
    }
    groups = sorted({(r["channel"], r["kind"]) for r in rs})
    comparisons = comparison_groups(rs)

    def curve(group, s, layers=None):
        """[BINS] mean mass over the reasoning, by relative position (sentence end / reasoning length)."""
        acc = [[] for _ in range(BINS)]
        for r in group:
            x = r["sentences"][s] if layers is None else r["sentences"][s][:, layers]
            per = x.mean(axis=(1, 2))
            for frac, v in zip(r["sentence_end_frac"], per):
                acc[min(BINS - 1, int(frac * BINS))].append(float(v))
        return [statistics.mean(a) if a else None for a in acc]

    maps, curves = {}, {}
    for c, k in groups:
        g = [r for r in rs if r["channel"] == c and r["kind"] == k]
        maps[f"{c} | {k}"] = np.mean([r["answer"] for r in g], axis=0)
        curves[f"{c} | {k}"] = np.array([curve(g, s) for s in range(len(SETS))], dtype=float)
    np.savez_compressed(d / "step9_maps.npz", groups=np.array(list(maps)), maps=np.stack(list(maps.values())),
                        curves=np.stack(list(curves.values())), sets=np.array(SETS), top_heads=top)
    layer_profile = {key: {s: [round(float(x), 5) for x in m[i].mean(axis=1)] for i, s in enumerate(SETS)}
                     for key, m in maps.items()}
    summary = {
        "step": "step9", "snapshot_commits": commits, "runs": len(rs),
        "groups": {f"{c} | {k}": sum(r["channel"] == c and r["kind"] == k for r in rs) for c, k in groups},
        "definitions": {"mass": "exp(logsumexp(scores to the span's visible keys) - logsumexp(scores to every visible key)); "
                                "per head, after the rotary embedding",
                        "answer position": "the last token, '(' of 'Answer: ('",
                        "spans": "hint = the hint's whole text; letter = its letter; control = a question-stem span with "
                                 "as many tokens as the hint", "top heads": f"the {TOP_HEADS} (layer, head) pairs with the "
                                 "highest mean answer -> hint mass over all runs pooled",
                        "sliding layers": "a query sees only the last 4,096 keys: far from the hint these layers give 0"},
        "answer_sees_hint_in_sliding_layers": f"{sum(r['answer_sees_hint_in_sliding_layers'] for r in rs)} of {len(rs)} runs",
        "control_inside_the_stem": f"{sum(r['control_in_stem'] for r in rs)} of {len(rs)} runs (else the stem is shorter "
                                   "than the hint and the control runs on into the options)",
        "layers_where_every_run_sees_the_hint": full,
        "top_heads": [{"layer": int(l), "head": int(h), "mean_hint_mass": float(pooled[l, h]),
                       "followed": float(np.mean([r["answer"][0, l, h] for r in rs if r["kind"] == "followed"] or [np.nan])),
                       "resisted": float(np.mean([r["answer"][0, l, h] for r in rs if r["kind"] == "resisted"] or [np.nan])),
                       "control": float(np.mean([r["answer"][2, l, h] for r in rs]))} for l, h in top],
        "group_means_at_answer": {key: {s: float(m[i].mean()) for i, s in enumerate(SETS)} for key, m in maps.items()},
        "layer_profile_at_answer": layer_profile,
        "comparisons": {name: {m: diff(a, b, f) for m, f in measures.items()} for name, (a, b) in comparisons.items()},
        "curves": {"bins": BINS, "x": "sentence end as a share of the reasoning",
                   "mean_over_layers_and_heads": {key: {s: [None if v != v else round(v, 6) for v in c[i]]
                                                        for i, s in enumerate(SETS)} for key, c in curves.items()}},
        "forced_answer_matches_final": f"{sum(r['forced_top'] == r['final_letter'] for r in rs)} of {len(rs)}",
    }
    p = kit.write_json(d / "step9_attention.json", summary)
    print(f"{len(rs)} runs (snapshot {', '.join(commits)})")
    print("| group | runs | answer -> hint | -> letter | -> control |")
    print("|---|---|---|---|---|")
    for key, m in maps.items():
        print(f"| {key} | {summary['groups'][key]} | {m[0].mean():.4f} | {m[1].mean():.4f} | {m[2].mean():.4f} |")
    print("\nTop heads (answer -> hint, pooled): " + ", ".join(f"L{t['layer']}H{t['head']} {t['mean_hint_mass']:.3f}"
                                                              for t in summary["top_heads"]))
    print("\nDifferences, bootstrap clustered by question (hint, all heads):")
    for name, res in summary["comparisons"].items():
        x = res["hint, all heads"]
        if x and x["difference"] is not None:
            print(f"- {name}: {fmt_diff(x, '.4f')} (n {x['n'][0]} vs {x['n'][1]})")
    print(f"saved {p} (copy back) and {d / 'step9_maps.npz'}")
    return summary


# ---------------------------------------------------------------- the follow-up (Oct 26)
READOUT_LAYERS = (15, 19, 23)     # Step 10: the layers where the hint's information leaves the hint tokens
ALIGN = 15                        # sentences either side of the takeover / closest approach
RISE_WINDOW, RISE_BASE = (-2, 0), (-ALIGN, -6)
CURVE_BOOT = 4000
TAKEOVER_ROWS = CODE / "results" / "summaries" / "trackA" / "takeover_per_run.jsonl"   # tracked: Step 3 per run
ONSET_ROWS = CODE / "results" / "summaries" / "trackA" / "hint_onsets.jsonl"          # tracked: Step 3's lead onsets
REDUCED = "step9_reduced.npz"     # the per-run reductions below, numbers only (a few MB): copy back to rerun on the Mac
KEEP = ("run_id", "item_id", "condition", "arm", "channel", "kind", "n_sentences", "tokens",
        "answer_sees_hint_in_sliding_layers", "step3_takeover_k", "snapshot_commit")


def reduced(d, full):
    """The saved runs, reduced as they load: the answer-position masses [set, layer, head], and per
    reasoning sentence the mean over the full-attention layers and heads [set, sentence], the same
    over the sliding-window layers, and whether every token of the sentence reaches the hint there
    (the next sentence still reaches it; the last sentence: the answer does)."""
    import numpy as np
    meta = {m["run_id"]: m for m in load(d / "step9_runs.jsonl")}
    out = []
    for rid, m in sorted(meta.items()):
        f = d / "runs" / f"{rid}.npz"
        if not f.exists():
            continue
        z = np.load(f)
        sent = z["sentences"].astype("float32")
        sliding = [i for i in range(sent.shape[2]) if i not in full]
        reach = (sent[0][:, sliding] > 0).any(axis=(1, 2)) if sliding else np.ones(sent.shape[1], bool)
        whole = np.append(reach[1:], m["answer_sees_hint_in_sliding_layers"]) if len(reach) else reach
        out.append({**{k: m.get(k) for k in KEEP}, "answer": z["answer"], "n_hint": m["spans"]["hint"][2],
                    "sent_full": sent[:, :, full].mean(axis=(2, 3)),
                    "sent_sliding": sent[:, :, sliding].mean(axis=(2, 3)) if sliding else None,
                    "sentence_reaches_hint_in_sliding": whole})
    return out


def save_reduced(rs, full, path):
    """The reduced runs in one .npz (numbers and ids only): answer masses, per-sentence means, reach."""
    import numpy as np
    np.savez_compressed(path, full=np.asarray(full), meta=np.asarray([json.dumps({k: r[k] for k in KEEP}) for r in rs]),
                        n_hint=np.asarray([r["n_hint"] for r in rs]), answer=np.stack([r["answer"] for r in rs]),
                        n_sentences=np.asarray([r["sent_full"].shape[1] for r in rs]),
                        sent_full=np.concatenate([r["sent_full"] for r in rs], axis=1),
                        sent_sliding=np.concatenate([r["sent_sliding"] for r in rs], axis=1),
                        reach=np.concatenate([r["sentence_reaches_hint_in_sliding"] for r in rs]))
    return path


def load_reduced(path):
    """(reduced runs, full-attention layers) from save_reduced's file."""
    import numpy as np
    z = np.load(path)
    out, at = [], 0
    for i, meta in enumerate(z["meta"]):
        n = int(z["n_sentences"][i])
        out.append({**json.loads(str(meta)), "answer": z["answer"][i], "n_hint": int(z["n_hint"][i]),
                    "sent_full": z["sent_full"][:, at:at + n], "sent_sliding": z["sent_sliding"][:, at:at + n],
                    "sentence_reaches_hint_in_sliding": z["reach"][at:at + n]})
        at += n
    return out, [int(x) for x in z["full"]]


def answer_measures(layers):
    """Per run at the answer position, over `layers` and every head: hint - control (spans of equal
    length), the hint's mass per token, and the letter's (one token)."""
    return {"hint - control": lambda r: float((r["answer"][0, layers] - r["answer"][2, layers]).mean()),
            "hint per token": lambda r: float(r["answer"][0, layers].mean() / r["n_hint"]),
            "letter": lambda r: float(r["answer"][1, layers].mean())}


def top_heads(rs, layers, by="hint", k=TOP_HEADS):
    """The k (layer, head) pairs among `layers` with the highest pooled answer -> hint mass
    (by="hint") or hint - control (by="hint - control")."""
    import numpy as np
    pooled = np.mean([r["answer"][0] - (r["answer"][2] if by == "hint - control" else 0) for r in rs], axis=0)
    masked = np.full_like(pooled, -np.inf)
    masked[layers] = pooled[layers]
    idx = np.argsort(-masked, axis=None)[:k]
    return [(int(l), int(h), float(pooled[l, h])) for l, h in zip(*np.unravel_index(idx, pooled.shape))]


def anchors(rs, rows):
    """{run_id: (anchor sentence index, 0-based)}: the takeover sentence of a followed run (Step 3's
    takeover_k: the hint leads from that probe on, so sentence k is where it takes over), the closest
    approach of a resisted run (the probe after the first fifth where the hint letter peaks), and
    why the others have none."""
    per = {r["source_run_id"]: r for r in rows}
    out, skipped = {}, Counter()
    for r in rs:
        s3 = per.get(r["run_id"])
        if s3 is None:
            skipped["not in Step 3's rows"] += 1
            continue
        if s3["n_sentences"] != r["n_sentences"]:
            skipped["sentence counts differ from Step 3's"] += 1
            continue
        k = s3["takeover_k"] if r["kind"] == "followed" else s3["closest_approach_k"]
        if r["kind"] == "followed" and r.get("step3_takeover_k") not in (None, k):
            skipped["takeover differs from the Step 9 record"] += 1
            continue
        if not k:
            skipped[f"{r['kind']}: " + ("takes over before any reasoning (k = 0)" if k == 0 else "no anchor")] += 1
            continue
        out[r["run_id"]] = k - 1
    return out, dict(skipped)


def aligned(rs, at):
    """Per kind and measure, per offset from the anchor (-ALIGN..ALIGN): the mean over runs with a 95%
    bootstrap clustered by question, and the runs present. Full-attention layers, which always reach
    the hint: hint - control and hint per token; sliding-window layers: hint per token, only for the
    sentences whose every token reaches the hint."""
    offs = list(range(-ALIGN, ALIGN + 1))
    vals = {}
    for r in rs:
        if r["run_id"] not in at:
            continue
        a, sf, ss = at[r["run_id"]], r["sent_full"], r["sent_sliding"]
        for o in offs:
            j = a + o
            if not 0 <= j < sf.shape[1]:
                continue
            got = {"full layers: hint - control": sf[0, j] - sf[2, j], "full layers: hint per token": sf[0, j] / r["n_hint"]}
            if ss is not None and r["sentence_reaches_hint_in_sliding"][j]:
                got["sliding layers, within reach: hint per token"] = ss[0, j] / r["n_hint"]
            for m, v in got.items():
                vals.setdefault((r["kind"], m, o), {}).setdefault(r["item_id"], []).append(float(v))
    out = {}
    for kind in ("followed", "resisted"):
        for m in ("full layers: hint - control", "full layers: hint per token", "sliding layers, within reach: hint per token"):
            pts = []
            for o in offs:
                g = vals.get((kind, m, o))
                mean, ci, nq = interval(g, CURVE_BOOT)
                pts.append({"offset": o, "runs": sum(len(v) for v in (g or {}).values()), "questions": nq, "mean": mean,
                            "ci95": ci})
            out.setdefault(kind, {})[m] = pts
    return out


def rise(rs, at):
    """Per run, full layers, hint - control: the anchor window (the anchor sentence and the 2 before)
    minus the same run's sentences 6-15 before it."""
    out = {}
    for r in rs:
        if r["run_id"] not in at:
            continue
        a, sf = at[r["run_id"]], r["sent_full"]
        x = sf[0] - sf[2]
        win = [x[a + o] for o in range(RISE_WINDOW[0], RISE_WINDOW[1] + 1) if 0 <= a + o < len(x)]
        base = [x[a + o] for o in range(RISE_BASE[0], RISE_BASE[1] + 1) if 0 <= a + o < len(x)]
        if win and base:
            out[r["run_id"]] = float(statistics.mean(win) - statistics.mean(base))
    return out


def onset_anchors(rs, rows):
    """{run_id: [(sentence index, permanent)]}: Step 3's onsets after the first fifth (the hint letter
    becomes the leading letter; permanent = it keeps the lead to the end, the takeover; temporary =
    it loses it again), in runs with a dense curve; and why other runs have none."""
    per = {r["source_run_id"]: r for r in rows}
    out, skipped = {}, Counter()
    for r in rs:
        s3 = per.get(r["run_id"])
        if s3 is None:
            skipped["not in Step 3's rows"] += 1
        elif not s3["dense"]:
            skipped["no dense curve"] += 1
        elif s3["n_sentences"] != r["n_sentences"]:
            skipped["sentence counts differ from Step 3's"] += 1
        else:
            out[r["run_id"]] = [(k - 1, bool(perm)) for k, perm in s3["onsets"]]
    return out, dict(skipped)


ONSET_MEASURES = {"full layers: hint - control": lambda r, j: r["sent_full"][0, j] - r["sent_full"][2, j],
                  "full layers: hint per token": lambda r, j: r["sent_full"][0, j] / r["n_hint"]}


def onset_points(rs, at):
    """One row per onset: the rise in each measure (the onset sentence and the 2 before, minus the
    same run's sentences 6-15 before), and whether it is isolated (no other onset in the 15 before)."""
    by_id = {r["run_id"]: r for r in rs}
    out = []
    for rid, ons in at.items():
        r = by_id[rid]
        n = r["sent_full"].shape[1]
        for a, perm in ons:
            row = {"run_id": rid, "item_id": r["item_id"], "kind": r["kind"], "permanent": perm, "sentence": a,
                   "isolated": not any(a - ALIGN <= b < a for b, _ in ons)}
            for m, f in ONSET_MEASURES.items():
                win = [f(r, a + o) for o in range(RISE_WINDOW[0], RISE_WINDOW[1] + 1) if 0 <= a + o < n]
                base = [f(r, a + o) for o in range(RISE_BASE[0], RISE_BASE[1] + 1) if 0 <= a + o < n]
                row[m] = float(statistics.mean(win) - statistics.mean(base)) if win and base else None
            out.append(row)
    return out


def per_run(rows, key):
    """{question: [each run's mean of key over its rows]}: a run weighs the same however many onsets it has."""
    runs = {}
    for o in rows:
        if o[key] is not None:
            runs.setdefault((o["item_id"], o["run_id"]), []).append(o[key])
    out = {}
    for (q, _), vals in runs.items():
        out.setdefault(q, []).append(statistics.mean(vals))
    return out


def onsets_matched(rs, at):
    """The matched comparison: the attention rise at permanent onsets (the takeovers after the first
    fifth) against temporary ones, both picked the same way; per run, then clustered by question."""
    pts = onset_points(rs, at)
    groups = {"permanent (the takeover)": [o for o in pts if o["permanent"]],
              "temporary": [o for o in pts if not o["permanent"]],
              "temporary, in followed runs": [o for o in pts if not o["permanent"] and o["kind"] == "followed"],
              "temporary, in resisted runs": [o for o in pts if not o["permanent"] and o["kind"] == "resisted"]}
    out = {"groups": {}, "comparisons": {}, "curves": {}}
    for sub, keep in (("all onsets", lambda o: True), ("isolated onsets", lambda o: o["isolated"])):
        g = {name: [o for o in rows if keep(o)] for name, rows in groups.items()}
        out["groups"][sub] = {name: {"onsets": len(rows), "runs": len({o["run_id"] for o in rows}),
                                     "questions": len({o["item_id"] for o in rows}),
                                     **{m: dict(zip(("mean", "ci95", "questions"), interval(per_run(rows, m))))
                                        for m in ONSET_MEASURES}} for name, rows in g.items()}
        perm_followed = [o for o in g["permanent (the takeover)"] if o["kind"] == "followed"]
        out["comparisons"][sub] = {
            m: {"permanent - temporary": diff_groups(per_run(g["permanent (the takeover)"], m), per_run(g["temporary"], m)),
                "permanent - temporary, followed runs only": diff_groups(per_run(perm_followed, m),
                                                                         per_run(g["temporary, in followed runs"], m)),
                "temporary: followed - resisted runs": diff_groups(per_run(g["temporary, in followed runs"], m),
                                                                   per_run(g["temporary, in resisted runs"], m))}
            for m in ONSET_MEASURES}
    by_id = {r["run_id"]: r for r in rs}
    for name in ("permanent (the takeover)", "temporary"):
        out["curves"][name] = {}
        for m, f in ONSET_MEASURES.items():
            line = []
            for o in range(-ALIGN, ALIGN + 1):
                runs = {}
                for p in groups[name]:
                    r = by_id[p["run_id"]]
                    j = p["sentence"] + o
                    if 0 <= j < r["sent_full"].shape[1]:
                        runs.setdefault((r["item_id"], r["run_id"]), []).append(float(f(r, j)))
                g = {}
                for (q, _), vals in runs.items():
                    g.setdefault(q, []).append(statistics.mean(vals))
                mean, ci, nq = interval(g, CURVE_BOOT)
                line.append({"offset": o, "runs": len(runs), "questions": nq, "mean": mean, "ci95": ci})
            out["curves"][name][m] = line
    return out


def followup(out=None, d=None, model=None, takeover_rows=None, onset_rows=None, reduced_from=None):
    """Step 9 read again (Oct 26), from the saved runs: every comparison on the full-attention layers
    only; the runs whose answer sees the hint in the sliding-window layers too, on their own;
    hint - control and per-token mass instead of raw mass; the top heads of the readout layers
    (Step 10: 15, 19, 23) for followed vs resisted runs; attention to the hint from each reasoning
    sentence, aligned on the takeover (followed) or the closest approach (resisted). Numbers only
    -> step9_followup.json (copy back) + step9_aligned.png."""
    import numpy as np
    if reduced_from:                                      # on the Mac, from the copied-back reductions
        rs, full = load_reduced(reduced_from)
        d = Path(reduced_from).parent
    else:
        d = Path(d) if d else kit.out_dir("step9", out)
        full = kit.full_attention_layers(model)
        rs = reduced(d, full)
        if rs:
            save_reduced(rs, full, d / REDUCED)
    if not rs:
        raise SystemExit(f"no saved runs in {d}")
    n_layers = rs[0]["answer"].shape[1]
    every = list(range(n_layers))
    sliding = [i for i in every if i not in full]
    readout = [layer for layer in READOUT_LAYERS if layer in full]
    near = [r for r in rs if r["answer_sees_hint_in_sliding_layers"]]
    run_sets = {"all runs, full-attention layers": (rs, full),
                "answer within reach of the hint in the sliding layers: all layers": (near, every),
                "answer within reach of the hint in the sliding layers: full-attention layers": (near, full),
                "answer within reach of the hint in the sliding layers: sliding-window layers": (near, sliding)}
    sets = {}
    for name, (runs, layers) in run_sets.items():
        if not runs or not layers:
            continue
        ms = answer_measures(layers)
        groups = sorted({(r["channel"], r["kind"]) for r in runs})
        sets[name] = {"runs": len(runs), "questions": len({r["item_id"] for r in runs}), "layers": layers,
                      "group_means": {f"{c} | {k}": {"runs": len(g), "questions": len({r["item_id"] for r in g}),
                                                     **{m: statistics.mean(f(r) for r in g) for m, f in ms.items()}}
                                      for c, k in groups for g in [[r for r in runs if r["channel"] == c and r["kind"] == k]]},
                      "comparisons": {cname: {m: diff(a, b, f) for m, f in ms.items()}
                                      for cname, (a, b) in comparison_groups(runs).items()}}
    by_mass = top_heads(rs, every)
    heads = {"pooled, all runs, ranked by hint mass (as in step9_attention.json)": by_mass,
             "pooled, all runs, ranked by hint - control": top_heads(rs, every, "hint - control")}
    if near:
        heads["runs within reach in the sliding layers, all layers, ranked by hint - control"] = top_heads(near, every, "hint - control")
    head_counts = {name: {"in full-attention layers": sum(l in full for l, _, _ in hs_),
                          "in layers " + ", ".join(map(str, READOUT_LAYERS)): sum(l in readout for l, _, _ in hs_),
                          "of": len(hs_)} for name, hs_ in heads.items()}
    fol, res = [r for r in rs if r["kind"] == "followed"], [r for r in rs if r["kind"] == "resisted"]
    ro = [(l, h) for l, h, _ in by_mass if l in readout]
    readout_heads = {"heads": [[l, h] for l, h in ro], "per head": {}, "mean over these heads": {}}
    for l, h in ro:
        readout_heads["per head"][f"L{l}H{h}"] = {
            "hint": diff(fol, res, lambda r, l=l, h=h: float(r["answer"][0, l, h])),
            "hint - control": diff(fol, res, lambda r, l=l, h=h: float(r["answer"][0, l, h] - r["answer"][2, l, h]))}
    if ro:
        mean_hint = lambda r: float(np.mean([r["answer"][0, l, h] for l, h in ro]))  # noqa: E731
        mean_hc = lambda r: float(np.mean([r["answer"][0, l, h] - r["answer"][2, l, h] for l, h in ro]))  # noqa: E731
        for cname, (a, b) in comparison_groups(rs).items():
            readout_heads["mean over these heads"][cname] = {"hint": diff(a, b, mean_hint), "hint - control": diff(a, b, mean_hc)}
    at, skipped = anchors(rs, list(load(Path(takeover_rows or TAKEOVER_ROWS))))
    onset_at, onset_skipped = onset_anchors(rs, list(load(Path(onset_rows or ONSET_ROWS))))
    rises = rise(rs, at)
    by_q = lambda kind: {r["item_id"]: [] for r in rs if r["kind"] == kind and r["run_id"] in rises}  # noqa: E731
    rise_out = {}
    for kind in ("followed", "resisted"):
        g = by_q(kind)
        for r in rs:
            if r["kind"] == kind and r["run_id"] in rises:
                g[r["item_id"]].append(rises[r["run_id"]])
        mean, ci, nq = interval(g)
        rise_out[kind] = {"runs": sum(map(len, g.values())), "questions": nq, "mean": mean, "ci95": ci}
    rise_out["followed - resisted"] = diff([r for r in fol if r["run_id"] in rises], [r for r in res if r["run_id"] in rises],
                                          lambda r: rises[r["run_id"]])
    summary = {
        "step": "step9_followup", "snapshot_commits": sorted({r["snapshot_commit"] for r in rs}), "runs": len(rs),
        "full_attention_layers": full, "readout_layers": readout,
        "definitions": {
            "hint - control": "mass on the hint minus mass on a question-stem span of the same number of tokens",
            "hint per token": "mass on the hint divided by its number of tokens",
            "within reach": "a sliding-window layer sees only the last 4,096 tokens; the answer is within reach when "
                            "it sees the hint's last token there",
            "anchor": "followed: the takeover sentence (Step 3: the hint letter leads from there to the end); resisted: "
                      "the closest approach (the probe after the first fifth where the hint letter peaks)",
            "rise": f"per run, full layers, hint - control: mean over offsets {RISE_WINDOW[0]}..{RISE_WINDOW[1]} minus mean "
                    f"over offsets {RISE_BASE[0]}..{RISE_BASE[1]}",
            "onset": "a probe after the first fifth where the hint letter becomes the leading letter (Step 3, dense "
                     "curves); permanent = it keeps the lead to the end (the takeover), temporary = it loses it again. "
                     "Picked the same way in followed and resisted runs, unlike the closest approach",
            "intervals": f"95% bootstrap clustered by question; a difference uses the questions both groups have; none "
                         f"under {MIN_QUESTIONS} questions ('too few questions')"},
        "runs_within_reach_in_sliding_layers": len(near),
        "run_sets": sets,
        "top_heads": {name: [{"layer": l, "head": h, "value": v} for l, h, v in hs_] for name, hs_ in heads.items()},
        "top_head_counts": head_counts,
        "readout_heads_followed_vs_resisted": readout_heads,
        "aligned": {"offsets": [-ALIGN, ALIGN], "runs_with_an_anchor": {k: sum(r["kind"] == k and r["run_id"] in at for r in rs)
                                                                       for k in ("followed", "resisted")},
                    "skipped": skipped, "curves": aligned(rs, at), "rise_at_anchor": rise_out,
                    "note": "biased: the closest approach is picked where the hint is strongest; see onsets_matched"},
        "onsets_matched": {"runs": len(onset_at), "skipped": onset_skipped, **onsets_matched(rs, onset_at)},
    }
    p = kit.write_json(d / "step9_followup.json", summary)
    show_followup(summary)
    plot_followup(summary, d)
    plot_onsets(summary, d)
    print(f"saved {p}, {d / 'step9_aligned.png'}, {d / 'step9_onsets.png'} and {d / REDUCED} (copy all back)")
    return summary


def fmt_mean(x):
    if not x or x.get("mean") is None:
        return "—"
    if x.get("ci95") is None:
        return f"{x['mean']:+.2e} (too few questions: {x.get('questions')})"
    return f"{x['mean']:+.2e} [{x['ci95'][0]:+.2e}, {x['ci95'][1]:+.2e}] ({x.get('questions')} questions)"


def show_followup(s):
    fmt = fmt_diff
    for name, st in s["run_sets"].items():
        print(f"\n{name}: {st['runs']} runs, {st['questions']} questions, layers {st['layers']}")
        print("| group | runs | questions | hint - control | hint per token | letter |")
        print("|---|---|---|---|---|---|")
        for g, m in st["group_means"].items():
            print(f"| {g} | {m['runs']} | {m.get('questions', '—')} | {m['hint - control']:.2e} | {m['hint per token']:.2e} | "
                  f"{m['letter']:.2e} |")
        print("| comparison | runs | questions (both) | hint - control | hint per token | letter |")
        print("|---|---|---|---|---|---|")
        for cname, c in st["comparisons"].items():
            x = c["hint - control"]
            n = f"{x['n'][0]} vs {x['n'][1]}" if x else "—"
            q = f"{x['questions'][0]} vs {x['questions'][1]} ({x['questions_in_both']})" if x and "questions" in x else "—"
            print(f"| {cname} | {n} | {q} | {fmt(c['hint - control'])} | {fmt(c['hint per token'])} | {fmt(c['letter'])} |")
    print("\nTop heads:")
    for name, hs_ in s["top_heads"].items():
        c = s["top_head_counts"][name]
        print(f"- {name}: " + ", ".join(f"L{h['layer']}H{h['head']}" for h in hs_) + f"  ({'; '.join(f'{v} {k}' for k, v in c.items() if k != 'of')}, of {c['of']})")
    ro = s["readout_heads_followed_vs_resisted"]
    print(f"\nReadout-layer heads among the top 10 ({len(ro['heads'])}), followed - resisted:")
    for name, c in ro["per head"].items():
        print(f"  {name}: hint {fmt(c['hint'])}; hint - control {fmt(c['hint - control'])}")
    for cname, c in ro["mean over these heads"].items():
        print(f"  mean over them, {cname}: hint {fmt(c['hint'])}; hint - control {fmt(c['hint - control'])}")
    a = s["aligned"]
    print(f"\nAligned on the anchor: {a['runs_with_an_anchor']}; skipped {a['skipped']}")
    for kind in ("followed", "resisted"):
        x = a["rise_at_anchor"][kind]
        if x["mean"] is not None:
            print(f"  rise at the anchor, {kind}: {fmt_mean(x)} ({x['runs']} runs)")
    print(f"  followed - resisted: {fmt(a['rise_at_anchor']['followed - resisted'])}  ({a.get('note', '')})")
    o = s.get("onsets_matched")
    if o:
        print(f"\nMatched: the rise at every onset after the first fifth ({o['runs']} runs with a dense curve; skipped "
              f"{o['skipped']}); per run, then clustered by question")
        for sub, groups in o["groups"].items():
            print(f"\n{sub}:")
            print("| onset | onsets | runs | questions | rise, hint - control | rise, hint per token |")
            print("|---|---|---|---|---|---|")
            for name, g in groups.items():
                print(f"| {name} | {g['onsets']} | {g['runs']} | {g['questions']} | "
                      f"{fmt_mean(g['full layers: hint - control'])} | {fmt_mean(g['full layers: hint per token'])} |")
            for m, cs in o["comparisons"][sub].items():
                for cname, x in cs.items():
                    print(f"  {m}, {cname}: {fmt(x)}")


def plot_followup(s, d):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = {"followed": "#2a78d6", "resisted": "#eb6834"}
    panels = ["full layers: hint - control", "full layers: hint per token", "sliding layers, within reach: hint per token"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, m in zip(axes, panels):
        for kind in ("followed", "resisted"):
            pts = [p for p in s["aligned"]["curves"][kind][m] if p["mean"] is not None]
            if not pts:
                continue
            x = [p["offset"] for p in pts]
            ax.plot(x, [p["mean"] for p in pts], color=colors[kind], lw=2,
                    label=f"{kind} ({s['aligned']['runs_with_an_anchor'][kind]} runs)")
            band = [p for p in pts if p["ci95"]]
            ax.fill_between([p["offset"] for p in band], [p["ci95"][0] for p in band], [p["ci95"][1] for p in band],
                            color=colors[kind], alpha=0.15, lw=0)
        ax.axvline(0, color="#52514e", lw=0.8)
        ax.axhline(0, color="#b5b4ad", lw=0.6)
        ax.set_title(m, fontsize=10)
        ax.set_xlabel("sentences from the anchor (0 = takeover / closest approach)")
        ax.grid(axis="y", color="#e5e4df", lw=0.5)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[0].set_ylabel("attention mass from the sentence")
    if axes[0].lines[2:]:
        axes[0].legend(frameon=False)
    fig.suptitle("Attention to the hint from each reasoning sentence, aligned on the takeover (followed) or the "
                 "closest approach (resisted); 95% intervals clustered by question", fontsize=10)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(Path(d) / f"step9_aligned.{ext}", dpi=150)
    plt.close(fig)


def plot_onsets(s, d):
    """The matched figure: attention to the hint around permanent vs temporary onsets."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    o = s.get("onsets_matched")
    if not o or not o["curves"]:
        return
    colors = {"permanent (the takeover)": "#2a78d6", "temporary": "#eb6834"}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, m in zip(axes, ONSET_MEASURES):
        for name, c in o["curves"].items():
            pts = [p for p in c[m] if p["mean"] is not None]
            if not pts:
                continue
            g = o["groups"]["all onsets"][name]
            ax.plot([p["offset"] for p in pts], [p["mean"] for p in pts], color=colors[name], lw=2,
                    label=f"{name}: {g['onsets']} onsets, {g['runs']} runs, {g['questions']} questions")
            band = [p for p in pts if p["ci95"]]
            ax.fill_between([p["offset"] for p in band], [p["ci95"][0] for p in band], [p["ci95"][1] for p in band],
                            color=colors[name], alpha=0.15, lw=0)
        ax.axvline(0, color="#52514e", lw=0.8)
        ax.axhline(0, color="#b5b4ad", lw=0.6)
        ax.set_title(m, fontsize=10)
        ax.set_xlabel("sentences from the onset (0 = the hint letter takes the lead)")
        ax.grid(axis="y", color="#e5e4df", lw=0.5)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[0].set_ylabel("attention mass from the sentence")
    axes[0].legend(frameon=False, fontsize=8)
    fig.suptitle("Attention to the hint around every lead onset after the first fifth: kept (the takeover) vs lost "
                 "again; per run, 95% intervals clustered by question", fontsize=10)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(Path(d) / f"step9_onsets.{ext}", dpi=150)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true", help="summary from the saved runs; no model")
    ap.add_argument("--followup", action="store_true", help="the Oct 26 follow-up from the saved runs; no model, no GPU")
    ap.add_argument("--plot-followup", metavar="SUMMARY", help="redraw the aligned-curve figure from a step9_followup.json")
    ap.add_argument("--from-reduced", metavar="NPZ", help="with --followup: from a copied-back step9_reduced.npz (Mac)")
    ap.add_argument("--limit", type=int, help="only the N shortest runs")
    ap.add_argument("--model", help="a local model directory (a trained version, or a test's tiny model)")
    ap.add_argument("--runs-from", help="a base_format-style .jsonl.gz of runs (default: Step 2b's)")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--q-chunk", type=int, default=Q_CHUNK)
    ap.add_argument("--k-chunk", type=int, default=K_CHUNK)
    ap.add_argument("--out", help="output base directory (default $TRACKA_OUT)")
    a = ap.parse_args(argv)
    if a.plot_followup:
        summary = json.loads(Path(a.plot_followup).read_text())
        plot_onsets(summary, Path(a.plot_followup).parent)
        return plot_followup(summary, Path(a.plot_followup).parent)
    if a.followup:
        return followup(a.out, model=a.model, reduced_from=a.from_reduced)
    if a.report:
        return report(a.out)
    d = run(a.model, a.device, a.out, a.dry_run, a.limit, a.runs_from, a.q_chunk, a.k_chunk)
    if d and not a.limit:
        return report(d=d)
    return d


if __name__ == "__main__":
    main()
