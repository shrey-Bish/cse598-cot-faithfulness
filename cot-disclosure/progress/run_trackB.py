"""Track B: the same wrong hint through four channels, on more models (see docs/plan/TRACK_B_test_widely.md).

  python progress/run_trackB.py --dry-run                     # call count and estimated cost per provider
  python progress/run_trackB.py --run --only-provider voyager # resumable; writes results/trackB/<provider>.jsonl

Every (model, thinking, question, condition, run) is one job with a deterministic run_id;
finished jobs are skipped on restart. Paid providers go through the budget guard
(providers/budget.py) and stop at their cap. Each record keeps the prompt, the reply,
the private reasoning (or summary, or none), its visibility, the tool steps and usage.
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

import yaml

from common import CODE, append, done_ids, get_logger, run_id

sys.path.insert(0, str(CODE))
import experiments as pilot  # noqa: E402
from parse import parse_answer  # noqa: E402
from providers import budget, generate  # noqa: E402
from providers.base import MissingKey  # noqa: E402
from tools.answer_key import build, run_tool_loop  # noqa: E402

CONFIG = CODE / "configs" / "trackB.yaml"
OUT = CODE / "results" / "trackB"
LETTERS = "ABCDEFGHIJ"
log = get_logger("trackB")


def load_questions(name, spec):
    """Items as {item_id, question (with lettered options), correct, hint_letter, n_options}."""
    if spec["source"] == "pilot":
        return [{"set": name, "item_id": f"pilot-{i}", "question": it["question"], "correct": it["correct"],
                 "hint_letter": pilot.WRONG_CUES[(i, 0)], "n_options": len(it["options"])}
                for i, it in enumerate(pilot.ITEMS[:spec.get("n", len(pilot.ITEMS))])]
    path = CODE / spec["path"]
    if not path.exists():
        log.warning(f"question set {name}: {spec['path']} not found ({spec.get('note', '')}); skipped")
        return []
    items = [json.loads(line) for line in open(path)]
    if spec["source"] == "mmlupro":
        return [{"set": name, "item_id": f"mmlupro-{it['question_id']}",
                 "question": it["question"] + "\n" + "\n".join(f"({LETTERS[i]}) {o}" for i, o in enumerate(it["options"])),
                 "correct": it["answer"], "hint_letter": it["cue_letter"], "n_options": len(it["options"])}
                for it in items]
    return [{"set": name, **it} for it in items]   # gpqa: export already in this item format


def jobs(cfg, only_provider=None):
    sets = {n: load_questions(n, s) for n, s in cfg["question_sets"].items()}
    out = []
    for m in cfg["models"]:
        if only_provider and m["provider"] != only_provider:
            continue
        for set_name in m.get("question_sets", list(sets)):
            for item in sets[set_name]:
                for cond in m.get("conditions", cfg["conditions"]):
                    for rep in range(m.get("runs_per_question", cfg["runs_per_question"])):
                        tag = f"{m['model']}|think={m.get('thinking')}"
                        out.append({"run_id": run_id("trackB", item["item_id"], tag, cond, None, rep), "model": m,
                                    "item": item, "condition": cond, "repeat": rep})
    return out


def plan(cfg, todo):
    """Jobs and estimated cost per provider (tool_real counts two calls: lookup + answer)."""
    est = cfg["estimate"]
    out = {}
    for j in todo:
        p, model = j["model"]["provider"], j["model"]["model"]
        row = out.setdefault(p, {"jobs": 0, "calls": 0, "est_usd": 0.0, "paid": p in budget.PAID})
        n = 2 if j["condition"] == "tool_real" else 1
        row["jobs"] += 1
        row["calls"] += n
        if p in budget.PAID:
            row["est_usd"] += n * budget.cost(model, est["input_tokens"], est["output_tokens"])
    for p, row in out.items():
        row["est_usd"] = round(row["est_usd"], 2)
        if row["paid"]:
            row["cap_usd"] = budget.cap(p)
    return out


def dry_run(cfg, todo):
    est = cfg["estimate"]
    print(f"Track B plan: {len(todo)} jobs ({cfg['runs_per_question']} runs per question by default), estimate "
          f"assumes {est['input_tokens']} input / {est['output_tokens']} output tokens per call")
    for p, row in sorted(plan(cfg, todo).items()):
        line = f"  {p:10} {row['jobs']:6,} jobs {row['calls']:6,} calls"
        if row["paid"]:
            over = row["est_usd"] > row["cap_usd"]
            line += f"   est. ${row['est_usd']:8.2f}   cap ${row['cap_usd']:.2f}   {'OVER CAP: trim the plan' if over else 'within cap'}"
        else:
            line += "   free"
        print(line)


def run_one(cfg, j):
    m, item = j["model"], j["item"]
    msgs, tools = build(item["question"], item["item_id"], j["condition"],
                        None if j["condition"] == "none" else item["hint_letter"])
    paid = m["provider"] in budget.PAID
    kw = {"thinking": m.get("thinking"), "max_tokens": cfg["closed_max_tokens"] if paid else cfg["max_tokens"],
          "temperature": cfg["temperature"], "seed": j["repeat"], "label": f"trackB:{j['run_id']}"}
    gen = lambda **k: generate(m["provider"], m["model"], **{**kw, **k})  # noqa: E731
    steps = []
    if tools:
        reply, transcript, steps = run_tool_loop(gen, msgs, tools, question_id=item["item_id"],
                                                 letter=item["hint_letter"], force_first=False)
    else:
        reply, transcript = gen(messages=msgs), msgs
    letter = parse_answer(reply.final_text, item["n_options"])[0] if not reply.error else None
    return {"run_id": j["run_id"], "experiment": "trackB", "provider": m["provider"], "model": m["model"],
            "thinking": m.get("thinking"), "set": item["set"], "item_id": item["item_id"], "condition": j["condition"],
            "repeat": j["repeat"], "hint_letter": None if j["condition"] == "none" else item["hint_letter"],
            "correct_letter": item["correct"], "parsed_letter": letter, "status": "api_error" if reply.error else "ok",
            "error_type": reply.error, "finish_reason": reply.finish_reason, "final_text": reply.final_text,
            "reasoning_text": reply.reasoning_text, "reasoning_visibility": reply.reasoning_visibility,
            "tool_steps": steps, "called_tool": bool(steps and steps[0]["tool_calls"]), "usage": reply.usage,
            "latency_s": reply.latency_s, "cost_usd": reply.cost_usd, "prompt_messages": msgs, "transcript": transcript}


def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--run", action="store_true")
    ap.add_argument("--only-provider")
    ap.add_argument("--limit", type=int, help="run at most N jobs (smoke tests)")
    a = ap.parse_args()
    cfg = yaml.safe_load(open(CONFIG))
    all_jobs = jobs(cfg, a.only_provider)
    OUT.mkdir(parents=True, exist_ok=True)
    todo = [j for j in all_jobs if j["run_id"] not in done_ids(OUT / f"{j['model']['provider']}.jsonl")]
    if a.dry_run:
        dry_run(cfg, todo)
        return
    todo = todo[: a.limit] if a.limit else todo
    workers = 4 if a.only_provider in (None, "voyager") else 1   # paid providers: one at a time under the guard

    def safe(j):
        try:
            return run_one(cfg, j)
        except (budget.BudgetExceeded, MissingKey) as err:
            log.error(f"stopped {j['model']['provider']}: {err}")
            return None
    with ThreadPoolExecutor(workers) as pool:
        for rec in pool.map(safe, todo):
            if rec:
                append(OUT / f"{rec['provider']}.jsonl", rec)


if __name__ == "__main__":
    main()
