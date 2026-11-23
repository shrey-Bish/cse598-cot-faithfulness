"""The bench's recorded runs (Nov 22): every recorded run of the drawn questions, for the local build only.

  python tools/demo_template/runs.py      # -> results/demo/bench_runs.json (gitignored; never committed)

The questions are draw.json's (seeded, never by outcome). For each test, every recorded run of each drawn question
under each condition the test compares, with its file and line, our analysis's outcome fields (trackB_report.flags for
the models-and-sources runs, the run index's fields for the fixes, the review logs' own fields, the hand labels where
they exist) and its text (the exact prompt, the private reasoning, the tool call and reply, the final answer), gzipped
and base64-encoded so the page stays small; the page opens one when it's shown. Runs whose text is only on Sol come in
from results/demo/sol/ when it exists (tools/demo_template/sol.py); until then their outcome rows come from this Mac's
numbers-only indexes, marked "outcome only". "Run 20 more" draws 20 runs of a condition, by the seed, from the same
indexes (outcomes only). Read-only on every source.
"""
import base64
import glob
import gzip
import io
import json
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE = HERE.parents[1]
RES = CODE / "results"
OUT = RES / "demo" / "bench_runs.json"
SOL = RES / "demo" / "sol"
for p in (CODE, CODE / "progress", CODE / "tools"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

MODEL = {"qwen3-30b-a3b-thinking-2507": "Qwen3 30B Thinking", "qwen3-30b-a3b-instruct-2507": "Qwen3 30B Instruct",
         "olmo3-7b-think": "Olmo 3 7B Think", "qwen3-8b": "Qwen3-8B", "gpt-oss-20b": "gpt-oss-20b",
         "nemotron-3-nano-30b-a3b": "Nemotron 3 Nano 30B-A3B", "olmo3-32b-instruct": "Olmo 3.1 32B Instruct",
         "olmo3-7b-instruct": "Olmo 3 7B Instruct", "granite-4.1-30b": "Granite 4.1 30B", "mistral-small-3.2-24b": "Mistral Small 3.2 24B"}
SETTING = {"Qwen3 30B Thinking": "thinking always", "Qwen3 30B Instruct": "no thinking", "Olmo 3 7B Think": "thinking always"}
SRC = {"none": "none", "user": "user", "tool_pasted": "pasted", "tool_real": "call", "tool_injected": "call", "system": "system",
       "user_classmate": "classmate", "user_authority": "key", "user_manual": "manual"}


def jsonl(p):
    p = Path(p)
    op = gzip.open if p.suffix == ".gz" else open
    with op(p, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if line.strip():
                yield i, json.loads(line)


def rel(p):
    p = str(p)
    return p.split("cot-disclosure/", 1)[1] if "cot-disclosure/" in p else p


def blob(obj):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as g:
        g.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode())
    return base64.b64encode(buf.getvalue()).decode()


def model_name(m):
    m = (m or "").lower()
    for k, v in MODEL.items():
        if k in m:
            return v
    return m


def tool_of(r):
    """The tool call and reply, from the record's own steps or transcript."""
    for s in r.get("tool_steps") or r.get("steps") or []:
        if s.get("tool_calls"):
            c = s["tool_calls"][0]
            res = (s.get("tool_results") or [None])[0]
            return {"call": f"{c.get('name')}({c.get('arguments')})", "reply": res}
    for m in r.get("transcript") or r.get("prompt_messages") or []:
        if m.get("role") in ("tool", "environment"):
            return {"call": "a tool turn in the chat", "reply": m.get("content")}
    return None


def text_of(r):
    pm = r.get("prompt_messages") or r.get("messages")
    return blob({"prompt": pm if pm else r.get("rendered_prompt"), "reasoning": r.get("reasoning_text"),
                 "final": r.get("final_text"), "tool": tool_of(r)})


def date_of(r):
    return (r.get("timestamp_utc") or "")[:10]


def options_from(prompt):
    """(letter, text) pairs from a prompt's option lines '(A) ...'."""
    return re.findall(r"^\(([A-J])\)\s*(.+)$", prompt or "", flags=re.M)


# ---------------------------------------------------------------- the questions
def questions(draw):
    q = {}
    for name in ("fresh120", "held30"):
        src = "data/progress/mmlupro_e2.jsonl" if name == "fresh120" else "data/progress/mmlupro_30.jsonl"
        for i, r in jsonl(CODE / src):
            iid = f"mmlupro-{r['question_id']}"
            if iid in draw[name]["drawn"]:
                q[iid] = {"text": r["question"], "options": [[chr(65 + j), o] for j, o in enumerate(r["options"])],
                          "right": r["answer"], "hint": r.get("cue_letter"), "set": draw[name]["what"], "src": src, "line": i}
    c4_items = {c.split("|")[0] for c in draw["c4_bad"]["drawn"]}
    for i, r in jsonl(RES / "trackB/steered_cases.jsonl"):
        if (r["item_id"] in draw["test54"]["drawn"] or r["item_id"] in c4_items) and r["item_id"] not in q:
            opts = options_from(r["question"])
            stem = r["question"].split("\n(A)")[0].strip() if opts else r["question"]
            q[r["item_id"]] = {"text": stem, "options": [list(o) for o in opts], "right": r["correct_letter"],
                               "hint": r["hint_letter"], "set": draw["test54"]["what"], "src": "results/trackB/steered_cases.jsonl", "line": i}
    for i, r in jsonl(RES / "trackC/c15_items.jsonl"):
        if r["item_id"] in draw["c15"]["drawn"]:
            opts = options_from(r["question"])
            q.setdefault(r["item_id"], {"text": r["question"].split("\n(A)")[0].strip() if opts else r["question"],
                                        "options": [list(o) for o in opts], "right": r["correct_letter"], "hint": r["hint_letter"],
                                        "set": draw["c15"]["what"], "src": "results/trackC/c15_items.jsonl", "line": i})
    for i, r in jsonl(RES / "trackA/setA/items.jsonl"):
        qid = str(r.get("question_id"))
        iid = r.get("item_id") or (qid if qid.startswith(("mmlupro-", "puzzle-", "pilot-")) else f"mmlupro-{qid}")
        if iid in draw["patch16"]["drawn"]:
            q.setdefault(iid, {"text": r["question"], "options": [[chr(65 + j), o] for j, o in enumerate(r["options"])],
                               "right": r["answer"], "hint": r.get("cue_letter"), "set": draw["patch16"]["what"],
                               "src": "results/trackA/setA/items.jsonl", "line": i})
    return q


# ---------------------------------------------------------------- models and sources (tests 1-3)
def trackb_runs(path, items, conds, flags, test, extra=None):
    from common import latest
    rows = [(i, r) for i, r in jsonl(path) if r.get("item_id") in items and r.get("condition") in conds and r.get("status") == "ok"]
    keep = {id(r) for r in latest([r for _, r in rows])}
    out = []
    for i, r in rows:
        if id(r) not in keep:
            continue
        f = flags(r)
        m = model_name(r.get("model"))
        out.append({"t": test, "q": r["item_id"], "m": m, "s": setting_of(r, m), "src": SRC[r["condition"]],
                    "w": None if r["condition"] == "none" else True, "rep": r.get("repeat"), "L": r.get("parsed_letter"),
                    "H": r.get("hint_letter"), "R": r.get("correct_letter"),
                    "out": {"took": f["followed"] if r["condition"] != "none" else None, "private": f["mention_private"], "final": f["mention_final"]},
                    "rec": f"Recorded run: {m}, {setting_of(r, m)}, {date_of(r)}", "file": rel(path), "line": i, "x": text_of(r), **(extra or {})})
    return out


def setting_of(r, m):
    if m in SETTING:
        return SETTING[m]
    if r.get("reasoning_effort") and "gpt-oss" in m:
        return f"effort {r['reasoning_effort']}"
    th = r.get("thinking")
    return "thinking on" if th in (True, "on", "true") else "thinking off" if th in (False, "off", "false") else (th or "")


def outcome_rows(path, items, test, keep=lambda r: True):
    """Outcome-only rows from a numbers-only flags index (text on Sol)."""
    out = []
    for i, r in jsonl(path):
        if r.get("item_id") in items and keep(r):
            m = model_name(r.get("model"))
            out.append({"t": test, "q": r["item_id"], "m": m, "s": setting_of(r, m), "src": SRC.get(r.get("condition"), r.get("condition")),
                        "w": None if r.get("condition") == "none" else True, "rep": r.get("repeat"), "L": r.get("parsed_letter"),
                        "H": r.get("hint_letter"), "R": r.get("correct_letter"),
                        "out": {"took": r.get("followed") if r.get("condition") != "none" else None, "private": r.get("mention_private"),
                                "final": r.get("mention_final")},
                        "rec": f"Recorded run: {m}, {setting_of(r, m)}; outcome only (its text is on Sol)", "file": rel(path), "line": i, "x": None})
    return out


def sol_trackb(group, items, test, flags):
    p = SOL / f"runs_{group}.jsonl"
    if not p.exists():
        return None
    out = []
    for _, o in jsonl(p):
        r = o["record"]
        if r.get("item_id") not in items or r.get("status") != "ok":
            continue
        f = flags(r)
        m = model_name(r.get("model"))
        out.append({"t": test, "q": r["item_id"], "m": m, "s": setting_of(r, m), "src": SRC.get(r["condition"], r["condition"]),
                    "w": None if r["condition"] == "none" else True, "rep": r.get("repeat"), "L": r.get("parsed_letter"),
                    "H": r.get("hint_letter"), "R": r.get("correct_letter"),
                    "out": {"took": f["followed"] if r["condition"] != "none" else None, "private": f["mention_private"], "final": f["mention_final"]},
                    "rec": f"Recorded run: {m}, {setting_of(r, m)}, {date_of(r)}", "file": "Sol: " + o["src"], "line": o["line"], "x": text_of(r)})
    return out


# ---------------------------------------------------------------- the fixes (test 4)
# the fixes' plain names (bench.js FIXSHORT), for the record line; the 30's other trained versions too
FIX_NAME = {"base": "no fix", "prompt_only": "instruction", "lora": "fine-tuned", "lora_note": "fine-tuned + instruction", "a40": "consistency",
            "a40_note": "consistency + instruction", "wrap": "label", "wrap_note": "label + instruction", "lora_wrap": "fine-tuned + label",
            "lora_tags": "fine-tuned + tags", "lora_attn3": "fine-tuned on 3 layers", "tags": "tags only"}
FIX_SRC = {"user": "user", "tool_pasted": "pasted", "tool_injected": "call", "none": "none", "system_note": "system"}


def fixes_index(items):
    rows = []
    for p in sorted(glob.glob(str(RES / "trackA/gpu/a39/eval_*_runs.jsonl"))) + sorted(glob.glob(str(RES / "trackA/gpu/eval/eval_*_runs.jsonl"))):
        qset = "120" if "_a39_e2_" in p else "30"
        for i, r in jsonl(p):
            if r.get("item_id") in items and r.get("status") == "ok":
                rows.append((p, i, qset, r))
    last = {r["run_id"]: k for k, (_, _, _, r) in enumerate(rows)}      # a run listed twice: its last line, as latest()
    return [x for k, x in enumerate(rows) if last[x[3]["run_id"]] == k]


def fixes_runs(items):
    idx = fixes_index(items)
    sol = {}
    for g in ("fixes_120", "fixes_30"):
        p = SOL / f"runs_{g}.jsonl"
        if p.exists():
            for _, o in jsonl(p):
                sol[o["record"].get("run_id")] = o
    out = []
    for p, i, qset, r in idx:
        hc = r.get("hint_correct")
        w = None if r.get("channel") == "none" else (not hc)
        took = None if w is None else (r.get("parsed_letter") == r.get("hint_letter"))
        o = sol.get(r["run_id"])
        out.append({"t": 4, "q": r["item_id"], "m": "Olmo 3 7B Think", "s": "thinking always", "fix": r.get("system"), "qset": qset,
                    "src": FIX_SRC.get(r.get("channel"), r.get("channel")), "wording": r.get("wording"), "w": w, "rep": r.get("repeat"),
                    "L": r.get("parsed_letter"), "H": r.get("hint_letter"), "R": r.get("correct_letter"),
                    "out": {"took": took, "private": r.get("mention_reasoning"), "final": r.get("mention_final_broad", r.get("mention_final"))},
                    "rec": f"Recorded run: Olmo 3 7B Think, {FIX_NAME.get(r.get('system'), 'another fix')}, {date_of(r)}" + ("" if o else "; outcome only (its text is on Sol)"),
                    "file": rel(p), "line": i, "text_file": ("Sol: " + o["src"]) if o else None, "text_line": o["line"] if o else None,
                    "x": text_of(o["record"]) if o else None})
    return out


def l6_finals():
    """L6's frozen sheet: the final answers of the fine-tuned model and the one-line instruction, with Ritik's labels."""
    base = RES / "labels/L6"
    if not (base / "texts_L6.jsonl").exists():
        return []
    import csv
    key = {r["row"]: r for r in csv.DictReader(open(base / "key_L6.csv"))}
    lab = {r["row"]: r for r in csv.DictReader(open(base / "L6_RA_20261113.csv"))}
    texts = {(r["run_id"], r["timestamp_utc"]): (i, r) for i, r in jsonl(base / "texts_L6.jsonl")}
    out = []
    for row, k in sorted(key.items(), key=lambda kv: int(kv[0])):
        i, t = texts.get((k["run_id"], k["timestamp_utc"]), (None, None))
        if t is None:
            continue
        out.append({"row": int(row), "fix": k["system"], "src": FIX_SRC.get(k["channel"], k["channel"]), "q": k["item_id"],
                    "H": t.get("hint_letter"), "L": t.get("parsed_letter"), "label": lab.get(row, {}).get("label_final"),
                    "file": "results/labels/L6/texts_L6.jsonl", "line": i, "x": blob({"final": t.get("final_text")})})
    return out


# ---------------------------------------------------------------- review teams (test 5)
REVIEW_LOGS = ["team_c4.jsonl", "team_c11.jsonl", "team_c13_granite.jsonl", "team_c13_mistral.jsonl"]


def review_cases(cases, c15_items):
    out = []
    solvers = {}
    for log, keep in (("team_c4.jsonl", lambda r: r.get("case_id") in cases), ("team_c15_solve.jsonl", lambda r: r.get("item_id") in c15_items)):
        for i, r in jsonl(RES / "trackC" / log):
            if not keep(r) or r.get("team") != "tool":
                continue
            if r.get("agent") == "solver":
                solvers[r["attempt"]] = r["case_id"]
                out.append({"t": 5, "kind": "solver", "case": r["case_id"], "q": r["item_id"], "m": model_name(r.get("model")),
                            "bad": r.get("bad_lookup"), "tool_letter": r.get("tool_letter"), "L": r.get("letter"), "R": r.get("correct"),
                            "set": "c15" if "c15" in log else "c4", "rec": f"Recorded run: {model_name(r.get('model'))}, solver with the tool, {date_of(r)}",
                            "file": f"results/trackC/{log}", "line": i, "x": blob({"reasoning": r.get("reasoning_text"), "final": r.get("final_text"), "tool": tool_of(r)})})
            elif r.get("agent") == "checker":
                out.append({"t": 5, "kind": "checker", "case": r["case_id"], "q": r["item_id"], "m": model_name(r.get("model")),
                            "L": r.get("letter"), "flag": r.get("checker_flag"), "set": "c15" if "c15" in log else "c4",
                            "file": f"results/trackC/{log}", "line": i})
    for log in REVIEW_LOGS + ["team_c15.jsonl"]:
        for i, r in jsonl(RES / "trackC" / log):
            if r.get("agent") != "reviewer" or r.get("team") != "tool":
                continue
            if not (r.get("case_id") in cases or (log == "team_c15.jsonl" and r.get("item_id") in c15_items)):
                continue
            out.append({"t": 5, "kind": "reviewer", "case": r["case_id"], "q": r["item_id"], "m": model_name(r.get("reviewer_model") or r.get("model")),
                        "variant": r.get("variant"), "L": r.get("letter"), "solver_L": r.get("solver_letter"), "R": r.get("correct"),
                        "corrected": r.get("letter") == r.get("correct"), "solver_wrong": r.get("solver_wrong"),   # agents/c15.py corrects()
                        "set": "c15" if log == "team_c15.jsonl" else "c4",
                        "rec": f"Recorded verdict: {model_name(r.get('reviewer_model') or r.get('model'))}, {r.get('variant')}, {date_of(r)}",
                        "file": f"results/trackC/{log}", "line": i, "x": blob({"final": r.get("final_text")})})
    return out


# ---------------------------------------------------------------- inside the model (test 6)
def patching(items):
    """The analysis's own per-question numbers (finetune/look/patching.py): per cut, the share of the hint's drop at each
    layer (where it leaves the hint's tokens) and of its rise (where it reaches the answer)."""
    src = RES / "trackA/setA/step10_handoff.json"
    meta = {c["job"]: c for c in json.loads((RES / "trackA/setA/step10_patching.json").read_text())["cuts"]}
    out = []
    for j, c in enumerate(json.loads(src.read_text())["handoff"]["per_cut"]):
        if c["item_id"] not in items:
            continue
        m = meta.get(c["job"], {})
        out.append({"t": 6, "q": c["item_id"], "cut": c["cut"], "src": SRC.get(m.get("condition"), m.get("condition")), "H": m.get("hint_letter"),
                    "own": m.get("own_letter"), "drop": c["drop_by_layer"], "rise": c["rise_by_layer"],
                    "drop_readout": c["drop_share_readout"], "rise_readout": c["rise_share_readout"],
                    "file": rel(src), "line": f"handoff.per_cut[{j}]"})
    runs = [{"t": 6, "kind": "run", "q": r["item_id"], "src": SRC.get(r.get("condition"), r.get("condition")), "rep": r.get("repeat"),
             "L": r.get("parsed_letter"), "H": r.get("cue_letter"), "R": r.get("correct_letter"),
             "rec": f"Recorded run: Olmo 3 7B Think, thinking always, {date_of(r)}", "file": "results/trackA/setA/runs.jsonl.gz", "line": i, "x": text_of(r)}
            for i, r in jsonl(RES / "trackA/setA/runs.jsonl.gz") if r.get("item_id") in items]
    return out, runs


# ---------------------------------------------------------------- "Run 20 more": seeded outcome samples
def samples(seed, test1, test4):
    rnd_key = lambda k: random.Random(f"{seed}:sample:{k}")
    out = {}

    def add(key, rows):
        rows = sorted(rows, key=lambda r: r["id"])
        if rows:
            out[key] = {"n_index": len(rows), "runs": rnd_key(key).sample(rows, min(20, len(rows)))}

    from trackB_report import flags
    from common import latest
    groups = {}
    for name in ("voyager", "b16_voyager", "b19_voyager", "b24_voyager"):
        for r in latest([r for _, r in jsonl(RES / f"trackB/{name}.jsonl.gz") if r.get("status") == "ok"]):
            f = flags(r)
            m = model_name(r["model"])
            groups.setdefault(f"{m}|{setting_of(r, m)}|{SRC[r['condition']]}|{name}", []).append(
                {"id": r["run_id"], "q": r["item_id"], "took": f["followed"], "private": f["mention_private"], "final": f["mention_final"]})
    for path in ("trackB/sol_vllm_flags.jsonl", "trackB/b17/b17_flags.jsonl"):
        for _, r in jsonl(RES / path):
            if r.get("status") not in (None, "ok"):
                continue
            m = model_name(r.get("model"))
            groups.setdefault(f"{m}|{setting_of(r, m)}|{SRC.get(r['condition'], r['condition'])}|sol", []).append(
                {"id": r["run_id"], "q": r["item_id"], "took": r.get("followed"), "private": r.get("mention_private"), "final": r.get("mention_final")})
    for p in sorted(glob.glob(str(RES / "trackA/gpu/a39/eval_*_a39_e2_*_runs.jsonl"))):
        for _, r in jsonl(p):
            if r.get("status") != "ok" or r.get("channel") == "none":
                continue
            key = f"fix|{r['system']}|{FIX_SRC.get(r['channel'], r['channel'])}|{'right' if r.get('hint_correct') else 'wrong'}"
            groups.setdefault(key, []).append({"id": r["run_id"], "q": r["item_id"], "took": r.get("parsed_letter") == r.get("hint_letter"),
                                               "final": r.get("mention_final_broad", r.get("mention_final"))})
    for k, rows in groups.items():
        add(k, rows)
    return out


def build(draw_path=HERE / "draw.json"):
    from trackB_report import flags
    d = json.loads(Path(draw_path).read_text())
    sets = d["sets"]
    t54 = set(sets["test54"]["drawn"])
    runs = []
    runs += trackb_runs(RES / "trackB/voyager.jsonl.gz", t54, ("none", "user", "tool_pasted", "tool_real", "tool_injected"), flags, 1)
    runs += trackb_runs(RES / "trackB/voyager.jsonl.gz", t54, ("user",), flags, 2)
    runs += trackb_runs(RES / "trackB/b24_voyager.jsonl.gz", t54, ("user_classmate", "user_manual"), flags, 2)
    runs += trackb_runs(RES / "trackB/b16_voyager.jsonl.gz", t54, ("user_authority",), flags, 2)
    runs += trackb_runs(RES / "trackB/b19_voyager.jsonl.gz", t54, ("tool_pasted", "tool_real", "tool_injected"), flags, 2)
    sol_state = {}
    for g, test_ids in (("qwen8b", (1, 3)), ("gptoss", (1, 3)), ("nemotron", (1, 3))):
        got = sol_trackb(g, t54, 1, flags)
        sol_state[g] = got is not None
        if got is None:
            if g == "qwen8b":
                got = outcome_rows(RES / "trackB/sol_vllm_flags.jsonl", t54, 1)
            elif g == "gptoss":
                got = outcome_rows(RES / "trackB/b17/b17_flags.jsonl", t54, 1)
            else:
                got = []
        for t in test_ids:
            runs += [dict(r, t=t) for r in got]
    fx = fixes_runs(set(sets["fresh120"]["drawn"]) | set(sets["held30"]["drawn"]))
    runs += fx
    runs += review_cases(set(sets["c4_bad"]["drawn"]), set(sets["c15"]["drawn"]))
    cuts, prun = patching(set(sets["patch16"]["drawn"]))
    runs += prun
    return {"seed": d["seed"], "draw": sets, "tests": d["tests"], "questions": questions(sets), "runs": runs, "cuts": cuts,
            "l6": l6_finals(), "samples": samples(d["seed"], None, None),
            "sol": {**sol_state, "fixes": any((SOL / f"runs_{g}.jsonl").exists() for g in ("fixes_120", "fixes_30"))},
            "not_in_build": ["Gemma 4 26B-A4B", "Granite 4.2 8B"]}


if __name__ == "__main__":
    out = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    by = {}
    for r in out["runs"]:
        k = (r["t"], "text" if r.get("x") else "outcome")
        by[k] = by.get(k, 0) + 1
    print(OUT, f"{OUT.stat().st_size / 1e6:.1f} MB", dict(sorted(by.items())), "cuts", len(out["cuts"]), "l6", len(out["l6"]),
          "samples", len(out["samples"]), "sol", out["sol"])
