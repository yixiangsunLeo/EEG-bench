# configs/

All runnable configuration. Python never hard-codes paths or hyperparameters.

| path | content |
|:---|:---|
| `paths.example.yaml` → copy to `paths.local.yaml` (gitignored) | machine-local roots: raw, external processed manifests, canonical, weights, outputs |
| `datasets/<key>.yaml` | dataset cards (facts from the paper / verified in-house facts); `canonical_version` set by `prepare` |
| `models/roster.yaml` | the 20 Table-2 entries with paper facts and `input_spec`; `models/<key>.yaml` added at integration |
| `protocols/<key>.yaml` | split definitions; fields marked TBD are PLAN.md §5 decisions |
| `experiments/<name>.yaml` | `run_id` + datasets × models × protocol + training defaults |
