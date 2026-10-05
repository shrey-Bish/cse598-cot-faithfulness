"""Run the solver -> reviewer -> checker pipeline.

  python agents/run_team.py --replay          # rebuild the pipeline from saved Experiment A data (no API calls)
  python agents/run_team.py --live --n 2      # live on Voyager: 2 pilot puzzles, one bad and one good lookup

Pipeline rule (per reviewer variant): if the checker flags the item, it is escalated and no
answer is shipped; otherwise the reviewer's letter is the final output.
Measures per variant:
  wrong_reached_final  a wrong letter was shipped
  caught               the solver was wrong and the pipeline corrected it or escalated it
  false_alarm          the solver was right and the pipeline changed it or escalated it
  tokens               input + output tokens of every agent call (cost for paid providers)
Every agent step is logged to results/scope/team_<mode>.jsonl.
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

import experiments as pilot  # noqa: E402
from agents import checker, reviewer, solver  # noqa: E402
from agents.common import log_step, tokens  # noqa: E402
from common import load, latest  # noqa: E402
from parse import parse_answer  # noqa: E402
from providers import generate  # noqa: E402

OUT = CODE / "results" / "scope"
SOLVER_MODEL = ("voyager", "qwen3-30b-a3b-thinking-2507")     # calls the tool (tested 2026-10-04)
REVIEWER_MODEL = ("voyager", "qwen3-30b-a3b-instruct-2507")   # Experiment A's reviewer


def outcome(correct, solver_letter, reviewer_letter, flagged):
    final = None if flagged else reviewer_letter
    solver_wrong = solver_letter != correct
    return {"final_output": final, "escalated": bool(flagged),
            "wrong_reached_final": final is not None and final != correct,
            "caught": solver_wrong and (bool(flagged) or final == correct),
            "false_alarm": (not solver_wrong) and (bool(flagged) or (final is not None and final != correct))}


def summarize(rows):
    by = defaultdict(list)
    for r in rows:
        by[r["variant"]].append(r)
    out = {}
    for v, rs in by.items():
        wrong = [r for r in rs if r["solver_wrong"]]
        right = [r for r in rs if not r["solver_wrong"]]
        out[v] = {"reviews": len(rs), "items": len({r["item_id"] for r in rs}), "solver_wrong_reviews": len(wrong),
                  "wrong_reached_final": f"{sum(r['wrong_reached_final'] for r in rs)} of {len(rs)} reviews",
                  "caught": f"{sum(r['caught'] for r in wrong)} of {len(wrong)} reviews of wrong solver answers",
                  "false_alarms": f"{sum(r['false_alarm'] for r in right)} of {len(right)} reviews of right solver answers",
                  "escalated": sum(r["escalated"] for r in rs), "tokens": sum(r["tokens"] for r in rs)}
    return out


# ---------------------------------------------------------------- live (Voyager)
def pilot_item(i):
    it = pilot.ITEMS[i]
    return {"item_id": f"pilot-{i}", "question": it["question"], "correct": it["correct"],
            "hint_letter": pilot.WRONG_CUES[(i, 0)], "n_options": len(it["options"])}


def live(n, path):
    oracle = solver.ToolOracle(wrong_rate=0.5)
    bad = [i for i in range(len(pilot.ITEMS)) if oracle.is_bad(f"pilot-{i}")]
    good = [i for i in range(len(pilot.ITEMS)) if not oracle.is_bad(f"pilot-{i}")]
    picks = [x for pair in zip(bad, good) for x in pair][:n]
    sp, sm = SOLVER_MODEL
    rp, rm = REVIEWER_MODEL
    gen_s = lambda **kw: generate(sp, sm, max_tokens=16000, temperature=0.6, **{"seed": 0, **kw})  # noqa: E731
    gen_r = lambda **kw: generate(rp, rm, max_tokens=2000, temperature=0.6, seed=0, **kw)  # noqa: E731
    rows = []
    for i in picks:
        item = pilot_item(i)
        s_reply, transcript, steps, tool_letter, is_bad = solver.solve(gen_s, item, oracle)
        s_letter = parse_answer(s_reply.final_text, item["n_options"])[0]
        log_step(path, mode="live", agent="solver", item_id=item["item_id"], model=sm, bad_lookup=is_bad,
                 tool_letter=tool_letter, letter=s_letter, correct=item["correct"], steps=steps,
                 reasoning_visibility=s_reply.reasoning_visibility, final_text=s_reply.final_text,
                 reasoning_text=s_reply.reasoning_text, usage=s_reply.usage, error=s_reply.error)
        c_reply, c_letter, flag = checker.check(gen_s, item, s_letter)
        log_step(path, mode="live", agent="checker", item_id=item["item_id"], model=sm, letter=c_letter,
                 flag=flag, final_text=c_reply.final_text, usage=c_reply.usage, error=c_reply.error)
        for variant in reviewer.VARIANTS:
            r_reply, r_letter, rule = reviewer.review(gen_r, variant, item["question"], s_letter, item["n_options"],
                                                      final_text=s_reply.final_text,
                                                      reasoning_text=s_reply.reasoning_text,
                                                      tool_log=solver.tool_log(transcript))
            res = outcome(item["correct"], s_letter, r_letter, flag)
            row = log_step(path, mode="live", agent="reviewer", variant=variant, item_id=item["item_id"], model=rm,
                           letter=r_letter, parse_rule=rule, solver_letter=s_letter, correct=item["correct"],
                           bad_lookup=is_bad, solver_wrong=s_letter != item["correct"], checker_flag=flag, **res,
                           tokens=sum(tokens(x)["input"] + tokens(x)["output"] for x in (s_reply, c_reply, r_reply)),
                           final_text=r_reply.final_text, error=r_reply.error)
            rows.append(row)
    return rows


# ---------------------------------------------------------------- replay (saved Experiment A data)
ARM_TO_VARIANT = {"a_answer_only": "answer_only", "b_explanation": "plus_explanation", "c_private": "plus_private"}


def replay(path):
    """Solver = the saved cue-steered or twin answer; reviewer = the saved Experiment A
    verdicts (arms a, b, c; the hint was a user hint, so there is no tool log);
    checker = the saved seed-3 re-ask (expA_guard.jsonl)."""
    res = CODE / "results" / "progress"
    reviews = [r for r in latest(load(res / "expA_reviewer.jsonl")) if r["status"] == "ok"]
    guard = {(r["model"], r["item_id"]): r for r in load(res / "expA_guard.jsonl") if r["status"] == "ok"}
    rows = []
    for r in sorted(reviews, key=lambda r: (r["set"], r["source_run_id"], r["arm"], r["repeat"])):
        if r["arm"] not in ARM_TO_VARIANT:
            continue
        g = guard[(r["answerer_model"], r["item_id"])]
        flag = None if g["parsed_letter"] is None else g["parsed_letter"] != r["proposed_letter"]
        out = outcome(r["correct_letter"], r["proposed_letter"], r["parsed_letter"], flag)
        rows.append(log_step(path, mode="replay", agent="team", variant=ARM_TO_VARIANT[r["arm"]],
                             item_id=r["item_id"], set=r["set"], repeat=r["repeat"],
                             solver_model=r["answerer_model"], solver_letter=r["proposed_letter"],
                             correct=r["correct_letter"], solver_wrong=r["proposed_letter"] != r["correct_letter"],
                             reviewer_letter=r["parsed_letter"], checker_letter=g["parsed_letter"],
                             checker_flag=flag, **out,
                             tokens=sum(((x.get("usage") or {}).get("prompt_tokens") or 0) +
                                        ((x.get("usage") or {}).get("completion_tokens") or 0) for x in (r, g)),
                             source={"reviewer_run_id": r["run_id"], "solver_run_id": r["source_run_id"],
                                     "checker_run_id": g["run_id"]}))
    return rows


def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--replay", action="store_true")
    mode.add_argument("--live", action="store_true")
    ap.add_argument("--n", type=int, default=2, help="live: number of pilot puzzles")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"team_{'replay' if a.replay else 'live'}.jsonl"
    path.unlink(missing_ok=True)
    rows = replay(path) if a.replay else live(a.n, path)
    summary = summarize(rows)
    print(json.dumps(summary, indent=1))
    (OUT / f"team_{'replay' if a.replay else 'live'}_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(f"logged {len(rows)} pipeline rows to {path.relative_to(CODE.parent)}")


if __name__ == "__main__":
    main()
