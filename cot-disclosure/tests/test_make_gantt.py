"""The project tracker (tools/make_gantt.py) on a small fake history: a temp git repo with commits on given dates,
and a TODO, PLAN, OVERVIEW, FINDINGS, session index, session logs and a daily of the real shapes. No network."""
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import date
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "tools"))

import make_gantt as mg  # noqa: E402

TODAY = date(2026, 10, 30)
TODO = """# Open work

## Track A

| # | Item | From | Status | Blocked by | Owner | Needs | Time |
|---|---|---|---|---|---|---|---|
| A1 | Step 11 `train.py`: LoRA only | Oct 21 | done (`{h2}`) | — | Ritik | no calls | 4–6 h |
| A2 | Evaluate the trained versions on Sol | Oct 26 | **Oct 30:** two parts submitted; base done | — | Ritik submits | Sol | ~7 GPU h per system |
| A3 | Step 13 analysis: 4 measures | Oct 25 | not started | A2 | Ritik | no calls | 1 day |
| A4 | Copy the follow-up file | Oct 27 | done Oct 28 (F2) | — | Ritik | Sol | 30 min |
| A5 | Look-inside rerun on the best version (L1) | Oct 27 | not started | A2 | Ritik submits | Sol | 4–10 GPU h |

## Track B (Ritik until Nov 3, then Arsha)

| # | Task | When decided | Status | Depends | Owner | Cost | Estimate |
|---|---|---|---|---|---|---|---|
| B1 | Closed-provider keys | Oct 5 | blocked | keys | Ritik; Arsha, from Nov 3 | — | — |
| B2 | Voyager runs, 3 per question | Oct 27 | done Oct 28 03:11 (810 runs) | — | Ritik; Arsha, from Nov 3 | Voyager | ~15 h (notes) |
| B3 | The Gate 2 question: is the gap clear? | PLAN | Qwen3 Thinking: clear (+35) | B2 | Ritik; Arsha, from Nov 3 | no calls | — |

## Track C (Ritik until Nov 3, then Shrey)

| # | Item | From | Status | Blocked by | Owner | Needs | Time |
|---|---|---|---|---|---|---|---|
| C1 | Live team on 5 items | Gate 1 | done (log 15:05) | — | Ritik | Voyager (35 calls) | 15 min |
| C2 | Fresh items for the reviewer | Oct 29 | planned (pre-register first); due Nov 5 | — | Ritik; Shrey, from Nov 3 | Voyager | ~400 reviews; 1 day |

## Labels

| # | Item | From | Status | Blocked by | Owner | Needs | Time |
|---|---|---|---|---|---|---|---|
| L1 | Label the queue, two raters | PLAN (Gate 2, Nov 8) | **Oct 30:** Ritik is asking Shrey and Arsha; ready to start | raters | two raters | none | 3–4 h per rater |

## Handoff, repo, docs, gates

| # | Item | From | Status | Blocked by | Owner | Needs | Time |
|---|---|---|---|---|---|---|---|
| H1 | `docs/handoff/TRACK_B.md`, for Arsha: what's done, final by Nov 3 | Oct 27 | draft, kept current | — | Ritik | no calls | 2 h |
| D1 | Session logs after every run | Oct 27 | standing | — | Ritik | no calls | 15 min each |
| G1 | Gate 1 (Oct 25): missed | PLAN | missed | — | everyone | — | — |
| G2 | Gate 2 (Nov 8): the gap (B3) and the labels (L1) | PLAN | not started | B3, L1 | everyone | — | — |
| R1 | GitHub main is behind | Oct 21 | open | A1, the push | Ritik | no calls | — |

## Notes

| # | Step | Calls | Time |
|---|---|---|---|
| 0 | Code | 0 | half a day |
"""
PLAN = """# Plan

## Timeline

| When | Track A | Track B | Track C | Labels, repo, handoff |
|---|---|---|---|---|
| Tue Oct 27 **(now)** | Steps 6–7 end | runs | — | rewrite |
| Mon Nov 2–Tue Nov 3 | E1–E5 continue | **Handoff to Arsha, Nov 3** | **Handoff to Shrey, Nov 3** | docs final |
| Nov 4–9 | E1–E5 done; look inside the best version (L1) | Arsha | Shrey | **Gate 2, Nov 8** |
| Nov 10–20 | Step 13 analysis; reruns; all evaluation done by Nov 20 at the latest | | | Phase 6 sample labeled |
| Nov 30–Dec 6 | | | | Final presentation (week 16) |
| Dec 7–12 | | | | Final report |

## Gates

- **Gate 1 (Oct 25): missed.**
- **Gate 2 (Nov 8).** The gap.
- **Gate 3 (Nov 22).** Training.
"""
OVERVIEW = """# Overview

## 2. Status at a glance

| Area | Done | Not done yet |
|---|---|---|
| Track A (Ritik) | Steps 1–10, the window analysis | Steps 11–13 on Sol |

## 3. What was done, in order

| Date | Work | Calls |
|---|---|---|
| Oct 1–2 | Harness; **Test 1** (24 puzzles) | 312 |
| Oct 22–24 | **Step 3:** takeover curves, 219 runs | 137,143 probes |
| Oct 26 | Sol kit; **Steps 8, 9, 10** on Sol | Sol |

## 6. The progress round (Oct 1–6)

Test 1.

## 7. Track A: explain and fix (Oct 21–27)

- **Step 3, takeover curves** (219 runs): the hint letter leads.
- **Step 9, attention to the hint** (Sol): tool hints get less attention.
"""
INDEX = """# Session logs

| When (MST) | Log | What |
|---|---|---|
| 2026-10-27 15:05 | [2026-10-27_1505_C_c1-five-items.md](2026-10-27_1505_C_c1-five-items.md) | Track C live on 5 items (35 calls): the checker caught 3 of 3 |
| 2026-10-28 (day) | [DAILY_2026-10-28.md](DAILY_2026-10-28.md) | The day: B2 done (810 runs), Sol 66759753 |
"""
DAILY = """# Daily log: 2026-10-28

## The day in brief

Runs.

## Compute used

- **Voyager:** 810 runs, 0 errors.
- **Sol:** lora 3.41 GPU h.

## Tomorrow

- more
"""


def git(repo, *args, when=None):
    env = dict(os.environ)
    if when:
        env.update(GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    out = subprocess.run(["git", "-C", str(repo), "-c", "user.name=Ritik", "-c", "user.email=r@example.com",
                          "-c", "commit.gpgsign=false", *args], capture_output=True, text=True, env=env, check=True)
    return out.stdout.strip()


def commit(repo, files, subject, when):
    for name, text in files.items():
        p = repo / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        git(repo, "add", name)
    git(repo, "commit", "-q", "-m", subject, when=when)
    return git(repo, "rev-parse", "--short=7", "HEAD")


@pytest.fixture
def repo(tmp_path):
    if not shutil.which("git"):
        pytest.skip("no git")
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-q")
    commit(r, {"cot-disclosure/results/progress/test2.json": "{}", "docs/FINDINGS.md": "# Findings\n\n## F1. A tool "
               "hint moves thinking models more\n\nbody\n"}, "Progress run: Test 2", "2026-10-04T12:00:00-07:00")
    h2 = commit(r, {"cot-disclosure/finetune/train.py": "x = 1\n"}, "Track A step 11: train.py",
                "2026-10-24T10:00:00-07:00")
    commit(r, {"cot-disclosure/agents/team.py": "y = 2\n", "docs/FINDINGS.md": "# Findings\n\n## F1. A tool hint "
               "moves thinking models more\n\nbody\n\n## F2. Track A: the readout replicates\n\nbody\n"},
           "C1 on 5 items; F2 added", "2026-10-28T09:00:00-07:00")
    sess = "docs/sessions/"
    commit(r, {"docs/TODO.md": TODO.format(h2=h2), "docs/PLAN.md": PLAN, "docs/OVERVIEW.md": OVERVIEW,
               sess + "INDEX.md": INDEX, sess + "DAILY_2026-10-28.md": DAILY,
               sess + "2026-10-27_1505_C_c1-five-items.md": "# Session log: C1\n",
               sess + "2026-10-30_1700_C_c3-prereg.md": "# Session log: C3 pre-registered: is the cue the argument? "
                                                        "(2026-10-30 17:00 MST)\n"},
           "Docs name people, not tools: every doer credited to Acme Writer Pro is now the track's owner",
           "2026-10-30T08:00:00-07:00")
    (r / "docs" / "FINDINGS.md").write_text((r / "docs" / "FINDINGS.md").read_text()
                                            + "\n## F3. Track C (C1): a new one, not committed\n\nbody\n")
    return r, h2


@pytest.fixture
def model(repo):
    return mg.build(repo[0], TODAY)


def by_id(model):
    return {t["id"]: t for t in model["data"]["tasks"]}


def test_tasks_are_parsed_from_every_todo_table_with_its_own_header(model):
    t = by_id(model)
    assert {"A1", "A2", "A3", "A4", "A5", "B1", "B2", "B3", "C1", "C2", "L1", "H1", "D1", "R1"} <= set(t)
    assert "0" not in t                                         # the Notes table has no Status column
    assert t["B2"]["track"] == "B" and t["B2"]["time"] == "~15 h (notes)" and t["B3"]["depends"] == "B2"
    assert t["A1"]["phase"] == "Steps 11–13: code and Sol kit" and t["A3"]["phase"] == "Evaluation and Gate 3"
    assert t["Step 3"]["status"] == "done" and (t["Step 3"]["start"], t["Step 3"]["end"]) == (date(2026, 10, 22),
                                                                                            date(2026, 10, 24))
    assert t["Step 9"]["name"] == "Step 9: attention to the hint" and t["P1"]["track"] == "Setup"
    gates = [x for x in model["data"]["tasks"] if x["phase"] == "Gates"]
    assert [(g["id"], g["start"]) for g in gates] == [("Gate 1", date(2026, 10, 25)), ("Gate 2", date(2026, 11, 8)),
                                                      ("Gate 3", date(2026, 11, 22))]
    assert not any(x["kind"] == "gate" for x in model["data"]["tasks"])      # TODO's G rows became the milestones


def test_statuses(model):
    t = by_id(model)
    assert [t[i]["status"] for i in ("A1", "A2", "A3", "A4", "B1", "B2", "C1", "C2", "H1")] == [
        "done", "in progress", "planned", "done", "blocked", "done", "done", "planned", "in progress"]
    assert (t["B3"]["status"], t["B3"]["note"]) == ("in progress", "no status word")
    assert t["L1"]["status"] == "blocked"                                      # "asking" a rater
    assert (t["R1"]["status"], t["R1"]["note"]) == ("blocked", "waits on an outside step")   # open, blocked by the push
    assert (t["D1"]["note"], t["D1"]["counted"]) == ("standing", False)
    assert by_id(model)["Gate 1"]["status"] == "done" and by_id(model)["Gate 2"]["status"] == "planned"


@pytest.mark.parametrize("text, blocked, want", [
    ("done (`56e2894`)", "—", "done"), ("**done** Oct 29: FlashInfer", "—", "done"),
    ("format and export done (`--steered`); export after each model's runs", "B7", "done"),
    ("code and CPU tests done; not trained. Every bias logged", "batch 3's order", "planned"),
    ("prepared, not run (`af2f2fb`); waiting for Ritik's choices", "the push; the 10 jobs", "blocked"),
    ("**Oct 30 ~09:50:** tags submitted (2 at a time); wait for free submission slots", "—", "in progress"),
    ("decided; not started", "A16", "planned"), ("**final Oct 30** (handed over early)", "—", "done"),
    ("missed", "—", "done"), ("standing", "—", "in progress"), ("blocked", "keys", "blocked"),
])
def test_classify(text, blocked, want):
    assert mg.classify(text, blocked)[0] == want


def test_dates_and_inferred_marking(model, repo):
    t = by_id(model)
    a1 = t["A1"]                                                    # done by a commit: its date, inferred
    assert (a1["start"], a1["end"], a1["end_basis"], a1["end_inferred"]) == (
        date(2026, 10, 21), date(2026, 10, 24), f"commit {repo[1]}", True)
    a4 = t["A4"]                                                    # "done Oct 28": stated
    assert (a4["end"], a4["end_inferred"]) == (date(2026, 10, 28), False)
    c1 = t["C1"]                                                    # "log 15:05" -> the INDEX row; From "Gate 1"
    assert (c1["end"], c1["end_inferred"], c1["start"], c1["start_inferred"]) == (
        date(2026, 10, 27), False, date(2026, 10, 25), True)
    a3 = t["A3"]                                                    # PLAN's window by its clause, start and end
    assert (a3["start"], a3["end"], a3["end_inferred"]) == (date(2026, 11, 10), date(2026, 11, 20), False)
    a5 = t["A5"]
    assert (a5["start"], a5["end"]) == (date(2026, 11, 4), date(2026, 11, 9))
    a2 = t["A2"]                                                    # due before A5, which waits on it
    assert (a2["end"], a2["end_basis"], a2["end_inferred"]) == (date(2026, 11, 9), "before A5 (it waits on it)", True)
    assert (t["C2"]["end"], t["C2"]["end_basis"]) == (date(2026, 11, 5), "TODO row")
    assert (t["H1"]["end"], t["L1"]["end"], t["B3"]["end"]) == (date(2026, 11, 3), date(2026, 11, 8),
                                                                  date(2026, 11, 8))
    assert t["L1"]["start"] is None                     # its only From date (Nov 8) is a deadline, not a start
    assert t["B1"]["end"] is None and t["B1"]["end_basis"] == "not in the repo"
    assert "inferred" in mg.basis(a1) and "inferred" not in mg.basis(a4)
    assert model["meta"]["inferred"] == mg.inferred_count(model["data"]["tasks"]) >= 4
    windows = {x["id"]: x for x in model["data"]["tasks"] if x["kind"] == "window"}
    assert (windows["Final report"]["end"], windows["Final report"]["end_inferred"]) == (date(2026, 12, 12), True)
    assert windows["Progress talk"]["start"] is None                     # no kit in this repo: no date, no marker
    f = model["data"]["findings"]
    assert (f[1][0], f[2][0], f[2][3], f[3][0], f[3][2]) == (date(2026, 10, 4), date(2026, 10, 28), "A", TODAY, None)


def test_owner_normalization(model):
    t = by_id(model)
    assert t["B1"]["owner"] == "Arsha (from Nov 3)" and t["B3"]["owner"] == "Arsha (from Nov 3)"
    assert t["B2"]["owner"] == "Ritik"                                  # past work stays Ritik's
    assert t["C2"]["owner"] == "Shrey (from Oct 30)" and t["C2"]["owner_todo"] == "Ritik; Shrey, from Nov 3"
    assert t["C1"]["owner"] == "Ritik" and t["L1"]["owner"] == "Ritik" and t["A2"]["owner"] == "Ritik"
    hand = {x["id"]: x for x in model["data"]["tasks"] if x["phase"] == "Handoffs"}
    assert hand["Handoff C"]["start"] == date(2026, 10, 30) and "PLAN says Nov 3" in hand["Handoff C"]["end_basis"]
    assert hand["Handoff B"]["start"] == date(2026, 11, 3) and "PLAN says" not in hand["Handoff B"]["end_basis"]


def test_a_task_named_only_in_a_session_log_is_picked_up(model):
    c3 = by_id(model)["C3"]
    assert (c3["status"], c3["start"], c3["track"], c3["counted"]) == ("planned", TODAY, "C", True)
    assert c3["name"].startswith("is the cue the argument") and c3["owner"] == "Shrey (from Oct 30)"


def test_progress_numbers(model):
    rows = {r["track"]: r for r in mg.progress_rows(model["data"])}
    a = rows[mg.TRACK_NAME["A"]]
    # A1 5 h work (done), A2 7 GPU h, A3 8 h (1 day), A4 0.5 GPU h (done), A5 7 GPU h
    assert (a["tasks"], a["done"], a["percent"], a["with_estimate"], a["without_estimate"]) == (5, 2, 40.0, 5, 0)
    assert (a["hours_done"], a["hours_total"], a["percent_weighted"]) == (5.5, 27.5, 20.0)
    assert (a["remaining_hours"], a["remaining_work"], a["remaining_gpu"]) == (22.0, 8.0, 14.0)
    b = rows[mg.TRACK_NAME["B"]]
    assert (b["tasks"], b["done"], b["with_estimate"], b["without_estimate"], b["percent_weighted"]) == (3, 1, 1, 2,
                                                                                                         100.0)
    assert rows[mg.TRACK_NAME["Repo"]]["tasks"] == 2                    # H1, R1; D1 is a standing duty
    assert rows["All"]["tasks"] == sum(r["tasks"] for k, r in rows.items() if k != "All")
    prog = model["sheets"]["Progress"]
    assert prog["columns"][0] == "Track" and len(prog["rows"]) == len(rows)
    assert any("B3" in n for n in prog["notes"]) and any("R1" in n for n in prog["notes"])


@pytest.mark.parametrize("time, needs, want", [
    ("4–6 h", "no calls", {"work": 5.0}), ("150 GPU-min", "Sol", {"gpu": 2.5}), ("1 day", "Voyager", {"work": 8.0}),
    ("P1 0.25–0.5, P2 11–23 GPU h", "Sol", {"gpu": 17.375}), ("half a day", "", {"work": 4.0}),
    ("~6 h per part per rater (294 and 292 rows, ~1¼ min a row)", "none", {"work": 6.0}),
    ("~1.5–3 h Voyager; ≤2 GPU h", "Voyager, then Sol", {"voyager": 2.25, "gpu": 2.0}),
    ("—", "Sol (~1.1 + 2.6–4.3 GPU h)", {"gpu": 4.55}), ("group 1: ~2 h per rater", "none", {"work": 2.0}),
])
def test_hours(time, needs, want):
    got = mg.hours(time, needs)
    assert {k: v for k, v in got.items() if v} == pytest.approx(want)


@pytest.mark.parametrize("time", ["—", "done", "done about 2–4 PM MST Oct 27", "from the refit", ""])
def test_no_estimate(time):
    assert mg.hours(time, "no calls") is None


def test_remaining_is_every_open_task_sorted_by_due(model):
    rem = model["sheets"]["Remaining"]
    due = [r[0] for r in rem["rows"]]
    dated = [d for d in due if d != "not in the repo"]
    assert dated == sorted(dated) and due[len(dated):] == ["not in the repo"] * (len(due) - len(dated))
    ids = [r[1] for r in rem["rows"]]
    assert ids[0] == "H1" and set(ids) >= {"A2", "A3", "A5", "B1", "B3", "C2", "C3", "L1", "R1", "Gate 2", "Gate 3"}
    assert not {"A1", "A4", "B2", "C1", "D1", "Gate 1"} & set(ids)        # done, standing or passed
    row = dict(zip(rem["columns"], rem["rows"][ids.index("A2")]))
    assert (row["Owner"], row["Hours"], row["Status"], row["Due"]) == ("Ritik", 7.0, "in progress", "2026-11-09")
    assert row["Due date from"] == "before A5 (it waits on it) (inferred)"


def test_daily_and_changes(model, repo):
    daily = [dict(zip(model["sheets"]["Daily"]["columns"], r)) for r in model["sheets"]["Daily"]["rows"]]
    c27 = next(r for r in daily if r["Date"] == "2026-10-27" and r["Track"] == mg.TRACK_NAME["C"])
    assert "15:05 Track C live on 5 items" in c27["What was done"] and "35 calls" in c27["Runs and compute (as logged)"]
    all28 = next(r for r in daily if r["Date"] == "2026-10-28" and r["Track"] == mg.TRACK_NAME["ALL"])
    assert "Sol: lora 3.41 GPU h" in all28["Runs and compute (as logged)"] and "Sol jobs 66759753" in \
        all28["Runs and compute (as logged)"]
    a24 = next(r for r in daily if r["Date"] == "2026-10-24")
    assert a24["Track"] == mg.TRACK_NAME["A"] and a24["What was done"].startswith("From commits (no session log")
    assert a24["Sources"] == "git log (inferred)" and a24["Commits"] == 1 and a24["Hashes"] == repo[1]
    assert next(r for r in daily if r["Date"] == "2026-10-28" and r["Track"] == mg.TRACK_NAME["A"])[
        "Findings added"] == "F2"
    ch = model["sheets"]["Changes"]["rows"]
    assert [r[3] for r in ch] == ["C", "C", "A", "Setup"]      # newest first; from the files (the docs commit adds C logs)
    assert ch[2][2] == repo[1] and all(len(r[4]) <= 120 for r in ch)
    assert "Acme" not in ch[0][4] and "credited to a tool is now" in ch[0][4]
    assert mg.clean("work credited to Ritik") == "work credited to Ritik"


def test_gantt_rows_days_today_and_milestones(model):
    g = model["sheets"]["Gantt"]
    days = g["columns"][g["left"]:]
    assert (days[0], days[-1], len(days)) == ("2026-10-01", "2026-12-12", 73)
    assert g["milestones"]["2026-11-08"] == "Gate 2" and g["milestones"]["2026-10-30"] == "Handoff C"
    kinds = [r["kind"] for r in g["rows"]]
    assert kinds[0] == "track" and kinds.count("track") == 7
    row = {r["values"][0]: r for r in g["rows"] if r["kind"] not in ("track", "phase")}
    assert row["A1"]["days"]["2026-10-21"] == "done" and row["A1"]["days"]["2026-10-24"] == "done"
    assert "2026-10-25" not in row["A1"]["days"]
    assert row["A2"]["days"]["2026-10-30"] == "in progress" and row["A2"]["days"]["2026-11-09"] == "planned"
    assert row["B1"]["days"]["2026-10-05"] == "blocked" and "2026-10-31" not in row["B1"]["days"]
    assert row["Gate 2"]["days"] == {"2026-11-08": "milestone"}
    assert set(row["A3"]["days"]) == {f"2026-11-{d:02d}" for d in range(10, 21)}


def test_the_files_are_written(model, repo, tmp_path):
    path = mg.write_xlsx(model, tmp_path / "out" / "GANTT.xlsx")
    assert list(model["sheets"]) == ["Gantt", "Daily", "Changes", "Progress", "Remaining"]
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        sheets = sorted(n for n in z.namelist() if n.startswith("xl/worksheets/sheet"))
        assert len(sheets) == 5
        wb = z.read("xl/workbook.xml").decode()
        assert all(f'name="{n}"' in wb for n in model["sheets"])
        text = " ".join(z.read(n).decode() for n in z.namelist() if n.endswith(".xml"))
        assert "Acme" not in text
    png = mg.write_png(model, tmp_path / "out" / "gantt.png")
    assert png.read_bytes()[:4] == b"\x89PNG"
    md = mg.write_status(model, tmp_path / "out" / "STATUS.md").read_text()
    head = mg.head_commit(repo[0])
    assert f"Generated by tools/make_gantt.py on 2026-10-30 from {head}; do not edit by hand" in md
    assert "| Track A: explain and fix | 2 of 5 | 40.0% | 20.0% |" in md
    assert "**H1**" in md and "**C2**" in md and "Nov 8: Gate 2" in md


def test_main_writes_three_files(repo, tmp_path):
    out = tmp_path / "progress"
    assert mg.main(["--root", str(repo[0]), "--today", "2026-10-30", "--out", str(out)])
    assert sorted(p.name for p in out.iterdir()) == ["GANTT.xlsx", "STATUS.md", "gantt.png"]
    assert mg.main(["--root", str(repo[0]), "--today", "2026-11-02", "--dry-run"])
