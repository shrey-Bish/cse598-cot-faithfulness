"""Zip the progress outputs for the assistant that builds the slides.

  python cot-disclosure/progress/make_bundle.py

Writes progress_bundle_<YYYYMMDD>.zip at the repo root (gitignored by the root
.gitignore's `/*` rule) with docs/progress/, presentation/progress/, a sanitized
copy of the session log, and results/progress/*.jsonl when they total under 25 MB
(otherwise the first 20 lines of each file plus a note).
"""
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from common import CODE, LOGS, OUT, REPO

LIMIT = 25 * 1024 * 1024
SECRET = re.compile(r"(Bearer\s+\S+|sk-[A-Za-z0-9_\-]{8,}|Authori[sz]ation[^\n]*)", re.IGNORECASE)


def secrets():
    env = CODE / ".env"
    vals = []
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and "KEY" in line.split("=", 1)[0]:
                v = line.split("=", 1)[1].strip()
                if v:
                    vals.append(v)
    return vals


def sanitize(text, vals):
    for v in vals:
        text = text.replace(v, "[REDACTED]")
    return SECRET.sub("[REDACTED]", text)


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = REPO / f"progress_bundle_{stamp}.zip"
    vals = secrets()
    jsonl = sorted(OUT.glob("*.jsonl"))
    total = sum(f.stat().st_size for f in jsonl)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for root in (REPO / "docs" / "progress", REPO / "presentation" / "progress"):
            for f in sorted(root.rglob("*")):
                if f.is_file() and f.name != ".DS_Store":
                    z.write(f, f.relative_to(REPO))
        for log in sorted(LOGS.glob("progress_*.log")):
            z.writestr(f"logs/{log.stem}.sanitized.log", sanitize(log.read_text(), vals))
        if total < LIMIT:
            for f in jsonl:
                z.write(f, f.relative_to(REPO))
            for f in sorted(OUT.glob("*.json")):
                z.write(f, f.relative_to(REPO))
        else:
            for f in jsonl:
                head = "".join(f.open().readlines()[:20])
                z.writestr(str(f.relative_to(REPO)).replace(".jsonl", ".sample20.jsonl"), head)
            z.writestr("results_NOTE.txt", f"results/progress/*.jsonl total {total / 1e6:.1f} MB > 25 MB: "
                                           "only the first 20 lines of each file are included.")
    print(f"wrote {path.name}: {path.stat().st_size / 1e6:.1f} MB; jsonl total {total / 1e6:.1f} MB "
          f"({'included' if total < LIMIT else 'sampled'})")


if __name__ == "__main__":
    main()
