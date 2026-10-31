#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 0-01:00:00
#SBATCH -J trackA-timing
#SBATCH -o /scratch/%u/trackA/slurm/%x-%j.out
#SBATCH --signal=B:USR1@300
# Track A S1, the training timing run: 12 examples spread over the lengths, every version (~20-30 min)
# Submit only through submit.sh (its limit: the estimate x 1.3, rounded up to 30 min):
#   cot-disclosure/finetune/gpu/sol/submit.sh timing
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh timing "$@"
