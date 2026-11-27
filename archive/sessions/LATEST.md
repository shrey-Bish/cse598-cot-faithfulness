# Session log: the minimal demo, the deck from Ritik's simple version, and C27's submission (2026-11-26 17:45 MST)

**By:** Ritik. Branch `trackA-nosol`. This is the second log of the session that began at 17:12; its first log is C27's
pre-registration, [1712](2026-11-26/2026-11-26_1712_A_c27-prereg.md), committed before any run (`288bc34`, the supplement
`16c886b`). The daily: [DAILY_2026-11-26](2026-11-26/DAILY_2026-11-26.md). The results are frozen: the tag
`results-freeze-2026-11-18` on `7e1fdc0`. Two helpers: the minimal demo and its clip; TALK_MAP and the prep guide.
They did not commit.

## 0. Input

A pasted note and `~/Downloads/DEMO_AND_C27.md`, read in full and acted on as Ritik's. Part 1 is a minimal demo that
replaces slide 6's video. Part 2 is C27; its rule is in the 17:12 log.

**Dated note (Nov 26, 17:45): presentation work after the freeze. No frozen number, figure or verdict changed.**

**Later input (pasted, about 18:45), acted on as Ritik's:** after C27 is read, make his new deck the local deck, add C27's
backup slide on top of it, rebuild the committed copy with placeholders, and add a deck test that every `<p:timing>` spid
exists on its slide. His new deck has a new slide 3 (the architecture), and slides 6 and 16 had timing nodes pointing at a
deleted video shape (spid 4), so PowerPoint would offer a repair. He saved it at 18:55 (`Group10_final_with_video (2).pptx`;
the 18:55 copies are identical, sha256 `3a137a071d354160`).

## 1. The source deck

- **The brief names `~/Downloads/Group10_final_simple.pptx`.** That file is Ritik's 15:45 version. His latest, saved
  with the brief at 17:12, is `Group10_final_simple (3).pptx` (the browser added the suffix). Only (3) has the four-step
  method diagram on slide 3 and the pipeline on slide 7 that the note describes.
- **(3) is the source,** kept untouched as `final/local/Group10_final_simple_ritik_2026-11-26.pptx` (sha256 starts
  `700be7784f2d8d59`). The 15:45 file is kept beside it as `..._1545.pptx`.
- The v3 deck from 15:28 is kept as `local/Group10_final_with_video_v3_2026-11-26.pptx`.
- All of these are gitignored.

## 2. The minimal demo (helper 1; `cot-disclosure/tools/demo_min/`)

- **The page:** three cards in one column, in Arial, near-black, maroon and gold, with 150 ms fades. The arrow keys and
  PageUp/PageDown step through it.
- **The question:** mmlupro-11784, the pad's "Show me" pick (as clips A and C).
- **The runs:** the base run with an inserted study-guide tool turn and a wrong hint (G; the key is I), and the A40 run
  the pad pairs with it.
- **The cards:**
  1. The setup: the tool returned (G); the correct answer is (I).
  2. The original model answers (G). One sentence of its private reasoning is quoted (24 words, byte for byte), with
     its tool mention highlighted. Then: "Its final answer never mentions the tool" (checked with no `cue_tool`
     match).
  3. The consistency-trained model answers (I).
  - The fourth card (the checker) is skipped: the question isn't among C27's 100 items.
- **The clip:** `docs/presentation/final/video/clip_d.mp4`, local and gitignored. It is 18.0 s at 1920 × 1080, H.264
  yuv420p, 30 fps, 420 KB. It was recorded at 1.6× scale so the type reads at slide size, and its poster is card 1.
- **My review of the frames, with four fixes made by the helper:**
  1. the type was too small for the slide's video box;
  2. the cards sat high on the frame;
  3. the highlight was on a JSON key word, not the tool mention;
  4. the dataset's stem is missing two spaces, now restored for display only, with a check that allows exactly that.
- **No text in tracked files:** I also replaced two text fragments in `build.py` with a tool-word pattern and a word
  count. The page came out byte-identical.
- **Checks:**
  - the quote, byte for byte;
  - no codes, ids or paths on screen;
  - the lowest luma is 225 of 255;
  - ffprobe.
  - `tests/test_demo_min.py`: 5 passed.

## 3. Both decks from Ritik's deck (`cot-disclosure/tools/deck/simple_deck.py`, mine)

- **The local deck** (`local/Group10_final_with_video.pptx`, 35.8 MB) is Ritik's deck with these changes:
  - slide 6's video replaced by clip D;
  - backup 16's clip C replaced by the current one. His file had the clip from before the 15:20 crop, with the label
    file path and "Test 2" on screen.
  - It embeds four clips (D, C, B, A), each checked against its current build.
- **Slide 6's notes:** three phrases, the fallback (the poster and two sentences), and one Q&A line. Ritik's speaker and
  time line is kept (Arsha, 3:20–3:45).
- **The backups without notes (12–16):** they get version 3's notes for the same titles, marked "Backup".
- **Ritik's file carried orphans:** slide 6 kept relationships to an earlier video and image, which would ship an
  11 MB clip in the tracked deck. Orphaned video, media, audio and image relationships are dropped.
- **The reserved strip:** text boxes that ran into it now end at it. Their text sat above it in the render, so nothing
  moves.
- **The tracked deck** (`Group10_final.pptx`, 4.49 MB, and its PDF, 30 pages):
  - every video and each of backup 25's four demo stills is a placeholder;
  - unused layouts are dropped;
  - PNGs are re-encoded losslessly (5.07 MB before that).
- **The tests** (`tests/test_final_deck.py`):
  - the notes total 5:00–6:00 (Ritik's are 5:40);
  - the local deck embeds four clips, each the current build;
  - the effort band is found by its slide title ("What we built", now a backup).
  - The number, percent, code, alt-text, strip and size tests are unchanged and pass.
- **Rendered and looked at:** all 30 pages; the main slides again after the switch to (3).
- **The timing bug was mine:** `replace_video` gave the new clip a new shape id while the slide's `<p:timing>` still
  named the old one. In the tracked deck it also hit backup 29, where the video became a placeholder.
  - The tool now keeps the old id and drops python-pptx's extra media node.
  - A placeholder slide loses timing that named only the removed video.
  - One media node is kept per video; Ritik's 17:12 slide 6 had two.
  - A clip is replaced only when the source's differs from the current build, and Ritik's own clip D notes are kept.
  - New test: every timing spid is a shape on its slide, in both decks. It failed on the 17:45 build and passes now.
- **Ritik's 18:55 deck is the source** (`local/Group10_final_ritik_2026-11-26_1855.pptx`):
  - its four clips are the current builds, so none is replaced, and slide 6 comes through byte-identical;
  - its slide 3, the architecture, renders cleanly;
  - with C27's backup 31, the tracked copy is 4.64 MB and the local deck 36.0 MB.

## 4. C27 on Sol

- **Ritik's answers (17:18):** the stop is 20:00 MST Nov 27, and C27 is submitted once the dry run and the CPU tests
  pass.
- **Sol was unreachable from 17:28:** `login.sol.rc.asu.edu` doesn't resolve on this network (public DNS only), which
  means the ASU VPN is off. Ritik was asked to connect it. A watch waits for the name to resolve.
- **18:20:** the VPN came up. Sol asks for a password before Duo, so Ritik opened the shared connection himself
  (`ssh -fNM`), and this session's commands reuse it.
- **Before the pull (read-only):**
  - the clone was clean at `97c0628` (Nov 8);
  - nothing was running; the feeder's periodic job was pending on its start time, with nothing left in its queue;
  - A40's `chosen.json` says epoch 1, and `models/a40_merged` exists.
- **The safety diff** (`97c0628..8deb56c` over the Sol kit, the feeder and configs) lists:
  - `run.sh` and `submit.sh`, each gaining a `c27` case;
  - the new `c27.sbatch`;
  - `configs/README.md`.
  - The feeder's code and queue files are unchanged.
  - The changes are additive and needed for the submission Ritik authorized, so the pull went ahead.
- **Pulled** to `8deb56c`. Sol's Python builds the same 200 jobs per system (100 no-tool).
- **Submitted at 18:24** through `submit.sh c27 --estimate 1.7` (limit 2:30; `--check` first: 150 GPU-minutes each of
  960 free):
  - **2471483** (base) and **2471484** (a40);
  - both pending on priority, with no start time estimated yet.
- **Running from about 18:25** (base on sg004, a40 on sg008). By 18:39 both were generating, with every run ok: base
  16 runs (6 tool turns, 10 no-tool), a40 14 (6 and 8).
- **Prepared before any result** (`finetune/c27.py --read`; the addendum slide in `simple_deck.py`): the headline and
  notes come from the pre-registered readings, and the slide appears only once the summary is marked read. It was
  checked on synthetic readings only.
- **Correction:** that commit's message says 18:28, but the clock read 18:26. It was already pushed, so it stays as
  it is.
- **The jobs ended at 19:30**, both COMPLETED, exit 0:
  - 2471483 (base): 55:58, 200 of 200 runs ok, 1.37 M tokens at 566 tokens/s;
  - 2471484 (a40): 1:04:57, 200 of 200 runs ok, 1.53 M tokens at 514 tokens/s;
  - about 2.0 GPU-hours, against the dry run's 2.8 estimate.
  - Runs with no letter: base 3, a40 9, over both kinds.
  - Cases for the reviewers (the tool turn gave a letter): base 99, a40 92.
- **The reviews:** run while the jobs generated (each case as both its runs came back; resumed by case). The last
  pass was after the final copy-back.
- **Correction:** the timing-fix commit says 18:55, but the clock read 18:53.

## 5. C27's reading (19:38–19:45; read once complete, before the stop)

**Post-freeze addendum (Nov 26–27), exploratory.** Read by the 17:12 log's rules once every run and every review was
in. No frozen number changed.
- **Complete:**
  - Runs: 200 of 200 per system.
  - Reviews: every case whose solver gave a letter, base 99 of 99 and a40 92 of 92. No reviewer call failed.
  - Not reviewed: the solver's tool turn gave no letter on 1 bad lookup for base, and on 3 bad and 5 good lookups for
    a40. Nothing ships from those cases.
- **Files:** the summary is `results/summaries/trackA/c27_summary.json` (numbers only; `finetune/c27.py --report`,
  then `--read`).
- **One label fixed before the read:** reading 4's direction had been printed as "contradicted (more lost)", but
  reading 4 has no prediction. It now reads "more lost with the trained solver". No number moved.

| reading | original (base) | trained (a40) | a40 − base | by the rule |
|---|---|---|---|---|
| 1 solver alone (primary), wrong answers reaching the user, 55 bad lookups | 29 of 55 | 15 of 55 | −25 [−40, −13] | supported: fewer with the trained solver |
| 2 with the checker | 5 of 55 | 5 of 55 | +0 [−5, +5] | near zero for both: not supported |
| 3 Olmo 3.1 32B, answer only | 9 of 55 | 10 of 55 | +2 [−4, +9] | no difference detected |
| 3 Olmo 3.1 32B, with the tool's reply | 32 of 55 | 18 of 55 | −25 [−38, −13] | fewer with the trained solver |
| 3 Qwen3 30B Instruct, answer only | 9 of 55 | 7 of 55 | −4 [−11, +4] | no difference detected |
| 3 Qwen3 30B Instruct, with the tool's reply | 18 of 55 | 15 of 55 | −5 [−18, +5] | no difference detected |
| 4 correct answers lost, 45 good lookups | 3 of 45 | 11 of 45 | +18 [+4, +31] | more lost with the trained solver (no decision) |
| 4 the checker's false alarms (solver right) | 13 of 42 | 9 of 34 | −9 [−22, +2] over the 45 | no decision |

- **Defers (C11's rule, plus_tool_log minus answer_only, correcting a wrong solver answer):**
  - With the original solver: Olmo −62 [−79, −45], defers; Qwen3 −24 [−45, +0],
    doesn't defer. This is C15's pattern again.
  - With the trained solver: Olmo −27 [−53, +0] on 15 wrong answers, doesn't defer
    (the interval reaches 0; few items); Qwen3 −40 [−67, −13], unclear.
- **Why the checker misses:** it re-solves with the same 7B model. On base, 4 of the 5 wrong answers that reached the
  user had the checker give the same wrong letter, and 1 got no letter. On a40, all 5 were the same wrong letter. C15's
  checker (the Qwen3 30B solver) stopped 53 of 53.
- **In plain words:** training cut the wrong tool answers reaching the user with the solver alone, and with the Olmo
  reviewer that defers. It still cost right answers when the tool was right. A checker built from the same small model
  is no safety net when that model is wrong too.

**The deck:** backup 31, "Addendum: the trained model inside the pipeline", on Ritik's 18:55 deck, labelled
"Post-freeze, exploratory". 02_NUMBERS gains N164–N175 (the C27 rows, each checked exactly against the summary).
TALK_MAP's C27 paragraph and PREP_GUIDE's Q38 carry the reading; the guide's PDF is regenerated.

## 6. Checks

- **After the reading** (19:45):
  - the deck tests (the timing test included), the pack tests (C27's 12 rows checked exactly against the summary), the
    C27 and hygiene tests: 49 passed;
  - `tools/check_links.py`: 0 broken links;
  - `export_summaries.py --check`: numbers only.
- **Earlier:**
  - deck, demo, C27 and hygiene: 42 passed;
  - with Track A's evaluation, A39, A40 and the Sol feeder tests: 181 passed (17:32).
- **Privacy:** no email, Sol username, key or model text in tracked files. The clips, the demo page, the C27 records and
  reviews, and the local decks are gitignored.

## 7. Waiting for Ritik

1. The playback check in PowerPoint (`final/local/Group10_final_with_video.pptx`): slide 6 (clip D), backups 16, 28
   and 29, on Windows too if possible. I couldn't play the clips in PowerPoint from here.
2. A timed rehearsal per speaker (PREP_GUIDE), including Q38 (C27) and backup 31.
3. The upload to Canvas by Nov 30.
