"""Track B on Sol: Qwen3-8B served by vLLM on one A100, thinking on and off (decided Oct 28: Ollama never
runs on the Mac). One job starts the server from vLLM's own environment ($TRACKA_VLLM, envs/olmo-vllm),
runs progress/run_trackB.py against it (provider sol_vllm, --order core-first: the 30 MMLU-Pro items x
none / user / tool_real x on / off x 3 runs first, then the puzzles, then the other conditions), and
stops it. Thinking on/off goes in each request (enable_thinking, providers/sol_vllm.py).

  # once, a job without a GPU and the only one with the network: the pinned snapshot into $HF_HOME
  # (/scratch/ragarw68/hf) unless it is cached, checked against the Hub's sha256 of every file
  cot-disclosure/finetune/gpu/sol/submit.sh get_qwen8b          # -> $TRACKA_OUT/trackb_qwen8b/snapshot.json
  # the job: 1 A100, offline, resumable (finished runs are skipped); limit = estimate x 1.3
  cot-disclosure/finetune/gpu/sol/submit.sh trackb_qwen8b --estimate 1.5 --dependency=afterok:<get_qwen8b job>
  # back to the Mac, numbers only (results/trackB/): sol_vllm_runs.jsonl and sol_vllm_flags.jsonl

First step: `vllm serve --help=all` on the GPU node must give the committed option list and the
server command must fit it (finetune/gpu/vllm_options.py); then the snapshot must be on disk at the
pinned revision, its files the sizes snapshot.json recorded. The server gets the snapshot's chat
template as a file (--chat-template, written from tokenizer_config.json), and the runner saves that
file's sha256 with every run (chat_template_sha256). Slurm's
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


def serve_cmd(snapshot, vllm="vllm", port=sol_vllm.PORT, template=None):
    """The server for Track B's Qwen3-8B: reasoning split out, tool calls parsed, the budget's context,
    and (in the job) the snapshot's chat template as a file, so the template it uses is known."""
    return [vllm, "serve", str(snapshot), "--served-model-name", MODEL, "--port", str(port),
            "--max-model-len", str(MAX_MODEL_LEN), "--dtype", "bfloat16", "--seed", "0",
            "--reasoning-parser", "qwen3", "--enable-auto-tool-choice", "--tool-call-parser", "hermes",
            *(["--chat-template", str(template)] if template else [])]


def snapshot(local_only=True):
    from huggingface_hub import snapshot_download
    return Path(snapshot_download(REPO, revision=REVISION, allow_patterns=PATTERNS, local_files_only=local_only))


def chat_template(snap):
    """The snapshot's chat template text: chat_template.jinja, else tokenizer_config.json's."""
    jinja = Path(snap) / "chat_template.jinja"
    if jinja.exists():
        return jinja.read_text()
    tpl = json.loads((Path(snap) / "tokenizer_config.json").read_text()).get("chat_template")
    if isinstance(tpl, list):                                        # named templates: the default one
        tpl = next(x["template"] for x in tpl if x.get("name") == "default")
    if not tpl:
        raise ValueError(f"no chat template in {snap}")
    return tpl


def write_template(snap, log_dir):
    """The template as the file the server is given, and its sha256."""
    import hashlib
    text = chat_template(snap)
    path = Path(log_dir) / "qwen3_8b_chat_template.jinja"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path, hashlib.sha256(text.encode()).hexdigest()


def snapshot_record(log_dir):
    return Path(log_dir) / "snapshot.json"


def download(log_dir):
    """The no-GPU download job (the only one with the network): the pinned snapshot unless it is cached,
    every file checked against the Hub (sha256 for the large files, the git blob id for the small ones),
    and the record (revision, path, files, sizes, hashes, the chat template's sha256) in snapshot.json."""
    import fnmatch
    from huggingface_hub import HfApi
    from finetune.gpu import kit
    info = HfApi().model_info(REPO, revision=REVISION, files_metadata=True)
    wanted = [s for s in info.siblings if any(fnmatch.fnmatch(s.rfilename, pat) for pat in PATTERNS)]
    try:                                               # cached = every wanted file is there (a tokenizer-only
        snap = snapshot(local_only=True)               # cache is not)
        cached = all((snap / s.rfilename).exists() for s in wanted)
    except Exception:
        cached = False
    if not cached:
        snap = snapshot(local_only=False)              # fetches only what is missing
    files, bad = [], []
    for s in wanted:
        local = snap / s.rfilename
        if not local.exists():
            bad.append(f"{s.rfilename}: missing")
            continue
        lfs = s.lfs
        want = (lfs.get("sha256") if isinstance(lfs, dict) else getattr(lfs, "sha256", None)) if lfs is not None else None
        if want:                                       # weights and tokenizer.json: the Hub's sha256
            digest, kind = kit.sha256(local), "sha256"
        else:                                          # small files: the Hub's git blob id
            digest, kind, want = kit.git_blob_id(local), "git_blob_id", getattr(s, "blob_id", None)
        if want and digest != want:
            bad.append(f"{s.rfilename}: {kind} {digest[:12]} but the Hub has {want[:12]}")
        files.append({"file": s.rfilename, "bytes": local.stat().st_size, kind: digest, "hub": want})
    if bad:
        sys.exit(f"refusing: the {REPO}@{REVISION[:8]} snapshot doesn't match the Hub:\n  " + "\n  ".join(bad))
    _, tpl_sha = write_template(snap, log_dir)
    rec = {"repo": REPO, "revision": REVISION, "hub_sha": info.sha, "path": str(snap), "was_cached": cached,
           "files": files, "chat_template_sha256": tpl_sha, "checked_utc": kit.now()}
    snapshot_record(log_dir).write_text(json.dumps(rec, indent=1) + "\n")
    print(f"{REPO}@{REVISION[:8]}: {'already cached' if cached else 'downloaded'} at {snap}; {len(files)} files match "
          f"the Hub's sha256; chat template {tpl_sha[:12]}; -> {snapshot_record(log_dir)}", flush=True)
    return rec


def check_snapshot(snap, log_dir):
    """In the GPU job (offline): the download job's record exists and every file still has its size."""
    path = snapshot_record(log_dir)
    if not path.exists():
        sys.exit(f"no {path}: run the download job first (submit.sh get_qwen8b)")
    rec = json.loads(path.read_text())
    off = [f["file"] for f in rec["files"] if not (Path(snap) / f["file"]).exists()
           or (Path(snap) / f["file"]).stat().st_size != f["bytes"]]
    if rec["revision"] != REVISION or off:
        sys.exit(f"refusing: the snapshot differs from {path} (revision {rec['revision'][:8]}; files {off})")
    return rec


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
        sys.exit(f"no {REPO} snapshot at {REVISION} in $HF_HOME ({type(err).__name__}): run the download job "
                 f"first (submit.sh get_qwen8b)")
    check_snapshot(snap, log_dir)
    template, tpl_sha = write_template(snap, log_dir)
    cmd = serve_cmd(snap, vllm=vllm, template=template)
    STOP.parent.mkdir(parents=True, exist_ok=True)
    STOP.unlink(missing_ok=True)
    signal.signal(signal.SIGUSR1, lambda *_: STOP.write_text("Slurm's time-limit warning"))
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    with eval_job.Server(None, False, port=sol_vllm.PORT, log=Path(log_dir) / "vllm_qwen3_8b.log", cmd=cmd):
        env = {**os.environ, "TRACKB_VLLM_URL": f"http://localhost:{sol_vllm.PORT}/v1",
               "TRACKB_CHAT_TEMPLATE_SHA256": tpl_sha}
        rc = subprocess.call(runner_cmd(extra), env=env, cwd=CODE)
    print(f"runner exit {rc} (0 done, 1 work left, 2 stopped); {export_flags()} records' flags in {FLAGS}", flush=True)
    return rc


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--download", action="store_true", help="the no-GPU download job: the pinned snapshot, checked")
    mode.add_argument("--run", action="store_true", help="the job: server + runner (inside a Slurm job)")
    mode.add_argument("--export-flags", action="store_true", help="rewrite sol_vllm_flags.jsonl from the records")
    mode.add_argument("--print-cmd", action="store_true", help="the server command")
    ap.add_argument("--thinking", choices=["on", "off"], help="only this setting")
    ap.add_argument("--limit", type=int, help="at most N runs (a smoke test)")
    ap.add_argument("--log-dir", default=os.environ.get("TRACKA_OUT", "/scratch/ragarw68/trackA") + "/trackb_qwen8b")
    a = ap.parse_args()
    if a.download:
        Path(a.log_dir).mkdir(parents=True, exist_ok=True)
        download(a.log_dir)
    elif a.print_cmd:
        print(" ".join(serve_cmd("SNAPSHOT", template="TEMPLATE")))
    elif a.export_flags:
        print(export_flags())
    else:
        extra = (["--thinking", a.thinking] if a.thinking else []) + (["--limit", str(a.limit)] if a.limit else [])
        sys.exit(run(extra, a.log_dir))


if __name__ == "__main__":
    main()
