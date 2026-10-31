#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 0-00:30:00
#SBATCH -J trackA-step8
#SBATCH -o /scratch/%u/trackA/slurm/%x-%j.out
# Track A Step 8, the checkpoint check (~5-10 min). Submit only through submit.sh:
#   cot-disclosure/finetune/gpu/sol/submit.sh step8
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh step8 "$@"
