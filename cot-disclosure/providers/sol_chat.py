"""A chat model on a vLLM server we run ourselves in a Sol GPU job (OpenAI-compatible /v1/chat/completions):
Track C's C13 reviewers (agents/sol_c13.py starts the server, one model at a time; decided Oct 29).

The request carries what C4's reviewer calls on Voyager carried, and nothing else: the messages, max_tokens
(the reviewer's cap), temperature and seed. Every other sampling setting is the server's default, which vLLM
takes from the model's own generation_config.json (`--generation-config auto`, its default), as a served
model on Voyager does; agents/sol_c13.py saves that file's sampling values with the job.
No reasoning parser: both C13 reviewers are non-thinking instruct models.
URL: $SOL_CHAT_URL (default http://localhost:8013/v1). No key.
"""
import os
import time

from .base import Reply, plain, post_json, tool_calls_from_openai

NAME = "sol_chat"
TIMEOUT_S = 3600         # one long review at a busy server's per-sequence speed
PORT = 8013


def url():
    return os.environ.get("SOL_CHAT_URL", f"http://localhost:{PORT}/v1").rstrip("/") + "/chat/completions"


def build_request(model, messages, *, max_tokens, temperature=0.6, seed=None, tools=None, tool_choice=None):
    if not max_tokens or max_tokens < 1:
        raise ValueError(f"max_tokens must be the caller's cap, not {max_tokens!r}")
    req = {"model": model, "messages": plain(messages), "max_tokens": max_tokens, "temperature": temperature}
    if seed is not None:
        req["seed"] = seed
    if tools:
        req["tools"] = tools
        if tool_choice is not None:
            req["tool_choice"] = tool_choice
    return req


def generate(model, messages, *, max_tokens, tools=None, thinking=None, temperature=0.6, seed=None,
             tool_choice=None):
    if thinking:
        raise ValueError("sol_chat serves non-thinking models only (C13); thinking must be None or False")
    temperature = 0.6 if temperature is None else temperature
    req = build_request(model, messages, max_tokens=max_tokens, temperature=temperature, seed=seed, tools=tools,
                        tool_choice=tool_choice)
    start = time.monotonic()
    try:
        status, body = post_json(url(), {}, req, timeout=TIMEOUT_S)
    except Exception as err:
        return Reply(provider=NAME, model=model, error=f"{type(err).__name__}: {err} (is the job's vLLM server up?)",
                     finish_reason="error")
    latency = round(time.monotonic() - start, 2)
    if status != 200:
        return Reply(provider=NAME, model=model, error=f"HTTP {status}: {str(body.get('message') or body)[:200]}",
                     finish_reason="error", latency_s=latency)
    choice = (body.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    usage = body.get("usage") or {}
    return Reply(provider=NAME, model=model, final_text=msg.get("content") or "",
                 tool_calls=tool_calls_from_openai(msg.get("tool_calls")), finish_reason=choice.get("finish_reason"),
                 usage={"input_tokens": usage.get("prompt_tokens"), "output_tokens": usage.get("completion_tokens"),
                        "reasoning_tokens": None, "raw": usage},
                 latency_s=latency, cost_usd=0.0, raw={"served_model": body.get("model"), "engine": "vllm"})
