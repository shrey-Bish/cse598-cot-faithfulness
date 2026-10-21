"""Source tags: a small learned embedding added to every input token that marks where the
token came from (system, user, tool, model).

Why: attention treats every earlier token the same way, and role labels are just more
tokens. A per-token source vector gives the model a direct, learnable signal that a span
came from a tool. The tag table starts at zero, so a freshly wrapped model behaves exactly
like the base model until training moves it.

  lm = SourceTaggedLM(base_model)                 # or a PEFT/LoRA-wrapped model
  ids, src, spans = source_ids_from_render(tokenizer, olmo_format.render(messages))   # Olmo 3 (Track A)
  out = lm(input_ids=torch.tensor([ids]), source_ids=torch.tensor([src]), labels=...)

For Olmo 3 use source_ids_from_render: its template is not prefix-stable (a final assistant
turn ends in <|endoftext|>, a middle one in <|im_end|>), so source_ids_from_chat refuses it.

Generation with tags needs a decoding loop that tags each new token as "model"; that is
a documented later step (finetune/README.md).
"""
import re

import torch
from torch import nn

SOURCES = {"system": 0, "user": 1, "tool": 2, "model": 3}
ROLE_TO_SOURCE = {"system": "system", "user": "user", "tool": "tool", "assistant": "model",
                  "environment": "tool"}        # Olmo renders a tool reply as an environment turn
TURN = re.compile(r"<\|im_start\|>(system|user|assistant|environment)\n")


def turn_spans(text):
    """[(role, start, end)] character spans of each turn in rendered Olmo text: a turn runs
    from its <|im_start|> to the next one (so its <|im_end|> or <|endoftext|> belongs to it).
    The generation prompt "<|im_start|>assistant\n<think>" and anything generated after it
    are one more assistant turn."""
    starts = [(m.start(), m.group(1)) for m in TURN.finditer(text)]
    if not starts or starts[0][0] != 0:
        raise ValueError("rendered text must start with an <|im_start|>role header")
    return [(role, a, starts[i + 1][0] if i + 1 < len(starts) else len(text)) for i, (a, role) in enumerate(starts)]


def source_ids_from_render(tokenizer, text):
    """Token ids, one source id per token, and the turn spans, from rendered text (built from
    our own rendering, not by re-rendering prefixes). Every token must sit inside one turn:
    a token that crosses a turn boundary raises, so spans always line up with tokens.
    Tags: system prompt -> system; user turn (including a pasted hint) -> user; environment
    (tool reply) -> tool; assistant turns, including a tool call we write for it, and
    everything it generates -> model."""
    enc = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
    ids, offsets = list(enc["input_ids"]), list(enc["offset_mapping"])
    spans, src, j = turn_spans(text), [], 0
    out_spans = []
    for role, a, b in spans:
        first = j
        while j < len(ids) and offsets[j][0] < b:
            s, e = offsets[j]
            if s < a or e > b:
                raise ValueError(f"token {j} {text[s:e]!r} crosses the boundary of the {role} turn at {b}")
            src.append(SOURCES[ROLE_TO_SOURCE[role]])
            j += 1
        out_spans.append({"role": role, "source": ROLE_TO_SOURCE[role], "chars": (a, b), "tokens": (first, j)})
    if j != len(ids):
        raise ValueError("tokens left over after the last turn")
    return ids, src, out_spans


def _ids(rendered):
    if isinstance(rendered, dict) or hasattr(rendered, "keys"):
        rendered = rendered["input_ids"]
    if rendered and isinstance(rendered[0], list):
        rendered = rendered[0]
    return list(rendered)


def source_ids_from_chat(tokenizer, messages, add_generation_prompt=True):
    """Token ids for the chat and one source id per token, from the chat template's role
    spans: render the conversation one message longer each time and give the new tokens
    that message's source. Requires a template whose renderings are prefixes of each
    other (true for plain templates; some thinking templates rewrite earlier turns)."""
    ids, src = [], []
    for i, m in enumerate(messages):
        cur = _ids(tokenizer.apply_chat_template(messages[: i + 1], tokenize=True, add_generation_prompt=False))
        if cur[: len(ids)] != ids:
            raise ValueError(f"chat template is not prefix-stable at message {i}; tag spans by hand for this model")
        src += [SOURCES[ROLE_TO_SOURCE[m["role"]]]] * (len(cur) - len(ids))
        ids = cur
    if add_generation_prompt:
        full = _ids(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True))
        if full[: len(ids)] != ids:
            raise ValueError("generation prompt rewrites earlier tokens; tag spans by hand for this model")
        src += [SOURCES["model"]] * (len(full) - len(ids))
        ids = full
    return ids, src


class SourceTaggedLM(nn.Module):
    """Wraps a Hugging Face causal LM: inputs_embeds = token embeddings + tag(source)."""

    def __init__(self, model, n_sources=len(SOURCES), freeze_base=False):
        super().__init__()
        self.model = model
        emb = model.get_input_embeddings()
        self.tags = nn.Embedding(n_sources, emb.embedding_dim)
        nn.init.zeros_(self.tags.weight)                 # start as the base model
        if freeze_base:
            for p in self.model.parameters():
                p.requires_grad_(False)

    def embed(self, input_ids, source_ids):
        tok = self.model.get_input_embeddings()(input_ids)
        return tok + self.tags(source_ids).to(tok.dtype)

    def forward(self, input_ids, source_ids, attention_mask=None, labels=None, **kw):
        return self.model(inputs_embeds=self.embed(input_ids, source_ids), attention_mask=attention_mask,
                          labels=labels, **kw)
