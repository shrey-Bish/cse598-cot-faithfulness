#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=96G
#SBATCH -t 0-02:00:00
#SBATCH -J trackA-a18
#SBATCH -o /scratch/%u/trackA/slurm/%x-%j.out
#SBATCH --signal=B:USR1@300
# A18 (Oct 31): inside the fixed model (finetune/look/a18.py): step3 --system base|lora (probes and cases), step10
# --cases C --weights W (patching at the takeover), swap (base and LoRA both loaded), step9 --system S (attention).
# Hugging Face only; resumable (one file or row per run, cut or case); numbers only in $TRACKA_OUT/a18/, except
# sources_<system>.jsonl.gz (the evaluation's texts, which stay on Sol). Submit only through submit.sh:
#   cot-disclosure/finetune/gpu/sol/submit.sh a18 --estimate 1 -- step3 --system base
#   cot-disclosure/finetune/gpu/sol/submit.sh a18 --estimate 1.2 --dependency=afterok:<step3 base> -- swap
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh a18 "$@"
