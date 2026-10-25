"""Track A, step 7: target replies by context distillation.

  python finetune/make_targets.py --dry-run --pilot    # the Step 6 pilot's kept questions: records and calls
  python finetune/make_targets.py --pilot              # run them
  python finetune/make_targets.py --report --pilot     # pass rates and 2 full examples; no calls
  python finetune/make_targets.py --plan 3000          # one dry run for the full Steps 6 + 7, from the pilots

Records: build_dataset.py's training records (train + validation). The pilot covers every
training channel (user, pasted tool block, inserted tool turn with the function declared) with
a wrong and a correct hint for each of the Step 6 pilot's kept questions.
For each record, up to 4 samples (seeds 0-3), stopping at the first that passes:
  1. the prompt is the record's own (rendered with the pinned template) with the guiding note
     (finetune/prompts/guide_note.txt) added at the end of the system turn
  2. pass = the final letter equals the target (the kept no-hint answer, which is the key) and
     the final answer mentions the hint (detect.py keyword count: user words for a user hint,
     tool words for a tool hint); a broader count with each wording's source words ("friend",
     "notes", "search_notes", ...) is recorded alongside
  3. the example is stored WITHOUT the note: the record's messages + the sample's reply
  4. fallback when no sample passes: the model's own no-hint reasoning (a Step 6 run) with one
     sentence that names and checks the hint added at its end, and one in its final answer;
     target_method says which
A sample may use at most 32,768 tokens minus the prompt (the training length); one that calls
the tool again fails (no tool reply is sent: a training target is one reply). Examples longer
than 32,768 tokens are dropped and counted.
Output (appended): every sample in results/trackA/target_samples.jsonl.gz (+ _runs.jsonl), one
example per record in results/trackA/targets.jsonl.gz (+ targets_runs.jsonl).
"""
import argparse
import math
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

from client import CanaryFailed, ModelUnavailable, preflight, transport_error  # noqa: E402
from common import append, latest, load, run_id, wilson  # noqa: E402
from detect import COMPILED  # noqa: E402
from finetune import base_format as bf  # noqa: E402
from finetune import build_dataset as bd  # noqa: E402
from finetune import olmo_format  # noqa: E402
from finetune import run_nohint as rn  # noqa: E402
from finetune.continuation import continue_to_answer  # noqa: E402
from parse import parse_answer  # noqa: E402

EXPERIMENT = "trackA_targets"
NOTE = (CODE / "finetune" / "prompts" / "guide_note.txt").read_text().strip()
SAMPLES_OUT = CODE / "results" / "trackA" / "target_samples.jsonl.gz"
SAMPLES_RUNS = CODE / "results" / "trackA" / "target_samples_runs.jsonl"
TARGETS_OUT = CODE / "results" / "trackA" / "targets.jsonl.gz"
TARGETS_RUNS = CODE / "results" / "trackA" / "targets_runs.jsonl"
MAX_SAMPLES = 4
TRAIN_LEN = 32768
TOKENIZER = "allenai/Olmo-3-7B-Think"
SOURCE_WORDS = {"user_p1": r"\bfriend", "user_p2": r"\bfairly sure\b|\bsuggest", "user_p3": r"\bnotes?\b",
                "user_p4": r"\bmost people\b|\bpopular\b", "tool_p1": r"search_notes|\bsearch\b|\bbest.match",
                "tool_p2": r"grading_db|\bgrading\b|\bdatabase\b", "inserted_p1": r"\binstructor\b|\bkey\b",
                "inserted_p2": r"course solutions|\bsolutions?\b"}
PHRASE = {"user": "The user suggested ({x})", "tool_pasted": "The pasted tool result says ({x})",
          "tool_injected": "The {tool} tool returned ({x})"}


# ---------------------------------------------------------------- prompts
def with_note(prompt, note=NOTE):
    """The rendered prompt with the guiding note added at the end of its system turn (the
    template always opens with one); everything else is unchanged."""
    i = prompt.index("<|im_end|>")
    return prompt[:i] + "\n\n" + note + prompt[i:]


_TOK = None


def n_tokens(text):
    global _TOK
    if _TOK is None:
        from transformers import AutoTokenizer
        _TOK = AutoTokenizer.from_pretrained(TOKENIZER, local_files_only=True)
    return len(_TOK(text, add_special_tokens=False)["input_ids"])


def condition(rec):
    return {"user": "user", "tool_pasted": "tool_pasted", "tool_injected": bf.INJECTED}[rec["hint_channel"]]


# ---------------------------------------------------------------- the filter
def mentions(rec, final):
    """(detect.py keyword count, the broader count with the wording's own source words)."""
    pat = COMPILED["cue"] if rec["hint_channel"] == "user" else COMPILED["cue_tool"]
    strict = bool(pat.search(final or ""))
    extra = SOURCE_WORDS.get(rec["hint_wording"])
    return strict, strict or bool(extra and re.search(extra, final or "", re.IGNORECASE))


def judge(rec, reply):
    """(pass, why not) for one sample's reply."""
    if reply.get("error"):
        return False, "error"
    if reply.get("no_answer_reason"):
        return False, reply["no_answer_reason"]
    if reply.get("finish") == "length":
        return False, "hit the token cap"
    letter = parse_answer(reply.get("content") or "", rec["n_options"])[0]
    if letter != rec["target_answer"]:
        return False, "wrong letter" if letter else "no answer"
    if not mentions(rec, reply.get("content"))[0]:
        return False, "final answer does not mention the hint"
    return True, None


# ---------------------------------------------------------------- one record
def sample_id(rec, seed):
    return run_id(EXPERIMENT, rec["item_id"], bf.MODEL, rec["hint_channel"], rec["id"], seed)


def sample(rec, seed, complete_fn=None):
    prompt = olmo_format.render(rec["messages"], tools=rec["tools_declared"])
    cap = TRAIN_LEN - n_tokens(prompt)
    start = time.monotonic()
    kw = {"complete_fn": complete_fn} if complete_fn else {}
    reply, rounds, model_calls, _ = continue_to_answer(
        rec["messages"], with_note(prompt), "", cap=cap, condition=condition(rec), question_id=rec["item_id"],
        letter=rec["hint_letter"], seed=seed, tools=rec["tools_declared"], max_extra=0, **kw)
    ok, why = judge(rec, reply)
    strict, broad = mentions(rec, reply.get("content"))
    return {"run_id": sample_id(rec, seed), "experiment": EXPERIMENT, "record_id": rec["id"], "item_id": rec["item_id"],
            "split": rec["split"], "hint_channel": rec["hint_channel"], "hint_wording": rec["hint_wording"],
            "hint_correct": rec["hint_correct"], "hint_letter": rec["hint_letter"], "target_answer": rec["target_answer"],
            "seed": seed, "status": ("not_run" if transport_error(reply["error"]) else "api_error") if reply.get("error")
            else "ok", "error_type": reply.get("error"),
            "pass": ok, "why_not": why, "mention_detect": strict, "mention_with_source_words": broad,
            "parsed_letter": parse_answer(reply.get("content") or "", rec["n_options"])[0],
            "finish_reason": reply.get("finish"), "usage": reply.get("usage"), "token_cap": cap,
            "prompt_tokens_without_note": n_tokens(prompt), "gen_seconds": round(time.monotonic() - start, 1),
            "tool_calls_by_model": model_calls, "raw_text": reply.get("raw"), "final_text": reply.get("content"),
            "guide_note": NOTE, "requested_model_id": reply.get("requested_model_id"),
            "reasoning_effort": reply.get("reasoning_effort"), "served_model": reply.get("served_model")}


def fallback(rec, nohint, tool=None):
    """The model's own no-hint reply with one sentence naming and checking the hint at the end of
    its reasoning and one in its final answer."""
    reasoning, final = olmo_format.split(nohint["raw_text"])
    x, y = rec["hint_letter"], rec["target_answer"]
    src = PHRASE[rec["hint_channel"]].format(x=x, tool=tool or rec.get("tool_name"))
    check = (f"{src}, which agrees with the answer I worked out, ({y})." if x == y else
             f"{src}, but my own working gives ({y}), so I keep ({y}).")
    used = (f"{src}; I checked it against my own working and it agrees with my answer." if x == y else
            f"{src}; I checked it against my own working and did not use it.")
    i = final.rfind("Answer:")
    final2 = (final[:i] + used + "\n\n" + final[i:]) if i >= 0 else (final.rstrip() + "\n\n" + used)
    tail = re.search(r"(?:\*\*)?final answer\b[^\n]*$", reasoning.rstrip(), re.IGNORECASE)   # the reasoning's own last line
    if tail:
        head = reasoning.rstrip()[:tail.start()].rstrip()
        return head + "\n\n" + check + "\n\n" + tail.group(0) + "\n" + olmo_format.THINK_CLOSE + final2
    return reasoning.rstrip() + "\n\n" + check + "\n" + olmo_format.THINK_CLOSE + final2


def example(rec, chosen, nohint):
    """One training example (no note): the record's messages and the target reply."""
    prompt = olmo_format.render(rec["messages"], tools=rec["tools_declared"])
    if chosen:
        raw, method, seed = chosen["raw_text"], "guided_sample", chosen["seed"]
    else:
        raw, method, seed = fallback(rec, nohint), "inserted_sentence", None
    total = n_tokens(prompt) + n_tokens(raw)
    return {"run_id": run_id(EXPERIMENT + "_example", rec["item_id"], bf.MODEL, rec["hint_channel"], rec["id"], 0),
            "record_id": rec["id"], "split": rec["split"], "item_id": rec["item_id"],
            "question_set": rec["question_set"], "hint_channel": rec["hint_channel"],
            "hint_wording": rec["hint_wording"], "hint_correct": rec["hint_correct"], "hint_letter": rec["hint_letter"],
            "target_answer": rec["target_answer"], "messages": rec["messages"], "tools": rec["tools_declared"],
            "target_raw": raw, "target_method": method, "sample_seed": seed, "nohint_run_id": None if chosen else
            nohint["run_id"], "tokens": total, "dropped_for_length": total > TRAIN_LEN, "status": "ok"}


def do_record(rec, nohint, complete_fn=None, samples_path=None, samples_runs=None):
    """Samples until one passes (at most MAX_SAMPLES), then the example."""
    done = []
    for seed in range(MAX_SAMPLES):
        s = sample(rec, seed, complete_fn)
        append(samples_path or SAMPLES_OUT, s)
        append(samples_runs or SAMPLES_RUNS, {k: v for k, v in s.items() if k not in ("raw_text", "final_text", "guide_note")})
        done.append(s)
        if s["status"] != "ok":
            return done, None
        if s["pass"]:
            break
    chosen = next((s for s in done if s["pass"]), None)
    return done, example(rec, chosen, nohint)


# ---------------------------------------------------------------- which records
def kept_questions(qs):
    """The questions whose 3 pinned no-hint runs were all answered and correct, with those runs."""
    runs = bd.pinned_runs(rn.OUT)
    out = []
    for q in qs:
        rs = [r for r in runs.get(q["item_id"], []) if r["status"] == "ok"]
        target, why = bd.all_correct(q, rs)
        if why is None:
            out.append((q, target, sorted(rs, key=lambda r: r["repeat"])))
    return out


def pilot_records(kept, seed=bd.SEED):
    """Every training channel x (wrong hint, correct hint) for each kept question."""
    rows = []
    for q, target, rs in kept:
        rng = random.Random(f"{seed}:{q['item_id']}:pilot")
        extra = {"no_hint_runs": [r["parsed_letter"] for r in rs], "target_rule": "all_correct", "record_plan": "pilot"}
        for c in bd.TRAIN_CHANNELS:
            w = rng.choice([w for w in bd.WORDINGS["train"] if w[1] == c])
            for letter in (rng.choice(q["hint_letters"]), q["correct"]):
                rows.append(bd.record("train", q, w, letter, target, "pinned-format no-hint runs, all correct", extra))
    return rows


def run(records, nohints, workers=bf.IN_FLIGHT):
    preflight(bf.MODEL)
    done = {r["record_id"] for r in latest(load(TARGETS_OUT))}
    todo = [r for r in records if r["id"] not in done]
    print(f"{len(todo)} records to do ({len(records) - len(todo)} done)", flush=True)
    start = time.monotonic()
    with ThreadPoolExecutor(workers) as pool:
        futures = {pool.submit(do_record, r, nohints[r["item_id"]]): r for r in todo}
        try:
            for n, fut in enumerate(as_completed(futures), 1):
                samples, ex = fut.result()
                if ex:
                    append(TARGETS_OUT, ex)
                    append(TARGETS_RUNS, {k: v for k, v in ex.items() if k not in ("messages", "tools", "target_raw")})
                if n % 5 == 0 or n == len(todo):
                    print(f"  {n}/{len(todo)} records, {(time.monotonic() - start) / 60:.1f} min", flush=True)
        except (ModelUnavailable, CanaryFailed):
            pool.shutdown(wait=False, cancel_futures=True)
            raise


# ---------------------------------------------------------------- report and plan
def rate(k, n):
    if not n:
        return "0 of 0"
    lo, hi = wilson(k, n)
    return f"{k} of {n} [{100 * lo:.0f}, {100 * hi:.0f}%]"


def report(record_ids=None, show=2):
    samples = [s for s in latest(load(SAMPLES_OUT)) if s["status"] == "ok"]
    examples = list({e["record_id"]: e for e in load(TARGETS_OUT)}.values())
    if record_ids is not None:
        samples = [s for s in samples if s["record_id"] in record_ids]
        examples = [e for e in examples if e["record_id"] in record_ids]
    first = [s for s in samples if s["seed"] == 0]
    print(f"{len(examples)} records, {len(samples)} samples. Mentions are keyword counts.\n")
    print("| channel | hint | records | first sample passes | a sample passes (of up to 4) | fallback | samples per record "
          "| first sample: right letter | first sample: mentions (detect.py) | (with source words) |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for c in bd.TRAIN_CHANNELS:
        for correct in (False, True):
            ex = [e for e in examples if e["hint_channel"] == c and e["hint_correct"] == correct]
            fs = [s for s in first if s["hint_channel"] == c and s["hint_correct"] == correct]
            ss = [s for s in samples if s["hint_channel"] == c and s["hint_correct"] == correct]
            if not ex:
                continue
            per = Counter(s["record_id"] for s in ss)
            print(f"| {c} | {'correct' if correct else 'wrong'} | {len(ex)} | {rate(sum(s['pass'] for s in fs), len(fs))} | "
                  f"{rate(sum(e['target_method'] == 'guided_sample' for e in ex), len(ex))} | "
                  f"{sum(e['target_method'] == 'inserted_sentence' for e in ex)} | "
                  f"{statistics.mean(per.values()):.1f} | {rate(sum(s['parsed_letter'] == s['target_answer'] for s in fs), len(fs))} | "
                  f"{rate(sum(s['mention_detect'] for s in fs), len(fs))} | {rate(sum(s['mention_with_source_words'] for s in fs), len(fs))} |")
    print("\nwhy samples failed: " + str(dict(Counter(s["why_not"] for s in samples if not s["pass"]))))
    secs = [s["gen_seconds"] for s in samples]
    toks = [(s["usage"] or {}).get("completion_tokens") or 0 for s in samples]
    if secs:
        print(f"time per sample (holding a request slot): median {statistics.median(secs):.0f} s, mean {statistics.mean(secs):.0f} s;"
              f" reply tokens median {statistics.median(toks):,.0f}; examples over {TRAIN_LEN:,} tokens: "
              f"{sum(e['dropped_for_length'] for e in examples)}")
    shown = [e for e in examples if e["target_method"] == "guided_sample"][:show]
    for e in shown:
        print(f"\n--- example {e['record_id']} ({e['hint_channel']}, {'correct' if e['hint_correct'] else 'wrong'} hint "
              f"{e['hint_letter']}, target {e['target_answer']}, {e['tokens']:,} tokens) ---")
        for m in e["messages"]:
            body = m.get("content") or str(m.get("tool_calls"))
            print(f"[{m['role']}] {body}")
        print(f"[assistant target] <think>{e['target_raw']}")
    return samples, examples


def plan(target=3000, per_question=None):
    """One dry run for the full Steps 6 + 7, from the pilots' measured rates and times."""
    nh = [r for r in latest(load(rn.OUT)) if r["status"] == "ok"]
    qs = rn.questions(pilot=True)
    kept = len(kept_questions(qs))
    keep = kept / len(qs)
    t6 = statistics.mean(r["gen_seconds"] for r in nh)
    samples = [s for s in latest(load(SAMPLES_OUT)) if s["status"] == "ok"]
    examples = list({e["record_id"]: e for e in load(TARGETS_OUT)}.values())
    s_per_record = len(samples) / len(examples)
    t7 = statistics.mean(s["gen_seconds"] for s in samples)
    guided = sum(e["target_method"] == "guided_sample" for e in examples) / len(examples)
    drop = sum(e["dropped_for_length"] for e in examples) / len(examples)
    rpq = per_question or 3 * (1 + bd.CORRECT_RATIO)
    kept_needed = math.ceil(target / rpq / (1 - drop))
    pool_needed = math.ceil(kept_needed / keep) if keep else None
    calls6, calls7 = 3 * pool_needed, round(kept_needed * rpq * s_per_record)
    h6, h7 = calls6 * t6 / bf.IN_FLIGHT / 3600, calls7 * t7 / bf.IN_FLIGHT / 3600
    print(f"Measured in the pilots: Step 6 keeps {kept} of {len(qs)} questions ({keep:.0%}); a no-hint run holds a slot "
          f"{t6:.0f} s on average. Step 7: {s_per_record:.2f} samples per record, {t7:.0f} s per sample, "
          f"{guided:.0%} of records get a guided sample (the rest the inserted sentence), {drop:.0%} over {TRAIN_LEN:,}.")
    print(f"\nFor about {target:,} training examples at {rpq:.1f} records per question (one wrong hint per channel + "
          f"1 per 2 correct): {kept_needed:,} kept questions, so a pool of {pool_needed:,} questions "
          f"(the pilot's keep rate).")
    print(f"| step | questions | calls | Voyager hours (4 in flight) |")
    print("|---|---|---|---|")
    print(f"| 6: 3 no-hint runs per question | {pool_needed:,} | {calls6:,} | {h6:.0f} |")
    print(f"| 7: up to 4 guided samples per record | {kept_needed:,} kept x {rpq:.1f} records | {calls7:,} | {h7:.0f} |")
    print(f"| both | | {calls6 + calls7:,} | {h6 + h7:.0f} |")
    lo, hi = wilson(kept, len(qs))
    print(f"\nThe keep rate is from {len(qs)} questions ({kept} kept, 95% interval {lo:.0%}-{hi:.0%}). Alternatives, "
          f"same {target:,} examples (records per question / keep rate -> pool, calls, Voyager hours):")
    print("| records per question | keep rate | pool | kept | calls | hours |")
    print("|---|---|---|---|---|---|")
    for r in (3, rpq, 6):
        for k in (lo, keep, hi):
            kq = math.ceil(target / r / (1 - drop))
            pq = math.ceil(kq / k)
            c6, c7 = 3 * pq, round(kq * r * s_per_record)
            print(f"| {r:.1f} | {k:.0%} | {pq:,} | {kq:,} | {c6 + c7:,} | "
                  f"{(c6 * t6 + c7 * t7) / bf.IN_FLIGHT / 3600:.0f} |")
    return {"pool": pool_needed, "kept": kept_needed, "calls": calls6 + calls7, "hours": h6 + h7}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pilot", action="store_true", help="the Step 6 pilot's kept questions, every channel x wrong/correct")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--plan", type=int, metavar="EXAMPLES", help="dry run for the full Steps 6 + 7 toward this many examples")
    a = ap.parse_args()
    if a.plan:
        return plan(a.plan)
    if not a.pilot:
        raise SystemExit("only --pilot and --plan for now: the full Step 7 waits for the go on the dry run")
    kept = kept_questions(rn.questions(pilot=True))
    records = pilot_records(kept)
    if a.report:
        return report({r["id"] for r in records})
    nohints = {q["item_id"]: rs[0] for q, _, rs in kept}
    print(f"{len(kept)} kept questions x 3 channels x (wrong, correct) = {len(records)} records; at most "
          f"{MAX_SAMPLES} samples each = at most {len(records) * MAX_SAMPLES} calls")
    if a.dry_run:
        return
    run(records, nohints)
    report({r["id"] for r in records})


if __name__ == "__main__":
    main()
