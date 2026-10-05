"""Robust extraction of the final multiple-choice letter.

Models ignore format instructions: in our first pilot 17% of answers used
\\boxed{E} instead of 'Answer: (E)' and were silently scored wrong. Rules are
tried in priority order and the matching rule is returned for auditing.
Letters run A to J so ten-option items (MMLU-Pro) parse; `n_options` still
limits which letters count, so seven-option puzzles behave exactly as before.
"""
import re

RULES = [
    ("answer_colon", r"answer\s*[:：]\s*\**\s*\(?([A-J])\)?(?![a-z])"),
    ("boxed", r"\\boxed\{\s*(?:\\text\{)?\s*\(?([A-J])\)?"),
    ("answer_is", r"answer\s+is\s*:?\s*\**\s*\(?([A-J])\)?(?![a-z])"),
    ("bold", r"\*\*\s*\(?([A-J])\)?\s*\*\*"),
]
COMPILED = [(name, re.compile(rx, re.IGNORECASE)) for name, rx in RULES]


def parse_answer_span(text, n_options):
    """(letter, rule, (start, end) of the matched text) — the same rules, in the same
    priority order, as parse_answer; the span lets a viewer show where the letter was read."""
    text = text or ""
    valid = set("ABCDEFGHIJ"[:n_options])
    for name, rx in COMPILED:
        hits = [m for m in rx.finditer(text) if m.group(1).upper() in valid]
        if hits:
            return hits[-1].group(1).upper(), name, hits[-1].span()
    # last resort: a lone option letter near the end, but only if unambiguous
    offset = max(0, len(text) - 300)
    tail = [m for m in re.finditer(r"\(([A-J])\)", text[offset:]) if m.group(1) in valid]
    if len({m.group(1) for m in tail}) == 1:
        m = tail[-1]
        return m.group(1), "tail_paren", (offset + m.start(), offset + m.end())
    return None, "none", None


def parse_answer(text, n_options):
    letter, rule, _ = parse_answer_span(text, n_options)
    return letter, rule


# Reviewer replies (progress Experiment A) are asked to end with "FINAL: X".
# The letter must be upper case; without a FINAL line the general rules above
# are tried and the rule name is prefixed "fallback:" so it stays visible.
FINAL = re.compile(r"(?i:\bfinal)\s*[:：]\s*\**\s*\(?([A-J])\)?(?![A-Za-z])")


def parse_final(text, n_options):
    valid = set("ABCDEFGHIJ"[:n_options])
    hits = [h for h in FINAL.findall(text or "") if h in valid]
    if hits:
        return hits[-1], "final"
    letter, rule = parse_answer(text, n_options)
    return (letter, f"fallback:{rule}") if letter else (None, "none")
