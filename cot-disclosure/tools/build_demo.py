"""The final results demo for the Nov 24 presentation (Nov 13): one self-contained HTML page, built from the tracked
numbers-only summaries (results/summaries/) and FINDINGS' wording, that opens from file:// with no network request.

  python tools/build_demo.py      # -> docs/demo/index.html (tracked: numbers, ids and paths only)
                                  #    and, when results/demo/examples.json exists (tools/demo_examples.py), also
                                  #    results/demo/index.html (gitignored): the same page plus the example outputs

Two outputs, one ruling (Ritik's session, Nov 13): the brief wants the build to read the local examples "if present"
and wants no text field in the tracked page, so the examples go only into the local page.

Every number on the page comes from one JSON data block in which each number is {"v": value, "src": the summary's
path, "key": the key path to it} (or, for the per-layer swaps that only a loader computes, {"fn": the loader, "where":
its row, "field": the column}; FNS lists those loaders). tests/test_build_demo.py recomputes every one. A summary or a
key that is missing stops the build with a message naming it (MissingNumber; exit 1), and so does a sentence the page
quotes that FINDINGS no longer has (WORDING).

The page: seven sections, one per screen (0 the question; 1 tools vs users; 2 the bare final answer and the title
question; 3 inside the model; 4 between agents; 5 the fixes; 6 the scorecard, the limits and how we worked); keys
<- -> PageUp PageDown Home End, 0-6, i (index), t (theme), n (the numbers), f (full screen); #s0 ... #s6 open a
section. Its CSS and JS are tools/demo_page/ (inlined at build time).
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
ROOT = CODE.parent
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "tools"))
sys.path.insert(0, str(CODE / "progress"))

SUM = CODE / "results" / "summaries"
SUM_REL = "results/summaries"
FINDINGS = ROOT / "docs" / "FINDINGS.md"
OUT = ROOT / "docs" / "demo" / "index.html"
EXAMPLES = CODE / "results" / "demo" / "examples.json"
LOCAL_OUT = CODE / "results" / "demo" / "index.html"
PAGE = CODE / "tools" / "demo_page"


class MissingNumber(Exception):
    """A summary, a key or a quoted sentence the page needs is missing."""


# ---------------------------------------------------------------- reading the summaries, with a source on every number
class Sources:
    def __init__(self, root):
        self.root, self._cache = Path(root), {}

    def load(self, rel):
        if rel not in self._cache:
            p = self.root / rel
            if not p.exists():
                raise MissingNumber(f"missing source: {SUM_REL}/{rel} (not found under {self.root})")
            self._cache[rel] = json.loads(p.read_text())
        return self._cache[rel]

    def get(self, rel, *keys):
        o = self.load(rel)
        for i, k in enumerate(keys):
            try:
                o = o[k]
            except (KeyError, IndexError, TypeError):
                raise MissingNumber(f"missing number: {SUM_REL}/{rel} has no key {list(keys[:i + 1])}") from None
        return o

    def has(self, rel, *keys):
        try:
            self.get(rel, *keys)
            return True
        except MissingNumber:
            return False

    def num(self, rel, *keys):
        x = self.get(rel, *keys)
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise MissingNumber(f"not a number: {SUM_REL}/{rel} key {list(keys)} is {x!r}")
        return {"v": x, "src": f"{SUM_REL}/{rel}", "key": list(keys)}

    def word(self, rel, *keys):
        x = self.get(rel, *keys)
        if not isinstance(x, str):
            raise MissingNumber(f"not a reading: {SUM_REL}/{rel} key {list(keys)} is {x!r}")
        return x

    def kn(self, rel, *keys, wilson="wilson"):
        """X of Y with its 95% Wilson interval: {k, n, lo, hi}."""
        return {"k": self.num(rel, *keys, "k"), "n": self.num(rel, *keys, "n"),
                "lo": self.num(rel, *keys, wilson, 0), "hi": self.num(rel, *keys, wilson, 1)}

    def diff(self, rel, *keys, d="diff", iv="interval"):
        """A difference with its 95% interval (and the summary's reading, when it has one): {d, lo, hi[, reading]}."""
        out = {"d": self.num(rel, *keys, d), "lo": self.num(rel, *keys, iv, 0), "hi": self.num(rel, *keys, iv, 1)}
        e = self.get(rel, *keys)
        if isinstance(e.get("reading"), str):
            out["reading"] = e["reading"]
        elif isinstance(e.get("clear"), bool):
            out["reading"] = "clear" if e["clear"] else "not clear"
        return out

    def ci(self, rel, *keys):
        """A mean with its interval ({mean, low, high}): {m, lo, hi}."""
        return {"m": self.num(rel, *keys, "mean"), "lo": self.num(rel, *keys, "low"), "hi": self.num(rel, *keys, "high")}


# the loaders whose rows the page takes when no summary key holds the number (their own tests check them against
# the summaries); each takes the summaries root
def _a18_rows(root):
    import slide_figures as sf
    a18 = Path(root) / "trackA" / "gpu" / "a18"
    for p in (a18 / "a18_readout.json", a18 / "swap_rows.jsonl", a18 / "a41_readout.json", a18 / "swap_a40_rows.jsonl"):
        if not p.exists():
            raise MissingNumber(f"missing source: {SUM_REL}/{p.relative_to(root)} (slide_figures.a18_rows)")
    return sf.a18_rows(readout=a18 / "a18_readout.json", swap=a18 / "swap_rows.jsonl",
                       b1=Path(root) / "trackA" / "gpu" / "provenance_gen" / "provenance_gen_report.json",
                       a41=a18 / "a41_readout.json", swap_a40=a18 / "swap_a40_rows.jsonl")


FNS = {"slide_figures.a18_rows": _a18_rows}


class Rows:
    def __init__(self, root):
        self.root, self._cache = root, {}

    def num(self, fn, where, field, src):
        rows = self._cache.setdefault(fn, FNS[fn](self.root))
        hits = [r for r in rows if all(r.get(k) == v for k, v in where.items())]
        if len(hits) != 1:
            raise MissingNumber(f"missing number: {fn} has {len(hits)} rows for {where} (from {src})")
        return {"v": hits[0][field], "src": src, "fn": fn, "where": where, "field": field}


# ---------------------------------------------------------------- section 1: tools vs users
TRACKB = (("voyager | qwen3-30b-a3b-thinking-2507 | thinking=None", "Qwen3 30B Thinking", "thinking always", "F15"),
          ("voyager | qwen3-30b-a3b-instruct-2507 | thinking=None", "Qwen3 30B Instruct", "no thinking", "F16"),
          ("voyager | olmo3-7b-think | thinking=None", "Olmo 3 7B Think", "thinking always", "F17"),
          ("sol_vllm | qwen3-8b | thinking=True", "Qwen3-8B", "thinking on", "F29"),
          ("sol_vllm | qwen3-8b | thinking=False", "Qwen3-8B", "thinking off", "F29"))
B20 = (("gemma-4-26b-a4b-it", "Gemma 4 26B-A4B", ("on", "off")), ("nemotron-3-nano-30b-a3b", "Nemotron 3 Nano 30B-A3B",
                                                                  ("on", "off")),
       ("granite-4.2-8b", "Granite 4.2 8B", ("on",)))
CHANNEL = {"tool_real": "its own call", "tool_injected": "inserted tool turn"}
VOYAGER = (("qwen3-30b-a3b-thinking-2507", "Qwen3 30B Thinking"), ("qwen3-30b-a3b-instruct-2507", "Qwen3 30B Instruct"),
           ("olmo3-7b-think", "Olmo 3 7B Think"))


def tool_key(s, rel, *keys):
    for k in ("tool_real", "tool_injected"):
        if s.has(rel, *keys, k):
            return k
    raise MissingNumber(f"missing number: {SUM_REL}/{rel} has neither tool_real nor tool_injected under {list(keys)}")


def gate2_row(s, rel, base, model, setting, group, finding, g2):
    ch = base + ["channels"]
    tc = tool_key(s, rel, *ch)
    return {"model": model, "setting": setting, "group": group, "finding": finding, "channel": CHANNEL[tc],
            "user": s.kn(rel, *ch, "user", "following"), "pasted": s.kn(rel, *ch, "tool_pasted", "following"),
            "tool": s.kn(rel, *ch, tc, "following"), "d_pasted": s.diff(rel, *g2, "tool_pasted"),
            "d_tool": s.diff(rel, *g2, tc)}


def section1(s):
    rows = []
    rep = "trackB/trackB_report.json"
    for key, model, setting, finding in TRACKB:
        base = ["budget_32768", key]
        rows.append(gate2_row(s, rep, base, model, setting, "voyager" if key.startswith("voyager") else "sol", finding,
                              base + ["gate2_tool_minus_user"]))
    for e in ("low", "medium", "high"):
        base = ["per_effort", e]
        rows.append(gate2_row(s, "trackB/b17_report.json", base, "gpt-oss-20b", f"effort {e}", "sol", "F37",
                              base + ["gate2_tool_minus_user"]))
    b20, r2 = "trackB/b20_report.json", []
    for key, model, settings in B20:
        tc = s.word(b20, key, "tool_channel")
        for st in settings:
            base = [key, "settings", st, "budget_32768"]
            row = gate2_row(s, b20, base + ["secondary"], model, f"thinking {st}", "b20", "FB1", base + ["R1_gate2"])
            rows.append(row)
            for ch, form in (("tool_pasted", "pasted block"), (tc, CHANNEL[tc])):
                e = base + ["R2_tool_or_authority", ch]
                r2.append({"model": model, "setting": f"thinking {st}", "form": form, "pasted": ch == "tool_pasted",
                           **s.diff(b20, *e), "tool": s.kn(b20, *e, "a"), "claim": s.kn(b20, *e, "b")})
    dose = []
    for key, model in VOYAGER:
        b24 = "trackB/b24_report.json"
        tc = tool_key(s, b24, key, "c_tool_minus_manual")
        dose.append({"model": model, "tool_channel": CHANNEL[tc],
                     "plain": s.kn(b24, key, "b_classmate_minus_user", "b"),
                     "classmate": s.kn(b24, key, "arms", "user_classmate", "following"),
                     "answer_key": s.kn("trackB/b16_report.json", key, "arms", "user_authority", "following"),
                     "manual": s.kn(b24, key, "arms", "user_manual", "following"),
                     "pasted": s.kn(b24, key, "c_tool_minus_manual", "tool_pasted", "a"),
                     "call": s.kn(b24, key, "c_tool_minus_manual", tc, "a"),
                     "manual_minus_classmate": s.diff(b24, key, "b_manual_minus_classmate"),
                     "manual_minus_key": s.diff(b24, key, "a_wording"),
                     "pasted_minus_manual": s.diff(b24, key, "c_tool_minus_manual", "tool_pasted"),
                     "call_minus_manual": s.diff(b24, key, "c_tool_minus_manual", tc)})
    return {"gate2": rows, "dose": dose, "r2": r2}


# ---------------------------------------------------------------- section 2: the bare final answer, the title question
def section2(s):
    rep = ["budget_32768"]
    tb = "trackB/trackB_report.json"
    bare = []
    for key, model, finding in (("voyager | qwen3-30b-a3b-thinking-2507 | thinking=None", "Qwen3 30B Thinking", "F15"),
                                ("voyager | qwen3-30b-a3b-instruct-2507 | thinking=None", "Qwen3 30B Instruct", "F16"),
                                ("sol_vllm | qwen3-8b | thinking=True", "Qwen3-8B, thinking on", "F29")):
        ch = rep + [key, "channels"]
        bare.append({"model": model, "finding": finding,
                     "after_call": s.kn(tb, *ch, "tool_real", "bare_final_when_called"),
                     "pasted": s.kn(tb, *ch, "tool_pasted", "bare_final")})
    c4 = "trackC/team_c4_summary.json"
    arms = ["solver_replies", "arms"]
    control = {"right": s.kn(c4, *arms, "tool, good lookup", "bare"), "wrong": s.kn(c4, *arms, "tool, bad lookup", "bare"),
               "none": s.kn(c4, *arms, "notool", "bare")}
    th = rep + ["voyager | qwen3-30b-a3b-thinking-2507 | thinking=None", "channels", "tool_real"]
    b15 = "trackB/b15_report.json"
    names = {"thinking_private": s.kn(tb, *th, "mention_private_when_called"),
             "thinking_final": s.kn(tb, *th, "mention_final_when_followed"),
             "b15": {m: {"names": {"with": s.kn(b15, k, "names_tool_after_call", "with"),
                                   "without": s.kn(b15, k, "names_tool_after_call", "without"),
                                   **s.diff(b15, k, "names_tool_after_call")},
                         "following": s.diff(b15, k, "following", "tool_real")}
                     for k, m in (("qwen3-30b-a3b-thinking-2507", "thinking"), ("qwen3-30b-a3b-instruct-2507", "instruct"))}}
    q8 = rep + ["sol_vllm | qwen3-8b | thinking=True", "channels", "tool_real"]
    b17, hl = "trackB/b17_report.json", ["primary", "high - low"]
    nem = ["nemotron-3-nano-30b-a3b", "thinking_on_minus_off", "budget_32768", "R3b_bare_after_call"]
    title = {"f29": {"private": s.kn(tb, *q8, "mention_private_when_called"),
                     "final": s.kn(tb, *q8, "mention_final_when_followed"),
                     "calls_on": s.kn(tb, *q8, "tool_call_rate"),
                     "calls_off": s.kn(tb, "budget_32768", "sol_vllm | qwen3-8b | thinking=False", "channels",
                                       "tool_real", "tool_call_rate")},
             "f37": {m: {**s.diff(b17, *hl, m), "high": s.kn(b17, *hl, m, "with"), "low": s.kn(b17, *hl, m, "without")}
                     for m in ("following_tool_real", "bare_after_call")},
             "f37_tokens": {e: s.num(b17, "per_effort", e, "median_output_tokens") for e in ("low", "high")},
             "fb1": {**s.diff("trackB/b20_report.json", *nem), "on": s.kn("trackB/b20_report.json", *nem, "a"),
                     "off": s.kn("trackB/b20_report.json", *nem, "b")}}
    return {"bare": bare, "control": control, "names": names, "title": title}


# ---------------------------------------------------------------- section 3: inside the model
SWAPS = (("every", "LoRA, every layer", "A40, every layer"), ("before", "base + LoRA's 0-14", "base + A40's 0-14"),
         ("readout", "base + LoRA's 15, 19, 23", "base + A40's 15, 19, 23"),
         ("through", "base + LoRA's 0-23", "base + A40's 0-23"), ("after", "base + LoRA's 24-31", "base + A40's 24-31"))


def section3(s, rows):
    t2, sa = "trackA/step10_handoff.json", "trackA/setA/step10_handoff.json"
    allc = ["handoff", "by_cut_type", "ii", "all"]
    n_layers = len(s.get(t2, *allc, "drop_by_layer"))
    layers = [s.ci(t2, *allc, "drop_by_layer", i) for i in range(n_layers)]
    full = [s.num(t2, "handoff", "full_attention_layers", i) for i in range(len(s.get(t2, "handoff", "full_attention_layers")))]
    readout = [s.num(t2, "handoff", "readout_layers", i) for i in range(len(s.get(t2, "handoff", "readout_layers")))]
    q = "trackA/qwen8b_mech/qwen8b_readout.json"
    share = [{"what": "Olmo 3 7B Think, Test 2", "finding": "F11", **s.ci(t2, *allc, "drop_share_readout"),
              "questions": s.num(t2, *allc, "questions"), "cuts": s.num(t2, *allc, "cuts"),
              "at": [s.num(t2, "handoff", "readout_layers", i) for i in range(3)]},
             {"what": "Olmo 3 7B Think, set A (new questions)", "finding": "F26", **s.ci(sa, *allc, "drop_share_readout"),
              "questions": s.num(sa, *allc, "questions"), "cuts": s.num(sa, *allc, "cuts"),
              "at": [s.num(sa, "handoff", "readout_layers", i) for i in range(3)]},
             {"what": "Qwen3-8B, MMLU-Pro (the test)", "finding": "F36",
              **s.ci(q, "replication", "share_at_layers"), "questions": s.num(q, "replication", "share_at_layers",
                                                                               "questions"),
              "cuts": s.num(q, "replication", "usable_cuts"),
              "at": [s.num(q, "replication", "layers", i) for i in range(3)],
              "threshold": s.num(q, "replication", "threshold"), "reading": s.word(q, "replication", "verdict")}]
    h = "trackA/setA/step9_fixed_heads.json"
    hk = ["mean over the three heads", "followed - resisted (all channels)", "hint - control"]
    heads = {"d": s.num(h, *hk, "difference"), "lo": s.num(h, *hk, "ci95", 0), "hi": s.num(h, *hk, "ci95", 1),
             "questions": s.num(h, *hk, "questions_in_both"), "reading": s.word(h, "reading")}
    a18, a41 = "trackA/gpu/a18/a18_readout.json", "trackA/gpu/a18/a41_readout.json"
    src = f"{SUM_REL}/trackA/gpu/a18/swap_rows.jsonl"
    swaps = []
    for part, lora_arm, a40_arm in SWAPS:
        if part == "every":
            lora = s.ci(a18, "primary", "reduction_lora")
            a40 = s.ci(a41, "primary", "reduction_a40")
        else:
            lora = {m: rows.num("slide_figures.a18_rows", {"panel": "a", "arm": lora_arm}, f, src)
                    for m, f in (("m", "value"), ("lo", "low"), ("hi", "high"))}
            a40 = s.ci(a41, "layer R (reported, no decision)", part)
        swaps.append({"part": part, "lora": lora, "a40": a40})
    swap = {"rows": swaps, "cases": s.num(a18, "primary", "usable"), "questions": s.num(a18, "primary", "questions"),
            "lora_reading": s.word(a18, "primary", "reading"), "a40_reading": s.word(a41, "primary", "reading"),
            "a40_where": s.word(a41, "primary", "where"),
            "a40_minus_lora": {**s.ci(a41, "against LoRA", "difference"), "reading": s.word(a41, "against LoRA", "reading")}}
    return {"layers": layers, "full": full, "readout": readout, "share": share, "heads": heads, "swap": swap}


# ---------------------------------------------------------------- section 4: between agents
REVIEWERS = (("team_c4", "olmo3-32b-instruct", "Olmo 3.1 32B Instruct", "Olmo", "C4", "F18"),
             ("team_c11", "olmo3-7b-instruct", "Olmo 3 7B Instruct", "Olmo", "C11", "F22"),
             ("team_c4", "qwen3-30b-a3b-instruct-2507", "Qwen3 30B Instruct", "Qwen3", "C4", "F18"),
             ("team_c11", "qwen3-30b-a3b-thinking-2507", "Qwen3 30B Thinking", "Qwen3", "C11", "F22"),
             ("team_c13_granite", "granite-4.1-30b", "Granite 4.1 30B", "Granite", "C13", "F30"),
             ("team_c13_mistral", "mistral-small-3.2-24b", "Mistral Small 3.2 24B", "Mistral", "C13", "F30"))
VIEWS = ("answer_only", "plus_private", "plus_tool_log")
C15_VIEWS = ("answer_only", "plus_tool_log", "plus_tool_log_redacted")
CUES = (("c16_summary.json", "main", "C16", "F31", "the solver's answer names the tool − same-day control"),
        ("c17_summary.json", "b_names_minus_own", "C17", "F33", "+ a sentence naming the tool − + one naming own working"),
        ("c18_summary.json", "main_stripped_minus_unchanged", "C18", "F34",
         "the solver's tool-citing sentences removed − unchanged"))
RV_NAMES = {"olmo3-32b-instruct": "Olmo 3.1 32B Instruct", "qwen3-30b-a3b-instruct-2507": "Qwen3 30B Instruct"}


def section4(s):
    reviewers = []
    for log, m, name, family, run, finding in REVIEWERS:
        rel = f"trackC/{log}_summary.json"
        views = {v: s.kn(rel, "by_team_model_variant", f"tool | {m} | {v}", "reviewer_alone", "corrects_wrong_solver")
                 for v in VIEWS}
        reviewers.append({"name": name, "family": family, "run": run, "finding": finding, **views,
                          "log_minus_answer": s.diff(rel, "reviewer_vs_answer_only",
                                                     f"corrects_wrong_bad_lookups | {m} | plus_tool_log")})
    c15 = []
    for m in RV_NAMES:
        rel = "trackC/team_c15_summary.json"
        c15.append({"name": RV_NAMES[m], "run": "C15", "finding": "F24",
                    **{v: s.kn(rel, "by_team_model_variant", f"tool | {m} | {v}", "reviewer_alone", "corrects_wrong_solver")
                       for v in C15_VIEWS},
                    "log_minus_answer": {**s.diff("trackC/c15_summary.json", "a_replication", m),
                                         "reading": s.word("trackC/c15_summary.json", "a_replication", m, "rule")}})
    cf = ["c_frozen_rule", "olmo3-32b-instruct", "plus_tool_log"]
    checker = {"caught": s.kn("trackC/c15_summary.json", *cf, "bad_lookups", "checker_pipeline_caught"),
               "false_alarms": s.kn("trackC/c15_summary.json", *cf, "good_lookups", "checker_pipeline_false_alarms"),
               "floor": s.kn("trackC/c15_summary.json", "checker_flag_rate", "notool"),
               "shipped": s.kn("trackC/c15_summary.json", *cf, "bad_lookups", "checker_pipeline_shipped_wrong")}
    cues = []
    for fname, key, exp, finding, what in CUES:
        rel = f"trackC/{fname}"
        for m, name in RV_NAMES.items():
            cues.append({"experiment": exp, "finding": finding, "what": what, "reviewer": name, **s.diff(rel, key, m),
                         "items": s.num(rel, key, m, "items"), "a_k": s.num(rel, key, m, "variant_k"),
                         "b_k": s.num(rel, key, m, "answer_only_k"), "n": s.num(rel, key, m, "variant_n")})
    labels = {"wrapper": {**s.diff("trackA/gpu/a39/a39_e2.json", "r4", "following"),
                          "reading": s.word("trackA/gpu/a39/a39_e2.json", "r4", "reading")},
              "tag": [{"reviewer": name, **s.diff("trackC/c20_summary.json", "readings", m, "1_tag_minus_blind_catches"),
                       "a_k": s.num("trackC/c20_summary.json", "readings", m, "1_tag_minus_blind_catches", "variant_k"),
                       "b_k": s.num("trackC/c20_summary.json", "readings", m, "1_tag_minus_blind_catches", "answer_only_k"),
                       "n": s.num("trackC/c20_summary.json", "readings", m, "1_tag_minus_blind_catches", "items")}
                      for m, name in RV_NAMES.items()]}
    return {"reviewers": reviewers, "c15": c15, "checker": checker, "cues": cues, "labels": labels}


# ---------------------------------------------------------------- section 5: the fixes
SYSTEMS = ("base", "prompt_only", "lora", "lora_note", "wrap", "wrap_note", "lora_wrap", "a40", "a40_note")
B1 = (("B1", "trackA/gpu/provenance_gen/provenance_gen_report.json", "the held-out 30"),
      ("B1R2", "trackA/gpu/b1r2/provenance_gen_report.json", "E2's 120 questions"))
B1_MEASURES = (("following", "wrong_hint_following | tool_injected"),
               ("acceptance", "correct_hint_acceptance | tool_injected"), ("accuracy", "no_hint_accuracy | all"))


def section5(s):
    t = "trackA/gpu/a39/tradeoff_e2.json"
    systems = {}
    for sy in SYSTEMS:
        b = ["systems", sy]
        systems[sy] = {"following": s.kn(t, *b, "following", "pooled"), "acceptance": s.kn(t, *b, "acceptance", "pooled"),
                       "following_ins": s.kn(t, *b, "following", "inserted"),
                       "acceptance_ins": s.kn(t, *b, "acceptance", "inserted"),
                       "a_C": s.kn(t, *b, "tool", "a_C"), "a_W": s.kn(t, *b, "tool", "a_W"),
                       "keyword": s.kn(t, *b, "disclosure_when_following", "pooled"),
                       "diluted": "note" in s.get(t, *b)}
    crossings = {}
    for sy in ("a40", "lora"):
        e = ["crossings", "answered", sy]
        c = {"status": s.word(t, *e, "status"), "flipped": s.num(t, *e, "flipped"), "resamples": s.num(t, *e, "resamples")}
        if s.get(t, *e, "p_star") is not None:
            c.update({"p": s.num(t, *e, "p_star"), "lo": s.num(t, *e, "interval", 0), "hi": s.num(t, *e, "interval", 1),
                      "ahead": s.word(t, *e, "ahead")})
        crossings[sy] = c
    keyword_vs = {sy: s.diff(t, "disclosure_vs_prompt_only", sy) for sy in ("lora", "a40")}
    lr = "trackA/labels/l6_report.json"
    l6 = {"lora": s.kn(lr, "discloses", "lora"), "instruction": s.kn(lr, "discloses", "prompt_only"),
          "comparison": {**s.diff(lr, "comparison"), "questions": s.num(lr, "comparison", "questions")},
          "kappa": s.num(lr, "kappa", "overall", "kappa"), "agreement": s.num(lr, "kappa", "overall", "agreement"),
          "rows": s.num(lr, "kappa", "overall", "rows"), "rejects_lora": s.kn(lr, "rejects_hint", "lora"),
          "keyword_agrees": {sy: {"k": s.num(lr, "keyword_agrees", sy, "k"), "n": s.num(lr, "keyword_agrees", sy, "n")}
                             for sy in ("lora", "prompt_only")},
          "guess_trained": {"yes": s.num(lr, "guess_trained", "lora", "yes"), "n": s.num(lr, "guess_trained", "lora", "n")}}
    b1r2 = []
    for study, rel, qset in B1:
        res = s.load(rel)
        names = [k for k, e in res.get("systems", {}).items() if e.get("span") == "deployable"
                 and e.get("alpha") not in (None, 1.0)]
        if not names:
            raise MissingNumber(f"missing number: {SUM_REL}/{rel} has no deployable span system")
        sy, base = names[0], s.word(rel, "base")
        row = {"study": study, "set": qset, "alpha": s.num(rel, "systems", sy, "alpha"),
               "runs": s.num(rel, "systems", sy, "runs")}
        for m, key in B1_MEASURES:
            row[m] = {"k": s.num(rel, "systems", sy, key, "k"), "n": s.num(rel, "systems", sy, key, "n"),
                      "base_k": s.num(rel, "systems", base, key, "k"), "base_n": s.num(rel, "systems", base, key, "n"),
                      "d": s.num(rel, "systems", sy, key, "minus_alpha1", "diff"),
                      "lo": s.num(rel, "systems", sy, key, "minus_alpha1", "interval", 0),
                      "hi": s.num(rel, "systems", sy, key, "minus_alpha1", "interval", 1),
                      "questions": s.num(rel, "systems", sy, key, "minus_alpha1", "questions")}
        from finetune.gpu import provenance_job as pj
        row["reading"] = pj.b1_verdict(res, "deployable", "tool_injected")["reading"]
        b1r2.append(row)
    return {"systems": systems, "crossings": crossings, "keyword_vs": keyword_vs, "l6": l6, "b1r2": b1r2}


def collect(summaries=SUM):
    s, rows = Sources(summaries), Rows(Path(summaries))
    return {"s1": section1(s), "s2": section2(s), "s3": section3(s, rows), "s4": section4(s), "s5": section5(s),
            "s6": {"kappa_l6": s.num("trackA/labels/l6_report.json", "kappa", "overall", "kappa")}}


# ---------------------------------------------------------------- FINDINGS' wording
WORDING = (  # every sentence the page quotes, as FINDINGS has it (markdown emphasis and line breaks aside)
    "Tools sway models more than users.",
    "After a tool call, the answer stops explaining.",
    "Downstream, a reviewer shown the tool's output defers to it.",
    "So the title question is answered mixed",
    "with thinking on, Qwen3-8B names the tool in its private reasoning but not in its final answer (F29); in "
    "gpt-oss-20b, more reasoning effort changes nothing (F37); in Nemotron 3 Nano, the answer after the inserted tool "
    "turn is less bare with thinking on",
    "Training made the answer more candid about a hint it followed, in hand labels, without making it follow less.",
    "LoRA's trained opener names the hint (F28); LoRA's following shows no difference from the instruction (F44); one "
    "model, E2 only, 42 rows a system, the final answer only; the sheet not blind in practice, with J-opus (blind to "
    "systems) agreeing on 82 of 84 rows.",
    "\"ignores tools\" again",
    "B1's verdict on the 30 stays primary",
    "A40 gives more correct answers than the instruction only when fewer than 0.36 [0.22, 0.50] of the tool's answers "
    "are correct.",
    "The stricter bar, beating the one-line instruction on following at no cost to correct hints: met by no fix.",
    "provenance labels alone don't help",
    "independent verification does",
    "Scorecard against the original plan",
)


def normal(t):
    return re.sub(r"\s+", " ", t.replace("**", "").replace("*", "")).strip().lower()


def check_wording(findings):
    p = Path(findings)
    if not p.exists():
        raise MissingNumber(f"missing source: {p} (FINDINGS, for the page's wording)")
    text = normal(p.read_text())
    gone = [w for w in WORDING if normal(w) not in text]
    if gone:
        raise MissingNumber(f"FINDINGS ({p}) no longer has the wording the page quotes: {gone}")
    return p.read_text()


def md_inline(t):
    """FINDINGS' markdown, inline: escaped, **bold** and *italic* kept, links to their text."""
    t = html.escape(t, quote=False)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)


def scorecard(findings_text):
    """FINDINGS' story item 7, its bullets as written: [(lead, rest)] in HTML."""
    lines = findings_text.splitlines()
    try:
        start = next(i for i, x in enumerate(lines) if x.startswith("7. **Scorecard against the original plan"))
    except StopIteration:
        raise MissingNumber("FINDINGS has no story item 7 (\"7. **Scorecard against the original plan\")") from None
    bullets, cur = [], None
    for x in lines[start + 1:]:
        if not x.startswith("   ") or not x.strip():
            break
        if x.startswith("   - "):
            cur = [x[5:].strip()]
            bullets.append(cur)
        elif cur is not None:
            cur.append(x.strip())
    if len(bullets) < 5:
        raise MissingNumber(f"FINDINGS' scorecard (item 7) has {len(bullets)} bullets; expected its 7")
    out = []
    for b in bullets:
        h = md_inline(" ".join(b))
        m = re.match(r"\s*<strong>(.+?)</strong>\s*(.*)$", h, re.S)
        out.append((m.group(1), m.group(2)) if m else ("", h))
    return out


# ---------------------------------------------------------------- the page
def script_json(obj):
    """JSON safe inside a <script> element (no "</", "<!--" or "]]>" can close or confuse it)."""
    return (json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e")
            .replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def render(data, findings_text, examples=None):
    tpl = (PAGE / "template.html").read_text()
    css, js = (PAGE / "demo.css").read_text(), (PAGE / "demo.js").read_text()
    card = "\n".join(f'<li><p class="sc-lead">{lead}</p><p class="sc-rest">{rest}</p></li>'
                     for lead, rest in scorecard(findings_text))
    local = examples is not None
    parts = {"CSS": css, "JS": js, "DATA": script_json(data), "SCORECARD": card,
             "EXAMPLES_DATA": (f'<script type="application/json" id="demo-examples">{script_json(examples)}</script>'
                               if local else ""),
             "EXAMPLES_SLIDE": ((PAGE / "examples.html").read_text() if local else ""),
             "MODE": "local" if local else "tracked"}
    out = tpl
    for k, v in parts.items():
        out = out.replace(f"<!--{k}-->", v)
    left = re.findall(r"<!--[A-Z_]+-->", out)
    if left:
        raise MissingNumber(f"the template has unfilled parts: {left}")
    return out


def build(summaries=SUM, findings=FINDINGS, out=OUT, examples=EXAMPLES, local_out=LOCAL_OUT):
    """Write the tracked page (numbers only) and, when the examples file exists, the local page with them."""
    text = check_wording(findings)
    data = collect(summaries)
    page = render(data, text)
    written = []
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    written.append(out)
    if examples and Path(examples).exists():
        ex = json.loads(Path(examples).read_text())
        local = Path(local_out)
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text(render(data, text, ex))
        written.append(local)
    return written


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--summaries", default=str(SUM))
    ap.add_argument("--findings", default=str(FINDINGS))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--examples", default=str(EXAMPLES))
    ap.add_argument("--local-out", default=str(LOCAL_OUT))
    a = ap.parse_args(argv)
    try:
        written = build(a.summaries, a.findings, a.out, a.examples, a.local_out)
    except MissingNumber as e:
        print(f"build_demo: {e}", file=sys.stderr)
        raise SystemExit(1)
    for p in written:
        print(p)


if __name__ == "__main__":
    main()
