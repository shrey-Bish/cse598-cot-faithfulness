# progress/

Shared plumbing, Track B's runners, and the October progress round.

- Used by every track: `common.py` (one record format, the 4-request limiter, run IDs, Wilson intervals) and
  `guard.py` (the power rules; restarts a run after the laptop sleeps).
- Track B: `run_trackB.py`, the experiment runners `run_b15.py` to `run_b24.py`, `trackB_report.py`, and Sol's
  `sol_trackB.py`, `sol_b17.py`, `sol_b20.py`.
- The progress round (historical, evidence for its figures): `mmlu_pro_probe.py`, `reviewer_demo.py`,
  `analyze_progress.py`, the presentation tools.

Open `common.py` first, then the runner for the experiment you care about. Do not change shared files without the
owner: Track B's runner paths are listed in `../configs/path_allowlist.txt`.
Commands: [`../../docs/RUNBOOK.md`](../../docs/RUNBOOK.md) §1 and §18.
