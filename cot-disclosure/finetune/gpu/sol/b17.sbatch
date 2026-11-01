#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 0-01:00:00
#SBATCH -J trackB-b17-gpt-oss-20b
#SBATCH -o /scratch/%u/trackA/slurm/%x-%j.out
#SBATCH --signal=B:USR1@300
# B17 (Oct 31): gpt-oss-20b at reasoning effort low, medium and high on our vLLM server, one A100
# (progress/sol_b17.py): the option check, the snapshot check, the served-template check, then the runner
# (progress/run_b17.py), resumable. Submit only through submit.sh, with an estimate (limit = estimate x 1.3):
#   cot-disclosure/finetune/gpu/sol/submit.sh b17 --estimate 0.75 -- --smoke     # first: the design's first 15 runs
#   cot-disclosure/finetune/gpu/sol/submit.sh b17 --estimate 6                   # then the rest; again if runs are left
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh b17 "$@"
