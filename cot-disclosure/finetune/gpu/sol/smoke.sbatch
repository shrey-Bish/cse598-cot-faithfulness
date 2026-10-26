#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q debug
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 0-00:15:00
#SBATCH -J trackA-smoke
#SBATCH -o /scratch/ragarw68/trackA/slurm/%x-%j.out
# Sol kit item 1 as a batch job (debug QoS, 15 min). Submit only through submit.sh, from anywhere:
#   cot-disclosure/finetune/gpu/sol/submit.sh smoke
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh smoke
