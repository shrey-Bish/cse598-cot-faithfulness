"""The demo's example outputs (Nov 13): a few already-labelled rows per section, drawn with a fixed string seed, for the
local demo page only (tools/build_demo.py adds them to results/demo/explainer.html; the tracked docs/demo/explainer.html never
holds them).

  python tools/demo_examples.py        # -> results/demo/examples.json (gitignored; the pre-push check refuses it)

Read-only on every source; writes one file, under results/demo/. Each example carries its sheet's row id, the run id,
the system, the channel, its label as the sheet has it, and "illustrative, drawn by seed". A source that isn't there is
named in "missing" and the rest is written.

  s2 (the bare final answer)       L3: results/labels/L3_RA.csv, Ritik's sheet, rows on the simulated tool block with a
                                   private excerpt: the only labelled sheet that holds the private reasoning beside the
                                   final answer. L3's labels are not the final labels for F3: Gate 2's label part is not
                                   met under the Nov 4 protocol, so F3 stays a keyword count.
  s5 (disclosure when following)   L6: the frozen sheet results/labels/L6/L6_RA_20261113.csv (Ritik's labels, final),
                                   key_L6.csv (system, run id), texts_L6.jsonl (the final text), LoRA's and the
                                   instruction's rows; L4 part 1: results/labels/gate3/L4/L4_part1_RA.csv (Ritik's
                                   labels) with key_L4.csv, LoRA's rows on the 30. Both sheets hold the final answer
                                   only: the private reasoning stays on Sol.

The draw: random.Random(SEED), candidates sorted by row id before each sample, so the same sheets give the same draw.
"""
import argparse
import csv
import json
import random
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
LABELS = CODE / "results" / "labels"
OUT = CODE / "results" / "demo" / "examples.json"
SEED = "cse598-demo-examples-2026-11-13"
ILL = "illustrative, drawn by seed"
SRC = {"L6": ("L6/L6_RA_20261113.csv", "L6/key_L6.csv", "L6/texts_L6.jsonl"),
       "L4": ("gate3/L4/L4_part1_RA.csv", "gate3/L4/key_L4.csv"),
       "L3": ("L3_RA.csv",)}
PER = {("L3", "s2"): 3, ("L6", "lora"): 2, ("L6", "prompt_only"): 2, ("L4", "lora"): 2}
NO_PRIVATE = "not in this sheet: L6 and L4 hold the final answer only (the private reasoning stays on Sol)"
L3_LABELS = "L3, Ritik's sheet; not the final labels for F3 (Gate 2's label part not met; F3 stays a keyword count)"


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def pick(rng, rows, k):
    """k rows by the seed, from the candidates sorted by row id (all of them when there are fewer)."""
    rows = sorted(rows, key=lambda r: int(r["row"]))
    return sorted(rng.sample(rows, min(k, len(rows))), key=lambda r: int(r["row"]))


def have(labels, name, missing):
    paths = [Path(labels) / p for p in SRC[name]]
    gone = [str(p) for p in paths if not p.exists()]
    missing += [f"{name}: {g} not found" for g in gone]
    return None if gone else paths


def l6(labels, rng, missing):
    paths = have(labels, "L6", missing)
    if not paths:
        return []
    sheet, key = {r["row"]: r for r in read_csv(paths[0])}, {r["row"]: r for r in read_csv(paths[1])}
    texts = {}
    with open(paths[2]) as f:
        for line in f:
            if line.strip():
                t = json.loads(line)
                texts[t["run_id"]] = t
    out = []
    for system in ("lora", "prompt_only"):
        rows = [sheet[r] for r, k in key.items() if k["system"] == system and r in sheet]
        for r in pick(rng, rows, PER[("L6", system)]):
            k = key[r["row"]]
            t = texts.get(k["run_id"], {})
            out.append({"section": "s5", "source": "L6", "sheet": SRC["L6"][0], "row": int(r["row"]),
                        "run_id": k["run_id"], "system": system, "channel": k["channel"], "item_id": k["item_id"],
                        "label": r["label_final"], "labels_are": "Ritik's labels, final (L6; frozen Nov 13)",
                        "hint_letter": r["hint_letter"], "parsed_letter": t.get("parsed_letter", ""),
                        "final_answer": t.get("final_text") or r["final_answer"], "private": None,
                        "private_status": NO_PRIVATE, "illustrative": ILL})
    return out


def l4(labels, rng, missing):
    paths = have(labels, "L4", missing)
    if not paths:
        return []
    key = {r["row"]: r for r in read_csv(paths[1]) if str(r["part"]) == "1"}
    rows = [r for r in read_csv(paths[0]) if key.get(r["row"], {}).get("system") == "lora"]
    return [{"section": "s5", "source": "L4", "sheet": SRC["L4"][0], "row": int(r["row"]), "run_id": r["run_id"],
             "system": "lora", "channel": r["channel"], "item_id": key[r["row"]]["item_id"], "label": r["label_final"],
             "labels_are": "Ritik's labels (L4 part 1, Gate 3's 30)", "hint_letter": r["hint_letter"],
             "final_answer": r["final_answer"], "private": None, "private_status": NO_PRIVATE, "illustrative": ILL}
            for r in pick(rng, rows, PER[("L4", "lora")])]


def l3(labels, rng, missing):
    paths = have(labels, "L3", missing)
    if not paths:
        return []
    rows = [r for r in read_csv(paths[0]) if "cue_tool" in r["condition"] and r["private_excerpt"].strip()
            and r["final_excerpt"].strip()]
    return [{"section": "s2", "source": "L3", "sheet": SRC["L3"][0], "row": int(r["row"]), "run_id": r["run_id"],
             "system": r["model"], "channel": "tool, pasted (simulated tool block)", "condition": r["condition"],
             "label": r["label_final"], "label_private": r["label_private"], "labels_are": L3_LABELS,
             "hint_letter": r["cue_letter"], "final_answer": r["final_excerpt"], "private": r["private_excerpt"],
             "private_status": "the sheet's private excerpt", "illustrative": ILL}
            for r in pick(rng, rows, PER[("L3", "s2")])]


def draw(labels=LABELS, out=OUT, seed=SEED):
    """Draw the examples and write them to out (only ever results/demo/<name>.json). Returns what was written."""
    out = Path(out)
    if out.parent.name != "demo" or out.parent.parent.name != "results" or out.suffix != ".json":
        raise ValueError(f"the examples go under results/demo/ only, not {out}")
    rng, missing = random.Random(seed), []
    examples = l3(labels, rng, missing) + l6(labels, rng, missing) + l4(labels, rng, missing)
    res = {"seed": seed, "illustrative": ILL, "missing": missing, "examples": examples}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--labels", default=str(LABELS))
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    res = draw(a.labels, a.out)
    by = {}
    for e in res["examples"]:
        by[(e["source"], e["system"])] = by.get((e["source"], e["system"]), 0) + 1
    print(f"{a.out}: {len(res['examples'])} examples " + ", ".join(f"{s} {m}: {n}" for (s, m), n in by.items()))
    for m in res["missing"]:
        print(f"missing: {m}", file=sys.stderr)


if __name__ == "__main__":
    main()
