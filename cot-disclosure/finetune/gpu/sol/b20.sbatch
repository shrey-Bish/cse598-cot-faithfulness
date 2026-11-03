#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=128G
#SBATCH -t 0-01:30:00
#SBATCH -J trackB-b20
#SBATCH -o /scratch/%u/trackA/slurm/%x-%j.out
#SBATCH --signal=B:USR1@300
# B20 (Nov 3): one of three new families (gemma-4-26b-a4b-it, nemotron-3-nano-30b-a3b, granite-4.2-8b) on our vLLM
# server, one A100, thinking on and off (progress/sol_b20.py): the option check, the snapshot check, the
# served-template check, the canary, then the runner (progress/run_b20.py), resumable. 128 GB: up to 63 GB of bf16
# weights pass through the page cache. Submit only through submit.sh, the model before -- (limit = estimate x 1.3;
# without --estimate, 1 h for the smoke and 6 h for the runs):
#   cot-disclosure/finetune/gpu/sol/submit.sh b20 --model M -- --smoke    # first: the design's first 12 runs
#   cot-disclosure/finetune/gpu/sol/submit.sh b20 --model M               # then the rest; again if runs are left
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh b20 "$@"
