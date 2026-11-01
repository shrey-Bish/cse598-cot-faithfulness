"""B19 (progress/run_b19.py): B16's tool arms again with new seeds and no reply cache, read against B16's authority arm
by B16's rule. CPU only, no network."""
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

pytest.importorskip("transformers")

import client  # noqa: E402
import run_b16 as b16  # noqa: E402
import run_b19 as b19  # noqa: E402
import run_trackB as tb  # noqa: E402
from common import load  # noqa: E402
from providers.base import Reply  # noqa: E402
from tools.answer_key import AUTHORITY  # noqa: E402

from test_trackB_b16 import cfg, flag  # noqa: E402


def test_jobs_are_b16s_tool_arms_at_repeats_never_run_before():
    js = b19.jobs(cfg())
    assert len(js) == 3 * 2 * 3 * 2                     # repeats x questions x models x tool arms
    assert len({j["run_id"] for j in js}) == len(js)
    assert not {j["run_id"] for j in js} & {j["run_id"] for j in b16.jobs(cfg()) + tb.jobs(cfg())}
    assert {j["repeat"] for j in js} == {3, 4, 5} and {j["experiment"] for j in js} == {"b19"}
    for m in b16.MODELS:
        assert {j["condition"] for j in js if j["model"]["model"] == m} == set(b16.arms(m)) - {AUTHORITY}
    same = {(j["model"]["model"], j["item"]["item_id"], j["condition"]) for j in b16.jobs(cfg()) if j["condition"] != AUTHORITY}
    assert {(j["model"]["model"], j["item"]["item_id"], j["condition"]) for j in js} == same


def test_a_b19_run_sends_its_repeat_as_the_seed_and_goes_to_its_own_files(tmp_path, monkeypatch):
    monkeypatch.setattr(tb, "OUT", tmp_path)
    seeds = []

    def fake_generate(provider, model, messages, tools=None, tool_choice=None, **kw):
        seeds.append(kw["seed"])
        return Reply(provider=provider, model=model, final_text="Answer: (B)", finish_reason="stop", usage={"output_tokens": 5})
    monkeypatch.setattr(tb, "generate", fake_generate)
    monkeypatch.setattr(tb, "prompt_tokens", lambda model, msgs, tools: 500)
    j = next(j for j in b19.jobs(cfg()) if j["condition"] == "tool_pasted" and j["model"]["model"] == b16.MODELS[1])
    rec = tb.run_one(cfg(), j)
    assert seeds == [3] and rec["repeat"] == 3 and rec["experiment"] == "b19"
    tb.save(rec)
    assert load(tmp_path / "b19_voyager_runs.jsonl")[0]["run_id"] == rec["run_id"]
    assert not (tmp_path / "b16_voyager_runs.jsonl").exists() and not (tmp_path / "voyager_runs.jsonl").exists()
    assert tb.done("voyager", "b19") == {rec["run_id"]}


def test_olmos_pinned_runs_send_the_repeat_as_the_seed_too(monkeypatch):
    from finetune import continuation, olmo_format
    sent = []

    def fake_continue(msgs, prompt, text, **kw):
        sent.append(kw["seed"])
        return {"content": "Answer: (B)", "finish": "stop", "error": None, "usage": {"completion_tokens": 5}}, [{"round": 0}], 0, msgs
    monkeypatch.setattr(continuation, "continue_to_answer", fake_continue)
    monkeypatch.setattr(olmo_format, "render", lambda msgs, tools=None: "PROMPT")
    monkeypatch.setattr(olmo_format, "n_tokens", lambda text: 10)
    j = next(j for j in b19.jobs(cfg()) if j["model"]["model"] == "olmo3-7b-think" and j["repeat"] == 5)
    assert tb.run_one(cfg(), j)["repeat"] == 5 and sent == [5]


def test_no_cache_sends_every_request_and_writes_nothing_to_the_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(client, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(client, "_request", client._request)      # restored after the test
    sent = []

    def fake_stream(payload, path="/chat/completions"):
        sent.append(payload["seed"])
        return {"content": "Answer: (B)", "reasoning": "", "finish": "stop", "usage": {}, "reasoning_field": None,
                "tool_calls": []}
    monkeypatch.setattr(client, "_stream", fake_stream)
    ask = lambda: client.chat("not-a-voyager-model", [{"role": "user", "content": "Q?"}], seed=3)  # noqa: E731
    assert ask()["cached"] is False and ask()["cached"] is True and len(sent) == 1    # the cache, as client.py has it
    assert len(list(tmp_path.glob("*.json"))) == 1
    b19.no_cache()
    assert ask()["cached"] is False and ask()["cached"] is False and len(sent) == 3
    assert len(list(tmp_path.glob("*.json"))) == 1                                   # nothing more written


def test_the_report_reads_b19s_tool_arms_against_b16s_authority_and_marks_a_changed_reading():
    m = b16.MODELS[0]
    qs = [f"q{i}" for i in range(8)]
    old = [flag(m, c, q, followed=c != "user", source="trackB") for q in qs for c in ("none", "user", "tool_pasted", "tool_real")]
    before = [flag(m, AUTHORITY, q, followed=False) for q in qs]
    before += [flag(m, "tool_pasted", q, followed=False) for q in qs] + [flag(m, "tool_real", q, followed=True) for q in qs]
    new = [flag(m, c, q, followed=True, source="b19") for q in qs for c in ("tool_pasted", "tool_real")]
    res = b19.report(new, before, old)[m]
    assert res["arms"][AUTHORITY]["following"]["n"] == 8 and res["arms"]["tool_pasted"]["following"]["k"] == 8
    pasted, real = res["primary"]["tool_pasted"], res["primary"]["tool_real"]
    assert pasted["reading"] == "tool beyond authority" and pasted["b16_reading"] == "no difference detected"
    assert pasted["same_as_b16"] is False and real["same_as_b16"] is True
    assert res["drift"]["tool_real"]["reading"] == "no difference detected"           # B19's tool arm against Track B's
    assert "CHANGED" in b19.show({m: res}) and "tool_real (B19) - user_authority (B16)" in b19.show({m: res})


def test_replays_count_runs_whose_texts_match_a_track_b_run_of_the_same_question_and_arm(tmp_path, monkeypatch):
    monkeypatch.setattr(tb, "OUT", tmp_path)
    m = b16.MODELS[0]

    def rec(run, exp, item, final, private):
        return {"run_id": run, "experiment": exp, "provider": "voyager", "model": m, "item_id": item,
                "condition": "tool_pasted", "status": "ok", "final_text": final, "reasoning_text": private}
    tb.save(rec("t1", "trackB", "q1", "Answer: (B)", "the guide says B"))
    tb.save(rec("t2", "trackB", "q2", "Answer: (B)", "the guide says B"))
    tb.save(rec("n1", "b19", "q1", "Answer: (B)", "the guide says B"))          # the same texts, the same question
    tb.save(rec("n2", "b19", "q3", "Answer: (B)", "the guide says B"))          # the same texts, another question
    tb.save(rec("n3", "b19", "q2", "Answer: (B)", "worked it out: B"))
    assert b19.replays(tmp_path) == {m: {"tool_pasted": {"identical": 1, "runs": 3}}}
