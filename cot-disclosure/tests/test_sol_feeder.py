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
    """The kit names no Sol user (test_sol_second_user): the queue file says $USER, and the feeder expands it."""
    monkeypatch.setenv("USER", "someone")
    l = sf.parse_queue("a | - | provenance_gen -- --alpha-from /scratch/$USER/trackA/x.json --b1r2\n")[0]
    assert l.argv[-2] == "/scratch/someone/trackA/x.json"
    assert "$USER" in sf.QUEUE.read_text() and "ragarw68" not in sf.QUEUE.read_text()


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
                    "e2-lora-2of4": "428299", "e2-lora_note-2of4": "428330", "e2-base-2of4": "428332",
                    "b20-granite-smoke": "456999", "b20-gemma-smoke": "457471"}
    todo = [l for l in lines if "job" not in l.opts]
    kinds = [l.argv[0] for l in todo]
    first_a39 = kinds.index("a39_1gpu")
    assert set(kinds[:first_a39]) == {"b20"} and kinds[-1] == "provenance_gen"   # B20 first, B1R2 last
    assert all("needs" in l.opts for l in todo if l.argv[0] == "provenance_gen")
    parts = [(l.argv[-3], l.argv[-1]) for l in todo if l.argv[0] == "a39_1gpu" and l.argv[-2] == "e2"
             and l.argv[-1].endswith("/16")]
    assert len(parts) == 28 and {p for _, p in parts} == {f"{k}/16" for k in (3, 4, 7, 8, 11, 12, 15, 16)}
    from finetune import eval as ev
    for system, quarters in {"base": [4], "prompt_only": [3, 4], "lora": [3, 4], "lora_note": [3, 4]}.items():
        mine = {p for s, p in parts if s == system}
        assert mine == {f"{q + 4 * i}/16" for q in quarters for i in range(4)}, system
    fifths = [l for l in todo if l.argv[-2] == "e2" and l.argv[-1].endswith("/5")]
    assert len(fifths) == 15
    thirty = [l for l in todo if "mmlupro_30" in l.argv and re.search(r"/\d+$", l.argv[-1])]
    assert len(thirty) == 22
    assert sum(l.argv[0] == "provenance_gen" and "--part" in l.argv and l.argv[-1].endswith("/40") for l in todo) == 40
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
        assert l.argv[0] in ("b20", "a39_1gpu", "provenance_gen") and "--" not in l.opts


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
