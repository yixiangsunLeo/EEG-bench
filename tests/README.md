# tests/

Contract tests first, run with `pytest` (config in `pyproject.toml`):

- `data/` — canonical manifest schema, sha256 round-trip, channel names are valid 10-20 labels.
- `transforms/` — each transform is shape-preserving where expected, fit-free, deterministic.
- `models/` — for every integrated model key: random-tensor forward gives `[B, n_classes]`;
  `linear_probe` freezes the encoder; `input_spec` matches `configs/models/<key>.yaml`.
- `protocols/` — no subject (or dataset) leakage for every protocol × dataset; split hash stable.
- `training/` — resume is idempotent; `cell_signature` rejects a changed config; test set never used for selection.

Markers: `slow` (GPU / downloaded data), `needs_weights` (files in `weights/MANIFEST.yaml`).
