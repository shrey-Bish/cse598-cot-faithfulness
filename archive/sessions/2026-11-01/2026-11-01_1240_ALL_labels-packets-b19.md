# Session log: Ritik's labels in, the packets reviewed, B19 started (Nov 1, 12:20–12:45 MST)

By: Ritik. Ritik's message of about 12:20: the rater 1 sheets, the packet review, B19, the push, the note to Arsha
(sent with the bundle on Nov 3, unchanged).

## 1. Ritik's label sheets (rater 1): format checked, placed

- **Where they were:** in `results/labels/packets/ritik/`, the files named `L3_RA.csv` and `L4_part1_RA.csv` are the
  blank sheets as built (byte for byte `results/labels/rater1.csv` and `gate3/L4/part1.csv`). The filled sheets are
  `L3_RA_updated.csv` and `L4_part1_RA_updated.csv` (saved Nov 1, 12:08). Those are the ones checked and placed.
- **The format check** (a script that reports problems only and never counts labels; the packet's `check_sheet.py`
  prints each label's count, so it wasn't run):
  - both UTF-8, no byte-order mark, CRLF line ends like the packet;
  - the header unchanged; 101 and 294 rows, in the original order; every cell outside the label columns unchanged;
  - every label cell an allowed value, exactly as written (lowercase, with the underscore); `n/a` kept wherever the
    sheet had it; every `guess_trained` (L4) `yes` or `no`;
  - a one-line note on every `unclear` and `says_changed`.
  - **No problems found.**
- **Placed**, byte for byte, where `label_kit kappa` reads them (both gitignored):
  `results/labels/L3_RA.csv` (sha256 `9a5532cd…`) and `results/labels/gate3/L4/L4_part1_RA.csv` (`0b93afb9…`).
  **No kappa, distribution or summary of the labels was computed.** Kappa waits for Shrey's sheets.
- **Kept as received** in `results/labels/returned/ritik_20261101/` (gitignored): the two filled sheets, and two
  files that were also in the packet folder, `check_sheet.py` and `hint_labeler.html` (Nov 1, 11:41). The packet
  build doesn't make them, and rebuilding the packet replaces the folder.

## 2. The packet review: recorded, rebuilt, re-checked

- **Ritik reviewed all 14 examples and 10 practice answers** while labeling; no changes.
- **Recorded as reviewed and set by Ritik:** the spec's note (`results/labels/packets/spec.json`, gitignored; the
  build doesn't read it), TODO L3, RATER_GUIDE, RUNBOOK §15.
- **Rebuilt** (`tools/rater_packets.py build`): Ritik's and Shrey's packets both clean, rows 101, 294, 10, 10. Every
  rebuilt file is byte for byte the Oct 31 file Ritik reviewed (sha256 of all 12, before and after). `check` on each
  folder: clean. Each zip's 6 files match its folder; no file name with "key".
- **Shrey's packet** (`results/labels/packets/rater_packet_shrey.zip`): Ritik sends it.

## 3. B19: the amendment, the smoke, the run

- **Pre-registered** as B16's amendment: §9 of [`2026-10-31_2220_B_b16-prereg.md`](../2026-10-31/2026-10-31_2220_B_b16-prereg.md),
  committed (`32d0eed`) at 12:35, before any B19 call. The same rule, now same-day; T11's fix stated.
- **T11's fix:**
  - **New seeds:** repeats 3–5 (`run_trackB` sends the repeat as the seed; every record of these models has 0–2).
  - **`use_cache=False` on every request:** `run_b19.no_cache` wraps `client._request`.
- **Built without changing a file Sol's queued jobs load.** `client.py` is loaded by Qwen3-8B's job
  (`finetune/look/qwen8b_mech.py` imports `progress/common.py`, which imports `client`), and the daily told Ritik
  the pull is safe because none of those files changed. So B19's two settings live in its own runner:
  - the cache wrapper;
  - its records files (`run_trackB.FILE_PREFIX`).
- **Smoke, 12:34–12:37:**
  - 6 of 6 ok; the canary passed for all three models (largest difference 0.0).
  - `cache/` held 163,903 entries before and after. Five replies were new and none was written, so `use_cache=False`
    held on the request path.
  - One of the six (Qwen3 30B Instruct's real call, a 31-token reply) has the same text as a Track B run of that
    question. That's the chance match the amendment expects for Instruct's short replies, not a cache hit.
- **The run:** under the power guard from 12:37 (`logs/guard_b19.log`), 966 jobs left. Expected to end about
  19:00–20:00. Read in its own session log.

## 4. Judgment calls

1. **The `_updated` files are the ones placed.** They are the only filled sheets; the names given hold the blanks.
2. **My own format check, not `check_sheet.py`,** which prints label counts, which Ritik asked not to compute.
3. **`check_sheet.py` and `hint_labeler.html` kept,** not deleted with the rebuilt folder. They aren't part of the
   packet, so Shrey's zip doesn't carry them.
4. **B19's settings in its own runner** (above), not in `client.py` or `run_trackB.py`. Cost if wrong: none to the
   results. A later reader finds B19's cache setting in `run_b19.py`, not in `client.py`.
5. **B19's authority arm is B16's,** as Ritik said ("against today's authority arm"). B16 ran it Oct 31 22:25 –
   Nov 1 02:36, 10–20 hours before B19's tool arms.
6. **Two pushes.** Ritik's OK covers items 1–3. The first push carries B19's pre-registration before its results;
   the second, its reading.

## 5. Checks

- B16's and B19's tests: 10 passed (B19's 6 failing first: no module).
- Before the push: the full suite in a separate worktree (as on the night of B16, so no test writes into the
  running tree's `logs/`); check_links; the scripts named in pre-registration logs exist; `make_supplement --check`;
  `make_gantt --dry-run`; bundle dry runs B and C; the pre-push check; nothing missing; metadata.
