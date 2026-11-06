"""A data bundle per track for the Nov 3 handoff: produced data is gitignored, so a teammate taking over
a track gets it from this tar.gz (shared through ASU storage), not from GitHub.

  python tools/make_handoff_bundle.py --track B          # -> results/handoff/trackB_<date>.tar.gz + manifest
  python tools/make_handoff_bundle.py --track C --format zip    # (Nov 5) -> results/handoff/trackC_<date>.zip + manifest
  python tools/make_handoff_bundle.py --track C --dry-run
  python tools/make_handoff_bundle.py --verify results/handoff/trackB_20261103.tar.gz     # or a .zip

Each bundle holds the track's gitignored results (below), paths relative to cot-disclosure/, and a
manifest (MANIFEST.json inside, and a copy beside the tar.gz) with every file's bytes and sha256.
GPQA files (any path with "gpqa" in its name) are never included unless --include-gpqa is given, on
Ritik's say. Sol's records with text (results/trackB/b17/ and b20/ *.jsonl.gz) never travel: their logs keep them on
Sol and only the numbers-only files come back (Nov 4: two B20 smoke records had reached the Mac). Files still being written by a running job are bundled as they are at that moment; the
manifest records the time. --verify checks a packed bundle (.tar.gz, or .zip by its extension) against its manifest.
A zip (Nov 5, for ASU Drive) holds the same files and MANIFEST.json; tar.gz stays the default.
"""
import argparse
import hashlib
import io
import json
import re
import sys
import tarfile
import zipfile
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
SOL_RECORDS = re.compile(r"^results/trackB/b(17|20)/.*\.jsonl\.gz$")       # B17's and B20's text stays on Sol


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sol_records(track, root=CODE):
    """The Sol record files (with text) under the track's folders, which are never bundled."""
    return sorted(str(p.relative_to(root)) for rel in TRACKS[track] for p in ((root / rel).rglob("*.jsonl.gz")
                  if (root / rel).is_dir() else []) if SOL_RECORDS.match(str(p.relative_to(root))))


def files_for(track, include_gpqa=False, root=CODE):
    """[(relative path, absolute path)] of the track's produced files, and the GPQA paths left out. Sol's records
    with text (SOL_RECORDS) are left out too (sol_records lists them)."""
    out, skipped = [], []
    for rel in TRACKS[track]:
        base = root / rel
        found = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file()) if base.exists() else []
        for p in found:
            r = str(p.relative_to(root))
            if SOL_RECORDS.match(r):
                continue
            if GPQA.search(r) and not include_gpqa:
                skipped.append(r)
            else:
                out.append((r, p))
    return out, skipped


def build(track, include_gpqa=False, out_dir=OUT, root=CODE, stamp=None, fmt="tar.gz"):
    files, skipped = files_for(track, include_gpqa, root)
    stamp = stamp or datetime.now().strftime("%Y%m%d")
    manifest = {"track": track, "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "root": "cot-disclosure/", "gpqa_included": include_gpqa, "gpqa_left_out": skipped,
                "sol_records_left_out": sol_records(track, root),
                "files": [{"path": r, "bytes": p.stat().st_size, "sha256": sha256(p)} for r, p in files]}
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tar = out_dir / f"track{track}_{stamp}.{fmt}"
    beside = out_dir / f"track{track}_{stamp}.manifest.json"
    for p in (tar, beside):
        if p.exists():
            sys.exit(f"{p} exists: bundles are never overwritten")
    data = json.dumps(manifest, indent=1).encode()
    if fmt == "zip":
        with zipfile.ZipFile(tar, "w", zipfile.ZIP_DEFLATED) as z:
            for r, p in files:
                z.write(p, arcname=r)
            z.writestr("MANIFEST.json", data)
    else:
        with tarfile.open(tar, "w:gz") as t:
            for r, p in files:
                t.add(p, arcname=r)
            info = tarfile.TarInfo("MANIFEST.json")
            info.size = len(data)
            t.addfile(info, io.BytesIO(data))
    beside.write_text(json.dumps(manifest, indent=1) + "\n")
    return tar, manifest


def verify(tar_path):
    """[problem] for a packed bundle (a .zip by its extension, else a tar.gz): every file present with its manifest's
    sha256, and nothing extra. Files are read one at a time."""
    problems = []
    is_zip = str(tar_path).endswith(".zip")
    with (zipfile.ZipFile(tar_path) if is_zip else tarfile.open(tar_path, "r:gz")) as t:
        if is_zip:
            names, read = {i.filename for i in t.infolist() if not i.is_dir()}, t.read
        else:
            names, read = {m.name for m in t.getmembers() if m.isfile()}, lambda n: t.extractfile(n).read()
        manifest = json.loads(read("MANIFEST.json"))
        names -= {"MANIFEST.json"}
        want = {f["path"]: f for f in manifest["files"]}
        for path, f in want.items():
            if path not in names:
                problems.append(f"missing {path}")
                continue
            h = hashlib.sha256(read(path)).hexdigest()
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
    ap.add_argument("--format", choices=["tar.gz", "zip"], default="tar.gz", help="zip for ASU Drive (Nov 5)")
    ap.add_argument("--verify", metavar="BUNDLE", help="a .tar.gz, or a .zip")
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
          + (f"; GPQA files left out: {len(skipped)}" if skipped else "")
          + (f"; Sol records left out (they stay on Sol): {len(sol_records(a.track))}" if sol_records(a.track) else ""))
    if a.dry_run:
        return 0
    tar, manifest = build(a.track, a.include_gpqa, fmt=a.format)
    print(f"wrote {tar.relative_to(CODE)} ({tar.stat().st_size / 2 ** 20:.1f} MB) and its manifest; "
          f"verify: {'ok' if not verify(tar) else 'FAILED'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
