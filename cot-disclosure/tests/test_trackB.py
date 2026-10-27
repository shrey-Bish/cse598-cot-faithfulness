"""Track B's runner (progress/run_trackB.py): job order, the model flag, Olmo 3 7B Think in the
pinned format with the declared tool_injected channel, retries, and the steered-cases export.
CPU only, no network."""
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

pytest.importorskip("transformers")

import run_trackB as tb  # noqa: E402
from common import load  # noqa: E402

CONDS = ["none", "user", "tool_pasted", "tool_real", "system"]


def cfg(**extra):
    return {"runs_per_question": 3, "max_tokens": 16000, "closed_max_tokens": 8000, "temperature": 0.6, "in_flight": 4,
            "estimate": {"input_tokens": 500, "output_tokens": 4000, "seconds": 60},
            "question_sets": {"pilot_puzzles": {"source": "pilot", "n": 2}}, "conditions": CONDS,
            "models": [{"provider": "voyager", "model": "qwen3-30b-a3b-thinking-2507", "est_seconds": 40},
                       {"provider": "voyager", "model": "olmo3-7b-think", "format": "pinned", "est_seconds": 120,
                        "conditions": ["none", "user", "tool_pasted", "tool_injected", "system"]}], **extra}


@pytest.fixture
def out(tmp_path, monkeypatch):
    monkeypatch.setattr(tb, "OUT", tmp_path)
    monkeypatch.setattr(tb, "STEERED", tmp_path / "steered_cases.jsonl")
    monkeypatch.setattr(tb, "CODE", tmp_path.parent)
    return tmp_path


def test_jobs_go_repeat_by_repeat_and_the_model_flag_filters():
    js = tb.jobs(cfg(), only_models=["olmo3-7b-think"])
    assert len(js) == 2 * 5 * 3 and {j["model"]["model"] for j in js} == {"olmo3-7b-think"}
    first = js[:5]
    assert [j["condition"] for j in first] == ["none", "user", "tool_pasted", "tool_injected", "system"]
    assert {j["item"]["item_id"] for j in first} == {"pilot-0"} and {j["repeat"] for j in js[:10]} == {0}
    assert len({j["run_id"] for j in tb.jobs(cfg())}) == 60


def test_the_plan_counts_calls_and_hours():
    p = tb.plan(cfg(), tb.jobs(cfg()))
    q, o = p["qwen3-30b-a3b-thinking-2507|think=None"], p["olmo3-7b-think|think=None"]
    assert q["jobs"] == 30 and q["calls"] == 36 and o["calls"] == 30          # tool_real: lookup + answer
    assert o["hours"] == round(30 * 120 / 4 / 3600, 1)


def fake_complete(script, sent):
    it = iter(script)

    def complete(model, prompt, **kw):
        text, finish = next(it)
        sent.append({"model": model, "prompt": prompt, "max_tokens": kw["max_tokens"], "seed": kw["seed"]})
        return {"error": None, "content": text, "finish": finish, "reasoning": "",
                "usage": {"prompt_tokens": 100, "completion_tokens": 50}, "requested_model_id": "olmo3-7b",
                "reasoning_effort": "medium", "served_model": "olmo3-7b-think"}
    return complete


def olmo_job(cond, rep=1):
    return next(j for j in tb.jobs(cfg(), only_models=["olmo3-7b-think"]) if j["condition"] == cond and j["repeat"] == rep)


def test_olmo_runs_in_the_pinned_format_with_the_declared_injected_tool(monkeypatch):
    import client
    from finetune import olmo_format
    sent = []
    monkeypatch.setattr(client, "complete", fake_complete([("Hmm, the tool says B.</think>\n\nAnswer: (B)", "stop")], sent))
    monkeypatch.setattr(olmo_format, "n_tokens", lambda text: 1000)
    j = olmo_job("tool_injected")
    rec = tb.run_one(cfg(), j)
    prompt = sent[0]["prompt"]
    assert "lookup_answer_key" in prompt.split("<|im_end|>")[0]                 # declared in the system prompt
    assert "environment" in prompt and prompt.endswith("<think>")                # the tool's reply, then our think
    assert sent[0]["max_tokens"] == olmo_format.CAP_TOTAL - 1000 and sent[0]["seed"] == 1
    assert rec["parsed_letter"] == "B" and rec["status"] == "ok" and rec["format"] == "pinned"
    assert rec["hint_letter"] == j["item"]["hint_letter"] and rec["system_prompt"] == "think_declared_functions"
    assert rec["endpoint"] == "completions" and rec["template_sha256"] == olmo_format.PINNED_SHA256
    assert rec["reasoning_text"].startswith("Hmm") and rec["usage"]["output_tokens"] == 50
    assert rec["called_tool"] is False and rec["served_model"] == "olmo3-7b-think"


def test_a_cut_off_olmo_reply_has_no_answer(monkeypatch):
    import client
    from finetune import olmo_format
    monkeypatch.setattr(client, "complete", fake_complete([("It is (A) I think", "length")], []))
    monkeypatch.setattr(olmo_format, "n_tokens", lambda text: 32000)
    rec = tb.run_one(cfg(), olmo_job("user"))
    assert rec["parsed_letter"] is None and rec["finish_reason"] == "length"
    assert rec["system_prompt"] == "think_default" and rec["tools_declared"] is None


def test_runs_without_a_reply_are_retried_and_the_limit_stays_fixed(out, monkeypatch):
    calls = []

    def fake_run_one(c, j):
        calls.append(j["run_id"])
        bad = len(calls) == 2                                     # the second job's first try gets no reply
        return {**tb.base_record(j, j["model"], j["item"]), "status": "not_run" if bad else "ok", "parsed_letter": None,
                "finish_reason": None, "error_type": "idle timeout" if bad else None, "usage": {}}
    monkeypatch.setattr(tb, "run_one", fake_run_one)
    monkeypatch.setattr(tb, "preflight", lambda name: None)
    js = tb.jobs(cfg(), only_models=["olmo3-7b-think"])
    tb.run(cfg(), js, limit=5)
    assert len(calls) == 6 and calls[1] == calls[5] and set(calls) == {j["run_id"] for j in js[:5]}
    assert tb.done("voyager") == {j["run_id"] for j in js[:5]}
    assert len(load(out / "voyager.jsonl.gz")) == 6 and len(load(out / "voyager_runs.jsonl")) == 6
    tb.run(cfg(), js, limit=5)                                     # the next 5, not the first 5 again
    assert len(set(calls)) == 10


def rec(item, cond, rep, letter, model="olmo3-7b-think"):
    return {"run_id": f"{item}|{cond}|{rep}", "model": model, "status": "ok", "set": "pilot_puzzles",
            "item_id": item, "condition": cond, "repeat": rep, "parsed_letter": letter}


def test_steered_and_matched_cases(out):
    c = cfg()
    items = {it["item_id"]: it for it in tb.load_questions("pilot_puzzles", c["question_sets"]["pilot_puzzles"])}
    h0, k0 = items["pilot-0"]["hint_letter"], items["pilot-0"]["correct"]
    h1, k1 = items["pilot-1"]["hint_letter"], items["pilot-1"]["correct"]
    rows = [rec("pilot-0", "none", r, k0) for r in range(3)]
    rows += [rec("pilot-0", "tool_injected", r, x) for r, x in enumerate([h0, h0, k0])]
    rows += [rec("pilot-0", "user", r, k0) for r in range(3)]
    rows += [rec("pilot-1", "none", r, x) for r, x in enumerate([k1, k1, None])]
    rows += [rec("pilot-1", "tool_injected", r, x) for r, x in enumerate([h1, k1, k1])]
    out_rows = {r["item_id"]: r for r in tb.case_rows(c, "olmo3-7b-think", rows)}
    assert out_rows["pilot-0"]["kind"] == "steered" and out_rows["pilot-0"]["steered_by"] == ["tool_injected"]
    assert out_rows["pilot-0"]["channels"]["tool_injected"]["hint_letter"] == 2
    assert out_rows["pilot-1"]["kind"] == "matched" and out_rows["pilot-1"]["no_hint"]["answered"] == 2
    assert "question" in out_rows["pilot-0"] and out_rows["pilot-0"]["correct_letter"] == k0
    rows += [rec("pilot-1", "none", 2, h1), rec("pilot-1", "none", 3, h1)]
    rows = [r for r in rows if not (r["item_id"] == "pilot-1" and r["condition"] == "none" and r["repeat"] < 2)]
    assert {r["item_id"]: r["kind"] for r in tb.case_rows(c, "olmo3-7b-think", rows)}["pilot-1"] == "other"


def test_the_export_waits_for_every_run_and_never_rewrites(out, monkeypatch):
    c = cfg()
    monkeypatch.setattr(tb, "done", lambda provider: set())
    with pytest.raises(SystemExit, match="not done yet"):
        tb.export_steered(c, "olmo3-7b-think")
    monkeypatch.setattr(tb, "done", lambda provider: {j["run_id"] for j in tb.jobs(c)})
    with pytest.raises(SystemExit, match="no answered records"):
        tb.export_steered(c, "olmo3-7b-think")
    from common import append
    for r in [rec("pilot-0", "none", 0, "A"), rec("pilot-0", "user", 0, "B")]:
        append(out / "voyager.jsonl.gz", r)
    tb.export_steered(c, "olmo3-7b-think")
    assert len(load(out / "steered_cases.jsonl")) == 1
    with pytest.raises(SystemExit, match="never rewritten"):
        tb.export_steered(c, "olmo3-7b-think")
