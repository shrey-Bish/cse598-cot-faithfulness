#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 0-04:00:00
#SBATCH -J trackA-step10
#SBATCH -o /scratch/%u/trackA/slurm/%x-%j.out
# Track A Step 10, activation patching (~1-2 h; resumes from the cuts already saved). Submit only
# through submit.sh:   cot-disclosure/finetune/gpu/sol/submit.sh step10
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh step10 "$@"
