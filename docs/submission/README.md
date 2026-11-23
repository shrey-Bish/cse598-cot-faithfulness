# The submission, Nov 19–24

**Edited by:** Ritik. Set up Nov 13 (14:13) from PLAN's
[submission checklist](../PLAN.md#submission-checklist-nov-1924); made a checklist with one command Nov 19 (10:25).
Every file here reads only the results frozen on Nov 18: the tag `results-freeze-2026-11-18` on `7e1fdc0` (CHECKIN
[§10](../status/CHECKIN.md#10-the-results-freeze-nov-18-the-procedure)). The course's exact requirements (formats,
length and time limits, where and how to submit, the form of the contribution statement and of the AI-use disclosure)
are not in the repo: confirm them against the course page.

## One command

```bash
python3 cot-disclosure/tools/make_submission.py --check     # each piece and its state; writes nothing
python3 cot-disclosure/tools/make_submission.py             # the zip, once every piece is ready
```

The second refuses, naming what isn't ready, while a part we write is missing (or `CONTRIBUTIONS.md` still holds its
placeholder, or `AI_USE.md` still says "to confirm"). Once all are in, it writes
`cot-disclosure/results/submission/cse598_group10_submission.zip` (gitignored): the report, the slides, the
contributions, the AI-use disclosure, every figure (`docs/paper/figures/`: PNG, SVG and CSV), the demo
(`demo/index.html`), `CODE_LINK.txt` (the repository, the freeze tag and its commit, main's commit at the build),
`BUNDLES.sha256` and a `MANIFEST.sha256` of every file. `--with-supplement` adds `docs/paper/supplement/` (whether it
goes in as an appendix: confirm). `--verify-bundles` checks the bundles on this Mac against `BUNDLES.sha256` (all three
matched on Nov 19, 10:22). Stdlib only; tests in `cot-disclosure/tests/test_make_submission.py`.

## The checklist

"Ready" means made and checked; "to write by us" means the team's own words, which no tool writes.

| piece | file | state (Nov 23) | who | by when |
|---|---|---|---|---|
| the report's material | [`docs/paper/REPORT.md`](../paper/REPORT.md): every section's bullets with exact numbers, plain names (codes in parentheses), limits and its figure or table; [`RELATED_WORK.md`](../paper/RELATED_WORK.md); [`CLAIMS.md`](../paper/CLAIMS.md) | ready | — | done Nov 19 |
| **the report** | `docs/submission/report.pdf` or `report.docx`: the prose, from REPORT's bullets (numbers only from FINDINGS, FINDINGS_B, FINDINGS_C); format and length: confirm | **to write by us** | each section's owner (PLAN's writing plan); Ritik merges | draft Nov 22; final Nov 24 |
| the supplement | [`docs/paper/supplement/`](../paper/supplement/), regenerated at the freeze by `tools/make_supplement.py` | ready | — | done Nov 18 |
| the figures | [`docs/paper/figures/`](../paper/figures/): each slide's and each report section's figure, with a CSV of every plotted number | ready | — | done |
| the slide shell | [`docs/presentation/deck.pptx`](../presentation/deck.pptx), built by `tools/make_deck.py` from [`TALK_MAP.md`](../presentation/TALK_MAP.md): a title slide, one slide a map entry (its figure and a short plain title), "Limits and next steps"; no paragraphs, no notes | ready | — | done Nov 19 |
| **the slides** | `docs/submission/slides.pptx` or `slides.pdf`: the shell with our words; format and time limit (about 12 minutes planned): confirm | **to write by us** | each slide's owner (PLAN's map); Ritik assembles | rehearsal Nov 23; presented Nov 24 |
| the presentation kit | [`TALK_MAP.md`](../presentation/TALK_MAP.md) (slide by slide: the point, the figure, the time, the speaker column blank; and "The live run", 12 minutes from the demo, each live moment with its keys and its fallback slide) and [`QA_FACTS.md`](../presentation/QA_FACTS.md) (likely questions and the facts to point to) | ready | — | done Nov 19 |
| the demo | [`docs/demo/index.html`](../demo/index.html), the answer sheet in three parts (how we did it, run it, what we found): one file, opens offline; its DATA the tag's (Nov 22). The earlier Hint Explainer: [`archive/superseded/explainer_2026-11-14/explainer.html`](../../archive/superseded/explainer_2026-11-14/explainer.html) | ready | — | done Nov 22 |
| the front door | [`README.md`](../../README.md) (the question, the answer, the five findings, the demo, the folders), [`REPRODUCE.md`](../../REPRODUCE.md), [`CITATION.cff`](../../CITATION.cff) and a short README in each main folder (Nov 23) | ready | — | done Nov 23 |
| the code link | https://github.com/shrey-Bish/cse598-cot-faithfulness, the tag `results-freeze-2026-11-18` (`7e1fdc0`); the tool writes it into `CODE_LINK.txt`; the graders' access: confirm | ready | — | the tag Nov 18 |
| the bundles' sha256s | [`BUNDLES.sha256`](BUNDLES.sha256): Track A 1,704.3 MB, Track B 60.1 MB, Track C 5.1 MB (built and verified Nov 18; the [freeze log](../../archive/sessions/2026-11-18/2026-11-18_2044_ALL_freeze.md)); the bundles stay local | ready | — | done Nov 18 |
| **the contribution statement** | [`CONTRIBUTIONS.md`](CONTRIBUTIONS.md): the placeholder "Contributions: to be completed before submission"; the facts in PLAN's "Who runs what" and each track's TODO; form: confirm | **to write by us** | Ritik | before submission |
| **the AI-use disclosure** | `docs/submission/AI_USE.md`, written from [`AI_USE_INVENTORY.md`](AI_USE_INVENTORY.md); form and policy: confirm | **to write by us** | each member for their own work; Ritik merges | Nov 22 |

## The inventory's "to confirm" lines

The AI-use inventory records what the repo shows; these lines it can't, so the member each names confirms or corrects
it before `AI_USE.md` is written:

1. **Ritik:** from when Claude Code was used (the git history starts Oct 2, the session logs Oct 27).
2. **Ritik:** which prompts Claude in chat (claude.ai) drafted for planning, and from when.
3. **Arsha:** Track B's own AI use, from Nov 6 (her `docs/trackB/sessions/`).
4. **Shrey:** Track C's own AI use, from Oct 30 (his `docs/trackC/sessions/`).
5. **Each member:** what you checked by hand in AI-written code, docs or analyses.

## The folder at submission (Nov 24)

```
docs/submission/
  README.md               this page
  AI_USE_INVENTORY.md     the facts the disclosure is written from
  AI_USE.md               the AI-use disclosure, written by us
  CONTRIBUTIONS.md        the contribution statement, written by us (now the placeholder)
  BUNDLES.sha256          the three bundles' sha256s, from the freeze
  report.<pdf|docx>       the final report
  slides.<pptx|pdf>       the deck, from docs/presentation/deck.pptx
docs/presentation/        the slide shell, TALK_MAP.md, QA_FACTS.md
docs/demo/index.html      the demo (linked, and copied into the zip)
```

A file over 50 MB doesn't go in git (the pre-push check refuses it): it goes where the course page says, and this
page names where.
