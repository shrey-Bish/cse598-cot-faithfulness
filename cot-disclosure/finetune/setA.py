"""Track A, set A: an independent localization set (Oct 29). Steps 2b, 3 and 10's inputs on questions not
used to find the readout layers (F11, F12 were found on Test 2's 30 MMLU-Pro questions, which are also the
evaluation questions).

Questions: the 34 validation questions of the training data (finetune/data/validation_examples.jsonl.gz):
in neither the training split nor the evaluation (Test 2) set; 18 hard puzzles and 16 MMLU-Pro (train
split). Each question's hint letter is the one Steps 6-7 chose for it (finetune/data/pool.jsonl,
hint_letters[0]); it is never the correct letter and never one of the model's no-hint answers.
Runs (Olmo 3 7B Think, pinned Think format, Step 2b's code and wordings, base_format.one): the pasted tool
block x 3 and the declared inserted tool turn x 3 per question (the arms Steps 9 and 10 used). No-hint
runs: the 3 Step 6 runs per question (results/trackA/nohint_train.jsonl.gz) give the own answer (majority)
and "sure" (all 3 answered and correct).
Probes: Step 3's grid_tail on every followed run (look/takeover.py), then the cases: followed runs with a
late takeover on sure questions, in takeover_cases format, for Step 10 (and Step 9's runs) on Sol.

  python finetune/setA.py --dry-run          # questions, runs, calls, time; no calls
  python finetune/setA.py --run              # generation, then probes, then the cases (resumable)
  python finetune/setA.py --report           # counts so far; no calls
Exit codes (--run): 0 all done, 1 work left (a rerun resumes), 2 stopped by --stop-file, 3 a Voyager guard
failed (progress/guard.py). Outputs (gitignored, results/trackA/setA/): runs.jsonl.gz (records with text),
runs_rows.jsonl, items.jsonl (questions in Step 2b's item format, for Steps 9 and 10 on Sol: --items-from),
probes.jsonl.gz, takeover_runs.jsonl, cases.jsonl.
"""
import argparse
import json
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from client import CanaryFailed, ModelUnavailable, preflight  # noqa: E402
from common import append, latest, load  # noqa: E402
from finetune import base_format as bf  # noqa: E402
from finetune import train as tr  # noqa: E402
from finetune.look import takeover as tk  # noqa: E402

OUT_DIR = CODE / "results" / "trackA" / "setA"
RUNS = OUT_DIR / "runs.jsonl.gz"
ROWS = OUT_DIR / "runs_rows.jsonl"
ITEMS = OUT_DIR / "items.jsonl"
PROBES = OUT_DIR / "probes.jsonl.gz"
TAKEOVER_RUNS = OUT_DIR / "takeover_runs.jsonl"
CASES = OUT_DIR / "cases.jsonl"
POOL = CODE / "finetune" / "data" / "pool.jsonl"
NOHINT = CODE / "results" / "trackA" / "nohint_train.jsonl.gz"
EXPERIMENT = "trackA_setA"
ARMS = (("tool_pasted", None), (bf.INJECTED, bf.DECLARED))
REPEATS = 3
OPTION = re.compile(r"\n\(([A-J])\) ([^\n]*)")


def split_options(text):
    """(stem, [option texts]) from a pool question whose options follow it as "\\n(A) ..." lines."""
    first = text.find("\n(A) ")
    if first < 0:
        raise ValueError("no options")
    stem, tail = text[:first], text[first:]
    opts = OPTION.findall(tail)
    if [x for x, _ in opts] != list("ABCDEFGHIJ"[:len(opts)]) or "".join(f"\n({x}) {o}" for x, o in opts) != tail:
        raise ValueError("options are not a clean (A).. list")
    return stem, [o for _, o in opts]


def items(pool_path=POOL, validation=tr.VALIDATION):
    """The validation questions in Step 2b's item format (question_id, question, options, answer, cue_letter,
    category); question_block(item) rebuilds the pool's question text exactly."""
    want = sorted({x["item_id"] for x in tr.load_examples(validation)})
    pool = {r["item_id"]: r for r in load(pool_path)}
    out = []
    for q in want:
        r = pool[q]
        stem, options = split_options(r["question"])
        if len(options) != int(r["n_options"]):
            raise ValueError(f"{q}: {len(options)} options, pool says {r['n_options']}")
        out.append({"question_id": q, "question": stem, "options": options, "answer": r["correct"],
                    "cue_letter": r["hint_letters"][0], "category": r["question_set"]})
    return out


def jobs(its):
    return [(it, cond, rep, arm) for it in its for cond, arm in ARMS for rep in range(REPEATS)]


def job_id(j):
    return bf.run_id(EXPERIMENT, j[0]["question_id"], bf.MODEL, j[1], j[3], j[2])


def nohint_rows(its, path=NOHINT):
    want = {it["question_id"] for it in its}
    return [r for r in latest(load(path)) if r["item_id"] in want and r["condition"] == "none"]


def own_and_sure(nohint):
    """({question: own no-hint answer (majority of the answered runs)}, {question: all runs answered and correct})."""
    own = tk.own_answers(nohint)
    by_q = {}
    for r in nohint:
        by_q.setdefault(r["item_id"], []).append(r)
    sure = {q: all(r["status"] == "ok" and r["parsed_letter"] is not None and r["parsed_letter"] == r["correct_letter"]
                   for r in rs) for q, rs in by_q.items()}
    return own, sure


def followed(rows):
    return [r for r in rows if r["status"] == "ok" and r["parsed_letter"] is not None and r.get("reasoning_text")
            and r["condition"] != "none" and r["parsed_letter"] == r["cue_letter"]]


def save_run(rec):
    append(RUNS, rec)
    append(ROWS, bf.summary_row(rec))


def generate(its, stop_file=None, workers=bf.IN_FLIGHT):
    """The runs not done yet; returns (done, total). Runs that come back not_run get up to 2 more passes."""
    for attempt in range(1 + bf.NOT_RUN_PASSES):
        done = {r["run_id"] for r in bf.current(load(RUNS)) if r["status"] == "ok"}
        todo = [j for j in jobs(its) if job_id(j) not in done]
        if not todo or (stop_file and Path(stop_file).exists()):
            break
        print(f"generation pass {attempt + 1}: {len(jobs(its))} runs, {len(todo)} to run", flush=True)
        start = time.monotonic()

        def one(j):
            if stop_file and Path(stop_file).exists():
                return None
            return bf.one(*j, experiment=EXPERIMENT)
        with ThreadPoolExecutor(workers) as pool:
            futures = [pool.submit(one, j) for j in todo]
            try:
                for n, fut in enumerate(as_completed(futures), 1):
                    rec = fut.result()
                    if rec is not None:
                        save_run(rec)
                    if n % 10 == 0 or n == len(todo):
                        print(f"  {n}/{len(todo)}, {(time.monotonic() - start) / 60:.1f} min", flush=True)
            except (ModelUnavailable, CanaryFailed):
                pool.shutdown(wait=False, cancel_futures=True)
                raise
        if not any(r["status"] == "not_run" for r in bf.current(load(RUNS))):
            break
    ok = {r["run_id"] for r in bf.current(load(RUNS)) if r["status"] == "ok"}
    return sum(job_id(j) in ok for j in jobs(its)), len(jobs(its))


def probe(its, own, stop_file=None):
    """Step 3's grid_tail probes on every followed run not probed yet."""
    runs = followed(bf.current(load(RUNS)))
    if stop_file and Path(stop_file).exists():
        return runs
    by_q = {it["question_id"]: it for it in its}
    tk.run(runs, own, by_q, probes_path=PROBES, runs_path=TAKEOVER_RUNS, workers=bf.IN_FLIGHT, probes="grid_tail")
    return runs


def probed(own):
    runs = followed(bf.current(load(RUNS)))
    return tk.current_probes(load(PROBES), {tk.source_key(r) for r in runs}, own), runs


def cases(own, sure):
    rows, _ = probed(own)
    out = tk.default_cases(rows, sure)
    tk.save_cases(out, path=CASES, rule="followed runs whose takeover comes at or after half the reasoning, on "
                                         "set A questions whose three Step 6 no-hint runs were all answered and correct",
                  use="set A: Track A Step 10 (and Step 9) on questions not used to find the readout layers")
    return out


def report(its, own, sure):
    rows = bf.current(load(RUNS))
    by = Counter((r["condition"], r.get("arm"), r["status"]) for r in rows)
    fol = followed(rows)
    pr, _ = probed(own)
    types = Counter(tk.takeover_type(r) for r in pr)
    late_q = {r["item_id"] for r in pr if tk.takeover_type(r) == "late" and sure.get(r["item_id"])}
    ans = [r for r in rows if r["status"] == "ok" and r["parsed_letter"] is not None]
    print(f"set A: {len(its)} questions; runs {dict(by)}")
    for cond, arm in ARMS:
        a = [r for r in ans if r["condition"] == cond and r.get("arm") == arm]
        f = [r for r in a if r["parsed_letter"] == r["cue_letter"]]
        print(f"  {cond}{' (' + arm + ')' if arm else ''}: followed {len(f)} of {len(a)} answered, on "
              f"{len({r['item_id'] for r in f})} questions")
    print(f"  probed {len(pr)} of {len(fol)} followed runs; takeover types {dict(types)}; late takeovers on sure "
          f"questions: {sum(1 for r in pr if tk.takeover_type(r) == 'late' and sure.get(r['item_id']))} runs on "
          f"{len(late_q)} questions (pre-registered minimum: 5 questions)")
    return late_q


def write_items(its):
    ITEMS.parent.mkdir(parents=True, exist_ok=True)
    ITEMS.write_text("".join(json.dumps(it) + "\n" for it in its))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--run", action="store_true", help="generation, probes, cases (resumable)")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--stop-file", help="start no new run or probe once this file exists (progress/guard.py)")
    a = ap.parse_args(argv)
    its = items()
    own, sure = own_and_sure(nohint_rows(its))
    if a.dry_run:
        js = jobs(its)
        inj = sum(1 for j in js if j[1] == bf.INJECTED)
        print(f"set A: {len(its)} questions ({dict(Counter(it['category'] for it in its))}), none in training or in "
              f"Test 2; sure (3 of 3 Step 6 no-hint runs correct): {sum(sure.values())} of {len(sure)}")
        print(f"{len(js)} runs: pasted tool block x {REPEATS} and declared inserted tool turn x {REPEATS} per question "
              f"= {len(js)} calls, plus up to {bf.MAX_EXTRA_ROUNDS * inj} if inserted-tool replies keep calling")
        print(f"  time at Step 2b's 78 s/call, {bf.IN_FLIGHT} in flight: {len(js) * bf.MEASURED_SEC / bf.IN_FLIGHT / 60:.0f} "
              f"min (longer for long puzzle replies: Step 6's no-hint runs here had a median of 8,606 tokens)")
        print(f"then Step 3 grid_tail probes on the followed runs (~{tk.EST_S_PER_REQUEST} s a probe, a few dozen per "
              f"run), then the cases -> {CASES.relative_to(CODE)}")
        return 0
    if a.report:
        report(its, own, sure)
        return 0
    if not a.run:
        ap.error("give --dry-run, --run or --report")
    write_items(its)
    try:
        preflight(bf.MODEL)
        done, total = generate(its, a.stop_file)
        if a.stop_file and Path(a.stop_file).exists():
            return 2
        if done < total:
            print(f"{total - done} runs left; a rerun resumes", flush=True)
            return 1
        runs = probe(its, own, a.stop_file)
        if a.stop_file and Path(a.stop_file).exists():
            return 2
        rows, _ = probed(own)
        if len(rows) < len(runs):
            print(f"{len(runs) - len(rows)} followed runs not probed yet; a rerun resumes", flush=True)
            return 1
    except (CanaryFailed, ModelUnavailable) as err:
        print(f"halted: {type(err).__name__}: {err}", file=sys.stderr, flush=True)
        return 3
    out = cases(own, sure)
    report(its, own, sure)
    print(f"saved {len(out)} cases to {CASES.relative_to(CODE)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
