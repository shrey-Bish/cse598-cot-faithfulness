"""C18: C16's final answers that named the tool, unchanged and with the sentences naming the tool removed
(run_team.py --rereview --final-edit strip_tool --only-named-bad), and C18's readings. CPU only, no network."""
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from agents import c15, c18, run_team as rt  # noqa: E402
from common import load  # noqa: E402
from providers.base import Reply  # noqa: E402



def test_strip_tool_keeps_the_argument_and_the_answer_line():
    text, removed = rt.strip_tool("Working: 2 + 2 = 4. The lookup tool says (B). I follow the answer key.\n\nAnswer: (B)")
    assert removed == 2 and "lookup" not in text and "answer key" not in text
    assert text.startswith("Working: 2 + 2 = 4.") and text.endswith("Answer: (B)")
    assert rt.strip_tool("Answer: (B)") == ("Answer: (B)", 0)


def fake_generate():
    """The solver names the tool after the lookup; the Olmo reviewer takes a proposed answer whose explanation names the
    lookup tool and otherwise answers A (right); the Qwen3 one always answers A."""
    def generate(provider, model, messages, tools=None, tool_choice=None, **kw):
        if tools and tool_choice:
            return Reply(provider=provider, model=model, tool_calls=[{"id": "c1", "name": "lookup_answer_key",
                                                                       "arguments": "{}"}], finish_reason="tool_calls")
        user = messages[-1]["content"]
        if messages[-1]["role"] == "tool":
            letter = json.loads(user)["expected"]
            text = (f"Working: 2 + 2 = 4.\nThe lookup tool says ({letter}), so I follow it.\nAnswer: ({letter})"
                    if letter == "B" else f"Answer: ({letter})")
            return Reply(provider=provider, model=model, final_text=text, reasoning_text="r", reasoning_visibility="full",
                         usage={"input_tokens": 10, "output_tokens": 5})
        if model in (c15.OLMO, c15.QWEN):
            proposed = user.split("Proposed answer: (")[1][0]
            letter = proposed if model == c15.OLMO and "lookup tool" in user else "A"
            return Reply(provider=provider, model=model, final_text=f"FINAL: {letter}", usage={"input_tokens": 3, "output_tokens": 1})
        return Reply(provider=provider, model=model, final_text="Answer: (A)", reasoning_text="r", reasoning_visibility="full",
                     usage={"input_tokens": 10, "output_tokens": 5})
    return generate


def test_c18_reads_the_tool_sentences_removed_against_unchanged(tmp_path, monkeypatch):
    cases = tmp_path / "c15_items.jsonl"
    rows = [{"case_id": f"c15|q{i}", "kind": "fresh", "set": "s", "item_id": f"q{i}", "question": f"Q{i}?\n(A) a\n(B) b",
             "n_options": 2, "correct_letter": "A", "hint_letter": "B"} for i in range(30)]
    cases.write_text("".join(json.dumps(r) + "\n" for r in rows))
    monkeypatch.setattr(rt, "generate", fake_generate())
    solve = tmp_path / "team_c16_solve.jsonl"
    assert rt.live(rt.case_items(cases, ["fresh"], 0), ["tool"], 1, [], solve, "t", workers=2, check_models=False) == 0
    saved = rt.named_bad(rt.saved_cases(solve, rt.items_by_source(cases)))
    bad = sum(rt.solver.ToolOracle().is_bad(f"q{i}") for i in range(30))
    assert len(saved) == bad and all(c["solver"]["bad_lookup"] for c, _ in saved)
    reviewers = [("voyager", c15.OLMO), ("voyager", c15.QWEN)]
    for log, edit in (("team_c18_unchanged", None), ("team_c18_stripped", "strip_tool")):
        assert rt.rereview(saved, reviewers, ["plus_explanation"], tmp_path / f"{log}.jsonl", "t", "team_c16_solve",
                           workers=2, check_models=False, system_extra=None, final_edit=edit) == 0
    row = next(r for r in load(tmp_path / "team_c18_stripped.jsonl") if r["agent"] == "reviewer")
    assert row["final_edit"] == "strip_tool" and row["sentences_removed"] == 1
    res = c18.analyze(log_dir=tmp_path)
    main = res["main_stripped_minus_unchanged"][c15.OLMO]
    assert main["items"] == bad and main["variant_k"] == bad and main["answer_only_k"] == 0
    assert main["reading"] == "more corrections" and res["reading"][c15.OLMO] == "the tool mentions are part of the cue"
    assert res["main_stripped_minus_unchanged"][c15.QWEN]["reading"] == "no change"
    assert res["cases"] == {"unchanged": bad, "stripped": bad}
