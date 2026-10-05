"""Anthropic Messages API adapter.

Facts used (platform.claude.com docs, read 2026-10-04; see configs/models.yaml):
- POST /v1/messages with x-api-key and anthropic-version: 2023-06-01; system is top level.
- Thinking modes: "budget" models (e.g. Haiku 4.5) take {"type": "enabled", "budget_tokens"}
  with budget >= 1024 and < max_tokens, and are off when the field is omitted; "adaptive"
  models (Opus 4.7 and later, e.g. Opus 5.5) take {"type": "adaptive", "display": "summarized"}
  plus output_config.effort, and cannot be turned off.
- Thinking text is always a summary. With thinking on, temperature must not be set and
  tool_choice may only be auto/none (forced choices are downgraded here and recorded).
- Tools: {name, description, input_schema}; calls are tool_use blocks; results go back in a
  user message as tool_result blocks; the assistant turn is echoed back unchanged.
- No seed.
"""
import json
import time

from .base import Reply, native_items, post_json, provider_key
from .config import model_info
from .responses_api import json_args

NAME = "anthropic"
URL = "https://api.anthropic.com/v1/messages"
VERSION = "2023-06-01"


def to_messages(messages):
    system, out = [], []
    for m in messages:
        role = m["role"]
        if role == "system":
            system.append(m["content"])
        elif role == "user":
            out.append({"role": "user", "content": m["content"]})
        elif role == "assistant":
            blocks = native_items(m, NAME)
            if blocks is None:
                blocks = ([{"type": "text", "text": m["content"]}] if m.get("content") else []) + [
                    {"type": "tool_use", "id": c["id"], "name": c["function"]["name"],
                     "input": json_args(c["function"]["arguments"])} for c in m.get("tool_calls") or []]
            out.append({"role": "assistant", "content": blocks})
        elif role == "tool":
            block = {"type": "tool_result", "tool_use_id": m["tool_call_id"], "content": m["content"]}
            if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list):
                out[-1]["content"].append(block)  # consecutive tool results share one user turn
            else:
                out.append({"role": "user", "content": [block]})
    return "\n\n".join(system) or None, out


def build_request(model, messages, *, tools=None, tool_choice=None, thinking=None, effort=None, max_tokens=4000,
                  temperature=None, budget_tokens=None):
    info = model_info(model)
    system, msgs = to_messages(messages)
    req, notes = {"model": model, "max_tokens": max_tokens, "messages": msgs}, {}
    if system:
        req["system"] = system
    mode, on = info.get("mode"), thinking is not False
    if info.get("thinking") == "always" and thinking is False:
        raise ValueError(f"{model}: thinking cannot be turned off")
    if on and mode == "budget":
        b = budget_tokens or max(1024, int(max_tokens * 0.75))
        if b >= max_tokens:
            raise ValueError("budget_tokens must be below max_tokens (min budget 1024)")
        req["thinking"] = {"type": "enabled", "budget_tokens": b}
    elif on and mode == "adaptive":
        req["thinking"] = {"type": "adaptive", "display": "summarized"}
        req["output_config"] = {"effort": effort or "medium"}
    if temperature is not None and not on and mode != "adaptive":
        req["temperature"] = temperature
    elif temperature is not None:
        notes["temperature_not_sent"] = True
    if tools:
        req["tools"] = [{"name": t["function"]["name"], "description": t["function"].get("description", ""),
                         "input_schema": t["function"]["parameters"]} for t in tools]
        if tool_choice:
            if on:
                req["tool_choice"] = {"type": "auto"}
                notes["tool_choice_downgraded"] = "forced tool_choice is not allowed with thinking; sent auto"
            else:
                req["tool_choice"] = {"type": "tool", "name": tool_choice["function"]["name"]}
    return req, notes


def parse_response(body):
    texts, thinking, calls, redacted = [], [], [], 0
    for b in body.get("content") or []:
        t = b.get("type")
        if t == "text":
            texts.append(b.get("text", ""))
        elif t == "thinking":
            thinking.append(b.get("thinking", ""))
        elif t == "redacted_thinking":
            redacted += 1
        elif t == "tool_use":
            calls.append({"id": b.get("id"), "name": b.get("name"), "arguments": json.dumps(b.get("input") or {})})
    u = body.get("usage") or {}
    usage = {"input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"),
             "reasoning_tokens": (u.get("output_tokens_details") or {}).get("thinking_tokens"), "raw": u}
    stop = body.get("stop_reason")
    finish = {"max_tokens": "length", "tool_use": "tool_calls", "end_turn": "stop"}.get(stop, stop)
    summary = "\n\n".join(x for x in thinking if x) or None
    return "".join(texts), summary, calls, usage, finish, redacted


def generate(model, messages, *, tools=None, thinking=None, max_tokens=4000, temperature=None, seed=None,
             tool_choice=None, effort=None, budget_tokens=None):
    req, notes = build_request(model, messages, tools=tools, tool_choice=tool_choice, thinking=thinking,
                               effort=effort, max_tokens=max_tokens, temperature=temperature,
                               budget_tokens=budget_tokens)
    key = provider_key("Anthropic", "ANTHROPIC_API_KEY")
    start = time.monotonic()
    try:
        status, body = post_json(URL, {"x-api-key": key, "anthropic-version": VERSION}, req)
    except Exception as err:
        return Reply(provider=NAME, model=model, error=type(err).__name__, finish_reason="error")
    latency = round(time.monotonic() - start, 2)
    if status != 200:
        msg = (body.get("error") or {}).get("message", "") if isinstance(body, dict) else ""
        return Reply(provider=NAME, model=model, error=f"HTTP {status}: {msg[:200]}", finish_reason="error",
                     latency_s=latency, raw=notes)
    text, summary, calls, usage, finish, redacted = parse_response(body)
    return Reply(provider=NAME, model=model, final_text=text, reasoning_text=summary,
                 reasoning_visibility="summary" if summary else "none", tool_calls=calls, finish_reason=finish,
                 usage=usage, latency_s=latency,
                 raw={**notes, "native_items": body.get("content"), "redacted_thinking_blocks": redacted,
                      "seed_ignored": seed is not None, "id": body.get("id")})
