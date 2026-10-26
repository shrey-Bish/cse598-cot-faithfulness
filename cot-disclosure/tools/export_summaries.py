"""Copy the numbers-only summaries and figures of produced results into results/summaries/ (tracked).

Produced data (runs, probes, replies, caches, checkpoints, Sol outputs, GPQA files) stays in
gitignored folders and never goes to GitHub (decided Oct 26). Every reported number must still be
traceable, so the small per-run summaries and the figures behind them are copied here, after a
check that they hold no question or reply text:
  - every JSON string is at most MAX_STRING characters (ids, labels, letters, timestamps), except
    under keys holding text we wrote ourselves (AUTHORED: notes, definitions, readings)
  - no file contains the start of any question we ask (MMLU-Pro items, the training pool)
Files whose source is still being written (the Steps 6-7 run) are exported once it has finished.

  python tools/export_summaries.py --dry-run     # what would be copied, and the checks
  python tools/export_summaries.py               # copy (refuses a file that fails the checks)
  python tools/export_summaries.py --check       # check what is already in results/summaries/
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import load  # noqa: E402

SUMMARIES = CODE / "results" / "summaries"
TRACK_A = CODE / "results" / "trackA"
CANARY = CODE / "results" / "voyager_canary.jsonl"        # the client's identity-canary log (all tracks)
MAX_STRING = 200
STEM = 40                # characters of each question's start that must not appear
AUTHORED = {"note", "cut_ii_note", "reading", "definitions", "text", "meaning", "for_scale", "rule", "use"}
# source (under results/trackA/) -> what it holds; copied under the same name to results/summaries/trackA/
TRACK_A_FILES = {
    "base_format_runs.jsonl": "Step 2b: one row per run (channel, letters, outcome, tokens)",
    "template_revisions.json": "Step 2: prompt-token counts of every template revision against Voyager's",
    "takeover_runs.jsonl": "Step 3: one row per probed run (outcome, takeover point and type)",
    "takeover_cases.jsonl": "Step 3: the default cases for Steps 4 and 10",
    "takeover_adaptive_check.jsonl": "Step 3: adaptive vs dense probing on the saved curves",
    "before_takeover.jsonl": "before Step 4: concentration, matched onsets, closest approaches",
    "deletion_runs.jsonl": "Step 4: one row per call (arm, outcome)",
    "length_audit.jsonl": "Step 5: reply lengths",
}
GPU = {                  # copied back from Sol to results/trackA/gpu/ (numbers only; Step 8's goes through step8_verdict.py)
    "gpu/step9_attention.json": "Step 9: attention to the hint (group means, layer profiles, top heads, comparisons)",
    "gpu/step10_patching.json": "Step 10: activation patching (every cut's logit differences, restoration by layer)",
}
LATER = ["nohint_train_runs.jsonl", "targets_runs.jsonl", "target_samples_runs.jsonl", "targets_prefill_runs.jsonl",
         "target_samples_prefill_runs.jsonl"]                    # Steps 6-7: after the run finishes


def strings(x, skip=AUTHORED):
    """Every string in a JSON value, except under the keys in `skip`."""
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for k, v in x.items():
            yield k
            if k not in skip:
                yield from strings(v, skip)
    elif isinstance(x, list):
        for v in x:
            yield from strings(v, skip)


def question_starts():
    """The start of every question text we have locally (empty where the data isn't here)."""
    out = set()
    for path in (CODE / "data" / "progress" / "mmlupro_30.jsonl", CODE / "finetune" / "data" / "pool.jsonl"):
        for row in load(path):
            q = (row.get("question") or "").strip()
            if len(q) >= STEM:
                out.add(q[:STEM])
    return out


def problems(path, starts):
    """Why a file is not numbers-only ([] if it is)."""
    text = path.read_text(errors="replace")
    out = [f"contains the start of a question: {s!r}" for s in starts if s in text][:3]
    if path.suffix in (".json", ".jsonl"):
        objs = [json.loads(line) for line in text.splitlines() if line.strip()] if path.suffix == ".jsonl" \
            else [json.loads(text)]
        long = [s for o in objs for s in strings(o) if len(s) > MAX_STRING]
        if long:
            out.append(f"{len(long)} strings over {MAX_STRING} characters, e.g. {long[0][:80]!r}")
    return out


def remention_rows():
    """Step 4's re-mention check as numbers: per continuation that ended on the hint letter, whether
    the reasoning after the cut mentions the hint again (from deletion_calls.jsonl.gz)."""
    from finetune.look import deletion as dl
    return [{k: r[k] for k in ("item_id", "arm", "mentions", "n_mentions")} for r in dl.remention(load(dl.CALLS_OUT))]


def takeover_rows():
    """Step 3, per probed run, as numbers: which letter leads before any reasoning (k = 0), the
    takeover type, and whether a hint mention comes in the takeover sentence or the 2 before (a late
    takeover) or at the closest approach (a resisted run's strongest point after the first fifth)."""
    from finetune import base_format as bf
    from finetune.look import takeover as tk
    key = {it["question_id"]: it["answer"] for it in bf.questions()}
    out = []
    for r in tk.current_probes(load(tk.PROBES_OUT)):
        top0 = r["top_letters"][0]
        closest = tk.closest_approach(r) if r["kind"] == "resisted" else None
        out.append({"source_run_id": r["source_run_id"], "item_id": r["item_id"], "condition": r["condition"],
                    "arm": r.get("arm"), "kind": r["kind"], "hint_letter": r["hint_letter"], "correct_letter": key[r["item_id"]],
                    "own_letter": r.get("own_letter"), "final_letter": r["final_letter"], "top_letter_at_k0": top0,
                    "n_sentences": r["n_sentences"], "takeover_k": r.get("takeover_k"),
                    "type": tk.takeover_type(r) if r["kind"] != "no hint" else None,
                    "mention_within_2_before_takeover": r.get("mention_within_2_before"),
                    "closest_approach_k": closest[0] if closest else None,
                    "closest_approach_mention": closest[1] if closest else None})
    return out


def plan():
    """[(source or None, destination, writer)]: copies, plus derived numbers-only files."""
    out = [(TRACK_A / name, SUMMARIES / "trackA" / name, None) for name in TRACK_A_FILES if (TRACK_A / name).exists()]
    out += [(TRACK_A / name, SUMMARIES / "trackA" / Path(name).name, None) for name in GPU if (TRACK_A / name).exists()]
    if (TRACK_A / "takeover_probes.jsonl.gz").exists():
        out.append((None, SUMMARIES / "trackA" / "takeover_per_run.jsonl", takeover_rows))
    if CANARY.exists():
        out.append((CANARY, SUMMARIES / "voyager_canary.jsonl", None))
    out += [(f, SUMMARIES / "trackA" / "figures" / f.name, None) for f in sorted((TRACK_A / "figures").glob("*"))
            if f.suffix in (".png", ".svg")]
    if (TRACK_A / "deletion_calls.jsonl.gz").exists():
        out.append((None, SUMMARIES / "trackA" / "deletion_remention.jsonl", remention_rows))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true", help="check every file already in results/summaries/")
    a = ap.parse_args(argv)
    starts = question_starts()
    if a.check:
        bad = {p: problems(p, starts) for p in sorted(SUMMARIES.rglob("*")) if p.is_file()}
        bad = {p: v for p, v in bad.items() if v}
        for p, v in bad.items():
            print(f"{p.relative_to(CODE)}: {'; '.join(v)}")
        print("results/summaries/: " + ("all numbers-only" if not bad else f"{len(bad)} files are not"))
        return not bad
    failed = []
    for src, dst, writer in plan():
        if writer is not None:
            tmp = dst.with_name(dst.name + ".tmp")
            if not a.dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                tmp.write_text("".join(json.dumps(r) + "\n" for r in writer()))
                why = problems(tmp, starts)
                tmp.replace(dst) if not why else tmp.unlink()
            else:
                why = []
            label = "derived"
        else:
            why = problems(src, starts) if src.suffix != ".png" else []
            if not why and not a.dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            label = str(src.relative_to(CODE))
        failed += [dst] if why else []
        print(f"{'REFUSED' if why else ('would copy' if a.dry_run else 'copied')}: {label} -> {dst.relative_to(CODE)}"
              + (f"  ({'; '.join(why)})" if why else ""))
    print(f"later, after the Steps 6-7 run: {', '.join(LATER)}")
    return not failed


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
