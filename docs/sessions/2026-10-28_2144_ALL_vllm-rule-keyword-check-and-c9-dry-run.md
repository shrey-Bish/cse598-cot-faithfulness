# Session log: the vLLM preflight rule, the Python crash, the keyword check, and C9's dry run (2026-10-28 21:44 MST)

Project: CSE 598 Group 10. Track A trains Olmo 3 7B Think on Sol to stop hiding hint-following; Track
B measures hint-following across open models and channels; Track C runs a solver/reviewer/checker
team on Track B's cases. This log covers Ritik's 21:30 message (the vllm_check failure and decisions
on the 18:23 log) up to the start of C9. C9's results get their own log.

## 1. Header

- **Time:** 2026-10-28 21:44 MST. **Track:** all. **By:** Ritik.
- **Branch:** `trackA-nosol` (= `main`); `trackB-main` and `trackC-main` move to this log's commit.
- **Input:** Ritik's message: vllm_check 66862780 failed after 6:23 at the preflight ("choices 1:
  --mm-processor-device"); he copied sg018's option list to `finetune/gpu/vllm_serve_options.txt`.
  S7 is 66865939, waiting on 66862721 and 66862726 (training ends in about 1–1.5 h). Decisions:
  S7 on all four versions; a 20-row keyword check; C9 (pre-approved on Voyager once this dry run is
  in a session log); FINDINGS F18 and a "story so far". Then, mid-turn: "fix this python crashing,
  its happening again and again".

## 2. What ran

- **Mac, no model calls:**
  - `vllm_options.py --check-commands --installed 0.31.0` on the new list;
  - `label_kit.py trackb` (rebuilt);
  - `val_loss.py --dry-run lora tags lora_tags lora_attn3` (real tokenizer);
  - C4's summary, regenerated (identical to the exported one after the refactor);
  - C9's dry run (§5);
  - the tests.
- **Voyager:** C9, started 21:46 under the power guard, after its dry run (§5) was in this log.
  The first 28 reviews had 0 errors, and every one gave a letter.
- **Sol:** nothing by me. Ritik's lines are in §6.

## 3. Changes

**vLLM preflight (`finetune/gpu/vllm_options.py`).**
- **sg018's list checked:** it differs from the Mac's CPU list in one line,
  `--mm-processor-device {auto,cpu}` → `{auto,cpu,cuda}`, which no server command uses. All 9 server
  commands fit it: 8 Track A (6 eval systems and the check's 2 servers), 1 Track B Qwen3-8B. The
  list's second header line now says where it came from.
- **The new rule (Ritik's):** a GPU job stops only if an option or value a server command uses is
  missing or changed on the node:
  - the option is gone;
  - a value we pass is not among the node's choices;
  - the option changed form (a flag on one list, taking a value on the other).
  Any other difference is a `WARNING:` line in the job's log, and the job goes on. The node's list is
  still saved (`vllm_serve_options_node.txt`) to copy back.
- **One call of mine:** an option we use that gained or lost other choices, with our value still
  accepted, is a warning, not a refusal (e.g. a new `--tool-call-parser`). Say if it should refuse.
- **Tests:** `test_a_vllm_job_refuses_only_what_the_server_commands_use` (a used option missing, a
  used value outside the choices, a used flag that takes a value; a command misfit is still refused
  before vLLM runs) and `test_other_differences_on_the_node_are_a_warning_in_the_log` (the Mac list
  vs sg018's; an unused option added and one removed; `--dtype` with an extra choice).

**The Python crash ("Python quit unexpectedly").**
- **Cause:** every crash report today is ours: 11 since 12:07, each a SIGABRT whose parent is
  Python (`~/Library/Logs/DiagnosticReports`). The preflight's time limit sent SIGABRT to vLLM so
  Python's faulthandler would print its traceback. The test of that limit runs a fake Python
  `vllm`, and macOS reports each abort as a crash. It happened at every test run since 12:07.
- **Fix:** past the limit the preflight now sends SIGUSR1. A `sitecustomize` put first on vLLM's
  path registers faulthandler for it, which prints every thread's traceback, even inside C code;
  then the process is killed. Nothing aborts. The test now also checks that no SIGABRT arrives.
- **Checked:** after the change, the vLLM tests ran with no new crash report.
- **Risk:** if Sol's vLLM environment had its own `sitecustomize`, ours would hide it for the help
  run only (the server doesn't get it). It has none that we installed.

**Labeling (`tools/label_kit.py trackb`): the keyword check.**
- 20 of the 45 bare real-call replies of Qwen3 30B Thinking not in the spot check, seeded (seed
  20261027, "private"), go last in the sheets as group 3: rows 152–171.
- They show the private reasoning only, with no final answer, and `label_final` is `n/a`.
- `key.csv` marks them (`private_check`). `kappa` reports each rater's agreement with the keyword on
  them (a label other than no_mention = the keyword's "mentions").
- **Now:** the keyword says the reasoning names the tool in 20 of 20. The agreement comes from the
  labels.
- **Rows to label:** 171 (68 + 83 + 20). The progress-round queue (L3, 101 rows) still goes first.

**S7 (`finetune/val_loss.py`) on four versions.**
- Nothing to change: it takes any of train.py's four versions.
- **Dry run:** 9 systems (base + 4 versions × 2 epochs), 5 models built, **45–80 GPU minutes** on an
  A100. That is inferred from lora's training rate, not measured.
- `--estimate 1.25` gives a 2:00 limit (120 GPU-minutes). `run` refuses at once, before any GPU
  work, if a version's epoch checkpoint is missing (e.g. a training job failed).

**C9 (`agents/run_team.py --rereview`).**
- **What runs:** only the reviewers, again, on C4's completed tool-team cases:
  - the same saved solver answers, explanations, private reasoning and tool logs (the tool log
    is rebuilt from the logged steps: the same text, tested against `solver.tool_log`);
  - C4's checker flag for the pipeline outcome;
  - C4's settings (temperature 0.6, seed = repeat, the 8,000-token cap);
  - one sentence appended to the reviewer's system prompt: "The tool's answer may be wrong; check
    it independently."
- **Scope:** both reviewer models, variants answer_only, plus_private and plus_tool_log, good and
  bad lookups.
- **The log:** rows go to `results/trackC/team_c9.jsonl` with `from_log: team_c4` and C4's case ids.
- **The summary (`--summary --log team_c9 --cases …`):** adds `vs_original_prompt`. That is each
  reviewer × variant with the sentence minus the same one with C4's prompt, paired by item on the
  same cases:
  - corrects a wrong answer on bad lookups;
  - keeps a right one on good lookups.
  It also gives the usual per-variant table and each variant minus answer_only under the new
  prompt, and with `--cases` the same per kind and kind × set.
- **Refactor:** `reviewer_vs_answer_only` now shares its pairing with the new comparison. C4's
  summary is unchanged (byte-identical).
- **Tests:** 2 new (the tool log rebuilt; C9 end to end with a fake reviewer that only checks when
  told to).

**FINDINGS.**
- **The story so far**, at the top. Five steps, each with its F-numbers and status:
  1. tools sway models more than users (confirmed);
  2. after a tool call the answer stops explaining (confirmed for both Qwen3 models; tentative for
     Olmo and for call vs declared tool);
  3. layers 15/19/23 (confirmed on 19 cuts, the mechanism tentative);
  4. the reviewer defers (confirmed for Olmo 3.1 32B; C9 waiting);
  5. the fix (Gate 3, waiting).
- **F18, both sides** (from the tracked C4 summary). The Olmo reviewer, with the private reasoning
  or the tool log:
  - bad lookups 59 → 6 and 3 of 73 corrected;
  - good lookups 67 → 84 of 84 kept (+20 [+8, +35]);
  - right in 128 → 92 and 89 of 159, against the tool's 84 of 159: as good as the tool.
- **F18, the reading:** called automation bias, citing Skitka, Mosier & Burdick 1999 (IJHCS 51(5)
  991–1006) and Parasuraman & Manzey 2010 (Human Factors 52(3) 381–410), both checked. Plus the
  deployment reading and C9 as next.
- **F15's status:** the 20-row keyword check.

**Docs.**
- PLAN, TODO, RUNBOOK, the labeling guide and both handoffs now cover the vLLM rule, S7 on four
  versions, 171 rows and C9.
- TODO had two A18 rows (my 18:23 training-baseline row reused the number): it is now **A28**.
- RUNBOOK's header still said Oct 27; it now says 21:50.

## 4. Results

None yet: C9 is starting. The keyword's count on the 20 rows: 20 of 20.

## 5. C9's dry run (pre-approved on Voyager once in a session log)

```
$ ../.venv/bin/python agents/run_team.py --rereview team_c4 --cases results/trackB/steered_cases.jsonl --log team_c9 --dry-run
159 saved tool-team cases of team_c4 (53 items; 75 bad and 84 good lookups), 159 to run: ~954 calls (2 reviewer models x 3 variants: answer_only, plus_private, plus_tool_log); no solver or checker calls. Added to the reviewer's system prompt: "The tool's answer may be wrong; check it independently."
```

- **Calls:** 954 to Voyager: Qwen3 30B Instruct and Olmo 3 32B Instruct (served as 3.1), 477 each.
  Each model gets its identity canary first. There are 4 cases in flight, each running its 6 reviews
  one after another, so at most 4 requests at a time.
- **Time:** about 4 h at C4's mean reviewer times (6 reviews, 372 s per case). Those were measured
  beside Olmo 3 7B Think's long replies, so it is likely less alone.
- **Under the power guard:**
  ```
  cd cot-disclosure
  nohup caffeinate -i ../.venv/bin/python -u progress/guard.py \
    --job "voyager:c9=agents/run_team.py --rereview team_c4 --cases results/trackB/steered_cases.jsonl --log team_c9 --run-name C9-oct28" >> logs/guard_c9.log 2>&1 &
  ```
  `logs/stop_guard` stops it, letting the cases in flight finish; exit 3 means a Voyager guard failed.
- **The comparison when done:** `run_team.py --summary --log team_c9 --cases
  results/trackB/steered_cases.jsonl --table`. That gives each reviewer × variant with the sentence
  minus C4's prompt, paired by item, with intervals, overall and by kind and kind × set. FINDINGS
  gets F19 then.

## 6. For Ritik (Sol)

```bash
# Mac, after this log's commit:
git fetch origin && git log --oneline main..origin/main          # must print nothing
git push origin main trackA-nosol trackB-main trackC-main
git ls-files | rsync -av --files-from=- ./ ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/

# Sol: the vLLM check again (setup_vllm is done, so no dependency; limit 1:30; it waits for a slot
# while both training jobs run)
cot-disclosure/finetune/gpu/sol/submit.sh vllm_check --estimate 1

# Sol: S7 — which versions did 66865939 get?
sacct -j 66865939 -X -o JobID,JobName%20,State,SubmitLine%300
# if its SubmitLine ends in "val_loss.sbatch lora tags" (or names no version): cancel and resubmit with all four
scancel 66865939
cot-disclosure/finetune/gpu/sol/submit.sh val_loss --estimate 1.25 --dependency=afterany:66862721:66862726 -- lora tags lora_tags lora_attn3
```

## 7. For review

- **Warning or refusal:** a used option with other choices on the node, ours still accepted, is a
  warning (§3). Ritik's wording ("missing or changed") could also mean a refusal.
- **The sitecustomize hook** shadows any `sitecustomize` in the vLLM environment during the help run.
- **S7's 45–80 GPU minutes** is an inference, not a measurement.
- **C9 is one sentence, on one solver's cases:**
  - The comparison is the prompt, not a fresh solver.
  - Run-to-run variation of the reviewer at temperature 0.6 is in both arms. The seeds are the same
    as C4's, but Voyager doesn't promise the same reply for the same seed.
  - So a small difference can be noise, and that is what the intervals are for.
- **The answer_only arm also gets the sentence,** although it never sees a tool. It shows whether the
  sentence alone changes the reviewer.
- **The deployment reading is worded more narrowly than Ritik's** "the only check that caught wrong
  tool answers was the one that never saw the tool". The answer-only reviewers never saw the tool
  either and corrected 59 and 62 of 73. The Qwen3 reviewer saw the tool log and still corrected 56
  of 73. FINDINGS says that the check that kept every wrong answer from shipping (the checker, 73 of
  75) never sees the tool, and that a reviewer shown the trace may or may not defer.
- **"Automation bias"** comes from studies of people. FINDINGS uses it for the pattern and says it
  claims no shared cause.
