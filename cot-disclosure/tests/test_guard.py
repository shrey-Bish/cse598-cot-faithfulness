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
