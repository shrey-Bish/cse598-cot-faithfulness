"""Track A, Steps 6 + 7 driver (finetune/run_steps67.py): CPU only, no network, fakes for both steps."""
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

pytest.importorskip("transformers")

from finetune import make_targets as mt  # noqa: E402
from finetune import run_nohint as rn  # noqa: E402
from finetune import run_steps67 as d  # noqa: E402


def pool(n):
    return [{"item_id": f"q{i}", "question_set": "mmlupro_train" if i % 2 else "fresh_puzzles_hard",
             "question": f"Q{i}\n(A) a\n(B) b\n(C) c", "n_options": 3, "correct": "A", "hint_letters": ["B"]}
            for i in range(n)]


@pytest.fixture
def fakes(monkeypatch, tmp_path):
    """Step 6 keeps every other question; Step 7 gives every record a prefill target."""
    for mod, names in ((rn, ("OUT", "RUNS_OUT")), (d, ("REPORT", "TRAIN_SET", "VALIDATION_SET", "SET_MANIFEST"))):
        for n in names:
            monkeypatch.setattr(mod, n, tmp_path / f"{mod.__name__.split('.')[-1]}_{n}.{'jsonl.gz' if 'SET' in n and n != 'SET_MANIFEST' else 'jsonl'}")
    outs = tuple(tmp_path / f"t{i}.jsonl" for i in range(4))
    monkeypatch.setitem(mt.OUTPUTS, mt.PREFILL, outs)
    monkeypatch.setattr(mt.rn, "OUT", rn.OUT)
    monkeypatch.setattr(mt, "n_tokens", lambda text: len(text) // 4)
    monkeypatch.setattr(d, "heldout_lengths", lambda: [12000, 14000])
    calls = {"step6": 0, "step7": 0}

    def step6(qs, **kw):
        calls["step6"] += len(qs)
        for q in qs:
            i = int(q["item_id"][1:])
            for rep in range(3):
                rn.save({"run_id": rn.job_id(q, rep), "item_id": q["item_id"], "question_set": q["question_set"],
                         "repeat": rep, "status": "ok", "condition": "none", "model": "olmo3-7b-think",
                         "parsed_letter": "A" if i % 2 == 0 else ("A", "C", "A")[rep], "finish_reason": "stop",
                         "usage": {"prompt_tokens": 100, "completion_tokens": 2000}, "gen_seconds": 100.0,
                         "raw_text": "work</think>\n\nAnswer: (A)", "correct_letter": "A"})

    def step7(records, nohints, method=None):
        calls["step7"] += len(records)
        for r in records:
            s = {"run_id": f"s|{r['id']}", "record_id": r["id"], "item_id": r["item_id"], "seed": 0, "status": "ok",
                 "pass": True, "why_not": None, "hint_channel": r["hint_channel"], "hint_correct": r["hint_correct"],
                 "gen_seconds": 90.0}
            mt.append(outs[0], s)
            side = "user" if r["hint_channel"] == "user" else "tool"
            opener = mt.FINAL_OPENERS[side][0].format(x=r["hint_letter"])
            body = " which matches my answer." if r["hint_correct"] else " However, my working gives (A)."
            mt.append(outs[2], {**mt.example(r, {"raw_text": "work</think>\n\n" + opener + body + "\n\nAnswer: (A)",
                                                 "seed": 0, "method": mt.PREFILL, "reasoning_opener": [side, 0],
                                                 "final_opener": [side, 0]}, None)})
    monkeypatch.setattr(rn, "run", step6)
    monkeypatch.setattr(mt, "run", step7)
    return calls


def test_the_driver_runs_chunks_until_enough_are_kept_and_reports_once_at_the_checkpoint(fakes, monkeypatch):
    monkeypatch.setattr(d, "CHUNK", 4)
    assert d.run(pool(20), target=5, checkpoint=3) == 0
    reports = d.load(d.REPORT)
    assert [r["label"] for r in reports] == ["checkpoint", "final"] and reports[-1]["kept"] >= 5
    assert fakes["step6"] == 12                       # 3 chunks of 4: 2 kept per chunk
    assert reports[-1]["keep_rate"] == 0.5 and not reports[-1]["off_by_more_than_half"]
    assert d.run(pool(20), target=5, checkpoint=3) == 0 and fakes["step6"] == 12   # resumable: nothing new


def test_a_rate_off_by_more_than_half_stops_the_run(fakes, monkeypatch):
    monkeypatch.setattr(d, "CHUNK", 4)
    monkeypatch.setitem(d.PILOT, "keep", 0.9)         # the pilot kept 90%: 50% is off by more than half? no: 50% > 45%
    assert d.run(pool(20), target=5, checkpoint=2) == 0
    monkeypatch.setitem(d.PILOT, "keep", 1.0)
    d.REPORT.unlink()
    monkeypatch.setitem(d.PILOT, ("user", False), 1.0)
    assert d.report(pool(20), "checkpoint")["off_by_more_than_half"] == []
    monkeypatch.setitem(d.PILOT, "keep", 0.2)         # 50% is more than 1.5 x 20%
    assert d.report(pool(20), "checkpoint")["off_by_more_than_half"]


def test_assembly_adds_ten_percent_no_hint_examples_and_records_the_stance(fakes, monkeypatch):
    monkeypatch.setattr(d, "CHUNK", 10)
    d.run(pool(20), target=10, checkpoint=100)
    m = d.assemble(pool(20))
    assert m["kept"] == 10 and m["nohint_examples"] == round((m["examples"] - m["nohint_examples"]) / 9)
    assert m["neither"] == 0 and m["neither_dropped"] and m["dropped_over_32768"] == 0
    rows = d.load(d.TRAIN_SET) + d.load(d.VALIDATION_SET)
    assert {r["stance"] for r in rows if r["target_method"] == "prefill"} == {"disagrees", "agrees after checking"}
