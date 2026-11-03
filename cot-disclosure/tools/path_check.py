"""Path allowlist check: on a branch listed in configs/path_allowlist.txt, a commit may touch only that branch's paths
(Nov 3: Track C's branch, trackC-main, is Shrey's; shared code is read-only there). Standard library only, so a plain
python3 runs it as a git hook.

Install once per clone as the pre-commit hook:
  printf '#!/bin/sh\\nexec python3 "$(git rev-parse --show-toplevel)/cot-disclosure/tools/path_check.py" "$@"\\n' > .git/hooks/pre-commit
  chmod +x .git/hooks/pre-commit
Check by hand, or review a branch before merging it:
  python3 cot-disclosure/tools/path_check.py                                   # the staged files (what the hook does)
  python3 cot-disclosure/tools/path_check.py --range origin/main..origin/trackC-main --branch trackC-main

The rules: one line per rule, "<branch> <path>"; a path ending in / is a folder, anything else a glob (fnmatch); # starts
a comment. Only listed branches are checked. The rules are read from HEAD's committed copy, so staging a wider list
doesn't widen it, and changing the list on a listed branch is itself refused (it is outside every list).
Every staged path counts: added, changed, deleted, and both names of a rename. During a merge (MERGE_HEAD), a path
outside the list passes only if it is exactly the version from the branch merged in. --range A..B lists every path
changed on B since its merge base with A (A's own changes aren't B's).
"""
import argparse
import fnmatch
import subprocess
import sys
from pathlib import Path

ALLOWLIST = "cot-disclosure/configs/path_allowlist.txt"


def git(repo, *args, check=True):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if check and r.returncode:
        raise SystemExit(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r


def parse_rules(text):
    """{branch: [path rules]}"""
    out = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            branch, path = line.split(None, 1)
            out.setdefault(branch, []).append(path.strip())
    return out


def allowed(path, rules):
    return any(path.startswith(r) if r.endswith("/") else fnmatch.fnmatchcase(path, r) for r in rules)


def rules_at_head(repo):
    r = git(repo, "show", f"HEAD:{ALLOWLIST}", check=False)
    if r.returncode == 0:
        return parse_rules(r.stdout)
    p = Path(repo) / ALLOWLIST                                    # no commit yet: the working copy
    return parse_rules(p.read_text()) if p.exists() else {}


def branch_of(repo):
    return git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def blob(repo, spec):
    r = git(repo, "rev-parse", "-q", "--verify", spec, check=False)
    return r.stdout.strip() if r.returncode == 0 else None


def check_staged(repo="."):
    """(branch, [staged paths outside its list]); an empty list on an unlisted branch."""
    branch = branch_of(repo)
    rules = rules_at_head(repo).get(branch)
    if rules is None:
        return branch, []
    names = git(repo, "diff", "--cached", "--name-only", "--no-renames").stdout.split("\n")
    outside = sorted({p for p in names if p and not allowed(p, rules)})
    if outside and blob(repo, "MERGE_HEAD"):                    # a merge: main's files pass only unchanged
        outside = [p for p in outside if blob(repo, f":{p}") != blob(repo, f"MERGE_HEAD:{p}")]
    return branch, outside


def check_range(repo, rng, branch):
    """[paths changed on the range's tip since its merge base with the start, outside the branch's list]"""
    rules = rules_at_head(repo).get(branch)
    if rules is None:
        return []
    a, b = rng.split("..", 1)
    names = git(repo, "diff", "--name-only", "--no-renames", f"{a}...{b}").stdout.split("\n")
    return sorted({p for p in names if p and not allowed(p, rules)})


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--range", help="A..B: check what B changed since its merge base with A")
    ap.add_argument("--branch", help="the branch whose list applies to --range (default: the current branch)")
    a = ap.parse_args(argv)
    repo = git(a.repo, "rev-parse", "--show-toplevel").stdout.strip()
    if a.range:
        branch = a.branch or branch_of(repo)
        outside = check_range(repo, a.range, branch)
        where = f"{a.range} (the {branch} list)"
    else:
        branch, outside = check_staged(repo)
        where = f"this commit on {branch}"
    if outside:
        print(f"path check: {where} touches {len(outside)} path(s) outside {ALLOWLIST}:", file=sys.stderr)
        for p in outside:
            print(f"  {p}", file=sys.stderr)
        print("Shared code is read-only here: write a new module under cot-disclosure/agents/, or ask Ritik.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
