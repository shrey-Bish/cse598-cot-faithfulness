"""B1R2 (finetune/gpu/provenance_job.py generate --b1r2; the A39 log's section 13, Nov 4): B1's deployable span against
alpha = 1 on E2, the inserted tool turn only, 2 wrong + 2 correct + 1 no-hint run a question, in its own folder; and
that no vLLM job (A39, B20) imports B1's generation module, so this option can't change a queued job. No GPU, no
network."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))
sys.path.insert(0, str(CODE / "tests"))

from common import load  # noqa: E402
from finetune import eval as ev  # noqa: E402
from finetune.gpu import provenance_job as pj  # noqa: E402

CHOSEN = {"chosen": {"deployable": {"alpha": 0.25}, "oracle": {"alpha": 0.5}}}


def test_b1r2_jobs_are_e2s_inserted_turn_with_two_correct_runs():
    jobs, pasted = pj.b1r2_jobs()
    e2 = [q["item_id"] for q in ev.questions("e2")]
    assert len(e2) == 120 and len(jobs) == 120 * 5 and not pasted
    assert {j["wording"] for j in jobs} == {"inserted_study_guide", "none"}
    for q in e2[:5]:
        mine = [j for j in jobs if j["item_id"] == q]
        kinds = sorted((j["hint_correct"], j["repeat"]) for j in mine if j["wording"] != "none")
        assert kinds == [(False, 0), (False, 1), (True, 0), (True, 1)] and sum(j["wording"] == "none" for j in mine) == 1
    assert len({ev.job_id("prov-a1-v2", j) for j in jobs}) == len(jobs)
    part = pj.b1r2_jobs((1, 40))[0]
    assert len(part) == 15 and {j["item_id"] for j in part} == set(e2[0::40])          # 3 questions a part


def test_b1rs_default_jobs_are_unchanged_by_the_option():
    jobs = pj.gen_jobs()[0]
    assert len(jobs) == 30 * 7                                 # B1: 2 wordings x (2 wrong + 1 correct) + 1 no hint
    assert pj.gen_jobs(correct_runs=1)[0] == jobs


def test_b1r2_configurations_are_alpha_one_and_the_deployable_span():
    assert pj.b1r2_configs({"deployable": 0.25, "oracle": 0.5}) == [("prov-a1-v2", "deployable", 1.0),
                                                                    ("prov-deployable-a0.25-v2", "deployable", 0.25)]
    with pytest.raises(SystemExit, match="alpha = 1"):
        pj.b1r2_configs({"deployable": 1.0})


def test_generate_b1r2_writes_its_own_folder(tmp_path):
    from _tiny_olmo import tiny_model_dir
    d = tiny_model_dir(tmp_path)
    summary = tmp_path / "forced.json"
    summary.write_text(json.dumps(CHOSEN))
    out = pj.generate(tmp_path / "out", alpha_from=summary, part=(1, 40), model=str(d), device="cpu", layers=(1, 3),
                      max_batch=2, limit=2, max_new=4, b1r2=True)
    assert out == tmp_path / "out" / "b1r2" and not (tmp_path / "out" / "provenance_gen").exists()
    files = sorted(p.name for p in out.glob("eval_prov-*_runs.jsonl"))
    assert files == ["eval_prov-a1-v2_p1of40_runs.jsonl", "eval_prov-deployable-a0.25-v2_p1of40_runs.jsonl"]
    rows = [r for f in files for r in load(out / f)]
    e2 = {q["item_id"] for q in ev.questions("e2")}
    assert len(rows) == 4 and {r["item_id"] for r in rows} <= e2 and {r["design"] for r in rows} == {"b1r2"}
    assert {r["alpha"] for r in rows} == {1.0, 0.25} and {r["engine_tag"] for r in rows} == {"v2"}
    for bad in ({"note": True}, {"version": "gate3"}, {"alphas": (0.5,)}):
        with pytest.raises(SystemExit, match="b1r2"):
            pj.generate(tmp_path / "out", alpha_from=summary, model=str(d), device="cpu", b1r2=True, dry_run=True, **bad)


def test_the_cli_takes_b1r2(tmp_path, capsys):
    summary = tmp_path / "forced.json"
    summary.write_text(json.dumps(CHOSEN))
    pj.main(["generate", "--out", str(tmp_path), "--alpha-from", str(summary), "--b1r2", "--part", "1/40", "--dry-run"])
    assert "15 runs x 2 configurations (prov-a1-v2, prov-deployable-a0.25-v2)" in capsys.readouterr().out


def test_no_vllm_job_imports_b1s_generation_module():
    """The Sol jobs queued on Nov 4 (A39's parts: run.sh gives eval_job --engine vllm; B20: sol_b20) load these modules
    and the lazy imports on their vLLM path. None of them loads provenance_job, so --b1r2 can't change them."""
    mods = ["finetune.gpu.eval_job", "finetune.eval", "finetune.gpu.vllm_options", "finetune.gpu.kit",
            "finetune.generate", "finetune.make_targets", "finetune.continuation", "finetune.olmo_format",
            "sol_b17", "sol_trackB", "agents.sol_c13", "sol_b20", "run_b20"]
    code = ("import sys; sys.path[:0] = [%r, %r]\n" % (str(CODE), str(CODE / "progress"))
            + "".join(f"import {m}\n" for m in mods)
            + "print('finetune.gpu.provenance_job' in sys.modules, 'finetune.hf_engine' in sys.modules)")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=CODE)
    assert r.returncode == 0, r.stderr
    assert r.stdout.split() == ["False", "False"]
