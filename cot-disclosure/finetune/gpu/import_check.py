"""Every Sol job's first step (sol/run.sh, before the step's own script): the job's Python imports torch,
transformers (with AutoTokenizer), tokenizers and peft, each from its own environment, and prints their
versions; a vLLM job also imports vllm in vLLM's environment. A missing or broken package fails the job
in seconds (Oct 29: Track B's Qwen3-8B job failed after 22 minutes, at its first prompt count).

  python finetune/gpu/import_check.py                              # the project environment (envs/olmo)
  python finetune/gpu/import_check.py --vllm "$TRACKA_VLLM_PY"     # and vLLM's (envs/olmo-vllm)

Each package must come from that Python's own environment (sys.prefix): one found elsewhere (another
environment through PYTHONPATH, or ~/.local) fails the check, and so does a sys.path entry inside
another environment. The sitecustomize Python loaded, if any, is named (Sol's PYTHONPATH is /etc/python).
Exit 0 with one line of versions, or 1 with what is wrong.
"""
import argparse
import importlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PACKAGES = ("torch", "transformers", "tokenizers", "peft")
VLLM_TIMEOUT_S = 900          # vLLM's first import on a node reads many files from /scratch (login node,
                              # Oct 29: both checks took 510 s, so 300 s was too close)

# run by vLLM's Python: its versions, and where vllm came from (all inside its prefix?)
VLLM_PROBE = r"""
import importlib.metadata as md, json, os, sys
import vllm
where = os.path.realpath(vllm.__file__)
print(json.dumps({"prefix": os.path.realpath(sys.prefix), "vllm_file": where,
                  "inside": where.startswith(os.path.realpath(sys.prefix) + os.sep),
                  "python": sys.version.split()[0],
                  "versions": {p: md.version(p) for p in ("vllm", "torch", "transformers")}}))
"""


def inside(path, prefix):
    try:
        Path(path).resolve().relative_to(Path(prefix).resolve())
        return True
    except ValueError:
        return False


def foreign_paths(prefix, path=None):
    """sys.path entries inside another conda environment (a leak such as PYTHONPATH from envs/olmo-vllm)."""
    return [p for p in (sys.path if path is None else path) if p and "/envs/" in p and not inside(p, prefix)]


def check_project(prefix=None):
    """({package: version}, [problems]) for this Python's environment."""
    prefix = prefix or sys.prefix
    found, problems = {}, []
    for name in PACKAGES:
        try:
            mod = importlib.import_module(name)
        except Exception as err:                      # noqa: BLE001 - any failure is the answer
            problems.append(f"import {name}: {type(err).__name__}: {err}")
            continue
        found[name] = getattr(mod, "__version__", "?")
        where = getattr(mod, "__file__", None) or ""
        if not inside(where, prefix):
            problems.append(f"{name} {found[name]} comes from {where}, not from {prefix}")
    if "transformers" in found:
        try:
            from transformers import AutoTokenizer  # noqa: F401
        except Exception as err:                      # noqa: BLE001
            problems.append(f"from transformers import AutoTokenizer: {type(err).__name__}: {err}")
    leaked = foreign_paths(prefix)
    if leaked:
        problems.append(f"sys.path has another environment's paths: {leaked} (PYTHONPATH={os.environ.get('PYTHONPATH')!r})")
    return found, problems


def check_vllm(python, timeout=VLLM_TIMEOUT_S):
    """(probe result or None, [problems]) for vLLM's environment, run by its own Python."""
    try:
        r = subprocess.run([python, "-c", VLLM_PROBE], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as err:
        return None, [f"vLLM's Python ({python}): {type(err).__name__}: {err}"]
    if r.returncode != 0:
        tail = "\n    ".join((r.stderr or r.stdout).strip().splitlines()[-8:])
        return None, [f"import vllm with {python} failed (exit {r.returncode}):\n    {tail}"]
    try:
        res = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None, [f"vLLM's probe printed no versions: {r.stdout[-300:]!r}"]
    return res, ([] if res["inside"] else [f"vllm comes from {res['vllm_file']}, not from {res['prefix']}"])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vllm", metavar="PYTHON", help="also check vLLM's environment with this Python")
    ap.add_argument("--dry-run", action="store_true", help="say what would be checked; import nothing")
    a = ap.parse_args()
    if a.dry_run:
        print(f"would import {', '.join(PACKAGES)} (and AutoTokenizer) with {sys.executable}"
              + (f", and vllm with {a.vllm}" if a.vllm else ""))
        return 0
    # a line on stderr as each part starts: each can take minutes, and the result line comes only at the end
    print(f"importing {', '.join(PACKAGES)} with {sys.executable} ...", file=sys.stderr, flush=True)
    start = time.monotonic()
    found, problems = check_project()
    line = (f"import check ({sys.prefix}, Python {sys.version.split()[0]}): "
            + ", ".join(f"{k} {v}" for k, v in found.items()) + (" (AutoTokenizer ok)" if not problems else ""))
    site = sys.modules.get("sitecustomize")
    line += f"; sitecustomize: {getattr(site, '__file__', None) or 'none'} ({time.monotonic() - start:.0f} s)"
    if a.vllm:
        print(f"importing vllm with {a.vllm} (up to {VLLM_TIMEOUT_S} s) ...", file=sys.stderr, flush=True)
        start = time.monotonic()
        res, bad = check_vllm(a.vllm)
        problems += bad
        if res:
            line += (f"; vLLM environment ({res['prefix']}, Python {res['python']}): "
                     + ", ".join(f"{k} {v}" for k, v in res["versions"].items()))
        line += f" ({time.monotonic() - start:.0f} s)"
    if problems:
        print(line.replace("import check", "import check FAILED", 1), flush=True)
        print("  " + "\n  ".join(problems), file=sys.stderr, flush=True)
        return 1
    print(line, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
