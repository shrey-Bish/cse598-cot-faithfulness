"""Track C, C18 (Oct 30): H33, is the cue the argument for the wrong letter? The pre-registered readings (no calls).
Pre-registered in docs/sessions/2026-10-30_1700_C_c18-prereg.md.

  python agents/c18.py                    # -> results/trackC/c18_summary.json; prints the readings

C16's solver final answers on bad lookups that name the tool (34 items, every one wrong), reviewed by Olmo 3.1 32B
Instruct and Qwen3 30B Instruct with plus_explanation and C4's prompt, in two versions run together:
  unchanged   team_c18_unchanged
  stripped    team_c18_stripped: the sentences that name the tool removed (run_team.strip_tool), the rest kept
References, no new calls: C17's own-working version of the same items (team_c17_own: C15's bare answer + "This answer is
based on my own step-by-step working.", a short answer with no argument and no tool) and C16's original reviews of the
unchanged answers (team_c16).

Main, per reviewer: stripped minus unchanged on correcting a wrong answer, paired by item, 95% bootstrap clustered by
item, c16.two_sided (C11's 20-point margin). Its reading for H33:
  the tool mentions are part of the cue   the interval lies above 0 (more corrections, or a smaller rise)
  the argument is the cue                 no change (removing the tool mentions doesn't restore corrections)
  removing them lowers corrections        the interval lies below 0
  unclear                                 otherwise
Also, no decision: stripped minus C17's own-working version (the argument against no argument, neither naming the
tool); unchanged minus C16's original reviews (the same answers, reviewed again).
"""
import argparse
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from agents.c15 import OLMO, QWEN, corrects  # noqa: E402
from agents.c16 import VARIANT, compare  # noqa: E402
from agents.run_team import OUT, complete_rows  # noqa: E402

LOGS = {"unchanged": "team_c18_unchanged", "stripped": "team_c18_stripped"}
REFERENCES = {"c17_own": "team_c17_own", "c16_original": "team_c16"}
NAMES = ("variant", "answer_only")      # paired()'s keys: the first group, then the one it is compared with
H33 = {"more corrections": "the tool mentions are part of the cue", "no change": "the argument is the cue",
       "fewer corrections": "removing them lowers corrections"}


def h33(e):
    r = e["reading"]
    if r.startswith("a smaller rise"):
        return H33["more corrections"]
    if r.startswith("a smaller drop"):
        return H33["fewer corrections"]
    return H33.get(r, r)


def rows_of(log_dir, name):
    path = Path(log_dir) / f"{name}.jsonl"
    return complete_rows(path) if path.exists() else []


def analyze(log_dir=OUT):
    rows = {k: rows_of(log_dir, v) for k, v in {**LOGS, **REFERENCES}.items()}
    items = {r["item_id"] for r in rows["unchanged"] if r["agent"] == "reviewer"}

    def cor(name, m):
        return {q: v for q, v in corrects(rows[name], m, VARIANT).items() if q in items}
    main = {m: compare(cor("stripped", m), cor("unchanged", m), NAMES) for m in (OLMO, QWEN)}
    removed = [r["sentences_removed"] for r in rows["stripped"] if r["agent"] == "reviewer"]
    return {"main_stripped_minus_unchanged": main,
            "reading": {m: h33(e) for m, e in main.items()},
            "stripped_minus_c17_own": {m: compare(cor("stripped", m), cor("c17_own", m), NAMES) for m in (OLMO, QWEN)},
            "unchanged_minus_c16_original": {m: compare(cor("unchanged", m), cor("c16_original", m), NAMES)
                                             for m in (OLMO, QWEN)},
            "sentences_removed": {"min": min(removed, default=None), "max": max(removed, default=None),
                                  "total": sum(removed)},
            "cases": {k: len({r["case_id"] for r in rows[k] if r["agent"] == "case_done"}) for k in LOGS}}


def show(res):
    def iv(e):
        return ("too few questions" if e.get("diff") is None
                else f"{e['diff']:+.0%} [{e['interval'][0]:+.0%}, {e['interval'][1]:+.0%}]")
    lines = [f"cases: {res['cases']}; sentences removed per answer: {res['sentences_removed']}"]
    for key, label in (("main_stripped_minus_unchanged", "corrects a wrong answer: stripped minus unchanged (main)"),
                       ("stripped_minus_c17_own", "stripped minus C17's own-working version (no decision)"),
                       ("unchanged_minus_c16_original", "unchanged minus C16's original reviews (no decision)")):
        lines.append(label)
        for m in (OLMO, QWEN):
            e = res[key][m]
            lines.append(f"  {m}: {e['variant_k']} of {e['variant_n']} against {e['answer_only_k']} of {e['answer_only_n']}: "
                         f"{iv(e)} ({e['items']} items) -> {e['reading']}"
                         + (f"; H33: {res['reading'][m]}" if key == "main_stripped_minus_unchanged" else ""))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()
    res = analyze()
    (OUT / "c18_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    print(show(res))


if __name__ == "__main__":
    main()
