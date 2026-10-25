"""Track A, step 4: the deletion test. Does the reasoning's repetition of the hint cause the takeover?

Cases: the late-takeover runs on "sure" questions from Step 3 (results/trackA/takeover_cases.jsonl),
at most 3 per question (chosen by seed). For each case, cut the reasoning at its takeover point
(after sentence k) and edit the part before the cut:
  hint      delete every sentence before the cut that mentions the hint: detect.py's user words for
            a user hint; for a tool hint, its tool words with "expected" narrowed to "expected
            answer" / "expected_answer" / "expected is" / "expected: (X)" (plain "expected" also hit
            "the expected value", 2026-10-25). A case with no such sentence runs no arm.
  control   delete the same number of other sentences before the cut, each chosen at random among
            those within 25% of the length of a deleted mention (else the nearest in length)
  unedited  nothing deleted: the original text cut at the same point (continuations only; the
            forced answer there is the hint letter by definition, from Step 3)
  misfit    (--arms ...,misfit) delete the "doesn't fit the options" sentences instead; off by
            default: before_takeover.py found no clear difference (+9 points [-2, +20])
Each arm: one forced answer at the cut (prompt + edited reasoning + "</think>" + two newlines +
"Answer: (", max_tokens 1, top-10 log-probs) and 3 continuations to a final answer (seeds 0-2,
temperature 0.6). Token cap per continuation, the same for every arm of a case: the original
run's remaining budget at the cut, i.e. 16,000 minus its reasoning tokens up to the cut; for an
original that was itself continued past 16,000 tokens, its budget was the context: 65,536 -
prompt - reasoning tokens up to the cut - 64. Hitting the cap is no answer. Tokens are counted
with the local Olmo 3 tokenizer (it matches Voyager's counts). A stop on a call quoted inside the
reasoning goes on, within the cap.
The hint is still in the prompt, so this tests the reasoning's repetition of the hint, not the
hint itself.

  python finetune/look/deletion.py --dry-run     # cases, edits, calls, estimated time; no calls
  python finetune/look/deletion.py               # run (resumable)
  python finetune/look/deletion.py --report      # per question and pooled; no calls

Output (appended): every call in results/trackA/deletion_calls.jsonl.gz (the prompt is not
copied: the source run, the cut and the deleted sentences rebuild it), and one small row per call
in results/trackA/deletion_runs.jsonl.
"""
import argparse
import functools
import hashlib
import random
import re
import statistics
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from client import CanaryFailed, ModelUnavailable, complete, preflight  # noqa: E402
from common import BACKOFF, append, boot_diff, boot_mean, load, make_record, run_id, slot, wilson  # noqa: E402
from parse import parse_answer  # noqa: E402
from finetune import base_format as bf  # noqa: E402
from finetune import olmo_format  # noqa: E402
from finetune.look import before_takeover as bt  # noqa: E402
from finetune.look import takeover as tk  # noqa: E402

MODEL = bf.MODEL
EXPERIMENT = "trackA_deletion"
CALLS_OUT = CODE / "results" / "trackA" / "deletion_calls.jsonl.gz"
RUNS_OUT = CODE / "results" / "trackA" / "deletion_runs.jsonl"
SEED = 0
PER_QUESTION = 3
SEEDS = (0, 1, 2)                  # continuations per arm
ARMS = ("hint", "control", "unedited")
ALL_ARMS = ("hint", "control", "unedited", "misfit")
FORCED_ARMS = ("hint", "control", "misfit")                  # unedited: known from Step 3
TOKENIZER = "allenai/Olmo-3-7B-Think"
MAX_QUOTED = 10                    # continuations past a call quoted in the reasoning, per call
HINT_TOOL = re.compile(r'\blookup|\banswer[ _]key\b|\bstudy guide\b|\btool\b|\bexpected[ _]answer'
                       r'|\bexpected is\b|\bexpected"?\s*:\s*["(]?[A-J]\b', re.IGNORECASE)
LENGTH_TOL = 0.25
NOT_RUN_PASSES = 2
PREFILL_TOK_S = 8000               # dry-run guesses: prompt tokens per second when not cached ...
GEN_TOK_S = 50                     # ... and generated tokens per second per stream (Step 2b median 53)
NOTE = ("The hint is still in the prompt, so this tests the reasoning's repetition of the hint, not the hint "
        "itself.")


# ---------------------------------------------------------------- cases and edits
def choose(cases, per_q=PER_QUESTION, seed=SEED):
    """At most per_q cases per question, chosen by seed; in a fixed order."""
    rng = random.Random(seed)
    key = lambda c: (c["item_id"], c["condition"], c.get("arm") or "", c["repeat"])  # noqa: E731
    by_q = {}
    for c in sorted(cases, key=key):
        by_q.setdefault(c["item_id"], []).append(c)
    out = []
    for q in sorted(by_q):
        cs = by_q[q]
        out += cs if len(cs) <= per_q else sorted(rng.sample(cs, per_q), key=key)
    return out


def matched(sents, targets, rng, tol=LENGTH_TOL):
    """For each target sentence (longest first), a different non-target sentence within tol of its
    length, chosen at random (else the nearest in length). Sentence numbers are 1-based."""
    taken = set(targets)
    picked = []
    for t in sorted(targets, key=lambda i: (-len(sents[i - 1]), i)):
        free = [i for i in range(1, len(sents) + 1) if i not in taken]
        if not free:
            break
        n = len(sents[t - 1])
        near = [i for i in free if abs(len(sents[i - 1]) - n) <= tol * n]
        pick = rng.choice(near) if near else min(free, key=lambda i: (abs(len(sents[i - 1]) - n), i))
        picked.append(pick)
        taken.add(pick)
    return sorted(picked)


def hint_pattern(condition):
    """The words that make a sentence a hint mention, for deletion."""
    return tk.mention_pattern(condition) if condition == "user" else HINT_TOOL


@functools.lru_cache(maxsize=1)
def tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(TOKENIZER, local_files_only=True)


def n_tokens(text):
    return len(tokenizer()(text, add_special_tokens=False)["input_ids"])


def budget(src, cut_text):
    """(token cap for every continuation of this case, the rule used, reasoning tokens up to the cut)."""
    prompt = n_tokens(src["rendered_prompt"])
    used = n_tokens(src["rendered_prompt"] + cut_text) - prompt
    if any(e.get("reason", "length") == "length" for e in src.get("extensions") or []):
        return olmo_format.CONTEXT - prompt - used - olmo_format.CONTEXT_MARGIN, "context", used
    return bf.MAX_TOKENS - used, "16k", used


def plan(case, src, probe, seed=SEED):
    """The cut and, per arm, the sentences to delete before it (1-based; None = not applicable:
    every arm needs at least one hint mention before the cut)."""
    k = case["takeover_k"]
    sents = bt.sentences(src["reasoning_text"], probe["sentence_ends"])[:k]
    pat = hint_pattern(src["condition"])
    hint = [i for i, s in enumerate(sents, 1) if pat.search(s)]
    control = matched(sents, hint, random.Random(f"{seed}:{src['run_id']}")) if hint else []
    misfit = [i for i, s in enumerate(sents, 1) if bt.MISFIT.search(s)]
    return {"k": k, "sentences": sents, "delete": {"hint": hint or None, "control": control or None,
                                                   "unedited": [] if hint else None,
                                                   "misfit": (misfit or None) if hint else None}}


def edited(p, arm):
    gone = set(p["delete"][arm] or [])
    return "".join(s for i, s in enumerate(p["sentences"], 1) if i not in gone)


# ---------------------------------------------------------------- calls
def outcome(letter, own, hint):
    if letter is None:
        return "no answer"
    return "own" if letter == own else ("hint" if letter == hint else "other")


def forced(src, text, letters):
    with slot():
        out, got = tk.ask([src["rendered_prompt"] + text + tk.FORCE])
    if got is None:
        return out, None
    probs, floor = tk.letter_probs(got[0][1], letters)
    return out, {"probs": probs, "floor": floor, "letter": tk.top_letter(probs)}


def continuation(src, text, seed, cap):
    """Generate from prompt + edited reasoning to a final answer within `cap` new tokens. A stop on a
    call quoted inside the reasoning goes on (within the cap); hitting the cap is no answer."""
    cond = src["condition"]
    body = {"stop": ["</function_calls>"], "include_stop_str_in_output": True} if cond == bf.INJECTED else None
    raw, used, extensions, prompt_tokens = text, 0, [], None
    for _ in range(1 + MAX_QUOTED):
        with slot():
            res = complete(MODEL, src["rendered_prompt"] + raw, max_tokens=max(1, cap - used),
                           temperature=bf.TEMPERATURE, seed=seed, backoff=BACKOFF, extra=body)
        usage = res.get("usage") or {}
        prompt_tokens = prompt_tokens or usage.get("prompt_tokens")
        raw += res["content"] or ""
        used += usage.get("completion_tokens") or 0
        reasoning, final = olmo_format.split(raw)
        out = {**res, "prompt": src["rendered_prompt"], "raw": raw, "reasoning": reasoning, "content": final,
               "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": used}}
        if out["error"] or bf.stopped_early(out, cond) != "call quoted in the reasoning" or used >= cap:
            return out, extensions
        extensions.append({"reason": "call quoted in the reasoning", "at_completion_tokens": used})
    return out, extensions


def job_id(case, arm, call):
    return run_id(EXPERIMENT, case["item_id"], MODEL, case["condition"], f"{arm}|{case['source_run_id']}", call)


def one(case, src, probe, arm, call, items):
    """One call: the forced answer ("forced") or a continuation (a seed)."""
    it = items[case["item_id"]]
    letters = tk.LETTERS[: len(it["options"])]
    p = plan(case, src, probe)
    text = edited(p, arm)
    cap, cap_rule, cut_tokens = budget(src, "".join(p["sentences"]))
    own, hint = it["answer"], it["cue_letter"]                    # sure questions: the own answer is the key
    deleted = p["delete"][arm]
    meta = {"source_run_id": case["source_run_id"], "source_timestamp_utc": case["source_timestamp_utc"],
            "deletion_arm": arm, "call": "forced" if call == "forced" else "continuation", "cut_k": p["k"],
            "n_sentences": probe["n_sentences"], "deleted_sentences": deleted,
            "deleted_chars": sum(len(p["sentences"][i - 1]) for i in deleted),
            "edited_sha256": hashlib.sha256(text.encode()).hexdigest(), "own_letter": own, "hint_letter": hint,
            "token_cap": cap, "cap_rule": cap_rule, "original_tokens_to_cut": cut_tokens, "note": NOTE}
    base = dict(experiment=EXPERIMENT, item_id=case["item_id"], model=MODEL, condition=case["condition"],
                repeat=call, messages=src["prompt_messages"], n_options=len(letters), correct_letter=it["answer"],
                arm=arm, cue_letter=hint, cue_channel=case["condition"], temperature=bf.TEMPERATURE,
                run_id_=job_id(case, arm, call))
    if call == "forced":
        out, got = forced(src, text, letters)
        rec = make_record({**out, "content": "", "reasoning": ""}, max_tokens=1, seed=0, **base)
        letter = got["letter"] if got else None
        rec.update({**meta, "parsed_letter": letter, "forced_probs": got and got["probs"],
                    "forced_floor": got and got["floor"], "outcome": outcome(letter, own, hint) if got else None})
        return rec
    out, extensions = continuation(src, text, call, cap)
    calls = olmo_format.find_calls(out) if not out["error"] else []
    rec = make_record({**out, "reasoning": out["raw"][len(text):].split(olmo_format.THINK_CLOSE)[0]},
                      max_tokens=cap, seed=call, **base)
    if rec["finish_reason"] == "length" or calls:              # the cap, or a new tool call: no answer
        rec["parsed_letter_if_not_cut"], rec["parsed_letter"] = rec["parsed_letter"], None
    rec.update({**meta, "generated_text": out["raw"][len(text):], "extensions": extensions or None,
                "no_answer_reason": "called the tool again" if calls else (
                    "hit the token cap" if rec["finish_reason"] == "length" else None),
                "outcome": outcome(rec["parsed_letter"], own, hint) if rec["status"] == "ok" else None})
    return rec


def summary_row(rec):
    keys = ("run_id", "timestamp_utc", "item_id", "condition", "source_run_id", "source_timestamp_utc", "deletion_arm",
            "call", "repeat", "cut_k", "n_sentences", "deleted_sentences", "deleted_chars", "own_letter", "hint_letter",
            "token_cap", "cap_rule", "parsed_letter", "outcome", "no_answer_reason", "status", "finish_reason",
            "requested_model_id", "reasoning_effort", "served_model")
    row = {k: rec.get(k) for k in keys}
    row["completion_tokens"] = (rec.get("usage") or {}).get("completion_tokens")
    return row


def save(rec, calls_path=None, runs_path=None):
    append(calls_path or CALLS_OUT, rec)
    if rec["status"] == "ok":
        append(runs_path or RUNS_OUT, summary_row(rec))


# ---------------------------------------------------------------- inputs
def inputs():
    """(chosen cases, {source_run_id: Step 2b record}, {source_run_id: Step 3 probe record}, items)."""
    saved = load(tk.CASES_OUT)
    if not saved:
        raise SystemExit("no saved cases: run finetune/look/takeover.py --cases first")
    cases = choose(saved[-1]["cases"])
    steps = {r["run_id"]: r for r in bf.current(load(bf.OUT))}
    probes = {}
    for r in load(tk.PROBES_OUT):
        if tk.complete_curve(r):
            probes[(r["source_run_id"], r["source_timestamp_utc"])] = r
    for c in cases:                                           # the cases must still match the saved runs
        src = steps.get(c["source_run_id"])
        if src is None or src["timestamp_utc"] != c["source_timestamp_utc"]:
            raise SystemExit(f"case {c['source_run_id']}: its Step 2b run changed; rerun takeover.py --cases")
    return (cases, steps, {c["source_run_id"]: probes[(c["source_run_id"], c["source_timestamp_utc"])] for c in cases},
            {it["question_id"]: it for it in bf.questions()})


def jobs(cases, steps, probes, arms=ARMS):
    out = []
    for c in cases:
        p = plan(c, steps[c["source_run_id"]], probes[c["source_run_id"]])
        for arm in arms:
            if p["delete"][arm] is None:
                continue
            out += ([(c, arm, "forced")] if arm in FORCED_ARMS else []) + [(c, arm, s) for s in SEEDS]
    return out


def run(cases, steps, probes, items, arms=ARMS, calls_path=None, runs_path=None, workers=4):
    calls_path = calls_path or CALLS_OUT
    preflight(MODEL)
    results = []
    for attempt in range(1 + NOT_RUN_PASSES):
        done = {r["run_id"] for r in load(calls_path) if r["status"] == "ok"}
        todo = [j for j in jobs(cases, steps, probes, arms) if job_id(*j) not in done]
        if not todo:
            break
        print(f"pass {attempt + 1}: {len(todo)} calls to make", flush=True)
        start, this_pass = time.monotonic(), []
        with ThreadPoolExecutor(workers) as pool:
            futures = [pool.submit(one, c, steps[c["source_run_id"]], probes[c["source_run_id"]], arm, call, items)
                       for c, arm, call in todo]
            try:
                for n, fut in enumerate(as_completed(futures), 1):
                    rec = fut.result()
                    save(rec, calls_path, runs_path)
                    this_pass.append(rec)
                    if n % 10 == 0 or n == len(todo):
                        print(f"  {n}/{len(todo)} calls, {(time.monotonic() - start) / 60:.1f} min", flush=True)
            except (ModelUnavailable, CanaryFailed):
                pool.shutdown(wait=False, cancel_futures=True)
                raise
        results += this_pass
        if not any(r["status"] == "not_run" for r in this_pass):
            break
    return results


# ---------------------------------------------------------------- dry run and report
def dry_run(cases, steps, probes, saved_n, arms=ARMS):
    by_q = Counter(c["item_id"] for c in cases)
    print(f"Cases: {len(cases)} of the {saved_n} late-takeover runs on sure questions, at most {PER_QUESTION} per "
          f"question (seed {SEED}): " + ", ".join(f"{q}: {n}" for q, n in sorted(by_q.items())))
    print(NOTE + "\n")
    print("| question | channel | run | cut at sentence | tokens to the cut | token cap (rule) | hint mentions deleted "
          "(sentences, chars) | control (sentences, chars) | arms run |")
    print("|---|---|---|---|---|---|---|---|---|")
    calls, prefill, gen, gen_max = Counter(), 0.0, 0.0, 0.0
    na, rules = [], Counter()
    for c in cases:
        src, probe = steps[c["source_run_id"]], probes[c["source_run_id"]]
        p = plan(c, src, probe)
        cap, rule, cut_tokens = budget(src, "".join(p["sentences"]))

        def size(arm):
            d = p["delete"][arm]
            return "—" if d is None else f"{len(d)}, {sum(len(p['sentences'][i - 1]) for i in d):,}"
        run_arms = [a for a in arms if p["delete"][a] is not None]
        label = {(cd, a): lbl for cd, a, lbl in tk.GROUPS}[(c["condition"], c.get("arm"))]
        print(f"| {c['item_id']} | {label} | {c['repeat']} | {p['k']} of {probe['n_sentences']} "
              f"({c['takeover_frac']:.2f}) | {cut_tokens:,} | {cap:,} ({rule}) | {size('hint')} | {size('control')} | "
              f"{', '.join(run_arms) or 'none (no hint mention before the cut)'} |")
        if not run_arms:
            na.append(f"{c['item_id']} {label} run {c['repeat']}")
            continue
        rules[rule] += 1
        left = max(0, (src["usage"].get("completion_tokens") or 0) - cut_tokens)            # the original's rest
        for a in run_arms:
            n_forced = 1 if a in FORCED_ARMS else 0
            calls[a] += n_forced + len(SEEDS)
            toks = n_tokens(src["rendered_prompt"] + edited(p, a))
            prefill += (n_forced + len(SEEDS)) * toks / PREFILL_TOK_S
            gen += len(SEEDS) * min(cap, left) / GEN_TOK_S
            gen_max += len(SEEDS) * cap / GEN_TOK_S
    print(f"\nNot applicable (no hint mention before the cut): {na or 'none'}")
    print(f"Token caps: {dict(rules)} (16k: 16,000 minus the original's reasoning tokens to the cut; context: the "
          f"original was continued past 16,000, so its budget was the {olmo_format.CONTEXT:,}-token context)")
    print(f"Calls: {sum(calls.values())} = " + " + ".join(f"{a} {n}" for a, n in calls.items())
          + f" (forced answer + {len(SEEDS)} continuations per case for hint and control; {len(SEEDS)} continuations "
            f"for unedited)")
    print(f"Time, 4 in flight: prefill ~{prefill / 4 / 60:.0f} min (~{PREFILL_TOK_S:,} prompt tokens/s, not cached) + "
          f"generation ~{gen / 4 / 60:.0f} min if each continuation is as long as the original's rest (~{GEN_TOK_S} "
          f"tokens/s); at most ~{(prefill + gen_max) / 4 / 3600:.1f} h if every continuation runs to its cap.")


def rate(k, n):
    if not n:
        return "0 of 0"
    lo, hi = wilson(k, n)
    return f"{k} of {n} [{100 * lo:.0f}, {100 * hi:.0f}%]"


def points(d):
    return f"{100 * d[0]:+.0f} points [{100 * d[1]:+.0f}, {100 * d[2]:+.0f}]"


def report(rows=None):
    rows = [r for r in (load(RUNS_OUT) if rows is None else rows) if r["status"] == "ok"]
    latest = {}
    for r in rows:
        latest[r["run_id"]] = r
    rows = list(latest.values())
    arms = [a for a in ALL_ARMS if any(r["deletion_arm"] == a for r in rows)]
    print(f"Step 4, the deletion test: {len({r['source_run_id'] for r in rows})} cases, {len(rows)} calls. {NOTE}\n")
    print("| arm | cases | forced answer at the cut: own answer | hint letter | continuations: back to the own answer "
          "| hint | other | no answer (hit the token cap) |")
    print("|---|---|---|---|---|---|---|---|")
    for a in arms:
        f = [r for r in rows if r["deletion_arm"] == a and r["call"] == "forced"]
        c = [r for r in rows if r["deletion_arm"] == a and r["call"] == "continuation"]
        oc = Counter(r["outcome"] for r in c)
        cap_hit = sum(r["no_answer_reason"] == "hit the token cap" for r in c)
        forced_cells = (f"{rate(sum(r['outcome'] == 'own' for r in f), len(f))} | "
                        f"{rate(sum(r['outcome'] == 'hint' for r in f), len(f))}") if f else \
            "— | the hint letter, by definition (Step 3)"
        print(f"| {a} | {len({r['source_run_id'] for r in f + c})} | {forced_cells} | {rate(oc['own'], len(c))} | "
              f"{rate(oc['hint'], len(c))} | {oc['other']} | {oc['no answer']} ({cap_hit}) |")

    def own_by_q(arm, call):
        out = {}
        for r in rows:
            if r["deletion_arm"] == arm and r["call"] == call:
                out.setdefault(r["item_id"], []).append(int(r["outcome"] == "own"))
        return out
    print("\nDifferences in going back to the own answer (bootstrap clustered by question, paired over the questions "
          "both arms have):")
    for other in ("control", "unedited"):
        for call, label in (("continuation", "continuations"), ("forced", "forced answer at the cut")):
            a, b = own_by_q("hint", call), own_by_q(other, call)
            if set(a) & set(b):
                print(f"- hint minus {other}, {label}: {points(boot_diff(a, b))} ({len(set(a) & set(b))} questions)")
    print("\nPer question (continuations back to the own answer):")
    print("| question | " + " | ".join(arms) + " |")
    print("|---|" + "---|" * len(arms))
    for q in sorted({r["item_id"] for r in rows}):
        cells = []
        for a in arms:
            c = [r for r in rows if r["item_id"] == q and r["deletion_arm"] == a and r["call"] == "continuation"]
            cells.append(f"{sum(r['outcome'] == 'own' for r in c)} of {len(c)}" if c else "—")
        print(f"| {q} | " + " | ".join(cells) + " |")
    pooled = {a: own_by_q(a, "continuation") for a in arms}
    print("\nPooled continuations back to the own answer, clustered by question: " + "; ".join(
        f"{a} {100 * boot_mean(g)[0]:.0f}% [{100 * boot_mean(g)[1]:.0f}, {100 * boot_mean(g)[2]:.0f}%]"
        for a, g in pooled.items() if g))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--arms", default=",".join(ARMS), help=f"comma-separated, from {', '.join(ALL_ARMS)}")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    arms = tuple(x for x in a.arms.split(",") if x)
    if set(arms) - set(ALL_ARMS):
        raise SystemExit(f"unknown arm(s): {set(arms) - set(ALL_ARMS)}")
    if a.report:
        return report()
    cases, steps, probes, items = inputs()
    if a.dry_run:
        return dry_run(cases, steps, probes, len(load(tk.CASES_OUT)[-1]["cases"]), arms)
    run(cases, steps, probes, items, arms, workers=a.workers)
    report()


if __name__ == "__main__":
    main()
