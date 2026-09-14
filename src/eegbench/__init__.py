"""eegbench — EEG foundation-model / specialist-model benchmark and cross-dataset experiments.

Layers (see docs/ARCHITECTURE.md §2):

    data        raw / MOABB  -> canonical trials (versioned, hashed)
    transforms  pure functions executing a model's `input_spec` on canonical trials
    models      unified `EEGModel` interface + thin adapters over third_party/ official code
    protocols   deterministic split generators (LOSO, few-shot, cross-dataset) + leakage assertions
    training    the single trainer (full / linear_probe / lora), best+last checkpoints, resume
    evaluation  metrics, summarizer (result.json -> tables), statistics
    cli         `python -m eegbench.cli prepare|split|train|summarize|doctor`

Status 2026-09-13: skeleton only; no implementation yet.
"""

__version__ = "0.0.1"
