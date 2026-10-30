# Session log: Thread 1 on a second model: Qwen3-8B Steps 3 and 10, prepared and pre-registered (2026-10-30 11:45 MST)

Project: CSE 598 Group 10, Track A. "One model" is Thread 1's biggest gap. Ritik asked (Oct 30) for Step 3 (takeover
probes) and Step 10 (patching) for Qwen3-8B with thinking on, using Track B's runs on Sol, with these constraints:
- localization on one half;
- a pre-registered replication on the other;
- nothing ever chosen on the 30 evaluation questions;
- prepared, not submitted.

Code in `af2f2fb`. **By:** Ritik.

## 1. Why Qwen3-8B is a real test

Olmo 3 7B Think's readout (15, 19, 23) is partly forced by its architecture: 24 of its 32 layers slide over 4,096
tokens, so a far hint can be read only by the 8 full-attention layers. Qwen3-8B has 36 layers, all full attention
(`use_sliding_window: false`). Any layer can read the hint. If a few still carry most of the drop, and they are the
same few on new questions, the readout isn't an artifact of Olmo's windows.

## 2. Halves, channel and counts

- **Localization: the 24 pilot puzzles only.** Track B's other set, `mmlupro_30`, **is** Track A's 30 evaluation
  questions (the same file). So it can only be the replication half, read by the rule below. The localization
  code refuses any non-puzzle or any of the 30, and a test shows the chosen layers don't change with the MMLU-Pro
  data.
- **Channel: `tool_real`** (the model calls `lookup_answer_key`; the wrong letter comes back as a real tool
  message). On the puzzles it is the only channel followed: 66 of 72 runs; pasted and system once each, user never.
  It is Qwen's analog of Olmo's declared inserted tool turn. Pasted, system and user are described on MMLU-Pro only,
  outside the verdict.
- **Counts** (thinking on; from the Mac's numbers-only runs file; `qwen8b_mech.py plan`):

| half | sure questions | followed `tool_real` runs | on sure questions |
|---|---|---|---|
| puzzles (localization) | 23 of 24 | 66 (24 questions) | 63 (23) |
| MMLU-Pro (replication) | 21 of 30 | 77 (28) | 50 (19) |

How many are late takeovers (the cases) is unknown until Step 3 runs.

## 3. Method (`finetune/look/qwen8b_mech.py`)

- **Prompts:** each run's final-call prompt is rebuilt with Track B's renderer.
  - It must match the server's token count; a run that doesn't is left out.
  - If more than 10% don't match, the job stops before loading the model.
- **Step 3:** every sentence of all 251 followed thinking-on runs is probed, as Track A's Step 3 does.
  - The forced answer closes Qwen3's think block, then "Answer: (".
  - The probes use a reused cache, checked against fresh forwards at 2 probes per run.
  - The takeover point, "late" (at or after half the reasoning) and the cases follow Track A's definitions.
- **Step 10:** Track A's patching code unchanged, at cuts (i) and (ii).
  - The clean prompt swaps the hint's W for O in the tool's reply (one token).
  - Restoration is measured per layer at the hint tokens, the reasoning and the answer position.

## 4. The rules (fixed before any probe; two choices are Ritik's, below)

**Definitions.**
- **Cases:** followed `tool_real` runs whose takeover is at or after half the reasoning, on questions whose 3
  no-hint runs were all correct.
- **Drop at layer l:** restoration at the hint's tokens after layer l − 1 minus after layer l (`patching.handoff`).
- **Excluded cuts:** |LD_clean − LD_hinted| < 0.5.
- **Intervals:** 95% bootstrap clustered by question.

**Localization** (puzzles, `tool_real`, cut (ii)): the chosen layers S are the 3 layers with the largest mean drop,
ties to the lower layer. With fewer than 5 questions with a usable cut, the result is "too few" and nothing is
chosen (fallback, decision 3).

**Replication** (MMLU-Pro, `tool_real`, cut (ii)), with S:
- **replicates:** the share of the drop at S has a lower bound above **T**, *and* S **match** this half's 3 largest
  drops;
- **partly:** one of the two;
- **doesn't replicate:** neither;
- **too few:** fewer than 5 questions with a usable cut.

Reported either way against the puzzles' share at S and Olmo's 0.90 (Test 2, set A).

**Descriptive only, never in the verdict:**
- how many layers hold 80% of the drop;
- cut (i);
- the answer position's rise at S;
- the swap of only the prompt's letter;
- the secondary channels.

## 5. Ritik's choices before anything is submitted

The rule becomes final when these are answered. The jobs aren't submitted before then, so no data exists yet.

1. **T, the share threshold.**
   - As drafted: T = 3/36 = 0.083, S's even share. That mirrors Olmo's 3/8 = 0.375, but with 36 layers almost any
     concentrated pattern passes it.
   - **Recommended: T = 0.5**, "these three layers hold most of the drop". That is the claim that would make the
     readout a property of the model rather than of Olmo's windows.
2. **"Match".**
   - Strict: S are exactly this half's top 3.
   - **Recommended: each layer of S is within one layer of one of this half's top 3.** In 36 layers, neighbours can
     swap ranks from noise. The strict version stays as a descriptive line either way.
3. **If the puzzles give too few cases.**
   - Plausible: the tool's reply sits right before the thinking, so Qwen may lead with W from the start (an "at 0"
     takeover, not a late one).
   - **Recommended, A:** 24–48 fresh puzzles from the existing generator with a new seed at the pilot's level, run on
     Sol (no hint × 3, `tool_real` × 3; about 1 GPU h; a small runner, not written yet). Then Steps 3 and 10 on
     them.
   - **B:** widen the case rule on both halves to any takeover after the first sentence. It has to be fixed before
     Step 3 is read.
4. **Step 10's limit.** `--estimate 4.3` (a 6:00 limit) covers the upper bound. `--estimate 3.0` (4:00) covers the
   puzzles and MMLU-Pro `tool_real`; the secondary channels would resume in a second job.

## 6. Cost and lines

**GPU estimate** (A100 80 GB, bf16; 8,000 tokens/s and 0.05 s per cached probe are assumptions, not measurements):
- Step 3: about 1.1 h.
- Step 10: about 2.6 h at Olmo's late-takeover share, at most 4.3 h.

**After the current 10 jobs, as places free** (MaxSubmitPU 10). It needs the push and a `git pull` on Sol:

```bash
# optional, login node, no GPU (~1–2 min): rebuilds every prompt and checks it against the server's count
source cot-disclosure/finetune/gpu/sol/env.sh && cd cot-disclosure && "$TRACKA_PY" finetune/look/qwen8b_mech.py step3 --dry-run && cd ..
cot-disclosure/finetune/gpu/sol/submit.sh qwen8b_step3 --estimate 1.2
cot-disclosure/finetune/gpu/sol/submit.sh qwen8b_step10 --estimate 4.3 --dependency=afterok:<the qwen8b_step3 job id>
```

If Step 3 fails, the dependent Step 10 sits pending: `scancel` it.

**Copy back (numbers only, one remote path per rsync):**
```bash
cd ~/Documents/Projects/ODL/cse598-cot-faithfulness/cot-disclosure && mkdir -p results/trackB/qwen8b_mech
S=ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/trackA
rsync -av $S/qwen8b_step3/qwen8b_step3.json results/trackB/qwen8b_mech/
rsync -av $S/qwen8b_step3/takeover_runs.jsonl results/trackB/qwen8b_mech/
rsync -av $S/qwen8b_step3/cases.jsonl results/trackB/qwen8b_mech/
rsync -av $S/qwen8b_step10/qwen8b_step10_patching.json results/trackB/qwen8b_mech/
rsync -av $S/qwen8b_step10/qwen8b_readout.json results/trackB/qwen8b_mech/
../.venv/bin/python finetune/look/qwen8b_mech.py readout results/trackB/qwen8b_mech/qwen8b_step10_patching.json
```

## 7. Tested, and not

- **Tested:** 23 CPU tests with a tiny random Qwen3 on the real tokenizer and chat template, covering the hint spans,
  the one-token clean prompt, the forced answer, cached against fresh probes, the patching identities, the guard
  against the 30, the planted verdicts, and both jobs end to end. The full suite: 561.
- **Not tested on a GPU:** bf16 numerics of the cached probes; CUDA attention on a trimmed cache; loading the real
  snapshot; memory at 30K+ tokens; the throughput figures; whether the rebuilt prompts equal what vLLM saw (the
  job's check 1 and the login-node dry run test this).
