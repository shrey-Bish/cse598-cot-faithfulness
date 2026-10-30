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
  python finetune/look/patching.py --handoff results/trackA/gpu/step10_patching.json
                                                 # the readout: per layer, the drop in hint-token restoration
                                                 # and the rise at the answer; shares at the full-attention
                                                 # layers and at 15, 19, 23; direct vs written at cut (ii)
                                                 # -> results/summaries/trackA/step10_handoff.json + figure
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

from common import boot_mean, load, too_few  # noqa: E402
from finetune.gpu import kit  # noqa: E402
from finetune.look import hint_spans as hs  # noqa: E402

GROUPS = ("hint", "reasoning", "answer")
OLMO3_FULL_LAYERS = kit.OLMO3_FULL_LAYERS
BY_TYPE_OUT = CODE / "results" / "summaries" / "trackA" / "step10_by_layer_type.json"
HANDOFF_OUT = CODE / "results" / "summaries" / "trackA" / "step10_handoff.json"
HANDOFF_FIG = CODE / "results" / "trackA" / "figures" / "step10_handoff.png"
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
def inputs(runs_from=None, cases_from=None, items_from=None):
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
    return cases, steps, {it["question_id"]: it for it in (load(items_from) if items_from else bf.questions())}, step4


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


def run(model=None, device="auto", out=None, dry_run=False, limit=None, runs_from=None, cases_from=None, items_from=None):
    path, commit = kit.snapshot(model)
    snap = kit.describe_snapshot(path, commit)
    print(kit.snapshot_line(snap))
    cases, steps, items, step4 = inputs(runs_from, cases_from, items_from)
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
def clustered(groups, n=20000):
    """{mean, low, high, questions} for values grouped by question, with a 95% bootstrap clustered by
    question; low and high are None under MIN_QUESTIONS questions ("too few questions")."""
    if not groups:
        return None
    if too_few(groups):
        return {"mean": statistics.mean(v for vs in groups.values() for v in vs), "low": None, "high": None,
                "questions": len(groups)}
    m, lo, hi = boot_mean(groups, n=n)
    return {"mean": m, "low": lo, "high": hi, "questions": len(groups)}


def show_ci(c, sign=True):
    """'m [low, high] (q questions)', or the mean with 'too few questions'."""
    if not c:
        return "—"
    f = (lambda x: f"{x:+.2f}") if sign else (lambda x: f"{x:.2f}")  # noqa: E731
    if c["low"] is None:
        return f"{f(c['mean'])} (too few questions: {c['questions']})"
    return f"{f(c['mean'])} [{f(c['low'])}, {f(c['high'])}]"


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
                c = clustered(groups)
                means.append([c["mean"], c["low"], c["high"]] if c else None)
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
    return kit.full_attention_layers()


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
                cell[t] = clustered(groups)
            for t in ("full", "sliding"):
                if layer_means[t]:
                    best = max(layer_means[t], key=lambda i: statistics.mean(layer_means[t][i]))
                    cell[f"best {t} layer"] = {"layer": best, "mean": statistics.mean(layer_means[t][best])}
            cell["cuts"] = sum(len(v) for v in per["full"].values())
            out[cut][g] = cell
    return out


def show_by_layer_type(res):
    fmt = show_ci
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


def hint_distances(runs_from=None, cases_from=None, items_from=None):
    """{job id: tokens from the hint (its last token; its letter) to the answer position, and the
    cut's length}, rebuilt with the tokenizer alone (no model), as the GPU run built the inputs
    (set A: the same --runs-from, --cases-from and --items-from as its Step 10 job)."""
    tok = kit.load_tokenizer(kit.snapshot()[0])
    cases, steps, items, _ = inputs(runs_from, cases_from, items_from)
    out = {}
    for j in jobs(tok, cases, steps, items):
        lay = hs.layout(tok, steps[j["case"]["source_run_id"]], j["reasoning"])
        out[job_id(j)] = {"tokens": len(lay["ids"]), "hint_end": lay["answer"] - lay["hint"][-1],
                          "letter": lay["answer"] - lay["letter"][0]}
    return out


def steps_of(rest, start):
    """Per layer, the change from the layer before; the layer before layer 0 is the unpatched input
    (start: 1 for the hint's tokens, where it is the clean input itself; 0 for the answer position,
    whose input is the same in both runs)."""
    prev, out = start, []
    for v in rest:
        out.append(None if v is None else v - prev)
        prev = prev if v is None else v
    return out


def handoff(summary, distances=None, full=None, readout=(15, 19, 23), window=4096):
    """Where the hint's information leaves the hint tokens and reaches the answer, per cut:
    - drop at layer l = restoration(hint tokens, l - 1) - restoration(hint tokens, l): what layer l
      read out of the hint tokens (patching them after it no longer matters). The drops add up to
      1 - restoration at the last layer = 1.
    - rise at layer l = restoration(answer, l) - restoration(answer, l - 1); they add up to 1.
    Shares of the total at the full-attention layers and at the readout layers, per cut, then the
    mean over cuts with a 95% bootstrap clustered by question; per cut type, all cuts and split by
    whether the hint letter is within `window` tokens of the answer (the sliding layers reach it).
    Cuts with |LD_clean - LD_hinted| < MIN_GAP are left out, as everywhere."""
    full = sorted(full or summary.get("full_attention_layers") or OLMO3_FULL_LAYERS)
    readout = [layer for layer in readout if layer in full]
    out = {"full_attention_layers": full, "readout_layers": list(readout), "window": window, "min_gap": MIN_GAP,
           "per_cut": [], "by_cut_type": {}}
    for r in summary["cuts"]:
        if abs(r["ld_clean"] - r["ld_hinted"]) < MIN_GAP:
            continue
        drop = steps_of(restoration(r, "hint"), 1.0)
        drop = [None if v is None else -v for v in drop]
        rise = steps_of(restoration(r, "answer"), 0.0)
        row = {"job": r["job"], "item_id": r["item_id"], "cut": r["cut"]}
        if distances:
            dist = distances[r["job"]]
            if dist["tokens"] != r["tokens"]:
                raise SystemExit(f"{r['job']}: {dist['tokens']} tokens here, {r['tokens']} on the GPU")
            row.update({"letter_to_answer": dist["letter"], "hint_within_window": dist["letter"] < window})
        for name, xs in (("drop", drop), ("rise", rise)):
            tot = sum(v for v in xs if v is not None)
            row[f"{name}_by_layer"] = xs
            row[f"{name}_total"] = tot
            row[f"{name}_share_full"] = sum(xs[i] for i in full if xs[i] is not None) / tot if tot else None
            row[f"{name}_share_readout"] = sum(xs[i] for i in readout if xs[i] is not None) / tot if tot else None
        out["per_cut"].append(row)

    def agg(rows):
        res = {"cuts": len(rows), "questions": len({r["item_id"] for r in rows})}
        if not rows:
            return res
        for key in ("drop_share_full", "drop_share_readout", "rise_share_full", "rise_share_readout"):
            g = {}
            for r in rows:
                if r[key] is not None:
                    g.setdefault(r["item_id"], []).append(r[key])
            res[key] = clustered(g)
        for name in ("drop", "rise"):
            per_layer = []
            for i in range(len(rows[0][f"{name}_by_layer"])):
                g = {}
                for r in rows:
                    if r[f"{name}_by_layer"][i] is not None:
                        g.setdefault(r["item_id"], []).append(r[f"{name}_by_layer"][i])
                per_layer.append(clustered(g, n=5000))
            res[f"{name}_by_layer"] = per_layer
        return res

    for cut in ("i", "ii"):
        rows = [r for r in out["per_cut"] if r["cut"] == cut]
        cell = {"all": agg(rows)}
        if distances:
            cell["hint within the window"] = agg([r for r in rows if r["hint_within_window"]])
            cell["hint beyond the window"] = agg([r for r in rows if not r["hint_within_window"]])
        b = summary["restoration_by_layer"][cut]["reasoning"]
        peak = max((i for i, v in enumerate(b) if v), key=lambda i: b[i][0], default=None)
        cell["reasoning_peak"] = None if peak is None else {"layer": peak, "mean": b[peak][0], "low": b[peak][1],
                                                            "high": b[peak][2], "questions": len({r["item_id"] for r in rows})}
        out["by_cut_type"][cut] = cell
    return out


def paths_at_cut_ii(summary, distances=None):
    """Direct vs written: per case at cut (ii), the clean run's forced answer (only the prompt's letter
    swapped, W -> O; the reasoning still names W) beside Step 4's (the mentions deleted, the prompt still
    W), with the totals and Wilson intervals. The case sets differ: Step 4 has no deletion for the
    cases with no mention before the takeover."""
    from common import wilson
    rows = []
    for r in summary["cuts"]:
        if r["cut"] != "ii":
            continue
        clean = "W" if r["top_clean"] == r["hint_letter"] else ("O" if r["top_clean"] == r["own_letter"] else "other")
        rows.append({"job": r["job"], "item_id": r["item_id"], "condition": r["condition"], "arm": r["arm"],
                     "hinted_answers_W": r["top_hinted"] == r["hint_letter"], "clean_answers": clean,
                     "ld_hinted": r["ld_hinted"], "ld_clean": r["ld_clean"],
                     "step4_after_deleting_mentions": r["step4_forced_after_deleting_mentions"],
                     "letter_to_answer": (distances or {}).get(r["job"], {}).get("letter")})
    n = len(rows)
    off = sum(r["clean_answers"] != "W" for r in rows)
    s4 = [r for r in rows if r["step4_after_deleting_mentions"]]
    own4 = sum(r["step4_after_deleting_mentions"] == "own" for r in s4)
    both = {}
    for r in s4:
        k = f"step 4 {r['step4_after_deleting_mentions']}, clean {r['clean_answers']}"
        both[k] = both.get(k, 0) + 1
    return {"cases": rows,
            "hinted_run_answers_W": f"{sum(r['hinted_answers_W'] for r in rows)} of {n}",
            "swap_only_the_prompt_letter": {"off_W": off, "to_O": sum(r["clean_answers"] == "O" for r in rows),
                                            "to_another_letter": sum(r["clean_answers"] == "other" for r in rows),
                                            "still_W": n - off, "of": n, "off_W_ci95": wilson(off, n)},
            "step4_delete_the_mentions": {"back_to_own": own4, "of": len(s4), "ci95": wilson(own4, len(s4)),
                                          "outcomes": {k: sum(r["step4_after_deleting_mentions"] == k for r in s4)
                                                       for k in ("own", "hint", "other")}},
            "cases_in_both": len(s4), "cross_table": dict(sorted(both.items()))}


def show_handoff(h, paths):
    pct = lambda c: show_ci(c, sign=False)  # noqa: E731
    ro = ", ".join(map(str, h["readout_layers"]))
    print(f"Readout: the drop in hint-token restoration per layer, as a share of its total (= 1), and the rise at the "
          f"answer; full-attention layers {h['full_attention_layers']}; 95% bootstrap by question")
    print(f"| cut | cuts | questions | drop: share at full layers | drop: share at {ro} | rise: share at full layers | "
          f"rise: share at {ro} |")
    print("|---|---|---|---|---|---|---|")
    for cut, cell in h["by_cut_type"].items():
        for part, a in cell.items():
            if part == "reasoning_peak" or not a.get("cuts"):
                continue
            print(f"| ({cut}) {part} | {a['cuts']} | {a['questions']} | {pct(a['drop_share_full'])} | "
                  f"{pct(a['drop_share_readout'])} | {pct(a['rise_share_full'])} | {pct(a['rise_share_readout'])} |")
    for cut, cell in h["by_cut_type"].items():
        a = cell["all"]
        big = [(i, d) for i, d in enumerate(a["drop_by_layer"]) if d and d["mean"] >= 0.03]
        print(f"({cut}) drops of 0.03 or more: " + ", ".join(f"layer {i} {pct(d)}" for i, d in big))
        p = cell["reasoning_peak"]
        if p:
            print(f"({cut}) reasoning positions: peak restoration {show_ci(p)} at layer {p['layer']}")
    s, d4 = paths["swap_only_the_prompt_letter"], paths["step4_delete_the_mentions"]
    print(f"\nCut (ii), the hinted run answers W in {paths['hinted_run_answers_W']}.")
    print(f"Swap only the prompt's letter (W -> O; the reasoning still names W): off W in {s['off_W']} of {s['of']} "
          f"[{s['off_W_ci95'][0]:.2f}, {s['off_W_ci95'][1]:.2f}] ({s['to_O']} to O, {s['to_another_letter']} to another "
          f"letter); still W in {s['still_W']}.")
    if d4["of"]:
        print(f"Step 4, delete the mentions (prompt still W): back to the own answer in {d4['back_to_own']} of "
              f"{d4['of']} [{d4['ci95'][0]:.2f}, {d4['ci95'][1]:.2f}] ({d4['outcomes']}).")
    else:
        print("Step 4: no deletion runs on these cases (Test 2's only).")
    print(f"Both, {paths['cases_in_both']} cases: {paths['cross_table']}")
    print("| case | channel | tokens, letter to answer | LD hinted | LD clean | clean answers | Step 4 |")
    print("|---|---|---|---|---|---|---|")
    for r in paths["cases"]:
        print(f"| {r['job'][:8]} (q {r['item_id']}) | {r['condition']}{' + declared' if r['arm'] else ''} | "
              f"{r['letter_to_answer'] if r['letter_to_answer'] is not None else '—'} | {r['ld_hinted']:+.2f} | "
              f"{r['ld_clean']:+.2f} | {r['clean_answers']} | {r['step4_after_deleting_mentions'] or '— (no mention)'} |")


def plot_handoff(summary, path, readout=(15, 19, 23)):
    """The handoff figure: per cut, hint-token and answer restoration by layer, 95% bands clustered by
    question; light lines at the full-attention layers, the readout layers marked."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    full = summary.get("full_attention_layers") or OLMO3_FULL_LAYERS
    colors = {"hint": "#2a78d6", "answer": "#eb6834"}
    labels = {"hint": "patch the hint's tokens", "answer": "patch the answer position"}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for ax, cut in zip(axes, ("i", "ii")):
        b = summary["restoration_by_layer"][cut]
        for layer in full:
            ax.axvline(layer, color="#52514e" if layer in readout else "#d6d5cf", lw=1.0 if layer in readout else 0.6,
                       ls="--" if layer in readout else "-", zorder=0)
        for g in ("hint", "answer"):
            pts = [(i, v) for i, v in enumerate(b[g]) if v]
            x = [i for i, _ in pts]
            ax.plot(x, [v[0] for _, v in pts], color=colors[g], lw=2, label=labels[g])
            band = [(i, v) for i, v in pts if v[1] is not None]
            ax.fill_between([i for i, _ in band], [v[1] for _, v in band], [v[2] for _, v in band], color=colors[g],
                            alpha=0.15, lw=0)
        for layer in readout:
            ax.text(layer, 1.13, str(layer), ha="center", va="center", fontsize=9, color="#0b0b0b",
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5})
        ax.axhline(0, color="#b5b4ad", lw=0.6)
        ax.axhline(1, color="#b5b4ad", lw=0.6, ls=":")
        ax.set_ylim(-0.1, 1.2)
        ax.set_xlim(-0.5, len(b["hint"]) - 0.5)
        ax.set_title(f"cut ({cut}): {'before the first hint mention' if cut == 'i' else 'at the takeover'} "
                     f"({b['usable']} of {b['cuts']} cuts)", fontsize=10)
        ax.set_xlabel("layer patched (lines: the 8 full-attention layers; dashed: 15, 19, 23)")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[0].set_ylabel("restoration (1 = the clean answer)")
    axes[0].legend(frameon=False, loc="center left")
    fig.suptitle("The handoff: where the hint's effect leaves its tokens and reaches the answer (restoration by layer, "
                 "95% bands clustered by question)", fontsize=11)
    fig.tight_layout()
    path = Path(path)
    for ext in ("png", "svg"):
        fig.savefig(path.with_suffix(f".{ext}"), dpi=150)
    plt.close(fig)


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
            band = [(i, v) for i, v in pts if v[1] is not None]
            ax.fill_between([i for i, _ in band], [v[1] for _, v in band], [v[2] for _, v in band], alpha=0.2)
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
    ap.add_argument("--handoff", metavar="SUMMARY", help="where the hint's information leaves the hint tokens (drops by "
                    "layer, shares at the full-attention and readout layers, split by distance) and the direct vs written "
                    "paths at cut (ii), from a step10_patching.json -> results/summaries/trackA/step10_handoff.json + figure")
    ap.add_argument("--no-distances", action="store_true", help="with --handoff: skip the split by distance (no tokenizer)")
    ap.add_argument("--limit", type=int, help="only the N shortest cuts")
    ap.add_argument("--model", help="a local model directory (a trained version, or a test's tiny model)")
    ap.add_argument("--runs-from", help="a base_format-style .jsonl.gz of runs (default: Step 2b's)")
    ap.add_argument("--cases-from", help="a takeover_cases-style .jsonl (default: Step 3's)")
    ap.add_argument("--items-from", help="the questions in Step 2b's item format (set A: setA/items.jsonl)")
    ap.add_argument("--handoff-out", help="with --handoff: write the summary here instead (set A), figure beside it")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--out", help="output base directory (default $TRACKA_OUT)")
    a = ap.parse_args(argv)
    if a.plot:
        return plot(json.loads(Path(a.plot).read_text()), Path(a.plot).parent)
    if a.handoff:
        summary = json.loads(Path(a.handoff).read_text())
        dist = None if a.no_distances else hint_distances(a.runs_from, a.cases_from, a.items_from)
        h = handoff(summary, dist)
        paths = paths_at_cut_ii(summary, dist)
        show_handoff(h, paths)
        out_json = Path(a.handoff_out) if a.handoff_out else HANDOFF_OUT
        fig = out_json.with_suffix(".png") if a.handoff_out else HANDOFF_FIG
        fig.parent.mkdir(parents=True, exist_ok=True)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        plot_handoff(summary, fig)
        out_json.write_text(json.dumps({"handoff": h, "paths_at_cut_ii": paths,
                                        "snapshot_commits": summary["snapshot_commits"]}, indent=1) + "\n")
        print(f"saved {out_json} and {fig} (+ .svg)")
        return h, paths
    if a.by_layer_type:
        res = by_layer_type(json.loads(Path(a.by_layer_type).read_text()))
        show_by_layer_type(res)
        BY_TYPE_OUT.parent.mkdir(parents=True, exist_ok=True)
        BY_TYPE_OUT.write_text(json.dumps(res, indent=1) + "\n")
        print(f"saved {BY_TYPE_OUT.relative_to(CODE)}")
        return res
    if a.report:
        return report(a.out)
    d = run(a.model, a.device, a.out, a.dry_run, a.limit, a.runs_from, a.cases_from, a.items_from)
    if d and not a.limit:
        return report(d=d)
    return d


if __name__ == "__main__":
    main()
