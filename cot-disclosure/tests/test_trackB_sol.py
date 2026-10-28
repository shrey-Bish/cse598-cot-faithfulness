"""Track B's Qwen3-8B on Sol (decided Oct 28: in place of Ollama on the Mac): the vLLM adapter
(providers/sol_vllm.py) against a fake of the job's OpenAI-compatible server, a whole Track B run
through it (thinking on and off, the tool loop, the one budget), the job driver (progress/sol_trackB.py)
and the numbers-only flags that come back to the Mac. CPU only; no GPU, no network."""
import io
import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

pytest.importorskip("transformers")

import run_trackB as tb  # noqa: E402
import sol_trackB as st  # noqa: E402
import trackB_report as rep  # noqa: E402
from providers import sol_vllm  # noqa: E402


def vllm_answer(body):
    """/v1/chat/completions as vLLM 0.31.0 answers it (message.reasoning, tool_calls, usage)."""
    thinking = (body.get("chat_template_kwargs") or {}).get("enable_thinking")
    msg = {"role": "assistant", "content": "Answer: (B)", "reasoning": "The hint says B; I check it." if thinking else None}
    finish = "stop"
    if body.get("tools") and not any(m["role"] == "tool" for m in body["messages"]):
        msg = {"role": "assistant", "content": "", "reasoning": "Let me look it up." if thinking else None,
               "tool_calls": [{"id": "call_1", "type": "function", "function": {
                   "name": "lookup_answer_key", "arguments": json.dumps({"question_id": "x"})}}]}
        finish = "tool_calls"
    return {"model": body["model"], "choices": [{"message": msg, "finish_reason": finish}],
            "usage": {"prompt_tokens": 300, "completion_tokens": 120 if thinking else 20}}


@pytest.fixture
def server(monkeypatch):
    """A fake urlopen standing in for the job's server (tests never reach the network: conftest.py)."""
    import urllib.request
    bodies = []
    monkeypatch.setenv("TRACKB_VLLM_URL", "http://localhost:8012/v1")

    class Resp(io.BytesIO):
        status = 200

    def fake(req, timeout=None):
        assert req.full_url == "http://localhost:8012/v1/chat/completions"
        body = json.loads(req.data)
        bodies.append(body)
        return Resp(json.dumps(vllm_answer(body)).encode())
    monkeypatch.setattr(urllib.request, "urlopen", fake)
    return bodies


def config():
    c = yaml.safe_load((CODE / "configs" / "trackB.yaml").read_text())
    return {**c, "question_sets": {"pilot_puzzles": {"source": "pilot", "n": 2}}}


def test_the_config_runs_qwen3_8b_on_sol_and_never_ollama():
    c = yaml.safe_load((CODE / "configs" / "trackB.yaml").read_text())
    providers = [(m["provider"], m["model"], m.get("thinking")) for m in c["models"]]
    assert ("sol_vllm", "qwen3-8b", True) in providers and ("sol_vllm", "qwen3-8b", False) in providers
    assert not any(p == "ollama" for p, _, _ in providers)
    assert tb.in_flight(c, "sol_vllm") == c["sol_in_flight"] == 48 and tb.in_flight(c, "voyager") == 4
    assert tb.in_flight(c, "openai") == 1


def test_the_request_and_the_reply():
    req = sol_vllm.build_request("qwen3-8b", [{"role": "user", "content": "Q"}], thinking=False, max_tokens=99, seed=2)
    assert req["chat_template_kwargs"] == {"enable_thinking": False} and req["max_tokens"] == 99 and req["seed"] == 2
    assert "chat_template_kwargs" not in sol_vllm.build_request("m", [], thinking=None)
    text, reasoning, calls, finish, usage = sol_vllm.parse_response(
        {"choices": [{"message": {"content": "A", "reasoning_content": "old field", "tool_calls": None},
                      "finish_reason": "stop"}], "usage": {"prompt_tokens": 5, "completion_tokens": 7}})
    assert (text, reasoning, calls, finish) == ("A", "old field", [], "stop") and usage["output_tokens"] == 7


def test_a_track_b_run_through_the_sol_server(server, tmp_path, monkeypatch):
    monkeypatch.setattr(tb, "OUT", tmp_path)
    c = config()
    jobs = [j for j in tb.jobs(c, only_models=["qwen3-8b"]) if j["repeat"] == 0 and j["item"]["item_id"] == "pilot-0"]
    on = {j["condition"]: j for j in jobs if j["model"]["thinking"]}
    off = {j["condition"]: j for j in jobs if not j["model"]["thinking"]}
    rec = tb.run_one(c, on["tool_real"])
    first, second = server[0], server[1]
    assert first["chat_template_kwargs"] == {"enable_thinking": True} and first["model"] == "qwen3-8b"
    assert first["tools"] and second["max_tokens"] == first["max_tokens"] - 120           # one budget over the calls
    assert first["max_tokens"] == 32768 - rec["max_tokens"]["prompt_tokens_local"] and rec["budget_total"] == 32768
    assert rec["provider"] == "sol_vllm" and rec["called_tool"] and rec["parsed_letter"] == "B"
    assert rec["reasoning_text"] and rec["reasoning_visibility"] == "full" and rec["total_output_tokens"] == 240
    rec_off = tb.run_one(c, off["none"])
    assert server[-1]["chat_template_kwargs"] == {"enable_thinking": False} and not rec_off["reasoning_text"]
    for r in (rec, rec_off):
        tb.save(r)
    n = st.export_flags(records=tmp_path / "sol_vllm.jsonl.gz", out=tmp_path / "back" / "sol_vllm_flags.jsonl")
    assert n == 2
    flags = [json.loads(x) for x in (tmp_path / "back" / "sol_vllm_flags.jsonl").read_text().splitlines()]
    assert not any(k.endswith("_text") or k in ("messages", "prompt") for f in flags for k in f)    # numbers only
    assert all(len(str(v)) < 80 for f in flags for v in f.values())
    got = rep.load_flags(tmp_path / "back")                                              # the Mac: flags, no records
    assert {r["run_id"] for r in got} == {rec["run_id"], rec_off["run_id"]}
    by_id = {r["run_id"]: r for r in got}
    assert by_id[rec["run_id"]]["followed"] == (rec["hint_letter"] == "B") and by_id[rec["run_id"]]["called_tool"]
    assert by_id[rec["run_id"]]["mention_private"] is not None and by_id[rec_off["run_id"]]["followed"] is False


def test_the_job_driver(tmp_path, monkeypatch):
    monkeypatch.setenv("TRACKA_OUT", str(tmp_path))
    monkeypatch.setattr(st, "STOP", tmp_path / "stop")
    monkeypatch.setattr(st, "snapshot", lambda local_only=True: (_ for _ in ()).throw(OSError("not cached")))
    with pytest.raises(SystemExit, match="run --download first"):
        st.run([], tmp_path / "log")
    monkeypatch.setattr(st, "snapshot", lambda local_only=True: tmp_path / "snap")
    with pytest.raises(SystemExit, match="run setup_vllm first"):
        st.run([], tmp_path / "log")
    shutil.copy(CODE / "finetune" / "gpu" / "vllm_serve_options.txt", tmp_path / "vllm_serve_options.txt")
    from finetune.gpu import eval_job
    seen, handlers = {}, {}

    class FakeServer:
        def __init__(self, *a, cmd=None, **kw):
            seen["cmd"] = cmd

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_call(cmd, env, cwd):
        seen["runner"], seen["url"] = cmd, env["TRACKB_VLLM_URL"]
        handlers["usr1"]()                                                                  # Slurm's warning
        return 2
    monkeypatch.setattr(eval_job, "Server", FakeServer)
    monkeypatch.setattr(st.subprocess, "call", fake_call)
    monkeypatch.setattr(st.signal, "signal", lambda sig, h: handlers.__setitem__("usr1", lambda: h(sig, None)))
    monkeypatch.setattr(st, "export_flags", lambda: 0)
    assert st.run(["--limit", "5"], tmp_path / "log") == 2
    assert seen["cmd"][:3] == ["vllm", "serve", str(tmp_path / "snap")] and "--reasoning-parser" in seen["cmd"]
    assert seen["runner"][-6:] == ["--order", "core-first", "--stop-file", str(tmp_path / "stop"), "--limit", "5"]
    assert "--model" in seen["runner"] and "qwen3-8b" in seen["runner"] and seen["url"].endswith(":8012/v1")
    assert (tmp_path / "stop").read_text() == "Slurm's time-limit warning"
    (tmp_path / "vllm_serve_options.txt").write_text(
        (tmp_path / "vllm_serve_options.txt").read_text().replace("--enable-auto-tool-choice, --no-enable-auto-tool-choice\n", ""))
    with pytest.raises(SystemExit, match="trackB qwen3-8b: --enable-auto-tool-choice"):
        st.run([], tmp_path / "log")
