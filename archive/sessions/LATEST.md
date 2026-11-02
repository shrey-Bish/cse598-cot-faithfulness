# Session log: B17's template check amended for its last try; B1's part 8; the story's line 1 (Nov 2, 14:10–15:00 MST)

By: Ritik. Ritik's message of about 14:10, eight items: the standing rules (0), B17 first (1), B1's part 8 and the
finished parts (2), Sol's queue (3), the story's line 1 and the README (4), Arsha's note and her bundle (5), A37 in
plain words (6), and the push (7).

## 1. B17: why the smoke stopped, and the fix

**What Ritik reported:** the smoke 245445 stopped 22:26 into the job (exit 4) at the served-template check, before
any run. Its log reads "template check: FAILED (... low system differs ... medium system differs ... high system
differs)", and the other four conditions were "identical" at all three efforts. The server had started fine (vLLM
0.31.0, the options check passed). The main run 245462 was cancelled by its dependency. Ritik copied
`template_check.json` to `results/trackB/b17/`.

**The difference** (`template_check.json`, then rebuilt on the Mac):
- **Two newlines, in one place.** Both renderings of the `system` prompt have 379 tokens and are identical through
  token 87, the developer header and `# Instructions` included. At token 88:
  - the chat template has `...(source: study guide v2).\n\n<|end|>`;
  - vLLM has `...(source: study guide v2).<|end|>`.
- **Why:**
  - **The chat template** (`6cee5e81`, `chat_template.jinja` lines 246–248) always writes `\n\n` after the developer
    instructions, as the separator before `# Tools`, even when there are no tools.
  - **Harmony, as vLLM renders it,** puts a separator only between sections.
  - **Only `system` is hit:** it is Track B's only condition with instructions and no tools.
- **Ritik's guess, half right.** Both renderings put our note in the developer message; the difference is only that
  trailing blank line.
- **Which is the model's format: harmony, as vLLM serves it.**
  - vLLM renders with `openai-harmony`, OpenAI's renderer of the format gpt-oss was trained in. The jinja template
    re-implements it for `transformers`.
  - The note already sits where harmony puts a request's system prompt: the developer message's instructions.
    Harmony's own system message holds the effort and the date.
  - So the requests stay as they are.
- **The fault was the check's.**
  - The pre-registration's rule passes prompts "differing in whitespace only". Its code collapsed runs of whitespace
    to one space, which leaves `). <|end|>` against `).<|end|>`.
  - So whitespace on one side only counted as a difference.

**The fix** (`e008a9d`, pushed 14:26; [B17's pre-registration, §12](2026-10-31/2026-10-31_2237_B_b17-prereg.md)):
- **"Whitespace only"** now means the decoded texts are equal once all whitespace is removed. Any other difference
  still stops the job before any run.
- **Whitespace-only rows** in `template_check.json` now also give the first difference and the text on each side.
- **Checked on the Mac** (no calls; the real chat template from the local Hugging Face cache):
  - **The job's numbers:** our 15 prompts give the job's own token counts.
  - **The server's side:** deleting only that blank line gives the server's 379 tokens and, exactly, its text at the
    first difference, at each effort.
- **Tests:** two new ones in `tests/test_trackB_b17.py` failed on the old code and pass now (14 of 14).
  - One rebuilds the smoke's 15 prompts from the real template: with the old check it fails as the job did; with the
    fix it passes.
  - The other is a minimal case: whitespace on one side only, beside a real difference that still stops.
- **Not chosen:**
  - **A new reference** (`openai-harmony`'s own rendering): it isn't installed on the Mac, and it would be new code on
    the day.
  - **Sending the note another way:** it already arrives as harmony expects.
  - **Dropping `system`:** nothing in how it is served is wrong.
- **The failed check is kept** as `results/trackB/b17/template_check_245445.json` (gitignored), so the copy-back
  can't overwrite it.

**The one-day rule (§6):**
- **The clock** started with the first smoke (Nov 1, about 15:57 MST). This is its one fix and one resubmission.
- **Ritik's reading:** the rerun must start before about 16:00 today.
- **§6's words:** the smoke must be *clean* 24 hours after the clock starts. The first smoke took 22 minutes to reach
  the check, so a start before about 15:20 meets the words as well.
- **If the smoke isn't clean, B17 is dropped:** TODO says "dropped (could not run cleanly within one day, Nov 2)".

**The pull on Sol is safe for the queued jobs.** Since `2f9306f` (the oldest commit Sol can be at), the pull brings
`run_b17.py` and its tests, `run_b19.py`, three tools (`export_summaries`, `make_supplement`, `slide_figures`), their
tests, and docs. The two job types' imports, traced statically and transitively:
- **B1's parts** (`finetune/gpu/provenance_job.py`): none of these files.
- **A18's jobs** (`finetune/look/a18.py`): they reach `progress/sol_b17.py` only inside vLLM's preflight
  (`vllm_options.job_commands`, imported inside a function), which calls `serve_cmd` (unchanged). `sol_b17` loads
  `run_b17` only inside its own job.

## 2. Sol's lines (given to Ritik after the first push)

Queue at Ritik's message: 10 of 10, all pending.
- **B1:** part 9 (334078) and part 10 (334081).
- **A18, tool-only (§8):**
  - Step 3: base 334084 (A), lora 334085 (B);
  - Step 10: 334111, 334112, then 334113 (afterok B);
  - the swap: 334114;
  - Step 9: base 334115, lora 334116 (afterok B).

No job can end before 16:00, since none is running. So 334116 is cancelled to make the place, as Ritik offered.

```bash
cd /scratch/ragarw68/cse598-cot-faithfulness
git pull --ff-only && git log -1 --format=%h      # e008a9d or later
squeue -u ragarw68
scancel 334116                                    # A18 step9 lora; resubmitted later (below)
S=cot-disclosure/finetune/gpu/sol/submit.sh
F=/scratch/ragarw68/trackA/provenance_forced/provenance_forced.json
$S b17 --estimate 0.75 -- --smoke                 # -> K (limit 1:00)
scontrol top K
# B17's 2,430 runs: chained on the smoke if a place frees while K is pending or running ...
$S b17 --estimate 6 --dependency=afterok:K
# ... or, once K has ended (sacct -j K --format=JobID,State,Elapsed,ExitCode shows COMPLETED 0:0), in its place:
$S b17 --estimate 6
# then, as places free:
$S provenance_gen --estimate 0.75 -- --alpha-from $F --part 8/10           # B1 part 8's last run (limit 1:00)
$S a18 --estimate 0.6 --dependency=afterok:334085 -- step9 --system lora     # 334116 again (no dependency once 334085 has ended)
```

- **B1's part 8** (245547) was stopped by Slurm's warning just before its 5:30 limit, with 1 of its 63 runs left
  (`prov-a1-v2` 21 of 21, deployable 21 of 21, oracle 20 of 21). The rerun skips the 62 saved runs. One run plus the
  model load is well under an hour: the estimate is 0.75, so the limit is 1:00.
- **Copy-backs (Mac, `cot-disclosure/`, numbers only):**

```bash
H=ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68
# B1, parts 1-7 (counts only; B1's rule is read when all 630 runs are done)
rsync -av "$H/trackA/provenance_gen/eval_prov-*-v2_p[1-7]of10_runs.jsonl" results/trackA/gpu/provenance_gen/
for f in results/trackA/gpu/provenance_gen/eval_prov-*-v2_p[1-7]of10_runs.jsonl; do
  printf '%3s ok  %s\n' "$(grep -c '"status": "ok"' "$f")" "${f##*/}"; done                 # 21 each: 21 files
# B17's smoke, once K has ended
rsync -av $H/cse598-cot-faithfulness/cot-disclosure/results/trackB/b17/ results/trackB/b17/
rsync -av $H/cse598-cot-faithfulness/cot-disclosure/results/trackB/b17_sol_vllm_runs.jsonl results/trackB/
../.venv/bin/python progress/run_b17.py --smoke-check
```

## 3. The story's line 1 and the README (item 4)

- **FINDINGS, the story's line 1:** "**Confirmed same-day (B19):** B16's tool replies were cross-day, mostly Track
  B's replayed from the reply cache (T11); rerun on Nov 1 with new seeds and no cache, all six readings held (+10
  [+4, +17], +75 [+65, +85], −14 [−22, −7]; F35)". This replaces "Cross-day: the tool replies are mostly Track B's,
  replayed from the reply cache (T11), with the served models unchanged."
- **README, line 1:** "(B16, F35; confirmed same-day, B19)".
- **README, line 5:** "a second model's mechanism (Qwen3-8B) [is] under way" was out of date since A37 (Nov 1). It now
  reads "the trained model's mechanism (A18)".

## 4. Arsha (item 5)

- **The note** (Nov 1 daily): the B19 line is now "B19 (Nov 1) reran B16's tool arms the same day with new seeds
  and no cache: all six readings held (F35)." It is still 11 lines.
- **Set when the bundle is rebuilt on Nov 3:**
  - **the bundle line:** its name and size;
  - **the B17 line:** "your part" depends on today's smoke. If it isn't clean, B17 is dropped, and that line changes.
- **The bundle, Nov 3 morning** (TODO H2): rebuilt with B19's records and A37's summaries, verified, and the file
  named to Ritik. Last night's dry run gave 26 files, 59.0 MB. This needs Ritik's first message on Nov 3; nothing
  runs on its own.

## 5. A37 in plain words (item 6)

- **The rule** (fixed Oct 30, before anything ran):
  - **Choose:** find the three layers that do most of the work of carrying the tool's letter into the answer, using
    the puzzles only.
  - **Test:** on MMLU-Pro, questions not used to choose, check two things. Do those three layers still hold more
    than half of it (the 95% lower bound above 0.5)? And are they MMLU-Pro's own top three, give or take one layer?
  - **Reading:** both means "replicates"; one means "partly"; neither means "doesn't".
- **The result:**
  - **Chosen:** layers 21, 22 and 29 hold 0.74 on the puzzles.
  - **Tested:** on MMLU-Pro they hold 0.70 [0.60, 0.83] (30 cuts, 14 questions), and they are exactly MMLU-Pro's top
    three. Both conditions hold: **replicates**.
  - **The prompt's letter carries the answer.** At the takeover, swapping only the letter in the prompt (while the
    reasoning still names the old one) moves the answer in 54 of 63 and 30 of 30 cuts.
- **For line 3: yes, the readout holds in a second model family.**
  - Qwen3-8B, a different family from Olmo, also reads the tool's letter straight from the prompt at a few
    mid-to-late layers.
  - That rules out the worry that Olmo's sliding windows force it: every Qwen3-8B layer sees the whole prompt.
- **Weaker than in Olmo, and narrower:**
  - **Less concentrated:** 0.70, against Olmo's 0.90, and a fourth layer (26) adds about 0.15–0.19.
  - **One channel:** the real tool call only.
  - **Small:** 14 questions.
  - **Patching only:** no attention heads were tested in Qwen3-8B, so F12's heads aren't replicated.
- **Line 3 needs no new change.** It and the README's line 3 were updated with A37 on Nov 1 (`164eba2`). The "as a
  whole *tentative*" status stays.

## 6. Judgment calls, with their cost if wrong

1. **The check is fixed; the requests are untouched.** The served rendering is harmony's own, and the rule's words
   already allowed whitespace.
   - Cost if wrong: if someone held that the chat template is the reference, the trailing blank line would be a real
     difference. It is two newlines at the end of the instructions, and the runs use vLLM's rendering either way.
2. **Whitespace is removed, not collapsed.** This loosens the check everywhere in the 15 prompts, not just at this
   spot.
   - Cost if wrong: a whitespace-only difference elsewhere would pass unremarked. It is still recorded in
     `template_check.json`.
3. **334116 is the job cancelled,** as Ritik offered. No queued job can end before 16:00, since all ten are pending.
   - Cost if wrong: A18's Step 9 on the LoRA side starts later; it is resubmitted at the next free place.
4. **B17's main run waits for the smoke's own place** rather than a second cancellation.
   - Cost if wrong: the 2,430 runs start a little later (B17 is due Nov 12).
5. **B1's part 8 estimate is 0.75 h (limit 1:00).** That covers 1 run and the model load (0.15 h).
   - Cost if wrong: if that one run is unusually long, the job stops again and a rerun finishes it.
6. **README line 5** was corrected in passing: A37 is done, so Qwen3-8B is no longer "under way".
7. **Arsha's note was edited in place,** in the Nov 1 daily, since it is a draft for Ritik to send.

## 7. Checks and pushes

- **First push** (`e008a9d`, B17 only, before Sol's pull):
  - the full suite in a clean worktree: 725 passed, 8 skipped (6:45);
  - `check_links`: 0 broken;
  - a fast-forward of all four branches from `e6466c7`;
  - the pre-push check;
  - author and committer Ritik, with no attribution.
- **Second push** (this log, the story, the README, Arsha's note, the daily, TODO, STATUS and the Gantt): the same
  checks, plus the supplement's check.

## 8. What's waiting for Ritik

1. **On Sol now:** the pull, `scancel 334116`, then the smoke, moved to the top. It should start before 16:00, and
   before about 15:20 to meet §6's words.
2. **B17's main run:** chained on the smoke, or submitted in its place once it ends clean.
3. **As places free:** B1's part 8, then 334116's Step 9 again.
4. **Copy-backs:** B1's parts 1–7 (counts) and B17's smoke (then `--smoke-check`). If the smoke isn't clean, B17 is
   dropped.
5. **Nov 3 morning:** your first message, and I rebuild and verify Arsha's bundle and name the file. Then the note,
   with its bundle line and, if B17 is dropped, its B17 line updated.
