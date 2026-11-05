"""The Sol feeder (tools/sol_feeder.py, Nov 4): keeps the class QoS's queue full from an ordered queue file, through
submit.sh. A fake Sol for the rules (order, references to job ids, no second submission after a restart, a failed
dependency skips its line and alerts, the 10 places, GPU-minutes, the stop file, B20's "again" lines, a commit a line
needs, a sweep with nothing left); the real submit.sh with fake Slurm commands for the wiring; and the real queue
file against the plan. CPU only, no network, no Slurm."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))
sys.path.insert(0, str(CODE / "tests"))
sys.path.insert(0, str(CODE / "tools"))

import sol_feeder as sf  # noqa: E402

ACTIVE = ("PENDING", "RUNNING")


class FakeSol:
    """Slurm in memory: 10 places, 960 running GPU-minutes; a job holds its need while it runs."""

    def __init__(self, places=10, cap=960):
        self.jobs, self.next, self.places, self.cap = {}, 100, places, cap
        self.submitted, self.mails, self.commits, self.left, self.checks = [], [], set(), {}, 0
        self.usage_rows, self.usage_fails = [], False

    @staticmethod
    def need(argv):
        return 150 if argv[0] == "provenance_gen" else 90

    def check(self, argv):
        self.checks += 1
        active = [j for j in self.jobs.values() if j["state"] in ACTIVE]
        if len(active) + 1 > self.places:
            return {"full": True, "refused": "refusing: you would have more than 10 jobs in the QoS"}
        used = sum(j["need"] for j in active if j["state"] == "RUNNING")
        pending = sum(j["need"] for j in active if j["state"] == "PENDING")
        return {"full": False, "refused": None, "need": self.need(argv), "free": self.cap - used, "pending": pending,
                "places": self.places - len(active) - 1}

    def submit(self, argv):
        jid = str(self.next)
        self.next += 1
        comment = next((a.split("=", 1)[1] for a in argv if a.startswith("--comment=")), "")
        self.jobs[jid] = {"state": "PENDING", "exit": "0:0", "need": self.need(argv), "comment": comment}
        self.submitted.append((jid, argv))
        return jid

    def states(self, ids):
        return {i: (self.jobs[i]["state"], self.jobs[i]["exit"]) for i in ids if i in self.jobs}

    def active_comments(self):
        return {j["comment"]: i for i, j in self.jobs.items() if j["state"] in ACTIVE and j["comment"]}

    def has_commit(self, commit):
        return commit in self.commits

    def runs_left(self, spec, argv):
        return self.left.get(spec)

    def mail(self, to, subject, body):
        self.mails.append((to, subject, body))
        return "mailed"

    def usage(self, since):
        if self.usage_fails:
            raise sf.FeederError("sacct failed (code 1): slurm_load_jobs error")
        return list(self.usage_rows)

    # test helpers
    def end(self, jid, state="COMPLETED", exit="0:0"):
        self.jobs[jid].update(state=state, exit=exit)

    def run_all(self):
        for j in self.jobs.values():
            if j["state"] == "PENDING":
                j["state"] = "RUNNING"

    def labels(self):
        return [next(a.split("=", 1)[1] for a in argv if a.startswith("--comment=")).split(":", 1)[1]
                for _, argv in self.submitted]


def feeder(tmp_path, text, sol, **kw):
    kw.setdefault("now", Clock("2026-11-04T03:00:00"))     # before the digest's hour, whenever the tests run (Nov 4)
    return sf.Feeder(sf.parse_queue(text), tmp_path / "state", sol, log_path=tmp_path / "feeder.log",
                     stop_file=tmp_path / "feeder.stop", mail_to="me@example.org", **kw)


def q(*rows):
    return "\n".join(rows) + "\n"


SIX = q(*[f"l{i} | - | a39_1gpu --estimate 1 -- base e2 {i}/16" for i in range(1, 7)])


def test_the_lines_go_in_order_while_places_are_left(tmp_path):
    sol = FakeSol(places=4)
    f = feeder(tmp_path, SIX, sol)
    f.tick()
    assert sol.labels() == ["l1", "l2", "l3", "l4"]                       # 4 places
    f.tick()
    assert len(sol.submitted) == 4                                        # full: nothing more
    sol.end("100")
    sol.end("101", "FAILED", "1:0")
    f.tick()
    assert sol.labels() == ["l1", "l2", "l3", "l4", "l5", "l6"]
    assert all(argv[1] == f"--comment=feeder:{lab}" for (_, argv), lab in zip(sol.submitted, sol.labels()))
    assert "submitted l1 as job 100" in (tmp_path / "feeder.log").read_text()


def test_the_ten_place_limit(tmp_path):
    sol = FakeSol(cap=10_000)
    for i in range(9):
        sol.jobs[str(i)] = {"state": "RUNNING", "exit": "0:0", "need": 90, "comment": ""}
    f = feeder(tmp_path, SIX, sol)
    f.tick()
    assert sol.labels() == ["l1"]                                         # the 10th place only
    f.tick()
    assert sol.labels() == ["l1"]
    assert "full" in (tmp_path / "feeder.log").read_text()


def test_a_line_that_doesnt_fit_the_gpu_minutes_waits_and_holds_the_order(tmp_path):
    sol = FakeSol()
    for i in range(6):                                                    # 6 x 135 = 810 held: 150 left
        sol.jobs[str(i)] = {"state": "RUNNING", "exit": "0:0", "need": 135, "comment": ""}
    text = q("a | - | a39_1gpu --estimate 1 -- base e2 1/16",
             "b | - | provenance_gen --estimate 1.6 -- --b1r2 --part 1/40",
             "c | - | a39_1gpu --estimate 1 -- base e2 2/16")
    f = feeder(tmp_path, text, sol)
    f.tick()
    assert sol.labels() == ["a"]                                          # a (90) fits; then b (150) > 150 - 90 pending
    assert "b waits for GPU-minutes" in (tmp_path / "feeder.log").read_text()


def test_references_become_job_ids_and_dependencies_are_the_feeders(tmp_path):
    sol = FakeSol()
    sol.jobs["999"] = {"state": "RUNNING", "exit": "0:0", "need": 90, "comment": ""}
    text = q("smoke | - | b20 --model granite-4.2-8b -- --smoke",
             "main | afterok=@smoke | b20 --model granite-4.2-8b --estimate 1.1",
             "sweep | afterany=@smoke:999 | a39_1gpu --estimate 1 -- base e2")
    f = feeder(tmp_path, text, sol)
    f.tick()
    assert sol.labels() == ["smoke"]
    assert not any("--dependency" in " ".join(argv) for _, argv in sol.submitted)
    sol.run_all()
    f.tick()
    assert sol.labels() == ["smoke"]                                       # both wait while 100 and 999 run
    status = f.status_text()
    assert "main" in status and "afterok:100" in status and "afterany:100:999" in status
    sol.end("100")
    f.tick()
    assert sol.labels() == ["smoke", "main"]                              # 999 still runs
    sol.end("999", "TIMEOUT", "0:0")
    f.tick()
    assert sol.labels() == ["smoke", "main", "sweep"]                     # afterany: however it ended


def test_no_second_submission_after_a_restart(tmp_path):
    sol = FakeSol()
    feeder(tmp_path, SIX, sol).tick()
    assert len(sol.submitted) == 6
    feeder(tmp_path, SIX, sol).tick()                                     # a new feeder reads the same state
    assert len(sol.submitted) == 6
    # a crash between sbatch and the record: the job's comment recovers it; none found: held, never resubmitted
    state = json.loads((tmp_path / "state" / "state.json").read_text())
    state["lines"]["l6"] = {"status": "submitting", "at": "x"}
    state["lines"]["l5"] = {"status": "submitting", "at": "x"}
    sol.end("104")                                                        # l5's job ended: squeue no longer shows it
    (tmp_path / "state" / "state.json").write_text(json.dumps(state))
    f = feeder(tmp_path, SIX, sol)
    f.tick()
    st = json.loads((tmp_path / "state" / "state.json").read_text())["lines"]
    assert st["l6"]["job"] == "105" and st["l5"]["status"] == "unknown" and len(sol.submitted) == 6
    assert sol.mails and "l5" in sol.mails[-1][2]


def test_a_failed_dependency_skips_its_line_and_alerts_once(tmp_path):
    sol = FakeSol()
    text = q("smoke | - | b20 --model gemma-4-26b-a4b-it -- --smoke",
             "main | afterok=@smoke | b20 --model gemma-4-26b-a4b-it --estimate 1.1",
             "again | again=@main | b20 --model gemma-4-26b-a4b-it --estimate 1.1",
             "other | afterany=@smoke | a39_1gpu --estimate 1 -- base e2")
    f = feeder(tmp_path, text, sol)
    f.tick()
    sol.end("100", "FAILED", "5:0")                                       # the smoke isn't clean (exit 5)
    f.tick()
    f.tick()
    st = json.loads((tmp_path / "state" / "state.json").read_text())["lines"]
    assert st["main"]["status"] == "skipped" and st["again"]["status"] == "skipped"
    assert sol.labels() == ["smoke", "other"]                             # the smoke is never resubmitted
    assert len(sol.mails) == 1 and "FAILED" in sol.mails[0][2] and "main" in sol.mails[0][2]
    assert sol.mails[0][0] == "me@example.org"


def test_b20s_again_lines_run_only_while_runs_are_left(tmp_path):
    sol = FakeSol()
    text = q("run1 | - | b20 --model granite-4.2-8b --estimate 1.1",
             "run2 | again=@run1 | b20 --model granite-4.2-8b --estimate 1.1",
             "run3 | again=@run2 | b20 --model granite-4.2-8b --estimate 1.1")
    f = feeder(tmp_path, text, sol)
    f.tick()
    sol.end("100", "FAILED", "2:0")                                       # stopped at its limit, runs left
    f.tick()
    assert sol.labels() == ["run1", "run2"] and not sol.mails             # a planned stop: no alert
    sol.end("101")                                                        # done
    f.tick()
    st = json.loads((tmp_path / "state" / "state.json").read_text())["lines"]
    assert st["run3"]["status"] == "not needed" and len(sol.submitted) == 2


def test_a_b20_line_that_ran_into_its_limit_counts_as_stopped_there(tmp_path):
    """Nov 4 (468897, b20-granite-r2-1): a B20 job whose requests in flight outlast Slurm's 5-minute warning ends
    TIMEOUT, not exit 2. Its finished runs are saved and its runner resumes, so its next line runs it again, with an
    alert (it didn't stop itself). A job that failed (508647, b20-gemma-r2-1: exit 1) still skips the rest."""
    sol = FakeSol()
    text = q("g1 | - | b20 --model granite-4.2-8b --estimate 1.1",
             "g2 | again=@g1 | b20 --model granite-4.2-8b --estimate 1.1",
             "e1 | - | b20 --model gemma-4-26b-a4b-it --estimate 1.1",
             "e2 | again=@e1 | b20 --model gemma-4-26b-a4b-it --estimate 1.1")
    f = feeder(tmp_path, text, sol)
    f.tick()
    sol.end("100", "TIMEOUT", "0:0")                                      # g1 ran into its limit
    sol.end("101", "FAILED", "1:0")                                       # e1 failed
    f.tick()
    st = json.loads((tmp_path / "state" / "state.json").read_text())["lines"]
    assert sol.labels() == ["g1", "e1", "g2"] and st["e2"]["status"] == "skipped"
    assert any("TIMEOUT" in m[2] and "its next line runs it again" in m[2] for m in sol.mails)


def test_a_line_waits_for_the_commit_it_needs_and_a_sweep_with_nothing_left_isnt_run(tmp_path):
    sol = FakeSol()
    text = q("b1r2 | needs=27a2a39 | provenance_gen --estimate 1.6 -- --b1r2 --part 1/40",
             "sweep | left=a39:base:e2 | a39_1gpu --estimate 1 -- base e2",
             "sweep2 | left=a39:lora:e2 | a39_1gpu --estimate 1 -- lora e2")
    sol.left = {"a39:base:e2": 0, "a39:lora:e2": 12}
    f = feeder(tmp_path, text, sol)
    f.tick()
    assert sol.labels() == ["sweep2"]
    sol.commits.add("27a2a39")
    f.tick()
    assert sol.labels() == ["sweep2", "b1r2"]
    st = json.loads((tmp_path / "state" / "state.json").read_text())["lines"]
    assert st["sweep"]["status"] == "not needed"


def test_a_queue_it_cant_count_ends_the_tick_and_skips_nothing(tmp_path):
    """squeue failing for a moment (submit.sh: "running and pending jobs not checked") is no reason to drop a line."""
    sol = FakeSol()
    real = sol.check
    sol.check = lambda argv: {"full": False, "transient": True, "refused": "submit.sh couldn't count the queue"}
    f = feeder(tmp_path, SIX, sol)
    f.tick()
    assert not sol.submitted and not json.loads((tmp_path / "state" / "state.json").read_text())["lines"]
    sol.check = real
    f.tick()
    assert sol.labels() == ["l1", "l2", "l3", "l4", "l5", "l6"]


def test_the_stop_file_stops_it_cleanly(tmp_path):
    sol = FakeSol()
    f = feeder(tmp_path, SIX, sol)
    (tmp_path / "feeder.stop").write_text("")
    assert f.tick() == "stopped" and not sol.submitted
    assert f.loop(interval=0) == "stopped"                                 # the loop ends too
    assert "stop file" in (tmp_path / "feeder.log").read_text()


def test_dry_run_submits_nothing_and_writes_no_state(tmp_path):
    sol = FakeSol(places=3)
    f = feeder(tmp_path, SIX, sol)
    out = f.tick(dry=True)
    assert out == ["l1", "l2", "l3"] and not sol.submitted and not (tmp_path / "state" / "state.json").exists()


def test_adopt_skip_and_reset(tmp_path):
    sol = FakeSol()
    f = feeder(tmp_path, SIX, sol)
    f.adopt("l1", "457471")
    f.skip("l2", "by hand")
    f.tick()
    assert sol.labels() == ["l3", "l4", "l5", "l6"]
    f.reset("l2")
    f.tick()
    assert sol.labels()[-1] == "l2"


def test_the_queue_names_no_user_and_the_feeder_expands_user(monkeypatch):
    """The kit names no Sol user (test_sol_second_user): the queue file says $USER, and the feeder expands it. The one
    exception (Nov 5) is each queue file's owner line, whose job is to name the account."""
    monkeypatch.setenv("USER", "someone")
    l = sf.parse_queue("a | - | provenance_gen -- --alpha-from /scratch/$USER/trackA/x.json --b1r2\n")[0]
    assert l.argv[-2] == "/scratch/someone/trackA/x.json"
    for p in sf.SOL.glob("queue_*.txt"):
        assert [x for x in p.read_text().splitlines() if "ragarw68" in x] in \
            (["owner: ragarw68"], ["owner: not ragarw68"], []), p.name


@pytest.mark.parametrize("text,err", [
    ("a | - | x\na | - | y\n", "twice"),
    ("a | afterok=@b | x\nb | - | y\n", "earlier line"),
    ("a | colour=red | x\n", "option"),
    ("a | - \n", "LABEL | OPTIONS | ARGUMENTS"),
    ("a | left=a39:base:e3 | x\n", "left="),
])
def test_bad_queue_lines_are_refused_with_their_line(text, err):
    with pytest.raises(sf.QueueError, match=err):
        sf.parse_queue(text)


# ---------------------------------------------------------------- the real queue file
def test_the_queue_file_follows_the_plan():
    lines = sf.parse_queue(sf.QUEUE.read_text())
    labels = [l.label for l in lines]
    done = {l.label: l.opts["job"] for l in lines if "job" in l.opts}
    assert done == {"e2-base-1of4": "426582", "e2-prompt_only-1of4": "428294", "e2-lora-1of4": "428295",
                    "e2-lora_note-1of4": "428296", "e2-base-3of4": "428297", "e2-prompt_only-2of4": "428298",
                    "e2-lora-2of4": "428299", "e2-lora_note-2of4": "428330", "e2-base-2of4": "428332"}
    todo = [l for l in lines if "job" not in l.opts]
    # Nov 5 (the logs' sections 19): B20's lines are on Arsha's account and B1R2's dropped; E2, then A40, then the 30
    groups = [l.label.split("-")[0] for l in lines]
    assert set(groups) <= {"e2", "a40", "m30"} and groups == sorted(groups, key=["e2", "a40", "m30"].index)
    todo = [l for l in todo if not l.label.startswith("a40-")]             # A40's lines: its own tests
    parts = [(l.argv[-3], l.argv[-1]) for l in todo if l.argv[0] == "a39_1gpu" and l.argv[-2] == "e2"
             and l.argv[-1].endswith("/16")]
    assert len(parts) == 56
    # the 00:26 plan's 7 core quarters as sixteenths, and (the A39 log's section 15, Nov 4) the 7 quarters that left
    # runs, as theirs: every quarter but base 2/4 and lora_note 2/4, which finished; quarter k/4 is k, k+4, k+8, k+12
    for system, quarters in {"base": [1, 3, 4], "prompt_only": [1, 2, 3, 4], "lora": [1, 2, 3, 4],
                             "lora_note": [1, 3, 4]}.items():
        mine = sorted(p for s, p in parts if s == system)
        assert mine == sorted(f"{q + 4 * i}/16" for q in quarters for i in range(4)), system
    fifths = [l for l in todo if l.argv[-2] == "e2" and l.argv[-1].endswith("/5")]
    assert len(fifths) == 15
    thirty = [l for l in todo if "mmlupro_30" in l.argv and re.search(r"/\d+$", l.argv[-1])]
    assert len(thirty) == 22
    # every sweep waits for every part of its system, and runs only if runs are left
    for l in todo:
        if l.argv[0] == "a39_1gpu" and not re.search(r"/\d+$", l.argv[-1]):
            system, qset = l.argv[-2], l.argv[-1]
            refs = set(l.opts["afterany"].split(":"))
            want = {"@" + x.label for x in lines if x.argv[0] == "a39_1gpu" and x.argv[-3] == system
                    and x.argv[-2] == qset and re.search(r"/\d+$", x.argv[-1])}
            assert refs == want and l.opts["left"] == f"a39:{system}:{qset}", l.label
    assert len(labels) == len(set(labels))
    for l in todo:                                                         # each one passes submit.sh's own checks
        assert l.argv[0] == "a39_1gpu" and "--" not in l.opts


def test_runs_left_counts_what_resume_would_run(tmp_path):
    from common import append
    from finetune import eval as ev
    out = tmp_path / "a39"
    out.mkdir()
    js = ev.jobs((1, 16), "e2", "a39", "base")
    for j in js[:30]:
        append(out / "eval_base_a39_e2_p1of16_runs.jsonl", {"run_id": ev.job_id("base", j), "status": "ok",
                                                             "system": "base"})
    left = sf.runs_left_here(f"a39:base:e2:1/16", [], tmp_path)
    assert left == len(js) - 30
    assert sf.runs_left_here("a39:base:e2", [], tmp_path) == len(ev.jobs(None, "e2", "a39", "base")) - 30


# ---------------------------------------------------------------- the wiring: the real submit.sh, fake Slurm commands
def test_one_tick_through_the_real_submit_sh(tmp_path):
    from test_trackA_gpu_kit import fake_sbatch
    env, log = fake_sbatch(tmp_path)
    bin_dir = tmp_path / "bin"
    (bin_dir / "squeue").write_text("#!/bin/bash\nexit 0\n")              # no jobs
    (bin_dir / "squeue").chmod(0o755)
    (bin_dir / "sacct").write_text("#!/bin/bash\necho '1|PENDING|0:0'\n")
    (bin_dir / "sacct").chmod(0o755)
    text = q("one | - | a39_1gpu --estimate 1 -- base e2 3/16", "two | afterok=@one | a39_1gpu --estimate 1 -- base e2 7/16")
    sol = sf.Sol(env=env)
    f = sf.Feeder(sf.parse_queue(text), tmp_path / "state", sol, log_path=tmp_path / "feeder.log",
                  stop_file=tmp_path / "feeder.stop", mail_to="none")
    f.tick()
    args = log.read_text().split()
    assert "--comment=feeder:one" in args and args[-3:] == ["base", "e2", "3/16"] and "--mail-type=FAIL" in args
    st = json.loads((tmp_path / "state" / "state.json").read_text())
    assert st["lines"]["one"]["job"] == "1" and "two" not in st["lines"]


# ---------------------------------------------------------------- Nov 4 overnight: --status, the digest
# (B20's reruns, b20-*-smoke-r2 and b20-*-r2-K, left this file on Nov 5 with every B20 line: the B20 log's section 19.
# Their tests went with them; test_trackB_b20.py checks B20's own queue file, whose first lines need a commit that has
# both amendments, 2361152 and 063bc78.)
class Clock:
    """A settable local time for the digest and the health check."""

    def __init__(self, text):
        from datetime import datetime
        self.t = datetime.fromisoformat(text).astimezone()

    def __call__(self):
        return self.t

    def add(self, **kw):
        from datetime import timedelta
        self.t = self.t + timedelta(**kw)


def test_status_shows_sacct_state_and_exit_for_every_job_and_never_a_question_mark(tmp_path):
    sol = FakeSol()
    f = feeder(tmp_path, SIX, sol)
    f.adopt("l1", "457471")                                               # no tick yet: the state knows no job state
    sol.jobs["457471"] = {"state": "FAILED", "exit": "5:0", "need": 90, "comment": ""}
    f.adopt("l2", "999")                                                  # sacct doesn't know it
    text = f.status_text()
    row = next(x for x in text.splitlines() if x.startswith("l1 "))
    assert "FAILED" in row and "exit 5:0" in row and "?" not in text
    assert "not known to sacct" in next(x for x in text.splitlines() if x.startswith("l2 "))


def test_status_says_whether_a_needed_commit_is_on_sol(tmp_path):
    """Nov 4, 12:52: after Ritik's pull brought 063bc78, --status still printed "to submit (needs 063bc78)" beside
    Nemotron's second smoke, which reads as waiting for a pull; it was waiting for a place. It now says which."""
    sol = FakeSol()
    f = feeder(tmp_path, q("l1 | needs=063bc78 | b20 --model x -- --smoke", "l2 | needs=abc1234 | b20 --model y"), sol)
    sol.commits.add("063bc78")
    rows = {x.split()[0]: x for x in f.status_text().splitlines() if x.startswith("l")}
    assert rows["l1"].endswith("(needs 063bc78: on Sol)") and rows["l2"].endswith("(needs abc1234: not on Sol yet)")


def test_status_piped_to_head_ends_quietly(tmp_path):
    queue = tmp_path / "q.txt"
    queue.write_text(q("owner: someone", *[f"line-{i:05d} | - | a39_1gpu --estimate 1 -- base e2 {i % 16 + 1}/16"
                                           for i in range(4000)]))
    env = {**os.environ, "PATH": str(tmp_path / "nobin"), "USER": "someone"}   # no sacct here: nothing to ask
    p1 = subprocess.Popen([sys.executable, str(CODE / "tools" / "sol_feeder.py"), "--status", "--queue", str(queue),
                           "--out", str(tmp_path / "out")], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    p2 = subprocess.Popen(["head", "-1"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    first = p2.communicate()[0].decode()
    err = p1.stderr.read().decode()
    p1.wait()
    assert first.startswith("last tick") and "BrokenPipeError" not in err and "Traceback" not in err, err


def test_status_into_a_pipe_whose_reader_left_ends_quietly(tmp_path):
    """Nov 4, 10:18 on Sol: `--status | head -40` still printed "Exception ignored ... BrokenPipeError". The output was
    small enough to wait in Python's buffer until exit, so the error came at the final flush, outside the try."""
    queue = tmp_path / "q.txt"
    queue.write_text(q("owner: someone", *[f"line-{i:02d} | - | a39_1gpu --estimate 1 -- base e2 {i % 16 + 1}/16"
                                           for i in range(60)]))
    env = {**os.environ, "PATH": str(tmp_path / "nobin"), "USER": "someone"}   # no sacct here: nothing to ask
    p = subprocess.Popen([sys.executable, str(CODE / "tools" / "sol_feeder.py"), "--status", "--queue", str(queue),
                          "--out", str(tmp_path / "out")], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    p.stdout.close()                                                      # the reader leaves before a byte is written
    err = p.stderr.read().decode()
    assert p.wait() == 0 and "BrokenPipeError" not in err and "Exception ignored" not in err, err


def test_the_daily_digest_goes_once_a_day_after_seven(tmp_path):
    sol = FakeSol()
    clock = Clock("2026-11-05T06:50:00")
    text = q("e2-a | - | a39_1gpu --estimate 1 -- base e2 3/16", "e2-b | - | a39_1gpu --estimate 1 -- base e2 4/16",
             "b20-x | - | b20 --model granite-4.2-8b --estimate 1.1")
    f = feeder(tmp_path, text, sol, now=clock)
    f.tick()
    sol.end("100")                                                        # e2-a done, e2-b failed, b20-x runs
    sol.end("101", "FAILED", "1:0")
    sol.run_all()
    sol.usage_rows = [{"job": "100", "start": clock.t.timestamp() - 3600, "end": clock.t.timestamp(), "gpus": 1},
                      {"job": "102", "start": clock.t.timestamp() - 1800, "end": None, "gpus": 1}]
    sol.mails.clear()
    f.tick()                                                              # 06:50: not yet
    assert not any("digest" in s for _, s, _ in sol.mails)
    clock.add(minutes=12)                                                 # 07:02
    f.tick()
    digests = [(s, b) for _, s, b in sol.mails if "digest" in s]
    assert len(digests) == 1
    body = digests[0][1]
    for want in ("finished in the last 24 h", "e2-a", "failed in the last 24 h", "e2-b", "running", "b20-x",
                 "GPU-hours in the last 24 h: 1.7", "A39 on E2", "B20"):
        assert want in body, want
    clock.add(minutes=5)
    f.tick()
    assert len([s for _, s, _ in sol.mails if "digest" in s]) == 1        # once a day
    clock.add(days=1)
    f.tick()
    assert len([s for _, s, _ in sol.mails if "digest" in s]) == 2
    assert "digest mailed" in (tmp_path / "feeder.log").read_text()


def test_a_gap_of_over_30_minutes_between_ticks_is_said_in_the_log_the_status_and_the_digest(tmp_path):
    sol = FakeSol()
    clock = Clock("2026-11-05T05:00:00")
    f = feeder(tmp_path, SIX, sol, now=clock)
    f.tick()
    clock.add(minutes=10)
    f.tick()
    assert "minutes since the last tick" not in (tmp_path / "feeder.log").read_text()
    clock.add(minutes=47)                                                 # the scrontab job waited at Priority
    f.tick()
    log = (tmp_path / "feeder.log").read_text()
    assert "47 minutes since the last tick" in log and "nohup" in log
    clock.add(minutes=40)
    assert "40 minutes ago" in f.status_text() and "late" in f.status_text()
    clock.add(hours=2)                                                    # 07:37: the digest lists the gaps
    f.tick()
    body = next(b for _, s, b in sol.mails if "digest" in s)
    assert "gaps over 30 minutes" in body and "47 min" in body


def test_a_digest_that_fails_never_stops_the_tick(tmp_path):
    sol = FakeSol()
    sol.usage = lambda since: 1 / 0
    f = feeder(tmp_path, SIX, sol, now=Clock("2026-11-05T07:10:00"))
    assert f.tick() == ["l1", "l2", "l3", "l4", "l5", "l6"]
    body = next(b for _, s, b in sol.mails if "digest" in s)
    assert "The digest failed" in body and "ZeroDivisionError" in body
    assert json.loads((tmp_path / "state" / "state.json").read_text())["heartbeat"]["at"].startswith("2026-11-05 07:10")


# ---------------------------------------------------------------- Nov 4 morning: exit 138 at the warning (job 460114)
def a39_job(tmp_path, saved, warn=True, own_exit=None):
    """The real a39_1gpu.sbatch over a fake run.sh that "saves" `saved` of part 4/16's prompt_only runs and then, on
    Slurm's warning, ends 138 as 460114's did (or ends `own_exit` by itself). The runs are counted by the real
    finetune/eval.py from TRACKA_CODE. Returns (exit code, the job's output)."""
    import signal
    import time
    from common import append
    from finetune import eval as ev
    repo = tmp_path / "repo"
    sol = repo / "cot-disclosure" / "finetune" / "gpu" / "sol"
    sol.mkdir(parents=True)
    (sol / "a39_1gpu.sbatch").write_text((CODE / "finetune" / "gpu" / "sol" / "a39_1gpu.sbatch").read_text())
    started = tmp_path / "started"
    (sol / "run.sh").write_text("#!/bin/bash\ntrap 'exit 138' USR1\ntouch %s\n%s\nwhile true; do sleep 0.1; done\n"
                                % (started, "exit %d" % own_exit if own_exit is not None else ""))
    (sol / "run.sh").chmod(0o755)
    out = tmp_path / "out"
    (sol / "env.sh").write_text(f"TRACKA_PY={sys.executable}\nTRACKA_CODE={CODE}\nTRACKA_OUT={out}\n")
    js = ev.jobs((4, 16), "e2", "a39", "prompt_only")
    (out / "a39").mkdir(parents=True)
    for j in js[:saved]:
        append(out / "a39" / (ev.stem("prompt_only", (4, 16), "e2", "a39") + "_runs.jsonl"),
               {"run_id": ev.job_id("prompt_only", j), "status": "ok", "system": "prompt_only"})
    env = {**{k: v for k, v in os.environ.items() if not k.startswith("SLURM_")}, "SLURM_SUBMIT_DIR": str(repo)}
    p = subprocess.Popen(["bash", str(sol / "a39_1gpu.sbatch"), "prompt_only", "e2", "4/16"], env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for _ in range(100):
        if started.exists() or p.poll() is not None:
            break
        time.sleep(0.05)
    time.sleep(0.2)                                                       # the job script is in its wait
    if warn and p.poll() is None:
        p.send_signal(signal.SIGUSR1)                                     # --signal=B:USR1: the batch shell only
    text = p.communicate(timeout=60)[0]
    return p.returncode, text, len(js)


def test_a_job_warned_after_its_last_run_is_saved_exits_0(tmp_path):
    rc, text, n = a39_job(tmp_path, saved=None)
    assert n == 90 and rc == 0, text
    assert "after Slurm's warning, with none of the part's runs left: the job exits 0" in text


def test_a_job_warned_with_runs_left_keeps_its_exit_and_says_how_many(tmp_path):
    rc, text, n = a39_job(tmp_path, saved=60)
    assert rc == 138 and "runs left: 30" in text, text


def test_a_job_that_ends_by_itself_keeps_its_exit_code(tmp_path):
    rc, text, _ = a39_job(tmp_path, saved=None, warn=False, own_exit=3)  # every run saved, but no warning came
    assert rc == 3 and "warning" not in text, text


def test_an_a39_part_that_ends_138_with_all_its_runs_saved_is_done(tmp_path):
    """Nov 4: 460114 (e2-prompt_only-4of16) saved 90 of 90, then ended FAILED, exit 138 (the warning, as it ended).
    The feeder counts the part's runs (left=a39:prompt_only:e2:4/16, finetune/eval.py's resume): none left is done."""
    sol = FakeSol()
    f = feeder(tmp_path, q("po4 | - | a39_1gpu --estimate 1 -- prompt_only e2 4/16",
                           "after | afterok=@po4 | a39_1gpu --estimate 1 -- base e2 5/16"), sol)
    f.tick()
    sol.left["a39:prompt_only:e2:4/16"] = 0
    sol.end("100", "FAILED", "138:0")
    f.tick()
    st = json.loads((tmp_path / "state" / "state.json").read_text())
    assert st["jobs"]["100"]["saved"] is True and st["alerts"] == [] and sol.mails == []
    assert sol.labels() == ["po4", "after"]                               # afterok: it counts as done
    log = (tmp_path / "feeder.log").read_text()
    assert "exit 138 at Slurm's warning with all its runs saved: done" in log
    row = next(x for x in f.status_text().splitlines() if x.startswith("po4 "))
    assert "done: exit 138 at the warning, all its runs saved" in row and "1 ok" in f.status_text()


def test_an_a39_part_that_ends_138_with_runs_left_is_an_alert_with_the_count(tmp_path):
    sol = FakeSol()
    f = feeder(tmp_path, q("po4 | - | a39_1gpu --estimate 1 -- prompt_only e2 4/16"), sol)
    f.tick()
    sol.left["a39:prompt_only:e2:4/16"] = 30
    sol.end("100", "FAILED", "138:0")
    f.tick()
    st = json.loads((tmp_path / "state" / "state.json").read_text())
    assert "saved" not in st["jobs"]["100"] and st["jobs"]["100"]["left"] == 30
    assert [a["text"] for a in st["alerts"]] == ["job 100 (po4) ended FAILED, exit 138:0; 30 of its runs left"]


def test_a_part_that_completes_with_runs_left_says_so_without_an_alert(tmp_path):
    """A part stopped at its limit exits 0 (eval_job's stop) when the race doesn't hit: the log says how many are left,
    for the sweep, so a limit that is too short shows."""
    sol = FakeSol()
    f = feeder(tmp_path, q("po4 | - | a39_1gpu --estimate 1 -- prompt_only e2 4/16",
                           "b1 | - | provenance_gen --estimate 1.6 -- --alpha-from /x.json --b1r2 --part 3/40"), sol)
    f.tick()
    sol.left.update({"a39:prompt_only:e2:4/16": 12, "b1r2:3/40": 0})
    sol.end("100")
    sol.end("101")
    f.tick()
    log = (tmp_path / "feeder.log").read_text()
    assert "job 100 (po4) done; 12 of its runs left (stopped at its limit?)\n" in log
    assert "job 101 (b1) done\n" in log                                  # none left: nothing to say
    assert json.loads((tmp_path / "state" / "state.json").read_text())["alerts"] == []


def test_a_part_that_ended_138_before_this_check_is_checked_once(tmp_path):
    """460114's alert came at 06:55, before this check existed: the next tick counts its runs once, and calls it
    done if none are left (the old alert stays in the log)."""
    sol = FakeSol()
    f = feeder(tmp_path, q("po4 | job=460114 | a39_1gpu --estimate 1 -- prompt_only e2 4/16"), sol)
    sol.jobs["460114"] = {"state": "FAILED", "exit": "138:0", "need": 90, "comment": ""}
    st = {"lines": {"po4": {"job": "460114", "how": "submitted", "at": "x"}},
          "jobs": {"460114": {"state": "FAILED", "exit": "138:0", "ended": "x", "ended_ts": 1.0}},
          "alerts": [{"at": "x", "text": "job 460114 (po4) ended FAILED, exit 138:0"}]}
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "state.json").write_text(json.dumps(st))
    sol.left["a39:prompt_only:e2:4/16"] = 0
    f.tick()
    sol.left["a39:prompt_only:e2:4/16"] = 5                               # never counted again
    f.tick()
    st = json.loads((tmp_path / "state" / "state.json").read_text())
    assert st["jobs"]["460114"]["saved"] is True and len(st["alerts"]) == 1
    assert "job 460114 (po4): exit 138 at Slurm's warning with all its runs saved: done" in (tmp_path / "feeder.log").read_text()


def test_every_a39_and_b1r2_line_in_the_queue_has_a_countable_spec():
    lines = sf.parse_queue(sf.QUEUE.read_text())
    for l in lines:
        spec = sf.spec_of(l)
        if l.argv[0] == "a39_1gpu" or "--b1r2" in l.argv:
            assert spec and sf.LEFT.match(spec), l.label
            if "left" in l.opts:                                          # a sweep counts what its own left= counts
                assert spec == l.opts["left"], l.label
        else:
            assert spec is None, l.label
    assert sf.spec_of(next(l for l in lines if l.label == "e2-prompt_only-4of16")) == "a39:prompt_only:e2:4/16"


def test_a39_parts_not_yet_submitted_get_2_00_and_the_sweeps_3_00():
    """The A39 log's section 14 (Nov 4, 10:43): a sixteenth took 1:24:54 of its 1:30 (460114), so the parts not yet
    submitted by 10:15 get 2:00 and the sweeps, whose size is the leftovers, 3:00; the 16 sixteenths already submitted
    keep their 1:30. Section 15's 28 sixteenths (the quarters' leftovers) get 2:00 as well."""
    lines = sf.parse_queue(sf.QUEUE.read_text())
    a39 = [l for l in lines if l.argv[0] == "a39_1gpu" and "job" not in l.opts]
    first = next(i for i, l in enumerate(a39) if l.label == "e2-lora_note-11of16")
    assert {sf.limit_hours(l.argv) for l in a39[:first]} == {1.5} and len(a39[:first]) == 16
    later = a39[first:]
    assert {sf.limit_hours(l.argv) for l in later if "left" not in l.opts} == {2.0}
    assert {sf.limit_hours(l.argv) for l in later if "left" in l.opts} == {3.0}
    assert sum("left" not in l.opts for l in later) == 49 + 28 and sum("left" in l.opts for l in later) == 14


NOV6 = q("e2-base-1of16 | - | a39_1gpu --estimate 1.5 -- base e2 1/16",
         "b20-g-1 | - | b20 --model granite-4.2-8b --estimate 1.1",
         "b20-g-2 | again=@b20-g-1 | b20 --model granite-4.2-8b --estimate 1.1",
         "e2-base-sweep | afterany=@e2-base-1of16 left=a39:base:e2 | a39_1gpu --estimate 2.3 -- base e2",
         "m30-base-1of4 | dropif=nov6 | a39_1gpu --estimate 1.5 -- base mmlupro_30 1/4",
         "b1r2-01of40 | holdif=nov6 | provenance_gen --estimate 1.6 -- --b1r2 --part 1/40")


def nov6_usage(sol, hours_in_window):
    """One job of 1 GPU that ran from an hour before Nov 4 12:36 until HOURS after it, and one of 2 GPUs still running
    from an hour before Nov 6 07:00: the window counts HOURS + 2."""
    a, b = sf.sacct_time("2026-11-04T12:36:00"), sf.sacct_time("2026-11-06T07:00:00")
    sol.usage_rows = [{"job": "1", "start": a - 3600, "end": a + hours_in_window * 3600, "gpus": 1},
                      {"job": "2", "start": b - 3600, "end": None, "gpus": 2}]


def test_nov6_under_10_gpu_hours_drops_the_30_and_holds_b1r2(tmp_path):
    """The A39 log's section 16 (Nov 4): at the first tick at or after Nov 6 07:00, the GPU-hours Sol delivered to
    Ritik's jobs from Nov 4 12:36 to Nov 6 07:00 decide, once. Under 10: the 30's lines are dropped, and B1R2's wait
    until E2's sweeps and B20's lines are submitted or settled. Jobs running across 07:00 count up to 07:00 only."""
    sol, clock = FakeSol(places=2), Clock("2026-11-06T06:55:00")
    f = feeder(tmp_path, NOV6, sol, now=clock)
    nov6_usage(sol, 3)                                                    # 3 + 2 = 5 GPU-hours
    f.tick()                                                              # 06:55: no decision yet
    assert sol.labels() == ["e2-base-1of16", "b20-g-1"]
    assert not json.loads((tmp_path / "state" / "state.json").read_text()).get("decisions")
    sol.mails.clear()
    sol.places = 6                                                        # room for everything from here
    clock.add(minutes=7)                                                  # 07:02: the digest's tick
    f.tick()
    st = json.loads((tmp_path / "state" / "state.json").read_text())
    assert st["decisions"]["nov6"]["branch"] == "cut" and st["decisions"]["nov6"]["gpu_hours"] == 5.0
    assert st["lines"]["m30-base-1of4"]["status"] == "dropped"
    assert "b1r2-01of40" not in st["lines"] and "b1r2-01of40" not in sol.labels()      # held, with places free
    alerts = [b for _, subj, b in sol.mails if "alert" in subj]
    assert alerts and "decision nov6" in alerts[0] and "5.0 GPU-hours" in alerts[0]
    assert "decision nov6" in next(b for _, subj, b in sol.mails if "digest" in subj)
    assert "decision nov6" in f.status_text() and "cut" in f.status_text()
    nov6_usage(sol, 40)                                                   # made once: later usage changes nothing
    sol.end("100")
    sol.end("101")                                                        # b20-g-1 finished: b20-g-2 isn't needed
    f.tick()                                                              # the sweep goes in, b20-g-2 is settled,
    assert sol.labels()[-2:] == ["e2-base-sweep", "b1r2-01of40"]          # so B1R2 goes right after it
    assert json.loads((tmp_path / "state" / "state.json").read_text())["decisions"]["nov6"]["gpu_hours"] == 5.0


def test_nov6_with_10_gpu_hours_or_more_cuts_nothing(tmp_path):
    sol, clock = FakeSol(places=2), Clock("2026-11-06T06:55:00")
    f = feeder(tmp_path, NOV6, sol, now=clock)
    nov6_usage(sol, 8)                                                    # 8 + 2 = 10: not under 10
    f.tick()
    clock.add(minutes=7)
    f.tick()
    st = json.loads((tmp_path / "state" / "state.json").read_text())
    assert st["decisions"]["nov6"]["branch"] == "no cut" and st["decisions"]["nov6"]["gpu_hours"] == 10.0
    sol.end("100")
    sol.end("101")
    f.tick()
    f.tick()
    assert "m30-base-1of4" in sol.labels() and "dropped" not in json.dumps(st["lines"])


def test_nov6_waits_a_tick_when_sacct_fails(tmp_path):
    """A failed sacct must not read as no GPU-hours (a cut): the decision waits for the next tick, same window."""
    sol, clock = FakeSol(places=2), Clock("2026-11-06T07:01:00")
    f = feeder(tmp_path, NOV6, sol, now=clock)
    nov6_usage(sol, 30)
    sol.usage_fails = True
    f.tick()
    st = json.loads((tmp_path / "state" / "state.json").read_text())
    assert "nov6" not in st.get("decisions", {}) and "decision nov6 waits" in (tmp_path / "feeder.log").read_text()
    sol.usage_fails = False
    clock.add(minutes=5)
    f.tick()
    assert json.loads((tmp_path / "state" / "state.json").read_text())["decisions"]["nov6"]["branch"] == "no cut"


def test_the_queue_tags_the_30_to_drop_by_nov6_and_nov11_and_holds_nothing():
    """The A39 log's sections 16 and 17: the 30's 29 lines carry dropif=nov6:nov11, and nothing else does. B1R2's 44
    lines, which carried holdif=nov6, were dropped on Nov 5 (section 19): no line is held now."""
    lines = sf.parse_queue(sf.QUEUE.read_text())
    drop = {l.label for l in lines if l.opts.get("dropif") == "nov6:nov11"}
    assert drop == {l.label for l in lines if "mmlupro_30" in l.argv} and len(drop) == 29
    assert not [l.label for l in lines if "holdif" in l.opts or ("dropif" in l.opts and l.label not in drop)]
    with pytest.raises(sf.QueueError, match="no such decision"):
        sf.parse_queue("x | dropif=nov7 | a39_1gpu -- base e2 1/16\n")


NOV11 = q("e2-base-1of16 | - | a39_1gpu --estimate 1.5 -- base e2 1/16",            # Nov 5: E2 and A40 (section 19)
          "e2-base-sweep | afterany=@e2-base-1of16 left=a39:base:e2 | a39_1gpu --estimate 2.3 -- base e2",
          "a40-e2-1of4 | - | a39_1gpu --estimate 1.5 -- a40 e2 1/4",
          "m30-base-1of4 | dropif=nov6:nov11 | a39_1gpu --estimate 1.5 -- base mmlupro_30 1/4")


def test_nov11_drops_the_30_when_e2_or_a40_isnt_finished(tmp_path):
    """The A39 log's section 10.2, applied by the feeder (sections 17 and 19): at the first tick at or after Nov 11
    09:00, if any E2 or A40 line has no ended job and isn't settled, the 30's lines are dropped ("not run: no GPU time
    by Nov 12"). Lines already submitted run on. Nov 6's decision came out no cut here."""
    sol, clock = FakeSol(places=2), Clock("2026-11-06T07:01:00")
    f = feeder(tmp_path, NOV11, sol, now=clock)
    nov6_usage(sol, 30)
    f.tick()                                                              # Nov 6: no cut; e2 and a40-e2-1of4 go in
    clock.add(days=5, hours=2)                                            # Nov 11 09:01; both still run
    f.tick()
    st = json.loads((tmp_path / "state" / "state.json").read_text())
    assert st["decisions"]["nov6"]["branch"] == "no cut" and st["decisions"]["nov11"]["branch"] == "cut"
    assert st["lines"]["m30-base-1of4"]["status"] == "dropped" and "nov11" in st["lines"]["m30-base-1of4"]["why"]
    assert "decision nov11" in f.status_text()


def test_nov11_keeps_the_30_when_e2_and_a40_are_finished(tmp_path):
    sol, clock = FakeSol(places=2), Clock("2026-11-11T08:50:00")
    f = feeder(tmp_path, NOV11, sol, now=clock)
    nov6_usage(sol, 30)                                                   # Nov 6's decision (made now): no cut
    f.tick()
    sol.end("100")
    sol.end("101")                                                        # A40's line finished
    sol.left["a39:base:e2"] = 0                                           # E2's sweep: nothing left, settled now
    clock.add(minutes=15)                                                 # 09:05
    f.tick()
    st = json.loads((tmp_path / "state" / "state.json").read_text())
    assert st["decisions"]["nov11"]["branch"] == "no cut" and "m30-base-1of4" in sol.labels()


def test_a_line_can_name_two_decisions():
    lines = sf.parse_queue("x | dropif=nov6:nov11 | a39_1gpu -- base mmlupro_30 1/4\n")
    assert lines[0].opts["dropif"] == "nov6:nov11"
    with pytest.raises(sf.QueueError, match="no such decision"):
        sf.parse_queue("x | dropif=nov6:nov12 | a39_1gpu -- base mmlupro_30 1/4\n")



# ---------------------------------------------------------------- Nov 5: one queue file a Sol account (the owner line)
OWNED = "# a comment\n\nowner: %s\nl1 | - | a39_1gpu --estimate 1 -- base e2 1/16\n"
QUEUES = sorted(sf.SOL.glob("queue_*.txt"))
B20_QUEUE = sf.SOL / "queue_b20_2026-11-05.txt"


@pytest.mark.parametrize("owner,user,refused", [("alice", "alice", False), ("alice", "bob", True),
                                                ("not alice", "bob", False), ("not alice", "alice", True)])
def test_the_feeder_uses_only_a_queue_its_user_owns(tmp_path, monkeypatch, capsys, owner, user, refused):
    """Nov 5 (the B20 log's section 19): B20 runs on Arsha's account from a queue file of its own, A39 and A40 on
    Ritik's; no line is ever submitted from both. A queue's first line that isn't a comment names its owner ("owner:
    USER", or "owner: not USER"), and the feeder does nothing with a queue that isn't its user's."""
    monkeypatch.setenv("USER", user)
    queue = tmp_path / "q.txt"
    queue.write_text(OWNED % owner)
    argv = ["--status", "--queue", str(queue), "--out", str(tmp_path / "out")]
    if refused:
        with pytest.raises(SystemExit) as e:
            sf.main(argv)
        msg = str(e.value.code)
        assert e.value.code not in (0, None) and user in msg and f"owner: {owner}" in msg and "--queue" in msg
    else:
        assert sf.main(argv) == 0 and "1 lines: 1 to submit" in capsys.readouterr().out


@pytest.mark.parametrize("mode", [["--once"], ["--loop"], ["--dry-run"], ["--status"], ["--adopt", "l1", "5"],
                                  ["--skip", "l1"], ["--reset", "l1"]], ids=lambda m: m[0])
def test_a_queue_not_yours_or_with_no_owner_is_refused_in_every_mode_before_anything(tmp_path, monkeypatch, mode):
    monkeypatch.setenv("USER", "bob")
    out = tmp_path / "out"
    out.mkdir()
    (out / "feeder.stop").write_text("")                                  # were it not refused: a tick that does nothing
    for text in (OWNED % "alice", OWNED % "not bob", "l1 | - | a39_1gpu --estimate 1 -- base e2 1/16\n"):
        queue = tmp_path / "q.txt"
        queue.write_text(text)
        with pytest.raises(SystemExit) as e:
            sf.main([*mode, "--queue", str(queue), "--out", str(out)])
        assert e.value.code not in (0, None) and "owner" in str(e.value.code)
        assert sorted(p.name for p in out.iterdir()) == ["feeder.stop"]  # no log, no state


def test_the_owner_line_comes_first_and_is_not_a_job():
    assert [l.label for l in sf.parse_queue(OWNED % "alice")] == ["l1"]
    assert sf.owner_of(OWNED % "alice") == ("alice", False) and sf.owner_of(OWNED % "not alice") == ("alice", True)
    with pytest.raises(sf.QueueError, match="owner"):
        sf.parse_queue("l1 | - | a39_1gpu -- base e2 1/16\nowner: alice\n")
    with pytest.raises(sf.QueueError, match="owner"):
        sf.owner_of("l1 | - | a39_1gpu -- base e2 1/16\n")
    assert sf.refusal(OWNED % "alice", "alice") is None and "alice" in sf.refusal(OWNED % "alice", "bob")


def test_every_queue_file_names_its_owner_and_no_label_is_in_two():
    """Ritik's file is his; B20's is for any account but his, for good (a tracked file names no other Sol user; Arsha's
    feeder runs it). So no one runs both, and no label is in two files."""
    assert {p.name for p in QUEUES} >= {sf.QUEUE.name, B20_QUEUE.name}
    texts = {p.name: p.read_text() for p in QUEUES}
    assert sf.owner_of(texts[sf.QUEUE.name]) == ("ragarw68", False)
    assert sf.owner_of(texts[B20_QUEUE.name]) == ("ragarw68", True)
    for user in ("ragarw68", "arsha"):
        assert len([n for n, t in texts.items() if sf.refusal(t, user) is None]) <= 1, user
    labels = [l.label for t in texts.values() for l in sf.parse_queue(t)]
    assert len(labels) == len(set(labels))


def test_ritiks_queue_has_no_b20_line_and_no_queue_has_a_b1r2_line():
    """The B20 log's section 19 (B20 moves to Arsha's account) and the A39 log's section 19 (B1R2 dropped)."""
    lines = sf.parse_queue(sf.QUEUE.read_text())
    assert not [l.label for l in lines if l.label.startswith("b20-") or l.argv[0] in ("b20", "get_b20")]
    for p in QUEUES:
        bad = [l.label for l in sf.parse_queue(p.read_text())
               if l.label.startswith("b1r2-") or l.argv[0] == "provenance_gen" or "--b1r2" in l.argv]
        assert bad == [], p.name
    b20 = sf.parse_queue(B20_QUEUE.read_text())
    assert b20 and all(l.label.startswith("b20-") and l.argv[0] == "b20" for l in b20)


def test_nov11_checks_e2s_and_a40s_lines_on_this_account():
    """The A39 log's section 19: B20's lines have left this account's queue, so the feeder can't see them; A40 now
    stands ahead of the 30 here, as B20 did. So nov11 checks E2's and A40's lines."""
    d = sf.DECISIONS["nov11"]
    pat = re.compile(d["lines"])
    assert all(pat.match(x) for x in ("e2-base-1of16", "e2-base-sweep", "a40-train", "a40-e2-1of4"))
    assert not any(pat.match(x) for x in ("b20-granite-r3-1", "m30-base-1of4", "b1r2-01of40"))
    assert "A40" in d["what"] and "B20" not in d["what"] and "19" in d["rule"]
    assert "B1R2" not in sf.DECISIONS["nov6"]["no cut"] and "section 19" in sf.DECISIONS["nov6"]["cut"]


def test_nov11_drops_the_30_while_an_a40_line_is_open_and_no_b20_line_counts(tmp_path):
    sol, clock = FakeSol(places=3), Clock("2026-11-06T07:01:00")
    text = q("e2-base-1of16 | - | a39_1gpu --estimate 1.5 -- base e2 1/16",
             "a40-e2-1of4 | - | a39_1gpu --estimate 1.5 -- a40 e2 1/4",
             "b20-g-1 | - | b20 --model granite-4.2-8b --estimate 2.3",
             "m30-base-1of4 | dropif=nov6:nov11 | a39_1gpu --estimate 1.5 -- base mmlupro_30 1/4")
    f = feeder(tmp_path, text, sol, now=clock)
    nov6_usage(sol, 30)
    f.tick()                                                              # Nov 6: no cut; e2, a40 and b20 go in
    sol.end("100")                                                        # E2's line ended; A40's and B20's run on
    clock.add(days=5, hours=2)                                            # Nov 11 09:01
    f.tick()
    st = json.loads((tmp_path / "state" / "state.json").read_text())
    assert st["decisions"]["nov11"]["branch"] == "cut" and st["decisions"]["nov11"]["first"] == "a40-e2-1of4"
    assert st["decisions"]["nov11"]["open"] == 1                          # not b20-g-1: B20 isn't this account's
    assert st["lines"]["m30-base-1of4"]["status"] == "dropped"


def test_the_digest_gives_a40_its_own_group(tmp_path):
    """The coordinator (Nov 5): group_of put any line with "e2" in its arguments under A39 on E2, so A40's E2 lines
    would have counted as A39's. A40 (a40- labels, or the system a40) is its own group; B20's stays (Arsha's feeder)."""
    line = lambda label, args: sf.parse_queue(f"{label} | - | {args}\n")[0]   # noqa: E731
    assert sf.group_of(line("a40-e2-1of4", "a39_1gpu --estimate 1.5 -- a40 e2 1/4")) == "A40"
    assert sf.group_of(line("a40-train", "a40_train --estimate 3")) == "A40"
    assert sf.group_of(line("x", "a39_1gpu --estimate 1.5 -- a40 e2 1/4")) == "A40"            # by its system
    assert sf.group_of(line("e2-base-1of16", "a39_1gpu --estimate 1.5 -- base e2 1/16")) == "A39 on E2"
    assert sf.group_of(line("m30-base-1of4", "a39_1gpu --estimate 1.5 -- base mmlupro_30 1/4")) == "A39 on the 30"
    assert sf.group_of(line("b20-granite-r3-1", "b20 --model granite-4.2-8b --estimate 2.3")) == "B20"
    sol, clock = FakeSol(), Clock("2026-11-05T07:02:00")
    f = feeder(tmp_path, q("e2-base-1of16 | - | a39_1gpu --estimate 1.5 -- base e2 1/16",
                           "a40-e2-1of4 | afterok=@e2-base-1of16 | a39_1gpu --estimate 1.5 -- a40 e2 1/4"), sol, now=clock)
    f.tick()
    body = next(b for _, s, b in sol.mails if "digest" in s)
    assert "  A39 on E2: 1 pending" in body and "  A40: 1 to submit" in body


def test_the_mail_and_the_digest_name_the_queue_when_it_isnt_the_default(tmp_path):
    """Helper E's review (Nov 5): on Arsha's account, "Status: ... --status" with no --queue reads Ritik's file, which the
    owner line refuses there. So the alert mail and the digest give --queue whenever the queue isn't the default."""
    sol, clock = FakeSol(), Clock("2026-11-05T07:02:00")
    text = q("g1 | - | b20 --model granite-4.2-8b --estimate 2.3")
    f = feeder(tmp_path, text, sol, now=clock, queue=B20_QUEUE)
    f.tick()
    sol.end("100", "FAILED", "1:0")
    clock.add(days=1)
    f.tick()
    want = "Status: python3 cot-disclosure/tools/sol_feeder.py --status --queue " \
           "cot-disclosure/finetune/gpu/sol/queue_b20_2026-11-05.txt"
    alert = next(b for _, s, b in sol.mails if "alert" in s)
    digest = next(b for _, s, b in sol.mails if "digest" in s)
    assert want in alert and want in digest
    for queue in (None, sf.QUEUE):                                        # Ritik's, the default: no --queue
        g = feeder(tmp_path / str(queue is None), text, FakeSol(), now=clock, queue=queue)
        assert g.status_hint() == "python3 cot-disclosure/tools/sol_feeder.py --status"
