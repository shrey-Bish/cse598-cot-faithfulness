# The answer sheet: a template for the demo

This folder is the design template for the project's demo. Four items are built to the finished standard: 1 (the setup), 2 (tool against person), 4 (the quiet answer) and 6 (inside the model). Items 3, 5, 7, 8, 9 and 10 show a placeholder. **Your job is to build those six in exactly the same visual language, using the marks below, and to change nothing in the four reference items except what this guide asks.**

## Files

| file | what it is |
|---|---|
| `style.css` | tokens, the sheet, the form print, and the marks' styles |
| `body.html` | the sheet's skeleton and the three SVG filters (`#pencil`, `#pen`, `#marker`) |
| `app.js` | the marks (functions), the four reference items, the navigation |
| `build.py` | joins the three with the data into one `index.html` (`--offline` drops the web-font link) |
| `data.json` | `compact()` of the frozen summaries (the tag `results-freeze-2026-11-18`); never edit by hand |

## The idea

The whole screen is one optical answer sheet, printed in dropout green. Everything that happens on it is a **mark** someone made: pencil fills a bubble per run of a model, a sticky note or a stapled tool slip brings the hint, a red pen grades and tallies, a highlighter marks what matters, a violet rubber stamp certifies. The audience already knows how to read an exam sheet; that's why it works. **Nothing on the page is a chart widget, a card, a pill, a badge or a gradient.**

## Tokens (in `style.css`)

| token | light: paper | dark: carbon copy | used for |
|---|---|---|---|
| `--paper` | `#F1F4EF` | `#17202A` | the sheet |
| `--print` | `#4E8C6F` | `#6DB394` | everything printed on the form: rules, labels, bubble outlines |
| `--ink` | `#23292D` | `#E6ECE9` | printed statements and body text |
| `--pencil` | `#2E3236` | `#DCE1E4` | pencil fills and pencil handwriting (always with `filter: url(#pencil)`) |
| `--red` | `#D3202E` | `#FF5D62` | the grader's pen: tallies, loops, crosses, margin notes |
| `--canary` | `#F7E15A` | `#E3CD48` | sticky notes and the highlighter |
| `--violet` | `#5B3E96` | `#B39DEB` | rubber stamps only |

No other colors. Never color a bubble fill with anything but pencil.

## Type

- **Archivo** (`--text-font`): printed statements and body text.
- **Archivo Narrow** (`--print-font`): the form's own print: labels, captions, the footer.
- **Nanum Pen Script** (`--hand-font`): anything written by hand, in pencil or red pen.

For the repo, embed the three as subset `woff2` files inside the HTML (`@font-face` with `src: url(data:font/woff2;base64,...)`, Latin subset, with the SIL Open Font License note in a comment), so the page keeps its look offline. Sizes at the 1600 × 900 sheet: statement 46 px (one line, at most about 45 characters), sub-line 23 px (at most two lines), body text at least 21 px, printed labels at least 15 px, red-pen tallies 44–52 px. Sentence case everywhere, no all-caps labels.

## Layout

The sheet is designed at 1600 × 900 and scaled to fit the window (`fit()`), so positions are fixed numbers. Each item calls `statement(no, title, sub)`, which returns `.body`: draw everything inside it, in `.body` coordinates, about **1374 wide and 480–520 tall**. The footer holds at most one row: `choiceRow()` for a choice (answer-sheet bubbles) or `infoRow()` for one printed line. At most two panels per item.

## The marks (`app.js`)

| function | what it draws | notes |
|---|---|---|
| `bubbles(parent, {x, y, n, k, cols, w, h, gx, gy, delay, dur, label})` | `n` capsules; the first `k` fill in pencil in reading order | returns the time the last fill lands, so the next mark can follow it |
| `letterBubble(parent, x, y, letter, {filled, size})` | one answer bubble with its letter | returns `{fill()}` |
| `tally(parent, {x, y, k, n, caption, delay, size, seed})` | the red-pen "k of n", circled, with a printed caption | measures its own text for the loop |
| `penLoop(parent, {cx, cy, rx, ry, delay, seed})` | a hand-drawn red loop, drawn on | |
| `penStroke(parent, points, {delay, color, pencil})` | a hand stroke: cross, tick, arrow, bracket, underline | `color: "--pencil", pencil: true` for a pencil underline |
| `writeText(parent, {x, y, text, size, red, delay, dur, width})` | handwriting that writes itself left to right | pencil unless `red: true` |
| `sticky(parent, {x, y, text, delay, width, size, rot})` | a canary sticky note that lands | the user's hint |
| `slip(parent, {x, y, call, rows, delay, width, rot})` | a stapled tool slip: the call and its reply | the tool's hint |
| `stamp(parent, {x, y, text, delay, rot})` | a violet rubber stamp that thumps down | certifications and labels like "Exploratory" |
| `highlight(parent, {x, y, w, h, delay})` | a highlighter swipe | |
| `panel(parent, {x, y, w, h, title, sub})` | a printed box on the form with a heading | at most two per item |
| `choiceRow(label, options, value, pick, note)` / `infoRow(label, text)` | the footer | choices are bubbles; picking one re-runs the item |

Every timed step goes through `at(ms, fn)`, which runs everything at once when the theme changes or motion is reduced. Don't use `setTimeout` directly.

## Motion

One choreography per item, in reading order, in about 3–4 seconds: the hint arrives (note or slip), the pencil fills, then the red pen grades. The pencil goes first and the pen goes last, every time. No looping animation, no motion that isn't a mark being made.

## Words

- Plain names only (`docs/GLOSSARY.md`); never an internal code.
- The statement is the finding, as a sentence. The sub-line says what you're looking at. Red-pen notes are a grader's words: short ("source?", "didn't follow less").
- Every number comes from `DATA`, never typed. Exact counts appear as "k of n".
- Mark what's illustrative ("Illustrative question, written by us"; "illustrative wording") and what's exploratory (a stamp).

## The six items to build

**3. Mostly, it's the authority.** Sub: "Claim a more official source and the same letter pulls harder." Six rows of bubbles, one per claim, top to bottom: the user's guess (`plain`), a classmate (`classmate`), "my answer key" (`key`), "the official manual" (`manual`), pasted tool output (`pasted`), a tool call (`call`), from `DATA.dose[i]`. Each row: a printed label at the left, then `bubbles()` with `n` and `k` from that row, in a single long strip (for example 2 rows of 81), then a small red-pen tally at the right. Rows fill one after another. The user rows' label is printed; the two tool rows get a small stapled-slip icon. Footer: `choiceRow("Model", ...)` with the three models. Where a model's own tool call is far stronger than any claim (Qwen3 30B Instruct), a red-pen margin note says so, from the data.

**5. Does thinking make it more honest? Not reliably.** Sub: "That was our title question. Three models gave three different answers." Three small panels side by side, each one model: Qwen3 8B (calls the tool, thinking off against on: `DATA.quiet.title.f29.calls_off`, `calls_on`), gpt-oss 20B (follows the tool, low against high effort: `f37.following_tool_real.low`, `.high`), Nemotron 3 Nano (a bare final answer after the tool, off against on: `fb1.off`, `fb1.on`). In each, two bubble strips (before, after), each with its small tally, and the grader's verdict in red pen at the bottom: "moved into the scratch work only", "more thinking, no change", "a little more explanation". Footer: `infoRow` with gpt-oss's reasoning length (`f37_tokens.low` to `.high` tokens).

**7. Olmo's reviewers defer to the tool's log.** Sub: "A checker that solves the question again, without the tool, stops them." Left panel: the reviewer's grading of the 73 wrong tool answers, as a grid of 73 small boxes in which the red pen writes a cross (corrected) or a tick (let through), `k` corrected from `DATA.agents.reviewers[i]` (`answer_only`, `plus_private`, `plus_tool_log`). Right panel: the checker, a violet stamp "Checked without the tool" and the tallies `checker.caught` (53 of 53), `checker.false_alarms` (7 of 45) and `checker.shipped`, with the printed note that these are on a different set of 100 items. Footer: one `choiceRow` for the reviewer (six); the "what it sees" choice (answer only, plus its private reasoning, plus the tool's log) as a second row of bubbles inside the left panel, not the footer. A red-pen margin note: "Only the two Olmo reviewers defer; the other four keep checking."

**8. Every fix is a trade-off.** Sub: "Fixes that resist wrong hints also distrust right ones." The sheet's own graph paper (a fine `--print-soft` grid) with the six non-diluted fixes from `DATA.fixes.systems` (`base`, `prompt_only`, `lora`, `lora_note`, `a40`, `a40_note`; plain names in the glossary) plotted as pencil dots: across, right hints taken (`acceptance`); up, wrong hints resisted (1 − `following`). Each dot labelled in pencil handwriting; a faint pencil line through them. "How often is your tool right?" as a row of 11 bubbles (0%, 10% … 100%) inside the panel: picking one fills it, and the red pen circles the fix that gets the most answers right at that rate (p × `a_C` + (1 − p) × `a_W`). A violet "Exploratory" stamp.

**9. Fine-tuning made answers mention the hint.** Sub: "When it followed a wrong hint, its answer usually said the hint was there. It didn't follow wrong hints any less often." Two panels: fine-tuned and one-line instruction, each 42 answer boxes (small rectangles like the item's answer box); the pencil writes a tick in each box whose answer mentions the hint: `DATA.fixes.l6.lora` (37 of 42), `.instruction` (18 of 42); a tally each; a red-pen note: "didn't follow less". Printed small: hand-labelled; the AI judge that didn't know the model agreed on 82 of 84.

**10. What we learned.** No sub. The grader's comments at the foot of the sheet, three lines in red pen, each with one printed line under it: where a hint seems to come from changes how hard it pulls; final answers hide what the reasoning knew; prompts and training trade resistance for trust, and a checker that solves the question again, without the tool, is what held. Then score boxes like the item box: 12 models; 10,080 runs on 120 fresh questions for the fixes; 4,860 runs on three newer families; 479 answers labelled by hand. The team's names printed, as on a cover sheet.

## Rules

- Change nothing in the four reference items except to fix a bug; match them.
- Check every item at 1920 × 1080 in both themes with the real fonts loaded; nothing overlaps, nothing runs off the sheet, every number is from `DATA`.
- Before you finish an item, remove one thing it doesn't need.
- Tests: `DATA` equals `compact()` of the frozen summaries; no network request in the offline build; no console errors through all ten items; no internal code in the visible text.
