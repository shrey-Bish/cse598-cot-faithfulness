"""Voyager replaced its model IDs on 2026-10-21 (olmo3-7b-think -> family "olmo3-7b", where
reasoning_effort picks the member). Before resuming, check the new route. 8 calls.

  1 routing: /v1/completions with reasoning_effort low / medium / high (the echo calls of
    check 2), and one short chat request at each level, comparing prompt_tokens (does the
    level add text to the prompt on the chat route?)
  2 same model: echo log-probabilities of Step 1's exact prompt at low / medium / high,
    against those saved from the old olmo3-7b-think (Step 1 call 8). Pass = the same top
    token at every position and max |difference| < 0.01 (batching moves log-probs a little)
  3 default: the same echo with no reasoning_effort (should be the Instruct model)

  python finetune/voyager_ids_check.py --dry-run
  python finetune/voyager_ids_check.py           # records -> results/trackA/voyager_ids_check.jsonl.gz

Requests are made here directly (streamed) so the raw response fields, including the model
name the server reports, are saved as they come.
"""
import argparse
import json
import statistics
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

import client  # noqa: E402
from common import append, load  # noqa: E402

FAMILY = "olmo3-7b"
LEVELS = ("low", "medium", "high")
TOL = 0.01
OUT = CODE / "results" / "trackA" / "voyager_ids_check.jsonl.gz"
STEP1 = CODE / "results" / "trackA" / "voyager_capabilities.jsonl.gz"
SHORT = [{"role": "user", "content": "What is 2 + 3? Reply with just the number."}]


def stream(path, body):
    """One streamed request; returns the folded fields plus the server's model name per chunk."""
    req = urllib.request.Request(f"{client.BASE_URL}{path}",
                                 data=json.dumps({**body, "stream": True, "stream_options": {"include_usage": True}}).encode(),
                                 headers={"Authorization": f"Bearer {client.API_KEY}", "Content-Type": "application/json"})
    served, start = set(), time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            lines = []
            for raw in resp:
                line = raw.decode("utf-8", "replace").strip()
                if line.startswith("data:") and line[5:].strip() not in ("", "[DONE]"):
                    served.add(json.loads(line[5:]).get("model"))
                lines.append(raw)
        out = client.parse_stream_lines(lines)
        out["error"] = None
    except urllib.error.HTTPError as err:
        out = {"error": f"HTTP {err.code}: {client._error_detail(err)}", "usage": {}, "logprobs": [], "content": ""}
    out.update({"served_model": sorted(m for m in served if m), "latency_s": round(time.monotonic() - start, 2)})
    return out


def compare(ref, new):
    """Prompt-token log-probabilities, position by position (the last entry is the generated token)."""
    a, b = ref[:-1], new[: len(ref) - 1]
    if len(b) != len(a):
        return {"pass": False, "reason": f"length {len(b)} vs {len(a)}"}
    if [x["token"] for x in a] != [x["token"] for x in b]:
        return {"pass": False, "reason": "different tokens"}
    top = lambda e: max((e.get("top_logprobs") or {}).items(), key=lambda kv: kv[1])[0] if e.get("top_logprobs") else None  # noqa: E731
    pos = [i for i in range(len(a)) if a[i]["logprob"] is not None and b[i]["logprob"] is not None]
    diffs = [abs(a[i]["logprob"] - b[i]["logprob"]) for i in pos]
    top_mismatch = [i for i in pos if top(a[i]) != top(b[i])]
    res = {"positions": len(pos), "mean_abs_diff": statistics.mean(diffs), "max_abs_diff": max(diffs),
           "top_token_mismatches": len(top_mismatch), "first_mismatches": top_mismatch[:5]}
    res["pass"] = not top_mismatch and res["max_abs_diff"] < TOL
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    ref_rec = next(r for r in load(STEP1) if r["arm"] == "completions_echo_served_template")
    prompt, ref = ref_rec["rendered_prompt"], ref_rec["logprobs"]
    plan = ([("chat_prompt_tokens", lvl) for lvl in LEVELS]
            + [("echo_identity", lvl) for lvl in LEVELS] + [("echo_default", None)])
    if a.dry_run:
        print(f"reference: Step 1 echo on old olmo3-7b-think, {len(ref) - 1} prompt tokens (run {ref_rec['run_id']})")
        for check, lvl in plan:
            print(f"  {check:20} {FAMILY} reasoning_effort={lvl}")
        print(f"{len(plan)} calls -> {OUT.relative_to(CODE.parent)}")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    results = []
    for check, lvl in plan:
        effort = {"reasoning_effort": lvl} if lvl else {}
        if check == "chat_prompt_tokens":
            out = stream("/chat/completions", {"model": FAMILY, "messages": SHORT, "max_tokens": 1, "temperature": 0.6,
                                               "seed": 0, **effort})
        else:
            out = stream("/completions", {"model": FAMILY, "prompt": prompt, "max_tokens": 1, "temperature": 0.6,
                                          "seed": 0, "echo": True, "logprobs": 1, **effort})
        row = {"check": check, "requested_model_id": FAMILY, "reasoning_effort": lvl, "served_model": out["served_model"],
               "error": out["error"], "prompt_tokens": (out.get("usage") or {}).get("prompt_tokens"),
               "latency_s": out["latency_s"], "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        if check != "chat_prompt_tokens" and not out["error"]:
            row["vs_old_olmo3_7b_think"] = compare(ref, out["logprobs"])
            row["logprobs"] = out["logprobs"]
        append(OUT, row)
        results.append(row)
        print(f"{check:20} effort={str(lvl):6} served={out['served_model']} prompt_tokens={row['prompt_tokens']} "
              f"error={out['error']} " + (json.dumps({k: v for k, v in row.get('vs_old_olmo3_7b_think', {}).items()
                                                      if k != 'first_mismatches'}) if 'vs_old_olmo3_7b_think' in row else ""))


if __name__ == "__main__":
    main()
