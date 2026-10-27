"""Store the identity-canary reference for one model (client.py guard c): one echo call on a
fixed short text through the current route, never served from the cache.

  python progress/make_canary.py --spec path/to/spec.json --dry-run
  python progress/make_canary.py --spec path/to/spec.json      # -> configs/canary/<name>.json

spec.json: {"name": our model name, "text": the reference text (rendered prompt), "built_from": ...,
            optional "template_sha256"}. The text must be under 2,048 tokens on the server: past
2,048 tokens long prompts are processed in chunks and log-probs drift slightly (2026-10-21).
The reference is refused unless the server reports `name` as the model that answered.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

import client  # noqa: E402

MAX_TOKENS_REF = 2048
PARAMS = {"temperature": 0.6, "seed": 0}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    spec = json.loads(Path(a.spec).read_text())
    name = spec["name"]
    vid, effort = client.route(name)
    out_path = client.CANARY_DIR / f"{name}.json"
    print(f"{name} -> {vid} at reasoning_effort={effort}; {len(spec['text'])} chars; 1 echo call -> "
          f"{out_path.relative_to(CODE.parent)}")
    if a.dry_run:
        return
    from common import slot
    with slot():                                                # one of the 4 requests in flight, like every run
        client.check_catalog(name)                              # guard b first
        out = client.canary_request(name, {"text": spec["text"], "params": PARAMS})
    if out["error"]:
        sys.exit(f"echo call failed: {out['error']}")
    n = (out.get("usage") or {}).get("prompt_tokens")
    if out.get("served_model") != name:
        sys.exit(f"server reports {out.get('served_model')!r}, not {name}: no reference stored")
    if not n or n >= MAX_TOKENS_REF:
        sys.exit(f"reference text is {n} tokens on the server; it must be under {MAX_TOKENS_REF}")
    ref = {"name": name, "requested_model_id": out["requested_model_id"], "reasoning_effort": out["reasoning_effort"],
           "served_model": out["served_model"], "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "prompt_tokens": n, "params": PARAMS, "rule": {"top_token": "same at every position", "max_abs_diff": client.CANARY_TOL},
           "built_from": spec.get("built_from"), "template_sha256": spec.get("template_sha256"),
           "text": spec["text"], "logprobs": out["logprobs"][:n]}       # prompt tokens only (the last one is generated)
    client.CANARY_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(ref, indent=1) + "\n")
    print(f"stored: {n} prompt tokens, served by {out['served_model']}")


if __name__ == "__main__":
    main()
