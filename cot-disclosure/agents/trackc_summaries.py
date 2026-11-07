"""Track C: copy a reading's summary into the tracked, numbers-only folder (no calls).

  python agents/trackc_summaries.py c19_summary.json      # results/trackC/ -> results/summaries/trackC/

tools/export_summaries.py is shared code, so Track C's summaries from Nov 3 are exported here, with the same checks
(its `problems` and `question_starts`, imported read-only): a file with the start of a question in it, or a string over
its length limit, is refused and nothing is written. Afterwards `python tools/export_summaries.py --check` must end
with "results/summaries/: all numbers-only".
"""
import argparse
import shutil
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

from tools.export_summaries import problems, question_starts  # noqa: E402

SRC = CODE / "results" / "trackC"
DST = CODE / "results" / "summaries" / "trackC"


def export(name, src=SRC, dst=DST, starts=None):
    """Copy src/name to dst/name if it is numbers-only. Returns the reasons it was refused ([] if copied)."""
    path = Path(src) / name
    why = problems(path, question_starts() if starts is None else starts)
    if not why:
        Path(dst).mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, Path(dst) / name)
    return why


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("names", nargs="+", help="file names under results/trackC/, e.g. c19_summary.json")
    a = ap.parse_args(argv)
    starts, failed = question_starts(), False
    for name in a.names:
        why = export(name, starts=starts)
        failed = failed or bool(why)
        print(f"{'REFUSED' if why else 'copied'}: results/trackC/{name} -> results/summaries/trackC/{name}"
              + (f"  ({'; '.join(why)})" if why else ""))
    return not failed


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
