#!/usr/bin/env python3
"""Rebuild `weights/eegpt.ckpt` (the Lightning layout expected by the benchmark's EEGPT loader) from the
weights-only safetensors mirror `weights/eegpt_large_official.safetensors`.

The benchmark loader (third_party/eeg_fm_benchmark/models/FM/EEGPT/Loader_EEGPT.py) does
    ckpt = torch.load("eegpt.ckpt"); sd = {k[15:]: v for k, v in ckpt["state_dict"].items() if k.startswith("target_encoder.")}
    model.load_state_dict(sd, strict=True)
so only the key layout matters. Run inside the `eegbench` env:

    python scripts/convert_eegpt_safetensors.py

If you later obtain the official figshare file (eegpt_mcae_58chs_4s_large4E.ckpt), run with
`--compare /path/to/official.ckpt` to check tensor-wise equality before trusting the mirror.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import torch
from safetensors.torch import load_file

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "weights" / "eegpt_large_official.safetensors"
DST = ROOT / "weights" / "eegpt.ckpt"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--compare", type=Path, default=None, help="official .ckpt to compare against")
    args = ap.parse_args()

    sd = load_file(str(SRC))
    prefixes = sorted({k.split(".")[0] for k in sd})
    n_params = sum(v.numel() for v in sd.values())
    te = {k: v for k, v in sd.items() if k.startswith("target_encoder.")}
    print(f"source: {SRC.name}  tensors={len(sd)}  params={n_params/1e6:.1f}M  prefixes={prefixes}")
    print(f"target_encoder tensors={len(te)}  params={sum(v.numel() for v in te.values())/1e6:.1f}M")
    if prefixes != ["encoder", "predictor", "reconstructor", "target_encoder"]:
        raise SystemExit("unexpected module structure; refusing to convert")

    if args.compare is not None:
        official = torch.load(args.compare, map_location="cpu", weights_only=False)["state_dict"]
        missing = sorted(set(official) - set(sd))
        extra = sorted(set(sd) - set(official))
        mismatched = [k for k in official if k in sd and not torch.equal(official[k].float(), sd[k].float())]
        print(f"compare: missing_in_mirror={len(missing)} extra_in_mirror={len(extra)} value_mismatch={len(mismatched)}")
        for k in (missing + extra + mismatched)[:20]:
            print("   ", k)
        return 0 if not (missing or mismatched) else 1

    torch.save({"state_dict": sd, "eegbench_note": "rebuilt from eeg-telecom-paris/eegpt-large-official safetensors"}, DST)
    digest = hashlib.sha256(DST.read_bytes()).hexdigest()
    print(f"wrote {DST.relative_to(ROOT)}  {DST.stat().st_size/1e6:.1f} MB  sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
