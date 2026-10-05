"""Shared builder and parser for the OpenAI-style Responses API (OpenAI and xAI).

Facts used (official docs, read 2026-10-04; see configs/models.yaml):
- POST {base}/responses with a bearer-token header.
- reasoning: {"effort": ..., "summary": "auto"}; effort "none" turns reasoning off on models
  that allow it; when reasoning is on, temperature/top_p must not be sent.
- The raw chain of thought is not exposed: only a summary (output item type "reasoning",
  summary[].text). Reasoning items returned with a tool call must be passed back.
- Function tools: {"type": "function", name, description, parameters}; calls come back as
  {"type": "function_call", call_id, name, arguments}; results go back as
  {"type": "function_call_output", call_id, output}.
- No `seed` on the Responses API.
"""
import json

from .base import native_items


def to_input(messages, provider):
    items = []
    for m in messages:
        role = m["role"]
        if role in ("system", "user"):
            items.append({"role": role, "content": m["content"]})
        elif role == "assistant":
            native = native_items(m, provider)
            if native:
                items.extend(native)
                continue
            if m.get("content"):
                items.append({"role": "assistant", "content": m["content"]})
            for c in m.get("tool_calls") or []:
                items.append({"type": "function_call", "call_id": c["id"], "name": c["function"]["name"],
                              "arguments": c["function"]["arguments"]})
        elif role == "tool":
            items.append({"type": "function_call_output", "call_id": m["tool_call_id"], "output": m["content"]})
    return items


def to_tools(tools):
    return [{"type": "function", "name": t["function"]["name"], "description": t["function"].get("description", ""),
             "parameters": t["function"]["parameters"]} for t in tools or []]


def build_request(model, messages, *, provider, tools=None, tool_choice=None, effort=None, summary=True,
                  max_tokens=4000, temperature=None):
    req = {"model": model, "input": to_input(messages, provider), "max_output_tokens": max_tokens}
    if tools:
        req["tools"] = to_tools(tools)
        if tool_choice:
            req["tool_choice"] = {"type": "function", "name": tool_choice["function"]["name"]}
    if effort is not None:
        req["reasoning"] = {"effort": effort, **({"summary": "auto"} if summary and effort != "none" else {})}
    if temperature is not None and (effort in (None, "none")):
        req["temperature"] = temperature   # not allowed while reasoning is on
    return req


def parse_response(body):
    """(final_text, reasoning_summary or None, tool_calls, usage, finish, native output items)."""
    texts, summaries, calls = [], [], []
    for item in body.get("output") or []:
        kind = item.get("type")
        if kind == "message":
            for part in item.get("content") or []:
                if part.get("type") in ("output_text", "text"):
                    texts.append(part.get("text", ""))
        elif kind == "reasoning":
            summaries += [s.get("text", "") for s in item.get("summary") or []]
        elif kind == "function_call":
            calls.append({"id": item.get("call_id"), "name": item.get("name"), "arguments": item.get("arguments", "")})
    u = body.get("usage") or {}
    usage = {"input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"),
             "reasoning_tokens": (u.get("output_tokens_details") or {}).get("reasoning_tokens"), "raw": u}
    status = body.get("status")
    incomplete = (body.get("incomplete_details") or {}).get("reason")
    finish = "length" if incomplete == "max_output_tokens" else ("tool_calls" if calls else status)
    reasoning = "\n\n".join(t for t in summaries if t) or None
    return "".join(texts), reasoning, calls, usage, finish, body.get("output") or []


def error_text(status, body):
    err = body.get("error") if isinstance(body, dict) else None
    msg = err.get("message") if isinstance(err, dict) else err
    return f"HTTP {status}: {str(msg)[:200]}" if msg else f"HTTP {status}"


def json_args(arguments):
    try:
        return json.loads(arguments or "{}")
    except json.JSONDecodeError:
        return {"_unparsed": arguments}
