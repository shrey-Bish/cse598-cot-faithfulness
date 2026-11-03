# Session log: the Nov 3 big session: corrections, Track C as its own workspace, B20, E2 and A39, the clean-up (Nov 3, 11:05– MST)

By: Ritik. Ritik's message of about 11:05, five parts and 19 items, worked in order. This log is written as the work
goes. Each structural change has its plan here before it is made, as Ritik asked.

## Part 1. Corrections and quick items (committed as `6ea9016`)

1. **Arsha's handoff is Nov 6, not Nov 3.** The 10:00 "sent" is corrected in TODO H2, TRACK_B (title, §0, §1),
   PLAN, README, the TODO owner column (12 rows: "Arsha, from Nov 6") and the note in the Nov 1 daily. Her bundle is
   rebuilt on Nov 6 morning.
   - **Started for her (TRACK_B §1a): B18's table and slide 2.**
     - `tools/trackb_final.py` writes `docs/paper/tables/trackB_final.md` and `.csv` from the tracked summaries. It
       has 8 model settings: following per channel, Gate 2 with clustered intervals, B16's authority arm, and B17's
       efforts labelled §13.
     - Slide 2 is `docs/paper/figures/gate2.png`, drawn from the same rows (`fig_gate2`).
     - 5 new tests. I wrote them before the code but ran them only after, so I didn't watch them fail.
   - TRACK_B §1a says what is done and what she takes over: checking, B20's rows, three decisions, the text.
2. **A18:** all four jobs COMPLETED on Sol, but their outputs aren't on the Mac. The user-hint folders still hold 15,
   16 and 8 cuts, and there is no `step9_lora`. Left there; the copy-back lines are in §10.
3. **L3, prepared for the settling call; nothing judged:**
   - **(a) The settling sheet:** `results/labels/L3_settle.csv` (`label_kit.py settle`, gitignored). It holds the 23
     rows with the 25 disagreements: both raters' labels and notes side by side, `to_settle`, an empty third column
     pair (`settled_label_private`, `settled_label_final`) and an empty `guide_rule_that_decided_it`.
   - **(b) The fresh batch:** `results/labels/fresh/` (`label_kit.py fresh`, gitignored), 72 rows.
     - **Source:** L3's own sources (Test 2, the pilot) have only 25 hinted runs left outside the queue, too few to
       balance. So the draw comes from Track B's Oct 27–28 Voyager runs of L3's three model types: Olmo 3 7B Think,
       Qwen3 30B Thinking and Qwen3 30B Instruct.
     - **The draw:** seeded (`L3-fresh-20261103`), 12 per model and channel (user; tool = pasted, own call or
       inserted turn).
     - **Exclusions:** runs in no sheet (982 run ids excluded: L5's batch, bare or not, and L3's and L4's keys), with
       a final answer over 30 characters (L5's bare rule, Oct 28).
     - **Size:** 48 private and 72 final cells, about 85 minutes per rater at L3's pace.
     - No label or keyword was looked at in choosing it.
   - 2 tests, failing first, then 9 of 9.
4. **D12 done:** `finetune/__init__.py` and `finetune/source_tags.py` name `docs/tracks/TRACK_A.md`;
   `progress/common.py`'s `DOCS` is `docs/labeling`, which nothing reads; archive/MOVES.md is updated.

## Part 2. Track C as Shrey's own workspace: the plan, written before the changes

**Who owns what, by path.** Shrey works only on `trackC-main`, and only in these paths:
- `cot-disclosure/agents/`;
- `cot-disclosure/tests/test_trackC_*`;
- `docs/trackC/` (new);
- `docs/tracks/TRACK_C.md`;
- `cot-disclosure/results/trackC/` and `cot-disclosure/results/summaries/trackC/`.

Everything else is read-only for him. If he needs a change elsewhere, he writes a new module under `agents/` or
asks Ritik. `tests/test_agents_dataset.py` doesn't match `test_trackC_*`, so it is read-only for him too, as the
allowlist reads.

**The plan:**
1. **The allowlist: `cot-disclosure/configs/path_allowlist.txt`** (tracked; `configs/` is read-only for him, so he
   can't widen his own list). One line per rule, `<branch> <path>`: a path ending in `/` is a folder, anything else
   a glob. Only branches listed there are checked.
2. **The check: `cot-disclosure/tools/path_check.py`** (standard library only, so a plain `python3` runs it as a
   hook):
   - **As a pre-commit hook** (he installs it once, like the pre-push check): on a listed branch it refuses a commit
     whose staged files (added, changed, deleted or renamed, both names of a rename) fall outside the allowlist.
   - **During a merge** (`MERGE_HEAD` present): a file outside the list passes only if it is exactly the version from
     the branch being merged in. So he can merge `main` into `trackC-main` and take its files unchanged, but can't
     edit them in the merge.
   - **`--range A..B`, for review:** every path changed between the merge base and the tip, as Ritik checks before
     merging his branch into `main`.
   - **Tests** (`tests/test_path_check.py`) on throwaway git repos:
     - an allowed commit passes and a refused one is refused;
     - a merge that takes main's files unchanged passes, and one that edits them is refused;
     - other branches aren't checked;
     - `--range` reports the paths outside the list.
3. **His records, so no file is edited by both of us:** `docs/trackC/`
   - `START_HERE.md`;
   - `TODO_C.md`: Track C's rows moved from `docs/status/TODO.md`, history kept. TODO.md keeps a one-line pointer.
   - `FINDINGS_C.md`: new Track C findings, numbered FC1, FC2, … so they never collide with FINDINGS' F-numbers.
     F18–F34 stay in FINDINGS.md, which links to it, and Ritik merges at the end.
   - `sessions/INDEX.md`: his session logs go in `sessions/<date>/`.
4. **`tools/make_gantt.py` reads every TODO:** `docs/status/TODO.md`, `docs/trackB/TODO_B.md` and
   `docs/trackC/TODO_C.md`. Each table's track still comes from its heading. This needs a test, failing first.
5. **The same layout for Track B** (`docs/trackB/`), for Arsha on Nov 6:
   - START_HERE (pointing to TRACK_B.md until Nov 6);
   - TODO_B with Track B's rows moved;
   - FINDINGS_B (FB1, …);
   - sessions/INDEX.
   - Ritik keeps them current until Nov 6. No path allowlist for `trackB-main` yet, because Ritik didn't ask for
     one; the same file takes it when wanted.
6. **What doesn't move:** no code folder or module. TRACK_C.md stays as the track's design record and links to
   START_HERE.

**Done as planned** (commit `f603110`):
- **The allowlist and its check.** `path_check.py` has 7 tests on throwaway repos, all failing first:
  - an allowed commit passes and a shared file is refused;
  - a deletion or rename of a shared file is refused;
  - a wider list staged in the same commit doesn't help;
  - other branches aren't checked;
  - a merge may take main's files unchanged but not edit them;
  - `--range` reports outside paths.
- **The TODOs.** 25 Track C rows went to `docs/trackC/TODO_C.md` and 19 Track B rows to `docs/trackB/TODO_B.md`,
  verbatim; TODO.md keeps a pointer for each.
  - `make_gantt.todo_paths` reads all three. Its test failed first; 51 of 51 pass.
  - The Gantt counts Track B and Track C as before.
- **The records.** `FINDINGS_C.md` (FC1, …) and `FINDINGS_B.md` (FB1, …) exist; FINDINGS.md links to both. Each track
  has `sessions/INDEX.md`. Track B's START_HERE points to TRACK_B until Nov 6.
- **START_HERE.md (Track C)** was drafted from TRACK_C, FINDINGS and the four pre-registration logs, then checked
  (§2a below).
- **Shrey's bundle:** `results/handoff/trackC_20261103.tar.gz` (gitignored):
  - 43 files, 31.3 MB raw, 5.1 MB packed;
  - all of `results/trackC/` (C15's items, every team log and summary) plus Track B's `steered_cases.jsonl`;
  - verified against its manifest; no GPQA.
  - C19, C20, C25 and C26 read only these. Drawing new fresh items would need the training pool, which no prepared
    run does.

## Part 4, so far: E2 and A39 (their pre-registration is the 11:30 log, commit `61db5af`, before any run on E2)

The full record is in [`2026-11-03_1130_A_e2-a39-prereg.md`](2026-11-03_1130_A_e2-a39-prereg.md).
- **Item 12:** PLAN's honest verdict (one paragraph, "The fix, honestly").
- **Item 13, E2:** 120 questions, 30 per evaluation category, seed `e2-20261103`, sha256 `59c5c250…`.
  - Its size comes from Gate 3's own runs (`make_e2.py --power`), not the GPU cap: at 120, following is ±3.8 to
    ±4.9 and acceptance ±3.7 to ±3.9.
  - Checked by id and text: none of the 30, the pool, set A, Track B's 54 or C15's items.
- **Item 14, A39:** 7 systems, a lean design of 12 runs a question, and shared runs where the wrapper's prompt is
  identical (60 a question, 9,000 with the 30 beside), with rules R1–R4.
  - **Added: LoRA + wrapper,** because it is cheap (4 runs a question) and asks whether marking adds to training.
  - The implementation is under way.
- **Item 15, B1R2:** written as conditional: it runs only if the Sol plan leaves about 60 GPU-hours by Nov 15 after
  A39 and B20.

### §2a. START_HERE, checked; the handoff verified as Shrey would run it (items 7–8)

**START_HERE.md** (866 lines; drafted from TRACK_C, FINDINGS and the four pre-registrations, then reviewed):
- the setup, hand-back and brief sections were read line by line; the bundle line was corrected to Nov 3's contents;
- the brief names no product; every number in its results section is copied from FINDINGS;
- **its additions, kept and listed here for Ritik:**
  - a smoke step before each run, with its own log, read by no rule;
  - one-line meanings for C25's four spot-check labels, from the guide's rules;
  - figures written to `docs/trackC/figures/` and placed by Ritik at merge;
  - halt handling: an unreachable Voyager resumes; a canary failure or a changed model stops and goes to Ritik;
  - the assistant asks Shrey before any command that calls Voyager.

**TRACK_C.md fixed where it contradicted the decisions:**
- a header says START_HERE holds;
- the bundle is now Nov 3's;
- FC entries, logs, summaries and figures go where START_HERE says.

**RUNBOOK §0:** C19, C25, C20 and C26 now run without a further go from Ritik, since they are pre-registered and
their choices were confirmed Nov 1.

**The fresh clone** (`git clone` of this repo at `5f38123` as `trackC-main`, the commit pushed today):
1. The allowlist, `path_check.py` and `docs/trackC/` are all present.
2. **The bundle:** unpacked with `--exclude MANIFEST.json`. `--verify` printed "bundle matches its manifest"; 42 files
   are in `results/trackC/`; C15's items hash begins `10dd00e3e8f5bc0e`.
3. **Tests:** Track C's 8 files and the allowlist's give **54 passed**. The full suite in the clone is in §11.
   - The clone reused the project's virtual environment; a fresh `pip install` wasn't repeated.
4. **The hooks:**
   - a commit of a session log under `docs/trackC/sessions/` **went through**;
   - a commit touching `cot-disclosure/client.py` was **refused** (exit 1, naming the file);
   - `--range` over the branch is clean.
5. **F18, F24 and F34 reproduced with no calls:**
   - F18: Olmo 32B with the private reasoning corrects 6 of 73;
   - F24: −55 [−70, −38], "defers"; H23 +14 [−13, +37], "not supported";
   - F34: +47 [+29, +65], "more corrections";
   - each summary is byte-identical to the tracked copy in `results/summaries/trackC/`.
6. **One thing to tell Shrey:** the run guard (`progress/guard.py`) uses macOS's `pmset` and `caffeinate`. If his
   machine isn't a Mac, the guard won't start, and he should say so before C19.

### §2b. The message for Ritik to send Shrey (item 9)

> Hi Shrey, Track C is set up for you to run on your own from today.
> - **Branch:** `trackC-main`. Start with `docs/trackC/START_HERE.md`; it has everything, and where TRACK_C.md differs,
>   START_HERE holds.
> - **Your paths** on that branch: `agents/`, `tests/test_trackC_*`, `docs/trackC/`, `docs/tracks/TRACK_C.md`,
>   `results/trackC/` and `results/summaries/trackC/`. Install the two git hooks in START_HERE §4; the first refuses a
>   commit outside those paths, the second keeps data off GitHub.
> - **Data:** `trackC_20261103.tar.gz` (5 MB) is in our ASU storage folder. Unpack it into `cot-disclosure/` and run
>   `--verify` (START_HERE §4, step 6).
> - **First two tasks:** (1) setup, the tests and the three no-call reproductions of F18, F24 and F34, which should
>   match exactly; (2) C19 by its pre-registration, due Nov 7.
> - **To hand back:** push to `trackC-main` and tell me; I review and merge into main.
> - **One check first:** the run guard uses macOS tools. If you're not on a Mac, tell me before C19.

## Part 5, item 18: the sloppiness audit and its fixes (docs only, plus one constant)

**How the audit was done:** a read-only audit of 18 docs against the facts of Nov 3 found 81 problems: 41 stale or
wrong statements, 20 out-of-date TODO rows, 10 numbers that disagree and 10 long or duplicated passages. They were
fixed as below. Line numbers are as of `5f38123`.

**Stale or wrong statements:**
- **PLAN:**
  - the header is one line, and the history is in git;
  - the Sol order;
  - the open questions: B1, B17 and L4 moved to "known";
  - the map, dated Nov 3, now has rows for A18 (done on Sol), B18 (started), B20, E2, A39 and B1R2;
  - a new calendar to Nov 18;
  - Gate 2: five models, and L3's kappa;
  - Gate 3: L4 read; it waits on A18 and A39;
  - slides 2, 5, 8 and 12;
  - the report outline's B1 line;
  - "confirmed same-day (B19)";
  - the 458 lines of Oct 31 per-track design notes replaced by a pointer (they are word for word in
    `archive/superseded/PLAN_2026-10-31.md`);
  - the risks rewritten for Nov 3.
  - 695 → 274 lines.
- **FINDINGS:**
  - the header is one line (a 27-line changelog before);
  - story line 1: "all five Track B models";
  - story line 4: the family reading, now confirmed over four families (F30), so the stale "tentative" line was
    deleted;
  - F3's status;
  - F20's two "waiting (Gate 3)" lines;
  - F26's "Step 9 isn't read" (it is F32);
  - F27's generation line;
  - the Oct 27 figure plan replaced by a pointer;
  - "*waiting*" defined as in CLAIMS ("going or planned").
- **CLAIMS:**
  - the header;
  - the obsolete `[TONIGHT]` line deleted;
  - set A "tonight" → Oct 29, and Step 9 read;
  - 1.6's behavior (F28);
  - 1.8, B2: dropped.
- **README:**
  - line 5: A18 done on Sol, A39 and B1R2;
  - the read-first table sends Shrey and Arsha to their START_HERE;
  - the folder map has `trackB/`, `trackC/`, `paper/REPORT.md` and `paper/tables/`.
- **TODO.md:**
  - the header is one line;
  - one status vocabulary, shared with TODO_B and TODO_C;
  - current cells for A17, A18, A30, A36, L3, L4, L5, G2, G3, H1, H2 and D14 (each points to the logs for history);
  - "Blocked by" cleared on A17, A18 and L4;
  - L4's and L5's owner: "Ritik and Shrey";
  - H2's item: "final by Nov 6";
  - the old Notes section moved word for word to `archive/superseded/TODO_notes_2026-11-03.md`.
- **TODO_B:**
  - the closed-provider rows are renamed B21–B23 (they were B1–B3, which clashed with the attention scaling) and
    marked dropped for cost (Part 3);
  - B9, B17 and B18 are current, and B20 is added;
  - done rows' owner: "Ritik", never a later owner for past work;
  - B4's time column.
- **TRACK_B:**
  - the header;
  - the bundle line, sized on Nov 6;
  - B16/B19 due Nov 7;
  - five models;
  - §5 links TODO_B, dated Nov 3, with B18 and B20;
  - B16 "confirmed same-day";
  - the closed providers dropped.
- **TRACK_A:** the header (steps 1–13 done; Gate 3 met Oct 31; A18 and A39 open), steps 6–7 and 11–13 done, the
  fourth version's line, and Gate 3's date.
- **TRACK_A_FIX:** B2 dropped; B1R and B1R2; LR_GATE approved Oct 29; B1's GPU hours as run (34.3 for 630).
- **RUNBOOK:**
  - the header;
  - TODO pointers;
  - §0's Sol order (Nov 3);
  - the test count;
  - §14's status;
  - §15's labels (both sheets in; settle; the fresh batch);
  - §17's pre-commit hook lines;
  - §18's status;
  - B17 and A38 marked done and dropped;
  - §19's Track C status;
  - §20: whose logs go where.
- **RATER_GUIDE:**
  - raters "Ritik and Shrey";
  - L3 and L4 part 1 returned;
  - rows for L3's settling and its fresh batch;
  - the kappa rule's wording aligned with PLAN's "per channel" (written Oct 27). This changes no verdict: L3's final
    answer fails overall too, and L4 passes everywhere.
- **WAITING.md:** the preamble (slides 2, 4, 7, 8 made; Shrey's figures go under `docs/trackC/figures/`), slide 8's
  owner, B1 read, slide 2 → `gate2.png`, slides 5 and 9.
- **SOL_SETUP:** the per-user kit is on `trackC-main`; his accounts file stays uncommitted (it is outside the
  allowlist); C13's run dates (Oct 29–30, 66954278).
- **OUTLINE:**
  - a dated header pointing to REPORT.md;
  - contributions with 5 models and F36, F38 and L4;
  - the setup's models;
  - Gate 2 table;
  - set A's Step 9 (F32);
  - B2 removed;
  - "missing" now A18 and A39;
  - the mechanism in two models.
- **The code map (`cot-disclosure/README.md`):** `path_check.py`, `slide_figures.py`, `trackb_final.py`,
  `path_allowlist.txt`, E2's file, and the tracks' own folders.
- **`tools/make_gantt.py`:** Track B's takeover date Nov 3 → Nov 6, the source of STATUS's "Arsha from Nov 3". The
  Gantt tests' fixtures and expectations moved to Nov 6; 51 of 51 pass.

**Numbers that disagreed:**

| # | what | fix |
|---|---|---|
| N1 | the family reading | confirmed, F30 |
| N2 | TRACK_B's bundle size | sized on Nov 6 |
| N3 | trackB-main | kept at main until Nov 6 |
| N4 | the test count | 745 on Nov 3 |
| N5 | B1's GPU hours | as run |
| N6 | Gate 3's date | Nov 20 |
| N7 | the kappa wording | above |
| N8 | B4's engine and hours | vLLM, 2:01 |
| N9 | C13's dates | Oct 29–30 |
| N10 | the training-target median | left: the two numbers are different snapshots, each labelled where it appears |

**Not done, on purpose:**
- **L7:** TODO_C's C19–C26 cells repeat TRACK_C §5. That is Shrey's file now; he may trim it.
- **L8:** F28's "earlier readings, interim" (66 lines) stays. The supplement's DEVIATIONS check reads strings in F28,
  and moving them risks unverifying rows.
- **L9:** the repeated phrases ("§13", "underpowered") stay where each is a label the rule asks for. They were cut in
  TODO's cells.
- **The ID clash between E2 (the set) and PLAN's old batch-3 job "E2":** the job ID left with the removed PLAN
  sections. `eval_job.py`'s docstring still says "jobs E1-E6", and the A39 change is editing that file now.

**After the fixes:**
- `check_links`: 0 broken.
- The supplement: 34 ledger rows (A39 and B1R2 added), none unverified, no log outside it; DEVIATIONS 0 unverified;
  CLAIMS the same 3 old mismatches.
- `make_gantt --dry-run` parses everything.

**A correction of times (12:20):** several times written today ran ahead of the clock.
- **"Last updated" lines and the amendment:** PLAN 12:30, FINDINGS 12:40, TODO 12:50, TRACK_B 13:00, and A39's
  amendment at "13:45". These were corrected to the times the edits were made (about 12:00 and 12:15).
- **Two commit messages:** `5f38123` says "12:05" and `3ae88c7` says "13:20". Git records them at 11:41 and about
  12:05. They were left as written, because their hashes are cited in today's docs. **Git's commit times are the
  record.**

## Part 3: B20, open models instead of closed ones (items 10–11)

**Closed models are dropped for cost** (TODO_B: the closed-provider rows B21–B23 dropped).

**Item 10, the models, from a web check of the Hub's metadata, model cards and vLLM 0.31.0's parser registries**
(each claim with its source in the pre-registration):

| model | why | licence and gate | reasoning switch | vLLM 0.31.0 parsers |
|---|---|---|---|---|
| **Gemma 4 26B-A4B-it** (Google) | a new family; strong; MoE, fits one A100 | Apache-2.0, ungated | `enable_thinking` | `gemma4` (reasoning), `gemma4` (tools) |
| **Nemotron 3 Nano 30B-A3B** (NVIDIA) | a third lab and another architecture (hybrid Mamba/MoE) | NVIDIA Open Model License, ungated | `enable_thinking` | `nemotron_v3`, `qwen3_coder` |
| **Granite 4.2 8B** (IBM) | off/low/full modes in one set of weights; the 8B for GPU hours | Apache-2.0, ungated | `enable_thinking` | `granite_thinking_parser` (a plugin from the snapshot, as its card serves it), `qwen3_coder` |

- **Granite's family (4.1) was a Track C reviewer;** this is said in the log.
- **Excluded:**
  - Phi-4-reasoning: its chat template drops system and tool messages;
  - the DeepSeek-R1 distills: no tool calling in vLLM, and the Qwen-based ones are Qwen weights;
  - SmolLM3: too weak, and served only through Transformers;
  - Magistral: reasoning always on, and its base model is Mistral Small 3.2, a Track C reviewer.
- **None needs a licence acceptance on Hugging Face.** Nemotron's licence is NVIDIA's own and should be read.

**Item 11, pre-registered** ([`2026-11-03_1219_B_b20-prereg.md`](2026-11-03_1219_B_b20-prereg.md), before any run):
- **Design:** Track B's 54 questions × 6 conditions (with B16's `user_authority`) × 3 runs × thinking on and off.
  1,944 runs a model, 5,832 in all, at each model's recommended sampling.
- **Readings, per model and setting:**
  - R1, Gate 2;
  - R2, tool or authority (B16's rule);
  - R3a, the bare answer after a call against with the pasted block;
  - R3b, thinking on minus off on it.
- **Checks before any run:**
  - the served-template check, by token ids;
  - a canary at temperature 0, compared across jobs;
  - a smoke of the first 12 runs, clean only if all 12 ran, at least 10 answered, everything parses, the tool path ran
    and the reasoning split is right.
- **A fallback fixed in advance:** the inserted tool turn, if a model's own call doesn't work.
- **Revisions pinned in code:** Gemma `4d7ae498…`, Nemotron `bf77c317…`, Granite `a7042144…`.
- **Code:** `progress/run_b20.py`, `progress/sol_b20.py`, `b20.sbatch` and `get_b20.sbatch`, with `submit.sh` and
  `run.sh` kinds. Its tests: 29 passed, 1 skipped (the real-template test needs a cached tokenizer). They failed first.
- **The dry run:** 2.8–13.1 GPU-hours for all three, at 650–1,310 tokens/s (B17's measured rate, and half of it).
- **Two calls made on the way:**
  - **Gemma is served with its snapshot's own template,** not vLLM's example one. The check compares against the
    snapshot's template, so the example one would likely stop the smoke by design. Decided before the log was
    committed.
  - **Granite gets its card's parser plugin.**
- **Runs by Nov 15, read by Nov 17; Arsha's from Nov 6.**

## Part 4, the rest: A39's code, B1R2, and Sol (items 14–17)

**A39's code** (`finetune/eval.py`'s question set, design and systems; `finetune/a39.py`, R1–R4;
`finetune/gpu/eval_job.py --gpus N` serving one vLLM with `--data-parallel-size N`):
- Its tests: 22 new ones (all failing first), plus 5 lines of existing tests updated for intended signature changes.
- Gate 3's own design, files and report are unchanged.
- **Its dry run:**
  - E2: 7,200 runs, about 43 GPU-hours, 11 four-GPU jobs;
  - the 30: 1,800 runs, about 11 GPU-hours;
  - both at batch 3's 500 tokens/s per A100.
- **The amendment** (the 11:30 log §9, before any run) makes explicit: no-answer counts beside every reading (and
  "no-answer imbalance" over 5 points), the wrapper's pooled readings diluted by design, every tool output marked in
  later rounds too, A39's own experiment name and folder, and the job shapes.
- **E2's file** is in the Sol kit's eval inputs (`kit.py --manifest`: `inputs_manifest.json`, `sol/inputs.txt`).
- **Sol kinds:**
  - `a39` (4 GPUs, one data-parallel server, 192 in flight, a 2-hour limit: half the 960 GPU-minutes);
  - `a39_1gpu` (the 30's jobs and the bench's 1-GPU shape).
  - `submit.sh` refuses a missing system or question set.
  - The kit's account test now checks the class QoS's real limits (up to 4 GPUs, GPUs × limit ≤ 960) instead of
    "1 GPU". A new `submit.sh` test passes.

**B1R2** stays conditional (11:30 log §5). Its job lines need `provenance_job` on E2, which isn't written. They come
in an amendment if the calendar leaves about 60 GPU-hours by Nov 15.

**Item 16, Sol used fully.** The limits, from `accounts.conf` (confirmed Oct 27, re-checked Oct 30) and ASU's public
docs:
- per job: up to 4 GPUs, 32 cores, 320 GB, 24 h;
- per user: 2 running, 10 submitted, **960 running GPU-minutes**;
- every recorded GPU an A100 80 GB;
- the H100s are listed as privately owned, so probably not ours.

**The shapes:**
- 2 jobs × 4 GPUs × a 2-hour limit = 960, so **8 A100s at once**;
- 1-GPU jobs give 2 at once.

**To confirm on a login node** (no job):
```bash
sacctmgr -P show qos class format=Name,MaxWall,MaxTRES,MaxTRESPU,MaxTRESRunMinsPU,MaxJobsPU,MaxSubmitPU
sacctmgr -P show assoc where account=class_cse59888883fall2026 format=Account,User,QOS,GrpTRES,MaxTRES,MaxJobs,MaxSubmit
sinfo -N -h -O "NodeList:10,PartitionName:10,Gres:32,Features:40" | grep -i -E 'h100|a100' | sort -k3 | uniq -c -f2 | head
sbatch --test-only -A class_cse59888883fall2026 -p public -q class -G h100:1 -t 1:00:00 --wrap=true   # H100: allowed?
sbatch --test-only -A class_cse59888883fall2026 -p public -q class -G a100:4 -t 2:00:00 --wrap=true   # 4 A100s: when?
```

**The bench (TODO R3), before the big runs.** Both count toward base's E2 runs, and nothing is read from them but
speed:
```bash
S=cot-disclosure/finetune/gpu/sol/submit.sh
$S a39 --estimate 0.75 -- base e2 1/2 --limit 384          # 4 GPUs, data-parallel, 192 in flight (limit 1:00)
$S a39_1gpu --estimate 0.75 -- base e2 2/2 --limit 96      # 1 GPU, 48 in flight (limit 1:00)
```
- **What it measures:** tokens/s from vLLM's "Avg generation throughput" lines
  (`/scratch/ragarw68/trackA/a39/vllm_*.log`), minutes to start, and each job's wait in the queue.
- **The rule for the shape:** if 4 GPUs give at least 3× one GPU's tokens/s, E2 runs on 4-GPU jobs. Otherwise it
  runs on 1-GPU jobs (2 at once), and the calendar below stretches by about 2 days.

**The GPU hours to Nov 15:**

| work | GPU-hours | jobs |
|---|---|---|
| A39 on E2 | ~43 | 11 × 4 GPUs, 2 h |
| A39 on the 30 | ~11 | 7 × 1 GPU |
| B20 | 3–13 | 3 downloads with no GPU; 3 smokes and 3 mains on 1 GPU |
| B1R2 (if it fits) | ~60 | 1-GPU jobs of up to 8 h, Hugging Face engine |
| **in all** | **117–127** | |

At 8 A100s, A39's E2 is about 6 hours of running time. The 1-GPU work, two at a time, is about 2–3 days. **The class
account fits A39 and B20 by Nov 15 with days to spare. B1R2 fits if queue waits stay under about a day per round.**
If they don't, the request to Prof. Davulcu for the lab account would be **about 60 GPU-hours on 1 A100 a job (B1R2's
share) for Nov 9–14**. No other account is used without Ritik's OK.

**Item 17, the Sol calendar to Nov 18** (in Ritik's priority: A39 on E2, then B20, then B1R2):

| when | on Sol | on the Mac |
|---|---|---|
| Nov 3 evening | pull; the login-node reads; B20's three downloads (no GPU); the bench | A18's copy-back and reading (its jobs are done) |
| Nov 4–5 | A39 on E2: 11 four-GPU jobs, two at a time (in waves, at most 10 submitted) | the bench's numbers into the plan |
| Nov 5–7 | B20: three smokes, then three mains (1 GPU); A39 on the 30 (7 × 1 GPU) | each B20 smoke's check |
| Nov 8 | the decision on B1R2 (about 60 GPU-hours left by Nov 15?); its amendment and lines if yes | Gate 2 (L3) |
| Nov 9–14 | B1R2 if it fits; any reruns | A39's reading as parts come back |
| Nov 15 | runs end | |
| Nov 17 | | A39 read (Ritik); B20 read (Arsha) |
| Nov 18 | the freeze | |

## §10. A18's copy-back (item 2; its jobs are done, its outputs not on the Mac)

```bash
# on the Mac, from cot-disclosure/ (numbers only; the sources stay on Sol)
H=ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68
rsync -av --exclude 'sources_*' $H/trackA/a18/ results/trackA/gpu/a18/
for d in results/trackA/gpu/a18/step10_*; do printf '%3s cuts  %s\n' "$(ls $d/cuts | wc -l | tr -d ' ')" "${d##*/}"; done
# complete: base_on_base 30, base_on_base_user 22, lora_on_base 30, lora_on_base_user 22, lora_on_lora 18, lora_on_lora_user 12
ls results/trackA/gpu/a18/step9_lora/step9/
```
Then I read the primary (the swap and Step 10) and Step 9's secondary by the 22:44 log's rule, and draw slide 10.

## Judgment calls, each with its cost if wrong

1. **The L3 fresh batch comes from Track B's runs,** not L3's own sources, which have 25 runs left. It uses the same
   three model types and both channels, in no sheet, with finals over 30 characters.
   - Cost: a slightly different mix of texts from L3. Kappa is still read per channel by the same rule.
2. **E2's size is 120 questions,** from Gate 3's own variance: following ±4.9 at worst, acceptance ±3.9.
   - Cost: if Sol's queue is slow, B1R2 gives way first, not E2.
3. **A39 adds LoRA + wrapper** (4 runs a question). Nothing else was added, to protect power.
4. **The wrapper marks tool-role turns only.** The pasted block sits in the user's turn, which a system can't tell is
   a tool's output, so it serves as the wrapper's control.
5. **B20's models:** Gemma 4, Nemotron 3 Nano and Granite 4.2 8B.
   - Granite's family was a Track C reviewer; this is disclosed.
   - Gemma is served with its own snapshot template.
6. **Shrey's START_HERE adds a smoke step, label meanings, figures under `docs/trackC/figures/`, halt handling, and
   "ask Shrey before any Voyager call".**
   - Cost: none to the rules; they are operational.
7. **Doc audit L8 left as is:** F28's interim readings stay, because the supplement's DEVIATIONS check reads strings in
   them.
8. **The kit's account test now allows 4-GPU jobs** within the 960 GPU-minutes, as item 16 asks. It no longer checks
   for 1 GPU.

## What's waiting for Ritik

- **Send Shrey** the message (§2b) and `results/handoff/trackC_20261103.tar.gz` through ASU storage.
- **L3:** the settling call with Shrey (`results/labels/L3_settle.csv`), then the notes for tightening the guide.
- **Sol, in order** (the first step after this push):
  1. `git pull --ff-only` on Sol.
  2. The login-node checks of Part 4: the QoS and H100 lines, and B20's parser grep (the 12:19 log's line 0).
  3. A18's copy-back on the Mac (§10).
  4. B20's three downloads (`get_b20`; no GPU).
  5. The bench (`a39` and `a39_1gpu` with `--limit`).
  6. After the bench: A39 on E2's 11 jobs; then B20's smokes and mains; then A39 on the 30.
  7. On Nov 8: the B1R2 decision.
- **Nov 6 morning:** Arsha's bundle and note (H2).
- **If H100s turn out to be allowed** (the `--test-only` line), A39's jobs could use them. B17's kernels are tied to
  the A100, so that would need a bench first.
