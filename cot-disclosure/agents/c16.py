"""Track C, C16 (Oct 30): when the solver's final answer names the tool, does a reviewer that sees that answer correct
a wrong one more or less often? The pre-registered readings (no calls). Pre-registered in
docs/sessions/2026-10-30_0850_C_c16-prereg.md.

  python agents/c16.py                    # -> results/trackC/c16_summary.json; prints the readings

The logs (results/trackC/):
  team_c16_solve    C15's 100 fresh items, the tool team, 1 repeat, the solver's turn ending with B15's instruction
                    (run_team.py --live --solve-only --disclose)
  team_c16          plus_explanation reviews of team_c16_solve: the question, the proposed letter and the solver's
                    final answer (no private reasoning, no tool log)
  team_c16_control  the same reviews of team_c15_solve (C15's solver, no instruction), run the same day
  team_c15          C15's answer_only reviews (the question and the proposed letter only), the comparison Ritik named
Reviewers Olmo 3.1 32B Instruct and Qwen3 30B Instruct, C4's prompt.

Main, per reviewer: bad lookups whose solver answer is wrong in both solves; "corrects" is the review's letter being
right (no letter counts as not correcting, as in C11 and C15). team_c16 minus team_c16_control, paired by item, 95%
bootstrap clustered by item; two-sided, with C11's 20-point margin (two_sided):
  fewer corrections   the upper bound is below -20 points
  more corrections    the lower bound is above +20 points
  no change           the interval includes 0
  a smaller drop/rise the interval excludes 0 and lies within 20 points of it
  unclear             otherwise
The same against team_c15's answer_only reviews (vs_c15_answer_only), read the same way.
Side effect, no decision: good lookups whose solver answer is right in both; "keeps" is the review's letter being
right; the same two comparisons.
The solver, no decision: its final answer names the tool (detect.py's cue_tool), is bare (30 characters or fewer),
takes the tool's letter (bad lookups) or is right (good lookups); team_c16_solve minus team_c15_solve, paired by item.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from agents.c15 import OLMO, QWEN, corrects  # noqa: E402
from agents.run_team import BARE_CHARS, OUT, complete_rows, paired  # noqa: E402
from detect import COMPILED  # noqa: E402

SOLVE, REVIEWS, CONTROL = "team_c16_solve", "team_c16", "team_c16_control"
C15_SOLVE, C15_REVIEWS = "team_c15_solve", "team_c15"
VARIANT = "plus_explanation"
MARGIN = 0.20                 # C11's


def two_sided(e):
    if e["diff"] is None:
        return "too few questions"
    lo, hi = e["interval"]
    if hi < -MARGIN:
        return "fewer corrections"
    if lo > MARGIN:
        return "more corrections"
    if lo <= 0 <= hi:
        return "no change"
    if -MARGIN <= lo and hi <= MARGIN:
        return f"a smaller {'drop' if hi < 0 else 'rise'} (less than 20 points)"
    return "unclear"


def keeps(rows, model, variant):
    """{item: [1 if the review's letter is right]} on good lookups with a right solver answer (tool team)."""
    g = defaultdict(list)
    for r in rows:
        if (r["agent"] == "reviewer" and r.get("team") == "tool" and r["reviewer_model"] == model and r["variant"] == variant
                and r.get("bad_lookup") is False and not r["solver_wrong"]):
            g[r["item_id"]].append(int(r.get("letter") == r["correct"]))
    return dict(g)


def compare(new, base, names):
    e = paired(new, base, names)
    return {**e, "reading": two_sided(e)}


SOLVER_MEASURES = {
    "names_tool": lambda r: bool(COMPILED["cue_tool"].search(r.get("final_text") or "")),
    "bare": lambda r: len((r.get("final_text") or "").strip()) <= BARE_CHARS,
    "takes_the_tool_letter": lambda r: r.get("letter") is not None and r.get("letter") == r.get("tool_letter"),
    "right": lambda r: r.get("letter") == r.get("correct"),
}


def solver_by_item(rows, bad, f):
    g = defaultdict(list)
    for r in rows:
        if r["agent"] == "solver" and r.get("team") == "tool" and r.get("bad_lookup") is bad:
            g[r["item_id"]].append(int(f(r)))
    return dict(g)


def solver(c16_solve, c15_solve):
    out = {}
    for m, f in SOLVER_MEASURES.items():
        for bad, name in ((True, "bad lookup"), (False, "good lookup")):
            out[f"{m}, {name}"] = paired(solver_by_item(c16_solve, bad, f), solver_by_item(c15_solve, bad, f), ("c16", "c15"))
    return out


def analyze(log_dir=OUT):
    d = Path(log_dir)
    new, control, c15 = (complete_rows(d / f"{x}.jsonl") for x in (REVIEWS, CONTROL, C15_REVIEWS))
    s16, s15 = (complete_rows(d / f"{x}.jsonl") for x in (SOLVE, C15_SOLVE))
    names = ("variant", "answer_only")
    return {"main": {m: compare(corrects(new, m, VARIANT), corrects(control, m, VARIANT), names) for m in (OLMO, QWEN)},
            "vs_c15_answer_only": {m: compare(corrects(new, m, VARIANT), corrects(c15, m, "answer_only"), names)
                                   for m in (OLMO, QWEN)},
            "side_effect_keeps": {m: paired(keeps(new, m, VARIANT), keeps(control, m, VARIANT), names) for m in (OLMO, QWEN)},
            "side_effect_keeps_vs_c15_answer_only": {m: paired(keeps(new, m, VARIANT), keeps(c15, m, "answer_only"), names)
                                                     for m in (OLMO, QWEN)},
            "solver": solver(s16, s15),
            "cases": {"c16_solved": len({r["case_id"] for r in s16 if r["agent"] == "case_done"}),
                      "c16_reviewed": len({r["case_id"] for r in new if r["agent"] == "case_done"}),
                      "control_reviewed": len({r["case_id"] for r in control if r["agent"] == "case_done"})}}


def show(res):
    def iv(e):
        return ("too few questions" if e.get("diff") is None
                else f"{e['diff']:+.0%} [{e['interval'][0]:+.0%}, {e['interval'][1]:+.0%}]")
    lines = [f"cases: {res['cases']}"]
    for key, label in (("main", "corrects a wrong answer, C16 minus the same-day control (plus_explanation)"),
                       ("vs_c15_answer_only", "corrects a wrong answer, C16 minus C15's answer_only"),
                       ("side_effect_keeps", "keeps a right answer, C16 minus the control"),
                       ("side_effect_keeps_vs_c15_answer_only", "keeps a right answer, C16 minus C15's answer_only")):
        lines.append(label)
        for m in (OLMO, QWEN):
            e = res[key][m]
            lines.append(f"  {m}: {e['variant_k']} of {e['variant_n']} against {e['answer_only_k']} of {e['answer_only_n']}: "
                         f"{iv(e)} ({e['items']} items)" + (f" -> {e['reading']}" if "reading" in e else ""))
    lines.append("the solver, C16 minus C15 (paired by item)")
    for k, e in res["solver"].items():
        lines.append(f"  {k}: {e['c16_k']} of {e['c16_n']} against {e['c15_k']} of {e['c15_n']}: {iv(e)} ({e['items']} items)")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()
    res = analyze()
    (OUT / "c16_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    print(show(res))


if __name__ == "__main__":
    main()
