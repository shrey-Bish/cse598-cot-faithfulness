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


# ---------------------------------------------------------------- a tiny model with the real tokenizer
def olmo_tokenizer_dir():
    try:
        p, _ = kit.snapshot()
    except Exception:                                    # noqa: BLE001
        pytest.skip("the Olmo 3 tokenizer is not in the local Hugging Face cache")
    if not (p / "tokenizer.json").exists():
        pytest.skip("the Olmo 3 tokenizer is not in the local Hugging Face cache")
    return p


def tiny_model_dir(tmp_path, layers=4, window=8, seed=0):
    """A random Olmo 3 model with the real vocabulary (so real prompts tokenize), saved with the
    tokenizer and chat template of the cached snapshot."""
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    src = olmo_tokenizer_dir()
    torch.manual_seed(seed)
    kinds = ["sliding_attention", "sliding_attention", "sliding_attention", "full_attention"] * (layers // 4)
    cfg = transformers.Olmo3Config(vocab_size=100278, hidden_size=32, intermediate_size=64, num_hidden_layers=layers,
                                   num_attention_heads=4, num_key_value_heads=4, max_position_embeddings=4096,
                                   sliding_window=window, layer_types=kinds, tie_word_embeddings=False,
                                   pad_token_id=100277, eos_token_id=100257)
    model = transformers.Olmo3ForCausalLM(cfg).eval()
    d = tmp_path / "tiny-olmo3"
    model.save_pretrained(d)
    for f in ("tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "chat_template.jinja"):
        if (src / f).exists():
            shutil.copy(src / f, d / f)
    return d


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
    shutil.copy(SOL / "submit.sh", sol / "submit.sh")
    (sol / "lab.sbatch").write_text((SOL / "smoke.sbatch").read_text().replace(ACCOUNT, "grp_hdavulcu"))
    r = submit(env, "lab", script=sol / "submit.sh")
    assert r.returncode == 1 and "must set exactly" in r.stderr and not log.exists()


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
