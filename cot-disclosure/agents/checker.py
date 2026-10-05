"""Checker agent: re-asks the solver model the same question without the tool and flags
the item when the answer changes (the counterfactual guard from Experiment A, live)."""
from parse import parse_answer
from tools.answer_key import build


def check(generate, item, solver_letter, *, seed=3, **gen_kwargs):
    msgs, _ = build(item["question"], item["item_id"], "none")
    reply = generate(messages=msgs, seed=seed, **gen_kwargs)
    letter = parse_answer(reply.final_text, item["n_options"])[0] if not reply.error else None
    flag = None if letter is None else letter != solver_letter   # None: no answer, undetermined
    return reply, letter, flag
