"""Track A: continue an Olmo reply from a given point to a final answer, the same way everywhere
(Step 4's deletion test, the look-inside reruns, Phase 6's evaluation of trained versions).

continue_to_answer(messages, prompt, text, cap=..., condition=..., ...) sends prompt + text through
/v1/completions (the pinned format, rendered by the caller) and goes on until a final answer:
  - a stop on a call quoted inside the reasoning goes on (base_format.stopped_early)
  - with the inserted tool turn, a tool call in the final answer (after </think>) is answered the
    way tools.answer_key.run_injected answers it in Step 2b: the reply is replayed as an assistant
    turn, the tool's same (wrong) result follows, and the next round is rendered with the pinned
    template; at most MAX_EXTRA_ROUNDS more rounds, and still calling after that is no answer
  - every round shares one token cap; hitting it is no answer (finish "length")
complete_fn defaults to client.complete (Voyager); Phase 6 passes its local server's instead.
"""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import BACKOFF, slot  # noqa: E402
from finetune import base_format as bf  # noqa: E402
from finetune import olmo_format  # noqa: E402
from tools.answer_key import INJECTED, MAX_EXTRA_ROUNDS, run_injected  # noqa: E402

MAX_QUOTED = 10                    # continuations past a call quoted in the reasoning, per round
STOP_AFTER_CALL = {"stop": ["</function_calls>"], "include_stop_str_in_output": True}


class _Budget:
    def __init__(self, cap):
        self.cap, self.used = cap, 0

    @property
    def left(self):
        return self.cap - self.used


def _round(prompt, text, budget, *, condition, seed, model, temperature, complete_fn, backoff, use_slot):
    """One round: from prompt + text, within what is left of the cap; goes past quoted calls."""
    body = STOP_AFTER_CALL if condition == INJECTED else None
    raw, prompt_tokens, out = text, None, None
    for _ in range(1 + MAX_QUOTED):
        if budget.left <= 0:
            break
        if use_slot:
            with slot():
                res = complete_fn(model, prompt + raw, max_tokens=budget.left, temperature=temperature, seed=seed,
                                  backoff=backoff, extra=body)
        else:
            res = complete_fn(model, prompt + raw, max_tokens=budget.left, temperature=temperature, seed=seed,
                              backoff=backoff, extra=body)
        usage = res.get("usage") or {}
        prompt_tokens = prompt_tokens or usage.get("prompt_tokens")
        raw += res.get("content") or ""
        budget.used += usage.get("completion_tokens") or 0
        reasoning, final = olmo_format.split(raw)
        out = {**res, "prompt": prompt, "raw": raw, "reasoning": reasoning, "content": final,
               "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": budget.used}}
        if out["error"] or bf.stopped_early(out, condition) != "call quoted in the reasoning":
            return out
    if out is None or budget.left <= 0:                     # the cap is spent: no answer
        base = out or {"error": None, "usage": {"prompt_tokens": None, "completion_tokens": budget.used}}
        return {**base, "prompt": prompt, "raw": raw, "reasoning": olmo_format.split(raw)[0], "content": "",
                "finish": "length", "no_answer_reason": "hit the token cap"}
    return out


def continue_to_answer(messages, prompt, text, *, cap, condition, question_id, letter, seed, tools=None,
                       model=bf.MODEL, temperature=bf.TEMPERATURE, complete_fn=None, backoff=BACKOFF, use_slot=True,
                       max_extra=MAX_EXTRA_ROUNDS, render=None):
    """(last reply, rounds log, tool calls the model made, the messages before the last reply).
    messages: the conversation whose rendering is `prompt` (the round being continued); text: the
    reasoning so far, after the prompt's "<think>"; cap: new tokens allowed over all rounds.
    render(messages, tools) renders a later round (default: the pinned format; prompt-only adds its
    note to the system turn the same way in every round)."""
    if complete_fn is None:
        from client import complete as complete_fn
    render = render or (lambda msgs, tools: olmo_format.render(msgs, tools=tools))
    budget = _Budget(cap)
    pending = [(prompt, text)]

    def generate_round(msgs):
        p, t = pending.pop() if pending else (render(msgs, tools), "")
        reply = _round(p, t, budget, condition=condition, seed=seed, model=model, temperature=temperature,
                       complete_fn=complete_fn, backoff=backoff, use_slot=use_slot)
        if reply.get("finish") == "length" and not reply.get("no_answer_reason"):
            reply["no_answer_reason"] = "hit the token cap"
        return reply

    if condition != INJECTED:
        reply = generate_round(messages)
        return reply, [{"round": 0, "finish": reply.get("finish"), "error": reply.get("error"), "calls": [],
                        "usage": reply.get("usage")}], 0, list(messages)
    reply, msgs, rounds, model_calls = run_injected(generate_round, messages, question_id=question_id, letter=letter,
                                                    find_calls=olmo_format.find_calls,
                                                    assistant_turn=olmo_format.assistant_turn, max_extra=max_extra)
    return reply, rounds, model_calls, msgs
