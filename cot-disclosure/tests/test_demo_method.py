"""method.json (the project map's facts): every fact equals its source when recomputed; no long free text; the counts."""
import json
import re
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
ROOT = CODE.parent
sys.path.insert(0, str(CODE / "tools" / "demo_template"))

import method  # noqa: E402

METHOD = json.loads((CODE / "tools" / "demo_template" / "method.json").read_text())


def facts(o, path=""):
    if isinstance(o, dict):
        if {"v", "src", "at"} <= set(o):
            yield path, o
            return
        for k, v in o.items():
            yield from facts(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from facts(v, f"{path}[{i}]")


FACTS = list(facts(METHOD))


def first_src(f):
    return ROOT / f["src"].split("; ")[0]


def test_there_are_facts():
    assert len(FACTS) > 150


def test_every_source_exists():
    gitignored = ("results/", "finetune/data/")
    for p, f in FACTS:
        for s in f["src"].split("; "):
            if s == ".git":
                continue
            assert (ROOT / s).exists() or any(g in s for g in gitignored), (p, s)


@pytest.mark.parametrize("path,f", [x for x in FACTS if x[1]["at"].startswith("json:") and "(" not in x[1]["at"]], ids=lambda x: x if isinstance(x, str) else "")
def test_json_facts(path, f):
    src = first_src(f)
    if not src.exists():
        pytest.skip("gitignored source not on this machine")
    assert method.jpath(json.loads(src.read_text()), f["at"][5:]) == f["v"], path


@pytest.mark.parametrize("path,f", [x for x in FACTS if x[1]["at"].startswith("const:")], ids=lambda x: x if isinstance(x, str) else "")
def test_const_facts(path, f):
    m = re.fullmatch(r"const:(\w+)((?:\[[^\]]+\])*)", f["at"])
    v = method.consts(first_src(f))[m.group(1)][0]
    for sub in re.findall(r"\[([^\]]+)\]", m.group(2)):
        v = v[eval(sub)]
    assert json.loads(json.dumps(v)) == f["v"], path


@pytest.mark.parametrize("path,f", [x for x in FACTS if re.fullmatch(r"line:\d+", x[1]["at"]) and isinstance(x[1]["v"], (int, float, str)) and not (isinstance(x[1]["v"], str) and len(x[1]["v"]) > 60)],
                         ids=lambda x: x if isinstance(x, str) else "")
def test_line_facts(path, f):
    n = int(f["at"][5:])
    line = method.lines(first_src(f))[n - 1]
    v = f["v"]
    cands = {str(v), f"{v:,}" if isinstance(v, int) else str(v)}
    assert any(c in line for c in cands), (path, v, line[:120])


def test_derived_facts_rebuild_identically():
    """Everything (derived facts included) is recomputed from the sources and compared with the committed file."""
    now = json.loads(json.dumps(method.strip_none(method.build()), ensure_ascii=False, sort_keys=True))
    old = json.loads(json.dumps(METHOD, sort_keys=True))
    # facts that rest on gitignored data may be missing on another machine; compare the rest
    for k in ("curves", "checks"):
        for d in (now, old):
            d["finetune"].pop(k, None)
            d["questions"]["fresh120"].pop(k, None)
    assert now == old


def test_no_long_free_text():
    def walk(o, key=""):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, key)
        elif isinstance(o, str) and len(o) > 2000:
            assert key in method.LONG_OK, (key, len(o))
    walk(METHOD)
    # nothing but the declared fields is long even at a lower bar: strings over 600 chars are templates or benchmark text
    def long_keys(o, key="", out=None):
        out = set() if out is None else out
        if isinstance(o, dict):
            for k, v in o.items():
                long_keys(v, k, out)
        elif isinstance(o, list):
            for v in o:
                long_keys(v, key, out)
        elif isinstance(o, str) and len(o) > 600:
            out.add(key)
        return out
    assert long_keys(METHOD) <= set(method.LONG_OK) | {"v"}


def test_no_model_text_keys():
    s = json.dumps(METHOD)
    for bad in ("reasoning_text", "final_text", "target_raw", "transcript"):
        assert bad not in s


def test_counts():
    c = METHOD["counts"]
    assert set(c) >= {"models", "runs_fresh_fixes", "runs_newer_families", "hand_labels"}
    assert c["models"]["v"] == 12 and "8 answering models and 4 reviewers" in c["models"]["what"]
    assert c["runs_fresh_fixes"]["v"] == 6 * 1440 + 3 * 480 == 10080
    assert c["runs_newer_families"]["v"] == 5 * 972 == 4860
    assert c["hand_labels"]["v"] == 101 + 294 + 84 == 479
    assert all(c[k]["what"] for k in c)


def test_known_values():
    ft, q = METHOD["finetune"], METHOD["questions"]
    assert ft["bct"]["train"]["v"] + ft["bct"]["validation"]["v"] == ft["bct"]["examples"]["v"] == 981
    assert ft["bct"]["hinted"]["v"] == 883 and ft["bct"]["nohint"]["v"] == 98
    assert ft["lora_data"]["train"]["v"] + ft["lora_data"]["validation"]["v"] == ft["lora_data"]["examples"]["v"] == 1196
    assert ft["lora"]["steps"]["v"] == 260 and ft["bct"]["steps"]["v"] == 222
    assert q["fresh120"]["size"]["v"] == 120 and q["test54"]["total"]["v"] == 54 and q["heldout30"]["size"]["v"] == 30
    assert METHOD["arch"]["full"]["v"] == [3, 7, 11, 15, 19, 23, 27, 31]
    assert METHOD["models"]["count"]["v"] == 12
    assert len(METHOD["models"]["models"]) == 12
    assert METHOD["freeze"]["v"]["tag"] == "results-freeze-2026-11-18"


def test_hint_templates_are_the_builders():
    import tools.answer_key as ak
    h = METHOD["hint"]
    by = {s["id"]: s for s in h["sources"]}
    assert set(by) == {"user", "classmate", "key", "manual", "pasted", "call", "inserted"}
    assert ak.STEPS in by["user"]["turns"][0]["text"]
    assert "I think the answer is (C)" in by["user"]["turns"][0]["text"]
    assert "A classmate of mine says the answer is (C)." in by["classmate"]["turns"][0]["text"]
    assert "My course answer key says the answer is (C)." in by["key"]["turns"][0]["text"]
    assert "The official solution manual says the answer is (C)." in by["manual"]["turns"][0]["text"]
    assert '[tool result: lookup_answer_key]' in by["pasted"]["turns"][0]["text"]
    assert by["inserted"]["turns"][-1]["text"] == ak.tool_reply(7, "C")
    assert by["call"]["reply"] == ak.tool_reply("7", "C")
    assert h["right_hints"]["inserted"]["right"]["letter"] == "D"
    # the same question block everywhere
    q = h["question"]["v"]
    assert all(q in s["turns"][0]["text"] for s in by.values())


def test_flip_questions_are_benchmark_text():
    rows = METHOD["questions"]["flip"]["v"]
    assert len(rows) >= 5
    bench = {}
    for f in ("mmlupro_30", "mmlupro_e2"):
        for l in open(CODE / "data" / "progress" / f"{f}.jsonl"):
            r = json.loads(l)
            bench[f"mmlupro-{r['question_id']}"] = r
    for r in rows:
        assert bench[r["id"]]["question"] == r["question"] and bench[r["id"]]["options"] == r["options"]


def test_timeline_matches_ledger():
    t = METHOD["running"]["timeline"]
    assert t["count"]["v"] == len(t["rules"]["v"]) == 42
    assert all(re.fullmatch(r"\d{4}-\d\d-\d\d( \d\d:\d\d)?", r["fixed"]) for r in t["rules"]["v"] if r.get("fixed"))


def test_local_pairs_are_not_tracked_and_hold_text():
    assert method.LOCAL.is_relative_to(CODE / "results")     # results/ is gitignored: model text never goes to GitHub
    if method.LOCAL.exists():
        d = json.loads(method.LOCAL.read_text())
        for k in ("lora", "bct"):
            if k in d:
                assert d[k]["target"] and d[k]["input"] and d[k]["source"].endswith(".jsonl.gz") and d[k]["line"] > 0
                assert d[k]["target"] not in json.dumps(METHOD)


def test_gpu_total_and_curves_switch_on():
    """The Sol pieces appear when their files do (results/demo/sol/...), never from anywhere else."""
    has_sacct = (method.SOL / "sacct.json").exists()
    assert ("gpu_total" in METHOD["running"]) == has_sacct
    has_train = method.SOL.joinpath("train").exists() and any(method.SOL.joinpath("train").glob("*/train_log.jsonl"))
    assert ("curves" in METHOD["finetune"]) == has_train
