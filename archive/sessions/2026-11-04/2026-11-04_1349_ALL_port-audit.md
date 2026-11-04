# Session log: the shared-port audit, the Sol access rule, the queue (2026-11-04 13:49 MST)

**By:** Ritik. Ritik pulled `f8b61af` on Sol at about 13:47 and asked for an audit of every earlier vLLM job. On Sol
only read-only commands ran: `sacct`, `squeue`, `sprio`, `git log`, and reading logs and records. Nothing was
submitted, cancelled, moved or pulled from here. No paid calls; nothing of E2 read.

## 0. What Ritik asked

1. **A Sol access rule,** kept in local memory and never committed:
   - allowed: read-only commands, and `git pull --ff-only` once the safety diff prints nothing;
   - ask first: before submitting, cancelling, moving, renaming or deleting anything on Sol;
   - the 340 runs already moved: fine, with the one-line undo kept in §15.
2. **Confirm the fix is in place** for the next jobs that start.
3. **The audit.** Ports 8011, 8012 and 8013 were shared before Nov 4. Check every earlier vLLM job and report per
   finding (F28, F29, F30, F37, F38's inputs) whether it is clean or affected. Set aside nothing without asking. If all
   are clean, add a trap with the evidence.
4. **The queue:** keep the projected dates current. If GPU time stays this scarce, propose what to cut first to
   protect A39 on E2 and B20, without changing any pre-registered rule. Ritik decides.
5. **Arsha's bundle** is built from Ritik's first message on Nov 6.
6. **The standing rules.**

## 1. The access rule

Saved in local memory (`work-on-sol-by-ssh`), not in the repo, in the words above. The SSH master connection
stays as it was; `ssh -O exit login.sol.rc.asu.edu` cuts it.

One lapse to record: between 13:49 and 13:53, a read-only count wrote and removed a temporary file under Sol's
`/tmp`. From now on
such counts go through pipes.

## 2. The fix is in place

Checked between 13:49 and 13:53:
- Sol's clone is at `f8b61af`, and `36c639b` (the port and the saving), `54291fd` (the leftover lines) and `1f01ead`
  (the status) are all in it.
- `generate.free_port`, `eval_job.Server`'s use of it, `eval.run`'s `as_completed`, and `sol_b20.py`'s port are in
  the files.
- Ritik's `--status` counts 220 lines (192 + 28). Nothing is running.
- The 9 queued jobs (7 A39, 2 B20) load these files when they start, so every next job serves on its own port.
  - They keep the batch scripts they were submitted with: 1:30 limits, and the old `a39_1gpu.sbatch` without the
    exit-0 wrapper.
  - The feeder already treats an exit 138 with no runs left as done.

## 3. The audit: no earlier result is affected

**Method:**
- `sacct` for every job from Oct 20. 69 vLLM jobs are by name, of which 59 ran: 8011 for `trackA-eval`, `vllm_check`
  and `a39*`; 8012 for `trackB-qwen3-8b`, `b17` and `b20`; 8013 for `trackC-c13`.
- Every pair on the same port and the same node, overlapping in time.
- Every vLLM log on Sol, split at its start lines (each names its job), counting the requests that server received
  (`POST /v1/`) and any failed bind.

**Same port, same node, same time:** only the six A39 pairs of Nov 3–4, already handled (the A39 log's §15). Nothing
earlier.

**Each result's own servers:**

| finding | jobs | nodes | what each job's own server logged | verdict |
|---|---|---|---|---|
| **F28, Gate 3** | 12 parts: base, prompt_only, lora, tags, lora_tags and lora_attn3, 1/2 and 2/2 (66932942–66989539, Oct 29–31) | one node each, no other job of ours on it at the time | 465 of 465 runs a part, no reply missing, 476–500 tokens a second; lora's, tags', lora_tags' and lora_attn3's parts logged 490–536 requests each; base's two and prompt_only's two shared a log name (no part in it then), 1,020 and 994 requests for 930 runs | **clean** |
| **F29, Qwen3-8B (B4)** | 66954217 (Oct 29–30) | sg038, beside Gate 3's lora 1/2 on 8011 | 1,799 requests, on 8012 | **clean** |
| **F30, C13** | 66954278 (Oct 30) | sg038, 4 minutes beside lora 1/2 | 477 requests to each of its two reviewers, on 8013 | **clean** |
| **F37, B17** | 355632, 355650 (Nov 3) | sg023, sg236, alone | 31 and 2,679 requests | **clean** |
| **F38, B1** and **F39, A18** | Hugging Face jobs, no server | | their vLLM inputs are Gate 3's runs, above | **clean** |
| B20's smokes (§15–§16 rest on them) | 456999, 457471, 460109, 466399 | each beside A39 jobs, but on 8012 | 33, 31, 32 and 26 requests | **clean** |
| A39's bench, and every A39 part outside the six pairs | 389340 and the rest | | each logged its own requests (bench 98) | **clean** |
| the vLLM check | 66928369 | sg014 | 3 and 3 | clean (a check, no finding) |

- **Two more signals:**
  - A server answering two jobs halved each job's rate (A39's 460114: 217 tokens a second, against 476–500 for
    Gate 3's parts).
  - Another user's server on our port would have failed our requests, since none serves our model names. Gate 3's
    parts missed no reply.
- **Two jobs had no log segment, and neither matters.**
  - 66932942 (base 1/2) shared `vllm_base.log` with base 2/2. They were on two nodes, and base 2/2's start line
    replaced base 1/2's in the shared file.
  - 66920318 ran the Hugging Face engine and was cancelled.
- **Jobs that failed before any run** have empty segments: 66932943 (Qwen3-8B), and 66920320's tagged server (its
  known out-of-memory failure).
- **So nothing is "under audit".** FINDINGS gets trap **T12** (the shared port) with this evidence.

## 4. The queue

- **Nothing has run since 12:36:14.** By 13:53 Sol gave our 9 jobs no start estimate (`squeue --start`: N/A).
- **Why, from `sprio` and `squeue`:**
  - 226 GPU jobs are pending on the public partition, 212 of them above ours.
  - 219 of the 226 are in the `public` QoS, whose priority factor (weight 200 M) takes them up to about 98 M. Our
    `class` QoS has a factor of 0, so our priority (about 0.76 M) is waiting time plus fair share (0.005).
  - So our jobs start only in backfill gaps, or when the public GPU queue runs dry. The last 24 hours' 38.8
    GPU-hours came in a quieter spell.
- **The projected dates** (daily, §6), with about 184 GPU-hours left (A39 61, B20 at most 57, B1R2 66), counted from
  whenever jobs start again:
  - at the last 24 hours' pace: E2 and B20 about 2.6 days after the restart, the 30 3.0, B1R2 4.7;
  - at half that pace: 5.2, 6.1 and 9.5 days.
- **The two deadlines,** from a restart at Nov 5 00:00:
  - the 30's rule (E2 and B20 by Nov 11 09:00) needs about 16 GPU-hours a day, 41% of the last 24 hours' pace;
  - B1R2 by Nov 15 23:59 (the A39 log's §13.8) needs about 17 a day, 43%.
  - At 12:52 I put the second at 47%, counting to the start of Nov 15. Corrected in both logs.
- **At 13:56 Sol's estimates came back:** Nov 5 06:25 for Gemma's second smoke, 08:45 for the first A39 part.
  - If they hold, nothing runs from 12:36 to 06:25, about 18 hours, past the 12 Ritik named.
  - From a 06:25 restart, at the last 24 hours' pace: E2 and B20 about Nov 7 21:00, the 30 about Nov 8 06:00, B1R2
    about Nov 9 23:00. At half that pace: about Nov 10 11:00, Nov 11 09:00 and Nov 14 18:00.
  - The 30's rule then needs 43% of the pace, and B1R2 44%.

**What to cut first, if GPU time stays this scarce (a proposal; no rule changed; Ritik decides):**
- **Nothing yet.** The order and two rules already protect E2 and B20:
  - E2's and B20's lines come first in the feeder;
  - the 30 drops itself if E2 and B20 aren't done by Nov 11 09:00;
  - B1R2 runs last and is read partial at Nov 15 23:59.
- **Where they still compete.** B20 runs as three chains, one job a model at a time, so the 30's and B1R2's parts can
  take the places in between. A B20 line that becomes ready then waits for a place (up to 2:00–2:30).
- **If nothing has started by the Nov 6 digest, in this order:**
  1. **Drop the 30 early.** An amendment to §10.2; it frees about 17–21 GPU-hours (22 jobs) and costs the 30's
     readings beside A39. Its rule may drop it on Nov 11 anyway.
  2. **Hold B1R2's parts until E2's sweeps and B20's last lines are submitted.** An operational order change, in line
     with §13.6's "B1R2 is last". It costs places left idle while B20's chains run one job at a time.
  3. **Cut B1R2 to fewer parts** (say 20 of 40). An amendment to §13. It helps E2 and B20 least, since B1R2 already
     runs last and its partial rule cuts it at the deadline.

## 5. Arsha

Her bundle is built from Ritik's first message on Nov 6, as Nov 5's daily says. Nothing is built now. The Track B
bundle's dry run (§7) holds 51 files, with Nemotron's numbers-only files.

## 6. Docs

- FINDINGS: T12, with the audit's evidence; the header's time.
- The 12:52 log and DAILY_2026-11-04 §5: B1R2's margin, 43% (to Nov 15 23:59), not 47%.
- DAILY_2026-11-04 §6; DAILY_2026-11-05's carry-over (the pull is done; the queue's cause; the cut proposal); INDEX;
  LATEST; TODO's A39 row; STATUS and the Gantt; the supplement (T12 reaches its traps list).

## 7. Checks and push

On the final tree:
- **The full suite** on `81eaa74`: 912 passed, 1 skipped (CPU, no network). No code has changed since `1f01ead`.
- **Links:** 0 broken.
- **`export_summaries --check`:** numbers only.
- **The supplement** (regenerated, `81eaa74`; `--check` passes): TRAPS has T12. 36 rows, none unverified, no log
  outside the ledger. CLAIMS unchanged: 198 numbers, the same 3 mismatches, 13 weak, 12 source problems.
- **The Gantt's dry run:** passes.
- **The bundles:** Track B 51 files, 73.8 MB (3 Sol records left out); Track C 43 files, 31.3 MB.
- **The pre-push check:** nothing produced, GPQA or over 50 MB.
- **Nothing missing:** all 747 files tracked at `origin/main` (`f8b61af`) are still here.
- **The pull on Sol:** none from here. Ritik's pull brought everything (`f8b61af`), and this prompt changes no file a
  job loads.

## 8. Judgment calls, with their cost if wrong

1. **The audit counts each server's requests from its own log** rather than reading any run's text or outcome.
   - Cost if wrong: none for the verdict where nodes differ; the two shared log names are covered by the node and
     reply checks.
2. **F38 and F39 are clean by construction:** Hugging Face only, with Gate 3's runs as their vLLM inputs.
   - Cost if wrong: a re-check of their input lists.
3. **No cut is proposed for now.** The rules already put E2 and B20 first.
   - Cost if wrong: about a day, if the queue stays empty past Nov 6 and the 30's parts take places B20's chain needs.
4. **The projections are counted from the restart,** since Sol gives no start estimate.
