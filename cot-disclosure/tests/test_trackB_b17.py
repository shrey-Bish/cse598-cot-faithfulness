"""B17 (Oct 31): gpt-oss-20b at three reasoning efforts on our Sol vLLM server. The design and its run ids, the
request (effort, sampling, the reasoning passed back between calls), a whole run through a fake of vLLM's harmony
server, the served-template check, the smoke's verdict, the report's pre-registered contrasts, the job driver and
the download job. CPU only; no GPU, no network."""
import hashlib
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest
import yaml

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

import run_b17 as rb  # noqa: E402
import run_trackB as tb  # noqa: E402
import sol_b17 as sb  # noqa: E402
import trackB_report as rep  # noqa: E402
from providers import sol_vllm  # noqa: E402

CFG = yaml.safe_load((CODE / "configs" / "trackB.yaml").read_text())


def test_the_design_is_track_bs_at_three_efforts_with_their_own_run_ids():
    jobs = rb.jobs(CFG)
    assert len(jobs) == 54 * 5 * 3 * 3 == 2430 and len({j["run_id"] for j in jobs}) == 2430
    assert {j["model"]["effort"] for j in jobs} == {"low", "medium", "high"} and {j["experiment"] for j in jobs} == {"b17"}
    first = jobs[:rb.SMOKE_JOBS]                                       # the smoke: one question, every cell
    assert {j["item"]["item_id"] for j in first} == {"pilot-0"} and {j["repeat"] for j in first} == {0}
    assert {(j["model"]["effort"], j["condition"]) for j in first} == {(e, c) for e in rb.EFFORTS for c in CFG["conditions"]}
    assert max(j["repeat"] for j in jobs[:810]) == 0                   # repeat by repeat
    assert tb.model_tag(first[0]["model"]) == "gpt-oss-20b|think=None|effort=low"
    qwen = next(m for m in CFG["models"] if m["model"] == "qwen3-8b")   # Track B's run ids don't move
    assert tb.model_tag(qwen) == "qwen3-8b|think=True"


def test_the_request_carries_the_effort_and_gpt_oss_sampling_and_qwen_is_unchanged():
    msgs = [{"role": "user", "content": "Q"}]
    r = sol_vllm.build_request("gpt-oss-20b", msgs, max_tokens=9, temperature=0.6, seed=1, reasoning_effort="high")
    assert (r["reasoning_effort"], r["temperature"], r["top_p"], r["seed"]) == ("high", 0.6, 1.0, 1) and "top_k" not in r
    assert "chat_template_kwargs" not in r
    q = sol_vllm.build_request("qwen3-8b", msgs, max_tokens=9, thinking=True)
    assert (q["top_p"], q["top_k"]) == (0.95, 20) and "reasoning_effort" not in q
    called = {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {
        "name": "lookup_answer_key", "arguments": "{}"}}], "_native": {"provider": "sol_vllm", "items": {"reasoning": "R"}}}
    sent = sol_vllm.build_request("gpt-oss-20b", msgs + [called], max_tokens=9)["messages"][-1]
    assert sent["reasoning"] == "R" and "_native" not in sent           # harmony's analysis before the call
    assert "reasoning" not in sol_vllm.build_request("qwen3-8b", msgs + [called], max_tokens=9)["messages"][-1]


def harmony_answer(body):
    """/v1/chat/completions as vLLM 0.31.0 answers a gpt-oss request (message.reasoning, tool_calls, usage);
    the reasoning's length follows the effort."""
    n = {"low": 50, "medium": 200, "high": 800}[body["reasoning_effort"]]
    msg, finish = {"role": "assistant", "content": "Answer: (B)", "reasoning": "x" * n}, "stop"
    if body.get("tools") and not any(m["role"] == "tool" for m in body["messages"]):
        msg = {"role": "assistant", "content": None, "reasoning": "Let me look it up.", "tool_calls": [
            {"id": "call_1", "type": "function", "function": {"name": "lookup_answer_key",
                                                              "arguments": json.dumps({"question_id": "pilot-0"})}}]}
        finish = "tool_calls"
    return {"model": body["model"], "choices": [{"message": msg, "finish_reason": finish}],
            "usage": {"prompt_tokens": 150, "completion_tokens": n}}


@pytest.fixture
def server(monkeypatch, tmp_path):
    import urllib.request
    bodies = []
    monkeypatch.setenv("TRACKB_VLLM_URL", "http://localhost:8012/v1")
    monkeypatch.setattr(tb, "OUT", tmp_path)
    monkeypatch.setattr(tb, "prompt_tokens", lambda model, msgs, tools: 140)

    class Resp(io.BytesIO):
        status = 200

    def fake(req, timeout=None):
        body = json.loads(req.data)
        bodies.append(body)
        return Resp(json.dumps(harmony_answer(body)).encode())
    monkeypatch.setattr(urllib.request, "urlopen", fake)
    return bodies


def test_a_b17_run_through_the_harmony_server_and_the_flags_track_b_never_reads(server, tmp_path):
    jobs = {(j["model"]["effort"], j["condition"]): j for j in rb.jobs(CFG)[:rb.SMOKE_JOBS]}
    rec = tb.run_one(CFG, jobs[("high", "tool_real")])
    first, second = server[0], server[1]
    assert first["reasoning_effort"] == second["reasoning_effort"] == "high" and first["tools"]
    assert first["max_tokens"] == 32768 - 140 and second["max_tokens"] == first["max_tokens"] - 800
    assert second["messages"][-2]["reasoning"] == "Let me look it up." and second["messages"][-1]["role"] == "tool"
    assert (rec["effort"], rec["reasoning_effort"], rec["experiment"]) == ("high", "high", "b17")
    assert rec["called_tool"] and rec["parsed_letter"] == "B" and rec["provider"] == "sol_vllm"
    low = tb.run_one(CFG, jobs[("low", "none")])
    for r in (rec, low):
        tb.save(r)
    assert (tmp_path / "b17_sol_vllm.jsonl.gz").exists() and tb.summary_row(rec)["effort"] == "high"
    assert "effort" not in tb.summary_row({"run_id": "x"})                 # Track B's rows as they were
    n = rb.export_flags(records=tmp_path / "b17_sol_vllm.jsonl.gz", out=tmp_path / "b17" / "b17_flags.jsonl")
    flags = [json.loads(x) for x in (tmp_path / "b17" / "b17_flags.jsonl").read_text().splitlines()]
    assert n == 2 and {f["effort"] for f in flags} == {"high", "low"}
    assert not any(k.endswith("_text") or k in ("messages", "prompt") for f in flags for k in f)
    assert rep.load_flags(tmp_path) == []                                  # never in Track B's table
    assert tb.done("sol_vllm", "b17") == {rec["run_id"], low["run_id"]} and tb.done("sol_vllm") == set()


def test_the_template_check_passes_identical_and_whitespace_and_stops_on_a_difference():
    decode = lambda ids: " ".join(str(i) for i in ids)                    # noqa: E731
    same = rb.template_check(CFG, lambda e, m, t: [1, 2, 3], lambda e, m, t: [1, 2, 3], decode)
    assert same["ok"] and len(same["rows"]) == 15 and {r["verdict"] for r in same["rows"]} == {"identical"}
    words = {1: "a b", 2: "a  b", 3: "a c"}
    ws = rb.compare_ids([2], [1], lambda ids: words[ids[0]])
    assert ws["verdict"] == "whitespace only"
    diff = rb.template_check(CFG, lambda e, m, t: [1, 9, 3] if m[0]["role"] == "system" else [1, 2, 3],
                             lambda e, m, t: [1, 2, 3], decode)
    bad = [r for r in diff["rows"] if r["verdict"] == "differs"]
    assert not diff["ok"] and {r["condition"] for r in bad} == {"system"} and len(bad) == 3
    assert bad[0]["first_difference"] == 1 and bad[0]["gap"] == 0


def test_whitespace_on_one_side_only_is_a_whitespace_only_difference():
    """The amendment of Nov 2 (§12): the smoke 245445 stopped on the system condition, where the chat template ends
    the developer message's instructions with a blank line and vLLM's harmony rendering doesn't. Whitespace present on
    one side only differs in whitespace only, as the rule says; the record keeps where."""
    words = {1: "v2).<|end|>", 2: "v2).\n\n<|end|>", 3: "v3).<|end|>"}
    decode = lambda ids: "".join(words[i] for i in ids)                      # noqa: E731
    ws = rb.compare_ids([1], [2], decode)
    assert ws["verdict"] == "whitespace only" and ws["first_difference"] == 0
    assert (ws["server_text"], ws["local_text"]) == (words[1], words[2])
    assert rb.compare_ids([3], [2], decode)["verdict"] == "differs"


def smoke_rows(tokens=None, statuses=None, called=True):
    tokens = tokens or {"low": 300, "medium": 1200, "high": 5000}
    rows = []
    for k, j in enumerate(rb.jobs(CFG)[:rb.SMOKE_JOBS]):
        e = j["model"]["effort"]
        rows.append({"run_id": j["run_id"], "status": (statuses or {}).get(k, "ok"), "condition": j["condition"],
                     "effort": e, "called_tool": called and j["condition"] == "tool_real", "parsed_letter": "B",
                     "finish_reason": "stop", "total_output_tokens": tokens[e]})
    return rows


def test_the_smoke_check():
    ok = rb.smoke_check(smoke_rows())
    assert ok["ok"] and ok["status_ok"] == 15 and ok["tool_real_called"] == 3
    assert ok["median_output_tokens"] == {"low": 300, "medium": 1200, "high": 5000}
    flat = rb.smoke_check(smoke_rows(tokens={"low": 900, "medium": 900, "high": 900}))
    assert not flat["ok"] and not flat["checks"]["effort reaches the model"]
    err = rb.smoke_check(smoke_rows(statuses={4: "api_error"}))
    assert not err["checks"]["all ran"] and err["statuses"] == {"ok": 14, "api_error": 1}
    assert not rb.smoke_check(smoke_rows(called=False))["checks"]["tool path ran"]
    assert not rb.smoke_check(smoke_rows()[:10])["checks"]["all ran"]


def test_the_smoke_check_counts_answers_and_parses(monkeypatch):
    """Ritik, Nov 1: the smoke also fails on too few answers (fewer than 12 of 15 with a letter) or on a run that
    ended on its own without a letter the parser reads."""
    rows = smoke_rows()
    for r in rows[:3]:                                                    # 3 cut off: 12 of 15 answered, still clean
        r.update(parsed_letter=None, finish_reason="length")
    ok = rb.smoke_check(rows)
    assert ok["ok"] and ok["answered"] == 12 and ok["checks"]["answered"] and ok["checks"]["parse"]
    rows[3].update(parsed_letter=None, finish_reason="length")             # 11 of 15
    few = rb.smoke_check(rows)
    assert not few["ok"] and not few["checks"]["answered"] and few["checks"]["parse"]
    rows = smoke_rows()
    rows[7]["parsed_letter"] = None                                       # ended on its own, no letter: a parse failure
    bad = rb.smoke_check(rows)
    assert not bad["ok"] and not bad["checks"]["parse"] and bad["checks"]["answered"] and bad["unparsed"] == 1


def test_b17_runs_at_gpt_oss_recommended_temperature(server):
    """Ritik, Nov 1: gpt-oss-20b at its recommended temperature 1.0 (top_p 1.0); Track B's other models keep 0.6."""
    cfg = rb.config()
    assert cfg["temperature"] == rb.TEMPERATURE == 1.0 and CFG["temperature"] == 0.6
    assert {**cfg, "temperature": CFG["temperature"]} == CFG                    # nothing else differs
    job = rb.jobs(cfg)[0]
    assert job["run_id"] == rb.jobs(CFG)[0]["run_id"]                   # the run ids don't move
    tb.run_one(cfg, job)
    assert {(b["temperature"], b["top_p"]) for b in server} == {(1.0, 1.0)}


@pytest.fixture
def smoke_job(tmp_path, monkeypatch):
    """sol_b17.run with its server, snapshot and runner faked; returns run(rows) -> the job's exit code."""
    monkeypatch.setattr(sb, "STOP", tmp_path / "stop")
    monkeypatch.setattr(rb, "OUT", tmp_path / "b17")
    monkeypatch.setattr(tb, "OUT", tmp_path)
    monkeypatch.setattr(sb, "preflight", lambda vllm, log_dir: None)
    snap = tmp_path / "snap"
    snap.mkdir()
    (snap / "chat_template.jinja").write_text("{{ messages }}")
    (snap / "model-00000-of-00002.safetensors").write_bytes(b"w" * 10)
    monkeypatch.setattr(sb, "snapshot", lambda local_only=True: snap)
    (tmp_path / "log").mkdir()
    (tmp_path / "log" / "snapshot.json").write_text(json.dumps({"revision": sb.REVISION, "files": [
        {"file": "model-00000-of-00002.safetensors", "bytes": 10}]}))
    from finetune.gpu import eval_job
    import transformers

    class FakeServer:
        def __init__(self, *a, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False
    monkeypatch.setattr(eval_job, "Server", FakeServer)
    monkeypatch.setattr(transformers.AutoTokenizer, "from_pretrained", lambda path, **kw: NS(decode=str))
    monkeypatch.setattr(sb, "local_ids", lambda tok: lambda e, m, t: [1, 2])
    monkeypatch.setattr(rb, "export_flags", lambda: 0)

    def run(rows, served=(1, 2), runner_rc=0):
        monkeypatch.setattr(sb, "server_ids", lambda url: lambda e, m, t: list(served))
        monkeypatch.setattr(sb.subprocess, "call", lambda cmd, env, cwd: runner_rc)
        (tmp_path / "b17_sol_vllm_runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        return sb.run(tmp_path / "log", smoke=True)
    return run


def test_the_smoke_job_exits_non_zero_when_any_check_fails(smoke_job):
    """Ritik, Nov 1: the main job chains on the smoke (afterok), so the smoke job exits 0 only when every check
    passes: the served template (4), then all ran, answered, parse, the tool path and the effort (5)."""
    assert smoke_job(smoke_rows()) == 0
    assert smoke_job(smoke_rows(), served=(1, 9)) == 4                    # the template differs
    few = smoke_rows()
    for r in few[:4]:
        r.update(parsed_letter=None, finish_reason="length")
    assert smoke_job(few) == 5                                           # 11 of 15 answered
    unparsed = smoke_rows()
    unparsed[0]["parsed_letter"] = None
    assert smoke_job(unparsed) == 5                                      # a finished run the parser can't read
    assert smoke_job(smoke_rows(statuses={2: "api_error"})) == 5         # not all ran
    assert smoke_job(smoke_rows(called=False)) == 5                      # the tool path never ran
    assert smoke_job(smoke_rows(tokens={"low": 900, "medium": 900, "high": 900})) == 5     # the effort doesn't reach it
    assert smoke_job(smoke_rows(), runner_rc=2) == 2                     # stopped by Slurm's warning: not 0 either


def flag(q, effort, cond, followed, called=True, chars=20, tokens=1000):
    return {"item_id": f"q{q}", "effort": effort, "condition": cond, "answered": True, "followed": followed,
            "called_tool": called and cond == "tool_real", "final_chars": chars, "parsed_letter": "B",
            "hint_letter": "B" if followed else "C", "correct_letter": "A", "mention_final": False,
            "mention_private": True, "total_output_tokens": tokens}


def test_the_report_reads_high_minus_low_by_the_rule():
    rows = []
    for q in range(8):
        rows += [flag(q, "low", "tool_real", False, chars=200), flag(q, "medium", "tool_real", q % 2 == 0, chars=200),
                 flag(q, "high", "tool_real", True, chars=20, tokens=20000)]
        rows += [flag(q, e, c, False) for e in rb.EFFORTS for c in ("none", "user", "tool_pasted", "system")]
    res = rb.report(rows)
    p = res["primary"]["high - low"]
    assert p["following_tool_real"]["diff"] == 1.0 and p["following_tool_real"]["reading"] == "rises with effort"
    assert p["bare_after_call"]["reading"] == "rises with effort"
    assert res["secondary"]["medium - low"]["following_tool_real"]["reading"] in ("rises with effort", "no change detected")
    cut = res["cut_16000"]["high - low"]["following_tool_real"]                  # the 16,000 cut: high has no answer
    assert cut["with"]["n"] == 0 and cut["reading"] == "too few questions"
    assert res["per_effort"]["high"]["channels"]["tool_real"]["following"]["k"] == 8
    assert res["per_effort"]["high"]["gate2_tool_minus_user"]["tool_real"]["clear"]
    few = rb.report([r for r in rows if r["item_id"] in ("q0", "q1", "q2")])
    assert few["primary"]["high - low"]["following_tool_real"]["reading"] == "too few questions"


def test_the_job_driver(tmp_path, monkeypatch):
    order, seen = [], {}
    monkeypatch.setattr(sb, "STOP", tmp_path / "stop")
    monkeypatch.setattr(rb, "OUT", tmp_path / "b17")
    monkeypatch.setattr(sb, "preflight", lambda vllm, log_dir: order.append("preflight") or sys.exit("refusing: options"))
    with pytest.raises(SystemExit, match="options"):                  # the node's options come first
        sb.run(tmp_path / "log")
    monkeypatch.setattr(sb, "preflight", lambda vllm, log_dir: order.append("preflight"))
    monkeypatch.setattr(sb, "snapshot", lambda local_only=True: (_ for _ in ()).throw(OSError("not cached")))
    with pytest.raises(SystemExit, match="submit.sh get_gptoss"):
        sb.run(tmp_path / "log")
    snap = tmp_path / "snap"
    snap.mkdir()
    (snap / "chat_template.jinja").write_text("{{ messages }}")
    (snap / "model-00000-of-00002.safetensors").write_bytes(b"w" * 10)
    monkeypatch.setattr(sb, "snapshot", lambda local_only=True: snap)
    (tmp_path / "log").mkdir()
    (tmp_path / "log" / "snapshot.json").write_text(json.dumps({"revision": sb.REVISION, "files": [
        {"file": "model-00000-of-00002.safetensors", "bytes": 10}]}))
    from finetune.gpu import eval_job
    import transformers

    class FakeServer:
        def __init__(self, *a, cmd=None, **kw):
            seen["cmd"], seen["date"] = cmd, sb.os.environ.get("VLLM_SYSTEM_START_DATE")

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False
    monkeypatch.setattr(eval_job, "Server", FakeServer)
    monkeypatch.setattr(transformers.AutoTokenizer, "from_pretrained", lambda path, **kw: NS(decode=str))
    monkeypatch.delenv("VLLM_SYSTEM_START_DATE", raising=False)
    monkeypatch.setattr(sb, "server_ids", lambda url: lambda e, m, t: [1, 9] if m[0]["role"] == "system" else [1, 2])
    monkeypatch.setattr(sb, "local_ids", lambda tok: lambda e, m, t: [1, 2])
    monkeypatch.setattr(sb.subprocess, "call", lambda cmd, env, cwd: seen.setdefault("runner", cmd) and 0)
    assert sb.run(tmp_path / "log", smoke=True) == 4 and "runner" not in seen     # the check stops it before any run
    assert not json.loads((tmp_path / "b17" / "template_check.json").read_text())["ok"]
    cmd = seen["cmd"]
    assert cmd[:3] == ["vllm", "serve", str(snap)] and seen["date"] == sb.START_DATE
    assert cmd[cmd.index("--reasoning-parser") + 1] == "openai_gptoss" and cmd[cmd.index("--tool-call-parser") + 1] == "openai"
    assert cmd[cmd.index("--attention-backend") + 1] == "TRITON_ATTN" and cmd[cmd.index("--moe-backend") + 1] == "marlin"
    assert "--attention-backend" not in sb.serve_cmd("S", auto_backends=True)
    monkeypatch.setattr(sb, "server_ids", lambda url: lambda e, m, t: [1, 2])
    monkeypatch.setattr(rb, "export_flags", lambda: 0)
    monkeypatch.setattr(rb, "smoke_check", lambda rows: {"ok": True, "checks": {}, "median_output_tokens": {}})
    assert sb.run(tmp_path / "log", smoke=True) == 0
    assert seen["runner"][-4:] == ["--stop-file", str(tmp_path / "stop"), "--limit", "15"]
    assert json.loads((tmp_path / "b17" / "smoke_check.json").read_text())["ok"]


def test_the_download_job_takes_the_mxfp4_shards_only_and_checks_them(tmp_path, monkeypatch):
    import huggingface_hub
    from finetune.gpu import kit
    snap = tmp_path / "snap"
    snap.mkdir()
    (snap / "chat_template.jinja").write_text("T")
    (snap / "model-00000-of-00002.safetensors").write_bytes(b"weights")
    good = hashlib.sha256(b"weights").hexdigest()
    monkeypatch.setattr(sb, "snapshot", lambda local_only=True: snap)
    hub = {"lfs": good}

    class Api:
        def model_info(self, repo, revision, files_metadata):
            assert (repo, revision) == (sb.REPO, sb.REVISION)
            return NS(sha=sb.REVISION, siblings=[
                NS(rfilename="model-00000-of-00002.safetensors", lfs=NS(sha256=hub["lfs"]), blob_id="x"),
                NS(rfilename="chat_template.jinja", lfs=None, blob_id=kit.git_blob_id(snap / "chat_template.jinja")),
                NS(rfilename="original/model.safetensors", lfs=NS(sha256="0" * 64), blob_id="y"),
                NS(rfilename="metal/model.bin", lfs=NS(sha256="0" * 64), blob_id="z"),
                NS(rfilename="original/config.json", lfs=None, blob_id="w")])
    monkeypatch.setattr(huggingface_hub, "HfApi", Api)
    rec = sb.download(tmp_path / "log")
    assert [f["file"] for f in rec["files"]] == ["model-00000-of-00002.safetensors", "chat_template.jinja"]
    assert (tmp_path / "log" / sb.TEMPLATE_FILE).read_text() == "T" and rec["was_cached"]
    hub["lfs"] = "1" * 64
    with pytest.raises(SystemExit, match="doesn't match the Hub"):
        sb.download(tmp_path / "log2")


def test_the_real_chat_template_at_each_effort_if_cached():
    """With gpt-oss-20b's tokenizer in the local Hugging Face cache (no network): the effort and the pinned date reach
    the rendering, the system note becomes the developer message's instructions (as vLLM renders it), and the
    effort costs no prompt tokens."""
    transformers = pytest.importorskip("transformers")
    try:
        tok = transformers.AutoTokenizer.from_pretrained(sb.REPO, revision=sb.REVISION, local_files_only=True)
    except Exception:
        pytest.skip("gpt-oss-20b's tokenizer isn't cached here")
    rows = rb.template_rows(CFG)
    ids = sb.local_ids(tok)
    text = {(r["effort"], r["condition"]): tok.decode(ids(r["effort"], r["messages"], r["tools"])) for r in rows}
    assert "Reasoning: high" in text[("high", "none")] and "Reasoning: low" in text[("low", "none")]
    assert f"Current date: {sb.START_DATE}" in text[("low", "none")]
    assert "<|start|>developer<|message|># Instructions\n\nAnswer key note:" in text[("medium", "system")]
    assert "namespace functions" in text[("medium", "tool_real")]
    n = {k: len(ids(k[0], r["messages"], r["tools"])) for k, r in zip(text, rows)}
    assert all(n[("low", c)] == n[("high", c)] for c in CFG["conditions"])


def test_the_smokes_served_prompts_pass_the_check_if_cached():
    """The smoke 245445's failure (Nov 1), rebuilt from the real chat template: vLLM served the system condition as
    ours without the blank line before the developer message's <|end|> (379 tokens each, template_check.json). The
    check reads that as whitespace only; every other prompt is identical."""
    transformers = pytest.importorskip("transformers")
    try:
        tok = transformers.AutoTokenizer.from_pretrained(sb.REPO, revision=sb.REVISION, local_files_only=True)
    except Exception:
        pytest.skip("gpt-oss-20b's tokenizer isn't cached here")
    ours = sb.local_ids(tok)

    def served(effort, messages, tools):
        ids = ours(effort, messages, tools)
        if messages[0]["role"] != "system":
            return ids
        text = tok.decode(ids)
        end = text.index("<|end|>", text.index("<|start|>developer"))
        return tok.encode(text[:end].rstrip("\n") + text[end:], add_special_tokens=False)
    check = rb.template_check(CFG, served, ours, tok.decode)
    assert check["ok"]
    assert {(r["condition"], r["verdict"]) for r in check["rows"]} == \
        {(c, "identical") for c in CFG["conditions"] if c != "system"} | {("system", "whitespace only")}
    system = [r for r in check["rows"] if r["condition"] == "system"]
    assert {(r["server_tokens"], r["local_tokens"], r["first_difference"]) for r in system} == {(379, 379, 88)}
