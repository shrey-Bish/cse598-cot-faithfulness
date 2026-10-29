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
#
# The job script's partition and QoS must be a pair accounts.conf lists for the account (Oct 28: the
# course account has only the class QoS; "-q public" was rejected by sbatch); else refused here, before
# sbatch. Partition and QoS are set in the job script, never on the command line.
#
# --dependency (afterok:N etc.): every named job must be running or pending, and of a kind this job
# may wait for (depends_on below; e.g. vllm_check waits for setup_vllm), else the submission is refused.
#
# train and eval need their argument after --: a version (train), a system and an optional K/N part
# (eval). Without it they are refused here, not when the job starts hours later. val_loss takes
# versions only (none: lora tags).
# It always ends with sbatch's "Submitted batch job N", or a clear error and a non-zero exit code.
set -euo pipefail
trap 'echo "submit.sh: stopped at line $LINENO ($BASH_COMMAND): exit $?. Nothing was submitted." >&2' ERR
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$HERE/../../../.." && pwd)
source "$HERE/guard.sh"
ACCOUNT=${TRACKA_SUBMIT_ACCOUNT:-$TRACKA_ACCOUNT}
if ! tracka_account_allowed "$ACCOUNT"; then
    echo "refusing: account '$ACCOUNT' is not listed in $TRACKA_ACCOUNTS_FILE" >&2
    exit 1
fi
rows=$(awk -v a="$ACCOUNT" '!/^[[:space:]]*#/ && $1 == a {print $2, $3, $4, $5, $6, $7, $8}' "$TRACKA_ACCOUNTS_FILE")

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
        -q*|--qos*|-p*|--partition*)
            echo "refusing: the partition and QoS come from the job script, checked against accounts.conf, not the command line" >&2
            exit 1 ;;
        *) sb+=("$1"); shift ;;
    esac
done

# Oct 28: lora_tags and lora_attn3 (afterany on lora and tags) reached run.sh with no version and
# failed in seconds when they started, hours after they were submitted
versions="lora tags lora_tags lora_attn3"
gates="gate3 lora_attn3_gate"              # B2 (Oct 29): trained and measured like the others; not served by vLLM (no eval)
case "$job" in
    train) want="$versions $gates" ;;
    eval)  want="base prompt_only $versions" ;;
    *)     want="" ;;
esac
if [ -n "$want" ] && ! printf '%s\n' $want | grep -qx -- "${jobargs[0]:-}"; then
    echo "refusing: $job needs one of: $want, after -- (submit.sh $job --estimate H -- ${want%% *});" \
         "got: '${jobargs[*]:-nothing}'. Nothing was submitted." >&2
    exit 1
fi
if [ "$job" = val_loss ]; then              # versions only (none: lora tags); the base model always comes first
    for v in ${jobargs[@]+"${jobargs[@]}"}; do
        if ! printf '%s\n' $versions $gates | grep -qx -- "$v"; then
            echo "refusing: val_loss takes versions after -- (of: $versions $gates); got: '$v'. Nothing was submitted." >&2
            exit 1
        fi
    done
fi

accounts=$(grep -E '^#SBATCH[[:space:]]+(-A|--account)' "$script" | sed -E 's/^#SBATCH[[:space:]]+(-A[[:space:]]*|--account[=[:space:]]+)//')
if [ "$(printf '%s\n' "$accounts" | grep -c .)" -ne 1 ] || ! tracka_account_allowed "$accounts"; then
    echo "refusing: $script must set exactly one -A, an account listed in accounts.conf (it sets: ${accounts:-nothing})" >&2
    exit 1
fi

opt() { { grep -E "^#SBATCH[[:space:]]+$1" "$2" || true; } | tail -1 | sed -E "s/^#SBATCH[[:space:]]+$1[=[:space:]]*//"; }
script_qos=$(opt '(-q|--qos)' "$script")
script_part=$(opt '(-p|--partition)' "$script")
row=$(printf '%s\n' "$rows" | awk -v p="$script_part" -v q="$script_qos" '$1 == p && $2 == q' | head -1)
override=()
if [ -z "$row" ] && [ -n "${TRACKA_SUBMIT_ACCOUNT:-}" ]; then
    row=$(printf '%s\n' "$rows" | head -1)                  # another listed account: its own partition and QoS
    override=(-p "${row%% *}" -q "$(echo "$row" | awk '{print $2}')")
fi
if [ -z "$row" ]; then
    echo "refusing: $job.sbatch asks for partition '${script_part:-none}' and QoS '${script_qos:-none}'," \
         "which accounts.conf doesn't list for $ACCOUNT (listed: $(printf '%s\n' "$rows" | awk '{printf "%s-p %s -q %s", (NR > 1 ? "; " : ""), $1, $2}'))." \
         "sbatch would reject it (Invalid qos specification); nothing was submitted." >&2
    exit 1
fi
read -r PARTITION QOS GPU_RUN_MIN MAX_JOBS MAX_SUBMIT MAX_WALL_H MAX_GPUS <<< "$row"
gpus=$(opt '(-G|--gpus)' "$script" | awk -F: '{print ($NF ~ /^[0-9]+$/) ? $NF : 1}')
gpus=${gpus:-0}
to_min() { awk -v t="$1" 'BEGIN { d = 0; if (index(t, "-")) { split(t, a, "-"); d = a[1]; t = a[2] }
    n = split(t, a, ":"); m = (n == 3) ? a[1] * 60 + a[2] + a[3] / 60 : (n == 2) ? a[1] + a[2] / 60 : a[1];
    printf "%d", d * 1440 + m + 0.999 }'; }
if [ -n "$estimate" ]; then
    limit_min=$(awk -v h="$estimate" 'BEGIN { m = h * 60 * 1.3; printf "%d", 30 * int((m + 29.999) / 30) }')
else
    limit_min=$(to_min "$(opt '(-t|--time)' "$script")")
fi
limit=$(printf '%d:%02d:00' $((limit_min / 60)) $((limit_min % 60)))
need=$((limit_min * gpus))

if true; then                                 # always a listed QoS (checked above)
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
fi

# --dependency: the named jobs must be running or pending, and of a kind this job may wait for
depends_on() {          # the job kinds each job may wait for (plain case: works in any bash)
    case "$1" in
        vllm_check) echo "setup_vllm" ;;
        eval) echo "setup_vllm vllm_check train" ;;
        train) echo "timing train" ;;
        val_loss) echo "train" ;;
        provenance_gen) echo "provenance_forced train" ;;
        trackb_qwen8b) echo "setup_vllm get_qwen8b trackb_qwen8b" ;;
        c13) echo "get_c13 step10 step9 provenance_forced c13" ;;     # after set A's jobs (Oct 29)
    esac
}
deps=""
for ((i = 0; i < ${#sb[@]}; i++)); do
    case "${sb[$i]}" in
        --dependency=*|-d=*) deps=${sb[$i]#*=} ;;
        --dependency|-d) deps=${sb[$((i + 1))]:-} ;;
        -d*) deps=${sb[$i]#-d} ;;
    esac
done
if [ -n "$deps" ]; then
    kinds=$(depends_on "$job")
    [ -n "$kinds" ] || { echo "refusing: $job waits for no other job; drop --dependency" >&2; exit 1; }
    names=$(for k in $kinds; do opt '(-J|--job-name)' "$HERE/$k.sbatch"; done)
    ids=$(echo "$deps" | tr ',?' '\n\n' | sed -E 's/^[a-z]+://' | tr ':' '\n' | grep -E '^[0-9]+$' || true)
    [ -n "$ids" ] || { echo "refusing: no job id in --dependency=$deps" >&2; exit 1; }
    command -v squeue >/dev/null 2>&1 || { echo "refusing: squeue not found, so --dependency can't be checked" >&2; exit 1; }
    for id in $ids; do
        info=$(squeue -h -j "$id" -o "%T %j" 2>/dev/null || true)
        state=${info%% *} name=${info#* }
        if [ "$state" != "RUNNING" ] && [ "$state" != "PENDING" ]; then
            echo "refusing: dependency job $id is not running or pending (squeue: '${info:-not found}'); if it finished OK, submit without --dependency" >&2
            exit 1
        fi
        if ! printf '%s\n' "$names" | grep -qx -- "$name"; then
            echo "refusing: dependency job $id is '$name'; $job may wait only for: $(echo $names | tr ' ' ',')" >&2
            exit 1
        fi
        echo "dependency ok: job $id ($name, $state)"
    done
fi

unset SBATCH_ACCOUNT SLURM_ACCOUNT
mkdir -p "${TRACKA_SLURM_LOGS:-/scratch/ragarw68/trackA/slurm}"   # the scripts' -o directory
cd "$REPO"                                   # the job starts here ($SLURM_SUBMIT_DIR)
trap - ERR
if ! out=$(sbatch -A "$ACCOUNT" ${override[@]+"${override[@]}"} -t "$limit" ${sb[@]+"${sb[@]}"} "$script" \
           ${jobargs[@]+"${jobargs[@]}"} 2>&1); then
    echo "sbatch refused the job: ${out:-no message}" >&2
    exit 1
fi
echo "$out"
if ! printf '%s\n' "$out" | grep -qE '^Submitted batch job [0-9]+'; then
    echo "sbatch printed no job id: nothing may have been submitted; check squeue -u ${USER:-$(id -un)}" >&2
    exit 1
fi
