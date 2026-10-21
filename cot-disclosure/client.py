"""Minimal client for ASU Research Computing's OpenAI-compatible LLM endpoint.

Every successful response is cached on disk, keyed by the full request, so
reruns and re-analysis cost nothing. Errors are never cached.
"""
import hashlib
import json
import os
import random
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent


def _load_env():
    env = HERE / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


_load_env()
BASE_URL = os.environ.get("RC_LLM_BASE_URL", "https://openai.rc.asu.edu/v1").rstrip("/")
API_KEY = os.environ.get("RC_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
CACHE_DIR = HERE / "cache"
CACHE_DIR.mkdir(exist_ok=True)


def chat(model, messages, max_tokens=8000, temperature=0.0, seed=None, retries=4,
         backoff=None, on_retry=None, stream=True, tools=None, tool_choice=None, extra=None):
    """Return {content, reasoning, finish, usage, error, retries, latency_s,
    reasoning_field, cached}. `reasoning` is the separate private trace thinking
    models emit in `reasoning_content`; `reasoning_field` names the field it came in.

    backoff: optional list of waits in seconds between tries (e.g. [2, 4, 8]);
    by default the original 1, 2, 4, 8 s schedule with jitter is kept.
    on_retry: optional callback(attempt, error, wait_s) so callers can log retries.
    stream=False sends one non-streamed request (only for short replies: the
    proxy cuts requests idle for ~100 s); it gets its own cache key.
    tools / tool_choice are passed through in the OpenAI chat format; the model's
    tool calls come back in `tool_calls`. Without tools the cache key is unchanged.
    extra: more request fields sent as-is (vLLM options such as continue_final_message,
    logprobs, top_logprobs, prompt_logprobs); they join the cache key only when given.
    Token log-probabilities, when requested, come back in `logprobs` / `prompt_logprobs`."""
    payload = {"model": model, "messages": messages,
               "max_tokens": max_tokens, "temperature": temperature}
    if seed is not None:
        payload["seed"] = seed
    if tools:
        payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
    if extra:
        payload.update(extra)
    key = payload if stream else {**payload, "stream": False}  # streamed keys unchanged
    return _request(payload, key, "/chat/completions", stream, retries, backoff, on_retry)


def complete(model, prompt, max_tokens=8000, temperature=0.0, seed=None, retries=4, backoff=None, on_retry=None,
             extra=None):
    """The raw text-completion endpoint (/v1/completions): `prompt` is sent as-is, so the
    caller renders the chat template itself (e.g. to continue a partial reasoning trace).
    Always streamed. Same result fields as chat(); `content` is the generated text and
    `reasoning` is empty (no reasoning parser runs on this endpoint)."""
    payload = {"model": model, "prompt": prompt, "max_tokens": max_tokens, "temperature": temperature}
    if seed is not None:
        payload["seed"] = seed
    if extra:
        payload.update(extra)
    return _request(payload, {**payload, "endpoint": "completions"}, "/completions", True, retries, backoff,
                    on_retry)


def _request(payload, key, path, stream, retries, backoff, on_retry):
    """Cache lookup, then the request with retries on transport errors (never cached)."""
    digest = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:24]
    cached = CACHE_DIR / f"{digest}.json"
    if cached.exists():
        return {"retries": 0, "latency_s": None, "reasoning_field": None, "tool_calls": [],
                **json.loads(cached.read_text()), "cached": True}

    last_error, waits = None, list(backoff) if backoff else None
    for attempt in range(retries):
        start = time.monotonic()
        try:
            out = _stream(payload, path) if stream else _post(payload)
            result = {"content": out["content"], "reasoning": out["reasoning"],
                      "finish": out["finish"], "usage": out["usage"], "error": None, "retries": attempt,
                      "latency_s": round(time.monotonic() - start, 2),
                      "reasoning_field": out["reasoning_field"], "tool_calls": out["tool_calls"]}
            for k in ("logprobs", "prompt_logprobs"):     # only when the request asked for them
                if out.get(k):
                    result[k] = out[k]
            cached.write_text(json.dumps(result))
            return {**result, "cached": False}
        except urllib.error.HTTPError as err:
            last_error = f"HTTP {err.code}"
            detail = _error_detail(err)
            if detail:
                last_error += f": {detail}"
            if err.code not in (408, 429, 500, 502, 503, 504, 524):
                break
        except Exception as err:  # timeouts, dropped connections
            last_error = type(err).__name__
        if attempt == retries - 1:
            break
        wait = waits[attempt] if waits else 2 ** attempt + random.random()
        if on_retry:
            on_retry(attempt + 1, last_error, wait)
        time.sleep(wait)
    return {"content": "", "reasoning": "", "finish": "error", "usage": {},
            "error": last_error, "retries": attempt, "latency_s": None,
            "reasoning_field": None, "tool_calls": [], "cached": False}


def _error_detail(err):
    """The server's error message (vLLM puts it in {"message": ...} or {"error": {"message": ...}}),
    trimmed. It never contains the request headers."""
    try:
        body = json.loads(err.read().decode("utf-8", "replace"))
    except Exception:
        return ""
    if not isinstance(body, dict):
        return ""
    inner = body.get("error")
    msg = body.get("message") or (inner.get("message") if isinstance(inner, dict) else inner)
    return str(msg or "")[:300]


def _stream(payload, path="/chat/completions"):
    """Stream the response. The endpoint sits behind Cloudflare, which returns
    HTTP 524 for any request idle for ~100s; long reasoning traces on large
    models exceeded that. Streaming keeps bytes flowing so the proxy never
    times out. The cache key is computed without `stream`, so it is unchanged."""
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps({**payload, "stream": True,
                         "stream_options": {"include_usage": True}}).encode(),  # usage arrives in the last chunk
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:  # per-read timeout
        return parse_stream_lines(response)


def iter_stream_lines(lines):
    """Yield ("reasoning" | "content", text piece) as server-sent-event lines arrive, then
    ("end", folded) where folded has content, reasoning (and the field it came in), finish
    reason, usage, tool calls (their fragments joined by index), and, when requested, token
    log-probabilities (`logprobs`: chat entries, or completion tokens/top_logprobs) and
    `prompt_logprobs`. Text-completion chunks (`choices[].text`) count as content."""
    content, reasoning, finish, usage, field, calls = [], [], None, {}, None, {}
    logprobs, prompt_logprobs = [], None
    for raw in lines:
        line = raw.decode("utf-8", "replace").strip()
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break
        chunk = json.loads(data)
        usage = chunk.get("usage") or usage
        prompt_logprobs = chunk.get("prompt_logprobs") or prompt_logprobs
        for choice in chunk.get("choices", []):
            prompt_logprobs = choice.get("prompt_logprobs") or prompt_logprobs
            lp = choice.get("logprobs")
            if isinstance(lp, dict) and lp.get("content"):          # chat format: one entry per token
                logprobs += lp["content"]
            elif isinstance(lp, dict) and lp.get("tokens"):         # completions format: parallel lists
                tops = lp.get("top_logprobs") or [None] * len(lp["tokens"])
                logprobs += [{"token": t, "logprob": l, "top_logprobs": top}
                             for t, l, top in zip(lp["tokens"], lp.get("token_logprobs") or [], tops)]
            if choice.get("text"):
                content.append(choice["text"])
                yield "content", choice["text"]
            delta = choice.get("delta") or {}
            name = "reasoning_content" if delta.get("reasoning_content") else "reasoning"
            piece = delta.get(name)
            if piece:
                reasoning.append(piece)
                field = field or name
                yield "reasoning", piece
            if delta.get("content"):
                content.append(delta["content"])
                yield "content", delta["content"]
            for tc in delta.get("tool_calls") or []:
                slot = calls.setdefault(tc.get("index", 0), {"id": None, "type": "function",
                                                             "function": {"name": "", "arguments": ""}})
                slot["id"] = tc.get("id") or slot["id"]
                fn = tc.get("function") or {}
                slot["function"]["name"] += fn.get("name") or ""
                slot["function"]["arguments"] += fn.get("arguments") or ""
            finish = choice.get("finish_reason") or finish
    yield "end", {"content": "".join(content), "reasoning": "".join(reasoning), "finish": finish, "usage": usage,
                  "reasoning_field": field, "tool_calls": [calls[i] for i in sorted(calls)],
                  "logprobs": logprobs, "prompt_logprobs": prompt_logprobs}


def parse_stream_lines(lines):
    """The folded result of a whole stream (see iter_stream_lines)."""
    for kind, value in iter_stream_lines(lines):
        if kind == "end":
            return value


def chat_live(model, messages, max_tokens=8000, temperature=0.0, seed=None):
    """Like chat(), but a generator for interactive use: yields ("reasoning" | "content",
    piece) as the reply streams in, then ("done", result) with the same fields as chat().
    Uses and fills the same cache (same key as chat()); no retries, so a failure shows at once."""
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
    if seed is not None:
        payload["seed"] = seed
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]
    cached = CACHE_DIR / f"{digest}.json"
    if cached.exists():
        result = {"retries": 0, "latency_s": None, "reasoning_field": None, "tool_calls": [],
                  **json.loads(cached.read_text()), "cached": True}
        if result["reasoning"]:
            yield "reasoning", result["reasoning"]
        if result["content"]:
            yield "content", result["content"]
        yield "done", result
        return
    start = time.monotonic()
    request = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps({**payload, "stream": True, "stream_options": {"include_usage": True}}).encode(),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            for kind, value in iter_stream_lines(response):
                if kind == "end":
                    out = value
                else:
                    yield kind, value
    except urllib.error.HTTPError as err:
        yield "done", {"content": "", "reasoning": "", "finish": "error", "usage": {}, "error": f"HTTP {err.code}",
                       "retries": 0, "latency_s": None, "reasoning_field": None, "tool_calls": [], "cached": False}
        return
    except Exception as err:
        yield "done", {"content": "", "reasoning": "", "finish": "error", "usage": {}, "error": type(err).__name__,
                       "retries": 0, "latency_s": None, "reasoning_field": None, "tool_calls": [], "cached": False}
        return
    result = {"content": out["content"], "reasoning": out["reasoning"], "finish": out["finish"], "usage": out["usage"],
              "error": None, "retries": 0, "latency_s": round(time.monotonic() - start, 2),
              "reasoning_field": out["reasoning_field"], "tool_calls": out["tool_calls"]}
    cached.write_text(json.dumps(result))
    yield "done", {**result, "cached": False}


def _post(payload):
    """One non-streamed request: the whole reply arrives at once."""
    request = urllib.request.Request(
        f"{BASE_URL}/chat/completions", data=json.dumps({**payload, "stream": False}).encode(),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        body = json.loads(response.read().decode("utf-8", "replace"))
    choice = (body.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    field = next((k for k in ("reasoning_content", "reasoning") if message.get(k)), None)
    return {"content": message.get("content") or "", "reasoning": message.get(field) or "" if field else "",
            "finish": choice.get("finish_reason"), "usage": body.get("usage") or {}, "reasoning_field": field,
            "tool_calls": message.get("tool_calls") or []}


def list_models():
    """The service's model catalog (the `data` list from GET /models)."""
    request = urllib.request.Request(f"{BASE_URL}/models",
                                     headers={"Authorization": f"Bearer {API_KEY}"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8", "replace")).get("data", [])
