# Open work, every track

Last updated: 2026-10-29 00:35 MST (week 11). Rebuilt from the session transcripts (Oct 4–27),
[`PLAN.md`](PLAN.md), [`FINDINGS.md`](FINDINGS.md), [`OVERVIEW.md`](OVERVIEW.md), the commit log
and every local and remote branch; updated with Ritik's decisions and the Oct 27–Nov 3 plan. How
to run each step: [`RUNBOOK.md`](RUNBOOK.md).

- **Status:** done / in progress / not started / blocked.
- **Needs:** Voyager (ASU's API), Ollama (local), Sol (GPU jobs), paid (closed-model API), or no
  calls. Paid calls and Sol jobs always wait for Ritik's "go"; GPQA waits until Ritik has
  accepted its terms on Hugging Face.
- **Times** are working time for code and docs, and GPU or Voyager time for runs.
- **Owners:** Ritik did the work so far in all three tracks and runs them until Nov 3. On Nov 3
  Track B goes to Arsha and Track C to Shrey: "Arsha, from Nov 3" in the owner column says who takes
  an open item over, never who did past work. "Ritik submits" marks a Sol job Ritik submits.
  The repo has no commits by Arsha and none by Shrey after Oct 4, so their local work can't be
  seen from here.

## Track A

| # | Item | From | Status | Blocked by | Owner | Needs | Time |
|---|---|---|---|---|---|---|---|
| A1 | Steps 6–7 to 240 kept questions (`run_steps67.py --kept 240 --checkpoint 100`) | Oct 25 "go" | done: 251 kept of 530 [43, 52%], ended 13:45 MST Oct 27 | — | Ritik (pid 12290) | Voyager | done about 2–4 PM MST Oct 27 |
| A2 | The checkpoint report at 100 kept | Oct 25 | done: written Oct 26 10:42 MST, sent Oct 27 (notes below) | — | Ritik | no calls | — |
| A3 | Final Steps 6–7 counts and the final-count log | Oct 27 | done (log 13:55) | — | Ritik | no calls | 30 min |
| A4 | Assemble train / validation (`--assemble`): 10% no-hint, "neither" dropped if under 10%, counts | Oct 25; "go" Oct 27 | done: 1,196 examples (1,040 train, 156 validation; 120 no-hint; 57 "neither" dropped) | — | Ritik | no calls | 15 min |
| A5 | Export the final Steps 6–7 summaries | Oct 26 | done (`56e2894`) | — | Ritik | no calls | 10 min |
| A6 | History rewrite (`untrack_produced.py --run`), approved Oct 27 with conditions: `git bundle` backup and a sha256 list of every file under `results/`, `finetune/data/`, `configs/` first; keep tracked `configs/canary/*.json`, `results/summaries/`, `docs/sessions/` and every numbers-only summary; rewrite only commits unique to `trackA-nosol` (a plan for `main` first if it carries produced files); after: tests pass, sha256 list identical, pre-push check passes on both branches | Oct 26, Oct 27 | done for `trackA-nosol` (13:49): bundle + sha256 list (192 files identical), 0 produced paths tracked; `main`'s 2 unpushed commits wait on the plan for `main` | decision: plan for `main` | Ritik | no calls | 30 min |
| A7 | Merge `trackA-nosol` into local `main` (shared code, docs, no produced data); tests; push commands for Ritik | Oct 27 | local `main` fast-forwarded to `trackA-nosol`; push blocked by the canary row in `280bd12` until the plan for `main` | the plan for `main`, then Ritik pushes | Ritik | no calls | 30 min |
| A8 | Step 11 `train.py`: LoRA only, tags only, both; 32,768 tokens, chunked loss, gradient checkpointing, checkpoint after each epoch and resume; validation loss per epoch; CPU tests | Oct 21, Oct 25 | done (`f52a5ef`, 9 CPU tests) | — | Ritik | no calls | 4–6 h |
| A9 | Step 12 generation: tagged decoding loop, and the vLLM path (`tags_vllm.py`, equal on a tiny model on CPU) | Oct 21, Oct 25 | done (`f2a9c4f`: vLLM client with tagged prompt embeddings, own loop, fold) | — | Ritik | no calls | 3–5 h |
| A10 | Step 13 `eval.py`: hint following, no-hint accuracy, mention, hiding check, false-disclosure check; X of Y, clustered bootstrap | Oct 21, Oct 25 | done (`f85f100`, 6 tests) | — | Ritik | no calls | 3–4 h |
| A11 | Sol job scripts for Steps 11–13 in the kit: account guard, checkpoint/resume; CPU tests | Oct 25–26 | done (`9256acc`: timing, vllm_check, train, eval jobs; eval_job.py; setup_vllm) | — | Ritik | no calls | 2 h |
| A12 | Sol kit QoS checks (Oct 27): one config file of accounts, partitions, QoS and limits (only listed accounts allowed; today the course account); each job's limit = estimate × 1.3 rounded up to 30 min; `submit.sh` refuses a job over 960 GPU-minutes, adds the remaining GPU-minutes of running and pending jobs (`squeue`), warns over 960 and says when the second slot frees; QoS fields in the GPU README | Oct 27 | done (`1608665`: accounts.conf, submit.sh checks, 5 tests) | — | Ritik | no calls | 2 h |
| A13 | First Sol jobs: setup_vllm (envs/olmo-vllm), S1 the timing run, S2 the vLLM check | Oct 25, Oct 27 | "go" given Oct 27; S1 submitted (66749357); S2 66753250 failed after 12 min (vLLM 0.31.0 has no `--disable-log-requests`): option removed. Oct 28: `vllm serve --help=all` can't run on a CPU node ("Failed to infer device type"): setup_vllm now checks the version and commands against the committed list, and each GPU job compares its node's help with the list first; 66757260 cancelled; rerun setup_vllm, then S2. Oct 28: setup_vllm 66760181 done; S2 66760726 failed after 3:04: `vllm serve --help=all` didn't finish in 180 s on sg002 (the first vLLM import on Sol); now 900 s, and past it the job prints vLLM's traceback; resubmitted Oct 28 as 66862780. vllm_check 66862780 failed after 6:23 at the preflight: sg018's vLLM lists a `cuda` choice for `--mm-processor-device`, an option no server command uses (the committed list came from the Mac's CPU). The committed list is now sg018's, and the preflight refuses only what a server command uses (an option missing, a value outside the node's choices, a flag that now takes a value or the reverse); any other difference is a warning in the job's log (Oct 28); resubmitted Oct 28 as 66878660 (pending) | Ritik submits | Ritik | Sol | 150 GPU-min |
| A14 | Gate 3 job plan: every job in order, 2 at a time, limits, dates | Oct 26–27 | done (PLAN; updated Oct 27 with the QoS and the accelerated dates) | — | Ritik | no calls | — |
| A15 | Train the versions (S3–S6) in batch 2: lora and tags at once, lora_tags after lora, lora_attn3 after tags (afterany); rank 16, LoRA 2e-4, tag table 1e-3, 2 epochs; checkpoint per epoch, chosen by validation loss only (decided Oct 27, Oct 28) | PLAN | lora done (3.41 h; epoch 2, validation loss 0.1854) and tags done (2.81 h; epoch 2, 0.2140); lora_tags and lora_attn3 failed in seconds when they started (no version reached run.sh: sacct's SubmitLine shows `train.sbatch` with nothing after it, confirmed Oct 28; `submit.sh` now refuses train and eval without their argument); resubmitted Oct 28, two at once: lora_tags 66862721 done in 3:25:40 (epoch 2, 0.18723 → 0.18598), lora_attn3 66862726 done in 2:44:43 (epoch 2, 0.19654 → 0.19278). **Done Oct 28: all four versions chose epoch 2** | A4, A13 (S1) | Ritik submits | Sol | from the refit |
| A16 | Evaluate base, prompt-only and the trained versions on Sol (batch 3) | Oct 26, Oct 28 | "go" Oct 28 once vllm_check passes: base and prompt-only first, then each version as its training is done; re-planned from the first job's measured rate (`finetune/gpu/plan_eval.py`). Queued Oct 28 night, afterok vllm_check 66878660: base 66879564/66879567, prompt_only 66879569/66879571, lora 66879572/66879573, tags 66879761/66879792 (limit 4:30 each); lora_tags and lora_attn3 (4 parts) wait for free submission slots (MaxSubmitPU 10) | A13, A15 | Ritik submits | Sol | 2–7 GPU h per system (prior rate) |
| A28 | Training needs a baseline (Ritik, Oct 28): the validation loss of base and both epochs of every version (lora, tags, lora_tags, lora_attn3; all four decided Oct 28 21:30), each split into the taught tokens (prefilled opener, hint-check sentences, final answer; 6.4% of the reply tokens) and the rest; FINDINGS and PLAN report training by the taught tokens against base | Oct 28 | code and CPU tests done (`finetune/val_loss.py`, `val_loss.sbatch`, run.sh step, submit.sh check; `--dry-run` gives the parts); 66865939 done Oct 28 in 0:37:09 (all four versions); copied back and reported (`finetune/val_loss.py --report`): FINDINGS F20 and PLAN. LoRA's taught tokens −58% against base (−40% without the opener; the rest −19%); tags −17%; lora_tags ≈ lora; lora_attn3 −52%. **Done** | A15 | Ritik | Sol | 37 GPU-min (measured) |
| A17 | Step 13 analysis: 4 measures, hiding check, false-disclosure check, measure 4 on hand-label categories, "tags help more on the inserted tool turn than the pasted block" | Oct 25, Oct 27 | not started | A16, L4 | Ritik | no calls | 1 day |
| A18 | Look-inside rerun on the best version (L1): Step 10 drops at 15/19/23; heads L19H31, L23H17, L15H31: drop, or stay while the answer stops following | Oct 26–27 | not started (code takes `--model`) | A16 | Ritik submits | Sol | 4–10 GPU h |
| A19 | Fourth version (S6, E6): LoRA on the attention of layers 15, 19, 23 only; included, scheduled last, dropped if E1–E5 aren't done by Nov 9 | Oct 26, Oct 27 | decided; not started | A16 | Ritik submits | Sol | 6–16 GPU h |
| A29 | Set A, an independent localization set (Ritik, Oct 29): Olmo 3 7B Think on the 34 validation questions (pasted and declared inserted tool turn, 3 runs each; Step 6's no-hint runs), Step 3 grid_tail probes, cases; then Steps 9 and 10 on Sol; pre-registered: does the readout at 15/19/23 replicate (session log Oct 29 00:20)? | Oct 29 | Voyager runs started Oct 29 00:20 (`finetune/setA.py`) | — | Ritik | Voyager, then Sol | ~1.5–3 h Voyager; ≤2 GPU h |
| A30 | B1, provenance-scaled attention at inference (`finetune/provenance.py`): the forced-answer job on set A's cuts (chooses alpha on set A), then generation on the 30 evaluation questions; deployable (tool-role spans) and oracle (pasted block) apart | Oct 29 | code and CPU tests done (`provenance_job.py`, `provenance_forced`/`provenance_gen` jobs) | A29 | Ritik submits | Sol | P1 0.25–0.5, P2 11–23 GPU h |
| A31 | B2, provenance-gated attention bias (versions gate3, lora_attn3_gate in train.py): a learned per-head bias on tool-tagged keys in 15/19/23, zero-initialized; LR_GATE 1e-2 is new and needs Ritik's sign-off | Oct 29 | code and CPU tests done; not trained | Ritik's LR_GATE decision | Ritik submits | Sol | ~2.75 GPU h each |
| A32 | Rank heads on set A (Step 9 rerun) for B1's head-subset variant; never on the evaluation questions | Oct 29 | after S9A | A29 | Ritik | Sol | — |
| A20 | Training settings | finetune README | done: one setting, decided Oct 27 (A15) | — | Ritik | — | — |
| A21 | Hand the best version to Tracks B and C (week 15) | Oct 21 brief | not started | A16 | Ritik | Sol | — |
| A22 | Figure #1: the pinned panel (Step 2b per channel) | Oct 26 | done Oct 27 (`finetune/look/plot_figures.py`; counts tested against F1, F7) | — | Ritik | no calls | 30 min |
| A23 | Figure #4: deletion vs control vs unedited | Oct 26 | done Oct 27 (`finetune/look/plot_figures.py`; counts tested against F1, F7) | — | Ritik | no calls | 45 min |
| A24 | Sol scripts call `/scratch/ragarw68/envs/olmo/bin/python` by full path | Oct 27 | done (`39f8534`, with a test) | — | Ritik | no calls | — |
| A25 | Record Step 9's matched onsets | Oct 27 | done (`07999f7`: F14, T9) | — | Ritik | no calls | — |
| A26 | Copy Sol's original `step9_followup.json` to `results/trackA/gpu/original/step9_followup_sol.json` (gitignored) | Oct 27 | done (sha256 `6282a790…`, same as the scratchpad copy) | — | Ritik | no calls | — |
| A27 | Olmo 3 32B identity (3 vs 3.1) on Voyager | Oct 4 | done Oct 28: the instruct route (`olmo3-32b`, effort none) is Olmo 3.1 32B Instruct: the only public Olmo 3 32B Instruct, and Voyager's prompt-token counts match its template in 4 of 5 conditions (−1 with the tool spec) | — | Ritik | Voyager (6 calls) | — |

## Track B (Ritik until Nov 3, then Arsha)

| # | Item | From | Status | Blocked by | Owner | Needs | Time |
|---|---|---|---|---|---|---|---|
| B5 | Olmo 3 7B Think in Track B through the pinned Think format on `/v1/completions` (`olmo_format.py`), with the declared `tool_injected` channel in place of `tool_real` | Oct 21, Oct 27 | done (`fb9b5c1`) | — | Ritik | no calls | 1–2 h |
| B12 | A model flag for `run_trackB.py` | Oct 27 | done (`fb9b5c1`, `d2210cf`: --model, --thinking) | — | Ritik | no calls | 30 min |
| B8 | `steered_cases.jsonl`: define the format (no code writes it today), then export from B7 | PLAN, Oct 27 | format and export done (`--steered`); export after each model's runs; done for all three: Qwen3 Thinking Oct 28 03:13 (24 steered, 29 matched, 1 other); after C4, Instruct (48 steered: all 24 puzzles and 24 MMLU-Pro; 6 matched) and Olmo 3 7B Think (21 steered, 31 matched, 2 other), 18:00. The file now has three models: `run_team --case-model` picks one, each with its own `--log` | B7 | Ritik; Arsha, from Nov 3 | no calls | 1 h |
| B10 | Served chat template per Voyager model (prompt-token count against a local rendering, as for Olmo on Oct 21), recorded | Oct 27 | done: gap 0 except Qwen3's tool spec (sorted keys); Olmo 3 7B Instruct differs only without a system message | — | Ritik | Voyager (a few calls) | 30 min |
| B11 | Identity-canary references for every Voyager model Tracks B and C use, before their first batch | Oct 27 | done: Qwen3 Thinking, Qwen3 Instruct, Olmo 3 7B Instruct (Olmo 3 7B Think existed) | — | Ritik | Voyager (a few calls) | 30 min |
| B13 | Per model: smoke test (`--limit 5`) and the dry run (calls, hours) in a session log; then the run starts | Oct 27 | done: smoke 15 of 15; dry runs in the 13:05 log | — | Ritik | Voyager | 15 min each |
| B7 | Voyager runs, 3 per question, the 24 puzzles and the 30 MMLU-Pro items, all conditions: Qwen3 30B Thinking, then Qwen3 30B Instruct, then Olmo 3 7B Think | PLAN, Oct 27 | done Oct 28: Qwen3 30B Thinking 03:11, Instruct 05:32, Olmo 3 7B Think 17:52 (810 runs each; Olmo 10 no answer, 0 errors) | — | Ritik | Voyager | ~15 h (notes) |
| B4 | Qwen3-8B, thinking on and off, real tool calls: on Sol (our vLLM server, `enable_thinking`), core cells first; replaces the Ollama grid (decided Oct 28: Ollama never on the Mac; 2 Ollama runs at the right context exist) | PLAN, Oct 27, Oct 28 | code and CPU tests done (`progress/sol_trackB.py`, `providers/sol_vllm.py`); "go" Oct 28; get_qwen8b 66879245 done (1:31); trackb_qwen8b 66879362 queued after it (Oct 28 night) | setup_vllm, the snapshot | Ritik submits; Arsha, from Nov 3 | Sol | 0.5–1.5 GPU h |
| B14 | Track B table: model × channel × thinking (on/off where it exists); hint following against the per-letter no-hint baseline; sure and unsure questions; mention in the private reasoning and the final answer (keywords); tool-call rate | Oct 27 | done for the Voyager models: `trackB_report.py` (+ `--by-set`, thinking minus not, and since Oct 28 the bare final answer per channel); Qwen3 Thinking in FINDINGS F15, Instruct and thinking − Instruct in F16, Olmo 3 7B Think in F17; Qwen3-8B when B4 runs | B7, B4 | Ritik | no calls | 3 h |
| B9 | The Gate 2 question: is the tool-vs-user gap still clear with 3 runs per question and more models? Answered as soon as the data allows | PLAN, Oct 27 | Qwen3 Thinking: clear (pasted +35 [+24, +46], real call +31 [+22, +42]; F15); Qwen3 Instruct: clear (pasted +21 [+12, +31], real call +90 [+83, +96]; F16); Olmo 3 7B Think: clear (pasted +32 [+22, +42], injected +21 [+13, +30]; F17). Clear for all three Voyager models, at both cuts | B14 | Ritik; Arsha, from Nov 3 | no calls | — |
| B1 | Closed-provider keys: a real OpenAI key (the current one is the Voyager key), Anthropic, xAI | Oct 5 | blocked | keys | Ritik; Arsha, from Nov 3 | — | — |
| B2 | Is Claude Haiku 4.5 still served? Swap in its replacement if not (Haiku 5.5 needs an adapter change) | PLAN | not started | B1 | Ritik; Arsha, from Nov 3 | no calls | 15 min |
| B3 | Closed-model smoke tests (`run_trackB.py --run --only-provider X --limit 1`) | Gate 1 | blocked | B1, "go" (paid) | Ritik; Arsha, from Nov 3 | paid (under $0.20) | 15 min |
| B6 | GPQA Diamond: export to `data/gpqa_diamond.jsonl` (gitignored); nothing from it in any doc or tracked file | PLAN | blocked | Ritik accepts its terms on Hugging Face and says so | Ritik; Arsha, from Nov 3 | none | 1 h |

## Track C (Ritik until Nov 3, then Shrey)

| # | Item | From | Status | Blocked by | Owner | Needs | Time |
|---|---|---|---|---|---|---|---|
| C6 | `run_team.py`: append-only, writing to gitignored `results/trackC/` (today it deletes its own log and writes to tracked `results/scope/`) | Oct 22, Oct 26, Oct 27 | done (`b72b747`) | — | Ritik | no calls | 30 min |
| C2 | No-tool team (the solver always gets the tool today) | PLAN | done (`b72b747`) | — | Ritik | no calls | 1–2 h |
| C3 | Second reviewer model (hard-coded today) | PLAN, Oct 27 | done: Olmo 3 32B Instruct since Oct 28 (decision 5; canary and template check Oct 28; smoke 5 of 5 cases, 20 of 20 letters); was olmo3-7b-instruct (`b72b747`) | — | Ritik | Voyager | — |
| C7 | Input-file option for `run_team.py` (`live` takes pilot puzzles only) | Oct 27 | done (`b72b747`) | — | Ritik | no calls | 1 h |
| C1 | Live team on 5 items (`run_team.py --live --n 5`) | Gate 1 | done Oct 27 15:00 (5 items; log 15:05) | — | Ritik | Voyager (35 calls) | 15 min |
| C4 | The team on Track B's steered cases (Qwen3 Thinking's first), 3 repeats, tool and no-tool teams, both reviewers (`--log team_c4`) | PLAN, Oct 27, Oct 28 | done Oct 28 17:51 (03:13–17:51 under a second power guard; 53 items: 24 steered + 29 matched; 318 of 318 cases, 0 errors). Reported by kind and by kind × set, saying plainly that steered vs matched is also MMLU-Pro vs puzzles; no extra cases (Ritik, Oct 28). FINDINGS F18 | B8, C2, C3, C7 | Ritik | Voyager (~3,400 calls) | ~3–13 h |
| C9 | Does an instruction restore the reviewer's check? (Ritik, Oct 28) Only the reviewers again, on C4's saved tool-team cases (no solver or checker calls), with "The tool's answer may be wrong; check it independently." after the reviewer's system prompt; both reviewer models; answer_only, plus_private, plus_tool_log; good and bad lookups; compared with C4's prompt paired by item, with intervals and by kind × set (`run_team.py --rereview team_c4 --log team_c9`) | Oct 28 | done Oct 28 22:33 (21:46–22:33 under the power guard; 954 calls, 0 errors). FINDINGS F19: no restoration for the Olmo reviewer (+3 [−4, +9], +1 [−3, +6]); Qwen3 +4 [+0, +11], +7 [−4, +19]; numbers-only copy in `results/summaries/trackC/team_c9_summary.json` | C4 | Ritik | Voyager (954 calls) | 2–4 h |
| C10 | Commit first (Ritik, Oct 28): only the reviewers' second step again on C4's saved cases: C9's answer_only review first (its reply as the assistant turn), then the private reasoning or the tool log and a final answer; both reviewer models; good and bad lookups; compared with C4 and C9 and with the own first answer, paired by item, by kind × set (`run_team.py --rereview team_c4 --first-from team_c9 --log team_c10`) | Oct 28 | done Oct 28 23:16 (23:06–23:16; 636 calls, 0 errors). FINDINGS F21: no protection; Olmo +18 [+10, +26] with the private reasoning against C4 but −56 from its own answer; Qwen3 with the tool log −32 [−44, −20] against C4; `results/summaries/trackC/team_c10_summary.json` | C9 | Ritik | Voyager (636 calls) | 30–60 min |
| C11 | Is the deference general? Two more reviewer models on C4's saved cases with C4's prompt (Olmo 3 7B Instruct, Qwen3 30B Thinking); pre-registered rule in the Oct 29 00:20 log | Oct 29 | queued under the night's guard (after set A) | C4 | Ritik | Voyager (954 calls) | ~1–2 h |
| C12 | What is the cue? Both C4 reviewers with every statement of the tool's letter redacted (private reasoning; tool log); against C4's unredacted variants and answer_only | Oct 29 | queued under the night's guard (after C11) | C4 | Ritik | Voyager (636 calls) | ~40 min |
| C5 | Track C table per reviewer variant: shipped, caught, false alarms, undetermined; bad and good lookups apart; the checker's disagreement against the no-tool team's run-to-run variation; tokens | PLAN, Oct 27 | done Oct 28 (FINDINGS F18): `run_team --summary --cases --table`, now also each reviewer variant minus answer only paired by item, and the solver's final answer after good vs bad lookups (F15's control); numbers-only copy in `results/summaries/trackC/team_c4_summary.json` | C4 | Ritik | no calls | 3 h |

## Labels

| # | Item | From | Status | Blocked by | Owner | Needs | Time |
|---|---|---|---|---|---|---|---|
| L1 | Replace the 10 label-queue rows with no text: no calls, the original rule (random hinted pilot runs with saved text, seed recorded), marked as replacements in the queue and in the guide | PLAN; decided Oct 27 | done (`d41f77e`): 7 pilot replay + 3 Test 2 runs (only 7 pilot runs qualify) | — | Ritik | no calls | 30 min |
| L2 | Labeling kit: two blank rater sheets from `LABEL_QUEUE.csv` (keyword columns hidden), the guide, a kappa-per-channel script that lists disagreements (no labels filled in by the kit) | Oct 27 | done (`d41f77e`): kit in gitignored results/labels/ | — | Ritik | no calls | 1–2 h |
| L3 | Label the queue, two raters; Cohen's kappa per channel; under 0.6, tighten the guide and label a fresh batch | PLAN (Gate 2, Nov 8) | ready to start (kit built). **Goes first** (Ritik, Oct 28: F3 rests on it), before L5 | raters | two raters | none | 3–4 h per rater |
| L5 | Track B labeling batch (`tools/label_kit.py trackb`), labeled in order: group 1, Qwen3 Thinking's runs that followed after a real call or with the pasted block (113: F15's contrast); group 2, the same for Instruct (182) | Oct 28 | built, after L3 (Ritik, Oct 28). 295 runs; bare replies (30 characters or fewer, 162: 51 + 111) are `no_mention` by rule (`prelabeled.csv`), with a seeded 10% per group (6 + 12) left in the sheets as a blind spot check; raters label the 133 replies with text (62 + 71) and the 18 spot checks (68 + 83 rows), then group 3 (decided Oct 28 21:30): the private reasoning only of a seeded 20 of Thinking's other 45 bare real-call replies, a check on F15's keyword count (it says 20 of 20 name the tool); `kappa` gives each rater's agreement with the keyword there. **171 rows** (68 + 83 + 20), in gitignored `results/labels/trackB/` | L3 | two raters (a second from Shrey or Arsha) | none | group 1: ~2 h per rater |
| L4 | Phase 6 labeling sample: 200 evaluation replies (240 with the fourth version) + every false-disclosure candidate | Oct 25, Oct 27 | planned | A16 | two raters | none | 6–8 h per rater |

## Handoff, repo, docs, gates

| # | Item | From | Status | Blocked by | Owner | Needs | Time |
|---|---|---|---|---|---|---|---|
| H1 | Start `trackB-main` and `trackC-main` from `main` | Oct 27, Oct 28 | done Oct 28 (local, from `main` now; Ritik pushes them); kept at `main` until Nov 3 | A7, the push | Ritik | no calls | 10 min |
| H2 | `docs/handoff/TRACK_B.md`, for Arsha: what's done, results (FINDINGS links), how to run each step (RUNBOOK), open items, inherited decisions, traps; current all week, final by Nov 3 | Oct 27 | draft, kept current | — | Ritik | no calls | 2 h |
| H3 | `docs/handoff/TRACK_C.md`, for Shrey: the same | Oct 27 | draft, kept current | — | Ritik | no calls | 2 h |
| H4 | `tools/make_handoff_bundle.py`: a tar.gz per track of its gitignored results, with a sha256 manifest; GPQA files never inside unless Ritik says so | Oct 27 | done (`87f3357`; `--verify` checks a bundle) | — | Ritik | no calls | 1 h |
| H5 | Teammates' work on GitHub: check before every merge; never overwrite; report it in a log; merge only on Ritik's say | Oct 27 | standing | — | Ritik | no calls | — |
| D1 | Docs kept in line with the code and results; each says when it was last updated | Oct 27 | standing | — | Ritik | no calls | — |
| D2 | Session logs after every run and every stop: `docs/sessions/YYYY-MM-DD_HHMM_<A\|B\|C\|ALL>_<name>.md`, `LATEST.md`, `INDEX.md` | Oct 27 | standing | — | Ritik | no calls | 15 min each |
| D3 | A daily log at the end of each day, `docs/sessions/DAILY_YYYY-MM-DD.md` | Oct 27 | standing | — | Ritik | no calls | 15 min |
| G1 | Gate 1 (Oct 25): missed (recorded Oct 27); the fallback applies: Voyager and Ollama for B, Voyager for C (PLAN, gates) | PLAN | missed | — | everyone | — | — |
| G2 | Gate 2 (Nov 8): the tool-vs-user gap (B9) and the hand labels with kappa (L3) | PLAN | not started | B9, L3 | everyone | — | — |
| G3 | Gate 3 (Nov 22): a trained version follows fewer wrong hints, accuracy within 5 points, hiding check not up | PLAN | not started | A17 | Ritik | — | — |
| R1 | GitHub `main` still has the old Voyager IDs: runs from GitHub fail the Oct 21 routing | Oct 21 | open | A7, the push | Ritik | no calls | — |
| R2 | The pre-push hook is installed only on this Mac; each teammate installs it (RUNBOOK, repo hygiene) | Oct 26 | open | — | each teammate | no calls | 2 min |

## Notes

**A2, the checkpoint report at 100 kept** (written Oct 26 10:42 MST, after 250 questions; not sent
at the time because the session ran out):
- **Keep rate:** 117 of 250 [41, 53%], pilot 5 of 10. Kept by set: MMLU-Pro 68 of 149, hard puzzles
  46 of 96, easy puzzles 3 of 5.
- **Step 7, a prefill target within 4 samples:**

  | channel | wrong hint | correct hint |
  |---|---|---|
  | user | 112 of 117 [90, 98%] | 60 of 61 [91, 100%] |
  | tool, pasted | 110 of 117 [88, 97%] | 59 of 59 [94, 100%] |
  | tool, inserted (declared) | 102 of 117 [80, 92%] | 62 of 62 [94, 100%] |

  Failed samples: wrong letter 192, hit the token cap 18, reasoning refers to instructions 14,
  called the tool again 6. No rate was off by more than half from the pilot, so the run went on.
- **Target length** (prompt + target, tokens; median / 90th percentile / max): easy puzzles 5,401 /
  7,356 / 9,611 (18 examples); hard puzzles 11,342 / 16,869 / 26,748 (204); MMLU-Pro 4,678 / 10,409 /
  18,523 (311); all 7,352 / 14,094 / 26,748 (533). Held-out Step 2b replies: 11,988 / 24,856 / 34,706.
- **Stance after the final-answer opener** (keyword count): wrong hint: disagrees 331, agrees after
  checking 13, neither 7; correct hint: agrees after checking 148, disagrees 14, neither 20.
  "Neither" 27 of 533 (5%).

**A1 final** (13:45 MST Oct 27): 251 kept of 530 [43, 52%]; Step 7 targets: user wrong 243 of 251,
pasted wrong 238 of 250, inserted wrong 229 of 250 (correct hints 122 of 123, 128 of 128, 131 of
131); 1,133 targets, 42 of them the fallback; "neither" 57 (5%), dropped. Assembled: 1,196 examples
(1,040 train from 217 questions, 156 validation from 34). Session log 2026-10-27 13:55.

**Order for Tracks B and C (decided Oct 27).** Track A needs no Voyager after Steps 6–7. At most 4
requests in flight across every process on the Mac.

| # | Step | Calls | Time |
|---|---|---|---|
| 0 | Code, no calls: B5, B12, the B8 format | 0 | half a day |
| 1 | Per Voyager model: served-template check (B10), canary reference (B11), smoke `--limit 5` and dry run in a log (B13) | ~10 per model | 15 min per model |
| 2 | Track B, Qwen3 30B Thinking first (Track C's solver): 54 questions × 5 conditions × 3 runs + tool rounds | ~972 | ~5.4 h (972 × 80 s / 4) |
| 3 | Track B, Qwen3 30B Instruct | ~972 | ~1.4 h |
| 4 | Track B, Olmo 3 7B Think with `tool_injected` | ~810 | ~7.9 h (810 × 140 s / 4) |
| 5 | Qwen3-8B on Sol (replaces Ollama, Oct 28): one GPU job, core cells first | 1,620 runs | 0.5–1.5 GPU h |
| 6 | Track C code (C6, C2, C3, C7), then C1 when Voyager has room | 35 | 15 min |
| 7 | Export `steered_cases.jsonl` (B8); Track C on N steered + N matched no-hint cases, 3 repeats, tool and no-tool teams (C4), Qwen3 Thinking's first | ~114 × N (N = 30: ~3,400) | ~3.3 h at 4 in flight |
| 8 | Analysis as data lands: B14, B9 (the Gate 2 question), C5 | 0 | — |

Without GPQA: about 6,200 Voyager calls, 18–28 hours. Closed models only on keys and "go". Times
for Qwen3-8B on Sol are an estimate (~5,000 output tokens a thinking run, ~800 without, 48 in flight);
Voyager times come from the progress round's per-call means.
