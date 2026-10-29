#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=96G
#SBATCH -t 0-08:00:00
#SBATCH -J trackA-prov-gen
#SBATCH -o /scratch/ragarw68/trackA/slurm/%x-%j.out
#SBATCH --signal=B:USR1@300
# Track A, B1 (and B2's gate versions): generation on the held-out 30 MMLU-Pro questions with provenance-scaled
# attention (finetune/gpu/provenance_job.py generate): alpha = 1 and the chosen alphas, or a gate version's
# learned biases. Batched Hugging Face generation, no vLLM; every run is saved as it ends, so a rerun resumes.
# Submit only through submit.sh (split by --part to stay under the limit):
#   cot-disclosure/finetune/gpu/sol/submit.sh provenance_gen --estimate 5.5 --dependency=afterok:<forced job> -- --alpha-from /scratch/ragarw68/trackA/provenance_forced/provenance_forced.json --part 1/3
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh provenance_gen "$@"
