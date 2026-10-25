"""Track A: can the source-tag versions run in vLLM? (the alternative to Step 12's own decoding loop)

A tagged model (source_tags.SourceTaggedLM) adds tag[source] to every input embedding. Every
generated token is tagged "model", so a plain engine reproduces it exactly with two changes:
  1. the input embedding table becomes E + tag[model]: every token vLLM embeds itself (all the
     generated ones) then carries the model tag. Only valid when the input and output
     embeddings are separate matrices: Olmo 3 7B has tie_word_embeddings false.
  2. the prompt is passed as precomputed embeddings (vLLM's prompt_embeds): each prompt
     position's ORIGINAL token embedding + its own source tag, so system, user and tool text
     keep their tags.
LoRA adapters on the attention and MLP projections are untouched by either change.
`folded_model` / `prompt_embeds` build the two inputs; tests/test_trackA_tags_vllm.py checks on a
tiny Olmo 3 model (CPU) that logits and greedy outputs equal the tagged model's. Whether vLLM
accepts prompt_embeds together with a LoRA adapter for Olmo 3 has to be checked on Sol (its
docs mark the pair compatible; see docs/PLAN.md, Track A, Step 12).
"""
import copy

import torch

from finetune.source_tags import SOURCES

MODEL = SOURCES["model"]


def check_untied(model):
    out, inp = model.get_output_embeddings(), model.get_input_embeddings()
    if out is not None and out.weight.data_ptr() == inp.weight.data_ptr():
        raise ValueError("input and output embeddings are tied: folding the model tag would change the output layer")


@torch.no_grad()
def folded_model(tagged):
    """A copy of the wrapped model whose input embedding table is E + tag[model]."""
    check_untied(tagged.model)
    model = copy.deepcopy(tagged.model)
    emb = model.get_input_embeddings()
    emb.weight += tagged.tags.weight[MODEL].to(emb.weight.dtype)
    return model


@torch.no_grad()
def prompt_embeds(tagged, input_ids, source_ids):
    """The prompt as vLLM's prompt_embeds: original token embeddings + each position's tag."""
    return tagged.embed(input_ids, source_ids)


@torch.no_grad()
def tagged_greedy(tagged, input_ids, source_ids, n):
    """Reference: greedy decoding with the tagged model, every generated token tagged as model."""
    ids, src = input_ids.clone(), source_ids.clone()
    for _ in range(n):
        logits = tagged(ids, src).logits[:, -1]
        nxt = logits.argmax(-1, keepdim=True)
        ids = torch.cat([ids, nxt], 1)
        src = torch.cat([src, torch.full_like(nxt, MODEL)], 1)
    return ids[:, input_ids.shape[1]:]


@torch.no_grad()
def folded_greedy(folded, embeds, n):
    """What vLLM would do: start from the prompt embeddings, embed each generated token with the
    folded table (a KV cache, as in serving)."""
    out, past, x = [], None, embeds
    for _ in range(n):
        res = folded(inputs_embeds=x, past_key_values=past, use_cache=True)
        past = res.past_key_values
        nxt = res.logits[:, -1].argmax(-1, keepdim=True)
        out.append(nxt)
        x = folded.get_input_embeddings()(nxt)
    return torch.cat(out, 1)
