# Track A GPU kit: ASU Sol

The look-inside steps that need the weights (Steps 8–10), and the Sol plumbing every later GPU
step (11–13) reuses. The Sol commands below run from the clone's root
(`/scratch/ragarw68/cse598-cot-faithfulness`); the scripts move into `cot-disclosure/` and the
project environment `/scratch/ragarw68/envs/olmo` (Python 3.11) themselves. Never use the system
`python3` (3.6.8). The Mac commands run from `cot-disclosure/` with the repo's `.venv`.

| Item | Script | Reads | Output on Sol | One A100 80GB |
|---|---|---|---|---|
| 1. environment + smoke | `sol/setup_env.sh`, `smoke.py` | the cached model | `/scratch/ragarw68/trackA/smoke/smoke.json` | setup 5–15 min (downloads); smoke 2–5 min |
| 2. Step 8: checkpoint check | `checkpoint_check.py` | Step 1, Oct 21 and canary echoes | `/scratch/ragarw68/trackA/step8/step8_checkpoint.json` | 5–10 min |
| 3. Step 9: attention to the hint | `../look/attn_to_hint.py` | the 199 hinted, answered Step 2b runs | `/scratch/ragarw68/trackA/step9/step9_attention.json` | 15–40 min |
| 4. Step 10: activation patching | `../look/patching.py` | Step 4's 21 cases (Steps 3–4) | `/scratch/ragarw68/trackA/step10/step10_patching.json` | 1–2 h |

In all, about 2–3 GPU hours: everything fits in today's session (until 6:30 pm) if it runs in
order (smoke, 8, 9, 10). Each step resumes where it stopped, so a later batch job picks up what the
session didn't finish.

## Rules every script follows

- **Account.** Every job runs under `class_cse59888883fall2026` (the CSE 598 section), never the
  lab's `grp_hdavulcu`. `sol/submit.sh` always passes `-A class_cse59888883fall2026` itself and
  refuses a job script that names another account, or any account option you add. Inside a job,
  `sol/run.sh` checks `$SLURM_JOB_ACCOUNT` and stops under any other account, and also stops
  outside a Slurm job (login nodes). Don't call `sbatch` directly.
- **Where.** `-p public -q class -G a100:1` (class QoS: at most 24 h, 4 GPUs, 32 cores, 320 GB
  per job; 2 running and 10 queued jobs, and 960 GPU running minutes in all). Your open session
  counts against the 960, so while it's open, run in the session. Batch jobs ask for at most
  16 h and resume from their own checkpoints. Quick script tests: `-q debug` (15 min). Setup
  without a GPU: `-p lightwork -q public`.
- **Model.** `allenai/Olmo-3-7B-Think` from `HF_HOME=/scratch/ragarw68/hf`, offline
  (`HF_HUB_OFFLINE=1`). Every output records the snapshot's commit hash and whether it is
  `d97e442`, the revision our template came from. If it isn't, the kit says whether its files,
  and at least its weights, equal d97e442's. It checks this offline: the cache names each file by
  its hash, and `olmo3_7b_think_d97e442.json` lists d97e442's hashes. On Oct 26, `main` was
  d97e442, and the weights were the same in 24 of the repo's 25 revisions (all but the first).
- **Outputs.** `$TRACKA_OUT/<step>/` = `/scratch/ragarw68/trackA/<step>/`, plus a console log
  there. Only the small summary file of each step comes back to the Mac
  (`cot-disclosure/results/trackA/gpu/`, committed).
- **No API keys on Sol.** Anything compared with Voyager uses values already saved on the Mac
  (the result files below).

## 0. Code and data onto Sol

**The repo is public and stays public. Produced files never go to GitHub** (decided Oct 26).
- Runs, probes, replies, caches, checkpoints and Sol outputs live in gitignored folders:
  `results/trackA/`, `results/trackB/`, `results/trackC/`, `finetune/data/`, and
  `/scratch/ragarw68/trackA/` on Sol.
- Numbers-only summaries and figures go in `results/summaries/` (tracked;
  `tools/export_summaries.py` checks that they hold no question or reply text).
- A pre-push hook (`tools/prepush_check.py`, installed in `.git/hooks/pre-push` on the Mac)
  refuses a push that would add produced data, a GPQA file, or a file over 50 MB.

### Code: GitHub

`trackA-nosol` can be pushed once its history no longer carries the Track A data. That is done by
`tools/untrack_produced.py --run`, after the Steps 6–7 run has finished: it rewrites the unpushed
commits without moving any file on disk, and the hook checks it. Then:

```bash
git push origin trackA-nosol                                         # Mac; the hook checks it
git clone -b trackA-nosol https://github.com/shrey-Bish/cse598-cot-faithfulness.git \
    /scratch/ragarw68/cse598-cot-faithfulness                        # Sol, once
cd /scratch/ragarw68/cse598-cot-faithfulness && git pull              # Sol, after each push
```

Until then, the code also goes by rsync (tracked files only):

```bash
cd ~/Documents/Projects/ODL/cse598-cot-faithfulness
git ls-files | rsync -av --files-from=- ./ ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/
```

(An earlier clone made from the Oct 26 bundle works too; replace it with the GitHub clone once
the push is done.)

### Data: rsync (VPN on)

Steps 8–10 read the files below; `finetune/gpu/sol/inputs.txt` lists them. Each step checks
their sha256 against `finetune/gpu/inputs_manifest.json` before it runs, and
`python finetune/gpu/kit.py --check-inputs` checks them all. The `results/trackA/` files are
gitignored, so only rsync brings them; the other three are tracked.

| File (under `cot-disclosure/`) | Size | Used by |
|---|---|---|
| `results/trackA/voyager_capabilities.jsonl.gz` | 0.10 MB | Step 8: Step 1's echo log-probs (old route) |
| `results/trackA/voyager_ids_check.jsonl.gz` | 0.30 MB | Step 8: the Oct 21 echoes (low / medium / high; default = Instruct, the negative control) |
| `configs/canary/olmo3-7b-think.json` | 0.07 MB | Step 8: the canary text and its reference log-probs (tracked) |
| `results/trackA/base_format.jsonl.gz` | 7.25 MB | Steps 9, 10: the Step 2b runs (prompts, reasoning) |
| `results/trackA/takeover_runs.jsonl` | 0.15 MB | Step 9: Step 3's outcome and takeover point per run |
| `results/trackA/takeover_cases.jsonl` | 0.01 MB | Step 10: Step 3's default cases |
| `results/trackA/deletion_runs.jsonl` | 0.15 MB | Step 10: Step 4's results, for the cut (ii) cross-check |
| `results/progress/expB_cued.jsonl` | 2.70 MB | Steps 9, 10: which questions and hint letters Step 2b used (tracked) |
| `data/progress/mmlupro_30.jsonl` | 0.03 MB | Steps 9, 10: the questions and answer keys (tracked) |

```bash
cd ~/Documents/Projects/ODL/cse598-cot-faithfulness/cot-disclosure
rsync -av --files-from=finetune/gpu/sol/inputs.txt ./ \
    ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/cot-disclosure/
```

### Results back

Sol outputs stay in `/scratch/ragarw68/trackA/`. Only each step's summary comes back, into the
gitignored `results/trackA/gpu/` on the Mac:

```bash
cd ~/Documents/Projects/ODL/cse598-cot-faithfulness/cot-disclosure && mkdir -p results/trackA/gpu
S=ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/trackA
rsync -av $S/smoke/smoke.json $S/step8/step8_checkpoint.json $S/step9/step9_attention.json \
    $S/step10/step10_patching.json results/trackA/gpu/
rsync -av $S/step9/step9_followup.json $S/step9/step9_aligned.png $S/step9/step9_aligned.svg \
    $S/step9/step9_onsets.png $S/step9/step9_onsets.svg $S/step9/step9_reduced.npz \
    results/trackA/gpu/                                    # after the Step 9 follow-up (section 3)
```

Then, on the Mac:
- `python finetune/gpu/step8_verdict.py --sha256sum results/trackA/gpu/weights_sha256.txt`
  applies the Oct 26 Step 8 rule. It lists every position outside near-ties with both sides'
  gaps, compares the weights' `sha256sum` from Sol with d97e442's, and writes the numbers to
  `results/summaries/trackA/step8_verdict.json`.
- `python finetune/look/patching.py --handoff results/trackA/gpu/step10_patching.json` gives the
  readout: per layer, the drop in hint-token restoration and the rise at the answer, with their
  shares at the full-attention layers and at 15, 19 and 23, split by the hint's distance. It also
  puts the direct and written paths side by side at cut (ii), per case. Outputs:
  `results/summaries/trackA/step10_handoff.json` and the handoff figure,
  `results/trackA/figures/step10_handoff.png`.
- `python finetune/look/patching.py --by-layer-type results/trackA/gpu/step10_patching.json`
  gives the first, superseded reading: mean restoration over the full vs sliding layers
  (docs/FINDINGS.md, T7).
- `python tools/export_summaries.py` copies the numbers-only Step 9 and 10 summaries and the
  figures into `results/summaries/trackA/`.

`smoke.json` and `step8_checkpoint.json` hold prompt text and token strings, so they stay
gitignored.

## 1. Environment and smoke test

Installs pinned torch 2.14.1 (the CUDA 13.0 build; the driver reports CUDA 13.4 and runs any build
up to it), transformers, accelerate, peft and the repo's requirements into the existing
environment (`requirements-sol.txt`; no vLLM until Steps 12–13). Then loads the model in bf16 on
the GPU, generates 32 tokens (greedy) in our pinned Think format, and prints the GPU name, library
versions, the snapshot hash (and whether it matches d97e442), whether the snapshot's own chat
template renders our prompt exactly, and the config fields the later steps need (layers, heads,
key/value heads, hidden size, max positions, sliding-window settings, tie_word_embeddings).

**In your session** (from the clone):

```bash
cd /scratch/ragarw68/cse598-cot-faithfulness
bash cot-disclosure/finetune/gpu/sol/setup_env.sh        # 5-15 min, once
cot-disclosure/finetune/gpu/sol/run.sh smoke              # 2-5 min
```

**Batch:** `cot-disclosure/finetune/gpu/sol/submit.sh setup_env` (lightwork, no GPU), then
`cot-disclosure/finetune/gpu/sol/submit.sh smoke` (debug QoS, 15 min). Log:
`/scratch/ragarw68/trackA/slurm/trackA-smoke-<job>.out`.

**CPU test (Mac):** `python -m pytest tests/test_trackA_gpu_kit.py` (a tiny random Olmo 3 with the
real tokenizer; the offline snapshot check; the account guards), and
`python finetune/gpu/smoke.py --dry-run` (the real config; the memory check refuses the Mac:
the model needs ~15.6 GiB).

**Look for:** `snapshot d97e442… matches d97e442`, `renders our prompt exactly`, the A100 and
CUDA 13.0 in the versions, and a sensible start of reasoning in `generated:`.

**Back to the Mac:** `/scratch/ragarw68/trackA/smoke/smoke.json` (a few KB; see "Results back").

## 2. Step 8: checkpoint check

Is Voyager's `olmo3-7b-think` the checkpoint we load? A local forward pass over the saved texts
whose per-token log-probabilities Voyager returned by echo, compared token by token with the
two-part rule (`docs/PLAN.md`, Track A):

- **Strict on the first 2,047 tokens:** the same top token at every position, and max absolute
  log-prob difference under 0.01.
- **Beyond that** (Voyager seems to process long prompts in 2,048-token chunks): the mean, median
  and max difference, and top-token mismatches counted only where they are not near-ties. A
  near-tie means the two tokens are within 0.1 probability of each other: under the local model,
  and under Voyager too when its saved top tokens include both. A mismatch outside a near-tie fails.

| Reference | Tokens | Saved |
|---|---|---|
| `step1_old_route` | 5,185 | Step 1 call 8, `olmo3-7b-think` before the Oct 21 ID change |
| `oct21_low`, `oct21_medium`, `oct21_high` | 5,185 each | the same text through `olmo3-7b` at each effort |
| `canary` | 530 | the identity canary's reference (all of it falls in the strict part) |
| `oct21_default` (negative control) | 5,185 | the same text at the default effort = the **Instruct** checkpoint; it must fail |

The rule is applied to the bf16 pass, the dtype every GPU step uses. An fp32 pass with the same
weights (loaded once in fp32, then cast to bf16, which is exact) is reported beside it, to tell
numerics from a different checkpoint. For scale: Voyager against itself (old vs new route) was
max 0.0003 in the strict part, mean 0.006 / max 0.19 beyond, with 24 mismatches, all near-ties.
The Instruct model against Think gave 654 mismatches, mean 0.32 and max 20.7.

**In your session:** `cot-disclosure/finetune/gpu/sol/run.sh step8` (5–10 min, peak ~32 GiB).
**Batch:** `cot-disclosure/finetune/gpu/sol/submit.sh step8` (class QoS, 30 min).
**CPU test (Mac):** `python -m pytest tests/test_trackA_checkpoint.py`. This covers the rule on
synthetic log-probs (a strict-part difference, near-ties, a mismatch outside one, Voyager-side
gaps), echo alignment, and an end-to-end run on a tiny random Olmo 3 whose own log-probs stand in
for Voyager's. `python finetune/gpu/checkpoint_check.py --dry-run` checks the references and
alignment (all 5 Think references align token for token; the control has 5 positions tokenized
differently, so it is compared on the rest).

**Look for:** the table, then the decision under the Oct 26 rule (`step8_verdict.py`). If it
fails, the strict part's `worst` and `mismatches` and the beyond part's `outside_examples` in the
JSON show where. Per-position differences are in `step8_positions.npz`.

**Result (Oct 26).** (a) fails at 4 positions with gaps of 0.113–0.140; (b) and (c) hold; the
weights on Sol are d97e442's by sha256 (docs/FINDINGS.md, F9). Since then, the snapshot check
hashes regular files: Sol's snapshot holds copies, not cache links, and the first run reported
`weights_same: false` without hashing. Each file is hashed once, and the result is kept in
`/scratch/ragarw68/trackA/file_hashes.json`. The first run after this change reads the 15 GB of
weights, about a minute. To check by hand:

```bash
cd /scratch/ragarw68/hf/hub/models--allenai--Olmo-3-7B-Think/snapshots/d97e442d7cc678210054dbcc9b440894d62c89a4
sha256sum model-0000*-of-00003.safetensors     # paste into results/trackA/gpu/weights_sha256.txt on the Mac
```

**Back to the Mac:** `/scratch/ragarw68/trackA/step8/step8_checkpoint.json` (tens of KB).

## 3. Step 9: attention to the hint

`finetune/look/attn_to_hint.py`: one forward pass per run, no gradients, over prompt + reasoning +
`</think>\n\nAnswer: (`, for the 199 hinted Step 2b runs that ended with an answer:

| Channel | Followed | Resisted |
|---|---|---|
| user | 7 | 13 |
| tool, pasted | 40 | 19 |
| tool, inserted | 24 | 36 |
| tool, inserted + declared | 34 | 26 |

Lengths run from 1,944 to 34,089 tokens (median 11,842).

- **How.** There is no `output_attentions`. An attention implementation registered by the script
  receives each layer's queries and keys after the rotary embedding, computes the masses in fp32,
  then runs the model's own sdpa attention unchanged (a test checks the logits are identical).
  The mass on a span is `exp(logsumexp(scores to the span) − logsumexp(scores to every key the row
  may see))`, in chunks of 512 query rows and 4,096 keys. Grouped key/value heads are handled
  (Olmo 3 7B has none: 32 and 32).
- **Sliding window.** 24 of the 32 layers are sliding-window (4,096). A token more than 4,096
  tokens past the hint gets exactly 0 from them, so at the answer position, usually only the 8
  full-attention layers (3, 7, …, 31) can see the hint. The summary counts the runs where the
  answer is within the window.
- **Spans** (`finetune/look/hint_spans.py`, checked on all 199 runs). The hint is its whole text:
  16 tokens (user), 31 (pasted) or 23 (inserted). Also its letter (1 token), and a control span of
  the question stem with as many tokens as the hint. In 187 of 199 runs the control lies inside the
  stem; in the other 12 the stem is shorter, so it runs on into the options.
- **From where.** The answer position (the last `(`), per layer × head; and each reasoning
  sentence (Step 3's sentence split), the mean over its tokens, as a curve.
- **Comparisons**, as bootstrap differences clustered by question: followed − resisted (pooled and
  per channel), tool − user, pasted − inserted, and inserted − inserted + declared. Each on: all
  heads, the 10 top heads, hint − control, the letter, and the hint per token. The top heads are
  chosen on all runs pooled.

**In your session:** start with a quick check on the 3 shortest runs, then run the rest (it
resumes; the report runs at the end):

```bash
cot-disclosure/finetune/gpu/sol/run.sh step9 --limit 3      # ~3 min with the load
cot-disclosure/finetune/gpu/sol/run.sh step9                # the rest, then the report
```

**Batch:** `cot-disclosure/finetune/gpu/sol/submit.sh step9` (class QoS, 2 h; resumes from the
runs already saved). `run.sh step9 --report` rebuilds the summary from the saved runs.
**CPU test (Mac):** `python -m pytest tests/test_trackA_attn.py`. On sequences under 512 tokens
with tiny random Olmo 3 models, the masses match eager `output_attentions` within 1e-3. This is
checked with sliding-window layers and 1, 2 and 4 key/value heads, with chunks crossing rows and
keys, for user, pasted and inserted prompts built the Step 2b way. The test also checks that the
capture leaves the logits unchanged, and runs the script plus its report on the 2 shortest real
Step 2b runs. `python finetune/look/attn_to_hint.py --dry-run` gives the runs, tokens and estimate.

**Outputs** in `/scratch/ragarw68/trackA/step9/`:
- `runs/<run_id>.npz`: answer [3 spans × 32 layers × 32 heads]; sentences [3 × sentences × 32 ×
  32] (fp16)
- `step9_runs.jsonl`: per run, the spans, channel, outcome, Step 3's takeover point, the forced
  answer's letter probabilities, and the snapshot hash
- `step9_maps.npz`: group mean maps and binned curves, plus the top heads

**Back to the Mac:** `step9_attention.json` (group means, layer profiles, top heads, comparisons,
curves; tens of KB).

**Follow-up (Oct 26), no GPU, from the saved runs.** It reads `runs/*.npz`, `step9_runs.jsonl` and
two tracked files: `results/summaries/trackA/takeover_per_run.jsonl` (Step 3's takeovers and closest
approaches) and `hint_onsets.jsonl` (Step 3's lead onsets). So first re-send the code (section 0,
the `git ls-files` rsync). It covers:
- every comparison on the 8 full-attention layers only
- the 25 runs whose answer is within reach of the hint in the sliding layers, apart: all, full and
  sliding layers
- hint − control and per-token mass instead of raw mass
- the top heads re-ranked: by hint − control, and within those 25 runs over all 32 layers
- the heads in layers 15, 19 and 23 (Step 10's readout layers), followed vs resisted, with
  intervals
- attention to the hint from each reasoning sentence, aligned on the takeover (followed) or the
  closest approach (resisted): full layers, and sliding layers where the sentence is within reach.
  This is biased, because the closest approach is picked where the hint is strongest.
- the matched version: the attention rise at every lead onset after the first fifth, permanent
  (the takeover) vs temporary, picked the same way in every run (`onsets_matched`,
  `step9_onsets.png`)

Every interval resting on fewer than 5 questions is replaced by "too few questions", and every
group shows its questions as well as its runs.

```bash
cot-disclosure/finetune/gpu/sol/run.sh step9 --followup     # ~1 min, CPU only
```

It writes `step9_followup.json` (numbers only), `step9_aligned.png` / `.svg` and `step9_onsets.png`
/ `.svg`. It also writes `step9_reduced.npz` (about 3 MB, numbers and run ids only): each run's
answer masses and per-sentence means. Copy them all back as in "Results back". With the reduced
file on the Mac, later re-anchoring needs no Sol run:

```bash
python finetune/look/attn_to_hint.py --followup --from-reduced results/trackA/gpu/step9_reduced.npz
```

The CPU test is `tests/test_trackA_attn.py::test_followup_on_saved_runs`.

## 4. Step 10: activation patching

`finetune/look/patching.py`: the causal test. Swap one layer's activations at a time and see which
layer brings the answer back.

- **Cases.** Step 4's: the late-takeover runs on sure questions from Step 3, at most 3 per
  question (`deletion.choose`, seed 0). That gives 21 runs, all tool hints: 11 pasted, 3 inserted,
  7 inserted + declared.
- **Cuts**, each followed by `</think>\n\nAnswer: (`:
  - (i) the reasoning just before its first hint mention (Step 4's mention words)
  - (ii) the reasoning up to the takeover point

  Cases with no hint mention before the cut get only cut (ii). That is 2 cases (9837
  inserted + declared run 1, 11392 pasted run 1), so there are 40 cuts in all (19 + 21). They run
  from 348 to 32,674 tokens (median 6,677). Step 3's sentence split was rechecked for all 21 runs,
  so the 15.7 MB probes file isn't needed on Sol.
- **Pairs.** The hinted prompt has the wrong letter W. The clean prompt replaces W with the own
  no-hint letter O inside the hint only. The token counts must match and the prompts may differ
  only inside the hint; otherwise an equal-length neutral filler is used. All 21 cases differ in
  exactly one token (the letter) with equal length, so no filler is needed. Both keep the same
  reasoning.
- **Measure.** LD = logit(W) − logit(O) at the answer position. Restoration = (patched − hinted)
  / (clean − hinted). A cut whose |clean − hinted| is under 0.5 is left out of the means and
  counted, since there the ratio is noise.
- **Patch.** One decoder layer at a time, the clean run's layer output is copied into the hinted
  run at the hint's tokens, the reasoning, or the answer position: 32 × 3 patched passes per cut.
  Restoration by layer for each group goes into `step10_restoration.png`, with a panel per cut and
  bootstrap intervals clustered by question.
- **Sanity checks**, per cut: patching every position at the last layer gives the clean LD, and
  patching nothing gives the hinted LD.
- **Cut (ii) note**, in the output. Here the reasoning itself names W. If the clean run still
  answers W, the reasoning's repetition carries the hint. The report lists, per case, the clean
  run's answer next to Step 4's forced answer after deleting the mentions.

**In your session:**

```bash
cot-disclosure/finetune/gpu/sol/run.sh step10 --limit 3     # quick check on the 3 shortest cuts, ~3 min
cot-disclosure/finetune/gpu/sol/run.sh step10               # the remaining cuts, then the report
```

**Batch:** `cot-disclosure/finetune/gpu/sol/submit.sh step10` (class QoS, 4 h; resumes from the
saved cuts). `run.sh step10 --report` rebuilds the summary and the figure.
**CPU test (Mac):** `python -m pytest tests/test_trackA_patching.py`. It checks the equal-length
pairs (user, pasted, inserted) and the filler fallback, and the identities that must hold exactly:
- patching the answer position at the last layer gives the clean LD
- patching the reasoning at the last layer leaves the hinted LD
- a full copy at any layer gives the clean LD

It also checks the cuts on the real cases (21 cases, 19 with cut (i)), and runs the script and its
report on the 2 shortest real cuts with a tiny random Olmo 3.
`python finetune/look/patching.py --dry-run` lists every cut with its tokens.

**Outputs** in `/scratch/ragarw68/trackA/step10/`:
- `cuts/<run>_<cut>.json`: per cut, the LDs per group and layer, both baselines, letter
  probabilities, the sanity checks and the snapshot hash
- `step10_restoration.png` and `.svg`

**Back to the Mac:** `step10_patching.json`. It holds every cut's LDs, so the figure can be
redrawn on the Mac (`python finetune/look/patching.py --plot results/trackA/gpu/step10_patching.json`)
and the readout computed there (`--handoff`, see "Results back"; the hint's distance to the answer
is rebuilt with the tokenizer alone).

## Later steps on the trained versions (Phase 6)

Steps 9 and 10 take `--model DIR` (a merged or wrapped trained version), `--runs-from` (that
version's own runs, in the Step 2b format) and, for Step 10, `--cases-from` (its own Step 3 cases).
Outputs then go to their own `--out` directory.

**Mechanism check (Step 13).** Rerun Step 10 on the best version and run `--handoff` on its
summary. Report whether the drops in hint-token restoration at layers 15, 19 and 23 shrink: they
are 0.90 [0.85, 0.96] of the total drop at cut (ii) in the base model.
