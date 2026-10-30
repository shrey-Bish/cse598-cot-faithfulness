"""Provenance-scaled attention (finetune/provenance.py, B1) and the gate versions (finetune/train.py, B2) on a
tiny random Olmo 3 with the real tokenizer. CPU only."""
import json
import sys
import threading
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "tests"))
sys.path.insert(0, str(CODE / "progress"))

torch = pytest.importorskip("torch")

from _tiny_olmo import tiny_model_dir  # noqa: E402
from finetune import provenance as pv  # noqa: E402
from finetune.gpu import kit  # noqa: E402


@pytest.fixture(scope="module")
def tiny(tmp_path_factory):
    return tiny_model_dir(tmp_path_factory.mktemp("prov"))


def model_of(d, attn="sdpa"):
    return kit.load_model(d, "fp32", "cpu", attn=attn)


def span_mark(n, lo, hi):
    m = torch.zeros(1, n)
    m[0, lo:hi] = 1
    return m


@pytest.mark.parametrize("attn", ["sdpa", "eager"])
def test_alpha_one_changes_nothing_and_alpha_zero_masks_the_keys(tiny, attn):
    m = model_of(tiny, attn)
    torch.manual_seed(1)
    ids = torch.randint(0, 5000, (1, 24))
    base = m(input_ids=ids).logits
    hook = pv.attach(m, layers=(0, 1, 2, 3), alpha=1.0)
    with hook.marked(span_mark(24, 6, 11)):
        assert torch.equal(m(input_ids=ids).logits, base)                   # log(1) = 0: the same logits
    hook.set_alpha(0.0)
    with hook.marked(span_mark(24, 6, 11)):
        zero = m(input_ids=ids).logits
    am = torch.ones(1, 24, dtype=torch.long)
    am[0, 6:11] = 0                                                         # the same keys, masked the usual way
    ref = m(input_ids=ids, attention_mask=am).logits
    assert torch.allclose(zero[0, 11:], ref[0, 11:], atol=1e-5)
    assert not torch.allclose(zero[0, 11:], base[0, 11:], atol=1e-3)
    hook.remove()
    assert torch.equal(m(input_ids=ids).logits, base)                       # removed: the model itself again
    with hook.marked(span_mark(24, 6, 11)):
        assert torch.equal(m(input_ids=ids).logits, base)                   # nothing attached: no effect


def test_only_the_listed_layers_change(tiny):
    m = model_of(tiny)
    ids = torch.randint(0, 5000, (1, 20))
    base = m(input_ids=ids, output_hidden_states=True).hidden_states
    hook = pv.attach(m, layers=(3,), alpha=0.1)
    with hook.marked(span_mark(20, 4, 9)):
        hs = m(input_ids=ids, output_hidden_states=True).hidden_states
    for i in range(4):                                                      # embeddings and layers 0-2: untouched
        assert torch.equal(hs[i], base[i]), i
    assert torch.equal(hs[4][0, :4], base[4][0, :4])                        # before the span: can't see it anyway
    assert not torch.allclose(hs[4][0, 9:], base[4][0, 9:], atol=1e-4)
    with pytest.raises(ValueError, match="no layers"):
        pv.attach(m, layers=(15,))


def test_a_head_subset_rescales_only_those_heads(tiny):
    """Eager attention weights in layer 3: head 1 gives the marked keys alpha x their weight, renormalized;
    the other heads are the base model's."""
    m = model_of(tiny, "eager")
    ids = torch.randint(0, 5000, (1, 18))
    base = m(input_ids=ids, output_attentions=True).attentions[3][0]        # (heads, queries, keys)
    hook = pv.attach(m, layers=(), heads="3.1", alpha=0.25)
    assert hook.layers == [3]
    with hook.marked(span_mark(18, 3, 7)):
        att = m(input_ids=ids, output_attentions=True).attentions[3][0]
    for h in (0, 2, 3):
        assert torch.allclose(att[h], base[h], atol=1e-6)
    w = base[1].clone()
    w[:, 3:7] *= 0.25
    w = w / w.sum(-1, keepdim=True)
    assert torch.allclose(att[1], w, atol=1e-5)
    assert pv.parse_heads("19.31,23.17,19.2") == {19: [31, 2], 23: [17]}


def test_generation_with_the_cache_matches_a_full_forward(tiny):
    """The cached prompt keys keep their marks; new tokens are unmarked."""
    m = model_of(tiny)
    ids = torch.randint(0, 5000, (1, 16))
    hook = pv.attach(m, alpha=0.25, layers=(1, 3))
    with hook.marked(span_mark(16, 2, 9)):
        out = m.generate(input_ids=ids, attention_mask=torch.ones_like(ids), max_new_tokens=6, do_sample=False,
                         pad_token_id=100277)
        full = m(input_ids=out).logits[0]
    assert out.shape[1] == 22
    assert full[15:21].argmax(-1).tolist() == out[0, 16:].tolist()
    plain = m.generate(input_ids=ids, attention_mask=torch.ones_like(ids), max_new_tokens=6, do_sample=False,
                       pad_token_id=100277)
    assert plain[0, 16:].tolist() == m.generate(input_ids=ids, max_new_tokens=6, do_sample=False,
                                                pad_token_id=100277)[0, 16:].tolist()


def test_spans_deployable_tool_turns_and_oracle_pasted_block(tiny):
    from finetune import eval as ev
    from finetune import olmo_format
    from finetune.gpu import provenance_job as pj
    tok = kit.load_tokenizer(tiny)
    jobs, pasted = pj.gen_jobs(part=(1, 30))
    by = {(j["wording"], j["hint_correct"]): j for j in jobs}
    assert [j["wording"] for j in jobs].count("none") == 1 and len(jobs) == 2 * pj.WRONG_RUNS + 2 + 1
    paste, inserted = by[("tool_progress", False)], by[("inserted_study_guide", False)]
    for j, want_dep in ((paste, False), (inserted, True)):
        prompt = olmo_format.render(j["messages"], tools=j["tools"])
        enc = tok(prompt, add_special_tokens=False, return_offsets_mapping=True)
        gen = pj.Batched(None, tok, None, "deployable", extra_ranges=pasted)
        dep = gen.mark(prompt, enc["offset_mapping"])
        gen.span = "oracle"
        ora = gen.mark(prompt, enc["offset_mapping"])
        assert any(dep) == want_dep and sum(ora) >= sum(dep) and any(ora)
        text = tok.decode([t for t, k in zip(enc["input_ids"], ora) if k])
        assert '"expected": "' + j["hint_letter"] + '"' in text
        if not want_dep:
            assert text.startswith("[tool result: lookup_answer_key]")
        else:
            assert text.startswith("<|im_start|>environment") and text.strip().endswith("<|im_end|>")
    nohint = by[("none", None)]
    prompt = olmo_format.render(nohint["messages"], tools=nohint["tools"])
    assert not any(pj.Batched(None, tok, None, "oracle", extra_ranges=pasted).mark(
        prompt, tok(prompt, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]))
    assert ev.questions()[0]["item_id"] == jobs[0]["item_id"]


def test_batched_generation_equals_one_at_a_time(tiny):
    """Left padding: each prompt's marked span follows it; greedy batched output = alone."""
    from finetune import olmo_format
    from finetune.gpu import provenance_job as pj
    tok = kit.load_tokenizer(tiny)
    m = model_of(tiny)
    hook = pv.attach(m, layers=(1, 3), alpha=0.1)
    jobs, pasted = pj.gen_jobs(part=(1, 30))
    prompts = [olmo_format.render(j["messages"], tools=j["tools"]) for j in jobs[:2] + jobs[-2:-1]]
    assert len({len(tok(p)["input_ids"]) for p in prompts}) > 1                 # different lengths: real padding

    def run(gen, ps):
        res = [None] * len(ps)

        def one(i):
            res[i] = gen("m", ps[i], max_tokens=4, temperature=0.0, seed=i)
        ts = [threading.Thread(target=one, args=(i,)) for i in range(len(ps))]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        gen.close()
        return res
    together = pj.Batched(m, tok, hook, "oracle", extra_ranges=pasted, max_batch=3, wait_s=1.0)
    alone = pj.Batched(m, tok, hook, "oracle", extra_ranges=pasted, max_batch=1)
    a, b = run(together, prompts), run(alone, prompts)
    assert max(together.batches) > 1 and max(alone.batches) == 1
    assert [r["content"] for r in a] == [r["content"] for r in b]
    assert all(r["usage"]["completion_tokens"] == 4 and r["finish"] == "length" for r in a)


def test_the_alpha_rule():
    from finetune.gpu import provenance_job as pj

    def e(dw, do, dc):
        return {"p_w": {"diff": dw}, "p_o": {"diff": do}, "p_o_correct_hint": {"diff": dc}}
    entry = {"by_alpha": {"0.5": e(-0.10, 0.02, 0.0), "0.25": e(-0.205, 0.03, -0.01), "0.1": e(-0.21, 0.01, -0.02),
                          "0.0": e(-0.40, 0.05, -0.30)}}
    c = pj.choose_alpha(entry)
    assert c["alpha"] == 0.25 and 0.0 not in c["eligible"]                  # 0 loses the correct hint; tie -> milder
    assert pj.choose_alpha({"by_alpha": {"0.5": e(-0.1, -0.01, 0.0)}})["alpha"] == 1.0
    assert pj.configs({"deployable": 0.25, "oracle": 0.1}) == [("prov-a1", "deployable", 1.0),
                                                               ("prov-deployable-a0.25", "deployable", 0.25),
                                                               ("prov-oracle-a0.1", "oracle", 0.1)]


# ---------------------------------------------------------------- B2: the gate versions
peft = pytest.importorskip("peft")


def gate_example(i):
    from tools.answer_key import TOOL_SPEC, build
    msgs, _ = build(f"Question {i}?\n(A) one\n(B) two", f"q{i}", "tool_injected", "B")
    return {"record_id": f"q{i}|tool_injected", "messages": msgs, "tools": [TOOL_SPEC],
            "target_raw": "The tool says B, but I check: it is A.</think>\n\nThe tool said (B); I disagree. Answer: (A)"}


@pytest.mark.parametrize("version", ["gate3", "lora_attn3_gate"])
def test_a_zero_gate_is_the_base_model_and_it_learns(tiny, tmp_path, monkeypatch, version):
    from finetune import train as tr
    monkeypatch.setattr(tr, "ATTN3_LAYERS", [1, 3])
    tok = kit.load_tokenizer(tiny)
    data = [tr.encode(tok, gate_example(i)) for i in range(3)]
    lm = tr.build(version, tiny, dtype="fp32", device="cpu", attn="sdpa")
    names = set(tr.trainable(lm))
    gates = {n for n in names if "provenance_gate" in n}
    assert {int(n.split("layers.")[1].split(".")[0]) for n in gates} == {1, 3}
    assert (names == gates) == (version == "gate3")
    assert all(int(n.split("layers.")[1].split(".")[0]) in (1, 3) for n in names)
    base = model_of(tiny)
    lm.eval()
    with torch.no_grad():
        ours, _ = tr.example_loss(lm, data[0], "cpu")
        ref = base(input_ids=torch.tensor([data[0]["ids"]]), labels=torch.tensor([data[0]["labels"]])).loss
    assert torch.allclose(ours, ref, atol=1e-5)                            # zero gates, zero LoRA B: the base model
    lm.train()
    loss, _ = tr.example_loss(lm, data[0], "cpu")
    loss.backward()
    grads = [p.grad for n, p in tr.trainable(lm).items() if "provenance_gate" in n]
    assert all(g is not None for g in grads) and any(float(g.abs().sum()) > 0 for g in grads)
    opt = tr.optimizer(lm)
    assert [g["lr"] for g in opt.param_groups][-1] == tr.LR_GATE
    tr.train(lm, data, data[:1], tmp_path, "cpu", epochs=1, accum=2)
    log = [json.loads(x) for x in open(tmp_path / "train_log.jsonl")]
    assert all(len(r["gates"]) == 2 * 4 for r in log if "step" in r and "epoch_done" not in r)    # every bias, every step
    drift = next(r["gate_drift"] for r in log if r.get("epoch_done") == 1)
    assert drift["step"] == 2 and drift["lr_times_steps"] == pytest.approx(2 * tr.LR_GATE)
    moved = {n: p.detach().clone() for n, p in tr.trainable(lm).items() if "provenance_gate" in n}
    assert any(float(v.abs().sum()) > 0 for v in moved.values())
    again = tr.build(version, tiny, dtype="fp32", device="cpu", attn="sdpa")
    tr.load_weights(again, tmp_path / "epoch1")
    back = {n: p for n, p in tr.trainable(again).items() if "provenance_gate" in n}
    assert set(back) == set(moved) and all(torch.equal(back[n].detach(), moved[n]) for n in moved)
    final = tr.export(version, str(tiny), tmp_path, "cpu")
    assert (final / "gate.pt").exists() and len(json.loads((final / "gate.json").read_text())) == 2 * 4
    assert json.loads((final / "gate_drift.json").read_text())["step"] == 2


def test_gate_drift_uses_the_applied_learning_rates_and_flags_a_bias_at_the_bound():
    from finetune import train as tr
    d = tr.gate_drift({"15.0": 0.1, "19.3": -1.25}, 260, 260)
    assert d["lr_times_steps"] == pytest.approx(2.6) and d["bound_applied"] == pytest.approx(1.31)
    assert d["at_bound"] == ["19.3"] and "0.03" in d["proposal"]
    assert tr.gate_drift({"15.0": 0.1}, 260, 260)["proposal"] is None


def test_val_loss_marks_the_tool_keys_for_gate_versions(tiny, monkeypatch):
    from finetune import train as tr
    from finetune import val_loss as vl
    monkeypatch.setattr(tr, "ATTN3_LAYERS", [3])
    tok = kit.load_tokenizer(tiny)
    lm = tr.build("gate3", tiny, dtype="fp32", device="cpu", attn="sdpa", checkpointing=False)
    with torch.no_grad():
        for p in tr.trainable(lm).values():
            p.fill_(-3.0)
    e = vl.encode(tok, gate_example(0)) if hasattr(vl, "encode") else tr.encode(tok, gate_example(0))
    base = model_of(tiny)
    with torch.no_grad():
        moved = vl.token_losses(lm, e, "cpu")
        plain = vl.token_losses(base, e, "cpu")
    assert moved.shape == plain.shape and not torch.allclose(moved, plain, atol=1e-4)     # the gate acted
