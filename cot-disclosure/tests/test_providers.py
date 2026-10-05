"""Provider adapters (mocked HTTP), the budget guard, and the answer-key tool loop."""
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

import providers  # noqa: E402
from providers import anthropic, budget, ollama, openai, responses_api  # noqa: E402
from providers.base import AUTH_HEADER, MissingKey, Reply, provider_key  # noqa: E402
from providers.config import resolve_effort  # noqa: E402
from tools import answer_key  # noqa: E402


# ---------------------------------------------------------------- keys and budget
def test_provider_key_refuses_the_voyager_key(monkeypatch):
    monkeypatch.setenv("RC_LLM_API_KEY", "sk-same")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-same")
    with pytest.raises(MissingKey):
        provider_key("OpenAI", "OPENAI_API_KEY")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-different")
    assert provider_key("OpenAI", "OPENAI_API_KEY") == "sk-different"


def test_cost_and_table():
    assert budget.cost("gpt-6-luna", 1_000_000, 1_000_000) == pytest.approx(0.60)
    rows = {r["model"]: r for r in budget.table(500, 4000)}
    assert rows["claude-haiku-4-5-20251001"]["usd_per_call"] == pytest.approx((500 * 1 + 4000 * 5) / 1e6)


def test_guard_refuses_past_cap_and_record_accumulates(tmp_path, monkeypatch):
    log = tmp_path / "spend.jsonl"
    monkeypatch.setenv("ANTHROPIC_CAP_USD", "0.05")
    msgs = [{"role": "user", "content": "x" * 400}]
    budget.guard("anthropic", "claude-haiku-4-5-20251001", msgs, 4000, log=log)       # ~ $0.02 worst case: ok
    budget.record("anthropic", "claude-haiku-4-5-20251001", {"input_tokens": 100, "output_tokens": 6000}, log=log)
    assert budget.spent("anthropic", log) == pytest.approx((100 * 1 + 6000 * 5) / 1e6)
    with pytest.raises(budget.BudgetExceeded):
        budget.guard("anthropic", "claude-haiku-4-5-20251001", msgs, 4000, log=log)  # 0.0301 + 0.02 > 0.05
    assert budget.guard("voyager", "olmo3-7b-think", msgs, 16000, log=log) == 0.0     # free providers pass


# ---------------------------------------------------------------- OpenAI / xAI (Responses API)
def test_effort_rules():
    assert resolve_effort("gpt-6-luna", False) == "none"
    assert resolve_effort("gpt-6-luna", True) == "medium"
    with pytest.raises(ValueError):
        resolve_effort("gpt-6-astra", False)
    with pytest.raises(ValueError):
        resolve_effort("grok-4.7", False)


def test_responses_request_shapes():
    msgs, tools = answer_key.build("Q?\n(A) a\n(B) b", "q1", "tool_real", "B")
    req = responses_api.build_request("gpt-6-luna", msgs, provider="openai", tools=tools,
                                      tool_choice={"type": "function", "function": {"name": "lookup_answer_key"}},
                                      effort="medium", max_tokens=4000, temperature=0.6)
    assert req["reasoning"] == {"effort": "medium", "summary": "auto"} and "temperature" not in req
    assert req["tools"][0]["name"] == "lookup_answer_key" and "function" not in req["tools"][0]
    assert req["tool_choice"] == {"type": "function", "name": "lookup_answer_key"}
    off = responses_api.build_request("gpt-6-luna", msgs, provider="openai", effort="none", temperature=0.6)
    assert off["temperature"] == 0.6 and off["reasoning"] == {"effort": "none"}


def test_responses_parse_and_tool_echo():
    body = {"status": "completed", "output": [
        {"type": "reasoning", "id": "rs_1", "summary": [{"type": "summary_text", "text": "Checked the key."}]},
        {"type": "function_call", "call_id": "call_9", "name": "lookup_answer_key", "arguments": "{\"question_id\": \"q1\"}"}],
        "usage": {"input_tokens": 50, "output_tokens": 300, "output_tokens_details": {"reasoning_tokens": 250}}}
    text, summary, calls, usage, finish, native = responses_api.parse_response(body)
    assert summary == "Checked the key." and finish == "tool_calls" and usage["reasoning_tokens"] == 250
    assert calls == [{"id": "call_9", "name": "lookup_answer_key", "arguments": "{\"question_id\": \"q1\"}"}]
    from providers.base import assistant_tool_message
    reply = Reply(provider="openai", model="gpt-6-luna", tool_calls=calls, raw={"native_items": native})
    turn = assistant_tool_message(reply)
    items = responses_api.to_input([turn, {"role": "tool", "tool_call_id": "call_9", "content": "{}"}], "openai")
    assert items[0]["type"] == "reasoning" and items[1]["type"] == "function_call"   # echoed unchanged
    assert items[2] == {"type": "function_call_output", "call_id": "call_9", "output": "{}"}
    assert responses_api.to_input([turn], "xai")[0]["type"] == "function_call"       # other providers ignore it
    trunc = responses_api.parse_response({"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"}})
    assert trunc[4] == "length"


def test_openai_generate_end_to_end_mocked(monkeypatch, tmp_path):
    monkeypatch.setenv("RC_LLM_API_KEY", "sk-voyager")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
    monkeypatch.setattr(budget, "LOG", tmp_path / "spend.jsonl")
    sent = {}

    def fake_post(url, headers, payload, timeout=600):
        sent.update(url=url, payload=payload, auth=headers[AUTH_HEADER])
        return 200, {"status": "completed", "output": [
            {"type": "message", "content": [{"type": "output_text", "text": "Answer: (B)"}]}],
            "usage": {"input_tokens": 100, "output_tokens": 1000}}
    monkeypatch.setattr(openai, "post_json", fake_post)
    msgs, _ = answer_key.build("Q?\n(A) a\n(B) b", "q1", "user", "B")
    reply = providers.generate("openai", "gpt-6-luna", msgs, max_tokens=2000, temperature=0.6, seed=0)
    assert reply.final_text == "Answer: (B)" and reply.reasoning_visibility == "none"
    assert sent["url"].endswith("/v1/responses") and sent["auth"] == "Bearer sk-openai" and "seed" not in sent["payload"]
    assert reply.raw["seed_ignored"] and reply.cost_usd == pytest.approx((100 * 0.10 + 1000 * 0.50) / 1e6)
    assert budget.spent("openai", tmp_path / "spend.jsonl") == pytest.approx(reply.cost_usd)


# ---------------------------------------------------------------- Anthropic
def test_anthropic_thinking_modes():
    msgs = [{"role": "system", "content": "S"}, {"role": "user", "content": "Q"}]
    on, _ = anthropic.build_request("claude-haiku-4-5-20251001", msgs, thinking=True, max_tokens=4000, temperature=0.6)
    assert on["thinking"] == {"type": "enabled", "budget_tokens": 3000} and "temperature" not in on
    assert on["system"] == "S" and on["messages"] == [{"role": "user", "content": "Q"}]
    off, _ = anthropic.build_request("claude-haiku-4-5-20251001", msgs, thinking=False, max_tokens=4000, temperature=0.6)
    assert "thinking" not in off and off["temperature"] == 0.6
    ad, notes = anthropic.build_request("claude-opus-5-5", msgs, max_tokens=4000, temperature=0.6)
    assert ad["thinking"] == {"type": "adaptive", "display": "summarized"} and ad["output_config"] == {"effort": "medium"}
    assert "temperature" not in ad and notes["temperature_not_sent"]
    with pytest.raises(ValueError):
        anthropic.build_request("claude-opus-5-5", msgs, thinking=False)


def test_anthropic_tools_and_parse():
    msgs, tools = answer_key.build("Q?", "q1", "tool_real", "B")
    req, notes = anthropic.build_request("claude-haiku-4-5-20251001", msgs, tools=tools, thinking=True,
                                         tool_choice={"type": "function", "function": {"name": "lookup_answer_key"}})
    assert req["tools"][0]["input_schema"]["required"] == ["question_id"]
    assert req["tool_choice"] == {"type": "auto"} and "tool_choice_downgraded" in notes
    convo = msgs + [{"role": "assistant", "content": None, "tool_calls": [
        {"id": "toolu_1", "type": "function", "function": {"name": "lookup_answer_key", "arguments": "{\"question_id\": \"q1\"}"}}]},
        {"role": "tool", "tool_call_id": "toolu_1", "name": "lookup_answer_key", "content": "{\"expected\": \"B\"}"}]
    _, converted = anthropic.to_messages(convo)
    assert converted[1]["content"][0] == {"type": "tool_use", "id": "toolu_1", "name": "lookup_answer_key",
                                          "input": {"question_id": "q1"}}
    assert converted[2] == {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_1",
                                                         "content": "{\"expected\": \"B\"}"}]}
    body = {"stop_reason": "end_turn", "content": [{"type": "thinking", "thinking": "summary", "signature": "x"},
                                                   {"type": "text", "text": "Answer: (B)"}],
            "usage": {"input_tokens": 10, "output_tokens": 20}}
    text, summary, calls, usage, finish, redacted = anthropic.parse_response(body)
    assert (text, summary, finish, calls) == ("Answer: (B)", "summary", "stop", [])


# ---------------------------------------------------------------- Ollama
def test_ollama_request_and_parse():
    msgs, tools = answer_key.build("Q?", "q1", "tool_real", "B")
    req = ollama.build_request("qwen3:8b", msgs, tools=tools, thinking=False, max_tokens=100, temperature=0.6, seed=1)
    assert req["think"] is False and req["options"] == {"num_predict": 100, "temperature": 0.6, "seed": 1}
    text, thinking, calls, usage, finish = ollama.parse_response({
        "message": {"content": "", "thinking": "hmm", "tool_calls": [
            {"function": {"name": "lookup_answer_key", "arguments": {"question_id": "q1"}}}]},
        "done_reason": "stop", "prompt_eval_count": 5, "eval_count": 9})
    assert calls == [{"id": "ollama-call-0", "name": "lookup_answer_key", "arguments": "{\"question_id\": \"q1\"}"}]
    assert thinking == "hmm" and finish == "tool_calls" and usage["output_tokens"] == 9
    back = ollama.to_messages([{"role": "tool", "tool_call_id": "ollama-call-0", "name": "lookup_answer_key",
                                "content": "{}"}])
    assert back == [{"role": "tool", "tool_name": "lookup_answer_key", "content": "{}"}]


# ---------------------------------------------------------------- hint conditions and the tool loop
def test_conditions_and_pasted_block_match_the_progress_run():
    sys.path.insert(0, str(CODE / "progress"))
    from mmlu_pro_probe import TOOL_BLOCK
    assert answer_key.PASTED == TOOL_BLOCK
    q = "Q?\n(A) a\n(B) b"
    for cond in answer_key.CONDITIONS:
        msgs, tools = answer_key.build(q, 7, cond, None if cond == "none" else "B")
        assert msgs[-1]["role"] == "user" and msgs[-1]["content"].startswith(q)
        assert (tools is not None) == (cond == "tool_real")
    assert answer_key.build(q, 7, "system", "B")[0][0] == {"role": "system", "content": answer_key.SYSTEM_HINT.format(letter="B")}
    with pytest.raises(ValueError):
        answer_key.build(q, 7, "user", None)


def test_tool_loop_returns_the_wrong_letter_as_a_tool_message():
    replies = [Reply(provider="fake", model="m", tool_calls=[{"id": "c1", "name": "lookup_answer_key",
                                                              "arguments": "{\"question_id\": \"q1\"}"}],
                     finish_reason="tool_calls"),
               Reply(provider="fake", model="m", final_text="Answer: (B)", finish_reason="stop")]
    seen = []

    def fake_generate(**kw):
        seen.append(kw)
        return replies[len(seen) - 1]
    msgs, tools = answer_key.build("Q?", "q1", "tool_real", "B")
    final, transcript, log = answer_key.run_tool_loop(fake_generate, msgs, tools, question_id="q1", letter="B")
    assert final.final_text == "Answer: (B)" and len(log) == 2
    assert seen[0]["tool_choice"] == {"type": "function", "function": {"name": "lookup_answer_key"}}
    assert seen[1]["tool_choice"] is None
    tool_msg = transcript[-1]
    assert tool_msg["role"] == "tool" and tool_msg["tool_call_id"] == "c1"
    assert json.loads(tool_msg["content"]) == {"question_id": "q1", "expected": "B", "source": "study guide v2"}
