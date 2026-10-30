"""A data bundle per track for the Nov 3 handoff: produced data is gitignored, so a teammate taking over
a track gets it from this tar.gz (shared through ASU storage), not from GitHub.

  python tools/make_handoff_bundle.py --track B          # -> results/handoff/trackB_<date>.tar.gz + manifest
  python tools/make_handoff_bundle.py --track C --dry-run
  python tools/make_handoff_bundle.py --verify results/handoff/trackB_20261103.tar.gz

Each bundle holds the track's gitignored results (below), paths relative to cot-disclosure/, and a
manifest (MANIFEST.json inside, and a copy beside the tar.gz) with every file's bytes and sha256.
GPQA files (any path with "gpqa" in its name) are never included unless --include-gpqa is given, on
Ritik's say. Files still being written by a running job are bundled as they are at that moment; the
manifest records the time. --verify checks an unpacked or packed bundle against its manifest.
"""
import argparse
import hashlib
import io
import json
import re
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
OUT = CODE / "results" / "handoff"
TRACKS = {
    "A": ["results/trackA", "finetune/data"],
    "B": ["results/trackB", "results/voyager_canary.jsonl"],
    "C": ["results/trackC", "results/trackB/steered_cases.jsonl"],     # labels go to the raters directly (Oct 30)
}
GPQA = re.compile(r"gpqa", re.IGNORECASE)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def files_for(track, include_gpqa=False, root=CODE):
    """[(relative path, absolute path)] of the track's produced files, and the GPQA paths left out."""
    out, skipped = [], []
    for rel in TRACKS[track]:
        base = root / rel
        found = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file()) if base.exists() else []
        for p in found:
            r = str(p.relative_to(root))
            if GPQA.search(r) and not include_gpqa:
                skipped.append(r)
            else:
                out.append((r, p))
    return out, skipped


def build(track, include_gpqa=False, out_dir=OUT, root=CODE, stamp=None):
    files, skipped = files_for(track, include_gpqa, root)
    stamp = stamp or datetime.now().strftime("%Y%m%d")
    manifest = {"track": track, "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "root": "cot-disclosure/", "gpqa_included": include_gpqa, "gpqa_left_out": skipped,
                "files": [{"path": r, "bytes": p.stat().st_size, "sha256": sha256(p)} for r, p in files]}
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tar = out_dir / f"track{track}_{stamp}.tar.gz"
    if tar.exists():
        sys.exit(f"{tar} exists: bundles are never overwritten")
    with tarfile.open(tar, "w:gz") as t:
        for r, p in files:
            t.add(p, arcname=r)
        data = json.dumps(manifest, indent=1).encode()
        info = tarfile.TarInfo("MANIFEST.json")
        info.size = len(data)
        t.addfile(info, io.BytesIO(data))
    tar.with_suffix("").with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return tar, manifest


def verify(tar_path):
    """[problem] for a packed bundle: every file present with its manifest's sha256, and nothing extra."""
    problems = []
    with tarfile.open(tar_path, "r:gz") as t:
        manifest = json.load(t.extractfile("MANIFEST.json"))
        names = {m.name for m in t.getmembers() if m.isfile()} - {"MANIFEST.json"}
        want = {f["path"]: f for f in manifest["files"]}
        for path, f in want.items():
            if path not in names:
                problems.append(f"missing {path}")
                continue
            h = hashlib.sha256(t.extractfile(path).read()).hexdigest()
            if h != f["sha256"]:
                problems.append(f"different bytes: {path}")
        problems += [f"not in the manifest: {n}" for n in sorted(names - set(want))]
        if not manifest["gpqa_included"]:
            problems += [f"a GPQA file: {n}" for n in sorted(names) if GPQA.search(n)]
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--track", choices=sorted(TRACKS))
    ap.add_argument("--include-gpqa", action="store_true", help="only on Ritik's say")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify", metavar="TAR_GZ")
    a = ap.parse_args()
    if a.verify:
        problems = verify(a.verify)
        print("bundle matches its manifest" if not problems else "\n".join(problems))
        return 1 if problems else 0
    if not a.track:
        sys.exit("--track A, B or C")
    files, skipped = files_for(a.track, a.include_gpqa)
    total = sum(p.stat().st_size for _, p in files)
    print(f"track {a.track}: {len(files)} files, {total / 2 ** 20:.1f} MB from {', '.join(TRACKS[a.track])}"
          + (f"; GPQA files left out: {len(skipped)}" if skipped else ""))
    if a.dry_run:
        return 0
    tar, manifest = build(a.track, a.include_gpqa)
    print(f"wrote {tar.relative_to(CODE)} ({tar.stat().st_size / 2 ** 20:.1f} MB) and its manifest; "
          f"verify: {'ok' if not verify(tar) else 'FAILED'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
