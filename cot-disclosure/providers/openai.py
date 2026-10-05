"""OpenAI Responses API adapter (see providers/responses_api.py for the documented facts)."""
import time

from . import responses_api as R
from .base import AUTH_HEADER, Reply, post_json, provider_key
from .config import resolve_effort

NAME = "openai"
URL = "https://api.openai.com/v1/responses"
KEY_ENV = "OPENAI_API_KEY"


def generate(model, messages, *, tools=None, thinking=None, max_tokens=4000, temperature=None, seed=None,
             tool_choice=None, effort=None, url=URL, provider=NAME, key_env=KEY_ENV, label="OpenAI"):
    effort = resolve_effort(model, thinking, effort)
    req = R.build_request(model, messages, provider=provider, tools=tools, tool_choice=tool_choice, effort=effort,
                          max_tokens=max_tokens, temperature=temperature)
    key = provider_key(label, key_env)
    start = time.monotonic()
    try:
        status, body = post_json(url, {AUTH_HEADER: f"Bearer {key}"}, req)
    except Exception as err:  # network failure
        return Reply(provider=provider, model=model, error=type(err).__name__, finish_reason="error")
    latency = round(time.monotonic() - start, 2)
    if status != 200:
        return Reply(provider=provider, model=model, error=R.error_text(status, body), finish_reason="error",
                     latency_s=latency, raw={"request_effort": effort})
    text, summary, calls, usage, finish, native = R.parse_response(body)
    return Reply(provider=provider, model=model, final_text=text, reasoning_text=summary,
                 reasoning_visibility="summary" if summary else "none", tool_calls=calls, finish_reason=finish,
                 usage=usage, latency_s=latency,
                 raw={"native_items": native, "effort": effort, "seed_ignored": seed is not None,
                      "id": body.get("id")})
