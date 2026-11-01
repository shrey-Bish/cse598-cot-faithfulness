"""Track C, C20 (prepared Oct 31, reframed by Ritik: pipeline vs model): can the pipeline carry the source where the
model drops it? Four ways to check the solver's answer on C15's 100 fresh items (tool team, 55 bad and 45 good lookups),
each a pipeline with one check stage. The pre-registered readings (no calls). Pre-registered in
archive/sessions/2026-10-31/2026-10-31_2232_C_c20-prereg.md.

  python agents/c20.py                    # -> results/trackC/c20_summary.json; prints the table and the readings

The pipelines (the solver is C15's, team_c15_solve, except in (c)):
  (a) blind       the reviewer sees the question and the proposed letter, nothing from the solver's work, the tool or
                  the pipeline (C15's answer_only reviews, team_c15: the same call, saved)
  (b) tag         (a) plus the pipeline's provenance tag after the proposed letter, "[letter from tool
                  lookup_answer_key; unverified]", attached when that letter is the one the tool returned (the pipeline
                  reads it from the tool log; no solver prose): reviewer.answer_tagged, team_c20_tag (new: 200 reviews)
  (c) disclosure  the solver told to say what its answer is based on (C16's solve, team_c16_solve); the reviewer sees
                  the question, the letter and that final answer (C16's plus_explanation reviews, team_c16: saved)
  (d) checker     the solver model re-asked without the tool (C15's checker, team_c15_solve: saved); a flag escalates,
                  otherwise the solver's letter ships; no reviewer
Reviewers Olmo 3.1 32B Instruct and Qwen3 30B Instruct, C4's prompt (no added sentence). In (a)-(c) the reviewer's
letter ships (run_team.outcome with no checker flag); also reported, no decision, each as a flag: a reviewer letter
other than the solver's escalates, otherwise the solver's letter ships.
Per pipeline and reviewer: caught (the solver is wrong and the pipeline corrects or escalates), false alarms (the
solver is right and the pipeline changes or escalates), wrong answers shipped (of all cases), the check stage's tokens
per case; bad and good lookups apart.

Readings, per reviewer, paired by item, 95% bootstrap clustered by item:
  (1) main: (b) minus (a) on catches (cases with a wrong solver answer), c16.two_sided with C11's 20-point margin:
      more catches / fewer catches / no change / a smaller rise or drop / unclear. The tag works if "more catches" or
      "a smaller rise".
  (2) (b) minus (a) on false alarms (cases with a right solver answer): costs false alarms (the lower bound is above 0),
      fewer false alarms (the upper bound is below 0), no change otherwise.
  (3) (b) against (d): matches the checker if catches (b) minus (d) has a lower bound above -10 points and false alarms
      (b) minus (d) an upper bound below +10 (C15's (c2) margin); doesn't match otherwise.
  (4) pipeline vs model: (b) minus (c) on catches, items whose answer is wrong in both solves, c16.two_sided.
The main reading is the Olmo 3.1 32B reviewer's (the deferring family); Qwen3 30B Instruct's is read the same way.
Cross-day: (a), (c) and (d) were run Oct 29-30, (b) later; the same prompt and seed reproduced exactly on Voyager in
C18, so (a) is not rerun.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from agents.c15 import OLMO, QWEN  # noqa: E402
from agents.c16 import two_sided  # noqa: E402
from agents.run_team import OUT, complete_rows, outcome, paired  # noqa: E402
from common import boot_diff, too_few, wilson  # noqa: E402

PIPELINES = {"a_blind": ("team_c15", "answer_only"), "b_tag": ("team_c20_tag", "answer_tagged"),
             "c_disclosure": ("team_c16", "plus_explanation")}
SOLVE, C16_SOLVE = "team_c15_solve", "team_c16_solve"
CHECKER_MARGIN = 0.10          # (3), C15's (c2)
NAMES = ("variant", "answer_only")


def rows_of(log_dir, name):
    path = Path(log_dir) / f"{name}.jsonl"
    return complete_rows(path) if path.exists() else []


def reviewer_cases(rows, model, variant, rule="ship"):
    """[{item, bad, solver_wrong, caught, false_alarm, shipped_wrong, tokens}] for one reviewer's tool-team reviews.
    rule "ship": the reviewer's letter ships; "flag": a letter other than the solver's escalates."""
    out = []
    for r in rows:
        if not (r["agent"] == "reviewer" and r.get("team") == "tool" and r["reviewer_model"] == model
                and r["variant"] == variant):
            continue
        if rule == "ship":
            res = outcome(r["correct"], r["solver_letter"], r.get("letter"), False)
        else:
            flag = r.get("letter") is not None and r["letter"] != r["solver_letter"]
            res = outcome(r["correct"], r["solver_letter"], r["solver_letter"], flag)
        out.append({"item": r["item_id"], "bad": r.get("bad_lookup"), "solver_wrong": r["solver_wrong"],
                    "caught": res["caught"], "false_alarm": res["false_alarm"],
                    "shipped_wrong": res["wrong_reached_final"], "tokens": r.get("tokens") or 0})
    return out


def checker_cases(solve_rows):
    """The checker pipeline: a flag escalates, otherwise the solver's letter ships (tool team)."""
    by = defaultdict(dict)
    for r in solve_rows:
        if r.get("team") == "tool" and r["agent"] in ("solver", "checker"):
            by[r["case_id"]][r["agent"]] = r
    out = []
    for c in by.values():
        s, k = c["solver"], c["checker"]
        res = outcome(s["correct"], s["letter"], s["letter"], k["flag"])
        u = k.get("usage") or {}
        out.append({"item": s["item_id"], "bad": s.get("bad_lookup"), "solver_wrong": s["letter"] != s["correct"],
                    "caught": res["caught"], "false_alarm": res["false_alarm"], "shipped_wrong": res["wrong_reached_final"],
                    "tokens": (u.get("input_tokens") or 0) + (u.get("output_tokens") or 0)})
    return out


def by_item(cases, key, where):
    g = defaultdict(list)
    for c in cases:
        if where(c):
            g[c["item"]].append(int(c[key]))
    return dict(g)


def rate(cases, key, where=lambda c: True):
    sub = [c for c in cases if where(c)]
    k, n = sum(bool(c[key]) for c in sub), len(sub)
    return {"k": k, "n": n, "wilson": wilson(k, n) if n else None}


def block(cases):
    wrong, right = (lambda c: c["solver_wrong"]), (lambda c: not c["solver_wrong"])
    out = {"cases": len(cases), "caught": rate(cases, "caught", wrong), "false_alarms": rate(cases, "false_alarm", right),
           "shipped_wrong": rate(cases, "shipped_wrong"),
           "tokens_per_case": round(sum(c["tokens"] for c in cases) / len(cases), 1) if cases else None}
    for name, lookup in (("bad_lookups", True), ("good_lookups", False)):
        sub = [c for c in cases if c["bad"] is lookup]
        out[name] = {"cases": len(sub), "caught": rate(sub, "caught", wrong), "false_alarms": rate(sub, "false_alarm", right),
                     "shipped_wrong": rate(sub, "shipped_wrong")}
    return out


def relabel(reading):
    return reading.replace("corrections", "catches")


def diff(a, b):
    """a minus b on common items; None when too few."""
    both = set(a) & set(b)
    if not both or too_few({q: a[q] for q in both}):
        return {"diff": None, "interval": "too few questions", "items": len(both)}
    d, lo, hi = boot_diff({q: a[q] for q in both}, {q: b[q] for q in both})
    return {"diff": d, "interval": [lo, hi], "items": len(both)}


def false_alarm_reading(e):
    if e["diff"] is None:
        return "too few questions"
    lo, hi = e["interval"]
    return "costs false alarms" if lo > 0 else "fewer false alarms" if hi < 0 else "no change"


def matches_checker(catch, alarm):
    if catch["diff"] is None or alarm["diff"] is None:
        return "too few questions"
    ok = catch["interval"][0] > -CHECKER_MARGIN and alarm["interval"][1] < CHECKER_MARGIN
    return "matches the checker" if ok else "doesn't match the checker"


def analyze(log_dir=OUT):
    logs = {k: rows_of(log_dir, log) for k, (log, _) in PIPELINES.items()}
    checker = checker_cases(rows_of(log_dir, SOLVE))
    wrong, right = (lambda c: c["solver_wrong"]), (lambda c: not c["solver_wrong"])
    res = {"pipelines": {"d_checker": block(checker)}, "as_a_flag": {}, "readings": {}}
    for m in (OLMO, QWEN):
        cases = {k: reviewer_cases(logs[k], m, v) for k, (_, v) in PIPELINES.items()}
        for k, c in cases.items():
            res["pipelines"][f"{k} | {m}"] = block(c)
        for k in ("a_blind", "b_tag"):
            res["as_a_flag"][f"{k} | {m}"] = block(reviewer_cases(logs[k], m, PIPELINES[k][1], rule="flag"))
        catch = {k: by_item(c, "caught", wrong) for k, c in {**cases, "d_checker": checker}.items()}
        alarm = {k: by_item(c, "false_alarm", right) for k, c in {**cases, "d_checker": checker}.items()}
        main = paired(catch["b_tag"], catch["a_blind"], NAMES)
        fa = diff(alarm["b_tag"], alarm["a_blind"])
        vs_c, vs_a = diff(catch["b_tag"], catch["d_checker"]), diff(alarm["b_tag"], alarm["d_checker"])
        model = paired(catch["b_tag"], catch["c_disclosure"], NAMES)
        res["readings"][m] = {
            "1_tag_minus_blind_catches": {**main, "reading": relabel(two_sided(main))},
            "2_tag_minus_blind_false_alarms": {**fa, "reading": false_alarm_reading(fa)},
            "3_tag_vs_checker": {"catches": vs_c, "false_alarms": vs_a, "reading": matches_checker(vs_c, vs_a)},
            "4_tag_minus_disclosure_catches": {**model, "reading": relabel(two_sided(model))}}
    res["cases"] = {k: len({r["case_id"] for r in rows if r["agent"] == "case_done"}) for k, rows in logs.items()}
    return res


def show(res):
    def f(x):
        return "—" if not x or not x["n"] else f"{x['k']} of {x['n']} [{x['wilson'][0]:.0%}, {x['wilson'][1]:.0%}]"

    def iv(e):
        return ("too few questions" if e.get("diff") is None
                else f"{e['diff']:+.0%} [{e['interval'][0]:+.0%}, {e['interval'][1]:+.0%}]")
    def cells(k):
        name, _, model = k.partition(" | ")
        return f"{name} | {model or '—'}"
    lines = [f"cases: {res['cases']}", "| pipeline | reviewer | caught | false alarms | shipped wrong | tokens per case |",
             "|---|---|---|---|---|---|"]
    for k, b in res["pipelines"].items():
        lines.append(f"| {cells(k)} | {f(b['caught'])} | {f(b['false_alarms'])} | {f(b['shipped_wrong'])} | "
                     f"{b['tokens_per_case']} |")
    lines += ["", "as a flag (no decision)", "| pipeline | reviewer | caught | false alarms | shipped wrong |",
              "|---|---|---|---|---|"]
    for k, b in res["as_a_flag"].items():
        lines.append(f"| {cells(k)} | {f(b['caught'])} | {f(b['false_alarms'])} | {f(b['shipped_wrong'])} |")
    for m, r in res["readings"].items():
        lines.append(f"\n{m}")
        for k, e in r.items():
            if k.startswith("3"):
                lines.append(f"  {k}: catches {iv(e['catches'])}, false alarms {iv(e['false_alarms'])} -> {e['reading']}")
            else:
                lines.append(f"  {k}: {iv(e)} ({e['items']} items) -> {e['reading']}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()
    res = analyze()
    (OUT / "c20_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    print(show(res))


if __name__ == "__main__":
    main()
