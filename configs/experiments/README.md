# configs/experiments

One YAML per runnable experiment. An experiment = `run_id` + list of datasets + list of model keys +
protocol key + training defaults (overridable per model YAML) + output roots. Planned first files:

- `bench_loso_mi_v1.yaml` — 3 BNCI MI sets + WBCIC-SHU + SHU 2022 × all specialists (P2), then FMs (P3).
- `bench_loso_p300_v1.yaml` — BNCI2014009 / BNCI2014008.
- `bench_loso_linear_probe_v1.yaml` — FMs with frozen encoders.
- `xdataset_*.yaml` — blocked until PLAN Q1/Q4/Q5 are decided.

A completed `run_id` is read-only; re-runs get a new suffix (`_v2`).
