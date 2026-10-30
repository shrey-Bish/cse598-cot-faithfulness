#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 0-02:00:00
#SBATCH -J qwen8b-step3
#SBATCH -o /scratch/ragarw68/trackA/slurm/%x-%j.out
#SBATCH --signal=B:USR1@300
# Thread 1 on Qwen3-8B, Step 3 (finetune/look/qwen8b_mech.py step3): forced-answer probes after every sentence of
# Track B's followed thinking-on runs (results/trackB/sol_vllm.jsonl.gz in the clone), takeover points, and the
# cases (late takeovers on sure questions) for Step 10. Hugging Face only, offline; resumable (finished runs are
# skipped). Numbers only in $TRACKA_OUT/qwen8b_step3/. Submit only through submit.sh, with an estimate:
#   cot-disclosure/finetune/gpu/sol/submit.sh qwen8b_step3 --estimate 1.2
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh qwen8b_step3 "$@"
