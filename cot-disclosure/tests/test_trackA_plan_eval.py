"""Track A's batch 3 plan (finetune/gpu/plan_eval.py): hours per system from Step 2b's reply lengths and
a decoding rate (measured once an evaluation job has run), parts under 8 h, the order and dependencies
(base and prompt-only after the vLLM check; each trained version after its training job), and what
the queue says on Sol. No GPU, no Slurm: the Sol answers are stand-ins."""
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

from finetune.gpu import plan_eval as pe  # noqa: E402

TRAIN = {"lora": "101", "tags": "102", "lora_tags": "103", "lora_attn3": "104"}
LENGTHS = {1308: 10000.0}                                # every question: 10,000 reply tokens (overall mean)


def sol(**kw):
    base = {"queued": lambda j: "PENDING", "ended": lambda j: None, "job_count": lambda: 5, "trained": lambda v: False,
            "check": lambda: None, "rate": lambda: None}
    return {**base, **kw}


def lines_for(res, system):
    return [x for x in pe.commands(res) if "submit.sh eval" in x and f"-- {system} " in x + " "]


def test_everything_queued_keeps_every_dependency():
    res = pe.plan("100", TRAIN, sol(job_count=lambda: 0), LENGTHS)
    assert [s["system"] for s in res["systems"]] == ["base", "prompt_only", "lora", "tags", "lora_tags", "lora_attn3"]
    s = res["systems"][0]
    assert s["tokens"] == 930 * 10000 and s["hours"] == [round(9.3e6 / 1500 / 3600, 2), round(9.3e6 / 500 / 3600, 2)]
    assert s["parts"] == 1 and s["estimate"] * 1.3 <= 8 and s["limit_min"] == 30 * -(-s["estimate"] * 78 // 30)
    assert "--dependency=afterok:100 -- base" in lines_for(res, "base")[0]
    assert "--dependency=afterok:100:103 -- lora_tags" in lines_for(res, "lora_tags")[0]


def test_long_systems_are_split_by_question():
    res = pe.plan("100", TRAIN, sol(job_count=lambda: 0), {1308: 20000.0})          # 18.6M tokens: 10.3 h at 500/s
    s = res["systems"][0]
    assert s["parts"] == 2 and s["estimate"] * 1.3 <= 8
    assert [x.split(" -- ")[1].split()[:2] for x in lines_for(res, "base")] == [["base", "1/2"], ["base", "2/2"]]


def test_finished_dependencies_drop_out_and_failures_stop_their_systems():
    done = {"100": "COMPLETED", "101": "COMPLETED", "102": "TIMEOUT"}
    res = pe.plan("100", TRAIN, sol(queued=lambda j: "RUNNING" if j in ("103", "104") else "",
                                    ended=lambda j: done.get(j), trained=lambda v: v == "lora"), LENGTHS)
    assert "--dependency" not in lines_for(res, "base")[0] and "--dependency" not in lines_for(res, "lora")[0]
    assert lines_for(res, "tags") == [] and any("tags: train job 102 ended TIMEOUT" in n for n in res["notes"])
    assert "--dependency=afterok:103 -- lora_tags" in lines_for(res, "lora_tags")[0]
    res = pe.plan("100", TRAIN, sol(queued=lambda j: "", ended=lambda j: "FAILED"), LENGTHS)
    assert res["systems"] == [] and "vllm_check job 100 ended FAILED" in res["notes"][0]


def test_a_failed_check_leaves_the_tag_versions_out():
    res = pe.plan("100", TRAIN, sol(check=lambda: False), LENGTHS)
    assert {s["system"] for s in res["systems"]} == {"base", "prompt_only", "lora", "lora_attn3"}
    assert sum("own loop" in n for n in res["notes"]) == 2


def test_the_measured_rate_and_the_submit_limit(tmp_path):
    res = pe.plan("100", TRAIN, sol(rate=lambda: 2000.0, job_count=lambda: 8), LENGTHS)
    assert res["rate"]["range"] == [1600.0, 2400.0] and res["queue"]["room"] == 2
    cmds = pe.commands(res)
    assert "measured 2000" in cmds[0] and sum(not x.startswith("#") for x in cmds) == 2
    assert all(x.startswith("# later (MaxSubmitPU)") for x in cmds[3:] if "submit.sh" in x)
    out = tmp_path / "eval"
    out.mkdir()
    (out / "eval_jobs.jsonl").write_text(json.dumps({"system": "base", "started_utc": "2026-10-28T10:00:00+00:00",
                                                      "ended_utc": "2026-10-28T11:00:00+00:00"}) + "\n")
    (out / "eval_base_runs.jsonl").write_text("".join(json.dumps(
        {"timestamp_utc": f"2026-10-28T{h}:30:00+00:00", "completion_tokens": 3_600_000}) + "\n" for h in ("10", "12")))
    assert pe.measured_rate(out) == 1000.0                  # only the run inside the job's hour counts
    assert pe.step2b_lengths()                               # the tracked Step 2b summary is readable
