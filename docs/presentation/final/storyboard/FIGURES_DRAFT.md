# Draft figures (Phase A storyboard)

Script: `cot-disclosure/tools/deck/figures.py` (`../.venv/bin/python tools/deck/figures.py`; `plotted()` returns every
plotted row with its source and key path, for Phase B's test against 02_NUMBERS). Every interval is a 95% Wilson interval
computed from k of n; the script asserts it equals the summary's stored Wilson bounds wherever one exists (all did).
PNGs are 300 dpi at these drawn sizes (inches): tool_vs_user 8.2 x 5.0, reasoning_vs_answer 8.0 x 4.4, tradeoff 6.6 x 4.3,
checker 8.0 x 3.6. Labels are 14 pt at that size, so on the slide each figure must be placed at about that width or
larger. Slide 4 holds two of them, so they will have to shrink or be split (open question 1).
Paths below are under `cot-disclosure/results/summaries/`. TRACKB = `trackB/trackB_report.json`, B20 = `trackB/b20_report.json`.

## 1. fig_tool_vs_user.png (slide 4, part 1: "tools pull harder")
Dot plot, two dots per model joined: user gives the wrong letter (gold) vs tool gives it (maroon circle = the model's own
call, diamond = inserted tool turn). Sorted by tool rate, Instruct on the bottom row, annotated "1 of 162 / 147 of 162".
Following = picked the wrong letter, answered runs. Path = `<setting>/channels/<channel>/following` ({k, n, wilson}).

| model (tool channel) | user | tool | finding | key path prefix |
|---|---|---|---|---|
| Qwen3 30B Instruct (own call) | 1 of 162 | 147 of 162 | F16 | TRACKB budget_32768/voyager \| qwen3-30b-a3b-instruct-2507 \| thinking=None/channels |
| Qwen3 30B Thinking (own call) | 3 of 162 | 54 of 162 | F15 | ...voyager \| qwen3-30b-a3b-thinking-2507 \| thinking=None |
| Olmo 3 7B Think (inserted turn) | 13 of 162 | 46 of 157 | F17 | ...voyager \| olmo3-7b-think \| thinking=None |
| Qwen3-8B thinking on (own call) | 16 of 162 | 143 of 162 | F29 | ...sol_vllm \| qwen3-8b \| thinking=True |
| Qwen3-8B thinking off (own call) | 19 of 159 | 40 of 162 | F29 | ...sol_vllm \| qwen3-8b \| thinking=False |
| Gemma 4 on (inserted turn) | 3 of 162 | 37 of 145 | FB1 | B20 gemma-4-26b-a4b-it/settings/on/budget_32768/secondary/channels |
| Gemma 4 off (inserted turn) | 7 of 162 | 60 of 162 | FB1 | ...settings/off/... |
| Nemotron 3 on (inserted turn) | 4 of 160 | 121 of 156 | FB1 | B20 nemotron-3-nano-30b-a3b/settings/on/... |
| Nemotron 3 off (inserted turn) | 63 of 162 | 162 of 162 | FB1 | ...settings/off/... |
| Granite 4.2 (own call, thinking on only) | 8 of 157 | 156 of 162 | FB1 | B20 granite-4.2-8b/settings/on/... |

Channel keys: user, tool_real (own call), tool_injected (inserted turn). Intervals: see `plotted()` (e.g. Instruct user
[0, 3%], tool [85, 94%], matching F16).
- **Not verbatim in FINDINGS:** FB1's table gives user/tool counts only for its readings (e.g. "3/162, 37/145" Gemma on;
  "63/162, 162/162" Nemotron off), so those match; the Qwen3-8B user counts (16, 19 of 159-162) are as F29 states. Gemma off
  "7, 60 of 162" and Granite "8/157, 156/162" appear in the FB1 table too. I found no number here that is absent.
  The intervals themselves are not printed in FINDINGS for the FB1 rows or F29; they come from the summaries' stored Wilson.
- **gpt-oss-20b:** left out (no decision, F37); I did not grey it in. Add one footnote on the slide: "gpt-oss-20b: reported, no decision".
- Qwen3 30B Thinking's tool rate is its call rate (it followed in 54 of 54 calls, F15); a slide line may need to say so.
- Open: 10 rows is dense for a half slide. Option: keep 6 rows (three decided Track B models + Qwen3-8B on + Gemma + Granite).
  Also the claim wording "decided in the five Track B models and clear in all 10 readings of the newer families" is the slide's, not the figure's.

## 2. fig_reasoning_vs_answer.png (slide 4, part 2: "the answer goes quiet")
Paired horizontal bars: private reasoning (maroon) vs final answer (gold) naming the tool; Wilson whiskers; annotation on 0 of 143.

| row | reasoning | final answer | finding | source and key path |
|---|---|---|---|---|
| Qwen3-8B thinking on, own call | 141 of 145 (runs that called) | 0 of 143 (runs that followed) | F29 | TRACKB budget_32768/sol_vllm \| qwen3-8b \| thinking=True/channels/tool_real/mention_private_when_called ; .../mention_final_when_followed |
| Qwen3 30B Thinking, own call | 54 of 54 (called) | 3 of 54 (followed = called) | F15 | TRACKB .../voyager \| qwen3-30b-a3b-thinking-2507 \| thinking=None/channels/tool_real/mention_private_when_called ; mention_final_when_followed |
| Gemma 4 thinking on, inserted turn | 138 of 145 | 24 of 145 | FB1 | B20 gemma-4-26b-a4b-it/settings/on/budget_32768/secondary/channels/tool_injected/mention_private ; mention_final |
| Gemma 4 thinking off, inserted turn | none exists (no private reasoning) | 127 of 162 | FB1 | B20 .../settings/off/.../tool_injected/mention_final (mention_private k=0, n=0) |

- Gemma's 127 of 162 is the keyword "names the tool" over **all answered runs in the inserted-tool-turn channel with
  thinking off** (FINDINGS_B "Reported per model", "Gemma 24 of 145 on, 127 of 162 off"), not only runs that followed. Stated on the slide this way.
- **Not verbatim in FINDINGS/FINDINGS_B:** Gemma on's reasoning bar, 138 of 145 (in b20_report.json only). FINDINGS_B states only 24 of 145.
  Drop that row's reasoning bar if you want strictly verbatim numbers. (It is in the same JSON as the quoted 24 of 145.)
- Denominators differ by design (called vs followed), as FINDINGS states them; label them on the slide.
- Granite (own call) would also fit (private 162 of 162, final 0 of 162 in b20_report.json); FINDINGS_B gives only the final "0 of 162", so left out.
- The three "thinking on" bars use different tool channels (own call vs inserted turn); the sublabels were dropped from the drawing
  for space, so the slide needs a footnote naming which rows are own call.

## 3. fig_tradeoff.png (slide 6, small figure; EXPLORATORY)
Expected correct answers = p x (correct when the tool is right) + (1 - p) x (correct when the tool is wrong), two lines, with
"Exploratory (post hoc)" on the figure. Crossover marked with its interval (grey band). Source `trackA/gpu/a39/tradeoff_e2.json`
(120 questions, answered runs, tool channels), finding F41/F44 context, FINDINGS story item 7, REPORT section 7.

| point | k of n | key path |
|---|---|---|
| Consistency training, tool wrong (p = 0) | 285 of 466 | crossings/answered/a40/a/a_W_kn |
| Consistency training, tool right (p = 1) | 347 of 459 | crossings/answered/a40/a/a_C_kn |
| One-line instruction, tool wrong | 251 of 476 | crossings/answered/a40/b/a_W_kn |
| One-line instruction, tool right | 431 of 476 | crossings/answered/a40/b/a_C_kn |
| crossover p* | 0.36 [0.22, 0.50] | crossings/answered/a40/p_star, .../interval |

- Whiskers at the ends are Wilson (not drawn for the line in between). The line is the formula, not measured at intermediate p.
- Matches REPORT ("a_W 61.2 against 52.7, a_C 75.6 against 90.5", "0.36 [0.22, 0.50]"). The crossover's y value (about 66%) is read off the lines and not quoted anywhere.
- Open: "Consistency training" is the plain name for the A40 model (GLOSSARY); the figure says nothing about the 1-run-per-system limit; put it in the slide text.

## 4. fig_checker.png (slide 6, optional)
Left: wrong tool answers stopped. Right: false alarms on good lookups. Different item sets in the left panel (checker on 100 fresh
items, reviewers on C4's 73 cases), stated here; the slide should say so.

| bar | k of n | finding | source and key path |
|---|---|---|---|
| Independent checker, stopped | 53 of 53 | F24 | trackC/team_c15_summary.json by_kind/fresh/by_team_model_variant/tool \| olmo3-32b-instruct \| plus_tool_log/caught |
| Checker false alarms, good lookups | 7 of 45 | F24 | same prefix /good_lookups/false_alarms |
| Olmo reviewer, answer only, corrected | 59 of 73 | F18 | trackC/team_c4_summary.json by_team_model_variant/tool \| olmo3-32b-instruct \| answer_only/reviewer_alone/corrects_wrong_solver |
| Olmo reviewer + tool's log, corrected | 3 of 73 | F18 | same, plus_tool_log |

- Note: C15's own table-level false-alarm count over all 100 items is "7 of 47" in the by_team_model_variant block (a different denominator);
  FINDINGS quotes 7 of 45 (good lookups only), which is what is drawn.
- Reviewer + log is the Olmo 3.1 32B reviewer; the checker is the pipeline with that same reviewer (plus_tool_log). Say so.

## Design problems left
- Fig 1 is dense (10 rows plus two count columns); Fig 4's two panels use different item sets.
- Fig 2's annotation arrow into the 0 of 143 bar is short (the bar has zero length); fine, but could be a plain label.
- Fig 3's lines are linear by construction; the slide should say "expected, by formula".
- Sizes: if a figure sits at half slide width (5 in) its 14 pt text becomes about 9 pt; plan layouts at the sizes above or split slide 4.
