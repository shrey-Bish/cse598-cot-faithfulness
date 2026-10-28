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
        if all((CODE / f).exists() for f in kit.NEEDED[step]):   # produced inputs are gitignored: not in a fresh clone
            kit.check_inputs(step)                           # the same bytes as on the Mac that wrote the manifest


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
    part = next(o.split()[1] for o in opts if o.startswith("-p "))
    t = minutes(next(o.split()[1] for o in opts if o.startswith("-t ")))
    listed = [line.split()[1:3] for line in (SOL / "accounts.conf").read_text().splitlines()
              if line.strip() and not line.startswith("#")]
    assert [part, qos] in listed                               # Oct 28: the course account has only public/class
    assert qos == "class" and t <= 16 * 60                     # class QoS: <= 4 GPUs, 32 cores, 320 GB; we cap at 16 h
    assert int(next(o.split()[1] for o in opts if o.startswith("-c "))) <= 32
    assert int(next(o.split("=")[1].rstrip("G") for o in opts if o.startswith("--mem="))) <= 320
    gpus = [o for o in opts if o.startswith("-G ")]
    assert gpus in ([], ["-G a100:1"])
    assert "run.sh" in script.read_text() or "setup_env.sh" in script.read_text() or "setup_vllm.sh" in script.read_text()


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


@pytest.mark.parametrize("pair", [("lightwork", "public"), ("public", "debug"), ("public", "public")])
def test_submit_refuses_a_qos_the_account_does_not_list(tmp_path, pair):
    """Oct 28: setup_vllm asked for -p lightwork -q public; sbatch said "Invalid qos specification" after
    submit.sh printed "limits not checked". Now refused before sbatch, with the reason."""
    env, log = fake_sbatch(tmp_path)
    sol = tmp_path / "repo" / "cot-disclosure" / "finetune" / "gpu" / "sol"
    sol.mkdir(parents=True)
    for f in ("submit.sh", "guard.sh", "accounts.conf"):
        shutil.copy(SOL / f, sol / f)
    text = (SOL / "setup_vllm.sbatch").read_text().replace("-p public\n#SBATCH -q class", f"-p {pair[0]}\n#SBATCH -q {pair[1]}")
    (sol / "lab.sbatch").write_text(text)
    r = submit(env, "lab", script=sol / "submit.sh")
    assert r.returncode == 1 and not log.exists(), r.stdout + r.stderr
    assert f"partition '{pair[0]}' and QoS '{pair[1]}'" in r.stderr and "listed: -p public -q class" in r.stderr
    assert "limits not checked" not in r.stdout + r.stderr
    for extra in (["-q", "public"], ["--qos=debug"], ["-p", "lightwork"], ["--partition=public"]):
        r = submit(env, "setup_vllm", *extra)
        assert r.returncode == 1 and "from the job script" in r.stderr and not log.exists()


def test_a_job_without_a_gpu_runs_in_the_class_qos(tmp_path):
    env, log = fake_sbatch(tmp_path)
    for job in ("setup_vllm", "setup_env"):
        r = submit(env, job)
        assert r.returncode == 0 and "Submitted batch job 1" in r.stdout, r.stderr
        assert "x 0 GPU = 0 GPU-minutes" in r.stdout or "squeue not found" in r.stdout
        assert sbatch_args(log)[:2] == ["-A", ACCOUNT] and "-q" not in sbatch_args(log)


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


def fake_squeue_jobs(tmp_path, jobs):
    """A fake squeue: with -j ID it prints that job's "STATE NAME" (nothing if unknown); otherwise no jobs."""
    table = "".join(f"{k} {v}\n" for k, v in jobs.items())
    (tmp_path / "jobs.txt").write_text(table)
    (tmp_path / "bin" / "squeue").write_text(
        "#!/bin/bash\nwhile [ $# -gt 0 ]; do [ \"$1\" = -j ] && { grep \"^$2 \" " + str(tmp_path / "jobs.txt")
        + " | cut -d' ' -f2-; exit 0; }; shift; done\nexit 0\n")
    (tmp_path / "bin" / "squeue").chmod(0o755)


@pytest.mark.parametrize("job", ["setup_vllm", "setup_env", "smoke", "timing"])
def test_every_job_prints_its_job_id(tmp_path, job):
    env, log = fake_sbatch(tmp_path)
    r = submit(env, job)
    assert r.returncode == 0 and "Submitted batch job 1" in r.stdout, r.stderr          # no GPU line: no silence


def test_sbatch_failing_or_silent_is_an_error(tmp_path):
    env, log = fake_sbatch(tmp_path)
    (tmp_path / "bin" / "sbatch").write_text("#!/bin/bash\necho 'sbatch: error: Invalid qos' >&2\nexit 1\n")
    r = submit(env, "timing")
    assert r.returncode == 1 and "sbatch refused the job: sbatch: error: Invalid qos" in r.stderr
    (tmp_path / "bin" / "sbatch").write_text("#!/bin/bash\nexit 0\n")
    r = submit(env, "timing")
    assert r.returncode == 1 and "printed no job id" in r.stderr


def test_dependencies_must_be_live_jobs_of_the_right_kind(tmp_path):
    env, log = fake_sbatch(tmp_path)
    fake_squeue_jobs(tmp_path, {100: "PENDING trackA-setup-vllm", 101: "RUNNING trackA-timing",
                                102: "COMPLETED trackA-setup-vllm"})
    r = submit(env, "vllm_check", "--estimate", "1", "--dependency=afterok:100")
    assert r.returncode == 0 and "dependency ok: job 100" in r.stdout and "--dependency=afterok:100" in log.read_text()
    log.unlink()
    for dep, why in (("afterok:101", "is 'trackA-timing'"), ("afterok:102", "not running or pending"),
                     ("afterok:999", "not running or pending"), ("afterok:100:101", "is 'trackA-timing'")):
        r = submit(env, "vllm_check", "--estimate", "1", f"--dependency={dep}")
        assert r.returncode == 1 and why in r.stderr and not log.exists(), (dep, r.stderr)
    r = submit(env, "vllm_check", "--estimate", "1", "--dependency", "afterok:101")
    assert r.returncode == 1 and "trackA-timing" in r.stderr
    r = submit(env, "timing", "--dependency=afterok:100")
    assert r.returncode == 1 and "waits for no other job" in r.stderr


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


@pytest.mark.parametrize("step,args,want", [
    ("train", ["lora"], ["finetune/train.py", "--version", "lora", "--out", "{out}/train/lora"]),
    ("eval", ["lora_tags", "2/3"], ["finetune/gpu/eval_job.py", "--system", "lora_tags", "--out", "{out}/eval", "--part", "2/3"]),
    ("eval", ["base"], ["finetune/gpu/eval_job.py", "--system", "base", "--out", "{out}/eval"]),
    ("timing", [], ["finetune/train.py", "--version", "lora,tags,lora_tags,lora_attn3", "--timing", "12", "--out", "{out}/timing"]),
    ("vllm_check", [], ["finetune/gpu/eval_job.py", "--check", "--out", "{out}/vllm_check"]),
    ("trackb_qwen8b", ["--limit", "5"], ["progress/sol_trackB.py", "--run", "--log-dir", "{out}/trackb_qwen8b", "--limit", "5"]),
    ("get_qwen8b", [], ["progress/sol_trackB.py", "--download", "--log-dir", "{out}/trackb_qwen8b"])])
def test_run_sh_builds_each_new_step(tmp_path, step, args, want):
    """run.sh with env.sh stubbed (no mamba on the Mac): which script and arguments each step gets."""
    sol = tmp_path / "repo" / "cot-disclosure" / "finetune" / "gpu" / "sol"
    sol.mkdir(parents=True)
    for f in ("run.sh", "guard.sh", "accounts.conf"):
        shutil.copy(SOL / f, sol / f)
    out = tmp_path / "out"
    py = tmp_path / "py"
    py.write_text('#!/bin/bash\necho "ARGS $*"\necho "ONLINE ${HF_HUB_OFFLINE:-unset}"\n')
    py.chmod(0o755)
    (sol / "env.sh").write_text(f'TRACKA_PY={py}\nTRACKA_OUT={out}\nTRACKA_CODE={tmp_path}\n'
                                'source "$(dirname "${BASH_SOURCE[0]}")/guard.sh"\n')
    env = {**{k: v for k, v in os.environ.items() if not k.startswith("SLURM_")},
           "SLURM_JOB_ID": "7", "SLURM_JOB_ACCOUNT": ACCOUNT}
    r = subprocess.run(["bash", str(sol / "run.sh"), step, *args], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    line = next(x for x in r.stdout.splitlines() if x.startswith("ARGS "))
    assert line.split()[1:] == [w.format(out=out) for w in want]
    online = next(x for x in r.stdout.splitlines() if x.startswith("ONLINE "))
    assert online == ("ONLINE 0" if step == "get_qwen8b" else "ONLINE unset")      # only the download is online


def test_vllm_gets_its_own_environment_and_outputs_name_it():
    env = (SOL / "env.sh").read_text()
    assert "TRACKA_VLLM_ENV=/scratch/ragarw68/envs/olmo-vllm " in env and "TRACKA_ENV=/scratch/ragarw68/envs/olmo " in env
    setup = (SOL / "setup_vllm.sh").read_text()
    assert '"$TRACKA_PY" -m pip' not in setup and '"$TRACKA_VLLM_PY" -m pip install' in setup
    assert "refusing: the vLLM environment must not be the project environment" in setup
    rec = kit.environments()
    assert rec["driver"]["prefix"] and "transformers" in rec["driver"] and "vllm_server" not in rec


# ---------------------------------------------------------------- vLLM server options (Oct 27: 0.31.0 dropped one)
def test_every_server_command_uses_options_vllm_lists():
    """The exact command lines every job starts, against vLLM 0.31.0's own option list (tracked)."""
    from finetune.eval import SYSTEMS
    from finetune.gpu import eval_job as ej
    from finetune.gpu import vllm_options as vo
    version, opts = vo.load(vo.TRACKED)
    cmds = ej.server_commands()
    assert version == "0.31.0" and len(opts) > 300
    assert set(cmds) == {f"eval {s}" for s in SYSTEMS} | {"vllm_check plain", "vllm_check tagged"}
    assert vo.problems(cmds, opts) == [] and vo.problems(vo.job_commands(), opts) == []
    assert set(vo.job_commands()) == set(cmds) | {"trackB qwen3-8b"}              # Track B's Qwen3-8B server too
    assert "--enable-prompt-embeds" in cmds["eval lora_tags"] and "--enable-prompt-embeds" not in cmds["eval lora"]
    assert vo.unknown(["vllm", "serve", "M", "--disable-log-requests"], opts) == ["--disable-log-requests"]


def test_option_lines_and_choices_from_argparse_help():
    from finetune.gpu import vllm_options as vo
    help_text = ("usage: vllm serve [model_tag] [options]\n\noptions:\n"
                 "  --port PORT           Port number. (default: 8000)\n"
                 "  --dtype {auto,bfloat16,half}\n"
                 "                        Data type; see --kv-cache-dtype for the cache.\n"
                 "  --enable-lora, --no-enable-lora\n"
                 "  --api-server-count API_SERVER_COUNT, -asc API_SERVER_COUNT\n"
                 "  Use `--help=all` to show all available flags at once.\n")
    opts = vo.options(vo.option_lines(help_text))
    assert opts == {"--port": None, "--dtype": ["auto", "bfloat16", "half"], "--enable-lora": None,
                    "--no-enable-lora": None, "--api-server-count": None, "-asc": None}
    cmd = ["vllm", "serve", "M", "--port", "1", "--dtype", "bf16", "--dtype=half", "--seed", "0"]
    assert vo.unknown(cmd, opts) == ["--dtype bf16 (choices: auto,bfloat16,half)", "--seed"]


def run_setup_vllm(root, installed="0.31.0", committed=None):
    """setup_vllm.sh with env.sh stubbed: a fake vLLM environment (pip, and the installed version from
    the package metadata) whose `vllm` fails if anything calls it (no --help on a CPU node, Oct 28);
    the real driver Python runs vllm_options.py against the committed list (or `committed`)."""
    sol = root / "repo" / "cot-disclosure" / "finetune" / "gpu" / "sol"
    sol.mkdir(parents=True)
    shutil.copy(SOL / "setup_vllm.sh", sol)
    venv, bin_dir = root / "envs" / "olmo-vllm" / "bin", root / "bin"
    venv.mkdir(parents=True)
    bin_dir.mkdir()
    calls = root / "calls"
    py = (f'#!/bin/bash\necho "python $*" >> {calls}\n'
          f'if [ "$1" = -c ]; then case "$2" in *torch*) echo "vllm {installed} torch 2.13.0" ;; *) echo "{installed}" ;; esac; fi\n')
    for p, text in {venv / "python": py,
                    venv / "vllm": f'#!/bin/bash\necho "vllm $*" >> {calls}\necho "RuntimeError: Failed to infer device type" >&2\nexit 1\n',
                    bin_dir / "realpath": '#!/bin/bash\necho "${@: -1}"\n'}.items():       # the Mac's has no -m
        p.write_text(text)
        p.chmod(0o755)
    (sol / "env.sh").write_text(f"TRACKA_ENV={root}/envs/olmo\nTRACKA_VLLM_ENV={root}/envs/olmo-vllm\n"
                                f"TRACKA_VLLM_PY={venv}/python\nTRACKA_VLLM={venv}/vllm\nTRACKA_PY={sys.executable}\n"
                                f"TRACKA_OUT={root}/out\nTRACKA_CODE={CODE}\n"
                                + (f"TRACKA_VLLM_OPTIONS={committed}\n" if committed else ""))
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"}
    r = subprocess.run(["bash", str(sol / "setup_vllm.sh")], env=env, capture_output=True, text=True)
    return r, calls.read_text() if calls.exists() else ""


def test_setup_vllm_checks_version_and_commands_against_the_committed_list_without_help(tmp_path):
    from finetune.gpu import vllm_options as vo
    r, calls = run_setup_vllm(tmp_path / "ok")
    assert r.returncode == 0, r.stderr
    assert "vLLM 0.31.0 installed = the committed list's 0.31.0; all 9 server commands" in r.stdout
    assert "python -m pip install --no-input vllm==0.31.0" in calls          # the version comes from the list
    assert "vllm " not in calls.replace("vllm==", "")                         # vllm itself never ran (no --help)
    r, _ = run_setup_vllm(tmp_path / "newer", installed="0.32.0")
    assert r.returncode == 1 and "the installed vLLM is 0.32.0, but the committed option list" in r.stderr
    no_seed = tmp_path / "no_seed.txt"
    no_seed.write_text("".join(x + "\n" for x in vo.TRACKED.read_text().splitlines() if not x.startswith("--seed ")))
    r, _ = run_setup_vllm(tmp_path / "list", committed=no_seed)
    assert r.returncode == 1 and "eval base: --seed" in r.stderr and "trackB qwen3-8b: --seed" in r.stderr


def fake_vllm(tmp_path, lines=None, fail=None):
    """A `vllm` whose `serve --help=all` prints these option lines as argparse does (or fails)."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    help_file = tmp_path / "help.txt"
    help_file.write_text("usage: vllm serve [model_tag] [options]\n\noptions:\n" + "".join(f"  {x}\n" for x in lines or []))
    exe = tmp_path / "vllm"
    body = f'echo "{fail}" >&2; exit 1' if fail else f'[ "$*" = "serve --help=all" ] && cat {help_file}'
    exe.write_text(f"#!/bin/bash\necho ran >> {tmp_path / 'ran'}\n{body}\n")
    exe.chmod(0o755)
    return str(exe)


def test_every_vllm_job_compares_the_nodes_help_with_the_committed_list_first(tmp_path):
    from finetune.gpu import vllm_options as vo
    lines = [x for x in vo.TRACKED.read_text().splitlines() if x and not x.startswith("#")]
    vo.gpu_preflight(fake_vllm(tmp_path / "same", lines), tmp_path / "same")             # the same list: on
    with pytest.raises(SystemExit, match=r"differ from the committed 0.31.0 list \(removed 1: --seed\)"):
        vo.gpu_preflight(fake_vllm(tmp_path / "diff", [x for x in lines if not x.startswith("--seed ")]), tmp_path / "diff")
    assert vo.load(tmp_path / "diff" / "vllm_serve_options_node.txt")[1] == {k: v for k, v in vo.load()[1].items() if k != "--seed"}
    changed = [x.replace("{auto,bfloat16,", "{auto,") if x.startswith("--dtype") else x for x in lines]
    with pytest.raises(SystemExit, match="choices 1: --dtype"):
        vo.gpu_preflight(fake_vllm(tmp_path / "choice", changed), tmp_path / "choice")
    with pytest.raises(SystemExit, match="exited with code 1 on this node(.|\n)*Failed to infer device type"):
        vo.gpu_preflight(fake_vllm(tmp_path / "cpu", fail="RuntimeError: Failed to infer device type"), tmp_path / "cpu")
    committed = tmp_path / "committed.txt"
    committed.write_text(vo.TRACKED.read_text().replace("--enable-prompt-embeds, --no-enable-prompt-embeds\n", ""))
    exe = fake_vllm(tmp_path / "bad", lines)
    with pytest.raises(SystemExit, match="eval tags: --enable-prompt-embeds"):
        vo.gpu_preflight(exe, tmp_path / "bad", committed=committed)
    assert not (tmp_path / "bad" / "ran").exists()                         # a command misfit: refused before vllm


def test_eval_job_checks_the_node_before_anything_else(tmp_path, monkeypatch):
    from finetune.gpu import eval_job as ej
    order = []
    monkeypatch.setenv("SLURM_JOB_ID", "7")
    monkeypatch.setattr(ej, "preflight", lambda: (order.append("preflight"), sys.exit("refusing: differs"))[1])
    monkeypatch.setattr(kit, "check_inputs", lambda step: order.append("inputs"))
    monkeypatch.setattr(ej, "check", lambda out: order.append("check"))
    monkeypatch.setattr(sys, "argv", ["eval_job.py", "--check", "--out", str(tmp_path)])
    with pytest.raises(SystemExit, match="differs"):
        ej.main()
    assert order == ["preflight"]


def test_the_check_starts_the_plain_server_before_any_merge(tmp_path, monkeypatch):
    """S2: a server that can't start fails the job before the LoRA merge, the shard writing and the
    Hugging Face references (Oct 27: it failed after 12 minutes)."""
    from finetune.gpu import eval_job as ej
    events, command, plain = [], ej.Server.command, ej.server_commands()["vllm_check plain"]

    class Broken:
        def __init__(self, model_dir, prompt_embeds, log=None, **kw):
            events.append(command(model_dir, prompt_embeds))

        def __enter__(self):
            raise RuntimeError("the server exited with code 2")

        def __exit__(self, *exc):
            return False
    monkeypatch.setattr(ej, "Server", Broken)
    monkeypatch.setattr(kit, "snapshot", lambda *a: ("BASE", None))
    monkeypatch.setattr(ej, "check_prompts", lambda: ["p"])
    for name in ("synthetic_parts", "merge_lora", "hf_greedy"):
        monkeypatch.setattr(ej, name, lambda *a, _n=name, **k: events.append(_n))
    monkeypatch.setattr(ej.gen, "fold_model", lambda *a, **k: events.append("fold_model"))
    with pytest.raises(RuntimeError, match="exited with code 2"):
        ej.check(tmp_path)
    assert events == [plain]


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
