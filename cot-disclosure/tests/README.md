# tests/

CPU-only tests for every module: no network, no model calls, no GPU. About 100 test files.

```bash
cd cot-disclosure && ../.venv/bin/python -m pytest -q                   # everything
../.venv/bin/python -m pytest -q tests/test_repo_hygiene.py tests/test_check_links.py   # the repo's own checks
```

Files are named for what they test (`test_demo_*` the demo, `test_trackA_*` Track A, `test_trackB*` and
`test_trackC_*` the other tracks, `test_repo_hygiene.py` and `test_check_links.py` the repo's rules). Tests that need
torch skip without it. Several tests also check that a reported number still matches its frozen source.
Set up the environment first: [`../../REPRODUCE.md`](../../REPRODUCE.md).
