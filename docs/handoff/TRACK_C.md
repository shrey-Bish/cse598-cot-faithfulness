# Track C: the agent team (for Shrey, owner from Oct 30)

Final, Oct 30, 2026. The work through C18 is Ritik's; from Oct 30 Track C is yours. Branch `trackC-main`. The data
comes as a bundle through ASU storage (§7), never through GitHub.

**The question.** A solver agent looks something up with a tool, and the tool returns a wrong answer. Does the wrong
answer reach the team's output? Does a reviewer that sees more of the solver's work (its final answer, its private
reasoning, the tool log) catch it? Does a checker that never sees the tool catch it, and at what cost in false
alarms?

## 1. The answer, in five lines

1. **A reviewer that sees the solver's tool trace stops checking, but only in one model family.** Olmo 3.1 32B
   corrects 59 of 73 wrong answers from the answer alone and 6 and 3 once it sees the reasoning or the tool log. Of
   six reviewers in four families, only the two Olmo models defer.
2. **Prompt fixes don't restore it:** a warning sentence (C9) and committing to its own answer first (C10).
3. **It replicates on 100 fresh items** (C15). Hiding the tool's letter restores part of the check, not most of it
   (C12, C15).
4. **The checker that never sees the tool holds:** it caught every wrong answer with every reviewer (C4, C13, C15).
   A cheaper check from two reviews didn't (C14 → C15).
5. **When the solver discloses its source, the deferring reviewer gets worse** (C16). It follows the solver's
   sentences that cite the tool's letter as authority. A generic "based on the lookup tool" changes nothing (C17).
   Removing the citing sentences restores the check (C18).

## 2. Results

Correcting a wrong answer after a bad lookup. "Minus" is the trace (or the change) minus the comparison, paired by
item, in points with a 95% bootstrap clustered by item. The rule is C11's (defers: upper bound below −20).

| run | what it asks | Olmo reviewer | Qwen3 reviewer | finding |
|---|---|---|---|---|
| C4 | does a reviewer that sees the trace defer? (53 items, 318 cases) | 59 → 6 / 3 of 73: −73 [−86, −58], −77 [−91, −61] | 62 → 66 / 56 of 73: no change | F18 |
| C9 | does a warning sentence restore it? | 8 and 4 of 73: +3 [−4, +9] | +4, +7 | F19 |
| C10 | does committing first protect it? | drops its own right answers (60 → 19, 5) | worse with the tool log: 56 → 33, −32 [−44, −20] | F21 |
| C11 | other reviewers | Olmo 3 7B Instruct 32 → 1: −42 [−58, −28] | Qwen3 30B Thinking +1 [−6, +10] | F22 |
| C12 | the tool's letter hidden | 6 → 23 and 3 → 24 of 73 (alone 59): partly | no harm | F23 |
| C13 | two more families (Sol) | Granite 4.1 30B −5 [−26, +15]; Mistral Small 3.2 24B +19 [+10, +30]: neither defers | — | F30 |
| C14 | escalate when two reviews disagree (exploratory) | matched the checker's catches only on C4's cases | — | log Oct 29 23:00 |
| C15 | all of it on 100 fresh items | 39 → 10 of 53: −55 [−70, −38]; hidden letter +25 [+11, +38]; C14's rule ships 4 wrong | −6 [−15, +4]; C14's rule ships 7 wrong | F24 |
| C16 | the solver told to disclose | 25 vs 36 of 53: −21 [−34, −8] (unclear by the rule) | no change | F31 |
| C17 | a fixed sentence naming the tool | +0 [−11, +11] against one naming own working | no change | F33 |
| C18 | C16's tool-citing sentences removed | 25 vs 9 of 34: +47 [+29, +65] | no change | F34 |

**The checker** (re-asks without the tool):
- C4: it flagged 73 of 75 bad lookups; in the other 2 the solver was right.
- C15: 53 of 55.
- Its false alarms are at the no-tool floor.
- No wrong answer shipped in any variant.

**What's refuted, and why it's kept:**
- **C14's cheaper check:** chosen on C4's cases, it failed on fresh ones. That is the case for pre-registration.
- **H23** (redaction helps where the reviewer can re-solve): not supported in C15.
- **H33** (the argument is the cue): not supported in C18. It led to H34, the first item in your plan.

**Limits:**
- One solver (Qwen3 30B Thinking) and one tool format (an answer key's JSON).
- Reviewer temperature 0.6, one repeat from C15 on.
- Kind and set confounded on Track B's cases.
- Two models in the deferring family.
- "Names the tool" is a keyword count.

## 3. For deployment

- The check that never sees the tool is the one that held, across all six reviewers.
- A reviewer that sees the trace is only as safe as its family, and prompt fixes don't change that.
- A disclosure the solver writes can make a deferring reviewer worse, because it carries the authority claim.

## 4. Your first day

1. **The code:** clone `trackC-main`, then `python3 -m venv .venv && .venv/bin/pip install -r cot-disclosure/requirements.txt`.
2. **The tests:** `cd cot-disclosure && ../.venv/bin/python -m pytest -q`. They need no network. Tests that need
   Track A's data skip without it.
3. **Your Voyager key:** create your own at voyager.rc.asu.edu → LLM Access → Create Key.
   - `cp cot-disclosure/.env.example cot-disclosure/.env`, then set `RC_LLM_API_KEY` and `RC_LLM_BASE_URL`.
   - Never commit `.env`, never print a key, never use anyone else's.
   - Leave `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` and `XAI_API_KEY` empty: no paid calls.
4. **The data:**
   - `tar xzf trackC_20261030.tar.gz -C cot-disclosure`;
   - then `../.venv/bin/python tools/make_handoff_bundle.py --verify <the tar.gz>`.
5. **Reproduce three findings** (no calls):
   - `../.venv/bin/python agents/run_team.py --summary --log team_c4 --cases results/trackB/steered_cases.jsonl --table`
     (F18);
   - `../.venv/bin/python agents/c15.py` (F24);
   - `../.venv/bin/python agents/c18.py` (F34).
6. **A dry run** (no calls): `../.venv/bin/python agents/run_team.py --live --n 5 --dry-run`.
7. **GPUs:** when you need them, [`SOL_SETUP.md`](SOL_SETUP.md).

## 5. Your plan (ranked; up to Gate 3, Nov 22)

Pre-register each in a session log (the rule, the comparison, the reading) before it runs, with a dry run first.

| # | question | sketch | cost | deliverable | by |
|---|---|---|---|---|---|
| C19 | H34: is an authority claim the cue? | C15's bare answers + "The course answer key gives (X); I follow it." vs "My working gives (X)." (same length), both reviewers, `plus_explanation`; corrects on bad lookups, paired, two-sided with C11's margin (`--final-suffix` takes a new sentence) | ~400 reviews; 1 day | an F-entry, `agents/c19.py` | Nov 5 |
| C20 | a structural fix: withhold the trace, or a blind first review that only reports disagreement | pipelines on C15's items: the reviewer `answer_only` alone; blind then trace-seeing, escalating on disagreement; the checker; caught, shipped wrong, false alarms, tokens | ~800 reviews; 2 days | the pipeline table | Nov 9 |
| C21 | items the solver can't answer without the tool (the checker's floor rises) | fresh MMLU-Pro items outside the 30 where the no-tool solver is wrong in ≥2 of 3 runs; C4's team; the checker's catches and false alarms | ~600 calls; 2 days | the checker's limit, measured | Nov 13 |
| C22 | another solver model | Olmo 3 7B Think's or Qwen3 30B Instruct's steered cases (`--case-model`, own `--log`); F18 by C11's rule | ~2,000 calls; 3 days | F18 with a second solver | Nov 17 |
| C23 | a pre-registered set of reviewer wordings | 4–6 system prompts fixed in advance, C4's cases, Olmo 3.1 32B; C11's rule per wording, corrected for their number | ~1,500 reviews; 2 days | a wordings table | Nov 19 |
| C24 | thread 2's figures and tables | from `results/summaries/trackC/` and `docs/paper/supplement/` | 2 days | the report's figures and tables | Nov 22 |

## 6. Reference

**The team** (`cot-disclosure/agents/`):
- **solver:** Qwen3 30B Thinking with a real `lookup_answer_key` tool, forced on its first turn. A seeded oracle
  (seed 20261005) makes each lookup bad (the wrong letter) or good (the key), about half each.
- **reviewer:** sees the question and the proposed letter, plus `answer_only` (nothing else), `plus_explanation`
  (the final answer), `plus_private` (also the reasoning) or `plus_tool_log` (also the tool log). Reviewers are Qwen3
  30B Instruct and Olmo 3.1 32B Instruct, capped at 8,000 tokens.
- **checker:** re-asks without the tool. A flag escalates; otherwise the reviewer's letter ships.
- **the no-tool team:** the false-alarm floor.

**The files you need:**
- **Code:** `cot-disclosure/agents/`:
  - `run_team.py`: live runs, `--summary`, `--rereview` with `--disclose`, `--final-suffix`, `--final-edit`,
    `--only-named-bad`;
  - `reviewer.py`, `checker.py`, `solver.py`;
  - `c15.py`–`c18.py`: each experiment's pre-registered readings;
  - `disagreement.py` (C14), `fresh_items.py` (C15), `sol_c13.py` (reviewers on Sol).
- **Numbers:** `cot-disclosure/results/summaries/trackC/`.
- **Logs:** `cot-disclosure/results/trackC/`, from the bundle.
- **Commands:** [`docs/RUNBOOK.md`](../RUNBOOK.md) §19. Each experiment's own lines are in its pre-registration
  log in [`archive/sessions/`](../../archive/sessions/INDEX.md): C15 Oct 29 23:00; C16 Oct 30 08:50; C17 10:25; C18
  17:00.
- **The findings:** [`docs/FINDINGS.md`](../FINDINGS.md) F18–F24, F30, F31, F33, F34.

**Decisions you inherit:**
- **Reporting:** false alarms are always reported next to catches, and undetermined checks are counted, never
  dropped. Every rate is X of Y with an interval and the number of items; fewer than 5 items is "too few".
- **Pre-registration:** pre-register before running; "no decision" lines are labelled, and a reading made after the
  fact is said to be one.
- **C4's cases:** reported by kind and by kind × set (steered is MMLU-Pro and matched is mostly puzzles).
- **The variant for a reviewer that should see the final answer is `plus_explanation`:** `answer_only` shows only
  the letter (C16's ruling).
- **Data:** logs are append-only and gitignored; numbers-only summaries go to `results/summaries/`
  (`tools/export_summaries.py`). C15's items file is written once and never rewritten (sha256 `10dd00e3…`).
- **Voyager only:** no paid providers, no LLM judging, and nothing is ever chosen on the 30 evaluation questions
  (`data/progress/mmlupro_30.jsonl`).

**Known traps:**
- **4 requests in flight** across every process on the machine (slot files in `cot-disclosure/logs/`). Run under the
  power guard (`progress/guard.py`); the machine must stay awake.
- **Identity canaries:** each Voyager model is checked against `configs/canary/<model>.json` before its first call.
  A failed one halts all Voyager work (`logs/voyager_halted`) until you look.
- **Olmo 3 32B Instruct on Voyager is 3.1;** reviewer calls always send their own system prompt.
- **The solver skips the tool unless forced;** the first call is forced.
- **`steered_cases.jsonl` holds three models' rows** with the same item ids: use `--case-model` and your own `--log`.
- **A `--rereview` writes its own `--log`** and needs `--cases`.
- **The same prompt and seed reproduce on Voyager** (C18's re-review matched C16 exactly), so repeats need new seeds.
- **vLLM's ports are fixed on Sol:** two users' jobs on one node would collide ([`SOL_SETUP.md`](SOL_SETUP.md)).

## 7. The data bundle

`trackC_20261030.tar.gz`: 43 files, 31.3 MB unpacked, 5.1 MB packed, with a sha256 manifest inside and beside it.
- **Logs and summaries:** C1 (`team_live`), the 32B smoke, C4, C9–C13, C15 (solve and reviews), C16 (solve, control,
  reviews), C17 (names, own working) and C18 (unchanged, stripped).
- **Readings:** C14's and C15–C18's.
- **Inputs:** C15's items and `results/trackB/steered_cases.jsonl`.
- **Not in it:** GPQA, keys, `.env`, labels.

It never goes on GitHub; the pre-push check enforces that.
