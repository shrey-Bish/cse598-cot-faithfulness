"""Path allowlist check, both ways (configs/path_allowlist.txt). Standard library only, so a plain python3 runs it as a
git hook.
- **Forward:** on a branch listed there, a commit may touch only that branch's paths (Nov 3: trackC-main is Shrey's,
  trackB-main Arsha's; shared code is read-only on both).
- **Reverse** (Nov 3): every other branch (Ritik's trackA-nosol and main) may not change a path a listed branch owns,
  unless the commit is a merge from that branch and the path is exactly its version. A change the owner agreed to:
  PATH_CHECK_ALLOW=<owner branch> (comma-separated), which passes with a warning.

Install once per clone, as the pre-commit hook (a commit, or a merge that stopped on a conflict) and the pre-merge-commit
hook (a clean merge):
  python3 cot-disclosure/tools/path_check.py --install
Check by hand, or review a branch before merging it:
  python3 cot-disclosure/tools/path_check.py                                   # the staged files (what the hook does)
  python3 cot-disclosure/tools/path_check.py --range origin/main..origin/trackC-main --branch trackC-main

The rules: one line per rule, "<branch> <path>"; a path ending in / is a folder, anything else a glob (fnmatch); "!" before
a path excludes it from that branch's list (Nov 3: files Sol's jobs import stay Ritik's); # starts a comment. The rules are read from HEAD's committed copy, so staging a wider list
doesn't widen it, and changing the list on a listed branch is itself refused (it is outside every list).
Every staged path counts: added, changed, deleted, and both names of a rename. During a merge (MERGE_HEAD), a path
outside the list passes only if it is exactly the version from the branch merged in. --range A..B lists every path
changed on B since its merge base with A (A's own changes aren't B's).
"""
import argparse
import fnmatch
import os
import subprocess
import sys
from pathlib import Path

ALLOWLIST = "cot-disclosure/configs/path_allowlist.txt"
HOOKS = ("pre-commit", "pre-merge-commit")
HOOK = '#!/bin/sh\n# the path allowlist, both ways (cot-disclosure/tools/path_check.py --install)\n' \
       'exec python3 "$(git rev-parse --show-toplevel)/cot-disclosure/tools/path_check.py" "$@"\n'


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


def match(path, rule):
    return path.startswith(rule) if rule.endswith("/") else fnmatch.fnmatchcase(path, rule)


def allowed(path, rules):
    """In the list: a rule matches and no "!" rule excludes it."""
    return (any(match(path, r) for r in rules if not r.startswith("!"))
            and not any(match(path, r[1:]) for r in rules if r.startswith("!")))


def owners(path, all_rules):
    return [b for b, rules in all_rules.items() if allowed(path, rules)]


def owner_of(path, all_rules):
    """The listed branch whose paths include this one, else None (shared: Ritik's)."""
    return next(iter(owners(path, all_rules)), None)


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


def merge_heads(repo, env=None):
    """The commits being merged: MERGE_HEAD when a merge stopped (pre-commit), else the GITHEAD_<sha> variables git merge
    sets for its hooks (pre-merge-commit, a clean merge; MERGE_HEAD isn't written yet). [] outside a merge."""
    env = os.environ if env is None else env
    if blob(repo, "MERGE_HEAD"):
        path = git(repo, "rev-parse", "--git-path", "MERGE_HEAD").stdout.strip()
        path = path if os.path.isabs(path) else os.path.join(repo, path)
        return [line.strip() for line in open(path) if line.strip()]
    return [k[len("GITHEAD_"):] for k in env if k.startswith("GITHEAD_") and blob(repo, k[len("GITHEAD_"):])]


def unchanged_from(repo, path, commits):
    """Is the staged path exactly some merged commit's version (deleted in both counts)?"""
    return any(blob(repo, f":{path}") == blob(repo, f"{c}:{path}") for c in commits)


def check_staged(repo=".", env=None):
    """(branch, [staged paths outside its list]); an empty list on an unlisted branch."""
    branch = branch_of(repo)
    rules = rules_at_head(repo).get(branch)
    if rules is None:
        return branch, []
    outside = sorted({p for p in staged(repo) if not allowed(p, rules)})
    heads = merge_heads(repo, env) if outside else []
    if heads:                                                   # a merge: main's files pass only unchanged
        outside = [p for p in outside if not unchanged_from(repo, p, heads)]
    return branch, outside


def staged(repo):
    return [p for p in git(repo, "diff", "--cached", "--name-only", "--no-renames").stdout.split("\n") if p]


def from_branch(repo, commit, branch):
    """Is the commit on the branch (its tip or an ancestor), locally or on origin?"""
    for ref in (f"refs/heads/{branch}", f"refs/remotes/origin/{branch}"):
        if blob(repo, ref) and git(repo, "merge-base", "--is-ancestor", commit, ref, check=False).returncode == 0:
            return True
    return False


def check_owned(repo=".", env=None):
    """(branch, {staged path: owner} refused, {path: owner} waived by PATH_CHECK_ALLOW): the reverse rule, for a branch
    that isn't the owner. A merge from the owner may bring the owner's version of a path, unchanged."""
    env = os.environ if env is None else env
    branch = branch_of(repo)
    all_rules = rules_at_head(repo)
    owned = {p: o for p in staged(repo) if (o := owner_of(p, all_rules)) and o != branch}
    heads = merge_heads(repo, env) if owned else []
    if heads:
        owned = {p: o for p, o in owned.items()
                 if not unchanged_from(repo, p, [h for h in heads if from_branch(repo, h, o)])}
    allow = {s.strip() for s in env.get("PATH_CHECK_ALLOW", "").split(",") if s.strip()}
    return (branch, {p: o for p, o in owned.items() if o not in allow},
            {p: o for p, o in owned.items() if o in allow})


def install(repo):
    """Write the two hooks; one that someone else wrote is left alone (returns the hooks refused)."""
    d = Path(git(repo, "rev-parse", "--git-path", "hooks").stdout.strip())
    d = d if d.is_absolute() else Path(repo) / d
    d.mkdir(parents=True, exist_ok=True)
    refused = []
    for name in HOOKS:
        h = d / name
        if h.exists() and "path_check.py" not in h.read_text():
            refused.append(str(h))
            continue
        h.write_text(HOOK)
        h.chmod(0o755)
    return refused


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
    ap.add_argument("--install", action="store_true", help="write the pre-commit and pre-merge-commit hooks")
    a = ap.parse_args(argv)
    repo = git(a.repo, "rev-parse", "--show-toplevel").stdout.strip()
    if a.install:
        refused = install(repo)
        for h in refused:
            print(f"path check: {h} is someone else's hook; not overwritten (add this line to it: {HOOK.splitlines()[-1]})",
                  file=sys.stderr)
        return 1 if refused else 0
    if a.range:
        branch = a.branch or branch_of(repo)
        outside = check_range(repo, a.range, branch)
        where = f"{a.range} (the {branch} list)"
    else:
        branch, outside = check_staged(repo, os.environ)
        where = f"this commit on {branch}"
    if outside:
        print(f"path check: {where} touches {len(outside)} path(s) outside {ALLOWLIST}:", file=sys.stderr)
        for p in outside:
            print(f"  {p}", file=sys.stderr)
        print("Shared code is read-only here: write a new module in your track's folder, or ask Ritik.", file=sys.stderr)
        return 1
    if a.range:
        return 0
    branch, owned, waived = check_owned(repo)
    for p, o in sorted(waived.items()):
        print(f"path check: PATH_CHECK_ALLOW={o}: committing {p}, owned by {o} (agreed with its owner)", file=sys.stderr)
    if owned:
        print(f"path check: this commit on {branch} changes {len(owned)} path(s) owned by another branch "
              f"({ALLOWLIST}):", file=sys.stderr)
        for p, o in sorted(owned.items()):
            print(f"  {p}  (owned by {o})", file=sys.stderr)
        print("They change only through a merge from their branch (git merge origin/<owner>), taken unchanged; for a "
              "change the owner agreed to: PATH_CHECK_ALLOW=<owner> git commit ...", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
