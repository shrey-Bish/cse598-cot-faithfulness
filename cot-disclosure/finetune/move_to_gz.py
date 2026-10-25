"""Move Track A files that store full replies to gzip (2026-10-25: no tracked file over 50 MB, no
LFS). Every record is kept unchanged and checked before the original is removed; base_format also
gets a one-row-per-record summary beside it. No calls.

  python finetune/move_to_gz.py --dry-run     # what would move, and the sizes
  python finetune/move_to_gz.py               # move
"""
import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import move_to_gz  # noqa: E402
from finetune import base_format as bf  # noqa: E402

RESULTS = CODE / "results" / "trackA"
MOVES = [  # (from, to, summary row, summary file)
    (RESULTS / "base_format.jsonl", bf.OUT, bf.summary_row, bf.RUNS_OUT),
    (RESULTS / "base_format_smoke.jsonl", RESULTS / "base_format_smoke.jsonl.gz", None, None),
    (RESULTS / "voyager_capabilities.jsonl", RESULTS / "voyager_capabilities.jsonl.gz", None, None),
    (RESULTS / "voyager_ids_check.jsonl", RESULTS / "voyager_ids_check.jsonl.gz", None, None),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    for src, dst, summary, summary_path in MOVES:
        if not src.exists():
            print(f"{src.name}: already moved" if dst.exists() else f"{src.name}: missing")
            continue
        size = src.stat().st_size / 2 ** 20
        if a.dry_run:
            print(f"{src.name} ({size:.1f} MB) -> {dst.name}" + (f" + {summary_path.name}" if summary else ""))
            continue
        n = move_to_gz(src, dst, summary, summary_path)
        print(f"{src.name} ({size:.1f} MB) -> {dst.name} ({dst.stat().st_size / 2 ** 20:.1f} MB), {n} records, "
              f"checked" + (f"; {summary_path.name} {summary_path.stat().st_size / 2 ** 20:.2f} MB" if summary else ""))


if __name__ == "__main__":
    main()
