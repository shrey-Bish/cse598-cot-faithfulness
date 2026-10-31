# Session log: B1's stricter path, the bench as the gate, and the push (2026-10-31 12:40 MST)

Project: CSE 598 Group 10, Track A (B1). **By:** Ritik. No calls and no GPU. Ritik's decisions on the 11:50 log, item
by item.

## 1. Pushed

`c6f4d31` was pushed, and `main`, `trackB-main` and `trackC-main` were fast-forwarded to it and pushed:
`a752db5..c6f4d31` on all four.
- Checks:
  - the full test suite, 648 passed;
  - the pre-push check passed (and passed again as the hook);
  - author and committer Ritik, no attribution lines;
  - the three branches were ancestors of `c6f4d31`.
- Sol can update now (11:50 log §g, step 1): the L4 sheets, the bench and Qwen3-8B.
- **Not the B1 resubmits** (§5 below).

## 2. The stricter path, written into B1's rule log before any result was read

**The check Ritik asked for first** (the runs files, numbers only): the first engine gave every run the full
32,768-token budget, prompt and reply.
- Each run's budget is `CAP_TOTAL − prompt tokens` (`finetune/continuation.py`). The old `Batched` generated
  `max(max_tokens)` new tokens. Its `reserve=16000` only decided which requests could share a batch.
- In the runs: 41 of 174 runs went past 16,000 tokens, 8 past 24,000, the longest 32,127. The one run that hit the
  cap ended at prompt 641 + reply 32,127 = 32,768.
- No answer: **1 of 174**, that run (`hit the token cap`).

**The deviation**, appended as §4 to `archive/sessions/2026-10-30/2026-10-30_1715_A_b1-generation-rule.md`:
1. **Every configuration is rerun on the fixed engine under its own name:** `prov-a1-v2`,
   `prov-deployable-a0.25-v2`, `prov-oracle-a0.5-v2`. All 210 alpha = 1 runs are included.
2. **The primary comparison uses those runs only;** §1–§2 of the rule are unchanged, with `prov-a1-v2` as alpha = 1.
3. **The robustness check, labelled so:** the first engine's alpha = 1 runs against `prov-a1-v2` on following,
   acceptance and no-hint accuracy. Old minus new, paired by question; expected no difference.
4. **Set aside:** the first engine's deployable runs (counts only).
5. **The gate** (§3 below).

The deviation also says what has been looked at so far:
- run and token counts;
- times;
- finish reasons;
- the no-answer count.

No letter has been compared with a hint. The supplement lists it among the curated deviations, checked against the
log's text.

**The code** (`finetune/gpu/provenance_job.py`):
- `configs()` adds the engine's tag: `ENGINE_TAG = "v2"`, so names are `prov-a1-v2` etc.; `tag=None` gives the
  first engine's plain names.
  - The file names can't collide: `runs_files("prov-a1")` globs `eval_prov-a1_p*of*`, which `eval_prov-a1-v2_…`
    doesn't match.
  - Records carry `engine_tag` and the batching settings.
- `report()` reads the `-v2` configurations only, against `prov-a1-v2`. Beside them:
  - `robustness_engine_check`: the three measures, old, new and old − new, with its label;
  - `set_aside`: the first engine's other runs, by count.
- B2's gate versions, when they run, are `-v2` too.

**Tests:** the generate/report test uses the `-v2` file names and fields. The report test has old and new systems
and checks the split, the label and the set-aside counts. The alpha-rule test checks the names.

## 3. The bench is the gate

- **`GATE = 1.5`.** `bench_gate(res)` takes the bench's measured tokens/s, after over before, at alpha 1 and at the
  deployable alpha. It passes when the smaller ratio is at least 1.5.
- **`plan` prints no lines unless the gate passed.** Without a bench it stops ("the bench is the gate"). With a
  failed gate it stops with "stop and report before any resubmit". `--no-gate` is a preview only.
- **The bench run from `c6f4d31` already writes everything the gate needs,** since `plan` recomputes it from
  bench.json's `engines`. The bench in this commit also prints it in its line.
- Tested: no bench → stop; 2.50x and 1.48x → stop; 1.50x → lines; one alpha only → not passed.

**What the gate measures:** the bench's before/after runs, 16 set A runs capped at 1,024 tokens. These show the
batching (the old scheduler's batches of ~1–2 against batches of up to 8) more than the long-reply effect. The
full-length gain is in the bench's projection, which `plan` uses as its rate.

## 4. The plan, with the alpha = 1 rerun (a preview; the real one after the bench)

A preview on the Mac's copies, at the projected 60 tokens/s, without the gate (`--no-gate`):
- **630 runs**: 3 configurations × 210, alpha = 1 rerun included;
- mean reply 12,175 tokens (the finished runs' mean × 1.15);
- **10 parts of 63 runs, ~3.7 h each** (submit.sh's limit 5:00);
- **~37 GPU-h** (against ~27 without the alpha = 1 rerun).

The real lines come from `plan` on Sol, which needs three things first:
- this commit pulled;
- the bench done;
- 3/4 and 4/4 stopped.

`plan` then uses the bench's rate and its gate.

## 5. Sol: the order changes in one place

- **Steps 1–4 of the 11:50 log stand,** from `c6f4d31`: the update, L4's sheets, the bench, Qwen3-8B.
- **Don't submit `provenance_gen` from `c6f4d31`.** It has the fixed engine but not the `-v2` names, so its runs
  would go into the first engine's files.
- **Before step 5, pull this commit:**
  ```bash
  cd /scratch/ragarw68/cse598-cot-faithfulness
  git pull --ff-only origin trackA-nosol && git log -1 --format='%h %s' | cut -c1-80   # expect this commit
  ```
- **Then step 5:**
  ```bash
  "$TRACKA_PY" cot-disclosure/finetune/gpu/provenance_job.py plan --out /scratch/ragarw68/trackA --alpha-from $F
  ```
  If the gate fails, it prints the ratios and stops. Then send them to me; nothing is submitted.

## 6. Gate 3's story line

FINDINGS story item 6 and the root README now say: **no trained version so far beats the one-line instruction on
following**. Each minus prompt_only, not pre-registered:
- LoRA +3 [−1, +8];
- tags +7 [+1, +14];
- LoRA + tags +10 [+4, +16], interim.

## 7. Checks and commit

Listed in the commit message: the tests, the link check, the supplement, the Gantt. Committed as Ritik. **Pushing
waits for Ritik's OK;** Sol's B1 resubmits need it.
