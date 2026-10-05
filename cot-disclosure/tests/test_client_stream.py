"""SSE parsing in client.py: content, reasoning field name, usage, and streamed tool calls."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from client import parse_stream_lines  # noqa: E402


def sse(obj):
    return f"data: {json.dumps(obj)}".encode()


def test_content_reasoning_usage():
    lines = [sse({"choices": [{"delta": {"reasoning": "think "}}]}),
             sse({"choices": [{"delta": {"reasoning": "more"}}]}),
             sse({"choices": [{"delta": {"content": "Answer: (B)"}, "finish_reason": "stop"}]}),
             sse({"choices": [], "usage": {"completion_tokens": 7}}), b"data: [DONE]"]
    out = parse_stream_lines(lines)
    assert out["content"] == "Answer: (B)" and out["reasoning"] == "think more"
    assert out["reasoning_field"] == "reasoning" and out["finish"] == "stop"
    assert out["usage"] == {"completion_tokens": 7} and out["tool_calls"] == []


def test_streamed_tool_call_fragments_are_joined():
    lines = [sse({"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "call_1", "type": "function",
                                                         "function": {"name": "lookup_answer_key", "arguments": ""}}]}}]}),
             sse({"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": "{\"question_"}}]}}]}),
             sse({"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": "id\": \"7\"}"}}]},
                               "finish_reason": "tool_calls"}]}),
             b"data: [DONE]"]
    out = parse_stream_lines(lines)
    assert out["finish"] == "tool_calls"
    assert out["tool_calls"] == [{"id": "call_1", "type": "function",
                                  "function": {"name": "lookup_answer_key", "arguments": "{\"question_id\": \"7\"}"}}]


def test_iter_stream_lines_yields_pieces_then_the_folded_result():
    from client import iter_stream_lines
    lines = [sse({"choices": [{"delta": {"reasoning": "think "}}]}),
             sse({"choices": [{"delta": {"content": "Answer: "}}]}),
             sse({"choices": [{"delta": {"content": "(B)"}, "finish_reason": "stop"}]}),
             sse({"choices": [], "usage": {"completion_tokens": 3}}), b"data: [DONE]"]
    events = list(iter_stream_lines(lines))
    assert events[:3] == [("reasoning", "think "), ("content", "Answer: "), ("content", "(B)")]
    kind, folded = events[-1]
    assert kind == "end" and folded == parse_stream_lines(lines)


def test_chat_live_replays_a_cached_reply_without_network(tmp_path, monkeypatch):
    import client
    monkeypatch.setattr(client, "CACHE_DIR", tmp_path)
    payload = {"model": "m", "messages": [{"role": "user", "content": "q"}], "max_tokens": 10, "temperature": 0.6,
               "seed": 1}
    import hashlib
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]
    (tmp_path / f"{digest}.json").write_text(json.dumps({"content": "Answer: (C)", "reasoning": "hmm", "finish": "stop",
                                                         "usage": {}, "error": None}))
    def no_net(*a, **k):
        raise AssertionError("no network for a cached reply")
    monkeypatch.setattr(client.urllib.request, "urlopen", no_net)
    events = list(client.chat_live("m", payload["messages"], max_tokens=10, temperature=0.6, seed=1))
    assert ("reasoning", "hmm") in events and ("content", "Answer: (C)") in events
    assert events[-1][0] == "done" and events[-1][1]["cached"] is True
