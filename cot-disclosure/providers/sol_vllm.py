"""A vLLM server we run ourselves in a Sol GPU job (OpenAI-compatible /v1/chat/completions): Track B's
Qwen3-8B, in place of Ollama on the Mac (decided Oct 28; progress/sol_trackB.py starts the server).

Thinking on/off: the request's chat_template_kwargs {"enable_thinking": true/false} (Qwen3's template;
off renders an empty think block). The server splits the private reasoning out (--reasoning-parser
qwen3) into message.reasoning (vLLM 0.31.0; reasoning_content in older versions, read as a fallback)
and parses tool calls (--enable-auto-tool-choice --tool-call-parser hermes).
Every request carries its max_tokens: Track B's budget, 32,768 tokens minus the prompt and the replies
so far (progress/run_trackB.py; the 16,000 cut is computed afterwards), never a default here.
Sampling is the same with thinking on and off (decided Oct 28): temperature 0.6 (the caller's), top_p
0.95, top_k 20, sent in every request (Qwen recommends 0.7 / 0.8 for non-thinking mode: FINDINGS,
limitations). The server's chat template is the snapshot's, passed as a file (--chat-template); its
sha256 ($TRACKB_CHAT_TEMPLATE_SHA256, set by progress/sol_trackB.py) is saved with every reply.
URL: $TRACKB_VLLM_URL (default http://localhost:8012/v1). No key.
"""
import os
import time

from .base import Reply, plain, post_json, tool_calls_from_openai

NAME = "sol_vllm"
TIMEOUT_S = 3600         # one long thinking reply at a busy server's per-sequence speed
PORT = 8012
TOP_P, TOP_K = 0.95, 20  # with thinking on and off alike (Qwen's thinking-mode values)


def url():
    return os.environ.get("TRACKB_VLLM_URL", f"http://localhost:{PORT}/v1").rstrip("/") + "/chat/completions"


def build_request(model, messages, *, max_tokens, tools=None, thinking=None, temperature=0.6, seed=None,
                  tool_choice=None):
    if not max_tokens or max_tokens < 1:
        raise ValueError(f"max_tokens must be the budget left (32,768 minus the prompt and replies so far), not {max_tokens!r}")
    req = {"model": model, "messages": plain(messages), "max_tokens": max_tokens, "temperature": temperature,
           "top_p": TOP_P, "top_k": TOP_K}
    if seed is not None:
        req["seed"] = seed
    if thinking is not None:
        req["chat_template_kwargs"] = {"enable_thinking": bool(thinking)}
    if tools:
        req["tools"] = tools
        if tool_choice is not None:
            req["tool_choice"] = tool_choice
    return req


def parse_response(body):
    choice = (body.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    reasoning = msg.get("reasoning") or msg.get("reasoning_content") or None
    usage = body.get("usage") or {}
    return (msg.get("content") or "", reasoning, tool_calls_from_openai(msg.get("tool_calls")), choice.get("finish_reason"),
            {"input_tokens": usage.get("prompt_tokens"), "output_tokens": usage.get("completion_tokens"),
             "reasoning_tokens": None, "raw": usage})


def generate(model, messages, *, max_tokens, tools=None, thinking=None, temperature=0.6, seed=None,
             tool_choice=None):
    temperature = 0.6 if temperature is None else temperature  # pilot setting
    req = build_request(model, messages, tools=tools, thinking=thinking, max_tokens=max_tokens,
                        temperature=temperature, seed=seed, tool_choice=tool_choice)
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
    text, reasoning, calls, finish, usage = parse_response(body)
    return Reply(provider=NAME, model=model, final_text=text, reasoning_text=reasoning,
                 reasoning_visibility="full" if reasoning else "none", tool_calls=calls, finish_reason=finish,
                 usage=usage, latency_s=latency, cost_usd=0.0,
                 raw={"enable_thinking": req.get("chat_template_kwargs", {}).get("enable_thinking"),
                      "served_model": body.get("model"), "top_p": TOP_P, "top_k": TOP_K,
                      "chat_template_sha256": os.environ.get("TRACKB_CHAT_TEMPLATE_SHA256")})
