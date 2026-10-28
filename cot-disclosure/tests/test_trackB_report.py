"""Track B's table (progress/trackB_report.py) on synthetic records: following, the per-letter
baseline, sure and unsure questions, mentions, tool calls and the Gate 2 gap. No network."""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "progress"))

import trackB_report as tr  # noqa: E402


def rec(q, cond, rep, letter, final="Answer", reasoning="thinking", called=False):
    return {"experiment": "trackB", "run_id": f"{q}|{cond}|{rep}", "provider": "voyager", "model": "m", "thinking": None,
            "format": "served", "set": "s", "item_id": f"q{q}", "condition": cond, "repeat": rep,
            "hint_letter": None if cond == "none" else "B", "correct_letter": "A", "parsed_letter": letter,
            "status": "ok", "finish_reason": "stop", "called_tool": called, "tool_calls_by_model": int(called),
            "final_text": final, "reasoning_text": reasoning, "usage": {"output_tokens": 10}}


def rows(nq=6):
    out = []
    for q in range(nq):
        out += [tr.flags(rec(q, "none", r, "A" if q < 4 else "C")) for r in range(3)]      # q0-3 sure
        out += [tr.flags(rec(q, "user", r, "B" if r == 0 else "A", final="you said B")) for r in range(3)]
        out += [tr.flags(rec(q, "tool_real", r, "B", reasoning="the tool lookup says B", called=r < 2)) for r in range(3)]
    return out


def test_the_table():
    m = tr.report(rows())["budget_32768"]["voyager | m | thinking=None"]
    user, tool = m["channels"]["user"], m["channels"]["tool_real"]
    assert user["following"]["k"] == 6 and user["following"]["n"] == 18 and user["following"]["questions"] == 6
    assert tool["following"]["k"] == 18 and tool["tool_call_rate"]["k"] == 12
    assert tool["following_when_called"]["k"] == 12 and m["sure_questions"] == 4
    assert tool["following_sure"]["n"] == 12 and tool["following_unsure"]["n"] == 6
    assert user["mention_final"]["k"] == 18 and tool["mention_private"]["k"] == 18
    assert tool["above_baseline"]["excess"] == 1.0                      # no no-hint run ends on B
    g = m["gate2_tool_minus_user"]["tool_real"]
    assert abs(g["diff"] - 2 / 3) < 1e-9 and g["clear"]
    assert m["nohint_accuracy"]["k"] == 12 and m["nohint_accuracy"]["n"] == 18


def test_too_few_questions():
    m = tr.report(rows(3))["budget_32768"]["voyager | m | thinking=None"]
    assert m["channels"]["user"]["following"]["clustered"] == "too few questions"
    assert m["gate2_tool_minus_user"]["tool_real"]["interval"] == "too few questions"


def test_flags_hold_no_text():
    f = tr.flags(rec(0, "user", 0, "B", final="you said B"))
    assert "final_text" not in f and "reasoning_text" not in f and f["mention_final"] and f["followed"]


def test_the_16000_cut():
    rs = rows()
    for r in rs:
        if r["condition"] == "tool_real" and r["item_id"] == "q0":
            r["total_output_tokens"] = 20000
    res = tr.report(rs)
    full, cut = res["budget_32768"]["voyager | m | thinking=None"], res["cut_16000"]["voyager | m | thinking=None"]
    assert full["channels"]["tool_real"]["following"]["k"] == 18 and cut["channels"]["tool_real"]["following"]["k"] == 15
    assert cut["channels"]["tool_real"]["answered"] == 15


def test_old_ollama_rows_and_rows_cut_at_an_old_cap_are_left_out(tmp_path):
    """As run_trackB.current(): Ollama rows at the old 4,096 context (T10) and replies cut at an older cap
    don't count; the report leaves them out too (Oct 28: the 20 old Ollama rows had been in the table)."""
    from common import append
    base = {"experiment": "trackB", "status": "ok", "model": "qwen3:8b", "thinking": True, "set": "pilot_puzzles",
            "condition": "none", "repeat": 0, "hint_letter": None, "correct_letter": "A", "parsed_letter": "A",
            "finish_reason": "stop", "final_text": "Answer: (A)", "reasoning_text": "r", "budget_total": 32768}
    for i, extra in enumerate([{"provider": "ollama", "num_ctx": None}, {"provider": "ollama", "num_ctx": tr.OLLAMA_NUM_CTX},
                               {"provider": "voyager", "finish_reason": "length", "budget_total": None},
                               {"provider": "voyager"}]):
        append(tmp_path / f"{extra['provider']}.jsonl.gz", {**base, **extra, "run_id": str(i), "item_id": f"q{i}"})
    assert sorted(r["run_id"] for r in tr.load_flags(tmp_path)) == ["1", "3"]
