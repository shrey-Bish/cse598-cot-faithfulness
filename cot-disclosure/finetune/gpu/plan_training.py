"""Track A on Sol: refit S1's timing and plan the training jobs (no GPU, no model: a login node or the Mac).

  "$TRACKA_PY" finetune/gpu/plan_training.py /scratch/$USER/trackA/timing/timing.jsonl

S1 (finetune/train.py --timing) fit seconds = fixed + per_token x tokens, and the fixed part came out
negative (Oct 28): the cost per token grows with the length (attention over the whole prefix, again
in the recomputation under gradient checkpointing), so a straight line through long and short
examples crosses below zero. The refit, per version: seconds = c1 x tokens + c2 x tokens^2, both
>= 0, through the timed examples (the first, a warm-up, is left out).
Hours for 2 epochs = the fit summed over the training examples' lengths, twice, plus a validation pass
after each epoch (forward only: VAL_SHARE of a training step's time for the same length).
The range: the 5th to 95th percentile of BOOT refits on the timed examples resampled with
replacement, the low end with the validation share at its low value, the high end at its high value.
Lengths: results/summaries/trackA/data/examples_lengths.json (finetune/check_examples.py).

Jobs (decided Oct 28): lora and tags at once, lora_tags after lora, lora_attn3 after tags (afterany).
Each limit = the high end x 1.3, rounded up to 30 minutes (submit.sh does that from --estimate), at
most 8 h; a version that needs more resumes in another job (train.py saves every 25 optimizer steps,
after each epoch, and at Slurm's warning 5 minutes before the limit).
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
LENGTHS = CODE / "results" / "summaries" / "trackA" / "data" / "examples_lengths.json"
VERSIONS = ("lora", "tags", "lora_tags", "lora_attn3")
EPOCHS = 2
VAL_SHARE = (0.25, 0.5)          # a forward pass vs forward + recomputation + backward
BOOT = 2000
SAFETY, MAX_LIMIT_H, ROUND_MIN = 1.3, 8.0, 30
SUBMIT = "cot-disclosure/finetune/gpu/sol/submit.sh"
CHAIN = (("lora", None), ("tags", None), ("lora_tags", "lora"), ("lora_attn3", "tags"))


def latest_rows(path):
    """The newest timing row per version."""
    out = {}
    for line in Path(path).read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["version"]] = r
    return out


def fit(points):
    """(c1, c2) >= 0 for seconds = c1 x k + c2 x k^2, k in thousands of tokens, least squares."""
    xs = [t / 1000 for t, _ in points]
    ys = [s for _, s in points]
    s2, s3, s4 = (sum(x ** p for x in xs) for p in (2, 3, 4))
    sxy, sx2y = sum(x * y for x, y in zip(xs, ys)), sum(x * x * y for x, y in zip(xs, ys))
    det = s2 * s4 - s3 * s3
    if det > 0:
        c1, c2 = (sxy * s4 - sx2y * s3) / det, (s2 * sx2y - s3 * sxy) / det
        if c1 >= 0 and c2 >= 0:
            return c1, c2
    one = (sxy / s2, 0.0) if s2 else (0.0, 0.0)            # the better of the two one-term fits
    two = (0.0, sx2y / s4) if s4 else (0.0, 0.0)
    sse = lambda c: sum((y - c[0] * x - c[1] * x * x) ** 2 for x, y in zip(xs, ys))  # noqa: E731
    return min((max(0.0, one[0]), 0.0), (0.0, max(0.0, two[1])), key=sse)


def seconds(c, tokens):
    k = tokens / 1000
    return c[0] * k + c[1] * k * k


def hours(c, lengths, val_share):
    per_epoch = sum(seconds(c, t) for t in lengths["train"]) + val_share * sum(seconds(c, t) for t in lengths["validation"])
    return EPOCHS * per_epoch / 3600


def percentile(xs, q):
    s = sorted(xs)
    return s[min(len(s) - 1, max(0, round(q * (len(s) - 1))))]


def plan_version(row, lengths, seed=0):
    points = [(e["tokens"], e["seconds"]) for e in row["examples"][1:]]       # the first warms up
    c = fit(points)
    rng = random.Random(seed)
    boots = [fit([rng.choice(points) for _ in points]) for _ in range(BOOT)]
    low = percentile([hours(b, lengths, VAL_SHARE[0]) for b in boots], 0.05)
    high = percentile([hours(b, lengths, VAL_SHARE[1]) for b in boots], 0.95)
    return {"version": row["version"], "timed_examples": len(points), "c1_s_per_1k_tokens": round(c[0], 4),
            "c2_s_per_1k_tokens_squared": round(c[1], 5),
            "hours": round(hours(c, lengths, sum(VAL_SHARE) / 2), 2), "hours_range": [round(low, 2), round(high, 2)],
            "s1_linear_fit": {"seconds_fixed": row.get("seconds_fixed"), "seconds_per_token": row.get("seconds_per_token"),
                              "predicted_hours_2_epochs": row.get("predicted_hours_2_epochs")},
            "peak_memory_gb": row.get("peak_memory_gb")}


def job(high):
    """(--estimate to pass, the limit submit.sh makes of it in minutes, jobs needed) for a version."""
    cap = MAX_LIMIT_H / SAFETY
    est = math.ceil(min(high, cap) * 100) / 100
    if est * SAFETY > MAX_LIMIT_H:
        est = math.floor(cap * 100) / 100
    limit = ROUND_MIN * math.ceil(est * 60 * SAFETY / ROUND_MIN - 1e-9)
    usable = limit / 60 - 5 / 60                     # the last 5 minutes go to the resume checkpoint
    return est, limit, max(1, math.ceil(high / usable))


def plan(timing_path, lengths_path=LENGTHS):
    lengths = json.loads(Path(lengths_path).read_text())
    rows = latest_rows(timing_path)
    out = {"examples": {k: len(v) for k, v in lengths.items()}, "versions": {}, "missing": []}
    for v in VERSIONS:
        if v in rows:
            out["versions"][v] = plan_version(rows[v], lengths)
        else:
            out["missing"].append(v)
    if out["missing"] and out["versions"]:                # no S1 row: the slowest timed version's numbers
        slowest = max(out["versions"].values(), key=lambda p: p["hours_range"][1])
        for v in out["missing"]:
            out["versions"][v] = {**slowest, "version": v, "from": slowest["version"]}
    for p in out["versions"].values():
        p["estimate"], p["limit_min"], p["jobs"] = job(p["hours_range"][1])
    return out


def commands(res):
    lines = ["# batch 2 (Oct 28): lora and tags now, lora_tags after lora, lora_attn3 after tags (afterany)"]
    for v, after in CHAIN:
        p = res["versions"][v]
        dep = f" --dependency=afterany:<{after} job>" if after else ""
        lim = f"{p['limit_min'] // 60}:{p['limit_min'] % 60:02d}"
        lines.append(f"{SUBMIT} train --estimate {p['estimate']:.2f}{dep} -- {v}"
                     f"     # limit {lim}; {p['hours_range'][0]:.1f}-{p['hours_range'][1]:.1f} h"
                     + (f"; {p['jobs']} jobs: resubmit the same line after it ends" if p["jobs"] > 1 else "")
                     + ("" if after else f"  -> <{v} job>"))
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("timing", help="S1's timing.jsonl")
    ap.add_argument("--lengths", default=str(LENGTHS))
    ap.add_argument("--json", help="also write the plan here (numbers only)")
    a = ap.parse_args()
    res = plan(a.timing, a.lengths)
    print(f"{res['examples']['train']} training and {res['examples']['validation']} validation examples, {EPOCHS} epochs")
    print("| version | S1 line: fixed s, s/token, h | refit c1 (s/1k tok), c2 (s/(1k tok)^2) | hours | range | peak GB | limit | jobs |")
    print("|---|---|---|---|---|---|---|---|")
    for v, p in res["versions"].items():
        s1 = p["s1_linear_fit"]
        f = lambda x, d: "—" if x is None else f"{x:.{d}f}"  # noqa: E731
        print(f"| {v}{' (from ' + p['from'] + ')' if p.get('from') else ''} | {f(s1['seconds_fixed'], 1)}, "
              f"{f(s1['seconds_per_token'], 5)}, {f(s1['predicted_hours_2_epochs'], 2)} | {p['c1_s_per_1k_tokens']}, "
              f"{p['c2_s_per_1k_tokens_squared']} | {p['hours']} | {p['hours_range'][0]}–{p['hours_range'][1]} | "
              f"{f(p['peak_memory_gb'], 1)} | {p['limit_min'] // 60}:{p['limit_min'] % 60:02d} | {p['jobs']} |")
    if res["missing"]:
        print(f"no S1 timing for {', '.join(res['missing'])}: the slowest timed version's numbers are used")
    print()
    print("\n".join(commands(res)))
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
