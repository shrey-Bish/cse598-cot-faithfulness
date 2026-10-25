"""No tracked file may grow past GitHub's 50 MB warning (a 100 MB file is refused on push). Large
per-probe data goes to .jsonl.gz files with a small summary beside them."""
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LIMIT = 50 * 2 ** 20


def test_no_tracked_file_is_over_50_mb():
    try:
        listed = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout")
    sizes = {p: (ROOT / p).stat().st_size for p in listed.decode().split("\0") if p and (ROOT / p).is_file()}
    big = {p: f"{s / 2 ** 20:.1f} MB" for p, s in sizes.items() if s > LIMIT}
    assert not big, f"tracked files over 50 MB: {big}"
