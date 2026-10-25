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


def test_boot_diff_resamples_questions_together():
    import pytest
    from common import boot_diff
    a = {q: [1, 1, 0] for q in range(10)}                     # 2 of 3 in every question
    b = {q: [0, 0, 0] for q in range(10)}
    d, lo, hi = boot_diff(a, b)
    assert d == pytest.approx(2 / 3) and lo == pytest.approx(2 / 3) and hi == pytest.approx(2 / 3)
    mixed = {q: [1] if q < 5 else [0] for q in range(10)}       # the gap lives in which questions are drawn
    d, lo, hi = boot_diff(mixed, b)
    assert d == 0.5 and lo < 0.5 < hi and boot_diff(mixed, b) == (d, lo, hi)    # fixed seed: reproducible
    d, lo, hi = boot_diff({0: [1], 1: [1]}, {0: [0], 2: [0]})                    # only shared questions count
    assert (d, lo, hi) == (1.0, 1.0, 1.0)


def test_boot_mean_resamples_questions_together():
    import pytest
    from common import boot_mean
    m, lo, hi = boot_mean({q: [0.2, 0.2] for q in range(8)})
    assert (m, lo, hi) == (pytest.approx(0.2), pytest.approx(0.2), pytest.approx(0.2))
    m, lo, hi = boot_mean({0: [1.0, 1.0, 1.0], 1: [0.0]})                    # pooled over values, not questions
    assert m == 0.75 and lo == 0.0 and hi == 1.0


def test_load_and_append_read_and_write_gzip(tmp_path):
    import gzip
    from common import append, load
    plain, packed = tmp_path / "r.jsonl", tmp_path / "r.jsonl.gz"
    for i in range(3):
        append(plain, {"i": i})
        append(packed, {"i": i})                                    # one gzip member per append
    assert load(packed) == load(plain) == [{"i": 0}, {"i": 1}, {"i": 2}]
    with gzip.open(packed, "rt") as f:                              # a plain gzip reader sees the same lines
        assert [line for line in f] == plain.read_text().splitlines(keepends=True)
    assert load(tmp_path / "missing.jsonl.gz") == []


def test_move_to_gz_copies_every_record_checks_it_then_removes_the_original(tmp_path):
    import pytest
    from common import append, load, move_to_gz
    src = tmp_path / "r.jsonl"
    for i in range(3):
        append(src, {"i": i, "text": "x" * 100})
    n = move_to_gz(src, tmp_path / "r.jsonl.gz", lambda r: {"i": r["i"]}, tmp_path / "r_runs.jsonl")
    assert n == 3 and not src.exists()
    assert load(tmp_path / "r.jsonl.gz") == [{"i": i, "text": "x" * 100} for i in range(3)]
    assert load(tmp_path / "r_runs.jsonl") == [{"i": 0}, {"i": 1}, {"i": 2}]
    append(src, {"i": 9})
    with pytest.raises(FileExistsError):                              # never over an existing copy
        move_to_gz(src, tmp_path / "r.jsonl.gz")
    assert src.exists()


def test_rescore_compares_the_newest_record_per_run_and_keeps_track_a_gating():
    import rescore
    n = {1: 4}
    rows = [{"run_id": "a", "item_id": 1, "final_text": "**Answer**: B", "parsed_letter": None, "parse_rule": "none"},
            {"run_id": "b", "item_id": 1, "final_text": "Answer: (C)", "parsed_letter": "C", "parse_rule": "answer_colon"}]
    assert [(r["run_id"], new) for r, old, new in rescore.rescore(rows, rescore.general, n)] == [("a", ("B", "answer_colon"))]
    rows.append({**rows[0], "parsed_letter": "B"})                       # a re-scored copy supersedes it
    assert rescore.rescore(rows, rescore.general, n) == []
    cut = {"run_id": "c", "item_id": 1, "final_text": "**Answer**: B", "parsed_letter": None, "finish_reason": "length"}
    called = {**cut, "run_id": "d", "finish_reason": "stop", "no_answer_reason": "called the tool again"}
    assert rescore.rescore([cut, called], rescore.track_a, n) == []        # still no answer
