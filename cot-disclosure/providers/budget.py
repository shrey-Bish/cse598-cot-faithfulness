"""Spending caps for the paid providers (OpenAI, Anthropic, xAI).

  python -m providers.budget --status                     # spent and remaining per provider
  python -m providers.budget --table --output-tokens 4000 --input-tokens 500

- Caps come from cot-disclosure/.env: OPENAI_CAP_USD, ANTHROPIC_CAP_USD, XAI_CAP_USD
  (default 5 each). Prices come from configs/prices.yaml.
- Before a call, `guard()` assumes the worst case (the prompt plus max_tokens of output)
  and refuses the call if that could push the provider past its cap.
- After a call, `record()` prices the returned token usage and appends it to
  results/spend_log.jsonl. Running totals are always recomputed from that log.
- Voyager and Ollama are free and never logged here.
"""
import argparse
import fcntl
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone

import yaml

from .base import CODE, load_env

PAID = ("openai", "anthropic", "xai")
CAP_ENV = {"openai": "OPENAI_CAP_USD", "anthropic": "ANTHROPIC_CAP_USD", "xai": "XAI_CAP_USD"}
DEFAULT_CAP = 5.0
PRICES = CODE / "configs" / "prices.yaml"
LOG = CODE / "results" / "spend_log.jsonl"


class BudgetExceeded(RuntimeError):
    pass


def prices(path=PRICES):
    return yaml.safe_load(open(path))["models"]


def cap(provider):
    load_env()
    return float(os.environ.get(CAP_ENV[provider], DEFAULT_CAP))


def cost(model, input_tokens, output_tokens, table=None):
    p = (table or prices())[model]
    return ((input_tokens or 0) * p["input"] + (output_tokens or 0) * p["output"]) / 1e6


def spent(provider, log=None):
    log = log or LOG
    if not log.exists():
        return 0.0
    return sum(r["cost_usd"] for r in map(json.loads, open(log)) if r["provider"] == provider)


def estimate_input_tokens(messages):
    """Rough prompt size: about 4 characters per token, rounded up, plus a small overhead."""
    chars = sum(len(json.dumps(m)) for m in messages)
    return chars // 4 + 50


@contextmanager
def _locked(log):
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log.with_suffix(".lock"), "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def guard(provider, model, messages, max_tokens, log=None):
    """Raise BudgetExceeded if the worst case of this call could pass the provider's cap."""
    log = log or LOG
    if provider not in PAID:
        return 0.0
    worst = cost(model, estimate_input_tokens(messages), max_tokens)
    with _locked(log):
        total, limit = spent(provider, log), cap(provider)
    if total + worst > limit:
        raise BudgetExceeded(f"{provider}: spent ${total:.4f} + worst case ${worst:.4f} > cap ${limit:.2f}")
    return worst


def record(provider, model, usage, label="", log=None):
    """Price the returned usage and append it to the spend log; returns the cost."""
    log = log or LOG
    if provider not in PAID:
        return 0.0
    c = cost(model, usage.get("input_tokens"), usage.get("output_tokens"))
    row = {"timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "provider": provider,
           "model": model, "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
           "reasoning_tokens": usage.get("reasoning_tokens"), "cost_usd": round(c, 6), "label": label}
    with _locked(log):
        with open(log, "a") as f:
            f.write(json.dumps(row) + "\n")
    return c


def table(input_tokens, output_tokens, budget=DEFAULT_CAP):
    """Rows: model, provider, cost per call, calls per `budget` dollars (an estimate)."""
    rows = []
    for model, p in prices().items():
        per_call = cost(model, input_tokens, output_tokens)
        rows.append({"model": model, "provider": p["provider"], "usd_per_call": per_call,
                     "calls_per_budget": int(budget / per_call + 1e-9) if per_call else None})  # avoid float floor error
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--table", action="store_true")
    ap.add_argument("--input-tokens", type=int, default=500)
    ap.add_argument("--output-tokens", type=int, default=4000)
    a = ap.parse_args()
    if a.status or not a.table:
        for p in PAID:
            s, c = spent(p), cap(p)
            print(f"{p:10} spent ${s:.4f} of ${c:.2f}  (remaining ${c - s:.4f})")
    if a.table:
        print(f"| Model | Provider | Est. USD per call ({a.input_tokens} in / {a.output_tokens} out) | Est. calls per ${DEFAULT_CAP:.0f} |")
        print("|---|---|---|---|")
        for r in table(a.input_tokens, a.output_tokens):
            print(f"| {r['model']} | {r['provider']} | {r['usd_per_call']:.5f} | {r['calls_per_budget']:,} |")


if __name__ == "__main__":
    main()
