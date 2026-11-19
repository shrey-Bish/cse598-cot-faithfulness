"""tools/make_submission.py: the submission's pieces and their state, and the zip, built only once every piece the
team writes is written. Tests run on a throwaway git repo shaped like ours; nothing touches the real one."""
import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cot-disclosure" / "tools"))

import make_submission as ms  # noqa: E402

SHA = "a" * 64


def _git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)


def _write(root, rel, text="x\n", data=None):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if data is not None:
        p.write_bytes(data)
    else:
        p.write_text(text)
    return p


@pytest.fixture
def repo(tmp_path):
    """Everything the tools make is in place; the team's own parts are not (the placeholder contributions only)."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "T")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "remote", "add", "origin", "https://github.com/example/proj.git")
    _write(root, "docs/paper/figures/gate2.png", data=b"\x89PNG fake")
    _write(root, "docs/paper/figures/gate2.csv", "a,b\n1,2\n")
    _write(root, "docs/paper/figures/WAITING.md", "spec\n")
    _write(root, "docs/demo/index.html", "<title>x</title>\n")
    _write(root, "docs/paper/supplement/README.md", "supp\n")
    _write(root, "docs/submission/BUNDLES.sha256", f"{SHA}  trackA_20261118.tar.gz\n{'b' * 64}  trackB_20261118.tar.gz\n")
    _write(root, "docs/submission/CONTRIBUTIONS.md", f"# Contributions\n\n{ms.PLACEHOLDER}\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    _git(root, "tag", "-a", ms.TAG, "-m", "freeze")
    return root


def _team_parts(root):
    _write(root, "docs/submission/report.pdf", data=b"%PDF fake")
    _write(root, "docs/submission/slides.pptx", data=b"PK fake")
    _write(root, "docs/submission/CONTRIBUTIONS.md", "# Contributions\n\nRitik: Track A.\n")
    _write(root, "docs/submission/AI_USE.md", "# AI use\n\nClaude Code for code.\n")


def _states(root):
    return {p.name: p.state for p in ms.pieces(root)}


def test_check_lists_every_piece_and_marks_the_teams_parts_to_write(repo):
    states = _states(repo)
    assert set(states) == {"report", "slides", "contributions", "AI-use disclosure", "figures", "explainer",
                           "code link", "bundles' sha256s"}
    for name in ("report", "slides", "contributions", "AI-use disclosure"):
        assert states[name] == ms.TO_WRITE, name
    for name in ("figures", "explainer", "code link", "bundles' sha256s"):
        assert states[name] == ms.READY, name


def test_the_placeholder_and_unconfirmed_lines_are_not_written(repo):
    _team_parts(repo)
    _write(repo, "docs/submission/CONTRIBUTIONS.md", f"# Contributions\n\n{ms.PLACEHOLDER}\n")
    _write(repo, "docs/submission/AI_USE.md", "# AI use\n\n- Claude Code: *to confirm* from when.\n")
    states = _states(repo)
    assert states["contributions"] == ms.TO_WRITE
    assert states["AI-use disclosure"] == ms.TO_WRITE
    assert states["report"] == ms.READY


def test_two_report_files_are_refused_as_ambiguous(repo):
    _team_parts(repo)
    _write(repo, "docs/submission/report.docx", data=b"PK fake")
    piece = {p.name: p for p in ms.pieces(repo)}["report"]
    assert piece.state == ms.PROBLEM
    assert "report.docx" in piece.note and "report.pdf" in piece.note


def test_a_malformed_bundle_line_is_a_problem(repo):
    _write(repo, "docs/submission/BUNDLES.sha256", "not-a-hash  trackA.tar.gz\n")
    assert _states(repo)["bundles' sha256s"] == ms.PROBLEM


def test_the_build_refuses_while_a_team_part_is_missing_and_writes_nothing(repo, capsys):
    out = repo / "out" / "sub.zip"
    assert ms.main(["--root", str(repo), "--out", str(out)]) == 1
    text = capsys.readouterr().out
    assert "report" in text and "contributions" in text and "AI-use disclosure" in text and "slides" in text
    assert not out.exists()


def test_check_writes_nothing_and_exits_zero(repo, capsys):
    assert ms.main(["--root", str(repo), "--check"]) == 0
    text = capsys.readouterr().out
    assert ms.TO_WRITE in text and ms.READY in text
    assert not (repo / "cot-disclosure" / "results" / "submission").exists()


def test_the_zip_has_every_piece_once_the_team_parts_are_written(repo):
    _team_parts(repo)
    out = repo / "out" / "sub.zip"
    assert ms.main(["--root", str(repo), "--out", str(out)]) == 0
    with zipfile.ZipFile(out) as z:
        names = set(z.namelist())
        top = ms.TOP
        for rel in ("report.pdf", "slides.pptx", "CONTRIBUTIONS.md", "AI_USE.md", "figures/gate2.png",
                    "figures/gate2.csv", "explainer/index.html", "CODE_LINK.txt", "BUNDLES.sha256", "MANIFEST.sha256"):
            assert f"{top}/{rel}" in names, rel
        assert f"{top}/figures/WAITING.md" not in names          # a spec for the team, not a figure
        assert not any("/supplement/" in n for n in names)        # only with --with-supplement
        link = z.read(f"{top}/CODE_LINK.txt").decode()
        tag_commit = subprocess.run(["git", "-C", str(repo), "rev-list", "-n1", ms.TAG], capture_output=True,
                                    text=True, check=True).stdout.strip()
        assert "https://github.com/example/proj" in link and ".git\n" not in link
        assert ms.TAG in link and tag_commit in link
        manifest = z.read(f"{top}/MANIFEST.sha256").decode()
        pdf = z.read(f"{top}/report.pdf")
        assert f"{hashlib.sha256(pdf).hexdigest()}  report.pdf" in manifest
        assert z.read(f"{top}/BUNDLES.sha256").decode().startswith(SHA)


def test_the_supplement_goes_in_only_when_asked(repo):
    _team_parts(repo)
    out = repo / "out" / "sub.zip"
    assert ms.main(["--root", str(repo), "--out", str(out), "--with-supplement"]) == 0
    with zipfile.ZipFile(out) as z:
        assert f"{ms.TOP}/supplement/README.md" in z.namelist()


def test_two_builds_of_the_same_files_give_the_same_bytes(repo):
    _team_parts(repo)
    a, b = repo / "out" / "a.zip", repo / "out" / "b.zip"
    assert ms.main(["--root", str(repo), "--out", str(a)]) == 0
    assert ms.main(["--root", str(repo), "--out", str(b)]) == 0
    assert a.read_bytes() == b.read_bytes()


def test_verify_bundles_compares_local_bundles_to_the_recorded_hashes(repo, capsys):
    data = b"bundle bytes"
    _write(repo, "cot-disclosure/results/handoff/trackA_20261118.tar.gz", data=data)
    _write(repo, "docs/submission/BUNDLES.sha256",
           f"{hashlib.sha256(data).hexdigest()}  trackA_20261118.tar.gz\n{'b' * 64}  trackB_20261118.tar.gz\n")
    rows = dict(ms.verify_bundles(repo))
    assert rows == {"trackA_20261118.tar.gz": "matches", "trackB_20261118.tar.gz": "not on this machine"}


def test_the_real_folder_records_the_freeze_bundles_and_the_placeholder():
    """The tracked folder: three bundles' sha256s as the Nov 18 log gives them; the contribution placeholder."""
    lines = (ROOT / "docs/submission/BUNDLES.sha256").read_text().splitlines()
    assert [ln.split("  ")[1] for ln in lines] == [f"track{t}_20261118.tar.gz" for t in "ABC"]
    log = (ROOT / "archive/sessions/2026-11-18/2026-11-18_2044_ALL_freeze.md").read_text()
    for ln in lines:
        assert ln.split("  ")[0] in log, ln
    assert ms.PLACEHOLDER in (ROOT / "docs/submission/CONTRIBUTIONS.md").read_text()
