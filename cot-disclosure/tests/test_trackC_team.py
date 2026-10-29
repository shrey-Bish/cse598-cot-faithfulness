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
    assert rt.live(items(), ["tool", "notool"], 2, REVIEWERS, path, "t", workers=2, check_models=False) == 0
    assert len(done_case_ids(path)) == 4 * 2 * 2
    assert len(calls) == sum(rt.calls_per_case(t, REVIEWERS) for _, t, _ in rt.plan_cases(items(), ["tool", "notool"], 2))
    rows = load(path)
    nt = [r for r in rows if r["agent"] == "reviewer" and r["team"] == "notool"]
    assert {r["variant"] for r in nt} == {"answer_only", "plus_explanation", "plus_private"}
    assert {r["reviewer_model"] for r in rows if r["agent"] == "reviewer"} == {"rev-a", "rev-b"}
    n = len(calls)
    rt.live(items(), ["tool", "notool"], 2, REVIEWERS, path, "t", workers=2, check_models=False)
    assert len(calls) == n and len(load(path)) == len(rows)                       # done cases are not rerun


def done_case_ids(path):
    return {r["case_id"] for r in load(path) if r.get("agent") == "case_done"}


def test_a_stop_file_starts_no_new_case(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(rt, "generate", fake_generate(calls))
    stop = tmp_path / "stop"
    stop.write_text("guard")
    assert rt.live(items(), ["tool"], 1, REVIEWERS, tmp_path / "log.jsonl", "t", workers=2, check_models=False,
                   stop_file=stop) == 2 and calls == []


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
    assert rt.live(items(), ["notool"], 1, REVIEWERS, path, "t", workers=1, check_models=False) == 1     # one left
    assert len(done_case_ids(path)) == 3
    assert rt.live(items(), ["notool"], 1, REVIEWERS, path, "t", workers=1, check_models=False) == 0
    assert len(done_case_ids(path)) == 4
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
    assert alone["keeps_wrong_solver"]["k"] == n_bad and alone["reply_names_tool"]["k"] == 0
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
    append(p, {"case_id": "n|q0", "kind": "steered", "item_id": "q0", "question": "Q0", "correct_letter": "A",
               "hint_letter": "B", "n_options": 4})
    try:                                          # a second model's export: the same item ids, so pick one
        rt.case_items(p, ["steered", "matched"], 0)
        raise AssertionError("mixed models accepted")
    except SystemExit as e:
        assert "--case-model" in str(e)
    assert [it["source"] for it in rt.case_items(p, ["steered"], 0, model="n")] == ["n|q0"]
    assert rt.case_items(p, ["steered", "matched"], 1, model="m") == its


def test_c5_compares_the_checker_with_the_no_tool_floor():
    """C5: the notool solver's own run-to-run variation, the checker's flag rate there (the floor), and the
    tool team's bad / good lookup flag rates minus the floor, paired by item."""
    items = [f"q{i}" for i in range(6)]
    checks, solvers = [], []
    for i, q in enumerate(items):
        for rep in range(3):
            checks.append({"team": "notool", "item_id": q, "repeat": rep, "flag": rep == 0 and i == 0})     # 1 of 18
            checks.append({"team": "tool", "bad_lookup": i < 3, "item_id": q, "repeat": rep, "flag": i < 3})
            solvers.append({"team": "notool", "item_id": q, "repeat": rep, "letter": "B" if (i == 1 and rep == 2) else "A"})
    c5 = rt.floor_comparison(checks, solvers)
    assert c5["run_to_run"]["rate"] == 2 / 18 and c5["run_to_run"]["items"] == 6        # q1: 2 of its 3 pairs differ
    assert abs(c5["floor"]["rate"] - 1 / 18) < 1e-9 and c5["floor"]["items"] == 6
    assert c5["bad_lookup"]["interval"] == "too few questions" and c5["bad_lookup"]["items"] == 3
    assert c5["bad_minus_floor"] == {"diff": None, "interval": "too few questions", "items": 3}
    many = checks + [{"team": "tool", "bad_lookup": True, "item_id": q, "repeat": 9, "flag": True} for q in items[3:]]
    d = rt.floor_comparison(many, solvers)["bad_minus_floor"]
    assert d["items"] == 6 and d["diff"] > 0.5 and d["interval"][0] > 0
    assert "| C5 | value |" in rt.table({"by_team_model_variant": {}, "checker_flag_rate": {}, "c5_checker_vs_floor": c5})


def test_the_reviewer_with_more_to_read_against_answer_only_paired_by_item():
    """Oct 28 (C4): the Olmo 32B reviewer corrected 59 of 73 wrong answers from the answer alone, 6 of 73
    with the private reasoning. Each variant minus answer only, on the same solver answers, by item."""
    rows = []
    for i in range(6):
        for rep in range(2):
            for v in ("answer_only", "plus_private", "plus_tool_log"):
                fixed = v == "answer_only" or (v == "plus_tool_log" and i == 0)
                rows.append({"team": "tool", "bad_lookup": True, "solver_wrong": True, "item_id": f"b{i}", "repeat": rep,
                             "reviewer_model": "rev-a", "variant": v, "correct": "A", "letter": "A" if fixed else "B"})
        rows.append({"team": "tool", "bad_lookup": True, "solver_wrong": False, "item_id": f"b{i}", "repeat": 9,
                     "reviewer_model": "rev-a", "variant": "plus_private", "correct": "A", "letter": "A"})  # ignored the tool
    for i in range(3):
        for v in ("answer_only", "plus_private"):
            rows.append({"team": "tool", "bad_lookup": False, "solver_wrong": False, "item_id": f"g{i}", "repeat": 0,
                         "reviewer_model": "rev-a", "variant": v, "correct": "A", "letter": None if v == "answer_only" else "A"})
    rows.append({"team": "notool", "bad_lookup": None, "solver_wrong": True, "item_id": "b0", "repeat": 0,
                 "reviewer_model": "rev-a", "variant": "plus_private", "correct": "A", "letter": "B"})
    rv = rt.reviewer_vs_answer_only(rows)
    p = rv["corrects_wrong_bad_lookups | rev-a | plus_private"]
    assert (p["variant_k"], p["variant_n"], p["answer_only_k"], p["answer_only_n"], p["items"]) == (0, 12, 12, 12, 6)
    assert p["diff"] == -1 and p["interval"] == [-1, -1]
    t = rv["corrects_wrong_bad_lookups | rev-a | plus_tool_log"]
    assert t["variant_k"] == 2 and abs(t["diff"] + 10 / 12) < 1e-9 and t["interval"][1] < 0
    k = rv["keeps_right_good_lookups | rev-a | plus_private"]          # no letter counts as not keeping
    assert (k["variant_k"], k["answer_only_k"], k["diff"], k["interval"]) == (3, 0, None, "too few questions")
    assert not any("answer_only" in key for key in rv)
    md = rt.table({"by_team_model_variant": {}, "checker_flag_rate": {}, "reviewer_vs_answer_only": rv})
    assert "| corrects a wrong answer (bad lookups) | rev-a | plus_private | 0 of 12 | 12 of 12 | -100% [-100%, -100%] | 6 |" in md
    assert "| keeps a right answer (good lookups) | rev-a | plus_private | 3 of 3 | 0 of 3 | — too few questions | 3 |" in md


def test_the_solvers_final_answer_after_good_and_bad_lookups():
    """Oct 28: is F15's bare letter about the wrong hint or about the tool call? Good lookups return the
    key: bare share, median length and naming the tool per arm; good - bad unpaired, each - notool paired."""
    solvers = []
    for i in range(12):
        bad = i < 6
        for rep in range(2):
            solvers.append({"team": "tool", "bad_lookup": bad, "item_id": f"q{i}", "repeat": rep,
                            "final_text": "\n\nAnswer: (B)" if (bad or rep == 0) else "The tool's answer key says (A). Answer: (A)"})
            solvers.append({"team": "notool", "bad_lookup": None, "item_id": f"q{i}", "repeat": rep,
                            "final_text": "Step 1 ... " * 10 + "Answer: (A)"})
    sr = rt.solver_replies(solvers)
    bad, good, notool = (sr["arms"][k] for k in ("tool, bad lookup", "tool, good lookup", "notool"))
    assert (bad["bare"]["k"], bad["bare"]["n"], bad["items"], bad["median_chars"]) == (12, 12, 6, len("Answer: (B)"))
    assert (good["bare"]["k"], good["names_tool"]["k"], notool["bare"]["k"], notool["items"]) == (6, 6, 0, 12)
    d = sr["differences"]
    assert d["bare: good minus bad lookup"]["diff"] == -0.5 and not d["bare: good minus bad lookup"]["paired"]
    assert d["bare: good minus bad lookup"]["items"] == 12 and d["bare: good minus bad lookup"]["interval"][1] < 0
    assert d["bare: bad lookup minus notool"] == {**d["bare: bad lookup minus notool"], "diff": 1.0, "items": 6, "paired": True}
    assert d["names_tool: good lookup minus notool"]["diff"] == 0.5
    few = rt.solver_replies([s for s in solvers if s["item_id"] in ("q0", "q1", "q6")])
    assert few["differences"]["bare: good minus bad lookup"]["interval"] == "too few questions"
    md = rt.table({"by_team_model_variant": {}, "checker_flag_rate": {}, "solver_replies": sr})
    assert "| tool, bad lookup | 6 | 12 of 12 [76%, 100%] | 11 | 0 of 12 [0%, 24%] |" in md
    assert "| bare: good minus bad lookup (unpaired) | -50%" in md


def test_summary_split_by_track_b_kind_and_set(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(rt, "generate", fake_generate(calls))
    cases = tmp_path / "steered_cases.jsonl"
    for i in range(8):
        append(cases, {"case_id": f"m|q{i}", "kind": "steered" if i < 4 else "matched", "set": "s1" if i % 2 else "s2",
                       "item_id": f"q{i}", "question": f"Q{i}?\n(A) a\n(B) b", "correct_letter": "A",
                       "hint_letter": "B", "n_options": 2})
    its = rt.case_items(cases, ["steered", "matched"], 0)
    path = tmp_path / "team_c4.jsonl"
    rt.live(its, ["tool", "notool"], 1, REVIEWERS[:1], path, "t", workers=4, check_models=False)
    res = rt.results(path, rt.case_groups(cases))
    assert sorted(res["by_kind"]) == ["matched", "steered"]
    assert sorted(res["by_kind_and_set"]) == ["matched | s1", "matched | s2", "steered | s1", "steered | s2"]
    whole = res["by_team_model_variant"]["notool | rev-a | answer_only"]["reviews"]
    parts = sum(v["by_team_model_variant"]["notool | rev-a | answer_only"]["reviews"] for v in res["by_kind"].values())
    assert whole == parts == 8
    assert "### steered | s1" in rt.table(res)


def test_the_tool_log_from_saved_steps_is_the_reviewers_tool_log():
    """C9 rebuilds the tool log from the solver row's steps (C4 didn't log the transcript): the same text
    run_case gave the reviewer, also with two calls in one turn."""
    from agents import solver

    def two_calls(messages, tools=None, tool_choice=None, **kw):
        if tool_choice:
            return Reply(provider="voyager", model="s", finish_reason="tool_calls", tool_calls=[
                {"id": "c1", "name": "lookup_answer_key", "arguments": '{"question_id": "q0"}'},
                {"id": "c2", "name": "other", "arguments": "{}"}])
        return Reply(provider="voyager", model="s", final_text="Answer: (B)")
    gen = fake_generate([])
    for g in (lambda **kw: gen("voyager", "s", **kw), two_calls):
        _, transcript, steps, _, _ = solver.solve(g, items()[0], solver.ToolOracle())
        assert rt.steps_tool_log(json.loads(json.dumps(steps))) == solver.tool_log(transcript) != ""
    assert solver.tool_log(transcript).count("result: ") == 2


def test_c9_reviews_c4s_saved_cases_again_with_the_sentence_and_pairs_with_the_original(tmp_path, monkeypatch):
    """Only the reviewers run again, on the tool team's saved cases, with CHECK_TOOL after the system
    prompt; the summary compares each reviewer x variant with the original prompt, paired by item."""
    calls, seen = [], []
    gen = fake_generate(calls)
    monkeypatch.setattr(rt, "generate", gen)
    monkeypatch.setattr(rt, "OUT", tmp_path)
    cases = tmp_path / "steered_cases.jsonl"
    for i in range(12):                                   # bad lookups on 6 of the 12 items (the seeded oracle)
        append(cases, {"case_id": f"m|q{i}", "kind": "steered" if i < 6 else "matched", "set": "s1" if i % 2 else "s2",
                       "item_id": f"q{i}", "question": f"Q{i}?\n(A) a\n(B) b", "correct_letter": "A",
                       "hint_letter": "B", "n_options": 2})
    c4 = tmp_path / "team_c4.jsonl"
    rt.live(rt.case_items(cases, ["steered", "matched"], 0), ["tool", "notool"], 2, REVIEWERS, c4, "c4", workers=4,
            check_models=False)
    n = len(calls)

    def told_to_check(provider, model, messages, **kw):   # rev-a checks the tool once told to; rev-b never does
        seen.append(messages)
        if model == "rev-a" and rt.CHECK_TOOL in messages[0]["content"]:
            calls.append((model, kw.get("seed"), False))
            return Reply(provider=provider, model=model, final_text="FINAL: A", usage={"input_tokens": 3, "output_tokens": 1})
        return gen(provider, model, messages, **kw)
    monkeypatch.setattr(rt, "generate", told_to_check)
    saved = rt.saved_cases(c4, rt.items_by_source(cases))
    assert len(saved) == 12 * 2 and {c["solver"]["team"] for c, _ in saved} == {"tool"}
    c9 = tmp_path / "team_c9.jsonl"
    assert rt.rereview(saved, REVIEWERS, rt.C9_VARIANTS, c9, "c9", "team_c4", workers=3, check_models=False) == 0
    assert len(calls) - n == 24 * 2 * 3 and not any(tools for _, _, tools in calls[n:])       # reviewers only
    assert all(m[0]["content"] == f"{rt.reviewer.SYSTEM} {rt.CHECK_TOOL}" for m in seen)
    logs = [m[1]["content"].split("Tool log of the first assistant:\n")[1] for m in seen if "Tool log" in m[1]["content"]]
    assert len(logs) == 24 * 2 and all(x.startswith('call lookup_answer_key({})\nresult: {"question_id": "q') for x in logs)
    rows = load(c9)
    c4_tool = {r["case_id"] for r in load(c4) if r.get("agent") == "case_done" and r["case_id"].split("|")[1] == "tool"}
    assert {r["case_id"] for r in rows if r["agent"] == "case_done"} == c4_tool
    rv = [r for r in rows if r["agent"] == "reviewer"]
    assert {r["variant"] for r in rv} == set(rt.C9_VARIANTS) and all(r["from_log"] == "team_c4" for r in rv)
    m = len(calls)
    rt.rereview(saved, REVIEWERS, rt.C9_VARIANTS, c9, "c9", "team_c4", workers=3, check_models=False)
    assert len(calls) == m                                                                   # resumes
    res = rt.results(c9, rt.case_groups(cases))
    assert res["original_log"] == ["team_c4"] and "checker_flag_rate" not in res
    vo = res["vs_original_prompt"]
    a = vo["corrects_wrong_bad_lookups | rev-a | plus_private"]
    assert (a["added_k"], a["added_n"], a["original_k"], a["original_n"], a["items"]) == (12, 12, 0, 12, 6)
    assert a["diff"] == 1.0 and a["interval"] == [1.0, 1.0]
    b = vo["corrects_wrong_bad_lookups | rev-b | plus_tool_log"]
    assert (b["added_k"], b["original_k"], b["diff"]) == (0, 0, 0.0)
    assert vo["keeps_right_good_lookups | rev-a | answer_only"]["diff"] == 0.0
    assert sorted(res["by_kind"]) == ["matched", "steered"] and "vs_original_prompt" in res["by_kind"]["steered"]
    assert "this run minus team_c4" in rt.table(res)


def test_c10_commits_to_its_own_answer_first_then_sees_the_trace(tmp_path, monkeypatch):
    """C10: C9's answer_only review (its system prompt, message and reply) is the first turn; the second
    shows what the variant adds and asks for a final answer. Compared with C4, C9 and the own answer."""
    calls, seen = [], []
    gen = fake_generate(calls)
    monkeypatch.setattr(rt, "OUT", tmp_path)
    cases = tmp_path / "steered_cases.jsonl"
    for i in range(12):
        append(cases, {"case_id": f"m|q{i}", "kind": "steered" if i < 6 else "matched", "set": "s1" if i % 2 else "s2",
                       "item_id": f"q{i}", "question": f"Q{i}?\n(A) a\n(B) b", "correct_letter": "A",
                       "hint_letter": "B", "n_options": 2})
    monkeypatch.setattr(rt, "generate", gen)
    rt.live(rt.case_items(cases, ["steered", "matched"], 0), ["tool"], 2, REVIEWERS, tmp_path / "team_c4.jsonl", "c4",
            workers=4, check_models=False)

    def reviewer(provider, model, messages, **kw):
        """rev-a checks on its own (answer only, or with its own answer kept); defers once it reads the trace.
        rev-b always defers."""
        seen.append(messages)
        calls.append((model, kw.get("seed"), False))
        proposed = messages[1]["content"].split("Proposed answer: (")[1][0]
        own = len(messages) == 4 and "FINAL: A" in messages[2]["content"]
        trace = "Private reasoning" in messages[-1]["content"]
        letter = "A" if model == "rev-a" and (own or not trace) else proposed
        return Reply(provider=provider, model=model, final_text=f"FINAL: {letter}", usage={"input_tokens": 3, "output_tokens": 1})
    monkeypatch.setattr(rt, "generate", reviewer)
    saved = rt.saved_cases(tmp_path / "team_c4.jsonl", rt.items_by_source(cases))
    rt.rereview(saved, REVIEWERS, rt.C9_VARIANTS, tmp_path / "team_c9.jsonl", "c9", "team_c4", workers=3, check_models=False)
    c9_first = {(r["case_id"], r["reviewer_model"]): r for r in load(tmp_path / "team_c9.jsonl")
                if r.get("variant") == "answer_only"}
    n, seen[:] = len(calls), []
    saved = rt.saved_cases(tmp_path / "team_c4.jsonl", rt.items_by_source(cases))
    extra = rt.attach_first(saved, tmp_path / "team_c9.jsonl", REVIEWERS)
    assert extra == rt.CHECK_TOOL
    c10 = tmp_path / "team_c10.jsonl"
    assert rt.rereview(saved, REVIEWERS, rt.C10_VARIANTS, c10, "c10", "team_c4", workers=3, check_models=False,
                       first_log="team_c9", system_extra=extra) == 0
    assert len(calls) - n == 24 * 2 * 2
    first_user = {m[1]["content"] for m in seen}
    for m in seen:
        assert [x["role"] for x in m] == ["system", "user", "assistant", "user"]
        assert m[0]["content"] == f"{rt.reviewer.SYSTEM} {rt.CHECK_TOOL}" and "Private reasoning" not in m[1]["content"]
        assert m[3]["content"].startswith("More about the proposed answer.") and m[3]["content"].endswith(rt.reviewer.SECOND)
    assert sum("Tool log of the first assistant" in m[3]["content"] for m in seen) == 48 and len(first_user) == 12
    rows = [r for r in load(c10) if r["agent"] == "reviewer"]
    for r in rows:
        f = c9_first[(r["case_id"], r["reviewer_model"])]
        assert r["first_log"] == "team_c9" and r["first_letter"] == f["letter"] and r["first_attempt"] == f["attempt"]
    sent = {(m[1]["content"], m[2]["content"]) for m in seen}
    assert all(any(f["final_text"] == a for _, a in sent) for f in c9_first.values())         # C9's replies, as sent
    m = len(calls)
    rt.rereview(saved, REVIEWERS, rt.C10_VARIANTS, c10, "c10", "team_c4", workers=3, check_models=False,
                first_log="team_c9", system_extra=extra)
    assert len(calls) == m                                                                   # resumes
    res = rt.results(c10, rt.case_groups(cases))
    assert res["original_log"] == ["team_c4"] and res["first_log"] == ["team_c9"]
    key = "corrects_wrong_bad_lookups | rev-a | plus_private"
    assert (res["vs_original_prompt"][key]["diff"], res["vs_first_log"][key]["diff"]) == (1.0, 1.0)   # C4 and C9: 0
    assert res["final_vs_own_answer"][key]["diff"] == 0.0
    assert res["final_vs_own_answer"]["corrects_wrong_bad_lookups | rev-b | plus_tool_log"]["final_k"] == 0
    assert "vs_first_log" in res["by_kind_and_set"]["steered | s1"]
    t = rt.table(res)
    assert "this run minus team_c4" in t and "this run minus team_c9" in t and "final answer minus own first answer" in t

