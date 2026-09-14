# data/

Canonical datasets only (gitignored). Raw data never lives in the project; MOABB downloads go to `raw_root`
from `configs/paths.local.yaml`, the two in-house datasets are read from their external processed manifests.

```text
data/canonical/<dataset_key>/v<k>/
├── manifest.json          # key, version, sfreq, channel_names (10-20), class_names, units, sha256 per file,
│                          # source (MOABB version / external manifest sha256), generating command + git commit
└── sub-<id>/ses-<id>.npz  # X float32 [n_trials, n_ch, n_times] @ native fs, y int64, trial_meta
```

- Produced by `python -m eegbench.cli prepare --dataset <key>`; bump `v<k>` only when conversion logic changes.
- No filtering / resampling at this layer (model-side, see `eegbench.transforms`).
- `data/` may be a symlink to a large disk; keep the relative layout identical.
