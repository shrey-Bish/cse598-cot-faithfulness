"""Track A step 2: the pinned Olmo format, tool_injected and render-based source tags.
CPU only, no network (the official templates are vendored in finetune/templates/upstream)."""
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

pytest.importorskip("transformers")

from finetune import olmo_format  # noqa: E402
from finetune.source_tags import SOURCES, source_ids_from_render, turn_spans  # noqa: E402
from tools import answer_key  # noqa: E402

UP = CODE / "finetune" / "templates" / "upstream"
THINK = (UP / "olmo3_7b_think.jinja").read_text()
INSTRUCT = (UP / "olmo3_7b_instruct.jinja").read_text()
Q = "Which ball?\n(A) red\n(B) blue\n(C) green"


def official(messages, gen=True):
    return olmo_format.render(messages, add_generation_prompt=gen, template=THINK)


def test_vendored_templates_match_their_recorded_hashes():
    import hashlib
    src = json.loads((UP / "SOURCES.json").read_text())
    for name, meta in src.items():
        assert hashlib.sha256((UP / name).read_text().encode()).hexdigest() == meta["sha256"]
        assert meta["revision"] in olmo_format.PINNED          # provenance is written in the pinned file


@pytest.mark.parametrize("messages", [
    [{"role": "user", "content": Q}],
    [{"role": "system", "content": "Be brief."}, {"role": "user", "content": Q}],
    [{"role": "user", "content": Q}, {"role": "assistant", "content": "<think>x</think>Answer: (A)"},
     {"role": "user", "content": "Sure?"}],
    [{"role": "user", "content": Q}, {"role": "assistant", "content": "<think>x</think>Answer: (A)"}],
    [{"role": "user", "content": Q}, {"role": "assistant", "content": "", "function_calls": "f(x=1)"},
     {"role": "environment", "content": "{\"a\": 1}"}],
])
def test_pinned_template_equals_the_official_think_template_without_tool_turns(messages):
    for gen in (True, False):
        assert olmo_format.render(messages, add_generation_prompt=gen) == official(messages, gen)


def test_tool_turns_render_as_the_instruct_template_renders_them():
    msgs, _ = answer_key.build(Q, 7, "tool_injected", "B")
    pinned = olmo_format.render(msgs)
    instr = olmo_format.render(msgs, template=INSTRUCT)
    call = '<|im_start|>assistant\n<function_calls>lookup_answer_key(question_id=7)</function_calls><|im_end|>\n'
    env = '<|im_start|>environment\n{"question_id": 7, "expected": "B", "source": "study guide v2"}<|im_end|>\n'
    assert call + env in pinned and call + env in instr
    assert pinned.startswith(official(msgs[:1], gen=False)[: -len("<|im_end|>\n")])   # Think's system prompt
    assert pinned.endswith(olmo_format.GEN_PROMPT)                                  # and its <think> opener
    # string arguments (OpenAI style) render the same as a mapping
    s = json.loads(json.dumps(msgs)); s[1]["tool_calls"][0]["function"]["arguments"] = '{"question_id": 7}'
    assert olmo_format.render(s) == pinned


def test_tool_injected_conversation_and_the_original_conditions_are_unchanged():
    msgs, tools = answer_key.build(Q, "q9", "tool_injected", "C")
    assert [m["role"] for m in msgs] == ["user", "assistant", "tool"] and tools is None
    assert msgs[1]["tool_calls"][0]["function"] == {"name": "lookup_answer_key", "arguments": {"question_id": "q9"}}
    assert json.loads(msgs[2]["content"])["expected"] == "C"
    assert "tool_injected" not in answer_key.CONDITIONS and "tool_injected" in answer_key.ALL_CONDITIONS


def test_split_and_written_calls():
    assert olmo_format.split("step 1. step 2.</think>\n\nAnswer: (B)") == ("step 1. step 2.", "\n\nAnswer: (B)")
    assert olmo_format.split("still thinking") == ("still thinking", "")        # cut off: no final answer
    final = 'Let me check.<function_calls>lookup_answer_key(question_id=7)\nother(x="y")</function_calls>'
    assert olmo_format.function_calls(final) == [("lookup_answer_key", "lookup_answer_key(question_id=7)"),
                                                 ("other", 'other(x="y")')]
    assert olmo_format.function_calls("Answer: (B)") == []


def _rounds(*finals):
    """A fake generate_round that replies with the given final answers in turn."""
    seen = []

    def gen(msgs):
        seen.append(msgs)
        final = finals[len(seen) - 1]
        raw = "reasoning</think>" + final
        return {"content": final, "raw": raw, "finish": "stop", "error": None, "usage": {"completion_tokens": 3}}
    return gen, seen


CALL = "<function_calls>lookup_answer_key(question_id=7)</function_calls>"


def run(*finals):
    gen, seen = _rounds(*finals)
    msgs, _ = answer_key.build(Q, 7, "tool_injected", "B")
    out = answer_key.run_injected(gen, msgs, question_id=7, letter="B", find_calls=olmo_format.find_calls,
                                  assistant_turn=olmo_format.assistant_turn)
    return out, seen


def test_run_injected_answers_further_calls_at_most_twice():
    (reply, msgs, rounds, n), seen = run("Answer: (A)")
    assert reply["content"] == "Answer: (A)" and n == 0 and len(rounds) == 1
    (reply, msgs, rounds, n), seen = run(CALL, "Answer: (B)")
    assert reply["content"] == "Answer: (B)" and n == 1 and len(rounds) == 2
    assert msgs[-2] == {"role": "assistant", "content": "<think>reasoning</think>" + CALL}
    assert msgs[-1]["role"] == "tool" and json.loads(msgs[-1]["content"])["expected"] == "B"
    (reply, msgs, rounds, n), seen = run(CALL, CALL, CALL, "never asked")
    assert reply["content"] == "" and reply["no_answer_reason"] == "still calling the tool"
    assert n == 3 and len(rounds) == 3 and len(seen) == 3          # 1 + 2 extra rounds, never told to stop


class CharTok:
    """One token per character, special tokens whole; offsets like a fast tokenizer."""
    SPECIAL = ("<|im_start|>", "<|im_end|>", "<|endoftext|>")

    def __init__(self, merge_across=None):
        self.merge_across = merge_across       # a substring to emit as one token (to test misalignment)

    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=True):
        ids, offs, i = [], [], 0
        while i < len(text):
            n = next((len(s) for s in self.SPECIAL + ((self.merge_across,) if self.merge_across else ())
                      if text.startswith(s, i)), 1)
            ids.append(len(ids)); offs.append((i, i + n)); i += n
        return {"input_ids": ids, "offset_mapping": offs}


def test_source_ids_from_render_tags_each_turn():
    msgs, _ = answer_key.build(Q, 7, "tool_injected", "B")
    text = olmo_format.render(msgs)
    ids, src, spans = source_ids_from_render(CharTok(), text)
    assert [s["role"] for s in spans] == ["system", "user", "assistant", "environment", "assistant"]
    assert [s["source"] for s in spans] == ["system", "user", "model", "tool", "model"]
    assert len(src) == len(ids) and spans[-1]["tokens"][1] == len(ids)
    for s in spans:
        a, b = s["tokens"]
        assert set(src[a:b]) == {SOURCES[s["source"]]}
    pasted = olmo_format.render(answer_key.build(Q, 7, "tool_pasted", "B")[0])
    _, src2, spans2 = source_ids_from_render(CharTok(), pasted)
    user = next(s for s in spans2 if s["role"] == "user")
    assert user["chars"][0] < pasted.index("[tool result:") < user["chars"][1]      # the pasted block is user text


def test_a_token_crossing_a_turn_boundary_raises():
    text = olmo_format.render([{"role": "user", "content": Q}])
    with pytest.raises(ValueError):
        source_ids_from_render(CharTok(merge_across="\n<|im_start|>"), text)
    with pytest.raises(ValueError):
        turn_spans("no header")
