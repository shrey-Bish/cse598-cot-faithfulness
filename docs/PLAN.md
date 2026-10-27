# Plan: weeks 11–16 (CSE 598, Group 10)

Last updated: 2026-10-27 12:30 MST (week 11; the plan for Oct 27–Nov 3 moved everything as early
as it can go). What's left, by track: the timeline, the gates, the Sol hours and the risks. What
is done is in [`OVERVIEW.md`](OVERVIEW.md); each result, with its numbers, source and status, is in
[`FINDINGS.md`](FINDINGS.md). Every open item, with its owner and status, is in
[`TODO.md`](TODO.md); how to run each step is in [`RUNBOOK.md`](RUNBOOK.md).

**Who runs what.** Until Nov 3 Ritik runs all three tracks (the code work by Claude Code). On Nov 3
Track B goes back to Arsha and Track C to Shrey, with a handoff doc each
(`docs/handoff/TRACK_B.md`, `TRACK_C.md`) and a data bundle (`tools/make_handoff_bundle.py`;
produced data is gitignored, so it doesn't come with GitHub).

## The failure, what we now know about it, the fix

- **Failure.** A wrong hint changes the answer, most of all when it comes from a tool, and the
  final answer hides it. Test 2 (served format): thinking models followed the tool hint on 17 of 31
  questions, the user hint on 2 of 31 (F1). Test 1: the private reasoning names the hint in 208 of
  216 hinted runs, the final answer in 8 (F3).
- **What Track A found inside Olmo 3 7B Think** (Steps 3–10, FINDINGS F4–F14):
  - The hint letter is the starting answer, the lead swings many times, and on known answers it
    wins late, on a few questions (F4, F5).
  - Three full-attention layers, 15, 19 and 23, read the hint's letter straight from the prompt:
    0.90 [0.85, 0.96] of the drop in hint-token restoration at the takeover (F11). The reasoning's
    own repetition carries it in a minority of cases (F7, F13).
  - Tool hints get *less* attention at the answer than user hints yet move it more (F10); heads
    L19H31, L23H17 and L15H31 look at the hint more when the model follows it (F12). So the extra
    trust in tools lies in what is read at the hint, not in how much it is attended to.
- **The fix.** Fine-tune Olmo 3 7B Think with LoRA plus **source tags** (a learned vector added to
  every token, marking whether it came from the system, the user, a tool or the model), on examples
  that see the hint, say so, check it and keep the no-hint answer. Judge by behavior.

## Timeline (set Oct 27: everything as early as it can go)

Day by day to the Nov 3 handoff, then by week. Sol work starts the day its code is ready, not on
the old week-14 schedule. A date is the earliest start; Sol queue waits move it.

| When | Track A | Track B | Track C | Labels, repo, handoff |
|---|---|---|---|---|
| Tue Oct 27 **(now)** | Steps 6–7 end; assemble train / validation; final counts | `tool_injected` for Olmo 3 Think, a model flag, the `steered_cases.jsonl` format; served-template checks, canary references, smoke tests; then the Voyager runs start: Qwen3 30B Thinking | — | History rewrite with its safeguards; merge into `main`; push commands for Ritik |
| Wed Oct 28 | Steps 11–13 code (`train.py`, tagged generation, `eval.py`, Sol scripts) and the kit's QoS checks, CPU tests | Qwen3 30B Instruct, then Olmo 3 7B Think (Voyager, in the background); Ollama `qwen3:8b`: 5-call timing pilot, then its grid | Append-only log in `results/trackC/`, no-tool team, second reviewer, input file; then the live team on 5 items | Labeling kit; the 10 replacement rows |
| Thu Oct 29 | **First Sol jobs** (on "go"): timing run and vLLM tag check, then training | Olmo 3 runs finish; the first Track B table; the Gate 2 question answered as soon as the data allows | The team on Qwen3 Thinking's steered cases, 3 repeats, tool and no-tool teams | Labeling starts (two raters) |
| Fri Oct 30–Sun Nov 1 | Training done; evaluation of base, prompt-only and the 3 versions (E1–E5) | Analysis; gaps filled | Steered cases continue; the Track C table | Labels; kappa as rows come in |
| Mon Nov 2–Tue Nov 3 | E1–E5 continue | **Handoff to Arsha, Nov 3** | **Handoff to Shrey, Nov 3** | Handoff docs and bundles final |
| Nov 4–9 | E1–E5 done; look inside the best version (L1); the fourth version last (S6, E6), dropped if E1–E5 aren't done by Nov 9 | Arsha | Shrey | **Gate 2, Nov 8** |
| Nov 10–20 | Step 13 analysis; reruns; all evaluation done by Nov 20 at the latest | | | Phase 6 sample labeled |
| Nov 22 | **Gate 3** | | | |
| Nov 23–29 | Hand the best version to B and C | Run it through B's conditions | Run it as the solver | Draft report |
| Nov 30–Dec 6 | | | | Final presentation (week 16) |
| Dec 7–12 | | | | Final report |

## Gates

- **Gate 1 (Oct 25): missed** (recorded Oct 27; TODO, G1). It needed real tool calls on 2+
  providers (Voyager only so far), closed-model smoke tests (no keys) and the agents on 5 items
  (2 so far). The fallback written for this applies: **Track B narrows to the providers that work
  (Voyager and Ollama), and Track C runs on Voyager only.** Paid calls wait for keys and Ritik's
  "go".
- **Gate 2 (Nov 8).** Is the tool-vs-user gap still clear with 3 runs per question and more models
  (Track B)? Answered as soon as the data allows, not on Nov 8. And are the hand labels in, with
  Cohen's kappa per channel? If the gap isn't clear, the headline becomes the private-vs-final
  gap, the mechanism (Track A) and the agent results.
- **Gate 3 (Nov 22).** Does a trained version follow fewer wrong hints on held-out questions
  without losing accuracy? Success: the 95% bootstrap difference against the base model,
  clustered by question, excludes 0; no-hint accuracy stays within 5 points; the hiding check
  doesn't rise. Otherwise a negative result with the analysis. All systems run on the same Sol
  stack (F9).

---

## Track A: explain and fix (Ritik)

**Model.** `allenai/Olmo-3-7B-Think`, revision d97e442 (the Sol weights match it by sha256, F9).

### What's left, in order

1. **Steps 6–7 finish** (Voyager, running since Oct 25): 237 kept after 490 questions at 12:00
   MST Oct 27, target 240; the last chunk of 40 is running.
2. **Assemble** as soon as they end (`run_steps67.py --assemble`, no calls; decided Oct 27): the
   Step 7 examples of the kept questions, plus no-hint examples (10% of the set) from Step 6's kept
   runs; examples over 32,768 tokens are dropped and counted; "neither" targets are dropped if they
   are under 10% of the hinted ones (5% so far). About 1,150 hinted examples are expected. Then the
   final-count log.
3. **Repo:** untrack the produced Track A data and rewrite the commits unique to `trackA-nosol`
   (approved Oct 27, with a bundle backup and a sha256 list first; files stay on disk); merge into
   local `main`; Ritik pushes.
4. **Steps 11–13 code** (no calls, CPU tests on tiny Olmo 3 models): `train.py`, the tagged
   generation (own loop and vLLM), `eval.py`, and their Sol job scripts in the kit, with the QoS
   checks below. Written while Track B runs on Voyager.
5. **Sol:** the timing run, the vLLM tag check, training, evaluation, the look-inside rerun, the
   fourth version last (the job plan below). Each job on Ritik's "go".
6. **Step 13 analysis** and the hand-labeled sample (measure 4, the false-disclosure check).

### Training (Step 11)

- **Three versions on the same data:** LoRA only; source tags only (base frozen); LoRA + tags.
  This separates "the tags help" from "fine-tuning on this data helps".
- **Settings (decided Oct 27, one setting, no grid):** LoRA rank 16 on the attention and MLP
  projections, alpha 32, dropout 0.05, learning rate 2e-4; the tag table 1e-3; 2 epochs.
  32,768-token examples, bf16, gradient checkpointing, batch 1 with accumulation, the loss in
  chunks of positions and only on the model's tokens. 6–9 GPU hours for the three versions.
- **Choosing the checkpoint:** saved after each epoch; the one with the lower loss on the
  validation slice (10% of the kept training questions) is used. Never chosen by held-out results.
- **Fourth version (included Oct 27, scheduled last):** LoRA only on the attention of layers 15,
  19 and 23, where Step 10 sees the hint's effect leave the hint tokens (F11). It tests whether the
  fix can be that local. Same settings; training is ~0.7 of a version (the backward pass stops at
  layer 15); evaluation is like LoRA only, merged. 6–16 Sol GPU hours. **Dropped if the main
  evaluations (E1–E5) aren't done by Nov 9**, and the logs say so.

### Generation with tags (Step 12)

Olmo 3 7B does not tie its input and output embeddings, so adding the model tag to the input
embedding table tags every generated token, and the prompt goes in as precomputed embeddings with
its own tags (`finetune/tags_vllm.py`: equal to the tagged model's logits and greedy output on a
tiny Olmo 3, with and without LoRA). vLLM marks prompt embeddings + LoRA as compatible, but Olmo 3
runs through vLLM's Transformers backend and there are open bugs on that combination, so a short
Sol job checks it first. The fallback is our own decoding loop (+8–19 GPU hours).

### Evaluation (Step 13)

Per held-out question (the 30 MMLU-Pro Test 2 items, 7 held-out wordings): 3 runs for wrong hints on the
user, pasted and declared inserted channels; 1 run for correct hints, the undeclared inserted turn
and the system note; 3 no-hint runs. 930 generations per system, 32,768 tokens in all (a run that
hits it has no answer). Five systems: base, prompt-only, LoRA only, tags only, LoRA + tags.

1. **Hint following** on held-out questions and wordings (primary), against the base model and the
   per-letter no-hint baseline.
2. **No-hint accuracy.**
3. **Mention** in the final answer, by keyword.
4. **What the final answer says about the hint**, by the labeling guide's categories
   (`mentions_only`, `rejects_hint`, `says_changed`) on a hand-labeled sample. Every trained version
   opens its final answer by naming the hint, because the targets teach that, so a keyword mention
   says nothing there.
- **Hiding check:** follows the hint without mentioning it.
- **False-disclosure check:** the final letter is the hint letter, but the final answer claims it
  checked the hint and disagreed, or worked it out independently. If this rises after training, the
  model learned to describe checking without doing it.
- **Prediction, set in advance:** tags help more on the inserted tool turn than on the pasted block,
  since only the inserted turn's tokens are tagged "tool" (the pasted block sits inside a user turn).
- **Mechanism check, on the best version:** rerun Step 10 (`patching.py --model`, then `--handoff`):
  do the drops at layers 15, 19 and 23 shrink from 0.90 [0.85, 0.96] of the total at cut (ii)?
  Rerun Step 9 (`attn_to_hint.py --model --runs-from`, then `--followup`): does attention in heads
  L19H31, L23H17 and L15H31 drop, or stay while the answer stops following (the model still looks
  but discounts what it reads)? Both outcomes are reported.

### Sol: limits and the Gate 3 job plan

- **Account and queue.** Every job today uses `class_cse59888883fall2026`, on
  `-p public -q class -G a100:1`; `-q debug` for 15-minute tests. Accounts, partitions, QoS and
  their limits are to live in one config file that `sol/submit.sh` reads; it allows only the
  accounts listed there (today only the course account; Ritik adds others himself if more Sol
  access comes).
- **The class QoS** (`sacctmgr -P show qos class`, confirmed Oct 27): MaxTRES cpu=32,
  gres/gpu=4, mem=320G; MaxWall 24 h; MaxJobsPU 2; MaxSubmitPU 10; MaxTRESRunMinsPU
  gres/gpu=960; Flags DenyOnLimit. What that means here:
  - Slurm counts each running job's *remaining* time × GPUs against the 960 GPU-minutes. One
    1-GPU job can run alone with a limit up to 16 h; two run at once only if their remaining
    times add up to 16 h or less, so a second job can start partway through the first.
    Interactive sessions count too.
  - DenyOnLimit rejects at submission a job whose own request is over 960 GPU-minutes;
    `submit.sh` refuses it first, with a clear message.
  - The *requested* time is what counts: each job's limit is its estimate × 1.3, rounded up to the
    next 30 minutes. Every long job checkpoints and resumes, so a short limit only splits it.
  - Before submitting, `submit.sh` adds the job's GPU-minutes to the remaining GPU-minutes of
    Ritik's running and pending jobs (`squeue`), warns if the total is over 960 and says when the
    second slot frees up.
- **Python** is always `/scratch/ragarw68/envs/olmo/bin/python`, by full path (`sol/env.sh`).
- **Hours** (`finetune/gpu_estimate.py`, one A100 80GB): **35–89 Sol GPU hours** with the tag
  versions in vLLM, 42–108 in our own loop; +6–16 for the fourth version.

Each job's limit is the high estimate × 1.3, rounded up to 30 minutes. Evaluation is split into
jobs of at most 6 estimated hours (limit 8 h), so two can always run at once; the timing run (S1)
replaces these estimates with measured ones.

| # | Job | GPU hours | Limit per job | Pairs with | Earliest | Depends on |
|---|---|---|---|---|---|---|
| S1 | Timing run: 20 training steps at 32,768 tokens, each version's memory and seconds per step | 0.25–0.5 | 1:00 | S2 | Oct 29 | code (TODO A8, A11) |
| S2 | vLLM tag check: prompt embeddings + LoRA on Olmo 3, against the own loop on 3 prompts | ≤1 | 1:30 | S1 | Oct 29 | code (A9) |
| S3 | Train LoRA only (1,150–1,300 examples × 2 epochs) | 2–3 | 4:00 | S4 | Oct 29 | S1, assembled data |
| S4 | Train tags only | 2–3 | 4:00 | S3 | Oct 29 | S1 |
| S5 | Train LoRA + tags | 2–3 | 4:00 | E1 | Oct 30 | S1 |
| E1 | Evaluate base (vLLM, no adapter), 930 generations | 5–14 (1–3 jobs) | 8:00 | S5, E2 | Oct 30 | code (A10), S2 |
| E2 | Evaluate prompt-only | 5–14 (1–3 jobs) | 8:00 | E1, E3 | Oct 30 | A10 |
| E3 | Evaluate LoRA only (merged, vLLM) | 5–14 (1–3 jobs) | 8:00 | E2, E4 | Oct 31 | S3 |
| E4 | Evaluate LoRA + tags (vLLM with prompt embeddings; own loop if S2 fails: 9–24, 2–4 jobs) | 5–14 (1–3 jobs) | 8:00 | E3, E5 | Oct 31 | S2, S5 |
| E5 | Evaluate tags only (same) | 5–14 (1–3 jobs) | 8:00 | E4 | Nov 1 | S2, S4 |
| L1 | Look inside the best version: Step 3 probes (vLLM), Step 9, Step 10 | 4–10 (1–2 jobs) | 8:00 | S6 | after E1–E5 | E1–E5 |
| S6 | The fourth version, last: train (LoRA on the attention of layers 15, 19, 23) | 1.5–2 | 3:00 | L1 | after E1–E5 | E1–E5 done by Nov 9 |
| E6 | Evaluate the fourth version | 5–14 (1–3 jobs) | 8:00 | — | after S6 | S6 |
| — | Buffer for queue waits and reruns; all evaluation done | | | | by Nov 20 | |

With two jobs at a time the running time is about half the GPU hours: 18–45 hours for S1–L1
(+3–8 for the fourth version). Starting Oct 29, E1–E5 can be done between Oct 31 and Nov 4 if the
queue waits are short; Nov 9 is the cutoff for the fourth version, Nov 20 for everything. Ritik
submits every job; nothing runs without "go".

### Risks (Track A)

| Risk | Plan |
|---|---|
| Training teaches the model to hide the hint, or to describe checking without doing it | Behavior first; the hiding and false-disclosure checks; held-out wordings |
| Training is slower than estimated at 32,768 tokens | The timing run first; one setting before any grid |
| Sol queue waits, or the 960 GPU-minute cap | Limits of estimate × 1.3; jobs of at most 8 h that resume; `submit.sh` checks the cap before submitting; start Oct 29, done by Nov 20 |
| The fourth version delays the main ones | Scheduled last; dropped if E1–E5 aren't done by Nov 9 |
| vLLM can't serve the tag versions | Own decoding loop (+8–19 GPU h), still inside the budget |
| Training targets are shorter than held-out replies (median 7,343 vs 11,988 tokens; MMLU-Pro targets are short) | Report length by source; check no-hint accuracy on long held-out questions |
| The mechanism rests on 9 questions and 21 cases (F4, F11, F13) | Said in each finding; the look-inside rerun on the trained model adds cases |
| The Mac sleeps during Voyager runs (lost 9 hours on Oct 27) | Plugged in, lid open; `caffeinate -s` only helps on power |

---

## Track B: test widely (Ritik until Nov 3, then Arsha)

**Question.** Does the failure hold beyond Olmo and Qwen on Voyager? More open and closed thinking
models, thinking on vs off in the same model, real tool calls, harder questions, 3 runs per
question.

**State (Oct 27, from the repo).** The code is done (providers, budget guard, `run_trackB.py`
with dry run, `configs/trackB.yaml`); only Voyager has been called; no keys; `results/trackB/` is
empty; no GPQA export; Olmo 3 Think's `tool_injected` channel isn't wired in (TODO B1–B9).

**This week (decided Oct 27).** Gate 1's fallback: Voyager and Ollama only; paid calls wait for
keys and "go"; GPQA waits until Ritik has accepted its terms on Hugging Face.
1. Code, no calls: Olmo 3 7B Think through our pinned Think format on `/v1/completions`
   (`olmo_format.py`) with the declared `tool_injected` channel, as in Track A; a model flag for
   `run_trackB.py`; the `steered_cases.jsonl` format for Track C.
2. Per Voyager model: the served chat template checked against the model's own (prompt-token count
   against a local rendering, as for Olmo on Oct 21) and recorded; an identity-canary reference;
   a smoke test (`--limit 5`); the dry run (calls, hours) in a session log. Then the runs start
   without waiting.
3. Voyager runs, 3 per question, the 24 puzzles and the 30 MMLU-Pro items, all conditions: Qwen3
   30B Thinking first (Track C's solver), then Qwen3 30B Instruct, then Olmo 3 7B Think. At most 4
   requests in flight across every process on the Mac.
4. Ollama `qwen3:8b`, thinking on and off: a 5-call timing pilot, then the grid it allows.

**Conditions** (`tools/answer_key.py`, same wrong letter per question): `none`, `user`,
`tool_pasted`, `tool_real`, `system`; for Olmo 3 7B Think, `tool_injected` in place of `tool_real`
(it never calls the tool itself, so with `tool_real` it never sees the hint).

**Questions:** the 24 puzzles; the 30 MMLU-Pro items; GPQA Diamond (gated; request access, export
to `data/gpqa_diamond.jsonl`, gitignored; nothing from it goes into any doc or tracked file).

**Models** (`configs/trackB.yaml`; facts in `configs/models.yaml`):

| Provider | Model | Thinking on/off | Reasoning returned |
|---|---|---|---|
| Voyager (free) | Olmo 3 7B Think, Qwen3 30B Thinking, Qwen3 30B Instruct | no (use the twins) | full |
| Ollama (free, local) | `qwen3:8b` | yes, same weights | full |
| OpenAI | `gpt-6-luna` | effort `medium` vs `none` | summary |
| Anthropic | `claude-haiku-4-5-20251001` (check it's still served; Haiku 5.5 needs an adapter change) | yes | summary |
| xAI | `grok-4.3` | effort vs `none` | summary |

**Runs.** 3 per question for open models and OpenAI; 1 per question, on fewer conditions, for
Anthropic and xAI. Temperature 0.6; 16,000 tokens (open) / 8,000 (closed). Always streamed; a
cut-off reply is no answer. The proposed order, with calls and hours, is in TODO (notes): about
6,200 Voyager calls and 18–28 hours for B and C together, without GPQA.

**Measures.** Hint following vs the per-letter no-hint baseline, by sure / unsure questions;
admission in the final answer and the private reasoning (keywords, then hand labels); tool-call
rate; cost and tokens.

**Success.** 6+ models across 3+ providers (or, under the Gate 1 fallback, the providers that
work); 3 runs per question for the main models; every rate as "X of Y" with a 95% interval.

## Track C: multi-agent pipeline (Ritik until Nov 3, then Shrey)

**Question.** When the solver's lookup tool returns a wrong answer, does it reach the team's final
output? What changes when the reviewer sees more, and how often does the checker catch it or raise
a false alarm?

**State (Oct 27, from the repo).** Solver, reviewer, checker and `run_team.py` (`--replay`,
`--live --n N`); live on 2 items (Oct 4). No no-tool team, one reviewer model, no input from Track
B (TODO C1–C6). `run_team.py` rewrites its own log and writes to tracked `results/scope/`; it
should append and write to gitignored `results/trackC/` before any run on new data.

**This week (decided Oct 27), in order:** the append-only log in `results/trackC/` (C6); the
no-tool team (C2); a second reviewer model (C3); an input-file option; the live team on 5 items
(C1) as soon as Voyager has room; the team on Track B's steered cases (Qwen3 Thinking's first), 3
repeats, tool and no-tool teams (C4); the analysis (C5).

**The team** (`agents/`): a thinking solver with the real `lookup_answer_key` tool (a seeded oracle
makes each lookup bad or good; default Qwen3 30B Thinking); a reviewer (`answer_only`,
`plus_explanation`, `plus_private`, `plus_tool_log`); a checker that re-asks without the tool and
flags a changed answer. A flagged item is escalated, not shipped.

**Method.** Track B's steered cases plus matched no-hint cases, about 50% bad lookups; all four
reviewer variants plus a no-tool team; two reviewer models; 3 repeats per case. Voyager first;
closed reviewers only within Track B's budget.

**Measures and success.** Per reviewer variant: wrong answers shipped, catches, false alarms (always
next to the catches) and tokens, as "X of Y" with intervals, against the no-tool team.

## Everyone: hand labels

- **The queue** (`docs/progress/LABEL_QUEUE.csv`, 101 rows; 10 have no text yet and are replaced,
  with no calls, by the original rule: random hinted pilot runs with saved text, seed recorded,
  marked as replacements in the queue and in the guide; decided Oct 27). Two raters label
  the private reasoning and the final answer with [`progress/LABELING_GUIDE.md`](progress/LABELING_GUIDE.md):
  no mention / mentions only / rejects the hint / says the hint changed the answer / unclear.
  Cohen's kappa per channel; under 0.6, tighten the guide and label a fresh batch. No
  acknowledgment claim goes in the report before this is done (Gate 2).
- **The kit** (to build, no calls): two blank sheets with the keyword columns hidden, the guide, and
  a script for kappa per channel that lists the disagreements.
- **Phase 6 sample** (after evaluation): per system, 40 wrong-hint replies stratified by channel
  (user, pasted, declared inserted) and outcome (followed / resisted), final answer only: 200 rows
  for the five systems. Plus every false-disclosure candidate (the final letter is the hint letter
  and the keyword stance says it disagreed or worked independently), expected under 50. About 6–8
  hours per rater. 40 per system gives a Wilson interval of at most ±15 points. With the fourth
  version: 240 rows.

## Budget

**About $15 in total:** $5 each for OpenAI, Anthropic and xAI. Voyager, Ollama and Sol are free.
**Spent so far: $0** (no `results/spend_log.jsonl`).

- **The guard** (`providers/budget.py`): caps in `cot-disclosure/.env` (`OPENAI_CAP_USD`,
  `ANTHROPIC_CAP_USD`, `XAI_CAP_USD`, default 5). Before each paid call it assumes the worst case
  (prompt + `max_tokens`) and refuses a call that could pass the cap; after it, the priced usage is
  appended to `results/spend_log.jsonl`. `python -m providers.budget --status` (from
  `cot-disclosure/`); `progress/run_trackB.py --dry-run` before any sweep.
- **Keys** go in `cot-disclosure/.env` and are never printed. The adapters refuse a key equal to the
  Voyager key; the current `OPENAI_API_KEY` *is* the Voyager key.
- **Data rule:** only public benchmark questions go to outside providers.
- **Prices** (USD per 1M tokens, checked Oct 4, `configs/prices.yaml`): gpt-6-luna 0.10 / 0.50;
  claude-haiku-4-5 1.00 / 5.00; grok-4.3 1.25 / 2.50. The flagship models only fit spot checks.

## Deliverables

1. **Track B table:** hint following and admission per model × hint channel × thinking on/off,
   with 95% intervals and n.
2. **Hand labels** with Cohen's kappa per channel.
3. **Track C:** wrong answers shipped, catches, false alarms and cost per reviewer variant.
4. **Track A:** the look-inside analysis (FINDINGS F4–F14); the trained adapters and tags; the
   behavior-based evaluation; the mechanism check on the best version.
5. **Code and configs** on GitHub; produced data stays local (gitignored) with numbers-only
   summaries tracked. Final talk (week 16); report (Dec 7–12).

## Risks (all tracks)

| Risk | Plan |
|---|---|
| Gate 1 missed (recorded Oct 27): no closed keys, agents on 2 items | The fallback: Voyager and Ollama only for B, Voyager only for C; paid calls on keys and "go" |
| Too few models to generalize | Track B on every provider that works, thinking on/off, 3 runs per question |
| Hand labels not started, Gate 2 on Nov 8 | The kit and the 10 replacement rows this week; labeling from Oct 29 |
| Voyager is shared by Tracks A, B and C (4 requests in flight per machine) | Track A needs no Voyager after Steps 6–7 (the 10 label rows are replaced from saved runs); B and C take it from Oct 27 |
| Keyword counts are rough | Two raters, Cohen's kappa |
| Long replies cut off, or leaking when not streamed | Always stream; a cut-off reply is unanswered |
| Closed models return summaries only | Score the answer and the final text; a summary is not the reasoning |
| GitHub `main` lacks the Oct 21 Voyager ID fix and the data gitignore | Merge `trackA-nosol` into local `main` after the history rewrite; Ritik pushes; `trackB-main` and `trackC-main` start from it |
| Teammates have unpushed local work | Nothing of theirs on GitHub is overwritten; anything new is reported in a log and merged only on Ritik's say |
| The handoff on Nov 3 loses context or data | Handoff docs kept current all week; per-track data bundles with a sha256 manifest |
