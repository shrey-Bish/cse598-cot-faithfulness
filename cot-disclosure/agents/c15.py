"""Track C, C15: the pre-registered readings on fresh items (no calls), from the reviews (team_c15) and the solver
and checker log (team_c15_solve). Pre-registered in docs/sessions/2026-10-29_2300_ALL_c14-c15-b15-prereg.md.

  python agents/c15.py                    # -> results/trackC/c15_summary.json; prints the readings

Bad lookups whose solver answer is wrong are where a reviewer can correct; "corrects" is the reviewer's letter being
right (no letter counts as not correcting, as in C11).
(a) F18 on fresh items: per reviewer, plus_tool_log minus answer_only on correcting, paired by item, and C11's rule:
    defers (upper bound below -20 points), doesn't defer (the interval includes 0 or lies above -20), unclear
    otherwise. Replicates: the Olmo 3.1 32B reviewer defers and the Qwen3 30B Instruct one doesn't; partly: one of
    the two; doesn't replicate: neither.
(b) H23: restoration = plus_tool_log_redacted minus plus_tool_log on correcting, in two groups fixed by the same
    reviewer's answer_only review of the case (it corrects / it doesn't). The groups' difference in restoration,
    with a bootstrap that resamples items within each group. Supported: the interval lies above 0; not supported:
    it includes 0; contradicted: it lies below 0; a group with fewer than 5 items: too few questions. The main
    reading is the Olmo 3.1 32B reviewer's (the one that defers); Qwen3 30B Instruct's is reported beside it.
(c) C14's rule, frozen (agents/disagreement.py RULE: answer_only against plus_tool_log of the same reviewer), against
    the checker's pipeline with plus_tool_log (a flag escalates, otherwise that review's letter ships), paired by item:
    (c1) Olmo 3.1 32B: the rule's false alarms (good lookups, solver right) minus the checker's pipeline. Confirmed:
         the interval lies above 0 (C14: +12 [+1, +24]); not confirmed: it includes 0; refuted: below 0.
    (c2) Qwen3 30B Instruct: the rule matches the checker's pipeline within 10 points. Confirmed: caught minus the
         checker's pipeline has a lower bound above -10 and false alarms minus the checker's pipeline an upper bound
         below +10 (C14: +0 [+0, +0], +1 [-6, +8]); not confirmed otherwise.
    Also, no decision: escalated against the checker's flag, shipped wrong, the tokens per case.
Also reported, no decision: the checker against the no-tool team's floor (C5) and the solver's final answers after a
tool call (F15's bare letter), from the solve log; by set (MMLU-Pro, puzzles) for (a) and (b).
"""
import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from agents import disagreement as dg  # noqa: E402
from agents.run_team import OUT, complete_rows, floor_comparison, paired, checker_rates, solver_replies  # noqa: E402
from common import MIN_QUESTIONS, load  # noqa: E402

OLMO, QWEN = "olmo3-32b-instruct", "qwen3-30b-a3b-instruct-2507"
REVIEW_LOG, SOLVE_LOG = "team_c15", "team_c15_solve"
CASES = CODE / "results" / "trackC" / "c15_items.jsonl"
DEFERS_BELOW = -0.20          # C11's rule
MARGIN = 0.10                 # (c2)


def c11_rule(e):
    if e["diff"] is None:
        return "too few questions"
    lo, hi = e["interval"]
    if hi < DEFERS_BELOW:
        return "defers"
    if lo <= 0 <= hi or lo > DEFERS_BELOW:
        return "doesn't defer"
    return "unclear"


def corrects(rows, model, variant, sets=None, want=None):
    """{item: [1 if the review's letter is right]} on bad lookups with a wrong solver answer (tool team)."""
    g = defaultdict(list)
    for r in rows:
        if (r["agent"] == "reviewer" and r.get("team") == "tool" and r["reviewer_model"] == model and r["variant"] == variant
                and r.get("bad_lookup") is True and r["solver_wrong"] and (want is None or sets.get(r.get("source")) == want)):
            g[r["item_id"]].append(int(r.get("letter") == r["correct"]))
    return dict(g)


def replication(rows, sets):
    out = {}
    for model in (OLMO, QWEN):
        base = corrects(rows, model, "answer_only")
        e = paired(corrects(rows, model, "plus_tool_log"), base)
        out[model] = {**e, "rule": c11_rule(e)}
        for s in sorted(set(sets.values())):
            sub = paired(corrects(rows, model, "plus_tool_log", sets, s), corrects(rows, model, "answer_only", sets, s))
            out[model].setdefault("by_set", {})[s] = {**sub, "rule": c11_rule(sub)}
    a, b = out[OLMO]["rule"], out[QWEN]["rule"]
    hits = (a == "defers") + (b == "doesn't defer")
    out["reading"] = {2: "replicates", 1: "partly", 0: "doesn't replicate"}[hits]
    return out


def stratified_diff(g1, g2, n=20000, seed=0):
    """mean(g1) - mean(g2), each {item: [values]}, items resampled within each group. (diff, low, high)."""
    def mean(g, qs):
        vals = [x for q in qs for x in g[q]]
        return sum(vals) / len(vals) if vals else None
    q1, q2 = sorted(g1, key=str), sorted(g2, key=str)
    rng = random.Random(seed)
    vals = []
    for _ in range(n):
        a, b = mean(g1, [rng.choice(q1) for _ in q1]), mean(g2, [rng.choice(q2) for _ in q2])
        if a is not None and b is not None:
            vals.append(a - b)
    vals.sort()
    return mean(g1, q1) - mean(g2, q2), vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]


def h23(rows, model, sets=None, want=None):
    """Restoration (redacted minus unredacted, correcting) in the groups the answer_only review fixes."""
    by = defaultdict(dict)                       # case_id -> variant -> row
    for r in rows:
        if (r["agent"] == "reviewer" and r.get("team") == "tool" and r["reviewer_model"] == model
                and r.get("bad_lookup") is True and r["solver_wrong"] and (want is None or sets.get(r.get("source")) == want)):
            by[r["case_id"]][r["variant"]] = r
    groups = {"answer_only_corrects": defaultdict(list), "answer_only_doesnt": defaultdict(list)}
    raw = {k: {"redacted": 0, "unredacted": 0, "cases": 0} for k in groups}
    for v in by.values():
        if not all(x in v for x in ("answer_only", "plus_tool_log", "plus_tool_log_redacted")):
            continue
        key = "answer_only_corrects" if v["answer_only"].get("letter") == v["answer_only"]["correct"] else "answer_only_doesnt"
        red = int(v["plus_tool_log_redacted"].get("letter") == v["plus_tool_log_redacted"]["correct"])
        unred = int(v["plus_tool_log"].get("letter") == v["plus_tool_log"]["correct"])
        groups[key][v["answer_only"]["item_id"]].append(red - unred)
        raw[key]["redacted"] += red
        raw[key]["unredacted"] += unred
        raw[key]["cases"] += 1
    out = {"groups": {}}
    for k, g in groups.items():
        vals = [x for xs in g.values() for x in xs]
        out["groups"][k] = {**raw[k], "items": len(g), "restoration": sum(vals) / len(vals) if vals else None}
    g1, g2 = groups["answer_only_corrects"], groups["answer_only_doesnt"]
    if len(g1) < MIN_QUESTIONS or len(g2) < MIN_QUESTIONS:
        out.update(diff=None, interval="too few questions", reading="too few questions")
        return out
    d, lo, hi = stratified_diff(dict(g1), dict(g2))
    out.update(diff=d, interval=[lo, hi], reading="supported" if lo > 0 else "contradicted" if hi < 0 else "not supported")
    return out


def frozen_rule(rows, solve_rows, sets):
    tokens = dg.case_tokens(solve_rows)
    out = {"rule": dg.RULE}
    for model in (OLMO, QWEN):
        b = {c: r for (m, c), r in dg.reviews(rows, "answer_only").items() if m == model}
        s = {c: r for (m, c), r in dg.reviews(rows, "plus_tool_log").items() if m == model}
        sr = {c: r for (m, c), r in dg.reviews(rows, "plus_tool_log_redacted").items() if m == model}
        out[model] = {"plus_tool_log": dg.evaluate(b, s, tokens, sets), "plus_tool_log_redacted": dg.evaluate(b, sr, tokens, sets)}
    fa = out[OLMO]["plus_tool_log"]["good_lookups"]["false_alarms_minus_checker_pipeline"]
    out["c1_olmo_more_false_alarms"] = ("too few questions" if fa["diff"] is None else
                                        "confirmed" if fa["interval"][0] > 0 else "refuted" if fa["interval"][1] < 0
                                        else "not confirmed")
    q = out[QWEN]["plus_tool_log"]
    c, f = q["bad_lookups"]["caught_minus_checker_pipeline"], q["good_lookups"]["false_alarms_minus_checker_pipeline"]
    out["c2_qwen_matches_checker"] = ("too few questions" if c["diff"] is None or f["diff"] is None else
                                      "confirmed" if c["interval"][0] > -MARGIN and f["interval"][1] < MARGIN
                                      else "not confirmed")
    return out


def analyze(log_dir=OUT, cases=CASES):
    rows = complete_rows(Path(log_dir) / f"{REVIEW_LOG}.jsonl")
    solve = complete_rows(Path(log_dir) / f"{SOLVE_LOG}.jsonl")
    sets = {r["case_id"]: r["set"] for r in load(cases)}
    checks = [r for r in solve if r["agent"] == "checker"]
    solvers = [r for r in solve if r["agent"] == "solver"]
    return {"a_replication": replication(rows, sets),
            "b_h23": {m: {**h23(rows, m), "by_set": {s: h23(rows, m, sets, s) for s in sorted(set(sets.values()))}}
                      for m in (OLMO, QWEN)},
            "c_frozen_rule": frozen_rule(rows, solve, sets),
            "checker_flag_rate": checker_rates(checks), "c5_checker_vs_floor": floor_comparison(checks, solvers),
            "solver_replies": solver_replies(solvers),
            "cases": {"reviewed": len({r["case_id"] for r in rows if r["agent"] == "case_done"}),
                      "solved": len({r["case_id"] for r in solve if r["agent"] == "case_done"})}}


def show(res):
    def iv(e):
        return ("too few questions" if e.get("diff") is None
                else f"{e['diff']:+.0%} [{e['interval'][0]:+.0%}, {e['interval'][1]:+.0%}]")
    a = res["a_replication"]
    lines = [f"(a) F18 on fresh items: {a['reading']}"]
    for m in (OLMO, QWEN):
        e = a[m]
        lines.append(f"  {m}: plus_tool_log {e['variant_k']} of {e['variant_n']}, answer_only {e['answer_only_k']} of "
                     f"{e['answer_only_n']}: {iv(e)} ({e['items']} items) -> {e['rule']}")
    lines.append("(b) H23")
    for m in (OLMO, QWEN):
        e = res["b_h23"][m]
        g = e["groups"]
        lines.append(f"  {m}: restoration when answer_only corrects {g['answer_only_corrects']['restoration']} "
                     f"({g['answer_only_corrects']['items']} items), when it doesn't {g['answer_only_doesnt']['restoration']} "
                     f"({g['answer_only_doesnt']['items']} items); difference {iv(e)} -> {e['reading']}")
    c = res["c_frozen_rule"]
    lines.append(f"(c) frozen rule: (c1) Olmo more false alarms than the checker: {c['c1_olmo_more_false_alarms']}; "
                 f"(c2) Qwen matches the checker within 10 points: {c['c2_qwen_matches_checker']}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()
    res = analyze()
    (OUT / "c15_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    print(show(res))


if __name__ == "__main__":
    main()
