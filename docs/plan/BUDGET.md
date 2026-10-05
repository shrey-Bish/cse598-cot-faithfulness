# Budget

About **$15 in total**: $5 for OpenAI, $5 for Anthropic, $5 for xAI. Everything else is
free:
- **ASU Voyager:** the open models used so far
- **Ollama:** local Qwen3
- **ASU Sol GPUs:** Track A training

## How spending is capped and logged (`cot-disclosure/providers/budget.py`)

- **Caps.** Set in `cot-disclosure/.env` as `OPENAI_CAP_USD`, `ANTHROPIC_CAP_USD` and
  `XAI_CAP_USD`. The default is 5 each.
- **Before each paid call,** the guard assumes the worst case: the prompt (about 4
  characters per token) plus `max_tokens` of output. It refuses the call if that could
  take the provider past its cap. The Track B runner sends paid calls one at a time and
  stops a provider at its cap.
- **After each paid call,** it prices the token usage the provider returned and appends
  a row to `cot-disclosure/results/spend_log.jsonl`. The row records provider, model,
  input / output / reasoning tokens, cost and a label. Totals are always recomputed from
  that log.
- **Status:** `python -m providers.budget --status` (run from `cot-disclosure/`).
- **Before a sweep:** `python cot-disclosure/progress/run_trackB.py --dry-run` prints
  jobs, calls and estimated cost per provider, and says when a plan would go over a cap.
- **Keys.** Read from `.env` (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `XAI_API_KEY`) and
  never printed. The adapters refuse a key that equals the Voyager key. Today's `.env`
  has `OPENAI_API_KEY` set to the Voyager key, so no OpenAI call can be made until a
  real OpenAI key replaces it.
- **Data.** Only public benchmark questions (our generated puzzles, MMLU-Pro, GPQA) go
  to OpenAI, Anthropic or xAI. Never personal or university data.

## Prices (from each provider's pricing page on 2026-10-04)

USD per 1M tokens, standard tier, short prompts. Stored in
`cot-disclosure/configs/prices.yaml`.

| Model | Provider | Input | Output | Thinking on/off? | Reasoning returned |
|---|---|---|---|---|---|
| gpt-6-luna | OpenAI | 0.10 | 0.50 | yes (effort `none`) | summary |
| gpt-6-astra | OpenAI | 10.00 | 50.00 | always on | summary |
| claude-haiku-4-5-20251001 | Anthropic | 1.00 | 5.00 | yes (retires no sooner than 2026-10-15) | summary |
| claude-opus-5-5 | Anthropic | 4.00 | 20.00 | always on | summary |
| grok-4.3 | xAI | 1.25 | 2.50 | yes (effort `none`, per model page) | summary |
| grok-4.7 | xAI | 2.00 | 6.00 | always on | summary |

Sources:
- OpenAI: https://developers.openai.com/api/docs/pricing
- Anthropic: https://platform.claude.com/docs/en/about-claude/pricing
- xAI: https://docs.x.ai/developers/models.md

## How many calls $5 buys: an estimate, not a measurement

This assumes 500 input and 4,000 output tokens per thinking call. Real thinking replies
on our questions were often longer: Olmo 3 7B Think's median was 8,025.5 output tokens on
the puzzles, and some MMLU-Pro replies hit 16,000. So treat these numbers as upper
bounds. From `python -m providers.budget --table` and `RESULTS_SUMMARY.json` →
`scope_numbers.budget_estimate`:

| Model | Est. USD per call | Est. calls per $5 |
|---|---|---|
| gpt-6-luna | 0.00205 | 2,439 |
| gpt-6-astra | 0.20500 | 24 |
| claude-haiku-4-5-20251001 | 0.02050 | 243 |
| claude-opus-5-5 | 0.08200 | 60 |
| grok-4.3 | 0.01063 | 470 |
| grok-4.7 | 0.02500 | 200 |

**What this means for the plan:**
- Track B uses the cheapest model per provider that can switch thinking off:
  gpt-6-luna, Haiku 4.5, grok-4.3.
- The flagship models (gpt-6-astra, Opus 5.5, grok-4.7) only fit a handful of
  spot-checks.
- The Track B dry run (`TRACK_B_test_widely.md`) keeps every provider inside its cap.

## Spend so far

$0. No paid call has been made. There are no OpenAI, Anthropic or xAI keys in `.env`
yet, so the smoke tests were skipped (`cot-disclosure/results/spend_log.jsonl` does not
exist).
