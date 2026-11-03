#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -c 4
#SBATCH --mem=16G
#SBATCH -t 0-02:00:00
#SBATCH -J trackB-get-b20
#SBATCH -o /scratch/%u/trackA/slurm/%x-%j.out
# B20's snapshot of one model at its pinned revision (progress/run_b20.py MODELS: 18-63 GB of bf16 weights, the
# tokenizer, the chat template, Nemotron's and Granite's code files) into $HF_HOME (/scratch/$USER/hf) unless it is
# cached, every file checked against the Hub, recorded in $TRACKA_OUT/b20/<model>/snapshot.json (progress/sol_b20.py
# --download). No GPU (public partition, class QoS); the only B20 job with the network. Submit only through submit.sh:
#   cot-disclosure/finetune/gpu/sol/submit.sh get_b20 --model M
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh get_b20 "$@"
