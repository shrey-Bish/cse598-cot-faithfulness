#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 0-02:00:00
#SBATCH -J trackB-qwen3-8b
#SBATCH -o /scratch/ragarw68/trackA/slurm/%x-%j.out
#SBATCH --signal=B:USR1@300
# Track B's Qwen3-8B on one A100 (progress/sol_trackB.py): the Track B runner on Hugging Face generation
# (--engine hf, the default since Oct 29) or our vLLM server (-- --engine vllm), core cells first,
# resumable. Submit only through submit.sh, with an estimate (limit = estimate x 1.3):
#   cot-disclosure/finetune/gpu/sol/submit.sh trackb_qwen8b --estimate 6.15
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh trackb_qwen8b "$@"
