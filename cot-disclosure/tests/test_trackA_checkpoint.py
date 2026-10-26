"""Step 8, the checkpoint check (finetune/gpu/checkpoint_check.py): the two-part rule on synthetic
log-probs, echo alignment, and an end-to-end run on a tiny random Olmo 3 model on CPU whose own
log-probs stand in for Voyager's echo. No GPU, no network."""
import json
import math
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

from finetune.gpu import checkpoint_check as cc  # noqa: E402
from _tiny_olmo import olmo_tokenizer_dir, tiny_model_dir  # noqa: E402


class FakeDec:
    def decode(self, i):
        return f"t{i}"


def synthetic(n, strict_n):
    """Voyager entries and a local pass that agree exactly: token i is "t{i}", the top token is the
    prompt's own token with p = 0.9, the second has p = 0.05."""
    strings = [f"t{i}" for i in range(n)]
    entries = [{"token": "t0", "logprob": None, "top_logprobs": None}]
    entries += [{"token": f"t{i}", "logprob": math.log(0.9), "top_logprobs": {f"t{i}": math.log(0.9)}} for i in range(1, n)]
    local = {"lp": [None] + [math.log(0.9)] * (n - 1), "top1": [None] + list(range(1, n)),
             "top1_lp": [None] + [math.log(0.9)] * (n - 1), "top2": [None] + [10 ** 6] * (n - 1),
             "top2_lp": [None] + [math.log(0.05)] * (n - 1), "want_lp": [None] + [math.log(0.9)] * (n - 1)}
    return strings, entries, local


def test_identical_passes():
    strings, entries, local = synthetic(40, 20)
    r = cc.compare(strings, entries, local, FakeDec(), strict_n=20)
    assert r["pass"] and r["strict"]["positions"] == 19 and r["beyond"]["positions"] == 20
    assert r["strict"]["max_abs_diff"] == 0 and r["beyond"]["top_token_mismatches"] == 0


def test_strict_part_fails_on_a_small_difference():
    strings, entries, local = synthetic(40, 20)
    local["lp"][5] += 0.02                                    # over 0.01 in the first 2,047 (here 20) tokens
    r = cc.compare(strings, entries, local, FakeDec(), strict_n=20)
    assert not r["strict"]["pass"] and r["beyond"]["pass"] and not r["pass"]
    local["lp"][5] -= 0.02
    local["lp"][30] += 0.5                                    # beyond: reported, not a failure by itself
    r = cc.compare(strings, entries, local, FakeDec(), strict_n=20)
    assert r["pass"] and r["beyond"]["max_abs_diff"] == pytest.approx(0.5)


def test_strict_part_fails_on_any_top_token_mismatch():
    strings, entries, local = synthetic(40, 20)
    local["top1"][7] = 999                                    # even a near-tie fails in the strict part
    local["want_lp"][7] = math.log(0.89)
    r = cc.compare(strings, entries, local, FakeDec(), strict_n=20)
    assert not r["strict"]["pass"] and r["strict"]["top_token_mismatches"] == 1


def test_beyond_counts_only_mismatches_outside_near_ties():
    strings, entries, local = synthetic(40, 20)
    # position 25: local top is another token at 0.46; Voyager's top (t25) has 0.44 locally -> near-tie
    local["top1"][25], local["top1_lp"][25], local["want_lp"][25] = 999, math.log(0.46), math.log(0.44)
    r = cc.compare(strings, entries, local, FakeDec(), strict_n=20)
    assert r["pass"] and r["beyond"]["top_token_mismatches"] == 1 and r["beyond"]["near_ties"] == 1
    # position 30: local top at 0.7, Voyager's top at 0.2 locally -> a real mismatch
    local["top1"][30], local["top1_lp"][30], local["want_lp"][30] = 998, math.log(0.7), math.log(0.2)
    r = cc.compare(strings, entries, local, FakeDec(), strict_n=20)
    assert not r["pass"] and r["beyond"]["mismatches_outside_near_ties"] == 1
    assert r["beyond"]["outside_examples"][0]["pos"] == 30


def test_near_tie_needs_both_sides_when_voyager_has_both():
    strings, entries, local = synthetic(40, 20)
    local["top1"][25], local["top1_lp"][25], local["want_lp"][25] = 999, math.log(0.46), math.log(0.44)
    entries[25]["top_logprobs"] = {"t25": math.log(0.8), "t999": math.log(0.1)}   # Voyager: 0.8 vs 0.1, no tie
    r = cc.compare(strings, entries, local, FakeDec(), strict_n=20)
    assert not r["pass"] and r["beyond"]["outside_examples"][0]["gap_voyager"] == pytest.approx(0.7)


def test_verdict_needs_every_think_reference_and_a_failing_control():
    ok = {"pass": True, "pass_logprobs": True, "control": False}
    bad_control = {"pass": False, "pass_logprobs": False, "control": True}
    v = cc.verdict({"bf16": {"a": ok, "b": ok, "c": bad_control}, "fp32": {"a": ok, "b": ok, "c": bad_control}})
    assert v["pass"] and "fails, as it must" in v["lines"][0]
    v = cc.verdict({"bf16": {"a": ok, "b": {**ok, "pass": False}, "c": bad_control}, "fp32": {"a": ok, "b": ok}})
    assert not v["pass"] and v["by_dtype"] == {"bf16": False, "fp32": True}
    v = cc.verdict({"bf16": {"a": ok, "c": {**bad_control, "pass_logprobs": True}}})
    assert "cannot tell checkpoints apart" in v["lines"][0]


def test_align_marks_positions_tokenized_differently():
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(olmo_tokenizer_dir(), local_files_only=True)
    text = "<|im_start|>user\nWhat is 17 + 25?<|im_end|>\n"
    ids = tok(text, add_special_tokens=False)["input_ids"]
    echo = [{"token": tok.decode([t]), "logprob": -1.0, "top_logprobs": {}} for t in ids] + [{"token": "A"}]
    _, strings, entries = cc.align(tok, text, echo)
    assert all(e is not None for e in entries) and "".join(strings) == text
    merged = echo[:3] + [{"token": echo[3]["token"] + echo[4]["token"], "logprob": -1.0}] + echo[5:]
    _, _, entries = cc.align(tok, text, merged)
    assert [i for i, e in enumerate(entries) if e is None] == [3, 4]


def echo_from(model, tok, text):
    """What Voyager's echo would return if it served exactly this model (logprobs: 1)."""
    ids = tok(text, add_special_tokens=False)["input_ids"]
    local = cc.local_logprobs(model, ids, [None] * len(ids), chunk=37)
    out = [{"token": tok.decode([ids[0]]), "logprob": None, "top_logprobs": None}]
    for i in range(1, len(ids)):
        tops = {tok.decode([local["top1"][i]]): local["top1_lp"][i], tok.decode([ids[i]]): local["lp"][i]}
        out.append({"token": tok.decode([ids[i]]), "logprob": local["lp"][i], "top_logprobs": tops})
    return out


def test_end_to_end_on_a_tiny_model(tmp_path):
    torch = pytest.importorskip("torch")
    from finetune import olmo_format
    from finetune.gpu import kit
    d = tiny_model_dir(tmp_path)
    tok = kit.load_tokenizer(d)
    model = kit.load_model(d, "fp32", torch.device("cpu"), attn="eager")
    text = olmo_format.render([{"role": "user", "content": "Which is larger, 17 + 25 or 6 x 7? Explain."}]) + \
        "Let me add them. 17 + 25 = 42, and 6 x 7 = 42, so they are equal.</think>\n\nAnswer: ("
    good = echo_from(model, tok, text)
    other = [dict(e) for e in good]                           # a "different checkpoint": every log-prob moved
    for e in other[1:]:
        e["logprob"] -= 0.3
    refs = [{"name": "same", "text": text, "logprobs": good, "control": False, "source": "the tiny model itself"},
            {"name": "other", "text": text, "logprobs": other, "control": True, "source": "shifted"}]
    s = cc.run(str(d), "cpu", ("fp32",), str(tmp_path / "out"), strict_n=40, refs=refs)
    same = s["results"]["fp32"]["same"]
    assert same["pass"] and same["strict"]["max_abs_diff"] < 1e-4 and same["beyond"]["positions"] > 0
    assert not s["results"]["fp32"]["other"]["pass_logprobs"] and s["verdict"]["pass"]
    saved = json.loads((tmp_path / "out" / "step8" / "step8_checkpoint.json").read_text())
    assert saved["snapshot_commit"] == "local:tiny-olmo3" and saved["rule"]["strict_first_tokens"] == 40
    assert (tmp_path / "out" / "step8" / "step8_positions.npz").exists()
