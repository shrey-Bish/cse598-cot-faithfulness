"""Track A, Steps 6 + 7 together, in chunks, until enough questions are kept.

  python finetune/run_steps67.py --dry-run --kept 240                 # what it would run; no calls
  python finetune/run_steps67.py --kept 240 --checkpoint 100          # run (resumable)
  python finetune/run_steps67.py --report                             # the state so far; no calls
  python finetune/run_steps67.py --assemble                           # the training set; no calls

Each chunk: the next CHUNK pool questions not yet run (finetune/data/pool.jsonl) -> Step 6, 3
no-hint runs each (32,768 tokens in all) -> the questions kept (all 3 answered and correct) ->
their records (build_dataset's per-channel plan: one wrong hint per channel + 1 or 2 correct;
about 10% of questions in validation) -> Step 7 with prefill targets (make_targets).
At --checkpoint kept questions it writes a report (keep rate, Step 7 pass rate by channel and
hint type, target lengths by source next to the held-out questions, final-answer stance) to
results/trackA/steps67_report.jsonl and stops (exit 3) if a rate is off by more than half from
the pilot's; otherwise it goes on to --kept, then reports again.
--assemble writes the training set: the Step 7 examples of the kept questions plus no-hint
examples (10% of the set, from Step 6's kept runs, no calls), dropping examples over 32,768
tokens and, if they are under 10% of the hinted ones, examples whose final answer says neither
that it disagrees nor that it agrees after checking.
"""
import argparse
import json
import math
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import append, latest, load, wilson  # noqa: E402
from finetune import base_format as bf  # noqa: E402
from finetune import build_dataset as bd  # noqa: E402
from finetune import make_targets as mt  # noqa: E402
from finetune import run_nohint as rn  # noqa: E402

CHUNK = 40
REPORT = CODE / "results" / "trackA" / "steps67_report.jsonl"
TRAIN_SET = CODE / "finetune" / "data" / "train_examples.jsonl.gz"
VALIDATION_SET = CODE / "finetune" / "data" / "validation_examples.jsonl.gz"
SET_MANIFEST = CODE / "finetune" / "data" / "examples_manifest.json"
NOHINT_SHARE = 0.10
NEITHER_LIMIT = 0.10
# The pilots (2026-10-25): Step 6 kept 5 of 10; Step 7 prefill passed (within 4 samples) per channel x hint type.
PILOT = {"keep": 0.5, ("user", False): 1.0, ("user", True): 1.0, ("tool_pasted", False): 0.8,
         ("tool_pasted", True): 1.0, ("tool_injected", False): 0.8, ("tool_injected", True): 1.0}


def ran(rows):
    """Questions whose 3 no-hint runs are all saved and ok."""
    by_q = Counter(r["item_id"] for r in rows if r["status"] == "ok")
    return {q for q, n in by_q.items() if n >= rn.RUNS}


def records_for(kept):
    rows = []
    for q, target, rs in kept:
        extra = {"no_hint_runs": [r["parsed_letter"] for r in rs], "target_rule": "all_correct", "record_plan": "per_channel"}
        rows += bd.per_channel(bd.split_of(q["item_id"]), q, target, "pinned-format no-hint runs, all correct", extra,
                               bd.CORRECT_RATIO, bd.SEED)
    return rows


def state(pool):
    nh = latest(load(rn.OUT))
    done = ran(nh)
    asked = [q for q in pool if q["item_id"] in done]
    kept = mt.kept_questions(asked)
    return nh, asked, kept


def heldout_lengths():
    rows = [r for r in bf.current(load(bf.OUT)) if r["status"] == "ok" and r["finish_reason"] != "length"]
    return [r["usage"]["prompt_tokens"] + r["usage"]["completion_tokens"] for r in rows]


def lengths_line(name, xs):
    if not xs:
        return f"| {name} | 0 | — | — | — | — |"
    xs = sorted(xs)
    return (f"| {name} | {len(xs)} | {statistics.median(xs):,.0f} | {statistics.mean(xs):,.0f} | "
            f"{xs[int(0.9 * (len(xs) - 1))]:,} | {max(xs):,} |")


def rate(k, n):
    if not n:
        return "0 of 0"
    lo, hi = wilson(k, n)
    return f"{k} of {n} [{100 * lo:.0f}, {100 * hi:.0f}%]"


def report(pool, label="report", show_neither=5):
    nh, asked, kept = state(pool)
    kept_ids = {q["item_id"] for q, _, _ in kept}
    examples = [e for e in {e["record_id"]: e for e in load(mt.OUTPUTS[mt.PREFILL][2])}.values()
                if e["item_id"] in kept_ids]
    samples = [s for s in latest(load(mt.OUTPUTS[mt.PREFILL][0])) if s["status"] == "ok" and s["item_id"] in kept_ids]
    keep = len(kept) / len(asked) if asked else 0
    off = []
    if asked and (keep < PILOT["keep"] / 2 or keep > PILOT["keep"] * 1.5):
        off.append(f"keep rate {keep:.0%} (pilot {PILOT['keep']:.0%})")
    print(f"=== {label}: {len(asked)} questions run in Step 6, {len(kept)} kept: {rate(len(kept), len(asked))} "
          f"(pilot 5 of 10); by set: {dict(Counter(q['question_set'] for q, _, _ in kept))} kept of "
          f"{dict(Counter(q['question_set'] for q in asked))}")
    print("\n| channel | hint | records | a prefill target within 4 samples | first sample | samples per record | pilot |")
    print("|---|---|---|---|---|---|---|")
    passes = {}
    for c in bd.TRAIN_CHANNELS:
        for correct in (False, True):
            g = mt.group_stats(samples, examples, c, correct)
            r = g["passed"] / g["records"] if g["records"] else None
            passes[(c, correct)] = r
            if r is not None and r < PILOT[(c, correct)] / 2:
                off.append(f"{c} {'correct' if correct else 'wrong'} hint: {r:.0%} (pilot {PILOT[(c, correct)]:.0%})")
            print(f"| {c} | {'correct' if correct else 'wrong'} | {g['records']} | {rate(g['passed'], g['records'])} | "
                  f"{rate(g['first'], g['n_first'])} | {g['per_record']:.2f} | {PILOT[(c, correct)]:.0%} |")
    print(f"why samples failed: {dict(Counter(s['why_not'] for s in samples if not s['pass']))}")
    print("\nTarget length (prompt + target, tokens) by source, next to the held-out questions (Step 2b, prompt + reply):")
    print("| source | examples | median | mean | 90th percentile | max |")
    print("|---|---|---|---|---|---|")
    for qs in sorted({e["question_set"] for e in examples}):
        print(lengths_line(qs, [e["tokens"] for e in examples if e["question_set"] == qs]))
    print(lengths_line("all training targets", [e["tokens"] for e in examples]))
    print(lengths_line("held-out (Step 2b, answered)", heldout_lengths()))
    stances = Counter((e["hint_correct"], mt.target_stance(e)) for e in examples)
    hinted = sum(stances.values())
    neither = [e for e in examples if mt.target_stance(e) == "neither"]
    print(f"\nFinal-answer stance after the opener (keyword count): wrong hint "
          f"{ {k[1]: v for k, v in stances.items() if not k[0]} }, correct hint "
          f"{ {k[1]: v for k, v in stances.items() if k[0]} }; neither {len(neither)} of {hinted} "
          f"({len(neither) / max(1, hinted):.0%})")
    for e in neither[:show_neither]:
        final = e["target_raw"].split("</think>", 1)[-1]
        print(f"  neither: {e['record_id']} ({e['hint_channel']}, {'correct' if e['hint_correct'] else 'wrong'} hint): "
              f"\"{' '.join(final.split())[:300]}\"")
    t6 = [r["gen_seconds"] for r in nh if r["status"] == "ok"]
    t7 = [s["gen_seconds"] for s in samples]
    print(f"\nVoyager time so far: Step 6 {sum(t6) / 4 / 3600:.1f} h ({statistics.mean(t6):.0f} s a run), Step 7 "
          f"{sum(t7) / 4 / 3600:.1f} h ({statistics.mean(t7) if t7 else 0:.0f} s a sample), 4 in flight")
    out = {"timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "label": label,
           "questions_run": len(asked), "kept": len(kept), "keep_rate": keep,
           "pass_rates": {f"{c}|{'correct' if x else 'wrong'}": v for (c, x), v in passes.items()},
           "examples": len(examples), "neither": len(neither), "hinted": hinted, "off_by_more_than_half": off}
    append(REPORT, out)
    if off:
        print(f"\nOFF BY MORE THAN HALF FROM THE PILOT: {off}")
    return out


def run(pool, target, checkpoint, chunk=None):
    chunk = chunk or CHUNK
    checked = any(r["label"] == "checkpoint" for r in load(REPORT))
    while True:
        nh, asked, kept = state(pool)
        if len(kept) >= target:
            break
        done = {q["item_id"] for q in asked}
        todo = [q for q in pool if q["item_id"] not in done][:chunk]
        if not todo:
            print(f"the pool is used up: {len(kept)} kept of {len(asked)}")
            break
        print(f"--- chunk: {len(todo)} questions ({len(kept)} kept so far, target {target})", flush=True)
        rn.run(todo)
        _, _, kept_now = state(pool)
        new = [k for k in kept_now if k[0]["item_id"] in {q["item_id"] for q in todo}]
        if new:
            mt.run(records_for(new), {q["item_id"]: rs[0] for q, _, rs in new}, method=mt.PREFILL)
        if not checked and len(kept_now) >= checkpoint:
            checked = True
            if report(pool, "checkpoint")["off_by_more_than_half"]:
                print("stopping: a rate is off by more than half from the pilot")
                return 3
    report(pool, "final")
    return 0


def assemble(pool, seed=bd.SEED):
    """The training set: Step 7 examples of the kept questions + no-hint examples (10% of the set)."""
    _, asked, kept = state(pool)
    kept_ids = {q["item_id"] for q, _, _ in kept}
    examples = [e for e in {e["record_id"]: e for e in load(mt.OUTPUTS[mt.PREFILL][2])}.values() if e["item_id"] in kept_ids]
    too_long = [e for e in examples if e["dropped_for_length"]]
    examples = [e for e in examples if not e["dropped_for_length"]]
    neither = [e for e in examples if mt.target_stance(e) == "neither"]
    share = len(neither) / max(1, len(examples))
    dropped_neither = share < NEITHER_LIMIT
    if dropped_neither:
        examples = [e for e in examples if mt.target_stance(e) != "neither"]
    n_nohint = round(len(examples) * NOHINT_SHARE / (1 - NOHINT_SHARE))
    nohint = [e for e in mt.nohint_examples(kept, n_nohint, seed) if not e["dropped_for_length"]]
    for e in nohint:
        e["split"] = bd.split_of(e["item_id"], seed)
    for e in examples:
        e["split"] = bd.split_of(e["item_id"], seed)
        e["stance"] = mt.target_stance(e)
    rows = examples + nohint
    import gzip
    for path, split in ((TRAIN_SET, "train"), (VALIDATION_SET, "validation")):
        with gzip.open(path, "wt") as f:
            for e in rows:
                if e["split"] == split:
                    f.write(json.dumps(e) + "\n")
    manifest = {"questions_run": len(asked), "kept": len(kept), "examples": len(rows),
                "by_split": dict(Counter(e["split"] for e in rows)),
                "by_method": dict(Counter(e["target_method"] for e in rows)),
                "by_channel": dict(Counter(f"{e['hint_channel']}|{e.get('hint_correct')}" for e in rows)),
                "dropped_over_32768": len(too_long), "neither": len(neither), "neither_share": round(share, 3),
                "neither_dropped": dropped_neither, "nohint_examples": len(nohint),
                "tokens_median": statistics.median(e["tokens"] for e in rows) if rows else None}
    SET_MANIFEST.write_text(json.dumps(manifest, indent=1) + "\n")
    print(json.dumps(manifest, indent=1))
    if not dropped_neither:
        print(f"'neither' is {share:.0%} of the hinted examples (>= {NEITHER_LIMIT:.0%}): kept, waiting for your decision")
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--kept", type=int, default=240)
    ap.add_argument("--checkpoint", type=int, default=100)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--assemble", action="store_true")
    a = ap.parse_args()
    pool = rn.questions()
    if a.report:
        return report(pool)
    if a.assemble:
        return assemble(pool)
    _, asked, kept = state(pool)
    need = max(0, a.kept - len(kept))
    keep = PILOT["keep"]
    est_q = math.ceil(need / keep)
    print(f"pool {len(pool)} questions; {len(asked)} run, {len(kept)} kept; need {need} more kept: about {est_q} more "
          f"questions at the pilot's keep rate, {3 * est_q} Step 6 calls and about {need * 4.5 * 1.43 * 2:.0f} Step 7 "
          f"requests; chunks of {CHUNK}; checkpoint report at {a.checkpoint} kept")
    if a.dry_run:
        return
    sys.exit(run(pool, a.kept, a.checkpoint))


if __name__ == "__main__":
    main()
