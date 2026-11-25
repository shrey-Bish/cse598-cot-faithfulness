# Template map (Phase A)

Inspected: the official ASU 2026 template and the Markstrat example, both as scratch copies (the originals under
`docs/presentation/final/templates/` were not touched). Scratch renders (80/50 dpi PNGs, contact sheets) are in
`/private/tmp/claude-501/-Users-ritik-Documents-Projects-ODL-cse598-cot-faithfulness/6437843c-727d-4cdd-b96a-b44c54ad56f9/scratchpad/deck_helper1/tpl/`
(`s-01.png` to `s-19.png`; `sheet1.png` = slides 1-10, `sheet2.png` = slides 11-19) and `.../mk/` (`s-1.png` to `s-7.png`).
Positions are inches, (left, top, width, height), on the 10 x 5.625 in slide. Layout numbers are 0-based positions in
the one master's layout list (python-pptx `prs.slide_layouts[i]`); every layout's name is a Google-export code
("CUSTOM_40"), so layouts must be picked by position or by that code, not by a friendly name.

## 1. Size, fonts, colors

- **Slide size:** 10 x 5.625 in (9144000 x 5143500 EMU), 16:9. One slide master, **122 layouts**.
- **Font:** Arial everywhere (the theme's major and minor font; all 92 explicit typeface settings in the layouts are Arial).
- **Theme colors.** The master uses `theme2.xml` ("Simple Light"); `theme1.xml` is a leftover Google default (blue/green
  accents) the master does not use. Confirmed from `theme2.xml`:

  | Slot | Hex | Role |
  |---|---|---|
  | dk1 (text) | 191919 | near-black |
  | lt1 (background) | FFFFFF | white |
  | dk2 | 747474 | mid gray |
  | lt2 | E8E8E8 | light gray |
  | accent1 | FFC627 | gold (also the title/preheader highlight) |
  | accent2 | 8C1D40 | maroon |
  | accent3 | 78BE20 | green |
  | accent4 | FF7F32 | orange |
  | accent5 | 00A3E0 | blue |
  | accent6 | CC2F2F | red |
  | hlink / folHlink | 8C1D40 / 0097A7 | links |

  The brief's five colors (8C1D40, FFC627, 191919, FFFFFF, E8E8E8) are all confirmed. Use RGB values directly on
  new shapes (what `diagram.py` does) so nothing depends on which theme a viewer resolves.
- Type sizes in the layouts: slide titles 30 pt bold with gold highlight; title-slide 48 pt; key numbers 40-48 pt;
  body 18 pt (12 pt for captions); quote 36 pt; "Thank you" title and subtitle highlights as below.

## 2. Layouts used by the template's slides

All the "looks" the brief names live **on the layouts** (backgrounds, the network image, the dark panel, the ASU logo,
quote marks), except the photographs on slides 14 and 18, which are pictures dropped into a picture placeholder on
the slide. Adding a slide from the layout therefore gives the look with nothing to copy.

| Template slide | What it is | Layout (pos, code) | Placeholders (idx, type; position) | Look lives in |
|---|---|---|---|---|
| 1 | Title page of the template ("2026 Official ASU presentation template") | 10, CUSTOM_23_..._2_1_2_1 | pic 2 (0,-0.01,10.01,3.27); title 0 (0.38,2.51,9.25,1.24; 48 pt); body 1 (5.48,4.23,4.15,0.55); subtitle 3 (0.38,1.88,4.58,0.63; 14 pt bold, gold highlight) | layout: a title text box over the picture area (a rectangle at 0.37,2.51,9.26,1.24) and the ASU logo (0.27,4.66,3.53,0.76); the picture is a slide placeholder |
| 2, 5 | Instruction pages ("What's new", "More layouts") | 57 and 41 | title/body/subtitle placeholders plus tables and screenshots | slides (hand-placed) |
| 3, 4, 6, 7, 19 | Hand-built pages on the plain layout | 2, CUSTOM_35 (no placeholders; only an off-slide guide mark at -0.38,4.75) | none | slides (hand-placed shapes) |
| **8** | **Network-background title** | **9, CUSTOM_23_..._2_1_2** | title 0 (0.37,0.35,9.26,2.94; 48 pt; anchored bottom); subtitle 2 (0.37,3.27,4.25,0.48; 14 pt bold, gold highlight); body 1 (5.48,4.23,4.15,1.07; 12 pt, for names/date) | layout: the gray network picture (0,0,10,3.75) and the ASU logo (0.27,4.66,3.53,0.76) |
| 9 | Presenter bio | 65 | picture, name, "Today's presenter" label, bio | layout |
| 10 | Agenda | 12 | title left (0.37,0.35,3.41,4.95); body right (4.59,0.35,5.04,4.95); gold rule | layout |
| 11 | Section title, full gold | 25, CUSTOM_19_1_2_1 | center title (0.37,0.35,9.17,4.08); subtitle 1 (0.37,4.4,9.26,0.38); ASU logo (0.22,4.88,0.86,0.57) | layout: gold fill via bg, the pattern strip, the small logo |
| **12** | **White "Slide title" with the gold highlight** | **4, CUSTOM_40** | title 0 (0.37,0.35,9.26,0.48; 30 pt bold, gold highlight, anchored top, 90% line spacing); body 1 (0.37,1.2,9.26,3.59; 18 pt, maroon bullet, gray lower levels) | layout. Also holds a 0.00-wide guide mark off-slide at x < 0 and the tiny copyright line at (8.76,5.51) |
| **13** | White two-column with a preheader | 39, CUSTOM_22_..._3 | subtitle 3 (0.37,0.79,9.26,0.18; 12 pt bold black on gold highlight); title 0 (0.37,0.35,9.26,0.48); two bodies 1 and 2 (0.37,1.2,4.58,3.58) and (5.05,1.2,4.58,3.58) | layout. Quirk: slide 13's own title placeholder has an orphaned idx (4294967295), so in the template it renders small and plain; a slide created from the layout gets the proper 30 pt gold-highlighted title |
| **14** | **Black half with an image** | **61, CUSTOM_23_..._3_1** | title 0 (0.37,0.35,5.0,0.63; 30 pt bold, gold, anchored bottom); body 1 (0.37,1.2,4.68,3.59; 18 pt white); picture 2 (5.51,0,4.49,5.62) | layout: 191919 background, a left strip image (0,0.01,0.21,5.63). The photograph is a picture dropped into the picture placeholder on the slide (an empty picture placeholder shows nothing) |
| 15 | Subsection title on a maroon band with a pattern | 32, CUSTOM_22_1_1_1 | title 0 (0,1.97,9.63,1.69); subtitle 1 (0.38,1.42,4.63,0.65) = the "preheader of the parent section" | layout: full-slide pattern picture and a maroon band (0,1.97,10.02,1.69) |
| **16** | **Highlight key numbers** | **78, CUSTOM_25_2** | three columns: number (idx 0/4/5 at x 0.38, 3.67, 6.98; y 1.39, 2.64 wide, 1.43 tall; 40-48 pt, gold highlight), caption (idx 1/2/3; y 2.83; 14 pt bold), source line (idx 6/7/8; y 3.38, 1.4 tall; 12 pt); slide title idx 9 (0.37,0.35,9.26,0.48) | layout (ASU logo at 8.84,4.88,0.86,0.57 sits just above the safe strip) |
| **17** | **Dark statement** (quote slide) | **99, CUSTOM_23_..._6_1_2** | title 0 (1.23,0.98,7.63,3.81; 36 pt gold, centered); attribution 1 (1.23,4.23,3.82,0.55) | layout: 191919 background and the two large gray quote marks |
| **18** | **Thank you** | **62, CUSTOM_23_1_1_1_1_2_1_1_1_2** | picture 2 (0,0,4.49,5.62); title 0 (4.95,0.35,4.68,0.62; gold highlight); body 1 (4.95,1.2,4.68,3.58; 18 pt, first line bold) | layout: a right-edge pattern strip. The flower photograph is a picture in the placeholder on the slide |
| 19 | End logo | 2, CUSTOM_35 | none | slide: one picture (3.0,2.28,4.13,1.14) |

Other templates worth knowing about: 122 layouts exist; the ones above are the core set. List them with
`[(i, l.name) for i, l in enumerate(prs.slide_layouts)]`.

## 3. The content-safe zone (template slide 6)

Slide 6's own text, quoted:
- "Green = Content safe zone" and "This only applies to slides that will be presented live (in person or online) or
  recorded and shared".
- "Red = Reserved for accessibility overlays" and "Avoid placing important text in this area of the slide to
  accommodate live transcription and Closed Captions overlay."
- "To ensure Closed Captions and live transcription overlays do not obscure meaningful content, use this guide to
  inform where you place critical text on your slides." and "For slides intended for independent up close reading
  review only: Text can safely extend beyond this area of the slide."
- "If using layout guides, the reserved area is indicated with a dotted red line for your reference."

**Geometry (read from slide 6's shapes):**
- Safe (green) area: (0, 0, 10, 4.78). The reserved (red) strip is **y = 4.78 to 5.625 in: the bottom 0.845 in**, full width.
- Dotted line at y = 4.78 (the template's layouts end their content placeholders at about 4.78-4.79).
- Slide 6 also draws a 0.12-in strip down each side (x < 0.12 and x > 9.88). The template's own placeholders use 0.37 in
  side margins (9.26 in content width), so keep to 0.37 in at left and right.
- Rule for Phase B: nothing important below y = 4.75 in (at 1920 x 1080: below y = 912 px); the burned-in video captions
  sit just above that line. The layouts' own logo/footers in the strip (small copyright line, corner logos) are fine.

## 4. What template slides 1-7 and 19 say (all removed in the deck)

- 1: the template's cover ("Prepared by ASU Enterprise Brand Strategy and Management for enterprise-wide distribution and use";
  access limited to asu.edu addresses; a link to the ASU presentation toolkit).
- 2: "What's new in the 2026 template": streamlined layouts, flexible titles/subtitles/preheaders, layouts grouped by
  common use, more photo-based layouts, more agenda/timeline/featured layouts in the toolkit.
- 3: section page "How to use this template" ("Getting started").
- 4: "Making an editable version of this template": make a copy, new from template, import theme, download PowerPoint.
- 5: "More layouts, more tools, more graphics": layouts in the file's Layout menu; the toolkit's extra layouts; quick
  links (messaging, photos, interactive tools, how to embed video, layout guides, color palette, brand standards).
- 6: the safe-zone guide (section 3 above); it is "Revised for 2026".
- 7: section page "Basic presentation template" (points to slide 7 for more layouts and to the Enterprise Brand guide).
- 19: the end slide: only the ASU Arizona State University logo, centered. (The brief removes it; our closer is slide 8.)

## 5. The Markstrat deck's gold "preheader"

Markstrat slides 2-7 use a layout ("Cover Intro Option 2") with a small gold-highlighted line **above** the title:
- Text: sentence case, e.g. "Markstrat Taught us…" (slide 2), "1. Applying the 3Cs", "2. Segmentation", "3. Marketing Mix".
- **Arial, 16 pt, bold, black (000000) text on a gold (accent1 = FFC627) highlight**; not all caps; left-aligned; line
  spacing 115%; no insets.
- Position: (0.36, 0.28), 8.21 wide, 0.26 tall, i.e. top-left, about 0.1 in above the title's top edge (title at about
  0.66-0.73). The title under it is **25-30 pt in maroon** (accent2), not highlighted, 9.19 in wide.
- Mapping to the ASU template: its own equivalent is the **subtitle placeholder** of CUSTOM_22_..._3 (template slide 13, layout
  39), a 12 pt bold black-on-gold line, which sits at y = 0.79 **below** the title; slide 15's subtitle is the maroon
  band's "preheader of the parent section". Markstrat puts the label above the title and at 16 pt; to copy that, add
  a text box (Arial 16 pt bold, 191919, gold highlight, at 0.37, 0.28) and start the title at about 0.66. Phase B
  should use it sparingly (backup divider, and as a section tag such as "Finding, part 1"); the brief only asks for the style.
- Markstrat is otherwise a table of lessons in long text, maroon type on white with a large ASU logo bottom-left; do not copy.

## 6. How Phase B should build slides

**Create the working file.** Copy the template to the deck's path (never save over the original). Delete slides 1-7 and 19
and keep the masters. With python-pptx, which `diagram.py` already does (`open_template_copy`):
`for sld in list(prs.slides._sldIdLst): prs.part.drop_rel(sld.get(qn("r:id"))); prs.slides._sldIdLst.remove(sld)`; also
drop slides 9-18 (the sample slides) because the planned slides come from layouts. The 122 layouts and the master stay.
(The draft pptx is 8 MB because the layouts carry their pictures; the deck's 50 MB budget is fine.) Then
`prs.slides.add_slide(prs.slide_layouts[i])` for the layouts below, fill the placeholders, delete any unused empty
placeholder (an empty body shows only in edit view, but delete it so the file validates cleanly).
Photographs go in the picture placeholders (14/18 styles), set alt text on every picture and video.

| Planned slide | Layout to use | Notes |
|---|---|---|
| 1. Title | 9, CUSTOM_23_..._2_1_2 (template slide 8, network background) | Title 48 pt wraps to 3-4 lines for our title; set about 34-36 pt. Subtitle placeholder = the question line; body placeholder = course, names, date. |
| 2. The question and why it matters | 61, CUSTOM_23_..._3_1 (slide 14, black half with an image) | Left: the scenario, 18 pt; right: the illustrative example card as the picture (4.49 x 5.62 in), labelled "illustrative". Alternative: 4, CUSTOM_40 with the card as a picture. |
| 3. How we tested (diagram) | 4, CUSTOM_40 (slide 12, white "Slide title") | The simple diagram from `diagram.py` (6 boxes) plus the four "why" lines; remove the body placeholder or use it for the why lines at 14 pt. |
| 4. The finding: tools pull harder, and the answer goes quiet | 4, CUSTOM_40 for two figures; or 39, CUSTOM_22_..._3 (two-column) | Layout 78 (CUSTOM_25_2, "Highlight key numbers") is the natural base for the big numbers (1 of 162 vs 147 of 162; 141 of 145 vs 0 of 143) if the figures move to the backup. |
| 5. See it happen (video) | 4, CUSTOM_40 | Title as a claim, the video filling the content area (up to y = 4.75), poster frame set, caption above the safe strip. |
| 6. What we'd tell a team deploying it | 4, CUSTOM_40 (rows of icon + text) or 39 (two-column) | Four recommendations, each with its number; the trade-off figure marked exploratory. |
| 7. Where this holds, and what we don't know | 39, CUSTOM_22_..._3 (two-column: "applies to" / "unknown") | Its preheader line holds "Limits". |
| 8. Thank you | 62, CUSTOM_23_..._2 (slide 18) | Title "Thank you" (gold highlight), body "Questions" + repo link + three names; the template's photo or one of ours in the picture placeholder (alt text). |
| Backup divider "Backup: for questions" | 25, CUSTOM_19_1_2_1 (slide 11, gold section) or 32, CUSTOM_22_1_1_1 (slide 15, maroon band) | Use 32 with the preheader "Backup" if a quieter divider is wanted. |
| B1-B8 | 4, CUSTOM_40 for all; 78, CUSTOM_25_2 for B1's three numbers; 39 for B2 or B5 | B7 = the full diagram (`draw_full`). The dark statement layout 99 (CUSTOM_23_..._2, slide 17) is available for one optional, short line (for example the title question's answer, "Mixed") if a slide needs a pause; not budgeted in the 6:00. |

Rules that came out of inspecting the template:
- Titles are 30 pt bold with the gold highlight, one text line at about 40 characters; claim titles longer than that wrap
  (the highlight follows each line), so set 22-24 pt explicitly for long claims, as `diagram.py` does, and move the
  content top down (about 1.1-1.4 in).
- Do not add lines under titles (the template has none; the diagram draft has none).
- LibreOffice renders these layouts fine, but not video playback (Ritik checks in PowerPoint).

## 7. Conflicts between the template and the brief

- **None blocking.** Colors, Arial, 16:9 at 10 x 5.625, the layouts named in the brief, and the safe zone all match.
- The brief says "the white Slide title with the gold highlight (12/13)". Slide 12's layout (4) has the gold-highlighted 30 pt title;
  slide 13's sample renders a small plain title because of an orphaned placeholder, and its gold element is the 12 pt
  subtitle. For the highlighted claim title use layout 4; layout 39 gives the subtitle line plus two columns.
- The brief's design rule "at least 14 pt body": the template's own captions are 12 pt (layout source/caption text) and
  its footer copyright is about 5 pt; our text should stay at 14 pt or more, with 10 pt only for captions
  (the full diagram, B7, uses 10 pt for small specifics, which the brief allows).
- The template's body bullets are maroon with 18 pt text; the brief's "no text-only slides" still needs a visual on every slide.
- The template's picture layouts (14, 18) need a picture; an empty picture placeholder shows nothing on the slide but a
  hollow frame in edit view. Fill or delete.

## 8. Diagram facts (every number on the diagram, with its source)

Sources: `03_METHODS.md` = `docs/presentation/pack/03_METHODS.md`; `02_NUMBERS.md` = `docs/presentation/pack/02_NUMBERS.md`;
`method.json` = `cot-disclosure/tools/demo_template/method.json`.

| On the diagram | Fact | Source |
|---|---|---|
| Simple: "12 open models", "Thinking on or off" | 12 models: eight answer, four review; thinking on/off for Qwen3-8B, Gemma, Nemotron (Granite on only; Olmo 3 7B Think always on; gpt-oss by effort) | 03_METHODS.md section 3 ("The 12 models and their settings"; count from `method.json` key `models`) |
| Simple: "Multiple choice", "Fixed, seeded sets" | Every question multiple choice (letters A-J); seeded sets (seed `e2-20261103` for the 120; run seed 20261005) | 03_METHODS.md section 1 and "Other seeds and settings" |
| Simple: "Same wrong letter", "Source swapped", "Wrong or right" | Only the hint's source changes; wrong hint is never the correct letter; correct-hint arms exist | 03_METHODS.md section 2 |
| Simple: "95% intervals", "Paired by question", "Rules written first" | 95% intervals; paired bootstrap by question (each resample draws questions with all their runs); decision rules written before the data (brief section 2; the pre-registration log) | 03_METHODS.md; `method.json` key `checking.bootstrap` (`paired_by_question`) |
| Full: "54 test questions, 3 runs each" | 54 = 24 puzzles + 30 MMLU-Pro; 3 runs per question (162 runs a condition) | 03_METHODS.md section 1, row "The 54 test questions" |
| Full: "30 held-out" | 30 MMLU-Pro held-out questions (31 runs a question) | 03_METHODS.md section 1, row "The 30 held-out questions" |
| Full: "120 fresh" | 120 MMLU-Pro fresh questions (12 runs a question) | 03_METHODS.md section 1, row "The 120 fresh questions" |
| Full: "12 open models (8 answer, 4 review)" | Eight models answer; four more are reviewers | 03_METHODS.md section 3 |
| Full: "352 GPU-hours on Sol" | 352.47 GPU-hours, 271 GPU jobs on Sol (one account) | 03_METHODS.md section 4; `method.json` key `running.gpu_total` |
| Full: "paired bootstrap by question, 20,000 resamples" | 20,000 resamples (seed 0) | `method.json` key `checking.bootstrap.resamples`; 03_METHODS.md |
| Full: "95% intervals" | 95% intervals | 03_METHODS.md; brief section 2 |
| Full, Inside the model: "Olmo 3 7B Think, 32 layers" | 32 decoder layers; pinned revision d97e442d... | 03_METHODS.md section 3; `method.json` key `arch.layers` |
| Full, Inside the model: "three layers carry 0.90 [0.85, 0.96] of the hint's effect" | share of the drop at the takeover held by layers 15, 19, 23 (19 cuts, 9 questions): 0.90 [0.85, 0.96] | 02_NUMBERS.md, row N39 (also N92) |
| Full, Inside the model: "Activation patching" -> "The readout layers" | method and result names | 03_METHODS.md section 6 (activation patching); 02_NUMBERS.md N39/N92 |
| Full, The fixes: five fixes (instruction, "unverified" label, fine-tuning, consistency training, attention dial) | the fixes tested | brief section 2 and `docs/presentation/pack/01_STORY.md`; 02_NUMBERS.md rows for each fix |
| Full, The fixes: "30 held-out and the 120 fresh questions, with wrong and right hints" | the 30 (Gate 3's first test) and the 120 (powered test set; 6 wrong-hint, 4 correct-hint, 2 no-hint runs a question) | 03_METHODS.md section 1 |
| Full, The review team: "solver -> reviewer -> checker"; "100 fresh items" | the review team's 100 fresh items (60 MMLU-Pro + 40 puzzles; seed `c15-20261029`) | 03_METHODS.md section 1, row "The review team's 100 fresh items" |

Not on the diagram, on purpose: the 53-item first review test, the 16 new questions, the layers' numbers beyond 0.90, any
model name other than Olmo 3 7B Think, and every internal code.

If Ritik changes any figure on the diagram, change `cot-disclosure/tools/deck/diagram.py` (the strings in `draw_simple`
and `draw_full`), then rebuild with
`.venv/bin/python cot-disclosure/tools/deck/diagram.py <template copy>.pptx <out>.pptx`.
