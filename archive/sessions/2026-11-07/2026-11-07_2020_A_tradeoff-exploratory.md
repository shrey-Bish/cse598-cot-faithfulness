# Session log: the trade-off between resisting wrong hints and taking right ones, explored on E2 (**post hoc**; 2026-11-07 20:20 MST)

**By:** Ritik (decision b of the [20:19 session](2026-11-07_2019_ALL_a39-tradeoff-label-check.md)).
**Exploratory, not pre-registered.** It is written and committed before any of it is computed, and says exactly what
is computed. It is chosen after A40, A41 and A42 were read (Nov 7, 13:29–13:31) and in the same session as A39's
reading. It never replaces or qualifies a pre-registered verdict, and every place it appears says "exploratory (post
hoc)".

## 1. Why

A40 follows far fewer wrong hints than the one-line instruction but also takes fewer correct ones (F41: "fewer, but
costs acceptance"). Whether that trade is worth it depends on how often a tool's answer is right, which no rule of ours
fixes. This analysis puts every E2 system on the two axes at once, asks at what share of correct tool answers each
system gives more correct answers than the instruction, and asks how often each system says so when it follows a wrong
hint.

## 2. The data

- E2 only (120 questions), the A39 design's runs: the run files copied back on Nov 7 (`results/trackA/gpu/a39/
  eval_*_a39_e2*_runs.jsonl`, numbers only). The 30 aren't used.
- **Nine systems:** base, prompt_only, lora, lora_note, wrap, wrap_note, lora_wrap (A39), a40 (A40) and a40_note (A42).
- **Each run once,** its last ok record, and each wrapper system with its partner's shared runs (`a39.by_system`, as
  the readers load them).
- **Answered runs only** (a parsed letter), as `eval.report`'s measures, unless said otherwise (§3.2's sensitivity).
- Channels: user (`user_turpin`, `user_professor`), pasted (`tool_progress`) and inserted (`inserted_study_guide`,
  `inserted_database`). The lean design gives correct hints on the pasted and inserted channels only.

## 3. What is computed (nothing else)

### 3.1 The trade-off figure (`docs/paper/figures/tradeoff_e2`: .png, .svg, .csv)

- **Each system is a point:** x = correct-hint acceptance (the correct letter among answered correct-hint runs), y =
  following (the hint's letter among answered wrong-hint runs). Each is X of Y with a 95% Wilson interval, drawn as a
  bar on its axis.
- **Panel (a), pooled:** wrong hints over all three channels, correct hints over pasted and inserted. The wrapper
  systems are hollow and marked "diluted by design" (most of their pooled runs are their partner's; the A39 log's
  §9.2).
- **Panel (b), the inserted tool turn only,** where the wrapper acts.
- The headline says "exploratory (post hoc)". No reading is printed on it.

### 3.2 Expected accuracy under hints, Acc(p), and where systems cross

- **Where:** the two tool channels only (pasted and inserted). There each system gets the same four wordings with a
  wrong hint and with a correct one, so p means "the share of tool answers that are correct".
- **Per system:** a_C, the correct answers among answered correct-hint tool runs; a_W, the correct answers (the right
  letter, not merely not the hint's) among answered wrong-hint tool runs.
- **Acc(p) = p · a_C + (1 − p) · a_W,** for p from 0 to 1.
- **The crossing of system A with system B:** with dW = a_W(A) − a_W(B) and dC = a_C(A) − a_C(B), p* = dW / (dW − dC).
  - It lies in (0, 1) when dW and dC have opposite signs. If dW > 0, A gives more correct answers than B when fewer
    than p* of the tool's answers are correct, and fewer above it.
  - With the same sign there is no crossing: A is ahead (or behind) at every p, reported so.
- **The pairs:** every system against prompt_only, **A40 first, then LoRA**, then the others.
- **Intervals:** questions resampled with replacement, the same questions for both systems (paired), 20,000 resamples,
  seed 0, the rates recomputed as ratios of sums over the resampled questions' runs.
  - p* in each resample by the same formula, clipped to [0, 1] (0 or 1 when one system is ahead throughout). The
    interval is the 2.5th and 97.5th percentiles.
  - A resample where dW − dC has the other sign from the full data's (the systems' order flips) is counted, reported
    and left out of the interval.
  - Beside it, Acc_A(p) − Acc_B(p) at p = 0, 0.25, 0.5, 0.75, 0.9 and 1, each with the same bootstrap's interval.
- **Sensitivity, beside it:** the crossings with a run that gave no answer counted as a wrong answer.
- **A second figure,** `docs/paper/figures/tradeoff_acc_p` (.png, .svg, .csv): Acc(p) for base, prompt_only, lora and
  a40, with the two crossings (A40 and LoRA against prompt_only) marked with their intervals.

### 3.3 Disclosure when following (keyword)

- **Per system:** among answered wrong-hint runs that end on the hint's letter, the share whose final answer names the
  hint by the broad keyword (`mention_final_broad`, the keyword `hiding` uses). So it is 1 − hiding ÷ following.
- Pooled and per channel, X of Y with 95% Wilson intervals, all nine systems.
- **Against prompt_only** (LoRA and A40 first): the difference in shares, by the same clustered bootstrap (a ratio of
  sums per resample; a resample in which either side has no followed run is counted and left out).
- **Its limit, said now:** a keyword. LoRA's trained opener names the hint (F28), so this may count a formula as a
  disclosure. The hand-label check pre-registered today (L6) tests exactly that.

## 4. Code and outputs

- `tools/tradeoff.py` (tracked), with CPU tests on synthetic runs (`tests/test_tradeoff.py`), written before it is
  run on E2.
- **Numbers only:** `results/trackA/gpu/a39/tradeoff_e2.json`, exported to `results/summaries/trackA/gpu/a39/`. Every
  output carries "exploratory (post hoc)".
- REPORT gets one bullet labelled "exploratory (post hoc)" and `tradeoff_e2`; the numbers go in §5 below.

## 5. Results

(Written after the computation, below this line. Nothing above it changes.)
