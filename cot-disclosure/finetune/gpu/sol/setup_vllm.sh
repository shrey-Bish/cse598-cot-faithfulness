#!/bin/bash
# Make vLLM's own environment for Steps 12-13 on Sol: $TRACKA_VLLM_ENV (/scratch/$USER/envs/olmo-vllm,
# Python 3.11) with vLLM 0.31.0 (released Oct 5; it pins torch 2.13.0 and transformers < 5.18, so it
# can't share the project environment, which has torch 2.14.1 and transformers 5.18.0). Only the
# server runs there: finetune/gpu/eval_job.py (project environment) starts "$TRACKA_VLLM serve".
#   bash cot-disclosure/finetune/gpu/sol/setup_vllm.sh            # in your session (10-20 minutes)
#   cot-disclosure/finetune/gpu/sol/submit.sh setup_vllm          # or as a job without a GPU (public, class QoS)
# Safe to run again.
source "$(dirname "${BASH_SOURCE[0]}")/env.sh" || exit 1
set -euo pipefail
# the version is the committed option list's (finetune/gpu/vllm_serve_options.txt): one source for both
VLLM_OPTIONS=${TRACKA_VLLM_OPTIONS:-$TRACKA_CODE/finetune/gpu/vllm_serve_options.txt}
VLLM_VERSION=$("$TRACKA_PY" "$TRACKA_CODE/finetune/gpu/vllm_options.py" --list-version --committed "$VLLM_OPTIONS")
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
"$TRACKA_VLLM_PY" -c 'import importlib.metadata as m; print("vllm", m.version("vllm"), "torch", m.version("torch"))'
[ -x "$TRACKA_VLLM" ] || { echo "no server command at $TRACKA_VLLM after the install" >&2; exit 1; }
# The server options, without a GPU: the CUDA build can't print `vllm serve --help=all` on a CPU node
# (Oct 28: "Failed to infer device type"), so no --help here. The installed version must be the
# committed list's, and every server command the jobs start must use only options that list has.
# Each vLLM GPU job then compares the node's own --help=all with the list as its first step.
installed=$("$TRACKA_VLLM_PY" -c 'import importlib.metadata as m; print(m.version("vllm"))')
"$TRACKA_PY" "$TRACKA_CODE/finetune/gpu/vllm_options.py" --check-commands --installed "$installed" --committed "$VLLM_OPTIONS"
echo "setup_vllm done: vLLM $installed in $TRACKA_VLLM_ENV; the server commands fit the committed list"
