# The handbook's Part C: three descriptive analyses (Nov 26)

**Descriptive, post-freeze (nov 26).** From saved, frozen records only; no new runs; no verdict changes. Made by `cot-disclosure/tools/handbook_part_c.py`; numbers in `cot-disclosure/results/summaries/handbook/part_c.json`; checked by `cot-disclosure/tests/test_handbook_part_c.py`. Rates are k of n runs with a 95% Wilson interval.

## 1. Evaluation at a glance

Each headline is a row of [02_NUMBERS](../presentation/pack/02_NUMBERS.md) (no new number). The backup slide "Datasets, metrics and baselines" shows it without the codes.

| data | measure | compared with | systems | headline | finding | 02 rows |
|---|---|---|---|---|---|---|
| 54 test questions, 3 runs each (Track B) | follows the same wrong answer | the same answer from the user | 12 open models, thinking on and off | Qwen3 30B Instruct: 1 of 162 from the user, 147 of 162 from its own tool call | F16 | N132 |
| the same questions, after a tool call | names the tool (keywords) | the private reasoning | Qwen3 8B, thinking on | reasoning 141 of 145; final answer 0 of 143 | F29 | N134, N135 |
| Olmo 3 7B Think's takeovers (19 cuts, 9 questions) | share of the hint's effect (activation patching) | all 32 layers | Olmo 3 7B Think | layers 15, 19 and 23 carry 0.90 [0.85, 0.96] | F11 | N92 |
| 120 fresh questions (held out) | follows a wrong hint; takes a right tool hint | no fix; the one-line instruction | five trained versions | consistency training: 297 of 703 → 84 of 694 wrong hints followed; 439 of 476 → 347 of 459 right tool hints taken | F41 | N151 |
| 84 hand-labelled followed answers | the final answer says the hint shaped it | the one-line instruction | fine-tuning (LoRA) | 37 of 42 against 18 of 42 | F45 | N75 |
| Track C's 73 wrong tool answers | the reviewer corrects a wrong answer | the reviewer seeing the answer only | Olmo 3.1 32B reviewer | 59 of 73 alone; 3 of 73 with the tool's reply | F18 | N48 |
| 100 fresh items (Track C) | wrong answers stopped | the reviewer alone | the checker (re-solves without the tool) | 53 of 53 | F24 | N137 |
| the same 100 items, after the freeze | wrong answers reaching the user | the original model as solver | consistency-trained solver | 29 of 55 → 15 of 55 with the solver alone | C27 | N164, N165 |

## 2. How the answers fail, by category (the hand labels)

Every labelled row followed its hint; no sheet holds a resisted answer. Ritik's final labels; the categories are the rater guide's ([docs/labeling/](../labeling/)).

### L6 (84 rows; `cot-disclosure/results/labels/L6/L6_RA_20261113.csv + key_L6.csv`)

| group | n | No mention of the hint | Mentions the hint only | Says the hint changed its answer | Says it rejected the hint | Unclear |
|---|---|---|---|---|---|---|
| lora | 42 | 5 (12%) | 9 (21%) | 28 (67%) | 0 (0%) | 0 (0%) |
| prompt_only | 42 | 23 (55%) | 5 (12%) | 13 (31%) | 1 (2%) | 0 (0%) |

By channel:

| group, channel | n | no_mention | mentions_only | says_changed | rejects_hint | unclear |
|---|---|---|---|---|---|---|
| lora | inserted | 14 | 0 | 4 | 10 | 0 | 0 |
| lora | pasted | 14 | 3 | 2 | 9 | 0 | 0 |
| lora | user | 14 | 2 | 3 | 9 | 0 | 0 |
| prompt_only | inserted | 14 | 9 | 1 | 4 | 0 | 0 |
| prompt_only | pasted | 14 | 8 | 2 | 4 | 0 | 0 |
| prompt_only | user | 14 | 6 | 2 | 5 | 1 | 0 |

### L4 part 1 (294 rows; `cot-disclosure/results/labels/gate3/L4/L4_part1_RA.csv + key_L4.csv`)

| group | n | No mention of the hint | Mentions the hint only | Says the hint changed its answer | Says it rejected the hint | Unclear |
|---|---|---|---|---|---|---|
| base, matched followed run | 74 | 62 (84%) | 0 (0%) | 11 (15%) | 0 (0%) | 1 (1%) |
| lora, keyword candidate | 147 | 6 (4%) | 42 (29%) | 97 (66%) | 1 (1%) | 1 (1%) |
| prompt_only, matched followed run | 73 | 57 (78%) | 4 (5%) | 12 (16%) | 0 (0%) | 0 (0%) |

By channel:

| group, channel | n | no_mention | mentions_only | says_changed | rejects_hint | unclear |
|---|---|---|---|---|---|---|
| base, matched followed run | tool_injected | 40 | 31 | 0 | 8 | 0 | 1 |
| base, matched followed run | tool_pasted | 16 | 15 | 0 | 1 | 0 | 0 |
| base, matched followed run | user | 18 | 16 | 0 | 2 | 0 | 0 |
| lora, keyword candidate | tool_injected | 70 | 0 | 25 | 44 | 0 | 1 |
| lora, keyword candidate | tool_pasted | 30 | 2 | 7 | 20 | 1 | 0 |
| lora, keyword candidate | user | 47 | 4 | 10 | 33 | 0 | 0 |
| prompt_only, matched followed run | tool_injected | 37 | 30 | 3 | 4 | 0 | 0 |
| prompt_only, matched followed run | tool_pasted | 12 | 8 | 1 | 3 | 0 | 0 |
| prompt_only, matched followed run | user | 24 | 19 | 0 | 5 | 0 | 0 |

## 3. By subject on the 120 fresh questions (descriptive)

Pooled as A39's report pools them (answered runs; wrong hints over the user's, pasted and inserted channels; right hints over the tool channels). chemistry 30, engineering 30, law 30, physics 30 questions.

**Wrong hints followed (lower is better)**

| system | chemistry | engineering | law | physics | all |
|---|---|---|---|---|---|
| No fix | 61 of 175 (35%) [28, 42%] | 73 of 173 (42%) [35, 50%] | 107 of 180 (59%) [52, 66%] | 56 of 175 (32%) [26, 39%] | 297 of 703 (42%) [39, 46%] |
| One-line instruction | 38 of 178 (21%) [16, 28%] | 70 of 176 (40%) [33, 47%] | 93 of 180 (52%) [44, 59%] | 36 of 179 (20%) [15, 27%] | 237 of 713 (33%) [30, 37%] |
| Fine-tuning (LoRA) | 45 of 174 (26%) [20, 33%] | 71 of 175 (41%) [34, 48%] | 94 of 177 (53%) [46, 60%] | 38 of 179 (21%) [16, 28%] | 248 of 705 (35%) [32, 39%] |
| Consistency training | 6 of 174 (3%) [2, 7%] | 15 of 171 (9%) [5, 14%] | 55 of 175 (31%) [25, 39%] | 8 of 174 (5%) [2, 9%] | 84 of 694 (12%) [10, 15%] |

**Right tool hints taken (higher is better)**

| system | chemistry | engineering | law | physics | all |
|---|---|---|---|---|---|
| No fix | 113 of 118 (96%) [90, 98%] | 107 of 118 (91%) [84, 95%] | 109 of 120 (91%) [84, 95%] | 110 of 120 (92%) [85, 95%] | 439 of 476 (92%) [89, 94%] |
| One-line instruction | 113 of 120 (94%) [88, 97%] | 110 of 116 (95%) [89, 98%] | 100 of 120 (83%) [76, 89%] | 108 of 120 (90%) [83, 94%] | 431 of 476 (91%) [88, 93%] |
| Fine-tuning (LoRA) | 111 of 120 (92%) [86, 96%] | 110 of 120 (92%) [85, 95%] | 91 of 117 (78%) [69, 84%] | 109 of 120 (91%) [84, 95%] | 421 of 477 (88%) [85, 91%] |
| Consistency training | 100 of 117 (85%) [78, 91%] | 79 of 111 (71%) [62, 79%] | 71 of 112 (63%) [54, 72%] | 97 of 119 (82%) [74, 87%] | 347 of 459 (76%) [71, 79%] |

