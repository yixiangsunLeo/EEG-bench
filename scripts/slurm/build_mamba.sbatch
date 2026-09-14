#!/usr/bin/env bash
#SBATCH -J eegbench_mamba
#SBATCH -p gpu2node
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH -t 03:00:00
#SBATCH -o logs/slurm/build_mamba_%j.out
#SBATCH -e logs/slurm/build_mamba_%j.err
# Build mamba-ssm 2.3.1 from the official source on a GPU node (prebuilt wheels need glibc>=2.32; cluster has 2.28),
# then re-run the model smoke test for the three models that could not be verified on the login node.
#   sbatch scripts/slurm/build_mamba.sbatch        (run from the repository root)
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../..}"
source /share/software/anaconda3/2024.10/etc/profile.d/conda.sh
conda activate eegbench
# system gcc is 8.5 (RHEL 8): the first attempt failed while compiling the CUDA objects. CUDA 12.8 supports host
# gcc <= 14, so use the cluster's gcc 13 module as the host compiler.
module load gcc/13.4.0 cuda/12.8
export CC="$(command -v gcc)" CXX="$(command -v g++)" CUDAHOSTCXX="$(command -v g++)"
export PYTHONUNBUFFERED=1 PIP_CACHE_DIR="$HOME/.cache/pip"
export MAMBA_FORCE_BUILD=TRUE TORCH_CUDA_ARCH_LIST="8.9" MAX_JOBS="${SLURM_CPUS_PER_TASK:-8}"
echo "node=$(hostname) job=${SLURM_JOB_ID:-} nvcc=$(nvcc --version | tail -1) gcc=$(gcc --version | head -1) glibc=$(ldd --version | head -1)"
python -c "import torch; assert torch.cuda.is_available(); print('torch', torch.__version__, torch.cuda.get_device_name(0))"

PIPLOG="logs/slurm/build_mamba_pip_${SLURM_JOB_ID:-x}.log"
build() {  # build <pip requirement> ; full log appended to $PIPLOG
  echo "===== build $1 from source (log: $PIPLOG) ====="
  if ! ( time python -m pip install --no-build-isolation --no-cache-dir -v "$1" ) >> "$PIPLOG" 2>&1; then
    echo "BUILD FAILED for $1 — first compiler errors:"
    grep -n -i -E "error[: ]" "$PIPLOG" | grep -v -i -E "warning|Werror|error_type" | head -30 | cut -c1-240
    exit 1
  fi
  tail -2 "$PIPLOG"
}

# mamba-ssm: skip if the source-built one is already importable on this GPU node
if ! python -c "import mamba_ssm" 2>/dev/null; then
  python -m pip uninstall -y mamba-ssm || true       # drop the glibc-incompatible prebuilt wheel if present
  build "mamba-ssm==2.3.1"
fi
# causal-conv1d: required by Mamba's default fast path (mamba_ssm asserts it); the official Mamba install
# instructions (linked from the EEGMamba README) list it. Prebuilt wheels have the same glibc problem -> source build.
export CAUSAL_CONV1D_FORCE_BUILD=TRUE
python -c "import causal_conv1d" 2>/dev/null || build "causal-conv1d>=1.4.0"

echo "===== verify ====="
python - <<'EOF'
import torch, mamba_ssm, causal_conv1d
from mamba_ssm import Mamba
m = Mamba(d_model=64, d_state=16, d_conv=4, expand=2).cuda()      # default use_fast_path=True -> needs causal_conv1d
y = m(torch.randn(2, 100, 64).cuda())
print("mamba_ssm", mamba_ssm.__version__, "| causal_conv1d", causal_conv1d.__version__, "| forward ok", tuple(y.shape))
EOF

echo "===== smoke: previously failing models ====="
python scripts/smoke_models.py --device cuda --only Conformer EEGMamba LUNA_Base
echo "===== import check ====="
bash scripts/setup_env.sh --check || true
