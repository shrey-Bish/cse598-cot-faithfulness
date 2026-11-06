"""Path allowlist check, both ways (configs/path_allowlist.txt). Standard library only, so a plain python3 runs it as a
git hook.
- **Forward:** on a branch listed there, a commit may touch only that branch's paths (Nov 3: trackC-main is Shrey's,
  trackB-main Arsha's; shared code is read-only on both).
- **Reverse** (Nov 3): every other branch (Ritik's trackA-nosol and main) may not change a path a listed branch owns,
  unless the commit is a merge from that branch and the path is exactly its version. A change the owner agreed to:
  PATH_CHECK_ALLOW=<owner branch> (comma-separated), which passes with a warning.

Install once per clone, as the pre-commit hook (a commit, or a merge that stopped on a conflict) and the pre-merge-commit
hook (a clean merge), and (Nov 5) the commit-msg hook:
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

The commit-msg hook (Nov 5; every branch, CLAUDE.md): a commit carries only its human author's own name. It refuses a
message with an AI co-author trailer (Co-Authored-By naming Claude or Anthropic), a "generated with" line for Claude
Code, or noreply@anthropic.com, and an author or committer named Claude or at anthropic.com. Comment lines and
`commit -v`'s diff below the scissors line don't count; naming Claude Code or CLAUDE.md in a message is fine.

Only the team commits (Nov 6, Ritik's permanent rule; configs/team_identities.txt, read from HEAD like the allowlist).
- An identity ("Name <email>") passes if its email is one listed for a person (any case); for a person with no email
  listed yet, if its name is that person's exact name. Never if its name or email is an AI tool's (AI_NAME, AI_DOMAINS,
  and a GitHub noreply address of a bot or an AI agent). Without the file (an old branch), only AI identities fail.
- pre-commit and pre-merge-commit also refuse a non-team author or committer (git var GIT_AUTHOR_IDENT and
  GIT_COMMITTER_IDENT, so --author and -c user.* count).
- commit-msg also refuses any Co-authored-by (any case) that isn't a team identity, any line with an AI tool's email,
  a "Generated with ..." line (any tool) and a session line ("Claude-Session:", "Session-Id:", a claude.ai/code link).
- pre-push (written by --install since Nov 6; tools/prepush_check.py) checks every commit being pushed that isn't
  already on the remote by the same rules, and names each offender. History already on the remote is never blocked.
Claude Code's own attribution setting (.claude/settings.json) is not relied on: these hooks are the enforcement.
"""
import argparse
import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path

ALLOWLIST = "cot-disclosure/configs/path_allowlist.txt"
HOOK = '#!/bin/sh\n# the path allowlist, both ways (cot-disclosure/tools/path_check.py --install)\n' \
       'exec python3 "$(git rev-parse --show-toplevel)/cot-disclosure/tools/path_check.py" "$@"\n'
MSG_HOOK = '#!/bin/sh\n# no AI attribution; the human author only (cot-disclosure/tools/path_check.py --install)\n' \
           'exec python3 "$(git rev-parse --show-toplevel)/cot-disclosure/tools/path_check.py" --commit-msg "$1"\n'
PUSH_HOOK = '#!/bin/sh\n# no produced data, and only the team with no AI attribution, in what is pushed ' \
            '(cot-disclosure/tools/path_check.py --install)\n' \
            'exec python3 "$(git rev-parse --show-toplevel)/cot-disclosure/tools/prepush_check.py" "$@"\n'
HOOKS = {"pre-commit": HOOK, "pre-merge-commit": HOOK, "commit-msg": MSG_HOOK, "pre-push": PUSH_HOOK}
OURS = {"pre-push": ("path_check.py", "prepush_check.py")}           # a hook with one of these in it is ours to rewrite
SCISSORS = re.compile(r"^# -+ >8 -+$", re.MULTILINE)
TEAM_FILE = "cot-disclosure/configs/team_identities.txt"
# AI tools, by name (an author, committer or co-author) and by email domain (any line of a message). Nov 6; extend here.
AI_NAME = re.compile(r"\b(claude|anthropic|openai|chatgpt|gpt-?\d\w*|codex|copilot|cursor|codeium|windsurf|gemini|bard|"
                     r"aider|tabnine|codewhisperer|amazon q|devin-ai|jules)\b|\[bot\]", re.IGNORECASE)
AI_DOMAINS = ("anthropic.com", "claude.ai", "claude.com", "openai.com", "chatgpt.com", "cursor.com", "cursor.sh",
              "codeium.com", "windsurf.com", "tabnine.com", "aider.chat", "cognition.ai", "devin.ai")
EMAIL = re.compile(r"[\w.+\[\]-]+@[\w-]+(?:\.[\w-]+)+")
CO_AUTHOR = re.compile(r"^\s*co-authored-by\s*:\s*(.*)$", re.IGNORECASE)
TOOL_LINE = re.compile(r"^\W*generated with\b", re.IGNORECASE)                  # "🤖 Generated with [X](...)"
SESSION_LINE = re.compile(r"^\s*([\w-]*-)?session(-[\w-]+)?\s*:|claude\.ai/code/|/code/session_", re.IGNORECASE)


TEAM_HELP = ("Only the team commits here, as themselves (CLAUDE.md): git config user.name and user.email must match your line "
             f"in {TEAM_FILE} (to add an email: ask Ritik, a line on main), with no AI co-author, \"Generated with\" or "
             "session line. Fix it and commit again; never --no-verify.")


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


def parse_team(text):
    """[(person, [emails, lower case])] from configs/team_identities.txt: "Person | Name <email>, Name <email>"."""
    out = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            person, _, idents = line.partition("|")
            out.append((person.strip(), [e.lower() for e in EMAIL.findall(idents)]))
    return out


def team_at_head(repo):
    """The team from HEAD's committed copy (staging a wider list doesn't widen it); no commit of it yet: the working
    copy; no file at all (an old branch): None, and only AI identities fail."""
    r = git(repo, "show", f"HEAD:{TEAM_FILE}", check=False)
    if r.returncode == 0:
        return parse_team(r.stdout)
    p = Path(repo) / TEAM_FILE
    return parse_team(p.read_text()) if p.exists() else None


def split_ident(ident):
    name, _, rest = ident.partition("<")
    return name.strip(), rest.split(">", 1)[0].strip()


def ai_email(email):
    local, _, domain = email.lower().rpartition("@")
    if any(domain == d or domain.endswith("." + d) for d in AI_DOMAINS):
        return True
    return domain.endswith("noreply.github.com") and bool(AI_NAME.search(local.replace("+", " ")))


def identity_problem(ident, team):
    """None if "Name <email>" is a team identity (or, with no team file, anything but an AI tool's); else why not."""
    name, email = split_ident(ident)
    if AI_NAME.search(name) or ai_email(email):
        return f"{ident.strip()} is an AI tool's identity"
    if team is None:
        return None
    for person, emails in team:
        if (email.lower() in emails) if emails else (name == person):
            return None
    return f"{ident.strip()} is not a team identity ({TEAM_FILE})"


def attribution_problems(message, author, committer, team=None):
    """[problem] in the message as git keeps it (no # comments, nothing below commit -v's scissors line): a co-author
    that isn't a team identity (or, with no team, is an AI tool), a line with an AI tool's email, a "Generated with"
    line, a session line; and an author or committer ("Name <email>") that isn't a team identity or is an AI tool."""
    kept = [line for line in SCISSORS.split(message, 1)[0].splitlines() if not line.startswith("#")]
    problems = []
    for line in kept:
        m = CO_AUTHOR.match(line)
        if m:
            why = identity_problem(m.group(1), team)
            if why:
                problems.append(f"a co-author line: {line.strip()} ({why})")
        elif TOOL_LINE.search(line) or SESSION_LINE.search(line) or any(ai_email(e) for e in EMAIL.findall(line)):
            problems.append(f"an attribution line: {line.strip()}")
    for role, who in (("author", author), ("committer", committer)):
        why = identity_problem(who, team)
        if why:
            problems.append(f"the {role}: {why}")
    return problems


def ident(repo, var):
    """"Name <email>" of GIT_AUTHOR_IDENT or GIT_COMMITTER_IDENT, as this commit will record it (--author, -c user.*)."""
    return git(repo, "var", var).stdout.strip().rsplit(">", 1)[0] + ">"


def install(repo):
    """Write the four hooks; one that someone else wrote is left alone (returns the hooks refused)."""
    d = Path(git(repo, "rev-parse", "--git-path", "hooks").stdout.strip())
    d = d if d.is_absolute() else Path(repo) / d
    d.mkdir(parents=True, exist_ok=True)
    refused = []
    for name, text in HOOKS.items():
        h = d / name
        if h.exists() and not any(mark in h.read_text() for mark in OURS.get(name, ("path_check.py",))):
            refused.append(str(h))
            continue
        h.write_text(text)
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
    ap.add_argument("--install", action="store_true", help="write the pre-commit, pre-merge-commit, commit-msg and pre-push hooks")
    ap.add_argument("--commit-msg", metavar="FILE", help="the commit-msg hook: refuse AI attribution in FILE's message")
    a = ap.parse_args(argv)
    repo = git(a.repo, "rev-parse", "--show-toplevel").stdout.strip()
    if a.commit_msg:
        problems = attribution_problems(Path(a.commit_msg).read_text(errors="replace"),
                                        ident(repo, "GIT_AUTHOR_IDENT"), ident(repo, "GIT_COMMITTER_IDENT"),
                                        team_at_head(repo))
        for p in problems:
            print(f"commit-msg: refused: {p}", file=sys.stderr)
        if problems:
            print(TEAM_HELP, file=sys.stderr)
        return 1 if problems else 0
    if a.install:
        refused = install(repo)
        for h in refused:
            print(f"path check: {h} is someone else's hook; not overwritten (add this line to it: "
                  f"{HOOKS[Path(h).name].splitlines()[-1]})", file=sys.stderr)
        return 1 if refused else 0
    if a.range:
        branch = a.branch or branch_of(repo)
        outside = check_range(repo, a.range, branch)
        where = f"{a.range} (the {branch} list)"
    else:
        team = team_at_head(repo)
        bad = [f"the {role}: {why}" for role, var in (("author", "GIT_AUTHOR_IDENT"), ("committer", "GIT_COMMITTER_IDENT"))
               if (why := identity_problem(ident(repo, var), team))]
        if bad:
            for b in bad:
                print(f"identity check: refused: {b}", file=sys.stderr)
            print(TEAM_HELP, file=sys.stderr)
            return 1
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
