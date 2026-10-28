"""The hand-labeling kit (docs/progress/LABELING_GUIDE.md): the 10 replacement rows, two blank rater
sheets, and Cohen's kappa. No model calls; no labels are filled in here.

  python tools/label_kit.py build        # -> results/labels/ (gitignored: the sheets hold model text)
  python tools/label_kit.py kappa results/labels/rater1.csv results/labels/rater2.csv

build:
  - the queue (docs/progress/LABEL_QUEUE.csv) has 10 rows whose text was never saved (pilot runs of
    Oct 1-2). They are replaced, with no calls (decided Oct 27), by a seeded random draw (SEED) of
    hinted runs with saved text that are not in the queue: first the pilot replay's wrong-hint runs
    (results/progress/pilot_replay.jsonl; only 7 exist outside the queue), then Test 2's hinted runs
    (results/progress/expB_cued.jsonl) for the rest. Each replacement names the row it replaces.
  - results/labels/queue_full.csv: the 91 rows with text + the 10 replacements (keyword columns kept)
  - results/labels/rater1.csv, rater2.csv: the same rows, keyword and outcome columns hidden, label
    columns blank (private: n/a where the model returns no private reasoning)
  - results/labels/key.csv: row -> run, source, keyword pre-sort, whether the answer followed the hint
  - the tracked queue's 10 rows get "replaced by <run_id>" (ids only; their text stays in the kit)
kappa: Cohen's kappa per text (private reasoning, final answer), overall and by hint channel (user /
tool, and Track B's user / tool_pasted / tool_real / system), with the disagreements listed by row.

  python tools/label_kit.py trackb       # -> results/labels/trackB/ (gitignored)

trackb: Track B's batch, in the order to label (decided Oct 28: the F15/F16 contrast first): group 1,
Qwen3 30B Thinking's runs that followed the hint after a real call or with the pasted block; group 2,
the same for Qwen3 30B Instruct. Within a group the two channels are mixed in a seeded order. The
sheets carry the whole final answer and the private reasoning around its first hint keyword (as in
the queue); the key holds the keyword flags. Runs as the Track B report counts them.
"""
import argparse
import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import latest, load  # noqa: E402

QUEUE = CODE.parent / "docs" / "progress" / "LABEL_QUEUE.csv"
OUT = CODE / "results" / "labels"
REPLAY = CODE / "results" / "progress" / "pilot_replay.jsonl"
CUED = CODE / "results" / "progress" / "expB_cued.jsonl"
SEED = 20261027
TRACKB = CODE / "results" / "trackB" / "voyager.jsonl.gz"
TRACKB_GROUPS = (("1 Qwen3 30B Thinking: real call and pasted (F15)", "qwen3-30b-a3b-thinking-2507"),
                 ("2 Qwen3 30B Instruct: real call and pasted (F16)", "qwen3-30b-a3b-instruct-2507"))
LABELS = ("no_mention", "mentions_only", "rejects_hint", "says_changed", "unclear")
HIDDEN = ("keyword_private", "keyword_final", "followed_cue", "answer", "text_status", "source")
PATTERN = {"cue_user": "cue", "cue_tool": "cue_tool", "wrong": "cue"}


def excerpt(text, n=300):
    t = " ".join((text or "").split())
    return t if len(t) <= n else t[:n] + " …"


def around(text, pattern, width=220):
    if not text:
        return ""
    from detect import COMPILED
    m = COMPILED[pattern].search(text)
    return text[:2 * width] if not m else text[max(0, m.start() - width):m.end() + width]


def row_of(r, source, condition, pattern):
    from detect import COMPILED
    pm = bool(COMPILED[pattern].search(r["reasoning_text"] or "")) if r["reasoning_text"] else "n/a"
    return {"source": source, "run_id": r["run_id"], "model": r["model"], "condition": condition,
            "cue_letter": r["cue_letter"], "answer": r["parsed_letter"], "followed_cue": r["parsed_letter"] == r["cue_letter"],
            "keyword_private": pm, "keyword_final": bool(COMPILED[pattern].search(r["final_text"] or "")),
            "private_excerpt": excerpt(around(r["reasoning_text"], pattern)), "final_excerpt": excerpt((r["final_text"] or "")[-600:])}


def replacements(queue, n, seed=SEED):
    """n rows: the pilot replay's wrong-hint runs not in the queue first (seeded order), then Test 2's."""
    have = {r["run_id"] for r in queue}
    rng = random.Random(seed)
    pilot = [r for r in load(REPLAY) if r["condition"] == "wrong" and r["status"] == "ok" and r["run_id"] not in have]
    pilot = rng.sample(pilot, min(n, len(pilot)))
    out = [row_of(r, "cot-disclosure/results/progress/pilot_replay.jsonl", "pilot wrong hint, replacement", "cue")
           for r in pilot]
    if len(out) < n:
        cued = sorted((r for r in latest(load(CUED)) if r["status"] == "ok" and r["run_id"] not in have),
                      key=lambda r: r["run_id"])
        for r in rng.sample(cued, n - len(out)):
            out.append(row_of(r, "cot-disclosure/results/progress/expB_cued.jsonl",
                              f"expB {r['cue_channel']}, replacement", PATTERN[r["cue_channel"]]))
    return out


def build(seed=SEED):
    with open(QUEUE, newline="") as f:
        queue = list(csv.DictReader(f))
    cols = list(queue[0].keys())
    missing = [r for r in queue if not r["text_status"].startswith("saved")]
    if any(r["text_status"].startswith("replaced by") for r in queue):
        sys.exit("the queue's rows are already replaced; the kit is in results/labels/")
    new = replacements(queue, len(missing), seed)
    for old, rep in zip(missing, new):
        rep["text_status"] = f"saved (replacement for {old['run_id']}; no calls; seed {seed})"
        old["text_status"] = f"replaced by {rep['run_id']} (seed {seed}; text in the labeling kit, results/labels/)"
    full = [r for r in queue if r["text_status"].startswith("saved")] + new
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "queue_full.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in full:
            w.writerow({c: r.get(c, "") for c in cols})
    sheet_cols = ["row", "run_id", "model", "condition", "cue_letter", "private_excerpt", "final_excerpt",
                  "label_private", "label_final", "note"]
    for rater in ("rater1", "rater2"):
        with open(OUT / f"{rater}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=sheet_cols)
            w.writeheader()
            for i, r in enumerate(full, 1):
                w.writerow({"row": i, "run_id": r["run_id"], "model": r["model"], "condition": r["condition"],
                            "cue_letter": r["cue_letter"], "private_excerpt": r["private_excerpt"],
                            "final_excerpt": r["final_excerpt"],
                            "label_private": "n/a" if not r["private_excerpt"] else "", "label_final": "", "note": ""})
    with open(OUT / "key.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["row", "run_id", *HIDDEN])
        w.writeheader()
        for i, r in enumerate(full, 1):
            w.writerow({"row": i, "run_id": r["run_id"], **{c: r.get(c, "") for c in HIDDEN}})
    with open(QUEUE, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in queue:
            w.writerow(r)
    (OUT / "kit.json").write_text(json.dumps({"rows": len(full), "replacements": [r["run_id"] for r in new],
                                              "replacement_sources": dict(Counter(r["source"] for r in new)),
                                              "seed": seed, "labels": LABELS}, indent=1) + "\n")
    return len(full), new


def trackb_rows(path=TRACKB, seed=SEED):
    """Track B's batch: per group, the model's runs that followed the hint after a real call or with the
    pasted block, the two channels mixed in a seeded order."""
    import trackB_report as tr
    runs = [r for r in latest(load(path)) if r.get("experiment") == "trackB" and r["status"] == "ok" and tr.counts(r)
            and r["condition"] in ("tool_real", "tool_pasted") and tr.flags(r)["followed"]]
    out = []
    for group, model in TRACKB_GROUPS:
        mine = sorted((r for r in runs if r["model"] == model), key=lambda r: r["run_id"])
        random.Random(f"{seed} {model}").shuffle(mine)
        for r in mine:
            f = tr.flags(r)
            out.append({"group": group, "run_id": r["run_id"], "model": model, "condition": r["condition"],
                        "cue_letter": r["hint_letter"], "item_id": r["item_id"], "set": r["set"],
                        "called_tool": f["called_tool"], "keyword_private": f["mention_private"],
                        "keyword_final": f["mention_final"],
                        "private_excerpt": excerpt(around(r["reasoning_text"], "cue_tool"), 600) if r["reasoning_text"] else "",
                        "final_text": (r["final_text"] or "").strip()})
    return out


def build_trackb(path=TRACKB, out=None, seed=SEED):
    rows = trackb_rows(path, seed)
    out = Path(out or OUT / "trackB")
    out.mkdir(parents=True, exist_ok=True)
    sheet_cols = ["row", "group", "run_id", "model", "condition", "cue_letter", "private_excerpt", "final_text",
                  "label_private", "label_final", "note"]
    for rater in ("rater1", "rater2"):
        with open(out / f"{rater}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=sheet_cols)
            w.writeheader()
            for i, r in enumerate(rows, 1):
                w.writerow({"row": i, **{c: r[c] for c in sheet_cols[1:8]},
                            "label_private": "n/a" if not r["private_excerpt"] else "", "label_final": "", "note": ""})
    key_cols = ["row", "run_id", "group", "item_id", "set", "called_tool", "keyword_private", "keyword_final"]
    with open(out / "key.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=key_cols)
        w.writeheader()
        for i, r in enumerate(rows, 1):
            w.writerow({"row": i, **{c: r[c] for c in key_cols[1:]}})
    sizes = {g: dict(Counter(r["condition"] for r in rows if r["group"] == g)) for g, _ in TRACKB_GROUPS}
    (out / "kit.json").write_text(json.dumps({"rows": len(rows), "groups": sizes, "seed": seed, "labels": LABELS,
                                              "source": str(Path(path).relative_to(CODE) if Path(path).is_relative_to(CODE)
                                                            else path)}, indent=1) + "\n")
    return rows, sizes


def cohen_kappa(a, b):
    """(kappa, observed agreement, n) for two equal-length label lists."""
    n = len(a)
    if not n:
        return None, None, 0
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return (1.0 if pe == 1 else (po - pe) / (1 - pe)), po, n


def channel_of(condition):
    if condition in ("user", "tool_pasted", "tool_real", "system"):            # Track B's channels
        return condition
    return "tool" if "tool" in condition else "user"


def kappa(path1, path2):
    def read(p):
        with open(p, newline="") as f:
            return {r["row"]: r for r in csv.DictReader(f)}
    r1, r2 = read(path1), read(path2)
    out, disagreements = {}, []
    for text in ("private", "final"):
        col = f"label_{text}"
        rows = [k for k in r1 if k in r2 and r1[k][col] in LABELS and r2[k][col] in LABELS]
        for group in ("all", *sorted({channel_of(r1[k]["condition"]) for k in r1})):
            keep = [k for k in rows if group == "all" or channel_of(r1[k]["condition"]) == group]
            k_, po, n = cohen_kappa([r1[k][col] for k in keep], [r2[k][col] for k in keep])
            out[f"{text} | {group}"] = {"kappa": k_, "agreement": po, "rows": n}
        disagreements += [{"row": k, "text": text, "rater1": r1[k][col], "rater2": r2[k][col], "run_id": r1[k]["run_id"]}
                          for k in rows if r1[k][col] != r2[k][col]]
    return out, disagreements


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    sub.add_parser("trackb")
    k = sub.add_parser("kappa")
    k.add_argument("rater1")
    k.add_argument("rater2")
    a = ap.parse_args()
    if a.cmd == "build":
        n, new = build()
        print(f"{n} rows in {OUT.relative_to(CODE)}; replacements: " + ", ".join(r["run_id"] for r in new))
        return
    if a.cmd == "trackb":
        rows, sizes = build_trackb()
        print(f"{len(rows)} rows in {(OUT / 'trackB').relative_to(CODE)}, labeled in this order:")
        for g, s in sizes.items():
            print(f"  {g}: " + ", ".join(f"{c} {n}" for c, n in sorted(s.items())))
        return
    res, dis = kappa(a.rater1, a.rater2)
    print(json.dumps(res, indent=1))
    print(f"{len(dis)} disagreements:")
    for d in dis:
        print(f"  row {d['row']} {d['text']}: {d['rater1']} vs {d['rater2']} ({d['run_id']})")


if __name__ == "__main__":
    main()
