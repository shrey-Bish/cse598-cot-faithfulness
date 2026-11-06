"""Pre-push check: refuse a push that would put produced data on GitHub (the repo is public).

Every commit being pushed (each one not already on the remote) is checked. A file in it fails the
push when the same file with the same content isn't already on the remote and it is:
  - under a produced-data folder: results/trackA/, results/trackB/, results/trackC/, results/labels/,
    results/handoff/, results/voyager_canary.jsonl, finetune/data/ (under cot-disclosure/)
  - a GPQA file: "gpqa" in its name, any case (code and docs, .py/.md, are allowed)
  - over 50 MB
Files already on the remote with the same content (the progress-round files on main) upload
nothing, so they pass. Numbers-only summaries belong in results/summaries/.

Every commit being pushed (Nov 6, Ritik's permanent rule) must also be the team's, with no AI attribution: its
author and committer team identities (configs/team_identities.txt), and no AI co-author, AI email, "Generated
with" or session line in its message. The rules are path_check.py's (its docstring); each offender is named.
Commits already on the remote are never checked, so old history never blocks a push.

Install it once per clone as the repo's pre-push hook (git passes the remote's name and the refs on stdin); since
Nov 6, path_check.py --install writes it with the other hooks:
  python3 cot-disclosure/tools/path_check.py --install
Check by hand, without pushing:
  python3 cot-disclosure/tools/prepush_check.py --rev trackA-nosol      # its commits not on origin
"""
import argparse
import os
import re
import subprocess
import sys

_bytecode, sys.dont_write_bytecode = sys.dont_write_bytecode, True     # a hook leaves no __pycache__ in tools/
import path_check  # noqa: E402                        # the team and attribution rules (same folder; stdlib only)
sys.dont_write_bytecode = _bytecode

PRODUCED = re.compile(r"^cot-disclosure/(results/track[ABC]/|results/labels/|results/handoff/|results/voyager_canary\.jsonl$|finetune/data/)")
GPQA = re.compile(r"gpqa", re.IGNORECASE)
ALLOWED_GPQA = (".py", ".md")
LIMIT = int(os.environ.get("PREPUSH_SIZE_LIMIT", 50 * 2 ** 20))
ZERO = "0" * 40


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def remote_files(remote):
    """{(path, blob)} in the tips of the remote's branches (what is already public)."""
    out = set()
    for ref in git("for-each-ref", "--format=%(refname)", f"refs/remotes/{remote}").split():
        if ref.endswith("/HEAD"):
            continue
        for line in git("ls-tree", "-r", ref).splitlines():
            meta, path = line.split("\t", 1)
            out.add((path, meta.split()[2]))
    return out


def new_commits(sha, remote):
    return git("rev-list", sha, "--not", f"--remotes={remote}").split()


def reasons(path, size):
    out = []
    if PRODUCED.match(path):
        out.append("produced data")
    name = path.rsplit("/", 1)[-1]
    if GPQA.search(name) and not name.endswith(ALLOWED_GPQA):
        out.append("a GPQA file")
    if size is not None and size > LIMIT:
        out.append(f"over {LIMIT // 2 ** 20} MB ({size / 2 ** 20:.1f} MB)")
    return out


def check(shas, remote):
    """[(commit, path, reasons)] for every offending file in the commits being pushed."""
    public = remote_files(remote)
    bad, seen = [], set()
    for sha in shas:
        for commit in new_commits(sha, remote):
            for line in git("ls-tree", "-r", "-l", commit).splitlines():
                meta, path = line.split("\t", 1)
                _, kind, blob, size = meta.split()
                if kind != "blob" or (path, blob) in public or (path, blob) in seen:
                    continue
                seen.add((path, blob))
                why = reasons(path, None if size == "-" else int(size))
                if why:
                    bad.append((commit, path, why))
    return bad


def commit_problems(shas, remote, team):
    """[(commit, problem)]: each commit being pushed (not yet on the remote) whose author, committer or message breaks
    the team rule (path_check.attribution_problems)."""
    out, seen = [], set()
    for sha in shas:
        for commit in new_commits(sha, remote):
            if commit in seen:
                continue
            seen.add(commit)
            author, committer, message = git("log", "-1", "--format=%an <%ae>%x00%cn <%ce>%x00%B", commit).split("\0", 2)
            out += [(commit, p) for p in path_check.attribution_problems(message, author, committer, team)]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("remote", nargs="?", default="origin", help="(from git) the remote's name")
    ap.add_argument("url", nargs="?", help="(from git) the remote's URL")
    ap.add_argument("--rev", action="append", help="check this branch or commit instead of reading stdin")
    a = ap.parse_args(argv)
    if a.rev:
        shas = [git("rev-parse", r).strip() for r in a.rev]
    else:
        shas = [line.split()[1] for line in sys.stdin if line.strip() and line.split()[1] != ZERO]
    bad = check(shas, a.remote)
    people = commit_problems(shas, a.remote, path_check.team_at_head(git("rev-parse", "--show-toplevel").strip()))
    if people:
        print(f"pre-push check: refusing the push, {len(people)} problem(s) with who made a commit (only the team, "
              "with no AI attribution; CLAUDE.md):", file=sys.stderr)
        for commit, why in people[:40]:
            print(f"  {commit[:9]} {why}", file=sys.stderr)
        print("Fix the unpushed commits (git commit --amend --reset-author for the last one, or git rebase -i), "
              "then push again; never --no-verify.", file=sys.stderr)
    if not bad:
        if people:
            return 1
        print(f"pre-push check: nothing produced, GPQA or over {LIMIT // 2 ** 20} MB in the push")
        print("pre-push check: every commit pushed is the team's, with no AI attribution")
        return 0
    print(f"pre-push check: refusing the push, {len(bad)} file(s) must not go to GitHub:", file=sys.stderr)
    for commit, path, why in bad[:40]:
        print(f"  {commit[:9]} {path}: {', '.join(why)}", file=sys.stderr)
    if len(bad) > 40:
        print(f"  ... and {len(bad) - 40} more", file=sys.stderr)
    print("Untrack them (they stay on disk) and rewrite the unpushed commits: cot-disclosure/tools/untrack_produced.py",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
