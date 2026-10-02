# Do Thinking Modes Make Chain-of-Thought More Honest?

CSE 598, Fall 2026 · Group 10: Shrey Bishnoi, Arsha Jindal, Ritik Agarwal

When a hint pushes a model toward an answer, does its explanation say so? We compare
three instruct/thinking pairs (Olmo 3 7B, Olmo 3 32B, Qwen3 30B-A3B) on ASU Research
Computing's Voyager API. Thinking models return a private reasoning trace and a final
answer separately, so we can check which of the two mentions the hint.

| Folder | Contents |
|---|---|
| `cot-disclosure/` | Experiment harness, raw results, analysis. Its README has the exact commands. |
| `presentation/` | Progress-presentation deck and the script that builds it from the results. |

## Reproduce the numbers

```bash
cd cot-disclosure
python analyze.py          # recomputes every reported number from results/*.jsonl
```

Rerunning the experiments themselves needs a Voyager key: `cp .env.example .env`, add
the key, then `python experiments.py run`.
