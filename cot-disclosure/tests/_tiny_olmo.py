"""A tiny random Olmo 3 model with the real Olmo 3 vocabulary, for the GPU kit's CPU tests: real
prompts tokenize exactly as on the GPU, and the model is small enough for eager attention."""
import shutil
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

from finetune.gpu import kit  # noqa: E402


def olmo_tokenizer_dir():
    try:
        p, _ = kit.snapshot()
    except Exception:                                    # noqa: BLE001
        pytest.skip("the Olmo 3 tokenizer is not in the local Hugging Face cache")
    if not (p / "tokenizer.json").exists():
        pytest.skip("the Olmo 3 tokenizer is not in the local Hugging Face cache")
    return p


def tiny_config(layers=4, window=8, heads=4, kv_heads=4, hidden=32):
    transformers = pytest.importorskip("transformers")
    kinds = (["sliding_attention"] * 3 + ["full_attention"]) * (layers // 4)
    return transformers.Olmo3Config(vocab_size=100278, hidden_size=hidden, intermediate_size=2 * hidden,
                                    num_hidden_layers=layers, num_attention_heads=heads, num_key_value_heads=kv_heads,
                                    max_position_embeddings=4096, sliding_window=window, layer_types=kinds,
                                    tie_word_embeddings=False, pad_token_id=100277, eos_token_id=100257)


def tiny_model_dir(tmp_path, seed=0, **cfg):
    """Saved with the cached snapshot's tokenizer and chat template; loads like the real model."""
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    src = olmo_tokenizer_dir()
    torch.manual_seed(seed)
    model = transformers.Olmo3ForCausalLM(tiny_config(**cfg)).eval()
    d = tmp_path / "tiny-olmo3"
    model.save_pretrained(d)
    for f in ("tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "chat_template.jinja"):
        if (src / f).exists():
            shutil.copy(src / f, d / f)
    return d
