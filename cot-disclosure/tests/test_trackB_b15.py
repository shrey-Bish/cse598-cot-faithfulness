"""B15 (progress/run_b15.py): the added instruction, the right-letter tool, its own records files and the
pre-registered report. CPU only, no network."""
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

pytest.importorskip("transformers")

import run_b15 as b15  # noqa: E402
import run_trackB as tb  # noqa: E402
from common import load  # noqa: E402
from experiments import STEPS  # noqa: E402
from providers.base import Reply  # noqa: E402


def cfg():
    return {"runs_per_question": 3, "token_budget": 32768, "closed_max_tokens": 8000, "temperature": 0.6, "in_flight": 4,
            "estimate": {"input_tokens": 500, "output_tokens": 4000, "seconds": 60},
            "question_sets": {"pilot_puzzles": {"source": "pilot", "n": 2},
                              "mmlupro_30": {"source": "mmlupro", "path": "data/progress/not_here.jsonl"}},
            "conditions": ["none", "user", "tool_pasted", "tool_real", "system"],
            "models": [{"provider": "voyager", "model": m, "est_seconds": 30} for m in b15.MODELS]}


def test_jobs_cover_every_arm_and_never_share_a_run_id_with_track_b():
    js = b15.jobs(cfg())
    assert len(js) == 3 * 2 * 2 * len(b15.ARMS)       # runs x questions x models x arms
    assert len({j["run_id"] for j in js}) == len(js)
    trackb = {j["run_id"] for j in tb.jobs(cfg())}
    assert not trackb & {j["run_id"] for j in js}
    assert {j["experiment"] for j in js} == {"b15"} and js[0]["repeat"] == 0 and js[-1]["repeat"] == 2
    plain = [j for j in js if j["arm"] == "plain|correct"]
    assert plain and all(j["instruction"] is None for j in plain)
    assert all(j["instruction"] == f"{STEPS} {b15.DISCLOSE}" for j in js if j["arm"].startswith("disclose"))


def test_the_instruction_ends_the_user_turn_and_the_correct_tool_returns_the_key(tmp_path, monkeypatch):
    monkeypatch.setattr(tb, "OUT", tmp_path)
    sent = []

    def fake_generate(provider, model, messages, tools=None, tool_choice=None, **kw):
        sent.append(list(messages))
        if tools and messages[-1]["role"] == "user":
            return Reply(provider=provider, model=model, tool_calls=[{"id": "c1", "name": "lookup_answer_key", "arguments": "{}"}],
                         finish_reason="tool_calls", usage={"output_tokens": 5})
        return Reply(provider=provider, model=model, final_text="Based on the tool. Answer: (A)", finish_reason="stop",
                     usage={"output_tokens": 5})
    monkeypatch.setattr(tb, "generate", fake_generate)
    monkeypatch.setattr(tb, "prompt_tokens", lambda model, msgs, tools: 500)
    j = next(j for j in b15.jobs(cfg()) if j["arm"] == "disclose|correct")
    rec = tb.run_one(cfg(), j)
    assert sent[0][-1]["content"].endswith(f"{STEPS} {b15.DISCLOSE}")
    assert json.loads(sent[1][-1]["content"])["expected"] == j["item"]["correct"]
    assert rec["hint_letter"] == j["item"]["correct"] and rec["letter_kind"] == "correct" and rec["experiment"] == "b15"
    tb.save(rec)
    assert load(tmp_path / "b15_voyager_runs.jsonl")[0]["arm"] == "disclose|correct"
    assert not (tmp_path / "voyager_runs.jsonl").exists()
    assert tb.done("voyager", "b15") == {rec["run_id"]} and tb.done("voyager") == set()


def flag(model, cond, arm, item, called=True, names=False, chars=11, followed=False, answered=True, parsed="A"):
    return {"model": model, "condition": cond, "arm": arm, "item_id": item, "called_tool": called, "mention_final": names,
            "final_chars": chars, "followed": followed, "answered": answered, "parsed_letter": parsed, "correct_letter": "A"}


def test_the_report_reads_naming_after_a_call_against_track_b():
    m = b15.MODELS[0]
    new = [flag(m, "tool_real", "disclose|hint", f"q{i}", names=True, chars=200) for i in range(8)]
    base = [flag(m, "tool_real", "trackB|hint", f"q{i}") for i in range(8)]
    new += [flag(m, "none", "disclose|hint", f"q{i}", called=False) for i in range(8)]
    base += [flag(m, "none", "trackB|hint", f"q{i}", called=False) for i in range(8)]
    res = b15.report(new, base)[m]
    assert res["names_tool_after_call"]["reading"] == "rises" and res["names_tool_after_call"]["diff"] == 1
    assert res["bare_after_call"]["reading"] == "falls"
    assert res["side_effects"]["nohint_accuracy"]["diff"] == 0
    assert res["following"]["tool_pasted"]["reading"] == "too few questions"
