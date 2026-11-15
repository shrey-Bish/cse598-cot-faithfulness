# AI use: the inventory

**Edited by:** Ritik. Written Nov 13 (14:13). **Facts only, for the team to write the AI-use disclosure from**
(`AI_USE.md`, the team's own words; form and policy: confirm against the course page). Each line says where the repo
records it. A line marked *to confirm* is something the repo doesn't record: the member it names confirms or corrects
it. Arsha and Shrey add their own tracks' uses.

## 1. Assistance: AI that helped do the work

| tool | used for | who, when | where it is recorded |
|---|---|---|---|
| **Claude Code** (Anthropic's coding agent, in VS Code and the terminal) | writing and running code, tests, analyses and figures; writing the docs, session logs and handoff guides; reading results by their pre-registered rules (each reading's code has tests, written before it) | Ritik's Track A sessions and the shared docs. *To confirm (Ritik):* from when; the git history starts Oct 2 and the session logs Oct 27 | the session logs, [`archive/sessions/`](../../archive/sessions/INDEX.md), each with its §0 "Input" (the instructions given) |
| Claude Code's sub-agents ("helpers", at most 2 at once from Nov 13's rule) | parallel pieces of a session, e.g. B1R2's report and figure (Nov 13, [the 11:09 log](../../archive/sessions/2026-11-13/2026-11-13_1109_A_b1r2-results.md)); the demo and slide 5's figure (Nov 13, [the 13:36 log](../../archive/sessions/2026-11-13/2026-11-13_1336_A_demo-freeze-submission.md)); the Hint Explainer, and the glossary, the README's plain rewrite, the slide figures' plain labels and the START_HERE drafts (Nov 14, [the 22:15 log](../../archive/sessions/2026-11-14/2026-11-14_2215_A_explainer.md)) | Ritik's sessions; helpers never commit | those logs |
| Claude Code, mapping words to labels | Ritik's 7 re-look labels, written in his own words, were put into the guide's five categories by Claude Code (Claude Opus) at his request, before any comparison; his words are shown beside each | Nov 4, 21:24 | [the 21:24 log](../../archive/sessions/2026-11-04/2026-11-04_2124_ALL_relook-recorded.md) |
| Claude Code, the rules it works under | every commit is the member's own, with no AI author, co-author or "generated with" line: `CLAUDE.md` and `.claude/settings.json` (Nov 5), enforced by git hooks (Nov 6) | all three members' clones | [the Nov 5 23:13 log](../../archive/sessions/2026-11-05/2026-11-05_2313_ALL_shrey-handoff.md), [the Nov 6 11:07 log](../../archive/sessions/2026-11-06/2026-11-06_1107_ALL_a40-gate-no-ai-sol-busy.md); Track B's and Track C's `START_HERE.md`, §11 |
| **Claude in chat** (claude.ai) | planning: drafting the prompts given to the Claude Code sessions | *To confirm (Ritik):* which prompts and from when. Named in Ritik's Nov 13 prompt ("Claude in chat for planning") | each session log's §0 "Input" records what a prompt decided, e.g. [Nov 8, 14:55](../../archive/sessions/2026-11-08/2026-11-08_1455_ALL_l6-gate2-b20-merge.md), Nov 13 [09:37](../../archive/sessions/2026-11-13/2026-11-13_0937_A_l6-judge-reading.md), [11:00](../../archive/sessions/2026-11-13/2026-11-13_1100_A_b1r2-freeze-wording.md) and [13:36](../../archive/sessions/2026-11-13/2026-11-13_1336_A_demo-freeze-submission.md) |
| Track B's and Track C's own use | *to be added by Arsha (Track B, from Nov 6) and Shrey (Track C, from Oct 30)* | | their `docs/trackB/sessions/` and `docs/trackC/sessions/` |

## 2. Labels: AI as a rater or a judge

Ritik's labels are the final labels in every hand-label set; AI raters and judges are their reliability check, under
the LLM-judge protocol (pre-registered Nov 4), always disclosed.

| set | AI used | how | when | where it is recorded |
|---|---|---|---|---|
| L3 (Gate 2's labels; F3) and L4 part 1 (Gate 3's; F28) | **ChatGPT 5 Astra High** (OpenAI), "AI rater 1": the second sheets | run by Ritik with the rater packet's guide and the blind sheets. First recorded as a second human rater; corrected Nov 4, 17:51: it was an AI model, not a teammate | Nov 3 | [the Nov 4 17:42 log](../../archive/sessions/2026-11-04/2026-11-04_1742_ALL_label-correction.md) |
| L3 and L4 part 1 | **LLM judges:** J-opus, **Claude Opus** (fresh Claude Code sub-agents, one per batch: L3 in 2, L4 part 1 in 6, told to use no tools); J-qwen, **Qwen3 30B Instruct**, and J-olmo, **Olmo 3.1 32B Instruct**, both on ASU Voyager (temperature 0); and AI rater 1's sheets | by the protocol: Ritik against the judges' majority, kappa per cell; Gate 2's label part read **not met** | pre-registered Nov 4, 17:45; read 17:56 | [the 17:45 log](../../archive/sessions/2026-11-04/2026-11-04_1745_ALL_llm-judge-prereg.md), [the 17:56 log](../../archive/sessions/2026-11-04/2026-11-04_1756_ALL_llm-judge-results.md) |
| L6 (F45) | Ritik labelled the sheet alone, with no AI help; then **J-opus, Claude Opus** (`claude-opus-5-5`), 2 fresh sub-agents of 42 rows each, blind to systems, as the check (kappa 0.961) | Ritik's labels frozen (sha256) before any judge ran | Nov 13, 09:46 (frozen); 09:48–09:49 (judged) | [the 09:37 log](../../archive/sessions/2026-11-13/2026-11-13_0937_A_l6-judge-reading.md), [the 09:51 reading](../../archive/sessions/2026-11-13/2026-11-13_0951_A_l6-reading.md) |

## 3. Not assistance: the models we studied

These models are the experiments' subjects, run by the experiments' code; they wrote no part of the work. Track A:
Olmo 3 7B Think (Voyager and Sol) and its trained versions (Sol); Olmo 3 32B Think and Qwen3 30B Thinking in the
first tests (F3); Qwen3-8B (Sol). Track B: Qwen3 30B Thinking and Instruct, Olmo 3 7B
Think (ASU Voyager); Qwen3-8B and gpt-oss-20b (Sol); Gemma 4 26B-A4B, Nemotron 3 Nano 30B-A3B and Granite 4.2 8B (Sol,
B20). Track C: the solver, reviewers and checker (Voyager and Sol), as FINDINGS F18–F34 and FC1–FC4 name them. No paid
API was called (/bin/zsh spent; PLAN, Budget).

## 4. What the repo records as done by hand

- Every hand label in L3, L4 part 1 and L6 is Ritik's (L6 "alone, with no AI help", the Nov 13 09:37 log's §0).
- Every pre-registration was committed before its runs (the supplement's ledger, `docs/paper/supplement/`), and each
  decision in a session's §0 "Input" is the member's.
- *To confirm (each member):* what each of you checked by hand in AI-written code, docs or analyses.
