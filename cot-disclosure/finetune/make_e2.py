"""Track A, E2 (Nov 3): a second, larger held-out evaluation set, fixed before any new result (no calls; MMLU-Pro from
the local cache). Pre-registered in archive/sessions/2026-11-03/2026-11-03_1330_A_e2-a39-prereg.md.

  python finetune/make_e2.py --power        # its size: the half-widths from Gate 3's runs (F28), no calls
  python finetune/make_e2.py --dry-run      # the draw and its checks, nothing written
  python finetune/make_e2.py                # -> data/progress/mmlupro_e2.jsonl, written once, and its sha256

The draw: N_PER_CATEGORY MMLU-Pro test questions with 10 options from each evaluation category (make_pool's
EVAL_CATEGORIES: law, engineering, chemistry, physics), by a seeded shuffle per category (SEED). None of them is:
  - one of the 30 evaluation questions (data/progress/mmlupro_30.jsonl, which are also Track B's 30 MMLU-Pro; Track B's
    other 24 are generated puzzles);
  - in Track A's pool (finetune/data/pool.jsonl: training, validation and set A, all 1,600);
  - one of C15's items (results/trackC/c15_items.jsonl);
by question id and by question text (MMLU-Pro repeats some texts). The wrong hint letter of each question (cue_letter,
as in the 30's file) is drawn by seed from its wrong options. Rows have the 30's fields, so build_dataset reads either.
"""
import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import load  # noqa: E402
from finetune.make_pool import EVAL_CATEGORIES, HELDOUT, LETTERS, stem  # noqa: E402

OUT = CODE / "data" / "progress" / "mmlupro_e2.jsonl"
POOL = CODE / "finetune" / "data" / "pool.jsonl"
C15 = CODE / "results" / "trackC" / "c15_items.jsonl"
SEED = "e2-20261103"
N_PER_CATEGORY = 30
DATASET, REVISION = "TIGER-Lab/MMLU-Pro", "b189ec765aa7ed75c8acfea42df31fdae71f97be"     # the 30's revision


def cue_letter(qid, answer, seed=SEED):
    """The wrong hint's letter: a wrong option, drawn by seed and question."""
    return random.Random(f"{seed}:cue:{qid}").choice([x for x in LETTERS if x != answer])


def used(held, pool, c15):
    """(question ids, question texts) already used anywhere."""
    ids = {int(h["question_id"]) for h in held}
    ids |= {int(i["item_id"].split("-")[1]) for i in [*pool, *c15] if i["item_id"].startswith("mmlupro-")}
    texts = {h["question"] for h in held} | {stem(i["question"]) for i in [*pool, *c15]}
    return ids, texts


def draw(ds, held, pool, c15, per=N_PER_CATEGORY, seed=SEED):
    ids, texts = used(held, pool, c15)
    by_cat = {}
    for r in ds:
        if (r["category"] in EVAL_CATEGORIES and len(r["options"]) == 10 and r["question_id"] not in ids
                and r["question"] not in texts):
            by_cat.setdefault(r["category"], []).append(r)
    out = []
    for c in sorted(EVAL_CATEGORIES):
        rs = sorted(by_cat.get(c, []), key=lambda r: r["question_id"])
        for r in random.Random(f"{seed}:{c}").sample(rs, per):
            out.append({"question_id": r["question_id"], "category": c, "question": r["question"],
                        "options": list(r["options"]), "answer": r["answer"], "cue_letter": cue_letter(r["question_id"],
                                                                                                      r["answer"], seed),
                        "dataset": DATASET, "dataset_revision": REVISION, "split": "test", "src": r.get("src"),
                        "e2_seed": seed})
    return out


def checks(rows, held, pool, c15):
    ids_held, texts_held = used(held, [], [])
    pool_ids, pool_texts = used([], pool, [])
    c15_ids, c15_texts = used([], [], c15)
    hit = lambda r, ids, texts: r["question_id"] in ids or r["question"] in texts  # noqa: E731
    return {"questions": len(rows), "by_category": dict(sorted(Counter(r["category"] for r in rows).items())),
            "in_the_30": sum(hit(r, ids_held, texts_held) for r in rows),
            "in_track_a_pool": sum(hit(r, pool_ids, pool_texts) for r in rows),
            "in_c15": sum(hit(r, c15_ids, c15_texts) for r in rows),
            "duplicates": len(rows) - len({r["question_id"] for r in rows}) + len(rows) - len({r["question"] for r in rows}),
            "cue_is_the_answer": sum(r["cue_letter"] == r["answer"] for r in rows),
            "answers": dict(sorted(Counter(r["answer"] for r in rows).items())),
            "cue_letters": dict(sorted(Counter(r["cue_letter"] for r in rows).items()))}


def write(rows, path=OUT):
    data = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows).encode()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def power(eval_dir=CODE / "results" / "trackA" / "gpu" / "eval", target=0.05):
    """E2's size from Gate 3's own runs: for each pair (LoRA, prompt_only, base), the between-question variance of the
    per-question difference and each system's within-question variance per run, then the questions needed for a 95%
    half-width of `target` with the lean design's runs per question (6 wrong-hint, 4 correct-hint)."""
    import glob
    import math
    import statistics
    main = ("user_turpin", "user_professor", "tool_progress", "inserted_study_guide", "inserted_database",
            "inserted_new_tool")

    def per_q(system, kind):
        out = {}
        for f in sorted(glob.glob(str(Path(eval_dir) / f"eval_{system}_p*_runs.jsonl"))):
            for r in load(f):
                if r["status"] == "ok" and ((kind == "following" and r["wording"] in main and r["hint_correct"] is False)
                                            or (kind == "acceptance" and r["hint_correct"] is True)):
                    out.setdefault(r["item_id"], []).append(r["parsed_letter"] == r["hint_letter"])
        return out

    res = {}
    for a, b in (("lora", "base"), ("prompt_only", "base"), ("lora", "prompt_only")):
        for kind, r_e2 in (("following", 6), ("acceptance", 4)):
            x, y = per_q(a, kind), per_q(b, kind)
            qs = sorted(set(x) & set(y))
            d = [statistics.mean(x[q]) - statistics.mean(y[q]) for q in qs]
            within = statistics.mean(sum(statistics.mean(m[q]) * (1 - statistics.mean(m[q])) / (len(m[q]) - 1)
                                         for m in (x, y)) for q in qs)
            s2 = sum(statistics.mean(statistics.mean(m[q]) * (1 - statistics.mean(m[q])) * len(m[q]) / (len(m[q]) - 1)
                                     for q in qs) for m in (x, y))
            vb = max(0.0, statistics.variance(d) - within)
            n = math.ceil((vb + s2 / r_e2) / (target / 1.96) ** 2)
            res[f"{a} - {b} | {kind}"] = {"gate3_diff": statistics.mean(d), "gate3_half_width": 1.96 * math.sqrt(
                statistics.variance(d) / len(qs)), "between_var": vb, "within_var_per_run_sum": s2,
                "runs_per_question_e2": r_e2, "questions_for_5_points": n,
                "half_width_at_120": 1.96 * math.sqrt((vb + s2 / r_e2) / 120)}
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--power", action="store_true")
    a = ap.parse_args()
    if a.power:
        print(json.dumps(power(), indent=1))
        return
    if OUT.exists() and not a.dry_run:
        sys.exit(f"{OUT.relative_to(CODE)} exists; it is written once (its sha256 is in the pre-registration)")
    from datasets import load_dataset
    ds = load_dataset(DATASET, split="test", revision=REVISION)
    held, pool, c15 = load(HELDOUT), load(POOL), load(C15)
    rows = draw(ds, held, pool, c15)
    c = checks(rows, held, pool, c15)
    print(json.dumps(c, indent=1))
    assert not (c["in_the_30"] or c["in_track_a_pool"] or c["in_c15"] or c["duplicates"] or c["cue_is_the_answer"])
    if not a.dry_run:
        print(f"wrote {OUT.relative_to(CODE)}: sha256 {write(rows)}")


if __name__ == "__main__":
    main()
