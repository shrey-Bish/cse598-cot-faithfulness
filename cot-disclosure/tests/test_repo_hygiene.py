"""Produced data stays off GitHub: the pre-push check (tools/prepush_check.py) and the history
rewrite that untracks produced files (tools/untrack_produced.py), on scratch git repos with a
local bare "remote". Also: everything in results/summaries/ is numbers-only."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
TOOLS = CODE / "tools"
sys.path.insert(0, str(TOOLS))

import prepush_check  # noqa: E402
import untrack_produced  # noqa: E402


def git(repo, *args, **kw):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True, **kw).stdout


def write(repo, path, text):
    p = Path(repo) / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def commit(repo, msg, **files):
    for path, text in files.items():
        write(repo, path.replace("__", "/"), text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg)
    return git(repo, "rev-parse", "HEAD").strip()


@pytest.fixture
def repo(tmp_path):
    """origin/main has code and an old finetune/data file (already public); local main adds the
    canary log (unpushed)."""
    if not shutil.which("git"):
        pytest.skip("no git")
    remote, r = tmp_path / "remote.git", tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(r)], check=True)
    for k, v in (("user.name", "Test"), ("user.email", "t@example.com"), ("commit.gpgsign", "false")):
        git(r, "config", k, v)
    git(r, "remote", "add", "origin", str(remote))
    write(r, "cot-disclosure/tools/prepush_check.py", (TOOLS / "prepush_check.py").read_text())
    write(r, "cot-disclosure/.gitignore", "results/trackA/\nresults/trackB/\nresults/trackC/\n"
                                          "results/voyager_canary.jsonl\nfinetune/data/\n")
    commit(r, "base", **{"cot-disclosure__code.py": "x = 1\n", "cot-disclosure__finetune__data__train.jsonl": "{}\n"})
    git(r, "push", "-q", "origin", "main")
    write(r, "cot-disclosure/results/voyager_canary.jsonl", "{\"pass\": true}\n")
    git(r, "add", "-f", "cot-disclosure/results/voyager_canary.jsonl")
    commit(r, "main: canary log (unpushed)", **{"cot-disclosure__client.py": "guard = True\n"})
    return r


def check(repo, rev, env=None):
    return subprocess.run([sys.executable, str(TOOLS / "prepush_check.py"), "origin", "--rev", rev], cwd=repo,
                          capture_output=True, text=True, env={**os.environ, **(env or {})})


def test_prepush_refuses_produced_gpqa_and_big_files(repo):
    git(repo, "checkout", "-q", "-b", "feature")
    commit(repo, "code", **{"cot-disclosure__progress__gpqa_export.py": "pass\n", "README.md": "hi\n"})
    assert check(repo, "feature").returncode == 1                      # the canary log, from local main
    git(repo, "checkout", "-q", "-b", "clean", "origin/main")
    commit(repo, "fine", **{"cot-disclosure__progress__gpqa_export.py": "pass\n", "README.md": "hi\n"})
    ok = check(repo, "clean")
    assert ok.returncode == 0, ok.stderr                                 # gpqa in a .py name is code; data on main is public
    for path in ("cot-disclosure/results/trackB/run.jsonl", "cot-disclosure/data/GPQA_diamond.jsonl",
                 "cot-disclosure/finetune/data/train.jsonl"):
        git(repo, "checkout", "-q", "-B", "bad", "clean")
        write(repo, path, "{\"changed\": 1}\n")
        git(repo, "add", "-f", path)
        git(repo, "commit", "-q", "-m", "bad")
        r = check(repo, "bad")
        assert r.returncode == 1 and path in r.stderr
    git(repo, "checkout", "-q", "-B", "big", "clean")
    commit(repo, "big", **{"cot-disclosure__model.bin": "y" * 500})
    assert check(repo, "big", {"PREPUSH_SIZE_LIMIT": "100"}).returncode == 1
    assert check(repo, "big").returncode == 0


def test_hook_reads_refs_from_stdin(repo):
    tip = git(repo, "rev-parse", "main").strip()
    line = f"refs/heads/main {tip} refs/heads/main {git(repo, 'rev-parse', 'origin/main').strip()}\n"
    r = subprocess.run([sys.executable, str(TOOLS / "prepush_check.py"), "origin", "url"], cwd=repo, input=line,
                       capture_output=True, text=True)
    assert r.returncode == 1 and "voyager_canary" in r.stderr
    deleting = f"(delete) {'0' * 40} refs/heads/old {tip}\n"
    assert subprocess.run([sys.executable, str(TOOLS / "prepush_check.py"), "origin", "url"], cwd=repo,
                          input=deleting, capture_output=True, text=True).returncode == 0


def build_branch(repo):
    """trackA-nosol on top of local main: produced files, code, summaries, and a merge."""
    git(repo, "checkout", "-q", "-b", "trackA-nosol")
    for i, (msg, files) in enumerate([
            ("Step 1 results", {"cot-disclosure/results/trackA/probes.jsonl.gz": "data1", "cot-disclosure/a.py": "a\n"}),
            ("Step 2 report", {"cot-disclosure/results/trackA/probes.jsonl.gz": "data2",
                               "cot-disclosure/results/summaries/trackA/runs.jsonl": "{\"n\": 3}\n"}),
            ("dataset", {"cot-disclosure/finetune/data/train.jsonl": "{\"q\": \"text\"}\n", "cot-disclosure/b.py": "b\n"})]):
        for path, text in files.items():
            write(repo, path, text)
            git(repo, "add", "-f", path)
        git(repo, "commit", "-q", "-m", msg, "--date", f"2026-10-2{i}T10:00:00-07:00")
    git(repo, "checkout", "-q", "-b", "side", "main")
    commit(repo, "side docs", **{"docs__notes.md": "n\n"})
    git(repo, "checkout", "-q", "trackA-nosol")
    git(repo, "merge", "-q", "--no-ff", "-m", "merge side", "side")
    write(repo, "cot-disclosure/results/trackA/probes.jsonl.gz", "data3, being written")      # unstaged change
    write(repo, "cot-disclosure/results/trackA/new_run.jsonl", "new")                          # ignored, untracked


def test_untrack_rewrites_history_without_touching_files(repo, monkeypatch, capsys):
    build_branch(repo)
    before = {b: git(repo, "rev-parse", b).strip() for b in ("main", "trackA-nosol", "side")}
    messages = git(repo, "log", "--format=%an|%aI|%s", "trackA-nosol")
    disk = untrack_produced.disk_hashes(repo, untrack_produced.PATHS)
    monkeypatch.chdir(repo)
    assert untrack_produced.main(["--running", ""]) == 0                       # dry run: nothing moves
    assert {b: git(repo, "rev-parse", b).strip() for b in before} == before
    assert untrack_produced.main(["--run", "--running", ""]) == 0
    out = capsys.readouterr().out
    assert "moved trackA-nosol" in out and "moved main" in out and "pre-push check: nothing produced" in out
    assert git(repo, "rev-parse", "side").strip() != before["side"]         # merged into the branch: rewritten too
    assert untrack_produced.disk_hashes(repo, untrack_produced.PATHS) == disk
    assert (Path(repo) / "cot-disclosure/results/trackA/probes.jsonl.gz").read_text() == "data3, being written"
    assert not git(repo, "ls-files", "--", *untrack_produced.PATHS).strip()
    assert git(repo, "ls-files", "cot-disclosure/results/summaries").strip() == "cot-disclosure/results/summaries/trackA/runs.jsonl"
    assert git(repo, "log", "--format=%an|%aI|%s", "trackA-nosol") == messages
    for c in git(repo, "rev-list", "trackA-nosol", "--not", "--remotes=origin").split():
        assert not untrack_produced.touched(c, untrack_produced.PATHS, cwd=repo)
    assert git(repo, "status", "--porcelain").strip() == ""
    assert git(repo, "rev-parse", "origin/main").strip() == git(repo, "rev-list", "--max-parents=0", "trackA-nosol").strip()
    backups = git(repo, "for-each-ref", "--format=%(refname) %(objectname)", "refs/backup").splitlines()
    assert {line.split()[1] for line in backups} == set(before.values())


def test_untrack_refuses_while_the_run_is_going(repo, monkeypatch):
    build_branch(repo)
    monkeypatch.chdir(repo)
    tips = git(repo, "for-each-ref", "refs/heads")
    monkeypatch.setattr(untrack_produced, "still_running", lambda pattern: ["12290 python finetune/run_steps67.py"])
    with pytest.raises(SystemExit, match="still going"):
        untrack_produced.main(["--run"])
    assert git(repo, "for-each-ref", "refs/heads") == tips                 # nothing moved


def test_the_process_check_sees_a_running_process():
    if not shutil.which("pgrep"):
        pytest.skip("no pgrep")
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)  # untrack_test_marker_7f3"])
    try:
        import time
        for _ in range(50):
            if untrack_produced.still_running("untrack_test_marker_7f3"):
                break
            time.sleep(0.1)
        assert untrack_produced.still_running("untrack_test_marker_7f3")
        assert untrack_produced.still_running("") == []
    finally:
        proc.kill()


def test_summaries_are_numbers_only():
    sys.path.insert(0, str(CODE / "progress"))
    import export_summaries
    assert export_summaries.main(["--check"])
