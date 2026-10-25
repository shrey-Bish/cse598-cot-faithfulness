"""Source tags as vLLM would run them (finetune/tags_vllm.py): a tiny Olmo 3 model on CPU."""
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")

from finetune.source_tags import SOURCES, SourceTaggedLM  # noqa: E402
from finetune import tags_vllm as tv  # noqa: E402


def tiny_olmo3(tied=False, seed=0):
    torch.manual_seed(seed)
    cfg = transformers.Olmo3Config(vocab_size=96, hidden_size=48, intermediate_size=96, num_hidden_layers=4,
                                   num_attention_heads=4, num_key_value_heads=4, max_position_embeddings=128,
                                   sliding_window=6, layer_types=["sliding_attention"] * 3 + ["full_attention"],
                                   tie_word_embeddings=tied)
    return transformers.Olmo3ForCausalLM(cfg).eval()


def tagged(model, lora=False):
    if lora:
        peft = pytest.importorskip("peft")
        model = peft.get_peft_model(model, peft.LoraConfig(r=4, lora_alpha=8, init_lora_weights=False,
                                                           target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                                                           "gate_proj", "up_proj", "down_proj"]))
        model = model.merge_and_unload()           # the same function, as vLLM applies an adapter
    lm = SourceTaggedLM(model)
    with torch.no_grad():
        lm.tags.weight.normal_(0, 0.5)             # trained tags, not the zero start
    return lm.eval()


def prompt():
    ids = torch.randint(0, 96, (1, 14))
    src = torch.tensor([[SOURCES["system"]] * 3 + [SOURCES["user"]] * 5 + [SOURCES["tool"]] * 4 +
                        [SOURCES["model"]] * 2])     # ... ending with the assistant header
    return ids, src


@pytest.mark.parametrize("lora", [False, True])
def test_folded_table_plus_prompt_embeddings_equal_the_tagged_model(lora):
    lm = tagged(tiny_olmo3(), lora)
    ids, src = prompt()
    gen = torch.randint(0, 96, (1, 9))             # some generated tokens, all tagged model
    full_ids = torch.cat([ids, gen], 1)
    full_src = torch.cat([src, torch.full_like(gen, SOURCES["model"])], 1)
    ref = lm(full_ids, full_src).logits
    folded = tv.folded_model(lm)
    embeds = torch.cat([tv.prompt_embeds(lm, ids, src), folded.get_input_embeddings()(gen)], 1)
    got = folded(inputs_embeds=embeds).logits
    assert torch.allclose(ref, got, atol=1e-5), (ref - got).abs().max()


@pytest.mark.parametrize("lora", [False, True])
def test_greedy_decoding_matches_token_for_token(lora):
    lm = tagged(tiny_olmo3(seed=1), lora)
    ids, src = prompt()
    want = tv.tagged_greedy(lm, ids, src, 12)
    got = tv.folded_greedy(tv.folded_model(lm), tv.prompt_embeds(lm, ids, src), 12)
    assert torch.equal(want, got)


def test_the_prompt_must_keep_its_own_tags():
    lm = tagged(tiny_olmo3(seed=2))
    ids, src = prompt()
    folded = tv.folded_model(lm)
    plain = folded(input_ids=ids).logits           # prompt embedded by the folded table: all tagged model
    assert not torch.allclose(lm(ids, src).logits, plain, atol=1e-4)


def test_folding_refuses_tied_embeddings():
    with pytest.raises(ValueError, match="tied"):
        tv.folded_model(tagged(tiny_olmo3(tied=True)))
