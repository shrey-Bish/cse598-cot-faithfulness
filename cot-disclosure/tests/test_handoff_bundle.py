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
    (tmp_path / "results" / "labels" / "gate3").mkdir(parents=True)               # Track A's label sample: not Track C's
    (tmp_path / "results" / "labels" / "gate3" / "label_sample.csv").write_text("row\n")
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


def test_b20s_sol_records_with_text_never_travel_only_its_numbers_only_files(tmp_path):
    """B20's log (§3): its records stay on Sol, and only the numbers-only files come back. If a record file reaches the
    Mac anyway (Nov 4: the two smokes' b20_sol_vllm.jsonl.gz), Track B's bundle leaves it out and says so."""
    tree(tmp_path)
    for rel in ("results/trackB/b20/granite-4.2-8b/b20_sol_vllm.jsonl.gz", "results/trackB/b20/granite-4.2-8b/b20_flags.jsonl",
                "results/trackB/b20/granite-4.2-8b/smoke_check.json", "results/trackB/b17/b17_sol_vllm.jsonl.gz"):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")
    tar, manifest = hb.build("B", out_dir=tmp_path / "out", root=tmp_path, stamp="t")
    paths = {f["path"] for f in manifest["files"]}
    assert "results/trackB/b20/granite-4.2-8b/b20_flags.jsonl" in paths and "results/trackB/b20/granite-4.2-8b/smoke_check.json" in paths
    assert not any(p.endswith("_sol_vllm.jsonl.gz") for p in paths)
    assert manifest["sol_records_left_out"] == ["results/trackB/b17/b17_sol_vllm.jsonl.gz",
                                                "results/trackB/b20/granite-4.2-8b/b20_sol_vllm.jsonl.gz"]
    assert "results/trackB/sub/x.jsonl.gz" in paths                       # Voyager's records still travel


def test_a_zip_bundle_holds_the_same_files_and_manifest_and_verifies(tmp_path):
    """Nov 5: Track C's bundle goes to ASU Drive as a zip (--format zip); tar.gz stays the default."""
    import zipfile
    tree(tmp_path)
    z, manifest = hb.build("C", out_dir=tmp_path / "out", root=tmp_path, stamp="t", fmt="zip")
    assert z == tmp_path / "out" / "trackC_t.zip" and zipfile.is_zipfile(z)
    with zipfile.ZipFile(z) as f:
        assert set(f.namelist()) == {"MANIFEST.json", "results/trackC/team_live.jsonl", "results/trackB/steered_cases.jsonl"}
        assert json.loads(f.read("MANIFEST.json"))["files"] == manifest["files"]
    assert json.loads((tmp_path / "out" / "trackC_t.manifest.json").read_text())["files"] == manifest["files"]
    assert hb.verify(z) == [] and hb.verify(str(z)) == []
    with pytest.raises(SystemExit, match="never overwritten"):
        hb.build("C", out_dir=tmp_path / "out", root=tmp_path, stamp="t", fmt="zip")
    with pytest.raises(SystemExit, match="never overwritten"):                  # nor its manifest, by a tar.gz that day
        hb.build("C", out_dir=tmp_path / "out", root=tmp_path, stamp="t")
    t, _ = hb.build("C", out_dir=tmp_path / "tgz", root=tmp_path, stamp="t")   # the default is unchanged
    assert t.name == "trackC_t.tar.gz" and tarfile.is_tarfile(t) and hb.verify(t) == []
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(z) as src, zipfile.ZipFile(bad, "w") as dst:
        for name in src.namelist():
            dst.writestr(name, b"changed\n" if name == "results/trackC/team_live.jsonl" else src.read(name))
        dst.writestr("results/trackC/extra.jsonl", b"{}\n")
    assert hb.verify(bad) == ["different bytes: results/trackC/team_live.jsonl", "not in the manifest: results/trackC/extra.jsonl"]
