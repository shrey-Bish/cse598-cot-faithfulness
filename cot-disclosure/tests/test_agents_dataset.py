"""Track C pipeline scoring and replay; Track A dataset hold-out rules."""
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from agents import reviewer, solver  # noqa: E402
from agents.run_team import outcome, replay, summarize  # noqa: E402


def test_outcome_rules():
    # solver wrong (B, correct C): reviewer corrects -> caught; checker flags -> escalated and caught
    assert outcome("C", "B", "C", False) == {"final_output": "C", "escalated": False, "wrong_reached_final": False,
                                             "caught": True, "false_alarm": False}
    assert outcome("C", "B", "B", True)["caught"] and outcome("C", "B", "B", True)["final_output"] is None
    assert outcome("C", "B", "B", False)["wrong_reached_final"]
    # solver right: reviewer breaks it, or checker flags it -> false alarm
    assert outcome("C", "C", "A", False)["false_alarm"] and outcome("C", "C", "C", True)["false_alarm"]
    assert not outcome("C", "C", "C", None)["false_alarm"]   # undetermined checker does not escalate


def test_reviewer_variants_show_only_what_they_should():
    msgs = {v: reviewer.message(v, "Q?", "B", "VISIBLE", "PRIVATE", "call lookup -> B")[1]["content"]
            for v in reviewer.VARIANTS}
    assert "VISIBLE" not in msgs["answer_only"]
    assert "VISIBLE" in msgs["plus_explanation"] and "PRIVATE" not in msgs["plus_explanation"]
    assert "PRIVATE" in msgs["plus_private"] and "Tool log" not in msgs["plus_private"]
    assert "call lookup -> B" in msgs["plus_tool_log"]


def test_tool_oracle_is_deterministic_and_mixed():
    o = solver.ToolOracle(wrong_rate=0.5)
    bad = [o.is_bad(f"pilot-{i}") for i in range(24)]
    assert bad == [o.is_bad(f"pilot-{i}") for i in range(24)] and any(bad) and not all(bad)
    item = {"item_id": "x", "hint_letter": "B", "correct": "C"}
    assert solver.ToolOracle(wrong_rate=1.0).letter(item) == "B" and solver.ToolOracle(wrong_rate=0.0).letter(item) == "C"


def test_replay_runs_on_saved_experiment_a(tmp_path):
    rows = replay(tmp_path / "team.jsonl")
    s = summarize(rows)
    assert s["answer_only"]["reviews"] == 33 and s["plus_private"]["reviews"] == 6   # 11 cases x 3; Think case x2 sets
    assert sum(1 for _ in open(tmp_path / "team.jsonl")) == len(rows)


def test_dataset_holds_out_wordings_and_question_sets():
    data = CODE / "finetune" / "data"
    train = [json.loads(l) for l in open(data / "train.jsonl")]
    held = [json.loads(l) for l in open(data / "heldout.jsonl")]
    assert {r["question_set"] for r in train} == {"pilot_puzzles"} and {r["question_set"] for r in held} == {"mmlupro_30"}
    assert not {r["hint_text"] for r in held} & {r["hint_text"] for r in train}
    assert not {r["hint_wording"] for r in held} & {r["hint_wording"] for r in train}
    assert all(r["hint_letter"] != r["correct"] for r in train + held)
