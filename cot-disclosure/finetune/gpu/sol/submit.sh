#!/bin/bash
# Submit one Track A batch job under an account listed in accounts.conf, and refuse anything else.
#   cot-disclosure/finetune/gpu/sol/submit.sh JOB [--estimate HOURS] [sbatch options] [-- job arguments]
# JOB is JOB.sbatch in this folder. The account always comes from here: the first one in
# accounts.conf, or TRACKA_SUBMIT_ACCOUNT if it names another listed one (-A on the sbatch command
# line beats SBATCH_ACCOUNT and the script). An account option among the extras, or a script that
# names an account not listed there, is refused. Inside the job, run.sh checks the account again.
#
# The class QoS (accounts.conf) counts each running job's remaining time x GPUs against 960
# GPU-minutes, the requested time is what counts, and DenyOnLimit rejects at submission any job whose
# own request is over it. So, for a job in the account's QoS:
#   --estimate H   the time limit becomes H x 1.3, rounded up to the next 30 minutes (else the script's -t)
#   refused here first: a limit x GPUs over the QoS's GPU-minutes, or over its MaxWall
#   before submitting: this job's GPU-minutes + the remaining GPU-minutes of your running jobs and the
#   requested GPU-minutes of your pending ones in that QoS (squeue); over the limit: a warning, and
#   when the job can start; both slots taken: when the second slot frees up
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$HERE/../../../.." && pwd)
source "$HERE/guard.sh"
ACCOUNT=${TRACKA_SUBMIT_ACCOUNT:-$TRACKA_ACCOUNT}
if ! tracka_account_allowed "$ACCOUNT"; then
    echo "refusing: account '$ACCOUNT' is not listed in $TRACKA_ACCOUNTS_FILE" >&2
    exit 1
fi
read -r PARTITION QOS GPU_RUN_MIN MAX_JOBS MAX_SUBMIT MAX_WALL_H MAX_GPUS < <(
    awk -v a="$ACCOUNT" '!/^[[:space:]]*#/ && $1 == a {print $2, $3, $4, $5, $6, $7, $8}' "$TRACKA_ACCOUNTS_FILE")

job=${1:?usage: submit.sh JOB [--estimate HOURS] [sbatch options] [-- job arguments]}
shift
script="$HERE/$job.sbatch"
[ -f "$script" ] || { echo "no such job script: $script" >&2; exit 2; }

estimate="" sb=() jobargs=()
while [ $# -gt 0 ]; do
    case "$1" in
        --estimate) estimate=${2:?--estimate needs hours}; shift 2 ;;
        --estimate=*) estimate=${1#*=}; shift ;;
        --) shift; jobargs=("$@"); break ;;
        -A*|--account*) echo "refusing: the account is set here ($ACCOUNT), not on the command line" >&2; exit 1 ;;
        *) sb+=("$1"); shift ;;
    esac
done

accounts=$(grep -E '^#SBATCH[[:space:]]+(-A|--account)' "$script" | sed -E 's/^#SBATCH[[:space:]]+(-A[[:space:]]*|--account[=[:space:]]+)//')
if [ "$(printf '%s\n' "$accounts" | grep -c .)" -ne 1 ] || ! tracka_account_allowed "$accounts"; then
    echo "refusing: $script must set exactly one -A, an account listed in accounts.conf (it sets: ${accounts:-nothing})" >&2
    exit 1
fi

opt() { grep -E "^#SBATCH[[:space:]]+$1" "$script" | tail -1 | sed -E "s/^#SBATCH[[:space:]]+$1[=[:space:]]*//"; }
script_qos=$(opt '(-q|--qos)')
gpus=$(opt '(-G|--gpus)' | awk -F: '{print ($NF ~ /^[0-9]+$/) ? $NF : 1}')
gpus=${gpus:-0}
to_min() { awk -v t="$1" 'BEGIN { d = 0; if (index(t, "-")) { split(t, a, "-"); d = a[1]; t = a[2] }
    n = split(t, a, ":"); m = (n == 3) ? a[1] * 60 + a[2] + a[3] / 60 : (n == 2) ? a[1] + a[2] / 60 : a[1];
    printf "%d", d * 1440 + m + 0.999 }'; }
if [ -n "$estimate" ]; then
    limit_min=$(awk -v h="$estimate" 'BEGIN { m = h * 60 * 1.3; printf "%d", 30 * int((m + 29.999) / 30) }')
else
    limit_min=$(to_min "$(opt '(-t|--time)')")
fi
limit=$(printf '%d:%02d:00' $((limit_min / 60)) $((limit_min % 60)))
need=$((limit_min * gpus))

if [ "$script_qos" = "$QOS" ]; then
    if [ "$limit_min" -gt $((MAX_WALL_H * 60)) ]; then
        echo "refusing: a $limit limit is over the $QOS QoS's MaxWall of $MAX_WALL_H h" >&2
        exit 1
    fi
    if [ "$need" -gt "$GPU_RUN_MIN" ]; then
        echo "refusing: $limit x $gpus GPU = $need GPU-minutes, over the $QOS QoS's $GPU_RUN_MIN" \
             "(DenyOnLimit would reject it at submission). Ask for less time: the job resumes from its checkpoint." >&2
        exit 1
    fi
    if command -v squeue >/dev/null 2>&1 && queue=$(squeue -h -u "${USER:-$(id -un)}" --qos="$QOS" -o "%i %T %L %l %b %e"); then
        printf '%s\n' "$queue" | awk -v need="$need" -v cap="$GPU_RUN_MIN" \
            -v maxjobs="$MAX_JOBS" -v maxsub="$MAX_SUBMIT" -v limit="$limit" -v gpus="$gpus" '
            function mins(t,   a, d, n) { if (t !~ /^[0-9]/) return 0; d = 0
                if (index(t, "-")) { split(t, a, "-"); d = a[1]; t = a[2] }
                n = split(t, a, ":"); return d * 1440 + (n == 3 ? a[1] * 60 + a[2] + a[3] / 60 : n == 2 ? a[1] + a[2] / 60 : a[1]) }
            function ngpu(g,   a, n) { if (g !~ /gpu/) return 1; n = split(g, a, ":"); return (a[n] ~ /^[0-9]+$/) ? a[n] : 1 }
            $2 == "RUNNING" { g = ngpu($5); used += mins($3) * g; rate += g; running++
                              if (first == "" || $6 < first) { first = $6; firstid = $1 } }
            $2 == "PENDING" { pend += mins($4) * ngpu($5); pending++ }
            END { total = used + pend + need
                printf "QoS check: this job %s x %d GPU = %d GPU-minutes; running %d (%d GPU-minutes left), pending %d (%d requested); total %d of %d\n",
                       limit, gpus, need, running, used, pending, pend, total, cap
                if (running + pending + 1 > maxsub) { print "refusing: you would have more than " maxsub " jobs in the QoS"; exit 3 }
                if (running >= maxjobs) printf "both slots are taken: the second slot frees up when job %s ends (%s)\n", firstid, first
                if (total > cap) {
                    printf "WARNING: over the %d GPU-minute limit by %d: the job waits", cap, total - cap
                    if (rate > 0) printf " about %d min, until the running jobs have used that much of their time", (total - cap) / rate + 0.999
                    print "" } }' || exit 1
    else
        echo "squeue not found or failed: running and pending jobs not checked"
    fi
else
    echo "QoS ${script_qos:-none} (not the account's $QOS): limits not checked"
fi

unset SBATCH_ACCOUNT SLURM_ACCOUNT
mkdir -p "${TRACKA_SLURM_LOGS:-/scratch/ragarw68/trackA/slurm}"   # the scripts' -o directory
cd "$REPO"                                   # the job starts here ($SLURM_SUBMIT_DIR)
override=()
if [ -n "${TRACKA_SUBMIT_ACCOUNT:-}" ] && [ "$script_qos" = "class" ]; then
    override=(-p "$PARTITION" -q "$QOS")      # another listed account: its own partition and QoS
fi
sbatch -A "$ACCOUNT" ${override[@]+"${override[@]}"} -t "$limit" ${sb[@]+"${sb[@]}"} "$script" ${jobargs[@]+"${jobargs[@]}"}
