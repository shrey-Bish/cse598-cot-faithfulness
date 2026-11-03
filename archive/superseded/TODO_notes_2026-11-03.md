# TODO's Notes section, moved here on Nov 3 (the doc audit), word for word

## Notes

**A2, the checkpoint report at 100 kept** (written Oct 26 10:42 MST, after 250 questions; not sent
at the time because the session ran out):
- **Keep rate:** 117 of 250 [41, 53%], pilot 5 of 10. Kept by set: MMLU-Pro 68 of 149, hard puzzles
  46 of 96, easy puzzles 3 of 5.
- **Step 7, a prefill target within 4 samples:**

  | channel | wrong hint | correct hint |
  |---|---|---|
  | user | 112 of 117 [90, 98%] | 60 of 61 [91, 100%] |
  | tool, pasted | 110 of 117 [88, 97%] | 59 of 59 [94, 100%] |
  | tool, inserted (declared) | 102 of 117 [80, 92%] | 62 of 62 [94, 100%] |

  Failed samples: wrong letter 192, hit the token cap 18, reasoning refers to instructions 14,
  called the tool again 6. No rate was off by more than half from the pilot, so the run went on.
- **Target length** (prompt + target, tokens; median / 90th percentile / max): easy puzzles 5,401 /
  7,356 / 9,611 (18 examples); hard puzzles 11,342 / 16,869 / 26,748 (204); MMLU-Pro 4,678 / 10,409 /
  18,523 (311); all 7,352 / 14,094 / 26,748 (533). Held-out Step 2b replies: 11,988 / 24,856 / 34,706.
- **Stance after the final-answer opener** (keyword count): wrong hint: disagrees 331, agrees after
  checking 13, neither 7; correct hint: agrees after checking 148, disagrees 14, neither 20.
  "Neither" 27 of 533 (5%).

**A1 final** (13:45 MST Oct 27): 251 kept of 530 [43, 52%]; Step 7 targets: user wrong 243 of 251,
pasted wrong 238 of 250, inserted wrong 229 of 250 (correct hints 122 of 123, 128 of 128, 131 of
131); 1,133 targets, 42 of them the fallback; "neither" 57 (5%), dropped. Assembled: 1,196 examples
(1,040 train from 217 questions, 156 validation from 34). Session log 2026-10-27 13:55.

**Order for Tracks B and C (decided Oct 27).** Track A needs no Voyager after Steps 6–7. At most 4
requests in flight across every process on the Mac.

| # | Step | Calls | Time |
|---|---|---|---|
| 0 | Code, no calls: B5, B12, the B8 format | 0 | half a day |
| 1 | Per Voyager model: served-template check (B10), canary reference (B11), smoke `--limit 5` and dry run in a log (B13) | ~10 per model | 15 min per model |
| 2 | Track B, Qwen3 30B Thinking first (Track C's solver): 54 questions × 5 conditions × 3 runs + tool rounds | ~972 | ~5.4 h (972 × 80 s / 4) |
| 3 | Track B, Qwen3 30B Instruct | ~972 | ~1.4 h |
| 4 | Track B, Olmo 3 7B Think with `tool_injected` | ~810 | ~7.9 h (810 × 140 s / 4) |
| 5 | Qwen3-8B on Sol (replaces Ollama, Oct 28; Hugging Face since Oct 29): two GPU jobs, core cells first | 1,620 runs | 10–15 GPU h |
| 6 | Track C code (C6, C2, C3, C7), then C1 when Voyager has room | 35 | 15 min |
| 7 | Export `steered_cases.jsonl` (B8); Track C on N steered + N matched no-hint cases, 3 repeats, tool and no-tool teams (C4), Qwen3 Thinking's first | ~114 × N (N = 30: ~3,400) | ~3.3 h at 4 in flight |
| 8 | Analysis as data lands: B14, B9 (the Gate 2 question), C5 | 0 | — |

Without GPQA: about 6,200 Voyager calls, 18–28 hours. Closed models only on keys and "go". Times
for Qwen3-8B on Sol are an estimate (Oct 29: ~6,200 output tokens a thinking run and ~2,000 without,
Voyager's Qwen3 30B lengths; ~120–190 tokens/s on Hugging Face);
Voyager times come from the progress round's per-call means.
