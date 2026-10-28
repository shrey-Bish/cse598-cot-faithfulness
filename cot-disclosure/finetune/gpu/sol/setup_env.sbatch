#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -c 4
#SBATCH --mem=16G
#SBATCH -t 0-01:00:00
#SBATCH -J trackA-setup
#SBATCH -o /scratch/ragarw68/trackA/slurm/%x-%j.out
# setup_env.sh as a job without a GPU (public partition, class QoS: the course account's only QoS). Submit only through submit.sh:
#   cot-disclosure/finetune/gpu/sol/submit.sh setup_env
cd "$SLURM_SUBMIT_DIR"
source cot-disclosure/finetune/gpu/sol/env.sh || exit 1
tracka_require_job || exit 1
exec bash cot-disclosure/finetune/gpu/sol/setup_env.sh
