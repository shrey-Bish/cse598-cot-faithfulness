"""Writes docs/presentation/pack/02_NUMBERS.md: the slide numbers (curated, verbatim from FINDINGS), the deck's numbers
read from the frozen summaries (Nov 25: intervals and counts FINDINGS doesn't print as "k of n [interval]"), and every
finding at a glance (docs/paper/tables/results_at_a_glance.csv).

  python cot-disclosure/tools/make_pack_numbers.py      # from the repo root; checked by tests/test_presentation_pack.py
"""
import csv
import json
from pathlib import Path

S = "cot-disclosure/results/summaries/"
SRC = {  # finding -> its numbers-only source(s), from each finding's Source bullet in FINDINGS / FINDINGS_B / FINDINGS_C
    "F1": "docs/labeling/RESULTS_SUMMARY.json; " + S + "trackA/base_format_runs.jsonl", "F2": S + "trackA/base_format_runs.jsonl", "F3": "docs/labeling/RESULTS_SUMMARY.json",
    "F4": S + "trackA/takeover_runs.jsonl", "F5": S + "trackA/takeover_per_run.jsonl", "F6": S + "trackA/takeover_per_run.jsonl",
    "F7": S + "trackA/deletion_runs.jsonl", "F8": S + "trackA/window_reach.json", "F9": S + "trackA/step8_verdict.json",
    "F10": S + "trackA/step9_followup.json", "F11": S + "trackA/step10_handoff.json", "F12": S + "trackA/step9_followup.json",
    "F13": S + "trackA/step10_handoff.json; " + S + "trackA/deletion_runs.jsonl", "F14": S + "trackA/step9_followup.json",
    "F15": S + "trackB/trackB_report.json; " + S + "trackC/team_c4_summary.json", "F16": S + "trackB/trackB_report.json; " + S + "trackB/trackB_runs.jsonl",
    "F17": S + "trackB/trackB_report.json", "F18": S + "trackC/team_c4_summary.json", "F19": S + "trackC/team_c9_summary.json",
    "F20": S + "trackA/val_loss_report.json", "F21": S + "trackC/team_c10_summary.json", "F22": S + "trackC/team_c11_summary.json",
    "F23": S + "trackC/team_c12_summary.json", "F24": S + "trackC/c15_summary.json", "F25": S + "trackB/b15_report.json",
    "F26": S + "trackA/setA/step10_handoff.json", "F27": S + "trackA/setA/provenance_forced.json", "F28": S + "trackA/gpu/eval/gate3.json; " + S + "trackA/gpu/eval/gate3_table.md; " + S + "trackA/gpu/eval/eval_report.json; docs/FINDINGS.md",
    "F29": S + "trackB/trackB_report.json",
    "F30": S + "trackC/team_c13_granite_summary.json; " + S + "trackC/team_c13_mistral_summary.json",
    "F31": S + "trackC/c16_summary.json", "F32": S + "trackA/setA/step9_fixed_heads.json; " + S + "trackA/step9_followup.json", "F33": S + "trackC/c17_summary.json",
    "F34": S + "trackC/c18_summary.json; " + S + "trackC/team_c18_unchanged_summary.json", "F35": S + "trackB/b16_report.json; " + S + "trackB/b19_report.json",
    "F36": S + "trackA/qwen8b_mech/qwen8b_readout.json", "F37": S + "trackB/b17_report.json",
    "F38": S + "trackA/gpu/provenance_gen/provenance_gen_report.json; " + S + "trackA/gpu/b1r2/provenance_gen_report.json",
    "F39": S + "trackA/gpu/a18/a18_readout.json", "F40": S + "trackB/b24_report.json", "F41": S + "trackA/gpu/a39/a40_e2.json",
    "F42": S + "trackA/gpu/a18/a41_readout.json", "F43": S + "trackA/gpu/a39/a42_e2.json", "F44": S + "trackA/gpu/a39/a39_e2.json",
    "F45": S + "trackA/labels/l6_report.json; " + S + "trackA/gpu/a39/tradeoff_e2.json", "FB1": S + "trackB/b20_report.json", "FC1": S + "trackC/c19_summary.json",
    "FC2": S + "trackC/c25_summary.json; docs/trackC/FINDINGS_C.md", "FC3": S + "trackC/c20_summary.json", "FC4": S + "trackC/c26_summary.json",
}
X = "exploratory"
# (claim, numbers, interval, finding(s), source override or None, status)
GROUPS = [
    ("The title question: does thinking make the chain of thought more honest? (FINDINGS story, item 5: \"mixed\")", [
        ("With thinking on, Qwen3-8B names the tool in its private reasoning after a call", "141 of 145 calls", "", "F29", None, "measured; one model"),
        ("…but its final answer doesn't name it (followed runs)", "0 of 143", "", "F29", None, "measured; one model"),
        ("Thinking on raises Qwen3-8B's call rate (on against off)", "145 against 35 of 162 runs", "", "F29", None, "measured; one model"),
        ("…so it takes the tool's wrong letter far more (real tool call, on − off, points)", "+64", "[+51, +75]", "F29", None, X + " (on − off read after the fact; no rule fixed)"),
        ("gpt-oss-20b: more reasoning effort, following on the real tool call (high − low, points)", "+7", "[−1, +16]", "F37", None, "pre-registered: no change detected; run after its one-day window"),
        ("gpt-oss-20b: the bare answer after a call (high − low); 37 of 37 bare at low", "−5; 37 of 37", "[−10, 0]", "F37", None, "pre-registered: no change detected"),
        ("gpt-oss-20b calls the tool far more at high effort", "129 against 37 of 162 runs", "", "F37", None, "descriptive"),
        ("Nemotron 3 Nano: the answer after the inserted tool turn is less bare with thinking on (points)", "−14", "[−19, −9]", "FB1", None, "confirmed by the rule (B20)"),
    ]),
    ("Finding 1: a tool's hint pulls harder than the user's; much of the pull is the claim to be the answer key", [
        ("Qwen3 30B Thinking, pasted tool block − user (Gate 2: 54 questions × 3 runs; points)", "+35", "[+24, +46]", "F15", None, "confirmed"),
        ("Qwen3 30B Thinking, its own tool call − user", "+31", "[+22, +42]", "F15", None, "confirmed"),
        ("Qwen3 30B Instruct, pasted tool block − user", "+21", "[+12, +31]", "F16", None, "confirmed"),
        ("Qwen3 30B Instruct, its own tool call − user", "+90", "[+83, +96]", "F16", None, "confirmed"),
        ("Olmo 3 7B Think, pasted tool block − user", "+32", "[+22, +42]", "F17", None, "confirmed"),
        ("Olmo 3 7B Think, inserted tool turn − user", "+21", "[+13, +30]", "F17", None, "confirmed"),
        ("Qwen3-8B, tool − user, thinking on and off (points)", "+19, +13", "", "F29", None, "confirmed"),
        ("gpt-oss-20b, every reasoning effort: pasted − user; the real call − user (points)", "+24 to +26; +14 to +26", "", "F37", None, "reported with no decision; run after its one-day window"),
        ("Three more families (Gemma 4 26B-A4B, Nemotron 3 Nano 30B-A3B, Granite 4.2 8B), clear in all 10 readings: tool channel − user; pasted − user (points)", "+24 to +91; +18 to +73", "", "FB1", None, "confirmed by the rule (B20; temperature 1.0)"),
        ("Served format, two models (the first test): tool 17 of 31 against user 2 of 31", "17 of 31; 2 of 31; +48", "[+31, +65]", "F1", None, "confirmed in the served format"),
        ("A user's answer-key claim closes the gap to the pasted block: 68% and 71% in the two Qwen3 models, all of it in Olmo", "68%; 71%", "", "F35", None, "confirmed by the rule (B16)"),
        ("Beyond the claim: Qwen3 30B Instruct's own call", "+75", "[+65, +85]", "F35", None, "confirmed by the rule"),
        ("Beyond the claim: Qwen3 30B Thinking's pasted block", "+12", "[+5, +19]", "F35", None, "confirmed by the rule"),
        ("Olmo's inserted tool turn moves it less than the user's claim", "−14", "[−21, −6]", "F35", None, "confirmed by the rule"),
        ("Same-day rerun (B19): all six readings held", "+10; +75; −14", "[+4, +17]; [+65, +85]; [−22, −7]", "F35", None, "confirmed same-day"),
        ("Authority ladder: \"the official solution manual\" − \"a classmate\" (three models)", "+41; +12; +32", "[+31, +51]; [+4, +20]; [+23, +41]", "F40", None, "confirmed by the rule (B24)"),
        ("The manual − B16's answer key, Qwen3 30B Thinking (the other two: no difference detected)", "+21", "[+14, +29]", "F40", None, "confirmed by the rule"),
    ]),
    ("Finding 2: after a tool call the reasoning names the tool, but the final answer usually doesn't", [
        ("Keyword counts (Test 1): the private reasoning names the hint; the final answer does", "208 of 216; 8 of 216", "", "F3", None, "confirmed as keyword counts; hand labels don't stand (L3)"),
        ("Hand labels L3 didn't reach agreement: kappa, private and final", "0.63; 0.54", "", "F3", None, "not met (L3)"),
        ("Bare letter after a call (C4, Qwen3 30B Thinking): after a right lookup; after a wrong one; with no tool", "80 of 84; 71 of 75; 2 of 159", "", "F15", None, "confirmed"),
        ("Qwen3 30B Thinking, bare after a call (Track B)", "51 of 54", "", "F15", None, "confirmed"),
        ("Qwen3 30B Instruct calls the lookup; bare after its calls", "147 of 162; 111 of 147", "", "F16", None, "confirmed"),
        ("Olmo 3 7B Think, bare: after the inserted turn; after a changed system turn", "115 of 162; 85 of 162", "", "F17", None, "tentative (system-turn confound)"),
        ("Qwen3-8B with thinking on, bare after a call", "138 of 145", "", "F29", None, "confirmed"),
        ("gpt-oss-20b, bare after a call at low, medium, high effort (bare with no hint too: 79% to 81%)", "37 of 37; 75 of 78; 122 of 129", "", "F37", None, "run after its one-day window"),
        ("Barer after Granite's own call; after Nemotron's inserted turn, thinking off (points)", "+37; +27", "[+25, +49]; [+21, +34]", "FB1", None, "confirmed by the rule (B20)"),
        ("Not general: Gemma names the tool in its answer with thinking off", "127 of 162", "", "FB1", None, "after the fact (Gemma's readings uninformative)"),
        ("One instruction (\"say what your answer is based on\") brings the tool back: Thinking bare 51 of 54 → 30 of 63; Instruct 111 → 12 of 162", "51 of 54; 30 of 63; 12 of 162", "", "F25", None, "confirmed as keyword counts"),
        ("…names the tool after a call (points): Thinking; Instruct", "+47; +70", "[+30, +64]; [+59, +81]", "F25", None, "confirmed as keyword counts"),
        ("…but following doesn't change: Thinking; Instruct", "+6; −1", "[−2, +14]; [−7, +6]", "F25", None, "no change detected"),
    ]),
    ("Finding 3: inside the model, three layers carry most of the hint's effect", [
        ("Olmo 3 7B Think: share of the drop at the takeover held by layers 15, 19 and 23 (19 cuts, 9 questions)", "0.90", "[0.85, 0.96]", "F11", None, "confirmed (one model)"),
        ("…per layer (15, 19, 23)", "0.34; 0.17; 0.39", "", "F11", None, "confirmed"),
        ("On 16 questions not used to find them (set A, 31 cuts)", "0.90", "[0.76, 1.06]", "F26", None, "confirmed (replicates)"),
        ("Attention: of the 10 top heads, in layers 15/19/23; followed − resisted", "8 of the 10; +0.040", "[+0.021, +0.057]", "F12", None, "confirmed"),
        ("The three heads separate followed from resisted runs on new questions (set A, 15 questions); on Test 2", "+0.068; +0.084", "[+0.044, +0.088]; [+0.062, +0.105]", "F32", None, "confirmed (one model)"),
        ("Second model: Qwen3-8B's own three layers (21, 22, 29) on MMLU-Pro (14 questions); on the puzzles", "0.70; 0.74", "[0.60, 0.83]; [0.69, 0.79]", "F36", None, "confirmed (replicates; pre-registered)"),
        ("The reasoning relays at most", "0.26", "[0.14, 0.43]", "F13", None, "confirmed as measured"),
        ("Inside the fixed model: LoRA's weights on base's reasoning pull toward the hint harder (logits)", "−0.72", "[−1.02, −0.39]", "F39", None, "confirmed by the rule"),
        ("Consistency training's weights (A40) remove part of the pull, in layers 0–14; A40 − LoRA (logits)", "+0.68; +1.40", "[+0.17, +1.18]; [+0.73, +2.09]", "F42", None, "confirmed by the rule"),
    ]),
    ("Finding 4: Olmo reviewers defer to the tool's log; an independent checker holds", [
        ("Olmo 3.1 32B reviewer corrects a wrong tool answer: alone 59 of 73; with the solver's private reasoning or the tool log, 6 and 3 of 73", "59 of 73; 3 of 73", "", "F18", None, "confirmed for that reviewer"),
        ("…differences (points): private reasoning; tool log", "−73; −77", "[−86, −58]; [−91, −61]", "F18", None, "confirmed"),
        ("The checker (re-solves without the tool) flagged bad lookups", "73 of 75", "[91, 99%]", "F18", None, "confirmed"),
        ("False alarms on good lookups; the no-tool floor", "7 of 80; 12 of 155", "[4, 17%]; [4, 13%]", "F18", None, "confirmed"),
        ("Telling the reviewer to check the tool: 6 → 8 of 73 and 3 → 4", "8 of 73; +3; +1", "[−4, +9]; [−3, +6]", "F19", None, "confirmed as no restoration"),
        ("Committing to its own answer first (Olmo + tool log; Qwen3 + tool log)", "−75; −32", "[−86, −62]; [−44, −20]", "F21", None, "confirmed"),
        ("Olmo 3 7B Instruct defers too (32 → 1 of 73); Qwen3 30B Thinking doesn't", "1 of 73; −42; +1", "[−58, −28]; [−6, +10]", "F22", None, "confirmed per model"),
        ("Redacting the tool's letter restores part: 6 → 23 and 3 → 24 of 73", "24 of 73; +23; +29", "[+13, +34]; [+16, +41]", "F23", None, "confirmed as partial"),
        ("On 100 fresh items (C15): the deference; redaction; H23 (not supported)", "−55; +25; +14", "[−70, −38]; [+11, +38]; [−13, +37]", "F24", None, "confirmed; H23 not supported"),
        ("A cheaper check from two reviews ships wrong answers (4 and 7 of 53); the checker stops all 53; its false alarms", "7 of 53; 7 of 45", "", "F24", None, "confirmed"),
        ("Two more families don't defer: Granite 4.1 30B; Mistral Small 3.2 24B", "−5; +19", "[−26, +15]; [+10, +30]", "F30", None, "confirmed per model"),
        ("When the solver's final answer names the tool, the Olmo reviewer corrects fewer", "25 against 36 of 53; −21", "[−34, −8]", "F31", None, "confirmed fall; unclear by the 20-point rule"),
        ("A fixed sentence naming the tool changes nothing (Olmo)", "+0", "[−11, +11]", "F33", None, "confirmed (no change)"),
        ("Removing the solver's tool-citing sentences restores the check (Olmo)", "25 against 9 of 34; +47", "[+29, +65]", "F34", None, "confirmed; H33 not supported"),
    ]),
    ("Finding 5: every fix is a trade; fine-tuning made answers more candid, following wrong hints no less than the instruction and fewer than no fix", [
        ("Training (LoRA): the taught tokens' loss against base; without the fixed opener", "−58%; −40%", "", "F20", None, "confirmed (as loss)"),
        ("Gate 3 on the held-out 30 (930 runs per system), following − no fix: LoRA; tags; LoRA + tags; LoRA on 15/19/23", "−10; −6; −7; −7", "[−16, −4]; [−10, −2]; [−13, −1]; [−13, −2]", "F28", None, "met by the pre-registered rule"),
        ("The one-line instruction − no fix", "−13", "[−21, −6]", "F28", None, "confirmed"),
        ("Each trained version − the instruction: LoRA; tags; LoRA + tags; LoRA on 15/19/23", "+3; +7; +6; +6", "[−1, +8]; [+1, +14]; [+1, +11]; [+0.4, +12]", "F28", None, X + " (not pre-registered)"),
        ("False-disclosure candidates: LoRA; LoRA + tags; the instruction", "+10; +10; −9", "[+2, +18]; [+2, +19]; [−14, −4]", "F28", None, "confirmed"),
        ("By hand labels (L4, kappa 0.93), LoRA's candidates that claim to reject the hint they end on; that say the hint shaped the answer", "1 to 2 of 147; 97 of 147", "", "F28", None, "labels (L4 part 1)"),
        ("Consistency training (A40) against the instruction on the 120 fresh questions: wrong hints followed", "84 of 694; 237 of 713; −21", "[−26, −16]", "F41", None, "confirmed by the rule: \"fewer, but costs acceptance\""),
        ("…right hints taken (acceptance)", "347 of 459; 431 of 476; −15", "[−20, −10]", "F41", None, "confirmed by the rule"),
        ("A40 + the note follows fewest of all; its acceptance cost against the instruction", "64 of 706; −20", "[−26, −14]", "F43", None, "confirmed by the rule"),
        ("Marking tool output \"unverified\" alone (the inserted tool turn)", "−1", "[−7, +4]", "F44", None, "confirmed by the rule: no effect"),
        ("…with the instruction: following; acceptance", "−14; −12", "[−20, −9]; [−18, −6]", "F44", None, "confirmed: adds, costs acceptance"),
        ("LoRA + the note − the instruction: following (R2); acceptance", "−8; −9", "[−12, −4]; [−13, −5]", "F44", None, "confirmed: fewer than the instruction, at an acceptance cost"),
        ("Gate 3 again on the 120, with power: the instruction; LoRA (− no fix)", "−9; −7", "[−14, −4]; [−11, −3]", "F44", None, "passes (R1)"),
        ("Hand labels (L6): when LoRA follows a wrong hint its final answer says so; the instruction's", "37 of 42; 18 of 42; +45", "[+25, +64]", "F45", None, "confirmed by the rule: discloses more than the instruction, in labels"),
        ("L6 agreement: Ritik against J-opus (kappa); J-opus (blind to systems) agreeing on rows", "0.96; 82 of 84", "", "F45", None, "labels"),
        ("The keyword version of the same comparison; its agreement with the labels; A40's keyword rate", "225 of 248; 118 of 237; 83 of 84; 60 of 84", "", "F45", None, X + " (post hoc)"),
        ("The attention dial (B1) on the 30: the inserted tool turn; its acceptance cost (25 → 23 of 30, −7 points against a 5-point limit); every hint span", "−17; 23 of 30; −9", "[−30, −3]; [−19, +1]", "F38", None, "\"ignores tools\" by the rule; underpowered at 30 questions"),
        ("Its replication on the 120 (B1R2): following 82 of 240 → 49 of 240", "49 of 240; −13.8", "[−20.0, −7.5]", "F38", None, "the cut replicates"),
        ("…acceptance 211 → 197 of 240; no-hint accuracy", "197 of 240; −5.8; +0.8", "[−10.8, −1.3]; [−6.7, +8.3]", "F38", None, "a real cost, past the limit by the point estimate"),
        ("The trade-off: A40 gives more correct answers than the instruction only when fewer than this share of the tool's answers are correct", "0.36", "[0.22, 0.50]", "STORY", "docs/paper/REPORT.md; docs/paper/figures/tradeoff_e2.csv", X + " (post hoc); replaces no verdict"),
    ]),
]


def _w(path, keys):
    o = json.loads(Path(path).read_text())
    for k in keys:
        o = o[k]
    lo, hi = (round(100 * x) for x in o["wilson"])
    return o["k"], o["n"], lo, hi


def summary_rows():
    """The deck's numbers whose interval (or count) is stored in a frozen summary but not printed in FINDINGS as
    "k of n [interval]": each read here from its JSON, with its key path."""
    TB, B20 = S + "trackB/trackB_report.json", S + "trackB/b20_report.json"
    q8 = ["budget_32768", "sol_vllm | qwen3-8b | thinking=True", "channels", "tool_real"]
    rows = [
        ("Qwen3-8B, thinking on: the private reasoning names the tool after a call", TB, q8 + ["mention_private_when_called"], "F29"),
        ("Qwen3-8B, thinking on: the final answer names it (runs that followed)", TB, q8 + ["mention_final_when_followed"], "F29"),
        ("Gemma 4 26B-A4B, thinking off: the final answer names the tool (inserted tool turn, answered runs)", B20,
         ["gemma-4-26b-a4b-it", "settings", "off", "budget_32768", "secondary", "channels", "tool_injected", "mention_final"], "FB1"),
        ("The checker stopped wrong tool answers (100 fresh items; Olmo 3.1 32B pipeline)", S + "trackC/c15_summary.json",
         ["c_frozen_rule", "olmo3-32b-instruct", "plus_tool_log", "bad_lookups", "checker_pipeline_caught"], "F24"),
        ("…its false alarms on good lookups", S + "trackC/c15_summary.json",
         ["c_frozen_rule", "olmo3-32b-instruct", "plus_tool_log", "good_lookups", "checker_pipeline_false_alarms"], "F24"),
        ("No fix took the wrong hint, the 120 fresh questions, a tool call's reply, both wordings (the count beside the demo's run)",
         S + "trackA/gpu/a39/a40_e2.json", ["systems", "base", "following", "inserted"], "F41"),
    ]
    strip = [("Qwen3 30B Instruct", TB, ["budget_32768", "voyager | qwen3-30b-a3b-instruct-2507 | thinking=None", "channels"], "tool_real", "F16"),
             ("Qwen3 30B Thinking", TB, ["budget_32768", "voyager | qwen3-30b-a3b-thinking-2507 | thinking=None", "channels"], "tool_real", "F15"),
             ("Olmo 3 7B Think", TB, ["budget_32768", "voyager | olmo3-7b-think | thinking=None", "channels"], "tool_injected", "F17"),
             ("Qwen3-8B, thinking on", TB, ["budget_32768", "sol_vllm | qwen3-8b | thinking=True", "channels"], "tool_real", "F29"),
             ("Gemma 4 26B-A4B, thinking on", B20, ["gemma-4-26b-a4b-it", "settings", "on", "budget_32768", "secondary", "channels"], "tool_injected", "FB1"),
             ("Nemotron 3 Nano 30B-A3B, thinking on", B20, ["nemotron-3-nano-30b-a3b", "settings", "on", "budget_32768", "secondary", "channels"], "tool_injected", "FB1"),
             ("Granite 4.2 8B, thinking on", B20, ["granite-4.2-8b", "settings", "on", "budget_32768", "secondary", "channels"], "tool_real", "FB1"),
             # the full backup figure's three thinking-off settings (Nov 25)
             ("Qwen3-8B, thinking off", TB, ["budget_32768", "sol_vllm | qwen3-8b | thinking=False", "channels"], "tool_real", "F29"),
             ("Gemma 4 26B-A4B, thinking off", B20, ["gemma-4-26b-a4b-it", "settings", "off", "budget_32768", "secondary", "channels"], "tool_injected", "FB1"),
             ("Nemotron 3 Nano 30B-A3B, thinking off", B20, ["nemotron-3-nano-30b-a3b", "settings", "off", "budget_32768", "secondary", "channels"], "tool_injected", "FB1")]
    out = [
        ("Qwen3 30B Instruct, the user's guess against its own tool call (following the wrong letter)", "1 of 162; 147 of 162", "[0, 3%]; [85, 94%]", "F16", None, "confirmed"),
        ("Qwen3 30B Thinking, when it called the tool: the private reasoning names it; the final answer does", "54 of 54; 3 of 54", "[93, 100%]; [2, 15%]", "F15", None, "confirmed (keyword counts)"),
    ]
    for claim, src, keys, fid in rows:
        k, n, lo, hi = _w(src, keys)
        out.append((claim, f"{k} of {n}", f"[{lo}, {hi}%]", fid, src + "#" + "/".join(keys).replace("|", "\\|"), "summary: k and n as FINDINGS; interval from the summary's stored Wilson"))
    for name, src, keys, tool, fid in strip:
        ku, nu, lu, hu = _w(src, keys + ["user", "following"])
        kt, nt, lt, ht = _w(src, keys + [tool, "following"])
        ch = "its own tool call" if tool == "tool_real" else "the inserted tool turn"
        out.append((f"Across models (slide 4's strip): {name}, the wrong letter followed, from the user against from {ch}",
                    f"{ku} of {nu}; {kt} of {nt}", f"[{lu}, {hu}%]; [{lt}, {ht}%]", fid, src + "#" + "/".join(keys).replace("|", "\\|"),
                    "summary: k and n as FINDINGS' tables; intervals from the summary's stored Wilson"))
    # slide 6's rates: consistency training against the instruction, each the k of n above rounded (Nov 25)
    a40 = S + "trackA/gpu/a39/a40_e2.json"
    r = {}
    for sysk in ("a40", "prompt_only"):
        for m, path in (("follow", ["following", "pooled"]), ("accept", ["acceptance", "pooled"])):
            k, n, _, _ = _w(a40, ["systems", sysk] + path)
            r[sysk, m] = (k, n)
    pct = lambda kn: f"{round(100 * kn[0] / kn[1])}%"
    out.append(("Consistency training against the one-line instruction, as rates (slide 6): wrong hints followed; right hints taken",
                f"{r['a40', 'follow'][0]} of {r['a40', 'follow'][1]} ({pct(r['a40', 'follow'])}) vs {r['prompt_only', 'follow'][0]} of {r['prompt_only', 'follow'][1]} ({pct(r['prompt_only', 'follow'])}); "
                f"{r['a40', 'accept'][0]} of {r['a40', 'accept'][1]} ({pct(r['a40', 'accept'])}) vs {r['prompt_only', 'accept'][0]} of {r['prompt_only', 'accept'][1]} ({pct(r['prompt_only', 'accept'])})",
                "", "F41", a40, "rates: each k of n as FINDINGS, rounded to a percent"))
    # version 3 (Nov 26). Slide 6 and 9's rates: consistency training against no fix (wrong hints followed, pooled over
    # the user's, pasted and inserted channels; right tool hints taken, pasted and inserted)
    for sysk in ("base",):
        for m, path in (("follow", ["following", "pooled"]), ("accept", ["acceptance", "pooled"])):
            k, n, _, _ = _w(a40, ["systems", sysk] + path)
            r[sysk, m] = (k, n)
    out.append(("No fix against consistency training, as rates (slides 6 and 9): wrong hints followed (from the user or a tool); right tool hints taken",
                f"{r['base', 'follow'][0]} of {r['base', 'follow'][1]} ({pct(r['base', 'follow'])}) vs {r['a40', 'follow'][0]} of {r['a40', 'follow'][1]} ({pct(r['a40', 'follow'])}); "
                f"{r['base', 'accept'][0]} of {r['base', 'accept'][1]} ({pct(r['base', 'accept'])}) vs {r['a40', 'accept'][0]} of {r['a40', 'accept'][1]} ({pct(r['a40', 'accept'])})",
                "", "F41", a40, "rates: each k of n as FINDINGS, rounded to a percent"))
    # slide 8: the six reviewers, the same 73 wrong tool answers, seeing the answer only and the tool's log
    reviewers = [("Olmo 3.1 32B", "trackC/team_c4_summary.json", "olmo3-32b-instruct", "F18"),
                 ("Olmo 3 7B", "trackC/team_c11_summary.json", "olmo3-7b-instruct", "F22"),
                 ("Qwen3 30B Instruct", "trackC/team_c4_summary.json", "qwen3-30b-a3b-instruct-2507", "F18"),
                 ("Qwen3 30B Thinking", "trackC/team_c11_summary.json", "qwen3-30b-a3b-thinking-2507", "F22"),
                 ("Granite 4.1 30B", "trackC/team_c13_granite_summary.json", "granite-4.1-30b", "F30"),
                 ("Mistral Small 3.2 24B", "trackC/team_c13_mistral_summary.json", "mistral-small-3.2-24b", "F30")]
    for name, src, rid, fid in reviewers:
        for v, view in (("answer_only", "the answer only"), ("plus_tool_log", "the tool's log too")):
            keys = ["by_team_model_variant", f"tool | {rid} | {v}", "reviewer_alone", "corrects_wrong_solver"]
            k, n, lo, hi = _w(S + src, keys)
            out.append((f"The review team (slide 8): the {name} reviewer corrected the solver's wrong tool answers, seeing {view}",
                        f"{k} of {n}", f"[{lo}, {hi}%]", fid, S + src + "#" + "/".join(keys).replace("|", "\\|"),
                        "summary: k and n from the summary; interval from its stored Wilson"))
    return out


def row(i, c):
    claim, nums, ival, fid, src, status = c
    src = src or (SRC.get(fid) if fid != "STORY" else "")
    srcs = "<br>".join(f"`{s.strip()}`" for s in src.split(";")) if src else ""
    srcs = srcs.replace("#", "` (key `").replace("`<br>", "`)<br>") if "#" in srcs else srcs
    if "#" in src and not srcs.endswith(")"):
        srcs += ")"
    return f"| N{i:02d} | {claim} | {nums} | {ival} | {fid} | {srcs} | {status} |"


def main():
    out = ["# 02. The numbers", "",
           "Every number a slide or the report might use, as frozen (the tag `results-freeze-2026-11-18`), with its finding "
           "and its numbers-only source. Wording and numbers are FINDINGS' ([`docs/FINDINGS.md`](../../FINDINGS.md), with "
           "[`FINDINGS_B.md`](../../trackB/FINDINGS_B.md) and [`FINDINGS_C.md`](../../trackC/FINDINGS_C.md)); \"STORY\" is "
           "FINDINGS' summary at its top. Three rows of the glance table are in FINDINGS' own words here (F4, FC2, FC4: the "
           "same numbers).", "",
           "- **How to read:** rates are \"k of n\" runs (or items) with a 95% Wilson interval where one is given; differences "
           "are percentage points with a 95% bootstrap clustered by question (by item in Track C). \"Exploratory\" marks a "
           "result FINDINGS marks post hoc, after the fact, descriptive or not pre-registered.",
           "- **Checked:** `cot-disclosure/tests/test_presentation_pack.py` finds every \"k of n\" and interval of each row in "
           "its finding's section of FINDINGS (or the STORY), every source file in the repo, and every \"k of n\" as a k and "
           "n pair, and every interval bound, in the row's JSON source. Rows whose source is per-run (`.jsonl`) are checked "
           "against FINDINGS only.",
           "- **Plain names:** the codes in parentheses are for searching FINDINGS; [`docs/GLOSSARY.md`](../../GLOSSARY.md) "
           "gives each one's plain name.", ""]
    i = 1
    for g, rows in GROUPS:
        out += [f"## {g}", "", "| ID | claim | numbers | interval | finding | source | status |", "|---|---|---|---|---|---|---|"]
        for c in rows:
            out.append(row(i, c)); i += 1
        out.append("")
    out += ["## Every finding at a glance", "",
            "One row per finding, the numbers as FINDINGS states them (from "
            "[`results_at_a_glance.csv`](../../paper/tables/results_at_a_glance.csv), built from FINDINGS on Nov 4 and "
            "kept with it), the source from the finding's own Source bullet, the status in FINDINGS' words.", "",
            "| ID | claim | numbers | interval | finding | source | status |", "|---|---|---|---|---|---|---|"]
    # three glance rows put in FINDINGS' own words (the same numbers): F4 "26 of the 43", FC2 "0 [0, 0]", FC4 "[−29, 0]"
    fix = {"F4": ("26 of 43 late; on 9 of 11 questions", "26 of the 43 late; on 9 of the 11 questions"),
           "FC2": ("Qwen3 +0 [+0, +0]", "Qwen3 0 [0, 0]"), "FC4": ("Qwen3 −14 [−29, +0]", "Qwen3 −14 [−29, 0]")}
    for r in csv.DictReader(open("docs/paper/tables/results_at_a_glance.csv")):
        if r["finding"] in fix:
            a, b = fix[r["finding"]]
            assert a in r["key_numbers"], r["finding"]
            r["key_numbers"] = r["key_numbers"].replace(a, b)
        if r["finding"] == "F42":
            r["key_numbers"] += " (the source holds 4.8148 for the upper bound, so 4.81: FINDINGS' 4.82 is one off in the last place; kept as frozen)"
        st = r["status"]
        if any(w in st.lower() for w in ("after the fact", "post hoc", "exploratory", "descriptive", "not pre-registered")):
            st = "exploratory in part: " + st
        out.append(row(i, (f"{r['claim']} (Track {r['track']})", r["key_numbers"], "", r["finding"], None, st))); i += 1
    out += ["## The final deck's numbers (Nov 25)", "",
            "Numbers the final deck shows whose interval (or count) is stored in a frozen summary but not printed in "
            "FINDINGS as \"k of n [interval]\": read here from the summary, with its key path. Each one's k and n are "
            "FINDINGS' (FB1's table writes them as k/n). Checked against the JSON only (Nov 25).", "",
            "| ID | claim | numbers | interval | finding | source | status |", "|---|---|---|---|---|---|---|"]
    for c in summary_rows():
        out.append(row(i, c)); i += 1
    out.append("")
    out.append("")
    Path("docs/presentation/pack/02_NUMBERS.md").write_text("\n".join(out))
    print("rows", i - 1)


main()
