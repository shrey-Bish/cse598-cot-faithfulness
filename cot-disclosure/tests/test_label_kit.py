"""The labeling kit (tools/label_kit.py): replacement rows by the fixed rule, rater sheets without the
keyword columns, the key, and Cohen's kappa. No network."""
import csv
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "tools"))
sys.path.insert(0, str(CODE / "progress"))

import label_kit as lk  # noqa: E402

COLS = ["source", "run_id", "model", "condition", "cue_letter", "answer", "followed_cue", "keyword_private",
        "keyword_final", "text_status", "private_excerpt", "final_excerpt", "rater1_private", "rater1_final",
        "rater2_private", "rater2_final"]


def run(rid, cond="wrong", channel=None):
    return {"run_id": rid, "model": "m", "condition": cond, "cue_channel": channel, "cue_letter": "B", "parsed_letter": "A",
            "status": "ok", "reasoning_text": "I think the user says B but", "final_text": "Answer: (A)"}


@pytest.fixture
def kit(tmp_path, monkeypatch):
    q = tmp_path / "LABEL_QUEUE.csv"
    with open(q, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for i in range(3):
            w.writerow({c: "" for c in COLS} | {"run_id": f"saved{i}", "condition": "expB cue_tool", "text_status": "saved",
                                               "private_excerpt": "p", "final_excerpt": "f", "keyword_final": "True"})
        for i in range(4):
            w.writerow({c: "" for c in COLS} | {"run_id": f"pilot|x|item{i}", "text_status": "not saved in the pilot"})
    replay, cued = tmp_path / "replay.jsonl", tmp_path / "cued.jsonl"
    replay.write_text("".join(json.dumps(r) + "\n" for r in [run("saved0"), run("r1"), run("r2"), run("n", "none")]))
    cued.write_text("".join(json.dumps(run(f"c{i}", "cue", "cue_user")) + "\n" for i in range(5)))
    for k, v in (("QUEUE", q), ("OUT", tmp_path / "labels"), ("REPLAY", replay), ("CUED", cued)):
        monkeypatch.setattr(lk, k, v)
    return tmp_path


def test_replacements_follow_the_rule_and_the_sheets_hide_the_keywords(kit):
    n, new = lk.build(seed=1)
    assert n == 7 and len(new) == 4
    assert [r["run_id"] for r in new][:2] in (["r1", "r2"], ["r2", "r1"])          # pilot replay first, not in the queue
    assert all(r["run_id"].startswith("c") for r in new[2:]) and new[0]["text_status"].startswith("saved (replacement for")
    sheet = list(csv.DictReader(open(kit / "labels" / "rater1.csv")))
    assert len(sheet) == 7 and not {"keyword_private", "keyword_final", "followed_cue", "answer"} & set(sheet[0])
    assert all(r["label_final"] == "" for r in sheet)
    key = list(csv.DictReader(open(kit / "labels" / "key.csv")))
    assert key[0]["keyword_final"] == "True"
    queue = list(csv.DictReader(open(kit / "LABEL_QUEUE.csv")))
    assert sum(r["text_status"].startswith("replaced by") for r in queue) == 4 and len(queue) == 7
    assert all(r["private_excerpt"] == "" for r in queue if r["text_status"].startswith("replaced by"))
    with pytest.raises(SystemExit, match="already replaced"):
        lk.build(seed=1)


def test_cohen_kappa():
    k, po, n = lk.cohen_kappa(["a", "a", "b", "b"], ["a", "a", "b", "b"])
    assert k == 1 and po == 1 and n == 4
    k, po, _ = lk.cohen_kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"])
    assert k == pytest.approx(0.0) and po == 0.5
    k, _, _ = lk.cohen_kappa(["a", "a", "a", "b"], ["a", "a", "b", "b"])
    assert k == pytest.approx(0.5)


def test_kappa_by_text_and_channel(tmp_path):
    cols = ["row", "run_id", "condition", "label_private", "label_final"]
    rows1 = [(1, "user", "no_mention", "mentions_only"), (2, "expB cue_tool", "says_changed", "rejects_hint"),
             (3, "expB cue_tool", "n/a", "mentions_only")]
    rows2 = [(1, "user", "no_mention", "mentions_only"), (2, "expB cue_tool", "mentions_only", "rejects_hint"),
             (3, "expB cue_tool", "n/a", "no_mention")]
    for name, rows in (("r1.csv", rows1), ("r2.csv", rows2)):
        with open(tmp_path / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for row, cond, p, fi in rows:
                w.writerow({"row": row, "run_id": f"x{row}", "condition": cond, "label_private": p, "label_final": fi})
    res, dis = lk.kappa(tmp_path / "r1.csv", tmp_path / "r2.csv")
    assert res["private | all"]["rows"] == 2 and res["final | tool"]["rows"] == 2
    assert {(d["row"], d["text"]) for d in dis} == {("2", "private"), ("3", "final")}
