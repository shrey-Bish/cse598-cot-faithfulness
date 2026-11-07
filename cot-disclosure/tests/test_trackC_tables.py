"""C24's tables (agents/trackc_tables.py): the rows carry the summaries' counts and readings, every number is a number,
and the files are written. CPU only, no network; reads the tracked summaries in results/summaries/trackC/."""
import csv
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

from agents import trackc_tables as t  # noqa: E402


def test_points_are_signed_with_a_true_minus():
    assert (t.pts(0.08), t.pts(-0.13), t.pts(0.0)) == ("+8", "−13", "+0")
    assert t.diff({"diff": -0.132, "interval": [-0.226, -0.057]}) == "−13 [−23, −6]"
    assert t.diff({"diff": None, "interval": None}) == ""


def test_the_experiment_rows_match_the_summaries():
    rows = t.experiment_rows()
    at = {(r["experiment"], r["comparison"], r["reviewer"], r["measure"]): r for r in rows}
    c19 = at[("C19", "answer-key sentence − own-working sentence", "Olmo 3.1 32B Instruct", "corrects a wrong answer")]
    s19 = t.load("c19")["main_key_minus_own"][t.OLMO]
    assert (c19["a"], c19["b"], c19["items"]) == (f"{s19['variant_k']} of 53", f"{s19['answer_only_k']} of 53", "53")
    assert c19["a − b"] == t.diff(s19) and c19["decision"].startswith("pre-registered, main")
    c25 = at[("C25", "M1: keep note with its tool sentences stripped − keep note", "Olmo 3.1 32B Instruct",
              "accepts the solver's wrong letter")]
    s25 = t.load("c25")["deciders"][t.OLMO]["M1_stripped_minus_keep"]
    assert c25["a − b"] == t.diff(s25) and s25["reading"] in c25["reading"]
    hop = at[("C25", "hop 2, the keep note (bad lookups)", "the writer (Qwen3 30B Instruct)", "names the tool")]
    assert hop["a"] == t.count(t.load("c25")["source_bad_lookups"]["hop2_keep"])
    c20 = at[("C20", "(b) tag − (a) blind", "Qwen3 30B Instruct", "catches the wrong solver answer")]
    assert c20["a − b"] == t.diff(t.load("c20")["readings"][t.QWEN]["1_tag_minus_blind_catches"])
    c26 = at[("C26", "R2: + tool log − answer only (C26's bad lookups)", "Olmo 3.1 32B Instruct", "corrects a wrong answer")]
    s26 = t.load("c26")["reviewers"][t.OLMO]["R2_plus_tool_log_minus_answer_only"]
    assert c26["a"] == f"{s26['variant_k']} of {s26['variant_n']}" and c26["reading"] == s26["rule"]
    assert {r["experiment"] for r in rows} == {"C19", "C25", "C20", "C26"}
    assert all(r["decision"] for r in rows)


def test_the_pipeline_rows_are_the_summarys_counts():
    rows = t.pipeline_rows()
    s20 = t.load("c20")["pipelines"]
    ship = [r for r in rows if r["rule"].startswith("ship")]
    assert len(ship) == 7 and len(rows) == 7 + 4
    tag = next(r for r in ship if r["pipeline"] == "(b) tag" and r["reviewer"] == "Olmo 3.1 32B Instruct")
    e = s20[f"b_tag | {t.OLMO}"]
    assert (tag["caught"], tag["false alarms"], tag["shipped wrong"]) == (t.count(e["caught"]), t.count(e["false_alarms"]),
                                                                        t.count(e["shipped_wrong"]))
    assert tag["tokens a case"] == f"{e['tokens_per_case']:,.0f}"


def test_the_tables_are_written_and_the_csvs_hold_no_model_text(tmp_path):
    paths = t.main(tmp_path)
    assert sorted(p.name for p in paths) == sorted(["trackC_experiments.md", "trackC_experiments.csv", "trackC_pipelines.md",
                                                    "trackC_pipelines.csv", "at_a_glance_FC.md", "at_a_glance_FC.csv"])
    glance = list(csv.DictReader(open(tmp_path / "at_a_glance_FC.csv")))
    assert [r["finding"] for r in glance] == ["FC1", "FC2", "FC3", "FC4"]
    assert all(r["figure"].startswith("docs/trackC/figures/") for r in glance)
    for p in paths:
        text = p.read_text()
        assert "Proposed answer" not in text and "question" not in text.lower().replace("question_id", "")
