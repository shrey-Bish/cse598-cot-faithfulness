# Session log: the scratch pad, the demo's main screen (2026-11-23 13:24 MST)

**By:** Ritik. Branch `trackA-nosol`, from `360acd1` (main, `trackA-nosol`, `origin/main` and `origin/trackA-nosol`
level). The day's second session; the daily: [DAILY_2026-11-23](2026-11-23/DAILY_2026-11-23.md). The previous session: Nov 23,
[09:10](2026-11-23/2026-11-23_0910_ALL_front-door.md). The results are frozen: the tag `results-freeze-2026-11-18` on `7e1fdc0`.
Presentation work only. Two helpers: the pad's page, then its live mode; the review team's flow and the local server.
They did not commit.

## 0. Input

A pasted prompt, acted on as Ritik's: "THE SCRATCH PAD: rebuild the demo's main screen as one scratch pad". Keep every
existing part working; the pad becomes part 1 and the default screen of the local build.
- **Phase A:** a read-only script, `results/demo/sol/fetch_all.py`, fetching every evaluation run of the fixes, the dial,
  Qwen3-8B, gpt-oss and Nemotron. First estimate its size, then give the one command for Ritik's Mac and the unpack
  command.
- **Phase B:** the pad: the top row; the question and the hint on the left; the streaming pad with highlights from the
  analysis's own keyword matcher; the final answer and three red-pen checks; the version row and the split; the
  review-team flow; "next run"; one JSON per question, served on localhost, with the drawn set embedded.
- **Phase C (time-boxed):** "your own question", live through Ollama.
- **Checks:** every dataset, two sizes, both themes, offline. Tests: the highlights are verbatim, every count is
  DATA's, every run traces to its file and line. Screenshots.

## 1. What was done (13:24–14:32)

**Phase A, the full Sol copy** (`tools/demo_template/sol.py plan_all` writes `results/demo/sol/plan_all.json` and
`fetch_all.py`, gitignored; `unpack_all` reads the stream):
- Same pattern as the drawn copy (stdlib only, reads only, nothing written on Sol, paths printed as `<scratch>`), but
  every evaluation run: kept by the run ids in this Mac's numbers-only indexes (the frozen sets).
- Groups and the run ids in the Mac's indexes:

  | group | ids |
  |---|---|
  | the fixes on the 120 (nine systems) | 10,080 |
  | the 30 (Gate 3's six and A39's on the 30) | 7,380 |
  | the attention dial (B1R2 on the 120, B1 on the 30) | 2,024 |
  | Qwen3-8B, thinking on and off | 1,620 |
  | gpt-oss-20b | 2,430 |
  | Nemotron (no index here: its whole file) | about 1,944 |

- Per run, the record minus the raw text and the prompt messages (the transcript keeps the tool call and reply).
- The output is one gzip stream, with progress on stderr. A cut stream is reported, not hidden.
- **Estimate:** about 25,500 runs and about 240 MB compressed (200–280 MB; per-run sizes measured on the drawn copy),
  about 1.1 GB if fully expanded. It stays compressed on the Mac.
- **Found before Ritik ran it:** one run id, `c43d897ec5a49dd1`, names three runs on Sol. The Mac's index keeps the
  one in an unsplit file (`eval_base_a39_e2.jsonl.gz`), which the first globs missed. The unsplit files are added.
  - Texts now match their index rows by run id **and** timestamp, in the pad and the bench (`runs.py`).
  - Before, the bench showed one of the other two runs' text under that row; that row is now "outcome only" until the
    full copy is in.
- Tested on a fake tree, including a cut stream.

**Phase B, the pad** (the local build's part 1 and default screen; the map, the bench and the sheets are parts 2–4,
unchanged; the tracked page is unchanged and carries none of the pad's code):
- **Data** (`tools/demo_template/pad.py`, mine): one JSON per question under `results/demo/pad/<dataset>/`, plus an
  index. The question counts are in the table below.
  - Each run carries its file and line, and its text gzipped with the spans where the analysis's own keyword matcher
    fires.
    - `runs.spans_of`: `detect.COMPILED`, chosen as `trackB_report.flags()` and `finetune/eval.py` choose it, plus
      `SOURCE_WORDS` for the fixes' broad final.
    - Offsets are in UTF-16, so the page slices the same characters.
  - Outcomes are the analysis's own fields.
  - Texts come from this Mac (the Voyager runs, the review logs) and the Sol copy (the full copy when unpacked, else the
    drawn copy).
  - Counts: `DATA.pad` (`pad.counts()`), every one with its path in the frozen data (the explainer's compact or a frozen
    summary: `eval_report.json` for Gate 3, `a39_mmlupro_30.json`).
  - The drawn questions are embedded (15.7 MB, the page now 34.5 MB), so a double-click still works.

  | dataset | questions |
  |---|---|
  | the 54 | 54 |
  | the 30 | 30 |
  | the 120 | 120 |
  | the review team's items | 175 (the 73 graded wrong lookups' cases with two ungraded, and C15's 100) |

- **The page** (helper 1: `pad.js`, `pad.css`, `shell.js`, `shots.py`):
  - The top row: Dataset, Question (search by id or words), Hint (source, wording, wrong or right) and Model.
  - The question and the hint's sticky note or tool slip on the left.
  - The pad streams the private reasoning with every recorded span highlighted: 3,000 characters a second, at most
    20 s; Esc or a click finishes.
  - The final answer and three red-pen checks from the run's fields.
  - The version row: 13 versions, the untested ones greyed. Picking one splits the pad: no fix (the same experiment's)
    beside it; for the dial, its own control at α 1.
  - Under each half, the frozen count for that condition.
  - "Next run" cycles the recorded repeats; every run is labelled, with its file and line on hover. Large type: nothing
    under 23 px.
  - Mine: the call hint opens on "a study guide", the wording every version, the dial too, was run with. On the 30,
    Gate 3's runs come first. The 54 open on Qwen3 30B Thinking.
- **The review team** (helper 2: `padreview.js`, `padreview.css`): solver → reviewer (choose the reviewer and what it
  sees) → checker → you, left to right.
  - Each step shows its recorded verdict and its file and line; the frozen counts sit beside it.
  - What reaches the user follows the pipeline's rule (`agents/run_team.py` lines 31–32: a flag escalates and no answer
    ships; otherwise the reviewer's letter).
- **The server** (helper 2, `serve.py`): 127.0.0.1 only, GET and HEAD, no listings, nothing outside `results/demo/`.
  Mine: `POST /live`.
- **TALK_MAP's live run:** the part keys shifted by one (the pad is key 1), with a note on the pad.
- **README:** `docs/demo/README.md` says how to start the pad.

**Phase C, live** (`tools/demo_template/live.py`, mine; the page by helper 1):
- "Your own question (live)" in the Dataset list, over the server only. Qwen3-8B (`qwen3:8b`; this Mac's Ollama has no
  Olmo), thinking on, temperature 0.6.
- It uses the experiments' own prompt builder (`tools/answer_key.build`), the answer parser, `trackB_report.flags` and
  the spans.
- The version row is greyed, "recorded runs only". No count is shown, nothing is saved, and the run is labelled "not a
  recorded run, never counted".
- **Times** on this Mac:

  | question | hint | total | tokens | Ollama |
  |---|---|---|---|---|
  | planet | the user says it | 21.8 s | 323 | cold |
  | 17 × 23 | pasted | 66.4 s | 1,569 | |
  | prime | the user says it | 47.1 s | 1,140 | through the server |
  | planet | | 14–16 s | | helper 1, through the page |

**After the freeze (Nov 23, 13:24): presentation work only.** No number, figure or verdict changed. The pad shows
recorded runs, labelled, and the frozen counts with their paths; a live run is never counted.

## 2. Waiting for Ritik

1. **The full Sol copy** (Ritik's Mac, ASU VPN, one Duo push), from the repo root:
   ```
   cd ~/Documents/Projects/ODL/cse598-cot-faithfulness/cot-disclosure && ssh -o ConnectTimeout=30 login.sol.rc.asu.edu 'P=/scratch/$USER/envs/olmo/bin/python; [ -x $P ] || P=python3; $P -I -S -' < results/demo/sol/fetch_all.py > results/demo/sol/fetch_all.jsonl.gz
   ```
   Then, in `cot-disclosure/`:
   - `python3 tools/demo_template/sol.py unpack_all`;
   - `../.venv/bin/python tools/demo_template/pad.py`;
   - `../.venv/bin/python tools/demo_template/build.py`.

   The 30's and the 120's runs and the dial then show their text; until then they are outcome rows, marked "outcome
   only".
2. **Start the pad:** `../.venv/bin/python tools/demo_template/serve.py`, from `cot-disclosure/`. It needs the venv for
   live mode, and Ollama running for live (`ollama serve`). It opens `http://127.0.0.1:8765/demo.html#pad`.
   Double-clicking `results/demo/demo.html` works too, but with the drawn questions only.
3. As before: publishing the seeded runs, a LICENSE, Pages (Shrey), the username in the logs, the four files; Prompt 2
   tonight.

## 3. Checks and push

**The walk** (Playwright; both builds):
- Every dataset in 13 states: a wrong hint and a right hint; the user, pasted and call sources; another model on the 54;
  the split with fine-tuned, 3 layers, consistency and the dial; the review flow on a C4 case and a C15 case.
- At 1920×1080 and 1440×900, both themes, both file:// with the network off and served on 127.0.0.1: **104 states**.
- **Results:**
  - 0 console errors.
  - 0 requests but the file or the local server.
  - 0 text cut by its box (the top row's question is cut short with "…" on purpose).
  - The sheet inside the window every time.
  - Keys 1–4 switch parts.
  - The tracked build: its three parts and keys 1–3, as before, with no pad.
- **Screenshots:** `cot-disclosure/results/demo/screens_pad_final/` (104, gitignored); helper 1's in `screens_pad/`, the
  live mode's included.
- **Looked at:** two contact sheets of 13 (file:// 1920 light; served 1440 dark), the split's checks cropped, and helper
  1's split, default and review shots.
- **Found and fixed:**
  - The dial greyed on the default wording.
  - The 54 opening on a model with no reasoning.
  - The run label breaking inside its date.
  - A red check drawn half way in a screenshot was the animation, not a cut.

**Tests:**
- `tests/test_demo_pad.py` (new): the index covers the four datasets; the highlights are verbatim spans that agree with
  each run's own recorded flag; every count resolves to the frozen data, and the page carries exactly those counts;
  every run traces to its file and line; the full copy's script only reads and its stream unpacks; on the page, with the
  network off, the marks are the recorded spans.
  - 6 passed.
  - 1 skipped: the full copy's completeness, until Ritik's fetch.
- `tests/test_demo_template.py`: the browser test finds parts by id and walks the pad too.
- The full suite once: **1,408 passed, 2 skipped** (15 min 46 s; the second skip is the full copy's completeness). pad.js
  changed during it (the run label), so the demo's tests ran again on the final sources: 176 passed, 1 skipped.
- `tools/check_links.py`: 0 broken links. `make_supplement.py --check` and `export_summaries.py --check`: pass.
- STATUS and the Gantt; the pre-push check.
- The push: `git push origin trackA-nosol:main trackA-nosol:trackA-nosol`.
