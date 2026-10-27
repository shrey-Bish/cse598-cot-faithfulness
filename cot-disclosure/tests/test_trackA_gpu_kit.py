"""The Sol GPU kit (finetune/gpu/): the smoke run on a tiny random Olmo 3 model on CPU, the offline
snapshot check against d97e442, and the account guards in the Sol scripts. No GPU, no network."""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
SOL = CODE / "finetune" / "gpu" / "sol"
ACCOUNT = "class_cse59888883fall2026"

from finetune.gpu import kit  # noqa: E402
from _tiny_olmo import tiny_model_dir  # noqa: E402



def test_smoke_on_a_tiny_model(tmp_path):
    from finetune.gpu import smoke
    d = tiny_model_dir(tmp_path)
    res = smoke.main(["--model", str(d), "--device", "cpu", "--dtype", "fp32", "--new-tokens", "4",
                      "--out", str(tmp_path / "out")])
    saved = json.loads((tmp_path / "out" / "smoke" / "smoke.json").read_text())
    assert saved["generated_tokens"] == 4 and saved["prompt"].endswith("<|im_start|>assistant\n<think>")
    assert saved["template_renders_same"] is True                 # the snapshot's template = ours, no tool turn
    assert saved["snapshot_commit"] == "local:tiny-olmo3" and saved["snapshot_is_d97e442"] is False
    c = saved["config"]
    assert (c["num_hidden_layers"], c["num_key_value_heads"], c["sliding_window"]) == (4, 4, 8)
    assert c["layer_types"] == {"full_attention": 1, "sliding_attention": 3} and c["full_attention_layers"] == [3]
    assert c["tie_word_embeddings"] is False and saved["versions"]["torch"] == res["versions"]["torch"]


def test_smoke_dry_run_loads_nothing(tmp_path, capsys):
    from finetune.gpu import smoke
    d = tiny_model_dir(tmp_path)
    assert smoke.main(["--model", str(d), "--device", "cpu", "--dry-run"]) is None
    assert "memory: needs" in capsys.readouterr().out
    assert not (tmp_path / "out").exists()


def test_memory_check_refuses(monkeypatch):
    torch = pytest.importorskip("torch")
    monkeypatch.setattr(kit, "free_bytes", lambda device: 10 * kit.GiB)
    with pytest.raises(SystemExit, match="refusing to start"):
        kit.check_memory(torch.device("cpu"), 15 * kit.GiB, "Olmo 3 7B Think in bf16")
    assert kit.check_memory(torch.device("cpu"), 2 * kit.GiB, "x") == (2 * kit.GiB, 10 * kit.GiB)


# ---------------------------------------------------------------- snapshot against d97e442
def fake_cache(tmp_path, rev, overrides=None):
    """A Hugging Face cache layout: snapshots/<rev>/<file> -> ../../blobs/<hash>."""
    ref = json.loads(kit.REV_FILES.read_text())["files"]
    root = tmp_path / "models--allenai--Olmo-3-7B-Think"
    snap, blobs = root / "snapshots" / rev, root / "blobs"
    snap.mkdir(parents=True)
    blobs.mkdir(exist_ok=True)
    for name, h in {**ref, **(overrides or {})}.items():
        (blobs / h).write_text("x")
        (snap / name).symlink_to(Path("..") / ".." / "blobs" / h)
    return snap


def test_snapshot_files_match_d97e442(tmp_path):
    snap = fake_cache(tmp_path, kit.TEMPLATE_REV)
    path, commit = kit.snapshot(str(snap))
    s = kit.describe_snapshot(path, commit)
    assert commit == kit.TEMPLATE_REV and s["snapshot_is_d97e442"] and s["files_vs_d97e442"]["same"]
    assert "matches d97e442" in kit.snapshot_line(s)


def test_snapshot_other_revision_same_weights(tmp_path):
    snap = fake_cache(tmp_path, "7c991fde2671813ab41745054310f60a610b0fac", {"config.json": "0" * 40})
    s = kit.describe_snapshot(*kit.snapshot(str(snap)))
    r = s["files_vs_d97e442"]
    assert not s["snapshot_is_d97e442"] and not r["same"] and r["weights_same"] and r["differ"] == ["config.json"]
    assert "weights equal" in kit.snapshot_line(s)


def test_snapshot_different_weights(tmp_path):
    snap = fake_cache(tmp_path, "64dab40", {"model-00002-of-00003.safetensors": "f" * 64})
    r = kit.files_vs_template_rev(snap)
    assert not r["weights_same"] and r["differ"] == ["model-00002-of-00003.safetensors"]


def test_regular_files_are_hashed_once(tmp_path, monkeypatch):
    """Sol's snapshot holds regular files, not cache links: they are hashed (sha256 for the weights,
    the git blob id for the rest) and the result is kept, keyed by path, size and mtime."""
    snap = tmp_path / "snapshots" / kit.TEMPLATE_REV
    snap.mkdir(parents=True)
    (snap / "config.json").write_text('{"x": 1}\n')
    (snap / "model-00001-of-00001.safetensors").write_bytes(b"\x00weights" * 1000)
    blob = subprocess.run(["git", "hash-object", str(snap / "config.json")], capture_output=True, text=True).stdout.strip()
    assert kit.git_blob_id(snap / "config.json") == blob
    ref = {"revision": kit.TEMPLATE_REV, "revisions_with_these_weights": [kit.TEMPLATE_REV],
           "files": {"config.json": blob, "model-00001-of-00001.safetensors": kit.sha256(snap / "model-00001-of-00001.safetensors")}}
    cache = tmp_path / "file_hashes.json"
    r = kit.files_vs_template_rev(snap, ref, cache)
    assert r["same"] and r["weights_same"] and sorted(r["hashed_regular_files"]) == sorted(ref["files"])
    monkeypatch.setattr(kit, "sha256", lambda p: pytest.fail("hashed again"))
    assert kit.files_vs_template_rev(snap, ref, cache)["weights_same"]                     # from the cache
    monkeypatch.undo()
    (snap / "model-00001-of-00001.safetensors").write_bytes(b"\x01other" * 1000)
    r = kit.files_vs_template_rev(snap, ref, cache)
    assert not r["weights_same"] and r["differ"] == ["model-00001-of-00001.safetensors"]
    assert "weights DIFFER" in kit.snapshot_line({"snapshot_commit": kit.TEMPLATE_REV, "snapshot_is_d97e442": True,
                                                  "files_vs_d97e442": r})


def test_reference_lists_the_weights():
    ref = json.loads(kit.REV_FILES.read_text())
    assert ref["revision"] == kit.TEMPLATE_REV
    weights = [n for n in ref["files"] if n.endswith(".safetensors")]
    assert len(weights) == 3 and all(re.fullmatch(r"[0-9a-f]{64}", ref["files"][n]) for n in weights)
    assert kit.TEMPLATE_REV in ref["revisions_with_these_weights"]


# ---------------------------------------------------------------- inputs
def test_inputs_manifest_matches_the_committed_files():
    manifest = json.loads(kit.INPUTS.read_text())
    assert set(manifest) == set(kit.NEEDED)
    for step in kit.NEEDED:
        assert [r["path"] for r in manifest[step]] == kit.NEEDED[step]
        kit.check_inputs(step)                               # the same bytes as committed


def test_check_inputs_catches_a_changed_file(tmp_path, monkeypatch):
    bad = tmp_path / "inputs.json"
    bad.write_text(json.dumps({"step8": [{"path": "configs/canary/olmo3-7b-think.json", "bytes": 1,
                                          "sha256": "0" * 64}]}))
    monkeypatch.setattr(kit, "INPUTS", bad)
    with pytest.raises(SystemExit, match="different bytes"):
        kit.check_inputs("step8")


# ---------------------------------------------------------------- Sol scripts: the course account only
def sbatch_options(path):
    return [line.split(None, 1)[1].strip() for line in path.read_text().splitlines() if line.startswith("#SBATCH")]


def minutes(t):
    days, _, hms = t.rpartition("-")
    h, m, s = (int(x) for x in hms.split(":"))
    return int(days or 0) * 1440 + h * 60 + m + s / 60


@pytest.mark.parametrize("script", sorted(SOL.glob("*.sbatch")), ids=lambda p: p.name)
def test_every_job_script_uses_the_course_account_within_limits(script):
    opts = sbatch_options(script)
    accounts = [o for o in opts if o.startswith(("-A", "--account"))]
    assert accounts == [f"-A {ACCOUNT}"]
    qos = next(o.split()[1] for o in opts if o.startswith("-q "))
    t = minutes(next(o.split()[1] for o in opts if o.startswith("-t ")))
    if qos == "debug":
        assert t <= 15
    elif qos == "class":                                       # class QoS: <= 4 GPUs, 32 cores, 320 GB; we cap at 16 h
        assert t <= 16 * 60
        assert int(next(o.split()[1] for o in opts if o.startswith("-c "))) <= 32
        assert int(next(o.split("=")[1].rstrip("G") for o in opts if o.startswith("--mem="))) <= 320
    gpus = [o for o in opts if o.startswith("-G ")]
    assert gpus in ([], ["-G a100:1"])
    assert "run.sh" in script.read_text() or "setup_env.sh" in script.read_text()


def fake_sbatch(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "sbatch_args"
    (bin_dir / "sbatch").write_text(f'#!/bin/bash\necho "$@" > {log}\necho "Submitted batch job 1"\n')
    (bin_dir / "sbatch").chmod(0o755)
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}", "TRACKA_SLURM_LOGS": str(tmp_path / "logs"),
           "SBATCH_ACCOUNT": "grp_hdavulcu"}
    return env, log


def submit(env, *args, script=SOL / "submit.sh"):
    return subprocess.run(["bash", str(script), *args], env=env, capture_output=True, text=True)


def test_submit_uses_the_course_account(tmp_path):
    env, log = fake_sbatch(tmp_path)
    r = submit(env, "smoke")
    assert r.returncode == 0, r.stderr
    args = log.read_text().split()
    assert args[:2] == ["-A", ACCOUNT] and args[-1].endswith("smoke.sbatch")   # beats SBATCH_ACCOUNT in the env


@pytest.mark.parametrize("extra", [["-A", "grp_hdavulcu"], ["-Agrp_hdavulcu"], ["--account=grp_hdavulcu"],
                                   ["--account", ACCOUNT]])
def test_submit_refuses_an_account_on_the_command_line(tmp_path, extra):
    env, log = fake_sbatch(tmp_path)
    r = submit(env, "smoke", *extra)
    assert r.returncode == 1 and "refusing" in r.stderr and not log.exists()


def test_submit_refuses_a_script_with_another_account(tmp_path):
    env, log = fake_sbatch(tmp_path)
    sol = tmp_path / "repo" / "cot-disclosure" / "finetune" / "gpu" / "sol"
    sol.mkdir(parents=True)
    for f in ("submit.sh", "guard.sh", "accounts.conf"):
        shutil.copy(SOL / f, sol / f)
    (sol / "lab.sbatch").write_text((SOL / "smoke.sbatch").read_text().replace(ACCOUNT, "grp_hdavulcu"))
    r = submit(env, "lab", script=sol / "submit.sh")
    assert r.returncode == 1 and "must set exactly" in r.stderr and not log.exists()


def fake_queue(tmp_path, env, lines):
    """A fake squeue printing these lines (id state time-left time-limit gres end-time)."""
    (tmp_path / "bin" / "squeue").write_text("#!/bin/bash\ncat <<'EOF'\n" + "".join(x + "\n" for x in lines) + "EOF\n")
    (tmp_path / "bin" / "squeue").chmod(0o755)
    return env


def sbatch_args(log):
    return log.read_text().split()


def test_the_estimate_sets_the_limit_and_job_arguments_pass_through(tmp_path):
    env, log = fake_sbatch(tmp_path)
    r = submit(fake_queue(tmp_path, env, []), "step9", "--estimate", "3", "--", "--followup")
    assert r.returncode == 0, r.stderr
    args = sbatch_args(log)
    assert args[:4] == ["-A", ACCOUNT, "-t", "4:00:00"] and args[-2].endswith("step9.sbatch") and args[-1] == "--followup"
    assert "QoS check: this job 4:00:00 x 1 GPU = 240 GPU-minutes" in r.stdout
    submit(env, "step9", "--estimate", "6")
    assert sbatch_args(log)[3] == "8:00:00"                    # 6 h x 1.3 = 7.8 h -> 8:00
    submit(env, "step9")
    assert sbatch_args(log)[3] == "2:00:00"                    # the script's own -t


def test_a_job_over_the_gpu_minute_limit_is_refused(tmp_path):
    env, log = fake_sbatch(tmp_path)
    r = submit(env, "step9", "--estimate", "13")               # 13 x 1.3 = 16.9 h -> 17:00 = 1,020 GPU-minutes
    assert r.returncode == 1 and "DenyOnLimit" in r.stderr and "1020 GPU-minutes" in r.stderr and not log.exists()


def test_running_and_pending_jobs_are_counted(tmp_path):
    env, log = fake_sbatch(tmp_path)
    fake_queue(tmp_path, env, ["101 RUNNING 5:00:00 8:00:00 gres/gpu:a100:1 2026-10-29T18:00:00"])
    r = submit(env, "step9", "--estimate", "6")                # 300 left + 480 = 780 of 960
    assert r.returncode == 0 and "total 780 of 960" in r.stdout and "WARNING" not in r.stdout
    fake_queue(tmp_path, env, ["101 RUNNING 7:00:00 8:00:00 gres/gpu:a100:1 2026-10-29T18:00:00",
                               "102 RUNNING 6:00:00 8:00:00 N/A 2026-10-29T17:00:00"])
    r = submit(env, "step9", "--estimate", "6")                # 420 + 360 + 480 = 1,260
    assert r.returncode == 0 and "both slots are taken" in r.stdout and "job 102 ends (2026-10-29T17:00:00)" in r.stdout
    assert "over the 960 GPU-minute limit by 300" in r.stdout and "about 150 min" in r.stdout
    fake_queue(tmp_path, env, [f"{i} PENDING 0:00 1:00:00 N/A N/A" for i in range(10)])
    r = submit(env, "step9")
    assert r.returncode == 1 and "more than 10 jobs" in r.stdout


def test_only_listed_accounts(tmp_path):
    env, log = fake_sbatch(tmp_path)
    r = submit({**env, "TRACKA_SUBMIT_ACCOUNT": "grp_hdavulcu"}, "smoke")
    assert r.returncode == 1 and "not listed" in r.stderr and not log.exists()
    conf = (SOL / "accounts.conf").read_text()
    rows = [line.split() for line in conf.splitlines() if line.strip() and not line.startswith("#")]
    assert rows == [[ACCOUNT, "public", "class", "960", "2", "10", "24", "4"]]


@pytest.mark.parametrize("env_vars,ok", [({"SLURM_JOB_ID": "5", "SLURM_JOB_ACCOUNT": ACCOUNT}, True),
                                         ({"SLURM_JOB_ID": "5", "SLURM_JOB_ACCOUNT": "grp_hdavulcu"}, False),
                                         ({}, False)])
def test_runs_only_inside_a_job_under_the_course_account(env_vars, ok):
    env = {k: v for k, v in os.environ.items() if not k.startswith("SLURM_")}
    r = subprocess.run(["bash", "-c", f"source {SOL / 'guard.sh'} && tracka_require_job"], env={**env, **env_vars},
                       capture_output=True, text=True)
    assert (r.returncode == 0) is ok, r.stderr


def test_shell_scripts_parse():
    for f in list(SOL.glob("*.sh")) + list(SOL.glob("*.sbatch")):
        assert subprocess.run(["bash", "-n", str(f)], capture_output=True).returncode == 0, f.name


def test_sol_scripts_call_the_env_python_by_full_path():
    """No bare python or python3 in a Sol script (after an rsync or a changed PATH it can be the
    system 3.6.8): Python is always "$TRACKA_PY", the project environment's own."""
    import re
    assert "TRACKA_PY=$TRACKA_ENV/bin/python\n" in (SOL / "env.sh").read_text()
    assert "TRACKA_ENV=/scratch/ragarw68/envs/olmo " in (SOL / "env.sh").read_text()
    bare = re.compile(r'(?<![\w/$"{.-])python3?(?![\w.-])')
    for f in list(SOL.glob("*.sh")) + list(SOL.glob("*.sbatch")):
        for i, line in enumerate(f.read_text().splitlines(), 1):
            code = line.split("#", 1)[0] if not line.lstrip().startswith("#") else ""
            assert not bare.search(code), f"{f.name}:{i}: {line.strip()}"
