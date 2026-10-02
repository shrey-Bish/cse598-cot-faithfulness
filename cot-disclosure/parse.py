"""Robust extraction of the final multiple-choice letter.

Models ignore format instructions: in our first pilot 17% of answers used
\\boxed{E} instead of 'Answer: (E)' and were silently scored wrong. Rules are
tried in priority order and the matching rule is returned for auditing.
"""
import re

RULES = [
    ("answer_colon", r"answer\s*[:：]\s*\**\s*\(?([A-I])\)?(?![a-z])"),
    ("boxed", r"\\boxed\{\s*(?:\\text\{)?\s*\(?([A-I])\)?"),
    ("answer_is", r"answer\s+is\s*:?\s*\**\s*\(?([A-I])\)?(?![a-z])"),
    ("bold", r"\*\*\s*\(?([A-I])\)?\s*\*\*"),
]
COMPILED = [(name, re.compile(rx, re.IGNORECASE)) for name, rx in RULES]


def parse_answer(text, n_options):
    valid = set("ABCDEFGHI"[:n_options])
    for name, rx in COMPILED:
        hits = [h.upper() for h in rx.findall(text or "") if h.upper() in valid]
        if hits:
            return hits[-1], name
    # last resort: a lone option letter near the end, but only if unambiguous
    tail = set(h for h in re.findall(r"\(([A-I])\)", (text or "")[-300:]) if h in valid)
    if len(tail) == 1:
        return tail.pop(), "tail_paren"
    return None, "none"
