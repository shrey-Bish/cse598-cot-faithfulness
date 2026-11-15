# The submission, Nov 19–24

**Edited by:** Ritik. Set up Nov 13 (14:13) from PLAN's
[submission checklist](../PLAN.md#submission-checklist-nov-1924). Every file here reads only the results frozen on
Nov 18 (CHECKIN [§10](../status/CHECKIN.md#10-the-results-freeze-nov-18-the-procedure)). The course's exact requirements
(formats, length and time limits, where and how to submit, the form of the contribution statement and of the AI-use
disclosure) are not in the repo: each row says what to confirm against the course page.

## What goes in, and where

| piece | where it is, or will be | who | by when | state (Nov 13) |
|---|---|---|---|---|
| **the report** | the prose written from [`docs/paper/REPORT.md`](../paper/REPORT.md)'s bullets (numbers only from FINDINGS and CLAIMS); the final file here as `docs/submission/report.<pdf or docx>` (format and length: confirm) | each section's owner (PLAN's writing plan); Ritik merges | draft Nov 22; final Nov 24 | bullets in; prose not started |
| **the supplement** | [`docs/paper/supplement/`](../paper/supplement/), regenerated at the freeze by `tools/make_supplement.py`; whether it goes in as an appendix: confirm | Ritik | Nov 20 (D6) | regenerated Nov 13 (42 rows) |
| **the slides** | one deck, `docs/submission/slides.<pptx or pdf>` (format and time limit: confirm), from the 13 slides of PLAN's [presentation map](../PLAN.md#final-presentation-map-about-12-slides), figures from [`docs/paper/figures/`](../paper/figures/) | each slide's owner; the deck Ritik (proposed) | 11–12 Nov 18; 2, 6–8 Nov 20; 9 after Gate 3's statement (Nov 20); 13 Nov 21–22; presented Nov 24 | figures made but slide 5's (Nov 13) and 13 |
| **the demo** | [`docs/demo/index.html`](../demo/index.html), the Hint Explainer: one file, opens offline in any browser; a guided tour of 7 scenes and an article; built by `cot-disclosure/tools/build_demo.py` from the tracked numbers-only summaries | Ritik | rebuilt at the freeze (Nov 18) | built Nov 13; replaced by the Hint Explainer Nov 14 |
| **the code link** | https://github.com/shrey-Bish/cse598-cot-faithfulness, `main` at the tag `results-freeze-2026-11-18` (made Nov 18, CHECKIN §10); the README's test and recompute commands; produced data local, numbers-only summaries tracked; the graders' access: confirm | Ritik (the merges, the push, the tag) | the tag Nov 18 | the tag not made yet |
| **the contribution statement** | `docs/submission/CONTRIBUTIONS.md` (not created: the team writes it), from PLAN's "Who runs what" and each track's TODO; form: confirm | each member their own lines; Ritik merges (proposed) | Nov 22 (proposed) | not started |
| **the AI-use disclosure** | `docs/submission/AI_USE.md` (not created: the team writes it), from the facts in [`AI_USE_INVENTORY.md`](AI_USE_INVENTORY.md); form and policy: confirm | each member for their own work; Ritik merges (proposed) | Nov 22 (proposed) | the inventory written Nov 13; the statement not started |

## The folder at submission (Nov 24)

```
docs/submission/
  README.md               this page
  AI_USE_INVENTORY.md     the facts the disclosure is written from (Nov 13)
  AI_USE.md               the AI-use disclosure, written by the team
  CONTRIBUTIONS.md        the contribution statement, written by the team
  report.<pdf|docx>       the final report
  slides.<pptx|pdf>       the deck
docs/demo/index.html      the demo, the Hint Explainer (linked, not copied)
```

A file over 50 MB doesn't go in git (the pre-push check refuses it): it goes where the course page says, and this
page names where.
