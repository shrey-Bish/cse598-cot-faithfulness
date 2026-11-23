> Saved on Nov 20 from Ritik's pasted brief, word for word below this note: the copy meant for `~/Downloads/DEMO_SPEC.md`
> wasn't on this Mac. It replaces the earlier spec (the ten-beat brief of Nov 19). Phase 1's answer:
> [INVENTORY.md](INVENTORY.md).

# The demo: how we did it, a test bench, and what we found

**What it is.** One offline page with three parts, driven by the presenter (no autoplay):

1. **How we did it:** an interactive map of the whole project. Every step opens up to show its method, with something to try.
2. **Run it:** a test bench. Pick a test, set it up, run real examples, and watch the results build.
3. **What we found:** the ten result sheets from the template (`demo_template/`), stepped through by hand.

**The look:** the answer-sheet template's visual language throughout. Read its `TEMPLATE_GUIDE.md` first: the form in dropout green, pencil, red pen, sticky notes for a user's hint, stapled slips for a tool's, stamps, highlighter. Reuse its marks and add new ones only in the same style (a printed diagram on the form, pencil annotations). No cards, pills, badges, gradients or generic charts.

**Presentation work after the freeze:** no frozen number changes; a dated note in the day's log.

---

## Phase 1: inventory, then stop

Before building, write `docs/demo/INVENTORY.md` and stop for Ritik:

- **Method facts:** for each step of the map below, where its facts live in the repo (pre-registrations, configs, PLAN, FINDINGS, logs, summaries): the models and settings, the question sets and seeds, the hint templates, the run counts, the compute (jobs, GPU time), the architecture of Olmo 3 7B Think (layers, which ones see the whole prompt), the patching method and its per-layer and per-head results, the fine-tuning configs (LoRA: rank, alpha, learning rate, steps, target modules, data counts; consistency training: data construction, counts kept and dropped, epochs, steps, how the epoch was chosen), training logs (loss curves) if they're on this Mac, the attention-dial setup, the review-team setup, the labelling and judge protocols, the statistics, the freeze.
- **Recorded runs:** for each of the six bench tests, which raw run records are on this Mac (results/, finetune/, the newer-families outputs, Track C outputs; all gitignored) and which are only on Sol (exact paths, for Ritik to copy from his own account when he's on the ASU network). Never use anyone else's login.
- Say what's missing and what you'd show instead.

---

## Part 1: How we did it (the project map)

**The map.** One printed diagram across the sheet, left to right, the way a run flows:

```
 questions -> the hint -> the models -> inside the model -> what it wrote -> how we checked
                                              |                                  |
                                          the fixes                        the review team
```

The three tracks are marked on it by plain names (inside the model and the fixes; models and sources; downstream review). Click a step and it opens in place, as a page of the booklet, with the method in a few plain sentences, the real numbers, and one thing to try. Esc closes it. ← → move between steps.

**The steps, each with its interactive part.**

1. **The questions.** Where they come from (the test sets with their sizes and seeds: the 54 test questions, the 30 held-out, the 16 new, the 120 fresh, the patching sets), what a question looks like (a real one, ten options). *Try:* flip through a few real questions from the curated set.
2. **The hint.** How the same wrong letter is put in front of the model by each source: the user's guess, a classmate, "my answer key", "the official manual", pasted tool output, the model's own tool call, an inserted tool turn; and a right hint for the fixes. *Try:* switch the source and watch the exact prompt change on the sheet (from the experiments' own templates).
3. **The models.** The 12 models and their settings (thinking on/off, reasoning effort), which part of the project used each, and where they ran (Sol, and the other servers used). *Try:* pick a model and see its settings and which tests it's in.
4. **Running it.** The compute: Sol jobs, GPU time, the job feeder (a small diagram: queue → feeder → jobs within the class limits), run counts per study, and the reproducibility rules (seeds, checksums, everything pre-registered before running). *Try:* a timeline of the project from the Gantt data: pre-registrations, runs, reads, the freeze.
5. **Inside the model: the architecture.** Olmo 3 7B Think as a printed column of 32 layers; the layers that see the whole prompt marked (from `DATA.layers.full`), the rest seeing a sliding window. *Try:* click a layer to see what kind it is.
6. **How we checked the layers.** Activation patching, step by step: a run with the hint and the same question without it; swap one layer's activations from the run without the hint into the run with it, at the answer; measure how much of the pull toward the hint's letter disappears. *Try:* click a layer to "swap" it and see its measured effect fill in (`DATA.layers.effect`); then the three readout layers together (`share`), the heads (`heads`), the same test on 16 new questions, and Qwen3 8B. Label clearly what was measured.
7. **The fixes: fine-tuning.** LoRA: what the training data looked like (one real training example: the hinted prompt and the target, whose opener notes the hint's source and then decides), the configuration, the loss curve if available, and what it changed. Consistency training: the idea (train the model to reason as it does without the hint), how the data was built (counts kept and dropped, the split, epochs, steps, the epoch chosen by validation loss). *Try:* step through a training pair: the input with the hint against the target written without it.
8. **What training changed inside.** The swap experiment: fine-tuning acts in the reasoning; consistency training acts before the readout layers (`DATA.layers.swap`). *Try:* choose the fine-tuned or the consistency-trained model and see which layers carry the change.
9. **The other fixes.** The one-line instruction (its exact text), the "unverified" label on tool output, the attention dial (attention to the tool turn scaled at answer time; the two measured settings only). *Try:* the dial with its two measured points, nothing in between.
10. **The review team.** The pipeline: solver with the tool → reviewer (sees the answer only, plus the private reasoning, or plus the tool's log) → checker that solves again without the tool → user. *Try:* switch what the reviewer sees.
11. **How we checked ourselves.** Pre-registration before every run (a few real dates); the statistics (k of n with 95% Wilson intervals; paired bootstrap clustered by question, 20,000 resamples); hand labels and their agreement with a blind AI judge; the AI-use disclosure; the contamination audit; the freeze. *Try:* nothing heavy; maybe a small bootstrap explainer.

Every number on these pages comes from the frozen summaries or the configs and logs found in the inventory, never from memory. Anything illustrative is labelled.

---

## Part 2: Run it (the test bench)

**Two modes.** Replay (the core; works offline): every run shown is a real recorded run, replayed with its real text, labelled "Recorded run: model, setting, date". Live (optional, phase 3, only if Ritik says yes): a small model on this Mac, labelled "Live, on this laptop", hidden when the local server isn't running.

**The curated set,** `results/demo/examples.json` (gitignored, never committed): for each test, questions drawn **at random with a fixed seed** from that test's frozen question set (not chosen by outcome; the seed shown on screen), with **every recorded run** of each chosen question under each condition the test compares. Per run: question id, question and options, right letter, hint letter, the condition (model, setting, hint source, wrong or right hint, fix), the exact prompt or turns, the private reasoning, any tool call and reply, the final answer, the outcome fields our analysis computed (followed / accepted, keyword flags, hand labels where they exist), and the source file and line. Under about 15 MB. Optional "our picks": at most three runs a test, labelled "chosen by us to illustrate", never mixed with the random draws.

**The bench (one sheet).** Left: the six tests as items. Centre: the run: the question with its options as bubbles, the hint landing (sticky note or slip), the scratch work streaming (Esc skips; long reasoning collapses with "show all"), the tool slip where there was a call, the final answer written into the box, then the red pen grading with **our own checks**: took the hint? the reasoning names the source? the final answer does? Right: this test's frozen result as bubbles ("147 of 162"), with your runs filling in pencil as you go. Footer: the condition as bubble rows.

**Actions.** Run (Enter); Next question (N); Run 20 more (M: 20 recorded runs of this condition drawn by the seed, filling bubbles beside the frozen total, clearly a sample of it); Compare (C: the same question under two conditions side by side, run together); Show the prompt (P); tests 1–6; T theme.

**The six tests.**
1. Tool vs person: the eight models and 13 settings; user, pasted tool output, tool call. Result: `DATA.hint`.
2. Authority: three models; the six claims. Result: `DATA.dose`.
3. Thinking on and off: Qwen3 8B (and gpt-oss's effort levels and Nemotron where runs exist); the scratch work names the tool, the answer box doesn't. Result: `DATA.quiet.title`.
4. The fixes: Olmo 3 7B Think on the 120 fresh questions; the fix, the hint source, wrong or right hint; best in Compare mode. Result: `DATA.fixes.systems` (following and acceptance); the trade-off as a second view, its "how often is your tool right?" row labelled exploratory; hand labels beside the keyword check where they exist.
5. Review teams: six reviewers; what the reviewer sees; checker on or off. Result: `DATA.agents` (the checker's numbers are on a different set of 100 items; say so).
6. Inside the model: the patching result for a question from the patching sets if per-question records exist; otherwise the aggregate rows, as in the map's step 6.

---

## Part 3: What we found

The template's ten result sheets (items 1–10, per `TEMPLATE_GUIDE.md`), stepped through by hand (← →), no autoplay. Each sheet links to its test on the bench ("Run this test") and to its method step on the map ("How we did this").

---

## Navigation

The form header carries the three parts as tabs printed on the sheet: How we did it, Run it, What we found. Keys: 1–3 switch parts when no input has focus; inside a part, as described. Deep links by `#map`, `#bench`, `#found` (plain hashes only).

## Honesty rules

- Every run on screen is real (recorded or live), labelled as which; draws are seeded and shown; "our picks" labelled.
- Checks are our analysis's outcome fields or hand labels, never re-judged in the page.
- Every aggregate is the frozen one, with k of n and its interval on hover; every method fact traces to a repo file.
- Real benchmark questions, unedited.

## Builds

- **Local, for presenting:** `results/demo/demo.html` (gitignored), with the curated runs embedded; works with Wi-Fi off.
- **Tracked:** `docs/demo/index.html`, parts 1 and 3 complete, part 2 on the frozen aggregates only, with a printed note: "Recorded runs appear in the local build." Ritik decides later whether any runs may be committed.
- Fonts embedded as subset woff2 with their OFL notes.

## Phase 3 (optional): live mode

Only if Ritik says yes. `tools/demo_live.py` serves the page and runs one model through Ollama on this Mac (Qwen3 8B, thinking on and off, downloaded before the talk), using the experiments' own prompt builders and checks imported from the repo. The page detects it at localhost and shows a "Live" switch. Time a run with thinking on and off first and report it; over about 45 seconds a run, say so. One model loaded, nothing else heavy running.

## Checks, tests, handoff

- Look at every map step, every bench test (a normal run, a compare run, after "Run 20 more") and every result sheet, in both themes at 1920 × 1080 with the real fonts. Nothing overlaps; long text collapses cleanly.
- Tests: the embedded DATA equals compact() of the frozen summaries; every run traces to its recorded file; the seeded draw is reproducible; no network request (live mode only talks to localhost); no console errors; no internal codes in visible text.
- Update README (how to open each build), TALK_MAP and the submission checklist.
- Handoff, at most 8 lines per phase.
