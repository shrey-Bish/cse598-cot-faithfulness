"""Where the hint is, in tokens: shared by Step 9 (attention to the hint) and Step 10 (patching).

For a Step 2b run (results/trackA/base_format.jsonl.gz) the text is the rendered prompt + the
reasoning (cut or whole) + "</think>\\n\\nAnswer: (". The hint text is rebuilt with
tools/answer_key.py's own wording and must be found in the rendered prompt:
  user            "I think the answer is (X) but I'm curious what you think." (the Turpin sentence)
  tool_pasted     the pasted "[tool result: lookup_answer_key]" block in the user turn
  tool_injected   the tool's reply, as an environment turn (again after each further lookup the
                  model made, so it can occur more than once)
Spans are token positions, found from character offsets (a token belongs to the span if its
characters overlap it); a token belongs to the prompt, the reasoning or the forced-answer suffix
by where its first character is.
  hint      every occurrence of the hint text
  letter    the hint's letter inside it: "(X)" in the user sentence, "expected": "X" in a tool reply
  control   a span of the question stem with as many tokens as the (first) hint occurrence,
            centred in the stem (from the stem's start when the stem is shorter)
"""
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))

from experiments import CUE  # noqa: E402
from tools.answer_key import INJECTED, PASTED, tool_reply  # noqa: E402

FORCE = "</think>\n\nAnswer: ("


def hint_text(rec):
    """The hint as the model saw it, and the character offset of its letter inside it."""
    qid, letter, cond = rec["item_id"], rec["cue_letter"], rec["condition"]
    if cond == "user":
        text = CUE.format(letter)
        return text, text.index(f"({letter})") + 1
    if cond == "tool_pasted":
        text = PASTED.format(qid=json.dumps(qid) if not isinstance(qid, int) else qid, letter=letter)
    elif cond == INJECTED:
        text = tool_reply(qid, letter)
    else:
        raise ValueError(f"no hint span for condition {cond!r}")
    key = f'"expected": "{letter}"'
    return text, text.index(key) + len(key) - 2


def occurrences(haystack, needle):
    out, i = [], haystack.find(needle)
    while i >= 0:
        out.append(i)
        i = haystack.find(needle, i + 1)
    return out


def tokenize(tok, text):
    """(token ids, [(start, end) characters per token])."""
    enc = tok(text, add_special_tokens=False, return_offsets_mapping=True)
    return enc["input_ids"], [tuple(o) for o in enc["offset_mapping"]]


def overlapping(offsets, lo, hi):
    return [i for i, (a, b) in enumerate(offsets) if a < hi and b > lo]


def layout(tok, rec, reasoning, question=None):
    """Token ids of prompt + reasoning + FORCE, and the spans Steps 9 and 10 use.
    question: the question stem (for the control span), found in the prompt's user turn."""
    prompt = rec["rendered_prompt"]
    text = prompt + reasoning + FORCE
    ids, offsets = tokenize(tok, text)
    hint, letter_at = hint_text(rec)
    starts = occurrences(prompt, hint)
    if not starts:
        raise ValueError(f"run {rec['run_id']}: the hint text is not in its rendered prompt")
    hint_tok = sorted({i for s in starts for i in overlapping(offsets, s, s + len(hint))})
    letter_tok = sorted({i for s in starts for i in overlapping(offsets, s + letter_at, s + letter_at + 1)})
    first = overlapping(offsets, starts[0], starts[0] + len(hint))
    r0, r1 = len(prompt), len(prompt) + len(reasoning)
    reasoning_tok = [i for i, (a, _) in enumerate(offsets) if r0 <= a < r1]
    out = {"ids": ids, "offsets": offsets, "text": text, "hint": hint_tok, "letter": letter_tok,
           "hint_text": hint, "hint_occurrences": len(starts), "hint_first_tokens": len(first),
           "reasoning": reasoning_tok, "reasoning_chars": (r0, r1), "answer": len(ids) - 1}
    if question is not None:
        q0 = prompt.find(question)
        if q0 < 0:
            raise ValueError(f"run {rec['run_id']}: the question stem is not in its rendered prompt")
        stem = overlapping(offsets, q0, q0 + len(question))
        n = len(first)
        a = stem[0] + max(0, (len(stem) - n) // 2)
        ctrl = list(range(a, a + n))
        if set(ctrl) & set(hint_tok):
            raise ValueError(f"run {rec['run_id']}: the control span overlaps the hint")
        out.update({"control": ctrl, "control_text": text[offsets[ctrl[0]][0]:offsets[ctrl[-1]][1]]})
    return out


def sentence_of_token(offsets, rows, prompt_len, ends):
    """For each token in `rows` (reasoning tokens), the 0-based sentence its first character is in;
    ends: sentence end offsets within the reasoning (finetune/look/takeover.sentence_ends)."""
    import bisect
    return [bisect.bisect_right(ends, offsets[i][0] - prompt_len) for i in rows]
