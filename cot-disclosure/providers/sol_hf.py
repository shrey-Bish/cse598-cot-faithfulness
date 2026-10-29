"""Track B's Qwen3-8B without a server: Hugging Face generation inside the Sol job (finetune/hf_engine.py),
in place of vLLM (decided Oct 29: vLLM's engine core failed in its kernel warmup on Sol, Oct 28-29). The
provider stays sol_vllm, so run ids, records, the numbers-only flags and the report are unchanged:
providers/sol_vllm.py hands each request here once progress/sol_trackB.py --engine hf has installed an
engine, and every record says which engine wrote it ("engine": "hf-continuous", "hf-static" or "vllm").

What the vLLM server did, done here the same way:
  - the prompt: the snapshot's chat template (the file whose sha256 every run records) through the
    tokenizer's apply_chat_template with add_generation_prompt, the tools and enable_thinking (only when
    the request sets it), after vLLM's message handling: a tool call's JSON-string arguments parsed into
    a mapping (empty: {}), a missing content as "", each tool spec as {type, function: {name,
    description, parameters}} (its pydantic fields, in their order)
  - the private reasoning (--reasoning-parser qwen3): a leading <think> dropped; reasoning = the text
    before </think>, the reply = the text after it. No </think>: with thinking off (the template renders
    the empty think block in the prompt, so the reply has neither tag) the whole text is the reply. A
    reply that opened <think> and stopped before </think> (it hit the token cap) is all private
    reasoning and no reply; vLLM's parser would have returned that text as the reply. Such a run has
    finish "length" and so no answer either way (run_trackB.no_answer_if_cut).
  - tool calls (--tool-call-parser hermes), only when the request declared tools: every
    <tool_call>{json}</tool_call> block in the reply (an unclosed last one too), name and arguments
    (re-serialized as JSON) as OpenAI-style calls; the reply keeps only the text before the first block.
    A block that isn't JSON with a name and arguments: no calls, the reply unchanged. Calls make the
    finish reason "tool_calls", as vLLM reports it.
  - sampling: the caller's temperature (0.6), top_p 0.95 and top_k 20 (providers/sol_vllm.py, the same
    with thinking on and off), the engine's end tokens (<|im_end|>, <|endoftext|>); max_tokens is the
    budget left. Per-run seeds can't be kept inside a batch (finetune/hf_engine.py): runs are samples.
An engine failure is a reply that never finished: not_run (retried), never "no answer".
"""
import json
import re
import time
import uuid

from .base import Reply, plain

NAME = "sol_vllm"                          # the provider the config, run ids and records name
THINK_OPEN, THINK_CLOSE = "<think>", "</think>"
TOOL_OPEN = "<tool_call>"
TOOL_CALL = re.compile(r"<tool_call>(.*?)</tool_call>|<tool_call>(.*)", re.DOTALL)     # vLLM's hermes regex
_STATE = {"engine": None, "tokenizer": None, "template": None, "template_sha256": None, "sample": None}


def install(engine, tokenizer, template, template_sha256, sample=None):
    """Route sol_vllm's requests to this in-process engine (progress/sol_trackB.py --engine hf)."""
    _STATE.update(engine=engine, tokenizer=tokenizer, template=template, template_sha256=template_sha256,
                  sample=sample)


def uninstall():
    for k in _STATE:
        _STATE[k] = None


def active():
    return _STATE["engine"] is not None


def engine_name():
    kind = getattr(_STATE["engine"], "kind", None)
    return f"hf-{kind}" if kind else "hf"


# ---------------------------------------------------------------- the prompt
def vllm_messages(messages):
    """The messages as vLLM's chat endpoint hands them to the template."""
    out = []
    for m in plain(messages):
        m = dict(m)
        if m.get("content") is None:
            m["content"] = ""
        if m.get("role") == "assistant" and isinstance(m.get("tool_calls"), list):
            calls = []
            for c in m["tool_calls"]:
                fn = dict(c.get("function") or {})
                args = fn.get("arguments")
                fn["arguments"] = (args if isinstance(args, dict) else json.loads(args)) if args else {}
                calls.append({**c, "function": fn})
            m["tool_calls"] = calls
        out.append(m)
    return out


def vllm_tools(tools):
    return [{"type": t.get("type", "function"),
             "function": {"name": t["function"]["name"], "description": t["function"].get("description"),
                          "parameters": t["function"].get("parameters")}} for t in tools]


def render(tokenizer, template, messages, tools=None, thinking=None):
    kw = {} if thinking is None else {"enable_thinking": bool(thinking)}
    return tokenizer.apply_chat_template(vllm_messages(messages), tools=vllm_tools(tools) if tools else None,
                                         chat_template=template, add_generation_prompt=True, tokenize=False, **kw)


# ---------------------------------------------------------------- the reply
def split_reasoning(text):
    """(reasoning or None, reply or None, cut inside the reasoning): the module docstring's rule."""
    head, opened, tail = text.partition(THINK_OPEN)
    rest = tail if opened else head
    if THINK_CLOSE not in rest:
        if opened:
            return rest or None, None, True
        return None, rest or None, False
    reasoning, _, content = rest.partition(THINK_CLOSE)
    return reasoning or None, content or None, False


def tool_calls(content):
    """([{"id", "name", "arguments"}], the reply without the calls): vLLM's hermes parser."""
    if not content or TOOL_OPEN not in content:
        return [], content
    try:
        raw = [json.loads(a if a else b) for a, b in TOOL_CALL.findall(content)]
        calls = [{"id": f"chatcmpl-tool-{uuid.uuid4().hex[:24]}", "name": c["name"],
                  "arguments": json.dumps(c["arguments"], ensure_ascii=False)} for c in raw]
    except Exception:                                                  # noqa: BLE001 - as vLLM: no calls
        return [], content
    before = content[:content.find(TOOL_OPEN)]
    return calls, before or None


def parse(text, finish, tools=None):
    """(reply text, reasoning, tool calls, finish reason, cut inside the reasoning) from a raw reply."""
    reasoning, content, cut = split_reasoning(text)
    calls = []
    if tools:
        calls, content = tool_calls(content)
    return content or "", reasoning, calls, "tool_calls" if calls else finish, cut


def generate(model, messages, *, max_tokens, tools=None, thinking=None, temperature=0.6, seed=None, tool_choice=None):
    if not active():
        raise RuntimeError("no Hugging Face engine installed (progress/sol_trackB.py --engine hf installs one)")
    if not max_tokens or max_tokens < 1:
        raise ValueError(f"max_tokens must be the budget left (32,768 minus the prompt and replies so far), not {max_tokens!r}")
    temperature = 0.6 if temperature is None else temperature
    tok, eng = _STATE["tokenizer"], _STATE["engine"]
    start = time.monotonic()
    prompt = render(tok, _STATE["template"], messages, tools, thinking)
    out = eng(model, prompt, max_tokens=max_tokens, temperature=temperature, seed=seed)
    raw = {"enable_thinking": thinking, "served_model": model, "top_p": (_STATE["sample"] or {}).get("top_p"),
           "top_k": (_STATE["sample"] or {}).get("top_k"), "chat_template_sha256": _STATE["template_sha256"],
           "engine": engine_name()}
    latency = round(time.monotonic() - start, 2)
    if out.get("error"):
        return Reply(provider=NAME, model=model, error=f"IncompleteStream: {out['error']}", finish_reason="error",
                     latency_s=latency, raw=raw)
    text, reasoning, calls, finish, cut = parse(out.get("content") or "", out.get("finish"), tools)
    usage = out.get("usage") or {}
    return Reply(provider=NAME, model=model, final_text=text, reasoning_text=reasoning,
                 reasoning_visibility="full" if reasoning else "none", tool_calls=calls, finish_reason=finish,
                 usage={"input_tokens": usage.get("prompt_tokens"), "output_tokens": usage.get("completion_tokens"),
                        "reasoning_tokens": None, "raw": usage},
                 latency_s=latency, cost_usd=0.0, raw={**raw, "reasoning_cut": cut})
