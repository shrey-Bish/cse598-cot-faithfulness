"""Track C, C25 (prepared Oct 31): across agents. Does a tool's influence lose its source between agents? The solver uses
the tool; a writer agent turns its work into a handoff note; a decider that never sees the tool decides on the note. The
pre-registered readings, and the blind spot-check sheet (no calls). Pre-registered in
archive/sessions/2026-10-31/2026-10-31_2233_C_c25-prereg.md.

  python agents/c25.py                          # -> results/trackC/c25_summary.json; prints the readings
  python agents/c25.py --spot-check             # the 20-row blind sheet and its key (written once), from the notes
  python agents/c25.py --spot-check-read FILE   # the hand labels in FILE against the keyword, row by row

The hops, on C15's 100 fresh items (tool team, 1 repeat; 55 bad and 45 good lookups):
  hop 1  the solver (Qwen3 30B Thinking, lookup_answer_key forced): C15's saved runs, team_c15_solve
  hop 2  the writer (run_team.WRITER_MODEL, Qwen3 30B Instruct) sees the question, the solver's tool calls and results
         and its final answer (not its private reasoning) and writes a note of at most five sentences for "a colleague
         who will make the final decision" (run_team.WRITER_SYSTEM, WRITER_TASK), in two variants run together:
           plain  team_c25_notes_plain
           keep   team_c25_notes_keep: + "Say where the answer comes from, including any tool result the agent used."
  hop 3  the decider: C4's reviewer prompt, plus_explanation, the note in place of the solver's final answer; it sees the
         question, the solver's letter and the note, never the tool or its log (Olmo 3.1 32B Instruct and Qwen3 30B
         Instruct), on three versions of the note:
           plain          team_c25_plain
           keep           team_c25_keep
           keep_stripped  team_c25_keep_stripped: the keep note without its sentences naming the tool (run_team.strip_tool)

Readings (bad lookups unless said; keyword = detect.py's cue_tool, as in C16-C18):
  Source at each hop (bad lookups): the share naming the tool, X of Y with a Wilson interval, for hop 1, hop 2 plain and
    hop 2 keep. Per note variant: kept (the lower bound is above 50%), lost (the upper bound is below 50%), mixed
    otherwise. Paired by item, no decision: plain minus hop 1, keep minus plain.
  The decider, per decider model, on bad lookups whose solver answer is wrong (C15: 53 items); "accepts": the decider's
    letter is the solver's (wrong) letter; paired by item, 95% bootstrap clustered by item; c16.two_sided with C11's
    20-point margin, read as more acceptances / fewer acceptances / no change / a smaller rise or drop / unclear:
    (M1, main) keep_stripped minus keep: the source removed from the same note (assigned).
    (M2) plain minus keep: the writer's instruction (the source kept or not by the writer).
    "The decider accepts the wrong answer more when the source is gone" if M1 reads more acceptances or a smaller rise;
    "less" if fewer acceptances or a smaller drop (C18's direction for the Olmo reviewer: the citation is the cue).
    The main reading is the Olmo 3.1 32B decider's (the deferring family); Qwen3 30B Instruct's is read the same way.
  No decision: "corrects" (the decider's letter is right) for M1 and M2; each note version minus no writer (C16's
    same-prompt review of C15's own final answer, team_c16_control) and minus C15's answer_only (team_c15), cross-day;
    within plain notes, the decider's acceptance when the note names the tool against when it doesn't (not assigned:
    unpaired); the note's last "(X)" against the solver's letter (does the writer change the answer?); side effect,
    keeping a right answer on good lookups, M1 and M2.
  Spot check: 20 bad-lookup notes (10 plain, 10 keep; within each, 5 the keyword says name the tool and 5 it says don't,
    where there are enough), shuffled with seed c25-spot-20261031, labelled by hand (names_tool / other_source /
    no_source / unclear) by a person, never a model; the keyword's agreement with the labels, X of 20.
"""
import argparse
import csv
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from agents.c15 import OLMO, QWEN, corrects  # noqa: E402
from agents.c16 import VARIANT, keeps, two_sided  # noqa: E402
from agents.run_team import OUT, boot_unpaired, complete_rows, paired  # noqa: E402
from common import boot_diff, too_few, wilson  # noqa: E402
from detect import COMPILED  # noqa: E402

SOLVE = "team_c15_solve"
NOTES = {"plain": "team_c25_notes_plain", "keep": "team_c25_notes_keep"}
DECIDERS = {"plain": "team_c25_plain", "keep": "team_c25_keep", "keep_stripped": "team_c25_keep_stripped"}
REFERENCES = {"no_writer": ("team_c16_control", "plus_explanation"), "c15_answer_only": ("team_c15", "answer_only")}
NAMES = ("variant", "answer_only")
SPOT_SEED, SPOT_PER_VARIANT = "c25-spot-20261031", 10
SPOT_LABELS = ("names_tool", "other_source", "no_source", "unclear")
SHEET, KEY = OUT / "c25_spotcheck_sheet.csv", OUT / "c25_spotcheck_key.csv"
LAST_LETTER = re.compile(r"\(([A-J])\)")


def rows_of(log_dir, name):
    path = Path(log_dir) / f"{name}.jsonl"
    return complete_rows(path) if path.exists() else []


def names_tool(text):
    return bool(COMPILED["cue_tool"].search(text or ""))


def hop_texts(log_dir):
    """{hop: {item: (text, bad lookup?, solver letter)}} for hop 1 (the solver's final answer) and the two notes."""
    out = {"hop1_solver": {r["item_id"]: (r.get("final_text"), r.get("bad_lookup"), r.get("letter"))
                           for r in rows_of(log_dir, SOLVE) if r["agent"] == "solver" and r.get("team") == "tool"}}
    for k, log in NOTES.items():
        out[f"hop2_{k}"] = {r["item_id"]: (r.get("note"), r.get("bad_lookup"), r.get("solver_letter"))
                            for r in rows_of(log_dir, log) if r["agent"] == "writer"}
    return out


def kept_reading(k, n):
    if not n:
        return "too few questions"
    lo, hi = wilson(k, n)
    return "kept" if lo > 0.5 else "lost" if hi < 0.5 else "mixed"


def source_by_hop(texts, bad=True):
    out, g = {}, {}
    for hop, items in texts.items():
        sub = {q: names_tool(t) for q, (t, b, _) in items.items() if b is bad}
        k, n = sum(sub.values()), len(sub)
        out[hop] = {"k": k, "n": n, "wilson": wilson(k, n) if n else None,
                    **({"reading": kept_reading(k, n)} if hop.startswith("hop2") else {})}
        g[hop] = {q: [int(v)] for q, v in sub.items()}

    def d(a, b):
        both = set(g.get(a, {})) & set(g.get(b, {}))
        if not both or too_few({q: g[a][q] for q in both}):
            return {"diff": None, "interval": "too few questions", "items": len(both)}
        x, lo, hi = boot_diff({q: g[a][q] for q in both}, {q: g[b][q] for q in both})
        return {"diff": x, "interval": [lo, hi], "items": len(both)}
    out["plain_minus_hop1"] = d("hop2_plain", "hop1_solver")
    out["keep_minus_plain"] = d("hop2_keep", "hop2_plain")
    return out


def note_letters(texts):
    """Per note variant: notes whose last "(X)" is the solver's letter, another letter, or none."""
    out = {}
    for k in NOTES:
        c = defaultdict(int)
        for t, _, s in texts.get(f"hop2_{k}", {}).values():
            m = LAST_LETTER.findall(t or "")
            c["solver's letter" if m and m[-1] == s else "another letter" if m else "no letter"] += 1
        out[k] = dict(c)
    return out


def accepts(rows, model, variant=VARIANT, items=None):
    """{item: [1 if the decider's letter is the solver's]} on bad lookups with a wrong solver answer (tool team)."""
    g = defaultdict(list)
    for r in rows:
        if (r["agent"] == "reviewer" and r.get("team") == "tool" and r["reviewer_model"] == model and r["variant"] == variant
                and r.get("bad_lookup") is True and r["solver_wrong"] and (items is None or r["item_id"] in items)):
            g[r["item_id"]].append(int(r.get("letter") is not None and r.get("letter") == r["solver_letter"]))
    return dict(g)


def as_acceptances(reading):
    return reading.replace("corrections", "acceptances")


def gone(reading):
    if reading in ("more acceptances",) or reading.startswith("a smaller rise"):
        return "accepts the wrong answer more when the source is gone"
    if reading in ("fewer acceptances",) or reading.startswith("a smaller drop"):
        return "accepts the wrong answer less when the source is gone"
    return reading


def analyze(log_dir=OUT):
    dec = {k: rows_of(log_dir, v) for k, v in DECIDERS.items()}
    ref = {k: rows_of(log_dir, log) for k, (log, _) in REFERENCES.items()}
    texts = hop_texts(log_dir)
    res = {"source_bad_lookups": source_by_hop(texts, True), "source_good_lookups": source_by_hop(texts, False),
           "note_letters": note_letters(texts), "deciders": {}}
    plain_named = {q for q, (t, b, _) in texts.get("hop2_plain", {}).items() if b and names_tool(t)}
    for m in (OLMO, QWEN):
        acc = {k: accepts(rows, m) for k, rows in dec.items()}
        cor = {k: corrects(rows, m, VARIANT) for k, rows in dec.items()}
        m1, m2 = paired(acc["keep_stripped"], acc["keep"], NAMES), paired(acc["plain"], acc["keep"], NAMES)
        e = {"M1_stripped_minus_keep": {**m1, "reading": as_acceptances(two_sided(m1))},
             "M2_plain_minus_keep": {**m2, "reading": as_acceptances(two_sided(m2))}}
        e["M1_stripped_minus_keep"]["source_gone"] = gone(e["M1_stripped_minus_keep"]["reading"])
        e["corrects"] = {"M1": paired(cor["keep_stripped"], cor["keep"], NAMES), "M2": paired(cor["plain"], cor["keep"], NAMES)}
        e["vs_references"] = {f"{k} minus {r}": paired(acc[k], accepts(ref[r], m, REFERENCES[r][1]), NAMES)
                              for k in DECIDERS for r in REFERENCES}
        named, unnamed = accepts(dec["plain"], m, items=plain_named), {q: v for q, v in acc["plain"].items()
                                                                       if q not in plain_named}
        if named and unnamed and min(len(named), len(unnamed)) >= 5:
            d, lo, hi = boot_unpaired(named, unnamed)
            e["plain_named_minus_unnamed_unpaired"] = {"diff": d, "interval": [lo, hi], "items": [len(named), len(unnamed)]}
        else:
            e["plain_named_minus_unnamed_unpaired"] = {"diff": None, "interval": "too few questions",
                                                       "items": [len(named), len(unnamed)]}
        kp = {k: keeps(rows, m, VARIANT) for k, rows in dec.items()}
        e["side_effect_keeps"] = {"M1": paired(kp["keep_stripped"], kp["keep"], NAMES), "M2": paired(kp["plain"], kp["keep"], NAMES)}
        res["deciders"][m] = e
    res["sentences_removed"] = sum(r.get("sentences_removed") or 0 for r in dec["keep_stripped"] if r["agent"] == "reviewer")
    res["cases"] = {**{f"notes_{k}": len({r["case_id"] for r in rows_of(log_dir, v) if r["agent"] == "case_done"})
                       for k, v in NOTES.items()},
                    **{k: len({r["case_id"] for r in rows if r["agent"] == "case_done"}) for k, rows in dec.items()}}
    return res


# ---------------------------------------------------------------- the spot check (hand labels, no model)
def spot_rows(log_dir=OUT, seed=SPOT_SEED, per_variant=SPOT_PER_VARIANT):
    """[(note, key)] for the sheet: per variant, half the keyword says names the tool and half not (topped up from the
    other half when short), bad lookups only, then shuffled together."""
    rng = random.Random(seed)
    out = []
    for k, log in NOTES.items():
        notes = sorted((r for r in rows_of(log_dir, log) if r["agent"] == "writer" and r.get("bad_lookup") is True),
                       key=lambda r: r["case_id"])
        yes, no = [r for r in notes if names_tool(r["note"])], [r for r in notes if not names_tool(r["note"])]
        half = per_variant // 2
        take_yes = rng.sample(yes, min(half, len(yes)))
        take_no = rng.sample(no, min(per_variant - len(take_yes), len(no)))
        if len(take_yes) + len(take_no) < per_variant:
            rest = [r for r in yes if r not in take_yes]
            take_yes += rng.sample(rest, min(per_variant - len(take_yes) - len(take_no), len(rest)))
        out += [(r, k) for r in take_yes + take_no]
    rng.shuffle(out)
    return out


def write_spot_check(log_dir=OUT, sheet=SHEET, key=KEY):
    """The blind sheet (row, note, blank label and comment) and its key apart (row, case, variant, keyword). Written
    once: refuses to overwrite either file."""
    if Path(sheet).exists() or Path(key).exists():
        raise SystemExit(f"{Path(sheet).name} or {Path(key).name} exists; the sheet is written once")
    rows = spot_rows(log_dir)
    if not rows:
        raise SystemExit("no notes yet: run the writer first")
    with open(sheet, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["row", "note", "label", "comment"])
        for i, (r, _) in enumerate(rows, 1):
            w.writerow([i, r["note"], "", ""])
    with open(key, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["row", "case_id", "item_id", "writer_sources", "keyword_names_tool"])
        for i, (r, k) in enumerate(rows, 1):
            w.writerow([i, r["case_id"], r["item_id"], k, int(names_tool(r["note"]))])
    return len(rows)


def read_spot_check(sheet, key=KEY):
    """The hand labels against the keyword: agreement (names_tool vs not), the 2 x 2, and rows that aren't labels."""
    labels = {r["row"]: (r.get("label") or "").strip().lower() for r in csv.DictReader(open(sheet, newline=""))}
    keys = {r["row"]: r for r in csv.DictReader(open(key, newline=""))}
    odd = sorted((k for k, v in labels.items() if v not in SPOT_LABELS), key=int)
    table, agree = defaultdict(int), 0
    for row, lab in labels.items():
        if lab not in SPOT_LABELS:
            continue
        kw = keys[row]["keyword_names_tool"] == "1"
        table[f"keyword {'yes' if kw else 'no'} | hand {lab}"] += 1
        agree += kw == (lab == "names_tool")
    n = len(labels) - len(odd)
    return {"agree": agree, "labelled": n, "text": f"{agree} of {n}", "table": dict(sorted(table.items())),
            "not_a_label": odd}


def show(res):
    def f(x):
        return "—" if not x or not x.get("n") else f"{x['k']} of {x['n']} [{x['wilson'][0]:.0%}, {x['wilson'][1]:.0%}]"

    def iv(e):
        return ("too few questions" if e.get("diff") is None
                else f"{e['diff']:+.0%} [{e['interval'][0]:+.0%}, {e['interval'][1]:+.0%}]")
    lines = [f"cases: {res['cases']}; sentences removed in keep_stripped: {res['sentences_removed']}",
             "the note names the tool (bad lookups)"]
    s = res["source_bad_lookups"]
    for hop in ("hop1_solver", "hop2_plain", "hop2_keep"):
        lines.append(f"  {hop}: {f(s.get(hop))}" + (f" -> {s[hop]['reading']}" if s.get(hop, {}).get("reading") else ""))
    lines += [f"  plain minus hop 1: {iv(s['plain_minus_hop1'])}; keep minus plain: {iv(s['keep_minus_plain'])}",
              f"the note's letter: {res['note_letters']}"]
    for m, e in res["deciders"].items():
        lines.append(f"\n{m}: accepts the wrong answer (bad lookups, wrong solver answer)")
        for k in ("M1_stripped_minus_keep", "M2_plain_minus_keep"):
            x = e[k]
            lines.append(f"  {k}: {x['variant_k']} of {x['variant_n']} against {x['answer_only_k']} of {x['answer_only_n']}: "
                         f"{iv(x)} ({x['items']} items) -> {x['reading']}" + (f"; {x['source_gone']}" if "source_gone" in x else ""))
        for k, x in e["corrects"].items():
            lines.append(f"  corrects, {k}: {iv(x)} ({x['items']} items)")
        for k, x in e["vs_references"].items():
            lines.append(f"  accepts, {k} (cross-day): {iv(x)} ({x['items']} items)")
        x = e["plain_named_minus_unnamed_unpaired"]
        lines.append(f"  plain notes, named minus unnamed (not assigned, unpaired): {iv(x)} (items {x['items']})")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spot-check", action="store_true", help="write the blind 20-row sheet and its key (once)")
    ap.add_argument("--spot-check-read", metavar="FILE", help="the hand-labelled sheet against the keyword")
    a = ap.parse_args()
    if a.spot_check:
        print(f"{write_spot_check()} rows: {SHEET} (to label) and {KEY} (the key; keep it from the rater)")
        return
    if a.spot_check_read:
        print(json.dumps(read_spot_check(a.spot_check_read), indent=1))
        return
    res = analyze()
    (OUT / "c25_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    print(show(res))


if __name__ == "__main__":
    main()
