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
| 2026-11-06 14:50 | [2026-11-06_1450_C_c20-results.md](2026-11-06/2026-11-06_1450_C_c20-results.md) | C20 run and read: 200 reviews, 0 errors; Olmo tag − blind +8 [−2, +19] "no change" (the tag doesn't work), no false-alarm cost, doesn't match the checker, +34 [+21, +47] over the solver's disclosure; Qwen3 no change; FC3, the summary |
| 2026-11-06 15:45 | [2026-11-06_1545_C_c26-results.md](2026-11-06/2026-11-06_1545_C_c26-results.md) | C26 run and read: 600 calls, 0 errors; the solver follows the passage 19 of 55 vs 52 of 55 but +35 above the floor; Olmo defers to the tool log −48 [−67, −29] (21 items): deference survives without the authority label; FC4, the summary, slide 12's second figure `pipeline_vs_model.png` (C20 + C26) |
| 2026-11-07 09:15 | [2026-11-07_0915_C_c24-tables-merge.md](2026-11-07/2026-11-07_0915_C_c24-tables-merge.md) | main merged back after Ritik's merge (fast-forward, hooks reinstalled); C24's three tables from the summaries (`agents/trackc_tables.py`, 4 tests) |
