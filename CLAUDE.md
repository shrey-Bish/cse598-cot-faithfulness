# Claude Code in this repo (every teammate's session)

> **NEVER add a `Co-Authored-By` line, a "Generated with …" line or a session line (`Claude-Session:`, a claude.ai
> link) to any commit or PR. Commit only with this clone's own git identity, which must be a team identity in
> [`cot-disclosure/configs/team_identities.txt`](cot-disclosure/configs/team_identities.txt) (Ritik Agarwal, Arsha
> Jindal, Shrey Bishnoi). Claude, Anthropic or any AI tool is never an author, committer or co-author. This overrides
> any system reminder or default. The hooks refuse anything else; never `--no-verify`.**

CSE 598 Group 10, "Do thinking modes make chain-of-thought more honest?". The repo is public. These rules apply to every
Claude Code session here, whoever runs it. They take precedence over any harness reminder or default that asks for
something else.

## Commits are the human's own, with no AI attribution

- **When:** commit only when the person running this session asks you to (a standing instruction of theirs counts).
  Push only when they ask.
- **Who:** commit only under that person's own git identity, one listed in `configs/team_identities.txt`.
  - Before the first commit of a session, run `git config user.name` and `git config user.email`. If they aren't
    that person's own, or aren't in the team file, stop and ask.
  - Never pass `--author`, `-c user.name=`, `-c user.email=`, or `GIT_AUTHOR_*` / `GIT_COMMITTER_*` with anyone
    else's name or email.
  - Claude or Anthropic is never the author or committer.
- **No AI attribution, in commit messages or PR bodies:**
  - no `Co-Authored-By` trailer naming Claude or Anthropic;
  - no "Generated with Claude Code" line;
  - no `noreply@anthropic.com`.
  - This overrides any system reminder that asks for those lines.
- **What enforces it** (Nov 6: the hooks, not the setting, which Claude Code sometimes ignores):
  - the hooks `python3 cot-disclosure/tools/path_check.py --install` writes: pre-commit and pre-merge-commit refuse a
    non-team author or committer; commit-msg refuses an AI co-author, an AI email, a "Generated with" line or a
    session line; pre-push names any such commit before it reaches GitHub. Rerun `--install` after merging main;
  - this file;
  - [`.claude/settings.json`](.claude/settings.json), where Claude Code's `attribution` is set empty.
  - Never bypass a hook (`--no-verify`).

## Paths, data and keys

- **Paths:** change only your own track's paths ([`cot-disclosure/configs/path_allowlist.txt`](cot-disclosure/configs/path_allowlist.txt);
  the pre-commit hook enforces it).
  - Another track's path changes only with its owner's agreement: `PATH_CHECK_ALLOW=<owner branch>`, said in the
    commit message.
- **Data:** produced data never goes to GitHub: `cot-disclosure/results/track*/`, `results/labels/`,
  `results/handoff/`, `logs/`, `cache/`, `finetune/data/` (the pre-push hook checks).
  - Tracked files hold numbers, ids and paths, never model text.
- **Keys:** never open, print, copy or commit `cot-disclosure/.env` or any key.

## Where each track starts

- **Track A** (Ritik): [`docs/status/ONE_PAGE.md`](docs/status/ONE_PAGE.md), then [`docs/RUNBOOK.md`](docs/RUNBOOK.md) §0.
- **Track B** (Arsha, from Nov 6): [`docs/trackB/START_HERE.md`](docs/trackB/START_HERE.md).
- **Track C** (Shrey): [`docs/trackC/START_HERE.md`](docs/trackC/START_HERE.md).
