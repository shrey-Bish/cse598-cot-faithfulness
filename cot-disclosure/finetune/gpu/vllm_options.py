"""Every vllm serve command a Track A job starts, checked against the installed vLLM's own option list
before any GPU work (Oct 27: vLLM 0.31.0 dropped --disable-log-requests, and the vLLM check job
failed on a GPU after 12 minutes).

  vllm serve --help=all > HELP          # the full list; a plain --help shows only the option groups
  python finetune/gpu/vllm_options.py --help-file HELP --version 0.31.0 --save OUT/vllm_serve_options.txt
  python finetune/gpu/vllm_options.py --check OUT/vllm_serve_options.txt

setup_vllm.sh runs the first two on Sol (CPU only) and fails there if a command uses an option the
installed vLLM doesn't list; eval_job.py checks the saved list again at the start of every job.
A saved list: a "# vllm VERSION" line, then the option lines of the help ("--dtype {auto,bfloat16,...}",
"--enable-lora, --no-enable-lora", "--port PORT"). finetune/gpu/vllm_serve_options.txt (tracked) is
0.31.0's, for the CPU test (tests/test_trackA_gpu_kit.py); setup_vllm.sh says whether Sol's matches it.
"""
import argparse
import re
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))

TRACKED = Path(__file__).resolve().parent / "vllm_serve_options.txt"
NAME = re.compile(r"(?:^|[\s,])(--?[A-Za-z0-9][\w.-]*)")


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


def load(path):
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


def job_commands():
    from finetune.gpu import eval_job
    return eval_job.server_commands()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--help-file", help="the output of `vllm serve --help=all`")
    ap.add_argument("--version", help="the installed vLLM's version (with --help-file)")
    ap.add_argument("--save", help="write the option list here (with --help-file)")
    ap.add_argument("--check", help="check the job commands against a saved list")
    a = ap.parse_args()
    if not (a.help_file or a.check) or (a.save and not a.help_file):
        ap.error("give --help-file (and --save) or --check")
    if a.help_file:
        lines = option_lines(Path(a.help_file).read_text())
        if len(lines) < 50 or "--port" not in options(lines):
            sys.exit(f"{a.help_file}: {len(lines)} option lines and no --port; was it `vllm serve --help=all`?")
        version, opts = a.version, options(lines)
    else:
        version, opts = load(a.check)
    commands = job_commands()
    bad = problems(commands, opts)
    if bad:
        print(f"refusing: vLLM {version} doesn't list these server options:", *bad, sep="\n  ", file=sys.stderr)
        print("Fix finetune/generate.py serve_cmd; nothing ran on a GPU.", file=sys.stderr)
        sys.exit(1)
    print(f"vLLM {version}: all {len(commands)} server commands use only options it lists ({len(opts)} options)")
    if a.save:
        save(a.save, lines, version, f"saved by vllm_options.py from {a.help_file}")
        if TRACKED.exists():
            t_version, tracked = load(TRACKED)
            added, removed = sorted(set(opts) - set(tracked)), sorted(set(tracked) - set(opts))
            if (t_version, added, removed) == (version, [], []):
                print(f"the same options as the tracked list ({TRACKED.relative_to(CODE)})")
            else:
                print(f"differs from the tracked list (vLLM {t_version}): {len(added)} more, {len(removed)} fewer"
                      f"{': ' + ' '.join(removed[:10]) if removed else ''}. Copy it to the Mac and commit it:\n"
                      f"  rsync <sol>:{a.save} cot-disclosure/finetune/gpu/vllm_serve_options.txt")


if __name__ == "__main__":
    main()
