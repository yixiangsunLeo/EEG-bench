# scripts/

Thin wrappers only; anything reusable belongs in `src/eegbench/` behind the CLI.

| script | purpose |
|:---|:---|
| `setup_env.sh` | create / check the `eegbench` conda env (torch 2.7.1+cu128 + benchmark requirements + torcheeg); `--check` runs the import test |
| `download_weights.py` | collect the 12 FM checkpoints into `weights/` (HF mirror / GitHub release / bundled / git history) and write `weights/MANIFEST.yaml`; `--verify` re-hashes |
| `convert_eegpt_safetensors.py` | rebuild `weights/eegpt.ckpt` from the safetensors mirror; `--compare <official.ckpt>` for tensor-wise verification |
| `download_bnci.py` | download the 5 BNCI datasets with MOABB into `raw_root`; `--curl N` = MOABB enumerates files, curl fetches with resume; `--check` inventory; `--finalize` writes the persistent MNE config |
| `verify_bnci.py` | load every subject with MOABB and compare subjects / channels / sfreq / trials with `configs/datasets/*.yaml` (Table 14) |
| `smoke_models.py` | forward all Table-2 models through the benchmark loaders with real weights (`--device cuda` on a GPU node) |
| `slurm/smoke_gpu.sbatch` | GPU-node import check + model smoke |
| `slurm/build_mamba.sbatch` | source-build mamba-ssm + causal-conv1d (gcc 13 / CUDA 12.8) and re-smoke EEGMamba |

Cluster: partitions `gpu2node` / `gpu3node` (RTX 4090 D, driver CUDA 12.8), shared env `mi_torch_cu118` (read-only),
project env `eegbench`. GPU jobs must fail fast when CUDA is unavailable; never run training on the login node.
