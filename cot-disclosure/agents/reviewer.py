"""Reviewer agent: sees the question plus what its variant allows, never the solver's prompt.

Variants (what the reviewer sees in addition to the question and the proposed answer):
  answer_only        nothing else
  plus_explanation   the solver's visible final answer text
  plus_private       + the solver's private reasoning (when the provider returns it)
  plus_tool_log      + the solver's tool calls and tool replies
Uses Experiment A's reviewer system prompt and FINAL: X parser unchanged; system_extra appends a sentence
to that system prompt (C9: "The tool's answer may be wrong; check it independently.").
Commit first (C10, second_message): the reviewer's own answer_only review comes first (its reply kept as the
assistant turn), then what the variant adds beyond the answer only, and a final answer (SECOND).
"""
import sys

from providers.base import CODE

sys.path.insert(0, str(CODE / "progress"))
from parse import parse_final  # noqa: E402
from reviewer_demo import SYSTEM  # noqa: E402

VARIANTS = ("answer_only", "plus_explanation", "plus_private", "plus_tool_log")
SECOND = ("You gave your own answer above, before seeing this. Considering your answer and this information, give "
          "your final answer. Explain briefly, then end with exactly FINAL: X, where X is one option letter.")


def parts(variant, question, proposed, final_text="", reasoning_text=None, tool_log=""):
    """The user message's parts for a variant: the question, the proposed answer, then what it adds."""
    parts = [question, f"Proposed answer: ({proposed})"]
    if variant in ("plus_explanation", "plus_private", "plus_tool_log"):
        parts.append("Proposed explanation:\n" + (final_text or ""))
    if variant in ("plus_private", "plus_tool_log") and reasoning_text:
        parts.append("Private reasoning of the first assistant:\n" + reasoning_text)
    if variant == "plus_tool_log":
        parts.append("Tool log of the first assistant:\n" + (tool_log or "(no tool calls)"))
    return parts


def message(variant, question, proposed, final_text="", reasoning_text=None, tool_log="", system_extra=None):
    system = f"{SYSTEM} {system_extra}" if system_extra else SYSTEM
    return [{"role": "system", "content": system},
            {"role": "user", "content": "\n\n".join(parts(variant, question, proposed, final_text, reasoning_text, tool_log))}]


def second_message(variant, question, proposed, first_reply, final_text="", reasoning_text=None, tool_log="",
                   system_extra=None):
    """C10: the answer_only review as it was sent, the reviewer's own reply to it, then the variant's
    additions and SECOND."""
    more = parts(variant, question, proposed, final_text, reasoning_text, tool_log)[2:]
    return message("answer_only", question, proposed, system_extra=system_extra) + [
        {"role": "assistant", "content": first_reply or ""},
        {"role": "user", "content": "\n\n".join(["More about the proposed answer.", *more, SECOND])}]


def review(generate, variant, question, proposed, n_options, *, final_text="", reasoning_text=None, tool_log="",
           system_extra=None, first_reply=None, **gen_kwargs):
    """One review; with first_reply (C10), the second turn after the reviewer's own answer_only reply."""
    msgs = (message(variant, question, proposed, final_text, reasoning_text, tool_log, system_extra) if first_reply is None
            else second_message(variant, question, proposed, first_reply, final_text, reasoning_text, tool_log, system_extra))
    reply = generate(messages=msgs, **gen_kwargs)
    letter, rule = parse_final(reply.final_text, n_options) if not reply.error else (None, "error")
    return reply, letter, rule
