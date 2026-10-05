"""Source tags on a tiny randomly initialised causal LM (CPU)."""
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from finetune.source_tags import SOURCES, SourceTaggedLM, source_ids_from_chat  # noqa: E402


def tiny_model():
    torch.manual_seed(0)
    cfg = transformers.LlamaConfig(vocab_size=64, hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                                   num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=64)
    return transformers.LlamaForCausalLM(cfg)


class StubTokenizer:
    """Renders each message as [role marker] + one token per word, like a chat template."""
    marker = {"system": 1, "user": 2, "tool": 3, "assistant": 4}

    def apply_chat_template(self, messages, tokenize=True, add_generation_prompt=False):
        ids = []
        for m in messages:
            ids += [self.marker[m["role"]]] + [10 + len(w) % 50 for w in m["content"].split()]
        if add_generation_prompt:
            ids += [self.marker["assistant"]]
        return ids


def test_source_ids_follow_role_spans():
    msgs = [{"role": "system", "content": "be careful"}, {"role": "user", "content": "what is it"},
            {"role": "tool", "content": "expected C"}, {"role": "assistant", "content": "it is B"}]
    ids, src = source_ids_from_chat(StubTokenizer(), msgs, add_generation_prompt=False)
    assert len(ids) == len(src) == 3 + 4 + 3 + 4
    assert src == [SOURCES["system"]] * 3 + [SOURCES["user"]] * 4 + [SOURCES["tool"]] * 3 + [SOURCES["model"]] * 4
    ids2, src2 = source_ids_from_chat(StubTokenizer(), msgs[:3], add_generation_prompt=True)
    assert src2[-1] == SOURCES["model"]          # the generation prompt belongs to the model


def test_shapes_zero_init_and_gradients():
    lm = SourceTaggedLM(tiny_model())
    ids = torch.randint(0, 64, (2, 7))
    src = torch.tensor([[0, 0, 1, 1, 2, 2, 3]] * 2)
    base = lm.model(input_ids=ids).logits
    out = lm(input_ids=ids, source_ids=src, labels=ids)
    assert out.logits.shape == (2, 7, 64)
    assert torch.allclose(out.logits, base, atol=1e-5)    # zero-initialised tags start as the base model
    out.loss.backward()
    assert lm.tags.weight.grad is not None and lm.tags.weight.grad.abs().sum() > 0


def test_tags_change_the_output_once_trained():
    lm = SourceTaggedLM(tiny_model())
    with torch.no_grad():
        lm.tags.weight.normal_(0, 0.5)
    ids = torch.randint(0, 64, (1, 6))
    as_user = lm(input_ids=ids, source_ids=torch.full((1, 6), SOURCES["user"])).logits
    as_tool = lm(input_ids=ids, source_ids=torch.full((1, 6), SOURCES["tool"])).logits
    assert not torch.allclose(as_user, as_tool)


def test_only_tags_and_unfrozen_parts_train():
    lm = SourceTaggedLM(tiny_model(), freeze_base=True)
    trainable = [n for n, p in lm.named_parameters() if p.requires_grad]
    assert trainable == ["tags.weight"]
