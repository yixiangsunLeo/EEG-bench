#!/usr/bin/env bash
#SBATCH -J eegbench_smoke
#SBATCH -p gpu2node
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH -t 00:30:00
#SBATCH -o logs/slurm/smoke_gpu_%j.out
#SBATCH -e logs/slurm/smoke_gpu_%j.err
# GPU-node verification of the eegbench environment and all benchmark model loaders (P0 acceptance).
#   sbatch scripts/slurm/smoke_gpu.sbatch        (run from the repository root)
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../..}"
source /share/software/anaconda3/2024.10/etc/profile.d/conda.sh
conda activate eegbench
export PYTHONUNBUFFERED=1
echo "node=$(hostname) job=${SLURM_JOB_ID:-} gpu=${CUDA_VISIBLE_DEVICES:-}"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader || true
python -c "import torch; assert torch.cuda.is_available(), 'CUDA unavailable — refusing to continue'; print('torch', torch.__version__, 'cuda', torch.version.cuda, torch.cuda.get_device_name(0))"

echo "===== import check ====="
bash scripts/setup_env.sh --check || true

echo "===== model smoke (cuda) ====="
python scripts/smoke_models.py --device cuda
