"""The supplement generator (tools/make_supplement.py): FINDINGS parsing, the CLAIMS number check, the pre-registration
ledger, tables from summaries, the numbers-only guard, and a full run on the real repo. CPU, no network; the git lookups
run on a small repo made in a temp folder."""
import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "tools"))

import make_supplement as ms  # noqa: E402

FINDINGS = """# Findings

Preamble with a date, Oct 30 11:00.

## F1. A tool hint moves the model (C4)

- tool − user **+48 points [+31, +65]**; the reviewer corrects 39 of 53.
- **Source.** `cot-disclosure/results/summaries/trackB/rep.json` and `rep_by_set.json`
  (`budget`); per-run flags in `detect.py`; `python progress/report.py
  --by-set`
- **Status.** *confirmed*.

## F2. The reviewer defers to a named tool (C16)

- Olmo **−21 [−34, −8]**; the share is 0.90 [0.76, 1.06].
- **Source.** `cot-disclosure/results/summaries/trackC/missing.json`.
- **Status.** *confirmed*. **Result: replicates.**

## Measurement traps we hit and fixed

**T1. Template mismatch.**
- *What.* The server rendered the wrong template.
- *Found* Oct 21 from token counts.
- *Fix.* Render it ourselves and send it
  to the completions endpoint.
- *Source.* `template.json`.

**Also:**
- Streams that closed early were taken as complete.
"""
FINDINGS_V1 = FINDINGS.split("## F2.")[0] + "## Measurement traps we hit and fixed\n"
CLAIMS = """# Claims

Oct 29; updated 23:15 (dates are not numbers to check).

## Thread 1

**1.1 Tools sway models.**
- **Evidence:** F1: +48 [+31, +65]; 39 of 53.
  - hyphen for minus: -21 [-34, -8] (F2)
- **Status:** C16 gives 0.90 [0.76, 1.06] and the planted −99 [−98, −97].
- **Planted, cited wrong:** F2 says 39 of 53.
- `[SOL: following = ___ ]` is a placeholder.
"""
PREREG_LOG = """# Session log: X pre-registered (2026-10-29 00:20 MST)

## 2. The rule (pre-registered)

- **Replicates:** the lower bound is above 0.375. F1 is the reference.
"""
RESULTS_LOG = "# Session log: X done (2026-10-30 09:00 MST)\n\nResult: replicates. FINDINGS F2.\n"
OTHER_PREREG = "# Session log: Y pre-registered (2026-10-30 10:00 MST)\n\n## 3. Pre-registered reading\n\nSomething.\n"
ROWS = [{"id": "x", "track": "A", "experiment": "X: does it replicate?", "kind": "pre", "rule": "lower bound above 0.375",
         "rule_log": "2026-10-29_0020_A_x-prereg.md", "rule_check": ["0.375"], "f_title": r"\(C16\)",
         "result_glob": ["*x-results*"], "verdict": "replicates", "verdict_check": ["Result: replicates"],
         "after": ["a split read afterwards"]},
        {"id": "z", "track": "C", "experiment": "Z", "kind": "pre", "rule": "r",
         "rule_log": "2026-10-29_0020_A_x-prereg.md", "rule_check": ["a phrase the log lacks"], "f": [1],
         "verdict": "v", "verdict_check": ["no such verdict"]},
        {"id": "w", "track": "B", "experiment": "W", "kind": "pre", "rule": "r",
         "rule_log": "2026-10-30_1700_B_w-prereg.md", "rule_check": [], "verdict": "waiting", "verdict_check": []}]


def git_repo(root):
    def run(*args, when="2026-10-26T13:31:00-07:00"):
        env = {**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when, "GIT_AUTHOR_NAME": "Ritik",
               "GIT_AUTHOR_EMAIL": "ritik@example.com", "GIT_COMMITTER_NAME": "Ritik",
               "GIT_COMMITTER_EMAIL": "ritik@example.com"}
        return subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", *args], cwd=root,
                              env=env, check=True, capture_output=True, text=True).stdout

    def write(rel, text):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def commit(msg, when):
        run("add", "-A")
        run("commit", "-q", "-m", msg, when=when)
        return run("rev-parse", "--short", "HEAD").strip()
    run("init", "-q")
    return write, commit


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    write, commit = git_repo(root)
    write(ms.FINDINGS_REL, FINDINGS_V1)
    write(ms.CLAIMS_REL, CLAIMS)
    write(f"{ms.SUM_REL}/trackB/rep.json", "{}")
    write(f"{ms.SUM_REL}/trackB/rep_by_set.json", "{}")
    write("cot-disclosure/progress/report.py", "")
    write("cot-disclosure/detect.py", "")
    c1 = commit("F1", "2026-10-26T13:31:00-07:00")
    write(f"{ms.SESSIONS_REL}/2026-10-29_0020_A_x-prereg.md", PREREG_LOG)
    c2 = commit("X's rule", "2026-10-29T00:25:00-07:00")
    write(ms.FINDINGS_REL, FINDINGS)
    write(f"{ms.SESSIONS_REL}/2026-10-30_0900_A_x-results.md", RESULTS_LOG)
    c3 = commit("F2 and X's results", "2026-10-30T09:03:00-07:00")
    write(f"{ms.SESSIONS_REL}/2026-10-30_1000_C_y-prereg.md", OTHER_PREREG)
    commit("Y's rule", "2026-10-30T10:00:00-07:00")
    return {"root": root, "c1": c1, "c2": c2, "c3": c3}


# ---------------------------------------------------------------- FINDINGS
def test_findings_entries_sources_logs_and_commits(repo):
    root = repo["root"]
    entries = ms.findings((root / ms.FINDINGS_REL).read_text())
    assert [(f["n"], f["title"]) for f in entries] == [(1, "A tool hint moves the model (C4)"),
                                                       (2, "The reviewer defers to a named tool (C16)")]
    files = ms.tracked_files(root)
    s1 = ms.sources(entries[0], files, root)
    assert [(r["path"], r["status"]) for r in s1["summaries"]] == [
        (f"{ms.SUM_REL}/trackB/rep.json", "tracked"), (f"{ms.SUM_REL}/trackB/rep_by_set.json", "tracked")]
    assert [r["path"] for r in s1["others"]] == ["cot-disclosure/detect.py"]           # a bare module: in cot-disclosure/
    assert s1["commands"] == [{"command": "python progress/report.py --by-set", "script": "progress/report.py",
                               "script_tracked": True}]                                # wrapped over two lines
    s2 = ms.sources(entries[1], files, root)
    assert s2["summaries"][0]["status"] == "missing" and not s2["commands"]
    texts = ms.session_texts(root)
    assert ms.mentions(1, texts) == ["2026-10-29_0020_A_x-prereg.md"]
    assert ms.mentions(2, texts) == ["2026-10-30_0900_A_x-results.md"]
    commits = ms.heading_commits(root)
    assert commits[1][0] == repo["c1"] and commits[2][0] == repo["c3"] and commits[1][1].startswith("2026-10-26 13:31")
    md, rep = ms.evidence(root, files, "HEAD LINE")
    assert "HEAD LINE" in md and f"`{repo['c1']}` 2026-10-26 13:31" in md
    assert any("F2" in p and "missing" in p for p in rep["problems"])
    assert any(p.startswith("F2: no command") for p in rep["problems"])


def test_traps_parse_fields_and_the_also_list():
    ts, extra = ms.traps(FINDINGS)
    t = ts[0]
    assert (t["n"], t["title"]) == (1, "Template mismatch")
    assert t["what"] == "The server rendered the wrong template." and t["found"] == "Oct 21 from token counts."
    assert t["fix"] == "Render it ourselves and send it to the completions endpoint." and t["source"] == "`template.json`."
    assert extra == ["Streams that closed early were taken as complete."]


# ---------------------------------------------------------------- CLAIMS
def test_numbers_are_read_and_identifiers_are_not():
    text = ms.norm("Olmo 3.1 32B: −21 [−34, −8]; 39 of 53; 0.90 [0.76, 1.06]; 6 → 8 of 73; Qwen3-8B at L19H31; "
                   "+0.068 [+0.044, +0.088]; −58%; 85–90%; 26 of 43 [46, 74%]; 60 → 19; the −20 line; on Oct 29, 23:15")
    assert ms.numbers(text) == [("interval", "-21 [-34, -8]"), ("count", "39 of 53"), ("interval", "0.90 [0.76, 1.06]"),
                                ("chain of", "6 → 8 of 73"), ("interval", "+0.068 [+0.044, +0.088]"),
                                ("signed", "-58%"), ("percent range", "85-90%"),
                                ("count with interval", "26 of 43 [46, 74%]"), ("chain", "60 → 19"), ("signed", "-20")]


def test_claims_check_finds_the_planted_mismatches(repo):
    root = repo["root"]
    text = (root / ms.FINDINGS_REL).read_text()
    rows = ms.check_claims((root / ms.CLAIMS_REL).read_text(), ms.findings(text), text, ms.session_texts(root))
    got = {(r["line"], r["number"]): (r["result"], r["cites"], r["where"]) for r in rows}
    assert got[(8, "+48 [+31, +65]")] == ("format differs", ["F1"], [])               # "+48 points [+31, +65]"
    assert got[(8, "39 of 53")] == ("exact", ["F1"], [])
    assert got[(9, "−21 [−34, −8]")] == ("exact", ["F2"], [])          # '-' in CLAIMS, '−' in FINDINGS
    assert got[(10, "0.90 [0.76, 1.06]")] == ("exact", ["F2"], [])                    # C16 -> F2 by its heading
    assert got[(10, "−99 [−98, −97]")] == ("not found", ["F2"], [])
    assert got[(11, "39 of 53")] == ("other entry", ["F2"], ["F1"])                   # cites F2, lives in F1
    assert not any(r["line"] in (3, 12) for r in rows)                                 # preamble and placeholder
    _, rep = ms.evidence(root, ms.tracked_files(root), "h")
    assert {(c["line"], c["result"]) for c in rep["mismatches"]} == {(10, "not found"), (11, "other entry")}


# ---------------------------------------------------------------- PREREGISTRATIONS
def test_prereg_ledger_rows_commits_checks_and_scan(repo, monkeypatch):
    root = repo["root"]
    monkeypatch.setattr(ms, "PREREG", ROWS)
    entries = ms.findings((root / ms.FINDINGS_REL).read_text())
    texts = ms.session_texts(root)
    rows, extra = ms.prereg_rows(root, entries, texts, ms.tracked_files(root))
    x, z, w = rows
    assert x["fixed"][0][1][0] == repo["c2"] and x["fixed"][0][1][1].startswith("2026-10-29 00:25")
    assert [label for label, _ in x["results"]] == ["F2", "log 2026-10-30_0900"]
    assert all(c[0] == repo["c3"] for _, c in x["results"])
    assert (x["before"], x["checked"], x["waiting"]) == ("yes", "yes", False)
    assert z["checked"].startswith("unverified") and "a phrase the log lacks" in z["checked"] \
        and "no such verdict" in z["checked"]
    assert w["waiting"] and w["fixed"][0][1] == ("not found",)                         # a rule log not written yet
    assert extra == ["2026-10-30_1000_C_y-prereg.md"]                                   # found by the scan, not curated
    md, _ = ms.preregistrations(root, entries, texts, ms.tracked_files(root), "h")
    assert "a split read afterwards" in md and "not in PREREG" in md


def test_the_real_ledger_resolves_every_rule_and_flags_the_after_the_fact_readings():
    rows, _ = ms.prereg_rows(ms.REPO, ms.findings((ms.REPO / ms.FINDINGS_REL).read_text()), ms.session_texts(ms.REPO),
                             ms.tracked_files(ms.REPO))
    by = {r["id"]: r for r in rows}
    for r in rows:
        if r["kind"] != "none" and not (r.get("rule_log") and not (ms.REPO / ms.SESSIONS_REL / r["rule_log"]).exists()):
            assert all(len(c) > 1 for _, c in r["fixed"]), r["id"]                       # a commit and a date each
        if not r["waiting"]:
            assert r["checked"] == "yes", (r["id"], r["checked"])
            assert r["before"] in ("yes", "n/a"), (r["id"], r["before"])
    assert by["c14"]["kind"] == "exploratory" and by["b4_on_off"]["kind"] == "none"
    assert by["b1_alpha"]["fixed"][0][1][0].startswith("0bd2241")
    assert any("after the fact" in a for a in by["b4_on_off"]["after"])
    assert any("not pre-registered" in a for a in by["gate3"]["after"])
    assert any("descriptive" in a for a in by["c16"]["after"])


# ---------------------------------------------------------------- tables
def rate(k, n, q=54):
    return {"k": k, "n": n, "rate": k / n, "wilson": [0.1, 0.2], "questions": q, "clustered": [0.1, 0.2]}


def test_tables_from_a_fixture_summary(tmp_path):
    ch = {"runs": 162, "answered": 162, "following": rate(59, 162),
          "above_baseline": {"excess": 0.35, "interval": [0.25, 0.46], "questions": 54},
          "mention_final_when_followed": rate(54, 59), "bare_final": rate(0, 162)}
    model = {"runs": 810, "no_answer": 0, "questions": 54, "sure_questions": 47, "nohint_accuracy": rate(151, 162),
             "nohint_bare_final": rate(0, 162), "channels": {"tool_pasted": ch},
             "gate2_tool_minus_user": {"tool_pasted": {"diff": 0.35, "interval": [0.24, 0.46], "questions": 54,
                                                       "clear": True}}}
    pilot = {**model, "runs": 2}
    rep = {b: {"voyager | qwen3-30b-a3b-thinking-2507 | thinking=None": model, "ollama | qwen3:8b | thinking=True": pilot}
           for b in ("budget_32768", "cut_16000")}
    rep["thinking_minus_not"] = {"budget_32768": {"a | m | thinking=True minus a | m | thinking=False": {
        "tool_real": {"diff": 0.64, "interval": [0.51, 0.75], "questions": 54, "clear": True}}}}
    (tmp_path / "trackB").mkdir()
    (tmp_path / "trackB" / "trackB_report.json").write_text(json.dumps(rep))
    t = ms.Tables(tmp_path / "out", "HEAD LINE")
    rows = ms.table_trackB(t, tmp_path)
    assert {r["model"] for r in rows} == {"Qwen3 30B Thinking"}                         # the 2-run pilot left out
    md = (tmp_path / "out" / "tables" / "trackB_by_model_channel.md").read_text()
    assert md.splitlines()[2] == "HEAD LINE" and "59 of 162" in md and "+35 [+24, +46] clear" in md
    assert "ollama | qwen3:8b" in md and "Left out" in md
    lines = (tmp_path / "out" / "tables" / "trackB_by_model_channel.csv").read_text().splitlines()
    assert lines[0] == "# HEAD LINE"
    table = list(csv.DictReader(lines[1:]))
    pasted = [r for r in table if r["channel"] == "tool_pasted" and r["budget"] == "budget_32768"]
    assert len(table) == 4 and pasted[0]["following_k"] == "59" and pasted[0]["gate2_tool_minus_user"] == "0.35"
    assert t.counts["tables/trackB_by_model_channel.md"] == 2 and t.counts["tables/trackB_thinking_minus_not.csv"] == 1


def test_c11_rule_and_formats():
    assert ms.c11_rule({"diff": -0.42, "interval": [-0.58, -0.28]}) == "defers"
    assert ms.c11_rule({"diff": -0.05, "interval": [-0.26, 0.15]}) == "doesn't defer"
    assert ms.c11_rule({"diff": -0.21, "interval": [-0.34, -0.08]}) == "unclear"
    assert ms.pts(-0.2075, [-0.3396, -0.0755]) == "−21 [−34, −8]"
    assert ms.pts(0.0, [-0.11, 0.11]) == "+0 [−11, +11]" and ms.pts(0.1, [None, None]).endswith("too few questions)")


def test_the_real_summaries_give_the_findings_numbers():
    rows = ms.reviewer_rows(ms.REPO / ms.SUM_REL)
    olmo = {(r["run"], r["variant"]): r for r in rows if r["reviewer"] == "Olmo 3.1 32B Instruct"}
    assert (olmo[("C4", "answer only")]["corrects_k"], olmo[("C4", "+ private reasoning")]["corrects_k"]) == (59, 6)  # F18
    assert round(olmo[("C4", "+ private reasoning")]["corrects_minus_answer_only"] * 100) == -73
    assert olmo[("C15", "+ tool log")]["c11_rule"] == "defers" and olmo[("C4", "+ tool log")]["rule_pre_registered"] == "no"
    cue, _ = ms.cue_rows(ms.REPO / ms.SUM_REL)
    c16 = [r for r in cue if r["experiment"] == "C16" and r["decision"] == "pre-registered, main"
           and r["reviewer"] == "Olmo 3.1 32B Instruct"][0]
    assert (c16["a_k"], c16["b_k"], round(c16["diff"] * 100), c16["reading"]) == (25, 36, -21, "unclear")       # F31


# ---------------------------------------------------------------- the numbers-only guard
def test_guard_catches_a_planted_question_start(tmp_path):
    import experiments as ex
    starts = ms.question_starts()
    planted = ex.ITEMS[0]["question"].strip()[:60]
    assert planted[:40] in starts                                                     # the pilot puzzles, always
    (tmp_path / "clean.md").write_text("Generated by tools/make_supplement.py; 39 of 53 [60, 84%]\n")
    (tmp_path / "bad.md").write_text(f"a table cell: {planted}\n")
    (tmp_path / "long.csv").write_text("# head\nnote\n" + "x" * 201 + "\n")
    bad = ms.check_outputs(tmp_path, starts)
    assert set(p.name for p in bad) == {"bad.md", "long.csv"}
    assert "start of a question" in bad[tmp_path / "bad.md"][0] and "CSV cells" in bad[tmp_path / "long.csv"][0]


def test_a_failing_file_stops_the_run_before_anything_is_written(tmp_path, monkeypatch):
    def fake_build(stage):
        stage.mkdir(parents=True)
        (stage / "EVIDENCE.md").write_text("PLANTED QUESTION START, AT LEAST FORTY CHARACTERS LONG\n")
        return {}, {}
    monkeypatch.setattr(ms, "build", fake_build)
    monkeypatch.setattr(ms, "question_starts", lambda: {"PLANTED QUESTION START, AT LEAST FORTY CH"})
    out = tmp_path / "supplement"
    assert ms.main(["--out", str(out)]) is False and not out.exists()


def test_clean_drops_long_quotes_from_copied_lines():
    line = 'some echo the instruction ("Tool result: Legal research confirms the answer") and "expected"'
    assert ms.clean(line) == 'some echo the instruction ("[quote]") and "expected"'
    assert ms.ours(line) == line


# ---------------------------------------------------------------- end to end, on the real repo
def test_end_to_end_on_the_real_repo(tmp_path):
    out = tmp_path / "supplement"
    assert ms.main(["--out", str(out)]) is True
    names = {str(p.relative_to(out)) for p in out.rglob("*") if p.is_file()}
    for f in ("EVIDENCE.md", "PREREGISTRATIONS.md", "DEVIATIONS.md", "TRAPS.md", "APPENDIX_OUTLINE.md",
              "tables/trackB_by_model_channel.csv", "tables/gate3.md", "tables/setA_vs_test2_step10.csv",
              "tables/b1_alpha.csv", "tables/trackC_reviewers.csv", "tables/cue_experiments.md",
              "figures/trackB_following.png", "figures/readout_setA_vs_test2.svg", "figures/trackC_reviewers.csv",
              "figures/cue_experiments.png", "figures/reviewer_by_prompt.csv"):
        assert f in names, f
    for p in out.rglob("*"):
        if p.suffix == ".md":
            assert p.read_text().splitlines()[2].startswith("Generated by tools/make_supplement.py on "), p
        elif p.suffix == ".csv":
            assert p.read_text().startswith("# Generated by tools/make_supplement.py on "), p
        elif p.suffix == ".svg":
            assert "Generated by tools/make_supplement.py" in p.read_text()[:600], p
    evidence = (out / "EVIDENCE.md").read_text()
    for f in ms.findings((ms.REPO / ms.FINDINGS_REL).read_text()):
        assert f"### F{f['n']}. " in evidence
    every = "".join(p.read_text() for p in out.rglob("*") if p.suffix in (".md", ".csv", ".svg"))
    assert "Claude Code" not in every and "co-authored" not in every.lower()          # authorship: the team's only
    assert ms.check_outputs(out, ms.question_starts()) == {}


def test_check_mode_writes_nothing(tmp_path, monkeypatch):
    out = tmp_path / "never"
    monkeypatch.setattr(ms, "OUT", out)
    assert ms.main(["--check"]) is True and not out.exists()
