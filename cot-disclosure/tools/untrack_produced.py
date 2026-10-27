"""Untrack the produced data on the unpushed branches and rewrite their history, so it never
reaches GitHub (decided Oct 26). No file on disk is moved, changed or deleted.

What it does (with --run; the default is a dry run that changes nothing):
  1. refuses while the Steps 6-7 run is still going, or if HEAD isn't the branch to clean
  2. backs up first (--backup, required with --run): a git bundle of every ref, and beside it
     (<bundle>.sha256) the sha256 of every file under results/, finetune/data/ and configs/
  3. rewrites every commit of the branch that is on no remote (and, with --not-in, on none of the
     named local branches: decided Oct 27, only the commits unique to trackA-nosol), oldest first, with git plumbing
     on a temporary index: the same commit with the produced paths left out of its tree (same
     message, author, committer and dates; parents mapped; merges kept; commits left empty keep
     their message). The working tree and the real index are not touched.
  4. keeps the old tips as refs/backup/untrack-<date>/<branch> (local only; never use
     git push --mirror), then moves each local branch whose tip was rewritten (trackA-nosol, and
     main / voyager-ids-oct21, whose 2 unpushed commits are part of it)
  5. removes the produced paths from the real index only (git rm --cached): the files stay on
     disk and are now ignored (cot-disclosure/.gitignore)
  6. checks: every rewritten commit equals the old one outside the produced paths; no produced
     path in any rewritten commit; every file in the backup's sha256 list is unchanged; the
     pre-push check on the branch and on every --not-in branch
Produced paths (under cot-disclosure/): results/trackA/, results/trackB/, results/trackC/,
results/voyager_canary.jsonl, finetune/data/.

  python3 cot-disclosure/tools/untrack_produced.py --not-in main      # dry run: commits, paths, refs, checks
  python3 cot-disclosure/tools/untrack_produced.py --not-in main --run --backup ~/backup-before-rewrite.bundle
"""
import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

PATHS = ["cot-disclosure/results/trackA", "cot-disclosure/results/trackB", "cot-disclosure/results/trackC",
         "cot-disclosure/results/voyager_canary.jsonl", "cot-disclosure/finetune/data"]
RUNNING = "finetune/run_steps67.py"
SNAPSHOT = ["cot-disclosure/results", "cot-disclosure/finetune/data", "cot-disclosure/configs"]   # sha256-listed around the rewrite


def git(*args, env=None, input=None, cwd=None):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True, env=env, input=input,
                          cwd=cwd).stdout


def still_running(pattern):
    if not pattern:
        return []
    out = subprocess.run(["pgrep", "-fl", pattern], capture_output=True, text=True).stdout
    return [line for line in out.splitlines() if "untrack_produced" not in line]


def unpushed(branch, remote, cwd=None, not_in=()):
    return git("rev-list", "--reverse", "--topo-order", branch, "--not", f"--remotes={remote}", *not_in, cwd=cwd).split()


def backup(bundle, root):
    """A bundle of every ref and the sha256 list of SNAPSHOT's files beside it; {path: sha256}."""
    bundle = Path(bundle).expanduser()
    listing = bundle.with_name(bundle.name + ".sha256")
    if bundle.exists() or listing.exists():
        sys.exit(f"refusing: {bundle} or {listing} already exists (never overwritten)")
    git("bundle", "create", str(bundle), "--all", cwd=root)
    git("bundle", "verify", str(bundle), cwd=root)
    hashes = disk_hashes(root, SNAPSHOT)
    listing.write_text("".join(f"{h}  {p}\n" for p, h in sorted(hashes.items())))
    print(f"backup: {bundle} ({bundle.stat().st_size / 2 ** 20:.1f} MB, verified); {len(hashes)} files listed in {listing}")
    return hashes


def touched(commit, paths, cwd=None):
    return [p for p in git("ls-tree", "-r", "--name-only", commit, "--", *paths, cwd=cwd).splitlines()]


def disk_hashes(root, paths):
    out = {}
    for p in paths:
        base = Path(root) / p
        files = [base] if base.is_file() else sorted(f for f in base.rglob("*") if f.is_file()) if base.exists() else []
        for f in files:
            out[str(f.relative_to(root))] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


def split_commit(commit, cwd=None):
    """(author line, committer line, message) from the raw commit object."""
    raw = git("cat-file", "commit", commit, cwd=cwd)
    head, _, message = raw.partition("\n\n")
    fields = dict(line.split(" ", 1) for line in head.splitlines() if " " in line)
    return fields["author"], fields["committer"], message


def ident_env(line, who):
    """GIT_<WHO>_NAME / _EMAIL / _DATE from a raw 'Name <email> 1700000000 -0700' line."""
    name, rest = line.split(" <", 1)
    email, when = rest.split("> ", 1)
    return {f"GIT_{who}_NAME": name, f"GIT_{who}_EMAIL": email, f"GIT_{who}_DATE": "@" + when}


def rewrite(commits, paths, cwd=None):
    """{old commit: new commit}, oldest first, with `paths` left out of every tree."""
    mapping = {}
    with tempfile.TemporaryDirectory() as tmp:
        index = os.path.join(tmp, "index")
        for c in commits:
            env = {**os.environ, "GIT_INDEX_FILE": index}
            git("read-tree", c, env=env, cwd=cwd)
            git("rm", "-r", "-q", "-f", "--cached", "--ignore-unmatch", "--", *paths, env=env, cwd=cwd)   # index only
            tree = git("write-tree", env=env, cwd=cwd).strip()
            parents = git("rev-list", "--parents", "-n", "1", c, cwd=cwd).split()[1:]
            author, committer, message = split_commit(c, cwd)
            env = {**os.environ, **ident_env(author, "AUTHOR"), **ident_env(committer, "COMMITTER")}
            args = ["commit-tree", tree]
            for p in parents:
                args += ["-p", mapping.get(p, p)]
            mapping[c] = git(*args, env=env, input=message, cwd=cwd).strip()
    return mapping


def verify(mapping, paths, cwd=None):
    """[problem] (empty if every new commit equals the old one outside `paths` and has none of them)."""
    out = []
    excludes = [f":(exclude){p}" for p in paths]
    for old, new in mapping.items():
        if git("diff", "--name-only", old, new, "--", ".", *excludes, cwd=cwd).strip():
            out.append(f"{new[:9]} differs from {old[:9]} outside the produced paths")
        if touched(new, paths, cwd):
            out.append(f"{new[:9]} still has produced paths")
        if split_commit(old, cwd) != split_commit(new, cwd):
            out.append(f"{new[:9]} has a different message, author or date than {old[:9]}")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="store_true", help="rewrite (default: dry run)")
    ap.add_argument("--branch", default="trackA-nosol")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--running", default=RUNNING, help="refuse while a process matching this runs ('' = don't check)")
    ap.add_argument("--not-in", action="append", default=[], metavar="BRANCH",
                    help="leave the commits of this local branch alone (repeatable)")
    ap.add_argument("--backup", metavar="BUNDLE", help="with --run (required): the git bundle to write first")
    a = ap.parse_args(argv)
    root = git("rev-parse", "--show-toplevel").strip()
    os.chdir(root)
    commits = unpushed(a.branch, a.remote, not_in=a.not_in)
    hits = {c: touched(c, PATHS) for c in commits}
    heads = dict(line.split() for line in git("for-each-ref", "--format=%(refname:short) %(objectname)",
                                              "refs/heads").splitlines())
    moving = sorted(b for b, sha in heads.items() if sha in hits)
    disk = disk_hashes(root, PATHS)
    current = git("rev-parse", "--abbrev-ref", "HEAD").strip()
    busy = still_running(a.running)
    print(f"{a.branch}: {len(commits)} commits on no remote, {sum(bool(v) for v in hits.values())} of them track produced "
          f"files ({len({p for v in hits.values() for p in v})} paths)")
    for p in PATHS:
        n = len({x for v in hits.values() for x in v if x == p or x.startswith(p + '/')})
        print(f"  {p}: {n} paths in the history; {sum(1 for f in disk if f == p or f.startswith(p + '/'))} files on disk "
              f"(stay where they are)")
    print(f"branches that move to their rewritten commits: {', '.join(moving)}"
          + (f"; left alone: {', '.join(a.not_in)}" if a.not_in else ""))
    print(f"HEAD: {current}; the Steps 6-7 run: {'STILL RUNNING' if busy else 'not running'}")
    if not a.run:
        print("dry run: nothing changed. --run does it once the run has finished.")
        return 0
    if busy:
        sys.exit("refusing: the Steps 6-7 run is still going:\n  " + "\n  ".join(busy))
    if current != a.branch:
        sys.exit(f"refusing: HEAD is {current}, not {a.branch}")
    if not a.backup:
        sys.exit("refusing: --run needs --backup BUNDLE (a bundle of every ref and a sha256 list, written first)")
    listed = backup(a.backup, root)
    mapping = rewrite(commits, PATHS)
    problems = verify(mapping, PATHS)
    if problems:
        sys.exit("refusing to move any branch; the rewrite does not check out:\n  " + "\n  ".join(problems[:20]))
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    for b in moving:
        git("update-ref", f"refs/backup/untrack-{stamp}/{b}", heads[b])
        git("update-ref", f"refs/heads/{b}", mapping[heads[b]], heads[b])
        print(f"moved {b}: {heads[b][:9]} -> {mapping[heads[b]][:9]} (old tip kept as refs/backup/untrack-{stamp}/{b})")
    if current in moving:
        git("rm", "-r", "-q", "-f", "--cached", "--ignore-unmatch", "--", *PATHS)     # --cached: the index only
    after = disk_hashes(root, SNAPSHOT)
    if after != listed:
        sys.exit(f"FILES ON DISK CHANGED: {sorted(set(listed.items()) ^ set(after.items()))[:10]}")
    print(f"{len(listed)} files under {', '.join(SNAPSHOT)}: sha256 list identical; tracked under the produced "
          f"paths now: {len(git('ls-files', '--', *PATHS).split())}")
    worst = 0
    for b in [a.branch, *a.not_in]:
        check = subprocess.run([sys.executable, str(Path(root) / "cot-disclosure/tools/prepush_check.py"), a.remote,
                                "--rev", b], capture_output=True, text=True)
        print(f"{b}: " + (check.stdout + check.stderr).strip())
        worst = max(worst, check.returncode)
    return worst


if __name__ == "__main__":
    sys.exit(main())
