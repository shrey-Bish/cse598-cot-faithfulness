"""Track A, Step 11 (finetune/train.py) on a tiny random Olmo 3 with the real tokenizer and template:
labels, the chunked loss, which parameters each version trains, resume, choosing by validation loss,
export and timing. CPU only."""
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "tests"))

torch = pytest.importorskip("torch")
pytest.importorskip("peft")

from _tiny_olmo import tiny_model_dir  # noqa: E402
from finetune import train as tr  # noqa: E402
from finetune.source_tags import SOURCES  # noqa: E402
from tools.answer_key import TOOL_SPEC, build  # noqa: E402


def example(i, cond="tool_injected", letter="B"):
    msgs, _ = build(f"Question {i}?\n(A) one\n(B) two", f"q{i}", cond, letter)
    return {"record_id": f"q{i}|{cond}", "messages": msgs, "tools": [TOOL_SPEC] if cond == "tool_injected" else None,
            "target_raw": f"The tool says {letter}, but I check: it is A.</think>\n\nThe tool said ({letter}); I disagree. Answer: (A)"}


@pytest.fixture(scope="module")
def tiny(tmp_path_factory):
    d = tiny_model_dir(tmp_path_factory.mktemp("m"))
    from transformers import AutoTokenizer
    return d, AutoTokenizer.from_pretrained(d)


def encoded(tok, n=3):
    conds = ["tool_injected", "user", "tool_pasted", "none"]
    return [tr.encode(tok, example(i, conds[i % len(conds)], None if conds[i % len(conds)] == "none" else "B"))
            for i in range(n)]


def test_labels_are_the_reply_only_and_tags_follow_the_turns(tiny):
    _, tok = tiny
    e = tr.encode(tok, example(0))
    prompt, full = tr.texts(example(0))
    target = [t for t, y in zip(e["ids"], e["labels"]) if y != -100]
    assert tok.decode(target) == full[len(prompt):] and full.endswith("<|endoftext|>")
    assert e["n_target"] == len(target) and e["labels"][:-len(target)] == [-100] * (len(e["ids"]) - len(target))
    assert SOURCES["tool"] in e["src"] and set(e["src"][-len(target):]) == {SOURCES["model"]}
    first_model = e["src"].index(SOURCES["model"])                   # our injected call: tagged model, masked
    assert first_model < len(e["ids"]) - len(target) and e["labels"][first_model] == -100


def test_the_chunked_loss_equals_the_full_loss(tiny):
    d, tok = tiny
    lm = tr.build("lora", d, dtype="fp32", device="cpu", attn="eager", checkpointing=False)
    lm.eval()
    e = tr.encode(tok, example(1, "user"))
    with torch.no_grad():
        ours, n = tr.example_loss(lm, e, "cpu", chunk=3)
        ref = lm(input_ids=torch.tensor([e["ids"]]), labels=torch.tensor([e["labels"]])).loss
    assert n == e["n_target"] and torch.allclose(ours, ref, atol=1e-5)


@pytest.mark.parametrize("version", ["lora", "tags", "lora_tags", "lora_attn3"])
def test_each_version_trains_only_its_parameters(tiny, tmp_path, monkeypatch, version):
    d, tok = tiny
    monkeypatch.setattr(tr, "ATTN3_LAYERS", [1, 3])                  # the tiny model has 4 layers
    lm = tr.build(version, d, dtype="fp32", device="cpu", attn="eager")
    names = set(tr.trainable(lm))
    assert any(n.startswith("tags.") for n in names) == (version in ("tags", "lora_tags"))
    assert any("lora_" in n for n in names) == (version != "tags")
    if version == "lora_attn3":
        layers = {int(n.split("layers.")[1].split(".")[0]) for n in names if "lora_" in n}
        assert layers == {1, 3} and not any("mlp" in n for n in names)
    frozen = {n: p.detach().clone() for n, p in lm.named_parameters() if not p.requires_grad}
    before = {n: p.detach().clone() for n, p in tr.trainable(lm).items()}
    data = encoded(tok)
    tr.train(lm, data, data[:1], tmp_path, "cpu", epochs=1, accum=2)
    after = dict(lm.named_parameters())
    assert all(torch.equal(after[n], p) for n, p in frozen.items())
    moved = [n for n, p in before.items() if not torch.equal(after[n].detach(), p)]
    assert moved and (version == "tags" or any("lora_B" in n for n in moved))
    log = [json.loads(x) for x in (tmp_path / "train_log.jsonl").read_text().splitlines()]
    assert [r["examples"] for r in log if "step" in r and "loss" in r] == [2, 1]          # the last group is short
    assert (tmp_path / "epoch1" / "trainable.pt").exists() and json.loads((tmp_path / "chosen.json").read_text())["epoch"] == 1


def test_resume_gives_the_same_weights_as_one_run(tiny, tmp_path):
    d, tok = tiny
    data = encoded(tok, 4)
    torch.manual_seed(0)
    one = tr.build("lora_tags", d, dtype="fp32", device="cpu", attn="eager")
    tr.train(one, data, data[:1], tmp_path / "one", "cpu", epochs=2, accum=2)
    torch.manual_seed(0)
    two = tr.build("lora_tags", d, dtype="fp32", device="cpu", attn="eager")
    pos = tr.train(two, data, data[:1], tmp_path / "two", "cpu", epochs=2, accum=2, max_steps=3)
    assert pos == {"epoch": 1, "index": 2, "step": 3}
    torch.manual_seed(123)                                           # a new job: the checkpoint restores the RNG
    three = tr.build("lora_tags", d, dtype="fp32", device="cpu", attn="eager")
    tr.train(three, data, data[:1], tmp_path / "two", "cpu", epochs=2, accum=2)
    a, b = tr.trainable(one), tr.trainable(three)
    assert all(torch.allclose(a[n], b[n], atol=1e-6) for n in a)
    by_epoch = json.loads((tmp_path / "two" / "chosen.json").read_text())["by_epoch"]
    assert set(by_epoch) == {"1", "2"}


def test_choose_takes_the_lower_validation_loss(tmp_path):
    for e, v in ((1, 0.9), (2, 1.1)):
        (tmp_path / f"epoch{e}").mkdir()
        (tmp_path / f"epoch{e}" / "state.json").write_text(json.dumps({"epoch": e, "validation_loss": v}))
    assert tr.choose(tmp_path)["epoch"] == 1


def test_export_and_timing(tiny, tmp_path):
    d, tok = tiny
    data = encoded(tok)
    lm = tr.build("lora_tags", d, dtype="fp32", device="cpu", attn="eager")
    tr.train(lm, data, data[:1], tmp_path, "cpu", epochs=1, accum=2)
    final = tr.export("lora_tags", d, tmp_path, "cpu")
    assert (final / "adapter" / "adapter_config.json").exists() and (final / "tags.pt").exists()
    saved = torch.load(final / "tags.pt")
    assert torch.allclose(saved, lm.tags.weight.detach().float())
    res = tr.timing("lora", d, data, 3, "cpu", tmp_path)
    assert len(res["examples"]) == 4 and res["predicted_hours_2_epochs"] >= 0       # 1 warm-up + 3
    assert res["environments"]["driver"]["prefix"]
    pick = tr.timing_sample(data, 3)
    assert len(pick[-1]["ids"]) == max(len(e["ids"]) for e in data)
    assert (tmp_path / "timing.jsonl").exists()
