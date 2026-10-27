"""Keep long runs going on this Mac within Ritik's power rules (Oct 27), and restart them after a sleep.

  nohup caffeinate -i ../.venv/bin/python -u progress/guard.py \\
      --job "voyager:qwen3think=progress/run_trackB.py --run --model qwen3-30b-a3b-thinking-2507" \\
      --job "local:ollama=progress/run_trackB.py --run --model qwen3:8b --order core-first" \\
      --battery-until 2026-10-27T17:15 >> logs/guard.log 2>&1 &
  touch logs/stop_guard        # stop: every job finishes its requests in flight, then the guard exits

Rules (checked every 5 minutes with `pmset -g batt`, and at start):
  local jobs (Ollama: the model runs on this Mac)   on the charger; on battery only before --battery-until
                                                    (an exception Ritik grants) and at 30% or more
  voyager jobs (remote calls)                       on the charger, or on battery at 15% or more
A job that may not run is paused gracefully: its stop file (logs/stop_<name>) makes the runner start no
new job, the requests in flight finish, and it exits (code 2). It restarts when the rules allow again.
A job that exits with work left (code 1: a request lost to a sleep or a dropped connection, never
counted as "no answer") restarts after a minute; code 0 means all its jobs are done. Every start, pause,
resume and end is logged with the battery level (stdout, appended to logs/guard.log).
"""
import argparse
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
PY = CODE.parent / ".venv" / "bin" / "python"
LOGS = CODE / "logs"
BATTERY_EVERY_S = 300
TICK_S = 60
LOCAL_MIN, VOYAGER_MIN = 30, 15


def battery(text=None):
    """(on_ac, percent) from `pmset -g batt`."""
    text = text if text is not None else subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True).stdout
    m = re.search(r"(\d+)%", text)
    return "AC Power" in text, int(m.group(1)) if m else 100


def allowed(kind, on_ac, pct, now, battery_until=None):
    if on_ac:
        return True
    if kind == "local":
        return battery_until is not None and now < battery_until and pct >= LOCAL_MIN
    return pct >= VOYAGER_MIN


def say(msg, on_ac=None, pct=None):
    power = "" if pct is None else f" [{'AC' if on_ac else 'battery'} {pct}%]"
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}{power}", flush=True)


class Job:
    def __init__(self, spec):
        kind_name, cmd = spec.split("=", 1)
        self.kind, self.name = kind_name.split(":", 1)
        if self.kind not in ("local", "voyager"):
            raise ValueError(f"job kind must be local or voyager: {spec}")
        self.cmd = cmd.split()
        self.stop = LOGS / f"stop_{self.name}"
        self.proc, self.finished, self.restart_at = None, False, 0.0

    def start(self, on_ac, pct):
        self.stop.unlink(missing_ok=True)
        log = open(LOGS / f"guard_{self.name}.log", "a")
        self.proc = subprocess.Popen([str(PY), "-u", *self.cmd, "--stop-file", str(self.stop)], cwd=CODE,
                                     stdout=log, stderr=subprocess.STDOUT)
        say(f"start {self.name} (pid {self.proc.pid})", on_ac, pct)

    def pause(self, on_ac, pct, why):
        if self.proc and self.proc.poll() is None and not self.stop.exists():
            self.stop.write_text(why)
            say(f"pause {self.name}: {why}; its requests in flight finish first", on_ac, pct)


def step(jobs, on_ac, pct, now, battery_until, clock):
    """One pass: pause what may not run, notice exits, (re)start what may run."""
    for j in jobs:
        ok = allowed(j.kind, on_ac, pct, now, battery_until)
        running = j.proc is not None and j.proc.poll() is None
        if running and not ok:
            j.pause(on_ac, pct, "battery rule" if not on_ac else "stop")
        if j.proc is not None and j.proc.poll() is not None:
            code = j.proc.returncode
            j.proc = None
            if code == 0:
                j.finished = True
                say(f"done {j.name}: every job finished", on_ac, pct)
            else:
                say(f"{j.name} exited with code {code} ({'paused' if code == 2 else 'work left'})", on_ac, pct)
                j.restart_at = clock + TICK_S
        if j.proc is None and not j.finished and ok and clock >= j.restart_at:
            j.start(on_ac, pct)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--job", action="append", required=True, metavar="KIND:NAME=COMMAND")
    ap.add_argument("--battery-until", help="local jobs may run on battery until this time (ISO, local)")
    a = ap.parse_args(argv)
    LOGS.mkdir(exist_ok=True)
    until = datetime.fromisoformat(a.battery_until) if a.battery_until else None
    jobs = [Job(s) for s in a.job]
    guard_stop = LOGS / "stop_guard"
    guard_stop.unlink(missing_ok=True)
    on_ac, pct = battery()
    say(f"guard started: {', '.join(f'{j.kind}:{j.name}' for j in jobs)}; local jobs on battery until {until}", on_ac, pct)
    last_check = time.monotonic()
    while not all(j.finished for j in jobs):
        clock = time.monotonic()
        if clock - last_check >= BATTERY_EVERY_S:
            on_ac, pct = battery()
            last_check = clock
            say("battery check", on_ac, pct)
        if guard_stop.exists():
            for j in jobs:
                j.pause(on_ac, pct, "guard stop")
            if all(j.proc is None or j.proc.poll() is not None for j in jobs):
                say("guard stopped", on_ac, pct)
                return 0
        else:
            step(jobs, on_ac, pct, datetime.now(), until, clock)
        time.sleep(TICK_S if not guard_stop.exists() else 5)
    say("guard ended: every job done", on_ac, pct)
    return 0


if __name__ == "__main__":
    sys.exit(main())
