# Track A on Sol: the environment every Sol script runs in. Source it, don't execute it:
#   source cot-disclosure/finetune/gpu/sol/env.sh
# It activates the existing project environment (it never creates one, and never uses the system
# python3, which is 3.6.8) and defines the account check every GPU run makes (guard.sh).
# Every script calls Python by its full path, "$TRACKA_PY", never a bare python: after an rsync or a
# changed PATH (Oct 26), a bare python can be the system one.

TRACKA_ENV=/scratch/ragarw68/envs/olmo         # Python 3.11, made with mamba create -p
TRACKA_PY=$TRACKA_ENV/bin/python
export HF_HOME=/scratch/ragarw68/hf             # Olmo 3 7B Think is already downloaded here
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1  # never download at run time
export TRACKA_OUT=${TRACKA_OUT:-/scratch/ragarw68/trackA}
export TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
TRACKA_REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)
TRACKA_CODE=$TRACKA_REPO/cot-disclosure
source "$(dirname "${BASH_SOURCE[0]}")/guard.sh" || return 1

module load mamba/latest || return 1
source activate "$TRACKA_ENV" || return 1
[ -x "$TRACKA_PY" ] || { echo "no Python at $TRACKA_PY" >&2; return 1; }
"$TRACKA_PY" - "$TRACKA_ENV" <<'EOF' || return 1
import os, sys
want = os.path.realpath(sys.argv[1])
if os.path.realpath(sys.prefix) != want or sys.version_info[:2] != (3, 11):
    sys.exit(f"wrong Python: {sys.executable} ({sys.version.split()[0]}); want {want}, Python 3.11")
EOF
