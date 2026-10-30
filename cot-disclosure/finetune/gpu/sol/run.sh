#!/bin/bash
# Run one Track A GPU step inside a Slurm job on Sol: your interactive session, or a batch job
# (the .sbatch scripts call this). Refuses outside a job, or under an account not in accounts.conf.
#   cot-disclosure/finetune/gpu/sol/run.sh smoke|step8|step9|step10 [arguments for the Python script]
#   cot-disclosure/finetune/gpu/sol/run.sh timing                    # S1: 12 examples of every length, every version
#   cot-disclosure/finetune/gpu/sol/run.sh vllm_check                # S2: the vLLM tag check
#   cot-disclosure/finetune/gpu/sol/run.sh train VERSION [args]      # S3-S6: lora, tags, lora_tags, lora_attn3
#   cot-disclosure/finetune/gpu/sol/run.sh eval SYSTEM [K/N] [args]  # E1-E6: one system, the K-th of N parts
#   cot-disclosure/finetune/gpu/sol/run.sh val_loss [VERSION ...]    # validation loss by part: base + each version's epochs
#   cot-disclosure/finetune/gpu/sol/run.sh trackb_qwen8b [args]      # Track B: Qwen3-8B, Hugging Face or vLLM (progress/sol_trackB.py)
#   cot-disclosure/finetune/gpu/sol/run.sh get_qwen8b                # its snapshot (no GPU; the only step online)
#   cot-disclosure/finetune/gpu/sol/run.sh provenance_forced --cases-from C --runs-from R [--items-from I]   # B1 on set A
#   cot-disclosure/finetune/gpu/sol/run.sh provenance_gen [--alpha-from S | --version V --checkpoint D] [--part K/N]
#   cot-disclosure/finetune/gpu/sol/run.sh c13 [--model M]          # Track C: two more reviewer families (agents/sol_c13.py)
#   cot-disclosure/finetune/gpu/sol/run.sh get_c13                  # their snapshots (no GPU; online)
#   cot-disclosure/finetune/gpu/sol/run.sh qwen8b_step3 [args]      # Qwen3-8B Step 3 on Track B's runs (finetune/look/qwen8b_mech.py)
#   cot-disclosure/finetune/gpu/sol/run.sh qwen8b_step10 [args]     # Qwen3-8B Step 10 on its cases; Hugging Face only
# Output: $TRACKA_OUT/<step>/ (/scratch/ragarw68/trackA/<step>/), plus a log of the console there.
# Every step starts with the import check (finetune/gpu/import_check.py): a broken environment stops the
# job in seconds, before any model loads.
# Slurm's warning before the time limit (sbatch --signal=B:USR1@300) is passed on to Python: training
# saves a resume checkpoint at its next optimizer step; evaluation stops and resumes in the next job.
source "$(dirname "${BASH_SOURCE[0]}")/env.sh" || exit 1
set -euo pipefail
tracka_require_job

step=${1:?usage: run.sh smoke|step8|step9|step10|timing|vllm_check|train|eval|val_loss|trackb_qwen8b|get_qwen8b|provenance_forced|provenance_gen|c13|get_c13|qwen8b_step3|qwen8b_step10 [args]}
shift
args=("$@")
case "$step" in
    smoke)  script=finetune/gpu/smoke.py ;;
    step8)  script=finetune/gpu/checkpoint_check.py ;;
    step9)  script=finetune/look/attn_to_hint.py ;;
    step10) script=finetune/look/patching.py ;;
    timing) script=finetune/train.py
            args=(--version lora,tags,lora_tags,lora_attn3 --timing 12 --out "$TRACKA_OUT/timing" "$@") ;;
    vllm_check) script=finetune/gpu/eval_job.py
            args=(--check --out "$TRACKA_OUT/vllm_check" "$@") ;;
    train)  script=finetune/train.py
            version=${1:?usage: run.sh train lora|tags|lora_tags|lora_attn3|gate3|lora_attn3_gate}
            args=(--version "$version" --out "$TRACKA_OUT/train/$version" "${@:2}") ;;
    eval)   script=finetune/gpu/eval_job.py
            system=${1:?usage: run.sh eval SYSTEM [K/N]}
            args=(--system "$system" --out "$TRACKA_OUT/eval")
            if [ $# -ge 2 ] && [[ "$2" == */* ]]; then args+=(--part "$2" "${@:3}"); else args+=("${@:2}"); fi ;;
    val_loss) script=finetune/val_loss.py                         # Hugging Face only, no vLLM
            args=(--out "$TRACKA_OUT/val_loss" --train-dir "$TRACKA_OUT/train" "$@") ;;
    trackb_qwen8b) script=progress/sol_trackB.py
            args=(--run --log-dir "$TRACKA_OUT/trackb_qwen8b" "$@") ;;
    get_qwen8b) script=progress/sol_trackB.py                  # the only step with the network (decided Oct 28)
            export HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0
            args=(--download --log-dir "$TRACKA_OUT/trackb_qwen8b") ;;
    provenance_forced) script=finetune/gpu/provenance_job.py      # B1 on set A; Hugging Face only
            args=(forced --out "$TRACKA_OUT" "$@") ;;
    provenance_gen) script=finetune/gpu/provenance_job.py         # B1 / B2 generation; Hugging Face only
            args=(generate --out "$TRACKA_OUT" "$@") ;;
    c13)    script=agents/sol_c13.py                              # Track C: reviewers on our vLLM, one after the other
            args=(--run --log-dir "$TRACKA_OUT/c13" "$@") ;;
    get_c13) script=agents/sol_c13.py                             # their snapshots: online, like get_qwen8b
            export HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0
            args=(--download --log-dir "$TRACKA_OUT/c13") ;;
    qwen8b_step3) script=finetune/look/qwen8b_mech.py          # Thread 1 on Qwen3-8B (Oct 30); Hugging Face only
            args=(step3 --out "$TRACKA_OUT" "$@") ;;
    qwen8b_step10) script=finetune/look/qwen8b_mech.py
            args=(step10 --out "$TRACKA_OUT" "$@") ;;
    *) echo "unknown step: $step (smoke, step8, step9, step10, timing, vllm_check, train, eval, val_loss, trackb_qwen8b, get_qwen8b, provenance_forced, provenance_gen, c13, get_c13, qwen8b_step3, qwen8b_step10)" >&2; exit 2 ;;
esac
mkdir -p "$TRACKA_OUT/$step"
log="$TRACKA_OUT/$step/console_$(date +%Y%m%d_%H%M%S)_${SLURM_JOB_ID}.log"
cd "$TRACKA_CODE"
echo "job $SLURM_JOB_ID ($(tracka_account)) on $(hostname): $script ${args[*]}" | tee "$log"
# First (Oct 29): the job's imports, each from its own environment, with their versions, in seconds
# (finetune/gpu/import_check.py): torch, transformers with AutoTokenizer, peft; vllm in vLLM's
# environment for a vLLM job (vllm_check, c13; eval and trackb_qwen8b with --engine vllm)
check=(finetune/gpu/import_check.py)
uses_vllm=0
if [ "$step" = vllm_check ] || [ "$step" = c13 ]; then uses_vllm=1; fi
for i in "${!args[@]}"; do
    if [ "${args[$i]}" = "--engine=vllm" ]; then uses_vllm=1; fi
    if [ "${args[$i]}" = "--engine" ] && [ "${args[$((i + 1))]:-}" = vllm ]; then uses_vllm=1; fi
done
if [ "$uses_vllm" = 1 ]; then check+=(--vllm "$TRACKA_VLLM_PY"); fi
"$TRACKA_PY" "${check[@]}" 2>&1 | tee -a "$log" || { echo "the import check failed; nothing else ran" >&2; exit 1; }
"$TRACKA_PY" "$script" "${args[@]}" > >(tee -a "$log") 2>&1 &
pid=$!
trap 'kill -USR1 "$pid" 2>/dev/null' USR1 TERM
while true; do                                   # a trapped signal ends wait early: wait again for Python
    wait "$pid" && rc=0 || rc=$?
    if [ "$rc" -gt 128 ] && kill -0 "$pid" 2>/dev/null; then continue; fi
    break
done
exit "$rc"
