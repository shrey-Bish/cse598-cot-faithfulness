"""A vLLM server we run ourselves in a Sol GPU job (OpenAI-compatible /v1/chat/completions): Track B's
Qwen3-8B, in place of Ollama on the Mac (decided Oct 28; progress/sol_trackB.py starts the server).

Thinking on/off: the request's chat_template_kwargs {"enable_thinking": true/false} (Qwen3's template;
off renders an empty think block). The server splits the private reasoning out (--reasoning-parser
qwen3) into message.reasoning (vLLM 0.31.0; reasoning_content in older versions, read as a fallback)
and parses tool calls (--enable-auto-tool-choice --tool-call-parser hermes). Sampling beyond the
temperature comes from the model's generation_config.json (top_p 0.95, top_k 20, as in Ollama's
qwen3:8b). URL: $TRACKB_VLLM_URL (default http://localhost:8012/v1). No key.
"""
import os
import time

from .base import Reply, plain, post_json, tool_calls_from_openai

NAME = "sol_vllm"
TIMEOUT_S = 3600         # one long thinking reply at a busy server's per-sequence speed
PORT = 8012


def url():
    return os.environ.get("TRACKB_VLLM_URL", f"http://localhost:{PORT}/v1").rstrip("/") + "/chat/completions"


def build_request(model, messages, *, tools=None, thinking=None, max_tokens=16000, temperature=0.6, seed=None,
                  tool_choice=None):
    req = {"model": model, "messages": plain(messages), "max_tokens": max_tokens, "temperature": temperature}
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


def generate(model, messages, *, tools=None, thinking=None, max_tokens=16000, temperature=0.6, seed=None,
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
                      "served_model": body.get("model")})
