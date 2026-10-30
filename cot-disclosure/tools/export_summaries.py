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
    "takeover_pilot.jsonl": "Step 3: the probe pilot's timing (Oct 22)",
}
GPU = {                  # copied back from Sol to results/trackA/gpu/ (numbers only; Step 8's goes through step8_verdict.py)
    "gpu/step9_attention.json": "Step 9: attention to the hint (group means, layer profiles, top heads, comparisons)",
    "gpu/step10_patching.json": "Step 10: activation patching (every cut's logit differences, restoration by layer)",
    "gpu/step9_followup.json": "Step 9 follow-up: full-attention layers, runs within the window, readout heads, aligned curve",
    "gpu/step9_aligned.png": "Step 9 follow-up: the takeover-aligned curve",
    "gpu/step9_aligned.svg": "Step 9 follow-up: the takeover-aligned curve",
    "gpu/step9_onsets.png": "Step 9 follow-up: attention around permanent vs temporary onsets (matched)",
    "gpu/step9_onsets.svg": "Step 9 follow-up: attention around permanent vs temporary onsets (matched)",
    "gpu/val_loss.json": "S7: validation loss by part, base and both epochs of each version (tokens and mean loss)",
    "gpu/val_loss_examples.jsonl": "S7: per system and example, tokens and loss sum per part (record ids only)",
}
KEEP_PATH = {             # under results/trackA/ -> under results/summaries/ (subfolders kept: set A's Step 10 has
                         # Test 2's file names)
    "setA/step10_patching.json": "trackA/setA/step10_patching.json",        # set A, Step 10 (F26)
    "setA/step10_handoff.json": "trackA/setA/step10_handoff.json",          # patching.py --handoff (F26)
    "setA/step10_handoff.png": "trackA/setA/step10_handoff.png",
    "setA/step10_handoff.svg": "trackA/setA/step10_handoff.svg",
    "setA/step9_attention.json": "trackA/setA/step9_attention.json",        # set A, Step 9
    "setA/step9_fixed_heads.json": "trackA/setA/step9_fixed_heads.json",    # set A, F12's three heads (F32)
    "setA/provenance_forced.json": "trackA/setA/provenance_forced.json",    # B1's forced answers and alpha (F27)
    "gpu/eval/eval_report.json": "trackA/gpu/eval/eval_report.json",        # batch 3 (F28)
    "gpu/eval/gate3.json": "trackA/gpu/eval/gate3.json",                    # finetune/gate3.py
    "gpu/eval/gate3_table.md": "trackA/gpu/eval/gate3_table.md",
    **{f"gpu/eval/figures/{f}.{x}": f"trackA/gpu/eval/figures/{f}.{x}"
       for f in ("gate3_following", "gate3_vs_base") for x in ("png", "svg", "csv")},
}
LATER = ["nohint_train_runs.jsonl", "targets_runs.jsonl", "target_samples_runs.jsonl", "targets_prefill_runs.jsonl",
         "target_samples_prefill_runs.jsonl"]                    # Steps 6-7: after the run finishes
OTHER = {                # Tracks B and C: numbers-only reports their scripts write (copied as they are)
    "results/trackB/trackB_report.json": "trackB/trackB_report.json",            # progress/trackB_report.py
    "results/trackB/template_check.jsonl": "trackB/template_check.jsonl",        # progress/voyager_template_check.py
    "results/trackB/b15_report.json": "trackB/b15_report.json",                  # B15 (progress/run_b15.py --report)
    "results/trackC/team_live_summary.json": "trackC/team_live_summary.json",    # agents/run_team.py --summary
    "results/trackC/team_replay_summary.json": "trackC/team_replay_summary.json",
    "results/trackC/team_smoke_olmo32b_summary.json": "trackC/team_smoke_olmo32b_summary.json",   # Oct 28, the 32B reviewer
    "results/trackC/team_c4_summary.json": "trackC/team_c4_summary.json",                        # C4 (--log team_c4)
    "results/trackC/team_c9_summary.json": "trackC/team_c9_summary.json",                        # C9 (--log team_c9)
    "results/trackC/team_c10_summary.json": "trackC/team_c10_summary.json",                      # C10 (--log team_c10)
    "results/trackC/team_c11_summary.json": "trackC/team_c11_summary.json",                      # C11 (--log team_c11)
    "results/trackC/team_c12_summary.json": "trackC/team_c12_summary.json",                      # C12 (--log team_c12)
    "results/trackC/c14_disagreement.json": "trackC/c14_disagreement.json",                      # C14 (agents/disagreement.py)
    "results/trackC/c15_summary.json": "trackC/c15_summary.json",                                # C15 (agents/c15.py)
    "results/trackC/team_c15_summary.json": "trackC/team_c15_summary.json",                      # C15's reviews (--log team_c15)
    "results/trackC/team_c15_solve_summary.json": "trackC/team_c15_solve_summary.json",          # C15's solver and checker
    "results/trackC/team_c13_granite_summary.json": "trackC/team_c13_granite_summary.json",      # C13 (Sol; F30)
    "results/trackC/team_c13_mistral_summary.json": "trackC/team_c13_mistral_summary.json",
    "results/trackC/c16_summary.json": "trackC/c16_summary.json",                                # C16 (agents/c16.py)
    "results/trackC/team_c16_summary.json": "trackC/team_c16_summary.json",
    "results/trackC/team_c16_control_summary.json": "trackC/team_c16_control_summary.json",
    "results/trackC/team_c16_solve_summary.json": "trackC/team_c16_solve_summary.json",
    "results/trackC/c17_summary.json": "trackC/c17_summary.json",                                # C17 (agents/c17.py)
    "results/trackC/team_c17_names_summary.json": "trackC/team_c17_names_summary.json",
    "results/trackC/team_c17_own_summary.json": "trackC/team_c17_own_summary.json",
}
RUNNING = "finetune/run_steps67.py"
DATA = CODE / "finetune" / "data"
DATA_FILES = {           # source (under finetune/data/) -> what it holds; copied to results/summaries/trackA/data/
    "manifest.json": "Step 5: records, wordings, held-out overlap (counts and ids only)",
    "examples_manifest.json": "Steps 6-7 assembly: example counts by split, channel and stance",
}


def still_running():
    """True while the Steps 6-7 run is going (its files are still being written)."""
    import subprocess
    out = subprocess.run(["pgrep", "-f", RUNNING], capture_output=True, text=True).stdout
    return bool(out.strip())


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


def onset_rows():
    """Step 3, per hinted run: whether its curve is dense, and every onset after the first fifth (a
    probe where the hint letter becomes the leading letter) as [k, permanent] (permanent: it keeps the
    lead to the end, the takeover). Step 9's matched comparison anchors on these on Sol."""
    from finetune.look import before_takeover as bt
    from finetune.look import takeover as tk
    out = []
    for r in tk.current_probes(load(tk.PROBES_OUT)):
        if r["kind"] == "no hint":
            continue
        dense = tk.dense(r)
        out.append({"source_run_id": r["source_run_id"], "item_id": r["item_id"], "kind": r["kind"],
                    "n_sentences": r["n_sentences"], "dense": dense,
                    "onsets": [[k, perm] for k, perm in bt.onsets(r)] if dense else None})
    return out


def plan():
    """[(source or None, destination, writer)]: copies, plus derived numbers-only files."""
    out = [(TRACK_A / name, SUMMARIES / "trackA" / name, None) for name in TRACK_A_FILES if (TRACK_A / name).exists()]
    out += [(TRACK_A / name, SUMMARIES / "trackA" / Path(name).name, None) for name in GPU if (TRACK_A / name).exists()]
    out += [(TRACK_A / src, SUMMARIES / dst, None) for src, dst in KEEP_PATH.items() if (TRACK_A / src).exists()]
    out += [(DATA / name, SUMMARIES / "trackA" / "data" / name, None) for name in DATA_FILES if (DATA / name).exists()]
    out += [(CODE / src, SUMMARIES / dst, None) for src, dst in OTHER.items() if (CODE / src).exists()]
    if not still_running():
        out += [(TRACK_A / name, SUMMARIES / "trackA" / name, None) for name in LATER if (TRACK_A / name).exists()]
    if (TRACK_A / "takeover_probes.jsonl.gz").exists():
        out.append((None, SUMMARIES / "trackA" / "takeover_per_run.jsonl", takeover_rows))
        out.append((None, SUMMARIES / "trackA" / "hint_onsets.jsonl", onset_rows))
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
    if still_running():
        print(f"later, after the Steps 6-7 run: {', '.join(LATER)}")
    return not failed


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
