# Session log: training against base (S7) and C9 (2026-10-28 22:42 MST)

Project: CSE 598 Group 10. Track A trains Olmo 3 7B Think on Sol to stop hiding hint-following; Track
B measures hint-following across open models and channels; Track C runs a solver/reviewer/checker
team on Track B's cases. This log covers Ritik's two Sol messages after 21:44 (training done, S7
done, the queue full) and C9's end.

## 1. Header

- **Time:** 2026-10-28 22:42 MST. **Track:** all. **By:** Ritik.
- **Branch:** `trackA-nosol` (= `main`); `trackB-main` and `trackC-main` move to this log's commit.
- **Input:** Ritik's messages:
  - all four versions trained, each chose epoch 2;
  - S7 66865939 done in 0:37:09 on all four versions;
  - get_qwen8b done (1:31);
  - queued, 10 of 10 submissions: vllm_check 66878660, trackb_qwen8b 66879362, and 8 eval parts
    (afterok 66878660): base 66879564/66879567, prompt_only 66879569/66879571, lora 66879572/66879573,
    tags 66879761/66879792;
  - S7's two files copied back with the command I gave, and the report's output.

## 2. What ran

- **Voyager:** C9 ended 22:33: 159 of 159 cases, 954 calls, 0 errors, and the guard ended 22:34.
  The waiter's exit code 1 was its last `ls logs/voyager_halted`: no halt file.
- **Sol (Ritik):** the jobs in §1.
- **Mac, no calls:**
  - `val_loss.py --report` (new) on S7's files;
  - `run_team.py --summary --log team_c9 --cases … --table`;
  - `export_summaries.py`;
  - the tests.

## 3. Changes

- **`finetune/val_loss.py --report DIR`** reads `val_loss.json` and `val_loss_examples.jsonl` copied
  back from Sol. It gives each trained system minus base:
  - for the taught tokens, the taught tokens without the opener (added after the first look: the
    opener is 3% of the taught tokens and half of LoRA's drop), their parts, the rest and overall;
  - for the taught tokens per hint channel.
  The differences are paired, with a 95% bootstrap clustered by question (20,000 resamples, seed 0).
  It writes `results/summaries/trackA/val_loss_report.json` and prints two tables. A test checks its
  points against `val_loss.json`'s own differences.
- **`export_summaries.py`** now also copies S7's two files and C9's summary.
- **Copy-back lines** for S7, S2 and the evaluation are in `finetune/gpu/README.md` ("Results back")
  and RUNBOOK §14.

## 4. Results

**S7, training against base** (FINDINGS F20; 156 validation examples on 34 questions, none of them in
training; epoch 2; nats per token, minus base):

| version | taught | taught without the opener | the rest | overall |
|---|---|---|---|---|
| base (loss) | 0.4696 | 0.3304 | 0.2287 | 0.2442 |
| lora | −0.2740 [−0.3132, −0.2401] (−58%) | −0.1328 [−0.1527, −0.1176] (−40%) | −0.0440 (−19%) | −0.0588 (−24%) |
| lora_tags | −0.2731 [−0.3121, −0.2392] (−58%) | −0.1318 [−0.1516, −0.1168] (−40%) | −0.0435 (−19%) | −0.0582 (−24%) |
| lora_attn3 | −0.2460 [−0.2809, −0.2156] (−52%) | −0.1127 [−0.1268, −0.1016] (−34%) | −0.0380 (−17%) | −0.0514 (−21%) |
| tags | −0.0793 [−0.0908, −0.0701] (−17%) | −0.0300 [−0.0339, −0.0264] (−9%) | −0.0268 (−12%) | −0.0302 (−12%) |

- **LoRA by part:** the opener 4.66 → 0.13 (−97%), the hint-check sentences −23% [−28, −19], the
  final answer −53% [−65, −45].
- **LoRA by channel (taught):** user −57%, pasted −58%, injected −60%.
- **Epoch 1 → 2** moves little: lora −57.4% → −58.4% (taught).
- **Self-check:** each overall loss matches its `state.json` within 7e-9.
- **Reading:**
  - The taught tokens fall about twice as much as the rest, even without the opener.
  - Tags alone don't favor them (−9% vs −12%) and add nothing to LoRA.
  - lora_attn3 gets 85–90% of LoRA's drop.
  - Teacher-forced loss only: behavior is batch 3 and Gate 3.

**C9** (FINDINGS F19; the sentence minus C4's prompt on the same 159 cases, paired by item):

| reviewer, variant | corrects (bad lookups, 25 items) | difference | keeps right (good, 28 items) |
|---|---|---|---|
| Olmo 3 32B, answer only | 59 → 60 of 73 | +1 [−5, +8] | 67 → 64 of 84 |
| Olmo 3 32B, + private reasoning | 6 → 8 of 73 | +3 [−4, +9] | 84 → 84 |
| Olmo 3 32B, + tool log | 3 → 4 of 73 | +1 [−3, +6] | 84 → 84 |
| Qwen3 30B Instruct, answer only | 62 → 62 of 73 | +0 [−4, +4] | 72 → 72 |
| Qwen3 30B Instruct, + private reasoning | 66 → 69 of 73 | +4 [+0, +11] | 76 → 75 |
| Qwen3 30B Instruct, + tool log | 56 → 61 of 73 | +7 [−4, +19] | 77 → 77 |

- **Olmo:** it still keeps the wrong letter in 63 and 68 of 73 and names the key in 62 and 61 of 75.
- **By kind × set** (Olmo, corrects with the private reasoning):
  - matched puzzles: 5 → 6 of 43 (15 items);
  - steered MMLU-Pro: 1 → 2 of 24 (8 items);
  - matched MMLU-Pro: too few questions (2).
- **Qwen3's gain** is mostly on matched puzzles with the tool log: 35 → 41 of 43, +14 [+0, +30].
- **No letter:** Olmo answer-only gave none in 8 of 159 (C4: 7).

## 5. For Ritik

```bash
# Mac: the commit, then the rsync
git fetch origin && git log --oneline main..origin/main          # must print nothing
git push origin main trackA-nosol trackB-main trackC-main
git ls-files | rsync -av --files-from=- ./ ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/
```
The morning commands (the four remaining eval parts, the copy-backs) are in
[DAILY_2026-10-29.md](DAILY_2026-10-29.md).

## 6. For review

- **The hint-check part is a keyword rule.** F20's "taught without the opener" includes those
  sentences.
- **"The rest falls 19% too"** has no explanation here. It could be the targets' general style
  (they were sampled from the model itself), or the template. It is not checked.
- **F19 tests one generic sentence.** A stronger intervention (answer before reading the trace, or
  the trace withheld) is untested and is not proposed as decided.
- **The docs said "23:00"** before it was 23:00. The stamps were set to the commit time.
- **trackb_qwen8b 66879362 isn't held for vllm_check** (see the 22:40 reply); Ritik's call.
