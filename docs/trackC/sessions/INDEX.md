# Track C session logs (Shrey's, from Nov 3)

One log per working session, `docs/trackC/sessions/<YYYY-MM-DD>/<YYYY-MM-DD>_<HHMM>_C_<slug>.md`: what was asked, what
was done, the results, the judgment calls (each with its cost if wrong), and what's next. A pre-registration is its own
log (`…_C_<experiment>-prereg.md`), committed before the first call. The project's logs up to Nov 3 are in
[`archive/sessions/`](../../../archive/sessions/INDEX.md).

| when | log | what |
|---|---|---|
| 2026-11-06 09:42 | [2026-11-06_0942_C_setup.md](2026-11-06/2026-11-06_0942_C_setup.md) | Setup, no calls: tests, hooks, bundle verified, F18, F24 and F34 reproduced, C19's dry runs |
| 2026-11-06 10:31 | [2026-11-06_1031_C_c19-results.md](2026-11-06/2026-11-06_1031_C_c19-results.md) | C19 run and read: 400 reviews, 0 errors; Olmo 24 vs 31 of 53, −13 [−25, −2], "unclear" by the rule (H34 unclear); Qwen3 no change; FC1, the summary, slide 11's bars |
| 2026-11-06 14:25 | [2026-11-06_1425_C_c25-results.md](2026-11-06/2026-11-06_1425_C_c25-results.md) | C25 run, spot check and read: 800 calls, 0 errors; the writer restores the source (plain 35 of 55, keep 55 of 55); Olmo decider stripped − keep 9 vs 16 of 53, −13 [−23, −6], "unclear" by the rule; Qwen3 no change; keyword 15 of 20 against the hand labels; FC2, the summary, slide 12's figure |
