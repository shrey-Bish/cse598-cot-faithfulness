#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -c 4
#SBATCH --mem=16G
#SBATCH -t 0-01:00:00
#SBATCH -J trackB-get-qwen3-8b
#SBATCH -o /scratch/ragarw68/trackA/slurm/%x-%j.out
# Track B's Qwen3-8B snapshot into $HF_HOME (/scratch/ragarw68/hf) unless it is cached, every file checked
# against the Hub's sha256, recorded in $TRACKA_OUT/trackb_qwen8b/snapshot.json (progress/sol_trackB.py
# --download). No GPU (public partition, class QoS); the only job with the network. Submit only through
# submit.sh:
#   cot-disclosure/finetune/gpu/sol/submit.sh get_qwen8b
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh get_qwen8b "$@"
