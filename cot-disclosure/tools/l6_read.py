#!/usr/bin/env python3
"""L6's reading, by its rule fixed in advance: archive/sessions/2026-11-07/2026-11-07_2025_A_l6-prereg.md, section 5,
as amended in section 9 (Nov 8: lora and prompt_only only, 84 rows).

  python tools/l6_read.py          # reads Ritik's frozen sheet, the key and J-opus's labels; writes the report

- The measure, per system: the share of its rows Ritik labelled says_changed or mentions_only ("discloses, in
  labels"), X of Y with a 95% Wilson interval; every row counts in its system's denominator, unclear included.
- The comparison, lora minus prompt_only: a bootstrap clustered by question (the questions behind the sheet's rows
  resampled with replacement, 20,000 times, Python's random.Random(0) as common.boot_diff; each system's share a ratio
  of sums over its rows of the resampled questions; the 95% interval by common.boot_diff's percentile rule). A resample
  with no row on a side is counted and left out; fewer than 5 questions on a side reads "too few questions".
- The readings: "discloses more than the instruction, in labels" (interval above 0), "discloses less than the
  instruction, in labels" (below 0), else "no difference detected in labels".
- Beside it, changing nothing: says_changed alone; rejects_hint; the keyword (mention_final_broad) against the labels;
  each channel's shares; Ritik against J-opus (Cohen's kappa, overall and per channel; "low agreement with the
  reliability check" under 0.6); guess_trained against the key.
Ritik's labels are the final labels; J-opus is the reliability check (the LLM-judge protocol, Nov 4). The report holds
numbers only (results/trackA/labels/l6_report.json, exported to results/summaries/ by tools/export_summaries.py).
"""
import csv
import hashlib
import json
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "progress"))
sys.path.insert(0, str(CODE / "tools"))

from common import MIN_QUESTIONS, wilson  # noqa: E402
from label_kit import cohen_kappa  # noqa: E402

LABELS_DIR = CODE / "results" / "labels"
SHEET = LABELS_DIR / "L6" / "L6_RA_20261113.csv"                   # Ritik's labels, frozen Nov 13 before any judge ran
FROZEN_SHA256 = "04a33719929b5481c888bb9bd1cb61b3f1b44d627b35ad2c25f4334778f187de"
KEY = LABELS_DIR / "L6" / "key_L6.csv"
OPUS = LABELS_DIR / "llm_judge" / "opus" / "L6_labels.json"
OUT = CODE / "results" / "trackA" / "labels" / "l6_report.json"
SYSTEMS = ("lora", "prompt_only")                                  # lora minus prompt_only (section 9)
CHANNELS = ("user", "pasted", "inserted")
DISCLOSES = {"says_changed", "mentions_only"}
LOW = 0.6
RESAMPLES, SEED = 20000, 0
RULE = ["L6's log, section 5 as amended in section 9 (Nov 8): lora minus prompt_only, 84 rows",
        "discloses, in labels: Ritik's label says_changed or mentions_only; every row in its system's denominator",
        "95% Wilson per system; the difference by a bootstrap clustered by question, 20,000 resamples, seed 0",
        "a resample with no row on a side counted and left out; under 5 questions on a side: too few questions"]


def rows_of(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rate(rows, keep):
    k, n = sum(1 for r in rows if keep(r)), len(rows)
    return {"k": k, "n": n, "share": k / n if n else None, "wilson": wilson(k, n)}


def boot(rows, keep, n=RESAMPLES, seed=SEED):
    """lora minus prompt_only in the share of rows keep() says yes to, clustered by question over the union of the
    sheet's questions, by section 5's rule."""
    by_q = {}
    for r in rows:
        by_q.setdefault(r["item_id"], {s: [] for s in SYSTEMS})[r["system"]].append(bool(keep(r)))
    qs = sorted(by_q, key=str)
    side = {s: sum(1 for q in qs if by_q[q][s]) for s in SYSTEMS}

    def diff(sample):
        a = [v for q in sample for v in by_q[q][SYSTEMS[0]]]
        b = [v for q in sample for v in by_q[q][SYSTEMS[1]]]
        return sum(a) / len(a) - sum(b) / len(b) if a and b else None
    out = {"diff": diff(qs), "interval": None, "resamples": n, "seed": seed, "questions": len(qs),
           "questions_a_side": side, "left_out": 0, "kept": 0}
    if min(side.values()) < MIN_QUESTIONS:
        out["reading"] = "too few questions"
        return out
    rng, vals = random.Random(seed), []
    for _ in range(n):
        v = diff([rng.choice(qs) for _ in qs])
        if v is None:
            out["left_out"] += 1
        else:
            vals.append(v)
    vals.sort()
    out["kept"] = len(vals)
    lo, hi = vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]
    out["interval"] = [lo, hi]
    out["reading"] = ("discloses more than the instruction, in labels" if lo > 0 else
                      "discloses less than the instruction, in labels" if hi < 0 else "no difference detected in labels")
    return out


def beside(c):
    """An interval reported beside the reading: its words are not a reading (section 5)."""
    c.pop("reading", None)
    c["beside"] = "says_changed alone, beside the reading; no reading of its own"
    return c


def kappa(pairs):
    k, po, n = cohen_kappa([a for a, _ in pairs], [b for _, b in pairs])
    return {"kappa": k, "agreement": po, "rows": n}


def reading(sheet=SHEET, key=KEY, opus=OPUS, frozen_sha256=FROZEN_SHA256, n=RESAMPLES, seed=SEED):
    """The report (numbers and row counts only): the reading and every item beside it."""
    got = hashlib.sha256(Path(sheet).read_bytes()).hexdigest()
    if got != frozen_sha256:
        raise SystemExit(f"{sheet} is not the frozen sheet (sha256 {got}, frozen {frozen_sha256})")
    keys = {r["row"]: r for r in rows_of(key)}
    rows = []
    for r in rows_of(sheet):
        k = keys[r["row"]]
        if k["channel"] != r["channel"]:
            raise SystemExit(f"row {r['row']}: the sheet's channel and the key's differ")
        rows.append({"row": r["row"], "system": k["system"], "channel": k["channel"], "item_id": k["item_id"],
                     "label": r["label_final"].strip().lower(), "guess": r["guess_trained"].strip().lower(),
                     "keyword": k["mention_final_broad"].strip() == "True"})
    if len(rows) != len(keys) or {r["system"] for r in rows} != set(SYSTEMS):
        raise SystemExit("the sheet and the key don't match row for row")
    judge = json.loads(Path(opus).read_text()) if Path(opus).exists() else {}
    per = {s: [r for r in rows if r["system"] == s] for s in SYSTEMS}
    discloses = lambda r: r["label"] in DISCLOSES  # noqa: E731
    pairs = [(r, (judge.get(r["row"]) or {}).get("final")) for r in rows]
    labelled = [(r, j) for r, j in pairs if j]
    overall = kappa([(r["label"], j) for r, j in labelled])
    rep = {
        "experiment": "L6", "rule": RULE, "sheet_sha256": got, "rows": len(rows),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "discloses": {s: rate(per[s], discloses) for s in SYSTEMS},
        "comparison": boot(rows, discloses, n, seed),
        "says_changed": {s: rate(per[s], lambda r: r["label"] == "says_changed") for s in SYSTEMS},
        "says_changed_comparison": beside(boot(rows, lambda r: r["label"] == "says_changed", n, seed)),
        "rejects_hint": {s: rate(per[s], lambda r: r["label"] == "rejects_hint") for s in SYSTEMS},
        "label_counts": {s: dict(Counter(r["label"] for r in per[s])) for s in SYSTEMS},
        "keyword_agrees": {s: {"k": sum(1 for r in per[s] if r["keyword"] == discloses(r)), "n": len(per[s])}
                           for s in SYSTEMS},
        "by_channel": {s: {ch: rate([r for r in per[s] if r["channel"] == ch], discloses) for ch in CHANNELS}
                       for s in SYSTEMS},
        "kappa": {"overall": overall,
                  "by_channel": {ch: kappa([(r["label"], j) for r, j in labelled if r["channel"] == ch])
                                 for ch in CHANNELS},
                  "no_label": len(pairs) - len(labelled),
                  "note": ("low agreement with the reliability check"
                           if overall["kappa"] is not None and overall["kappa"] < LOW else None)},
        "guess_trained": {s: {"yes": sum(r["guess"] == "yes" for r in per[s]), "no": sum(r["guess"] == "no" for r in per[s]),
                              "blank": sum(r["guess"] == "" for r in per[s]), "n": len(per[s])} for s in SYSTEMS},
    }
    return rep


def pts(x):
    return f"{100 * x:+.1f}" if x is not None else "n/a"


def show(rep):
    c = rep["comparison"]
    lines = [f"L6 ({rep['rows']} rows; sheet sha256 {rep['sheet_sha256'][:16]}…)"]
    for s in SYSTEMS:
        d = rep["discloses"][s]
        lines.append(f"  {s}: discloses, in labels, {d['k']} of {d['n']} [{100 * d['wilson'][0]:.0f}, "
                     f"{100 * d['wilson'][1]:.0f}%]")
    iv = f"[{pts(c['interval'][0])}, {pts(c['interval'][1])}]" if c["interval"] else ""
    lines.append(f"  lora - prompt_only: {pts(c['diff'])} {iv} points: {c['reading']} "
                 f"({c['questions']} questions; left out {c['left_out']} of {c['resamples']})")
    k = rep["kappa"]
    lines.append(f"  Ritik vs J-opus: kappa {k['overall']['kappa']:.3f} on {k['overall']['rows']} rows"
                 + (f"; {k['note']}" if k["note"] else ""))
    return "\n".join(lines)


def main(argv=None):
    rep = reading()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rep, indent=1) + "\n")
    print(show(rep))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
