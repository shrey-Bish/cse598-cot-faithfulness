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
