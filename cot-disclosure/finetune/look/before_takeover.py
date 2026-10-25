"""Track A, before Step 4: what comes just before a late takeover, against a resisted run's
closest approach? On the saved Step 3 curves and Step 2b texts (no calls).

  python finetune/look/before_takeover.py --dry-run   # what it reads
  python finetune/look/before_takeover.py             # the analysis (appends a summary to
                                                      # results/trackA/before_takeover.jsonl)

1. Concentration: the followed runs on "sure" questions (both Step 2b no-hint runs answered and
   correct), per question.
2. (a) Matched comparison: in every hinted run with a dense curve, each onset after the first
       fifth (a probe where the hint letter becomes the leading letter), labelled permanent (the
       takeover: the hint keeps the lead to the end) or temporary (the lead is lost again). Just
       before each onset (the probe after sentence k - 1): does the model's own no-hint answer
       lead, and its probability (outside the top 10 counts as the 10th, an upper bound). Also
       described: the own answer just before a late takeover.
   (b) Late takeovers (followed runs, at or after half the reasoning) against resisted runs'
       closest approaches (the probe after the first fifth where the hint letter peaks): is there a
       sentence saying its own result doesn't fit the options, in the point's sentence or the 3
       before (keyword count, MISFIT; 5 example sentences, one per keyword family)?
   Means and rates come with 95% bootstrap intervals clustered by question; differences are
   paired by question (the questions with both kinds).
"""
import argparse
import random
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import append, boot_diff, boot_mean, load  # noqa: E402
from finetune import base_format as bf  # noqa: E402
from finetune.look import takeover as tk  # noqa: E402

OUT = CODE / "results" / "trackA" / "before_takeover.jsonl"
BEFORE = 3                    # the point's sentence and the 3 before it
SEED = 0
MISFIT_FAMILIES = {
    "doesn't match / fit": r"\b(?:does|do|did|is|are)(?:n't| not) (?:match|fit|correspond|align)\w*",
    "not matching / no match": r"\bnot match(?:ing|es|ed)?\b|\bno match\b|\bmismatch\w*",
    "none of the options": r"\bnone of the (?:options|answers|answer choices|choices|given)",
    "not among / not listed": r"\bnot (?:among|in|one of) the (?:options|answers|answer choices|choices|given)"
                              r"|\b(?:is|are)(?:n't| not) (?:listed|an option|among)",
    "closest / nearest": r"\bclosest\b|\bnearest\b",
}
FAMILY_RX = {name: re.compile(rx, re.IGNORECASE) for name, rx in MISFIT_FAMILIES.items()}
MISFIT = re.compile("|".join(f"(?:{rx})" for rx in MISFIT_FAMILIES.values()), re.IGNORECASE)


def sentences(text, ends):
    """[sentence 1, ..., sentence n] from the reasoning and its sentence ends."""
    starts = [0] + ends[:-1]
    return [text[a:b] for a, b in zip(starts, ends)]


def window(sents, k):
    """Sentences k - BEFORE .. k (1-based), as (sentence number, text)."""
    return [(i, sents[i - 1]) for i in range(max(1, k - BEFORE), k + 1)]


def own_before(r, k):
    """(probability of the own no-hint answer at the probe after sentence k - 1, does it lead there),
    or None without an own answer or a probe there."""
    own = r.get("own_letter")
    probe = next((p for p in r["curve"] if p["k"] == k - 1), None)
    if not own or probe is None:
        return None
    p = probe["probs"].get(own)
    return (p if p is not None else (probe["floor"] or 0.0)), tk.top_letter(probe["probs"]) == own


def onsets(r):
    """[(k, permanent)] for each probe after the first fifth where the hint letter becomes the
    leading letter (the probe before it led with another letter, or none)."""
    n, hint, tops = r["n_sentences"], r["hint_letter"], r["top_letters"]
    ks = [p["k"] for p in r["curve"]]
    return [(ks[i], all(t == hint for t in tops[i:])) for i in range(1, len(ks))
            if tops[i] == hint and tops[i - 1] != hint and ks[i] > tk.FIFTH * n]


def onset_rows(rows):
    """One row per onset in the hinted runs with a dense curve and an own answer."""
    out, skipped = [], Counter()
    for r in rows:
        if r["kind"] == "no hint":
            continue
        if not tk.dense(r):
            skipped["not dense"] += 1
            continue
        for k, permanent in onsets(r):
            ob = own_before(r, k)
            if ob is None:
                skipped["no own answer"] += 1
                continue
            out.append({"item_id": r["item_id"], "source_run_id": r["source_run_id"], "kind": r["kind"], "k": k,
                        "permanent": permanent, "own_prob_before": ob[0], "own_leads_before": ob[1]})
    return out, skipped


def per_run(rows, key):
    """{question: [the run's mean of key]}: each run weighs the same, however many onsets it has."""
    runs = {}
    for o in rows:
        runs.setdefault((o["item_id"], o["source_run_id"]), []).append(float(o[key]))
    out = {}
    for (q, _), vals in runs.items():
        out.setdefault(q, []).append(sum(vals) / len(vals))
    return out


def onset_comparison(rows, sure, label):
    os_, skipped = onset_rows(rows)
    if sure is not None:
        os_ = [o for o in os_ if sure.get(o["item_id"])]
    groups = [("permanent (the takeover)", [o for o in os_ if o["permanent"]]),
              ("temporary", [o for o in os_ if not o["permanent"]]),
              ("temporary, in followed runs", [o for o in os_ if not o["permanent"] and o["kind"] == "followed"]),
              ("temporary, in resisted runs", [o for o in os_ if not o["permanent"] and o["kind"] == "resisted"])]
    print(f"| {label}: onset | onsets | runs | questions | own answer leads just before | own answer's probability "
          f"just before (mean) | the same, each run weighted once |")
    print("|---|---|---|---|---|---|---|")
    for name, g in groups:
        print(f"| {name} | {len(g)} | {len({o['source_run_id'] for o in g})} | {len({o['item_id'] for o in g})} | "
              f"{sum(o['own_leads_before'] for o in g)} of {len(g)}: {ci(by_q(g, 'own_leads_before'))} | "
              f"{ci(by_q(g, 'own_prob_before'), pct=False)} | leads {ci(per_run(g, 'own_leads_before'))}, "
              f"probability {ci(per_run(g, 'own_prob_before'), pct=False)} |")
    perm, temp = groups[0][1], groups[1][1]
    print(f"| permanent minus temporary | | | | {diff(by_q(perm, 'own_leads_before'), by_q(temp, 'own_leads_before'))} | "
          f"{diff(by_q(perm, 'own_prob_before'), by_q(temp, 'own_prob_before'))} | leads "
          f"{diff(per_run(perm, 'own_leads_before'), per_run(temp, 'own_leads_before'))} |")
    per = Counter(o["source_run_id"] for o in temp)
    print(f"Temporary onsets per run: median {sorted(per.values())[len(per) // 2] if per else 0}, max "
          f"{max(per.values(), default=0)} ({len(per)} runs). Left out: {dict(skipped) or 'none'}.\n")
    return {"permanent": len(perm), "temporary": len(temp),
            "leads_diff": boot_diff(by_q(perm, "own_leads_before"), by_q(temp, "own_leads_before"))
            if set(by_q(perm, "own_leads_before")) & set(by_q(temp, "own_leads_before")) else None}


def points(rows, texts):
    """[(kind of point, run, k)] for late takeovers and closest approaches."""
    out = []
    for r in rows:
        if r["kind"] == "followed" and tk.takeover_type(r) == "late":
            out.append(("late takeover", r, r["takeover_k"]))
        elif r["kind"] == "resisted":
            ca = tk.closest_approach(r)
            if ca:
                out.append(("closest approach", r, ca[0]))
    return [(name, r, k) for name, r, k in out if r["source_run_id"] in texts]


def measure(name, r, k, text):
    sents = sentences(text, r["sentence_ends"])
    win = window(sents, k)
    hits = [(i, s, [f for f, rx in FAMILY_RX.items() if rx.search(s)]) for i, s in win if MISFIT.search(s)]
    ob = own_before(r, k)
    n = r["n_sentences"]
    base = [any(MISFIT.search(s) for _, s in window(sents, j)) for j in range(1, n + 1)]
    return {"point": name, "item_id": r["item_id"], "condition": r["condition"], "arm": r.get("arm"),
            "repeat": r["repeat"], "source_run_id": r["source_run_id"], "k": k, "share": k / n if n else None,
            "own_letter": r.get("own_letter"), "own_prob_before": None if ob is None else ob[0],
            "own_leads_before": None if ob is None else ob[1], "misfit": bool(hits), "misfit_hits": hits,
            "misfit_any_window": sum(base) / len(base) if base else None}


def by_q(ms, key, cast=float):
    out = {}
    for m in ms:
        if m[key] is not None:
            out.setdefault(m["item_id"], []).append(cast(m[key]))
    return out


def ci(groups, pct=True):
    if not groups:
        return "—"
    m, lo, hi = boot_mean(groups)
    f = (lambda x: f"{100 * x:.0f}%") if pct else (lambda x: f"{x:.2f}")
    return f"{f(m)} [{f(lo)}, {f(hi)}]"


def diff(a, b):
    shared = set(a) & set(b)
    if not shared:
        return "— (no shared questions)"
    d, lo, hi = boot_diff(a, b)
    return f"{100 * d:+.0f} points [{100 * lo:+.0f}, {100 * hi:+.0f}] ({len(shared)} shared questions)"


def concentration(rows, steps, sure):
    print(f"1. Concentration: followed runs on the {sum(sure.values())} sure questions")
    hinted = [r for r in steps if r["condition"] != "none" and sure.get(r["item_id"])]
    fol = [r for r in rows if r["kind"] == "followed" and sure.get(r["item_id"])]
    late = Counter(r["item_id"] for r in fol if tk.takeover_type(r) == "late")
    per_q = Counter(r["item_id"] for r in fol)
    runs_q = Counter(r["item_id"] for r in hinted)
    order = sorted((q for q in sure if sure[q]), key=lambda q: (-per_q[q], q))
    print("| question | category | hinted runs | followed | late takeovers |")
    print("|---|---|---|---|---|")
    cat = {r["item_id"]: r.get("category") for r in steps}
    for q in order:
        print(f"| {q} | {cat.get(q)} | {runs_q[q]} | {per_q[q]} | {late[q]} |")
    top3 = sum(per_q[q] for q in order[:3])
    print(f"{len(fol)} followed runs come from {len(per_q)} of the {len(order)} sure questions; the top 3 questions "
          f"give {top3} of {len(fol)}; {sum(1 for q in order if not per_q[q])} sure questions have none.\n")
    return {"followed": len(fol), "questions_with_followed": len(per_q), "sure_questions": len(order),
            "per_question": {str(q): per_q[q] for q in order}, "top3": top3}


def describe_late(ms, label):
    late = [m for m in ms if m["point"] == "late takeover" and m["own_leads_before"] is not None]
    print(f"Description ({label}): just before a late takeover the model's own no-hint answer leads in "
          f"{sum(m['own_leads_before'] for m in late)} of {len(late)} runs with an own answer "
          f"({ci(by_q(late, 'own_leads_before'))}); its mean probability there is "
          f"{ci(by_q(late, 'own_prob_before'), pct=False)}.")


def compare(ms, label):
    late = [m for m in ms if m["point"] == "late takeover"]
    close = [m for m in ms if m["point"] == "closest approach"]
    print(f"| {label} | late takeovers | closest approaches | difference (late - closest) |")
    print("|---|---|---|---|")
    print(f"| points | {len(late)} ({len({m['item_id'] for m in late})} questions) | {len(close)} "
          f"({len({m['item_id'] for m in close})} questions) | |")
    print(f"| (b) a \"doesn't fit the options\" sentence in the point's window | "
          f"{sum(m['misfit'] for m in late)} of {len(late)}: {ci(by_q(late, 'misfit'))} | "
          f"{sum(m['misfit'] for m in close)} of {len(close)}: {ci(by_q(close, 'misfit'))} | "
          f"{diff(by_q(late, 'misfit'), by_q(close, 'misfit'))} |")
    print(f"| (b) baseline: any 4-sentence window in the same runs | {ci(by_q(late, 'misfit_any_window'))} | "
          f"{ci(by_q(close, 'misfit_any_window'))} | |")
    print()
    d, lo, hi = boot_diff(by_q(late, "misfit"), by_q(close, "misfit")) if set(by_q(late, "misfit")) & set(
        by_q(close, "misfit")) else (None, None, None)
    return {"late": len(late), "closest": len(close), "misfit_diff": d, "misfit_diff_ci": [lo, hi]}


def examples(ms, n=5):
    """One example sentence per keyword family (seeded), then more from any family up to n."""
    rng = random.Random(SEED)
    pool = [(m, i, s, fams) for m in ms for i, s, fams in m["misfit_hits"]]
    picked, used = [], set()
    for fam in MISFIT_FAMILIES:
        cands = [x for x in pool if fam in x[3] and id(x) not in used]
        if cands:
            x = rng.choice(cands)
            picked.append((fam, x))
            used.add(id(x))
    rest = [x for x in pool if id(x) not in used]
    rng.shuffle(rest)
    picked += [(x[3][0], x) for x in rest[: max(0, n - len(picked))]]
    return picked[:n]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    runs, own = tk.runs_to_probe()
    rows = tk.current_probes(load(tk.PROBES_OUT), {tk.source_key(r) for r in runs}, own)
    steps = bf.current(load(bf.OUT))
    sure = tk.sure_questions(steps)
    texts = {r["run_id"]: r["reasoning_text"] for r in runs}
    pts = points(rows, texts)
    print(f"reads {tk.PROBES_OUT.relative_to(CODE)} ({len(rows)} probed runs) and {bf.OUT.relative_to(CODE)}; "
          f"{Counter(p[0] for p in pts)}; no calls")
    if a.dry_run:
        return
    print()
    conc = concentration(rows, steps, sure)
    ms = [measure(name, r, k, texts[r["source_run_id"]]) for name, r, k in pts]
    print("2(a). Matched comparison: just before the hint letter takes the lead after the first fifth, does the "
          "model's own no-hint answer lead? Permanent onsets (the takeover) against temporary ones (the lead is lost "
          "again). 95% bootstrap intervals clustered by question.\n")
    onset_all = onset_comparison(rows, None, "all hinted runs")
    onset_sure = onset_comparison(rows, sure, "sure questions only")
    describe_late(ms, "all hinted runs")
    describe_late([m for m in ms if sure.get(m["item_id"])], "sure questions only")
    print("\n2(b). Late takeovers against resisted runs' closest approaches: the point (sentence k) and the "
          f"{BEFORE} sentences before it. Keyword counts; 95% bootstrap intervals clustered by question.\n")
    all_hinted = compare(ms, "all hinted runs")
    on_sure = compare([m for m in ms if sure.get(m["item_id"])], "sure questions only")
    fams = Counter(f for m in ms for _, _, fs in m["misfit_hits"] for f in fs)
    print("Keyword families matched (sentences in the windows): "
          + "; ".join(f"{f}: {fams[f]}" for f in MISFIT_FAMILIES))
    print("\nExample sentences (one per family where possible), to check the list:")
    for fam, (m, i, s, fs) in examples(ms):
        hit = FAMILY_RX[fam].search(s).group(0)
        print(f"- [{fam}; matched \"{hit}\"] Q{m['item_id']} {m['condition']}{' (declared)' if m['arm'] else ''} "
              f"run {m['repeat']}, {m['point']}, sentence {i} of the window ending at {m['k']}: "
              f"\"{' '.join(s.split())[:300]}\"")
    append(OUT, {"timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "concentration": conc, "all_hinted": all_hinted, "sure_only": on_sure,
                 "onsets_all": onset_all, "onsets_sure": onset_sure,
                 "keyword_families": MISFIT_FAMILIES, "family_counts": dict(fams),
                 "points": [{k: v for k, v in m.items() if k != "misfit_hits"} | {
                     "misfit_sentences": [i for i, _, _ in m["misfit_hits"]]} for m in ms]})


if __name__ == "__main__":
    main()
