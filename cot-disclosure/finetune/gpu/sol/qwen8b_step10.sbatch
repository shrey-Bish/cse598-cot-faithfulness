#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 0-05:00:00
#SBATCH -J qwen8b-step10
#SBATCH -o /scratch/%u/trackA/slurm/%x-%j.out
#SBATCH --signal=B:USR1@300
# Thread 1 on Qwen3-8B, Step 10 (finetune/look/qwen8b_mech.py step10): activation patching at cuts (i) and (ii) of
# Step 3's cases, the puzzles' tool_real cases first (localization), then MMLU-Pro's (replication), then the
# secondary channels; then the summary and the readout by the pre-registered rules. Hugging Face only; one file per
# cut, so a rerun resumes. Numbers only in $TRACKA_OUT/qwen8b_step10/. Submit only through submit.sh:
#   cot-disclosure/finetune/gpu/sol/submit.sh qwen8b_step10 --estimate 4.3 --dependency=afterok:<the Step 3 job>
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh qwen8b_step10 "$@"
