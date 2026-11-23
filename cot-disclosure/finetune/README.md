# finetune/

Track A: inside one open thinking model, Olmo 3 7B Think, and the fixes. Read
[`../README.md`](../README.md) for the code map; this is the short version.

- Top-level files: the pinned Olmo prompt format (`olmo_format.py`), the dataset (`build_dataset.py`), source tags,
  training (`train.py`), generation and evaluation (`generate.py`, `eval.py`), Gate 3's table (`gate3.py`), and the
  readings for A39, A40 and A42 (`a39.py`, `a40.py`, `a42.py`). `make_e2.py` makes the 120 fresh questions.
- `look/`: looking inside the model: the takeover curve, the deletion test, attention to the hint, activation
  patching, the same in Qwen3-8B (`qwen8b_mech.py`) and in the trained model (`a18.py`).
- `gpu/`: the Sol kit: job plans, the evaluation job, one `.sbatch` per job kind and the only submit script. Its
  [README](gpu/README.md) has the commands.
- `prompts/`, `templates/`: prompt text and chat templates.
- Some files are historical: they ran once and are kept as evidence for a result.

Training and most analyses need A100 GPUs on Sol. `data/` here (gitignored, not in the repo) holds the training data.
Which step is which: [`../../docs/RUNBOOK.md`](../../docs/RUNBOOK.md) §3 to §14.
