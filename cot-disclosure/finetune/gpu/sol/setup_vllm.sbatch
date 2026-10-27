#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p lightwork
#SBATCH -q public
#SBATCH -c 4
#SBATCH --mem=16G
#SBATCH -t 0-01:00:00
#SBATCH -J trackA-setup-vllm
#SBATCH -o /scratch/ragarw68/trackA/slurm/%x-%j.out
# setup_vllm.sh as a job without a GPU (lightwork partition, public QoS). Submit only through submit.sh:
#   cot-disclosure/finetune/gpu/sol/submit.sh setup_vllm
cd "$SLURM_SUBMIT_DIR"
source cot-disclosure/finetune/gpu/sol/env.sh || exit 1
tracka_require_job || exit 1
exec bash cot-disclosure/finetune/gpu/sol/setup_vllm.sh
