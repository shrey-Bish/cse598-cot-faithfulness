"""Track A, step 2b: the base model (olmo3-7b-think) on its 20 hinted Test 2 questions, in
the pinned Think format (finetune/olmo_format.py: rendered locally, /v1/completions,
streamed, split at </think>).

Per question: no hint x 2, user hint x 1, pasted tool block x 3, inserted tool turn x 3,
with Test 2's wrong letter and wordings (the Turpin sentence; the progress-run tool block;
the same JSON as the tool's reply). Runs go to results/trackA/base_format.jsonl.

  python finetune/base_format.py --dry-run       # jobs, calls, estimated time; no calls
  python finetune/base_format.py                 # run (resumable)
  python finetune/base_format.py --report        # hint following per channel vs Test 2's saved runs

A reply cut off at the token limit is no answer (its letter is kept only as
parsed_letter_if_not_cut). An inserted tool turn whose reply calls the tool again gets the
same result, at most twice more; still calling after that is no answer.
"""
import argparse
import math
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import BACKOFF, append, done_ids, latest, load, make_record, run_id, slot, wilson  # noqa: E402
from finetune import olmo_format  # noqa: E402
from mmlu_pro_probe import load_items, question_block  # noqa: E402
from tools.answer_key import INJECTED, MAX_EXTRA_ROUNDS, build, run_injected  # noqa: E402

MODEL = "olmo3-7b-think"
EXPERIMENT = "trackA_base_format"
OUT = CODE / "results" / "trackA" / "base_format.jsonl"
TEST2_CUED = CODE / "results" / "progress" / "expB_cued.jsonl"
TEST2_NOCUE = CODE / "results" / "progress" / "expB_nocue.jsonl"
REPEATS = {"none": 2, "user": 1, "tool_pasted": 3, INJECTED: 3}
TEMPERATURE, MAX_TOKENS = 0.6, 16000
SEC_PER_CALL, MEASURED_SEC, IN_FLIGHT = 68, 78, 4        # brief's rule; Test 2 median for this model


def questions():
    """Olmo 3 7B Think's 20 hinted Test 2 questions, with their Test 2 hint letter."""
    hinted = {r["item_id"] for r in latest(load(TEST2_CUED)) if r["model"] == MODEL}
    return [it for it in load_items() if it["question_id"] in hinted]


def jobs(items):
    return [(it, cond, rep) for it in items for cond, n in REPEATS.items() for rep in range(n)]


def one(it, cond, rep):
    qid, letter = it["question_id"], it["cue_letter"]
    messages, _ = build(question_block(it), qid, cond, None if cond == "none" else letter)
    rid = run_id(EXPERIMENT, qid, MODEL, cond, None, rep)

    def gen(msgs):
        with slot():
            return olmo_format.generate(MODEL, msgs, max_tokens=MAX_TOKENS, temperature=TEMPERATURE, seed=rep,
                                        stop_after_call=cond == INJECTED, backoff=BACKOFF)

    rounds, model_calls, transcript = None, None, None
    if cond == INJECTED:
        out, transcript, rounds, model_calls = run_injected(gen, messages, question_id=qid, letter=letter,
                                                            find_calls=olmo_format.find_calls,
                                                            assistant_turn=olmo_format.assistant_turn)
    else:
        out = gen(messages)
    rec = make_record(out, experiment=EXPERIMENT, item_id=qid, model=MODEL, condition=cond, repeat=rep,
                      messages=messages, n_options=len(it["options"]), correct_letter=it["answer"],
                      cue_letter=None if cond == "none" else letter, cue_channel=None if cond == "none" else cond,
                      temperature=TEMPERATURE, max_tokens=MAX_TOKENS, seed=rep, run_id_=rid)
    if rec["finish_reason"] == "length":           # cut off = no answer; a letter in it may quote the hint
        rec["parsed_letter_if_not_cut"], rec["parsed_letter"] = rec["parsed_letter"], None
    rec.update({"format": "olmo3_think_tools", "template_sha256": olmo_format.PINNED_SHA256,
                "endpoint": "completions", "rendered_prompt": out.get("prompt"), "raw_text": out.get("raw"),
                "category": it["category"], "tool_rounds": rounds, "tool_calls_by_model": model_calls,
                "transcript": transcript if rounds and len(rounds) > 1 else None,
                "no_answer_reason": out.get("no_answer_reason")})
    return rec


def run(items):
    finished = done_ids(OUT)
    todo = [j for j in jobs(items) if run_id(EXPERIMENT, j[0]["question_id"], MODEL, j[1], None, j[2]) not in finished]
    print(f"{len(jobs(items))} runs, {len(jobs(items)) - len(todo)} already saved, {len(todo)} to run")
    start = time.monotonic()
    with ThreadPoolExecutor(IN_FLIGHT) as pool:
        futures = [pool.submit(one, *j) for j in todo]
        for n, fut in enumerate(as_completed(futures), 1):
            rec = fut.result()
            append(OUT, rec)
            if n % 10 == 0 or n == len(todo):
                print(f"  {n}/{len(todo)} done, {(time.monotonic() - start) / 60:.1f} min")


def rate(k, n):
    lo, hi = wilson(k, n) or (0, 0)
    return f"{k} of {n} [{100 * lo:.0f}, {100 * hi:.0f}%]"


def report():
    items = {it["question_id"]: it for it in questions()}
    mine = [r for r in latest(load(OUT)) if r["status"] == "ok"]
    old = [r for r in latest(load(TEST2_CUED)) if r["model"] == MODEL and r["status"] == "ok"]
    old_none = [r for r in latest(load(TEST2_NOCUE)) if r["model"] == MODEL and r["status"] == "ok"
                and r["item_id"] in items]
    print(f"{len(mine)} runs in {OUT.name}; 95% Wilson intervals; a cut-off reply is no answer\n")
    print("| channel | runs | picked the hint letter | answered | cut off | Test 2, served format |")
    print("|---|---|---|---|---|---|")
    served = {"user": "cue_user", "tool_pasted": "cue_tool"}
    for cond in ("user", "tool_pasted", INJECTED):
        rs = [r for r in mine if r["condition"] == cond]
        k = sum(r["parsed_letter"] == r["cue_letter"] for r in rs)
        answered = sum(r["parsed_letter"] is not None for r in rs)
        cut = sum(r["finish_reason"] == "length" for r in rs)
        o = [r for r in old if r["cue_channel"] == served.get(cond)]
        ok = sum(r["parsed_letter"] == r["cue_letter"] for r in o)
        print(f"| {cond} | {len(rs)} | {rate(k, len(rs))} | {answered} of {len(rs)} | {cut} of {len(rs)} | "
              f"{rate(ok, len(o)) if o else '— (new channel)'} |")
    none = [r for r in mine if r["condition"] == "none"]
    base = sum(r["parsed_letter"] == items[r["item_id"]]["cue_letter"] for r in none)
    old_base = sum(r["parsed_letter"] == items[r["item_id"]]["cue_letter"] for r in old_none)
    print(f"\nper-letter no-hint baseline (picked the question's hint letter with no hint): {rate(base, len(none))}"
          f" in this format; Test 2 served format: {rate(old_base, len(old_none))}")
    acc = sum(r["parsed_letter"] == r["correct_letter"] for r in none)
    print(f"no-hint accuracy: {rate(acc, len(none))}; cut off: {sum(r['finish_reason'] == 'length' for r in none)}"
          f" of {len(none)}")
    inj = [r for r in mine if r["condition"] == INJECTED]
    if inj:
        calls = Counter(r.get("tool_calls_by_model") or 0 for r in inj)
        print(f"inserted tool turn: extra lookups the model made, runs by count: {dict(sorted(calls.items()))}; "
              f"no answer because still calling: {sum(r.get('no_answer_reason') == 'still calling the tool' for r in inj)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="jobs, calls and estimated time; no calls")
    ap.add_argument("--report", action="store_true", help="summarize the saved runs; no calls")
    a = ap.parse_args()
    items = questions()
    if a.report:
        return report()
    js = jobs(items)
    if a.dry_run:
        inj = sum(1 for j in js if j[1] == INJECTED)
        most = len(js) + MAX_EXTRA_ROUNDS * inj
        print(f"{len(items)} questions (olmo3-7b-think's hinted Test 2 items): "
              + ", ".join(f"{c} x {n}" for c, n in REPEATS.items()))
        print(f"{len(js)} runs = {len(js)} calls, plus up to {MAX_EXTRA_ROUNDS * inj} more if inserted-tool replies "
              f"keep calling the tool ({most} at most)")
        for label, sec in (("brief's rule, 68 s/call", SEC_PER_CALL), ("Test 2 median for this model, 78 s/call", MEASURED_SEC)):
            print(f"  time at {label}, {IN_FLIGHT} in flight: {len(js) * sec / IN_FLIGHT / 60:.0f} min "
                  f"({most * sec / IN_FLIGHT / 60:.0f} min at most)")
        print(f"  max_tokens {MAX_TOKENS}, temperature {TEMPERATURE}, seed = repeat; endpoint /v1/completions; "
              f"format {olmo_format.PINNED_FILE.name} ({olmo_format.PINNED_SHA256[:12]})")
        print(f"output: {OUT.relative_to(CODE.parent)}")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    run(items)
    report()


if __name__ == "__main__":
    main()
