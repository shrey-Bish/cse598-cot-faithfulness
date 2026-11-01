# Session log: the 20-day program set up; B16 running; seven experiments prepared (2026-10-31 22:50 MST)

Project: CSE 598 Group 10, all tracks. **By:** Ritik.
- Calls: Voyager only, for B16 (pre-registered first).
- No Sol job, no paid call, no local model.
- Nothing chosen on the 30 evaluation questions.

## 1. What Ritik asked

1. **Decisions on the rater packets** (from the 20:50 log's questions):
   1. both new guide rules accepted as written;
   2. `practice_answers.csv` stays in the packet;
   3. no third L4 sheet;
   4. the examples and practice answers reviewed, with the changes to apply (see §3);
   5. push `3a98c63` and `c3d5638`.
2. **The 20-day program** (Oct 31 → Nov 20, then the report and slides Nov 21–24), replacing the planning reset:
   - **0.** The push; Qwen3-8B Step 10's real job.
   - **1.** The story in PLAN.
   - **2.** The program with owners and dates.
   - **3.** Code, CPU tests, a pre-registration log and a dry run for each new experiment; B16 on Voyager now.
   - **4.** The dates.
   - **5.** A presentation map and a report outline.
   - **6.** TODO, STATUS, the Gantt, TRACK_B and TRACK_C.
   - **7.** This log; the first Sol lines; commit, no push.
3. **During the session:**
   - What is A21? Keep it if it's required, updated to the plan.
   - The Gantt must be kept up to date after every prompt, with things marked done as they finish.

## 2. The push (done, 22:10)

- `3a98c63` (Gate 3 final) and `c3d5638` (rater packets) went to `trackA-nosol`, `main`, `trackB-main` and
  `trackC-main`, all fast-forward (`4222ff6..c3d5638`).
- The pre-push check was clean ("nothing produced, GPQA or over 50 MB"). Author and committer were Ritik, with no
  trailers.
- **Sol** is still at `4222ff6` (Ritik's single update of Oct 31).

## 3. The rater packets

- **The guide's two rules** are accepted as written:
  - a noted conflict is `mentions_only` (noticing a conflict isn't taking a position);
  - cut text is `unclear`, with the note "cut".

  `docs/progress/LABELING_GUIDE.md` now says so. The packets' own guides had no "to confirm" wording, so they are
  unchanged.
- **`practice_answers.csv`** stays in the packet, opened after the practice.
- **No third L4 sheet.** LoRA + tags' 150 candidates and LoRA on 15/19/23's 126 aren't labelled: labeling time is the
  bottleneck, and part 1 already tests the claim. TODO L4's open question is closed.
- **The examples and practice answers: not recorded as reviewed.** The decision's line for them arrived with its
  template placeholder unfilled: "[your changes here, e.g. … or "none"]". So:
  - this log does not say they were reviewed and set by Ritik;
  - `spec.json` is unchanged;
  - Shrey's packet waits for that line (TODO L3).
- **The check, rerun on both packets: clean.** Row counts L3 101, L4 part 1 294, practice 10, answers 10.

## 4. Qwen3-8B Step 10 (A37)

**123025 is the real job.** Ritik cancelled a duplicate, 125173. Before saying a job is missing, check `squeue`:
`sacct` doesn't list a job waiting on a dependency. TODO A37 now says so, and A37 is due Nov 3.

## 5. The story and the program (PLAN)

**The story.** The new top of `docs/PLAN.md` is built around one theme: "Where did that answer come from?" A tool's
influence loses its source at three levels:
- inside the model: the readout layers read the tool's letter directly;
- in the model's words: after a tool call the answer stops naming its source;
- between agents: downstream agents can't tell a tool's claim from a colleague's conclusion.

Each level lists what is known (with F-numbers) and what is open.

**The new top also has:**
- **The map:** every experiment by level, owner, due date and state; B16 is the control for all three levels.
- **The calendar:**
  - results freeze Nov 18;
  - Nov 19–20: final verdicts, figures, supplement, STATUS, and Gate 3's final statement;
  - Nov 21–22: the report draft;
  - Nov 23: the rehearsal;
  - Nov 24: the final presentation and report.
- **The gates:** Gate 2 on Nov 8; Gate 3's final statement moves from Nov 22 to Nov 20.
- **The final presentation map:** 13 slides, each with its finding, figure file (existing, or "to make"), status and
  owner.
- **The report outline:** 11 sections, one figure each.

**What else changed:**
- The version before this one is kept word for word in `archive/superseded/PLAN_2026-10-31.md`; only its link
  targets are repointed.
- The sections below the gates are unchanged apart from their dates: the evaluation deadline Nov 18, and the final
  talk and report on Nov 24.
- The README gains the theme line.

**Dropped (scope, Oct 31)**, kept in TODO and never deleted:
- B2 (A31, the provenance-gated bias);
- C21;
- C23;
- **A21**, "Hand the best version to Tracks B and C":
  - What it was: from the Oct 21 brief, running the best trained version through Track B's conditions and as Track
    C's solver, in the old plan's Nov 23–29.
  - **Not required by the program.** Gate 3's evaluation already ran all four trained versions through Track B's
    hint channels (user, pasted, inserted turn) on the 30 held-out questions (F28). Running one as Track C's solver
    needs a model that calls the tool, and Olmo 3 7B Think never does. Its window also falls after the results
    freeze.
  - The row says so.

**C22** is a stretch. **L4 part 2 and L5** are SHOULD.

## 6. B16, tool or authority? (running)

- **Pre-registration:** the 22:20 log, committed in `ca56e4e` before any run.
- **Design:**
  - the answer key's authority from the user ("My course answer key says the answer is (X).");
  - against the tool arms, run again the same day;
  - Qwen3 30B Thinking and Instruct and Olmo 3 7B Think, Track B's 54 questions, 3 runs: 1,458 runs.
- **Smoke test:** 9 of 9 answered, 0 errors. The authority sentence is in every model's prompt, with no tools.
- **The run:** under the power guard since 22:25. At 22:49, 114 runs were done (all ok, 1 without an answer).
- **The reading** waits for all 1,458 runs.

## 7. Prepared (code, CPU tests, a pre-registration log, a dry run; nothing run)

| # | what | pre-registration | tests | dry run | due |
|---|---|---|---|---|---|
| A18 | inside the fixed model: Steps 3, 9, 10 and a layer swap on batch 3's runs of base and LoRA | 22:44 | `test_a18.py` (15) | ~36 base and ~26 LoRA cases; 8 jobs, 6.6 GPU h at most | Nov 10 |
| A38 | STRETCH: the note + B1 deployable, against each alone, the inserted tool turn | 22:45 | `test_a38.py` (11) | 240 runs, ~11–14 GPU h; `plan --note` prints nothing unless B1 reads "works" | Nov 14 |
| B17 | thinking dose: gpt-oss-20b at effort low, medium, high (Sol vLLM) | 22:37 | `test_trackB_b17.py` (9) | 2,430 runs, 3.6–5.4 GPU h at assumed rates | Nov 12 |
| C19 | H34: is an authority claim the cue? | 22:31 | `test_trackC_c19_c20.py` (4, with C20) | 400 reviews, ~25 min | Nov 7 |
| C25 | across agents: solver → writer's note → decider without the tool | 22:33 | `test_trackC_c25_c26.py` (5, with C26) | 800 calls, ~1–1.5 h + a 20-row hand spot check | Nov 12 |
| C20 | pipeline vs model: blind review, a system tag, the solver's disclosure, the checker | 22:32 | (above) | 200 reviews, ~15 min | Nov 15 |
| C26 | SHOULD: a retrieval tool, no letter, no "answer key" | 22:34 | (above) | ~700 calls, ~1.5 h | Nov 15 |

- **Readings:** each log has the question, the comparison, the rule, what counts as each outcome, the cost, the dry
  run and the exact lines.
- **Track C's lines,** in order, are in `docs/handoff/TRACK_C.md` §5a, for Shrey from about Nov 4.
- **B17's lines** are in TRACK_B and RUNBOOK §18; A18's and A38's in RUNBOOK §14.

## 8. Rulings, with the cost if wrong

**B16:**
- **The tool arms run again the same day** (972 of the 1,458 runs, ~5.6 h). Cost: free Voyager hours; the
  cross-day version is reported beside it.
- **No same-day plain user arm.** Cost: the secondary comparison stays cross-day.

**The program:**
- **A21 dropped** (§5). Cost: Ritik reopens it.

**A18:**
1. **The primary is the weight swap on base's cases,** with LoRA's own cases secondary. Cost if wrong: swap the two
   readings, at no extra compute.
2. **"Acts in the reasoning"** is named in advance as a third outcome.
3. **Cut (ii) only.** Cost: ~3 GPU h to add cut (i).
4. **User-hint cases are kept** (32 of base's 98 followed runs). Test 2's were tool-only because user hints were
   rarely followed. **Ritik decides before submitting.**
5. **Runs with a tool call in the final answer are left out** (base 10, LoRA 4).
6. **A38 runs only the inserted tool turn.** Cost: ~9 GPU h for the pasted block.
7. **LoRA's weights are `lora_merged`,** exactly as the evaluation served them.

**B17:**
1. **Temperature 0.6** (Track B's), not gpt-oss's recommended 1.0. Cost: possibly more loops; counted, with the
   16,000 cut.
2. **The reasoning written before a call goes back with the call** (gpt-oss's format), unlike Track B's Qwen runs.
   Cost: none for B17's contrasts, which are within one model.
3. **Kernels are named** (`TRITON_ATTN`, `marlin`) for the A100. Cost: one failed start, then `--auto-backends`.
4. **Primary 2 counts answered runs after a call;** the share over every run with a call is reported beside it.
5. **The smoke's 15 runs count** toward the 2,430.
6. **vLLM only.** If the smoke fails twice in the day, B17 is dropped.
7. **The flags live in `results/trackB/b17/`,** so they never enter Track B's table (tested).

**Track C:**
1. **C19's own-working sentence** is "My own careful working gives (X); I follow it." (46 characters against the
   key's 45; the plan's "My working gives (X)." was 21). Cost: a weaker control if "I follow it" reads oddly.
2. **C25's writer is Qwen3 30B Instruct,** and its decider uses C4's reviewer prompt. Cost: the Qwen3 decider reads
   its own model's notes; results are reported per decider.
3. **C25's writer sees the tool log and the final answer,** not the private reasoning.
4. **C20's (a), (c) and (d) are reused from saved runs** (the same call; C18 reproduced C16 exactly). Cost: (b) runs on
   a later day.
5. **C26's passage has one wording.**
6. **C25's notes are stripped by keyword,** as in C18.

**The Gantt:**
- **`make_gantt` gains a "dropped" status.** A row whose status starts "dropped" is neither done nor open, has no bar,
  and is listed under "Dropped (scope)" on the status page.
- A log that names a dropped item doesn't bring it back.
- Two tests were added (48 pass); the new one failed on the old code.

## 9. For Ritik to decide

1. **The rater packets:** the review line (§3), "none" or the changes. Shrey's packet goes out after it.
2. **A18:** keep the user-hint cases, or tool-only? Decide before submitting.
3. **B17:**
   - temperature 0.6 or 1.0?
   - the main job chained on a clean smoke (`afterok`, as written), or `smoke_check.json` read first?
4. **Track C:** confirm rulings 1, 2 and 4, and say who labels C25's 20-row sheet (about 15 minutes, by a person).
5. **Sol hours before the Nov 18 freeze:**

   | job | GPU hours |
   |---|---|
   | B1's rerun, if the bench passes | ~37 |
   | A37 | ~1.1 + 2.6–4.3 |
   | B17 | ~4–6 |
   | A18 | 6.6 |
   | A38, only if B1 works | 11–14 |

   With two jobs at a time that is a few days of the queue. B1 is due Nov 4, so it goes first once its bench passes.
6. **The push:** this log's commit is local. Sol needs it for B17 and A18 (new job kinds `get_gptoss`, `b17`, `a18`).

## 10. The first Sol lines, in order (after the push, with Ritik's OK)

**Is a pull safe for the queued jobs (bench 122956, Qwen3-8B 123022 and 123025)?** Checked, and yes:
- `run.sh` and `submit.sh` only gain the three new kinds.
- `provenance_job.py`'s `bench`, `plan` and `generate` keep their defaults; `--note` is new.
- `qwen8b_mech.py`'s helpers behave as before:
  - `hint_spans.hint_text` changes only for records that carry their own hint text;
  - `sol_trackB.check_snapshot` keeps Qwen's defaults.
- No `env.sh`, `guard.sh` or `accounts.conf` change.

```bash
cd /scratch/ragarw68/cse598-cot-faithfulness && git pull --ff-only
squeue -u ragarw68                         # the bench 122956 and Qwen3-8B 123022, 123025 should be listed
S=cot-disclosure/finetune/gpu/sol/submit.sh
$S get_gptoss                                                    # B17's snapshot (online, ~13.8 GB) -> job G
$S b17 --estimate 0.75 --dependency=afterok:G -- --smoke        # template check + 15 runs (limit 1:00) -> job K
$S b17 --estimate 6 --dependency=afterok:K                      # the 2,430 runs (limit 8:00, resumable)
```

- **B17's one-day clock** starts when the smoke job starts running.
- **A18's eight lines** (RUNBOOK §14) go in as submission slots free (MaxSubmitPU 10). Start with the two Step 3 jobs.
- **B1's resubmit lines** come from `provenance_job.py plan` once the bench's line passes its gate.
- **Copy back:**
  - B17's numbers only: `results/trackB/b17/` and `b17_sol_vllm_runs.jsonl`;
  - then, on the Mac, `progress/run_b17.py --smoke-check`.

## 11. Docs and checks

- **Docs updated:**
  - PLAN (§5);
  - TODO: due dates on every open item; A18, A38, B16, B17, B18, C19, C20, C25, C26 and D4–D10 added or rewritten;
    the dropped items; L3 and L4;
  - TRACK_B (B16, B17, B18);
  - TRACK_C (§5 rewritten to the program, and §5a, ready to run);
  - RUNBOOK §14, §18, §19;
  - the README; LABELING_GUIDE.
- **STATUS and the Gantt** are regenerated (§12).
- **Results of the checks** are in the commit message.

## 12. The Gantt after every prompt (Ritik, Oct 31)

A standing rule from now on, also TODO D10: after each session's work, TODO is brought up to date (finished items
marked done) and `tools/make_gantt.py` regenerates STATUS and the Gantt in the same commit.
