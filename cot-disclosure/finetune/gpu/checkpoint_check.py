"""Track A, step 8: is Voyager's olmo3-7b-think the checkpoint we load on the GPU?

A local forward pass over the saved texts whose per-token log-probabilities Voyager returned by
echo, compared token by token with the two-part rule (docs/PLAN.md, Track A; set Oct 21-22):
  strict, the first 2,047 tokens   the same top token at every position, and max |difference| < 0.01
  beyond them                      Voyager seems to process long prompts in 2,048-token chunks
                                   (likely, not confirmed), so: the mean, median and max |difference|,
                                   and top-token mismatches counted only where they are not
                                   near-ties. A mismatch outside a near-tie fails.
The difference is in each prompt token's log-probability, local minus Voyager's. A near-tie: at a
mismatch, the local model gives its own top token and Voyager's top token probabilities within 0.1
of each other (and so does Voyager, when its saved top tokens include both: the echo kept the
top-1 token plus the prompt's own, logprobs: 1). If the check fails, Voyager isn't serving this
checkpoint, and every base number must be re-measured on the GPU.

References, all saved on the Mac (no API calls here):
  step1_old_route        Step 1 call 8, olmo3-7b-think before the Oct 21 ID change (5,185 tokens)
  oct21_low/medium/high  the same text through olmo3-7b at reasoning_effort low / medium / high
  canary                 the identity canary's text and reference (530 tokens)
  oct21_default          negative control: the same text at the default effort, which serves the
                         Instruct checkpoint. It must fail, or the check can't tell checkpoints apart.
The rule is applied to the bf16 pass (the dtype every GPU step uses). An fp32 pass, the same
weights upcast, is reported beside it, to tell numerics from a different checkpoint.

  python finetune/gpu/checkpoint_check.py --dry-run   # references, tokens, alignment, memory; no model
  python finetune/gpu/checkpoint_check.py             # -> $TRACKA_OUT/step8/: step8_checkpoint.json (the
                                                      #    summary to copy back) + step8_positions.npz
On Sol: finetune/gpu/sol/run.sh step8 (session) or finetune/gpu/sol/submit.sh step8 (batch).
"""
import argparse
import json
import math
import statistics
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import load  # noqa: E402
from finetune.gpu import kit  # noqa: E402

CAPS = CODE / "results" / "trackA" / "voyager_capabilities.jsonl.gz"
IDS = CODE / "results" / "trackA" / "voyager_ids_check.jsonl.gz"
CANARY = CODE / "configs" / "canary" / "olmo3-7b-think.json"
STRICT_N = 2047          # tokens 0..2046; token 0 has no log-prob
TOL = 0.01
NEAR_TIE = 0.1
CHUNK = 1024             # positions per output-layer chunk (the full 5,185 x 100,278 table is 2 GB in fp32)
HEADROOM = 4 * kit.GiB


# ---------------------------------------------------------------- references
def references():
    """[{name, text, logprobs (Voyager's echo entries), source, control}]."""
    step1 = next(r for r in load(CAPS) if r["arm"] == "completions_echo_served_template")
    text = step1["rendered_prompt"]
    refs = [{"name": "step1_old_route", "text": text, "logprobs": step1["logprobs"], "control": False,
             "source": f"Step 1 call 8, olmo3-7b-think, {step1['timestamp_utc']}"}]
    for r in load(IDS):
        if r["check"] == "echo_identity":
            refs.append({"name": f"oct21_{r['reasoning_effort']}", "text": text, "logprobs": r["logprobs"],
                         "control": False, "source": f"olmo3-7b at reasoning_effort {r['reasoning_effort']}, "
                                                     f"served {r['served_model']}, {r['timestamp_utc']}"})
    canary = json.loads(CANARY.read_text())
    refs.append({"name": "canary", "text": canary["text"], "logprobs": canary["logprobs"], "control": False,
                 "source": f"identity canary reference, {canary['served_model']}, {canary['created_utc']}"})
    for r in load(IDS):
        if r["check"] == "echo_default":
            refs.append({"name": "oct21_default", "text": text, "logprobs": r["logprobs"], "control": True,
                         "source": f"olmo3-7b at the default effort, served {r['served_model']} (negative control)"})
    return refs


def align(tok, text, echo):
    """Local token ids of `text` and, per local position, the echo entry for the same token at the
    same character offset (None where the two tokenizations differ). The echo's last entry may be
    the one generated token; it is never matched past the text."""
    ids = tok(text, add_special_tokens=False)["input_ids"]
    strings = [tok.decode([t]) for t in ids]
    by_offset, pos = {}, 0
    for e in echo:
        by_offset[pos] = e
        pos += len(e["token"] or "")
    out, pos = [], 0
    for s in strings:
        e = by_offset.get(pos)
        out.append(e if e is not None and e["token"] == s else None)
        pos += len(s)
    return ids, strings, out


def voyager_top(entry):
    tops = (entry or {}).get("top_logprobs") or {}
    return max(tops.items(), key=lambda kv: kv[1]) if tops else (None, None)


# ---------------------------------------------------------------- the local pass
def local_logprobs(model, ids, want, chunk=CHUNK):
    """Per position i >= 1 (token i given the tokens before it): its log-prob, the top two tokens
    and their log-probs, and the best log-prob among the ids in want[i] (Voyager's top token)."""
    import torch
    dev = next(model.parameters()).device
    x = torch.tensor([ids], device=dev)
    out = {k: [None] for k in ("lp", "top1", "top1_lp", "top2", "top2_lp", "want_lp")}
    with torch.no_grad():
        h = model.model(input_ids=x).last_hidden_state[0]
        head = model.get_output_embeddings()
        for a in range(0, len(ids) - 1, chunk):
            b = min(a + chunk, len(ids) - 1)
            logp = torch.log_softmax(head(h[a:b]).float(), dim=-1)          # rows predict tokens a+1 .. b
            out["lp"] += logp.gather(1, x[0, a + 1:b + 1, None])[:, 0].tolist()
            v, i = logp.topk(2, dim=-1)
            out["top1"] += i[:, 0].tolist()
            out["top1_lp"] += v[:, 0].tolist()
            out["top2"] += i[:, 1].tolist()
            out["top2_lp"] += v[:, 1].tolist()
            for j in range(a, b):
                w = want[j + 1]
                out["want_lp"].append(max(logp[j - a, w].tolist()) if w else None)
    return out


# ---------------------------------------------------------------- the rule
def compare(strings, entries, local, dec, strict_n=STRICT_N, tol=TOL, near=NEAR_TIE):
    """The two-part rule for one reference. entries: the aligned echo entry per local position;
    local: local_logprobs(); dec: a Decoder (token id -> text, as Voyager names tokens)."""
    rows = []
    for i in range(1, len(strings)):
        e = entries[i]
        if e is None or e.get("logprob") is None:
            continue
        v_top, _ = voyager_top(e)
        l_top = dec.decode(local["top1"][i])
        row = {"pos": i, "token": strings[i], "voyager_lp": e["logprob"], "local_lp": local["lp"][i],
               "diff": abs(local["lp"][i] - e["logprob"]), "voyager_top": v_top, "local_top": l_top,
               "mismatch": v_top != l_top}
        if row["mismatch"]:
            p_local_top = math.exp(local["top1_lp"][i])
            p_local_voy = math.exp(local["want_lp"][i]) if local["want_lp"][i] is not None else 0.0
            tops = e.get("top_logprobs") or {}
            gap_v = (math.exp(tops[v_top]) - math.exp(tops[l_top])) if l_top in tops else None
            row.update({"gap_local": p_local_top - p_local_voy, "gap_voyager": gap_v,
                        "near_tie": p_local_top - p_local_voy < near and (gap_v is None or gap_v < near)})
        rows.append(row)
    strict = [r for r in rows if r["pos"] < strict_n]
    beyond = [r for r in rows if r["pos"] >= strict_n]

    def stats(rs):
        d = [r["diff"] for r in rs]
        return {"positions": len(rs), "mean_abs_diff": statistics.mean(d) if d else None,
                "median_abs_diff": statistics.median(d) if d else None, "max_abs_diff": max(d) if d else None,
                "top_token_mismatches": sum(r["mismatch"] for r in rs)}
    s = stats(strict)
    s["pass"] = s["top_token_mismatches"] == 0 and (s["max_abs_diff"] or 0.0) < tol
    s["worst"] = sorted(strict, key=lambda r: -r["diff"])[:5]
    s["mismatches"] = [r for r in strict if r["mismatch"]][:20]
    b = stats(beyond)
    outside = [r for r in beyond if r["mismatch"] and not r["near_tie"]]
    b.update({"near_ties": b["top_token_mismatches"] - len(outside), "mismatches_outside_near_ties": len(outside),
              "pass": not outside, "outside_examples": outside[:20], "worst": sorted(beyond, key=lambda r: -r["diff"])[:5]})
    unaligned = sum(1 for i in range(1, len(strings)) if entries[i] is None)
    return {"strict": s, "beyond": b, "unaligned_positions": unaligned, "pass_logprobs": s["pass"] and b["pass"],
            "pass": s["pass"] and b["pass"] and not unaligned,
            "diffs": [r["diff"] for r in rows], "positions": [r["pos"] for r in rows],
            "mismatch": [r["mismatch"] for r in rows]}


class Decoder:
    """Token id <-> text for the comparison (Voyager names tokens by their text)."""

    def __init__(self, tok):
        self.tok, self._index, self._cache = tok, None, {}

    def decode(self, i):
        if i not in self._cache:
            self._cache[i] = self.tok.decode([i])
        return self._cache[i]

    def ids(self, text):
        """Token ids whose text is `text` (usually one)."""
        if self._index is None:
            self._index = {}
            for i in range(len(self.tok)):
                self._index.setdefault(self.decode(i), []).append(i)
        return self._index.get(text, [])


# ---------------------------------------------------------------- run
def check(model, tok, refs, dtype, strict_n=STRICT_N):
    """{reference name: compare() result} for one loaded model."""
    dec = Decoder(tok)
    out = {}
    for ref in refs:
        ids, strings, entries = align(tok, ref["text"], ref["logprobs"])
        want = [None] + [dec.ids(voyager_top(e)[0]) if e else None for e in entries[1:]]
        res = compare(strings, entries, local_logprobs(model, ids, want), dec, strict_n)
        res.update({"name": ref["name"], "source": ref["source"], "control": ref["control"], "tokens": len(ids),
                    "dtype": dtype})
        out[ref["name"]] = res
    return out


def verdict(results):
    """bf16 decides; fp32 is shown beside it."""
    lines, ok = [], {}
    for dtype, res in results.items():
        think = [r for r in res.values() if not r["control"]]
        ctrl = [r for r in res.values() if r["control"]]
        ok[dtype] = all(r["pass"] for r in think)
        ctrl_failed = all(not r["pass_logprobs"] for r in ctrl)          # on its log-probs, not on tokenization
        lines.append(f"{dtype}: {'PASS' if ok[dtype] else 'FAIL'} on {sum(r['pass'] for r in think)} of {len(think)} "
                     f"Think references; the Instruct control {'fails, as it must' if ctrl_failed else 'PASSES: the check cannot tell checkpoints apart'}")
    main = "bf16" if "bf16" in results else next(iter(results))
    return {"pass": ok[main], "decided_by": main, "by_dtype": ok, "lines": lines,
            "meaning": ("Voyager serves this checkpoint: base numbers from Voyager stand" if ok[main] else
                        "Voyager isn't serving this checkpoint (or the local pass differs): re-measure every base "
                        "number on the GPU, after looking at where it fails")}


def table(results):
    print("| reference | dtype | tokens | strict: mismatches, max diff | beyond: mean / median / max diff | "
          "beyond: mismatches (near-ties) | pass |")
    print("|---|---|---|---|---|---|---|")
    for dtype, res in results.items():
        for r in res.values():
            s, b = r["strict"], r["beyond"]
            fmt = lambda x: "—" if x is None else f"{x:.4f}"  # noqa: E731
            print(f"| {r['name']}{' (control)' if r['control'] else ''} | {dtype} | {r['tokens']:,} | "
                  f"{s['top_token_mismatches']}, {fmt(s['max_abs_diff'])} | {fmt(b['mean_abs_diff'])} / "
                  f"{fmt(b['median_abs_diff'])} / {fmt(b['max_abs_diff'])} | {b['top_token_mismatches']} "
                  f"({b['near_ties']}) | {'yes' if r['pass'] else 'NO'} |")


def run(model=None, device="auto", dtypes=("bf16", "fp32"), out=None, dry_run=False, strict_n=STRICT_N, refs=None):
    import numpy as np
    from transformers import AutoConfig
    path, commit = kit.snapshot(model)
    snap = kit.describe_snapshot(path, commit)
    print(kit.snapshot_line(snap))
    if refs is None:
        kit.check_inputs("step8")
        refs = references()
    tok = kit.load_tokenizer(path)
    for ref in refs:
        ids, _, entries = align(tok, ref["text"], ref["logprobs"])
        print(f"{ref['name']:16} {len(ids):5,} tokens, {sum(e is None for e in entries[1:])} not aligned with the echo; "
              f"{ref['source']}")
    dev = kit.pick_device(device)
    longest = max(len(r["text"]) for r in refs) // 3
    act = CHUNK * AutoConfig.from_pretrained(path, local_files_only=True).vocab_size * 8 + longest * 64 * 1024
    need = kit.model_bytes(path, "fp32" if "fp32" in dtypes else dtypes[0]) + act + HEADROOM
    if dry_run:
        n, have = kit.check_memory(dev, need, f"Step 8 ({', '.join(dtypes)})")
        print(f"memory: needs ~{n / kit.GiB:.1f} GiB, {have / kit.GiB:.1f} GiB free on {dev}: ok")
        return None
    kit.check_memory(dev, need, f"Step 8 ({', '.join(dtypes)})")
    import torch
    first = "fp32" if "fp32" in dtypes else dtypes[0]           # load once; bf16 weights upcast to fp32 exactly
    t = kit.Timer()
    m = kit.load_model(path, first, dev)
    load_s = t()
    results = {}
    for dtype in sorted(dtypes, key=lambda d: d != first):
        if dtype != first:
            m = m.to(kit.torch_dtype(dtype))
        t = kit.Timer()
        results[dtype] = check(m, tok, refs, dtype, strict_n)
        print(f"{dtype}: {t():.0f} s")
    v = verdict(results)
    table(results)
    print("\n".join(v["lines"]) + f"\nverdict: {'PASS' if v['pass'] else 'FAIL'} ({v['decided_by']}): {v['meaning']}")
    d = kit.out_dir("step8", out)
    np.savez_compressed(d / "step8_positions.npz", **{f"{dt}__{name}__{k}": np.asarray(r[k]) for dt, res in results.items()
                                                       for name, r in res.items() for k in ("positions", "diffs", "mismatch")})
    summary = {**kit.header("step8", snap), "rule": {"strict_first_tokens": strict_n, "max_abs_diff": TOL,
                                                     "near_tie_probability_gap": NEAR_TIE,
                                                     "applied_to": "bf16; fp32 shown beside it"},
               "device": str(dev), "load_s": load_s, "verdict": v,
               "results": {dt: {name: {k: x for k, x in r.items() if k not in ("diffs", "positions", "mismatch")}
                                for name, r in res.items()} for dt, res in results.items()},
               "for_scale": "Oct 21, Voyager old vs new route on the Step 1 text: strict part max 0.0003; beyond: mean "
                            "0.006, max 0.19, 24 mismatches, all near-ties. Instruct vs Think: 654 mismatches, mean 0.32, "
                            "max 20.7 (docs/OVERVIEW.md §5)",
               "peak_gib": round(torch.cuda.max_memory_allocated() / kit.GiB, 2) if dev.type == "cuda" else None}
    p = kit.write_json(d / "step8_checkpoint.json", summary)
    print(f"saved {p} (copy back) and {d / 'step8_positions.npz'}")
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="references, alignment and memory check; no model")
    ap.add_argument("--model", help="a local model directory instead of the cached Olmo 3 7B Think (tests)")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--dtypes", default="bf16,fp32", help="comma-separated; the rule is applied to bf16")
    ap.add_argument("--out", help="output base directory (default $TRACKA_OUT)")
    a = ap.parse_args(argv)
    dtypes = tuple(x for x in a.dtypes.split(",") if x)
    if set(dtypes) - set(kit.DTYPES):
        raise SystemExit(f"unknown dtype in {dtypes}")
    return run(a.model, a.device, dtypes, a.out, a.dry_run)


if __name__ == "__main__":
    main()
