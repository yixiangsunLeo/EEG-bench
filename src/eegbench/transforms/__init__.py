"""Pure, stateless signal transforms that execute a model's `input_spec`.

resample, bandpass / notch, channel select / map / interpolate (to a template montage),
normalization (z-score, min-max to [-1, 1], P95 scaling), Euclidean Alignment (reference matrix supplied
by the caller, computed on the training side only), patchify (window_s / stride_s).

Rule: any statistic used here must be per-trial (fit-free) or computed on training data by the caller.
"""
