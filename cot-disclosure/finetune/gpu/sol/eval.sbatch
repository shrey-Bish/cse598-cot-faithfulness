#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 0-08:00:00
#SBATCH -J trackA-eval
#SBATCH -o /scratch/%u/trackA/slurm/%x-%j.out
#SBATCH --signal=B:USR1@300
# Track A E1-E6, evaluate one system, or one part of it (resumes). System and part as job arguments:
# Submit only through submit.sh (its limit: the estimate x 1.3, rounded up to 30 min):
#   cot-disclosure/finetune/gpu/sol/submit.sh eval --estimate 6 -- base 1/2
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh eval "$@"
