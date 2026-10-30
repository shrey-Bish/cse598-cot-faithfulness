"""C14 (two reviews that disagree, on saved logs), C15's fresh items, the solve-only first phase and C15's readings.
CPU only, no network."""
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from agents import c15, disagreement as dg, fresh_items as fi, run_team as rt  # noqa: E402
from common import load  # noqa: E402
from finetune.make_pool import stem  # noqa: E402
from providers.base import Reply  # noqa: E402


def review(case, item, letter, correct="A", solver="B", bad=True, flag=True, model="m", variant="answer_only", **kw):
    res = rt.outcome(correct, solver, letter, flag)
    return {"agent": "reviewer", "team": "tool", "case_id": case, "item_id": item, "reviewer_model": model, "variant": variant,
            "letter": letter, "correct": correct, "solver_letter": solver, "solver_wrong": solver != correct,
            "bad_lookup": bad, "checker_flag": flag, "mode": "rereview", "tokens": 10, "source": f"src|{item}", **res, **kw}


def test_the_rule_escalates_on_different_or_missing_letters():
    assert dg.escalates("A", "B") and dg.escalates(None, "A") and dg.escalates("A", None)
    assert not dg.escalates("C", "C")


def test_evaluate_counts_the_rule_and_the_checkers_pipeline():
    blind, seeing = {}, {}
    for i in range(6):                    # bad lookups, solver wrong (B); the blind review corrects, the other defers
        blind[f"b{i}"] = review(f"b{i}", f"q{i}", "A")
        seeing[f"b{i}"] = review(f"b{i}", f"q{i}", "B", variant="plus_tool_log", flag=i < 5)
    for i in range(6):                    # good lookups, solver right (A); the blind review is wrong once
        blind[f"g{i}"] = review(f"g{i}", f"p{i}", "C" if i == 0 else "A", solver="A", bad=False, flag=False)
        seeing[f"g{i}"] = review(f"g{i}", f"p{i}", "A", solver="A", bad=False, flag=False, variant="plus_tool_log")
    tokens = {f"{k}{i}": {"checker": 100, "solver_and_checker": 150} for k in "bg" for i in range(6)}
    e = dg.evaluate(blind, seeing, tokens)
    bad, good = e["bad_lookups"], e["good_lookups"]
    assert bad["escalated"]["k"] == 6 and bad["caught"]["k"] == 6 and bad["shipped_wrong"]["k"] == 0
    assert bad["checker_flagged"]["k"] == 5 and bad["checker_pipeline_caught"]["k"] == 5
    assert bad["caught_minus_checker_pipeline"]["diff"] == pytest.approx(1 / 6)
    assert good["escalated"]["k"] == 1 and good["false_alarms"]["k"] == 1 and good["checker_pipeline_false_alarms"]["k"] == 0
    assert e["cost_tokens_per_case"] == {"added_answer_only_review": 10, "trace_seeing_review": 10, "checker_reask": 100}


def test_a_live_rows_own_tokens_leave_out_the_solver_and_checker():
    row = {"mode": "live", "case_id": "c", "tokens": 1000}
    assert dg.own_tokens(row, {"c": {"solver_and_checker": 800}}) == 200
    assert dg.own_tokens({**row, "mode": "rereview"}, {}) == 1000


# ---------------------------------------------------------------- C15's fresh items
def fake_mmlu():
    rows = []
    for c in ("biology", "math", "law"):                      # law is an evaluation category
        for k in range(20):
            qid = {"biology": 0, "math": 100, "law": 200}[c] + k
            rows.append({"question_id": qid, "category": c, "question": f"{c} question {k}?",
                         "options": [f"o{j}" for j in range(10)], "answer": "ABCDEFGHIJ"[k % 10], "src": "x"})
    rows.append({"question_id": 999, "category": "math", "question": "math question 3?", "options": [f"o{j}" for j in range(10)],
                 "answer": "A", "src": "x"})                  # the same text as a pool question, another id
    return rows


def test_fresh_items_leave_out_evaluation_categories_the_pool_and_pilot_puzzles(monkeypatch):
    pool = [{"item_id": "mmlupro-3", "question_set": "mmlupro_train", "question": "math question 3?\n(A) o0"},
            {"item_id": "mmlupro-1", "question_set": "mmlupro_train", "question": "biology question 1?\n(A) o0"}]
    monkeypatch.setattr(fi, "N_MMLU", 10)
    rows = fi.mmlu(n=10, ds=fake_mmlu(), pool=pool)
    assert len(rows) == 10 and {r["source"]["category"] for r in rows} == {"biology", "math"}
    ids = {r["item_id"] for r in rows}
    assert "mmlupro-3" not in ids and "mmlupro-1" not in ids and "mmlupro-999" not in ids
    assert all(r["hint_letter"] != r["correct_letter"] and r["kind"] == "fresh" and r["case_id"] == f"c15|{r['item_id']}"
               for r in rows)
    assert rows == fi.mmlu(n=10, ds=fake_mmlu(), pool=pool)        # seeded


def test_fresh_puzzles_are_new_and_cycle_over_the_levels():
    rows = fi.puzzles(n=12, pool=[])
    assert len(rows) == 12 and len({r["item_id"] for r in rows}) == 12
    assert len({str(r["source"]["level"]) for r in rows}) == 11
    pilot_stems = {stem(it["question"]) for it in fi.pilot.ITEMS}
    assert not any(stem(r["question"]) in pilot_stems for r in rows)
    first = rows[0]
    assert fi.puzzles(n=12, pool=[{"question_set": "fresh_puzzles_hard", "question": first["question"]}])[0]["item_id"] != first["item_id"]


# ---------------------------------------------------------------- the solve-only phase, then the reviews
def fake_generate(calls):
    def generate(provider, model, messages, tools=None, tool_choice=None, **kw):
        calls.append(model)
        if tools and tool_choice:
            return Reply(provider=provider, model=model, tool_calls=[{"id": "c1", "name": "lookup_answer_key",
                                                                       "arguments": "{}"}], finish_reason="tool_calls")
        user = messages[-1]["content"]
        if messages[-1]["role"] == "tool":
            return Reply(provider=provider, model=model, final_text=f"Answer: ({json.loads(user)['expected']})",
                         reasoning_text="the key says (B)", reasoning_visibility="full", usage={"input_tokens": 10, "output_tokens": 5})
        if model == "olmo3-32b-instruct":                     # defers to a tool log that shows the letter
            proposed = user.split("Proposed answer: (")[1][0]
            letter = proposed if f'"expected": "{proposed}"' in user else "A"
            return Reply(provider=provider, model=model, final_text=f"FINAL: {letter}", usage={"input_tokens": 3, "output_tokens": 1})
        if model == "qwen3-30b-a3b-instruct-2507":
            return Reply(provider=provider, model=model, final_text="FINAL: A", usage={"input_tokens": 3, "output_tokens": 1})
        return Reply(provider=provider, model=model, final_text="Answer: (A)", reasoning_text="r", reasoning_visibility="full",
                     usage={"input_tokens": 10, "output_tokens": 5})
    return generate


def test_solve_only_then_rereview_gives_c15s_readings(tmp_path, monkeypatch):
    cases = tmp_path / "c15_items.jsonl"
    rows = [{"case_id": f"c15|q{i}", "kind": "fresh", "set": "mmlupro_c15" if i % 2 else "puzzles_c15", "item_id": f"q{i}",
             "question": f"Q{i}?\n(A) a\n(B) b", "n_options": 2, "correct_letter": "A", "hint_letter": "B"} for i in range(30)]
    cases.write_text("".join(json.dumps(r) + "\n" for r in rows))
    calls = []
    monkeypatch.setattr(rt, "generate", fake_generate(calls))
    solve = tmp_path / "team_c15_solve.jsonl"
    items = rt.case_items(cases, ["fresh"], 0)
    assert rt.live(items, ["tool", "notool"], 1, [], solve, "t", workers=2, check_models=False) == 0
    assert {r["agent"] for r in load(solve)} == {"solver", "checker", "case_done"}
    saved = rt.saved_cases(solve, rt.items_by_source(cases))
    assert len(saved) == 30
    reviewers = [("voyager", c15.OLMO), ("voyager", c15.QWEN)]
    log = tmp_path / "team_c15.jsonl"
    assert rt.rereview(saved, reviewers, ["answer_only", "plus_tool_log", "plus_tool_log_redacted"], log, "t", "team_c15_solve",
                       workers=2, check_models=False, system_extra=None) == 0
    res = c15.analyze(log_dir=tmp_path, cases=cases)
    bad = sum(rt.solver.ToolOracle().is_bad(f"q{i}") for i in range(30))
    olmo = res["a_replication"][c15.OLMO]
    assert olmo["answer_only_k"] == bad and olmo["variant_k"] == 0 and olmo["rule"] == "defers"
    assert res["a_replication"][c15.QWEN]["rule"] == "doesn't defer" and res["a_replication"]["reading"] == "replicates"
    h = res["b_h23"][c15.OLMO]                       # the redacted log hides "expected": the fake corrects every case
    assert h["groups"]["answer_only_corrects"]["restoration"] == 1 and h["reading"] == "too few questions"
    assert res["c_frozen_rule"]["c2_qwen_matches_checker"] in ("confirmed", "not confirmed")
    assert res["cases"] == {"reviewed": 30, "solved": 60}


def test_c11_rule_and_h23_readings():
    assert c15.c11_rule({"diff": -0.5, "interval": [-0.6, -0.3]}) == "defers"
    assert c15.c11_rule({"diff": -0.05, "interval": [-0.15, 0.05]}) == "doesn't defer"
    assert c15.c11_rule({"diff": -0.25, "interval": [-0.35, -0.10]}) == "unclear"
    assert c15.c11_rule({"diff": None, "interval": "too few questions"}) == "too few questions"
    rows = []
    for i in range(12):                   # answer_only corrects on q0-q5 (restoration 1), not on q6-q11 (restoration 0)
        good = i < 6
        rows += [review(f"c{i}", f"q{i}", "A" if good else "C", model=c15.OLMO),
                 review(f"c{i}", f"q{i}", "B", model=c15.OLMO, variant="plus_tool_log"),
                 review(f"c{i}", f"q{i}", "A" if good else "B", model=c15.OLMO, variant="plus_tool_log_redacted")]
    h = c15.h23(rows, c15.OLMO)
    assert h["groups"]["answer_only_corrects"]["items"] == 6 and h["groups"]["answer_only_doesnt"]["items"] == 6
    assert h["diff"] == 1 and h["reading"] == "supported"
