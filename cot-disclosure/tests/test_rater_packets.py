"""Rater packets (tools/rater_packets.py, Oct 31): built from the sheets as they are, checked, zipped. Synthetic
sheets and runs; no network."""
import csv
import json
import sys
import zipfile
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "tools"))

import rater_packets as rp  # noqa: E402

L3_COLS = ["row", "run_id", "model", "condition", "cue_letter", "private_excerpt", "final_excerpt", "label_private",
           "label_final", "note"]
L4_COLS = ["row", "run_id", "channel", "hint_letter", "final_answer", "label_final", "guess_trained", "note"]


def write(path, cols, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def run(rid, item="q-other", final="Answer: (E)", reasoning="Okay. The tool says the expected answer is F. Hmm."):
    return {"run_id": rid, "item_id": item, "cue_channel": "tool_injected", "cue_letter": "F", "parsed_letter": "E",
            "final_text": final, "reasoning_text": reasoning}


@pytest.fixture
def env(tmp_path, monkeypatch):
    labels = tmp_path / "labels"
    (labels / "gate3" / "L4").mkdir(parents=True)
    for n in (1, 2):
        write(labels / f"rater{n}.csv", L3_COLS, [{"row": i, "run_id": f"l3-{i}", "condition": "expB cue_user",
                                                  "label_private": "n/a" if i == 1 else ""} for i in (1, 2)])
    write(labels / "gate3" / "L4" / "part1.csv", L4_COLS, [{"row": i, "run_id": f"l4-{i}", "channel": "user"} for i in (1, 2)])
    write(labels / "gate3" / "L4" / "key_L4.csv", ["part", "row", "run_id", "system"],
          [{"part": 1, "row": i, "run_id": f"l4-{i}", "system": "lora"} for i in (1, 2)])
    runs = [run("ex1", final="Despite the tool's answer (F), my tracking gives E. Answer: (E)"), run("p1"), run("p2"),
            run("l3-1"), run("evalq", item="q-eval")]
    src = tmp_path / "runs.jsonl"
    src.write_text("".join(json.dumps(r) + "\n" for r in runs))
    spec = {"sources": [str(src)],
            "examples": [{"label": "rejects_hint", "run_id": "ex1", "text": "final", "hint_letter": "F", "answer": "E",
                          "quote": "… my tracking gives E. Answer: (E)", "why": "It sets the tool aside."}],
            "practice": [{"run_id": "p1", "label_private": "mentions_only", "label_final": "no_mention", "reason": "r"},
                         {"run_id": "p2", "label_private": "mentions_only", "label_final": "no_mention", "reason": "r"}]}
    (labels / "packets").mkdir()
    (labels / "packets" / "spec.json").write_text(json.dumps(spec))
    for k, v in (("LABELS", labels), ("PACKETS", labels / "packets"), ("SPEC", labels / "packets" / "spec.json"),
                 ("L3_SHEETS", {1: labels / "rater1.csv", 2: labels / "rater2.csv"}),
                 ("L4_PART1", labels / "gate3" / "L4" / "part1.csv"),
                 ("SHEET_IDS", (labels / "rater1.csv", labels / "gate3" / "L4" / "key_L4.csv")),
                 ("ROWS", {"L3": 2, "L4_part1": 2, "practice": 2})):
        monkeypatch.setattr(rp, k, v)
    monkeypatch.setattr(rp, "eval_items", lambda: {"q-eval"})
    return labels


def test_build_writes_two_clean_packets_with_the_sheets_as_built(env):
    out = rp.build()
    assert all(r["ok"] for r in out.values()), out
    shrey = env / "packets" / "shrey"
    assert {p.name for p in shrey.iterdir()} == rp.files_of("SB")
    assert (shrey / "L3_SB.csv").read_bytes() == (env / "rater2.csv").read_bytes()
    assert (env / "packets" / "ritik" / "L4_part1_RA.csv").read_bytes() == (env / "gate3" / "L4" / "part1.csv").read_bytes()
    with zipfile.ZipFile(env / "packets" / "rater_packet_shrey.zip") as z:
        assert sorted(z.namelist()) == sorted(f"rater_packet_shrey/{n}" for n in rp.files_of("SB"))
    readme = (shrey / "README_RATER.md").read_text()
    assert "L3_SB.csv" in readme and "Nov 6" in readme and "Nov 14" in readme and "rater 2" in readme
    assert "results/labels/gate3/L4/" in (env / "packets" / "ritik" / "README_RATER.md").read_text()
    guide = (shrey / "LABELING_GUIDE.md").read_text()
    assert "my tracking gives E" in guide and "### `unclear`" in guide
    practice = list(csv.DictReader(open(shrey / "practice.csv", newline="")))
    assert [r["run_id"] for r in practice] == ["p1", "p2"] and not any(r["label_final"] for r in practice)


def test_the_check_catches_keys_system_names_counts_and_sheet_rows(env):
    rp.build()
    d = env / "packets" / "shrey"
    (d / "key_L4.csv").write_text("row,system\n")
    write(d / "practice.csv", rp.PRACTICE_COLS + ["system"], [{"row": 1, "run_id": "l3-1"}])
    (d / "README_RATER.md").write_text("Rows from the LoRA version and the base model.")
    res = rp.check(d, "SB", {"l3-1"})
    text = "\n".join(res["problems"])
    assert not res["ok"]
    for want in ('a file name with "key": key_L4.csv', "not expected: key_L4.csv", 'practice.csv: key column "system"',
                 "practice.csv: 1 rows, not 2", "practice.csv: run l3-1 is in a sheet", 'README_RATER.md: system name "LoRA"',
                 'README_RATER.md: system name "base"'):
        assert want in text, want


def test_the_check_catches_a_sheet_changed_or_labeled(env):
    rp.build()
    d = env / "packets" / "ritik"
    write(d / "L4_part1_RA.csv", L4_COLS, [{"row": 1, "run_id": "l4-1", "label_final": "no_mention"}, {"row": 2, "run_id": "l4-2"}])
    text = "\n".join(rp.check(d, "RA", set())["problems"])
    assert "L4_part1_RA.csv: not byte for byte the sheet as built" in text and "L4_part1_RA.csv: label cells filled" in text


def test_the_build_refuses_a_spec_with_a_run_in_a_sheet_an_evaluation_question_or_a_borrowed_quote(env):
    spec = json.loads((env / "packets" / "spec.json").read_text())
    spec["examples"][0]["quote"] = "words the run never wrote"
    spec["practice"][1]["run_id"] = "l3-1"
    spec["practice"].append({"run_id": "evalq", "label_private": "maybe", "label_final": "no_mention", "reason": "r"})
    (env / "packets" / "spec.json").write_text(json.dumps(spec))
    with pytest.raises(SystemExit) as e:
        rp.build()
    msg = str(e.value)
    for want in ("ex1: the quote isn't the run's final text", "l3-1: in a sheet", "evalq: on one of the 30 evaluation questions",
                 "evalq: label_private 'maybe' isn't a label", "practice: 3 distinct rows, not 2"):
        assert want in msg, want
    assert not (env / "packets" / "shrey").exists()
