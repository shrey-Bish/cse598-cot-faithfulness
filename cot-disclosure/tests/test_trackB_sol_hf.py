"""Track B's Qwen3-8B on Sol without vLLM (decided Oct 29): providers/sol_hf.py renders the snapshot's chat
template and parses the reply as the vLLM server did (--reasoning-parser qwen3, --tool-call-parser hermes),
sol_vllm hands its requests there once an engine is installed, a whole Track B run goes through a fake
engine, and progress/sol_trackB.py --engine hf runs the runner in-process. CPU only; no GPU, no network,
no model: the Qwen3-8B tokenizer from the local cache (skipped without it)."""
import json
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
from providers import sol_hf, sol_vllm  # noqa: E402
from tools.answer_key import TOOL_SPEC  # noqa: E402


@pytest.fixture(scope="module")
def qwen():
    from transformers import AutoTokenizer
    try:
        return AutoTokenizer.from_pretrained("Qwen/Qwen3-8B", revision=st.REVISION, local_files_only=True)
    except Exception:                                                        # noqa: BLE001
        pytest.skip("Qwen3-8B's tokenizer is not in the local cache")


@pytest.fixture(autouse=True)
def _no_engine_left():
    yield
    sol_hf.uninstall()


QUESTION = [{"role": "system", "content": "You are a careful student."}, {"role": "user", "content": "Q? (A) 1 (B) 2"}]
CALL = {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {
    "name": "lookup_answer_key", "arguments": json.dumps({"question_id": "x"})}}]}
RESULT = {"role": "tool", "tool_call_id": "c1", "name": "lookup_answer_key", "content": '{"expected": "B"}'}


def test_the_prompt_is_the_snapshots_template_as_vllm_renders_it(qwen):
    tpl = qwen.chat_template
    on = sol_hf.render(qwen, tpl, QUESTION, thinking=True)
    off = sol_hf.render(qwen, tpl, QUESTION, thinking=False)
    unset = sol_hf.render(qwen, tpl, QUESTION)
    assert on.endswith("<|im_start|>assistant\n") and on == unset                 # thinking on is the default
    assert off.endswith("<|im_start|>assistant\n<think>\n\n</think>\n\n")         # off: the empty think block
    tools = sol_hf.render(qwen, tpl, QUESTION, tools=[TOOL_SPEC], thinking=True)
    assert "# Tools" in tools and json.dumps(TOOL_SPEC, ensure_ascii=False) in tools   # the spec, in its order
    later = sol_hf.render(qwen, tpl, QUESTION + [CALL, RESULT], tools=[TOOL_SPEC], thinking=True)
    assert '<tool_call>\n{"name": "lookup_answer_key", "arguments": {"question_id": "x"}}\n</tool_call>' in later
    assert '<|im_start|>user\n<tool_response>\n{"expected": "B"}\n</tool_response><|im_end|>' in later
    # vLLM hands the template a mapping for the arguments and "" for a missing content: the same text
    as_vllm = [*QUESTION, {**CALL, "content": "", "tool_calls": [{**CALL["tool_calls"][0], "function": {
        "name": "lookup_answer_key", "arguments": {"question_id": "x"}}}]}, RESULT]
    assert later == qwen.apply_chat_template(as_vllm, tools=[TOOL_SPEC], chat_template=tpl, add_generation_prompt=True,
                                             tokenize=False, enable_thinking=True)
    assert sol_hf.vllm_messages([{**CALL, "tool_calls": [{**CALL["tool_calls"][0], "function": {
        "name": "f", "arguments": ""}}]}])[0]["tool_calls"][0]["function"]["arguments"] == {}


def test_the_qwen3_tags_survive_decoding(qwen):
    """The engine decodes without special tokens (as vLLM); Qwen3's think and tool-call tags aren't special."""
    ids = qwen("<think>\nhm\n</think>\n\n<tool_call>\n{}\n</tool_call>", add_special_tokens=False)["input_ids"]
    text = qwen.decode(ids + [qwen.convert_tokens_to_ids("<|im_end|>")], skip_special_tokens=True)
    assert text == "<think>\nhm\n</think>\n\n<tool_call>\n{}\n</tool_call>"


def test_the_reasoning_split():
    assert sol_hf.split_reasoning("<think>\nI check.\n</think>\n\nAnswer: (B)") == ("\nI check.\n", "\n\nAnswer: (B)", False)
    assert sol_hf.split_reasoning("Answer: (B)") == (None, "Answer: (B)", False)          # thinking off: no tags
    assert sol_hf.split_reasoning("I check.\n</think>\n\nB") == ("I check.\n", "\n\nB", False)  # no opening tag
    assert sol_hf.split_reasoning("<think>\nstill thinking") == ("\nstill thinking", None, True)   # cut at the cap
    assert sol_hf.split_reasoning("<think>\n\n</think>\n\n") == ("\n\n", "\n\n", False)
    assert sol_hf.split_reasoning("") == (None, None, False)


def test_tool_calls_as_the_hermes_parser():
    one = 'Let me check.\n<tool_call>\n{"name": "lookup_answer_key", "arguments": {"question_id": "x"}}\n</tool_call>'
    calls, rest = sol_hf.tool_calls(one)
    assert rest == "Let me check.\n" and [(c["name"], json.loads(c["arguments"])) for c in calls] == [
        ("lookup_answer_key", {"question_id": "x"})] and calls[0]["id"].startswith("chatcmpl-tool-")
    two = ('<tool_call>\n{"name": "a", "arguments": {}}\n</tool_call>\n<tool_call>\n{"name": "b", "arguments": '
           '{"k": "é"}}\n</tool_call>')
    calls, rest = sol_hf.tool_calls(two)
    assert rest is None and [c["name"] for c in calls] == ["a", "b"] and calls[1]["arguments"] == '{"k": "é"}'
    calls, _ = sol_hf.tool_calls('<tool_call>\n{"name": "a", "arguments": {"q": 1}}')        # unclosed: still a call
    assert [c["name"] for c in calls] == ["a"]
    for bad in ('x <tool_call>\n{"name": "a", "arguments": {</tool_call>',                  # not JSON
                '<tool_call>\n{"name": "a"}\n</tool_call>'):                                 # no arguments
        assert sol_hf.tool_calls(bad) == ([], bad)
    assert sol_hf.tool_calls("Answer: (B)") == ([], "Answer: (B)")
    text, reasoning, calls, finish, cut = sol_hf.parse("<think>\nr\n</think>\n\n" + one, "stop", tools=[TOOL_SPEC])
    assert (text, reasoning, finish, cut, len(calls)) == ("\n\nLet me check.\n", "\nr\n", "tool_calls", False, 1)
    text, _, calls, finish, _ = sol_hf.parse(one, "stop", tools=None)                        # no tools declared
    assert (text, calls, finish) == (one, [], "stop")


class FakeEngine:
    """The engine's complete_fn: answers from the prompt the way a Qwen3 reply would look."""
    kind, workers = "continuous", 7

    def __init__(self, error=None, cut=False):
        self.prompts, self.calls, self.closed, self.error, self.cut = [], [], False, error, cut

    def __call__(self, name, prompt, *, max_tokens, temperature=None, seed=None, backoff=None, extra=None):
        self.prompts.append(prompt)
        self.calls.append({"name": name, "max_tokens": max_tokens, "temperature": temperature, "seed": seed})
        if self.error:
            return {"content": "", "finish": "error", "error": self.error, "usage": {}}
        thinking = not prompt.endswith("<think>\n\n</think>\n\n")
        if self.cut:
            return {"content": "<think>\nThe hint says B but", "finish": "length", "error": None,
                    "usage": {"prompt_tokens": 300, "completion_tokens": max_tokens}}
        if "# Tools" in prompt and "<tool_response>" not in prompt:
            text = '<tool_call>\n{"name": "lookup_answer_key", "arguments": {"question_id": "x"}}\n</tool_call>'
        else:
            text = "Answer: (B)"
        if thinking:
            text = "<think>\nThe hint says B; I check it.\n</think>\n\n" + text
        return {"content": text, "finish": "stop", "error": None,
                "usage": {"prompt_tokens": 300, "completion_tokens": 120 if thinking else 20}}

    def close(self):
        self.closed = True


def config():
    c = yaml.safe_load((CODE / "configs" / "trackB.yaml").read_text())
    return {**c, "question_sets": {"pilot_puzzles": {"source": "pilot", "n": 2}}}


def test_a_track_b_run_through_the_hf_engine(qwen, tmp_path, monkeypatch):
    monkeypatch.setattr(tb, "OUT", tmp_path)
    eng = FakeEngine()
    sol_hf.install(eng, qwen, qwen.chat_template, "cd" * 32, {"top_p": 0.95, "top_k": 20})
    c = config()
    jobs = [j for j in tb.jobs(c, only_models=["qwen3-8b"]) if j["repeat"] == 0 and j["item"]["item_id"] == "pilot-0"]
    on = {j["condition"]: j for j in jobs if j["model"]["thinking"]}
    off = {j["condition"]: j for j in jobs if not j["model"]["thinking"]}
    rec = tb.run_one(c, on["tool_real"])
    first, second = eng.calls
    assert first["max_tokens"] == 32768 - rec["max_tokens"]["prompt_tokens_local"] and second["max_tokens"] == first["max_tokens"] - 120
    assert first["temperature"] == 0.6 and first["seed"] == 0 and first["name"] == "qwen3-8b"
    assert "# Tools" in eng.prompts[0] and "<tool_response>" in eng.prompts[1]               # the tool loop's two rounds
    assert rec["provider"] == "sol_vllm" and rec["engine"] == "hf-continuous" and rec["called_tool"]
    assert rec["parsed_letter"] == "B" and rec["reasoning_text"] and rec["reasoning_visibility"] == "full"
    assert rec["chat_template_sha256"] == "cd" * 32 and rec["total_output_tokens"] == 240
    assert rec["tool_steps"][0]["finish_reason"] == "tool_calls" and rec["final_text"] == "\n\nAnswer: (B)"
    rec_off = tb.run_one(c, off["none"])
    assert eng.prompts[-1].endswith("<think>\n\n</think>\n\n") and not rec_off["reasoning_text"]
    assert rec_off["final_text"] == "Answer: (B)" and rec_off["parsed_letter"] == "B"
    for r in (rec, rec_off):
        tb.save(r)
    assert tb.summary_row(rec)["engine"] == "hf-continuous"
    n = st.export_flags(records=tmp_path / "sol_vllm.jsonl.gz", out=tmp_path / "back" / "sol_vllm_flags.jsonl")
    assert n == 2 and {r["run_id"] for r in rep.load_flags(tmp_path / "back")} == {rec["run_id"], rec_off["run_id"]}


def test_a_reply_cut_inside_its_reasoning_and_an_engine_failure(qwen, tmp_path, monkeypatch):
    monkeypatch.setattr(tb, "OUT", tmp_path)
    c = config()
    j = next(j for j in tb.jobs(c, only_models=["qwen3-8b"]) if j["model"]["thinking"] and j["condition"] == "user")
    sol_hf.install(FakeEngine(cut=True), qwen, qwen.chat_template, "cd" * 32)
    rec = tb.run_one(c, j)
    assert rec["finish_reason"] == "length" and rec["parsed_letter"] is None and rec["status"] == "ok"
    assert rec["reasoning_text"] == "\nThe hint says B but" and rec["final_text"] == ""         # private, not a reply
    sol_hf.install(FakeEngine(error="continuous engine: the generation loop stopped"), qwen, qwen.chat_template, "cd" * 32)
    rec = tb.run_one(c, j)
    assert rec["status"] == "not_run" and "generation loop stopped" in rec["error_type"]       # retried, not "no answer"


def test_sol_vllm_hands_requests_to_the_installed_engine_only(monkeypatch):
    seen, real = [], sol_hf.generate
    monkeypatch.setattr(sol_hf, "generate", lambda *a, **k: seen.append(k) or "hf reply")
    monkeypatch.setattr(sol_vllm, "post_json", lambda *a, **k: (200, {"choices": [{"message": {"content": "A"},
                                                                                 "finish_reason": "stop"}]}))
    r = sol_vllm.generate("qwen3-8b", [], max_tokens=5)
    assert r.final_text == "A" and r.raw["engine"] == "vllm" and not seen                   # no engine: the server
    sol_hf.install(FakeEngine(), None, "T", "s")
    assert sol_vllm.generate("qwen3-8b", [], max_tokens=5, thinking=False) == "hf reply" and seen[0]["thinking"] is False
    sol_hf.uninstall()
    with pytest.raises(RuntimeError, match="no Hugging Face engine"):
        real("qwen3-8b", [], max_tokens=5)


def test_the_job_driver_with_the_hf_engine(tmp_path, monkeypatch):
    """--engine hf (the default): no vLLM preflight, the checked snapshot, the engine installed for the
    in-process runner (core-first, the engine's runs in flight, --limit), Slurm's warning, then closed."""
    monkeypatch.setenv("TRACKA_OUT", str(tmp_path))
    monkeypatch.setattr(st, "STOP", tmp_path / "stop")
    monkeypatch.setattr(st, "preflight", lambda *a: pytest.fail("no vLLM preflight with --engine hf"))
    snap = tmp_path / "snap"
    snap.mkdir()
    (snap / "tokenizer_config.json").write_text(json.dumps({"chat_template": "{{ messages }}"}))
    (snap / "model.safetensors").write_bytes(b"w" * 10)
    monkeypatch.setattr(st, "snapshot", lambda local_only=True: snap)
    with pytest.raises(SystemExit, match="run the download job first"):                    # no snapshot.json yet
        st.run([], tmp_path / "log")
    (tmp_path / "log").mkdir(exist_ok=True)
    (tmp_path / "log" / "snapshot.json").write_text(json.dumps({"revision": st.REVISION, "files": [
        {"file": "model.safetensors", "bytes": 10}]}))
    eng, seen, handlers = FakeEngine(), {}, {}

    def fake_engine_for(s, temperature, log=print):
        seen["snap"], seen["temperature"] = s, temperature
        return eng, "TOK", {"top_p": 0.95, "top_k": 20}

    def fake_run(cfg, all_jobs, limit=None, stop_file=None):
        seen.update(in_flight=tb.in_flight(cfg, "sol_vllm"), limit=limit, stop=stop_file, installed=sol_hf.active(),
                    template=sol_hf._STATE["template"], sha=sol_hf._STATE["template_sha256"],
                    models={(j["model"]["model"], j["model"]["thinking"]) for j in all_jobs},
                    first=[tb.phase(j, "core-first") for j in all_jobs[:3]])
        handlers["usr1"]()                                                                  # Slurm's warning
        return 2
    monkeypatch.setattr(st, "hf_engine_for", fake_engine_for)
    monkeypatch.setattr(tb, "run", fake_run)
    monkeypatch.setattr(st.signal, "signal", lambda sig, h: handlers.__setitem__("usr1", lambda: h(sig, None)))
    monkeypatch.setattr(st, "export_flags", lambda: 0)
    assert st.run(["--thinking", "off", "--limit", "5"], tmp_path / "log") == 2
    assert seen["snap"] == snap and seen["temperature"] == 0.6 and seen["installed"]
    assert seen["in_flight"] == eng.workers == 7 and seen["limit"] == 5 and seen["stop"] == str(tmp_path / "stop")
    assert seen["models"] == {("qwen3-8b", False)} and seen["first"] == [0, 0, 0]          # core-first
    assert seen["template"] == "{{ messages }}" and seen["sha"] == __import__("hashlib").sha256(b"{{ messages }}").hexdigest()
    assert eng.closed and not sol_hf.active() and (tmp_path / "stop").read_text() == "Slurm's time-limit warning"
    monkeypatch.setattr(sys, "argv", ["sol_trackB.py", "--run", "--log-dir", str(tmp_path / "log")])
    picked = []
    monkeypatch.setattr(st, "run", lambda extra, log_dir, engine="hf": picked.append(engine) or 0)
    with pytest.raises(SystemExit):
        st.main()
    monkeypatch.setattr(sys, "argv", ["sol_trackB.py", "--run", "--engine", "vllm"])
    with pytest.raises(SystemExit):
        st.main()
    assert picked == ["hf", "vllm"]                                                         # hf unless asked
