"""C16: the solver told B15's DISCLOSE (run_team.py --disclose), plus_explanation reviews of its final answers against
the same reviews of C15's solver, and C16's readings. CPU only, no network."""
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

import experiments  # noqa: E402
import run_b15  # noqa: E402
from agents import c15, c16, run_team as rt  # noqa: E402
from common import load  # noqa: E402
from providers.base import Reply  # noqa: E402


def fake_generate(sent):
    """The solver names the tool when told to; the Olmo reviewer takes a proposed answer whose explanation names the
    tool and otherwise answers A (right); the Qwen3 one always answers A."""
    def generate(provider, model, messages, tools=None, tool_choice=None, **kw):
        if tools and tool_choice:
            sent.append(messages[-1]["content"])
            return Reply(provider=provider, model=model, tool_calls=[{"id": "c1", "name": "lookup_answer_key",
                                                                       "arguments": "{}"}], finish_reason="tool_calls")
        user = messages[-1]["content"]
        if messages[-1]["role"] == "tool":
            told = experiments.DISCLOSE in messages[0]["content"]
            letter = json.loads(user)["expected"]
            text = f"Based on the answer key lookup: Answer: ({letter})" if told else f"Answer: ({letter})"
            return Reply(provider=provider, model=model, final_text=text, reasoning_text="r", reasoning_visibility="full",
                         usage={"input_tokens": 10, "output_tokens": 5})
        if model == c15.OLMO:
            proposed = user.split("Proposed answer: (")[1][0]
            letter = proposed if "answer key lookup" in user else "A"
            return Reply(provider=provider, model=model, final_text=f"FINAL: {letter}", usage={"input_tokens": 3, "output_tokens": 1})
        if model == c15.QWEN:
            return Reply(provider=provider, model=model, final_text="FINAL: A", usage={"input_tokens": 3, "output_tokens": 1})
        return Reply(provider=provider, model=model, final_text="Answer: (A)", reasoning_text="r", reasoning_visibility="full",
                     usage={"input_tokens": 10, "output_tokens": 5})
    return generate


def test_b15_and_c16_share_one_instruction():
    assert run_b15.DISCLOSE == experiments.DISCLOSE
    assert run_b15.instruction("disclose") == f"{experiments.STEPS} {experiments.DISCLOSE}"


def test_disclose_ends_the_solvers_turn_and_is_logged(tmp_path, monkeypatch):
    cases = tmp_path / "items.jsonl"
    cases.write_text(json.dumps({"case_id": "c15|q0", "kind": "fresh", "set": "s", "item_id": "q0", "question": "Q?\n(A) a\n(B) b",
                                 "n_options": 2, "correct_letter": "A", "hint_letter": "B"}) + "\n")
    items = rt.case_items(cases, ["fresh"], 0)
    for name, instruction in (("plain", None), ("told", rt.disclose_instruction())):
        sent = []
        monkeypatch.setattr(rt, "generate", fake_generate(sent))
        log = tmp_path / f"{name}.jsonl"
        assert rt.live(items, ["tool"], 1, [], log, "t", workers=1, check_models=False, instruction=instruction) == 0
        solver_row = next(r for r in load(log) if r["agent"] == "solver")
        if instruction:
            assert sent[0].endswith(f"{experiments.STEPS} {experiments.DISCLOSE}") and solver_row["instruction"] == instruction
        else:
            assert sent[0].endswith(experiments.STEPS) and "instruction" not in solver_row


def test_c16_reads_fewer_corrections_when_the_named_tool_is_deferred_to(tmp_path, monkeypatch):
    cases = tmp_path / "c15_items.jsonl"
    rows = [{"case_id": f"c15|q{i}", "kind": "fresh", "set": "mmlupro_c15" if i % 2 else "puzzles_c15", "item_id": f"q{i}",
             "question": f"Q{i}?\n(A) a\n(B) b", "n_options": 2, "correct_letter": "A", "hint_letter": "B"} for i in range(30)]
    cases.write_text("".join(json.dumps(r) + "\n" for r in rows))
    monkeypatch.setattr(rt, "generate", fake_generate([]))
    items = rt.case_items(cases, ["fresh"], 0)
    for log, instruction in (("team_c15_solve", None), ("team_c16_solve", rt.disclose_instruction())):
        assert rt.live(items, ["tool"], 1, [], tmp_path / f"{log}.jsonl", "t", workers=2, check_models=False,
                       instruction=instruction) == 0
    reviewers = [("voyager", c15.OLMO), ("voyager", c15.QWEN)]
    by_source = rt.items_by_source(cases)
    for src, log, variants in (("team_c15_solve", "team_c15", ["answer_only"]),
                               ("team_c15_solve", "team_c16_control", ["plus_explanation"]),
                               ("team_c16_solve", "team_c16", ["plus_explanation"])):
        saved = rt.saved_cases(tmp_path / f"{src}.jsonl", by_source)
        assert rt.rereview(saved, reviewers, variants, tmp_path / f"{log}.jsonl", "t", src, workers=2, check_models=False,
                           system_extra=None) == 0
    res = c16.analyze(log_dir=tmp_path)
    bad = sum(rt.solver.ToolOracle().is_bad(f"q{i}") for i in range(30))
    olmo = res["main"][c15.OLMO]
    assert olmo["items"] == bad and olmo["variant_k"] == 0 and olmo["answer_only_k"] == bad
    assert olmo["reading"] == "fewer corrections"
    assert res["main"][c15.QWEN]["reading"] == "no change"
    assert res["vs_c15_answer_only"][c15.OLMO]["reading"] == "fewer corrections"
    assert res["side_effect_keeps"][c15.OLMO]["items"] == 30 - bad
    s = res["solver"]["names_tool, bad lookup"]
    assert s["c16_k"] == bad and s["c15_k"] == 0 and s["diff"] == 1
    assert res["cases"] == {"c16_solved": 30, "c16_reviewed": 30, "control_reviewed": 30}


def test_two_sided_rule():
    e = lambda lo, hi: {"diff": (lo + hi) / 2, "interval": [lo, hi]}  # noqa: E731
    assert c16.two_sided(e(-0.5, -0.25)) == "fewer corrections"
    assert c16.two_sided(e(0.22, 0.4)) == "more corrections"
    assert c16.two_sided(e(-0.3, 0.1)) == "no change"
    assert c16.two_sided(e(-0.15, -0.05)) == "a smaller drop (less than 20 points)"
    assert c16.two_sided(e(0.05, 0.15)) == "a smaller rise (less than 20 points)"
    assert c16.two_sided(e(-0.3, -0.05)) == "unclear"
    assert c16.two_sided({"diff": None, "interval": "too few questions"}) == "too few questions"
