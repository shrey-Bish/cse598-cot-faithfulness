"""The scratch pad's live mode (Nov 23): your own question, run now on a base model through Ollama on this Mac.

  python tools/demo_template/live.py "Question text" "opt A" "opt B" ... --hint user --letter B   # one run, printed
  # the page calls it through serve.py (POST /live), localhost only

The experiments' own pieces, imported, not rewritten: the prompt builder (tools/answer_key.build, as run_trackB.run_one
builds a run), the answer parser (parse.parse_answer), the outcome flags (trackB_report.flags) and the highlight spans
(runs.spans_of: detect.COMPILED). Base model only: Qwen3-8B (qwen3:8b; this Mac has no Olmo 3 7B Think in Ollama),
thinking on, the experiments' temperature 0.6. The fixes exist as recorded runs only. Nothing is saved: a live run is
not a recorded run and is never counted.
"""
import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE = HERE.parents[1]
for p in (HERE, CODE, CODE / "progress", CODE / "tools"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

MODEL = "qwen3:8b"
MODEL_NAME = "Qwen3-8B (Ollama, this Mac)"
CONDITIONS = {"none": "none", "user": "user", "pasted": "tool_pasted", "system": "system", "call": "tool_injected"}
MAX_TOKENS = 6000


def question_block(text, options):
    return text.strip() + "\n" + "\n".join(f"({chr(65 + i)}) {o.strip()}" for i, o in enumerate(options))


def run(text, options, hint="user", letter=None, thinking=True, seed=0, max_tokens=MAX_TOKENS):
    from answer_key import build
    from parse import parse_answer
    from providers.ollama import generate
    from trackB_report import flags
    import runs as R
    cond = CONDITIONS[hint]
    msgs, tools = build(question_block(text, options), "live-1", cond, letter if cond != "none" else None)
    t0 = time.monotonic()
    reply = generate(MODEL, msgs, tools=tools, thinking=thinking, max_tokens=max_tokens, temperature=0.6, seed=seed)
    secs = round(time.monotonic() - t0, 1)
    if reply.error:
        return {"error": reply.error, "seconds": secs}
    letter_out = parse_answer(reply.final_text, len(options))[0]
    rec = {"condition": cond, "hint_letter": letter, "correct_letter": None, "parsed_letter": letter_out,
           "reasoning_text": reply.reasoning_text, "final_text": reply.final_text, "status": "ok"}
    f = flags({**rec, "run_id": None, "item_id": "live-1"})
    hinted = cond != "none"
    return {"m": MODEL_NAME, "s": "thinking on" if thinking else "thinking off", "src": hint, "H": letter, "L": letter_out,
            "w": True if hinted else None, "seconds": secs, "tokens": (reply.usage or {}).get("output_tokens"),
            "out": {"took": f["followed"] if hinted else None, "private": f["mention_private"], "final": f["mention_final"]},
            "x": {"prompt": msgs, "reasoning": reply.reasoning_text, "final": reply.final_text, "tool": None, "spans": R.spans_of(rec)},
            "rec": f"Live run: {MODEL_NAME}, no fix, now; not a recorded run, never counted"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("question")
    ap.add_argument("options", nargs="+")
    ap.add_argument("--hint", default="user", choices=sorted(CONDITIONS))
    ap.add_argument("--letter")
    ap.add_argument("--no-think", action="store_true")
    a = ap.parse_args(argv)
    out = run(a.question, a.options, a.hint, a.letter, not a.no_think)
    x = out.get("x") or {}
    print(json.dumps({k: v for k, v in out.items() if k != "x"}, indent=1))
    print("reasoning chars:", len(x.get("reasoning") or ""), "spans:", x.get("spans"))
    return 0 if "error" not in out else 1


if __name__ == "__main__":
    sys.exit(main())
