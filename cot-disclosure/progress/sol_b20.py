"""B20 on Sol (Nov 3): one of three new families on our vLLM server, one A100 a job, thinking on and off
(progress/run_b20.py: the models, the design, the checks, the report). vLLM only, as B17.

  # once a model, a job without a GPU and the only one with the network: the pinned snapshot into $HF_HOME
  # (/scratch/$USER/hf) unless it is cached, every file checked against the Hub's sha256 or git blob id
  cot-disclosure/finetune/gpu/sol/submit.sh get_b20 --model M          # -> $TRACKA_OUT/b20/<M>/snapshot.json
  # the smoke (the design's first 12 runs, which count), then the runs once it is clean (afterok)
  cot-disclosure/finetune/gpu/sol/submit.sh b20 --model M -- --smoke  # estimate 1 h (limit 1:30)
  cot-disclosure/finetune/gpu/sol/submit.sh b20 --model M             # estimate 6 h (limit 8:00); again if runs are left
  # back to the Mac, numbers only: results/trackB/b20/<M>/ without the records (*.jsonl.gz)

The job, in order (every step stops it before the next):
  1. vLLM's options on this node: every server command, B20's three with the kit's, fits the committed list and the
     node's `vllm serve --help=all` (finetune/gpu/vllm_options.py).
  2. The snapshot at the pinned revision, its files the sizes snapshot.json recorded.
  3. A model whose MODELS entry names a vLLM template (none since Nov 3: Gemma 4 is served with its snapshot's own
     template, the one the check compares against): found in the installed package, else the job stops.
  4. The server (serve_cmd): the model's reasoning and tool-call parsers, bf16, the budget's context; Granite's parser
     from the snapshot's plugin file (--reasoning-parser-plugin, as its card serves it).
  5. The served-template check (run_b20.template_check): the 12 first-turn prompts' token ids from the server
     (return_token_ids, max_tokens 1) against the snapshot's chat template with the same enable_thinking; a prompt that
     differs beyond whitespace stops the job before any run (template_check.json); tool_real's second turn is recorded.
  6. The canary: 5 fixed prompts (run_b20.CANARY) at temperature 0, 64 tokens, thinking off; the completions' token ids
     appended to canary.jsonl, one row a job (a later job that differs is flagged in the report, never stopped).
  7. The runner (run_b20.py --run --model M) against the server; Slurm's warning (USR1, 5 minutes before the limit)
     writes this job's own stop file (logs/stop_b20_<job id>), so the runner starts no new request; GRACE seconds later
     a runner still waiting on requests in flight is stopped (SIGINT, then SIGKILL), so the job ends itself, exit 2,
     before its limit (Nov 4: 468897 and 508647).
  8. The numbers-only flags (results/trackB/b20/<M>/b20_flags.jsonl); with --smoke, the smoke's verdict
     (run_b20.smoke_check -> smoke_check.json): all 12 ran, at least 10 answered, every run that ended on its own
     parsed, the tool path ran (or the fallback's amendment is in), the reasoning split is right.
The exit code is 0 only when every step and check passed (4: the template check failed; 5: the smoke isn't clean;
1 or 2: the runner left runs or was stopped), so the main job can wait on the smoke with afterok, as B17's.
"""
import argparse
import getpass
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

import run_b20 as rb  # noqa: E402
from providers import sol_vllm  # noqa: E402
import sol_trackB as st  # noqa: E402

MAX_MODEL_LEN = 33792            # the 32,768-token budget + room
STOP_DIR = CODE / "logs"         # Nov 4: a stop file per job, stop_b20_<job id> (with one for all, Granite's warning
                                 # stopped Gemma's runner, and Nemotron's start removed it before Gemma looked: 508647)
GRACE = 120                      # after the warning, the requests in flight get this long; then the runner is stopped
# vLLM's template, found by the vLLM environment's own Python in the installed package's file list (RECORD)
FIND = ("import sys\nfrom importlib import metadata\n"
        "hits = [f.locate() for f in metadata.files('vllm') or [] if f.name == sys.argv[1]]\n"
        "print(hits[0] if hits else '')\n")


def serve_cmd(name, snapshot, vllm="vllm", port=sol_vllm.PORT, template=None):
    """B20's server for one model: its own reasoning and tool-call parsers (run_b20.MODELS), bf16, the budget's context;
    each with its snapshot's own chat template, Granite's parser from its snapshot's plugin file."""
    m = rb.MODELS[name]
    if m.get("vllm_template") and template is None:
        raise ValueError(f"{name} is served with vLLM's {m['vllm_template']}: pass its path")
    return [vllm, "serve", str(snapshot), "--served-model-name", name, "--port", str(port),
            "--max-model-len", str(MAX_MODEL_LEN), "--dtype", "bfloat16", "--seed", "0", *m["flags"],
            *(["--reasoning-parser-plugin", str(Path(snapshot) / m["plugin"])] if m.get("plugin") else []),
            *(["--chat-template", str(template)] if template else [])]


def job_commands():
    return {f"b20 {name}": serve_cmd(name, "SNAPSHOT", template="TEMPLATE" if m.get("vllm_template") else None)
            for name, m in rb.MODELS.items()}


def snapshot(name, local_only=True):
    from huggingface_hub import snapshot_download
    m = rb.MODELS[name]
    return Path(snapshot_download(m["repo"], revision=m["revision"], allow_patterns=m["patterns"], local_files_only=local_only))


def download(name, log_dir):
    """The no-GPU download job (the only one with the network): the pinned snapshot unless it is cached, every file
    checked against the Hub (sol_trackB.check_files), and the record (the revision and the Hub's commit, the files, the
    license, the chat template's sha256) in <log_dir>/<model>/snapshot.json."""
    import fnmatch
    from huggingface_hub import HfApi
    from finetune.gpu import kit
    m, here = rb.MODELS[name], Path(log_dir) / name
    info = HfApi().model_info(m["repo"], revision=m["revision"], files_metadata=True)
    if getattr(info, "gated", False):
        sys.exit(f"refusing: {m['repo']} is gated ({info.gated}); B20 takes only models without gated access")
    wanted = [s for s in info.siblings if any(fnmatch.fnmatch(s.rfilename, pat) for pat in m["patterns"])]
    if not any(s.rfilename.endswith(".safetensors") for s in wanted):
        sys.exit(f"refusing: no weight shards of {m['repo']}@{m['revision'][:8]} match {m['patterns']}")
    try:
        snap = snapshot(name, local_only=True)
        cached = all((snap / s.rfilename).exists() for s in wanted)
    except Exception:
        cached = False
    if not cached:
        snap = snapshot(name, local_only=False)
    files, bad = st.check_files(snap, wanted)
    if bad:
        sys.exit(f"refusing: the {m['repo']}@{m['revision'][:8]} snapshot doesn't match the Hub:\n  " + "\n  ".join(bad))
    _, tpl_sha = st.write_template(snap, here, "chat_template.jinja")
    rec = {"name": name, "repo": m["repo"], "revision": m["revision"], "hub_sha": info.sha, "path": str(snap),
           "was_cached": cached, "gated": getattr(info, "gated", None),
           "license": getattr(getattr(info, "card_data", None), "license", None), "files": files,
           "bytes": sum(f["bytes"] for f in files), "chat_template_sha256": tpl_sha, "checked_utc": kit.now()}
    st.snapshot_record(here).write_text(json.dumps(rec, indent=1) + "\n")
    print(f"{m['repo']}@{m['revision'][:8]}: {'already cached' if cached else 'downloaded'} at {snap}; {len(files)} files "
          f"({rec['bytes'] / 1e9:.1f} GB) match the Hub; chat template {tpl_sha[:12]}; -> {st.snapshot_record(here)}",
          flush=True)
    return rec


def checked_snapshot(name, log_dir):
    m = rb.MODELS[name]
    try:
        snap = snapshot(name)
    except Exception as err:
        sys.exit(f"no {m['repo']} snapshot at {m['revision']} in $HF_HOME ({type(err).__name__}): run the download job "
                 f"first (submit.sh get_b20 --model {name})")
    st.check_snapshot(snap, Path(log_dir) / name, revision=m["revision"], job=f"get_b20 --model {name}")
    return snap


def vllm_template(vllm, filename):
    """The template file the installed vLLM ships (Gemma 4's tool template), found by the vLLM environment's Python
    (beside the vllm command) in the package's file list. Not there: the job stops before any server."""
    py = Path(vllm).with_name("python") if os.sep in str(vllm) else Path("python")
    r = subprocess.run([str(py), "-c", FIND, filename], capture_output=True, text=True, timeout=600)
    path = Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None
    if path is None or not path.exists():
        why = (r.stderr or "").strip()[-300:] or "not in its file list"
        sys.exit(f"refusing: the installed vLLM ships no {filename} ({why}); nothing was served. Serving the snapshot's "
                 f"own chat template instead needs an amendment first")
    return path


def preflight(vllm, log_dir):
    """Step 1, vllm_options.gpu_preflight over the kit's server commands and B20's: vllm_options.job_commands() lists
    the kit's and stays as Sol's queued jobs load it, so B20's are added for this job only."""
    from finetune.gpu import vllm_options
    kit = vllm_options.job_commands
    vllm_options.job_commands = lambda: {**kit(), **job_commands()}
    try:
        vllm_options.gpu_preflight(vllm, log_dir)
    finally:
        vllm_options.job_commands = kit


def server_ids(url, name):
    """(thinking, messages, tools) -> the prompt token ids the server rendered (return_token_ids; max_tokens 1)."""
    from providers.base import post_json

    def ids(thinking, messages, tools):
        req = {**sol_vllm.build_request(name, messages, tools=tools, max_tokens=1, thinking=thinking, seed=0,
                                        temperature=rb.MODELS[name]["temperature"]), "return_token_ids": True}
        status, body = post_json(url.rstrip("/") + "/chat/completions", {}, req, timeout=600)
        if status != 200 or "prompt_token_ids" not in body:
            sys.exit(f"refusing: the template check's request got HTTP {status} without prompt_token_ids: "
                     f"{str(body)[:300]}")
        return body["prompt_token_ids"]
    return ids


def local_ids(tok):
    """(thinking, messages, tools) -> our token ids: the snapshot's chat template with the same enable_thinking."""
    def ids(thinking, messages, tools):
        out = tok.apply_chat_template(messages, tools=tools, add_generation_prompt=True, tokenize=True,
                                      enable_thinking=thinking)
        return list(out["input_ids"] if hasattr(out, "keys") else out)
    return ids


def canary(url, name):
    """The canary (run_b20.CANARY): each prompt at temperature 0, 64 tokens, thinking off, one at a time before any
    run; the completion's token ids (and its text's sha256, the text itself kept nowhere)."""
    from providers.base import post_json
    rows = []
    for i, prompt in enumerate(rb.CANARY):
        req = {**sol_vllm.build_request(name, [{"role": "user", "content": prompt}], max_tokens=64, temperature=0.0,
                                        seed=0, thinking=False), "return_token_ids": True}
        status, body = post_json(url.rstrip("/") + "/chat/completions", {}, req, timeout=600)
        choice = (body.get("choices") or [{}])[0]
        text = (choice.get("message") or {}).get("content") or ""
        rows.append({"prompt": i, "status": status, "token_ids": choice.get("token_ids"),
                     "finish_reason": choice.get("finish_reason"), "text_sha256": hashlib.sha256(text.encode()).hexdigest()})
    return {"rows": rows}


def stop_path(job=None):
    """This job's stop file: Slurm's warning writes it, and only this job's runner reads it."""
    return STOP_DIR / f"stop_b20_{job or os.environ.get('SLURM_JOB_ID') or os.getpid()}"


def runner_cmd(name, limit=None, stop=None):
    return [sys.executable, "-u", str(CODE / "progress" / "run_b20.py"), "--run", "--model", name, "--stop-file",
            str(stop or stop_path()), *(["--limit", str(limit)] if limit else [])]


def run_runner(cmd, env, stop, grace=GRACE, poll=5, kill_after=30):
    """The runner, as a child. Once the stop file exists (Slurm's warning), its requests in flight get `grace` seconds;
    then SIGINT (a record being saved is written whole: the save is in its main thread) and, `kill_after` seconds later,
    SIGKILL (its threads wait on their requests). Returns the runner's own exit code, or 2 when it had to be stopped:
    its runs in flight are lost, and the next job runs them (Nov 4: 468897 ran into its limit instead)."""
    proc = subprocess.Popen(cmd, env=env, cwd=CODE)
    warned = None
    while True:
        try:
            return proc.wait(timeout=poll)
        except subprocess.TimeoutExpired:
            pass
        if warned is None and stop.exists():
            warned = time.monotonic()
        if warned is not None and time.monotonic() - warned >= grace:
            break
    proc.send_signal(signal.SIGINT)
    try:
        proc.wait(timeout=kill_after)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    print(f"the runner was stopped {grace} s after Slurm's warning; its requests in flight run in the next job", flush=True)
    return 2


def run(log_dir, name, smoke=False, limit=None):
    from transformers import AutoTokenizer
    from common import append, load
    from finetune import generate as gen
    from finetune.gpu import eval_job, kit
    m, here, out = rb.MODELS[name], Path(log_dir) / name, rb.model_dir(name)
    vllm = os.environ.get("TRACKA_VLLM", "vllm")
    preflight(vllm, log_dir)
    snap = checked_snapshot(name, log_dir)
    template = vllm_template(vllm, m["vllm_template"]) if m.get("vllm_template") else None
    _, tpl_sha = st.write_template(snap, here, "chat_template.jinja")    # the check's reference, and Nemotron's and
    if template:                                                          # Granite's served template; Gemma's is vLLM's
        shutil.copy(template, here / "served_chat_template.jinja")
        tpl_sha = hashlib.sha256(Path(template).read_bytes()).hexdigest()
    port = gen.free_port(sol_vllm.PORT)                                   # Nov 4: a port of this job's own
    cmd = serve_cmd(name, snap, vllm=vllm, port=port, template=template)
    stop = stop_path()                                                    # Nov 4: this job's own
    stop.parent.mkdir(parents=True, exist_ok=True)
    stop.unlink(missing_ok=True)
    signal.signal(signal.SIGUSR1, lambda *_: stop.write_text("Slurm's time-limit warning"))
    out.mkdir(parents=True, exist_ok=True)
    url = f"http://localhost:{port}/v1"
    with eval_job.Server(None, False, port=port, log=here / "vllm.log", cmd=cmd):
        tok = AutoTokenizer.from_pretrained(str(snap))
        check = rb.template_check(rb.config(name), name, server_ids(url, name), local_ids(tok), tok.decode)
        (out / "template_check.json").write_text(json.dumps({**check, "revision": m["revision"], "server": cmd[3:],
                                                             "served_template_sha256": tpl_sha}, indent=1) + "\n")
        print(f"template check: {'passed' if check['ok'] else 'FAILED'} ("
              + ", ".join(f"{r['setting']} {r['condition']} {r['verdict']}" for r in check["rows"]) + ")", flush=True)
        if not check["ok"]:
            print(f"stopped before any run: a served prompt differs from the chat template ({out / 'template_check.json'})",
                  flush=True)
            return 4
        append(out / "canary.jsonl", {"job": os.environ.get("SLURM_JOB_ID"), "utc": kit.now(), "revision": m["revision"],
                                      "server": cmd[3:], **canary(url, name)})
        env = {**os.environ, "TRACKB_VLLM_URL": url, "TRACKB_CHAT_TEMPLATE_SHA256": tpl_sha}
        rc = run_runner(runner_cmd(name, rb.SMOKE_JOBS if smoke else limit, stop), env, stop)
    print(f"runner exit {rc} (0 done, 1 work left, 2 stopped); {rb.export_flags(name)} records' flags in "
          f"{rb.flags_path(name)}", flush=True)
    if smoke:
        verdict = rb.smoke_check(load(rb.flags_path(name)), name)
        (out / "smoke_check.json").write_text(json.dumps(verdict, indent=1) + "\n")
        print(f"smoke: {'clean' if verdict['ok'] else 'NOT clean'} {verdict['checks']}"
              + (f"; the fallback {verdict['fallback']}" if verdict["fallback"] else ""), flush=True)
        return rc if verdict["ok"] else 5
    return rc


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--download", action="store_true", help="the no-GPU download job: the pinned snapshot, checked")
    mode.add_argument("--run", action="store_true", help="the job: server, template check, canary, runner (Slurm)")
    mode.add_argument("--export-flags", action="store_true", help="rewrite the model's b20_flags.jsonl from its records")
    mode.add_argument("--print-cmd", action="store_true", help="the server command")
    ap.add_argument("--model", required=True, choices=list(rb.MODELS))
    ap.add_argument("--smoke", action="store_true", help="the design's first 12 runs, then the smoke's verdict")
    ap.add_argument("--limit", type=int, help="at most N runs")
    ap.add_argument("--log-dir", default=os.environ.get("TRACKA_OUT", f"/scratch/{getpass.getuser()}/trackA") + "/b20")
    a = ap.parse_args()
    if a.download:
        download(a.model, a.log_dir)
    elif a.print_cmd:
        print(" ".join(serve_cmd(a.model, "SNAPSHOT", template="TEMPLATE" if rb.MODELS[a.model].get("vllm_template") else None)))
    elif a.export_flags:
        print(rb.export_flags(a.model))
    else:
        sys.exit(run(a.log_dir, a.model, smoke=a.smoke, limit=a.limit))


if __name__ == "__main__":
    main()
