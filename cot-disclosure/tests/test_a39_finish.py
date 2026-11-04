"""A39's reader on the day its runs finish (Nov 4): finetune/a39.py --report end to end on synthetic files of the real
shape (tests/test_a39_synthetic.py; no real A39 file is read), then what a real finish could leave: a part file
missing, a run saved twice (a part and its sweep), a failed run, a run cut at the cap, a system with no inserted-turn
runs, empty or cut files, the 30 with too few questions. Beside it, the amendment's no-answer counts and its "no-answer
imbalance" label (the A39 log's section 9.1), and that no job Sol has queued loads a39.py. CPU only, no network."""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))
sys.path.insert(0, str(CODE / "tests"))

pytest.importorskip("transformers")

import common  # noqa: E402
from common import load  # noqa: E402
from finetune import a39, gate3  # noqa: E402
from finetune import eval as ev  # noqa: E402
from finetune.gpu import provenance_job as pj  # noqa: E402
from test_a39_synthetic import PROFILE, build, expected, failed  # noqa: E402

A38 = {"adds to both", "adds, costs acceptance", "adds, costs accuracy", "worse than one alone",
       "no better than the better one alone"}
B1 = {"works", "ignores tools", "costs accuracy", "no effect", "worse"}
R2 = {"fewer than the instruction", "more", "no difference detected"}
FEW = "too few questions"


@pytest.fixture(autouse=True)
def quick_bootstrap(monkeypatch):
    """The readings' bootstraps at 400 resamples (seed 0, as the report's); the report itself uses 20,000."""
    monkeypatch.setattr(ev, "boot_diff", lambda a, b: common.boot_diff(a, b, n=400))
    monkeypatch.setattr(ev, "boot_mean", lambda g: common.boot_mean(g, n=400))


def diffs(res):
    """Every difference the report holds: [(where, {diff, interval, questions, no_answer})]."""
    out = []
    for s, e in res["r1"].items():
        out += [(f"r1 {s} {k}", e[k]) for k in ("following_vs_base", "nohint_accuracy_vs_base", "hiding_vs_base",
                                                 "acceptance_vs_base")]
    for s, e in res["r2"].items():
        out += [(f"r2 {s} {k}", e[k]) for k in ("following", "acceptance", "accuracy")]
    for s, e in res["r3"].items():
        out += [(f"r3 {s} minus {p} {m}", e[f"minus {p}"][m]) for p in e["against"] if f"minus {p}" in e
                for m in ("following", "acceptance", "accuracy")]
    out += [(f"r4 {k}", res["r4"][k]) for k in ("following", "acceptance", "accuracy") if k in res["r4"]]
    return out


def report(out, qset="e2"):
    res = a39.report(out, qset)
    return res, a39.text(res)


def path(out, system, part=None, qset="e2"):
    return Path(out) / f"{ev.stem(system, part, qset, 'a39')}_runs.jsonl"


def ids(out, system, qset="e2"):
    return {r["run_id"] for r in a39.systems(out, qset).get(system, []) if "shared_from" not in r}


# ---------------------------------------------------------------- end to end
@pytest.fixture(scope="module")
def finished(tmp_path_factory):
    """E2 and the 30 in one folder, as $TRACKA_OUT/a39 holds them (both sets, every shape, a few retried runs)."""
    out = tmp_path_factory.mktemp("a39")
    build(out, "e2", flaky=0.02)
    build(out, "mmlupro_30", flaky=0.02)
    (out / "eval_jobs.jsonl").write_text('{"system": "base", "part": [1, 4]}\n')    # eval_job's job rows: not runs
    return out


@pytest.mark.parametrize("qset,n", [("e2", 120), ("mmlupro_30", 30)])
def test_the_report_reads_every_part_and_gives_r1_to_r4(finished, qset, n, capsys):
    a39.main(["--report", "--out", str(finished), "--qset", qset])
    res = json.loads((finished / f"a39_{qset}.json").read_text())
    text = capsys.readouterr().out
    assert res["questions"] == n and set(res["systems"]) == set(ev.A39_SYSTEMS)
    assert res["complete"] is True
    assert {s: (e["expected"], e["ok"], e["missing"], e["not_run"]) for s, e in res["completeness"].items()} == {
        s: (len(w), len(w), 0, 0) for s, w in expected(qset).items()}
    for s in ev.A39_SYSTEMS:                                                   # a wrapper system: its own 4, 8 shared
        assert (res["systems"][s]["runs"], res["systems"][s]["shared"]) == (12 * n, 8 * n if s in ev.SHARED else 0)
    assert set(res["r1"]) == set(ev.A39_SYSTEMS) - {"base"} and set(res["r2"]) == set(ev.A39_SYSTEMS) - {"prompt_only"}
    for e in res["r1"].values():                                               # R1: gate3.py's own verdict
        assert e["verdict"] in ("passes", "fails") and e == {**e, **gate3.verdict(e)}
    assert {e["reading"] for e in res["r2"].values()} <= R2
    assert set(res["r3"]) == {"lora_note", "wrap_note", "lora_wrap"} and {e["reading"] for e in res["r3"].values()} <= A38
    assert res["r4"]["reading"] in B1 and res["r4"]["channel"] == "inserted"
    assert res["r4"]["reading"] == pj.b1_reading(res["r4"]["following"], res["r4"]["acceptance"], res["r4"]["accuracy"])
    check = res["r4"]["pasted_check"]                                          # the shared runs: exactly 0
    assert check["exactly_zero"] is True and check["following_minus_base"]["diff"] == 0
    assert res["r4"]["accuracy"]["diff"] == 0                                  # wrap's no-hint runs are base's
    for where, d in diffs(res):                                                # each side's no-answer count, beside
        assert set(d["no_answer"]) == {"a", "b", "gap", "imbalance"}, where
    for s in ev.SHARED:                                                        # the amendment's 9.2, said beside
        assert "diluted by design" in res["r1"][s]["note"] and "diluted by design" in res["r2"][s]["note"]
    assert "note" not in res["r1"]["lora"]
    read = {p.name for s in ev.A39_SYSTEMS for p in ev.runs_files(finished, s, qset, "a39")}   # every file read, listed
    assert read <= set(res["files"]) == {p.name for p in finished.glob("eval_*_runs.jsonl")}
    assert not any(f["unreadable_lines"] for f in res["files"].values())
    for word in ("R1", "R2", "R3", "R4", "no answer", "complete"):
        assert word in text
    assert "INCOMPLETE" not in text and "final_text" not in json.dumps(res)


def test_a_no_answer_imbalance_is_labelled_beside_the_reading_and_changes_nothing(tmp_path):
    """Section 9.1: each side's no-answer count on the reading's channel; over 5 points apart: "no-answer imbalance"."""
    build(tmp_path, "e2", n=20, profile={"base": {**PROFILE["base"], "no_answer": 0.0},
                                         "prompt_only": {**PROFILE["prompt_only"], "no_answer": 0.0},
                                         "lora": {**PROFILE["lora"], "no_answer": 0.3}})
    res, text = report(tmp_path)
    lora = res["r1"]["lora"]
    na = lora["following_vs_base"]["no_answer"]
    wrong = [r for r in a39.systems(tmp_path, "e2")["lora"] if r["hint_correct"] is False]
    assert na["a"] == {"k": sum(not r["parsed_letter"] for r in wrong), "n": len(wrong)} and na["b"]["k"] == 0
    assert na["gap"] == pytest.approx(na["a"]["k"] / na["a"]["n"]) and na["imbalance"] is True
    assert "following" in lora["no_answer_imbalance"] and "no-answer imbalance" in text
    assert lora["verdict"] == gate3.verdict(lora)["verdict"]                   # the reading itself is unchanged:
    a, b = a39.pick(a39.systems(tmp_path, "e2")["lora"], "following"), a39.pick(a39.systems(tmp_path, "e2")["base"], "following")
    assert lora["following_vs_base"]["diff"] == ev.diff(a[0], b[0], a[1])["diff"]   # answered runs only, as before
    assert res["r1"]["prompt_only"]["no_answer_imbalance"] == []               # 3% against 0%: no label
    line = next(x for x in text.splitlines() if x.strip().startswith("no answer") and "lora" in x)
    assert "no-answer imbalance" in line and f"{na['a']['k']} of {na['a']['n']}" in line


# ---------------------------------------------------------------- what a real finish could leave
@pytest.fixture
def twelve(monkeypatch):
    """E2 cut to its first 12 questions in eval itself, so the jobs, the parts and completeness all agree on them."""
    whole = ev.QSETS["e2"]
    monkeypatch.setitem(ev.QSETS, "e2", lambda: sorted(whole(), key=lambda q: q["item_id"])[:12])


@pytest.fixture
def small(tmp_path, twelve):
    build(tmp_path, "e2")
    return tmp_path


def test_a_missing_part_file_is_reported_not_silently_read_as_complete(small):
    gone = path(small, "lora", (3, 16))
    lost = {r["run_id"] for r in load(gone)}
    gone.unlink()
    res, text = report(small)
    assert lost and res["complete"] is False
    assert res["completeness"]["lora"]["missing"] == len(lost) and res["completeness"]["base"]["missing"] == 0
    assert ids(small, "lora") == expected("e2")["lora"] - lost
    assert "INCOMPLETE" in text and "lora" in text.split("INCOMPLETE")[1].splitlines()[0]
    assert res["r1"]["lora"]["verdict"] in ("passes", "fails", FEW)            # the readings still come


def test_a_run_saved_twice_part_and_sweep_counts_once(small):
    first = load(path(small, "lora", (1, 4)))[0]
    twice = {**first, "parsed_letter": "J" if first["parsed_letter"] != "J" else "I"}
    with open(path(small, "lora"), "a") as f:                                  # the sweep saved it again
        f.write(json.dumps(twice) + "\n")
    rows = a39.systems(small, "e2")["lora"]
    assert len(rows) == len({r["run_id"] for r in rows}) == 12 * 12
    assert [r["parsed_letter"] for r in rows if r["run_id"] == first["run_id"]] == [twice["parsed_letter"]]
    assert report(small)[0]["completeness"]["lora"] == {"expected": 144, "ok": 144, "missing": 0, "not_run": 0}


def test_a_failed_record_in_a_file_that_sorts_later_doesnt_hide_the_run(small):
    """The bench's file (p2of2) sorts after p12of16 and p16of16, whose runs it shares: a not_run record it left must not
    replace a run another part finished (common.latest keeps the last record in file order)."""
    done = load(path(small, "base", (12, 16)))[-1]
    assert path(small, "base", (12, 16)).name < path(small, "base", (2, 2)).name
    with open(path(small, "base", (2, 2)), "a") as f:
        f.write(json.dumps(failed(done)) + "\n")
    assert done["run_id"] in ids(small, "base")
    assert report(small)[0]["completeness"]["base"]["missing"] == 0


def test_a_run_that_only_failed_is_left_out_and_counted(small):
    p = path(small, "lora", (1, 4))
    rows = load(p)
    p.write_text("".join(json.dumps(r) + "\n" for r in [failed(rows[0])] + rows[1:]))
    assert rows[0]["run_id"] not in ids(small, "lora")
    res, text = report(small)
    assert res["completeness"]["lora"] == {"expected": 144, "ok": 143, "missing": 1, "not_run": 1}
    assert res["systems"]["lora"]["runs"] == 143 and "INCOMPLETE" in text


def test_a_run_cut_at_the_cap_is_a_run_with_no_answer(tmp_path, twelve):
    build(tmp_path, "e2", profile={"base": {**PROFILE["base"], "no_answer": 0.15}})
    rows = a39.systems(tmp_path, "e2")["base"]
    capped = [r for r in rows if r["finish_reason"] == "length"]
    assert capped and all(r["parsed_letter"] is None and r["status"] == "ok" for r in capped)
    res = report(tmp_path)[0]
    assert res["systems"]["base"]["no_answer"] == len(capped) and res["completeness"]["base"]["missing"] == 0
    wrong = [r for r in rows if r["hint_correct"] is False]
    assert res["systems"]["base"]["following"]["pooled"]["n"] == sum(r["parsed_letter"] is not None for r in wrong)
    assert res["r1"]["lora"]["following_vs_base"]["no_answer"]["b"]["k"] == sum(r["parsed_letter"] is None for r in wrong)


def test_a_system_with_no_inserted_turn_runs(small):
    for p in ev.runs_files(small, "wrap", "e2", "a39"):                       # no wrap at all
        p.unlink()
    res, text = report(small)
    assert res["r4"] == {"reading": "missing runs"} and res["r3"]["wrap_note"]["reading"] == "missing runs"
    assert res["r3"]["lora_wrap"]["reading"] == "missing runs" and "wrap" not in res["systems"]
    assert res["completeness"]["wrap"]["missing"] == 4 * 12 and "R4" in text and "missing runs" in text
    for p in ev.runs_files(small, "base", "e2", "a39"):                       # base without its inserted turns
        p.write_text("".join(json.dumps(r) + "\n" for r in load(p) if not ev.tool_turn(r)))
    build(small, "e2", systems=("wrap",))
    res, text = report(small)
    assert res["r4"]["reading"] == FEW and res["r4"]["following"]["diff"] is None
    assert res["r4"]["pasted_check"]["exactly_zero"] is True                  # the pasted block is still shared
    assert "inserted" not in res["systems"]["base"]["following"] and "R4" in text


def test_empty_files_and_a_cut_last_line_are_read_around_and_reported(small):
    path(small, "prompt_only", (1, 4)).write_text("")
    (small / "eval_lora_a39_e2_p9of9_runs.jsonl").write_text("")
    p = path(small, "lora_note", (2, 4))
    n = len(load(p))
    with open(p, "a") as f:
        f.write("\n" + '{"run_id": "0123456789abcdef", "experiment": "trackA_a3')      # a blank line, then a cut one
    res, text = report(small)
    assert res["files"][p.name] == {"records": n, "unreadable_lines": [n + 2]}
    assert res["files"]["eval_lora_a39_e2_p9of9_runs.jsonl"] == {"records": 0, "unreadable_lines": []}
    assert res["completeness"]["prompt_only"]["missing"] > 0 and res["completeness"]["lora_note"]["missing"] == 0
    assert "unreadable" in text and p.name in text


def test_the_30_with_fewer_than_5_questions_says_too_few_questions(tmp_path):
    build(tmp_path, "mmlupro_30", n=4)
    res, text = report(tmp_path, "mmlupro_30")
    assert res["questions"] == 4
    assert {e["verdict"] for e in res["r1"].values()} == {FEW} and {e["reading"] for e in res["r2"].values()} == {FEW}
    assert {e["reading"] for e in res["r3"].values()} == {FEW} and res["r4"]["reading"] == FEW
    assert res["r4"]["pasted_check"]["exactly_zero"] == FEW                    # not checked, rather than "False"
    assert all(d["diff"] is None and d["interval"] == FEW for _, d in diffs(res))
    assert res["systems"]["base"]["accuracy"]["clustered"] == FEW and FEW in text and "exactly 0: False" not in text


# ---------------------------------------------------------------- nothing Sol has queued loads a39.py
FROZEN = """agents/__init__.py agents/sol_c13.py client.py detect.py experiments.py finetune/__init__.py
finetune/base_format.py finetune/build_dataset.py finetune/continuation.py finetune/eval.py finetune/generate.py
finetune/gpu/__init__.py finetune/gpu/eval_job.py finetune/gpu/import_check.py finetune/gpu/kit.py
finetune/gpu/provenance_job.py finetune/gpu/sol/a39.sbatch finetune/gpu/sol/a39_1gpu.sbatch finetune/gpu/sol/accounts.conf
finetune/gpu/sol/b20.sbatch finetune/gpu/sol/env.sh finetune/gpu/sol/get_b20.sbatch finetune/gpu/sol/guard.sh
finetune/gpu/sol/run.sh finetune/gpu/vllm_options.py finetune/gpu/vllm_serve_options.txt finetune/hf_engine.py
finetune/make_targets.py finetune/olmo_format.py finetune/provenance.py finetune/run_nohint.py finetune/source_tags.py
finetune/tags_vllm.py finetune/train.py parse.py progress/common.py progress/mmlu_pro_probe.py progress/run_b20.py
progress/sol_b17.py progress/sol_b20.py progress/sol_trackB.py providers/__init__.py providers/base.py
providers/budget.py providers/sol_chat.py providers/sol_hf.py providers/sol_vllm.py tasks.py tools/answer_key.py""".split()
IMPORTS = re.compile(r"^\s*(?:from\s+[\w.]*\s+import\s+[^\n]*\ba39(?:_figures)?\b|import\s+[^\n]*\ba39(?:_figures)?\b)",
                     re.MULTILINE)


def test_no_file_sol_s_queued_jobs_load_imports_a39():
    """The 49 files the jobs queued on Sol (Nov 4) load: none imports finetune/a39.py or tools/a39_figures.py or runs
    them (eval.py only names a39.py in its docstring), so changing them can't change a queued job."""
    assert len(FROZEN) == 49 and all((CODE / f).exists() for f in FROZEN)
    for f in FROZEN:
        text = (CODE / f).read_text()
        assert not IMPORTS.search(text), f
        if not f.endswith(".py"):
            assert "a39.py" not in text and "a39_figures" not in text, f
    mods = ["finetune.gpu.eval_job", "finetune.eval", "finetune.gpu.vllm_options", "finetune.gpu.kit",
            "finetune.generate", "finetune.make_targets", "finetune.continuation", "finetune.olmo_format",
            "finetune.gpu.provenance_job", "sol_b17", "sol_trackB", "agents.sol_c13", "sol_b20", "run_b20"]
    code = ("import sys; sys.path[:0] = [%r, %r]\n" % (str(CODE), str(CODE / "progress"))
            + "".join(f"import {m}\n" for m in mods)
            + "print(any(m.endswith(('a39', 'a39_figures')) for m in sys.modules))")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=CODE)
    assert r.returncode == 0, r.stderr
    assert r.stdout.split() == ["False"]
