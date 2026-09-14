#!/usr/bin/env bash
# Create / update the `eegbench` conda environment (see docs/DECISIONS.md D-009).
#
#   bash scripts/setup_env.sh            # create env + install everything
#   bash scripts/setup_env.sh --check    # only run the import checks
#
# Choices:
#   * Python 3.10, torch 2.7.1+cu128 — matches the cluster driver (CUDA 12.8) and the mamba_ssm-2.3.1 wheel
#     already present in the user's pip cache, so EEGMamba needs no CUDA compilation on the login node.
#   * Everything from third_party/eeg_fm_benchmark/requirements.txt except mamba-ssm, which is installed
#     afterwards (prefers cached/prebuilt wheel; falls back to `--no-build-isolation` build only if asked).
set -euo pipefail

ENV_NAME="${ENV_NAME:-eegbench}"
PY_VER="3.10"
TORCH_INDEX="https://download.pytorch.org/whl/cu128"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Some agent harnesses point these at an unwritable sandbox dir; force the user's own caches.
export PIP_CACHE_DIR="$HOME/.cache/pip"
export CONDA_PKGS_DIRS="$HOME/.conda/pkgs"

# shellcheck disable=SC1091
source /share/software/anaconda3/2024.10/etc/profile.d/conda.sh

env_python() {
  local p
  p="$(conda env list | awk -v n="$ENV_NAME" '$1==n {print $NF}')/bin/python"
  [[ -x "$p" ]] || { echo "env $ENV_NAME not found" >&2; return 1; }
  echo "$p"
}

check() {
  # call the env interpreter directly: `conda run` does not forward heredoc stdin reliably
  "$(env_python)" - <<'EOF'
import importlib, sys
mods = ["torch", "torchvision", "numpy", "scipy", "sklearn", "pandas", "mne", "moabb", "pyedflib", "timm",
        "einops", "transformers", "torchinfo", "einx", "vector_quantize_pytorch", "deepspeed",
        "linear_attention_transformer", "safetensors", "rotary_embedding_torch", "mamba_ssm", "yaml",
        "huggingface_hub", "gdown", "pytest", "eegbench"]
bad = []
for m in mods:
    try:
        importlib.import_module(m)
    except Exception as e:  # noqa: BLE001
        bad.append((m, f"{type(e).__name__}: {e}"[:120]))
import torch
print(f"python {sys.version.split()[0]} | torch {torch.__version__} | cuda build {torch.version.cuda} | cuda available {torch.cuda.is_available()}")
print("import OK :", [m for m in mods if m not in dict(bad)])
print("import BAD:", bad if bad else "none")
sys.exit(1 if bad else 0)
EOF
}

if [[ "${1:-}" == "--check" ]]; then check; exit $?; fi

if ! conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  conda create -y -n "$ENV_NAME" "python=$PY_VER"
fi
PIP="conda run -n $ENV_NAME --no-capture-output python -m pip"

$PIP install --upgrade pip
$PIP install "torch==2.7.1" "torchvision==0.22.1" "torchaudio==2.7.1" --index-url "$TORCH_INDEX"

# benchmark requirements minus mamba-ssm (handled below)
grep -v -E '^\s*(#|$)|mamba-ssm' "$ROOT/third_party/eeg_fm_benchmark/requirements.txt" > /tmp/eegbench_req.txt
$PIP install -r /tmp/eegbench_req.txt

# project extras
$PIP install moabb pyyaml pytest ruff gdown huggingface_hub

# torcheeg: imported by the benchmark's LUNA loaders (models/FM/LUNA_*/modules/channel_embeddings.py) but missing
# from upstream requirements.txt. Its metadata pins scipy<=1.10.1, which would downgrade scipy and break mne/moabb;
# LUNA only needs `torcheeg.datasets.constants`, so install it without deps and add its real deps separately.
$PIP install --no-deps "torcheeg==1.1.3"
$PIP install lmdb xmltodict PyWavelets spectrum torchmetrics mne_connectivity pytorch-lightning wfdb xlrd

# mamba-ssm + causal-conv1d (EEGMamba; the Mamba fast path asserts causal_conv1d, per the official Mamba install
# notes linked from the EEGMamba README). Prebuilt wheels on GitHub releases need glibc>=2.32; this cluster is
# RHEL 8 (glibc 2.28), so both must be compiled from the official sources with the cluster toolchain
# (module gcc/13.4.0 + cuda/12.8, sm_89; system gcc 8.5 fails). That is done by scripts/slurm/build_mamba.sbatch on
# a GPU node. Here we only build if EEGBENCH_BUILD_MAMBA=1 is set (i.e. we are already on such a node).
if [[ "${EEGBENCH_BUILD_MAMBA:-0}" == "1" ]]; then
  module load gcc/13.4.0 cuda/12.8
  export CC="$(command -v gcc)" CXX="$(command -v g++)" CUDAHOSTCXX="$(command -v g++)"
  export MAMBA_FORCE_BUILD=TRUE CAUSAL_CONV1D_FORCE_BUILD=TRUE TORCH_CUDA_ARCH_LIST="${TORCH_CUDA_ARCH_LIST:-8.9}" MAX_JOBS="${MAX_JOBS:-8}"
  $PIP install --no-build-isolation --no-cache-dir "mamba-ssm==2.3.1" "causal-conv1d>=1.4.0"
else
  echo "NOTE: mamba-ssm / causal-conv1d not installed here; submit scripts/slurm/build_mamba.sbatch (GPU node build)."
fi

$PIP install -e "$ROOT"
check || true
