"""Track A's batch 3 plan (finetune/gpu/plan_eval.py): hours per system from Step 2b's reply lengths (cut
runs as a range) and a decoding rate per engine (measured once an evaluation job on that engine has run),
balanced parts under 8 h, the order and dependencies (hf: no vLLM check; vllm: base and prompt-only after
the check; each trained version after its training job), runs already saved, parts already queued, and
what the queue says on Sol. No GPU, no Slurm: the Sol answers are stand-ins."""
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from finetune import eval as ev  # noqa: E402
from finetune.gpu import plan_eval as pe  # noqa: E402

TRAIN = {"lora": "101", "tags": "102", "lora_tags": "103", "lora_attn3": "104"}
LENGTHS = {1308: 10000.0}                                # every question: 10,000 reply tokens (overall mean)


def sol(**kw):
    base = {"queued": lambda j: "PENDING", "ended": lambda j: None, "job_count": lambda: 5, "trained": lambda v: False,
            "check": lambda: None, "rate": lambda e: None, "saved": lambda s: frozenset(), "in_queue": lambda: {}}
    return {**base, **kw}


def lines_for(res, system):
    return [x for x in pe.commands(res) if "submit.sh eval" in x and f"-- {system} " in x + " "]


def test_the_hf_engine_needs_no_vllm_check_and_runs_every_version():
    res = pe.plan(None, TRAIN, sol(job_count=lambda: 0), LENGTHS)
    assert res["engine"] == "hf" and res["rate"]["range"] == list(pe.PRIORS["hf"])
    assert [s["system"] for s in res["systems"]] == ["base", "prompt_only", "lora", "tags", "lora_tags", "lora_attn3"]
    assert "--dependency" not in lines_for(res, "base")[0] and "--engine" not in lines_for(res, "base")[0]
    assert "--dependency=afterok:103 -- lora_tags " in lines_for(res, "lora_tags")[0]
    s = res["systems"][0]
    assert s["tokens"] == [9_300_000] * 3 and s["hours"][2] == round(9.3e6 / 70 / 3600, 2)
    assert all(p["estimate"] * 1.3 <= 8 and p["limit_min"] <= 480 for p in s["parts"])
    est = [p["estimate"] for p in s["parts"]]
    assert len(est) == len(s["parts"]) > 1 and max(est) - min(est) < 0.1                  # every n-th run: balanced


def test_vllm_waits_for_its_check_and_a_failed_check_leaves_the_tag_versions_out():
    res = pe.plan("100", TRAIN, sol(job_count=lambda: 0), LENGTHS, engine="vllm")
    s = res["systems"][0]
    assert s["hours"] == [round(9.3e6 / 1500 / 3600, 2), round(9.3e6 / 1000 / 3600, 2), round(9.3e6 / 500 / 3600, 2)]
    assert len(s["parts"]) == 1 and s["parts"][0]["limit_min"] == 30 * -(-s["parts"][0]["estimate"] * 78 // 30)
    assert "--dependency=afterok:100 -- base --engine vllm" in lines_for(res, "base")[0]
    assert "--dependency=afterok:100:103 -- lora_tags --engine vllm" in lines_for(res, "lora_tags")[0]
    res = pe.plan("100", TRAIN, sol(check=lambda: False), LENGTHS, engine="vllm")
    assert {s["system"] for s in res["systems"]} == {"base", "prompt_only", "lora", "lora_attn3"}
    assert sum("hf engine" in n for n in res["notes"]) == 2
    res = pe.plan("100", TRAIN, sol(queued=lambda j: "", ended=lambda j: "FAILED"), LENGTHS, engine="vllm")
    assert res["systems"] == [] and "vllm_check job 100 ended FAILED" in res["notes"][0]
    assert pe.plan(None, TRAIN, sol(), LENGTHS, engine="vllm")["notes"][0].startswith("--engine vllm needs --vllm-check")


def test_long_systems_are_split_into_parts_of_every_nth_run():
    res = pe.plan(None, TRAIN, sol(job_count=lambda: 0), {1308: 20000.0})           # 18.6M tokens: 73.8 h at 70/s
    s = res["systems"][0]
    n = len(s["parts"])                    # a part fits 8 h / 1.3 at 70/s: at most 77 runs of 20,000, so 13 parts
    assert n == 13 and all(p["part"][1] == n for p in s["parts"])
    assert [x.split(" -- ")[1].split()[:2] for x in lines_for(res, "base")][:2] == [["base", f"1/{n}"], ["base", f"2/{n}"]]
    assert sum(len(ev.jobs((k, n))) for k in range(1, n + 1)) == 930


def test_finished_dependencies_drop_out_and_failures_stop_their_systems():
    done = {"101": "COMPLETED", "102": "TIMEOUT"}
    res = pe.plan(None, TRAIN, sol(queued=lambda j: "RUNNING" if j in ("103", "104") else "",
                                   ended=lambda j: done.get(j), trained=lambda v: v == "lora"), LENGTHS)
    assert "--dependency" not in lines_for(res, "lora")[0]
    assert lines_for(res, "tags") == [] and any("tags: train job 102 ended TIMEOUT" in n for n in res["notes"])
    assert "--dependency=afterok:103 -- lora_tags" in lines_for(res, "lora_tags")[0]


def test_runs_saved_and_parts_queued_are_left_out_of_a_new_plan():
    all_ids = frozenset(ev.job_id("prompt_only", j) for j in ev.jobs())
    first_half = frozenset(ev.job_id("base", j) for j in ev.jobs()[:465])
    res = pe.plan(None, TRAIN, sol(saved=lambda s: {"base": first_half, "prompt_only": all_ids}.get(s, frozenset()),
                                   in_queue=lambda: {"lora": {(1, 4), (2, 4)}, "tags": {None}}), LENGTHS)
    by = {s["system"]: s for s in res["systems"]}
    assert by["base"]["saved"] == 465 and by["base"]["tokens"][0] == 465 * 10000
    assert "prompt_only" not in by and "prompt_only: all 930 runs saved" in res["notes"]
    assert [p["part"] for p in by["lora"]["parts"]] == [[3, 4], [4, 4]]                   # N kept, queued parts left out
    assert "tags" not in by and any(n.startswith("tags: a whole-system job") for n in res["notes"])
    assert "base" in " ".join(lines_for(res, "base")) and "465 runs saved" in lines_for(res, "base")[0]


def test_queued_evaluations_from_sacct(monkeypatch):
    out = "\n".join(["trackA-eval|sbatch -A x -t 8:00 /r/cot-disclosure/finetune/gpu/sol/eval.sbatch base 3/10",
                     "trackA-eval|sbatch -A x -t 4:00 --dependency=afterok:5 /r/eval.sbatch lora",
                     "trackA-eval|sbatch -A x /r/eval.sbatch base 4/10 --engine vllm",
                     "trackB-qwen3-8b|sbatch -A x /r/trackb_qwen8b.sbatch --engine hf"])
    monkeypatch.setattr(pe, "_run", lambda cmd: out)
    assert pe.queued_evals() == {"base": {(3, 10), (4, 10)}, "lora": {None}}
    monkeypatch.setattr(pe, "_run", lambda cmd: None)
    assert pe.queued_evals() is None


def test_step2b_lengths_count_runs_cut_at_voyagers_cap_as_a_range(tmp_path):
    rows = [{"item_id": 1, "status": "ok", "finish_reason": "stop", "completion_tokens": 4000, "prompt_tokens": 768},
            {"item_id": 1, "status": "ok", "finish_reason": "length", "completion_tokens": 16000, "prompt_tokens": 768},
            {"item_id": 2, "status": "ok", "finish_reason": "stop", "completion_tokens": 22000, "prompt_tokens": 768,
             "continued": ["length"]}]
    p = tmp_path / "runs.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    got = pe.step2b_lengths(p)
    assert got[1] == ((4000 + 16000) / 2, (4000 + 22000) / 2, (4000 + 32000) / 2) and got[2] == (22000.0,) * 3
    real = pe.step2b_lengths()
    lo, mid, hi = (sum(v[i] for v in real.values()) for i in range(3))
    assert lo < mid < hi                                                                # the tracked Step 2b summary


def test_the_measured_rate_per_engine_and_part_files_and_the_submit_limit(tmp_path):
    res = pe.plan(None, TRAIN, sol(rate=lambda e: 200.0, job_count=lambda: 8), LENGTHS)
    assert res["rate"]["range"] == [160.0, 240.0] and res["queue"]["room"] == 2
    cmds = pe.commands(res)
    assert "measured 200" in cmds[0] and sum(not x.startswith("#") for x in cmds) == 2
    assert all(x.startswith("# later (MaxSubmitPU)") for x in cmds[3:] if "submit.sh" in x)
    out = tmp_path / "eval"
    out.mkdir()
    jobs = [{"system": "base", "part": [2, 10], "engine": "continuous", "started_utc": "2026-10-28T10:00:00+00:00",
             "ended_utc": "2026-10-28T11:00:00+00:00"},
            {"system": "base", "part": None, "started_utc": "2026-10-28T10:00:00+00:00",          # a vLLM job
             "ended_utc": "2026-10-28T11:00:00+00:00"}]
    (out / "eval_jobs.jsonl").write_text("".join(json.dumps(j) + "\n" for j in jobs))
    (out / "eval_base_p2of10_runs.jsonl").write_text("".join(json.dumps(
        {"timestamp_utc": f"2026-10-28T{h}:30:00+00:00", "completion_tokens": 360_000}) + "\n" for h in ("10", "12")))
    (out / "eval_base_runs.jsonl").write_text(json.dumps(
        {"timestamp_utc": "2026-10-28T10:30:00+00:00", "completion_tokens": 3_600_000}) + "\n")
    assert pe.measured_rate(out, "hf") == 100.0               # only its part's run inside the job's hour counts
    assert pe.measured_rate(out, "vllm") == 1000.0
    assert pe.saved_runs("base", tmp_path / "nowhere") == frozenset()
