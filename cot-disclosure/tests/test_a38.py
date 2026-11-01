"""A38 (finetune/gpu/provenance_job.py, Oct 31): prompt_only's note with B1's deployable span, against each alone, on
the same Hugging Face stack. The configurations and their runs (inserted tool turn only; the note in the prompt), B1's
rule as A38's gate, A38's reading on planted runs, and the plan's two gates. No GPU, no network."""
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))
sys.path.insert(0, str(CODE / "tests"))

from common import append, load  # noqa: E402
from finetune.gpu import provenance_job as pj  # noqa: E402

Q = 10


def test_the_note_configurations_and_the_note_in_their_prompts():
    from finetune import eval as ev
    assert pj.note_configs({"deployable": 0.25, "oracle": 0.5}) == [("prov-note-a1-v2", "deployable", 1.0),
                                                                   ("prov-note-deployable-a0.25-v2", "deployable", 0.25)]
    q = ev.questions()[0]
    j = ev.job(q, "inserted_study_guide", q["hint_letters"][0], 0)
    for system in ("prov-note-a1-v2", "prov-note-deployable-a0.25-v2", "prompt_only"):
        assert ev.NOTE in ev.renderer(system)(j["messages"], j["tools"])
    for system in ("prov-a1-v2", "prov-deployable-a0.25-v2", "base"):
        assert ev.NOTE not in ev.renderer(system)(j["messages"], j["tools"])
    jobs, pasted = pj.gen_jobs(wordings=pj.NOTE_WORDINGS)
    assert len(jobs) == 30 * 4 and {x["wording"] for x in jobs} == {"inserted_study_guide", "none"} and not pasted


def test_generate_with_the_note_writes_its_two_configurations(tmp_path):
    from _tiny_olmo import tiny_model_dir
    d = tiny_model_dir(tmp_path)
    summary = tmp_path / "forced.json"
    summary.write_text(json.dumps({"chosen": {"deployable": {"alpha": 0.25}, "oracle": {"alpha": 0.5}}}))
    out = pj.generate(tmp_path / "out", alpha_from=summary, part=(1, 30), model=str(d), device="cpu", layers=(1, 3),
                      max_batch=2, limit=2, max_new=4, note=True)
    files = sorted(p.name for p in out.glob("eval_prov-*_runs.jsonl"))
    assert files == ["eval_prov-note-a1-v2_p1of30_runs.jsonl", "eval_prov-note-deployable-a0.25-v2_p1of30_runs.jsonl"]
    rows = [r for f in files for r in load(out / f)]
    assert len(rows) == 4 and {r["channel"] for r in rows} <= {"tool_injected", "none"} and {r["alpha"] for r in rows} == {1.0, 0.25}


def row(system, alpha, q, channel, correct, letter):
    hint = None if channel == "none" else ("B" if not correct else "A")
    return {"run_id": f"{system}|{q}|{channel}|{correct}", "system": system, "alpha": alpha, "span": "deployable",
            "status": "ok", "item_id": q, "channel": channel, "hint_letter": hint,
            "hint_correct": None if channel == "none" else correct, "correct_letter": "A", "parsed_letter": letter,
            "timestamp_utc": "t"}


def plant(d, follows, accept=None, nohint=None, channels=("tool_pasted", "tool_injected")):
    """follows: {system: (alpha, questions on which the wrong inserted hint is followed)}."""
    accept, nohint = accept or {}, nohint or {}
    for system, (alpha, fol) in follows.items():
        f = d / f"eval_{system}_p1of2_runs.jsonl"
        chs = ("tool_injected",) if system.startswith(pj.NOTE) else channels
        for q in range(Q):
            for ch in chs:
                append(f, row(system, alpha, q, ch, False, "B" if q in fol else "A"))
                append(f, row(system, alpha, q, ch, True, "C" if q in accept.get(system, ()) else "A"))
            append(f, row(system, alpha, q, "none", None, "C" if q in nohint.get(system, ()) else "A"))


ALL = set(range(Q))


@pytest.mark.parametrize("dep,accept,nohint,want", [
    (set(range(3)), {}, {}, "works"),
    (set(range(3)), {"prov-deployable-a0.25-v2": {0, 1}}, {}, "ignores tools"),
    (set(range(3)), {}, {"prov-deployable-a0.25-v2": {0}}, "costs accuracy"),
    (ALL - {0}, {}, {}, "no effect")])
def test_b1_s_rule(tmp_path, dep, accept, nohint, want):
    plant(tmp_path, {"prov-a1-v2": (1.0, ALL), "prov-deployable-a0.25-v2": (0.25, dep)}, accept, nohint)
    v = pj.b1_verdict(pj.report(tmp_path))
    assert v["reading"] == want and v["system"] == "prov-deployable-a0.25-v2" and v["channel"] == "tool_injected"


@pytest.mark.parametrize("combined,want", [
    (set(), "adds to both"),
    (set(range(5)), "no better than the better one alone"),
    (ALL, "worse than one alone")])
def test_a38_reads_the_combination_against_each_alone(tmp_path, combined, want):
    plant(tmp_path, {"prov-a1-v2": (1.0, ALL), "prov-deployable-a0.25-v2": (0.25, set(range(5))),
                     "prov-note-a1-v2": (1.0, set(range(6))), "prov-note-deployable-a0.25-v2": (0.25, combined)})
    res = pj.a38(tmp_path)
    assert res["b1"]["reading"] == "works" and res["reading"] == want, res
    assert res["runs"]["combined"] == Q * 3 and res["systems"]["note"] == "prov-note-a1-v2"
    assert (tmp_path / "a38_report.json").exists()


def test_a38_costs_are_read_and_it_does_not_run_unless_b1_works(tmp_path):
    plant(tmp_path, {"prov-a1-v2": (1.0, ALL), "prov-deployable-a0.25-v2": (0.25, set(range(5))),
                     "prov-note-a1-v2": (1.0, set(range(6))), "prov-note-deployable-a0.25-v2": (0.25, set())},
          accept={"prov-note-deployable-a0.25-v2": {0, 1, 2}})
    assert pj.a38(tmp_path)["reading"] == "adds, costs acceptance"
    other = tmp_path / "no_effect"
    other.mkdir()
    plant(other, {"prov-a1-v2": (1.0, ALL), "prov-deployable-a0.25-v2": (0.25, ALL)})
    assert pj.a38(other)["reading"].startswith("not run: B1 reads 'no effect'")


def test_the_plan_s_second_gate_is_b1_s_verdict(tmp_path):
    summary = tmp_path / "forced.json"
    summary.write_text(json.dumps({"chosen": {"deployable": {"alpha": 0.25}, "oracle": {"alpha": 0.5}}}))
    gen = tmp_path / "provenance_gen"
    gen.mkdir()
    b = tmp_path / "provenance_bench"
    b.mkdir()
    (b / "bench.json").write_text(json.dumps({"alphas": [1.0], "projection": {"new_tokens_per_s": 60.0},
                                              "engines": [{"engine": "before", "alpha": 1.0, "tokens_per_s": 30.0},
                                                          {"engine": "after", "alpha": 1.0, "tokens_per_s": 60.0}]}))
    plant(gen, {"prov-a1-v2": (1.0, ALL), "prov-deployable-a0.25-v2": (0.25, ALL)})
    with pytest.raises(SystemExit, match="A38 runs only if B1 works"):
        pj.plan(tmp_path, summary, note=True)
    works = tmp_path / "w"
    (works / "provenance_gen").mkdir(parents=True)
    (works / "provenance_bench").mkdir()
    (works / "provenance_bench" / "bench.json").write_text((b / "bench.json").read_text())
    plant(works / "provenance_gen", {"prov-a1-v2": (1.0, ALL), "prov-deployable-a0.25-v2": (0.25, set(range(3)))})
    p = pj.plan(works, summary, note=True)
    assert p["runs_left"] == 240 and all(" --note --part " in line for line in p["lines"])
