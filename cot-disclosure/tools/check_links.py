"""Every internal markdown link in the tracked .md files points at a file or folder that exists, and every script a
RUNBOOK command runs exists (Oct 30, the cleanup). No network: web links aren't checked.

  python tools/check_links.py              # lists what's broken; exit 1 if anything is
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
SCRIPT = re.compile(r"(?:python3?|\.venv/bin/python|bash|sh)\s+(?:-u\s+)?((?:\.\./)?[\w./-]+\.(?:py|sh))")


def tracked_md(root=ROOT):
    out = subprocess.run(["git", "ls-files", "*.md"], cwd=root, capture_output=True, text=True).stdout.split("\n")
    return [root / f for f in out if f]


def broken_links(root, files):
    """[(file, target)] for every relative link whose target doesn't exist (anchors ignored)."""
    out = []
    for f in files:
        for target in LINK.findall(f.read_text(errors="ignore")):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            path = target.split("#")[0]
            if path and not (f.parent / path).exists():
                out.append((f, target))
    return out


def missing_scripts(root, runbook):
    """Scripts a RUNBOOK command runs that exist neither from the repo root nor from cot-disclosure/."""
    out = []
    for s in SCRIPT.findall(runbook.read_text(errors="ignore")):
        rel = s[3:] if s.startswith("../") else s
        if not any((base / rel).exists() for base in (root, root / "cot-disclosure")) and s not in out:
            out.append(s)
    return out


def main():
    broken = broken_links(ROOT, tracked_md())
    for f, t in broken:
        print(f"broken link: {f.relative_to(ROOT)} -> {t}")
    missing = missing_scripts(ROOT, ROOT / "docs" / "RUNBOOK.md")
    for s in missing:
        print(f"RUNBOOK runs a missing script: {s}")
    print(f"{len(broken)} broken links, {len(missing)} missing RUNBOOK scripts")
    return 1 if broken or missing else 0


if __name__ == "__main__":
    sys.exit(main())
