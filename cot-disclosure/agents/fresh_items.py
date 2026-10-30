"""Track C, C15: fresh items for the replication (no calls; MMLU-Pro from the local cache).

  python agents/fresh_items.py --dry-run      # counts and checks only
  python agents/fresh_items.py                # -> results/trackC/c15_items.jsonl (gitignored; question text)

100 items, seeded (SEED), none used before:
  - 60 MMLU-Pro questions with 10 options from the categories evaluation does not use (finetune/make_pool.py's
    EVAL_CATEGORIES: law, engineering, chemistry, physics), 6 per category; none of the 30 evaluation questions
    (which are also Track B's 30) and none in Track A's training pool (finetune/data/pool.jsonl, all 1,600
    questions: training, validation and set A), by id and by question text (MMLU-Pro repeats some texts)
  - 40 fresh puzzles from tasks.py, cycling over the pool's levels (make_pool.LEVELS, then HARD_LEVELS), so the
    set mixes easy and hard; none the same as a pilot puzzle (Track B's 24) or a pool puzzle; the right answer
    placed round-robin over the positions
  - one wrong lookup letter per item (the bad lookup returns it), drawn by seed from the wrong options
Rows are in Track B's steered_cases.jsonl format, so agents/run_team.py takes them with --cases and --kinds fresh:
case_id "c15|<item_id>", kind "fresh", set mmlupro_c15 or puzzles_c15.
"""
import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

import experiments as pilot  # noqa: E402
from common import load  # noqa: E402
from finetune.make_pool import EVAL_CATEGORIES, HARD_LEVELS, HELDOUT, LETTERS, LEVELS, place_answer, stem  # noqa: E402
from tasks import make_items  # noqa: E402

OUT = CODE / "results" / "trackC" / "c15_items.jsonl"
POOL = CODE / "finetune" / "data" / "pool.jsonl"
SEED = "c15-20261029"
N_MMLU, N_PUZZLES = 60, 40
KIND = "fresh"


def lookup_letter(item_id, n_options, correct):
    """The bad lookup's letter: a wrong option, drawn by seed and item."""
    wrong = [x for x in LETTERS[:n_options] if x != correct]
    return random.Random(f"{SEED}:lookup:{item_id}").choice(wrong)


def row(item_id, set_name, question, n_options, correct, **extra):
    return {"case_id": f"c15|{item_id}", "kind": KIND, "set": set_name, "item_id": item_id, "question": question,
            "n_options": n_options, "correct_letter": correct, "hint_letter": lookup_letter(item_id, n_options, correct),
            "source": {"made_by": "agents/fresh_items.py", "seed": SEED, **extra}}


def mmlu(n=N_MMLU, ds=None, pool=None):
    """n MMLU-Pro questions, n / 10 from each category evaluation doesn't use, by a seeded shuffle per category."""
    if ds is None:
        from datasets import load_dataset
        ds = load_dataset("TIGER-Lab/MMLU-Pro", split="test")
    pool = load(POOL) if pool is None else pool
    held = load(HELDOUT)
    used = {it["question_id"] for it in held} | {int(i["item_id"].split("-")[1]) for i in pool
                                                 if i["item_id"].startswith("mmlupro-")}
    used_stems = {it["question"] for it in held} | {stem(i["question"]) for i in pool}   # MMLU-Pro repeats some texts
    by_cat = {}
    for r in ds:
        if (r["category"] not in EVAL_CATEGORIES and len(r["options"]) == 10 and r["question_id"] not in used
                and r["question"] not in used_stems):
            by_cat.setdefault(r["category"], []).append(r)
    cats = sorted(by_cat)
    per = n // len(cats)
    rng = random.Random(f"{SEED}:mmlu")
    out = []
    for c in cats:
        rs = sorted(by_cat[c], key=lambda r: r["question_id"])
        for r in rng.sample(rs, per):
            out.append(row(f"mmlupro-{r['question_id']}", "mmlupro_c15",
                           r["question"] + "\n" + "\n".join(f"({LETTERS[i]}) {o}" for i, o in enumerate(r["options"])),
                           10, r["answer"], category=c, dataset="TIGER-Lab/MMLU-Pro", split="test"))
    return out


def puzzles(n=N_PUZZLES, pool=None):
    """n fresh puzzles, the i-th from its own seed, over LEVELS + HARD_LEVELS in turn; a repeat of a pilot or
    pool puzzle (or of an earlier one) is skipped and replaced by the next index."""
    pool = load(POOL) if pool is None else pool
    seen = {stem(it["question"]) for it in pilot.ITEMS} | {stem(i["question"]) for i in pool
                                                           if i["question_set"].startswith("fresh")}
    levels = LEVELS + HARD_LEVELS
    out, i = [], 0
    while len(out) < n:
        kind, level = levels[i % len(levels)]
        item = make_items(kind, level, 1, seed=f"{SEED}-{i}")[0]
        i += 1
        if stem(item["question"]) in seen:
            continue
        seen.add(stem(item["question"]))
        item = place_answer(item, len(out) % len(item["options"]))
        out.append(row(f"puzzle-{SEED}-{i - 1}", "puzzles_c15", item["question"], len(item["options"]), item["correct"],
                       kind=kind, level=list(level) if isinstance(level, tuple) else level,
                       made=f"tasks.make_items({kind!r}, {level!r}, 1, seed='{SEED}-{i - 1}')"))
    return out


def items(ds=None, pool=None):
    pool = load(POOL) if pool is None else pool
    return mmlu(ds=ds, pool=pool) + puzzles(pool=pool)


def checks(rows, pool=None):
    pool = load(POOL) if pool is None else pool
    held = {f"mmlupro-{it['question_id']}" for it in load(HELDOUT)}
    pool_ids = {i["item_id"] for i in pool}
    pilot_stems = {stem(it["question"]) for it in pilot.ITEMS}
    pool_stems = {stem(i["question"]) for i in pool}
    return {"items": len(rows), "by_set": dict(Counter(r["set"] for r in rows)),
            "in_the_30_evaluation_questions": sum(r["item_id"] in held for r in rows),
            "in_track_a_pool": sum(r["item_id"] in pool_ids or stem(r["question"]) in pool_stems for r in rows),
            "same_as_a_pilot_puzzle": sum(stem(r["question"]) in pilot_stems for r in rows),
            "duplicates": len(rows) - len({r["item_id"] for r in rows}),
            "lookup_is_the_answer": sum(r["hint_letter"] == r["correct_letter"] for r in rows),
            "categories": dict(Counter(r["source"].get("category") for r in rows if r["set"] == "mmlupro_c15")),
            "puzzle_levels": dict(Counter(f"{r['source']['kind']} {r['source']['level']}" for r in rows
                                          if r["set"] == "puzzles_c15")),
            "answer_positions": dict(sorted(Counter(r["correct_letter"] for r in rows).items()))}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if OUT.exists() and not a.dry_run:
        sys.exit(f"{OUT.relative_to(CODE)} exists; it is never rewritten (the C15 cases point at its items)")
    rows = items()
    c = checks(rows)
    print(json.dumps(c, indent=1))
    assert not (c["in_the_30_evaluation_questions"] or c["in_track_a_pool"] or c["same_as_a_pilot_puzzle"]
                or c["duplicates"] or c["lookup_is_the_answer"])
    if a.dry_run:
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"wrote {len(rows)} items to {OUT.relative_to(CODE)}")


if __name__ == "__main__":
    main()
