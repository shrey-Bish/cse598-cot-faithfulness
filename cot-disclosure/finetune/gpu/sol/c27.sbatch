#!/bin/bash
#SBATCH -A class_cse59888883fall2026
#SBATCH -p public
#SBATCH -q class
#SBATCH -G a100:1
#SBATCH -c 8
#SBATCH --mem=96G
#SBATCH -t 0-03:00:00
#SBATCH -J trackA-c27
#SBATCH -o /scratch/%u/trackA/slurm/%x-%j.out
#SBATCH --signal=B:USR1@300
# C27 (Nov 26, post-freeze addendum, exploratory; pre-registered in
# archive/sessions/2026-11-26/2026-11-26_1712_A_c27-prereg.md): one system (base or a40) on C15's 100 items, the
# inserted tool turn with the oracle's letter and the checker's no-tool run (finetune/eval.py --design c27 --qset c15),
# on one GPU, 48 runs in flight. As a39_1gpu.sbatch otherwise. Submit only through submit.sh:
#   cot-disclosure/finetune/gpu/sol/submit.sh c27 --estimate 1.7 -- base
cd "$SLURM_SUBMIT_DIR" || exit 1
cot-disclosure/finetune/gpu/sol/run.sh c27 "$@" &
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
           "$TRACKA_PY" - "$TRACKA_OUT/c27" "$@" 2>/dev/null <<'EOF'
import sys
from pathlib import Path
sys.path[:0] = [".", "progress"]
from finetune import eval as ev
out, system = Path(sys.argv[1]), sys.argv[2]
done = {r["run_id"] for r in ev.latest([r for p in ev.runs_files(out, system, "c15", "c27") for r in ev.load(p)])
        if r["status"] == "ok"}
print(sum(1 for j in ev.jobs(None, "c15", "c27", system) if ev.job_id(system, j) not in done))
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
