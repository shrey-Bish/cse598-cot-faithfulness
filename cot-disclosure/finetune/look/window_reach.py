"""Track A: does the sliding window matter? No calls; the Olmo tokenizer only.

24 of Olmo 3 7B Think's 32 layers attend only to the last 4,096 tokens: a query sees itself and the
4,095 tokens before it. Hypothesis: the reasoning's mentions of the hint keep it within reach of
those layers, so the hint's pull weakens once the last mention falls out of the window.

For every probe of every hinted Step 3 run (the forced answer after sentence k; results/trackA/
takeover_probes.jsonl.gz), with the run's own no-hint answer known and different from the hint:
  answer position  the last token of prompt + reasoning up to sentence k + "</think>\\n\\nAnswer: (";
                   found from one tokenization of the whole run (within about 2 tokens of
                   tokenizing each probe separately)
  d_mention        tokens from the answer position back to the most recent hint mention in the
                   reasoning so far (the last token of the latest sentence with a mention, in
                   Step 4's words), or back to the prompt's hint when there is none yet
  d_prompt         tokens back to the prompt's hint (its last token)
  outcome          log-odds of the hint letter vs the own answer: log p(hint) - log p(own). A letter
                   outside the top 10 counts at the 10th probability (an upper bound); the share of
                   such probes is reported, and the test is repeated without them.
Step test at a cutoff c: within each run, the mean outcome of the probes just outside (distance c to
c+511) minus just inside (c-512 to c-1). Runs with probes on both sides count; their differences are
averaged with a 95% bootstrap clustered by question. The cutoff 4,096 is the window; 2,048, 3,072,
5,120 and 6,144 are placebos. Also: the 4,096 step minus the mean of the placebo steps, bootstrapped
the same way. Information still passes forward through intermediate tokens, so the window predicts a
soft effect at most, not a cliff; the placebos show whether 4,096 is special at all.

  python finetune/look/window_reach.py            # -> results/summaries/trackA/window_reach.json + .png/.svg
                                                  #    per-probe rows -> results/trackA/window_reach_probes.jsonl.gz
"""
import argparse
import bisect
import json
import math
import random
import statistics
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import MIN_QUESTIONS, append, load  # noqa: E402
from finetune.look import hint_spans as hs  # noqa: E402

WINDOW = 4096
CUTOFFS = (2048, 3072, 4096, 5120, 6144)
BAND = 512
BIN = 256
MAX_D = 8192
N_BOOT = 20000
SUMMARY = CODE / "results" / "summaries" / "trackA" / "window_reach.json"
PROBES = CODE / "results" / "trackA" / "window_reach_probes.jsonl.gz"


def outcome(probe, hint, own):
    """(log p(hint) - log p(own), whether either letter was outside the top 10)."""
    ph, po, floor = probe["probs"].get(hint), probe["probs"].get(own), probe["floor"] or 1e-12
    return math.log(ph if ph is not None else floor) - math.log(po if po is not None else floor), \
        ph is None or po is None


def distances(tok, src, probe_rec):
    """Per probe k: (answer position, d_mention, d_prompt), from one tokenization of the whole run."""
    from finetune.look import deletion as dl
    from finetune.look import before_takeover as bt
    reasoning, prompt = src["reasoning_text"], src["rendered_prompt"]
    lay = hs.layout(tok, src, reasoning)
    starts = [a for a, _ in lay["offsets"]]
    n_force = len(hs.tokenize(tok, hs.FORCE)[0])
    hint_end = max(lay["hint"])
    ends = probe_rec["sentence_ends"]
    pat = dl.hint_pattern(src["condition"])
    mention = [bool(pat.search(s)) for s in bt.sentences(reasoning, ends)]

    def tokens_before(char):                                        # tokens that start before this character
        return bisect.bisect_left(starts, len(prompt) + char)
    last_tok = [tokens_before(e) - 1 for e in ends]                 # last token of each sentence
    out, latest = {}, None
    for k in range(len(ends) + 1):
        if k and mention[k - 1]:
            latest = last_tok[k - 1]
        pos = tokens_before(ends[k - 1] if k else 0) + n_force - 1
        out[k] = (pos, pos - (latest if latest is not None else hint_end), pos - hint_end)
    return out


def rows_for(tok, runs, sources, key_for_ties=None):
    """One row per probe of the hinted runs with a usable own answer. key_for_ties ({question: answer
    key}): only the runs whose question's no-hint runs split, with the answer key as the own answer."""
    rows, skipped = [], {"no own answer": 0, "own answer is the hint letter": 0}
    for rec in runs:
        if rec["kind"] == "no hint":
            continue
        own, hint = rec.get("own_letter"), rec["hint_letter"]
        if key_for_ties is not None:
            if own is not None:
                continue
            own = key_for_ties[rec["item_id"]]
        if own is None or own == hint:
            skipped["no own answer" if own is None else "own answer is the hint letter"] += 1
            continue
        d = distances(tok, sources[rec["source_run_id"]], rec)
        for p in rec["curve"]:
            pos, dm, dp = d[p["k"]]
            y, bounded = outcome(p, hint, own)
            rows.append({"run": rec["source_run_id"], "q": rec["item_id"], "kind": rec["kind"],
                         "condition": rec["condition"], "arm": rec.get("arm"), "k": p["k"], "pos": pos,
                         "d_mention": dm, "d_prompt": dp, "log_odds": y, "bounded": bounded})
    return rows, skipped


def run_steps(rows, key, cutoff, band=BAND):
    """{question: [per-run mean outside - mean inside]} for one distance and cutoff."""
    by_run = {}
    for r in rows:
        d = r[key]
        side = "in" if cutoff - band <= d < cutoff else ("out" if cutoff <= d < cutoff + band else None)
        if side:
            by_run.setdefault((r["q"], r["run"]), {"in": [], "out": []})[side].append(r["log_odds"])
    out = {}
    for (q, _), s in by_run.items():
        if s["in"] and s["out"]:
            out.setdefault(q, []).append(statistics.mean(s["out"]) - statistics.mean(s["in"]))
    return out


def boot(steps_by_cutoff, n=N_BOOT, seed=0):
    """Means per cutoff and the 4,096 step minus the mean of the placebos, each with a 95% bootstrap
    clustered by question (one resample of questions serves every cutoff)."""
    qs = sorted({q for g in steps_by_cutoff.values() for q in g})

    def stats(sample):
        m = {}
        for c, g in steps_by_cutoff.items():
            vals = [v for q in sample for v in g.get(q, [])]
            m[c] = statistics.mean(vals) if vals else None
        plac = [m[c] for c in m if c != WINDOW and m[c] is not None]
        m["contrast"] = (m[WINDOW] - statistics.mean(plac)) if m.get(WINDOW) is not None and plac else None
        return m
    point = stats(qs)
    rng = random.Random(seed)
    draws = [stats([rng.choice(qs) for _ in qs]) for _ in range(n)]
    out = {}
    for c in point:
        vals = sorted(d[c] for d in draws if d[c] is not None)
        out[c] = {"mean": point[c], "ci95": [vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]] if vals else None}
    for c, g in steps_by_cutoff.items():
        out[c].update({"runs": sum(len(v) for v in g.values()), "questions": len(g)})
    out["contrast"]["questions"] = len(qs)
    for c in out:                                                 # too few questions: no interval (Oct 26)
        if out[c]["questions"] < MIN_QUESTIONS:
            out[c]["ci95"] = None
    return out


def binned(rows, key):
    """Run-centred mean outcome by distance bin (outcome minus the run's own mean), 0 to MAX_D."""
    mean_of = {}
    for r in rows:
        mean_of.setdefault(r["run"], []).append(r["log_odds"])
    mean_of = {k: statistics.mean(v) for k, v in mean_of.items()}
    bins = {}
    for r in rows:
        if 0 <= r[key] < MAX_D:
            bins.setdefault(r[key] // BIN, []).append(r["log_odds"] - mean_of[r["run"]])
    return [(b * BIN + BIN / 2, statistics.mean(v), len(v)) for b, v in sorted(bins.items())]


def analyse(rows, n_boot=N_BOOT, tie_rows=()):
    res = {}
    for label, subset in (("all", rows), ("without bounded probes", [r for r in rows if not r["bounded"]]),
                          ("followed", [r for r in rows if r["kind"] == "followed"]),
                          ("resisted", [r for r in rows if r["kind"] == "resisted"]),
                          ("with split questions, own = answer key", list(rows) + list(tie_rows))):
        res[label] = {key: {str(c): v for c, v in boot({c: run_steps(subset, key, c) for c in CUTOFFS}, n_boot).items()}
                      for key in ("d_mention", "d_prompt")}
    return res


def figure(rows, res, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(12, 7))
    for col, key in enumerate(("d_mention", "d_prompt")):
        ax = axes[0][col]
        b = binned(rows, key)
        ax.plot([x for x, _, _ in b], [y for _, y, _ in b], marker=".", lw=1)
        for c in CUTOFFS:
            ax.axvline(c, color="black" if c == WINDOW else "grey", lw=1.2 if c == WINDOW else 0.6,
                       ls="-" if c == WINDOW else "--")
        ax.axhline(0, color="grey", lw=0.5)
        ax.set_title(f"{key}: hint vs own log-odds, run-centred", fontsize=10)
        ax.set_xlabel(f"{key} (tokens; {BIN}-token bins; black = the 4,096 window, grey = placebos)")
        ax = axes[1][col]
        st = res["all"][key]
        xs = [str(c) for c in CUTOFFS] + ["contrast"]
        for i, c in enumerate(xs):
            v = st[c]
            if v["mean"] is None or v["ci95"] is None:
                continue
            lo, hi = v["ci95"]
            ax.errorbar([i], [v["mean"]], yerr=[[v["mean"] - lo], [hi - v["mean"]]], fmt="o",
                        color="black" if c in (str(WINDOW), "contrast") else "grey", capsize=3)
        ax.axhline(0, color="grey", lw=0.5)
        ax.set_xticks(range(len(xs)), [f"{c}\n({st[c].get('runs', '')} runs)" if c != "contrast" else
                                       "4,096 minus\nplacebo mean" for c in xs], fontsize=8)
        ax.set_title(f"{key}: step at each cutoff ({BAND} tokens out minus in)", fontsize=10)
    axes[0][0].set_ylabel("log-odds, run-centred")
    axes[1][0].set_ylabel("step in log-odds (95% CI, by question)")
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(path.with_suffix(f".{ext}"), dpi=150)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="count runs and probes; no tokenizing")
    ap.add_argument("--boot", type=int, default=N_BOOT)
    a = ap.parse_args(argv)
    from finetune import base_format as bf
    from finetune.look import takeover as tk
    from transformers import AutoTokenizer
    runs = tk.current_probes(load(tk.PROBES_OUT))
    hinted = [r for r in runs if r["kind"] != "no hint"]
    print(f"{len(hinted)} hinted Step 3 runs, {sum(len(r['curve']) for r in hinted):,} probes")
    if a.dry_run:
        return None
    sources = {r["run_id"]: r for r in bf.current(load(bf.OUT))}
    tok = AutoTokenizer.from_pretrained("allenai/Olmo-3-7B-Think", local_files_only=True)
    rows, skipped = rows_for(tok, runs, sources)
    keys = {it["question_id"]: it["answer"] for it in bf.questions()}
    tie_rows, _ = rows_for(tok, runs, sources, key_for_ties=keys)
    PROBES.unlink(missing_ok=True)
    for r in rows:
        append(PROBES, r)
    res = analyse(rows, a.boot, tie_rows)
    share = lambda key, lo: sum(r[key] >= lo for r in rows) / len(rows)  # noqa: E731
    summary = {"analysis": "sliding window reach (no calls)", "window": WINDOW, "cutoffs": CUTOFFS, "band": BAND,
               "runs": len({r["run"] for r in rows}), "questions": len({r["q"] for r in rows}), "probes": len(rows),
               "runs_skipped": skipped,
               "split_question_runs_in_the_sensitivity_row": len({r["run"] for r in tie_rows}),
               "bounded_probes": f"{sum(r['bounded'] for r in rows)} of {len(rows)}",
               "probes_beyond_window": {key: round(share(key, WINDOW), 4) for key in ("d_mention", "d_prompt")},
               "steps": res,
               "reading": "step = mean log-odds (hint vs own) just outside minus just inside the cutoff, within runs; "
                          "negative = the hint's pull is weaker once the distance passes the cutoff"}
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=1) + "\n")
    figure(rows, res, SUMMARY.with_suffix(""))
    print(f"{summary['runs']} runs on {summary['questions']} questions, {len(rows):,} probes (skipped: {skipped}); "
          f"letters outside the top 10 in {summary['bounded_probes']} probes")
    print(f"probes with the distance >= 4,096: d_mention {100 * summary['probes_beyond_window']['d_mention']:.1f}%, "
          f"d_prompt {100 * summary['probes_beyond_window']['d_prompt']:.1f}%")
    for label, by_key in res.items():
        for key, st in by_key.items():
            cells = []
            for c in [str(x) for x in CUTOFFS] + ["contrast"]:
                v = st[c]
                ci = (f"[{v['ci95'][0]:+.2f}, {v['ci95'][1]:+.2f}]" if v["ci95"] else "(too few questions)")
                cells.append(f"{c}: " + ("—" if v["mean"] is None else
                                         f"{v['mean']:+.2f} {ci}" + (f" ({v['runs']} runs, {v['questions']} questions)"
                                                                     if "runs" in v else "")))
            print(f"{label:24} {key:9} " + "; ".join(cells))
    print(f"saved {SUMMARY.relative_to(CODE)} (+ .png/.svg) and {PROBES.relative_to(CODE)}")
    return summary


if __name__ == "__main__":
    main()
