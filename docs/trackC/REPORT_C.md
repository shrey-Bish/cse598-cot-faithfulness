# Track C's section of the report, as bullets (Shrey; for Ritik to merge into `docs/paper/REPORT.md` §8 and §9)

Status: **ready for Ritik, Nov 6.** The numbers, status, limits and figure lines are taken from FC1–FC4
(`FINDINGS_C.md`) and the numbers-only summaries (`cot-disclosure/results/summaries/trackC/c19…c26_summary.json`),
each checked against its summary on Nov 6. The claim sentences (the bold lines) are Shrey's, from the FC headings.

The four results below join §8 (C19, after F34) and §9 (C25, C20, C26, replacing the three "waiting" entries). All
rates are X of Y with 95% Wilson intervals; differences are paired by item, 95% bootstrap clustered by item; "the
rule" is C11's 20-point two-sided rule unless another is named.

## §8 addition, after F34

- **FC1. C19: when the solver says its answer came from the answer key instead of from its own working, the Olmo
  reviewer corrects fewer wrong answers (24 against 31 of 53), but the pre-registered rule cannot call the drop.**
  - Numbers: C15's 100 saved solver answers with one sentence appended ("The course answer key gives (X); I follow
    it." against "My own careful working gives (X); I follow it."), both reviewers with `plus_explanation`, 400
    reviews. Corrects a wrong answer, 53 items, answer key − own working: Olmo 3.1 32B 24 of 53 against 31 of 53,
    −13 [−25, −2]; Qwen3 30B Instruct 47 against 48 of 53, −2 [−9, +6]. Cross-day references, no decision: answer key −
    unchanged (C16's control) Olmo −23 [−38, −8], Qwen3 +6 [−2, +13]; answer key − C17's names_tool Olmo −25 [−38,
    −11]. Bare answers only (49 items): Olmo −10 [−22, +2]. Keeping a right answer on good lookups (45): Olmo 44 vs 43,
    +2 [0, +7].
  - Status: by the rule, "unclear" for Olmo (the interval excludes 0 but crosses the 20-point margin), so H34 ("an
    authority claim is the cue") is neither supported nor not supported; tentative: the direction (fewer corrections
    with the answer-key claim). Qwen3: no change, as expected for the reviewer that doesn't defer.
  - Limits: one wording per sentence, appended rather than the solver's own text; the answer-key claim also states the
    letter; one solver, 1 repeat, 53 items; the references are other days' reviews.
  - figure: docs/trackC/figures/c19_authority.png (slide 11's bars; Ritik places it; WAITING.md "Additions")

## §9, replacing the three "waiting" entries

- **FC2. C25: a second agent that writes the handoff note puts the tool back as the source (35 of 55 plain notes, 55
  of 55 when told to say where the answer came from); when that source is stripped out again, the Olmo decider
  accepts the wrong answer less, not more (9 against 16 of 53), and the rule reads the drop as unclear.**
  - Numbers: three hops on C15's 100 items (55 bad lookups). Hop 1, the solver's final answer names the tool in 5 of
    55 [4, 20%]. Hop 2, a Qwen3 30B Instruct writer's note of at most five sentences: plain 35 of 55 [50, 75%] (kept:
    the lower bound is above 50%), keep (told to say where the answer comes from) 55 of 55 [93, 100%] (kept); plain −
    hop 1 +55 [+42, +67], keep − plain +36 [+24, +49]. The note keeps the solver's letter in 92 (plain) and 94 (keep) of
    100. Hop 3, a decider that never sees the tool (C4's reviewer prompt, `plus_explanation`, the note in place of the
    final answer), accepts the solver's wrong letter, 53 items: Olmo plain 13, keep 16, keep with its tool sentences
    stripped 9 of 53; M1 (main) stripped − keep −13 [−23, −6]; M2 plain − keep −6 [−19, +8]. Qwen3: 1, 0 and 0 of
    53; M1 0 [0, 0], M2 +2 [0, +6]. No decision: every note version is accepted more than C15's bare answers by Olmo
    (plain +19 [+9, +30], keep +25 [+13, +36], stripped +11 [+4, +21]); within plain notes, named − not named
    (unpaired, 33 and 20 items) Olmo +23 [+2, +44]; keeping a right answer on good lookups (45) Olmo stripped − keep
    −13 [−24, −4]. The spot check: Shrey's hand labels on 20 blind rows against the keyword, 15 of 20 agree; every
    disagreement a keyword "names the tool" read by hand as another source (4) or unclear (1); 394 sentences removed
    by the strip over the 100 keep notes.
  - Status: confirmed (by the rule): the writer puts the source back at hop 2 in both note versions. The main
    question (does the decider accept the wrong answer more, or less, with the source gone) reads "unclear" for Olmo
    (the interval excludes 0 but crosses the margin); tentative: the direction (fewer acceptances once the source is
    stripped, C18's direction). Qwen3: no change.
  - Limits: one writer model and one wording per variant; the keyword decides which sentences are stripped and how
    "names the tool" is counted (15 of 20 against a hand label, the keyword likely overcounting); one solver, 1 repeat,
    53 items; the notes are written on a later day than the solve; the plain note's "kept" rests on a 50.4% lower bound.
  - figure: docs/trackC/figures/c25_hops.png (slide 12; WAITING.md's spec)
- **FC3. C20: a tag the pipeline attaches ("this letter came from the tool, unverified") does not change what the
  blind reviewer catches by the rule (+8 points), costs no false alarms, catches 19 points fewer than the checker,
  and catches 34 points more than when the solver says the same thing itself.**
  - Numbers: four pipelines on C15's 100 items, one check stage each; "caught" = the solver is wrong and the stage
    corrects or escalates (53 items), "false alarm" = the solver is right and the stage changes or escalates (47).
    Olmo 3.1 32B: blind 39 of 53, 8 of 47, 21 of 100 shipped wrong, 1,206 tokens a case; with the tag "[letter from
    tool lookup_answer_key; unverified]" (on 97 of 100 cases) 43 of 53, 9 of 47, 19 of 100, 1,342; the solver's own
    disclosure (C16) 26 of 55, 2 of 45, 31 of 100, 1,108; the checker 53 of 53, 7 of 47, 0 of 100, 3,545. Qwen3 30B
    Instruct: blind 43 of 53, 9 of 47; tag 46 of 53, 8 of 47; disclosure 46 of 55, 5 of 45. Readings, paired: (1) tag
    − blind on catches Olmo +8 [−2, +19], Qwen3 +6 [−2, +13]; (2) on false alarms Olmo +2 [−6, +11], Qwen3 −2 [−13,
    +9]; (3) tag − checker, catches Olmo −19 [−30, −9], Qwen3 −13 [−23, −6], false alarms +4 [−6, +15] and +2 [−11,
    +15]; (4) tag − disclosure on catches Olmo +34 [+21, +47], Qwen3 +4 [−6, +15]. As a flag (no decision): either
    reviewer escalating on any disagreement catches 49–52 of 53 at 8–9 false alarms of 47.
  - Status: not supported: "the tag works" (reading 1, no change for both reviewers). Confirmed by the rule: the tag
    doesn't match the checker (3); it beats the solver's own disclosure for the deferring reviewer (4). One Qwen3 tag
    review gave no letter (the 8,000-token cap), counted as not correcting.
  - Limits: one tag wording; one solver, 1 repeat; the tag runs on a later day than the saved pipelines; the
    disclosure arm comes from a different solve (C16), so reading 4 pairs the items wrong in both.
  - figure: docs/trackC/figures/pipeline_vs_model.png (slide 12's second figure, with C26, if there is room)
- **FC4. C26: when the tool returns a plain retrieved passage instead of an "answer key" letter, the solver follows a
  bad lookup a third as often (19 against 52 of 55) but still far more than with no tool, and the Olmo reviewer still
  defers to the tool log (5 against 15 of 21), so the deference does not depend on the authority label.**
  - Numbers: C15's 100 items and team with `search_passages` in place of `lookup_answer_key`, returning the chosen
    option's text with no letter and no "answer key"; 100 solves, 100 checks, 400 reviews. The solver follows the bad
    lookup in 19 of 55 [23, 48%] against 52 of 55 [85, 98%] with the answer key: R1 −60 [−73, −45]; R1b, against the
    no-tool floor (0 of 55), +35 [+22, +47]. Good lookups right 45 of 45 in both. The final answer names its source in
    9 of 100 (C15 6 of 100) and is bare in 90 of 100 (C15 93). Reviewers, corrects a wrong answer after a bad lookup,
    21 items: Olmo answer only 15 of 21, with the tool log 5 of 21, −48 [−67, −29]; Qwen3 15 and 12 of 21, −14 [−29, 0].
    No decision: tool-log corrections C26 − C15 on the items wrong in both, Olmo +5 [−10, +19], Qwen3 0 [−14, +14]; the
    checker flags 27 of 100 and gives the same letter as C15's checker on 98 of 100.
  - Status: confirmed by the rule: R1 fewer following; R1b deference survives in the solver; R2 the Olmo reviewer
    defers (C11's rule), so deference survives in the reviewer without the authority label. Qwen3 doesn't defer.
  - Limits: one passage wording and one tool name; the passage quotes the option's own words (a paraphrase isn't
    tested); one solver, 1 repeat; C26 and C15 solve on different days; the reviewer reading rests on 21 items.
  - figure: docs/trackC/figures/pipeline_vs_model.png (with C20)

## Lines to keep from the current §9 (unchanged)

- The checker's record (F18, F24) and F24 (c): as in `REPORT.md` §9 today.
- Delete the three "waiting" entries and the two schedule lines once the four bullets above are in.
