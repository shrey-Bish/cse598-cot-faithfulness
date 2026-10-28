"""The power guard (progress/guard.py): battery parsing, the rules, and one pass of pausing,
restarting and finishing jobs. No processes are started."""
import sys
from datetime import datetime
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "progress"))

import guard as g  # noqa: E402

T0 = datetime(2026, 10, 27, 16, 0)
UNTIL = datetime(2026, 10, 27, 17, 15)


def test_battery_parsing():
    assert g.battery("Now drawing from 'Battery Power'\n -InternalBattery-0 (id=1)\t93%; discharging;") == (False, 93)
    assert g.battery("Now drawing from 'AC Power'\n -InternalBattery-0 (id=1)\t100%; charged;") == (True, 100)


def test_the_rules():
    assert g.allowed("local", True, 5, T0) and g.allowed("voyager", True, 5, T0)
    assert g.allowed("local", False, 31, T0, UNTIL) and not g.allowed("local", False, 29, T0, UNTIL)
    assert not g.allowed("local", False, 90, datetime(2026, 10, 27, 17, 30), UNTIL)     # the exception is over
    assert not g.allowed("local", False, 90, T0)                                         # no exception given
    assert g.allowed("voyager", False, 15, T0) and not g.allowed("voyager", False, 14, T0)


class FakeProc:
    def __init__(self, code=None):
        self.returncode, self.pid = code, 1

    def poll(self):
        return self.returncode


def job(spec, tmp_path, monkeypatch):
    monkeypatch.setattr(g, "LOGS", tmp_path)
    j = g.Job(spec)
    started = []
    monkeypatch.setattr(j, "start", lambda on_ac, pct: (started.append(1), setattr(j, "proc", FakeProc())))
    return j, started


def test_pause_below_30_then_resume_on_ac(tmp_path, monkeypatch):
    j, started = job("local:ollama=progress/run_trackB.py --run", tmp_path, monkeypatch)
    g.step([j], False, 80, T0, UNTIL, clock=0)
    assert started == [1]
    g.step([j], False, 29, T0, UNTIL, clock=60)                    # below 30%: graceful pause
    assert j.stop.exists() and started == [1]
    j.proc.returncode = 2                                          # the runner stops after its request
    g.step([j], False, 29, T0, UNTIL, clock=120)
    assert j.proc is None and not j.finished and started == [1]
    g.step([j], True, 29, T0, UNTIL, clock=200)                    # back on the charger
    assert started == [1, 1]


def test_work_left_restarts_and_done_finishes(tmp_path, monkeypatch):
    j, started = job("voyager:qwen=progress/run_trackB.py --run", tmp_path, monkeypatch)
    g.step([j], False, 50, T0, None, clock=0)
    j.proc.returncode = 1                                          # e.g. a request lost to a sleep
    g.step([j], False, 50, T0, None, clock=10)
    assert started == [1]                                          # waits a minute
    g.step([j], False, 50, T0, None, clock=80)
    assert started == [1, 1]
    j.proc.returncode = 0
    g.step([j], False, 50, T0, None, clock=200)
    assert j.finished and started == [1, 1]
    g.step([j], False, 10, T0, None, clock=300)
    assert started == [1, 1]


def test_a_job_with_after_starts_once_that_job_is_done(tmp_path, monkeypatch):
    """Voyager models one after another (Oct 28): never more than one runner's requests in flight."""
    first, s1 = job("voyager:qwen3think=progress/run_trackB.py --run --model a", tmp_path, monkeypatch)
    second, s2 = job("voyager:olmo:qwen3think=progress/run_trackB.py --run --model b", tmp_path, monkeypatch)
    assert (second.kind, second.name, second.after) == ("voyager", "olmo", "qwen3think") and first.after is None
    g.step([first, second], True, 100, T0, None, clock=0)
    assert s1 == [1] and s2 == []
    first.proc.returncode = 1                                      # work left: restarts; the second still waits
    g.step([first, second], True, 100, T0, None, clock=10)
    g.step([first, second], True, 100, T0, None, clock=80)
    assert s1 == [1, 1] and s2 == []
    first.proc.returncode = 0
    g.step([first, second], True, 100, T0, None, clock=200)
    assert first.finished and s2 == [1]


def test_a_failed_voyager_guard_halts_every_voyager_job(tmp_path, monkeypatch):
    """Code 3 (identity canary or model check failed): not restarted; the other Voyager jobs pause and the
    ones waiting on it never start; the guard then has nothing left to do."""
    a, sa = job("voyager:qwen3think=progress/run_trackB.py --run --model a", tmp_path, monkeypatch)
    b, sb = job("voyager:c4=agents/run_team.py --live", tmp_path, monkeypatch)
    c, sc = job("voyager:olmo:qwen3think=progress/run_trackB.py --run --model b", tmp_path, monkeypatch)
    g.step([a, b, c], True, 100, T0, None, clock=0)
    assert sa == [1] and sb == [1] and sc == []
    a.proc.returncode = 3
    g.step([a, b, c], True, 100, T0, None, clock=10)
    assert a.halted and b.stop.read_text() == "Voyager halted"            # the other one pauses gracefully
    b.proc.returncode = 2
    g.step([a, b, c], True, 100, T0, None, clock=200)
    assert sa == [1] and sb == [1] and sc == [] and b.proc is None
    assert all(g.settled(j, [a, b, c]) for j in (a, b, c))
