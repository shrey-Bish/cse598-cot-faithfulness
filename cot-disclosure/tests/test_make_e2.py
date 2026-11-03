"""E2 (finetune/make_e2.py, Nov 3): the larger held-out evaluation set, drawn once by a recorded seed from the evaluation
categories, with none of the 30, Track A's pool (training, validation, set A), Track B's 54 or C15's items, by id and by
text. On a synthetic dataset; no network."""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

from finetune import make_e2 as e2  # noqa: E402

LETTERS = "ABCDEFGHIJ"


def q(qid, cat, text=None, n=10, answer="C"):
    return {"question_id": qid, "category": cat, "question": text or f"question {qid}?", "src": f"ori_{cat}",
            "options": [f"option {i}" for i in range(n)], "answer": answer}


def dataset():
    ds = [q(i, c) for c in ("law", "engineering", "chemistry", "physics", "biology") for i in
          range({"law": 0, "engineering": 100, "chemistry": 200, "physics": 300, "biology": 400}[c],
                {"law": 0, "engineering": 100, "chemistry": 200, "physics": 300, "biology": 400}[c] + 12)]
    ds.append(q(999, "law", n=4))                                             # 4 options: never drawn
    ds.append(q(998, "physics", text="question 5?"))                          # the same text as a pool question
    return ds


HELD = [{"question_id": 1, "question": "question 1?"}]                       # the 30 (Track B's MMLU-Pro 30 too)
POOL = [{"item_id": "mmlupro-2", "question": "question 2?\n(A) x"}, {"item_id": "mmlupro-77", "question": "question 5?\n(A) y"},
        {"item_id": "puzzle-1", "question": "a puzzle"}]
C15 = [{"item_id": "mmlupro-3", "question": "question 3?\n(A) z"}]


def test_draw_takes_the_same_number_per_evaluation_category_and_excludes_every_used_question():
    rows = e2.draw(dataset(), HELD, POOL, C15, per=5, seed="t")
    assert len(rows) == 20 and {r["category"] for r in rows} == {"law", "engineering", "chemistry", "physics"}
    ids = {r["question_id"] for r in rows}
    assert not ids & {1, 2, 3, 998, 999}
    assert all(len(r["options"]) == 10 and r["cue_letter"] != r["answer"] for r in rows)
    assert all(r["dataset"] == "TIGER-Lab/MMLU-Pro" and r["split"] == "test" and r["e2_seed"] == "t" for r in rows)
    c = e2.checks(rows, HELD, POOL, C15)
    assert c["in_the_30"] == c["in_track_a_pool"] == c["in_c15"] == c["duplicates"] == c["cue_is_the_answer"] == 0
    assert c["by_category"] == {"chemistry": 5, "engineering": 5, "law": 5, "physics": 5}


def test_the_seed_fixes_the_draw_and_the_wrong_letter():
    a, b = e2.draw(dataset(), HELD, POOL, C15, per=5, seed="t"), e2.draw(dataset(), HELD, POOL, C15, per=5, seed="t")
    assert [(r["question_id"], r["cue_letter"]) for r in a] == [(r["question_id"], r["cue_letter"]) for r in b]
    c = e2.draw(dataset(), HELD, POOL, C15, per=5, seed="other")
    assert [r["question_id"] for r in a] != [r["question_id"] for r in c]


def test_checks_catch_a_reused_question_by_text():
    rows = e2.draw(dataset(), HELD, POOL, C15, per=5, seed="t")
    rows[0] = {**rows[0], "question": "question 1?"}                          # the 30's text under a new id
    assert e2.checks(rows, HELD, POOL, C15)["in_the_30"] == 1


def test_sha256_is_of_the_written_bytes(tmp_path):
    rows = e2.draw(dataset(), HELD, POOL, C15, per=2, seed="t")
    path = tmp_path / "e2.jsonl"
    digest = e2.write(rows, path)
    import hashlib
    assert digest == hashlib.sha256(path.read_bytes()).hexdigest()
    assert e2.write(rows, tmp_path / "again.jsonl") == digest                 # the same rows, the same bytes
