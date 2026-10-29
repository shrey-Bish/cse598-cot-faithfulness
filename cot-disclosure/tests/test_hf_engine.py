"""finetune/hf_engine.py on a tiny random Olmo 3 with the real tokenizer (CPU): continuous batching against
plain generate, stop strings, the static fallback, tags as token ids, sampling and sizing."""
import json
import sys
import threading
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "tests"))
sys.path.insert(0, str(CODE / "progress"))

torch = pytest.importorskip("torch")

from _tiny_olmo import tiny_model_dir  # noqa: E402
from finetune import hf_engine as he  # noqa: E402
from finetune import olmo_format  # noqa: E402
from finetune.gpu import kit  # noqa: E402

GREEDY = {"temperature": 0.0, "eos_ids": [100257, 100265]}


@pytest.fixture(scope="module")
def tiny(tmp_path_factory):
    return tiny_model_dir(tmp_path_factory.mktemp("hfe"))


@pytest.fixture(scope="module")
def loaded(tiny):
    return he.load(tiny, "cpu")


def prompts(tok):
    msgs = [[{"role": "user", "content": f"Question {i}: what is {i} + {i}?" + " Think step by step." * i}] for i in range(3)]
    return [olmo_format.render(m) for m in msgs]


def greedy_ref(model, tok, prompt, n):
    ids = tok(prompt, add_special_tokens=False)["input_ids"]
    x = torch.tensor([ids])
    with torch.no_grad():
        out = model.generate(input_ids=x, attention_mask=torch.ones_like(x), max_new_tokens=n, do_sample=False,
                             eos_token_id=GREEDY["eos_ids"], pad_token_id=tok.pad_token_id)
    return out[0, len(ids):].tolist()


def test_sampling_takes_only_what_the_snapshot_sets(tiny, loaded):
    _, tok = loaded
    s = he.sampling(tiny, tok, 0.6)
    assert s["temperature"] == 0.6 and 100257 in s["eos_ids"] and 100265 in s["eos_ids"]     # <|im_end|> ends a reply
    assert not set(s) & {"top_p", "top_k", "min_p", "repetition_penalty"}       # never Hugging Face's top_k=50
    (Path(tiny) / "generation_config.json").write_text(json.dumps({"eos_token_id": [100257, 100265], "top_p": 0.95,
                                                                     "temperature": 1.0}))
    try:
        s = he.sampling(tiny, tok, 0.6)
    finally:
        (Path(tiny) / "generation_config.json").unlink()
    assert s["temperature"] == 0.6 and s["top_p"] == 0.95 and "top_k" not in s


def test_continuous_batching_gives_plain_generate_tokens_with_many_callers(loaded):
    model, tok = loaded
    ps = prompts(tok)
    eng = he.Continuous(model, tok, GREEDY, workers=3)
    try:
        with ThreadPoolExecutor(3) as pool:
            got = list(pool.map(lambda p: eng("system", p, max_tokens=20, temperature=0.0), ps))
    finally:
        eng.close()
    for p, g in zip(ps, got):
        ref = greedy_ref(model, tok, p, 20)
        assert g["content"] == tok.decode(ref, skip_special_tokens=True)
        assert g["usage"] == {"prompt_tokens": len(tok(p, add_special_tokens=False)["input_ids"]), "completion_tokens": len(ref)}
        assert g["finish"] == ("length" if len(ref) == 20 and ref[-1] not in GREEDY["eos_ids"] else "stop")
        assert g["engine"] == "continuous" and g["error"] is None


def test_a_stop_string_ends_the_reply_after_the_string_and_frees_the_request(loaded):
    model, tok = loaded
    p = prompts(tok)[1]
    ref = greedy_ref(model, tok, p, 24)
    full = tok.decode(ref, skip_special_tokens=True)
    stop = tok.decode(ref[6:9], skip_special_tokens=True)
    assert stop and stop in full
    k = he.stop_index(tok, ref, [stop], 1)
    eng = he.Continuous(model, tok, GREEDY, workers=2)
    try:
        r = eng("system", p, max_tokens=24, temperature=0.0, extra={"stop": [stop], "include_stop_str_in_output": True})
        again = eng("system", p, max_tokens=5, temperature=0.0)               # the engine goes on after a cancel
    finally:
        eng.close()
    assert r["content"] == full[:full.find(stop) + len(stop)] and r["finish"] == "stop"
    assert r["usage"]["completion_tokens"] == k <= 9
    assert again["content"] == tok.decode(ref[:5], skip_special_tokens=True)


def test_the_static_fallback_gives_the_same_reply_fields(loaded):
    model, tok = loaded
    p = prompts(tok)[0]
    ref = greedy_ref(model, tok, p, 12)
    eng = he.static(model, tok, GREEDY, workers=2)
    try:
        r = eng("system", p, max_tokens=12, temperature=0.0)
    finally:
        eng.close()
    assert r["content"] == tok.decode(ref, skip_special_tokens=True) and r["engine"] == "static"
    assert r["usage"]["completion_tokens"] == len(ref)


def test_make_uses_continuous_batching_when_its_self_check_passes_and_falls_back_otherwise(loaded, monkeypatch):
    model, tok = loaded
    lines = []
    eng = he.make(model, tok, GREEDY, workers=2, log=lines.append)
    eng.close()
    assert eng.kind == "continuous" and eng.why == "self-check passed" and "passed" in lines[0]

    def broken(*a, **k):
        raise RuntimeError("no paged attention on this GPU")
    monkeypatch.setattr(model, "generate_batch", broken)
    eng = he.make(model, tok, {**GREEDY, "temperature": 0.6}, workers=2, log=lines.append, seed=3)
    try:
        r = eng("system", prompts(tok)[0], max_tokens=4, temperature=0.6)
    finally:
        eng.close()
    assert eng.kind == "static" and "RuntimeError" in eng.why and r["usage"]["completion_tokens"] <= 4


def test_a_failed_start_leaves_the_static_fallback_its_own_attention(loaded, monkeypatch):
    model, tok = loaded
    attn = model.config._attn_implementation

    def half_started(*a, **k):                                   # switched to paged attention, then failed
        model.set_attn_implementation(f"paged|{attn}")
        raise RuntimeError("cache allocation failed")
    monkeypatch.setattr(he, "Continuous", half_started)
    lines = []
    eng = he.make(model, tok, GREEDY, workers=2, log=lines.append, check=False)
    try:
        r = eng("system", prompts(tok)[0], max_tokens=4, temperature=0.0)
    finally:
        eng.close()
    assert eng.kind == "static" and "cache allocation failed" in eng.why and model.config._attn_implementation == attn
    assert r["error"] is None and r["usage"]["completion_tokens"] <= 4


def test_a_static_batch_that_raises_fails_its_runs_and_three_in_a_row_break_the_engine(loaded, monkeypatch):
    model, tok = loaded
    eng = he.static(model, tok, GREEDY, workers=2)
    real, boom = eng._generate, [True]

    def flaky(batch):
        if boom[0]:
            raise ValueError("paged|sdpa was called without a paged attention cache")
        return real(batch)
    monkeypatch.setattr(eng, "_generate", flaky)
    try:
        r = eng("system", prompts(tok)[0], max_tokens=4, temperature=0.0)          # an error reply, not a hang
        assert r["finish"] == "error" and "paged attention cache" in r["error"] and not eng.broken
        boom[0] = False
        assert eng("system", prompts(tok)[0], max_tokens=4, temperature=0.0)["error"] is None   # the loop goes on
        boom[0] = True
        for _ in range(3):
            eng("system", prompts(tok)[0], max_tokens=4, temperature=0.0)
        assert eng.broken and "3 batches in a row" in eng.broken
        boom[0] = False
        assert eng("system", "x", max_tokens=4)["finish"] == "error"                    # broken: fails at once
    finally:
        eng.close()


def test_tag_table_ids_give_training_inputs(tiny):
    from finetune.generate import Tagger
    from finetune.source_tags import SOURCES
    plain = kit.load_model(tiny, "fp32", "cpu")
    tagged, tok = he.load(tiny, "cpu")
    torch.manual_seed(5)
    tags = torch.randn(len(SOURCES), plain.config.hidden_size)
    table = he.TagTable.install(tagged, tok, tags)
    msgs = [{"role": "system", "content": "Be brief."}, {"role": "user", "content": "What is 2 + 2?"}]
    prompt = olmo_format.render(msgs) + "Let me add."
    ids, src = Tagger(tok, None, None).ids_and_sources(prompt)
    wide = table.ids(prompt)
    V = plain.get_input_embeddings().weight.shape[0]
    assert [i % V for i in wide] == ids and {i // V for i in wide} == {0, 1, 2}           # model, system, user blocks
    assert all(w < V for w, s in zip(wide, src) if s == SOURCES["model"])               # generated tokens: tag[model]
    emb = plain.get_input_embeddings()(torch.tensor([ids])) + tags[torch.tensor([src])]   # SourceTaggedLM.embed
    with torch.no_grad():
        want = plain(inputs_embeds=emb).logits
        got = tagged(input_ids=torch.tensor([wide])).logits
    assert torch.allclose(got, want, atol=1e-5)


def test_key_value_sizing_counts_sliding_layers_up_to_their_window():
    cfg = types.SimpleNamespace(num_key_value_heads=32, num_attention_heads=32, hidden_size=4096, head_dim=None,
                                num_hidden_layers=32, sliding_window=4096,
                                layer_types=(["sliding_attention"] * 3 + ["full_attention"]) * 8)
    per = he.kv_bytes_per_request(cfg, 12000)
    assert per == 8 * 2 * 32 * 128 * 2 * 12000 + 24 * 2 * 32 * 128 * 2 * 4096
    model = types.SimpleNamespace(config=cfg)
    assert he.workers_for(model, 63 * he.GiB) == int(0.8 * 63 * he.GiB // per) == 16
    assert he.workers_for(model, 1 * he.GiB) == 4 and he.workers_for(model, 10 ** 15) == 48


def test_a_dead_generation_loop_fails_the_waiting_runs_and_every_later_one():
    class Manager:
        def __init__(self):
            self.n = 0

        def start(self):
            pass

        def add_request(self, ids, **kw):
            self.n += 1
            return f"r{self.n}"

        def get_result(self, timeout=None):
            raise RuntimeError("CUDA error: an illegal memory access")

        def is_running(self):
            return False

        def stop(self, **kw):
            pass

    model = types.SimpleNamespace(init_continuous_batching=lambda **kw: Manager())
    tok = types.SimpleNamespace(pad_token_id=0, __call__=None)
    eng = he.Continuous(model, tok, {"temperature": 0.6, "eos_ids": [1]}, encode=lambda p: [5, 6], workers=2,
                        log=lambda s: None)
    done = []
    t = threading.Thread(target=lambda: done.append(eng("system", "x", max_tokens=8)))
    t.start()
    t.join(10)
    assert done and done[0]["finish"] == "error" and "illegal memory access" in done[0]["error"]
    assert eng.broken and eng("system", "y", max_tokens=8)["finish"] == "error"
    eng.close()
