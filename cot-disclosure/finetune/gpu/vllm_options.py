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
                          `vllm serve --help=all` on the GPU node. The job stops only if an option a
                          server command uses is missing there, a value it passes isn't among the
                          node's choices, or the option changed form (a flag on one list, taking a
                          value on the other). Any other difference (Oct 28: --mm-processor-device
                          has a cuda choice on a GPU node, not on the Mac's CPU) is a warning in the
                          log, and the node's list is saved to copy back. Up to 15 minutes; past
                          that, Python's traceback shows where vLLM was (a slow import or a hang)
  the CPU test            the exact commands against the committed list (tests/test_trackA_gpu_kit.py)
  python finetune/gpu/vllm_options.py --help-file HELP --version V --save FILE    # a list from a help text
"""
import argparse
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))

TRACKED = Path(__file__).resolve().parent / "vllm_serve_options.txt"
NAME = re.compile(r"(?:^|[\s,])(--?[A-Za-z0-9][\w.-]*)")
HELP_TIMEOUT_S = 900          # Oct 28: 180 s ran out on sg002, the first vLLM import on Sol (the server gets 1,800 s)


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


def forms(lines):
    """{option: True if it takes a value, False for a flag} from option lines ("--port PORT",
    "--enable-lora, --no-enable-lora", "--dtype {auto,...}")."""
    out = {}
    for line in lines:
        for part in re.split(r",\s+(?=-)", line.split(" or ")[0]):
            tokens = part.split()
            if tokens and tokens[0].startswith("-"):
                out[tokens[0]] = len(tokens) > 1
    return out


def read(path=TRACKED):
    """(version, the option lines) of a saved list."""
    text = Path(path).read_text().splitlines()
    version = next((x.split()[2].rstrip(":") for x in text if x.startswith("# vllm ")), None)
    return version, [x for x in text if x.strip() and not x.startswith("#")]


def load(path=TRACKED):
    """(version, {option: choices or None}) from a saved list."""
    version, lines = read(path)
    return version, options(lines)


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


def used(commands):
    """The options the server commands use."""
    return {a.partition("=")[0] for cmd in commands.values() for a in cmd[2:] if a.startswith("-")}


def node_check(commands, node_lines, committed_lines):
    """(refusals, warnings) for a node's list. Refused: an option a command uses is missing on the node,
    a value it passes isn't among the node's choices, or the option changed form (a flag on one list,
    taking a value on the other). Every other difference from the committed list is a warning,
    including other choices of an option we use when our value is still among them."""
    node, committed = options(node_lines), options(committed_lines)
    node_form, committed_form = forms(node_lines), forms(committed_lines)
    ours = used(commands)
    refuse = problems(commands, node) + [
        f"{name}: {'takes a value' if committed_form[name] else 'a flag'} in the committed list, "
        f"{'takes a value' if node_form[name] else 'a flag'} on this node"
        for name in sorted(ours) if name in node_form and name in committed_form and node_form[name] != committed_form[name]]
    warn = {k: [x for x in v if not (x in ours and k != "choices")] for k, v in differences(node, committed).items()}
    return refuse, {k: v for k, v in warn.items() if v}


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


DUMP_HOOK = "import faulthandler, signal\nfaulthandler.register(signal.SIGUSR1, all_threads=True)\n"
DUMP_WAIT_S = 5               # after SIGUSR1, the time the traceback gets before the kill


def run_help(vllm, timeout):
    """`vllm serve --help=all`. Past the timeout it gets SIGUSR1, which Python's faulthandler (registered
    by a sitecustomize put first on its path) answers with every thread's traceback, even inside C code;
    then it is killed, and the refusal carries that traceback: where it was (Oct 28: the job said only
    TimeoutExpired). Not SIGABRT: on the Mac every abort is a "Python quit unexpectedly" crash report
    (Oct 28: one per run of the test's fake vLLM)."""
    with tempfile.TemporaryDirectory() as hook:
        Path(hook, "sitecustomize.py").write_text(DUMP_HOOK)
        path = os.pathsep.join(x for x in (hook, os.environ.get("PYTHONPATH")) if x)
        proc = subprocess.Popen([vllm, "serve", "--help=all"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                env={**os.environ, "PYTHONFAULTHANDLER": "1", "PYTHONPATH": path})
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.send_signal(signal.SIGUSR1)
            try:
                out, err = proc.communicate(timeout=DUMP_WAIT_S)
            except subprocess.TimeoutExpired:
                proc.kill()
                out, err = proc.communicate()
            timed_out = True
        else:
            timed_out = False
    if timed_out:
        stack = "\n".join((err or "").split("Current thread's C stack trace")[0].strip().splitlines()[:120])
        sys.exit(f"refusing: `{vllm} serve --help=all` didn't finish in {timeout} s on {socket.gethostname()}; "
                 f"where it was (its Python traceback, most recent call first):\n{stack or '(nothing on stderr)'}")
    return subprocess.CompletedProcess(proc.args, proc.returncode, out, err)


def gpu_preflight(vllm, out_dir, committed=TRACKED, timeout=HELP_TIMEOUT_S):
    """A vLLM GPU job's first step: every command fits the committed list, and on this node's
    `vllm serve --help=all` every option and value the commands use is there, in the same form
    (node_check). Exits (SystemExit) otherwise, as soon as the help has run; any other difference is a
    warning in the log."""
    start = time.monotonic()
    version, committed_lines = read(committed)
    opts = options(committed_lines)
    commands = job_commands()
    bad = problems(commands, opts)
    if bad:
        sys.exit(f"refusing: the committed vLLM {version} list doesn't have these server options:\n  " + "\n  ".join(bad))
    try:
        r = run_help(vllm, timeout)
    except OSError as err:
        sys.exit(f"refusing: `{vllm} serve --help=all` didn't start ({type(err).__name__}: {err})")
    if r.returncode != 0:
        tail = "\n".join((r.stderr or r.stdout).splitlines()[-30:])
        sys.exit(f"refusing: `{vllm} serve --help=all` exited with code {r.returncode} on this node; its last lines:\n{tail}")
    lines = option_lines(r.stdout)
    refuse, warn = node_check(commands, lines, committed_lines)
    node = Path(out_dir) / "vllm_serve_options_node.txt"
    if refuse or warn:
        save(node, lines, version, f"`vllm serve --help=all` on {socket.gethostname()}; it differs from the "
                                   f"committed list: check before committing it")
    if refuse:
        sys.exit(f"refusing: on this node, vLLM lacks or changed what the server commands use (committed "
                 f"{version} list):\n  " + "\n  ".join(refuse) + f"\nThe node's list is in {node}.")
    took = f"({time.monotonic() - start:.0f} s)"
    if warn:
        show = "; ".join(f"{k} {len(v)}: {' '.join(v[:8])}" for k, v in warn.items())
        print(f"WARNING: this node's vLLM options differ from the committed {version} list ({show}), but not "
              f"in any option or value the {len(commands)} server commands use: going on {took}. The node's "
              f"list is in {node}; copy it to the Mac as cot-disclosure/finetune/gpu/vllm_serve_options.txt "
              f"and commit it when convenient.", flush=True)
        return
    print(f"vLLM options on this node: exactly the committed {version} list ({len(opts)} options); all "
          f"{len(commands)} server commands fit {took}", flush=True)


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
