"""Track A, Step 12 (finetune/generate.py) on a tiny random Olmo 3: tagged prompt embeddings, the
folded embedding table, the own decoding loop against the tagged model, and the vLLM client's request.
CPU only, no network."""
import base64
import io
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "tests"))

torch = pytest.importorskip("torch")

from _tiny_olmo import tiny_model_dir  # noqa: E402
from finetune import generate as gen  # noqa: E402
from finetune import olmo_format, tags_vllm  # noqa: E402
from finetune.source_tags import SOURCES, SourceTaggedLM  # noqa: E402
from tools.answer_key import TOOL_SPEC, build  # noqa: E402


@pytest.fixture(scope="module")
def tagged(tmp_path_factory):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tmp = tmp_path_factory.mktemp("g")
    d = tiny_model_dir(tmp)
    model = AutoModelForCausalLM.from_pretrained(d, attn_implementation="eager").eval()
    lm = SourceTaggedLM(model)
    torch.manual_seed(1)
    with torch.no_grad():
        lm.tags.weight.normal_(0, 0.5)
    torch.save(lm.tags.weight.detach(), tmp / "tags.pt")
    return d, AutoTokenizer.from_pretrained(d), lm, tmp / "tags.pt"


def prompt():
    msgs, _ = build("Q?\n(A) 1\n(B) 2", "q1", "tool_injected", "B")
    return olmo_format.render(msgs, tools=[TOOL_SPEC])


def test_a_continuation_is_tagged_model_and_the_turns_keep_theirs(tagged):
    d, tok, lm, tags = tagged
    t = gen.Tagger(tok, gen.load_embedding(d), torch.load(tags))
    ids, src = t.ids_and_sources(prompt())
    ids2, src2 = t.ids_and_sources(prompt() + "So far I think")
    assert ids2[:len(ids)] == ids and src2[:len(src)] == src and set(src2[len(src):]) == {SOURCES["model"]}
    assert SOURCES["tool"] in src and src[0] == SOURCES["system"]
    e = t.embeds(prompt())
    ref = lm.embed(torch.tensor([ids]), torch.tensor([src]))[0]
    assert torch.allclose(e.float(), ref.float(), atol=1e-6)


def test_fold_rewrites_only_the_embedding_shard(tagged, tmp_path):
    d, tok, lm, tags = tagged
    out = gen.fold_model(d, tags, tmp_path / "folded")
    folded = gen.load_embedding(out)
    want = tags_vllm.folded_model(lm).get_input_embeddings().weight
    assert torch.allclose(folded.float(), want.float(), atol=1e-6)
    assert (out / "tokenizer.json").is_symlink() and json.loads((out / "folded_from.json").read_text())["tag_norm"] > 0
    cfg = json.loads((Path(d) / "config.json").read_text())
    bad = tmp_path / "tied"
    bad.mkdir()
    (bad / "config.json").write_text(json.dumps({**cfg, "tie_word_embeddings": True}))
    with pytest.raises(ValueError, match="tied"):
        gen.fold_model(bad, tags, tmp_path / "x")


def test_the_own_loop_matches_the_tagged_model(tagged, tmp_path):
    from transformers import AutoModelForCausalLM
    d, tok, lm, tags = tagged
    folded = AutoModelForCausalLM.from_pretrained(gen.fold_model(d, tags, tmp_path / "f"), attn_implementation="eager").eval()
    t = gen.Tagger(tok, gen.load_embedding(d), torch.load(tags))
    complete = gen.hf_complete(folded, tok, t, device="cpu")
    out = complete("x", prompt(), max_tokens=6, temperature=0)
    ids, src = t.ids_and_sources(prompt())
    ref = tags_vllm.tagged_greedy(lm, torch.tensor([ids]), torch.tensor([src]), 6)[0].tolist()
    assert out["usage"]["completion_tokens"] == 6 and out["usage"]["prompt_tokens"] == len(ids)
    assert out["content"] == tok.decode(ref)


def test_the_server_client_sends_tagged_embeddings(tagged, monkeypatch):
    d, tok, lm, tags = tagged
    t = gen.Tagger(tok, gen.load_embedding(d), torch.load(tags))
    sent = {}

    class Resp(io.BytesIO):
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake(req, timeout=None):
        sent.update(json.loads(req.data.decode()))
        return Resp(json.dumps({"choices": [{"text": "Hm.</think>\n\nAnswer: (A)", "finish_reason": "stop"}],
                                "usage": {"prompt_tokens": 9, "completion_tokens": 4}}).encode())
    monkeypatch.setattr(gen.urllib.request, "urlopen", fake)
    out = gen.server_complete("http://localhost:8011", "lora_tags", t)("ignored", prompt(), max_tokens=50, seed=2,
                                                                       extra={"stop": ["</function_calls>"]})
    assert out["content"].endswith("(A)") and out["finish"] == "stop" and out["usage"]["completion_tokens"] == 4
    assert "prompt" not in sent and sent["seed"] == 2 and sent["stop"] == ["</function_calls>"] and sent["model"] == "lora_tags"
    e = torch.load(io.BytesIO(base64.b64decode(sent["prompt_embeds"])))
    assert torch.equal(e, t.embeds(prompt()))
    plain = gen.server_complete("http://localhost:8011", "base")("x", prompt(), max_tokens=5)
    assert sent["prompt"] == prompt() and plain["error"] is None


def test_serve_command():
    cmd = gen.serve_cmd("/m", lora={"lora": "/a"}, prompt_embeds=True)
    assert cmd[:3] == ["vllm", "serve", "/m"] and "--enable-prompt-embeds" in cmd and "lora=/a" in cmd
    assert str(gen.MAX_MODEL_LEN) in cmd
