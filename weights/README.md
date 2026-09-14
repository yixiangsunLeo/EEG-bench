# weights/

Pretrained weights for the 12 foundation models (gitignored). `MANIFEST.yaml` is the only tracked file and is
written by `scripts/download_weights.py` (file, url, sha256, size, license, source_commit, downloaded).
Relative paths mirror the benchmark's `models/pretrained_models/` layout, so the benchmark loaders can be pointed
here by overriding `utils.utils.get_pretrained_models_path` (planned in `eegbench.models`).

```bash
python scripts/download_weights.py            # fetch anything missing, hash, update manifest
python scripts/download_weights.py --verify   # re-hash against manifest (also run by `eegbench doctor`)
```

## Sources (2026-09-14)

| file | model | source | provenance |
|:---|:---|:---|:---|
| `encoder.pt` (+ `contextualizer.pt`) | BENDR | GitHub release SPOClab-ca/BENDR v0.1-alpha | official |
| `EEG-six-datasets-18-channels.ckpt` (+ PREST / SHHS+PREST) | BIOT | bundled in official repo | official |
| `labram-base.pth` | LaBraM | bundled in official repo | official |
| `neurogpt.bin` | Neuro-GPT | HF `wenhuic/Neuro-GPT` `pretrained_model/pytorch_model.bin` | official |
| `CBraMod.pth` | CBraMod | HF `weighting666/CBraMod` `pretrained_weights.pth` | official |
| `EEGMamba.pth` | EEGMamba | HF `weighting666/EEGMamba` `pretrained_EEGMamba.pth` | official |
| `BrainOmni/{tiny,base}/BrainOmni.pt`, `BrainOmni/braintokenizer/BrainTokenizer.pt` (+ `model_cfg.json`) | BrainOmni | HF `OpenTSLab/BrainOmni` | official |
| `LUNA_base.safetensors` (+ `LUNA_config.json`) | LUNA-Base | HF `PulpBio/LUNA` | official, CC BY-ND 4.0 |
| `singlem_pretrained.pt` | SingLEM | git history of the official repo, `05abe21:weights/singlem_pretrained.pt` (the file the benchmark loads; deleted upstream on 2026-07-31 and replaced by *retrained* checkpoints — D-013) | official, paper-era |
| `singlem_downstream_excluded_rev2026-07-31.pt` | SingLEM (revised) | `6db5b5a:SingLEM/checkpoints/singlem_downstream_excluded.pt` | official, **not** what the paper used; kept for a future comparison only |
| `tfm_tokenizer_last.pth`, `tfm_encoder_mtp_last.pth` | TFM-Tokenizer | bundled `pretrained_weigths/multiple_dataset_settings/…` | official |
| `eegpt_large_official.safetensors` → `eegpt.ckpt` | EEGPT | HF `eeg-telecom-paris/eegpt-large-official` | **third-party conversion** (see below) |

Hugging Face files were fetched through the public mirror `https://hf-mirror.com` (huggingface.co is unreachable from
the cluster); the mirror serves byte-identical files from the same repos.

## EEGPT provenance caveat

The official checkpoint `eegpt_mcae_58chs_4s_large4E.ckpt` is distributed only via a figshare private link
(https://figshare.com/s/e37df4f8a907a866df4b) that requires a browser (JS challenge; the API rejects the token).
`eeg-telecom-paris/eegpt-large-official` is a weights-only safetensors with exactly the official module structure
(`encoder` / `predictor` / `reconstructor` / `target_encoder`, 413 tensors, 58 ch, 256 Hz, 4 s, patch 64, embed 512×4).
`scripts/convert_eegpt_safetensors.py` rebuilds the Lightning `{"state_dict": …}` layout as `eegpt.ckpt`; the benchmark
loader's `strict=True` load of `target_encoder.*` validates the structure.

**To close the gap**: download the figshare file in a browser, copy it to the cluster, and run
`python scripts/convert_eegpt_safetensors.py --compare /path/to/eegpt_mcae_58chs_4s_large4E.ckpt` (tensor-wise equality).
Until then EEGPT numbers must be footnoted as "mirror weights, unverified against figshare original".
