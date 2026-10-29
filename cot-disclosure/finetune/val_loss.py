"""Track A: the validation loss by part, for the base model and both epochs of each trained version (on Sol,
one A100; CPU tests on a tiny Olmo 3). Ritik, Oct 28: lora's average barely moved (0.18567 -> 0.18537) and
the base model's loss was never measured. Most target tokens are the model's own reasoning, which it
already predicts well; what training teaches is a small part of each target, so each loss is split.

  python finetune/val_loss.py --dry-run                                    # parts' token counts, GPU minutes; tokenizer only
  python finetune/val_loss.py --out OUT --train-dir TRAIN lora tags        # base, then epoch1 and epoch2 of each version
On Sol: finetune/gpu/sol/submit.sh val_loss --estimate H [--dependency=afterany:N] -- lora tags
Back on the Mac (val_loss.json and val_loss_examples.jsonl copied to results/trackA/gpu/):
  python finetune/val_loss.py --report results/trackA/gpu     # each system minus base, with intervals

The same tokens and labels as train.py's validation loss (train.encode, train.usable). Each reply token
belongs to one part, the part where its first non-space character is:
  opener      the reasoning opener we prefilled (make_targets.REASONING_OPENERS; prefill examples)
  hint_check  a reasoning sentence (the opener excluded) that names the hint's source: detect.py's keywords
              for the channel ("cue" for the user, "cue_tool" otherwise), the hint wording's own source words
              (make_targets.SOURCE_WORDS), and for the user channel "suggest..." (the openers' word); plus the
              check sentence of an inserted_sentence example. A keyword rule, not labels.
  final       from </think> to the end of the reply, the template's closing token included
  rest        every other reply token
taught = opener + hint_check + final of the hinted examples; not taught = everything else (the rest, and the
no-hint examples' final answers). Losses are token-weighted means, as train.validation_loss.

Systems: base (the model alone: no adapter, no tags), and <version>/epoch1 and <version>/epoch2 from
TRAIN/<version>/epoch<k>/ (train.py's checkpoints). Each epoch's overall loss is checked against the
validation_loss in its state.json (a warning past 1e-3).
Output (numbers only): OUT/val_loss.json (per system and part: tokens and mean loss; each trained system minus
base) and OUT/val_loss_examples.jsonl (per system and example: tokens and loss sum per part). A rerun skips
the systems already in val_loss.json; Slurm's warning (SIGUSR1) stops before the next example, and the
unfinished system is redone next time.

--report: each trained system minus base per group (taught, its parts, not taught, overall) and the taught
tokens per hint channel, and the taught tokens without the opener (hint_check + final_hinted), paired (the same tokens), with a 95% bootstrap clustered by question (the record id's
item; 20,000 resamples, seed 0). Writes results/summaries/trackA/val_loss_report.json and prints a table.
"""
import argparse
import json
import os
import re
import signal
import sys
import time
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from detect import COMPILED  # noqa: E402
from finetune import olmo_format  # noqa: E402
from finetune import train as tr  # noqa: E402
from finetune.make_targets import REASONING_OPENERS, SOURCE_WORDS  # noqa: E402

PARTS = ("opener", "hint_check", "final", "rest")
GROUPS = ("opener", "hint_check", "final_hinted", "rest_hinted", "final_no_hint", "rest_no_hint",
          "taught", "not_taught", "hinted", "no_hint", "overall")
CHECK = re.compile(r", (?:which agrees with the answer I worked out, \([A-Z]\)|"
                   r"but my own working gives \([A-Z]\), so I keep \([A-Z]\))\.")     # make_targets.fallback
SENTENCE_END = re.compile(r"[.!?]+[\"')\]]*(?=\s)|\n+")
PASS_MINUTES = (3.9, 7.8)       # one forward pass over the 156 validation examples (1.30M tokens) on an A100:
                                # lora trained 2 epochs + 2 validation passes in 3.41 h (Oct 28), a training epoch
                                # ~1.6 h over 7.99M tokens; a forward pass is 1/4 to 1/2 of a training step
LOAD_MINUTES = 2.0              # Python, torch and the 15 GB of weights from /scratch, per model built
VAL_TOKENS = 1301780            # the validation slice's tokens (results/summaries/trackA/data/examples_lengths.json)
DEFINITIONS = {
    "parts": "opener: the prefilled reasoning opener; hint_check: reasoning sentences naming the hint's source "
             "(keywords) and inserted check sentences; final: </think> to the end of the reply; rest: the other "
             "reply tokens",
    "taught": "opener + hint_check + final of the hinted examples",
    "not_taught": "rest of every example + final of the no-hint examples",
    "loss": "token-weighted mean cross-entropy (nats) over the part's reply tokens, as train.validation_loss"}


# ---------------------------------------------------------------- parts
def hinted(ex):
    return ex.get("hint_channel") not in (None, "none")


def source_words(ex):
    """The keywords that name the example's hint source (None: a no-hint example)."""
    if not hinted(ex):
        return None
    ch = ex["hint_channel"]
    pats = [COMPILED["cue" if ch == "user" else "cue_tool"].pattern]
    if SOURCE_WORDS.get(ex.get("hint_wording")):
        pats.append(SOURCE_WORDS[ex["hint_wording"]])
    if ch == "user":
        pats.append(r"\bsuggest")
    return re.compile("|".join(f"(?:{p})" for p in pats), re.IGNORECASE)


def char_spans(ex):
    """(opener end, [(start, end)] of hint-check sentences, where the final answer starts), in target_raw."""
    raw = ex["target_raw"]
    cut = raw.find(olmo_format.THINK_CLOSE)
    end = cut if cut >= 0 else len(raw)
    start = 0
    if ex.get("target_method") == "prefill":
        side, i = ex["openers"]["reasoning"]
        opener = REASONING_OPENERS[side][i]
        if not raw.startswith(opener):
            raise ValueError(f"{ex['record_id']}: the target does not start with its opener")
        start = len(opener)
    checks = []
    pat = source_words(ex)
    if pat:
        bounds = [start] + [start + m.end() for m in SENTENCE_END.finditer(raw[start:end])] + [end]
        checks = [(a, b) for a, b in zip(bounds, bounds[1:]) if b > a and pat.search(raw[a:b])]
        if ex.get("target_method") == "inserted_sentence":
            m = CHECK.search(raw, start, end)
            if not m:
                raise ValueError(f"{ex['record_id']}: no inserted check sentence")
            checks.append((raw.rfind("\n", 0, m.start()) + 1, m.end()))
    return start, checks, end


def encode(tokenizer, ex):
    """train.encode plus each reply token's part, and the example's method and channel."""
    e = tr.encode(tokenizer, ex)
    prompt, full = tr.texts(ex)
    reply = full[len(prompt):]
    if not reply.startswith(ex["target_raw"]):
        raise ValueError(f"{ex['record_id']}: the rendered reply does not start with target_raw")
    enc = tokenizer(reply, add_special_tokens=False, return_offsets_mapping=True)
    if list(enc["input_ids"]) != e["ids"][len(e["ids"]) - e["n_target"]:]:
        raise ValueError(f"{ex['record_id']}: the reply tokenizes differently with offsets")
    opener_end, checks, final_start = char_spans(ex)
    parts = []
    for s, t in enc["offset_mapping"]:
        piece = reply[s:t]
        c = s + len(piece) - len(piece.lstrip()) if piece.strip() else s
        parts.append("final" if c >= final_start else "opener" if c < opener_end
                     else "hint_check" if any(a <= c < b for a, b in checks) else "rest")
    if len(parts) != e["n_target"] or sum(y != -100 for y in e["labels"]) != len(parts):
        raise ValueError(f"{ex['record_id']}: {len(parts)} parts for {e['n_target']} labeled tokens")
    return {**e, "parts": parts, "method": ex.get("target_method"), "channel": ex.get("hint_channel")}


def part_counts(data):
    """Tokens per summary group, no model."""
    rows = [{"channel": e["channel"], **{p: {"tokens": e["parts"].count(p), "loss_sum": 0.0} for p in PARTS}}
            for e in data]
    return {k: v["tokens"] for k, v in summarize(rows).items()}


# ---------------------------------------------------------------- losses
def token_losses(lm, ex, device, chunk=tr.CHUNK):
    """Every reply token's loss, in order (no grad): train.example_loss without the mean."""
    import torch
    import torch.nn.functional as F
    from finetune.source_tags import SourceTaggedLM
    ids = torch.tensor([ex["ids"]], device=device)
    model = tr.causal(lm)
    if isinstance(lm, SourceTaggedLM):
        embeds = lm.embed(ids, torch.tensor([ex["src"]], device=device))
    else:
        embeds = model.get_input_embeddings()(ids)
    h = model.get_decoder()(inputs_embeds=embeds, use_cache=False).last_hidden_state[0, :-1]
    target = torch.tensor(ex["labels"][1:], device=device)        # position t predicts token t + 1
    pos = (target != -100).nonzero().squeeze(-1)
    head = model.get_output_embeddings()
    return torch.cat([F.cross_entropy(head(h[p]).float(), target[p], reduction="none") for p in pos.split(chunk)]).cpu()


def evaluate(lm, data, device, stop=lambda: False):
    """Per example: tokens and loss sum per part; None when stopped."""
    import torch
    lm.eval()
    rows = []
    with torch.no_grad():
        for e in data:
            if stop():
                return None
            acc = {p: [0, 0.0] for p in PARTS}
            for part, x in zip(e["parts"], token_losses(lm, e, device).tolist()):
                acc[part][0] += 1
                acc[part][1] += x
            rows.append({"record_id": e["record_id"], "method": e["method"], "channel": e["channel"],
                         **{p: {"tokens": n, "loss_sum": s} for p, (n, s) in acc.items()}})
    return rows


def summarize(rows):
    """Tokens and token-weighted mean loss per group (GROUPS)."""
    acc = {g: [0, 0.0] for g in GROUPS}
    for r in rows:
        h = r["channel"] not in (None, "none")
        for p in PARTS:
            n, s = r[p]["tokens"], r[p]["loss_sum"]
            name = p if p in ("opener", "hint_check") else f"{p}_{'hinted' if h else 'no_hint'}"
            for g in (name, "taught" if h and p != "rest" else "not_taught", "hinted" if h else "no_hint", "overall"):
                acc[g][0] += n
                acc[g][1] += s
    return {g: {"tokens": n, "loss": s / n if n else None} for g, (n, s) in acc.items()}


REPORT_GROUPS = ("taught", "taught_no_opener", "opener", "hint_check", "final_hinted", "not_taught", "rest_hinted",
                 "overall")      # taught_no_opener: hint_check + final_hinted (Oct 28: the opener is 3% of the taught
                                 # tokens but under LoRA about half of their drop: a fixed phrase, learned)
CHANNELS = ("user", "tool_pasted", "tool_injected")
REPORT = CODE / "results" / "summaries" / "trackA" / "val_loss_report.json"


def per_item(rows):
    """{system: {item: {group: [tokens, loss sum]}}} from val_loss_examples.jsonl rows, and the same for the
    taught tokens per hint channel ("taught | <channel>")."""
    out = {}
    for r in rows:
        g = summarize([r])
        n = g["hint_check"]["tokens"] + g["final_hinted"]["tokens"]
        g["taught_no_opener"] = {"tokens": n, "loss": (sum((g[k]["loss"] or 0.0) * g[k]["tokens"] for k in
                                                           ("hint_check", "final_hinted")) / n) if n else None}
        cell = out.setdefault(r["system"], {}).setdefault(r["record_id"].split("|")[0], {})
        names = list(g) + ([f"taught | {r['channel']}"] if r["channel"] in CHANNELS else [])
        for name in names:
            src = g[name if name in g else "taught"]
            acc = cell.setdefault(name, [0, 0.0])
            acc[0] += src["tokens"]
            acc[1] += (src["loss"] or 0.0) * src["tokens"]
    return out


def boot_minus(sys_items, base_items, group, n=20000, seed=0):
    """(system - base) token-weighted mean loss on the group, and its 95% interval clustered by item."""
    import random
    items = sorted(q for q in base_items if group in base_items[q] and base_items[q][group][0])

    def diff(sample):
        tok = sum(base_items[q][group][0] for q in sample)
        return (sum(sys_items[q][group][1] for q in sample) - sum(base_items[q][group][1] for q in sample)) / tok
    if not items:
        return None, None, 0
    rng = random.Random(seed)
    vals = sorted(diff([rng.choice(items) for _ in items]) for _ in range(n))
    return diff(items), [vals[int(0.025 * n)], vals[int(0.975 * n) - 1]], len(items)


def report(src, out=REPORT):
    """Each trained system minus base (REPORT_GROUPS and the taught tokens per channel), with intervals."""
    res = json.loads((Path(src) / "val_loss.json").read_text())
    rows = [json.loads(x) for x in (Path(src) / "val_loss_examples.jsonl").read_text().splitlines() if x.strip()]
    items = per_item(rows)
    if "base" not in items:
        raise SystemExit(f"no base rows in {src}/val_loss_examples.jsonl")
    groups = list(REPORT_GROUPS) + [f"taught | {c}" for c in CHANNELS]
    table = {}
    for name in [s for s in res["systems"] if s != "base"]:
        if name not in items:
            continue
        table[name] = {}
        for g in groups:
            d, iv, k = boot_minus(items[name], items["base"], g)
            tok = sum(v[g][0] for v in items["base"].values() if g in v)
            base = sum(v[g][1] for v in items["base"].values() if g in v) / tok if tok else None
            table[name][g] = {"base": base, "system": None if base is None else base + d, "minus_base": d,
                              "interval": iv, "relative": d / base if base else None, "tokens": tok, "items": k}
    rep_ = {"source": {k: v for k, v in res.items() if k not in ("systems", "minus_base", "environments")},
            "bootstrap": "paired, clustered by question (record id's item), 20,000 resamples, seed 0",
            "state_check": {s: e.get("overall_minus_state") for s, e in res["systems"].items()},
            "minus_base": table}
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(rep_, indent=1) + "\n")
    def cell(e):
        if e["minus_base"] is None:
            return "—"
        iv = "" if e["interval"] is None else f" [{e['interval'][0]:+.4f}, {e['interval'][1]:+.4f}]"
        return f"{e['minus_base']:+.4f}{iv} ({e['relative']:+.1%})"
    first = next(iter(table.values()), {})
    for title, cols in (("taught tokens and the rest", ("taught", "taught_no_opener", "not_taught", "overall")),
                        ("taught tokens by part and by hint channel", ("opener", "hint_check", "final_hinted",
                                                                       *(f"taught | {c}" for c in CHANNELS)))):
        print(f"\n{title}: each system minus base")
        print("| system | " + " | ".join(c.replace(" | ", ", ") for c in cols) + " |")
        print("|---" * (len(cols) + 1) + "|")
        print("| base (loss; tokens) | " + " | ".join(
            f"{first[c]['base']:.4f}; {first[c]['tokens']:,}" if first.get(c, {}).get("base") is not None else "—"
            for c in cols) + " |")
        for name, t in table.items():
            print(f"| {name} | " + " | ".join(cell(t[c]) for c in cols) + " |")
    print(f"(each system minus base, nats per token, 95% bootstrap clustered by question; relative to base in "
          f"parentheses) -> {out}")
    return rep_


def minus_base(systems):
    base = systems["base"]["groups"]
    return {name: {g: (s["groups"][g]["loss"] - base[g]["loss"]) if base[g]["loss"] is not None else None
                   for g in GROUPS} for name, s in systems.items() if name != "base"}


# ---------------------------------------------------------------- systems
def plan(versions, train_dir):
    """[(name, version, epoch directory)]: base first, then each version's epochs."""
    out = [("base", None, None)]
    for v in versions:
        out += [(f"{v}/epoch{k}", v, Path(train_dir) / v / f"epoch{k}") for k in range(1, tr.EPOCHS + 1)]
    return out


def predicted_minutes(n_systems, n_builds, val_tokens):
    scale = val_tokens / VAL_TOKENS
    return [round(n_systems * m * scale + n_builds * LOAD_MINUTES, 1) for m in PASS_MINUTES]


_stop = {"asked": False}


def _on_signal(signum, frame):
    _stop["asked"] = True


def save(out, res, rows_by_system):
    """val_loss.json, and the examples file with every finished system's rows (a redone system's old rows go)."""
    from finetune.gpu import kit
    path = Path(out) / "val_loss_examples.jsonl"
    old = [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
    keep = [r for r in old if r["system"] not in rows_by_system]
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text("".join(json.dumps(r) + "\n" for r in keep + [{"system": s, **r} for s, rows in rows_by_system.items()
                                                                  for r in rows]))
    tmp.replace(path)
    res["minus_base"] = minus_base(res["systems"]) if "base" in res["systems"] else {}
    kit.write_json(Path(out) / "val_loss.json", res)


def run(versions, train_dir, out, model=None, validation=tr.VALIDATION, device="cuda", dtype="bf16", attn="sdpa"):
    import torch
    from finetune.gpu import kit
    todo = plan(versions, train_dir)
    missing = [str(d) for _, _, d in todo if d is not None and not (d / "trainable.pt").exists()]
    if missing:
        raise SystemExit(f"no checkpoint in: {', '.join(missing)} (train those versions first)")
    path, commit = kit.snapshot(model)
    tok = kit.load_tokenizer(path)
    data = tr.usable(encode(tok, x) for x in tr.load_examples(validation))
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    prev = json.loads((out / "val_loss.json").read_text()) if (out / "val_loss.json").exists() else {}
    res = {**kit.header("val_loss", kit.describe_snapshot(path, commit)), "definitions": DEFINITIONS,
           "validation": str(validation), "examples": len(data), "part_tokens": part_counts(data),
           "systems": prev.get("systems", {})}
    old = {s: signal.signal(s, _on_signal) for s in (signal.SIGTERM, signal.SIGUSR1)}
    try:
        return _run(todo, res, data, out, path, device, dtype, attn)
    finally:
        for s, h in old.items():
            signal.signal(s, h)


def _run(todo, res, data, out, path, device, dtype, attn):
    import torch
    from finetune.gpu import kit
    lm, built = None, None
    for name, version, ckpt in todo:
        if name in res["systems"]:
            print(f"{name}: done before; skipped")
            continue
        t0 = time.monotonic()
        if built != (version or "base"):
            del lm
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            lm = (kit.load_model(path, dtype, device, attn) if version is None
                  else tr.build(version, path, dtype=dtype, device=device, attn=attn, checkpointing=False))
            built = version or "base"
        state = {}
        if ckpt is not None:
            tr.load_weights(lm, ckpt)
            state = json.loads((ckpt / "state.json").read_text())
        rows = evaluate(lm, data, device, stop=lambda: _stop["asked"])
        if rows is None:
            save(out, res, {})
            raise SystemExit(f"stopped by a signal during {name}; a rerun redoes it (finished systems are saved)")
        groups = summarize(rows)
        entry = {"groups": groups, "seconds": round(time.monotonic() - t0, 1)}
        if state.get("validation_loss") is not None:
            entry["state_validation_loss"] = state["validation_loss"]
            entry["overall_minus_state"] = groups["overall"]["loss"] - state["validation_loss"]
            flag = "  WARNING: over 1e-3" if abs(entry["overall_minus_state"]) > 1e-3 else ""
            print(f"{name}: overall {groups['overall']['loss']:.5f} vs its state.json {state['validation_loss']:.5f} "
                  f"({entry['overall_minus_state']:+.2e}){flag}")
        res["systems"][name] = entry
        save(out, res, {name: rows})
        g = groups
        print(f"{name}: taught {g['taught']['loss']:.4f} ({g['taught']['tokens']} tokens), not taught "
              f"{g['not_taught']['loss']:.4f}, overall {g['overall']['loss']:.4f} in {entry['seconds']:.0f} s")
    return res


def dry_run(validation=tr.VALIDATION, model=None, versions=("lora", "tags")):
    from finetune.gpu import kit
    path, _ = kit.snapshot(model)
    tok = kit.load_tokenizer(path)
    data = tr.usable(encode(tok, x) for x in tr.load_examples(validation))
    counts = part_counts(data)
    total = sum(len(e["ids"]) for e in data)
    n_sys = len(plan(versions, "."))
    lo, hi = predicted_minutes(n_sys, 1 + len(versions), total)
    print(f"{len(data)} examples, {total} tokens with the prompts, {counts['overall']} reply tokens:")
    for g in GROUPS:
        print(f"  {g:14s} {counts[g]:>9,} tokens ({counts[g] / counts['overall']:.1%})")
    print(f"{n_sys} systems (base + {', '.join(versions)} x {tr.EPOCHS} epochs), {1 + len(versions)} models built: "
          f"about {lo}-{hi} GPU minutes on an A100")
    return counts, (lo, hi)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("versions", nargs="*", default=["lora", "tags"], help=f"of {tr.VERSIONS} (default: lora tags)")
    ap.add_argument("--out", help="output directory")
    ap.add_argument("--train-dir", help="train.py's outputs, one directory per version")
    ap.add_argument("--model", help="model directory (default: the cached allenai/Olmo-3-7B-Think snapshot)")
    ap.add_argument("--validation", default=str(tr.VALIDATION))
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--dtype", default="bf16", choices=("bf16", "fp32"))
    ap.add_argument("--attn", default="sdpa")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", metavar="DIR", help="val_loss.json and val_loss_examples.jsonl copied back from Sol: "
                                                    "each system minus base with intervals")
    a = ap.parse_args(argv)
    if a.report:
        return report(a.report)
    for v in a.versions:
        if v not in tr.VERSIONS:
            sys.exit(f"unknown version {v!r}; one of {tr.VERSIONS}")
    if os.environ.get("SLURM_JOB_ID") and a.validation == str(tr.VALIDATION):     # on Sol: the Mac's bytes
        from finetune.gpu import kit
        kit.check_inputs("train")
    if a.dry_run:
        return dry_run(a.validation, a.model, a.versions)
    if not (a.out and a.train_dir):
        sys.exit("--out and --train-dir are required")
    return run(a.versions, a.train_dir, a.out, a.model, a.validation, a.device, a.dtype, a.attn)


if __name__ == "__main__":
    main()
