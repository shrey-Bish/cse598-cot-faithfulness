"""Track A, step 6: the training question pool. No calls (MMLU-Pro is read from the local cache).

  python finetune/make_pool.py --dry-run --puzzles 300 --mmlu 300   # counts and checks only
  python finetune/make_pool.py --puzzles 300 --mmlu 300             # -> finetune/data/pool.jsonl

  - fresh puzzles from tasks.py at mixed difficulty (shuffles of 5-8 people, orderings of 5-7),
    one seed per puzzle (POOL_SEED-index), none identical to the 24 pilot puzzles or to each other
  - MMLU-Pro questions with 10 options from the categories evaluation does not use (evaluation
    uses law, engineering, chemistry and physics), balanced across categories, 0 overlap with
    the 30 held-out items
  - one wrong hint letter per question, spread over the answer positions
The pool is prefix-stable: a larger --puzzles / --mmlu keeps every earlier question, so the
pilot's questions (the first 5 of each) stay part of the full pool.
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
from tasks import make_items  # noqa: E402

OUT = CODE / "finetune" / "data" / "pool.jsonl"
HELDOUT = CODE / "data" / "progress" / "mmlupro_30.jsonl"
POOL_SEED = 2026
LETTERS = "ABCDEFGHIJ"
LEVELS = [("shuffle", (5, 8)), ("ordering", 5), ("shuffle", (6, 12)), ("ordering", 6), ("shuffle", (7, 15)),
          ("ordering", 7), ("shuffle", (8, 20))]
EVAL_CATEGORIES = {"law", "engineering", "chemistry", "physics"}


def stem(question):
    return question.split("\n(A) ")[0]


def place_answer(item, target):
    """Move the correct option to position `target` (generated options are alphabetical)."""
    correct_text = item["options"][LETTERS.index(item["correct"])]
    others = [o for o in item["options"] if o != correct_text]
    options = others[:target] + [correct_text] + others[target:]
    question = stem(item["question"]) + "\n" + "\n".join(f"({LETTERS[i]}) {o}" for i, o in enumerate(options))
    return {**item, "question": question, "options": options, "correct": LETTERS[target]}


def wrong_letter(index, n_options, correct):
    """A wrong letter that cycles over the positions, skipping the correct one."""
    letter = LETTERS[(index * 3 + 1) % n_options]
    return letter if letter != correct else LETTERS[(index * 3 + 2) % n_options]


def puzzles(n, seed=POOL_SEED):
    """n fresh puzzles, the i-th made from its own seed; repeats of a pilot puzzle (or of an
    earlier pool puzzle) are skipped and replaced by the next index."""
    seen = {stem(it["question"]) for it in pilot.ITEMS}
    out, i = [], 0
    while len(out) < n:
        kind, level = LEVELS[i % len(LEVELS)]
        item = make_items(kind, level, 1, seed=f"{seed}-{i}")[0]
        i += 1
        if stem(item["question"]) in seen:
            continue
        seen.add(stem(item["question"]))
        k = len(out)
        item = place_answer(item, k % len(item["options"]))
        out.append({"item_id": f"puzzle-{seed}-{i - 1}", "question_set": "fresh_puzzles", "question": item["question"],
                    "n_options": len(item["options"]), "correct": item["correct"],
                    "hint_letters": [wrong_letter(k, len(item["options"]), item["correct"])],
                    "kind": kind, "level": list(level) if isinstance(level, tuple) else level,
                    "source": f"tasks.make_items({kind!r}, {level!r}, 1, seed='{seed}-{i - 1}')"})
    return out


def mmlu(n, seed=POOL_SEED, ds=None):
    """n MMLU-Pro questions (10 options) from the categories evaluation does not use: each
    category shuffled once by seed, then taken round-robin, so the pool stays balanced."""
    if ds is None:
        from datasets import load_dataset
        ds = load_dataset("TIGER-Lab/MMLU-Pro", split="test")
    held = {it["question_id"] for it in load(HELDOUT)}
    by_cat = {}
    for r in ds:
        if r["category"] not in EVAL_CATEGORIES and len(r["options"]) == 10 and r["question_id"] not in held:
            by_cat.setdefault(r["category"], []).append(r)
    rng = random.Random(seed)
    cats = sorted(by_cat)
    for c in cats:
        by_cat[c].sort(key=lambda r: r["question_id"])
        rng.shuffle(by_cat[c])
    out, depth = [], 0
    while len(out) < n:
        for c in cats:
            if len(out) < n and depth < len(by_cat[c]):
                r = by_cat[c][depth]
                k = len(out)
                out.append({"item_id": f"mmlupro-{r['question_id']}", "question_set": "mmlupro_train", "qid": r["question_id"],
                            "question": r["question"] + "\n" + "\n".join(f"({LETTERS[i]}) {o}"
                                                                          for i, o in enumerate(r["options"])),
                            "n_options": 10, "correct": r["answer"],
                            "hint_letters": [wrong_letter(k, 10, r["answer"])], "category": c, "src": r["src"],
                            "dataset": "TIGER-Lab/MMLU-Pro", "split": "test"})
        depth += 1
    return out


def pool(n_puzzles, n_mmlu, seed=POOL_SEED, ds=None):
    """Interleaved, so any prefix mixes both sets: puzzle, MMLU-Pro, puzzle, ..."""
    a, b = puzzles(n_puzzles, seed), mmlu(n_mmlu, seed, ds)
    out = []
    for i in range(max(len(a), len(b))):
        out += a[i:i + 1] + b[i:i + 1]
    return out


def checks(items):
    held = {f"mmlupro-{it['question_id']}" for it in load(HELDOUT)}
    pilot_stems = {stem(it["question"]) for it in pilot.ITEMS}
    return {"questions": len(items), "by_set": dict(Counter(i["question_set"] for i in items)),
            "overlap_with_heldout": sum(i["item_id"] in held for i in items),
            "same_as_a_pilot_puzzle": sum(stem(i["question"]) in pilot_stems for i in items),
            "duplicates": len(items) - len({i["item_id"] for i in items}),
            "hint_is_the_answer": sum(i["correct"] in i["hint_letters"] for i in items),
            "mmlu_categories": dict(Counter(i.get("category") for i in items if i["question_set"] == "mmlupro_train")),
            "puzzle_levels": dict(Counter(f"{i['kind']} {i['level']}" for i in items if i["question_set"] == "fresh_puzzles"))}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--puzzles", type=int, default=300)
    ap.add_argument("--mmlu", type=int, default=300)
    a = ap.parse_args()
    items = pool(a.puzzles, a.mmlu)
    c = checks(items)
    print(json.dumps(c, indent=1))
    assert not (c["overlap_with_heldout"] or c["same_as_a_pilot_puzzle"] or c["duplicates"] or c["hint_is_the_answer"])
    if a.dry_run:
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(i) + "\n" for i in items))
    print(f"wrote {len(items)} questions to {OUT.relative_to(CODE)} (seed {POOL_SEED})")


if __name__ == "__main__":
    main()
