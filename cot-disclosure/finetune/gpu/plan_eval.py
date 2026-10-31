"""Track A on Sol: plan batch 3, the evaluation jobs (no GPU, no model: a login node, or the Mac).

  "$TRACKA_PY" finetune/gpu/plan_eval.py --train lora=66759753,tags=66759769,lora_tags=66862721,lora_attn3=66862726
  "$TRACKA_PY" finetune/gpu/plan_eval.py --engine vllm --vllm-check 66878660 --train ...      # optional, later

Engines (finetune/gpu/eval_job.py): hf, Hugging Face generation in the training environment
(finetune/hf_engine.py; the default since Oct 29, when vLLM's engine core failed in its kernel warmup),
needs no vLLM check and runs the tag versions too; vllm, our vLLM server, after a passing check.
Per system (finetune/eval.py): 930 runs, 31 per held-out question. Its tokens: for each run, the mean
reply length Olmo 3 7B Think gave on that question in Step 2b (results/summaries/trackA/
base_format_runs.jsonl, completion tokens, capped at 32,768 with the prompt). 92 of Step 2b's 350 runs
stopped at Voyager's 16,000-token cap and were never continued, so their length is a range: as
recorded (low), the 94 continued runs' mean (mid, 23,547) and the 32,768 cap less the prompt (high).
Runs already saved on Sol ($TRACKA_OUT/eval, every part file) are left out, so the plan can be made
again after any job. Hours = tokens / the decoding rate. The rate is measured once an evaluation job
on the same engine has run (eval_jobs.jsonl: the completion tokens of that job's runs inside its start
and end over the job's seconds, +-20%); until then a prior of PRIORS[engine] tokens/s in all. hf (Oct 29,
from memory traffic, not measured): transformers 5.18's paged SDPA gathers each run's keys and values
into a new tensor and copies it again (.contiguous()) before attention, about 5 passes over them a step;
a run holds ~3.0 GB of them at the 10,522-token average context of a generated token (8 full layers x
16 KiB a token + 24 sliding layers x 16 KiB x 4,096), so 16 in flight move ~254 GB a step with the
weights, ~160 ms at ~1.6 TB/s: ~100 tokens/s, and no more than ~110 with more in flight. vllm: 48
requests in flight. Hours low = low tokens at the high rate; high = high tokens at the low rate; mid =
mid tokens at the middle rate.
Jobs: a system is split into the fewest N parts (eval.py --part k/N, every N-th run, so every part has
some of each question's runs) whose high end x 1.3 is at most 8 h each; each part's --estimate is its own high end, and its limit
that x 1.3 rounded up to 30 minutes (submit.sh does it). The class QoS runs two at once (MaxJobsPU 2;
two 8 h limits are its 960 GPU-minutes) and holds ten (MaxSubmitPU); the rest wait for room.
Order (decided Oct 28): base and prompt_only first (vllm: afterok on the check); each trained version
afterok on its training job. On Sol the plan also reads: squeue (a dependency still queued stays in
--dependency; your job count against MaxSubmitPU), sacct (how a finished dependency ended),
$TRACKA_OUT/train/<version>/final/chosen.json (training done), vllm_check/vllm_check.json (vllm: pass,
the tag versions may use vLLM's prompt embeddings), the saved runs, and the evaluation jobs already in the
queue (sacct's SubmitLine): a system with parts queued keeps their N and gets only its other parts, so a
plan made again never runs a part twice.
"""
import argparse
import getpass
import json
import math
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

STEP2B = CODE / "results" / "summaries" / "trackA" / "base_format_runs.jsonl"
CAP = 32768
PRIORS = {"hf": (70, 120), "vllm": (500, 1500)}      # tokens/s in all, until an evaluation job measures it
CUT_AT = 16000                   # Voyager's cap in Step 2b: a run that stopped there was cut, not finished
MEASURED_SPREAD = 0.2
SAFETY, MAX_LIMIT_H, ROUND_MIN = 1.3, 8.0, 30
MAX_SUBMIT = 10                  # the class QoS's MaxSubmitPU
SUBMIT = "cot-disclosure/finetune/gpu/sol/submit.sh"
FIRST = ("base", "prompt_only")
TRAINED = ("lora", "tags", "lora_tags", "lora_attn3")
TAGGED = ("tags", "lora_tags")


def out_root():
    return Path(os.environ.get("TRACKA_OUT", f"/scratch/{getpass.getuser()}/trackA"))


def step2b_lengths(path=STEP2B):
    """{question id: (low, mid, high) mean reply tokens} from Step 2b's base runs, each capped at 32,768 with
    its prompt; a run cut at Voyager's 16,000 counts as recorded, as the continued runs' mean, and as the cap."""
    rows = [r for r in map(json.loads, Path(path).read_text().splitlines())
            if r.get("status") == "ok" and r.get("completion_tokens") is not None]
    cap = lambda r: CAP - (r.get("prompt_tokens") or 0)  # noqa: E731
    cut = lambda r: r.get("finish_reason") == "length" and r["completion_tokens"] <= CUT_AT < cap(r)  # noqa: E731
    went_on = [min(r["completion_tokens"], cap(r)) for r in rows if "length" in (r.get("continued") or [])]
    mid = sum(went_on) / len(went_on) if went_on else (CUT_AT + CAP) / 2
    by = defaultdict(list)
    for r in rows:
        n = min(r["completion_tokens"], cap(r))
        by[r["item_id"]].append((n, min(mid, cap(r)), cap(r)) if cut(r) else (n, n, n))
    return {q: tuple(sum(x[i] for x in v) / len(v) for i in range(3)) for q, v in by.items()}


def system_tokens(lengths, part=None, system=None, done=frozenset()):
    """Expected reply tokens (low, mid, high) over a system's runs (or one part's) not saved yet."""
    from finetune import eval as ev
    lengths = {q: v if isinstance(v, tuple) else (v, v, v) for q, v in lengths.items()}
    overall = tuple(sum(v[i] for v in lengths.values()) / len(lengths) for i in range(3))
    todo = [j for j in ev.jobs(part) if not done or ev.job_id(system, j) not in done]
    return tuple(sum(lengths.get(j["qid"], overall)[i] for j in todo) for i in range(3))


def saved_runs(system, out=None):
    """The run ids of a system's finished runs on Sol (every part file), or none on the Mac."""
    from common import latest, load
    from finetune import eval as ev
    out = Path(out or out_root() / "eval")
    if not out.exists():
        return frozenset()
    return frozenset(r["run_id"] for r in latest([r for f in ev.runs_files(out, system) for r in load(f)])
                     if r["status"] == "ok")


def engine_of(job_row):
    """hf for a job row from the Hugging Face path (it names its engine), else vllm."""
    return "hf" if job_row.get("engine") in ("continuous", "static") else "vllm"


def measured_rate(out=None, engine="hf"):
    """Tokens/s from finished evaluation jobs on this engine (eval_jobs.jsonl and the runs inside each), or None."""
    from finetune import eval as ev
    out = Path(out or out_root() / "eval")
    jobs_file = out / "eval_jobs.jsonl"
    if not jobs_file.exists():
        return None
    tokens = seconds = 0.0
    for line in jobs_file.read_text().splitlines():
        j = json.loads(line)
        if engine_of(j) != engine:
            continue
        start, end = datetime.fromisoformat(j["started_utc"]), datetime.fromisoformat(j["ended_utc"])
        runs = out / f"{ev.stem(j['system'], tuple(j['part']) if j.get('part') else None)}_runs.jsonl"
        if not runs.exists() or end <= start:
            continue
        n = sum(r.get("completion_tokens") or 0 for r in map(json.loads, runs.read_text().splitlines())
                if start <= datetime.fromisoformat(r["timestamp_utc"]) <= end)
        tokens, seconds = tokens + n, seconds + (end - start).total_seconds()
    return tokens / seconds if seconds > 600 and tokens else None          # at least 10 minutes measured


def limit_min(est):
    return ROUND_MIN * math.ceil(est * 60 * SAFETY / ROUND_MIN - 1e-9)


def split(high_tokens_of, rate_lo):
    """The fewest parts N whose every part's high end x 1.3 fits 8 h: [(k, N, hours high)] for the parts with
    runs left. high_tokens_of(part) gives a part's high-end tokens; N stops at 93 (10 runs a part)."""
    for n in range(1, 94):
        parts = [(k, n, high_tokens_of((k, n) if n > 1 else None) / rate_lo / 3600) for k in range(1, n + 1)]
        if max(h for *_, h in parts) * SAFETY <= MAX_LIMIT_H or n == 93:
            return [p for p in parts if p[2] > 0]


def estimate(hours_high):
    """--estimate for a part (hours, rounded up to 0.01, never over the 8 h limit's share)."""
    return min(math.ceil(hours_high * 100) / 100, math.floor(MAX_LIMIT_H / SAFETY * 100) / 100)


# ---------------------------------------------------------------- what Sol says (each None on the Mac)
def _run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def queued(job):
    """'RUNNING' / 'PENDING' / '' (not in the queue), or None without squeue."""
    out = _run(["squeue", "-h", "-j", str(job), "-o", "%T"])
    return None if out is None else out.splitlines()[0] if out else ""


def ended(job):
    """How a job that left the queue ended (sacct), e.g. COMPLETED, FAILED, TIMEOUT; None if unknown."""
    out = _run(["sacct", "-n", "-X", "-j", str(job), "-o", "State"])
    return out.split()[0] if out else None


EVAL_LINE = re.compile(r"eval\.sbatch\s+(\S+)(?:\s+(\d+)/(\d+))?")


def queued_evals():
    """{system: {(k, n), or None for the whole system}} of your evaluation jobs pending or running (sacct's
    SubmitLine; submit.sh puts the system and part after eval.sbatch), or None without sacct."""
    out = _run(["sacct", "-n", "-X", "-P", "-u", os.environ.get("USER", ""), "-s", "PENDING,RUNNING,REQUEUED",
                "-o", "JobName,SubmitLine"])
    if out is None:
        return None
    q = defaultdict(set)
    for line in out.splitlines():
        m = EVAL_LINE.search(line)
        if m and line.startswith("trackA-eval"):
            q[m[1]].add((int(m[2]), int(m[3])) if m[2] else None)
    return dict(q)


def job_count():
    out = _run(["squeue", "-h", "-u", os.environ.get("USER", ""), "-o", "%i"])
    return None if out is None else len(out.splitlines())


def trained(version):
    return (out_root() / "train" / version / "final" / "chosen.json").exists()


def check_result():
    """vllm_check.json's pass (True / False), or None before the check has run."""
    p = out_root() / "vllm_check" / "vllm_check.json"
    return json.loads(p.read_text()).get("pass") if p.exists() else None


# ---------------------------------------------------------------- the plan
def dependency(job, kind, sol):
    """(the id to wait for, or None when it is done; a problem, or None)."""
    state = sol["queued"](job)
    if state is None or state in ("RUNNING", "PENDING"):
        return job, None                                     # on the Mac (no squeue): keep it
    how = sol["ended"](job)
    if how == "COMPLETED":
        return None, None
    return None, f"{kind} job {job} ended {how or 'unknown'}"


def plan(vllm_check, train_jobs, sol=None, lengths=None, engine="hf"):
    sol = sol or {"queued": queued, "ended": ended, "job_count": job_count, "trained": trained, "check": check_result,
                  "rate": lambda e: measured_rate(engine=e), "saved": saved_runs, "in_queue": queued_evals}
    lengths = lengths or step2b_lengths()
    rate = sol["rate"](engine)
    lo, hi = ((rate * (1 - MEASURED_SPREAD), rate * (1 + MEASURED_SPREAD)) if rate else PRIORS[engine])
    res = {"engine": engine, "rate": {"measured": rate, "range": [lo, hi]}, "systems": [], "notes": []}
    in_queue = sol["in_queue"]() or {}
    check_dep = passed = None
    if engine == "vllm":
        if not vllm_check:
            res["notes"].append("--engine vllm needs --vllm-check JOB: every vLLM evaluation waits for a passing check")
            return res
        check_dep, check_problem = dependency(vllm_check, "vllm_check", sol)
        if check_problem:
            res["notes"].append(f"{check_problem}: every vLLM evaluation waits for a passing vLLM check "
                                f"(or plan --engine hf)")
            return res
        passed = sol["check"]()
    for system in FIRST + TRAINED:
        deps = [check_dep] if check_dep else []
        if system in TRAINED:
            if system not in train_jobs:
                res["notes"].append(f"{system}: no training job given")
                continue
            if not sol["trained"](system):
                t_dep, problem = dependency(train_jobs[system], "train", sol)
                if problem:
                    res["notes"].append(f"{system}: {problem} before its final/ was written: resubmit "
                                        f"`{SUBMIT} train --estimate E -- {system}` (it resumes); its evaluation waits")
                    continue
                if t_dep is None:
                    res["notes"].append(f"{system}: its training job completed without final/: check its log")
                    continue
                deps.append(t_dep)
        if engine == "vllm" and system in TAGGED and passed is False:
            res["notes"].append(f"{system}: the vLLM check failed: tag versions need the hf engine (plan --engine hf)")
            continue
        done = sol["saved"](system)
        t_lo, t_mid, t_hi = system_tokens(lengths, system=system, done=done)
        if not t_hi:
            res["notes"].append(f"{system}: all 930 runs saved")
            continue
        hours = [t_lo / hi / 3600, t_mid / ((lo + hi) / 2) / 3600, t_hi / lo / 3600]
        high_of = lambda p: system_tokens(lengths, p, system, done)[2]  # noqa: E731
        queued_parts = in_queue.get(system, set())
        if None in queued_parts or len({p[1] for p in queued_parts}) > 1:
            res["notes"].append(f"{system}: a whole-system job or parts of different N are queued: nothing planned")
            continue
        if queued_parts:
            n = next(iter(queued_parts))[1]
            parts = [(k, n, high_of((k, n)) / lo / 3600) for k in range(1, n + 1) if (k, n) not in queued_parts]
            parts = [p for p in parts if p[2] > 0]
            res["notes"].append(f"{system}: {len(queued_parts)} of its {n} parts are queued; the others keep N = {n}")
            if not parts:
                continue
        else:
            parts = split(high_of, lo)
        res["systems"].append({"system": system, "saved": len(done), "tokens": [round(t) for t in (t_lo, t_mid, t_hi)],
                               "hours": [round(h, 2) for h in hours],
                               "parts": [{"part": [k, n], "estimate": estimate(h), "limit_min": limit_min(estimate(h))}
                                         for k, n, h in parts], "after": deps})
    count = sol["job_count"]()
    res["queue"] = {"jobs_now": count, "room": None if count is None else MAX_SUBMIT - count}
    res["gpu_hours"] = [round(sum(s["hours"][i] for s in res["systems"]), 1) for i in range(3)]
    return res


def commands(res):
    lo, hi = res["rate"]["range"]
    src = f"measured {res['rate']['measured']:.0f}" if res["rate"]["measured"] else "prior (no evaluation job measured yet)"
    g = res.get("gpu_hours") or [0, 0, 0]
    lines = [f"# batch 3, evaluation, engine {res['engine']}: decoding {lo:.0f}-{hi:.0f} tokens/s, {src}; "
             f"{g[0]:.0f}-{g[2]:.0f} GPU h in all (mid {g[1]:.0f}); two run at once, ten in the queue"]
    room, n = res["queue"]["room"], 0
    for s in res["systems"]:
        dep = f" --dependency=afterok:{':'.join(str(d) for d in s['after'])}" if s["after"] else ""
        engine = " --engine vllm" if res["engine"] == "vllm" else ""
        many = len(s["parts"]) > 1 or s["parts"][0]["part"][1] > 1
        for p in s["parts"]:
            k, m = p["part"]
            part = f" {k}/{m}" if many else ""
            lim = f"{p['limit_min'] // 60}:{p['limit_min'] % 60:02d}"
            later = room is not None and n >= room
            lines.append(f"{'# later (MaxSubmitPU): ' if later else ''}{SUBMIT} eval --estimate {p['estimate']:.2f}{dep} -- "
                         f"{s['system']}{part}{engine}     # limit {lim}; {s['system']} {s['hours'][0]:.1f}-{s['hours'][2]:.1f} h "
                         f"(mid {s['hours'][1]:.1f}) in {m} part(s)" + (f", {s['saved']} runs saved" if s["saved"] else ""))
            n += 1
    lines += [f"# note: {x}" for x in res["notes"]]
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engine", choices=["hf", "vllm"], default="hf", help="hf (default, Oct 29) or vllm (after a passing check)")
    ap.add_argument("--vllm-check", help="the vLLM check's job id (--engine vllm only)")
    ap.add_argument("--train", required=True, help="VERSION=JOB,... the training jobs")
    ap.add_argument("--json", help="also write the plan here (numbers only)")
    a = ap.parse_args()
    res = plan(a.vllm_check, dict(x.split("=", 1) for x in a.train.split(",")), engine=a.engine)
    print("\n".join(commands(res)))
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
