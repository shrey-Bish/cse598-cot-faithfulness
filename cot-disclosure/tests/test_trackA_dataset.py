"""Track A Step 5 (finetune/build_dataset.py): CPU only, no network, synthetic inputs."""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from finetune import build_dataset as bd  # noqa: E402


def q(i, correct="A"):
    return {"question_set": "pool", "item_id": f"q{i}", "question": f"Question {i}\n(A) 1\n(B) 2\n(C) 3\n(D) 4",
            "n_options": 4, "correct": correct, "hint_letters": ["B"]}


def runs(*letters, finish="stop", status="ok"):
    return [{"condition": "none", "status": status, "parsed_letter": x, "finish_reason": finish, "repeat": i}
            for i, x in enumerate(letters)]


HELD = [{"question_set": "mmlupro_30", "item_id": "mmlupro-9", "qid": 9, "question": "H?\n(A) x\n(B) y",
         "n_options": 2, "correct": "A", "hint_letters": ["B"]}]


def build(questions, pinned, rule="all_correct", ratio=0.5, plan="all_wordings"):
    return bd.build(rule, ratio, train_questions=questions, heldout=HELD, runs=pinned, served={}, step2b=[], plan=plan)


def test_the_default_plan_has_few_records_per_question():
    qs = [q(i) for i in range(40)]
    rows, _ = build(qs, {f"q{i}": runs("A", "A", "A") for i in range(40)}, plan="per_channel")
    train = [r for r in rows if r["split"] != "heldout"]
    for i in range(40):
        mine = [r for r in train if r["item_id"] == f"q{i}"]
        wrong = [r for r in mine if not r["hint_correct"]]
        assert sorted(r["hint_channel"] for r in wrong) == ["tool_injected", "tool_pasted", "user"]
        assert 1 <= len(mine) - len(wrong) <= 2
    n_right = sum(r["hint_correct"] for r in train)
    assert 0.35 < n_right / (len(train) - n_right) < 0.65                       # 1 per 2 on average
    assert rows == build(qs, {f"q{i}": runs("A", "A", "A") for i in range(40)}, plan="per_channel")[0]   # seeded


def test_the_target_rule_keeps_only_three_answered_correct_runs():
    qs = [q(i) for i in range(7)]
    pinned = {"q0": runs("A", "A", "A"), "q1": runs("A", "A"), "q2": runs("A", "A", "C"),
              "q3": runs("C", "C", "C"), "q4": runs("A", "A", "A", finish="length"), "q5": runs("A", None, "A")}
    rows, facts = build(qs, pinned)
    assert facts["kept"] == 1 and {r["item_id"] for r in rows if r["split"] != "heldout"} == {"q0"}
    assert facts["dropped"] == {"fewer than 3 no-hint runs": 1, "the no-hint runs disagree": 1,
                                "the no-hint runs agree on a wrong answer": 1, "a no-hint run was cut off": 1,
                                "a no-hint run has no answer": 1, "no pinned-format no-hint runs yet (Step 6)": 1}
    assert all(r["target_answer"] == "A" for r in rows if r["split"] != "heldout")


def test_the_old_majority_rule_falls_back_to_the_correct_answer():
    rows, facts = build([q(0), q(1)], {"q0": runs("C", "C", "A"), "q1": runs("B", "C")}, rule="majority")
    targets = {r["item_id"]: r["target_answer"] for r in rows if r["split"] != "heldout"}
    assert facts["kept"] == 2 and targets == {"q0": "C", "q1": "A"}


def test_correct_hint_records_are_one_per_two_wrong_ones_with_the_same_target():
    rows, _ = build([q(0)], {"q0": runs("A", "A", "A")})
    mine = [r for r in rows if r["item_id"] == "q0"]
    wrong = [r for r in mine if not r["hint_correct"]]
    right = [r for r in mine if r["hint_correct"]]
    assert len(wrong) == len(bd.WORDINGS["train"]) and len(right) == round(len(wrong) / 2)
    assert all(r["hint_letter"] == "A" and r["target_answer"] == "A" for r in right)
    assert len({r["id"] for r in mine}) == len(mine)
    rows, _ = build([q(0)], {"q0": runs("A", "A", "A")}, ratio=0)
    assert not any(r["hint_correct"] for r in rows)


def test_training_channels_are_user_pasted_and_the_declared_inserted_turn():
    rows, _ = build([q(0)], {"q0": runs("A", "A", "A")})
    train = [r for r in rows if r["split"] != "heldout"]
    assert {r["hint_channel"] for r in train} == {"user", "tool_pasted", "tool_injected"}
    ins = next(r for r in train if r["hint_channel"] == "tool_injected")
    assert ins["tools_declared"][0]["function"]["name"] == "lookup_answer_key"
    assert ins["system_prompt"] == "think_declared_functions"
    assert [m["role"] for m in ins["messages"]] == ["user", "assistant", "tool"]
    assert ins["messages"][2]["content"] == ins["hint_text"] and ins["hint_text"] not in ins["messages"][0]["content"]
    held = {r["hint_wording"]: r for r in rows if r["split"] == "heldout"}
    assert held["inserted_study_guide_undeclared"]["tools_declared"] is None
    assert held["inserted_new_tool"]["messages"][1]["tool_calls"][0]["function"]["name"] == bd.NEW_TOOL
    assert held["inserted_study_guide"]["hint_text"] == bd.tool_reply(9, "B")      # Step 2b's exact reply
    assert held["system_note"]["messages"][0]["role"] == "system"


def test_heldout_wordings_never_appear_in_training():
    rows, _ = build([q(i) for i in range(3)], {f"q{i}": runs("A", "A", "A") for i in range(3)})
    assert bd.heldout_overlap(rows) == []
    leaked = rows + [{**rows[0], "split": "train", "hint_text": "My professor said the answer is (B).",
                      "tool_name": None, "id": "x"}]
    assert bd.heldout_overlap(leaked)                                            # caught
    tool = rows + [{**rows[0], "split": "train", "tool_name": bd.NEW_TOOL, "hint_text": "z", "id": "y"}]
    assert "tool:" + bd.NEW_TOOL in bd.heldout_overlap(tool)


def test_the_validation_slice_is_ten_percent_of_kept_questions_and_whole_questions():
    qs = [q(i) for i in range(30)]
    rows, facts = build(qs, {f"q{i}": runs("A", "A", "A") for i in range(30)})
    val = {r["item_id"] for r in rows if r["split"] == "validation"}
    train = {r["item_id"] for r in rows if r["split"] == "train"}
    assert len(val) == 3 and not val & train and sorted(val) == facts["validation_questions"]


def test_a_declared_inserted_record_renders_in_the_pinned_format():
    import pytest
    pytest.importorskip("transformers")
    from finetune import olmo_format
    rows, _ = build([q(0)], {"q0": runs("A", "A", "A")})
    ins = next(r for r in rows if r["hint_channel"] == "tool_injected" and r["split"] != "heldout")
    text = olmo_format.render(ins["messages"], tools=ins["tools_declared"])
    assert "lookup_answer_key" in text.split("<|im_start|>user")[0]                 # declared in the system turn
    assert "<|im_start|>environment" in text and ins["hint_text"] in text and text.endswith("<think>")


def test_length_summary_counts_finished_runs_and_prompt_plus_reply():
    from finetune import length_audit as la
    rows = [{"cut": False, "reply": 9000, "prompt": 500, "counted": False},
            {"cut": False, "reply": 16000, "prompt": 500, "counted": False},
            {"cut": True, "reply": 16000, "prompt": 500, "counted": False},
            {"cut": False, "reply": 100, "prompt": None, "counted": True}]
    s = la.summarize(rows)
    assert (s["runs"], s["cut_off"], s["finished"], s["median_reply"]) == (4, 1, 3, 9000)
    assert (s["over_8192"], s["over_16384"], s["total_over_8192"], s["total_over_16384"]) == (2, 0, 2, 1)
    assert s["with_prompt"] == 2 and s["counted_with_tokenizer"] == 1



def test_a_no_hint_run_over_32768_tokens_in_all_counts_as_cut_off():
    long = runs("A", "A", "A")
    long[1]["usage"] = {"prompt_tokens": 400, "completion_tokens": 32500}
    assert bd.all_correct(q(0), long) == (None, "a no-hint run was cut off")
    long[1]["usage"] = {"prompt_tokens": 400, "completion_tokens": 32000}
    assert bd.all_correct(q(0), long) == ("A", None)
