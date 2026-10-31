"""Track C, C13 on Sol: a third and a fourth model family as reviewers (decided Oct 29). Reviewer only, on
C4's 159 saved tool-team cases, with C4's prompt (run_team.py --rereview team_c4 --no-check-tool), the
variants answer_only, plus_private and plus_tool_log, bad lookups first; C11's settings otherwise
(temperature 0.6, seed = repeat, the 16,000-token cap). Each model is served by our own vLLM (envs/olmo-vllm)
in one A100 job, one model after the other, and reviews through providers/sol_chat.py.

  Model (served name)       Repository @ revision                                   Family, size
  granite-4.1-30b           ibm-granite/granite-4.1-30b @ 4fae6278                  IBM Granite, 28.9B dense
  mistral-small-3.2-24b     mistralai/Mistral-Small-3.2-24B-Instruct-2506 @ 95a6d26c Mistral, 24.0B dense
Both Apache 2.0, not gated on Hugging Face (checked Oct 29), non-thinking instruct models like C4's Olmo 3.1
32B Instruct and Qwen3 30B Instruct. Mistral runs in its own format (consolidated weights, its tokenizer),
as its model card serves it; the vision encoder gets no images.

  python agents/sol_c13.py --dry-run                            # models, commands, calls, GPU estimate
  cot-disclosure/finetune/gpu/sol/submit.sh get_c13             # the snapshots: no GPU, the network
  cot-disclosure/finetune/gpu/sol/submit.sh c13 --estimate 1.5  # both reviewers (limit 2:00)
  # back to the Mac (text included, like every Track C log): results/trackC/team_c13_<model>.jsonl
  python agents/run_team.py --summary --log team_c13_granite --cases results/trackB/steered_cases.jsonl --table

The job (--run): first `vllm serve --help=all` on the node against the committed option list
(finetune/gpu/vllm_options.py), then C4's log and the cases file must be in this checkout, then per model:
its snapshot as the download job recorded it (sizes), its server (log: $TRACKA_OUT/c13/vllm_<model>.log),
the runner as a subprocess against it (its own log, team_c13_<model>, so each model resumes on its own),
the server stopped. Slurm's warning (USR1) makes the runner start no new case; a case is done only when all
its reviews are saved, so the next job redoes the rest. Exit: the largest runner exit code (0 all done).
"""
import argparse
import fnmatch
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

from providers import sol_chat  # noqa: E402

MODELS = {
    "granite-4.1-30b": {"repo": "ibm-granite/granite-4.1-30b", "revision": "4fae6278f7132abf5e971f9de49ebbad09c54cce",
                        "family": "IBM Granite", "size": "28.9B dense", "log": "team_c13_granite",
                        "patterns": ["*.json", "*.safetensors", "*.jinja", "*.txt"], "flags": []},
    "mistral-small-3.2-24b": {"repo": "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
                              "revision": "95a6d26c4bfb886c58daf9d3f7332c857cb27b43", "family": "Mistral",
                              "size": "24.0B dense", "log": "team_c13_mistral",
                              "patterns": ["consolidated.safetensors", "params.json", "tekken.json", "config.json",
                                           "generation_config.json", "SYSTEM_PROMPT.txt"],
                              "flags": ["--tokenizer-mode", "mistral", "--config-format", "mistral", "--load-format",
                                        "mistral", "--limit-mm-per-prompt", '{"image":0}']},
}
MAX_MODEL_LEN = 32768            # the 16,000-token cap + C4's longest reviewer prompt (C11: 16.4k in all)
REVIEWER_MAX_TOKENS = 16000      # C11's cap (C4: 8,000)
WORKERS = 16                     # cases at once against the job's own server (Voyager: 4)
SOURCE_LOG, CASES = "team_c4", Path("results") / "trackB" / "steered_cases.jsonl"
STOP = CODE / "logs" / "stop_sol_c13"
# the GPU estimate's rates for a 24-30B dense model on one A100 with ~16 reviews in flight: assumptions,
# not measured (the job's own log has the measured rate)
PREFILL_TOK_S, DECODE_TOK_S = (2000, 4000), (300, 600)
START_MIN, OPTIONS_MIN = (5, 15), (5, 15)


def serve_cmd(name, snapshot, vllm="vllm", port=sol_chat.PORT):
    return [vllm, "serve", str(snapshot), "--served-model-name", name, "--port", str(port), "--max-model-len",
            str(MAX_MODEL_LEN), "--dtype", "bfloat16", "--seed", "0", *MODELS[name]["flags"]]


def runner_cmd(name, extra=()):
    return [sys.executable, "-u", str(CODE / "agents" / "run_team.py"), "--rereview", SOURCE_LOG, "--no-check-tool",
            "--bad-first", "--reviewer-model", f"{sol_chat.NAME}:{name}", "--reviewer-max-tokens",
            str(REVIEWER_MAX_TOKENS), "--cases", str(CASES), "--log", MODELS[name]["log"], "--run-name",
            f"C13-{name}", "--workers", str(WORKERS), "--stop-file", str(STOP), *extra]


def record_path(log_dir, name):
    return Path(log_dir) / f"snapshot_{name}.json"


def snapshot(name, local_only=True):
    from huggingface_hub import snapshot_download
    m = MODELS[name]
    return Path(snapshot_download(m["repo"], revision=m["revision"], allow_patterns=m["patterns"],
                                  local_files_only=local_only))


def download(name, log_dir):
    """The no-GPU download job (the only one with the network): the pinned snapshot unless it is cached,
    every file checked against the Hub (sha256 for the large files, the git blob id for the small ones),
    recorded in snapshot_<name>.json with the model's generation_config.json (the server's defaults)."""
    from huggingface_hub import HfApi
    from finetune.gpu import kit
    m = MODELS[name]
    info = HfApi().model_info(m["repo"], revision=m["revision"], files_metadata=True)
    if getattr(info, "gated", False):
        sys.exit(f"refusing: {m['repo']} is gated ({info.gated}); C13 takes only models without gated access")
    wanted = [s for s in info.siblings if any(fnmatch.fnmatch(s.rfilename, p) for p in m["patterns"])]
    try:
        snap = snapshot(name, local_only=True)
        cached = all((snap / s.rfilename).exists() for s in wanted)
    except Exception:
        cached = False
    if not cached:
        snap = snapshot(name, local_only=False)
    files, bad = [], []
    for s in wanted:
        local = snap / s.rfilename
        if not local.exists():
            bad.append(f"{s.rfilename}: missing")
            continue
        lfs = s.lfs
        want = (lfs.get("sha256") if isinstance(lfs, dict) else getattr(lfs, "sha256", None)) if lfs is not None else None
        if want:
            digest, kind = kit.sha256(local), "sha256"
        else:
            digest, kind, want = kit.git_blob_id(local), "git_blob_id", getattr(s, "blob_id", None)
        if want and digest != want:
            bad.append(f"{s.rfilename}: {kind} {digest[:12]} but the Hub has {want[:12]}")
        files.append({"file": s.rfilename, "bytes": local.stat().st_size, kind: digest, "hub": want})
    if bad:
        sys.exit(f"refusing: the {m['repo']}@{m['revision'][:8]} snapshot doesn't match the Hub:\n  " + "\n  ".join(bad))
    gen_cfg = snap / "generation_config.json"
    rec = {"name": name, "repo": m["repo"], "revision": m["revision"], "path": str(snap), "was_cached": cached,
           "gated": getattr(info, "gated", None), "license": getattr(getattr(info, "card_data", None), "license", None),
           "files": files, "generation_config": json.loads(gen_cfg.read_text()) if gen_cfg.exists() else None,
           "checked_utc": kit.now()}
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    record_path(log_dir, name).write_text(json.dumps(rec, indent=1) + "\n")
    gb = sum(f["bytes"] for f in files) / 1e9
    print(f"{m['repo']}@{m['revision'][:8]}: {'already cached' if cached else 'downloaded'} ({len(files)} files, "
          f"{gb:.1f} GB) at {snap}; every file matches the Hub -> {record_path(log_dir, name)}", flush=True)
    return rec


def checked_snapshot(name, log_dir):
    """In the GPU job (offline): the download job's record exists and every file still has its size."""
    path = record_path(log_dir, name)
    if not path.exists():
        sys.exit(f"no {path}: run the download job first (submit.sh get_c13)")
    try:
        snap = snapshot(name)
    except Exception as err:
        sys.exit(f"no {MODELS[name]['repo']} snapshot in $HF_HOME ({type(err).__name__}): run the download job first "
                 f"(submit.sh get_c13)")
    rec = json.loads(path.read_text())
    off = [f["file"] for f in rec["files"] if not (snap / f["file"]).exists() or (snap / f["file"]).stat().st_size != f["bytes"]]
    if rec["revision"] != MODELS[name]["revision"] or off:
        sys.exit(f"refusing: the {name} snapshot differs from {path} (revision {rec['revision'][:8]}; files {off})")
    return snap


def inputs_present():
    """C4's saved log and the cases file, which rsync brings (gitignored: they hold text)."""
    missing = [p for p in (CODE / "results" / "trackC" / f"{SOURCE_LOG}.jsonl", CODE / CASES) if not p.exists()]
    if missing:
        sys.exit("refusing: rsync these from the Mac first (README, C13): " + ", ".join(str(p) for p in missing))


def run(log_dir, names=None, extra=()):
    from finetune.gpu import eval_job, vllm_options
    vllm = os.environ.get("TRACKA_VLLM", "vllm")
    vllm_options.gpu_preflight(vllm, log_dir)
    inputs_present()
    STOP.parent.mkdir(parents=True, exist_ok=True)
    STOP.unlink(missing_ok=True)
    signal.signal(signal.SIGUSR1, lambda *_: STOP.write_text("Slurm's time-limit warning"))
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    codes = []
    for name in names or MODELS:
        if STOP.exists():
            break
        snap = checked_snapshot(name, log_dir)
        with eval_job.Server(None, False, port=sol_chat.PORT, log=Path(log_dir) / f"vllm_{name}.log",
                             cmd=serve_cmd(name, snap, vllm=vllm)):
            env = {**os.environ, "SOL_CHAT_URL": f"http://localhost:{sol_chat.PORT}/v1"}
            rc = subprocess.call(runner_cmd(name, extra), env=env, cwd=CODE)
        print(f"{name}: runner exit {rc} (0 done, 1 work left, 2 stopped)", flush=True)
        codes.append(rc)
    return max(codes, default=2)


def estimate(c11=CODE / "results" / "trackC" / "team_c11.jsonl"):
    """Tokens per model from C11's Olmo 3 7B Instruct reviews (the same 159 cases and variants, a
    non-thinking reviewer; its tokens are prompt + reply), and hours at the assumed rates."""
    rows = [json.loads(x) for x in open(c11)] if Path(c11).exists() else []
    rev = [r for r in rows if r.get("agent") == "reviewer" and r.get("reviewer_model") == "olmo3-7b-instruct"]
    total = sum(r["tokens"] or 0 for r in rev) or 1_290_000
    out = int(sum(len(r.get("final_text") or "") for r in rev) / 3.6) or 160_000      # ~3.6 characters a token
    prompt = total - out
    hours = [(prompt / p + out / d) / 3600 for p, d in zip(PREFILL_TOK_S[::-1], DECODE_TOK_S[::-1])]
    return {"reviews_per_model": len(rev) or 477, "tokens_per_model": total, "generated_per_model": out,
            "generation_hours_per_model": [round(h, 2) for h in hours]}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--download", action="store_true", help="the no-GPU download job: both snapshots, checked")
    mode.add_argument("--run", action="store_true", help="the GPU job: each model's server + the runner")
    mode.add_argument("--dry-run", action="store_true", help="models, server commands, calls and the GPU estimate")
    ap.add_argument("--model", action="append", choices=list(MODELS), help="only this model (repeatable)")
    ap.add_argument("--log-dir", default=os.environ.get("TRACKA_OUT", f"/scratch/{getpass.getuser()}/trackA") + "/c13")
    a = ap.parse_args()
    names = a.model or list(MODELS)
    if a.download:
        for name in names:
            download(name, a.log_dir)
    elif a.run:
        sys.exit(run(a.log_dir, names))
    else:
        for name in names:
            m = MODELS[name]
            print(f"{name}: {m['repo']}@{m['revision'][:8]} ({m['family']}, {m['size']}); log {m['log']}")
            print("  server: " + " ".join(serve_cmd(name, "SNAPSHOT")))
            print("  runner: " + " ".join(runner_cmd(name)[2:]))
        e = estimate()
        lo = sum(e["generation_hours_per_model"][0] for _ in names) + (OPTIONS_MIN[0] + START_MIN[0] * len(names)) / 60
        hi = sum(e["generation_hours_per_model"][1] for _ in names) + (OPTIONS_MIN[1] + START_MIN[1] * len(names)) / 60
        print(f"per model: {e['reviews_per_model']} reviews, ~{e['tokens_per_model'] / 1e6:.2f}M tokens (~"
              f"{e['generated_per_model'] / 1e6:.2f}M generated; C11's Olmo 3 7B Instruct on the same cases), "
              f"{e['generation_hours_per_model'][0]:.2f}-{e['generation_hours_per_model'][1]:.2f} h at "
              f"{PREFILL_TOK_S[0]:,}-{PREFILL_TOK_S[1]:,} prompt and {DECODE_TOK_S[0]}-{DECODE_TOK_S[1]} generated "
              f"tokens/s (assumed). Job: the option check ({OPTIONS_MIN[0]}-{OPTIONS_MIN[1]} min), {len(names)} server "
              f"starts ({START_MIN[0]}-{START_MIN[1]} min each) and the reviews: {lo:.1f}-{hi:.1f} A100 hours")


if __name__ == "__main__":
    main()
