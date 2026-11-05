# Session log: a correction: the second rater was an AI model, not Shrey (2026-11-04 17:42 MST)

**By:** Ritik. A correction, recorded as Ritik stated it on Nov 4 at 17:42. Nothing earlier is rewritten or deleted:
every log keeps what it said, and this log says what was wrong.

## 1. The facts, exactly as Ritik stated them (Nov 4, 2026)

- The second rater's sheets filed as Shrey's (`L3_SB.csv`, `L4_part1_SB.csv`, and both "_final" versions) were
  produced by an AI model, not by Shrey: **ChatGPT 5 Astra High**, used by Ritik with the rater packet's guide and
  blind sheets. **Shrey did no labeling.**
- Ritik's sheets (`L3_RA`, `L4_part1_RA`) are human labels.

## 2. The deviation

- **What was pre-registered:** two human raters (PLAN's L3 and L4; the labeling guide; RATER_GUIDE), with Cohen's
  kappa as the inter-rater reliability.
- **What happened:** one human rater (Ritik) and one AI model (ChatGPT 5 Astra High) as rater 2.
- **What that changes:**
  - Every kappa reported so far is **human-vs-AI agreement, not inter-human reliability**:
    - L3, read Nov 3: private 0.627 (tool 0.288, user 0.850); final 0.543 (tool 0.589, user 0.425);
    - L4 part 1, read Nov 3: 0.930 (tool_injected 0.958, tool_pasted 0.891, user 0.908).
  - **L4 part 1's conclusion stays as read,** now described as human + AI agreement (0.930) rather than two raters'.
  - **L3's numbers stay as read,** relabelled the same way. Gate 2's label part was "not passed" on them and remains
    so until the protocol below reads it.
- **What follows:** an LLM-judge protocol, pre-registered in its own log before any judge runs. Ritik's labels stay
  the final labels; several AI judges become the reliability check, reported openly.

## 3. What is corrected, and where

**"Rater 2" becomes "AI rater 1 (ChatGPT 5 Astra High)"** wherever the labels are described:
- FINDINGS: F3's L3 kappa, and F28's L4 reading and its 0.93;
- CLAIMS, REPORT's methods, PLAN, TODO, RATER_GUIDE, LABELING_GUIDE, ONE_PAGE, CHECKIN;
- the supplement (its deviations list gets this entry).

**Every labeling task, and the settling call, comes off Shrey:** TODO_C, Track C's START_HERE, CHECKIN, PLAN, and the
drafted messages. His Track C plan stays as it is.

**The old logs that said "Shrey" for the labels stay as written.** INDEX gets a correction note pointing to them and to
this log.

**The files:**
- the `_SB` files stay untouched;
- copies go in `results/labels/returned/ai_rater1_chatgpt5_astra_high/`, under the AI rater's name, with a
  provenance note.

## 4. Corrections to this session's own earlier records

- **The 16:07 log** called the "_final" sheets "his [Shrey's] own revisions". They were produced by the same AI model.
  Its drafted message to Shrey carried a labels paragraph that no longer applies, and its "needs Ritik" list asked
  Ritik to ask Shrey how the sheets were made; that question no longer applies.
- The 16:07 log keeps its text, with a dated correction note at its end.
- **The message to Shrey** to send is the Track C handoff without the labels paragraph (section 5).

## 5. The message to Shrey (the Track C handoff, with no labels)

> Hi Shrey, here's the final Track C handoff. Your branch is `trackC-main`, and from now on it's yours alone: I won't
> push to it again (it's level with `main` today, so you start current).
> - **Start** with the Quick start at the top of `docs/trackC/START_HERE.md`.
> - **The data:** the bundle `trackC_20261103.tar.gz` is in our ASU folder (re-verified today). Unpack it into
>   `cot-disclosure/` and run `--verify` (§4).
> - **The hooks,** once: `python3 cot-disclosure/tools/path_check.py --install`, plus the pre-push line in §4.
> - **First:** setup, the tests and the three no-call reproductions. Then C19 by Sat Nov 7.
> - **Check-ins:** Nov 7, 12, 15 and 18, when I merge `trackC-main` into `main`. After each, please merge
>   `origin/main` back into your branch.
