# cot-disclosure

Do reasoning models' private traces and public answers tell the same story?

Thinking models return two channels: a private scratchpad (`reasoning_content`)
and the reply a user sees (`content`). This harness measures what shows up in
the first and disappears from the second, using ASU Research Computing's free
LLM endpoint.

## Setup

Python 3.9+ with only the standard library. No GPU, no `pip install`.

```bash
cp .env.example .env      # then paste your key from https://voyager.rc.asu.edu -> LLM Access
```

## Run

```bash
python run.py ladder                     # find the difficulty where models start failing
python run.py pilot --level 7 9 --n 30   # control vs suggested-answer cue, 7 people / 9 swaps
python run.py pilot --models olmo3-32b-instruct olmo3-32b-think --level 7 9
```

### Progress-presentation round (responds to the proposal review)

```bash
python experiments.py run --workers 20   # 1,056 calls: repeated no-hint runs, balanced wrong
                                         # hints, correct hints, "think briefly", "answer only"
python analyze.py                        # report + results/summary.json (works on partial runs)
```

Design: 24 shuffled-object puzzles (7 people, 15 swaps) with correct answers
balanced across A–G; per item, no hint × 3 seeds, wrong hint × 2 (positions
balanced), correct hint × 1; temperature 0.6, fixed seeds, 16k max tokens,
streamed. Three instruct/thinking pairs: Olmo 3 7B, Olmo 3 32B, Qwen3 30B-A3B.

### Slides

```bash
cd ../presentation
npm install          # pptxgenjs, react-icons, sharp
node build_deck.js   # writes CSE598_progress_presentation.pptx
```

The deck reads every number from `results/summary.json`, so rerunning
`analyze.py` and then `build_deck.js` refreshes it.

Every response is cached in `cache/`, so rerunning a command re-analyses
without new API calls. Delete `cache/` to force fresh calls. Raw per-call
results land in `results/*.jsonl`.

## Files

| File | Purpose |
|---|---|
| `client.py` | API client: retries, backoff, on-disk cache, splits trace from answer |
| `tasks.py` | Procedurally generated puzzles with exact answers (shuffled objects, race ordering) |
| `parse.py` | Extracts the final letter; handles `Answer: (X)`, `\boxed{X}`, bold, prose |
| `detect.py` | Keyword detectors: cue acknowledgement, uncertainty, self-correction |
| `run.py` | `ladder` and `pilot` experiments plus summary tables |

## Things we learned about the endpoint (verified 2026-10-01/02)

- Thinking models return the trace in a separate `reasoning_content` field.
- **Set `max_tokens` high (we use 8000).** When a response is cut off, the trace
  is *not* returned separately: all of the raw reasoning lands in `content`, the
  user-facing field. At `max_tokens=1500` we saw 5,929 characters of private
  reasoning in `content` and an empty `reasoning_content`.
- `reasoning_effort` is accepted but ignored (low and high gave ~7,300 chars
  each). Prompt wording does work: "think very briefly" roughly halves the trace.
- Thinking cannot be switched off: `chat_template_kwargs={"enable_thinking": false}`
  is ignored on all 7 thinking models tried, including Qwen 3.5/3.6/3.8 hybrids.
- `seed` is honored (same seed, same output at temperature 0.8), so repeats are reproducible.
- Responses over ~100 s fail with Cloudflare HTTP 524 unless streamed; `client.py` streams,
  and requests `stream_options.include_usage` so token counts still come back.
- Models often ignore the requested answer format and write `\boxed{E}`; this
  silently failed 17% of answers before `parse.py` handled it.

## Known limitations

- `detect.py` is keyword matching. Headline numbers must be checked against a
  hand-labelled sample before they are reported.
- Puzzles are synthetic. They avoid training-data contamination but are not
  the full BIG-Bench Hard distribution.
