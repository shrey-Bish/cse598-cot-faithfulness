#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:4
#SBATCH -c 32
#SBATCH --mem=192G
#SBATCH -t 0-02:00:00
#SBATCH -J trackA-a39
#SBATCH -o /scratch/%u/trackA/slurm/%x-%j.out
#SBATCH --signal=B:USR1@300
# A39 (Nov 3): one system on one question set (e2 or mmlupro_30), or one part of it (resumes), in finetune/eval.py's
# lean design: one vLLM server over the 4 GPUs (--data-parallel-size 4), 192 runs in flight; $TRACKA_OUT/a39/.
# 4 GPUs x 2:00 is half the class QoS's 960 running GPU-minutes, so two run at once. Submit only through submit.sh:
#   cot-disclosure/finetune/gpu/sol/submit.sh a39 --estimate 1.5 -- base e2 1/2
#   cot-disclosure/finetune/gpu/sol/submit.sh a39 --estimate 0.75 -- base e2 1/2 --limit 384    # the bench (R3)
cd "$SLURM_SUBMIT_DIR" && exec cot-disclosure/finetune/gpu/sol/run.sh a39 "$@"
