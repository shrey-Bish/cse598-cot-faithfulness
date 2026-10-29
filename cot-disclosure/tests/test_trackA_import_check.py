"""Every Sol job's startup import check (finetune/gpu/import_check.py, run first by sol/run.sh): CPU only,
no network. Oct 29: Track B's Qwen3-8B job failed after 22 minutes on `from transformers import
AutoTokenizer`; the environment was fine, but nothing checked it at the start."""
import json
import subprocess
import sys
import types
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

from finetune.gpu import import_check as ic  # noqa: E402

pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")


def test_this_environment_passes_and_names_every_version():
    r = subprocess.run([sys.executable, str(CODE / "finetune" / "gpu" / "import_check.py")], capture_output=True,
                       text=True, timeout=300)
    assert r.returncode == 0, r.stderr
    line = r.stdout.strip()
    assert line.startswith(f"import check ({sys.prefix}, Python ") and "(AutoTokenizer ok)" in line
    for name in ("torch", "transformers", "tokenizers", "peft"):
        assert f"{name} " in line
    assert "sitecustomize:" in line


def test_a_package_from_another_environment_fails(tmp_path):
    found, problems = ic.check_project(prefix=tmp_path / "envs" / "olmo")
    assert set(found) == set(ic.PACKAGES)
    assert len([p for p in problems if " comes from " in p]) == len(ic.PACKAGES)


def test_a_path_inside_another_environment_is_a_leak():
    olmo, vllm = "/scratch/ragarw68/envs/olmo", "/scratch/ragarw68/envs/olmo-vllm"
    path = ["/scratch/ragarw68/cse598-cot-faithfulness/cot-disclosure", "/etc/python",
            f"{olmo}/lib/python3.11/site-packages", f"{vllm}/lib/python3.11/site-packages"]
    assert ic.foreign_paths(olmo, path) == [f"{vllm}/lib/python3.11/site-packages"]
    assert ic.foreign_paths(vllm, path) == [f"{olmo}/lib/python3.11/site-packages"]


def test_auto_tokenizer_failing_to_import_fails_the_check(tmp_path, monkeypatch):
    """The Oct 29 message, from a transformers module without AutoTokenizer: reported, not a crash."""
    prefix = tmp_path / "env"
    fake = {n: types.SimpleNamespace(__version__="1.0", __file__=str(prefix / n / "__init__.py")) for n in ic.PACKAGES}
    monkeypatch.setattr(ic.importlib, "import_module", lambda name: fake[name])
    monkeypatch.setitem(sys.modules, "transformers", types.ModuleType("transformers"))
    found, problems = ic.check_project(prefix=prefix)
    assert found == {n: "1.0" for n in ic.PACKAGES}
    assert problems == ["from transformers import AutoTokenizer: ImportError: cannot import name 'AutoTokenizer' "
                        "from 'transformers' (unknown location)"]


def fake_python(tmp_path, body):
    py = tmp_path / "python"
    py.write_text("#!/bin/bash\n" + body)
    py.chmod(0o755)
    return str(py)


def test_vllms_environment_is_checked_with_its_own_python(tmp_path):
    ok = {"prefix": "/envs/olmo-vllm", "vllm_file": "/envs/olmo-vllm/lib/vllm/__init__.py", "inside": True,
          "python": "3.11.18", "versions": {"vllm": "0.31.0", "torch": "2.13.0", "transformers": "5.17.0"}}
    res, problems = ic.check_vllm(fake_python(tmp_path, f"echo 'INFO a log line'\necho '{json.dumps(ok)}'\n"))
    assert res == ok and problems == []
    res, problems = ic.check_vllm(fake_python(tmp_path, f"echo '{json.dumps({**ok, 'inside': False})}'\n"))
    assert problems == ["vllm comes from /envs/olmo-vllm/lib/vllm/__init__.py, not from /envs/olmo-vllm"]
    res, problems = ic.check_vllm(fake_python(tmp_path, "echo \"ModuleNotFoundError: No module named 'vllm'\" >&2\nexit 1\n"))
    assert res is None and "exit 1" in problems[0] and "No module named 'vllm'" in problems[0]
    res, problems = ic.check_vllm(fake_python(tmp_path, "sleep 30\n"), timeout=1)
    assert res is None and "TimeoutExpired" in problems[0]


def test_a_failure_exits_1_with_what_is_wrong(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(ic, "check_project", lambda: ({"torch": "2.14.1"}, ["import transformers: ImportError: x"]))
    monkeypatch.setattr(sys, "argv", ["import_check.py"])
    assert ic.main() == 1
    out = capsys.readouterr()
    assert out.out.startswith("import check FAILED (") and "import transformers: ImportError: x" in out.err


def test_dry_run_imports_nothing(monkeypatch, capsys):
    monkeypatch.setattr(ic, "check_project", lambda: pytest.fail("imported"))
    monkeypatch.setattr(sys, "argv", ["import_check.py", "--dry-run", "--vllm", "/envs/olmo-vllm/bin/python"])
    assert ic.main() == 0 and "and vllm with /envs/olmo-vllm/bin/python" in capsys.readouterr().out
