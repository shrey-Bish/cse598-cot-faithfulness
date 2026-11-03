"""The path allowlist check (tools/path_check.py): on a listed branch a commit may touch only the branch's allowed
paths; a merge may bring other files only unchanged from the branch merged in; --range reports what a branch changed
outside its list. On throwaway git repos; no network."""
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
