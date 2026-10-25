"""Shared plumbing for the progress-presentation runs (October 2026).

Everything model-facing goes through the repo's own `client.chat` (streaming,
cache, reasoning/answer split), `parse.parse_answer` and `detect.detect`. This
module only adds what the new runs need on top: one session log, a limit of
four requests in flight across every process on this machine, deterministic
run ids, the JSONL record schema, and Wilson intervals.
"""
import fcntl
import gzip
import hashlib
import json
import logging
import math
import random
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent            # cot-disclosure/progress
CODE = HERE.parent                                # cot-disclosure
REPO = CODE.parent
sys.path.insert(0, str(CODE))

from client import chat, transport_error  # noqa: E402
from parse import parse_answer  # noqa: E402

RESULTS = CODE / "results"
OUT = RESULTS / "progress"
DATA = CODE / "data" / "progress"
LOGS = CODE / "logs"
DOCS = REPO / "docs" / "progress"
PRES = REPO / "presentation" / "progress"
FIGS = PRES / "figures"
SHOTS = PRES / "screenshots"
for _d in (OUT, DATA, LOGS):
    _d.mkdir(parents=True, exist_ok=True)

MAX_IN_FLIGHT = 4                 # across all jobs and processes
BACKOFF = [2, 4, 8]               # transport failures only, at most 3 retries
SEED = 20261005

# Pilot settings (experiments.py) reused by every new answerer call.
PILOT_TEMPERATURE = 0.6
PILOT_MAX_TOKENS = 16000


# ---------------------------------------------------------------- logging
def _session_log():
    """One log per session: the first script to run picks the timestamp."""
    marker = LOGS / "SESSION"
    if not marker.exists():
        marker.write_text(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    return LOGS / f"progress_{marker.read_text().strip()}.log"


def get_logger(name):
    log = logging.getLogger(name)
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s", "%Y-%m-%dT%H:%M:%SZ")
    fmt.converter = time.gmtime
    for handler in (logging.FileHandler(_session_log()), logging.StreamHandler(sys.stdout)):
        handler.setFormatter(fmt)
        log.addHandler(handler)
    log.propagate = False
    return log


# ---------------------------------------------------------------- concurrency
_SLOTS = LOGS / ".slots"
_SLOTS.mkdir(exist_ok=True)


@contextmanager
def slot():
    """Hold one of MAX_IN_FLIGHT lock files while a request is open, so every
    process together never has more than four requests in flight. The jittered
    waits keep it fair: without them a thread that just released a slot takes it
    straight back and a second process starves."""
    time.sleep(random.uniform(0, 0.4))
    while True:
        for i in random.sample(range(MAX_IN_FLIGHT), MAX_IN_FLIGHT):
            fh = open(_SLOTS / f"slot{i}", "w")
            try:
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                fh.close()
                continue
            try:
                yield i
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)
                fh.close()
            return
        time.sleep(random.uniform(0.05, 0.3))


# ---------------------------------------------------------------- records
def run_id(experiment, item_id, model, condition, arm, repeat):
    key = "|".join(str(x) for x in (experiment, item_id, model, condition, arm, repeat))
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def parse_status(out, letter):
    if out["error"]:
        return None
    if out["finish"] == "length":
        return "truncated"
    return "ok" if letter else "parse_failure"


def make_record(out, *, experiment, item_id, model, condition, repeat, messages, n_options, correct_letter=None,
                arm=None, cue_letter=None, cue_channel=None, temperature=PILOT_TEMPERATURE,
                max_tokens=PILOT_MAX_TOKENS, seed=None, stream=True, run_id_=None):
    """The JSONL record for one finished call (`out` as returned by client.chat or chat_live)."""
    letter, rule = parse_answer(out["content"], n_options)
    return {
        "run_id": run_id_ or run_id(experiment, item_id, model, condition, arm, repeat), "experiment": experiment,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": model, "item_id": item_id, "condition": condition, "arm": arm, "repeat": repeat,
        "cue_letter": cue_letter, "cue_channel": cue_channel, "correct_letter": correct_letter,
        "prompt_messages": messages,
        "prompt_sha256": hashlib.sha256(json.dumps(messages, sort_keys=True).encode()).hexdigest(),
        "params": {"temperature": temperature, "max_tokens": max_tokens, "seed": seed, "stream": stream},
        "latency_s": out.get("latency_s"), "cached": out.get("cached", False),
        "finish_reason": out["finish"], "usage": out["usage"],
        "reasoning_field": out.get("reasoning_field"),
        "reasoning_text": out["reasoning"] or None, "final_text": out["content"],
        "parsed_letter": letter, "parse_rule": rule, "parse_status": parse_status(out, letter),
        "status": status_of(out), "error_type": out["error"], "retries": out.get("retries", 0),
        # what was sent and what answered (client.py; Voyager IDs changed on 2026-10-21)
        "requested_model_id": out.get("requested_model_id"), "reasoning_effort": out.get("reasoning_effort"),
        "served_model": out.get("served_model"),
    }


def status_of(out):
    """ok; not_run when the request never got a whole reply (idle timeout, dropped connection,
    stream cut short, gateway 5xx: retry it later, never "no answer"); api_error for anything else."""
    if not out["error"]:
        return "ok"
    return "not_run" if transport_error(out["error"]) else "api_error"


def call(log, *, experiment, item_id, model, condition, repeat, messages, n_options,
         correct_letter=None, arm=None, cue_letter=None, cue_channel=None,
         temperature=PILOT_TEMPERATURE, max_tokens=PILOT_MAX_TOKENS, seed=None,
         stream=True, extra=None):
    """One model call through the repo client, returned as a schema record."""
    rid = run_id(experiment, item_id, model, condition, arm, repeat)

    def on_retry(attempt, error, wait):
        log.warning(f"retry {attempt} run_id={rid} model={model} error={error} wait={wait}s")

    with slot():
        out = chat(model, messages, max_tokens=max_tokens, temperature=temperature, seed=seed,
                   backoff=BACKOFF, on_retry=on_retry, stream=stream)
    rec = make_record(out, experiment=experiment, item_id=item_id, model=model, condition=condition, repeat=repeat,
                      messages=messages, n_options=n_options, correct_letter=correct_letter, arm=arm,
                      cue_letter=cue_letter, cue_channel=cue_channel, temperature=temperature,
                      max_tokens=max_tokens, seed=seed, stream=stream, run_id_=rid)
    status = rec["status"]
    rec.update(extra or {})
    tokens = (out["usage"] or {}).get("completion_tokens")
    log.info(f"call {experiment} run_id={rid} model={model} cond={condition} arm={arm} rep={repeat} "
             f"status={status} finish={out['finish']} letter={rec['parsed_letter']} tokens={tokens} "
             f"latency={out.get('latency_s')}s cached={rec['cached']} retries={rec['retries']}")
    return rec


# ---------------------------------------------------------------- files
_write_lock = threading.Lock()


def _open(path, mode):
    """A results file, gzip-compressed when its name ends in .gz (each append adds a gzip member;
    readers see one stream of lines)."""
    return gzip.open(path, mode + "t") if str(path).endswith(".gz") else open(path, mode)


def append(path, rec):
    with _write_lock, _open(path, "a") as f:
        f.write(json.dumps(rec) + "\n")


def load(path):
    path = Path(path)
    if not path.exists():
        return []
    with _open(path, "r") as f:
        return [json.loads(line) for line in f]


def move_to_gz(src, dst, summary=None, summary_path=None):
    """Move a results file to gzip: every record unchanged, plus (optionally) one summary row per
    record in summary_path. The copy is checked record by record before the original is removed.
    Returns the number of records."""
    src, dst = Path(src), Path(dst)
    if dst.exists() or (summary_path and Path(summary_path).exists()):
        raise FileExistsError(f"{dst.name} or its summary already exists: nothing moved")
    rows = load(src)
    with gzip.open(dst, "wt") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    if load(dst) != rows:
        dst.unlink()
        raise ValueError(f"the compressed copy of {src.name} differs: original kept")
    for r in rows if summary else []:
        append(summary_path, summary(r))
    src.unlink()
    return len(rows)


def latest(rows):
    """Last record per run_id (a resumed job may append a retry of an api_error)."""
    out = {}
    for r in rows:
        out[r["run_id"]] = r
    return list(out.values())


def done_ids(path):
    return {r["run_id"] for r in latest(load(path)) if r["status"] == "ok"}


# ---------------------------------------------------------------- statistics
def boot_diff(a, b, n=20000, seed=0):
    """Difference in rate between two systems (a - b) over the questions both have, with a 95%
    percentile bootstrap clustered by question: a and b map question -> 0/1 outcomes, and each
    resample draws questions (with all their runs, in both systems) with replacement.
    Returns (difference, low, high)."""
    qs = sorted(set(a) & set(b), key=str)

    def diff(sample):
        ra = [x for q in sample for x in a[q]]
        rb = [x for q in sample for x in b[q]]
        return sum(ra) / len(ra) - sum(rb) / len(rb) if ra and rb else None
    rng = random.Random(seed)
    vals = sorted(v for v in (diff([rng.choice(qs) for _ in qs]) for _ in range(n)) if v is not None)
    return diff(qs), vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]


def boot_mean(groups, n=20000, seed=0):
    """Mean of values grouped by question, with a 95% percentile bootstrap clustered by question
    (each resample draws questions, with all their values). Returns (mean, low, high)."""
    qs = sorted(groups, key=str)

    def mean(sample):
        vals = [x for q in sample for x in groups[q]]
        return sum(vals) / len(vals) if vals else None
    rng = random.Random(seed)
    vals = sorted(v for v in (mean([rng.choice(qs) for _ in qs]) for _ in range(n)) if v is not None)
    return mean(qs), vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]


def wilson(k, n, z=1.959964):
    """Wilson score 95% interval for k successes out of n."""
    if not n:
        return None
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [max(0.0, centre - half), min(1.0, centre + half)]
