"""The demo's method facts (Nov 22): every fact the project map shows, read from its source at build time.

  python tools/demo_template/method.py            # -> tools/demo_template/method.json (tracked) and
                                                  #    results/demo/method_local.json (gitignored: two real training pairs)

Each fact is {"v": value, "src": "<repo-relative path>", "at": "<where>", "what": "<plain words>"} with `at` one of
  json:a.b.0.c    a key path in a JSON file          const:NAME        a module-level constant (read with ast, no import)
  line:N          a line of a text file (v is on it)  derived:...       computed from the sources named in `src`
Nothing here is typed as a value: values come from code, JSON, tables or logs. What is typed is plain wording (`what`,
labels), the illustrative question's place in marks.js, and which of our own tests a model is in.
method.json holds numbers, ids, paths, our own templates and benchmark question text, never model output. The two
training pairs (model text) go to the gitignored method_local.json.
tests/test_demo_method.py recomputes every fact from its source.
"""
import ast
import gzip
import json
import random
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE = HERE.parents[1]
ROOT = CODE.parent
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

OUT = HERE / "method.json"
LOCAL = CODE / "results" / "demo" / "method_local.json"
SOL = CODE / "results" / "demo" / "sol"
SUM = CODE / "results" / "summaries"
FREEZE_TAG = "results-freeze-2026-11-18"
LONG_OK = ("template", "turns", "text", "question", "options")     # fields that may be long (our templates, benchmark text)
CURVE_POINTS = 300


# ------------------------------------------------------------------ readers
def rel(p):
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:                       # a file outside the repo (a test's scratch folder)
        return str(p)


def F(v, src, at, what=None):
    if isinstance(src, (list, tuple)):
        src = "; ".join(x if isinstance(x, str) else rel(x) for x in src)
    d = {"v": v, "src": src if isinstance(src, str) else rel(src), "at": at}
    if what:
        d["what"] = what
    return d


_J = {}


def jload(path):
    p = str(path)
    if p not in _J:
        _J[p] = json.loads(Path(path).read_text())
    return _J[p]


def jpath(obj, dotted):
    """Follow a dotted key path; a key may itself contain dots (the longest key present wins)."""
    parts = dotted.split(".")
    while parts:
        if isinstance(obj, list):
            obj = obj[int(parts.pop(0))]
            continue
        for n in range(len(parts), 0, -1):
            k = ".".join(parts[:n])
            if k in obj:
                obj, parts = obj[k], parts[n:]
                break
        else:
            raise KeyError(dotted)
    return obj


def jf(path, dotted, what=None, scale=None):
    v = jpath(jload(path), dotted)
    return F(v, path, "json:" + dotted, what)


def lines(path):
    return Path(path).read_text().splitlines()


def lf(path, pattern, cast=str, what=None, group=1, start=0):
    """The first line (from `start`) matching `pattern`: v is the captured group, at is that line."""
    for i, line in enumerate(lines(path), 1):
        if i <= start:
            continue
        m = re.search(pattern, line)
        if m:
            return F(cast(m.group(group).replace(",", "")) if cast in (int, float) else cast(m.group(group)), path, f"line:{i}", what)
    raise ValueError(f"{pattern!r} not found in {path}")


SAFE = {"range": range, "list": list, "dict": dict, "tuple": tuple, "set": set, "len": len, "sorted": sorted, "str": str,
        "int": int, "float": float, "min": min, "max": max, "sum": sum, "True": True, "False": False, "None": None}
_C = {}


def consts(path):
    """{NAME: (value, line)} of a module's top-level assignments that evaluate with no imports (read with ast)."""
    p = str(path)
    if p in _C:
        return _C[p]
    ns, out = {}, {}
    for node in ast.parse(Path(path).read_text()).body:
        if not isinstance(node, ast.Assign):
            continue
        try:
            val = eval(compile(ast.Expression(node.value), str(path), "eval"), {"__builtins__": SAFE}, dict(ns))
        except Exception:
            continue
        tgt = node.targets[0]
        if isinstance(tgt, ast.Name):
            ns[tgt.id] = val
            out[tgt.id] = (val, node.lineno)
        elif isinstance(tgt, ast.Tuple) and isinstance(node.value, ast.Tuple) and len(tgt.elts) == len(val):
            for t, x in zip(tgt.elts, val):
                if isinstance(t, ast.Name):
                    ns[t.id] = x
                    out[t.id] = (x, node.lineno)
    _C[p] = out
    return out


def cf(path, name, what=None, key=None):
    v, ln = consts(path)[name]
    at = f"const:{name}"
    if key is not None:
        v, at = v[key], f"const:{name}[{key!r}]"
    return F(v, path, at, what)


def dv(v, srcs, expr, what=None):
    srcs = [srcs] if isinstance(srcs, (str, Path)) else srcs
    return F(v, "; ".join(s if isinstance(s, str) else rel(s) for s in srcs), "derived:" + expr, what)


def nlines(path):
    return sum(1 for _ in open(path))


def jsonl(path):
    return [json.loads(x) for x in open(path)]


# ------------------------------------------------------------------ paths
P = {
    "mmlu30": CODE / "data/progress/mmlupro_30.jsonl", "e2": CODE / "data/progress/mmlupro_e2.jsonl",
    "answer_key": CODE / "tools/answer_key.py", "experiments": CODE / "experiments.py", "b24": CODE / "progress/run_b24.py",
    "eval": CODE / "finetune/eval.py", "bd": CODE / "finetune/build_dataset.py", "train": CODE / "finetune/train.py",
    "note": CODE / "finetune/prompts/guide_note.txt", "make_e2": CODE / "finetune/make_e2.py", "common": CODE / "progress/common.py",
    "kit": CODE / "finetune/gpu/kit.py", "patching": CODE / "finetune/look/patching.py", "b20": CODE / "progress/run_b20.py",
    "accounts": CODE / "finetune/gpu/sol/accounts.conf", "trackb": CODE / "configs/trackB.yaml", "sol_b17": CODE / "progress/sol_b17.py",
    "sol_tb": CODE / "progress/sol_trackB.py", "run_team": CODE / "agents/run_team.py", "c13": CODE / "agents/sol_c13.py",
    "reviewer": CODE / "agents/reviewer.py", "reviewer_demo": CODE / "progress/reviewer_demo.py", "provenance": CODE / "finetune/provenance.py",
    "make_bct": CODE / "finetune/make_bct.py", "marks": HERE / "marks.js", "draw": HERE / "draw.json", "feeder": CODE / "tools/sol_feeder.py",
    "report": ROOT / "docs/paper/REPORT.md", "prereg": ROOT / "docs/paper/supplement/PREREGISTRATIONS.md",
    "findings": ROOT / "docs/FINDINGS.md", "runbook": ROOT / "docs/RUNBOOK.md",
    "a40log": ROOT / "archive/sessions/2026-11-06/2026-11-06_2316_ALL_a40-check-merge-c-hook-fix.md",
    "manifest": SUM / "trackA/data/examples_manifest.json", "a40manifest": CODE / "finetune/data/a40/manifest.json",
    "check": SUM / "trackA/data/examples_check.json", "valloss": SUM / "trackA/val_loss.json",
    "handoff": SUM / "trackA/step10_handoff.json", "handoffA": SUM / "trackA/setA/step10_handoff.json",
    "bylayer": SUM / "trackA/step10_by_layer_type.json", "window": SUM / "trackA/window_reach.json",
    "heads": SUM / "trackA/setA/step9_fixed_heads.json", "q8": SUM / "trackA/qwen8b_mech/qwen8b_readout.json",
    "b1r2": SUM / "trackA/gpu/b1r2/provenance_gen_report.json", "l6": SUM / "trackA/labels/l6_report.json",
    "a39": SUM / "trackA/gpu/a39/a39_e2.json", "a40": SUM / "trackA/gpu/a39/a40_e2.json", "a42": SUM / "trackA/gpu/a39/a42_e2.json",
    "b20r": SUM / "trackB/b20_report.json", "smoke": CODE / "results/trackA/gpu/smoke.json",
    "a18": SUM / "trackA/gpu/a18/a18_readout.json", "a41": SUM / "trackA/gpu/a18/a41_readout.json",
    "olmo_pin": CODE / "finetune/gpu/olmo3_7b_think_d97e442.json", "a40in": CODE / "finetune/gpu/a40_inputs.json",
    "trainx": CODE / "finetune/data/train_examples.jsonl.gz", "a40x": CODE / "finetune/data/a40/train_examples.jsonl.gz",
}


# ------------------------------------------------------------------ the illustrative question (marks.js ITEM)
def item():
    src = P["marks"].read_text()
    block = re.search(r"const ITEM = \{(.*?)\n\};", src, re.S).group(1)
    q = re.search(r'q: "(.*?)",\n', block).group(1)
    opts = re.findall(r'\["([A-J])", "([^"]*)"\]', block)
    right, hint = re.search(r'right: "([A-J])"', block).group(1), re.search(r'hint: "([A-J])"', block).group(1)
    return q, opts, right, hint


# ------------------------------------------------------------------ step 1: the questions
def questions():
    import experiments
    import finetune.build_dataset as bd
    from finetune import make_e2
    import finetune.eval as ev
    A = P["answer_key"]
    out = {}
    out["test54"] = {
        "mmlupro": dv(nlines(P["mmlu30"]), P["mmlu30"], "lines(mmlupro_30.jsonl)", "MMLU-Pro questions in the 54 test questions (the same 30 as the held-out set)"),
        "puzzles": dv(len(experiments.ITEMS), P["experiments"], "len(experiments.ITEMS)", "generated puzzles (rng seeded per kind, level and seed 0)"),
        "runs_each": lf(P["trackb"], r"^runs_per_question:\s*(\d+)", int, "runs per question and condition"),
    }
    out["test54"]["total"] = dv(out["test54"]["mmlupro"]["v"] + out["test54"]["puzzles"]["v"], [P["mmlu30"], P["experiments"]], "mmlupro + puzzles", "test questions")
    out["test54"]["runs"] = dv(out["test54"]["total"]["v"] * out["test54"]["runs_each"]["v"], [P["mmlu30"], P["experiments"], P["trackb"]], "total * runs_each", "runs a model and condition")
    out["heldout30"] = {
        "size": dv(nlines(P["mmlu30"]), P["mmlu30"], "lines(mmlupro_30.jsonl)", "held-out questions"),
        "wordings": dv(len(bd.WORDINGS["heldout"]), P["bd"], "len(WORDINGS['heldout'])", "hint wordings the held-out set uses (the training paraphrases are different ones)"),
        "jobs_each": lf(P["eval"], r'"""(\d+) jobs \(\d+ per question\)', int, "runs a system on the 30"),
        "per_question": lf(P["eval"], r'"""\d+ jobs \((\d+) per question\)', int, "runs a question and system"),
    }
    out["fresh120"] = {
        "size": dv(nlines(P["e2"]), P["e2"], "lines(mmlupro_e2.jsonl)", "fresh questions"),
        "per_category": cf(P["make_e2"], "N_PER_CATEGORY", "questions in each of four categories"),
        "categories": dv(sorted(make_e2.EVAL_CATEGORIES), P["make_e2"], "sorted(EVAL_CATEGORIES)", "categories"),
        "seed": cf(P["make_e2"], "SEED", "the draw's seed, per category"),
        "dataset": cf(P["make_e2"], "DATASET", "source benchmark"),
        "revision": cf(P["make_e2"], "REVISION", "benchmark revision"),
        "per_question": dv(len(ev.A39_WRONG) + len(ev.A39_CORRECT) + len(ev.A39_NOHINT), P["eval"], "len(A39_WRONG)+len(A39_CORRECT)+len(A39_NOHINT)", "runs a question and system: 6 with a wrong hint, 4 with a right hint, 2 with none"),
        "wrong": dv(len(ev.A39_WRONG), P["eval"], "len(A39_WRONG)", "runs a question with a wrong hint"),
        "right": dv(len(ev.A39_CORRECT), P["eval"], "len(A39_CORRECT)", "runs a question with a right hint"),
        "none": dv(len(ev.A39_NOHINT), P["eval"], "len(A39_NOHINT)", "runs a question with no hint"),
        "runs_each": jf(P["a39"], "completeness.base.expected", "runs a system on the 120"),
        "checks": dv(make_e2_checks(make_e2), [P["make_e2"], P["e2"], P["mmlu30"], CODE / "finetune/data/pool.jsonl", CODE / "results/trackC/c15_items.jsonl"], "make_e2.checks(rows, held, pool, c15)", "the exclusion checks the draw passes (the 120 against the 30, the training pool and the review teams' 100)") if make_e2_inputs() else None,
    }
    if out["fresh120"]["checks"] is None:
        del out["fresh120"]["checks"]
    out["new16"] = {
        "questions": jf(P["handoffA"], "handoff.by_cut_type.ii.all.questions", "new questions the readout was re-tested on"),
        "cuts": jf(P["handoffA"], "handoff.by_cut_type.ii.all.cuts", "usable cut points on them"),
    }
    out["patching_sets"] = {
        "olmo_questions": jf(P["handoff"], "handoff.by_cut_type.ii.all.questions", "questions in the first patching set"),
        "olmo_cuts": jf(P["handoff"], "handoff.by_cut_type.ii.all.cuts", "cut points in it"),
        "qwen_questions": jf(P["q8"], "replication.questions", "Qwen3 8B: MMLU-Pro questions in its replication") if "questions" in jload(P["q8"])["replication"] else None,
    }
    if out["patching_sets"]["qwen_questions"] is None:
        del out["patching_sets"]["qwen_questions"]
    out["flip"] = flip()
    return out


def make_e2_inputs():
    return all(p.exists() for p in (CODE / "finetune/data/pool.jsonl", CODE / "results/trackC/c15_items.jsonl"))


def make_e2_checks(make_e2):
    if not make_e2_inputs():
        return None
    rows, held = jsonl(P["e2"]), jsonl(P["mmlu30"])
    pool, c15 = jsonl(CODE / "finetune/data/pool.jsonl"), jsonl(CODE / "results/trackC/c15_items.jsonl")
    return make_e2.checks(rows, held, pool, c15)


def flip():
    """A few real questions, by the draw's seed (draw.json), from the tracked benchmark files."""
    draw = jload(P["draw"])
    by = {}
    for tag, path in (("held30", P["mmlu30"]), ("fresh120", P["e2"])):
        for r in jsonl(path):
            by[f"mmlupro-{r['question_id']}"] = (tag, r)
    rows = []
    for key in ("test54", "fresh120", "held30"):
        for i in draw["sets"][key]["drawn"]:
            if i in by:
                tag, r = by[i]
                rows.append({"id": i, "set": {"held30": "the 30 held-out questions", "fresh120": "the 120 fresh questions"}[tag],
                             "drew_from": draw["sets"][key]["what"], "category": r["category"], "question": r["question"],
                             "options": r["options"], "answer": r["answer"], "hint_letter": r["cue_letter"]})
    return F(rows, P["draw"], "derived:draw.json sets test54/fresh120/held30 -> mmlupro_30.jsonl, mmlupro_e2.jsonl",
             f"{len(rows)} real questions drawn by seed {draw['seed']} ({draw['how']}); text from the tracked benchmark files")


# ------------------------------------------------------------------ step 2: the hint
def turns(msgs):
    out = []
    for m in msgs:
        if m.get("tool_calls"):
            for c in m["tool_calls"]:
                a = c["function"]["arguments"]
                a = a if isinstance(a, str) else json.dumps(a)
                out.append({"role": "assistant call", "text": f"{c['function']['name']}({a})"})
        elif m["role"] == "tool":
            out.append({"role": "tool reply", "text": m["content"]})
        else:
            out.append({"role": m["role"], "text": m["content"]})
    return out


def hint():
    import finetune.build_dataset as bd
    import finetune.eval as ev
    import run_b24
    import tools.answer_key as ak
    q, opts, right, wrong = item()
    qid = 7
    block = bd.block(q, [v for _, v in opts])
    srcs = []

    def add(sid, label, kind, builder, cond, letter, src, at, what, extra=None):
        msgs, tools = builder(block, qid, cond, letter)
        d = {"id": sid, "label": label, "kind": kind, "turns": turns(msgs), "tools": [t["function"]["name"] for t in tools or []],
             "letter": letter, "src": src, "at": at, "what": what}
        d.update(extra or {})
        srcs.append(d)

    A = rel(P["answer_key"])
    add("user", "The user's guess", "sticky", ak.build, "user", wrong, A + ", " + rel(P["experiments"]), "const:CUE (experiments.py)", "the experiments' own template, built by tools/answer_key.build")
    add("classmate", "A classmate", "sticky", run_b24.build, "user_classmate", wrong, rel(P["b24"]), "const:CUES['user_classmate']", "built by progress/run_b24.build")
    add("key", "My answer key", "sticky", ak.build, "user_authority", wrong, A, "const:AUTHORITY_CUE", "built by tools/answer_key.build")
    add("manual", "The official manual", "sticky", run_b24.build, "user_manual", wrong, rel(P["b24"]), "const:CUES['user_manual']", "built by progress/run_b24.build")
    add("pasted", "Pasted tool output", "slip", ak.build, "tool_pasted", wrong, A, "const:PASTED", "built by tools/answer_key.build; no tool is called")
    own = {"reply": ak.tool_reply(f"{qid}", wrong), "call": f"{ak.TOOL_NAME}(question_id={qid})",
           "spec": F(ak.TOOL_SPEC["function"]["description"], P["answer_key"], "const:TOOL_SPEC['function']['description']", "the tool's declared description")}
    add("call", "The model's own tool call", "slip", ak.build, "tool_real", wrong, A, "const:TOOL_INVITE", "built by tools/answer_key.build; the reply is tool_reply()", own)
    add("inserted", "An inserted tool turn", "slip", ak.build, "tool_injected", wrong, A, "const:INJECTED / tool_reply", "we write the call and the reply into the chat; built by tools/answer_key.build")
    # right hints for the fixes: eval.py's right-hint jobs (A39_CORRECT), the wordings the experiments used
    wd = {w[0]: w for w in bd.WORDINGS["heldout"]}
    right_hints = {}
    for sid, wid in (("pasted", "tool_progress"), ("inserted", "inserted_study_guide")):
        for letter, tag in ((wrong, "wrong"), (right, "right")):
            rec = bd.record("heldout", {"question_set": "illustrative", "item_id": "illustrative", "qid": qid, "question": block,
                                        "n_options": len(opts), "correct": right}, wd[wid], letter, None, "demo", {})
            right_hints.setdefault(sid, {})[tag] = {"turns": turns(rec["messages"]), "tools": [t["function"]["name"] for t in rec["tools_declared"] or []],
                                                    "letter": letter, "wording": wid}
    right_src = dv(sorted({w for w, _ in ev.A39_CORRECT}), [P["eval"], P["bd"]], "set(w for w, r in A39_CORRECT)", "wordings eval.py uses for right hints: tool outputs only, no user guess")
    return {
        "question": F(q, P["marks"], "derived:marks.js ITEM.q", "the illustrative question, written by us"),
        "options": F([[l, v] for l, v in opts], P["marks"], "derived:marks.js ITEM.opts"),
        "wrong_letter": F(wrong, P["marks"], "derived:marks.js ITEM.hint", "the wrong letter every source carries"),
        "right_letter": F(right, P["marks"], "derived:marks.js ITEM.right"),
        "instruction": F(ak.STEPS, P["experiments"], "const:STEPS", "closing instruction of every prompt"),
        "sources": srcs,
        "right_hints": right_hints, "right_hint_wordings": right_src,
        "wordings": dv([w[0] for w in bd.WORDINGS["heldout"]], P["bd"], "[w[0] for w in WORDINGS['heldout']]", "the held-out wordings (names are code names; shown as a count)"),
    }


# ------------------------------------------------------------------ step 3: the models
def report_table():
    ls = lines(P["report"])
    i0 = next(i for i, l in enumerate(ls) if l.startswith("| model | where, how | thinking"))
    rows = []
    for j in range(i0 + 2, len(ls)):
        if not ls[j].startswith("|"):
            break
        rows.append((j + 1, [c.strip() for c in ls[j].strip().strip("|").split("|")]))
    return rows


def models():
    t = report_table()
    rows = {}
    for ln, c in t:
        rows[c[0].split(" (")[0].split(",")[0]] = (ln, c)
    b20 = consts(P["b20"])["MODELS"][0]
    pilot_t = consts(P["common"])["PILOT_TEMPERATURE"][0]

    def row(prefix):
        ln, c = next((l, c) for l, c in t if c[0].startswith(prefix))
        return ln, c

    spec = [
        # id, plain name, report-table prefix, temperature fact, revision fact, tests (our plain names)
        ("olmo7", "Olmo 3 7B Think", "Olmo 3 7B Think", "answers", ["Tool vs person", "Authority", "The fixes", "Inside the model"]),
        ("qwen30t", "Qwen3 30B Thinking", "Qwen3 30B-A3B Thinking", "answers", ["Tool vs person", "Authority", "Review teams (the solver)"]),
        ("qwen30i", "Qwen3 30B Instruct", "Qwen3 30B-A3B Instruct", "answers", ["Tool vs person", "Authority", "Review teams (a reviewer)"]),
        ("qwen8", "Qwen3 8B", "Qwen3-8B", "answers", ["Tool vs person", "Thinking on and off", "Inside the model"]),
        ("gptoss", "gpt-oss 20B", "gpt-oss-20b", "answers", ["Tool vs person", "Thinking on and off (low, medium, high effort)"]),
        ("gemma", "Gemma 4 26B-A4B", "B20's three", "answers", ["Tool vs person", "Thinking on and off"]),
        ("nemotron", "Nemotron 3 Nano 30B-A3B", "B20's three", "answers", ["Tool vs person", "Thinking on and off"]),
        ("granite42", "Granite 4.2 8B", "B20's three", "answers", ["Tool vs person", "Thinking on (only)"]),
        ("olmo32", "Olmo 3.1 32B Instruct", "Olmo 3.1 32B Instruct", "reviewer", ["Review teams (a reviewer)"]),
        ("olmo7i", "Olmo 3 7B Instruct", "Olmo 3.1 32B Instruct", "reviewer", ["Review teams (a reviewer)"]),
        ("granite41", "Granite 4.1 30B", "Olmo 3.1 32B Instruct", "reviewer", ["Review teams (a reviewer)"]),
        ("mistral", "Mistral Small 3.2 24B", "Olmo 3.1 32B Instruct", "reviewer", ["Review teams (a reviewer)"]),
    ]
    c13 = consts(P["c13"])["MODELS"][0]
    team = consts(P["run_team"])
    out = []
    for mid, name, prefix, role, tests in spec:
        ln, c = row(prefix)
        d = {"id": mid, "name": name, "role": role, "tests": F(tests, P["report"], f"line:{ln}", "plain-name rewrite of the report's 'used in' column"),
             "table": F({"where": c[1], "thinking": c[2]}, P["report"], f"line:{ln}", "the report's setup table: where it ran and its thinking setting")}
        # where it ran: the setup table's words for the answering models; the code's own provider for the reviewers
        if role == "answers":
            w = c[1]
            ran = [n for n, ok in (("Voyager", "Voyager" in w), ("Sol (vLLM)", "vLLM" in w or w.startswith("Sol, our vLLM") or "Sol (C13)" in w),
                                   ("Sol (Hugging Face)", "Hugging Face" in w)) if ok]
            d["ran"] = F(ran, P["report"], f"derived:the setup table's 'where' column (line {ln}), by place named", "places it ran")
        elif mid in ("olmo32", "olmo7i"):
            prov = {m[1]: m[0] for m in team["REVIEWER_MODELS"][0]}
            key = "olmo3-32b-instruct" if mid == "olmo32" else "olmo3-7b-instruct"
            assert prov.get(key) == "voyager" if mid == "olmo32" else f"  {key}: [" in (CODE / "configs/models.yaml").read_text()
            d["ran"] = F(["Voyager"], [P["run_team"], CODE / "configs/models.yaml"], f"derived:REVIEWER_MODELS provider for {key} is voyager" if mid == "olmo32" else "derived:models.yaml voyager_ids lists olmo3-7b-instruct", "places it ran")
        else:
            d["ran"] = F(["Sol (vLLM)"], P["c13"], "derived:agents/sol_c13.py serves it through sol_chat (our vLLM server on Sol)", "places it ran")
        if mid in ("gemma", "nemotron", "granite42"):
            k = {"gemma": "gemma-4-26b-a4b-it", "nemotron": "nemotron-3-nano-30b-a3b", "granite42": "granite-4.2-8b"}[mid]
            m = b20[k]
            d["revision"] = F(m["revision"], P["b20"], f"const:MODELS['{k}']['revision']", "pinned revision")
            d["temperature"] = F(m["temperature"], P["b20"], f"const:MODELS['{k}']['temperature']")
            d["size"] = F(m["size"], P["b20"], f"const:MODELS['{k}']['size']")
            d["settings"] = F(["on" if x else "off" for x in m.get("settings", consts(P["b20"])["SETTINGS"][0])], P["b20"], f"derived:MODELS['{k}'] settings (default on and off; Granite 4.2: on only)",
                              "thinking on and off in the same weights (Granite 4.2 on only)")
            d["tool"] = F(m["tool"], P["b20"], f"const:MODELS['{k}']['tool']", "how the tool's hint reaches it")
        elif mid in ("granite41", "mistral"):
            k = {"granite41": "granite-4.1-30b", "mistral": "mistral-small-3.2-24b"}[mid]
            d["revision"] = F(c13[k]["revision"], P["c13"], f"const:MODELS['{k}']['revision']", "pinned revision")
            d["size"] = F(c13[k]["size"], P["c13"], f"const:MODELS['{k}']['size']")
        elif mid == "qwen8":
            d["revision"] = cf(P["sol_tb"], "REVISION", "pinned revision")
            d["temperature"] = F(pilot_t, P["common"], "const:PILOT_TEMPERATURE")
        elif mid == "gptoss":
            d["revision"] = cf(P["sol_b17"], "REVISION", "pinned revision")
            d["temperature"] = lf(P["report"], r"gpt-oss-20b (1\.0) \(its", float, "its recommended temperature")
        elif mid in ("olmo7", "qwen30t", "qwen30i"):
            d["temperature"] = F(pilot_t, P["common"], "const:PILOT_TEMPERATURE")
            if mid == "olmo7":
                d["revision"] = jf(P["valloss"], "snapshot_commit", "pinned revision")
        out.append(d)
    return {
        "models": out,
        "count": dv(len(out), P["report"], "len(models)", "8 answering models and 4 reviewers"),
        "answering": dv(sum(1 for m in out if m["role"] == "answers"), P["report"], "count role=answers"),
        "reviewers": dv(sum(1 for m in out if m["role"] == "reviewer"), P["report"], "count role=reviewer"),
        "budget": lf(P["report"], r"one (32,768)-token budget", int, "tokens a run may use, prompt and every reply"),
        "temperatures": F({"olmo_qwen": pilot_t, "gpt_oss_b20": 1.0}, [P["common"], P["report"]], "derived:PILOT_TEMPERATURE and the report's gpt-oss line", "0.6 for Olmo and Qwen3; 1.0 for gpt-oss and B20's three"),
        "where": [
            F("Voyager", P["report"], "derived:the setup table's 'where' column (line " + str(row("Olmo 3 7B Think")[0]) + ")", "ASU's model server: Qwen3 30B (both), Olmo 3 7B Think, the Olmo reviewers"),
            F("Sol (vLLM)", P["report"], "derived:the setup table's 'where' column (line " + str(row("Qwen3-8B")[0]) + ")", "ASU's supercomputer, our own vLLM server: Qwen3 8B, gpt-oss, Gemma, Nemotron, Granite, two reviewers"),
            F("Sol (Hugging Face)", P["report"], "derived:the setup table's 'where' column (line " + str(row("Olmo 3 7B Think")[0]) + ")", "training, evaluations and the layer experiments"),
        ],
    }


# ------------------------------------------------------------------ step 4: running it
def running():
    import tools.answer_key  # noqa: F401
    acc = lines(P["accounts"])
    ai = next(i for i, l in enumerate(acc, 1) if l.startswith("class_cse"))
    cols = acc[ai - 1].split()
    out = {
        "limits": {
            "gpu_minutes": F(int(cols[3]), P["accounts"], f"line:{ai}", "running GPU-minutes allowed at once (each running job's time left x its GPUs)"),
            "jobs": F(int(cols[4]), P["accounts"], f"line:{ai}", "jobs queued at once"),
            "wall_hours": F(int(cols[6]), P["accounts"], f"line:{ai}", "longest one job may run"),
            "gpus": F(int(cols[7]), P["accounts"], f"line:{ai}", "GPUs in one job"),
            "gpu": jf(P["smoke"], "gpu.name", "the GPU") if P["smoke"].exists() else jf(P["valloss"], "gpu.name", "the GPU"),
            "gpu_memory_gib": jf(P["valloss"], "gpu.memory_gib", "GPU memory"),
        },
        "feeder": {
            "tick_seconds": lf(P["feeder"], r"(\d+) by default\)", int, "seconds between the feeder's ticks"),
            "digest": lf(P["feeder"], r"first tick after (\d\d:\d\d)", str, "the daily digest's hour (local time)"),
            "steps": F(["its stop file is checked first", "every job's state is read from the scheduler", "each queue line is submitted once, in order",
                        "a line goes in only if it fits the 10 places and the GPU-minutes left"],
                       P["feeder"], "derived:docstring lines 3-30, in plain words", "one tick, in plain words (rewritten from the docstring)"),
        },
        "runs": {
            "fresh_per_system": jf(P["a39"], "completeness.base.expected", "runs a system on the 120 fresh questions"),
            "on_the_30": lf(P["eval"], r'"""(\d+) jobs \(\d+ per question\)', int, "runs a system on the 30 held-out"),
            "dial_per_setting": jf(P["b1r2"], "systems.prov-a1-v2.runs", "runs a dial setting on the 120"),
            "b20_per_model_setting": jf(P["b20r"], "gemma-4-26b-a4b-it.runs.on", "runs a model and setting in the newer families"),
        },
        "repro": {
            "seed": cf(P["common"], "SEED", "base seed of the progress runs"),
            "train_seed": cf(P["train"], "SEED", "training seed"),
            "revision": jf(P["valloss"], "snapshot_commit", "the pinned Olmo 3 7B Think revision"),
            "weights_same": jf(P["valloss"], "files_vs_d97e442.weights_same", "weights checked against the pinned revision, file by file (sha256)"),
            "checked_files": jf(P["valloss"], "files_vs_d97e442.checked", "files checked"),
            "template_sha": cf(CODE / "finetune/olmo_format.py", "PINNED_SHA256", "the chat template's pinned sha256") if "PINNED_SHA256" in consts(CODE / "finetune/olmo_format.py") else None,
            "a40_plan_sha": jf(P["a40in"], "plan_sha256", "sha256 of the consistency-training plan, fixed before any call"),
        },
        "gpu_pieces": [
            lf(P["findings"], r"(34\.3) GPU-hours", float, "the attention dial's first test: its own runs, Slurm elapsed time with model loading"),
            lf(P["runbook"], r"E2 is (53\.2) GPU-hours", float, "the plan for the 120 fresh questions' generation (at about 400 tokens a second on one A100)"),
            lf(P["a40log"], r"About (2:44) of wall time", str, "consistency training: three jobs, hours:minutes of wall time"),
        ],
        "timeline": timeline(),
    }
    if out["repro"]["template_sha"] is None:
        del out["repro"]["template_sha"]
    sa = SOL / "sacct.json"
    if sa.exists():
        d = json.loads(sa.read_text())
        out["gpu_total"] = F({"since": d["since"], "jobs": d["jobs"], "gpu_hours": d["gpu_hours"], "by_name": d.get("by_name", {})},
                             sa, "json:(whole file)", "on Ritik's account only (Slurm sacct, read-only)")
    return out


def ledger():
    ls = lines(P["prereg"])
    i0 = next(i for i, l in enumerate(ls) if l.startswith("| # | track"))
    rows = []
    for j in range(i0 + 2, len(ls)):
        if not ls[j].startswith("| "):
            break
        c = [x.strip() for x in ls[j].strip().strip("|").split(" | ")]
        d = re.findall(r"\d{4}-\d\d-\d\d(?: \d\d:\d\d)?", c[5])
        r = re.findall(r"\d{4}-\d\d-\d\d(?: \d\d:\d\d)?", c[6])
        rows.append({"n": int(c[0]), "line": j + 1, "kind": c[3], "fixed": d[0] if d else None, "result": r[0] if r else None})
    return rows


PLAIN = {2: "Tool against person, on 54 questions", 4: "The first test of the fixes, on the 30 held-out", 9: "Does the readout replicate on 16 new questions?",
         15: "The review teams on 100 fresh items", 24: "Tool or authority?", 29: "Three newer model families", 32: "The fixes on the 120 fresh questions",
         34: "Consistency training", 38: "The hand-label check"}


def timeline():
    rows = ledger()
    p = str(P["prereg"].relative_to(ROOT))
    tag = tag_info()
    ev = [{"n": r["n"], "fixed": r["fixed"], "result": r["result"], "kind": r["kind"], "plain": PLAIN.get(r["n"]), "line": r["line"]} for r in rows]
    start = re.search(r"checked: \"(\d{4}-\d\d-\d\d)\"", P["trackb"].parent.joinpath("models.yaml").read_text()).group(1)
    return {
        "rules": dv(ev, p, "ledger rows: #, kind, fixed date, first-result date", "one row a pre-registered rule: when it was fixed and when its first result was committed"),
        "plain_names": F(PLAIN, p, "derived:PLAIN (our wording for these rows)", "plain names for some rows; the others show only dates"),
        "count": dv(len(rows), p, "len(ledger rows)", "rules in the ledger"),
        "pre_registered": dv(sum(1 for r in rows if r["kind"] == "pre-registered"), p, "count(kind == 'pre-registered')", "rules marked pre-registered, fixed before their runs"),
        "first_call_check": F(start, CODE / "configs/models.yaml", "derived:checked: date (line 3)", "the date the model providers' documents were read, before any run"),
        "freeze": tag,
    }


def tag_info():
    r = subprocess.run(["git", "log", "-1", "--format=%H|%ci", FREEZE_TAG], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        return F({"tag": FREEZE_TAG}, ".git", "derived:git tag", "the freeze's tag (not in this clone)")
    h, d = r.stdout.strip().split("|")
    return F({"tag": FREEZE_TAG, "commit": h[:7], "date": d[:10], "time": d[11:16]}, ".git", f"derived:git log -1 {FREEZE_TAG}", "the results freeze: no number changes after it")


# ------------------------------------------------------------------ steps 5, 6: the architecture and the patching
def arch():
    from finetune.gpu import kit
    full = kit.OLMO3_FULL_LAYERS
    return {
        "layers": F(len(jload(P["handoff"])["handoff"]["by_cut_type"]["ii"]["all"]["drop_by_layer"]), P["handoff"], "derived:len(handoff.by_cut_type.ii.all.drop_by_layer)", "decoder layers (one drop per layer)"),
        "full": cf(P["kit"], "OLMO3_FULL_LAYERS", "layers that attend to the whole prompt"),
        "full_check": jf(P["bylayer"], "full_attention_layers", "the same layers, as the analysis recorded them"),
        "window": jf(P["window"], "window", "tokens each of the other layers can look back"),
        "heads": jf(P["smoke"], "config.num_attention_heads", "attention heads a layer") if "num_attention_heads" in jload(P["smoke"]).get("config", {}) else None,
        "hidden": jf(P["smoke"], "config.hidden_size", "hidden size") if "hidden_size" in jload(P["smoke"]).get("config", {}) else None,
        "revision": F(jload(P["valloss"])["snapshot_commit"], P["valloss"], "json:snapshot_commit", "pinned Olmo 3 7B Think revision"),
        "n_full": dv(len(full), P["kit"], "len(OLMO3_FULL_LAYERS)", "layers that see the whole prompt"),
        "n_window": dv(32 - len(full), P["kit"], "32 - len(OLMO3_FULL_LAYERS)", "layers with a sliding window"),
    }


def patching():
    from finetune.look import patching as pt
    q = jload(P["q8"])["localization"]
    return {
        "unit": F("one decoder layer at a time", P["patching"], "derived:docstring lines 27-28, in plain words", "what is swapped: the clean run's residual stream at that layer's output"),
        "groups": cf(P["patching"], "GROUPS", "where it is swapped in (the hint's tokens, the reasoning, the answer position)"),
        "min_gap": cf(P["patching"], "MIN_GAP", "cuts where the two runs' logit gap is under this are left out"),
        "measure": F("logit(wrong letter) minus logit(own letter) at the answer position", P["patching"], "derived:docstring lines 20-21, in plain words", "what is measured (plain words)"),
        "readout": cf(CODE / "finetune/provenance.py", "READOUT", "the three layers that read the hint"),
        "readout_share": jf(P["handoff"], "handoff.by_cut_type.ii.all.drop_share_readout.mean", "share of the hint's effect at layers 15, 19, 23"),
        "heads": jf(P["heads"], "heads", "the three attention heads"),
        "heads_diff": jf(P["heads"], "mean over the three heads.followed - resisted (all channels).hint - control.difference", "followed minus resisted, hint minus control attention"),
        "qwen": {"layers": jf(P["q8"], "localization.layers", "Qwen3 8B's three layers (chosen on the puzzles)"), "n_layers": jf(P["q8"], "localization.n_layers", "its layers")},
    }


# ------------------------------------------------------------------ steps 7, 8: fine-tuning
def finetune():
    tr = consts(P["train"])
    man, am = jload(P["manifest"]), jload(P["a40manifest"])
    vl = jload(P["valloss"])
    steps_lora = (man["by_split"]["train"] // tr["ACCUM"][0]) * tr["EPOCHS"][0]
    a40_epoch = lf(P["a40log"], r"^\s*1 by validation loss \((0\.\d+) against (0\.\d+)\)", float, "consistency training's validation loss, epoch 1")
    a40_epoch2 = lf(P["a40log"], r"^\s*1 by validation loss \((0\.\d+) against (0\.\d+)\)", float, "and epoch 2", group=2)
    out = {
        "lora": {
            "rank": cf(P["train"], "RANK", "LoRA rank"), "alpha": cf(P["train"], "ALPHA", "LoRA alpha"), "dropout": cf(P["train"], "DROPOUT"),
            "modules": cf(P["train"], "LORA_ALL", "the projections trained, on every layer"),
            "lr": cf(P["train"], "LR_LORA", "learning rate"), "epochs": cf(P["train"], "EPOCHS"), "per_step": cf(P["train"], "ACCUM", "examples an optimizer step"),
            "max_tokens": dv(consts(CODE / "finetune/olmo_format.py")["CAP_TOTAL"][0], CODE / "finetune/olmo_format.py", "olmo_format.CAP_TOTAL", "tokens an example may have (prompt and reply)"),
            "steps": dv(steps_lora, [P["manifest"], P["train"]], "train examples // ACCUM * EPOCHS", "optimizer steps"),
            "warmup": cf(P["train"], "WARMUP", "share of steps spent warming up the learning rate"),
        },
        "lora_data": {
            "questions_run": jf(P["manifest"], "questions_run", "questions run with no hint, three times each, to find ones the model gets right"),
            "kept": jf(P["manifest"], "kept", "questions kept (all three runs answered and on the key)"),
            "examples": jf(P["manifest"], "examples", "training examples written from them (hinted prompts with several wordings, and no-hint ones)"),
            "train": jf(P["manifest"], "by_split.train", "examples the model trained on"),
            "validation": jf(P["manifest"], "by_split.validation", "examples held back to choose the epoch"),
            "neither": jf(P["manifest"], "neither", "examples dropped because the reasoning neither followed nor rejected the hint"),
            "nohint": jf(P["manifest"], "nohint_examples", "of the examples, those with no hint at all (the model's own runs)"),
            "by_channel": jf(P["manifest"], "by_channel", "examples by where the hint sat and whether it was right"),
            "tokens_median": jf(P["manifest"], "tokens_median", "median tokens an example"),
            "dropped_long": jf(P["manifest"], "dropped_over_32768", "examples dropped for length"),
            "leak_checks": F({"examples_train": jpath(jload(P["check"]), "a_heldout.train.examples"), "heldout_questions": jpath(jload(P["check"]), "a_heldout.train.heldout_questions"),
                              "question_by_id": len(jpath(jload(P["check"]), "a_heldout.train.heldout_question_by_id")), "question_by_text": len(jpath(jload(P["check"]), "a_heldout.train.heldout_question_by_text")),
                              "wording_in_training": len(jpath(jload(P["check"]), "a_heldout.train.wording_not_a_training_one")), "passes": jpath(jload(P["check"]), "a_heldout.train.pass"),
                              "validation_passes": jpath(jload(P["check"]), "a_heldout.validation.pass")}, P["check"], "derived:examples_check.json a_heldout.* (counts of each list)", "the held-out leak check: no held-out question, wording or channel among the training examples"),
        },
        "lora_loss": {
            "base": jf(P["valloss"], "systems.base.groups.overall.loss", "validation loss of the model before training") if "overall" in vl["systems"]["base"]["groups"] else None,
            "epoch1": jf(P["valloss"], "systems.lora/epoch1.state_validation_loss", "validation loss after epoch 1"),
            "epoch2": jf(P["valloss"], "systems.lora/epoch2.state_validation_loss", "validation loss after epoch 2"),
            "taught_base": F(vl["systems"]["base"]["groups"]["taught"]["loss"], P["valloss"], "json:systems.base.groups.taught.loss", "loss on the tokens training teaches (the opener, the hint check, the final answer), before training"),
            "taught_epoch2": F(vl["systems"]["lora/epoch2"]["groups"]["taught"]["loss"], P["valloss"], "json:systems.lora/epoch2.groups.taught.loss", "the same, after epoch 2"),
            "taught_tokens": F(vl["systems"]["base"]["groups"]["taught"]["tokens"], P["valloss"], "json:systems.base.groups.taught.tokens", "tokens in that group"),
            "overall_tokens": F(vl["part_tokens"]["overall"], P["valloss"], "json:part_tokens.overall", "validation tokens in all"),
        },
        "bct": {
            "examples": jf(P["a40manifest"], "examples", "examples in all (hinted prompts and no-hint ones)"),
            "train": jf(P["a40manifest"], "by_split.train", "examples trained on"),
            "validation": jf(P["a40manifest"], "by_split.validation", "examples held back to choose the epoch"),
            "nohint": jf(P["a40manifest"], "nohint_examples", "of the examples, those with no hint"),
            "hinted": dv(am["examples"] - am["nohint_examples"], P["a40manifest"], "examples - nohint_examples", "of the examples, those with a hint"),
            "records": jf(P["a40manifest"], "records", "prompts that got a target"),
            "dropped": jf(P["a40manifest"], "dropped", "prompts dropped, and why"),
            "dropped_total": dv(sum(am["dropped"].values()), P["a40manifest"], "sum(dropped)", "prompts dropped in all"),
            "questions": jf(P["a40manifest"], "questions", "questions in each split"),
            "tokens_median": jf(P["a40manifest"], "tokens_median"),
            "steps": F(a40_steps(am, tr), [rel(P["a40log"]), rel(P["a40manifest"])], "derived:ceil(train examples / ACCUM) * EPOCHS", "optimizer steps over two epochs"),
            "steps_in_log": lf(P["a40log"], r"The training log has (\d+) steps", int, "the training log's own count of steps"),
            "epoch_loss": {"epoch1": a40_epoch, "epoch2": a40_epoch2},
            "chosen": F(1, P["a40log"], "line:" + a40_epoch["at"].split(":")[1], "epoch chosen: the lower validation loss (never held-out results)"),
            "epoch_rule": F("lower loss on the validation slice; never held-out results", P["train"], "line:" + str(lineno(P["train"], "never held-out results")), "the rule that picks the epoch"),
        },
    }
    if out["lora_loss"]["base"] is None:
        out["lora_loss"]["base"] = F(vl["systems"]["base"]["groups"]["overall"]["loss"], P["valloss"], "json:systems.base.groups.overall.loss") if "overall" in vl["systems"]["base"]["groups"] else None
    out["lora_loss"] = {k: v for k, v in out["lora_loss"].items() if v}
    cur = curves()
    if cur:
        out["curves"] = cur
    return out


def lineno(path, needle):
    return next(i for i, l in enumerate(lines(path), 1) if needle in l)


def a40_steps(am, tr):
    per_epoch = -(-am["by_split"]["train"] // tr["ACCUM"][0])
    return per_epoch * tr["EPOCHS"][0]


def curves():
    d = SOL / "train"
    if not d.exists():
        return None
    out = {}
    for vdir in sorted(p for p in d.iterdir() if p.is_dir()):
        lp = vdir / "train_log.jsonl"
        if not lp.exists():
            continue
        rows = [json.loads(x) for x in open(lp) if x.strip()]
        steps = [(r["step"], r["loss"], r.get("epoch")) for r in rows if "loss" in r and "step" in r and "epoch_done" not in r]
        done = [{"epoch": r["epoch_done"], "validation_loss": r["validation_loss"], "step": r["step"]} for r in rows if "epoch_done" in r]
        if len(steps) > CURVE_POINTS:
            idx = sorted({round(i * (len(steps) - 1) / (CURVE_POINTS - 1)) for i in range(CURVE_POINTS)})
            steps = [steps[i] for i in idx]
        ch = None
        if (vdir / "chosen.json").exists():
            c = json.loads((vdir / "chosen.json").read_text())
            ch = {"epoch": c["epoch"], "validation_loss": c["validation_loss"], "by_epoch": c.get("by_epoch")}
        out[vdir.name] = F({"points": [[s, round(l, 5), e] for s, l, e in steps], "epochs": done, "chosen": ch, "logged_steps": len(rows)},
                           lp, "derived:train_log.jsonl rows with loss, downsampled to <= 300 points", f"training loss per optimizer step, run '{vdir.name}'")
    return out or None


# ------------------------------------------------------------------ steps 8-10
def other_fixes():
    ev = consts(P["eval"])
    sy = jload(P["b1r2"])["systems"]
    return {
        "instruction": F(P["note"].read_text().strip(), P["note"], "line:1", "the one-line instruction, exact text"),
        "label": cf(P["eval"], "WRAP", "the label put in front of a tool's output (the inserted tool turn only)"),
        "dial": {
            "layers": cf(CODE / "finetune/provenance.py", "READOUT", "the layers where attention to the tool turn is scaled"),
            "alphas_built": cf(CODE / "finetune/provenance.py", "ALPHAS", "settings the dial supports (only the two below were measured on the 120)"),
            "measured": [
                {"alpha": jf(P["b1r2"], "systems.prov-a1-v2.alpha", "dial setting 1 = the model itself"),
                 "following": jf(P["b1r2"], "systems.prov-a1-v2.wrong_hint_following | all", "wrong hints followed, k of n (runs)"),
                 "accepted": jf(P["b1r2"], "systems.prov-a1-v2.correct_hint_acceptance | all", "right hints taken, k of n"),
                 "accuracy": jf(P["b1r2"], "systems.prov-a1-v2.no_hint_accuracy | all", "no-hint accuracy, k of n")},
                {"alpha": jf(P["b1r2"], "systems.prov-deployable-a0.25-v2.alpha", "dial setting 0.25"),
                 "following": jf(P["b1r2"], "systems.prov-deployable-a0.25-v2.wrong_hint_following | all"),
                 "accepted": jf(P["b1r2"], "systems.prov-deployable-a0.25-v2.correct_hint_acceptance | all"),
                 "accuracy": jf(P["b1r2"], "systems.prov-deployable-a0.25-v2.no_hint_accuracy | all")},
            ],
            "questions": jf(P["b1r2"], "systems.prov-a1-v2.wrong_hint_following | all.questions", "questions"),
            "runs": jf(P["b1r2"], "systems.prov-a1-v2.runs", "runs a setting"),
        },
    }


def review():
    import agents.reviewer as rv
    tm = consts(P["run_team"])
    return {
        "variants": dv(list(rv.VARIANTS), P["reviewer"], "reviewer.VARIANTS", "what a reviewer can see besides the question and the proposed answer"),
        "solver": F(consts(P["run_team"])["SOLVER_MODEL"][0][1], P["run_team"], "const:SOLVER_MODEL[1]", "the solver, which calls the lookup tool"),
        "reviewer_system": F(consts(P["reviewer_demo"])["SYSTEM"][0], P["reviewer_demo"], "const:SYSTEM", "the reviewers' instruction, exact text"),
        "check_sentence": cf(P["run_team"], "CHECK_TOOL", "a sentence added to the reviewer's instruction in one test (it did not restore the check)"),
        "private_header": F("Private reasoning of the first assistant:", P["reviewer"], f"line:{lineno(P['reviewer'], 'Private reasoning of the first assistant')}", "how the reviewer's page labels the solver's reasoning"),
        "log_header": F("Tool log of the first assistant:", P["reviewer"], f"line:{lineno(P['reviewer'], 'Tool log of the first assistant')}", "how it labels the tool's log"),
        "checker": F("re-asks the same model the same question with no tool and flags the item when its answer differs", CODE / "agents/checker.py", "derived:docstring lines 1-2, in plain words", "the checker"),
        "bad_lookups": jf(CODE / "tools/demo_template/data.json", "agents.reviewers.0.answer_only.n", "wrong tool answers each reviewer grades"),
        "max_review_tokens": cf(P["run_team"], "REVIEWER_MAX_TOKENS", "tokens a reviewer may write"),
    }


# ------------------------------------------------------------------ step 11
def checking():
    l6 = jload(P["l6"])
    return {
        "wilson": {"z": lf(P["common"], r"def wilson\(k, n, z=(1\.\d+)\)", float, "the 95% Wilson interval's z"),
                   "what": F("k of n runs, with a 95% Wilson interval", P["common"], f"derived:def wilson (line {lineno(P['common'], 'def wilson')}), in plain words", "plain words")},
        "bootstrap": {"resamples": lf(P["common"], r"def boot_diff\(a, b, n=(\d+)", int, "resamples"),
                      "seed": lf(P["common"], r"def boot_diff\(a, b, n=\d+, seed=(\d+)", int, "seed"),
                      "min_questions": cf(P["common"], "MIN_QUESTIONS", "under this many questions behind an interval, the table says 'too few'"),
                      "paired_by_question": F("each resample draws questions with all their runs, in both systems", P["common"], f"derived:boot_diff's docstring (line {lineno(P['common'], 'clustered by question')}), in plain words", "plain words")},
        "labels": {
            "l3": lf(P["report"], r"L3, (\d+) runs", int, "runs labelled in the first sheet (the reasoning and the final answer)"),
            "l4": lf(P["report"], r"L4 part 1, (\d+) final answers", int, "final answers labelled in the second sheet"),
            "l6": jf(P["l6"], "rows", "final answers labelled in the third sheet"),
            "labels": F(["no mention", "mentions only", "rejects the hint", "says it changed the answer", "unclear"], P["report"], f"line:{lineno(P['report'], 'no mention, mentions only')}", "the five labels"),
            "kappa": jf(P["l6"], "kappa.overall.kappa", "Cohen's kappa between Ritik's labels and the blind AI judge, third sheet"),
            "agree": jf(P["l6"], "kappa.overall.agreement", "share of rows they agree on"),
            "agree_rows": F(round(l6["kappa"]["overall"]["agreement"] * l6["kappa"]["overall"]["rows"]), P["l6"], "derived:kappa.overall.agreement * kappa.overall.rows", "rows they agree on"),
            "judges": lf(P["report"], r"Three more AI judges:\*\* (Claude Opus)", str, "the blind judge's family (fresh sub-agents that saw only the guide and the blind rows)"),
        },
        "e2_checks": F(["the 120 against the 30 held-out (by id and by text)", "against the training pool", "against the review teams' 100", "no duplicates", "the hint letter is never the answer", "answer and hint letters spread over A-J"],
                       P["make_e2"], f"line:{lineno(P['make_e2'], 'def checks')}", "the exclusion checks the 120 fresh questions pass (plain words for make_e2.checks' fields)"),
        "heldout_checks": F(["no held-out question in training (by id or text)", "no held-out wording", "no held-out channel", "no held-out text in a prompt", "none over 32,768 tokens"],
                            P["check"], "derived:examples_check.json keys a_heldout, e_length, in plain words", "the leak checks on the training examples (plain words for examples_check.json's keys)"),
        "freeze": tag_info(),
        "prereg_count": dv(len(ledger()), P["prereg"], "len(ledger rows)", "rules in the pre-registration ledger"),
    }


# ------------------------------------------------------------------ counts (the other helper reads METHOD.counts.<key>.v and .what)
def counts():
    a39, a40, a42, ca = jload(P["a39"]), jload(P["a40"]), jload(P["a42"]), jload(P["a39"])["completeness"]
    six = {"base": a39, "prompt_only": a39, "lora": a39, "lora_note": a39, "a40": a40, "a40_note": a42}
    six_runs = sum(s["systems"][k]["runs"] for k, s in six.items())
    label_runs = sum(ca[k]["expected"] for k in ("wrap", "wrap_note", "lora_wrap"))
    b20 = jload(P["b20r"])
    newer = sum(v for m in b20.values() for v in m["runs"].values())
    labels = {"l3": checking()["labels"]["l3"]["v"], "l4": checking()["labels"]["l4"]["v"], "l6": jload(P["l6"])["rows"]}
    return {
        "models": dv(12, [P["report"], P["marks"]], "models(): 8 answering models and 4 reviewers", "models used: 8 answering models and 4 reviewers (the report's count)"),
        "runs_fresh_fixes": dv(six_runs + label_runs, [P["a39"], P["a40"], P["a42"]],
                               "sum(runs of base, prompt_only, lora, lora_note, a40, a40_note) + sum(expected of wrap, wrap_note, lora_wrap)",
                               "runs on the 120 fresh questions for the fixes: 6 systems x 1,440, plus 3 label systems x 480 (their other runs are shared with a system without the label)"),
        "runs_newer_families": dv(newer, P["b20r"], "sum(runs of every model and setting)", "runs on the three newer families: 5 model-and-thinking settings x 972"),
        "hand_labels": dv(sum(labels.values()), [P["report"], P["l6"]], "L3 + L4 part 1 + L6", "answers labelled by hand: 101 + 294 + 84"),
    }


# ------------------------------------------------------------------ the local pairs (model text; gitignored)
def local_pairs():
    out = {"note": "model text; gitignored; the local build passes this as RUNS.method_local"}
    for key, path, seed in (("lora", P["trainx"], "demo-lora-pair-20261122"), ("bct", P["a40x"], "demo-bct-pair-20261122")):
        if not path.exists():
            continue
        with gzip.open(path, "rt") as f:
            rows = [json.loads(x) for x in f]
        ok = [i for i, r in enumerate(rows) if r.get("hint_channel") not in (None, "none") and str(r.get("hint_correct")) in ("False", "false") and r.get("messages")]
        i = random.Random(seed).choice(ok)
        r = rows[i]
        out[key] = {"input": turns(r["messages"]), "tools": [t["function"]["name"] for t in (r.get("tools") or [])], "target": r["target_raw"],
                    "hint_channel": r["hint_channel"], "hint_letter": r["hint_letter"], "hint_wording": r["hint_wording"], "stance": r.get("stance"),
                    "tokens": r.get("tokens"), "seed": seed, "source": rel(path), "line": i + 1}
    return out


# ------------------------------------------------------------------ build
def build():
    q = questions()
    return {
        "freeze": tag_info(), "questions": q, "hint": hint(), "models": models(), "running": running(), "arch": arch(),
        "patching": patching(), "finetune": finetune(), "fixes": other_fixes(), "review": review(), "checking": checking(), "counts": counts(),
    }


def strip_none(o):
    if isinstance(o, dict):
        return {k: strip_none(v) for k, v in o.items() if v is not None}
    if isinstance(o, list):
        return [strip_none(v) for v in o]
    return o


def main():
    m = strip_none(build())
    OUT.write_text(json.dumps(m, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print(OUT, OUT.stat().st_size)
    LOCAL.parent.mkdir(parents=True, exist_ok=True)
    LOCAL.write_text(json.dumps(local_pairs(), ensure_ascii=False, indent=1) + "\n")
    print(LOCAL, LOCAL.stat().st_size)


if __name__ == "__main__":
    main()
