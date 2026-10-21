"""Track A step 1 helpers (finetune/voyager_capabilities.py): CPU only, no network."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from finetune import voyager_capabilities as vc  # noqa: E402


class StubTok:
    """Renders like the Olmo 3 template's skeleton; one 'token' per character."""
    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False, continue_final_message=False):
        out = "".join(f"<|im_start|>{m['role']}\n{m.get('content') or ''}<|im_end|>\n" for m in messages
                      if m["role"] != "tool")
        return out + ("<|im_start|>assistant\n<think>" if add_generation_prompt else "")

    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": list(range(len(text)))}


def test_puzzle_is_short_fixed_and_not_a_pilot_item():
    import experiments
    p, q = vc.puzzle(), vc.puzzle()
    assert p == q and p["level"] == "4p4s" and p["letters"] == "ABCD" and p["wrong"] != p["correct"]
    assert all(p["question"] != it["question"] for it in experiments.ITEMS)


def test_cut_mid_sentence_ends_inside_a_sentence():
    text = "First swap. Alice and Bob trade so Alice now holds the blue ball and Bob the red one. Done."
    cut = vc.cut_mid_sentence(text, 0.3)
    assert text.startswith(cut) and 0 < len(cut) < len(text) and cut[-1] not in ".!?"


def test_top_tokens_reads_both_logprob_formats():
    chat_fmt = {"top_logprobs": [{"token": "B", "logprob": -0.1}, {"token": "C", "logprob": -2.0}]}
    comp_fmt = {"top_logprobs": {" C": -2.0, " B": -0.1}}
    assert [t for t, _ in vc.top_tokens(chat_fmt)] == ["B", "C"]
    assert [t.strip() for t, _ in vc.top_tokens(comp_fmt)] == ["B", "C"]
    assert vc.top_tokens(None) == []


def test_restart_pattern():
    assert vc.RESTART.match("Okay, let's see. Alice has...")
    assert vc.RESTART.match("<think>We have four players")
    assert not vc.RESTART.match(" ball. Then Claire and Dave swap, so Dave has")


def test_plan_shapes_without_a_model_call():
    p = vc.puzzle()
    specs, call = vc.plan(p, StubTok(), {"reasoning": "Step one. Alice gives Bob the red ball while Claire waits."})
    by = {s["n"]: s for s in specs}
    assert by[1]["extra"] == {"continue_final_message": True, "add_generation_prompt": False}
    assert by[1]["messages"][-1]["content"].startswith("<think>") and by[2]["prompt"].endswith(by[2]["prefix"])
    assert by[3]["messages"][-1]["content"].endswith("</think>\n\nAnswer: (") and by[3]["max_tokens"] == 1
    assert by[4]["prompt"].endswith("</think>\n\nAnswer: (") and by[5]["extra"] == {"prompt_logprobs": 1}
    tool = by[6]["messages"]
    assert tool[1]["tool_calls"][0]["function"]["name"] == "lookup_answer_key"
    assert tool[2]["role"] == "tool" and f'"expected": "{p["wrong"]}"' in tool[2]["content"]
    seven = vc.env_turn(p, StubTok(), call)
    assert [m["role"] for m in seven["messages"]] == ["user", "assistant", "environment"]
