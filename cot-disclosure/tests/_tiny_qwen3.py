"""A tiny random Qwen3 model with the real Qwen3-8B vocabulary and chat template (the pinned revision's, from
the local Hugging Face cache), for the Qwen3-8B Steps 3 and 10 CPU tests: real prompts tokenize exactly as on
the GPU, and the model is small enough for the CPU."""
import shutil
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

REPO, REVISION = "Qwen/Qwen3-8B", "b968826d9c46dd6066d109eabc6255188de91218"     # progress/sol_trackB.py's pin
FILES = ("tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt", "special_tokens_map.json",
         "chat_template.jinja")


def qwen_tokenizer_dir():
    try:
        from huggingface_hub import snapshot_download
        p = Path(snapshot_download(REPO, revision=REVISION, local_files_only=True))
    except Exception:                                    # noqa: BLE001
        pytest.skip("the Qwen3-8B tokenizer is not in the local Hugging Face cache")
    if not (p / "tokenizer.json").exists() or not (p / "tokenizer_config.json").exists():
        pytest.skip("the Qwen3-8B tokenizer is not in the local Hugging Face cache")
    return p


def tiny_config(layers=4, hidden=32, heads=4, kv_heads=2):
    transformers = pytest.importorskip("transformers")
    return transformers.Qwen3Config(vocab_size=151936, hidden_size=hidden, intermediate_size=2 * hidden,
                                    num_hidden_layers=layers, num_attention_heads=heads, num_key_value_heads=kv_heads,
                                    head_dim=hidden // heads, max_position_embeddings=8192, tie_word_embeddings=False,
                                    bos_token_id=151643, eos_token_id=151645)


def tiny_model_dir(tmp_path, seed=0, **cfg):
    """Saved with the cached snapshot's tokenizer and chat template; loads like the real model."""
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    src = qwen_tokenizer_dir()
    torch.manual_seed(seed)
    model = transformers.Qwen3ForCausalLM(tiny_config(**cfg)).eval()
    d = tmp_path / "tiny-qwen3"
    model.save_pretrained(d)
    for f in FILES:
        if (src / f).exists():
            shutil.copy(src / f, d / f)
    return d
