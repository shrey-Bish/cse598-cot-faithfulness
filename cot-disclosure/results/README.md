# results/

**Open `summaries/` first.** It is the tracked, numbers-only copy of every result. Every figure and table is made
from it (`tools/export_summaries.py` writes it and refuses a file with model text).

| Path | In the repo? | What it is |
|---|---|---|
| `summaries/` | yes | Numbers, ids and paths for Tracks A, B and C |
| `*.jsonl`, `progress/`, `scope/` | yes | The October progress round's runs, kept as its evidence |
| `trackA/`, `trackB/`, `trackC/`, `labels/`, `handoff/`, `demo/`, `archive/`, `submission/` | no | Produced data: runs, checkpoints, labels, bundles, the local demo, the submission zip |

Produced data is not on GitHub: it is large, and tracked files hold numbers, ids and paths, never model text. A
pre-push hook enforces it. See [`../../REPRODUCE.md`](../../REPRODUCE.md).
