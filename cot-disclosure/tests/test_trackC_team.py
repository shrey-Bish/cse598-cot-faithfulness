"""Track C's live team (agents/run_team.py) with a fake model: the tool and no-tool teams, two reviewer
models, append-only resumable logs, cases from Track B's steered_cases.jsonl, and the summary.
CPU only, no network."""
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from agents import run_team as rt  # noqa: E402
from common import append, load  # noqa: E402
from providers.base import Reply  # noqa: E402

REVIEWERS = [("voyager", "rev-a"), ("voyager", "rev-b")]


def fake_generate(calls, fail=None):
    """The solver follows a bad lookup (answers what the tool said) and is right otherwise; the checker
    (seed 3, 13, ...) answers the key; reviewers answer FINAL: <the proposed letter>."""
    def generate(provider, model, messages, tools=None, tool_choice=None, **kw):
        calls.append((model, kw.get("seed"), bool(tools)))
        if fail and fail(model, messages):
            return Reply(provider=provider, model=model, error="connection reset", finish_reason="error")
        if tools and tool_choice:
            return Reply(provider=provider, model=model, tool_calls=[{"id": "c1", "name": "lookup_answer_key",
                                                                       "arguments": "{}"}], finish_reason="tool_calls")
        user = messages[-1]["content"]
        if messages[-1]["role"] == "tool":
            letter = json.loads(user)["expected"]
            return Reply(provider=provider, model=model, final_text=f"Answer: ({letter})", reasoning_text="r",
                         reasoning_visibility="full", usage={"input_tokens": 10, "output_tokens": 5})
        if model.startswith("rev"):
            proposed = user.split("Proposed answer: (")[1][0]
            return Reply(provider=provider, model=model, final_text=f"FINAL: {proposed}", usage={"input_tokens": 3, "output_tokens": 1})
        return Reply(provider=provider, model=model, final_text="Answer: (A)", reasoning_text="r", reasoning_visibility="full",
                     usage={"input_tokens": 10, "output_tokens": 5})
    return generate


def items():
    return [{"item_id": f"q{i}", "question": f"Q{i}?\n(A) a\n(B) b", "correct": "A", "hint_letter": "B", "n_options": 2,
             "source": "test"} for i in range(4)]


def test_both_teams_two_reviewers_and_resume(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(rt, "generate", fake_generate(calls))
    path = tmp_path / "team_live.jsonl"
    ok = rt.live(items(), ["tool", "notool"], 2, REVIEWERS, path, "t", workers=2, check_models=False)
    assert all(ok) and len(ok) == 4 * 2 * 2
    assert len(calls) == sum(rt.calls_per_case(t, REVIEWERS) for _, t, _ in rt.plan_cases(items(), ["tool", "notool"], 2))
    rows = load(path)
    nt = [r for r in rows if r["agent"] == "reviewer" and r["team"] == "notool"]
    assert {r["variant"] for r in nt} == {"answer_only", "plus_explanation", "plus_private"}
    assert {r["reviewer_model"] for r in rows if r["agent"] == "reviewer"} == {"rev-a", "rev-b"}
    n = len(calls)
    rt.live(items(), ["tool", "notool"], 2, REVIEWERS, path, "t", workers=2, check_models=False)
    assert len(calls) == n and len(load(path)) == len(rows)                       # done cases are not rerun


def test_a_failed_case_is_rerun_and_only_its_complete_attempt_counts(tmp_path, monkeypatch):
    calls = []
    first = {"n": 0}

    def fail(model, messages):
        if model == "rev-b" and messages[-1]["content"].startswith("Q1?") and first["n"] == 0:
            first["n"] += 1
            return True
        return False
    monkeypatch.setattr(rt, "generate", fake_generate(calls, fail))
    path = tmp_path / "team_live.jsonl"
    ok = rt.live(items(), ["notool"], 1, REVIEWERS, path, "t", workers=1, check_models=False)
    assert ok.count(False) == 1
    ok = rt.live(items(), ["notool"], 1, REVIEWERS, path, "t", workers=1, check_models=False)
    assert ok == [True]
    reviews, checks = rt.live_rows(path)
    assert len(reviews) == 4 * 2 * 3 and len(checks) == 4 and len({r["attempt"] for r in reviews if r["item_id"] == "q1"}) == 1


def test_summary_splits_lookups_and_gives_the_checker_floor(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(rt, "generate", fake_generate(calls))
    path = tmp_path / "team_live.jsonl"
    its = [{**it, "item_id": f"pilot-{i}"} for i, it in enumerate(items() * 3)][:12]
    rt.live(its, ["tool", "notool"], 1, REVIEWERS[:1], path, "t", workers=4, check_models=False)
    reviews, checks = rt.live_rows(path)
    s = rt.summarize(reviews)
    tool = s["tool | rev-a | answer_only"]
    oracle = rt.solver.ToolOracle(wrong_rate=0.5)
    n_bad = sum(oracle.is_bad(it["item_id"]) for it in its)
    assert tool["bad_lookups"]["reviews"] == n_bad and tool["good_lookups"]["reviews"] == 12 - n_bad
    assert tool["bad_lookups"]["caught"]["k"] == n_bad                   # the checker (no tool) disagrees: escalated
    assert tool["good_lookups"]["false_alarms"]["k"] == 0
    alone = tool["bad_lookups"]["reviewer_alone"]                      # the fake reviewer repeats the proposal
    assert alone["corrects_wrong_solver"]["k"] == 0 and alone["corrects_wrong_solver"]["n"] == n_bad
    assert tool["good_lookups"]["reviewer_alone"]["keeps_right_solver"]["k"] == 12 - n_bad
    rates = rt.checker_rates(checks)
    assert rates["notool"]["k"] == 0 and rates["notool"]["n"] == 12 and rates["tool, bad lookup"]["k"] == n_bad


def test_items_from_track_b_cases(tmp_path):
    p = tmp_path / "steered_cases.jsonl"
    for i in range(6):
        append(p, {"case_id": f"m|q{i}", "kind": ["steered", "matched", "other"][i % 3], "item_id": f"q{i}",
                   "question": f"Q{i}", "correct_letter": "A", "hint_letter": "C", "n_options": 4})
    its = rt.case_items(p, ["steered", "matched"], 1)
    assert [it["kind"] for it in its] == ["steered", "matched"] and its[0]["hint_letter"] == "C"
    assert len(rt.case_items(p, ["steered", "matched"], 0)) == 4
