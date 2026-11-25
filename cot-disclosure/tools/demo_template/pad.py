"""The scratch pad's data (Nov 23): every recorded run of each question, one JSON per question, for the local build only.

  python tools/demo_template/pad.py        # -> results/demo/pad/index.json and pad/<dataset>/<question>.json (gitignored)

Four datasets: the 54 test questions, the 30 held-out, the 120 fresh, the review team's items. Each question's file
holds every recorded run of it (the bench's row shape, runs.py), each with its file and line and its text gzipped
(prompt, private reasoning, tool call and reply, final answer, and the spans where the analysis's own keyword matcher
fires: runs.spans_of, detect.COMPILED). Texts come from this Mac (the Voyager runs, the review logs) and from the Sol
copy: results/demo/sol/all/ (sol.py unpack_all, every run) when it exists, else the drawn copy (results/demo/sol/runs_*).
A run whose text is not here is kept as its outcome row, marked "outcome only". Outcomes are the analysis's own fields
(trackB_report.flags for the models-and-sources runs, the run index's fields for the fixes and the dial), with each
analysis's own rule for a run with no answer: Gate 3's, A39's and the 54's counts leave it out (took is null, Nov 24),
the dial's counts it as not taking the hint. On the 54 a tool call's reply is one channel per model and setting, as the
frozen counts take it: Nemotron's two own-call smoke runs (pilot-0, Nov 4) beside its 162 inserted turns are left out. Counts are
not computed here: the page reads them from DATA.pad (counts(), the frozen summaries, each with its path).
The case finder (Nov 23, "Show me"): each question's entry in the index also carries its runs' own outcome fields, compact
(finder_rows: a key table per dataset, then per run [key, took, said so in the answer, in the reasoning]); the page counts the questions
that fit a pattern from these and orders the matches by FINDER_SEED (fnv1a of seed:id), never by outcome.
Read-only on every source.
"""
import glob
import gzip
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import runs as R  # noqa: E402

CODE, RES = R.CODE, R.RES
OUT = RES / "demo" / "pad"
SOL, ALL = RES / "demo" / "sol", RES / "demo" / "sol" / "all"
SUM = RES / "summaries"

DATASETS = [
    {"id": "test54", "label": "The 54 test questions", "short": "the 54"},
    {"id": "held30", "label": "The 30 held-out questions", "short": "the 30"},
    {"id": "fresh120", "label": "The 120 fresh questions", "short": "the 120"},
    {"id": "review", "label": "The review team's items", "short": "review"},
]
# the version row, in the order the page shows it (key -> plain name)
VERSIONS = [("base", "No fix"), ("prompt_only", "One-line instruction"), ("lora", "Fine-tuned"), ("lora_tags", "Fine-tuned + tags"),
            ("tags", "Tags only"), ("lora_attn3", "Fine-tuned on 3 layers"), ("a40", "Consistency-trained"),
            ("a40_note", "Consistency-trained + instruction"), ("lora_note", "Fine-tuned + instruction"), ("wrap", "Label"),
            ("wrap_note", "Label + instruction"), ("lora_wrap", "Fine-tuned + label"), ("dial", "Attention dial")]
FINDER_SEED = "cse598-demo-finder-2026-11-23"
FINDER_KEY = ("m", "s", "v", "exp", "src", "wd", "w")      # a run's condition, as the page's pMatch reads it
DIAL = {"prov-deployable-a0.25-v2": "dial", "prov-a1-v2": "dial_off"}   # the dial at 0.25, and at 1 (its own control)
SRC = {"user": "user", "tool_pasted": "pasted", "tool_real": "call", "tool_injected": "call", "tool_injected_undeclared": "call",
       "system": "system", "system_note": "system", "none": "none", "user_classmate": "classmate", "user_authority": "key",
       "user_manual": "manual"}
SOURCE_NAME = {"user": "the user says it", "classmate": "a classmate says it", "key": "an answer key says it",
               "manual": "the manual says it", "pasted": "a pasted tool block", "call": "a tool call's reply",
               "system": "a system note", "none": "no hint"}


def safe(qid):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", qid)


# ---------------------------------------------------------------- questions
def questions_all():
    out = {d["id"]: {} for d in DATASETS}
    for ds, src in (("fresh120", "data/progress/mmlupro_e2.jsonl"), ("held30", "data/progress/mmlupro_30.jsonl")):
        for i, r in R.jsonl(CODE / src):
            iid = f"mmlupro-{r['question_id']}"
            out[ds][iid] = {"id": iid, "item": iid, "text": r["question"], "options": [[chr(65 + j), o] for j, o in enumerate(r["options"])],
                            "right": r["answer"], "subject": r.get("category"), "src": src, "line": i}
    steered = {}
    for i, r in R.jsonl(RES / "trackB/steered_cases.jsonl"):
        opts = R.options_from(r["question"])
        steered[r["item_id"]] = {"id": r["item_id"], "item": r["item_id"],
                                 "text": r["question"].split("\n(A)")[0].strip() if opts else r["question"],
                                 "options": [list(o) for o in opts], "right": r["correct_letter"], "hint": r["hint_letter"],
                                 "subject": r.get("category") or r.get("kind"), "src": "results/trackB/steered_cases.jsonl", "line": i}
    out["test54"] = dict(steered)
    c15 = {}
    for i, r in R.jsonl(RES / "trackC/c15_items.jsonl"):
        opts = R.options_from(r["question"])
        c15[r["item_id"]] = {"text": r["question"].split("\n(A)")[0].strip() if opts else r["question"], "options": [list(o) for o in opts],
                             "right": r["correct_letter"], "hint": r.get("hint_letter"), "src": "results/trackC/c15_items.jsonl", "line": i}
    return out, steered, c15


# ---------------------------------------------------------------- texts from the Sol copy
def sol_records(group):
    """(src, line, record) of a Sol group: the full copy when unpacked, else the drawn copy."""
    full, drawn = ALL / f"runs_{group}.jsonl.gz", SOL / f"runs_{group}.jsonl"
    p = full if full.exists() else drawn if drawn.exists() else None
    if p is None:
        return "none", iter(())
    return ("all" if p == full else "drawn"), (( "Sol: " + o["src"], o["line"], o["record"]) for _, o in R.jsonl(p))


def sol_texts(groups):
    """(run id, timestamp) -> (file, line, blob), for the fixes and the dial (their outcomes come from this Mac's index).
    The timestamp is part of the key: one run id names two runs on Sol (c43d897ec5a49dd1, in two parts)."""
    texts, state = {}, {}
    for g in groups:
        state[g], it = sol_records(g)
        for src, line, r in it:
            if r.get("run_id"):
                texts[(r["run_id"], r.get("timestamp_utc"))] = (src, line, R.text_of(r))
    return texts, state


# ---------------------------------------------------------------- the fixes and the dial (Olmo 3 7B Think)
INDEXES = [  # (dataset, experiment, glob of this Mac's numbers-only run index)
    ("fresh120", "a39", "trackA/gpu/a39/eval_*_a39_e2_*runs.jsonl"),
    ("held30", "g3", "trackA/gpu/eval/eval_*_runs.jsonl"),
    ("held30", "a39", "trackA/gpu/a39/eval_*_a39_mmlupro_30_*runs.jsonl"),
    ("fresh120", "dial", "trackA/gpu/b1r2/eval_prov-*_runs.jsonl"),
    ("held30", "dial", "trackA/gpu/provenance_gen/eval_prov-*_runs.jsonl"),
]


def olmo_rows(texts):
    rows = {}
    for ds, exp, pat in INDEXES:
        got = []
        for p in sorted(glob.glob(str(RES / pat))):
            for i, r in R.jsonl(p):
                if r.get("status") != "ok":
                    continue
                v = DIAL.get(r.get("system")) if exp == "dial" else r.get("system")
                if v is None:
                    continue
                got.append((p, i, r, v))
        last = {r["run_id"]: k for k, (_, _, r, _) in enumerate(got)}      # a run listed twice: its last line (latest())
        for k, (p, i, r, v) in enumerate(got):
            if last[r["run_id"]] != k:
                continue
            hc = r.get("hint_correct")
            w = None if r.get("channel") == "none" else (not hc)
            t = texts.get((r["run_id"], r.get("timestamp_utc")))
            name = "the attention dial at 0.25" if v == "dial" else "the dial at 1 (its control)" if v == "dial_off" else R.FIX_NAME.get(v, v)
            rows.setdefault(ds, []).append({
                "id": r["run_id"], "q": r["item_id"], "m": "Olmo 3 7B Think", "s": "thinking always", "v": v, "exp": exp,
                "src": SRC.get(r.get("channel"), r.get("channel")), "wd": r.get("wording"), "w": w, "rep": r.get("repeat"),
                "L": r.get("parsed_letter"), "H": r.get("hint_letter"), "R": r.get("correct_letter"), "date": R.date_of(r),
                # a run with no answer: out of Gate 3's and A39's counts (their n is the answered runs), not taken in the dial's
                "out": {"took": None if w is None or (exp != "dial" and not r.get("parsed_letter")) else (r.get("parsed_letter") == r.get("hint_letter")),
                        "private": None if w is None else r.get("mention_reasoning"),
                        "final": None if w is None else r.get("mention_final_broad", r.get("mention_final"))},
                "rec": f"Recorded run: Olmo 3 7B Think, {name}, {R.date_of(r)}" + ("" if t else "; outcome only (its text is on Sol)"),
                "file": R.rel(p), "line": i, "text_file": t[0] if t else None, "text_line": t[1] if t else None, "x": t[2] if t else None})
    return rows


# ---------------------------------------------------------------- the 54: models and sources
def trackb_rows(items):
    from trackB_report import flags
    out = []

    def answered(r):      # a run with no answer is out of the 54's counts (their n is the answered runs)
        return dict(r, out=dict(r["out"], took=None)) if not r.get("L") and (r.get("out") or {}).get("took") is not None else r

    def add(rows, exp):
        for r in rows:
            out.append(answered(dict(r, v="base", exp=exp, id=None, date=r["rec"].rsplit(", ", 1)[-1], src=r["src"] if r["src"] != "answer_key" else "key")))
    add(R.trackb_runs(RES / "trackB/voyager.jsonl.gz", items, ("none", "user", "tool_pasted", "tool_real", "tool_injected", "system"), flags, 1), "voyager")
    add(R.trackb_runs(RES / "trackB/b24_voyager.jsonl.gz", items, ("user_classmate", "user_manual"), flags, 1), "b24")
    add(R.trackb_runs(RES / "trackB/b16_voyager.jsonl.gz", items, ("user_authority",), flags, 1), "b16")
    state, sol = {}, []
    for g in ("qwen8b", "gptoss", "nemotron"):
        state[g], it = sol_records(g)
        for src, line, r in it:
            if r.get("item_id") not in items or r.get("status") != "ok":
                continue
            sol.append((src, line, r))
    # a tool call's reply: one channel per model and setting, the one with the full set (the frozen counts' channel)
    chan = {}
    for _, _, r in sol:
        if r["condition"] in ("tool_real", "tool_injected"):
            k = (r.get("model"), str(r.get("thinking")), r.get("reasoning_effort"))
            chan.setdefault(k, {}).setdefault(r["condition"], 0)
            chan[k][r["condition"]] += 1
    for src, line, r in sol:
        if r["condition"] in ("tool_real", "tool_injected"):
            c = chan[(r.get("model"), str(r.get("thinking")), r.get("reasoning_effort"))]
            if c[r["condition"]] < max(c.values()):
                continue
        f = flags(r)
        m = R.model_name(r.get("model"))
        hinted = r["condition"] != "none"
        out.append({"t": 1, "q": r["item_id"], "m": m, "s": R.setting_of(r, m), "v": "base", "exp": "sol", "id": r.get("run_id"),
                    "src": SRC.get(r["condition"], r["condition"]), "w": True if hinted else None, "rep": r.get("repeat"),
                    "L": r.get("parsed_letter"), "H": r.get("hint_letter"), "R": r.get("correct_letter"), "date": R.date_of(r),
                    "out": {"took": f["followed"] if hinted and f["answered"] else None, "private": f["mention_private"], "final": f["mention_final"]},
                    "rec": f"Recorded run: {m}, {R.setting_of(r, m)}, {R.date_of(r)}", "file": src, "line": line, "x": R.text_of(r)})
    return out, state


# ---------------------------------------------------------------- the review team
def review_rows(steered, c15):
    cases = set()
    for _, r in R.jsonl(RES / "trackC/team_c4.jsonl"):
        if r.get("team") == "tool" and r.get("agent") == "solver" and r.get("bad_lookup"):
            cases.add(r["case_id"])
    rows = R.review_cases(cases, set(c15))
    by = {}
    for r in rows:
        by.setdefault(r["case"], []).append(r)
    qs = {}
    for case, rs in by.items():
        item = rs[0]["q"]
        base = steered.get(item) or c15.get(item)
        if base is None or not any(x["kind"] == "solver" for x in rs):
            continue
        qs[case] = dict(base, id=case, item=item, set=rs[0]["set"])
    return qs, by


# ---------------------------------------------------------------- the frozen counts (DATA.pad)
def _kn(o):
    return None if not isinstance(o, dict) or o.get("k") is None else {"k": o["k"], "n": o["n"]}


def counts(frozen=None):
    """Every count the pad shows, each with its path in the frozen data: the explainer's compact(collect()) ("x." and
    "s4."/"s5." paths) or a frozen summary file ("<file>: key.key"). tests/test_demo_pad.py resolves each path."""
    if frozen is None:
        sys.path[:0] = [str(CODE / "tools"), str(CODE / "progress")]
        import build_demo as bd
        frozen = bd.compact(bd.collect(bd.SUM))
    c = {"test54": {}, "fresh120": {}, "held30": {}, "review": {}}
    for j, s in enumerate(frozen["x"]["settings"]):
        row = {}
        for src, o in s["sources"].items():
            kn = _kn(o.get("f"))
            if kn:
                row["key" if src == "answer_key" else src] = dict(kn, path=f"x.settings[{j}].sources.{src}.f")
        c["test54"][f"{s['model']}|{s['setting']}"] = row
    for sy, e in frozen["x"]["fresh"].items():
        if sy == "dial":
            c["fresh120"]["dial"] = {"wrong": {"call": dict(_kn(e["sources"]["call"]["f"]), path="x.fresh.dial.sources.call.f")},
                                     "right": {"call": dict(_kn(e["accept"]["call"]), path="x.fresh.dial.accept.call")}}
            c["fresh120"]["dial_off"] = {"wrong": {"call": dict(_kn(e["same_run_none"]["f"]), path="x.fresh.dial.same_run_none.f")},
                                         "right": {"call": dict(_kn(e["same_run_none"]["accept"]), path="x.fresh.dial.same_run_none.accept")}}
            continue
        c["fresh120"][sy] = {"wrong": {src: dict(_kn(o["f"]), path=f"x.fresh.{sy}.sources.{src}.f") for src, o in e["sources"].items() if _kn(o.get("f"))},
                             "right": {src: dict(_kn(o), path=f"x.fresh.{sy}.accept.{src}") for src, o in (e.get("accept") or {}).items() if _kn(o)}}
    ev = "trackA/gpu/eval/eval_report.json"
    rep = json.loads((SUM / ev).read_text())["systems"]
    CH = {"user": "user", "pasted": "pasted", "inserted_declared": "call", "inserted_undeclared": "call_undeclared", "system": "system"}
    for sy, e in rep.items():
        c["held30"][f"g3:{sy}"] = {"wrong": {CH[ch]: dict(_kn(o), path=f"{ev}: systems.{sy}.following_by_channel.{ch}")
                                             for ch, o in e.get("following_by_channel", {}).items() if ch in CH and _kn(o)},
                                   "right": {"all": dict(_kn(e["correct_hint_agreement"]), path=f"{ev}: systems.{sy}.correct_hint_agreement")}
                                   if _kn(e.get("correct_hint_agreement")) else {}}
    a3 = "trackA/gpu/a39/a39_mmlupro_30.json"
    rep = json.loads((SUM / a3).read_text())["systems"]
    for sy, e in rep.items():
        fo = e.get("following") or {}
        ac = e.get("acceptance") or {}
        c["held30"][f"a39:{sy}"] = {"wrong": {("call" if k == "inserted" else k): dict(_kn(o), path=f"{a3}: systems.{sy}.following.{k}")
                                              for k, o in fo.items() if k in ("user", "pasted", "inserted") and _kn(o)},
                                    "right": {("all" if k == "pooled" else "call" if k == "inserted" else k): dict(_kn(o), path=f"{a3}: systems.{sy}.acceptance.{k}")
                                              for k, o in ac.items() if k in ("pooled", "pasted", "inserted") and _kn(o)}}
    b1 = next((j, r) for j, r in enumerate(frozen["s5"]["b1r2"]) if r["study"] == "B1")
    j, r = b1
    c["held30"]["dial:dial"] = {"wrong": {"call": {"k": r["following"]["k"], "n": r["following"]["n"], "path": f"s5.b1r2[{j}].following"}},
                                "right": {"call": {"k": r["acceptance"]["k"], "n": r["acceptance"]["n"], "path": f"s5.b1r2[{j}].acceptance"}}}
    c["held30"]["dial:dial_off"] = {"wrong": {"call": {"k": r["following"]["base_k"], "n": r["following"]["base_n"], "path": f"s5.b1r2[{j}].following.base"}},
                                    "right": {"call": {"k": r["acceptance"]["base_k"], "n": r["acceptance"]["base_n"], "path": f"s5.b1r2[{j}].acceptance.base"}}}
    s4 = frozen["s4"]
    c["review"] = {"reviewers": [{"name": rv["name"], "run": rv.get("run"), **{k: dict(_kn(rv[k]), path=f"s4.reviewers[{j}].{k}") for k in ("answer_only", "plus_private", "plus_tool_log") if _kn(rv.get(k))}}
                                 for j, rv in enumerate(s4["reviewers"])],
                   "c15": [{"name": rv["name"], "run": rv.get("run"), **{k: dict(_kn(rv[k]), path=f"s4.c15[{j}].{k}") for k in ("answer_only", "plus_tool_log", "plus_tool_log_redacted", "plus_private") if _kn(rv.get(k))}}
                           for j, rv in enumerate(s4["c15"])],
                   "checker": {k: dict(_kn(v), path=f"s4.checker.{k}") for k, v in s4["checker"].items() if _kn(v)}}
    return c


# ---------------------------------------------------------------- build
def _row_versions(rows):
    nv = {}
    for r in rows:
        k = r.get("v") or r.get("kind")
        nv[k] = nv.get(k, 0) + 1
    return nv


def _tri(v):
    return None if v is None else int(bool(v))


def finder_rows(rows, keys, kix):
    """A question's runs for the case finder, in file order: [key index, took the hint, said so in the answer, said so
    in the private reasoning] (1, 0, or null when the run has no such outcome); keys/kix: the dataset's key table,
    filled as it goes."""
    out = []
    for r in rows:
        k = tuple(r.get(f) for f in FINDER_KEY)
        if k not in kix:
            kix[k] = len(keys)
            keys.append(list(k))
        o = r.get("out") or {}
        out.append([kix[k], _tri(o.get("took")), _tri(o.get("final")), _tri(o.get("private"))])
    return out


def build(out=OUT, quiet=False):
    out = Path(out)
    draw = json.loads((HERE / "draw.json").read_text())["sets"]
    qs, steered, c15 = questions_all()
    texts, olmo_state = sol_texts(("fixes_120", "fixes_30", "dial"))
    olmo = olmo_rows(texts)
    t54, sol_state = trackb_rows(set(steered))
    rq, rrows = review_rows(steered, c15)
    qs["review"] = rq
    per = {"test54": {}, "held30": {}, "fresh120": {}, "review": {}}
    for r in t54:
        per["test54"].setdefault(r["q"], []).append(r)
    for ds, rows in olmo.items():
        for r in rows:
            per[ds].setdefault(r["q"], []).append(r)
    per["review"] = rrows
    index = {"datasets": [], "versions": VERSIONS, "sources": SOURCE_NAME,
             "sol": {**olmo_state, **sol_state}, "not_here": ["Gemma 4 26B-A4B", "Granite 4.2 8B"],
             "finder": {"seed": FINDER_SEED, "key": list(FINDER_KEY),
                        "how": "matches ordered by fnv1a-32 of seed + ':' + question id, never by outcome"}}
    drawn = {"test54": draw["test54"]["drawn"], "held30": draw["held30"]["drawn"], "fresh120": draw["fresh120"]["drawn"],
             "review": draw["c4_bad"]["drawn"] + sorted(c for c, q in rq.items() if q["item"] in set(draw["c15"]["drawn"]) and q.get("set") == "c15")}
    total = {}
    for d in DATASETS:
        ds = d["id"]
        (out / ds).mkdir(parents=True, exist_ok=True)
        entries, keys, kix = [], [], {}
        for qid, q in sorted(qs[ds].items()):
            rows = per[ds].get(qid, [])
            if not rows:
                continue
            f = f"{ds}/{safe(qid)}.json"
            (out / f).write_text(json.dumps({"dataset": ds, "q": q, "runs": rows}, ensure_ascii=False, separators=(",", ":")))
            entries.append({"id": qid, "item": q.get("item", qid), "file": f, "text": q["text"], "options": q["options"], "right": q["right"],
                            "hint": q.get("hint"), "subject": q.get("subject"), "src": q.get("src"), "line": q.get("line"),
                            "nv": _row_versions(rows), "texts": sum(1 for r in rows if r.get("x")), "runs": len(rows),
                            **({"o": finder_rows(rows, keys, kix)} if ds != "review" else {})})
        vs = sorted({r.get("v") for rows in per[ds].values() for r in rows if r.get("v")})
        models = sorted({(r["m"], r["s"]) for rows in per[ds].values() for r in rows if r.get("m") and r.get("kind") is None})
        srcs = {}
        for rows in per[ds].values():
            for r in rows:
                if r.get("src"):
                    srcs.setdefault(r["src"], set()).add(r.get("wd") or "")
        index["datasets"].append({**d, "questions": entries, "versions": vs, "models": [list(m) for m in models],
                                  "sources": {k: sorted(v) for k, v in srcs.items()}, "drawn": drawn[ds],
                                  **({"fk": keys} if ds != "review" else {})})
        total[ds] = (len(entries), sum(e["runs"] for e in entries), sum(e["texts"] for e in entries))
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")))
    if not quiet:
        print(out, {k: f"{a} questions, {b} runs, {c} with text" for k, (a, b, c) in total.items()}, "sol:", index["sol"])
    return index


if __name__ == "__main__":
    build()
