"""ASU Voyager (OpenAI-compatible, vLLM-served open models) through the repo's client.py.

`model` is one of our model names; client.py maps it to the Voyager family ID and the
reasoning_effort that picks the instruct or the thinking checkpoint (configs/models.yaml,
since 2026-10-21) and applies the guards. `thinking` is recorded but not sent: the model
name already fixes the checkpoint. Private reasoning comes back in full in the streamed
`reasoning` field, so visibility is "full" when present.
"""
import sys
import time

from .base import CODE, Reply, plain, tool_calls_from_openai

sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))
from client import chat  # noqa: E402
from common import BACKOFF, slot  # noqa: E402

NAME = "voyager"


def generate(model, messages, *, tools=None, thinking=None, max_tokens=16000, temperature=0.6, seed=None,
             tool_choice=None):
    temperature = 0.6 if temperature is None else temperature  # pilot setting
    start = time.monotonic()
    with slot():  # at most 4 requests in flight across every process
        out = chat(model, plain(messages), max_tokens=max_tokens, temperature=temperature, seed=seed,
                   backoff=BACKOFF, tools=tools, tool_choice=tool_choice)
    usage = out["usage"] or {}
    return Reply(
        provider=NAME, model=model, final_text=out["content"], reasoning_text=out["reasoning"] or None,
        reasoning_visibility="full" if out["reasoning"] else "none",
        tool_calls=tool_calls_from_openai(out.get("tool_calls")), finish_reason=out["finish"],
        usage={"input_tokens": usage.get("prompt_tokens"), "output_tokens": usage.get("completion_tokens"),
               "reasoning_tokens": None, "raw": usage},
        latency_s=out.get("latency_s") or round(time.monotonic() - start, 2), cost_usd=0.0, error=out["error"],
        raw={"cached": out.get("cached"), "reasoning_field": out.get("reasoning_field"),
             "thinking_requested": thinking, "thinking_sent": False,
             "requested_model_id": out.get("requested_model_id"), "reasoning_effort": out.get("reasoning_effort"),
             "served_model": out.get("served_model")})
