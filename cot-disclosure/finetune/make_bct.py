"""Track A, A40 (Nov 5): bias-augmented consistency training's targets on Voyager (Chua et al. 2024, "Bias-Augmented
Consistency Training Reduces Biased Reasoning in Chain-of-Thought", adapted). Pre-registered in
archive/sessions/2026-11-05/2026-11-05_0918_A_a40-prereg.md before any call.

  python finetune/make_bct.py --dry-run [--shards 2]          # the plan (records, sha256), calls, Voyager and Sol hours
  python finetune/make_bct.py --plan-out PATH                 # the plan as a file, for a shard on another machine
  python finetune/make_bct.py --run --shard K/N [--plan PATH] [--limit N] [--stop-file F]   # resumable
  python finetune/make_bct.py --report                        # every shard folder so far: passes, drops, stances; no calls
  python finetune/make_bct.py --check-shards                  # every shard folder against the plan (before --assemble)
  python finetune/make_bct.py --assemble                      # finetune/data/a40/ + finetune/gpu/a40_inputs.json
  python finetune/make_bct.py --check-data                    # Sol, after the rsync: the files against that manifest

BCT (the paper's sections 2.2 and 3.1): supervised fine-tuning on prompts that carry a bias, paired with the model's own
reasoning on the same prompt without it. Here:
  questions  the pool's sure questions: Step 6's 3 no-hint runs all answered and on the key (run_steps67's kept), less
             set A (LoRA's validation questions, the set A localization set); a question also in E2 or the 30 (by id,
             or by its stem's text) stops the plan. A tenth, the round(n/10) with the lowest Random("a40:<item>:
             validation"), is A40's validation slice (train.py chooses the epoch on it).
  records    LoRA's own (run_steps67.records_for: a wrong hint on each of the three channels, and 1-2 correct hints,
             build_dataset's training wordings, by seed), so A40 and LoRA differ only in the target.
  pass 1     the model's reasoning with no hint: the no-hint prompt (Step 6's and evaluation's), the pinned format,
             temperature 0.6, the 32,768 cap, continued as Step 6. At most 4 samples, seeds PASS1_SEED0 + 4j + s (j:
             the record's place among its question's records; never Step 6's seeds 0-2, never two records of a question
             alike), kept at the first that is answered and ends on the key.
  pass 2     the final answer: the hinted prompt, that reasoning, "</think>", "\\n\\n" and a final opener in the model's
             own voice that names the hint (make_targets.FINAL_OPENERS, by record and seed); the model continues, at
             most FINAL_MAX tokens, and a tool call stops it. At most 4 samples (seeds 0-3), kept at the first that ends
             on the reasoning's letter with a stance that fits the hint (make_targets.stance after the opener:
             "disagrees" with a wrong hint, "agrees after checking" with a correct one).
  example    the record's messages and the target "<reasoning></think>\\n\\n<opener><continuation>": no instruction
             anywhere, so none can be quoted. Over 32,768 tokens in all: counted and left out. A record with no pass in
             either pass is dropped and counted. The no-hint examples (a tenth of the set) are Step 6's own runs, as
             LoRA's (make_targets.nohint_examples).
Shards (--shard K/N) split by question (its place in the plan mod N), so no seed depends on the split; each writes its
own folder, results/trackA/a40/shard<K>of<N>/ (gitignored). Another machine runs from the plan file (--plan-out),
whose sha256 must be the pre-registered PLAN_SHA256. Exit codes, as progress/guard.py reads them: 0 every chosen record
done, 1 work left (a request got no reply: rerun), 2 stopped by the stop file, 3 a Voyager guard failed.
"""
import argparse
import gzip
import hashlib
import json
import random
import re
import statistics
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

import client  # noqa: E402
from client import CanaryFailed, ModelUnavailable, preflight, transport_error  # noqa: E402
from common import BACKOFF, append, latest, load, run_id, slot  # noqa: E402
from finetune import base_format as bf  # noqa: E402
from finetune import build_dataset as bd  # noqa: E402
from finetune import make_targets as mt  # noqa: E402
from finetune import olmo_format  # noqa: E402
from finetune import run_nohint as rn  # noqa: E402
from finetune import run_steps67 as rs  # noqa: E402
from finetune.continuation import continue_to_answer  # noqa: E402
from parse import parse_answer  # noqa: E402
from tools.answer_key import build  # noqa: E402

EXPERIMENT = "trackA_a40"
OUT_DIR = CODE / "results" / "trackA" / "a40"                     # gitignored: every sample, one folder a shard
DATA_DIR = CODE / "finetune" / "data" / "a40"                     # gitignored: the training set
TRAIN_SET, VALIDATION_SET = DATA_DIR / "train_examples.jsonl.gz", DATA_DIR / "validation_examples.jsonl.gz"
SET_MANIFEST = DATA_DIR / "manifest.json"
INPUTS = CODE / "finetune" / "gpu" / "a40_inputs.json"            # tracked: the training set's bytes, checked on Sol
PLAN_SHA256 = "297478e77e42dd9af0d2232be4d23e9f370db594b27f15c778ae539ebd6bdf0c"   # the A40 log's section 5
VALIDATION_SHARE, SALT = 0.10, "a40"
PASS1_SEED0, MAX_PASS1, MAX_PASS2 = 100, 4, 4
FINAL_MAX = 2048                       # a final answer's tokens (Step 7's: median 263, mean 405, 90th percentile 591)
SEP = "\n\n"                           # between "</think>" and the opener, as make_targets.sample_prefill
NOT_RUN_PASSES = 2
STANCE = {False: "disagrees", True: "agrees after checking"}
TEXT_KEYS = ("raw_text", "reasoning_text", "final_text", "messages", "tools", "target_raw")
# the dry run's rates (the A40 log, section 7)
P1_SECONDS = 113.7      # Step 6's no-hint runs on these questions (Oct 25-27): mean seconds a slot, at the 32,768 cap
P1_PASS = 0.92          # a fresh no-hint sample ends on the key: a beta-binomial fit to the pool's 530 questions' k of 3
P2_SECONDS = 10.0       # Step 7's final answers: mean 405 tokens at 57-72 tokens/s (Step 7; B24's Olmo, Nov 4) + the prompt
P2_PASS = 0.88          # Step 7's correct-hint samples passed 381 of 412 (0.92), less its 5% "neither" stance
P2_TOKENS = 405         # Step 7's mean final answer (tokens after the opener)
LORA_HOURS = 3.41       # S3: lora's training job 66759753, 3:24:50 for its 1,040 + 156 examples (the Oct 28 12:20 log)


def n_tokens(text):
    return olmo_format.n_tokens(text)


# ---------------------------------------------------------------- the plan
def stem_key(text):
    """A question's stem, lowercased, its whitespace collapsed (MMLU-Pro repeats some texts under other ids)."""
    return " ".join(text.split("\n(A) ")[0].lower().split())


def overlap(questions, excluded):
    """[(item_id, set name, "id" or "text")] for each question that is also in an excluded set."""
    out = []
    for name, qs in excluded.items():
        ids = {q["item_id"] for q in qs} | {f"mmlupro-{q['qid']}" for q in qs if q.get("qid") is not None}
        texts = {stem_key(q["question"]) for q in qs}
        for q in questions:
            if q["item_id"] in ids or (q.get("qid") is not None and f"mmlupro-{q['qid']}" in ids):
                out.append((q["item_id"], name, "id"))
            elif stem_key(q["question"]) in texts:
                out.append((q["item_id"], name, "text"))
    return out


def excluded_sets():
    """{name: questions} never trained on: set A (LoRA's validation questions), E2 and the 30."""
    from finetune import train as tr
    pool = {q["item_id"]: q for q in rn.questions()}
    set_a = sorted({x["item_id"] for x in tr.load_examples(tr.VALIDATION)})
    return {"set A": [pool[i] for i in set_a], "E2": list(bd.e2_questions()), "the 30": list(bd.heldout_questions())}


def splits(ids, share=VALIDATION_SHARE, salt=SALT):
    """{item_id: "train" or "validation"}: the round(share x n) questions with the lowest seeded hash are validation."""
    ids = sorted(set(ids))
    h = {i: random.Random(f"{salt}:{i}:validation").random() for i in ids}
    val = set(sorted(ids, key=lambda i: (h[i], i))[:round(share * len(ids))])
    return {i: "validation" if i in val else "train" for i in ids}


def plan(kept=None, excluded=None):
    """The records A40 makes targets for, in a fixed order (question, then record id), each with its split, its
    question's place and its seeds. kept: run_steps67's kept questions [(question, target, runs)]; excluded: {name:
    questions} (excluded_sets()). Set A's questions are left out; any question left that is also in set A, E2 or the
    30 (by id or by text) stops it."""
    kept = rs.state(rn.questions())[2] if kept is None else kept
    excluded = excluded_sets() if excluded is None else excluded
    set_a = {q["item_id"] for q in excluded.get("set A", [])}
    kept = sorted((k for k in kept if k[0]["item_id"] not in set_a), key=lambda k: k[0]["item_id"])
    clash = overlap([q for q, _, _ in kept], excluded)
    if clash:
        raise ValueError("A40's questions overlap a set never trained on: " +
                         "; ".join(f"{i} in {name} (by {how})" for i, name, how in clash))
    split = splits([q["item_id"] for q, _, _ in kept])
    rows = []
    for qi, (q, target, runs) in enumerate(kept):
        nohint, _ = build(q["question"], q.get("qid", q["item_id"]), "none")
        for j, r in enumerate(sorted(rs.records_for([(q, target, runs)]), key=lambda r: r["id"])):
            rows.append({**r, "split": split[q["item_id"]], "qid": q.get("qid", q["item_id"]), "question_index": qi,
                         "nohint_messages": nohint, "experiment": EXPERIMENT,
                         "pass1_seeds": [PASS1_SEED0 + MAX_PASS1 * j + s for s in range(MAX_PASS1)],
                         "pass2_seeds": list(range(MAX_PASS2))})
    return rows


def plan_sha(rows):
    h = hashlib.sha256()
    for r in rows:
        h.update((json.dumps(r, sort_keys=True) + "\n").encode())
    return h.hexdigest()


def write_plan(rows, path):
    with gzip.open(path, "wt") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    return plan_sha(rows)


def read_plan(path, sha=None):
    """The plan file another machine runs from; refused unless its sha256 is the pre-registered one."""
    sha = sha or PLAN_SHA256
    rows = load(path)
    if plan_sha(rows) != sha:
        raise SystemExit(f"{path}: the plan's sha256 is {plan_sha(rows)}, not the pre-registered {sha}: nothing ran")
    return rows


def shard(rows, k, n):
    """Shard k of n: whole questions, by their place in the plan."""
    return [r for r in rows if r["question_index"] % n == k - 1]


def shard_dir(k, n, root=OUT_DIR):
    return Path(root) / f"shard{k}of{n}"


# ---------------------------------------------------------------- the two passes
def p1_id(rec, seed):
    return run_id(EXPERIMENT + "_pass1", rec["item_id"], bf.MODEL, "none", rec["id"], seed)


def p2_id(rec, p1_seed, seed):
    return run_id(EXPERIMENT + "_pass2", rec["item_id"], bf.MODEL, rec["hint_channel"], f"{rec['id']}|p1s{p1_seed}", seed)


def _status(error):
    return ("not_run" if transport_error(error) else "api_error") if error else "ok"


def _meta(reply):
    return {k: (reply or {}).get(k) for k in ("served_model", "requested_model_id", "reasoning_effort")}


def pass1_sample(rec, seed, complete_fn=None):
    """The model's reasoning on the question with no hint (Step 6's prompt and settings); passes when it is answered
    and ends on the key."""
    complete_fn = complete_fn or client.complete
    prompt = olmo_format.render(rec["nohint_messages"])
    start = time.monotonic()
    reply, _, _, _ = continue_to_answer(rec["nohint_messages"], prompt, "", cap=olmo_format.CAP_TOTAL - n_tokens(prompt),
                                        condition="none", question_id=None, letter=None, seed=seed,
                                        complete_fn=complete_fn)
    raw, error = reply.get("raw") or "", reply.get("error")
    reasoning, final = olmo_format.split(raw)
    letter = parse_answer(final, rec["n_options"])[0] if final else None
    why = None
    if not error:
        if reply.get("finish") == "length" or reply.get("no_answer_reason"):
            why = reply.get("no_answer_reason") or "hit the token cap"
        elif olmo_format.THINK_CLOSE not in raw or letter is None:
            why = "no answer"
        elif letter != rec["target_answer"]:
            why = "wrong letter"
    return {"run_id": p1_id(rec, seed), "experiment": EXPERIMENT, "stage": 1, "record_id": rec["id"],
            "item_id": rec["item_id"], "split": rec["split"], "hint_channel": rec["hint_channel"],
            "hint_correct": rec["hint_correct"], "target_answer": rec["target_answer"], "seed": seed,
            "status": _status(error), "error_type": error, "pass": not error and why is None, "why_not": why,
            "parsed_letter": letter, "finish_reason": reply.get("finish"), "usage": reply.get("usage"),
            "gen_seconds": round(time.monotonic() - start, 1), **_meta(reply), "raw_text": raw, "reasoning_text": reasoning}


def _gen(complete_fn, prompt, max_tokens, seed, stop):
    with slot():
        return complete_fn(bf.MODEL, prompt, max_tokens=max_tokens, temperature=bf.TEMPERATURE, seed=seed,
                           backoff=BACKOFF, extra={"stop": stop, "include_stop_str_in_output": True} if stop else None)


def judge2(rec, final, f_open, finish):
    """(pass, why not, stance) for a final answer: within its cap, no tool call, the reasoning's letter (the key), and a
    stance after the opener that fits the hint (make_targets.stance)."""
    after = final[len(f_open):] if final.startswith(f_open) else final
    stance = mt.stance(after, rec["hint_correct"])
    if finish == "length":
        return False, "hit the token cap", stance
    if rec["hint_channel"] == "tool_injected" and olmo_format.function_calls(final):
        return False, "called the tool again", stance
    letter = parse_answer(final, rec["n_options"])[0]
    if letter != rec["target_answer"]:
        return False, "wrong letter" if letter else "no answer", stance
    if stance == "neither":
        return False, "the final answer says neither", stance
    if stance != STANCE[rec["hint_correct"]]:
        return False, "the stance doesn't fit the hint", stance
    return True, None, stance


def pass2_sample(rec, p1, seed, complete_fn=None):
    """The final answer after the hinted prompt, pass 1's reasoning and an opener naming the hint."""
    complete_fn = complete_fn or client.complete
    side, _, j, _, f_open = mt.openers(rec, seed)
    prompt = (olmo_format.render(rec["messages"], tools=rec["tools_declared"]) + p1["reasoning_text"] +
              olmo_format.THINK_CLOSE + SEP + f_open)
    left = min(FINAL_MAX, olmo_format.CAP_TOTAL - n_tokens(prompt))
    injected = rec["hint_channel"] == "tool_injected"
    start, reply, final = time.monotonic(), {}, f_open
    if left > 0:
        reply = _gen(complete_fn, prompt, left, seed, ["</function_calls>"] if injected else None)
        final = f_open + (reply.get("content") or "")
    error = reply.get("error")
    ok, why, stance = judge2(rec, final, f_open, reply.get("finish") if left > 0 else "length")
    return {"run_id": p2_id(rec, p1["seed"], seed), "experiment": EXPERIMENT, "stage": 2, "record_id": rec["id"],
            "item_id": rec["item_id"], "split": rec["split"], "hint_channel": rec["hint_channel"],
            "hint_correct": rec["hint_correct"], "hint_letter": rec["hint_letter"], "target_answer": rec["target_answer"],
            "pass1_seed": p1["seed"], "seed": seed, "status": _status(error), "error_type": error,
            "pass": not error and ok, "why_not": None if error else why, "stance": stance,
            "parsed_letter": parse_answer(final, rec["n_options"])[0], "final_opener": [side, j],
            "finish_reason": reply.get("finish"), "usage": reply.get("usage"), "max_tokens": left,
            "gen_seconds": round(time.monotonic() - start, 1), **_meta(reply), "final_text": final}


# ---------------------------------------------------------------- a record
def example(rec, p1, p2):
    """The training example, as make_targets.example writes them: the record's messages and the target."""
    raw = p1["reasoning_text"] + olmo_format.THINK_CLOSE + SEP + p2["final_text"]
    total = n_tokens(olmo_format.render(rec["messages"], tools=rec["tools_declared"])) + n_tokens(raw)
    return {**final_head(rec), "outcome": "example", "messages": rec["messages"], "tools": rec["tools_declared"],
            "target_raw": raw, "target_method": "bct", "pass1_seed": p1["seed"], "pass2_seed": p2["seed"],
            "pass1_run_id": p1["run_id"], "pass2_run_id": p2["run_id"],
            "openers": {"reasoning": None, "final": p2["final_opener"]}, "stance": p2["stance"], "tokens": total,
            "dropped_for_length": total > olmo_format.CAP_TOTAL}


def final_head(rec):
    return {"run_id": run_id(EXPERIMENT + "_record", rec["item_id"], bf.MODEL, rec["hint_channel"], rec["id"], 0),
            "experiment": EXPERIMENT, "record_id": rec["id"], "split": rec["split"], "item_id": rec["item_id"],
            "question_set": rec["question_set"], "hint_channel": rec["hint_channel"], "hint_wording": rec["hint_wording"],
            "hint_correct": rec["hint_correct"], "hint_letter": rec["hint_letter"], "target_answer": rec["target_answer"],
            "status": "ok"}


def dropped(rec, why):
    return {**final_head(rec), "outcome": "dropped", "why": why}


def keep(out_dir, stage, row):
    append(Path(out_dir) / f"{stage}.jsonl.gz", row)
    append(Path(out_dir) / f"{stage}_runs.jsonl", {k: v for k, v in row.items() if k not in TEXT_KEYS})
    return row


def save_final(out_dir, row):
    return keep(out_dir, "records", row)


def finished(out_dir):
    """{record id: its final row (an example, or why it was dropped)} in one shard's folder."""
    return {r["record_id"]: r for r in latest(load(Path(out_dir) / "records.jsonl.gz"))}


def saved_samples(out_dir):
    """{run id: sample} of the samples saved with a reply (a resumed run reads them instead of sending them again)."""
    return {r["run_id"]: r for stage in ("pass1", "pass2") for r in latest(load(Path(out_dir) / f"{stage}.jsonl.gz"))
            if r["status"] == "ok"}


def do_record(rec, out_dir, complete_fn=None, saved=None):
    """Pass 1 until a sample ends on the key (its seeds in order), then pass 2 on that reasoning until a final answer
    passes; samples already saved are read, not sent again. Returns the record's final row (its example, or why it is
    dropped), or None when a request got no reply (the record runs again in the next pass)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = saved_samples(out_dir) if saved is None else saved
    p1 = None
    for seed in rec["pass1_seeds"]:
        s = saved.get(p1_id(rec, seed)) or keep(out_dir, "pass1", pass1_sample(rec, seed, complete_fn))
        if s["status"] != "ok":
            return None
        if s["pass"]:
            p1 = s
            break
    if p1 is None:
        return save_final(out_dir, dropped(rec, f"no no-hint sample ended on the key in {MAX_PASS1}"))
    for seed in rec["pass2_seeds"]:
        s = saved.get(p2_id(rec, p1["seed"], seed)) or keep(out_dir, "pass2", pass2_sample(rec, p1, seed, complete_fn))
        if s["status"] != "ok":
            return None
        if s["pass"]:
            return save_final(out_dir, example(rec, p1, s))
    return save_final(out_dir, dropped(rec, f"no final answer passed in {MAX_PASS2}"))


def run(rows, out_dir, workers=bf.IN_FLIGHT, stop_file=None, complete_fn=None, limit=None):
    """Every record of rows (the first `limit`) not yet finished in out_dir; records whose request got no reply get up
    to NOT_RUN_PASSES more passes. Once the stop file exists, no record starts (those in flight finish). Returns 0
    when every chosen record is finished, 2 when stopped by the file, 1 when some are left."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stopped = lambda: bool(stop_file) and Path(stop_file).exists()  # noqa: E731
    chosen = rows[:limit] if limit else rows
    if stopped():
        return 2
    if complete_fn is None:
        with slot():
            preflight(bf.MODEL)       # /v1/models + the identity canary before any record; raises on failure
    for attempt in range(1 + NOT_RUN_PASSES):
        done = finished(out_dir)
        todo = [r for r in chosen if r["id"] not in done]
        if not todo:
            break
        saved, lost, t0 = saved_samples(out_dir), 0, time.monotonic()
        print(f"pass {attempt + 1}: {len(todo)} records ({len(chosen) - len(todo)} done), {workers} at a time", flush=True)

        def one(r):
            return "stopped" if stopped() else do_record(r, out_dir, complete_fn, saved)
        with ThreadPoolExecutor(workers) as pool:
            sent = [pool.submit(one, r) for r in todo]
            try:
                for i, f in enumerate(as_completed(sent), 1):
                    lost += f.result() is None
                    if i % 10 == 0 or i == len(todo):
                        print(f"  {i}/{len(todo)} records; no reply {lost}; {(time.monotonic() - t0) / 60:.1f} min",
                              flush=True)
            except (ModelUnavailable, CanaryFailed):
                pool.shutdown(wait=False, cancel_futures=True)
                raise
        if stopped():
            print(f"stopped by {stop_file}", flush=True)
            return 2
        if not lost:
            break
    done = finished(out_dir)
    return 0 if all(r["id"] in done for r in chosen) else 1


# ---------------------------------------------------------------- shards, the report
def shard_dirs(root=OUT_DIR):
    """[(k, n, folder)] of every shard folder under root."""
    out = []
    for d in sorted(Path(root).glob("shard*of*")):
        m = re.fullmatch(r"shard(\d+)of(\d+)", d.name)
        if m and d.is_dir():
            out.append((int(m.group(1)), int(m.group(2)), d))
    return out


def example_problems(rec, row, where):
    """An example re-checked from its own text: the plan's messages, a pass-1 reasoning, and its final answer judged
    again as pass 2 judged it."""
    out = []
    if row["messages"] != rec["messages"] or row["tools"] != rec["tools_declared"]:
        out.append(f"{where}: {rec['id']}: its messages are not the plan's")
    side, j = row["openers"]["final"]
    f_open = mt.FINAL_OPENERS[side][j].format(x=rec["hint_letter"])
    head = olmo_format.THINK_CLOSE + SEP + f_open
    if head not in row["target_raw"]:
        out.append(f"{where}: {rec['id']}: the target has no opener after its reasoning")
    elif not judge2(rec, row["target_raw"].split(olmo_format.THINK_CLOSE + SEP, 1)[1], f_open, "stop")[0]:
        out.append(f"{where}: {rec['id']}: its final answer doesn't pass when judged again")
    if row["pass1_seed"] not in rec["pass1_seeds"] or row["pass2_seed"] not in rec["pass2_seeds"]:
        out.append(f"{where}: {rec['id']}: a seed outside the plan")
    return out


def check_shards(rows, root=OUT_DIR):
    """Every shard folder against the plan: each final row's record is in the plan and in that folder's shard, in one
    shard only; each example passes again from its own text with the plan's messages and seeds; every sample came from
    the model asked for. {problems, final, missing, shards}."""
    by_id = {r["id"]: r for r in rows}
    problems, seen, ns = [], {}, set()
    for k, n, d in shard_dirs(root):
        ns.add(n)
        for rid, row in finished(d).items():
            rec = by_id.get(rid)
            if rec is None:
                problems.append(f"{d.name}: record {rid} is not in the plan")
                continue
            if rec["question_index"] % n != k - 1:
                problems.append(f"{d.name}: record {rid} is not in shard {k} of {n}")
            if rid in seen:
                problems.append(f"record {rid} is in two shards ({seen[rid]}, {d.name})")
            seen.setdefault(rid, d.name)
            if row["outcome"] == "example":
                problems += example_problems(rec, row, d.name)
        for s in (r for stage in ("pass1", "pass2") for r in load(d / f"{stage}_runs.jsonl")):
            if s["status"] == "ok" and s.get("served_model") not in (None, bf.MODEL):
                problems.append(f"{d.name}: sample {s['run_id']} was served by {s['served_model']}")
    if len(ns) > 1:
        problems.append(f"the shard folders split the plan in different ways: {sorted(ns)}")
    return {"problems": problems, "final": len(seen), "missing": len(set(by_id) - set(seen)),
            "shards": [d.name for _, _, d in shard_dirs(root)]}


def report(rows, root=OUT_DIR):
    """Every shard folder so far: final rows by channel and hint, drops, samples a record, why samples failed, stances,
    Voyager time. No calls."""
    finals = {rid: r for _, _, d in shard_dirs(root) for rid, r in finished(d).items()}
    samples = [s for _, _, d in shard_dirs(root) for stage in ("pass1", "pass2") for s in latest(load(d / f"{stage}_runs.jsonl"))]
    print(f"{len(finals)} of {len(rows)} records finished; examples {sum(r['outcome'] == 'example' for r in finals.values())}; "
          f"dropped {dict(Counter(r['why'] for r in finals.values() if r['outcome'] == 'dropped'))}")
    print("| channel | hint | records | examples | pass-1 samples a record | pass-2 samples a record |")
    print("|---|---|---|---|---|---|")
    for c in bd.TRAIN_CHANNELS:
        for hc in (False, True):
            ids = {r["id"] for r in rows if r["hint_channel"] == c and r["hint_correct"] == hc}
            fin = [finals[i] for i in ids if i in finals]
            per = {st: [s for s in samples if s["record_id"] in ids and s["stage"] == st and s["status"] == "ok"] for st in (1, 2)}
            print(f"| {c} | {'correct' if hc else 'wrong'} | {len(ids)} | {sum(r['outcome'] == 'example' for r in fin)} | "
                  f"{len(per[1]) / max(1, len(fin)):.2f} | {len(per[2]) / max(1, len(fin)):.2f} |")
    for st in (1, 2):
        ss = [s for s in samples if s["stage"] == st and s["status"] == "ok"]
        secs = [s["gen_seconds"] for s in ss]
        print(f"pass {st}: {len(ss)} samples, why not {dict(Counter(s['why_not'] for s in ss if not s['pass']))}; "
              f"{statistics.mean(secs) if secs else 0:.1f} s a sample (a slot), {sum(secs) / 4 / 3600:.2f} h at 4 in flight")
    print(f"stances of the examples: {dict(Counter((r['hint_correct'], r['stance']) for r in finals.values() if r['outcome'] == 'example'))}")
    return finals


# ---------------------------------------------------------------- the training set
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def assemble(rows, root=OUT_DIR, kept=None, data_dir=DATA_DIR, inputs=INPUTS, code=CODE, seed=bd.SEED):
    """The training set from every shard folder: the examples (their tokens counted again; over 32,768 left out and
    counted) and a tenth of no-hint examples (Step 6's runs of A40's questions, as LoRA's), each in its question's
    split; then the byte manifest Sol checks (inputs). Refused while a shard check fails or a record has no final row."""
    check = check_shards(rows, root)
    if check["problems"] or check["missing"]:
        raise SystemExit(f"not assembled: {check['missing']} records have no final row; problems: {check['problems'][:5]}")
    finals = {rid: r for _, _, d in shard_dirs(root) for rid, r in finished(d).items()}
    kept = rs.state(rn.questions())[2] if kept is None else kept
    split = {r["item_id"]: r["split"] for r in rows}
    examples, too_long = [], 0
    for r in rows:
        e = finals[r["id"]]
        if e["outcome"] != "example":
            continue
        e = {**e, "tokens": n_tokens(olmo_format.render(e["messages"], tools=e["tools"])) + n_tokens(e["target_raw"])}
        e["dropped_for_length"] = e["tokens"] > olmo_format.CAP_TOTAL
        too_long += e["dropped_for_length"]
        if not e["dropped_for_length"]:
            examples.append(e)
    n_nohint = round(len(examples) * rs.NOHINT_SHARE / (1 - rs.NOHINT_SHARE))
    nohint = [e for e in mt.nohint_examples([k for k in kept if k[0]["item_id"] in split], n_nohint, seed)
              if not e["dropped_for_length"]]
    for e in nohint:
        e["split"] = split[e["item_id"]]
    out = examples + nohint
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    paths = {s: data_dir / f"{s}_examples.jsonl.gz" for s in ("train", "validation")}
    for s, path in paths.items():
        with gzip.open(path, "wt") as f:
            for e in out:
                if e["split"] == s:
                    f.write(json.dumps(e) + "\n")
    dropped_why = Counter(r["why"] for r in finals.values() if r["outcome"] == "dropped")
    manifest = {"plan_sha256": plan_sha(rows), "records": len(rows), "examples": len(out),
                "by_split": dict(Counter(e["split"] for e in out)),
                "questions": dict(Counter(split[q] for q in {e["item_id"] for e in out})),
                "by_channel": dict(Counter(f"{e['hint_channel']}|{e.get('hint_correct')}" for e in out)),
                "dropped": dict(dropped_why), "dropped_over_32768": too_long, "nohint_examples": len(nohint),
                "stances": dict(Counter(f"{e['hint_correct']}|{e.get('stance')}" for e in examples)),
                "tokens_median": statistics.median(e["tokens"] for e in out) if out else None}
    (data_dir / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    Path(inputs).write_text(json.dumps({"what": "A40's training set (finetune/make_bct.py --assemble); train.py "
                                                "--version a40 checks it on Sol", "plan_sha256": plan_sha(rows),
                                        "files": [{"path": str(p.relative_to(code)), "bytes": p.stat().st_size,
                                                   "sha256": sha256(p)} for p in paths.values()]}, indent=1) + "\n")
    return manifest


def check_data(inputs=INPUTS, code=CODE):
    """Sol, after the rsync (and train.py --version a40 first thing): every file of the manifest present with its bytes.
    [] when they match."""
    if not Path(inputs).exists():
        return [f"no {inputs}: --assemble on the Mac writes it, and it is committed before training"]
    bad = []
    for r in json.loads(Path(inputs).read_text())["files"]:
        p = Path(code) / r["path"]
        if not p.exists():
            bad.append(f"missing {r['path']}")
        elif p.stat().st_size != r["bytes"] or sha256(p) != r["sha256"]:
            bad.append(f"different bytes: {r['path']}")
    return bad


# ---------------------------------------------------------------- the dry run
def expected(p, tries=4):
    """Samples sent a record when each passes with probability p and at most `tries` are sent."""
    return (1 - (1 - p) ** tries) / p


def budget(rows, p1_seconds=P1_SECONDS, p1_pass=P1_PASS, p2_seconds=P2_SECONDS, p2_pass=P2_PASS,
           in_flight=bf.IN_FLIGHT, shards=1):
    """Voyager calls and hours: pass 1 for every record, pass 2 for those with a pass-1 hit, at in_flight at a time."""
    def one(rs_):
        n = len(rs_)
        c1 = n * expected(p1_pass, MAX_PASS1)
        c2 = n * (1 - (1 - p1_pass) ** MAX_PASS1) * expected(p2_pass, MAX_PASS2)
        return {"records": n, "questions": len({r["item_id"] for r in rs_}), "pass1_calls": c1, "pass2_calls": c2,
                "hours": (c1 * p1_seconds + c2 * p2_seconds) / in_flight / 3600}
    return {**one(rows), "shards": [one(shard(rows, k, shards)) for k in range(1, shards + 1)],
            "rates": {"p1_seconds": p1_seconds, "p1_pass": p1_pass, "p2_seconds": p2_seconds, "p2_pass": p2_pass,
                      "in_flight": in_flight}}


def sol_hours(rows, runs=None, lora_sets=None):
    """Training hours on one A100, from S3's measured LORA_HOURS scaled by tokens: A40's examples (each record's hinted
    prompt + its question's mean Step 6 reply + P2_TOKENS; the no-hint tenth at Step 6's prompt + reply) against
    LoRA's own (its examples' tokens); a validation token at a quarter of a training token (no backward pass)."""
    from finetune import train as tr
    runs = [r for r in latest(load(rn.OUT)) if r["status"] == "ok"] if runs is None else runs
    mean = {}
    for r in runs:
        mean.setdefault(r["item_id"], []).append((r.get("usage") or {}).get("completion_tokens") or 0)
    mean = {q: statistics.mean(v) for q, v in mean.items()}
    per = {"train": [], "validation": []}
    for r in rows:
        per[r["split"]].append(n_tokens(olmo_format.render(r["messages"], tools=r["tools_declared"])) + mean[r["item_id"]]
                               + P2_TOKENS)
    nohint = statistics.mean(n_tokens(olmo_format.render(r["nohint_messages"])) + mean[r["item_id"]] for r in rows)
    t = {s: sum(v) + len(v) * rs.NOHINT_SHARE / (1 - rs.NOHINT_SHARE) * nohint for s, v in per.items()}
    lora = lora_sets or (tr.load_examples(tr.TRAIN), tr.load_examples(tr.VALIDATION))
    lt = sum(e["tokens"] for e in lora[0]) + sum(e["tokens"] for e in lora[1]) / 4
    at = t["train"] + t["validation"] / 4
    return {"tokens": t, "lora_tokens": lt, "hours": LORA_HOURS * at / lt}


def dry_run_text(rows, shards):
    b = budget(rows, shards=shards)
    r = b["rates"]
    by = Counter((x["split"], x["hint_correct"]) for x in rows)
    lines = [f"A40's plan: {b['questions']} questions ({sum(1 for q in {x['item_id']: x['split'] for x in rows}.values() if q == 'validation')} "
             f"in validation), {b['records']} records (wrong hint: train {by[('train', False)]}, validation "
             f"{by[('validation', False)]}; correct hint: train {by[('train', True)]}, validation {by[('validation', True)]})",
             f"  plan sha256 {plan_sha(rows)} ({'the pre-registered one' if plan_sha(rows) == PLAN_SHA256 else 'NOT the pre-registered ' + PLAN_SHA256})",
             f"Voyager (no calls now): pass 1 {b['pass1_calls']:,.0f} calls at {r['p1_seconds']} s, pass 2 "
             f"{b['pass2_calls']:,.0f} at {r['p2_seconds']} s (pass rates {r['p1_pass']}, {r['p2_pass']}); "
             f"{b['hours']:.1f} h at {r['in_flight']} in flight on one machine"]
    for k, s in enumerate(b["shards"], 1):
        lines.append(f"  shard {k}/{shards}: {s['questions']} questions, {s['records']} records, {s['pass1_calls'] + s['pass2_calls']:,.0f} "
                     f"calls, {s['hours']:.1f} h at {r['in_flight']} in flight")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    for m in ("--dry-run", "--run", "--report", "--check-shards", "--assemble", "--check-data"):
        mode.add_argument(m, action="store_true")
    mode.add_argument("--plan-out", metavar="PATH", help="write the plan (for a shard on another machine)")
    ap.add_argument("--shard", default="1/1", help="K/N: the questions whose place in the plan is K-1 mod N")
    ap.add_argument("--shards", type=int, default=2, help="--dry-run: the split to show")
    ap.add_argument("--plan", help="run from this plan file (another machine); its sha256 must be PLAN_SHA256")
    ap.add_argument("--limit", type=int, help="the shard's first N records only (a smoke)")
    ap.add_argument("--workers", type=int, default=bf.IN_FLIGHT)
    ap.add_argument("--stop-file", help="start no new record once this file exists (progress/guard.py)")
    ap.add_argument("--sol", action="store_true", help="--dry-run: also the training hours (reads LoRA's data; slower)")
    a = ap.parse_args(argv)
    if a.check_data:
        bad = check_data(INPUTS)                         # INPUTS at call time (Nov 6: a test patches it)
        print("\n".join(bad) if bad else f"a40 data: every file matches {INPUTS.relative_to(CODE)}")
        return 1 if bad else 0
    rows = read_plan(a.plan) if a.plan else plan()
    if a.dry_run:
        print(dry_run_text(rows, a.shards))
        if a.sol:
            s = sol_hours(rows)
            print(f"Sol: training about {s['hours']:.2f} h on one A100 (S3's {LORA_HOURS} h x {s['tokens']['train'] + s['tokens']['validation'] / 4:,.0f} "
                  f"/ {s['lora_tokens']:,.0f} weighted tokens)")
        return 0
    if a.plan_out:
        print(f"wrote {len(rows)} records to {a.plan_out}, sha256 {write_plan(rows, a.plan_out)}")
        return 0
    if a.report:
        report(rows)
        return 0
    if a.check_shards:
        c = check_shards(rows)
        print(json.dumps(c, indent=1))
        return 1 if c["problems"] else 0
    if a.assemble:
        print(json.dumps(assemble(rows), indent=1))
        print(f"wrote {INPUTS.relative_to(CODE)}: commit it before the training line goes in")
        return 0
    if plan_sha(rows) != PLAN_SHA256:
        raise SystemExit(f"the plan's sha256 is {plan_sha(rows)}, not the pre-registered {PLAN_SHA256}: nothing ran")
    k, n = (int(x) for x in a.shard.split("/"))
    try:
        return run(shard(rows, k, n), shard_dir(k, n), a.workers, a.stop_file, limit=a.limit)
    except (CanaryFailed, ModelUnavailable) as err:
        print(f"halted: {type(err).__name__}: {err}", flush=True)
        return 3


if __name__ == "__main__":
    sys.exit(main() or 0)
