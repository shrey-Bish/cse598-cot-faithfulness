"""Project tracking from the repo's own records: a Gantt workbook, a one-page chart for slides, a printable
chart with a page per track, and a status page.

Everything is read from what the repo already holds, so it can be made again any day (no calls, no network):
  - git log of the current branch (read-only): each commit's date, hash, files and subject; whether the
    branch's remote-tracking ref holds HEAD (the push done, as of the last fetch or push)
  - docs/status/TODO.md (docs/TODO.md until Nov 1, still read if it is there), and from Nov 3 each track's own
    docs/trackB/TODO_B.md and docs/trackC/TODO_C.md: every task table (each section's own
    header): status, dependency, owner, time
  - docs/PLAN.md: the gates, the timeline (windows for later work, the presentations and the report), the
    handoffs, the date by which all evaluation is done, and the deliverables
  - archive/superseded/OVERVIEW_<date>.md (docs/OVERVIEW.md until Oct 30): what was done before the session logs
    began (the progress round, Track A's Steps 1-10)
  - archive/sessions/INDEX.md and the session logs and dailies in archive/sessions/<YYYY-MM-DD>/ (from Oct 27;
    docs/sessions/ until Oct 30, still read if it is there): each day's work and compute
  - docs/FINDINGS.md: the F-numbers, each dated by the commit that added it, with its title and first interval
  - the progress-presentation kit at the repo root, if one is there: the week of the progress talk

  python tools/make_gantt.py                      # -> docs/status/GANTT.xlsx, gantt.png, gantt.pdf, STATUS.md
  python tools/make_gantt.py --today 2026-11-02   # the "today" column and line, and what "next 7 days" means
  python tools/make_gantt.py --dry-run            # print the Progress sheet, write nothing

Sheets: Gantt (a row and a bar per task by track and phase: ID, a short label, owner, start, end or due, status,
the date basis; a cell per day from Oct 1 to Dec 12, filled by status), To do (every open task by due: the next
action, estimate, blocker, the milestone it feeds; a row per milestone with what it needs; it replaces the old
Remaining sheet), Done (every finished task by date: what it delivered, with its finding and key number, and the
evidence: F-numbers, session logs, commits), Progress (per track: done of total, weighted by TODO's time, remaining
hours), Daily (each day per track: the work, the runs and compute as logged, the findings added, the commits),
Changes (every commit). gantt.png is the one-page overview (16:9, a bar per phase); gantt.pdf is that page, then
a page per track (A, B, C, the labels, the repo and handoffs with the progress round) with a bar per task.

Dates. A date read from a doc where it is stated (TODO, PLAN, OVERVIEW, a session log) is used as it is. A date is
marked "inferred" when it is derived: from a commit date (a commit isn't the work), from a vague phrase ("Oct 29
night"), from TODO's From column when the row gives no done date, from a dependency (an item due before the item
that waits on it), from the end of a PLAN window, or from the handoff it serves. Where the repo gives no date the
cell says "not in the repo" and no marker is drawn.

Status, from TODO's status text: "dropped ..." is dropped (Oct 31: an item dropped for scope stays in TODO, marked
"dropped (scope, <date>)"; it is neither done nor open, has no bar and is listed apart on the status page); "done
..." or "final ..." (or a bold "done" anywhere, "; done (", or "done" in the
first clause with no "not started / run / trained" after it) is done; "blocked" is blocked; otherwise the first
status word decides: running / submitted / queued / pending / draft / kept current
-> in progress; not started / not run / not trained / decided / planned / prepared / plan fixed / ready -> planned;
waiting for / asking -> blocked. A planned item whose "Blocked by" names an outside step (the push, a rater, keys, a
decision, terms) is blocked; the push no longer counts once the remote-tracking ref holds HEAD. Standing duties are
in progress. A row with no status word is read as in progress and listed in the Progress sheet's notes.

The next action (To do) is put together from TODO's own words: for an item under way, its latest status clause; for
a blocked one, what it waits for; for a planned one, "pre-register, then run" where the row says so, after its open
dependencies. What a milestone needs: the gate's "Blocked by" in TODO and what those items wait on (done or not);
a handoff that falls before the gate on a track it needs, open items due by the gate on its track, and done items
named for the gate that still have a rerun to do (inferred); for a report or presentation window, the other clauses
of PLAN's timeline row and PLAN's deliverables, each with its track's open items (inferred).

Owners (the rule): past work is Ritik's; an open Track B item is Arsha's from Nov 6 (moved from Nov 3); an open Track C item is
Shrey's from Oct 30; Track A, the labels, the repo and the report are Ritik's. TODO's own owner text is kept in a
column beside it.
"""
import argparse
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
ROOT = CODE.parent
# where the session logs live (a folder per date since Oct 30; before, one flat folder) and the superseded overview
SESSIONS = ("archive/sessions", "docs/sessions")
STATUS_DIR = "docs/status"                  # TODO (by hand), STATUS and the Gantt files (generated); docs/ until Nov 1
OVERVIEWS = ("archive/superseded/OVERVIEW_*.md", "docs/OVERVIEW.md")
FIRST, LAST = date(2026, 10, 1), date(2026, 12, 12)
STATUSES = ("done", "in progress", "planned", "blocked")
# status colors: good / a neutral blue for work under way / a light neutral / critical (status steps, not series)
FILL = {"done": "#0ca30c", "in progress": "#2a78d6", "planned": "#d6d5d0", "blocked": "#d03b3b"}
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
TRACKS = ("Setup", "A", "B", "C", "Labels", "Repo", "Milestones")
TRACK_NAME = {"Setup": "Setup and the progress round", "A": "Track A: explain and fix", "B": "Track B: test widely",
              "C": "Track C: multi-agent pipeline", "Labels": "Labels", "Repo": "Repo, docs and handoff",
              "Milestones": "Milestones: gates, handoffs, presentations, report", "ALL": "All tracks"}
# Who owns what (the rule): past work stays Ritik's; open items move to the teammate who takes the track over
TAKEOVER = {"B": ("Arsha", date(2026, 11, 6)), "C": ("Shrey", date(2026, 10, 30))}   # B: Nov 6 (moved from Nov 3 on Nov 3)
OWNER = {"A": "Ritik", "Labels": "Ritik", "Repo": "Ritik", "Setup": "Ritik", "Milestones": "everyone"}
MON = {m: i for i, m in enumerate(("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
                                   "Dec"), 1)}
MONTHS = "|".join(MON)
DAY = re.compile(rf"\b({MONTHS})\s+(\d{{1,2}})\b(?:\s*[–-]\s*(?:(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+)?(?:({MONTHS})\s+)?"
                 rf"(\d{{1,2}})\b)?(\s+(?:night|morning|evening|afternoon)\b)?")
ISO = re.compile(r"\b(20\d\d)-(\d\d)-(\d\d)\b")
FILEDATE = re.compile(r"(20\d\d)-(\d\d)-(\d\d)")      # in a file name (followed by _)
HASH = re.compile(r"`([0-9a-f]{7,12})`")
FREF = re.compile(r"\bF(\d{1,3})\b")
LOGREF = re.compile(r"\blog (?:(20\d\d-\d\d-\d\d) )?(\d\d):(\d\d)\b|\b(\d\d):(\d\d) (?:session )?log\b")
ID = re.compile(r"\b([ABC])(\d{1,2})\b")
TASKREF = re.compile(r"\b[ABCLHRD]\d{1,2}\b")
NUM = r"[+−-]?\d[\d,.]*%?"
INTERVAL = re.compile(rf"(?:\b([A-Z][a-z]\w*) )?({NUM} \[{NUM}, {NUM}\])")      # "Olmo +47 [+29, +65]"
CREDIT = re.compile(r"\bcredited to (?!Ritik|Arsha|Shrey)[A-Z][\w-]*(?: [A-Z][\w-]*)*")
# a phase per TODO row, by the first rule its item text matches (lowercased); Track A in this order
PHASES = {
    "A": [(r"^b1\b|provenance-scaled", "B1: provenance scaling"),
          (r"^b2\b|provenance-gated", "B2: provenance bias"), (r"\bset a\b", "Set A"),
          (r"needs a baseline|\bs7\b", "S7: validation loss"), (r"on a second model", "Thread 1 on Qwen3-8B"),
          (r"gate 3|^evaluate|step 13 analysis|look-inside|hand the best version|batch 3", "Evaluation and Gate 3"),
          (r"history rewrite|^merge ", "Repo: history rewrite, merge"),
          (r"\bsteps? (?:10|[1-9])\b|step ?9|figure|checkpoint report|assemble", "Steps 1–10"),
          (r"first sol jobs|^train the|fourth version|training settings", "Training (S1–S6)"),
          (r"step 1[123]\b|sol job|qos|vllm|sol scripts|hugging face", "Steps 11–13: code and Sol kit"),
          (r"identity", "Voyager model checks")],
    "B": [(r"qwen3-8b", "Qwen3-8B, thinking on and off"), (r"closed|\bkeys?\b|gpqa|haiku", "Closed models, GPQA")],
    "C": [(r"^run_team\.py|^no-tool team|^second reviewer model|^input-file", "Team code")],
}
DEFAULT_PHASE = {"A": "Other", "B": "Voyager models (B5, B7–B15)", "C": "Experiments", "Labels": "Labels L1–L5",
                 "Repo": "Handoffs, repo, docs"}
OUTSIDE = re.compile(r"push|rater|keys?\b|decision|accepts|terms|\"go\"", re.I)
STOP = {"with", "from", "done", "after", "then", "each", "into", "continue", "starts", "start", "that", "this",
        "their", "until", "when", "only"}


# ---------------------------------------------------------------- small readers
def read(path):
    path = Path(path)
    return path.read_text(errors="replace") if path.exists() else ""


def plain(text):
    """Markdown to one line of plain text (links keep their label; no bold, code ticks or extra spaces)."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("`", "").replace("\\|", "|")
    return re.sub(r"\s+", " ", text).strip()


def clean(text):
    """The docs name people, not tools: work credited to anything but a team member reads "credited to a tool"."""
    return CREDIT.sub("credited to a tool", text)


def short(text, n=120):
    text = plain(text)
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def clauses(text, sep=";"):
    """Split at sep outside parentheses and brackets."""
    out, depth, cur = [], 0, ""
    for ch in text:
        depth += (ch in "([") - (ch in ")]")
        if ch == sep and depth <= 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    return [c for c in out + [cur.strip()] if c]


def unparen(text):
    for _ in range(3):
        text = re.sub(r"\s*\([^()]*\)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def label(name, n=60):
    """A short label for a task: TODO's item text without code ticks or parentheses, cut after its question, else at
    the last clause end (':' or ';' after 12 characters) that fits, else at a comma, else shortened."""
    s = unparen(plain(name))
    q = s.find("? ")
    if 12 <= q < n:
        return s[:q + 1]
    if len(s) <= n:
        return s
    fit = [m.start() for m in re.finditer(r": |; ", s) if 12 <= m.start() <= n]
    if fit:
        return s[:max(fit)].rstrip(" ,")
    commas = [m.start() for m in re.finditer(r", ", s) if 20 <= m.start() <= n]
    return s[:max(commas)] if commas else short(s, n)


def dates_in(text, year):
    """[(date, offset, vague)] for every 'Oct 27', both ends of 'Oct 26–27' / 'Oct 30–Sun Nov 1', '2026-10-27'."""
    out = []
    for m in DAY.finditer(text):
        vague = bool(m.group(5))
        try:
            out.append((date(year, MON[m.group(1)], int(m.group(2))), m.start(), vague))
            if m.group(4):
                out.append((date(year, MON[m.group(3) or m.group(1)], int(m.group(4))), m.start(), vague))
        except ValueError:
            continue
    for m in ISO.finditer(text):
        try:
            out.append((date(int(m.group(1)), int(m.group(2)), int(m.group(3))), m.start(), False))
        except ValueError:
            continue
    return sorted(out, key=lambda x: x[1])


def md_tables(text):
    """[(heading, header cells, [row cells])] for every markdown table, with the nearest heading above it."""
    out, heading, rows, header = [], "", None, None
    for line in text.splitlines() + [""]:
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
        if line.lstrip().startswith("|"):
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
            if header is None:
                header, rows = cells, []
            elif all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            else:
                rows.append(cells + [""] * (len(header) - len(cells)))
        elif header is not None:
            out.append((heading, header, rows))
            header = None
    return out


def column(header, *names):
    """Index of the first header cell matching one of the names (case-insensitive), else None."""
    low = [h.lower().strip() for h in header]
    for n in names:
        if n in low:
            return low.index(n)
    return None


def sections(text):
    """[(heading, body)] split at markdown headings."""
    out, head, body = [], "", []
    for line in text.splitlines():
        if line.startswith("#"):
            out.append((head, "\n".join(body)))
            head, body = line.lstrip("#").strip(), []
        else:
            body.append(line)
    out.append((head, "\n".join(body)))
    return out


def bullets(body):
    """Top-level bullets, each with its continuation lines and sub-bullets joined."""
    out = []
    for line in body.splitlines():
        if line.startswith("- "):
            out.append(line[2:])
        elif out and line.startswith(" ") and line.strip():
            out[-1] += " " + line.strip().lstrip("- ")
    return [plain(b) for b in out]


# ---------------------------------------------------------------- git
def git_log(root):
    """[{hash, short, when (datetime), subject, files}] of the current branch, oldest first."""
    try:
        res = subprocess.run(["git", "-C", str(root), "log", "--name-only", "--format=\x1e%H\x1f%h\x1f%aI\x1f%s"],
                             capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    out = []
    for chunk in res.stdout.split("\x1e")[1:]:
        head, _, files = chunk.partition("\n")
        full, h, when, subject = head.split("\x1f", 3)
        out.append({"hash": full, "short": h, "when": datetime.fromisoformat(when), "subject": clean(subject),
                    "files": [f for f in files.splitlines() if f.strip()]})
    return out[::-1]


def head_commit(root):
    try:
        return subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "no commit"


def pushed(root):
    """The remote-tracking ref of the current branch (as of the last fetch or push), if it holds HEAD; else None."""
    def git(*args):
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                              check=True).stdout.strip()
    try:
        upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
        git("merge-base", "--is-ancestor", "HEAD", upstream)
        return upstream
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def finding_dates(root, today):
    """{n: (date, title, commit or None, track, key)}: each F-number dated by the commit that first added its
    heading (one in the working tree but in no commit yet is dated today, inferred), and its key number: the first
    bold interval in its text, else None."""
    out = {}
    try:
        log = subprocess.run(["git", "-C", str(root), "log", "--reverse", "-p", "--format=\x1e%h %aI", "--",
                              "docs/FINDINGS.md"], capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        log = ""
    for chunk in log.split("\x1e")[1:]:
        head, _, patch = chunk.partition("\n")
        h, when = head.split(" ", 1)
        for m in re.finditer(r"^\+## F(\d+)\. (.*)$", patch, re.M):
            out.setdefault(int(m.group(1)), (datetime.fromisoformat(when.strip()).date(), h))
    res = {}
    text = read(Path(root) / "docs" / "FINDINGS.md")
    parts = re.split(r"^## F(\d+)\. ", text, flags=re.M)
    for n, body in zip(parts[1::2], parts[2::2]):
        title, _, rest = body.partition("\n")
        d, h = out.get(int(n), (today, None))
        key = next((m.group(2) for b in re.findall(r"\*\*([^*]+)\*\*", rest) for m in [INTERVAL.search(b)] if m),
                   None)
        res[int(n)] = (d, clean(title.strip()), h, finding_track(title, rest[:2500]), key)
    return res


def finding_track(title, body):
    m = re.search(r"Track ([ABC])\b", title)
    if m:
        return m.group(1)
    score = {t: len(re.findall(p, body)) for t, p in (("A", r"summaries/trackA|Step \d|Olmo 3 7B Think"),
                                                      ("B", r"summaries/trackB|Track B"),
                                                      ("C", r"summaries/trackC|Track C"))}
    best = max(score, key=score.get)
    return best if score[best] else "ALL"


def commit_track(c, round_end):
    """The tracks a commit touched, from its files (code, summaries, session logs, handoffs) and else its subject;
    a commit from the progress round is Setup."""
    if round_end and c["when"].date() <= round_end:
        return "Setup"
    votes = set()
    for f in c["files"]:
        if re.search(r"summaries/trackA|cot-disclosure/finetune/|tests/test_(trackA|setA|qwen8b|provenance|val_loss|hf_)"
                     r"|_A_[\w-]+\.md$", f):
            votes.add("A")
        if re.search(r"summaries/trackB|progress/(run_trackB|trackB_report|sol_trackB|run_b15|voyager_template)"
                     r"|tests/test_trackB|(handoff|tracks)/TRACK_B|_B_[\w-]+\.md$", f):
            votes.add("B")
        if re.search(r"summaries/trackC|cot-disclosure/agents/|tests/test_trackC|(handoff|tracks)/TRACK_C|_C_[\w-]+\.md$", f):
            votes.add("C")
        if re.search(r"label_kit|LABEL|RATER_GUIDE|tests/test_label", f):
            votes.add("Labels")
    if not votes:
        s = c["subject"]
        for t, p in (("A", r"Track A|\bStep \d|\bset A\b|Gate 3|\bSol\b"), ("B", r"Track B|\bB1[0-5]\b"),
                     ("C", r"Track C|\bC\d{1,2}\b"), ("Labels", r"\blabel")):
            if re.search(p, s):
                votes.add(t)
    return "+".join(t for t in TRACKS if t in votes) or "ALL"


# ---------------------------------------------------------------- sessions
def session_files(root):
    """{name: path} of every session log and daily: in archive/sessions/<YYYY-MM-DD>/ (since Oct 30), else in the
    old flat docs/sessions/ (a name in both is read from archive/)."""
    out = {}
    for folder in SESSIONS:
        for f in sorted((Path(root) / folder).rglob("*.md")):
            if f.name not in ("INDEX.md", "LATEST.md"):
                out.setdefault(f.name, f)
    return out


def overview_path(root):
    """The overview of the work before the session logs: the newest archived copy, else docs/OVERVIEW.md."""
    for pattern in OVERVIEWS:
        found = sorted(Path(root).glob(pattern))
        if found:
            return found[-1]
    return Path(root) / OVERVIEWS[-1]


def session_logs(root):
    """[{date, time, track, file, path, what, daily}] from INDEX.md, plus any log on disk that INDEX doesn't list yet
    (its first heading as the summary). A log is named by its file name wherever INDEX's link points."""
    files = session_files(root)
    index = next((Path(root) / f / "INDEX.md" for f in SESSIONS if (Path(root) / f / "INDEX.md").exists()), None)
    out, listed = [], set()
    for _, header, rows in md_tables(read(index) if index else ""):
        if column(header, "log") is None:
            continue
        for r in rows:
            when, log, what = r[column(header, "when (mst)", "when")], r[column(header, "log")], r[-1]
            m = re.search(r"\(([^)]+\.md)\)", log) or re.search(r"([\w/-]+\.md)", log)
            name = Path(m.group(1)).name if m else plain(log)
            listed.add(name)
            out.append(log_row(name, when, what, files.get(name), root))
    for name, f in sorted(files.items()):
        if name not in listed:
            first = next((plain(line.lstrip("#")) for line in read(f).splitlines() if line.startswith("#")), f.stem)
            out.append(log_row(name, "", re.sub(r"^(Session log|Daily log):\s*", "", first), f, root))
    return sorted([r for r in out if r["date"]], key=lambda r: (r["date"], r["time"] or "99:99"))


def log_row(name, when, what, path=None, root=None):
    m = re.match(r"(\d{4}-\d\d-\d\d)_(\d\d)(\d\d)_(?:(A|B|C|ALL)_)?", name)
    d = ISO.search(when) or FILEDATE.search(name)
    t = re.search(r"\b(\d\d):(\d\d)\b", when)
    time = f"{t.group(1)}:{t.group(2)}" if t else (f"{m.group(2)}:{m.group(3)}" if m else None)
    daily = name.startswith("DAILY_")
    rel = path.relative_to(root).as_posix() if path and root and Path(path).is_relative_to(root) else None
    return {"date": date(*map(int, d.groups())) if d else None, "time": None if daily else time, "file": name,
            "path": rel, "track": "ALL" if daily or not m or not m.group(4) else m.group(4),
            "what": clean(plain(what)), "daily": daily}


def compute_lines(root):
    """{date: [line]}: each daily's "Compute used" bullets, else its Voyager / Sol / Mac bullets from the brief."""
    out = {}
    for name, f in sorted(session_files(root).items()):
        if not name.startswith("DAILY_"):
            continue
        d = FILEDATE.search(f.name)
        secs = sections(read(f))
        lines = [b for h, body in secs if re.search(r"compute used", h, re.I) for b in bullets(body)]
        if not lines:
            lines = [b for h, body in secs if re.search(r"in brief", h, re.I) for b in bullets(body)
                     if re.match(r"(Voyager|Sol|Local|Mac|Paid|No paid)\b", b)]
        out[date(*map(int, d.groups()))] = [clean(x) for x in lines]
    return out


def run_phrases(text):
    """The runs a summary line names: counts of calls/runs/reviews/cases, GPU or A100 hours, Sol job ids."""
    found = [m.group(0) for m in re.finditer(r"(?<!Step )(?<!Steps )\b\d[\d,]*(?:\s*\+\s*\d[\d,]*)?\s+(?:calls|reviews|"
                                             r"runs|cases|probes|agent steps|generations)\b", text)]
    found += [m.group(0) for m in re.finditer(r"~?\d+(?:\.\d+)?(?:\s*[–-]\s*\d+(?:\.\d+)?)?\s*(?:A100|GPU)[ -]?"
                                              r"(?:h|hours|min|minutes)\b", text)]
    jobs = sorted(set(re.findall(r"\b6[5-9]\d{6}\b", text)))
    return found + ([f"Sol jobs {', '.join(jobs)}"] if jobs else [])


# ---------------------------------------------------------------- statuses, hours, owners
def classify(status, blocked_by="", is_pushed=False):
    """(status, note): one of STATUSES from TODO's status text (rules in the module docstring)."""
    raw = status.replace("\\|", "|")
    s = plain(raw).lower()
    first, _, rest = s.partition(";")
    if s.startswith("dropped"):
        return "dropped", "scope"
    if re.match(r"(done|final)\b", s) or re.search(r"\*\*done\b", raw, re.I) or "; done (" in s or (
            re.search(r"\bdone\b", first) and not re.search(r"\bnot (started|run|trained)\b", rest)):
        return "done", ""
    if s.startswith("missed"):
        return "done", "missed"
    if s.startswith("standing"):
        return "in progress", "standing"
    if re.search(r"\bblocked\b", s):
        return "blocked", ""
    words = [(r"\b(running|submitted|resubmitted|queued|pending|in progress|draft|kept current|met, interim)\b",
              "in progress"),
             (r"\b(not started|not run|not trained|decided|planned|prepared|plan fixed|ready to start|open)\b",
              "planned"),
             (r"\b(waiting for|waits (?:on|for)|asking)\b", "blocked")]
    hits = [(m.start(), st) for p, st in words for m in [re.search(p, s)] if m]
    if not hits:
        return "in progress", "no status word"
    st = min(hits)[1]
    outside = re.sub(r"(?:the )?push(?: and a pull)?", "", blocked_by or "") if is_pushed else blocked_by or ""
    if st == "planned" and OUTSIDE.search(outside):
        return "blocked", "waits on an outside step"
    return st, ""


QTY = re.compile(r"(?P<a>\d+(?:\.\d+)?)(?:\s*[–-]\s*(?P<b>\d+(?:\.\d+)?))?\s*(?P<u>GPU[- ]?h(?:ours?)?|GPU[- ]?min(?:utes)?"
                 r"|A100 h|h(?:ours?)?|min(?:utes)?|days?)\b(?P<after>\s*Voyager)?")
BARE = re.compile(r"(?P<a>\d+(?:\.\d+)?)(?:\s*[–-]\s*(?P<b>\d+(?:\.\d+)?)(?=[\s,;])|\s*(?=\+))")


def hours(time, needs=""):
    """{"work", "gpu", "voyager": hours} from TODO's time text, or from its Needs text when the time gives none
    (ranges at their midpoint; "1 day" = 8 h of work, "half a day" = 4 h; per-rater or per-part figures taken once;
    a bare range or "x +" takes the next unit; GPU or A100 hours, "h Voyager", else the Needs column says which
    kind), or None."""
    t = plain(time)
    if t.lower().startswith("done") or "from the refit" in t:
        return None
    base = re.sub(r"\([^)]*\)", "", t)
    if "half a day" in base:
        return {"work": 4.0, "gpu": 0.0, "voyager": 0.0}
    found = list(QTY.finditer(base))
    if not found:
        base = plain(needs)
        found = list(QTY.finditer(base))
        if not found:
            return None
    out = {"work": 0.0, "gpu": 0.0, "voyager": 0.0}
    used = [(m.start(), m.end()) for m in found]

    def kind(unit, after):
        if unit.startswith("day"):
            return "work"
        if "GPU" in unit or "A100" in unit:
            return "gpu"
        if after:
            return "voyager"
        if re.search(r"\bSol\b", needs or ""):
            return "gpu"
        return "voyager" if re.search(r"Voyager", needs or "") else "work"

    def value(m):
        a = float(m.group("a"))
        return (a + float(m.group("b"))) / 2 if m.group("b") else a

    def scale(unit):
        return 1 / 60 if "min" in unit else (8 if unit.startswith("day") else 1)

    for m in found:
        out[kind(m.group("u"), m.group("after"))] += value(m) * scale(m.group("u"))
    for m in BARE.finditer(base):
        if any(a <= m.start() < b for a, b in used):
            continue
        nxt = next((q for q in found if q.start() > m.start()), None)
        if nxt is not None:
            out[kind(nxt.group("u"), nxt.group("after"))] += value(m) * scale(nxt.group("u"))
    return {k: round(v, 3) for k, v in out.items()}


def owner(track, status):
    """The owner by the rule: past work Ritik's; open Track B Arsha's from Nov 6, open Track C Shrey's from Oct 30."""
    if track in TAKEOVER and status != "done":
        who, when = TAKEOVER[track]
        return f"{who} (from {when:%b} {when.day})"
    if track == "Milestones":
        return "everyone"
    return OWNER.get(track, "Ritik")


# ---------------------------------------------------------------- sources -> tasks
def task(**kw):
    t = {"id": "", "name": "", "track": "", "phase": "", "status": "planned", "note": "", "status_text": "",
         "start": None, "start_basis": "not in the repo", "start_inferred": False, "end": None,
         "end_basis": "not in the repo", "end_inferred": False, "depends": "", "owner": "", "owner_todo": "",
         "needs": "", "time": "", "hours": None, "source": "", "kind": "task", "counted": False, "from": "",
         "raw_status": "", "log_files": []}
    t.update(kw)
    return t


def phase_of(track, name):
    low = plain(name).lower()
    for pat, ph in PHASES.get(track, []):
        if re.search(pat, low):
            return ph
    return DEFAULT_PHASE.get(track, "Other")


def todo_path(root):
    """docs/status/TODO.md; docs/TODO.md in a tree from before the Nov 1 move."""
    p = Path(root) / STATUS_DIR / "TODO.md"
    return p if p.exists() else Path(root) / "docs" / "TODO.md"


TRACK_TODOS = ("docs/trackB/TODO_B.md", "docs/trackC/TODO_C.md")   # each track's own rows (Nov 3: Shrey's, Arsha's)


def todo_paths(root):
    """TODO.md, then each track's own TODO where it exists."""
    return [todo_path(root)] + [Path(root) / p for p in TRACK_TODOS if (Path(root) / p).exists()]


def todo_tasks(root, is_pushed=False):
    """Every row of every TODO task table (any header that has # and Status), in TODO.md and the tracks' own TODOs."""
    out = []
    for heading, header, rows in (t for p in todo_paths(root) for t in md_tables(read(p))):
        ci, cs = column(header, "#"), column(header, "status")
        if ci is None or cs is None:
            continue
        col = {k: column(header, *names) for k, names in {
            "name": ("item", "task"), "from": ("from", "when decided", "raised"), "dep": ("blocked by", "depends",
                                                                                          "depends on"),
            "owner": ("owner",), "needs": ("needs", "cost"), "time": ("time", "estimate")}.items()}
        h = heading.lower()
        track = ("A" if "track a" in h else "B" if "track b" in h else "C" if "track c" in h else
                 "Labels" if "label" in h else "Repo")
        for r in rows:
            get = (lambda k: r[col[k]] if col[k] is not None and col[k] < len(r) else "")
            tid = plain(r[ci])
            if not tid:
                continue
            st, note = classify(r[cs], get("dep"), is_pushed)
            kind = "gate" if track == "Repo" and re.match(r"G\d", tid) else "task"
            name = clean(plain(get("name")))
            out.append(task(id=tid, name=name, track="Milestones" if kind == "gate" else track,
                            phase="Gates" if kind == "gate" else ("Standing duties" if note == "standing" else
                                                                  phase_of(track, get("name"))),
                            status=st, note=note, status_text=clean(plain(r[cs])), depends=plain(get("dep")),
                            owner_todo=plain(get("owner")), needs=plain(get("needs")), time=plain(get("time")),
                            hours=hours(get("time"), get("needs")), source="TODO", kind=kind,
                            counted=kind == "task" and note != "standing", **{"from": plain(get("from"))},
                            raw_status=r[cs]))
    return out


def overview_tasks(root, year, today):
    """The progress round and Track A's Steps 1-10 from OVERVIEW: "What was done, in order" for the dates, the
    Track A section's bullets for the names, "Status at a glance" for done."""
    text = read(overview_path(root))
    secs = sections(text)
    rnd = next(((h, b) for h, b in secs if re.search(r"progress round", h, re.I)), ("", ""))
    rd = [d for d, _, _ in dates_in(rnd[0], year)]
    round_end = max(rd) if rd else None
    names, summary = {}, {}
    for h, body in secs:
        for m in re.finditer(r"^- \*\*(Steps? [\d–]+b?), ([^*:]+?):?\*\*", body, re.M):
            names[m.group(1).replace("Steps", "Step").replace("Step ", "")] = m.group(2).strip()
        for b in bullets(body):
            m = re.match(r"(Steps? [\d–]+b?), ", b)
            if m:
                summary[m.group(1).replace("Steps", "Step").replace("Step ", "")] = clean(b)
    done_upto = 0
    for _, header, rows in md_tables(text):
        if column(header, "done") is not None:
            for r in rows:
                if "Track A" in r[0]:
                    m = re.search(r"Steps 1–(\d+)", r[column(header, "done")])
                    done_upto = int(m.group(1)) if m else 0
    out, steps = [], {}
    for _, header, rows in md_tables(text):
        if column(header, "date") is None or column(header, "work") is None:
            continue
        for r in rows:
            ds = [d for d, _, _ in dates_in(r[column(header, "date")], year)]
            if not ds:
                continue
            work = r[column(header, "work")]
            if round_end and max(ds) <= round_end:
                out.append(task(id=f"P{len(out) + 1}", name=short(clean(work), 110), track="Setup",
                                phase="The progress round", status="done", start=min(ds), end=max(ds),
                                status_text=clean(plain(work)),
                                start_basis="OVERVIEW", end_basis="OVERVIEW", source="OVERVIEW", owner="Ritik"))
                continue
            for m in re.finditer(r"Steps? ((?:\d+b?)(?:\s*(?:–|,|and)\s*\d+b?)*)", work):
                spec = m.group(1)
                units = [spec.replace(" ", "")] if "–" in spec else re.split(r"\s*(?:,|and)\s*", spec)
                for u in units:
                    lo, hi = steps.get(u, (min(ds), max(ds)))
                    steps[u] = (min(lo, min(ds)), max(hi, max(ds)))
    for u, (lo, hi) in sorted(steps.items(), key=lambda kv: (int(re.match(r"\d+", kv[0]).group()), kv[0])):
        n = int(re.match(r"\d+", u).group())
        sid = f"Steps {u}" if "–" in u else f"Step {u}"
        st = "done" if n <= done_upto else ("in progress" if lo <= today else "planned")
        out.append(task(id=sid, name=f"{sid}: {names.get(u, '')}".rstrip(": "), track="A", phase="Steps 1–10",
                        status=st, start=lo, end=hi, start_basis="OVERVIEW", end_basis="OVERVIEW",
                        source="OVERVIEW", owner="Ritik", status_text=summary.get(u, "")))
    return out, round_end


def plan_facts(root, year):
    """Gates, PLAN's handoff dates, the timeline's windows (by clause), the evaluation deadline."""
    text = read(Path(root) / "docs" / "PLAN.md")
    gates = {}
    for m in re.finditer(rf"Gate (\d) \(({MONTHS}) (\d{{1,2}})\)", text):
        gates.setdefault(int(m.group(1)), date(year, MON[m.group(2)], int(m.group(3))))
    handoffs = {}
    for m in re.finditer(rf"Handoff to (\w+), ({MONTHS}) (\d{{1,2}})", text):
        handoffs.setdefault(m.group(1), date(year, MON[m.group(2)], int(m.group(3))))
    windows = []
    for _, header, rows in md_tables(text):
        if column(header, "when") is None or len(header) < 3:
            continue
        for r in rows:
            ds = [d for d, _, _ in dates_in(re.sub(r"\*\*\(now\)\*\*", "", r[0]), year)]
            if not ds:
                continue
            for ci, cell in enumerate(r[1:], 1):
                for clause in re.split(r";|\bthen\b", cell):
                    c = plain(clause)
                    if c:
                        windows.append({"start": min(ds), "end": max(ds), "column": header[ci], "clause": c})
    m = re.search(rf"all evaluation done by ({MONTHS}) (\d{{1,2}})", text)
    eval_by = date(year, MON[m.group(1)], int(m.group(2))) if m else None
    body = next((b for h, b in sections(text) if h.lower().startswith("deliverables")), "")
    deliverables = [plain(m.group(1)).rstrip(":") for m in re.finditer(r"^\d+\. \*\*([^*]+)\*\*", body, re.M)]
    return {"gates": gates, "handoffs": handoffs, "windows": windows, "eval_by": eval_by,
            "deliverables": deliverables}


def words(text):
    return {w for w in re.findall(r"[a-z]+", plain(text).lower().replace("-", " ")) if len(w) >= 4 and w not in STOP}


def kit_week(root, year):
    """The progress talk's week from the presentation kit at the repo root, or None."""
    for f in sorted(Path(root).glob("*presentation kit*.md")):
        m = re.search(rf"[Pp]rogress talk week of ({MONTHS}) (\d{{1,2}}) to (?:({MONTHS}) )?(\d{{1,2}})", read(f))
        if m:
            return date(year, MON[m.group(1)], int(m.group(2))), date(year, MON[m.group(3) or m.group(1)],
                                                                         int(m.group(4))), f.name
    return None


def extra_tasks(known, logs, commits):
    """Track A/B/C items named in session logs or commits but not (yet) in TODO, e.g. a new C-number: status from
    the latest mention (read / done / results -> done; else planned), dates from the first and the done mention."""
    top = defaultdict(int)
    for t in known:
        m = re.fullmatch(r"([ABC])(\d+)", t["id"])
        if m:
            top[m.group(1)] = max(top[m.group(1)], int(m.group(2)))
    mentions = defaultdict(list)
    for r in logs:
        for m in ID.finditer(r["what"] + " " + r["file"].replace("-", " ").replace("_", " ").upper()):
            mentions[m.group(0)].append((r["date"], r["what"], "log " + r["file"], r))
    for c in commits:
        for m in ID.finditer(c["subject"]):
            mentions[m.group(0)].append((c["when"].date(), c["subject"], "commit " + c["short"], None))
    out = []
    for tid, ms in sorted(mentions.items()):
        letter, n = tid[0], int(tid[1:])
        if not top.get(letter) or n <= top[letter]:
            continue
        ms.sort(key=lambda x: x[0])
        done = [x for x in ms if re.search(rf"\b{tid}\b[^.;]{{0,40}}\b(read|done|results)\b", x[1], re.I)
                or re.search(rf"{tid.lower()}-results", x[2])]
        title = next((x[1] for x in ms if x[3] is not None), ms[0][1])
        name = re.sub(rf"^{tid} pre-registered[^:]*:\s*", "", title)
        st = "done" if done else "planned"
        start = ms[0][0]
        out.append(task(id=tid, name=short(name, 110), track=letter, phase=phase_of(letter, name), status=st,
                        start=start, start_basis=f"first mention ({ms[0][2]})",
                        end=done[0][0] if done else None, end_basis=f"done ({done[0][2]})" if done else
                        "not in the repo", end_inferred=bool(done) and done[0][3] is None,
                        start_inferred=ms[0][3] is None, source="session logs, commits (not in TODO yet)",
                        counted=True, status_text=short(ms[-1][1], 200)))
    return out


# ---------------------------------------------------------------- dates per task
def commit_dates(root, hashes, commits):
    """{short hash: (date, short)} for hashes TODO names: from the branch's log, else the object itself (a commit
    from before the Oct 27 history rewrite is still in the repo, outside the branch)."""
    known = {c["short"][:7]: (c["when"].date(), c["short"]) for c in commits}
    out = {}
    for h in hashes:
        if h[:7] in known:
            out[h[:7]] = known[h[:7]]
            continue
        try:
            when = subprocess.run(["git", "-C", str(root), "show", "-s", "--format=%aI", h], capture_output=True,
                                  text=True, check=True).stdout.strip()
            out[h[:7]] = (datetime.fromisoformat(when).date(), h[:7])
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            continue
    return out


def todo_dates(tasks, logs, by_hash, findings, gates, year, today):
    """Start (TODO's From: its earliest date, or the Gate it names; a From date after today is a deadline, not a
    start) and, for done items, the done date: a date right after "done", else the latest date in the status up to
    today, else a "log HH:MM" it names, else its commits, else its findings, else From (inferred)."""
    by_time = defaultdict(list)
    for r in logs:
        if r["time"]:
            by_time[r["time"]].append(r)
    for t in tasks:
        if t["source"] != "TODO":
            continue
        frm, raw = t["from"], t.get("raw_status", "")
        found = dates_in(frm, year)
        fd = [(d, v) for d, _, v in found]
        fd += [(gd, True) for g, gd in gates.items() if re.search(rf"\bGate {g}\b", frm)]
        starts = [(d, v) for d, v in fd if t["status"] == "done" or d <= today]
        if starts:
            d, v = min(starts)
            t["start"], t["start_basis"] = d, "TODO From"
            t["start_inferred"] = v or not any(x == d for x, _, _ in found)
        if t["kind"] == "gate" or t["status"] != "done":
            continue
        s = plain(raw)
        m = re.search(rf"\b(?:done|final)\b[^;.]{{0,12}}?\b({MONTHS}) (\d{{1,2}})\b", s, re.I)
        sd = [(d, v) for d, _, v in dates_in(s, year) if d <= today]
        logs_named = []
        for lm in LOGREF.finditer(s):
            hh = f"{lm.group(2) or lm.group(4)}:{lm.group(3) or lm.group(5)}"
            if lm.group(1):
                d = date(*map(int, lm.group(1).split("-")))
                logs_named.append(d)
                t["log_files"] += [r["file"] for r in by_time.get(hh, []) if r["date"] == d]
            else:
                cands = [r for r in by_time.get(hh, []) if not t["start"] or r["date"] >= t["start"]]
                if cands:
                    first = min(cands, key=lambda r: r["date"])
                    logs_named.append(first["date"])
                    t["log_files"].append(first["file"])
        hashes = [by_hash[h[:7]] for h in HASH.findall(raw) if h[:7] in by_hash]
        frefs = [findings[int(n)][0] for n in FREF.findall(s) if int(n) in findings]
        if m:
            t["end"], t["end_basis"] = date(year, MON[m.group(1).title()], int(m.group(2))), "TODO status"
        elif sd:
            d, v = max(sd)
            t["end"], t["end_basis"], t["end_inferred"] = d, "TODO status" + (" (vague)" if v else ""), v
        elif logs_named:
            t["end"], t["end_basis"] = max(logs_named), "the session log it names"
        elif hashes:
            d, h = max(hashes)
            t["end"], t["end_basis"], t["end_inferred"] = d, f"commit {h}", True
        elif frefs:
            t["end"], t["end_basis"], t["end_inferred"] = max(frefs), "its finding's date", True
        elif fd:
            t["end"], t["end_basis"], t["end_inferred"] = max(d for d, _ in fd), "TODO From (no done date)", True
        if t["end"] and (not t["start"] or t["start"] > t["end"]):
            t["start"], t["start_basis"], t["start_inferred"] = t["end"], "set to the done date", True


def window_match(name, windows, today):
    """PLAN's timeline window whose clause the task names: all of the clause's content words (3 or more) are in the
    task's text, or the clause (2 words or more) is in it as a phrase. Only windows not over yet."""
    tw, tn = words(name), " ".join(re.findall(r"[a-z0-9]+", plain(name).lower()))
    hit = []
    for w in windows:
        cw = words(w["clause"])
        phrase = " ".join(re.findall(r"[a-z0-9]+", w["clause"].lower()))
        if w["end"] >= today and ((len(cw) >= 3 and cw <= tw) or (len(cw) >= 2 and phrase and phrase in tn)):
            hit.append(w)
    return min(hit, key=lambda w: w["end"]) if hit else None


def due_dates(tasks, facts, today, year):
    """Due dates for open items, the first that applies: a future date in the row (item, From, status), a Gate it
    names, PLAN's timeline window it names, the handoff it serves, PLAN's evaluation deadline for Track A's Sol
    work; then each item is due no later than the open items that wait on it (inferred)."""
    gates, windows = facts["gates"], facts["windows"]
    for t in tasks:
        if t["status"] == "done" or t["kind"] != "task" or t["end"]:
            continue
        row = " ".join((t["name"], t["from"], t["status_text"]))
        cands = [(d, "TODO row", v) for d, _, v in dates_in(row, year) if d > today]
        cands += [(gd, f"Gate {g} (PLAN)", False) for g, gd in gates.items()
                  if re.search(rf"\bGate {g}\b", row) and gd > today]
        w = window_match(t["name"], windows, today)
        if cands:
            t["end"], t["end_basis"], t["end_inferred"] = min(cands)
        elif w:
            t["end"], t["end_basis"] = w["end"], f"PLAN timeline ({w['start']:%b} {w['start'].day}–" \
                                                 f"{w['end']:%b} {w['end'].day}): {short(w['clause'], 60)}"
            if t["status"] == "planned" and (not t["start"] or t["start"] < w["start"]):
                t["start"], t["start_basis"], t["start_inferred"] = w["start"], "PLAN timeline", False
        else:
            for person, when in TAKEOVER.values():
                if re.search(rf"\bfor {person}\b", t["name"]) and when >= today:
                    t["end"], t["end_basis"], t["end_inferred"] = when, f"the handoff to {person}", True
            if not t["end"] and t["track"] == "A" and re.search(r"\bSol\b", t["needs"]) and facts["eval_by"]:
                t["end"], t["end_basis"], t["end_inferred"] = facts["eval_by"], "PLAN: all evaluation done by", True
    ids = {t["id"]: t for t in tasks}
    for _ in range(len(tasks)):
        changed = False
        for t in tasks:
            if not t["end"] or t["status"] == "done":
                continue
            for dep in TASKREF.findall(t["depends"]):
                d = ids.get(dep)
                if d and d["status"] != "done" and d["kind"] == "task" and (not d["end"] or d["end"] > t["end"]):
                    d["end"], d["end_basis"], d["end_inferred"] = t["end"], f"before {t['id']} (it waits on it)", True
                    changed = True
        if not changed:
            break
    for t in tasks:
        if t["start"] and t["end"] and t["start"] > t["end"]:
            t["start"], t["start_basis"], t["start_inferred"] = None, "not in the repo", False


def milestones(facts, kit, today):
    """Gates (PLAN), the handoffs (the owner rule; PLAN's date noted where it differs), the presentations and the
    report (PLAN's timeline windows; no marker where the repo gives no day)."""
    out = []
    for g, d in sorted(facts["gates"].items()):
        out.append(task(id=f"Gate {g}", name=f"Gate {g}", track="Milestones", phase="Gates", kind="milestone",
                        start=d, end=d, start_basis="PLAN", end_basis="PLAN", status="done" if d < today else "planned",
                        source="PLAN", owner="everyone"))
    for track, (who, when) in TAKEOVER.items():
        planned = facts["handoffs"].get(who)
        note = f"; PLAN says {planned:%b} {planned.day}" if planned and planned != when else ""
        out.append(task(id=f"Handoff {track}", name=f"Track {track} to {who}", track="Milestones", phase="Handoffs",
                        kind="milestone", start=when, end=when, start_basis="the owner rule" + note,
                        end_basis="the owner rule" + note, status="done" if when <= today else "planned",
                        source="owner rule", owner=who))
    if kit:
        lo, hi, name = kit
        out.append(task(id="Progress talk", name="Progress presentation (exact day not in the repo)", track="Milestones",
                        phase="Presentations and report", kind="window", start=lo, end=hi,
                        start_basis=f"week of the talk ({name})", end_basis=f"week of the talk ({name})",
                        status="done" if hi < today else "planned", source="presentation kit"))
    else:
        out.append(task(id="Progress talk", name="Progress presentation (v3 presented; date not in the repo)",
                        track="Milestones", phase="Presentations and report", kind="window", status="done",
                        source="OVERVIEW", owner="everyone"))
    for w in facts["windows"]:
        if re.search(r"presentation|report", w["clause"], re.I):
            is_report = "report" in w["clause"].lower()
            out.append(task(id=re.sub(r"\s*\(.*", "", w["clause"])[:24], name=f"{w['clause']} (exact day not in the repo)",
                            track="Milestones", phase="Presentations and report", kind="window", start=w["start"],
                            end=w["end"], start_basis="PLAN timeline window", end_basis="PLAN timeline window (its end)",
                            end_inferred=True, status="done" if w["end"] < today else "planned", source="PLAN",
                            owner="Ritik" if is_report else "everyone"))
    return out


# ---------------------------------------------------------------- what was delivered, what comes next
def own_finding(t, findings):
    """The finding a done task delivered: one whose title names the task (same track), else the first F-number its
    status names that isn't cited as a comparison ("tested against F1", "C15 refuted it (F24)"). A status naming
    three or more answers a question across findings (B9's gap, per model): no one of them is its delivery."""
    for n, f in sorted(findings.items()):
        m = re.match(r"Track ([ABC])\b[^:]*\(([^)]*)\)", f[1])
        if m and m.group(1) == t["track"] and re.search(rf"\b{re.escape(t['id'])}\b", m.group(2)):
            return n
    named = []
    for c in clauses(t["status_text"]):
        for m in FREF.finditer(c):
            if int(m.group(1)) in findings and not re.search(r"refuted", c) and not re.search(
                    r"against|tested|reworded", c[max(0, m.start() - 30):m.start()]):
                named.append(int(m.group(1)))
    return named[0] if named and len(set(named)) < 3 else None


def delivered(t, findings):
    """One line: the finding and its key number (the first interval in TODO's status, else the finding's), else the
    task's label and what its status says it produced (no hashes, log references or the word "done")."""
    lab = label(t["name"], 70)
    if t.get("finding"):
        _, title, _, _, fkey = findings[t["finding"]]
        clause = label(clauses(re.sub(r"^Track [ABC]\b[^:]*:\s*", "", title))[0], 110)
        m = INTERVAL.search(t["status_text"])
        if m:
            key = f"{m.group(1)} {m.group(2)}" if m.group(1) and m.group(1) not in clause else m.group(2)
        else:       # the finding's own first interval, if it is a difference and the title gives no number
            key = fkey if fkey and fkey[0] in "+−-" and not re.search(r"\d", clause) else None
        return f"F{t['finding']}: {clause}" + (f", {key}" if key and key not in clause else "")
    if t["source"] != "TODO":
        return short(t["status_text"] or t["name"], 220)
    s = t["raw_status"] or t["status_text"]
    for _ in range(3):              # a hash at either end of parentheses goes; one inside a sentence stays
        s = re.sub(r"(?<=\()\s*`[0-9a-f]{7,12}`\s*[,:;]?\s*|\s*[,;]?\s*`[0-9a-f]{7,12}`\s*(?=\))", "", s)
    s = LOGREF.sub("", clean(plain(s)))
    m = re.search(rf"\b(?:done|final)\b(?: for [^:;(]+?)?(?: (?:on )?(?:{MONTHS}) \d{{1,2}}[^:;(]{{0,12}})?"
                  r"(?: \([^)]*\))?: (.+)", s, re.I)
    if m:
        rest = m.group(1)
    else:
        rest = re.sub(rf"^\s*(?:done|final)\b(?: (?:for [^:;(]+|about|on))?"
                      rf"(?: (?:{MONTHS}) \d{{1,2}}(?: ~?\d\d:\d\d)?)?\s*[:,.;]?\s*", "", s, flags=re.I)
    rest = re.sub(r"\(\s*\)", "", rest).strip(" ,;:")
    rest = clauses(rest)[0] if rest else ""
    if re.fullmatch(r"\([^()]*\)", rest):
        rest = rest[1:-1]
    if set(re.findall(r"[a-z0-9]+", rest.lower())) <= set(re.findall(r"[a-z0-9]+", lab.lower())):
        rest = ""                   # the status only repeats the label
    return lab + (("; " if ":" in lab else ": ") + short(rest, 160) if rest else "")


def evidence(t, data):
    """(findings, session logs, commits) for a done task: the F-numbers its status names (with the commit that added
    each), the logs it names (else a log on its done date named for it), the hashes it names (else a commit on its
    done date or the next whose subject names it)."""
    findings, tid = data["findings"], t["id"]
    fs = sorted({int(n) for n in FREF.findall(t["status_text"]) if int(n) in findings} | (
        {t["finding"]} if t.get("finding") else set()))
    fcol = ", ".join(f"F{n}" + (f" ({findings[n][2]})" if findings[n][2] else " (not committed yet)") for n in fs)
    near = (lambda d: t["end"] and t["end"] <= d <= t["end"] + timedelta(1))
    logs = list(dict.fromkeys(t["log_files"])) or [
        r["file"] for r in data["logs"] if near(r["date"]) and not r["daily"] and (
            re.search(rf"[_-]{tid}[_-]", r["file"], re.I) or re.match(rf"{tid}\b", r["what"]))][:2]
    hashes = [h[:7] for h in HASH.findall(t["raw_status"])] or [
        c["short"] for c in data["commits"] if near(c["when"].date()) and (
            re.match(rf"{tid}\b", c["subject"]) or (len(tid) > 2 and re.search(rf"\b{tid}\b", c["subject"])))][:2]
    if t["source"] == "OVERVIEW":
        logs = [overview_path(data["root"]).relative_to(data["root"]).as_posix()]
    return fcol, ", ".join(logs), ", ".join(dict.fromkeys(hashes))


def span_text(lo, hi):
    """'Nov 23–29', 'Nov 30–Dec 6', 'Nov 8'."""
    if lo == hi:
        return f"{lo:%b} {lo.day}"
    return f"{lo:%b} {lo.day}–" + (f"{hi.day}" if (lo.year, lo.month) == (hi.year, hi.month) else f"{hi:%b} {hi.day}")


def latest_clause(status):
    """The newest update in a status: its first clause that starts with a date, else its first clause."""
    cl = clauses(plain(status))
    return next((c for c in cl if re.match(rf"(?:{MONTHS}) \d{{1,2}}\b", c)), cl[0] if cl else "")


def waiting_for(t):
    """What a blocked task waits for: the status clause that says so (no leading date), else its Blocked by."""
    for c in clauses(t["status_text"]):
        if re.search(r"\b(waiting for|waits? (?:on|for)|asking|blocked by)\b", c):
            return re.sub(rf"^(?:{MONTHS}) \d{{1,2}}[^:]*:\s*", "", c)
    return t["depends"] if t["depends"] not in ("", "—", "-") else "not said in TODO"


def next_action(t, by_id):
    """The next concrete step for an open task, in TODO's own words (rules in the module docstring)."""
    item = short(unparen(t["name"]), 130)
    stop = (lambda s: s if s.endswith((".", "?", "!", "…")) else s + ".")
    if t["status"] == "in progress":
        latest = latest_clause(t["status_text"])
        return f"Finish: {stop(label(t['name'], 80))}" + (f" Latest: {short(latest, 150)}" if latest else "")
    if t["status"] == "blocked":
        return f"Waiting: {stop(short(waiting_for(t), 120))} Then: {item}"
    deps = [d for d in TASKREF.findall(t["depends"]) if d in by_id and by_id[d]["status"] != "done"]
    step = "Pre-register, then run" if re.search(r"pre-regist", t["status_text"]) else "Start"
    return (f"After {', '.join(deps)}: {step.lower()}: " if deps else f"{step}: ") + item


def milestone_needs(data):
    """{milestone id: [need]}, each need {id, text, status, owner, due, basis, inferred} for the milestones ahead
    (rules in the module docstring)."""
    tasks, today, facts = data["tasks"], data["today"], data["facts"]
    by_id = {t["id"]: t for t in tasks if t["kind"] == "task"}
    ahead = sorted((t for t in tasks if t["kind"] in ("milestone", "window") and t["start"] and t["end"] >= today),
                   key=lambda t: t["start"])
    gates = [m for m in ahead if m["phase"] == "Gates"]
    out = {}
    for m in ahead:
        got, seen = [], set()

        def add(t, basis, inferred=False, text=None):
            if t is not None and t["id"] in seen:
                return
            if t is not None:
                seen.add(t["id"])
            got.append({"id": t["id"] if t else "", "text": text or label(t["name"]), "status": t["status"] if t
                        else "", "owner": t["owner"] if t else "", "due": t["end"] if t else None, "basis": basis,
                        "inferred": inferred})
        if m["phase"] == "Gates":
            gid = m["id"].replace("Gate ", "G")
            direct = [d for d in TASKREF.findall(m["depends"]) if d in by_id]
            queue = [(d, f"TODO {gid}: Blocked by", 0) for d in direct]
            while queue:                    # what those wait on: done ones one step down, open ones all the way
                d, why, depth = queue.pop(0)
                if d not in seen and (depth <= 1 or by_id[d]["status"] != "done"):
                    add(by_id[d], why)
                    queue += [(x, f"{d} waits on it (TODO)", depth + 1) for x in TASKREF.findall(by_id[d]["depends"])
                              if x in by_id]
            tracks = {by_id[d]["track"] for d in direct}
            for h in ahead:
                if h["phase"] == "Handoffs" and h["start"] <= m["start"] and h["id"][-1] in tracks:
                    add(None, f"Track {h['id'][-1]} is needed by {m['id']} (the owner rule)", True,
                        f"{h['name']}, {h['start']:%b} {h['start'].day}")
                    for t in tasks:
                        if t["kind"] == "task" and t["status"] != "done" and re.search(rf"\bfor {h['owner']}\b",
                                                                                         t["name"]):
                            add(t, f"the handoff to {h['owner']}", True)
            for t in sorted(tasks, key=lambda t: (t["end"] or date.max, id_key(t))):
                if (t["kind"] == "task" and t["status"] != "done" and t["note"] != "standing" and t["track"] in tracks
                        and t["end"] and t["end"] <= m["start"]):
                    add(t, f"due by {m['id']}: {t['end_basis']}", True)
            for t in tasks:
                if t["status"] == "done" and re.search(rf"\b{m['id']}\b", t["name"]):
                    rerun = next((c for c in clauses(t["status_text"]) if re.search(r"\brerun", c)), None)
                    if rerun:
                        add(None, f"{t['id']} is done; its status says it reruns (TODO)", True,
                            f"{t['id']} again: {short(rerun, 90)}")
        elif m["phase"] == "Handoffs":
            for t in tasks:
                if t["kind"] == "task" and t["status"] != "done" and re.search(rf"\bfor {m['owner']}\b", t["name"]):
                    add(t, f"its item names {m['owner']}")
            for w in facts["windows"]:
                if w["end"] == m["start"] and re.search(r"handoff|bundle", w["clause"], re.I) and \
                        not re.search(r"handoff to", w["clause"], re.I):
                    add(None, f"PLAN timeline ({span_text(w['start'], w['end'])})", False, w["clause"])
            moving = [t["id"] for t in sorted(tasks, key=id_key) if t["kind"] == "task" and t["track"] == m["id"][-1]
                      and t["status"] != "done" and t["note"] != "standing"]
            if moving:
                add(None, "the owner rule", False, f"open Track {m['id'][-1]} items move to {m['owner']}: "
                                                   + ", ".join(moving))
        else:
            row = [w for w in facts["windows"] if (w["start"], w["end"]) == (m["start"], m["end"])]
            for w in row:
                hits = [t for t in tasks if t["kind"] == "task" and w["clause"][:40] in t["end_basis"]]
                for t in hits:
                    add(t, f"PLAN timeline ({span_text(w['start'], w['end'])}): {short(w['clause'], 50)}")
                if not hits and not re.search(r"presentation|report", w["clause"], re.I):
                    add(None, f"PLAN timeline, {w['column']} ({span_text(w['start'], w['end'])})", False,
                        f"{w['clause']} ({w['column']})")
            if re.search(r"draft", m["id"], re.I):
                before = [g for g in gates if g["start"] <= m["start"]]
                if before:
                    g = before[-1]
                    add(None, "PLAN gates (the gate before this window)", True,
                        f"{g['id']}'s result, {g['start']:%b} {g['start'].day}")
                for t in sorted(tasks, key=lambda t: (t["end"] or date.max, id_key(t))):
                    earlier = {n["id"] for v in out.values() for n in v}
                    if (t["kind"] == "task" and t["status"] != "done" and t["note"] != "standing" and t["end"]
                            and t["end"] <= m["end"] and t["id"] not in earlier):
                        add(t, "a result due before the draft report", True)
            else:
                prev = [w for w in ahead if w["kind"] == "window" and w["end"] < m["start"]]
                if prev:
                    add(None, "PLAN timeline (the window before)", True,
                        f"{prev[-1]['id']}, {span_text(prev[-1]['start'], prev[-1]['end'])}")
                for i, d in enumerate(facts["deliverables"], 1):
                    tr = next((x for x, p in (("A", r"Track A"), ("B", r"Track B"), ("C", r"Track C"),
                                              ("Labels", r"label"), ("Repo", r"code|github")) if re.search(p, d, re.I)),
                              None)
                    ts = [t for t in tasks if t["counted"] and t["track"] == tr]
                    left = [t["id"] for t in sorted(ts, key=id_key) if t["status"] != "done"]
                    state = (f"{len(ts) - len(left)} of {len(ts)} of its track's tasks done" +
                             (f"; open: {', '.join(left)}" if left else "")) if ts else "no task rows"
                    add(None, f"PLAN deliverable {i} (its track's tasks)", True, f"{d}: {state}")
        out[m["id"]] = got
    return out


def annotate(data):
    """Each done task's finding, delivery line and evidence; each open task's next action and the milestone it
    feeds; what each milestone needs."""
    by_id = {t["id"]: t for t in data["tasks"] if t["kind"] == "task"}
    for t in data["tasks"]:
        if t["kind"] != "task":
            continue
        if t["status"] == "done":
            t["finding"] = own_finding(t, data["findings"]) if t["source"] == "TODO" else None
            t["delivered"] = delivered(t, data["findings"])
            t["evidence"] = evidence(t, data)
        elif t["note"] != "standing":
            t["next"] = next_action(t, by_id)
    data["needs"] = milestone_needs(data)
    for mid, needs in data["needs"].items():
        for n in needs:
            if n["id"] in by_id:
                by_id[n["id"]].setdefault("feeds", mid)


# ---------------------------------------------------------------- the model
def collect(root, today, year=FIRST.year):
    """Every task, milestone and record the sheets are made from (dates without a year are in the project's year)."""
    root = Path(root)
    commits = git_log(root)
    logs = session_logs(root)
    findings = finding_dates(root, today)
    facts = plan_facts(root, year)
    upstream = pushed(root)
    todo = todo_tasks(root, bool(upstream))
    dropped = [t for t in todo if t["status"] == "dropped"]
    hist, round_end = overview_tasks(root, year, today)
    hashes = {h for t in todo for h in HASH.findall(t.get("raw_status", ""))}
    todo_dates(todo, logs, commit_dates(root, hashes, commits), findings, facts["gates"], year, today)
    extra = extra_tasks(todo, logs, commits)              # dropped items count as known: a log naming one adds nothing
    tasks = hist + [t for t in todo if t["status"] != "dropped"] + extra
    for t in tasks:
        if not t["owner"]:
            t["owner"] = owner(t["track"], t["status"])
    due_dates(tasks, facts, today, year)
    gate_rows = {t["id"]: t for t in tasks if t["kind"] == "gate"}
    ms = milestones(facts, kit_week(root, year), today)
    for m in ms:
        g = gate_rows.get(m["id"].replace("Gate ", "G"))
        if g:
            m["status_text"] = g["status_text"]
            m["name"] = f"{m['name']}: {short(clauses(re.sub(r'^Gate \d \([^)]*\):?\s*', '', g['name']))[0], 90)}"
            m["status"] = "done" if g["status_text"].lower().startswith("missed") else m["status"]
            m["depends"] = g["depends"]
    tasks = [t for t in tasks if t["kind"] != "gate"] + ms
    for c in commits:
        c["track"] = commit_track(c, round_end)
    data = {"tasks": tasks, "commits": commits, "logs": logs, "findings": findings, "facts": facts, "root": root,
            "compute": compute_lines(root), "round_end": round_end, "today": today, "head": head_commit(root),
            "pushed": upstream, "dropped": dropped}
    annotate(data)
    return data


def days(first=FIRST, last=LAST):
    return [first + timedelta(i) for i in range((last - first).days + 1)]


def day_cells(t, today, span):
    """{day: status or "milestone"} for one row of the Gantt."""
    out = {}
    if t["kind"] == "milestone":
        if t["start"]:
            out[t["start"]] = "milestone"
        return out
    lo, hi = t["start"], t["end"]
    st = t["status"]
    if st == "done" or t["kind"] == "window":
        if lo and hi:
            for d in span:
                if lo <= d <= hi:
                    out[d] = "done" if st == "done" else "planned"
        return out
    if st in ("in progress", "blocked"):
        lo = lo or today
        for d in span:
            if lo <= d <= today:
                out[d] = st
            elif hi and today < d <= hi:
                out[d] = "planned"
        return out
    if hi:
        lo = max(lo or today, today)
        for d in span:
            if lo <= d <= hi:
                out[d] = "planned"
    return out


def basis(t):
    s = f"start: {t['start_basis']}{' (inferred)' if t['start'] and t['start_inferred'] else ''}"
    e = f"end: {t['end_basis']}{' (inferred)' if t['end'] and t['end_inferred'] else ''}"
    return f"{s}; {e}"


def iso(d):
    return d.isoformat() if d else "not in the repo"


def id_key(t):
    m = re.search(r"(\d+)", t["id"])
    return (re.sub(r"s?\s*\d.*", "", t["id"]), int(m.group(1)) if m else 0, t["id"])


def task_order(t):
    """A Gantt's order: by start (else end), undated last, then by ID."""
    return (t["start"] or t["end"] or date.max, id_key(t))


def gantt_sheet(data, span):
    """Rows by track, phase, task (a phase's tasks by start): the left columns and the per-day status."""
    today, rows = data["today"], []
    left = ["ID", "Task", "Owner", "Start", "End / due", "Status", "Date basis", "Depends on", "Details (TODO's item)",
            "Source"]
    by = defaultdict(lambda: defaultdict(list))
    for t in data["tasks"]:
        by[t["track"]][t["phase"]].append(t)
    for track in TRACKS:
        if track not in by:
            continue
        rows.append({"kind": "track", "values": [TRACK_NAME[track]] + [""] * (len(left) - 1), "days": {}})
        phases = sorted(by[track], key=lambda p: min((t["start"] or LAST) for t in by[track][p]))
        for ph in phases:
            ts = sorted(by[track][ph], key=task_order)
            done = sum(t["status"] == "done" for t in ts)
            rows.append({"kind": "phase", "values": [f"{ph} ({done} of {len(ts)} done)"] + [""] * (len(left) - 1),
                         "days": {}})
            for t in ts:
                status = t["status"] + (f" ({t['note']})" if t["note"] in ("missed", "standing") else "")
                rows.append({"kind": t["kind"], "status": t["status"], "values": [
                    t["id"], label(t["name"]), t["owner"], iso(t["start"]), iso(t["end"]), status, basis(t),
                    t["depends"] if t["depends"] not in ("—", "-") else "", short(t["name"], 300), t["source"]],
                    "days": {d.isoformat(): v for d, v in day_cells(t, today, span).items()}})
    marks = {t["start"].isoformat(): t["id"] for t in data["tasks"] if t["kind"] == "milestone" and t["start"]}
    return {"columns": left + [d.isoformat() for d in span], "left": len(left), "rows": rows, "milestones": marks}


def daily_sheet(data):
    """One row per day and track: the work, the runs as logged, findings added, commits."""
    work, runs, fnd, coms, srcs = (defaultdict(list) for _ in range(5))
    for r in data["logs"]:
        key = (r["date"], r["track"])
        work[key].append((f"{r['time']} " if r["time"] else "Daily: ") + r["what"])
        runs[key] += run_phrases(r["what"])
        srcs[key].append(r["file"])
    for d, lines in data["compute"].items():
        runs[(d, "ALL")] += ["compute (daily): " + "; ".join(lines)] if lines else []
    for n, (d, title, h, tr, _) in data["findings"].items():
        fnd[(d, tr)].append(f"F{n}" + ("" if h else " (not committed yet)"))
    first_log = min((r["date"] for r in data["logs"]), default=None)
    for c in data["commits"]:
        for tr in c["track"].split("+"):
            coms[(c["when"].date(), tr)].append(c)
    for (d, tr), cs in coms.items():
        if first_log is None or d < first_log:
            work[(d, tr)].append("From commits (no session log before " + (f"{first_log:%b} {first_log.day}"
                                 if first_log else "any") + "): " + " | ".join(short(c["subject"], 100) for c in cs))
            srcs[(d, tr)].append("git log (inferred)")
        elif not work.get((d, tr)):
            work[(d, tr)].append("From commits (no session log for this track that day): "
                                 + " | ".join(short(c["subject"], 100) for c in cs))
            srcs[(d, tr)].append("git log")
    keys = sorted(set(work) | set(runs) | set(fnd) | set(coms), key=lambda k: (k[0], TRACKS.index(k[1])
                                                                                 if k[1] in TRACKS else 99))
    rows = []
    for d, tr in keys:
        cs = coms.get((d, tr), [])
        rows.append([d.isoformat(), f"{d:%a}", TRACK_NAME.get(tr, tr), short(" || ".join(work.get((d, tr), [])), 3000),
                     short("; ".join(dict.fromkeys(runs.get((d, tr), []))), 2000),
                     ", ".join(sorted(fnd.get((d, tr), []), key=lambda f: int(f[1:].split()[0]))), len(cs),
                     " ".join(c["short"] for c in cs), ", ".join(dict.fromkeys(srcs.get((d, tr), []))) or "git log"])
    return {"columns": ["Date", "Day", "Track", "What was done", "Runs and compute (as logged)", "Findings added",
                        "Commits", "Hashes", "Sources"], "rows": rows}


def changes_sheet(data):
    rows = [[c["when"].date().isoformat(), c["when"].strftime("%H:%M"), c["short"], c["track"], short(c["subject"], 120),
             len(c["files"])] for c in reversed(data["commits"])]
    return {"columns": ["Date", "Time (MST)", "Hash", "Track (A, B, C, Labels, Setup, ALL; + = several)",
                        "Summary (first 120 characters)", "Files"], "rows": rows}


def progress_rows(data):
    """Per track: counted tasks done of total, by count and weighted by TODO's time; remaining hours by kind."""
    out = []
    groups = [tr for tr in TRACKS if tr not in ("Milestones", "Setup")] + ["All"]
    for tr in groups:
        ts = [t for t in data["tasks"] if t["counted"] and (tr == "All" or t["track"] == tr)]
        if not ts:
            continue
        done = [t for t in ts if t["status"] == "done"]
        est = [t for t in ts if t["hours"]]
        h = (lambda t: sum(t["hours"].values()))
        tot, hd = sum(h(t) for t in est), sum(h(t) for t in est if t["status"] == "done")
        left = [t for t in est if t["status"] != "done"]
        rem = {k: round(sum(t["hours"][k] for t in left), 2) for k in ("work", "gpu", "voyager")}
        out.append({"track": TRACK_NAME.get(tr, tr), "tasks": len(ts), "done": len(done),
                    **{st: sum(t["status"] == st for t in ts) for st in STATUSES[1:]},
                    "percent": round(100 * len(done) / len(ts), 1), "with_estimate": len(est),
                    "without_estimate": len(ts) - len(est), "hours_done": round(hd, 2), "hours_total": round(tot, 2),
                    "percent_weighted": round(100 * hd / tot, 1) if tot else None,
                    "remaining_hours": round(sum(rem.values()), 2), "remaining_work": rem["work"],
                    "remaining_gpu": rem["gpu"], "remaining_voyager": rem["voyager"],
                    "open_without_estimate": sum(1 for t in ts if t["status"] != "done" and not t["hours"])})
    return out


def progress_sheet(data):
    rows = progress_rows(data)
    cols = ["Track", "Tasks", "Done", "In progress", "Planned", "Blocked", "Done % (by count)", "With a time estimate",
            "Without one", "Hours done", "Hours estimated", "Done % (weighted by time)", "Remaining hours",
            "Remaining: work", "Remaining: GPU", "Remaining: Voyager", "Open tasks without an estimate"]
    keys = ["track", "tasks", "done", "in progress", "planned", "blocked", "percent", "with_estimate", "without_estimate",
            "hours_done", "hours_total", "percent_weighted", "remaining_hours", "remaining_work", "remaining_gpu",
            "remaining_voyager", "open_without_estimate"]
    vals = [[r[k] if r[k] is not None else "no estimates" for k in keys] for r in rows]
    tasks = data["tasks"]
    notes = [
        "Counted: TODO's task rows and items named in session logs or commits that TODO doesn't list yet; not "
        "counted: gates, handoffs, presentations, the report (milestones), standing duties ("
        + ", ".join(t["id"] for t in tasks if t["note"] == "standing") + ") and the history rows from OVERVIEW.",
        "Weighted: TODO's Time column (working time for code and docs, GPU or Voyager time for runs; ranges at "
        "their midpoint, 1 day = 8 h, per-rater or per-part figures once; the Needs column's hours where Time has "
        "none); rows with no hours in either have no estimate.",
        "Read as in progress (no status word in TODO): " + (", ".join(t["id"] for t in tasks if t["note"] ==
                                                                     "no status word") or "none") + ".",
        "Blocked because 'Blocked by' names an outside step (push, rater, keys, decision): " + (", ".join(
            t["id"] for t in tasks if t["note"] == "waits on an outside step") or "none") + ".",
        "Not in TODO yet (from session logs or commits): " + (", ".join(t["id"] for t in tasks if "not in TODO" in
                                                                       t["source"]) or "none") + ".",
    ]
    return {"columns": cols, "rows": vals, "notes": notes}


def need_text(n):
    """One need of a milestone: "L3 Label the queue… (blocked)", "(inferred)" where it was derived."""
    head = f"{n['id']} {n['text']}" if n["id"] else n["text"]
    return head + (f" ({n['status']})" if n["status"] else "") + (" (inferred)" if n["inferred"] else "")


def todo_sheet(data):
    """Every open task by due date, with its next action, and a row per milestone ahead with what it needs (it
    sorts after the tasks due the same day). It replaces the old Remaining sheet."""
    open_ = [t for t in data["tasks"] if t["kind"] == "task" and t["status"] != "done" and t["note"] != "standing"]
    ms = [m for m in data["tasks"] if m["id"] in data["needs"] and m["status"] != "done"]
    rows = []
    for t in sorted(open_ + ms, key=lambda t: (t["end"] or date.max, t["kind"] != "task", t["start"] or date.max,
                                               TRACKS.index(t["track"]), id_key(t))):
        due_from = t["end_basis"] + (" (inferred)" if t["end"] and t["end_inferred"] else "")
        if t["kind"] == "task":
            rows.append([iso(t["end"]), t["id"], label(t["name"]), TRACK_NAME[t["track"]], t["owner"], t["next"],
                         t["status"], t["time"] if t["time"] and t["time"] != "—" else "",
                         round(sum(t["hours"].values()), 2) if t["hours"] else "",
                         t["depends"] if t["depends"] not in ("—", "-") else "", t.get("feeds", ""), due_from, "task"])
        else:
            needs = data["needs"][t["id"]]
            rows.append([iso(t["end"]), t["id"], label(t["name"], 80), TRACK_NAME["Milestones"], t["owner"],
                         "Needs: " + "; ".join(need_text(n) for n in needs) if needs else "nothing named in the repo",
                         t["status"], "", "", ", ".join(n["id"] for n in needs if n["id"]), "", due_from, t["kind"]])
    return {"columns": ["Due", "ID", "Task", "Track", "Owner", "Next action", "Status", "Estimate (TODO)", "Hours",
                        "Blocked by / depends on", "Feeds (the first milestone that needs it)", "Due date from",
                        "Kind"], "rows": rows, "notes": todo_checks(data)}


def done_sheet(data):
    """Every finished task by its done date: what it delivered and the evidence."""
    done = [t for t in data["tasks"] if t["kind"] == "task" and t["status"] == "done"]
    rows = []
    for t in sorted(done, key=lambda t: (t["end"] or date.max, TRACKS.index(t["track"]), id_key(t))):
        f, logs, commits = t["evidence"]
        rows.append([iso(t["end"]), t["id"], label(t["name"]), TRACK_NAME[t["track"]], t["phase"], t["owner"],
                     t["delivered"], f, logs, commits,
                     t["end_basis"] + (" (inferred)" if t["end"] and t["end_inferred"] else "")])
    return {"columns": ["Done", "ID", "Task", "Track", "Phase", "Owner", "What it delivered", "Findings (commit)",
                        "Session logs", "Commits", "Done date from"], "rows": rows}


def todo_checks(data):
    """TODO rows worth a second look: no status word; blocked by a push that is done; a Sol job that one row calls
    pending or queued and a row calls failed, done, passed, cancelled or removed; a done row that still says it
    waits, is pending, queued, running or unread."""
    rows = [t for t in data["tasks"] if t["source"] == "TODO" and t["kind"] == "task"]
    out = []
    word = [t["id"] for t in rows if t["note"] == "no status word"]
    if word:
        out.append("No status word (read as in progress): " + ", ".join(word) + ".")
    if data.get("pushed"):
        push = [t["id"] for t in rows if t["status"] != "done" and re.search(r"\bpush\b", t["depends"])]
        if push:
            out.append(f"'Blocked by' names the push, but {data['pushed']} already holds HEAD: "
                       + ", ".join(push) + ".")
    pending, closed = defaultdict(set), defaultdict(set)
    for t in rows:
        for c in clauses(t["name"] + "; " + plain(t["raw_status"])):
            for part in re.split(r"(?<=[a-z)])\. ", c):
                for m in re.finditer(r"\b(6\d{7})\b(?:/\d+)?\s*\(?(pending|queued)\b", part):
                    pending[m.group(1)].add(t["id"])
                if re.search(r"\b(fail\w*|done|passed|cancel\w*|removed)\b", part):
                    for j in re.findall(r"\b6\d{7}\b", part):
                        closed[j].add(t["id"])
    for j in sorted(pending):
        if closed.get(j):
            out.append(f"Sol job {j}: pending or queued in {', '.join(sorted(pending[j]))}; failed, done or passed in "
                       f"{', '.join(sorted(closed[j]))}.")
    stale = [t["id"] for t in rows if t["status"] == "done" and re.search(
        r"\b(unread|pending|queued|running|waits? (?:on|for)|waiting for|needs [^;]* from Sol)\b", t["status_text"])]
    if stale:
        out.append("Done, but the status still says it waits, is pending, queued, running or unread: "
                   + ", ".join(stale) + ".")
    return out or ["none"]


def inferred_count(tasks):
    return sum(bool(t["start"] and t["start_inferred"]) + bool(t["end"] and t["end_inferred"]) for t in tasks)


def build(root=ROOT, today=None, first=FIRST, last=LAST):
    """The workbook model: {"meta", "sheets": {Gantt, To do, Done, Progress, Daily, Changes}}, plus the data."""
    today = today or date.today()
    data = collect(root, today, first.year)
    span = days(first, last)
    sheets = {"Gantt": gantt_sheet(data, span), "To do": todo_sheet(data), "Done": done_sheet(data),
              "Progress": progress_sheet(data), "Daily": daily_sheet(data), "Changes": changes_sheet(data)}
    meta = {"today": today, "commit": data["head"], "generated": today.isoformat(), "first": first, "last": last,
            "inferred": inferred_count(data["tasks"]),
            "daily_inferred": sum("(inferred)" in r[-1] for r in sheets["Daily"]["rows"])}
    return {"meta": meta, "sheets": sheets, "data": data}


# ---------------------------------------------------------------- writers
def write_xlsx(model, path):
    import xlsxwriter
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = xlsxwriter.Workbook(str(path))
    meta, sh = model["meta"], model["sheets"]
    base = {"font_name": "Arial", "font_size": 9, "valign": "top"}
    fmt = {k: wb.add_format({**base, **v}) for k, v in {
        "text": {"text_wrap": True}, "head": {"bold": True, "bg_color": GRID, "text_wrap": True, "border": 1,
                                              "border_color": "#c9c8c3"},
        "title": {"bold": True, "font_size": 12}, "track": {"bold": True, "font_size": 10, "bg_color": "#d9e6f5"},
        "phase": {"bold": True, "italic": True, "bg_color": "#f1f0ec"}, "note": {"italic": True, "font_color": MUTED,
                                                                                 "text_wrap": True},
        "flat": {"italic": True, "font_color": MUTED}, "line": {}, "bold": {"bold": True}}.items()}
    cache = {}

    def cell(fill=None, today=False, mark=False, head=False):
        key = (fill, today, mark, head)
        if key not in cache:
            f = {**base, "align": "center", "valign": "vcenter", "font_size": 7 if head else 9}
            if fill:
                f.update({"bg_color": FILL[fill], "pattern": 1})
            if mark:
                f.update({"bold": True, "font_color": INK, "font_size": 10})
            if today:
                f.update({"left": 2, "right": 2, "left_color": "#d03b3b", "right_color": "#d03b3b"})
            if head:
                f.update({"bold": True, "bg_color": "#fbe3e3" if today else GRID})
            cache[key] = wb.add_format(f)
        return cache[key]

    # Gantt
    g = sh["Gantt"]
    ws = wb.add_worksheet("Gantt")
    nl, span = g["left"], g["columns"][g["left"]:]
    today = meta["today"].isoformat()
    ws.write(0, 0, f"Gantt, {meta['first']:%b} {meta['first'].day} to {meta['last']:%b} {meta['last'].day}, "
                   f"{meta['last'].year}: generated by tools/make_gantt.py on {meta['generated']} from {meta['commit']}; "
                   f"today = {today} (red column)", fmt["title"])
    ws.write(1, 0, "Legend:", fmt["head"])
    ws.write(1, 1, "◆ milestone; red border = today; 'inferred' in the Date basis column marks a derived date; "
                   "+/- at the left folds a track or phase; the item in full: the Details column", fmt["flat"])
    for i, st in enumerate(STATUSES):
        ws.write(1, nl + 9 * i, "", cell(st))
        ws.write(1, nl + 9 * i + 1, st, fmt["flat"])
    months = defaultdict(list)
    for j, d in enumerate(span):
        months[d[:7]].append(j)
    for ym, js in months.items():
        month = datetime.strptime(ym, "%Y-%m").strftime("%B %Y")
        if len(js) > 1:
            ws.merge_range(2, nl + js[0], 2, nl + js[-1], month, fmt["head"])
        else:
            ws.write(2, nl + js[0], month, fmt["head"])
    for j, h in enumerate(g["columns"][:nl]):
        ws.write(4, j, h, fmt["head"])
    for j, d in enumerate(span):
        dd = date.fromisoformat(d)
        ws.write(3, nl + j, dd.day, cell(today=d == today, head=True))
        ws.write(4, nl + j, "MTWTFSS"[dd.weekday()], cell(today=d == today, head=True))
        mark = g["milestones"].get(d)
        ws.write(5, nl + j, "◆" if mark else "", cell(today=d == today, mark=bool(mark)))
    ws.write(5, 0, "Milestones", fmt["phase"])
    ws.write(5, 1, "; ".join(f"{v} {k[5:]}" for k, v in sorted(g["milestones"].items())), fmt["note"])
    r0 = 6
    for i, row in enumerate(g["rows"]):
        r = r0 + i
        level = {"track": 0, "phase": 1}.get(row["kind"], 2)
        ws.set_row(r, None, None, {"level": level})
        if row["kind"] in ("track", "phase"):
            ws.write(r, 0, row["values"][0], fmt[row["kind"]])
            for j in range(1, nl):
                ws.write_blank(r, j, None, fmt[row["kind"]])
        else:
            for j, v in enumerate(row["values"]):
                ws.write(r, j, v, fmt["bold" if j == 0 else "line"])
        for j, d in enumerate(span):
            v = row["days"].get(d)
            if v == "milestone":
                ws.write(r, nl + j, "◆", cell(today=d == today, mark=True))
            elif v or d == today:
                ws.write(r, nl + j, "", cell(v, today=d == today))
    for j, w in enumerate((9, 42, 16, 10, 10, 11, 40, 12, 60, 10)):
        ws.set_column(j, j, w)
    ws.set_column(nl, nl + len(span) - 1, 2.6)
    ws.freeze_panes(r0, 2)
    ws.outline_settings(True, False, True, False)
    ws.set_landscape()
    ws.set_paper(8)                      # A3
    ws.fit_to_pages(1, 0)
    ws.repeat_rows(2, r0 - 1)

    def table(name, s, widths, extra=None):
        w = wb.add_worksheet(name)
        for j, h in enumerate(s["columns"]):
            w.write(0, j, h, fmt["head"])
        for i, row in enumerate(s["rows"], 1):
            for j, v in enumerate(row):
                w.write(i, j, v, fmt["text"])
        for j, wd in enumerate(widths):
            w.set_column(j, j, wd)
        w.freeze_panes(1, 0)
        if s["rows"]:
            w.autofilter(0, 0, len(s["rows"]), len(s["columns"]) - 1)
        for k, note in enumerate((extra or []), len(s["rows"]) + 2):
            w.merge_range(k, 0, k, min(len(s["columns"]) - 1, 12), note, fmt["note"])
            w.set_row(k, 30)
        return w

    table("To do", sh["To do"], (11, 9, 34, 20, 17, 70, 10, 18, 7, 16, 12, 30, 9),
          ["Checks on TODO (rows worth a second look): " + n for n in sh["To do"]["notes"]])
    table("Done", sh["Done"], (11, 9, 34, 20, 18, 9, 80, 22, 34, 16, 26))
    table("Progress", sh["Progress"], (26,) + (11,) * 16, sh["Progress"]["notes"])
    table("Daily", sh["Daily"], (11, 5, 20, 90, 60, 14, 8, 30, 40))
    table("Changes", sh["Changes"], (11, 8, 9, 22, 100, 6))
    wb.close()
    return path


def plotting():
    """matplotlib (no display) with the charts' style; (plt, mdates, Line2D, Patch)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    plt.rcParams.update({"figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
                         "font.size": 8, "axes.edgecolor": "#a3a29c", "text.color": INK, "xtick.color": MUTED,
                         "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False,
                         "hatch.color": SURFACE, "hatch.linewidth": 1.0})
    return plt, mdates, Line2D, Patch


def status_bars(ax, t, y, today, span, height, mdates):
    """A task's days as bars, one run per status (blocked hatched), with a thin surface gap between runs."""
    for st in ("planned", "done", "in progress", "blocked"):
        ds = sorted(d for d, v in day_cells(t, today, span).items() if v == st)
        for lo, hi in runs_of(ds):
            ax.barh(y, (hi - lo).days + 1, left=mdates.date2num(lo), height=height, color=FILL[st],
                    edgecolor=SURFACE, linewidth=0.6, hatch="////" if st == "blocked" else None)


def milestone_labels(ax, fig, ms, y, first, last, fontsize, step=0.4):
    """Each milestone's diamond and label, its label on the lowest level (step apart, in data units) where it
    overlaps no other label (widths estimated from the characters); the number of levels used."""
    import matplotlib.dates as mdates
    pos = ax.get_position()
    per_day = fig.get_figwidth() * pos.width / ((last - first).days + 1)        # inches per day
    ends, used = [], 0
    for t in sorted(ms, key=lambda t: t["start"]):
        x = mdates.date2num(t["start"]) + 0.5
        text = (f"Track {t['id'][-1]} to {t['owner']}" if t["phase"] == "Handoffs" else t["id"]) + \
            f", {t['start']:%b} {t['start'].day}"
        half = len(text) * fontsize * 0.55 / 72 / per_day / 2 + 0.8
        level = next((i for i, e in enumerate(ends) if x - half > e), len(ends))
        if level == len(ends):
            ends.append(0)
        ends[level] = x + half
        used = max(used, level + 1)
        ax.plot(x, y, marker="D", markersize=6.5, color=INK if t["status"] == "done" else FILL["in progress"],
                markeredgecolor=SURFACE, zorder=5)
        ax.text(x, y + step * (1.05 + level), text, ha="center", va="bottom", fontsize=fontsize, color=INK, zorder=6,
                bbox={"facecolor": SURFACE, "edgecolor": "none", "pad": 0.4})
    return used


def window_bars(ax, fig, ws, y, height, first, last, fontsize):
    """The presentation and report windows as gray bars, each named inside it (on two lines when one is too wide)."""
    import matplotlib.dates as mdates
    per_day = fig.get_figwidth() * ax.get_position().width / ((last - first).days + 1)
    for t in ws:
        lo, width = mdates.date2num(t["start"]), (t["end"] - t["start"]).days + 1
        ax.barh(y, width, left=lo, height=height, color="#c9c8c3", edgecolor=SURFACE, linewidth=0.8)
        name = re.sub(r"\s*\(.*", "", t["name"])
        fits = (lambda s: len(s) * fontsize * 0.55 / 72 <= width * per_day - 0.04)
        if not fits(name):
            name = name.replace(" ", "\n", 1)
        size = fontsize if all(fits(s) for s in name.split("\n")) else fontsize * 0.82
        ax.text(lo + width / 2, y, name, ha="center", va="center", fontsize=size, color=INK, linespacing=0.95)


def legend_handles(Line2D, Patch):
    handles = [Patch(facecolor=FILL[s], label=s, hatch="////" if s == "blocked" else None) for s in STATUSES]
    return handles + [Line2D([], [], marker="D", color="w", markerfacecolor=INK, markersize=7,
                             label="milestone, passed"),
                      Line2D([], [], marker="D", color="w", markerfacecolor=FILL["in progress"], markersize=7,
                             label="milestone, ahead"),
                      Patch(facecolor="#c9c8c3", label="window (no exact day in the repo)"),
                      Line2D([], [], color=FILL["blocked"], linestyle="--", label="today")]


def overview_figure(model, size=(13.33, 7.5)):
    """The one-page overview: a bar per track and phase, colored by its tasks' status; milestones (diamonds), the
    presentation and report windows, and today."""
    plt, mdates, Line2D, Patch = plotting()
    data, meta = model["data"], model["meta"]
    today, first, last = meta["today"], meta["first"], meta["last"]
    span = days(first, last)
    groups = []
    for track in TRACKS[:-1]:
        ph = defaultdict(list)
        for t in data["tasks"]:
            if t["track"] == track and t["note"] != "standing":
                ph[t["phase"]].append(t)
        for p in sorted(ph, key=lambda p: min((t["start"] or last) for t in ph[p])):
            groups.append((track, p, ph[p]))
    fig, ax = plt.subplots(figsize=size)
    fig.subplots_adjust(left=0.175, right=0.955, top=0.875, bottom=0.115)
    n = len(groups)
    y_win, y_ms = n + 0.4, n + 1.5
    for i, (track, p, ts) in enumerate(groups):
        y = n - 1 - i
        for t in ts:
            status_bars(ax, t, y, today, span, 0.62, mdates)
        done = sum(t["status"] == "done" for t in ts)
        ax.text(mdates.date2num(last) + 1.6, y, f"{done}/{len(ts)}", va="center", fontsize=7.5, color=MUTED)
    labels = [f"{tr} · {p}" for tr, p, _ in groups]
    ax.set_yticks([n - 1 - i for i in range(n)] + [y_win, y_ms], labels + ["Talks, report", "Milestones"],
                  fontsize=7.5)
    prev = None
    for i, (tr, _, _) in enumerate(groups):
        if prev is not None and tr != prev:
            ax.axhline(n - 0.5 - i, color=GRID, linewidth=0.8)
        prev = tr
    ax.axhline(n - 0.45, color="#a3a29c", linewidth=0.8)
    levels = milestone_labels(ax, fig, [t for t in data["tasks"] if t["kind"] == "milestone" and t["start"]], y_ms,
                              first, last, 6.8)
    window_bars(ax, fig, [t for t in data["tasks"] if t["kind"] == "window" and t["start"]], y_win, 0.5, first, last,
                6.5)
    tx = mdates.date2num(today) + 0.5
    ax.axvline(tx, color=FILL["blocked"], linewidth=1.2, linestyle="--", zorder=4)
    ax.text(tx, -1.05, f"today, {today:%b} {today.day}", color=FILL["blocked"], ha="center", fontsize=7.5)
    ax.set_xlim(mdates.date2num(first), mdates.date2num(last) + 1)
    ax.set_ylim(-1.3, y_ms + 0.4 * (levels + 1.05) + 0.45)
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %-d"))
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(handles=legend_handles(Line2D, Patch), loc="upper center", bbox_to_anchor=(0.45, -0.06), ncol=8,
              fontsize=7.5, frameon=False)
    fig.suptitle(f"Group 10: project Gantt, {first:%b} {first.day} to {last:%b} {last.day}, {last.year}", x=0.01,
                 ha="left", fontsize=12, color=INK)
    fig.text(0.01, 0.935, "Each row is a phase; its bars are its tasks by status; n/N at the right = tasks done; "
                          "a page per track with a bar per task: gantt.pdf. "
                          f"Generated by tools/make_gantt.py on {meta['generated']} from {meta['commit']}.",
             fontsize=7.5, color=MUTED)
    return fig


def write_png(model, path):
    """The overview as one 16:9 page for slides."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig = overview_figure(model)
    fig.savefig(path, dpi=150)
    import matplotlib.pyplot as plt
    plt.close(fig)
    return path


PAGES = (("A",), ("B",), ("C",), ("Labels",), ("Repo", "Setup"))      # a page each; the progress round with the repo
PAGE = (11, 8.5)                                        # US Letter, landscape


def page_rows(data, tracks):
    """[(kind, phase or task)] for a track page: each phase (by its first start) and its tasks (by start)."""
    rows = []
    for track in tracks:
        ph = defaultdict(list)
        for t in data["tasks"]:
            if t["track"] == track and t["kind"] == "task":
                ph[t["phase"]].append(t)
        for p in sorted(ph, key=lambda p: min(task_order(t) for t in ph[p])):
            rows.append(("phase", f"{TRACK_NAME[track]}: {p}" if len(tracks) > 1 else p))
            rows += [("task", t) for t in sorted(ph[p], key=task_order)]
    return rows


def track_figure(model, tracks, page, pages):
    """A page per track (US Letter, landscape): a bar per task with its ID and label at the left and its status,
    owner and date at the right, phases as headers; above, the milestones and the report and presentation windows;
    gates and handoffs as dotted lines through the tasks; today."""
    plt, mdates, Line2D, Patch = plotting()
    data, meta = model["data"], model["meta"]
    today, first, last = meta["today"], meta["first"], meta["last"]
    span = days(first, last)
    rows = page_rows(data, tracks)
    units = max(sum(0.85 if k == "phase" else 1 for k, _ in rows), 24)       # a short page keeps rows of a usual height
    fig = plt.figure(figsize=PAGE)
    left, right, top, bottom, head = 0.30, 0.815, 0.79, 0.075, 1.0 / PAGE[1]
    ax = fig.add_axes((left, bottom, right - left, top - bottom))
    hx = fig.add_axes((left, top + 0.004, right - left, head), sharex=ax)
    fs = max(5.5, min(7.6, PAGE[1] * (top - bottom) * 72 / max(units, 1) * 0.74))
    trans = ax.get_yaxis_transform()
    x_id, x_label = -left / (right - left) + 0.02 / (right - left), -left / (right - left) + 0.075 / (right - left)
    y = 0.0
    for kind, item in rows:
        h = 0.85 if kind == "phase" else 1
        yc = -(y + h / 2)
        if kind == "phase":
            ax.axhspan(yc - h / 2, yc + h / 2, color="#f1f0ec", zorder=0, linewidth=0)
            ax.text(x_id, yc, item, transform=trans, ha="left", va="center", fontsize=fs, fontweight="bold",
                    style="italic", clip_on=False)
        else:
            t = item
            status_bars(ax, t, yc, today, span, 0.64, mdates)
            ax.text(x_id, yc, t["id"], transform=trans, ha="left", va="center", fontsize=fs, fontweight="bold",
                    clip_on=False)
            fit = int((left - 0.083) * PAGE[0] * 72 / (fs * 0.53))         # characters that fit the label column
            ax.text(x_label, yc, label(t["name"], fit), transform=trans, ha="left", va="center", fontsize=fs,
                    clip_on=False)
            when = (f"done {md_day(t['end'])}" if t["status"] == "done" and t["end"] else "done, no date"
                    if t["status"] == "done" else due_md(t).replace("no due date in the repo", "no due date"))
            star = "*" if t["end"] and t["end_inferred"] and "*" not in when else ""
            st = "standing duty" if t["note"] == "standing" else t["status"]
            ax.text(1.012, yc, f"{st} · {t['owner'].split()[0]}" + ("" if t["note"] == "standing" else
                                                                     f" · {when}{star}"), transform=trans,
                    ha="left", va="center", fontsize=min(fs, 7.2), color=MUTED if t["status"] == "done" else INK,
                    clip_on=False)
        y += h
    ms = [t for t in data["tasks"] if t["kind"] == "milestone" and t["start"]]
    ws = [t for t in data["tasks"] if t["kind"] == "window" and t["start"]]
    for t in ms:
        ax.axvline(mdates.date2num(t["start"]) + 0.5, color=INK if t["status"] == "done" else FILL["in progress"],
                   linewidth=0.7, linestyle=(0, (1, 2)), zorder=1)
    for t in ws:
        ax.axvspan(mdates.date2num(t["start"]), mdates.date2num(t["end"]) + 1, color="#c9c8c3", alpha=0.22, zorder=0,
                   linewidth=0)
    tx = mdates.date2num(today) + 0.5
    for a in (ax, hx):
        a.axvline(tx, color=FILL["blocked"], linewidth=1.1, linestyle="--", zorder=4)
        a.grid(axis="x", color=GRID, linewidth=0.6)
        a.set_axisbelow(True)
        a.set_yticks([])
    ax.set_xlim(mdates.date2num(first), mdates.date2num(last) + 1)
    ax.set_ylim(-units - 0.2, 0.2)
    window_bars(hx, fig, ws, 0.65, 1.0, first, last, 6.2)
    hx.set_ylim(0, 1.75 + 0.8 * (1.05 + milestone_labels(hx, fig, ms, 1.75, first, last, 6.6, step=0.8)) + 0.4)
    hx.spines["bottom"].set_visible(False)
    hx.spines["left"].set_visible(False)
    hx.tick_params(axis="x", which="both", bottom=False, labelbottom=False)
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %-d"))
    ax.tick_params(axis="x", labelsize=7)
    hx.text(-0.005, 1.75, "Milestones", transform=hx.get_yaxis_transform(), ha="right", va="center", fontsize=6.8,
            color=MUTED)
    hx.text(-0.005, 0.65, "Talks, report", transform=hx.get_yaxis_transform(), ha="right", va="center", fontsize=6.8,
            color=MUTED)
    counted = [t for t in data["tasks"] if t["counted"] and t["track"] in tracks]
    done = sum(t["status"] == "done" for t in counted)
    who = "; ".join(dict.fromkeys(f"{TAKEOVER[tr][0]} from {md_day(TAKEOVER[tr][1])} (the work before, Ritik's)"
                                  if tr in TAKEOVER else OWNER[tr] for tr in tracks))
    fig.text(0.02, 0.966, "; ".join(TRACK_NAME[t] for t in tracks), fontsize=12.5, color=INK)
    fig.text(0.02, 0.943, (f"{done} of {len(counted)} tasks done ({100 * done / len(counted):.0f}%). "
                           if counted else "") + f"Owner: {who}.", fontsize=8, color=INK)
    fig.text(0.02, 0.925, "A bar per task, by status; * = an inferred date (the Gantt sheet's Date basis says from "
                          "what); dotted lines: gates and handoffs; shaded: the report and presentation windows.",
             fontsize=7, color=MUTED)
    ax.legend(handles=legend_handles(Line2D, Patch)[:4] + legend_handles(Line2D, Patch)[-1:], loc="upper left",
              bbox_to_anchor=(-left / (right - left) + 0.02 / (right - left), -0.022), ncol=5, fontsize=7,
              frameon=False, handlelength=2.2)
    fig.text(0.98, 0.012, f"Page {page} of {pages}. Generated by tools/make_gantt.py on {meta['generated']} from "
                          f"{meta['commit']}.", ha="right", fontsize=6.5, color=MUTED)
    return fig


def write_pdf(model, path):
    """gantt.pdf: page 1 the overview, then a page per track (A, B, C, the labels, the repo with the progress
    round), US Letter, landscape."""
    from matplotlib.backends.backend_pdf import PdfPages
    import matplotlib.pyplot as plt
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pages = [tr for tr in PAGES if page_rows(model["data"], tr)]
    with PdfPages(path, metadata={"Title": "Group 10: project Gantt", "Creator": "tools/make_gantt.py"}) as pdf:
        fig = overview_figure(model, PAGE)
        fig.text(0.98, 0.015, f"Page 1 of {len(pages) + 1}.", ha="right", fontsize=6.5, color=MUTED)
        pdf.savefig(fig)
        plt.close(fig)
        for i, tracks in enumerate(pages, 2):
            fig = track_figure(model, tracks, i, len(pages) + 1)
            pdf.savefig(fig)
            plt.close(fig)
    return path


def runs_of(ds):
    """Consecutive days -> [(first, last)]."""
    out = []
    for d in ds:
        if out and (d - out[-1][1]).days == 1:
            out[-1] = (out[-1][0], d)
        else:
            out.append((d, d))
    return out


def md_day(d):
    return f"{d:%b} {d.day}" if d else "no date in the repo"


def due_md(t):
    """'due Nov 9*' (inferred), 'due Nov 8', 'no due date in the repo'."""
    return f"due {md_day(t['end'])}{'*' if t['end_inferred'] else ''}" if t["end"] else "no due date in the repo"


def who_md(owner_text):
    """'Arsha (from Nov 3)' -> 'Arsha, from Nov 3' (inside parentheses)."""
    return re.sub(r" \(from ([^)]*)\)$", r", from \1", owner_text)


def owner_note(t):
    """TODO's own owner text where the owner rule names someone else (the raters, a teammate)."""
    first = t["owner"].split()[0]
    return f" (TODO: {t['owner_todo']})" if t["owner_todo"] and first not in t["owner_todo"] else ""


def status_md(model):
    """Per track: done of total; done since the session logs began, the next steps, what is blocked; per owner; the
    milestones and what each needs; the next 7 days."""
    meta, data = model["meta"], model["data"]
    today = meta["today"]
    soon = today + timedelta(7)
    since = data["logs"][0]["date"] if data["logs"] else today
    tasks = [t for t in data["tasks"] if t["kind"] == "task" and t["note"] != "standing"]
    by_id = {t["id"]: t for t in tasks}
    open_ = sorted((t for t in tasks if t["status"] != "done"), key=lambda t: (t["end"] or date.max, id_key(t)))
    page = Path(data["root"]) / STATUS_DIR / "ONE_PAGE.md"         # Nov 4: Ritik's page in plain words, by hand
    lines = [f"# Project status, {today:%b} {today.day}, {today.year}", "",
             f"Generated by tools/make_gantt.py on {meta['generated']} from {meta['commit']}; do not edit by hand.", "",
             *([page.read_text().strip(), ""] if page.exists() else []),
             "Every task: `GANTT.xlsx` (Gantt, To do, Done, Progress, Daily, Changes); one page for slides: "
             "`gantt.png`; to print, the overview and a page per track: `gantt.pdf`. A date with * is inferred (the "
             "Gantt sheet's Date basis column says from what).", "", "## Done, per track", "",
             "| Track | Tasks done | Done % | Done % by time | Hours left (work / GPU / Voyager) |",
             "|---|---|---|---|---|"]
    for r in progress_rows(data):
        w = f"{r['percent_weighted']}%" if r["percent_weighted"] is not None else "no estimates"
        lines.append(f"| {r['track']} | {r['done']} of {r['tasks']} | {r['percent']}% | {w} | {r['remaining_hours']:g} "
                     f"({r['remaining_work']:g} / {r['remaining_gpu']:g} / {r['remaining_voyager']:g}) |")
    lines += ["", "By time: weighted by TODO's time column, over the tasks that have one. "
                  f"{meta['inferred']} task dates are inferred, and {meta['daily_inferred']} Daily rows from before "
                  "the session logs come from commits only.", ""]
    for tr in ("A", "B", "C", "Labels", "Repo"):
        ts = [t for t in tasks if t["track"] == tr]
        if not ts:
            continue
        who = f"{TAKEOVER[tr][0]} from {md_day(TAKEOVER[tr][1])}; the work before, Ritik" if tr in TAKEOVER else \
            OWNER[tr]
        done = sorted((t for t in ts if t["status"] == "done" and t["end"] and t["end"] >= since),
                      key=lambda t: (t["end"], id_key(t)))
        nxt = [t for t in open_ if t["track"] == tr]
        lines += [f"## {TRACK_NAME[tr]} ({who})", "", f"### Done since {md_day(since)} ({len(done)})", ""]
        lines += [f"- {md_day(t['end'])}{'*' if t['end_inferred'] else ''}: **{t['id']}** "
                  + (f"{label(t['name'])}: {t['delivered']}" if t.get("finding") else t["delivered"])
                  for t in done] or ["- none"]
        lines += ["", "### Next", ""] + ([f"{i}. **{t['id']}** ({who_md(t['owner'])}; {due_md(t)}): {t['next']}"
                                          for i, t in enumerate(nxt, 1)] or ["- nothing open"])
        blocked = [t for t in nxt if t["status"] == "blocked"]
        lines += ["", "### Blocked on", ""] + ([f"- **{t['id']}** {label(t['name'])}: {waiting_for(t)}"
                                                 for t in blocked] or ["- nothing"]) + [""]
    lines += ["## Per owner", ""]
    people = [("Ritik", "Track A, the labels, the repo and the report")] + [
        (who, f"Track {tr} from {md_day(when)}") for tr, (who, when) in TAKEOVER.items()]
    ms = [t for t in data["tasks"] if t["kind"] in ("milestone", "window")]
    for who, what in people:
        mine = [t for t in open_ if t["owner"].split()[0] == who]
        lines += [f"### {who} ({what})", ""]
        lines += [f"- **{t['id']}** {label(t['name'])} ({t['status']}; {due_md(t)}){owner_note(t)}" for t in mine]
        lines += [f"- {t['name'].split(' (')[0]}: {span_text(t['start'], t['end'])}" for t in ms
                  if t["owner"] == who and t["start"] and t["end"] >= today and t["status"] != "done"]
        lines += [""]
    lines += ["## Milestones and what each needs", ""]
    for t in sorted(ms, key=lambda t: t["start"] or date.max):
        name = re.sub(r"\s*\((?:exact day )?(?:v3 presented; )?(?:date )?not in the repo\)", "", t["name"])
        if t["kind"] == "milestone":
            when = md_day(t["start"])
        elif t["start"]:
            when = f"{span_text(t['start'], t['end'])} (a window; the exact day is not in the repo)"
        else:
            when = "date not in the repo"
        state = " (passed)" if t["end"] and t["end"] < today else (" (today)" if t["start"] == today else "")
        needs = data["needs"].get(t["id"], []) if not state else []
        lines.append(f"- **{when}: {name}**{state}" + (". Needs:" if needs else ""))
        for n in needs:
            x = by_id.get(n["id"])
            head = f"**{n['id']}** {n['text']}" if x else n["text"]
            st = f": {x['status']} ({who_md(x['owner'])}; " + (f"{due_md(x)})" if x["status"] != "done" else
                                                               f"done {md_day(x['end'])})") if x else ""
            lines.append(f"  - {head}{st} ({'inferred: ' if n['inferred'] else ''}{n['basis']})")
    lines += ["", f"## The next 7 days ({md_day(today)} to {md_day(soon)})", ""]
    due = [t for t in open_ if t["end"] and t["end"] <= soon]
    lines += [f"- **{t['id']}** {label(t['name'])} ({t['status']}; {who_md(t['owner'])}; {due_md(t)})"
              for t in due] or ["- nothing due"]
    lines += [f"- {md_day(t['start'])}: {t['name']}" for t in sorted(
        (t for t in ms if t["start"] and today < t["start"] <= soon), key=lambda t: t["start"])]
    nodue = [t["id"] for t in open_ if not t["end"]]
    lines += ["", f"Open tasks with no due date in the repo: {', '.join(nodue) or 'none'}."]
    lines += ["", "## Dropped (scope)", ""] + ([f"- **{t['id']}** {label(t['name'])} (Track {t['track']}): "
                                               f"{clauses(t['status_text'])[0]}" for t in data.get("dropped", [])]
                                             or ["- none"])
    return "\n".join(lines) + "\n"


def write_status(model, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(status_md(model))
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--today", type=date.fromisoformat, help="the run date (YYYY-MM-DD); default: the clock")
    ap.add_argument("--root", type=Path, default=ROOT, help="the repo (default: this one)")
    ap.add_argument("--out", type=Path, default=None, help="output folder (default: <root>/docs/status)")
    ap.add_argument("--dry-run", action="store_true", help="print the Progress sheet; write nothing")
    a = ap.parse_args(argv)
    model = build(a.root, a.today)
    prog = model["sheets"]["Progress"]
    for row in prog["rows"]:
        print(" | ".join(str(v) for v in row))
    print(f"{model['meta']['inferred']} inferred task dates; {model['meta']['daily_inferred']} Daily rows from commits "
          f"only; {len(model['data']['tasks'])} rows; {len(model['data']['commits'])} commits")
    if a.dry_run:
        return True
    out = a.out or a.root / STATUS_DIR
    for p in (write_xlsx(model, out / "GANTT.xlsx"), write_png(model, out / "gantt.png"),
              write_pdf(model, out / "gantt.pdf"), write_status(model, out / "STATUS.md")):
        print(f"wrote {p}")
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
