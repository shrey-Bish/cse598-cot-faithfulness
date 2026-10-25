"""Track A Step 6 (finetune/make_pool.py, finetune/run_nohint.py): CPU only, no network."""
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

pytest.importorskip("transformers")

from finetune import make_pool as mp  # noqa: E402
from finetune import run_nohint as rn  # noqa: E402

FAKE_DS = [{"question_id": 100 + i, "category": cat, "question": f"Q{i}?", "options": [f"o{j}" for j in range(10)],
            "answer": "ABCDEFGHIJ"[i % 10], "src": "x"} for i, cat in enumerate(["math", "law", "history", "math"] * 6)]


def test_the_pool_is_prefix_stable_and_clean():
    small, big = mp.pool(4, 4, ds=FAKE_DS), mp.pool(8, 8, ds=FAKE_DS)
    assert big[:len(small)] == small                                         # a bigger pool keeps the pilot's questions
    c = mp.checks(big)
    assert c["overlap_with_heldout"] == c["same_as_a_pilot_puzzle"] == c["duplicates"] == c["hint_is_the_answer"] == 0
    assert "law" not in c["mmlu_categories"] and set(c["mmlu_categories"]) == {"math", "history"}
    assert [q["question_set"] for q in big[:4]] == ["fresh_puzzles", "mmlupro_train"] * 2
    puzzle = big[0]
    assert puzzle["question"].count("\n(A) ") == 1 and puzzle["correct"] in "ABCDEFGHIJ"[:puzzle["n_options"]]


def test_puzzles_never_repeat_a_pilot_puzzle(monkeypatch):
    first = mp.make_items("shuffle", (5, 8), 1, seed=f"{mp.POOL_SEED}-0")[0]
    monkeypatch.setattr(mp.pilot, "ITEMS", [first])                          # pretend the first one is a pilot puzzle
    out = mp.puzzles(2)
    assert all(mp.stem(q["question"]) != mp.stem(first["question"]) for q in out) and out[0]["item_id"].endswith("-1")


def out_of(letter, finish="stop"):
    return {"error": None, "content": f"Answer: ({letter})", "reasoning": "", "finish": finish,
            "usage": {"prompt_tokens": 100, "completion_tokens": 900}, "prompt": "P", "raw": f"r</think>Answer: ({letter})",
            "latency_s": 1.0, "retries": 0, "reasoning_field": "split_at_think_close", "tool_calls": [], "cached": False,
            "served_model": "olmo3-7b-think", "requested_model_id": "olmo3-7b", "reasoning_effort": "medium"}


def test_a_no_hint_run_record_and_a_resumable_run(monkeypatch, tmp_path):
    q = {"item_id": "puzzle-1", "question_set": "fresh_puzzles", "question": "Q\n(A) a\n(B) b", "n_options": 2,
         "correct": "B", "kind": "shuffle"}
    calls = []

    def complete(model, prompt, **kw):
        calls.append((prompt, kw))
        rep = kw["seed"]
        return {"error": None, "content": "r</think>Answer: (B)", "finish": "stop" if rep < 2 else "length",
                "reasoning": "", "usage": {"prompt_tokens": 100, "completion_tokens": 900}, "served_model": "olmo3-7b-think"}
    monkeypatch.setattr(rn, "complete", complete)
    monkeypatch.setattr(rn.olmo_format, "n_tokens", lambda text: len(text) // 4)
    paths = dict(out=tmp_path / "n.jsonl.gz", runs_out=tmp_path / "n_runs.jsonl")
    recs = rn.run([q], workers=1, **paths)
    assert len(recs) == 3 and "Please think step by step" in calls[0][0] and calls[0][0].endswith("<think>")
    assert calls[0][1]["max_tokens"] == 32768 - len(calls[0][0]) // 4 and calls[0][1]["extra"] is None   # one capped request
    by_rep = {r["repeat"]: r for r in recs}
    assert by_rep[0]["parsed_letter"] == "B" and by_rep[0]["no_hint_source"] == "voyager" and by_rep[0]["gen_seconds"] >= 0
    assert by_rep[2]["parsed_letter"] is None and by_rep[2]["parsed_letter_if_not_cut"] == "B"     # cut off: no answer
    assert rn.run([q], workers=1, **paths) == []                                                 # resumable
    kept, reasons = rn.report([q], rn.latest(rn.load(paths["out"])))
    assert kept == 0 and reasons == {"a no-hint run was cut off": 1}
