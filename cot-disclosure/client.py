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
         backoff=None, on_retry=None, stream=True):
    """Return {content, reasoning, finish, usage, error, retries, latency_s,
    reasoning_field, cached}. `reasoning` is the separate private trace thinking
    models emit in `reasoning_content`; `reasoning_field` names the field it came in.

    backoff: optional list of waits in seconds between tries (e.g. [2, 4, 8]);
    by default the original 1, 2, 4, 8 s schedule with jitter is kept.
    on_retry: optional callback(attempt, error, wait_s) so callers can log retries.
    stream=False sends one non-streamed request (only for short replies: the
    proxy cuts requests idle for ~100 s); it gets its own cache key."""
    payload = {"model": model, "messages": messages,
               "max_tokens": max_tokens, "temperature": temperature}
    if seed is not None:
        payload["seed"] = seed
    key = payload if stream else {**payload, "stream": False}  # streamed keys unchanged
    digest = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:24]
    cached = CACHE_DIR / f"{digest}.json"
    if cached.exists():
        return {"retries": 0, "latency_s": None, "reasoning_field": None,
                **json.loads(cached.read_text()), "cached": True}

    last_error, waits = None, list(backoff) if backoff else None
    for attempt in range(retries):
        start = time.monotonic()
        try:
            content, reasoning, finish, usage, field = (_stream if stream else _post)(payload)
            result = {"content": content, "reasoning": reasoning,
                      "finish": finish, "usage": usage, "error": None, "retries": attempt,
                      "latency_s": round(time.monotonic() - start, 2), "reasoning_field": field}
            cached.write_text(json.dumps(result))
            return {**result, "cached": False}
        except urllib.error.HTTPError as err:
            last_error = f"HTTP {err.code}"
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
            "reasoning_field": None, "cached": False}


def _stream(payload):
    """Stream the response. The endpoint sits behind Cloudflare, which returns
    HTTP 524 for any request idle for ~100s; long reasoning traces on large
    models exceeded that. Streaming keeps bytes flowing so the proxy never
    times out. The cache key is computed without `stream`, so it is unchanged."""
    request = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps({**payload, "stream": True,
                         "stream_options": {"include_usage": True}}).encode(),  # usage arrives in the last chunk
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    content, reasoning, finish, usage, field = [], [], None, {}, None
    with urllib.request.urlopen(request, timeout=300) as response:  # per-read timeout
        for raw in response:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            usage = chunk.get("usage") or usage
            for choice in chunk.get("choices", []):
                delta = choice.get("delta") or {}
                if delta.get("content"):
                    content.append(delta["content"])
                name = "reasoning_content" if delta.get("reasoning_content") else "reasoning"
                piece = delta.get(name)
                if piece:
                    reasoning.append(piece)
                    field = field or name
                finish = choice.get("finish_reason") or finish
    return "".join(content), "".join(reasoning), finish, usage, field


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
    return (message.get("content") or "", message.get(field) or "" if field else "",
            choice.get("finish_reason"), body.get("usage") or {}, field)


def list_models():
    """The service's model catalog (the `data` list from GET /models)."""
    request = urllib.request.Request(f"{BASE_URL}/models",
                                     headers={"Authorization": f"Bearer {API_KEY}"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8", "replace")).get("data", [])
