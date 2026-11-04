#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=96G
#SBATCH -t 0-04:00:00
#SBATCH -J trackA-a39-1gpu
#SBATCH -o /scratch/%u/trackA/slurm/%x-%j.out
#SBATCH --signal=B:USR1@300
# A39 (Nov 3) on one GPU: the 30's jobs (too few runs to fill four GPUs) and the bench's 1-GPU shape; otherwise as
# a39.sbatch (48 runs in flight). Submit only through submit.sh:
#   cot-disclosure/finetune/gpu/sol/submit.sh a39_1gpu --estimate 2.5 -- base mmlupro_30
# Nov 4: Slurm's warning can come as the job ends, after its last run is saved. Job 460114 saved 90 of 90, then ended
# 138 (128 + USR1): run.sh's wait was cut short after Python had gone. So run.sh runs as this script's child, the
# warning is passed on, and a warned job with none of its part's runs left (finetune/eval.py's resume, as the feeder's
# left=) exits 0. Slurm keeps each job's copy of this script from its submission, so queued jobs keep the old one;
# run.sh, which they load when they start, is unchanged.
export A39_GPUS=1
cd "$SLURM_SUBMIT_DIR" || exit 1
cot-disclosure/finetune/gpu/sol/run.sh a39 "$@" &
pid=$!
warned=0
trap 'warned=1; kill -USR1 "$pid" 2>/dev/null' USR1 TERM
while true; do                                   # a trapped signal ends wait early: wait again for run.sh
    wait "$pid" && rc=0 || rc=$?
    if [ "$rc" -gt 128 ] && kill -0 "$pid" 2>/dev/null; then continue; fi
    break
done
if [ "$rc" -ne 0 ] && [ "$warned" = 1 ]; then
    left=$(source cot-disclosure/finetune/gpu/sol/env.sh >/dev/null 2>&1 && cd "$TRACKA_CODE" &&
           "$TRACKA_PY" - "$TRACKA_OUT/a39" "$@" 2>/dev/null <<'EOF'
import sys
from pathlib import Path
sys.path[:0] = [".", "progress"]
from finetune import eval as ev
out, system, qset = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
part = tuple(int(x) for x in sys.argv[4].split("/")) if len(sys.argv) > 4 and "/" in sys.argv[4] else None
done = {r["run_id"] for r in ev.latest([r for p in ev.runs_files(out, system, qset, "a39") for r in ev.load(p)])
        if r["status"] == "ok"}
print(sum(1 for j in ev.jobs(part, qset, "a39", system) if ev.job_id(system, j) not in done))
EOF
    )
    if [ "$left" = 0 ]; then
        echo "exit $rc after Slurm's warning, with none of the part's runs left: the job exits 0"
        rc=0
    else
        echo "exit $rc after Slurm's warning; runs left: ${left:-not counted}"
    fi
fi
exit "$rc"
