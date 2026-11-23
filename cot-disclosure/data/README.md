# data/

The question sets, small enough to track. All in `progress/`.

- `mmlupro_30.jsonl`: the 30 evaluation questions from MMLU-Pro.
- `mmlupro_e2.jsonl`: "E2", 120 fresh questions made on Nov 3 (`finetune/make_e2.py`). Its sha256 is in its
  pre-registration. Nothing is ever chosen on it.

The training data and the model runs are produced data: they live in `finetune/data/` and `results/track*/` on a
local copy and are not in the repo ([`../../REPRODUCE.md`](../../REPRODUCE.md)). GPQA files are gated and never tracked.
