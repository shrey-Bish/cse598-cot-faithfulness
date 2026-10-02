# Do Thinking Modes Make Chain-of-Thought More Honest?

CSE 598, Fall 2026 · Group 10: Shrey Bishnoi, Arsha Jindal, Ritik Agarwal

When a hint pushes a model toward an answer, does the model say so? We test three
pairs of models (Olmo 3 7B, Olmo 3 32B, Qwen3 30B) on ASU's free Voyager service.
Each pair has a regular chat model and a thinking model. Thinking models send back
their private reasoning and their final answer separately, so we can check which of
the two mentions the hint.

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
