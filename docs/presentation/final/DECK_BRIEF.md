# The final presentation: brief (Group 10)

Read all of this before doing anything. Save a copy as `docs/presentation/final/DECK_BRIEF.md`.

---

## 0. The requirements (from Canvas, Nov 24)

- **Format:** one PowerPoint file (.pptx), uploaded to Canvas by **Monday, Nov 30**. That file is final. The teaching team downloads it and plays it **on their own machine**: no live demo, no internet, no laptop of ours.
- **The demo:** "If you'd like to show your system working, record a short demo and embed the video directly in your PowerPoint."
- **When:** Thursday, **Dec 3**, Group 10 presents **first**. All three members present.
- **Length:** **6 minutes of talk, then 2 minutes of Q&A.** The course's suggested split:
  - about **1 minute:** the question and why it matters;
  - about **1 minute:** how we tested it;
  - about **2 minutes:** our strongest finding and the evidence behind it;
  - the last **2 minutes:** what we'd tell a team preparing to deploy the system, and where our results have limits.
- **The rubric:**

  | Criterion | Points | What earns it |
  |---|---|---|
  | Technical soundness | 7 | The evaluation is designed to answer the question; we explain what we tested, how, and **why** the data, conditions, metrics and comparisons were appropriate |
  | Quality and interpretation of results | 5 | The main finding is supported with concrete evidence; we explain what the results show **and where they're uncertain** |
  | Deployment framing and takeaways | 4 | Why the finding matters in real use, and a practical recommendation that **follows from the evidence** |
  | Presentation clarity | 2 | Organized, easy to follow, **within six minutes**; slides and demo help the audience understand the main finding |
  | Q&A | (2) | Direct, accurate answers that draw on the evaluation and acknowledge what remains unknown |

- **Past feedback:** at the progress presentation we lost marks on "quality of preliminary results". This time every result on a slide carries its number, its n, its interval, its comparison and one honest limit (the checklist in §9).
- **The report** (due Dec 10, NeurIPS format, 1–3 pages) is **not** part of this brief. Presentation first.

## 1. Rules

- **The freeze holds** (tag `results-freeze-2026-11-18`): no number changes. Every number comes from `docs/presentation/pack/02_NUMBERS.md` or FINDINGS, with its n and interval. New figures are drawn from the frozen summaries only.
- **Plain names on every slide** (`docs/GLOSSARY.md`); no internal codes (F41, A40, E2…) anywhere visible. Codes may appear in speaker notes and the prep guide.
- **Use FINDINGS' wording, including the corrected story (Nov 23 log):**
  - Authority explains the tool's pull for **pasted** tool output.
  - Gemma names the tool in **127 of 162** final answers with thinking off.
  - Qwen3 8B replicates with **its own** layers (21, 22, 29) at **0.70**.
  - Fine-tuning is candid while following wrong hints **no less than the one-line instruction** (it does follow fewer than no fix).
  - **Don't say "all 13 settings"** for tool vs user: gpt-oss's test was reported without a decision (F37). Use FINDINGS' own wording: decided in the five Track B models (Gate 2) and clear in all 10 readings of the three newer families (FB1).
- **Exploratory results** (the trade-off's crossover) are said to be exploratory, on the slide.
- The team reviews and owns every word. AI use is disclosed in the report's note.
- Work as usual: dated note in today's log; at most 2 helpers; push `trackA-nosol` and `main`; no AI attribution.

## 2. The spine (the six-minute story)

**The question.** AI systems that use tools (search, lookups, retrieval) increasingly reason in a "thinking" mode before answering. When a tool returns a wrong answer, does the model follow it? And does its reasoning, or its final answer, tell the user why? Do thinking modes make that reasoning more honest?

**How we tested** (the technical-soundness slide; each choice with **why**):
- **Same question, same wrong letter; only the source changes:** the user's guess, a stronger claim ("my answer key", "the official manual"), pasted tool output, or the model's own tool call. *Why:* this isolates the source's effect from question difficulty. The comparison is paired by question.
- **Multiple-choice questions** (MMLU-Pro and our own puzzles; fixed, seeded sets; fresh questions for the fixes). *Why:* following the hint is unambiguous (the hint's letter picked), and fresh questions mean no tuning to the test.
- **Three measures:** took the wrong hint? reasoning names the source? final answer names it? Plus **right hints**, to measure the cost of a fix that distrusts tools. *Why:* honesty and over-correction are both visible. The keyword measure was checked against hand labels.
- **12 open models, thinking on and off**, run on ASU's Sol GPUs (352 GPU-hours on Ritik's account).
- **Statistics:** 95% intervals; differences by a paired bootstrap, clustered by question (20,000 resamples). **Every decision rule was written down before its data.**
- **Three levels:** the model's behavior; inside the model (activation patching); a review team downstream (solver → reviewer → checker).

**The strongest finding** (one finding, two parts, with uncertainty):
- **Part 1, tools pull harder than people.** The same wrong letter, from a tool rather than the user, is followed far more often. Qwen3 30B Instruct: the user's guess 1 of 162; its own tool call 147 of 162. This holds wherever the test was decided (FINDINGS' wording). For pasted tool output, much of the pull is the claimed authority: a user citing "the official manual" pulls about as hard.
- **Part 2, and the answer the user reads goes quiet.** After a tool call, Qwen3 8B with thinking on names the tool in its private reasoning in 141 of 145 runs, and in its final answer in 0 of 143. Qwen3 30B Thinking: 54 of 54 against 3 of 54. **The exception:** Gemma names it in 127 of 162 with thinking off.
- **The title question's answer: mixed.** Thinking on moved the tool into Qwen3 8B's private reasoning, but not into its answer, and it followed the real tool call more (+64 [+51, +75], because it calls the tool far more). gpt-oss: more effort, no change detected. Nemotron: a little less bare with thinking on (−14 [−19, −9]).
- **Inside the model (one line, or a backup slide):** three layers of Olmo 3 7B Think carry about 90% of the hint's effect (0.90 [0.85, 0.96]); Qwen3 8B, its own three, about 70%.

**What we'd tell a team deploying a tool-using model** (each recommendation follows from a number):
1. **Don't treat the final answer as a record of why.** It rarely names the tool (0 of 143). Log the tool's provenance outside the model, and where private reasoning is available, monitor that instead (141 of 145), though this isn't universal across models.
2. **Don't rely on a label or a prompt line to fix it.** Marking tool output "unverified" had no effect (−1 [−7, +4]). Asking the model to cite its sources made the answer name the tool more often, but it followed the tool no less.
3. **Put an independent check before acting on a tool-backed answer.** A checker that re-solves without the tool stopped 53 of 53 wrong tool answers (on a separate set of 100 items), at the cost of 7 false alarms out of 45 good lookups and a second model call. Reviewers that only read the work aren't enough: an Olmo reviewer shown the tool's log corrected 3 of 73 wrong answers (59 of 73 from the answer alone).
4. **If you fine-tune, choose by how reliable your tool is.** Consistency training cut wrong-hint following to 84 of 694 (against 237 of 713 for the instruction), but took right hints less often (347 of 459 against 431 of 476). By our exploratory estimate, it only gives more correct answers when the tool is right less than about 36% of the time [22%, 50%].

**Limits** (where it applies; what remains uncertain):
- Multiple-choice questions; one tool format (an answer-key lookup).
- Open models up to about 32B parameters.
- Every fix tested on one model (Olmo 3 7B Think), one training run each.
- The hand labels for candid answers: 42 answers per system.
- The checker was tested on items the solver can solve without the tool.
- Unknown: whether this transfers to free-form, multi-step agent tasks, and to larger closed models.

## 3. The deck (about 8 main slides + backups; 6:00)

Build from the **official ASU 2026 template** (`__2026_Official_ASU_presentation_template…pptx`, copied, never edited in place).

**The template:**
- 16:9 at 10 × 5.625 in; Arial throughout.
- Brand colors: maroon `8C1D40`, gold `FFC627`, near-black `191919`, white, light gray `E8E8E8`.
- Remove its instruction slides (1–7) and the end logo slide (19); keep its masters.
- Use its layouts with variety:
  - the network-background title (template slide 8);
  - the white "Slide title" with the gold highlight (12/13);
  - the black half with an image (14);
  - "Highlight key numbers" (16);
  - the dark statement (17);
  - "Thank you" (18).
- **Respect the template's content-safe zone** (template slide 6): no important text in the bottom strip reserved for caption overlays.
- The second file (`Markstrat_Lessons_Video.pptx`) is an example of the ASU look in use, but it's far too text-heavy to copy. Take only its gold preheader style.

| # | Slide | Time | Rubric | Content | Visual | Speaker (suggested) |
|---|---|---|---|---|---|---|
| 1 | **Title** | 0:10 | clarity | "Do thinking modes make chain-of-thought more honest?"; the subtitle "When a tool is wrong, does the model follow it, and does it tell you?"; CSE 598, Group 10; the three names; Dec 3, 2026 | template's title layout | Ritik |
| 2 | **The question and why it matters** | 0:50 | deployment, soundness | the scenario: a tool-using model asks a lookup tool; the tool is wrong; what does the model do, and what does the user see? The title question in one line | the illustrative example (question card, tool slip "the answer key says (C)", the bare answer "(C)"), labelled "illustrative" | Ritik |
| 3 | **How we tested** | 1:00 | soundness (7) | the design diagram (§5); beside it, the four "why" lines from §2 (paired source swap; multiple choice and fresh questions; three measures plus right hints; pre-registered, paired bootstrap) | native PowerPoint diagram | Ritik |
| 4 | **The finding: tools pull harder, and the answer goes quiet** | 0:55 | results (5) | part 1 and part 2, each with its big numbers, n and interval; the exception (Gemma); a one-line answer to the title question ("mixed") | two compact figures (§4): tool vs user across models; reasoning against final answer | Arsha |
| 5 | **See it happen** (the demo video) | 1:05 | results, clarity | the embedded video, clip A (§6): a real recorded run: wrong tool hint, the reasoning citing it, the bare answer, the count. Caption: "a real recorded run; the count is every run" | video with poster frame | Arsha |
| 6 | **What we'd tell a team deploying it** | 1:15 | deployment (4) | the four recommendations, each with its number; clip B (§6) optional and short, or a still of the checker's flag | icon + text rows; small figure of the trade-off marked "exploratory" | Shrey |
| 7 | **Where this holds, and what we don't know** | 0:40 | results (uncertainty), Q&A | the limits from §2, in two groups: "applies to" and "unknown" | two-column | Shrey |
| 8 | **Thank you** | 0:05 | — | the repo link, the three names; "questions" | template's thank-you layout | Shrey |

**Backup slides,** after a divider "Backup: for questions", not presented:
- B1. Inside the model: the layers and the Qwen3 8B replication.
- B2. The authority ladder.
- B3. Every fix on one table: following, acceptance, intervals.
- B4. Review teams by model family.
- B5. What's new against related work.
- B6. Statistics and pre-registration, with real dates.
- B7. The full architecture.
- B8. Stills of the demo, in case a video won't play.

**Timing:** the main slides total 6:00. Speaker notes per slide carry **cues, not a script**: the 2–4 points to hit, the numbers, the transition line's idea and the time. Speakers are a suggestion for the team to change.

## 4. Figures for the main slides (new, from the frozen summaries)

- Draw **2–4 slide-specific figures**: tool vs user across models (dot plot with 95% intervals, the two sources per model); reasoning against final answer (paired bars with n); the trade-off (exploratory, marked on the figure); optionally the checker's catch and false-alarm counts.
- **Style:**
  - ASU palette: maroon for the tool, gold or gray for the user, near-black text.
  - Arial; labels at least 14 pt as seen on the slide.
  - Plain names, an n on every bar or dot, intervals drawn, one annotation pointing at the key number.
  - No chart junk; white background.
  - Export PNG at 2× slide resolution, plus SVG.
- Every figure is generated by a script in the repo from the frozen data, with a test that its numbers equal 02_NUMBERS.

## 5. The architecture diagram (slide 3, B7 and the README)

- A **native PowerPoint diagram** (editable shapes, not an image) of the evaluation, left to right:
  - questions (sets and sizes)
  - → the hint (sources; wrong or right)
  - → the model (12 models; thinking on/off; Sol GPUs)
  - → what it wrote (private reasoning, final answer)
  - → the three measures
  - → statistics (paired bootstrap, 95% intervals, pre-registered).
- Three branches off the model: **inside the model** (activation patching → the readout layers); **the fixes** (instruction, label, fine-tuning, consistency training, attention dial → re-tested on fresh questions with wrong and right hints); **the review team** (solver → reviewer → checker).
- **On slide 3:** a simplified version that reads in five seconds. **On B7:** the full version.
- Export the same diagram as `docs/figures/architecture.svg` and `.png` for the README and the report.

## 6. The demo videos (embedded; no live demo)

**Two short clips,** recorded from the local scratch pad (served by `serve.py` on 127.0.0.1), driven deterministically through `PAD_API.set(...)`:
- **Clip A, slide 5:** 40–55 s, the problem.
  1. The question and the tool's wrong reply land (zoom on the slip).
  2. The scratch work streams; zoom to the highlighted sentence where the model cites the tool.
  3. Zoom out to the final answer box: the bare letter.
  4. The red-pen checks: took it yes, reasoning says so yes, answer says so no.
  5. The count: "No fix took the wrong hint on 38 of 114 questions", plus the frozen run count.

  Pick the question with **Show me** (its seeded order) for a run whose reasoning names the tool and whose answer doesn't. The caption says "a real recorded run, found by pattern; the count is every question".
- **Clip B, slide 6:** 20–30 s, optional, the fix and the check.
  1. Consistency training on a question where the fix held (verdict line), then the cost (a right hint refused).
  2. Then the review team: the reviewer defers, the checker flags, nothing ships.

  If clip B doesn't fit 6:00, keep it as a backup slide.

**How:**
- Playwright (Chromium) at 1920 × 1080 with `device_scale_factor` 2, for sharp zooms.
- Real-time recording only for the streaming segment. Screenshots for the held moments.
- Compose with ffmpeg:
  - smooth eased zooms (0.6–0.8 s), never jumpy;
  - highlight boxes in ASU gold or red-pen red;
  - captions burned in: at least 40 px at 1080p, white on near-black at about 80%, bottom-center but above the template's safe-zone strip; each on screen at least 2.5 s; one idea per caption;
  - 0.3 s fades between beats.
- No audio track needed (we narrate live). H.264 MP4, yuv420p, 30 fps, `+faststart`, each clip under about 15 MB.
- **Embed** in the .pptx as a movie with a **poster frame** (the key moment's still), so the slide makes its point even before it plays. Plays on click.
- Keep the clips and their stills in `docs/presentation/final/video/`. Write the exact ffmpeg and Playwright scripts to the repo (`tools/demo_video/`) so the clips can be rebuilt.
- **Ritik checks playback in PowerPoint** (Mac and, if possible, Windows); LibreOffice can't verify it.

## 7. Design rules

- **One message per slide.** The title states the takeaway as a claim, not a topic.
- **Big numbers** with small labels for the key results (the template's "highlight key numbers" style).
- At least 14 pt body and 10 pt captions; usually much larger, since this is projected.
- No decorative stripes or accent lines under titles; no text-only slides.
- Alt text on every image and video.
- The deck stays under about 50 MB.
- Check every slide rendered as an image: no overflow, no overlap, nothing in the safe-zone strip, consistent title positions.

## 8. The preparation guide (6-minute version)

Rewrite `docs/presentation/pack/08_PREP_GUIDE.md` as `docs/presentation/final/PREP_GUIDE.md` (and a PDF):
- **The run of show:** slide, speaker, start and end time, the 2–4 points to hit, the numbers, the hand-off to the next speaker.
- **Timing plan:** about 130 words a minute while a video plays and is narrated; where to cut if running long (clip B first, then the "inside the model" line).
- **Concepts in plain words** (keep the 13 from the pack, shortened): a one-line explanation, an analogy, our number.
- **Q&A bank** (the rubric rewards direct, accurate answers that draw on the evaluation and say what's unknown): 25–30 likely questions. For each: the one-sentence direct answer in FINDINGS' wording, the evidence (numbers and n), what remains unknown, and which backup slide to show. Use `09_QA_BANK.md` and `QA_FACTS.md` (as corrected). Include the hard ones:
  - why one model for the fixes; whether 42 labels are enough;
  - why multiple choice; is this just sycophancy;
  - how this differs from the related work; are the demo's examples cherry-picked;
  - why consistency training isn't just ignoring tools; how expensive the checker is;
  - would larger or closed models behave the same; what we'd do with another month.
- **Rubric self-check:** each criterion → where the deck earns it → the evidence → what a grader could still mark down.
- **If the video doesn't play:** the poster frame and the B8 stills carry the point; what to say.
- **Rehearsal plan:** three timed run-throughs, one with a stopwatch per speaker; a 2-minute mock Q&A.

## 9. The checklist for every result slide (the past feedback)

Each result on a slide has:
- the number;
- the n;
- the 95% interval or paired difference;
- the comparison it's against (user vs tool; no fix vs fix; instruction);
- what it means, in one line;
- one honest limit;
- for exploratory results, the word "exploratory".

The QA step checks each slide against this list and reports it.

## 10. Phases and stops

- **Phase A, the storyboard, then STOP:** a one-page plan:
  - the slides with their exact titles, timings and rubric mapping;
  - the figures (quick draft renders);
  - the diagram (a draft render);
  - the video storyboard (the beats, the question picked by Show me, the zoom targets, the captions' text).

  Save it to `docs/presentation/final/STORYBOARD.md` with the renders, and stop for Ritik.
- **Phase B, build:** the figures, the diagram, the clips, the deck, the speaker notes. Then QA:
  - content: every number checked against 02_NUMBERS by a test;
  - visual: every slide rendered and looked at;
  - `validate` the .pptx;
  - an estimated timing from the notes.

  Deliver `docs/presentation/final/Group10_final.pptx` plus a PDF export, and stop for Ritik, who checks video playback in PowerPoint.
- **Phase C, the prep guide** (§8), after Ritik's OK on the deck.
- **Phase D, the repo (for the code submission, Dec 10; after the presentation is done):**
  - **A quick start that works:** clone → environment (pinned requirements, Python version, `.env.example` for paths) → `make verify` (offline: the tests that need no data or GPU, regenerating every figure and table from the frozen summaries) → open the demo.
  - **A harness a team could run on their own model:** the evaluation (hint builders, scoring, statistics) runnable against any OpenAI-compatible endpoint (vLLM or Ollama), with a 5-question smoke run documented, using the experiments' own code.
  - **Full reproduction:**
    - Sol/Slurm steps with paths and accounts moved to configuration, not hard-coded;
    - GPU needs and the 352 GPU-hours;
    - seeds; the data sources;
    - which script makes which result.
  - **`docs/ARCHITECTURE.md`:** the diagram from §5 plus a map of the code's modules.
  - **Continuous integration:** a GitHub Actions run of the offline tests on push, with its badge in the README.

## 11. Handoff after each phase (at most 8 lines)

What was made (paths), what needs Ritik, anything that didn't match its source, and the timing estimate.
