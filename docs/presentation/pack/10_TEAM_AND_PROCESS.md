# 10. Team and process: facts for CONTRIBUTIONS.md

Facts only, for Ritik to write `docs/submission/CONTRIBUTIONS.md` (now the placeholder "Contributions: to be completed before submission") and slide S13 in his own words. Nothing here characterizes effort. Names: Ritik Agarwal, Arsha Jindal, Shrey Bishnoi. Gathered Nov 24 from `git log`, the track pages, REPORT's headings, TODO, PLAN, the session-log INDEX and the submission folder. Counts are counts of commits or files, not of work.

## 1. The three tracks and who owned them

| track | what it is | owner and dates (source) |
|---|---|---|
| Track A | Explain and fix Olmo 3 7B Think's hint following: inside the model (readout, attention, patching), the trained fixes, Gate 3 | Ritik, to the end ([`docs/tracks/TRACK_A.md`](../../tracks/TRACK_A.md): "Owner: Ritik"; [`TRACK_A_FIX.md`](../../tracks/TRACK_A_FIX.md): "By: Ritik"; PLAN "Who runs what": "Track A: Ritik, to the end") |
| Track B | Test widely: the hint from a tool, the user and other channels across models; the answer after a tool call; authority; thinking effort | Ritik until Nov 6, Arsha from Nov 6 ([`TRACK_B.md`](../../tracks/TRACK_B.md): "Edited by Ritik until Nov 6, then Arsha"; CLAUDE.md: "Track B (Arsha, from Nov 6)"). B20's runs were on Arsha's own Sol account from Nov 5 (PLAN) |
| Track C | The agent team: a solver, a reviewer that sees more of the solver's work, a checker | Ritik's work through C18; Shrey owner from Oct 30 ([`TRACK_C.md`](../../tracks/TRACK_C.md): "Shrey, owner from Oct 30"; "The work through C18 is Ritik's; from Oct 30 Track C is yours"); the final handoff Nov 3 (PLAN) |

Rules in the repo about authorship, quoted:
- TODO's Owners bullet (`docs/status/TODO.md` line 15): "Ritik did the work so far in all three tracks. Track C is Shrey's from Oct 30 ... Track B goes to Arsha on Nov 6 ... 'Shrey, from Oct 30' or 'Arsha, from Nov 6' in the owner column says who takes an open item over, never who did past work."
- FINDINGS numbering: Track B's later finding is FB1 (Arsha's, read Nov 7, merged Nov 8, in `docs/trackB/FINDINGS_B.md`); Track C's later findings are FC1 to FC4 (Shrey's, run and read Nov 6, in `docs/trackC/FINDINGS_C.md`, merged Nov 7). The "track" column of [`results_at_a_glance.md`](../../paper/tables/results_at_a_glance.md) assigns the F-findings: Track A: F1 to F14, F20, F26, F27, F28, F32, F36, F38, F39, F41 to F45; Track B: F15, F16, F17, F25, F29, F35, F37, F40, FB1; Track C: F18, F19, F21 to F24, F30, F31, F33, F34, FC1 to FC4. (TODO's rule above: a finding's track names its topic, and Ritik did the Track B and Track C work before the handoffs.)
- The label rule (INDEX, Nov 4 correction): "Shrey did no labeling. Ritik's sheets are the only human labels, so every kappa so far is human-vs-AI agreement" (`archive/sessions/INDEX.md` lines 102 to 103).

## 2. Who wrote the report sections (REPORT.md headings, `docs/paper/REPORT.md`)

| section | heading's owner(s) |
|---|---|
| 1 Introduction | Ritik |
| 2 Setup | Ritik; Track B's part, Arsha |
| 3 Methods | Ritik ("each track's section, its owner") |
| 4 The failure: tools pull harder | Arsha |
| 5 Level 1, inside the model | Ritik |
| 6 Level 2, in the words | Ritik, Arsha |
| 7 Fixing it | Ritik |
| 8 Level 3, between agents | Shrey |
| 9 Across agents, and the pipeline | Shrey |
| 10 Limits and threats | everyone |
| 11 Related work, 12 Conclusion and deployment | everyone |

PLAN's writing plan (PLAN lines 433 to 443) adds: §2's and §3's Track B parts Arsha, Track C's parts Shrey; §10 each owner writes their track's limits and Ritik merges (proposed); §11 and §12 everyone, Ritik merges (proposed). Track B's and Track C's report bullets are in `docs/trackB/REPORT_B.md` and `docs/trackC/REPORT_C.md`.

PLAN's slide owners (PLAN line 461, the older 13-slide map): Ritik 1, 3, 4, 9, 10; Arsha 2, 6, 7, 8; Ritik and Shrey 5; Shrey 11, 12; everyone 13. (The pack's planned slide list S1 to S13 differs; map owners from the slide's finding.)

## 3. Git history, as counts

Run on `trackA-nosol` and across all refs on Nov 24 (author name as git records it; Ritik's git author name is "Ritik", the other two are the full names):

| author | commits on all refs | commits on the current branch (HEAD, 468 commits) | first and last commit dates (all refs) |
|---|---|---|---|
| Ritik | 607 | 451 | Oct 4 to Nov 24 |
| Shrey Bishnoi | 13 | 13 | Oct 2 to Nov 7 |
| Arsha Jindal | 4 | 4 | Nov 7 to Nov 15 |

(Total 624 commits on all refs; the repository's first commit is dated Oct 2. The repo has 13 branches, including `main`, `trackB-main`, `trackC-main`.)

Commits by Shrey Bishnoi (dates):
- Oct 2 and Oct 4: 5 commits (the progress round: "Add hint-acknowledgment harness, results, and progress deck", "Final progress-round results and plain-language slides", "Rework progress slides for first-time viewers", "Add tool-hint, reviewer and leak results to the progress deck", "Restore .gitignore rules and .env.example").
- Nov 6 and Nov 7: 8 commits on Track C (the setup, C19, C25, C20, C26 run and read on Nov 6; the report bullets `docs/trackC/REPORT_C.md`; C24's tables `agents/trackc_tables.py`; two merges of `origin/main` into `trackC-main`).

Commits by Arsha Jindal (dates): Nov 7 (B20 read by its rule, all 4,860 runs, FB1), Nov 14 (B18's table with B20's rows, and the re-reads of B16, B19, B17 and B24), Nov 15 (slide 7 with B24's arms; a merge of main into `trackB-main`). The Nov 7 commit's message names Arsha's B20 runs as "all 4,860 runs".

Commits touching a path (all refs; each counts a commit once for that path):

| path | Ritik | Shrey Bishnoi | Arsha Jindal |
|---|---|---|---|
| `docs/trackB` | 22 | 0 | 3 |
| `docs/trackC` | 10 | 8 | 0 |
| `cot-disclosure/agents` (Track C's code) | 25 | 4 | 0 |
| `docs/paper` | 105 | 0 | 2 |
| `docs/paper/REPORT.md` | 19 | 0 | 0 |
| `docs/FINDINGS.md` | 74 | 0 | 0 |
| `docs/trackB/FINDINGS_B.md` | 4 | 0 | 1 |
| `docs/trackC/FINDINGS_C.md` | 2 | 3 | 0 |
| `docs/demo` | 11 | 0 | 0 |
| `docs/presentation` | 5 | 0 | 0 |
| `cot-disclosure/finetune` (Track A's code) | 217 | 0 | 0 |
| `archive` | 146 | 0 | 0 |

Facts that matter for reading these counts (from the repo):
- TODO line 18 (written before the later commits) says: "The repo has no commits by Arsha and none by Shrey after Oct 4, so their local work can't be seen from here." Their Nov 6 to Nov 15 commits arrived later through `trackB-main` and `trackC-main` merges.
- Track B's and Track C's own session logs are in `docs/trackB/sessions/` (3 logs: Nov 7, Nov 14, Nov 15) and `docs/trackC/sessions/` (6 logs: Nov 6 and Nov 7). Track A's and the shared logs are in `archive/sessions/` (133 logs plus 19 daily logs, named by date, time and track A, B, C or ALL).
- CLAUDE.md and the git hooks require every commit to carry a team member's own identity (hashes in `cot-disclosure/configs/team_identities.txt`; no emails are written in the repo), with no AI author, co-author or "generated with" line; so no commit lists an AI tool.
- Hand labels: Ritik's (see §5).

## 4. Timeline of key dates (all 2026; MST times from the session logs)

Sources: `archive/sessions/INDEX.md` (one row per log), `docs/PLAN.md`, `docs/status/TODO.md`, FINDINGS, the freeze tag.

**Before the plan**
- Oct 2 to Oct 6: the progress round (git history; tag `progress-oct-2026`).
- Oct 20 to Oct 26: Track A's Steps 1 to 10 on Voyager and Sol (`TRACK_A.md`: Step 1 done Oct 21; the base model in the pinned format Oct 22; takeover curves Oct 24; Steps 6 and 7 finished Oct 27).
- Oct 25: Gate 1: missed (recorded Oct 27; TODO G1); the fallback applied (Track B narrows to the providers that work, Track C on Voyager only).
- Oct 27 (13:05): session logs start, one per run or stop; first Sol jobs the same day.

**Main runs**
- Track B on Voyager: Qwen3 30B Thinking final Oct 28 03:25 (F15); Qwen3 30B Instruct Oct 28 05:45 (F16); Olmo 3 7B Think and Track C's C4 Oct 28 18:23 (F17, F18).
- Track A's training on Sol: LoRA and tags done Oct 28 (F20); Gate 3's final on all six systems Oct 31 16:40.
- Qwen3-8B thinking on and off (F29) Oct 30; Qwen3-8B's readout (F36) Nov 1; B16 Oct 31 to Nov 1 (F35); B17 Nov 3 (F37); B24 on Voyager Nov 4 (F40); B20 on Arsha's Sol account Nov 5 to Nov 6 (complete Nov 6, 21:11); C19, C25, C20, C26 run Nov 6 (FC1 to FC4); A39, A40 to A42 read Nov 7 (F41 to F44); B1R2 read Nov 13 (F38).

**Pre-registrations** (a log written and committed before the runs; the names in `archive/sessions/*/`; 23 files named `*prereg*`)
- Oct 29: C13 (16:45 log "sol-fixes-and-c13-prereg"), C14, C15 and B15 (23:00).
- Oct 30: C16 (08:50), Set A step 9 (10:10), C17 (10:25), Qwen3-8B mechanism (11:45), C18 (17:00).
- Oct 31 (22:20 to 22:45): B16, C19, C20, C25, C26, B17, A18, A38.
- Nov 3: E2 and A39 (11:30), B20 (12:19).
- Nov 4: B24 (03:37), the LLM-judge protocol for the hand labels (17:45).
- Nov 5: A40 (09:18). Nov 6: A41, A42 (11:21, 11:22). Nov 7: L6 (20:25).
- PLAN's pre-registration rule: each new experiment has code with CPU tests, a pre-registration session log and a dry run before it runs. The supplement holds the ledger (`docs/paper/supplement/`).

**Gates**
- Gate 1 (Oct 25): missed (above).
- Gate 2: marked Nov 8, 15:12: met for the tool-versus-user gap on every model tested; the label part not met by its pre-registered rule (TODO G2).
- Gate 3: interim Oct 30 09:10 (F28); met, final Oct 31 (F28); L4 part 1 read Nov 3; its final statement was due Nov 20 (PLAN); the Nov 23 commit message records "Gate 3 approved by Ritik as drafted (PLAN, ONE_PAGE)".

**Label rounds**
- L3 (Gate 2's labels; F3): rater sheets made Oct 31 (20:50 log); Ritik's rater 1 sheets placed Nov 1 (12:40); kappa read Nov 3 (10:00); LLM judges Nov 4 (protocol 17:45, results 17:56); Ritik's blind re-look of 7 cells recorded Nov 4 (21:24).
- L4 (Gate 3's blind sheets): built Oct 30 (10:45); part 1 read Nov 3 (F28).
- L6 (F45): pre-registered Nov 7 (20:25); reduced and its sheet built Nov 8 (14:55 log: 84 rows); Ritik's labels frozen Nov 13 09:46; judged 09:48 to 09:49; read Nov 13 (F45).

**Handoffs and check-ins**
- Track C to Shrey: Oct 30 (log 18:05 "handoff-to-shrey"); final handoff Nov 3 (`START_HERE`, bundle `trackC_20261105.zip` from Nov 5).
- Track B to Arsha: Nov 6 (09:18 handoff; bundle `trackB_20261106.zip`).
- Check-ins and merges of `trackB-main` and `trackC-main` into `main`: Nov 6 or 7, 12, 15 and 18 (PLAN: Track B Nov 6, 12, 15, 18; Track C Nov 7, 12, 15, 18).

**Freeze and submission**
- Nov 18: results freeze (tag `results-freeze-2026-11-18` on `7e1fdc0`); no new runs after it.
- Nov 19: last materials (REPORT bullets complete; the slide shell `deck.pptx` built; the presentation kit).
- Nov 20: Track B's and Track C's report bullets; Gate 3's final statement due. Nov 22: report draft due (PLAN). Nov 22 to Nov 23: the demo rebuilt as an answer sheet; Nov 23: the repo as a front door (README, REPRODUCE, CITATION); rehearsal planned Nov 23.
- Nov 24: presentation (about 12 minutes planned, `TALK_MAP.md`) and final report (PLAN calendar; `docs/submission/README.md`: "rehearsal Nov 23; presented Nov 24"; report "final Nov 24"). Where and how to submit: the repo does not say (see 11_REQUIREMENTS.md).
- Submission folder (`docs/submission/`): the checklist marks the report, the slides, the contribution statement and the AI-use disclosure "to write by us"; everything else "ready" as of Nov 23.

## 5. Who made the hand labels, and the AI used as rater or judge

- Every hand label in L3, L4 part 1 and L6 is Ritik's (L6 "alone, with no AI help", the Nov 13 09:37 log's section 0).
- Rater 2 for L3 and L4 part 1 was ChatGPT 5 Astra High (OpenAI), "AI rater 1": first recorded as a second human rater, corrected Nov 4 at 17:51 (the 17:42 log): it was an AI model, not a teammate.
- LLM judges, by the protocol pre-registered Nov 4 (17:45), read 17:56: J-opus (Claude Opus, fresh Claude Code sub-agents, one per batch, told to use no tools); J-qwen (Qwen3 30B Instruct) and J-olmo (Olmo 3.1 32B Instruct) on ASU Voyager at temperature 0.
- L6's check: J-opus (`claude-opus-5-5`), 2 fresh sub-agents of 42 rows each, blind to systems; Ritik's labels frozen (sha256) before any judge ran. FINDINGS F45 states Ritik vs J-opus kappa 0.961; "not blind in practice (32 of LoRA's 42 guessed trained)".
- Ritik's 7 re-look labels, written in his own words, were put into the guide's five categories by Claude Code (Claude Opus) at his request (Nov 4, 21:24), his words shown beside each.
- Gate 2's label part: not met by its rule; no claim rests on the hand labels (F3's status in FINDINGS).

## 6. AI-use facts, from [`docs/submission/AI_USE_INVENTORY.md`](../../submission/AI_USE_INVENTORY.md) (Nov 13, updated Nov 19)

The inventory says it is "Facts only, for the team to write the AI-use disclosure from" (`AI_USE.md`, the team's own words; "form and policy: confirm against the course page"), that "each line says where the repo records it", and that "a line marked *to confirm* is something the repo doesn't record: the member it names confirms or corrects it". `AI_USE.md` is not yet written (the checklist marks it "to write by us").

**Assistance (AI that helped do the work)**
1. Claude Code (Anthropic's coding agent, in VS Code and the terminal): writing and running code, tests, analyses and figures; writing the docs, session logs and handoff guides; reading results by their pre-registered rules (each reading's code has tests, written before it). Ritik's Track A sessions and the shared docs. To confirm (Ritik): from when; the git history starts Oct 2 and the session logs Oct 27. Recorded in `archive/sessions/` (each log's section 0 "Input" is the instructions given).
2. Claude Code's sub-agents ("helpers", at most 2 at once from Nov 13's rule): parallel pieces of a session, namely B1R2's report and figure (Nov 13); the demo and slide 5's figure (Nov 13); the Hint Explainer, the glossary, the README's plain rewrite, the slide figures' plain labels and the START_HERE drafts (Nov 14); the explainer's presentation fixes after the freeze (Nov 18); the related-work look-ups on arXiv, the report's bullets completed from FINDINGS, the slide shell (`deck.pptx`, built by `tools/make_deck.py`) and the presentation kit (Nov 19). Ritik's sessions; helpers never commit.
3. Claude Code, mapping words to labels: Ritik's 7 re-look labels (Nov 4, 21:24), above.
4. Claude Code, the rules it works under: every commit is the member's own, with no AI author, co-author or "generated with" line (`CLAUDE.md` and `.claude/settings.json`, Nov 5; enforced by git hooks, Nov 6), on all three members' clones.
5. Claude in chat (claude.ai): planning, drafting the prompts given to the Claude Code sessions. To confirm (Ritik): which prompts and from when; named in Ritik's Nov 13 prompt ("Claude in chat for planning").
6. Track B's and Track C's own use: "to be added by Arsha (Track B, from Nov 6) and Shrey (Track C, from Oct 30)"; their session logs are in `docs/trackB/sessions/` and `docs/trackC/sessions/`.

**Labels: AI as a rater or a judge**: see §5 (ChatGPT 5 Astra High as AI rater 1 for L3 and L4 part 1; LLM judges J-opus, J-qwen, J-olmo; L6's J-opus check).

**Not assistance: the models we studied.** The inventory lists these as experiments' subjects, run by the experiments' code, who wrote no part of the work: Track A: Olmo 3 7B Think (Voyager and Sol) and its trained versions (Sol); Olmo 3 32B Think and Qwen3 30B Thinking in the first tests (F3); Qwen3-8B (Sol). Track B: Qwen3 30B Thinking and Instruct, Olmo 3 7B Think (ASU Voyager); Qwen3-8B and gpt-oss-20b (Sol); Gemma 4 26B-A4B, Nemotron 3 Nano 30B-A3B and Granite 4.2 8B (Sol, B20). Track C: the solver, reviewers and checker (Voyager and Sol), as FINDINGS F18 to F34 and FC1 to FC4 name them. No paid API was called ($0 spent; PLAN, Budget).

**Done by hand (what the repo records)**
- Every hand label in L3, L4 part 1 and L6 is Ritik's.
- Every pre-registration was committed before its runs (the supplement's ledger), and each decision in a session's section 0 "Input" is the member's.
- To confirm (each member): what each of you checked by hand in AI-written code, docs or analyses.

**The inventory's five "to confirm" lines** (also in `docs/submission/README.md`): Ritik, from when Claude Code was used; Ritik, which prompts Claude in chat drafted, and from when; Arsha, Track B's own AI use from Nov 6; Shrey, Track C's own AI use from Oct 30; each member, what you checked by hand.

**Other AI-related facts in the repo**
- CLAUDE.md: Claude, Anthropic or any AI tool is never an author, committer or co-author; hooks refuse any such commit or message line.
- This presentation pack, and the Nov 23 to Nov 24 demo and slide-shell work, are logged as Claude Code sessions in `archive/sessions/` (for example the Nov 19 10:18 and Nov 23 09:10 logs); the inventory (updated Nov 19) lists the Nov 18 and Nov 19 helper uses but not the later ones: Ritik may want to add Nov 20 to Nov 24 to the disclosure.

## 7. Things the repo does not say (for Ritik to supply)

- Hours or effort per person (the repo records none; do not infer it from commit counts).
- Whether Arsha and Shrey worked on their local clones beyond what was committed (TODO line 18).
- The form the course wants for the contribution statement and the AI-use disclosure ("confirm against the course page", PLAN and `docs/submission/README.md`).
- Who presents which slide (TALK_MAP's speaker column is blank, "for us to fill").
