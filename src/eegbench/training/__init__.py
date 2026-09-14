"""The single trainer.

Fine-tuning modes: full / linear_probe (/ lora). Per cell: `best.pt` + `last.pt` only, resumable from
`last.pt` (optimizer / scheduler / RNG / history), atomic writes, `result.json` as completion marker,
`cell_signature` guard against reusing a directory with a different configuration.
Records final-epoch and best-val metrics plus per-trial predictions. Test data never drives model selection.
Model-specific behaviour enters through hooks (`compute_loss`, `on_after_step`), never a trainer fork.
"""
