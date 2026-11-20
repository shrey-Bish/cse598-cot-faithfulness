# Session log: the demo rebuilt, phase 1: the inventory, then stop (2026-11-20 10:13 MST)

**By:** Ritik. Branch `trackA-nosol`, from `55cb36c` (main, `trackA-nosol`, `origin/main` and `origin/trackA-nosol`
level). The day's first session; the daily: [DAILY_2026-11-20](2026-11-20/DAILY_2026-11-20.md). The previous session: Nov 19,
[22:49](2026-11-19/2026-11-19_2249_ALL_demo-concepts.md). The results are frozen: the tag
`results-freeze-2026-11-18` on `7e1fdc0`. Presentation work after the freeze: no number, figure or verdict changes.

## 0. Input

A pasted prompt, acted on as Ritik's, with the brief pasted beside it: the demo rebuilt as one offline page in the
answer-sheet look (concept A, carried on as a template, `~/Downloads/demo_template/`), three parts: how we did it (a
map of the project, each step opening on its method), run it (a test bench replaying real recorded runs) and what we
found (ten result sheets). **Phase 1 only:** `docs/demo/INVENTORY.md` (where every method fact and every set of
recorded runs lives, what is only on Sol with its exact paths, what is missing), move the template in as
`tools/demo_template/`, then stop. At most 2 helpers. Ritik paused the session partway ("stop it for now";
both helpers stopped) and resumed it ("continue"; both resumed where they were).

## 1. What was done (10:13–13:39)

- `~/Downloads/DEMO_SPEC.md` and `~/Downloads/demo_template/` are not on this Mac (Downloads, Desktop and Documents
  searched). The brief was saved from the paste, word for word, as `docs/demo/DEMO_SPEC.md`; **the template was not
  moved** (nothing to move). Phase 2 needs it.
- Two helpers, read-only, no connection to any server: one found where each method fact lives (the map's steps
  2–11), the other the recorded runs for the six bench tests (on this Mac and, from the repo's records, on Sol).
  Their main claims checked here: LoRA's settings (`train.py:64–70`), the full-attention layers (`kit.py:182`), the
  bootstrap (`common.py:232, 248, 261`), the training data counts (`examples_manifest.json`); no evaluation text for
  the fixes on this Mac (0 `.jsonl.gz` in `results/trackA/gpu/a39/` and `eval/`); no Qwen3-8B text
  (`sol_vllm.jsonl.gz` absent); all 486 tool-call runs in `voyager.jsonl.gz` carry their call.
- One helper error corrected: the 120's pre-registration is the 11:30 log, not "13:30".
- **The inventory:** `docs/demo/INVENTORY.md` (numbers, ids and paths only). In short:
  - The map: steps 1–3, 5–10 rich on this Mac. Step 4 has no project-wide GPU-hour total (pieces only; `sacct` on
    Sol would give one). Step 7 has real training pairs on the Mac but its loss only per epoch (per-step logs on Sol).
    Step 11 has no contamination audit file (the 120's exclusion checks and the held-out leak checks exist).
  - The bench: tests 2 (authority), 5 (review teams) and 6 (inside the model, per-question cut records, numbers)
    complete; test 1 with text for 3 of 8 models; test 3 (thinking on/off) and test 4 (the fixes) have no text here:
    their runs are on Ritik's Sol account (paths in its §4); Granite and Gemma's B20 runs on Arsha's.
  - Proposal: a targeted copy (draw the questions on the Mac, fetch only those runs by run id with the read-only
    stdin pattern), or tests 3 and 4 on numbers and hand-label final answers.
- `docs/status/TODO.md`: D19 (the demo rebuilt), phase 1 done.

**After the freeze (Nov 20, 13:39): presentation work only.** No number, figure or verdict changed; no frozen file
changed. The tracked changes are the brief, the inventory, TODO's D19 and the logs.

## 2. Waiting for Ritik

- What to keep or drop on the map and the bench (INVENTORY §1).
- Whether to copy from his Sol account (INVENTORY §4), all of it or only the drawn runs; Arsha's B20 runs are hers.
- The template `demo_template/` with `TEMPLATE_GUIDE.md` saved on this Mac.
- Then phase 2.

## 3. Checks and push

`tests/test_repo_hygiene.py` and `tests/test_check_links.py`; `tools/check_links.py`; `tools/make_supplement.py
--check`; `tools/export_summaries.py --check`; STATUS and the Gantt; the pre-push check; nothing on `origin/main`
missing here. Results in the commit message. The push: `git push origin trackA-nosol:main trackA-nosol:trackA-nosol`.
