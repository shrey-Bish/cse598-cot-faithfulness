"""Track C, C14 (exploratory, Oct 29): two reviews that disagree as the escalation signal, on the saved
C4 and C9-C12 logs (no calls).

  python agents/disagreement.py --cases results/trackB/steered_cases.jsonl           # -> results/trackC/c14_disagreement.json
  python agents/disagreement.py --cases results/trackB/steered_cases.jsonl --table   # and markdown tables

The rule (RULE): on a tool-team case, escalate when a reviewer that never saw the tool (answer_only) and the
same reviewer model shown the solver's trace (its private reasoning or its tool log) give different letters, or
either gives none; otherwise ship the letter both gave. The no-letter part is fixed here: a review that can't
confirm is treated as a disagreement.

Per reviewer model and pairing (PAIRINGS: which saved reviews stand for the two), on C4's 159 tool-team cases
(75 bad lookups, 84 good; 53 items, 3 repeats):
  escalated        bad and good lookups (the signal, as the checker's flag)
  caught           the solver's wrong answers (bad lookups) that are escalated or replaced by the right letter
  shipped wrong    bad-lookup cases that ship a wrong letter
  false alarms     the solver's right answers (good lookups) that are escalated or replaced by a wrong letter
  vs the checker   escalated minus the checker's flag on the same cases (a flag of None, no answer, doesn't
                   escalate, as in the pipeline); and caught / false alarms minus the checker's pipeline with the
                   same trace-seeing reviewer (C4's rule: a flag escalates, otherwise that reviewer's letter ships).
                   Paired by item: 95% bootstrap clustered by item
  cost             per case, the tokens of the rule's added call (the answer_only review, when a pipeline already
                   runs the reviewer that sees the trace) and of the trace-seeing review, against the checker's
                   re-ask (C4's checker rows)
  by set           escalated on bad and good lookups per question set (puzzles, MMLU-Pro)
Exploratory: the rule and the pairings are looked at on these cases, so nothing here is a confirmed finding;
C15 (fresh items, pre-registered) confirms or refutes the frozen rule.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from agents.run_team import OUT, complete_rows  # noqa: E402
from common import boot_diff, load, too_few, wilson  # noqa: E402

RULE = ("escalate when the answer_only review and the same reviewer model's trace-seeing review give different "
        "letters, or either gives none; otherwise ship their common letter")
# (name, blind (log, variant), trace-seeing (log, variant)); C10's first turn is C9's answer_only review
PAIRINGS = [
    ("C4: + private reasoning", ("team_c4", "answer_only"), ("team_c4", "plus_private")),
    ("C4: + tool log", ("team_c4", "answer_only"), ("team_c4", "plus_tool_log")),
    ("C9 (warning): + private reasoning", ("team_c9", "answer_only"), ("team_c9", "plus_private")),
    ("C9 (warning): + tool log", ("team_c9", "answer_only"), ("team_c9", "plus_tool_log")),
    ("C10 (commit first): + private reasoning", ("team_c9", "answer_only"), ("team_c10", "plus_private")),
    ("C10 (commit first): + tool log", ("team_c9", "answer_only"), ("team_c10", "plus_tool_log")),
    ("C11: + private reasoning", ("team_c11", "answer_only"), ("team_c11", "plus_private")),
    ("C11: + tool log", ("team_c11", "answer_only"), ("team_c11", "plus_tool_log")),
    ("C12: + private reasoning, redacted", ("team_c4", "answer_only"), ("team_c12", "plus_private_redacted")),
    ("C12: + tool log, redacted", ("team_c4", "answer_only"), ("team_c12", "plus_tool_log_redacted")),
]
CHECKER_LOG = "team_c4"           # the solver, checker and their tokens for every saved case


def escalates(blind, seeing):
    """RULE: True when the two letters differ or either is missing."""
    return blind is None or seeing is None or blind != seeing


def count(xs):
    k, n = sum(bool(x) for x in xs), len(xs)
    return {"k": k, "n": n, "wilson": wilson(k, n)}


def own_tokens(row, case_tokens):
    """A review's own tokens: C4's live rows add the solver's final reply and the checker's (run_case); a
    rereview row holds the review's alone."""
    if row.get("mode") == "live":
        return row["tokens"] - case_tokens.get(row["case_id"], {}).get("solver_and_checker", 0)
    return row["tokens"]


def case_tokens(rows):
    """{case_id: {checker, solver_and_checker}} from a live log's solver and checker rows."""
    out = defaultdict(dict)
    for r in rows:
        if r["agent"] in ("solver", "checker"):
            u = r.get("usage") or {}
            out[r["case_id"]][r["agent"]] = (u.get("input_tokens") or 0) + (u.get("output_tokens") or 0)
    return {k: {"checker": v.get("checker", 0), "solver_and_checker": v.get("solver", 0) + v.get("checker", 0)}
            for k, v in out.items()}


def reviews(rows, variant):
    """{(reviewer model, case_id): row} of the tool team's reviews of one variant."""
    return {(r["reviewer_model"], r["case_id"]): r for r in rows
            if r["agent"] == "reviewer" and r.get("team") == "tool" and r["variant"] == variant}


def paired_minus(a, b):
    """a minus b by item (both {item: [0/1]}), the bootstrap clustered by item; too few items: no interval."""
    both = sorted(set(a) & set(b))
    if too_few({q: a[q] for q in both}):
        return {"diff": None, "interval": "too few questions", "items": len(both)}
    d, lo, hi = boot_diff({q: a[q] for q in both}, {q: b[q] for q in both})
    return {"diff": d, "interval": [lo, hi], "items": len(both)}


def evaluate(blind, seeing, tokens, sets=None):
    """One pairing for one reviewer model: blind and seeing are {case_id: review row} (same cases)."""
    cases = sorted(set(blind) & set(seeing))
    out = {"cases": len(cases), "items": len({seeing[c]["item_id"] for c in cases})}
    for side, bad in (("bad_lookups", True), ("good_lookups", False)):
        rows = [(blind[c], seeing[c]) for c in cases if seeing[c].get("bad_lookup") is bad]
        esc, flag = defaultdict(list), defaultdict(list)
        rule, chk = defaultdict(list), defaultdict(list)       # caught (bad) or false alarm (good), by item
        shipped_wrong, chk_shipped_wrong, missing = [], [], 0
        for b, s in rows:
            e = escalates(b["letter"], s["letter"])
            missing += b["letter"] is None or s["letter"] is None
            ship = None if e else s["letter"]
            esc[s["item_id"]].append(int(e))
            flag[s["item_id"]].append(int(s.get("checker_flag") is True))
            if bad and s["solver_wrong"]:
                rule[s["item_id"]].append(int(e or ship == s["correct"]))
                chk[s["item_id"]].append(int(s["caught"]))
                shipped_wrong.append(ship is not None and ship != s["correct"])
                chk_shipped_wrong.append(s["wrong_reached_final"])
            elif not bad and not s["solver_wrong"]:
                rule[s["item_id"]].append(int(e or (ship is not None and ship != s["correct"])))
                chk[s["item_id"]].append(int(s["false_alarm"]))
        entry = {"cases": len(rows), "items": len(esc), "escalated": count([x for v in esc.values() for x in v]),
                 "no_letter": missing, "checker_flagged": count([x for v in flag.values() for x in v]),
                 "escalated_minus_checker": paired_minus(dict(esc), dict(flag))}
        name = "caught" if bad else "false_alarms"
        # the checker's pipeline with the same trace-seeing reviewer (C4's rule: a flag escalates, otherwise the
        # reviewer's letter ships): the rows' own outcome
        entry.update({name: count([x for v in rule.values() for x in v]),
                      f"checker_pipeline_{name}": count([x for v in chk.values() for x in v]),
                      f"{name}_minus_checker_pipeline": paired_minus(dict(rule), dict(chk))})
        if bad:
            entry.update(shipped_wrong=count(shipped_wrong), checker_pipeline_shipped_wrong=count(chk_shipped_wrong))
        if sets:
            by = defaultdict(list)
            for b, s in rows:
                by[sets.get(s.get("source"), "unknown")].append(escalates(b["letter"], s["letter"]))
            entry["escalated_by_set"] = {k: count(v) for k, v in sorted(by.items())}
        out[side] = entry

    def mean(xs):
        return round(sum(xs) / len(xs)) if xs else None
    out["cost_tokens_per_case"] = {
        "added_answer_only_review": mean([own_tokens(blind[c], tokens) for c in cases]),
        "trace_seeing_review": mean([own_tokens(seeing[c], tokens) for c in cases]),
        "checker_reask": mean([tokens[c]["checker"] for c in cases if c in tokens])}
    out["cost_calls_per_case"] = {"rule": "1 added (answer_only), or 2 if no reviewer runs yet",
                                  "checker": "1 (the solver model without the tool)"}
    return out


def analyze(log_dir=OUT, cases_path=None, pairings=PAIRINGS):
    logs = {}

    def rows_of(name):
        if name not in logs:
            logs[name] = complete_rows(Path(log_dir) / f"{name}.jsonl")
        return logs[name]
    tokens = case_tokens(rows_of(CHECKER_LOG))
    sets = {r["case_id"]: r["set"] for r in load(cases_path)} if cases_path else None
    out = {"rule": RULE, "exploratory": True, "checker_log": CHECKER_LOG, "pairings": {}}
    for name, (blog, bvar), (slog, svar) in pairings:
        b, s = reviews(rows_of(blog), bvar), reviews(rows_of(slog), svar)
        for model in sorted({m for m, _ in s} & {m for m, _ in b}):
            bm = {c: r for (m, c), r in b.items() if m == model}
            sm = {c: r for (m, c), r in s.items() if m == model}
            out["pairings"][f"{name} | {model}"] = {"pairing": name, "reviewer": model, "blind": f"{blog} {bvar}",
                                                     "seeing": f"{slog} {svar}", **evaluate(bm, sm, tokens, sets)}
    return out


def table(res):
    def f(c):
        return "—" if not c or not c["n"] else f"{c['k']} of {c['n']} [{c['wilson'][0]:.0%}, {c['wilson'][1]:.0%}]"

    def d(x):
        return ("— too few questions" if x["diff"] is None
                else f"{x['diff']:+.0%} [{x['interval'][0]:+.0%}, {x['interval'][1]:+.0%}] ({x['items']} items)")
    out = [f"Rule: {res['rule']}. Exploratory.", "",
           "| pairing | reviewer | bad: escalated | escalated − checker's flag | caught | checker pipeline | caught − checker pipeline | "
           "shipped wrong (checker pipeline) | good: escalated | false alarms | checker pipeline | false alarms − checker pipeline | "
           "no letter (bad, good) | tokens: added review / trace review / checker |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in res["pairings"].values():
        bd, gd, t = e["bad_lookups"], e["good_lookups"], e["cost_tokens_per_case"]
        out.append(f"| {e['pairing']} | {e['reviewer']} | {f(bd['escalated'])} | {d(bd['escalated_minus_checker'])} | "
                   f"{f(bd['caught'])} | {f(bd['checker_pipeline_caught'])} | {d(bd['caught_minus_checker_pipeline'])} | "
                   f"{f(bd['shipped_wrong'])} ({f(bd['checker_pipeline_shipped_wrong'])}) | {f(gd['escalated'])} | "
                   f"{f(gd['false_alarms'])} | {f(gd['checker_pipeline_false_alarms'])} | {d(gd['false_alarms_minus_checker_pipeline'])} | "
                   f"{bd['no_letter']}, {gd['no_letter']} | "
                   f"{t['added_answer_only_review']} / {t['trace_seeing_review']} / {t['checker_reask']} |")
    first = next(iter(res["pairings"].values()), None)
    if first:
        out += ["", f"Checker (C4's re-ask) on the same cases: bad lookups flagged {f(first['bad_lookups']['checker_flagged'])}, "
                    f"good lookups {f(first['good_lookups']['checker_flagged'])}."]
    if first and "escalated_by_set" in first["bad_lookups"]:
        out += ["", "| pairing | reviewer | set | bad: escalated | good: escalated |", "|---|---|---|---|---|"]
        for e in res["pairings"].values():
            for s in e["bad_lookups"]["escalated_by_set"]:
                out.append(f"| {e['pairing']} | {e['reviewer']} | {s} | {f(e['bad_lookups']['escalated_by_set'][s])} | "
                           f"{f(e['good_lookups'].get('escalated_by_set', {}).get(s))} |")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cases", help="Track B's steered_cases.jsonl: split escalations by question set")
    ap.add_argument("--table", action="store_true")
    a = ap.parse_args()
    res = analyze(cases_path=a.cases)
    (OUT / "c14_disagreement.json").write_text(json.dumps(res, indent=1) + "\n")
    print(table(res) if a.table else json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
