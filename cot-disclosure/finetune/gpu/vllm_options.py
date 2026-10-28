"""Every vllm serve command a job starts, checked against vLLM's own option list before any GPU work
(Oct 27: vLLM 0.31.0 dropped --disable-log-requests, and the vLLM check job failed on a GPU after 12
minutes).

The list is committed: finetune/gpu/vllm_serve_options.txt, a "# vllm VERSION" line, then the option
lines of `vllm serve --help=all` ("--dtype {auto,bfloat16,...}", "--enable-lora, --no-enable-lora",
"--port PORT"). The CUDA build of vLLM can't build that help without a GPU (Oct 28, on a CPU node:
"Failed to infer device type"), so:
  setup_vllm.sh (CPU)     the installed vLLM's version must be the committed list's, and every server
                          command must use only options the committed list has; no --help
                            python finetune/gpu/vllm_options.py --check-commands --installed 0.31.0
  every vLLM GPU job      its first step, before any model load, merge or shard writing (gpu_preflight):
                          `vllm serve --help=all` on the GPU node must give the committed list exactly
                          (options and choices); else the job stops, saving the node's list to copy
                          back (it becomes the committed list once checked)
  the CPU test            the exact commands against the committed list (tests/test_trackA_gpu_kit.py)
  python finetune/gpu/vllm_options.py --help-file HELP --version V --save FILE    # a list from a help text
"""
import argparse
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))

TRACKED = Path(__file__).resolve().parent / "vllm_serve_options.txt"
NAME = re.compile(r"(?:^|[\s,])(--?[A-Za-z0-9][\w.-]*)")
HELP_TIMEOUT_S = 180


def option_lines(help_text):
    """The option lines of argparse help: indented 2 spaces (descriptions are indented further); the
    invocation ends at the first run of 2 or more spaces, where a description on the same line starts."""
    return [re.split(r"\s{2,}", line.strip())[0] for line in help_text.splitlines() if re.match(r" {2}-", line)]


def options(lines):
    """{option: its choices, or None} from option lines."""
    out = {}
    for line in lines:
        m = re.search(r"\{([^}]*)\}", line)
        for name in NAME.findall(line.split("{")[0]):
            out[name] = m.group(1).split(",") if m else None
    return out


def load(path=TRACKED):
    """(version, {option: choices or None}) from a saved list."""
    text = Path(path).read_text().splitlines()
    version = next((x.split()[2].rstrip(":") for x in text if x.startswith("# vllm ")), None)
    return version, options([x for x in text if x.strip() and not x.startswith("#")])


def save(path, lines, version, source):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(f"# vllm {version}: the option lines of `vllm serve --help=all`\n# {source}\n"
                          + "\n".join(lines) + "\n")


def unknown(cmd, opts):
    """What a vllm serve command uses that the list doesn't have: options, and values outside an
    option's choices."""
    if cmd[1:2] != ["serve"]:
        raise ValueError(f"not a vllm serve command: {cmd[:3]}")
    args, bad = cmd[2:], []
    for i, a in enumerate(args):
        if not a.startswith("-"):
            continue
        name, eq, value = a.partition("=")
        if name not in opts:
            bad.append(name)
        elif opts[name] is not None:
            value = value if eq else (args[i + 1] if i + 1 < len(args) else "")
            if value not in opts[name]:
                bad.append(f"{name} {value} (choices: {','.join(opts[name])})")
    return bad


def problems(commands, opts):
    """["system: option", ...] for every command (label -> argv) and option the list lacks."""
    return [f"{label}: {b}" for label, cmd in commands.items() for b in unknown(cmd, opts)]


def differences(live, committed):
    """How a node's list differs from the committed one: options added, removed, or with other choices."""
    return {"added": sorted(set(live) - set(committed)), "removed": sorted(set(committed) - set(live)),
            "choices": sorted(k for k in set(live) & set(committed) if live[k] != committed[k])}


def job_commands():
    """Track A's servers (evaluation, the check) and Track B's Qwen3-8B server (progress/sol_trackB.py)."""
    sys.path.insert(0, str(CODE / "progress"))
    import sol_trackB
    from finetune.gpu import eval_job
    return {**eval_job.server_commands(), "trackB qwen3-8b": sol_trackB.serve_cmd("SNAPSHOT", template="TEMPLATE")}


def check_commands(installed=None, committed=TRACKED):
    """setup_vllm (CPU): the installed version is the committed list's, and every command fits the list.
    Returns the problems (empty: fine)."""
    version, opts = load(committed)
    out = []
    if installed is not None and installed != version:
        out.append(f"the installed vLLM is {installed}, but the committed option list ({Path(committed).name}) is "
                   f"for {version}: install {version}, or make and commit the list for {installed}")
    return out + problems(job_commands(), opts)


def gpu_preflight(vllm, out_dir, committed=TRACKED, timeout=HELP_TIMEOUT_S):
    """A vLLM GPU job's first step: every command fits the committed list, and `vllm serve --help=all` on
    this node gives exactly that list (options and choices). Exits (SystemExit) otherwise, as soon as
    the help has run."""
    start = time.monotonic()
    version, opts = load(committed)
    bad = problems(job_commands(), opts)
    if bad:
        sys.exit(f"refusing: the committed vLLM {version} list doesn't have these server options:\n  " + "\n  ".join(bad))
    try:
        r = subprocess.run([vllm, "serve", "--help=all"], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as err:
        sys.exit(f"refusing: `{vllm} serve --help=all` didn't finish ({type(err).__name__}: {err})")
    if r.returncode != 0:
        tail = "\n".join((r.stderr or r.stdout).splitlines()[-30:])
        sys.exit(f"refusing: `{vllm} serve --help=all` exited with code {r.returncode} on this node; its last lines:\n{tail}")
    lines = option_lines(r.stdout)
    diff = differences(options(lines), opts)
    if any(diff.values()):
        node = Path(out_dir) / "vllm_serve_options_node.txt"
        save(node, lines, version, f"`vllm serve --help=all` on {socket.gethostname()}; it differs from the "
                                   f"committed list: check before committing it")
        show = "; ".join(f"{k} {len(v)}: {' '.join(v[:8])}" for k, v in diff.items() if v)
        sys.exit(f"refusing: this node's vLLM options differ from the committed {version} list ({show}).\n"
                 f"The node's list is in {node}. If the difference is expected, copy it to the Mac as "
                 f"cot-disclosure/finetune/gpu/vllm_serve_options.txt, run the tests, commit, rsync, resubmit.")
    print(f"vLLM options on this node: exactly the committed {version} list ({len(opts)} options); all "
          f"{len(job_commands())} server commands fit ({time.monotonic() - start:.0f} s)", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check-commands", action="store_true", help="the commands against the committed list (CPU)")
    ap.add_argument("--installed", help="with --check-commands: the installed vLLM version; it must be the list's")
    ap.add_argument("--committed", default=str(TRACKED), help="the committed list (default: %(default)s)")
    ap.add_argument("--list-version", action="store_true", help="print the committed list's vLLM version")
    ap.add_argument("--help-file", help="the output of `vllm serve --help=all`")
    ap.add_argument("--version", help="with --help-file: the vLLM version that printed it")
    ap.add_argument("--save", help="with --help-file: write the option list here")
    a = ap.parse_args()
    if a.list_version:
        print(load(a.committed)[0])
    elif a.check_commands:
        bad = check_commands(a.installed, a.committed)
        version = load(a.committed)[0]
        if bad:
            print(f"refusing (the committed vLLM {version} list):", *bad, sep="\n  ", file=sys.stderr)
            print("Nothing ran on a GPU.", file=sys.stderr)
            sys.exit(1)
        print(f"vLLM {a.installed or version} installed = the committed list's {version}; all "
              f"{len(job_commands())} server commands use only options it lists")
    elif a.help_file and a.save:
        lines = option_lines(Path(a.help_file).read_text())
        if len(lines) < 50 or "--port" not in options(lines):
            sys.exit(f"{a.help_file}: {len(lines)} option lines and no --port; was it `vllm serve --help=all`?")
        save(a.save, lines, a.version, f"saved by vllm_options.py from {a.help_file}")
        print(f"{len(lines)} option lines -> {a.save}")
    else:
        ap.error("give --check-commands, --list-version, or --help-file with --save")


if __name__ == "__main__":
    main()
