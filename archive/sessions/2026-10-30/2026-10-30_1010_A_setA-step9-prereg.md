# Session log: set A's Step 9 pre-registered: do F12's three heads separate followed from resisted runs? (2026-10-30 10:10 MST)

Project: CSE 598 Group 10, Track A. Set A's Step 9 (Sol 66953968, 201 runs) is back as `step9_attention.json`, and
it hasn't been read. This log fixes its rule before the per-run numbers it needs are on the Mac. The rule is Ritik's
suggestion (Oct 30, 10:00). **By:** Ritik.

## 1. The question

F12 found, on Test 2's questions, that three heads in the readout layers look at the hint more when the model
follows it: L19H31, L23H17 and L15H31. Do the same three heads, fixed in advance, do it on set A's 16 questions,
which weren't used to find them?

## 2. The rule

- **Measure:** at the answer position, per run, the mean over the three heads of the hint span's attention mass
  minus the control span's (a question-stem span as long as the hint).
- **Comparison:** followed runs minus resisted runs, over all channels, paired by question, with a 95% bootstrap
  clustered by question. This is `attn_to_hint.fixed_heads`, which uses Step 9's own `diff()`.
- **Reading:**
  - **replicates:** the interval lies above 0;
  - **reversed:** it lies below 0;
  - **doesn't replicate:** it includes 0;
  - **too few questions:** fewer than 5 questions have both followed and resisted runs.
- **Reported beside it, no decision:**
  - the hint's mass alone (not minus control);
  - each channel;
  - each head.
- **Not used:** the follow-up's own "top heads", which are re-ranked on set A's attention. The heads stay F12's.

**The reference, Test 2** (the same function on Test 2's `step9_reduced.npz`, computed for this log): +0.084
[+0.062, +0.105], 105 followed and 94 resisted runs, 16 questions.
- Per head: L19H31 +0.115, L23H17 +0.086, L15H31 +0.051 (F12's).
- By channel:
  - inserted +0.097 [+0.065, +0.121];
  - pasted +0.097 [+0.059, +0.139];
  - **inserted + declared +0.028 [−0.002, +0.058]**: no difference, as F12 said.

**What to expect, said before the data.** Set A has two channels: pasted (30 followed, 70 resisted) and inserted +
declared (26 followed, 75 resisted). On Test 2, inserted + declared showed no difference, so the pooled result here
may be weaker than Test 2's. The rule reads the pooled interval either way.

## 3. What it needs from Sol (Ritik)

The per-run masses are in set A's saved Step 9 runs on Sol. The follow-up reduces them to one numbers-only file
(`step9_reduced.npz`, a few MB) before anything else. Its takeover-aligned part matches runs against Test 2's Step
3 rows, so it skips set A's runs and isn't read here.

```bash
# Sol, login node (no GPU, no model), from the clone after `source cot-disclosure/finetune/gpu/sol/env.sh`:
"$TRACKA_PY" cot-disclosure/finetune/look/attn_to_hint.py --followup --out /scratch/ragarw68/trackA/setA
# (after the next pull, the same file alone: ... attn_to_hint.py --reduce-only --out /scratch/ragarw68/trackA/setA)

# Mac, from cot-disclosure/:
rsync -av ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/trackA/setA/step9/step9_reduced.npz results/trackA/setA/
../.venv/bin/python finetune/look/attn_to_hint.py --fixed-heads results/trackA/setA/step9_reduced.npz
```

Then the reading, in its own session log.

## 4. Code

- `attn_to_hint.py`:
  - `F12_HEADS`;
  - `fixed_heads()`;
  - `--fixed-heads NPZ`, which writes `step9_fixed_heads.json` beside the file;
  - `--reduce-only`, which writes the reduced file and stops.
- A CPU test: a planted difference reads "replicates", none reads "doesn't replicate".
- On Test 2's file it reproduces F12's per-head numbers.
