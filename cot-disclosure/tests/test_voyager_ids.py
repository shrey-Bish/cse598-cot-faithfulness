"""Voyager's model IDs changed on 2026-10-21: the mapping and the client's guards. No network."""
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

import client  # noqa: E402

EXPECTED = {
    "olmo3-7b-instruct": ("olmo3-7b", "none"), "olmo3-7b-think": ("olmo3-7b", "medium"),
    "olmo3-32b-instruct": ("olmo3-32b", "none"), "olmo3-32b-think": ("olmo3-32b", "medium"),
    "qwen3-30b-a3b-instruct-2507": ("qwen3-30b-a3b", "none"),
    "qwen3-30b-a3b-thinking-2507": ("qwen3-30b-a3b", "medium"),
}
OLD_IDS = set(EXPECTED)


def test_each_old_name_maps_to_its_family_and_effort():
    assert client.VOYAGER_IDS == EXPECTED
    for name, (vid, effort) in EXPECTED.items():
        assert client.route(name) == (vid, effort)
        assert ("think" in name) == (effort != "none")          # guard a, in the mapping itself


def test_the_mapping_reads_the_same_without_pyyaml(monkeypatch):
    monkeypatch.setitem(sys.modules, "yaml", None)               # import yaml -> ImportError
    assert client.load_voyager_ids() == EXPECTED


def test_route_refuses_unsafe_requests(tmp_path):
    with pytest.raises(ValueError):
        client.route("olmo3-7b-think", "none")                  # a thinking model sent as instruct
    with pytest.raises(ValueError):
        client.route("olmo3-7b")                                # a family ID's default is instruct: say which
    assert client.route("olmo3-7b", "high") == ("olmo3-7b", "high")
    assert client.route("some-other-model") == ("some-other-model", None)
    bad = tmp_path / "models.yaml"
    bad.write_text("voyager_ids:\n  olmo3-7b-think: [olmo3-7b, none]\n")
    with pytest.raises(ValueError):
        client.load_voyager_ids(bad)


class FakeHTTP:
    """Stands in for urlopen: records each request body; streams one tiny reply."""
    def __init__(self, served="olmo3-7b-think"):
        self.bodies, self.served = [], served

    def __call__(self, request, timeout=None):
        body = json.loads(request.data) if request.data else {}
        self.bodies.append((request.full_url, body))
        served = self.served

        class Resp:
            def __enter__(s):
                return s

            def __exit__(s, *a):
                return False

            def __iter__(s):
                chunk = {"model": served, "choices": [{"text": " A", "delta": {"content": "A"}, "finish_reason": "stop"}]}
                return iter([f"data: {json.dumps(chunk)}".encode(), b"data: [DONE]"])

            def read(s):
                return json.dumps({"model": served, "choices": [{"message": {"content": "A"},
                                                                 "finish_reason": "stop"}], "usage": {}}).encode()
        return Resp()


@pytest.fixture
def http(monkeypatch, tmp_path):
    fake = FakeHTTP()
    monkeypatch.setattr(client.urllib.request, "urlopen", fake)
    monkeypatch.setattr(client, "CACHE_DIR", tmp_path)
    return fake


def test_no_code_path_sends_an_old_id(http):
    from providers import voyager
    msgs = [{"role": "user", "content": "q"}]
    for name, (vid, effort) in EXPECTED.items():
        client.chat(name, msgs, max_tokens=5, seed=1)
        client.chat(name, msgs, max_tokens=5, seed=2, stream=False)
        client.complete(name, "prompt", max_tokens=5, seed=3)
        list(client.chat_live(name, msgs, max_tokens=5, seed=4))
        voyager.generate(name, msgs, max_tokens=5, seed=5)
        sent = [b for _, b in http.bodies[-5:]]
        assert {b["model"] for b in sent} == {vid}, name
        assert {b["reasoning_effort"] for b in sent} == {effort}, name
    assert not any(b["model"] in OLD_IDS for _, b in http.bodies)
    assert {u.split("/v1", 1)[-1] for u, _ in http.bodies} == {"/chat/completions", "/completions"}


def test_results_and_records_carry_what_was_sent_and_what_answered(http):
    from common import make_record
    from providers import voyager
    from providers.base import route_fields
    out = client.complete("olmo3-7b-think", "prompt", max_tokens=5, seed=9)
    assert (out["requested_model_id"], out["reasoning_effort"], out["served_model"]) == ("olmo3-7b", "medium",
                                                                                          "olmo3-7b-think")
    rec = make_record(out, experiment="t", item_id=1, model="olmo3-7b-think", condition="none", repeat=0,
                      messages=[], n_options=4)
    assert rec["requested_model_id"] == "olmo3-7b" and rec["reasoning_effort"] == "medium"
    assert rec["served_model"] == "olmo3-7b-think" and rec["status"] == "ok"
    reply = voyager.generate("olmo3-7b-think", [{"role": "user", "content": "q"}], max_tokens=5, seed=10)
    assert route_fields(reply) == {"requested_model_id": "olmo3-7b", "reasoning_effort": "medium",
                                   "served_model": "olmo3-7b-think"}


CATALOG = [{"id": "olmo3-7b", "family": {"default_level": "none", "members": {
    "none": "olmo3-7b-instruct", "low": "olmo3-7b-think", "medium": "olmo3-7b-think", "high": "olmo3-7b-think"}}}]


def test_catalog_guard():
    client.check_catalog("olmo3-7b-think", CATALOG)
    client.check_catalog("olmo3-7b-instruct", CATALOG)
    with pytest.raises(client.ModelUnavailable):
        client.check_catalog("olmo3-32b-think", CATALOG)                     # family not listed
    moved = [{"id": "olmo3-7b", "family": {"members": {"medium": "olmo3-7b-think-v2"}}}]
    with pytest.raises(client.ModelUnavailable):
        client.check_catalog("olmo3-7b-think", moved)                        # the route serves something else


def lp(tokens, logprobs, tops):
    return [{"token": t, "logprob": l, "top_logprobs": {top: 0.0} if top else None}
            for t, l, top in zip(tokens, logprobs, tops)]


def test_canary_rule_is_strict():
    ref = lp(["a", "b", "c"], [None, -1.0, -2.0], [None, "b", "x"])
    assert client.compare_logprobs(ref, lp(["a", "b", "c", "!"], [None, -1.004, -2.0, -0.1], [None, "b", "x", "!"]))["pass"]
    assert not client.compare_logprobs(ref, lp(["a", "b", "c"], [None, -1.02, -2.0], [None, "b", "x"]))["pass"]
    assert not client.compare_logprobs(ref, lp(["a", "b", "c"], [None, -1.0, -2.0], [None, "b", "y"]))["pass"]
    assert not client.compare_logprobs(ref, lp(["a", "B", "c"], [None, -1.0, -2.0], [None, "b", "x"]))["pass"]


def test_a_failed_canary_stops_every_later_request(monkeypatch, tmp_path):
    ref = {"text": "t", "params": {"temperature": 0.6, "seed": 0}, "served_model": "olmo3-7b-think",
           "logprobs": lp(["a", "b"], [None, -1.0], [None, "b"])}
    (tmp_path / "olmo3-7b-think.json").write_text(json.dumps(ref))
    monkeypatch.setattr(client, "CANARY_DIR", tmp_path)
    monkeypatch.setattr(client, "CANARY_LOG", tmp_path / "canary.jsonl")
    monkeypatch.setattr(client, "GUARDS", True)
    monkeypatch.setattr(client, "list_models", lambda: CATALOG)
    good = {"error": None, "logprobs": lp(["a", "b", "z"], [None, -1.001, -0.5], [None, "b", "z"]),
            "served_model": "olmo3-7b-think", "requested_model_id": "olmo3-7b", "reasoning_effort": "medium"}
    monkeypatch.setattr(client, "canary_request", lambda name, r: good)
    client.preflight("olmo3-7b-think")                                       # passes, logged
    assert json.loads((tmp_path / "canary.jsonl").read_text())["pass"] is True
    monkeypatch.setattr(client, "_canary_at", {})                            # an hour later ...
    monkeypatch.setattr(client, "canary_request", lambda name, r: {**good, "served_model": "olmo3-7b-instruct"})
    with pytest.raises(client.CanaryFailed):
        client.preflight("olmo3-7b-think")
    monkeypatch.setattr(client, "canary_request", lambda name, r: good)
    with pytest.raises(client.CanaryFailed):                                 # halted for the rest of the process
        client.preflight("olmo3-7b-think")


def test_a_model_missing_from_the_catalog_stops_the_run(monkeypatch):
    monkeypatch.setattr(client, "GUARDS", True)
    monkeypatch.setattr(client, "list_models", lambda: [])
    with pytest.raises(client.ModelUnavailable):
        client.preflight("olmo3-7b-think")
    with pytest.raises(client.ModelUnavailable):
        client.chat("olmo3-7b-think", [{"role": "user", "content": "q"}], max_tokens=5, seed=77)


def test_idle_timeout_aborts_and_marks_the_run_not_run(monkeypatch, tmp_path):
    t = iter([0, 100, 700, 800])
    keepalive = [b": ping", b": ping", b": ping"]
    with pytest.raises(client.IdleTimeout):
        list(client.iter_stream_lines(keepalive, idle_s=600, clock=lambda: next(t)))
    monkeypatch.setattr(client, "CACHE_DIR", tmp_path)
    calls = []

    def stuck(payload, path):
        calls.append(1)
        raise client.IdleTimeout("no token for 600 s")
    monkeypatch.setattr(client, "_stream", stuck)
    out = client.complete("olmo3-7b-think", "p", max_tokens=5, seed=1, backoff=[0, 0, 0])
    assert out["error"].startswith("IdleTimeout") and len(calls) == 1      # not retried on the spot
    from common import make_record
    rec = make_record(out, experiment="t", item_id=1, model="olmo3-7b-think", condition="none", repeat=0,
                      messages=[], n_options=4)
    assert rec["status"] == "not_run" and rec["parsed_letter"] is None
    assert not list(tmp_path.glob("*.json"))                                # never cached


class FakeClock:
    """Stands in for the client's sleep and clock during an outage."""
    def __init__(self):
        self.t, self.slept = 0.0, []

    def sleep(self, s):
        self.slept.append(s)
        self.t += s

    def __call__(self):
        return self.t


def outage(monkeypatch, tmp_path, replies):
    """The canary's echo calls return `replies` in turn (an error string = no reply)."""
    ref = {"text": "t", "params": {"temperature": 0.6, "seed": 0}, "served_model": "olmo3-7b-think",
           "logprobs": lp(["a", "b"], [None, -1.0], [None, "b"])}
    (tmp_path / "olmo3-7b-think.json").write_text(json.dumps(ref))
    monkeypatch.setattr(client, "CANARY_DIR", tmp_path)
    monkeypatch.setattr(client, "CANARY_LOG", tmp_path / "canary.jsonl")
    monkeypatch.setattr(client, "GUARDS", True)
    monkeypatch.setattr(client, "list_models", lambda: CATALOG)
    good = {"error": None, "logprobs": lp(["a", "b", "z"], [None, -1.0, -0.5], [None, "b", "z"]),
            "served_model": "olmo3-7b-think", "requested_model_id": "olmo3-7b", "reasoning_effort": "medium"}
    it = iter(replies)

    def canary(name, r):
        x = next(it)
        return good if x == "ok" else ({**good, "served_model": x} if x.startswith("olmo") else
                                       {**good, "error": x, "logprobs": [], "served_model": None})
    monkeypatch.setattr(client, "canary_request", canary)
    clock = FakeClock()
    monkeypatch.setattr(client, "_sleep", clock.sleep)
    monkeypatch.setattr(client, "_clock", clock)
    return clock


def test_an_unreachable_canary_pauses_and_resumes(monkeypatch, tmp_path):
    clock = outage(monkeypatch, tmp_path, ["URLError", "HTTP 502", "ConnectionResetError", "ok"])
    client.preflight("olmo3-7b-think")                                       # no halt
    assert clock.slept == [120, 120, 120] and client._halted is None
    log = [json.loads(x) for x in (tmp_path / "canary.jsonl").read_text().splitlines()]
    assert [x["pass"] for x in log] == [None, None, None, True] and log[0]["unreachable"]


def test_unreachable_for_30_minutes_halts(monkeypatch, tmp_path):
    clock = outage(monkeypatch, tmp_path, ["URLError"] * 20)
    with pytest.raises(client.CanaryFailed, match="unreachable for 30 minutes"):
        client.preflight("olmo3-7b-think")
    assert sum(clock.slept) == 1800 and len(clock.slept) == 15
    with pytest.raises(client.CanaryFailed):
        client.preflight("olmo3-7b-think")                                    # halted for the rest of the run


def test_an_identity_mismatch_still_halts_at_once(monkeypatch, tmp_path):
    clock = outage(monkeypatch, tmp_path, ["URLError", "olmo3-7b-instruct"])
    with pytest.raises(client.CanaryFailed, match="identity"):
        client.preflight("olmo3-7b-think")
    assert clock.slept == [120]
    outage(monkeypatch, tmp_path, ["HTTP 404: model not found"])           # the server answered: a verdict
    monkeypatch.setattr(client, "_halted", None)
    with pytest.raises(client.CanaryFailed):
        client.preflight("olmo3-7b-think")


def test_requests_that_fail_in_transit_are_not_run_and_make_the_canary_due(monkeypatch, tmp_path):
    from common import status_of
    from providers.base import Reply, status_of as reply_status
    for err in ("URLError", "ConnectionResetError", "IncompleteStream", "TimeoutError", "HTTP 503", "HTTP 524",
                "HTTP 429", "IdleTimeout: no token for 600 s"):
        assert status_of({"error": err}) == "not_run", err
    for err in ("HTTP 400: error processing request body", "HTTP 404"):
        assert status_of({"error": err}) == "api_error", err
    assert reply_status(Reply("voyager", "m", error="URLError")) == "not_run"
    assert reply_status(Reply("voyager", "m", error="HTTP 400")) == "api_error"
    assert reply_status(Reply("openai", "m", error="BadRequestError: bad")) == "api_error"
    monkeypatch.setattr(client, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(client, "_canary_at", {"olmo3-7b-think": 10 ** 12})   # canary not due
    monkeypatch.setattr(client, "_stream", lambda payload, path: (_ for _ in ()).throw(client.urllib.error.URLError("x")))
    out = client.complete("olmo3-7b-think", "p", max_tokens=5, seed=1, backoff=[0, 0, 0])
    assert out["error"] == "URLError" and "olmo3-7b-think" not in client._canary_at   # next request checks first


def test_a_failed_canary_pauses_voyager_work_in_every_process(monkeypatch, tmp_path):
    """Oct 28: one process's failed canary writes client.HALT_FILE; a new process (fresh state) then
    refuses every Voyager request without a call until the file is removed."""
    monkeypatch.setattr(client, "GUARDS", True)
    monkeypatch.setattr(client, "CANARY_LOG", tmp_path / "canary.jsonl")
    monkeypatch.setattr(client, "list_models", lambda: CATALOG)
    bad = {"error": None, "logprobs": lp(["a", "b", "z"], [None, -1.001, -0.5], [None, "b", "z"]),
           "served_model": "olmo3-7b-instruct", "requested_model_id": "olmo3-7b", "reasoning_effort": "medium"}
    monkeypatch.setattr(client, "canary_request", lambda name, r: bad)
    with pytest.raises(client.CanaryFailed):
        client.preflight("olmo3-7b-think")
    assert "olmo3-7b-think: CanaryFailed" in client.HALT_FILE.read_text()
    calls = []
    monkeypatch.setattr(client, "_halted", None)                             # another process: fresh state
    monkeypatch.setattr(client, "_canary_at", {})
    monkeypatch.setattr(client, "canary_request", lambda name, r: calls.append(name))
    with pytest.raises(client.CanaryFailed, match="Voyager work is paused"):
        client.preflight("qwen3-30b-a3b-thinking-2507")
    assert calls == []
