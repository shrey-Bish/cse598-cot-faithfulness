# Session log: the repo as a front door, the demo's final pass, the presentation kit (2026-11-23 09:10 MST)

**By:** Ritik. Branch `trackA-nosol`, from `914317f` (main, `trackA-nosol`, `origin/main` and `origin/trackA-nosol`
level). The day's first session; the daily: [DAILY_2026-11-23](2026-11-23/DAILY_2026-11-23.md). The previous session: Nov 22,
[18:48](2026-11-22/2026-11-22_1848_ALL_demo-sol-copy.md). The results are frozen: the tag
`results-freeze-2026-11-18` on `7e1fdc0`. Presentation and docs work only. Two helpers (the README and folder pages;
the presentation kit and QA_FACTS); they did not commit.

## 0. Input

Two pastes, acted on as Ritik's. The first is a review of the tracked page at 1920×1080, with seven demo fixes and a
request to check the local bench (test 1 compare, test 4 no fix against consistency, test 5 with the checker on). The
second is the day's plan, with "Prompt 1: send now":
- **A.** The repo as a front door: README, folder READMEs, process material to `archive/` (MOVES.md), CITATION.cff
  and REPRODUCE.md, hygiene, GitHub Pages.
- **B.** The demo's final pass: both themes at 1920×1080 and 1440×900, every key, both builds offline; the seven fixes.
- **C.** The presentation kit: TALK_MAP as a live run from the demo; QA_FACTS checked against FINDINGS.
- **D.** The submission checklist.

Also: **"Gate 3: I approve the statement as drafted (PLAN, REPORT §7)."** Prompt 2 (tonight's final check and the
zip) and the Sol feeder stop are not part of this session.

## 1. What was done (09:10–09:40)

**Gate 3:** recorded as approved by Ritik, as drafted (PLAN's Gates section and its status row; ONE_PAGE).
`REPORT.md` was not touched: Ritik writes its prose today, and it has no line waiting on the approval.

**Moves** (`33be48e`, `git mv` only; [MOVES.md](../MOVES.md), Nov 23):
- `docs/drafts/` → `archive/drafts/`.
- `DEMO_SPEC.md` and `INVENTORY.md` → `archive/demo_build/`.
- The Hint Explainer → `archive/superseded/explainer_2026-11-14/` (`build_demo.py` and its tour test point there).

Links updated in 22 files. `docs/demo/` now holds one demo. **Not moved:** `docs/status/`, because Track B's and C's
pages link to it and `make_gantt.py` writes it; it gained a README saying a reader can skip it. The tracks' session
folders are their owners' paths. In the zip, the demo goes in as `demo/index.html` (it was `explainer/`).

**The front door** (helper 1; checked here):
- `README.md`: the question; the answer in one paragraph ("mixed"); five findings with `three_levels.png`; what's new
  and what isn't; the demo; the folders; reproduce; the team; AI use; cite.
- Two lines tightened to FINDINGS: F35's 68% and 71%, and F45's "without following fewer than the instruction".
- `REPRODUCE.md` and `CITATION.cff`; the root `.gitignore` now admits both.
- Short READMEs in `archive/`, `docs/`, `docs/demo/`, `docs/status/` and nine `cot-disclosure/` folders. None in
  `agents/` (Track C's path); `cot-disclosure/README.md` describes it.

**The demo** (the review's seven):
1. The overview: the third bracket now reads "review teams" (it was clipped); "What it wrote" links to the bench's
   test 3.
2. Step 1: "↓ scroll the options" sits under the options. Its class lacked `plab`, so it was never positioned.
3. Step 6 opens with layer 15 swapped (34% [27%, 42%]) and every layer's measured effect drawn faintly.
4. Step 7: the loss chart is taller and zoomed to the data, with y values and the first and last step; "epoch N
   kept" in red; the boxes shortened.
5. Sheet 8: "Five fixes and no fix, on Olmo 3 7B Think".
6. The explainer moved (above).
7. The tracked bench shows each test's prompt in place of the empty area: the experiments' own template on a sample
   question (`method.json`), the hint marked. Test 4 adds the instruction (end of the system turn) or the label
   (the inserted tool turn only), and the right letter for right hints. Test 5 shows the reviewer's instruction and
   what it is shown. Test 6 shows what is measured. The frozen result stays on the right.

**Found on the local bench:**
- Test 5's checker was always stamped "Agrees": `runs.py` read `checker_flag`, but the records' field is `flag`. Now
  the stamp is the record's own flag; a new test checks it against the file and line.
- In compare, the column headers ran into the result panel; now they name only what differs.
- In the dark theme, marked text was light on yellow; now it uses the sticky's dark text, as the template does.
- Test 4, no fix against consistency, read correctly.

**Checks of the page:**
- Both builds walked offline at 1920×1080 and 1440×900, both themes: every page of the three parts; keys 1–3,
  ← →, Esc, R, T, Shift+1–6; on the local bench Enter, N, M, C, P, L. No console error, no request but the file,
  no text cut by its container, the sheet inside the window.
- Screenshots (gitignored): `cot-disclosure/results/demo/screens_final/` (the fixed pages in both themes, the local
  states) and `screens_final_1440/` (all 28 pages). Looked at: the fixed pages and four at 1440.

**The presentation kit** (helper 2):
- TALK_MAP gained "The live run: 12 minutes from the demo": per slide, the keys, the test or sheet, what to point
  at, the time and the fallback slide. The deck's parser reads the same rows; `deck.pptx` is unchanged.
- The "next steps" line on B1's replication was stale after B1R2; it now reads "The attention dial replicated on 120
  questions; its cost to right hints is open (F38)".
- QA_FACTS: 10 corrections against FINDINGS. For example: F25's "no change detected"; "layers only" for the
  second-family replication (the heads are Olmo only); B1R2's replication; F29's +64 "on the real tool call"; the
  system-level fix marked "our reading".

**Ritik's five-line story against FINDINGS** (both helpers):
1. Holds in every model tested; "much of the pull is authority" holds for pasted blocks (F35).
2. Not general: Gemma names the tool in 127 of 162 with thinking off (FB1); Olmo is tentative (F17).
3. Qwen3-8B replicates with its own layers (21, 22, 29) at 0.70 (F36), not the same three.
4. Holds.
5. "Without making them follow less" is false against base (LoRA −10). The candid result is LoRA against the
   instruction, one model, 42 rows (F45).

**After the freeze (Nov 23, 09:40): presentation and docs work only.** No number, figure or verdict changed.
QA_FACTS and the README now say what FINDINGS says where they had said more.

## 2. Hygiene (A.5)

- **Keys and tokens:** none in tracked files.
- **Files over 5 MB:** none tracked.
- **Produced data:** nothing under `results/track*/`, `labels/`, `handoff/`, `demo/`, `logs/`, `cache/` or
  `finetune/data/` is tracked.
- **AI attribution:** none in the full history (no Co-Authored-By, "Generated with", session lines or Anthropic
  email). Authors and committers are the three team members only.
- **Emails:** none written as an email. Ritik's own Sol account appears in ssh and rsync lines (user@host).
- **Sol usernames:** only Ritik's own, in 79 tracked files: 50 session logs, frozen summaries' paths, the Sol tools'
  tests and the run docs. No teammate's.
- **Pages:** the page has no external or root-absolute path; served from `docs/` it works as is.

## 3. Waiting for Ritik

1. **Publish the seeded runs in the tracked build?** `bench_runs.json` is 17.5 MB with the Sol copy (the page about
   18 MB). It is model text, which the repo's rule keeps out of tracked files, so the team would change that rule
   first. Before that: check the license of each source (MMLU-Pro; each model's terms for its outputs: Qwen3, Olmo,
   gpt-oss, Nemotron, Mistral, Granite, Gemma; our puzzles are ours). Then one follow-up: "include bench_runs.json in
   the tracked build".
2. **LICENSE:** none added. A suggestion: MIT for the code, CC BY 4.0 for the docs and figures; the team decides.
3. **GitHub Pages** needs the repo's owner, Shrey: Settings → Pages → "Deploy from a branch", `main`, folder `/docs`.
   The demo would then be at `<owner>.github.io/cse598-cot-faithfulness/demo/`.
4. **Your Sol username in 79 tracked files:** keep it (the repo's convention so far), or scrub the logs and docs. The
   frozen summaries can't change after the freeze, and the history keeps it either way.
5. **The story's wording** (above) for the talk, the report and the slides.
6. **CLAIMS 1.4** says the heads replicate in a second family; only the layers did (F36). Changing it means
   regenerating the supplement.
7. **Your worded deck:** if it carries the old B1 "107 to 245" line, change it. `deck.pptx` was not rebuilt.
8. **The course's rule on AI-drafted prose** before the report's text; the Sol feeder stop when next on the VPN.
9. As before: the report's prose, the slides' words, `CONTRIBUTIONS.md`, `AI_USE.md` (the checklist's only open
   rows).

## 4. Checks and push

- The demo's tests (with the new checker test), the method tests, the explainer's tour, hygiene and links, the deck,
  the submission and the supplement tests.
- The full suite once.
- `tools/check_links.py`; `make_supplement.py --check`; `export_summaries.py --check`.
- STATUS and the Gantt; the pre-push check.
- The push: `git push origin trackA-nosol:main trackA-nosol:trackA-nosol`.
- **Results:** the full suite 1,402 passed, 1 skipped (11 min 15 s); the deck's tests 13 passed, its rows parsed as before; 0 broken links; the supplement and export checks pass.
