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
