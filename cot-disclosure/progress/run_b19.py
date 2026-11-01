"""Track B, B19 (Nov 1): B16's tool arms again, now the same day as its authority arm. Pre-registered as B16's amendment
(archive/sessions/2026-10-31/2026-10-31_2220_B_b16-prereg.md, section 9).

  python progress/run_b19.py --dry-run           # jobs, calls, hours
  python progress/run_b19.py --run               # resumable; results/trackB/b19_voyager.jsonl.gz (gitignored)
  python progress/run_b19.py --report            # B16's rule on B19's tool arms -> results/trackB/b19_report.json

Why (FINDINGS T11): B16's tool arms sent Track B's exact requests, so client.py's reply cache gave back Track B's Oct
27-28 replies for 907 of 972, and B16's primary comparison was cross-day. B19 is B16's three models, 54 questions,
settings and tool arms (run_b16.arms without user_authority), with T11's fix:
  new seeds   repeats 3-5: run_trackB sends the repeat as the seed, and Track B and B16 ran 0-2 (Voyager gives the same
              reply to the same request and seed, as C18 did C16's, so new seeds are needed even without the cache)
  no cache    use_cache=False on every request the run sends (no_cache()): no reply is read from or written to cache/
B16's user_authority runs (Oct 31 22:25 - Nov 1 02:36; a new prompt, so none came from the cache) are the comparison.

Report (B16's report, run_b16.model_report, with B19's tool arms in place of B16's):
  primary   each B19 tool arm minus B16's user_authority, paired by question: B16's rule and readings, the 16,000 cut
            beside it, and each reading beside B16's (same, or changed)
  drift     B19's tool arms minus Track B's (Oct 27-28): a real check across the days now, as B16's tool arms were replays
  secondary and per arm, as B16's (the plain user hint is still Track B's, cross-day)
  replays   per model and arm, B19 runs whose final and private texts both equal a Track B run's of the same question
            (expected none for the two thinking models; Instruct's short replies can match by chance)
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import yaml

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

import client  # noqa: E402
import run_b16 as b16  # noqa: E402
import run_trackB as tb  # noqa: E402
from common import latest, load, run_id  # noqa: E402
from tools.answer_key import AUTHORITY  # noqa: E402
from trackB_report import counts, flags  # noqa: E402

EXPERIMENT = "b19"
REPEATS = (3, 4, 5)                                   # the seeds: Track B and B16 ran repeats 0-2
tb.FILE_PREFIX.setdefault(EXPERIMENT, "b19_")         # B19's own records files (run_trackB.py waits for D12, as below)


def jobs(cfg):
    """B16's tool-arm jobs at repeats 3-5, repeat by repeat."""
    items = [it for s in b16.SETS for it in tb.load_questions(s, cfg["question_sets"][s])]
    models = [next(m for m in cfg["models"] if m["model"] == name) for name in b16.MODELS]
    return [{"run_id": run_id(EXPERIMENT, item["item_id"], tb.model_tag(m), cond, None, rep), "model": m,
             "item": item, "condition": cond, "repeat": rep, "experiment": EXPERIMENT}
            for rep in REPEATS for item in items for m in models for cond in b16.arms(m["model"])[1:]]


def no_cache():
    """use_cache=False on every request this process sends. client.chat() and complete() don't take it, and client.py
    stays as it is while Sol's queued jobs load it (TODO D12), so its _request is wrapped here."""
    send = client._request

    def without_cache(*args, **kw):
        return send(*args, **{**kw, "use_cache": False})
    client._request = without_cache


def dry_run(cfg, todo):
    print(f"B19: {len(todo)} jobs to run; hours use each model's est_seconds per call, {cfg['in_flight']} in flight "
          f"(shared with every Voyager run on this Mac)")
    for tag, row in tb.plan(cfg, todo).items():
        print(f"  {tag:45} {row['jobs']:6,} jobs {row['calls']:6,} calls {row['hours']:6.1f} h   free")


# ---------------------------------------------------------------- report
def b19_flags(out=tb.OUT):
    return [{**flags(r), "source": "b19"} for r in latest(load(Path(out) / "b19_voyager.jsonl.gz"))
            if r.get("experiment") == EXPERIMENT and r["status"] == "ok" and counts(r)]


def report(new, before, old):
    """new: B19's flags; before: B16's (its user_authority arm is the comparison); old: Track B's."""
    res = b16.report([r for r in before if r["condition"] == AUTHORITY] + new, old)
    was = b16.report(before, old)
    for m, e in res.items():
        e["b19_runs"] = sum(r["model"] == m for r in new)
        for key in ("primary", "primary_16k"):
            for c, x in e[key].items():
                x["b16_reading"] = was[m][key][c]["reading"]
                x["same_as_b16"] = x["reading"] == x["b16_reading"]
    return res


def replays(out=tb.OUT):
    """{model: {arm: {identical, runs}}}: B19 runs whose final and private texts both equal a Track B run's of the same
    model, question and arm."""
    def key(r):
        return r["model"], r["item_id"], r["condition"]
    seen = defaultdict(set)
    for r in latest(load(Path(out) / "voyager.jsonl.gz")):
        if r.get("experiment") == "trackB" and r["model"] in b16.MODELS:
            seen[key(r)].add((r.get("final_text") or "", r.get("reasoning_text") or ""))
    res = defaultdict(lambda: defaultdict(lambda: {"identical": 0, "runs": 0}))
    for r in latest(load(Path(out) / "b19_voyager.jsonl.gz")):
        if r.get("experiment") == EXPERIMENT and r["status"] == "ok":
            e = res[r["model"]][r["condition"]]
            e["runs"] += 1
            e["identical"] += (r.get("final_text") or "", r.get("reasoning_text") or "") in seen[key(r)]
    return {m: dict(arms) for m, arms in res.items()}


def show(res):
    def d(x):
        return ("too few questions" if x["diff"] is None
                else f"{x['diff']:+.0%} [{x['interval'][0]:+.0%}, {x['interval'][1]:+.0%}] ({x['questions']} q)")

    def same(x):
        return "same as B16" if x["same_as_b16"] else f"CHANGED from B16's {x['b16_reading']}"
    lines = []
    for model, e in res.items():
        lines.append(f"\n{model} ({e['b19_runs']} B19 runs)")
        for c, x in e["arms"].items():
            f = x["following"]
            lines.append(f"  {c} ({'B16' if c == AUTHORITY else 'B19'}): following {f['k']} of {f['n']} ({f['questions']} q)"
                         + (f"; replays {e['replays'][c]['identical']} of {e['replays'][c]['runs']}"
                            if c in e.get("replays", {}) else ""))
        for c, x in e["primary"].items():
            y = e["primary_16k"][c]
            lines.append(f"  PRIMARY {c} (B19) - {AUTHORITY} (B16): {d(x)} -> {x['reading']}, {same(x)}"
                         f"   (16,000 cut: {d(y)} -> {y['reading']}, {same(y)})")
            share = e["secondary"][c]["share_of_gap_closed"]
            lines.append(f"  drift {c}, B19 - Track B: {d(e['drift'][c])} -> {e['drift'][c]['reading']}; share of Gate 2's "
                         f"gap closed by authority {'n/a' if share is None else f'{share:.0%}'}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--report", action="store_true")
    ap.add_argument("--limit", type=int, help="run at most N jobs (smoke tests)")
    ap.add_argument("--stop-file", help="start no new job once this file exists (progress/guard.py)")
    a = ap.parse_args()
    cfg = yaml.safe_load(open(tb.CONFIG))
    if a.report:
        res = report(b19_flags(), b16.b16_flags(), b16.trackb_flags())
        for m, arms in replays().items():
            res[m]["replays"] = arms
        (tb.OUT / "b19_report.json").write_text(json.dumps(res, indent=1) + "\n")
        print(show(res))
        return
    all_jobs = jobs(cfg)
    if a.dry_run:
        finished = tb.done("voyager", EXPERIMENT)
        return dry_run(cfg, [j for j in all_jobs if j["run_id"] not in finished])
    no_cache()
    try:
        return tb.run(cfg, all_jobs, a.limit, a.stop_file)
    except (client.CanaryFailed, client.ModelUnavailable) as err:
        tb.log.error(f"halted: {type(err).__name__}: {err}")
        return 3


if __name__ == "__main__":
    sys.exit(main() or 0)
