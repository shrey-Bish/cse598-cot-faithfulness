"""Track A: provenance-scaled attention. A fix that acts where the mechanism lives (F11, F12: layers 15,
19 and 23 read the hint's letter straight from the prompt).

In chosen layers (default the readout layers 15, 19, 23), every query's attention logit to a key in a
marked span gets a bias b_h added (per head h, before the softmax):
  B1, at inference (training-free): b_h = log(alpha) for the chosen heads (all heads, or a subset such as
      "19.31,23.17,15.31"), 0 for the others; alpha in {1, 0.5, 0.25, 0.1, 0}. alpha = 1 is the model
      itself; alpha = 0 masks the span (b = NEG). Scaling a key's attention weight by alpha before
      renormalizing is exactly adding log(alpha) to its logit.
  B2, trained (gate versions in finetune/train.py): b_h is a learned scalar per head, zero-initialized,
      for keys tagged "tool" by the source tags (finetune/source_tags.py): the model starts as the base
      model and learns how much these layers should read tool text.
Marked spans:
  deployable  the tool-role tokens: every environment turn (the inserted tool turn), which a serving
              system can identify from the conversation's roles
  oracle      the deployable span plus the pasted tool block inside the user turn, which a system can't
              identify in general (reported separately)

How (no query x key mask is built, so 32k-token contexts stay on sdpa's efficient kernels): queries get
an extra constant dimension 1 and keys an extra dimension b_h * marked(key) / scaling, so
q'.k' * scaling = q.k * scaling + b_h * marked(key); both are padded with zeros to a multiple of 8,
values with zeros, and the output's extra dimensions are dropped. It runs after the KV cache update,
so during generation the cached prompt keys keep their marks and new tokens (positions past the marked
prompt) are unmarked. The wrapped attention functions ("sdpa", "eager") pass every module without an
attached provenance straight to the original: other models and layers are untouched.

  hook = attach(model, layers=(15, 19, 23), heads=None, alpha=0.25)    # B1
  with hook.marked(mask):                                              # (batch, tokens) 0/1
      model(input_ids=...)
  gates = attach_gate(model)                                           # B2: zero-initialized parameters
  set_sources(model, src)                                              # mark the tool-tagged tokens
"""
import math
import re
import sys
from contextlib import contextmanager
from difflib import SequenceMatcher
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

READOUT = (15, 19, 23)                 # F11: 0.90 of the drop in hint-token restoration at the takeover
ALPHAS = (1.0, 0.5, 0.25, 0.1, 0.0)
NEG = -1e4                             # alpha = 0: a logit this low gets weight exp(-1e4) = 0
TOOL = 2                               # source_tags.SOURCES["tool"]
_ORIGINAL = {}


# ---------------------------------------------------------------- the attention wrapper
def install():
    """Wrap the "sdpa" and "eager" attention functions once (idempotent). Modules without an attached
    provenance go to the original function unchanged."""
    if _ORIGINAL:
        return
    from transformers.modeling_utils import AttentionInterface
    _ORIGINAL["sdpa"] = AttentionInterface._global_mapping["sdpa"]
    AttentionInterface._global_mapping["sdpa"] = _wrapped("sdpa")
    AttentionInterface._global_mapping["eager"] = _wrapped("eager")


def _eager_of(module):
    """The model file's own eager attention (each modeling file defines one)."""
    fn = getattr(sys.modules[type(module).__module__], "eager_attention_forward", None)
    if fn is None:
        raise RuntimeError(f"{type(module).__name__}: no eager_attention_forward in {type(module).__module__}")
    return fn


def _wrapped(kind):
    def attention(module, query, key, value, attention_mask, *args, **kwargs):
        orig = _ORIGINAL["sdpa"] if kind == "sdpa" else _eager_of(module)
        prov = getattr(module, "_provenance", None)
        mark = prov["state"].mark if prov else None
        if prov is None or mark is None:
            return orig(module, query, key, value, attention_mask, *args, **kwargs)
        scaling = kwargs.get("scaling", module.scaling)
        q2, k2, v2, d = augment(module, query, key, value, prov["bias"](), mark, scaling)
        out, weights = orig(module, q2, k2, v2, attention_mask, *args, **kwargs)
        return out[..., :d], weights
    attention.provenance_wrapper = kind
    return attention


def augment(module, query, key, value, bias, mark, scaling):
    """(query', key', value', head dim): one extra dimension (1 for queries, bias_h * mark / scaling for
    keys), zero-padded to a multiple of 8. bias: (heads,); mark: (batch, marked tokens) 0/1, extended
    with zeros to the key length (generated tokens are never marked)."""
    import torch
    import torch.nn.functional as F
    b, h, q_len, d = query.shape
    kh, k_len = key.shape[1], key.shape[2]
    bias = bias.to(device=query.device, dtype=torch.float32)
    if kh != h:
        if not bool(torch.all(bias == bias[0])):
            raise ValueError(f"per-head bias needs one key head per query head ({h} heads, {kh} key heads)")
        bias = bias[:kh]
    mark = mark.to(device=query.device, dtype=torch.float32)
    mark = F.pad(mark, (0, k_len - mark.shape[1])) if mark.shape[1] < k_len else mark[:, :k_len]
    if mark.shape[0] != b:
        if mark.shape[0] != 1:
            raise ValueError(f"mark has batch {mark.shape[0]}, the attention {b}")
        mark = mark.expand(b, -1)
    pad = 8 - d % 8 if d % 8 else 8
    col = bias.view(1, -1, 1) * mark.view(b, 1, k_len) / scaling                     # (batch, key heads, keys)
    k_extra = torch.zeros(b, kh, k_len, pad, device=key.device, dtype=key.dtype)
    k_extra[..., 0] = col.to(key.dtype)
    q_extra = torch.zeros(b, h, q_len, pad, device=query.device, dtype=query.dtype)
    q_extra[..., 0] = 1
    v_extra = torch.zeros(b, value.shape[1], k_len, pad, device=value.device, dtype=value.dtype)
    return torch.cat([query, q_extra], -1), torch.cat([key, k_extra], -1), torch.cat([value, v_extra], -1), d


# ---------------------------------------------------------------- attaching (B1) and gates (B2)
class _State:
    def __init__(self):
        self.mark = None


def attention_modules(model):
    """{layer index: attention module} of a (possibly PEFT-wrapped) causal LM."""
    m = model.get_base_model() if hasattr(model, "get_base_model") else model
    layers = m.get_decoder().layers
    return {i: layer.self_attn for i, layer in enumerate(layers)}


def parse_heads(spec):
    """"19.31,23.17" -> {19: [31], 23: [17]}."""
    out = {}
    for part in filter(None, (spec or "").split(",")):
        layer, head = part.strip().split(".")
        out.setdefault(int(layer), []).append(int(head))
    return out


class Hook:
    """B1: log(alpha) on the chosen layers' (and heads') attention to the marked tokens."""

    def __init__(self, model, layers=READOUT, heads=None, alpha=1.0):
        import torch
        install()
        self.model, self.state, self.mods = model, _State(), attention_modules(model)
        heads = parse_heads(heads) if isinstance(heads, str) else (heads or {})
        self.layers = sorted(set(layers) | set(heads))
        bad = [i for i in self.layers if i not in self.mods]
        if bad:
            raise ValueError(f"no layers {bad} in a {len(self.mods)}-layer model")
        self.masks = {}
        for i in self.layers:
            n = self.mods[i].config.num_attention_heads
            sel = torch.zeros(n)
            sel[heads.get(i, list(range(n)))] = 1.0
            self.masks[i] = sel
            self.mods[i]._provenance = {"state": self.state, "bias": (lambda i=i: self.masks[i] * self.log_alpha)}
        self.set_alpha(alpha)

    def set_alpha(self, alpha):
        if not 0 <= alpha <= 1:
            raise ValueError(f"alpha {alpha} outside [0, 1]")
        self.alpha = alpha
        self.log_alpha = NEG if alpha == 0 else math.log(alpha)
        return self

    @contextmanager
    def marked(self, mark):
        """Mark tokens (a (batch, tokens) or (tokens,) 0/1 tensor or list) for the calls inside."""
        self.state.mark = as_mark(mark)
        try:
            yield self
        finally:
            self.state.mark = None

    def remove(self):
        for i in self.layers:
            self.mods[i].__dict__.pop("_provenance", None)


def attach(model, layers=READOUT, heads=None, alpha=1.0):
    return Hook(model, layers, heads, alpha)


def as_mark(mark):
    import torch
    if mark is None:
        return None
    t = mark if isinstance(mark, torch.Tensor) else torch.tensor(mark, dtype=torch.float32)
    return (t[None] if t.dim() == 1 else t).float()


def attach_gate(model, layers=READOUT):
    """B2: a zero-initialized learned bias per head (float32 parameter `provenance_gate` on each chosen
    layer's attention), for keys tagged tool. Returns {layer: parameter}. Call after any PEFT wrapping, so
    the gates stay trainable."""
    import torch
    from torch import nn
    install()
    mods, state = attention_modules(model), _State()
    base = model.get_base_model() if hasattr(model, "get_base_model") else model
    base._provenance_state = state
    gates = {}
    for i in layers:
        attn = mods[i]
        p = next(attn.parameters())
        attn.provenance_gate = nn.Parameter(torch.zeros(attn.config.num_attention_heads, device=p.device,
                                                        dtype=torch.float32))
        attn._provenance = {"state": state, "bias": (lambda a=attn: a.provenance_gate)}
        gates[i] = attn.provenance_gate
    return gates


def has_gate(model):
    base = model.get_base_model() if hasattr(model, "get_base_model") else model
    return getattr(base, "_provenance_state", None) is not None


def set_sources(model, src):
    """B2: mark the tool-tagged tokens (source id TOOL) of the next forward; no-op without gates.
    src: one source id per token (a list, or a (batch, tokens) tensor)."""
    import torch
    base = model.get_base_model() if hasattr(model, "get_base_model") else model
    state = getattr(base, "_provenance_state", None)
    if state is None:
        return
    t = src if isinstance(src, torch.Tensor) else torch.tensor(src)
    state.mark = as_mark((t == TOOL).float())


def gate_values(model):
    """{"layer.head": learned bias} for the report."""
    return {f"{i}.{h}": float(v) for i, attn in attention_modules(model).items()
            if hasattr(attn, "provenance_gate") for h, v in enumerate(attn.provenance_gate.detach().cpu().tolist())}


# ---------------------------------------------------------------- spans
TURN = re.compile(r"<\|im_start\|>(system|user|assistant|environment)\n")


def tool_turns(text):
    """[(start, end)] characters of every environment (tool) turn in rendered Olmo text."""
    from finetune.source_tags import turn_spans
    return [(a, b) for role, a, b in turn_spans(text) if role == "environment"]


def inserted(base, hinted):
    """[(start, end)] characters of `hinted` that `base` doesn't have (the hint added to a message)."""
    out = []
    for op, _, _, j1, j2 in SequenceMatcher(None, base, hinted, autojunk=False).get_opcodes():
        if op in ("insert", "replace") and j2 > j1:
            out.append((j1, j2))
    return out


def token_mark(offsets, ranges):
    """0/1 per token: 1 when the token's characters overlap one of the ranges."""
    return [int(any(a < hi and b > lo for lo, hi in ranges)) for a, b in offsets]


def mark_for(offsets, text, span, extra=()):
    """deployable: the tool turns; oracle: also `extra` character ranges (the pasted block)."""
    if span not in ("deployable", "oracle"):
        raise ValueError(f"span {span!r}: deployable or oracle")
    ranges = tool_turns(text) + (list(extra) if span == "oracle" else [])
    return token_mark(offsets, ranges)
