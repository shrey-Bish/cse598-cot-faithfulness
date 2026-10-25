"""Track A, step 6: 3 no-hint runs per training question, in the pinned format.

  python finetune/run_nohint.py --dry-run --pilot      # the 10 pilot questions: calls and time
  python finetune/run_nohint.py --pilot                # run them
  python finetune/run_nohint.py --dry-run --limit 900  # the first 900 pool questions
  python finetune/run_nohint.py --limit 900            # run (resumable)

Questions: finetune/data/pool.jsonl (make_pool.py) in pool order; --pilot takes the first 10
(5 puzzles, 5 MMLU-Pro). Each run is a no-hint generation: the question and the usual
instruction rendered with the pinned Think template, /v1/completions, temperature 0.6, seed =
the run's number, at most 32,768 tokens in all, prompt included (from 2026-10-25; the pilot ran
up to the 65,536-token context); past that is no answer. Every record carries no_hint_source "voyager" and the time the run held a
request slot (gen_seconds), which sizes the full run.
Output (appended): results/trackA/nohint_train.jsonl.gz, one row per run in
results/trackA/nohint_train_runs.jsonl. A run that never got a whole reply is not_run and is
retried in up to two more passes.
"""
import argparse
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from client import CanaryFailed, ModelUnavailable, complete, preflight  # noqa: E402
from common import append, latest, load, make_record, run_id  # noqa: E402
from finetune import base_format as bf  # noqa: E402
from finetune import olmo_format  # noqa: E402
from finetune.continuation import continue_to_answer  # noqa: E402
from tools.answer_key import build  # noqa: E402

EXPERIMENT = "trackA_nohint_train"
OUT = CODE / "results" / "trackA" / "nohint_train.jsonl.gz"
RUNS_OUT = CODE / "results" / "trackA" / "nohint_train_runs.jsonl"
POOL = CODE / "finetune" / "data" / "pool.jsonl"
RUNS = 3
PILOT = 10
NOT_RUN_PASSES = 2
EST_S = 230.0          # dry run before the pilot: Step 2b's no-hint runs, ~11,500 tokens at ~50 tokens/s


def questions(limit=None, pilot=False):
    items = load(POOL)
    return items[:PILOT] if pilot else items[:limit] if limit else items


def job_id(q, rep):
    return run_id(EXPERIMENT, q["item_id"], bf.MODEL, "none", None, rep)


def generate(msgs, rep):
    """One no-hint reply, within 32,768 tokens in all (one request; hitting the cap is no answer)."""
    prompt = olmo_format.render(msgs)
    reply, _, _, _ = continue_to_answer(msgs, prompt, "", cap=olmo_format.CAP_TOTAL - olmo_format.n_tokens(prompt),
                                        condition="none", question_id=None, letter=None, seed=rep, complete_fn=complete)
    return reply


def one(q, rep):
    msgs, _ = build(q["question"], q.get("qid", q["item_id"]), "none")
    extensions, start = [], time.monotonic()
    out = generate(msgs, rep)
    seconds = round(time.monotonic() - start, 1)
    rec = make_record(out, experiment=EXPERIMENT, item_id=q["item_id"], model=bf.MODEL, condition="none", repeat=rep,
                      messages=msgs, n_options=q["n_options"], correct_letter=q["correct"],
                      temperature=bf.TEMPERATURE, max_tokens=olmo_format.CAP_TOTAL, seed=rep, run_id_=job_id(q, rep))
    if rec["finish_reason"] == "length":                       # cut off at the context: no answer
        rec["parsed_letter_if_not_cut"], rec["parsed_letter"] = rec["parsed_letter"], None
    rec.update({"question_set": q["question_set"], "category": q.get("category") or q.get("kind"),
                "no_hint_source": "voyager", "format": "olmo3_think_tools", "template_sha256": olmo_format.PINNED_SHA256,
                "endpoint": "completions", "rendered_prompt": out.get("prompt"), "raw_text": out.get("raw"),
                "extensions": extensions or None, "gen_seconds": seconds,
                "token_limit": {"total_with_prompt": olmo_format.CAP_TOTAL}})
    return rec


def summary_row(rec):
    keys = ("run_id", "timestamp_utc", "item_id", "question_set", "category", "repeat", "correct_letter", "parsed_letter",
            "status", "finish_reason", "gen_seconds", "requested_model_id", "reasoning_effort", "served_model")
    usage = rec.get("usage") or {}
    return {**{k: rec.get(k) for k in keys}, "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "continued": [e.get("reason", "length") for e in rec.get("extensions") or []] or None}


def save(rec, out=None, runs_out=None):
    append(out or OUT, rec)
    append(runs_out or RUNS_OUT, summary_row(rec))


def run(qs, workers=bf.IN_FLIGHT, out=None, runs_out=None):
    out = out or OUT
    preflight(bf.MODEL)
    results = []
    for attempt in range(1 + NOT_RUN_PASSES):
        done = {r["run_id"] for r in latest(load(out)) if r["status"] == "ok"}
        todo = [(q, rep) for q in qs for rep in range(RUNS) if job_id(q, rep) not in done]
        if not todo:
            break
        print(f"pass {attempt + 1}: {len(todo)} runs", flush=True)
        start, this_pass = time.monotonic(), []
        with ThreadPoolExecutor(workers) as pool:
            futures = [pool.submit(one, q, rep) for q, rep in todo]
            try:
                for n, fut in enumerate(as_completed(futures), 1):
                    rec = fut.result()
                    save(rec, out, runs_out)
                    this_pass.append(rec)
                    if n % 10 == 0 or n == len(todo):
                        print(f"  {n}/{len(todo)} runs, {(time.monotonic() - start) / 60:.1f} min", flush=True)
            except (ModelUnavailable, CanaryFailed):
                pool.shutdown(wait=False, cancel_futures=True)
                raise
        results += this_pass
        if not any(r["status"] == "not_run" for r in this_pass):
            break
    return results


def report(qs, rows=None):
    """Per question: kept (3 answered, all correct) or why not; and the measured time per run."""
    from finetune.build_dataset import all_correct
    rows = latest(load(OUT)) if rows is None else rows
    by_q = {}
    for r in rows:
        by_q.setdefault(r["item_id"], []).append(r)
    kept, reasons = 0, {}
    for q in qs:
        _, why = all_correct(q, [r for r in by_q.get(q["item_id"], []) if r["status"] == "ok"])
        kept += why is None
        reasons[why or "kept"] = reasons.get(why or "kept", 0) + 1
    secs = [r["gen_seconds"] for r in rows if r.get("gen_seconds") and r["status"] == "ok"]
    toks = [r["usage"]["completion_tokens"] for r in rows if r["status"] == "ok" and (r.get("usage") or {}).get("completion_tokens")]
    print(f"{len(qs)} questions: kept {kept} (all {RUNS} runs answered and correct); {reasons}")
    if secs:
        print(f"time per run (holding a request slot): median {statistics.median(secs):.0f} s, mean "
              f"{statistics.mean(secs):.0f} s; reply tokens median {statistics.median(toks):,.0f}")
    return kept, reasons


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pilot", action="store_true", help=f"the first {PILOT} pool questions")
    ap.add_argument("--limit", type=int, help="the first N pool questions")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    qs = questions(a.limit, a.pilot)
    if a.report:
        return report(qs)
    done = {r["run_id"] for r in latest(load(OUT)) if r["status"] == "ok"}
    todo = sum(job_id(q, rep) not in done for q in qs for rep in range(RUNS))
    print(f"{len(qs)} questions x {RUNS} runs = {len(qs) * RUNS} calls ({todo} not done yet); at ~{EST_S:.0f} s a run, "
          f"{bf.IN_FLIGHT} in flight: ~{todo * EST_S / bf.IN_FLIGHT / 3600:.1f} h")
    if a.dry_run:
        return
    run(qs)
    report(qs)


if __name__ == "__main__":
    main()
