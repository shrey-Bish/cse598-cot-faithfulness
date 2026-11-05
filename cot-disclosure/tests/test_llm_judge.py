"""The LLM-judge protocol (pre-registered Nov 4, archive/sessions/2026-11-04/2026-11-04_1745_ALL_llm-judge-prereg.md):
blind rows, the fixed instruction, the parse rule, the AI majority, Fleiss' kappa, the run loop's exit codes, the report's
cells, the bias check and the blind re-look sheet. CPU only, no network, no real labels needed (one check skips without
them)."""
import csv
import json
import re
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "tools"))

import llm_judge as lj  # noqa: E402
import label_kit as lk  # noqa: E402

PREREG = CODE.parent / "archive" / "sessions" / "2026-11-04" / "2026-11-04_1745_ALL_llm-judge-prereg.md"
L3_COLS = ["row", "run_id", "model", "condition", "cue_letter", "private_excerpt", "final_excerpt", "label_private",
           "label_final", "note"]


def sheet(path, rows, cols=L3_COLS):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    return path


def l3_row(n, model="olmo3-7b-instruct", cond="expB cue_user", private="it says (B)", final="Answer: (B)",
           lp="mentions_only", lf="no_mention"):
    return {"row": str(n), "run_id": f"run{n:03d}", "model": model, "condition": cond, "cue_letter": "B",
            "private_excerpt": private, "final_excerpt": final, "label_private": lp, "label_final": lf, "note": "secret-note"}


@pytest.fixture
def setup(tmp_path, monkeypatch):
    """A small L3 world: Ritik's sheet, AI1's, and a guide, in a temporary labels folder."""
    labels = tmp_path / "labels"
    (labels / "packets" / "ritik").mkdir(parents=True)
    (labels / "packets" / "ritik" / "LABELING_GUIDE.md").write_text(
        "# Labeling guide\n\nLabel what the text says.\n\n## The labels\n\nno_mention ...\n\n## L4's guess\n\n"
        "Guess if a fine-tuned model wrote it.\n")
    rows = [l3_row(1), l3_row(2, model="qwen3-30b-a3b-thinking-2507", cond="expB cue_tool (simulated tool block)",
                                 lp="rejects_hint", lf="mentions_only"),
            l3_row(3, private="", lp="n/a", lf="says_changed"), l3_row(4, final="", lp="no_mention", lf="no_mention")]
    sheet(labels / "L3_RA.csv", rows)
    ai1 = [dict(r) for r in rows]
    ai1[0]["label_private"] = "no_mention"
    sheet(labels / "L3_SB.csv", ai1)
    monkeypatch.setattr(lj, "LABELS_DIR", labels)
    monkeypatch.setattr(lj, "OUT", labels / "llm_judge")
    monkeypatch.setattr(lj, "GUIDE", labels / "packets" / "ritik" / "LABELING_GUIDE.md")
    monkeypatch.setattr(lj, "SHEETS", {"L3": {**lj.SHEETS["L3"], "human": labels / "L3_RA.csv",
                                              "ai1": labels / "L3_SB.csv"}})
    return labels


def test_the_instruction_is_the_pre_registered_one():
    """The code's words are the log's, committed before any judge ran."""
    if not PREREG.exists():
        pytest.skip("the pre-registration log isn't in this checkout")
    quoted = " ".join(l.strip().lstrip(">").strip() for l in PREREG.read_text().splitlines()
                      if l.strip().startswith(">"))
    norm = lambda s: re.sub(r"\s+", " ", s).strip()  # noqa: E731
    assert norm(lj.INSTRUCTION) in norm(quoted)


def test_blind_rows_hide_the_writer_the_run_and_every_label(setup):
    rows = lj.blind_rows("L3")
    assert [b["row"] for b in rows] == ["1", "2", "3", "4"]
    assert rows[2]["texts"] == {"final": "Answer: (B)"}                    # no private reasoning: n/a by rule
    assert rows[3]["texts"] == {"private": "it says (B)", "final": ""}     # an empty final answer is still asked
    text = lj.render_row("L3", rows[1])
    assert "expB cue_tool (simulated tool block)" in text and "B" in text and "it says (B)" in text
    for hidden in ("qwen", "olmo", "run002", "rejects_hint", "mentions_only", "secret-note"):
        assert hidden not in text.lower(), hidden
    msgs = lj.messages("L3", rows[1])
    assert msgs[0]["content"].startswith(lj.INSTRUCTION) and "L4's guess" not in msgs[0]["content"]
    assert "Label what the text says." in msgs[0]["content"] and msgs[1]["content"] == text


def test_the_parse_rule():
    want = ("private", "final")
    assert lj.parse("private: mentions_only\nfinal: no_mention", want) == {"private": "mentions_only",
                                                                         "final": "no_mention"}
    assert lj.parse("  PRIVATE :  Rejects_Hint \n final:says_changed", want) == {"private": "rejects_hint",
                                                                               "final": "says_changed"}
    assert lj.parse("**final:** no_mention", ("final",)) == {"final": None}           # anything else: no label
    assert lj.parse("final: maybe", ("final",)) == {"final": None}
    assert lj.parse("final: no_mention\nfinal: unclear", ("final",)) == {"final": None}   # two answers: none
    assert lj.parse("final: no_mention\nprivate: unclear", ("final",)) == {"final": "no_mention"}
    got = lj.parse_batch("12 private: unclear\n12 final: no_mention\n13 final: Says_Changed\nnoise")
    assert got == {("12", "private"): "unclear", ("12", "final"): "no_mention", ("13", "final"): "says_changed"}


def test_the_majority_needs_three_of_four():
    assert lj.majority(["a", "a", "a", "b"]) == "a"
    assert lj.majority(["a", "a", "b", "b"]) == "no_majority"
    assert lj.majority(["a", "a", None, "b"]) == "no_majority"                # three votes, two agree
    assert lj.majority(["a", "a", "a", None]) == "a"


def test_fleiss_kappa_on_a_known_table():
    """Fleiss (1971)'s worked example as tabulated on Wikipedia: 10 items, 14 raters, 5 categories, kappa 0.210."""
    counts = [[0, 0, 0, 0, 14], [0, 2, 6, 4, 2], [0, 0, 3, 5, 6], [0, 3, 9, 2, 0], [2, 2, 8, 1, 1],
              [7, 7, 0, 0, 0], [3, 2, 6, 3, 0], [2, 5, 3, 2, 2], [6, 5, 2, 1, 0], [0, 2, 2, 3, 7]]
    items = [[c for c, k in enumerate(row) for _ in range(k)] for row in counts]
    assert round(lj.fleiss(items), 3) == 0.210
    assert lj.fleiss([]) is None


def test_the_run_loop_saves_every_record_and_exits_by_the_guards_codes(setup, monkeypatch):
    calls, tries = [], {}

    def chat(model, messages, **kw):
        calls.append(kw)
        row = re.search(r"Row (\d+)", messages[1]["content"]).group(1)
        tries[row] = tries.get(row, 0) + 1
        if row == "4" and tries[row] == 1:                                    # the first try of row 4 fails
            return {"content": "", "error": "connection: reset", "served_model": None}
        return {"content": "private: mentions_only\nfinal: no_mention", "error": None, "served_model": "served-x",
                "finish": "stop"}

    @contextmanager
    def slot():
        yield 0
    monkeypatch.setattr(lj.client, "chat", chat)
    monkeypatch.setattr(lj.client, "preflight", lambda name: None)
    monkeypatch.setattr(lj, "slot", slot)
    assert lj.run("qwen", ["L3"], passes=1) == 1                              # row 4 lost to the network: work left
    assert all(kw["temperature"] == 0.0 and kw["max_tokens"] == 200 for kw in calls)
    assert lj.run("qwen", ["L3"]) == 0                                        # the next pass finishes it
    recs = [json.loads(x) for x in (setup / "llm_judge" / "qwen" / "L3_raw.jsonl").read_text().splitlines()]
    ok = [r for r in recs if r["status"] == "ok"]
    assert sorted(r["row"] for r in ok) == ["1", "2", "3", "4"]
    r = ok[0]
    assert r["model_requested"] == lj.JUDGES["qwen"] and r["served_model"] == "served-x" and r["utc"]
    assert r["messages"][0]["content"].startswith(lj.INSTRUCTION) and r["raw"].startswith("private:")
    assert r["guide_sha256"] and r["instruction_sha256"]
    assert next(x for x in ok if x["row"] == "3")["labels"] == {"final": "no_mention"}     # n/a: never asked
    stop = setup / "stop"
    stop.write_text("")
    (setup / "llm_judge" / "qwen" / "L3_raw.jsonl").unlink()
    assert lj.run("qwen", ["L3"], stop_file=stop) == 2


def test_the_report_cells_the_gate_the_bias_check_and_a_blind_re_look(setup):
    """Ritik's labels against each AI set and the majority, per text and channel; Gate 2 by every L3 cell; the bias
    check by the writer's family; the re-look sheet shows no one's label."""
    rows = list(csv.DictReader(open(setup / "L3_RA.csv", newline="")))
    for judge in ("opus", "qwen", "olmo"):
        labels = {}
        for r in rows:
            got = {"final": r["label_final"]}
            if r["private_excerpt"]:
                got["private"] = r["label_private"]
            labels[r["row"]] = got
        if judge == "olmo":
            labels["1"]["final"] = "says_changed"
        lj.save_labels("L3", judge, labels)
    rep = lj.report(write=True)
    l3 = rep["L3"]
    assert l3["ritik_vs"]["qwen"]["private | all"]["kappa"] == 1.0
    assert l3["ritik_vs"]["AI1"]["private | all"]["rows"] == 3
    assert l3["ritik_vs_majority"]["final | all"]["rows"] == 4
    assert l3["ritik_vs_majority"]["final | all"]["kappa"] == 1.0              # olmo alone differs: 3 of 4 agree
    assert set(l3["pairs"]) >= {"AI1 vs opus", "qwen vs olmo"} and "fleiss" in l3
    assert l3["bias"]["olmo"]["final"]["qwen-written"]["rows"] == 1
    assert rep["gate2"]["verdict"] in ("met", "not met") and len(rep["gate2"]["cells"]) == 6
    relook = list(csv.DictReader(open(setup / "llm_judge" / "relook_L3.csv", newline="")))
    assert relook == [] or set(relook[0]) == {"row", "text", "source", "letter", "excerpt", "label", "note"}
    assert all(r["label"] == "" for r in relook)


def test_ritiks_and_ai1s_real_l3_kappa_reproduces_nov_3():
    """The kappa this protocol reuses (label_kit.kappa) gives the Nov 3 numbers on the real sheets."""
    a, b = lj.SHEETS["L3"]["human"], lj.SHEETS["L3"]["ai1"]
    if not (a.exists() and b.exists()):
        pytest.skip("the label sheets aren't on this machine (results/labels/, gitignored)")
    res, _ = lk.kappa(a, b)
    assert round(res["private | all"]["kappa"], 3) == 0.627 and round(res["final | user"]["kappa"], 3) == 0.425
