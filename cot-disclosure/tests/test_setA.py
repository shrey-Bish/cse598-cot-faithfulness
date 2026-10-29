"""Set A (finetune/setA.py): the 34 validation questions in Step 2b's item format, the runs, resuming and
the stop file with a fake model, and the cases; Steps 9 and 10 reading another question set's files
(--items-from, --step3-from, --cases-from). No network."""
import gzip
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import load  # noqa: E402
from finetune import base_format as bf  # noqa: E402
from finetune import setA  # noqa: E402
from finetune import train as tr  # noqa: E402
from mmlu_pro_probe import question_block  # noqa: E402

HAVE_DATA = setA.POOL.exists() and tr.VALIDATION.exists()


def test_options_split_back_into_the_same_text():
    stem, opts = setA.split_options("Who won?\nLine two.\n(A) Amy\n(B) Ben (the tall one)\n(C) Cy")
    assert stem == "Who won?\nLine two." and opts == ["Amy", "Ben (the tall one)", "Cy"]
    with pytest.raises(ValueError):
        setA.split_options("Who won?\n(A) Amy\n(C) Cy")
    with pytest.raises(ValueError):
        setA.split_options("Who won? no options")


@pytest.mark.skipif(not HAVE_DATA, reason="needs finetune/data")
def test_set_a_is_the_validation_questions_and_disjoint_from_training_and_test2():
    its = setA.items()
    pool = {r["item_id"]: r for r in load(setA.POOL)}
    assert len(its) == 34 and len({it["question_id"] for it in its}) == 34
    for it in its:
        assert question_block(it) == pool[it["question_id"]]["question"]          # the pool's text, exactly
        assert it["cue_letter"] != it["answer"] and it["cue_letter"] in "ABCDEFGHIJ"[:len(it["options"])]
    train = {x["item_id"] for x in tr.load_examples(CODE / "finetune" / "data" / "train_examples.jsonl.gz")}
    assert not train & {it["question_id"] for it in its}
    test2 = {str(it["question_id"]) for it in bf.questions()}
    assert not test2 & {it["question_id"].split("-")[-1] for it in its if it["question_id"].startswith("mmlupro-")}
    js = setA.jobs(its)
    assert len(js) == 204 and len({setA.job_id(j) for j in js}) == 204
    assert {(j[1], j[3]) for j in js} == {("tool_pasted", None), (bf.INJECTED, bf.DECLARED)}


def nohint(q, letters, correct="A"):
    return [{"item_id": q, "condition": "none", "status": "ok", "parsed_letter": x, "correct_letter": correct}
            for x in letters]


def test_own_answer_and_sure_from_the_step6_runs():
    own, sure = setA.own_and_sure(nohint("q1", "AAA") + nohint("q2", "ABA") + nohint("q3", "AB") + nohint("q4", "BBB"))
    assert own == {"q1": "A", "q2": "A", "q3": None, "q4": "B"}
    assert sure == {"q1": True, "q2": False, "q3": False, "q4": False}


def fake_items(n=2):
    return [{"question_id": f"q{i}", "question": f"Q{i}?", "options": ["a", "b", "c"], "answer": "A",
             "cue_letter": "B", "category": "x"} for i in range(n)]


def test_generation_resumes_and_stops_at_the_stop_file(tmp_path, monkeypatch):
    for name in ("RUNS", "ROWS"):
        monkeypatch.setattr(setA, name, tmp_path / getattr(setA, name).name)
    calls = []

    def one(it, cond, rep, arm=None, experiment=None):
        calls.append((it["question_id"], cond, rep))
        return {"run_id": bf.run_id(experiment, it["question_id"], bf.MODEL, cond, arm, rep), "status": "ok",
                "requested_model_id": bf.ROUTE[0], "reasoning_effort": bf.ROUTE[1], "timestamp_utc": f"t{len(calls)}",
                "condition": cond, "arm": arm, "repeat": rep, "item_id": it["question_id"], "parsed_letter": "B",
                "cue_letter": "B", "reasoning_text": "r", "usage": {}}
    monkeypatch.setattr(bf, "one", one)
    its = fake_items()
    assert setA.generate(its) == (12, 12) and len(calls) == 12
    assert setA.generate(its) == (12, 12) and len(calls) == 12                       # resumes: nothing redone
    assert len(setA.followed(bf.current(load(setA.RUNS)))) == 12
    stop = tmp_path / "stop"
    stop.touch()
    monkeypatch.setattr(setA, "RUNS", tmp_path / "other.jsonl.gz")
    assert setA.generate(its, stop_file=str(stop)) == (0, 12) and len(calls) == 12   # no new run once it exists


def test_cases_are_late_takeovers_on_sure_questions(tmp_path, monkeypatch):
    rows = [{"source_run_id": f"r{i}", "source_timestamp_utc": "t", "item_id": q, "condition": "tool_pasted", "arm": None,
             "repeat": i, "hint_letter": "B", "n_sentences": 10, "takeover_k": k, "takeover_frac": k / 10,
             "kind": "followed", "mentions": [False] * 11, "leads_before_reasoning": False}
            for i, (q, k) in enumerate((("q0", 8), ("q0", 2), ("q1", 9)))]
    monkeypatch.setattr(setA, "probed", lambda own: (rows, rows))
    monkeypatch.setattr(setA, "CASES", tmp_path / "cases.jsonl")
    out = setA.cases({}, {"q0": True, "q1": False})
    assert [c["source_run_id"] for c in out] == ["r0"]
    saved = load(tmp_path / "cases.jsonl")[-1]
    assert saved["rule"].startswith("followed runs whose takeover") and "set A" in saved["use"]
    assert [c["takeover_k"] for c in saved["cases"]] == [8]


@pytest.mark.skipif(not (bf.OUT.exists() and HAVE_DATA), reason="needs Step 2b's runs")
def test_steps_9_and_10_read_another_question_sets_files(tmp_path):
    """Set A on Sol: the same code with --runs-from, --items-from, --step3-from and --cases-from. Here the files
    are Step 2b's own runs, items and cases, written out, so the inputs must match the defaults."""
    pytest.importorskip("torch")
    from finetune.look import attn_to_hint as at
    from finetune.look import patching as pt
    from finetune.look import takeover as tk
    items = tmp_path / "items.jsonl"
    items.write_text("".join(json.dumps(it) + "\n" for it in bf.questions()))
    runs = tmp_path / "runs.jsonl.gz"
    with gzip.open(runs, "wt") as f:
        f.writelines(json.dumps(r) + "\n" for r in load(bf.OUT))
    step3 = tmp_path / "takeover_runs.jsonl"
    step3.write_text(tk.RUNS_OUT.read_text())
    cases = tmp_path / "cases.jsonl"
    cases.write_text(tk.CASES_OUT.read_text())
    h1, i1, s1 = at.inputs(str(runs), str(items), str(step3))
    h0, i0, s0 = at.inputs(str(runs))
    assert [r["run_id"] for r in h1] == [r["run_id"] for r in h0] and i1.keys() == i0.keys() and s1 == s0
    c1, st1, it1, step4 = pt.inputs(str(runs), str(cases), str(items))
    assert len(c1) == 21 and it1.keys() == {it["question_id"] for it in bf.questions()} and step4 == {}
