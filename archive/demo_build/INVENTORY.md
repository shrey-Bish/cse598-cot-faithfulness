# The demo's inventory (phase 1 of [DEMO_SPEC](DEMO_SPEC.md))

By: Ritik, Nov 20. Where every method fact and every set of recorded runs for the new demo lives, what is only on Sol,
and what is missing. Numbers, ids and paths only: no model text, no question text. `cd/` = `cot-disclosure/`; **gi** =
gitignored produced data, on this Mac only. Line numbers as found on Nov 20. Nothing was read on Sol: its paths come
from the repo's own records (RUNBOOK, SOL_SETUP, SOL_ARSHA, job code, handoff manifests) and are unchecked there.

## 0. Not on this Mac

- `~/Downloads/DEMO_SPEC.md` and `~/Downloads/demo_template/` (with `TEMPLATE_GUIDE.md`): neither is anywhere on this
  Mac (Downloads, Desktop, Documents searched). The brief was saved from the paste as [DEMO_SPEC.md](DEMO_SPEC.md);
  the template was not moved. Phase 2 needs it (`cd/tools/demo_template/`).

## 1. The short answer: what's rich, what's thin

**The map (part 1).**

| step | material | verdict |
|---|---|---|
| 1 Questions | all sets on the Mac, MMLU-Pro (no GPQA); seeds recorded for the 120 and the puzzles | rich |
| 2 The hint | every template in code, with line numbers; the exact prompts for the 30 (`heldout.jsonl`) | rich |
| 3 Models | 12 models with settings and where each ran | rich |
| 4 Running it | feeder, class limits, checksums, prereg ledger, Gantt input; **no project-wide GPU-hour total** | medium |
| 5 Architecture | 32 layers, 8 full (3, 7, …, 31), 24 sliding (4,096), heads, sizes | rich |
| 6 Patching | per-layer and per-head results, **per-question cut records** (numbers) for both sets and Qwen3-8B | rich |
| 7 Fine-tuning | configs, data counts, **real training examples on the Mac**; loss only per epoch (per-step logs on Sol) | rich, curve thin |
| 8 Training inside | swap rows for LoRA and consistency training (52 each) | rich |
| 9 Other fixes | instruction and label text, the dial's two measured settings | rich |
| 10 Review team | pipeline code, prompts, counts | rich |
| 11 Checking ourselves | 42-row prereg ledger, stats code, label agreement; **no contamination audit file** | rich, one gap |

**The bench (part 2).** Text of a run = prompt, private reasoning, tool call and reply, final answer.

| test | text on this Mac | only on Sol | without a copy, show |
|---|---|---|---|
| 1 Tool vs person | Qwen3 30B Thinking and Instruct, Olmo 3 7B Think (3 of 8 models, all three sources) | Qwen3-8B on/off, gpt-oss ×3, Gemma, Nemotron, Granite | those three models on the bench; the other five as the frozen result only |
| 2 Authority | all three models, all claims | — | complete |
| 3 Thinking on/off | none for one model toggled (22 Ollama pilot and 48 smoke runs only) | Qwen3-8B on/off (Ritik's account) | Qwen3 30B Thinking vs Instruct, labelled "two models, not a switch" |
| 4 The fixes | **no evaluation text** for any fix; hand-label sheets hold final answers (84 L6, 294 L4, 385 sample) | every E2 and held-out evaluation (Ritik's account) | outcome rows as bubbles (numbers on the Mac); L6's final answers for LoRA vs the instruction |
| 5 Review teams | complete: solver text, tool log, reviewer verdicts, checker | — | complete (no reviewer reasoning was ever stored) |
| 6 Inside the model | per-question cut records (numbers; no text needed) | Qwen3-8B source texts | the per-question patching view from numbers |

**My proposal:** keep tests 2, 5, 6 and the map whole; test 1 on three models now. Tests 3 and 4 need one copy from
Ritik's own account (§4): with it, both become complete; without it, they run on numbers and hand-label final answers.
A targeted copy is small: draw the questions on the Mac first (seeded), then fetch only those runs by run id with the
read-only stdin pattern (`cd/tools/l6_sheet.py --remote-script`; nothing written on Sol). Granite and Gemma's B20 runs
are on Arsha's account: hers to copy, never with her login.

## 2. The map: where each fact lives

**Step 1, the questions.**
- The 54 test questions (162 = 54 × 3): 30 MMLU-Pro (`cd/data/progress/mmlupro_30.jsonl`, tracked) + 24 generated
  puzzles (`tasks.make_items`, rng seeded `"{kind}-{level}-{seed}"`, seed 0). Ids and text: `cd/results/trackB/steered_cases.jsonl` (gi, 162 rows).
- The 30 held-out: `mmlupro_30.jsonl`; their 240 exact prompts (8 wordings): `cd/finetune/data/heldout.jsonl` (gi).
- The 120 fresh: `cd/data/progress/mmlupro_e2.jsonl` (tracked; 30 each of law, engineering, chemistry, physics), drawn by
  `cd/finetune/make_e2.py` (seed `e2-20261103`, excludes the 30, the pool and C15's items; sha256 recorded);
  prereg `archive/sessions/2026-11-03/2026-11-03_1130_A_e2-a39-prereg.md`.
- The 16 new (set A): `cd/results/trackA/setA/items.jsonl` (gi, 34 rows; 16 used in patching). The training pool:
  `cd/finetune/data/pool.jsonl` (gi, 1,600). Review teams' 100: `cd/results/trackC/c15_items.jsonl` (gi).
- Patching sets: `cd/results/trackA/gpu/a18/items.jsonl` (gi, 30); Qwen3-8B on MMLU-Pro 30 (`qwen8b_readout.json`).

**Step 2, the hint.** Builders `cd/tools/answer_key.py` (`build`, `TOOL_SPEC` :38–48, `tool_reply` :57–59,
`run_tool_loop` :122–148, `run_injected` :93–119) and `cd/experiments.py` (`CUE`, `STEPS`).
- User's guess: `experiments.py` `CUE`. Classmate and official manual: `cd/progress/run_b24.py:53–56`. My answer key:
  `answer_key.py:53`. Pasted output: `answer_key.py:37, 49–50`. Own tool call: `lookup_answer_key`, reply
  `{question_id, expected, source: "study guide v2"}`. Inserted turn: `answer_key.py:84–90`; Olmo's rendering
  `cd/finetune/templates/olmo3_think_tools.jinja`.
- Track A's held-out wordings (`user_turpin`, `user_professor`, `tool_progress`, `inserted_study_guide`,
  `inserted_database`, `inserted_new_tool`, …) and the training paraphrases: `cd/finetune/build_dataset.py` `WORDINGS`.
- Right hint for the fixes: the same wordings with the correct letter, `cd/finetune/eval.py:100–106` (`A39_WRONG` 6,
  `A39_CORRECT` 4, `A39_NOHINT` 2 jobs a question).

**Step 3, the models: 12** (8 answering + 4 reviewers; `docs/paper/REPORT.md:84–94`).
- Settings and servers: `cd/configs/models.yaml`, `trackB.yaml`; Qwen3-8B `cd/progress/sol_trackB.py:56`; gpt-oss
  `sol_b17.py:50`; Gemma, Nemotron, Granite `run_b20.py:81–107`; reviewers `cd/agents/run_team.py:146–153`, Granite 4.1
  and Mistral `cd/agents/sol_c13.py:44–57`.
- Where: Voyager (Qwen3 30B ×2, Olmo 3 7B Think, Olmo reviewers); Sol vLLM (Qwen3-8B, gpt-oss, B20's three, C13's two);
  Sol Hugging Face (Olmo training, evaluations, mechanism).
- Temperature 0.6 (Olmo, Qwen3), 1.0 (gpt-oss, B20's three).

**Step 4, running it.**
- Class limits: `cd/finetune/gpu/sol/accounts.conf:6–14`, `submit.sh:15–28` (960 running GPU-minutes, 10 jobs, 24 h).
- The feeder: `cd/tools/sol_feeder.py:1–117`; queue `cd/finetune/gpu/sol/queue_2026-11-04.txt`. GPU A100 80 GB
  (`results/trackA/gpu/val_loss.json`, gi).
- Run counts: 1,440 a system on the 120 (FINDINGS F41); 930 a system on the 30 (`eval.py` docstring); 600 a dial
  setting (`summaries/trackA/gpu/b1r2/provenance_gen_report.json`); B20 1,944 each for Gemma and Nemotron (REPORT:352).
- Reproducibility: seeds (`cd/progress/common.py:44`), pinned revisions and `snapshot.json`, Olmo's weights sha256
  (`cd/finetune/gpu/olmo3_7b_think_d97e442.json`), the template's `PINNED_SHA256` (`olmo_format.py:25`), A40's
  inputs sha256 (`cd/finetune/gpu/a40_inputs.json`).
- Timeline: `cd/tools/make_gantt.py:67–99, 550–565` reads `docs/status/TODO.md` (+ TODO_B, TODO_C); prereg dates
  `docs/paper/supplement/PREREGISTRATIONS.md:9–52`; the freeze tag.
- **Missing:** a project-wide job and GPU-hour total. Pieces only (B1 34.3 h, the 120's plan 53.2 h, A40 training
  2 h 44 min). A total needs `sacct` on Sol (read-only, Ritik's account) or show the pieces.

**Step 5, architecture (Olmo 3 7B Think).** 32 layers; full attention at 3, 7, 11, 15, 19, 23, 27, 31
(`cd/finetune/gpu/kit.py:182`; `summaries/trackA/step10_by_layer_type.json#full_attention_layers`), the other 24 a
4,096-token sliding window (`summaries/trackA/window_reach.json#window`); 32 heads, hidden 4,096
(`results/trackA/gpu/smoke.json` `config`, gi). Revision `d97e442d…` (`olmo3_7b_think_d97e442.json`).

**Step 6, patching.** Method `cd/finetune/look/patching.py:1–64` (one layer at a time, clean run's residual into the
hinted run, at hint tokens, reasoning or answer; logit difference W − O; restoration share; cuts with gap < 0.5 out).
- Per layer: `summaries/trackA/step10_handoff.json#handoff.by_cut_type.ii.all.drop_by_layer` (= DATA `s3.layers`).
- Readout share 0.902: same file, `drop_share_readout`. Set A: `summaries/trackA/setA/step10_handoff.json`.
- Heads: `summaries/trackA/setA/step9_fixed_heads.json` (use `hint - control`).
- Qwen3-8B: `summaries/trackA/qwen8b_mech/qwen8b_readout.json`.
- **Per-question records (numbers):** `step10_patching.json#cuts` (40 cuts), `setA/step10_patching.json#cuts` (66,
  16 questions), `cd/results/trackB/qwen8b_mech/qwen8b_step10_patching.json#cuts` (gi; 243 cuts, 42 questions).

**Step 7, fine-tuning.**
- LoRA: rank 16, alpha 32, dropout 0.05, all seven projections on every layer, LR 2e-4, 2 epochs, 8 examples a step,
  260 steps, max 32,768 tokens (`cd/finetune/train.py:64–76, 166`).
- Data: 530 questions run, 251 kept, 1,196 examples (1,040 train, 156 validation), 57 "neither" dropped
  (`summaries/trackA/data/examples_manifest.json`; not the stale `data/manifest.json`).
- Openers: `cd/finetune/make_targets.py:78, 99`.
- Consistency training (A40): `cd/finetune/make_bct.py:1–40`; 981 examples (881 train, 100 validation); 96 dropped
  (91 with no passing final answer in 4 tries, 5 with no no-hint sample on the key); 222 steps; epoch 1 chosen by validation loss 0.198727 vs 0.198789
  (`archive/sessions/2026-11-06/2026-11-06_2316_ALL_a40-check-merge-c-hook-fix.md:104–113`;
  `cd/finetune/data/a40/manifest.json`, gi).
- **Real training pairs on the Mac:** `cd/finetune/data/{train,validation}_examples.jsonl.gz` and `cd/finetune/data/a40/`
  (gi); A40's two passes `cd/results/trackA/a40/shard{1,2}of2/` (gi).
- **Loss curve:** per epoch only on the Mac (`summaries/trackA/val_loss.json`: base 0.2442, LoRA 0.18567 → 0.18537).
  Per-step `train_log.jsonl` on Sol (§4).

**Step 8, training inside.** Method `cd/finetune/look/a18.py:1–60`. LoRA: `summaries/trackA/gpu/a18/a18_readout.json`
(acts in the reasoning); consistency training: `a41_readout.json` (acts before the readout, layers 0–14). Rows:
`swap_rows.jsonl`, `swap_a40_rows.jsonl` (52 each; DATA `s3.swap`).

**Step 9, the other fixes.**
- The instruction: `cd/finetune/prompts/guide_note.txt:1`.
- The label: `WRAP` in `cd/finetune/eval.py:109`; only the inserted tool turn.
- The dial: `cd/finetune/provenance.py:1–45` (log α on the attention to the tool turn, layers 15, 19, 23).
- The two measured settings: α = 1 and α = 0.25 on the 120 (`summaries/trackA/gpu/b1r2/provenance_gen_report.json`,
  DATA `s5.b1r2`). The 30's α 0.25 and 0.5 (`summaries/trackA/gpu/provenance_gen/…`) are the earlier test.

**Step 10, the review team.** Solver `cd/agents/solver.py:20–45`; reviewers `cd/agents/reviewer.py:1–92`; checker
`cd/agents/checker.py`; reviewer prompt `cd/progress/reviewer_demo.py:34–36`; sentences `run_team.py:157–165`. 73, 53,
45 and 100: DATA `s4`, `docs/presentation/QA_FACTS.md:37–46`.

**Step 11, checking ourselves.**
- Preregistrations: the 42-row ledger `docs/paper/supplement/PREREGISTRATIONS.md:9–52`.
- Wilson: `cd/progress/common.py:279`. Bootstrap by question, 20,000, seed 0: `common.py:232, 248` (under 5 questions:
  "too few", :261).
- Labels: L3 and judges `docs/FINDINGS.md:279–304, 1675–1696` and the Nov 4 logs; L6 κ 0.961 with the blind judge
  (`summaries/trackA/labels/l6_report.json`).
- AI use: `docs/submission/AI_USE_INVENTORY.md` (`AI_USE.md` not yet written).
- The freeze: `docs/status/CHECKIN.md` §10 and the tag.
- **Missing:** a contamination audit. What exists: the 120's exclusion checks (`make_e2.py:30–89`) and the held-out
  leak checks (`summaries/trackA/data/examples_check.json`). Show those under their real name, or drop the word.

## 3. The bench: recorded runs

| test | records with text (gi) | numbers only (gi) | outcome fields |
|---|---|---|---|
| 1 | `cd/results/trackB/voyager.jsonl.gz` (2,430: 810 a model), `b15_voyager`, `b19_voyager` | `sol_vllm_runs/flags` (Qwen3-8B 1,620), `b17_sol_vllm_runs`, `b17/b17_flags` (2,430) | `summaries/trackB/trackB_runs.jsonl` (by run id) |
| 2 | `b16_voyager.jsonl.gz` (1,458), `b24_voyager.jsonl.gz` (972), `b19` | — | the same |
| 3 | `ollama.jsonl.gz` (22), `b20/<model>/b20_sol_vllm.jsonl.gz` (48: Nov 4 smoke) | the flags above | `mention_private`, `mention_final` |
| 4 | — | `cd/results/trackA/gpu/a39/eval_<system>_a39_{e2,mmlupro_30}_p*_runs.jsonl`; `gpu/eval/eval_<system>_p*_runs.jsonl` | on the run lines; labels `results/labels/L6/`, `gate3/L4/`, `L3_RA.csv` |
| 5 | `cd/results/trackC/team_c4.jsonl` (3,180), `team_c15_solve.jsonl` (600), rereviews c9–c18 | — | on the lines (`caught`, `checker_flag`) |
| 6 | — (no text needed) | the cut records in §2 step 6 | — |

- The text files hold `prompt_messages`, `transcript`, `reasoning_text`, `final_text`, `tool_steps` and
  `called_tool` (all 486 tool-call runs in `voyager.jsonl.gz` carry their call).
- Questions join by `item_id` to `mmlupro_30.jsonl`, `mmlupro_e2.jsonl`, `steered_cases.jsonl` or `c15_items.jsonl`.
- `results/demo/examples.json` (9 labelled rows, seeded, from `cd/tools/demo_examples.py`) carries no question,
  prompt, tool call or source line: the curated set needs a new builder.

## 4. On Sol: paths to copy

**Ritik's account:**
- The 120 and the 30, every fix:
  `/scratch/ragarw68/trackA/a39/eval_<system>_a39_{e2,mmlupro_30}_p<K>of<N>.jsonl.gz`. Systems: base, prompt_only, lora,
  lora_note, a40, a40_note, wrap, wrap_note, lora_wrap. Read by `l6_sheet.py`'s `REMOTE_DIR`.
- The 30 (Gate 3): `/scratch/ragarw68/trackA/eval/eval_<system>.jsonl.gz` (base, prompt_only, lora, lora_attn3, tags,
  lora_tags).
- Training logs: `/scratch/ragarw68/trackA/train/<version>/train_log.jsonl` and `chosen.json` (`train.py:318`;
  RUNBOOK:445).
- Qwen3-8B on/off and gpt-oss:
  `/scratch/ragarw68/cse598-cot-faithfulness/cot-disclosure/results/trackB/sol_vllm.jsonl.gz` (name inferred) and
  `…/results/trackB/b17/*.jsonl.gz`.
- Nemotron (B20): probably
  `/scratch/ragarw68/cse598-cot-faithfulness/cot-disclosure/results/trackB/b20/nemotron-3-nano-30b-a3b/b20_sol_vllm.jsonl.gz`
  (SOL_ARSHA:9, "Nemotron's are done" before the move).
- The dial's runs: `/scratch/ragarw68/trackA/provenance_gen/eval_prov-*`.

**Arsha's account (hers to copy):**
`/scratch/<Arsha's user>/cse598-cot-faithfulness/cot-disclosure/results/trackB/b20/{granite-4.2-8b,gemma-4-26b-a4b-it}/`.

**Shrey's account:** nothing needed; the Mac holds Track C's logs.

## 5. The DATA keys the brief names

| brief | current page (`docs/demo/index.html`, `demo-data`) |
|---|---|
| `layers.full`, `.effect`, `.share`, `.heads`, `.swap` | `s3.full`, `s3.layers`, `s3.share` (+ `s3.readout`, `s3.qwen`), `s3.heads`, `s3.swap` |
| `hint` | `s1.gate2`, `x.settings` (wordings aren't in DATA: from the code in step 2) |
| `dose` | `s1.dose` |
| `quiet` | `s2` |
| `fixes.systems` | `s5.systems` (+ `s5.b1r2`, `x.fresh`) |
| `agents` | `s4` |

The template's DATA (not on this Mac) may name these differently; phase 2 maps them once it's here.

## 6. Cautions found

- FINDINGS F41 says "883 examples": 883 are the hint examples; 981 in all (881 + 100). The frozen text isn't changed.
- `summaries/trackA/data/manifest.json` is an early, stale manifest; use `examples_manifest.json`.
- Heads: the frozen +0.068 is the `hint - control` key, not the sibling `hint` (0.066).
- 13 models if the progress round's Olmo 3 32B Think is counted; the report counts 12.
- B20's per-run files on the Mac are the Nov 4 smoke copies; B20's numbers come from `b20_report.json` only.
