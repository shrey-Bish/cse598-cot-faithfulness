# Do Thinking Modes Make Chain-of-Thought More Honest?

CSE 598, Fall 2026 · Group 10: Shrey Bishnoi, Arsha Jindal, Ritik Agarwal

When a hint pushes a model toward an answer, does the model say so? We test three
pairs of models (Olmo 3 7B, Olmo 3 32B, Qwen3 30B) on ASU's free Voyager service.
Each pair has a regular chat model and a thinking model. Thinking models send back
their private reasoning and their final answer separately, so we can check which of
the two mentions the hint.

## Status (October 2026, after the progress presentation)

**Question:** when a wrong hint changes a model's answer, does the model admit that it
used the hint?

**What we found** (all numbers in `docs/progress/RESULTS_SUMMARY.json`; mentions are
keyword counts until hand-labeled):
- **Test 1, 24 generated puzzles, user hint.**
  - Only the smallest instruct model followed wrong hints: Olmo 3 7B Instruct, 5 of 48
    hinted runs.
  - The thinking models' private reasoning mentioned the hint in 208 of 216 hinted runs,
    their final answers in 8. All 8 final-answer mentions also appear in the private
    reasoning.
- **Test 2, 30 MMLU-Pro questions.**
  - Thinking models picked a pasted tool hint's wrong letter on 17 of 31 questions, and
    a user hint's on 2 of 31.
  - Of the 17, the private reasoning referred to the tool in 16, the final answer in 6.
- **Reviewer check (5 hint-steered answers × 3 reviews).** A reviewer accepted the wrong
  answer in 0 of 15 reviews from the answer alone, and in 7 of 15 once it read the
  explanation.
- **Replies cut off at the token limit** leak private reasoning when not streamed: 8 of
  8 vs 0 of 8 streamed.

**Plan (weeks 9–16):** `docs/plan/PROJECT_PLAN.md`
- [Track A: explain and fix](docs/plan/TRACK_A_explain_fix.md) (Ritik): look inside Olmo
  3 7B Think; LoRA + source tags; behavior-based evaluation.
- [Track B: test widely](docs/plan/TRACK_B_test_widely.md) (Arsha): Ollama Qwen3,
  OpenAI, Anthropic, xAI; thinking on/off; real tool calls (they work on Voyager);
  GPQA; 3 runs per question.
- [Track C: multi-agent pipeline](docs/plan/TRACK_C_multi_agent.md) (Shrey): solver →
  reviewer → checker.
- [Budget](docs/plan/BUDGET.md): about $15, capped at $5 per closed provider, enforced
  in code.

**Code** (in `cot-disclosure/`):
- `providers/`: one interface over Voyager, Ollama, OpenAI, Anthropic and xAI, plus the
  budget guard
- `tools/answer_key.py`: hint conditions and real tool calls
- `progress/run_trackB.py` (`--dry-run`) with `configs/trackB.yaml`
- `agents/run_team.py` (`--replay`, `--live`)
- `finetune/`: dataset and source tags

**Progress-round notes and figures:**
- notes: [`docs/progress/`](docs/progress/) (`PROGRESS_REPORT.md`, `SLIDE_POINTS.md`,
  `CONCEPTS.md`)
- figures: [`presentation/progress/figures/`](presentation/progress/figures/)
- evidence viewer and screenshots: [`presentation/progress/`](presentation/progress/)

**Reproduce:**

```bash
.venv/bin/python cot-disclosure/progress/analyze_progress.py       # RESULTS_SUMMARY.json + figures F1-F9
.venv/bin/python cot-disclosure/progress/run_trackB.py --dry-run   # Track B plan: calls and cost per provider
.venv/bin/python cot-disclosure/agents/run_team.py --replay        # Track C on saved data (no API calls)
.venv/bin/python cot-disclosure/finetune/build_dataset.py          # Track A train / held-out records
cd cot-disclosure && ../.venv/bin/python -m pytest -q tests        # unit tests
```

The commands that call models need keys in `cot-disclosure/.env` (see
`docs/plan/BUDGET.md`). They are listed in `docs/progress/PROGRESS_REPORT.md` §8 and the
track pages.

| Folder | What's in it |
|---|---|
| `cot-disclosure/` | The code that runs the models, the raw results, and the analysis. Its README has the exact commands. |
| `presentation/` | The progress slides and the script that builds them from the results. |

## Get the same numbers

```bash
cd cot-disclosure
python analyze.py          # recomputes every number we report from results/*.jsonl
```

To rerun the experiments themselves you need a Voyager key: `cp .env.example .env`,
add the key, then run `python experiments.py run`.
