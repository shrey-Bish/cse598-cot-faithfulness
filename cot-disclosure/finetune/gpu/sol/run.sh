#!/bin/bash
# Run one Track A GPU step inside a Slurm job on Sol: your interactive session, or a batch job
# (the .sbatch scripts call this). Refuses outside a job, or under an account not in accounts.conf.
#   cot-disclosure/finetune/gpu/sol/run.sh smoke|step8|step9|step10 [arguments for the Python script]
#   cot-disclosure/finetune/gpu/sol/run.sh timing                    # S1: 12 examples of every length, every version
#   cot-disclosure/finetune/gpu/sol/run.sh vllm_check                # S2: the vLLM tag check
#   cot-disclosure/finetune/gpu/sol/run.sh train VERSION [args]      # S3-S6: lora, tags, lora_tags, lora_attn3
#   cot-disclosure/finetune/gpu/sol/run.sh eval SYSTEM [K/N] [args]  # E1-E6: one system, the K-th of N parts
#   cot-disclosure/finetune/gpu/sol/run.sh val_loss [VERSION ...]    # validation loss by part: base + each version's epochs
#   cot-disclosure/finetune/gpu/sol/run.sh trackb_qwen8b [args]      # Track B: Qwen3-8B on vLLM (progress/sol_trackB.py)
#   cot-disclosure/finetune/gpu/sol/run.sh get_qwen8b                # its snapshot (no GPU; the only step online)
# Output: $TRACKA_OUT/<step>/ (/scratch/ragarw68/trackA/<step>/), plus a log of the console there.
# Slurm's warning before the time limit (sbatch --signal=B:USR1@300) is passed on to Python: training
# saves a resume checkpoint at its next optimizer step; evaluation stops and resumes in the next job.
source "$(dirname "${BASH_SOURCE[0]}")/env.sh" || exit 1
set -euo pipefail
tracka_require_job

step=${1:?usage: run.sh smoke|step8|step9|step10|timing|vllm_check|train|eval|val_loss|trackb_qwen8b|get_qwen8b [args]}
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
            version=${1:?usage: run.sh train lora|tags|lora_tags|lora_attn3}
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
    *) echo "unknown step: $step (smoke, step8, step9, step10, timing, vllm_check, train, eval, val_loss, trackb_qwen8b, get_qwen8b)" >&2; exit 2 ;;
esac
mkdir -p "$TRACKA_OUT/$step"
log="$TRACKA_OUT/$step/console_$(date +%Y%m%d_%H%M%S)_${SLURM_JOB_ID}.log"
cd "$TRACKA_CODE"
echo "job $SLURM_JOB_ID ($(tracka_account)) on $(hostname): $script ${args[*]}" | tee "$log"
"$TRACKA_PY" "$script" "${args[@]}" > >(tee -a "$log") 2>&1 &
pid=$!
trap 'kill -USR1 "$pid" 2>/dev/null' USR1 TERM
while true; do                                   # a trapped signal ends wait early: wait again for Python
    wait "$pid" && rc=0 || rc=$?
    if [ "$rc" -gt 128 ] && kill -0 "$pid" 2>/dev/null; then continue; fi
    break
done
exit "$rc"
