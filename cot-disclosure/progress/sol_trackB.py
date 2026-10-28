"""Track B on Sol: Qwen3-8B served by vLLM on one A100, thinking on and off (decided Oct 28: Ollama never
runs on the Mac). One job starts the server from vLLM's own environment ($TRACKA_VLLM, envs/olmo-vllm),
runs progress/run_trackB.py against it (provider sol_vllm, --order core-first: the 30 MMLU-Pro items x
none / user / tool_real x on / off x 3 runs first, then the puzzles, then the other conditions), and
stops it. Thinking on/off goes in each request (enable_thinking, providers/sol_vllm.py).

  # once, in a CPU session (salloc, class QoS) with the network: the pinned snapshot into $HF_HOME
  source cot-disclosure/finetune/gpu/sol/env.sh
  HF_HUB_OFFLINE=0 "$TRACKA_PY" cot-disclosure/progress/sol_trackB.py --download
  # the job: 1 A100, resumable (finished runs are skipped); limit = estimate x 1.3
  cot-disclosure/finetune/gpu/sol/submit.sh trackb_qwen8b --estimate 1.5
  # back to the Mac, numbers only (results/trackB/): sol_vllm_runs.jsonl and sol_vllm_flags.jsonl

First step: `vllm serve --help=all` on the GPU node must give the committed option list and the
server command must fit it (finetune/gpu/vllm_options.py); then the snapshot must be on disk at the
pinned revision. Slurm's
warning (USR1, 5 minutes before the limit) makes the runner start no new request; replies still in
flight when the job ends are not saved and run again in the next job (never "no answer"). At the end,
every record's numbers-only flags (progress/trackB_report.flags: answered, followed, mention flags,
tokens; no text) are written to results/trackB/sol_vllm_flags.jsonl; trackB_report.py on the Mac reads
them where the records themselves (with text) stay on Sol.
"""
import argparse
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from providers import sol_vllm  # noqa: E402

REPO, REVISION = "Qwen/Qwen3-8B", "b968826d9c46dd6066d109eabc6255188de91218"
MODEL = "qwen3-8b"
MAX_MODEL_LEN = 33792            # the 32,768-token budget + room
OUT = CODE / "results" / "trackB"
FLAGS = OUT / "sol_vllm_flags.jsonl"
STOP = CODE / "logs" / "stop_sol_trackB"
PATTERNS = ["*.json", "*.safetensors", "*.txt", "*.jinja", "tokenizer*", "merges.txt", "vocab.json"]


def serve_cmd(snapshot, vllm="vllm", port=sol_vllm.PORT):
    """The server for Track B's Qwen3-8B: reasoning split out, tool calls parsed, the budget's context."""
    return [vllm, "serve", str(snapshot), "--served-model-name", MODEL, "--port", str(port),
            "--max-model-len", str(MAX_MODEL_LEN), "--dtype", "bfloat16", "--seed", "0",
            "--reasoning-parser", "qwen3", "--enable-auto-tool-choice", "--tool-call-parser", "hermes"]


def snapshot(local_only=True):
    from huggingface_hub import snapshot_download
    return Path(snapshot_download(REPO, revision=REVISION, allow_patterns=PATTERNS, local_files_only=local_only))


def runner_cmd(extra=()):
    return [sys.executable, "-u", str(CODE / "progress" / "run_trackB.py"), "--run", "--model", MODEL,
            "--order", "core-first", "--stop-file", str(STOP), *extra]


def export_flags(records=OUT / "sol_vllm.jsonl.gz", out=FLAGS):
    """Every finished record's numbers-only flags, rewritten in full (a derived copy)."""
    from common import latest, load
    from trackB_report import flags
    rows = [flags(r) for r in latest(load(records)) if r.get("experiment") == "trackB" and r["status"] == "ok"] \
        if Path(records).exists() else []
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("".join(json.dumps(r) + "\n" for r in rows))
    return len(rows)


def preflight(vllm, log_dir):
    """The job's first step: `vllm serve --help=all` on this GPU node must give the committed option list,
    and every server command (this one included) must fit it (finetune/gpu/vllm_options.py)."""
    from finetune.gpu import vllm_options
    vllm_options.gpu_preflight(vllm, log_dir)


def run(extra, log_dir):
    from finetune.gpu import eval_job
    vllm = os.environ.get("TRACKA_VLLM", "vllm")
    preflight(vllm, log_dir)
    try:
        snap = snapshot()
    except Exception as err:
        sys.exit(f"no {REPO} snapshot at {REVISION} in $HF_HOME ({type(err).__name__}): run --download first")
    cmd = serve_cmd(snap, vllm=vllm)
    STOP.parent.mkdir(parents=True, exist_ok=True)
    STOP.unlink(missing_ok=True)
    signal.signal(signal.SIGUSR1, lambda *_: STOP.write_text("Slurm's time-limit warning"))
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    with eval_job.Server(None, False, port=sol_vllm.PORT, log=Path(log_dir) / "vllm_qwen3_8b.log", cmd=cmd):
        env = {**os.environ, "TRACKB_VLLM_URL": f"http://localhost:{sol_vllm.PORT}/v1"}
        rc = subprocess.call(runner_cmd(extra), env=env, cwd=CODE)
    print(f"runner exit {rc} (0 done, 1 work left, 2 stopped); {export_flags()} records' flags in {FLAGS}", flush=True)
    return rc


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--download", action="store_true", help="the pinned snapshot into $HF_HOME (needs the network)")
    mode.add_argument("--run", action="store_true", help="the job: server + runner (inside a Slurm job)")
    mode.add_argument("--export-flags", action="store_true", help="rewrite sol_vllm_flags.jsonl from the records")
    mode.add_argument("--print-cmd", action="store_true", help="the server command")
    ap.add_argument("--thinking", choices=["on", "off"], help="only this setting")
    ap.add_argument("--limit", type=int, help="at most N runs (a smoke test)")
    ap.add_argument("--log-dir", default=os.environ.get("TRACKA_OUT", "/scratch/ragarw68/trackA") + "/trackb_qwen8b")
    a = ap.parse_args()
    if a.download:
        print(snapshot(local_only=False))
    elif a.print_cmd:
        print(" ".join(serve_cmd("SNAPSHOT")))
    elif a.export_flags:
        print(export_flags())
    else:
        extra = (["--thinking", a.thinking] if a.thinking else []) + (["--limit", str(a.limit)] if a.limit else [])
        sys.exit(run(extra, a.log_dir))


if __name__ == "__main__":
    main()
