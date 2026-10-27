#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 0-01:30:00
#SBATCH -J trackA-vllm_check
#SBATCH -o /scratch/ragarw68/trackA/slurm/%x-%j.out
#SBATCH --signal=B:USR1@300
# Track A S2, the vLLM tag check: served vs Hugging Face, plain and tagged (<= 1 h)
# Submit only through submit.sh (its limit: the estimate x 1.3, rounded up to 30 min):
#   cot-disclosure/finetune/gpu/sol/submit.sh vllm_check
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh vllm_check "$@"
