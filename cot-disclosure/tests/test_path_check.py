"""The path allowlist check (tools/path_check.py): on a listed branch a commit may touch only the branch's allowed
paths; a merge may bring other files only unchanged from the branch merged in; --range reports what a branch changed
outside its list. On throwaway git repos; no network."""
import hashlib
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
                        ("docs/paper/tables/trackB_final.md", "trackB-main"),       # Nov 6: B18's table, which
                        ("docs/paper/tables/trackB_final.csv", "trackB-main"),      # trackb_final.py writes
                        ("cot-disclosure/results/summaries/trackB/b17_report.json", "trackB-main")):
        assert pc.owner_of(path, rules) == owner, path
    for path in FROZEN_FOR_SOL + ["README.md", "docs/PLAN.md", "docs/status/TODO.md", "cot-disclosure/tools/slide_figures.py"]:
        assert pc.owner_of(path, rules) is None, path
    samples = [re.sub(r"\[(.)[^\]]*\]", r"\1", r).replace("*", "x") + ("x.md" if r.endswith("/") else "")
               for rs in rules.values() for r in rs if not r.startswith("!")]       # one path each rule matches
    assert all(len(pc.owners(s, rules)) == 1 for s in samples)               # no path is claimed by both


# ---------------------------------------------------------------- Nov 5: commits carry only the human's own name
TRAILER = "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
FOOTER = "\U0001f916 Generated with [Claude Code](https://claude.com/claude-code)"
ME = "Shrey <shrey@example.com>"


def test_ai_attribution_lines_and_an_ai_identity_are_refused():
    assert pc.attribution_problems("C19's reading (Shrey, Nov 7)\n", ME, ME) == []
    for message in (f"C19's reading\n\n{TRAILER}\n", f"C19's reading\n\n{FOOTER}\n",
                    "C19\n\nco-authored-by: claude <claude@example.com>\n", "C19\n\nCo-Authored-By: x <noreply@anthropic.com>\n",
                    "C19\n\nGenerated with Claude Code\n"):
        assert pc.attribution_problems(message, ME, ME), message
    assert pc.attribution_problems("C19\n", "Claude <noreply@anthropic.com>", ME)          # --author
    assert pc.attribution_problems("C19\n", ME, "Someone <bot@anthropic.com>")             # -c user.email=
    assert pc.attribution_problems("C19\n", "claude-bot <x@example.com>", ME)


def test_naming_claude_code_or_a_human_co_author_is_fine_and_comments_are_ignored():
    for message in ("The root CLAUDE.md and .claude/settings.json: Claude Code adds no trailer (Ritik, Nov 5)\n",
                    "C25's notes\n\nCo-Authored-By: Arsha <arsha@example.com>\n",
                    f"C19\n# {TRAILER}\n",                                                 # a comment line: git drops it
                    f"C19\n# ------------------------ >8 ------------------------\n+{FOOTER}\n+{TRAILER}\n"):  # commit -v's diff
        assert pc.attribution_problems(message, ME, ME) == [], message


def test_install_adds_a_commit_msg_hook_that_git_runs(tmp_path):
    repo = make_repo(tmp_path)
    write(repo, "cot-disclosure/tools/path_check.py", (CODE / "tools" / "path_check.py").read_text())
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "the tool", "--no-verify")
    assert pc.main(["--repo", str(repo), "--install"]) == 0
    assert "--commit-msg" in (Path(repo) / ".git" / "hooks" / "commit-msg").read_text()

    def commit(message, config=(), extra=()):
        write(repo, "docs/trackC/TODO_C.md", f"{message} {config} {extra}\n")
        git(repo, "add", "-A")
        return subprocess.run(["git", *config, "commit", "-qm", message, *extra], cwd=repo, capture_output=True, text=True)

    for r in (commit(f"C19\n\n{TRAILER}"), commit(f"C19\n\n{FOOTER}"),
              commit("C19", extra=["--author=Claude <noreply@anthropic.com>"]),
              commit("C19", config=["-c", "user.name=Claude", "-c", "user.email=noreply@anthropic.com"])):
        assert r.returncode == 1 and re.search(r"(commit-msg|identity check): refused", r.stderr), r.stderr  # Nov 6:
    assert git(repo, "log", "-1", "--format=%s").strip() == "the tool"   # an AI author is refused at pre-commit already
    assert commit("C19's reading (T, Nov 7)").returncode == 0                             # a clean one passes
    assert git(repo, "log", "-1", "--format=%an <%ae>|%cn <%ce>").strip() == "T <t@example.com>|T <t@example.com>"


# ---------------------------------------------------------------- Nov 6: only the team commits (configs/team_identities.txt)
def h(email):
    """The team file's form of an email (Nov 6, Ritik's decision b): sha256 of it lower-cased; no email is stored."""
    return "sha256:" + hashlib.sha256(email.strip().lower().encode()).hexdigest()


TEAM = f"""# test team: hashed emails only
Ritik Agarwal | {h("ritik@example.com")}
Shrey Bishnoi | {h("Shrey@Example.com")}, {h("shrey2@example.com")}
Arsha Jindal  | {h("arsha@example.com")}, {h("aj@example.com")}
"""


def test_a_team_identity_passes_by_the_hash_of_its_email_whatever_its_name():
    team = pc.parse_team(TEAM)
    assert [p[0] for p in team] == ["Ritik Agarwal", "Shrey Bishnoi", "Arsha Jindal"]
    assert [len(p[1]) for p in team] == [1, 2, 2]
    for ok in ("Ritik <ritik@example.com>", "Ritik Agarwal <RITIK@example.com>",      # the email, any case, any name
               "Shrey <shrey@example.com>", "S B <shrey2@example.com>",
               "Arsha Jindal <arsha@example.com>", "A <AJ@example.com>"):
        assert pc.identity_problem(ok, team) is None, ok
    for bad in ("Ritik <other@example.com>",                                        # a listed person, another email
                "Arsha Jindal <arsha.j@example.com>",                               # her name, an email not hers
                "Shrey Bishnoi <s@example.com>",
                "Someone <s@example.com>",
                "Arsha Jindal <x@openai.com>",                                      # her name, an AI email
                "Claude <noreply@anthropic.com>", "Ritik <noreply@anthropic.com>",
                "Copilot <198982749+Copilot@users.noreply.github.com>", "Ritik (aider) <ritik@example.com>",
                "gemini-code-assist[bot] <bot@example.com>", "Cursor Agent <cursoragent@cursor.com>"):
        assert pc.identity_problem(bad, team), bad


def test_an_older_copy_with_plain_emails_is_read_by_their_hashes():
    old = "Ritik Agarwal | Ritik <ritik@example.com>\nArsha Jindal |   # email to confirm\n"   # 37738b4's form
    team = pc.parse_team(old)
    assert team == [("Ritik Agarwal", {h("ritik@example.com")}), ("Arsha Jindal", set())]
    assert pc.identity_problem("R <RITIK@example.com>", team) is None
    assert pc.identity_problem("Arsha Jindal <arsha@example.com>", team)           # no name-only pass any more


def test_hash_prints_the_team_file_form_of_an_email(capsys):
    assert pc.main(["--hash", " Ritik@Example.com "]) == 0
    assert capsys.readouterr().out.strip() == h("ritik@example.com")


def test_without_a_team_file_only_ai_identities_are_refused():
    assert pc.identity_problem("T <t@example.com>", None) is None
    assert pc.identity_problem("Claude <noreply@anthropic.com>", None)
    assert pc.identity_problem("ChatGPT <x@example.com>", None)


def test_message_rules_refuse_ai_co_authors_tool_lines_and_session_lines():
    team = pc.parse_team(TEAM)
    me = "Ritik <ritik@example.com>"
    for message in ("C19\n\nco-authored-by: Someone <s@example.com>\n",                   # any case, not the team
                    "C19\n\nCO-AUTHORED-BY: Shrey <shrey@other.com>\n",
                    "C19\n\nCo-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>\n",
                    "C19\n\nReviewed-by: x <bot@openai.com>\n",                          # an AI email on any line
                    "C19\n\nGenerated with Cursor\n", "C19\n\n\U0001f916 Generated with [Codex](https://openai.com)\n",
                    "C19\n\nClaude-Session: 01ABCdef\n", "C19\n\nSession-Id: 42\n",
                    "C19\n\nhttps://claude.ai/code/session_01AbC\n"):
        assert pc.attribution_problems(message, me, me, team), message
    for message in ("C19\n\nCo-authored-by: Shrey Bishnoi <shrey@example.com>\n",          # a team co-author
                    "C19\n\nCo-Authored-By: Arsha Jindal <aj@example.com>\n",
                    "The root CLAUDE.md and .claude/settings.json: Claude Code adds no trailer (Ritik, Nov 6)\n",
                    "The supplement regenerated with make_supplement.py; the Gantt generated with make_gantt\n",
                    "The 23:13 session's checks recorded\n\nSession log: archive/sessions/x.md\n"):
        assert pc.attribution_problems(message, me, me, team) == [], message
    assert pc.attribution_problems("C19\n", "Someone <s@example.com>", me, team)           # a non-team author
    assert pc.attribution_problems("C19\n", me, "Someone <s@example.com>", team)           # a non-team committer


def test_the_real_team_file_holds_hashes_only_and_lets_the_history_in():
    text = (CODE.parent / pc.TEAM_FILE).read_text()
    assert not pc.EMAIL.findall(text) and "@" not in text                    # no email in it, plain, anywhere
    team = pc.parse_team(text)
    assert [(p, len(hs)) for p, hs in sorted(team)] == [("Arsha Jindal", 2), ("Ritik Agarwal", 1), ("Shrey Bishnoi", 2)]
    for person, hashes in team:
        assert all(re.fullmatch(r"sha256:[0-9a-f]{64}", x) for x in hashes), person
    seen = subprocess.run(["git", "log", "--all", "--format=%an <%ae>%n%cn <%ce>"], cwd=CODE.parent,
                          capture_output=True, text=True).stdout.split("\n")
    seen = {s for s in seen if s}
    names = {pc.split_ident(s)[0] for s in seen}
    assert {"Ritik", "Shrey Bishnoi"} <= names                                 # both have commits in the history
    for ident in seen:                                                         # every identity in the history passes
        assert pc.identity_problem(ident, team) is None, pc.split_ident(ident)[0]
    assert pc.identity_problem("Arsha Jindal <arsha@example.com>", team)       # her name alone no longer passes
    assert pc.identity_problem("Claude <noreply@anthropic.com>", team)


def test_no_tracked_file_holds_a_team_email_in_plain_text():
    team = pc.parse_team((CODE.parent / pc.TEAM_FILE).read_text())
    hashes = {x: person for person, hs in team for x in hs}
    files = subprocess.run(["git", "ls-files", "-z"], cwd=CODE.parent, capture_output=True, text=True).stdout
    found = []
    for f in filter(None, files.split("\0")):
        try:
            data = (CODE.parent / f).read_bytes()
        except OSError:
            continue
        if b"\0" in data[:8192]:                                               # binary
            continue
        for email in pc.EMAIL.findall(data.decode("utf-8", "replace")):
            if pc.email_hash(email) in hashes:
                found.append((f, hashes[pc.email_hash(email)]))               # the file and whose, never the address
    assert not found, found


def test_install_writes_four_hooks_and_a_non_team_commit_is_refused_before_it_is_made(tmp_path):
    repo = make_repo(tmp_path)
    git(repo, "checkout", "-q", "main")                                      # the tools and the team on every branch
    for name in ("path_check.py", "prepush_check.py"):
        write(repo, f"cot-disclosure/tools/{name}", (CODE / "tools" / name).read_text())
    write(repo, pc.TEAM_FILE, f"T Person | {h('t@example.com')}\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "the tools and the team", "--no-verify")
    git(repo, "checkout", "-q", "trackC-main")
    git(repo, "merge", "-q", "--ff-only", "main")
    hooks = Path(repo) / ".git" / "hooks"
    (hooks / "pre-push").write_text('#!/bin/sh\nexec python3 "$(git rev-parse --show-toplevel)/cot-disclosure/tools/'
                                    'prepush_check.py" "$@"\n')                # RUNBOOK §17's hand-written line
    assert pc.main(["--repo", str(repo), "--install"]) == 0
    assert set(pc.HOOKS) == {"pre-commit", "pre-merge-commit", "commit-msg", "pre-push"}
    assert "prepush_check.py" in (hooks / "pre-push").read_text() and "--install" in (hooks / "pre-push").read_text()

    def commit(message, config=(), extra=()):
        write(repo, "docs/trackC/TODO_C.md", f"{message} {config} {extra}\n")
        git(repo, "add", "-A")
        return subprocess.run(["git", *config, "commit", "-qm", message, *extra], cwd=repo, capture_output=True, text=True)

    r = commit("C19", extra=["--author=Someone <s@example.com>"])
    assert r.returncode == 1 and "not a team identity" in r.stderr, r.stderr
    r = commit("C19", config=["-c", "user.name=Other", "-c", "user.email=o@example.com"])
    assert r.returncode == 1 and "not a team identity" in r.stderr, r.stderr
    r = commit("C19\n\nCo-authored-by: Someone <s@example.com>")
    assert r.returncode == 1 and "commit-msg: refused" in r.stderr, r.stderr
    assert git(repo, "log", "-1", "--format=%s").strip() == "the tools and the team"         # none was made
    assert commit("C19's reading (T, Nov 7)").returncode == 0
    git(repo, "checkout", "-q", "main")
    write(repo, "cot-disclosure/client.py", "x = 5\n")
    git(repo, "commit", "-qam", "main moves on")
    git(repo, "checkout", "-q", "trackC-main")
    r = subprocess.run(["git", "merge", "-q", "--no-ff", "-m", "merge main", "main"], cwd=repo, capture_output=True,
                       text=True)
    assert r.returncode == 0, r.stderr                                          # a team merge of main passes
    (hooks / "pre-push").write_text("#!/bin/sh\nexit 0\n")                     # someone else's pre-push: left alone
    assert pc.main(["--repo", str(repo), "--install"]) == 1


# ---------------------------------------------------------------- Nov 6, 23:21: the hooks don't depend on the platform's encoding
# Arsha, Git for Windows: Windows Python reads the message as cp1252, so the footer's emoji arrives as mojibake that
# starts with letters (ð, Ÿ), and "Generated with" no longer matched at the line's start.
MOJIBAKE = FOOTER.encode("utf-8").decode("cp1252", errors="replace")


def cp1252_default(monkeypatch):
    """Make read_text() and text-mode subprocess.run() decode as Windows' cp1252 when no encoding is given."""
    real_read, real_run = Path.read_text, subprocess.run

    def read_text(self, encoding=None, errors=None, **kw):
        return real_read(self, encoding=encoding or "cp1252", errors=errors, **kw)

    def run(*a, **kw):
        if (kw.get("text") or kw.get("universal_newlines")) and not kw.get("encoding"):
            kw["encoding"], kw["errors"] = "cp1252", kw.get("errors") or "replace"
        return real_run(*a, **kw)
    monkeypatch.setattr(Path, "read_text", read_text)
    monkeypatch.setattr(subprocess, "run", run)


def test_the_commit_message_is_read_as_utf8_whatever_the_platform_default(tmp_path, monkeypatch):
    repo = make_repo(tmp_path)
    msg = tmp_path / "COMMIT_EDITMSG"
    msg.write_bytes(f"C19's reading\n\n{FOOTER}\n".encode("utf-8"))
    seen = []
    real = pc.attribution_problems
    monkeypatch.setattr(pc, "attribution_problems", lambda m, *a: seen.append(m) or real(m, *a))
    cp1252_default(monkeypatch)
    assert pc.main(["--repo", str(repo), "--commit-msg", str(msg)]) == 1
    assert FOOTER in seen[0], seen                        # the emoji arrives intact, not as mojibake


def test_a_tool_line_after_a_mojibake_prefix_is_still_refused():
    assert MOJIBAKE != FOOTER and MOJIBAKE[0].isalpha()    # "ðŸ¤– Generated with …": it starts with a letter
    assert pc.attribution_problems(f"C19\n\n{MOJIBAKE}\n", ME, ME)
    for message in ("The supplement regenerated with its script (Ritik, Nov 6)\n", "C19\n\nFigures generated with matplotlib\n"):
        assert pc.attribution_problems(message, ME, ME) == [], message


def test_git_output_is_decoded_as_utf8_whatever_the_platform_default(tmp_path, monkeypatch):
    repo = make_repo(tmp_path)
    git(repo, "commit", "-q", "--allow-empty", "--no-verify", "-m", f"C19\n\n{FOOTER}")
    cp1252_default(monkeypatch)
    assert FOOTER in pc.git(repo, "log", "-1", "--format=%B").stdout


def test_a_refusal_prints_even_to_a_cp1252_console(tmp_path, monkeypatch):
    import io
    repo = make_repo(tmp_path)
    msg = tmp_path / "COMMIT_EDITMSG"
    msg.write_bytes(f"C19\n\n{FOOTER}\n".encode("utf-8"))
    monkeypatch.setattr(sys, "stderr", io.TextIOWrapper(io.BytesIO(), encoding="cp1252"))
    assert pc.main(["--repo", str(repo), "--commit-msg", str(msg)]) == 1      # not a UnicodeEncodeError


def test_the_installed_hooks_run_python_in_utf8_mode_with_unix_line_ends(tmp_path):
    repo = make_repo(tmp_path)
    assert pc.main(["--repo", str(repo), "--install"]) == 0
    for name in pc.HOOKS:
        raw = (Path(repo) / ".git" / "hooks" / name).read_bytes()
        assert b"PYTHONUTF8=1" in raw and b"PYTHONIOENCODING=utf-8" in raw and b"\r\n" not in raw, name
        assert b"path_check.py" in raw, name               # still recognised as ours by --install
