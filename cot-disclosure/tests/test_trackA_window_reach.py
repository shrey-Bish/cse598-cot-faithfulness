"""The sliding-window analysis (finetune/look/window_reach.py): token distances on a synthetic run
with the real tokenizer, and the within-run step test on planted data. No network."""
import math
import random
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from finetune import olmo_format  # noqa: E402
from finetune.look import hint_spans as hs  # noqa: E402
from finetune.look import takeover as tk  # noqa: E402
from finetune.look import window_reach as wr  # noqa: E402
from tools.answer_key import build  # noqa: E402
from _tiny_olmo import olmo_tokenizer_dir  # noqa: E402


def test_distances_on_a_run():
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(olmo_tokenizer_dir(), local_files_only=True)
    messages, _ = build("Which is it?\n(A) one\n(B) two", 7, "tool_pasted", "B")
    reasoning = ("First I work it out on my own, step by step. " * 3 + "The tool says the expected answer is B. "
                 + "Now more of my own working, carefully. " * 4)
    src = {"run_id": "r", "item_id": 7, "condition": "tool_pasted", "cue_letter": "B",
           "rendered_prompt": olmo_format.render(messages), "reasoning_text": reasoning}
    ends = tk.sentence_ends(reasoning)
    d = wr.distances(tok, src, {"sentence_ends": ends})
    lay = hs.layout(tok, src, reasoning)
    for k in range(len(ends) + 1):                       # the answer position matches tokenizing each probe
        exact = len(hs.tokenize(tok, src["rendered_prompt"] + reasoning[:ends[k - 1] if k else 0] + hs.FORCE)[0]) - 1
        assert abs(d[k][0] - exact) <= 2
        assert d[k][2] == d[k][0] - max(lay["hint"])
    assert d[3][1] == d[3][2]                            # no mention yet: back to the prompt's hint
    assert d[4][1] < 15 and d[8][1] > d[5][1] > d[4][1]  # sentence 4 mentions the hint; then it recedes


def planted(step_at, n_runs=40, size=-1.0, seed=0):
    """Runs whose log-odds drop by `size` once the distance passes `step_at`, plus noise."""
    rng = random.Random(seed)
    rows = []
    for run in range(n_runs):
        base = rng.gauss(0, 1)
        for d in range(1500, 7000, 64):
            y = base + (size if d >= step_at else 0.0) + rng.gauss(0, 0.3)
            rows.append({"run": f"r{run}", "q": run % 10, "kind": "followed", "d_mention": d, "d_prompt": d,
                         "log_odds": y, "bounded": False})
    return rows


def test_a_planted_step_shows_at_4096_and_not_at_the_placebos():
    res = wr.boot({c: wr.run_steps(planted(4096), "d_mention", c) for c in wr.CUTOFFS}, n=500)
    assert res[4096]["ci95"][1] < -0.8 and res["contrast"]["ci95"][1] < -0.6
    for c in (2048, 3072, 5120, 6144):
        assert abs(res[c]["mean"]) < 0.2 if res[c]["mean"] is not None else True


def test_a_smooth_trend_gives_no_contrast():
    rows = planted(10 ** 9)
    for r in rows:
        r["log_odds"] -= r["d_mention"] / 1000                     # linear decline, no step
    res = wr.boot({c: wr.run_steps(rows, "d_mention", c) for c in wr.CUTOFFS}, n=500)
    assert res[4096]["mean"] < -0.3 and res["contrast"]["ci95"][0] < 0 < res["contrast"]["ci95"][1]


def test_outcome_uses_the_floor_outside_the_top_10():
    y, bounded = wr.outcome({"probs": {"A": 0.5, "B": None}, "floor": 0.01}, "A", "B")
    assert bounded and y == pytest.approx(math.log(50))
