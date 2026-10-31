"""The Sol kit for a second user (Oct 30): every path from $USER (/scratch/<user>, or TRACKA_SCRATCH), Slurm's
%u in the job scripts' log lines, the allowed accounts from accounts.d/<user>.conf, Ritik's case unchanged, and
no ragarw68 left in the kit's code. Fake sbatch, squeue, mkdir, module and Python on a copy of the kit; no
Slurm, no network."""
import os
import re
import shutil
import subprocess
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
SOL = CODE / "finetune" / "gpu" / "sol"
RITIK, RITIK_ACCOUNT = "ragarw68", "class_cse59888883fall2026"
SHREY, SHREY_ACCOUNT = "shrey", "class_cse598test"          # a made-up second user and course account
ROW = "public  class  960  2  10  24  4"                     # the class QoS's numbers (accounts.conf)
SHOW = ("TRACKA_SCRATCH TRACKA_ENV TRACKA_PY TRACKA_VLLM_ENV TRACKA_VLLM_PY TRACKA_VLLM HF_HOME TRACKA_OUT "
        "TRACKA_ACCOUNTS_FILE TRACKA_ACCOUNT")


def kit(tmp_path, accounts=None):
    """A copy of the Sol kit (tmp/repo/cot-disclosure/finetune/gpu/sol), with accounts.d/<user>.conf holding
    each {user: [row, ...]}. A committed accounts.d is left out, so the test doesn't depend on it."""
    sol = tmp_path / "repo" / "cot-disclosure" / "finetune" / "gpu" / "sol"
    shutil.copytree(SOL, sol, ignore=shutil.ignore_patterns("accounts.d"))
    for user, rows in (accounts or {}).items():
        (sol / "accounts.d").mkdir(exist_ok=True)
        (sol / "accounts.d" / f"{user}.conf").write_text(
            "# account  partition  qos  gpu_run_min  max_jobs  max_submit  max_wall_h  max_gpus\n"
            + "".join(r + "\n" for r in rows))
    return sol


def fake_bin(tmp_path, record_mkdir=False):
    """sbatch and squeue that record their arguments, and mkdir too for submit.sh (its default is /scratch/<user>,
    which the Mac doesn't have); module and activate that do nothing (no mamba on the Mac)."""
    b = tmp_path / "bin"
    b.mkdir()
    for name in ("sbatch", "squeue") + ("mkdir",) * record_mkdir:
        (b / name).write_text(f'#!/bin/bash\necho "$@" >> {tmp_path / (name + "_args")}\n')
    with open(b / "sbatch", "a") as f:
        f.write('echo "Submitted batch job 1"\n')
    (b / "module").write_text("#!/bin/bash\nexit 0\n")
    (b / "activate").write_text(":\n")                       # sourced by env.sh: source activate ENV
    for f in b.iterdir():
        f.chmod(0o755)
    return b


def environ(tmp_path, user, **extra):
    """The test's environment: this user, the fake tools first on PATH, nothing of Slurm's, the kit's or Hugging
    Face's from the Mac's shell."""
    keep = {k: v for k, v in os.environ.items() if not k.startswith(("SLURM_", "SBATCH_", "TRACKA_", "HF_"))}
    return {**keep, "PATH": f"{tmp_path / 'bin'}:{os.environ['PATH']}", "USER": user, **extra}


def args(tmp_path, name):
    p = tmp_path / f"{name}_args"
    return p.read_text().splitlines() if p.exists() else []


def source_env(sol, env):
    """Source env.sh and print every path it sets (also after its own refusal: they are set before it)."""
    script = f'source "{sol}/env.sh"; rc=$?; for v in {SHOW}; do echo "$v=${{!v}}"; done; echo "rc=$rc"'
    r = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True)
    return dict(x.split("=", 1) for x in r.stdout.splitlines() if "=" in x), r


def fake_python(prefix):
    """prefix/bin/python: passes env.sh's own check, then prints its arguments and the paths it was given."""
    py = prefix / "bin" / "python"
    py.parent.mkdir(parents=True)
    py.write_text('#!/bin/bash\nif [ "$1" = - ]; then cat > /dev/null; exit 0; fi\necho "ARGS $*"\n'
                  'echo "PATHS HF_HOME=$HF_HOME TRACKA_OUT=$TRACKA_OUT TRACKA_VLLM=$TRACKA_VLLM '
                  'ONLINE=$HF_HUB_OFFLINE"\n')
    py.chmod(0o755)
    return py


# ---------------------------------------------------------------- env.sh: every path from the user
def test_env_sh_puts_every_path_under_the_users_scratch(tmp_path):
    sol = kit(tmp_path, {SHREY: [f"{SHREY_ACCOUNT}  {ROW}"]})
    fake_bin(tmp_path)
    v, r = source_env(sol, environ(tmp_path, SHREY))
    s = "/scratch/shrey"
    assert (v["TRACKA_SCRATCH"], v["TRACKA_ENV"], v["TRACKA_PY"]) == (s, f"{s}/envs/olmo", f"{s}/envs/olmo/bin/python")
    assert (v["TRACKA_VLLM_ENV"], v["TRACKA_VLLM_PY"], v["TRACKA_VLLM"]) == (
        f"{s}/envs/olmo-vllm", f"{s}/envs/olmo-vllm/bin/python", f"{s}/envs/olmo-vllm/bin/vllm")
    assert (v["HF_HOME"], v["TRACKA_OUT"]) == (f"{s}/hf", f"{s}/trackA")
    assert v["TRACKA_ACCOUNTS_FILE"].endswith("/sol/accounts.d/shrey.conf") and v["TRACKA_ACCOUNT"] == SHREY_ACCOUNT
    # no environment yet on this machine: env.sh stops with the path a new user must create first
    assert v["rc"] == "1" and f"no Python at {s}/envs/olmo/bin/python" in r.stderr
    assert RITIK not in r.stdout + r.stderr


def test_env_sh_for_ritik_is_unchanged(tmp_path):
    sol = kit(tmp_path, {SHREY: [f"{SHREY_ACCOUNT}  {ROW}"]})   # another user's file changes nothing for him
    fake_bin(tmp_path)
    v, _ = source_env(sol, environ(tmp_path, RITIK))
    s = "/scratch/ragarw68"
    assert (v["TRACKA_ENV"], v["TRACKA_VLLM_ENV"], v["HF_HOME"], v["TRACKA_OUT"]) == (
        f"{s}/envs/olmo", f"{s}/envs/olmo-vllm", f"{s}/hf", f"{s}/trackA")
    assert v["TRACKA_ACCOUNTS_FILE"].endswith("/sol/accounts.conf") and v["TRACKA_ACCOUNT"] == RITIK_ACCOUNT
    v, _ = source_env(sol, environ(tmp_path, RITIK, TRACKA_OUT="/elsewhere"))
    assert v["TRACKA_OUT"] == "/elsewhere" and v["HF_HOME"] == f"{s}/hf"   # TRACKA_OUT still overrides


def test_env_sh_with_a_scratch_that_exists_activates(tmp_path):
    sol = kit(tmp_path, {SHREY: [f"{SHREY_ACCOUNT}  {ROW}"]})
    fake_bin(tmp_path)
    s = tmp_path / "scratch" / SHREY
    fake_python(s / "envs" / "olmo")
    v, r = source_env(sol, environ(tmp_path, SHREY, TRACKA_SCRATCH=str(s)))
    assert v["rc"] == "0", r.stderr
    for k in SHOW.split()[:-2]:
        assert v[k].startswith(str(s)), (k, v[k])


# ---------------------------------------------------------------- run.sh with the real env.sh
def run_sh(tmp_path, user, account, step, *a):
    sol = kit(tmp_path, {SHREY: [f"{SHREY_ACCOUNT}  {ROW}"]})
    if not (tmp_path / "bin").exists():
        fake_bin(tmp_path)
    s = tmp_path / "scratch" / user
    if not (s / "envs" / "olmo" / "bin" / "python").exists():
        fake_python(s / "envs" / "olmo")
    env = environ(tmp_path, user, TRACKA_SCRATCH=str(s), SLURM_JOB_ID="7", SLURM_JOB_ACCOUNT=account)
    return subprocess.run(["bash", str(sol / "run.sh"), step, *a], env=env, capture_output=True, text=True), s


def test_run_sh_c13_as_another_user(tmp_path):
    r, s = run_sh(tmp_path, SHREY, SHREY_ACCOUNT, "c13")
    assert r.returncode == 0, r.stderr
    check, line = [x.split()[1:] for x in r.stdout.splitlines() if x.startswith("ARGS ")]
    assert check == ["finetune/gpu/import_check.py", "--vllm", f"{s}/envs/olmo-vllm/bin/python"]
    assert line == ["agents/sol_c13.py", "--run", "--log-dir", f"{s}/trackA/c13"]
    paths = [x for x in r.stdout.splitlines() if x.startswith("PATHS ")][-1]
    assert paths == f"PATHS HF_HOME={s}/hf TRACKA_OUT={s}/trackA TRACKA_VLLM={s}/envs/olmo-vllm/bin/vllm ONLINE=1"
    log = next((s / "trackA" / "c13").glob("console_*_7.log")).read_text()
    assert f"({SHREY_ACCOUNT})" in log and RITIK not in r.stdout + r.stderr + log


def test_get_c13_as_another_user_downloads_into_their_cache(tmp_path):
    r, s = run_sh(tmp_path, SHREY, SHREY_ACCOUNT, "get_c13")
    assert r.returncode == 0, r.stderr
    line = [x.split()[1:] for x in r.stdout.splitlines() if x.startswith("ARGS ")][-1]
    assert line == ["agents/sol_c13.py", "--download", "--log-dir", f"{s}/trackA/c13"]
    paths = [x for x in r.stdout.splitlines() if x.startswith("PATHS ")][-1]
    assert f"HF_HOME={s}/hf " in paths and paths.endswith("ONLINE=0")          # the download job is online


def test_run_sh_refuses_another_users_account(tmp_path):
    """Shrey's job under Ritik's account (sbatch c13.sbatch without submit.sh) stops before anything runs."""
    r, _ = run_sh(tmp_path, SHREY, RITIK_ACCOUNT, "c13")
    assert r.returncode == 1 and "ARGS" not in r.stdout
    assert f"account '{RITIK_ACCOUNT}', not one listed in accounts.d/shrey.conf: stopping" in r.stderr
    r, _ = run_sh(tmp_path / "ritik", RITIK, RITIK_ACCOUNT, "c13")   # Ritik's own job: as before
    assert r.returncode == 0, r.stderr


# ---------------------------------------------------------------- submit.sh: the user's own accounts file
def submit(tmp_path, sol, user, *a, **extra):
    for f in ("sbatch_args", "squeue_args", "mkdir_args"):
        (tmp_path / f).unlink(missing_ok=True)
    env = environ(tmp_path, user, SBATCH_ACCOUNT="grp_hdavulcu", **extra)
    return subprocess.run(["bash", str(sol / "submit.sh"), *a], env=env, capture_output=True, text=True)


def test_submit_as_another_user_uses_their_account_and_scratch(tmp_path):
    sol = kit(tmp_path, {SHREY: [f"{SHREY_ACCOUNT}  {ROW}"]})
    fake_bin(tmp_path, record_mkdir=True)
    r = submit(tmp_path, sol, SHREY, "get_c13")
    assert r.returncode == 0 and "Submitted batch job 1" in r.stdout, r.stderr
    a = args(tmp_path, "sbatch")[0].split()
    assert a[:4] == ["-A", SHREY_ACCOUNT, "-t", "3:00:00"] and a[-1].endswith("get_c13.sbatch")
    assert "-p" not in a and "-q" not in a                       # his row lists the script's public / class
    assert args(tmp_path, "mkdir") == ["-p /scratch/shrey/trackA/slurm"]     # the scripts' /scratch/%u/... logs
    assert any(x.startswith("-h -u shrey --qos=class") for x in args(tmp_path, "squeue"))
    r = submit(tmp_path, sol, SHREY, "c13", "--estimate", "1.5")
    assert r.returncode == 0, r.stderr
    a = args(tmp_path, "sbatch")[0].split()
    assert a[:4] == ["-A", SHREY_ACCOUNT, "-t", "2:00:00"] and a[-1].endswith("c13.sbatch")
    assert "QoS check: this job 2:00:00 x 1 GPU = 120 GPU-minutes" in r.stdout and "total 120 of 960" in r.stdout
    assert RITIK not in r.stdout + r.stderr + "".join(args(tmp_path, "sbatch") + args(tmp_path, "mkdir"))


def test_submit_as_another_user_refuses_accounts_not_in_their_file(tmp_path):
    sol = kit(tmp_path, {SHREY: [f"{SHREY_ACCOUNT}  {ROW}"]})
    fake_bin(tmp_path, record_mkdir=True)
    for acct in (RITIK_ACCOUNT, "grp_hdavulcu"):
        r = submit(tmp_path, sol, SHREY, "c13", "--estimate", "1.5", TRACKA_SUBMIT_ACCOUNT=acct)
        assert r.returncode == 1 and not args(tmp_path, "sbatch"), r.stderr
        assert f"account '{acct}' is not listed in" in r.stderr and "accounts.d/shrey.conf" in r.stderr
    r = submit(tmp_path, sol, SHREY, "c13", "-A", SHREY_ACCOUNT)
    assert r.returncode == 1 and "not on the command line" in r.stderr and not args(tmp_path, "sbatch")
    (sol / "lab.sbatch").write_text((sol / "smoke.sbatch").read_text().replace(RITIK_ACCOUNT, "grp_hdavulcu"))
    r = submit(tmp_path, sol, SHREY, "lab")
    assert r.returncode == 1 and "must set exactly one -A" in r.stderr and not args(tmp_path, "sbatch")


def test_submit_for_ritik_is_unchanged(tmp_path):
    sol = kit(tmp_path, {SHREY: [f"{SHREY_ACCOUNT}  {ROW}"]})
    fake_bin(tmp_path, record_mkdir=True)
    r = submit(tmp_path, sol, RITIK, "c13", "--estimate", "1.5")
    assert r.returncode == 0, r.stderr
    a = args(tmp_path, "sbatch")[0].split()
    assert a[:4] == ["-A", RITIK_ACCOUNT, "-t", "2:00:00"] and "-p" not in a and "-q" not in a
    assert args(tmp_path, "mkdir") == ["-p /scratch/ragarw68/trackA/slurm"]
    r = submit(tmp_path, sol, RITIK, "c13", TRACKA_SUBMIT_ACCOUNT=SHREY_ACCOUNT)
    assert r.returncode == 1 and "is not listed in" in r.stderr and r.stderr.rstrip().endswith("/sol/accounts.conf")
    # a user with no accounts.d file of their own gets accounts.conf, as everyone did before Oct 30 (sbatch then
    # refuses the course account to anyone who isn't in it)
    r = submit(tmp_path, sol, "nobody", "get_c13")
    assert r.returncode == 0 and args(tmp_path, "sbatch")[0].split()[:2] == ["-A", RITIK_ACCOUNT], r.stderr


def test_the_qos_numbers_and_the_partition_come_from_the_users_row(tmp_path):
    """Each account row keeps its own QoS numbers; a partition and QoS the script names but the row doesn't list
    become the row's own, given on the command line (the job scripts are Ritik's)."""
    sol = kit(tmp_path, {SHREY: [f"{SHREY_ACCOUNT}  general  class  480  2  10  24  4"]})
    fake_bin(tmp_path, record_mkdir=True)
    r = submit(tmp_path, sol, SHREY, "step9", "--estimate", "6")          # 8:00 = 480 GPU-minutes: at the limit
    assert r.returncode == 0, r.stderr
    a = args(tmp_path, "sbatch")[0].split()
    assert a[:8] == ["-A", SHREY_ACCOUNT, "-p", "general", "-q", "class", "-t", "8:00:00"]
    assert "total 480 of 480" in r.stdout
    r = submit(tmp_path, sol, SHREY, "step9", "--estimate", "7")          # 9:30 = 570 > 480
    assert r.returncode == 1 and "over the class QoS's 480" in r.stderr and not args(tmp_path, "sbatch")


# ---------------------------------------------------------------- the job scripts and the code
def test_every_job_script_logs_under_the_submitting_users_scratch():
    """#SBATCH lines read no shell variable: the log path uses Slurm's %u (the user name), and submit.sh makes
    that same directory for the user who submits."""
    for f in sorted(SOL.glob("*.sbatch")):
        opts = [x for x in f.read_text().splitlines() if x.startswith("#SBATCH")]
        assert [x for x in opts if x.startswith(("#SBATCH -o", "#SBATCH -e", "#SBATCH --output", "#SBATCH --error"))] \
            == ["#SBATCH -o /scratch/%u/trackA/slurm/%x-%j.out"], f.name
        assert not [x for x in opts if "$" in x], f.name
    assert 'mkdir -p "${TRACKA_SLURM_LOGS:-/scratch/${USER:-$(id -un)}/trackA/slurm}"' in (SOL / "submit.sh").read_text()


def test_no_user_name_is_left_in_the_kits_code():
    """No literal ragarw68 in what runs on Sol: the kit's scripts and configs, and the Python it starts.
    The GPU README may name it only on a line that says it is an example."""
    files = [p for p in SOL.rglob("*") if p.is_file()]
    for pattern in ("finetune/**/*.py", "progress/*.py", "agents/sol_*.py", "providers/*.py"):
        files += CODE.glob(pattern)
    found = [f"{p.relative_to(CODE)}:{i}" for p in files
             for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1) if RITIK in line]
    assert found == []
    readme = (CODE / "finetune" / "gpu" / "README.md").read_text().splitlines()
    unlabelled = [f"README.md:{i}: {x}" for i, x in enumerate(readme, 1)
                  if RITIK in x and not re.search(r"\b(e\.g\.|for example)", x)]
    assert unlabelled == []
