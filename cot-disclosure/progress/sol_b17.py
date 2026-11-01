"""B17 on Sol (Oct 31): gpt-oss-20b at reasoning effort low, medium and high on our vLLM server, one A100
(progress/run_b17.py: the design, the checks, the report). vLLM only: the Hugging Face engine (sol_hf) has no
harmony format.

  # once, a job without a GPU and the only one with the network: the pinned snapshot into $HF_HOME
  # (/scratch/$USER/hf) unless it is cached (~13.8 GB: the three MXFP4 shards, not original/ or metal/), every file
  # checked against the Hub's sha256 or git blob id
  cot-disclosure/finetune/gpu/sol/submit.sh get_gptoss                          # -> $TRACKA_OUT/b17/snapshot.json
  # the smoke job (one question x 5 conditions x 3 efforts, the design's first 15 runs, which count), then the runs
  cot-disclosure/finetune/gpu/sol/submit.sh b17 --estimate 0.75 -- --smoke
  cot-disclosure/finetune/gpu/sol/submit.sh b17 --estimate 6                   # resumable; again if runs are left
  # back to the Mac, numbers only: results/trackB/b17/ and results/trackB/b17_sol_vllm_runs.jsonl

The job, in order (every step stops it before the next):
  1. vLLM's options on this node: every server command (this one's included) fits the committed list and the node's
     `vllm serve --help=all` (finetune/gpu/vllm_options.py).
  2. The snapshot at the pinned revision, its files the sizes snapshot.json recorded.
  3. The server (serve_cmd): harmony's reasoning and tool-call parsers (openai_gptoss, openai), the budget's context,
     and the A100's kernels named, not left to auto-selection (Ampere, compute capability 8.0): Triton attention,
     which takes gpt-oss's attention sinks (vLLM's FlashAttention takes them only at versions 3-4, Hopper), and
     Marlin for the MXFP4 experts. --auto-backends drops both, for a second try if a named kernel fails to start.
     The harmony system message's date is pinned (VLLM_SYSTEM_START_DATE = START_DATE), else it is the day's.
  4. The served-template check (run_b17.template_check, B10's, token for token): the 15 first-turn prompts' token
     ids from the server (return_token_ids, max_tokens 1) against the snapshot's chat template at each effort and the
     same date. A prompt that differs beyond whitespace stops the job before any run: template_check.json.
  5. The runner (run_b17.py --run) against the server; Slurm's warning (USR1, 5 minutes before the limit) makes it
     start no new request.
  6. The numbers-only flags (results/trackB/b17/b17_flags.jsonl); with --smoke, the smoke's verdict
     (run_b17.smoke_check -> smoke_check.json): all 15 ran, at least 12 answered, every run that ended on its own
     parsed, the tool path ran, the effort reaches the model.
The exit code is 0 only when every step and check passed (4: the template check failed; 5: the smoke isn't clean;
1 or 2: the runner left runs or was stopped), so the main job can wait on the smoke with afterok (Ritik, Nov 1).
"""
import argparse
import getpass
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
import sol_trackB as st  # noqa: E402

REPO, REVISION = "openai/gpt-oss-20b", "6cee5e81ee83917806bbde320786a8fb61efebee"
MODEL = "gpt-oss-20b"
MAX_MODEL_LEN = 33792            # the 32,768-token budget + room
START_DATE = "2026-10-31"        # the harmony system message's "Current date" (VLLM_SYSTEM_START_DATE), pinned
PATTERNS = ["config.json", "generation_config.json", "model.safetensors.index.json", "model-*-of-*.safetensors",
            "tokenizer*", "special_tokens_map.json", "chat_template.jinja"]
TEMPLATE_FILE = "gpt_oss_20b_chat_template.jinja"
STOP = CODE / "logs" / "stop_b17"
KERNELS = ["--attention-backend", "TRITON_ATTN", "--moe-backend", "marlin"]


def serve_cmd(snapshot, vllm="vllm", port=sol_vllm.PORT, auto_backends=False):
    """B17's server: harmony's reasoning and tool parsers, the budget's context, bf16 activations over the MXFP4
    experts, and the A100's kernels named (module docstring) unless auto_backends."""
    return [vllm, "serve", str(snapshot), "--served-model-name", MODEL, "--port", str(port),
            "--max-model-len", str(MAX_MODEL_LEN), "--dtype", "bfloat16", "--seed", "0",
            "--reasoning-parser", "openai_gptoss", "--enable-auto-tool-choice", "--tool-call-parser", "openai",
            *([] if auto_backends else KERNELS)]


def snapshot(local_only=True):
    from huggingface_hub import snapshot_download
    return Path(snapshot_download(REPO, revision=REVISION, allow_patterns=PATTERNS, local_files_only=local_only))


def download(log_dir):
    """The no-GPU download job (the only one with the network): the pinned snapshot unless it is cached, every file
    checked against the Hub (sol_trackB.check_files), and the record in snapshot.json."""
    import fnmatch
    from huggingface_hub import HfApi
    from finetune.gpu import kit
    info = HfApi().model_info(REPO, revision=REVISION, files_metadata=True)
    wanted = [s for s in info.siblings if any(fnmatch.fnmatch(s.rfilename, pat) for pat in PATTERNS)]
    if not any(s.rfilename.endswith(".safetensors") for s in wanted):
        sys.exit(f"refusing: no weight shards of {REPO}@{REVISION[:8]} match {PATTERNS}")
    try:
        snap = snapshot(local_only=True)
        cached = all((snap / s.rfilename).exists() for s in wanted)
    except Exception:
        cached = False
    if not cached:
        snap = snapshot(local_only=False)
    files, bad = st.check_files(snap, wanted)
    if bad:
        sys.exit(f"refusing: the {REPO}@{REVISION[:8]} snapshot doesn't match the Hub:\n  " + "\n  ".join(bad))
    _, tpl_sha = st.write_template(snap, log_dir, TEMPLATE_FILE)
    rec = {"repo": REPO, "revision": REVISION, "hub_sha": info.sha, "path": str(snap), "was_cached": cached,
           "files": files, "bytes": sum(f["bytes"] for f in files), "chat_template_sha256": tpl_sha, "checked_utc": kit.now()}
    st.snapshot_record(log_dir).write_text(json.dumps(rec, indent=1) + "\n")
    print(f"{REPO}@{REVISION[:8]}: {'already cached' if cached else 'downloaded'} at {snap}; {len(files)} files "
          f"({rec['bytes'] / 1e9:.1f} GB) match the Hub; chat template {tpl_sha[:12]}; -> {st.snapshot_record(log_dir)}",
          flush=True)
    return rec


def checked_snapshot(log_dir):
    try:
        snap = snapshot()
    except Exception as err:
        sys.exit(f"no {REPO} snapshot at {REVISION} in $HF_HOME ({type(err).__name__}): run the download job first "
                 f"(submit.sh get_gptoss)")
    st.check_snapshot(snap, log_dir, revision=REVISION, job="get_gptoss")
    return snap


def preflight(vllm, log_dir):
    from finetune.gpu import vllm_options
    vllm_options.gpu_preflight(vllm, log_dir)


def server_ids(url):
    """(effort, messages, tools) -> the prompt token ids the server rendered (return_token_ids; max_tokens 1)."""
    from providers.base import post_json

    def ids(effort, messages, tools):
        req = {**sol_vllm.build_request(MODEL, messages, tools=tools, max_tokens=1, temperature=run_b17().TEMPERATURE, seed=0,
                                        reasoning_effort=effort), "return_token_ids": True}
        status, body = post_json(url.rstrip("/") + "/chat/completions", {}, req, timeout=600)
        if status != 200 or "prompt_token_ids" not in body:
            sys.exit(f"refusing: the template check's request got HTTP {status} without prompt_token_ids: "
                     f"{str(body)[:300]}")
        return body["prompt_token_ids"]
    return ids


def local_ids(tok):
    """(effort, messages, tools) -> our token ids: the snapshot's chat template at that effort and START_DATE."""
    def ids(effort, messages, tools):
        out = tok.apply_chat_template(messages, tools=tools, add_generation_prompt=True, tokenize=True,
                                      reasoning_effort=effort, strftime_now=lambda fmt: START_DATE)
        return list(out["input_ids"] if hasattr(out, "keys") else out)
    return ids


def runner_cmd(limit=None):
    return [sys.executable, "-u", str(CODE / "progress" / "run_b17.py"), "--run", "--stop-file", str(STOP),
            *(["--limit", str(limit)] if limit else [])]


def run_b17():
    import run_b17 as rb
    return rb


def run(log_dir, smoke=False, limit=None, auto_backends=False):
    from transformers import AutoTokenizer
    from finetune.gpu import eval_job
    rb = run_b17()
    vllm = os.environ.get("TRACKA_VLLM", "vllm")
    preflight(vllm, log_dir)
    snap = checked_snapshot(log_dir)
    _, tpl_sha = st.write_template(snap, log_dir, TEMPLATE_FILE)
    os.environ["VLLM_SYSTEM_START_DATE"] = START_DATE                  # the server's environment is this one's
    cmd = serve_cmd(snap, vllm=vllm, auto_backends=auto_backends)
    STOP.parent.mkdir(parents=True, exist_ok=True)
    STOP.unlink(missing_ok=True)
    signal.signal(signal.SIGUSR1, lambda *_: STOP.write_text("Slurm's time-limit warning"))
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    rb.OUT.mkdir(parents=True, exist_ok=True)
    url = f"http://localhost:{sol_vllm.PORT}/v1"
    with eval_job.Server(None, False, port=sol_vllm.PORT, log=Path(log_dir) / "vllm_gpt_oss_20b.log", cmd=cmd):
        cfg = rb.config()
        tok = AutoTokenizer.from_pretrained(str(snap))
        check = rb.template_check(cfg, server_ids(url), local_ids(tok), tok.decode)
        (rb.OUT / "template_check.json").write_text(json.dumps({**check, "start_date": START_DATE,
                                                                 "server": cmd[3:]}, indent=1) + "\n")
        print(f"template check: {'passed' if check['ok'] else 'FAILED'} ("
              + ", ".join(f"{r['effort']} {r['condition']} {r['verdict']}" for r in check["rows"]) + ")", flush=True)
        if not check["ok"]:
            print(f"stopped before any run: a served prompt differs from the chat template ({rb.OUT / 'template_check.json'})",
                  flush=True)
            return 4
        env = {**os.environ, "TRACKB_VLLM_URL": url, "TRACKB_CHAT_TEMPLATE_SHA256": tpl_sha}
        rc = subprocess.call(runner_cmd(rb.SMOKE_JOBS if smoke else limit), env=env, cwd=CODE)
    print(f"runner exit {rc} (0 done, 1 work left, 2 stopped); {rb.export_flags()} records' flags in {rb.FLAGS}", flush=True)
    if smoke:
        from common import load
        import run_trackB as tb
        verdict = rb.smoke_check(load(tb.runs_path("sol_vllm", rb.EXPERIMENT)))
        (rb.OUT / "smoke_check.json").write_text(json.dumps(verdict, indent=1) + "\n")
        print(f"smoke: {'clean' if verdict['ok'] else 'NOT clean'} {verdict['checks']}; median output tokens "
              f"{verdict['median_output_tokens']}", flush=True)
        return rc if verdict["ok"] else 5
    return rc


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--download", action="store_true", help="the no-GPU download job: the pinned snapshot, checked")
    mode.add_argument("--run", action="store_true", help="the job: server, template check, runner (inside a Slurm job)")
    mode.add_argument("--export-flags", action="store_true", help="rewrite b17_flags.jsonl from the records")
    mode.add_argument("--print-cmd", action="store_true", help="the server command")
    ap.add_argument("--smoke", action="store_true", help="the design's first 15 runs, then the smoke's verdict")
    ap.add_argument("--limit", type=int, help="at most N runs")
    ap.add_argument("--auto-backends", action="store_true", help="leave the attention and MoE kernels to vLLM")
    ap.add_argument("--log-dir", default=os.environ.get("TRACKA_OUT", f"/scratch/{getpass.getuser()}/trackA") + "/b17")
    a = ap.parse_args()
    if a.download:
        Path(a.log_dir).mkdir(parents=True, exist_ok=True)
        download(a.log_dir)
    elif a.print_cmd:
        print(" ".join(serve_cmd("SNAPSHOT", auto_backends=a.auto_backends)))
    elif a.export_flags:
        print(run_b17().export_flags())
    else:
        sys.exit(run(a.log_dir, smoke=a.smoke, limit=a.limit, auto_backends=a.auto_backends))


if __name__ == "__main__":
    main()
