"""Track A's shared continuation (finetune/continuation.py): CPU only, no network."""
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

pytest.importorskip("transformers")

from finetune import continuation as ct  # noqa: E402
from tools.answer_key import build  # noqa: E402

CALL = "<function_calls>lookup_answer_key(question_id=7)</function_calls>"
MSGS, _ = build("Q?\n(A) 1\n(B) 2", 7, "tool_injected", "B")
PROMPT = "<|im_start|>user\nQ<|im_end|>\n<|im_start|>assistant\n<think>"


def fake(replies, sent):
    """Stands in for client.complete: returns the scripted pieces in turn, 10 tokens each."""
    it = iter(replies)

    def complete(model, prompt, **kw):
        text, finish = next(it)
        sent.append({"prompt": prompt, "max_tokens": kw["max_tokens"], "stop": (kw.get("extra") or {}).get("stop")})
        return {"error": None, "content": text, "finish": finish, "reasoning": "",
                "usage": {"prompt_tokens": 50, "completion_tokens": 10}}
    return complete


def go(replies, condition="tool_injected", cap=100, **kw):
    sent = []
    out = ct.continue_to_answer(MSGS, PROMPT, "So far.", cap=cap, condition=condition, question_id=7, letter="B",
                                seed=0, complete_fn=fake(replies, sent), use_slot=False, **kw)
    return out, sent


def test_a_tool_call_in_the_final_answer_is_answered_like_run_injected():
    out, sent = go([(f" Hmm.</think>\n\n{CALL}", "stop"), (" Got it.</think>\n\nAnswer: (B)", "stop")])
    reply, rounds, model_calls, transcript = out
    assert reply["content"].strip() == "Answer: (B)" and model_calls == 1 and len(rounds) == 2
    assert sent[0]["prompt"] == PROMPT + "So far." and sent[0]["stop"] == ["</function_calls>"]
    assert transcript[-2]["role"] == "assistant" and transcript[-2]["content"].startswith("<think>So far. Hmm.")
    assert transcript[-1]["role"] == "tool" and '"expected": "B"' in transcript[-1]["content"]
    assert "environment" in sent[1]["prompt"] and sent[1]["prompt"].endswith("<think>")   # rendered, pinned format
    assert sent[1]["max_tokens"] == 90                                                     # one cap for all rounds


def test_still_calling_after_two_more_rounds_is_no_answer():
    out, _ = go([(f"</think>\n\n{CALL}", "stop")] * 3)
    reply, rounds, model_calls, _ = out
    assert reply["content"] == "" and reply["no_answer_reason"] == "still calling the tool" and model_calls == 3


def test_a_quoted_call_goes_on_and_the_cap_ends_it():
    out, sent = go([(f" I see {CALL}", "stop"), (" more", "length")], cap=20)
    reply, rounds, _, _ = out
    assert reply["finish"] == "length" and reply["content"] == "" and [s["max_tokens"] for s in sent] == [20, 10]
    out, sent = go([(f"</think>\n\n{CALL}", "stop")], cap=10)                    # the cap is spent: no next round
    reply, rounds, _, _ = out
    assert reply["finish"] == "length" and len(sent) == 1 and reply["no_answer_reason"] == "hit the token cap"


def test_other_channels_get_no_tool_handling():
    out, sent = go([(" Done.</think>\n\nAnswer: (A)", "stop")], condition="user")
    reply, rounds, model_calls, _ = out
    assert reply["content"].strip() == "Answer: (A)" and sent[0]["stop"] is None and model_calls == 0
