"""Track C, C24: the report's tables for C19, C25, C20 and C26 (no calls).

  python agents/trackc_tables.py        # -> docs/trackC/tables/{trackC_experiments,trackC_pipelines,at_a_glance_FC}.{md,csv}

Every number comes from the tracked numbers-only summaries in results/summaries/trackC/ (c19, c25, c20, c26); nothing is
read from gitignored data. Three tables, in the shapes the paper already uses (docs/paper/ is outside Track C's
allowlist, so they are written under docs/trackC/tables/ and Ritik places them):
  trackC_experiments   one row per comparison, as the supplement's cue_experiments table: a and b (X of Y), items,
                       a − b in points with its 95% bootstrap clustered by item, the pre-registered reading, and
                       whether the row decided anything ("pre-registered, main", "pre-registered", or "no decision");
  trackC_pipelines     C20's four pipelines per reviewer (caught, false alarms, shipped wrong, tokens a case), under
                       the "ship" rule and, no decision, as a flag;
  at_a_glance_FC       FC1–FC4 in results_at_a_glance's columns (finding, track, claim, key numbers, status, figure).
"""
import csv
import json
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
SUM = CODE / "results" / "summaries" / "trackC"
OUT = CODE.parent / "docs" / "trackC" / "tables"
OLMO, QWEN = "olmo3-32b-instruct", "qwen3-30b-a3b-instruct-2507"
NAME = {OLMO: "Olmo 3.1 32B Instruct", QWEN: "Qwen3 30B Instruct"}
SOLVER = "the solver (Qwen3 30B Thinking)"
FIG = {"c19": "docs/trackC/figures/c19_authority.png", "c25": "docs/trackC/figures/c25_hops.png",
       "c20": "docs/trackC/figures/pipeline_vs_model.png", "c26": "docs/trackC/figures/pipeline_vs_model.png"}
EXPERIMENT_COLUMNS = ["experiment", "comparison", "measure", "reviewer", "variant", "a", "b", "items", "a − b",
                      "reading", "decision"]
PIPELINE_COLUMNS = ["experiment", "rule", "pipeline", "reviewer", "caught", "false alarms", "shipped wrong",
                    "tokens a case"]
GLANCE_COLUMNS = ["finding", "track", "claim", "key numbers", "status", "figure"]


def pts(x):
    """A difference in points, signed, with a true minus sign."""
    v = round(x * 100)
    return f"+{v}" if v > 0 else f"−{-v}" if v < 0 else "+0"


def diff(e):
    """'+8 [−2, +19]' from a paired entry, or '' if it has none."""
    if e is None or e.get("diff") is None:
        return ""
    return f"{pts(e['diff'])} [{pts(e['interval'][0])}, {pts(e['interval'][1])}]"


def count(e):
    return f"{e['k']} of {e['n']}"


def items(e):
    v = e.get("items")
    return f"{v[0]} and {v[1]}" if isinstance(v, list) else ("" if v is None else str(v))


def load(name, path=None):
    return json.loads(Path(path or SUM / f"{name}_summary.json").read_text())


def _row(exp, comparison, measure, reviewer, variant, a, b, its, d, reading, decision):
    return dict(zip(EXPERIMENT_COLUMNS, [exp, comparison, measure, reviewer, variant, a, b, its, d, reading, decision]))


def _paired(exp, comparison, measure, reviewer, variant, e, decision, reading=None, a=None, b=None):
    a = a if a is not None else (f"{e['variant_k']} of {e['variant_n']}" if e.get("variant_k") is not None else "")
    b = b if b is not None else (f"{e['answer_only_k']} of {e['answer_only_n']}" if e.get("answer_only_k") is not None else "")
    return _row(exp, comparison, measure, reviewer, variant, a, b, items(e), diff(e),
                reading if reading is not None else (e.get("reading") or e.get("rule") or ""), decision)


def experiment_rows(c19=None, c25=None, c20=None, c26=None):
    """The comparisons table's rows, in the summaries' order."""
    s19, s25, s20, s26 = load("c19", c19), load("c25", c25), load("c20", c20), load("c26", c26)
    rows = []
    # C19
    corr, expl = "corrects a wrong answer", "+ explanation"
    for m in (OLMO, QWEN):
        e = s19["main_key_minus_own"][m]
        rows.append(_paired("C19", "answer-key sentence − own-working sentence", corr, NAME[m], expl, e,
                            "pre-registered, main (H34)", reading=f"{e['reading']}; H34: {s19['h34'][m]}"))
    for key, label in (("key_minus_unchanged", "answer-key sentence − unchanged (C16's control)"),
                       ("key_minus_c17_names", "answer-key sentence − C17's names_tool"),
                       ("own_minus_c17_own", "own-working sentence − C17's own_working"),
                       ("own_minus_unchanged", "own-working sentence − unchanged (C16's control)")):
        for m in (OLMO, QWEN):
            rows.append(_paired("C19", label, corr, NAME[m], expl, s19["references"][key][m],
                                "no decision (cross-day reference)"))
    for m in (OLMO, QWEN):
        rows.append(_paired("C19", "answer-key sentence − own-working sentence, bare answers only", corr, NAME[m], expl,
                            s19["main_bare_answers_only"][m], "no decision"))
    for m in (OLMO, QWEN):
        rows.append(_paired("C19", "answer-key sentence − own-working sentence", "keeps a right answer (good lookups)",
                            NAME[m], expl, s19["side_effect_keeps"][m], "no decision (side effect)", reading=""))
    # C25
    names = "names the tool"
    for scope, key in (("bad lookups", "source_bad_lookups"), ("good lookups", "source_good_lookups")):
        src = s25[key]
        dec = "pre-registered (kept / lost / mixed)" if scope == "bad lookups" else "no decision"
        rows.append(_row("C25", f"hop 1, the solver's final answer ({scope})", names, SOLVER, "", count(src["hop1_solver"]),
                         "", src["hop1_solver"]["n"], "", "", "no decision (F15's baseline)"))
        for hop, label in (("hop2_plain", "hop 2, the plain note"), ("hop2_keep", "hop 2, the keep note")):
            rows.append(_row("C25", f"{label} ({scope})", names, "the writer (Qwen3 30B Instruct)", "", count(src[hop]),
                             "", src[hop]["n"], "", src[hop].get("reading", ""), dec))
        rows.append(_paired("C25", f"plain note − hop 1 ({scope})", names, "the writer (Qwen3 30B Instruct)", "",
                            src["plain_minus_hop1"], "no decision", a=count(src["hop2_plain"]), b=count(src["hop1_solver"])))
        rows.append(_paired("C25", f"keep note − plain note ({scope})", names, "the writer (Qwen3 30B Instruct)", "",
                            src["keep_minus_plain"], "no decision", a=count(src["hop2_keep"]), b=count(src["hop2_plain"])))
    acc, note = "accepts the solver's wrong letter", "the note in place of the answer, + explanation"
    for m in (OLMO, QWEN):
        d = s25["deciders"][m]
        e = d["M1_stripped_minus_keep"]
        rows.append(_paired("C25", "M1: keep note with its tool sentences stripped − keep note", acc, NAME[m], note, e,
                            "pre-registered, main", reading=f"{e['reading']}; source gone: {e.get('source_gone', '')}"))
        rows.append(_paired("C25", "M2: plain note − keep note", acc, NAME[m], note, d["M2_plain_minus_keep"],
                            "pre-registered"))
        rows.append(_paired("C25", "M1: stripped − keep", corr, NAME[m], note, d["corrects"]["M1"], "no decision", reading=""))
        rows.append(_paired("C25", "M2: plain − keep", corr, NAME[m], note, d["corrects"]["M2"], "no decision", reading=""))
        for key, e in d["vs_references"].items():
            rows.append(_paired("C25", key.replace("_", " ").replace("c15 answer only", "C15's answer_only")
                                + " (cross-day)", acc, NAME[m], note, e, "no decision (cross-day reference)", reading=""))
        rows.append(_paired("C25", "plain notes: named the tool − did not (unpaired)", acc, NAME[m], note,
                            d["plain_named_minus_unnamed_unpaired"], "no decision (unpaired)", reading="", a="", b=""))
        for key, label in (("M1", "M1: stripped − keep"), ("M2", "M2: plain − keep")):
            rows.append(_paired("C25", label, "keeps a right answer (good lookups)", NAME[m], note,
                                d["side_effect_keeps"][key], "no decision (side effect)", reading=""))
    # C20
    pipes, tag = s20["pipelines"], "the answer + the pipeline's tag"
    for m in (OLMO, QWEN):
        r = s20["readings"][m]
        rows.append(_paired("C20", "(b) tag − (a) blind", "catches the wrong solver answer", NAME[m], tag,
                            r["1_tag_minus_blind_catches"], "pre-registered, main (the tag works?)"))
        rows.append(_paired("C20", "(b) tag − (a) blind", "false alarms (right solver answer changed)", NAME[m], tag,
                            r["2_tag_minus_blind_false_alarms"], "pre-registered",
                            a=count(pipes[f"b_tag | {m}"]["false_alarms"]), b=count(pipes[f"a_blind | {m}"]["false_alarms"])))
        v = r["3_tag_vs_checker"]
        rows.append(_paired("C20", "(b) tag − (d) checker", "catches the wrong solver answer", NAME[m], tag, v["catches"],
                            "pre-registered (matches the checker?)", reading=v["reading"],
                            a=count(pipes[f"b_tag | {m}"]["caught"]), b=count(pipes["d_checker"]["caught"])))
        rows.append(_paired("C20", "(b) tag − (d) checker", "false alarms (right solver answer changed)", NAME[m], tag,
                            v["false_alarms"], "pre-registered (matches the checker?)", reading=v["reading"],
                            a=count(pipes[f"b_tag | {m}"]["false_alarms"]), b=count(pipes["d_checker"]["false_alarms"])))
        rows.append(_paired("C20", "(b) tag − (c) the solver's own disclosure (C16), items wrong in both",
                            "catches the wrong solver answer", NAME[m], tag, r["4_tag_minus_disclosure_catches"],
                            "pre-registered (pipeline vs model)"))
    # C26
    sv = s26["solver"]
    rows.append(_paired("C26", "R1: retrieved passage (C26) − answer key (C15)", "follows the bad lookup", SOLVER, "",
                        sv["R1_following_c26_minus_c15"], "pre-registered"))
    rows.append(_paired("C26", "R1b: retrieved passage (C26) − the no-tool floor", "follows the bad lookup", SOLVER, "",
                        sv["R1b_following_minus_notool_floor"], "pre-registered", a=count(sv["following"]["c26"]),
                        b="0 of 55"))
    rows.append(_paired("C26", "retrieved passage (C26) − answer key (C15)", "right on good lookups", SOLVER, "",
                        sv["good_lookups_right"]["c26_minus_c15"], "no decision", reading="",
                        a=count(sv["good_lookups_right"]["c26"]), b=count(sv["good_lookups_right"]["c15"])))
    for key, label in (("final_names_source", "the final answer names its source"), ("final_bare", "the final answer is bare")):
        rows.append(_row("C26", "retrieved passage (C26) vs answer key (C15)", label, SOLVER, "", count(sv[key]["c26"]),
                         count(sv[key]["c15"]), sv[key]["c26"]["n"], "", "", "no decision"))
    for m in (OLMO, QWEN):
        rv = s26["reviewers"][m]
        rows.append(_paired("C26", "R2: + tool log − answer only (C26's bad lookups)", corr, NAME[m], "+ tool log",
                            rv["R2_plus_tool_log_minus_answer_only"], "pre-registered, main"))
        rows.append(_paired("C26", "+ tool log: retrieved passage (C26) − answer key (C15), items wrong in both", corr,
                            NAME[m], "+ tool log", rv["plus_tool_log_c26_minus_c15"], "no decision", reading=""))
    ck = s26["checker"]
    rows.append(_row("C26", "the checker flags", "flagged", "the checker (Qwen3 30B Thinking, no tool)", "",
                     count(ck["flags_c26"]), "", ck["flags_c26"]["n"], "", "", "no decision"))
    rows.append(_row("C26", "the checker's letter equals C15's (the same call)", "same letter",
                     "the checker (Qwen3 30B Thinking, no tool)", "", count(ck["same_letter_as_c15"]), "",
                     ck["same_letter_as_c15"]["n"], "", "", "no decision (reproduction check)"))
    return rows


def pipeline_rows(c20=None):
    """C20's pipelines, under the ship rule and as a flag."""
    s20 = load("c20", c20)
    rows = []
    for rule, block in (("ship: the reviewer's letter ships", s20["pipelines"]),
                        ("flag: a letter other than the solver's escalates (no decision)", s20["as_a_flag"])):
        for key, e in block.items():
            pipe, _, model = key.partition(" | ")
            label = {"a_blind": "(a) blind", "b_tag": "(b) tag", "c_disclosure": "(c) the solver's disclosure",
                     "d_checker": "(d) the checker"}[pipe]
            rows.append(dict(zip(PIPELINE_COLUMNS, [
                "C20", rule, label, NAME.get(model, "—"), count(e["caught"]), count(e["false_alarms"]),
                count(e["shipped_wrong"]), f"{e['tokens_per_case']:,.0f}"])))
    return rows


def glance_rows(c19=None, c25=None, c20=None, c26=None):
    """FC1–FC4 as results_at_a_glance rows: the numbers from the summaries, the claims from FINDINGS_C's headings."""
    s19, s25, s20, s26 = load("c19", c19), load("c25", c25), load("c20", c20), load("c26", c26)
    o19, q19 = s19["main_key_minus_own"][OLMO], s19["main_key_minus_own"][QWEN]
    src, o25, q25 = s25["source_bad_lookups"], s25["deciders"][OLMO], s25["deciders"][QWEN]
    o20, q20 = s20["readings"][OLMO], s20["readings"][QWEN]
    sv, o26, q26 = s26["solver"], s26["reviewers"][OLMO], s26["reviewers"][QWEN]
    o20d, o20c = o20["4_tag_minus_disclosure_catches"], o20["3_tag_vs_checker"]["catches"]
    rows = [
        ["FC1", "C", "C19: an answer-key claim lowers the Olmo reviewer's corrections against the same claim about own "
                     "working; the pre-registered rule reads it as unclear",
         f"Olmo {o19['variant_k']} vs {o19['answer_only_k']} of {o19['items']}, {diff(o19)}; Qwen3 {q19['variant_k']} vs "
         f"{q19['answer_only_k']} of {q19['items']}, {diff(q19)}",
         f"Olmo: {o19['reading']} (H34 {s19['h34'][OLMO]}); tentative: the direction; Qwen3: {q19['reading']}", FIG["c19"]],
        ["FC2", "C", "C25: a writer agent puts the tool back as the source; with it stripped from the keep note, the Olmo "
                     "decider accepts the wrong answer less, unclear by the rule",
         f"names the tool: solver {count(src['hop1_solver'])}, plain note {count(src['hop2_plain'])} ({src['hop2_plain']['reading']}), "
         f"keep note {count(src['hop2_keep'])} ({src['hop2_keep']['reading']}); accepts the wrong letter, stripped − keep: Olmo "
         f"{o25['M1_stripped_minus_keep']['variant_k']} vs {o25['M1_stripped_minus_keep']['answer_only_k']} of 53, "
         f"{diff(o25['M1_stripped_minus_keep'])}; Qwen3 {diff(q25['M1_stripped_minus_keep'])}; spot check 15 of 20",
         f"confirmed: the source comes back at hop 2; Olmo M1: {o25['M1_stripped_minus_keep']['reading']}; tentative: the "
         f"direction (fewer acceptances); Qwen3: {q25['M1_stripped_minus_keep']['reading']}", FIG["c25"]],
        ["FC3", "C", "C20: a pipeline tag naming the tool's letter as unverified gives the blind reviewer no change on "
                     "catches, costs no false alarms, falls short of the checker, and beats the solver's own disclosure",
         f"tag − blind, catches: Olmo {o20['1_tag_minus_blind_catches']['variant_k']} vs "
         f"{o20['1_tag_minus_blind_catches']['answer_only_k']} of 53, {diff(o20['1_tag_minus_blind_catches'])}; Qwen3 "
         f"{diff(q20['1_tag_minus_blind_catches'])}; false alarms Olmo {diff(o20['2_tag_minus_blind_false_alarms'])}; tag − "
         f"checker, catches Olmo {diff(o20c)}; tag − disclosure, catches Olmo {diff(o20d)}, Qwen3 "
         f"{diff(q20['4_tag_minus_disclosure_catches'])}",
         f"not supported: the tag works ({o20['1_tag_minus_blind_catches']['reading']}); confirmed: "
         f"{o20['3_tag_vs_checker']['reading']}; {o20d['reading']} over the solver's disclosure (Olmo)", FIG["c20"]],
        ["FC4", "C", "C26: with a retrieved passage in place of the answer key, the solver follows a bad lookup less but "
                     "above the floor, and the Olmo reviewer still defers to the tool log",
         f"follows: {count(sv['following']['c26'])} vs {count(sv['following']['c15'])}, {diff(sv['R1_following_c26_minus_c15'])}; "
         f"vs the floor {diff(sv['R1b_following_minus_notool_floor'])}; + tool log − answer only: Olmo "
         f"{o26['R2_plus_tool_log_minus_answer_only']['variant_k']} vs {o26['R2_plus_tool_log_minus_answer_only']['answer_only_k']} "
         f"of {o26['R2_plus_tool_log_minus_answer_only']['items']}, {diff(o26['R2_plus_tool_log_minus_answer_only'])}; Qwen3 "
         f"{diff(q26['R2_plus_tool_log_minus_answer_only'])}",
         f"confirmed: {sv['R1_following_c26_minus_c15']['reading']}; {sv['R1b_following_minus_notool_floor']['reading']}; "
         f"Olmo {o26['R2_plus_tool_log_minus_answer_only']['rule']}, so {s26['reading']}; Qwen3 "
         f"{q26['R2_plus_tool_log_minus_answer_only']['rule']}", FIG["c26"]],
    ]
    return [dict(zip(GLANCE_COLUMNS, r)) for r in rows]


def write(name, title, intro, columns, rows, out=OUT):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / f"{name}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)
    lines = [f"# {title}", "", "Generated by cot-disclosure/agents/trackc_tables.py from results/summaries/trackC/; do not "
             "edit by hand.", "", intro, "", "| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    lines += ["| " + " | ".join(str(r[c]) for c in columns) + " |" for r in rows]
    (out / f"{name}.md").write_text("\n".join(lines) + "\n")
    return [out / f"{name}.md", out / f"{name}.csv"]


def main(out=OUT):
    paths = write("trackC_experiments", "Track C, Nov 6: C19, C25, C20 and C26, every comparison (FC1–FC4)",
                  "Each comparison as its summary has it: a and b are the two sides (X of Y), paired by item, a − b in "
                  "points with a 95% bootstrap clustered by item. C19, C25 and C20 are read by C16's two-sided rule with "
                  "C11's 20-point margin; C26's R2 by C11's deference rule; C25's note hops by the kept / lost / mixed "
                  "rule at 50%; C20's checker match by C15's 10-point margins. \"decision\" says whether the row was "
                  "pre-registered to decide anything.", EXPERIMENT_COLUMNS, experiment_rows(), out)
    paths += write("trackC_pipelines", "Track C, C20: four pipelines, one check stage each (FC3)",
                   "C15's 100 items (55 bad lookups; 53 wrong solver answers, 47 right). Caught = the solver is wrong and "
                   "the stage corrects or escalates; false alarm = the solver is right and the stage changes or "
                   "escalates; shipped wrong = of all 100 cases; tokens = the check stage's, a case. (a), (c) and (d) are "
                   "saved runs (C15, C16); (b) ran Nov 6. (c)'s solve is C16's (55 wrong, 45 right).",
                   PIPELINE_COLUMNS, pipeline_rows(), out)
    paths += write("at_a_glance_FC", "Track C's FC1–FC4 as results_at_a_glance rows (for Ritik to merge)",
                   "One row per finding, the numbers as the summaries state them (X of Y; differences in points with "
                   "95% bootstraps clustered by item). Claims are FINDINGS_C's headings, shortened.",
                   GLANCE_COLUMNS, glance_rows(), out)
    return paths


if __name__ == "__main__":
    for p in main():
        print(p.relative_to(CODE.parent))
