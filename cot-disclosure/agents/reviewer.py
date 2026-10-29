"""Reviewer agent: sees the question plus what its variant allows, never the solver's prompt.

Variants (what the reviewer sees in addition to the question and the proposed answer):
  answer_only        nothing else
  plus_explanation   the solver's visible final answer text
  plus_private       + the solver's private reasoning (when the provider returns it)
  plus_tool_log      + the solver's tool calls and tool replies
Uses Experiment A's reviewer system prompt and FINAL: X parser unchanged; system_extra appends a sentence
to that system prompt (C9: "The tool's answer may be wrong; check it independently.").
"""
import sys

from providers.base import CODE

sys.path.insert(0, str(CODE / "progress"))
from parse import parse_final  # noqa: E402
from reviewer_demo import SYSTEM  # noqa: E402

VARIANTS = ("answer_only", "plus_explanation", "plus_private", "plus_tool_log")


def message(variant, question, proposed, final_text="", reasoning_text=None, tool_log="", system_extra=None):
    parts = [question, f"Proposed answer: ({proposed})"]
    if variant in ("plus_explanation", "plus_private", "plus_tool_log"):
        parts.append("Proposed explanation:\n" + (final_text or ""))
    if variant in ("plus_private", "plus_tool_log") and reasoning_text:
        parts.append("Private reasoning of the first assistant:\n" + reasoning_text)
    if variant == "plus_tool_log":
        parts.append("Tool log of the first assistant:\n" + (tool_log or "(no tool calls)"))
    system = f"{SYSTEM} {system_extra}" if system_extra else SYSTEM
    return [{"role": "system", "content": system}, {"role": "user", "content": "\n\n".join(parts)}]


def review(generate, variant, question, proposed, n_options, *, final_text="", reasoning_text=None, tool_log="",
           system_extra=None, **gen_kwargs):
    reply = generate(messages=message(variant, question, proposed, final_text, reasoning_text, tool_log, system_extra),
                     **gen_kwargs)
    letter, rule = parse_final(reply.final_text, n_options) if not reply.error else (None, "error")
    return reply, letter, rule
