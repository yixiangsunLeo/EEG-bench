#!/usr/bin/env python3
"""CPU smoke test of the benchmark's model loaders with the weights collected in weights/.

For each Table-2 model: build synthetic BNCI2014001-shaped EEGData (22 ch, 250 Hz, 4 s, 4 classes), run the
model's own preprocessor (resample / filter / channel mapping, as the paper does), instantiate the loader
(pretrained weights load with the loader's own strictness), forward a small batch, check logits shape.

    conda run -n eegbench python scripts/smoke_models.py               # all
    conda run -n eegbench python scripts/smoke_models.py --only CBraMod LaBraM
    conda run -n eegbench python scripts/smoke_models.py --device cuda  # on a GPU node (needed for EEGMamba)

Weights are read from weights/ by redirecting the benchmark's `utils.utils.get_pretrained_models_path`
(the benchmark expects them under its own models/pretrained_models/). Nothing in third_party/ is modified.
"""

from __future__ import annotations

import argparse
import copy
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "third_party" / "eeg_fm_benchmark"
WEIGHTS = ROOT / "weights"

# benchmark model_name -> eegbench key (Table 2 roster)
MODELS = {
    "EEGNet": "eegnet", "ShallowConv": "shallowconv", "LMDA": "lmda", "TSception": "tsception",
    "CNNTransformer": "cnn_t", "Deformer": "deformer", "Conformer": "conformer",
    "BENDR": "bendr", "BIOT_6D": "biot_6d", "LaBraM": "labram", "NeuroGPT": "neuro_gpt", "EEGPT": "eegpt",
    "CBraMod": "cbramod", "TFMTokenizer": "tfm", "BrainOmni_Tiny": "brainomni_tiny",
    "BrainOmni_Base": "brainomni_base", "EEGMamba": "eegmamba", "SingLEM": "singlem", "LUNA_Base": "luna_base",
}
ML_MODELS = ["CSP_LDA", "Xdawn_LDA"]  # separate sklearn path; import-only check

BNCI2014001_CH = ["Fz", "FC3", "FC1", "FCZ", "FC2", "FC4", "C5", "C3", "C1", "CZ", "C2", "C4", "C6",
                  "CP3", "CP1", "CPZ", "CP2", "CP4", "P1", "PZ", "P2", "POZ"]


def make_eeg_data(n_trials: int = 8, seed: int = 0):
    import numpy as np
    from utils.EEGDataLoader import EEGData

    rng = np.random.default_rng(seed)
    x = rng.standard_normal((n_trials, len(BNCI2014001_CH), 1000)).astype("float32") * 10.0  # ~µV scale
    y = np.arange(n_trials) % 4
    subj = np.array([1] * (n_trials // 2) + [2] * (n_trials - n_trials // 2))
    return EEGData(dataset_name="BNCI2014001", eeg_data=x, subject_ids=subj, channel_names=BNCI2014001_CH,
                   sampling_rate=250, labels=y)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--batch", type=int, default=4)
    args = ap.parse_args()

    os.chdir(BENCH)                      # loaders use paths relative to the benchmark root
    sys.path.insert(0, str(BENCH))
    import torch
    import utils.utils as bench_utils

    def weights_path(*parts):            # redirect models/pretrained_models/ -> weights/
        return str(WEIGHTS.joinpath(*parts))

    bench_utils.get_pretrained_models_path = weights_path
    from utils.model_loader import import_model, import_preprocessor, apply_preprocessor

    torch.set_num_threads(max(1, min(8, os.cpu_count() or 1)))
    device = torch.device(args.device)
    base = make_eeg_data()
    names = args.only or list(MODELS)
    rows = []
    for name in names:
        t0 = time.time()
        status, detail = "ok", ""
        try:
            eeg = copy.deepcopy(base)
            try:
                pre = import_preprocessor(name)
            except (AttributeError, ImportError):
                pre = None
            if pre is not None:
                eeg = apply_preprocessor(eeg, pre, name, "BNCI2014001", task_mode="Cross")
            model = import_model(name, eeg, finetune_strategy="full").to(device).eval()
            xb = torch.as_tensor(eeg.eeg_data[: args.batch]).float().to(device)
            with torch.no_grad():
                out = model(xb)
            out = out[0] if isinstance(out, (tuple, list)) else out
            # count after the forward: some upstream models (Conformer) use LazyLinear, materialised on first call
            n_params = sum(p.numel() for p in model.parameters())
            if tuple(out.shape) != (args.batch, 4):
                status, detail = "BAD_SHAPE", f"logits {tuple(out.shape)}"
            else:
                detail = f"in {tuple(xb.shape)} @ {eeg.sampling_rate} Hz -> logits {tuple(out.shape)}; params {n_params/1e6:.2f}M"
        except Exception as e:  # noqa: BLE001
            status = "FAIL"
            detail = f"{type(e).__name__}: {str(e).splitlines()[0][:160]}"
            if os.environ.get("SMOKE_TRACE"):
                traceback.print_exc()
        rows.append((name, MODELS[name], status, f"{time.time()-t0:5.1f}s", detail))
        print(f"{status:9s} {name:15s} {rows[-1][3]}  {detail}", flush=True)

    for name in ML_MODELS:
        try:
            __import__(f"models.ML.{name}.Loader_{name}")
            print(f"ok        {name:15s} import only (sklearn path)")
        except Exception as e:  # noqa: BLE001
            print(f"FAIL      {name:15s} {type(e).__name__}: {str(e)[:120]}")

    bad = [r for r in rows if r[2] != "ok"]
    print(f"\n{len(rows)-len(bad)}/{len(rows)} deep models forward OK on {device}; failures: {[r[0] for r in bad]}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
