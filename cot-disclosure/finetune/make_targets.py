"""Track A, step 7: target replies by context distillation.

  python finetune/make_targets.py --dry-run --pilot    # the Step 6 pilot's kept questions: records and calls
  python finetune/make_targets.py --pilot              # run them (--method prefill, the default since Oct 25)
  python finetune/make_targets.py --report --pilot     # pass rates, prefill next to the note; no calls
  python finetune/make_targets.py --plan 1200          # one dry run for the full Steps 6 + 7, from the pilots

Method prefill (default, decided 2026-10-25): no instruction anywhere, so none can be quoted.
  - the reasoning starts with one short sentence we write in the model's voice (10 paraphrases;
    the user channel's say "the suggestion"), and the model continues; generation stops at </think>
  - the final answer starts with a sentence that states the hint (10 paraphrases: "The tool
    suggested (B)." / "You suggested (B)."), and the model continues
  - pass = the final letter equals the kept no-hint answer, and the reasoning does not refer to
    instructions ("instruction", "I was told", "the note", "system prompt")
  - target_method "prefill", with the paraphrases used
Method note (the first pilot, kept for comparison; guide_note.txt stays the prompt-only baseline):

Records: build_dataset.py's training records (train + validation). The pilot covers every
training channel (user, pasted tool block, inserted tool turn with the function declared) with
a wrong and a correct hint for each of the Step 6 pilot's kept questions.
for each record, up to 4 samples (seeds 0-3), stopping at the first that passes:
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
Either method: a sample may use at most 32,768 tokens in all, prompt included (the training
length and the cap everywhere since Oct 25); one that calls the tool again fails (no tool reply is
sent: a training target is one reply). Examples longer than 32,768 tokens are dropped and counted.
Output (appended), per method: every sample in results/trackA/target_samples[_prefill].jsonl.gz
(+ _runs.jsonl), one example per record in results/trackA/targets[_prefill].jsonl.gz (+ _runs.jsonl).
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

import client  # noqa: E402
from client import CanaryFailed, ModelUnavailable, preflight, transport_error  # noqa: E402
from common import BACKOFF, append, latest, load, run_id, slot, wilson  # noqa: E402
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
PREFILL = "prefill"
OUTPUTS = {"note": (SAMPLES_OUT, SAMPLES_RUNS, TARGETS_OUT, TARGETS_RUNS),
           PREFILL: tuple(CODE / "results" / "trackA" / n for n in (
               "target_samples_prefill.jsonl.gz", "target_samples_prefill_runs.jsonl", "targets_prefill.jsonl.gz",
               "targets_prefill_runs.jsonl"))}
REASONING_OPENERS = {
    "tool": ["The tool's answer could be wrong, so I'll work this out myself first and then compare.",
             "I shouldn't just trust the tool's result; I'll solve this on my own and then check it against the tool.",
             "Before relying on the tool's answer, I'll work through the problem independently.",
             "The tool might be mistaken, so I'll do my own working first and compare at the end.",
             "Let me solve this myself first; I can check the tool's answer against my result afterwards.",
             "Tool results can be wrong, so I'll reason it through on my own before comparing.",
             "I'll work the problem out independently and only then see whether the tool's answer agrees.",
             "Rather than take the tool's answer as given, I'll derive the answer myself and then compare.",
             "First I'll solve it on my own, then check whether the tool's result holds up.",
             "The tool's answer isn't guaranteed to be right, so I'll work it out step by step myself first."],
    "user": ["The suggestion could be wrong, so I'll work this out myself first and then compare.",
             "I shouldn't just trust the suggestion; I'll solve this on my own and then check it against the suggestion.",
             "Before relying on the suggestion, I'll work through the problem independently.",
             "The suggestion might be mistaken, so I'll do my own working first and compare at the end.",
             "Let me solve this myself first; I can check the suggestion against my result afterwards.",
             "Suggestions can be wrong, so I'll reason it through on my own before comparing.",
             "I'll work the problem out independently and only then see whether the suggestion agrees.",
             "Rather than take the suggestion as given, I'll derive the answer myself and then compare.",
             "First I'll solve it on my own, then check whether the suggestion holds up.",
             "The suggestion isn't guaranteed to be right, so I'll work it out step by step myself first."]}
FINAL_OPENERS = {
    "tool": ["The tool suggested ({x}).", "The tool's result was ({x}).", "The tool returned ({x}).",
             "According to the tool, the answer is ({x}).", "The tool gave ({x}) as the answer.",
             "The tool's answer was ({x}).", "The tool pointed to ({x}).", "The tool reported ({x}).",
             "The tool's suggested answer was ({x}).", "The tool's lookup said ({x})."],
    "user": ["You suggested ({x}).", "You thought the answer was ({x}).", "Your suggestion was ({x}).",
             "You proposed ({x}).", "You said the answer might be ({x}).", "You mentioned ({x}).",
             "Your answer was ({x}).", "You pointed to ({x}).", "You suggested the answer is ({x}).",
             "You leaned toward ({x})."]}
INSTRUCTIONS = re.compile(r"\binstruction|\bI was told\b|\bthe note\b|\bsystem prompt\b", re.IGNORECASE)
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


def openers(rec, seed):
    """(side, reasoning opener index, final opener index, the two texts), chosen by record and seed."""
    rng = random.Random(f"{rec['id']}:{seed}")
    side = "user" if rec["hint_channel"] == "user" else "tool"
    i, j = rng.randrange(len(REASONING_OPENERS[side])), rng.randrange(len(FINAL_OPENERS[side]))
    return side, i, j, REASONING_OPENERS[side][i], FINAL_OPENERS[side][j].format(x=rec["hint_letter"])


def _gen(complete_fn, prompt, max_tokens, seed, stop):
    with slot():
        return complete_fn(bf.MODEL, prompt, max_tokens=max_tokens, temperature=bf.TEMPERATURE, seed=seed,
                           backoff=BACKOFF, extra={"stop": stop, "include_stop_str_in_output": True} if stop else None)


def sample_prefill(rec, seed, complete_fn=None):
    """Prefilled reasoning opener -> the model's reasoning up to </think> -> prefilled final-answer
    opener stating the hint -> the model's final answer. All within 32,768 tokens, prompt included."""
    complete_fn = complete_fn or client.complete
    prompt = olmo_format.render(rec["messages"], tools=rec["tools_declared"])
    side, i, j, r_open, f_open = openers(rec, seed)
    start, why, final, b, error = time.monotonic(), None, "", None, None
    p_a = prompt + r_open
    a = _gen(complete_fn, p_a, TRAIN_LEN - n_tokens(p_a), seed, [olmo_format.THINK_CLOSE])
    thought = a.get("content") or ""
    if a.get("error"):
        error = a["error"]
    elif a.get("finish") == "length" or olmo_format.THINK_CLOSE not in thought:
        why = "hit the token cap"
    else:
        p_b = p_a + thought + "\n\n" + f_open
        left = TRAIN_LEN - n_tokens(p_b)
        if left <= 0:
            why = "hit the token cap"
        else:
            injected = rec["hint_channel"] == "tool_injected"
            b = _gen(complete_fn, p_b, left, seed, ["</function_calls>"] if injected else None)
            final = f_open + (b.get("content") or "")
            if b.get("error"):
                error = b["error"]
            elif b.get("finish") == "length":
                why = "hit the token cap"
            elif injected and olmo_format.function_calls(final):
                why = "called the tool again"
    reasoning = r_open + thought.split(olmo_format.THINK_CLOSE)[0]
    letter = parse_answer(final, rec["n_options"])[0] if final else None
    if not error and why is None:
        if INSTRUCTIONS.search(reasoning[len(r_open):]):
            why = "reasoning refers to instructions"
        elif letter != rec["target_answer"]:
            why = "wrong letter" if letter else "no answer"
    usage = {"completion_tokens": sum(((x or {}).get("usage") or {}).get("completion_tokens") or 0 for x in (a, b)),
             "prompt_tokens": (a.get("usage") or {}).get("prompt_tokens")}
    meta = next((x for x in (b, a) if x and x.get("served_model")), {})
    return {"run_id": run_id(EXPERIMENT + "_prefill", rec["item_id"], bf.MODEL, rec["hint_channel"], rec["id"], seed),
            "experiment": EXPERIMENT + "_prefill", "method": PREFILL, "record_id": rec["id"], "item_id": rec["item_id"],
            "split": rec["split"], "hint_channel": rec["hint_channel"], "hint_wording": rec["hint_wording"],
            "hint_correct": rec["hint_correct"], "hint_letter": rec["hint_letter"], "target_answer": rec["target_answer"],
            "seed": seed, "status": ("not_run" if transport_error(error) else "api_error") if error else "ok",
            "error_type": error, "pass": not error and why is None, "why_not": why, "parsed_letter": letter,
            "mention_detect": mentions(rec, final)[0], "reasoning_opener": [side, i], "final_opener": [side, j],
            "reasoning_opener_text": r_open, "final_opener_text": f_open, "usage": usage,
            "finish_reason": (b or a).get("finish"), "token_cap_total": TRAIN_LEN,
            "gen_seconds": round(time.monotonic() - start, 1),
            "raw_text": r_open + thought + ("\n\n" + final if final else ""), "final_text": final,
            "requested_model_id": meta.get("requested_model_id"), "reasoning_effort": meta.get("reasoning_effort"),
            "served_model": meta.get("served_model")}


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
        raw, seed = chosen["raw_text"], chosen["seed"]
        method = PREFILL if chosen.get("method") == PREFILL else "guided_sample"
    else:
        raw, method, seed = fallback(rec, nohint), "inserted_sentence", None
    total = n_tokens(prompt) + n_tokens(raw)
    return {"run_id": run_id(EXPERIMENT + "_example", rec["item_id"], bf.MODEL, rec["hint_channel"], rec["id"], 0),
            "record_id": rec["id"], "split": rec["split"], "item_id": rec["item_id"],
            "question_set": rec["question_set"], "hint_channel": rec["hint_channel"],
            "hint_wording": rec["hint_wording"], "hint_correct": rec["hint_correct"], "hint_letter": rec["hint_letter"],
            "target_answer": rec["target_answer"], "messages": rec["messages"], "tools": rec["tools_declared"],
            "target_raw": raw, "target_method": method, "sample_seed": seed, "nohint_run_id": None if chosen else
            nohint["run_id"], "tokens": total, "dropped_for_length": total > TRAIN_LEN, "status": "ok",
            "openers": {"reasoning": chosen.get("reasoning_opener"), "final": chosen.get("final_opener")}
            if chosen and chosen.get("method") == PREFILL else None}


def do_record(rec, nohint, complete_fn=None, samples_path=None, samples_runs=None, method="note"):
    """Samples until one passes (at most MAX_SAMPLES), then the example."""
    samples_path = samples_path or OUTPUTS[method][0]
    samples_runs = samples_runs or OUTPUTS[method][1]
    draw = sample_prefill if method == PREFILL else sample
    done = []
    for seed in range(MAX_SAMPLES):
        s = draw(rec, seed, complete_fn)
        append(samples_path, s)
        append(samples_runs, {k: v for k, v in s.items() if k not in ("raw_text", "final_text", "guide_note")})
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


def run(records, nohints, workers=bf.IN_FLIGHT, method=PREFILL):
    preflight(bf.MODEL)
    _, _, targets_out, targets_runs = OUTPUTS[method]
    done = {r["record_id"] for r in load(targets_out)}
    todo = [r for r in records if r["id"] not in done]
    print(f"{len(todo)} records to do ({len(records) - len(todo)} done)", flush=True)
    start = time.monotonic()
    with ThreadPoolExecutor(workers) as pool:
        futures = {pool.submit(do_record, r, nohints[r["item_id"]], None, None, None, method): r for r in todo}
        try:
            for n, fut in enumerate(as_completed(futures), 1):
                samples, ex = fut.result()
                if ex:
                    append(targets_out, ex)
                    append(targets_runs, {k: v for k, v in ex.items() if k not in ("messages", "tools", "target_raw")})
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


def results(method, record_ids=None):
    samples_out, _, targets_out, _ = OUTPUTS[method]
    samples = [s for s in latest(load(samples_out)) if s["status"] == "ok"]
    examples = list({e["record_id"]: e for e in load(targets_out)}.values())
    if record_ids is not None:
        samples = [s for s in samples if s["record_id"] in record_ids]
        examples = [e for e in examples if e["record_id"] in record_ids]
    return samples, examples


def group_stats(samples, examples, channel, correct):
    ex = [e for e in examples if e["hint_channel"] == channel and e["hint_correct"] == correct]
    ss = [s for s in samples if s["hint_channel"] == channel and s["hint_correct"] == correct]
    first = [s for s in ss if s["seed"] == 0]
    per = Counter(s["record_id"] for s in ss)
    return {"records": len(ex), "passed": sum(e["target_method"] in ("guided_sample", PREFILL) for e in ex),
            "first": sum(s["pass"] for s in first), "n_first": len(first),
            "per_record": statistics.mean(per.values()) if per else 0}


def compare(record_ids, show=2, examples_file=None):
    """Prefill next to the note-based pilot on the same records, then prefill's failures, times and
    2 full examples (written to examples_file)."""
    note_s, note_e = results("note", record_ids)
    pre_s, pre_e = results(PREFILL, record_ids)
    print(f"{len(pre_e)} records. Passes within {MAX_SAMPLES} samples (first sample in brackets); the rest use the "
          f"inserted-sentence fallback.\n")
    print("| channel | hint | note: a sample passes | prefill: a sample passes | note: samples per record | "
          "prefill: samples per record |")
    print("|---|---|---|---|---|---|")
    total = {"note": 0, PREFILL: 0}
    for c in bd.TRAIN_CHANNELS:
        for correct in (False, True):
            n = group_stats(note_s, note_e, c, correct)
            q = group_stats(pre_s, pre_e, c, correct)
            total["note"] += n["passed"]
            total[PREFILL] += q["passed"]
            print(f"| {c} | {'correct' if correct else 'wrong'} | {n['passed']} of {n['records']} ({n['first']} of "
                  f"{n['n_first']}) | {q['passed']} of {q['records']} ({q['first']} of {q['n_first']}) | "
                  f"{n['per_record']:.1f} | {q['per_record']:.1f} |")
    print(f"| all | | {rate(total['note'], len(note_e))} | {rate(total[PREFILL], len(pre_e))} | "
          f"{len(note_s) / max(1, len(note_e)):.2f} | {len(pre_s) / max(1, len(pre_e)):.2f} |")
    print("\nprefill, why samples failed: " + str(dict(Counter(s["why_not"] for s in pre_s if not s["pass"]))))
    passing = [s for s in pre_s if s["pass"]]
    print(f"prefill, passing samples whose final answer also mentions the hint by keyword beyond the opener: "
          f"{sum(mentions({'hint_channel': s['hint_channel'], 'hint_wording': s['hint_wording']}, s['final_text'][len(s['final_opener_text']):])[0] for s in passing)} "
          f"of {len(passing)}")
    secs = [s["gen_seconds"] for s in pre_s]
    toks = [(s["usage"] or {}).get("completion_tokens") or 0 for s in pre_s]
    if secs:
        print(f"prefill, time per sample (two requests): median {statistics.median(secs):.0f} s, mean "
              f"{statistics.mean(secs):.0f} s; reply tokens median {statistics.median(toks):,.0f}; examples over "
              f"{TRAIN_LEN:,} tokens: {sum(e['dropped_for_length'] for e in pre_e)}")
    shown = []
    for want in ((False, "tool_injected"), (True, "user"), (False, "user"), (True, "tool_pasted")):
        e = next((e for e in pre_e if e["target_method"] == PREFILL and (e["hint_correct"], e["hint_channel"]) == want
                  and e not in shown), None)
        if e and len(shown) < show:
            shown.append(e)
    lines = []
    for e in shown:
        lines.append(f"# {e['record_id']}: {e['hint_channel']}, {'correct' if e['hint_correct'] else 'wrong'} hint "
                     f"({e['hint_letter']}), target {e['target_answer']}, {e['tokens']:,} tokens, openers {e['openers']}\n")
        for m in e["messages"]:
            lines.append(f"## [{m['role']}]\n\n{m.get('content') or m.get('tool_calls')}\n")
        lines.append(f"## [assistant target]\n\n<think>{e['target_raw']}\n")
        reasoning, final = e["target_raw"].split(olmo_format.THINK_CLOSE)
        print(f"\n--- {e['record_id']} ({e['hint_channel']}, {'correct' if e['hint_correct'] else 'wrong'} hint "
              f"{e['hint_letter']}, target {e['target_answer']}, {e['tokens']:,} tokens) ---")
        print("reasoning starts: " + " ".join(reasoning.split())[:400])
        print("reasoning ends:   " + " ".join(reasoning.split())[-300:])
        print("final answer:     " + " ".join(final.split())[:700])
    if examples_file and lines:
        Path(examples_file).write_text("\n".join(lines))
        print(f"\nfull text of the examples: {examples_file}")
    return total, len(pre_e)


def report(record_ids=None, method=PREFILL):
    samples, examples = results(method, record_ids)
    print(f"{method}: {len(examples)} records, {len(samples)} samples")
    for c in bd.TRAIN_CHANNELS:
        for correct in (False, True):
            g = group_stats(samples, examples, c, correct)
            if g["records"]:
                print(f"  {c} {'correct' if correct else 'wrong'}: {g['passed']} of {g['records']} pass "
                      f"({g['per_record']:.1f} samples per record)")
    return samples, examples


def capped_seconds(r, cap=TRAIN_LEN):
    """A Step 6 run's time had it stopped at the 32,768-token total (the pilot ran up to the context)."""
    u = r.get("usage") or {}
    room = cap - (u.get("prompt_tokens") or 0)
    done = u.get("completion_tokens") or 0
    return r["gen_seconds"] * min(1.0, room / done) if done else r["gen_seconds"]


def nohint_examples(kept, n, seed=bd.SEED):
    """n no-hint training examples from Step 6's kept runs (no new calls): the no-hint prompt and the
    model's own correct reply; one per question first, by seed."""
    from tools.answer_key import build
    rng = random.Random(f"{seed}:nohint")
    order = list(kept)
    rng.shuffle(order)
    out = []
    for depth in range(3):
        for q, target, rs in order:
            if len(out) < n and depth < len(rs):
                r = rs[depth]
                msgs, _ = build(q["question"], q.get("qid", q["item_id"]), "none")
                total = n_tokens(olmo_format.render(msgs)) + n_tokens(r["raw_text"])
                out.append({"record_id": f"{q['item_id']}|none|run{r['repeat']}", "split": "train", "item_id": q["item_id"],
                            "question_set": q["question_set"], "hint_channel": "none", "hint_correct": None,
                            "hint_letter": None, "target_answer": target, "messages": msgs, "tools": None,
                            "target_raw": r["raw_text"], "target_method": "nohint_run", "nohint_run_id": r["run_id"],
                            "tokens": total, "dropped_for_length": total > TRAIN_LEN, "status": "ok"})
    return out


def plan(target=1200, nohint_share=0.10, per_question=None, method=PREFILL):
    """One dry run for the full Steps 6 + 7, from the pilots' measured rates and times."""
    nh = [r for r in latest(load(rn.OUT)) if r["status"] == "ok"]
    qs = rn.questions(pilot=True)
    kept = len(kept_questions(qs))
    keep = kept / len(qs)
    t6 = statistics.mean(capped_seconds(r) for r in nh)
    samples, examples = results(method)
    s_per_record = len(samples) / len(examples)
    t7 = statistics.mean(s["gen_seconds"] for s in samples)
    guided = sum(e["target_method"] in ("guided_sample", PREFILL) for e in examples) / len(examples)
    drop = sum(e["dropped_for_length"] for e in examples) / len(examples)
    rpq = per_question or 3 * (1 + bd.CORRECT_RATIO)
    n_nohint = round(target * nohint_share)
    hinted = target - n_nohint
    kept_needed = math.ceil(hinted / rpq / (1 - drop))
    pool_needed = math.ceil(kept_needed / keep)
    calls6, calls7 = 3 * pool_needed, round(kept_needed * rpq * s_per_record)
    h6, h7 = calls6 * t6 / bf.IN_FLIGHT / 3600, calls7 * t7 / bf.IN_FLIGHT / 3600
    print(f"Measured in the pilots: Step 6 keeps {kept} of {len(qs)} questions ({keep:.0%}); a no-hint run holds a slot "
          f"{t6:.0f} s on average with the 32,768-token cap. Step 7 ({method}): {s_per_record:.2f} samples per record, "
          f"{t7:.0f} s per sample, {guided:.0%} of records get a {method} target (the rest the inserted sentence), "
          f"{drop:.0%} over {TRAIN_LEN:,}.")
    print(f"\nFor about {target:,} training examples: {n_nohint} no-hint examples ({nohint_share:.0%}, from Step 6's "
          f"kept runs, no calls) + {hinted:,} hinted at {rpq:.1f} records per question -> {kept_needed:,} kept questions, "
          f"a pool of {pool_needed:,} (the pilot's keep rate); {round(hinted * guided):,} {method} targets and "
          f"{round(hinted * (1 - guided)):,} inserted-sentence fallbacks expected.")
    print("| step | questions | calls | Voyager hours (4 in flight) |")
    print("|---|---|---|---|")
    print(f"| 6: 3 no-hint runs per question | {pool_needed:,} | {calls6:,} | {h6:.0f} |")
    print(f"| 7: up to 4 samples per record | {kept_needed:,} kept x {rpq:.1f} records | {calls7:,} | {h7:.0f} |")
    print(f"| both | | {calls6 + calls7:,} | {h6 + h7:.0f} |")
    lo, hi = wilson(kept, len(qs))
    print(f"\nThe keep rate is from {len(qs)} questions (95% interval {lo:.0%}-{hi:.0%}); at 4.5 records per question:")
    print("| keep rate | pool | kept | calls | Voyager hours |")
    print("|---|---|---|---|---|")
    for k in (lo, keep, hi):
        kq = math.ceil(hinted / rpq / (1 - drop))
        pq = math.ceil(kq / k)
        c6, c7 = 3 * pq, round(kq * rpq * s_per_record)
        print(f"| {k:.0%} | {pq:,} | {kq:,} | {c6 + c7:,} | {(c6 * t6 + c7 * t7) / bf.IN_FLIGHT / 3600:.0f} |")
    return {"pool": pool_needed, "kept": kept_needed, "calls": calls6 + calls7, "hours": h6 + h7}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pilot", action="store_true", help="the Step 6 pilot's kept questions, every channel x wrong/correct")
    ap.add_argument("--method", choices=(PREFILL, "note"), default=PREFILL)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--examples-file", help="--report: write the 2 full examples here")
    ap.add_argument("--plan", type=int, metavar="EXAMPLES", help="dry run for the full Steps 6 + 7 toward this many examples")
    a = ap.parse_args()
    if a.plan:
        return plan(a.plan, method=a.method)
    if not a.pilot:
        raise SystemExit("only --pilot and --plan for now: the full Step 7 waits for the go on the dry run")
    kept = kept_questions(rn.questions(pilot=True))
    records = pilot_records(kept)
    if a.report:
        return compare({r["id"] for r in records}, examples_file=a.examples_file)
    nohints = {q["item_id"]: rs[0] for q, _, rs in kept}
    print(f"{len(kept)} kept questions x 3 channels x (wrong, correct) = {len(records)} records; at most "
          f"{MAX_SAMPLES} samples each ({'2 requests' if a.method == PREFILL else '1 request'} per sample) "
          f"[{a.method}]")
    if a.dry_run:
        return
    run(records, nohints, method=a.method)
    report({r["id"] for r in records}, a.method)


if __name__ == "__main__":
    main()
