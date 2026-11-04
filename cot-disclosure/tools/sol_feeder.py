#!/usr/bin/env python3
"""The Sol feeder (Nov 4): keeps Ritik's class-QoS queue full from an ordered queue file, through submit.sh, so places
that free up at night or in class are filled within a tick. Standard library only (Python 3.6+), on a login node.

One tick (--once; --loop runs one every --interval seconds, 300 by default):
  1. The stop file (/scratch/$USER/trackA/feeder.stop) ends it, the loop too, before anything else.
  2. Every job it knows (a line's job, or a job id a line names) gets its state from sacct (squeue while sacct doesn't
     know it yet). A job that ends other than COMPLETED with exit 0 is an alert, once; a B20 job that stops at its
     limit with runs left (exit 2) isn't, when a line runs it again.
  3. The queue's lines, in order. A line is submitted once and never again: its job id goes into the state file before
     the next line is looked at, and its --comment=feeder:LABEL lets a restart recover a submission it didn't record.
     A line waits while its dependencies run, or while Sol's clone lacks a commit it needs. It is skipped, and you
     are told, when an afterok dependency failed. A sweep with no runs left isn't run.
  4. A ready line goes in only if `submit.sh --check` leaves it a place in the 10 and its GPU-minutes fit what the
     running and pending jobs leave of the 960. The first ready line that doesn't fit ends the tick, so the order holds.
The dependencies are the feeder's, not Slurm's: a line is submitted after its dependencies have ended, so no pending
job holds one of the 10 places waiting, and none waits forever behind a failed job. It never resubmits a job that
ended: `--reset LABEL` (yours) lets a line go in again.
Alerts: the log, the state file (--status) and one mail a tick to $TRACKA_MAIL (default $USER@asu.edu) through the
login node's `mail`, if it has one.
The daily digest (Nov 4): the first tick after 07:00 (local time) mails what finished and what failed in the last 24 h,
what runs and waits, the GPU-hours delivered in the last 24 h (sacct: each job's time in the window x its GPUs), any gap
between ticks, and a rough finish for A39 on E2, A39 on the 30, B20 and B1R2: the GPU-hours the queue still holds up to
each group's last line (at each line's limit), at the last 24 h's pace. Also written to <out>/feeder/digest.txt.
Health: a tick that comes over 30 minutes after the one before says so in the log, the status and the next digest (the
scrontab job waited in Sol's queue; RUNBOOK section 0 has the nohup loop for that case).

  python3 cot-disclosure/tools/sol_feeder.py --status
  python3 cot-disclosure/tools/sol_feeder.py --dry-run             # what a tick would submit now; changes nothing
  python3 cot-disclosure/tools/sol_feeder.py --once                # one tick (scrontab)
  nohup python3 cot-disclosure/tools/sol_feeder.py --loop >> /scratch/$USER/trackA/feeder.out 2>&1 &
  touch /scratch/$USER/trackA/feeder.stop                          # it stops at its next check (10 s in --loop)
  python3 cot-disclosure/tools/sol_feeder.py --adopt LABEL JOBID   # a line you submitted by hand
  python3 cot-disclosure/tools/sol_feeder.py --skip LABEL          # never submit it
  python3 cot-disclosure/tools/sol_feeder.py --reset LABEL         # forget its job: it may go in again

The queue file (finetune/gpu/sol/queue_2026-11-04.txt): one job a line, "LABEL | OPTIONS | submit.sh ARGUMENTS";
OPTIONS ("-" for none):
  job=N           submitted by hand as job N: never submitted here, but tracked, and later lines may wait on it
  afterok=REFS    every REF ended COMPLETED with exit 0; if one ended otherwise, this line is skipped (and you're told)
  afterany=REFS   every REF has ended, however
  again=REF       REF stopped at its time limit with runs left (exit 2, B20): this line runs; REF finished (exit 0):
                  not needed; else skipped (and you're told)
  needs=COMMIT    Sol's clone has COMMIT (git merge-base --is-ancestor), else the line waits for a pull
  left=SPEC       run only if runs are left: a39:SYSTEM:QSET[:K/N] (finetune/eval.py's resume) or b1r2:K/N
REFS are colon-separated: @LABEL is an earlier line (its job id once submitted), a bare number a job id. $USER (any
environment variable) in the arguments is expanded, so the file names no Sol user.
"""
import argparse
import copy
import fcntl
import getpass
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import time
import traceback
from collections import namedtuple
from datetime import datetime
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
REPO = CODE.parent
SOL = CODE / "finetune" / "gpu" / "sol"
QUEUE = SOL / "queue_2026-11-04.txt"
USER = os.environ.get("USER") or getpass.getuser()
TRACKA_OUT = Path(os.environ.get("TRACKA_OUT") or "/scratch/%s/trackA" % USER)
OPTIONS = ("job", "afterok", "afterany", "again", "needs", "left")
ACTIVE = {"PENDING", "RUNNING", "REQUEUED", "RESIZING", "SUSPENDED", "CONFIGURING", "COMPLETING", "STOPPED"}
HELD = ("skipped", "not needed", "unknown", "submitting", "submit failed")
GAP_MIN = 30                                       # minutes between ticks before the next one says so
DIGEST_HOUR = 7                                    # the daily digest: the first tick at or after 07:00, local time
LEFT = re.compile(r"(a39:[a-z_]+:(e2|mmlupro_30)(:\d+/\d+)?|b1r2:\d+/\d+)$")
WARN_EXIT = "138:0"                                # 128 + SIGUSR1: Slurm's warning ended the job script's wait
Line = namedtuple("Line", "n label opts argv")


class QueueError(ValueError):
    pass


class FeederError(RuntimeError):
    pass


def parse_queue(text):
    lines, seen = [], set()
    for n, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        parts = [p.strip() for p in s.split("|")]
        if len(parts) != 3 or not parts[0] or not parts[2]:
            raise QueueError("queue line %d: want LABEL | OPTIONS | ARGUMENTS: %r" % (n, s))
        label, opts_text, args = parts
        if not re.match(r"[A-Za-z0-9][A-Za-z0-9_.-]*$", label):
            raise QueueError("queue line %d: a label is letters, digits, _ . -: %r" % (n, label))
        if label in seen:
            raise QueueError("queue line %d: the label %s is used twice" % (n, label))
        opts = {}
        for tok in ([] if opts_text in ("", "-") else opts_text.split()):
            k, _, v = tok.partition("=")
            if k not in OPTIONS or not v:
                raise QueueError("queue line %d: unknown option %r (options: %s)" % (n, tok, ", ".join(OPTIONS)))
            opts[k] = v
        for k in ("afterok", "afterany", "again"):
            for ref in opts.get(k, "").split(":") if k in opts else []:
                if ref.startswith("@") and ref[1:] not in seen:
                    raise QueueError("queue line %d: %s=%s must name an earlier line" % (n, k, ref))
                if not ref.startswith("@") and not ref.isdigit():
                    raise QueueError("queue line %d: %s=%s: @LABEL or a job id" % (n, k, ref))
        if "again" in opts and (":" in opts["again"] or not opts["again"].startswith("@")):
            raise QueueError("queue line %d: again= names one earlier line" % n)
        if "job" in opts and not opts["job"].isdigit():
            raise QueueError("queue line %d: job= is a job id" % n)
        if "left" in opts and not LEFT.match(opts["left"]):
            raise QueueError("queue line %d: left=%s: a39:SYSTEM:QSET[:K/N] or b1r2:K/N" % (n, opts["left"]))
        lines.append(Line(n, label, opts, [os.path.expandvars(a) for a in shlex.split(args)]))   # $USER: yours
        seen.add(label)
    return lines


def refs_of(line):
    return [r for k in ("afterok", "afterany", "again") if k in line.opts for r in line.opts[k].split(":")]


def with_flags(argv, *flags):
    return [argv[0]] + list(flags) + list(argv[1:])


def now_text():
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def stamp_of(t):
    return t.strftime("%Y-%m-%d %H:%M:%S %Z")


def epoch_of(text):
    """A stamp this feeder wrote ("2026-11-04 03:20:35 MST"), as seconds; None if it can't be read."""
    try:
        return time.mktime(time.strptime(text[:19], "%Y-%m-%d %H:%M:%S"))
    except (TypeError, ValueError):
        return None


def sacct_time(text):
    """sacct's Start or End ("2026-11-04T03:20:35", local time) as seconds; None for Unknown, None or empty."""
    try:
        return time.mktime(time.strptime(text.strip(), "%Y-%m-%dT%H:%M:%S"))
    except ValueError:
        return None


def limit_hours(argv):
    """The time limit submit.sh gives a line: its estimate (B20's smoke: 1 h; B20's runs: 6 h) x 1.3, rounded up to
    the next half hour."""
    if "--estimate" in argv:
        est = float(argv[argv.index("--estimate") + 1])
    else:
        est = 1.0 if "--smoke" in argv else 6.0 if argv[0] == "b20" else 1.0
    return -(-est * 1.3 // 0.5) * 0.5


def group_of(line):
    """The digest's groups: A39 on E2, A39 on the 30, B20, B1R2."""
    a = line.argv
    if a[0] == "b20":
        return "B20"
    if a[0] == "provenance_gen":
        return "B1R2"
    if a[0].startswith("a39"):
        return "A39 on E2" if "e2" in a else "A39 on the 30"
    return None


def ended(job):
    return bool(job.get("state")) and job["state"] not in ACTIVE


def ok(job):
    """COMPLETED with exit 0, or (Nov 4) a part that ended at Slurm's warning with every one of its runs saved."""
    return (job.get("state") == "COMPLETED" and job.get("exit") == "0:0") or job.get("saved") is True


def spec_of(line):
    """The runs-left spec (left=) of a line whose runs the feeder can count: an A39 part or sweep
    (a39:SYSTEM:QSET[:K/N]) or a B1R2 part (b1r2:K/N); else None."""
    a = line.argv
    if a[0] in ("a39", "a39_1gpu") and "--" in a and len(a) >= a.index("--") + 3:
        system, qset, *rest = a[a.index("--") + 1:]
        spec = "a39:%s:%s" % (system, qset) + (":" + rest[0] if rest and "/" in rest[0] else "")
    elif a[0] == "provenance_gen" and "--b1r2" in a and "--part" in a[:-1]:
        spec = "b1r2:" + a[a.index("--part") + 1]
    else:
        return None
    return spec if LEFT.match(spec) else None


# ---------------------------------------------------------------- Sol's commands
class Sol:
    """What the feeder asks of Sol: submit.sh (--check, then the job), sacct and squeue, git, mail."""

    def __init__(self, env=None, submit=SOL / "submit.sh", repo=REPO, out=TRACKA_OUT):
        base = dict(os.environ if env is None else env)
        self.env = {k: v for k, v in base.items() if not k.startswith(("SLURM_", "SBATCH_"))}   # not the scron job's
        self.submit_sh, self.repo, self.out, self.user = submit, repo, Path(out), self.env.get("USER", USER)

    def _run(self, cmd, timeout=180, **kw):
        """Never raises: a command that hangs gives code 124, one that isn't there 127 (the tick goes on)."""
        try:
            return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                                  env=self.env, timeout=timeout, **kw)
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(cmd, 124, "", "%s timed out after %d s" % (cmd[0], timeout))
        except OSError as err:
            return subprocess.CompletedProcess(cmd, 127, "", "%s: %s" % (cmd[0], err))

    def check(self, argv):
        r = self._run(["bash", str(self.submit_sh)] + with_flags(argv, "--check"))
        text = (r.stdout + r.stderr).strip()
        if r.returncode in (124, 127) or "running and pending jobs not checked" in text:   # try again next tick
            return {"full": False, "transient": True, "refused": "squeue failed, so the queue wasn't counted"}
        if r.returncode != 0 or "check only: nothing submitted" not in r.stdout:
            return {"full": "more than" in text and "jobs in the QoS" in text, "refused": text[-600:] or "exit %d" % r.returncode}
        qos = re.search(r"running (\d+) \((\d+) GPU-minutes left\), pending (\d+) \((\d+) requested", r.stdout)
        lim = re.search(r"limits: (\d+) of (\d+) GPU-minutes free now \(this job needs (\d+)\); (-?\d+) of (\d+) places",
                        r.stdout)
        if not (qos and lim):
            return {"full": False, "transient": True, "refused": "submit.sh couldn't count the queue: " + text[-300:]}
        return {"full": False, "refused": None, "need": int(lim.group(3)), "free": int(lim.group(1)),
                "pending": int(qos.group(4)), "places": int(lim.group(4))}

    def submit(self, argv):
        r = self._run(["bash", str(self.submit_sh)] + list(argv))
        m = re.search(r"^Submitted batch job (\d+)", r.stdout, re.M)
        if r.returncode != 0 or not m:
            raise FeederError(((r.stdout + r.stderr).strip() or "exit %d" % r.returncode)[-600:])
        return m.group(1)

    def states(self, ids):
        out = {}
        if not ids:
            return out
        r = self._run(["sacct", "-X", "-n", "-P", "-j", ",".join(ids), "-o", "JobID,State,ExitCode"])
        for row in r.stdout.splitlines():
            f = row.strip().split("|")
            if len(f) >= 3 and f[0] in ids:
                out[f[0]] = (f[1].split()[0] if f[1] else "", f[2])
        missing = [i for i in ids if i not in out]
        if missing:
            r = self._run(["squeue", "-h", "-j", ",".join(missing), "-o", "%i %T"])
            for row in r.stdout.splitlines():
                f = row.split()
                if len(f) == 2 and f[0] in missing:
                    out[f[0]] = (f[1], "0:0")
        return out

    def active_comments(self):
        """{comment: job id} of your queued jobs; None if squeue failed (nothing is concluded from it)."""
        r = self._run(["squeue", "-h", "-u", self.user, "-o", "%i|%k"])
        if r.returncode != 0:
            return None
        return {f[1]: f[0] for f in (row.split("|", 1) for row in r.stdout.splitlines()) if len(f) == 2 and f[1]}

    def has_commit(self, commit):
        return self._run(["git", "-C", str(self.repo), "merge-base", "--is-ancestor", commit, "HEAD"]).returncode == 0

    def runs_left(self, spec, argv):
        """Counted by the project's own resume code, in a child process (the feeder itself imports none of it)."""
        cmd = [sys.executable, str(Path(__file__).resolve()), "--runs-left", spec, "--out", str(self.out)]
        if "--alpha-from" in argv:
            cmd += ["--alpha-from", argv[argv.index("--alpha-from") + 1]]
        r = self._run(cmd, timeout=600, cwd=str(CODE))
        try:
            return int(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 else None
        except (ValueError, IndexError):
            return None

    def usage(self, since):
        """[{job, start, end (None while it runs), gpus}] of your jobs that ran since `since` (a datetime), from sacct."""
        r = self._run(["sacct", "-X", "-n", "-P", "-u", self.user, "-S", since.strftime("%Y-%m-%dT%H:%M:%S"),
                       "-E", "now", "-o", "JobID,Start,End,AllocTRES"])
        rows = []
        for row in r.stdout.splitlines():
            f = row.strip().split("|")
            if len(f) < 4 or sacct_time(f[1]) is None:
                continue
            m = re.search(r"gres/gpu=(\d+)", f[3]) or re.search(r"gres/gpu:[^=,]+=(\d+)", f[3])
            rows.append({"job": f[0], "start": sacct_time(f[1]), "end": sacct_time(f[2]), "gpus": int(m.group(1)) if m else 0})
        return rows

    def mail(self, to, subject, body):
        prog = shutil.which("mail") or shutil.which("mailx")
        if prog:
            r = self._run([prog, "-s", subject, to], input=body)
            return "mailed %s" % to if r.returncode == 0 else "mail failed: %s" % r.stderr.strip()[-200:]
        sendmail = shutil.which("sendmail") or ("/usr/sbin/sendmail" if os.path.exists("/usr/sbin/sendmail") else None)
        if sendmail:
            r = self._run([sendmail, "-t"], input="To: %s\nSubject: %s\n\n%s\n" % (to, subject, body))
            return "mailed %s" % to if r.returncode == 0 else "sendmail failed: %s" % r.stderr.strip()[-200:]
        return "no mail program on this node: see the log"


def runs_left_here(spec, argv, out_root, alpha_from=None):
    """The runs a resumed job would still run (finetune/eval.py's resume: a run counts once it has an ok record)."""
    sys.path[:0] = [str(CODE), str(CODE / "progress")]
    from finetune import eval as ev
    f = spec.split(":")
    done_of = lambda d, system, *qd: {r["run_id"] for r in ev.latest([r for p in ev.runs_files(d, system, *qd)  # noqa: E731
                                                                   for r in ev.load(p)]) if r["status"] == "ok"}
    if f[0] == "a39":
        system, qset = f[1], f[2]
        part = tuple(int(x) for x in f[3].split("/")) if len(f) > 3 else None
        done = done_of(Path(out_root) / "a39", system, qset, "a39")
        return sum(1 for j in ev.jobs(part, qset, "a39", system) if ev.job_id(system, j) not in done)
    from finetune.gpu import provenance_job as pj
    part = tuple(int(x) for x in f[1].split("/"))
    alpha_from = alpha_from or str(Path(out_root) / "provenance_forced" / "provenance_forced.json")
    jobs = pj.b1r2_jobs(part)[0]
    left = 0
    for system, _, _ in pj.b1r2_configs(pj.chosen_of(alpha_from)):
        done = done_of(Path(out_root) / pj.B1R2_DIR, system)
        left += sum(1 for j in jobs if ev.job_id(system, j) not in done)
    return left


# ---------------------------------------------------------------- the feeder
class Feeder:
    def __init__(self, lines, state_dir, sol, log_path, stop_file, mail_to, clock=None, echo=False, now=None):
        self.now = now or (lambda: datetime.now().astimezone())             # a datetime: the digest and the health check
        self.lines, self.sol, self.echo = lines, sol, echo
        self.clock = clock or (lambda: stamp_of(self.now()))
        self.by = {l.label: l for l in lines}
        self.state_dir, self.log_path, self.stop_file, self.mail_to = Path(state_dir), Path(log_path), Path(stop_file), mail_to
        self.state_path = self.state_dir / "state.json"
        self.again_of = {l.opts["again"][1:] for l in lines if "again" in l.opts}

    # -- state and log
    def load(self):
        if self.state_path.exists():
            st = json.loads(self.state_path.read_text())
        else:
            st = {}
        for k, v in (("lines", {}), ("jobs", {}), ("alerts", [])):
            st.setdefault(k, v)
        for l in self.lines:                                             # lines submitted by hand (job=N)
            if "job" in l.opts and l.label not in st["lines"]:
                st["lines"][l.label] = {"job": l.opts["job"], "how": "queue file"}
        return st

    def save(self, st):
        self.state_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_name("state.json.tmp")
        tmp.write_text(json.dumps(st, indent=1, sort_keys=True) + "\n")
        os.replace(str(tmp), str(self.state_path))

    def log(self, text, dry=False):
        line = "%s  %s%s" % (self.clock(), "[dry run] " if dry else "", text)
        if self.echo or dry:
            print(line, flush=True)
        if not dry:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(str(self.log_path), "a") as f:
                f.write(line + "\n")

    def locked(self):
        self.state_dir.mkdir(parents=True, exist_ok=True)
        fd = open(str(self.state_dir / "feeder.lock"), "w")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            fd.close()
            return None
        return fd

    # -- one tick
    def tick(self, dry=False):
        if self.stop_file.exists():
            self.log("stop file %s: nothing done (remove it to start again)" % self.stop_file, dry)
            return "stopped"
        lock = None if dry else self.locked()
        if not dry and lock is None:
            self.log("another feeder holds the lock: this tick does nothing")
            return []
        try:
            return self._tick(dry)
        finally:
            if lock:
                lock.close()

    def _tick(self, dry):
        st = self.load()
        if dry:
            st = copy.deepcopy(st)
        L, J, alerts, stamp = st["lines"], st["jobs"], [], self.clock()
        now_ts = self.now().timestamp()
        say = lambda text: self.log(text, dry)  # noqa: E731
        prev = st.get("heartbeat") or {}
        prev_ts = prev.get("ts") or epoch_of(prev.get("at"))
        if prev_ts and now_ts - prev_ts > GAP_MIN * 60:                  # health: the scrontab job waited?
            gap = int(round((now_ts - prev_ts) / 60))
            say("%d minutes since the last tick (%s): the scrontab job may have waited in Sol's queue (squeue -u $USER "
                "-n trackA-feeder); if it keeps happening, run the nohup loop instead (RUNBOOK section 0)"
                % (gap, prev.get("at", "?")))
            st["gaps"] = (st.get("gaps", []) + [{"at": stamp, "ts": now_ts, "minutes": gap}])[-50:]

        def alert(text):
            alerts.append(text)
            say("ALERT " + text)

        # 1. a submission that wasn't recorded (a crash between sbatch and the record): its comment finds it
        lost = [lab for lab, s in L.items() if s.get("status") == "submitting"]
        comments = self.sol.active_comments() if lost else {}
        if comments is None:
            say("squeue failed: %s stay%s 'submitting' until the next tick" % (", ".join(lost), "s" * (len(lost) == 1)))
        else:
            for lab in lost:
                jid = comments.get("feeder:" + lab)
                if jid:
                    L[lab] = {"job": jid, "how": "recovered from its comment", "at": stamp}
                    say("recovered %s: job %s (its submission wasn't recorded)" % (lab, jid))
                else:
                    L[lab] = {"status": "unknown", "at": stamp, "why": "its submission wasn't recorded and no queued job "
                              "carries its comment: check squeue and sacct, then --adopt %s JOBID or --reset %s" % (lab, lab)}
                    alert("%s: %s" % (lab, L[lab]["why"]))
        # 2. the jobs' states
        label_of = {s["job"]: lab for lab, s in L.items() if s.get("job")}
        ids = set(label_of) | {r for l in self.lines for r in refs_of(l) if r.isdigit()}
        ids = sorted(i for i in ids if not ended(J.get(i, {})))
        for jid, (state, ex) in self.sol.states(ids).items():
            j = J.setdefault(jid, {})
            if (state, ex) == (j.get("state"), j.get("exit")):
                continue
            j.update(state=state, exit=ex)
            name = "job %s (%s)" % (jid, label_of.get(jid, "not in the queue"))
            if not ended(j):
                continue
            j["ended"], j["ended_ts"] = stamp, now_ts
            self.count_left(jid, j, label_of.get(jid))                   # Nov 4: an A39 or B1R2 part's runs left
            left = j.get("left")
            if j.get("saved"):
                say("%s ended %s, exit 138 at Slurm's warning with all its runs saved: done" % (name, state))
            elif ok(j):
                say("%s done%s" % (name, "; %d of its runs left (stopped at its limit?)" % left if left else ""))
            elif ex == "2:0" and label_of.get(jid) in self.again_of:
                say("%s stopped at its limit with runs left (exit 2): its next line runs it again" % name)
            else:
                alert("%s ended %s, exit %s%s" % (name, state, ex, "; %d of its runs left" % left if left else ""))
        for jid, j in J.items():                         # a part that ended 138 before this check (460114): once
            if ended(j) and j.get("exit") == WARN_EXIT and "left" not in j and self.count_left(jid, j, label_of.get(jid)):
                say("job %s (%s): exit 138 at Slurm's warning with all its runs saved: done" % (jid, label_of[jid]))
        # 3. the lines, in order
        submitted, used_places, used_min = [], 0, 0
        for l in self.lines:
            s = L.get(l.label, {})
            if s.get("job") or s.get("status") in HELD:
                continue
            verdict, why = self.readiness(l, L, J)
            if verdict == "wait":
                continue
            if verdict in ("skip", "not needed"):
                L[l.label] = {"status": "skipped" if verdict == "skip" else "not needed", "why": why, "at": stamp}
                (alert if verdict == "skip" else say)("%s %s: %s" % (l.label, L[l.label]["status"], why))
                continue
            c = self.sol.check(l.argv)
            if c["refused"]:
                if c["full"]:
                    say("the queue is full (10 places): %s waits" % l.label)
                    break
                if c.get("transient"):
                    say("%s waits: %s; the next tick tries again" % (l.label, c["refused"]))
                    break
                L[l.label] = {"status": "skipped", "why": "submit.sh refuses it: " + c["refused"], "at": stamp}
                alert("%s skipped: %s" % (l.label, L[l.label]["why"]))
                continue
            places, free = c["places"] - used_places, c["free"] - c["pending"] - used_min
            if places < 0:
                say("the queue is full (10 places): %s waits" % l.label)
                break
            if c["need"] > free:
                say("%s waits for GPU-minutes: it needs %d, the running and pending jobs leave %d of the 960"
                    % (l.label, c["need"], max(free, 0)))
                break
            args = with_flags(l.argv, "--comment=feeder:" + l.label)
            if dry:
                say("would submit %s (%s): submit.sh %s" % (l.label, why, " ".join(shlex.quote(a) for a in args)))
                submitted.append(l.label)
                used_places, used_min = used_places + 1, used_min + c["need"]
                continue
            L[l.label] = {"status": "submitting", "at": stamp}
            self.save(st)
            try:
                jid = self.sol.submit(args)
            except FeederError as err:
                jid = (self.sol.active_comments() or {}).get("feeder:" + l.label)
                if not jid:
                    fails = s.get("fails", 0) + 1
                    L[l.label] = {"fails": fails, "at": stamp, "last error": str(err)[-300:]}
                    if fails >= 3:
                        L[l.label]["status"] = "submit failed"
                        alert("%s: submit.sh failed 3 times; held until --reset: %s" % (l.label, str(err)[-300:]))
                    else:
                        say("%s: submit.sh failed (try %d of 3): %s" % (l.label, fails, str(err)[-300:]))
                    self.save(st)
                    break
            L[l.label] = {"job": jid, "how": "submitted", "at": stamp}
            J[jid] = {"state": "PENDING", "exit": "0:0"}
            self.save(st)
            say("submitted %s as job %s (%s): submit.sh %s" % (l.label, jid, why, " ".join(shlex.quote(a) for a in args)))
            submitted.append(l.label)
        # 4. the record, and one mail for this tick's alerts
        st["heartbeat"] = {"at": stamp, "ts": now_ts, "host": socket.gethostname(), "pid": os.getpid()}
        if alerts:
            st["alerts"] = (st["alerts"] + [{"at": stamp, "text": a} for a in alerts])[-100:]
            if not dry and self.mail_to and self.mail_to != "none":
                body = "\n".join(alerts) + "\n\nThe log: %s\nStatus: python3 cot-disclosure/tools/sol_feeder.py --status\n" \
                       % self.log_path
                say(self.sol.mail(self.mail_to, "Sol feeder: %d alert%s" % (len(alerts), "s" * (len(alerts) > 1)), body))
        today = self.now().strftime("%Y-%m-%d")
        if not dry and self.now().hour >= DIGEST_HOUR and st.get("digest_day") != today:
            try:
                body = self.digest(st)
            except Exception:                                            # a digest never stops a tick
                body = "The digest failed (the tick went on):\n" + traceback.format_exc()
            st["digest_day"] = today
            self.state_dir.mkdir(parents=True, exist_ok=True)
            (self.state_dir / "digest.txt").write_text(body + "\n")
            if self.mail_to and self.mail_to != "none":
                say("digest mailed (%s): %s" % (self.sol.mail(self.mail_to, "Sol feeder: daily digest, %s" % today, body),
                                                 self.state_dir / "digest.txt"))
            else:
                say("digest written: %s" % (self.state_dir / "digest.txt"))
        if not dry:
            self.save(st)
            say("tick: %d submitted%s" % (len(submitted), (": " + ", ".join(submitted)) if submitted else ""))
        return submitted

    # -- the daily digest
    def digest(self, st):
        """What the digest says (module docstring), from the state, sacct's usage and the queue."""
        L, J, now = st["lines"], st["jobs"], self.now()
        now_ts, since = now.timestamp(), now.timestamp() - 24 * 3600
        label_of = {s["job"]: lab for lab, s in L.items() if s.get("job")}

        def end_ts(j):
            return j.get("ended_ts") or epoch_of(j.get("ended"))
        recent = [(jid, j) for jid, j in J.items() if ended(j) and (end_ts(j) or 0) >= since]
        done = ["%s (job %s%s)" % (label_of.get(jid, "not in the queue"), jid, "; %d of its runs left" % j["left"]
                                   if j.get("left") else "; exit 138 at the warning" if j.get("saved") else "")
                for jid, j in recent if ok(j)]
        bad = ["%s (job %s): %s, exit %s" % (label_of.get(jid, "not in the queue"), jid, j.get("state"), j.get("exit"))
               for jid, j in recent if not ok(j)]
        running = ["%s (job %s)" % (lab, s["job"]) for lab, s in L.items() if s.get("job")
                   and J.get(s["job"], {}).get("state") == "RUNNING"]
        pending = ["%s (job %s)" % (lab, s["job"]) for lab, s in L.items() if s.get("job")
                   and J.get(s["job"], {}).get("state") == "PENDING"]
        use = self.sol.usage(datetime.fromtimestamp(since))
        started = {u["job"]: u["start"] for u in use}
        gpu_h = sum(max(0.0, min(u["end"] or now_ts, now_ts) - max(u["start"], since)) * u["gpus"] for u in use) / 3600
        gaps = [g for g in st.get("gaps", []) if g.get("ts", 0) >= since]
        out = ["Sol feeder, daily digest, %s" % stamp_of(now), "",
               "finished in the last 24 h (%d): %s" % (len(done), ", ".join(done) or "none"),
               "failed in the last 24 h (%d): %s" % (len(bad), "; ".join(bad) or "none"),
               "running (%d): %s" % (len(running), ", ".join(running) or "none"),
               "pending (%d): %s" % (len(pending), ", ".join(pending) or "none"),
               "GPU-hours in the last 24 h: %.1f (sacct: each job's time in the window x its GPUs)" % gpu_h,
               "gaps over 30 minutes between ticks in the last 24 h: %s"
               % (", ".join("%d min before %s" % (g["minutes"], g["at"]) for g in gaps) or "none"), "",
               "Rough finish (the GPU-hours the queue holds up to each group's last open line, each line at its limit; at "
               "the last 24 h's pace; B20's again-lines counted as if all were needed, so at most):"]
        held, last = 0.0, {}
        tally = {}
        for l in self.lines:
            g, s = group_of(l), L.get(l.label, {})
            j = J.get(s.get("job"), {}) if s.get("job") else {}
            if s.get("job") and ended(j):
                word = "done" if ok(j) else "ended badly"
            elif s.get("job"):
                word = (j.get("state") or "submitted").lower()
                left = limit_hours(l.argv) - ((now_ts - started[s["job"]]) / 3600 if s["job"] in started else 0)
                held += max(left, 0.0)
            elif s.get("status"):
                word = s["status"]
            else:
                word = "to submit"
                held += limit_hours(l.argv)
            if g:
                tally.setdefault(g, {})
                tally[g][word] = tally[g].get(word, 0) + 1
                if word in ("to submit", "pending", "running", "submitted"):
                    last[g] = held
        for g in ("A39 on E2", "A39 on the 30", "B20", "B1R2"):
            if g not in tally:
                continue
            counts = ", ".join("%d %s" % (v, k) for k, v in sorted(tally[g].items()))
            if g not in last:
                out.append("  %s: %s; nothing left in the queue" % (g, counts))
            elif gpu_h > 0:
                eta = datetime.fromtimestamp(now_ts + last[g] / gpu_h * 24 * 3600).strftime("%b %d %H:%M")
                out.append("  %s: %s; at most %.0f GPU-hours up to its last line; at %.1f GPU-hours a day, by about %s"
                           % (g, counts, last[g], gpu_h, eta))
            else:
                out.append("  %s: %s; at most %.0f GPU-hours up to its last line; no pace yet (nothing ran in 24 h)"
                           % (g, counts, last[g]))
        out += ["", "The log: %s" % self.log_path, "Status: python3 cot-disclosure/tools/sol_feeder.py --status"]
        return "\n".join(out)

    def resolve(self, ref, L):
        """(job id or None, the line's held status or None) of a reference."""
        if not ref.startswith("@"):
            return ref, None
        s = L.get(ref[1:], {})
        return s.get("job"), (s.get("status") if not s.get("job") else None)

    def readiness(self, l, L, J):
        """("ready" | "wait" | "skip" | "not needed", why), with each reference as its job id."""
        shown = []
        for kind in ("afterok", "afterany"):
            if kind not in l.opts:
                continue
            ids = []
            for ref in l.opts[kind].split(":"):
                jid, held = self.resolve(ref, L)
                if not jid:
                    if held and kind == "afterany":
                        ids.append("%s(%s)" % (ref, held))
                        continue
                    if held:
                        return "skip", "%s %s: %s was %s" % (kind, ref, ref, held)
                    return "wait", "%s: %s isn't submitted yet" % (kind, ref)
                ids.append(jid)
                j = J.get(jid, {})
                if not ended(j):
                    return "wait", "%s:%s: job %s is %s" % (kind, ":".join(ids), jid, j.get("state") or "not seen yet")
                if kind == "afterok" and not ok(j):
                    return "skip", "afterok: job %s (%s) ended %s, exit %s" % (jid, ref, j.get("state"), j.get("exit"))
            shown.append("%s:%s" % (kind, ":".join(ids)))
        if "again" in l.opts:
            ref = l.opts["again"]
            jid, held = self.resolve(ref, L)
            if not jid:
                if held == "not needed":
                    return "not needed", "%s's runs were done" % ref
                if held:
                    return "skip", "again: %s was %s" % (ref, held)
                return "wait", "again: %s isn't submitted yet" % ref
            j = J.get(jid, {})
            if not ended(j):
                return "wait", "again:%s: job %s is %s" % (jid, jid, j.get("state") or "not seen yet")
            if ok(j):
                return "not needed", "job %s (%s) finished its runs" % (jid, ref)
            if j.get("exit") != "2:0":
                return "skip", "again: job %s (%s) ended %s, exit %s (not a stop at its limit)" % (
                    jid, ref, j.get("state"), j.get("exit"))
            shown.append("again:%s" % jid)
        if "needs" in l.opts and not self.sol.has_commit(l.opts["needs"]):
            return "wait", "needs a pull: Sol's clone lacks %s" % l.opts["needs"]
        if "left" in l.opts:
            n = self.sol.runs_left(l.opts["left"], l.argv)
            if n == 0:
                return "not needed", "no runs left (%s)" % l.opts["left"]
            shown.append("%s runs left" % n if n is not None else "runs left not counted")
        return "ready", "; ".join(shown) or "no dependency"

    def count_left(self, jid, j, label):
        """Nov 4: count an ended A39 or B1R2 part's runs left once (j["left"]; None if they couldn't be counted). A
        part that ended at Slurm's warning (exit 138) with none left is done: j["saved"]. True if it was saved."""
        line = self.by.get(label)
        spec = spec_of(line) if line else None
        if not spec:
            return False
        j["left"] = self.sol.runs_left(spec, line.argv)
        if j.get("exit") == WARN_EXIT and j["left"] == 0:
            j["saved"] = True
        return bool(j.get("saved"))

    # -- the loop, and your commands
    def loop(self, interval=300):
        self.log("loop started on %s, pid %d, a tick every %d s" % (socket.gethostname(), os.getpid(), interval))
        while True:
            try:
                if self.tick() == "stopped":
                    return "stopped"
            except Exception:                                            # a bad tick is logged; the loop goes on
                self.log("ERROR in a tick:\n" + traceback.format_exc())
            for _ in range(max(int(interval // 10), 1) if interval else 1):
                if self.stop_file.exists():
                    self.log("stop file %s: the loop ends" % self.stop_file)
                    return "stopped"
                time.sleep(min(10, interval))

    def _edit(self, label, entry, what):
        if label not in self.by:
            raise SystemExit("no line labelled %s in the queue file" % label)
        lock = self.locked()
        if lock is None:
            raise SystemExit("a feeder tick is running: try again in a minute")
        try:
            st = self.load()
            if entry is None:
                st["lines"].pop(label, None)
            else:
                st["lines"][label] = entry
            self.save(st)
            self.log("%s %s (by hand)" % (label, what))
        finally:
            lock.close()

    def adopt(self, label, job):
        self._edit(label, {"job": str(job), "how": "adopted by hand", "at": self.clock()}, "adopted as job %s" % job)

    def skip(self, label, why="by hand"):
        self._edit(label, {"status": "skipped", "why": why, "at": self.clock()}, "skipped")

    def reset(self, label):
        self._edit(label, None, "reset: it may be submitted again")

    def status_text(self):
        st = self.load()
        L, J = st["lines"], st["jobs"]
        hb = st.get("heartbeat") or {}
        ago = None
        if hb.get("ts") or epoch_of(hb.get("at")):
            ago = int(round((self.now().timestamp() - (hb.get("ts") or epoch_of(hb.get("at")))) / 60))
        late = ("; late: over %d minutes, so the scrontab job may be waiting (squeue -u $USER -n trackA-feeder; the "
                "nohup loop: RUNBOOK section 0)" % GAP_MIN) if ago is not None and ago > GAP_MIN else ""
        out = ["last tick: %s%s on %s (pid %s)%s; stop file %s: %s" % (
               hb.get("at", "never"), " (%d minutes ago)" % ago if ago is not None else "", hb.get("host", "-"),
               hb.get("pid", "-"), late, self.stop_file, "present" if self.stop_file.exists() else "absent")]
        live = self.sol.states(sorted({s["job"] for s in L.values() if s.get("job")}))    # sacct now, not the last tick
        counts, rows = {}, []
        for l in self.lines:
            s = L.get(l.label, {})
            if s.get("job"):
                state, ex = live.get(s["job"]) or (J.get(s["job"], {}).get("state"), J.get(s["job"], {}).get("exit"))
                j = {**J.get(s["job"], {}), "state": state, "exit": ex}
                word = "ok" if ok(j) else (state or "not known to sacct").lower()
                note = (" (done: exit 138 at the warning, all its runs saved)" if j.get("saved") else
                        " (%d of its runs left)" % j["left"] if ended(j) and j.get("left") else "")
                rows.append("%-28s job %-8s %-11s %s%s" % (l.label, s["job"], state or "not known to sacct",
                                                            "exit %s" % ex if state else "(not yet in sacct, or a typo)", note))
            elif s.get("status"):
                word = s["status"]
                rows.append("%-28s %s: %s" % (l.label, s["status"], s.get("why", "")))
            else:
                word = "to submit"
                deps = [self._shown(k, l, L) for k in ("afterok", "afterany", "again") if k in l.opts]
                extra = ["%s %s" % (k, l.opts[k]) for k in ("needs", "left") if k in l.opts]
                rows.append("%-28s to submit%s" % (l.label, (" (" + "; ".join(deps + extra) + ")") if deps or extra else ""))
            counts[word] = counts.get(word, 0) + 1
        out.append("%d lines: %s" % (len(self.lines), ", ".join("%d %s" % (v, k) for k, v in sorted(counts.items()))))
        if st["alerts"]:
            out.append("alerts (the last 10):")
            out += ["  %s  %s" % (a["at"], a["text"]) for a in st["alerts"][-10:]]
        return "\n".join(out + [""] + rows)

    def _shown(self, kind, l, L):
        return "%s:%s" % (kind, ":".join(self.resolve(r, L)[0] or r for r in l.opts[kind].split(":")))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--once", action="store_true", help="one tick (scrontab)")
    mode.add_argument("--loop", action="store_true", help="a tick every --interval seconds, until the stop file")
    mode.add_argument("--dry-run", action="store_true", help="what a tick would submit now; changes nothing")
    mode.add_argument("--status", action="store_true")
    mode.add_argument("--adopt", nargs=2, metavar=("LABEL", "JOBID"))
    mode.add_argument("--skip", metavar="LABEL")
    mode.add_argument("--reset", metavar="LABEL")
    mode.add_argument("--runs-left", metavar="SPEC", help=argparse.SUPPRESS)
    ap.add_argument("--queue", default=str(QUEUE))
    ap.add_argument("--out", default=str(TRACKA_OUT), help="the log, the state and the stop file live here")
    ap.add_argument("--interval", type=int, default=300)
    ap.add_argument("--mail-to", default=os.environ.get("TRACKA_MAIL") or "%s@asu.edu" % USER)
    ap.add_argument("--alpha-from", help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    if a.runs_left:
        print(runs_left_here(a.runs_left, [], a.out, a.alpha_from))
        return 0
    out = Path(a.out)
    f = Feeder(parse_queue(Path(a.queue).read_text()), out / "feeder", Sol(out=out), log_path=out / "feeder.log",
               stop_file=out / "feeder.stop", mail_to=a.mail_to, echo=not a.loop)
    if a.status:
        print(f.status_text())
    elif a.adopt:
        f.adopt(*a.adopt)
    elif a.skip:
        f.skip(a.skip)
    elif a.reset:
        f.reset(a.reset)
    elif a.dry_run:
        f.tick(dry=True)
    elif a.once:
        f.tick()
    else:
        f.loop(a.interval)
    return 0


if __name__ == "__main__":
    try:
        rc = main()
        sys.stdout.flush()                       # here, not at exit: a short output waits in the buffer until then
    except BrokenPipeError:                                              # --status | head: the reader left; that's fine
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        rc = 0
    sys.exit(rc)
