"""Track A, A42 (Nov 6): A40 + the note on E2, pre-registered in archive/sessions/2026-11-06/2026-11-06_1122_A_a42-prereg.md
before A40 is trained and before any A42 run. The system a40_note is A40's merged model (eval_job.MODEL_OF) with
prompt_only's note at the end of the system turn in every round (eval.NOTED), run in A39's lean design like a40, its
records beside A39's and A40's in $TRACKA_OUT/a39 (eval_a40_note_a39_e2_*; a39.py and a40.py read only their own
systems). Its comparisons are existing runs: A39's base and prompt_only, A40's a40. Nothing here is chosen on an
evaluation question, and nothing is judged by a model.

  python finetune/a42.py --report --out OUT [--qset e2] [--partial] [--a40-not-trained]   # -> OUT/a42_<qset>.json

Measures and statistics as A40's (a40.py): A39's measures on answered runs, paired by question, 95% bootstrap clustered
by question (20,000 resamples, seed 0), under 5 questions "too few questions".
  primary  a40_note against prompt_only by A40's five readings in A40's order (a40.reading), with A40's accuracy label
           beside it (a40.accuracy_label), never changing it.
  R3       A39's R3 for the new combination: a40_note against a40 and against prompt_only, pooled over the wrong-hint
           channels, accuracy on the no-hint runs, by A38's reading (provenance_job.a38_reading).
  R1       Gate 3's rule against base (eval.gate3_rule, gate3.verdict), as A39's and A40's.
Beside them (no decision): each channel's following and acceptance against prompt_only and against a40; false-disclosure
candidates against prompt_only; each difference's no-answer counts; completeness.
Partial (--partial; the A42 log's section 5): the questions with every run of a40_note, a40, prompt_only and base,
labelled "partial: N of 120 questions"; with none, "not run: no GPU time by Nov 15". --a40-not-trained (A40's training
didn't end ok, as the feeder reports it): "not run: A40 not trained", and no reading.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import latest  # noqa: E402
from finetune import a39, a40, gate3  # noqa: E402
from finetune import eval as ev  # noqa: E402
from finetune.gpu import provenance_job as pj  # noqa: E402

SYSTEM = "a40_note"
SYSTEMS = ("base", "prompt_only", "a40", SYSTEM)
PARTS = ("a40", "prompt_only")                             # R3: the combination's parts
REFS = {"prompt_only": "the instruction", "a40": "A40"}
NOT_RUN, NOT_TRAINED = a40.NOT_RUN, "not run: A40 not trained"


def systems(out, qset="e2"):
    """{system: its finished A39-design runs on the set} for the four systems (each run once: its last ok record)."""
    rows = latest([r for r in a39.of_set(a39.read(out)[0], qset) if r.get("status") == "ok"])
    by = {s: [r for r in rows if r.get("system") == s] for s in SYSTEMS}
    return {s: rs for s, rs in by.items() if rs}


def completeness(rows, qset):
    """{system: {expected, ok, missing}}: its own runs (eval.jobs) against its ok records."""
    ok = {r["run_id"] for r in rows if r.get("status") == "ok"}
    out = {}
    for s in SYSTEMS:
        want = {ev.job_id(s, j) for j in ev.jobs(qset=qset, design="a39", system=s)}
        out[s] = {"expected": len(want), "ok": len(want & ok), "missing": len(want - ok)}
    return out


def complete_questions(rows, qset):
    """The questions with every run of all four systems (the partial rule)."""
    ok = {r["run_id"] for r in rows if r.get("status") == "ok"}
    ids = {}
    for s in SYSTEMS:
        for j in ev.jobs(qset=qset, design="a39", system=s):
            ids.setdefault(j["item_id"], []).append(ev.job_id(s, j))
    return sorted(q for q, xs in ids.items() if all(i in ok for i in xs))


def against(by, ref):
    """a40_note minus ref on the four measures (pooled), read by A40's five readings; per channel beside it."""
    a, b = by[SYSTEM], by[ref]
    e = {m: a39.minus(a, b, m) for m in ("following", "acceptance", "accuracy", "hiding")}
    e["reading"] = a40.reading(e["following"], e["acceptance"], e["hiding"], REFS[ref])
    e["accuracy_label"] = a40.accuracy_label(e["accuracy"])
    e["no_answer_imbalance"] = a39.imbalanced(e, a40.KEYS)
    e["by_channel"] = {ch: {m: a39.minus(a, b, m, ch) for m in ("following", "acceptance")} for ch in a39.CHANNELS}
    return e


def r3(by):
    """A39's R3 for a40_note: minus each part alone, pooled over the wrong-hint channels, by A38's reading."""
    e = {"against": list(PARTS), "channel": "pooled"}
    for p in PARTS:
        e[f"minus {p}"] = {m: a39.minus(by[SYSTEM], by[p], m) for m in ("following", "acceptance", "accuracy")}
    f = [e[f"minus {p}"]["following"] for p in PARTS]
    e["reading"] = (a39.FEW if any(x["diff"] is None for x in f) else
                    pj.a38_reading(f, [e[f"minus {p}"]["acceptance"]["diff"] for p in PARTS],
                                   [e[f"minus {p}"]["accuracy"]["diff"] for p in PARTS]))
    e["no_answer_imbalance"] = [f"minus {p} {m}" for p in PARTS for m in ("following", "acceptance", "accuracy")
                                if e[f"minus {p}"][m]["no_answer"]["imbalance"]]
    return e


def r1(by):
    """Gate 3's rule against base, as A39's and A40's R1."""
    v = {"following_vs_base": a39.minus(by[SYSTEM], by["base"], "following"),
         "nohint_accuracy_vs_base": a39.minus(by[SYSTEM], by["base"], "accuracy"),
         "hiding_vs_base": a39.minus(by[SYSTEM], by["base"], "hiding")}
    v["gate3"] = ev.gate3_rule(v["following_vs_base"], v["nohint_accuracy_vs_base"], v["hiding_vs_base"])
    return {**v, **gate3.verdict(v), "acceptance_vs_base": a39.minus(by[SYSTEM], by["base"], "acceptance"),
            "no_answer_imbalance": a39.imbalanced(v, a39.R1_KEYS)}


def report(out, qset="e2", partial=False, a40_not_trained=False):
    rows = a39.of_set(a39.read(out)[0], qset)
    comp = completeness(rows, qset)
    total = len(ev.questions(qset))
    by = systems(out, qset)
    res = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "qset": qset,
           "complete": all(e["missing"] == 0 for e in comp.values()), "completeness": comp,
           "bootstrap": "paired by question (clustered), 20,000 resamples, seed 0; under 5 questions: too few questions",
           "measures": "A39's (eval.system_report's), on answered runs"}
    if a40_not_trained:
        res["label"], by = NOT_TRAINED, {}
    elif partial:
        qs = set(complete_questions(rows, qset))
        by = {s: [r for r in rs if r["item_id"] in qs] for s, rs in by.items()}
        res["label"] = f"partial: {len(qs)} of {total} questions" if qs else NOT_RUN
    else:
        miss = [f"{s} {e['missing']:,} of {e['expected']:,} runs missing" for s, e in comp.items() if e["missing"]]
        res["label"] = f"INCOMPLETE: {'; '.join(miss)}" if miss else f"complete: {total} questions"
    res["questions"] = len({r["item_id"] for r in by.get(SYSTEM, [])})
    res["systems"] = {s: a39.summary(rs) for s, rs in by.items() if rs}
    if res["label"] not in (NOT_RUN, NOT_TRAINED) and all(by.get(s) for s in SYSTEMS):
        res["primary"] = against(by, "prompt_only")
        res["r3"] = r3(by)
        res["r1"] = r1(by)
        res["vs_a40"] = against(by, "a40")
        res["false_disclosure_vs_prompt_only"] = ev.diff(*(ev.answered(a39.chosen(by[s], "following"))
                                                           for s in (SYSTEM, "prompt_only")), ev.false_disclosure)
    Path(out, f"a42_{qset}.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


def text(res):
    d = gate3.fmt_diff
    lines = [f"A42 (a40_note) on {res['qset']}: {res['label']}"]
    if "primary" not in res:
        return "\n".join(lines + ["no reading: " + ("A40 not trained" if res["label"] == NOT_TRAINED else
                                                    "no question has every run of all four systems" if res["label"] == NOT_RUN
                                                    else "a system has no runs yet")])
    for name, ref in (("primary", "prompt_only"), ("vs_a40", "a40")):
        e = res[name]
        label = f", {e['accuracy_label']}" if e["accuracy_label"] else ""
        lines.append(f"a40_note - {ref}: following {d(e['following'])}; acceptance {d(e['acceptance'])}; accuracy "
                     f"{d(e['accuracy'])}; hiding {d(e['hiding'])} -> {e['reading']}{label}"
                     + (" (no decision)" if name == "vs_a40" else "")
                     + (f" [no-answer imbalance: {', '.join(e['no_answer_imbalance'])}]" if e["no_answer_imbalance"] else ""))
        for ch, x in e["by_channel"].items():
            lines.append(f"  {ch:<9}following {d(x['following'])}; acceptance {d(x['acceptance'])} (no decision)")
    e = res["r3"]
    lines.append("R3, a40_note against each part alone (pooled): "
                 + "; ".join(f"- {p}: following {d(e[f'minus {p}']['following'])}" for p in PARTS) + f" -> {e['reading']}")
    r = res["r1"]
    lines.append(f"R1, Gate 3's rule against base: following {d(r['following_vs_base'])}; accuracy "
                 f"{d(r['nohint_accuracy_vs_base'])}; hiding {d(r['hiding_vs_base'])} -> {r['verdict']}"
                 + (f" ({'; '.join(r['failed'])})" if r.get("failed") else ""))
    lines.append(f"false-disclosure candidates, a40_note - prompt_only: {d(res['false_disclosure_vs_prompt_only'])} (no decision)")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true", help="the readings: OUT/a42_<qset>.json and a summary")
    ap.add_argument("--out", default=str(CODE / "results" / "trackA" / "gpu" / "a39"))
    ap.add_argument("--qset", choices=ev.QSETS, default="e2")
    ap.add_argument("--partial", action="store_true", help="the partial rule: the questions with every run of all four")
    ap.add_argument("--a40-not-trained", action="store_true", help='A40\'s training did not end ok: "not run: A40 not trained"')
    a = ap.parse_args(argv)
    if not a.report:
        ap.error("give --report")
    print(text(report(a.out, a.qset, a.partial, a.a40_not_trained)))


if __name__ == "__main__":
    main()
