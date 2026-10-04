"""Phase 1: model catalog check and a timing run (validate runtime and token budgets).

  python progress/timing_run.py

1. GET /models: saves the catalog ids to results/progress/model_catalog.json and
   checks that all six study models are listed.
2. One call per model on pilot puzzle 0 with no hint, seed 0: the exact payload
   of the pilot's first no-hint run, so it also checks that a seeded call repeats.
3. One MMLU-Pro item (the first of mmlupro_30.jsonl, no cue, seed 0) on each of
   the three Experiment B models. Same payload as Experiment B's first no-cue run,
   so Experiment B reuses these replies from the cache.
Then projects Experiment B's wall time at four requests in flight.
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor

from common import OUT, append, call, get_logger, load

import experiments as pilot  # noqa: E402
from client import list_models  # noqa: E402
from mmlu_pro_probe import MODELS as B_MODELS, build_prompt as b_prompt, load_items  # noqa: E402

TIMING = OUT / "timing.jsonl"
log = get_logger("timing")


def catalog():
    for attempt in (1, 2):
        try:
            ids = sorted(m["id"] for m in list_models())
            break
        except Exception as err:
            log.error(f"/models attempt {attempt} failed: {type(err).__name__} {getattr(err, 'code', '')}")
    else:
        sys.exit("STOP: /models failed twice (see docs/progress/BLOCKERS.md)")
    (OUT / "model_catalog.json").write_text(json.dumps({"ids": ids}, indent=1))
    missing = [m for m in pilot.MODELS if m not in ids]
    log.info(f"catalog: {len(ids)} ids; study models present: {6 - len(missing)}/6; missing: {missing}")
    if missing:
        sys.exit(f"STOP: missing model ids {missing}")


def pilot_call(model):
    prompt, _ = pilot.build_prompt(0, "none", 0, pilot.STEPS)
    item = pilot.ITEMS[0]
    return call(log, experiment="timing", item_id="pilot-0", model=model, condition="none", repeat=0,
                messages=[{"role": "user", "content": prompt}], n_options=len(item["options"]),
                correct_letter=item["correct"], seed=0, extra={"source": "pilot"})


def mmlu_call(model, item):
    return call(log, experiment="timing", item_id=item["question_id"], model=model, condition="nocue",
                repeat=0, messages=[{"role": "user", "content": b_prompt(item)}], n_options=10,
                correct_letter=item["answer"], seed=0, extra={"source": "mmlu-pro"})


def main():
    catalog()
    item = load_items()[0]
    jobs = [(pilot_call, m) for m in pilot.MODELS] + [(mmlu_call, m, item) for m in B_MODELS]
    with ThreadPoolExecutor(4) as pool:
        for rec in pool.map(lambda j: j[0](*j[1:]), jobs):
            append(TIMING, rec)

    rows = load(TIMING)
    stored = {(r["model"], r["item"]): r for r in load(pilot.OUT)
              if r["exp"] == "main" and r["cue_kind"] == "none" and r["seed"] == 0}
    for r in rows:
        if r.get("source") == "pilot":
            old = stored[(r["model"], 0)]
            same = (r["parsed_letter"] == old["answer"]
                    and len(r["reasoning_text"] or "") == old["trace_chars"]
                    and len(r["final_text"]) == old["answer_chars"])
            log.info(f"replay check {r['model']}: pilot answer={old['answer']} trace={old['trace_chars']} "
                     f"answer_chars={old['answer_chars']} tokens={old['out_tokens']} | now "
                     f"answer={r['parsed_letter']} trace={len(r['reasoning_text'] or '')} "
                     f"answer_chars={len(r['final_text'])} tokens={(r['usage'] or {}).get('completion_tokens')} "
                     f"identical={same}")

    # projection for Experiment B: 30 items x 3 models x 2 runs at 4 in flight
    mm = {r["model"]: r for r in rows if r.get("source") == "mmlu-pro" and r["latency_s"]}
    if len(mm) == len(B_MODELS):
        per_round = sum(r["latency_s"] for r in mm.values())  # one call per model
        nocue_min = per_round * 30 * 2 / 4 / 60
        cued_min = per_round * 20 * 2 / 4 / 60
        log.info(f"projection expB: no-cue {nocue_min:.0f} min + cued {cued_min:.0f} min at 4 in flight "
                 f"(from one MMLU-Pro call per model: "
                 + ", ".join(f"{m} {r['latency_s']}s/{(r['usage'] or {}).get('completion_tokens')} tok"
                             for m, r in mm.items()) + ")")


if __name__ == "__main__":
    main()
