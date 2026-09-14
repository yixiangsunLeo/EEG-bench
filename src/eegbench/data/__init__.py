"""Dataset registry and raw -> canonical conversion.

Contract (docs/ARCHITECTURE.md §3.1): one `prepare_<dataset>()` per dataset writes
`data/canonical/<dataset>/v<k>/{manifest.json, sub-*/ses-*.npz}` with
X float32 [n_trials, n_ch, n_times] at native sampling rate, y int64, 10-20 channel names, per-file sha256.

No filtering / resampling here — that is model-side (see `eegbench.transforms`).
Planned modules: registry.py, canonical.py, moabb_bnci.py, wbcic_shu.py, shu2022.py.
"""
