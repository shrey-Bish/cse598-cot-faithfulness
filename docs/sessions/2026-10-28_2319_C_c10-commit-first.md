# Session log: C10, commit first (2026-10-28 23:19 MST)

Project: CSE 598 Group 10. Track C runs a solver/reviewer/checker team on Track B's cases. This log
covers C10's run and results. The design and the dry run are in
[2026-10-28_2303_ALL_tags-check-and-c10-dry-run.md](2026-10-28_2303_ALL_tags-check-and-c10-dry-run.md).

## 1. Header

- **Time:** 2026-10-28 23:19 MST. **Track:** C. **By:** Shrey.
- **Branch:** `trackA-nosol` (= `main`); `trackB-main` and `trackC-main` move to this log's commit.

## 2. What ran

- **Voyager:** C10, 23:06–23:16 under the power guard (`voyager:c10`): 159 of 159 cases, 636 calls,
  0 errors, every reply with a letter, every finish "stop". The guard ended at 23:17.
- **Mac, no calls:** the C10 summary (`--summary --log team_c10 --cases … --table`) and
  `export_summaries.py` (now also C10's summary).

## 3. Results (FINDINGS F21; paired by item)

| reviewer, variant | corrects (bad lookups, 25 items) | minus C4 | minus C9 | minus its own first answer |
|---|---|---|---|---|
| Olmo 3 32B, + private reasoning | 19 of 73 | +18 [+10, +26] | +15 [+6, +25] | −56 [−68, −44] (60 first) |
| Olmo 3 32B, + tool log | 5 of 73 | +3 [−4, +9] | +1 [−4, +7] | −75 [−86, −62] |
| Qwen3 30B Instruct, + private reasoning | 67 of 73 | +1 [−5, +9] | −3 [−7, +0] | +7 [+0, +15] (62 first) |
| Qwen3 30B Instruct, + tool log | 33 of 73 | −32 [−44, −20] | −38 [−51, −26] | −40 [−55, −23] |

- **Good lookups:** Olmo keeps the right answer in 81 and 83 of 84 (C4: 84, 84); Qwen3 in 75 and 78
  (C4: 76, 77).
- **Qwen3 with the tool log** keeps the solver's wrong letter in 37 of 73 (C4: 13).
- **By kind × set:** Olmo's gain with the private reasoning is on both sets (puzzles +19, steered
  MMLU-Pro +21); Qwen3's drop with the tool log is too (−35, −21).
- **Pipeline:** no wrong answer shipped on a bad lookup (0 of 75 everywhere).
- **Reading:** committing first doesn't protect the check. A trace shown after the reviewer's own
  answer seems to read as new evidence. With F19, two prompt fixes fail; the check that never sees
  the tool remains the one that works.

## 4. For Ritik

```bash
git fetch origin && git log --oneline main..origin/main          # must print nothing
git push origin main trackA-nosol trackB-main trackC-main
```

## 5. For review

- **The second-turn wording is ours** and meant to be neutral. A "keep unless the trace shows an
  error" wording would test something else.
- **"New evidence" is a reading,** not tested.
- **Qwen3's drop is with the tool log only,** which states the answer key's letter outright; with
  the private reasoning it holds.
- **Nothing more is queued on Voyager.**
