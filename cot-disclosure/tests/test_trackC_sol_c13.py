"""Track C, C13 on Sol (agents/sol_c13.py, providers/sol_chat.py): two more reviewer families on our own vLLM
server, reviewer only on C4's saved cases. The provider against a fake server, the job driver's order, the
download job's checks, the runner it starts, and the GPU estimate. CPU only; no GPU, no network."""
import hashlib
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from agents import sol_c13 as c13  # noqa: E402
from providers import generate, sol_chat  # noqa: E402


@pytest.fixture
def server(monkeypatch):
    """A fake urlopen standing in for the job's server (tests never reach the network: conftest.py)."""
    import urllib.request
    bodies = []
    monkeypatch.setenv("SOL_CHAT_URL", "http://localhost:8013/v1")

    class Resp(io.BytesIO):
        status = 200

    def fake(req, timeout=None):
        assert req.full_url == "http://localhost:8013/v1/chat/completions"
        body = json.loads(req.data)
        bodies.append(body)
        return Resp(json.dumps({"model": body["model"], "choices": [{"message": {"role": "assistant", "content":
                                "The key's letter is wrong.\nFinal answer: (C)"}, "finish_reason": "stop"}],
                                "usage": {"prompt_tokens": 900, "completion_tokens": 40}}).encode())
    monkeypatch.setattr(urllib.request, "urlopen", fake)
    return bodies


def test_a_review_sends_what_c4s_voyager_calls_sent_and_nothing_else(server):
    """C4's reviewer calls carried messages, max_tokens, temperature and seed; everything else is the
    server's default (the model's generation_config.json), as on Voyager."""
    msgs = [{"role": "system", "content": "You review."}, {"role": "user", "content": "Q?"}]
    r = generate("sol_chat", "granite-4.1-30b", msgs, max_tokens=16000, temperature=0.6, seed=2)
    assert server == [{"model": "granite-4.1-30b", "messages": msgs, "max_tokens": 16000, "temperature": 0.6, "seed": 2}]
    assert r.final_text.endswith("Final answer: (C)") and r.finish_reason == "stop" and r.error is None
    assert r.usage["input_tokens"] == 900 and r.usage["output_tokens"] == 40 and r.raw["served_model"] == "granite-4.1-30b"
    with pytest.raises(ValueError, match="non-thinking"):
        generate("sol_chat", "granite-4.1-30b", msgs, max_tokens=10, thinking=True)


def test_a_server_that_is_down_is_an_error_reply_not_a_crash(monkeypatch):
    import urllib.request

    def down(req, timeout=None):
        raise ConnectionRefusedError("refused")
    monkeypatch.setattr(urllib.request, "urlopen", down)
    r = sol_chat.generate("m", [{"role": "user", "content": "q"}], max_tokens=10, seed=0)
    assert r.error.startswith("ConnectionRefusedError") and r.finish_reason == "error"


def test_the_two_reviewers_are_new_families_and_their_servers_fit_the_committed_options():
    from finetune.gpu import vllm_options
    assert [m["family"] for m in c13.MODELS.values()] == ["IBM Granite", "Mistral"]
    assert len({m["log"] for m in c13.MODELS.values()}) == 2                       # each model resumes on its own
    cmds = vllm_options.job_commands()
    assert {f"c13 {n}" for n in c13.MODELS} <= set(cmds)
    assert vllm_options.problems(cmds, vllm_options.load()[1]) == []
    mistral = c13.serve_cmd("mistral-small-3.2-24b", "S")
    for flag in ("--tokenizer-mode", "--config-format", "--load-format"):
        assert mistral[mistral.index(flag) + 1] == "mistral"
    assert c13.serve_cmd("granite-4.1-30b", "S")[2:] == ["S", "--served-model-name", "granite-4.1-30b", "--port", "8013",
                                                          "--max-model-len", "32768", "--dtype", "bfloat16", "--seed", "0"]


def test_the_runner_is_c4s_rereview_with_c11s_settings():
    cmd = c13.runner_cmd("granite-4.1-30b")
    assert cmd[2].endswith("agents/run_team.py")
    args = cmd[3:]
    opt = lambda k: args[args.index(k) + 1]  # noqa: E731
    assert opt("--rereview") == "team_c4" and "--no-check-tool" in args and "--bad-first" in args
    assert opt("--reviewer-model") == "sol_chat:granite-4.1-30b" and opt("--reviewer-max-tokens") == "16000"
    assert opt("--log") == "team_c13_granite" and opt("--workers") == "16" and "--variants" not in args  # C9's three


def test_run_team_passes_workers_to_the_rereview(monkeypatch, tmp_path):
    from agents import run_team as rt
    seen = {}
    monkeypatch.setattr(rt, "OUT", tmp_path)
    (tmp_path / "team_c4.jsonl").write_text("")
    monkeypatch.setattr(rt, "items_by_source", lambda cases: {})
    monkeypatch.setattr(rt, "saved_cases", lambda path, items: [])
    monkeypatch.setattr(rt, "rereview", lambda *a, **kw: seen.update(kw) or 0)
    monkeypatch.setattr(sys, "argv", ["run_team.py", "--rereview", "team_c4", "--no-check-tool", "--reviewer-model",
                                      "sol_chat:granite-4.1-30b", "--cases", "c.jsonl", "--log", "team_c13_granite",
                                      "--workers", "16"])
    assert rt.main() == 0 and seen["workers"] == 16
    monkeypatch.setattr(sys, "argv", sys.argv[:-2])
    rt.main()
    assert seen["workers"] == rt.IN_FLIGHT                                              # Voyager's 4 by default


def test_the_job_checks_the_node_and_inputs_first_then_runs_each_model_on_its_server(tmp_path, monkeypatch):
    from finetune.gpu import eval_job, vllm_options
    order = []
    monkeypatch.setattr(c13, "STOP", tmp_path / "stop")
    monkeypatch.setattr(c13.signal, "signal", lambda sig, handler: None)
    monkeypatch.setattr(vllm_options, "gpu_preflight", lambda vllm, log_dir: order.append("preflight"))
    monkeypatch.setattr(c13, "inputs_present", lambda: order.append("inputs"))
    monkeypatch.setattr(c13, "checked_snapshot", lambda name, log_dir: order.append(f"snapshot {name}") or Path(f"/snap/{name}"))

    class FakeServer:
        def __init__(self, model, prompt_embeds, port=None, log=None, cmd=None):
            order.append(f"server {Path(log).name} {cmd[2]} {port}")

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            order.append("stopped")
            return False
    codes = iter([0, 1])

    def fake_call(cmd, env, cwd):
        order.append(f"runner {cmd[cmd.index('--reviewer-model') + 1]} {env['SOL_CHAT_URL']}")
        return next(codes)
    monkeypatch.setattr(eval_job, "Server", FakeServer)
    monkeypatch.setattr(c13.subprocess, "call", fake_call)
    assert c13.run(tmp_path / "log") == 1                                     # the largest exit: work left
    assert order == ["preflight", "inputs",
                     "snapshot granite-4.1-30b", "server vllm_granite-4.1-30b.log /snap/granite-4.1-30b 8013",
                     "runner sol_chat:granite-4.1-30b http://localhost:8013/v1", "stopped",
                     "snapshot mistral-small-3.2-24b", "server vllm_mistral-small-3.2-24b.log /snap/mistral-small-3.2-24b 8013",
                     "runner sol_chat:mistral-small-3.2-24b http://localhost:8013/v1", "stopped"]


def test_missing_inputs_refuse_before_any_server(tmp_path, monkeypatch):
    monkeypatch.setattr(c13, "CODE", tmp_path)
    with pytest.raises(SystemExit, match="rsync these from the Mac first.*team_c4.jsonl.*steered_cases.jsonl"):
        c13.inputs_present()


def test_the_download_job_refuses_a_gated_model_and_checks_every_file(tmp_path, monkeypatch):
    import huggingface_hub
    from finetune.gpu import kit
    snap = tmp_path / "snap"
    snap.mkdir()
    (snap / "config.json").write_text("{}")
    (snap / "generation_config.json").write_text(json.dumps({"temperature": 0.7, "top_p": 0.9}))
    (snap / "model-00001-of-00002.safetensors").write_bytes(b"weights")
    monkeypatch.setattr(c13, "snapshot", lambda name, local_only=True: snap)
    hub = {"gated": False, "lfs": hashlib.sha256(b"weights").hexdigest()}

    class Api:
        def model_info(self, repo, revision, files_metadata):
            assert (repo, revision) == (c13.MODELS["granite-4.1-30b"]["repo"], c13.MODELS["granite-4.1-30b"]["revision"])
            return NS(gated=hub["gated"], card_data=NS(license="apache-2.0"), siblings=[
                NS(rfilename="model-00001-of-00002.safetensors", lfs=NS(sha256=hub["lfs"]), blob_id="x"),
                NS(rfilename="config.json", lfs=None, blob_id=kit.git_blob_id(snap / "config.json")),
                NS(rfilename="generation_config.json", lfs=None, blob_id=kit.git_blob_id(snap / "generation_config.json")),
                NS(rfilename="README.md", lfs=None, blob_id="y")])
    monkeypatch.setattr(huggingface_hub, "HfApi", Api)
    rec = c13.download("granite-4.1-30b", tmp_path / "log")
    assert rec["license"] == "apache-2.0" and rec["gated"] is False and rec["generation_config"]["top_p"] == 0.9
    assert [f["file"] for f in rec["files"]] == ["model-00001-of-00002.safetensors", "config.json", "generation_config.json"]
    assert c13.checked_snapshot("granite-4.1-30b", tmp_path / "log") == snap
    (snap / "config.json").write_text('{"changed": 1}')
    with pytest.raises(SystemExit, match="snapshot differs"):
        c13.checked_snapshot("granite-4.1-30b", tmp_path / "log")
    hub["gated"] = "manual"
    with pytest.raises(SystemExit, match="is gated"):
        c13.download("granite-4.1-30b", tmp_path / "log2")


def test_the_estimate_sizes_each_model_from_c11s_instruct_reviews(tmp_path):
    rows = [{"agent": "reviewer", "reviewer_model": "olmo3-7b-instruct", "tokens": 3600, "final_text": "x" * 360}] * 477
    rows += [{"agent": "reviewer", "reviewer_model": "qwen3-30b-a3b-thinking-2507", "tokens": 99999, "final_text": ""}]
    path = tmp_path / "team_c11.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    e = c13.estimate(path)
    assert e["reviews_per_model"] == 477 and e["tokens_per_model"] == 477 * 3600 and e["generated_per_model"] == 477 * 100
    fast = ((477 * 3500) / 4000 + 477 * 100 / 600) / 3600
    assert e["generation_hours_per_model"][0] == pytest.approx(fast, abs=0.01)
