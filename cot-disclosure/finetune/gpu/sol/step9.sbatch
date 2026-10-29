#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 0-02:00:00
#SBATCH -J trackA-step9
#SBATCH -o /scratch/ragarw68/trackA/slurm/%x-%j.out
# Track A Step 9, attention to the hint (~15-40 min; resumes from the runs already saved). Submit only
# through submit.sh:   cot-disclosure/finetune/gpu/sol/submit.sh step9
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh step9 "$@"
