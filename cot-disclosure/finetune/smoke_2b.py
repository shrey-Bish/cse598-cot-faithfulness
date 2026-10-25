"""Track A step 2b smoke test, before the full run: 3 checks on olmo3-7b-think, one question.

  1 a user-hint run, end to end (pinned format, /v1/completions, split at </think>)
  2 an inserted-tool run, end to end (our call + the tool's wrong reply; further calls answered)
  3 the stop rule: continue from a prefix that ends inside a tool call
    ("...</think>\\n\\n<function_calls>lookup_answer_key("), and check that generation stops at
    </function_calls>, that our parser reads the call, and that the environment reply is
    rendered right after it

  python finetune/smoke_2b.py --dry-run      # what it will send; no calls
  python finetune/smoke_2b.py                # run; records -> results/trackA/base_format_smoke.jsonl.gz

Checks 1 and 2 are the same requests as the full run's first jobs, so the full run reuses
their replies from the cache. Check 2 can take up to 3 calls if the model keeps calling.
Exits non-zero if any check fails.
"""
import argparse
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import BACKOFF, append, make_record, run_id, slot  # noqa: E402
from finetune import base_format as bf  # noqa: E402
from finetune import olmo_format  # noqa: E402
from mmlu_pro_probe import question_block  # noqa: E402
from tools.answer_key import INJECTED, TOOL_NAME, build, tool_reply  # noqa: E402

OUT = CODE / "results" / "trackA" / "base_format_smoke.jsonl.gz"
EXPERIMENT = "trackA_base_format_smoke"
PREFIX = "Let me look this up once more to check the answer key.</think>\n\n<function_calls>" + TOOL_NAME + "("


def stop_rule_check(it):
    qid, letter = it["question_id"], it["cue_letter"]
    msgs, _ = build(question_block(it), qid, INJECTED, letter)
    with slot():
        out = olmo_format.generate(bf.MODEL, msgs, max_tokens=64, temperature=bf.TEMPERATURE, seed=0,
                                   stop_after_call=True, backoff=BACKOFF, prefix=PREFIX)
    calls = olmo_format.find_calls(out)
    nxt = msgs + [olmo_format.assistant_turn(out), {"role": "tool", "name": TOOL_NAME, "content": tool_reply(qid, letter)}]
    rendered = olmo_format.render(nxt)
    seam = (out["raw"] + "<|im_end|>\n<|im_start|>environment\n" + tool_reply(qid, letter)
            + "<|im_end|>\n" + olmo_format.GEN_PROMPT)
    checks = {"stopped_on_stop_string": out["finish"] == "stop",
              "kept_the_closing_tag": out["raw"].endswith("</function_calls>"),
              "parser_read_one_lookup_call": [c[0] for c in calls] == [TOOL_NAME],
              "environment_reply_right_after_the_call": rendered.endswith(seam)}
    rec = make_record(out, experiment=EXPERIMENT, item_id=qid, model=bf.MODEL, condition="stop_rule", repeat=0,
                      messages=msgs, n_options=len(it["options"]), correct_letter=it["answer"], cue_letter=letter,
                      cue_channel=INJECTED, temperature=bf.TEMPERATURE, max_tokens=64, seed=0,
                      run_id_=run_id(EXPERIMENT, qid, bf.MODEL, "stop_rule", None, 0))
    rec.update({"endpoint": "completions", "rendered_prompt": out["prompt"], "raw_text": out["raw"], "prefix": PREFIX,
                "calls_parsed": calls, "next_round_tail": rendered[-400:], "checks": checks})
    return rec, checks


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="print what will be sent; no calls")
    a = ap.parse_args()
    it = bf.questions()[0]
    print(f"question {it['question_id']} ({it['category']}): correct ({it['answer']}), hint ({it['cue_letter']})")
    if a.dry_run:
        print("  1 user hint, seed 0, max_tokens 16000                     (1 call)")
        print("  2 inserted tool turn, think_default, seed 0, max_tokens 16000 (1 call, up to 3 if it keeps calling)")
        print(f"  3 stop rule: prefix ends {PREFIX[-40:]!r}, max_tokens 64   (1 call)")
        print(f"output: {OUT.relative_to(CODE.parent)}")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    ok = True
    for n, (cond, label) in enumerate((("user", "user hint"), (INJECTED, "inserted tool turn")), 1):
        rec = bf.one(it, cond, 0, experiment=EXPERIMENT)
        append(OUT, rec)
        checks = {"status_ok": rec["status"] == "ok", "split_at_think_close": rec["reasoning_field"] == "split_at_think_close",
                  "reasoning_present": bool(rec["reasoning_text"]),
                  "ended": rec["finish_reason"] in ("stop", "length")}
        if cond == INJECTED:
            checks["environment_turn_in_prompt"] = "<|im_start|>environment\n" in (rec["rendered_prompt"] or "")
            checks["rounds_recorded"] = bool(rec["tool_rounds"])
        ok &= all(checks.values())
        print(f"\n[{n}] {label}: finish {rec['finish_reason']}, answer {rec['parsed_letter']}"
              f" (hint {rec['cue_letter']}, correct {rec['correct_letter']}), {len(rec['reasoning_text'] or '')} reasoning "
              f"chars, {(rec['usage'] or {}).get('completion_tokens')} output tokens, {rec['latency_s']} s"
              + (f", tool rounds {len(rec['tool_rounds'])}, extra lookups by the model {rec['tool_calls_by_model']}"
                 if cond == INJECTED else ""))
        print(f"    final answer ends: {(rec['final_text'] or '')[-160:]!r}")
        print(f"    checks: {checks}")
    rec, checks = stop_rule_check(it)
    append(OUT, rec)
    ok &= all(checks.values())
    print(f"\n[3] stop rule: finish {rec['finish_reason']}, generated {(rec['final_text'] or '')[-80:]!r}")
    print(f"    parsed calls: {rec['calls_parsed']}")
    print(f"    next round ends: {json.dumps(rec['next_round_tail'][-230:])}")
    print(f"    checks: {checks}")
    print("\nALL CHECKS PASSED" if ok else "\nA CHECK FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
