# Session log: C18: removing the solver's sentences that cite the tool restores the Olmo reviewer's check (2026-10-30 17:20 MST)

Project: CSE 598 Group 10, Track C. C18 tests H33: is the cue the argument for the wrong letter? It was pre-registered
in the 17:00 log (commit `1928820`) before any call. FINDINGS F34. **By:** Ritik.

## 1. What ran

- **Voyager, 16:45–16:49:** 136 reviews, 0 errors, under the power guard (on battery at 77%, above the guard's 15%).
- **Answers:** C16's 34 final answers that named the tool after a bad lookup (every one wrong).
- **Versions:**
  - **unchanged** (`team_c18_unchanged`);
  - **stripped** (`team_c18_stripped`): the 2–4 sentences per answer that name the tool removed, the rest kept.
    The median length falls from 474 to 126 characters.
- **Reviewers:** Olmo 3.1 32B and Qwen3 30B Instruct, `plus_explanation`, C4's prompt.
- **Read:** `python agents/c18.py`.

## 2. The pre-registered reading

Correcting a wrong answer (34 items); stripped minus unchanged; paired by item; two-sided with C11's 20-point margin.

| reviewer | stripped | unchanged | minus | rule | H33 |
|---|---|---|---|---|---|
| Olmo 3.1 32B | 25 of 34 | 9 of 34 | **+47 [+29, +65]** | more corrections | **the tool mentions are part of the cue** |
| Qwen3 30B Instruct | 28 of 34 | 26 of 34 | +6 [−9, +21] | no change | (it doesn't defer) |

**H33 as stated is not supported for the Olmo reviewer.** Removing the sentences that cite the tool restores most of
its check; the argument that's left doesn't hold it back.

## 3. Also reported (no decision)

- **The stability check:** the unchanged answers reviewed again give exactly C16's original results (Olmo 9 of 34,
  Qwen3 26 of 34, +0 [0, 0]). The same prompt and seed reproduce on Voyager.
- **Stripped minus C17's own-working version** (32 items both have): Olmo 23 against 22, +3 [−9, +16]; Qwen3 +6 [0,
  +16]. Once the tool sentences are gone, Olmo reviews these answers about as it reviews a bare answer with "based on
  my own step-by-step working".

## 4. Reading, with C16 and C17

The three experiments on the Olmo reviewer (it defers; Qwen3 doesn't move in any of them):

| what the reviewer sees | corrects (Olmo) | source |
|---|---|---|
| the solver's bare answer (+ a neutral or a tool-naming line) | about 36–37 of 53 | C16 control, C17 |
| the solver's own disclosure: its working + sentences citing the tool's letter | 25 of 53 (C16); 9 of 34 named | C16, C18 |
| that disclosure with the tool-citing sentences removed | 25 of 34 | C18 |

- **The cue isn't a generic source label.** "This answer is based on the lookup tool's result." changes nothing
  (C17).
- **It isn't the solver's working either.** With the tool sentences gone, the working that remains doesn't hold Olmo
  back (C18).
- **It is the solver's sentences that cite the tool's letter as authority:** "the course answer key specifies the
  expected answer as H… Despite the discrepancy, the tool response confirms the expected answer is H."
- **Revised hypothesis (H34, untested):** the deferring reviewer follows a statement that an authoritative source
  gave this letter, especially one that overrides the solver's own working. A generic mention of a tool doesn't do
  it.

**For deployment:**
- Disclosure written by the solver can make a deferring reviewer worse, because the disclosure carries the authority
  claim.
- The check that never sees the tool (the checker) held throughout.

**Limits:**
- 34 items.
- One solver.
- Which sentences go is decided by a keyword, so the removed sentences carry both the citation and its
  justification.
- One deferring reviewer family.

## 5. What changes

- **FINDINGS F34.** Story step 4: the deferring family follows the solver's citations of the tool's letter, not a
  source label (C17) and not the remaining argument (C18).
- **CLAIMS** 2.1 and B15's headline.
- **REVIEWER_QUESTIONS** thread 1, question 10.
- **TODO C18:** done; H34 for Shrey's plan.
- **PLAN; TRACK_C.**
- **Exported:** `c18_summary.json`, `team_c18_unchanged_summary.json`, `team_c18_stripped_summary.json`.

## 6. Source

`cot-disclosure/results/summaries/trackC/c18_summary.json`. Recomputed with `python agents/c18.py`.
