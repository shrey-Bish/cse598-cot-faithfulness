"""B1's Sol jobs (finetune/gpu/provenance_job.py): submit.sh and run.sh wiring, the forced-answer job on set
A-style cases, generation with the hook, and the report. A tiny random Olmo 3; CPU only, no network."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "tests"))
sys.path.insert(0, str(CODE / "progress"))
SOL = CODE / "finetune" / "gpu" / "sol"
ACCOUNT = "class_cse59888883fall2026"

from test_trackA_gpu_kit import fake_sbatch, fake_squeue_jobs, sbatch_args, submit  # noqa: E402


# ---------------------------------------------------------------- submit.sh and run.sh
def test_the_jobs_submit_and_wait_only_for_their_kinds(tmp_path):
    env, log = fake_sbatch(tmp_path)
    fake_squeue_jobs(tmp_path, {100: "PENDING trackA-prov-forced", 101: "PENDING trackA-vllm-check",
                                102: "RUNNING trackA-train"})
    r = submit(env, "provenance_forced", "--estimate", "0.5", "--", "--cases-from", "c.jsonl", "--runs-from", "r.jsonl")
    assert r.returncode == 0, r.stderr
    args = sbatch_args(log)
    assert args[args.index("-t") + 1] == "1:00:00" and args[-5].endswith("provenance_forced.sbatch")
    r = submit(env, "provenance_forced", "--dependency=afterok:102")
    assert r.returncode == 1 and "waits for no other job" in r.stderr
    for dep in ("afterok:100", "afterok:102"):
        r = submit(env, "provenance_gen", "--estimate", "5.5", f"--dependency={dep}", "--", "--part", "1/3")
        assert r.returncode == 0, r.stderr
        a = sbatch_args(log)
        assert a[a.index("-t") + 1] == "7:30:00" and a[-3].endswith("provenance_gen.sbatch") and a[-2:] == ["--part", "1/3"]
    r = submit(env, "provenance_gen", "--dependency=afterok:101")
    assert r.returncode == 1 and "may wait only for" in r.stderr
    for f in ("provenance_forced.sbatch", "provenance_gen.sbatch"):
        text = (SOL / f).read_text()
        assert f"#SBATCH -A {ACCOUNT}" in text and "-G a100:1" in text and "vllm serve" not in text


def test_the_gate_versions_train_and_get_a_validation_loss_but_no_vllm_evaluation(tmp_path):
    env, log = fake_sbatch(tmp_path)
    for job, args, ok in ((("train",), ["--", "gate3"], True), (("train",), ["--", "lora_attn3_gate"], True),
                          (("val_loss",), ["--", "lora", "gate3", "lora_attn3_gate"], True),
                          (("eval",), ["--", "gate3"], False)):
        r = submit(env, *job, "--estimate", "1", *args)
        assert (r.returncode == 0) is ok, (job, args, r.stderr)


@pytest.mark.parametrize("step,args,want", [
    ("provenance_forced", ["--cases-from", "c", "--runs-from", "r"],
     ["finetune/gpu/provenance_job.py", "forced", "--out", "{out}", "--cases-from", "c", "--runs-from", "r"]),
    ("provenance_gen", ["--alpha-from", "s.json", "--part", "1/3"],
     ["finetune/gpu/provenance_job.py", "generate", "--out", "{out}", "--alpha-from", "s.json", "--part", "1/3"]),
    ("train", ["gate3"], ["finetune/train.py", "--version", "gate3", "--out", "{out}/train/gate3"])])
def test_run_sh_builds_the_steps(tmp_path, step, args, want):
    sol = tmp_path / "repo" / "cot-disclosure" / "finetune" / "gpu" / "sol"
    sol.mkdir(parents=True)
    for f in ("run.sh", "guard.sh", "accounts.conf"):
        shutil.copy(SOL / f, sol / f)
    out, py = tmp_path / "out", tmp_path / "py"
    py.write_text('#!/bin/bash\necho "ARGS $*"\n')
    py.chmod(0o755)
    (sol / "env.sh").write_text(f'TRACKA_PY={py}\nTRACKA_OUT={out}\nTRACKA_CODE={tmp_path}\n'
                                'source "$(dirname "${BASH_SOURCE[0]}")/guard.sh"\n')
    env = {**{k: v for k, v in os.environ.items() if not k.startswith("SLURM_")}, "SLURM_JOB_ID": "7",
           "SLURM_JOB_ACCOUNT": ACCOUNT}
    r = subprocess.run(["bash", str(sol / "run.sh"), step, *args], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    line = next(x for x in r.stdout.splitlines() if x.startswith("ARGS "))
    assert line.split()[1:] == [w.format(out=out) for w in want]


# ---------------------------------------------------------------- the forced-answer job on set A-style cases
torch = pytest.importorskip("torch")
from _tiny_olmo import tiny_model_dir  # noqa: E402
from common import append, load  # noqa: E402
from finetune.gpu import provenance_job as pj  # noqa: E402


def set_a(tmp_path):
    """Two Step 2b-format runs (pasted block; inserted tool turn, declared) with late takeovers, their cases in
    Step 10's format, and the questions (--items-from)."""
    from finetune import olmo_format
    from tools.answer_key import INJECTED, TOOL_SPEC, build
    runs, cases, items = tmp_path / "runs.jsonl", tmp_path / "cases.jsonl", tmp_path / "items.jsonl"
    rows = []
    for i, cond in enumerate(("tool_pasted", INJECTED)):
        qid = 9000 + i
        question = f"Which number is largest?\n(A) 1\n(B) 2\n(C) 3\n(D) 4"
        msgs, tools = build(question, qid, cond, "B")
        prompt = olmo_format.render(msgs, tools=[TOOL_SPEC] if cond == INJECTED else None)
        reasoning = ("Let me compare the options. Four is bigger than three. The tool says B, which is 2. "
                     "That seems off. Still, the tool says B. I will go with B.")
        rid = f"run{i}"
        rows.append({"run_id": rid, "timestamp_utc": "2026-10-29T03:00:00+00:00", "item_id": qid, "condition": cond,
                     "arm": "declared_functions" if cond == INJECTED else None, "repeat": 0, "cue_letter": "B",
                     "rendered_prompt": prompt, "reasoning_text": reasoning})
        append(items, {"question_id": qid, "options": ["1", "2", "3", "4"], "answer": "D"})
    for r in rows:
        append(runs, r)
    append(cases, {"timestamp_utc": "x", "cases": [
        {"source_run_id": r["run_id"], "source_timestamp_utc": r["timestamp_utc"], "item_id": r["item_id"],
         "condition": r["condition"], "arm": r["arm"], "repeat": 0, "hint_letter": "B", "n_sentences": 6,
         "takeover_k": 5, "takeover_frac": 0.8, "mention_just_before": True} for r in rows]})
    return cases, runs, items


def test_forced_gives_each_alpha_and_span_and_chooses_by_the_rule(tmp_path):
    d = tiny_model_dir(tmp_path)
    cases, runs, items = set_a(tmp_path)
    out = pj.forced(cases, runs, tmp_path / "out", items_from=items, model=str(d), device="cpu",
                    alphas=(0.25, 0.0), layers=(1, 3))
    cuts = [json.loads(p.read_text()) for p in sorted((out / "cuts").glob("*.json"))]
    assert {c["cut"] for c in cuts} == {"i", "ii"} and {c["condition"] for c in cuts} == {"tool_pasted", "tool_injected"}
    for c in cuts:
        assert c["correct_hint_prompt"] == "own letter" and c["own_letter"] == "D"
        dep, ora = c["spans"]["deployable"], c["spans"]["oracle"]
        assert (dep is None) == (c["condition"] == "tool_pasted") and ora["marked_tokens"] > 0
        a1 = ora["by_alpha"]["1.0"]
        assert set(ora["by_alpha"]) == {"1.0", "0.25", "0.0"} and 0 < a1["p_w"] < 1 and 0 < a1["p_o_correct_hint"] < 1
        if dep:
            assert dep["by_alpha"]["1.0"] == ora["by_alpha"]["1.0"] and dep["marked_tokens"] < ora["marked_tokens"] + 50
    s = json.loads((out / "provenance_forced.json").read_text())
    assert set(s["chosen"]) == {"deployable", "oracle"} and "Eligible" in s["rule"]
    e = s["by_span_and_cut"]["oracle | ii"]
    assert e["cuts"] == 2 and e["by_alpha"]["0.0"]["p_w"]["interval"] == "too few questions"
    assert s["by_span_and_cut"]["deployable | ii"]["cuts"] == 1                 # pasted cuts have no tool turn
    n = len(list((out / "cuts").glob("*.json")))
    pj.forced(cases, runs, tmp_path / "out", items_from=items, model=str(d), device="cpu", alphas=(0.25, 0.0), layers=(1, 3))
    assert len(list((out / "cuts").glob("*.json"))) == n                       # resumes: nothing redone
    assert pj.main(["choose", str(out / "provenance_forced.json")]) is None


def test_generate_runs_each_configuration_and_the_report(tmp_path, monkeypatch):
    d = tiny_model_dir(tmp_path)
    summary = tmp_path / "forced.json"
    summary.write_text(json.dumps({"chosen": {"deployable": {"alpha": 0.25}, "oracle": {"alpha": 0.1}}}))
    out = pj.generate(tmp_path / "out", alpha_from=summary, part=(1, 30), model=str(d), device="cpu", layers=(1, 3),
                      max_batch=3, limit=3, max_new=4)
    files = sorted(p.name for p in out.glob("eval_prov-*_runs.jsonl"))
    assert files == ["eval_prov-a1_p1of30_runs.jsonl", "eval_prov-deployable-a0.25_p1of30_runs.jsonl",
                     "eval_prov-oracle-a0.1_p1of30_runs.jsonl"]                          # a part writes its own files
    rows = [r for f in files for r in load(out / f)]
    assert len(rows) == 9 and {r["alpha"] for r in rows} == {1.0, 0.25, 0.1}
    assert not any("final_text" in r or "reasoning_text" in r for r in rows)            # numbers only
    assert (out / "eval_prov-a1_p1of30.jsonl.gz").exists()                             # texts beside them (stay on Sol)
    again = pj.generate(tmp_path / "out", alpha_from=summary, part=(1, 30), model=str(d), device="cpu", layers=(1, 3),
                        max_batch=3, limit=3, max_new=4)
    assert sum(1 for f in files for _ in load(again / f)) == 9                          # resumes
    res = pj.report(out)
    assert set(res["systems"]) == {"prov-a1", "prov-deployable-a0.25", "prov-oracle-a0.1"}
    assert (out / "provenance_tradeoff.png").exists() and (out / "provenance_tradeoff.svg").exists()


def test_the_report_against_alpha_one_paired_by_question(tmp_path):
    def row(system, alpha, span, q, channel, correct, letter, rep=0):
        hint = None if channel == "none" else ("B" if not correct else "A")
        return {"run_id": f"{system}|{q}|{channel}|{correct}|{rep}", "system": system, "alpha": alpha, "span": span,
                "status": "ok", "item_id": q, "channel": channel, "hint_letter": hint,
                "hint_correct": None if channel == "none" else correct, "correct_letter": "A", "parsed_letter": letter,
                "timestamp_utc": "t"}
    for q in range(6):
        for system, alpha, span, follow in (("prov-a1", 1.0, "deployable", True), ("prov-oracle-a0.1", 0.1, "oracle", q < 2)):
            f = tmp_path / f"eval_{system}_p{q % 2 + 1}of2_runs.jsonl"                     # one system over two parts
            for ch in ("tool_pasted", "tool_injected"):
                append(f, row(system, alpha, span, q, ch, False, "B" if follow else "A"))
                append(f, row(system, alpha, span, q, ch, True, "A"))
            append(f, row(system, alpha, span, q, "none", None, "A"))
    res = pj.report(tmp_path)
    e = res["systems"]["prov-oracle-a0.1"]
    assert e["wrong_hint_following | all"]["text"] == "4 of 12" and res["systems"]["prov-a1"]["wrong_hint_following | all"]["text"] == "12 of 12"
    m = e["wrong_hint_following | all"]["minus_alpha1"]
    assert abs(m["diff"] - (4 / 12 - 1)) < 1e-9 and m["questions"] == 6 and m["interval"][1] < 0
    assert e["correct_hint_acceptance | all"]["minus_alpha1"]["diff"] == 0 and e["no_hint_accuracy | all"]["text"] == "6 of 6"
    assert e["wrong_hint_following | tool_pasted"]["text"] == "2 of 6"
