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


def chat(model, messages, max_tokens=8000, temperature=0.0, seed=None, retries=4):
    """Return {content, reasoning, finish, usage, error}. `reasoning` is the
    separate private trace thinking models emit in `reasoning_content`."""
    payload = {"model": model, "messages": messages,
               "max_tokens": max_tokens, "temperature": temperature}
    if seed is not None:
        payload["seed"] = seed
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]
    cached = CACHE_DIR / f"{digest}.json"
    if cached.exists():
        return json.loads(cached.read_text())

    last_error = None
    for attempt in range(retries):
        try:
            content, reasoning, finish, usage = _stream(payload)
            result = {"content": content, "reasoning": reasoning,
                      "finish": finish, "usage": usage, "error": None}
            cached.write_text(json.dumps(result))
            return result
        except urllib.error.HTTPError as err:
            last_error = f"HTTP {err.code}"
            if err.code not in (408, 429, 500, 502, 503, 504, 524):
                break
        except Exception as err:  # timeouts, dropped connections
            last_error = type(err).__name__
        time.sleep(2 ** attempt + random.random())
    return {"content": "", "reasoning": "", "finish": "error",
            "usage": {}, "error": last_error}


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
    content, reasoning, finish, usage = [], [], None, {}
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
                piece = delta.get("reasoning_content") or delta.get("reasoning")
                if piece:
                    reasoning.append(piece)
                finish = choice.get("finish_reason") or finish
    return "".join(content), "".join(reasoning), finish, usage
