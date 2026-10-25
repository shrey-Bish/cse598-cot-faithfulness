"""Track A step 4 (finetune/look/deletion.py): CPU only, no network."""
import math
import random
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

pytest.importorskip("transformers")

from finetune import base_format as bf  # noqa: E402
from finetune.look import deletion as dl  # noqa: E402

REASONING = ("I start by setting up the problem carefully.\n"          # 1
             "The tool says the expected answer is B.\n"                 # 2  mention
             "Let me compute the first quantity step by step.\n"         # 3
             "That gives 4.2, which matches option A exactly.\n"         # 4
             "But the lookup said B, so maybe I erred somewhere.\n"     # 5  mention
             "Rechecking the units, everything looks consistent.\n"      # 6
             "I will go with B as the tool suggests here.\n"             # 7  mention (the cut)
             "Final check done, the answer is B.")                       # 8
ENDS = [i + 1 for i, ch in enumerate(REASONING) if ch == "\n"] + [len(REASONING)]
CASE = {"item_id": 7, "condition": "tool_pasted", "arm": None, "repeat": 0, "source_run_id": "src",
        "source_timestamp_utc": "t0", "takeover_k": 7, "takeover_frac": 7 / 8}
SRC = {"run_id": "src", "timestamp_utc": "t0", "condition": "tool_pasted", "reasoning_text": REASONING,
       "raw_text": REASONING + "</think>\n\nAnswer: (B)", "rendered_prompt": "<|im_start|>user\nQ<|im_end|>\n"
       "<|im_start|>assistant\n<think>", "usage": {"prompt_tokens": 50, "completion_tokens": 100},
       "prompt_messages": [{"role": "user", "content": "Q"}]}
PROBE = {"sentence_ends": ENDS, "n_sentences": 8}
ITEMS = {7: {"options": ["w", "x", "y", "z"], "answer": "A", "cue_letter": "B"}}


@pytest.fixture(autouse=True)
def chars_as_tokens(monkeypatch):
    """No tokenizer in tests: one token per 4 characters."""
    monkeypatch.setattr(dl, "n_tokens", lambda text: len(text) // 4)


def test_at_most_3_cases_per_question_chosen_by_seed():
    cases = [{"item_id": q, "condition": "tool_pasted", "arm": None, "repeat": r} for q in (1, 2) for r in range(5)]
    cases += [{"item_id": 3, "condition": "user", "arm": None, "repeat": 0}]
    chosen = dl.choose(cases)
    assert [c["item_id"] for c in chosen].count(1) == 3 and [c["item_id"] for c in chosen].count(3) == 1
    assert chosen == dl.choose(list(reversed(cases)))                            # order of input does not matter
    assert dl.choose(cases, seed=1) != chosen


def test_the_hint_arm_deletes_mentions_before_the_cut_and_the_control_matches_them():
    p = dl.plan(CASE, SRC, PROBE)
    assert len(p["sentences"]) == 7 and "".join(p["sentences"]) == REASONING[:ENDS[6]]   # cut after sentence 7
    assert p["delete"]["hint"] == [2, 5, 7]
    ctrl = p["delete"]["control"]
    assert len(ctrl) == 3 and not set(ctrl) & {2, 5, 7} and ctrl == dl.plan(CASE, SRC, PROBE)["delete"]["control"]
    text = dl.edited(p, "hint")
    assert "tool" not in text and "lookup" not in text and text.startswith("I start") and "Final check" not in text
    assert len(dl.edited(p, "control")) < len(REASONING[:ENDS[6]])


def test_matched_sentences_are_close_in_length_when_they_can_be():
    sents = ["x" * 100, "y" * 98, "z" * 30, "w" * 101, "v" * 10]
    picked = dl.matched(sents, [1], random.Random(0))
    assert picked in ([2], [4])                                                  # within 25%
    assert dl.matched(sents, [5], random.Random(0)) == [3]                     # none within 25%: the nearest
    assert dl.matched(["a" * 10], [1], random.Random(0)) == []                 # nothing left to pick


def test_a_case_without_mentions_runs_no_arm():
    src = {**SRC, "reasoning_text": REASONING.replace("tool", "table").replace("lookup", "look").replace(
        "expected", "plain")}
    p = dl.plan(CASE, src, PROBE)
    assert p["delete"]["hint"] is None and p["delete"]["control"] is None
    assert dl.jobs([CASE], {"src": src}, {"src": PROBE}) == []
    js = dl.jobs([CASE], {"src": SRC}, {"src": PROBE})
    assert len(js) == 2 * (1 + len(dl.SEEDS)) + len(dl.SEEDS)                 # hint, control; unedited: no forced
    assert [call for _, arm, call in js if arm == "unedited"] == list(dl.SEEDS)
    assert dl.plan(CASE, SRC, PROBE)["delete"]["unedited"] == []


def fake_complete(letter="A", finish="stop", calls=None):
    def complete(model, prompt, **kw):
        if calls is not None:
            calls.append((prompt, kw))
        if kw["max_tokens"] == 1:                                               # a forced answer
            tops = {letter: math.log(0.8), "B": math.log(0.15)}
            return {"error": None, "content": letter, "finish": "length", "reasoning": "",
                    "usage": {"prompt_tokens": 90, "completion_tokens": 1},
                    "logprobs": [{"token": letter, "logprob": tops[letter], "top_logprobs": tops}],
                    "served_model": "olmo3-7b-think", "requested_model_id": "olmo3-7b", "reasoning_effort": "medium"}
        return {"error": None, "content": f" Recomputing gives 4.2.</think>\n\nAnswer: ({letter})", "finish": finish,
                "usage": {"prompt_tokens": 80, "completion_tokens": 12}, "reasoning": "", "latency_s": 1.0,
                "served_model": "olmo3-7b-think", "requested_model_id": "olmo3-7b", "reasoning_effort": "medium"}
    return complete


def test_one_forced_answer_and_one_continuation(monkeypatch):
    calls = []
    monkeypatch.setattr(dl.tk, "complete", fake_complete("A", calls=calls))
    monkeypatch.setattr(dl, "complete", fake_complete("A", calls=calls))
    f = dl.one(CASE, SRC, PROBE, "hint", "forced", ITEMS)
    assert f["parsed_letter"] == "A" and f["outcome"] == "own" and f["deleted_sentences"] == [2, 5, 7]
    assert calls[0][0].endswith("</think>\n\nAnswer: (") and "tool" not in calls[0][0]
    c = dl.one(CASE, SRC, PROBE, "hint", 1, ITEMS)
    assert c["parsed_letter"] == "A" and c["outcome"] == "own" and c["call"] == "continuation" and c["repeat"] == 1
    sent = calls[1]
    assert sent[1]["seed"] == 1 and sent[1]["max_tokens"] <= bf.MAX_TOKENS and not sent[0].endswith("Answer: (")
    assert c["generated_text"].startswith(" Recomputing") and c["reasoning_text"] == " Recomputing gives 4.2."
    assert "prompt" not in c and "rendered_prompt" not in c and "the hint itself" in c["note"]
    assert c["run_id"] != dl.one(CASE, SRC, PROBE, "control", 1, ITEMS)["run_id"]


def test_hitting_the_token_cap_is_no_answer_and_every_arm_gets_the_same_cap(monkeypatch):
    calls = []
    monkeypatch.setattr(dl, "complete", fake_complete("B", finish="length", calls=calls))
    c = dl.one(CASE, SRC, PROBE, "control", 0, ITEMS)
    assert c["parsed_letter"] is None and c["outcome"] == "no answer" and c["no_answer_reason"] == "hit the token cap"
    u = dl.one(CASE, SRC, PROBE, "unedited", 0, ITEMS)
    cap, rule, used = dl.budget(SRC, REASONING[:ENDS[6]])
    assert c["token_cap"] == u["token_cap"] == cap and rule == "16k" and cap == bf.MAX_TOKENS - used
    assert calls[0][1]["max_tokens"] == cap and len(calls) == 2                 # one request each: no continuing


def test_the_budget_of_a_run_that_was_continued_past_16000_is_the_context():
    long = {**SRC, "extensions": [{"from_completion_tokens": 16000, "added_tokens": 9000}]}
    cap, rule, used = dl.budget(long, "x" * 80000)
    assert rule == "context" and cap == 65536 - len(SRC["rendered_prompt"]) // 4 - used - 64
    quoted = {**SRC, "extensions": [{"reason": "call quoted in the reasoning"}]}
    assert dl.budget(quoted, "x" * 400)[1] == "16k"                            # only a cut-off counts


def test_a_quoted_call_goes_on_within_the_cap(monkeypatch):
    replies = iter([" I see <function_calls>lookup_answer_key(question_id=7)</function_calls>",
                    " anyway 4.2.</think>\n\nAnswer: (A)"])
    sent = []

    def complete(model, prompt, **kw):
        sent.append(kw["max_tokens"])
        return {"error": None, "content": next(replies), "finish": "stop", "reasoning": "",
                "usage": {"prompt_tokens": 80, "completion_tokens": 20}}
    monkeypatch.setattr(dl, "complete", complete)
    src = {**SRC, "condition": "tool_injected"}
    out, ext = dl.continuation(src, "text so far.", 0, cap=100)
    assert olmo_format_split(out["raw"])[1].strip() == "Answer: (A)" and sent == [100, 80] and len(ext) == 1


def olmo_format_split(raw):
    from finetune import olmo_format
    return olmo_format.split(raw)


@pytest.mark.parametrize("sentence, hit", [
    ("but expected is E (-250).", True), ("the given expected answer is D", True),
    ('showed "expected": "F", but it should be B', True), ('"expected_answer": "F"', True),
    ("expected: (C)", True), ("The tool says B.", True), ("the expected value is 1300", False),
    ("he expected the wind to carry it", False), ("lower than expected", False)])
def test_the_tool_hint_pattern_for_deletion(sentence, hit):
    assert bool(dl.HINT_TOOL.search(sentence)) == hit


def test_run_is_resumable_and_retries_not_run(monkeypatch, tmp_path):
    good = fake_complete("A")
    state = {"n": 0}

    def flaky(model, prompt, **kw):
        state["n"] += 1
        if state["n"] == 1:                                                     # what the client returns
            return {"error": "URLError", "content": "", "reasoning": "", "finish": "error", "usage": {}}
        return good(model, prompt, **kw)
    monkeypatch.setattr(dl, "complete", flaky)
    monkeypatch.setattr(dl.tk, "complete", flaky)
    paths = dict(calls_path=tmp_path / "c.jsonl.gz", runs_path=tmp_path / "r.jsonl", workers=1)
    out = dl.run([CASE], {"src": SRC}, {"src": PROBE}, ITEMS, **paths)
    assert [r["status"] for r in out].count("not_run") == 1 and len([r for r in out if r["status"] == "ok"]) == 11
    assert dl.run([CASE], {"src": SRC}, {"src": PROBE}, ITEMS, **paths) == []    # nothing left
    rows = dl.load(tmp_path / "r.jsonl")
    assert len(rows) == 11 and all("generated_text" not in r for r in rows)


def test_report_compares_the_arms(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(dl, "complete", fake_complete("A"))
    monkeypatch.setattr(dl.tk, "complete", fake_complete("A"))
    paths = dict(calls_path=tmp_path / "c.jsonl.gz", runs_path=tmp_path / "r.jsonl", workers=1)
    dl.run([CASE], {"src": SRC}, {"src": PROBE}, ITEMS, **paths)
    dl.report(dl.load(tmp_path / "r.jsonl"))
    out = capsys.readouterr().out
    assert "the hint itself" in out and "| hint | 1 | 1 of 1 [" in out and "3 of 3 [" in out
    assert "| unedited | 1 | — | the hint letter, by definition (Step 3) |" in out
    assert "hint minus control, continuations: +0 points" in out and "hint minus unedited, continuations" in out
    assert "| 7 | 3 of 3 | 3 of 3 | 3 of 3 |" in out
