"""Shared pieces for the agents: one JSONL step log and token accounting."""
import json
import threading
from datetime import datetime, timezone

_lock = threading.Lock()


def log_step(path, **rec):
    rec = {"timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), **rec}
    with _lock, open(path, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def tokens(reply):
    u = (reply.usage or {}) if reply else {}
    return {"input": u.get("input_tokens") or 0, "output": u.get("output_tokens") or 0}
