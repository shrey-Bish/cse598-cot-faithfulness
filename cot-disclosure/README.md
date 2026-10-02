# cot-disclosure

Do thinking models tell the same story in their private reasoning and in their final answer?

A thinking model sends back two things: its private reasoning (the `reasoning_content`
field) and the reply a user sees (the `content` field). We give models puzzles, sometimes
with a hint, and check what shows up in the first and goes missing from the second. All
calls go to ASU Research Computing's free model service.

## Setup

You only need Python 3.9 or newer. No GPU and nothing to install.

```bash
cp .env.example .env      # then paste your key from https://voyager.rc.asu.edu -> LLM Access
```

## Run

```bash
python run.py ladder                     # find how hard the puzzles must be before models slip
python run.py pilot --level 7 9 --n 30   # no hint vs a suggested answer, 7 people and 9 swaps
python run.py pilot --models olmo3-32b-instruct olmo3-32b-think --level 7 9
```

### The progress-presentation round (our reply to the proposal review)

```bash
python experiments.py run --workers 20   # 1,056 calls: no-hint repeats, wrong hints spread
                                         # across letters, right hints, "think briefly", "answer only"
python analyze.py                        # prints the report and writes results/summary.json
                                         # (works on a half-finished run too)
```

What we ran: 24 swap puzzles (7 people, 15 swaps), with right answers spread evenly
across A to G. For each puzzle we ask with no hint 3 times, with a wrong hint 2 times
(the hinted letters are spread out too), and with a right hint once. Randomness
(temperature) is 0.6, random seeds are fixed so runs repeat exactly, and replies can be
up to 16,000 tokens. Three model pairs: Olmo 3 7B, Olmo 3 32B, Qwen3 30B.

### Slides

```bash
cd ../presentation
npm install          # pptxgenjs, react-icons, sharp
node build_deck.js   # writes CSE598_progress_presentation.pptx
```

The slides read every number from `results/summary.json`, so if you rerun
`analyze.py` and then `build_deck.js`, the slides update.

We save every reply in `cache/`, so running a command again redoes the analysis
without calling the models again. Delete `cache/` if you want fresh calls. The raw
result for each call goes to `results/*.jsonl`.

## Files

| File | What it does |
|---|---|
| `client.py` | Calls the model service: retries, waits between tries, saves replies, splits the reasoning from the answer |
| `tasks.py` | Makes new puzzles with one right answer (swap puzzles, race order puzzles) |
| `parse.py` | Finds the answer letter, whether the model wrote `Answer: (X)`, `\boxed{X}`, bold, or plain text |
| `detect.py` | Keyword checks: does the text mention the hint, show doubt, or correct itself |
| `run.py` | The `ladder` and `pilot` experiments and their summary tables |
| `audit.py` | Shows each keyword match in its sentence, so we can check the keyword checks by eye |
| `experiments.py` | The progress-presentation round |
| `analyze.py` | Turns the raw results into the numbers on the slides |

## What we learned about the model service (checked 2026-10-01 and 02)

- Thinking models send their reasoning in a separate `reasoning_content` field.
- **Allow long replies (we use 16,000 tokens).** When a reply gets cut off, the reasoning
  is *not* kept separate: all of it lands in `content`, the part the user sees. With a
  1,500-token limit we saw 5,929 characters of private reasoning in `content` and nothing
  in `reasoning_content`.
- The `reasoning_effort` setting is accepted but does nothing (low and high both gave
  about 7,300 characters). Wording does work: "think very briefly" cuts the reasoning
  by 30% to 48%.
- Thinking can't be turned off. `chat_template_kwargs={"enable_thinking": false}` is
  ignored on all 7 thinking models we tried, including the Qwen 3.5, 3.6 and 3.8 models.
- The `seed` setting works (same seed, same reply at temperature 0.8), so runs repeat exactly.
- Replies that take more than about 100 seconds fail with a Cloudflare 524 error unless
  they are streamed (sent back in pieces). `client.py` streams, and asks for
  `stream_options.include_usage` so token counts still come back.
- Models often ignore the answer format we ask for and write `\boxed{E}` instead. In our
  difficulty test, 54 of 118 answers (46%) weren't in the `Answer: (X)` form, and a simple
  reader would have marked them wrong. `parse.py` handles these.

## Limits

- `detect.py` only matches keywords. We will check our main numbers against replies we
  label by hand before we report them.
- The puzzles are made up by our code. That means no model has seen them before, but
  they don't cover the full range of BIG-Bench Hard tasks.
