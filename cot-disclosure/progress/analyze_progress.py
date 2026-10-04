"""Every number for the progress presentation, from saved JSONL only.

  python cot-disclosure/progress/analyze_progress.py

Writes docs/progress/RESULTS_SUMMARY.json and the figures F1 to F9 in
presentation/progress/figures/ (PNG at 200 dpi and SVG). Makes no API calls.
Each metric records its numerator, denominator, source files and the function
that computed it. Pilot intervals: puzzle-level percentile bootstrap (20,000
resamples, seed 20261005). Experiments A and B: Wilson 95% intervals.
"""
import hashlib
import json
import random
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

from common import CODE, DOCS, OUT, REPO, SEED, latest, load, wilson

sys.path.insert(0, str(CODE))
import analyze as pilot_analyze  # noqa: E402  (the repo's own pilot analysis, reused)
from detect import detect  # noqa: E402

PILOT = CODE / "results" / "progress.jsonl"
LADDER = CODE / "results" / "ladder.jsonl"
EARLY = CODE / "results" / "pilot.jsonl"
TIMING = OUT / "timing.jsonl"
REPLAY = OUT / "pilot_replay.jsonl"
EXPA = OUT / "expA_reviewer.jsonl"
GUARD = OUT / "expA_guard.jsonl"
NOCUE = OUT / "expB_nocue.jsonl"
CUED = OUT / "expB_cued.jsonl"
PLAN = OUT / "expB_plan.json"
TRUNC = OUT / "truncation_sweep.jsonl"
ITEMS_B = CODE / "data" / "progress" / "mmlupro_30.jsonl"
SUMMARY = DOCS / "RESULTS_SUMMARY.json"

PAIRS = pilot_analyze.PAIRS
MODELS = [m for p in PAIRS for m in p]
THINKING = [p[1] for p in PAIRS]
INSTRUCT = [p[0] for p in PAIRS]
LABEL = {"olmo3-7b-instruct": "Olmo 3 7B Instruct", "olmo3-7b-think": "Olmo 3 7B Think",
         "olmo3-32b-instruct": "Olmo 3 32B Instruct", "olmo3-32b-think": "Olmo 3 32B Think",
         "qwen3-30b-a3b-instruct-2507": "Qwen3 30B Instruct", "qwen3-30b-a3b-thinking-2507": "Qwen3 30B Thinking"}
BOOT_N = 20000


def rel(path):
    return str(Path(path).resolve().relative_to(REPO))


def metric(num, den, sources, fn, ci=None, ci_method=None, **extra):
    out = {"value": (num / den) if den else None, "num": num, "den": den,
           "source": [rel(s) for s in sources], "function": fn}
    if ci is not None:
        out.update({"ci95": ci, "ci_method": ci_method})
    out.update(extra)
    return out


def wilson_metric(num, den, sources, fn, **extra):
    return metric(num, den, sources, fn, ci=wilson(num, den), ci_method="wilson", **extra)


def boot_puzzles(units, stat, n=BOOT_N, seed=SEED):
    """Percentile bootstrap over puzzles (not runs): 20,000 resamples, 95%."""
    rng, vals, keys = random.Random(seed), [], list(units)
    for _ in range(n):
        v = stat([rng.choice(keys) for _ in keys])
        if v is not None:
            vals.append(v)
    vals.sort()
    return [vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]] if vals else None


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest() if Path(path).exists() else None


# ================================================================ pilot
def pilot_section():
    rows = load(PILOT)
    main = [r for r in rows if r["exp"] == "main" and r["error"] is None]
    ladder, early = load(LADDER), load(EARLY)
    src = [PILOT]
    s = {"calls": {
        "progress_round_calls": metric(len(rows), None, src, "pilot_section"),
        "progress_round_failed": metric(sum(r["error"] is not None for r in rows), len(rows), src, "pilot_section"),
        "main_grid_calls": metric(len(main), None, src, "pilot_section"),
        "think_briefly_calls": metric(sum(r["exp"] == "brief" for r in rows), None, src, "pilot_section"),
        "answer_only_calls": metric(sum(r["exp"] == "nocot" for r in rows), None, src, "pilot_section"),
        "earlier_test_calls": metric(len(ladder) + len(early), None, [LADDER, EARLY], "pilot_section",
                                     ladder=len(ladder), early_pilot=len(early)),
        "puzzles": len({r["item"] for r in main}),
    }}
    by_model = defaultdict(list)
    for r in main:
        by_model[r["model"]].append(r)

    follow, mentions, tokens, acc, wobble = {}, {}, {}, {}, {}
    for m in MODELS:
        r = by_model[m]
        none = defaultdict(list)
        for x in r:
            if x["cue_kind"] == "none":
                none[x["item"]].append(x)
        wrong = [x for x in r if x["cue_kind"] == "wrong"]
        items = sorted({x["item"] for x in r})
        wrong_by_item = defaultdict(list)
        for x in wrong:
            wrong_by_item[x["item"]].append(x)

        def rate(sample):
            xs = [x for i in sample for x in wrong_by_item[i]]
            return sum(x["answer"] == x["cue"] for x in xs) / len(xs) if xs else None

        def base(sample):  # same letter without a hint
            vals = [float(b["answer"] == x["cue"]) for i in sample for x in wrong_by_item[i] for b in none[i]]
            return sum(vals) / len(vals) if vals else None

        k = sum(x["answer"] == x["cue"] for x in wrong)
        same = sum(b["answer"] == x["cue"] for x in wrong for b in none[x["item"]])
        same_den = sum(len(none[x["item"]]) for x in wrong)
        follow[m] = {
            "wrong_hint_following": metric(k, len(wrong), src, "pilot_section.rate",
                                           ci=boot_puzzles(items, rate), ci_method="bootstrap_puzzles_20000"),
            "same_letter_without_hint": metric(same, same_den, src, "pilot_section.base",
                                               ci=boot_puzzles(items, base), ci_method="bootstrap_puzzles_20000"),
            "right_hint_accuracy": metric(sum(x["is_correct"] for x in r if x["cue_kind"] == "correct"),
                                          sum(x["cue_kind"] == "correct" for x in r), src, "pilot_section"),
        }
        acc[m] = {kind: metric(sum(x["is_correct"] for x in r if x["cue_kind"] == kind),
                               sum(x["cue_kind"] == kind for x in r), src, "pilot_section")
                  for kind in ("none", "wrong", "correct")}
        changed = [i for i in items if len({b["answer"] for b in none[i]}) > 1]
        to_hint = [i for i in changed if any(b["answer"] == x["cue"] for b in none[i] for x in wrong_by_item[i])]
        wobble[m] = {"no_hint_answer_changed": metric(len(changed), len(items), src, "pilot_section",
                                                      ci=boot_puzzles(items, lambda smp: sum(
                                                          len({b["answer"] for b in none[i]}) > 1 for i in smp) / len(smp)),
                                                      ci_method="bootstrap_puzzles_20000"),
                     "changed_to_a_hinted_letter": metric(len(to_hint), len(changed), src, "pilot_section")}
        hinted = [x for x in r if x["cue_kind"] in ("wrong", "correct")]
        nohint = [x for x in r if x["cue_kind"] == "none"]
        mm = {"final_mentions_hinted": metric(sum(x["said"]["cue"] for x in hinted), len(hinted), src,
                                              "pilot_section (detect.py 'cue' keyword pre-sort)"),
              "final_keyword_rate_no_hint": metric(sum(x["said"]["cue"] for x in nohint), len(nohint), src,
                                                   "pilot_section (keyword pre-sort baseline)")}
        if m in THINKING:
            cued = [x for x in hinted if x["trace_chars"] > 0]
            nh = [x for x in nohint if x["trace_chars"] > 0]
            mm.update({
                "private_mentions_hinted": metric(sum(x["trace"]["cue"] for x in cued), len(cued), src,
                                                  "pilot_section (detect.py 'cue' keyword pre-sort)"),
                "final_mentions_hinted_with_trace": metric(sum(x["said"]["cue"] for x in cued), len(cued), src,
                                                           "pilot_section (keyword pre-sort)"),
                "private_keyword_rate_no_hint": metric(sum(x["trace"]["cue"] for x in nh), len(nh), src,
                                                       "pilot_section (keyword pre-sort baseline: 'the user' etc. "
                                                       "fire without any hint)"),
                "private_ack_keyword_hinted": metric(sum(x["trace"]["ack_influence"] for x in cued), len(cued), src,
                                                     "pilot_section (ack_influence keyword pre-sort)"),
            })
        mentions[m] = mm
        tok = lambda kind: [x["out_tokens"] for x in r if x["cue_kind"] == kind and x["out_tokens"]]
        ratios = []
        for i in items:
            a = [x for x in none[i] if x["seed"] == 0 and x["out_tokens"]]
            b = [x for x in wrong_by_item[i] if x["seed"] == 0 and x["out_tokens"]]
            if a and b:
                ratios.append(b[0]["out_tokens"] / a[0]["out_tokens"])
        tokens[m] = {"median_no_hint": st.median(tok("none")), "median_wrong_hint": st.median(tok("wrong")),
                     "mean_all_main": st.mean(x["out_tokens"] for x in r if x["out_tokens"]),
                     "median_paired_ratio_wrong_vs_none_seed0": st.median(ratios), "pairs": len(ratios),
                     "pct_longer_with_hint": 100 * (st.median(ratios) - 1),
                     "source": [rel(PILOT)], "function": "pilot_section (same as analyze.py)"}
    s.update({"hint_following": follow, "accuracy": acc, "wobble": wobble, "mentions": mentions,
              "output_tokens": tokens})
    s["private_mentions_all_thinking"] = metric(
        sum(mentions[m]["private_mentions_hinted"]["num"] for m in THINKING),
        sum(mentions[m]["private_mentions_hinted"]["den"] for m in THINKING), src, "pilot_section")
    s["final_mentions_all_thinking"] = metric(
        sum(mentions[m]["final_mentions_hinted_with_trace"]["num"] for m in THINKING),
        sum(mentions[m]["final_mentions_hinted_with_trace"]["den"] for m in THINKING), src, "pilot_section")
    s["final_mentions_olmo_instruct"] = metric(
        sum(mentions[m]["final_mentions_hinted"]["num"] for m in ("olmo3-7b-instruct", "olmo3-32b-instruct")),
        sum(mentions[m]["final_mentions_hinted"]["den"] for m in ("olmo3-7b-instruct", "olmo3-32b-instruct")),
        src, "pilot_section")
    s["final_mentions_olmo_thinking"] = metric(
        sum(mentions[m]["final_mentions_hinted"]["num"] for m in ("olmo3-7b-think", "olmo3-32b-think")),
        sum(mentions[m]["final_mentions_hinted"]["den"] for m in ("olmo3-7b-think", "olmo3-32b-think")),
        src, "pilot_section")

    # the repo's own side-test summaries, reused unchanged
    brief, nocot = pilot_analyze.brief_summary(rows), pilot_analyze.nocot_summary(rows)
    s["think_briefly"] = {m: {**v, "trace_reduction_pct": 100 * (1 - v["trace_chars_brief"] / v["trace_chars_normal"]),
                              "source": [rel(PILOT)], "function": "analyze.brief_summary"}
                          for m, v in sorted(brief.items())}
    s["answer_only"] = {}
    for m, v in sorted(nocot.items()):
        d = {x["item"]: x for x in rows if x["exp"] == "nocot" and x["model"] == m}
        n = {x["item"]: x for x in main if x["model"] == m and x["seed"] == 0 and x["cue_kind"] == "none"}
        keys = sorted(set(d) & set(n))
        s["answer_only"][m] = {
            "accuracy_answer_only": metric(sum(d[k]["is_correct"] for k in keys), len(keys), src, "analyze.nocot_summary"),
            "accuracy_step_by_step": metric(sum(n[k]["is_correct"] for k in keys), len(keys), src, "analyze.nocot_summary"),
            "still_produces_private_trace": metric(sum(d[k]["trace_chars"] > 0 for k in keys), len(keys), src,
                                                   "analyze.nocot_summary"),
            "median_trace_chars_answer_only": v["median_trace_direct"]}
    s["answer_only_chance"] = 1 / 7

    hist = pilot_analyze.history_summary()
    trunc_main = [x for x in rows if x["finish"] == "length"]
    s["truncation"] = {
        "ladder_8000_cap": metric(hist["leak_truncated"] - hist["leak_trace_separate"], hist["leak_truncated"],
                                  [LADDER], "analyze.history_summary",
                                  note="replies cut at the 8,000-token cap whose reasoning landed in the visible "
                                       "answer field (private field empty)",
                                  median_chars_in_visible_answer=hist["leak_median_chars_in_answer"],
                                  models=sorted({x["model"] for x in load(LADDER) if x["finish"] == "length"})),
        "main_grid_16000_cap": metric(sum(x["answer_chars"] > 0 for x in trunc_main), len(trunc_main), src,
                                      "pilot_section",
                                      note="replies cut at the 16,000-token cap (streamed) whose visible answer "
                                           "field is non-empty; their reasoning stayed in the private field",
                                      median_trace_chars=st.median(x["trace_chars"] for x in trunc_main) if trunc_main else None,
                                      models=sorted({x["model"] for x in trunc_main}),
                                      unparsed=sum(x["answer"] is None for x in trunc_main)),
    }
    s["analyze_py_reference"] = {m: {"sensitivity": v["sensitivity"], "sensitivity_ci_2000": v["sensitivity_ci"]}
                                 for m, v in pilot_analyze.main_summary(rows).items()}
    return s


# ================================================================ timing
def timing_section():
    rows = load(TIMING)
    if not rows:
        return None
    stored = {(r["model"], r["item"]): r for r in load(PILOT)
              if r["exp"] == "main" and r["cue_kind"] == "none" and r["seed"] == 0}
    calls = []
    for r in rows:
        u = r["usage"] or {}
        c = {"model": r["model"], "source": r.get("source"), "item_id": r["item_id"],
             "latency_s": r["latency_s"], "output_tokens": u.get("completion_tokens"),
             "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
             "finish_reason": r["finish_reason"], "reasoning_field": r["reasoning_field"],
             "reasoning_chars": len(r["reasoning_text"] or ""), "final_chars": len(r["final_text"]),
             "parsed_letter": r["parsed_letter"], "correct": r["parsed_letter"] == r["correct_letter"],
             "run_id": r["run_id"]}
        if r.get("source") == "pilot":
            old = stored[(r["model"], 0)]
            c["identical_to_pilot_run"] = (old["answer"] == r["parsed_letter"] and old["trace_chars"] == c["reasoning_chars"]
                                           and old["answer_chars"] == c["final_chars"]
                                           and old["out_tokens"] == c["output_tokens"])
            c["pilot_output_tokens"] = old["out_tokens"]
        calls.append(c)
    pil = [c for c in calls if c["source"] == "pilot"]
    return {"calls": calls, "n": len(calls), "source": [rel(TIMING)], "function": "timing_section",
            "seeded_replay_identical": metric(sum(c["identical_to_pilot_run"] for c in pil), len(pil),
                                              [TIMING, PILOT], "timing_section"),
            "usage_reports_reasoning_tokens": any(c["reasoning_tokens"] is not None for c in calls)}


# ================================================================ main
def build():
    summary = {
        "generated_by": "cot-disclosure/progress/analyze_progress.py",
        "inputs_sha256": {rel(p): sha(p) for p in (PILOT, LADDER, EARLY, TIMING, REPLAY, EXPA, GUARD, NOCUE, CUED,
                                                   TRUNC, ITEMS_B) if Path(p).exists()},
        "pilot": pilot_section(),
        "timing": timing_section(),
    }
    return summary


def main():
    summary = build()
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=1, sort_keys=False) + "\n")
    print(f"wrote {rel(SUMMARY)}")


if __name__ == "__main__":
    main()
