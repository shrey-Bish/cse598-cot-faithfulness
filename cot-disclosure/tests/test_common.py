"""Run ids, parse status and Wilson intervals used by the progress scripts."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "progress"))

from common import latest, parse_status, run_id, wilson  # noqa: E402


def test_run_id_is_deterministic_and_distinct():
    a = run_id("expB", "q1", "m", "nocue", None, 0)
    assert a == run_id("expB", "q1", "m", "nocue", None, 0)
    assert a != run_id("expB", "q1", "m", "nocue", None, 1)
    assert len(a) == 16


def test_wilson_reference_values():
    lo, hi = wilson(5, 10)
    assert abs(lo - 0.2366) < 1e-3 and abs(hi - 0.7634) < 1e-3
    lo, hi = wilson(0, 10)
    assert lo == 0.0 and abs(hi - 0.2775) < 1e-3
    assert wilson(0, 0) is None


def test_parse_status():
    assert parse_status({"error": None, "finish": "stop"}, "A") == "ok"
    assert parse_status({"error": None, "finish": "stop"}, None) == "parse_failure"
    assert parse_status({"error": None, "finish": "length"}, "A") == "truncated"
    assert parse_status({"error": "HTTP 500", "finish": "error"}, None) is None


def test_latest_keeps_last_record_per_run():
    rows = [{"run_id": "x", "status": "api_error"}, {"run_id": "x", "status": "ok"}]
    assert latest(rows) == [{"run_id": "x", "status": "ok"}]


def test_make_record_matches_the_schema():
    from common import make_record
    out = {"content": "So it is B.\nAnswer: (B)", "reasoning": "private", "finish": "stop", "usage": {"completion_tokens": 9},
           "error": None, "latency_s": 1.5, "cached": False, "reasoning_field": "reasoning", "retries": 0}
    rec = make_record(out, experiment="ui", item_id=3, model="m", condition="cue_user", repeat=7,
                      messages=[{"role": "user", "content": "q"}], n_options=7, correct_letter="D", cue_letter="B",
                      cue_channel="cue_user", temperature=0.6, max_tokens=100, seed=7)
    assert rec["parsed_letter"] == "B" and rec["parse_rule"] == "answer_colon" and rec["parse_status"] == "ok"
    assert rec["reasoning_text"] == "private" and rec["status"] == "ok" and len(rec["run_id"]) == 16
    assert rec["params"] == {"temperature": 0.6, "max_tokens": 100, "seed": 7, "stream": True}


def test_call_end_to_end_with_stub_client(monkeypatch):
    import logging
    import common
    monkeypatch.setattr(common, "chat", lambda *a, **k: {"content": "Answer: (C)", "reasoning": "", "finish": "stop",
                                                          "usage": {"completion_tokens": 3}, "error": None,
                                                          "latency_s": 0.1, "cached": False, "retries": 0})
    rec = common.call(logging.getLogger("t"), experiment="t", item_id=1, model="m", condition="none", repeat=0,
                      messages=[{"role": "user", "content": "q"}], n_options=7, extra={"x": 1})
    assert rec["parsed_letter"] == "C" and rec["x"] == 1
