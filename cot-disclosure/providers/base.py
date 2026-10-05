"""What every provider adapter returns, and the message format they all accept.

Messages use the OpenAI chat format, which `client.py` already speaks:
  {"role": "system" | "user", "content": str}
  {"role": "assistant", "content": str | None, "tool_calls": [{"id", "type": "function",
                                                               "function": {"name", "arguments"}}]}
  {"role": "tool", "tool_call_id": str, "content": str}
Tools use the OpenAI chat function format: {"type": "function", "function": {name,
description, parameters}}. Each adapter converts both into its provider's own format.
"""
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]          # cot-disclosure/
VISIBILITY = ("full", "summary", "none")             # how much private reasoning the provider returns
AUTH_HEADER = "Authorization"                        # bearer-token header used by OpenAI-style APIs


@dataclass
class Reply:
    provider: str
    model: str
    final_text: str = ""
    reasoning_text: str | None = None
    reasoning_visibility: str = "none"              # full / summary / none
    tool_calls: list = field(default_factory=list)  # [{"id", "name", "arguments": str}]
    finish_reason: str | None = None
    usage: dict = field(default_factory=dict)       # {"input_tokens", "output_tokens", "reasoning_tokens", "raw"}
    latency_s: float | None = None
    cost_usd: float | None = None
    error: str | None = None
    raw: dict | None = None                         # provider response minus anything secret

    def to_dict(self):
        return asdict(self)


def load_env():
    """Read cot-disclosure/.env into os.environ (values are never printed)."""
    env = CODE / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def provider_key(name, env_var):
    """The API key for an outside provider. Refuses a value equal to the Voyager key:
    this repo's .env historically set OPENAI_API_KEY to the ASU key, and that key must
    never leave ASU's service."""
    load_env()
    key = os.environ.get(env_var, "").strip()
    if not key:
        raise MissingKey(f"{env_var} is not set; {name} calls are disabled")
    if key == os.environ.get("RC_LLM_API_KEY", "").strip():
        raise MissingKey(f"{env_var} holds the Voyager key, not a {name} key; refusing to send it to {name}")
    return key


class MissingKey(RuntimeError):
    pass


def tool_calls_from_openai(calls):
    return [{"id": c.get("id"), "name": (c.get("function") or {}).get("name"),
             "arguments": (c.get("function") or {}).get("arguments") or ""} for c in calls or []]


def assistant_tool_message(reply):
    """The assistant turn to append after a reply that called tools (canonical format).
    Provider items that must be echoed back (reasoning items, thinking blocks) ride
    along under `_native` and are ignored by every other provider."""
    msg = {"role": "assistant", "content": reply.final_text or None,
           "tool_calls": [{"id": c["id"], "type": "function",
                           "function": {"name": c["name"], "arguments": c["arguments"]}} for c in reply.tool_calls]}
    native = (reply.raw or {}).get("native_items")
    if native:
        msg["_native"] = {"provider": reply.provider, "items": native}
    return msg


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False)


def post_json(url, headers, payload, timeout=600):
    """One JSON POST. Returns (status, body dict). Network errors raise; HTTP errors
    return their status and parsed body so adapters can report them."""
    import urllib.error
    import urllib.request
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as err:
        try:
            body = json.loads(err.read().decode("utf-8", "replace"))
        except Exception:
            body = {}
        return err.code, body


def native_items(message, provider):
    """Provider-specific items stored on an assistant turn (e.g. OpenAI reasoning items
    or Anthropic thinking blocks) that must be echoed back unchanged; None otherwise."""
    nat = message.get("_native") or {}
    return nat.get("items") if nat.get("provider") == provider else None


def plain(messages):
    """Messages without `_native` riders, for providers that take the chat format as is."""
    return [{k: v for k, v in m.items() if k != "_native"} for m in messages]
