#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 0-04:00:00
#SBATCH -J trackA-train
#SBATCH -o /scratch/ragarw68/trackA/slurm/%x-%j.out
#SBATCH --signal=B:USR1@300
# Track A S3-S6, train one version (2-3 h; resumes from its checkpoint). Version as the job argument:
# Submit only through submit.sh (its limit: the estimate x 1.3, rounded up to 30 min):
#   cot-disclosure/finetune/gpu/sol/submit.sh train --estimate 3 -- lora
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh train "$@"
