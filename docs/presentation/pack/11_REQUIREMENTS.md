# 11. Course requirements found in the repo

**Short answer: the repo contains no course requirements.** No page limit, no word limit, no report format or template (no NeurIPS, ACL or other style file), no rubric or grading criteria, no syllabus, no Canvas instructions, no official presentation length, and no statement of where or how to submit. The repo says so itself, three times (quoted below). Ritik needs to check the course page or Canvas for each item in the list at the end.

Searched (case-insensitive) on Nov 24: `docs/` (including `docs/PLAN.md`, `docs/submission/`, `docs/presentation/`, `docs/status/`, `docs/trackB/`, `docs/trackC/`), `archive/` (session logs, drafts, superseded pages), `README.md`, `REPRODUCE.md`, `CITATION.cff`, and Claude's saved memory notes for this project. Terms: page limit, pages, rubric, syllabus, deadline, due, minutes, presentation, Canvas, submission, format, NeurIPS, ACL, ICLR, template, word limit, grading, assignment, instructor, course page. Every hit was either an internal deadline, a time limit on a compute job, or the repo's own "confirm against the course page" note. No PDF or document from the course is stored in the repo.

## What the repo says about the course's requirements (quoted)

1. [`docs/submission/README.md`](../../submission/README.md) lines 6 to 8: "The course's exact requirements (formats, length and time limits, where and how to submit, the form of the contribution statement and of the AI-use disclosure) are not in the repo: confirm them against the course page."
2. [`docs/PLAN.md`](../../PLAN.md) lines 453 to 455 (Submission checklist, Nov 19 to 24): "The course's exact requirements (formats, length and time limits, where and how to submit, the form of the contribution statement and of the AI-use disclosure) are not in the repo: each row says 'confirm against the course page'. 'Proposed' marks an owner or date set nowhere else in the repo, for Ritik to confirm."
3. [`docs/submission/AI_USE_INVENTORY.md`](../../submission/AI_USE_INVENTORY.md) line 4: "(`AI_USE.md`, the team's own words; form and policy: confirm against the course page)".

## Deliverables the repo lists, and what is only the team's own plan

These are the team's own list of what a submission needs, written Nov 4 (PLAN) and Nov 13 to Nov 19 (submission README); the repo does not say the course asked for exactly these.

| item | what the repo says | file and line | status marker in the repo |
|---|---|---|---|
| the report | "`docs/submission/report.pdf` or `report.docx`: the prose, from REPORT's bullets (numbers only from FINDINGS, FINDINGS_B, FINDINGS_C); format and length: confirm" | `docs/submission/README.md` line 33 | "to write by us", draft Nov 22, final Nov 24 |
| the report (PLAN) | "the prose from REPORT's bullets (numbers only from FINDINGS and CLAIMS), one figure a section ... format and length: confirm against the course page" | `docs/PLAN.md` line 459 | Track B's and C's bullets Nov 20; draft Nov 22; final Nov 24 |
| the slides | "`docs/submission/slides.pptx` or `slides.pdf`: the shell with our words; format and time limit (about 12 minutes planned): confirm" | `docs/submission/README.md` line 37 | "to write by us"; rehearsal Nov 23; presented Nov 24 |
| the slides (PLAN) | "the 13 slides of the presentation map above ... format and time limit: confirm against the course page" | `docs/PLAN.md` line 461 | one deck; Ritik assembles (proposed) |
| presentation length | "Talk map: the final presentation (Nov 24, about 12 minutes)"; "Total time: 12:00" | `docs/presentation/TALK_MAP.md` lines 1 and 12 | the team's plan; the source of "12" is not recorded; PLAN line 323 says "Final presentation map (about 12 slides)" (slides, not minutes), and the Nov 19 log (`archive/sessions/2026-11-19/2026-11-19_2249_ALL_demo-concepts.md` line 10) says "the 12-minute presentation" |
| the supplement | "whether it goes in as an appendix: confirm against the course page" | `docs/PLAN.md` line 460; `docs/submission/README.md` ("`--with-supplement` adds ... (whether it goes in as an appendix: confirm)") | ready (regenerated Nov 18) |
| the code link | "the graders' access: confirm against the course page" | `docs/PLAN.md` line 462; `docs/submission/README.md` (code link row) | ready; repository link and the freeze tag are in `docs/submission/README.md` |
| contribution statement | "form: confirm against the course page" | `docs/PLAN.md` line 463; `docs/submission/README.md` (contribution row) | "to write by us"; `docs/submission/CONTRIBUTIONS.md` is the placeholder |
| AI-use disclosure | "form and policy: confirm against the course page" | `docs/PLAN.md` line 464; `docs/submission/README.md` (AI-use row) | "to write by us"; `AI_USE.md` not yet written |
| the demo | one file that opens offline (`docs/demo/index.html`, copied into the zip as `demo/index.html`) | `docs/PLAN.md` line 465; `docs/submission/README.md` | ready; no requirement for a demo is recorded |
| the submission folder | `report.<pdf|docx>`, `slides.<pptx|pdf>`, `AI_USE.md`, `CONTRIBUTIONS.md`, `BUNDLES.sha256`, plus the demo | `docs/submission/README.md` "The folder at submission (Nov 24)" | "A file over 50 MB doesn't go in git ...: it goes where the course page says, and this page names where." (the page does not name it) |
| the zip | `cot-disclosure/tools/make_submission.py` writes `cot-disclosure/results/submission/cse598_group10_submission.zip` (gitignored) holding the report, slides, contributions, AI-use disclosure, every figure, the demo, `CODE_LINK.txt`, `BUNDLES.sha256`, `MANIFEST.sha256` | `docs/submission/README.md` ("One command") | refuses while a part we write is missing |

## Dates the repo records for the end of the course work (the team's calendar, not the course's)

| date | what | file and line |
|---|---|---|
| Nov 18 | results freeze (tag `results-freeze-2026-11-18`); "all evaluation done by Nov 18, no new runs after it" | `docs/PLAN.md` line 157 (calendar row); `docs/submission/README.md` line 4 |
| Nov 20 | Track B's and Track C's report bullets; Gate 3's final statement | `docs/PLAN.md` lines 158 and 442 |
| Nov 21 | sections' proposed dates; the submission folder (TODO D13) | `docs/PLAN.md` lines 433 to 440 and 466 |
| Nov 22 | the report draft, assembled by Ritik; AI-use and contribution drafts "with the draft, Nov 22 (proposed)" | `docs/PLAN.md` lines 158, 443, 463, 464 |
| Nov 23 | rehearsal | `docs/PLAN.md` lines 158 and 443 |
| Nov 24 | "the final report and" the final presentation; "submitted Nov 24" | `docs/PLAN.md` lines 443, 466, 503; `docs/submission/README.md` (slides row) |

"Proposed" dates are set nowhere else in the repo (PLAN's own word). Whether Nov 24 is the course's deadline is not stated anywhere: it is the team's plan.

## To check on Canvas or the course page (none of these is answered in the repo)

1. Report: page or word limit; file format (PDF or Word); a required template or section list; whether the supplement counts toward the limit or goes in as an appendix; whether the report is the REPORT.md outline (12 sections) or another structure.
2. Presentation: official length (the plan assumes about 12 minutes), whether there is Q&A time, whether a live demo is allowed, slide format (pptx or pdf), who must present.
3. Rubric or grading criteria, and how the report, slides, demo and code are weighed.
4. The deadline(s): report, slides, demo, code (the plan's Nov 24 is the team's own calendar).
5. Where and how to submit (Canvas upload, email, or a link), the name or shape of the zip, and whether a repository link is accepted: whether the graders have access to the repository (the code link row says "confirm").
6. The contribution statement and the AI-use disclosure: required form, length, and policy on AI use (including the AI rater and AI judges for the hand labels, and Claude Code's use).
7. Any limit on file size (the repo notes only its own 50 MB git rule) and whether the demo file may be included.
