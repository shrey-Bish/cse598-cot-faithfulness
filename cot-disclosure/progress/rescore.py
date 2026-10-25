"""Re-score saved results with today's parser (parse.py) and list every letter that changes. No calls.

  python progress/rescore.py --dry-run     # the files it reads
  python progress/rescore.py               # changes per experiment (appends to results/rescore.jsonl)
  python progress/rescore.py --apply       # also append re-scored copies of changed Track A Step 4 calls

Each experiment is re-parsed with its own rules: the general parser on the final answer
(parse_answer), the reviewer's FINAL line for Experiment A (parse_final), each item's own
number of options, and Track A's gating (a reply cut off at its limit, or one that calls the
tool again, has no answer). Test 1 saved letters but no texts, so it cannot be re-parsed: its
parse failures are counted instead, as the most that could change; its replays (pilot_replay)
are re-parsed.
"""
import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

import experiments as pilot  # noqa: E402
from common import append, load  # noqa: E402
from parse import parse_answer, parse_final  # noqa: E402

RESULTS = CODE / "results"
OUT = RESULTS / "rescore.jsonl"
ITEMS_B = CODE / "data" / "progress" / "mmlupro_30.jsonl"
NO_TEXT = {"Test 1": [RESULTS / "progress.jsonl", RESULTS / "pilot.jsonl", RESULTS / "ladder.jsonl"]}


def n_options():
    """{item id: number of options} for the pilot puzzles (0..23, "pilot-i") and the MMLU-Pro items."""
    n = {i: len(it["options"]) for i, it in enumerate(pilot.ITEMS)}
    n.update({f"pilot-{i}": k for i, k in n.items()})
    for line in open(ITEMS_B):
        it = json.loads(line)
        n[it["question_id"]] = len(it["options"])
    from finetune import base_format as bf
    n.update({it["question_id"]: len(it["options"]) for it in bf.questions()})
    return n


def status(rec, letter):
    """parse_status as common.parse_status sets it."""
    if rec.get("error_type"):
        return None
    if rec.get("finish_reason") == "length":
        return "truncated"
    return "ok" if letter else "parse_failure"


def general(rec, n):
    return parse_answer(rec.get("final_text") or "", n)


def reviewer(rec, n):
    return parse_final(rec.get("final_text") or "", n)


def track_a(rec, n):
    """Step 2b and Step 4: no answer when cut off at the limit or calling the tool again."""
    letter, rule = parse_answer(rec.get("final_text") or "", n)
    if rec.get("finish_reason") == "length" or rec.get("no_answer_reason") in ("still calling the tool",
                                                                                  "called the tool again"):
        return None, rule
    return letter, rule


EXPERIMENTS = [  # (experiment, file, parser)
    ("Test 1 replays (pilot_replay)", RESULTS / "progress" / "pilot_replay.jsonl", general),
    ("Test 2 (Experiment B), no hint", RESULTS / "progress" / "expB_nocue.jsonl", general),
    ("Test 2 (Experiment B), hinted", RESULTS / "progress" / "expB_cued.jsonl", general),
    ("Experiment A, reviewer", RESULTS / "progress" / "expA_reviewer.jsonl", reviewer),
    ("Experiment A, guard re-ask", RESULTS / "progress" / "expA_guard.jsonl", general),
    ("Progress round, timing", RESULTS / "progress" / "timing.jsonl", general),
    ("Progress round, truncation sweep", RESULTS / "progress" / "truncation_sweep.jsonl", general),
    ("Track A Step 2b", RESULTS / "trackA" / "base_format.jsonl.gz", track_a),
    ("Track A Step 2b smoke", RESULTS / "trackA" / "base_format_smoke.jsonl.gz", track_a),
    ("Track A Step 4 (continuations)", RESULTS / "trackA" / "deletion_calls.jsonl.gz", track_a),
    ("Demo app runs", RESULTS / "ui_runs.jsonl", general),
]


def newest(rows):
    """The newest record per run_id (a re-scored or repaired copy supersedes the earlier one)."""
    out = {}
    for i, r in enumerate(rows):
        out[r.get("run_id") or i] = r
    return list(out.values())


def rescore(rows, parser, n):
    """[(record, (old letter, old rule), (new letter, new rule))] for every letter that changes, on the
    newest record per run."""
    out = []
    for r in newest(rows):
        if "parsed_letter" not in r or r.get("call") == "forced":       # forced answers are read from log-probs
            continue
        k = n.get(r.get("item_id"), 10)
        new = parser(r, k)
        old = (r.get("parsed_letter"), r.get("parse_rule"))
        if new[0] != old[0]:
            out.append((r, old, new))
    return out


def apply_step4(changed, parser_commit):
    """Append a re-scored copy of each changed Step 4 call (same run_id and timestamp, the new letter
    and outcome, a `rescored` note); the report reads the newest record per call. Nothing is edited."""
    from finetune.look import deletion as dl
    for r, old, new in changed:
        rec = {**r, "parsed_letter": new[0], "parse_rule": new[1],
               "parse_status": status(r, new[0]) if r.get("status") == "ok" else r.get("parse_status"),
               "no_answer_reason": None if new[0] else r.get("no_answer_reason"),
               "outcome": dl.outcome(new[0], r["own_letter"], r["hint_letter"]),
               "rescored": {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "parser": parser_commit,
                            "old": list(old), "new": list(new)}}
        dl.save(rec)


def no_text_bound(path):
    rows = load(path)
    failed = [r for r in rows if not r.get("error") and r.get("answer") is None and r.get("finish") != "length"]
    return len(rows), len(failed)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true", help="append re-scored copies of changed Step 4 calls")
    a = ap.parse_args()
    if a.dry_run:
        for name, path, _ in EXPERIMENTS:
            print(f"{name}: {path.relative_to(CODE)}")
        for name, paths in NO_TEXT.items():
            print(f"{name} (no texts): " + ", ".join(str(p.relative_to(CODE)) for p in paths))
        return
    n = n_options()
    log = {"timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "changes": {}, "no_text": {}}
    for name, path, parser in EXPERIMENTS:
        rows = load(path)
        changed = rescore(rows, parser, n)
        print(f"{name}: {len(rows)} records, {len(changed)} letters change")
        for r, old, new in changed:
            tail = " ".join((r.get("final_text") or "").split())[-90:]
            print(f"  - {r.get('run_id')} item {r.get('item_id')} {r.get('model')} {r.get('condition')} "
                  f"{r.get('deletion_arm') or r.get('arm') or ''} repeat {r.get('repeat')}: {old[0]} ({old[1]}) -> "
                  f"{new[0]} ({new[1]}); ends \"...{tail}\"")
        log["changes"][name] = [{"run_id": r.get("run_id"), "timestamp_utc": r.get("timestamp_utc"), "old": old,
                                 "new": new} for r, old, new in changed]
        if a.apply and name == "Track A Step 4 (continuations)" and changed:
            apply_step4(changed, "b0331ed")
            print(f"  appended {len(changed)} re-scored record(s) to {path.name} and its summary")
    for name, paths in NO_TEXT.items():
        for p in paths:
            total, failed = no_text_bound(p)
            print(f"{name}, {p.name}: {total} records without texts; {failed} parse failures (the most that could "
                  f"change)")
            log["no_text"][p.name] = {"records": total, "parse_failures": failed}
    append(OUT, log)


if __name__ == "__main__":
    main()
