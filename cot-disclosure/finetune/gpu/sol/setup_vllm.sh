#!/bin/bash
# Make vLLM's own environment for Steps 12-13 on Sol: $TRACKA_VLLM_ENV (/scratch/ragarw68/envs/olmo-vllm,
# Python 3.11) with vLLM 0.31.0 (released Oct 5; it pins torch 2.13.0 and transformers < 5.18, so it
# can't share the project environment, which has torch 2.14.1 and transformers 5.18.0). Only the
# server runs there: finetune/gpu/eval_job.py (project environment) starts "$TRACKA_VLLM serve".
#   bash cot-disclosure/finetune/gpu/sol/setup_vllm.sh            # in your session (10-20 minutes)
#   cot-disclosure/finetune/gpu/sol/submit.sh setup_vllm          # or as a lightwork job, no GPU
# Safe to run again.
source "$(dirname "${BASH_SOURCE[0]}")/env.sh" || exit 1
set -euo pipefail
VLLM_VERSION=0.31.0
export HF_HUB_OFFLINE=0                     # pip only; nothing here touches the model
# never the project environment: it stays exactly as Steps 8-10 used it (decided Oct 27)
if [ "$(realpath -m "$TRACKA_VLLM_ENV")" = "$(realpath -m "$TRACKA_ENV")" ]; then
    echo "refusing: the vLLM environment must not be the project environment ($TRACKA_ENV)" >&2
    exit 1
fi
if [ ! -x "$TRACKA_VLLM_PY" ]; then
    mamba create -y -p "$TRACKA_VLLM_ENV" "python=3.11"
fi
"$TRACKA_VLLM_PY" -m pip install --no-input "vllm==$VLLM_VERSION"
"$TRACKA_VLLM_PY" -m pip check || echo "pip check reported conflicts (above); vLLM's own pins win in this environment"
"$TRACKA_VLLM_PY" - <<'PY'
import torch, vllm
print("vllm", vllm.__version__, "torch", torch.__version__, "CUDA", torch.version.cuda)
assert vllm.__version__ == "0.31.0", vllm.__version__
PY
[ -x "$TRACKA_VLLM" ] && echo "server command: $TRACKA_VLLM"
