#!/bin/bash
# Install Track A's GPU packages into the existing project environment on Sol
# (/scratch/ragarw68/envs/olmo, Python 3.11). No vLLM: that comes with Steps 12-13.
#   bash cot-disclosure/finetune/gpu/sol/setup_env.sh            # in your session (a few minutes)
#   cot-disclosure/finetune/gpu/sol/submit.sh setup_env          # or as a lightwork job, no GPU
# torch 2.14.1 comes from PyTorch's CUDA 13.0 index: the driver reports CUDA 13.4, and a driver
# runs any CUDA build up to its own version. Everything else is pinned in requirements-sol.txt
# (the Mac's versions, except numpy: 2.5 needs Python 3.12). Safe to run again.
source "$(dirname "${BASH_SOURCE[0]}")/env.sh" || exit 1
set -euo pipefail
KIT=$TRACKA_CODE/finetune/gpu
export HF_HUB_OFFLINE=0                     # pip only; nothing here touches the model

"$TRACKA_PY" -m pip install --no-input "torch==2.14.1" --index-url https://download.pytorch.org/whl/cu130
"$TRACKA_PY" -m pip install --no-input -r "$KIT/requirements-sol.txt"
"$TRACKA_PY" -m pip install --no-input -r "$TRACKA_CODE/requirements.txt" -c "$KIT/requirements-sol.txt"
"$TRACKA_PY" -m pip check
"$TRACKA_PY" - <<'EOF'
import torch
assert torch.__version__.startswith("2.14.1") and torch.version.cuda, f"wrong torch: {torch.__version__} (CUDA {torch.version.cuda})"
if torch.cuda.is_available():                # a quick bf16 matmul on the GPU, when there is one
    x = torch.randn(1024, 1024, device="cuda", dtype=torch.bfloat16)
    torch.cuda.synchronize(); print("GPU matmul ok:", float((x @ x).float().abs().mean()) > 0)
EOF
"$TRACKA_PY" "$KIT/smoke.py" --versions
