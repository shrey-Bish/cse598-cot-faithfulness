"""A39's synthetic finish (Nov 4): part files of the real shape, so finetune/a39.py and tools/a39_figures.py can be run
end to end before any real A39 run is read. Nothing here opens a real A39 file: the shapes come from the code that
writes them (finetune/eval.py's jobs, stem and runs_files; eval.run's resume by run id) and from the Nov 4 queue's
part lines (finetune/gpu/sol/queue_2026-11-04.txt; the A39 log's sections 10-12).

build(out, qset) writes what the jobs leave in $TRACKA_OUT/a39 once every A39 job has ended:
  E2     base: quarters 1-3, its fourth quarter as sixteenths 4, 8, 12, 16, and the bench (part 2/2, its first 36 runs,
         Nov 3); prompt_only, lora, lora_note: quarters 1-2 and sixteenths 3, 4, 7, 8, 11, 12, 15, 16; the wrapper
         systems: fifths; every system then a sweep (no part: eval_<system>_a39_e2_runs.jsonl) for what its parts left
  the 30 the core systems in quarters, the wrapper systems in halves, a sweep each
Each part saves the first `done_share` of the runs it has left (a part stopped at its time limit), skipping what an
earlier file holds (resume by run id); `flaky` runs get a not_run record and then their ok record in the same file
(eval.run's retry pass). Outcomes are seeded per run (random.Random(seed:run_id)), so the set is the same however it
is built. CPU only, no network."""
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

pytest.importorskip("transformers")

from common import latest, load  # noqa: E402
from finetune import eval as ev  # noqa: E402

CORE = ("base", "prompt_only", "lora", "lora_note")
WRAPPERS = tuple(ev.SHARED)
SIXTEENTHS_34 = tuple((k, 16) for k in (3, 4, 7, 8, 11, 12, 15, 16))   # quarters 3 and 4, as sixteenths
SHAPES = {"e2": {"base": ((1, 4), (2, 4), (3, 4), (4, 16), (8, 16), (12, 16), (16, 16)),
                 **{s: ((1, 4), (2, 4)) + SIXTEENTHS_34 for s in CORE[1:]},
                 **{s: tuple((k, 5) for k in range(1, 6)) for s in WRAPPERS}},
          "mmlupro_30": {**{s: tuple((k, 4) for k in range(1, 5)) for s in CORE},
                         **{s: ((1, 2), (2, 2)) for s in WRAPPERS}}}
BENCH = {"e2": ("base", (2, 2), 36)}          # job 389340: base e2 2/2 --limit 96, 36 runs saved (the log's section 11)
CAP = "hit the token cap"                     # finetune/continuation.py's no-answer reason past the cap


def rates(follow, accept=0.9, accuracy=0.55, no_answer=0.03, mention=0.4):
    return {"follow": follow, "accept": accept, "accuracy": accuracy, "no_answer": no_answer, "mention": mention}


PROFILE = {"base": rates({"user": 0.30, "tool_pasted": 0.55, "tool_injected": 0.60}),
           "prompt_only": rates({"user": 0.20, "tool_pasted": 0.40, "tool_injected": 0.45}, accept=0.88),
           "lora": rates({"user": 0.22, "tool_pasted": 0.45, "tool_injected": 0.50}, accept=0.85, accuracy=0.53),
           "lora_note": rates({"user": 0.15, "tool_pasted": 0.30, "tool_injected": 0.35}, accept=0.84, accuracy=0.53),
           "wrap": rates({"tool_injected": 0.35}, accept=0.80),
           "wrap_note": rates({"tool_injected": 0.25}, accept=0.80),
           "lora_wrap": rates({"tool_injected": 0.30}, accept=0.78)}


def other(letter):
    return "A" if letter != "A" else "B"


def record(system, j, p, seed=0):
    """One run's numbers-only record, as eval.run_one writes it (eval.save drops the texts): its outcome seeded by
    its run id. p: the system's rates()."""
    rid = ev.job_id(system, j)
    rng = random.Random(f"{seed}:{rid}")
    capped = rng.random() < p["no_answer"]
    if capped:
        letter = None
    elif j["wording"] == "none":
        letter = j["correct_letter"] if rng.random() < p["accuracy"] else other(j["correct_letter"])
    elif j["hint_correct"]:
        letter = j["correct_letter"] if rng.random() < p["accept"] else other(j["correct_letter"])
    else:
        letter = j["hint_letter"] if rng.random() < p["follow"][j["channel"]] else j["correct_letter"]
    mention = rng.random() < p["mention"]
    flags = {} if j["channel"] == "none" else {
        "mention_final": mention, "mention_final_broad": mention, "mention_reasoning": True, "says_disagrees": False,
        "says_independent": False}
    return {"run_id": rid, "experiment": j["experiment"], "system": system, "timestamp_utc": "2026-11-05T00:00:00+00:00",
            **{k: j[k] for k in ("item_id", "wording", "channel", "hint_letter", "hint_correct", "correct_letter", "repeat")},
            "parsed_letter": letter, "status": "ok", "error_type": None, "finish_reason": "length" if capped else "stop",
            "no_answer_reason": CAP if capped else None, "prompt_tokens": 900, "completion_tokens": 32768 - 900 if capped
            else 9000, "tool_calls_by_model": 0, "rounds": 1, "seconds": 600.0, "engine": "vllm-server", **flags}


def failed(rec):
    """The not_run record a run with no reply leaves before its retry (eval.run_one with an error)."""
    return {**{k: v for k, v in rec.items() if not k.startswith(("mention", "says"))}, "parsed_letter": None,
            "status": "not_run", "error_type": "connection: reset by peer", "finish_reason": "error",
            "no_answer_reason": None, "prompt_tokens": None, "completion_tokens": None}


def steps(qset, system):
    """(part or None for the sweep, how many of its runs left it saves: a share, or (count,) for the bench)."""
    bench = [(BENCH[qset][1], (BENCH[qset][2],))] if BENCH.get(qset, (None,))[0] == system else []
    return bench + [(p, None) for p in SHAPES[qset][system]] + [(None, 1.0)]


def build(out, qset="e2", profile=None, seed=0, done_share=0.9, n=None, systems=ev.A39_SYSTEMS, flaky=0.0):
    """Every A39 file a finished run of `qset` leaves in OUT (numbers only): {path: records}. n: the first n questions
    only (a smaller set, same shapes)."""
    out, profile = Path(out), {**PROFILE, **(profile or {})}
    out.mkdir(parents=True, exist_ok=True)
    keep = {q["item_id"] for q in ev.questions(qset)[:n]} if n else None
    files = {}
    for s in systems:
        done = set()
        for part, share in steps(qset, s):
            todo = [j for j in ev.jobs(part, qset=qset, design="a39", system=s)
                    if ev.job_id(s, j) not in done and (keep is None or j["item_id"] in keep)]
            count = share[0] if isinstance(share, tuple) else math.ceil((done_share if share is None else share) * len(todo))
            recs = []
            for j in todo[:count]:
                rec = record(s, j, profile[s], seed)
                if random.Random(f"{seed}:flaky:{rec['run_id']}").random() < flaky:
                    recs.append(failed(rec))
                recs.append(rec)
                done.add(rec["run_id"])
            path = out / f"{ev.stem(s, part, qset, 'a39')}_runs.jsonl"
            path.write_text("".join(json.dumps(r) + "\n" for r in recs))
            files[path] = recs
    return files


def expected(qset, systems=ev.A39_SYSTEMS, n=None):
    keep = {q["item_id"] for q in ev.questions(qset)[:n]} if n else None
    return {s: {ev.job_id(s, j) for j in ev.jobs(qset=qset, design="a39", system=s)
                if keep is None or j["item_id"] in keep} for s in systems}


# ---------------------------------------------------------------- the builder itself
@pytest.mark.parametrize("qset", ["e2", "mmlupro_30"])
def test_the_shapes_cover_every_run_once_and_the_files_are_eval_s_own(tmp_path, qset):
    for s in ev.A39_SYSTEMS:
        every = [ev.job_id(s, j) for p in SHAPES[qset][s] for j in ev.jobs(p, qset=qset, design="a39", system=s)]
        assert Counter(every) == Counter(expected(qset)[s])                 # the parts: each run once, none left out
    files = build(tmp_path, qset)
    for s in ev.A39_SYSTEMS:
        mine = [p for p in files if p.name.startswith(f"eval_{s}_a39_{qset}")]
        assert sorted(mine) == sorted(ev.runs_files(tmp_path, s, qset, "a39"))   # what the report and resume read
        rows = latest([r for p in mine for r in load(p)])
        assert {r["run_id"] for r in rows} == expected(qset)[s] and all(r["status"] == "ok" for r in rows)
        assert len(load(tmp_path / f"{ev.stem(s, None, qset, 'a39')}_runs.jsonl")) > 0      # the sweep had runs left
    if qset == "e2":
        bench = load(tmp_path / "eval_base_a39_e2_p2of2_runs.jsonl")
        assert [r["run_id"] for r in bench] == [ev.job_id("base", j)
                                                for j in ev.jobs((2, 2), qset="e2", design="a39", system="base")[:36]]


def test_the_build_is_seeded_and_writes_numbers_only(tmp_path):
    a = build(tmp_path / "a", "mmlupro_30", flaky=0.05)
    b = build(tmp_path / "b", "mmlupro_30", flaky=0.05)
    assert [(p.name, r) for p, r in a.items()] == [(p.name, r) for p, r in b.items()]
    rows = [r for rs in a.values() for r in rs]
    assert not any(k in r for r in rows for k in ev.TEXT_KEYS)
    assert {r["status"] for r in rows} == {"ok", "not_run"}
    capped = [r for r in rows if r["status"] == "ok" and r["parsed_letter"] is None]
    assert capped and all(r["finish_reason"] == "length" and r["no_answer_reason"] == CAP for r in capped)
