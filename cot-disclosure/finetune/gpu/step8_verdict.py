"""Track A, step 8: apply the Oct 26 rule to a step8_checkpoint.json copied back from Sol.

Same checkpoint if all three hold (docs/PLAN.md, Track A; fixed before seeing the result):
  (a) on the first 2,047 tokens, no top-token mismatch except near-ties (the top two within 0.1
      probability), in both the bf16 and the fp32 pass, for every Think reference
  (b) the mean absolute log-prob difference is at least 10 times smaller than the Instruct
      control's, in each dtype (over every compared token; the first-2,047 ratio is shown too)
  (c) the Instruct control clearly fails (a): at least 10 mismatches outside near-ties in its first
      2,047 tokens, in each dtype
Supporting evidence, not pass/fail: the fp32 pass against the old 0.01 max-difference limit.
If (a) fails outside near-ties, Voyager isn't serving this checkpoint.

Files written before the Oct 26 update of checkpoint_check.py list at most 20 first-part mismatches;
the count outside near-ties is then exact when there were 20 or fewer, and a lower bound otherwise.
Also listed: every first-part position outside near-ties, with both sides' probability gaps (which
side is over 0.1, and by how much); the Oct 21 two-part rule's line per dtype, counting the
failures; and, with --sha256sum, the weight files' sha256 on Sol against d97e442's.

  python finetune/gpu/step8_verdict.py                     # results/trackA/gpu/step8_checkpoint.json
  python finetune/gpu/step8_verdict.py PATH --no-save      # another file; write nothing
  python finetune/gpu/step8_verdict.py --sha256sum results/trackA/gpu/weights_sha256.txt
                                                           # + `sha256sum model-*.safetensors` from Sol
Writes the numbers (no text) to results/summaries/trackA/step8_verdict.json.
"""
import argparse
import json
import math
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))

DEFAULT = CODE / "results" / "trackA" / "gpu" / "step8_checkpoint.json"
SUMMARY = CODE / "results" / "summaries" / "trackA" / "step8_verdict.json"
RATIO = 10
CLEARLY = 10
FP32_LIMIT = 0.01
DTYPES = ("bf16", "fp32")
NEAR_TIE = 0.1
REV_FILES = CODE / "finetune" / "gpu" / "olmo3_7b_think_d97e442.json"


def outside_first_part(r):
    """(mismatches outside near-ties in the first 2,047 tokens, exact?)."""
    s = r["strict"]
    if "mismatches_outside_near_ties" in s:
        return s["mismatches_outside_near_ties"], True
    listed = s.get("mismatches") or []
    n = sum(not m.get("near_tie") for m in listed)
    return n, s["top_token_mismatches"] <= len(listed)


def mean_all(r):
    if "all" in r:
        return r["all"]["mean_abs_diff"]
    parts = [(p["positions"], p["mean_abs_diff"]) for p in (r["strict"], r["beyond"]) if p["positions"]]
    return sum(n * m for n, m in parts) / sum(n for n, _ in parts)


def ratio(control, ref):
    return math.inf if not ref else control / ref


def outside_positions(results):
    """Every listed first-part mismatch outside near-ties of the Think references: numbers only (no
    token text). A text echoed through several routes (the Step 1 text: 4 references) counts once
    per position in `distinct`."""
    rows = []
    for dtype in DTYPES:
        for r in results.get(dtype, {}).values():
            if r["control"]:
                continue
            for m in r["strict"].get("mismatches") or []:
                if m.get("near_tie"):
                    continue
                over = {side: g for side, g in (("local", m.get("gap_local")), ("voyager", m.get("gap_voyager")))
                        if g is not None and g >= NEAR_TIE}
                rows.append({"dtype": dtype, "reference": r["name"], "tokens": r["tokens"], "pos": m.get("pos"),
                             "gap_local": m.get("gap_local"), "gap_voyager": m.get("gap_voyager"),
                             "over_0.1_on": sorted(over), "largest_gap": max(over.values()) if over else None,
                             "abs_diff": m.get("diff")})
    distinct = sorted({(r["tokens"], r["pos"]) for r in rows})
    gaps = [r["largest_gap"] for r in rows if r["largest_gap"] is not None]
    return {"rows": rows, "distinct": [{"tokens": t, "pos": p} for t, p in distinct],
            "gap_range": [min(gaps), max(gaps)] if gaps else None}


def oct21_lines(results):
    """The Oct 21 two-part rule's line per dtype, counting the Think references that fail."""
    out = []
    for dtype, res in results.items():
        if not all("pass" in r and "pass_logprobs" in r for r in res.values()):
            continue
        think = [r for r in res.values() if not r["control"]]
        ctrl_failed = all(not r["pass_logprobs"] for r in res.values() if r["control"])
        fails = sum(not r["pass"] for r in think)
        out.append(f"{dtype}: {'PASS' if not fails else 'FAIL'}, {fails} of {len(think)} Think references fail; the "
                   f"Instruct control {'fails, as it must' if ctrl_failed else 'PASSES: the check cannot tell checkpoints apart'}")
    return out


def weights_vs_reference(sha256sum_text):
    """`sha256sum` output for the weight files against olmo3_7b_think_d97e442.json."""
    ref = json.loads(REV_FILES.read_text())
    got = {}
    for line in sha256sum_text.splitlines():
        if line.strip():
            h, name = line.split(None, 1)
            got[Path(name.strip().lstrip("*")).name] = h.lower()
    weights = [n for n in ref["files"] if n.endswith(".safetensors")]
    files = {n: {"sha256": got.get(n), "matches": got.get(n) == ref["files"][n]} for n in weights}
    return {"reference_revision": ref["revision"], "files": files, "all_match": all(f["matches"] for f in files.values())}


def decide(summary):
    """The Oct 26 rule on a Step 8 summary -> numbers, the three conditions, and the decision."""
    results = summary["results"]
    missing = [d for d in DTYPES if d not in results]
    rows, conds = [], {"a": True, "b": True, "c": True}
    undetermined = []
    for dtype in DTYPES:
        if dtype in missing:
            continue
        refs = results[dtype]
        controls = [r for r in refs.values() if r["control"]]
        if len(controls) != 1:
            raise SystemExit(f"{dtype}: expected one Instruct control, found {len(controls)}")
        ctrl = controls[0]
        c_out, c_exact = outside_first_part(ctrl)
        c_all, c_first = mean_all(ctrl), ctrl["strict"]["mean_abs_diff"]
        c_fails = c_out >= CLEARLY
        conds["c"] &= c_fails
        rows.append({"dtype": dtype, "reference": ctrl["name"], "control": True, "tokens": ctrl["tokens"],
                     "first_part_mismatches": ctrl["strict"]["top_token_mismatches"],
                     "outside_near_ties": c_out, "outside_count_exact": c_exact, "mean_abs_diff": c_all,
                     "mean_abs_diff_first_2047": c_first, "c_clearly_fails_a": c_fails})
        for r in refs.values():
            if r["control"]:
                continue
            out, exact = outside_first_part(r)
            a = out == 0 and exact
            if out == 0 and not exact:
                undetermined.append(f"{dtype} {r['name']}")
            b = ratio(c_all, mean_all(r)) >= RATIO
            conds["a"] &= a
            conds["b"] &= b
            row = {"dtype": dtype, "reference": r["name"], "control": False, "tokens": r["tokens"],
                   "first_part_mismatches": r["strict"]["top_token_mismatches"], "outside_near_ties": out,
                   "outside_count_exact": exact, "a_holds": a, "mean_abs_diff": mean_all(r),
                   "mean_abs_diff_first_2047": r["strict"]["mean_abs_diff"],
                   "control_over_this": ratio(c_all, mean_all(r)),
                   "control_over_this_first_2047": ratio(c_first, r["strict"]["mean_abs_diff"]), "b_holds": b,
                   "max_abs_diff_first_2047": r["strict"]["max_abs_diff"],
                   "max_abs_diff_beyond": r["beyond"]["max_abs_diff"]}
            if dtype == "fp32":
                row["fp32_under_0.01_first_2047"] = (r["strict"]["max_abs_diff"] or 0.0) < FP32_LIMIT
            rows.append(row)
    a_failed_outside = any(not r["control"] and r["outside_near_ties"] > 0 for r in rows)
    if missing:
        decision, text = "incomplete", f"no {' / '.join(missing)} pass in the file: rule (a) needs both bf16 and fp32"
    elif a_failed_outside:
        decision, text = "different checkpoint", ("(a) fails outside near-ties: Voyager isn't serving this checkpoint. "
                                                  "Every base number must be re-measured on the GPU before any Phase 6 "
                                                  "planning.")
    elif undetermined:
        decision, text = "undetermined", ("more than 20 first-part mismatches, all listed ones near-ties, in "
                                          f"{', '.join(undetermined)}: rerun Step 8 with the current checkpoint_check.py")
    elif all(conds.values()):
        decision, text = "same checkpoint", "(a), (b) and (c) hold: Voyager serves the checkpoint we load; base numbers stand."
    else:
        failed = [k for k, v in conds.items() if not v]
        decision, text = "inconclusive", (f"(a) holds but ({', '.join(failed)}) does not: the check can't tell checkpoints "
                                          "apart well enough to call it the same checkpoint")
    return {"rule": "Oct 26 (docs/PLAN.md, Track A)", "conditions": conds, "decision": decision, "text": text,
            "rows": rows, "outside_near_ties": outside_positions(results), "oct21_two_part_rule": oct21_lines(results),
            "snapshot_commit": summary.get("snapshot_commit"),
            "thresholds": {"ratio": RATIO, "clearly_fails": CLEARLY, "near_tie": 0.1, "fp32_limit": FP32_LIMIT}}


def show(d):
    print("| dtype | reference | first 2,047: mismatches (outside near-ties) | mean abs diff | control / this | "
          "max diff, first 2,047 | holds |")
    print("|---|---|---|---|---|---|---|")
    for r in d["rows"]:
        out = f"{r['outside_near_ties']}{'' if r['outside_count_exact'] else '+'}"
        if r["control"]:
            print(f"| {r['dtype']} | {r['reference']} (Instruct control) | {r['first_part_mismatches']} ({out}) | "
                  f"{r['mean_abs_diff']:.4f} | — | — | (c) {'yes' if r['c_clearly_fails_a'] else 'NO'} |")
        else:
            extra = f"; under 0.01: {'yes' if r['fp32_under_0.01_first_2047'] else 'no'}" if r["dtype"] == "fp32" else ""
            print(f"| {r['dtype']} | {r['reference']} | {r['first_part_mismatches']} ({out}) | {r['mean_abs_diff']:.4f} | "
                  f"{r['control_over_this']:.0f}x | {r['max_abs_diff_first_2047']:.4f}{extra} | "
                  f"(a) {'yes' if r['a_holds'] else 'NO'}, (b) {'yes' if r['b_holds'] else 'NO'} |")
    o = d.get("outside_near_ties")
    if o and o["rows"]:
        print(f"\nFirst-part mismatches outside near-ties: {len(o['distinct'])} distinct positions, largest gap "
              f"{o['gap_range'][0]:.3f}-{o['gap_range'][1]:.3f} (near-tie: under {NEAR_TIE} on both sides)")
        print("| dtype | reference | position | gap, local | gap, Voyager | over 0.1 on |")
        print("|---|---|---|---|---|---|")
        fmt = lambda g: "—" if g is None else f"{g:.3f}"  # noqa: E731
        for r in o["rows"]:
            print(f"| {r['dtype']} | {r['reference']} | {r['pos']} | {fmt(r['gap_local'])} | {fmt(r['gap_voyager'])} | "
                  f"{', '.join(r['over_0.1_on'])} |")
    if d.get("weights_sha256"):
        w = d["weights_sha256"]
        print(f"\nWeights on Sol (sha256sum) vs {w['reference_revision'][:7]}: " + ", ".join(
            f"{n} {'same' if f['matches'] else 'DIFFERENT'}" for n, f in w["files"].items()))
    print("\nOct 21 two-part rule (reference only): " + "; ".join(d.get("oct21_two_part_rule", [])))
    c = d["conditions"]
    print(f"\n(a) {c['a']}, (b) {c['b']}, (c) {c['c']}  ->  {d['decision'].upper()}: {d['text']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", default=str(DEFAULT))
    ap.add_argument("--no-save", action="store_true")
    ap.add_argument("--sha256sum", metavar="FILE", help="`sha256sum` output for the weight files on Sol")
    a = ap.parse_args(argv)
    d = decide(json.loads(Path(a.path).read_text()))
    if a.sha256sum:
        d["weights_sha256"] = weights_vs_reference(Path(a.sha256sum).read_text())
    show(d)
    if not a.no_save:
        SUMMARY.parent.mkdir(parents=True, exist_ok=True)
        SUMMARY.write_text(json.dumps(d, indent=1) + "\n")
        print(f"saved {SUMMARY.relative_to(CODE)}")
    return d


if __name__ == "__main__":
    main()
