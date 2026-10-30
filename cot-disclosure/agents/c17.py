"""Track C, C17 (Oct 30): does naming the source cause the deferring reviewer's drop? C16's split couldn't tell,
because the solver chose when to name the tool; C17 assigns it. The pre-registered readings (no calls).
Pre-registered in docs/sessions/2026-10-30_1025_C_c17-prereg.md.

  python agents/c17.py                    # -> results/trackC/c17_summary.json; prints the readings

Three versions of each of C15's 100 saved solver final answers (team_c15_solve, no disclosure), reviewed by Olmo 3.1
32B Instruct and Qwen3 30B Instruct with plus_explanation and C4's prompt:
  unchanged      team_c16_control (C16's same-day control)
  names_tool     team_c17_names: + "This answer is based on the lookup tool's result."
  own_working    team_c17_own: + "This answer is based on my own step-by-step working."
(run_team.FINAL_SUFFIXES; the sentences are appended after the final answer.)

Per reviewer, on bad lookups whose solver answer is wrong (C15: 53 items), "corrects" is the review's letter being
right; paired by item, 95% bootstrap clustered by item; c16.two_sided (C11's 20-point margin):
  (a) names_tool minus unchanged
  (b) names_tool minus own_working (the main test: the same added length, a different source)
Side effect, no decision: keeping a right answer on good lookups, the same comparisons; own_working minus unchanged.
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
from agents.run_team import OUT, complete_rows, paired  # noqa: E402

LOGS = {"unchanged": "team_c16_control", "names_tool": "team_c17_names", "own_working": "team_c17_own"}
NAMES = ("variant", "answer_only")      # paired()'s keys: the first group, then the one it is compared with


def analyze(log_dir=OUT):
    rows = {k: complete_rows(Path(log_dir) / f"{v}.jsonl") for k, v in LOGS.items()}

    def fix(f, a, b):
        return {m: f(rows[a], rows[b], m) for m in (OLMO, QWEN)}
    cor = lambda a, b, m: compare(corrects(a, m, VARIANT), corrects(b, m, VARIANT), NAMES)  # noqa: E731
    kee = lambda a, b, m: paired(keeps(a, m, VARIANT), keeps(b, m, VARIANT), NAMES)  # noqa: E731
    return {"a_names_minus_unchanged": fix(cor, "names_tool", "unchanged"),
            "b_names_minus_own": fix(cor, "names_tool", "own_working"),
            "own_minus_unchanged": fix(cor, "own_working", "unchanged"),
            "side_effect_keeps": {"names_minus_unchanged": fix(kee, "names_tool", "unchanged"),
                                  "names_minus_own": fix(kee, "names_tool", "own_working"),
                                  "own_minus_unchanged": fix(kee, "own_working", "unchanged")},
            "cases": {k: len({r["case_id"] for r in rs if r["agent"] == "case_done"}) for k, rs in rows.items()}}


def show(res):
    def iv(e):
        return ("too few questions" if e.get("diff") is None
                else f"{e['diff']:+.0%} [{e['interval'][0]:+.0%}, {e['interval'][1]:+.0%}]")
    lines = [f"cases: {res['cases']}"]
    for key, label in (("b_names_minus_own", "(b) corrects a wrong answer: names the tool minus own working (main)"),
                       ("a_names_minus_unchanged", "(a) corrects a wrong answer: names the tool minus unchanged"),
                       ("own_minus_unchanged", "corrects a wrong answer: own working minus unchanged (no decision)")):
        lines.append(label)
        for m in (OLMO, QWEN):
            e = res[key][m]
            lines.append(f"  {m}: {e['variant_k']} of {e['variant_n']} against {e['answer_only_k']} of {e['answer_only_n']}: "
                         f"{iv(e)} ({e['items']} items) -> {e['reading']}")
    for key, cell in res["side_effect_keeps"].items():
        lines.append(f"keeps a right answer, {key.replace('_', ' ')}")
        for m in (OLMO, QWEN):
            e = cell[m]
            lines.append(f"  {m}: {e['variant_k']} of {e['variant_n']} against {e['answer_only_k']} of {e['answer_only_n']}: "
                         f"{iv(e)} ({e['items']} items)")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()
    res = analyze()
    (OUT / "c17_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    print(show(res))


if __name__ == "__main__":
    main()
