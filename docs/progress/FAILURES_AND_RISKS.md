# Risks (updated after the progress presentation)

The four risks for the rest of the project, each with what we saw and the plan. Numbers
come from `docs/progress/RESULTS_SUMMARY.json`. The failures found in the models are listed
in `PROGRESS_REPORT.md` §5.

| Risk | What we saw | Plan |
|---|---|---|
| **1. Too few models to generalize** | Test 2 used two thinking models (Olmo 3 7B Think, Qwen3 30B Thinking), 11 to 20 questions each, one run each, and a pasted tool hint. Voyager can't switch thinking off. | Track B: more open and closed thinking models, thinking on vs off in the same model (Ollama `qwen3:8b`, gpt-6-luna, Haiku 4.5, grok-4.3), real tool calls, GPQA Diamond, 3 runs per question (`docs/plan/TRACK_B_test_widely.md`). |
| **2. Keyword counts are rough** | The hint keyword fires on 22 of 72 no-hint private traces of Olmo 3 7B Think ("the user asks…"). A keyword can't tell "the user says E, but it is D" from "the user says E, so E". | Two people label each reply in `LABEL_QUEUE.csv` (101 rows) by hand; report their agreement (Cohen's kappa). |
| **3. Long replies are cut off and can leak private reasoning** | Olmo 3 7B Think hit the 16,000-token limit in 13 of 60 no-hint MMLU-Pro runs. With identical requests cut off at 2,000 tokens, private reasoning landed in the visible answer in 8 of 8 non-streamed replies and 0 of 8 streamed ones. | Always stream; count a cut-off reply as unanswered, never parse a letter from it; raise the limit where the budget allows. |
| **4. Fine-tuning could teach the model to hide the hint** | If training rewards text that looks honest, the model can change its words instead of its behavior. OpenAI reported this in 2025 with reasoning monitors. | Train and judge on behavior (does the answer still follow the hint?). Evaluate on held-out questions with hint wordings unseen in training. Track a hiding check: follows the hint without mentioning it (`docs/plan/TRACK_A_explain_fix.md`). |
