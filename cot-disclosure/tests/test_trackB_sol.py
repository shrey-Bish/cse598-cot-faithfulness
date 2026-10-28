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
    assert "chat_template_kwargs" not in sol_vllm.build_request("m", [], thinking=None, max_tokens=5)
    for thinking in (True, False):                                   # the same sampling on and off (Oct 28)
        r = sol_vllm.build_request("qwen3-8b", [], thinking=thinking, max_tokens=5, temperature=0.6)
        assert (r["temperature"], r["top_p"], r["top_k"]) == (0.6, 0.95, 20)
    with pytest.raises(TypeError):                                   # no default: the caller gives the budget left
        sol_vllm.build_request("qwen3-8b", [])
    with pytest.raises(ValueError):
        sol_vllm.build_request("qwen3-8b", [], max_tokens=0)
    text, reasoning, calls, finish, usage = sol_vllm.parse_response(
        {"choices": [{"message": {"content": "A", "reasoning_content": "old field", "tool_calls": None},
                      "finish_reason": "stop"}], "usage": {"prompt_tokens": 5, "completion_tokens": 7}})
    assert (text, reasoning, calls, finish) == ("A", "old field", [], "stop") and usage["output_tokens"] == 7


def test_a_qwen3_8b_request_carries_the_budget_left(server, tmp_path, monkeypatch):
    """Track B's one budget (Oct 27): 32,768 tokens minus the prompt, counted with Qwen3-8B's template."""
    monkeypatch.setattr(tb, "OUT", tmp_path)
    c = config()
    for thinking in (True, False):
        j = next(j for j in tb.jobs(c, only_models=["qwen3-8b"]) if j["model"]["thinking"] is thinking
                 and j["condition"] == "user")
        rec = tb.run_one(c, j)
        prompt = rec["max_tokens"]["prompt_tokens_local"]
        assert 200 < prompt < 2000 and server[-1]["max_tokens"] == 32768 - prompt
        assert server[-1]["max_tokens"] > 16000                      # not the old 16,000 default


def test_a_track_b_run_through_the_sol_server(server, tmp_path, monkeypatch):
    monkeypatch.setattr(tb, "OUT", tmp_path)
    monkeypatch.setenv("TRACKB_CHAT_TEMPLATE_SHA256", "ab" * 32)
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
    assert rec["chat_template_sha256"] == "ab" * 32 and tb.summary_row(rec)["chat_template_sha256"] == "ab" * 32
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
    order = []

    def refuse(vllm, log_dir):
        order.append("preflight")
        sys.exit("refusing: this node's vLLM options differ")
    monkeypatch.setattr(st, "preflight", refuse)
    monkeypatch.setattr(st, "snapshot", lambda local_only=True: order.append("snapshot") or tmp_path / "snap")
    with pytest.raises(SystemExit, match="differ"):                       # the node check comes first
        st.run([], tmp_path / "log")
    assert order == ["preflight"]
    monkeypatch.setattr(st, "preflight", lambda vllm, log_dir: order.append("preflight"))
    monkeypatch.setattr(st, "snapshot", lambda local_only=True: (_ for _ in ()).throw(OSError("not cached")))
    with pytest.raises(SystemExit, match="no Qwen/Qwen3-8B snapshot.*run the download job first"):
        st.run([], tmp_path / "log")
    snap = tmp_path / "snap"
    snap.mkdir()
    (snap / "tokenizer_config.json").write_text(json.dumps({"chat_template": "{{ messages }}"}))
    (snap / "model.safetensors").write_bytes(b"w" * 10)
    monkeypatch.setattr(st, "snapshot", lambda local_only=True: snap)
    with pytest.raises(SystemExit, match="run the download job first"):                # no snapshot.json yet
        st.run([], tmp_path / "log")
    (tmp_path / "log").mkdir(exist_ok=True)
    (tmp_path / "log" / "snapshot.json").write_text(json.dumps({"revision": st.REVISION, "files": [
        {"file": "model.safetensors", "bytes": 10}]}))
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
        seen["runner"], seen["url"], seen["sha"] = cmd, env["TRACKB_VLLM_URL"], env["TRACKB_CHAT_TEMPLATE_SHA256"]
        handlers["usr1"]()                                                                  # Slurm's warning
        return 2
    monkeypatch.setattr(eval_job, "Server", FakeServer)
    monkeypatch.setattr(st.subprocess, "call", fake_call)
    monkeypatch.setattr(st.signal, "signal", lambda sig, h: handlers.__setitem__("usr1", lambda: h(sig, None)))
    monkeypatch.setattr(st, "export_flags", lambda: 0)
    assert st.run(["--limit", "5"], tmp_path / "log") == 2
    assert seen["cmd"][:3] == ["vllm", "serve", str(tmp_path / "snap")] and "--reasoning-parser" in seen["cmd"]
    template = Path(seen["cmd"][seen["cmd"].index("--chat-template") + 1])
    assert template.read_text() == "{{ messages }}"
    assert seen["sha"] == __import__("hashlib").sha256(b"{{ messages }}").hexdigest()
    assert seen["runner"][-6:] == ["--order", "core-first", "--stop-file", str(tmp_path / "stop"), "--limit", "5"]
    assert "--model" in seen["runner"] and "qwen3-8b" in seen["runner"] and seen["url"].endswith(":8012/v1")
    assert (tmp_path / "stop").read_text() == "Slurm's time-limit warning"


def test_the_download_job_checks_every_file_against_the_hub(tmp_path, monkeypatch):
    """The no-GPU job (the only one online): the pinned snapshot, each file's sha256 against the Hub's,
    and its record; a mismatch refuses. The GPU job then checks the record's sizes offline."""
    import hashlib
    import huggingface_hub
    from types import SimpleNamespace as NS
    snap = tmp_path / "snap"
    snap.mkdir()
    (snap / "tokenizer_config.json").write_text(json.dumps({"chat_template": "T"}))
    (snap / "model-00001.safetensors").write_bytes(b"weights")
    good = hashlib.sha256(b"weights").hexdigest()
    monkeypatch.setattr(st, "snapshot", lambda local_only=True: snap)
    hub = {"sha": st.REVISION, "lfs": good}

    class Api:
        def model_info(self, repo, revision, files_metadata):
            assert (repo, revision, files_metadata) == (st.REPO, st.REVISION, True)
            return NS(sha=hub["sha"], siblings=[NS(rfilename="model-00001.safetensors", lfs=NS(sha256=hub["lfs"])),
                                                NS(rfilename="tokenizer_config.json", lfs=None),
                                                NS(rfilename="README.md", lfs=None)])
    monkeypatch.setattr(huggingface_hub, "HfApi", Api)
    rec = st.download(tmp_path / "log")
    saved = json.loads((tmp_path / "log" / "snapshot.json").read_text())
    assert saved == rec and rec["revision"] == st.REVISION and rec["was_cached"]
    assert [f["file"] for f in rec["files"]] == ["model-00001.safetensors", "tokenizer_config.json"]
    assert rec["files"][0]["sha256"] == good and rec["chat_template_sha256"] == hashlib.sha256(b"T").hexdigest()
    assert st.check_snapshot(snap, tmp_path / "log")["revision"] == st.REVISION
    (snap / "model-00001.safetensors").write_bytes(b"weights, changed")
    with pytest.raises(SystemExit, match="snapshot differs"):
        st.check_snapshot(snap, tmp_path / "log")
    hub["lfs"] = "0" * 64
    with pytest.raises(SystemExit, match="doesn't match the Hub"):
        st.download(tmp_path / "log2")
