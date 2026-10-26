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

from common import append, boot_diff, load  # noqa: E402
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
    if not a or not b:
        return None
    x, y = group_by_q(a, f), group_by_q(b, f)
    if not set(x) & set(y):
        return {"n": [len(a), len(b)], "mean_a": statistics.mean(f(r) for r in a), "mean_b": statistics.mean(f(r) for r in b),
                "difference": None, "note": "no question in both groups"}
    dd = boot_diff(x, y)
    return {"n": [len(a), len(b)], "questions_in_both": len(set(x) & set(y)), "mean_a": statistics.mean(f(r) for r in a),
            "mean_b": statistics.mean(f(r) for r in b), "difference": dd[0], "ci95": [dd[1], dd[2]]}


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
    tool = [r for r in rs if r["condition"] != "user"]
    comparisons = {
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
            print(f"- {name}: {x['difference']:+.4f} [{x['ci95'][0]:+.4f}, {x['ci95'][1]:+.4f}] (n {x['n'][0]} vs {x['n'][1]})")
    print(f"saved {p} (copy back) and {d / 'step9_maps.npz'}")
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true", help="summary from the saved runs; no model")
    ap.add_argument("--limit", type=int, help="only the N shortest runs")
    ap.add_argument("--model", help="a local model directory (a trained version, or a test's tiny model)")
    ap.add_argument("--runs-from", help="a base_format-style .jsonl.gz of runs (default: Step 2b's)")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--q-chunk", type=int, default=Q_CHUNK)
    ap.add_argument("--k-chunk", type=int, default=K_CHUNK)
    ap.add_argument("--out", help="output base directory (default $TRACKA_OUT)")
    a = ap.parse_args(argv)
    if a.report:
        return report(a.out)
    d = run(a.model, a.device, a.out, a.dry_run, a.limit, a.runs_from, a.q_chunk, a.k_chunk)
    if d and not a.limit:
        return report(d=d)
    return d


if __name__ == "__main__":
    main()
