#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -c 4
#SBATCH --mem=16G
#SBATCH -t 0-03:00:00
#SBATCH -J trackC-get-c13
#SBATCH -o /scratch/ragarw68/trackA/slurm/%x-%j.out
# C13's two reviewer snapshots into $HF_HOME (/scratch/ragarw68/hf) unless cached (about 106 GB: Granite 4.1
# 30B 57.7, Mistral Small 3.2 24B 48.0 in its own format), every file checked against the Hub, recorded in
# $TRACKA_OUT/c13/snapshot_<model>.json (agents/sol_c13.py --download). No GPU (public partition, class
# QoS); with get_qwen8b, the only jobs with the network. Submit only through submit.sh:
#   cot-disclosure/finetune/gpu/sol/submit.sh get_c13
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh get_c13 "$@"
