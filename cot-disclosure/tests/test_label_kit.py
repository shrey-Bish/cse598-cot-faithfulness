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


def test_the_trackb_batch_labels_the_f15_contrast_first(tmp_path, monkeypatch):
    """Oct 28 (Ritik): the real-call vs pasted contrast in the final answer is a headline candidate on
    keyword counts, so those runs come first: Qwen3 Thinking's that followed, then Instruct's. Last, the
    keyword check: a seeded sample of Thinking's bare real-call replies, private reasoning only."""
    import gzip
    monkeypatch.setattr(lk, "PRIVATE_CHECK", (*lk.PRIVATE_CHECK[:2], 1))

    def rec(model, cond, i, letter="B", final="Answer: (B)", reasoning="the lookup tool says B"):
        return {"experiment": "trackB", "run_id": f"{model}|{cond}|{i}", "provider": "voyager", "model": model,
                "thinking": None, "format": "served", "set": "s", "item_id": f"q{i}", "condition": cond, "repeat": 0,
                "hint_letter": "B", "correct_letter": "A", "parsed_letter": letter, "status": "ok", "finish_reason": "stop",
                "called_tool": cond == "tool_real", "tool_calls_by_model": int(cond == "tool_real"),
                "final_text": final, "reasoning_text": reasoning, "usage": {"output_tokens": 10}}
    think, inst = lk.TRACKB_GROUPS[0][1], lk.TRACKB_GROUPS[1][1]
    recs = [rec(inst, "tool_real", i, reasoning=None) for i in range(3)]
    recs += [rec(think, c, i) for c in ("tool_real", "tool_pasted") for i in range(2)]
    recs += [rec(think, "tool_real", 9, letter="A"), rec(think, "user", 8), rec(think, "system", 7)]   # not counted
    recs.append(rec(inst, "tool_pasted", 5, reasoning=None, final="The answer key says B, so: Answer: (B)"))
    path = tmp_path / "voyager.jsonl.gz"
    with gzip.open(path, "wt") as f:
        f.writelines(json.dumps(r) + "\n" for r in recs)
    rows, sizes = lk.build_trackb(path, tmp_path / "out", seed=1)
    assert [r["model"] for r in rows] == [think] * 4 + [inst] * 4
    assert {g: sizes[g]["runs"] for g, _ in lk.TRACKB_GROUPS} == {lk.TRACKB_GROUPS[0][0]: {"tool_real": 2, "tool_pasted": 2},
                                                                  lk.TRACKB_GROUPS[1][0]: {"tool_real": 3, "tool_pasted": 1}}
    assert [r["run_id"] for r in lk.trackb_rows(path, seed=1)] == [r["run_id"] for r in rows]          # seeded
    # Oct 28: every "Answer: (B)" here is bare (no_mention by rule); 1 per group stays in as the spot check
    assert [(sizes[g]["bare_no_mention_by_rule"], sizes[g]["with_text"], sizes[g]["spot_check"], sizes[g]["sheet_rows"])
            for g, _ in lk.TRACKB_GROUPS] == [(4, 0, 1, 1), (3, 1, 1, 2)]
    check = sizes[lk.PRIVATE_CHECK[0]]
    assert check["sheet_rows"] == 1 and check["keyword_private"] == 1 and check["of_bare_real_call_outside_spot_check"] in (1, 2)
    sheet = list(csv.DictReader(open(tmp_path / "out" / "rater2.csv")))
    assert len(sheet) == 4 and not {"keyword_private", "keyword_final", "called_tool", "bare", "spot_check",
                                    "private_check"} & set(sheet[0])
    assert [r["model"] for r in sheet] == [think, inst, inst, think]
    assert [r["label_final"] for r in sheet] == ["", "", "", "n/a"] and [r["label_private"] for r in sheet] == ["", "n/a", "n/a", ""]
    assert sheet[3]["group"] == lk.PRIVATE_CHECK[0] and sheet[3]["final_text"] == "" and sheet[3]["condition"] == "tool_real"
    assert sheet[3]["run_id"] != sheet[0]["run_id"]                     # never a spot-check row
    assert any(r["final_text"].startswith("The answer key") for r in sheet)
    key = list(csv.DictReader(open(tmp_path / "out" / "key.csv")))
    assert key[0]["run_id"] == sheet[0]["run_id"] and {"keyword_final", "called_tool", "bare", "spot_check"} <= set(key[0])
    assert [k["private_check"] for k in key] == ["False"] * 3 + ["True"] and key[3]["keyword_private"] == "True"
    pre = list(csv.DictReader(open(tmp_path / "out" / "prelabeled.csv")))
    assert len(pre) == 7 and {p["label_final"] for p in pre} == {"no_mention"} and all(p["rule"].startswith("bare") for p in pre)
    spots = [p for p in pre if p["sheet_row"]]
    assert len(spots) == 2 and {sheet[int(p["sheet_row"]) - 1]["run_id"] for p in spots} == {p["run_id"] for p in spots}
    assert json.loads((tmp_path / "out" / "kit.json").read_text())["sheet_rows"] == 4
    for name, final, private in (("rater1.csv", "no_mention", "mentions_only"), ("rater2.csv", "mentions_only", "no_mention")):
        sh = list(csv.DictReader(open(tmp_path / "out" / name)))        # the spot check and the keyword check in kappa
        for r in sh:
            r["label_final"] = final if r["label_final"] != "n/a" else "n/a"
            r["label_private"] = private if r["label_private"] != "n/a" else "n/a"
        with open(tmp_path / "out" / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(sh[0]))
            w.writeheader()
            w.writerows(sh)
    res, _ = lk.kappa(tmp_path / "out" / "rater1.csv", tmp_path / "out" / "rater2.csv")
    assert res["spot check | rater1 agrees with the rule"] == {"agreement": 1.0, "rows": 2, "of": 2}
    assert res["spot check | rater2 agrees with the rule"]["agreement"] == 0.0
    assert res["keyword check | rater1 agrees with the keyword"] == {"agreement": 1.0, "rows": 1, "of": 1, "keyword_says_mention": 1}
    assert res["keyword check | rater2 agrees with the keyword"]["agreement"] == 0.0
    assert [lk.channel_of(c) for c in ("tool_real", "system", "expB cue_tool", "pilot wrong hint")] == \
        ["tool_real", "system", "tool", "user"]


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
