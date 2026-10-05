"""Does Voyager support real tool calls? (Track B prerequisite)

  python progress/check_tool_support.py

Pilot puzzle 0, `tool_real` condition (the tool returns the pilot's wrong letter),
temperature 0.6, seed 0. For each model: does it call lookup_answer_key on its own
(tool_choice auto), and with a forced tool_choice; are the arguments valid JSON; what
letter does it answer after the tool reply. Writes results/scope/voyager_tool_support.jsonl.
One puzzle per model: a capability check, not a measurement of hint following.
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from common import CODE, get_logger

sys.path.insert(0, str(CODE))
import experiments as pilot  # noqa: E402
from parse import parse_answer  # noqa: E402
from providers import voyager  # noqa: E402
from tools.answer_key import build, run_tool_loop  # noqa: E402

OUT = CODE / "results" / "scope" / "voyager_tool_support.jsonl"
CHECKS = [("qwen3-30b-a3b-instruct-2507", False), ("qwen3-30b-a3b-instruct-2507", True),
          ("qwen3-30b-a3b-thinking-2507", True), ("olmo3-7b-instruct", False),
          ("olmo3-7b-think", False), ("olmo3-7b-think", True)]
log = get_logger("toolcheck")


def check(model, forced):
    item, letter = pilot.ITEMS[0], pilot.WRONG_CUES[(0, 0)]
    msgs, tools = build(item["question"], "pilot-0", "tool_real", letter)
    reply, transcript, steps = run_tool_loop(lambda **kw: voyager.generate(model, **kw), msgs, tools,
                                             question_id="pilot-0", letter=letter, force_first=forced,
                                             max_tokens=8000, temperature=0.6, seed=0)
    first = steps[0]["tool_calls"]

    def valid(a):
        try:
            return isinstance(json.loads(a), dict)
        except json.JSONDecodeError:
            return False
    answer = parse_answer(reply.final_text, len(item["options"]))[0] if not reply.error else None
    rec = {"timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "model": model,
           "tool_choice": "forced" if forced else "auto", "called_tool": bool(first),
           "arguments_valid_json": all(valid(c["arguments"]) for c in first) if first else None,
           "first_call_arguments": [c["arguments"] for c in first], "steps": len(steps),
           "error": reply.error, "final_letter": answer, "hint_letter": letter, "correct_letter": item["correct"],
           "followed_tool_hint": answer == letter if answer else None,
           "reasoning_visibility": reply.reasoning_visibility, "final_text_tail": (reply.final_text or "")[-200:],
           "transcript": transcript, "step_log": steps}
    log.info(f"toolcheck {model} {rec['tool_choice']}: called={rec['called_tool']} "
             f"valid_args={rec['arguments_valid_json']} error={rec['error']} answer={answer}")
    return rec


def main():
    with ThreadPoolExecutor(4) as pool, open(OUT, "w") as f:
        for rec in pool.map(lambda c: check(*c), CHECKS):
            f.write(json.dumps(rec) + "\n")
    print(f"wrote {OUT.relative_to(CODE.parent)}")


if __name__ == "__main__":
    main()
