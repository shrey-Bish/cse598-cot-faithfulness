"""The handoff bundles (tools/make_handoff_bundle.py): the track's files with a sha256 manifest, GPQA
left out unless asked, never overwritten, and a check that catches a changed file."""
import json
import sys
import tarfile
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "tools"))

import make_handoff_bundle as hb  # noqa: E402


def tree(root):
    for rel, text in {"results/trackB/voyager_runs.jsonl": "{}\n", "results/trackB/sub/x.jsonl.gz": "gz",
                      "results/trackB/gpqa_runs.jsonl": "secret\n", "results/voyager_canary.jsonl": "{}\n",
                      "results/trackC/team_live.jsonl": "{}\n", "results/trackB/steered_cases.jsonl": "{}\n"}.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)


def test_bundle_has_the_track_files_and_a_manifest_without_gpqa(tmp_path):
    tree(tmp_path)
    tar, manifest = hb.build("B", out_dir=tmp_path / "out", root=tmp_path, stamp="t")
    paths = {f["path"] for f in manifest["files"]}
    assert paths == {"results/trackB/voyager_runs.jsonl", "results/trackB/sub/x.jsonl.gz",
                     "results/trackB/steered_cases.jsonl", "results/voyager_canary.jsonl"}
    assert manifest["gpqa_left_out"] == ["results/trackB/gpqa_runs.jsonl"] and hb.verify(tar) == []
    assert json.loads((tmp_path / "out" / "trackB_t.manifest.json").read_text())["files"] == manifest["files"]
    with pytest.raises(SystemExit, match="never overwritten"):
        hb.build("B", out_dir=tmp_path / "out", root=tmp_path, stamp="t")
    c_tar, c = hb.build("C", out_dir=tmp_path / "out", root=tmp_path, stamp="t")
    assert {f["path"] for f in c["files"]} == {"results/trackC/team_live.jsonl", "results/trackB/steered_cases.jsonl"}


def test_gpqa_only_when_asked_and_verify_catches_changes(tmp_path):
    tree(tmp_path)
    _, m = hb.build("B", include_gpqa=True, out_dir=tmp_path / "out", root=tmp_path, stamp="g")
    assert "results/trackB/gpqa_runs.jsonl" in {f["path"] for f in m["files"]}
    tar, _ = hb.build("B", out_dir=tmp_path / "out2", root=tmp_path, stamp="t")
    bad = tmp_path / "bad.tar.gz"
    with tarfile.open(tar) as src, tarfile.open(bad, "w:gz") as dst:
        for mem in src.getmembers():
            data = src.extractfile(mem).read()
            if mem.name == "results/voyager_canary.jsonl":
                data = b"changed\n"
                mem.size = len(data)
            import io
            dst.addfile(mem, io.BytesIO(data))
    assert hb.verify(bad) == ["different bytes: results/voyager_canary.jsonl"]
