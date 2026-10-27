#!/bin/bash
# Run one Track A GPU step inside a Slurm job on Sol: your interactive session, or a batch job
# (the .sbatch scripts call this). Refuses outside a job, or under any account but the course one.
#   cot-disclosure/finetune/gpu/sol/run.sh smoke|step8|step9|step10 [arguments for the Python script]
# Output: $TRACKA_OUT/<step>/ (/scratch/ragarw68/trackA/<step>/), plus a log of the console there.
source "$(dirname "${BASH_SOURCE[0]}")/env.sh" || exit 1
set -euo pipefail
tracka_require_job

step=${1:?usage: run.sh smoke|step8|step9|step10 [args]}
shift
case "$step" in
    smoke)  script=finetune/gpu/smoke.py ;;
    step8)  script=finetune/gpu/checkpoint_check.py ;;
    step9)  script=finetune/look/attn_to_hint.py ;;
    step10) script=finetune/look/patching.py ;;
    *) echo "unknown step: $step (smoke, step8, step9, step10)" >&2; exit 2 ;;
esac
mkdir -p "$TRACKA_OUT/$step"
log="$TRACKA_OUT/$step/console_$(date +%Y%m%d_%H%M%S)_${SLURM_JOB_ID}.log"
cd "$TRACKA_CODE"
echo "job $SLURM_JOB_ID ($(tracka_account)) on $(hostname): $script $*" | tee "$log"
"$TRACKA_PY" "$script" "$@" 2>&1 | tee -a "$log"
