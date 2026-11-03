#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=96G
#SBATCH -t 0-04:00:00
#SBATCH -J trackA-a39-1gpu
#SBATCH -o /scratch/%u/trackA/slurm/%x-%j.out
#SBATCH --signal=B:USR1@300
# A39 (Nov 3) on one GPU: the 30's jobs (too few runs to fill four GPUs) and the bench's 1-GPU shape; otherwise as
# a39.sbatch (48 runs in flight). Submit only through submit.sh:
#   cot-disclosure/finetune/gpu/sol/submit.sh a39_1gpu --estimate 2.5 -- base mmlupro_30
export A39_GPUS=1
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh a39 "$@"
