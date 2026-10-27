# Track A on Sol: the account check every GPU run makes (sourced by env.sh; tested on the Mac).
# The allowed accounts are the ones listed in accounts.conf (today only class_cse59888883fall2026,
# the CSE 598 course account; never grp_hdavulcu).
TRACKA_ACCOUNTS_FILE="$(dirname "${BASH_SOURCE[0]}")/accounts.conf"
TRACKA_ACCOUNTS=$(awk '!/^[[:space:]]*(#|$)/ {print $1}' "$TRACKA_ACCOUNTS_FILE")
TRACKA_ACCOUNT=$(echo "$TRACKA_ACCOUNTS" | head -1)      # the default

tracka_account_allowed() {   # is $1 one of the listed accounts?
    [ -n "$1" ] && echo "$TRACKA_ACCOUNTS" | grep -qx -- "$1"
}

tracka_account() {      # the Slurm account of the job this shell is in
    if [ -n "${SLURM_JOB_ACCOUNT:-}" ]; then
        echo "$SLURM_JOB_ACCOUNT"
    elif [ -n "${SLURM_JOB_ID:-}" ]; then
        squeue -h -j "$SLURM_JOB_ID" -o %a 2>/dev/null
    fi
}

tracka_require_job() {  # GPU work runs only inside a Slurm job under a listed account
    if [ -z "${SLURM_JOB_ID:-}" ]; then
        echo "not inside a Slurm job: run this in your GPU session or through submit.sh, never on a login node" >&2
        return 1
    fi
    local acct
    acct=$(tracka_account)
    if ! tracka_account_allowed "$acct"; then
        echo "job $SLURM_JOB_ID runs under account '${acct:-unknown}', not one listed in accounts.conf: stopping" >&2
        return 1
    fi
}
