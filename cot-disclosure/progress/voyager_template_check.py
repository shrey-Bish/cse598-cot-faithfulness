"""Which chat template does Voyager apply to each Track B model? The server's prompt-token count
for Track B's own prompts, against our rendering with the model's chat template from Hugging Face
(the check done for Olmo on Oct 21, finetune/template_revisions.py). One call per condition and
model, max_tokens 1; the first pilot puzzle, Track B's wordings (tools/answer_key.py).

  python progress/voyager_template_check.py --dry-run
  python progress/voyager_template_check.py [--model M]          # -> results/trackB/template_check.jsonl
  python progress/voyager_template_check.py --canary-specs DIR   # specs for progress/make_canary.py

Chat models are checked on /v1/chat/completions (the served template; tool_real sends the tool
spec). Olmo 3 7B Think runs in our pinned format on /v1/completions, so there the check is that the
server counts our rendered prompt as we do. A gap of 0 on every condition means the server renders
what we render; any other gap is reported, never patched over. Downloads only tokenizer files.

Oct 27: gap 0 on every condition for both Qwen3 models and Olmo, except tool_real on Qwen3: the
server counts 1 token fewer, and our rendering matches it when the tool spec's JSON keys are sorted
(local_tokens_sorted_tool_keys): the served template is the model's own; vLLM orders the keys.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import append, slot  # noqa: E402
from tools.answer_key import ALL_CONDITIONS, INJECTED, TOOL_SPEC, build  # noqa: E402

OUT = CODE / "results" / "trackB" / "template_check.jsonl"
REPOS = {"qwen3-30b-a3b-thinking-2507": "Qwen/Qwen3-30B-A3B-Thinking-2507",
         "qwen3-30b-a3b-instruct-2507": "Qwen/Qwen3-30B-A3B-Instruct-2507",
         "olmo3-7b-think": None}                                 # None: our pinned format (finetune/olmo_format.py)
CHAT_CONDITIONS = ("none", "user", "tool_pasted", "tool_real", "system")
PINNED_CONDITIONS = ("none", "user", "tool_pasted", INJECTED, "system")


def item():
    import experiments as pilot
    it = pilot.ITEMS[0]
    return {"item_id": "pilot-0", "question": it["question"], "hint_letter": pilot.WRONG_CUES[(0, 0)]}


def prompts(name):
    """[(condition, messages, tools)] for one model, as run_trackB.py sends them."""
    it = item()
    conds = PINNED_CONDITIONS if REPOS[name] is None else CHAT_CONDITIONS
    out = []
    for c in conds:
        msgs, tools = build(it["question"], it["item_id"], c, None if c == "none" else it["hint_letter"])
        if REPOS[name] is None and c == INJECTED:
            tools = [TOOL_SPEC]                                  # declared, as in run_trackB.run_one_pinned
        out.append((c, msgs, tools))
    return out


def local_chat(repo):
    """(tokenizer, the repo's current commit) for a chat model."""
    from huggingface_hub import HfApi
    from transformers import AutoTokenizer
    sha = HfApi().model_info(repo).sha
    return AutoTokenizer.from_pretrained(repo, revision=sha), sha


def count_chat(tok, msgs, tools):
    ids = tok.apply_chat_template(msgs, tools=tools, add_generation_prompt=True, tokenize=True)
    return len(ids["input_ids"] if hasattr(ids, "keys") else ids)      # transformers 5 returns an encoding


def sorted_keys(x):
    """The same JSON with every object's keys sorted: how Voyager (vLLM) serializes a tool spec
    (Oct 27: our rendering with sorted keys matches its count; with the spec's own order, 1 token more)."""
    if isinstance(x, dict):
        return {k: sorted_keys(x[k]) for k in sorted(x)}
    return [sorted_keys(v) for v in x] if isinstance(x, list) else x


def check(name):
    """One row per condition: our count, the server's, the gap (server - ours)."""
    import client
    from finetune import olmo_format
    repo = REPOS[name]
    tok, sha = local_chat(repo) if repo else (None, None)
    with slot():
        client.preflight(name)                                   # catalog check and identity canary
    rows = []
    for cond, msgs, tools in prompts(name):
        if repo:
            ours = count_chat(tok, msgs, tools)
            with slot():
                out = client.chat(name, msgs, max_tokens=1, temperature=0.6, seed=0, tools=tools)
        else:
            prompt = olmo_format.render(msgs, tools=tools)
            ours = olmo_format.n_tokens(prompt)
            with slot():
                out = client.complete(name, prompt, max_tokens=1, temperature=0.6, seed=0)
        server = (out.get("usage") or {}).get("prompt_tokens")
        rows.append({"timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "model": name,
                     "endpoint": "chat" if repo else "completions",
                     "template": f"{repo}@{sha}" if repo else f"pinned olmo3_think_tools.jinja ({olmo_format.PINNED_SHA256[:12]})",
                     "condition": cond, "tools_sent": bool(tools), "local_tokens": ours, "server_tokens": server,
                     "gap": None if server is None else server - ours, "error": out.get("error"),
                     "local_tokens_sorted_tool_keys": count_chat(tok, msgs, sorted_keys(tools)) if repo and tools else None,
                     "requested_model_id": out.get("requested_model_id"), "reasoning_effort": out.get("reasoning_effort"),
                     "served_model": out.get("served_model"), "cached": out.get("cached")})
    return rows


def canary_spec(name):
    """A make_canary.py spec: the no-hint prompt, rendered with the model's own chat template."""
    it = item()
    msgs, _ = build(it["question"], it["item_id"], "none")
    tok, sha = local_chat(REPOS[name])
    text = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
    return {"name": name, "text": text,
            "built_from": f"Track B pilot-0, condition none, rendered with {REPOS[name]}@{sha}'s chat template"}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--model", action="append", choices=sorted(REPOS))
    ap.add_argument("--canary-specs", metavar="DIR", help="write make_canary.py specs for the chat models; no calls")
    a = ap.parse_args()
    names = a.model or list(REPOS)
    if a.canary_specs:
        d = Path(a.canary_specs)
        d.mkdir(parents=True, exist_ok=True)
        for n in names:
            if REPOS[n]:
                (d / f"{n}.json").write_text(json.dumps(canary_spec(n), indent=1) + "\n")
                print(f"wrote {d / (n + '.json')}")
        return
    if a.dry_run:
        for n in names:
            print(f"{n}: {len(prompts(n))} calls (max_tokens 1) on {'chat' if REPOS[n] else 'completions'}; "
                  f"template {REPOS[n] or 'pinned'}")
        return
    for n in names:
        for r in check(n):
            append(OUT, r)
            print(f"{n:30} {r['condition']:14} ours {r['local_tokens']:5} server {r['server_tokens']} gap {r['gap']}"
                  + (f"  error {r['error']}" if r["error"] else ""))


if __name__ == "__main__":
    main()
