"""Track A, exploratory (post hoc), Nov 7: the trade-off between resisting wrong hints and taking right ones on E2,
exactly as archive/sessions/2026-11-07/2026-11-07_2020_A_tradeoff-exploratory.md (its section 3) says. That log was
written and committed (3c3aa62) before any of this was computed. It is not pre-registered: nothing here replaces or
qualifies a pre-registered verdict, and every output says "exploratory (post hoc)".

  python tools/tradeoff.py [--out OUT] [--qset e2]        # -> OUT/tradeoff_<qset>.json (numbers only) and a summary
  python tools/tradeoff.py --figures [--fig-out DIR]      # the same, then tradeoff_e2 and tradeoff_acc_p (.png .svg .csv)
  python tools/tradeoff.py --figures-only [--json PATH]   # the figures from a saved tradeoff_<qset>.json

Data: A39's lean design on E2 (OUT = results/trackA/gpu/a39, numbers only), nine systems: base, prompt_only, lora,
lora_note, wrap, wrap_note, lora_wrap (A39), a40 (A40) and a40_note (A42). Each run once, its last ok record; a wrapper
system also gets its partner's runs without a tool message, marked shared_from (finetune/a39.by_system; a40 and
a40_note by the same rule, as finetune/a40.py and a42.py load them). Answered runs only (a parsed letter,
eval.answered), unless said otherwise.

  3.1  each system's following (answered wrong-hint runs ending on the hint's letter: pooled over the three channels,
       and per channel) and correct-hint acceptance (the correct letter among answered correct-hint runs: pooled over
       pasted and inserted, and per channel), X of Y with 95% Wilson (common.wilson); the figure tradeoff_e2: (a)
       pooled, the wrapper systems hollow and marked diluted by design, (b) the inserted tool turn.
  3.2  on the two tool channels (pasted, inserted): a_C, the correct answers among answered correct-hint runs; a_W, the
       correct answers (the right letter, not merely not the hint's) among answered wrong-hint runs; Acc(p) =
       p a_C + (1 - p) a_W. Each system against prompt_only (A40 first, then LoRA, then the others): dW = a_W(A) -
       a_W(B), dC = a_C(A) - a_C(B), the crossing p* = dW / (dW - dC), inside (0, 1) only when dW and dC have opposite
       signs (else "ahead at every p" or "behind at every p"); Acc_A(p) - Acc_B(p) at p = 0, 0.25, 0.5, 0.75, 0.9 and
       1. Beside it, the same with a run that gave no answer counted as a wrong answer. The figure tradeoff_acc_p.
  3.3  disclosure when following: among answered wrong-hint runs ending on the hint's letter, the share whose final
       answer names the hint (mention_final_broad, hiding's keyword); pooled and per channel; each system minus
       prompt_only (LoRA and A40 first), pooled.

The bootstrap: questions resampled with replacement, the same questions for both systems (paired: the questions both
have), 20,000 resamples, seed 0 (numpy's default_rng(0); each resample a row of draw counts per question), every rate a
ratio of sums over the resampled questions' runs; the 95% interval by common.boot_diff's percentile rule (the sorted
values' int(0.025 n)-th and (int(0.975 n) - 1)-th). p* per resample by the same formula, clipped to [0, 1]; a resample
whose dW - dC has the other sign from the full data's (the order flips), or is 0, is counted and left out of p*'s
interval. A disclosure resample in which either side has no followed run is counted and left out. Under 5 questions
behind a comparison: "too few questions" (common.MIN_QUESTIONS).
"""
import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))
sys.path.insert(0, str(CODE / "tools"))

from common import MIN_QUESTIONS, latest, wilson  # noqa: E402
from finetune import a39, a40, a42  # noqa: E402
from finetune import eval as ev  # noqa: E402

LABEL = "exploratory (post hoc)"
LOG = "archive/sessions/2026-11-07/2026-11-07_2020_A_tradeoff-exploratory.md"
OUT = CODE / "results" / "trackA" / "gpu" / "a39"
SYSTEMS = ("base", "prompt_only", "lora", "lora_note", "wrap", "wrap_note", "lora_wrap", "a40", "a40_note")
REF = "prompt_only"
CROSSING_ORDER = ("a40", "lora", "base", "lora_note", "wrap", "wrap_note", "lora_wrap", "a40_note")    # 3.2
DISCLOSURE_ORDER = ("lora", "a40", "base", "lora_note", "wrap", "wrap_note", "lora_wrap", "a40_note")  # 3.3
ACC_P_SYSTEMS = ("base", "prompt_only", "lora", "a40")
MARKED = ("a40", "lora")                    # the crossings tradeoff_acc_p marks (against prompt_only)
TOOL = ("tool_pasted", "tool_injected")
PS = (0, 0.25, 0.5, 0.75, 0.9, 1)
N_BOOT, SEED, EPS = 20000, 0, 1e-12
CROSSES, AHEAD, BEHIND, EQUAL = "crosses in (0, 1)", "ahead at every p", "behind at every p", "equal at every p"
FEW, MISSING = a39.FEW, "missing runs"
DILUTED = ("diluted by design: its runs without a tool message (user, pasted, no hint) are {partner}'s (shared); the "
           "wrapper acts on the inserted tool turn only (the A39 log's section 9.2)")
BOOTSTRAP = ["questions resampled with replacement, paired (the questions both systems have), 20,000 resamples, seed 0 "
             "(numpy default_rng)",                                     # a list: the export allows 200 characters a string
             "rates as ratios of sums over the resampled questions' runs; 95% percentile interval by common.boot_diff's "
             "rule",
             "p* clipped to [0, 1]; a resample whose dW - dC flips sign (or is 0) counted and left out",
             "a disclosure resample with no followed run on either side counted and left out"]


# ---------------------------------------------------------------- the runs
def load(out=OUT, qset="e2"):
    """({system: its finished runs}, completeness) for the nine systems, by one rule: each run once, its last ok record
    (a39.by_system for A39's seven, the wrappers with their partner's shared runs; a40 and a40_note from the same
    records, as a40.systems and a42.systems take them)."""
    rows = a39.of_set(a39.read(out)[0], qset)
    by = a39.by_system(rows)
    ok = latest([r for r in rows if r.get("status") == "ok"])
    for s in ("a40", "a40_note"):
        by[s] = [r for r in ok if r.get("system") == s]
    comp = {**a39.completeness(rows, qset), "a40": a40.completeness(rows, qset)["a40"],
            "a40_note": a42.completeness(rows, qset)["a40_note"]}
    return {s: by[s] for s in SYSTEMS if by.get(s)}, comp


def correct(r):
    return r["parsed_letter"] == r["correct_letter"]


def named(r):
    return bool(r.get("mention_final_broad"))


def xofy(rows, outcome):
    """{k, n, rate, wilson}: k of n with a 95% Wilson interval (rate and interval None when n is 0)."""
    k, n = sum(bool(outcome(r)) for r in rows), len(rows)
    return {"k": k, "n": n, "rate": k / n if n else None, "wilson": wilson(k, n)}


def tool_runs(rs, hint_correct, answered_only=True):
    """The tool channels' runs with a correct (True) or wrong (False) hint; answered ones unless answered_only is False
    (the sensitivity: a run with no answer then counts as a wrong answer)."""
    keep = [r for r in rs if r["hint_correct"] is hint_correct and r["channel"] in TOOL]
    return ev.answered(keep) if answered_only else keep


def followed_runs(rs, channel=None):
    """Answered wrong-hint runs ending on the hint's letter (a39.MEASURES' following), on one channel or pooled."""
    ans, _ = a39.pick(rs, "following", channel)
    return [r for r in ans if ev.followed(r)]


def rates(rs):
    """One system's rates: following (pooled, user, pasted, inserted), acceptance (pooled, pasted, inserted), a_C and
    a_W on the tool channels (answered; and with no answer as wrong), disclosure when following (pooled and per
    channel), and the tool channels' no-answer counts."""
    out = {"runs": len(rs), "shared": sum("shared_from" in r for r in rs)}
    out["following"] = {ch or "pooled": xofy(*a39.pick(rs, "following", ch)) for ch in (None, *a39.CHANNELS)}
    out["acceptance"] = {ch or "pooled": xofy(*a39.pick(rs, "acceptance", ch)) for ch in (None, "pasted", "inserted")}
    out["tool"] = {"a_C": xofy(tool_runs(rs, True), correct), "a_W": xofy(tool_runs(rs, False), correct)}
    out["tool_no_answer_as_wrong"] = {"a_C": xofy(tool_runs(rs, True, False), correct),
                                      "a_W": xofy(tool_runs(rs, False, False), correct)}
    out["tool_no_answer"] = {"correct_hint": xofy(tool_runs(rs, True, False), lambda r: not r["parsed_letter"]),
                             "wrong_hint": xofy(tool_runs(rs, False, False), lambda r: not r["parsed_letter"])}
    out["disclosure_when_following"] = {ch or "pooled": xofy(followed_runs(rs, ch), named) for ch in (None, *a39.CHANNELS)}
    return out


# ---------------------------------------------------------------- the bootstrap
_COUNTS = {}


def resample_counts(nq, n=N_BOOT, seed=SEED):
    """(n x nq) draw counts: row b says how often each question is drawn in resample b (nq questions with replacement,
    numpy default_rng(seed)). The same matrix for every comparison over nq questions, so both sides are paired."""
    key = (nq, n, seed)
    if key not in _COUNTS:
        idx = np.random.default_rng(seed).integers(0, nq, size=(n, nq))
        flat = (np.arange(n)[:, None] * nq + idx).ravel()
        c = np.bincount(flat, minlength=n * nq).reshape(n, nq)
        c.setflags(write=False)
        _COUNTS[key] = c
    return _COUNTS[key]


def pct(vals):
    """The 95% percentile interval by common.boot_diff's rule: sorted[int(0.025 n)], sorted[int(0.975 n) - 1]."""
    v = np.sort(np.asarray(vals, dtype=float))
    if not len(v):
        return None
    return [float(v[int(0.025 * len(v))]) + 0.0, float(v[int(0.975 * len(v)) - 1]) + 0.0]       # + 0.0: no -0.0


def paired_questions(a, b):
    return sorted({r["item_id"] for r in a} & {r["item_id"] for r in b}, key=str)


def sums(rows, outcome, qs):
    """(numerator, denominator) per question, in qs's order: the runs, and those with the outcome."""
    pos = {q: i for i, q in enumerate(qs)}
    num, den = np.zeros(len(qs)), np.zeros(len(qs))
    for r in rows:
        i = pos.get(r["item_id"])
        if i is not None:
            den[i] += 1
            num[i] += bool(outcome(r))
    return num, den


def boot_rate(counts, num, den):
    """Each resample's ratio of sums (NaN where it has no run)."""
    d = counts @ den
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(d > 0, (counts @ num) / np.where(d > 0, d, 1), np.nan)


# ---------------------------------------------------------------- 3.2: Acc(p) and where two systems cross
def crossing_point(dw, dc):
    """Where Acc_A(p) - Acc_B(p) = dW + p (dC - dW) is 0: p* = dW / (dW - dC), inside (0, 1) only when dW and dC have
    opposite signs; ahead "below" means A gives more correct answers than B when fewer than p* of the tool's answers
    are correct (and fewer above it); "above", the reverse. With the same sign: ahead, behind or equal at every p."""
    if abs(dw) <= EPS and abs(dc) <= EPS:
        return {"p_star": None, "status": EQUAL, "ahead": None}
    if (dw > EPS and dc < -EPS) or (dw < -EPS and dc > EPS):
        return {"p_star": dw / (dw - dc), "status": CROSSES, "ahead": "below" if dw > 0 else "above"}
    return {"p_star": None, "status": AHEAD if dw >= -EPS and dc >= -EPS else BEHIND, "ahead": None}


def clip_crossings(dw, dc, sign):
    """The resamples' p* (arrays of dW and dC): a resample whose dW - dC is 0 (zero) or has the other sign from the full
    data's (flipped) is counted and left out; the rest's p* clipped to [0, 1] (values). clipped_to_0 and clipped_to_1:
    resamples whose p* was at or beyond that end before clipping (one system ahead throughout, or level at that end)."""
    dw, dc = np.asarray(dw, dtype=float), np.asarray(dc, dtype=float)
    den = dw - dc
    zero = np.abs(den) <= EPS
    keep = ~zero & (np.sign(den) == sign)
    raw = dw[keep] / den[keep]
    return {"values": np.clip(raw, 0, 1), "flipped": int((~zero & ~keep).sum()), "zero": int(zero.sum()),
            "clipped_to_0": int((raw <= 0).sum()), "clipped_to_1": int((raw >= 1).sum())}


def crossing(a, b, no_answer_as_wrong=False, n=N_BOOT, seed=SEED):
    """System a against system b on the tool channels: a_C and a_W each, dW and dC, the crossing p* (crossing_point)
    with its bootstrap interval (clip_crossings), and Acc_a(p) - Acc_b(p) at PS with theirs."""
    qs = paired_questions(a, b)
    answered_only = not no_answer_as_wrong

    def side(rs):
        return {"C": sums(tool_runs(rs, True, answered_only), correct, qs),
                "W": sums(tool_runs(rs, False, answered_only), correct, qs)}

    sa, sb = side(a), side(b)
    full = {k: {m: (s[m][0].sum() / s[m][1].sum() if s[m][1].sum() else None) for m in "CW"} for k, s in (("a", sa),
                                                                                                         ("b", sb))}
    e = {"questions": len(qs), "no_answer_as_wrong": no_answer_as_wrong,
         **{k: {"a_C": full[k]["C"], "a_W": full[k]["W"],
                "a_C_kn": [int(s["C"][0].sum()), int(s["C"][1].sum())],
                "a_W_kn": [int(s["W"][0].sum()), int(s["W"][1].sum())]} for k, s in (("a", sa), ("b", sb))}}
    if any(v is None for k in full for v in full[k].values()):
        return {**e, "status": MISSING, "p_star": None, "interval": None}
    dw, dc = full["a"]["W"] - full["b"]["W"], full["a"]["C"] - full["b"]["C"]
    e.update({"dW": float(dw), "dC": float(dc), **crossing_point(dw, dc)})
    e["p_star_clipped"] = float(np.clip(dw / (dw - dc), 0, 1)) if abs(dw - dc) > EPS else None
    point = {str(p): float(dw + p * (dc - dw)) for p in PS}
    if len(qs) < MIN_QUESTIONS:
        e.update({"interval": FEW, "pointwise": {p: {"diff": v, "interval": FEW} for p, v in point.items()}})
        return e
    counts = resample_counts(len(qs), n, seed)
    bw = boot_rate(counts, *sa["W"]) - boot_rate(counts, *sb["W"])
    bc = boot_rate(counts, *sa["C"]) - boot_rate(counts, *sb["C"])
    empty = np.isnan(bw) | np.isnan(bc)
    bw, bc = bw[~empty], bc[~empty]
    e["empty"] = int(empty.sum())                      # resamples where a side had no run (none on E2)
    if abs(dw - dc) > EPS:
        cl = clip_crossings(bw, bc, np.sign(dw - dc))
        e.update({"interval": pct(cl["values"]), "resamples": len(cl["values"]),
                  **{k: cl[k] for k in ("flipped", "zero", "clipped_to_0", "clipped_to_1")}})
    else:
        e.update({"interval": None, "resamples": 0, "flipped": None, "zero": None})
    e["pointwise"] = {p: {"diff": v, "interval": pct(bw + float(p) * (bc - bw))} for p, v in point.items()}
    return e


# ---------------------------------------------------------------- 3.3: disclosure when following, against prompt_only
def disclosure_diff(a, b, n=N_BOOT, seed=SEED):
    """a's share minus b's of followed runs whose final answer names the hint, pooled, paired by question; a resample
    in which either side has no followed run is counted (dropped) and left out."""
    qs = paired_questions(a, b)
    fa, fb = followed_runs(a), followed_runs(b)
    (na, da), (nb, db) = sums(fa, named, qs), sums(fb, named, qs)
    e = {"questions": len(qs), "a": xofy(fa, named), "b": xofy(fb, named)}
    if not (da.sum() and db.sum()):
        return {**e, "diff": None, "interval": MISSING, "dropped": None, "resamples": 0}
    e["diff"] = float(na.sum() / da.sum() - nb.sum() / db.sum())
    if len(qs) < MIN_QUESTIONS:
        return {**e, "interval": FEW, "dropped": None, "resamples": 0}
    counts = resample_counts(len(qs), n, seed)
    ra, rb = boot_rate(counts, na, da), boot_rate(counts, nb, db)
    ok = ~(np.isnan(ra) | np.isnan(rb))
    return {**e, "interval": pct((ra - rb)[ok]), "dropped": int((~ok).sum()), "resamples": int(ok.sum())}


# ---------------------------------------------------------------- the whole analysis
def analyse(by, qset="e2", completeness=None, n=N_BOOT, seed=SEED):
    res = {"label": LABEL, "log": LOG, "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "qset": qset, "questions": len({r["item_id"] for rs in by.values() for r in rs}),
           "measures": "A39's (a39.MEASURES, eval.followed), on answered runs; a_C and a_W on the tool channels only",
           "bootstrap": BOOTSTRAP, "ps": list(PS), "reference": REF}
    if completeness is not None:
        res["complete"] = all(e["missing"] == 0 for e in completeness.values())
        res["completeness"] = completeness
    res["systems"] = {}
    for s in SYSTEMS:
        if s in by:
            res["systems"][s] = rates(by[s])
            if s in ev.SHARED:
                res["systems"][s]["note"] = DILUTED.format(partner=ev.SHARED[s])
    diluted = lambda s: {"note": "diluted by design"} if s in ev.SHARED else {}  # noqa: E731
    have = [s for s in CROSSING_ORDER if s in by] if REF in by else []
    res["crossings"] = {"answered": {s: {**crossing(by[s], by[REF], n=n, seed=seed), **diluted(s)} for s in have},
                        "no_answer_as_wrong": {s: {**crossing(by[s], by[REF], True, n=n, seed=seed), **diluted(s)}
                                               for s in have}}
    res["disclosure_vs_prompt_only"] = {s: {**disclosure_diff(by[s], by[REF], n=n, seed=seed), **diluted(s)}
                                        for s in DISCLOSURE_ORDER if s in by and REF in by}
    return res


def report(out=OUT, qset="e2"):
    by, comp = load(out, qset)
    res = analyse(by, qset, comp)
    Path(out, f"tradeoff_{qset}.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


# ---------------------------------------------------------------- the summary
def pc(x, nd=1):
    return "-" if x is None else f"{100 * x:.{nd}f}"


def kn(e):
    """X of Y [Wilson, in percent]."""
    if not e or not e["n"]:
        return "0 of 0"
    lo, hi = e["wilson"]
    return f"{e['k']} of {e['n']} ({pc(e['rate'])}% [{pc(lo)}, {pc(hi)}])"


def pts(v, iv):
    """A difference in points with its interval."""
    if v is None:
        return "-"
    tail = f" [{100 * iv[0]:+.1f}, {100 * iv[1]:+.1f}]" if isinstance(iv, list) else f" ({iv})" if iv else ""
    return f"{100 * v:+.1f}{tail}"


def crossing_line(s, e):
    if e.get("status") == MISSING:
        return f"  {s:<10} missing runs"
    head = (f"  {s:<10} a_W {pc(e['a']['a_W'])} vs {pc(e['b']['a_W'])}, a_C {pc(e['a']['a_C'])} vs {pc(e['b']['a_C'])}"
            f"; dW {pts(e['dW'], None)}, dC {pts(e['dC'], None)} -> ")
    iv = e.get("interval")
    ivs = f"[{iv[0]:.3f}, {iv[1]:.3f}]" if isinstance(iv, list) else str(iv)
    if e["status"] == CROSSES:
        head += (f"p* {e['p_star']:.3f} {ivs} ({s} ahead {e['ahead']} p*); flipped {e['flipped']:,}, zero {e['zero']}, "
                 f"kept {e['resamples']:,}")
    else:
        head += f"{e['status']} (clipped p* {ivs}; flipped {e.get('flipped')}, kept {e.get('resamples')})"
    return head


def text(res):
    lines = [f"The trade-off on {res['qset']} ({res['questions']} questions), {LABEL}; the log: {res['log']}"]
    if "complete" in res:
        miss = {s: e["missing"] for s, e in res["completeness"].items() if e["missing"]}
        lines.append("complete: every system's own runs are in" if res["complete"] else f"INCOMPLETE: missing {miss}")
    lines.append("system: following pooled | acceptance pooled | inserted: following, acceptance | tool: a_C, a_W | "
                 "disclosure when following (pooled; user, pasted, inserted)")
    for s, e in res["systems"].items():
        d = e["disclosure_when_following"]
        lines.append(f"  {s:<10} {kn(e['following']['pooled'])} | {kn(e['acceptance']['pooled'])} | "
                     f"{kn(e['following']['inserted'])}, {kn(e['acceptance']['inserted'])} | "
                     f"{kn(e['tool']['a_C'])}, {kn(e['tool']['a_W'])} | {kn(d['pooled'])}; "
                     + ", ".join(f"{d[c]['k']}/{d[c]['n']}" for c in a39.CHANNELS) + (" (diluted)" if "note" in e else ""))
    for block, title in (("answered", "Crossings with prompt_only (answered runs)"),
                         ("no_answer_as_wrong", "Sensitivity: no answer counted as wrong")):
        lines.append(f"{title}:")
        for s, e in res["crossings"][block].items():
            lines.append(crossing_line(s, e))
            if block == "answered" and "pointwise" in e:
                lines.append(f"  {'':<10} Acc diff (points): " + "; ".join(
                    f"p={p} {pts(x['diff'], x['interval'])}" for p, x in e["pointwise"].items()))
    lines.append("Disclosure when following, minus prompt_only (pooled; points):")
    for s, e in res["disclosure_vs_prompt_only"].items():
        lines.append(f"  {s:<10} {pts(e['diff'], e['interval'])}; {e['a']['k']} of {e['a']['n']} vs {e['b']['k']} of "
                     f"{e['b']['n']}; dropped {e['dropped']}")
    return "\n".join(lines)


# ---------------------------------------------------------------- the figures (tools/slide_figures.py's style)
NAMES = {"base": "base", "prompt_only": "the instruction", "lora": "LoRA", "lora_note": "LoRA + note",
         "wrap": "wrapper", "wrap_note": "wrapper + note", "lora_wrap": "LoRA + wrapper", "a40": "A40",
         "a40_note": "A40 + note"}
FAMILY = {"base": "baseline", "prompt_only": "final", "lora": "private", "lora_note": "private", "a40": "correct",
          "a40_note": "correct", "wrap": "cue", "wrap_note": "cue", "lora_wrap": "cue"}          # ROLE keys
SHAPE = {"base": "o", "prompt_only": "o", "lora": "o", "lora_note": "D", "a40": "o", "a40_note": "D", "wrap": "o",
         "wrap_note": "D", "lora_wrap": "s"}
CSV_NOTE = (f"{LABEL}: tools/tradeoff.py, from results/trackA/gpu/a39/tradeoff_e2.json (numbers only); the log {LOG}, "
            "written before computing; not pre-registered and replaces no verdict")
FOOT = (f"Exploratory (post hoc), not pre-registered, replacing no verdict: the analysis is the log {LOG}, written and "
        "committed before computing. E2: 120 questions in A39's lean design, each run once (its last ok record), "
        "answered runs only. ")


def save(fig, name, rows, out):
    """slide_figures.save with the CSV's first line a comment saying exploratory (post hoc)."""
    from slide_figures import DPI
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(out / f"{name}.{ext}", dpi=DPI)
    with open(out / f"{name}.csv", "w", newline="") as f:
        f.write(f"# {CSV_NOTE}\n")
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return [out / f"{name}.{ext}" for ext in ("png", "svg", "csv")]


def color(s):
    from slide_figures import ROLE
    return ROLE[FAMILY[s]]


def tradeoff_rows(res):
    """Every plotted number of tradeoff_e2: per panel (a pooled, b inserted) and system, following and acceptance,
    X of Y with Wilson."""
    out = []
    for panel, ch in (("a", "pooled"), ("b", "inserted")):
        for s, e in res["systems"].items():
            f, a = e["following"][ch], e["acceptance"][ch]
            out.append({"panel": panel, "channels": "wrong: user, pasted, inserted; correct: pasted, inserted"
                        if ch == "pooled" else "inserted", "system": s, "name": NAMES[s], "family": FAMILY[s],
                        "hollow": s in ev.SHARED, "following_k": f["k"], "following_n": f["n"],
                        "following": f["rate"], "following_low": f["wilson"][0], "following_high": f["wilson"][1],
                        "acceptance_k": a["k"], "acceptance_n": a["n"], "acceptance": a["rate"],
                        "acceptance_low": a["wilson"][0], "acceptance_high": a["wilson"][1],
                        "shared_runs": e["shared"], "interval": "95% Wilson",
                        "note": "diluted by design" if s in ev.SHARED and panel == "a" else ""})
    return out


RING = [(r * np.cos(np.radians(a)), r * np.sin(np.radians(a))) for r in (9, 17, 27, 40, 54)
        for a in (30, -30, 150, -150, 90, -90, 0, 180, 60, -60, 120, -120)]       # label offsets (points), near first


def place_labels(fig, ax, pts_, size, bars=()):
    """Direct labels beside their points [(x, y, text)]: each takes the offset on RING that collides least (in order of
    weight: outside the axes, a label already placed, a point, another system's bar, its own bar; then the nearer
    offset). bars: [(owner index, (x0, y0), (x1, y1))], each interval as an axis-aligned segment in data units. The
    most crowded points are labelled first; a label set off far gets a thin leader to its point."""
    from matplotlib import patheffects
    from matplotlib.transforms import Bbox
    from slide_figures import WHITE
    from paper_figures import INK, MUTED
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    box = ax.get_window_extent(rend)
    px = ax.transData.transform
    dots = [px((x, y)) for x, y, _ in pts_]
    segs = [(i, Bbox([px(a), px(b)]).padded(1.5)) for i, a, b in bars]
    halo = [patheffects.withStroke(linewidth=3, foreground=WHITE)]

    def text(i, dx, dy, leader=False):
        x, y, label = pts_[i]
        ha = "left" if dx > 2 else "right" if dx < -2 else "center"
        va = "bottom" if dy > 2 else "top" if dy < -2 else "center"
        kw = {"arrowprops": {"arrowstyle": "-", "color": MUTED, "linewidth": 0.7, "shrinkA": 1, "shrinkB": 6}} if leader \
            else {}
        return ax.annotate(label, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va, fontsize=size,
                           color=INK, zorder=6, path_effects=halo, **kw)

    crowd = [sum(np.hypot(*(d - e)) < 90 for e in dots) for d in dots]
    taken = []
    for i in sorted(range(len(pts_)), key=lambda i: -crowd[i]):
        best = None
        for rank, (dx, dy) in enumerate(RING):
            t = text(i, dx, dy)
            bb = t.get_window_extent(rend).expanded(1.03, 1.12)
            t.remove()
            outside = not (box.x0 <= bb.x0 and bb.x1 <= box.x1 and box.y0 <= bb.y0 and bb.y1 <= box.y1)
            labels = sum(bb.overlaps(o) for o in taken)
            points = sum(bb.x0 - 5 <= a <= bb.x1 + 5 and bb.y0 - 5 <= b <= bb.y1 + 5 for a, b in dots)
            other = sum(bb.overlaps(g) for j, g in segs if j != i)
            own = sum(bb.overlaps(g) for j, g in segs if j == i)
            score = 1000 * outside + 200 * labels + 60 * points + 20 * other + 6 * own + 0.4 * rank
            if best is None or score < best[0]:
                best = (score, dx, dy, bb)
        _, dx, dy, bb = best
        text(i, dx, dy, leader=np.hypot(dx, dy) > 20)
        taken.append(bb)


def fig_tradeoff(res, out):
    """tradeoff_e2: each system a point, x = correct-hint acceptance, y = following, both with Wilson bars; (a) pooled,
    (b) the inserted tool turn; the wrapper systems hollow, in (a) marked diluted by design."""
    from slide_figures import LABEL_SIZE, LEFT, RIGHT, WHITE, frame, headline, key, note, title
    from paper_figures import MUTED
    from matplotlib.lines import Line2D
    plt, fig = frame()
    rows = tradeoff_rows(res)
    gs = fig.add_gridspec(1, 2, left=LEFT + 0.005, right=RIGHT, top=0.76, bottom=0.215, wspace=0.13)
    axes = {"a": fig.add_subplot(gs[0]), "b": fig.add_subplot(gs[1])}
    xs = [v for r in rows for v in (r["acceptance_low"], r["acceptance_high"])]
    ys = [v for r in rows for v in (r["following_low"], r["following_high"])]
    xlim = (max(0, np.floor(min(xs) * 20) / 20 - 0.03) * 100, 101.5)          # room for a label right of 90-odd
    ylim = (max(0, np.floor(min(ys) * 20) / 20 - 0.03) * 100, min(1, np.ceil(max(ys) * 20) / 20 + 0.03) * 100)
    for panel, ax in axes.items():
        pts_, bars = [], []
        for r in (r for r in rows if r["panel"] == panel):
            s, c = r["system"], color(r["system"])
            x, y = r["acceptance"] * 100, r["following"] * 100
            ax.plot([r["acceptance_low"] * 100, r["acceptance_high"] * 100], [y, y], color=c, linewidth=1.6,
                    solid_capstyle="butt", zorder=2, alpha=0.9)
            ax.plot([x, x], [r["following_low"] * 100, r["following_high"] * 100], color=c, linewidth=1.6,
                    solid_capstyle="butt", zorder=2, alpha=0.9)
            hollow = r["hollow"]
            ax.plot(x, y, marker=SHAPE[s], markersize=10 if SHAPE[s] == "o" else 9, linestyle="none", zorder=4,
                    markerfacecolor=WHITE if hollow else c, markeredgecolor=c if hollow else WHITE,
                    markeredgewidth=2.0 if hollow else 1.5)
            k = len(pts_)
            bars += [(k, (r["acceptance_low"] * 100, y), (r["acceptance_high"] * 100, y)),
                     (k, (x, r["following_low"] * 100), (x, r["following_high"] * 100))]
            pts_.append((x, y, NAMES[s]))
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.grid(axis="both")
        ax.set_xlabel("takes the correct hint: correct-hint acceptance (%)")
        if panel == "a":
            ax.set_ylabel("follows the wrong hint (%)")
        place_labels(fig, ax, pts_, LABEL_SIZE, bars)
    title(axes["a"], "(a) Pooled over the channels")
    title(axes["b"], "(b) The inserted tool turn only, where the wrapper acts")
    axes["a"].text(0.015, 0.975, "hollow: the wrapper systems, diluted by design here:\nmost of their pooled runs are "
                   "their partner's", transform=axes["a"].transAxes, fontsize=LABEL_SIZE - 0.5, color=MUTED,
                   va="top", ha="left", style="italic", zorder=7, linespacing=1.3,
                   bbox={"boxstyle": "square,pad=0.15", "facecolor": WHITE, "edgecolor": "none"})

    def mark(fam, shape="o", hollow=False):
        from slide_figures import ROLE
        c = ROLE[fam]
        return Line2D([], [], color=c, linewidth=1.6, marker=shape, markersize=9 if shape == "o" else 8,
                      markerfacecolor=WHITE if hollow else c, markeredgecolor=c if hollow else WHITE,
                      markeredgewidth=2.0 if hollow else 1.5)
    key(fig, [(mark("baseline"), "base"), (mark("final"), "the instruction"), (mark("private"), "LoRA family"),
              (mark("correct"), "A40 family"), (mark("cue", hollow=True), "wrapper family (hollow)"),
              (Line2D([], [], color=MUTED, marker="D", linestyle="none", markersize=8), "+ note"),
              (Line2D([], [], color=MUTED, marker="s", linestyle="none", markersize=8), "LoRA + wrapper")], ncol=7)
    headline(fig, f"The trade-off on E2, {LABEL}: wrong hints followed against correct hints taken, nine systems.",
             "Lower: fewer wrong hints followed. Further right: more correct hints taken. Each bar a 95% Wilson interval.")
    note(fig, FOOT + "Following: wrong-hint runs ending on the hint's letter, (a) over the user, pasted and inserted "
         "channels; acceptance: correct-hint runs ending on the correct letter, (a) over pasted and inserted (the lean "
         "design gives correct hints there only). Wrapper systems: their runs without a tool message are their "
         "partner's (shared). Color: the family; marker: the variant. Numbers: the CSV and tradeoff_e2.json.")
    paths = save(fig, "tradeoff_e2", rows, out)
    plt.close(fig)
    return paths


def acc_p_rows(res):
    """Every plotted number of tradeoff_acc_p: each line's ends (p = 0: a_W; p = 1: a_C, X of Y with Wilson) and each
    marked crossing (p*, its interval, Acc at p*, the flipped-order count)."""
    out = []
    blank = {k: "" for k in ("kind", "system", "name", "against", "measure", "p", "value", "low", "high", "interval",
                             "k", "n", "status", "flipped", "resamples")}
    for s in ACC_P_SYSTEMS:
        if s not in res["systems"]:
            continue
        t = res["systems"][s]["tool"]
        for p, m in ((0, "a_W"), (1, "a_C")):
            out.append({**blank, "kind": "line", "system": s, "name": NAMES[s], "p": p, "value": t[m]["rate"],
                        "low": t[m]["wilson"][0], "high": t[m]["wilson"][1], "k": t[m]["k"], "n": t[m]["n"],
                        "measure": f"{m} (Acc at p = {p})", "interval": "95% Wilson"})
    for s in MARKED:
        e = res["crossings"]["answered"].get(s)
        if not e:
            continue
        iv = e.get("interval") if isinstance(e.get("interval"), list) else ["", ""]
        at = (e["b"]["a_W"] + e["p_star"] * (e["b"]["a_C"] - e["b"]["a_W"])) if e["status"] == CROSSES else ""
        out.append({**blank, "kind": "crossing", "system": s, "name": NAMES[s], "against": REF,
                    "p": e["p_star"] if e["status"] == CROSSES else "", "value": at, "low": iv[0], "high": iv[1],
                    "status": e["status"], "flipped": e.get("flipped", ""), "resamples": e.get("resamples", ""),
                    "measure": "p* (value: Acc at p*)", "interval": "95% bootstrap over questions, paired, clipped"})
    return out


def fig_acc_p(res, out):
    """tradeoff_acc_p: Acc(p) for base, the instruction, LoRA and A40 on the tool channels, with where A40 and LoRA
    cross the instruction and those crossings' intervals (a strip under the lines); a pair with no crossing in (0, 1)
    says so."""
    from slide_figures import LABEL_SIZE, LEFT, RIGHT, WHITE, frame, headline, note, title, value
    from paper_figures import GRID, INK, MUTED
    plt, fig = frame()
    rows = acc_p_rows(res)
    gs = fig.add_gridspec(2, 1, height_ratios=[4.2, 1.25], left=LEFT + 0.005, right=RIGHT - 0.13, top=0.79,
                          bottom=0.215, hspace=0.12)
    ax, strip = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    ends = []
    for s in ACC_P_SYSTEMS:
        if s not in res["systems"]:
            continue
        t = res["systems"][s]["tool"]
        w, c = t["a_W"]["rate"] * 100, t["a_C"]["rate"] * 100
        ax.plot([0, 1], [w, c], color=color(s), linewidth=2.6, zorder=3, solid_capstyle="round")
        for p, v, m in ((0, w, "a_W"), (1, c, "a_C")):
            lo, hi = (x * 100 for x in t[m]["wilson"])
            ax.plot([p, p], [lo, hi], color=color(s), linewidth=1.4, alpha=0.55, zorder=2)
        ends.append((s, w, c))
    lo_y = min(min(w, c) for _, w, c in ends)
    hi_y = max(max(w, c) for _, w, c in ends)
    ax.set_ylim(np.floor(lo_y / 10) * 10 - 4, min(100, np.ceil(hi_y / 10) * 10 + 4))
    ax.set_xlim(-0.1, 1.02)
    ax.tick_params(labelbottom=False)
    ax.grid(axis="both", color=GRID)
    ax.set_ylabel("expected correct answers, Acc(p) (%)")
    # labels at both ends, spread so they never touch
    for side, idx in ((1, 2), (0, 1)):
        order = sorted(ends, key=lambda e: e[idx])
        span = ax.get_ylim()[1] - ax.get_ylim()[0]
        gap, placed = span * 0.055, []
        for s, *vals in order:
            v = vals[idx - 1]
            y = max(v, placed[-1] + gap) if placed else v
            placed.append(y)
            txt = f"{NAMES[s]} {v:.1f}" if side == 1 else f"{v:.1f}"
            ax.annotate(txt, (side, v), xytext=(10 if side else -10, 0), textcoords="offset points",
                        ha="left" if side else "right", va="center", fontsize=LABEL_SIZE, color=INK,
                        annotation_clip=False)
            if abs(y - v) > 1e-9:                                   # nudged: move the text, keep the anchor
                ax.texts[-1].remove()
                ax.annotate(txt, (side, v), xytext=(side + (0.012 if side else -0.012), y), textcoords="data",
                            ha="left" if side else "right", va="center", fontsize=LABEL_SIZE, color=INK,
                            annotation_clip=False)
    title(ax, "Acc(p) = p · a_C + (1 − p) · a_W on the two tool channels; p: the share of tool answers that are correct")
    # the crossings, marked on the lines and as intervals in the strip
    strip_rows = [s for s in MARKED if s in res["crossings"]["answered"]]
    for i, s in enumerate(strip_rows):
        e = res["crossings"]["answered"][s]
        y = len(strip_rows) - 1 - i
        name = f"{NAMES[s]} vs the instruction"
        if e["status"] == CROSSES:
            p = e["p_star"]
            acc = (e["b"]["a_W"] + p * (e["b"]["a_C"] - e["b"]["a_W"])) * 100
            ax.plot(p, acc, marker="o", markersize=11, markerfacecolor=WHITE, markeredgecolor=color(s),
                    markeredgewidth=2.4, zorder=5, linestyle="none")
            ax.axvline(p, color=color(s), linewidth=1.0, linestyle=(0, (4, 3)), zorder=1)
            strip.axvline(p, color=color(s), linewidth=1.0, linestyle=(0, (4, 3)), zorder=1)
            iv = e["interval"]
            if isinstance(iv, list):
                strip.plot(iv, [y, y], color=color(s), linewidth=6, solid_capstyle="butt", alpha=0.35, zorder=2)
                strip.plot([iv[0]] * 2, [y - 0.2, y + 0.2], color=color(s), linewidth=1.6, zorder=3)
                strip.plot([iv[1]] * 2, [y - 0.2, y + 0.2], color=color(s), linewidth=1.6, zorder=3)
            strip.plot(p, y, marker="o", markersize=8, color=color(s), markeredgecolor=WHITE, zorder=4,
                       linestyle="none")
            ivs = f"[{iv[0]:.2f}, {iv[1]:.2f}]" if isinstance(iv, list) else str(iv)
            words = (f"{name}: p* = {p:.2f} {ivs}\n{NAMES[s]} ahead {e['ahead']} p*; the order flipped in "
                     f"{e['flipped']:,} of {N_BOOT:,} resamples")
            right = isinstance(iv, list) and iv[1] < 0.62
            value(strip, words, ((iv[1] if right else iv[0]) if isinstance(iv, list) else p, y),
                  dx=8 if right else -8, ha="left" if right else "right", size=LABEL_SIZE - 0.5)
        else:
            strip.text(0.5, y, f"{name}: no crossing in (0, 1): {NAMES[s]} {e['status']} (dW {100 * e['dW']:+.1f}, "
                       f"dC {100 * e['dC']:+.1f} points)".replace("-", "−"), ha="center", va="center",
                       fontsize=LABEL_SIZE, color=INK, zorder=5,
                       bbox={"boxstyle": "square,pad=0.2", "facecolor": WHITE, "edgecolor": "none"})
    strip.set_ylim(-0.7, len(strip_rows) - 0.3)
    strip.set_yticks([])
    strip.set_xlim(-0.1, 1.02)
    strip.spines["left"].set_visible(False)
    strip.grid(axis="x", color=GRID)
    strip.grid(axis="y", visible=False)
    strip.set_xlabel("p: the share of the tool's answers that are correct")
    strip.text(0.0, 1.04, "where each crosses the instruction, with its 95% interval (questions resampled, paired)",
               transform=strip.transAxes, fontsize=LABEL_SIZE - 0.5, color=MUTED, va="bottom", style="italic")
    headline(fig, f"Expected accuracy under tool hints on E2, {LABEL}: base, the instruction, LoRA and A40.",
             "Each line runs from a_W (p = 0: every tool answer wrong) to a_C (p = 1: every tool answer right).")
    note(fig, FOOT + "a_C: correct answers among answered correct-hint tool runs; a_W: the right letter among answered "
         "wrong-hint tool runs (pasted and inserted; each system four wordings each way); line ends: 95% Wilson. "
         "p* = dW / (dW − dC) against the instruction; its interval: 20,000 resamples of questions (seed 0), clipped "
         "to [0, 1], resamples where the order flips left out and counted. Numbers: the CSV and tradeoff_e2.json.")
    paths = save(fig, "tradeoff_acc_p", rows, out)
    plt.close(fig)
    return paths


def figures(res, out):
    return fig_tradeoff(res, out) + fig_acc_p(res, out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(OUT), help="the runs' folder; tradeoff_<qset>.json is written there")
    ap.add_argument("--qset", choices=ev.QSETS, default="e2")
    ap.add_argument("--figures", action="store_true", help="also draw tradeoff_e2 and tradeoff_acc_p")
    ap.add_argument("--figures-only", action="store_true", help="draw the figures from a saved JSON, computing nothing")
    ap.add_argument("--json", help="the saved JSON for --figures-only (default OUT/tradeoff_<qset>.json)")
    ap.add_argument("--fig-out", default=str(CODE.parent / "docs" / "paper" / "figures"))
    a = ap.parse_args(argv)
    if a.figures_only:
        res = json.loads(Path(a.json or Path(a.out, f"tradeoff_{a.qset}.json")).read_text())
    else:
        res = report(a.out, a.qset)
        print(text(res))
    if a.figures or a.figures_only:
        for p in figures(res, a.fig_out):
            print(p)


if __name__ == "__main__":
    main()
