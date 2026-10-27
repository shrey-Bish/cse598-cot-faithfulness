# Project overview: everything done so far

CSE 598, Fall 2026 · Group 10: Shrey Bishnoi, Arsha Jindal, Ritik Agarwal.
Last updated: 2026-10-27 12:30 MST (week 11). What's left is in [`PLAN.md`](PLAN.md) and
[`TODO.md`](TODO.md); every result with its numbers, source and status is in
[`FINDINGS.md`](FINDINGS.md); how to run each step is in [`RUNBOOK.md`](RUNBOOK.md).

Every number here comes from saved runs through a script. Progress-round numbers are read from
[`progress/RESULTS_SUMMARY.json`](progress/RESULTS_SUMMARY.json) (`progress/analyze_progress.py`);
Track A numbers from the numbers-only summaries in `cot-disclosure/results/summaries/`. Mention
counts are keyword counts until the hand labels are done. Rates are "X of Y [95% Wilson
interval]"; differences are bootstraps clustered by question, and none is reported on fewer than 5
questions.

---

## 1. The project in short

**Question.** When a wrong hint changes a model's answer, does the model admit that it used the
hint? And why does a hint from a tool move it more than the same hint from the user?

**Base paper.** Turpin et al., NeurIPS 2023, "Language Models Don't Always Say What They Think". A
user line like "I think the answer is (B), but I'm curious what you think" moved GPT-3.5 and
Claude 1.0 toward (B), and their explanations rarely mentioned it.

**What we add.**
- Open **thinking** models, which return their private reasoning and their final answer
  separately, so we can check which of the two mentions the hint.
- A hint channel that looks like a **tool result**, pasted or as a real tool turn.
- **Inside the model** (Track A): where the hinted answer takes over in the reasoning, which layers
  read the hint, and whether deleting the reasoning's mentions undoes it.
- A **fix** (Track A): fine-tuning with source tags. A **multi-agent** test (Track C) and a **wide**
  test over more models and providers (Track B).

## 2. Status at a glance (Oct 27, week 11 of 16)

| Area | Done | Not done yet |
|---|---|---|
| Progress round (Oct 1–6) | Test 1, Test 2, reviewer demo, truncation sweep; deck, figures, demo app | — |
| Track A (Ritik) | Steps 1–5 and 8–10, the window analysis, Step 9's follow-up and matched onsets; FINDINGS F1–F14 | Steps 6–7 finishing today (237 of 240 kept at 12:00); assemble; Steps 11–13 (train, generate, evaluate) on Sol from Oct 29 |
| Track B (Ritik until Nov 3, then Arsha) | Provider adapters, budget guard, runner with dry run, real tool calls checked on Voyager (Oct 4) | Keys, smoke tests, Ollama, `tool_injected` wiring, GPQA export, main runs |
| Track C (Ritik until Nov 3, then Shrey) | Solver, reviewer, checker, `run_team.py` (replay; live on 2 items, Oct 4) | 5 items, no-tool team, second reviewer, Track B's cases |
| Labels | Guide and queue (101 rows) | Labeling kit, labeling, Cohen's kappa |
| Repo | Data off GitHub (gitignore, numbers-only summaries, pre-push hook); 283 tests | History rewrite of this branch, then push |

**Gate 1 (Oct 25) was missed** (recorded Oct 27; PLAN, gates): real tool calls work on Voyager
only, there are no closed-provider keys, and the agents ran on 2 items. The fallback applies:
Voyager and Ollama for Track B, Voyager for Track C.

## 3. What was done, in order

| Date | Work | Calls |
|---|---|---|
| Oct 1–2 | Harness: client, puzzle generator, parser, keyword detector; difficulty ladder; **Test 1** (24 puzzles × 6 models) | 312 + 1,056 |
| Oct 4 | Progress run: **Test 2**, **Experiment A** (reviewer demo), truncation sweep, timing. Every prompt and reply saved from here on | 427 |
| Oct 4–6 | Scope update (adapters, budget guard, real tool calls, Track A/B/C scaffolds); demo app | 20 |
| Oct 21 | Track A Step 1 (Voyager capabilities); Step 2 (pinned Think format, `tool_injected`, source tags from rendered spans); the Voyager ID change and its checks | 8 + 7 |
| Oct 21–22 | **Step 2b:** the base model in the pinned format, 240 runs | 240 + continuations |
| Oct 22–24 | **Step 3:** takeover curves by early answering, 219 runs | 137,143 probes |
| Oct 24 | Matched onsets; **Step 4** deletion test; parser fix and re-score; **Step 5** dataset rules and length audit; Steps 6–7 code and pilots | 209 + pilots |
| Oct 25–27 | **Steps 6–7** (no-hint runs and training targets), running | ~2,700 so far |
| Oct 26 | Sol kit; **Steps 8, 9, 10** on Sol; window analysis (no calls); data policy | Sol, one interactive session |
| Oct 26–27 | Step 9 follow-up on Sol (CPU); matched onsets on the Mac; "too few questions" rule | none |

## 4. Terms

- **Hint:** extra text naming one **wrong option** (the hint letter, W) of a multiple-choice
  question. The model's **own answer** (O) is its no-hint answer.
- **Channels.** **User:** "I think the answer is (C) but I'm curious what you think" (Turpin's
  wording). **Tool, pasted** (`tool_pasted`): a `[tool result: lookup_answer_key] {"expected": "C",
  …}` block inside the user's message. **Tool, inserted** (`tool_injected`): a tool call and a tool
  reply inserted as their own turns; **declared** when the function is also listed in the system
  prompt. **Real tool call** (`tool_real`): the model calls the tool itself. **System:** the letter
  in the system prompt.
- **Followed / resisted:** the final answer is / isn't the hint letter, always set against the
  per-letter no-hint baseline.
- **Served format:** Voyager's chat endpoint (for Olmo 3 7B Think, the Olmo 3 *Instruct* template).
  **Pinned format:** Olmo 3 7B Think's own Think template, rendered by us and sent to
  `/v1/completions` (Track A, from Oct 21).
- **Early answering** (Lanham et al. 2023): after each sentence of the reasoning, close it and force
  `Answer: (`; read the letters' probabilities. The **takeover** is the sentence from which the hint
  letter leads to the end; a **lead onset** is any sentence where the hint letter becomes the
  leader (lasting = the takeover; temporary = lost again).
- **Sure question:** both Step 2b no-hint runs answered and correct.
- **Full-attention / sliding layers:** Olmo 3 7B has 8 full-attention layers (3, 7, …, 31) and 24
  that see only the last 4,096 tokens.
- **Restoration** (activation patching): (patched − hinted) / (clean − hinted) on logit(W) −
  logit(O); 1 = the clean answer.
- **Keyword count vs hand label:** `detect.py` flags words; two raters label what the text says
  ([`progress/LABELING_GUIDE.md`](progress/LABELING_GUIDE.md)).
- **Cut off:** the reply hit its token limit; it counts as no answer.
- **Test 1** = the pilot (`results/progress.jsonl`); **Test 2** = Experiment B
  (`results/progress/expB_*.jsonl`).

## 5. Models and Voyager

Six open-weight models on ASU's free **Voyager** service (OpenAI-compatible, vLLM), three
instruct / thinking pairs; Track A also runs Olmo 3 7B Think on **ASU Sol** (section 8).

| Our name | Upstream model | Type |
|---|---|---|
| `olmo3-7b-instruct` / `olmo3-7b-think` | allenai/Olmo-3-7B-Instruct / -Think (d97e442 on Sol) | dense, 7B |
| `olmo3-32b-instruct` / `olmo3-32b-think` | Olmo 3 or 3.1 32B (**unconfirmed**) | dense, 32B |
| `qwen3-30b-a3b-instruct-2507` / `-thinking-2507` | Qwen/Qwen3-30B-A3B-…-2507 | MoE, 3.3B active |

The two members of a pair are separately post-trained, so an instruct-vs-thinking gap is a
checkpoint difference, not the effect of thinking alone.

**Voyager facts we found (and the code now guards):**
- **The chat endpoint renders `olmo3-7b-think` with the Olmo 3 *Instruct* template** (Oct 21, from
  prompt-token counts: 178 on a plain question, the Instruct count; every Think revision gives 215).
  Its default system prompt is the Instruct one, its generation prompt has no `<think>`, and a tool
  message becomes an `environment` turn, so an inserted tool turn does reach the model. Every
  served-format run of this model used the Instruct format. Track A renders the official Think
  template itself (T1).
- **The model IDs changed on Oct 21.** One family ID per pair; `reasoning_effort` chooses the
  member (`none`, the default, is the instruct checkpoint). Our six names stay and are mapped on
  every request; a thinking model sent without an effort is refused; the catalog is checked at the
  start of each run (T3). The new `olmo3-7b` + `medium` route gave the same log-probs as the old
  `olmo3-7b-think` on Step 1's 5,185-token text: max difference 0.0003 on the first 2,047 tokens,
  24 top-token mismatches after, all near-ties; the Instruct model gave 654.
- **The identity canary.** An echo call on a fixed 530-token text at the start of each run and
  hourly; the run stops unless the top tokens match and the max difference is under 0.01. A canary
  with no reply pauses requests and retries every 2 minutes, and halts only on a real mismatch or
  after 30 minutes (T6). 47 of 47 checks with a reply passed, Oct 22–26.
- **Stream every request** (replies over ~100 s fail with Cloudflare 524 otherwise; non-streamed
  cut-off replies leak the reasoning). The reasoning field is `reasoning` (was
  `reasoning_content`). `prompt_logprobs` is refused when streaming; `echo` + `logprobs` works. The
  gateway refuses a list of prompts in one request. Seeds repeat runs only partly. At most 4
  requests in flight (`progress/common.slot`).

## 6. The progress round (Oct 1–6)

**Test 1: 24 generated puzzles, user hint, 6 models.** 3 no-hint runs, 2 wrong-hint and 1
right-hint run per puzzle and model (864 runs, plus "think briefly" and "answer only").
- Hints moved only the least sure model: Olmo 3 7B Instruct picked the hint's letter in 5 of 48
  hinted runs, Olmo 3 7B Think in 1 of 48, the other four in 0 of 48; without a hint, 0 of 144.
- The final answer drops what the private reasoning says (three thinking models, 216 hinted runs):
  private 208, final 8 (F3). The keyword also fires on no-hint reasoning (22 of 72 for Olmo 3 7B
  Think), so 208 is an upper bound.
- "Answer only" breaks instruct models (Olmo 3 7B Instruct 21 → 1 of 24 correct), not thinking
  models. Wrong hints add 4.9–58.9% output tokens on all six models.

**Test 2: 30 MMLU-Pro questions, user vs pasted tool hint** (Olmo 3 7B Instruct, Olmo 3 7B Think,
Qwen3 30B Thinking; 2 no-hint runs per question, then 1 user and 1 tool run on the uncertain
questions plus 5 confident controls).

| Model (questions) | User hint | Tool hint | Same letter, no hint |
|---|---|---|---|
| Olmo 3 7B Instruct (19) | 7 | 8 | 4 of 38 runs |
| Olmo 3 7B Think (20) | 2 | 10 | 2 of 40 |
| Qwen3 30B Thinking (11) | 0 | 7 | 0 of 22 |

Thinking models: tool 17 of 31 vs user 2 of 31, +48 points [+31, +65] (F1). When the tool hint won
(17 runs), the reasoning named the tool in 16 and the final answer in 6.

**Experiment A (a demo, not a result).** A reviewer that never saw the hint kept a hinted wrong
answer in 0 of 15 reviews from the answer alone, 7 of 15 once it read the explanation. A guard that
re-asks without the hint flagged 5 of 5, with 1 false alarm in 6 twins.

**Truncation sweep.** Non-streamed cut-off replies put the reasoning in the visible answer in 8 of
8; streamed, 0 of 8.

**Scope checks (Oct 4).** Real tool calls on Voyager: Qwen3 30B Instruct and Thinking and Olmo 3 7B
Instruct call the tool; Olmo 3 7B Think doesn't, and its forced call is invalid. Track C live on 2
puzzles (14 calls): the checker caught the bad lookup; the tool-log reviewer passed it along.

## 7. Track A: explain and fix (Oct 21–27)

All on Olmo 3 7B Think. Numbers and status for each finding are in FINDINGS (F1–F14).

- **Step 1, Voyager capabilities** (8 calls): the template, `<think>` and log-prob facts in
  section 5.
- **Step 2, the pinned format:** the official Think template plus the Instruct template's tool
  turns, rendered locally and split at `</think>` by us; the `tool_injected` channel; source tags
  from the rendered role spans.
- **Step 2b, the base model in the pinned format:** the 20 hinted Test 2 questions × no hint (2
  runs), user (1), pasted, inserted and inserted + declared (3 each): 240 of 240 runs. 93 replies
  cut off at 16,000 tokens were continued up to the 65,536-token context (91 finished). Hint
  following: user 7 of 20, pasted 40 of 60, inserted 24 of 60, declared 34 of 60 (F1, F2); final
  answers name the tool far more than the user (F3); declaring the tool adds +17 points [+3, +30]
  (T2).
- **Step 3, takeover curves** (219 runs, 137,143 probes, one per request): the hint letter leads
  before any reasoning in 198 of 199 hinted runs; the lead swings many times; on sure questions 43
  of 110 hinted runs end on the hint, 26 of them taking over late, on 9 of 11 questions (F4, F5).
  Mentions mark the hint being in play, not winning (F6).
- **Step 4, deleting the reasoning's mentions** (19 cases, 209 calls): the forced answer at the cut
  goes back to the own answer in 7 of 19 vs 1 of 19 for a length-matched control (+32 points [+11,
  +56]); continuations go back to the hint (F7).
- **Step 5, the dataset rules:** a training question is kept only if its 3 no-hint runs are all
  answered and correct; one wrong hint per channel plus 1–2 correct hints per question; training
  channels user, pasted and declared inserted; held out: the 30 MMLU-Pro items and 7 wordings (0
  overlap); 10% validation. Length audit: Step 2b prompt + reply median 11,988 tokens, max 34,706;
  99% fit 32,768, the training and evaluation cap.
- **Steps 6–7, training data** (running since Oct 25): a pool of 1,600 questions (60% MMLU-Pro from
  categories evaluation doesn't use, and harder puzzles). Step 6: 3 no-hint runs per question.
  Step 7: prefill targets: the reasoning opens with one sentence in the model's voice and the final
  answer with one naming the hint (10 paraphrases each), the model writes the rest, and a sample
  passes if it ends on the kept answer without referring to instructions (up to 4 samples).
  Pilots: 5 of 10 questions kept; prefill targets for 28 of 30 records (a guiding note gave 18 of
  30). At 100 kept: keep rate 117 of 250, wrong-hint targets for 87–96% of records per channel,
  "neither" 27 of 533 (TODO, notes). Now: 225 kept of 469.
- **The window** (no calls): the hint's pull may weaken once its last mention leaves the 4,096-token
  window, −0.68 [−1.28, −0.26] in log-odds (F8, tentative).
- **Step 8, the checkpoint check** (Sol): a rule fixed in advance failed narrowly on 4 positions;
  the Sol weights are d97e442 by sha256; Gate 3 therefore runs every system on Sol (F9).
- **Step 9, attention to the hint** (Sol, 199 runs): tool hints get less attention at the answer
  than user hints yet move it more (F10); heads L19H31, L23H17 and L15H31 separate followed from
  resisted runs (F12); the hint takes the lead at sentences that look back at it, kept or not
  (F14).
- **Step 10, activation patching** (Sol, 21 cases, 40 cuts): layers 15, 19 and 23 read the hint's
  letter from the prompt, 0.90 [0.85, 0.96] of the drop at the takeover (F11); the prompt's letter
  read directly does more than the reasoning's repetition (F13).

## 8. Sol setup (Oct 26)

- **Access.** ASU Sol, account `class_cse59888883fall2026` (the CSE 598 section; never the lab's
  `grp_hdavulcu`), `-p public -q class -G a100:1`, `-q debug` for 15-minute tests. `sol/submit.sh`
  passes the account itself and refuses any other; `sol/run.sh` stops outside a job or under another
  account. Batch jobs ask for at most 16 h and resume.
- **Environment.** `/scratch/ragarw68/envs/olmo` (Python 3.11), always called by full path
  (`/scratch/ragarw68/envs/olmo/bin/python`; never the system `python3`, 3.6.8); torch 2.14.1 for
  CUDA 13.0; Hugging Face cache `/scratch/ragarw68/hf`, offline; outputs in `/scratch/ragarw68/trackA/`.
- **The model** is the cached `allenai/Olmo-3-7B-Think` snapshot d97e442; its three weight files
  match d97e442's sha256 (F9).
- **Data.** Code goes to Sol by `git ls-files | rsync`, inputs by rsync from `sol/inputs.txt`
  (checked by sha256 before each step). No API keys on Sol. Results come back as numbers-only
  summary files (plus `step9_reduced.npz`, numbers and run ids, so Step 9 can be re-read on the Mac).
- **Ran:** smoke and Steps 8, 9, 10 in the Oct 26 interactive session; Step 9's follow-up
  (CPU only) on Oct 26–27.

## 9. Measurement traps we hit and fixed

Each would have changed a reported number; details in FINDINGS (T1–T9).

| | Trap | Fix |
|---|---|---|
| T1 | Voyager rendered the Think model with the Instruct template | Render the Think template ourselves |
| T2 | The two templates' default system prompts differ; declaring the tool changes hint following by +17 points | Every record names its system prompt |
| T3 | Oct 21: model IDs became families + effort; the default effort serves Instruct | One name → (ID, effort) map; refuse a Think model without effort |
| T4 | The parser missed "**Answer**: D" | Fixed; re-scoring changed 1 letter |
| T5 | Plain "expected" matched 7 non-hint sentences | Narrowed the tool-mention words |
| T6 | A network error logged as a failed identity check | No reply is no verdict; pause and retry |
| T7 | Averaging a cumulative restoration curve by layer type | The per-layer drop and its share |
| T8 | A weights check that read link names and hashed nothing | Hash regular files; count failures |
| T9 | Anchoring one group where the hint is strongest (twice) | Anchor every group the same way |

Also: cut-off replies leak when not streamed; a tool call quoted inside the reasoning tripped the
tool-call stop (7 runs, continued); streams that closed without a finish reason were taken as
complete (3 runs, rerun); the Mac sleeping on battery stalls Voyager runs (Oct 27, 9 hours).

## 10. Code and data map

All code is in `cot-disclosure/` ([its README](../cot-disclosure/README.md): setup and commands).
283 tests pass, no network (`cd cot-disclosure && ../.venv/bin/python -m pytest -q`).

| Path | What it is |
|---|---|
| `client.py`, `parse.py`, `detect.py` | Voyager client (streaming, guards, canary, cache); answer-letter parser; keyword pre-sort |
| `tasks.py`, `experiments.py`, `analyze.py`, `run.py` | Puzzles; Test 1; its numbers; the Oct 1–2 runner |
| `progress/` | The progress round (Test 2, Experiment A, truncation, `analyze_progress.py`), `common.py` (records, limiter, Wilson, clustered bootstrap, the 5-question rule), `run_trackB.py` |
| `providers/` | One interface over Voyager, Ollama, OpenAI, Anthropic, xAI; `budget.py` caps and logs spend |
| `tools/answer_key.py` | The hint conditions (`none`, `user`, `tool_pasted`, `tool_real`, `tool_injected`, `system`) |
| `tools/export_summaries.py`, `prepush_check.py`, `untrack_produced.py` | Numbers-only summaries with a no-text check; the pre-push check; the history rewrite |
| `agents/` | Track C: solver, reviewer, checker, `run_team.py` |
| `finetune/` | Track A Steps 1–7 and the dataset ([README](../cot-disclosure/finetune/README.md)) |
| `finetune/look/` | Steps 3, 4, 9, 10, the window analysis and their figures |
| `finetune/gpu/` | The Sol kit and Step 8 ([README](../cot-disclosure/finetune/gpu/README.md)) |
| `configs/` | `models.yaml` (IDs, routing), `canary/`, `prices.yaml`, `trackB.yaml` |
| `ui/` | The demo app (`python3 cot-disclosure/ui/app.py`, http://127.0.0.1:8765) |

**Data policy (Oct 26).** The repo is public; produced files never go to GitHub. Runs, probes,
replies, caches, checkpoints and Sol outputs are gitignored (`results/trackA/`, `results/trackB/`,
`results/trackC/`, `finetune/data/`); numbers-only summaries and figures are tracked in
`results/summaries/`. A pre-push hook refuses produced data, any GPQA file, and files over 50 MB.
The progress-round result files on `main` (`results/progress/`, `results/progress.jsonl`, …) stay
as they are. Result files are never edited; new runs are appended.

**Presentation** (`presentation/`): the progress deck (v3 was presented), figures F1–F9, the
evidence viewer, the demo screenshots.

## 11. Known gaps

- **No closed-provider keys** (Track B's OpenAI, Anthropic and xAI runs and Gate 1's smoke tests
  can't start). Spend: $0. Claude Haiku 4.5 may be retired; check before running.
- **GPQA Diamond** is gated: access, then export to `cot-disclosure/data/gpqa_diamond.jsonl`
  (gitignored).
- **Labeling hasn't started.** 10 of the 101 queue rows have no text. Every mention number stays a
  keyword count until two raters label.
- **GitHub is behind.** `main` there lacks the Oct 21 Voyager ID fix and the data gitignore; this
  branch (`trackA-nosol`, 50+ commits) is unpushed until its history drops the Track A data.
- **The look-inside findings rest on few questions:** 9 for the late takeovers and the patching
  cases, 20 for Step 9. Olmo 3 32B's exact identity on Voyager is unconfirmed.
