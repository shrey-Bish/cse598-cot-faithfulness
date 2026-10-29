#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 0-01:00:00
#SBATCH -J trackA-prov-forced
#SBATCH -o /scratch/ragarw68/trackA/slurm/%x-%j.out
#SBATCH --signal=B:USR1@300
# Track A, B1's cheap test on set A (finetune/gpu/provenance_job.py forced): the forced answer at Step 10's cuts of
# set A's cases, per alpha and span (deployable, oracle); the chosen alpha per span by the written rule.
# Hugging Face only, no vLLM; one file per cut, so a rerun resumes. Submit only through submit.sh:
#   cot-disclosure/finetune/gpu/sol/submit.sh provenance_forced --estimate 0.5 -- --cases-from CASES --runs-from RUNS --items-from ITEMS
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh provenance_forced "$@"
