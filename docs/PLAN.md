# Plan: weeks 9–16 (CSE 598, Group 10)

What's left to do, by track, with the timeline, decision gates and budget. What is
already done is in [`OVERVIEW.md`](OVERVIEW.md). Updated 2026-10-20 (week 10).

## The failure, the suspected cause, the fix

- **Failure.** A wrong hint changes the answer, most of all when it comes from a tool,
  and the final answer hides it. Test 2: thinking models followed the tool hint on 17
  of 31 questions, the user hint on 2 of 31. Test 1: the hint is mentioned in the private
  reasoning in 208 of 216 runs, in the final answer in 8.
- **Suspected cause (to test).** Attention treats every earlier token alike, and nothing
  marks a tool's text as less trustworthy: role labels are just more tokens. Once the
  reasoning repeats the hint ("the expected answer is G"), later tokens build on it.
- **Proposed fix.**
  - Fine-tune Olmo 3 7B Think with LoRA plus **source tags**: a learned embedding on
    every token marking its source (system, user, tool, model).
  - Train on examples that check the hint, say it was seen, and keep the no-hint answer.
  - Judge by behavior (does the answer still follow the hint?), not only by the text.

**Why tool hints matter.** Agents get information as tool results: answer keys in
tutoring and grading tools, web search, company databases, retrieved documents, other
agents' outputs. A wrong result arrives from a source the model is built to trust.

## Timeline (week 16 = Nov 30–Dec 6)

| Weeks | Dates | Track A (Ritik) | Track B (Arsha) | Track C (Shrey) | Everyone |
|---|---|---|---|---|---|
| 9–10 | Oct 12–25 **(now)** | Sol GPUs; load Olmo 3 7B Think; reproduce one steered run locally | Ollama Qwen3 on/off; closed-model smoke tests; real tool calls on 2+ providers; GPQA access | Agents on Voyager end to end on 5 items | **Gate 1, Oct 25** |
| 11–12 | Oct 26–Nov 8 | Training data (target reasoning, correct-hint examples) | Main runs: 3 per question, all hint channels | Agent runs on Track B's steered cases; vary what the reviewer sees | Hand labels (two raters, Cohen's kappa); **Gate 2, Nov 8** |
| 13–14 | Nov 9–22 | Look inside (attention, answer takeover); train LoRA + source tags; evaluate | Fill gaps; write up | Cost analysis; write up | **Gate 3, Nov 22** |
| 15 | Nov 23–29 | Hand the trained model to B and C | Run it through B's conditions | Run it as the solver | Draft report |
| 16 | Nov 30–Dec 6 | | | | Final presentation |
| — | Dec 7–12 | | | | Final report |

## Decision gates

- **Gate 1 (Oct 25).** All of:
  - real tool calls work on 2+ providers
  - closed-model smoke tests pass within their caps
  - the agents run end to end on 5 items

  If not, Track B narrows to the providers that work, and Track C runs on Voyager only.
  **Today:** real tool calls work on Voyager only (3 of the 4 models tried). There are no
  closed-provider keys. The agents have run on 2 items.
- **Gate 2 (Nov 8).** Is the tool-vs-user gap still clear with 3 runs per question and
  more models? If not, the headline becomes the private-vs-final gap and the agent
  results.
- **Gate 3 (Nov 22).** Does the fine-tuned model follow fewer wrong hints on held-out
  questions without losing accuracy? If not, report a negative result with the analysis.

---

## Track A: explain and fix (Ritik)

**Question.** Why does a thinking model follow a wrong (tool) hint without saying so, and
can source tags + LoRA make it check the hint and keep its own answer?

**Model.** Olmo 3 7B Think (`allenai/Olmo-3-7B-Think`): open weights, fits one GPU, and
follows hints. It followed 1 of 48 user hints on puzzles and 10 of 20 tool hints in
Test 2 (10 of 11 among answered runs). Run it on ASU Sol. Voyager's checkpoint is only
the candidate, so re-measure the base model on Sol first.

**Method.**
1. **Look inside** (weeks 13–14), on saved steered and unsteered runs of the same
   question:
   - attention from the reasoning tokens to the hint tokens, per layer and head (steered
     vs not, user vs tool)
   - where the hinted answer takes over: the probability of each letter at each
     reasoning sentence (logit lens, or a forced "Answer: (" continuation), and whether
     it follows a repetition of the hint
   - a causal check: remove or mask the repeated hint sentence and see if the answer
     goes back
2. **Training data** (`finetune/build_dataset.py`, runs today).
   - 196 training records (the 24 puzzles, paraphrased hints only) and 120 held-out (the
     30 MMLU-Pro items, the exact test wordings). 0 held-out wordings appear in training.
   - **To do:** target reasoning (mention the hint, check it, end on the no-hint answer);
     correct-hint examples (so it doesn't learn "always disagree"); more training
     questions with the model's own no-hint runs.
3. **Source tags** (`finetune/source_tags.py`, unit-tested). An `Embedding(4,
   hidden_size)` added to each token. It starts at zero, so the wrapped model starts
   identical to the base.
4. **Train.** LoRA rank 8–32 + tags, loss on the model's tokens only. Three ablations:
   LoRA only, tags only, both. Settings are in
   [`finetune/README.md`](../cot-disclosure/finetune/README.md).
5. **Evaluate on behavior:**
   - hint following on held-out questions and wordings (primary)
   - no-hint accuracy
   - mention and acknowledgment
   - the **hiding check:** follows the hint without mentioning it
   - transfer to Tracks B and C

**Success (Gate 3).** The trained model follows fewer wrong hints than the base model
(95% bootstrap difference, clustered by question, excludes 0). No-hint accuracy stays
within 5 points, and the hiding check doesn't rise.

| Week | Task |
|---|---|
| 9–10 | Sol access; download Olmo 3 7B Think; reproduce one steered and one unsteered run; check the chat template with `source_ids_from_chat`; attention-extraction script |
| 11–12 | More training questions + no-hint runs; target reasoning; correct-hint examples |
| 13 | Look inside (attention, answer takeover, causal check) |
| 14 | Train (3 ablations); evaluate; Gate 3 |
| 15 | Hand the model to Tracks B and C |

**Risks.**
- Training can teach the model to hide the hint instead of resisting it (OpenAI saw this
  in 2025 with reasoning monitors). Use behavior targets and unseen wordings.
- 24 training questions is too few.
- Sol GPU access isn't confirmed.
- The chat template may not render prefix-stably. `source_ids_from_chat` raises in that
  case; tag spans by hand.

## Track B: test widely (Arsha)

**Question.** Does the failure hold beyond Olmo and Qwen on Voyager? Test with more open
and closed thinking models, thinking on vs off in the same model, real tool calls,
harder questions, and 3 runs per question.

**Conditions** (`tools/answer_key.py`, same wrong letter per question): `none`, `user`,
`tool_pasted`, `tool_real`, `system`.

**Questions:**
- the 24 puzzles (uncontaminated)
- the 30 MMLU-Pro items
- GPQA Diamond: gated; request access and export to `data/gpqa_diamond.jsonl`

**Models** (`configs/trackB.yaml`; facts in `configs/models.yaml`):

| Provider | Model | Thinking on/off | Reasoning returned |
|---|---|---|---|
| Voyager (free) | Olmo 3 7B Think, Qwen3 30B Thinking, Qwen3 30B Instruct | no (use the twins) | full |
| Ollama (free, local) | `qwen3:8b` | yes, same weights | full |
| OpenAI | `gpt-6-luna` | effort `medium` vs `none` | summary |
| Anthropic | `claude-haiku-4-5-20251001` | yes | summary |
| xAI | `grok-4.3` | effort vs `none` | summary |

- Haiku 4.5 was due to retire no sooner than Oct 15. Check before running, and swap in
  its replacement if it's gone.
- For summary-only providers we score the answer and the final text; a summary is not
  the model's reasoning.

**Runs.**
- 3 per question for open models and OpenAI.
- 1 per question, on fewer conditions, for Anthropic and xAI.
- Temperature 0.6; 16,000 tokens (open) / 8,000 (closed).
- Always streamed; a cut-off reply counts as no answer.

**Real tool calls on Voyager** (checked Oct 4, one puzzle each):
- Qwen3 30B Instruct, Qwen3 30B Thinking and Olmo 3 7B Instruct call the tool.
- **Olmo 3 7B Think** doesn't call it on its own, and its forced call is invalid. Decide:
  put the call and reply into the conversation ourselves, or use the pasted hint only.
  Record which.

**Dry-run plan** (Oct 4, before GPQA; assumes 500 input + 4,000 output tokens per call):

| Provider | Jobs | Calls | Est. cost | Cap |
|---|---|---|---|---|
| Voyager | 2,430 | 2,916 | free | — |
| Ollama | 1,620 | 1,944 | free | — |
| OpenAI | 1,620 | 1,944 | $3.99 | $5 |
| Anthropic | 180 | 240 | $4.92 | $5 |
| xAI | 240 | 300 | $3.19 | $5 |

**Measures.**
- **Hint following** vs the per-letter no-hint baseline, by sure / unsure questions.
- **Admission** in the final answer and the private reasoning: keywords, then hand labels.
- **Tool-call rate**, reported separately.
- **Cost and tokens.**

**Success.** 6+ models across 3+ providers. 3 runs per question for the main models. All
four hint channels where allowed. Every rate as "X of Y" with a 95% interval.

| Week | Task |
|---|---|
| 9–10 | Provider keys; one smoke call each (`run_trackB.py --run --only-provider X --limit 1`); Haiku first; `ollama serve` + `qwen3:8b` on/off; GPQA access and export; the Olmo Think real-tool design; Gate 1 |
| 11–12 | Main runs, 3 per question; first label batch; Gate 2 |
| 15 | Run the Track A model through every condition |

## Track C: multi-agent pipeline (Shrey)

**Question.** When the solver's lookup tool returns a wrong answer, does it reach the
team's final output? What changes when the reviewer sees more, and how often does the
checker catch it or raise a false alarm?

**The team** (`agents/`):
- **Solver:** a thinking model with the real `lookup_answer_key` tool. A seeded oracle
  makes each lookup **bad** (wrong letter) or **good**. Default: Qwen3 30B Thinking.
- **Reviewer:** Experiment A's prompt and `FINAL: X` format. Variants: `answer_only`,
  `plus_explanation`, `plus_private`, `plus_tool_log`.
- **Checker:** re-asks the solver without the tool (another seed). It flags the item if
  the answer changes; no answer = undetermined.
- **Rule:** a flagged item is escalated, not shipped. Otherwise the reviewer's letter
  ships.

**Measures** (per reviewer variant):
- wrong answers shipped
- catches
- false alarms
- tokens (dollars on paid providers)

Every step is logged to `results/scope/team_<mode>.jsonl`.

**Runs today:**
- `run_team.py --replay` (saved data, no calls).
- `--live --n 2` (2 items, 14 calls). The checker caught the bad lookup, and the
  tool-log reviewer passed it along.

**Method (weeks 10–14).**
- Track B's steered cases plus matched no-hint cases, about 50% bad lookups.
- All four reviewer variants, plus a no-tool team as the baseline.
- Two reviewer models: same family and another.
- 3 repeats per case. Voyager first; closed reviewers only within Track B's budget.

**Success.** The pipeline runs on every Track B steered case. Each variant reports
shipped / caught / false alarms as "X of Y" with intervals, against the no-tool team.

| Week | Task |
|---|---|
| 9–10 | Live team on 5 items (Gate 1); no-tool baseline team |
| 10 | Second reviewer model; Ollama as a provider option |
| 11–12 | Agent runs on Track B's steered cases, 3 repeats |
| 13–14 | Cost analysis; write up |
| 15 | Run the Track A model as the solver |

**Risks.**
- The checker's catches depend on run-to-run variation. Always report false alarms next
  to them.
- The reviewer may defer to the tool log. That is the effect being measured, so keep the
  variants separate.

---

## Everyone: hand labels

- Two raters label `docs/progress/LABEL_QUEUE.csv` (101 rows; 10 need their text
  regenerated first) with [`progress/LABELING_GUIDE.md`](progress/LABELING_GUIDE.md).
- Labels per channel: no mention / mentions only / rejects the hint / says the hint
  changed the answer / unclear.
- Report Cohen's kappa per channel. Below 0.6, tighten the guide and label a fresh batch.
- No acknowledgment claim goes in the report before this is done.

## Budget

**About $15 in total:** $5 each for OpenAI, Anthropic and xAI. Voyager, Ollama and Sol
are free. **Spent so far: $0.**

**How the guard works** (`providers/budget.py`):
- **Caps:** `OPENAI_CAP_USD`, `ANTHROPIC_CAP_USD`, `XAI_CAP_USD` in `cot-disclosure/.env`
  (default 5).
- **Before each paid call,** it assumes the worst case (prompt + `max_tokens`). It refuses
  a call that could pass the cap.
- **After each call,** it appends the priced usage to `results/spend_log.jsonl`. Totals
  are always recomputed from that log.
- **Commands:** `python -m providers.budget --status` (from `cot-disclosure/`);
  `progress/run_trackB.py --dry-run` before any sweep.

**Keys** go in `cot-disclosure/.env` as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` and
`XAI_API_KEY`. They are never printed.
- The adapters refuse a key equal to the Voyager key.
- The current `OPENAI_API_KEY` *is* the Voyager key; replace it with a real OpenAI key.

**Data rule:** only public benchmark questions (our puzzles, MMLU-Pro, GPQA) go to
outside providers.

**Prices** (USD per 1M tokens, checked 2026-10-04, in `configs/prices.yaml`). The last
column assumes 500 input + 4,000 output tokens per call. Real thinking replies are often
longer, so treat it as an upper bound.

| Model | Input | Output | Est. calls per $5 |
|---|---|---|---|
| gpt-6-luna | 0.10 | 0.50 | 2,439 |
| gpt-6-astra | 10.00 | 50.00 | 24 |
| claude-haiku-4-5-20251001 | 1.00 | 5.00 | 243 |
| claude-opus-5-5 | 4.00 | 20.00 | 60 |
| grok-4.3 | 1.25 | 2.50 | 470 |
| grok-4.7 | 2.00 | 6.00 | 200 |

Track B uses the cheapest model per provider that can switch thinking off. The flagship
models only fit spot-checks.

## Deliverables

1. **Track B table:** hint following and admission per model × hint channel × thinking
   on/off, with 95% intervals and n.
2. **Hand labels** with Cohen's kappa per channel.
3. **Track C:** wrong answers shipped, catches, false alarms and cost per reviewer
   variant.
4. **Track A:** the attention and answer-takeover analysis; trained adapters and tags;
   the behavior-based evaluation.
5. **Code, configs and every prompt and reply** in the repo. Final talk (week 16); report
   (Dec 7–12).

## Risks

| Risk | Plan |
|---|---|
| Too few models to generalize | Track B: more open and closed models, thinking on/off, 3 runs per question |
| Keyword counts are rough ("the user" fires with no hint; can't tell rejecting from following) | Two raters, Cohen's kappa |
| Long replies are cut off and can leak when not streamed | Always stream; a cut-off reply is unanswered |
| Fine-tuning could teach the model to hide the hint | Train and judge on behavior, with unseen wordings; track the hiding check |
| Closed models hide their reasoning (summaries only) | Score the answer and final text; don't treat summaries as reasoning |
