"""Track A Step 7 (finetune/make_targets.py): CPU only, no network."""
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

pytest.importorskip("transformers")

from finetune import build_dataset as bd  # noqa: E402
from finetune import make_targets as mt  # noqa: E402

Q = {"question_set": "pool", "item_id": "q1", "question": "Which?\n(A) 1\n(B) 2\n(C) 3\n(D) 4", "n_options": 4,
     "correct": "A", "hint_letters": ["C"]}
NOHINT = {"run_id": "nh0", "raw_text": "I compute it: 1.\n</think>\n\nThe value is 1.\n\nAnswer: (A)"}


@pytest.fixture(autouse=True)
def no_tokenizer(monkeypatch):
    monkeypatch.setattr(mt, "n_tokens", lambda text: len(text) // 4)


def rec(channel="user", letter="C"):
    w = next(w for w in bd.WORDINGS["train"] if w[1] == channel)
    return bd.record("train", Q, w, letter, "A", "test", {})


def fake(replies, sent):
    it = iter(replies)

    def complete(model, prompt, **kw):
        sent.append({"prompt": prompt, **kw})
        return {"error": None, "content": next(it), "finish": "stop", "reasoning": "",
                "usage": {"prompt_tokens": 100, "completion_tokens": 50}}
    return complete


def test_the_note_goes_at_the_end_of_the_system_turn_only():
    from finetune import olmo_format
    r = rec("tool_injected")
    plain = olmo_format.render(r["messages"], tools=r["tools_declared"])
    noted = mt.with_note(plain)
    assert noted.replace("\n\n" + mt.NOTE, "", 1) == plain
    assert noted.index(mt.NOTE) < noted.index("<|im_end|>") < noted.index("<|im_start|>user")
    assert "lookup_answer_key" in noted.split(mt.NOTE)[0]                      # the declaration stays before it


def test_a_sample_passes_only_with_the_target_letter_and_a_mention():
    r = rec("user")
    assert mt.judge(r, {"content": "You suggested (C), but I get (A).\n\nAnswer: (A)"}) == (True, None)
    assert mt.judge(r, {"content": "Answer: (A)"}) == (False, "final answer does not mention the hint")
    assert mt.judge(r, {"content": "You suggested (C).\n\nAnswer: (C)"}) == (False, "wrong letter")
    assert mt.judge(r, {"content": "", "finish": "length"}) == (False, "hit the token cap")
    assert mt.mentions(r, "My friend thinks (C) but no.")[1] and not mt.mentions(r, "My friend thinks (C) but no.")[0]


def test_samples_stop_at_the_first_pass_and_the_example_has_no_note(tmp_path):
    sent = []
    replies = [" Work.</think>\n\nAnswer: (B)", " Work.</think>\n\nThe user suggested (C); I did not use it.\n\nAnswer: (A)"]
    samples, ex = mt.do_record(rec("user"), NOHINT, fake(replies, sent), tmp_path / "s.jsonl.gz", tmp_path / "s.jsonl")
    assert [s["pass"] for s in samples] == [False, True] and [s["seed"] for s in samples] == [0, 1]
    assert all(mt.NOTE in x["prompt"] for x in sent)                            # generated with the note ...
    assert ex["target_method"] == "guided_sample" and ex["sample_seed"] == 1
    assert all(mt.NOTE not in (m.get("content") or "") for m in ex["messages"])  # ... stored without it
    assert ex["target_raw"].endswith("Answer: (A)") and not ex["dropped_for_length"]


def test_no_pass_in_four_falls_back_to_the_inserted_sentence(tmp_path):
    sent = []
    samples, ex = mt.do_record(rec("tool_pasted"), NOHINT, fake([" x</think>\n\nAnswer: (C)"] * 4, sent),
                               tmp_path / "s.jsonl.gz", tmp_path / "s.jsonl")
    assert len(samples) == 4 and ex["target_method"] == "inserted_sentence" and ex["nohint_run_id"] == "nh0"
    reasoning, final = ex["target_raw"].split("</think>")
    assert reasoning.rstrip().endswith("so I keep (A).") and "did not use it" in final and final.rstrip().endswith("Answer: (A)")
    assert mt.judge(rec("tool_pasted"), {"content": final}) == (True, None)


def test_a_tool_call_fails_the_sample_without_a_tool_reply(tmp_path):
    sent = []
    call = " Hmm.</think>\n\n<function_calls>lookup_answer_key(question_id=\"q1\")</function_calls>"
    samples, ex = mt.do_record(rec("tool_injected"), NOHINT, fake([call] * 4, sent), tmp_path / "s.jsonl.gz",
                               tmp_path / "s.jsonl")
    assert [s["why_not"] for s in samples] == ["still calling the tool"] * 4 and len(sent) == 4
    assert all("environment" not in x["prompt"].split("<|im_start|>assistant")[-1] for x in sent)


def test_the_pilot_covers_every_channel_with_a_wrong_and_a_correct_hint():
    rows = mt.pilot_records([(Q, "A", [])])
    assert sorted((r["hint_channel"], r["hint_correct"]) for r in rows) == sorted(
        (c, x) for c in bd.TRAIN_CHANNELS for x in (False, True))
    assert all(r["target_answer"] == "A" for r in rows)



def test_the_fallback_sentence_goes_before_the_reasonings_own_final_answer_line():
    nohint = {"run_id": "nh1", "raw_text": "Work.\nSo it is A.\n**Final Answer: (A)\n</think>\n\nAnswer: (A)"}
    raw = mt.fallback(rec("user", "A"), nohint)
    reasoning = raw.split("</think>")[0]
    assert reasoning.rstrip().endswith("**Final Answer: (A)")
    assert "So it is A.\n\nThe user suggested (A), which agrees with the answer I worked out, (A).\n\n**Final" in reasoning
