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

## 5. Checks

- Deck, demo, C27 and hygiene tests: 42 passed. With Track A's evaluation, A39, A40 and the Sol feeder tests: 181
  passed (17:32).
- `tools/check_links.py`: 0 broken links. `make_supplement.py --check`: pass.
- Privacy: no email, Sol username, key or model text in tracked files. The clips, the demo page and the local decks are
  gitignored.

## 6. Waiting for Ritik

1. Keep the Sol connection (or reopen it with `ssh -fNM login.sol.rc.asu.edu`) for the copy-back.
2. The playback check in PowerPoint: slide 6 (clip D), backups 16, 28 and 29. I couldn't play the clips in PowerPoint
   from here. Clip D is encoded like clips A–C.
3. C27's reading by 20:00 MST Nov 27, or it is reported as not tested.
