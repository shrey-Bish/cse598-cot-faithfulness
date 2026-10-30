"""C17: the same saved final answers with one fixed sentence appended (run_team.py --rereview --final-suffix), and
C17's readings. CPU only, no network."""
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from agents import c15, c17, run_team as rt  # noqa: E402
from common import load  # noqa: E402
from providers.base import Reply  # noqa: E402


def fake_generate(seen):
    """The Olmo reviewer takes a proposed answer whose explanation names the lookup tool and otherwise answers A
    (right); the Qwen3 one always answers A."""
    def generate(provider, model, messages, tools=None, tool_choice=None, **kw):
        if tools and tool_choice:
            return Reply(provider=provider, model=model, tool_calls=[{"id": "c1", "name": "lookup_answer_key",
                                                                       "arguments": "{}"}], finish_reason="tool_calls")
        user = messages[-1]["content"]
        if messages[-1]["role"] == "tool":
            return Reply(provider=provider, model=model, final_text=f"Answer: ({json.loads(user)['expected']})",
                         reasoning_text="r", reasoning_visibility="full", usage={"input_tokens": 10, "output_tokens": 5})
        if model in (c15.OLMO, c15.QWEN):
            seen.append(user)
            proposed = user.split("Proposed answer: (")[1][0]
            letter = proposed if model == c15.OLMO and "lookup tool" in user else "A"
            return Reply(provider=provider, model=model, final_text=f"FINAL: {letter}", usage={"input_tokens": 3, "output_tokens": 1})
        return Reply(provider=provider, model=model, final_text="Answer: (A)", reasoning_text="r", reasoning_visibility="full",
                     usage={"input_tokens": 10, "output_tokens": 5})
    return generate


def test_the_suffix_is_appended_to_the_final_answer_and_logged(tmp_path, monkeypatch):
    cases = tmp_path / "items.jsonl"
    cases.write_text(json.dumps({"case_id": "c15|q0", "kind": "fresh", "set": "s", "item_id": "q0", "question": "Q?\n(A) a\n(B) b",
                                 "n_options": 2, "correct_letter": "A", "hint_letter": "B"}) + "\n")
    seen = []
    monkeypatch.setattr(rt, "generate", fake_generate(seen))
    solve = tmp_path / "solve.jsonl"
    assert rt.live(rt.case_items(cases, ["fresh"], 0), ["tool"], 1, [], solve, "t", workers=1, check_models=False) == 0
    saved = rt.saved_cases(solve, rt.items_by_source(cases))
    final = saved[0][0]["solver"]["final_text"]
    for name, suffix in (("plain", None), ("names", "names_tool")):
        log = tmp_path / f"{name}.jsonl"
        assert rt.rereview(saved, [("voyager", c15.QWEN)], ["plus_explanation"], log, "t", "solve", workers=1,
                           check_models=False, system_extra=None, final_suffix=suffix) == 0
        row = next(r for r in load(log) if r["agent"] == "reviewer")
        if suffix:
            assert f"Proposed explanation:\n{final}\n\n{rt.FINAL_SUFFIXES['names_tool']}" in seen[-1]
            assert row["final_suffix"] == "names_tool"
        else:
            assert seen[-1].endswith(f"Proposed explanation:\n{final}") and "final_suffix" not in row


def test_c17_reads_the_named_source_against_own_working(tmp_path, monkeypatch):
    cases = tmp_path / "c15_items.jsonl"
    rows = [{"case_id": f"c15|q{i}", "kind": "fresh", "set": "s", "item_id": f"q{i}", "question": f"Q{i}?\n(A) a\n(B) b",
             "n_options": 2, "correct_letter": "A", "hint_letter": "B"} for i in range(30)]
    cases.write_text("".join(json.dumps(r) + "\n" for r in rows))
    monkeypatch.setattr(rt, "generate", fake_generate([]))
    solve = tmp_path / "team_c15_solve.jsonl"
    assert rt.live(rt.case_items(cases, ["fresh"], 0), ["tool"], 1, [], solve, "t", workers=2, check_models=False) == 0
    saved = rt.saved_cases(solve, rt.items_by_source(cases))
    reviewers = [("voyager", c15.OLMO), ("voyager", c15.QWEN)]
    for log, suffix in (("team_c16_control", None), ("team_c17_names", "names_tool"), ("team_c17_own", "own_working")):
        assert rt.rereview(saved, reviewers, ["plus_explanation"], tmp_path / f"{log}.jsonl", "t", "team_c15_solve",
                           workers=2, check_models=False, system_extra=None, final_suffix=suffix) == 0
    res = c17.analyze(log_dir=tmp_path)
    bad = sum(rt.solver.ToolOracle().is_bad(f"q{i}") for i in range(30))
    main = res["b_names_minus_own"][c15.OLMO]
    assert main["items"] == bad and main["variant_k"] == 0 and main["answer_only_k"] == bad
    assert main["reading"] == "fewer corrections"
    assert res["a_names_minus_unchanged"][c15.OLMO]["reading"] == "fewer corrections"
    assert res["b_names_minus_own"][c15.QWEN]["reading"] == "no change"
    assert res["side_effect_keeps"]["names_minus_own"][c15.OLMO]["items"] == 30 - bad
    assert res["cases"] == {"unchanged": 30, "names_tool": 30, "own_working": 30}
