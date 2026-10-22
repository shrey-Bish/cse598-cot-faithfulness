"""The one Olmo 3 7B Think prompt format Track A uses everywhere.

Every Olmo prompt is rendered locally with the pinned template
(templates/olmo3_think_tools.jinja: the official Think template, plus tool turns rendered
the way the Olmo 3 Instruct template renders them) and sent to Voyager's /v1/completions,
streamed. Voyager's chat endpoint applies a different template (the Instruct one; Step 1),
so it is never used for Olmo. We split the reasoning from the final answer at </think>
ourselves.

  text = render(messages, add_generation_prompt=True)     # ends with "<|im_start|>assistant\\n<think>"
  out = generate(model, messages)                          # client.complete on the rendered text
"""
import hashlib
import json
import re
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

TEMPLATES = Path(__file__).resolve().parent / "templates"
PINNED_FILE = TEMPLATES / "olmo3_think_tools.jinja"
PINNED = PINNED_FILE.read_text()
PINNED_SHA256 = hashlib.sha256(PINNED.encode()).hexdigest()
EOS = "<|endoftext|>"
THINK_OPEN, THINK_CLOSE = "<think>", "</think>"
GEN_PROMPT = "<|im_start|>assistant\n" + THINK_OPEN
CALLS = re.compile(r"<function_calls>(.*?)</function_calls>", re.DOTALL)
CALL_NAME = re.compile(r"^\s*([A-Za-z_][\w.]*)\s*\(")


def _dict_args(messages):
    """The template reads tool-call arguments as a mapping (vLLM parses JSON-string arguments
    before rendering; do the same)."""
    out = []
    for m in messages:
        m = dict(m)
        if m.get("tool_calls"):
            m["tool_calls"] = [{**tc, "function": {**tc["function"], "arguments": (
                json.loads(tc["function"]["arguments"]) if isinstance(tc["function"]["arguments"], str)
                else tc["function"]["arguments"])}} for tc in m["tool_calls"]]
        out.append(m)
    return out


def render(messages, add_generation_prompt=True, template=None, tools=None):
    """The exact prompt text. With add_generation_prompt it ends with the assistant header and
    "<think>", so the model's raw output is its reasoning, then "</think>", then the answer.
    tools (OpenAI-style specs) only change the default system prompt: it then declares them
    in the Olmo 3 Instruct template's words instead of "no functions" (SYSTEM_PROMPTS)."""
    from transformers.utils.chat_template_utils import render_jinja_template
    rendered, _ = render_jinja_template([_dict_args(messages)], tools=tools, chat_template=template or PINNED,
                                        add_generation_prompt=add_generation_prompt, eos_token=EOS)
    return rendered[0]


SYSTEM_PROMPTS = ("think_default", "think_declared_functions")   # tools=None / tools=[...]


def split(raw):
    """(reasoning, final) from the raw text generated after "<think>". Without a "</think>",
    the reply never left its reasoning: no final answer."""
    i = raw.find(THINK_CLOSE)
    if i < 0:
        return raw, ""
    return raw[:i], raw[i + len(THINK_CLOSE):]


def function_calls(final):
    """[(name, call text)] for each call the model wrote in its final answer."""
    calls = []
    for block in CALLS.findall(final or ""):
        for line in block.strip().splitlines():
            m = CALL_NAME.match(line)
            if m:
                calls.append((m.group(1), line.strip()))
    return calls


def generate(model, messages, *, max_tokens=16000, temperature=0.6, seed=None, stop_after_call=False,
             backoff=None, extra=None, prefix="", tools=None):
    """One streamed /v1/completions call on the rendered conversation (+ an optional reasoning
    prefix after "<think>"). Returns client.complete's result with `reasoning` and `content`
    split at </think>, plus `raw` (the generated text) and `prompt` (what was sent).

    stop_after_call ends generation right after a written tool call, so the caller can answer
    it (the call text is kept)."""
    from client import complete
    prompt = render(messages, add_generation_prompt=True, tools=tools) + prefix
    body = dict(extra or {})
    if stop_after_call:
        body.update({"stop": ["</function_calls>"], "include_stop_str_in_output": True})
    out = complete(model, prompt, max_tokens=max_tokens, temperature=temperature, seed=seed, backoff=backoff,
                   extra=body or None)
    raw = prefix + (out["content"] or "")
    reasoning, final = split(raw)
    return {**out, "raw": raw, "prompt": prompt, "reasoning": reasoning, "content": final,
            "reasoning_field": "split_at_think_close"}


def find_calls(reply):
    """For tools.answer_key.run_injected: the tool calls written in a reply's final answer."""
    return function_calls(reply.get("content"))


def assistant_turn(reply):
    """For tools.answer_key.run_injected: the assistant message that replays a reply in the
    conversation (its whole generated text, after the "<think>" the prompt opened)."""
    return {"role": "assistant", "content": THINK_OPEN + reply["raw"]}


CONTEXT = 65536        # olmo3-7b: context_window and max_input_tokens in Voyager's /v1/models (2026-10-21)
CONTEXT_MARGIN = 64


def extend(model, prompt, raw, usage, *, temperature=0.6, seed=None, stop_after_call=False, backoff=None):
    """Continue a reply that hit its token cap, from exactly where it stopped, up to the model's
    context: the same streamed /v1/completions request on prompt + the text so far. Equivalent
    to one run with the larger cap (the first part is reused, not regenerated). Returns a reply
    like generate()'s, covering the whole text, or None if the context has no room left.
    A reply still cut off at the context limit is no answer (finish "length")."""
    from client import complete
    used = (usage or {}).get("prompt_tokens", 0) + (usage or {}).get("completion_tokens", 0)
    room = CONTEXT - used - CONTEXT_MARGIN
    if room < 256:
        return None
    body = {"stop": ["</function_calls>"], "include_stop_str_in_output": True} if stop_after_call else None
    out = complete(model, prompt + raw, max_tokens=room, temperature=temperature, seed=seed, backoff=backoff, extra=body)
    whole = raw + (out["content"] or "")
    reasoning, final = split(whole)
    added = (out.get("usage") or {}).get("completion_tokens") or 0
    return {**out, "raw": whole, "prompt": prompt, "reasoning": reasoning, "content": final,
            "reasoning_field": "split_at_think_close",
            "usage": {"prompt_tokens": (usage or {}).get("prompt_tokens"),
                      "completion_tokens": (usage or {}).get("completion_tokens", 0) + added},
            "extension": {"from_completion_tokens": (usage or {}).get("completion_tokens", 0), "added_tokens": added,
                          "max_tokens_continuation": room, "finish": out["finish"], "error": out["error"]}}
