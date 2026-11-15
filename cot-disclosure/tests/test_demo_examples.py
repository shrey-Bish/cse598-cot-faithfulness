"""The demo's example draw (tools/demo_examples.py): a few already-labelled rows per section, drawn by a fixed string
seed, read-only on every source, written only to results/demo/examples.json (gitignored). Synthetic sources only: no
real label sheet or text is read here."""
import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "tools"))

import demo_examples as de  # noqa: E402

ILL = "illustrative, drawn by seed"


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


@pytest.fixture
def labels(tmp_path):
    """Synthetic L6, L4 and L3 sheets in the real layout (results/labels/...), fake text only."""
    root = tmp_path / "labels"
    systems = ["lora", "prompt_only"] * 10
    write_csv(root / "L6" / "L6_RA_20261113.csv",
              [{"row": i + 1, "channel": "pasted", "hint_letter": "B", "final_answer": f"fake final L6 {i} (B)",
                "label_final": ("says_changed", "no_mention")[i % 2], "guess_trained": "no", "note": ""}
               for i in range(20)])
    write_csv(root / "L6" / "key_L6.csv",
              [{"row": i + 1, "run_id": f"l6run{i}", "system": systems[i], "channel": "pasted", "item_id": f"q{i}",
                "timestamp_utc": "", "mention_final_broad": "True", "seed": "L6-x"} for i in range(20)])
    (root / "L6" / "texts_L6.jsonl").write_text("".join(
        json.dumps({"run_id": f"l6run{i}", "system": systems[i], "channel": "tool_pasted", "item_id": f"q{i}",
                    "hint_letter": "B", "parsed_letter": "B", "final_text": f"fake final L6 {i} (B)"}) + "\n"
        for i in range(20)))
    write_csv(root / "gate3" / "L4" / "L4_part1_RA.csv",
              [{"row": i + 1, "run_id": f"l4run{i}", "channel": "tool_injected", "hint_letter": "C",
                "final_answer": f"fake final L4 {i} (C)", "label_final": "says_changed", "guess_trained": "",
                "note": "fake note"} for i in range(12)])
    write_csv(root / "gate3" / "L4" / "key_L4.csv",
              [{"part": 1, "row": i + 1, "run_id": f"l4run{i}", "system": ("lora", "base", "prompt_only")[i % 3],
                "candidate": "True", "match": "question", "item_id": f"q{i}", "seed": "L4-x"} for i in range(12)])
    write_csv(root / "L3_RA.csv",
              [{"row": i + 1, "run_id": f"l3run{i}", "model": "qwen3-30b-a3b-thinking-2507",
                "condition": "expB cue_tool (simulated tool block)" if i % 2 else "expB cue_user",
                "cue_letter": "D", "private_excerpt": f"fake private L3 {i} (D)", "final_excerpt": f"fake final L3 {i}",
                "label_private": "mentions_only", "label_final": "no_mention", "note": ""} for i in range(10)])
    return root


def digest(root):
    return {p.relative_to(root): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}


def test_the_draw_is_deterministic_by_seed(labels, tmp_path):
    a = de.draw(labels=labels, out=tmp_path / "a" / "results" / "demo" / "examples.json")
    b = de.draw(labels=labels, out=tmp_path / "b" / "results" / "demo" / "examples.json")
    assert a == b and a["seed"] == de.SEED
    assert (tmp_path / "a" / "results" / "demo" / "examples.json").read_bytes() == \
        (tmp_path / "b" / "results" / "demo" / "examples.json").read_bytes()
    c = de.draw(labels=labels, out=tmp_path / "c" / "results" / "demo" / "examples.json", seed="another seed")
    assert [e["run_id"] for e in c["examples"]] != [e["run_id"] for e in a["examples"]]


def test_each_example_carries_its_row_system_channel_label_and_mark(labels, tmp_path):
    res = de.draw(labels=labels, out=tmp_path / "results" / "demo" / "examples.json")
    ex = res["examples"]
    assert {e["source"] for e in ex} == {"L6", "L4", "L3"}
    for e in ex:
        assert e["illustrative"] == ILL
        for k in ("section", "row", "run_id", "system", "channel", "label", "hint_letter", "final_answer"):
            assert e.get(k) not in (None, ""), (k, e)
    l6 = [e for e in ex if e["source"] == "L6"]
    assert {e["system"] for e in l6} == {"lora", "prompt_only"}                      # both sides of L6
    assert all(e["system"] == "lora" for e in ex if e["source"] == "L4")             # LoRA's candidates on the 30
    assert all(e["private"] for e in ex if e["source"] == "L3")                      # the side-by-side's source
    assert all("cue_tool" in e["condition"] for e in ex if e["source"] == "L3")
    assert all(e["private"] is None and e["private_status"] for e in ex if e["source"] != "L3")
    by_run = {f"l6run{i}": i for i in range(20)}
    for e in l6:                                                                     # the label is the sheet's row
        i = by_run[e["run_id"]]
        assert e["row"] == i + 1 and e["label"] == ("says_changed", "no_mention")[i % 2]


def test_it_reads_only_and_writes_only_its_one_file(labels, tmp_path):
    before = digest(labels)
    out = tmp_path / "w" / "results" / "demo" / "examples.json"
    de.draw(labels=labels, out=out)
    assert digest(labels) == before
    assert [p for p in (tmp_path / "w").rglob("*") if p.is_file()] == [out]
    assert de.OUT == CODE / "results" / "demo" / "examples.json"
    with pytest.raises(ValueError):
        de.draw(labels=labels, out=tmp_path / "docs" / "examples.json")             # never outside results/demo/


def test_a_missing_source_is_said_and_the_rest_written(labels, tmp_path):
    (labels / "L3_RA.csv").unlink()
    res = de.draw(labels=labels, out=tmp_path / "results" / "demo" / "examples.json")
    assert any("L3_RA.csv" in m for m in res["missing"])
    assert {e["source"] for e in res["examples"]} == {"L6", "L4"}
