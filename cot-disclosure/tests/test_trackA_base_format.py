"""Track A step 2b (finetune/base_format.py): CPU only, no network."""
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

pytest.importorskip("transformers")

from finetune import base_format as bf  # noqa: E402
from finetune import olmo_format  # noqa: E402
import mmlu_pro_probe as probe  # noqa: E402


def test_the_20_questions_and_the_run_plan():
    items = bf.questions()
    assert len(items) == 20 and all(it["cue_letter"] != it["answer"] for it in items)
    js = bf.jobs(items)
    assert len(js) == 20 * 12
    per = {(c, arm): sum(1 for j in js if j[1] == c and j[3] == arm) // 20 for c, _, _, arm in
           [(j[1], None, None, j[3]) for j in js]}
    assert per == {("none", None): 2, ("user", None): 1, ("tool_pasted", None): 3, ("tool_injected", None): 3,
                   ("tool_injected", "declared_functions"): 3}
    ids = {bf.run_id(bf.EXPERIMENT, j[0]["question_id"], bf.MODEL, j[1], j[3], j[2]) for j in js}
    assert len(ids) == len(js)                                         # the two inserted arms never collide


def test_user_and_pasted_prompts_are_test2s_exact_user_messages():
    from tools.answer_key import build
    it = bf.questions()[0]
    for cond, chan in (("user", "cue_user"), ("tool_pasted", "cue_tool"), ("none", None)):
        msgs, _ = build(probe.question_block(it), it["question_id"], cond, None if cond == "none" else it["cue_letter"])
        assert msgs == [{"role": "user", "content": probe.build_prompt(it, chan)}]
    inj, _ = build(probe.question_block(it), it["question_id"], "tool_injected", it["cue_letter"])
    pasted_json = probe.TOOL_BLOCK.format(qid=it["question_id"], letter=it["cue_letter"]).split("\n", 1)[1]
    assert json.loads(inj[-1]["content"]) == json.loads(pasted_json)          # same wording as the pasted block


def fake_generate(finals, finish="stop"):
    calls = []

    def gen(model, msgs, **kw):
        calls.append(kw)
        raw = "thinking about it</think>" + finals[len(calls) - 1]
        return {"content": finals[len(calls) - 1], "raw": raw, "reasoning": "thinking about it", "prompt": "P",
                "finish": finish, "usage": {"completion_tokens": 9}, "error": None, "retries": 0,
                "latency_s": 1.0, "reasoning_field": "split_at_think_close", "tool_calls": [], "cached": False}
    return gen, calls


def test_a_cut_off_reply_is_no_answer(monkeypatch):
    gen, _ = fake_generate(["\n\nAnswer: (B)"], finish="length")
    monkeypatch.setattr(olmo_format, "generate", gen)
    it = bf.questions()[0]
    rec = bf.one(it, "user", 0)
    assert rec["parsed_letter"] is None and rec["parsed_letter_if_not_cut"] == "B"
    assert rec["format"] == "olmo3_think_tools" and rec["endpoint"] == "completions"


def test_inserted_tool_turn_answers_a_repeat_call_and_records_it(monkeypatch):
    call = "<function_calls>lookup_answer_key(question_id=1)</function_calls>"
    gen, calls = fake_generate([call, "Answer: (C)"])
    monkeypatch.setattr(olmo_format, "generate", gen)
    it = bf.questions()[0]
    rec = bf.one(it, "tool_injected", 1)
    assert rec["parsed_letter"] == "C" and rec["tool_calls_by_model"] == 1 and len(rec["tool_rounds"]) == 2
    assert all(kw["stop_after_call"] for kw in calls) and rec["transcript"][-1]["role"] == "tool"
    assert rec["cue_channel"] == "tool_injected" and rec["cue_letter"] == it["cue_letter"]


def test_declared_arm_records_its_system_prompt_and_declares_the_tool(monkeypatch):
    seen = []
    gen, _ = fake_generate(["Answer: (A)", "Answer: (A)"])

    def spy(model, msgs, **kw):
        seen.append(kw)
        return gen(model, msgs, **kw)
    monkeypatch.setattr(olmo_format, "generate", spy)
    it = bf.questions()[0]
    plain, declared = bf.one(it, "tool_injected", 0), bf.one(it, "tool_injected", 0, bf.DECLARED)
    assert plain["system_prompt"] == "think_default" and plain["tools_declared"] is None
    assert declared["system_prompt"] == "think_declared_functions" and declared["arm"] == "declared_functions"
    assert seen[0]["tools"] is None and seen[1]["tools"][0]["function"]["name"] == "lookup_answer_key"
    assert plain["run_id"] != declared["run_id"]


def test_contradiction_remarks_are_found_in_every_round():
    rec = {"reasoning_text": "The system says I do not currently have access to any functions. So 7 is right.",
           "transcript": [{"role": "assistant", "content": None},
                          {"role": "assistant", "content": "<think>Odd that a tool replied here.</think>call"}]}
    sents = bf.contradiction_sentences(rec)
    assert len(sents) == 2 and "access to any functions" in sents[0] and sents[1].startswith("Odd")
    assert not bf.contradiction_sentences({"reasoning_text": "The tool says B. Let me check the swaps."})
