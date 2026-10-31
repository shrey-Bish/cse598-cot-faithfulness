#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=96G
#SBATCH -t 0-01:00:00
#SBATCH -J trackA-prov-bench
#SBATCH -o /scratch/%u/trackA/slurm/%x-%j.out
#SBATCH --signal=B:USR1@300
# Track A, B1's speed check (finetune/gpu/provenance_job.py bench, Oct 31): on set A's questions, never the 30, the
# decode time per step by rows and context, the generation engine before (a752db5's Batched) and after at alpha = 1
# and the deployable alpha on runs capped at 1,024 tokens, and the projection for the runs left. No answer is read.
# Its last line is the summary. Submit only through submit.sh:
#   cot-disclosure/finetune/gpu/sol/submit.sh provenance_bench -- --items-from /scratch/$USER/trackA/setA/items.jsonl --alpha-from /scratch/$USER/trackA/provenance_forced/provenance_forced.json
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh provenance_bench "$@"
