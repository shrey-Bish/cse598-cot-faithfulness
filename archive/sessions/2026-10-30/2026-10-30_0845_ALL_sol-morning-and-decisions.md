# Session log: Sol's night, the QoS, command 4, the push and Ritik's decisions (2026-10-30 08:45 MST)

Project: CSE 598 Group 10. Ritik ran commands 0 and 1 of the Oct 30 daily on Sol and the Mac and sent the output.
This log records what it shows, the decisions he made on the daily, and what was done about them. The readings of
what came back each have their own log (09:00–09:20). **By:** Ritik. **Branch:** `trackA-nosol`.

## 1. Sol's night (sacct, Oct 29 18:00 on)

| job | what | state | elapsed |
|---|---|---|---|
| 66932945, 66932946 | eval prompt_only 1/2, 2/2 (vLLM) | completed, exit 0 | 2:53:57, 3:01:53 |
| 66932947, 66932948 | eval lora 1/2, 2/2 (vLLM) | completed, exit 0 | 2:59:02, 3:16:26 |
| 66953953 | set A Step 10 | completed, exit 0 | 1:49:46 |
| 66953968 | set A Step 9 | completed, exit 0 | 0:22:07 |
| 66953970 | B1 forced (set A) | completed, exit 0 | 0:17:41 |
| 66954063 | get_c13 (snapshots, no GPU) | completed, exit 0 | 0:19:53 |
| 66954217 | Track B Qwen3-8B (vLLM) | completed, exit 0 | 2:00:45 |
| 66954219 | the duplicate Qwen3-8B | cancelled on purpose (Oct 29) | — |
| 66954278 | C13 (Granite, Mistral) | completed, exit 0 | 0:47:33 |

- **Nothing failed. The queue is empty.**
- **What came back is complete:**
  - every eval part has 465 of 465 runs;
  - Step 10 has 66 cuts, Step 9 201 runs;
  - Qwen3-8B has 1,620 runs and flags;
  - C13 has 159 cases × 3 variants per model.
- **C13 had its inputs.** Ritik's two input rsyncs this morning sent nothing new (the files were already on Sol);
  last night's open question is closed.

## 2. The QoS

`sacctmgr -P show qos class`: MaxJobsPU 2, MaxSubmitPU 10, MaxTRESRunMinsPU gres/gpu=960, MaxTRESPU empty.
- This is what the GPU README, PLAN and `accounts.conf` have said since Oct 27: 2 running jobs per user, 10 running
  and pending, 960 GPU-minutes of running jobs. No correction needed. The README now says it was re-checked
  Oct 30, and its stale "(TODO A12, not written yet)" is gone: A12 has been done since Oct 27.
- **Last night's "3 at once":** most likely an overlap at a job's edge. prompt_only 1/2 ended at about 21:56 (19:02
  + 2:53:57), about when get_c13 started; "~21:50" was an estimate. To check:
  `sacct -X -j 66932945,66954063 --format=JobID,Start,End`.

## 3. Command 4, adjusted

The queue is empty, so all 10 submissions go in now, in Ritik's order. Slurm runs 2 at a time; submit.sh refuses
only an 11th job and warns past 960 GPU-minutes. B1's alpha is not 1 (deployable 0.25, oracle 0.5; 09:05 log), so
provenance_gen runs as planned:

```bash
S=cot-disclosure/finetune/gpu/sol/submit.sh
F=/scratch/ragarw68/trackA/provenance_forced/provenance_forced.json   # alpha: deployable 0.25, oracle 0.5
$S provenance_gen --estimate 4.5 -- --alpha-from $F --part 1/4      # starts now
$S provenance_gen --estimate 4.5 -- --alpha-from $F --part 2/4      # starts now
$S eval --estimate 4.2 -- tags 1/2 --engine vllm
$S eval --estimate 4.2 -- tags 2/2 --engine vllm
$S provenance_gen --estimate 4.5 -- --alpha-from $F --part 3/4
$S provenance_gen --estimate 4.5 -- --alpha-from $F --part 4/4
$S eval --estimate 4.2 -- lora_tags 1/2 --engine vllm
$S eval --estimate 4.2 -- lora_tags 2/2 --engine vllm
$S eval --estimate 4.2 -- lora_attn3 1/2 --engine vllm
$S eval --estimate 4.2 -- lora_attn3 2/2 --engine vllm
```

## 4. Ritik's decisions on the Oct 30 daily, and what was done

1. **Push the six commits:** done after the usual checks: authors Ritik, no attribution lines, no produced data,
   525 tests at `8380e56`, a fast-forward. The pre-push check passed: `427f39e..f369bf6`.
2. **B1's alpha:** applied (above).
3. **Second rater:** Ritik is asking Shrey and Arsha today (TODO L3, L5).
4. **C16 approved:** pre-registered (08:50 log, commit `6b2ad02`) and running on Voyager since 08:50.
5. **B15's write-up:** FINDINGS F25, CLAIMS and the 04:00 log now say plainly that the "before" runs are Track B's
   from one to two days earlier, not an interleaved control.
6. **The story's B15 headline:** "Disclosure can be prompted, but it doesn't reduce deference to the tool." It is
   in FINDINGS' story so far, step 2.

## 5. Also

- **Set A's distances.** Step 10's split by distance read Test 2's cases whatever `--cases-from` said, so set A's
  handoff stopped. It now takes `--runs-from`, `--cases-from` and `--items-from`. The display also says "no deletion
  runs" for cases without Step 4 (set A), where it used to fail. Both are tested.
- **The daily's command 2 for set A** needs those three options (the 09:00 log has the line).
