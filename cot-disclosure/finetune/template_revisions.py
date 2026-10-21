"""Which chat template does Voyager apply to olmo3-7b-think? Compare every revision of the
Olmo 3 7B Think and Instruct repos' templates with the server's prompt-token counts from
Step 1 (results/trackA/voyager_capabilities.jsonl). No model calls: only Hugging Face file
downloads and local rendering.

  python finetune/template_revisions.py
  python finetune/template_revisions.py --dry-run     # list the revisions it would check
"""
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import load  # noqa: E402
from finetune.olmo_format import _dict_args, render  # noqa: E402

REPOS = ["allenai/Olmo-3-7B-Think", "allenai/Olmo-3-7B-Instruct"]
CAPS = CODE / "results" / "trackA" / "voyager_capabilities.jsonl"


def templates_at(api, repo, rev):
    """{source file: template text} at one revision (chat_template.jinja and tokenizer_config.json)."""
    from huggingface_hub import hf_hub_download
    out = {}
    files = set(api.list_repo_files(repo, revision=rev))
    if "chat_template.jinja" in files:
        out["chat_template.jinja"] = Path(hf_hub_download(repo, "chat_template.jinja", revision=rev)).read_text()
    if "tokenizer_config.json" in files:
        cfg = json.loads(Path(hf_hub_download(repo, "tokenizer_config.json", revision=rev)).read_text())
        if isinstance(cfg.get("chat_template"), str):
            out["tokenizer_config.json"] = cfg["chat_template"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="list the revisions to check; download nothing")
    a = ap.parse_args()
    from huggingface_hub import HfApi
    from transformers import AutoTokenizer
    api = HfApi()
    commits = {repo: api.list_repo_commits(repo) for repo in REPOS}
    if a.dry_run:
        for repo, cs in commits.items():
            print(f"{repo}: {len(cs)} revisions to check")
        return
    tok = AutoTokenizer.from_pretrained("allenai/Olmo-3-7B-Think")
    n = lambda text: len(tok(text, add_special_tokens=False)["input_ids"])  # noqa: E731
    rows = {(r["condition"], r["arm"]): r for r in load(CAPS)}
    plain = rows[("0_baseline", "chat_no_hint")]
    tool = rows[("4_tool_turn", "chat_openai_tool_message")]
    tool_msgs = copy.deepcopy(tool["prompt_messages"])
    target = {"plain": plain["usage"]["prompt_tokens"], "tool_turn": tool["usage"]["prompt_tokens"]}
    print(f"server prompt tokens: plain question {target['plain']}, tool turn {target['tool_turn']}")
    seen = {}
    for repo, cs in commits.items():
        for c in reversed(cs):                                  # oldest first
            for src, text in templates_at(api, repo, c.commit_id).items():
                h = hashlib.sha256(text.encode()).hexdigest()[:12]
                if h in seen:
                    seen[h]["revisions"].append(f"{repo.split('/')[1]}@{c.commit_id[:7]}:{src}")
                    continue
                from transformers.utils.chat_template_utils import render_jinja_template
                counts = {"plain": n(render(plain["prompt_messages"], template=text))}
                try:          # as vLLM renders it: tool-call arguments parsed to a mapping, tools passed in
                    out, _ = render_jinja_template([_dict_args(tool_msgs)], tools=tool["tools"], chat_template=text,
                                                   add_generation_prompt=True, eos_token="<|endoftext|>")
                    counts["tool_turn"] = n(out[0])
                except Exception as err:
                    counts["tool_turn"] = f"error: {type(err).__name__}"
                seen[h] = {"revisions": [f"{repo.split('/')[1]}@{c.commit_id[:7]}:{src}"], "counts": counts,
                           "first_date": str(c.created_at.date())}
    print(f"\n{len(seen)} distinct templates across {sum(len(c) for c in commits.values())} revisions of 2 repos")
    print("| template | first seen | where | plain (server %d) | tool turn (server %d) |" % (target["plain"], target["tool_turn"]))
    print("|---|---|---|---|---|")
    for h, v in seen.items():
        where = v["revisions"][0] + (f" (+{len(v['revisions']) - 1} more)" if len(v["revisions"]) > 1 else "")
        mark = lambda k: f"**{v['counts'][k]}**" if v["counts"][k] == target[k] else str(v["counts"][k])  # noqa: E731
        print(f"| {h} | {v['first_date']} | {where} | {mark('plain')} | {mark('tool_turn')} |")
    out = CODE / "results" / "trackA" / "template_revisions.json"
    out.write_text(json.dumps({"server_prompt_tokens": target, "templates": seen}, indent=1) + "\n")
    print(f"\nsaved {out.relative_to(CODE.parent)}")


if __name__ == "__main__":
    main()
