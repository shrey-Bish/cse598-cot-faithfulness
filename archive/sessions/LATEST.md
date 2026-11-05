# Session log: the LLM judges' results, read by the protocol (2026-11-04 17:56 MST)

**By:** Ritik. Read by the pre-registered protocol and nothing else: `2026-11-04_1745_ALL_llm-judge-prereg.md`
(committed `66dd3f7`; amended §9 `3a9881b`, §10 `d5727db`, both before the runs). The code is
`tools/llm_judge.py` (`740fde7`, `3a9881b`); the command is `tools/llm_judge.py --report` (17:55). No model judged a
label outside the protocol. Texts and raw outputs stay in `results/labels/llm_judge/` (gitignored).

## 1. The runs

- **J-qwen and J-olmo (Voyager):** under the power guard on AC power.
  - J-qwen ran 17:50:21–17:52:21 and J-olmo 17:52:21–17:54:21; the guard ended at 17:55:21.
  - 395 rows each, 0 errors. The served models were `qwen3-30b-a3b-instruct-2507` and `olmo3-32b-instruct`.
- **J-opus:** 8 fresh sub-agents, one batch each, all answered (Claude Opus).
  - Tool uses per agent: 2, 2, 3, 3, 2, 2, 2, 2. Only its file's reads were asked for; which files were read isn't
    visible (a limit).
  - Each reply was saved verbatim as `opus/<sheet>_batch_NN_reply.txt`, and `--import-opus` read it.
- **Texts with no label** (§3's parse, as amended by §9):
  - J-opus 0, J-qwen 0, AI1 0.
  - **J-olmo 72 of 159 on L3 and 8 of 294 on L4.** On 22 two-text rows it gave one bare label for two texts. On 17
    L3 rows and 8 L4 rows it began each line with the field's name ("final_excerpt:", "final_answer:") rather than
    "final:". On 1 row it added words.
  - By the rule these have no label: they are counted, and left out of J-olmo's kappas.
  - A cell J-olmo left unlabeled needs the other three AI sets unanimous for a majority (§4: 3 of 4).

## 2. L3 (101 rows; Ritik against each AI set, Cohen's kappa, rows in brackets)

| | private: all | tool | user | final: all | tool | user |
|---|---|---|---|---|---|---|
| AI1 (ChatGPT 5 Astra High) | 0.627 (58) | 0.288 (30) | 0.850 (28) | 0.543 (101) | 0.589 (44) | 0.425 (57) |
| J-opus (Claude Opus) | 0.669 (58) | 0.434 (30) | 0.842 (28) | 0.837 (101) | 0.935 (44) | 0.646 (57) |
| J-qwen (Qwen3 30B Instruct) | 0.462 (58) | 0.434 (30) | 0.468 (28) | 0.234 (101) | 0.316 (44) | 0.130 (57) |
| J-olmo (Olmo 3.1 32B Instruct) | 0.153 (26) | 0.074 (11) | 0.159 (15) | 0.291 (61) | 0.197 (23) | 0.330 (38) |
| **The AI majority (3 of 4)** | **0.472** (58) | **0.353** (30) | **0.576** (28) | **0.234** (101) | **0.223** (44) | **0.201** (57) |

- **AI1's row reproduces Nov 3's numbers exactly,** through the same code (`label_kit.kappa`).
- **Between the AI sets (final, all):**
  - AI1 and J-opus 0.468;
  - J-opus against J-qwen 0.306, J-olmo 0.230;
  - J-qwen and J-olmo 0.247;
  - AI1 against J-qwen 0.072, J-olmo 0.203.
  - Fleiss' kappa across all four: private 0.185 (26 rows all four labeled), final 0.267 (61).

## 3. L4 part 1 (294 rows, final answer only; Ritik against each AI set)

| | all | tool_injected | tool_pasted | user |
|---|---|---|---|---|
| AI1 | 0.930 (294) | 0.958 (147) | 0.891 (58) | 0.908 (89) |
| J-opus | 0.967 (294) | 0.958 (147) | 0.972 (58) | 0.981 (89) |
| J-qwen | 0.021 (294) | −0.012 (147) | 0.051 (58) | 0.066 (89) |
| J-olmo | 0.043 (286) | 0.081 (139) | 0.071 (58) | −0.014 (89) |
| **The AI majority** | **0.417** (294) | 0.442 (147) | 0.427 (58) | 0.367 (89) |

- **AI1 and J-opus agree with each other at 0.930.** Every pair with J-qwen or J-olmo is 0.015–0.051. Fleiss across
  the four is 0.050 (286 rows).
- **Why J-qwen and J-olmo are near 0 (descriptive, by label counts):**
  - J-qwen gave `says_changed` to 277 of 294 rows. Every L4 answer ends on the hint's letter, which the guide says
    not to treat as a reason.
  - J-olmo gave `mentions_only` to 250 of 294.
  - Ritik's counts are 125 `no_mention`, 120 `says_changed`, 46 `mentions_only`; AI1's and J-opus's are within a few
    of his.
  - Two near-constant judges carry no information about the rows, and the 3-of-4 majority inherits that.

## 4. The bias check (each judge against Ritik, by the writer's family)

| judge | L3 private, Olmo-written | Qwen-written | L3 final, Olmo-written | Qwen-written |
|---|---|---|---|---|
| AI1 | 0.746 (36) | 0.368 (22) | 0.503 (79) | 0.707 (22) |
| J-opus | 0.711 (36) | 0.522 (22) | 0.880 (79) | 0.730 (22) |
| J-qwen | 0.422 (36) | 0.522 (22) | 0.270 (79) | 0.093 (22) |
| J-olmo | 0.160 (12) | 0.133 (14) | 0.267 (47) | 0.300 (14) |

- No judge does consistently better on its own family's texts. J-qwen is higher on Qwen-written private reasoning
  (0.522 against 0.422) but lower on Qwen-written final answers (0.093 against 0.270). J-olmo is low on both.
- With 22 Qwen-written rows, these are wide.
- L4 part 1 is all Olmo-written, so it has no comparison.

## 5. Gate 2's label part, by the amended rule (§5): **not met**

- **The rule:** met only if Ritik against the AI majority has kappa 0.6 or more in every L3 cell. It is under 0.6 in
  all six: 0.472, 0.353, 0.576, 0.234, 0.223, 0.201.
- **Stated plainly:** Gate 2's label part is not met.
- **The labels are reported with their agreement:** Ritik's labels stand as the labels, as §6 says.
- **Why, in one line:** two of the four AI judges barely track the guide (near-constant on L4, low on L3), and the
  majority rule averages them in. The two strongest AI raters agree with Ritik closely: J-opus 0.669 and 0.837 on
  L3, 0.967 on L4; AI1 0.627 and 0.543 on L3, 0.930 on L4.
- **Not a gate claim,** reported for what it is: J-opus against Ritik is 0.6 or more in 5 of L3's 6 cells. Private
  reasoning on tool runs is 0.434.

## 6. The re-look (§6)

- **Cells where Ritik's label and the AI majority differ, "no majority" included:** 60 on L3 and 140 on L4 part 1.
- **The blind sheets:** `results/labels/llm_judge/relook_L3.csv` and `relook_L4_part1.csv`. Each shows the row, the
  text, the hint's source and letter, and the excerpt, with an empty label column and no one's label.
- **His re-look is final,** recorded in a dated log. Gate 2's number stays on his original labels.
- Most of these cells come from J-qwen's and J-olmo's near-constant labels, through the majority rule.

## 7. What Ritik may want to decide (none applied; any change would be a new, dated amendment, labelled post hoc)

1. **Do the re-look as pre-registered:** 200 cells, blind.
2. **Or amend the re-look list (post hoc, disclosed):** for example, only the cells where Ritik differs from both
   strong raters (AI1 and J-opus agreeing with each other).
   - Gate 2's verdict above would not change: it was read by the rule as committed.

## 8. Limits

- **One human rater.** Every number above is human-vs-AI or AI-vs-AI agreement, not inter-human reliability.
- **J-opus:**
  - its temperature can't be set;
  - its sub-agents' environment names the project folder;
  - which files they read isn't visible.
- **J-olmo's missing labels** (72 on L3) are format failures, counted as the rule says.
