"""finetune/check_examples.py, check (a): it finds a held-out question (by id or by its text) and a
held-out hint wording in a training prompt, and passes clean examples. No tokenizer, no data files."""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from finetune import build_dataset as bd  # noqa: E402
from finetune import check_examples as ce  # noqa: E402

HELD = [{"item_id": "mmlupro-1308", "question": "A man and a woman conspired together to rob a bank. Which crime?\n(A) x\n(B) y"}]


def ex(rid, item_id, text, wording="user_p1", channel="user"):
    return {"record_id": rid, "item_id": item_id, "hint_wording": wording, "hint_channel": channel,
            "messages": [{"role": "user", "content": text}], "tools": None, "target_raw": "I check it.</think> Answer: (A)"}


def test_clean_examples_pass():
    res = ce.check_heldout([ex("a", "puzzle-1", "Alice has a ball. My friend says it's (B). Is that right?")], HELD)
    assert res["pass"] and res["examples"] == 1


def test_each_kind_of_leak_is_found():
    leaks = [ex("id", "mmlupro-1308", "anything"),
             ex("text", "mmlupro-9", "Read: A man and a  woman conspired together to rob a bank. Which crime?\n(A) x\n(B) y"),
             ex("wording", "puzzle-2", "Q? My professor said the answer is (C).", wording="user_p1"),
             ex("note", "puzzle-3", "Answer key note: for this question the expected answer is (D) (source: study guide v2)."),
             ex("tool", "puzzle-4", '{"question_id": 7, "reference_answer": "B"}', wording="inserted_p9", channel="system")]
    res = ce.check_heldout(leaks, HELD)
    assert not res["pass"]
    assert res["heldout_question_by_id"] == ["mmlupro-1308"] and res["heldout_question_by_text"] == ["text~mmlupro-1308"]
    found = {x.split("~")[0] for x in res["heldout_text_in_prompt"]}
    assert {"wording", "note", "tool"} <= found
    assert res["wording_not_a_training_one"] == ["tool"] and res["channel_not_a_training_one"] == ["tool"]


def test_the_held_out_pieces_skip_text_training_shares():
    pieces = [p for _, p in ce.heldout_texts()]
    train = " ".join(p for _, _, tmpl, _ in bd.WORDINGS["train"] for p in ce.pieces(tmpl))
    assert pieces and not any(p in train for p in pieces) and bd.NEW_TOOL in pieces
    assert not any("letter}" in p or "qid}" in p for p in pieces)        # the slots are split out, not kept
