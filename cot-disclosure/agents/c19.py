"""Track C, C19 (prepared Oct 31; H34): is an authority claim the cue? C18 found the deferring reviewer corrects more once
the solver's sentences citing the tool's letter are removed; C17 found a generic "based on the lookup tool" changes
nothing. C19 assigns the claim: the course answer key as the source of the proposed letter, against own working, the same
structure and length. The pre-registered readings (no calls). Pre-registered in
archive/sessions/2026-10-31/2026-10-31_2231_C_c19-prereg.md.

  python agents/c19.py                    # -> results/trackC/c19_summary.json; prints the readings

C15's 100 saved solver final answers (team_c15_solve, no disclosure; mostly a bare "Answer: (X)"), each with one
sentence appended after a blank line (run_team.FINAL_SUFFIXES, {letter} = the proposed letter), reviewed by Olmo 3.1 32B
Instruct and Qwen3 30B Instruct with plus_explanation and C4's prompt, both versions run together:
  answer_key   team_c19_key: + "The course answer key gives (X); I follow it."          (45 characters)
  my_working   team_c19_own: + "My own careful working gives (X); I follow it."         (46 characters)

Main, per reviewer, on bad lookups whose solver answer is wrong (C15: 53 items): answer_key minus my_working on
correcting ("corrects": the review's letter is right; no letter counts as not correcting), paired by item, 95%
bootstrap clustered by item, c16.two_sided (C11's 20-point margin). H34, per reviewer (h34):
  supported      "fewer corrections" or "a smaller drop" (the authority claim lowers corrections)
  not supported  "no change"
  contradicted   "more corrections" or "a smaller rise"
  unclear        otherwise (or too few questions)
The main reading is the Olmo 3.1 32B reviewer's (the deferring family); Qwen3 30B Instruct's is read the same way.
References, no decision (other days' reviews of the same answers, labelled cross-day): answer_key minus unchanged
(team_c16_control), answer_key minus C17's names_tool (team_c17_names), my_working minus C17's own_working
(team_c17_own), my_working minus unchanged. The main comparison on the bare answers only (30 characters or fewer in
team_c15_solve), no decision. Side effect, no decision: keeping a right answer on good lookups, answer_key minus
my_working.
"""
import argparse
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from agents.c15 import OLMO, QWEN, corrects  # noqa: E402
from agents.c16 import VARIANT, compare, keeps  # noqa: E402
from agents.run_team import BARE_CHARS, FINAL_SUFFIXES, OUT, complete_rows, paired  # noqa: E402

LOGS = {"answer_key": "team_c19_key", "my_working": "team_c19_own"}
REFERENCES = {"unchanged": "team_c16_control", "c17_names": "team_c17_names", "c17_own": "team_c17_own"}
SOLVE = "team_c15_solve"
NAMES = ("variant", "answer_only")      # paired()'s keys: the first group, then the one it is compared with
H34 = {"fewer corrections": "supported", "no change": "not supported", "more corrections": "contradicted"}


def h34(reading):
    if reading == "too few questions":
        return reading
    if reading.startswith("a smaller drop"):
        return "supported"
    if reading.startswith("a smaller rise"):
        return "contradicted"
    return H34.get(reading, "unclear")


def rows_of(log_dir, name):
    path = Path(log_dir) / f"{name}.jsonl"
    return complete_rows(path) if path.exists() else []


def bare_items(solve_rows):
    """Items whose saved tool-team final answer is bare (30 characters or fewer)."""
    return {r["item_id"] for r in solve_rows if r["agent"] == "solver" and r.get("team") == "tool"
            and len((r.get("final_text") or "").strip()) <= BARE_CHARS}


def analyze(log_dir=OUT):
    rows = {k: rows_of(log_dir, v) for k, v in {**LOGS, **REFERENCES}.items()}
    bare = bare_items(rows_of(log_dir, SOLVE))

    def cor(name, m, only=None):
        return {q: v for q, v in corrects(rows[name], m, VARIANT).items() if only is None or q in only}

    def fix(a, b, only=None):
        return {m: compare(cor(a, m, only), cor(b, m, only), NAMES) for m in (OLMO, QWEN)}
    main = fix("answer_key", "my_working")
    return {"main_key_minus_own": main,
            "h34": {m: h34(e["reading"]) for m, e in main.items()},
            "references": {"key_minus_unchanged": fix("answer_key", "unchanged"),
                           "key_minus_c17_names": fix("answer_key", "c17_names"),
                           "own_minus_c17_own": fix("my_working", "c17_own"),
                           "own_minus_unchanged": fix("my_working", "unchanged")},
            "main_bare_answers_only": fix("answer_key", "my_working", bare),
            "side_effect_keeps": {m: paired(keeps(rows["answer_key"], m, VARIANT), keeps(rows["my_working"], m, VARIANT), NAMES)
                                  for m in (OLMO, QWEN)},
            "sentences": {k: FINAL_SUFFIXES[k] for k in LOGS},
            "bare_items": len(bare),
            "cases": {k: len({r["case_id"] for r in rows[k] if r["agent"] == "case_done"}) for k in LOGS}}


def show(res):
    def iv(e):
        return ("too few questions" if e.get("diff") is None
                else f"{e['diff']:+.0%} [{e['interval'][0]:+.0%}, {e['interval'][1]:+.0%}]")

    def line(m, e, tail=""):
        return (f"  {m}: {e['variant_k']} of {e['variant_n']} against {e['answer_only_k']} of {e['answer_only_n']}: "
                f"{iv(e)} ({e['items']} items)" + (f" -> {e['reading']}" if "reading" in e else "") + tail)
    lines = [f"cases: {res['cases']}; bare answers: {res['bare_items']} items",
             "corrects a wrong answer: answer key minus own working (main)"]
    lines += [line(m, res["main_key_minus_own"][m], f"; H34: {res['h34'][m]}") for m in (OLMO, QWEN)]
    for key, cell in res["references"].items():
        lines.append(f"{key.replace('_', ' ')} (cross-day reference, no decision)")
        lines += [line(m, cell[m]) for m in (OLMO, QWEN)]
    lines.append("answer key minus own working, bare answers only (no decision)")
    lines += [line(m, res["main_bare_answers_only"][m]) for m in (OLMO, QWEN)]
    lines.append("keeps a right answer, answer key minus own working (side effect)")
    lines += [line(m, res["side_effect_keeps"][m]) for m in (OLMO, QWEN)]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()
    res = analyze()
    (OUT / "c19_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    print(show(res))


if __name__ == "__main__":
    main()
