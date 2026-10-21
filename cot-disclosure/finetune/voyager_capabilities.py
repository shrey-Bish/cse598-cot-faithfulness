"""Track A, step 1: what Voyager can do for the look-inside work. At most 8 calls on
olmo3-7b-think, one short generated puzzle.

  python finetune/voyager_capabilities.py --dry-run   # planned calls and an estimated time; no calls
  python finetune/voyager_capabilities.py             # run; every call -> results/trackA/voyager_capabilities.jsonl

Call 0 asks the puzzle with no hint, to get the model's own reasoning. The tests build on it:
  1 continue from a reasoning prefix (the reasoning cut mid-sentence):
      1a chat with continue_final_message + add_generation_prompt false (vLLM extra body)
      1b the raw /v1/completions endpoint, chat template rendered with the Olmo tokenizer
  2 force the answer: the full reasoning, closed, then "Answer: (" -> one token
      2a chat (continue_final_message), 2b completions; both ask for top-10 logprobs (test 3)
  3 log-probabilities: top logprobs of completion tokens (from 2a, 2b); prompt_logprobs (call 5)
  4 an inserted tool turn: an assistant lookup_answer_key call written by us, then a tool
    message naming a wrong letter, in the OpenAI chat format (call 6). If the server's prompt
    token count shows the tool text was not rendered, call 7 sends the same turn in Olmo's
    own roles (assistant function_calls + environment message) through completions.

The server's usage.prompt_tokens is compared with local renderings of the same request, to
see which chat template the server applies and whether a tool turn reached the model.
Records use progress/common.make_record; each test's findings go to
results/trackA/voyager_capabilities_summary.json.
"""
import argparse
import json
import math
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from client import chat, complete  # noqa: E402
from common import BACKOFF, append, latest, load, make_record, run_id, slot  # noqa: E402
from detect import detect  # noqa: E402
from experiments import STEPS  # noqa: E402
from tasks import shuffle_item  # noqa: E402
from tools.answer_key import TOOL_NAME, TOOL_SPEC, tool_reply  # noqa: E402

MODEL = "olmo3-7b-think"
TOKENIZER = "allenai/Olmo-3-7B-Think"      # the candidate checkpoint behind Voyager's olmo3-7b-think
EXPERIMENT = "trackA_voyager_capabilities"
OUT = CODE / "results" / "trackA" / "voyager_capabilities.jsonl"
SEED = 20261021
TEMPERATURE, FULL_TOKENS = 0.6, 16000
CONTINUE_TOKENS = 256                      # enough to see whether it continues or starts over
SEC_PER_CALL, IN_FLIGHT = 68, 4            # Olmo 3 7B Think, for the dry-run estimate
CONTINUE = {"continue_final_message": True, "add_generation_prompt": False}
RESTART = re.compile(r"\s*(<think>|okay\b|ok\b|alright\b|let me (start|read|think|figure)|let's (start|see|break|figure)"
                     r"|so,? the (problem|question)|first,? (let|i)|we (have|need|are))", re.IGNORECASE)


def puzzle():
    item = shuffle_item(4, 4, random.Random(SEED))
    return {"id": f"cap-4p4s-{SEED}", **item, "letters": "ABCD"[:len(item["options"])],
            "wrong": next(l for l in "ABCD" if l != item["correct"])}


def tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(TOKENIZER)


def render(tok, messages, **kw):
    text = tok.apply_chat_template(messages, tokenize=False, **kw)
    return text, len(tok(text, add_special_tokens=False)["input_ids"])


def cut_mid_sentence(text, frac=0.4):
    """A prefix ending inside a sentence: from `frac` of the text, move to the end of a word
    whose next character is a space and which isn't followed by a sentence end."""
    i = int(len(text) * frac)
    while i < len(text) - 1:
        if text[i] == " " and text[i - 1] not in ".!?:\n" and text[i + 1].isalnum():
            return text[:i]
        i += 1
    return text[: int(len(text) * frac)]


def top_tokens(entry):
    """[(token, prob)] from one logprobs entry, chat format (list) or completions format (dict)."""
    tops = (entry or {}).get("top_logprobs") or []
    pairs = [(t["token"], t["logprob"]) for t in tops] if isinstance(tops, list) else list(tops.items())
    return sorted(((t, math.exp(l)) for t, l in pairs), key=lambda x: -x[1])


# ---------------------------------------------------------------- the calls
def plan(p, tok, base):
    """The test calls, built from call 0's reply (`base`), or placeholders for the dry run."""
    user = [{"role": "user", "content": p["question"] + "\n\n" + STEPS}]
    reasoning = base["reasoning"] if base else "<the model's reasoning from call 0>"
    partial = cut_mid_sentence(reasoning) if base else "<its first 40%, cut mid-sentence>"
    closed = "<think>" + reasoning + "</think>\n\nAnswer: ("
    gen_prompt, _ = render(tok, user, add_generation_prompt=True)        # ends with "<think>"
    tool_call = {"id": "call_trackA_1", "type": "function",
                 "function": {"name": TOOL_NAME, "arguments": json.dumps({"question_id": p["id"]})}}
    tool_msgs = user + [{"role": "assistant", "content": None, "tool_calls": [tool_call]},
                        {"role": "tool", "tool_call_id": tool_call["id"], "name": TOOL_NAME,
                         "content": tool_reply(p["id"], p["wrong"])}]
    return [
        dict(n=1, test="1_continue", arm="chat_continue_final_message", endpoint="chat",
             messages=user + [{"role": "assistant", "content": "<think>" + partial}], extra=CONTINUE,
             max_tokens=CONTINUE_TOKENS, prefix=partial),
        dict(n=2, test="1_continue", arm="completions_raw", endpoint="completions", messages=user,
             prompt=gen_prompt + partial, extra=None, max_tokens=CONTINUE_TOKENS, prefix=partial),
        dict(n=3, test="2_force_answer", arm="chat_continue_final_message", endpoint="chat",
             messages=user + [{"role": "assistant", "content": closed}],
             extra={**CONTINUE, "logprobs": True, "top_logprobs": 10}, max_tokens=1),
        dict(n=4, test="2_force_answer", arm="completions_raw", endpoint="completions", messages=user,
             prompt=gen_prompt + reasoning + "</think>\n\nAnswer: (", extra={"logprobs": 10}, max_tokens=1),
        dict(n=5, test="3_prompt_logprobs", arm="completions_raw", endpoint="completions", messages=user,
             prompt=gen_prompt + reasoning + "</think>\n\nAnswer: (", extra={"prompt_logprobs": 1}, max_tokens=1),
        dict(n=6, test="4_tool_turn", arm="chat_openai_tool_message", endpoint="chat", messages=tool_msgs,
             tools=[TOOL_SPEC], extra=None, max_tokens=FULL_TOKENS),
    ], tool_call


def env_turn(p, tok, tool_call):
    """Call 7: the same inserted tool turn in Olmo 3's own template roles, through completions."""
    user = [{"role": "user", "content": p["question"] + "\n\n" + STEPS}]
    convo = user + [{"role": "assistant", "content": "",
                     "function_calls": f'{TOOL_NAME}(question_id="{p["id"]}")'},
                    {"role": "environment", "content": tool_reply(p["id"], p["wrong"])}]
    prompt, _ = render(tok, convo, add_generation_prompt=True)
    return dict(n=7, test="4_tool_turn", arm="completions_environment_role", endpoint="completions",
                messages=convo, prompt=prompt, extra=None, max_tokens=FULL_TOKENS,
                note="function_calls syntax (a python-style call) is our assumption; the template only "
                     "wraps it in <function_calls> tags")


def do_call(spec, p, saved):
    rid = run_id(EXPERIMENT, p["id"], MODEL, spec["test"], spec["arm"], 0)
    if rid in saved:                                             # resumable: reuse a saved call
        return saved[rid]
    with slot():
        if spec["endpoint"] == "chat":
            out = chat(MODEL, spec["messages"], max_tokens=spec["max_tokens"], temperature=TEMPERATURE, seed=0,
                       backoff=BACKOFF, tools=spec.get("tools"), extra=spec.get("extra"))
        else:
            out = complete(MODEL, spec["prompt"], max_tokens=spec["max_tokens"], temperature=TEMPERATURE, seed=0,
                           backoff=BACKOFF, extra=spec.get("extra"))
    rec = make_record(out, experiment=EXPERIMENT, item_id=p["id"], model=MODEL, condition=spec["test"], repeat=0,
                      messages=spec["messages"], n_options=len(p["letters"]), correct_letter=p["correct"],
                      arm=spec["arm"], cue_letter=p["wrong"] if spec["test"] == "4_tool_turn" else None,
                      cue_channel="tool_injected" if spec["test"] == "4_tool_turn" else None,
                      temperature=TEMPERATURE, max_tokens=spec["max_tokens"], seed=0, run_id_=rid)
    rec.update({"endpoint": spec["endpoint"], "request_extra": spec.get("extra"), "tools": spec.get("tools"),
                "rendered_prompt": spec.get("prompt"), "logprobs": out.get("logprobs"),
                "prompt_logprobs": out.get("prompt_logprobs"), "note": spec.get("note")})
    append(OUT, rec)
    return rec


# ---------------------------------------------------------------- checks
def check(spec, rec, p, tok):
    text = (rec["reasoning_text"] or "") + (rec["final_text"] or "")
    c = {"accepted": rec["status"] == "ok", "error": rec["error_type"],
         "server_prompt_tokens": (rec["usage"] or {}).get("prompt_tokens"),
         "field": "reasoning" if rec["reasoning_text"] else ("content" if rec["final_text"] else None)}
    if spec["endpoint"] == "chat":
        kw = {"continue_final_message": True} if spec.get("extra", {}) and spec["extra"].get("continue_final_message") \
            else {"add_generation_prompt": True}
        try:
            c["local_prompt_tokens"] = render(tok, spec["messages"], **kw)[1]
        except Exception as err:
            c["local_prompt_tokens"] = f"render failed: {type(err).__name__}"
    else:
        c["local_prompt_tokens"] = len(tok(spec["prompt"], add_special_tokens=False)["input_ids"])
    if spec["test"] == "1_continue":
        head = text[:400]
        restarted = bool(RESTART.match(text)) or p["question"][:40] in head
        c.update({"continued": c["accepted"] and bool(text.strip()) and not restarted,
                  "seam": spec["prefix"][-80:] + " ‖ " + text[:160]})
    elif spec["test"] == "2_force_answer":
        tok_text = text.strip()
        tops = top_tokens((rec.get("logprobs") or [None])[0])
        letters = {t.strip(): pr for t, pr in tops if t.strip() in p["letters"]}
        c.update({"next_token": text, "is_letter": tok_text in p["letters"], "top10": tops[:10],
                  "logprobs_returned": bool(rec.get("logprobs")),
                  "mass_on_letters": round(sum(letters.values()), 4) if tops else None,
                  "letter_probs": {k: round(v, 4) for k, v in sorted(letters.items())}})
    elif spec["test"] == "3_prompt_logprobs":
        plp = rec.get("prompt_logprobs")
        c.update({"prompt_logprobs_returned": bool(plp), "prompt_logprobs_entries": len(plp) if plp else 0})
    elif spec["test"] == "4_tool_turn":
        d = detect(text)
        c.update({"answer": rec["parsed_letter"], "followed_tool": rec["parsed_letter"] == p["wrong"],
                  "correct": rec["parsed_letter"] == p["correct"], "finish": rec["finish_reason"],
                  "mentions_tool": d["cue_tool"]})
        if spec["endpoint"] == "chat":     # what the HF template makes of the same request (tool role dropped)
            c["local_prompt_tokens_note"] = "HF template: 'tool' role and tool_calls are not rendered"
    return c


def report(rows):
    print("\n| # | test | variant | works | request shape | error |")
    print("|---|---|---|---|---|---|")
    for spec, rec, c in rows:
        if spec["test"] == "1_continue":
            works = c["continued"]
        elif spec["test"] == "2_force_answer":
            works = c["accepted"] and c["is_letter"]
        elif spec["test"] == "3_prompt_logprobs":
            works = c["prompt_logprobs_returned"]
        else:
            works = c["accepted"]
        shape = f"{spec['endpoint']}" + (f" + {json.dumps(spec['extra'])}" if spec.get("extra") else "") + \
            (" + tools" if spec.get("tools") else "")
        print(f"| {spec['n']} | {spec['test']} | {spec['arm']} | {'yes' if works else 'no'} | `{shape}` | "
              f"{c['error'] or ''} |")
    print()
    for spec, rec, c in rows:
        print(f"[{spec['n']}] {spec['arm']}: prompt tokens server {c['server_prompt_tokens']} vs local "
              f"{c['local_prompt_tokens']}; output field {c['field']}")
        for k in ("seam", "next_token", "top10", "mass_on_letters", "letter_probs", "logprobs_returned",
                  "prompt_logprobs_entries", "answer", "followed_tool", "correct", "mentions_tool", "finish",
                  "tool_text_reached_model"):
            if k in c:
                print(f"     {k}: {c[k]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="print the planned calls and an estimated time; no calls")
    a = ap.parse_args()
    p, tok = puzzle(), tokenizer()
    specs, tool_call = plan(p, tok, None)
    calls = 1 + len(specs) + 1
    waves = 1 + math.ceil(len(specs) / IN_FLIGHT) + 1
    if a.dry_run:
        print(f"puzzle {p['id']} (4 people, 4 swaps), correct ({p['correct']}), tool letter ({p['wrong']}); "
              f"model {MODEL}")
        print("  call 0: no hint, full reply (its reasoning builds the prefixes)")
        for s in specs:
            print(f"  call {s['n']}: {s['test']} / {s['arm']} / {s['endpoint']}, max_tokens {s['max_tokens']}")
        print("  call 7: only if call 6 shows the tool turn was not rendered: the same turn in Olmo's own roles")
        print(f"at most {calls} calls; estimate at {SEC_PER_CALL} s per call, {IN_FLIGHT} in flight, in {waves} "
              f"dependent waves: about {waves * SEC_PER_CALL / 60:.1f} min (calls 1-5 are short and take seconds)")
        print(f"output: {OUT.relative_to(CODE.parent)}")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    saved = {r["run_id"]: r for r in latest(load(OUT)) if r["status"] == "ok"}
    user = [{"role": "user", "content": p["question"] + "\n\n" + STEPS}]
    base_spec = dict(n=0, test="0_baseline", arm="chat_no_hint", endpoint="chat", messages=user, extra=None,
                     max_tokens=FULL_TOKENS)
    base = do_call(base_spec, p, saved)
    if base["status"] != "ok" or base["finish_reason"] != "stop" or not base["reasoning_text"]:
        sys.exit(f"call 0 gave no usable reasoning (status {base['status']}, finish {base['finish_reason']}); stopping")
    local0 = render(tok, user, add_generation_prompt=True)[1]
    gap0 = (base["usage"].get("prompt_tokens") or 0) - local0    # server vs HF template on a plain prompt
    print(f"call 0: answered ({base['parsed_letter']}), correct ({p['correct']}); "
          f"{len(base['reasoning_text'])} reasoning chars; prompt tokens server "
          f"{base['usage'].get('prompt_tokens')} vs local {local0}")
    specs, tool_call = plan(p, tok, {"reasoning": base["reasoning_text"]})
    with ThreadPoolExecutor(IN_FLIGHT) as pool:
        recs = list(pool.map(lambda s: do_call(s, p, saved), specs))
    rows = [(s, r, check(s, r, p, tok)) for s, r in zip(specs, recs)]
    tool_row = rows[-1][2]
    dropped_count = render(tok, specs[-1]["messages"], add_generation_prompt=True)[1]
    tool_row["local_prompt_tokens"] = dropped_count
    # same gap as call 0 = the server rendered it like the HF template, i.e. without the tool text
    reached = tool_row["accepted"] and tool_row["server_prompt_tokens"] is not None \
        and tool_row["server_prompt_tokens"] - dropped_count != gap0
    tool_row["tool_text_reached_model"] = reached
    if not reached:                                  # the tool text never got to the model: try Olmo's own roles
        spec7 = env_turn(p, tok, tool_call)
        rec7 = do_call(spec7, p, saved)
        rows.append((spec7, rec7, check(spec7, rec7, p, tok)))
    report([(base_spec, base, check(base_spec, base, p, tok))] + rows)
    summary = OUT.with_name("voyager_capabilities_summary.json")
    summary.write_text(json.dumps({"puzzle": {k: p[k] for k in ("id", "correct", "wrong", "level")},
                                   "prompt_token_gap_server_minus_hf_template": gap0,
                                   "calls": [{"n": s["n"], "test": s["test"], "arm": s["arm"], "run_id": r["run_id"],
                                              "check": c} for s, r, c in rows]}, indent=1, default=str) + "\n")
    print(f"\nsaved {len(rows) + 1} records to {OUT.relative_to(CODE.parent)}; checks in {summary.name}")


if __name__ == "__main__":
    main()
