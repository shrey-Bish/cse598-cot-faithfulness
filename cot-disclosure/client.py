"""Minimal client for ASU Research Computing's OpenAI-compatible LLM endpoint (Voyager).

Every successful response is cached on disk, keyed by the full request, so
reruns and re-analysis cost nothing. Errors are never cached.

Voyager model IDs changed on 2026-10-21: each instruct/thinking pair is now one family ID,
and reasoning_effort picks the member (none = instruct, the default; low/medium/high =
thinking). Our six model names stay everywhere in the code and the saved runs; route()
maps them to (Voyager ID, effort) on every request (configs/models.yaml: voyager_ids), and
no request leaves with an old ID. Guards on every network request for those names:
  a. a thinking model is always sent with a non-none effort (route() refuses otherwise);
     a bare family ID needs an explicit effort, since its default is the instruct model
  b. the first request for a model in a process checks /v1/models: the family ID must be
     listed and must still serve our model at that effort (ModelUnavailable otherwise)
  c. identity canary, at the first request and then hourly: an echo call on a fixed short
     reference text (configs/canary/<name>.json, under 2,048 tokens) must give the same top
     token at every position as the stored log-probs, with max |difference| < 0.01, and the
     server must report our model name (CanaryFailed otherwise). After b or c fails, every
     later request in the process refuses: the run stops.
  d. idle timeout: no token for 10 minutes aborts the request; it returns with error
     "IdleTimeout: ..." and progress/common.make_record marks it "not_run" (retry it later)
  e. every result carries requested_model_id, reasoning_effort and served_model
"""
import hashlib
import json
import os
import random
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
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

MODELS_YAML = HERE / "configs" / "models.yaml"
CANARY_DIR = HERE / "configs" / "canary"
CANARY_LOG = HERE / "results" / "voyager_canary.jsonl"
IDLE_S = 600                  # guard d: no token for 10 minutes -> abort, "not run"
CANARY_EVERY_S = 3600         # guard c: hourly during long runs
CANARY_TOL = 0.01
GUARDS = True                 # guards b and c; tests switch them off


class ModelUnavailable(RuntimeError):
    """Guard b: the Voyager ID is gone, or no longer serves our model at that effort."""


class CanaryFailed(RuntimeError):
    """Guard c: the identity canary does not match the stored reference."""


class IdleTimeout(RuntimeError):
    """Guard d: no token arrived for IDLE_S seconds."""


# ---------------------------------------------------------------- model IDs
def load_voyager_ids(path=MODELS_YAML):
    """{our model name: (Voyager ID, reasoning_effort)} from configs/models.yaml. Uses PyYAML when
    installed, else reads the flat `voyager_ids:` block directly (the client needs no packages)."""
    text = Path(path).read_text()
    try:
        import yaml
        ids = {k: (str(v[0]), str(v[1])) for k, v in ((yaml.safe_load(text) or {}).get("voyager_ids") or {}).items()}
    except ImportError:
        ids, inside = {}, False
        for line in text.splitlines():
            if line.startswith("voyager_ids:"):
                inside = True
            elif inside and line and not line.startswith((" ", "#")):
                break
            elif inside:
                m = re.match(r"\s+([\w.-]+):\s*\[\s*([\w.-]+)\s*,\s*([\w-]+)\s*\]", line)
                if m:
                    ids[m.group(1)] = (m.group(2), m.group(3))
    for name, (_, effort) in ids.items():
        if "think" in name and effort == "none":
            raise ValueError(f"{path}: {name} must map to a non-none reasoning_effort (guard a)")
    return ids


VOYAGER_IDS = load_voyager_ids()
FAMILY_IDS = {vid for vid, _ in VOYAGER_IDS.values()}


def route(model, effort=None):
    """(Voyager ID, reasoning_effort to send) for a request naming `model`.
    Our names map through VOYAGER_IDS; asking one of them for another effort refuses (guard a).
    A bare family ID needs an explicit effort. Any other model name passes through unchanged."""
    if model in VOYAGER_IDS:
        vid, mapped = VOYAGER_IDS[model]
        if effort is not None and effort != mapped:
            raise ValueError(f"{model} is served as {vid} at reasoning_effort={mapped!r}; refusing {effort!r}")
        return vid, mapped
    if model in FAMILY_IDS and effort is None:
        raise ValueError(f"{model} is a Voyager family ID whose default is the instruct model: name the model "
                         f"(one of {sorted(VOYAGER_IDS)}) or pass reasoning_effort")
    return model, effort


def _prepare(payload):
    """Apply route() to a request payload in place. Returns our model name."""
    name = payload["model"]
    vid, effort = route(name, payload.get("reasoning_effort"))
    payload["model"] = vid
    if effort is not None:
        payload["reasoning_effort"] = effort
    if payload["model"] in VOYAGER_IDS:                       # never send a retired ID
        raise RuntimeError(f"refusing to send the retired Voyager ID {payload['model']!r}")
    return name


def _meta(payload):
    return {"requested_model_id": payload["model"], "reasoning_effort": payload.get("reasoning_effort")}


# ---------------------------------------------------------------- guards b and c
_lock = threading.RLock()
_catalog_ok, _canary_at, _halted, _warned = set(), {}, None, set()


def preflight(name):
    """Guards b and c for one of our model names (no-op for other names or with GUARDS off).
    Runs before a network request; raises ModelUnavailable or CanaryFailed, and once either has
    failed, every later call in this process raises the same error."""
    global _halted
    if not GUARDS or name not in VOYAGER_IDS:
        return
    with _lock:
        if _halted:
            raise _halted[0](_halted[1])
        try:
            if name not in _catalog_ok:
                check_catalog(name)
                _catalog_ok.add(name)
            if time.time() - _canary_at.get(name, 0) > CANARY_EVERY_S:
                run_canary(name)
                _canary_at[name] = time.time()
        except (ModelUnavailable, CanaryFailed) as err:
            _halted = (type(err), str(err))
            raise


def check_catalog(name, models=None):
    """Guard b: the family ID is listed, and its member at our effort is our model."""
    vid, effort = VOYAGER_IDS[name]
    models = list_models() if models is None else models
    entry = next((m for m in models if m.get("id") == vid), None)
    if entry is None:
        raise ModelUnavailable(f"/v1/models no longer lists {vid} (for {name})")
    members = (entry.get("family") or {}).get("members") or {}
    if members and members.get(effort) != name:
        raise ModelUnavailable(f"{vid} at reasoning_effort={effort} now serves {members.get(effort)!r}, not {name}")


def compare_logprobs(ref, new, tol=CANARY_TOL):
    """Prompt-token log-probabilities, position by position: pass = the same tokens, the same top
    token at every position, and max |difference| < tol."""
    b = new[: len(ref)]
    if len(b) != len(ref) or [x["token"] for x in ref] != [x["token"] for x in b]:
        return {"pass": False, "reason": "the prompt tokenized differently"}

    def top(e):
        tops = e.get("top_logprobs") or {}
        return max(tops.items(), key=lambda kv: kv[1])[0] if tops else None
    pos = [i for i in range(len(ref)) if ref[i]["logprob"] is not None and b[i]["logprob"] is not None]
    diffs = [abs(ref[i]["logprob"] - b[i]["logprob"]) for i in pos] or [0.0]
    mismatches = [i for i in pos if top(ref[i]) != top(b[i])]
    return {"pass": not mismatches and max(diffs) < tol, "positions": len(pos),
            "mean_abs_diff": sum(diffs) / len(diffs), "max_abs_diff": max(diffs),
            "top_token_mismatches": len(mismatches)}


def canary_request(name, ref):
    """The canary's echo request on the reference text (never served from the cache)."""
    payload = {"model": name, "prompt": ref["text"], "max_tokens": 1, "temperature": ref["params"]["temperature"],
               "seed": ref["params"]["seed"], "echo": True, "logprobs": 1}
    _prepare(payload)
    return _request(payload, None, "/completions", True, 3, [2, 4], None, name=name, use_cache=False, guard=False)


def run_canary(name):
    """Guard c. Without a stored reference for this model, warn once and skip."""
    path = CANARY_DIR / f"{name}.json"
    if not path.exists():
        if name not in _warned:
            _warned.add(name)
            print(f"[client] no canary reference for {name} ({path.name}); identity not checked", file=sys.stderr)
        return None
    ref = json.loads(path.read_text())
    out = canary_request(name, ref)
    res = {"pass": False, "reason": out["error"]} if out["error"] else compare_logprobs(ref["logprobs"], out["logprobs"])
    served_ok = out.get("served_model") == ref["served_model"]
    ok = res["pass"] and served_ok
    try:
        CANARY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(CANARY_LOG, "a") as f:
            f.write(json.dumps({"timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                "model": name, "requested_model_id": out["requested_model_id"],
                                "reasoning_effort": out["reasoning_effort"], "served_model": out.get("served_model"),
                                "pass": ok, **res}) + "\n")
    except OSError:
        pass
    if not ok:
        raise CanaryFailed(f"identity canary failed for {name}: served {out.get('served_model')!r} "
                           f"(want {ref['served_model']!r}), {res}")
    return res


# ---------------------------------------------------------------- requests
def chat(model, messages, max_tokens=8000, temperature=0.0, seed=None, retries=4,
         backoff=None, on_retry=None, stream=True, tools=None, tool_choice=None, extra=None):
    """Return {content, reasoning, finish, usage, error, retries, latency_s, reasoning_field,
    cached, requested_model_id, reasoning_effort, served_model}. `reasoning` is the separate
    private trace thinking models emit; `reasoning_field` names the field it came in.

    backoff: optional list of waits in seconds between tries (e.g. [2, 4, 8]);
    by default the original 1, 2, 4, 8 s schedule with jitter is kept.
    on_retry: optional callback(attempt, error, wait_s) so callers can log retries.
    stream=False sends one non-streamed request (only for short replies: the
    proxy cuts requests idle for ~100 s); it gets its own cache key.
    tools / tool_choice are passed through in the OpenAI chat format; the model's
    tool calls come back in `tool_calls`. Without tools the cache key is unchanged.
    extra: more request fields sent as-is (vLLM options such as continue_final_message,
    logprobs, top_logprobs, prompt_logprobs); they join the cache key only when given.
    Token log-probabilities, when requested, come back in `logprobs` / `prompt_logprobs`.
    `model` is one of our names (mapped by route()) or any other model ID."""
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
    name = _prepare(payload)
    key = payload if stream else {**payload, "stream": False}  # streamed keys unchanged
    return _request(payload, key, "/chat/completions", stream, retries, backoff, on_retry, name=name)


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
    name = _prepare(payload)
    return _request(payload, {**payload, "endpoint": "completions"}, "/completions", True, retries, backoff,
                    on_retry, name=name)


def _request(payload, key, path, stream, retries, backoff, on_retry, name=None, use_cache=True, guard=True):
    """Cache lookup, the guards, then the request with retries on transport errors (never cached).
    An idle timeout is not retried here: it comes back as error "IdleTimeout: ..." (not run)."""
    meta = _meta(payload)
    cached = None
    if use_cache:
        digest = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:24]
        cached = CACHE_DIR / f"{digest}.json"
        if cached.exists():
            return {"retries": 0, "latency_s": None, "reasoning_field": None, "tool_calls": [], "served_model": None,
                    **json.loads(cached.read_text()), **meta, "cached": True}
    if guard:
        preflight(name)

    last_error, waits = None, list(backoff) if backoff else None
    for attempt in range(retries):
        start = time.monotonic()
        try:
            out = _stream(payload, path) if stream else _post(payload)
            result = {"content": out["content"], "reasoning": out["reasoning"],
                      "finish": out["finish"], "usage": out["usage"], "error": None, "retries": attempt,
                      "latency_s": round(time.monotonic() - start, 2),
                      "reasoning_field": out["reasoning_field"], "tool_calls": out["tool_calls"],
                      "served_model": out.get("served_model"), **meta}
            for k in ("logprobs", "prompt_logprobs"):     # only when the request asked for them
                if out.get(k):
                    result[k] = out[k]
            if len(out.get("choices") or []) > 1:          # a list of prompts: each one's own result
                result["choices"] = out["choices"]
            if cached is not None:
                cached.write_text(json.dumps(result))
            return {**result, "cached": False}
        except IdleTimeout as err:                        # guard d: abort; the caller retries it later
            last_error = f"IdleTimeout: {err}"
            break
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
            "reasoning_field": None, "tool_calls": [], "served_model": None, **meta, "cached": False}


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
        return parse_stream_lines(response, idle_s=IDLE_S)


def iter_stream_lines(lines, idle_s=None, clock=time.monotonic):
    """Yield ("reasoning" | "content", text piece) as server-sent-event lines arrive, then
    ("end", folded) where folded has content, reasoning (and the field it came in), finish
    reason, usage, tool calls (their fragments joined by index), the model name the server
    reports, and, when requested, token log-probabilities (`logprobs`: chat entries, or
    completion tokens/top_logprobs) and `prompt_logprobs`. Text-completion chunks
    (`choices[].text`) count as content. With idle_s, raise IdleTimeout when no token has
    arrived for that long, even if the server keeps the connection busy with other lines."""
    content, reasoning, finish, usage, field, calls = [], [], None, {}, None, {}
    logprobs, prompt_logprobs, served = [], None, None
    by_choice = {}          # a list of prompts in one completions request: each prompt's own text and log-probs
    last = clock()
    for raw in lines:
        if idle_s is not None and clock() - last > idle_s:
            raise IdleTimeout(f"no token for {idle_s} s")
        line = raw.decode("utf-8", "replace").strip()
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break
        chunk = json.loads(data)
        usage = chunk.get("usage") or usage
        served = chunk.get("model") or served
        prompt_logprobs = chunk.get("prompt_logprobs") or prompt_logprobs
        for choice in chunk.get("choices", []):
            prompt_logprobs = choice.get("prompt_logprobs") or prompt_logprobs
            own = by_choice.setdefault(choice.get("index", 0), {"text": "", "logprobs": [], "finish": None})
            lp = choice.get("logprobs")
            if isinstance(lp, dict) and lp.get("content"):          # chat format: one entry per token
                logprobs += lp["content"]
                last = clock()
            elif isinstance(lp, dict) and lp.get("tokens"):         # completions format: parallel lists
                tops = lp.get("top_logprobs") or [None] * len(lp["tokens"])
                entries = [{"token": t, "logprob": l, "top_logprobs": top}
                           for t, l, top in zip(lp["tokens"], lp.get("token_logprobs") or [], tops)]
                logprobs += entries
                own["logprobs"] += entries
                last = clock()
            if choice.get("text"):
                content.append(choice["text"])
                own["text"] += choice["text"]
                last = clock()
                yield "content", choice["text"]
            own["finish"] = choice.get("finish_reason") or own["finish"]
            delta = choice.get("delta") or {}
            name = "reasoning_content" if delta.get("reasoning_content") else "reasoning"
            piece = delta.get(name)
            if piece:
                reasoning.append(piece)
                field = field or name
                last = clock()
                yield "reasoning", piece
            if delta.get("content"):
                content.append(delta["content"])
                last = clock()
                yield "content", delta["content"]
            for tc in delta.get("tool_calls") or []:
                last = clock()
                slot = calls.setdefault(tc.get("index", 0), {"id": None, "type": "function",
                                                             "function": {"name": "", "arguments": ""}})
                slot["id"] = tc.get("id") or slot["id"]
                fn = tc.get("function") or {}
                slot["function"]["name"] += fn.get("name") or ""
                slot["function"]["arguments"] += fn.get("arguments") or ""
            finish = choice.get("finish_reason") or finish
    yield "end", {"content": "".join(content), "reasoning": "".join(reasoning), "finish": finish, "usage": usage,
                  "reasoning_field": field, "tool_calls": [calls[i] for i in sorted(calls)],
                  "logprobs": logprobs, "prompt_logprobs": prompt_logprobs, "served_model": served,
                  "choices": [by_choice[i] for i in sorted(by_choice)]}


def parse_stream_lines(lines, idle_s=None):
    """The folded result of a whole stream (see iter_stream_lines)."""
    for kind, value in iter_stream_lines(lines, idle_s=idle_s):
        if kind == "end":
            return value


def chat_live(model, messages, max_tokens=8000, temperature=0.0, seed=None):
    """Like chat(), but a generator for interactive use: yields ("reasoning" | "content",
    piece) as the reply streams in, then ("done", result) with the same fields as chat().
    Uses and fills the same cache (same key as chat()); no retries, so a failure shows at once."""
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
    if seed is not None:
        payload["seed"] = seed
    name = _prepare(payload)
    meta = _meta(payload)
    fail = {"content": "", "reasoning": "", "finish": "error", "usage": {}, "retries": 0, "latency_s": None,
            "reasoning_field": None, "tool_calls": [], "served_model": None, **meta, "cached": False}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]
    cached = CACHE_DIR / f"{digest}.json"
    if cached.exists():
        result = {"retries": 0, "latency_s": None, "reasoning_field": None, "tool_calls": [], "served_model": None,
                  **json.loads(cached.read_text()), **meta, "cached": True}
        if result["reasoning"]:
            yield "reasoning", result["reasoning"]
        if result["content"]:
            yield "content", result["content"]
        yield "done", result
        return
    try:
        preflight(name)
    except (ModelUnavailable, CanaryFailed) as err:
        yield "done", {**fail, "error": f"{type(err).__name__}: {err}"}
        return
    start = time.monotonic()
    request = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps({**payload, "stream": True, "stream_options": {"include_usage": True}}).encode(),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            for kind, value in iter_stream_lines(response, idle_s=IDLE_S):
                if kind == "end":
                    out = value
                else:
                    yield kind, value
    except urllib.error.HTTPError as err:
        yield "done", {**fail, "error": f"HTTP {err.code}"}
        return
    except IdleTimeout as err:
        yield "done", {**fail, "error": f"IdleTimeout: {err}"}
        return
    except Exception as err:
        yield "done", {**fail, "error": type(err).__name__}
        return
    result = {"content": out["content"], "reasoning": out["reasoning"], "finish": out["finish"], "usage": out["usage"],
              "error": None, "retries": 0, "latency_s": round(time.monotonic() - start, 2),
              "reasoning_field": out["reasoning_field"], "tool_calls": out["tool_calls"],
              "served_model": out.get("served_model"), **meta}
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
            "tool_calls": message.get("tool_calls") or [], "served_model": body.get("model")}


def list_models():
    """The service's model catalog (the `data` list from GET /models)."""
    request = urllib.request.Request(f"{BASE_URL}/models",
                                     headers={"Authorization": f"Bearer {API_KEY}"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8", "replace")).get("data", [])
