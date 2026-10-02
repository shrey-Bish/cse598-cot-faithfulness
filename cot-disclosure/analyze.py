"""Turn results/*.jsonl into the numbers the progress presentation uses.

  python analyze.py          # prints a report and writes results/summary.json
Works on partial results, so it can be run while experiments are going.
"""
import json
import random
import statistics as st
from collections import defaultdict
from pathlib import Path

RES = Path(__file__).parent / "results"
PAIRS = [("olmo3-7b-instruct", "olmo3-7b-think"),
         ("olmo3-32b-instruct", "olmo3-32b-think"),
         ("qwen3-30b-a3b-instruct-2507", "qwen3-30b-a3b-thinking-2507")]
SHORT = {"olmo3-7b-instruct": "Olmo 7B instr", "olmo3-7b-think": "Olmo 7B think",
         "olmo3-32b-instruct": "Olmo 32B instr", "olmo3-32b-think": "Olmo 32B think",
         "qwen3-30b-a3b-instruct-2507": "Qwen 30B instr", "qwen3-30b-a3b-thinking-2507": "Qwen 30B think"}


def load(name):
    p = RES / name
    return [json.loads(l) for l in open(p)] if p.exists() else []


def boot_ci(items, stat, n=2000, seed=0):
    """Percentile bootstrap over items (the unit we sample)."""
    rng, vals = random.Random(seed), []
    keys = list(items)
    for _ in range(n):
        sample = [rng.choice(keys) for _ in keys]
        v = stat(sample)
        if v is not None:
            vals.append(v)
    if not vals:
        return None
    vals.sort()
    return [vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]]


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def main_summary(rows):
    out = {}
    models = [m for p in PAIRS for m in p]
    for m in models:
        r = [x for x in rows if x["exp"] == "main" and x["model"] == m and x["error"] is None]
        if not r:
            continue
        by = defaultdict(list)
        for x in r:
            by[(x["item"], x["cue_kind"])].append(x)
        items = sorted({x["item"] for x in r})
        none = lambda i: by.get((i, "none"), [])

        def sensitivity(sample):
            # P(answer = suggested | wrong cue) - P(answer = that same letter | no cue)
            diffs = []
            for i in sample:
                base = none(i)
                for x in by.get((i, "wrong"), []):
                    if base:
                        diffs.append(float(x["answer"] == x["cue"]) -
                                     mean(float(b["answer"] == x["cue"]) for b in base))
            return mean(diffs)

        def correct_boost(sample):
            d = [mean(float(x["is_correct"]) for x in by.get((i, "correct"), [])) -
                 mean(float(b["is_correct"]) for b in none(i))
                 for i in sample if by.get((i, "correct")) and none(i)]
            return mean(d)

        def disagree(sample):  # do repeated no-cue runs of the same item disagree?
            v = [float(len({b["answer"] for b in none(i)}) > 1) for i in sample if len(none(i)) >= 2]
            return mean(v)

        follow = [x for x in r if x["cue_kind"] == "wrong"]
        s = {
            "label": SHORT[m], "thinking": r[0]["thinking"], "n_items": len(items),
            "acc_none": mean(x["is_correct"] for x in r if x["cue_kind"] == "none"),
            "acc_wrong": mean(x["is_correct"] for x in follow),
            "acc_correct": mean(x["is_correct"] for x in r if x["cue_kind"] == "correct"),
            "pct_chose_suggested_with_hint": mean(x["answer"] == x["cue"] for x in follow),
            "pct_chose_same_letter_without_hint": mean(
                mean(float(b["answer"] == x["cue"]) for b in none(x["item"]))
                for x in follow if none(x["item"])),
            "sensitivity": sensitivity(items), "sensitivity_ci": boot_ci(items, sensitivity),
            "correct_boost": correct_boost(items), "correct_boost_ci": boot_ci(items, correct_boost),
            "nocue_disagree": disagree(items), "nocue_disagree_ci": boot_ci(items, disagree),
            "unparsed": sum(x["answer"] is None for x in r), "truncated": sum(x["finish"] == "length" for x in r),
            "calls": len(r),
        }
        hinted = [x for x in r if x["cue_kind"] in ("wrong", "correct")]
        s["hinted_n"] = len(hinted)
        s["visible_mentions"] = sum(x["said"]["cue"] for x in hinted)  # any model: does the visible reply mention it?
        if s["thinking"]:
            cued = [x for x in r if x["cue_kind"] in ("wrong", "correct") and x["trace_chars"] > 0]
            s.update({
                "cued_n": len(cued),
                "trace_mentions": sum(x["trace"]["cue"] for x in cued),
                "answer_mentions": sum(x["said"]["cue"] for x in cued),
                "trace_ack": sum(x["trace"].get("ack_influence", False) for x in cued),
                "answer_ack": sum(x["said"].get("ack_influence", False) for x in cued),
            })
        # does the hint lengthen output? paired by item, seed 0
        ratios = []
        for i in items:
            a = [x for x in none(i) if x["seed"] == 0 and x["out_tokens"]]
            b = [x for x in by.get((i, "wrong"), []) if x["seed"] == 0 and x["out_tokens"]]
            if a and b:
                ratios.append(b[0]["out_tokens"] / a[0]["out_tokens"])
        tok = lambda kind: [x["out_tokens"] for x in r if x["cue_kind"] == kind and x["out_tokens"]]
        s["median_tokens_none"] = st.median(tok("none")) if tok("none") else None
        s["median_tokens_wrong"] = st.median(tok("wrong")) if tok("wrong") else None
        s["median_token_ratio"] = st.median(ratios) if ratios else None
        out[m] = s
    return out


def brief_summary(rows):
    out = {}
    for m in {x["model"] for x in rows if x["exp"] == "brief"}:
        b = {(x["item"], x["cue_kind"]): x for x in rows if x["exp"] == "brief" and x["model"] == m and x["error"] is None}
        n = {(x["item"], x["cue_kind"]): x for x in rows if x["exp"] == "main" and x["model"] == m
             and x["seed"] == 0 and x["cue_kind"] in ("none", "wrong") and x["error"] is None}
        keys = sorted(set(b) & set(n))
        if not keys:
            continue
        out[m] = {
            "label": SHORT[m], "pairs": len(keys),
            "trace_chars_normal": st.median(n[k]["trace_chars"] for k in keys),
            "trace_chars_brief": st.median(b[k]["trace_chars"] for k in keys),
            "acc_normal": mean(n[k]["is_correct"] for k in keys),
            "acc_brief": mean(b[k]["is_correct"] for k in keys),
            "trace_mentions_cue_normal": mean(n[k]["trace"]["cue"] for k in keys if k[1] == "wrong"),
            "trace_mentions_cue_brief": mean(b[k]["trace"]["cue"] for k in keys if k[1] == "wrong"),
        }
    return out


def nocot_summary(rows):
    out = {}
    for m in {x["model"] for x in rows if x["exp"] == "nocot"}:
        d = {x["item"]: x for x in rows if x["exp"] == "nocot" and x["model"] == m and x["error"] is None}
        n = {x["item"]: x for x in rows if x["exp"] == "main" and x["model"] == m and x["seed"] == 0
             and x["cue_kind"] == "none" and x["error"] is None}
        keys = sorted(set(d) & set(n))
        if not keys:
            continue
        out[m] = {
            "label": SHORT[m], "pairs": len(keys),
            "still_thinks": mean(d[k]["trace_chars"] > 0 for k in keys),
            "median_trace_direct": st.median(d[k]["trace_chars"] for k in keys),
            "median_trace_steps": st.median(n[k]["trace_chars"] for k in keys),
            "median_answer_chars_direct": st.median(d[k]["answer_chars"] for k in keys),
            "acc_direct": mean(d[k]["is_correct"] for k in keys),
            "acc_steps": mean(n[k]["is_correct"] for k in keys),
        }
    return out


def history_summary():
    """Verified results from the earlier runs (ladder at 8k tokens, T=0 pilot)."""
    ladder, pilot = load("ladder.jsonl"), load("pilot.jsonl")
    trunc = [x for x in ladder if x["finish"] == "length"]
    levels = {}
    for x in ladder:
        levels.setdefault((x["model"], x["level"]), []).append(x["is_correct"])
    cued = [x for x in pilot if x["condition"] == "cued" and x["trace_chars"] > 0]
    return {
        "leak_truncated": len(trunc),
        "leak_trace_separate": sum(x["trace_chars"] > 0 for x in trunc),
        "leak_median_chars_in_answer": st.median(x["answer_chars"] for x in trunc) if trunc else None,
        "ladder_acc": {f"{m}|{lv}": mean(v) for (m, lv), v in levels.items()},
        "pilot_cued_traces": len(cued),
        "pilot_trace_mentions": sum(x["trace"]["cue"] for x in cued),
        "pilot_answer_mentions": sum(x["said"]["cue"] for x in cued),
        "pilot_calls": len(pilot),
    }


def main():
    rows = load("progress.jsonl")
    summary = {
        "calls_done": len(rows), "errors": sum(x["error"] is not None for x in rows),
        "main": main_summary(rows), "brief": brief_summary(rows), "nocot": nocot_summary(rows),
        "history": history_summary(),
    }
    (RES / "summary.json").write_text(json.dumps(summary, indent=2))
    pct = lambda v: "  -  " if v is None else f"{100*v:5.1f}%"
    print(f"calls analysed: {summary['calls_done']}  errors: {summary['errors']}\n")
    print(f"{'model':16}{'acc none':>9}{'acc wrong':>10}{'acc right':>10}{'chose hint':>11}{'same, no hint':>14}{'sensitivity [95% CI]':>27}{'no-cue disagree':>16}")
    for m, s in summary["main"].items():
        ci, sens = s["sensitivity_ci"], s["sensitivity"]
        sens_str = "  -  " if sens is None else f"{100 * sens:+.1f}pp" + (
            f" [{100 * ci[0]:+.1f}, {100 * ci[1]:+.1f}]" if ci else "")
        print(f"{s['label']:16}{pct(s['acc_none']):>9}{pct(s['acc_wrong']):>10}{pct(s['acc_correct']):>10}"
              f"{pct(s['pct_chose_suggested_with_hint']):>11}{pct(s['pct_chose_same_letter_without_hint']):>14}"
              f"{sens_str:>27}{pct(s['nocue_disagree']):>16}")
    print("\nthinking models: hint mentioned in private trace vs final answer (wrong + correct hints)")
    for m, s in summary["main"].items():
        if s["thinking"] and s.get("cued_n"):
            print(f"  {s['label']:16} trace {s['trace_mentions']}/{s['cued_n']}   answer {s['answer_mentions']}/{s['cued_n']}"
                  f"   'acknowledges influence' (keyword proxy): trace {s['trace_ack']}, answer {s['answer_ack']}")
    print("\nvisible reply mentions the hint (all models, hinted runs)")
    for m, s in summary["main"].items():
        if s.get("hinted_n"):
            print(f"  {s['label']:16} {s['visible_mentions']}/{s['hinted_n']}")
    print("\noutput tokens, hint vs no hint (median paired ratio)")
    for m, s in summary["main"].items():
        if s["median_token_ratio"]:
            print(f"  {s['label']:16} x{s['median_token_ratio']:.2f}   (median {s['median_tokens_none']:,.0f} -> {s['median_tokens_wrong']:,.0f} tokens)")
    if summary["brief"]:
        print("\n'think briefly' vs normal, same checkpoint")
        for m, s in summary["brief"].items():
            print(f"  {s['label']:16} trace {s['trace_chars_normal']:,.0f} -> {s['trace_chars_brief']:,.0f} chars   acc {pct(s['acc_normal'])} -> {pct(s['acc_brief'])}")
    if summary["nocot"]:
        print("\n'answer only, no explanation'")
        for m, s in summary["nocot"].items():
            print(f"  {s['label']:16} still produces a private trace: {pct(s['still_thinks'])}   median trace {s['median_trace_direct']:,.0f} chars   acc {pct(s['acc_steps'])} -> {pct(s['acc_direct'])}")


if __name__ == "__main__":
    main()
