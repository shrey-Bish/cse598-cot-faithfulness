"""Track B, B17 (Oct 31): the thinking dose. One set of weights at three amounts of thinking: gpt-oss-20b
(openai/gpt-oss-20b, Apache 2.0, not gated) on our vLLM server in a Sol job, at reasoning effort low, medium and
high. Pre-registered in archive/sessions/2026-10-31/2026-10-31_2237_B_b17-prereg.md.

  python progress/run_b17.py --dry-run           # jobs and GPU hours (no calls)
  python progress/run_b17.py --report            # the pre-registered comparisons, from the numbers-only flags
  python progress/run_b17.py --smoke-check       # the smoke job's verdict, from the numbers-only run rows
  python progress/run_b17.py --run [--limit N]   # inside the Sol job only (progress/sol_b17.py starts the server)

Track B's design (configs/trackB.yaml): the 24 pilot puzzles and the 30 MMLU-Pro items, conditions none / user /
tool_pasted / tool_real / system, 3 runs, temperature 0.6, seed = run, one 32,768-token budget (prompt + every reply),
the tool left to the model; x 3 efforts = 2,430 runs (810 a level). The effort goes in every request
(reasoning_effort; vLLM renders gpt-oss's harmony system message with it: "Reasoning: low"). Jobs go repeat by repeat,
each question in every effort and condition before any second run, so --limit 15 is the first question (a pilot
puzzle) in all 15 cells: the smoke test, whose runs are the design's first 15 and count. Records:
results/trackB/b17_sol_vllm.jsonl.gz and b17_sol_vllm_runs.jsonl (experiment "b17"; on Sol, the text never leaves it).
Numbers-only flags: results/trackB/b17/b17_flags.jsonl, in a subfolder so Track B's table never reads them.

Report (following = an answered run ends on the hint's letter; bare = a final answer of 30 characters or fewer,
F15's measure; a bootstrap clustered by question, 95%):
  primary          high minus low, paired by question, on (1) following on the real tool call (tool_real, answered
                   runs, called or not: the channel's effect) and (2) the bare final answer after a call (tool_real
                   runs that called the tool and answered). Each: rises with effort (the interval lies above 0),
                   falls (below 0), or no change detected (it includes 0). Read at the run's own budget.
  secondary        medium minus low and high minus medium on both (no decision); per effort: following per channel,
                   Gate 2 (each tool channel minus user, Track B's gap), the call rate, following when called, no-hint
                   accuracy, the final answer naming the tool, output tokens; the 16,000 cut beside all of it; the bare
                   final answer over every called run (F15's and B15's denominator, cut-off runs included).
Fewer than 5 questions behind an interval: "too few questions".
"""
import argparse
import json
import re
import statistics
import sys
from pathlib import Path

import yaml

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

import run_trackB as tb  # noqa: E402
from common import boot_diff, latest, load, run_id, too_few, wilson  # noqa: E402
from tools.answer_key import build  # noqa: E402
import trackB_report as tbr  # noqa: E402

EXPERIMENT = "b17"
MODEL = "gpt-oss-20b"
EFFORTS = ("low", "medium", "high")
SETS = ("pilot_puzzles", "mmlupro_30")
PRIMARY = ("high", "low")                                    # the pre-registered contrast
SECONDARY = (("medium", "low"), ("high", "medium"))
OUT = tb.OUT / "b17"
FLAGS = OUT / "b17_flags.jsonl"
SMOKE_JOBS = 15                                              # one question x 5 conditions x 3 efforts
# Planning assumptions for the dry run only (not measured; the smoke job measures them): mean output tokens a run
# (every turn), and the server's generated tokens/s on one A100 with Track B's 48 in flight. Qwen3-8B on the same
# kind of server (Oct 30, 66954217) generated 6.35M tokens in about 2 h: ~880 tokens/s.
TOKENS = {"low": 1500, "medium": 4000, "high": 9000}
RATE = (600, 900)


def models():
    """The three B17 models: one checkpoint, one effort each."""
    return [{"provider": "sol_vllm", "model": MODEL, "effort": e} for e in EFFORTS]


def jobs(cfg):
    """Every job, repeat by repeat: each question's first run in every effort and condition before any second run."""
    items = [it for s in SETS for it in tb.load_questions(s, cfg["question_sets"][s])]
    out = []
    for rep in range(cfg["runs_per_question"]):
        for item in items:
            for m in models():
                for cond in cfg["conditions"]:
                    out.append({"run_id": run_id(EXPERIMENT, item["item_id"], tb.model_tag(m), cond, None, rep),
                                "model": m, "item": item, "condition": cond, "repeat": rep, "experiment": EXPERIMENT})
    return out


def gpu_hours(todo):
    """(low, high) GPU hours for these jobs from the planning assumptions (TOKENS, RATE)."""
    tokens = sum(TOKENS[j["model"]["effort"]] for j in todo)
    return tokens / RATE[1] / 3600, tokens / RATE[0] / 3600


def dry_run(cfg, todo):
    print(f"B17: {len(todo)} jobs to run (gpt-oss-20b x {len(EFFORTS)} efforts x {len(cfg['conditions'])} conditions x "
          f"{len(SETS)} sets x {cfg['runs_per_question']} runs); {cfg['sol_in_flight']} in flight on one A100")
    for e in EFFORTS:
        mine = [j for j in todo if j["model"]["effort"] == e]
        lo, hi = gpu_hours(mine)
        print(f"  effort {e:6} {len(mine):5,} jobs  ~{TOKENS[e]:,} output tokens a run (assumed)  {lo:4.1f}-{hi:4.1f} GPU h")
    lo, hi = gpu_hours(todo)
    print(f"  all           {len(todo):5,} jobs  {sum(TOKENS[j['model']['effort']] for j in todo) / 1e6:.1f}M tokens at "
          f"{RATE[0]}-{RATE[1]} tokens/s: {lo:.1f}-{hi:.1f} GPU h, free (the smoke job measures both)")


# ---------------------------------------------------------------- the served-template check (in the job)
def template_rows(cfg):
    """The 15 first-turn prompts the check sends: the first question in every condition and effort."""
    item = tb.load_questions(SETS[0], cfg["question_sets"][SETS[0]])[0]
    rows = []
    for effort in EFFORTS:
        for cond in cfg["conditions"]:
            msgs, tools = build(item["question"], item["item_id"], cond, None if cond == "none" else item["hint_letter"])
            rows.append({"effort": effort, "condition": cond, "messages": msgs, "tools": tools})
    return rows


def compare_ids(server, local, decode):
    """How the server's prompt token ids (vLLM's harmony rendering) differ from ours (the snapshot's chat template):
    identical; whitespace only (the decoded texts equal once runs of whitespace are collapsed); or differs, with the
    first differing position and the decoded text around it on each side."""
    out = {"server_tokens": len(server), "local_tokens": len(local), "gap": len(server) - len(local)}
    if server == local:
        return {**out, "verdict": "identical"}
    s, t = decode(server), decode(local)
    if re.sub(r"\s+", " ", s).strip() == re.sub(r"\s+", " ", t).strip():
        return {**out, "verdict": "whitespace only"}
    i = next((k for k, (a, b) in enumerate(zip(server, local)) if a != b), min(len(server), len(local)))
    return {**out, "verdict": "differs", "first_difference": i, "server_text": decode(server[max(0, i - 8):i + 24]),
            "local_text": decode(local[max(0, i - 8):i + 24])}


def template_check(cfg, server_ids, local_ids, decode):
    """B10's check, token for token: server_ids(effort, messages, tools) -> the prompt token ids vLLM rendered
    (return_token_ids, max_tokens 1); local_ids(effort, messages, tools) -> ours. Passes when no prompt differs
    beyond whitespace; else the job stops before any run (sol_b17.py)."""
    rows = []
    for r in template_rows(cfg):
        cmp = compare_ids(server_ids(r["effort"], r["messages"], r["tools"]), local_ids(r["effort"], r["messages"], r["tools"]),
                          decode)
        rows.append({"effort": r["effort"], "condition": r["condition"], **cmp})
    return {"ok": not any(r["verdict"] == "differs" for r in rows), "rows": rows,
            "rule": "every first-turn prompt (5 conditions x 3 efforts) identical to the snapshot's chat template, or "
                    "differing in whitespace only"}


# ---------------------------------------------------------------- the smoke job's verdict
def smoke_check(rows):
    """The smoke job's verdict from the run rows (b17_sol_vllm_runs.jsonl; numbers only): the first SMOKE_JOBS jobs
    of the design all ran (status ok); the tool path ran (at least 1 of the 3 tool_real runs called the tool and
    answered); the effort reaches the model (median output tokens over the 5 conditions rise from low to high)."""
    first = {j["run_id"]: j for j in jobs(yaml.safe_load(open(tb.CONFIG)))[:SMOKE_JOBS]}
    got = {r["run_id"]: r for r in latest(rows) if r["run_id"] in first}
    ok = [r for r in got.values() if r["status"] == "ok"]
    real = [r for r in ok if r["condition"] == "tool_real"]
    tokens = {e: [r.get("total_output_tokens") or 0 for r in ok if r.get("effort") == e] for e in EFFORTS}
    med = {e: statistics.median(v) if v else None for e, v in tokens.items()}
    checks = {"all ran": len(ok) == SMOKE_JOBS,
              "tool path ran": any(r["called_tool"] and r["parsed_letter"] for r in real),
              "effort reaches the model": None not in med.values() and med["high"] > med["low"]}
    return {"ok": all(checks.values()), "checks": checks, "jobs": len(first), "ran": len(got), "status_ok": len(ok),
            "statuses": {s: sum(r["status"] == s for r in got.values()) for s in {r["status"] for r in got.values()}},
            "tool_real_called": sum(bool(r["called_tool"]) for r in real), "tool_real": len(real),
            "answered": sum(bool(r["parsed_letter"]) for r in ok),
            "cut_off": sum(r.get("finish_reason") == "length" for r in ok), "median_output_tokens": med}


# ---------------------------------------------------------------- flags and the report
def export_flags(records=tb.OUT / "b17_sol_vllm.jsonl.gz", out=FLAGS):
    """Every finished record's numbers-only flags with its effort, rewritten in full (a derived copy)."""
    rows = [{**tbr.flags(r), "effort": r.get("effort"), "experiment": EXPERIMENT} for r in latest(load(records))
            if r.get("experiment") == EXPERIMENT and r["status"] == "ok" and tbr.counts(r)] if Path(records).exists() else []
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("".join(json.dumps(r) + "\n" for r in rows))
    return len(rows)


def by_item(rows, f):
    g = {}
    for r in rows:
        g.setdefault(r["item_id"], []).append(int(bool(f(r))))
    return g


def rate(rows, f):
    k, n = sum(bool(f(r)) for r in rows), len(rows)
    return {"k": k, "n": n, "wilson": wilson(k, n), "questions": len({r["item_id"] for r in rows})}


def compare(a_rows, b_rows, f):
    """a minus b on outcome f, paired by question (boot_diff over the questions both have), as B15's paired one."""
    a, b = by_item(a_rows, f), by_item(b_rows, f)
    out = {"with": rate(a_rows, f), "without": rate(b_rows, f)}
    if not (a and b) or too_few(a, b):
        return {**out, "diff": None, "interval": "too few questions"}
    d, lo, hi = boot_diff(a, b)
    return {**out, "diff": d, "interval": [lo, hi]}


def reading(e):
    if e["diff"] is None:
        return "too few questions"
    lo, hi = e["interval"]
    return "rises with effort" if lo > 0 else "falls with effort" if hi < 0 else "no change detected"


def following(rows):
    return [r for r in rows if r["condition"] == "tool_real" and r["answered"]]


def after_call(rows):
    return [r for r in rows if r["condition"] == "tool_real" and r["called_tool"] and r["answered"]]


def contrast(by, hi, lo):
    """hi minus lo on the two pre-registered outcomes, paired by question."""
    f = compare(following(by[hi]), following(by[lo]), lambda r: r["followed"])
    b = compare(after_call(by[hi]), after_call(by[lo]), lambda r: r["final_chars"] <= tbr.BARE_CHARS)
    return {"following_tool_real": {**f, "reading": reading(f)}, "bare_after_call": {**b, "reading": reading(b)}}


def report(rows):
    by = {e: [r for r in rows if r.get("effort") == e] for e in EFFORTS}
    cut = {e: tbr.cut(v) for e, v in by.items()}
    out = {"runs": {e: len(v) for e, v in by.items()}, "primary": {f"{PRIMARY[0]} - {PRIMARY[1]}": contrast(by, *PRIMARY)},
           "secondary": {f"{a} - {b}": contrast(by, a, b) for a, b in SECONDARY},
           "cut_16000": {f"{a} - {b}": contrast(cut, a, b) for a, b in (PRIMARY, *SECONDARY)},
           "per_effort": {}, "per_effort_cut_16000": {}}
    for e in EFFORTS:
        if not by[e]:
            continue
        rep = tbr.model_report(by[e])
        called = [r for r in by[e] if r["condition"] == "tool_real" and r["called_tool"]]
        rep["bare_after_call_all_called"] = tbr.bare(called)
        rep["median_output_tokens"] = statistics.median(r.get("total_output_tokens") or 0 for r in by[e])
        out["per_effort"][e] = rep
        out["per_effort_cut_16000"][e] = tbr.model_report(cut[e])
    return out


def show(res):
    def d(x):
        return ("too few questions" if x["diff"] is None
                else f"{x['diff']:+.0%} [{x['interval'][0]:+.0%}, {x['interval'][1]:+.0%}]")

    def f(x):
        return f"{x['k']} of {x['n']} ({x['questions']} q)"
    lines = [f"B17 runs per effort: {res['runs']}"]
    for block in ("primary", "secondary", "cut_16000"):
        for name, e in res[block].items():
            for k, x in e.items():
                lines.append(f"  {block:9} {name:13} {k:20} {f(x['with'])} vs {f(x['without'])}: {d(x)} -> {x['reading']}")
    for e, rep in res["per_effort"].items():
        ch = rep["channels"]
        lines.append(f"  {e:6} following: " + ", ".join(f"{c} {v['following']['k']}/{v['following']['n']}" for c, v in ch.items())
                     + f"; call rate {ch.get('tool_real', {}).get('tool_call_rate', {}).get('k')}/"
                       f"{ch.get('tool_real', {}).get('tool_call_rate', {}).get('n')}; median output tokens "
                       f"{rep['median_output_tokens']:.0f}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--run", action="store_true", help="inside the Sol job (progress/sol_b17.py)")
    mode.add_argument("--report", action="store_true")
    mode.add_argument("--smoke-check", action="store_true")
    ap.add_argument("--limit", type=int, help="run at most N jobs (the smoke test: 15)")
    ap.add_argument("--stop-file", help="start no new job once this file exists (Slurm's warning)")
    ap.add_argument("--flags", default=str(FLAGS), help="the numbers-only flags (default: %(default)s)")
    a = ap.parse_args()
    cfg = yaml.safe_load(open(tb.CONFIG))
    if a.report:
        rows = latest(load(a.flags))
        if not rows:
            sys.exit(f"no B17 flags in {a.flags}: copy results/trackB/b17/ back from Sol first")
        OUT.mkdir(parents=True, exist_ok=True)
        res = report(rows)
        (OUT / "b17_report.json").write_text(json.dumps(res, indent=1) + "\n")
        print(show(res))
        return
    if a.smoke_check:
        res = smoke_check(load(tb.runs_path("sol_vllm", EXPERIMENT)))
        print(json.dumps(res, indent=1))
        return 0 if res["ok"] else 5
    all_jobs = jobs(cfg)
    if a.dry_run:
        finished = tb.done("sol_vllm", EXPERIMENT)
        return dry_run(cfg, [j for j in all_jobs if j["run_id"] not in finished])
    tb.OUT.mkdir(parents=True, exist_ok=True)
    return tb.run(cfg, all_jobs, a.limit, a.stop_file)


if __name__ == "__main__":
    sys.exit(main() or 0)
