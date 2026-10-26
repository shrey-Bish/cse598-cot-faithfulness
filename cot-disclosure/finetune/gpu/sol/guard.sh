# Track A on Sol: the account check every GPU run makes (sourced by env.sh; tested on the Mac).
TRACKA_ACCOUNT=class_cse59888883fall2026       # CSE 598 course account: all Track A jobs (never grp_hdavulcu)

tracka_account() {      # the Slurm account of the job this shell is in
    if [ -n "${SLURM_JOB_ACCOUNT:-}" ]; then
        echo "$SLURM_JOB_ACCOUNT"
    elif [ -n "${SLURM_JOB_ID:-}" ]; then
        squeue -h -j "$SLURM_JOB_ID" -o %a 2>/dev/null
    fi
}

tracka_require_job() {  # GPU work runs only inside a Slurm job under the course account
    if [ -z "${SLURM_JOB_ID:-}" ]; then
        echo "not inside a Slurm job: run this in your GPU session or through submit.sh, never on a login node" >&2
        return 1
    fi
    local acct
    acct=$(tracka_account)
    if [ "$acct" != "$TRACKA_ACCOUNT" ]; then
        echo "job $SLURM_JOB_ID runs under account '${acct:-unknown}', not $TRACKA_ACCOUNT: stopping" >&2
        return 1
    fi
}
