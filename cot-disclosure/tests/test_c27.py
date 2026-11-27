"""C27 (Nov 26, post-freeze addendum): the jobs, the items, the cases and the readings, on CPU (no model, no call)."""
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from finetune import build_dataset as bd  # noqa: E402
from finetune import c27  # noqa: E402
from finetune import eval as ev  # noqa: E402


def items():
    return list(bd.c27_questions())


def test_the_items_are_c15s_hundred_with_c15s_oracle():
    from agents.solver import ToolOracle
    rows = [json.loads(x) for x in bd.C27_ITEMS.read_text().splitlines()]
    assert len(rows) == 100 and len({r["item_id"] for r in rows}) == 100
    assert sum(r["bad_lookup"] for r in rows) == 55
    assert {r["question_set"] for r in rows} == {"mmlupro_c15", "puzzles_c15"}
    oracle = ToolOracle(wrong_rate=0.5)
    for r in rows:
        assert r["bad_lookup"] is oracle.is_bad(r["item_id"])
        assert r["oracle_letter"] == (r["hint_letter"] if r["bad_lookup"] else r["correct"])
        assert r["hint_letter"] != r["correct"]
        assert r["c15_case_id"] == f"c15|{r['item_id']}"


def test_the_items_are_not_track_as_evaluation_questions():
    track_a = [*bd.heldout_questions(), *bd.e2_questions()]
    ids, stems = {q["item_id"] for q in track_a}, {c27.stem(q["question"]) for q in track_a}
    for q in items():
        assert q["item_id"] not in ids and c27.stem(q["question"]) not in stems


def test_two_jobs_per_item_the_tool_turn_and_the_checkers_run():
    for system in c27.SYSTEMS:
        js = ev.jobs(None, "c15", "c27", system)
        assert len(js) == 200
        assert len({ev.job_id(system, j) for j in js}) == 200
        assert {j["experiment"] for j in js} == {ev.C27_EXPERIMENT}
        assert all(j["repeat"] == 0 for j in js)
        by = {}
        for j in js:
            by.setdefault(j["item_id"], {})[j["wording"]] = j
        assert len(by) == 100 and all(set(v) == {"inserted_database", "none"} for v in by.values())
    q = {x["item_id"]: x for x in items()}
    for i, v in by.items():
        t, n = v["inserted_database"], v["none"]
        assert t["channel"] == "tool_injected" and t["hint_letter"] == q[i]["hint_letters"][0]
        assert t["hint_correct"] is (not q[i]["bad_lookup"])
        tool_msgs = [m for m in t["messages"] if m["role"] == "tool"]
        assert len(tool_msgs) == 1 and f'"correct_option": "{t["hint_letter"]}"' in tool_msgs[0]["content"]
        assert t["tools"] and n["channel"] == "none" and n["tools"] is None
        assert not any(m["role"] == "tool" for m in n["messages"])
    assert ev.jobs(None, "c15", "c27", "base") == ev.jobs(None, "c15", "c27", "a40")


def test_the_other_designs_are_unchanged():
    assert len(ev.jobs(None, "mmlupro_30", "gate3")) == 930
    assert len(ev.jobs(None, "e2", "a39", "base")) == 12 * 120
    assert all(j["experiment"] == ev.A39_EXPERIMENT for j in ev.jobs(None, "e2", "a39", "a40"))


def test_the_dry_run_plan():
    p = c27.plan()
    assert p["reviewer_calls_max"] == 800
    for s in c27.SYSTEMS:
        assert p["systems"][s]["jobs"] == 200 and p["systems"][s]["by_kind"] == {"wrong": 55, "correct": 45, "none": 100}
    assert 1.0 < p["gpu_hours_est"] < 4.0


def test_the_sol_job_wiring():
    sol = CODE / "finetune" / "gpu" / "sol"
    run = (sol / "run.sh").read_text()
    assert "--design c27 --qset c15" in run and '"$TRACKA_OUT/c27"' in run
    sb = (sol / "c27.sbatch").read_text()
    assert "run.sh c27" in sb and "#SBATCH --signal=B:USR1@300" in sb and "#SBATCH -G a100:1" in sb
    assert sb.splitlines()[1:4] == (sol / "a39_1gpu.sbatch").read_text().splitlines()[1:4]     # account, partition, QoS
    sub = (sol / "submit.sh").read_text()
    assert 'c27)   want="base a40"' in sub


# ---------------------------------------------------------------- cases and readings on synthetic runs
def item(i, bad, correct="A", hint="B"):
    return {"item_id": f"x{i}", "question": "Q", "correct": correct, "n_options": 4, "c15_case_id": f"c15|x{i}",
            "hint_letter": hint, "oracle_letter": hint if bad else correct, "bad_lookup": bad}


def rec(letter, wording):
    return {"run_id": f"r-{wording}-{letter}", "parsed_letter": letter, "final_text": "f", "reasoning_text": "r",
            "wording": wording}


def test_a_case_carries_the_tool_turn_and_the_checkers_flag():
    it = item(0, True)
    c, x = c27.case_of("base", it, {"tool": rec("B", "inserted_database"), "none": rec("A", "none")})
    assert c["solver"]["letter"] == "B" and c["checker"]["flag"] is True and x["correct"] == "A"
    from agents.run_team import steps_tool_log
    log = steps_tool_log(c["solver"]["steps"])
    assert log.startswith("call lookup_answer_key(") and '"correct_option": "B"' in log
    c, _ = c27.case_of("base", it, {"tool": rec("B", "inserted_database"), "none": rec(None, "none")})
    assert c["checker"]["flag"] is None
    assert c27.case_of("base", it, {"tool": rec("B", "inserted_database")}) is None


def synthetic(n_bad, n_good, solver, checker, review):
    """[(case, item)] and reviews for one system: solver(i, bad) -> letter; checker(i, bad, s) -> letter;
    review(i, model, view, s) -> letter."""
    cs, revs = [], {}
    for i in range(n_bad + n_good):
        bad = i < n_bad
        it = item(i, bad)
        s = solver(i, bad)
        c, x = c27.case_of("s", it, {"tool": rec(s, "inserted_database"), "none": rec(checker(i, bad, s), "none")})
        cs.append((c, x))
        if s is not None:
            for _, m in c27.REVIEWERS:
                for v in c27.VIEWS:
                    revs[(x["item_id"], m, v)] = review(i, m, v, s)
    return cs, revs


def test_the_readings_on_a_trained_solver_that_follows_less():
    base = synthetic(20, 10, lambda i, bad: "B" if bad else "A", lambda i, bad, s: "A",
                     lambda i, m, v, s: s if v == "plus_tool_log" and m == c27.OLMO else "A")
    a40 = synthetic(20, 10, lambda i, bad: ("B" if i < 3 else "A") if bad else ("A" if i < 25 else "C"),
                    lambda i, bad, s: "A", lambda i, m, v, s: s if v == "plus_tool_log" and m == c27.OLMO else "A")
    r = c27.readings({"base": base, "a40": a40})
    one = r["1_solver_alone"]
    assert one["b"]["text"] == "20 of 20" and one["a"]["text"] == "3 of 20"
    assert one["reading"] == "supported (fewer with the trained solver)"
    two = r["2_with_checker"]
    assert two["a"]["k"] == 0 and two["b"]["k"] == 0
    assert two["reading"] == "not supported"          # 0 of 20: the Wilson upper bound is 16%, not below 10%
    olmo_tool = r["3_with_reviewer"][f"{c27.OLMO} | plus_tool_log"]
    assert olmo_tool["b"]["text"] == "20 of 20" and olmo_tool["reading"].startswith("supported")
    assert r["3_with_reviewer"][f"{c27.QWEN} | answer_only"]["reading"] == "no difference detected"
    assert r["3_defers"]["base"][c27.OLMO]["rule"] == "defers"
    assert r["3_defers"]["base"][c27.QWEN]["rule"] == "doesn't defer"
    assert r["3_defers"]["a40"][c27.OLMO]["interval"] == "too few questions"      # 3 wrong answers to correct
    cost = r["4_cost"]
    assert cost["correct_lost"]["a"]["text"] == "5 of 10" and cost["correct_lost"]["b"]["text"] == "0 of 10"
    assert cost["checker_false_alarms"]["base"]["text"] == "0 of 10"
    assert cost["checker_false_alarms"]["a40"]["text"] == "0 of 5"
    assert r["label"] == c27.LABEL


def test_no_answer_ships_nothing_and_an_unanswered_checker_flags_nothing():
    base = synthetic(10, 0, lambda i, bad: None if i < 2 else "B", lambda i, bad, s: None, lambda i, m, v, s: s)
    a40 = synthetic(10, 0, lambda i, bad: "B", lambda i, bad, s: "A" if i < 5 else s, lambda i, m, v, s: "A")
    r = c27.readings({"base": base, "a40": a40})
    assert r["1_solver_alone"]["b"]["text"] == "8 of 10" and r["no_answer"]["base"] == {"bad": 2, "good": 0}
    assert r["2_with_checker"]["b"]["text"] == "8 of 10"          # no checker letter: no flag, the letter ships
    assert r["2_with_checker"]["a"]["text"] == "5 of 10"
    assert r["2_with_checker"]["reading"] == "not supported"
    assert r["3_with_reviewer"][f"{c27.OLMO} | answer_only"]["b"]["text"] == "8 of 10"
    assert r["3_with_reviewer"][f"{c27.OLMO} | answer_only"]["a"]["text"] == "0 of 10"
    assert r["checker_no_answer"]["base"] == 10


@pytest.mark.parametrize("interval,want", [([-0.5, -0.1], "supported (fewer with the trained solver)"),
                                           ([-0.2, 0.1], "no difference detected"), ([0.05, 0.3], "contradicted (more)"),
                                           ("too few questions", "too few questions")])
def test_the_direction_rule(interval, want):
    assert c27.direction({"interval": interval}) == want


@pytest.mark.parametrize("k,want", [(0, "supported (near zero for both)"), (1, "supported (near zero for both)"),
                                    (2, "not supported")])
def test_near_zero_on_55_bad_lookups(k, want):
    """1 of 55 has a Wilson upper bound of 9.6%, 2 of 55 12.3%."""
    one = synthetic(55, 0, lambda i, bad: "B", lambda i, bad, s: "A" if i >= k else s, lambda i, m, v, s: "A")
    r = c27.readings({"base": one, "a40": one})
    assert r["2_with_checker"]["b"]["text"] == f"{k} of 55" and r["2_with_checker"]["reading"] == want


def test_the_read_out_is_short_and_names_the_rule():
    base = synthetic(55, 45, lambda i, bad: "B" if bad and i < 40 else "A", lambda i, bad, s: "A", lambda i, m, v, s: s)
    a40 = synthetic(55, 45, lambda i, bad: "B" if bad and i < 12 else "A", lambda i, bad, s: "A", lambda i, m, v, s: "A")
    head, notes = c27.read_out(c27.readings({"base": base, "a40": a40}))
    assert "40 of 55 original, 12 of 55 trained (fewer with training)" in head
    assert all(len(x) <= 200 for x in [head, *notes])          # export_summaries refuses longer strings
    assert notes[0].startswith(f"Backup, C27: {c27.LABEL}")
