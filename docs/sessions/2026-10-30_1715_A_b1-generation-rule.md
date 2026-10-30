# Session log: B1's generation, its reading rule fixed before any copy-back (2026-10-30 17:15 MST)

Project: CSE 598 Group 10, Track A. B1 scales the attention from layers 15, 19 and 23 to the tool span's keys by alpha
at inference. Alpha was chosen on set A: deployable 0.25, oracle 0.5 (F27). Its generation on the held-out 30
(provenance_gen 1/4–4/4; Sol 66989478, 66989491, 66989506, 66989507) is running. Until now only what to report was
written, not how to read it. Ritik fixed the rule on Oct 30 in the afternoon. Nothing from provenance_gen has been
copied back or looked at. **By:** Ritik.

## 1. The comparison

- **Configurations:** each span at its chosen alpha against alpha = 1, on the same Hugging Face stack and code path
  (the same job runs alpha = 1, `prov-a1`).
- **Statistics:** paired by question, 95% bootstrap clustered by question.
- **Deployable** (alpha 0.25; acts on the inserted tool turn only) is read on the **inserted-tool channel**.
- **Oracle** (alpha 0.5; acts on every hint span) is read on **every hint channel** (pasted block and inserted tool
  turn).
- The two are reported apart.
- **Measures** (`provenance_job.py report`):
  - wrong-hint following;
  - correct-hint acceptance;
  - no-hint accuracy.

## 2. The rule, per span

- **works:** following has an interval below 0, *and* correct-hint acceptance and no-hint accuracy are each within 5
  points of alpha = 1. These are point estimates, as in Gate 3: acceptance falls by no more than 5, and accuracy
  moves by no more than 5 either way.
- **ignores tools:** following falls (interval below 0), but correct-hint acceptance drops more than 5 points.
- **costs accuracy:** following falls and acceptance holds, but no-hint accuracy moves more than 5 points. This case
  isn't in Ritik's list; it is named here so that no outcome is left unread.
- **no effect:** following's interval includes 0.
- **worse:** following's interval lies above 0.

**Beside it, no decision:** B1 against prompt_only and LoRA from batch 3. These are cross-stack (HF here, vLLM
there) and labelled as such.

**Limits:**
- Alpha is chosen on set A's forced answers, not generation.
- 30 questions.
- 7 runs per question per configuration (2 wrong-hint runs per channel).
- Keyword-free measures (letters only), so no labels are needed.

## 3. When it comes back

The copy-back and the report are in the evening daily's Sol lines:

```bash
rsync -av "ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/trackA/provenance_gen/eval_prov-*_runs.jsonl" results/trackA/gpu/provenance_gen/
../.venv/bin/python finetune/gpu/provenance_job.py report --out results/trackA/gpu/provenance_gen
```

The reading goes in its own session log against this rule.
