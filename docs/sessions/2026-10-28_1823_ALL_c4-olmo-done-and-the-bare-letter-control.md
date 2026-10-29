# Session log: C4 and Olmo 3 7B Think done, the bare letter is about tool use, the training baseline job, labeling by rule (2026-10-28 18:23 MST)

Project: CSE 598 Group 10. Track A trains Olmo 3 7B Think on Sol to stop hiding hint-following; Track
B measures hint-following across open models and channels; Track C runs a solver/reviewer/checker
team on Track B's cases. This log covers the end of the Voyager runs and Ritik's evening message:
the training baseline, the bare-letter control and labeling by rule.

## 1. Header

- **Time:** 2026-10-28 18:23 MST. **Track:** all. **By:** Ritik (Track A), Arsha (Track B), Shrey (Track C).
- **Branch:** `trackA-nosol` (= `main`); `trackB-main` and `trackC-main` are moved to this log's
  commit.
- **Input:** Ritik's evening message: three points, his Sol output (the SubmitLine of the two failed
  jobs; the three new job numbers).

## 2. What ran

- **Voyager, finished:**
  - C4 ended 17:51: 318 of 318 cases, 0 errors.
  - Olmo 3 7B Think ended 17:52: 805 of 805 jobs, 0 not run, 0 API errors.
  - Both power guards ended (17:52, 17:53). Nothing of ours runs on the Mac now.
  - The watcher's exit code 1 was its last `ls logs/voyager_halted`: no halt file, so no halt.
- **Mac, no calls:**
  - the C4 summary;
  - the Track B report with all three models (`--export --by-set`);
  - the steered exports for Instruct and Olmo;
  - the label kit, rebuilt with the bare-reply rule;
  - `export_summaries.py`;
  - the F17 bootstrap;
  - `val_loss.py --dry-run` with the real tokenizer;
  - the tests.
- **Sol (Ritik, this afternoon):**
  - pushed and rsynced;
  - lora_tags **66862721** (limit 5:00), lora_attn3 **66862726** (4:00), vllm_check
    **66862780** (1:30), all pending (Priority). 630 of 960 GPU-minutes requested.
  - SubmitLine of 66759772 and 66759822: `sbatch -A … -t … --dependency=afterany:… …/train.sbatch`
    with nothing after it. The version was missing from the submitted line: **cause 1 confirmed**.

## 3. Results

**Track B, Olmo 3 7B Think** (FINDINGS F17; pinned format, `tool_injected` for the tool; 810 runs,
10 no answer):

| channel | following | above the no-hint baseline | final names the hint, when following | bare final (all runs) |
|---|---|---|---|---|
| user | 13 of 162 [5, 13%] | +6 [+2, +10] | 2 of 13 | 24 of 162 |
| tool, pasted | 64 of 160 [33, 48%] | +38 [+27, +48] | 33 of 64 | 30 of 162 |
| tool, injected | 46 of 157 [23, 37%] | +27 [+17, +37] | 11 of 46 | **115 of 162** |
| system note | 34 of 159 [16, 28%] | +19 [+10, +28] | 10 of 34 | **85 of 162** |

- **Gate 2 is clear:** pasted +32 [+22, +42], injected +21 [+13, +30]. At the 16,000 cut: +35
  [+22, +48] (40 q) and +18 [+9, +27] (49 q).
  - The cut takes 173 of 810 runs, 72 of them pasted (median pasted run 15,472 tokens).
  - Gate 2 is now clear for all three Voyager models.
- **By set:** MMLU-Pro pasted 59 of 89 and injected 44 of 87; puzzles 5 of 71 and 2 of 70.
- **Bare answers follow the system turn:** no hint 19 of 162. Our system note replaces Olmo's
  default system prompt, and `tool_injected` uses the function-calling one.
  - So injected − pasted naming, −28 [−44, −11] over 31 q (unpaired, F15's method), is not about
    the tool. The system note, with no tool, is named in 10 of 34.

**Track C, C4** (FINDINGS F18; 53 items × 2 teams × 3 repeats):
- **Shipped wrong on bad lookups: 0 of 75**, in every variant. The checker flagged 73 of 75 bad
  lookups; the other 2 had right solver answers.
- **Checker false alarms:** good lookups 7 of 80, floor 12 of 155, good − floor −4 [−11, +4]
  (27 items). All are on steered MMLU-Pro items: the floor is 18% there and 0% on matched items.
- **The reviewer alone on the 73 wrong answers after bad lookups,** minus answer only, paired by
  item over 25 items:

  | variant | Olmo 3 32B | − answer only | Qwen3 30B Instruct | − answer only |
  |---|---|---|---|---|
  | answer only | 59 of 73 | — | 62 of 73 | — |
  | + explanation | 61 of 73 | +3 [−5, +12] | 62 of 73 | +0 [−7, +8] |
  | + private reasoning | **6 of 73** | **−73 [−86, −58]** | 66 of 73 | +5 [−6, +19] |
  | + tool log | **3 of 73** | **−77 [−91, −61]** | 56 of 73 | −8 [−25, +9] |

  - With the private reasoning or the tool log, Olmo keeps the wrong letter (66 and 70 of 73), and
    its reply names the answer key (59 and 66 of 75; 0 of 75 with the answer only).
  - On good lookups, Olmo keeps the right answer 84 of 84 (vs 67 of 84): +20 [+8, +35].
- **By kind × set** (Olmo, private − answer only): matched puzzles −77 [−90, −62] (15 items);
  steered MMLU-Pro −58 [−88, −25] (8); matched MMLU-Pro 6 of 6 → 0 of 6, too few (2).
- **The solver's final answer** is bare in 151 of 159 tool-team cases, so "+ explanation" adds
  little.

**Ritik's point 2: is the bare letter about the hint or about tool use?** It is about tool use (no
new calls):

| C4 solver's final answer | bare (≤30 characters) | median characters | names the tool |
|---|---|---|---|
| after a good lookup | 80 of 84 [88, 98%] | 11 | 2 of 84 |
| after a bad lookup | 71 of 75 [87, 98%] | 11 | 4 of 75 |
| no tool, same items | 2 of 159 [0, 4%] | 1,979 | 3 of 159 |

- Good − bad: **+1 [−7, +9]** over 53 items, unpaired (each item's lookup is fixed).
- Against no tool, paired by item: good +93 [+86, +99] (28 items), bad +95 [+88, +100] (25 items).
- The same holds on the puzzles and on MMLU-Pro.
- In Track B, Qwen3 Thinking's real-call runs without a call are bare in 56 of 108: 52 of 68 on the
  puzzles, 4 of 40 on MMLU-Pro. With no hint, a user hint, a pasted hint or a system note: 0 of 162.
- **F15 now reads:** after a tool call, the final answer stops explaining where its answer came
  from, whether the tool was right or wrong. That is broader than hints. Which of the two matters
  more, the declared tool or the call, is tentative.

**Ritik's point 3: labeling.**
- The queue (L3, 101 rows) goes first.
- In the Track B batch, bare replies are `no_mention` by rule (`prelabeled.csv`), with a blind 10%
  spot check per group, rounded up.

| group | runs | bare, by rule | with text | spot check | rows to label |
|---|---|---|---|---|---|
| 1 Qwen3 Thinking (F15) | 113 | 51 | 62 | 6 | **68** (rows 1–68) |
| 2 Qwen3 Instruct (F16) | 182 | 111 | 71 | 12 | **83** (rows 69–151) |
| total | 295 | 162 | 133 | 18 | **151** |

**Ritik's point 1: the training baseline (S7).**
- `finetune/val_loss.py`: base plus both epochs of lora and tags on the 156 validation examples,
  each loss split by part. Taught = opener + hint-check sentences + final answer, in hinted
  examples.
- Dry run with the real tokenizer:

  | part | tokens | share |
  |---|---|---|
  | opener | 2,569 | 0.2% |
  | hint-check sentences | 27,976 | 2.2% |
  | final, hinted | 49,465 | 4.0% |
  | rest, hinted | 1,023,147 | 82.3% |
  | final, no hint | 7,088 | 0.6% |
  | rest, no hint | 133,447 | 10.7% |
  | **taught** | **80,010** | **6.4%** |

- The average loss is 94% tokens training does not target.
- Estimate: 25–45 GPU minutes, inferred from lora's training rate, not measured. Limit 1:00, which
  brings the total to 690 of 960.

## 4. Changes

- `agents/run_team.py`:
  - `reviewer_vs_answer_only` (each variant minus answer only, paired by item);
  - `solver_replies` (bare, median length, naming the tool, per team and lookup; good − bad
    unpaired, each − notool paired);
  - the reviewer alone keeping the wrong letter, and its reply naming the tool;
  - all of it in `--table` and in each kind / kind × set split.
- `progress/trackB_report.py`: `final_chars` in the per-run flags (a number); "bare final" per
  channel, with no hint, and with / without a call.
- `tools/label_kit.py`: the bare-reply rule, `prelabeled.csv`, the spot check, and kappa's
  agreement with the rule.
- `finetune/val_loss.py`, `finetune/gpu/sol/val_loss.sbatch`, a `run.sh` step, and `submit.sh`
  (val_loss takes versions only and may wait for train jobs).
- Tests: 12 more than this morning: Track C 2, the Track B report 1, val_loss 4 (a new file), and 5
  from the GPU kit's job lists (the new step and submission checks). The label kit's test is
  extended. 414 pass.
- Exported (numbers only):
  - `results/summaries/trackB/*` (now with `final_chars`);
  - `trackC/team_c4_summary.json` (new);
  - `trackC/team_smoke_olmo32b_summary.json` (its C5 block, regenerated at 00:34 but not exported
    then);
  - `voyager_canary.jsonl` (the night's canaries).
- `steered_cases.jsonl` (gitignored): Instruct has 48 steered (all 24 puzzles, 24 MMLU-Pro) and 6
  matched. Olmo has 21 steered, 31 matched and 2 other.
- Docs:
  - FINDINGS: F15 reworded, F16 a line, F17 and F18 new, a training-loss limitation.
  - PLAN: the batch-2 resubmission, S7, Track B/C state, labeling order.
  - TODO: A13, A15, A18 new, B7–B14, C4, C5, L3, L5.
  - Handoffs B and C, the labeling guide, RUNBOOK §14 and §15.

The F17 contrast's interval (as F15's: a bootstrap over the union of questions, seed 20261028,
10,000 resamples), from `cot-disclosure/`:
```bash
../.venv/bin/python -c "
import sys,random,collections; sys.path.insert(0,'progress')
import trackB_report as tr
rows=[f for f in tr.load_flags() if f['followed'] and f['model']=='olmo3-7b-think' and f['condition'] in ('tool_injected','tool_pasted')]
g={c:collections.defaultdict(list) for c in ('tool_injected','tool_pasted')}
for f in rows: g[f['condition']][f['item_id']].append(int(bool(f['mention_final'])))
qs=sorted(set(g['tool_injected'])|set(g['tool_pasted']))
rate=lambda d,ids:(lambda k,n:k/n if n else None)(sum(sum(d[i]) for i in ids if i in d),sum(len(d[i]) for i in ids if i in d))
rng=random.Random(20261028); ds=[]
for _ in range(10000):
    s=[rng.choice(qs) for _ in qs]; a,b=rate(g['tool_injected'],s),rate(g['tool_pasted'],s)
    if a is not None and b is not None: ds.append(a-b)
ds.sort(); print(rate(g['tool_injected'],qs)-rate(g['tool_pasted'],qs), ds[250], ds[9749])"
```

## 5. For review

1. **F15 changed meaning a second time today.**
   - At 12:20 the reading was "after a real call, the answer stops explaining". C4's good lookups
     show that this is not about the hint: the reply is just as bare when the tool returns the key.
   - Track B's no-call runs show that on the puzzles, declaring the tool alone is enough (52 of 68
     bare).
   - So the −86-point naming contrast is mostly a property of tool use: a bare answer can't name
     anything. The claim is now about tool use in general.
2. **The control isn't identical to Track B.** C4 forces the first call; Track B leaves it to the
   model. C4's 53 items are Qwen3 Thinking's steered and matched cases, not all 54 questions. Good
   and bad lookups fall on different items (unpaired).
3. **Olmo's system condition differs in two ways.** Our system note *replaces* its default system
   prompt, so "system" for Olmo changes both the hint and the identity prompt. The pinned format
   does this by design (T2). That is why F17 compares the system note with the injected tool, not
   with the pasted block.
4. **F18 rests on one reviewer of each family and one reviewer prompt.** "Keeps the wrong letter
   and names the key" may be reasonable deference to an answer key (as in F16). The claim is only
   that this reviewer's independent check disappears when it sees the source. The naming counts are
   keywords.
5. **The checker's catches depend on the model knowing better without the tool.** That held on
   73 of 75. On the steered (MMLU-Pro) items its floor is already 18% [7, 30].
6. **The labeling rule leaves some private reasoning unlabeled.** 45 of Thinking's bare real-call
   runs (51 minus the 6 spot checks) are out of the sheets. Their private reasoning, the "names the
   tool in 54 of 54" claim, stays a keyword count. If you want it hand-labeled, that is 45 more rows,
   private reasoning only. Your call.
7. **The S7 estimate is inferred** from lora's training time (3.9–7.8 minutes per pass), not
   measured; the job records its seconds. The hint-check part is a keyword rule. The fork widened
   it beyond detect.py: the hint wording's own source words, and "suggest" for the user channel,
   because the user openers say "the suggestion".
8. **Instruct's export marks all 24 puzzles as steered.** If Track C ever runs on Instruct's cases,
   its matched set is only 6 MMLU-Pro items.
9. **Earlier estimates ran early.** At 12:20 I gave "around 17:00" for both runs; they ended at
   17:51 and 17:52. Olmo ran at about 62 jobs an hour after 11:56, not 74.

## 6. Next

- **Ritik, Mac:**
  - `git fetch origin && git log --oneline main..origin/main` must print nothing;
  - `git push origin main trackA-nosol trackB-main trackC-main`;
  - `git ls-files | rsync -av --files-from=- ./ ragarw68@login.sol.rc.asu.edu:/scratch/ragarw68/cse598-cot-faithfulness/`.
- **Ritik, Sol:**
  - Submit S7: `cot-disclosure/finetune/gpu/sol/submit.sh val_loss --estimate 0.75
    --dependency=afterany:66862721:66862726 -- lora tags` (limit 1:00; 690 of 960).
  - To include lora_tags and lora_attn3 as well: `--estimate 1.25 … -- lora tags lora_tags
    lora_attn3` (limit 2:00; 750 of 960).
  - After vllm_check passes: Qwen3-8B and batch 3, as in the 12:20 log.
- **Raters:** L3 first (101 rows), then the Track B batch (151 rows). A second rater from Shrey or
  Arsha.
- **Not decided:** what Track C runs next (Instruct's or Olmo's cases, other reviewers). No
  Voyager work is queued.
