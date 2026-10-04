# Failures found in the systems, and risks (one slide)

| Failure or risk | Evidence and plan |
|---|---|
| **The smallest instruct model follows wrong hints** | Olmo 3 7B Instruct: 5/48 wrong-hint runs (10.4%, range 2.1 to 18.8 points) vs 0/144 without a hint. → Cue uncertain items, where steering should be larger (Experiment B, then GPQA / MMLU-Pro screen). |
| **Final answers drop what private reasoning says** | Thinking models: hint mentioned in 208/216 private traces vs 8/216 final answers (keyword pre-sort). → Human labels separate mention / rejection / acknowledgment. |
| **Instruct models can't answer without room to reason** | "Answer only": 21/24 → 1/24 and 24/24 → 2/24. Thinking models keep reasoning privately (21/24, 23/24 replies). → Report "no-CoT" conditions per track. |
| **Private reasoning leaks at the token cap when the reply isn't streamed** | Same 8 requests at a 2,000-token cap: streamed 0/8 leaked, non-streamed 8/8 leaked (whole trace in the visible field). The parser read a wrong letter from 1 leak. Earlier ladder run: 10/10. → Always stream; treat `finish_reason = length` as "no answer". |
| **A reviewer can pass a steered answer along (demo)** | Reviewer kept the hinted wrong answer 0/15 (answer only), 7/15 (+ explanation), 3/3 (+ private reasoning, 1 case), 6/15 (+ "the user suggested"); with answer only it broke 3/18 right twin answers. n = 5 + 6 cases. → Arms a–e with twins at scale, more than one reviewer. |
| **A tool result steers thinking models, and the final answer often hides it** | Experiment B (simulated tool block): Olmo 3 7B Think followed it 10/20 (user sentence 2/20), Qwen3 30B Thinking 7/11 (user 0/11), even on items they got right 2/2 without a cue. Steered runs: private reasoning referred to the tool 9/10 and 7/7, final answer 2/10 and 4/7. → Real tool-role turn, system channel, human labels. |
| **Keyword counts over-fire** | The `cue` keywords fire on 22/72, 18/72, 2/72 no-hint private traces ("the user …"). → Treat as pre-sort only; two raters, Cohen's kappa. |
| **Replays are not always deterministic** | Seeded replay matched the pilot on 4/6 models in the timing run (not Olmo 32B), and on 7/14 pilot runs in Experiment A. Pilot texts were not saved. → Save every prompt and reply (done today). |
| **Twins differ in training, not only thinking** | Separately post-trained checkpoints (`MODELS.md`). → Report checkpoint differences; use "think briefly" for a same-weights dose. |
| **Olmo 32B identity unconfirmed** | No upstream name in the catalog; 32B replays differ from the pilot. → Ask Research Computing which checkpoint is served. |
| **Budget** | Thinking replies average 4,252 to 8,535 output tokens; some MMLU-Pro replies hit 16,000. → Timing run before each sweep (done today, `F6`). |
| **GPQA Diamond is gated; tool-turn format untested** | Request access; test a real tool-role message on Voyager before the cue-channel sweep. |
| Operational today | 427 new calls, 0 API errors, 0 retries, 0 parse failures. 59 replies hit the cap: 24 were set on purpose in the sweep, 35 were at 16,000 tokens on MMLU-Pro, mostly Olmo 3 7B Think. One job starved another for 4 min until the shared 4-slot limiter was made fair. |
