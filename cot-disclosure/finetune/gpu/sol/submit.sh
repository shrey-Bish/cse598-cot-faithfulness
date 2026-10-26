#!/bin/bash
# Submit one Track A batch job under the course account, and refuse anything else.
#   cot-disclosure/finetune/gpu/sol/submit.sh smoke|step8|step9|step10|setup_env [extra sbatch options]
# The account always comes from here (-A on the sbatch command line beats SBATCH_ACCOUNT and the
# script); an account option among the extras, or a script that names another account, is refused.
# Inside the job, run.sh checks the account again and stops if it isn't the course account.
set -euo pipefail
ACCOUNT=class_cse59888883fall2026
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$HERE/../../../.." && pwd)
job=${1:?usage: submit.sh smoke|step8|step9|step10|setup_env [sbatch options]}
shift
script="$HERE/$job.sbatch"
[ -f "$script" ] || { echo "no such job script: $script" >&2; exit 2; }

accounts=$(grep -E '^#SBATCH[[:space:]]+(-A|--account)' "$script" | sed -E 's/^#SBATCH[[:space:]]+(-A[[:space:]]*|--account[=[:space:]]+)//')
if [ "$accounts" != "$ACCOUNT" ]; then
    echo "refusing: $script must set exactly -A $ACCOUNT (it sets: ${accounts:-nothing})" >&2
    exit 1
fi
for opt in "$@"; do
    case "$opt" in
        -A*|--account*) echo "refusing: the account is set here ($ACCOUNT), not on the command line" >&2; exit 1 ;;
    esac
done

unset SBATCH_ACCOUNT SLURM_ACCOUNT
mkdir -p "${TRACKA_SLURM_LOGS:-/scratch/ragarw68/trackA/slurm}"   # the scripts' -o directory
cd "$REPO"                                   # the job starts here ($SLURM_SUBMIT_DIR)
sbatch -A "$ACCOUNT" "$@" "$script"
