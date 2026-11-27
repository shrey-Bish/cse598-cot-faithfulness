"""The handbook's Part C (Nov 26): three descriptive analyses from saved, frozen records. Post-freeze, no new runs; they
change no verdict. Each number is a count from saved rows with a Wilson interval, as everywhere.

  ../.venv/bin/python tools/handbook_part_c.py      # from cot-disclosure/; needs the gitignored records (below)
  -> results/summaries/handbook/part_c.json (numbers only, tracked) and docs/handbook/PART_C.md (the tables)

1. Evaluation at a glance: each dataset, measure, baseline, system and headline result, from 02_NUMBERS' rows (no new
   number); the backup slide "Datasets, metrics and baselines".
2. How the answers fail, by category: the hand labels' categories (the rater guide's: no_mention, mentions_only,
   says_changed, rejects_hint, unclear), Ritik's final labels, by labelled set, system and channel.
   - L6 (results/labels/L6/L6_RA_20261113.csv, key_L6.csv): a seeded sample of followed wrong-hint runs on the 120 fresh
     questions, 14 per system and channel, the instruction and fine-tuning (42 each).
   - L4 part 1 (results/labels/gate3/L4/L4_part1_RA.csv, key_L4.csv): Gate 3's fine-tuned keyword candidates (147) and
     the followed runs of no fix and the instruction matched to them (74, 73). Not a random sample: the keyword picked
     the fine-tuned rows.
   Every labelled row followed its hint (eval.sheet_plan, the L6 rule): no sheet holds a resisted answer.
   The backup slide "How the answers fail, by category" shows L6 (the random sample).
3. By subject on the 120 fresh questions (30 each of chemistry, engineering, law and physics): wrong-hint following and
   right-tool-hint acceptance, pooled as A39's report pools them (finetune/a39.py MEASURES, pick), for no fix, the
   instruction, fine-tuning and consistency training, from results/trackA/gpu/a39/ (numbers only, gitignored).
   Under 5 questions in a cell: "too few questions" (never here: 30 each).
"""
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
ROOT = CODE.parent
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import load, wilson  # noqa: E402

LABEL = "descriptive, post-freeze (Nov 26)"
OUT_JSON = CODE / "results" / "summaries" / "handbook" / "part_c.json"
OUT_MD = ROOT / "docs" / "handbook" / "PART_C.md"
A39_OUT = CODE / "results" / "trackA" / "gpu" / "a39"
E2 = CODE / "data" / "progress" / "mmlupro_e2.jsonl"
L6_LABELS, L6_KEY = CODE / "results/labels/L6/L6_RA_20261113.csv", CODE / "results/labels/L6/key_L6.csv"
L4_LABELS, L4_KEY = CODE / "results/labels/gate3/L4/L4_part1_RA.csv", CODE / "results/labels/gate3/L4/key_L4.csv"
CATEGORIES = ("no_mention", "mentions_only", "says_changed", "rejects_hint", "unclear")
PLAIN_CAT = {"no_mention": "No mention of the hint", "mentions_only": "Mentions the hint only",
             "says_changed": "Says the hint changed its answer", "rejects_hint": "Says it rejected the hint",
             "unclear": "Unclear"}
SYSTEMS = ("base", "prompt_only", "lora", "a40")
PLAIN_SYS = {"base": "No fix", "prompt_only": "One-line instruction", "lora": "Fine-tuning (LoRA)",
             "a40": "Consistency training"}
MIN_QUESTIONS = 5


def rec(k, n, questions=None):
    out = {"k": k, "n": n, "text": f"{k} of {n}", "rate": k / n if n else None, "wilson": wilson(k, n)}
    if questions is not None:
        out["questions"] = questions
        if questions < MIN_QUESTIONS:
            out["note"] = "too few questions"
    return out


# ---------------------------------------------------------------- 1. at a glance (02_NUMBERS' rows, no new number)
GLANCE = [  # (data, measure, compared with, systems, headline, finding, 02 rows)
    ("54 test questions, 3 runs each (Track B)", "follows the same wrong answer", "the same answer from the user",
     "12 open models, thinking on and off", "Qwen3 30B Instruct: 1 of 162 from the user, 147 of 162 from its own tool call",
     "F16", "N132"),
    ("the same questions, after a tool call", "names the tool (keywords)", "the private reasoning",
     "Qwen3 8B, thinking on", "reasoning 141 of 145; final answer 0 of 143", "F29", "N134, N135"),
    ("Olmo 3 7B Think's takeovers (19 cuts, 9 questions)", "share of the hint's effect (activation patching)",
     "all 32 layers", "Olmo 3 7B Think", "layers 15, 19 and 23 carry 0.90 [0.85, 0.96]", "F11", "N92"),
    ("120 fresh questions (held out)", "follows a wrong hint; takes a right tool hint", "no fix; the one-line instruction",
     "five trained versions", "consistency training: 297 of 703 → 84 of 694 wrong hints followed; 439 of 476 → 347 of 459 "
     "right tool hints taken", "F41", "N151"),
    ("84 hand-labelled followed answers", "the final answer says the hint shaped it", "the one-line instruction",
     "fine-tuning (LoRA)", "37 of 42 against 18 of 42", "F45", "N75"),
    ("Track C's 73 wrong tool answers", "the reviewer corrects a wrong answer", "the reviewer seeing the answer only",
     "Olmo 3.1 32B reviewer", "59 of 73 alone; 3 of 73 with the tool's reply", "F18", "N48"),
    ("100 fresh items (Track C)", "wrong answers stopped", "the reviewer alone", "the checker (re-solves without the tool)",
     "53 of 53", "F24", "N137"),
    ("the same 100 items, after the freeze", "wrong answers reaching the user", "the original model as solver",
     "consistency-trained solver", "29 of 55 → 15 of 55 with the solver alone", "C27", "N164, N165"),
]


def glance():
    return [dict(zip(("data", "measure", "compared_with", "systems", "headline", "finding", "numbers_rows"), g))
            for g in GLANCE]


# ---------------------------------------------------------------- 2. the hand labels' categories
def _labels(labels, key, set_name):
    keyed = {r["row"]: r for r in csv.DictReader(open(key))}
    rows = []
    for r in csv.DictReader(open(labels)):
        k = keyed[r["row"]] if "part" not in next(iter(keyed.values())) else None
        rows.append((r, k))
    return rows


def taxonomy():
    out = {"note": "every labelled row followed its hint; no sheet holds a resisted answer", "sets": {}}
    # L6: key rows by row number
    key6 = {r["row"]: r for r in csv.DictReader(open(L6_KEY))}
    l6 = [(key6[r["row"]]["system"], r["channel"], r["label_final"]) for r in csv.DictReader(open(L6_LABELS))]
    # L4 part 1: key rows of part 1 by row number
    key4 = {r["row"]: r for r in csv.DictReader(open(L4_KEY)) if r["part"] == "1"}
    l4 = []
    for r in csv.DictReader(open(L4_LABELS)):
        k = key4[r["row"]]
        group = f"{k['system']}, {'keyword candidate' if k['candidate'] == 'True' else 'matched followed run'}"
        l4.append((group, r["channel"], r["label_final"]))
    for name, rows, source in (("L6", l6, "results/labels/L6/L6_RA_20261113.csv + key_L6.csv"),
                               ("L4 part 1", l4, "results/labels/gate3/L4/L4_part1_RA.csv + key_L4.csv")):
        groups = sorted({g for g, _, _ in rows})
        s = {"source": source, "rows": len(rows), "by_group": {}, "by_group_channel": {}}
        for g in groups:
            sub = [c for gg, _, c in rows if gg == g]
            cnt = Counter(sub)
            assert not set(cnt) - set(CATEGORIES), set(cnt) - set(CATEGORIES)
            s["by_group"][g] = {c: rec(cnt[c], len(sub)) for c in CATEGORIES}
            for ch in sorted({ch for gg, ch, _ in rows if gg == g}):
                sub2 = [c for gg, cc, c in rows if gg == g and cc == ch]
                cnt2 = Counter(sub2)
                s["by_group_channel"][f"{g} | {ch}"] = {c: rec(cnt2[c], len(sub2)) for c in CATEGORIES}
        out["sets"][name] = s
    return out


# ---------------------------------------------------------------- 3. by subject on the 120 fresh questions
def by_subject(out=A39_OUT):
    from common import latest
    from finetune import a39
    rows = latest([r for r in a39.of_set(a39.read(out)[0], "e2") if r.get("status") == "ok"])   # as a39.by_system
    by = {s: [r for r in rows if r.get("system") == s] for s in SYSTEMS}
    cat = {f"mmlupro-{q['question_id']}": q["category"] for q in load(E2)}
    subjects = sorted(set(cat.values()))
    res = {"subjects": {s: sum(1 for c in cat.values() if c == s) for s in subjects}, "systems": {}}
    for system in SYSTEMS:
        res["systems"][system] = {}
        for measure in ("following", "acceptance"):
            row = {}
            for subj in (*subjects, "all"):
                rs = [r for r in by[system] if subj == "all" or cat.get(r["item_id"]) == subj]
                runs, outcome = a39.pick(rs, measure)
                row[subj] = rec(sum(1 for r in runs if outcome(r)), len(runs), len({r["item_id"] for r in runs}))
            res["systems"][system][measure] = row
    return res


# ---------------------------------------------------------------- outputs
def pct(r):
    return "—" if r["rate"] is None else f"{100 * r['rate']:.0f}%"


def iv(r):
    lo, hi = r["wilson"]
    return f"[{100 * lo:.0f}, {100 * hi:.0f}%]"


def markdown(res):
    L = ["# The handbook's Part C: three descriptive analyses (Nov 26)", "",
         f"**{LABEL.capitalize()}.** From saved, frozen records only; no new runs; no verdict changes. Made by "
         "`cot-disclosure/tools/handbook_part_c.py`; numbers in `cot-disclosure/results/summaries/handbook/part_c.json`; "
         "checked by `cot-disclosure/tests/test_handbook_part_c.py`. Rates are k of n runs with a 95% Wilson interval.", "",
         "## 1. Evaluation at a glance", "",
         "Each headline is a row of [02_NUMBERS](../presentation/pack/02_NUMBERS.md) (no new number). The backup slide "
         "\"Datasets, metrics and baselines\" shows it without the codes.", "",
         "| data | measure | compared with | systems | headline | finding | 02 rows |", "|---|---|---|---|---|---|---|"]
    for g in res["glance"]:
        L.append(f"| {g['data']} | {g['measure']} | {g['compared_with']} | {g['systems']} | {g['headline']} | "
                 f"{g['finding']} | {g['numbers_rows']} |")
    t = res["taxonomy"]
    L += ["", "## 2. How the answers fail, by category (the hand labels)", "",
          f"{t['note'].capitalize()}. Ritik's final labels; the categories are the rater guide's "
          "([docs/labeling/](../labeling/)).", ""]
    for name, s in t["sets"].items():
        L += [f"### {name} ({s['rows']} rows; `cot-disclosure/{s['source']}`)", "",
              "| group | n | " + " | ".join(PLAIN_CAT[c] for c in CATEGORIES) + " |", "|---|---|" + "---|" * len(CATEGORIES)]
        for g, cells in s["by_group"].items():
            n = next(iter(cells.values()))["n"]
            L.append(f"| {g} | {n} | " + " | ".join(f"{cells[c]['k']} ({pct(cells[c])})" for c in CATEGORIES) + " |")
        L += ["", "By channel:", "", "| group, channel | n | " + " | ".join(CATEGORIES) + " |",
              "|---|---|" + "---|" * len(CATEGORIES)]
        for g, cells in s["by_group_channel"].items():
            n = next(iter(cells.values()))["n"]
            L.append(f"| {g} | {n} | " + " | ".join(str(cells[c]["k"]) for c in CATEGORIES) + " |")
        L.append("")
    b = res["by_subject"]
    subj = list(b["subjects"])
    L += ["## 3. By subject on the 120 fresh questions (descriptive)", "",
          "Pooled as A39's report pools them (answered runs; wrong hints over the user's, pasted and inserted channels; "
          "right hints over the tool channels). " + ", ".join(f"{s} {n}" for s, n in b["subjects"].items()) + " questions.", ""]
    for measure, title in (("following", "Wrong hints followed (lower is better)"),
                           ("acceptance", "Right tool hints taken (higher is better)")):
        L += [f"**{title}**", "", "| system | " + " | ".join(subj) + " | all |", "|---|" + "---|" * (len(subj) + 1)]
        for system in SYSTEMS:
            cells = b["systems"][system][measure]
            L.append(f"| {PLAIN_SYS[system]} | " + " | ".join(f"{cells[s]['text']} ({pct(cells[s])}) {iv(cells[s])}"
                                                           for s in (*subj, "all")) + " |")
        L.append("")
    return "\n".join(L) + "\n"


def run():
    res = {"made_by": "tools/handbook_part_c.py", "label": LABEL,
           "made_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "glance": glance(), "taxonomy": taxonomy(), "by_subject": by_subject()}
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(res, indent=1) + "\n")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(markdown(res))
    return res


if __name__ == "__main__":
    r = run()
    b = r["by_subject"]["systems"]
    for s in SYSTEMS:
        print(s, {m: b[s][m]["all"]["text"] for m in ("following", "acceptance")})
    for name, s in r["taxonomy"]["sets"].items():
        print(name, {g: {c: v["k"] for c, v in cells.items()} for g, cells in s["by_group"].items()})
