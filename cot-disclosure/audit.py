"""Show detector matches in context so a human can judge whether they are right.

  python audit.py --signal cue --where answer --n 15
Reads only cached responses; makes no API calls for anything already run.
"""
import argparse
import random
import re

from client import chat
from detect import COMPILED
from run import build_prompt
from tasks import make_items


def snippets(text, rx, width=90):
    out = []
    for m in rx.finditer(text or ""):
        a, b = max(0, m.start() - width), min(len(text), m.end() + width)
        out.append("..." + text[a:m.start()] + "[[" + m.group(0) + "]]" + text[m.end():b] + "...")
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--signal", default="cue", choices=list(COMPILED))
    p.add_argument("--where", default="answer", choices=["answer", "trace"])
    p.add_argument("--model", default="olmo3-32b-think")
    p.add_argument("--condition", default="cued", choices=["control", "cued"])
    p.add_argument("--level", type=int, nargs=2, default=[7, 15])
    p.add_argument("--n", type=int, default=24)
    p.add_argument("--max-tokens", type=int, default=16000)
    p.add_argument("--show", type=int, default=12)
    a = p.parse_args()
    rx = COMPILED[a.signal]
    hits = []
    for idx, item in enumerate(make_items("shuffle", tuple(a.level), a.n)):
        prompt, cue = build_prompt(item, a.condition, random.Random(f"{item['level']}-{idx}"))
        out = chat(a.model, [{"role": "user", "content": prompt}], max_tokens=a.max_tokens)
        text = out["content"] if a.where == "answer" else out["reasoning"]
        for s in snippets(text, rx):
            hits.append((idx, cue, s))
    print(f"{a.signal} in {a.where} | {a.model} | {a.condition} | {len(hits)} matches across {a.n} items\n")
    for idx, cue, s in hits[: a.show]:
        print(f"[item {idx}, cue=({cue})] " + re.sub(r"\s+", " ", s))
        print()


if __name__ == "__main__":
    main()
