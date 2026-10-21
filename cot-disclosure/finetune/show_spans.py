"""Print the source-tag span of every turn, with the real Olmo 3 7B Think tokenizer, for the
three hint channels: (a) a user hint, (b) a pasted tool block, (c) an inserted tool turn.
No model calls (the tokenizer is downloaded from Hugging Face once).

  python finetune/show_spans.py                 # Test 2 law item 1112, hint (B)
  python finetune/show_spans.py --item 11896
  python finetune/show_spans.py --dry-run       # same (nothing here calls a model)
"""
import argparse
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from finetune import olmo_format  # noqa: E402
from finetune.source_tags import SOURCES, source_ids_from_chat, source_ids_from_render  # noqa: E402
from mmlu_pro_probe import load_items, question_block  # noqa: E402
from tools.answer_key import build  # noqa: E402

TOKENIZER = "allenai/Olmo-3-7B-Think"
NAMES = {v: k for k, v in SOURCES.items()}


def show(tok, label, messages):
    text = olmo_format.render(messages, add_generation_prompt=True)
    ids, src, spans = source_ids_from_render(tok, text)
    print(f"\n({label}) {len(ids)} tokens")
    print("  turn         tag     tokens          first / last tokens of the span")
    for s in spans:
        a, b = s["tokens"]
        toks = tok.convert_ids_to_tokens(ids[a:b])
        assert all(NAMES[x] == s["source"] for x in src[a:b])
        assert tok.decode(ids[a:b]) == text[s["chars"][0]:s["chars"][1]]      # the span is exactly that turn's text
        head, tail = "".join(toks[:4]), "".join(toks[-3:])
        print(f"  {s['role']:12} {s['source']:7} [{a:>4}, {b:>4}) {b - a:>4}  {head!r} … {tail!r}")
    hint_turns = [s for s in spans if s["role"] in ("user", "environment")]
    return text, spans, hint_turns


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--item", type=int, default=1112, help="a Test 2 (MMLU-Pro) question id")
    ap.add_argument("--dry-run", action="store_true", help="same as a normal run: this script makes no model calls")
    a = ap.parse_args()
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(TOKENIZER)
    item = next(i for i in load_items() if i["question_id"] == a.item)
    q, letter = question_block(item), item["cue_letter"]
    print(f"Test 2 item {a.item}: correct ({item['answer']}), hint ({letter}); "
          f"pinned template {olmo_format.PINNED_FILE.name} sha256 {olmo_format.PINNED_SHA256[:16]}…")
    for label, cond in (("a: user hint", "user"), ("b: pasted tool block", "tool_pasted"),
                        ("c: inserted tool turn", "tool_injected")):
        msgs, _ = build(q, a.item, cond, letter)
        text, spans, _ = show(tok, label, msgs)
        if cond == "tool_pasted":
            block = text.index("[tool result: lookup_answer_key]")
            owner = next(s for s in spans if s["chars"][0] <= block < s["chars"][1])
            print(f"  -> the pasted tool block sits in the {owner['role']} turn, so it is tagged {owner['source']}")
        if cond == "tool_injected":
            print("  rendered tool turn:")
            i = text.index("<|im_start|>assistant\n<function_calls>")
            print("   ", json.dumps(text[i:])[1:-1][:400])
            tok.chat_template = olmo_format.PINNED
            try:
                source_ids_from_chat(tok, msgs)
                print("  source_ids_from_chat: worked")
            except ValueError as err:
                print(f"  source_ids_from_chat refuses it: {err}")


if __name__ == "__main__":
    main()
