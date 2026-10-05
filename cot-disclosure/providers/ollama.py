"""Ollama (local) adapter: POST /api/chat with stream false (docs.ollama.com, read 2026-10-04).

`think: true/false` switches thinking where the model permits it (qwen3:8b is the hybrid
model; qwen3:30b points to the thinking-only 2507 checkpoint). Reasoning comes back in full
in message.thinking. Tool calls have no ids and object arguments; results go back as
{"role": "tool", "tool_name", "content"}. tool_choice is not supported and is ignored.
"""
import json
import os
import time

from .base import Reply, post_json
from .responses_api import json_args

NAME = "ollama"


def url():
    return os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/") + "/api/chat"


def to_messages(messages):
    out = []
    for m in messages:
        if m["role"] == "assistant" and m.get("tool_calls"):
            out.append({"role": "assistant", "content": m.get("content") or "",
                        "tool_calls": [{"type": "function", "function": {"name": c["function"]["name"],
                                                                         "arguments": json_args(c["function"]["arguments"])}}
                                       for c in m["tool_calls"]]})
        elif m["role"] == "tool":
            out.append({"role": "tool", "tool_name": m.get("name", ""), "content": m["content"]})
        else:
            out.append({"role": m["role"], "content": m.get("content") or ""})
    return out


def build_request(model, messages, *, tools=None, thinking=None, max_tokens=16000, temperature=0.6, seed=None):
    req = {"model": model, "messages": to_messages(messages), "stream": False,
           "options": {"num_predict": max_tokens, "temperature": temperature}}
    if seed is not None:
        req["options"]["seed"] = seed
    if thinking is not None:
        req["think"] = bool(thinking)
    if tools:
        req["tools"] = tools
    return req


def parse_response(body):
    msg = body.get("message") or {}
    calls = [{"id": f"ollama-call-{i}", "name": (c.get("function") or {}).get("name"),
              "arguments": json.dumps((c.get("function") or {}).get("arguments") or {})}
             for i, c in enumerate(msg.get("tool_calls") or [])]
    usage = {"input_tokens": body.get("prompt_eval_count"), "output_tokens": body.get("eval_count"),
             "reasoning_tokens": None, "raw": {k: body.get(k) for k in ("prompt_eval_count", "eval_count")}}
    finish = "tool_calls" if calls else body.get("done_reason")
    return msg.get("content") or "", msg.get("thinking") or None, calls, usage, finish


def generate(model, messages, *, tools=None, thinking=None, max_tokens=16000, temperature=0.6, seed=None,
             tool_choice=None):
    temperature = 0.6 if temperature is None else temperature  # pilot setting
    req = build_request(model, messages, tools=tools, thinking=thinking, max_tokens=max_tokens,
                        temperature=temperature, seed=seed)
    start = time.monotonic()
    try:
        status, body = post_json(url(), {}, req)
    except Exception as err:
        return Reply(provider=NAME, model=model, error=f"{type(err).__name__} (is `ollama serve` running?)",
                     finish_reason="error")
    latency = round(time.monotonic() - start, 2)
    if status != 200:
        return Reply(provider=NAME, model=model, error=f"HTTP {status}: {str(body.get('error', ''))[:200]}",
                     finish_reason="error", latency_s=latency)
    text, thinking_text, calls, usage, finish = parse_response(body)
    return Reply(provider=NAME, model=model, final_text=text, reasoning_text=thinking_text,
                 reasoning_visibility="full" if thinking_text else "none", tool_calls=calls, finish_reason=finish,
                 usage=usage, latency_s=latency, cost_usd=0.0,
                 raw={"think": req.get("think"), "tool_choice_ignored": tool_choice is not None})
