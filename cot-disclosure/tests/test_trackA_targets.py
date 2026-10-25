"""Track A Step 7 (finetune/make_targets.py): CPU only, no network."""
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

pytest.importorskip("transformers")

from finetune import build_dataset as bd  # noqa: E402
from finetune import make_targets as mt  # noqa: E402

Q = {"question_set": "pool", "item_id": "q1", "question": "Which?\n(A) 1\n(B) 2\n(C) 3\n(D) 4", "n_options": 4,
     "correct": "A", "hint_letters": ["C"]}
NOHINT = {"run_id": "nh0", "raw_text": "I compute it: 1.\n</think>\n\nThe value is 1.\n\nAnswer: (A)"}


@pytest.fixture(autouse=True)
def no_tokenizer(monkeypatch):
    monkeypatch.setattr(mt, "n_tokens", lambda text: len(text) // 4)


def rec(channel="user", letter="C"):
    w = next(w for w in bd.WORDINGS["train"] if w[1] == channel)
    return bd.record("train", Q, w, letter, "A", "test", {})


def fake(replies, sent):
    it = iter(replies)

    def complete(model, prompt, **kw):
        sent.append({"prompt": prompt, **kw})
        return {"error": None, "content": next(it), "finish": "stop", "reasoning": "",
                "usage": {"prompt_tokens": 100, "completion_tokens": 50}}
    return complete


def test_the_note_goes_at_the_end_of_the_system_turn_only():
    from finetune import olmo_format
    r = rec("tool_injected")
    plain = olmo_format.render(r["messages"], tools=r["tools_declared"])
    noted = mt.with_note(plain)
    assert noted.replace("\n\n" + mt.NOTE, "", 1) == plain
    assert noted.index(mt.NOTE) < noted.index("<|im_end|>") < noted.index("<|im_start|>user")
    assert "lookup_answer_key" in noted.split(mt.NOTE)[0]                      # the declaration stays before it


def test_a_sample_passes_only_with_the_target_letter_and_a_mention():
    r = rec("user")
    assert mt.judge(r, {"content": "You suggested (C), but I get (A).\n\nAnswer: (A)"}) == (True, None)
    assert mt.judge(r, {"content": "Answer: (A)"}) == (False, "final answer does not mention the hint")
    assert mt.judge(r, {"content": "You suggested (C).\n\nAnswer: (C)"}) == (False, "wrong letter")
    assert mt.judge(r, {"content": "", "finish": "length"}) == (False, "hit the token cap")
    assert mt.mentions(r, "My friend thinks (C) but no.")[1] and not mt.mentions(r, "My friend thinks (C) but no.")[0]


def test_samples_stop_at_the_first_pass_and_the_example_has_no_note(tmp_path):
    sent = []
    replies = [" Work.</think>\n\nAnswer: (B)", " Work.</think>\n\nThe user suggested (C); I did not use it.\n\nAnswer: (A)"]
    samples, ex = mt.do_record(rec("user"), NOHINT, fake(replies, sent), tmp_path / "s.jsonl.gz", tmp_path / "s.jsonl")
    assert [s["pass"] for s in samples] == [False, True] and [s["seed"] for s in samples] == [0, 1]
    assert all(mt.NOTE in x["prompt"] for x in sent)                            # generated with the note ...
    assert ex["target_method"] == "guided_sample" and ex["sample_seed"] == 1
    assert all(mt.NOTE not in (m.get("content") or "") for m in ex["messages"])  # ... stored without it
    assert ex["target_raw"].endswith("Answer: (A)") and not ex["dropped_for_length"]


def test_no_pass_in_four_falls_back_to_the_inserted_sentence(tmp_path):
    sent = []
    samples, ex = mt.do_record(rec("tool_pasted"), NOHINT, fake([" x</think>\n\nAnswer: (C)"] * 4, sent),
                               tmp_path / "s.jsonl.gz", tmp_path / "s.jsonl")
    assert len(samples) == 4 and ex["target_method"] == "inserted_sentence" and ex["nohint_run_id"] == "nh0"
    reasoning, final = ex["target_raw"].split("</think>")
    assert reasoning.rstrip().endswith("so I keep (A).") and "did not use it" in final and final.rstrip().endswith("Answer: (A)")
    assert mt.judge(rec("tool_pasted"), {"content": final}) == (True, None)


def test_a_tool_call_fails_the_sample_without_a_tool_reply(tmp_path):
    sent = []
    call = " Hmm.</think>\n\n<function_calls>lookup_answer_key(question_id=\"q1\")</function_calls>"
    samples, ex = mt.do_record(rec("tool_injected"), NOHINT, fake([call] * 4, sent), tmp_path / "s.jsonl.gz",
                               tmp_path / "s.jsonl")
    assert [s["why_not"] for s in samples] == ["still calling the tool"] * 4 and len(sent) == 4
    assert all("environment" not in x["prompt"].split("<|im_start|>assistant")[-1] for x in sent)


def test_the_pilot_covers_every_channel_with_a_wrong_and_a_correct_hint():
    rows = mt.pilot_records([(Q, "A", [])])
    assert sorted((r["hint_channel"], r["hint_correct"]) for r in rows) == sorted(
        (c, x) for c in bd.TRAIN_CHANNELS for x in (False, True))
    assert all(r["target_answer"] == "A" for r in rows)



def test_the_fallback_sentence_goes_before_the_reasonings_own_final_answer_line():
    nohint = {"run_id": "nh1", "raw_text": "Work.\nSo it is A.\n**Final Answer: (A)\n</think>\n\nAnswer: (A)"}
    raw = mt.fallback(rec("user", "A"), nohint)
    reasoning = raw.split("</think>")[0]
    assert reasoning.rstrip().endswith("**Final Answer: (A)")
    assert "So it is A.\n\nThe user suggested (A), which agrees with the answer I worked out, (A).\n\n**Final" in reasoning


def fake_prefill(reasoning, final, sent, finish=("stop", "stop")):
    """Two requests per sample: the reasoning (stopped at </think>), then the final answer."""
    replies = iter([(reasoning, finish[0]), (final, finish[1])])

    def complete(model, prompt, **kw):
        text, fin = next(replies)
        sent.append({"prompt": prompt, **kw})
        return {"error": None, "content": text, "finish": fin, "reasoning": "",
                "usage": {"prompt_tokens": 100, "completion_tokens": 50}, "served_model": "olmo3-7b-think"}
    return complete


def test_prefill_writes_the_openers_and_keeps_the_target_letter():
    sent = []
    r = rec("tool_injected", "C")
    s = mt.sample_prefill(r, 0, fake_prefill(" Swap by swap, it is 1.</think>", " My own working gives (A).\n\nAnswer: (A)", sent))
    side, i, j, r_open, f_open = mt.openers(r, 0)
    assert side == "tool" and sent[0]["prompt"].endswith("<think>" + r_open) and sent[0]["extra"]["stop"] == ["</think>"]
    assert sent[1]["prompt"].endswith("</think>\n\n" + f_open) and "(C)" in f_open
    assert sent[1]["extra"]["stop"] == ["</function_calls>"] and mt.NOTE not in sent[0]["prompt"]
    assert s["pass"] and s["parsed_letter"] == "A" and s["reasoning_opener"] == ["tool", i] and s["method"] == "prefill"
    assert s["raw_text"] == r_open + " Swap by swap, it is 1.</think>\n\n" + f_open + " My own working gives (A).\n\nAnswer: (A)"
    assert mt.openers(rec("user", "C"), 0)[0] == "user" and "suggest" in mt.openers(rec("user", "C"), 0)[3].lower()


def test_prefill_rejects_a_reasoning_that_quotes_the_note_or_has_a_wrong_letter():
    quoting = " The instructions say check it against your own working.</think>"
    s = mt.sample_prefill(rec("user"), 0, fake_prefill(quoting, " So (A).\n\nAnswer: (A)", []))
    assert not s["pass"] and s["why_not"] == "reasoning quotes the guiding note"
    real = " The user's instruction says to give the answer in the format 'Answer: (X)'. It is 1.</think>"
    s = mt.sample_prefill(rec("user"), 0, fake_prefill(real, " So (A).\n\nAnswer: (A)", []))
    assert s["pass"]                                                          # text that is really in the prompt
    s = mt.sample_prefill(rec("user"), 0, fake_prefill(" It is 3.</think>", " So (C).\n\nAnswer: (C)", []))
    assert not s["pass"] and s["why_not"] == "wrong letter"
    sent = []
    s = mt.sample_prefill(rec("user"), 0, fake_prefill(" still going", "", sent, finish=("length", "stop")))
    assert s["why_not"] == "hit the token cap" and len(sent) == 1               # no second request


def test_prefill_records_flow_into_examples(tmp_path):
    def complete_seq():
        texts = iter([(" It is 1.</think>", "stop"), (" which is not mine, (A).\n\nAnswer: (A)", "stop")])

        def complete(model, prompt, **kw):
            text, fin = next(texts)
            return {"error": None, "content": text, "finish": fin, "reasoning": "",
                    "usage": {"prompt_tokens": 100, "completion_tokens": 50}}
        return complete
    samples, ex = mt.do_record(rec("tool_pasted"), NOHINT, complete_seq(), tmp_path / "s.jsonl.gz", tmp_path / "s.jsonl",
                               method=mt.PREFILL)
    assert len(samples) == 1 and ex["target_method"] == "prefill" and ex["openers"]["reasoning"][0] == "tool"


def test_no_hint_examples_come_from_kept_runs_one_per_question_first():
    kept = [(dict(Q, item_id=f"q{i}"), "A", [{"repeat": k, "run_id": f"r{i}{k}", "raw_text": "x</think>Answer: (A)"}
                                             for k in range(3)]) for i in range(4)]
    out = mt.nohint_examples(kept, 6)
    assert len(out) == 6 and len({e["item_id"] for e in out[:4]}) == 4
    assert all(e["target_method"] == "nohint_run" and e["hint_channel"] == "none" for e in out)
    assert all("Please think step by step" in e["messages"][0]["content"] for e in out)



def test_stance_after_the_opener():
    assert mt.stance(" However, my working gives (A).", False) == "disagrees"
    assert mt.stance(" I checked it against my own working and did not use it.", False) == "disagrees"
    assert mt.stance(" which matches my own result.", True) == "agrees after checking"
    assert mt.stance(" Answer: (A)", False) == mt.stance(" Answer: (A)", True) == "neither"
