"""Track A on Sol: plan batch 3, the evaluation jobs (no GPU, no model: a login node, or the Mac).

  "$TRACKA_PY" finetune/gpu/plan_eval.py --vllm-check 66760726 \\
      --train lora=66759753,tags=66759769,lora_tags=66759772,lora_attn3=66759822

Per system (finetune/eval.py): 930 runs, 31 per held-out question. Its tokens: for each run, the mean
reply length Olmo 3 7B Think gave on that question in Step 2b (results/summaries/trackA/
base_format_runs.jsonl, completion tokens, capped at 32,768 with the prompt). Hours = tokens / the
decoding rate. The rate is measured once an evaluation job has run (eval_jobs.jsonl: the completion
tokens of a system's runs inside each job's start and end over the job's seconds, +-20%); until then
a prior of PRIOR tokens/s in all (48 requests in flight on one A100; Voyager gave ~50 a stream in Step
2b). The range's high end comes from the low rate.
Jobs: a system whose high end x 1.3 is over 8 h is split by question into N parts (eval.py --part
k/N, every N-th question), so each part's high end x 1.3 is at most 8 h; limit = that, rounded up to
30 minutes (submit.sh does it from --estimate).
Order (decided Oct 28): base and prompt_only first, afterok on the vLLM check; each trained version
afterok on its training job and the check. On Sol the plan also reads: squeue (a dependency still
queued stays in --dependency; your job count against MaxSubmitPU), sacct (how a finished dependency
ended), $TRACKA_OUT/train/<version>/final/chosen.json (training done) and vllm_check/vllm_check.json
(pass: the tag versions may use vLLM's prompt embeddings).
"""
import argparse
import json
import math
import os
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
PRIOR = (500, 1500)              # tokens/s in all, until an evaluation job measures it
MEASURED_SPREAD = 0.2
SAFETY, MAX_LIMIT_H, ROUND_MIN = 1.3, 8.0, 30
MAX_SUBMIT = 10                  # the class QoS's MaxSubmitPU
SUBMIT = "cot-disclosure/finetune/gpu/sol/submit.sh"
FIRST = ("base", "prompt_only")
TRAINED = ("lora", "tags", "lora_tags", "lora_attn3")
TAGGED = ("tags", "lora_tags")


def out_root():
    return Path(os.environ.get("TRACKA_OUT", "/scratch/ragarw68/trackA"))


def step2b_lengths(path=STEP2B):
    """{question id: mean reply tokens} from Step 2b's base runs, each capped at 32,768 with its prompt."""
    by = defaultdict(list)
    for line in Path(path).read_text().splitlines():
        r = json.loads(line)
        if r.get("status") == "ok" and r.get("completion_tokens") is not None:
            by[r["item_id"]].append(min(r["completion_tokens"], CAP - (r.get("prompt_tokens") or 0)))
    return {q: sum(v) / len(v) for q, v in by.items()}


def system_tokens(lengths, part=None):
    """Expected reply tokens over a system's runs (or one part's)."""
    from finetune import eval as ev
    overall = sum(lengths.values()) / len(lengths)
    return sum(lengths.get(j["qid"], overall) for j in ev.jobs(part))


def measured_rate(out=None):
    """Tokens/s from finished evaluation jobs (eval_jobs.jsonl and the runs inside each), or None."""
    out = Path(out or out_root() / "eval")
    jobs_file = out / "eval_jobs.jsonl"
    if not jobs_file.exists():
        return None
    tokens = seconds = 0.0
    for line in jobs_file.read_text().splitlines():
        j = json.loads(line)
        start, end = datetime.fromisoformat(j["started_utc"]), datetime.fromisoformat(j["ended_utc"])
        runs = out / f"eval_{j['system']}_runs.jsonl"
        if not runs.exists() or end <= start:
            continue
        n = sum(r.get("completion_tokens") or 0 for r in map(json.loads, runs.read_text().splitlines())
                if start <= datetime.fromisoformat(r["timestamp_utc"]) <= end)
        tokens, seconds = tokens + n, seconds + (end - start).total_seconds()
    return tokens / seconds if seconds > 600 and tokens else None          # at least 10 minutes measured


def parts_and_limit(hours_high):
    """(parts, --estimate per part, the limit submit.sh makes of it in minutes)."""
    cap = MAX_LIMIT_H / SAFETY
    n = max(1, math.ceil(hours_high / cap - 1e-9))
    est = math.ceil(hours_high / n * 100) / 100
    if est * SAFETY > MAX_LIMIT_H:
        est = math.floor(cap * 100) / 100
    return n, est, ROUND_MIN * math.ceil(est * 60 * SAFETY / ROUND_MIN - 1e-9)


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


def plan(vllm_check, train_jobs, sol=None, lengths=None):
    sol = sol or {"queued": queued, "ended": ended, "job_count": job_count, "trained": trained, "check": check_result,
                  "rate": measured_rate}
    lengths = lengths or step2b_lengths()
    rate = sol["rate"]()
    lo, hi = ((rate * (1 - MEASURED_SPREAD), rate * (1 + MEASURED_SPREAD)) if rate else PRIOR)
    res = {"rate": {"measured": rate, "range": [lo, hi]}, "systems": [], "notes": []}
    check_dep, check_problem = dependency(vllm_check, "vllm_check", sol)
    if check_problem:
        res["notes"].append(f"{check_problem}: every evaluation waits for a passing vLLM check")
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
        if system in TAGGED and passed is False:
            res["notes"].append(f"{system}: the vLLM check failed: tag versions need the own loop (PLAN, E4), not planned here")
            continue
        tokens = system_tokens(lengths)
        h_lo, h_hi = tokens / hi / 3600, tokens / lo / 3600
        n, est, limit = parts_and_limit(h_hi)
        res["systems"].append({"system": system, "tokens": round(tokens), "hours": [round(h_lo, 2), round(h_hi, 2)],
                               "parts": n, "estimate": est, "limit_min": limit, "after": deps})
    count = sol["job_count"]()
    res["queue"] = {"jobs_now": count, "room": None if count is None else MAX_SUBMIT - count}
    return res


def commands(res):
    lo, hi = res["rate"]["range"]
    src = f"measured {res['rate']['measured']:.0f}" if res["rate"]["measured"] else "prior (no evaluation job measured yet)"
    lines = [f"# batch 3, evaluation (Oct 28): decoding {lo:.0f}-{hi:.0f} tokens/s, {src}"]
    room, n = res["queue"]["room"], 0
    for s in res["systems"]:
        dep = f" --dependency=afterok:{':'.join(str(d) for d in s['after'])}" if s["after"] else ""
        lim = f"{s['limit_min'] // 60}:{s['limit_min'] % 60:02d}"
        for k in range(1, s["parts"] + 1):
            part = f" {k}/{s['parts']}" if s["parts"] > 1 else ""
            later = room is not None and n >= room
            lines.append(f"{'# later (MaxSubmitPU): ' if later else ''}{SUBMIT} eval --estimate {s['estimate']:.2f}{dep} -- "
                         f"{s['system']}{part}     # limit {lim}; {s['system']} {s['hours'][0]:.1f}-{s['hours'][1]:.1f} h "
                         f"in {s['parts']} part(s)")
            n += 1
    lines += [f"# note: {x}" for x in res["notes"]]
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vllm-check", required=True, help="the vLLM check's job id")
    ap.add_argument("--train", required=True, help="VERSION=JOB,... the training jobs")
    ap.add_argument("--json", help="also write the plan here (numbers only)")
    a = ap.parse_args()
    res = plan(a.vllm_check, dict(x.split("=", 1) for x in a.train.split(",")))
    print("\n".join(commands(res)))
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
