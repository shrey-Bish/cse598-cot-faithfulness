"""Track A, step 10: activation patching. Which layers carry the hint's influence on the answer?

Cases: Step 4's. These are the late-takeover runs on sure questions from Step 3
(results/trackA/takeover_cases.jsonl), at most 3 per question, chosen by seed
(finetune/look/deletion.choose): 21 runs, all tool hints. Two cut points per run, each followed
by "</think>\\n\\nAnswer: (":
  (i)   the reasoning just before its first mention of the hint (Step 4's mention words)
  (ii)  the reasoning up to the takeover point (Step 3)
A run with no hint mention before the takeover gets only cut (ii) (2 of the 21).
Pairs of identical length. hinted = the run's own prompt, whose hint names the wrong letter W.
clean = the same prompt with W replaced by the model's own no-hint letter O inside the hint text
only (on these sure questions, O is the answer key). The two must have the same token count and
differ only inside the hint; otherwise an equal-length neutral filler replaces the letter
instead. Both keep the same reasoning.
  logit difference  LD = logit(W) - logit(O) at the answer position
  restoration       (LD_patched - LD_hinted) / (LD_clean - LD_hinted); left out of the means (and
                    counted) when |LD_clean - LD_hinted| < 0.5, where it is noise over a tiny gap
Patch: one decoder layer at a time, copy the clean run's residual stream (that layer's output) into
the hinted run, separately at three position groups: the hint's tokens, the reasoning, and the
answer position. 32 layers x 3 groups = 96 patched passes per cut, plus 4 more.
Sanity checks per cut: patching every position at the last layer gives the clean LD; patching
nothing gives the hinted LD.
Note: at cut (ii) the reasoning itself names W. If the clean run still answers W there, the
reasoning's repetition is carrying the hint, which should agree with Step 4: deleting the
mentions brought the forced answer back to the own answer in 7 of 19. The report puts the two side
by side per case.

  python finetune/look/patching.py --dry-run     # cases, cuts, tokens, memory, estimated GPU time; no model
  python finetune/look/patching.py               # all cuts -> $TRACKA_OUT/step10/ (resumable: one file per cut)
  python finetune/look/patching.py --limit 2     # a quick check on the 2 shortest cuts
  python finetune/look/patching.py --report      # step10_patching.json (copy back) + the figure; no model
  python finetune/look/patching.py --plot results/trackA/gpu/step10_patching.json   # redraw the figure (Mac)
  python finetune/look/patching.py --by-layer-type results/trackA/gpu/step10_patching.json
                                                 # restoration in the 8 full-attention vs 24 sliding-window
                                                 # layers -> results/summaries/trackA/step10_by_layer_type.json
On Sol: finetune/gpu/sol/run.sh step10 [args] (session) or finetune/gpu/sol/submit.sh step10 (batch).
--model, --runs-from and --cases-from let the same code run on a trained version (Phase 6).
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import boot_mean, load  # noqa: E402
from finetune.gpu import kit  # noqa: E402
from finetune.look import hint_spans as hs  # noqa: E402

GROUPS = ("hint", "reasoning", "answer")
OLMO3_FULL_LAYERS = list(range(3, 32, 4))   # Olmo 3 7B: every 4th layer is full attention; the rest slide (4,096)
BY_TYPE_OUT = CODE / "results" / "summaries" / "trackA" / "step10_by_layer_type.json"
FILLERS = ("X", "?", "_", "-")
MIN_GAP = 0.5
LETTERS = "ABCDEFGHIJ"
HEADROOM = 6 * kit.GiB
TOK_PER_S = 9000          # A100 bf16 forward, for the estimate
NOTE = ("At cut (ii) the reasoning itself names the hint letter W. If the clean run still answers W there, the "
        "reasoning's repetition is carrying the hint; compare Step 4 (deleting the mentions brought the forced answer "
        "back in 7 of 19).")


# ---------------------------------------------------------------- cases, cuts, pairs
def cuts(case, src):
    """[(cut name, sentences kept, reasoning text)] and the first mention's sentence (1-based) or None."""
    from finetune.look import before_takeover as bt
    from finetune.look import deletion as dl
    from finetune.look import takeover as tk
    k = case["takeover_k"]
    sents = bt.sentences(src["reasoning_text"], tk.sentence_ends(src["reasoning_text"]))[:k]
    pat = dl.hint_pattern(src["condition"])
    first = next((i for i, s in enumerate(sents, 1) if pat.search(s)), None)
    out = [("i", first - 1, "".join(sents[:first - 1]))] if first else []
    return out + [("ii", k, "".join(sents))], first


def replace_letter(prompt, src, letter):
    hint, at = hs.hint_text(src)
    return prompt.replace(hint, hint[:at] + letter + hint[at + 1:])


def pair(tok, src, reasoning, own):
    """(hinted layout, clean token ids, what replaced the hint letter): the same number of tokens,
    differing only inside the hint."""
    lay = hs.layout(tok, src, reasoning)
    inside = set(lay["hint"])
    for fill in (own,) + FILLERS:
        ids, _ = hs.tokenize(tok, replace_letter(src["rendered_prompt"], src, fill) + reasoning + hs.FORCE)
        if len(ids) == len(lay["ids"]) and {i for i, (a, b) in enumerate(zip(ids, lay["ids"])) if a != b} <= inside:
            return lay, ids, ("own letter" if fill == own else f"filler {fill!r}")
    raise ValueError(f"run {src['run_id']}: no equal-length clean prompt")


# ---------------------------------------------------------------- patching
def decoder_layers(model):
    return model.get_decoder().layers


def _hidden(out):
    return out[0] if isinstance(out, tuple) else out


class Hooks:
    """Record every layer's output, or overwrite one layer's output at some positions."""

    def __init__(self, model):
        self.layers, self.handles = decoder_layers(model), []

    def record(self, store):
        for i, layer in enumerate(self.layers):
            self.handles.append(layer.register_forward_hook(
                lambda mod, args, out, i=i: store.__setitem__(i, _hidden(out)[0].detach().clone())))
        return self

    def patch(self, layer, positions, source):
        def fn(mod, args, out):
            if len(positions):
                _hidden(out)[0, positions] = source[positions]
            return out
        self.handles.append(self.layers[layer].register_forward_hook(fn))
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        for h in self.handles:
            h.remove()
        self.handles = []


def forward(model, ids, w, o, letters):
    """(LD = logit(W) - logit(O) at the last position, {letter: probability} over the options)."""
    import torch
    with torch.no_grad():
        logits = model(input_ids=ids, logits_to_keep=1).logits[0, -1].float()
    p = torch.softmax(logits, -1)[letters].tolist()
    return float(logits[w] - logits[o]), dict(zip(LETTERS, p))


def patch_cut(model, tok, lay, clean_ids, hint_letter, own, n_options):
    """Every patched pass for one cut: LDs per group and layer, the two baselines, the sanity checks."""
    import torch
    dev = next(model.parameters()).device
    letter = lambda L: tok(L, add_special_tokens=False)["input_ids"][0]  # noqa: E731
    w, o = letter(hint_letter), letter(own)
    letters = [letter(L) for L in LETTERS[:n_options]]
    hinted = torch.tensor([lay["ids"]], device=dev)
    clean = torch.tensor([clean_ids], device=dev)
    ld_h, p_h = forward(model, hinted, w, o, letters)
    store = {}
    with Hooks(model).record(store):
        ld_c, p_c = forward(model, clean, w, o, letters)
    n = len(decoder_layers(model))
    everywhere = torch.arange(len(clean_ids), device=dev)
    with Hooks(model).patch(n - 1, everywhere, store[n - 1]):
        ld_last_all, _ = forward(model, hinted, w, o, letters)
    with Hooks(model).patch(n // 2, torch.tensor([], dtype=torch.long, device=dev), store[n // 2]):
        ld_none, _ = forward(model, hinted, w, o, letters)
    pos = {"hint": lay["hint"], "reasoning": lay["reasoning"], "answer": [lay["answer"]]}
    lds = {g: [None] * n for g in GROUPS}
    for layer in range(n):
        for g in GROUPS:
            if not pos[g]:
                continue                                               # e.g. cut (i) right after "<think>"
            with Hooks(model).patch(layer, torch.tensor(pos[g], device=dev), store[layer]):
                lds[g][layer] = forward(model, hinted, w, o, letters)[0]
    top = lambda p: max(p, key=p.get)  # noqa: E731
    return {"ld_hinted": ld_h, "ld_clean": ld_c, "probs_hinted": p_h, "probs_clean": p_c,
            "top_hinted": top(p_h), "top_clean": top(p_c), "ld_patched": lds,
            "sanity": {"last_layer_everywhere_minus_clean": ld_last_all - ld_c, "nothing_minus_hinted": ld_none - ld_h,
                       "ok": abs(ld_last_all - ld_c) < 1e-2 and abs(ld_none - ld_h) < 1e-2},
            "positions": {g: len(v) for g, v in pos.items()}}


# ---------------------------------------------------------------- inputs and jobs
def inputs(runs_from=None, cases_from=None):
    """(chosen cases, {run_id: Step 2b record}, {question_id: item}, Step 4 forced answers by run)."""
    from finetune import base_format as bf
    from finetune.look import deletion as dl
    from finetune.look import takeover as tk
    if runs_from is None and cases_from is None:
        kit.check_inputs("step10")
    saved = load(cases_from or tk.CASES_OUT)
    cases = dl.choose(saved[-1]["cases"])
    steps = {r["run_id"]: r for r in bf.current(load(runs_from or bf.OUT))}
    for c in cases:
        src = steps.get(c["source_run_id"])
        if src is None or src["timestamp_utc"] != c["source_timestamp_utc"]:
            raise SystemExit(f"case {c['source_run_id']}: its Step 2b run changed; rerun takeover.py --cases")
    step4 = {}
    if cases_from is None:
        for r in load(dl.RUNS_OUT):
            if r["deletion_arm"] == "hint" and r["call"] == "forced" and r["status"] == "ok":
                step4[r["source_run_id"]] = r["outcome"]
    return cases, steps, {it["question_id"]: it for it in bf.questions()}, step4


def jobs(tok, cases, steps, items):
    """One job per (case, cut), shortest first: (case, cut name, sentences kept, reasoning, first mention, tokens)."""
    out = []
    for c in cases:
        src = steps[c["source_run_id"]]
        cs, first = cuts(c, src)
        for name, kept, text in cs:
            n = len(hs.tokenize(tok, src["rendered_prompt"] + text + hs.FORCE)[0])
            out.append({"case": c, "cut": name, "kept": kept, "reasoning": text, "first_mention": first, "tokens": n})
    return sorted(out, key=lambda j: (j["tokens"], j["case"]["source_run_id"], j["cut"]))


def job_id(j):
    return f"{j['case']['source_run_id']}_{j['cut']}"


def run(model=None, device="auto", out=None, dry_run=False, limit=None, runs_from=None, cases_from=None):
    path, commit = kit.snapshot(model)
    snap = kit.describe_snapshot(path, commit)
    print(kit.snapshot_line(snap))
    cases, steps, items, step4 = inputs(runs_from, cases_from)
    tok = kit.load_tokenizer(path)
    todo_all = jobs(tok, cases, steps, items)
    if limit:
        todo_all = todo_all[:limit]
    only_ii = [c for c in cases if not cuts(c, steps[c["source_run_id"]])[1]]
    print(f"{len(cases)} cases, {len(todo_all)} cuts ({sum(j['cut'] == 'i' for j in todo_all)} at (i), "
          f"{sum(j['cut'] == 'ii' for j in todo_all)} at (ii)); only cut (ii), no mention before the takeover: "
          + (", ".join(f"{c['item_id']} {c['condition']} run {c['repeat']}" for c in only_ii) or "none"))
    toks = [j["tokens"] for j in todo_all]
    from transformers import AutoConfig
    cfg = AutoConfig.from_pretrained(path, local_files_only=True)
    passes = 3 * cfg.num_hidden_layers + 4
    est = passes * sum(toks) / TOK_PER_S
    print(f"tokens per cut: median {statistics.median(toks):,.0f}, max {max(toks):,}; {passes} passes per cut, "
          f"{passes * sum(toks) / 1e6:.1f}M tokens in all; estimated A100 time ~{est / 60:.0f} min + ~2 min to load")
    longest = max(toks)
    dev = kit.pick_device(device)
    act = longest * cfg.hidden_size * 2 * (cfg.num_hidden_layers + 4) + longest * cfg.intermediate_size * 2 * 3 \
        + longest ** 2
    need = kit.model_bytes(path, "bf16") + act + HEADROOM
    if dry_run:
        print("| case | channel | cut | sentences kept | tokens |")
        print("|---|---|---|---|---|")
        for j in todo_all:
            c = j["case"]
            print(f"| {c['item_id']} run {c['repeat']} | {c['condition']}{' + declared' if c.get('arm') else ''} | "
                  f"({j['cut']}) | {j['kept']} of {c['n_sentences']} | {j['tokens']:,} |")
        n, have = kit.check_memory(dev, need, "Step 10")
        print(f"memory: needs ~{n / kit.GiB:.1f} GiB at {longest:,} tokens, {have / kit.GiB:.1f} GiB free on {dev}: ok")
        return None
    kit.check_memory(dev, need, "Step 10")
    d = kit.out_dir("step10", out)
    (d / "cuts").mkdir(exist_ok=True)
    todo = [j for j in todo_all if not (d / "cuts" / f"{job_id(j)}.json").exists()]
    print(f"{len(todo_all) - len(todo)} cuts already done; {len(todo)} to go")
    if not todo:
        return d
    m = kit.load_model(path, "bf16" if dev.type != "cpu" else "fp32", dev)
    t, seen = kit.Timer(), 0
    for i, j in enumerate(todo, 1):
        c = j["case"]
        src, it = steps[c["source_run_id"]], items[c["item_id"]]
        own, w = it["answer"], src["cue_letter"]
        lay, clean_ids, clean_kind = pair(tok, src, j["reasoning"], own)
        res = patch_cut(m, tok, lay, clean_ids, w, own, len(it["options"]))
        row = {"job": job_id(j), "source_run_id": c["source_run_id"], "item_id": c["item_id"],
               "condition": c["condition"], "arm": c.get("arm"), "repeat": c["repeat"], "cut": j["cut"],
               "sentences_kept": j["kept"], "n_sentences": c["n_sentences"], "takeover_k": c["takeover_k"],
               "first_mention": j["first_mention"], "tokens": len(lay["ids"]), "hint_letter": w, "own_letter": own,
               "clean": clean_kind, "step4_forced_after_deleting_mentions": step4.get(c["source_run_id"]),
               **res, "snapshot_commit": commit, "timestamp_utc": kit.now()}
        kit.write_json(d / "cuts" / f"{job_id(j)}.json", row)
        seen += j["tokens"]
        left = sum(x["tokens"] for x in todo[i:])
        print(f"  {i}/{len(todo)} {row['job']} ({j['tokens']:,} tokens): LD hinted {res['ld_hinted']:+.2f} "
              f"({res['top_hinted']}), clean {res['ld_clean']:+.2f} ({res['top_clean']}); sanity "
              f"{'ok' if res['sanity']['ok'] else 'OFF ' + json.dumps(res['sanity'])}; {t() / 60:.1f} min, "
              f"~{t() / seen * left / 60:.0f} min left", flush=True)
    return d


# ---------------------------------------------------------------- report and figure
def restoration(row, group):
    gap = row["ld_clean"] - row["ld_hinted"]
    if abs(gap) < MIN_GAP:
        return None
    return [None if v is None else (v - row["ld_hinted"]) / gap for v in row["ld_patched"][group]]


def report(out=None, d=None):
    d = Path(d) if d else kit.out_dir("step10", out)
    rows = [json.loads(p.read_text()) for p in sorted((d / "cuts").glob("*.json"))]
    if not rows:
        raise SystemExit(f"no saved cuts in {d}")
    n_layers = len(rows[0]["ld_patched"]["hint"])
    by_layer = {}
    for cut in ("i", "ii"):
        rs = [r for r in rows if r["cut"] == cut]
        usable = [r for r in rs if abs(r["ld_clean"] - r["ld_hinted"]) >= MIN_GAP]
        by_layer[cut] = {"cuts": len(rs), "usable": len(usable), "left_out_small_gap": len(rs) - len(usable)}
        for g in GROUPS:
            means = []
            for layer in range(n_layers):
                groups = {}
                for r in usable:
                    v = restoration(r, g)[layer]
                    if v is not None:
                        groups.setdefault(r["item_id"], []).append(v)
                means.append(list(boot_mean(groups)) if groups else None)
            by_layer[cut][g] = means
    cases = [{k: r[k] for k in ("job", "item_id", "condition", "arm", "cut", "tokens", "sentences_kept", "n_sentences",
                                "hint_letter", "own_letter", "clean", "ld_hinted", "ld_clean", "top_hinted", "top_clean",
                                "step4_forced_after_deleting_mentions", "snapshot_commit")}
             | {"ld_patched": r["ld_patched"], "sanity": r["sanity"]} for r in rows]
    ii = [r for r in rows if r["cut"] == "ii"]
    summary = {"step": "step10", "snapshot_commits": sorted({r["snapshot_commit"] for r in rows}),
               "full_attention_layers": full_layers(),
               "definitions": {"LD": "logit(W) - logit(O) at the answer position; W = the hint letter, O = the own answer",
                               "restoration": "(LD_patched - LD_hinted) / (LD_clean - LD_hinted)",
                               "left out": f"cuts with |LD_clean - LD_hinted| < {MIN_GAP}",
                               "patch": "copy the clean run's output of one decoder layer into the hinted run, at the "
                                        "hint's tokens, the reasoning, or the answer position"},
               "sanity_ok": f"{sum(r['sanity']['ok'] for r in rows)} of {len(rows)} cuts",
               "restoration_by_layer": by_layer,
               "cut_ii_note": NOTE,
               "cut_ii_clean_still_answers_W": f"{sum(r['top_clean'] == r['hint_letter'] for r in ii)} of {len(ii)}",
               "cut_ii_vs_step4": [{"job": r["job"], "clean_top": r["top_clean"], "hint_letter": r["hint_letter"],
                                    "step4_forced_after_deleting_mentions": r["step4_forced_after_deleting_mentions"]}
                                   for r in ii],
               "cuts": cases}
    p = kit.write_json(d / "step10_patching.json", summary)
    print(f"{len(rows)} cuts; sanity checks ok on {summary['sanity_ok']}")
    for cut in ("i", "ii"):
        b = by_layer[cut]
        print(f"\ncut ({cut}): {b['usable']} of {b['cuts']} cuts usable (gap >= {MIN_GAP})")
        for g in GROUPS:
            best = max(((i, v[0]) for i, v in enumerate(b[g]) if v), key=lambda x: x[1], default=None)
            print(f"  {g:9} " + " ".join("  .  " if v is None else f"{v[0]:+.2f}" for v in b[g])
                  + (f"   best: layer {best[0]} ({best[1]:+.2f})" if best else ""))
    print(f"\ncut (ii): the clean run still answers W in {summary['cut_ii_clean_still_answers_W']}. {NOTE}")
    plot(summary, d)
    print(f"saved {p} (copy back) and {d / 'step10_restoration.png'}")
    return summary


def full_layers():
    """The full-attention layers of the model in the cache (Olmo 3 7B's when its config isn't there)."""
    try:
        from transformers import AutoConfig
        return kit.config_fields(AutoConfig.from_pretrained(kit.snapshot()[0], local_files_only=True))["full_attention_layers"]
    except Exception:                                        # noqa: BLE001
        return OLMO3_FULL_LAYERS


def by_layer_type(summary, full=None):
    """Restoration in the full-attention vs sliding-window layers, per cut and position group.
    Per cut: the mean restoration over the layers of each type; then the mean over cuts with a 95%
    bootstrap clustered by question, the paired difference full - sliding, and each type's best
    single layer (its mean over cuts). Cuts with |LD_clean - LD_hinted| < MIN_GAP are left out."""
    full = set(full or summary.get("full_attention_layers") or OLMO3_FULL_LAYERS)
    out = {"full_attention_layers": sorted(full), "min_gap": MIN_GAP}
    for cut in ("i", "ii"):
        rows = [r for r in summary["cuts"] if r["cut"] == cut and abs(r["ld_clean"] - r["ld_hinted"]) >= MIN_GAP]
        out[cut] = {"usable_cuts": len(rows), "left_out_small_gap": sum(r["cut"] == cut for r in summary["cuts"]) - len(rows)}
        for g in GROUPS:
            per = {"full": {}, "sliding": {}, "full - sliding": {}}
            layer_means = {"full": {}, "sliding": {}}
            for r in rows:
                rest = restoration(r, g)
                vals = {t: [v for i, v in enumerate(rest) if v is not None and ((i in full) == (t == "full"))]
                        for t in ("full", "sliding")}
                if not vals["full"] or not vals["sliding"]:
                    continue
                m = {t: statistics.mean(v) for t, v in vals.items()}
                for t in ("full", "sliding"):
                    per[t].setdefault(r["item_id"], []).append(m[t])
                per["full - sliding"].setdefault(r["item_id"], []).append(m["full"] - m["sliding"])
                for i, v in enumerate(rest):
                    if v is not None:
                        layer_means["full" if i in full else "sliding"].setdefault(i, []).append(v)
            cell = {}
            for t, groups in per.items():
                cell[t] = dict(zip(("mean", "low", "high"), boot_mean(groups))) if groups else None
            for t in ("full", "sliding"):
                if layer_means[t]:
                    best = max(layer_means[t], key=lambda i: statistics.mean(layer_means[t][i]))
                    cell[f"best {t} layer"] = {"layer": best, "mean": statistics.mean(layer_means[t][best])}
            cell["cuts"] = sum(len(v) for v in per["full"].values())
            out[cut][g] = cell
    return out


def show_by_layer_type(res):
    fmt = lambda c: "—" if not c else f"{c['mean']:+.2f} [{c['low']:+.2f}, {c['high']:+.2f}]"  # noqa: E731
    print(f"Restoration by layer type (full attention: layers {res['full_attention_layers']}; the other "
          f"{32 - len(res['full_attention_layers'])} slide over 4,096 tokens); mean over each type's layers, "
          f"then over cuts, 95% bootstrap by question")
    print("| cut | positions patched | cuts | full | sliding | full - sliding | best full layer | best sliding layer |")
    print("|---|---|---|---|---|---|---|---|")
    for cut in ("i", "ii"):
        for g in GROUPS:
            c = res[cut][g]
            best = lambda t: (f"{c[t]['layer']} ({c[t]['mean']:+.2f})" if t in c else "—")  # noqa: E731
            print(f"| ({cut}) | {g} | {c['cuts']} | {fmt(c['full'])} | {fmt(c['sliding'])} | {fmt(c['full - sliding'])} | "
                  f"{best('best full layer')} | {best('best sliding layer')} |")
        print(f"| ({cut}) | left out (gap < {res['min_gap']}) | {res[cut]['left_out_small_gap']} | | | | | |")


def plot(summary, d):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for ax, cut in zip(axes, ("i", "ii")):
        b = summary["restoration_by_layer"][cut]
        for g in GROUPS:
            pts = [(i, v) for i, v in enumerate(b[g]) if v]
            if not pts:
                continue
            x = [i for i, _ in pts]
            ax.plot(x, [v[0] for _, v in pts], label=g)
            ax.fill_between(x, [v[1] for _, v in pts], [v[2] for _, v in pts], alpha=0.2)
        ax.axhline(0, color="grey", lw=0.5)
        ax.axhline(1, color="grey", lw=0.5, ls="--")
        ax.set_title(f"cut ({cut}): {'before the first hint mention' if cut == 'i' else 'at the takeover point'} "
                     f"({b['usable']} of {b['cuts']})")
        ax.set_xlabel("layer patched")
    axes[0].set_ylabel("restoration (1 = clean answer)")
    if any(ax.lines[2:] for ax in axes):                       # beyond the two reference lines
        axes[0].legend(title="positions patched")
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(Path(d) / f"step10_restoration.{ext}", dpi=150)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true", help="summary and figure from the saved cuts; no model")
    ap.add_argument("--plot", metavar="SUMMARY", help="redraw the figure from a step10_patching.json (next to it)")
    ap.add_argument("--by-layer-type", metavar="SUMMARY", help="restoration in full vs sliding-window layers, from "
                    "a step10_patching.json; numbers to results/summaries/trackA/step10_by_layer_type.json")
    ap.add_argument("--limit", type=int, help="only the N shortest cuts")
    ap.add_argument("--model", help="a local model directory (a trained version, or a test's tiny model)")
    ap.add_argument("--runs-from", help="a base_format-style .jsonl.gz of runs (default: Step 2b's)")
    ap.add_argument("--cases-from", help="a takeover_cases-style .jsonl (default: Step 3's)")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--out", help="output base directory (default $TRACKA_OUT)")
    a = ap.parse_args(argv)
    if a.plot:
        return plot(json.loads(Path(a.plot).read_text()), Path(a.plot).parent)
    if a.by_layer_type:
        res = by_layer_type(json.loads(Path(a.by_layer_type).read_text()))
        show_by_layer_type(res)
        BY_TYPE_OUT.parent.mkdir(parents=True, exist_ok=True)
        BY_TYPE_OUT.write_text(json.dumps(res, indent=1) + "\n")
        print(f"saved {BY_TYPE_OUT.relative_to(CODE)}")
        return res
    if a.report:
        return report(a.out)
    d = run(a.model, a.device, a.out, a.dry_run, a.limit, a.runs_from, a.cases_from)
    if d and not a.limit:
        return report(d=d)
    return d


if __name__ == "__main__":
    main()
