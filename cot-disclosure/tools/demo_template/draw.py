"""The bench's questions, drawn at random with a fixed, stored seed (Nov 22), never by outcome.

  python tools/demo_template/draw.py          # -> tools/demo_template/draw.json (tracked: ids, set sizes, the seed)

Each test draws from its own frozen question set, sorted by id before the draw, so the same files give the same draw.
Tests 1-3 share one draw from the 54 test questions (the tool-vs-person, authority and thinking runs are all on them).
Test 4 draws from the 120 fresh questions and from the 30 held-out. Test 5 from the review teams' tool cases whose
lookup was wrong and whose solver answered wrong (the cases the reviewers graded, agents/c15.py corrects()) and from the checker's 100 fresh items. Test 6 from the 16 new
questions of the patching set. Read-only on every source.
"""
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE = HERE.parents[1]
OUT = HERE / "draw.json"
SEED = "cse598-demo-bench-2026-11-22"
K = {"test54": 3, "fresh120": 3, "held30": 2, "c4_bad": 3, "c15": 2, "patch16": 3}


def _jsonl(p):
    with open(p) as f:
        return [json.loads(line) for line in f if line.strip()]


def sets(code=CODE):
    r = code / "results"
    return {
        "test54": ("the 54 test questions", "results/trackB/steered_cases.jsonl",
                   sorted({x["item_id"] for x in _jsonl(r / "trackB/steered_cases.jsonl")})),
        "fresh120": ("the 120 fresh questions", "data/progress/mmlupro_e2.jsonl",
                     sorted(f"mmlupro-{x['question_id']}" for x in _jsonl(code / "data/progress/mmlupro_e2.jsonl"))),
        "held30": ("the 30 held-out questions", "data/progress/mmlupro_30.jsonl",
                   sorted(f"mmlupro-{x['question_id']}" for x in _jsonl(code / "data/progress/mmlupro_30.jsonl"))),
        "c4_bad": ("review teams: the wrong tool answers the reviewers graded", "results/trackC/team_c4.jsonl",
                   sorted({x["case_id"] for x in _jsonl(r / "trackC/team_c4.jsonl")
                           if x.get("agent") == "solver" and x.get("team") == "tool" and x.get("bad_lookup")
                           and x.get("letter") != x.get("correct")})),
        "c15": ("the checker's 100 fresh items", "results/trackC/c15_items.jsonl",
                sorted({x["item_id"] for x in _jsonl(r / "trackC/c15_items.jsonl")})),
        "patch16": ("the 16 new questions (patching)", "results/trackA/setA/step10_patching.json",
                    sorted({x["item_id"] for x in json.loads((r / "trackA/setA/step10_patching.json").read_text())["cuts"]})),
    }


def draw(code=CODE, seed=SEED):
    out = {"seed": seed, "how": "random.Random(seed + ':' + set).sample(sorted ids, k); never by outcome", "sets": {}}
    for name, (what, src, ids) in sets(code).items():
        rnd = random.Random(f"{seed}:{name}")
        out["sets"][name] = {"what": what, "source": "cot-disclosure/" + src, "size": len(ids), "k": K[name],
                             "drawn": sorted(rnd.sample(ids, K[name]))}
    out["tests"] = {"1": ["test54"], "2": ["test54"], "3": ["test54"], "4": ["fresh120", "held30"],
                    "5": ["c4_bad", "c15"], "6": ["patch16"]}
    return out


if __name__ == "__main__":
    d = draw()
    OUT.write_text(json.dumps(d, indent=1) + "\n")
    for k, v in d["sets"].items():
        print(k, v["size"], v["drawn"])
