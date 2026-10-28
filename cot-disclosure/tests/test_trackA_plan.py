"""Track A's training plan from S1 (finetune/gpu/plan_training.py): the refit through the timed examples,
the hours as a range, the job limits and the batch-2 commands. Synthetic timings; no GPU."""
import json
import random
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

from finetune.gpu import plan_training as pt  # noqa: E402

LENGTHS = {"train": [2000, 4000, 7000, 7000, 12000, 20000, 31000] * 100, "validation": [5000, 9000] * 50}


def timing_row(version, c1, c2, noise=0.0, seed=0):
    """What train.py --timing writes: a warm-up and 12 examples spread over the lengths, with its
    straight-line fit (which comes out with a negative fixed part when the cost is quadratic)."""
    rng = random.Random(seed)
    toks = [1500] + [1500 + i * 2700 for i in range(12)]
    ex = [{"tokens": t, "seconds": round(c1 * t / 1000 + c2 * (t / 1000) ** 2 + rng.gauss(0, noise), 3)} for t in toks]
    ex[0]["seconds"] += 30                                               # the warm-up is slow
    xs, ys = [e["tokens"] for e in ex[1:]], [e["seconds"] for e in ex[1:]]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return {"version": version, "examples": ex, "seconds_fixed": my - b * mx, "seconds_per_token": b,
            "predicted_hours_2_epochs": 1.0, "peak_memory_gb": 61.2}


def write(tmp_path, rows):
    p = tmp_path / "timing.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    (tmp_path / "lengths.json").write_text(json.dumps(LENGTHS))
    return p, tmp_path / "lengths.json"


def test_the_refit_recovers_a_quadratic_cost_where_the_line_goes_negative():
    row = timing_row("lora", 0.8, 0.03)
    assert row["seconds_fixed"] < 0                                      # what S1 printed
    c = pt.fit([(e["tokens"], e["seconds"]) for e in row["examples"][1:]])
    assert abs(c[0] - 0.8) < 1e-3 and abs(c[1] - 0.03) < 1e-4
    c1, c2 = pt.fit([(1000, 2.0), (2000, 4.0), (3000, 6.0)])                # a straight line through 0
    assert abs(c1 - 2.0) < 1e-9 and abs(c2) < 1e-9
    assert all(x >= 0 for x in pt.fit([(1000, 5.0), (2000, 4.0), (30000, 3.0)]))          # never negative


def test_hours_and_the_range(tmp_path):
    timing, lengths = write(tmp_path, [timing_row(v, 0.8, 0.03, noise=0.5, seed=i) for i, v in enumerate(pt.VERSIONS)])
    res = pt.plan(timing, lengths)
    exact = pt.hours((0.8, 0.03), LENGTHS, 0.375)
    for p in res["versions"].values():
        lo, hi = p["hours_range"]
        assert lo <= p["hours"] <= hi and abs(p["hours"] - exact) / exact < 0.05
        assert p["s1_linear_fit"]["seconds_fixed"] < 0 and p["peak_memory_gb"] == 61.2


def test_limits_are_the_high_end_times_1_3_at_most_8_hours():
    assert pt.job(2.0) == (2.0, 180, 1)                                  # 2.0 x 1.3 = 2.6 h -> 3:00
    assert pt.job(3.21)[1] == 270                                        # 4.17 h -> 4:30
    est, limit, jobs = pt.job(11.0)
    assert limit == 480 and est * 1.3 <= 8 and jobs == 2                 # capped at 8 h: two jobs
    assert pt.job(6.2)[1] == 480 and pt.job(6.2)[2] == 1


def test_the_batch2_commands(tmp_path):
    rows = [timing_row("lora", 0.8, 0.03), timing_row("tags", 0.5, 0.02), timing_row("lora_tags", 0.9, 0.03)]
    timing, lengths = write(tmp_path, rows)
    res = pt.plan(timing, lengths)
    assert res["missing"] == ["lora_attn3"] and res["versions"]["lora_attn3"]["from"] == "lora_tags"
    lines = pt.commands(res)
    assert lines[1].startswith(f"{pt.SUBMIT} train --estimate ") and lines[1].split(" -- ")[1].startswith("lora ")
    assert "--dependency=afterany:<lora job> -- lora_tags" in lines[3]
    assert "--dependency=afterany:<tags job> -- lora_attn3" in lines[4]
    for line, v in zip(lines[1:], ("lora", "tags", "lora_tags", "lora_attn3")):
        est = float(line.split("--estimate ")[1].split()[0])
        assert est == res["versions"][v]["estimate"] and est * 1.3 <= 8.0


def test_the_real_lengths_file_matches_the_assembled_set():
    lengths = json.loads(pt.LENGTHS.read_text())
    assert len(lengths["train"]) == 1040 and len(lengths["validation"]) == 156
    assert max(lengths["train"] + lengths["validation"]) <= 32768
