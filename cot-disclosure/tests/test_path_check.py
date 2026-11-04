"""The path allowlist check (tools/path_check.py): on a listed branch a commit may touch only the branch's allowed
paths; a merge may bring other files only unchanged from the branch merged in; --range reports what a branch changed
outside its list. On throwaway git repos; no network."""
import re
import subprocess
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "tools"))

import path_check as pc  # noqa: E402

RULES = """# branch  path (a folder ends in /; anything else is a glob)
trackC-main  cot-disclosure/agents/
trackC-main  cot-disclosure/tests/test_trackC_*
trackC-main  docs/trackC/
trackC-main  docs/tracks/TRACK_C.md
"""


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout


def write(repo, path, text):
    p = Path(repo) / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def make_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.name", "T")
    git(repo, "config", "user.email", "t@example.com")
    write(repo, pc.ALLOWLIST, RULES)
    write(repo, "cot-disclosure/client.py", "x = 1\n")
    write(repo, "cot-disclosure/agents/c19.py", "y = 1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    git(repo, "checkout", "-q", "-b", "trackC-main")
    return repo


def test_rules_and_matching():
    rules = pc.parse_rules(RULES)
    allow = rules["trackC-main"]
    assert pc.allowed("cot-disclosure/agents/new.py", allow)
    assert pc.allowed("cot-disclosure/tests/test_trackC_c19.py", allow)
    assert pc.allowed("docs/trackC/sessions/2026-11-04/x.md", allow)
    assert not pc.allowed("cot-disclosure/client.py", allow)
    assert not pc.allowed("cot-disclosure/tests/test_agents_dataset.py", allow)
    assert not pc.allowed("docs/tracks/TRACK_B.md", allow)
    assert not pc.allowed("docs/trackC.md", allow)                          # a folder rule is not a name prefix


def test_an_allowed_commit_passes_and_an_outside_one_is_refused(tmp_path):
    repo = make_repo(tmp_path)
    write(repo, "cot-disclosure/agents/c19.py", "y = 2\n")
    write(repo, "docs/trackC/TODO_C.md", "todo\n")
    git(repo, "add", "-A")
    assert pc.check_staged(repo) == ("trackC-main", [])
    git(repo, "commit", "-q", "-m", "ok")
    write(repo, "cot-disclosure/client.py", "x = 2\n")
    write(repo, "cot-disclosure/agents/c19.py", "y = 3\n")
    git(repo, "add", "-A")
    assert pc.check_staged(repo) == ("trackC-main", ["cot-disclosure/client.py"])
    assert pc.main(["--repo", str(repo)]) == 1


def test_deleting_or_renaming_a_shared_file_is_refused(tmp_path):
    repo = make_repo(tmp_path)
    git(repo, "mv", "cot-disclosure/client.py", "cot-disclosure/agents/client.py")
    assert pc.check_staged(repo)[1] == ["cot-disclosure/client.py"]


def test_the_allowlist_comes_from_head_so_staging_a_wider_one_does_not_help(tmp_path):
    repo = make_repo(tmp_path)
    write(repo, pc.ALLOWLIST, RULES + "trackC-main  cot-disclosure/\n")
    write(repo, "cot-disclosure/client.py", "x = 2\n")
    git(repo, "add", "-A")
    assert set(pc.check_staged(repo)[1]) == {pc.ALLOWLIST, "cot-disclosure/client.py"}


def test_other_branches_are_not_checked(tmp_path):
    repo = make_repo(tmp_path)
    git(repo, "checkout", "-q", "main")
    write(repo, "cot-disclosure/client.py", "x = 2\n")
    git(repo, "add", "-A")
    assert pc.check_staged(repo) == ("main", [])
    assert pc.main(["--repo", str(repo)]) == 0


def test_a_merge_may_take_main_files_unchanged_but_not_edit_them(tmp_path):
    repo = make_repo(tmp_path)
    write(repo, "cot-disclosure/agents/c19.py", "y = 2\n")
    git(repo, "commit", "-qam", "his work")
    git(repo, "checkout", "-q", "main")
    write(repo, "cot-disclosure/client.py", "x = 2\n")
    write(repo, "cot-disclosure/agents/c19.py", "y = 9\n")                 # a conflict with his work
    git(repo, "commit", "-qam", "main moves on")
    git(repo, "checkout", "-q", "trackC-main")
    subprocess.run(["git", "merge", "main"], cwd=repo, capture_output=True, text=True)   # stops on the conflict
    write(repo, "cot-disclosure/agents/c19.py", "y = 2\n")
    git(repo, "add", "-A")
    assert pc.check_staged(repo) == ("trackC-main", [])                     # client.py came from main unchanged
    write(repo, "cot-disclosure/client.py", "x = 3\n")                      # editing it in the merge is refused
    git(repo, "add", "-A")
    assert pc.check_staged(repo)[1] == ["cot-disclosure/client.py"]


def test_range_reports_what_a_branch_changed_outside_its_list(tmp_path):
    repo = make_repo(tmp_path)
    write(repo, "docs/trackC/FINDINGS_C.md", "f\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "ok")
    git(repo, "checkout", "-q", "main")
    write(repo, "cot-disclosure/client.py", "x = 5\n")                       # main's own change is not his
    git(repo, "commit", "-qam", "main")
    git(repo, "checkout", "-q", "trackC-main")
    assert pc.check_range(repo, "main..trackC-main", "trackC-main") == []
    write(repo, "README.md", "r\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "outside", "--no-verify")
    assert pc.check_range(repo, "main..trackC-main", "trackC-main") == ["README.md"]
    assert pc.main(["--repo", str(repo), "--range", "main..trackC-main", "--branch", "trackC-main"]) == 1


# ---------------------------------------------------------------- Nov 3: exclusions, the reverse guard, hooks, the real list
FROZEN_FOR_SOL = ["cot-disclosure/agents/__init__.py", "cot-disclosure/agents/sol_c13.py",   # every vLLM job's preflight
                  "cot-disclosure/progress/sol_trackB.py", "cot-disclosure/progress/sol_b17.py",
                  "cot-disclosure/progress/sol_b20.py", "cot-disclosure/progress/common.py", "cot-disclosure/client.py",
                  "cot-disclosure/finetune/eval.py", "cot-disclosure/finetune/gpu/sol/run.sh",
                  "cot-disclosure/tools/answer_key.py", "cot-disclosure/configs/path_allowlist.txt"]


def test_an_excluded_path_is_outside_the_list_and_owned_by_no_one():
    rules = pc.parse_rules(RULES + "trackC-main  !cot-disclosure/agents/sol_c13.py\n")
    assert pc.allowed("cot-disclosure/agents/c19.py", rules["trackC-main"])
    assert not pc.allowed("cot-disclosure/agents/sol_c13.py", rules["trackC-main"])
    assert pc.owner_of("cot-disclosure/agents/c19.py", rules) == "trackC-main"
    assert pc.owner_of("cot-disclosure/agents/sol_c13.py", rules) is None
    assert pc.owner_of("cot-disclosure/client.py", rules) is None


def test_on_another_branch_a_commit_may_not_change_the_owners_paths(tmp_path, capsys):
    repo = make_repo(tmp_path)
    git(repo, "checkout", "-q", "main")
    write(repo, "cot-disclosure/agents/c19.py", "y = 5\n")
    write(repo, "cot-disclosure/client.py", "x = 5\n")
    git(repo, "add", "-A")
    assert pc.check_owned(repo, env={}) == ("main", {"cot-disclosure/agents/c19.py": "trackC-main"}, {})
    assert pc.main(["--repo", str(repo)]) == 1
    err = capsys.readouterr().err
    assert "owned by trackC-main" in err and "git merge" in err and "cot-disclosure/agents/c19.py" in err


def test_the_owners_paths_come_in_only_by_a_merge_from_the_owner_unchanged(tmp_path):
    repo = make_repo(tmp_path)
    write(repo, "cot-disclosure/agents/c19.py", "y = 2\n")
    git(repo, "commit", "-qam", "his work")
    git(repo, "checkout", "-q", "main")
    write(repo, "cot-disclosure/client.py", "x = 2\n")
    git(repo, "commit", "-qam", "mine")
    git(repo, "merge", "--no-commit", "--no-ff", "trackC-main")
    assert pc.check_owned(repo, env={})[1] == {}                            # his file, exactly his version
    write(repo, "cot-disclosure/agents/c19.py", "y = 7\n")                  # edited during the merge: refused
    git(repo, "add", "-A")
    assert pc.check_owned(repo, env={})[1] == {"cot-disclosure/agents/c19.py": "trackC-main"}
    git(repo, "merge", "--abort")
    git(repo, "checkout", "-q", "-b", "side")                                # a merge from a branch that isn't his
    write(repo, "cot-disclosure/agents/c19.py", "y = 8\n")
    git(repo, "commit", "-qam", "side edits his file", "--no-verify")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "--no-commit", "--no-ff", "side")
    assert pc.check_owned(repo, env={})[1] == {"cot-disclosure/agents/c19.py": "trackC-main"}


def test_an_agreed_change_passes_with_a_warning_when_the_owner_is_named(tmp_path, capsys, monkeypatch):
    repo = make_repo(tmp_path)
    git(repo, "checkout", "-q", "main")
    write(repo, "docs/trackC/START_HERE.md", "quick start\n")
    git(repo, "add", "-A")
    monkeypatch.setenv("PATH_CHECK_ALLOW", "trackC-main")
    assert pc.check_owned(repo)[1:] == ({}, {"docs/trackC/START_HERE.md": "trackC-main"})
    assert pc.main(["--repo", str(repo)]) == 0 and "PATH_CHECK_ALLOW=trackC-main" in capsys.readouterr().err
    monkeypatch.setenv("PATH_CHECK_ALLOW", "trackB-main")                     # naming another owner doesn't help
    assert pc.main(["--repo", str(repo)]) == 1


def test_install_writes_both_hooks_and_git_runs_them(tmp_path):
    """The hooks: pre-commit (a commit, or a merge that stopped on a conflict) and pre-merge-commit (a clean merge)."""
    repo = make_repo(tmp_path)
    git(repo, "checkout", "-q", "main")                                      # the tool is on every branch, as here
    write(repo, "cot-disclosure/tools/path_check.py", (CODE / "tools" / "path_check.py").read_text())
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "the tool", "--no-verify")
    git(repo, "checkout", "-q", "trackC-main")
    git(repo, "merge", "-q", "--ff-only", "main")
    assert pc.main(["--repo", str(repo), "--install"]) == 0
    hooks = Path(repo) / ".git" / "hooks"
    assert all("path_check.py" in (hooks / h).read_text() for h in ("pre-commit", "pre-merge-commit"))
    assert pc.main(["--repo", str(repo), "--install"]) == 0                  # again: the same hooks, kept
    write(repo, "cot-disclosure/agents/c19.py", "y = 2\n")                  # his commit, on his branch: allowed
    assert subprocess.run(["git", "commit", "-qam", "his"], cwd=repo, capture_output=True).returncode == 0
    git(repo, "checkout", "-q", "main")
    write(repo, "cot-disclosure/agents/c19.py", "y = 9\n")                  # mine, on main: refused by git
    r = subprocess.run(["git", "commit", "-qam", "mine"], cwd=repo, capture_output=True, text=True)
    assert r.returncode != 0 and "owned by trackC-main" in r.stderr
    git(repo, "checkout", "-q", "--", ".")
    r = subprocess.run(["git", "merge", "-q", "--no-ff", "-m", "merge trackC-main", "trackC-main"], cwd=repo,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr                                       # a clean merge from the owner passes
    write(repo, "cot-disclosure/client.py", "x = 4\n")                      # and his clean merge of main the other way
    git(repo, "commit", "-qam", "main moves on")
    git(repo, "checkout", "-q", "trackC-main")
    r = subprocess.run(["git", "merge", "-q", "--no-ff", "-m", "merge main", "main"], cwd=repo, capture_output=True,
                       text=True)
    assert r.returncode == 0, r.stderr
    (hooks / "pre-commit").write_text("#!/bin/sh\nexit 0\n")                 # someone else's hook: not overwritten
    assert pc.main(["--repo", str(repo), "--install"]) == 1


def test_the_real_list_gives_each_teammate_their_track_and_keeps_sol_code_ritiks():
    rules = pc.parse_rules((CODE.parent / pc.ALLOWLIST).read_text())
    assert set(rules) == {"trackB-main", "trackC-main"}
    for path, owner in (("cot-disclosure/agents/c25.py", "trackC-main"), ("docs/trackC/START_HERE.md", "trackC-main"),
                        ("cot-disclosure/tests/test_trackC_c25.py", "trackC-main"),
                        ("cot-disclosure/results/summaries/trackC/c25_summary.json", "trackC-main"),
                        ("docs/trackB/START_HERE.md", "trackB-main"), ("docs/tracks/TRACK_B.md", "trackB-main"),
                        ("cot-disclosure/progress/run_b20.py", "trackB-main"),
                        ("cot-disclosure/progress/trackB_report.py", "trackB-main"),
                        ("cot-disclosure/tools/trackb_final.py", "trackB-main"),
                        ("cot-disclosure/tests/test_trackB_b20.py", "trackB-main"),
                        ("cot-disclosure/tests/test_trackb_final.py", "trackB-main"),
                        ("cot-disclosure/results/summaries/trackB/b17_report.json", "trackB-main")):
        assert pc.owner_of(path, rules) == owner, path
    for path in FROZEN_FOR_SOL + ["README.md", "docs/PLAN.md", "docs/status/TODO.md", "cot-disclosure/tools/slide_figures.py"]:
        assert pc.owner_of(path, rules) is None, path
    samples = [re.sub(r"\[(.)[^\]]*\]", r"\1", r).replace("*", "x") + ("x.md" if r.endswith("/") else "")
               for rs in rules.values() for r in rs if not r.startswith("!")]       # one path each rule matches
    assert all(len(pc.owners(s, rules)) == 1 for s in samples)               # no path is claimed by both
