# Track B: start here (Arsha, from Nov 6)

**Edited by:** Arsha, on `trackB-main`, from Nov 6. Written by Ritik on Nov 3; Ritik keeps it until then.

## Quick start (one page)

**Track B** tests the project's question widely: does a wrong hint from a tool move thinking models more than the same
hint from the user, with thinking on and off in the same weights, real tool calls and 3 runs per question? Does the
final answer stop naming the tool once the model has called it? It is the evidence for the story's line 1 and level 2
([`PLAN.md`](../PLAN.md)).

**Done** (Ritik's; [`docs/FINDINGS.md`](../FINDINGS.md) F15–F17, F25, F29, F35, F37):
- tools pull harder than users in all five models (Gate 2);
- after a tool call, the final answer goes bare;
- most of the pull is the tool's claim to be the answer key (B16, confirmed same-day by B19);
- more thinking changes neither (B17, labelled §13).
- **Started for you:** B18's table and slide 2 ([`TRACK_B.md`](../tracks/TRACK_B.md) §1a).
- **Running on Sol** (Ritik submits): B20, three open-weight families with thinking on and off. Its runs end by Nov 15.

**Your next steps:**

| # | what | by | check-in |
|---|---|---|---|
| 1 | **Setup** (§1): clone, `trackB-main`, the venv, the tests, both hooks, your own Voyager key, the bundle `trackB_20261106.tar.gz` with `--verify`, and the Track B numbers reproduced with no calls | **Fri Nov 6** | **Nov 6** (handoff) |
| 2 | **Re-read** B16, B19 and B17 by their reports, against F35 and F37 | Sat Nov 7 | — |
| 3 | **B18**: check every row of the table against FINDINGS; settle its open choices; its figure | Wed Nov 18 | Nov 12, Nov 18 |
| 4 | **B20's reading**, by its pre-registered rule, from the numbers-only files Ritik copies back (§4): an FB entry, B20 in B18's table, and the decision whether slide 2 shows it | **Tue Nov 17** | Nov 18 |
| 5 | **Slides 2, 6, 7 and 8**, final (§5), and Track B's section of the report as bullets in `docs/trackB/REPORT_B.md` | **Fri Nov 20** | — |

**Check-ins with Ritik: Nov 6, Nov 12, Nov 15 and Nov 18.**
- Bring what finished (session logs, FB entries, the table, figures), what's next, and anything blocked.
- On Nov 12, 15 and 18, Ritik merges `trackB-main` into `main` after its checks (§6). Then you merge `origin/main`
  back into `trackB-main`.

**How you work:**
- **Your branch and paths:** only on `trackB-main`, and only these paths (§2):
  - `docs/trackB/`, `docs/tracks/TRACK_B.md`;
  - Track B's runners and report (`progress/run_trackB.py`, `run_b15.py` … `run_b20.py`, `trackB_report.py`);
  - `tools/trackb_final.py` and its table `docs/paper/tables/trackB_final.*`;
  - `tests/test_trackB*` and `tests/test_trackb_final.py`;
  - `results/trackB/`, `results/summaries/trackB/`.

  The hooks enforce this, both ways: Ritik's branches can't change your paths except by merging yours.
- **The rules:** pre-register before any run; Voyager only, nothing paid; at most 4 requests in flight; every run under
  the power guard; no LLM judging; data never on GitHub; your commits carry no attribution lines.
- **Sol:** jobs are Ritik's. The Sol job code stays his (`progress/sol_trackB.py`, `sol_b17.py`, `sol_b20.py`).
- **Your machine:** a Mac, Linux, or Windows through WSL. Off a Mac the power guard skips its battery check and says so.

**Where to ask:** Ritik, by ASU email or the team's channel. Ask about anything outside your paths, a Sol job, a Voyager
halt, or a date that will slip.

---

## 1. Setup (Nov 6), step by step

1. **Clone and take your branch:**
   ```bash
   git clone https://github.com/shrey-Bish/cse598-cot-faithfulness.git && cd cse598-cot-faithfulness
   git checkout trackB-main
   git config user.name "Arsha Jindal" && git config user.email "<your ASU email>"     # this clone only
   ```
2. **The environment and the tests** (no network):
   ```bash
   python3 -m venv .venv && .venv/bin/pip install -r cot-disclosure/requirements.txt
   cd cot-disclosure && ../.venv/bin/python -m pytest -q && cd ..   # every test passes or skips
   ```
3. **The hooks**, once per clone, from the repo root:
   ```bash
   python3 cot-disclosure/tools/path_check.py --install       # the path check: pre-commit and pre-merge-commit
   printf '#!/bin/sh\nexec python3 "$(git rev-parse --show-toplevel)/cot-disclosure/tools/prepush_check.py" "$@"\n' > .git/hooks/pre-push && chmod +x .git/hooks/pre-push
   ```
   - **The path check** refuses a commit on `trackB-main` outside your paths (§2).
   - **The pre-push check** (RUNBOOK §17) refuses a push that adds produced data, a GPQA file or a file over 50 MB.
4. **Your own Voyager key:** `cp cot-disclosure/.env.example cot-disclosure/.env`. Put your key in `RC_LLM_API_KEY`
   and leave every paid key line empty. Never share, print, log or commit it.
5. **The data bundle.** Ritik sends `trackB_20261106.tar.gz` through ASU storage, never GitHub. He rebuilds it on Nov 6
   morning and checks it on a fresh clone first.
   ```bash
   tar --exclude MANIFEST.json -xzf <where you saved it>/trackB_20261106.tar.gz -C cot-disclosure
   cd cot-disclosure && ../.venv/bin/python tools/make_handoff_bundle.py --verify <where you saved it>/trackB_20261106.tar.gz
   ```
   It must print "bundle matches its manifest".
6. **Reproduce the numbers, no calls** (from `cot-disclosure/`); each should match FINDINGS:
   ```bash
   ../.venv/bin/python progress/trackB_report.py          # the Track B table: F15–F17, F29
   ../.venv/bin/python progress/run_b15.py --report       # F25
   ../.venv/bin/python progress/run_b16.py --report       # F35
   ../.venv/bin/python progress/run_b19.py --report       # F35, same-day
   ../.venv/bin/python progress/run_b17.py --report       # F37 (labelled §13)
   ../.venv/bin/python tools/trackb_final.py              # B18's table: docs/paper/tables/trackB_final.md
   ```
7. **Read:** this page, [`TRACK_B.md`](../tracks/TRACK_B.md) (results, how to run each step, known traps, decisions
   you inherit), then FINDINGS F15–F17, F25, F29, F35, F37 and traps T1–T11.

## 2. Your paths, and the hooks both ways

- **On `trackB-main` you may change only** (`cot-disclosure/configs/path_allowlist.txt`, tracked, read-only for you):
  - `docs/trackB/` (this page, `TODO_B.md`, `FINDINGS_B.md`, `sessions/`, `figures/`, `REPORT_B.md`);
  - `docs/tracks/TRACK_B.md`;
  - `cot-disclosure/progress/run_trackB.py`, `run_b15.py` … `run_b19.py`, `run_b20.py`, `trackB_report.py`;
  - `cot-disclosure/tools/trackb_final.py`, and `docs/paper/tables/trackB_final.*`, which it writes;
  - `cot-disclosure/tests/test_trackB*` and `tests/test_trackb_final.py`;
  - `cot-disclosure/results/trackB/` (gitignored data) and `cot-disclosure/results/summaries/trackB/` (numbers only).
- **`run_b20.py` is also B20's Sol runner.** Until B20's runs end (Nov 15), change only its report functions, and say
  so in the commit.
- **Everything else is shared, read-only for you:**
  - the Sol job code (`progress/sol_trackB.py`, `sol_b17.py`, `sol_b20.py`, `finetune/gpu/`);
  - `client.py`, `progress/common.py`, `providers/`, `tools/` (except `trackb_final.py`), `configs/`;
  - the slides' code (`tools/slide_figures.py`).

  Running and importing it is fine. For a change there, ask Ritik, or write the change in one of your own files.
- **The other way:** on Ritik's branches the same hook refuses any change to your paths except a merge of
  `trackB-main`, taken unchanged. Between now and Nov 6, Ritik may still update your files (TODO_B, this page), and
  says so in his commit.
- **To stay current:** `git fetch origin && git merge origin/main` on `trackB-main`. The hook passes `main`'s files
  only unchanged. Check by hand at any time: `python3 cot-disclosure/tools/path_check.py --range origin/main..HEAD`.
- Never bypass a hook (no `--no-verify`).

## 3. Your plan to the freeze

| date | what |
|---|---|
| **Fri Nov 6** | the handoff: the bundle, setup (§1); **check-in** |
| Sat Nov 7 | re-read B16, B19 and B17 by their reports |
| **Thu Nov 12** | B18: every row checked against FINDINGS; its open choices settled (§5); **check-in and merge** |
| **Sun Nov 15** | B20's runs end on Sol (Ritik); **check-in and merge** |
| **Tue Nov 17** | **B20 read** by its rule (§4): an FB entry; B20's rows in B18's table |
| **Wed Nov 18** | **results freeze** (no new runs after it); **B18's table and figure** done; **check-in and merge** |
| **Fri Nov 20** | **slides 2, 6, 7 and 8 final** (§5); Track B's section of the report, as bullets in `docs/trackB/REPORT_B.md` |
| Sun Nov 22 | the report draft (Ritik merges the sections) |
| Tue Nov 24 | the final presentation and report |

Should, if time allows: L5, Track B's labeling batch (171 rows, two raters), after L3 and L4.

## 4. B20's reading (by Nov 17)

- **What it is:** Gemma 4 26B-A4B, Nemotron 3 Nano 30B-A3B and Granite 4.2 8B on our vLLM on Sol, thinking on and off,
  Track B's design plus B16's authority arm. Pre-registered in `archive/sessions/2026-11-03/2026-11-03_1219_B_b20-prereg.md`
  (its §13: the order of the jobs).
- **The rule:**
  - **R1:** Gate 2, each tool channel minus the user's hint.
  - **R2:** tool or authority, each tool channel minus `user_authority`.
  - **R3a:** the bare answer after a call, against the pasted block.
  - **R3b:** thinking on minus off, on that bare answer.
  - Each is paired by question with a 95% bootstrap clustered by question, with the 16,000-token cut beside it.
- **Ritik runs the jobs and copies back** each model's numbers-only files (`results/trackB/b20/<model>/`, without the
  `*.jsonl.gz` records). He sends them to you through ASU storage by Nov 16.
- **You read:**
  ```bash
  ../.venv/bin/python progress/run_b20.py --report
  ```
  The reading goes in a results session log (the command, what it printed, the rule's words) and an FB entry.
  Then:
  - add B20's models to `tools/trackb_final.py`'s list;
  - decide whether slide 2 shows them.

## 5. B18 and the slides

- **B18's table:** `tools/trackb_final.py` → `docs/paper/tables/trackB_final.md` and `.csv`, from the tracked summaries
  only. Its tests are in `tests/test_trackb_final.py`.
  - Check every row.
  - Decide: the 16,000-token cut beside each row or not; B19 beside B16 or not; the figure (slide 2's, or another).
- **The slides** (PLAN's presentation map; the specs and colors are in `docs/paper/figures/WAITING.md`):
  - slide 2: Gate 2 (`gate2.png`);
  - slide 6: the bare answer after a call (`bare_after_call.png`);
  - slide 7: tool or authority (`b16_authority.png`);
  - slide 8: the thinking dose (`b17_effort.png`).

  Ritik drew all four from the tracked summaries with `tools/slide_figures.py` (his file). To change one:
  - the numbers only: ask Ritik to rerun it;
  - the design: draw yours with a script in your own files, into `docs/trackB/figures/` (PNG, SVG and a CSV of every
    plotted number). Ritik places it at merge.

## 6. Working rules, hand-back and merges

- **The rules:**
  - Pre-register before any run, in `docs/trackB/sessions/<date>/<date>_<HHMM>_B_<experiment>-prereg.md`, committed
    before the first call.
  - Nothing is chosen by looking at results.
  - A reading made after seeing results is labelled "after the fact".
  - Rates as X of Y with 95% intervals; differences as bootstraps clustered by question; fewer than 5 questions is
    "too few".
  - **No LLM judging:** labels are people's, and a coding assistant never labels or summarizes model text.
  - Voyager only, nothing paid; at most 4 requests in flight.
  - Every Voyager run goes under `progress/guard.py`, on a Mac under `caffeinate -i`. On Linux or WSL, leave
    `caffeinate` off; the guard says it skips the battery check. Keep the machine plugged in and awake.
  - Produced data never goes on GitHub. Tracked files hold numbers, ids and paths only.
  - Commits are authored by you, with no attribution lines of any kind.
- **Your records:**
  - `TODO_B.md`: the same columns; the Gantt reads it;
  - `FINDINGS_B.md`: FB1, FB2, …, with Ritik merging them into FINDINGS at the end;
  - `sessions/`: one log per working session, with a row in `sessions/INDEX.md`.
- **Hand back:**
  1. The tests pass.
  2. Commit on `trackB-main`.
  3. `python3 cot-disclosure/tools/path_check.py --range origin/main..HEAD` passes.
  4. `git push origin trackB-main`.
  5. Tell Ritik what finished: the commit range, the logs, the FB entries, the figures.
- **Merges** (RUNBOOK §16):
  - On Nov 12, 15 and 18, Ritik checks the range
    (`python3 cot-disclosure/tools/path_check.py --range origin/main..origin/trackB-main --branch trackB-main`) and runs
    the tests. He merges `trackB-main` into `main`, and places your figures.
  - Then you run `git fetch origin && git merge origin/main`.

## 7. First-session brief (paste this to start your coding assistant)

```text
You are helping Arsha Jindal run Track B of a university project: CSE 598 Group 10, "Do thinking modes make
chain-of-thought more honest?". Arsha owns Track B from Nov 6; the work before is Ritik Agarwal's.
Repo: https://github.com/shrey-Bish/cse598-cot-faithfulness.git, branch trackB-main only. Never push to main,
trackA-nosol or trackC-main; never force-push; never bypass a git hook (no --no-verify).
First read docs/trackB/START_HERE.md in full (the source of truth), then docs/tracks/TRACK_B.md. Commands run from
cot-disclosure/ with ../.venv/bin/python.
Paths: on trackB-main you may change only the paths in START_HERE section 2 (the hook enforces it). Everything else,
including the Sol job code and tools/slide_figures.py, is read-only: running or importing it is fine.
Rules: pre-register before any run; never choose anything by looking at results; Voyager only, no paid calls, never
read, print or log the key in cot-disclosure/.env; at most 4 requests in flight; runs under progress/guard.py; no LLM
judging: never label, classify, score or summarize model text for a result; produced data never goes on GitHub;
report X of Y with 95% intervals and bootstraps clustered by question; commits only when Arsha asks, authored by her,
with no attribution lines of any kind (no co-author trailers, no "generated with" lines, nothing naming a tool). Keep a
session log in docs/trackB/sessions/ with a row in its INDEX.md, and keep TODO_B.md and FINDINGS_B.md current.
Task 1 (no calls): START_HERE section 1: the venv, the tests, both hooks, .env exists and is gitignored (don't open
it), the bundle verified, and the reports in step 6 reproduced; report any difference from FINDINGS before going on.
Task 2: B18 (START_HERE section 5): check every row of docs/paper/tables/trackB_final.md against FINDINGS and list the
open choices for Arsha to decide.
```

## 8. Contacts

- **Ritik Agarwal:** submits every Sol job, owns the shared code, the allowlist and the bundles, and merges
  `trackB-main` into `main`.
- **Shrey Bishnoi:** Track C, on `trackC-main`.
