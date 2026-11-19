"""The submission zip, in one command, once the team's own parts are written (Nov 19).

  python3 cot-disclosure/tools/make_submission.py --check            # each piece and its state; writes nothing
  python3 cot-disclosure/tools/make_submission.py                    # the zip (refuses, naming what's missing)
  python3 cot-disclosure/tools/make_submission.py --with-supplement  # the same, with docs/paper/supplement/
  python3 cot-disclosure/tools/make_submission.py --verify-bundles   # the local bundles against BUNDLES.sha256

The pieces (docs/submission/README.md lists them with their owners):
  - written by us: docs/submission/report.(pdf|docx), docs/submission/slides.(pptx|pdf) (from the shell
    docs/presentation/deck.pptx), docs/submission/CONTRIBUTIONS.md (not while it holds the placeholder),
    docs/submission/AI_USE.md (not while a line says "to confirm");
  - made by the repo: the figures (docs/paper/figures/*.png, *.svg, *.csv), the explainer (docs/demo/index.html),
    the code link (origin's URL, the freeze tag and its commit, main's commit at the build), the bundles' sha256s
    (docs/submission/BUNDLES.sha256, from the Nov 18 freeze log).
The zip goes to cot-disclosure/results/submission/ (gitignored), with MANIFEST.sha256 (every file's sha256). Its
entries are sorted and dated at the freeze, so the same files give the same bytes. Stdlib only.
"""
import argparse
import hashlib
import re
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAG = "results-freeze-2026-11-18"
TOP = "cse598_group10"
OUT = Path("cot-disclosure/results/submission/cse598_group10_submission.zip")
SUB = Path("docs/submission")
PLACEHOLDER = "Contributions: to be completed before submission"
STAMP = (2026, 11, 18, 21, 4, 0)                     # the freeze tag's time: every zip entry carries it
READY, TO_WRITE, PROBLEM = "ready", "to write by us", "problem"
FIGURE_KINDS = (".png", ".svg", ".csv")
BUNDLE_LINE = re.compile(r"^[0-9a-f]{64}  \S+$")


@dataclass
class Piece:
    name: str
    state: str
    note: str
    files: list = field(default_factory=list)        # [(path on disk, path in the zip under TOP)]


def _git(root, *args):
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def _one_of(root, stem, kinds, name, made_from):
    found = [root / SUB / f"{stem}.{k}" for k in kinds if (root / SUB / f"{stem}.{k}").is_file()]
    if not found:
        return Piece(name, TO_WRITE, f"{SUB}/{stem}.({'|'.join(kinds)}), {made_from}")
    if len(found) > 1:
        return Piece(name, PROBLEM, "more than one: " + ", ".join(p.name for p in found) + "; keep one")
    return Piece(name, READY, str(found[0].relative_to(root)), [(found[0], found[0].name)])


def _team_md(root, fname, name, not_yet, made_from):
    p = root / SUB / fname
    if not p.is_file():
        return Piece(name, TO_WRITE, f"{SUB}/{fname}, {made_from}")
    text = p.read_text(encoding="utf-8")
    if not_yet.lower() in text.lower():
        return Piece(name, TO_WRITE, f"{SUB}/{fname} still says \"{not_yet}\"")
    return Piece(name, READY, f"{SUB}/{fname}", [(p, fname)])


def code_link(root):
    url = _git(root, "remote", "get-url", "origin")
    tag_commit = _git(root, "rev-list", "-n1", TAG)
    head = _git(root, "rev-parse", "HEAD")
    if not url or not tag_commit:
        return None
    url = re.sub(r"\.git$", "", url)
    return (f"code: {url}\n"
            f"results frozen at: the tag {TAG}, commit {tag_commit}\n"
            f"the frozen tree: {url}/tree/{TAG}\n"
            f"main at this build: commit {head}\n"
            f"produced data stays local (gitignored); its bundles' sha256s: BUNDLES.sha256\n")


def pieces(root=ROOT, with_supplement=False):
    root = Path(root)
    out = [
        _one_of(root, "report", ("pdf", "docx"), "report", "written from docs/paper/REPORT.md's bullets"),
        _one_of(root, "slides", ("pptx", "pdf"), "slides", "finished from the shell docs/presentation/deck.pptx"),
        _team_md(root, "CONTRIBUTIONS.md", "contributions", PLACEHOLDER, "written by us"),
        _team_md(root, "AI_USE.md", "AI-use disclosure", "to confirm", "written from AI_USE_INVENTORY.md"),
    ]
    figs = sorted(p for p in (root / "docs/paper/figures").glob("*") if p.suffix in FIGURE_KINDS)
    out.append(Piece("figures", READY if any(p.suffix == ".png" for p in figs) else PROBLEM,
                     f"docs/paper/figures/: {len(figs)} files (png, svg, csv)",
                     [(p, f"figures/{p.name}") for p in figs]))
    page = root / "docs/demo/index.html"
    out.append(Piece("explainer", READY if page.is_file() else PROBLEM, "docs/demo/index.html",
                     [(page, "explainer/index.html")] if page.is_file() else []))
    link = code_link(root)
    out.append(Piece("code link", READY if link else PROBLEM,
                     f"origin, the tag {TAG}" if link else f"no origin remote or no tag {TAG}",
                     [(link, "CODE_LINK.txt")] if link else []))
    sums = root / SUB / "BUNDLES.sha256"
    lines = sums.read_text().splitlines() if sums.is_file() else []
    ok = bool(lines) and all(BUNDLE_LINE.match(ln) for ln in lines)
    out.append(Piece("bundles' sha256s", READY if ok else PROBLEM,
                     f"{SUB}/BUNDLES.sha256: {len(lines)} bundles" if ok else f"{SUB}/BUNDLES.sha256 missing or malformed",
                     [(sums, "BUNDLES.sha256")] if ok else []))
    if with_supplement:
        sup = root / "docs/paper/supplement"
        files = sorted(p for p in sup.rglob("*") if p.is_file())
        out.append(Piece("supplement", READY if files else PROBLEM, f"docs/paper/supplement/: {len(files)} files",
                         [(p, "supplement/" + p.relative_to(sup).as_posix()) for p in files]))
    return out


def _bytes(src):
    return src.encode("utf-8") if isinstance(src, str) else Path(src).read_bytes()


def build(root, out, with_supplement=False):
    entries = {}
    for piece in pieces(root, with_supplement):
        for src, arc in piece.files:
            entries[arc] = _bytes(src)
    entries["MANIFEST.sha256"] = "".join(f"{hashlib.sha256(b).hexdigest()}  {a}\n"
                                         for a, b in sorted(entries.items())).encode()
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for arc in sorted(entries):
            info = zipfile.ZipInfo(f"{TOP}/{arc}", date_time=STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, entries[arc])
    return sorted(entries)


def verify_bundles(root=ROOT):
    root = Path(root)
    rows = []
    for ln in (root / SUB / "BUNDLES.sha256").read_text().splitlines():
        want, name = ln.split("  ", 1)
        p = root / "cot-disclosure/results/handoff" / name
        if not p.is_file():
            rows.append((name, "not on this machine"))
            continue
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        rows.append((name, "matches" if h.hexdigest() == want else "DIFFERS"))
    return rows


def _table(ps):
    w = max(len(p.name) for p in ps)
    return "\n".join(f"  {p.name:<{w}}  {p.state:<14}  {p.note}" for p in ps)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--out", default=None, help=f"default: {OUT}")
    ap.add_argument("--check", action="store_true", help="list each piece and its state; write nothing")
    ap.add_argument("--with-supplement", action="store_true")
    ap.add_argument("--verify-bundles", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root)
    if a.verify_bundles:
        rows = verify_bundles(root)
        for name, state in rows:
            print(f"  {name}: {state}")
        return 1 if any(s == "DIFFERS" for _n, s in rows) else 0
    ps = pieces(root, a.with_supplement)
    print("The submission's pieces:\n" + _table(ps))
    if a.check:
        return 0
    missing = [p for p in ps if p.state != READY]
    if missing:
        print("\nNo zip written. Not ready: " + "; ".join(f"{p.name} ({p.state})" for p in missing))
        return 1
    out = Path(a.out) if a.out else root / OUT
    names = build(root, out, a.with_supplement)
    print(f"\nWrote {out} ({len(names)} files, {out.stat().st_size / 2 ** 20:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
