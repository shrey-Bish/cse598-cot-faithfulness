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

## 4. Deviation (Oct 31, 12:40, before any B1 result was read)

Ritik's decision, on the 11:50 log of Oct 31 (`2026-10-31_1150_ALL_b1-engine-and-sol-update.md`).

The first generation engine was slow, at 21–35 tokens/s; that log has the cause. The fixed engine:
- batches in arrival order;
- sizes each batch so its key/value cache fits even if every reply runs to the full budget;
- lets finished rows leave every 512 tokens;
- uses expandable memory segments.

Each step is the same decode as before. To keep alpha = 1 and the chosen alphas on one engine without arguing that
the two engines are equivalent, the stricter path:

1. **All 210 alpha = 1 runs are rerun on the fixed engine.** Each configuration gets a new name, so old and new
   never share a file:
   - `prov-a1-v2`;
   - `prov-deployable-a0.25-v2`;
   - `prov-oracle-a0.5-v2`.

   Files are `eval_<name>_p<k>of<n>_runs.jsonl`, and records carry `engine_tag: v2` and the batching settings.
2. **The primary comparison uses the fixed engine's runs only, for every configuration.** §1–§2 apply unchanged,
   with `prov-a1-v2` as alpha = 1 (`provenance_job.py report`; its `base` is `prov-a1-v2`).
3. **The robustness check, labelled so, not this rule:** the first engine's alpha = 1 runs (`prov-a1`) against
   `prov-a1-v2`.
   - Measures: wrong-hint following, correct-hint acceptance and no-hint accuracy.
   - Old minus new, paired by question on the questions both have, 95% bootstrap clustered by question.
   - Expected: no difference.
   - In `report` as `robustness_engine_check`.
4. **Set aside, unused:** the first engine's deployable runs (2 at Oct 31 10:40, plus whatever parts 3/4 and 4/4
   finish before their limit). `report` gives their counts only (`set_aside`).
5. **The gate:** no resubmit unless the bench (`provenance_bench`) shows the fixed engine at **at least 1.5× the old
   engine's tokens/s**, at alpha 1 and at the deployable alpha (the smaller ratio counts). Otherwise stop and
   report. `provenance_job.py plan` prints no lines unless the gate passed.

**Checked before this was written** (the runs files, numbers only):
- **The full budget:** the first engine gave every run the full budget of 32,768 tokens, prompt and reply. Its
  16,000-token "reserve" only decided which runs could share a batch, not how many tokens a run got:
  - 41 of 174 runs went past 16,000 tokens, 8 past 24,000, the longest 32,127;
  - the one run that hit the cap ended at prompt 641 + reply 32,127 = 32,768.
- **Its no-answer count:** 1 of 174, that run (`hit the token cap`).
- **What has been looked at in B1's runs files so far:**
  - run counts;
  - prompt and reply token counts;
  - end times and durations;
  - finish reasons;
  - the no-answer count.

  No letter has been compared with a hint, and no measure of §1–§2 has been computed.

## 5. The first engine's runs, counted at the end of 3/4 and 4/4 (Oct 31, 16:40)

Parts 3/4 and 4/4 (66989506, 66989507) ended in TIMEOUT at 6:00, so the first engine's runs are now final. They
were counted from run IDs and status only. No other field was looked at, and nothing in §4's list was added to.

| configuration | p1 | p2 | p3 | p4 | runs | use (§4) |
|---|---|---|---|---|---|---|
| `prov-a1` | 56 | 23 | 49 | 49 | **177** | the robustness check's old side (item 3) |
| `prov-deployable-a0.25` | 2 | — | 12 | 3 | **17** | set aside, counts only (item 4) |
| `prov-oracle-a0.5` | — | — | — | — | 0 | — |

- Every record has status `ok` and none has an `engine_tag`, so all of them are the first engine's.
- The budget check above used the 10:40 copy: 174 runs, which were 172 at alpha = 1 (4/4 then had 44) and 2
  deployable. Since then, on the same engine: 5 more alpha = 1 runs (4/4) and 15 deployable runs (3/4 and 4/4).
  `report` takes all of the first engine's `prov-a1` files, 177 runs.
