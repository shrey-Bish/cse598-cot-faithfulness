#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 0-02:00:00
#SBATCH -J trackC-c13
#SBATCH -o /scratch/%u/trackA/slurm/%x-%j.out
#SBATCH --signal=B:USR1@300
# Track C, C13 (agents/sol_c13.py): a third and a fourth reviewer family (IBM Granite 4.1 30B, Mistral Small
# 3.2 24B), reviewer only on C4's saved cases with C4's prompt, each served by our vLLM, one after the other;
# resumable. After set A's jobs. Submit only through submit.sh, with an estimate (limit = estimate x 1.3):
#   cot-disclosure/finetune/gpu/sol/submit.sh c13 --estimate 1.5
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh c13 "$@"
