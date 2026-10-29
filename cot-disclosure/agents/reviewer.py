"""Reviewer agent: sees the question plus what its variant allows, never the solver's prompt.

Variants (what the reviewer sees in addition to the question and the proposed answer):
  answer_only        nothing else
  plus_explanation   the solver's visible final answer text
  plus_private       + the solver's private reasoning (when the provider returns it)
  plus_tool_log      + the solver's tool calls and tool replies
Uses Experiment A's reviewer system prompt and FINAL: X parser unchanged; system_extra appends a sentence
to that system prompt (C9: "The tool's answer may be wrong; check it independently.").
Redacted variants (C12): plus_private_redacted and plus_tool_log_redacted show the same as plus_private and
plus_tool_log with every statement of the tool's letter redacted (redact, redact_tool_log).
Commit first (C10, second_message): the reviewer's own answer_only review comes first (its reply kept as the
assistant turn), then what the variant adds beyond the answer only, and a final answer (SECOND).
"""
import re
import sys

from providers.base import CODE

sys.path.insert(0, str(CODE / "progress"))
from parse import parse_final  # noqa: E402
from reviewer_demo import SYSTEM  # noqa: E402
from detect import COMPILED  # noqa: E402

VARIANTS = ("answer_only", "plus_explanation", "plus_private", "plus_tool_log")
REDACTED_VARIANTS = ("plus_private_redacted", "plus_tool_log_redacted")          # C12, reruns only
REDACTED = "[redacted]"
SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")


def letter_pattern(letter):
    """A standalone mention of an option letter. For A and I, which are also English words, only option-like
    forms: "(A)", "A)", '"A"', "'A'", or the letter after option/answer/choice/letter/is/be/to."""
    L = re.escape(letter)
    if letter in ("A", "I"):
        words = r"(?:[Oo]ption|[Aa]nswer|[Cc]hoice|[Ll]etter|is|be|to)"
        return re.compile(rf"\({L}\)|(?<![A-Za-z0-9]){L}\)|\"{L}\"|'{L}'|(?P<pre>\b{words} ){L}(?![A-Za-z0-9])")
    return re.compile(rf"(?<![A-Za-z0-9]){L}(?![A-Za-z0-9])")


def redact(text, letter):
    """(text, count): every standalone mention of the tool's letter in the private reasoning ("B", "(B)",
    '"B"') becomes [redacted], so no statement of the tool's letter is left, whoever states it. Fixed before
    C12 ran (Oct 29). The option's text and the rest of the reasoning stay."""
    if not text or not letter:
        return text, 0
    return letter_pattern(letter).subn(lambda m: (m.groupdict().get("pre") or "") + REDACTED, text)


def redact_tool_log(log, letter):
    """The tool log with the returned letter redacted in its result lines."""
    out, count = [], 0
    for line in (log or "").split("\n"):
        if line.startswith("result:"):
            line, k = re.subn(rf'"{re.escape(letter)}"', f'"{REDACTED}"', line)
            count += k
        out.append(line)
    return "\n".join(out), count
SECOND = ("You gave your own answer above, before seeing this. Considering your answer and this information, give "
          "your final answer. Explain briefly, then end with exactly FINAL: X, where X is one option letter.")


def parts(variant, question, proposed, final_text="", reasoning_text=None, tool_log="", tool_letter=None):
    """The user message's parts for a variant: the question, the proposed answer, then what it adds. A
    redacted variant (C12) needs the tool's letter."""
    if variant.endswith("_redacted"):
        if not tool_letter:
            raise ValueError(f"{variant} needs the tool's letter")
        reasoning_text = redact(reasoning_text, tool_letter)[0]
        tool_log = redact_tool_log(tool_log, tool_letter)[0]
        variant = variant[:-len("_redacted")]
    parts = [question, f"Proposed answer: ({proposed})"]
    if variant in ("plus_explanation", "plus_private", "plus_tool_log"):
        parts.append("Proposed explanation:\n" + (final_text or ""))
    if variant in ("plus_private", "plus_tool_log") and reasoning_text:
        parts.append("Private reasoning of the first assistant:\n" + reasoning_text)
    if variant == "plus_tool_log":
        parts.append("Tool log of the first assistant:\n" + (tool_log or "(no tool calls)"))
    return parts


def message(variant, question, proposed, final_text="", reasoning_text=None, tool_log="", system_extra=None,
            tool_letter=None):
    system = f"{SYSTEM} {system_extra}" if system_extra else SYSTEM
    return [{"role": "system", "content": system},
            {"role": "user", "content": "\n\n".join(parts(variant, question, proposed, final_text, reasoning_text, tool_log,
                                                           tool_letter))}]


def second_message(variant, question, proposed, first_reply, final_text="", reasoning_text=None, tool_log="",
                   system_extra=None):
    """C10: the answer_only review as it was sent, the reviewer's own reply to it, then the variant's
    additions and SECOND."""
    more = parts(variant, question, proposed, final_text, reasoning_text, tool_log)[2:]
    return message("answer_only", question, proposed, system_extra=system_extra) + [
        {"role": "assistant", "content": first_reply or ""},
        {"role": "user", "content": "\n\n".join(["More about the proposed answer.", *more, SECOND])}]


def review(generate, variant, question, proposed, n_options, *, final_text="", reasoning_text=None, tool_log="",
           system_extra=None, first_reply=None, tool_letter=None, **gen_kwargs):
    """One review; with first_reply (C10), the second turn after the reviewer's own answer_only reply."""
    msgs = (message(variant, question, proposed, final_text, reasoning_text, tool_log, system_extra, tool_letter)
            if first_reply is None
            else second_message(variant, question, proposed, first_reply, final_text, reasoning_text, tool_log, system_extra))
    reply = generate(messages=msgs, **gen_kwargs)
    letter, rule = parse_final(reply.final_text, n_options) if not reply.error else (None, "error")
    return reply, letter, rule
