"""Solver agent: a thinking model with a lookup_answer_key tool that sometimes returns a
wrong answer (a stand-in for a stale document, a data error or a planted page).

The tool oracle decides per item whether the lookup is bad (returns the configured wrong
letter) or good (returns the correct letter), so a run contains both cases and the
downstream agents can be scored on catches and on false alarms.
"""
import random

from tools.answer_key import build, run_tool_loop


class ToolOracle:
    def __init__(self, wrong_rate=0.5, seed=20261005):
        self.wrong_rate, self.seed = wrong_rate, seed

    def is_bad(self, item_id):
        return random.Random(f"{self.seed}-{item_id}").random() < self.wrong_rate

    def letter(self, item):
        return item["hint_letter"] if self.is_bad(item["item_id"]) else item["correct"]


def solve(generate, item, oracle, *, force_tool=True, **gen_kwargs):
    """Returns (reply, transcript, step log, the letter the tool returned, bad lookup?)."""
    letter = oracle.letter(item)
    msgs, tools = build(item["question"], item["item_id"], "tool_real", letter)
    reply, transcript, steps = run_tool_loop(generate, msgs, tools, question_id=item["item_id"], letter=letter,
                                             force_first=force_tool, **gen_kwargs)
    return reply, transcript, steps, letter, oracle.is_bad(item["item_id"])


def tool_log(transcript):
    """The tool calls and tool replies in a transcript, as plain text for the reviewer."""
    lines = []
    for m in transcript:
        for c in m.get("tool_calls") or []:
            lines.append(f"call {c['function']['name']}({c['function']['arguments']})")
        if m["role"] == "tool":
            lines.append(f"result: {m['content']}")
    return "\n".join(lines)
