# Session log: the repository reorganization, APPLIED (2026-10-30 22:30 MST)

Project: CSE 598 Group 10, all tracks. Step 2 of the reorganization, after Ritik's "go" on the proposal
([`2026-10-30_2141_ALL_reorg-proposal.md`](2026-10-30/2026-10-30_2141_ALL_reorg-proposal.md)). Also in this session: Track C's
handoff shortened before Shrey receives it, and the Gantt reworked to say what is done and what is left. **By:**
Ritik. Nothing is pushed: main, trackB-main and trackC-main are brought to the new tip locally only.

Rules (Ritik's, unchanged from step 1):
- move with `git mv`, never delete;
- every moved, merged or archived file goes in [`docs/MOVES.md`](../../docs/MOVES.md): old path, new path, why;
- merge only real duplicates; each original is kept unchanged in `archive/merged-docs/`, and the merged doc keeps
  every non-duplicate fact;
- no code, tests, configs, sbatch files or anything a Sol job reads moves;
- produced data (results/trackA|B|C, finetune/data, labels, logs) is never moved or touched;
- numbers-only summaries that code or tests read stay where they are.

## a. What moved (131 files, all with `git mv`)

| files | from | to | why |
|---|---|---|---|
| 54 | `docs/sessions/` | `archive/sessions/<date>/` (INDEX.md and LATEST.md at `archive/sessions/`) | history: logs and dailies, a folder per date |
| 66 | `presentation/` | `archive/progress-round/presentation/` | the October progress deck and its assets |
| 3 | `cot-disclosure/results/pilot_stdout.txt`, `pilot_stdout_v2.txt`, `progress_log.txt` | `archive/progress-round/results/` | progress-round console logs no code reads |
| 3 | `docs/progress/STATUS.md`, `GANTT.xlsx`, `gantt.png` | `docs/` | living status, beside FINDINGS, PLAN and TODO |
| 1 | `docs/OVERVIEW.md` | `archive/superseded/OVERVIEW_2026-10-27.md` | the Oct 27 snapshot; its content lives on in FINDINGS, PLAN, STATUS and the code guide |
| 1 | `docs/paper/README.md` | `archive/merged-docs/paper_README.md` | merged into the root README (below) |
| 1 | `cot-disclosure/ui/README.md` | `archive/progress-round/ui_demo_README.md` | the demo's guide; the ui/ code stays |
| 1 | `cot-disclosure/finetune/README.md` | `docs/TRACK_A.md` | Track A's design doc, with the living docs |
| 1 | `cot-disclosure/finetune/PROVENANCE.md` | `docs/TRACK_A_PROVENANCE.md` | B1/B2's method doc, beside it |

The moves are their own commit, with every file's content unchanged, so `git log --follow <new path>` shows each
file's whole history. The edits (links, paths, the regenerated status files) are the next commit.

**The merge:** `docs/paper/README.md`, a 14-line index of the paper pack, went into the root README's folder map,
which lists every file it listed with the same descriptions. Its original is byte-identical at
`archive/merged-docs/paper_README.md`. **Dropped as duplicates:** none.

**Rewritten in place, the earlier version kept:**
- `README.md`: now the front door (the question, the story in five lines, where to start for each reader, the
  folders, quick start). The Oct 27 version is at `archive/superseded/README_2026-10-27.md`.
- `docs/handoff/TRACK_C.md`: 186 → 160 lines (below). The long version is at
  `archive/superseded/TRACK_C_2026-10-30_long.md`.
- Both kept versions are word for word the same as before. Only their link targets changed, so the links resolve
  from the new folder. Checked: 0 differing lines once link targets are blanked.

**Not moved:** all code, tests, configs, sbatch files, `results/summaries/`, `docs/progress/LABEL_QUEUE.csv` and
`RESULTS_SUMMARY.json` (code reads them), and all produced data.

**The tree after:**

```
/ (2 files)          README.md, .gitignore (now `!/archive/` instead of `!/presentation/`)
cot-disclosure/ 379  code, configs, tests, summaries (6 docs and logs moved out)
docs/            77  11 living docs at the top; handoff 3; paper 59; progress 4
archive/        130  sessions 56; progress-round 70; superseded 3; merged-docs 1
```

## b. Links and paths

- `fix_links.py` (scratchpad) rewrote every relative markdown link to a moved file, and every link inside a moved
  file, from the move table.
- `fix_copies.py` did the same for the two kept versions.
- By hand: path mentions in plain text, in FINDINGS, PLAN, RUNBOOK §20, TODO (D2, D3, the header), the code guide,
  the GPU kit's README, and the Track A docs' moved-from notes.
- The tools:
  - `tools/make_supplement.py` reads logs from `archive/sessions/<date>/`. It finds each log's first commit under
    either folder, since git's rename detection hides the add under the new path.
  - `tools/check_links.py` skips `archive/merged-docs/`. Those originals are kept unchanged, so their links point
    where they used to be.
  - `tools/make_gantt.py` (§d).
  - Each has its tests.
- **Progress-round scripts:** `analyze_progress.py`, `build_evidence_viewer.py`, `common.py`, `extract_slides.py`,
  `make_bundle.py`, `take_screenshots.py` and `ui/screenshots.py` point to `archive/progress-round/presentation/`.
- **Docstrings and messages:** `agents/c15.py`–`c18.py`, `progress/run_b15.py`, `finetune/__init__.py`,
  `finetune/source_tags.py`, `finetune/gpu/checkpoint_check.py`.

## c. Nothing went missing (the script and its output)

`scratchpad/reorg/nothing_missing.py`, run from the repo root with the file list saved before the first move
(`git ls-files` at `50076f2`):

```python
before = Path(sys.argv[1]).read_text().split()
now = set(subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.split())
moves = dict(re.findall(r"^\| \d+ \| `([^`]+)` \| `([^`]+)` \|", Path("docs/MOVES.md").read_text(), re.M))
same = [f for f in before if f in now]
moved = [f for f in before if f not in now and moves.get(f) in now]
missing = [f for f in before if f not in now and moves.get(f) not in now]
listed_wrong = [o for o, n in moves.items() if n not in now or o not in before]
```

```
before: 582 tracked files; now: 587
at the same path: 451; moved and listed in MOVES.md: 131; missing: 0
MOVES.md rows whose new path isn't tracked or old path wasn't: 0
```

The 5 new files: the two kept versions, `docs/MOVES.md`, `docs/gantt.pdf` and the proposal log. This log makes 588.

## d. The Gantt, reworked (`tools/make_gantt.py`)

It reads the new paths, and still reads `docs/sessions/` if a clone has it. It checks whether `origin/trackA-nosol`
holds HEAD, so a task blocked only by "the push" is no longer blocked once the push is done.

- **`docs/GANTT.xlsx`:**
  - **Gantt:** a row per task, milestone and window, with ID, label, owner, start, end or due, status, the basis
    for each date (inferred dates flagged), dependencies, the full item text and the source.
  - **To do** (replaces Remaining): each open task with its next action, estimate, blocker and the milestone it
    feeds; each milestone with what it needs. The sheet's notes run checks on TODO.
  - **Done:** every finished task by date, with a one-line delivery (the finding and its key number) and its
    evidence (findings with their commit, session logs, commits).
  - Progress, Daily and Changes, as before.
- **`docs/STATUS.md`:** per track, "Done since Oct 27", "Next" (ordered, owner, due) and "Blocked on". Then each
  owner's list (Ritik; Arsha, Track B from Nov 3; Shrey, Track C from Oct 30), each milestone with what it needs,
  and the next 7 days.
- **`docs/gantt.pdf`** (new): an overview, then a page per track with a bar per task.
- **`docs/gantt.png`:** the milestone labels no longer collide.
- **One more rule, tested:** a task whose status cites three or more findings, none of which names it, gets no
  single finding as its delivery. Before, B9 (the Gate 2 question, answered across F15–F17 and F29) showed F29's
  title, and B14 (the table) showed F15's.
- Gantt tests: 36 → 46.

**Stale TODO statuses fixed (the Gantt's checks found them):**
- **A13:** done Oct 29; S2 passed as vllm_check 66928369.
- **A19:** in progress; trained Oct 28 as lora_attn3, evaluation in A16.
- **A29:** Step 9 was read (A32, F32).
- **A30:** forced done; the old queue clause dropped.
- **A32:** the "needs step9_reduced.npz" tail dropped.
- **A37:** rule fixed in `fd1a679`; ready to submit as places free.
- **A6:** `main` settled by A7.
- **A16:** the Oct 29 order marked as carried out.
- **B9:** done, clear for all four models, Qwen3-8B's gap added from F29.
- **B14:** Qwen3-8B is in the summary.
- **C13:** queue lines folded.
- **G2:** in progress, half met.
- **H1:** on GitHub since Oct 30.
- **L3:** after L4, before L5.
- **L4:** waits on a pull on Sol, not the push.
- **PLAN's header:** points to the archived Oct 27 overview as what was done by Oct 27, and to STATUS for progress
  since.

**Progress now:**

| track | done |
|---|---|
| A | 29 of 37 |
| B | 11 of 15 |
| C | 17 of 23 |
| Labels | 2 of 5 |
| Repo | 4 of 6 |
| **All** | **63 of 86 (73.3%)** |

## e. Track C's handoff, cleaned before Shrey receives it

`docs/handoff/TRACK_C.md` is now a front page and a reference part:
1. The answer in five lines.
2. The results table, C4–C18, with the checker, what's refuted and the limits.
3. Deployment.
4. The first day.
5. His plan, C19–C24.
6. Reference: the team, the files, the decisions he inherits, the traps.
7. The bundle (43 files).

Every number in it is from FINDINGS. Every path in it exists after the moves.

## f. Sol: a `git pull` changes no code path the queued jobs use

What a pull brings into the code Sol runs (`finetune/`, `finetune/gpu/`, `agents/`, `providers/`, `configs/`):
- three changed lines, all docstrings or a printed message:
  - `finetune/__init__.py`'s docstring;
  - `finetune/source_tags.py`'s docstring;
  - a message string in `finetune/gpu/checkpoint_check.py`;
- two docs moved out of `finetune/` (README.md, PROVENANCE.md), which no code opens.

**Checked:**
- `grep` finds no reference to a moved path in any code file under those folders.
- `progress/common.py`'s `PRES` constant changed, but no Sol job imports `progress/`. Only the Mac-side
  `finetune/voyager_capabilities.py` uses `progress.common`, and the module makes no folder at import.
- No sbatch file, `env.sh`, `submit.sh`, `guard.sh`, config or job script changed.

Ritik pulls only after the current queue is done anyway.

## g. Checks

All run on the final tree, on this Mac (Track A's data present):

| check | result |
|---|---|
| the tests (`python -m pytest -q`) | 639 passed, 0 failed (4:17) |
| `tools/check_links.py` | 0 broken links, 0 missing RUNBOOK scripts |
| `tools/make_supplement.py --check` | all generated files numbers-only. Its 3 CLAIMS mismatches (2.6's C14 numbers, log only) and 12 source problems are the same as at `50076f2` (diffed) |
| `tools/make_gantt.py --dry-run` | 86 tasks, 63 done; 112 rows; 183 commits |
| `tools/make_handoff_bundle.py --track B --dry-run` | 14 files, 31.6 MB |
| `tools/make_handoff_bundle.py --track C --dry-run` | 43 files, 31.3 MB |
| nothing missing (§c) | 0 missing, 0 bad MOVES rows |
| TRACK_C.md's numbers against FINDINGS and CLAIMS | 14 intervals and 11 "X of Y" counts, all found |
| the pre-push check (`tools/prepush_check.py --rev`) | "nothing produced, GPQA or over 50 MB in the push" (exit 0) |
| commit metadata | author and committer Ritik on both commits; no attribution lines |

**The commits:**
1. The 131 moves alone, each file's content as at `50076f2`, plus the new `.gitignore`. Built in a separate
   index (`scratchpad/reorg/commit_moves.py`), so git pairs every rename at 100%.
2. Everything else: links, paths, docs, tools, tests, the regenerated status and supplement files, this log.

`main`, `trackB-main` and `trackC-main` were fast-forwarded to the new tip locally. **Not pushed**; that waits
for Ritik.

## h. The note for Shrey

Track C hasn't gone to Shrey yet, so nothing he was given has moved. The note to send with the link:

> Shrey: Track C is yours from today. Start at `docs/handoff/TRACK_C.md` on `trackC-main`: the answer in five
> lines, the results, your first day and your plan (C19–C24). For GPUs: `docs/handoff/SOL_SETUP.md`. The repo was
> reorganized tonight. Old session logs are in `archive/sessions/<date>/`, and `docs/MOVES.md` lists every file
> that moved. The data bundle (`trackC_20261030.tar.gz`) comes through ASU storage, never GitHub. Create your own
> Voyager key; never use anyone else's.
