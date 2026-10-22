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


def test_completion_chunks_and_their_logprobs():
    lines = [sse({"choices": [{"text": " B", "logprobs": {"tokens": [" B"], "token_logprobs": [-0.1],
                                                          "top_logprobs": [{" B": -0.1, " C": -2.5}]}}]}),
             sse({"choices": [{"text": ")", "finish_reason": "length",
                               "logprobs": {"tokens": [")"], "token_logprobs": [-0.01], "top_logprobs": [{")": -0.01}]}}]}),
             sse({"choices": [], "usage": {"prompt_tokens": 40, "completion_tokens": 2}}), b"data: [DONE]"]
    out = parse_stream_lines(lines)
    assert out["content"] == " B)" and out["reasoning"] == "" and out["finish"] == "length"
    assert [e["token"] for e in out["logprobs"]] == [" B", ")"]
    assert out["logprobs"][0]["top_logprobs"] == {" B": -0.1, " C": -2.5}


def test_chat_logprobs_and_prompt_logprobs_are_collected():
    lines = [sse({"prompt_logprobs": [None, {"12": {"logprob": -1.0}}],
                  "choices": [{"delta": {"content": "A"},
                               "logprobs": {"content": [{"token": "A", "logprob": -0.2,
                                                         "top_logprobs": [{"token": "A", "logprob": -0.2}]}]}}]}),
             sse({"choices": [{"delta": {}, "finish_reason": "length"}]}), b"data: [DONE]"]
    out = parse_stream_lines(lines)
    assert out["content"] == "A" and out["logprobs"][0]["token"] == "A"
    assert out["prompt_logprobs"] == [None, {"12": {"logprob": -1.0}}]
    plain = parse_stream_lines([sse({"choices": [{"delta": {"content": "x"}, "finish_reason": "stop"}]}),
                                b"data: [DONE]"])
    assert plain["logprobs"] == [] and plain["prompt_logprobs"] is None


def _cached(tmp_path, key, result):
    import hashlib
    digest = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:24]
    (tmp_path / f"{digest}.json").write_text(json.dumps(result))


def test_chat_cache_key_unchanged_without_extra_and_separate_with_it(tmp_path, monkeypatch):
    import client
    monkeypatch.setattr(client, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(client.urllib.request, "urlopen", lambda *a, **k: (_ for _ in ()).throw(AssertionError("net")))
    msgs = [{"role": "user", "content": "q"}]
    base = {"model": "m", "messages": msgs, "max_tokens": 5, "temperature": 0.6, "seed": 1}
    _cached(tmp_path, base, {"content": "plain", "reasoning": "", "finish": "stop", "usage": {}, "error": None})
    _cached(tmp_path, {**base, "logprobs": True}, {"content": "with lp", "reasoning": "", "finish": "stop",
                                                  "usage": {}, "error": None})
    assert client.chat("m", msgs, max_tokens=5, temperature=0.6, seed=1)["content"] == "plain"
    assert client.chat("m", msgs, max_tokens=5, temperature=0.6, seed=1, extra={"logprobs": True})["content"] == "with lp"


def test_complete_uses_its_own_cache_key(tmp_path, monkeypatch):
    import client
    monkeypatch.setattr(client, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(client.urllib.request, "urlopen", lambda *a, **k: (_ for _ in ()).throw(AssertionError("net")))
    payload = {"model": "m", "prompt": "<|im_start|>user\nq", "max_tokens": 1, "temperature": 0.6, "seed": 1}
    _cached(tmp_path, {**payload, "endpoint": "completions"},
            {"content": " C", "reasoning": "", "finish": "length", "usage": {}, "error": None})
    out = client.complete("m", payload["prompt"], max_tokens=1, temperature=0.6, seed=1)
    assert out["content"] == " C" and out["cached"] is True


def test_http_error_detail_is_read_safely():
    import io
    import urllib.error
    from client import _error_detail
    def err(body):
        return urllib.error.HTTPError("u", 400, "bad", {}, io.BytesIO(body))
    assert _error_detail(err(b'{"error": {"message": "role tool not supported"}}')) == "role tool not supported"
    assert _error_detail(err(b'{"message": "bad role"}')) == "bad role"
    assert _error_detail(err(b'{"error": "plain string"}')) == "plain string"
    assert _error_detail(err(b"not json")) == ""


def test_a_list_of_prompts_keeps_each_choice_separate():
    lines = [sse({"choices": [{"index": 1, "text": "C", "logprobs": {"tokens": ["C"], "token_logprobs": [-0.2],
                                                                      "top_logprobs": [{"C": -0.2, "B": -1.9}]}}]}),
             sse({"choices": [{"index": 0, "text": "B", "finish_reason": "length",
                               "logprobs": {"tokens": ["B"], "token_logprobs": [-0.1], "top_logprobs": [{"B": -0.1}]}}]}),
             sse({"choices": [{"index": 1, "text": "", "finish_reason": "length"}]}), b"data: [DONE]"]
    out = parse_stream_lines(lines)
    assert [c["text"] for c in out["choices"]] == ["B", "C"]                     # ordered by prompt index
    assert out["choices"][1]["logprobs"][0]["top_logprobs"] == {"C": -0.2, "B": -1.9}
    assert [c["finish"] for c in out["choices"]] == ["length", "length"]


def test_a_stream_that_closes_without_a_finish_reason_is_retried_and_never_cached(tmp_path, monkeypatch):
    import pytest
    import client
    cut = [sse({"choices": [{"text": "Let me think"}]})]                       # closed mid-reply
    with pytest.raises(client.IncompleteStream):
        parse_stream_lines(cut)
    with pytest.raises(client.IncompleteStream):                               # a list: every prompt needs one
        parse_stream_lines([sse({"choices": [{"index": 0, "text": "A", "finish_reason": "length"}]}),
                            sse({"choices": [{"index": 1, "text": "B"}]}), b"data: [DONE]"])
    monkeypatch.setattr(client, "CACHE_DIR", tmp_path)
    streams = iter([cut, [sse({"choices": [{"text": "A", "finish_reason": "stop"}]}), b"data: [DONE]"]])
    monkeypatch.setattr(client, "_stream", lambda payload, path: parse_stream_lines(next(streams)))
    key = {"model": "m", "prompt": "p", "max_tokens": 5, "temperature": 0.0, "endpoint": "completions"}
    _cached(tmp_path, key, {"content": "Let me", "reasoning": "", "finish": None, "usage": {}, "error": None})
    out = client.complete("m", "p", max_tokens=5, backoff=[0, 0, 0])            # old cut-short entry: not reused
    assert out["content"] == "A" and out["finish"] == "stop" and out["retries"] == 1 and not out["cached"]
    assert client.complete("m", "p", max_tokens=5)["cached"]                  # the complete reply is cached
