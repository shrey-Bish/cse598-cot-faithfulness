#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -c 4
#SBATCH --mem=16G
#SBATCH -t 0-01:00:00
#SBATCH -J trackB-get-gpt-oss-20b
#SBATCH -o /scratch/%u/trackA/slurm/%x-%j.out
# B17's gpt-oss-20b snapshot (openai/gpt-oss-20b at its pinned revision, ~13.8 GB: the MXFP4 shards, the tokenizer,
# the chat template) into $HF_HOME (/scratch/$USER/hf) unless it is cached, every file checked against the Hub,
# recorded in $TRACKA_OUT/b17/snapshot.json (progress/sol_b17.py --download). No GPU (public partition, class QoS);
# the only B17 job with the network. Submit only through submit.sh:
#   cot-disclosure/finetune/gpu/sol/submit.sh get_gptoss
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh get_gptoss "$@"
