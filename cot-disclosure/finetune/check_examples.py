"""Track A: the two checks on the assembled training and validation examples before training (no calls).

  python finetune/check_examples.py            # prints the counts; -> results/summaries/trackA/data/examples_check.json

(a) Held out stays held out: no example is one of the 30 held-out MMLU-Pro questions (by item id,
    or by its question text in the prompt), and no example's prompt carries a held-out hint wording:
    its wording id is a training one, its channel a training channel, and no held-out wording's fixed
    text (as build_dataset.heldout_overlap reads it), the system note or the held-out-only tool name
    appears in its messages or tool list. Targets quoting such text are counted too (informational).
(e) Length: every example encoded exactly as finetune/train.py encodes it (the pinned template, the
    reply after "<think>"): how many pass 32,768 tokens or have no reply tokens (train.usable leaves
    those out), next to the assembly's own count (examples_manifest.json, dropped_over_32768).
"""
import argparse
import json
import re
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from finetune import build_dataset as bd  # noqa: E402
from finetune import train as tr  # noqa: E402

OUT = CODE / "results" / "summaries" / "trackA" / "data" / "examples_check.json"
LENGTHS = OUT.with_name("examples_lengths.json")      # numbers only: finetune/gpu/plan_training.py reads it
MANIFEST = CODE / "finetune" / "data" / "examples_manifest.json"


def norm(text):
    return re.sub(r"\s+", " ", text).strip().lower()


def pieces(tmpl):
    """A template's fixed text between its {letter} and {qid} slots."""
    return re.split(r"\{(?:letter|qid)\}", tmpl.replace("{{", "{").replace("}}", "}"))


def heldout_texts():
    """(wording, text): every fixed piece of a held-out wording (over 12 characters) that no training
    wording contains, plus the held-out-only tool name. Split on the slots, not on "{": a piece like
    'letter}", "source": ...' never appears in a filled hint."""
    train = " ".join(p for _, _, tmpl, _ in bd.WORDINGS["train"] for p in pieces(tmpl))
    out = []
    for wid, _, tmpl, _ in bd.WORDINGS["heldout"]:
        reply = bd.tool_reply("{qid}", "{letter}").replace('"{qid}"', "{qid}")    # held-out ids are numbers
        for piece in pieces(tmpl or reply):
            if len(piece) > 12 and piece not in train and (wid, piece) not in out:
                out.append((wid, piece))
    out += [("new_tool", bd.NEW_TOOL)]
    return out


def prompt_text(ex):
    """Everything the model reads before its reply: message contents, tool calls, the tool list."""
    parts = []
    for m in ex["messages"]:
        parts.append(m.get("content") if isinstance(m.get("content"), str) else json.dumps(m.get("content")))
        parts += [json.dumps(c, ensure_ascii=False) for c in m.get("tool_calls") or []]
    return "\n".join(p or "" for p in parts) + "\n" + json.dumps(ex.get("tools"), ensure_ascii=False)


def check_heldout(examples, heldout):
    """(a) for these examples against these held-out questions."""
    ids = {q["item_id"] for q in heldout}
    stems = {q["item_id"]: norm(q["question"])[:150] for q in heldout}
    train_wordings = {w[0] for w in bd.WORDINGS["train"]}
    texts = heldout_texts()
    res = {"examples": len(examples), "heldout_questions": len(ids),
           "heldout_question_by_id": sorted({e["item_id"] for e in examples if e["item_id"] in ids}),
           "heldout_question_by_text": [], "wording_not_a_training_one": [], "channel_not_a_training_one": [],
           "heldout_text_in_prompt": [], "heldout_text_in_target": {}}
    for e in examples:
        prompt = norm(prompt_text(e))
        res["heldout_question_by_text"] += [f"{e['record_id']}~{q}" for q, s in stems.items() if s in prompt]
        if e.get("hint_wording") is not None and e["hint_wording"] not in train_wordings:
            res["wording_not_a_training_one"].append(e["record_id"])
        if e.get("hint_channel") not in (*bd.TRAIN_CHANNELS, "none", None):
            res["channel_not_a_training_one"].append(e["record_id"])
        raw = prompt_text(e)
        res["heldout_text_in_prompt"] += [f"{e['record_id']}~{name}" for name, t in texts if t in raw]
        for name, t in texts:
            if t in (e.get("target_raw") or ""):
                key = f"{name}: {t}"
                res["heldout_text_in_target"][key] = res["heldout_text_in_target"].get(key, 0) + 1
    res["pass"] = not any(res[k] for k in ("heldout_question_by_id", "heldout_question_by_text",
                                           "wording_not_a_training_one", "channel_not_a_training_one",
                                           "heldout_text_in_prompt"))
    return res


def check_lengths(examples, tokenizer):
    """(e): the training encoding's length of every example."""
    lens, no_reply = [], 0
    for ex in examples:
        e = tr.encode(tokenizer, ex)
        lens.append(len(e["ids"]))
        no_reply += e["n_target"] == 0
    s = sorted(lens)
    return {"examples": len(lens), "over_32768": sum(n > tr.MAX_LEN for n in lens), "no_reply_tokens": no_reply,
            "max_tokens": s[-1] if s else None, "median_tokens": s[len(s) // 2] if s else None,
            "over_30000": sum(n > 30000 for n in lens), "total_tokens": sum(lens), "lengths": s}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-lengths", action="store_true", help="skip (e) (it needs the Olmo 3 tokenizer)")
    a = ap.parse_args()
    sets = {s: tr.load_examples(p) for s, p in (("train", tr.TRAIN), ("validation", tr.VALIDATION))}
    heldout = list(bd.heldout_questions())
    res = {"a_heldout": {s: check_heldout(x, heldout) for s, x in sets.items()}}
    if not a.no_lengths:
        from transformers import AutoTokenizer
        from finetune.gpu import kit
        tok = AutoTokenizer.from_pretrained(kit.snapshot()[0])
        res["e_length"] = {s: check_lengths(x, tok) for s, x in sets.items()}
        LENGTHS.write_text(json.dumps({s: res["e_length"][s].pop("lengths") for s in sets}) + "\n")
        res["e_length"]["assembly_dropped_over_32768"] = json.loads(MANIFEST.read_text())["dropped_over_32768"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
