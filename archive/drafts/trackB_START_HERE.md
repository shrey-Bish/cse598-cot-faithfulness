# Models and sources (Track B): start here

> **Draft, not in force.** A plain rewrite of `docs/trackB/START_HERE.md` (taken from `origin/trackB-main`, commit
> 688cf48, Arsha's latest), drafted Nov 14 at Ritik's request, for Arsha to adopt or change. It becomes the real page
> only when Arsha moves it into `docs/trackB/`. Plain names come from [`docs/GLOSSARY.md`](../../docs/GLOSSARY.md); the internal
> codes (B20, F35, ...) stay in parentheses where a reader needs them to find a log or a finding. Commands, paths,
> dates and numbers are as in the original. What was dropped as stale is listed at the end.

**Edited by:** Arsha, on `trackB-main`, from Nov 6. Written by Ritik on Nov 3 and handed over on Nov 6.

**Where things stand (Nov 14).** The newer-families run (B20: Gemma 4, Nemotron 3 Nano and Granite 4.2) finished on
Arsha's own Sol account on Nov 6, all 4,860 runs. It was read on Nov 7 by its pre-registered rule (FB1) and merged into
`main` on Nov 8. The final table of this track (B18) has B20's rows, and its open choices are settled (section 5). The
re-reads of the authority ladder (B16, B19), reasoning effort (B17) and the classmate-versus-manual test (B24) match
F35, F37 and F40. Nothing of this track's runs on Sol any more.

> **Only the team commits, as themselves (Ritik's permanent rule, Nov 6, 11:17).**
> No commit may list Claude, Anthropic or any AI tool as author, committer or co-author, or carry a
> "Generated with ..." or session line. The only authors and committers are the identities in
> `cot-disclosure/configs/team_identities.txt`; the hooks refuse anything else (section 11).
> **Before your next commit:** `git fetch origin && git merge origin/main`, then
> `python3 cot-disclosure/tools/path_check.py --install` again (it now writes four hooks, pre-push included), and
> check that `git config user.name` / `user.email` match your line in that file.
> Your two emails are listed there, as hashes (Nov 6). Commit with your Gmail: the repo is public, and an ASU
> email in a commit's author line shows your Sol username.
> **Nov 7:** merge `origin/main` and rerun `--install` again: the hooks now read every message as UTF-8 (a Windows fix).

## Quick start (one page)

**What this track asks.** Does a wrong hint from a tool move thinking models more than the same hint from the user?
We test this with thinking on and off in the same weights, with real tool calls, and with 3 runs per question. A second
question: once the model has called a tool, does its final answer stop naming the tool? This track is the evidence for
the first level of the story's map (the model's own words) and for the tool-vs-user line ([`PLAN.md`](../../docs/PLAN.md)).

**What is done** (Ritik's runs and Arsha's; [`docs/FINDINGS.md`](../../docs/FINDINGS.md): F15 to F17, F25, F29, F35, F37, F40):
- Tools pull harder than users in all five models (the tool-vs-user test, Gate 2).
- After a tool call the final answer goes bare (the quiet answer).
- Most of the pull is the tool's claim to be the answer key (the authority ladder, B16; confirmed the same day in B19).
- More thinking changes neither (reasoning effort, B17; labelled section 13).
- The pull grows from a classmate to the official solution manual in all three models (B24, F40), read Nov 4.
- The newer families (B20): a tool's hint moves all three more than the user's, clear in all 10 readings (FB1 in
  `FINDINGS_B.md`; merged Nov 8).
- The final table (B18) and slide 2 are started ([`TRACK_B.md`](../../docs/tracks/TRACK_B.md) section 1a); the table is checked
  and has B20's rows (Nov 14, section 5).

**What is left**

| what | by | check-in |
|---|---|---|
| **The final table and its figure** (B18): the checks and choices are done (section 5); the figure is slide 2 | Wed Nov 18 | Nov 18 |
| **Slides 2, 6, 7 and 8, final** (section 5), and this track's section of the report as bullets in `docs/trackB/REPORT_B.md` | **Fri Nov 20** | none |

**Check-ins with Ritik: Nov 15 and Nov 18** (Nov 6 and Nov 12 are past).
- Bring what finished (session logs, FB entries, the table, figures), what is next, and anything blocked.
- On Nov 15 and 18, Ritik merges `trackB-main` into `main` after its checks (section 6). Then you merge `origin/main` back
  into `trackB-main`.

**How you work**
- **Your branch and paths:** only on `trackB-main`, and only these paths (section 2):
  - `docs/trackB/`, `docs/tracks/TRACK_B.md`;
  - this track's runners and report (`progress/run_trackB.py`, `run_b15.py` ... `run_b20.py`, `trackB_report.py`);
  - `tools/trackb_final.py` and its table `docs/paper/tables/trackB_final.*`;
  - `tests/test_trackB*` and `tests/test_trackb_final.py`;
  - `results/trackB/`, `results/summaries/trackB/`.

  The hooks enforce this both ways: Ritik's branches cannot change your paths except by merging yours.
- **The rules:** pre-register before any run; Voyager only, nothing paid; at most 4 requests in flight; every run under
  the power guard; no LLM judging; data never on GitHub; your commits carry no attribution lines.
- **Your commits are yours alone** (section 11): authored and committed as you (your clone's `git config`), never as
  Claude, with no co-author trailer and no "generated with" line. The repo's root `CLAUDE.md` tells every Claude Code
  session this, `.claude/settings.json` turns Claude Code's attribution off, and the commit-msg hook refuses such a
  commit.
- **No conflicts with `main`** (section 10): you change only your paths, on your branch; Ritik merges it on check-in days
  and you merge `origin/main` back. Never rebase or force-push `trackB-main`.
- **Sol:** B20's jobs were yours, on your own account: you typed every command in your own login, and no credentials
  were shared (`SOL_ARSHA.md`). Ritik's account runs Track A's jobs (the label run and the
  consistency-training run); no line was submitted from both. The Sol job code stays Ritik's (`progress/sol_trackB.py`,
  `sol_b17.py`, `sol_b20.py`).
- **Your machine:** a Mac, Linux, or Windows through WSL. Off a Mac the power guard skips its battery check and says so.

**Where to ask:** Ritik, by ASU email or the team's channel. Ask about anything outside your paths, a Sol job, a Voyager
halt, or a date that will slip.

**How to use this page.** The quick start above is the summary. Section 1 is a first day on a new machine, in order.
Section 2 is your paths, section 3 the dates, section 4 the newer-families run, section 4a the classmate-versus-manual
test, section 5 the table and the slides, section 6 the working rules and merges. Paste section 7 to start a coding
session. Section 9 maps the repo, section 10 is git without conflicts, section 11 is Claude Code.

---

## 1. A first day on a new machine, in order

(Arsha did this on Nov 6. It stays because anyone cloning the branch afresh needs it, step by step.)

1. **Clone, take your branch, bring it level with `main`, and set your own name** (on your machine):
   ```bash
   git clone https://github.com/shrey-Bish/cse598-cot-faithfulness.git && cd cse598-cot-faithfulness
   git checkout trackB-main
   git merge --ff-only origin/main                  # "Already up to date" after Ritik's Nov 6 push
   git config user.name "Arsha Jindal" && git config user.email "<your ASU email>"     # this clone only
   git var GIT_AUTHOR_IDENT                         # check: your name and email (then a timestamp)
   git log -1 --format=%h                           # the commit Ritik's message names (or a later one)
   ```
   - `--ff-only` only moves your branch forward to `main`. If it refuses ("Not possible to fast-forward"), your branch has
     commits `main` lacks: run `git merge origin/main` instead (section 10).
   - If you already had a clone from before Nov 6: `git fetch origin`, `git checkout trackB-main`, then the same merge.
2. **The environment and the tests** (no network):
   ```bash
   python3 -m venv .venv && .venv/bin/pip install -r cot-disclosure/requirements.txt
   cd cot-disclosure && ../.venv/bin/python -m pytest -q && cd ..   # every test passes or skips
   ```
   On Nov 6, in a fresh clone with only this track's zip unpacked: 979 passed, 10 skipped (about 10 minutes; tests needing
   other tracks' data skip). This track's own (`tests/test_trackB*.py tests/test_trackb_final.py`): 117 passed, 2 skipped
   (no cached tokenizers; Granite's records, which stay on Sol).
3. **The hooks**, once per clone, from the repo root:
   ```bash
   python3 cot-disclosure/tools/path_check.py --install       # pre-commit and pre-merge-commit (paths), commit-msg (no AI attribution)
   printf '#!/bin/sh\nexec python3 "$(git rev-parse --show-toplevel)/cot-disclosure/tools/prepush_check.py" "$@"\n' > .git/hooks/pre-push && chmod +x .git/hooks/pre-push
   ```
   - **The path check** refuses a commit on `trackB-main` outside your paths (section 2).
   - **The commit-msg hook** (Nov 5; section 11) refuses a commit whose message has an AI co-author trailer
     (`Co-Authored-By` naming Claude or Anthropic), a "Generated with Claude Code" line or `noreply@anthropic.com`, or
     whose author or committer is named Claude or has an anthropic.com email. Check it once, by running the hook itself
     on a test message (it commits nothing, installed or not):
     ```bash
     printf 'hook check\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n' > /tmp/hook_check.txt
     .git/hooks/commit-msg /tmp/hook_check.txt; echo "exit $?"   # must print "commit-msg: refused: ..." and "exit 1"
     ```
     "No such file" means the hook isn't installed: run `--install` again. If you installed the hooks before Nov 6, run
     `--install` again too: it rewrites its own hooks and adds commit-msg.
   - **The pre-push check** (RUNBOOK section 17) refuses a push that adds produced data, a GPQA file or a file over 50 MB.
4. **Your own Voyager key:** `cp cot-disclosure/.env.example cot-disclosure/.env`. Put your key in `RC_LLM_API_KEY` and
   leave every paid key line empty. Never share, print, log or commit it.
5. **The data bundle.** Ritik puts `trackB_20261106.zip` in the team's ASU Drive folder and sends you the link: data goes
   through ASU storage, never GitHub. Download it into `cot-disclosure/results/handoff/` (gitignored) or outside the
   repo. From the repo root:
   ```bash
   shasum -a 256 <where you saved it>/trackB_20261106.zip      # must begin df243bcf24042ac5 (the full sha256 is in Ritik's message)
   unzip -q <where you saved it>/trackB_20261106.zip -x MANIFEST.json -d cot-disclosure
   cd cot-disclosure
   ../.venv/bin/python tools/make_handoff_bundle.py --verify <where you saved it>/trackB_20261106.zip
   git status --porcelain                                       # prints nothing: everything unpacked is gitignored
   ```
   - It must print **"bundle matches its manifest"**. `--verify` takes the packed `.zip` (or a `.tar.gz`; any path) and
     checks every file's sha256 against the `MANIFEST.json` inside, that nothing extra is in it, and that no GPQA file is.
   - Use `unzip` in a terminal, not a double-click: macOS's Archive Utility unpacks into a new folder of its own. On Linux
     or WSL, `sudo apt install unzip` if it is missing.
   - `-x MANIFEST.json` keeps the manifest out of `cot-disclosure/`; it isn't gitignored and isn't needed there.
   - **What is in it:** `results/trackB/` and the canary log, with a sha256 manifest inside and beside it:
     - the Voyager records and reports: this track's three models, the disclosure instruction (B15), the authority ladder
       (B16, B19) and the classmate-versus-manual test (B24);
     - the numbers-only files of the Sol runs: Qwen3-8B thinking on and off (B4), reasoning effort (B17), and B20's smokes
       so far;
     - the Qwen3-8B replication's files (A37, `qwen8b_mech/`).
   - **Left out:** GPQA (none), and B20's three record files with text, which stay on Sol.
   - **Built and verified Nov 6, 09:18:** 51 files, 73.8 MB unpacked, 60.2 MB packed. Against Nov 4's
     `trackB_20261104.tar.gz`: the same 51 paths, and the same sha256 for every file but one, the canary log
     (`results/voyager_canary.jsonl`), which grew with Voyager's later identity checks.
   - **Checked Nov 4** on Nov 4's build (51 files, 73.8 MB, 60.1 MB packed), in a fresh clone of `trackB-main`, and
     **again Nov 6** on this zip (the steps above in a fresh clone; the hooks, `--verify`, step 6's reports and this
     track's tests, each as written): "bundle matches its manifest"; step 6's reports, and `run_b24.py --report`, wrote
     their files byte for byte as in the bundle, and the final table (B18) came out unchanged.
6. **Reproduce the numbers, no calls** (from `cot-disclosure/`); each should match FINDINGS:
   ```bash
   ../.venv/bin/python progress/trackB_report.py          # the main table: F15–F17, F29
   ../.venv/bin/python progress/run_b15.py --report       # the disclosure instruction: F25
   ../.venv/bin/python progress/run_b16.py --report       # the authority ladder: F35
   ../.venv/bin/python progress/run_b19.py --report       # its same-day rerun: F35
   ../.venv/bin/python progress/run_b17.py --report       # reasoning effort: F37 (labelled section 13)
   ../.venv/bin/python progress/run_b24.py --report       # classmate versus manual: F40
   ../.venv/bin/python tools/trackb_final.py              # the final table (B18): docs/paper/tables/trackB_final.md
   ```
7. **Read:** this page, [`TRACK_B.md`](../../docs/tracks/TRACK_B.md) (results, how to run each step, known traps, decisions you
   inherit), then FINDINGS F15 to F17, F25, F29, F35, F37, F40 and traps T1 to T13.

Your Sol clone is for running jobs only: you never commit in it. Your commits come from your machine's clone. (The Sol
steps for the newer-families run are in `SOL_ARSHA.md`; that run is finished, see the list at the end.)

## 2. Your paths, and the hooks both ways

- **On `trackB-main` you may change only** (`cot-disclosure/configs/path_allowlist.txt`, tracked, read-only for you):
  - `docs/trackB/` (this page, `TODO_B.md`, `FINDINGS_B.md`, `sessions/`, `figures/`, `REPORT_B.md`);
  - `docs/tracks/TRACK_B.md`;
  - `cot-disclosure/progress/run_trackB.py`, `run_b15.py` ... `run_b19.py`, `run_b20.py`, `trackB_report.py`;
  - `cot-disclosure/tools/trackb_final.py`, and `docs/paper/tables/trackB_final.*`, which it writes;
  - `cot-disclosure/tests/test_trackB*` and `tests/test_trackb_final.py`;
  - `cot-disclosure/results/trackB/` (gitignored data) and `cot-disclosure/results/summaries/trackB/` (numbers only).
- **`run_b20.py` and `run_trackB.py` are also the newer-families run's Sol runner** (`run_b20.py` runs it through
  `run_trackB.run`; since Nov 5 its jobs on your account load them from your clone). Until B20's runs end (Nov 15),
  change only their report functions, and say so in the commit. If B20 is read partial (section 4), the report's code for
  it is written and tested before it is read (the B20 log's section 19.4): a report function, so it is yours to write.
- **Everything else is shared, read-only for you:**
  - the Sol job code (`progress/sol_trackB.py`, `sol_b17.py`, `sol_b20.py`, `finetune/gpu/`);
  - `client.py`, `progress/common.py`, `providers/`, `tools/` (except `trackb_final.py`), `configs/`;
  - the slides' code (`tools/slide_figures.py`).

  Running and importing it is fine. For a change there, ask Ritik, or write the change in one of your own files.
- **The other way:** on Ritik's branches the same hook refuses any change to your paths except a merge of `trackB-main`,
  taken unchanged. Ritik's Nov 6 handoff edits to your files (this page, `SOL_ARSHA.md`, `TRACK_B.md`) went in that way,
  with `PATH_CHECK_ALLOW=trackB-main` said in the commit, before his last push. From then on only you change them
  (section 10).
- **To stay current:** `git fetch origin && git merge origin/main` on `trackB-main`. The hook passes `main`'s files only
  unchanged. Check by hand at any time: `python3 cot-disclosure/tools/path_check.py --range origin/main..HEAD`.
- Never bypass a hook (no `--no-verify`).

## 3. Your plan to the freeze

| date | what |
|---|---|
| Thu Nov 5 | the newer-families run (B20) moved to your own Sol account (the B20 log's section 19); your setup moved to Nov 6, since you started then |
| **Fri Nov 6** | the handoff: the zip, setup on your machine (section 1), then B20 on your Sol account (Sat Nov 7 at the latest, Ritik to confirm); **check-in** |
| Sat Nov 7 | re-read B16, B19 and B17 by their reports |
| Mon Nov 9 | B24 re-read against F40 (section 4a; read Nov 4) |
| **Thu Nov 12** | the final table (B18): every row checked against FINDINGS; its open choices settled (section 5); **check-in and merge** |
| **Sun Nov 15** | **check-in and merge** (B20's runs ended Nov 6, so the partial cut-off no longer applies) |
| ~~Tue Nov 17~~ | **B20 read Nov 7** by its rule (section 4), all runs in: FB1; B20's rows in the final table Nov 14 |
| **Wed Nov 18** | **results freeze** (no new runs after it); **the final table and its figure** done; **check-in and merge** |
| **Fri Nov 20** | **slides 2, 6, 7 and 8 final** (section 5); this track's section of the report, as bullets in `docs/trackB/REPORT_B.md` |
| Sun Nov 22 | the report draft (Ritik merges the sections) |
| Tue Nov 24 | the final presentation and report |

Should, if time allows: L5, this track's hand-labeling batch (171 rows, two raters), after the project's first two
labeling rounds (L3 and L4).

## 4. The newer-families run (B20), read Nov 7 (FB1)

- **Done:** all 4,860 runs on your account by Nov 6; read once, Nov 7 19:17, by the rule below with all runs in, so the
  partial read did not apply (the Nov 7 log (`sessions/2026-11-07/2026-11-07_1917_B_b20-results.md`); FB1 in
  `FINDINGS_B.md`; merged into `main` Nov 8). B20's rows are in the final table (Nov 14, section 5).
- **What it is:** Gemma 4 26B-A4B, Nemotron 3 Nano 30B-A3B and Granite 4.2 8B on our vLLM on Sol, thinking on and off,
  the main design plus the answer-key arm of the authority ladder. Pre-registered in
  `archive/sessions/2026-11-03/2026-11-03_1219_B_b20-prereg.md` (its sections 13 and 14: the jobs; 15 and 16: the
  amendments of Nov 4; 17: one port a job, and Granite's second smoke; 18: the shared stop file; 19: your account, the
  3:00 lines, the run order and the partial read).
- **The design as amended** (Nov 4, sections 15 and 16, after the smokes; 4,860 runs):
  - Gemma's and Nemotron's tool channel is the inserted tool turn (`tool_injected`), the pre-registered fallback. Their
    smokes never made the tool path work. Label it "the inserted tool turn (the fallback)".
  - Granite runs thinking on only (972 runs). With thinking off it still wrote a think block and closed it itself, in 6
    of 6 smoke runs. The thinking-on-minus-off reading (R3b) is not read for Granite, and the report says "thinking on
    only". Only Granite keeps the model's own call, so R3b on the model's own call is read for no model.
  - Their set-aside smoke runs (Gemma's 2 `tool_real`, Nemotron's 2, Granite's 6 thinking-off) stay in the records and are
    never read: `run_b20.py --report` reads each model's amended design only.
  - Descriptive, read by no rule: offered the tool, Granite called it in 2 of 2 smoke runs, Gemma in 0 of 2, Nemotron in 1
    of 2, a run that then reached the length limit without an answer (FINDINGS_B's note).
- **The rule:**
  - **R1:** the tool-vs-user test (Gate 2), each tool channel minus the user's hint.
  - **R2:** tool or authority, each tool channel minus `user_authority`.
  - **R3a:** the bare answer after a call, against the pasted block.
  - **R3b:** thinking on minus off, on that bare answer.
  - Each is paired by question with a 95% bootstrap clustered by question, with the 16,000-token cut beside it.
- **The partial read** (section 19.4, set Nov 5 before any B20 result was read): if B20 were not complete by **Nov 15
  23:59**, each model would be read on the questions that have every run of its design (18 runs a question for Granite, 36
  for Gemma and Nemotron), labelled **"partial: N of 54 questions"**, with how many are pilot puzzles and how many MMLU-Pro
  items. A model with no whole question would be "not run: no GPU time by Nov 15". It did not apply: B20 finished Nov 6.
- **Each B20 job serves on a port of its own** (section 17). The shared-port audit found no earlier result affected
  (FINDINGS T12): each B20 smoke had its own server.
- **To read it again:**
  ```bash
  ../.venv/bin/python progress/run_b20.py --report
  ```
  The reading goes in a results session log (the command, what it printed, the rule's words) and an FB entry. Both are
  done (FB1). B20's models were added to `tools/trackb_final.py`'s list (Nov 14), and slide 2 shows them once Ritik
  relabels its legend and note (section 5).
- **Copying back from Sol** (if a rerun is ever needed): each model's numbers-only files (`results/trackB/b20/<model>/`,
  without the `*.jsonl.gz` records), SOL_ARSHA step 9.

## 4a. Classmate versus official manual (B24, F40), read Nov 4

- **What it is:** the authority ladder's design (Qwen3 30B Thinking and Instruct, Olmo 3 7B Think; the 54 questions; 3 runs
  at B19's seeds, no reply cache) with two new user arms, where the answer-key sentence went:
  - "A classmate of mine says the answer is (X)." (`user_classmate`);
  - "The official solution manual says the answer is (X)." (`user_manual`).
  Pre-registered in `archive/sessions/2026-11-04/2026-11-04_0337_B_b24-prereg.md` before any call. 972 runs on Voyager, from
  Nov 4 03:42 on Ritik's Mac.
- **The rule** (its section 3): (a) the manual minus the authority ladder's answer key (expected: no difference
  detected); (b) the manual minus the classmate, and the classmate minus the plain hint of the main design; (c) each of
  B19's tool arms minus the manual. Paired by question, 95% bootstrap clustered by question, the 16,000 cut beside each.
  Three of the five readings are cross-day, and labelled so.
- **Read by Ritik, Nov 4 11:12** (`archive/sessions/2026-11-04/2026-11-04_1112_B_b24-results.md`; FINDINGS F40):
  - the manual moves all three more than the classmate (+41, +12, +32);
  - against the authority ladder's wording, Qwen3 30B Thinking +21 (the manual higher), the others no difference detected;
  - the manual's claim pulls as hard as every tool channel, or harder, except Qwen3 30B Instruct's own call.
- **You re-read it** from the Nov 6 bundle's records, with no calls (it matched, Nov 14):
  ```bash
  ../.venv/bin/python progress/run_b24.py --report
  ```
  It must print the log's numbers. Its records never enter the final table. Slide 7's figure can take its two arms (PLAN's
  map).

## 5. The final table (B18) and the slides

- **The table:** `tools/trackb_final.py` writes `docs/paper/tables/trackB_final.md` and `.csv`, from the tracked summaries
  only. Its tests are in `tests/test_trackb_final.py`.
  - Check every row.
  - Decide: the 16,000-token cut beside each row or not; B19 beside B16 or not; the figure (slide 2's, or another).
  - **Done Nov 14 (Arsha):** every row checked against F15 to F17, F29, F35, F37 and FB1; B20's five rows added with their
    labels (13 model settings). **Decided:** the 16,000 cut as one note under the table (it changes one reading: Gemma,
    thinking on, tool versus authority); B19 as the existing note; the figure is slide 2 (`gate2.png`), which takes B20's
    rows from the table. Its legend and note named only this track's first models, so Ritik relabels them (his file).
- **The slides** (PLAN's presentation map; the specs and colors are in `docs/paper/figures/WAITING.md`):
  - slide 2: the tool-vs-user test (`gate2.png`);
  - slide 6: the bare answer after a call (`bare_after_call.png`);
  - slide 7: tool or authority (`b16_authority.png`);
  - slide 8: reasoning effort (`b17_effort.png`).

  Ritik drew all four from the tracked summaries with `tools/slide_figures.py` (Ritik's file). To change one:
  - the numbers only: ask Ritik to rerun it;
  - the design: draw yours with a script in your own files, into `docs/trackB/figures/` (PNG, SVG and a CSV of every
    plotted number). Ritik places it at merge.

## 6. Working rules, hand-back and merges

- **The rules:**
  - Pre-register before any run, in `docs/trackB/sessions/<date>/<date>_<HHMM>_B_<experiment>-prereg.md`, committed before
    the first call.
  - Nothing is chosen by looking at results.
  - A reading made after seeing results is labelled "after the fact".
  - Rates as X of Y with 95% intervals; differences as bootstraps clustered by question; fewer than 5 questions is "too
    few".
  - **No LLM judging:** labels are people's, and a coding assistant never labels or summarizes model text. (The project's
    AI judges work only on the project's own hand labels, for a reliability check, and are always disclosed; this changes
    nothing here: no model labels, scores or summarizes this track's model text.)
  - Voyager only, nothing paid; at most 4 requests in flight.
  - Every Voyager run goes under `progress/guard.py`, on a Mac under `caffeinate -i`. On Linux or WSL, leave `caffeinate`
    off; the guard says it skips the battery check. Keep the machine plugged in and awake.
  - Produced data never goes on GitHub. Tracked files hold numbers, ids and paths only.
  - Commits are authored and committed by you (your clone's `git config`), with no attribution lines of any kind: no
    co-author trailers, no "generated with" lines, nothing naming a tool. A coding assistant commits only when you ask, and
    only as you; section 11 has the three layers that enforce it.
- **Your records:**
  - `TODO_B.md`: the same columns; the Gantt reads it;
  - `FINDINGS_B.md`: FB1, FB2, ..., with Ritik merging them into FINDINGS at the end;
  - `sessions/`: one log per working session, with a row in `sessions/INDEX.md`.
- **Hand back:**
  1. The tests pass.
  2. Commit on `trackB-main`.
  3. `python3 cot-disclosure/tools/path_check.py --range origin/main..HEAD` passes.
  4. `git push origin trackB-main`.
  5. Tell Ritik what finished: the commit range, the logs, the FB entries, the figures.
- **Merges** (RUNBOOK section 16):
  - On Nov 15 and 18, Ritik checks the range
    (`python3 cot-disclosure/tools/path_check.py --range origin/main..origin/trackB-main --branch trackB-main`) and runs
    the tests. Ritik merges `trackB-main` into `main`, and places your figures.
  - Then you run `git fetch origin && git merge origin/main`.

## 7. First-session brief (paste this to start your coding assistant)

```text
You are helping Arsha Jindal run Track B of a university project: CSE 598 Group 10, "Do thinking modes make
chain-of-thought more honest?". Arsha owns Track B from Nov 6; the work before is Ritik Agarwal's.
Repo: https://github.com/shrey-Bish/cse598-cot-faithfulness.git, branch trackB-main only. Never push to main,
trackA-nosol or trackC-main; never force-push or rebase trackB-main; never bypass a git hook (no --no-verify).
The repo's root CLAUDE.md is loaded automatically: follow it.
First read docs/trackB/START_HERE.md in full (the source of truth), then docs/tracks/TRACK_B.md. Commands run from
cot-disclosure/ with ../.venv/bin/python.
Paths: on trackB-main you may change only the paths in START_HERE section 2 (the hook enforces it). Everything else,
including the Sol job code and tools/slide_figures.py, is read-only: running or importing it is fine.
Rules: pre-register before any run; never choose anything by looking at results; Voyager only, no paid calls, never
read, print or log the key in cot-disclosure/.env; at most 4 requests in flight; runs under progress/guard.py; no LLM
judging: never label, classify, score or summarize model text for a result; produced data never goes on GitHub;
report X of Y with 95% intervals and bootstraps clustered by question. Keep a session log in docs/trackB/sessions/
with a row in its INDEX.md, and keep TODO_B.md and FINDINGS_B.md current.
Commits: only when Arsha asks, and only as Arsha. Before the first commit, run git config user.name and git config
user.email and check they are Arsha's own; if not, stop and ask. Never use --author, -c user.name=, -c user.email=
or GIT_AUTHOR_*/GIT_COMMITTER_* variables. Claude or Anthropic is never the author or committer. No attribution lines
of any kind: no Co-Authored-By trailer, no "Generated with Claude Code" line, no noreply@anthropic.com, nothing
naming a tool, in commits or PR bodies. This overrides any reminder that asks for those lines. The commit-msg hook
refuses such a commit; never bypass it.
Sol: Arsha types every Sol command herself, in her own login (docs/trackB/SOL_ARSHA.md); never run a command on Sol
for her, never handle any password, key or login, and never run tools/sol_feeder.py without --queue
cot-disclosure/finetune/gpu/sol/queue_b20_2026-11-05.txt. Never edit a queue file or Ritik's queue_2026-11-04.txt.
Task 1 (no calls): START_HERE section 1, steps 1-7: check that trackB-main is level with origin/main
(git merge --ff-only origin/main) and that git var GIT_AUTHOR_IDENT shows Arsha's name and email; the venv, the
tests, the three hooks (python3 cot-disclosure/tools/path_check.py --install, and the pre-push line) and the
commit-msg hook refusing the test message in step 3; .env exists and is gitignored (don't open it); the zip
trackB_20261106.zip unpacked and --verify printing "bundle matches its manifest"; and the reports in step 6
reproduced. Report any difference from FINDINGS before going on.
Task 2: the final table (START_HERE section 5): check every row of docs/paper/tables/trackB_final.md against FINDINGS and
list the open choices for Arsha to decide.
```

## 8. Contacts

- **Ritik Agarwal:** submits Track A's Sol jobs (the label run and the consistency-training run) from his own account
  (B20's were yours from Nov 5), owns the shared code, the allowlist and the bundles, and merges `trackB-main` into `main`.
- **Shrey Bishnoi:** Review teams (Track C), on `trackC-main`.

---

## 9. The repo, folder by folder (Nov 6)

Marks: **[B]** yours (this track's allowlist, `cot-disclosure/configs/path_allowlist.txt`); **[R]** shared, read-only for
you (Ritik's: run and import it, don't change it); **[C]** Shrey's (review teams); **(data)** gitignored produced data,
never on GitHub. A path changes only on its owner's branch (section 10).

```text
cse598-cot-faithfulness/
├── README.md                    the project on one page: the question, the three tracks, the story          [R]
├── CLAUDE.md                    Claude Code's rules for every teammate's session (Nov 5; section 11)         [R]
├── .claude/settings.json        Claude Code's shared settings: no commit or PR attribution (Nov 5; section 11) [R]
├── .gitignore                   a whitelist: only README, CLAUDE.md, .claude/settings.json, cot-disclosure/,
│                                archive/ and docs/ are tracked                                               [R]
├── docs/
│   ├── PLAN.md                  the plan, the story, the presentation map (slides 2, 6, 7, 8 are yours)      [R]
│   ├── FINDINGS.md              every F-entry; yours: F15–F17, F25, F29, F35, F37, F40; traps T1–T13         [R]
│   ├── RUNBOOK.md               commands for everything (section 16 merges, 17 pre-push, 18 this track)      [R]
│   ├── trackB/                  YOUR records                                                                 [B]
│   │   ├── START_HERE.md        this page
│   │   ├── SOL_ARSHA.md         the newer-families run on your own Sol account, step by step
│   │   ├── TODO_B.md            your task rows (tools/make_gantt.py reads them)
│   │   ├── FINDINGS_B.md        your findings, FB1, FB2, ...
│   │   ├── sessions/            your session logs and pre-registrations, with INDEX.md
│   │   ├── figures/             (you create it) your figures: PNG, SVG and a CSV of every plotted number
│   │   └── REPORT_B.md          (you create it) your section of the report, as bullets
│   ├── tracks/
│   │   ├── TRACK_B.md           the Nov 3 handoff: results, how to run, traps, decisions; START_HERE holds  [B]
│   │   ├── SOL_SETUP.md         Sol for a second user, in general (SOL_ARSHA.md is B20's)                    [R]
│   │   ├── TRACK_A.md, TRACK_A_FIX.md                                                                       [R]
│   │   └── TRACK_C.md                                                                                       [C]
│   ├── trackC/                  Shrey's records (review teams)                                               [C]
│   ├── status/                  ONE_PAGE, TODO, STATUS, CHECKIN, FIX_SO_FAR and the Gantt (generated)       [R]
│   ├── paper/                   REPORT.md, CLAIMS, OUTLINE; figures/ (WAITING.md: slide specs), supplement/  [R]
│   │   └── tables/trackB_final.md, .csv   the final table (B18), written by tools/trackb_final.py            [B]
│   └── labeling/                RATER_GUIDE.md, LABELING_GUIDE.md, the label queue                           [R]
├── archive/
│   ├── sessions/                every session log and pre-registration up to Nov 6 (B15–B20, B24 among
│   │                            them); INDEX.md, LATEST.md                                                   [R]
│   ├── progress-round/          the progress round's slides and evidence (historical)                       [R]
│   └── merged-docs/, superseded/, MOVES.md   older docs kept for the record                                 [R]
└── cot-disclosure/              all the code; every command runs from here with ../.venv/bin/python
    ├── progress/                run_trackB.py (one runner for every provider), run_b15.py–run_b19.py,
    │                            run_b20.py (also B20's Sol runner: until Nov 15 only its report functions
    │                            change, section 2), trackB_report.py (the main table)                         [B]
    │                            run_b24.py (read Nov 4), sol_trackB.py, sol_b17.py, sol_b20.py (the Sol
    │                            job code), common.py (record format, slot(), Wilson), guard.py (the power
    │                            guard), make_canary.py and the progress round's scripts                      [R]
    ├── tests/                   CPU tests, no network; test_trackB*.py and test_trackb_final.py are yours   [B]
    │                            every other test file                                                        [R]
    ├── client.py                the Voyager client: reply cache, identity canaries, the 4-slot limit        [R]
    ├── detect.py, parse.py      cue detection, answer parsing                                                [R]
    ├── experiments.py, run.py, tasks.py, analyze.py, audit.py   the early pipeline                          [R]
    ├── agents/                  the review teams' agent team                                                 [C]
    ├── providers/               one interface over Voyager, vLLM, Hugging Face and the paid APIs
    │                            (budget.py: the spend guard)                                                 [R]
    ├── configs/                 models.yaml, trackB.yaml (your design), canary/, path_allowlist.txt         [R]
    ├── tools/                   trackb_final.py (the final table)                                            [B]
    │                            path_check.py, prepush_check.py, make_handoff_bundle.py, slide_figures.py,
    │                            export_summaries.py, make_gantt.py, make_supplement.py, sol_feeder.py, ...    [R]
    ├── finetune/                the fixes (Track A): dataset, training, evaluation, looking inside; gpu/ is the Sol kit
    │                            (gpu/sol/: job scripts, submit.sh, env.sh, accounts, the feeder's queue
    │                            files, queue_b20_2026-11-05.txt among them)                                  [R]
    ├── data/progress/           the 30 held-out questions and the 120 fresh ones: nothing is ever chosen on them [R]
    ├── results/
    │   ├── summaries/trackB/    numbers-only summaries, tracked                                              [B]
    │   ├── trackB/              your records and reports (from the zip); b20/ grows by SOL_ARSHA step 9     [B] (data)
    │   ├── voyager_canary.jsonl Voyager's identity-canary log (from the zip)                                (data)
    │   ├── trackC/              Shrey's logs                                                                 [C] (data)
    │   ├── handoff/             bundles                                                                      (data)
    │   └── progress/, scope/, *.jsonl   the progress round's evidence (tracked, historical)                  [R]
    ├── ui/                      the progress round's demo (historical)                                       [R]
    ├── cache/, logs/            Voyager's reply cache; the guard's logs, stop files and slots                (data)
    ├── .env.example             copy it to .env (gitignored) for your own Voyager key                        [R]
    └── requirements.txt         the venv's packages                                                          [R]
```

---

## 10. Git: how your work stays out of conflict with `main`

**Who owns what.** Every path has one owner (section 9's marks). `main` and `trackA-nosol` are Ritik's, `trackC-main` is
Shrey's, and **`trackB-main` is yours** from Ritik's last push on Nov 6. After that push, nobody else commits or pushes to
`trackB-main`.
- On `trackB-main` the pre-commit hook refuses any change outside your paths (section 2).
- On Ritik's and Shrey's branches the same hook refuses a change to your paths, except a merge of `trackB-main` taken
  unchanged. The one exception is a change you agreed to, committed with `PATH_CHECK_ALLOW=trackB-main` and said in its
  message. Ritik's Nov 6 handoff edits to your files, made before you started, went in that way.
- So the same file is never edited on two branches, and merges in either direction do not conflict.

**The cycle.**
1. Work and commit on `trackB-main` only, in your paths, on your machine's clone (never in your Sol clone). Push with
   `git push origin trackB-main` (the pre-push hook checks for data).
2. On check-in days with merges (Nov 15 and 18, section 6) Ritik checks your range
   (`python3 cot-disclosure/tools/path_check.py --range origin/main..origin/trackB-main --branch trackB-main`) and merges
   `trackB-main` into `main`.
3. Then you bring `main` back:
   ```bash
   git checkout trackB-main
   git fetch origin
   git merge origin/main          # a merge commit, or a fast-forward; the hooks check it
   git push origin trackB-main
   ```
   Do this also whenever Ritik tells you `main` has something you need. Never `git pull --rebase` or `git rebase` on
   `trackB-main` once pushed, and never force-push: Ritik merges from your history.
4. **Your Sol clone** pulls `trackB-main` only by SOL_ARSHA step 2's rule (`git diff --stat HEAD..@{u}` first, and only
   while no B20 job is pending or running, or when it prints nothing), since a queued job reads its code from that clone
   when it starts.

**Before each push:**
```bash
python3 cot-disclosure/tools/path_check.py --range origin/main..HEAD       # nothing outside your paths
python3 cot-disclosure/tools/prepush_check.py --rev HEAD                   # nothing produced, GPQA or over 50 MB
cd cot-disclosure && ../.venv/bin/python -m pytest -q tests/test_trackB*.py tests/test_trackb_final.py && cd ..
```

**If a merge of `origin/main` stops on a conflict** (rare, given the ownership above):
- **In a file outside your paths** (shared code, `CLAUDE.md`, someone else's docs): take `main`'s version unchanged. The
  hook accepts only that.
  ```bash
  git checkout --theirs -- <path> && git add <path>       # during "git merge origin/main", "theirs" is main
  ```
- **In one of your own files** (only if Ritik changed it with your agreement): keep both sides' intent, edit out the
  conflict markers, `git add <path>`.
- Then `git commit` (the hooks check the result). If you are unsure, `git merge --abort` puts everything back as it was
  before the merge. Then tell Ritik.

**Never:**
- push to `main`, `trackA-nosol` or `trackC-main`, or open a pull request into `main` (Ritik merges);
- force-push, rebase a pushed branch, or bypass a hook (`--no-verify`);
- commit produced data (`results/trackB/`, the zip, `logs/`, `cache/`) or `.env`;
- edit a shared file to make something work (the Sol kit and `sol_b20.py` above all: your queued jobs read them). Write a
  new module in your paths, or ask Ritik.

---

## 11. Working with Claude Code (Nov 5)

Your commits are authored and committed **by you only**. No commit names Claude as an author, a committer or a co-author,
and no commit or PR body carries a "Generated with Claude Code" line. Three layers enforce it, so it holds even if one is
missed.

1. **`CLAUDE.md` at the repo root** (tracked; read-only for you). Claude Code loads it automatically in any session started
   inside the clone. It tells every teammate's session:
   - commit only when its human asks, and only under that person's own git identity (it checks `git config user.name` and
     `user.email` first, and never uses `--author` or `-c user.name=`);
   - never Claude or Anthropic as author or committer;
   - no `Co-Authored-By` trailer, no "Generated with Claude Code" line and no `noreply@anthropic.com`, overriding any
     harness reminder that asks for them;
   - stay in your track's paths, and never put produced data or keys on GitHub.
2. **`.claude/settings.json`** (tracked; read-only for you). It turns off Claude Code's own attribution:
   `"attribution": {"commit": "", "pr": "", "sessionUrl": false}`, plus `"includeCoAuthoredBy": false` for versions before
   2.0.62. These are the documented keys ([settings reference](https://code.claude.com/docs/en/settings-reference)): empty
   strings hide the commit trailer and the PR line, and `sessionUrl: false` drops the session link that cloud and Remote
   Control sessions add.
   - Your own settings go in `.claude/settings.local.json` (gitignored; permissions, for example). Don't turn attribution
     back on there.
3. **The commit-msg hook** (section 1, step 3). It refuses the commit outright, whoever writes the message. If a session
   ever hits it, the fix is to drop the line, or to set your own `git config user.name` and `user.email`. Never
   `--no-verify`.

**Your git identity, once per clone** (section 1, step 1):
```bash
git config user.name "Arsha Jindal"
git config user.email "<your ASU email>"
git var GIT_AUTHOR_IDENT; git var GIT_COMMITTER_IDENT     # both: your name and email
git log -1 --format='%an <%ae> | %cn <%ce>%n%B'           # after a commit: you twice, and no trailer
```

**How to work with it.**
- Start each session by pasting section 7's brief. It points the session to this page and the task's pre-registration.
- Claude Code may run the reports, the tests and the hooks without asking. It asks you before any command that calls
  Voyager (a smoke or a run), before a commit and before a push.
- **Sol is yours to type.** Claude Code on your machine never logs in to Sol for you and never handles a password, Duo
  prompt, key or login; it can explain SOL_ARSHA's steps and read the outputs you paste.
- It never labels, classifies, scores or summarizes model text for a result. It never opens or prints
  `cot-disclosure/.env` (section 6, "No LLM judging"; `CLAUDE.md`).
- Read what it wrote before you commit: you are the author.

---

## Left out as stale

Each item was in the original and is not in this draft, with the reason. Arsha can put any back.

1. **Header lines of Nov 3 to Nov 7 about the handoff** (the "handoff, Nov 6, 09:14" paragraph, the earlier-entries line
   with Nov 4 and Nov 5 times). The handoff is done; its content is in sections 1, 9, 10 and 11.
2. **Quick start rows 0, 1, 2, 2a and 4** (setup on your machine; B20 on your own Sol account; the re-reads of B16, B19,
   B17, B24; B20's reading). All marked "Done" in the original; the dates survive in section 3.
3. **Section 0, "What changed since Nov 4"** (the whole section). It described the Nov 6 state: B20 on your account, the
   partial-read rule, the queue-owner rule, B1R2's revival, A40, the label correction, the LLM-judge protocol, the port
   rule, the Claude Code files, the zip, `trackB-main`'s handover. All of it is now done or has moved: the project-wide
   points are in `CLAUDE.md`, `docs/FINDINGS.md` and the glossary; the "no LLM judging" rule is kept in section 6.
4. **Section 1, step 8 (Sol: B20 on your own account)** and the Sol-specific text of Quick start's "On Sol". B20 is finished
   (Nov 6) and nothing of this track runs on Sol; the steps remain in `SOL_ARSHA.md`.
5. **Section 4's progress notes**: "Where it stands (Nov 5)", the account of Nov 4's stop-file failure and its fix (commits
   `a530e80`, `e420ad1`), the cause confirmed in T13, "Runs left" (Granite 849 of 972, Gemma 1,784 of 1,944, Nemotron 0),
   the Nov 5 amendment's 3:00 lines, "Your account from Nov 5", "Your queue" (10 places and 960 GPU-minutes), and the
   Nov 6 and Nov 11 rules. They describe a run that ended Nov 6; the results and the design stay (section 4).
6. **Section 4's "You run the jobs and copy back"** as an instruction, folded into the short "Copying back from Sol" line.
7. **The queue-owner lines** (Ritik's queue says `owner: ragarw68`, B20's says `owner: not ragarw68`). Left out with
   item 5: they belong to B20's runs, which ended Nov 6. The rule they explained (the feeder refuses a queue file whose
   owner line doesn't match the Sol user running it) lives on in section 7's brief and `SOL_ARSHA.md`.
8. **Quick start's "Your next steps" rows 3 and 5 as one-liners**: row 3 (check B18) is now "done Nov 14" and shortened to
   the "What is left" table; row 5 stays there.
9. **"Check-ins with Ritik: Nov 6, Nov 12, Nov 15 and Nov 18"** shortened to the two still ahead (Nov 15 and 18); the
    past two are in section 3.
10. **In section 6's merge rule, "On Nov 12, 15 and 18"** shortened to Nov 15 and 18, for the same reason. In section 10,
    the same.
11. **The Nov 14 status paragraph of the original's header** was merged into "Where things stand".
